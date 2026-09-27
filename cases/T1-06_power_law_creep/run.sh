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

# Parameter-regression matrix at the reference timestep.
for temp in 800 1000 1200; do
  for stress in 50 100 150; do
    "$MOOSE_APP" -i creep.i \
      AuxVariables/temp/initial_condition="$temp" \
      Functions/pressure/y="-$stress -$stress" \
      Executioner/dt=0.2 \
      Outputs/file_base="out/T${temp}_S${stress}_dt02"
  done
done

# Timestep study at the reference stress and temperature.
for pair in "0.4 04" "0.2 02" "0.1 01"; do
  read -r dt tag <<< "$pair"
  "$MOOSE_APP" -i creep.i \
    AuxVariables/temp/initial_condition=1000 \
    Functions/pressure/y='-100 -100' \
    Executioner/dt="$dt" \
    Outputs/file_base="out/reference_dt${tag}"
done

date -u +%Y-%m-%dT%H:%M:%SZ > out/completed_utc.txt
end_time=$(date +%s.%N)
awk -v start="$start_time" -v end="$end_time" 'BEGIN { printf "%.3f\n", end-start }' > out/runtime_seconds.txt
python verify.py
