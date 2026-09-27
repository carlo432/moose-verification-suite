#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/j_*.csv out/interaction_*.csv
for r in 0 1 2; do
  "$MOOSE_APP" -i j.i Mesh/uniform_refine="$r" Outputs/file_base="out/j_r${r}" >/dev/null
  "$MOOSE_APP" -i interaction.i Mesh/uniform_refine="$r" Outputs/file_base="out/interaction_r${r}" >/dev/null
done
python verify.py
