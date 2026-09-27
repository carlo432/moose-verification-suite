#!/usr/bin/env bash
# Mesh-independence sweep at theta0 = 15 degrees.
#
# The original sweep (run_aniso.sh, tags mesh048/096/144) ran at theta0 = 90,
# which is 30 modulo 60. reference.json's own symmetry_caveat records that
# theta0 = 0 and 30 give S_6 identically zero because the configuration is
# mirror-symmetric about a mesh axis -- so the phase there is exact BY
# SYMMETRY, not by measurement, and a phase spread of 3.6e-15 across three
# meshes was not evidence of anything. 15 degrees is not mesh-symmetric, so
# the phase there is actually measured and the check can fail.
cd "$(dirname "$0")"
APP=${MOOSE_APP:-/home/CArlo76/miniforge/envs/moose/moose/bin/combined-opt}
mkdir -p out figures
go () { # tag nx mode theta0 delta
  setsid nohup "$APP" -i anisotropy.i \
    Mesh/nx="$2" Mesh/ny="$2" mode="$3" theta0="$4" delta="$5" \
    Outputs/file_base="out/an_$1" > "out/an_$1.log" 2>&1 < /dev/null &
  disown
  echo "launched an_$1  nx=$2 m=$3 theta0=$4 delta=$5"
}
#   tag          nx  m  th0  delta
go  m15_048      48  6   15  0.04
go  m15_096      96  6   15  0.04
go  m15_144     144  6   15  0.04
