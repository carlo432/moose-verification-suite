# T2-21 — Stefan problem

The case contains a 1-D transient conduction baseline and a two-phase Stefan similarity reference. It uses a temperature-coupled `DerivativeParsedMaterial` apparent heat capacity with a Gaussian latent-heat spike around `T_m=1.5`; the amplitude `4.00316291536` is chosen so the excess integrates exactly to the declared `Lf=0.212862645754`, which the verifier checks by independent quadrature. Because the initial solid is `T_i=1.0<T_m`, the corrected two-phase similarity solution predicts `X(0.01 s)=8.504123e-4 m`. Three mushy widths (0.015, 0.03, 0.06) are run on an 800-cell mesh; the baseline sigma=0.03 front is `8.528518e-4 m` (0.287% relative error).

All three widths are within the predeclared 2% tolerance, so the result is PASS. The reference assumes equal properties in the semi-infinite two-phase limit; the finite 0.1 m domain and apparent-capacity regularization are tested by the width sweep, but no Stefan-number sweep is included.
