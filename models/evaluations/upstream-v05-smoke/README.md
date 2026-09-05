# v0.5 upgrade smoke fixture

A generic 60 x 40 x 4 mm plate with four 4.5 mm diameter through holes at
(+/-24, +/-14) mm. It tests the v0.5 script decorators, STEP/GLB outputs,
build123d DXF generation, document inspection and rendering. It is not a
model-quality benchmark or a product fixture.

From the repository root, with the fork runtime installed:

```sh
python models/evaluations/upstream-v05-smoke/src/plate.py
python models/evaluations/upstream-v05-smoke/src/plate_drawing.py
cadgen step inspect validate models/evaluations/upstream-v05-smoke/STEP/plate.step --json
cadgen step inspect refs models/evaluations/upstream-v05-smoke/STEP/plate.step --facts --json
cadgen step snapshot models/evaluations/upstream-v05-smoke/STEP/plate.step models/evaluations/upstream-v05-smoke/plate.png
```

Expected volume: `60*40*4 - 4*pi*(4.5/2)^2*4 = 9345.530995 mm^3`.
Expected solid count: 1. An unchanged rerun should report `outcome: current`
and preserve the artifact bytes. Generated artifacts are ignored.
