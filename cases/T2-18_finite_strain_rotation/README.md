# T2-18 — Finite-strain elastic rotation

This case uses MOOSE's version-matched one-element elastic rotation test. It first applies a tiny uniaxial extension and then rotates the element through 90 degrees with finite-strain kinematics.

For a rigid rotation, `F=R`, `RᵀR=I`, and the objective elastic strain is zero; the late-stage stress should therefore remain at the extension-state value without spurious rotation stress. The verifier compares principal stresses (an objective tensor measure) through the rotation stage and normalizes the residual against the `1e6` elastic modulus. A prior componentwise maximum-stress diagnostic was rejected because it changed under basis rotation and created a false FAIL.

This does not demonstrate a Neo-Hookean tensile stress–stretch curve; it verifies the more fundamental finite-strain objectivity invariant and reports that limitation explicitly.
