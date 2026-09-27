#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/rotation_*.e
for dt in 0.02 0.01 0.005; do
  tag=${dt//./p}
  "$MOOSE_APP" -i rotation.i Executioner/dt="$dt" Outputs/file_base="out/rotation_${tag}" >/dev/null
done
python verify.py
