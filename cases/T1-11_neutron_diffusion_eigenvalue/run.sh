#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/ne_*.log out/ne_*.e out/sphere_*.log out/sphere_*.e
for n in 8 16 32; do
  "$MOOSE_APP" -i ne.i Mesh/nx="$n" Outputs/file_base="out/ne_${n}" >"out/ne_${n}.log"
  "$MOOSE_APP" -i sphere.i Mesh/nx="$n" Outputs/file_base="out/sphere_${n}" >"out/sphere_${n}.log"
done
python verify.py
