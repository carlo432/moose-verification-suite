#!/usr/bin/env python3
"""T1-03 -- convective and radiative thermal boundary conditions.

Acceptance is carried by the 2-D `fin.i` model, whose sides carry
`ConvectiveHeatFluxBC`.  It previously rested on `fin1d.i`, a 1-D
`Diffusion` + `CoefReaction` model in which convection is a volumetric sink
rather than a boundary condition -- that verified a different equation and
never exercised the BC.  `fin1d.i` is now only an independent cross-check.

The 1-D fin formula is itself an approximation to the 2-D problem, exact only
as the cross-section Biot number Bi = h w /(2k) goes to zero.  Holding
m = sqrt(2h/(kw)) fixed by scaling h with w keeps the analytic target
unchanged while Bi falls as w^2, so the residual gap must vanish at second
order in w.  That is what the fin-limit study measures, and it is what the
earlier unexplained "order deficit" actually was.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
FIG = ROOT / "figures"
REF = json.loads((ROOT / "reference.json").read_text())
FP = REF["parameters"]["fin"]
RP = REF["parameters"]["radiative_lumped"]
FL = REF["fin_limit_study"]
TOL = REF["tolerance"]["value"]
SEC = REF["secondary_tolerances"]

K = FP["conductivity_W_per_mK"]
LEN = FP["length_m"]
TB = FP["base_temperature_K"]
TINF = FP["ambient_temperature_K"]
THETA_B = TB - TINF
MESHES = REF["convergence"]["mesh_levels_nx"]


def last_row(name: str) -> dict[str, float]:
    with (OUT / f"{name}.csv").open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    return {k: float(v) for k, v in rows[-1].items()}


def fin_analytic(w: float, h: float) -> tuple[float, float]:
    """1-D straight fin, adiabatic tip, per unit out-of-plane depth."""
    perim, area = 2.0, w
    m = np.sqrt(h * perim / (K * area))
    t_tip = TINF + THETA_B / np.cosh(m * LEN)
    q_base = np.sqrt(h * perim * K * area) * THETA_B * np.tanh(m * LEN)
    return float(t_tip), float(q_base)


def fin_measured(name: str, w: float, h: float) -> dict[str, float]:
    """Tip temperature and heat rate from the 2-D solve.

    The heat rate is taken as the convective loss through the top and bottom
    faces, not the base diffusive flux: the Dirichlet base meets the convective
    sides at a re-entrant corner where the gradient is singular, so the base
    integral converges below first order.  The two must agree by conservation,
    which is checked separately.
    """
    r = last_row(name)
    q_loss = h * ((r["top_temperature_integral"] - TINF * LEN)
                  + (r["bottom_temperature_integral"] - TINF * LEN))
    return {"t_tip": r["tip_temperature"], "q_convective_loss": q_loss,
            "q_base_flux": abs(r["base_heat_rate"])}


def radiative_reference(t: float) -> float:
    factor = (RP["density_kg_per_m3"] * RP["specific_heat_J_per_kgK"] * RP["length_m"] / 2.0
              / (RP["emissivity"] * RP["stefan_boltzmann_W_per_m2K4"]))
    t0, tinf = RP["initial_temperature_K"], RP["ambient_temperature_K"]

    def elapsed(temp: float) -> float:
        return factor * quad(lambda q: 1.0 / (q**4 - tinf**4), temp, t0,
                             epsabs=1e-12, epsrel=1e-12)[0]

    return float(brentq(lambda temp: elapsed(temp) - t, tinf + 1e-9, t0))


def observed_order(hs: list[float], errs: list[float]) -> float | None:
    good = [(h, e) for h, e in zip(hs, errs) if e > 0]
    if len(good) < 2:
        return None
    lh = np.log(np.array([g[0] for g in good]))
    le = np.log(np.array([g[1] for g in good]))
    return float(np.polyfit(lh, le, 1)[0])


def main() -> None:
    FIG.mkdir(exist_ok=True)
    w0, h0 = FP["width_m"], FP["h_W_per_m2K"]
    t_tip_ref, q_ref = fin_analytic(w0, h0)

    # --- mesh convergence at the reference geometry -------------------------
    mesh_levels = []
    for nx in MESHES:
        m = fin_measured(f"fin_n{nx}", w0, h0)
        mesh_levels.append({
            "nx": nx,
            "t_tip_K": m["t_tip"],
            "t_tip_relative_error": abs(m["t_tip"] - t_tip_ref) / t_tip_ref,
            "q_convective_loss": m["q_convective_loss"],
            "q_relative_error": abs(m["q_convective_loss"] - q_ref) / q_ref,
            "q_base_flux": m["q_base_flux"],
            "conservation_imbalance": abs(m["q_base_flux"] - m["q_convective_loss"])
            / m["q_convective_loss"]})
    finest = mesh_levels[-1]

    # --- fin-limit study ----------------------------------------------------
    width_levels = []
    for w, h in zip(FL["widths"], FL["heat_transfer_coefficients"]):
        tag = str(w).replace(".", "p")
        ref_tip, ref_q = fin_analytic(w, h)
        m = fin_measured(f"finw_{tag}", w, h)
        width_levels.append({
            "width_m": w, "h_W_per_m2K": h,
            "biot_number": h * w / (2 * K),
            "t_tip_K": m["t_tip"], "analytic_t_tip_K": ref_tip,
            "t_tip_relative_error": abs(m["t_tip"] - ref_tip) / ref_tip,
            "q_convective_loss": m["q_convective_loss"], "analytic_q": ref_q,
            "q_relative_error": abs(m["q_convective_loss"] - ref_q) / ref_q})
    width_order = observed_order([lv["width_m"] for lv in width_levels],
                                 [lv["t_tip_relative_error"] for lv in width_levels])
    width_q_order = observed_order([lv["width_m"] for lv in width_levels],
                                   [lv["q_relative_error"] for lv in width_levels])
    monotone = all(width_levels[i + 1]["t_tip_relative_error"]
                   < width_levels[i]["t_tip_relative_error"]
                   for i in range(len(width_levels) - 1))

    # --- radiative lumped capacitance ---------------------------------------
    rad_levels, rad_max_error = [], 0.0
    for tag, dt in (("05", 0.5), ("025", 0.25), ("0125", 0.125)):
        with (OUT / f"radiative_dt{tag}.csv").open(newline="") as fh:
            rows = list(csv.DictReader(fh))
        times = np.array([float(r["time"]) for r in rows])
        temps = np.array([float(r[[c for c in rows[0] if "emp" in c][0]]) for r in rows])
        keep = times > 0
        ref = np.array([radiative_reference(t) for t in times[keep]])
        err = float(np.max(np.abs(temps[keep] - ref) / ref))
        rad_levels.append({"dt_s": dt, "max_relative_error": err})
        rad_max_error = max(rad_max_error, err)
    sampled = {}
    with (OUT / "radiative_dt0125.csv").open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    tcol = [c for c in rows[0] if "emp" in c][0]
    for t_target in RP["comparison_times_s"]:
        row = min(rows, key=lambda r: abs(float(r["time"]) - t_target))
        sampled[str(t_target)] = {"moose_K": float(row[tcol]),
                                  "analytic_K": radiative_reference(t_target)}

    # --- 1-D cross-check (no acceptance) ------------------------------------
    cross = {}
    try:
        r = last_row("fin1d_160")
        tip = [v for k, v in r.items() if "tip" in k.lower()]
        cross = {"fin1d_tip_theta": tip[0] if tip else None,
                 "analytic_theta_tip": THETA_B / float(np.cosh(FP["m_per_m"] * LEN)),
                 "role": "independent confirmation of the analytic fin solution; carries no acceptance"}
    except Exception as exc:  # pragma: no cover - diagnostic only
        cross = {"error": str(exc)}

    checks = {
        "t_tip_within_tolerance": bool(finest["t_tip_relative_error"] <= TOL),
        "heat_rate_within_tolerance": bool(finest["q_relative_error"] <= TOL),
        "energy_balance_closes": bool(finest["conservation_imbalance"]
                                      <= SEC["energy_balance_imbalance"]["value"]),
        "fin_limit_monotone": bool(monotone),
        "fin_limit_order": bool(width_order is not None
                                and abs(width_order - FL["expected_order_in_width"])
                                <= FL["order_tolerance"]),
        "radiative_within_tolerance": bool(rad_max_error <= TOL),
    }
    verdict = "PASS" if all(checks.values()) else "PARTIAL"

    result = {
        "case_id": REF["case_id"], "capability": REF["capability"],
        "validation_class": REF["validation_class"],
        "reference_value": t_tip_ref, "moose_value": finest["t_tip_K"], "units": "K",
        "error": {"absolute": abs(finest["t_tip_K"] - t_tip_ref),
                  "relative": finest["t_tip_relative_error"]},
        "tolerance": {"metric": REF["tolerance"]["metric"], "value": TOL},
        "convergence": {
            "levels": mesh_levels,
            "observed_order": observed_order([1.0 / nx for nx in MESHES],
                                             [lv["t_tip_relative_error"] for lv in mesh_levels]),
            "expected_order": REF["convergence"]["expected_order"],
            "order_note": ("T_tip converges to the 2-D answer, which sits a fixed distance from the "
                           "1-D analytic, so the error against the analytic plateaus rather than "
                           "falling. That plateau is fin model form and is removed by the width "
                           "study, not by mesh refinement."),
        },
        "convective_bc_diagnostic": {
            "model": "fin.i, 2-D, ConvectiveHeatFluxBC on the top and bottom faces",
            "reference_geometry": {"width_m": w0, "h_W_per_m2K": h0,
                                   "biot_number": h0 * w0 / (2 * K)},
            "analytic_t_tip_K": t_tip_ref, "analytic_q": q_ref,
            "finest_t_tip_K": finest["t_tip_K"],
            "finest_q_convective_loss": finest["q_convective_loss"],
            "finest_q_base_flux": finest["q_base_flux"],
            "conservation_imbalance": finest["conservation_imbalance"],
            "heat_rate_source": ("total convective loss over the top and bottom faces; the base "
                                 "diffusive flux integral is reported alongside as a conservation "
                                 "check but is not used for acceptance because the Dirichlet base "
                                 "meets the convective sides at a singular corner"),
            "fin_limit_study": {
                "levels": width_levels,
                "observed_order_in_width_t_tip": width_order,
                "observed_order_in_width_q": width_q_order,
                "expected_order": FL["expected_order_in_width"],
                "monotone": monotone,
                "interpretation": FL["purpose"]},
        },
        "radiative_diagnostic": {"timestep_levels": rad_levels,
                                 "max_relative_error": rad_max_error,
                                 "sampled": sampled},
        "one_dimensional_cross_check": cross,
        "checks": checks, "verdict": verdict,
        "runtime_s": float((OUT / "runtime_seconds.txt").read_text())
        if (OUT / "runtime_seconds.txt").exists() else None,
        "ranks": 1, "moose_version": "snapshot-20-10-27-41583-g2bd11a08a7",
        "notes": (
            f"Acceptance is on the 2-D ConvectiveHeatFluxBC model. At the reference geometry "
            f"(w={w0}, Bi={h0*w0/(2*K):.4g}) the finest mesh gives T_tip={finest['t_tip_K']:.6f} K "
            f"against the analytic {t_tip_ref:.6f} K, a relative error of "
            f"{finest['t_tip_relative_error']:.3g}, and a fin heat rate of "
            f"{finest['q_convective_loss']:.6f} against {q_ref:.6f} "
            f"({finest['q_relative_error']:.3g}); the base flux integral agrees with the convective "
            f"loss to {finest['conservation_imbalance']:.3g}, so energy closes. Refining the mesh "
            f"does not reduce the gap to the analytic value because it is fin model form, not "
            f"discretization: holding m fixed while shrinking the width drives Bi as w^2 and the "
            f"T_tip deviation falls with observed order {width_order:.3g} in w against the expected "
            f"{FL['expected_order_in_width']}. The radiative lumped history matches the integrated "
            f"ODE to {rad_max_error:.3g} across three timesteps."),
        "limitations": (
            "Constant properties, prescribed emissivity, no view factors or internal generation. "
            "The fin comparison is against the 1-D fin approximation, which is why the residual at "
            "finite width is nonzero by construction; the width study quantifies it rather than "
            "removing it from the reference geometry."),
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), constrained_layout=True)
    axes[0].loglog([1.0 / nx for nx in MESHES],
                   [lv["t_tip_relative_error"] for lv in mesh_levels], "o-", label="$T_{tip}$")
    axes[0].loglog([1.0 / nx for nx in MESHES],
                   [lv["conservation_imbalance"] for lv in mesh_levels], "s-",
                   label="energy imbalance")
    axes[0].set(xlabel="element size $1/n_x$", ylabel="relative error",
                title="Mesh convergence at $w=0.1$")
    axes[0].legend(fontsize=8)

    ws = [lv["width_m"] for lv in width_levels]
    es = [lv["t_tip_relative_error"] for lv in width_levels]
    axes[1].loglog(ws, es, "o-", label="$T_{tip}$ vs 1-D fin")
    axes[1].loglog(ws, [es[0] * (w / ws[0]) ** 2 for w in ws], "k--", lw=1, label="$w^2$")
    axes[1].set(xlabel="fin width $w$ (m)", ylabel="relative deviation",
                title=f"Fin limit: order {width_order:.2f} in $w$")
    axes[1].legend(fontsize=8)

    with (OUT / "radiative_dt0125.csv").open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    tcol = [c for c in rows[0] if "emp" in c][0]
    tt = np.array([float(r["time"]) for r in rows])
    axes[2].plot(tt, [float(r[tcol]) for r in rows], "-", label="MOOSE")
    axes[2].plot(tt[tt > 0][::40], [radiative_reference(t) for t in tt[tt > 0][::40]], "ko",
                 ms=4, label="analytic")
    axes[2].set(xlabel="time (s)", ylabel="temperature (K)",
                title=f"Radiative lumped, max err {rad_max_error:.1e}")
    axes[2].legend(fontsize=8)
    fig.savefig(FIG / "convective_radiative_convergence.png", dpi=180)
    plt.close(fig)
    print(json.dumps({"verdict": verdict, "checks": checks,
                      "t_tip_err": finest["t_tip_relative_error"],
                      "q_err": finest["q_relative_error"],
                      "width_order": width_order}, indent=2))


if __name__ == "__main__":
    main()
