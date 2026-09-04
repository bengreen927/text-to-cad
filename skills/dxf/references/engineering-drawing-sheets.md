# Dimensioned engineering drawing sheets with ezdxf

Read this file when the deliverable is a dimensioned drawing (title block, views, dimensions, notes,
tables) rather than a cut layout. The generator is still a `<name>.dxf.py` with `gen_dxf()`; the
validator switches to drawing mode automatically when the document contains DIMENSION entities, so
closed-profile checks on cut layers are relaxed. These are the settings and patterns that took several
rounds to get right.

## Layers

Layer intent is decided by whole tokens of the layer name. Use `PROFILE_VISIBLE` for visible outlines
(closed polylines, circles, arcs), and `REFERENCE_*` layers (`REFERENCE_DIM`, `REFERENCE_HIDDEN`,
`REFERENCE_CENTER`, `REFERENCE_TEXT`, `REFERENCE_TITLE`, `REFERENCE_HATCH`) for everything open:
dimensions, leaders, hidden lines, centerlines, text, borders, hatching. A layer named with the token
`cut` or `profile` must hold closed geometry when the file is a cut layout.

## Linetypes

`ezdxf.new("R2010", setup=True)` creates `CENTER` and `DASHED` but NOT `HIDDEN`. A layer that names a
missing linetype renders solid without any error. Add it and set the scale:

```python
doc.header["$LTSCALE"] = 0.5
if "HIDDEN" not in doc.linetypes:
    doc.linetypes.add("HIDDEN", pattern=[9.525, 6.35, -3.175], description="Hidden __ __ __ __")
```

## Dimension style

Duplicate the bundled `EZDXF` style and correct three things: it carries `dimlfac = 100` (every
measurement reads 100x), `dimzin` controls zero suppression, and an explicit `dimrnd = 0.0` rounds to whole
units (0.0 is not "no rounding" here; leave `dimrnd` unset).

```python
st = doc.dimstyles.duplicate_entry("EZDXF", "RX")
st.dxf.dimlfac = 1.0          # measurements in drawing units
st.dxf.dimdec = 1             # one decimal
st.dxf.dimzin = 0             # keep the decimal (8 suppresses trailing zeros; it does not round 103.6 to 104)
st.dxf.dimdsep = ord(".")
st.dxf.dimtxt = 2.5; st.dxf.dimasz = 2.0; st.dxf.dimexo = 1.0; st.dxf.dimexe = 1.5
st.dxf.dimtad = 1; st.dxf.dimgap = 0.8; st.dxf.dimtih = 0; st.dxf.dimtoh = 0
# do NOT set st.dxf.dimrnd
```

Create dimensions with `add_linear_dim(...).render()`, `add_diameter_dim`, `add_radius_dim`; pass
`text="<> LABEL"` to append a label to the measured value. For a detail drawn at 2:1 or 3:1, override
the text with the true value (`text=f"{value}"`) so the sheet never shows a scaled number.

## Sheet framework

Draw the sheet 1:1 in modelspace: an A3 landscape border (420 x 297 mm, 10 mm margin) and a title
block with product, title, drawing number, scale, units, sheet n of m, revision, author, date and a
tolerance line. Keep a notes block in the lower left. Put helpers (border, title block, `poly`,
`rounded_rect` with bulge arcs, `hdim`/`vdim`/`ddim`/`rdim`, `leader_note`, `view_label`,
`hatch_lines`, a generic table with a `header` parameter for BOMs and hole tables) in one shared
module next to the sheet generators, and import the dimension table module rather than repeating
numbers.

Bulge arcs: `tan(theta/4)` with the sign following the arc direction around its own centre (positive
counter-clockwise). A semicircular notch entered while travelling along an edge is a clockwise arc,
so its bulge is -1.

Layout collisions are the most common defect: keep every dimension at least 8 mm from the next
stacked one, put view labels above the topmost dimension, keep views 20 mm clear of the title block
and of each other, and shorten notes to one line each (long notes run into the title block).

## PDF / PNG export (true A3, white background)

The matplotlib backend defaults to auto-fitting the figure to the geometry, which prints a 176 x 122
mm page labelled "1:1", and to a dark background. Pin the page and the palette:

```python
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

fig = plt.figure(figsize=(16.535, 11.693)); ax = fig.add_axes([0, 0, 1, 1])
cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK)
Frontend(RenderContext(doc), MatplotlibBackend(ax, adjust_figure=False), config=cfg).draw_layout(msp, finalize=False)
ax.set_xlim(0, 420); ax.set_ylim(0, 297); ax.set_aspect("equal"); ax.axis("off")
fig.savefig("sheet.pdf", facecolor="white")          # pdfinfo reports 1190.5 x 841.9 pt = A3
with PdfPages("all_sheets.pdf") as pdf: pdf.savefig(fig, facecolor="white")   # one page per sheet
```

Verify with `pdfinfo` (page size) and by reading the dimension text back from the `*D` blocks of the
DXF (`TEXT`/`MTEXT` entities) before sending a sheet out.

## Review checklist

Missing or overlapping dimensions, one decimal everywhere, hidden lines dashed, centerlines on every
hole and axis, every view labelled with its orientation, the same state (open/closed) in all views of
an assembly, the same value for the same feature on every sheet, materials and fastener sizes in a
table, and a note saying where the numbers came from (measured, photogrammetric, inferred).
