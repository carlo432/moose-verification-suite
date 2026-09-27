#!/usr/bin/env python3
"""Regression guard: the reaper and the verifier must agree about L.

They disagreed three times in this case, each time because one copy of the
logic had a guard the other lacked. Both now go through coarsening_lib; this
asserts they still do, and pins the specific behaviours that were wrong before.
"""
import subprocess
import sys

import coarsening_lib as cl

fails = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        fails.append(name)


print("coarsening_lib consistency")

# 1. the reaper's shell entry point returns exactly what the library says
for s in range(10):
    out = subprocess.run([sys.executable, "coarsening_lib.py", "L", str(s)],
                         capture_output=True, text=True, cwd=cl.CASE).stdout.strip()
    lib = cl.current_L(s)
    want = "0" if lib is None else f"{lib:.2f}"
    check(f"reaper entry point agrees for seed {s}", out == want, f"{out} vs {want}")

# 2. t = 0 must never enter the series: the white-noise IC has gradient energy
#    far above the spinodal peak and putting it in makes argmax land on row 0
for s in range(10):
    t, _, _ = cl.read_series(s)
    if t:
        check(f"seed {s} excludes t=0", t[0] > 0, f"first t={t[0]:.4g}")
        break

# 3. a still-decomposing run is never reapable, however large its L looks
synth_t = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
synth_e = [1.0, 5.0, 20.0, 90.0, 400.0, 1800.0]     # monotonically rising
check("rising E_grad is not on the coarsening branch",
      not cl.on_coarsening_branch(synth_t, synth_e))

# 4. a genuinely coarsening run past MIN_TIME is
synth_t2 = [60.0, 80.0, 100.0, 130.0, 170.0, 220.0]
synth_e2 = [1800.0, 1500.0, 1200.0, 1000.0, 850.0, 700.0]
check("falling E_grad past MIN_TIME is on the coarsening branch",
      cl.on_coarsening_branch(synth_t2, synth_e2))

# 5. the window endpoints are the declared ones
check("L window is [10 delta, box/4]",
      abs(cl.L_MIN - 10 * cl.DELTA) < 1e-12 and abs(cl.L_MAX - cl.BOX / 4) < 1e-12,
      f"[{cl.L_MIN:.4f}, {cl.L_MAX:.1f}]")

# 6. duplicate times from a --recover replay collapse to one row
for s in range(10):
    t, _, _ = cl.read_series(s)
    if t:
        check(f"seed {s} times are strictly increasing after dedup",
              all(b > a for a, b in zip(t, t[1:])))
        break

print()
if fails:
    print(f"{len(fails)} FAILED: " + ", ".join(fails))
    sys.exit(1)
print("all consistency checks passed")
