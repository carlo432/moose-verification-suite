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

for regime in "05 0.5" "2 2" "10 10"; do
  read -r tag length <<< "$regime"
  for nx in 40 80 160 320; do
    "$MOOSE_APP" -i reaction_diffusion.i \
      Mesh/nx="$nx" \
      Mesh/xmax="$length" \
      VectorPostprocessors/profile/end_point="$length 0 0" \
      VectorPostprocessors/profile/num_points="$((nx + 1))" \
      Outputs/file_base="out/regime_${tag}_n${nx}"
  done
done

date -u +%Y-%m-%dT%H:%M:%SZ > out/completed_utc.txt
end_time=$(date +%s.%N)
awk -v start="$start_time" -v end="$end_time" 'BEGIN { printf "%.3f\n", end-start }' > out/runtime_seconds.txt
python verify.py
