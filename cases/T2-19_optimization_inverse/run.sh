#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/opt* out/*.csv out/*.e
"$MOOSE_APP" --allow-test-objects -i optimize.i Outputs/file_base=out/opt >out/opt.log
rm -rf out/mesh8 out/mesh16 out/mesh32 out/mesh64 out/noise1 out/noise5 out/noise10
for n in 8 16 32 64; do
  mkdir -p "out/mesh${n}"
  cp optimize.i forward.i adjoint.i "out/mesh${n}/"
  sed -i "s/nx = 10/nx = ${n}/; s/ny = 10/ny = ${n}/" "out/mesh${n}/forward.i" "out/mesh${n}/adjoint.i"
  (cd "out/mesh${n}" && "$MOOSE_APP" --allow-test-objects -i optimize.i Outputs/file_base=opt >opt.log)
done
for pct in 1 5 10; do
  mkdir -p "out/noise${pct}"
  cp optimize.i forward.i adjoint.i "out/noise${pct}/"
  vals=$(python -c "import numpy as np; r=np.random.default_rng(1900+${pct}); y=np.array([226.,254.,214.,146.]); print(' '.join(f'{v:.12g}' for v in y+r.normal(0,${pct}/100*np.sqrt(np.mean(y*y)),4)))")
  sed -i "s/measurement_values = '226 254 214 146'/measurement_values = '${vals}'/" "out/noise${pct}/optimize.i"
  (cd "out/noise${pct}" && "$MOOSE_APP" --allow-test-objects -i optimize.i Outputs/file_base=opt >opt.log)
done
python verify.py
