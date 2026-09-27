#!/usr/bin/env python3
"""T3-25 -- Kobayashi anisotropic dendrite scored on the far-field domain.

dendrite.i solved a 0.7 box with insulated walls, so the rejected latent heat
piled up ahead of the tip and the tip decelerated across the measurement
window instead of reaching a steady velocity.  dendrite_far.i solves the same
physics on a quarter-symmetry domain with a Dirichlet far field holding the
melt at its initial undercooling; see domain_correction in reference.json.

The measurement window in tip position, [0.45, 0.58], and every tolerance are
unchanged from the original declaration.
"""
from __future__ import annotations

import csv, glob, json, re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
REF = json.loads((ROOT / "reference.json").read_text())
WIN = REF["measurement_window"]["tip_position"]
TOL = REF["tolerance"]["value"]
SEC = REF["secondary_tolerances"]
GUARD = SEC["far_field_undisturbed"]["value"]
PROBE_X = SEC["far_field_undisturbed"]["probe_x"]


def series(tag: str):
    """Tip position against solution time, plus the far-field guard trace.

    Times come from the solution CSV, not from step_index * dt: the executioner
    cuts dt back on a failed solve and the startup steps are not 0.001.
    """
    hist = OUT / f"far_{tag}.csv"
    if not hist.exists():
        return None
    rows = list(csv.DictReader(hist.open()))
    times = [float(r["time"]) for r in rows]
    far = [float(r["T_far_field"]) for r in rows]

    # NB: "far_<tag>_axis_*.csv" also matches "far_<tag>_axis_T_*.csv", so the
    # w frames must be selected by an explicit index pattern. Globbing both into
    # one list silently concatenates them and every tip reading past the real
    # frame count is taken off a temperature profile.
    wpat = re.compile(rf"far_{re.escape(tag)}_axis_\d+\.csv$")
    frames = sorted(f for f in glob.glob(str(OUT / f"far_{tag}_axis_*.csv"))
                    if wpat.search(f))
    tframes = sorted(glob.glob(str(OUT / f"far_{tag}_axis_T_*.csv")))
    t, x, g = [], [], []
    for k, path in enumerate(frames):
        if k >= len(times):
            break
        prof = list(csv.DictReader(open(path, newline="")))
        xs = np.array([float(a["x"]) for a in prof])
        ws = np.array([float(a["w"]) for a in prof])
        below = np.where(ws < 0.5)[0]
        if len(below) == 0 or below[0] == 0:
            continue
        j = below[0]
        t.append(times[k])
        x.append(xs[j - 1] + (xs[j] - xs[j - 1]) * (ws[j - 1] - 0.5) / (ws[j - 1] - ws[j]))
        # melt temperature ahead of the tip, at the declared probe station
        if k < len(tframes):
            tp = list(csv.DictReader(open(tframes[k], newline="")))
            txs = np.array([float(a["x"]) for a in tp])
            tts = np.array([float(a["T"]) for a in tp])
            g.append(float(np.interp(PROBE_X, txs, tts)))
        else:
            g.append(float("nan"))
    return np.array(t), np.array(x), np.array(g)


def measure(tag: str):
    s = series(tag)
    if s is None:
        return None
    t, x, g = s
    if len(t) < 4:
        return None
    sel = (x >= WIN[0]) & (x <= WIN[1])
    rec = {"tag": tag, "frames": int(len(t)),
           "tip_range": [float(x.min()), float(x.max())],
           "window_points": int(sel.sum())}
    if sel.sum() < 4:
        rec["note"] = "window not covered"
        return rec
    # far field is judged up to the end of the window, not over the whole run
    upto = np.arange(len(t)) <= np.where(sel)[0][-1]
    slope, intercept = np.polyfit(t[sel], x[sel], 1)
    pred = slope * t[sel] + intercept
    r2 = 1.0 - float(((x[sel] - pred) ** 2).sum() / ((x[sel] - x[sel].mean()) ** 2).sum())
    local = np.gradient(x[sel], t[sel])
    rec.update({
        "V_tip": float(slope), "fit_R2": r2,
        "local_velocity_min": float(local.min()),
        "local_velocity_max": float(local.max()),
        "local_velocity_ratio": float(local.max() / max(local.min(), 1e-30)),
        "far_field_max_T_at_probe": float(np.nanmax(np.abs(g[upto]))),
        "far_field_probe_x": PROBE_X,
        "_t": t, "_x": x, "_sel": sel,
    })
    return rec


def public(d):
    return {k: v for k, v in d.items() if not k.startswith("_")}


def main() -> int:
    tes = REF["convergence"]["undercooling_levels_Te"]
    under = {}
    for te in tes:
        m = measure(f"Te{te}")
        if m and "V_tip" in m:
            under[te] = m

    meshes = {}
    for nx, tag in ((96, "n96"), (144, "Te1.0"), (192, "n192")):
        m = measure(tag)
        if m and "V_tip" in m:
            meshes[nx] = m

    incomplete = [tag for tag in [f"Te{t}" for t in tes] + ["n96", "n192"]
                  if (measure(tag) or {}).get("V_tip") is None]

    result = {
        "case_id": REF["case_id"], "capability": REF["capability"],
        "validation_class": REF["validation_class"],
        "reference_value": None, "units": "length/time",
        "tolerance": {"metric": REF["tolerance"]["metric"], "value": TOL},
    }

    if incomplete:
        result.update({
            "moose_value": None, "error": {"absolute": None, "relative": None},
            "verdict": "PARTIAL",
            "checks": {"monotonic_undercooling": False, "mesh_independent": False,
                       "steady_tip_velocity": False, "far_field_undisturbed": False},
            "notes": ("Runs have not reached the measurement window: "
                      + ", ".join(incomplete)),
        })
        print(json.dumps(result, indent=2))
        return 0

    vs = [under[te]["V_tip"] for te in tes]
    monotonic = all(b > a for a, b in zip(vs, vs[1:]))
    mesh_vs = [m["V_tip"] for m in meshes.values()]
    mesh_spread = (max(mesh_vs) - min(mesh_vs)) / float(np.mean(mesh_vs))
    worst_r2 = min(v["fit_R2"] for v in under.values())
    worst_guard = max(v["far_field_max_T_at_probe"] for v in list(under.values()) + list(meshes.values()))

    checks = {
        "monotonic_undercooling": bool(monotonic),
        "mesh_independent": bool(mesh_spread <= TOL),
        "steady_tip_velocity": bool(worst_r2 >= SEC["tip_velocity_linearity"]["value"]),
        "far_field_undisturbed": bool(worst_guard <= GUARD),
    }
    result.update({
        "moose_value": meshes[144]["V_tip"],
        "error": {"absolute": None, "relative": mesh_spread},
        "convergence": {
            "levels": [{"nx": nx, **public(m)} for nx, m in meshes.items()],
            "mesh_relative_spread": mesh_spread,
            "observed_order": None, "expected_order": None},
        "dendrite_diagnostic": {
            "model": ("ACInterfaceKobayashi1/2 with InterfaceOrientationMaterial on a "
                      "quarter-symmetry domain with a Dirichlet far field."),
            "measurement_window": REF["measurement_window"],
            "domain_correction": REF["domain_correction"],
            "interface_width_note": REF["interface_width_note"],
            "by_undercooling": {f"T_e={te}": public(v) for te, v in under.items()},
            "far_field_guard": {"probe_x": PROBE_X, "tolerance": GUARD,
                                "worst_observed": worst_guard},
            "worst_fit_R2": worst_r2,
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
