#!/usr/bin/env python3
"""Re-verify everything ENVIRONMENT.md claims. Run this before your first action.

    source /root/moose_validation/env.sh && $PY check_env.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

MOOSE_APP = os.environ.get(
    "MOOSE_APP", "/home/CArlo76/miniforge/envs/moose/moose/bin/combined-opt"
)
MOOSE_SHARE = os.environ.get(
    "MOOSE_SHARE", "/home/CArlo76/miniforge/envs/moose/moose/share/moose"
)
EXPECTED_VERSION = "snapshot-20-10-27-41583-g2bd11a08a7"

# Modules the capability checklist needs, with the registry label to look for.
REQUIRED_MODULES = [
    "SolidMechanicsApp", "HeatTransferApp", "NavierStokesApp", "PorousFlowApp",
    "PhaseFieldApp", "StochasticToolsApp", "OptimizationApp", "ContactApp",
    "XFEMApp", "FsiApp", "FluidPropertiesApp",
]

# Objects individual cases depend on.
REQUIRED_OBJECTS = [
    "IsotropicPlasticityStressUpdate", "PowerLawCreepStressUpdate",
    "ComputeMultipleInelasticStress", "ComputeFiniteStrain",
    "ComputeVariableEigenstrain", "DomainIntegral", "MassEigenKernel",
    "SplitCHParsed", "PolycrystalVoronoi", "MonteCarloSampler", "SobolSampler",
    "StatisticsReporter", "Optimize", "GeneralOptimization",
    "ConvectiveHeatFluxBC", "FunctionRadiativeBC", "ADParsedMaterial",
]

SMOKE = """
[Mesh]
  type = GeneratedMesh
  dim = 2
  nx = 20
  ny = 20
[]
[Variables/T][]
[Kernels]
  [cond]
    type = HeatConduction
    variable = T
  []
  [src]
    type = HeatSource
    variable = T
    value = 1e5
  []
[]
[Materials/k]
  type = GenericConstantMaterial
  prop_names = thermal_conductivity
  prop_values = 30
[]
[BCs/lr]
  type = DirichletBC
  variable = T
  boundary = 'left right'
  value = 500
[]
[Executioner]
  type = Steady
  solve_type = NEWTON
[]
[Postprocessors/Tmax]
  type = NodalExtremeValue
  variable = T
[]
[Outputs]
  csv = true
[]
"""

fails = []


def check(label, ok, detail=""):
    print(f"[{'OK ' if ok else 'FAIL'}] {label}{'  ' + detail if detail else ''}")
    if not ok:
        fails.append(label)
    return ok


def main():
    # --- binary ---------------------------------------------------------
    if not check("MOOSE binary present", os.path.isfile(MOOSE_APP), MOOSE_APP):
        return finish()

    ver = subprocess.run([MOOSE_APP, "--version"], capture_output=True, text=True).stdout
    check("MOOSE version matches ENVIRONMENT.md", EXPECTED_VERSION in ver, ver.strip())

    # --- registry -------------------------------------------------------
    reg = subprocess.run([MOOSE_APP, "--registry"], capture_output=True, text=True).stdout
    for mod in REQUIRED_MODULES:
        check(f"module {mod}", mod in reg)
    missing = [o for o in REQUIRED_OBJECTS if o not in reg]
    check("all required objects registered", not missing, f"missing: {missing}" if missing else "")

    # --- smoke test: analytic slab, Tmax = 916.6667 K -------------------
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "smoke.i")
        with open(path, "w") as f:
            f.write(SMOKE)
        r = subprocess.run([MOOSE_APP, "-i", path], capture_output=True, text=True, cwd=d)
        tmax = None
        csv = os.path.join(d, "smoke_out.csv")
        if os.path.isfile(csv):
            rows = [l.strip().split(",") for l in open(csv) if l.strip()]
            hdr = rows[0]
            if "Tmax" in hdr:
                tmax = float(rows[-1][hdr.index("Tmax")])
        ok = tmax is not None and abs(tmax - 916.6667) < 1e-3
        check("smoke test vs analytic slab (916.6667 K)",
              ok, f"got {tmax}" if tmax is not None else r.stdout[-300:])

    # --- test tree (the find -L gotcha) ---------------------------------
    n = sum(len([f for f in files if f.endswith(".i")])
            for _, _, files in os.walk(MOOSE_SHARE, followlinks=True))
    check("shipped test inputs reachable (expect >7000)", n > 7000, f"{n} .i files")

    # --- python stack ---------------------------------------------------
    for mod in ["numpy", "scipy", "matplotlib", "pandas", "sympy", "h5py"]:
        try:
            __import__(mod)
            check(f"python {mod}", True)
        except ImportError:
            check(f"python {mod}", False)

    sys.path.insert(0, os.path.join(MOOSE_SHARE, "python"))
    try:
        import mms  # noqa: F401
        check("MOOSE mms module importable", True)
    except Exception as e:
        check("MOOSE mms module importable", False, str(e)[:120])

    # --- mpi ------------------------------------------------------------
    check("mpiexec on PATH", shutil.which("mpiexec") is not None)

    return finish()


def finish():
    print()
    if fails:
        print(f"*** {len(fails)} CHECK(S) FAILED: {', '.join(fails)}")
        print("See ENVIRONMENT.md.")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
