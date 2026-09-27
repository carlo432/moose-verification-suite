# PLAN.md — MOOSE Capability Verification Suite

25 capabilities, each demonstrated in MOOSE and checked against a closed-form solution, a published
numerical benchmark, or experimental data. Ordered by dependency and risk, not by interest.

Read `SCHEMA.md` first. The rules there are not optional and several of them
(reference provenance, pre-declared tolerances, convergence orders) are what separates this from a
folder of pretty simulations.

---

## 0. What this suite is for, and what it is not

**It is:** evidence that you can pose a physics problem in a production multiphysics FE code, solve
it correctly, and *prove* it was correct against something external. Twenty-five times, across nine
physics domains, with the arithmetic shown.

**It is not:** a demonstration that MOOSE is correct (INL already verifies MOOSE far more rigorously
than this), and it is not experimental validation of anything except, partially, one case. Being
precise about that distinction is a feature. Anyone qualified to be impressed by this suite is
qualified to notice if you overclaim, and overclaiming would cost more than the suite gains.

**Three things make this credible rather than decorative**, and they are the three most likely to be
skipped under time pressure:
1. **The tolerance was declared before the answer was known.** Enforced by git history.
2. **Convergence order, not a single lucky mesh.** Three refinements minimum on every [A] case.
3. **The failures are still in the table.** A suite with 3 honest FAILs reads as real. A suite with
   25 PASSes reads as tuned, and the reader will assume it was.

**Validation classes:** **[A]** closed-form/MMS · **[B]** published numerical benchmark ·
**[E]** experimental data. Assigned per case below and carried in every `result.json`.

---

## 1. Schedule and gates

| Tier | Cases | Character | Estimate |
|---|---|---|---|
| **Tier 1** | 12 | Closed-form reference, seed input exists, low risk | ~2 weeks |
| **Tier 2** | 9 | Published benchmark or real setup work | ~3 weeks |
| **Tier 3** | 4 | Build from scratch, research-grade, may not close | open-ended, optional |

Gates: an independent review of Tier 1 after case T1-12 must sign off before Tier 2. Same after
T2-21. Tier 3 is reviewed case by case. **The project is a success at the end of Tier 2** — 21
capabilities, all verified. Tier 3 is upside, and its four items are the ones most likely to eat a
week each for a PARTIAL. Do not let them hold the suite hostage.

Per-case timebox: one working day without a running solve → write it up as blocked, move on.

---

# TIER 1 — closed-form reference, low risk

### T1-01 · Transient heat conduction · [A] · checklist 2.1

**Problem.** Semi-infinite solid, initially at `T_i`, surface stepped to `T_s` at `t=0`.
**Reference.** `T(x,t) = T_s + (T_i - T_s)·erf(x / (2√(αt)))`. Derive it in `verify.py` with
`scipy.special.erf`; no citation needed for a solution you derive, but state the assumptions.
**MOOSE.** `[Variables] T`, `HeatConductionTimeDerivative` + `HeatConduction`, `DirichletBC`,
`Transient` with `dt` refinement. Seed: `framework/tests/kernels/simple_transient_diffusion/`, or
`heat_transfer` transient tests.
**Acceptance.** L2 error over the domain at three times; observed spatial order 2.0 ± 0.2 and
temporal order 1.0 (backward Euler) or 2.0 (`CrankNicolson`) ± 0.2. Run **both** time integrators —
showing that the observed temporal order tracks the scheme you chose is stronger evidence than any
single error number, and it costs one extra run.
**Domain length must be long enough** that the far boundary never sees the front: check
`4√(αt_end) < L`, and assert it in the input. This is the classic way this case is silently wrong.
**Risk.** Low. This is the calibration case for the whole workflow — get `run.sh`, `verify.py`,
`result.json`, and the figure style right here, then clone the pattern 24 times.

### T1-02 · Fickian species diffusion · [A] · checklist 6.1

**Problem.** Same mathematics as T1-01, different physics label and a concentration variable.
Do it immediately after T1-01 while the pattern is warm — but make it a *different* problem, not a
rename: use a finite slab with the series solution, or a two-region diffusion couple with the
`erfc` interface solution and a concentration-dependent `D` as a second variant.
**Reference.** Finite slab: `c/c_0 = 1 - (4/π)Σ_{n odd} (1/n)·exp(-Dn²π²t/L²)·sin(nπx/L)`, summed to
convergence in `verify.py`. Or diffusion-couple `erfc`.
**MOOSE.** `TimeDerivative` + `MatDiffusion` (or `ADMatDiffusion`).
**Acceptance.** L2 order 2.0 ± 0.2; total species mass conserved to solver tolerance in the
no-flux variant — assert it.
**Risk.** Low. **Do not let this become a copy of T1-01 with `T` renamed to `c`.** The reviewer will
check, and a duplicated case weakens the suite rather than adding to it.

### T1-03 · Convective + radiative boundary conditions · [A] · checklist 2.2

**Problem.** Two sub-cases in one directory.
(a) **Convecting fin**, adiabatic tip: `θ/θ_b = cosh(m(L−x))/cosh(mL)`, `m = √(hP/kA)`; check the fin
    tip temperature and the base heat rate `q = √(hPkA)·θ_b·tanh(mL)`.
(b) **Radiating lumped body**: transient cooling of a body with `Bi ≪ 0.1` under `σεA(T⁴−T_∞⁴)`; the
    implicit analytic solution is standard and `scipy` can invert it. Confirm `Bi < 0.1` numerically
    before claiming the lumped solution applies — that check is part of the case.
**MOOSE.** `ConvectiveHeatFluxBC`, `FunctionRadiativeBC` (registered — confirmed). Seed:
`heat_transfer/tests/` radiative and convective BC tests.
**Acceptance.** Fin tip temperature and base heat rate each within 1% at the finest mesh, order 2.0.
Radiative case: peak deviation over the cooling history < 1%.
**Risk.** Low. Watch the sign convention on `ConvectiveHeatFluxBC` and whether `T_infinity` is a
postprocessor or a constant in this build.

### T1-04 · Reaction–diffusion · [A] · checklist 6.2

**Problem.** 1-D steady diffusion with a first-order volumetric sink, fixed surface concentration,
no-flux at depth `L`.
**Reference.** `c(x) = c_s · cosh((L−x)/λ) / cosh(L/λ)`, penetration length `λ = √(D/k)`. Verify the
recovered `λ` from the numerical profile by fitting, **and** verify the profile pointwise — the fit
alone can hide a systematic offset.
**MOOSE.** `Diffusion` + `Reaction` (rate = k). Add a transient variant approaching the steady state
if you want the extra evidence; it is cheap.
**Acceptance.** Recovered `λ` within 0.5%; L2 profile error order 2.0 ± 0.2. Sweep `L/λ` over
{0.5, 2, 10} — reaction-limited to diffusion-limited — so the case shows a regime change, not one
point.
**Risk.** Low.

### T1-05 · Elastoplasticity, J2 / von Mises · [A] · checklist 1.1

**Problem.** Thick-walled cylinder, internal pressure, plane strain, elastic–perfectly-plastic,
pressurized until fully plastic. `b/a = 2` is the conventional choice.
**Reference.** Von Mises plane strain (Nadai/Hill):
- yield onset at the bore: `p_y = (σ_y/√3)·(1 − a²/b²)`
- elastic-plastic interface at radius `c`: `p = (σ_y/√3)·[2·ln(c/a) + 1 − c²/b²]`
- full plastic collapse: `p_lim = (2σ_y/√3)·ln(b/a)`

⚠️ **These are the von Mises plane-strain forms. Tresca gives different constants** (no `2/√3`) and
most textbook tables print Tresca. Getting these mixed up is the single most common error in this
benchmark. Derive them symbolically in `verify.py` with `sympy` and cite a source for the derivation
— do not transcribe a table.
**MOOSE.** `[Physics/SolidMechanics/QuasiStatic]`, `ComputeMultipleInelasticStress` +
`IsotropicPlasticityStressUpdate` (both registered), `Pressure` BC ramped by a `Function`, RZ or
2-D plane-strain quarter model with symmetry. Seed: `solid_mechanics/tests/` plasticity tests;
`combined/tests/combined_plasticity_temperature/` shows the stack assembled.
**Acceptance.** Three quantities: `p_y` within 1%, the `p(c)` curve within 2% over the range
`c/a ∈ [1.2, 1.8]`, and `p_lim` within 2%. Mesh convergence on `p_lim`.
**Watch out.** Radial mesh grading matters — the plastic front is a moving discontinuity in the
stress gradient. Grade toward the bore. Report the load-step size sensitivity too; too coarse a
pressure ramp overshoots the collapse load.
**Risk.** Low-moderate. Highest-value case in Tier 1 — this is the one a structural engineer will
look at first.

### T1-06 · Power-law (secondary) creep · [A/E] · checklist 1.2

**Problem.** Two sub-cases.
(a) **Uniaxial bar** at constant stress and temperature → Norton secondary creep rate
    `ε̇ = A·σⁿ·exp(−Q/RT)`. Recover `A`, `n`, and `Q` from the simulation by regression and check
    against the values you put in. This is a round-trip verification of the material model —
    honest, but state plainly in the README that it is a round trip, not independent evidence.
(b) **The case that earns the [E]:** take published Norton constants for a real alloy (316H or
    Grade 91 are both well documented in the open literature) and reproduce a *published* creep
    curve — strain vs time at a stated stress and temperature. This is a genuine comparison to
    experiment-derived data. Get the constants and the curve from the same source and cite it.
**MOOSE.** `PowerLawCreepStressUpdate` (registered) inside `ComputeMultipleInelasticStress`. Seed:
`solid_mechanics/tests/substepping/power_law_creep.i`,
`solid_mechanics/tests/combined_creep_plasticity/`.
**Acceptance.** (a) recovered `n` within 1%, `Q` within 2%. (b) simulated strain within 10% of the
digitized published curve over the secondary-creep regime — and say explicitly that primary and
tertiary creep are outside the model, because the Norton form has neither.
**Watch out.** Time integration for creep needs substepping (hence the seed being in
`tests/substepping/`); check timestep independence explicitly.
**Risk.** Low for (a), moderate for (b) — obtaining a digitizable published curve is the hard part.
If (b) does not come together in a day, ship (a) as [A] and mark (b) as PARTIAL. Do not
fabricate a "published" curve.

### T1-07 · Laminar channel flow / Poiseuille · [A] · checklist 3.1

**Problem.** Pressure-driven flow between parallel plates, developed.
**Reference.** `u(y) = (1/(2μ))·(−dp/dx)·(h² − y²)`; `u_max/u_avg = 3/2`; friction factor
`f·Re = 96` for a plane channel (**not** 64 — that is the circular pipe; a plane channel is 96, and
this is a very common slip).
**MOOSE.** Finite volume INS. **Seed: `navier_stokes/tests/finite_volume/ins/mms/channel-flow/plane-poiseuille-flow.i`
— it already carries an MMS setup**, which means the convergence bookkeeping is half done.
**Acceptance.** Velocity profile L2 error order ≥ 1.9 (second-order FV); `f·Re` within 1%; mass
conservation between inlet and outlet to solver tolerance.
**Extras that cost almost nothing:** also run the developing-entrance case and compare the
development length to the `L_e/D ≈ 0.05·Re` correlation. Adds a second, independent check.
**Risk.** Low. Do this before the other CFD cases — it is where you learn this build's
Navier-Stokes syntax, which is the most version-sensitive part of MOOSE.

### T1-08 · Hertzian contact · [A] · checklist 1.4

**Problem.** Elastic sphere pressed onto a flat (or sphere-on-sphere), frictionless.
**Reference.** `a = (3FR/(4E*))^{1/3}`, `p₀ = 3F/(2πa²)`, `δ = a²/R`, with
`1/E* = (1−ν₁²)/E₁ + (1−ν₂²)/E₂`. Pressure distribution `p(r) = p₀√(1 − r²/a²)`.
**MOOSE.** Seed: `contact/tests/hertz_spherical/hertz_contact_rz.i` — **axisymmetric and it ships
with gold output**, so you get a working starting point and a regression check for free.
**Acceptance.** Contact radius within 3%, peak pressure within 5%, and the full `p(r)` distribution
within 5% away from the contact edge. Convergence study on contact radius with mesh refinement —
contact quantities converge slowly and non-monotonically, so report the trend honestly rather than
claiming order 2.
**Watch out.** Hertz assumes `a ≪ R` — keep the load small enough that it holds, and *check the
ratio* and report it. Penalty stiffness affects the answer; do a penalty sensitivity sweep and show
the result is converged with respect to it. That sweep is itself a good finding for the README.
**Risk.** Low-moderate. Contact is the most numerically finicky Tier 1 item; give it the full day.

### T1-09 · Cahn–Hilliard (spinodal decomposition) · [A] · checklist 5.1

**Problem.** 2-D periodic domain, composition at the spinodal with small random perturbation,
run through decomposition into coarsening.
**Reference.** Three independent checks, no single "the answer":
1. **Mass conservation** — `∫c dV` constant to solver tolerance for all time. Non-negotiable; CH is
   conservative by construction and any drift is a bug in your formulation or your solver tolerance.
2. **Free energy monotonically decreasing** — `dF/dt ≤ 0` at every step. Also non-negotiable.
3. **Coarsening law** — characteristic length `L(t) ∝ t^{1/3}` (Lifshitz–Slyozov–Wagner) in the
   late-stage regime. Extract `L(t)` from the structure factor first moment or from the
   interface-area-per-volume; fit the exponent over the late window only, and state the window.
**MOOSE.** Seed: `phase_field/tests/phase_field_kernels/SplitCahnHilliard.i` and `SplitCHParsed`.
Use the split form — the direct 4th-order form is much harder to solve.
**Acceptance.** Mass drift < 1e-8 relative; `F` monotone; fitted exponent `1/3 ± 0.05` with the fit
window and the R² reported. Fixed RNG seed on the initial condition.
**Watch out.** The `t^{1/3}` law only holds in late-stage coarsening, and the domain must be large
enough that you have many domains at the end — otherwise finite-size effects flatten the exponent.
If you cannot get a clean exponent, report the fit with its window and mark PARTIAL. **A forced
`1/3` from a hand-picked window is worse than an honest PARTIAL** and is easy for a reviewer to spot
by re-fitting.
**Risk.** Moderate — the exponent is the soft part; the two conservation checks are rock solid.

### T1-10 · Allen–Cahn grain growth · [A] · checklist 5.2

**Problem.** 2-D polycrystal, isotropic grain-boundary energy and mobility, curvature-driven growth.
**Reference.** Parabolic growth law `⟨R⟩² − ⟨R₀⟩² = k·t`, equivalently `⟨R⟩ ∝ t^{1/2}`. Also check
the **Herring/equilibrium triple-junction angle of 120°** for isotropic energy — an independent,
purely geometric check that costs one image-analysis function and is much harder to fake than an
exponent fit.
**MOOSE.** Seed: `phase_field/tests/actions/grain_growth.i` (the `GrainGrowth` action, registered)
with `PolycrystalVoronoi` initial conditions and `GrainTracker` for the grain count.
**Acceptance.** Fitted exponent `0.5 ± 0.05` on `⟨R⟩` vs `t` in the steady-growth regime, with the
window stated; grain count decreasing monotonically; mean triple-junction angle `120° ± 5°`.
**Watch out.** Early transient (from the Voronoi IC relaxing) is not in the scaling regime — exclude
it and say where you cut. Grain count must stay large enough at the end for statistics; stop the run
before you are down to a handful of grains.
**Risk.** Moderate, same soft-exponent issue as T1-09.

### T1-11 · Neutron diffusion eigenvalue, 1-group · [A] · checklist 7.1

**Problem.** Bare homogeneous reactor, one-group diffusion: `−D∇²φ + Σ_a φ = (1/k)·νΣ_f φ`. Do
**both** a slab and a sphere.
**Reference.** `k = νΣ_f / (Σ_a + D·B²)` with geometric buckling `B² = (π/ã)²` (slab, extrapolated
half-thickness) and `(π/R̃)²` (sphere), `ã = a + 2d`, extrapolation distance `d = 2.13·D` (transport)
or `0.71·λ_tr`. Flux shapes: `cos(πx/ã)` and `sin(πr/R̃)/r`. **State which extrapolation convention
you used** — it moves `k` by ~1% and is the usual source of a "mysterious" discrepancy here.
**MOOSE.** `[Problem] type = EigenProblem`, `Executioner type = Eigenvalue`, `MassEigenKernel` with
the eigen vector tag for the fission source. **Seed: `framework/tests/executioners/eigen_executioners/ne.i`
— `ne` is literally "neutron eigenvalue", it is the closest thing in the tree to this exact case.**
**Acceptance.** `k_eff` within 0.1% (100 pcm) of analytic at the finest mesh, order 2.0 ± 0.2 on the
eigenvalue error; flux shape L2 within 1% after normalization.
**Bonus with real leverage.** You already have an OpenMC 3-D Monte Carlo `k_eff` for a comparable
sphere in `/root/nuen304_openmc` (1.05660 ± 0.00012, against a diffusion value of 1.0500). If the
material data can be made consistent, add a third column: analytic diffusion / MOOSE diffusion /
OpenMC transport — and then **explain the diffusion-vs-transport gap physically** rather than
treating it as an error. Diffusion theory is not supposed to match transport near a vacuum boundary,
and saying why demonstrates more than any tolerance would. Check the material consistency carefully
before claiming the comparison; if the constants cannot be reconciled, report MOOSE vs analytic only.
**Risk.** Low-moderate. The eigen-tagging syntax is the only fiddly part, and the seed input has it.

### T1-12 · Stochastic Tools — UQ and sensitivity · [A] · checklist 9.2

**Problem.** Two sub-cases.
(a) **Analytic variance propagation** — a model whose output variance is known in closed form given
    the input distributions (a linear combination of independent normals: `Var = Σ aᵢ²σᵢ²`). Confirm
    the sampled variance converges to it as `1/√N`, and show the `1/√N` rate.
(b) **The one that actually proves something: the Ishigami function**,
    `f = sin(x₁) + a·sin²(x₂) + b·x₃⁴·sin(x₁)`, `a=7`, `b=0.1`, `xᵢ ~ U(−π,π)`. It has **closed-form
    Sobol indices**, which makes it the standard sensitivity-analysis verification problem.
    **ANCHOR (confirm before use):** `Var ≈ 13.8445`, `S₁ ≈ 0.3139`, `S₂ ≈ 0.4424`, `S₃ = 0`,
    `S_T1 ≈ 0.5576`, `S_T3 ≈ 0.2437`. Derive these symbolically with `sympy` rather than trusting the
    anchor — the derivation is a page of integrals and it makes the case self-contained.
    `S₃ = 0` with `S_T3 ≠ 0` is the interesting part: `x₃` has no main effect but a real interaction
    effect. If your suite reproduces that, it has demonstrated something a variance-only study cannot.
**MOOSE.** `MonteCarloSampler`, `SobolSampler`, `StatisticsReporter` (all registered);
`ParsedOptimizationFunction` or a trivial `ParsedFunction`-driven sub-app to evaluate Ishigami.
Seed: `stochastic_tools/tests/reporters/sobol/`, `.../actions/parameter_study_action/monte_carlo.i`.
**Acceptance.** Each Sobol index within its own bootstrap confidence interval of the analytic value,
at a stated sample count; convergence of the estimates with `N` shown as a figure. Report the
confidence intervals — `StatisticsReporter` computes them, and quoting a Sobol index without one
is the same error as quoting a Monte Carlo tally without its σ.
**Risk.** Low. Cheap to run, and a genuinely uncommon thing to have on a résumé.

---

# TIER 2 — published benchmark or real setup work

### T2-13 · Lid-driven cavity · [B] · checklist 3.2

**Reference.** Ghia, Ghia & Shin (1982), *J. Comput. Phys.* 48:387–411 — `u` along the vertical
centerline and `v` along the horizontal centerline, tabulated at 17 points each, for Re = 100, 400,
1000. **Transcribe the tables into `reference/ghia1982.json` with the page/table number, and do it
before you run anything.**
**ANCHOR only (Re=1000):** `u_min ≈ −0.38289`, `v_max ≈ 0.37095`, `v_min ≈ −0.51550`. Confirm from
the paper. If you cannot obtain Ghia, Botella & Peyret (1998) Re=1000 spectral results are an
acceptable substitute with higher accuracy — but cite whichever you actually used.
**MOOSE.** Seed: `navier_stokes/tests/finite_element/ins/lid_driven/lid_driven.i` (and the
`_stabilized` variant). FV is likely easier to converge at Re=1000.
**Acceptance.** L2 deviation over the 17 tabulated points < 2% of `U_lid` at Re=100 and 400, < 4% at
Re=1000, on a mesh at least 128×128. Also compare **primary vortex center location** — Ghia tabulates
it, and it is a much more sensitive discriminator than the velocity profile.
**Watch out.** The lid corner singularity: the benchmark is defined with the discontinuous lid BC,
so do **not** smooth it, and expect no clean convergence order near the corners. Report profile
error vs mesh as a trend, not as an order.
**Risk.** Moderate. Re=1000 needs a fine mesh and patience.

### T2-14 · Natural convection in a cavity · [B] · checklist 3.3

**Reference.** de Vahl Davis (1983), *Int. J. Numer. Methods Fluids* 3:249–264, differentially
heated square cavity, Pr = 0.71.
**ANCHOR (confirm from the paper):** average Nusselt `1.118 / 2.243 / 4.519 / 8.800` at
`Ra = 10³ / 10⁴ / 10⁵ / 10⁶`; midplane `u_max ≈ 3.649 / 16.178 / 34.73 / 64.63`.
**MOOSE.** Seed: `navier_stokes/tests/postprocessors/rayleigh/natural_convection.i`. Boussinesq
buoyancy. Non-dimensionalize carefully and **state the non-dimensionalization in the README** — half
the discrepancies in this benchmark are somebody's `Ra` differing by a factor.
**Acceptance.** `Nu_avg` within 2% at Ra ≤ 10⁵, within 4% at 10⁶; `u_max` within 3%. Run all four
Rayleigh numbers — **the trend across three decades of Ra is the actual result**, far more convincing
than a single Ra matching.
**Watch out.** Ra=10⁶ has thin boundary layers and needs a graded mesh; check `Nu` computed on the
hot wall against `Nu` on the cold wall — they must agree, and that is a free internal consistency
check that catches an unconverged solution immediately.
**Risk.** Moderate.

### T2-15 · Conjugate heat transfer · [A/B] · checklist 3.4

**Problem.** Fluid channel with a conducting solid wall, heat crossing the interface.
**Reference.** Build the case so a closed form exists: fully-developed laminar flow in a channel with
a constant-heat-flux outer solid wall gives `Nu = 8.235` (parallel plates, both walls heated,
constant `q″`) — an exact result — and the interface temperature then follows from a 1-D conduction
balance through the solid. That converts a vague "benchmark interface temperature" into a real
closed-form check. **`Nu = 8.235` for parallel plates with constant `q″`; do not confuse it with
`7.541` (constant wall temperature) or the circular-pipe values `4.364`/`3.66`.**
**MOOSE.** Seed: `heat_transfer/tests/conjugate_heat_transfer/conjugate_heat_transfer.i`. Single
mesh with two blocks is simpler and more robust than a MultiApp here — use the MultiApp version only
if the monolithic one fails.
**Acceptance.** `Nu` in the developed region within 2%; interface temperature within 1% of the
conduction balance; heat flux continuous across the interface to solver tolerance (assert it).
**Risk.** Moderate.

### T2-16 · Single-phase Darcy flow / Theis · [A] · checklist 4.1

**Reference.** Theis (1935): drawdown `s = (Q/4πT)·W(u)`, `u = r²S/(4Tt)`, well function
`W(u) = E₁(u)` = `scipy.special.exp1`. Also do the trivial 1-D steady Darcy case
(`Δp = μQL/(kA)`) as a units sanity check before the transient — it catches permeability-unit errors,
which are the standard way this case goes wrong.
**MOOSE.** Seed: `porous_flow/tests/dirackernels/theis1.i`, `theis_rz.i` — **they ship with gold
output**, so you have a regression target and a working PorousFlow parameter set immediately.
**Acceptance.** Drawdown within 2% over `u ∈ [1e-3, 1]` at several radii and times; recovered
transmissivity from a Cooper–Jacob straight-line fit within 2% of the input. That fit is what a
hydrogeologist would actually do with the data, which makes it a better demonstration than a
pointwise comparison.
**Watch out.** Theis assumes an infinite aquifer — the domain must be large enough that the outer
boundary is not felt at the latest time you compare. Check it and report the check.
**Risk.** Low-moderate. PorousFlow has a lot of required parameters; the gold-backed seed removes
most of that pain.

### T2-17 · Fracture — K_I · [A/B] · checklist 1.5

**Problem.** Single-edge-notched tension (SENT) specimen, linear elastic, mode I.
**Reference.** `K_I = σ√(πa)·F(a/W)` with `F(a/W)` from the Tada/Paris/Irwin handbook — the standard
polynomial fit, accurate to 0.5% for `a/W ≤ 0.6`. **Transcribe the polynomial with its citation into
`reference/`.** Cross-check against `K_I = √(E′·J)` from the J-integral, which is an independent
route to the same number through a different MOOSE object.
**MOOSE.** Two routes, both worth doing:
(a) `DomainIntegral` action with the **interaction integral** → `K_I` directly. Seed:
    `solid_mechanics/tests/interaction_integral/interaction_integral_2d.i`.
(b) J-integral → `K_I`. Seed: `solid_mechanics/tests/j_integral/j_integral_2d_small_strain.i`.
Agreement between (a) and (b) is itself a result.
**Acceptance.** `K_I` within 3% of handbook for `a/W ∈ {0.2, 0.4, 0.6}`; **path independence** of the
contour integral demonstrated across ≥4 rings (this is the real verification of a J/interaction
integral implementation and is more convincing than the value itself); (a) and (b) agree within 1%.
**Phase-field as an optional second capability.** `ComputeLinearElasticPFFractureStress` is
registered and `combined/tests/phase_field_fracture/` has working inputs. Validating phase-field
against `K_I` is *not* straightforward — the phase-field critical load depends on the regularization
length `ℓ` and only approaches Griffith as `ℓ → 0`. If you do it, the correct check is the
**Γ-convergence trend**: critical load vs `ℓ`, extrapolating toward the Griffith load. Do the
interaction integral first and treat phase-field as a bonus; do not claim phase-field "matches LEFM"
at a single `ℓ`.
**Watch out.** Crack-tip mesh refinement drives everything; use a focused mesh and report the tip
element size relative to `a`.
**Risk.** Moderate. Route (a) with the seed input is quite tractable.

### T2-18 · Finite strain / large deformation · [A/B] · checklist 1.6

**Problem.** Uniaxial extension of an incompressible (or nearly incompressible) hyperelastic bar to
large stretch.
**Reference.** Neo-Hookean, incompressible, uniaxial: Cauchy stress `σ = μ(λ² − 1/λ)`, nominal stress
`P = μ(λ − 1/λ²)`, out to `λ = 2` or more. This is exact and unambiguous.
**MOOSE.** `ComputeFiniteStrain` / `ComputeLagrangianStrain` (both registered) with the appropriate
finite-strain stress calculator; check what hyperelastic materials this snapshot actually registers
before committing to Neo-Hookean specifically — if there is no Neo-Hookean, use the finite-strain
elastic material and validate against the **exact large-rotation solution instead**: a bar subjected
to rigid-body rotation must produce **zero stress**, which small-strain formulations famously fail.
That "rigid rotation → zero stress" test is arguably the *better* demonstration anyway, because it
shows precisely what finite strain buys you over the small-strain kinematics already in the baseline
work. **Do both if the material exists; do the rotation test regardless.**
**Acceptance.** Stress-stretch curve within 1% of analytic out to `λ = 2`; spurious stress under 90°
rigid rotation < 1e-8 of the elastic modulus.
**Risk.** Moderate — mostly "what is registered in this build", which one `--registry | grep` answers.

### T2-19 · Optimization module — inverse problem · [A] · checklist 9.1

**Problem.** Recover a known parameter from synthetic data. Recommended: a 2-D conduction problem
with an unknown volumetric heat source magnitude (or an unknown conductivity in a subregion);
generate synthetic "measurements" at a set of points with the true value, then recover it.
**Reference.** The true value you used to make the data. Recovery within 0.1% is the bar for
noise-free data.
**MOOSE.** `Optimize` executioner with TAO (**confirmed working** — `taobncg` converges on the
shipped test), `GeneralOptimization` / `OptimizationReporter`, `OptimizationData`,
`ReporterTimePointSource`, adjoint via `SteadyAndAdjoint`. Seed:
`optimization/tests/executioners/basic_optimize/` (run with `--allow-test-objects` to see it work,
then rebuild with non-test objects).
**Acceptance.** Noise-free recovery within 0.1%. **Then add Gaussian noise at 1%, 5%, and 10% of the
signal and report the recovery error and its scaling** — an inverse problem that only works on
noise-free data has demonstrated the API, not the method. The noise study is what makes this case
worth having.
**Extra credit, cheap:** recover *two* parameters and show the correlation between them, or show
that a poorly-placed measurement set makes the problem ill-conditioned. Either one demonstrates
understanding of inverse problems rather than of MOOSE syntax.
**Risk.** Moderate. TAO is verified working, which removes the main risk.

### T2-20 · Neutronics ↔ heat conduction coupling · [A/B] · checklist 8.1

**Problem.** Take T1-11's eigenvalue solution, normalize the flux to a stated total power, deposit
`κΣ_f·φ` as a volumetric heat source, and solve conduction.
**Reference.** Two independent checks:
1. **Global energy balance** — total heat leaving through the boundaries equals the specified total
   power, to solver tolerance. Assert it. This is the check that actually proves the coupling and
   normalization are right, and it is exact.
2. **Analytic temperature profile** — for a slab with a cosine source `q(x) = q₀cos(πx/ã)` and fixed
   surface temperature, `T(x)` is exactly integrable. Compare pointwise.
**MOOSE.** Either a single input with both variables (simplest, and the FLiBe project's precedent
says the simple route is the right one), or `MultiApp` + `MultiAppCopyTransfer` if you want to
demonstrate the MultiApp system explicitly. **Doing it both ways and showing they agree is a
legitimate extra result** and directly demonstrates the MultiApp capability that the checklist's
"new combinations" section is really asking about.
**Acceptance.** Energy balance closes to < 1e-8 relative; `T(x)` within 1% of analytic; peak
temperature converges at order 2.
**Optional next step, only if time allows:** temperature feedback on `Σ_a` (a simple linear
coefficient) makes it a genuinely coupled nonlinear problem with a self-consistent `k_eff`. Then
verify the fixed point against a hand-iterated solution. That is a real reactor-physics
demonstration and it builds directly on what is already there.
**Risk.** Moderate. Depends on T1-11 being clean.

### T2-21 · Phase change / Stefan problem · [A] · checklist 2.3

**Problem.** 1-D one-phase Stefan problem: semi-infinite solid at `T_m`, surface held at `T_w > T_m`,
melt front advances.
**Reference.** `X(t) = 2λ√(αt)` where `λ` solves `λ·e^{λ²}·erf(λ) = St/√π`, Stefan number
`St = c_p(T_w − T_m)/L_f`. Solve the transcendental with `scipy.optimize.brentq`.
**MOOSE.** **No shipped phase-change input exists** — this is a build-from-scratch case. Use the
**apparent heat capacity** method: `c_eff(T) = c_p + L_f·δ(T − T_m)` smeared over a mushy interval
`ΔT`, implemented with `ADParsedMaterial` / `DerivativeParsedMaterial`. No C++ needed.
**Acceptance.** Front position within 2% over the run; **and a convergence study in the mushy-zone
width `ΔT`** showing the error → 0 as `ΔT` → 0. That second study is the whole point: the apparent
heat capacity method has a *modeling* parameter on top of the discretization, and showing you
identified it, converged it, and reported it is the difference between a validated case and a tuned
one. Run at ≥2 Stefan numbers.
**Watch out.** The apparent-`c_p` method needs the timestep small enough that the front does not jump
a full mushy zone in one step — otherwise latent heat is silently skipped and the front runs fast.
Check the CFL-like condition explicitly and report it. This is the failure mode of this method and
naming it in the README is worth more than the case passing.
**Risk.** Moderate-high — the only Tier 2 case with no seed input. If it stalls, it drops to Tier 3.

---

# TIER 3 — build from scratch, may not close

These four are optional. Each is worth attempting only after Tier 2 is signed off, and each is a
legitimate PARTIAL.

### T3-22 · Buckling · [A] · checklist 1.7

**The problem with this item:** MOOSE has **no linear buckling eigensolver** — there is no geometric
stiffness matrix assembly exposed for a classical `(K + λK_g)φ = 0` eigenproblem. Searching the test
tree for "buckl" returns nothing. So the checklist item as literally written ("mechanical eigenvalue")
is not directly available.

**The right substitute, which is arguably better:** an **imperfection-based nonlinear collapse
analysis with a Southwell plot**. Compress a slender column with a small mid-span geometric
imperfection (0.1–1% of length) using finite strain, record load vs mid-span lateral deflection, then
plot `δ/P` vs `δ` — for an imperfect Euler column this is a **straight line whose slope is `1/P_cr`**.
The Southwell plot recovers the *perfect-column* Euler load from imperfect-column data, which is
exactly what experimentalists do, and it converges to `π²EI/(KL)²`.

**Acceptance.** Southwell-recovered `P_cr` within 3% of Euler for `KL/r > 100`; the recovery should
be **insensitive to the imperfection amplitude** — demonstrate that across three amplitudes, because
that insensitivity is what proves you measured `P_cr` and not the imperfection. Also check ≥2
boundary conditions (pinned-pinned `K=1`, fixed-pinned `K=0.699`) to show the `K` factor comes out.
**Report the substitution honestly** in the README and in `RESULTS.md`: the capability demonstrated is
nonlinear post-buckling collapse, not a linear buckling eigenvalue.
**Risk.** Moderate. Arc-length continuation may be needed past the limit point; if `Steady` with load
control stalls at the bifurcation, use displacement control instead — that avoids the limit-point
problem entirely and is the standard trick.

### T3-23 · Irradiation swelling and creep · [E] · checklist 1.3

**The problem with this item:** MOOSE's open modules have **no irradiation swelling or irradiation
creep model** — those live in BISON, which is export-controlled and not available here. So the model
itself must be implemented as a dose-dependent volumetric eigenstrain via `ComputeVariableEigenstrain`
(registered) driven by a fitted correlation.

**And then be honest about the circularity:** if you fit a correlation to published swelling-vs-dose
data and then "validate" by reproducing that data, you have validated nothing but your curve fit.
Say so plainly. The defensible framing is two-part:
1. **Material model check (round trip, stated as such):** the implemented eigenstrain reproduces the
   published swelling correlation for 316 stainless or HT9 — incubation dose, then the ~1%/dpa steady
   swelling regime. Cite the source for the correlation.
2. **The part that is actually new information (this is the real deliverable):** apply a *dose
   gradient* across a component and compute the resulting differential-swelling stress field. That
   result is not in the correlation — it is a structural consequence the correlation cannot give you
   — and it can be checked against an independent hand calculation (a bimetallic-strip-style mismatch
   estimate) and against the requirement that stress → 0 for a uniform dose. That zero-stress check
   under uniform dose is a genuine, non-circular verification and it is exact.

**Acceptance.** Correlation reproduced to plotting accuracy; uniform-dose stress < 1e-8 of modulus;
gradient-driven peak stress within 20% of the analytical mismatch estimate.
**Rank this last of the four** — it is the weakest validation on the checklist and the honesty
caveats consume much of its résumé value.

### T3-24 · Fluid–structure interaction · [B] · checklist 8.2

**Reference target.** Turek & Hron (2006) FSI benchmark, **FSI1** — the *steady* case at Re=20, by far
the cheapest of the three. Reference tip displacement **ANCHOR:** `(2.27e-5, 8.209e-4)` m; confirm
from the source. FSI2 and FSI3 are periodic and far more expensive — do not start with them.
**MOOSE.** The `fsi` module has **only 7 input files** in the whole tree; seed:
`fsi/tests/2d-small-strain-transient/fsi_flat_channel.i`. `ConvectedMesh` + `ConvectedMeshPSPG` for
the ALE terms.
**Acceptance.** Tip displacement within 10% of the benchmark. Ten percent is a deliberately loose
bar — Turek-Hron is hard, and the community reports scatter.
**Fallback if FSI1 does not converge (likely, and acceptable):** a **coupling-consistency** check
instead — pressure-driven flow over an elastic wall, where the wall deflection under the *computed*
pressure field is compared to an independent Euler-Bernoulli beam solution loaded with that same
pressure. That verifies the load transfer and the structural response separately, which is not a
benchmark but is honest and checkable. Mark it PARTIAL and say what it does and does not show.
**Risk.** High. The most likely BLOCKED item on the list.

### T3-25 · Solidification / dendrite growth · [A/B] · checklist 5.3

**Reference.** Dendrite tip velocity and radius against **LGK (Lipton–Glicksman–Kurz)** theory, or
the microscopic solvability criterion `σ* = 2d₀D/(R²V)`.
**MOOSE.** No shipped solidification input (searched — nothing under `*solidif*` or `*dendrit*`). The
`GrandPotential` phase-field tests in `phase_field/tests/GrandPotentialPFM/` are the closest starting
structure. Adaptive mesh refinement at the interface is effectively mandatory.
**Acceptance.** Realistically, a **converged steady tip velocity that scales correctly with
undercooling** is a good outcome; matching LGK quantitatively requires thin-interface asymptotics and
anti-trapping currents and careful interface-width convergence. Set the bar at: tip velocity
independent of interface width `W` over a factor of 2 (the thin-interface limit), and the correct
scaling trend with undercooling `Δ`. Quantitative LGK agreement is a stretch within a stretch.
**Risk.** High. Expect PARTIAL. This is the right last item — it is the only one where "we got the
scaling and characterized the interface-width dependence" is a genuinely respectable stopping point.

---

## 2. Deliverables

1. `RESULTS.md` — the capability table. Generated, never hand-edited. Grouped by checklist section,
   with `validation_class` on every row and the legend visible.
2. `data/summary.csv` — machine-readable, one row per case.
3. `cases/*/README.md` — 25 short write-ups, each ending with what the case does *not* show.
4. `figures/` — one figure per case, interpretable without the code.
5. `run_all.py` — reruns everything, regenerates the table.
6. A short `docs/report.md` — 3–4 pages: the method (pre-declared tolerances, convergence orders,
   provenance), the table, and a limitations section. Follow the structure of
   `/root/dai_dai/docs/report/report.md`; that report's habit of naming its own weaknesses is the
   thing to copy.

## 3. The résumé bullet

The draft bullet says "analytically/experimentally validated". Once the suite exists, that phrasing
undersells the [A] work and overclaims the [E] work. Suggested replacement, adjust the counts to
whatever actually passes:

> Built a 21-case MOOSE verification suite spanning elastoplasticity, creep, contact, fracture
> mechanics, transient and conjugate heat transfer, incompressible CFD, porous flow, phase-field
> microstructure evolution, species transport, and neutron diffusion — each case checked against a
> closed-form solution or a published benchmark (Ghia, de Vahl Davis, Theis, Turek–Hron), with
> tolerances declared before execution, measured mesh-convergence orders, and a machine-generated
> pass/fail table including the cases that did not pass.

"Including the cases that did not pass" is not a weakness in a bullet like this. To anyone who does
verification work for a living, it is the most credible clause in the sentence.
