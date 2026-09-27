[GlobalParams]
  displacements = 'disp_x disp_y disp_z'
[]

[Mesh]
  type = GeneratedMesh
  dim = 3
  nx = 1
  ny = 1
  nz = 1
[]

[AuxVariables]
  [temp]
    initial_condition = 1000
  []
[]

[Functions]
  [pressure]
    type = PiecewiseLinear
    x = '0 10'
    y = '-100 -100'
  []
[]

[Physics/SolidMechanics/QuasiStatic]
  [all]
    strain = FINITE
    incremental = true
    add_variables = true
    generate_output = 'stress_yy creep_strain_yy'
    use_automatic_differentiation = false
  []
[]

[BCs]
  [top_pressure]
    type = Pressure
    variable = disp_y
    boundary = top
    factor = 1
    function = pressure
  []
  [bottom_fix]
    type = DirichletBC
    variable = disp_y
    boundary = bottom
    value = 0
  []
  [x_symmetry]
    type = DirichletBC
    variable = disp_x
    boundary = left
    value = 0
  []
  [y_symmetry]
    type = DirichletBC
    variable = disp_z
    boundary = back
    value = 0
  []
[]

[Materials]
  [elasticity_tensor]
    type = ComputeIsotropicElasticityTensor
    youngs_modulus = 1e6
    poissons_ratio = 0.3
  []
  [radial_return_stress]
    type = ComputeMultipleInelasticStress
    inelastic_models = power_law_creep
  []
  [power_law_creep]
    type = PowerLawCreepStressUpdate
    coefficient = 1e-6
    n_exponent = 3
    activation_energy = 50000
    temperature = temp
    substep_strain_tolerance = 0.1
    max_inelastic_increment = 0.01
  []
[]

[Executioner]
  type = Transient
  solve_type = NEWTON
  line_search = none
  automatic_scaling = true
  nl_abs_tol = 1e-10
  l_tol = 1e-10
  dt = 0.2
  end_time = 10
[]

[Postprocessors]
  [average_creep_strain]
    type = ElementAverageValue
    variable = creep_strain_yy
    execute_on = TIMESTEP_END
  []
  [average_stress]
    type = ElementAverageValue
    variable = stress_yy
    execute_on = TIMESTEP_END
  []
  [max_disp_z]
    type = NodalExtremeValue
    variable = disp_z
    execute_on = TIMESTEP_END
  []
[]

[Outputs]
  csv = true
[]
