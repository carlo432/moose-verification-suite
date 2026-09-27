# T1-06 — power-law secondary creep

This case verifies the registered Norton material in a constant-traction, constant-temperature
uniaxial cube. The prescribed law is

```
epsilon_dot = A sigma^n exp[-Q/(R T)]
```

with `A=1e-6`, `n=3`, `Q=50000 J/mol`, and `R=8.314 J/mol/K`. A 10-second pressure hold is run at
three stresses (50, 100, 150 MPa) and three temperatures (800, 1000, 1200 K). The verifier fits
`log(epsilon_dot/sigma^n)` against `1/T` to recover `Q` and `A`, and fits stress-rate scaling to
recover `n`. A three-level timestep study checks the 100 MPa, 1000 K strain against the closed-form
constant-rate result.

This is an input/material round-trip verification: the same constants generate and evaluate the
reference, and the case passes as [A] verification. It is not independent experimental validation;
no published-alloy [E] claim is made. Primary and tertiary creep are also outside the Norton
secondary-creep model.
