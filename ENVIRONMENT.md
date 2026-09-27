# Verified Environment

Everything below was **executed and confirmed** on 2026-08-02 on the development machine (WSL2
Ubuntu, 22 cores, 15 GB RAM). Paths are specific to that machine; adjust `env.sh` for yours.

Always `source env.sh` first.

---

## 1. MOOSE — WORKING

| Item | Value |
|---|---|
| Executable | `/home/CArlo76/miniforge/envs/moose/moose/bin/combined-opt` |
| Version | `snapshot-20-10-27-41583-g2bd11a08a7` (conda build 2024-10-06) |
| Also present | `exodiff`, `hit`, symlinks `moose`, `moose-opt` |

**Smoke test — re-run this before believing anything else.** 2-D unit square, `HeatConduction` +
`HeatSource value=1e5`, `k=30`, Dirichlet 500 K left/right → `Tmax = 916.6667 K`.
Analytic slab `500 + qL²/(8k) = 916.667 K`. **Exact match, confirmed today.**

### Every module this project needs is compiled in

Confirmed from `combined-opt --registry`:

| Module | Objects | Module | Objects |
|---|---:|---|---:|
| SolidMechanics | 491 | StochasticTools | 131 |
| NavierStokes | 429 | HeatTransfer | 124 |
| ThermalHydraulics | 327 | Contact | 53 |
| PhaseField | 303 | XFEM | 50 |
| PorousFlow | 174 | Optimization | 32 |
| Peridynamics | 53 | LevelSet | 15 |
| ChemicalReactions | 34 | ScalarTransport | 14 |
| Reactor | 31 | Fsi | 8 |

**No rebuild is needed for any item on the capability checklist.** Spot-checked as registered:
`IsotropicPlasticityStressUpdate`, `PowerLawCreepStressUpdate`, `ComputeFiniteStrain`,
`ComputeLagrangianStrain`, `ComputeLinearElasticPFFractureStress`, `CrackTipEnrichment`,
`DomainIntegral`, `MassEigenKernel`, `Eigenvalue`, `WCNSFVFlowPhysics`, `PorousFlowFullySaturated`,
`SplitCHParsed`, `GrainGrowth`, `PolycrystalVoronoi`, `MonteCarloSampler`, `SobolSampler`,
`ParameterMeshOptimization`, `Optimize`.

**TAO is built in and working** — `optimization/tests/executioners/basic_optimize/quadratic_minimize.i`
runs to `Solution converged: ||g(X)|| <= gatol` with `taobncg`. The optimization module is live.

### ⚠️ Gotcha 1 — `--allow-test-objects`

Many shipped test inputs use objects registered to a `*TestApp` (e.g. `QuadraticMinimize` in
`OptimizationTestApp`). Running them plain gives
`*** ERROR *** A 'QuadraticMinimize' is not a registered object.` — which looks like a broken install
and is not. Add `--allow-test-objects`:

```bash
$MOOSE_APP -i quadratic_minimize.i --allow-test-objects
```

Do **not** build production cases on test-app objects. Use them to learn the pattern, then rewrite
with a registered object.

### ⚠️ Gotcha 2 — `find` will lie to you in `share/moose`

`$MOOSE_SHARE/framework`, `/solid_mechanics`, etc. are **symlinks**. Plain `find` does not follow
them, so `find $MOOSE_SHARE -name '*.i'` returns **32** files. `find -L` returns **7,700+**.
Always use `find -L`. Same for `grep -r` (use `grep -rL`… no — use `grep -r` with an explicit
resolved path, or `find -L … -exec grep`).

### ⚠️ Gotcha 3 — use the conda MPI launcher, **not** `/usr/bin/mpiexec`

**Corrected 2026-08-03.** The earlier instruction here (`mpiexec --allow-run-as-root -n 4 …`) was
carried over from another project and is **wrong for this binary**. It fails silently, which is worse
than failing loudly.

`combined-opt` is built against the conda **MPICH**. `/usr/bin/mpiexec` is **OpenMPI**. Launching a
MPICH binary under OpenMPI does not error — it starts N *independent singleton* jobs that each report
`Num Processors: 1` and all write to the same output file, clobbering each other. A transient run
launched this way produces a truncated, interleaved Exodus file that looks like a solver failure.

```bash
# WRONG — 4 serial duplicates, one corrupt output file, exit code 0
mpiexec --allow-run-as-root -n 4 $MOOSE_APP -i x.i     # Num Processors: 1  (x4)

# RIGHT — one 4-rank job.  MPICH needs no --allow-run-as-root flag.
$MPIRUN -n 4 $MOOSE_APP -i x.i                          # Num Processors: 4
```

`$MPIRUN` is set by `env.sh` to `/home/CArlo76/miniforge/envs/moose/bin/mpiexec`. Verified: the smoke
test gives `Tmax = 916.6667 K` on 4 real ranks. Note MPICH's `mpiexec` **rejects**
`--allow-run-as-root` outright (`unrecognized argument`), so if you see that error you have the right
launcher and just need to drop the flag.

22 cores available; 15 GB RAM total, ~11 GB usable.

### ⚠️ Gotcha 4 — inherited from the FLiBe project, still true

Coupled temperature+displacement solves stall at a fixed residual with `DIVERGED_LINE_SEARCH` unless
you set `automatic_scaling = true` and `line_search = none`. And this snapshot requires
`displacements` stated explicitly inside `[Physics/SolidMechanics/QuasiStatic]`.

### ⚠️ Gotcha 5 — the binary is ~22 months old

Built 2024-10-06; today is 2026-08-02. Syntax introduced after that date **does not exist here**.
The online MOOSE documentation tracks `main` and will show you objects and parameters this binary
does not have. **The local `share/moose` test tree is the authoritative syntax reference for this
build** — it shipped with the binary and every input in it is version-matched. Prefer it over the
website. When the website and the local tree disagree, the local tree wins.

---

## 2. The local test tree is the single biggest asset here

`$MOOSE_SHARE` ships **7,700+ `.i` inputs with `gold/` reference outputs**, version-matched to the
binary:

```
framework 3104   solid_mechanics 1169   porous_flow 545   navier_stokes 374
thermal_hydraulics 346   phase_field 292   stochastic_tools 268   contact 259
combined 221   richards 207   heat_transfer 193   reactor 108   optimization 105
xfem 90   ray_tracing 68   peridynamics 59   chemical_reactions 55   fsi 7
```

Confirmed seed inputs already located for the checklist (paths relative to `$MOOSE_SHARE`):

| Capability | Seed input |
|---|---|
| Lid-driven cavity | `navier_stokes/tests/finite_element/ins/lid_driven/lid_driven.i` |
| Poiseuille (with MMS) | `navier_stokes/tests/finite_volume/ins/mms/channel-flow/plane-poiseuille-flow.i` |
| Natural convection | `navier_stokes/tests/postprocessors/rayleigh/natural_convection.i` |
| Conjugate heat transfer | `heat_transfer/tests/conjugate_heat_transfer/conjugate_heat_transfer.i` |
| Theis / Darcy | `porous_flow/tests/dirackernels/theis1.i` … `theis_rz.i` (with gold) |
| Hertzian contact | `contact/tests/hertz_spherical/hertz_contact_rz.i` (with gold) |
| Power-law creep | `solid_mechanics/tests/substepping/power_law_creep.i` |
| Creep + plasticity | `solid_mechanics/tests/combined_creep_plasticity/` |
| K_I interaction integral | `solid_mechanics/tests/interaction_integral/interaction_integral_2d.i` |
| J-integral | `solid_mechanics/tests/j_integral/j_integral_2d_small_strain.i` |
| Phase-field fracture | `combined/tests/phase_field_fracture/` |
| Cahn-Hilliard | `phase_field/tests/phase_field_kernels/SplitCahnHilliard.i` |
| Grain growth | `phase_field/tests/actions/grain_growth.i` |
| Neutron eigenvalue | `framework/tests/executioners/eigen_executioners/ne.i` (`ne` = neutron eigenvalue) |
| Sobol / Monte Carlo | `stochastic_tools/tests/reporters/sobol/`, `.../parameter_study_action/monte_carlo.i` |
| TAO optimization | `optimization/tests/executioners/basic_optimize/quadratic_minimize.i` |
| FSI | `fsi/tests/2d-small-strain-transient/fsi_flat_channel.i` (only 7 FSI inputs exist) |

**No shipped input exists for:** buckling, Stefan/melting, irradiation swelling, dendrite growth.
Those four are the build-from-scratch items and are tiered accordingly in `PLAN.md`.

---

## 3. Python — WORKING

`$PY` = `/root/miniforge3/bin/python3`, version 3.12.12.

| Package | Version |
|---|---|
| numpy | 2.4.3 |
| scipy | 1.17.1 |
| matplotlib | 3.10.8 |
| pandas | 3.0.1 |
| sympy | 1.14.0 |
| scikit-learn | 1.9.0 |
| h5py | 3.16.0 |
| meshio | 5.3.5 |

**MOOSE's `mms` module is importable** via the `PYTHONPATH` set in `env.sh` — confirmed
`import mms` succeeds. Use it for manufactured-solution convergence studies; it does the
spatial/temporal refinement bookkeeping and fits the observed order for you. `mooseutils` (for
reading MOOSE CSV/Exodus output) is on the same path.

Post-processing: prefer MOOSE `csv = true` output over parsing Exodus. `meshio` can read `.e` when
you genuinely need a field, but a `Postprocessor` or `VectorPostprocessor` writing CSV is simpler,
smaller, and diffable.

---

## 4. Resources

22 cores · 15 GB RAM · 872 GB free on `/`. Every case in `PLAN.md` is 1-D or 2-D and should run in
minutes. If a case needs more than 10 minutes on 4 ranks, it is over-specified — coarsen it.
