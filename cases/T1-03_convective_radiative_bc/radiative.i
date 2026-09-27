[Mesh]
  type = GeneratedMesh
  dim = 1
  nx = 20
  xmin = 0
  xmax = 0.01
  elem_type = EDGE2
[]

[Variables]
  [T]
  []
[]

[ICs]
  [initial]
    type = ConstantIC
    variable = T
    value = 500
  []
[]

[Kernels]
  [conduction]
    type = HeatConduction
    variable = T
  []
  [time]
    type = HeatConductionTimeDerivative
    variable = T
  []
[]

[BCs]
  [left_radiation]
    type = FunctionRadiativeBC
    variable = T
    boundary = left
    emissivity_function = '1'
    Tinfinity = 300
    stefan_boltzmann_constant = 5.670374e-8
  []
  [right_radiation]
    type = FunctionRadiativeBC
    variable = T
    boundary = right
    emissivity_function = '1'
    Tinfinity = 300
    stefan_boltzmann_constant = 5.670374e-8
  []
[]

[Materials]
  [properties]
    type = GenericConstantMaterial
    prop_names = 'density specific_heat thermal_conductivity'
    prop_values = '1000000 1 100'
  []
[]

[Postprocessors]
  [average_temperature]
    type = ElementAverageValue
    variable = T
    execute_on = TIMESTEP_END
  []
[]

[Executioner]
  type = Transient
  scheme = bdf2
  dt = 0.1
  end_time = 100
  solve_type = NEWTON
  nl_abs_tol = 1e-11
  l_tol = 1e-12
[]

[Outputs]
  csv = true
[]
