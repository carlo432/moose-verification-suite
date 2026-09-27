# T1-10 — Allen–Cahn grain growth

The case uses a fixed-seed 64-grain `PolycrystalVoronoi` initial condition (58 tracked at the first
output), the `PolycrystalKernel`, and `FeatureFloodCount` grain tracking on a 64×64 mesh.
`FeatureVolumeVectorPostprocessor` records per-feature areas, centroids, and equivalent radii.
`run.sh` repeats the transient at `dt=20,40,80`.

The analytic target is curvature-driven growth, `R²−R₀²=k t`, hence `R∝t^(1/2)` after the initial transient. This seed contains only two grains and five steps, so it cannot provide the planned polycrystal exponent or 120° triple-junction statistics.

Late-window equivalent-radius fits at `dt=20,40,80` give exponents `-0.005, 0.057, 0.118`,
respectively. The finest run retains 26 tracked grains with a monotone count, but the exponent
remains below `1/2` and no triple-junction angle statistic is available; the verdict remains
PARTIAL.
