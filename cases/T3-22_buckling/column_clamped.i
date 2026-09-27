# T3-22 -- Euler buckling of a FIXED-FIXED (sliding clamp) column.
#
# A geometrically imperfect column is compressed under finite strain.  The
# additional lateral deflection grows as a = a0 P/(Pcr-P), so a/P plotted
# against a is a straight line of slope 1/Pcr.  This recovers the Euler load
# from a genuine MOOSE nonlinear solve; no geometric-stiffness or eigenvalue
# object is required, which is why the absence of one is not a blocker.
#
# L = 100, h = 2 (unit depth), E = 1000, nu = 0  ->  I = h^3/12 = 0.6666667
# Fixed-fixed (sliding): Pcr = 4 pi^2 E I / L^2 = 2.63189451
# The load is applied by a UNIFORM prescribed disp_x on the loaded face. That
# forces the face to remain plane and vertical, which is the rotation restraint
# a disp_y = 0 roller does not provide. P is read from the clamp reaction.
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
  # First fixed-fixed mode, v = (a0/2)(1 - cos(2 pi x / L)), antinode at midspan.
  [imperfect]
    type = ParsedNodeTransformGenerator
    input = gen
    x_function = 'x'
    # 2 pi/L = 0.06283185307179587 ; 'pi' is not a parser identifier here.
    y_function = 'y + 0.5 * ${IMPERFECTION} * (1 - cos(0.06283185307179587*x))'
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
  [axial_shortening]
    type = ParsedFunction
    # Uniform axial shortening. At Pcr the bar strain is Pcr/(E*H) = 1.316e-3,
    # so 0.1316 of shortening reaches the critical load; ramp a little past it.
    expression = '-0.125 * t'
  []
[]

[BCs]
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
    type = FunctionDirichletBC
    variable = disp_x
    boundary = right
    function = axial_shortening
  []
  # Roller: removes lateral translation of the loaded face only.
  [slide_y]
    type = DirichletBC
    variable = disp_y
    boundary = right
    value = 0
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
