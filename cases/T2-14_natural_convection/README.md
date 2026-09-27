# T2-14 — Natural convection in a cavity

This case adapts the registered Boussinesq finite-volume seed to a differentially heated, no-slip square cavity. Four Rayleigh numbers (`10^3` through `10^6`) are run with side-wall temperature forcing and zero lid motion.

The intended benchmark is de Vahl Davis (1983); its Nusselt table is now source-backed in
`reference.json`. The verifier now consumes the registered `SideDiffusiveFluxIntegral` CSV
postprocessors and checks the magnitudes of the hot/cold fluxes directly. The resulting 32×32 Nu
values are `1.132, 2.295, 4.830, 10.218`; the first
two are within 4% of de Vahl Davis while the higher-Rayleigh cases miss on this coarse mesh. A
64×64 Ra=`10^5` repeat reduces the error from 6.89% to 3.42%, and the integrated hot/cold fluxes
agree to machine precision. The verifier now also extracts the horizontal velocity maximum on
the vertical cavity midplane: the Ra=`10^3` and `10^4` values are within 2% of the PLAN anchors,
while the coarse higher-Rayleigh values remain outside tolerance. A 128×128 Ra=`10^6` refinement
reduces the Nu error to 3.49% and velocity error to 3.83%, both inside the committed 4% benchmark
tolerance; hot/cold flux mismatch remains zero. The case is therefore PASS for the declared
benchmark contract. It does not claim a full velocity-profile or vortex-center comparison, and the
cited public transcription is the benchmark source.
