"""Frame: origin base bottom center, +Z up, +Y connector/front. Units mm."""
from pathlib import Path
from build123d import Box, Cylinder, Location, Axis, Compound, import_step, export_step

def at(shape,x=0,y=0,z=0): return shape.moved(Location((x,y,z)))
def rounded_box(x,y,z,r,z0):
    shape=at(Box(x,y,z),z=z0+z/2)
    return shape.fillet(r,shape.edges().filter_by(Axis.Z))
def build(p):
    x,y=p['plate']; pitchx,pitchy=p['pitch']; d=p['stem']
    plate=rounded_box(x,y,8,4,0)-at(Cylinder((d+.4)/2,10),z=4)
    for hx in (-pitchx,pitchx):
        for hy in (-pitchy,pitchy): plate=plate-at(Cylinder(2.25,10),hx,hy,4)
    insert=at(Cylinder(d/2,8),z=4)+at(Cylinder((d+8)/2,3),z=9.5)
    plate.label='plate'; insert.label='insert'
    return Compound(label='fixture',children=[plate,insert])

PARAMETERS={'nominal': {'plate': [80, 60], 'pitch': [30, 20], 'stem': 20}, 'wide': {'plate': [100, 70], 'pitch': [40, 25], 'stem': 24}}

def gen_step(variant='nominal'):
    return build(PARAMETERS[variant])

if __name__=='__main__':
    for variant,filename in [('nominal','model.step'),('wide','wide.step')]:
        export_step(gen_step(variant),str(Path(__file__).with_name(filename)))
