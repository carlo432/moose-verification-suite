#!/usr/bin/env bash
# Resume (or start) the coupled FSI1 mesh study after an interruption.
#
# This script exists because three separate things went wrong the last time a
# long run on this suite was interrupted, and each is guarded here:
#
#   1. NOTHING TO RESUME FROM. fsi1.i originally had no Checkpoint output, so an
#      interrupted run lost all of its progress. Checkpointing is now on
#      (every 20 steps, 2 files kept). A level with no out/<base>_cp/ directory
#      simply starts from t=0 -- that is correct, not an error.
#   2. WRONG --recover ARGUMENT. --recover takes the checkpoint FILE BASE, not
#      the directory. Passing out/fsi1_L2_cp makes MOOSE look for
#      out/fsi1_L2_cp-mesh.cpa.gz and fail. The correct form is
#      out/fsi1_L2_cp/LATEST. LATEST is a keyword MOOSE resolves to the newest
#      checkpoint in that directory; it is NOT a file, so it must never be used
#      as an existence test -- see the guard below.
#   3. TWO WRITERS ON ONE FILE BASE. Running a launcher twice put two solvers on
#      the same CSV; the file came back with NUL bytes in it and the corruption
#      was only caught later by a monotonicity check. The guard below reads
#      /proc/PID/cmdline -- which is NUL separated, so it is translated to
#      spaces first; a plain grep of it silently never matches.
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out

already_running () {   # $1 = mesh level
  local p
  for p in $(pgrep -x combined-opt 2>/dev/null); do
    tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null | grep -q "fsi1_L$1" && return 0
  done
  return 1
}

for L in 0 1 2; do
  if already_running "$L"; then
    echo "level $L: a solver is ALREADY writing out/fsi1_L$L -- refusing to start a second."
    continue
  fi

  done_t=$(tail -1 "out/fsi1_L$L.csv" 2>/dev/null | cut -d, -f1 || true)
  if [ "$done_t" = "12" ]; then
    echo "level $L: already complete at t=12, skipping."
    continue
  fi

  args=(-i fsi1.i Mesh/file/file="fsi1_L$L.msh" Outputs/file_base="out/fsi1_L$L")
  # NOTE: LATEST is a KEYWORD that MOOSE resolves to the newest checkpoint in
  # the directory -- there is no file of that name on disk, so testing
  # -f .../LATEST is always false and would silently restart from scratch every
  # time. That was the first version of this guard, and it defeated the entire
  # point of the script. Test for actual restart data instead. Verified against
  # a live checkpoint: MOOSE reported "Using out/fsi1_L2_cp/0040 for recovery"
  # and continued at the next step.
  if compgen -G "out/fsi1_L${L}_cp/*-restart-*" > /dev/null; then
    echo "level $L: resuming from checkpoint (csv reached t=${done_t:-0})"
    args+=(--recover "out/fsi1_L${L}_cp/LATEST")
  else
    echo "level $L: no checkpoint, starting from t=0"
  fi

  "$MOOSE_APP" "${args[@]}" >> "out/fsi1_L$L.log" 2>&1 || echo "level $L exited $?"
  echo "level $L: $(tail -1 "out/fsi1_L$L.csv" 2>/dev/null)"
done
