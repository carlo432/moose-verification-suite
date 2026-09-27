#!/usr/bin/env python3
"""Single definition of the T1-09 coarsening observables.

This module exists because the same quantity was implemented twice -- once in
the verifier, once in the reaper -- and the two drifted apart. L = A*sigma/E_grad
is derived from the quantity being measured and is NOT monotonic, and every
consumer has to handle that identically. Three separate failures came from one
copy of the logic missing a guard the other had:

  1. the fit window opened during spinodal decomposition, because L falls
     THROUGH the "ten interface widths" threshold on its way down;
  2. the reaper treated a still-decomposing run as "past the peak";
  3. the reaper included the t = 0 row, whose random-noise gradient energy
     (~11635) exceeds everything in a short run, putting argmax at row 0 and
     making every fresh seed look finished.

Nothing should compute L, the coarsening branch, or the window anywhere else.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

CASE = Path(__file__).resolve().parent

# geometry and material, read off coarsening.i
BOX, KAPPA, W = 480.0, 40.0, 1.0
AREA = BOX * BOX
DELTA = math.sqrt(2.0 * KAPPA / W)          # equilibrium tanh interface width
SIGMA_GRAD = 2.0 * KAPPA / (3.0 * DELTA)    # gradient half of sigma per unit length
L_MIN, L_MAX = 10.0 * DELTA, BOX / 4.0      # the declared window, from reference.json
MIN_PEAK_LAG = 3        # rows the E_grad peak must be behind the last row
MIN_TIME = 50.0         # well past phase separation; L there is ~50 and rising


def domain_size(e_grad: float) -> float:
    """L = box area / total interface length, interface length = E_grad/sigma_grad."""
    return AREA * SIGMA_GRAD / e_grad


def read_series(seed: int):
    """(t, e, mass) for one seed, cleaned.

    Drops t = 0 (white-noise IC, gradient energy far above the spinodal peak),
    drops rows that do not parse (a seed may be killed mid-write), and keeps the
    LAST row for each time so a --recover replay supersedes what it re-ran
    instead of the fit seeing the same interval twice.
    """
    f = CASE / "out" / f"coarsen_s{seed}.csv"
    if not f.exists():
        return [], [], []
    dedup = {}
    with f.open() as fh:
        for r in csv.DictReader(fh):
            try:
                t = float(r["time"])
                e = float(r["gradient_energy_integral"])
                m = float(r["mass"])
            except (TypeError, ValueError, KeyError):
                continue
            if t > 0 and e > 0:
                dedup[round(t, 9)] = (t, e, m)
    rows = [dedup[k] for k in sorted(dedup)]
    return ([r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows])


def coarsening_start(e: list[float]) -> int:
    """Index of the gradient-energy peak: phase separation ends, coarsening begins."""
    return max(range(len(e)), key=lambda i: e[i]) if e else 0


def on_coarsening_branch(t: list[float], e: list[float]) -> bool:
    """True only when the run is genuinely coarsening, not still decomposing."""
    if len(e) < MIN_PEAK_LAG + 2:
        return False
    return coarsening_start(e) < len(e) - MIN_PEAK_LAG and t[-1] > MIN_TIME


def current_L(seed: int) -> float | None:
    """L now, or None if the seed is not yet on the coarsening branch.

    This is what the reaper asks. Returning None rather than a number is the
    point: a fresh seed has a huge, meaningless L and must never be reaped.
    """
    t, e, _ = read_series(seed)
    if not on_coarsening_branch(t, e):
        return None
    return domain_size(e[-1])


def window(t: list[float], e: list[float]):
    """The declared fit window: L in [L_MIN, L_MAX], coarsening branch only."""
    i = coarsening_start(e)
    return [(a, b) for a, b in zip(t[i:], e[i:]) if L_MIN <= domain_size(b) <= L_MAX]


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "L":
        v = current_L(int(sys.argv[2]))
        print("0" if v is None else f"{v:.2f}")
    else:
        for s in range(10):
            t, e, _ = read_series(s)
            v = current_L(s)
            print(f"s{s}: n={len(t):5d} t={(t[-1] if t else 0):8.2f} "
                  f"branch={on_coarsening_branch(t, e)} "
                  f"L={'-' if v is None else f'{v:.2f}'}")
