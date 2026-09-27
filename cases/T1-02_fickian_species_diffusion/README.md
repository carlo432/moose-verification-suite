# T1-02 — Fickian species diffusion

The main subcase is a one-dimensional finite slab initially at normalized concentration `c0=1`,
with both surfaces held at zero concentration. Constant diffusivity is `D=0.1 m^2/s` and
`0 <= x <= 1 m`. The reference is the finite-slab series

```
c/c0 = (4/pi) sum_(n odd) exp(-D n^2 pi^2 t/L^2) sin(n pi x/L)/n.
```

The verifier compares profiles at three times, fits the spatial order over four meshes, and reports
the scalar value at `x=0.25 m, t=0.1 s`. A separate no-flux run starts from
`c = 1 + 0.2 cos(pi x/L)`. Its exact solution is the decaying cosine mode, whose integral is exactly
one for all time. The `ElementIntegralVariablePostprocessor` output is checked directly for relative
mass drift, providing the conservation test that a Dirichlet-only diffusion problem cannot provide.

This verifies the diffusion operator and its material diffusivity, not a chemical species model:
there is no advection, reaction, multicomponent coupling, concentration-dependent diffusivity, or
physical unit calibration. The Dirichlet slab has an initial/boundary compatibility corner, while the
no-flux cosine mode is smooth and is used for the conservation check.
