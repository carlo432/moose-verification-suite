# T3-23 -- dose-dependent swelling eigenstrain and the mismatch stress it drives.
#
# Reclassified from [E] to [A]: no sourced swelling-vs-dose correlation is
# available, so the capability verified here is the eigenstrain-to-stress
# mapping itself, against a closed form, with the correlation treated as a
# declared constitutive input rather than an experimental claim.
#
# Configuration: plane-strain slab, in-plane displacement fully restrained
# (disp_x = 0 on both ends) and traction-free on top.  With eps_xx = eps_zz = 0
# and sigma_yy = 0, the elasticity relations collapse to a POINTWISE result
#
#     sigma_xx(y) = sigma_zz(y) = -E e(y) / (1 - nu),    sigma_yy(y) = 0
#
# where e(y) = S D(y)/3 is the eigenstrain per component for a volumetric
# swelling S per dpa at dose D.  E/(1-nu) is the biaxial modulus.  Any dose
# profile therefore has an exact stress field, so a gradient case is a real
# test rather than an invariant.

S_PER_DPA = 0.01      # volumetric swelling per dpa
E = 200000.0
NU = 0.3
DOSE = 'y'            # dose profile D(y); overridden per case

[Mesh]
  [gen]
    type = GeneratedMeshGenerator
    dim = 2
    nx = 16
    ny = 16
    xmax = 1
    ymax = 1
    elem_type = QUAD9
  []
  second_order = true
[]

[GlobalParams]
  displacements = 'disp_x disp_y'
[]

[Functions]
  [dose_function]
    type = ParsedFunction
    expression = '${DOSE}'
  []
  # Closed-form mismatch stress, used by an element L2 norm. A LineValueSampler
  # cannot measure this cleanly: its fixed sample points straddle the element
  # boundaries of a discontinuous MONOMIAL field, which pollutes the observed
  # convergence order with a sampling artefact.
  [exact_sxx]
    type = ParsedFunction
    expression = '-${E} * (${S_PER_DPA} * (${DOSE}) / 3.0) / (1.0 - ${NU})'
  []
[]

[AuxVariables]
  [dose]
    order = SECOND
  []
  [sxx]
    order = FIRST
    family = MONOMIAL
  []
  [syy]
    order = FIRST
    family = MONOMIAL
  []
  [szz]
    order = FIRST
    family = MONOMIAL
  []
[]

[AuxKernels]
  [dose_aux]
    type = FunctionAux
    variable = dose
    function = dose_function
    execute_on = 'initial timestep_begin'
  []
  [sxx]
    type = RankTwoAux
    rank_two_tensor = stress
    variable = sxx
    index_i = 0
    index_j = 0
  []
  [syy]
    type = RankTwoAux
    rank_two_tensor = stress
    variable = syy
    index_i = 1
    index_j = 1
  []
  [szz]
    type = RankTwoAux
    rank_two_tensor = stress
    variable = szz
    index_i = 2
    index_j = 2
  []
[]

[Physics/SolidMechanics/QuasiStatic]
  [all]
    strain = SMALL
    add_variables = true
    eigenstrain_names = swelling
    generate_output = 'stress_xx stress_yy'
  []
[]

[BCs]
  # eps_xx = 0: the slab cannot expand in plane. Combined with plane strain
  # (eps_zz = 0) and a traction-free top, this fixes sigma_xx pointwise.
  [left_x]
    type = DirichletBC
    variable = disp_x
    boundary = left
    value = 0
  []
  [right_x]
    type = DirichletBC
    variable = disp_x
    boundary = right
    value = 0
  []
  [bottom_y]
    type = DirichletBC
    variable = disp_y
    boundary = bottom
    value = 0
  []
[]

[Materials]
  [elasticity]
    type = ComputeIsotropicElasticityTensor
    youngs_modulus = ${E}
    poissons_ratio = ${NU}
  []
  # Eigenstrain per component is S*D/3 for a volumetric swelling of S*D.
  [swelling_prefactor]
    type = DerivativeParsedMaterial
    property_name = swelling_prefactor
    coupled_variables = 'dose'
    constant_names = 'S'
    constant_expressions = '${S_PER_DPA}'
    expression = 'S * dose / 3.0'
    derivative_order = 1
  []
  [swelling]
    type = ComputeVariableEigenstrain
    eigen_base = '1 1 1 0 0 0'
    prefactor = swelling_prefactor
    args = dose
    eigenstrain_name = swelling
  []
  [stress]
    type = ComputeLinearElasticStress
  []
[]

[VectorPostprocessors]
  [profile]
    type = LineValueSampler
    variable = 'sxx syy szz dose'
    start_point = '0.5 0 0'
    end_point = '0.5 1 0'
    num_points = 65
    sort_by = y
    execute_on = TIMESTEP_END
  []
[]

[Postprocessors]
  [l2_error_sxx]
    type = ElementL2Error
    variable = sxx
    function = exact_sxx
  []
  [max_abs_sxx]
    type = ElementExtremeValue
    variable = sxx
  []
  [max_abs_syy]
    type = ElementExtremeValue
    variable = syy
  []
[]

[Executioner]
  type = Steady
  solve_type = NEWTON
  petsc_options_iname = '-pc_type'
  petsc_options_value = 'lu'
  nl_rel_tol = 1e-12
  nl_abs_tol = 1e-12
[]

[Outputs]
  csv = true
[]
