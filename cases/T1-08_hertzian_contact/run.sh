#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/hz_*.csv out/hz_*.e out/hz_*.log
start_time=$(date +%s.%N)
# Mesh refinement and a penalty sweep. Each of the 10 displacement increments is
# an independent (F, a, p0) comparison, since F is measured rather than assumed.
for lvl in 0 1 2; do
  "$MOOSE_APP" -i cyl_seed.i OUTBASE=out/hz_r${lvl} Mesh/uniform_refine=$lvl \
    Outputs/exodus/file_base=out/hz_r${lvl} --color off >out/hz_r${lvl}.log &
done
wait
for pen in 1e9 1e11; do
  "$MOOSE_APP" -i cyl_seed.i OUTBASE=out/hz_p${pen} Contact/interface/penalty=$pen \
    Outputs/exodus/file_base=out/hz_p${pen} --color off >out/hz_p${pen}.log &
done
wait
end_time=$(date +%s.%N)
awk -v s="$start_time" -v e="$end_time" 'BEGIN{printf "%.3f\n", e-s}' > out/runtime_seconds.txt
python verify.py
