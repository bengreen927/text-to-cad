# Reverse engineering from photographs: measure, draw, then model

Read this file when photographs or renders are the only dimensional source for
reproducing a real object. Images can establish topology, proportion, and design
intent, but they do not become a dimensioned contract without scale and
uncertainty.

Keep source images, measurement overlays, and identifying details in the owning
project. Do not copy them into a shared skill repository.

## Workflow

1. Survey every image and classify it by viewpoint, perspective, subject, and
   likely measurement value.
2. Establish one absolute scale and a documented scale for every image used.
3. Record pixel measurements, conversions, and uncertainty with source paths.
4. Resolve one shared dimension table used by both `@dxf` drawings and `@step`
   models.
5. Review dimensioned orthographic drawings against the images before building
   detailed solids.
6. Build the 3D parts and assembly from the same values.
7. Review visual resemblance, drawings, mechanism assumptions, fasteners, and
   measurements as separate passes. Fold corrections into the table first.
8. Inspect the written STEP documents, including complete interference checks
   for assemblies and requirement-specific checks from `cad-as-config.md`.

For a rough concept, the user may accept a shorter path. Label it as inferred
geometry rather than reverse-engineered dimensional evidence.

## Survey and scale

- Start with a contact sheet, then inspect full resolution only for images used
  to measure. Part-alone, nearly orthographic views are usually stronger than
  oblique assembly views. Marketing renders are useful for topology and pose,
  not dimensions.
- Find a trustworthy scale reference in the same plane as the feature: a ruler,
  caliper, known fastener, or other supplied dimension. A reference on the table
  does not directly scale a feature raised above it.
- Perspective scale varies approximately with
  `camera distance / (camera distance - feature height)`. Correct for parallax
  when the camera geometry is known; otherwise request one caliper reading of
  the largest, flattest important part and scale other dimensions from it.
- Carry scale between images only through a feature visible in both. Record that
  chain. If two images disagree materially, investigate perspective,
  foreshortening, shadows, cropping, or a different part variant instead of
  silently averaging them.

## Measurements and provenance

Use repeatable overlays or image-analysis tools when they improve the reading:
grids for coordinates, edge profiles for ruler ticks, and color segmentation for
distinct components. Shadows and highlights often corrupt bounding boxes, so
check diameters or widths on representative cross-sections as well as masks.

Counts, pitches, hole patterns, and repeated spacing are often more reliable
than outer silhouettes. Use the highest-resolution view that shows the feature.
Record one row per reading:

```text
source | feature | pixel endpoints/count | scale | resolved value | units | uncertainty | note
```

Distinguish `observed`, `derived`, `assumed`, and `unknown`. Preserve competing
readings until the conflict is resolved.

## One dimension table, separate model files

Keep shared dimensions and topology decisions in one tracked Python module:
overall dimensions, hole coordinates, feature counts, interfaces, and any
scale factor. A corrected measurement should flow into every affected drawing
and solid without copying a second table.
Resolve externally maintained data before building, as described in
[cad-as-config.md](cad-as-config.md).

Each artifact still follows the current model contract. Put the drawing in a
parameterless `@dxf` model file and the solid or assembly in a parameterless
`@step` model file; both may call ordinary factories using the shared values.
Run those scripts to produce documents. Pass the resulting `.dxf` or `.step`
documents, never the Python source, to cadgen inspection and snapshot commands.
Use the `$dxf` skill for drawing-sheet conventions. Its `@dxf` models generate
profile geometry; semantic dimensions and title blocks require a separate
document-authoring workflow. Keep that review sheet separate from CAM exports.

## Drawings before detailed solids

Review orthographic views and useful sections next to the source images. This
forces early decisions about mirrored views, feature counts, tapers, bores,
ribs, and other geometry that a single render may hide. Mark every inferred or
unknown feature on the review record; a clean drawing does not prove an unseen
interior.

Model the best-supported pose. Use source-level joints or declared kinematics
for additional supported states instead of inventing an unphotographed
mechanism. Preserve imported component frames and derive mating datums from
inspected geometry.

## Review and verification

Keep four questions separate:

- Does the model resemble the photographs from comparable viewpoints?
- Do the drawings match the dimension table and show required hidden geometry?
- Are mechanism, fastener, and interface assumptions supported or clearly
  labeled?
- Can another person reproduce the measurements from the recorded sources?

For a multipart reconstruction, assign independent reviewers these questions
with the actual image paths and outputs. Each reviewer must inspect the images
and distinguish visible evidence from inference. Correct the shared table first,
then rebuild affected drawings and models.

Then verify the documents. Run `refs --facts --planes --positioning` and
`validate` on each STEP. For an assembly, run `interfere` on the intended part
scope and each required static state. Confirm `ok`, `complete`, `conclusive`,
`errors`, and pair statistics; no visible clash is not proof that hidden parts
clear one another. Add targeted measurements for bores, fasteners, mating
interfaces, and motion envelopes.

When no reliable scale exists or perspective dominates, ask for one concrete
measurement: the largest, flattest functionally important part. Continue other
work under stated assumptions, but leave affected dimensions and fit checks
`INCOMPLETE` until scale is resolved.
