# T1-08 — Hertzian contact

This case exercises MOOSE's axisymmetric penalty contact mechanics using the shipped sphere-on-sphere seed. For two radius-2 spheres, the effective radius is `R=1`; with `E=1.40625e7`, `nu=0.25`, and load `F=10000`, Hertz theory gives `a=0.1`, `delta=0.01`, and `p0=477464.8293`. The input has been corrected to same-material, frictionless, pressure-controlled contact.

`run.sh` runs three penalty stiffnesses at three built-in uniform-refinement levels and `verify.py` extracts the final Exodus contact-pressure field. The active radius is the largest radial node above 1% of the peak pressure; this operational definition is recorded because the threshold remains mesh-edge sensitive.

The corrected sweep still gives a finest fitted radius of about `0.134` and an integrated force of `9.28 kN`. The remaining counterbody is only one compliant element deep, so it is not a Hertz half-space; the verifier therefore reports BLOCKED on model form rather than asserting that MOOSE fails Hertz theory. A deep half-space or rigid-plane rebuild is required before promotion. The case does not demonstrate frictional sliding or finite strain.
