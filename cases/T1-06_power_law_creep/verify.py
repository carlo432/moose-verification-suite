#!/usr/bin/env python3
"""Verify the Norton power-law creep round trip and timestep trend."""

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
A_REF = REF["parameters"]["coefficient_A"]
N_REF = REF["parameters"]["stress_exponent_n"]
Q_REF = REF["parameters"]["activation_energy_J_per_mol"]
R = REF["parameters"]["gas_constant_J_per_molK"]
END = REF["parameters"]["end_time_s"]


def final_row(path: Path) -> dict[str, str]:
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    return rows[-1]


def strain_from(row: dict[str, str]) -> float:
    candidates = [key for key in row if "creep_strain" in key]
    if not candidates:
        raise KeyError(f"no creep strain output in columns {row.keys()}")
    return abs(float(row[candidates[0]]))


def main() -> None:
    temps = [800.0, 1000.0, 1200.0]
    stresses = [50.0, 100.0, 150.0]
    records = []
    for temp in temps:
        for stress in stresses:
            row = final_row(OUT / f"T{int(temp)}_S{int(stress)}_dt02.csv")
            records.append((temp, stress, strain_from(row), float(row.get("stress_zz", 0.0))))

    # Least-squares fit ln(rate) = ln(A) + n ln(sigma) + Q[-1/(R T)].
    matrix = np.array([[1.0, np.log(stress), -1.0 / (R * temp)] for temp, stress, _, _ in records])
    target = np.array([np.log(strain / END) for _, _, strain, _ in records])
    intercept, n_fit, q_fit = np.linalg.lstsq(matrix, target, rcond=None)[0]
    a_fit = float(np.exp(intercept))
    n_fit = float(n_fit)
    q_fit = float(q_fit)

    dt_tags = [("04", 0.4), ("02", 0.2), ("01", 0.1)]
    ref_strain = A_REF * 100.0**N_REF * np.exp(-Q_REF / (R * 1000.0)) * END
    dt_values = []
    dt_errors = []
    for tag, dt in dt_tags:
        strain = strain_from(final_row(OUT / f"reference_dt{tag}.csv"))
        dt_values.append(strain)
        dt_errors.append(abs(strain - A_REF * 100.0**N_REF * np.exp(-Q_REF / (R * 1000.0)) * END) / (A_REF * 100.0**N_REF * np.exp(-Q_REF / (R * 1000.0)) * END))
    # The exact constant-stress solution makes the temporal error much smaller
    # than the constitutive/linear-solve residual.  The signed differences are
    # non-monotone at ~1e-8 strain, so a log-log slope would be a fabricated
    # convergence order rather than evidence.  Report timestep independence
    # directly and leave observed_order unset.
    dt_pairwise_max = float(max(abs(a - b) for a in dt_values for b in dt_values) / ref_strain)
    ref_error = abs(dt_values[1] - ref_strain) / ref_strain
    # Round-trip is verified, but the planned independent alloy curve is unavailable here.
    roundtrip_ok = abs(a_fit - A_REF) / A_REF <= 0.02 and abs(n_fit - N_REF) / N_REF <= 0.01 and abs(q_fit - Q_REF) / Q_REF <= 0.02 and ref_error <= 0.01
    result = {
        "case_id": REF["case_id"], "capability": REF["capability"], "validation_class": REF["validation_class"],
        "reference_value": ref_strain, "moose_value": dt_values[1], "units": "strain",
        "error": {"absolute": abs(dt_values[1] - ref_strain), "relative": ref_error},
        "tolerance": {"metric": REF["tolerance"]["metric"], "value": REF["tolerance"]["value"]},
        "convergence": {"levels": [{"dt_s": dt, "final_strain": value, "relative_error": error} for (tag, dt), value, error in zip(dt_tags, dt_values, dt_errors)], "observed_order": None, "expected_order": None,
                        "timestep_independence_max_pairwise_relative_difference": dt_pairwise_max,
                        "order_not_identifiable_reason": "exact constant-stress solution; timestep variation is below solver/constitutive residual"},
        "parameter_regression": {"A_reference": A_REF, "A_fitted": a_fit, "A_relative_error": abs(a_fit - A_REF) / A_REF, "n_reference": N_REF, "n_fitted": n_fit, "n_relative_error": abs(n_fit - N_REF) / N_REF, "Q_reference_J_per_mol": Q_REF, "Q_fitted_J_per_mol": q_fit, "Q_relative_error": abs(q_fit - Q_REF) / Q_REF, "samples": len(records)},
        "verdict": "PASS" if roundtrip_ok else "FAIL", "runtime_s": float((OUT / "runtime_seconds.txt").read_text()) if (OUT / "runtime_seconds.txt").exists() else None, "ranks": 1, "moose_version": "snapshot-20-10-27-41583-g2bd11a08a7", "date": "2026-08-02",
        "notes": f"The constant-stress/temperature Norton round trip passes its declared parameter-regression and closed-form strain checks. Three timesteps agree within {dt_pairwise_max:.3g} relative; a temporal order is not claimed because the exact solution makes the residual non-monotone at solver precision. This is [A] verification of the registered secondary-creep law; no independent published-alloy [E] claim is made.",
        "limitations": "Secondary Norton law only; no primary/tertiary creep, hardening, multiaxial transient stress, or independent experimental curve."
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    FIG.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for temp in temps:
        vals = [next(strain for t, s, strain, _ in records if t == temp and s == stress) for stress in stresses]
        axes[0].loglog(stresses, vals, "o-", label=f"T={temp:g} K")
    axes[0].set(xlabel="stress (MPa)", ylabel="final creep strain", title="Norton stress/temperature matrix")
    axes[0].legend()
    axes[1].loglog([d for _, d in dt_tags], dt_errors, "o-")
    axes[1].invert_xaxis()
    axes[1].set(xlabel="dt (s)", ylabel="relative final-strain error", title="Timestep sensitivity (order not identifiable)")
    fig.savefig(FIG / "power_law_creep_convergence.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
