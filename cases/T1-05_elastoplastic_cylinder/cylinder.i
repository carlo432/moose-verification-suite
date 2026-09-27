[Problem]
  coord_type = RZ
[]

[Mesh]
  type = GeneratedMesh
  dim = 2
  nx = 40
  ny = 1
  xmin = 1
  xmax = 2
  ymin = 0
  ymax = 1
[]

[GlobalParams]
  displacements = 'disp_x disp_y'
[]

[Functions]
  [pressure]
    type = ParsedFunction
    expression = '100*t'
  []
[]

[Variables]
  [disp_x]
  []
  [disp_y]
  []
[]

[Physics/SolidMechanics/QuasiStatic]
  [all]
    strain = SMALL
    incremental = true
    add_variables = true
    generate_output = 'stress_xx stress_yy stress_zz'
  []
[]

[BCs]
  [axial_bottom]
    type = DirichletBC
    variable = disp_y
    boundary = bottom
    value = 0
  []
  [axial_top]
    type = DirichletBC
    variable = disp_y
    boundary = top
    value = 0
  []
  [Pressure]
    [inner]
      boundary = left
      function = pressure
    []
  []
[]

[Materials]
  [elasticity]
    type = ComputeIsotropicElasticityTensor
    youngs_modulus = 210000
    poissons_ratio = 0.3
  []
  [plasticity]
    type = IsotropicPlasticityStressUpdate
    yield_stress = 100
    hardening_constant = 0
  []
  [radial_return]
    type = ComputeMultipleInelasticStress
    tangent_operator = elastic
    inelastic_models = plasticity
  []
[]

[AuxVariables]
  [srr]
    order = CONSTANT
    family = MONOMIAL
  []
  [shh]
    order = CONSTANT
    family = MONOMIAL
  []
  [szz]
    order = CONSTANT
    family = MONOMIAL
  []
  [eff_plastic_strain]
    order = CONSTANT
    family = MONOMIAL
  []
  [vonmises]
    order = CONSTANT
    family = MONOMIAL
  []
[]

[AuxKernels]
  [srr_aux]
    type = RankTwoAux
    rank_two_tensor = stress
    variable = srr
    index_i = 0
    index_j = 0
  []
  [shh_aux]
    type = RankTwoAux
    rank_two_tensor = stress
    variable = shh
    index_i = 2
    index_j = 2
  []
  # In RZ the stress tensor indices are 0=r, 1=z, 2=theta.  sigma_zz indicates
  # how far plastic flow has developed: it equals nu*(srr+shh) where the
  # material has only just yielded and (srr+shh)/2 where flow is developed.
  [szz_aux]
    type = RankTwoAux
    rank_two_tensor = stress
    variable = szz
    index_i = 1
    index_j = 1
  []
  [effective_plastic_strain_aux]
    type = MaterialRealAux
    property = effective_plastic_strain
    variable = eff_plastic_strain
    execute_on = timestep_end
  []
  [vonmises_aux]
    type = RankTwoScalarAux
    scalar_type = VonMisesStress
    rank_two_tensor = stress
    variable = vonmises
  []
[]

[Postprocessors]
  [max_srr]
    type = ElementExtremeValue
    variable = srr
  []
  [min_srr]
    type = ElementExtremeValue
    variable = srr
    value_type = min
  []
  [max_shh]
    type = ElementExtremeValue
    variable = shh
  []
  [min_shh]
    type = ElementExtremeValue
    variable = shh
    value_type = min
  []
  # Full-section yield: the plastic front has reached the outer wall.  This is
  # the primary p_lim observable, replacing the arbitrary eps_p >= 1 threshold.
  [outer_wall_plastic_strain]
    type = SideAverageValue
    variable = eff_plastic_strain
    boundary = right
  []
  [inner_wall_plastic_strain]
    type = SideAverageValue
    variable = eff_plastic_strain
    boundary = left
  []
  # Load-deflection curve: the inner wall opens without bound at the limit load.
  [inner_wall_displacement]
    type = SideAverageValue
    variable = disp_x
    boundary = left
  []
  [outer_wall_hoop]
    type = SideAverageValue
    variable = shh
    boundary = right
  []
  [max_eff_plastic_strain]
    type = ElementExtremeValue
    variable = eff_plastic_strain
  []
  [max_vonmises]
    type = ElementExtremeValue
    variable = vonmises
  []
[]

[VectorPostprocessors]
  [stress_profile]
    type = LineValueSampler
    variable = 'srr shh szz eff_plastic_strain'
    start_point = '1.0 0.5 0'
    end_point = '2.0 0.5 0'
    num_points = 201
    sort_by = x
    execute_on = TIMESTEP_END
  []
[]

[Preconditioning]
  [smp]
    type = SMP
    full = true
  []
[]

[Executioner]
  type = Transient
  solve_type = PJFNK
  line_search = none
  automatic_scaling = true
  dt = 0.02
  end_time = 1
  nl_abs_tol = 1e-10
  l_tol = 1e-9
[]

[Outputs]
  csv = true
[]
