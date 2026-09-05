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

import json, hashlib

def gen_step(variant='nominal'):
    config=json.loads(Path(__file__).with_name('config.json').read_text())
    if config['units']!='mm': raise ValueError('Units must be mm')
    p=config['variants'][variant]
    if any(v<=0 for v in p.values() if isinstance(v,(int,float))): raise ValueError('Positive dimensions required')
    shape=build(p)
    parts={c.label:c for c in shape.children}
    checks={}
    for k,s in parts.items():
        checks[k+'_valid']=bool(s.is_valid) and s.volume>0
    names=list(parts)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            v=0.0
            for sa in parts[a].solids():
                for sb in parts[b].solids():
                    c=sa.intersect(sb)
                    if c is not None: v+=sum(s.volume for s in c) if not hasattr(c,'volume') else c.volume
            checks[a+'_'+b+'_clear']=v<1e-5
    manifest={'variant':variant,'resolved':p,'checks':checks,'verified':all(checks.values()),
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()+Path(__file__).with_name('config.json').read_bytes()).hexdigest()}
    Path(__file__).with_name(variant+'.manifest.json').write_text(json.dumps(manifest,indent=2))
    if not all(checks.values()): raise ValueError('Verification failed: '+str(checks))
    return shape

if __name__=='__main__':
    for variant,filename in [('nominal','model.step'),('wide','wide.step')]:
        export_step(gen_step(variant),str(Path(__file__).with_name(filename)))
