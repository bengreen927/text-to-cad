"""Mounting plate and removable insert; mm, XY bottom datum, +Z up."""
from build123d import (
    Align, Color, Compound, Cylinder, Location, RectangleRounded,
    RigidJoint, extrude,
)


def gen_step(variant="nominal"):
    """Return fresh plate and insert children on every call."""
    if variant == "nominal":
        width, depth, hole_x, hole_y, stem_diameter = 80.0, 60.0, 30.0, 20.0, 20.0
    elif variant == "wide":
        width, depth, hole_x, hole_y, stem_diameter = 100.0, 70.0, 40.0, 25.0, 24.0
    else:
        raise ValueError("variant must be 'nominal' or 'wide'")
    thickness, corner_radius, mounting_diameter = 8.0, 4.0, 4.5
    radial_clearance, flange_height = 0.2, 3.0
    bore_diameter = stem_diameter + 2.0 * radial_clearance
    flange_diameter = stem_diameter + 8.0
    bottom_align = (Align.CENTER, Align.CENTER, Align.MIN)

    plate = extrude(RectangleRounded(width, depth, corner_radius), amount=thickness)
    # Through cutters extend 1 mm past both faces.
    cutters = [Cylinder(bore_diameter / 2, thickness + 2, align=bottom_align).moved(Location((0, 0, -1)))]
    for x in (-hole_x, hole_x):
        for y in (-hole_y, hole_y):
            cutters.append(Cylinder(mounting_diameter / 2, thickness + 2, align=bottom_align).moved(Location((x, y, -1))))
    plate = plate.cut(*cutters)
    plate.label = "plate"
    plate.color = Color(0.34, 0.44, 0.56)

    stem = Cylinder(stem_diameter / 2, thickness, align=bottom_align)
    flange = Cylinder(flange_diameter / 2, flange_height, align=bottom_align).moved(Location((0, 0, thickness)))
    insert = stem.fuse(flange)
    insert.label = "insert"
    insert.color = Color(0.75, 0.39, 0.10)
    # Named mating datums: flange underside seated on the plate top, coaxial Z.
    RigidJoint("flange_seat", plate, Location((0, 0, thickness)))
    RigidJoint("flange_underside", insert, Location((0, 0, thickness)))
    plate.joints["flange_seat"].connect_to(insert.joints["flange_underside"])
    return Compound(label="mounting_fixture", children=[plate, insert])
