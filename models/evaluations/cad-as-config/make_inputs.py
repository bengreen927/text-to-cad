from pathlib import Path
from build123d import Box, Cylinder, Location, Compound, export_step
out=Path(__file__).parent/'inputs'; out.mkdir(exist_ok=True)
pcb=Box(60,40,1.6)
for x in (-26,26):
    for y in (-16,16): pcb=pcb-Cylinder(1.6,10).moved(Location((x,y,0)))
usb=Box(8.94,7.3,3.2).moved(Location((10,20-7.3/2,2.4)))
pcb.label='pcb_board'; usb.label='usb_c'
export_step(Compound(label='pcb',children=[pcb,usb]),out/'pcb.step')
