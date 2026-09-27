# T3-25 -- Kobayashi anisotropic dendrite, far-field thermal boundary.
#
# Identical physics to dendrite.i.  Two things change, and only these two:
#
#   1. Quarter symmetry.  The seed sits at the origin instead of the box
#      centre and only one quadrant is solved.  The zero-flux natural BC on
#      x = 0 and y = 0 is exactly the symmetry condition of the four-fold
#      anisotropy, so this is free -- it buys 4x the domain per unit cost.
#   2. A far-field Dirichlet T = 0 on the outer boundaries, holding the melt
#      at its initial undercooling.  The insulated box of dendrite.i had
#      nowhere to put the rejected latent heat, so the melt ahead of the tip
#      warmed and the driving force decayed as the tip advanced.
#
# The declared measurement window in tip position, [0.45, 0.58], is UNCHANGED.
# With the seed at the origin the tip position is just its x coordinate, so
# the same window is being measured -- what changes is that the wall is now
# 0.62 beyond the end of it instead of 0.12.

L = 1.05
T_e = 1.0

[Mesh]
  type = GeneratedMesh
  dim = 2
  nx = 96
  ny = 96
  xmin = 0
  ymin = 0
  xmax = ${L}
  ymax = ${L}
[]

[Variables]
  [./w]
  [../]
  [./T]
  [../]
[]

[ICs]
  [./wIC]
    type = SmoothCircleIC
    variable = w
    int_width = 0.1
    x1 = 0
    y1 = 0
    radius = 0.08
    outvalue = 0
    invalue = 1
  [../]
[]

[BCs]
  # Hold the far field at the initial undercooling.  w is left natural: the
  # solid never approaches these boundaries within the measurement window.
  [./T_far]
    type = DirichletBC
    variable = T
    boundary = 'right top'
    value = 0
  [../]
[]

[Kernels]
  [./w_dot]
    type = TimeDerivative
    variable = w
  [../]
  [./anisoACinterface1]
    type = ACInterfaceKobayashi1
    variable = w
    mob_name = M
  [../]
  [./anisoACinterface2]
    type = ACInterfaceKobayashi2
    variable = w
    mob_name = M
  [../]
  [./AllenCahn]
    type = AllenCahn
    variable = w
    mob_name = M
    f_name = fbulk
    coupled_variables = 'T'
  [../]
  [./T_dot]
    type = TimeDerivative
    variable = T
  [../]
  [./CoefDiffusion]
    type = Diffusion
    variable = T
  [../]
  [./w_dot_T]
    type = CoefCoupledTimeDerivative
    variable = T
    v = w
    coef = -1.8 #This is -K from kobayashi's paper
  [../]
[]

[Materials]
  [./free_energy]
    type = DerivativeParsedMaterial
    property_name = fbulk
    coupled_variables = 'w T'
    constant_names = 'alpha gamma T_e pi'
    constant_expressions = '0.9 10 ${T_e} 4*atan(1)'
    expression = 'm:=alpha/pi * atan(gamma * (T_e - T)); 1/4*w^4 - (1/2 - m/3) * w^3 + (1/4 - m/2) * w^2'
    derivative_order = 2
  [../]
  [./material]
    type = InterfaceOrientationMaterial
    op = w
  [../]
  [./consts]
    type = GenericConstantMaterial
    prop_names  = 'M'
    prop_values = '3333.333'
  [../]
[]

[Preconditioning]
  [./SMP]
    type = SMP
    full = true
  [../]
[]

[Executioner]
  type = Transient
  solve_type = PJFNK
  scheme = bdf2
  # lu, exactly as dendrite.i used it, so the domain is the only thing that
  # changed between the superseded runs and these. asm/ilu was tried for cost
  # and abandoned: at nx=192 the linear solve hit l_max_its and the step never
  # converged (23 DIVERGED_ITS on time step 1).
  petsc_options_iname = '-pc_type'
  petsc_options_value = 'lu'

  nl_rel_tol = 1e-08
  l_tol = 1e-4
  l_max_its = 30

  dt = 0.001
  num_steps = 300
[]

[VectorPostprocessors]
  # Solid fraction along the +x axis from the seed centre at the origin; the
  # tip is the w = 0.5 crossing.
  [axis]
    type = LineValueSampler
    variable = w
    start_point = '0 0 0'
    end_point = '${L} 0 0'
    num_points = 526
    sort_by = x
    execute_on = TIMESTEP_END
  []

  # Temperature along the same axis. The T_far_field point probe sits at 0.95L,
  # five percent from a Dirichlet T = 0 boundary, so it is pinned small no
  # matter what the melt does -- too lenient to be evidence. This samples the
  # whole axis so the melt temperature can be read AHEAD OF THE TIP, which is
  # the quantity the domain fix actually claims to control.
  [axis_T]
    type = LineValueSampler
    variable = T
    start_point = '0 0 0'
    end_point = '${L} 0 0'
    num_points = 526
    sort_by = x
    execute_on = TIMESTEP_END
  []
[]

[Postprocessors]
  [solid_area]
    type = ElementIntegralVariablePostprocessor
    variable = w
    execute_on = 'initial timestep_end'
  []
  [T_max]
    type = ElementExtremeValue
    variable = T
    execute_on = 'initial timestep_end'
  []
  # The far-field guard: temperature just inside the outer boundary. If this
  # departs from zero the domain is again too small and the measurement is
  # contaminated, exactly as it was in dendrite.i.
  [T_far_field]
    type = PointValue
    variable = T
    point = '${fparse 0.95*L} 0 0'
    execute_on = 'initial timestep_end'
  []
[]

[Outputs]
  exodus = false
  perf_graph = false
  [csv]
    type = CSV
    execute_on = TIMESTEP_END
  []
[]
