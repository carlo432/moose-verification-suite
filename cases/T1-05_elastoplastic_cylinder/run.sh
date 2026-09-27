#!/usr/bin/env bash
set -euo pipefail

CASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export PYTHONPATH="${PYTHONPATH:-}"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$CASE_DIR"
OUT_DIR="$CASE_DIR/out"
case "$OUT_DIR" in
  "$CASE_DIR/out") rm -rf "$OUT_DIR" ;;
  *) echo "Refusing to remove unexpected output path: $OUT_DIR" >&2; exit 2 ;;
esac
mkdir -p "$OUT_DIR" figures
start_time=$(date +%s.%N)

# p_lim is measured as the applied pressure at which the plastic front reaches
# the outer wall (full-section yield).  reference.json requires the load
# increment to be at most 0.4002 MPa, i.e. 0.5% of p_lim, so the measurement is
# four times finer than the 2% acceptance tolerance.  dt=0.002 gives 0.2 MPa.
#
# The ramp stops at 80.8 MPa, just past collapse.  Past the limit load the
# small-strain perfectly plastic system has no equilibrium solution: Newton
# either fails outright (nx=20 aborts at 81.4 MPa) or converges to |R| ~ 1e-14
# on one of two spurious branches with a sign-flipped hoop stress.  An abort
# also truncates the unflushed CSV, so the ramp deliberately stops short of it.
# verify.py discards every step at and after collapse regardless.
run_case() {
  # A non-convergence at the limit point is the physically correct outcome and
  # must not fail the sweep; verify.py reports any run that never collapsed.
  "$MOOSE_APP" "$@" || echo "  (solver stopped at the limit load -- expected)" >&2
}

for nx in 20 40 80 160; do
  run_case -i cylinder.i \
    Mesh/nx="$nx" \
    Executioner/dt=0.002 \
    Executioner/end_time=0.808 \
    Outputs/file_base="out/cylinder_n${nx}"
done

# Load-step controls at the finest mesh: the coarsest increment reference.json
# permits, and one half of the primary increment.  Acceptance requires p_lim to
# move by less than the tolerance when the increment is halved.
for tag_dt in coarse:0.004 halved:0.001; do
  tag=${tag_dt%%:*}
  dt=${tag_dt##*:}
  run_case -i cylinder.i \
    Mesh/nx=160 \
    Executioner/dt="$dt" \
    Executioner/end_time=0.808 \
    Outputs/file_base="out/cylinder_${tag}_n160"
done

date -u +%Y-%m-%dT%H:%M:%SZ > out/completed_utc.txt
end_time=$(date +%s.%N)
awk -v start="$start_time" -v end="$end_time" 'BEGIN { printf "%.3f\n", end-start }' > out/runtime_seconds.txt
python verify.py
