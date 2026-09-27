#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/stefan_*.e
for pair in "0.015 8.0 s015" "0.03 4.0 s030" "0.06 2.0 s060"; do
  read -r sigma amp tag <<< "$pair"
  "$MOOSE_APP" -i stefan.i Mesh/nx=800 Materials/cp/expression="1.0 + ${amp}*exp(-((temp-1.5)/${sigma})^2)" Outputs/file_base="out/stefan_${tag}" >/dev/null
done
python verify.py
