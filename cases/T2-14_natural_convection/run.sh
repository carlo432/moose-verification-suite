#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/ra_*.e out/ra_*.csv
for ra in 1e3 1e4 1e5 1e6; do
  tag=${ra//./p}
  "$MOOSE_APP" -i boussinesq.i hot_temp="$ra" temp_ref="$(python -c "print($ra/2)")" \
    Functions/lid_function/expression=0 Outputs/file_base="out/ra_${tag}" >/dev/null
done
  "$MOOSE_APP" -i boussinesq.i Mesh/gen/nx=64 Mesh/gen/ny=64 hot_temp=1e5 temp_ref=5e4 \
  Functions/lid_function/expression=0 Outputs/file_base="out/ra_1e5_mesh64" >/dev/null
  for n in 64 96 128; do
  "$MOOSE_APP" -i boussinesq.i Mesh/gen/nx=$n Mesh/gen/ny=$n hot_temp=1e6 temp_ref=5e5 \
  Functions/lid_function/expression=0 Outputs/file_base="out/ra_1e6_mesh${n}" >/dev/null &
  done
  wait
python verify.py
