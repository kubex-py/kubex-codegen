# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Releases are git tags; the version repositories (kubex-py/k8s-1.NN) pin one.

## [Unreleased]

## [0.2.0] - 2026-11-23

### Removed

- **Breaking:** kubex-codegen no longer writes the package's `pyproject.toml`, and
  `--package-version` is gone with it. Each version repository keeps a hand-written
  `pyproject.toml` with the package's version, dependencies and tool settings; it should pin the
  ruff and mypy versions kubex-codegen uses and match its ruff settings (see the README).
- **Breaking:** kubex-codegen no longer copies a `LICENSE` into the package; each version
  repository keeps its own.
- The `packaging` dependency.

## [0.1.0] - 2026-11-23

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

[unreleased]: https://github.com/kubex-py/kubex-codegen/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/kubex-py/kubex-codegen/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kubex-py/kubex-codegen/releases/tag/v0.1.0
