#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/circ_*.csv out/circ_*.log out/poly_*.csv out/poly_*.log

# Acceptance: an isolated circular grain shrinking under its own curvature.
# R^2 = R0^2 - 2 M sigma t is exactly linear in t with a slope independent of R0.
for r0 in 120 150 180; do
  "$MOOSE_APP" -i shrinking_circle.i GlobalParams/radius=$r0 \
    Outputs/file_base=out/circ_r${r0} --color off >out/circ_r${r0}.log &
done
for nx in 75 150; do
  "$MOOSE_APP" -i shrinking_circle.i Mesh/nx=$nx Mesh/ny=$nx \
    Outputs/file_base=out/circ_n${nx} --color off >out/circ_n${nx}.log &
done
# GBMobility overrides the Arrhenius form, so the slope must scale exactly with
# it whatever GBEvolution's internal unit conversion is.  1.2e-8 also matches
# the Arrhenius material's effective mobility, giving a consistency check.
for m in 6e-9 1.2e-8; do
  "$MOOSE_APP" -i shrinking_circle.i Materials/Copper/GBMobility=$m \
    Outputs/file_base=out/circ_m${m} --color off >out/circ_m${m}.log &
done
wait

# Diagnostic only, no acceptance: the 64-grain polycrystal statistical exponent
# never leaves the transient at this size and duration.
for dt in 20 40; do
  "$MOOSE_APP" -i polycrystal.i Executioner/dt="$dt" \
    Outputs/file_base="out/poly_${dt}" --color off >"out/poly_${dt}.log" || true
done

python verify_circle.py
