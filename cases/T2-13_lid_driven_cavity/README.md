# T2-13 — Lid-driven cavity benchmark

This case adapts the shipped incompressible Navier–Stokes cavity seed by replacing its parabolic lid with the discontinuous uniform lid required by the Ghia benchmark. Three mesh sizes are run with `rho=1`, `mu=0.001`, and `U_lid=1`, i.e. the intended `Re=1000` scaling.

The reference contract includes the public Re=1000 Ghia profile mirror in
`reference/ghia_re1000.json`. The runs include a 64×64 refinement plus a separate 32×32 extension
to `t=50`. The finest available 64×64 profile remains transient (u/v RMSE `0.130/0.147` in the
current artifact), while the longer n=32 run is retained as a time-extension diagnostic. No
steady benchmark profile is claimed. The t=50 n=32 run supplies u/v RMSE `0.0392/0.0478` and a
candidate primary-vortex center at `(0.5469, 0.5781)` from the minimum interior speed, but no
external vortex-center reference is claimed; the verdict stays PARTIAL.
