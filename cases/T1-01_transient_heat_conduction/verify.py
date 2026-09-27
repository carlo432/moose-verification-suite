#!/usr/bin/env python3
"""Verify T1-01 profiles and write result.json plus a convergence figure."""

from __future__ import annotations

import csv
import glob
import json
import math
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.special import erf


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
FIG = ROOT / "figures"
REF = json.loads((ROOT / "reference.json").read_text())
TI = REF["parameters"]["initial_temperature_K"]
TS = REF["parameters"]["surface_temperature_K"]
ALPHA = REF["parameters"]["thermal_diffusivity_m2_per_s"]
LENGTH = REF["parameters"]["domain_length_m"]


def exact(x: np.ndarray, t: float, shift: float = 0.0) -> np.ndarray:
    return TS + (TI - TS) * erf(x / (2.0 * np.sqrt(ALPHA * (t + shift))))


def profile(base: str) -> tuple[np.ndarray, np.ndarray]:
    files = glob.glob(str(OUT / f"{base}_profile_*.csv"))
    if not files:
        raise FileNotFoundError(f"no LineValueSampler output for {base}")
    files.sort(key=lambda name: int(re.search(r"_(\d+)\.csv$", name).group(1)))
    with open(files[-1], newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows or "x" not in rows[0] or "T" not in rows[0]:
        raise ValueError(f"unexpected profile columns in {files[-1]}: {rows[0].keys() if rows else []}")
    rows.sort(key=lambda row: float(row["x"]))
    x = np.array([float(row["x"]) for row in rows])
    temperature = np.array([float(row["T"]) for row in rows])
    return x, temperature


def normalized_l2(x: np.ndarray, value: np.ndarray, reference: np.ndarray) -> float:
    numerator = np.sqrt(np.trapezoid((value - reference) ** 2, x) / LENGTH)
    return float(numerator / abs(TS - TI))


def observed_order(h: np.ndarray, errors: np.ndarray) -> float:
    slope, _ = np.polyfit(np.log(h), np.log(errors), 1)
    return float(slope)


def spatial_studies():
    times = [0.0625, 0.125, 0.25]
    levels = [20, 40, 80, 160]
    all_data = {}
    orders = {}
    for time in times:
        errors = []
        for nx in levels:
            tag = {0.0625: "00625", 0.125: "0125", 0.25: "025"}[time]
            x, value = profile(f"step_n{nx}_t{tag}")
            err = normalized_l2(x, value, exact(x, time))
            errors.append(err)
            all_data[(time, nx)] = (x, value)
        errors = np.array(errors)
        orders[time] = observed_order(4.0 / np.array(levels), errors)
    return times, levels, all_data, orders


def temporal_studies():
    dts = [0.03, 0.015, 0.0075, 0.00375]
    results = {}
    for scheme in ("implicit-euler", "crank-nicolson"):
        errors = []
        for dt in dts:
            tag = {0.03: "0030", 0.015: "0015", 0.0075: "00075", 0.00375: "000375"}[dt]
            x, value = profile(f"time_{scheme}_dt{tag}")
            errors.append(normalized_l2(x, value, exact(x, 0.24, shift=0.01)))
        results[scheme] = {
            "dts": dts,
            "errors": errors,
            "observed_order": observed_order(np.array(dts), np.array(errors)),
        }
    return results


def main() -> None:
    if 4.0 * math.sqrt(ALPHA * REF["parameters"]["end_time_s"]) >= LENGTH:
        raise AssertionError("semi-infinite-domain front check failed")

    times, levels, data, spatial_orders = spatial_studies()
    temporal = temporal_studies()
    finest_x, finest_value = data[(0.25, 160)]
    finest_error = normalized_l2(finest_x, finest_value, exact(finest_x, 0.25))
    x1_value = float(np.interp(1.0, finest_x, finest_value))
    reference_x1 = float(exact(np.array([1.0]), 0.25)[0])
    relative_x1_error = abs(x1_value - reference_x1) / abs(reference_x1)

    spatial_levels = []
    for nx in levels:
        err = normalized_l2(data[(0.25, nx)][0], data[(0.25, nx)][1], exact(data[(0.25, nx)][0], 0.25))
        spatial_levels.append({"h": 4.0 / nx, "nx": nx, "normalized_l2_error": err})

    expected_space = REF["convergence"]["expected_order"]
    order_tol = REF["convergence"]["spatial_order_tolerance"]
    expected_be = REF["convergence"]["temporal"]["backward_euler_expected_order"]
    expected_cn = REF["convergence"]["temporal"]["crank_nicolson_expected_order"]
    temporal_ok = (
        abs(temporal["implicit-euler"]["observed_order"] - expected_be) <= 0.2
        and abs(temporal["crank-nicolson"]["observed_order"] - expected_cn) <= 0.2
    )
    spatial_ok = all(abs(order - expected_space) <= order_tol for order in spatial_orders.values())
    verdict = "PASS" if finest_error <= REF["tolerance"]["value"] and spatial_ok and temporal_ok else "FAIL"

    result = {
        "case_id": REF["case_id"],
        "capability": REF["capability"],
        "validation_class": REF["validation_class"],
        "reference_value": REF["reference"]["value"],
        "moose_value": x1_value,
        "units": "K",
        "error": {"absolute": abs(x1_value - reference_x1), "relative": relative_x1_error},
        "tolerance": {"metric": REF["tolerance"]["metric"], "value": REF["tolerance"]["value"]},
        "profile": {
            "metric": "maximum normalized L2 error over the three comparison times, normalized by |T_s-T_i|",
            "value": max(normalized_l2(data[(time, 160)][0], data[(time, 160)][1], exact(data[(time, 160)][0], time)) for time in times),
            "times_s": times,
            "finest_mesh_nx": 160,
        },
        "convergence": {
            "levels": spatial_levels,
            "observed_order": spatial_orders[0.25],
            "expected_order": expected_space,
            "orders_by_time": {str(time): order for time, order in spatial_orders.items()},
        },
        "temporal_convergence": temporal,
        "verdict": verdict,
        "runtime_s": None,
        "ranks": 1,
        "moose_version": "snapshot-20-10-27-41583-g2bd11a08a7",
        "date": "2026-08-02",
        "notes": "Spatial study uses the surface-step problem; temporal order study uses the same similarity solution initialized at physical time 0.01 s to avoid a time-integrator order measurement being dominated by the t=0 boundary incompatibility. The temporal mesh is nx=640 so its finest time levels are not spatial-error limited.",
        "limitations": "Constant properties, one-dimensional finite interval, fixed far boundary approximation to a semi-infinite solid; no convection, radiation, nonlinear conductivity, or phase change.",
    }
    runtime_file = OUT / "runtime_seconds.txt"
    if runtime_file.exists():
        result["runtime_s"] = float(runtime_file.read_text())
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    FIG.mkdir(exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for time in times:
        x, value = data[(time, 160)]
        axes[0, 0].plot(x, value, label=f"MOOSE t={time:g} s")
        axes[0, 0].plot(x, exact(x, time), "--", linewidth=1, label=f"erf t={time:g} s")
    axes[0, 0].set(xlabel="x (m)", ylabel="T (K)", title="Surface-step profiles, nx=160")
    axes[0, 0].legend(fontsize=8, ncol=2)
    for time in times:
        errs = [normalized_l2(data[(time, nx)][0], data[(time, nx)][1], exact(data[(time, nx)][0], time)) for nx in levels]
        axes[0, 1].loglog(4.0 / np.array(levels), errs, "o-", label=f"t={time:g} s (p={spatial_orders[time]:.2f})")
    axes[0, 1].invert_xaxis()
    axes[0, 1].set(xlabel="mesh spacing h (m)", ylabel="normalized L2 error", title="Spatial convergence")
    axes[0, 1].legend(fontsize=8)
    for scheme, values in temporal.items():
        axes[1, 0].loglog(values["dts"], values["errors"], "o-", label=f"{scheme} (p={values['observed_order']:.2f})")
    axes[1, 0].invert_xaxis()
    axes[1, 0].set(xlabel="dt (s)", ylabel="normalized L2 error", title="Temporal convergence, physical t=0.25 s")
    axes[1, 0].legend(fontsize=8)
    axes[1, 1].axis("off")
    axes[1, 1].text(0.02, 0.9, f"Verdict: {verdict}\nmax profile error: {result['profile']['value']:.3e}\nT(1 m, 0.25 s): {x1_value:.6f} K\nanalytic: {reference_x1:.6f} K", va="top", family="monospace")
    fig.savefig(FIG / "transient_heat_convergence.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
