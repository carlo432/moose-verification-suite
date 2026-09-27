#!/usr/bin/env bash
# Reap a seed once its declared window closes (L >= 120). Everything after that
# is wasted compute that steals memory bandwidth from the laggards -- the
# ensemble runs ~20x slower with extra LU solves resident.
#
# L = A*sigma/E_grad is derived from the quantity being measured and is NOT
# monotonic, which has now caused three separate failures in this case. The
# gates below exist for concrete reasons, all observed:
#
#   (a) drop t = 0. The random IC is white noise with gradient energy ~11635 --
#       far ABOVE the spinodal peak (~17000 is the peak, but the noise row beats
#       everything in a short run). Including it puts argmax at row 0, so every
#       fresh seed looks "past the peak", and L computed from the post-noise
#       trough (E_grad ~ 3.6) comes out in the thousands. This silently killed
#       seeds 6, 7, 8 and 9 at birth.
#   (b) require the peak to be several rows back, so a still-rising run is not
#       mistaken for a coarsening one.
#   (c) require t > 50, well past phase separation, where L is ~50 and rising.
#       Belt and braces: no legitimate seed reaches 120 before then.
cd "$(dirname "$0")"

# Ask coarsening_lib for L. There is exactly ONE definition of L, the
# coarsening branch and the window, and the verifier uses the same one. The
# three bugs this case suffered all came from a second copy of that logic
# missing a guard the first copy had.
L_of () { ${PY:-python3} coarsening_lib.py L "$1"; }

while :; do
  live=0
  for s in 0 1 2 3 4 5 6 7 8 9; do
    pid=$(pgrep -x combined-opt | while read -r p; do
            grep -qa "coarsen_s$s" "/proc/$p/cmdline" 2>/dev/null && echo "$p"; done)
    [ -z "$pid" ] && continue
    live=$((live+1))
    L=$(L_of "$s")
    if ${PY:-python3} -c "import sys; sys.exit(0 if $L >= 120.0 else 1)" 2>/dev/null; then
      echo "$(date +%H:%M:%S) seed $s closed its window at L=$L -- reaping pid $pid"
      kill -9 "$pid"
    fi
  done
  [ "$live" = "0" ] && break
  sleep 120
done
echo "$(date +%H:%M:%S) all seeds done"
${PY:-python3} verify_coarsening.py
