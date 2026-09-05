"""Parametric enclosure around the supplied, unmodified PCB STEP.

FRAME: origin at centre of outside base bottom; +Z up; connector faces +Y; mm.
Base local Z=0 is bottom; lid local Z=0 is mating underside of its plate.
PCB mounting datum is its measured board bottom, placed at Z=6.
Acceptance: base has four coaxial D2.5 bores and empty USB cutter; lid has
0.3 mm lip clearance; all three top-level components have zero shared volume.
Assumptions: D6 standoffs, 2 mm lip wall, cavity R1 corners (constant wall).
The 6 mm drill from Z=6 reaches the bottom, as required by the specified stack.
"""
from pathlib import Path
import json
import sys
from itertools import combinations
from build123d import (Align, Box, Color, Compound, Cylinder, GeomType,
                      Location, RectangleRounded, extrude, import_step)

PCB_SOURCE = Path(str(__import__('pathlib').Path(__file__).resolve().parents[5] / 'inputs/pcb.step'))
WALL = 2.0
FLOOR = 2.0
DEPTH = 14.0
STANDOFF_HEIGHT = 4.0
STANDOFF_DIAMETER = 6.0
DRILL_DIAMETER = 2.5
DRILL_DEPTH = 6.0
LID_THICKNESS = 2.0
LIP_DROP = 3.0
LIP_CLEARANCE = 0.3
LIP_WALL = 2.0
OUTSIDE_RADIUS = 3.0


def box(x, y, z, at=(0, 0, 0)):
    return Box(x, y, z, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location(at))


def rounded(x, y, radius, height, z=0):
    return extrude(RectangleRounded(x, y, radius), amount=height).moved(Location((0, 0, z)))


def common_volume(a, b):
    total = 0.0
    for sa in a.solids():
        for sb in b.solids():
            result = sa.intersect(sb)
            if result is not None:
                total += result.volume if hasattr(result, 'volume') else sum(s.volume for s in result)
    return total


def source_datums():
    pcb = import_step(PCB_SOURCE)
    board = next(c for c in pcb.children if c.label == 'pcb_board')
    connector = next(c for c in pcb.children if c.label == 'usb_c')
    bb = board.bounding_box()
    holes = sorted({(round(f.axis_of_rotation.position.X, 8), round(f.axis_of_rotation.position.Y, 8))
                    for f in board.faces().filter_by(GeomType.CYLINDER)
                    if abs(f.axis_of_rotation.direction.Z) > 0.999})
    assert len(holes) == 4
    assert abs(bb.size.X - 60) < 1e-6 and abs(bb.size.Y - 40) < 1e-6
    assert connector.bounding_box().center().Y > 0
    return pcb, board, connector, holes


def gen_step(variant='nominal'):
    if variant not in ('nominal', 'wide'):
        raise ValueError('variant must be nominal or wide')
    cx, cy = (64.0, 44.0) if variant == 'nominal' else (70.0, 48.0)
    pcb, board, connector, holes = source_datums()
    pcb_shift = FLOOR + STANDOFF_HEIGHT - board.bounding_box().min.Z
    conn_center = connector.bounding_box().center()
    cut_center = (conn_center.X, cy / 2 + WALL / 2, conn_center.Z + pcb_shift)
    rim = FLOOR + DEPTH
    base = rounded(cx + 2 * WALL, cy + 2 * WALL, OUTSIDE_RADIUS, rim)
    cavity = rounded(cx, cy, OUTSIDE_RADIUS - WALL, DEPTH + 1, FLOOR)
    base = base - cavity
    for x, y in holes:
        base = base + Cylinder(STANDOFF_DIAMETER / 2, STANDOFF_HEIGHT,
                    align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x, y, FLOOR)))
    drills = []
    for x, y in holes:
        drill = Cylinder(DRILL_DIAMETER / 2, DRILL_DEPTH,
                    align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
                    Location((x, y, FLOOR + STANDOFF_HEIGHT - DRILL_DEPTH)))
        drills.append(drill)
        base = base - drill
    usb_cutter = box(10, WALL + 2, 4.5, (cut_center[0], cut_center[1], cut_center[2] - 2.25))
    base = base - usb_cutter
    lx, ly = cx - 2 * LIP_CLEARANCE, cy - 2 * LIP_CLEARANCE
    plate = rounded(cx + 2 * WALL, cy + 2 * WALL, OUTSIDE_RADIUS, LID_THICKNESS)
    lip = rounded(lx, ly, 0.7, LIP_DROP, -LIP_DROP) - box(lx - 2 * LIP_WALL, ly - 2 * LIP_WALL, LIP_DROP, (0, 0, -LIP_DROP))
    lid = (plate + lip).moved(Location((0, 0, rim)))
    pcb = pcb.moved(Location((0, 0, pcb_shift)))
    base.label, lid.label, pcb.label = 'base', 'lid', 'pcb'
    base.color, lid.color = Color(0.20, 0.36, 0.52), Color(0.7, 0.78, 0.86)
    assembly = Compound(label='enclosure_' + variant, children=[base, lid, pcb])
    checks(assembly, variant, holes, drills, usb_cutter, lip, (cx, cy), cut_center)
    return assembly


def checks(assembly, variant, holes, drills, usb_cutter, lip, cavity_size, cut_center):
    parts = {c.label: c for c in assembly.children}
    base = parts['base']
    bores = [f for f in base.faces().filter_by(GeomType.CYLINDER) if abs(f.radius - DRILL_DIAMETER / 2) < 1e-6]
    errors = [min(((f.axis_of_rotation.position.X-x)**2 + (f.axis_of_rotation.position.Y-y)**2)**0.5 for f in bores) for x,y in holes]
    overlaps = {a+' / '+b: common_volume(parts[a],parts[b]) for a,b in combinations(parts,2)}
    report = {
      'variant': variant,
      'valid': {k: p.is_valid for k,p in parts.items()},
      'solid_counts': {k: len(p.solids()) for k,p in parts.items()},
      'volumes_mm3': {k: p.volume for k,p in parts.items()},
      'bounds_mm': {k: {'min': list(p.bounding_box().min), 'max': list(p.bounding_box().max)} for k,p in parts.items()},
      'interference_mm3': overlaps,
      'hole_centres_mm': holes,
      'coaxiality_max_mm': max(errors),
      'drill_diameters_mm': [2*f.radius for f in bores],
      'drill_depths_mm': [f.bounding_box().size.Z for f in bores],
      'drill_residual_mm3': [common_volume(base,d) for d in drills],
      'usb_residual_mm3': common_volume(base,usb_cutter),
      'usb_cutout_center_xz_mm': [cut_center[0],cut_center[2]],
      'lip_outer_xy_mm': [lip.bounding_box().size.X, lip.bounding_box().size.Y],
      'lip_clearance_per_side_mm': [(cavity_size[0]-lip.bounding_box().size.X)/2,(cavity_size[1]-lip.bounding_box().size.Y)/2],
    }
    assert all(report['valid'].values())
    assert [report['solid_counts'][k] for k in ('base','lid','pcb')] == [1,1,2]
    assert max(overlaps.values()) < 1e-7
    assert len(bores) == 4 and max(errors) < 1e-7
    assert max(report['drill_residual_mm3']) < 1e-7
    assert report['usb_residual_mm3'] < 1e-7
    assert all(abs(d-6) < 1e-7 for d in report['drill_depths_mm'])
    print(json.dumps(report), file=sys.stderr)
    return report
