# Fork integration: upstream v0.5.0

This fork tracks `earthtojake/text-to-cad` while retaining generic drawings-first,
photo-measurement and configuration-driven modeling guidance. Upstream updates
are reviewed and merged through a PR; creating a GitHub fork does not synchronize
future commits automatically. Updating the repository and refreshing an installed
agent plugin are separate operations.

## 2026-09-05 migration

Base: upstream `main` at `c222e5da`, including release tag `v0.5.0`
(`95980fb6`) and subsequent dependency maintenance. Upstream moved the source
and installable tree onto `main`; future work branches from and returns to `main`.
The fork's older `develop` branch and existing local checkouts are preserved.

The prior reviewed improvements are retained from fork PR #3 (`0bda8e38`) and
the drawings-first work in PR #1. Their current instructions follow the v0.5
API: model scripts are programs using decorators, CLI inspection takes emitted
documents, and DXF models return build123d geometry. Prior experiment records
under `docs/research/` and `models/evaluations/cad-as-config/` are historical
v0.4 evidence, not v0.5 benchmarks; their old generators are not migration examples.

The incomplete-interference safeguard is adapted to the new part/intra-part
classification. Failure or truncation cannot become a no-clash pass. The
upstream ownership rules for public PyPI releases and docs deployment are
explicit in the publishing jobs, so syncing a fork does not publish upstream's
package or website.

## Installing this fork's runtime

The plugin's requirements pin the upstream release number. Additional Python
runtime fixes in this fork require installing the fork-built wheel, not just
updating the Markdown skills. From this checkout:

```sh
npm ci --prefix packages/cadgen-js
npm ci --prefix apps/viewer
scripts/bundle/bundle.sh
python -m build --wheel packages/cadgen --outdir dist
python -m pip install --force-reinstall --no-deps dist/cadgen-0.5.0-py3-none-any.whl
```

Install its dependencies first with `python -m pip install 'cadgen[snapshot]==0.5.0'`.
The wheel preserves the upstream version pin; its local wheel/commit identifies
the fork's additional fixes. No public package publication is required.

Use a separate Python environment for v0.5. The new runtime intentionally rejects
retired APIs. Existing model source is not automatically converted by syncing
the repository; retain its old environment until migrating and verifying it.
Existing STEP/DXF/GLB documents remain usable independently of their generators.

## Upgrade verification

The generic fixture in `models/evaluations/upstream-v05-smoke/` exercises STEP,
GLB, DXF, geometric validation, document facts, snapshots and unchanged rebuilds.
Targeted interference and CLI tests cover the carried patch. Version metadata,
generated bundles, shipping boundaries and both plugin manifests are also checked.
These checks establish compatibility; they do not prove improved visual fidelity.
