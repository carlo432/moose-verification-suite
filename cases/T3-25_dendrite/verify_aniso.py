#!/usr/bin/env python3
"""T3-25 (re-scoped) -- anisotropic solidification: growth-direction selection.

The tip-velocity observable was abandoned because this model has no steady tip
velocity in an affordable domain; see observable_correction in reference.json.
What is verified here is what the model predicts exactly: the grain acquires an
m-fold shape locked to reference_angle.

    C_m = integral w cos(m theta) dA        a_m = sqrt(C_m^2+S_m^2)/area
    S_m = integral w sin(m theta) dA        theta_m = atan2(S_m, C_m)/m

For R(theta) = R0[1 + a cos(m(theta-theta_0))] these recover a and theta_0
exactly. Volume integrals, so no interface-crossing error.
"""
from __future__ import annotations

import csv, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
REF = json.loads((ROOT / "reference.json").read_text())
TOL = REF["tolerance"]["value"]
SEC = REF["secondary_tolerances"]

# (tag, nx, mode, theta0, delta) -- must match run_aniso.sh
RUNS = [("rot000", 96, 6, 0, 0.04), ("rot015", 96, 6, 15, 0.04),
        ("rot030", 96, 6, 30, 0.04), ("rot045", 96, 6, 45, 0.04),
        ("mode4", 96, 4, 90, 0.04), ("null", 96, 6, 90, 0.0),
        ("mesh048", 48, 6, 90, 0.04), ("mesh096", 96, 6, 90, 0.04),
        ("mesh144", 144, 6, 90, 0.04),
        # Mesh-independence of the PHASE is checked at 15 degrees, not at the
        # 90 (= 30 mod 60) used above. See symmetry_caveat: at 0 and 30 the
        # configuration is mirror-symmetric about a mesh axis, S_6 is
        # identically zero, and the phase is exact by symmetry rather than by
        # measurement -- a spread of 3.6e-15 across three meshes there was not
        # evidence of anything. The theta0 = 90 sweep is retained because the
        # OFF-MODE amplitude it measures is informative regardless of symmetry.
        ("m15_048", 48, 6, 15, 0.04), ("m15_096", 96, 6, 15, 0.04),
        ("m15_144", 144, 6, 15, 0.04)]
AREA_FACTOR = 3.0
T_E = 1.0          # equilibrium temperature in the free energy


def wrap(d, period):
    """signed angular difference reduced into (-period/2, period/2]"""
    return (d + period / 2.0) % period - period / 2.0


def read(tag, mode):
    f = OUT / f"an_{tag}.csv"
    if not f.exists():
        return None
    rows = [r for r in csv.DictReader(f.open()) if float(r["area"]) > 0]
    if len(rows) < 4:
        return None
    a0 = float(rows[0]["area"])
    pick = next((r for r in rows if float(r["area"]) >= AREA_FACTOR * a0), None)
    if pick is None:
        return {"tag": tag, "note": f"area never reached {AREA_FACTOR}x (max "
                                    f"{max(float(r['area']) for r in rows)/a0:.2f}x)",
                "steps": len(rows)}

    def amp_phase(r, m):
        C, S = float(r[f"C{m}"]), float(r[f"S{m}"])
        A = float(r["area"])
        return math.hypot(C, S) / A, math.degrees(math.atan2(S, C)) / m

    a_on, ph_on = amp_phase(pick, mode)
    off = 4 if mode == 6 else 6
    a_off, _ = amp_phase(pick, off)

    # Phase stability, measured only while the melt is still undercooled.
    # Once T_max passes T_e the driving force atan(gamma(T_e - T)) changes sign
    # and the grain begins to MELT; melting is fastest where growth was slowest,
    # so the pattern inverts by half a lobe. That inversion is real and is
    # reported, but it is not phase noise and must not be scored as drift.
    period = 360.0 / mode
    pre = [r for r in rows if float(r["area"]) >= AREA_FACTOR * a0
           and float(r["T_max"]) < T_E]
    drift = (max(abs(wrap(amp_phase(r, mode)[1] - ph_on, period)) for r in pre)
             if len(pre) > 1 else 0.0)
    recal = next((float(r["time"]) for r in rows if float(r["T_max"]) >= T_E), None)
    return {"tag": tag, "steps": len(rows), "t": float(pick["time"]),
            "area_ratio": float(pick["area"]) / a0,
            "mode": mode, "amplitude_on_mode": a_on, "amplitude_off_mode": a_off,
            "off_over_on": (a_off / a_on if a_on > 0 else float("inf")),
            "phase_deg": ph_on, "phase_drift_deg": drift,
            "T_max_at_measurement": float(pick["T_max"]),
            "recalescence_time": recal,
            "measured_before_recalescence": bool(float(pick["T_max"]) < T_E)}


def main() -> int:
    got = {}
    for tag, nx, mode, th0, delta in RUNS:
        r = read(tag, mode)
        if r:
            r.update({"nx": nx, "reference_angle": th0, "anisotropy_strength": delta})
        got[tag] = r

    missing = [t for t, r in got.items() if r is None or "phase_deg" not in r]
    result = {"case_id": REF["case_id"], "capability": REF["capability"],
              "validation_class": REF["validation_class"],
              "units": "degrees",
              "tolerance": {"metric": REF["tolerance"]["metric"], "value": TOL}}

    if missing:
        result.update({"reference_value": None, "moose_value": None,
                       "error": {"absolute": None, "relative": None},
                       "verdict": "PARTIAL",
                       "checks": {k: False for k in
                                  ("arm_direction_exact", "rotation_slope_unity",
                                   "isotropic_null", "off_mode_suppressed",
                                   "mesh_independent_phase")},
                       "notes": "runs incomplete: " + ", ".join(missing)})
        print(json.dumps(result, indent=2))
        return 0

    # --- primary: arm direction tracks reference_angle, modulo 360/m ----------
    rot = [got[t] for t in ("rot000", "rot015", "rot030", "rot045")]
    period6 = 60.0
    errs = [abs(wrap(r["phase_deg"] - r["reference_angle"], period6)) for r in rot]
    worst = max(errs)

    # --- rotation slope: one degree of crystal per degree of reference_angle --
    xs = [r["reference_angle"] for r in rot]
    ys, acc = [], 0.0
    prev = None
    for r in rot:                      # unwrap the measured phases before fitting
        p = r["phase_deg"]
        if prev is not None:
            acc += wrap(p - prev, period6)
        else:
            acc = 0.0
        ys.append(ys[0] + acc if ys else p)
        prev = p
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    slope = (sum((a-mx)*(b-my) for a, b in zip(xs, ys)) / sum((a-mx)**2 for a in xs))

    # --- isotropic null, off-mode suppression, mesh independence --------------
    ref_amp = got["mesh096"]["amplitude_on_mode"]
    null_ratio = got["null"]["amplitude_on_mode"] / ref_amp
    off_ratios = {t: got[t]["off_over_on"] for t in ("mesh048", "mesh096", "mesh144", "mode4")}
    off_decreases = (got["mesh048"]["amplitude_off_mode"]
                     > got["mesh096"]["amplitude_off_mode"]
                     > got["mesh144"]["amplitude_off_mode"])
    # Phase spread at a NON-symmetric angle, where the phase is measured.
    mesh_phases = [15.0 + wrap(got[t]["phase_deg"] - 15.0, period6)
                   for t in ("m15_048", "m15_096", "m15_144")]
    mesh_spread = max(abs(wrap(a - mesh_phases[1], period6)) for a in mesh_phases)
    mode4_err = abs(wrap(got["mode4"]["phase_deg"] - got["mode4"]["reference_angle"], 90.0))

    checks = {
        "arm_direction_exact": bool(worst <= TOL),
        "rotation_slope_unity": bool(abs(slope - 1.0) <= SEC["rotation_slope"]["value"]),
        "isotropic_null": bool(null_ratio <= SEC["isotropic_null"]["value"]),
        "off_mode_suppressed": bool(max(off_ratios.values()) <= SEC["off_mode_suppression"]["value"]
                                    and off_decreases),
        "mesh_independent_phase": bool(mesh_spread <= SEC["mesh_independence_phase"]["value"]),
        "mode_selection_4fold": bool(mode4_err <= TOL),
        # formalises the wording already in reference.json quantity.measured_at,
        # "early enough to precede recalescence"
        "measured_before_recalescence": bool(all(got[t]["measured_before_recalescence"]
                                                 for t, *_ in RUNS)),
    }
    result.update({
        "reference_value": [r["reference_angle"] for r in rot],
        # Reported in the SAME branch as reference_value. theta_m = atan2/m has
        # period 360/m = 60 degrees, so the raw principal value lands in
        # (-30, 30]: a true 30 comes back as -30 and a true 45 as -14.855. Those
        # are the same angle, and the tolerance is declared modulo 360/m, but
        # writing the raw values into moose_value made RESULTS.md print "-30"
        # against a reference of "30" next to a PASS. The raw principal values
        # are kept in anisotropy_diagnostic.rotation_sweep[].phase_deg.
        "moose_value": [r["reference_angle"] + wrap(r["phase_deg"] - r["reference_angle"], period6)
                        for r in rot],
        "error": {"absolute": worst, "relative": None},
        # The theta0 = 90 sweep below measures the OFF-MODE amplitude, which is
        # what the mesh-artifact test needs and which symmetry does not pin.
        # The phase-independence sweep is separate and at 15 degrees.
        "phase_mesh_sweep_at_15deg": [
            {"nx": got[t]["nx"], "phase_deg": 15.0 + wrap(got[t]["phase_deg"] - 15.0, period6),
             "amplitude_on_mode": got[t]["amplitude_on_mode"]}
            for t in ("m15_048", "m15_096", "m15_144")],
        "convergence": {"levels": [{"nx": got[t]["nx"], "phase_deg": got[t]["phase_deg"],
                                    "amplitude_on_mode": got[t]["amplitude_on_mode"],
                                    "amplitude_off_mode": got[t]["amplitude_off_mode"]}
                                   for t in ("mesh048", "mesh096", "mesh144")],
                        "phase_spread_deg": mesh_spread,
                        "observed_order": None, "expected_order": None},
        "anisotropy_diagnostic": {
            "observable": REF["quantity"]["observable"],
            "measured_at": REF["quantity"]["measured_at"],
            "rotation_sweep": [{"reference_angle": r["reference_angle"],
                                "phase_deg": r["phase_deg"],
                                "error_deg": abs(wrap(r["phase_deg"] - r["reference_angle"], period6)),
                                "amplitude": r["amplitude_on_mode"],
                                "phase_drift_deg": r["phase_drift_deg"]} for r in rot],
            "rotation_slope": slope,
            "mode_selection": {"mode_number_4_phase_deg": got["mode4"]["phase_deg"],
                               "expected_mod_90": got["mode4"]["reference_angle"] % 90,
                               "error_deg": mode4_err,
                               "a4": got["mode4"]["amplitude_on_mode"],
                               "a6": got["mode4"]["amplitude_off_mode"]},
            "isotropic_null": {"amplitude_at_delta_0": got["null"]["amplitude_on_mode"],
                               "amplitude_at_delta_0p04": ref_amp,
                               "ratio": null_ratio},
            "off_mode": {"ratios": off_ratios,
                         "decreases_with_refinement": off_decreases,
                         "note": ("The square mesh imprints a four-fold bias on a circle. It is "
                                  "distinguished from physics by refinement, the same test used "
                                  "on the T1-08 contact checkerboard.")},
            "recalescence": {
                "note": ("T_max crosses T_e partway through every run. Past that point the driving "
                         "force atan(gamma(T_e - T)) is negative, the grain melts, and because "
                         "melting is fastest where growth was slowest the shape inverts by exactly "
                         "half a lobe -- the m=4 phase steps 0 -> -45 degrees. Every measurement "
                         "here is taken before that, as the declared measured_at requires."),
                "by_run": {t: {"recalescence_time": got[t]["recalescence_time"],
                               "measurement_time": got[t]["t"],
                               "T_max_at_measurement": got[t]["T_max_at_measurement"]}
                           for t, *_ in RUNS}},
            "symmetry_caveat": (
                "reference_angle 0 and 30 give S_6 identically zero (order 1e-18) because the "
                "configuration is mirror-symmetric about the mesh axis, so those two phases are "
                "exact by symmetry rather than by measurement. The informative rotation points are "
                "15 and 45 degrees, which are not mesh-symmetric."),
            "observable_correction": REF["observable_correction"],
        },
        "checks": checks,
        "verdict": "PASS" if all(checks.values()) else "PARTIAL",
        "ranks": 1,
        "moose_version": "snapshot-20-10-27-41583-g2bd11a08a7",
    })
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
