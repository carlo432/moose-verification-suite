#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/circ_*.csv out/circ_*.log
# Initial-radius sweep: dR/dt ~ 1/R makes dR^2/dt independent of R0.
for r0 in 120 150 180; do
  "$MOOSE_APP" -i shrinking_circle.i GlobalParams/radius=$r0 \
    Outputs/file_base=out/circ_r${r0} --color off >out/circ_r${r0}.log &
done
# Mesh sweep at the reference radius.
for nx in 75 150; do
  "$MOOSE_APP" -i shrinking_circle.i Mesh/nx=$nx Mesh/ny=$nx \
    Outputs/file_base=out/circ_n${nx} --color off >out/circ_n${nx}.log &
done
# Mobility scaling: GBMobility overrides the Arrhenius form, so the slope must
# scale exactly with it whatever GBEvolution's internal unit conversion is.
for m in 6e-9 1.2e-8; do
  "$MOOSE_APP" -i shrinking_circle.i Materials/Copper/GBMobility=$m \
    Outputs/file_base=out/circ_m${m} --color off >out/circ_m${m}.log &
done
wait
python verify_circle.py
