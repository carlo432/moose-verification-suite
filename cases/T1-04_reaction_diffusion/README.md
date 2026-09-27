# T1-04 — reaction–diffusion penetration depth

This is a one-dimensional steady diffusion problem with a first-order volumetric sink:
`-D c'' + k c = 0`, `c(0)=1`, and `c'(L)=0`, using `D=k=1` so the penetration length
`lambda=sqrt(D/k)=1`. The closed-form profile is

```
c(x) = cosh((L-x)/lambda) / cosh(L/lambda).
```

The run sweeps `L/lambda = 0.5, 2, 10`, covering reaction-limited through diffusion-limited
regimes, and uses four meshes in each regime. `verify.py` checks the profile pointwise through a
normalized L2 norm and independently fits lambda back from each numerical profile.

This verifies a linear constant-property transport equation, not a calibrated chemical reaction:
there is no advection, nonlinear kinetics, multicomponent coupling, or concentration-dependent
diffusivity. The large `L/lambda=10` case is intentionally included because a fit alone can hide a
systematic offset in the nearly depleted tail.
