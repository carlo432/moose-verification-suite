#!/usr/bin/env python3
"""Verify plane-Poiseuille profile, friction product, and mass conservation."""

from __future__ import annotations

import csv
import glob
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
FIG = ROOT / "figures"
REF = json.loads((ROOT / "reference.json").read_text())


def latest(base: str, suffix: str) -> list[dict[str, str]]:
    files = glob.glob(str(OUT / f"{base}_{suffix}_*.csv"))
    if not files:
        raise FileNotFoundError(f"missing {suffix} output for {base}")
    files.sort(key=lambda name: int(re.search(r"_(\d+)\.csv$", name).group(1)))
    with open(files[-1], newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    meshes = [2, 4, 8, 16]
    errors = []
    ratios = []
    flow_balance = []
    f_re = []
    profiles = {}
    for ny in meshes:
        rows = latest(f"ny{ny}", "profile")
        rows.sort(key=lambda row: float(row["y"]))
        y = np.array([float(row["y"]) for row in rows])
        u = np.array([float(row["u"]) for row in rows])
        ref = 1.0 - y**2
        errors.append(float(np.sqrt(np.mean((u - ref) ** 2))))
        avg = float(np.mean(u))
        ratios.append(float(np.max(u) / avg))
        profiles[ny] = (y, u)
        pp = latest(f"ny{ny}", "") if False else []
        with (OUT / f"ny{ny}.csv").open(newline="") as stream:
            post = list(csv.DictReader(stream))[-1]
        inlet = float(post["inlet_flow"])
        outlet = float(post["outlet_flow"])
        flow_balance.append(abs(abs(inlet) - abs(outlet)) / max(abs(inlet), 1e-14))
        prow = latest(f"ny{ny}", "pressure_line")
        prow.sort(key=lambda row: float(row["x"]))
        x = np.array([float(row["x"]) for row in prow])
        p = np.array([float(row["pressure"]) for row in prow])
        slope = float(np.polyfit(x, p, 1)[0])
        f_re.append(32.0 * abs(slope) / (0.5 * avg))

    positive = np.array(errors) > 1e-14
    observed = float(np.polyfit(np.log(1.0 / np.array(meshes)[positive]), np.log(np.array(errors)[positive]), 1)[0])
    finest_error = errors[-1]
    finest_ratio = ratios[-1]
    finest_fre = f_re[-1]
    finest_balance = flow_balance[-1]
    profile_ok = finest_error <= REF["tolerance"]["value"]
    ratio_ok = abs(finest_ratio - 1.5) / 1.5 <= 0.01
    fre_ok = abs(finest_fre - 96.0) / 96.0 <= 0.01
    balance_ok = finest_balance <= 1e-8
    order_ok = abs(observed - 2.0) <= REF["convergence"]["spatial_order_tolerance"]
    verdict = "PASS" if profile_ok and ratio_ok and fre_ok and balance_ok and order_ok else "FAIL"
    result = {
        "case_id": REF["case_id"], "capability": REF["capability"], "validation_class": REF["validation_class"],
        "reference_value": REF["reference"]["value"], "moose_value": float(np.max(profiles[16][1])), "units": "m/s",
        "error": {"absolute": finest_error, "relative": finest_error},
        "tolerance": {"metric": REF["tolerance"]["metric"], "value": REF["tolerance"]["value"]},
        "profile": {"metric": "normalized L2 error of u(y) over y in [-1,1]", "value": finest_error, "mesh_levels_ny": meshes},
        "convergence": {"levels": [{"ny": ny, "profile_error": errors[i]} for i, ny in enumerate(meshes)], "observed_order": observed, "expected_order": 2.0},
        "flow_diagnostics": {"max_to_average_ratio": finest_ratio, "reference_ratio": 1.5, "fRe": finest_fre, "reference_fRe": 96.0, "mass_balance_relative": finest_balance, "all_ratios": ratios, "all_fRe": f_re, "all_mass_balance": flow_balance},
        "verdict": verdict, "runtime_s": float((OUT / "runtime_seconds.txt").read_text()) if (OUT / "runtime_seconds.txt").exists() else None, "ranks": 1, "moose_version": "snapshot-20-10-27-41583-g2bd11a08a7", "date": "2026-08-02",
        "notes": "The numerical fRe is computed from the fitted centerline pressure gradient and the integrated mean velocity using the plane-channel hydraulic-diameter convention; inlet/outlet mass flow is checked independently.",
        "limitations": "Steady incompressible plane channel only; no entrance, turbulence, compressibility, or circular-pipe geometry."
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    FIG.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for ny, (y, u) in profiles.items():
        axes[0].plot(y, u, "o-", label=f"ny={ny}")
    yfine = np.linspace(-1, 1, 200)
    axes[0].plot(yfine, 1 - yfine**2, "k--", label="analytic")
    axes[0].set(xlabel="y/h", ylabel="u", title="Plane-Poiseuille velocity profile")
    axes[0].legend()
    axes[1].loglog(1 / np.array(meshes), errors, "o-", label=f"L2 p={observed:.2f}")
    axes[1].invert_xaxis()
    axes[1].set(xlabel="1/ny", ylabel="normalized L2 error", title=f"Convergence; fRe={finest_fre:.2f}")
    axes[1].legend()
    fig.savefig(FIG / "plane_poiseuille_convergence.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
