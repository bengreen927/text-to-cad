# CAD-as-config pilot reproduction

These are generic synthetic enclosure/fixture candidates, not product reverse-engineering assets.

Use a Python 3.12 environment with build123d 0.11.1 (the test kernel was cadquery-ocp 7.9.3.1.1). Run `python3 reproduce.py` from this folder. It generates the PCB input, all eight candidate pairs of nominal/wide STEP exports, then runs the same geometric grader. Generated artifacts stay local. To validate the grader itself, run `python3 make_inputs.py` and `python3 grader-smoke/check.py`; repeat with `GRADER_SMOKE_CAVITY_RADIUS=1`.

`tool/` candidates were written by four isolated GPT-6 agent runs using old/new instruction snapshots. `direct/` candidates were written by the coordinator; shared construction mathematics intentionally isolate config loading/check overhead and are not independent blind trials. Only input paths were made relative for portability. Models have the benchmark interface `gen_step(variant=...)`; the current cadgen CLI expects no-argument entry points, so use direct export here or wrappers.

The stock instruction baseline is the drawings-first branch at 50dbeb23. The new instruction was an uncommitted frozen draft, evaluated before review corrections. Instructions and input hashes, source coverage, and final results are summarized in `docs/research/cad-as-config-evaluation.md` at repository root. This reproducer re-evaluates geometry; it does not rerun generative agents or establish statistical efficacy. Full original snapshots and audit logs were retained in the local evaluation workspace.

The scorer uses independent analytic geometry, imported STEP round trips, required passages/material, clearances, and repeated calls. Checks repeat across isolated and in-process executions; check totals are not independent sample counts. Grader v1 miscounted allowed rounded cavity corners as supports; v2 corrects that for every candidate. See `grader-amendment.md`.
