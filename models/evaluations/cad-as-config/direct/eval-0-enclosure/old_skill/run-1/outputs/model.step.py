"""Frame: origin base bottom center, +Z up, +Y connector/front. Units mm."""
from pathlib import Path
from build123d import Box, Cylinder, Location, Axis, Compound, import_step, export_step

def at(shape,x=0,y=0,z=0): return shape.moved(Location((x,y,z)))
def rounded_box(x,y,z,r,z0):
    shape=at(Box(x,y,z),z=z0+z/2)
    return shape.fillet(r,shape.edges().filter_by(Axis.Z))
def build(p):
    cx,cy=p['cavity']; wall=p['wall']; floor=p['floor']; rim=floor+p['depth']
    base=rounded_box(cx+2*wall,cy+2*wall,rim,p['radius'],0)
    base=base-at(Box(cx,cy,p['depth']+2),z=floor+(p['depth']+2)/2)
    pcb=import_step(str(__import__('pathlib').Path(__file__).resolve().parents[5] / 'inputs/pcb.step'))
    board=next(c for c in pcb.children if c.label=='pcb_board')
    from build123d import GeomType
    centers=set()
    for f in board.faces().filter_by(GeomType.CYLINDER):
        if abs(f.radius-1.6)<1e-5:
            a=f.axis_of_rotation.position; centers.add((round(a.X,5),round(a.Y,5)))
    seat=floor+p['standoff']
    for x,y in sorted(centers):
        base=base+at(Cylinder(3,p['standoff']),x,y,floor+p['standoff']/2)
        base=base-at(Cylinder(1.25,6.02),x,y,seat-3)
    pcb=at(pcb,z=seat-board.bounding_box().min.Z)
    usb=next(c for c in pcb.children if c.label=='usb_c')
    # Children can retain local placement; measure transformed solids after applying the parent transform.
    usb_sol=max(pcb.solids(),key=lambda s:s.bounding_box().max.Z)
    ub=usb_sol.bounding_box(); center=ub.center()
    base=base-at(Box(10,2*wall+2,4.5),center.X,cy/2+wall/2,center.Z)
    lid=rounded_box(cx+2*wall,cy+2*wall,2,p['radius'],rim)
    lip=Box(cx-.6,cy-.6,3)-Box(cx-4.6,cy-4.6,5)
    lid=lid+at(lip,z=rim-1.5)
    base.label='base'; lid.label='lid'; pcb.label='pcb'
    return Compound(label='enclosure',children=[base,lid,pcb])

PARAMETERS={'nominal': {'cavity': [64, 44], 'wall': 2, 'floor': 2, 'depth': 14, 'radius': 3, 'standoff': 4}, 'wide': {'cavity': [70, 48], 'wall': 2, 'floor': 2, 'depth': 14, 'radius': 3, 'standoff': 4}}

def gen_step(variant='nominal'):
    return build(PARAMETERS[variant])

if __name__=='__main__':
    for variant,filename in [('nominal','model.step'),('wide','wide.step')]:
        export_step(gen_step(variant),str(Path(__file__).with_name(filename)))
