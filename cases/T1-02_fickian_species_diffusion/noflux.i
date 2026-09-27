[Mesh]
  type = GeneratedMesh
  dim = 1
  nx = 20
  xmin = 0
  xmax = 1
  elem_type = EDGE2
[]

[Variables]
  [c]
  []
[]

[Functions]
  [initial_profile]
    type = ParsedFunction
    expression = '1 + 0.2 * cos(pi*x)'
  []
[]

[ICs]
  [initial]
    type = FunctionIC
    variable = c
    function = initial_profile
  []
[]

[Kernels]
  [diffusion]
    type = ADMatDiffusion
    variable = c
    diffusivity = diffusivity
  []
  [time]
    type = ADTimeDerivative
    variable = c
  []
[]

[BCs]
  [left]
    type = NeumannBC
    variable = c
    boundary = left
    value = 0
  []
  [right]
    type = NeumannBC
    variable = c
    boundary = right
    value = 0
  []
[]

[Materials]
  [diffusivity]
    type = ADGenericConstantMaterial
    prop_names = diffusivity
    prop_values = 0.1
  []
[]

[Postprocessors]
  [mass]
    type = ElementIntegralVariablePostprocessor
    variable = c
    execute_on = TIMESTEP_END
  []
[]

[VectorPostprocessors]
  [profile]
    type = LineValueSampler
    variable = c
    start_point = '0 0 0'
    end_point = '1 0 0'
    num_points = 21
    sort_by = x
    execute_on = TIMESTEP_END
  []
[]

[Executioner]
  type = Transient
  scheme = bdf2
  dt = 0.00025
  end_time = 0.1
  solve_type = NEWTON
  nl_abs_tol = 1e-12
  l_tol = 1e-12
[]

[Outputs]
  csv = true
[]
