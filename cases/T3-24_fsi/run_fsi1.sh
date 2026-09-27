#!/usr/bin/env bash
# Coupled FSI1 mesh study. Run from a committed script, never from an inline
# command line: `ps | grep fsi1.i` matches the launching shell too, and killing
# by that pattern has already taken out a launcher mid-sweep.
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out

for L in 0 1 2; do
  echo "=== FSI1 level ${L} ==="
  "$MOOSE_APP" -i fsi1.i \
      Mesh/file/file=fsi1_L${L}.msh \
      Outputs/file_base=out/fsi1_L${L} \
      > out/fsi1_L${L}.log 2>&1 || echo "level ${L} exited $?"
  tail -1 out/fsi1_L${L}.csv
done
