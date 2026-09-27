# MOOSE Capability Checklist — "Simulated & Validated" Project

Goal: simulate each capability below in MOOSE and check it against a real-world / analytical / benchmark value. Each box = one validated capability.

**Already done (baseline — NOT part of this list):** linear-elastic solid mechanics, steady-state heat conduction, thermal-elastic coupling (TRISO), eigenstrain defect stress (UO2 micromechanics).

Validation legend: **[A]** analytical solution · **[B]** published numerical benchmark · **[E]** experimental / real-world data.

---

## 1. Solid Mechanics — beyond linear elastic
- [ ] **Elastoplasticity (J2 / von Mises)** — validate vs thick-walled pressurized cylinder elastic-plastic analytical solution **[A]** → `T1-05`
- [ ] **Creep (power-law secondary creep)** — validate vs analytical steady-state creep rate / published creep curve for a known alloy **[A/E]** → `T1-06`
- [ ] **Irradiation swelling & creep** — validate vs published cladding/steel swelling-vs-dose data **[E]** → `T3-23`
- [ ] **Contact mechanics** — validate vs Hertzian contact (peak pressure, contact radius) **[A]** → `T1-08`
- [ ] **Fracture — phase-field or XFEM crack** — validate vs LEFM stress-intensity factor K_I for a single-edge-notched specimen **[A/B]** → `T2-17`
- [ ] **Finite-strain / large deformation** — validate vs analytical hyperelastic or known necking benchmark **[A/B]** → `T2-18`
- [ ] **Buckling (mechanical eigenvalue)** — validate vs Euler critical buckling load **[A]** → `T3-22`

## 2. Heat Transfer — beyond steady conduction
- [ ] **Transient conduction** — validate vs semi-infinite-slab error-function / 1-D transient series solution **[A]** → `T1-01`
- [ ] **Convective + radiative boundary conditions** — validate vs analytical fin / lumped-capacitance solution **[A]** → `T1-03`
- [ ] **Phase change / melting (Stefan problem)** — validate vs Stefan analytical melt-front position **[A]** → `T2-21`

## 3. Fluid Flow & Thermal-Hydraulics (MOOSE Navier-Stokes)
- [ ] **Laminar channel flow** — validate vs Poiseuille analytical velocity profile **[A]** → `T1-07`
- [ ] **Lid-driven cavity** — validate vs Ghia et al. benchmark velocities **[B]** → `T2-13`
- [ ] **Natural convection in a cavity** — validate vs de Vahl Davis buoyant-cavity Nusselt numbers **[B]** → `T2-14`
- [ ] **Conjugate heat transfer (fluid + solid)** — validate vs analytical/benchmark interface temperature **[A/B]** → `T2-15`

## 4. Porous Media (PorousFlow module)
- [ ] **Single-phase Darcy flow** — validate vs 1-D analytical pressure / Theis solution **[A]** → `T2-16`

## 5. Phase-Field / Microstructure Evolution
- [ ] **Cahn-Hilliard (spinodal decomposition)** — validate vs mass conservation + expected coarsening law **[A]** → `T1-09`
- [ ] **Allen-Cahn (grain growth)** — validate vs grain-growth kinetics (R² ∝ t) **[A]** → `T1-10`
- [ ] **(Stretch) Solidification / dendrite growth** — validate vs tip-velocity theory **[A/B]** → `T3-25`

## 6. Mass Transport & Chemistry
- [ ] **Fickian species diffusion** — validate vs error-function diffusion profile **[A]** → `T1-02`
- [ ] **Reaction-diffusion (coupled)** — validate vs analytical steady reaction-diffusion length **[A]** → `T1-04`

## 7. Neutronics / Reactor Physics
- [ ] **Neutron diffusion eigenvalue (1-group)** — validate vs analytical bare-slab/sphere k_eff and flux shape **[A]** → `T1-11`

## 8. Multiphysics Coupling — new combinations
- [ ] **Neutronics ↔ heat conduction (coupled)** — validate via global energy balance / benchmark **[A/B]** → `T2-20`
- [ ] **Fluid-structure interaction** — validate vs a standard FSI benchmark **[B]** → `T3-24`

## 9. Advanced MOOSE Tooling
- [ ] **Optimization module (inverse problem)** — recover a known parameter from synthetic data **[A]** → `T2-19`
- [ ] **Stochastic Tools (UQ / sensitivity)** — validate vs analytical variance propagation **[A]** → `T1-12`

---

## Suggested order (original)
1. Transient conduction → 2. Elastoplasticity → 3. Creep → 4. Fracture (phase-field) → 5. Fickian diffusion → 6. Neutron diffusion eigenvalue → 7. Laminar/Poiseuille flow → 8. Phase-field grain growth → then the coupling and advanced-tooling items.

**Execution order used instead:** see `PLAN.md`. Reordered by (a) whether a version-matched seed
input exists in the local MOOSE test tree, and (b) risk — so that the cheap, certain cases land
first and the four items with no seed input (buckling, Stefan, irradiation swelling, dendrite) are
isolated at the end where they cannot block the rest.

## Target resume bullet (original draft)
> Built and analytically/experimentally validated a suite of MOOSE finite-element simulations spanning plasticity, creep, fracture, transient heat transfer, CFD, phase-field microstructure, diffusion, and neutron diffusion — each benchmarked against closed-form or reference solutions.

See `PLAN.md` §3 for a revised version — the draft's "experimentally validated" overclaims, since
only one case on the list touches experimental data.
