# Turek & Hron FSI1 -- the COUPLED benchmark.
#
# Built from two halves that were each validated on this same mesh first:
#   cfd1.i  fluid alone, rigid flag, drag 1.80 -> 1.02 -> 0.45 % vs Table 5
#   csm1.i  solid alone, gravity only, uy 16.88 -> 3.13 -> 1.11 % vs Table 9
# Neither half is a scored row (no tolerance was pre-declared for them); they
# are gates, so that a failure HERE can be localised to the coupling instead of
# guessed at. See staged_validation_results in reference.json.
#
# The coupling machinery is ported from fsi_flat_channel.i: monolithic ALE with
# ConvectedMesh/ConvectedMeshPSPG on the fluid momentum, pseudo-solid (Laplace)
# mesh motion in the fluid block, and CoupledPenaltyInterfaceDiffusion tying the
# fluid velocity to the solid velocity across the interface.
#
# Anchor: Table 13,  ux(A) = 0.0227e-3 m,  uy(A) = 0.8209e-3 m,
#                    drag = 14.295 N,      lift = 0.7638 N.

# --- fluid, Table 12 -------------------------------------------------------
rho_f = 1000.0
mu_f  = 1.0          # nu = mu/rho = 1e-3 m^2/s
Ubar  = 0.2          # Re = Ubar*d/nu = 0.2*0.1/1e-3 = 20

# --- solid, Table 12 -------------------------------------------------------
rho_s = 1000.0
E_solid  = 1.4e6
nu_solid = 0.4

# --- coupling --------------------------------------------------------------
# The one genuinely un-derivable number in this input. The flat-channel seed
# used 1e6 against E = 1e2; here E is 1.4e6, so the seed's value carries no
# information and this is swept (see run_fsi1.sh / penalty_sweep in
# reference.json). Too soft and the interface leaks -- the no-slip residual
# below reports that directly; too stiff and the monolithic Jacobian is
# ill-conditioned.
penalty = 1e8

[Mesh]
  [file]
    type = FileMeshGenerator
    file = fsi1_L0.msh
  []
  [sides]
    type = SideSetsFromNodeSetsGenerator
    input = file
  []
  [names]
    type = RenameBoundaryGenerator
    input = sides
    old_boundary = '1 2 3 4 5 6'
    new_boundary = 'inlet outlet walls cylinder interface_2sided attachment'
  []
  # The Gmsh 1-D physical group for the flag surface arrives DOUBLE SIDED --
  # mesh_check.i measured it at exactly 2x the true arc length, which would
  # silently double every traction integral. Rebuild it single sided, from the
  # fluid side, which is also the orientation the InterfaceKernel needs.
  [interface]
    type = SideSetsBetweenSubdomainsGenerator
    input = names
    primary_block = fluid
    paired_block = solid
    new_boundary = interface
  []
[]

[GlobalParams]
  gravity = '0 0 0'
  integrate_p_by_parts = true
  laplace = true
  convective_term = true
  transient_term = true
  pspg = true
  supg = true
  displacements = 'disp_x disp_y'
  preset = false
  order = FIRST
  # use_displaced_mesh is deliberately NOT global. Only the fluid lives on the
  # moving mesh; the pseudo-solid map and the total-Lagrangian solid are both
  # posed on the reference configuration, and the SolidMechanics action does not
  # even accept the parameter, so a global true would silently be the wrong
  # default for everything except the eight INS kernels below.
[]

[AuxVariables]
  # Fluid momentum residual, saved. On the CYLINDER this is a no-slip Dirichlet
  # node, so it is exactly the nodal reaction -- the same construction cfd1.i
  # validated to 0.45 % on drag.
  #
  # It is NOT usable on the interface here, and that is the one real difference
  # from CFD1: at an interface node the fluid momentum equation is no longer
  # closed by a Dirichlet condition, it is closed by the penalty InterfaceKernel,
  # whose contribution this AuxVariable does not see. Summing force_x over the
  # interface would therefore report a traction that is missing the term that
  # actually enforces the coupling.
  [force_x]
    block = fluid
  []
  [force_y]
    block = fluid
  []
  # Solid stress-divergence residual, saved. On the ATTACHMENT this is the
  # clamped weld, so it is the reaction the cylinder exerts on the flag. With no
  # body force on the solid in FSI1, equilibrium makes that the negative of the
  # total fluid load on the flag -- which recovers the S2 part of the surface
  # integral without ever touching the interface traction directly.
  [sforce_x]
    block = solid
  []
  [sforce_y]
    block = solid
  []
[]

[Variables]
  [vel_x]
    block = fluid
  []
  [vel_y]
    block = fluid
  []
  [p]
    block = fluid
  []
  [disp_x]
  []
  [disp_y]
  []
  [vel_x_solid]
    block = solid
  []
  [vel_y_solid]
    block = solid
  []
[]

[Kernels]
  # ---- fluid momentum and mass, on the moving (displaced) mesh -------------
  [vel_x_time]
    type = INSMomentumTimeDerivative
    variable = vel_x
    block = fluid
    use_displaced_mesh = true
  []
  [vel_y_time]
    type = INSMomentumTimeDerivative
    variable = vel_y
    block = fluid
    use_displaced_mesh = true
  []
  [mass]
    type = INSMass
    variable = p
    u = vel_x
    v = vel_y
    pressure = p
    block = fluid
    disp_x = disp_x
    disp_y = disp_y
    use_displaced_mesh = true
  []
  [x_momentum]
    type = INSMomentumLaplaceForm
    variable = vel_x
    u = vel_x
    v = vel_y
    pressure = p
    component = 0
    block = fluid
    disp_x = disp_x
    disp_y = disp_y
    use_displaced_mesh = true
    save_in = force_x
  []
  [y_momentum]
    type = INSMomentumLaplaceForm
    variable = vel_y
    u = vel_x
    v = vel_y
    pressure = p
    component = 1
    block = fluid
    disp_x = disp_x
    disp_y = disp_y
    use_displaced_mesh = true
    save_in = force_y
  []

  # ---- ALE: subtract the mesh velocity from the convective term ------------
  [vel_x_mesh]
    type = ConvectedMesh
    disp_x = disp_x
    disp_y = disp_y
    variable = vel_x
    u = vel_x
    v = vel_y
    pressure = p
    block = fluid
    use_displaced_mesh = true
  []
  [vel_y_mesh]
    type = ConvectedMesh
    disp_x = disp_x
    disp_y = disp_y
    variable = vel_y
    u = vel_x
    v = vel_y
    pressure = p
    block = fluid
    use_displaced_mesh = true
  []
  [p_mesh]
    type = ConvectedMeshPSPG
    disp_x = disp_x
    disp_y = disp_y
    variable = p
    u = vel_x
    v = vel_y
    pressure = p
    block = fluid
    use_displaced_mesh = true
  []

  # ---- pseudo-solid mesh motion in the fluid block -------------------------
  # Solved on the UNDISPLACED mesh: this is the map, not physics on it.
  [disp_x_fluid]
    type = Diffusion
    variable = disp_x
    block = fluid
    use_displaced_mesh = false
  []
  [disp_y_fluid]
    type = Diffusion
    variable = disp_y
    block = fluid
    use_displaced_mesh = false
  []

  # ---- solid: rho_s * dv/dt balances the stress divergence added by the
  #      QuasiStatic action below, and v is defined as d(disp)/dt ------------
  # The seed used a plain CoupledTimeDerivative here, i.e. an implicit density
  # of 1. FSI1 has rho_s = 1000, so the coefficient is carried explicitly.
  # FSI1 is steady, so this term vanishes at the answer -- it only shapes the
  # path there -- but a wrong inertia would still change which steady state a
  # marginally stable continuation lands on.
  [accel_x]
    type = CoefCoupledTimeDerivative
    variable = disp_x
    v = vel_x_solid
    coef = ${rho_s}
    block = solid
    use_displaced_mesh = false
  []
  [accel_y]
    type = CoefCoupledTimeDerivative
    variable = disp_y
    v = vel_y_solid
    coef = ${rho_s}
    block = solid
    use_displaced_mesh = false
  []
  [vxs_dt]
    type = CoupledTimeDerivative
    variable = vel_x_solid
    v = disp_x
    block = solid
    use_displaced_mesh = false
  []
  [vys_dt]
    type = CoupledTimeDerivative
    variable = vel_y_solid
    v = disp_y
    block = solid
    use_displaced_mesh = false
  []
  [source_vxs]
    type = MatReaction
    variable = vel_x_solid
    block = solid
    reaction_rate = 1
    use_displaced_mesh = false
  []
  [source_vys]
    type = MatReaction
    variable = vel_y_solid
    block = solid
    reaction_rate = 1
    use_displaced_mesh = false
  []
[]

# St. Venant-Kirchhoff, as the benchmark specifies (eq. 5-6), on the same
# total-Lagrangian path csm1.i validated to 1.11 % on uy. At FSI1's 0.23 %
# strain linear elasticity would be numerically close, but the validated path
# is the one to reuse.
[Physics/SolidMechanics/QuasiStatic]
  [solid_domain]
    strain = FINITE
    formulation = TOTAL
    new_system = true
    block = solid
    save_in = 'sforce_x sforce_y'
  []
[]

[InterfaceKernels]
  [penalty_x]
    type = CoupledPenaltyInterfaceDiffusion
    variable = vel_x
    neighbor_var = disp_x
    secondary_coupled_var = vel_x_solid
    boundary = interface
    penalty = ${penalty}
  []
  [penalty_y]
    type = CoupledPenaltyInterfaceDiffusion
    variable = vel_y
    neighbor_var = disp_y
    secondary_coupled_var = vel_y_solid
    boundary = interface
    penalty = ${penalty}
  []
[]

[Materials]
  [elasticity]
    type = ComputeIsotropicElasticityTensor
    youngs_modulus = ${E_solid}
    poissons_ratio = ${nu_solid}
    block = solid
    use_displaced_mesh = false
  []
  [stress]
    type = ComputeStVenantKirchhoffStress
    large_kinematics = true
    block = solid
  []
  [solid_density]
    type = GenericConstantMaterial
    prop_names = density
    prop_values = ${rho_s}
    block = solid
    use_displaced_mesh = false
  []
  [fluid_props]
    type = GenericConstantMaterial
    block = fluid
    prop_names = 'rho mu'
    prop_values = '${rho_f} ${mu_f}'
    use_displaced_mesh = false
  []
[]

[Functions]
  # Parabolic profile with mean Ubar, smoothly ramped over t in [0,2] exactly
  # as section 3.3 of the paper prescribes. FSI1 is steady, so the ramp only
  # has to get there without shocking the mesh motion.
  [inlet_ramp]
    type = ParsedFunction
    expression = '1.5*${Ubar}*4.0/0.1681*y*(0.41-y) * if(t<2.0, 0.5*(1-cos(pi*t/2.0)), 1.0)'
  []
[]

[BCs]
  [inlet_x]
    type = FunctionDirichletBC
    variable = vel_x
    boundary = inlet
    function = inlet_ramp
  []
  [inlet_y]
    type = DirichletBC
    variable = vel_y
    boundary = inlet
    value = 0.0
  []
  [noslip_x]
    type = DirichletBC
    variable = vel_x
    boundary = 'walls cylinder'
    value = 0.0
  []
  [noslip_y]
    type = DirichletBC
    variable = vel_y
    boundary = 'walls cylinder'
    value = 0.0
  []
  # outlet: do-nothing / stress free, which with integrate_p_by_parts fixes the
  # pressure level. No explicit pressure BC.

  # Mesh map is pinned on every rigid fluid boundary; it is free to move only
  # where the solid drags it.
  [mesh_fix_x]
    type = DirichletBC
    variable = disp_x
    boundary = 'inlet outlet walls cylinder'
    value = 0
    use_displaced_mesh = false
  []
  [mesh_fix_y]
    type = DirichletBC
    variable = disp_y
    boundary = 'inlet outlet walls cylinder'
    value = 0
    use_displaced_mesh = false
  []
  # The flag is welded to the rigid cylinder.
  [clamp_x]
    type = DirichletBC
    variable = disp_x
    boundary = attachment
    value = 0
    use_displaced_mesh = false
  []
  [clamp_y]
    type = DirichletBC
    variable = disp_y
    boundary = attachment
    value = 0
    use_displaced_mesh = false
  []
  [clamp_vx]
    type = DirichletBC
    variable = vel_x_solid
    boundary = attachment
    value = 0
    use_displaced_mesh = false
  []
  [clamp_vy]
    type = DirichletBC
    variable = vel_y_solid
    boundary = attachment
    value = 0
    use_displaced_mesh = false
  []
[]

[Postprocessors]
  # Point A in the REFERENCE configuration, (0.6, 0.2) -- the flag tip.
  # Section 2.4 puts B at (0.15,0.2) while Table 1 says (0.2,0.2), which is the
  # cylinder CENTRE; Table 1 is the typo, and it is the likely origin of the
  # secondary sources that mislabel A. A is unambiguous and is what Table 13
  # tabulates.
  [ux_A]
    type = PointValue
    variable = disp_x
    point = '0.6 0.2 0'
    use_displaced_mesh = false
  []
  [uy_A]
    type = PointValue
    variable = disp_y
    point = '0.6 0.2 0'
    use_displaced_mesh = false
  []

  # Steadiness. FSI1 has a steady answer, so the run is finished when the tip
  # stops moving -- not when the clock runs out. Reported so the verifier can
  # refuse to score an unconverged transient rather than quoting whatever the
  # last step happened to hold.
  [uy_A_rate]
    type = ChangeOverTimePostprocessor
    postprocessor = uy_A
    change_with_respect_to_initial = false
  []

  # Interface leak check: how far the penalty is from actually enforcing
  # no-slip. This is what tells a too-soft penalty from a converged one, and it
  # is measured rather than assumed.
  [interface_slip]
    type = SideAverageValue
    variable = vel_x
    boundary = interface
  []

  # --- force on the obstacle, S = S1 (cylinder) + S2 (flag) ----------------
  # Reported raw; the verifier applies the documented sign convention in code,
  # as verify_stages.py does, rather than by hand here.
  [cyl_fx]
    type = NodalSum
    variable = force_x
    boundary = cylinder
  []
  [cyl_fy]
    type = NodalSum
    variable = force_y
    boundary = cylinder
  []
  [weld_fx]
    type = NodalSum
    variable = sforce_x
    boundary = attachment
  []
  [weld_fy]
    type = NodalSum
    variable = sforce_y
    boundary = attachment
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
  solve_type = PJFNK
  petsc_options_iname = '-pc_type -pc_factor_shift_type'
  petsc_options_value = 'lu       NONZERO'
  line_search = none
  nl_rel_tol = 1e-07
  nl_abs_tol = 1e-8
  nl_max_its = 30
  l_max_its = 200
  dt = 0.05
  end_time = 12.0
[]

[Outputs]
  exodus = false
  perf_graph = false
  [csv]
    type = CSV
  []
  # Checkpointing every 20 steps. The finest level takes hours, and without this
  # an interrupted run -- a reboot, a laptop sleeping, a timed-out shell -- loses
  # everything, because there is nothing for --recover to resume FROM. That
  # happened once on this suite and cost a level.
  #
  # Resume with the checkpoint FILE BASE, not the directory:
  #     --recover out/fsi1_L2_cp/LATEST
  # Pointing --recover at out/fsi1_L2_cp makes MOOSE look for
  # out/fsi1_L2_cp-mesh.cpa.gz and fail. Use resume_fsi1.sh, which gets this
  # right and refuses to start a second writer on the same file base.
  [cp]
    type = Checkpoint
    num_files = 2
    time_step_interval = 20
  []
[]
