#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/sw_*.csv out/sw_*.log
start_time=$(date +%s.%N)
# Three dose profiles at three meshes. Uniform and linear lie inside the
# second-order FE space and must come out at round-off; only the quadratic
# profile has a genuine discretization error, so it carries the convergence study.
for nx in 8 16 32; do
  for pair in "uniform:1.0" "linear:y" "quadratic:y*y"; do
    tag=${pair%%:*}; dose=${pair##*:}
    "$MOOSE_APP" -i swelling_slab.i DOSE="$dose" Mesh/gen/nx=$nx Mesh/gen/ny=$nx \
      Outputs/file_base="out/sw_${tag}_n${nx}" --color off >"out/sw_${tag}_n${nx}.log" &
  done
done
wait
# Free-expansion invariant from the shipped seed: an unconstrained body under a
# uniform volumetric eigenstrain recovers the imposed volume change exactly and
# develops no stress.
"$MOOSE_APP" -i eigenstrain_seed.i Outputs/file_base=out/sw_freebody --color off >out/sw_freebody.log 2>&1 || true
end_time=$(date +%s.%N)
awk -v s="$start_time" -v e="$end_time" 'BEGIN{printf "%.3f\n", e-s}' > out/runtime_seconds.txt
python verify.py
