# T2-17 — Fracture J/interaction integrals

This case runs the version-matched NAFEMS R0020 crack benchmark through both MOOSE's J-integral and interaction-integral routes. Five annular contours are reported for the J path-independence check, at three uniform mesh-refinement levels.

The seed comment gives the NAFEMS analytic `J1=2.434`. The mean progresses from 2.32748 (4.38% error) on the base mesh to 2.42518 (0.362% error) on the finest mesh, with a 0.014% contour spread. The J check therefore passes its committed 3% contract. The interaction route produces equivalent-K values, but the planned SENT handbook polynomial was not independently sourced.
