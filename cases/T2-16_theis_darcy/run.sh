#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/theis_*.csv out/thrz_*.csv out/thrz_*.log
start_time=$(date +%s.%N)
# Square-domain seed, retained as a units/sanity diagnostic only.
for n in 10 20 30; do
  "$MOOSE_APP" -i theis1.i Mesh/nx="$n" Mesh/ny="$n" Outputs/file_base="out/theis_${n}" >/dev/null &
done
wait
# Axisymmetric Theis, which carries the acceptance. The dominant error is
# TEMPORAL: the Theis solution is steep at early time and the seed's dt=200
# leaves a 2.4% bias. Timestep is refined at fixed mesh, plus one mesh check.
for dt in 40 20 10; do
  "$MOOSE_APP" -i theis_rz.i Mesh/nx=2000 Executioner/dt=$dt \
    Outputs/csv/file_base=out/thrz_n2000_dt${dt} --color off >out/thrz_n2000_dt${dt}.log &
done
"$MOOSE_APP" -i theis_rz.i Mesh/nx=1000 Executioner/dt=10 \
  Outputs/csv/file_base=out/thrz_n1000_dt10 --color off >out/thrz_n1000_dt10.log &
wait
end_time=$(date +%s.%N)
awk -v s="$start_time" -v e="$end_time" 'BEGIN{printf "%.3f\n", e-s}' > out/runtime_seconds.txt
python verify.py
