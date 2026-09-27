# T2-20 — Neutronics-shaped heat source to conduction

This case adapts the heat-source bar seed to a positive cosine-plus-uniform source, `q(x)=q0[1+cos(πx/L)]`, with equal fixed surface temperatures. The analytic conduction profile is integrated exactly and checked on three meshes.

It verifies the source-to-temperature coupling path and profile convergence. The source is an analytic stand-in for a normalized eigenflux; this does not claim a live T1-11 eigenvector transfer, power normalization, or temperature feedback on cross sections. Those limitations are explicit in `result.json`.
