[Mesh]
  type = GeneratedMesh
  dim = 1
  nx = 20
  xmin = 0
  xmax = 4
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
    value = 300
  []
[]

[Kernels]
  [diffusion]
    type = HeatConduction
    variable = T
  []
  [time]
    type = HeatConductionTimeDerivative
    variable = T
  []
[]

[BCs]
  [surface]
    type = DirichletBC
    variable = T
    boundary = left
    value = 400
  []
  [far_field]
    type = DirichletBC
    variable = T
    boundary = right
    value = 300
  []
[]

[Materials]
  [properties]
    type = GenericConstantMaterial
    prop_names = 'thermal_conductivity specific_heat density'
    prop_values = '1 1 1'
  []
[]

[VectorPostprocessors]
  [profile]
    type = LineValueSampler
    variable = T
    start_point = '0 0 0'
    end_point = '4 0 0'
    num_points = 21
    sort_by = x
    execute_on = TIMESTEP_END
  []
[]

[Executioner]
  type = Transient
  scheme = bdf2
  dt = 0.00025
  end_time = 0.25
  solve_type = NEWTON
  nl_abs_tol = 1e-12
  l_tol = 1e-12
  num_steps = 1000
[]

[Outputs]
  csv = true
[]
