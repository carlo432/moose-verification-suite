# Assert the FSI1 mesh is the FSI1 geometry before any physics is put on it.
# Every quantity below has a closed form from the paper's Table 1, so a
# mis-tagged sideset or a lost subdomain shows up as a number, not a surprise
# three days later.
[Mesh]
  # Gmsh 1-D physical groups arrive as UNNAMED nodesets 1-6, in the order the
  # groups were declared in make_fsi1_mesh.py. They are promoted to sidesets and
  # given their names back here, so every downstream input refers to
  # "interface" rather than to a bare integer that nothing checks.
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
    new_boundary = 'inlet outlet walls cylinder interface_2sided attachment'
  []
  # The nodeset-derived interface carries sides from BOTH blocks, so it measures
  # exactly twice the true interface length and would silently double any
  # traction integral taken over it. This builds the properly oriented,
  # single-sided fluid->solid interface that the coupling actually needs.
  [interface]
    type = SideSetsBetweenSubdomainsGenerator
    input = names
    primary_block = fluid
    paired_block = solid
    new_boundary = interface
  []
[]
[Variables/u][]
[Kernels/diff]
  type = Diffusion
  variable = u
[]
[BCs]
  [l]
    type = DirichletBC
    variable = u
    boundary = inlet
    value = 0
  []
  [r]
    type = DirichletBC
    variable = u
    boundary = outlet
    value = 1
  []
[]
[Postprocessors]
  [area_fluid]
    type = VolumePostprocessor
    block = fluid
  []
  [area_solid]
    type = VolumePostprocessor
    block = solid
  []
  [len_inlet]
    type = AreaPostprocessor
    boundary = inlet
  []
  [len_outlet]
    type = AreaPostprocessor
    boundary = outlet
  []
  [len_walls]
    type = AreaPostprocessor
    boundary = walls
  []
  [len_cylinder]
    type = AreaPostprocessor
    boundary = cylinder
  []
  [len_interface]
    type = AreaPostprocessor
    boundary = interface
  []
  [len_interface_2sided]
    type = AreaPostprocessor
    boundary = interface_2sided
  []
  [len_attachment]
    type = AreaPostprocessor
    boundary = attachment
  []
[]
[Executioner]
  type = Steady
  solve_type = PJFNK
  petsc_options_iname = '-pc_type'
  petsc_options_value = 'lu'
[]
[Outputs]
  csv = true
  exodus = false
[]
