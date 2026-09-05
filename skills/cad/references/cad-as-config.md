# CAD as configuration

Use this workflow for part families, shared dimensions, assemblies with mating
interfaces, or designs expected to change repeatedly. A small standalone part
can keep named constants beside its model.

This guidance adapts Mason Hensley's
[CAD as Config](https://gwaihirrobotics.com/blog/2026-08-cad-as-config)
and its [MIT-licensed FreeCAD examples](https://github.com/Gwaihir-Robotics/CAD_as_Code)
to cadgen and build123d. The concepts are reusable; the FreeCAD-specific APIs
and shop rules are not.

## Start with a measurable design

1. Decompose an assembly into parts or coherent part families. Give each one a
   one-sentence acceptance check, then list its required dimensions, interfaces,
   and operating states.
2. State units, origin, positive axes, front face, and mating datums before
   building geometry.
3. Prefer measured geometry, dimensioned drawings, and supplied vendor STEP or
   DXF within the user's source constraints. Preserve originals and provenance.
   Photo-derived dimensions remain estimates; see
   `reverse-engineering-from-photos.md`.
4. Put shared values in one configuration and derive repeated placements from
   named datums. Let `@step` models and `@dxf` drawings read the same values.
5. Build, inspect the written documents, render fixed views, correct the source,
   and rebuild.

A configuration cannot recover a missing measurement or settle an ambiguous
mechanism. Keep observed features, inferred geometry, and unresolved decisions
separate.

## Configuration and model entry points

Use named Python constants or literal dictionaries imported from a shared module.
If users maintain JSON or YAML, validate and resolve it into that Python module
before running the models. Ordinary data-file reads are not tracked inputs in
v0.5, so changing only that file can leave a model incorrectly current. See
[step-generation.md](step-generation.md) for the freshness contract.
Validate consumed keys, units, finite values, ranges, and relationships; reject
misspelled required keys. YAML needs a real parser.
Environment variables, the working directory, time, and randomness are not
model inputs and must not silently control geometry.

Keep geometry in ordinary factories that accept explicit values. Each artifact
still has its own parameterless decorated model in a plain `.py` file:

```python
from cadgen import build123d as bd, step
from dimensions import PLATE_A


def make_plate(spec):
    return bd.Box(spec["width"], spec["depth"], spec["thickness"])


@step(out="../STEP/plate_a.step")
def plate_a():
    return make_plate(PLATE_A)


if __name__ == "__main__":
    plate_a()
```

Another configuration is another model entry point, normally in another file,
calling the same factory. Put an `@dxf` drawing in its own model file and import
the same dimensions. Run model scripts to build them. Inspection and snapshot
commands take the resulting documents; they do not run a `.py` script.

Use one model per coherent artifact. Compose assembly children by importing and
calling their model functions, preserve meaningful `AssemblyHelper`
relationships, and place children with `Pos/Rot/Location * child` or
`child.moved(loc)`. For vendor geometry, use `cadgen.read_step`, retain its
source identity, and derive project placement from inspected datums.

Keep configuration updates idempotent. When a factory or configuration loader
has stateful risk, exercise nominal, changed, then nominal values in one process
and compare the two nominal results. A repeated call must not accumulate
placements or reuse stale mutable geometry.

Manufacturing constraints must name their process, material, supplier or source,
units, and revision. Stock thicknesses and minimum features from an example shop
are examples, not universal design rules.

For a vendor-derived pocket, section or project the supplied geometry, offset by
the specified clearance, and subtract it. Verify the entire relevant envelope;
sampled sections can miss features between samples.

## Checks that can fail

Tie every required check to the acceptance sentence for its part. Passing a
short list proves only what that list measured.

| Requirement | Evidence |
| --- | --- |
| Sound geometry | Expected solid count, `inspect validate`, positive finite volume |
| Correct size and position | Bounds, named datums, and required dimensions in the stated frame |
| Pocket or through-hole | Empty passage at the intended position and full depth, plus surrounding material |
| Assembly clearance | Pairwise shared volume and measured minimum distance at every required state |
| Mating interface | Targeted `measure`, `align`, and `frame` results |
| Interchangeability | Bidirectional rotated or mirrored residual and matching functional interfaces |
| Regeneration | Nominal, changed, then nominal factory inputs yield equivalent nominal geometry |
| Unchanged unrelated geometry | A scoped `inspect diff` against the accepted document |
| Delivered document | Re-open the written STEP and repeat its critical checks and snapshot review |

A cylindrical surface is not proof of a through-hole. A zero cutter residual can
also come from a misplaced cutter. Check placement, depth, and expected
surrounding material. For nested or located assemblies, preserve world
transforms and evaluate leaf solids pairwise.

For interference, a clean claim requires `ok`, `complete`, and `conclusive` to
be true, no `errors`, and pair statistics that cover the intended parts and
states. Empty selections, failed Boolean operations, truncated pairs, invalid or
nonfinite results, and untested operating states are incomplete evidence, not
zero interference. Choose tolerances from the part scale and required
clearance; the default volume tolerance can hide a small but important clash.

Record each project-specific check with a unique name, measured value, units,
expectation, status (`PASS`, `FAIL`, or `INCOMPLETE`), and evidence. A
project-owned verifier is not a cadgen hook. Run it explicitly after building
the documents, and do not describe the model as accepted when a required check
failed or did not run. Diagnostic artifacts may be useful, but keep them marked
failed or incomplete and separate from accepted deliverables.

Checks may also run inside the decorated model body before it returns geometry,
raising on required failure. Those checks run only when the body builds; a
current model skips the body. Run the separate acceptance check before promoting
an export even after a no-op. Defining `checks()` alone never executes it.

## Reproducible review

Source-controlled configuration and model code are the source of truth;
generated documents and cadgen's store are derived. For a formal handoff, a
project may also record resolved parameters, source and input hashes, tool
versions, output hashes, full check records, and readiness status. That manifest
is project evidence, not an automatically produced cadgen guarantee.
Include configuration, model, helper and imported-input hashes in the build
identity. Record failed checks before terminating, reject empty suites and
duplicate check names, and publish the manifest atomically after accepted outputs
are complete. Distinguish byte identity from geometric equivalence of STEP files.

Compare the same fixed views and assembly states after each change. Inspect the
actual delivered STEP separately from the source model, and keep dimensional,
interference, and visual findings as different evidence types.

Nominal validity and zero static overlap do not establish tolerance stacks,
motion under load, strength, ergonomics, manufacturability, or performance.
When comparing workflows, freeze the task, inputs, runtime, instructions, and
grader; record failed and interrupted runs and preserve ties or regressions.

Product photographs, identifying details, and private measurements stay in the
owning project. Shared skills contain only generic guidance and generic fixtures.
