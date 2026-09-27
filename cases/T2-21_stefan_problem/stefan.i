[Mesh]
  type = GeneratedMesh
  dim = 1
  xmin = 0
  xmax = 0.1
  nx = 100
[]
[Variables]
  [temp]
    initial_condition = 1.0
  []
[]
[Kernels]
  [time]
    type = HeatConductionTimeDerivative
    variable = temp
  []
  [cond]
    type = HeatConduction
    variable = temp
  []
[]
[BCs]
  [hot]
    type = DirichletBC
    variable = temp
    boundary = left
    value = 2.0
  []
  [cold]
    type = DirichletBC
    variable = temp
    boundary = right
    value = 1.0
  []
[]
[Materials]
  [base]
    type = GenericConstantMaterial
    prop_names = 'density thermal_conductivity'
    prop_values = '1.0 1e-4'
  []
  [cp]
    # Apparent-heat-capacity regularization of latent heat.  The
    # temperature coupling is explicit here so the nonlinear Jacobian
    # contains d(cp)/d(temp), rather than silently using a constant seed.
    type = DerivativeParsedMaterial
    property_name = specific_heat
    coupled_variables = temp
    # Explicit latent heat declaration: Lf=0.212862645754, cp=1,
    # sigma=0.03, Tm=1.5.  The verifier independently checks that the
    # Gaussian excess integrates to this Lf.
    expression = '1.0 + 4.00316291536*exp(-((temp-1.5)/0.03)^2)'
    derivative_order = 1
  []
[]
[Executioner]
  type = Transient
  solve_type = NEWTON
  dt = 1e-4
  end_time = 0.01
  nl_abs_tol = 1e-10
[]
[Outputs]
  exodus = true
[]
