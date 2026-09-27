# Axisymmetric Theis drawdown subcase, based on the version-matched PorousFlow seed.
[Mesh]
  type = GeneratedMesh
  dim = 1
  nx = 200
  xmax = 1000
  bias_x = 1.0
  coord_type = RZ
[]
[GlobalParams]
  PorousFlowDictator = dictator
[]
[Variables]
  [pp]
    initial_condition = 20E6
  []
[]
[PorousFlowBasicTHM]
  dictator_name = dictator
  add_darcy_aux = false
  fp = simple_fluid
  gravity = '0 0 0'
  multiply_by_density = false
  porepressure = pp
[]
[FluidProperties]
  [simple_fluid]
    type = SimpleFluidProperties
    viscosity = 0.001
  []
[]
[Materials]
  [porosity]
    type = PorousFlowPorosityConst
    porosity = 0.05
  []
  [biot_mod]
    type = PorousFlowConstantBiotModulus
    fluid_bulk_modulus = 2E9
    biot_coefficient = 1.0
  []
  [permeability]
    type = PorousFlowPermeabilityConst
    permeability = '1E-14 0 0 0 1E-14 0 0 0 1E-14'
  []
[]
[DiracKernels]
  [sink]
    type = PorousFlowSquarePulsePointSource
    point = '0 0 0'
    mass_flux = -1.6E-4
    variable = pp
  []
[]
[VectorPostprocessors]
  [pp]
    type = LineValueSampler
    num_points = 201
    start_point = '0 0 0'
    end_point = '1000 0 0'
    sort_by = x
    variable = pp
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
  solve_type = Newton
  dt = 200
  end_time = 1000
  nl_abs_tol = 1e-10
[]
[Outputs]
  perf_graph = true
  [csv]
    type = CSV
    execute_on = final
  []
[]
