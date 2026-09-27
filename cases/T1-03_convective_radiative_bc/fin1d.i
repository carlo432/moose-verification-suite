[Mesh]
  type = GeneratedMesh
  dim = 1
  xmin = 0
  xmax = 1
  nx = 20
  elem_type = EDGE2
[]

[Variables]
  [theta]
  []
[]

[Kernels]
  [diffusion]
    type = Diffusion
    variable = theta
  []
  [side_convection]
    type = CoefReaction
    variable = theta
    coefficient = 10
  []
[]

[BCs]
  [base]
    type = DirichletBC
    variable = theta
    boundary = left
    value = 100
  []
  [tip]
    type = NeumannBC
    variable = theta
    boundary = right
    value = 0
  []
[]

[Materials]
  [conductivity]
    type = GenericConstantMaterial
    prop_names = thermal_conductivity
    prop_values = 1
  []
[]

[Postprocessors]
  [tip_temperature]
    type = SideAverageValue
    variable = theta
    boundary = right
  []
  [base_heat_rate]
    type = SideDiffusiveFluxIntegral
    variable = theta
    boundary = left
    diffusivity = 1
  []
  [theta_integral]
    type = ElementIntegralVariablePostprocessor
    variable = theta
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
