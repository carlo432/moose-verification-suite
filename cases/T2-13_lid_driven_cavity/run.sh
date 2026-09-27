#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
cp "$MOOSE_SHARE/navier_stokes/tests/finite_element/ins/lid_driven/lid_driven.i" cavity.i
rm -f out/cavity_*.e
for n in 16 24 32 64; do
  "$MOOSE_APP" -i cavity.i Mesh/gen/nx="$n" Mesh/gen/ny="$n" \
    Materials/const/prop_values='1 .001 1 .01' Functions/lid_function/expression=1.0 Executioner/num_steps=20 \
    Outputs/file_base="out/cavity_${n}" >/dev/null
done
# Time-extension diagnostic at moderate resolution; this is deliberately
# reported separately from the finest-mesh benchmark profile.
"$MOOSE_APP" -i cavity.i Mesh/gen/nx=32 Mesh/gen/ny=32 \
  Materials/const/prop_values='1 .001 1 .01' Functions/lid_function/expression=1.0 \
  Executioner/num_steps=100 Outputs/file_base="out/cavity_32_long" >out/cavity_32_long.log
python verify.py
