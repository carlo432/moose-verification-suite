# T1-10 -- curvature-driven grain-boundary migration: an isolated circular grain.
#
# A circular grain of radius R embedded in a matrix shrinks under its own
# curvature at dR/dt = -M_gb sigma_gb / R, so
#
#     R(t)^2 = R0^2 - 2 M_gb sigma_gb t
#
# is exactly linear in t with a slope independent of R0.  That is the
# "R^2 proportional to t" grain-growth law the checklist names, and unlike a
# polycrystal exponent fit it is a sharp analytic statement rather than a
# statistical one.
#
# The absolute slope 2 M sigma is NOT claimed: GBEvolution converts GBmob0 and
# GBenergy through its own length_scale/time_scale/eV bookkeeping, and
# reproducing that conversion here would be reverse-engineering the code under
# test.  What is verified instead is everything the law asserts that can be
# checked independently of that constant: linearity of R^2 in t, independence
# of the slope from R0 and from the mesh, and exact proportionality of the
# slope to the imposed GB mobility.

[Mesh]
  type = GeneratedMesh
  dim = 2
  nx = 100
  ny = 100
  xmin = 0
  xmax = 500
  ymin = 0
  ymax = 500
  elem_type = QUAD4
[]

[GlobalParams]
  op_num = 2
  var_name_base = gr
  radius = 150.0
  int_width = 60.0
  x1 = 250.0
  y1 = 250.0
[]

[Variables]
  [PolycrystalVariables]
  []
[]

[ICs]
  [gr0]
    type = SmoothCircleIC
    variable = gr0
    invalue = 1.0
    outvalue = 0.0
  []
  [gr1]
    type = SmoothCircleIC
    variable = gr1
    invalue = 0.0
    outvalue = 1.0
  []
[]

[Kernels]
  [PolycrystalKernel]
  []
[]

[AuxVariables]
  [bnds]
  []
[]

[AuxKernels]
  [BndsCalc]
    type = BndsCalcAux
    variable = bnds
    execute_on = timestep_end
  []
[]

[Materials]
  [Copper]
    type = GBEvolution
    T = 500
    wGB = 60
    GBmob0 = 2.5e-6
    Q = 0.23
    GBenergy = 0.708
  []
[]

[Postprocessors]
  # Area of the shrinking grain.  The diffuse profile is antisymmetric about
  # the interface, so the integral of gr0 recovers the sharp-interface area.
  [grain_area]
    type = ElementIntegralVariablePostprocessor
    variable = gr0
    execute_on = 'initial timestep_end'
  []
  [matrix_area]
    type = ElementIntegralVariablePostprocessor
    variable = gr1
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
  scheme = bdf2
  solve_type = NEWTON
  petsc_options_iname = '-pc_type -pc_hypre_type'
  petsc_options_value = 'hypre boomeramg'
  l_tol = 1e-4
  nl_rel_tol = 1e-9
  dt = 20.0
  num_steps = 60
[]

[Outputs]
  csv = true
[]
