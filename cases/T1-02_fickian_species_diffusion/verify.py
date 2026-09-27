#!/usr/bin/env python3
"""Verify finite-slab Fickian diffusion and no-flux mass conservation."""

from __future__ import annotations

import csv
import glob
import json
import math
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
FIG = ROOT / "figures"
REF = json.loads((ROOT / "reference.json").read_text())
D = REF["parameters"]["diffusivity_m2_per_s"]
L = REF["parameters"]["slab_length_m"]


def slab_exact(x: np.ndarray, t: float) -> np.ndarray:
    result = np.zeros_like(x, dtype=float)
    for n in range(1, 2000, 2):
        result += np.exp(-D * n * n * math.pi**2 * t / L**2) * np.sin(n * math.pi * x / L) / n
    return 4.0 / math.pi * result


def noflux_exact(x: np.ndarray, t: float) -> np.ndarray:
    return 1.0 + 0.2 * np.exp(-D * math.pi**2 * t / L**2) * np.cos(math.pi * x / L)


def latest_profile(base: str) -> tuple[np.ndarray, np.ndarray]:
    files = glob.glob(str(OUT / f"{base}_profile_*.csv"))
    if not files:
        raise FileNotFoundError(f"missing profile output for {base}")
    files.sort(key=lambda name: int(re.search(r"_(\d+)\.csv$", name).group(1)))
    with open(files[-1], newline="") as stream:
        rows = list(csv.DictReader(stream))
    rows.sort(key=lambda row: float(row["x"]))
    return (np.array([float(row["x"]) for row in rows]),
            np.array([float(row["c"]) for row in rows]))


def normalized_l2(x: np.ndarray, value: np.ndarray, reference: np.ndarray) -> float:
    return float(np.sqrt(np.trapezoid((value - reference) ** 2, x) / L))


def order(h: np.ndarray, error: np.ndarray) -> float:
    slope, _ = np.polyfit(np.log(h), np.log(error), 1)
    return float(slope)


def read_mass() -> tuple[np.ndarray, np.ndarray]:
    files = sorted(OUT.glob("noflux*.csv"))
    files = [p for p in files if "profile" not in p.name]
    if not files:
        raise FileNotFoundError("missing noflux postprocessor CSV")
    with files[0].open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    return (np.array([float(row["time"]) for row in rows]),
            np.array([float(row["mass"]) for row in rows]))


def main() -> None:
    times = [0.025, 0.05, 0.1]
    levels = [20, 40, 80, 160]
    tags = {0.025: "0025", 0.05: "005", 0.1: "01"}
    profiles = {}
    spatial_orders = {}
    errors_by_time = {}
    for time in times:
        errors = []
        for nx in levels:
            x, value = latest_profile(f"dirichlet_n{nx}_t{tags[time]}")
            profiles[(time, nx)] = (x, value)
            errors.append(normalized_l2(x, value, slab_exact(x, time)))
        errors_by_time[time] = errors
        spatial_orders[time] = order(1.0 / np.array(levels), np.array(errors))

    mass_time, mass = read_mass()
    # MOOSE emits a pre-IC row at t=0 for this postprocessor; it is zero before
    # the initial condition is applied and is not a physical conservation datum.
    physical = np.abs(mass) > 1e-12
    mass_time = mass_time[physical]
    mass = mass[physical]
    mass_drift = float(np.max(np.abs(mass - mass[0])) / abs(mass[0]))
    noflux_x, noflux_value = latest_profile("noflux")
    noflux_profile_error = normalized_l2(noflux_x, noflux_value, noflux_exact(noflux_x, 0.1))
    finest_error = errors_by_time[0.1][-1]
    x025_value = float(np.interp(0.25, profiles[(0.1, 160)][0], profiles[(0.1, 160)][1]))
    ref_x025 = float(slab_exact(np.array([0.25]), 0.1)[0])

    spatial_ok = all(abs(p - 2.0) <= REF["convergence"]["spatial_order_tolerance"] for p in spatial_orders.values())
    verdict = "PASS" if finest_error <= REF["tolerance"]["value"] and spatial_ok and mass_drift <= REF["convergence"]["mass_conservation_relative_tolerance"] else "FAIL"
    levels_out = [{"h": 1.0 / nx, "nx": nx, "normalized_l2_error": errors_by_time[0.1][i]} for i, nx in enumerate(levels)]
    result = {
        "case_id": REF["case_id"],
        "capability": REF["capability"],
        "validation_class": REF["validation_class"],
        "reference_value": REF["reference"]["value"],
        "moose_value": x025_value,
        "units": "normalized concentration",
        "error": {"absolute": abs(x025_value - ref_x025), "relative": abs(x025_value - ref_x025) / abs(ref_x025)},
        "tolerance": {"metric": REF["tolerance"]["metric"], "value": REF["tolerance"]["value"]},
        "profile": {"metric": "maximum normalized L2 concentration error over three Dirichlet comparison times", "value": max(errors_by_time[t][-1] for t in times), "times_s": times, "finest_mesh_nx": 160},
        "convergence": {"levels": levels_out, "observed_order": spatial_orders[0.1], "expected_order": 2.0, "orders_by_time": {str(t): p for t, p in spatial_orders.items()}},
        "mass_conservation": {"metric": "relative drift in integral of c over the no-flux slab", "initial_mass": float(mass[0]), "final_mass": float(mass[-1]), "relative_drift": mass_drift, "tolerance": 1e-10, "noflux_profile_error": noflux_profile_error},
        "verdict": verdict,
        "runtime_s": float((OUT / "runtime_seconds.txt").read_text()) if (OUT / "runtime_seconds.txt").exists() else None,
        "ranks": 1,
        "moose_version": "snapshot-20-10-27-41583-g2bd11a08a7",
        "date": "2026-08-02",
        "notes": "Dirichlet profiles use the odd-sine finite-slab series; the separate Neumann cosine mode supplies the mass-conservation check.",
        "limitations": "One-dimensional constant-D transport with prescribed boundaries; no advection, reaction, multicomponent coupling, or concentration-dependent diffusivity.",
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    FIG.mkdir(exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for time in times:
        x, value = profiles[(time, 160)]
        axes[0, 0].plot(x, value, label=f"MOOSE t={time:g}")
        axes[0, 0].plot(x, slab_exact(x, time), "--", label=f"series t={time:g}")
    axes[0, 0].set(xlabel="x (m)", ylabel="c/c0", title="Finite-slab Dirichlet profiles")
    axes[0, 0].legend(fontsize=8, ncol=2)
    for time in times:
        axes[0, 1].loglog(1.0 / np.array(levels), errors_by_time[time], "o-", label=f"t={time:g}, p={spatial_orders[time]:.2f}")
    axes[0, 1].invert_xaxis()
    axes[0, 1].set(xlabel="h (m)", ylabel="L2 error", title="Spatial convergence")
    axes[0, 1].legend(fontsize=8)
    axes[1, 0].plot(mass_time, mass, label="integral(c)")
    axes[1, 0].axhline(mass[0], color="k", linestyle="--", linewidth=1)
    axes[1, 0].set(xlabel="t (s)", ylabel="total species mass", title=f"No-flux conservation (drift={mass_drift:.2e})")
    axes[1, 1].plot(noflux_x, noflux_value, label="MOOSE")
    axes[1, 1].plot(noflux_x, noflux_exact(noflux_x, 0.1), "--", label="cosine exact")
    axes[1, 1].set(xlabel="x (m)", ylabel="c/c0", title="No-flux cosine mode at t=0.1 s")
    axes[1, 1].legend()
    fig.savefig(FIG / "fickian_diffusion_convergence.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
