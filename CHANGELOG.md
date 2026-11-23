# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Releases are git tags; the version repositories (kubex-py/k8s-1.NN) pin one.

## [Unreleased]

The first release as a standalone tool. Until now the generator lived in kubex's workspace as
`scripts/codegen`; its history came along.

### Changed

- The package is `kubex_codegen`, installed with a `kubex-codegen` command (was
  `python -m scripts.codegen`).
- `generate` and `regenerate` write into `--package-dir`, the package root (a version
  repository's root), instead of `<--output>/kubex-k8s-1-NN`. The option is required, so the
  generator never writes into the current directory by default.
- `regenerate` handles one version, `--k8s-version 1.35`, instead of `--versions 1.35,1.36`.
- Ruff and mypy run from kubex-codegen's own environment (`python -m ruff`, `python -m mypy`)
  instead of `uv run`. Ruff runs with `--isolated` and fixed settings (`target-version = "py311"`,
  `kubex` and `kubex_core` first-party), so the output no longer depends on the ruff
  configuration around the package. The generated models are unchanged.
- The generated `pyproject.toml` is ready for a standalone version repository: project URLs
  for `kubex-py/k8s-1.NN`, a dev group pinning the ruff and mypy versions kubex-codegen uses,
  strict mypy, and the ruff settings the models are formatted with. The workspace-only
  `[tool.ty.environment]` is gone.

### Added

- `kubex-codegen --version`.
- The LICENSE copied into generated packages ships with the tool.
