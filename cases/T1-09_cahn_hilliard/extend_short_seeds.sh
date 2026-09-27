#!/usr/bin/env bash
# Wait for the ensemble, then continue in place any seed that has not reached
# L = 120. verify_coarsening.py refuses to score until all five close their
# window, so an unextended ensemble reads PARTIAL rather than as a result.
cd "$(dirname "$0")"
APP=${MOOSE_APP:-/home/CArlo76/miniforge/envs/moose/moose/bin/combined-opt}
alive () { pgrep -x combined-opt | while read -r p; do
             grep -qa coarsening.i "/proc/$p/cmdline" 2>/dev/null && echo x; done | wc -l; }
while [ "$(alive)" != "0" ]; do sleep 300; done
echo "=== ensemble reached end_time ==="
for s in 0 1 2 3 4 5 6 7 8 9; do
  L=$(${PY:-python3} -c "
import csv,math
D=math.sqrt(80); S=2*40/(3*D); A=480**2
r=[x for x in csv.DictReader(open('out/coarsen_s$s.csv')) if float(x['time'])>0][-1]
print(f'{A*S/float(r[\"gradient_energy_integral\"]):.2f}')")
  if ${PY:-python3} -c "import sys; sys.exit(0 if $L < 120.0 else 1)"; then
    echo "seed $s at L=$L -- recovering to end_time=1600"
    setsid nohup "$APP" -i coarsening.i --recover out/coarsen_s${s}_cp \
      Executioner/end_time=1600 Outputs/file_base=out/coarsen_s$s \
      > out/coarsen_s${s}_ext.log 2>&1 < /dev/null &
    disown
  else
    echo "seed $s at L=$L -- window closed"
  fi
done
