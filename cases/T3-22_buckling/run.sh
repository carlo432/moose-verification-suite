#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/col_*.csv out/col_*.log
start_time=$(date +%s.%N)

# Southwell requires only a load-deflection curve from a geometrically imperfect
# column, not a geometric-stiffness or eigenvalue object.  The axial load is a
# dead load (FunctionNeumannBC).  A `Pressure` BC would be wrong: it defaults to
# use_displaced_mesh = true, making the load follow the rotating tip face, which
# is Beck's column -- non-conservative, no static bifurcation, and it produces
# lateral stiffening under compression instead of buckling.

# Imperfection sweep, both boundary conditions, at the reference mesh.
for a0 in 0.1 0.2 0.5; do
  tag=${a0//./p}
  "$MOOSE_APP" -i column.i       IMPERFECTION="$a0" Mesh/gen/nx=80 Executioner/end_time=0.95 \
    Outputs/file_base="out/col_cant_a${tag}"  --color off >"out/col_cant_a${tag}.log" &
  "$MOOSE_APP" -i column_fixed.i IMPERFECTION="$a0" Mesh/gen/nx=80 Executioner/end_time=0.95 \
    Outputs/file_base="out/col_fixed_a${tag}" --color off >"out/col_fixed_a${tag}.log" &
  "$MOOSE_APP" -i column_clamped.i IMPERFECTION="$a0" Mesh/gen/nx=80 Executioner/end_time=0.95 \
    Outputs/file_base="out/col_clamped_a${tag}" --color off >"out/col_clamped_a${tag}.log" &
done
wait

# Mesh sweep at the middle imperfection.
# nx=80 is the reference mesh, already covered by the imperfection sweep.
for nx in 40 160; do
  "$MOOSE_APP" -i column.i       IMPERFECTION=0.2 Mesh/gen/nx="$nx" Executioner/end_time=0.95 \
    Outputs/file_base="out/col_cant_n${nx}"  --color off >"out/col_cant_n${nx}.log" &
  "$MOOSE_APP" -i column_fixed.i IMPERFECTION=0.2 Mesh/gen/nx="$nx" Executioner/end_time=0.95 \
    Outputs/file_base="out/col_fixed_n${nx}" --color off >"out/col_fixed_n${nx}.log" &
  "$MOOSE_APP" -i column_clamped.i IMPERFECTION=0.2 Mesh/gen/nx="$nx" Executioner/end_time=0.95 \
    Outputs/file_base="out/col_clamped_n${nx}" --color off >"out/col_clamped_n${nx}.log" &
done
wait

# Independent EI calibration: a transverse tip load on the perfect column must
# reproduce delta = F L^3/(3 EI).  This pins the reference before it is used.
"$MOOSE_APP" -i column.i IMPERFECTION=0 Mesh/gen/nx=80 \
  Functions/axial_traction/expression='0' \
  BCs/inactive='axial' \
  Outputs/file_base=out/col_calibration --color off >out/col_calibration.log 2>&1 || true

end_time=$(date +%s.%N)
awk -v s="$start_time" -v e="$end_time" 'BEGIN{printf "%.3f\n", e-s}' > out/runtime_seconds.txt
python verify.py
