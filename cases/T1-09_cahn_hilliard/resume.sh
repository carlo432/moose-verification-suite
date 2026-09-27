#!/usr/bin/env bash
# Resume the ten-seed ensemble after the 2026-08-07 pause.
#
# Seeds 0-4 have checkpoints and continue in place from ~t=740-853.
# Seeds 5-9 have NO checkpoint (MOOSE had not written one yet -- they were only
# about an hour old) and restart from t=0. They were at t=75-120 of ~1000, so
# roughly 10% of their progress is lost, not a rerun of the whole ensemble.
#
# Serial by design: pc_type lu under MPI factorizes redundantly per rank.
# Memory is ~1.25 GB per seed and does NOT grow -- the footprint is the LU
# factorization, set by the 256x256 mesh, not by solution state. Ten seeds is
# ~12.6 GB of 15, which held, but the reaper must be running to free seeds as
# their windows close.
cd "$(dirname "$0")"
APP=${MOOSE_APP:-/home/CArlo76/miniforge/envs/moose/moose/bin/combined-opt}

for s in 0 1 2 3 4; do
  # --recover takes the checkpoint FILE BASE, not the directory: pointing it at
  # out/coarsen_s0_cp made it look for out/coarsen_s0_cp-mesh.cpa.gz. The LATEST
  # keyword resolves to the newest numbered prefix inside the directory.
  setsid nohup "$APP" -i coarsening.i --recover out/coarsen_s${s}_cp/LATEST \
    Executioner/end_time=1600 Outputs/file_base=out/coarsen_s$s \
    > out/coarsen_s${s}_resume.log 2>&1 < /dev/null &
  disown; echo "recovered seed $s from checkpoint"
done
# Seeds 5-9 restart from scratch and must be admitted ONE AT A TIME as memory
# allows. Launching them as a burst alongside the five recovering seeds killed
# all five instantly with zero-byte logs: ten LU factorizations being allocated
# at once spikes past the 15 GB box even though the steady footprint (12.6 GB)
# fits. admit_seeds.sh waits for headroom before each one.
setsid nohup ./admit_seeds.sh > out/admit.log 2>&1 < /dev/null &
disown
echo "seeds 5-9 queued for staggered admission (see out/admit.log)"

setsid nohup ./reap_closed_seeds.sh > out/reap.log 2>&1 < /dev/null & disown
echo "reaper armed"
