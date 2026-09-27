[Mesh]
  type = GeneratedMesh
  dim = 1
  nx = 40
  xmin = 0
  xmax = 2
  elem_type = EDGE2
[]

[Variables]
  [c]
  []
[]

[ICs]
  [initial]
    type = ConstantIC
    variable = c
    value = 0
  []
[]

[Kernels]
  [diffusion]
    type = CoefDiffusion
    variable = c
    coef = 1
  []
  [reaction]
    type = CoefReaction
    variable = c
    coefficient = 1
  []
[]

[BCs]
  [surface]
    type = DirichletBC
    variable = c
    boundary = left
    value = 1
  []
  [far]
    type = NeumannBC
    variable = c
    boundary = right
    value = 0
  []
[]

[VectorPostprocessors]
  [profile]
    type = LineValueSampler
    variable = c
    start_point = '0 0 0'
    end_point = '2 0 0'
    num_points = 41
    sort_by = x
    execute_on = TIMESTEP_END
  []
[]

[Executioner]
  type = Steady
  solve_type = NEWTON
  nl_abs_tol = 1e-12
  l_tol = 1e-12
[]

[Outputs]
  csv = true
[]
