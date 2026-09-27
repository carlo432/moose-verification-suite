# source env.sh   (from the repository root)
# Verified 2026-08-02 on the development machine. Override any variable before sourcing.

export MOOSE_ROOT=${MOOSE_ROOT:-/home/CArlo76/miniforge/envs/moose/moose}
export MOOSE_APP=$MOOSE_ROOT/bin/combined-opt
export MOOSE_SHARE=$MOOSE_ROOT/share/moose          # 7,700+ verified .i inputs + gold results
export EXODIFF=$MOOSE_ROOT/bin/exodiff

# Base conda python has numpy/scipy/matplotlib/pandas/sympy/sklearn/h5py/meshio.
export PY=${PY:-/root/miniforge3/bin/python3}

# MOOSE's own python tooling (mms convergence helper, mooseutils, TestHarness)
export PYTHONPATH=$MOOSE_SHARE/python:$PYTHONPATH

export MV_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# MPI: 22 cores available.
# combined-opt is built against the conda MPICH. /usr/bin/mpiexec is OpenMPI and will
# silently launch N independent singleton jobs that clobber one output file. Always use
# $MPIRUN. MPICH needs no --allow-run-as-root flag (it rejects it).
export MPIRUN=${MPIRUN:-/home/CArlo76/miniforge/envs/moose/bin/mpiexec}
alias mrun="$MPIRUN"
