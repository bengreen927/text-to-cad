"""Generic upstream-upgrade smoke fixture; not product geometry."""
from cadgen import build123d as bd
from cadgen import step, glb

@glb(out='../GLB/plate.glb')
@step(out='../STEP/plate.step')
def plate():
    body = bd.Box(60, 40, 4)
    for x in (-24, 24):
        for y in (-14, 14):
            body -= bd.Pos(x, y, 0) * bd.Cylinder(2.25, 8)
    body.label = 'Mounting plate — four clearance holes'
    return body

if __name__ == '__main__':
    plate()
