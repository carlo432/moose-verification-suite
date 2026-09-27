# T3-25 — Anisotropic solidification: growth-direction selection

Kobayashi anisotropic phase-field solidification (`ACInterfaceKobayashi1/2` plus
`InterfaceOrientationMaterial`), built on `phase_field/tests/anisotropic_interfaces/kobayashi.i`.

## What is measured, and why it is not tip velocity

The row originally claimed a **dendrite tip velocity and its scaling with undercooling**. That
observable is not reachable with this parameter set on this hardware, and the reason is measured,
not asserted:

| domain | what the tip does |
|---|---|
| 0.7 box, insulated (`dendrite.i`) | decelerates 14.1 → 1.6 across the window |
| 1.05 quarter-symmetry, Dirichlet far field (`dendrite_far.i`) | decelerates 15.5 → 10.7, then **stalls at 0.357** while the melt at x=0.70 recalesces to T = 0.98 |

Latent heat with `K = 1.8` saturates the domain faster than a boundary sink can drain it. A steady
tip needs the thermal layer thin against the domain — roughly `L = 3–4` at the same `dx`, so
`nx ≈ 300–400`. That is ~17× the elements with LU scaling worse than linearly: days per run, five
runs. `reference.json` records this in `observable_correction`.

**Two errors of mine are recorded there too**, because they change how the old result should be read:

- The declared window `[0.45, 0.58]` was in **absolute mesh coordinates**, where the seed sat at
  x = 0.35 — so it meant 0.10 to 0.23 *from the seed centre*. The superseded `verify.py` defines
  `SEED_X = 0.35` and never uses it. That window begins at 1.25× the initial seed radius and ends
  at 2.9×, covering the first 10% of the run while the seed is still relaxing off its IC. Scored
  correctly on the far-field data it gives R² = 0.9958 against the declared 0.98 — but that is a
  short segment of a smooth decelerating curve looking straight. **The check could not fail.**
- The quarter-symmetry domain was justified in writing as matching four-fold symmetry.
  `mode_number` defaults to **six** in this build, so those mirror planes imposed the wrong symmetry.

## The replacement observable

What the model *does* predict exactly is orientation. The interfacial parameter is
`ε(θ) = ε̄ [1 + δ cos(m(θ − θ₀))]`, so the grain must acquire an m-fold shape locked to `θ₀`. The
observable is the angular Fourier content of the solid region,

```
C_m = ∫ w cos(mθ) dA        a_m     = √(C_m² + S_m²) / area     (m-fold amplitude)
S_m = ∫ w sin(mθ) dA        θ_m     = atan2(S_m, C_m) / m       (arm direction)
```

For `R(θ) = R₀[1 + a cos(m(θ − θ₀))]` these recover `a` and `θ₀` exactly. They are **volume
integrals**, so the measurement does not inherit the node-straddling error a `LineValueSampler`
would — the same lesson as T3-23.

Measured at the first step where the solid area reaches **3× its own initial value** — geometric,
fixed in advance, late enough for the shape to develop and early enough to precede recalescence.
Each run is normalised by its own initial area so that discretisation of the IC divides out.

## Results

Rotation sweep, `m = 6`, `δ = 0.04`, nx = 96. Phase must equal `reference_angle` modulo 60°:

| `reference_angle` | measured phase | error | a₆ |
|---:|---:|---:|---:|
| 0° | 0.000° | 0.000° | 0.0352 |
| 15° | 14.832° | **0.168°** | 0.0333 |
| 30° | 30.000° | 0.000° | 0.0321 |
| 45° | 45.145° | **0.145°** | 0.0341 |

Declared tolerance 2°.

**Symmetry caveat, stated because it matters:** `reference_angle` 0° and 30° give `S₆ ≈ 1e-18`
because the configuration is mirror-symmetric about the mesh axis. Those two phases are exact *by
symmetry*, not by measurement. **The informative points are 15° and 45°.**

| test | result | tolerance |
|---|---|---|
| mode selection (`mode_number = 4`) | phase 0.000° = 90° mod 90; a₄ = 0.0387, a₆ = 0.00051 (1.3%) | 2°, off-mode ≤ 0.33 |
| isotropic null (`δ = 0`) | a₆ = 0.00051 against 0.0321 → **ratio 0.016** | ≤ 0.1 |
| off-mode vs mesh | 0.0054 (nx=48) → 0.0017 (nx=96), decreasing | must decrease |

The square mesh imprints a four-fold bias on a circle, so the off-mode channel is never exactly
zero. It is distinguished from physics by refinement — the same test used on the T1-08 contact
checkerboard.

## Recalescence inverts the pattern

`T_max` crosses `T_e` partway through every run. Past that the driving force
`atan(γ(T_e − T))` is negative, the grain **melts**, and because melting is fastest where growth
was slowest the shape inverts by exactly half a lobe: the `m = 4` phase steps 0° → −45°. This is
real and is reported as a diagnostic, not scored as phase drift. Every measurement here is taken
before it, which is what the declared measurement point requires — and the guard is checked, not
assumed.

## Scope

**Given up:** the "dendrite-growth scaling" half of checklist item 5.3. No tip velocity, no LGK
exponent, no steady-growth claim. The qualitative result that tip velocity rises monotonically with
undercooling is retained only as a diagnostic. This is a genuine reduction in scope.

**Not covered:** absolute interfacial energy, kinetic coefficient calibration to any real alloy,
sidebranching, or three dimensions.
