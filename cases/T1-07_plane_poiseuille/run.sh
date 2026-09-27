#!/usr/bin/env bash
set -euo pipefail

CASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export PYTHONPATH="${PYTHONPATH:-}"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$CASE_DIR"
OUT_DIR="$CASE_DIR/out"
case "$OUT_DIR" in
  "$CASE_DIR/out") rm -rf "$OUT_DIR" ;;
  *) echo "Refusing to remove unexpected output path: $OUT_DIR" >&2; exit 2 ;;
esac
mkdir -p "$OUT_DIR" figures
start_time=$(date +%s.%N)

for ny in 2 4 8 16; do
  y0=$(awk -v n="$ny" 'BEGIN { print -1 + 1/n }')
  y1=$(awk -v n="$ny" 'BEGIN { print 1 - 1/n }')
  "$MOOSE_APP" -i poiseuille.i \
    Mesh/ny="$ny" \
    Mesh/nx=160 \
    VectorPostprocessors/profile/start_point="5 $y0 0" \
    VectorPostprocessors/profile/end_point="5 $y1 0" \
    VectorPostprocessors/profile/num_points="$ny" \
    Outputs/file_base="out/ny${ny}"
done

date -u +%Y-%m-%dT%H:%M:%SZ > out/completed_utc.txt
end_time=$(date +%s.%N)
awk -v start="$start_time" -v end="$end_time" 'BEGIN { printf "%.3f\n", end-start }' > out/runtime_seconds.txt
python verify.py
