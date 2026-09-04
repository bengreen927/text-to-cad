"""Parametric enclosure, mm. Imported STEP is read-only; no adjacent import cache.
Base datum: outside bottom centre. Lid datum: plate underside. PCB: board underside.
Assumptions: standoffs OD6, lip wall 2, square cavity corners. Tap bores break
through the floor because the specified 6 mm depth equals floor+standoff height.
"""
from build123d import (Align, Axis, Box, Color, Compound, Cylinder, GeomType,
                       Location, RectangleRounded, RigidJoint, extrude, import_step)

PCB_PATH = str(__import__('pathlib').Path(__file__).resolve().parents[5] / 'inputs/pcb.step')
WALL = FLOOR = LID_THICKNESS = 2.0
CAVITY_DEPTH = 14.0
STANDOFF_HEIGHT = 4.0
STANDOFF_RADIUS = 3.0
TAP_RADIUS, TAP_DEPTH = 1.25, 6.0
CORNER_RADIUS = 3.0
LIP_DROP, LIP_CLEARANCE, LIP_WALL = 3.0, 0.3, 2.0
USB_WIDTH, USB_HEIGHT = 10.0, 4.5
BOTTOM_ALIGN = (Align.CENTER, Align.CENTER, Align.MIN)


def imported_geometry():
    pcb = import_step(PCB_PATH)
    board = next(c for c in pcb.children if c.label == 'pcb_board')
    usb = next(c for c in pcb.children if c.label == 'usb_c')
    axes = sorted(set((round(f.axis_of_rotation.position.X, 8),
                       round(f.axis_of_rotation.position.Y, 8))
                      for f in board.faces() if f.geom_type == GeomType.CYLINDER))
    assert len(axes) == 4
    return pcb, board, usb, axes


def gen_step(variant='nominal'):
    if variant not in ('nominal', 'wide'):
        raise ValueError('variant must be nominal or wide')
    cavity_x, cavity_y = (64.0, 44.0) if variant == 'nominal' else (70.0, 48.0)
    outside_x, outside_y = cavity_x + 2*WALL, cavity_y + 2*WALL
    rim_z = FLOOR + CAVITY_DEPTH
    support_z = FLOOR + STANDOFF_HEIGHT
    pcb, board, usb, hole_axes = imported_geometry()
    board_bounds = board.bounding_box()
    shift_x = -(board_bounds.min.X + board_bounds.max.X)/2
    shift_y = -(board_bounds.min.Y + board_bounds.max.Y)/2
    shift_z = support_z - board_bounds.min.Z
    connector = usb.bounding_box().center()
    usb_x, usb_z = connector.X + shift_x, connector.Z + shift_z

    base = extrude(RectangleRounded(outside_x, outside_y, CORNER_RADIUS), amount=rim_z)
    base -= Box(cavity_x, cavity_y, CAVITY_DEPTH,
                align=BOTTOM_ALIGN).moved(Location((0, 0, FLOOR)))
    bosses = [Cylinder(STANDOFF_RADIUS, STANDOFF_HEIGHT, align=BOTTOM_ALIGN)
              .moved(Location((x+shift_x,y+shift_y,FLOOR))) for x,y in hole_axes]
    base = base.fuse(*bosses)
    drills = [Cylinder(TAP_RADIUS, TAP_DEPTH, align=BOTTOM_ALIGN)
              .moved(Location((x+shift_x,y+shift_y,support_z-TAP_DEPTH))) for x,y in hole_axes]
    base = base.cut(*drills)
    base -= Box(USB_WIDTH, WALL+2, USB_HEIGHT).moved(
        Location((usb_x, cavity_y/2 + WALL/2, usb_z)))
    base.label, base.color = 'base', Color(0.25,0.40,0.57)

    lid = extrude(RectangleRounded(outside_x, outside_y, CORNER_RADIUS), amount=LID_THICKNESS)
    lip_x, lip_y = cavity_x-2*LIP_CLEARANCE, cavity_y-2*LIP_CLEARANCE
    lip = Box(lip_x, lip_y, LIP_DROP, align=BOTTOM_ALIGN).moved(Location((0,0,-LIP_DROP)))
    lip -= Box(lip_x-2*LIP_WALL, lip_y-2*LIP_WALL, LIP_DROP,
               align=BOTTOM_ALIGN).moved(Location((0,0,-LIP_DROP)))
    lid = lid.fuse(lip)
    lid.label, lid.color = 'lid', Color(0.72,0.78,0.85)
    # Native source joints state fixed-first datum relationships.
    RigidJoint('rim_seat', base, Location((0,0,rim_z)))
    RigidJoint('plate_underside', lid, Location())
    base.joints['rim_seat'].connect_to(lid.joints['plate_underside'])
    pcb.label = 'pcb'
    RigidJoint('board_seat', base, Location((shift_x,shift_y,support_z)))
    RigidJoint('board_underside', pcb, Location((0,0,board_bounds.min.Z)))
    base.joints['board_seat'].connect_to(pcb.joints['board_underside'])
    # Bake the resolved PCB joint transform into its children. build123d
    # compound booleans otherwise use child-local shapes despite world bounds.
    pcb = Compound(label='pcb', children=[child.moved(pcb.location) for child in pcb.children])
    return Compound(label='enclosure_'+variant, children=[base,lid,pcb])
