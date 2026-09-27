#!/usr/bin/env python3
"""Verify steady reaction–diffusion profiles and fitted penetration lengths."""

from __future__ import annotations

import csv
import glob
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
FIG = ROOT / "figures"
REF = json.loads((ROOT / "reference.json").read_text())


def exact(x: np.ndarray, length: float, lam: float = 1.0) -> np.ndarray:
    return np.cosh((length - x) / lam) / np.cosh(length / lam)


def latest_profile(base: str) -> tuple[np.ndarray, np.ndarray]:
    files = glob.glob(str(OUT / f"{base}_profile_*.csv"))
    if not files:
        raise FileNotFoundError(f"missing profile output for {base}")
    files.sort(key=lambda name: int(re.search(r"_(\d+)\.csv$", name).group(1)))
    with open(files[-1], newline="") as stream:
        rows = list(csv.DictReader(stream))
    rows.sort(key=lambda row: float(row["x"]))
    return np.array([float(row["x"]) for row in rows]), np.array([float(row["c"]) for row in rows])


def fit_lambda(x: np.ndarray, value: np.ndarray, length: float) -> float:
    def model(xv, lam):
        return exact(xv, length, lam)
    fitted, _ = curve_fit(model, x, value, p0=[1.0], bounds=(0.01, 100.0), maxfev=10000)
    return float(fitted[0])


def l2(x: np.ndarray, value: np.ndarray, ref: np.ndarray) -> float:
    return float(np.sqrt(np.trapezoid((value - ref) ** 2, x) / length_global))


def main() -> None:
    global length_global
    lengths = {"05": 0.5, "2": 2.0, "10": 10.0}
    meshes = [40, 80, 160, 320]
    data = {}
    errors = {}
    lambdas = {}
    orders = {}
    lambda_errors = {}
    for tag, length in lengths.items():
        length_global = length
        errors[tag] = []
        lambdas[tag] = []
        for nx in meshes:
            x, value = latest_profile(f"regime_{tag}_n{nx}")
            data[(tag, nx)] = (x, value)
            errors[tag].append(l2(x, value, exact(x, length)))
            lambdas[tag].append(fit_lambda(x, value, length))
        orders[tag] = float(np.polyfit(np.log(1.0 / np.array(meshes)), np.log(errors[tag]), 1)[0])
        lambda_errors[tag] = abs(np.array(lambdas[tag]) - 1.0)

    finest_profile = max(errors[tag][-1] for tag in lengths)
    finest_lambda_relative = max(lambda_errors[tag][-1] for tag in lengths)
    scalar_x, scalar_value = data[("2", 320)]
    scalar = float(np.interp(1.0, scalar_x, scalar_value))
    scalar_ref = float(exact(np.array([1.0]), 2.0)[0])
    orders_ok = all(abs(value - 2.0) <= REF["convergence"]["spatial_order_tolerance"] for value in orders.values())
    verdict = "PASS" if finest_profile <= REF["tolerance"]["value"] and finest_lambda_relative <= REF["convergence"]["lambda_relative_tolerance"] and orders_ok else "FAIL"
    result = {
        "case_id": REF["case_id"], "capability": REF["capability"], "validation_class": REF["validation_class"],
        "reference_value": REF["reference"]["value"], "moose_value": scalar, "units": "normalized concentration",
        "error": {"absolute": abs(scalar - scalar_ref), "relative": abs(scalar - scalar_ref) / abs(scalar_ref)},
        "tolerance": {"metric": REF["tolerance"]["metric"], "value": REF["tolerance"]["value"]},
        "profile": {"metric": "maximum normalized L2 profile error over L/lambda = 0.5, 2, 10", "value": finest_profile, "regimes": list(lengths), "finest_mesh_nx": 320},
        "convergence": {"levels": [{"nx": nx, "h_by_lambda": 2.0 / nx, "error_L_over_lambda_2": errors["2"][i]} for i, nx in enumerate(meshes)], "observed_order": orders["2"], "expected_order": 2.0, "orders_by_regime": orders},
        "penetration_length": {"reference_lambda": 1.0, "fitted_lambda_by_regime": {tag: vals for tag, vals in lambdas.items()}, "finest_relative_errors": {tag: float(lambda_errors[tag][-1]) for tag in lengths}, "maximum_finest_relative_error": float(finest_lambda_relative)},
        "verdict": verdict, "runtime_s": float((OUT / "runtime_seconds.txt").read_text()) if (OUT / "runtime_seconds.txt").exists() else None, "ranks": 1, "moose_version": "snapshot-20-10-27-41583-g2bd11a08a7", "date": "2026-08-02",
        "notes": "Each regime is solved with the same D and k while L is varied; lambda is fitted independently from the full numerical profile.",
        "limitations": "Steady one-dimensional linear sink with constant diffusivity; no advection, nonlinear kinetics, multicomponent effects, or concentration-dependent properties."
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    FIG.mkdir(exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for tag, length in lengths.items():
        x, value = data[(tag, 320)]
        axes[0, 0].plot(x, value, label=f"MOOSE L/lambda={tag}")
        axes[0, 0].plot(x, exact(x, length), "--", linewidth=1)
        axes[0, 1].loglog(1.0 / np.array(meshes), errors[tag], "o-", label=f"L/lambda={tag}, p={orders[tag]:.2f}")
    axes[0, 0].set(xlabel="x (m)", ylabel="c/cs", title="Reaction–diffusion profiles")
    axes[0, 0].legend(fontsize=8)
    axes[0, 1].invert_xaxis()
    axes[0, 1].set(xlabel="h/lambda", ylabel="normalized L2 error", title="Mesh convergence")
    axes[0, 1].legend(fontsize=8)
    for tag, length in lengths.items():
        axes[1, 0].semilogx(1.0 / np.array(meshes), lambdas[tag], "o-", label=f"L/lambda={tag}")
    axes[1, 0].axhline(1.0, color="k", linestyle="--")
    axes[1, 0].invert_xaxis()
    axes[1, 0].set(xlabel="h/lambda", ylabel="fitted lambda", title="Recovered penetration length")
    axes[1, 0].legend()
    axes[1, 1].axis("off")
    axes[1, 1].text(0.02, 0.9, f"Verdict: {verdict}\nmax profile error: {finest_profile:.3e}\nmax lambda error: {finest_lambda_relative:.3e}", va="top", family="monospace")
    fig.savefig(FIG / "reaction_diffusion_convergence.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
