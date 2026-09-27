[StochasticTools]
  auto_create_executioner = false
[]
[Distributions]
  [x1]
    type = Uniform
    lower_bound = 0
    upper_bound = 1
  []
  [x2]
    type = Uniform
    lower_bound = 0
    upper_bound = 1
  []
  [x3]
    type = Uniform
    lower_bound = 0
    upper_bound = 1
  []
[]
[Samplers]
  [sample]
    type = MonteCarlo
    distributions = 'x1 x2 x3'
    num_rows = 8
    seed = 3101
  []
  [resample]
    type = MonteCarlo
    distributions = 'x1 x2 x3'
    num_rows = 8
    seed = 3102
  []
  [sobol]
    type = Sobol
    sampler_a = sample
    sampler_b = resample
  []
[]
[MultiApps]
  [sub]
    type = SamplerTransientMultiApp
    input_files = ishigami_native_sub.i
    sampler = sobol
    # Without batch mode every one of the 8N rows is instantiated at once: N=4096
    # reached 7.5 GB and was killed. batch-restore reuses a small pool instead (batch-reset is not implemented for this MultiApp).
    mode = batch-restore
  []
[]
[Transfers]
  [parameters]
    type = SamplerParameterTransfer
    to_multi_app = sub
    sampler = sobol
    parameters = 'BCs/x1_left/value BCs/x2_left/value BCs/x3_left/value'
  []
  [results]
    type = SamplerPostprocessorTransfer
    from_multi_app = sub
    sampler = sobol
    to_vector_postprocessor = storage
    from_postprocessor = average_f
  []
[]
[VectorPostprocessors]
  [storage]
    type = StochasticResults
    parallel_type = DISTRIBUTED
    outputs = csv
  []
[]
# Native in-MOOSE Sobol index computation. The earlier implementation stopped at
# the StochasticResults vector and reconstructed indices in Python, recording
# that SobolStatistics was "unavailable in this MOOSE snapshot". It is available:
# SobolReporter, SobolStatistics and StatisticsReporter are all registered here.
[Reporters]
  [sobol]
    type = SobolReporter
    sampler = sobol
    vectorpostprocessors = storage
    ci_levels = '0.05 0.5 0.95'
    ci_replicates = 1000
    execute_on = FINAL
  []
[]

[Executioner]
  type = Transient
  num_steps = 1
  dt = 1
[]
[Outputs]
  execute_on = FINAL
  csv = true
  [json]
    type = JSON
    execute_on = FINAL
  []
[]
