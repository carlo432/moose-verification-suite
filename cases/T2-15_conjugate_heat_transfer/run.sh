#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/cht_*.e out/cht_*.csv out/cht_*.log
start_time=$(date +%s.%N)
# Thermally developed thin-wall channel; see channel_developed.i for why the
# original geometry could not converge to the constant-q'' reference.
for level in '11 120' '22 240' '44 480'; do
  set -- $level
  "$MOOSE_APP" -i channel_developed.i Mesh/gen/nx=$1 Mesh/gen/ny=$2 \
    Outputs/file_base=out/cht_${1}x${2} --color off >out/cht_${1}x${2}.log &
done
wait
end_time=$(date +%s.%N)
awk -v s="$start_time" -v e="$end_time" 'BEGIN{printf "%.3f\n", e-s}' > out/runtime_seconds.txt
python verify.py
