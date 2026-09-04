"""Parametric mounting plate and removable insert; dimensions in mm.

FRAME: origin at plate bottom footprint center, XY base, +Z up, +Y front.
Plate is the fixed root. Insert shoulder seats on plate top at Z=8.
Acceptance: plate has prescribed bounds, R4 corners and five open through bores.
Acceptance: insert is one fused solid with specified stem/flange and no clash.
"""
import json
import math
import sys
from build123d import (Align, Axis, Compound, Cylinder, GeomType, Location,
                      Pos, RectangleRounded, RigidJoint, extrude)

COMMON = dict(thickness=8.0, corner_radius=4.0, hole_diameter=4.5,
              radial_clearance=0.2, flange_thickness=3.0)  # mm, fixture specification
VARIANTS = {
    'nominal': dict(width=80.0, depth=60.0, hole_x=30.0, hole_y=20.0,
                    stem_diameter=20.0, flange_diameter=28.0),
    'wide': dict(width=100.0, depth=70.0, hole_x=40.0, hole_y=25.0,
                 stem_diameter=24.0, flange_diameter=32.0),
}


def volume(shape):
    if shape is None:
        return 0.0
    if hasattr(shape, 'volume'):
        return float(shape.volume)
    return sum(volume(s) for s in shape)


def cylinder(radius, height):
    return Cylinder(radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))


def checks(assembly, p, variant):
    plate, insert = assembly.children
    t = p['thickness']
    bore_r = p['stem_diameter']/2 + p['radial_clearance']
    holes = [(sx*p['hole_x'], sy*p['hole_y'], p['hole_diameter']/2)
             for sx in (-1, 1) for sy in (-1, 1)] + [(0, 0, bore_r)]
    hole_residuals = [volume(plate.intersect(Pos(x, y, 0)*cylinder(r, t)))
                      for x, y, r in holes]
    cylindrical = list(plate.faces().filter_by(GeomType.CYLINDER))
    missing = []
    for x, y, r in holes:
        if not any(abs(f.radius-r)<1e-6 and
                   abs(f.axis_of_rotation.position.X-x)<1e-6 and
                   abs(f.axis_of_rotation.position.Y-y)<1e-6 and
                   abs(f.bounding_box().size.Z-t)<1e-6 for f in cylindrical):
            missing.append([x, y, r])
    pb, ib = plate.bounding_box(), insert.bounding_box()
    corners = [f for f in cylindrical if abs(f.radius-p['corner_radius'])<1e-6]
    expected_plate = (p['width']*p['depth']-(4-math.pi)*p['corner_radius']**2
                      -4*math.pi*(p['hole_diameter']/2)**2-math.pi*bore_r**2)*t
    expected_insert = math.pi*(p['stem_diameter']/2)**2*t + math.pi*(p['flange_diameter']/2)**2*p['flange_thickness']
    interference = sum(volume(a.intersect(b)) for a in plate.solids() for b in insert.solids())
    symmetry = volume(plate-plate.rotate(Axis.Z, 180))
    stem_faces = [f for f in insert.faces().filter_by(GeomType.CYLINDER)
                  if abs(f.radius-p['stem_diameter']/2)<1e-6]
    bore_faces = [f for f in cylindrical if abs(f.radius-bore_r)<1e-6]
    clearance = bore_faces[0].radius-stem_faces[0].radius
    metrics = dict(variant=variant, labels=[c.label for c in assembly.children],
                   solids=[len(plate.solids()), len(insert.solids())],
                   valid=[plate.is_valid, insert.is_valid],
                   plate_bbox_mm=list(pb.size), insert_bbox_mm=list(ib.size),
                   plate_z_mm=[pb.min.Z,pb.max.Z], insert_z_mm=[ib.min.Z,ib.max.Z],
                   plate_volume_mm3=plate.volume, insert_volume_mm3=insert.volume,
                   volume_error_mm3=[plate.volume-expected_plate,insert.volume-expected_insert],
                   radial_clearance_mm=clearance, interference_mm3=interference,
                   hole_residuals_mm3=hole_residuals, missing_holes=missing,
                   corner_count=len(corners), symmetry_residual_mm3=symmetry)
    assert metrics['labels']==['plate','insert'] and metrics['solids']==[1,1]
    assert all(metrics['valid']) and len(corners)==4 and not missing
    assert all(abs(a-b)<1e-6 for a,b in zip(pb.size,(p['width'],p['depth'],t)))
    assert all(abs(a-b)<1e-6 for a,b in zip(ib.size,(p['flange_diameter'],p['flange_diameter'],t+p['flange_thickness'])))
    assert abs(pb.min.Z)<1e-6 and abs(ib.min.Z)<1e-6
    assert max(map(abs, metrics['volume_error_mm3']))<1e-5
    assert abs(clearance-0.2)<1e-6 and interference<1e-6
    assert max(hole_residuals)<1e-6 and symmetry<1e-6
    print(json.dumps(metrics), file=sys.stderr)
    return metrics


def gen_step(variant='nominal'):
    if variant not in VARIANTS:
        raise ValueError('variant must be nominal or wide')
    p = dict(COMMON, **VARIANTS[variant])
    t = p['thickness']
    plate = extrude(RectangleRounded(p['width'], p['depth'], p['corner_radius']), amount=t)
    for sx in (-1, 1):
        for sy in (-1, 1):
            plate = plate - Pos(sx*p['hole_x'],sy*p['hole_y'],0)*cylinder(p['hole_diameter']/2,t)
    plate = plate-cylinder(p['stem_diameter']/2+p['radial_clearance'],t)
    insert = cylinder(p['stem_diameter']/2,t) + Pos(0,0,t)*cylinder(p['flange_diameter']/2,p['flange_thickness'])
    plate.label = 'plate'
    insert.label = 'insert'
    # Native datum relationship: coaxial shoulder and top face, flush at Z=t.
    seat = RigidJoint('insert_seat', plate, Location((0,0,t)))
    shoulder = RigidJoint('flange_underside', insert, Location((0,0,t)))
    seat.connect_to(shoulder)
    result = Compound(label='mounting_fixture_'+variant, children=[plate,insert])
    checks(result,p,variant)
    return result


if __name__ == '__main__':
    first = gen_step('nominal')
    gen_step('wide')
    last = gen_step('nominal')
    assert abs(first.volume-last.volume)<1e-6
    assert first is not last and first.children[0] is not last.children[0]
    print('nominal-wide-nominal repeatability passed')
