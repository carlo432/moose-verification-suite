# One-group, one-dimensional bare-slab diffusion eigenproblem.
# -D phi'' + Sigma_a phi = (1/k) nuSigma_f phi, phi(0)=phi(L)=0.

[Mesh]
  type = GeneratedMesh
  dim = 1
  xmin = 0
  xmax = 10
  nx = 8
[]

[Variables]
  [phi]
    order = FIRST
    family = LAGRANGE
  []
[]

[Kernels]
  [diffusion]
    type = Diffusion
    variable = phi
  []
  [absorption]
    type = CoefReaction
    variable = phi
    coefficient = 0.1
  []
  [fission]
    type = MassEigenKernel
    variable = phi
  []
[]


[BCs]
  [left]
    type = DirichletBC
    variable = phi
    boundary = left
    value = 0
  []
  [right]
    type = DirichletBC
    variable = phi
    boundary = right
    value = 0
  []
[]

[Executioner]
  type = NonlinearEigen
  bx_norm = 'unorm'
  free_power_iterations = 4
  nl_abs_tol = 1e-12
  nl_rel_tol = 1e-10
  k0 = 1.0
  solve_type = PJFNK
[]

[Postprocessors]
  [unorm]
    type = ElementIntegralVariablePostprocessor
    variable = phi
    execute_on = linear
  []
[]

[Outputs]
  csv = true
  exodus = true
  execute_on = 'timestep_end'
  file_base = ne
[]
