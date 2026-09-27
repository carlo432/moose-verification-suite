# T2-15 -- conjugate heat transfer, thermally developed parallel-plate channel.
#
# Rebuilt from channel.i.  The original geometry could not converge to Nu=8.235:
#   * the solid wall was 1 unit thick with k=10, so axial conduction redistributed
#     heat toward the cold inlet and the interface flux was NOT uniform -- which is
#     the assumption behind the constant-q'' reference.  Measured dTb/dy was 0.155
#     against the 0.2586 the energy balance requires.
#   * the channel was 8 long (L/D_h = 2), too short to reach thermal development:
#     T_w - T_b varied by 50% across the nominal developed region.
# Here the wall is 0.1 thick with k=1 (axial conductance 0.1 against an advective
# capacity of 7.73, so redistribution is negligible) and the channel is 24 long
# (L/D_h = 6 against a thermal entry length of about 3.1).
#
# Fluid x in [0.1, 2.1] -> plate spacing 2, D_h = 4A/P = 4(2)/(2) = 4.
# Applied outer flux q'' = 1 on each wall; k_fluid = 1.

[Mesh]
  [gen]
    type = GeneratedMeshGenerator
    dim = 2
    xmin = 0
    xmax = 2.2
    ymin = 0
    ymax = 24
    nx = 8
    ny = 32
    elem_type = QUAD4
  []
  [fluid]
    type = SubdomainBoundingBoxGenerator
    input = gen
    bottom_left = '0.1 0 0'
    top_right = '2.1 24 0'
    block_id = 1
  []
  [break]
    type = BreakBoundaryOnSubdomainGenerator
    input = fluid
  []
  [interface0]
    type = SideSetsBetweenSubdomainsGenerator
    input = break
    primary_block = '0'
    paired_block = '1'
    new_boundary = interface0
  []
  [interface1]
    type = SideSetsBetweenSubdomainsGenerator
    input = interface0
    primary_block = '1'
    paired_block = '0'
    new_boundary = interface1
  []
[]

[Variables]
  [velocity]
    family = LAGRANGE_VEC
    block = 1
  []
  [p]
    block = 1
  []
  [temp_fluid]
    block = 1
  []
  [temp_wall]
    block = 0
  []
[]

[Kernels]
  [mass]
    type = INSADMass
    variable = p
    block = 1
  []
  [mass_pspg]
    type = INSADMassPSPG
    variable = p
    block = 1
  []
  [momentum_advection]
    type = INSADMomentumAdvection
    variable = velocity
    block = 1
  []
  [momentum_viscous]
    type = INSADMomentumViscous
    variable = velocity
    block = 1
  []
  [momentum_pressure]
    type = INSADMomentumPressure
    variable = velocity
    pressure = p
    integrate_p_by_parts = true
    block = 1
  []
  [momentum_supg]
    type = INSADMomentumSUPG
    variable = velocity
    velocity = velocity
    block = 1
  []
  [temperature_advection]
    type = INSADEnergyAdvection
    variable = temp_fluid
    block = 1
  []
  [temperature_conduction]
    type = ADHeatConduction
    variable = temp_fluid
    block = 1
  []
  [wall_conduction]
    type = ADHeatConduction
    variable = temp_wall
    block = 0
  []
[]

[BCs]
  [inlet_velocity]
    type = VectorFunctionDirichletBC
    variable = velocity
    boundary = bottom_to_1
    function_x = zero
    function_y = inlet_profile
  []
  [outlet_velocity]
    type = VectorFunctionDirichletBC
    variable = velocity
    boundary = top_to_1
    function_x = zero
    function_y = inlet_profile
  []
  [wall_velocity]
    type = VectorFunctionDirichletBC
    variable = velocity
    boundary = 'interface0 interface1'
    function_x = zero
    function_y = zero
  []
  [pressure_pin]
    type = DirichletBC
    variable = p
    boundary = bottom_to_1
    value = 0
  []
  [inlet_temperature]
    type = DirichletBC
    variable = temp_fluid
    boundary = bottom_to_1
    value = 0
  []
  [outer_heat_left]
    type = NeumannBC
    variable = temp_wall
    boundary = left
    value = 1
  []
  [outer_heat_right]
    type = NeumannBC
    variable = temp_wall
    boundary = right
    value = 1
  []
[]

[Functions]
  [inlet_profile]
    type = ParsedFunction
    expression = '5.8*(x-0.1)*(2.1-x)'
  []
  [zero]
    type = ParsedFunction
    expression = '0'
  []
[]

[Materials]
  [fluid]
    type = INSADStabilized3Eqn
    velocity = velocity
    pressure = p
    temperature = temp_fluid
    block = 1
  []
  [fluid_props]
    type = ADHeatConductionMaterial
    thermal_conductivity = 1
    specific_heat = 1
    block = 1
  []
  [fluid_transport]
    type = ADGenericConstantMaterial
    prop_names = 'rho mu cp k'
    prop_values = '1 0.1 1 1'
    block = 1
  []
  [wall_props]
    type = ADHeatConductionMaterial
    thermal_conductivity = 1
    specific_heat = 1
    block = 0
  []
  [alpha_wall]
    type = ADGenericConstantMaterial
    prop_names = alpha_wall
    prop_values = 1e6
    block = 1
  []
[]

[InterfaceKernels]
  [interface_coupling]
    type = ConjugateHeatTransfer
    variable = temp_fluid
    T_fluid = temp_fluid
    neighbor_var = temp_wall
    boundary = interface1
    htc = alpha_wall
  []
[]

[Preconditioning]
  [smp]
    type = SMP
    full = true
  []
[]

[Executioner]
  type = Steady
  solve_type = NEWTON
  nl_rel_tol = 1e-9
  nl_max_its = 30
  petsc_options_iname = '-pc_type'
  petsc_options_value = 'lu'
[]

[Outputs]
  exodus = true
  csv = true
[]

[Postprocessors]
  [interface_left_flux]
    type = ADSideDiffusiveFluxIntegral
    variable = temp_wall
    boundary = interface0
    diffusivity = thermal_conductivity
  []
  [interface_right_flux]
    type = ADSideDiffusiveFluxIntegral
    variable = temp_fluid
    boundary = interface1
    diffusivity = thermal_conductivity
  []
  [outer_left_flux]
    type = ADSideDiffusiveFluxIntegral
    variable = temp_wall
    boundary = left
    diffusivity = thermal_conductivity
  []
  [outer_right_flux]
    type = ADSideDiffusiveFluxIntegral
    variable = temp_wall
    boundary = right
    diffusivity = thermal_conductivity
  []
  [fluid_inlet_diffusive_flux]
    type = ADSideDiffusiveFluxIntegral
    variable = temp_fluid
    boundary = bottom_to_1
    diffusivity = thermal_conductivity
  []
  [fluid_outlet_diffusive_flux]
    type = ADSideDiffusiveFluxIntegral
    variable = temp_fluid
    boundary = top_to_1
    diffusivity = thermal_conductivity
  []
[]
