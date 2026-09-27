#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/ishigami_n*.csv out/ishigami_n*.json out/ishigami_n*.log
start_time=$(date +%s.%N)
# Native in-MOOSE Sobol indices. SobolReporter, SobolStatistics and
# StatisticsReporter are all registered in this build -- the earlier claim that
# they were unavailable was wrong, and the Python reconstruction it motivated is
# now only a cross-check. The Sobol design is 8N sub-app solves for k=3 inputs.
for n in 256 1024 4096; do
  "$MOOSE_APP" -i ishigami_native.i \
    Samplers/sample/num_rows=$n Samplers/resample/num_rows=$n \
    Outputs/file_base=out/ishigami_n${n} --color off >out/ishigami_n${n}.log 2>&1 &
done
wait
end_time=$(date +%s.%N)
awk -v s="$start_time" -v e="$end_time" 'BEGIN{printf "%.3f\n", e-s}' > out/runtime_seconds.txt
python verify.py
