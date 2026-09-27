#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/coupling_*.e
for n in 20 40 80; do
  "$MOOSE_APP" -i coupling.i Mesh/nx="$n" Outputs/file_base="out/coupling_${n}" >/dev/null
done
python verify.py
