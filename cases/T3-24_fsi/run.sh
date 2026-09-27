#!/usr/bin/env bash
set -eo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/env.sh"
cd "$(dirname "$0")"
mkdir -p out figures
rm -f out/fsi.e
"$MOOSE_APP" -i fsi_flat_channel.i Outputs/file_base=out/fsi >/dev/null 2>&1 || true
python verify.py
