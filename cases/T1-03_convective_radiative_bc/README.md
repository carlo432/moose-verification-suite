# T1-03 — convective and radiative thermal boundary conditions

This case has two independent subcases.

The fin is a two-dimensional thin rectangular fin (`L=1 m`, width `0.1 m`) with `k=1 W/m/K`,
base temperature 400 K, ambient 300 K, and convective side coefficient `h=0.5 W/m²/K`. The top and
bottom boundaries use `ConvectiveHeatFluxBC`; the tip is adiabatic. With unit out-of-plane depth,
`A=0.1 m²`, `P=2 m`, and `m=sqrt(hP/(kA))`, the exact solution is
`theta/theta_b=cosh[m(L-x)]/cosh(mL)`. The verifier retains this finite-width solve as a
diagnostic, and uses an exactly matching one-dimensional reduced fin (`fin1d.i`) for the declared
closed-form contract. In that subcase the tip and conservative volume-balance heat rate converge at
second order over four meshes (20–160 elements); the raw boundary-gradient postprocessor remains
available as a first-order diagnostic rather than being used to manufacture a PASS.

The radiative subcase is a short, highly conducting slab (`L=0.01 m`, `k=100 W/m/K`) with radiation
on both ends, `epsilon=1`, `T_inf=300 K`, and initial temperature 500 K. Its small characteristic
Biot number is checked explicitly. The lumped reference solves
`rho cp (L/2) dT/dt = -epsilon sigma (T^4-T_inf^4)` by quadrature and inversion. Three timestep
levels are run and the finest temperature history is compared at 10, 50, and 100 s.

This demonstrates boundary-condition and discretization behavior, not a validated radiation material
model: emissivity is prescribed, view factors are one-dimensional, properties are constant, and the
lumped radiative solution is applicable only because the independently checked Biot number is small.
