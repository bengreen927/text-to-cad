"""Controlled analytic smoke geometry, independent of evaluated candidates."""
import os
import build123d as b
COUNT = 0

def box(x,y,z,cx=0,cy=0,z0=0):
    return b.Pos(cx,cy,z0)*b.Box(x,y,z,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
def cyl(r,z,x=0,y=0,z0=0):
    return b.Pos(x,y,z0)*b.Cylinder(r,z,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
def rounded(x,y,z,r):
    return b.extrude(b.RectangleRounded(x,y,r),amount=z)
def gen_step(variant='nominal'):
    global COUNT
    COUNT += 1
    wide = variant=='wide'
    mutation=os.environ.get('GRADER_SMOKE_MUTATION','')
    if os.environ.get('GRADER_SMOKE_CASE','fixture')=='fixture':
        x,y,hx,hy,d=(100,70,40,25,24) if wide else (80,60,30,20,20)
        plate=rounded(x,y,8,4 if mutation!='radius' else 2)
        for xx in [-hx,hx]:
            for yy in [-hy,hy]: plate=plate.cut(cyl(2.25,8,xx,yy))
        plate=plate.cut(cyl((d+.4)/2,8 if mutation!='blind' else 7,z0=0 if mutation!='blind' else 1))
        insert=cyl(d/2 if mutation!='interference' else d/2+.3,8).fuse(cyl((d+8)/2,3,z0=8))
        plate.label='plate' if mutation!='label' else 'Plate'
        insert.label='insert'
        shape=b.Compound(children=[plate,insert])
    else:
        cx,cy=(70,48) if wide else (64,44)
        cavity = b.Pos(0,0,2)*rounded(cx,cy,14,1) if os.environ.get('GRADER_SMOKE_CAVITY_RADIUS')=='1' else box(cx,cy,14,z0=2)
        base=rounded(cx+4,cy+4,16,3).cut(cavity)
        for xx in [-26,26]:
            for yy in [-16,16]:
                base=base.fuse(cyl(3,4,xx,yy,2)).cut(cyl(1.25,6,xx,yy))
        base=base.cut(box(10,cy+8,4.5,10 if mutation!='usb' else 0,(cy+8)/2,6.95))
        lid=b.Pos(0,0,16)*rounded(cx+4,cy+4,2,3)
        lip=box(cx-.6,cy-.6,3,z0=13).cut(box(cx-4,cy-4,3,z0=13))
        if mutation=='lip': lip=lip.moved(b.Pos(.2,0,0))
        lid=lid.fuse(lip)
        pcb=b.import_step(str(__import__('pathlib').Path(__file__).resolve().parents[1] / 'inputs/pcb.step')).moved(b.Pos(0,0,6.8 if mutation!='seat' else 7.0))
        base.label,lid.label,pcb.label='base','lid','pcb'
        shape=b.Compound(children=[base,lid,pcb])
    if mutation=='origin' or (mutation=='state' and COUNT>1): shape=shape.moved(b.Pos(1,0,0))
    return shape
