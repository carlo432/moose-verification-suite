#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
# Re-scoped case: anisotropic growth-direction selection. run_aniso.sh launches
# the nine-run sweep concurrently (serial solves; see README).
./run_aniso.sh
# wait for the sweep, then score
until python verify_aniso.py 2>/dev/null | grep -q '"verdict"' \
   && ! python verify_aniso.py 2>/dev/null | grep -q "runs incomplete"; do sleep 60; done
python verify_aniso.py > result.json
python -c "import json;print(json.load(open('result.json'))['verdict'])"
