#!/usr/bin/env bash
# Re-scoped T3-25 sweep: anisotropic growth-direction selection.
# Serial by design (see run_far.sh); the runs are short, so they go concurrently.
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
#   tag        nx  m  th0  delta
go  rot000     96  6    0  0.04     # rotation sweep: phase must track theta0 one for one
go  rot015     96  6   15  0.04
go  rot030     96  6   30  0.04
go  rot045     96  6   45  0.04
go  mode4      96  4   90  0.04     # mode selection: signal must move to the 4-fold channel
go  null       96  6   90  0.0      # isotropic null: no anisotropy, no arms
go  mesh048    48  6   90  0.04     # mesh sweep at the reference configuration
go  mesh096    96  6   90  0.04
go  mesh144   144  6   90  0.04
