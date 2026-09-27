#!/usr/bin/env python3
"""Turek & Hron FSI1 geometry, meshed with Gmsh and tagged for MOOSE.

Geometry is taken from the primary paper (Table 1 and section 2.4), not from a
secondary restatement:

    channel            L = 2.5, H = 0.41
    cylinder           centre (0.2, 0.2), r = 0.05
    flag               l = 0.35, h = 0.02, right bottom corner (0.6, 0.19)
    control point A    (0.6, 0.2) at t = 0

The cylinder centre is at y = 0.2 while the channel centreline is at y = 0.205.
That asymmetry is DELIBERATE (section 2.4) -- it stops the onset of any
oscillation from depending on round-off. Do not "fix" it.

The flag's left end is fully attached to the cylinder, so the solid is the
rectangle minus the disk and its left boundary is the circular arc. The raw
rectangle is started at x = 0.24, inside the circle, so the difference lands
exactly on the arc; the circle meets y = 0.19 at
x = 0.2 + sqrt(0.05^2 - 0.01^2) = 0.248990.

Usage:  make_fsi1_mesh.py LEVEL      LEVEL = 0,1,2 -> ~1k, 4k, 16k elements,
matching the paper's own grid sequence (992 / 3968 / 15872) so the comparison
is like-for-like rather than under-resolved.
"""
import sys
import gmsh

L, H = 2.5, 0.41
CX, CY, R = 0.2, 0.2, 0.05
FX0_RAW, FX1 = 0.24, 0.6          # raw rectangle overlaps the disk
FY0, FY1 = 0.19, 0.21
A_POINT = (0.6, 0.2)

# Element size at the flag tip / cylinder, and in the far field, per level.
SIZES = {0: (0.0075, 0.06), 1: (0.00375, 0.03), 2: (0.001875, 0.015)}


def build(level: int, out: str) -> None:
    fine, coarse = SIZES[level]
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("fsi1")
    occ = gmsh.model.occ

    channel = occ.addRectangle(0, 0, 0, L, H)
    disk = occ.addDisk(CX, CY, 0, R, R)
    flag = occ.addRectangle(FX0_RAW, FY0, 0, FX1 - FX0_RAW, FY1 - FY0)
    # copies, because the boolean ops consume their arguments
    disk_c = occ.copy([(2, disk)])[0][1]
    flag_c = occ.copy([(2, flag)])[0][1]

    # solid = flag minus disk  -> left boundary is the cylinder arc
    solid, _ = occ.cut([(2, flag)], [(2, disk)])
    # fluid = channel minus (disk union flag)
    obstacle, _ = occ.fuse([(2, disk_c)], [(2, flag_c)])
    fluid, _ = occ.cut([(2, channel)], obstacle)
    # fragment so the fluid and solid share the interface nodes
    parts, _ = occ.fragment(fluid, solid)
    occ.synchronize()

    # Identify subdomains by bounding box: the solid is the only surface that
    # fits inside the flag's box.
    fluid_tags, solid_tags = [], []
    for dim, tag in gmsh.model.getEntities(2):
        x0, y0, _, x1, y1, _ = gmsh.model.getBoundingBox(dim, tag)
        if x0 > FX0_RAW - 1e-6 and x1 < FX1 + 1e-6 and y0 > FY0 - 1e-6 and y1 < FY1 + 1e-6:
            solid_tags.append(tag)
        else:
            fluid_tags.append(tag)
    if len(solid_tags) != 1 or len(fluid_tags) != 1:
        raise SystemExit(f"expected 1 fluid + 1 solid, got {fluid_tags} / {solid_tags}")

    # Classify curves by a point ON the curve, not by the bounding-box centre:
    # the bbox centre of a circular arc lies INSIDE the circle, so an on-circle
    # test against it silently fails and the cylinder ends up tagged as wall.
    def midpoint(tag):
        lo, hi = gmsh.model.getParametrizationBounds(1, tag)
        return gmsh.model.getValue(1, tag, [0.5 * (lo[0] + hi[0])])

    solid_curves = {abs(t) for _, t in
                    gmsh.model.getBoundary([(2, solid_tags[0])], oriented=False)}

    inlet, outlet, walls, cyl, interface, attach = [], [], [], [], [], []
    for dim, tag in gmsh.model.getEntities(1):
        x, y, _ = midpoint(tag)
        on_circle = abs(((x - CX) ** 2 + (y - CY) ** 2) ** 0.5 - R) < 1e-6
        if abs(x) < 1e-6:
            inlet.append(tag)
        elif abs(x - L) < 1e-6:
            outlet.append(tag)
        elif abs(y) < 1e-6 or abs(y - H) < 1e-6:
            walls.append(tag)
        elif on_circle:
            # the arc under the flag is the attachment (not wetted); the rest is
            # the cylinder surface the fluid sees
            (attach if tag in solid_curves else cyl).append(tag)
        elif tag in solid_curves:
            interface.append(tag)
        else:
            walls.append(tag)

    gmsh.model.addPhysicalGroup(2, fluid_tags, 1); gmsh.model.setPhysicalName(2, 1, "fluid")
    gmsh.model.addPhysicalGroup(2, solid_tags, 2); gmsh.model.setPhysicalName(2, 2, "solid")
    for tag, curves, name in ((1, inlet, "inlet"), (2, outlet, "outlet"),
                              (3, walls, "walls"), (4, cyl, "cylinder"),
                              (5, interface, "interface"), (6, attach, "attachment")):
        if curves:
            gmsh.model.addPhysicalGroup(1, curves, tag)
            gmsh.model.setPhysicalName(1, tag, name)

    # Refine towards the cylinder and the flag, coarsen downstream.
    gmsh.model.mesh.field.add("Distance", 1)
    gmsh.model.mesh.field.setNumbers(1, "CurvesList", cyl + interface + attach)
    gmsh.model.mesh.field.setNumber(1, "Sampling", 400)
    gmsh.model.mesh.field.add("Threshold", 2)
    gmsh.model.mesh.field.setNumber(2, "InField", 1)
    gmsh.model.mesh.field.setNumber(2, "SizeMin", fine)
    gmsh.model.mesh.field.setNumber(2, "SizeMax", coarse)
    gmsh.model.mesh.field.setNumber(2, "DistMin", 0.01)
    gmsh.model.mesh.field.setNumber(2, "DistMax", 0.35)
    gmsh.model.mesh.field.setAsBackgroundMesh(2)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.RecombineAll", 1)     # quads: better for the flag
    gmsh.model.mesh.generate(2)
    gmsh.write(out)

    counts = {}
    for name, tags in (("fluid", fluid_tags), ("solid", solid_tags)):
        n = 0
        for t in tags:
            for et, en in zip(*gmsh.model.mesh.getElements(2, t)[:2]):
                n += len(en)
        counts[name] = n
    print(f"level {level}: {out}  elements={counts['fluid']+counts['solid']} "
          f"(fluid {counts['fluid']}, solid {counts['solid']})")
    print(f"  fluid surface {fluid_tags}, solid surface {solid_tags}")
    print(f"  curves: inlet={len(inlet)} outlet={len(outlet)} walls={len(walls)} "
          f"cylinder={len(cyl)} interface={len(interface)} attachment={len(attach)}")
    gmsh.finalize()


if __name__ == "__main__":
    lv = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    build(lv, sys.argv[2] if len(sys.argv) > 2 else f"fsi1_L{lv}.msh")
