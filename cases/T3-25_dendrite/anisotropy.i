# T3-25 (re-scoped) -- anisotropic solidification: growth-direction selection.
#
# The tip-velocity observable was abandoned because this Kobayashi parameter
# set never reaches a steady tip velocity in any affordable domain: the melt
# recalesces to T_e and growth stalls. See observable_correction in
# reference.json.
#
# What the model DOES predict exactly is the orientation of growth. The
# interfacial parameter is eps(theta) = eps_bar [1 + delta cos(m (theta - theta_0))],
# so the solidifying grain must acquire an m-fold shape locked to theta_0. That
# is a sharp, falsifiable, parameter-exact statement and it is what is measured.
#
# Observable: the angular Fourier content of the solid region,
#     C_m = integral w cos(m theta) dA ,  S_m = integral w sin(m theta) dA
# with theta measured about the seed centre. For a shape R(theta) =
# R0 [1 + a cos(m(theta - theta_0))] these give
#     sqrt(C_m^2 + S_m^2) / integral w dA  = a        (m-fold amplitude)
#     atan2(S_m, C_m) / m                  = theta_0  (arm direction)
# Volume integrals, not pointwise interface crossings, so the measurement does
# not inherit the node-straddling error that a LineValueSampler would.
#
# FULL domain with the seed at the centre. The earlier quarter-symmetry domain
# was WRONG for this model: mirror planes on x=0 and y=0 impose four-fold
# symmetry, and the default mode_number here is SIX.

xc = 0.35
yc = 0.35
T_e = 1.0
delta = 0.04       # anisotropy_strength
mode = 6           # mode_number
theta0 = 90        # reference_angle, degrees

[Mesh]
  type = GeneratedMesh
  dim = 2
  nx = 96
  ny = 96
  xmax = 0.7
  ymax = 0.7
[]

[Variables]
  [w][]
  [T][]
[]

[ICs]
  [wIC]
    type = SmoothCircleIC
    variable = w
    int_width = 0.1
    x1 = ${xc}
    y1 = ${yc}
    radius = 0.08
    outvalue = 0
    invalue = 1
  []
[]

[Kernels]
  [w_dot]
    type = TimeDerivative
    variable = w
  []
  [anisoACinterface1]
    type = ACInterfaceKobayashi1
    variable = w
    mob_name = M
  []
  [anisoACinterface2]
    type = ACInterfaceKobayashi2
    variable = w
    mob_name = M
  []
  [AllenCahn]
    type = AllenCahn
    variable = w
    mob_name = M
    f_name = fbulk
    coupled_variables = 'T'
  []
  [T_dot]
    type = TimeDerivative
    variable = T
  []
  [CoefDiffusion]
    type = Diffusion
    variable = T
  []
  [w_dot_T]
    type = CoefCoupledTimeDerivative
    variable = T
    v = w
    coef = -1.8
  []
[]

[Materials]
  [free_energy]
    type = DerivativeParsedMaterial
    property_name = fbulk
    coupled_variables = 'w T'
    constant_names = 'alpha gamma T_e pi'
    constant_expressions = '0.9 10 ${T_e} 4*atan(1)'
    expression = 'm:=alpha/pi * atan(gamma * (T_e - T)); 1/4*w^4 - (1/2 - m/3) * w^3 + (1/4 - m/2) * w^2'
    derivative_order = 2
  []
  [material]
    type = InterfaceOrientationMaterial
    op = w
    anisotropy_strength = ${delta}
    mode_number = ${mode}
    reference_angle = ${theta0}
  []
  [consts]
    type = GenericConstantMaterial
    prop_names  = 'M'
    prop_values = '3333.333'
  []
[]

[AuxVariables]
  [c4][]
  [s4][]
  [c6][]
  [s6][]
[]

[AuxKernels]
  # w cos(m theta) and w sin(m theta) about the seed centre, for m = 4 and m = 6.
  # Both modes are always computed so that cross-mode contamination is measured
  # rather than assumed: whichever mode_number is set, the other amplitude is a
  # null channel and must stay small.
  [c4]
    type = ParsedAux
    variable = c4
    coupled_variables = 'w'
    use_xyzt = true
    expression = 'w*cos(4*atan2(y-${yc}, x-${xc}))'
    execute_on = 'initial timestep_end'
  []
  [s4]
    type = ParsedAux
    variable = s4
    coupled_variables = 'w'
    use_xyzt = true
    expression = 'w*sin(4*atan2(y-${yc}, x-${xc}))'
    execute_on = 'initial timestep_end'
  []
  [c6]
    type = ParsedAux
    variable = c6
    coupled_variables = 'w'
    use_xyzt = true
    expression = 'w*cos(6*atan2(y-${yc}, x-${xc}))'
    execute_on = 'initial timestep_end'
  []
  [s6]
    type = ParsedAux
    variable = s6
    coupled_variables = 'w'
    use_xyzt = true
    expression = 'w*sin(6*atan2(y-${yc}, x-${xc}))'
    execute_on = 'initial timestep_end'
  []
[]

[Postprocessors]
  [area]
    type = ElementIntegralVariablePostprocessor
    variable = w
    execute_on = 'initial timestep_end'
  []
  [C4]
    type = ElementIntegralVariablePostprocessor
    variable = c4
    execute_on = 'initial timestep_end'
  []
  [S4]
    type = ElementIntegralVariablePostprocessor
    variable = s4
    execute_on = 'initial timestep_end'
  []
  [C6]
    type = ElementIntegralVariablePostprocessor
    variable = c6
    execute_on = 'initial timestep_end'
  []
  [S6]
    type = ElementIntegralVariablePostprocessor
    variable = s6
    execute_on = 'initial timestep_end'
  []
  [T_max]
    type = ElementExtremeValue
    variable = T
    execute_on = 'initial timestep_end'
  []
[]

[Preconditioning]
  [SMP]
    type = SMP
    full = true
  []
[]

[Executioner]
  type = Transient
  solve_type = PJFNK
  scheme = bdf2
  petsc_options_iname = '-pc_type'
  petsc_options_value = 'lu'
  nl_rel_tol = 1e-08
  l_tol = 1e-4
  l_max_its = 30
  dt = 0.001
  num_steps = 40
[]

[Outputs]
  exodus = false
  perf_graph = false
  [csv]
    type = CSV
    execute_on = TIMESTEP_END
  []
[]
