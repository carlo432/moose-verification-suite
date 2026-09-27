#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/ch_*.e out/ch_*.csv out/long_ch.*
for dt in 0.1 0.5 1 2; do
  tag=${dt//./p}
  case "$dt" in 0.1) steps=200;; 0.5) steps=40;; 1) steps=20;; 2) steps=10;; esac
  "$MOOSE_APP" -i split_ch.i Mesh/nx=64 Mesh/ny=64 Mesh/xmax=120 Mesh/ymax=120 Executioner/dt="$dt" Executioner/num_steps="$steps" Outputs/file_base="out/ch_${tag}" >/dev/null
done
"$MOOSE_APP" -i split_ch.i Mesh/nx=64 Mesh/ny=64 Mesh/xmax=120 Mesh/ymax=120 Executioner/dt=1 Executioner/num_steps=100 Outputs/file_base=out/long_ch >/dev/null
python verify.py
