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

for nx in 20 40 80 160; do
  for pair in "0.025 0025" "0.05 005" "0.1 01"; do
    read -r time tag <<< "$pair"
    "$MOOSE_APP" -i dirichlet.i \
      Mesh/nx="$nx" \
      Executioner/end_time="$time" \
      VectorPostprocessors/profile/num_points="$((nx + 1))" \
      Outputs/file_base="out/dirichlet_n${nx}_t${tag}"
  done
done

# The no-flux cosine mode is an independent conservation check.
"$MOOSE_APP" -i noflux.i \
  Mesh/nx=160 \
  VectorPostprocessors/profile/num_points=161 \
  Outputs/file_base=out/noflux

date -u +%Y-%m-%dT%H:%M:%SZ > out/completed_utc.txt
end_time=$(date +%s.%N)
awk -v start="$start_time" -v end="$end_time" 'BEGIN { printf "%.3f\n", end-start }' > out/runtime_seconds.txt
python verify.py
