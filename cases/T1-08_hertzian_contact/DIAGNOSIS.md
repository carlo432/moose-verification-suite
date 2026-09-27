# T1-08 — why four rounds of refinement never moved the error

Investigated 2026-08-03. Conclusion: **the shipped seed is not a Hertz problem, and the reference was
taken from a comment describing a different problem.** The case has to be rebuilt; no amount of mesh
or penalty work will close it.

All numbers below are from runs in a scratchpad copy, not from `out/`.

## 1. The reference describes a model the input does not implement

`reference.json` derives `a = 0.1` from the seed's header comment:

```
# Let R1 = R2 = 2.  Then R = 1.
# Let nu1 = nu2 = 0.25, E1 = E2 = 1.40625e7.  Then E = 7.5e6.
# Let F = 10000.  Then a = 0.1, d = 0.01.
```

The input's `[Materials]` block does not do this. Block `1` is the sphere at `E = 1.40625e7,
nu = 0.25`, but block `1000` — the counter-body — is **`E = 1e6, nu = 0.0`**:

| | E* | ratio |
|---|---:|---|
| seed header (both bodies 1.40625e7) | 7,500,000 | — |
| what the input actually specifies | 937,500 | **8× softer** |

And block `1000` contains **one element** (mesh is 168 nodes, 139 elements total: 138 + 1). A single
element is neither rigid nor an elastic half-space, so *no* closed-form Hertz `E*` applies to it at
all. Hertz requires two elastic half-spaces.

Measured `a = 0.1374` sits between the header prediction (0.0996–0.1254) and the actual-modulus
prediction (0.199–0.251) — consistent with a thin compliant layer, which is exactly what one element
is. That is why the discrepancy is **flat under refinement**: it is a model-form mismatch, not
discretization.

The seed author says as much in the same header:

> `## Note: There is not a good way to check the result. The standard approach is to map contact`
> `## pressure as a function of radius, but we don't have the contact pressure available.`

## 2. The load was never the assumed load

`a = 0.1` assumes `F = 10000 N`. The input applies no force — it is **displacement-controlled**, a
`FunctionDirichletBC` ramping `disp_y` to `-0.01` on boundary 2. Nobody checked what force that
develops. Adding a `SidesetReaction` postprocessor:

```
time   maxdisp    react_top
1.0    -0.01     -18852        <- the model develops 18852 N, not 10000 N
```

So for four rounds the measured contact patch has been compared against a Hertz radius for a load
1.9× smaller than the one actually applied.

The seed *does* define a force-control function that is **never referenced anywhere**:

```
[./pressure]
  scale_factor = 795.77471545947674 # 10000/pi/2^2
```

Switching to it (`type = Pressure`, `boundary = 2`, `function = pressure`) gives `react_top = 9138.7 N`
— 8.6 % under 10000 because the top face radius is ~1.912, not the 2.0 the scale factor assumes.

## 3. Friction

`model = coulomb`, `friction_coefficient = 0.4`. Hertz is frictionless. Corrected to `frictionless`
in the runs below.

## 4. With load, friction and mesh all corrected, it still does not converge

Force-controlled, frictionless, uniform refinement 0→3, comparing against Hertz **at each run's own
measured reaction force** (so the load mismatch cannot contaminate it). `a` is from a
`p² vs r²` linear fit of `p(r) = p0·sqrt(1 - r²/a²)`:

```
refine  nodes  F_react   a_fit  a_Hertz  err_a       p0  p0_Hertz  err_p0
     0      4   9138.7  0.13231  0.09704  0.363   198492    463343   0.572
     1      8   9521.6  0.13885  0.09838  0.411   224724    469726   0.522
     2     17   9744.1  0.13692  0.09914  0.381   240862    473357   0.491
     3     36   9867.0  0.13737  0.09955  0.380   250959    475339   0.472
```

Nine-fold increase in contact nodes, error flat at ~38 %. That is the signature this project has now
hit four times: **an error that does not move under refinement is a wrong reference or a wrong model,
never a discretization error.**

## What to do

Do not try to rescue this seed. Build the case `PLAN.md` actually specifies:

1. An axisymmetric sphere (or spherical cap) of known radius against **either** a rigid analytical
   plane **or** a second body of the *same* material, deep enough to behave as a half-space.
2. **Force control**, with a `SidesetReaction` postprocessor asserting the applied load — and assert
   `sum(contact_pressure · nodal_area) == F_applied` before comparing anything to Hertz. That single
   assertion would have caught this on day one.
3. `frictionless`.
4. Graded mesh with ≥ 20 nodes inside the contact patch at the *base* level, refined ×2 twice.
5. Compare `a`, `p0`, and the full `p(r)` at the measured force, plus a penalty sweep showing the
   answer is converged with respect to penalty.

Until then the honest verdict is **BLOCKED on model form**, not FAIL — MOOSE has not been shown to
get anything wrong here. The current FAIL row asserts a discrepancy against Hertz that the model was
never posed to satisfy.
