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

run_step() {
  local nx=$1
  local time=$2
  local tag=$3
  local points=$((nx + 1))
  "$MOOSE_APP" -i step.i \
    Mesh/nx="$nx" \
    Executioner/end_time="$time" \
    VectorPostprocessors/profile/num_points="$points" \
    Outputs/file_base="out/step_n${nx}_t${tag}"
}

# Four spatial levels, with BDF2 time error made small relative to the spatial error.
for nx in 20 40 80 160; do
  for pair in "0.0625 00625" "0.125 0125" "0.25 025"; do
    read -r time tag <<< "$pair"
    run_step "$nx" "$time" "$tag"
  done
done

# Temporal order studies start from the exact solution at physical time 0.01 s.
# The run ends at 0.24 s, so every comparison is at physical t = 0.25 s.
for scheme in implicit-euler crank-nicolson; do
  for pair in "0.03 0030" "0.015 0015" "0.0075 00075" "0.00375 000375"; do
    read -r dt tag <<< "$pair"
    "$MOOSE_APP" -i temporal.i \
      Executioner/scheme="$scheme" \
      Executioner/dt="$dt" \
      Outputs/file_base="out/time_${scheme}_dt${tag}"
  done
done

date -u +%Y-%m-%dT%H:%M:%SZ > out/completed_utc.txt
end_time=$(date +%s.%N)
awk -v start="$start_time" -v end="$end_time" 'BEGIN { printf "%.3f\n", end-start }' > out/runtime_seconds.txt
python verify.py
