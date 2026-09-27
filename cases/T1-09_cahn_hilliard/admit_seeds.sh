#!/usr/bin/env bash
# Admit seeds 5-9 one at a time as memory frees up. Ten concurrent 256x256 LU
# solves would peak near 13 GB of 15; an OOM kill costs a whole seed, which has
# happened here before. The reaper frees ~1.2 GB each time a seed closes its
# window, so this just waits for room.
cd "$(dirname "$0")"
APP=${MOOSE_APP:-/home/CArlo76/miniforge/envs/moose/moose/bin/combined-opt}
# Refuse to start a seed that already has a solver. Running this script twice
# put TWO writers on out/coarsen_s6.csv and out/coarsen_s7.csv, which silently
# interleaves two different realisations into one file -- the ensemble would
# have been scored on corrupted members.
running () {
  for p in $(pgrep -x combined-opt); do
    # /proc/PID/cmdline is NUL-separated, so grepping for 'seed=N ' with a
    # trailing space NEVER matches and the guard silently passes. That put a
    # second writer on seed 5 and filled its CSV with NUL bytes. Translate first.
    tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null | grep -q "seed=$1 " && return 0
  done
  return 1
}

for s in 5 6 7 8 9; do
  if running "$s"; then echo "seed $s already running -- skipping"; continue; fi
  while [ "$(free -m | awk 'NR==2{print $7}')" -lt 3500 ]; do sleep 120; done
  setsid nohup "$APP" -i coarsening.i \
    Variables/c/InitialCondition/seed=$s Executioner/end_time=1600 \
    Outputs/file_base=out/coarsen_s$s > out/coarsen_s$s.log 2>&1 < /dev/null &
  disown
  echo "$(date +%H:%M:%S) admitted seed $s"
  sleep 60
done
echo "$(date +%H:%M:%S) all ten seeds launched"
