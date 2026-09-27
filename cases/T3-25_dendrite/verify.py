#!/usr/bin/env python3
"""T3-25 -- solidification and dendrite growth (Kobayashi anisotropic phase field).

Built on phase_field/tests/anisotropic_interfaces/kobayashi.i, which is a real
anisotropic dendrite model -- ACInterfaceKobayashi1/2 plus
InterfaceOrientationMaterial -- replacing the planar finite-volume smoke test
that had no dendrite observable at all.  The seed also suppressed per-timestep
output entirely, so no tip history could be extracted from it.

Result: the dendrite grows and the tip velocity increases monotonically with
undercooling, but the case does NOT reach a steady-state tip velocity, so it is
reported PARTIAL.  See the diagnosis below.
"""

from __future__ import annotations

import csv
import glob
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
FIG = ROOT / "figures"
REF = json.loads((ROOT / "reference.json").read_text())
WIN = REF["measurement_window"]["tip_position"]
TOL = REF["tolerance"]["value"]
SEC = REF["secondary_tolerances"]
DT = 0.001
SEED_X = 0.35


def tip_series(tag: str) -> tuple[np.ndarray, np.ndarray]:
    times, tips = [], []
    for k, path in enumerate(sorted(glob.glob(str(OUT / f"dend_{tag}_axis_*.csv")))):
        with open(path, newline="") as fh:
            rows = list(csv.DictReader(fh))
        x = np.array([float(a["x"]) for a in rows])
        w = np.array([float(a["w"]) for a in rows])
        below = np.where(w < 0.5)[0]
        if len(below) == 0 or below[0] == 0:
            continue
        j = below[0]
        times.append((k + 1) * DT)
        tips.append(x[j - 1] + (x[j] - x[j - 1]) * (w[j - 1] - 0.5) / (w[j - 1] - w[j]))
    return np.array(times), np.array(tips)


def measure(tag: str) -> dict | None:
    t, x = tip_series(tag)
    if len(t) < 4:
        return None
    sel = (x >= WIN[0]) & (x <= WIN[1])
    if sel.sum() < 4:
        return {"tag": tag, "frames": len(t), "window_points": int(sel.sum()),
                "note": "window not covered"}
    slope, intercept = np.polyfit(t[sel], x[sel], 1)
    pred = slope * t[sel] + intercept
    r2 = 1.0 - float(((x[sel] - pred) ** 2).sum() / ((x[sel] - x[sel].mean()) ** 2).sum())
    local = np.gradient(x[sel], t[sel])
    return {"tag": tag, "frames": len(t), "window_points": int(sel.sum()),
            "V_tip": float(slope), "fit_R2": r2,
            "local_velocity_min": float(local.min()),
            "local_velocity_max": float(local.max()),
            "local_velocity_ratio": float(local.max() / max(local.min(), 1e-30)),
            "tip_range": [float(x.min()), float(x.max())],
            "_t": t, "_x": x, "_sel": sel}


def public(d: dict) -> dict:
    return {k: v for k, v in d.items() if not k.startswith("_")}


def main() -> None:
    FIG.mkdir(exist_ok=True)
    under = {te: measure(f"Te{te}") for te in REF["convergence"]["undercooling_levels_Te"]}
    under = {k: v for k, v in under.items() if v and "V_tip" in v}
    meshes = {}
    for nx, tag in ((64, "n64"), (96, "Te1.0"), (128, "n128")):
        m = measure(tag)
        if m and "V_tip" in m:
            meshes[nx] = m

    vs = [v["V_tip"] for v in under.values()]
    monotonic = all(b > a for a, b in zip(vs, vs[1:]))
    mesh_vs = [m["V_tip"] for m in meshes.values()]
    mesh_spread = ((max(mesh_vs) - min(mesh_vs)) / float(np.mean(mesh_vs))
                   if len(mesh_vs) > 1 else None)
    worst_r2 = min(v["fit_R2"] for v in under.values())
    worst_ratio = max(v["local_velocity_ratio"] for v in under.values())

    checks = {
        "monotonic_undercooling": bool(monotonic),
        "mesh_independent": bool(mesh_spread is not None and mesh_spread <= TOL),
        "steady_tip_velocity": bool(worst_r2 >= SEC["tip_velocity_linearity"]["value"]),
    }
    verdict = "PASS" if all(checks.values()) else "PARTIAL"

    result = {
        "case_id": REF["case_id"], "capability": REF["capability"],
        "validation_class": REF["validation_class"],
        "reference_value": None,
        "moose_value": meshes.get(96, {}).get("V_tip"), "units": "length/time",
        "error": {"absolute": None, "relative": mesh_spread},
        "tolerance": {"metric": REF["tolerance"]["metric"], "value": TOL},
        "convergence": {
            "levels": [{"nx": nx, **public(m)} for nx, m in meshes.items()],
            "mesh_relative_spread": mesh_spread,
            "observed_order": None, "expected_order": None},
        "dendrite_diagnostic": {
            "model": ("ACInterfaceKobayashi1/2 with InterfaceOrientationMaterial -- a genuine "
                      "anisotropic dendrite model, replacing a planar finite-volume smoke test that "
                      "had no dendrite observable."),
            "measurement_window": REF["measurement_window"],
            "interface_width_note": REF["interface_width_note"],
            "by_undercooling": {f"T_e={te}": public(v) for te, v in under.items()},
            "why_partial": (
                "The tip does not reach a steady velocity, so V_tip is not the quantity LGK theory "
                "describes. At the lowest undercooling the local tip velocity DECELERATES from 14.1 "
                "to 1.6 across the measurement window, and the straight-line fit gives R^2 = "
                f"{worst_r2:.3f} against the declared {SEC['tip_velocity_linearity']['value']}. The "
                "faster runs look linear only because they cross the same window in less time. The "
                "cause is the domain: it is 0.7 across with insulated outer boundaries, so the "
                "latent heat the tip rejects has nowhere to go and the melt ahead of the tip warms, "
                "steadily reducing the driving force."),
            "what_would_fix_it": (
                "A larger domain with a far-field temperature boundary condition holding the melt at "
                "the initial undercooling, so the tip reaches steady growth before the thermal field "
                "interacts with the wall. The tip currently travels from 0.43 to 0.65 in a domain "
                "whose wall is at 0.7."),
            "what_does_hold": (
                f"Tip velocity increases strictly with undercooling "
                + ", ".join(f"{v['V_tip']:.2f} at T_e={te}" for te, v in under.items())
                + (f", and is mesh independent to {mesh_spread:.3g} across nx = "
                   + ", ".join(str(n) for n in meshes) if mesh_spread is not None else "")
                + ", so the anisotropic phase-field machinery itself is behaving."),
        },
        "checks": checks, "verdict": verdict,
        "ranks": 1, "moose_version": "snapshot-20-10-27-41583-g2bd11a08a7",
        "notes": (
            f"Anisotropic Kobayashi dendrite. The growth direction, the monotonic undercooling trend "
            f"and mesh independence all behave: V_tip is "
            + ", ".join(f"{v['V_tip']:.2f} at T_e={te}" for te, v in under.items())
            + (f" and varies by {mesh_spread:.3g} across meshes. " if mesh_spread is not None else ". ")
            + f"The case remains PARTIAL because the tip never reaches a steady velocity: in the "
            f"declared window the local tip velocity falls by a factor of {worst_ratio:.1f} at the "
            f"lowest undercooling, giving a fit R^2 of {worst_r2:.3f} against the declared "
            f"{SEC['tip_velocity_linearity']['value']}. That is a finite-domain artefact -- the "
            f"insulated 0.7-wide box traps the rejected latent heat -- not a phase-field failure, "
            f"and no tip-velocity number is claimed as a steady-state value."),
        "limitations": (
            "No steady-state tip velocity, so no LGK comparison, quantitative or otherwise. Two "
            "dimensional, pure-substance thermal dendrite with no solute field. The Kobayashi "
            "kinetic coefficient is not mapped to a physical alloy, so even a converged V_tip would "
            "have no absolute reference here. Only the primary <100> arm is measured."),
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    for te, v in under.items():
        axes[0].plot(v["_t"], v["_x"], lw=1.3, label=f"$T_e$={te}")
        axes[0].plot(v["_t"][v["_sel"]], v["_x"][v["_sel"]], "k.", ms=3)
    axes[0].axhspan(WIN[0], WIN[1], color="0.92", zorder=0)
    axes[0].set(xlabel="time", ylabel="tip position", title="Tip advance (shaded = window)")
    axes[0].legend(fontsize=8)
    for te, v in under.items():
        axes[1].plot(v["_x"][v["_sel"]], np.gradient(v["_x"][v["_sel"]], v["_t"][v["_sel"]]),
                     "o-", ms=3, label=f"$T_e$={te}")
    axes[1].set(xlabel="tip position", ylabel="local tip velocity",
                title="Not steady: velocity decays across the window")
    axes[1].legend(fontsize=8)
    fig.savefig(FIG / "dendrite_tip.png", dpi=170)
    plt.close(fig)
    print(json.dumps({"verdict": verdict, "checks": checks,
                      "V_tip": {str(k): round(v["V_tip"], 3) for k, v in under.items()},
                      "mesh_spread": mesh_spread, "worst_R2": worst_r2}, indent=2))


if __name__ == "__main__":
    main()
