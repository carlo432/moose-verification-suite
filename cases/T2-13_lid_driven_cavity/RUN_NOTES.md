# T2-13 run status

The 128x128 benchmark-resolution run was **abandoned**, not forgotten. It reached 19 of 120 steps
in about 4.5 hours (~14 min/step); finishing would have taken over a day. The partial Exodus
`out/cavity_128_long.e` (t=8) is left in place but is far from steady and carries no acceptance.

The mesh study instead uses **three meshes all run to t=100**: `cavity_32_t100`, `cavity_48_t100`
and `cavity_64_long2`. Comparing meshes at matched physical time is the right comparison anyway --
Ghia is a steady reference, so an under-converged fine mesh is further from it than a converged
coarse one, which is exactly the trap the old selection rule fell into.
