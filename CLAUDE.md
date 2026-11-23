# kubex-codegen

Generates the `kubex-k8s-1-NN` packages (Pydantic v2 models per Kubernetes version) from the
Kubernetes OpenAPI spec. Split out of kubex's workspace (`scripts/codegen`) with its history. Each
version's package lives in its own repository, `kubex-py/k8s-1.NN`, which pins a kubex-codegen
git tag. kubex-codegen is not published to PyPI.

## Layout

- `kubex_codegen/__main__.py`: the typer CLI (`kubex-codegen`): `generate`, `regenerate`, `verify`
- `spec_loader` → `resource_detector` → `model_emitter` (with `ref_resolver`, `type_mapper`,
  `naming`, `enum_emitter`, `imports`, `ir`) → `package_builder` renders through Jinja
  (`templates/`) and writes the package
- `fetch_specs`: resolves the latest patch release and downloads swagger.json plus the v3 files
- The generated package is `kubex/k8s/v1_NN/` (and a README when missing). Each version
  repository's `pyproject.toml` and `LICENSE` are hand-written; the generator never touches them.

## Commands

- `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`,
  `uv run mypy kubex_codegen tests`
- `uv.lock` is committed; CI syncs with `--locked`.

## Rules

- The output must be reproducible. Ruff (pinned in `pyproject.toml`) runs through
  `package_builder.ruff_command`, with `--isolated` and the settings in `RUFF_TARGET_VERSION` /
  `RUFF_KNOWN_FIRST_PARTY`. Version repositories must use the same settings and ruff version in
  their pyproject.toml. Changing either, or bumping ruff, can change every generated file.
- `tests/golden/` is the snapshot of the output for `tests/fixtures/mini_swagger.json`. Any change
  to it must be intentional; regenerate it with the command in the README and review the diff.
- `--package-dir` is required on purpose: generating replaces `kubex/k8s/v1_NN/` in that directory.
- Releases are git tags (`vX.Y.Z`) matching `version` in pyproject.toml (checked by
  `.github/workflows/release.yaml`). Workflow files are named `.yaml`.
