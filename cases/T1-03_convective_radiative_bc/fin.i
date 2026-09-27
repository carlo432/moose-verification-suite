[Mesh]
  type = GeneratedMesh
  dim = 2
  nx = 20
  ny = 4
  xmin = 0
  xmax = 1
  ymin = 0
  ymax = 0.1
  elem_type = QUAD4
[]

[Variables]
  [T]
  []
[]

[ICs]
  [initial]
    type = ConstantIC
    variable = T
    value = 300
  []
[]

[Kernels]
  [conduction]
    type = HeatConduction
    variable = T
  []
[]

[BCs]
  [base]
    type = DirichletBC
    variable = T
    boundary = left
    value = 400
  []
  [tip]
    type = NeumannBC
    variable = T
    boundary = right
    value = 0
  []
  [side_top]
    type = ConvectiveHeatFluxBC
    variable = T
    boundary = top
    T_infinity = 300
    heat_transfer_coefficient = 0.5
    heat_transfer_coefficient_dT = 0
  []
  [side_bottom]
    type = ConvectiveHeatFluxBC
    variable = T
    boundary = bottom
    T_infinity = 300
    heat_transfer_coefficient = 0.5
    heat_transfer_coefficient_dT = 0
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
    variable = T
    boundary = right
  []
  [base_heat_rate]
    type = SideDiffusiveFluxIntegral
    variable = T
    boundary = left
    diffusivity = 1
  []
  [top_temperature_integral]
    type = SideIntegralVariablePostprocessor
    variable = T
    boundary = top
  []
  [bottom_temperature_integral]
    type = SideIntegralVariablePostprocessor
    variable = T
    boundary = bottom
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
