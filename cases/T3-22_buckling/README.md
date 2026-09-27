# T3-22 — Buckling substitute

MOOSE has no exposed geometric-stiffness eigenproblem, so this case records the prescribed
imperfection/Southwell substitute. The reference is Euler's pinned-column load
`P_cr = pi² E I/L² = 2.4674011` for the declared unit parameters. The verifier reports the
three imperfection amplitudes and the analytic Southwell line, while `beam_seed.i` is a
version-matched small-strain beam smoke input.

This does not demonstrate a MOOSE linear buckling eigensolver or a nonlinear post-buckling path;
those require geometric stiffness and continuation support not exposed by the compiled app.
