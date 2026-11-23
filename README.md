# kubex-codegen

[![CI](https://github.com/kubex-py/kubex-codegen/actions/workflows/ci.yaml/badge.svg)](https://github.com/kubex-py/kubex-codegen/actions/workflows/ci.yaml)

Generates the `kubex-k8s-1-NN` packages, Pydantic v2 models for each Kubernetes version, from the
official OpenAPI spec. The models build on [kubex-core](https://github.com/kubex-py/kubex-core) and
are used by the [kubex](https://github.com/kubex-py/kubex) client.

Each Kubernetes version's package lives in its own repository, `kubex-py/k8s-1.NN`, and pins a
kubex-codegen release. kubex-codegen is released as git tags, not on PyPI.

## Regenerating a version repository

From the root of a version repository:

```bash
uv run --with "kubex-codegen @ git+https://github.com/kubex-py/kubex-codegen@v0.1.0" \
    kubex-codegen regenerate --k8s-version 1.35 --package-dir .
```

This resolves the latest 1.35.x release, downloads its OpenAPI spec (cached in `.cache/schemas`),
rewrites `kubex/k8s/v1_35/` and `LICENSE`, and verifies the result with ruff and strict mypy. The
repository's `pyproject.toml` (name, version, dependencies, tool settings) is written by hand and
left alone. GitHub API calls use `GITHUB_TOKEN`, or `gh auth token` when it isn't set.

`uv run --with` installs kubex-codegen into the version repository's environment, so `verify`'s
mypy sees pydantic and kubex-core. With `--no-verify`, any environment works.

## Commands

| Command | What it does |
|---|---|
| `kubex-codegen regenerate --k8s-version 1.35 --package-dir DIR` | Fetch the latest spec for a minor version and regenerate the package in `DIR` |
| `kubex-codegen generate --swagger swagger.json [--v3-dir v3/] --k8s-version 1.35 --package-dir DIR` | Generate from a spec on disk; `--only-groups core,apps` regenerates only some API groups |
| `kubex-codegen verify DIR` | Run ruff and strict mypy against a generated package |
| `kubex-codegen --version` | Print the version |

## Reproducible output

The generated code is formatted with ruff, which kubex-codegen pins along with mypy, and ruff runs
with `--isolated` and fixed settings. A given kubex-codegen release therefore produces the same
package wherever it runs.

For the version repository's own CI to check the models the way they were generated, its
`pyproject.toml` should pin the same ruff and mypy versions and use the same ruff settings:

```toml
[tool.ruff]
target-version = "py311"

[tool.ruff.lint.isort]
known-first-party = ["kubex", "kubex_core"]
```

## Development

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy kubex_codegen tests
```

`tests/test_golden_snapshot.py` compares the output for `tests/fixtures/mini_swagger.json` with the
package checked in under `tests/golden/`. When the output changes on purpose, regenerate it and
review the diff:

```bash
uv run kubex-codegen generate --swagger tests/fixtures/mini_swagger.json --k8s-version 1.30 \
    --package-dir tests/golden/kubex-k8s-1-30
```

## Releasing

Bump `version` in `pyproject.toml`, update `CHANGELOG.md`, merge, then push a `vX.Y.Z` tag on
`main`. The release workflow checks that the tag matches the version and creates the GitHub
release. Version repositories then move their pin to the new tag.
