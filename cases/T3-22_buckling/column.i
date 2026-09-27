# T3-22 -- Euler buckling of a cantilever column by imperfection + Southwell.
#
# A geometrically imperfect column is compressed under finite strain.  The
# additional lateral deflection grows as a = a0 P/(Pcr-P), so a/P plotted
# against a is a straight line of slope 1/Pcr.  This recovers the Euler load
# from a genuine MOOSE nonlinear solve; no geometric-stiffness or eigenvalue
# object is required, which is why the absence of one is not a blocker.
#
# L = 100, h = 2 (unit depth), E = 1000, nu = 0  ->  I = h^3/12 = 0.6666667
# Cantilever (fixed-free):  Pcr = pi^2 E I / (4 L^2) = 0.16449341
# nu = 0 keeps the plane-strain effective modulus equal to E.

L = 100
H = 2
IMPERFECTION = 0.1   # tip amplitude a0 of the initial shape, overridden per run

[Mesh]
  [gen]
    type = GeneratedMeshGenerator
    dim = 2
    nx = 160
    ny = 4
    xmin = 0
    xmax = ${L}
    ymin = -${fparse H/2}
    ymax = ${fparse H/2}
    elem_type = QUAD9
  []
  # Initial imperfection in the shape of the first cantilever mode.  Applying
  # it to the mesh rather than as a lateral load keeps the loading purely
  # axial, so P is unambiguous.
  [imperfect]
    type = ParsedNodeTransformGenerator
    input = gen
    x_function = 'x'
    # pi/(2L) = 0.015707963267948967 ; 'pi' is not a parser identifier here.
    y_function = 'y + ${IMPERFECTION} * (1 - cos(0.015707963267948967*x))'
    z_function = '0'
  []
  second_order = true
[]

[GlobalParams]
  displacements = 'disp_x disp_y'
[]

[Physics/SolidMechanics/QuasiStatic]
  [all]
    strain = FINITE
    incremental = true
    add_variables = true
    generate_output = 'stress_xx'
  []
[]

[Functions]
  [axial_traction]
    type = ParsedFunction
    # Ramps to 0.85*Pcr. The Southwell window closes at 0.8, and pushing nearer
    # the limit point only makes Newton stall at the turning point.
    # Traction is negative (acting in -x); total P = |traction| * H.
    expression = '-0.85 * 0.16449340668482262 / ${H} * t'
  []
[]

[BCs]
  # tip_shear is used only by the EI calibration run, which disables `axial`
  # instead.  delta = F L^3/(3 EI) with F = value * H pins EI independently of
  # the buckling reference.
  inactive = 'tip_shear'
  [tip_shear]
    type = NeumannBC
    variable = disp_y
    boundary = right
    value = 1e-4
  []
  [clamp_x]
    type = DirichletBC
    variable = disp_x
    boundary = left
    value = 0
  []
  [clamp_y]
    type = DirichletBC
    variable = disp_y
    boundary = left
    value = 0
  []
  # A dead (non-follower) axial load.  The `Pressure` BC would be wrong here:
  # it defaults to use_displaced_mesh = true, so the load rotates with the tip
  # face.  That is Beck's column -- a non-conservative follower-load problem
  # with no static bifurcation at all -- and it produces lateral *stiffening*
  # under compression instead of Euler buckling.
  [axial]
    type = FunctionNeumannBC
    variable = disp_x
    boundary = right
    function = axial_traction
  []
[]

[Materials]
  [elasticity]
    type = ComputeIsotropicElasticityTensor
    youngs_modulus = 1000
    poissons_ratio = 0.0
  []
  [stress]
    type = ComputeFiniteStrainElasticStress
  []
[]

[Postprocessors]
  [applied_load]
    # Reaction at the clamp equals the applied axial load; measured, not assumed.
    type = SidesetReaction
    direction = '1 0 0'
    stress_tensor = stress
    boundary = left
  []
  [max_deflection]
    # The modal antinode is the tip for the cantilever and midspan for
    # fixed-fixed, so take the extreme rather than a fixed location.
    type = NodalExtremeValue
    variable = disp_y
    value_type = max
  []
  [tip_deflection]
    type = SideAverageValue
    variable = disp_y
    boundary = right
  []
  [tip_shortening]
    type = SideAverageValue
    variable = disp_x
    boundary = right
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
  solve_type = NEWTON
  petsc_options_iname = '-pc_type'
  petsc_options_value = 'lu'
  line_search = none
  dt = 0.02
  end_time = 1.0
  nl_rel_tol = 1e-10
  nl_abs_tol = 1e-11
[]

[Outputs]
  csv = true
[]
