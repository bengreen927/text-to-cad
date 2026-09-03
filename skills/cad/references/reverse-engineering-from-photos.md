# Reverse engineering from photographs: measure, draw, then model

Read this file when the only inputs are photographs or renders of a real object and the user wants
engineering drawings and/or a STEP model of it. The workflow that produced usable results on a
multi-part consumer medical device (12 molded parts, rods, springs, fasteners) was, in order:

1. survey every photo and classify it (orthographic-ish vs oblique, whole device vs single part),
2. establish an absolute scale and per-photo scales,
3. take pixel measurements and record them with provenance,
4. write ONE dimension table module that both the 2D sheets and the 3D generator import,
5. draw the dimensioned 2D sheets from that table and review them against the photos,
6. only then build the 3D assembly from the same table,
7. run independent reviewers (model vs photos, drawings, mechanism/fasteners, measurement audit)
   and fold their findings back into the table.

Doing the 3D model first from a few images produced a plausible-looking but structurally wrong
model twice. Measuring in 2D first exposed the real part topology (which rods attach where, what is
hinged to what) before any solid was built.

## 1. Photo survey

- Look at every image at reduced size first (a contact sheet built with PIL is cheap), then at full
  resolution only for the frames you will measure.
- Part-alone photos (parts laid on a table, top-down) are the best measurement sources: they are
  close to orthographic and show hidden features (screw holes, ribs, notches).
- Photos of the assembled device lying on its back or side are good for relative proportions of the
  large parts but suffer from parallax (see 2).
- Marketing renders are good for topology and pose, bad for dimensions.
- Note which photos share a camera setup (same session, same table): their scales are often equal,
  which lets a screw or rod photographed twice tie two photos together.

## 2. Absolute and per-photo scale

- Find one true scale reference inside the photo set: a ruler, a coin, a tape measure, a known
  fastener, a known accessory (a 1 inch wrap roll). Read tick spacing with an intensity profile
  along the ruler rather than by eye (a column-sum of a high-pass filtered band, then peak finding).
- Parallax: a reference lying on the table and a feature 30 to 50 mm above it differ in scale by
  (camera distance) / (camera distance minus height). For a top-down shot from 0.4 to 0.8 m that is
  5 to 12 percent, which is larger than every other error in the chain. Correct for it explicitly and
  state the correction, or ask the user for one caliper reading of the largest part and make every
  other dimension relative to it.
- Derive each photo's scale from an anchor that appears in it and is already known: ring width from
  the ruler photo, then rod pitch from the ring photo, then the rods photo from the screw head, and so
  on. Write the chain down; a wrong link shows up as a 10 to 20 percent disagreement later.
- When two photos disagree by more than 5 percent on the same feature, do not average silently:
  find the reason (parallax, foreshortening, a shadow included in a bounding box) and record it.

## 3. Pixel measurements

- Render gridded overlays (lines every 100 or 200 original pixels, labeled) and read coordinates off
  them; this is faster and more repeatable than guessing from a scaled image.
- Colour-segment what has a distinct colour (blue parts, black rods) with HSV thresholds and use
  connected components for bounding boxes and centroids. White parts on a white table cannot be
  segmented by brightness; read those from the grid.
- Measure diameters with a thresholded run along a single row or column across the feature, not
  with the bounding box of a mask: a mask bounding box includes the cast shadow and reads 20 to 50
  percent large; a dark-core run reads small on shiny parts. Report both and choose with a reason.
- Counts (notches, teeth, holes) and pitches are the most reliable readings of all; take them from
  the highest-resolution part photo.
- Keep a `measure/` folder: the segmentation script, the overlays, and a `measurements.md` with one
  row per reading (photo, pixel values, scale, mm, note).

## 4. One dimension table

Put every dimension in one Python module (for example `<device>_dims.py`) as named values in mm, with a
single `SCALE` factor derived from the one measurement the user can confirm with calipers. Both the
`.dxf.py` sheet generators and the `.step.py` model import this module, so a corrected scale or a
corrected pitch flows into the drawings and the model at once. Store part topology decisions there
too (hole coordinates, notch counts per rod variant, which end carries the thread).

## 5. Sheets before solids

Draw the orthographic sheets (see the `dxf` skill's `references/engineering-drawing-sheets.md`) from
the table and review them next to the photos. Errors that are cheap to fix on a sheet (a mirrored
plan view, a wrong notch count, a saddle that is a step instead of a taper) are expensive to find in a
finished assembly. The sheets also force decisions about hidden features (bores, ribs, internal
springs) that a render never shows.

## 6. Model from the same table

- Model the pose the photos show most often (arm closed, cover standing) and add joints for the
  other poses rather than modelling an unphotographed pose.
- Coil springs: `Helix` in `BuildLine` plus a circle section in `BuildSketch(Plane.XZ)` and `sweep()`
  produce a real helical solid that exports and renders; move it with `Axis(...).location`.
- Extruding a trapezoid sketched on `Plane.XZ` gives local v = world Z (the shape stands up), and the
  only edges parallel to an axis are the extrusion-direction edges, so `edges().filter_by(Axis.Y)`
  is the corner set to fillet; filtering by Z on such a body selects nothing or the wrong edges.
- A `RevoluteJoint`/`LinearJoint` on the fixed part pairs with a `RigidJoint` on the moving part whose
  location is `axis.location` of the same axis, so that `connect_to(..., angle=0)` is the identity.
- Snapshot and inspect the `.step.py` generator target, never the exported `.step`: the exported
  file keeps its own render cache under `__cadgen__/models/<name>.step/` that is not invalidated by a
  rebuild, and `inspect refs --facts` on it reports the old geometry.

## 7. Independent review

Run separate reviewers with the photo paths and the outputs: (a) model vs photos, (b) drawing
quality, (c) mechanism and fastener inventory, (d) measurement re-audit. Ask each to look at the
actual image files before stating anything and to separate "visible in the photo" from "inferred".
Fold the findings back into the dimension table first, then rebuild sheets and model.

## What to ask the user

Ask for exactly one thing when no scale reference exists or parallax dominates: a caliper reading of
the largest, flattest part. Everything else can proceed under stated assumptions.
