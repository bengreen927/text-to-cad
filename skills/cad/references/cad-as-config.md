# CAD as config

Use this workflow for part families, shared dimensions, assemblies with mating interfaces,
and repeated changes. Small single parts can keep a parameter dictionary in their generator.

Source: [CAD as Config](https://gwaihirrobotics.com/blog/2026-08-cad-as-config),
Mason Hensley, Gwaihir Robotics, August 18, 2026; accompanying
[MIT-licensed FreeCAD examples](https://github.com/Gwaihir-Robotics/CAD_as_Code).
This reference adapts the workflow to build123d; it does not require FreeCAD.

## Define a measurable task

1. Decompose an assembly into parts or part families. Give each a short acceptance
   statement, then list the dimensions, interfaces, and operating states it must satisfy.
2. State units, origin, positive axes, front face, and mating datums before building geometry.
3. Prefer measured geometry or supplied vendor STEP/DXF within the user's source constraints.
   Preserve imported originals and record provenance. Photo-derived values remain estimates.
4. Put shared values in one configuration. Generate drawings and solids from that same source.
5. Generate, verify, render fixed views, correct the source, and regenerate.

A configuration does not recover missing measurements or resolve ambiguous mechanisms.
Record observed features separately from inferred parts and unresolved decisions.

## Configuration and generators

- Choose a Python dictionary, JSON, or YAML according to the project's users. YAML requires
  a real parser; validate required consumed keys, units, finite values, ranges, and relationships.
  Permit unrelated namespaces without silently accepting misspelled required keys.
- Derive repeated dimensions and placements from shared datums. A downstream generator adds
  namespaced settings instead of copying a second table of upstream dimensions.
- Keep config updates idempotent: applying an update twice leaves the same config.
- Build a fresh shape for every call. Exercise nominal, changed, nominal configurations in
  the same process to detect stale module state and cumulative placement changes.
- Preserve component-local placements when placing imported assemblies. Distinguish composing
  a relative transform from intentionally replacing an object's absolute frame.
- Use one generator per coherent part family, composed by an assembly entry. Retain existing
  `AssemblyHelper` relationships where useful; the source article's placement-only examples
  do not replace this toolchain's joint support.
- Encode DFM constraints with their process, material, supplier, units, and source. The article's
  stock thicknesses and minimum holes are examples for its shop, not universal design rules.

For a vendor-derived pocket, section or project the supplied geometry, offset by the specified
clearance, and subtract it. Verify the complete relevant envelope: sampled sections can miss
features between samples. A nominal envelope does not establish manufacturing tolerance fit.

## Verification that can fail

Use the existing CAD inspection commands and project-specific checks. Scope checks to the
requirements; passing a list of checks proves only what those checks actually measured.

| Requirement | Evidence |
| --- | --- |
| Sound geometry | Expected solid count, validity, positive finite volume |
| Correct size and position | Bounds, datums, and specified dimensions in the stated frame |
| Pocket or through-hole | Empty passage at the intended location and full required depth, plus surrounding material and measured profile |
| Clearance | Pairwise solid intersection and minimum distance at required operating states |
| Interchangeability | Bidirectional rotated/mirrored residual plus matching functional interfaces |
| Regeneration | Nominal → changed → nominal yields equivalent geometry |
| Deliverable integrity | Export STEP, re-import it, repeat critical checks |

A cylindrical surface alone can be a boss, blind bore, or open slot; it is not proof of a hole.
A zero cutter residual also passes for a misplaced cutter. Check placement and expected material.
Empty inputs, invalid solids, nonfinite numbers, kernel errors, and untested pairs are incomplete
verification, never evidence of zero interference.

For located or nested assemblies, preserve world transforms and check leaf solids individually.
Check Boolean completion before interpreting an empty result. Calibrate dimensional and volume
tolerances to the part scale and required clearance; a default volume threshold can hide a small
but important collision.

Every verification record should contain a unique name, measured value, units, expectation,
status, and evidence. Record successful pairs as well as failures, tested-pair counts, excluded
pairs, and exclusions' scope. Bound intentional overlap by region or volume; do not blanket-ignore
a pair that could acquire a new collision elsewhere.

Keep required checks blocking. A diagnostic build may export failed geometry for inspection,
but mark it FAIL or INCOMPLETE and keep it separate from accepted deliverables. An optional
advisory must remain visible as such; a failed advisory does not count as a passed check.
Do not relax a clearance simply because the current geometry cannot satisfy it.

`inspect validate` checks shape soundness. `inspect interfere` checks shared volume. Neither
establishes function, wall thickness, fastener engagement, motion clearance, or all dimensions
without those checks being explicitly added. Check `ok`, `errors`, and coverage/truncation fields.

A project-owned `checks()` function is not a cadgen hook. Explicitly call it from
`gen_step()` before returning geometry, and raise on required failure. Alternatively, run
a separate verification command as a required step before promoting exports. Merely
defining a function does not execute it.

```python
def gen_step():
    assembly = build_assembly(CONFIG)
    verify_requirements(assembly, CONFIG)  # project function; raises on FAIL/INCOMPLETE
    return assembly
```

## Reproducible outputs

Keep the existing `<name>.step.py` / `<name>.step` conventions and CLI-owned output paths.
Follow the owning repository's layout; in this repository put model artifacts under `models/`.
A project regeneration command should rebuild the requested variants and run their checks.

A build manifest should include:

- Schema version, units, resolved parameters, and variant.
- Content hashes of config, generator, imported helpers, supplied geometry, and other inputs.
- Python, CAD library/kernel versions, dependency lock identity, and relevant build options.
- A build identity derived from all those inputs, not only the config hash.
- Output hashes, labels, geometry summaries, full check records, coverage, and readiness status.

Materialize check iterators once and reject empty suites and duplicate check names. Record
FAIL or INCOMPLETE diagnostics before terminating. Publish an accepted export set only after
all required checks pass. Write the manifest atomically after its output files are complete.
Store project-relative paths or stable input identifiers; review params and metadata for secrets
or personal paths before publishing.

Repeated STEP exports may have different timestamps or serialization while representing equivalent
geometry. Report byte identity separately from geometric equivalence. A generator-only change must
change the build identity even when config values stay the same.

## Visual review and exchange formats

Store fixed camera jobs and compare the same views and assembly states after each change.
Keep the drawing views consistent with the 3D state. Inspect source targets during iteration,
then separately re-import the delivered STEP to catch translation or serialization defects.
A stale viewer is a freshness problem to diagnose; never edit caches as the design source.

The article's FreeCAD `GuiDocument.xml` workaround applies only to native FreeCAD documents.
For build123d, verify STEP round trips and actual viewer rendering. Read local runtime APIs
before adopting kernel offset/placement recipes; retain a reproducer for a workaround.

## Limits and evaluation

Nominal solid validity and zero static overlap do not establish tolerance stacks, motion under
load, strength, ergonomics, manufacturability, or clinical performance. An inferred mechanism
can be collision-free and still be wrong.

When comparing workflows, freeze task, inputs, model/runtime, instructions, and independent grader.
Give both arms the same requirements and variants. Record failed and interrupted runs, instruction
hashes, checks, runtime, and resource cost when available. An unblinded coordinator implementation
is a useful engineering comparison but is not an independent agent trial. Preserve ties and regressions.

Product photographs, identifying details, and private measurements remain in their project.
Shared skills contain generic instructions and generic test fixtures only.
