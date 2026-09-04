# CAD-as-config A/B evaluation

**Modeling accuracy tied in this pilot. Verification reliability improved in the checker fault tests.**

## Geometry results

| Execution | Task | Existing skill / direct parameters | CAD-as-config | Result |
|---|---|---:|---:|---|
| Independent agents + benchmark tools | Enclosure | 197/197 | 197/197 | Tie |
| Independent agents + benchmark tools | Mounting fixture | 94/94 | 94/94 | Tie |
| Coordinator-authored models | Enclosure | 197/197 | 197/197 | Tie |
| Coordinator-authored models | Mounting fixture | 94/94 | 94/94 | Tie |

Each task includes nominal and wider variants, separately spawned builds and a nominal → wide → nominal sequence in one process. The grader reimports fresh STEP exports and verifies the submitted STEP files match. Assertions check labels, positive valid solids, specified bounds/datums, holes and remaining material, exact insert profile, board preservation/seat, lip clearance, connector opening, and zero positive-volume collisions. Linear tolerance: 0.015 mm. Boolean residual tolerance: 0.025 mm³. The 197/94 checks include repeated assertions, not 197/94 independent trials.

All eight unchanged models passed. The fixture uses 0.2 mm radial clearance; the enclosure uses 0.3 mm lip clearance per side. No gain in geometry pass rate was demonstrated. The direct A/B intentionally shares construction mathematics, isolating external configuration and checks; it is unblinded and does not independently measure skill efficacy.

## Tools actually used

- The GitHub-owned autoresearch workflow from `bengreen927/claude-config/skills/autoresearch/SKILL.md`, verified blob `82b62d4168e6777fc02d68555edd36db6076805d`, supplies the bounded baseline/challenger contract, frozen protocol, and `results.tsv`. It is a workflow skill, not a standalone CAD benchmark executable.
- The installed skill-creator `scripts/aggregate_benchmark.py` and `eval-viewer/generate_review.py` generated both benchmark summaries and both interactive review files. They ran locally, not in GitHub Actions. Missing token metrics were removed from the displayed benchmark rather than presenting the aggregator's default zero as a measurement; raw output is preserved separately.
- Four isolated GPT-6 agent runs generated the tool-driven candidates from arm-specific snapshots without grader access. Stock = drawings-first skill at `50dbeb23`; challenger = frozen CAD-as-config draft. Same model, briefs, runtime, requested artifacts, and bounded instructions.
- The coordinator generated the other four candidates directly. A uses a parameter dict; B reads JSON config and executes explicit validity/interference checks.
- An independent grader was authored without reading candidate outputs. Its controls cover nominal/wide examples, known wrong geometry, corrupt/missing/stale exports, nested transformations, nonfinite values, and retained state.

Runtime: Python 3.12.13, build123d 0.11.1, cadgen 0.4.28, cadquery-ocp 7.9.3.1.1, ezdxf 1.4.4. Agent wall times were self-recorded and varied roughly 148–197 seconds. These are not controlled speed measurements; token/cost totals were unavailable. The historical interrupted Claude runs are excluded.

## Grader correction, preserved in the record

Grader v1 initially scored the challenger enclosure 191/197. It counted four permitted R1 cavity corners as four extra supports. This contradicted its own rule permitting square through R1 inner corners. V2 removes the allowed wall envelope before counting supports. Independent square and R1 controls pass and wrong geometry still fails. Every candidate was rerun unchanged. `grader-v1/`, `grader-amendment.md`, and both hashes retain the audit trail; this is a corrected grader result, not a repaired challenger.

## Verification code A/B

| Identical fault | Old checker | Corrected checker |
|---|---|---|
| Candidate pairs left untested | Success | Incomplete |
| Boolean operation failed | Success | Incomplete, pair error |
| Nonfinite measured volume | Success | Incomplete, measurement error |
| Real 500 mm³ collision | Collision | Collision, complete measurement |

The correction also distinguishes empty selection from a legitimate single part and keeps measured clashes visible in text output alongside errors. Twenty-four focused runtime/CLI tests and two skill-containment checks pass. The development bundle freshness check passes. These demonstrate specific reliability improvements, not universal geometric accuracy.

## Adoption decision

Keep shared dimensions, explicit frames, fixed visual review, STEP round trips, and required checks. Adopt the collision-checker correction. Replace the oversized draft helper with concise guidance: it had fail-open checks, incomplete manifest identity and a cylindrical-face matcher that could mistake a boss for a hole. Required failures remain blocking. Process-specific DFM examples stay scoped to their process/material/supplier.

The final reference was revised after testing the frozen draft, so the exact final instruction text has not been rerun as an agent treatment. Two task pairs are insufficient to establish statistical superiority, and both stock runs reached the score ceiling. The result supports selective adoption of verified safeguards, not a claim that more configuration makes the model more accurate. No claim of better photo reconstruction, complex mechanism fidelity, manufacturing readiness or clinical suitability follows from these generic fixtures.

## Artifacts

- `tool-review.html`: independent-agent outputs and benchmark.
- `direct-review.html`: coordinator outputs and benchmark.
- `models/review/`: eight nominal STEP files and fixed diagnostic snapshots.
- `tool/`, `direct/`: original sources, both STEP variants, checks and reports.
- `reference/`: full article Markdown and its MIT license, source provenance.
- `checker-ab.json`, `frozen-inputs.json`, `environment.json`, `results.tsv`: evidence.

The shared text-to-cad development branch contains generic replay sources, grader, protocol, findings, and runtime tests. Private product assets remain outside that repo.

Generic replay: `models/evaluations/cad-as-config/README.md`. Local-only HTML, snapshots, and full source archive referenced above are not committed.
