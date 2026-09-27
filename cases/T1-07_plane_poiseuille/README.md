# T1-07 — laminar plane-channel flow (Poiseuille)

This finite-volume INS case solves fully developed pressure-driven flow between parallel plates,
with half-height `h=1`, viscosity `mu=0.5`, density `rho=1.1`, and pressure gradient `dp/dx=-1`.
The exact profile is `u(y)=(1-y²)`, so `u_max/u_avg=3/2`, the plane-channel `f Re` is 96, and
the mass flow per unit depth is `rho * integral(u dy) = 1.4666667`.

The run refines the transverse mesh through `ny={2,4,8,16}` while sampling the centerline profile.
`verify.py` computes the normalized L2 profile error, maximum/average velocity ratio, and compares
inlet/outlet volumetric mass flow from `VolumetricFlowRate` postprocessors. The outlet and inlet
flow equality is an internal conservation check independent of the analytic profile.

This verifies a steady, incompressible, laminar finite-volume discretization, not turbulence,
entrance effects, compressibility, or a full developing-channel correlation. The benchmark is a
plane channel; circular-pipe `f Re=64` is not applicable here.
