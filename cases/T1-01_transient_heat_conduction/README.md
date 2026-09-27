# T1-01 — transient heat conduction

This case verifies one-dimensional transient conduction after a step in surface temperature. A
semi-infinite solid starts at `T_i = 300 K`; at `t = 0`, its surface is set to `T_s = 400 K`.
The constant-property diffusivity is `alpha = k/(rho c_p) = 1 m^2/s`. The MOOSE domain is the
finite interval `0 <= x <= 4 m`, with the far boundary held at 300 K. At the final time,
`4 sqrt(alpha t_end) = 2 m < L`, and the omitted semi-infinite tail is therefore negligible.

The reference is the similarity solution

```
T(x,t) = T_s + (T_i - T_s) erf(x / (2 sqrt(alpha t))).
```

`verify.py` evaluates this expression with `scipy.special.erf`, compares the numerical profile in
an L2 norm at three times, and reports the scalar value at `x=1 m, t=0.25 s` (`315.729920705 K`).
Four spatial levels are run with BDF2. A separate smooth-start study initializes the exact solution
at physical time 0.01 s, then compares backward Euler and Crank–Nicolson temporal orders at physical
time 0.25 s. The reference and tolerances were committed before the first successful solve.

This is verification of the discretized heat equation, not a material validation: properties are
constant, the medium is one-dimensional, radiation and convection are absent, and the finite far
boundary is an approximation to the semi-infinite domain. It does not demonstrate nonlinear or
temperature-dependent conduction, phase change, or multidimensional heat transfer.
