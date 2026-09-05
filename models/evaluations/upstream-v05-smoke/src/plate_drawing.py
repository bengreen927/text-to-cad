"""Generic build123d DXF export smoke fixture."""
from cadgen import build123d as bd
from cadgen import dxf

@dxf(out='../DXF/plate.dxf')
def plate_drawing():
    with bd.BuildSketch() as sketch:
        bd.Rectangle(60, 40)
        with bd.Locations(*[(x, y) for x in (-24, 24) for y in (-14, 14)]):
            bd.Circle(2.25, mode=bd.Mode.SUBTRACT)
    return sketch.sketch

if __name__ == '__main__':
    plate_drawing()
