[Mesh]
  type = GeneratedMesh
  dim = 2
  nx = 64
  ny = 64
  xmin = 0
  xmax = 1000
  ymin = 0
  ymax = 1000
  elem_type = QUAD4
[]

[GlobalParams]
  op_num = 16
  var_name_base = gr
[]

[Variables]
  [PolycrystalVariables]
  []
[]

[UserObjects]
  [voronoi]
    type = PolycrystalVoronoi
    rand_seed = 105
    grain_num = 64
    coloring_algorithm = bt
  []
[]

[ICs]
  [PolycrystalICs]
    [PolycrystalColoringIC]
      polycrystal_ic_uo = voronoi
    []
  []
[]

[AuxVariables]
  [bnds]
    order = FIRST
    family = LAGRANGE
  []
[]

[Kernels]
  [PolycrystalKernel]
  []
[]

[AuxKernels]
  [BndsCalc]
    type = BndsCalcAux
    variable = bnds
    execute_on = timestep_end
  []
[]

[BCs]
  [Periodic]
    [All]
      auto_direction = 'x y'
    []
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
  [ngrains]
    type = FeatureFloodCount
    variable = bnds
    threshold = 0.7
    compute_var_to_feature_map = true
  []
[]

[VectorPostprocessors]
  [features]
    type = FeatureVolumeVectorPostprocessor
    flood_counter = ngrains
    output_centroids = true
    execute_on = timestep_end
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
  solve_type = PJFNK
  petsc_options_iname = '-pc_type -pc_hypre_type -ksp_gmres_restart'
  petsc_options_value = 'hypre boomeramg 31'
  l_tol = 1e-4
  l_max_its = 30
  nl_max_its = 20
  nl_rel_tol = 1e-9
  start_time = 0
  num_steps = 10
  dt = 40
[]

[Outputs]
  exodus = true
  csv = true
[]
