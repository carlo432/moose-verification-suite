#!/usr/bin/env python3
"""T3-23 -- dose-dependent swelling eigenstrain and the mismatch stress it drives.

Reclassified [E] -> [A].  The row previously claimed experimental validation
while its own reference block said "Declared illustrative 1%/dpa correlation;
external journal source not available in workspace".  A self-declared
correlation is not experimental data.  The swelling law is now an input, and
what is verified is the capability MOOSE actually performs: turning a
dose-dependent volumetric eigenstrain into a mismatch stress field.

Configuration: plane-strain slab, in-plane displacement restrained at both ends,
traction-free top.  With eps_xx = eps_zz = 0 and sigma_yy = 0 the elasticity
relations collapse to a pointwise result, sigma_xx = -E e(y)/(1-nu), so a dose
GRADIENT has an exact stress field and is a real test rather than an invariant.
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
P = REF["parameters"]
TOL = REF["tolerance"]["value"]
SEC = REF["secondary_tolerances"]
E, NU, S = P["youngs_modulus"], P["poissons_ratio"], P["volumetric_swelling_per_dpa"]
MESHES = REF["convergence"]["mesh_levels_nx"]
PROFILES = [("uniform", "1.0"), ("linear", "y"), ("quadratic", "y*y")]


def element_l2(tag: str, nx: int) -> float | None:
    """MOOSE's own element L2 norm against the closed-form function.

    A line-sampled norm cannot measure this: fixed sample points straddle the
    element boundaries of a discontinuous MONOMIAL field, which showed up as a
    spurious order of 1.78/1.53 where the element norm gives a clean 2.000.
    """
    path = OUT / f"sw_{tag}_n{nx}.csv"
    if not path.exists():
        return None
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    scale = E * S / (3.0 * (1.0 - NU))
    return float(rows[-1]["l2_error_sxx"]) / scale


def sample(tag: str, nx: int) -> dict | None:
    files = sorted(glob.glob(str(OUT / f"sw_{tag}_n{nx}_profile_*.csv")))
    if not files:
        return None
    with open(files[-1], newline="") as fh:
        rows = list(csv.DictReader(fh))
    y = np.array([float(r["y"]) for r in rows])
    get = lambda k: np.array([float(r[k]) for r in rows])
    sxx, syy, szz, dose = get("sxx"), get("syy"), get("szz"), get("dose")
    exact = -E * (S * dose / 3.0) / (1.0 - NU)
    scale = max(float(np.max(np.abs(exact))), 1e-30)
    return {"nx": nx, "y": y, "sxx": sxx, "syy": syy, "szz": szz, "dose": dose,
            "exact": exact, "scale": scale,
            "l2_relative": element_l2(tag, nx),
            "l2_line_sampled": float(np.sqrt(np.mean((sxx - exact) ** 2)) / scale),
            "linf_relative": float(np.max(np.abs(sxx - exact)) / scale),
            "szz_l2_relative": float(np.sqrt(np.mean((szz - exact) ** 2)) / scale),
            "syy_max_relative": float(np.max(np.abs(syy)) / scale)}


def public(d: dict) -> dict:
    return {k: v for k, v in d.items()
            if k not in ("y", "sxx", "syy", "szz", "dose", "exact", "scale")}


def main() -> None:
    FIG.mkdir(exist_ok=True)
    data = {tag: [s for nx in MESHES if (s := sample(tag, nx))] for tag, _ in PROFILES}

    quad = data["quadratic"]
    orders = []
    for a, b in zip(quad, quad[1:]):
        if a["l2_relative"] > 0 and b["l2_relative"] > 0:
            orders.append(float(np.log(a["l2_relative"] / b["l2_relative"])
                                / np.log(b["nx"] / a["nx"])))
    finest_quad = quad[-1]
    worst_syy = max(s["syy_max_relative"] for v in data.values() for s in v)

    checks = {
        "quadratic_within_tolerance": bool(finest_quad["l2_relative"] <= TOL),
        "uniform_exact": bool(data["uniform"][-1]["l2_relative"]
                              <= SEC["uniform_dose_exact"]["value"]),
        "linear_exact": bool(data["linear"][-1]["l2_relative"]
                             <= SEC["linear_dose_exact"]["value"]),
        "transverse_stress_zero": bool(worst_syy <= SEC["transverse_stress_zero"]["value"]),
        "quadratic_order": bool(orders and min(orders)
                                >= SEC["quadratic_observed_order"]["value"]),
    }
    verdict = "PASS" if all(checks.values()) else "PARTIAL"

    result = {
        "case_id": REF["case_id"], "capability": REF["capability"],
        "validation_class": REF["validation_class"],
        "reference_value": float(finest_quad["exact"][-1]),
        "moose_value": float(finest_quad["sxx"][-1]), "units": "stress",
        "error": {"absolute": abs(float(finest_quad["sxx"][-1] - finest_quad["exact"][-1])),
                  "relative": finest_quad["l2_relative"]},
        "tolerance": {"metric": REF["tolerance"]["metric"], "value": TOL},
        "convergence": {
            "levels": [public(s) for s in quad],
            "observed_order": min(orders) if orders else None,
            "observed_orders": orders,
            "expected_order": REF["convergence"]["expected_order"]},
        "swelling_diagnostic": {
            "reclassification": REF["reclassification"],
            "closed_form": REF["reference"]["formula"],
            "biaxial_modulus": P["biaxial_modulus"],
            "by_dose_profile": {tag: [public(s) for s in v] for tag, v in data.items()},
            "worst_transverse_stress_relative": worst_syy,
            "exactness_note": (
                "The uniform and linear dose profiles have exact solutions inside the second-order "
                "FE space, so their errors sit at round-off (order 1e-14) and confirm the "
                "eigenstrain is applied as declared rather than testing the discretization. Only "
                "the quadratic profile has a genuine discretization error, so it carries the "
                "convergence study and the headline tolerance."),
            "free_body_invariant": (
                "eigenstrain_seed.i is retained: an unconstrained body under a uniform volumetric "
                "eigenstrain recovers the imposed volume change and develops no stress."),
        },
        "checks": checks, "verdict": verdict,
        "runtime_s": float((OUT / "runtime_seconds.txt").read_text())
        if (OUT / "runtime_seconds.txt").exists() else None,
        "ranks": 1, "moose_version": "snapshot-20-10-27-41583-g2bd11a08a7",
        "notes": (
            f"Class changed from [E] to [A]: no sourced swelling-versus-dose correlation exists in "
            f"this workspace, and the previous row claimed experimental validation while its own "
            f"reference block recorded the correlation as illustrative. The swelling law is now a "
            f"declared input and the eigenstrain-to-stress mapping is verified against a closed "
            f"form. In a restrained plane-strain slab the mismatch stress is pointwise "
            f"sigma_xx = -E e(y)/(1-nu). A uniform dose reproduces it to "
            f"{data['uniform'][-1]['l2_relative']:.2e} and a linear dose to "
            f"{data['linear'][-1]['l2_relative']:.2e}, both at round-off because those solutions "
            f"lie in the FE space. A quadratic dose gradient, which does not, converges at order "
            f"{min(orders):.2f} to {finest_quad['l2_relative']:.2e} against the declared 1e-3. The "
            f"traction-free transverse stress stays at {worst_syy:.2e} of the in-plane stress "
            f"across every case, which is the equilibrium invariant the closed form rests on."),
        "limitations": (
            "The swelling correlation is a declared constitutive input, not experimental data: "
            "this verifies the eigenstrain-to-stress mapping, not a swelling law. Linear elastic, "
            "small strain, isotropic, no irradiation creep, no dose-rate or temperature "
            "dependence, and no void-nucleation physics. The suite now contains no [E] rows."),
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    for tag, _ in PROFILES:
        s = data[tag][-1]
        axes[0].plot(s["y"], s["sxx"], lw=1.4, label=f"MOOSE {tag}")
        axes[0].plot(s["y"], s["exact"], "k--", lw=0.8)
    axes[0].set(xlabel="y", ylabel=r"$\sigma_{xx}$",
                title="Mismatch stress vs $-Ee(y)/(1-\\nu)$ (dashed)")
    axes[0].legend(fontsize=8)
    axes[1].loglog([1.0 / s["nx"] for s in quad], [s["l2_relative"] for s in quad], "o-")
    axes[1].set(xlabel="element size", ylabel="relative $L_2$",
                title=f"Quadratic dose: order {min(orders):.2f}")
    fig.savefig(FIG / "swelling_mismatch_stress.png", dpi=170)
    plt.close(fig)
    print(json.dumps({"verdict": verdict, "checks": checks,
                      "quadratic_l2": finest_quad["l2_relative"],
                      "orders": orders, "worst_syy": worst_syy}, indent=2))


if __name__ == "__main__":
    main()
