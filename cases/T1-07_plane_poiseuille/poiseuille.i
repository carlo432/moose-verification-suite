[Mesh]
  type = GeneratedMesh
  dim = 2
  xmin = 0
  xmax = 10
  ymin = -1
  ymax = 1
  nx = 20
  ny = 2
[]

[GlobalParams]
  rhie_chow_user_object = 'rc'
[]

[UserObjects]
  [rc]
    type = INSFVRhieChowInterpolator
    u = u
    v = v
    pressure = pressure
  []
[]

[Variables]
  [u]
    type = INSFVVelocityVariable
    initial_condition = 1
    two_term_boundary_expansion = true
  []
  [v]
    type = INSFVVelocityVariable
    initial_condition = 0
    two_term_boundary_expansion = true
  []
  [pressure]
    type = INSFVPressureVariable
    two_term_boundary_expansion = true
  []
[]

[FVKernels]
  [mass]
    type = INSFVMassAdvection
    variable = pressure
    advected_interp_method = average
    velocity_interp_method = average
    rho = 1.1
  []
  [u_advection]
    type = INSFVMomentumAdvection
    variable = u
    advected_interp_method = average
    velocity_interp_method = average
    rho = 1.1
    momentum_component = x
  []
  [u_viscosity]
    type = INSFVMomentumDiffusion
    variable = u
    mu = 0.5
    momentum_component = x
  []
  [u_pressure]
    type = INSFVMomentumPressure
    variable = u
    momentum_component = x
    pressure = pressure
  []
  [v_advection]
    type = INSFVMomentumAdvection
    variable = v
    advected_interp_method = average
    velocity_interp_method = average
    rho = 1.1
    momentum_component = y
  []
  [v_viscosity]
    type = INSFVMomentumDiffusion
    variable = v
    mu = 0.5
    momentum_component = y
  []
  [v_pressure]
    type = INSFVMomentumPressure
    variable = v
    momentum_component = y
    pressure = pressure
  []
[]

[FVBCs]
  [inlet-u]
    type = INSFVInletVelocityBC
    boundary = left
    variable = u
    function = exact_u
  []
  [inlet-v]
    type = INSFVInletVelocityBC
    boundary = left
    variable = v
    function = exact_v
  []
  [walls-u]
    type = INSFVNoSlipWallBC
    variable = u
    boundary = 'top bottom'
    function = exact_u
  []
  [walls-v]
    type = INSFVNoSlipWallBC
    variable = v
    boundary = 'top bottom'
    function = exact_v
  []
  [outlet_p]
    type = INSFVOutletPressureBC
    boundary = right
    variable = pressure
    function = exact_p
  []
[]

[Functions]
  [exact_u]
    type = ParsedFunction
    expression = '0.5*(1-y^2)/mu'
    symbol_names = mu
    symbol_values = 0.5
  []
  [exact_v]
    type = ParsedFunction
    expression = 0
  []
  [exact_p]
    type = ParsedFunction
    expression = '10-x'
  []
[]

[VectorPostprocessors]
  [profile]
    type = LineValueSampler
    variable = 'u v'
    start_point = '5 -1 0'
    end_point = '5 1 0'
    num_points = 3
    sort_by = y
    execute_on = TIMESTEP_END
  []
  [pressure_line]
    type = LineValueSampler
    variable = pressure
    start_point = '0 0 0'
    end_point = '10 0 0'
    num_points = 21
    sort_by = x
    execute_on = TIMESTEP_END
  []
[]

[Postprocessors]
  [L2u]
    type = ElementL2Error
    variable = u
    function = exact_u
  []
  [inlet_flow]
    type = VolumetricFlowRate
    boundary = left
    vel_x = u
    vel_y = v
    advected_quantity = 1.1
  []
  [outlet_flow]
    type = VolumetricFlowRate
    boundary = right
    vel_x = u
    vel_y = v
    advected_quantity = 1.1
  []
[]

[Executioner]
  type = Steady
  solve_type = NEWTON
  petsc_options_iname = '-pc_type -pc_factor_mat_solver_type'
  petsc_options_value = 'lu superlu_dist'
[]

[Outputs]
  csv = true
[]
