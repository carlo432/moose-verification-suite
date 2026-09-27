# T1-11 — One-group neutron diffusion eigenvalue

The local `ne.i` is an input-only one-group bare-slab problem: `-D phi'' + Sigma_a phi = (1/k) nuSigma_f phi` with `D=1`, `Sigma_a=0.1`, `nuSigma_f=1`, and `L=10`. The separated solution is `phi=sin(pi*x/L)` and `k = 1/(0.1 + (pi/10)^2) = 5.0328128322`.

`run.sh` performs three-level slab and radial-sphere refinements (`8,16,32` elements). The sphere uses MOOSE's `RSPHERICAL` coordinate weighting and the independently derived bare-sphere reference, `k=5.0328128322`; the finest sphere error is `5.1e-5` with observed order 1.98. The normalized flux-shape L2 errors are `7.5e-9` (slab) and `5.1e-4` (sphere), below the declared 1% criterion. The reference contract was committed before the corresponding successful solves, so this case is PASS.

An independent Robin/extrapolated-boundary calculation is also recorded: using extrapolation
length `2D`, the fundamental closed-form estimate is `k=6.57085106`. This is a boundary-condition
cross-check, not a second MOOSE solve.

This case does not demonstrate a transport-vs-diffusion or OpenMC comparison, and the live
MOOSE runs use Dirichlet zero flux at the outer radius rather than an extrapolated transport
boundary. Those limitations are reflected in the result rather than hidden.
