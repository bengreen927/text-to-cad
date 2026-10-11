# Sheet review

Use this checklist after `cadgen.eng_drawing` writes a sheet, and when a
drawing must stay consistent with photo-derived or shared dimensions. The
[sheet API](sheet-api.md) defines what the sheet can contain; this file covers
review. A sheet that renders without error is not a reviewed sheet.

## Shared dimensions and views

- Reuse one dimension table for drawings and solids, imported by both the
  drawing script and the models.
- Label orientation, projection convention, section/detail identifiers, and view
  scales. Show the same assembly state in every view.
- Include the views needed to explain holes, bores, ribs, interfaces, and hidden
  geometry. The sheet API has no section or detail views yet; say what the
  views do not show. Distinguish measured, derived, and inferred dimensions.
- Dimension from geometry or the shared table. Enlarged details must display true
  part dimensions, with the enlargement identified separately.

## Sheet quality

Use the requested sheet size. An A3 landscape sheet is 420 × 297 mm; a 10 mm
margin is a useful starting layout, not a mandatory drafting standard. Include
title, drawing number, units, scale, revision, sheet count, author/date, and the
applicable tolerance convention. Add materials, fasteners, or hole tables when
needed, using project-specific values and sources.

Confirm that visible, hidden, center, dimension, and note line work render
distinctly at the final scale. A clean run alone does not establish sheet
quality.

Keep dimension stacks, view labels, notes, and the title block clear of one
another. As initial spacing, allow roughly 8 mm between stacked dimensions and
20 mm around adjacent views or the title block, then inspect the actual output.
Choose decimal precision from measurement confidence and tolerances. Verify
displayed dimension values, units, and rounding against the underlying geometry.

## Export and review

Fix the intended sheet size and scale explicitly. Check physical page dimensions
(for example with `pdfinfo`), render every page, and inspect at intended print
size. Confirm a known length at the declared scale and avoid print-to-fit scaling.

Before handoff, check missing or overlapping dimensions, clipped text, readable
line styles, centerlines, consistent repeated values, view states, materials and
fasteners, and measurement provenance. Report geometric validation, sheet review,
and any unresolved dimensions separately. A plausible sheet does not verify an
unseen mechanism or establish manufacturing readiness.
