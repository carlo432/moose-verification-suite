#!/usr/bin/env bash
# Launch the far-field dendrite matrix. Serial by design: PJFNK with an ASM
# preconditioner over MPI subdomains gives Jacobian-free directions poor enough
# to fail the line search (DIVERGED_LINE_SEARCH at every rank count tried),
# while the same solve converges in ~4 Newton iterations in serial.
cd "$(dirname "$0")"
APP=${MOOSE_APP:-/home/CArlo76/miniforge/envs/moose/moose/bin/combined-opt}
mkdir -p out figures
launch () { # tag nx T_e
  setsid nohup "$APP" -i dendrite_far.i \
    T_e="$3" Mesh/nx="$2" Mesh/ny="$2" Executioner/num_steps=400 \
    Outputs/file_base="out/far_$1" > "out/far_$1.log" 2>&1 < /dev/null &
  disown
  echo "launched far_$1  nx=$2  T_e=$3"
}
# With no argument, launch the whole matrix. With arguments, launch only the
# named runs -- these compete hard for memory bandwidth with the T1-09
# coarsening ensemble (which slows 20x when the nx=192 LU solve is resident),
# so the two cases are best run one after the other.
want () { [ $# -eq 0 ] && return 0; for a in "$@"; do [ "$a" = "$TAG" ] && return 0; done; return 1; }

TAG=Te0.8; want "$@" && launch Te0.8 144 0.8    # undercooling sweep at the middle mesh
TAG=Te1.0; want "$@" && launch Te1.0 144 1.0
TAG=Te1.2; want "$@" && launch Te1.2 144 1.2
TAG=n96;   want "$@" && launch n96   96  1.0    # mesh sweep at the middle undercooling
TAG=n192;  want "$@" && launch n192  192 1.0
