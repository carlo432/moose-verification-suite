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

# 1. Mesh convergence of the 2-D ConvectiveHeatFluxBC model at the reference
#    geometry (w=0.1, h=0.5).  Acceptance lives here.
for nx in 100 200 400 800 1600; do
  "$MOOSE_APP" -i fin.i Mesh/nx="$nx" Mesh/ny=4 Outputs/file_base="out/fin_n${nx}" &
done
wait

# 2. Fin-limit study.  h is scaled with w so m = sqrt(2h/(k w)) and hence the
#    analytic target are unchanged, while Bi = h w/(2k) falls as w^2.  The
#    residual gap to the 1-D formula must vanish at second order in w.
for pair in "0.1 0.5" "0.05 0.25" "0.025 0.125" "0.0125 0.0625"; do
  read -r w h <<< "$pair"
  tag=${w//./p}
  "$MOOSE_APP" -i fin.i Mesh/ymax="$w" Mesh/nx=800 Mesh/ny=8 \
    BCs/side_top/heat_transfer_coefficient="$h" \
    BCs/side_bottom/heat_transfer_coefficient="$h" \
    Outputs/file_base="out/finw_${tag}" &
done
wait

# 3. Radiative lumped-capacitance history.
for pair in "0.5 05" "0.25 025" "0.125 0125"; do
  read -r dt tag <<< "$pair"
  "$MOOSE_APP" -i radiative.i Executioner/dt="$dt" Outputs/file_base="out/radiative_dt${tag}" &
done
wait

# 4. fin1d.i is retained only as an independent cross-check that the analytic
#    fin solution is what the 2-D model is being compared against.  It carries
#    no acceptance: convection there is a volumetric sink, not a BC.
for nx in 40 160; do
  "$MOOSE_APP" -i fin1d.i Mesh/nx="$nx" Outputs/file_base="out/fin1d_${nx}" &
done
wait

date -u +%Y-%m-%dT%H:%M:%SZ > out/completed_utc.txt
end_time=$(date +%s.%N)
awk -v s="$start_time" -v e="$end_time" 'BEGIN{printf "%.3f\n", e-s}' > out/runtime_seconds.txt
python verify.py
