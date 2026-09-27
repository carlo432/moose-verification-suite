# T3-24 — Fluid–structure interaction

The version-matched `fsi_flat_channel.i` is the closest shipped ALE/PSPG coupling seed. It is
used as a startup smoke test for the fluid and elastic blocks. The intended Turek–Hron FSI1 tip
displacement anchor is recorded in the contract, but the seed geometry and loading are not FSI1.

This row is therefore BLOCKED rather than pretending that a flat-channel smoke run validates the
benchmark. It does not demonstrate the Turek–Hron obstacle geometry, steady Re=20 tip displacement,
or a converged mesh study.
