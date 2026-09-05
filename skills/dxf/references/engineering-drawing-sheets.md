# Engineering drawing sheets

Read this reference for dimensioned drawings with views, dimensions, notes,
tables, and a title block. Keep review sheets separate from cut layouts.

## Authoring boundary

The current parameterless `@dxf` model returns build123d geometry in XY, either
a bare shape or a mapping of layer names to shapes. The engine writes the DXF.
See [generator-templates.md](generator-templates.md) for supported examples.
`bd.Text` produces engraved outlines; it does not create DXF dimension entities,
dimension styles, title blocks, or paper-space layouts.

Use a separate document-authoring workflow when those sheet features are
required, reusing the same resolved dimensions as the CAD model. Give the sheet
its own output path so it cannot overwrite the model's generated DXF. Existing
dimensioned DXF documents can be inspected in the CAD Viewer and checked with
the post-hoc validation described in [SKILL.md](../SKILL.md).

The fork's old ezdxf generator, dimension-style mutations, and plotting snippets
are intentionally omitted: their document-return contract is incompatible with
`@dxf`, and their library-specific settings are not a supported cadgen sheet API.
Verify settings against the document-authoring tool actually selected.

## Shared dimensions and views

- Reuse one dimension table for drawings and solids. Use tracked Python values
  for cadgen models; resolve external JSON/YAML into those values before building.
- Label orientation, projection convention, section/detail identifiers, and view
  scales. Show the same assembly state in every view.
- Include the views and sections needed to explain holes, bores, ribs, interfaces,
  and hidden geometry. Distinguish measured, derived, and inferred dimensions.
- Dimension from geometry or the shared table. Enlarged details must display true
  part dimensions, with the enlargement identified separately.

## Sheet quality

Use the requested sheet size. An A3 landscape sheet is 420 × 297 mm; a 10 mm
margin is a useful starting layout, not a mandatory drafting standard. Include
title, drawing number, units, scale, revision, sheet count, author/date, and the
applicable tolerance convention. Add materials, fasteners, or hole tables when
needed, using project-specific values and sources.

Separate visible profiles, hidden lines, centerlines, dimensions, and notes by
intent. Use reference-named layers for open construction geometry; keep CAM cut
profiles closed. Confirm hidden/center linetypes exist and render distinctly at
the final scale. A clean validation result alone does not establish sheet quality.

Keep dimension stacks, view labels, notes, and the title block clear of one
another. As initial spacing, allow roughly 8 mm between stacked dimensions and
20 mm around adjacent views or the title block, then inspect the actual output.
Choose decimal precision from measurement confidence and tolerances. Verify
displayed dimension values, units, and rounding against the underlying geometry.

## Export and review

Fix the intended page size and print palette explicitly. Auto-fitting geometry
can silently change scale. For PDF delivery, check physical page dimensions
(for example with `pdfinfo`), render every page, and inspect at intended print
size. Confirm a known length at the declared scale and avoid print-to-fit scaling.

Before handoff, check missing or overlapping dimensions, clipped text, readable
line styles, centerlines, consistent repeated values, view states, materials and
fasteners, and measurement provenance. Report geometric validation, sheet review,
and any unresolved dimensions separately. A plausible sheet does not verify an
unseen mechanism or establish manufacturing readiness.
