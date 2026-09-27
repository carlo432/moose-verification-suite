# T1-05 — J2 elastoplastic thick cylinder

Plane-strain thick-cylinder problem: inner radius 1 m, outer radius 2 m, Young's modulus 210 GPa,
Poisson ratio 0.3, yield stress 100 MPa. Internal pressure is ramped on an RZ mesh using the
registered `IsotropicPlasticityStressUpdate` and `ComputeMultipleInelasticStress` objects. Writing
`k = 2 sigma_y/sqrt(3) = 115.470 MPa`, the closed-form von Mises references are

```
p_y   = (sigma_y/sqrt(3)) (1-a^2/b^2)          = 43.3013 MPa
p(c)  = (sigma_y/sqrt(3)) [2 ln(c/a) + 1 - c^2/b^2]
p_lim = k ln(b/a)                              = 80.0377 MPa
sigma_rr(r) = -k ln(b/r),  sigma_tt(r) = k (1 - ln(b/r))     (fully plastic)
```

## What is measured

**`p_lim` is the applied pressure at which the plastic front reaches the outer wall.** Full-section
yield *is* plastic collapse for this problem, so this is the declared quantity itself. It replaces
the previous `max effective plastic strain >= 1` threshold, which was an arbitrary operational
proxy; `reference.json` records the substitution and was committed before any of these runs.

`SideAverageValue` of `eff_plastic_strain` on the outer boundary is exactly zero until the front
arrives, so the arrival is a sharp event rather than a threshold crossing.

| | measured | closed form | relative error |
|---|---:|---:|---:|
| `p_lim` (nx=160, 0.2 MPa increment) | 79.600 MPa | 80.0377 MPa | **0.547%** |
| `p_y` yield onset (nx=160) | 43.482 MPa | 43.3013 MPa | 0.417% |
| `p(c)` front curve, 65 samples over `c∈[1.2,1.8]` | — | — | 1.22% max |
| fully-plastic `sigma_rr`, `sigma_tt` at collapse | — | — | **0.608% L2** |

Declared tolerance is 2% on `p_lim`, 1% on `p_y`, 2% on `p(c)` and 2% on the stress field.

## Measurement resolution

The load increment is **0.2 MPa, which is 0.25% of `p_lim`** — eight times finer than the 2%
tolerance it is judged against. This is the point of review finding F2: the earlier ramp sampled
only multiples of 2 MPa, so the published `80.0` was a load step rather than a measurement and the
row could not fail. The mesh sweep now returns four *different* values, which quantization could
not produce:

```
nx     20     40     80    160
p_lim  79.8   79.7   79.6   79.6      (analytic 80.0377)
```

Load-step controls at nx=160 give 79.6 MPa at 0.4 MPa increments, 79.6 at 0.2, and 79.7 at 0.1 —
a 0.125% spread. The residual dependence is genuine path dependence of the plastic solution, not
sampling: different increments accumulate slightly different plastic states on the way to the limit
point.

## The fully-plastic stress field

At the collapse step the whole wall is at yield, so the closed-form field applies and is compared
pointwise. The von Mises condition holds at `(sigma_tt - sigma_rr)/k = 0.99518` across the wall,
and the combined `sigma_rr`/`sigma_tt` L2 error is 0.608%. This is the resolved stress plateau
whose absence previously kept the case PARTIAL.

`sigma_zz` is reported as a diagnostic and is **excluded from acceptance**, because the fully
plastic form `k(1/2 - ln(b/r))` assumes developed plastic flow. At the instant of collapse the
outer wall has only just yielded, so `sigma_zz` there is still the *elastic* `nu(sigma_rr+sigma_tt)`
— 33.653 MPa measured against 33.641 MPa predicted, agreeing to 0.04% — and it migrates toward the
plastic `(sigma_rr+sigma_tt)/2` at the inner wall where plastic strain has accumulated. Scoring
against the fully-plastic form would fail the case for being right.

## Past the limit load

For `p > p_lim` the small-strain perfectly plastic system has **no equilibrium solution**. The
solver either fails outright (nx=20 aborts at 81.4 MPa, which is the physically correct outcome) or
converges to `|R| ~ 1e-14` while alternating between two spurious branches with a sign-flipped hoop
stress — `max_shh = -115 MPa` on one step and `+114 MPa` on the next, with the inner wall
displacement flipping to −2.2 m. The ramp therefore stops at 80.8 MPa and the verifier discards
every step at and after collapse. Nothing is claimed about post-collapse response.

## Scope

Not a validation of hardening, cyclic plasticity, finite-strain effects, or pressure-vessel design.
The model is small-strain, plane-strain, monotonic, perfectly plastic, and input-file-only.
