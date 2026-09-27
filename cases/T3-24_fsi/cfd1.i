# Turek & Hron CFD1 -- the FLUID half of the FSI1 benchmark, alone.
#
# Steady flow at Re = 20 past the cylinder with the flag RIGID, on the mesh
# FSI1 will use. Table 5 of the paper:  ref. drag = 14.29,  lift = 1.119
#
# Deliberately built on the SAME discretization as fsi_flat_channel.i -- scalar
# vel_x/vel_y/p, all first order, equal-order with PSPG/SUPG inside the INS
# kernels. If CFD1 were solved with a different scheme (say the INSAD vector
# family) it would validate a fluid solver the coupled run does not use.

rho = 1000.0      # kg/m^3
mu  = 1.0         # dynamic; nu = mu/rho = 1e-3 m^2/s, Table 12
Ubar = 0.2        # mean inlet velocity; Re = Ubar*d/nu = 0.2*0.1/1e-3 = 20

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
    new_boundary = 'inlet outlet walls cylinder interface attachment'
  []
  [fluid_only]
    type = BlockDeletionGenerator
    input = names
    block = solid
  []
[]

[Variables]
  [vel_x]
    order = FIRST
  []
  [vel_y]
    order = FIRST
  []
  [p]
    order = FIRST
  []
[]

[AuxVariables]
  # Drag and lift come from the SAVED MOMENTUM RESIDUAL on the wetted surface.
  # At a no-slip node that residual is exactly the nodal reaction the fluid
  # exerts on the body -- no differentiated stress field, no hand-rolled
  # normals. Same reasoning as SidesetReaction in the solid cases.
  [force_x][]
  [force_y][]
[]

[Kernels]
  [mass]
    type = INSMass
    variable = p
    u = vel_x
    v = vel_y
    pressure = p
    pspg = true          # equal-order P1/P1 is inf-sup unstable without it
  []
  [x_mom]
    type = INSMomentumLaplaceForm
    variable = vel_x
    u = vel_x
    v = vel_y
    pressure = p
    component = 0
    supg = true          # Re = 20 advection
    save_in = force_x
  []
  [y_mom]
    type = INSMomentumLaplaceForm
    variable = vel_y
    u = vel_x
    v = vel_y
    pressure = p
    component = 1
    supg = true
    save_in = force_y
  []
[]

[Functions]
  # Section 2.5 eq. (10): parabolic, mean Ubar, peak 1.5*Ubar.
  [inlet_profile]
    type = ParsedFunction
    expression = '1.5*${Ubar}*4.0/0.1681*y*(0.41-y)'
  []
[]

[BCs]
  [inlet_x]
    type = FunctionDirichletBC
    variable = vel_x
    boundary = inlet
    function = inlet_profile
  []
  [inlet_y]
    type = DirichletBC
    variable = vel_y
    boundary = inlet
    value = 0
  []
  [noslip_x]
    type = DirichletBC
    variable = vel_x
    boundary = 'walls cylinder interface attachment'
    value = 0
  []
  [noslip_y]
    type = DirichletBC
    variable = vel_y
    boundary = 'walls cylinder interface attachment'
    value = 0
  []
  # do-nothing outflow; pressure datum pinned at the outlet
  [outlet_p]
    type = DirichletBC
    variable = p
    boundary = outlet
    value = 0
  []
[]

[Materials]
  [const]
    type = GenericConstantMaterial
    prop_names = 'rho mu'
    prop_values = '${rho} ${mu}'
  []
[]

[Postprocessors]
  # S = S1 (wetted cylinder) + S2 (flag surface), exactly as section 3 defines it.
  # The attachment arc is excluded: it is the flag/cylinder weld, not wetted.
  [drag]
    type = NodalSum
    variable = force_x
    boundary = 'cylinder interface'
  []
  [lift]
    type = NodalSum
    variable = force_y
    boundary = 'cylinder interface'
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
  type = Steady
  solve_type = NEWTON
  petsc_options_iname = '-pc_type -pc_factor_shift_type'
  petsc_options_value = 'lu       NONZERO'
  nl_rel_tol = 1e-10
  nl_abs_tol = 1e-9
  nl_max_its = 30
[]

[Outputs]
  exodus = false
  csv = true
[]
