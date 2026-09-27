#
# Test the split parsed function free enery Cahn-Hilliard Bulk kernel
# The free energy used here has the same functional form as the SplitCHPoly kernel
# If everything works, the output of this test should replicate the output
# of marmot/tests/chpoly_test/CHPoly_Cu_Split_test.i (exodiff match)
#

[Mesh]
  type = GeneratedMesh
  dim = 2
  nx = 10
  ny = 10
  xmin = 0
  xmax = 60
  ymin = 0
  ymax = 60
  elem_type = QUAD4
[]

[Variables]
  [./c]
    order = FIRST
    family = LAGRANGE
    [./InitialCondition]
      type = RandomIC
      legacy_generator = false
      min = -0.1
      max = 0.1
    [../]
  [../]
  [./w]
    order = FIRST
    family = LAGRANGE
  [../]
[]

[Kernels]
  [./c_res]
    type = SplitCHParsed
    variable = c
    f_name = F
    kappa_name = kappa_c
    w = w
  [../]
  [./w_res]
    type = SplitCHWRes
    variable = w
    mob_name = M
  [../]
  [./time]
    type = CoupledTimeDerivative
    variable = w
    v = c
  [../]
[]

[Materials]
  [./pfmobility]
    type = GenericConstantMaterial
    prop_names  = 'M kappa_c'
    prop_values = '100 40'
  [../]

  [./free_energy]
    # equivalent to `MathFreeEnergy`
    type = DerivativeParsedMaterial
    property_name = F
    coupled_variables = 'c'
    expression = '0.25*(1+c)^2*(1-c)^2'
    derivative_order = 2
  [../]
[]

[Preconditioning]
  # active = ' '
  [./SMP]
    type = SMP
    full = true
  [../]
[]

[Executioner]
  type = Transient
  scheme = bdf2

  solve_type = 'NEWTON'
  petsc_options_iname = -pc_type
  petsc_options_value = lu

  l_max_its = 30
  l_tol = 1.0e-4
  nl_rel_tol = 1.0e-10
  start_time = 0.0
  num_steps = 2

  dt = 1
[]

[Postprocessors]
  [mass]
    type = ElementIntegralVariablePostprocessor
    variable = c
    execute_on = 'initial timestep_end'
  []
  [free_energy_integral]
    type = ElementIntegralMaterialProperty
    mat_prop = F
    execute_on = 'initial timestep_end'
  []
  [gradient_energy_integral]
    type = ElementIntegralVariablePostprocessor
    variable = gradient_energy_density
    execute_on = 'initial timestep_end'
  []
[]

[AuxVariables]
  [dc_dx]
    family = MONOMIAL
    order = FIRST
  []
  [dc_dy]
    family = MONOMIAL
    order = FIRST
  []
  [gradient_energy_density]
    family = MONOMIAL
    order = FIRST
  []
[]

[AuxKernels]
  [dc_dx]
    type = VariableGradientComponent
    variable = dc_dx
    gradient_variable = c
    component = x
    execute_on = 'initial timestep_end'
  []
  [dc_dy]
    type = VariableGradientComponent
    variable = dc_dy
    gradient_variable = c
    component = y
    execute_on = 'initial timestep_end'
  []
  [gradient_energy_density]
    type = ParsedAux
    variable = gradient_energy_density
    coupled_variables = 'dc_dx dc_dy'
    expression = '20*(dc_dx^2 + dc_dy^2)'
    execute_on = 'initial timestep_end'
  []
[]

[Outputs]
  exodus = true
  csv = true
[]
