[Mesh]
  type = GeneratedMesh
  dim = 1
  nx = 8
  xmin = 0
  xmax = 1
[]
[Variables]
  [x1]
  []
  [x2]
  []
  [x3]
  []
[]
[Kernels]
  [d1]
    type = Diffusion
    variable = x1
  []
  [d2]
    type = Diffusion
    variable = x2
  []
  [d3]
    type = Diffusion
    variable = x3
  []
[]
[BCs]
  [x1_left]
    type = DirichletBC
    variable = x1
    boundary = left
    value = 0
  []
  [x2_left]
    type = DirichletBC
    variable = x2
    boundary = left
    value = 0
  []
  [x3_left]
    type = DirichletBC
    variable = x3
    boundary = left
    value = 0
  []
  [x1_right]
    type = NeumannBC
    variable = x1
    boundary = right
    value = 0
  []
  [x2_right]
    type = NeumannBC
    variable = x2
    boundary = right
    value = 0
  []
  [x3_right]
    type = NeumannBC
    variable = x3
    boundary = right
    value = 0
  []
[]
[AuxVariables]
  [f]
  []
[]
[AuxKernels]
  [ishigami]
    type = ParsedAux
    variable = f
    coupled_variables = 'x1 x2 x3'
    expression = 'sin(6.283185307179586*x1-3.141592653589793)+7*sin(6.283185307179586*x2-3.141592653589793)^2+0.1*(6.283185307179586*x3-3.141592653589793)^4*sin(6.283185307179586*x1-3.141592653589793)'
    execute_on = TIMESTEP_END
  []
[]
[Postprocessors]
  [x1_value]
    type = PointValue
    point = '0 0 0'
    variable = x1
  []
  [x2_value]
    type = PointValue
    point = '0 0 0'
    variable = x2
  []
  [x3_value]
    type = PointValue
    point = '0 0 0'
    variable = x3
  []
  [average_f]
    type = ElementAverageValue
    variable = f
  []
[]
[Executioner]
  type = Transient
  num_steps = 1
  dt = 1
  solve_type = NEWTON
[]
[Controls]
  [stochastic]
    type = SamplerReceiver
  []
[]
# No per-sample output: at N=4096 the Sobol design is 8N = 32768 sub-solves and
# writing a CSV for each is pure I/O cost.
[Outputs]
[]
