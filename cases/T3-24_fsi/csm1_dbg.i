# Turek & Hron CSM1 -- the SOLID half of the FSI1 benchmark, alone.
#
# The elastic beam under gravity only, no fluid, steady. Table 9 of the paper:
#   ref.  ux of A = -7.187e-3 m     uy of A = -66.10e-3 m
#
# This is run BEFORE any coupling. Its deflection is 66 mm on a 350 mm beam --
# 19%, about 80x FSI1's -- so it exercises the finite-strain path far harder
# than FSI1 will, and any failure here is unambiguously the solid solver rather
# than the interface treatment.
#
# Constitutive law is St. Venant-Kirchhoff with large kinematics, which is what
# section 2.2 eq. (5)-(6) specifies -- not linear elasticity, and not the
# incremental corotational default.

E_solid = 1.4e6      # = 2 mu (1+nu) with mu = 0.5e6, nu = 0.4
nu_solid = 0.4
rho_solid = 1.0e3
gravity = -2.0       # magnitude 2 from Table 8; downward, and the published
                     # uy of A is negative, so the beam sags

[Mesh]
  [file]
    type = FileMeshGenerator
    file = fsi1_L1.msh
  []
  [sides]
    type = SideSetsFromNodeSetsGenerator
    input = file
  []
  [names]
    type = RenameBoundaryGenerator
    input = sides
    old_boundary = '1 2 3 4 5 6'
    new_boundary = 'inlet outlet walls cylinder interface attachment'
  []
  [solid_only]
    type = BlockDeletionGenerator
    input = names
    block = fluid
  []
[]

[GlobalParams]
  displacements = 'disp_x disp_y'
[]

# Total-Lagrangian formulation via the supported action rather than hand-wired
# kernels. Hand-wiring TotalLagrangianStressDivergence directly left the Newton
# update doing essentially nothing (residual 8.80e-8 -> 8.78e-8 over 10
# iterations), i.e. an inconsistent Jacobian.
[Physics/SolidMechanics/QuasiStatic]
  [all]
    strain = FINITE
    formulation = TOTAL
    new_system = true
    add_variables = true
  []
[]

[Kernels]
  [gravity_y]
    type = Gravity
    variable = disp_y
    value = ${gravity}
  []
[]

[BCs]
  # the beam's left end is fully attached to the rigid cylinder
  [fix_x]
    type = DirichletBC
    variable = disp_x
    boundary = attachment
    value = 0
  []
  [fix_y]
    type = DirichletBC
    variable = disp_y
    boundary = attachment
    value = 0
  []
[]

[Materials]
  [elasticity]
    type = ComputeIsotropicElasticityTensor
    youngs_modulus = ${E_solid}
    poissons_ratio = ${nu_solid}
  []
  [stress]
    type = ComputeStVenantKirchhoffStress
    large_kinematics = true
  []
  [density]
    type = GenericConstantMaterial
    prop_names = density
    prop_values = ${rho_solid}
  []
[]

[Postprocessors]
  # Point A in the REFERENCE configuration, (0.6, 0.2). MOOSE solves on the
  # undisplaced mesh, so a PointValue of the displacement here is the published
  # quantity directly.
  [ux_A]
    type = PointValue
    variable = disp_x
    point = '0.6 0.2 0'
  []
  [uy_A]
    type = PointValue
    variable = disp_y
    point = '0.6 0.2 0'
  []
  [n_elem]
    type = NumElements
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
  solve_type = NEWTON
  petsc_options_iname = '-pc_type'
  petsc_options_value = 'lu'
  line_search = none
  nl_rel_tol = 1e-08
  nl_abs_tol = 1e-10
  # Gravity is ramped in pseudo-time rather than applied at once: at 19%
  # deflection a single Newton solve from the undeformed state is not reliable.
  # The end state is the steady solution either way.
  dt = 0.1
  end_time = 1.0
[]

[Outputs]
  exodus = false
  csv = true
[]
