# Task: two-part enclosure for an imported PCB

Build a parametric two-part enclosure (base + lid) for the PCB in the STEP file at
`inputs/pcb.step` (read-only ground truth; do not modify or copy over it). The PCB STEP contains two
labelled solids: `pcb_board` (the board) and `usb_c` (a connector body standing on the board's top
face at one edge). The four mounting holes and the connector position are only in the STEP; there is
no drawing.

Deliverable: `WORKDIR/model.step.py` defining `gen_step()` that returns a labelled assembly with
exactly these top-level children: `base`, `lid`, and `pcb` (the imported PCB, placed in its assembled
position). Write the `.step` file too (`WORKDIR/model.step`). Put any helper modules in WORKDIR.

Specification (mm):
- Frame: origin at the centre of the base's outside bottom face, +Z up, the PCB's connector edge
  faces +Y.
- Base: internal cavity 64 x 44 (2.0 mm clearance around the 60 x 40 board), walls 2.0, floor 2.0,
  outside vertical corner radius 3.0, cavity depth 14.0 measured from the floor top to the base rim.
- Four standoffs rise from the floor, coaxial with the four PCB holes, top face 4.0 above the floor
  top, each with an M3 tap-drill hole D2.5 x 6.0 deep from the standoff top. The PCB sits on the
  standoffs.
- Lid: a 2.0 plate covering the base rim, with a lip that drops 3.0 into the cavity and clears the
  cavity walls by 0.3 per side (lip outer 63.4 x 43.4).
- USB-C cutout through the +Y wall of the base: 10.0 wide (X) x 4.5 tall (Z), centred on the
  connector body of the placed PCB.
- No part may interpenetrate another: base, lid and pcb share 0 mm^3.
- Colours are free. No other features are required.

Acceptance: a script will path-load `model.step.py`, call `gen_step()`, and measure the
interpenetration volumes, standoff-to-hole coaxiality, lip clearance, and the USB-C cutout against
the placed connector. Report the checks you ran and their numeric results in your final message,
plus the exact commands you used to build and validate.


Also support gen_step(variant="wide"): cavity 70 x 48, all other values unchanged. gen_step() is the default nominal model. Treat each call independently. Save model.step and wide.step.
