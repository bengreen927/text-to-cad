# CAD-as-config: source analysis and adoption decisions

Source: [Mason Hensley, CAD as Config, August 18 2026](https://gwaihirrobotics.com/blog/2026-08-cad-as-config), [author repository](https://github.com/Gwaihir-Robotics/CAD_as_Code). Full published Markdown was read from the author repository; canonical web retrieval was unavailable during review. The local reference archive records source commit and SHA-256. All nine sections and code blocks were covered.

| Section | Recommendation | Decision for this fork |
|---|---|---|
|1: premise|Constrained, decomposed geometry tasks|Adopt measurable per-part acceptance criteria; do not promise autonomous machine design.|
|2: config-as-code|Config, generator, outputs, verification loop|Adopt within existing build123d/cadgen architecture.|
|3: four stator generators|Share config across part families and 2D/3D outputs|Adopt schema validation, derived dimensions, namespaced additions, idempotent writers. Retain existing Python config support; no YAML mandate.|
|4: machine plates|Use vendor geometry and explicit frames|Adopt subject to the user's source restrictions; validate full envelopes beyond sampled silhouettes.|
|5: working with agents|Checks, screenshots, DFM, schema extension|Adopt scripted checks and fixed visual views. Scope DFM numbers to process/material/supplier; the author's numerical examples are not universal.|
|6: repository hygiene|Headless regeneration, manifests, curated exports|Adopt source-controlled regeneration commands and input/output hashes. Fix config-only identity: generator, helpers, vendor geometry, options and dependency versions also matter.|
|7: failure stories|Offsets, STEP round trips, visible headless saves, repeat-safe writes, composed transforms|Adopt round-trip checks, explicit errors and repeatability. FreeCAD GUI XML is backend-specific and is not installed into build123d.|
|8: limits|Tolerance stacks, constraints, aesthetics and novelty remain limited|State limits explicitly. Keep this repo's existing joints; no downgrade to placement-only assembly support.|
|9: distribution|Reusable skill and examples|Add generic reference plus generic comparison fixtures. Keep private product evidence outside the skills repo.|

## Review corrections

The initial adaptation contained an unvalidated helper that could report PASS for empty checks, failed advisories, or consumed iterators. Its hole matcher could mistake a cylindrical boss for a through-hole, and its revision key omitted generator dependencies. That helper is not adopted. The revised reference specifies complete evidence and required-check semantics instead.

The existing interference runtime silently skipped Boolean/measurement failures and could return success after truncation. The implementation change makes those outcomes incomplete/error, covered by focused regression tests. Nominally valid CAD can still have wrong interfaces or inferred mechanisms; zero collision count is not a blanket approval.

## Evaluation

See the comparison report in this folder when generated. Stock is the pre-CAD-as-config drawings-first skill (50dbeb23); challenger is the frozen draft. Independent agents and coordinator-authored models receive the same two briefs with nominal and wide variants. The coordinator comparison is an unblinded implementation ablation, and the two independent task pairs are a pilot, not a statistical efficacy study. The final reference includes review corrections after the frozen draft: its exact revised text has not been rerun as an agent treatment.
