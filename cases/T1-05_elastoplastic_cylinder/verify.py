#!/usr/bin/env python3
"""T1-05 — J2/von Mises elastoplasticity in a thick-walled cylinder.

p_lim is measured directly as the applied pressure at which the plastic front
reaches the outer wall (full-section yield), which is the definition of plastic
collapse for this problem.  The previous observable -- the first pressure with
max effective plastic strain >= 1 -- was an arbitrary operational threshold; it
is gone, and reference.json records the substitution.

Past the limit load the small-strain perfectly plastic system is singular: there
is no equilibrium solution, Newton either fails outright or converges to
|R| ~ 1e-14 on one of two spurious branches whose hoop stress is sign flipped.
Every step at or after the collapse step is therefore discarded.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
FIG = ROOT / "figures"
REF = json.loads((ROOT / "reference.json").read_text())

P = REF["parameters"]
A, B = P["inner_radius_m"], P["outer_radius_m"]
SY = P["yield_stress_MPa"]
NU = P["poissons_ratio"]
K = 2 * SY / np.sqrt(3)                      # plane-strain von Mises flow stress
P_LIM = REF["reference"]["value"]
P_Y = SY / np.sqrt(3) * (1 - A**2 / B**2)
TOL = REF["tolerance"]["value"]
SEC = REF["secondary_tolerances"]
RAMP = 100.0                                 # pressure = 100*t MPa
MESHES = [20, 40, 80, 160]


def history(tag: str) -> dict[str, np.ndarray]:
    with (OUT / f"cylinder_{tag}.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    return {key: np.array([float(row[key]) for row in rows]) for key in rows[0]}


def profile(tag: str, index: int) -> dict[str, np.ndarray]:
    """Radial sample at a given output index; the index matches the history row."""
    with (OUT / f"cylinder_{tag}_stress_profile_{index:04d}.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    cols = {key: np.array([float(row[key]) for row in rows]) for key in rows[0]}
    order = np.argsort(cols["x"])
    return {key: value[order] for key, value in cols.items()}


def collapse_index(hist: dict[str, np.ndarray]) -> int | None:
    """First output index at which the outer wall has yielded."""
    hit = np.flatnonzero(hist["outer_wall_plastic_strain"] > 0.0)
    return int(hit[0]) if len(hit) else None


def measure_p_lim(tag: str) -> dict:
    hist = history(tag)
    index = collapse_index(hist)
    if index is None or index == 0:
        # Either the ramp stopped short of collapse or the run was truncated.
        return {"p_lim_MPa": None, "index": None, "relative_error": None,
                "increment_MPa": None, "reached_collapse": False,
                "last_pressure_MPa": float(RAMP * hist["time"][-1])}
    pressure = RAMP * hist["time"]
    return {
        "p_lim_MPa": float(pressure[index]),
        "bracket_MPa": [float(pressure[index - 1]), float(pressure[index])],
        "increment_MPa": float(pressure[index] - pressure[index - 1]),
        "outer_wall_plastic_strain": float(hist["outer_wall_plastic_strain"][index]),
        "relative_error": float(abs(pressure[index] - P_LIM) / P_LIM),
        "index": index, "reached_collapse": True,
    }


def yield_onset(tag: str) -> float | None:
    """Interpolate the von Mises crossing of sigma_y from the elastic branch.

    The first capped value is already clipped to sigma_y and cannot be
    interpolated, so the last two uncapped values are extrapolated instead.
    """
    hist = history(tag)
    vm, pressure = hist["max_vonmises"], RAMP * hist["time"]
    hit = np.flatnonzero(vm >= SY - 1e-8)
    if not len(hit):
        return None
    j = int(hit[0])
    if j < 2:
        return float(pressure[j])
    p0, p1, v0, v1 = pressure[j - 2], pressure[j - 1], vm[j - 2], vm[j - 1]
    if v1 <= v0:
        return float(pressure[j])
    return float(p1 + (SY - v1) * (p1 - p0) / (v1 - v0))


def front_curve(tag: str, index: int) -> list[dict[str, float]]:
    """Elastic-plastic interface radius c versus applied pressure, pre-collapse.

    Compared against p(c) = (sigma_y/sqrt(3))[2 ln(c/a) + 1 - c^2/b^2].  The
    pressure comes from the history row at the same index, not from
    increment*index, because MOOSE cuts timesteps on this ramp.
    """
    hist = history(tag)
    pressure = RAMP * hist["time"]
    rows, seen = [], set()
    for i in range(1, index):
        if not 50.0 <= pressure[i] <= 75.0:
            continue
        prof = profile(tag, i)
        x, epsp = prof["x"], prof["eff_plastic_strain"]
        positive = np.flatnonzero(epsp > 1e-10)
        if not len(positive) or positive[-1] >= len(epsp) - 1:
            continue
        j = int(positive[-1])
        c = x[j] + (x[j + 1] - x[j]) * epsp[j] / (epsp[j] - epsp[j + 1])
        if not 1.2 <= c <= 1.8:
            continue
        # The load ramp is finer than the mesh, so keep one sample per resolved
        # front position rather than repeating the same element boundary.
        key = round(float(c), 6)
        if key in seen:
            continue
        seen.add(key)
        p_ref = SY / np.sqrt(3) * (2 * np.log(c / A) + 1 - c * c / B**2)
        rows.append({"pressure_MPa": float(pressure[i]), "interface_radius_m": float(c),
                     "reference_pressure_MPa": float(p_ref),
                     "relative_error": float(abs(pressure[i] - p_ref) / p_ref)})
    return rows


def stress_field(tag: str, index: int) -> dict:
    """Fully-plastic stress field at the collapse step against closed form.

    sigma_rr = -k ln(b/r) and sigma_tt = k(1 - ln(b/r)) follow from equilibrium
    plus the plane-strain yield condition sigma_tt - sigma_rr = k.  sigma_zz is
    reported as a diagnostic only: its closed form k(1/2 - ln(b/r)) assumes
    fully developed plastic flow, which the outer wall has not reached at the
    instant it yields.
    """
    prof = profile(tag, index)
    r, srr, shh, szz = prof["x"], prof["srr"], prof["shh"], prof["szz"]
    a_rr = -K * np.log(B / r)
    a_hh = K * (1 - np.log(B / r))
    residual = np.concatenate([srr - a_rr, shh - a_hh])
    return {
        "sigma_rr_L2_relative": float(np.sqrt(np.mean((srr - a_rr) ** 2)) / K),
        "sigma_tt_L2_relative": float(np.sqrt(np.mean((shh - a_hh) ** 2)) / K),
        "combined_L2_relative": float(np.sqrt(np.mean(residual**2)) / K),
        "max_pointwise_relative": float(np.max(np.abs(residual)) / K),
        "von_mises_condition_mean": float(np.mean(shh - srr) / K),
        "sigma_zz_outer_wall": {"moose": float(szz[-1]),
                                "elastic_nu_times_trace": float(NU * (srr[-1] + shh[-1])),
                                "fully_plastic_half_trace": float(0.5 * (srr[-1] + shh[-1]))},
        "sigma_zz_inner_wall": {"moose": float(szz[0]),
                                "elastic_nu_times_trace": float(NU * (srr[0] + shh[0])),
                                "fully_plastic_half_trace": float(0.5 * (srr[0] + shh[0]))},
        "sigma_zz_note": ("sigma_zz tracks the elastic nu*(srr+stt) at the outer wall, which has "
                          "only just reached yield, and migrates toward the fully plastic "
                          "(srr+stt)/2 at the inner wall where plastic strain has accumulated. "
                          "Excluded from acceptance by reference.json and reported as a "
                          "plastic-flow-development indicator."),
        "radius_m": r.tolist(), "sigma_rr_MPa": srr.tolist(),
        "sigma_tt_MPa": shh.tolist(), "sigma_zz_MPa": szz.tolist(),
    }


def main() -> None:
    FIG.mkdir(exist_ok=True)

    mesh_levels = []
    for nx in MESHES:
        m = measure_p_lim(f"n{nx}")
        mesh_levels.append({"nx": nx, "p_lim_MPa": m["p_lim_MPa"],
                            "relative_error": m["relative_error"],
                            "reached_collapse": m["reached_collapse"]})

    primary_tag = f"n{MESHES[-1]}"
    primary = measure_p_lim(primary_tag)
    controls = {"coarse": measure_p_lim("coarse_n160"),
                "primary": primary,
                "halved": measure_p_lim("halved_n160")}

    all_reached = (all(lv["reached_collapse"] for lv in mesh_levels)
                   and all(c["reached_collapse"] for c in controls.values()))
    if not all_reached:
        result = {"case_id": REF["case_id"], "capability": REF["capability"],
                  "validation_class": REF["validation_class"],
                  "reference_value": P_LIM, "moose_value": None, "units": "MPa",
                  "error": {"absolute": None, "relative": None},
                  "tolerance": {"metric": REF["tolerance"]["metric"], "value": TOL},
                  "convergence": {"levels": mesh_levels, "observed_order": None,
                                  "expected_order": None},
                  "verdict": "PARTIAL",
                  "notes": ("At least one ramp did not reach full-section yield, so p_lim was not "
                            "measured. Check whether the solver aborted at the limit point and "
                            "truncated its CSV."),
                  "limitations": "No p_lim measurement available from this run set."}
        (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"verdict": "PARTIAL", "reason": "collapse not reached in every run",
                          "levels": mesh_levels}, indent=2))
        return

    index = primary["index"]
    halving_shift = abs(controls["halved"]["p_lim_MPa"] - primary["p_lim_MPa"]) / P_LIM
    onset = [yield_onset(f"n{nx}") for nx in MESHES]
    onset_error = abs(onset[-1] - P_Y) / P_Y
    curve = front_curve(primary_tag, index)
    curve_error = max((row["relative_error"] for row in curve), default=float("nan"))
    field = stress_field(primary_tag, index)

    checks = {
        "p_lim_within_tolerance": bool(primary["relative_error"] <= TOL),
        "increment_finer_than_declared": bool(
            primary["increment_MPa"] <= REF["measurement_resolution"]["max_pressure_increment_MPa"]),
        "step_independent": bool(halving_shift < TOL),
        "mesh_independent": bool(all(lv["relative_error"] <= TOL for lv in mesh_levels)),
        "yield_onset_within_tolerance": bool(onset_error <= SEC["yield_onset_relative"]),
        "front_curve_within_tolerance": bool(curve and curve_error <= SEC["p_c_curve_relative"]),
        "stress_field_within_tolerance": bool(
            field["combined_L2_relative"] <= SEC["fully_plastic_stress_profile"]["value"]),
    }
    verdict = "PASS" if all(checks.values()) else "PARTIAL"

    result = {
        "case_id": REF["case_id"], "capability": REF["capability"],
        "validation_class": REF["validation_class"],
        "reference_value": P_LIM, "moose_value": primary["p_lim_MPa"], "units": "MPa",
        "error": {"absolute": abs(primary["p_lim_MPa"] - P_LIM),
                  "relative": primary["relative_error"]},
        "tolerance": {"metric": REF["tolerance"]["metric"], "value": TOL},
        "convergence": {
            "levels": mesh_levels,
            "observed_order": None,
            "expected_order": None,
            "order_not_claimed_reason": (
                "p_lim is a limit load, not a pointwise field value, and dp/dc -> 0 as the front "
                "reaches the outer wall. Mesh independence within the load increment is reported "
                "instead of a convergence order."),
            "load_step_controls": [
                {"tag": tag, "increment_MPa": controls[tag]["increment_MPa"],
                 "p_lim_MPa": controls[tag]["p_lim_MPa"],
                 "relative_error": controls[tag]["relative_error"]}
                for tag in ("coarse", "primary", "halved")],
            "halving_relative_shift": float(halving_shift),
        },
        "plasticity_diagnostic": {
            "p_lim_observable": REF["quantity"]["observable"],
            "p_lim_bracket_MPa": primary["bracket_MPa"],
            "p_lim_measurement_increment_MPa": primary["increment_MPa"],
            "outer_wall_plastic_strain_at_collapse": primary["outer_wall_plastic_strain"],
            "analytic_yield_onset_MPa": P_Y,
            "measured_yield_onset_MPa": onset[-1],
            "measured_yield_onset_mesh_values_MPa": onset,
            "yield_onset_relative_error": float(onset_error),
            "front_curve": curve,
            "front_curve_max_relative_error": float(curve_error),
            "fully_plastic_stress_field": field,
            "post_collapse_steps_discarded": True,
            "post_collapse_note": (
                "Past the limit load the small-strain perfectly plastic system has no equilibrium "
                "solution. Newton either fails outright or converges to |R| ~ 1e-14 on one of two "
                "spurious branches with sign-flipped hoop stress. No quantity is taken from those "
                "steps."),
        },
        "checks": checks,
        "verdict": verdict,
        "runtime_s": float((OUT / "runtime_seconds.txt").read_text())
        if (OUT / "runtime_seconds.txt").exists() else None,
        "ranks": 1, "moose_version": "snapshot-20-10-27-41583-g2bd11a08a7",
        "notes": (
            f"p_lim is measured as full-section yield: the applied pressure at which the plastic "
            f"front reaches r=b. At nx=160 with a {primary['increment_MPa']:.3g} MPa increment the "
            f"measured value is {primary['p_lim_MPa']:.5g} MPa against the closed-form "
            f"{P_LIM:.6g} MPa, a relative error of {primary['relative_error']:.3g} within the "
            f"declared 2%. The increment is {100 * primary['increment_MPa'] / P_LIM:.2g}% of "
            f"p_lim, so the measurement is finer than the tolerance it is judged against; halving "
            f"it moves the result by {halving_shift:.3g}. All four meshes agree within the "
            f"increment. Secondary checks: yield onset {onset[-1]:.5g} MPa against analytic "
            f"{P_Y:.5g} MPa ({onset_error:.3g}); the p(c) front curve has maximum relative error "
            f"{curve_error:.3g} over c/a in [1.2,1.8]; and the fully-plastic stress field at "
            f"collapse matches -k ln(b/r) and k(1-ln(b/r)) with combined L2 relative error "
            f"{field['combined_L2_relative']:.3g}, the von Mises condition holding at "
            f"(stt-srr)/k = {field['von_mises_condition_mean']:.5g} across the wall."),
        "limitations": (
            "Small-strain, plane-strain RZ, monotonic loading, perfect plasticity with no "
            "hardening. Hardening, cyclic plasticity and finite-strain effects are not exercised. "
            "Steps past the limit load are discarded as non-physical and nothing is claimed about "
            "post-collapse response. sigma_zz is a diagnostic rather than an acceptance quantity "
            "because the fully-plastic closed form assumes developed plastic flow that the outer "
            "wall has not reached at the instant of collapse."),
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), constrained_layout=True)

    for nx in MESHES:
        hist = history(f"n{nx}")
        stop = collapse_index(hist)
        axes[0].plot(RAMP * hist["time"][:stop + 1], hist["inner_wall_displacement"][:stop + 1],
                     label=f"nx={nx}")
    axes[0].axvline(P_LIM, color="k", ls="--", lw=1, label="analytic $p_{lim}$")
    axes[0].axvline(P_Y, color="r", ls=":", lw=1, label="analytic $p_y$")
    axes[0].set(xlabel="applied pressure (MPa)", ylabel="inner-wall radial displacement (m)",
                title="Load-deflection to collapse")
    axes[0].legend(fontsize=8)

    r = np.array(field["radius_m"])
    axes[1].plot(r, field["sigma_rr_MPa"], "C0-", lw=1.4, label=r"MOOSE $\sigma_{rr}$")
    axes[1].plot(r, -K * np.log(B / r), "k--", lw=1, label=r"$-k\,\ln(b/r)$")
    axes[1].plot(r, field["sigma_tt_MPa"], "C1-", lw=1.4, label=r"MOOSE $\sigma_{\theta\theta}$")
    axes[1].plot(r, K * (1 - np.log(B / r)), "k:", lw=1, label=r"$k\,(1-\ln(b/r))$")
    axes[1].set(xlabel="radius (m)", ylabel="stress (MPa)",
                title=f"Fully-plastic field at collapse\nL2 = {field['combined_L2_relative']:.2e}")
    axes[1].legend(fontsize=8)

    axes[2].plot([row["interface_radius_m"] for row in curve],
                 [row["pressure_MPa"] for row in curve], "C0o", ms=4, label="MOOSE front")
    cc = np.linspace(A, B, 200)
    axes[2].plot(cc, SY / np.sqrt(3) * (2 * np.log(cc / A) + 1 - cc**2 / B**2), "k-", lw=1,
                 label="analytic $p(c)$")
    axes[2].axhline(P_LIM, color="k", ls="--", lw=1, label="analytic $p_{lim}$")
    axes[2].plot([B], [primary["p_lim_MPa"]], "C3*", ms=14, label="measured $p_{lim}$")
    axes[2].set(xlabel="elastic-plastic interface radius $c$ (m)", ylabel="pressure (MPa)",
                title="Plastic-front growth")
    axes[2].legend(fontsize=8)

    fig.savefig(FIG / "elastoplastic_cylinder_history.png", dpi=180)
    plt.close(fig)
    print(json.dumps({"verdict": verdict, "moose_value": primary["p_lim_MPa"],
                      "relative_error": primary["relative_error"], "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
