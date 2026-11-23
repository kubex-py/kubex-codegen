"""CLI entry point for the kubex code generator.

Each Kubernetes version's models live in their own repository (kubex-py/k8s-1.NN),
whose root is the `kubex-k8s-1-NN` package. From that root:

    kubex-codegen regenerate --k8s-version 1.35 --package-dir .

downloads the latest 1.35.x OpenAPI spec and regenerates the models in place.
The repository's pyproject.toml and LICENSE are hand-written and left alone.
`generate` does the same from a spec already on disk:

    kubex-codegen generate \\
        --swagger ./openapi/1.35/swagger.json \\
        --v3-dir  ./openapi/1.35/v3 \\
        --k8s-version 1.35 \\
        --package-dir .
"""

from __future__ import annotations

import importlib.metadata
import re
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer

from kubex_codegen import model_emitter, resource_detector, spec_loader
from kubex_codegen.package_builder import RenderInputs, ruff_command, write_package

app = typer.Typer(
    add_completion=False,
    help="Generate and verify kubex-k8s-<version> resource packages.",
    no_args_is_help=True,
)

_K8S_VERSION = re.compile(r"^\d+\.\d+$")

PackageDir = Annotated[
    Path,
    typer.Option(
        help="Root of the package to write: the version repository's root, "
        "e.g. '.'. Its kubex/k8s/v1_NN tree is rewritten; pyproject.toml and "
        "LICENSE are left alone."
    ),
]


def _print_version(value: bool) -> None:
    if value:
        typer.echo(importlib.metadata.version("kubex-codegen"))
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_print_version,
            is_eager=True,
            help="Print the kubex-codegen version and exit.",
        ),
    ] = False,
) -> None:
    """Generate and verify kubex-k8s-<version> resource packages."""


def _version_tag(k8s_version: str) -> str:
    """`1.30` -> `v1_30`."""
    return "v" + k8s_version.replace(".", "_")


def _check_k8s_version(k8s_version: str) -> None:
    if not _K8S_VERSION.match(k8s_version):
        msg = f'Expected a Kubernetes minor version such as "1.35", got {k8s_version!r}'
        raise ValueError(msg)


def run_generate(
    swagger: Path,
    k8s_version: str,
    *,
    package_dir: Path,
    v3_dir: Path | None = None,
    only_groups: str | None = None,
    format: bool = True,
) -> Path:
    """Generate a kubex-k8s-* package from a swagger.json into `package_dir`.

    Returns the path to the generated package root directory.
    """
    _check_k8s_version(k8s_version)
    spec = spec_loader.load_swagger(swagger)
    if v3_dir is not None:
        spec_loader.merge_v3_supplement(spec, v3_dir)

    resources = resource_detector.detect_resources(spec.definitions, spec.paths)
    if only_groups:
        wanted = {g.strip() for g in only_groups.split(",") if g.strip()}
        resources = [r for r in resources if r.group in wanted]
        if not resources:
            msg = f"No resources matched --only-groups={only_groups}"
            raise ValueError(msg)

    k8s_version_tag = _version_tag(k8s_version)
    build = model_emitter.build_modules(
        k8s_version_tag=k8s_version_tag,
        definitions=spec.definitions,
        resources=resources,
    )
    pkg_root = write_package(
        RenderInputs(
            package_root=package_dir,
            k8s_version=k8s_version,
            k8s_version_tag=k8s_version_tag,
            modules=build.modules,
            shared_enums=build.shared_enums,
            clean=only_groups is None,
        )
    )
    typer.echo(f"Wrote generated package to {pkg_root}")

    if format:
        subprocess.run(ruff_command("format", str(pkg_root)), check=False)

    return pkg_root


@app.command()
def generate(
    swagger: Annotated[Path, typer.Option(help="Path to swagger.json")],
    k8s_version: Annotated[str, typer.Option(help='Kubernetes version, e.g. "1.35"')],
    package_dir: PackageDir,
    v3_dir: Annotated[
        Path | None,
        typer.Option(help="Optional directory of v3 per-group files"),
    ] = None,
    only_groups: Annotated[
        str | None,
        typer.Option(help='Comma-separated groups to emit (e.g. "core,apps")'),
    ] = None,
    format: Annotated[
        bool,
        typer.Option(
            "--format/--no-format",
            help="Run ruff format on the output (default: on).",
        ),
    ] = True,
) -> None:
    """Generate a kubex-k8s-* package from a swagger.json."""
    try:
        run_generate(
            swagger,
            k8s_version,
            package_dir=package_dir,
            v3_dir=v3_dir,
            only_groups=only_groups,
            format=format,
        )
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


def run_verify(package: Path) -> int:
    """Run ruff and mypy against a generated package.

    mypy runs in this interpreter's environment, so pydantic and kubex-core
    must be installed next to kubex-codegen (as they are when it runs with
    `uv run --with` from a version repository).

    Returns 0 on success, non-zero on failure.
    """
    rc = 0
    for cmd in (
        ruff_command("check", str(package)),
        ruff_command("format", "--check", str(package)),
    ):
        typer.echo(f"$ {' '.join(cmd)}")
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            rc = result.returncode
    # `kubex/` below is a relative path, so it only resolves to the generated
    # package's own kubex.k8s.* tree when mypy's cwd is the package directory.
    mypy_cmd = [
        sys.executable,
        "-m",
        "mypy",
        "--strict",
        "--namespace-packages",
        "--explicit-package-bases",
        "kubex/",
    ]
    typer.echo(f"$ (cd {package}) {' '.join(mypy_cmd)}")
    result = subprocess.run(mypy_cmd, check=False, cwd=str(package))
    if result.returncode != 0:
        rc = result.returncode
    return rc


@app.command()
def verify(
    package: Annotated[Path, typer.Argument(help="Path to a kubex-k8s-* package root")],
) -> None:
    """Run ruff and mypy against a generated package."""
    raise typer.Exit(code=run_verify(package))


@app.command()
def regenerate(
    k8s_version: Annotated[
        str, typer.Option(help='Kubernetes minor version, e.g. "1.35"')
    ],
    package_dir: PackageDir,
    cache_dir: Annotated[Path, typer.Option(help="Directory for cached specs")] = Path(
        ".cache/schemas"
    ),
    do_verify: Annotated[
        bool,
        typer.Option(
            "--verify/--no-verify",
            help="Run ruff/mypy verification after generation (default: on).",
        ),
    ] = True,
) -> None:
    """Download the latest patch release's OpenAPI spec and regenerate the package."""
    from kubex_codegen.fetch_specs import download_specs, resolve_latest_release

    try:
        _check_k8s_version(k8s_version)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    try:
        typer.echo(f"Resolving the latest release of Kubernetes {k8s_version}...")
        tag = resolve_latest_release(k8s_version)
        typer.echo(f"Resolved {k8s_version} -> {tag}")
        specs = download_specs(tag, cache_dir)
    except Exception as exc:
        typer.echo(f"Fetch failed for {k8s_version}: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    try:
        pkg_root = run_generate(
            specs.swagger_path,
            k8s_version,
            package_dir=package_dir,
            v3_dir=specs.v3_dir,
        )
    except Exception as exc:
        typer.echo(f"Generation failed for {k8s_version}: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if do_verify:
        typer.echo(f"Verifying the package for Kubernetes {k8s_version}...")
        rc = run_verify(pkg_root)
        if rc != 0:
            typer.echo(f"Verify failed for {k8s_version} (exit code {rc})", err=True)
            raise typer.Exit(code=1)

    typer.echo(f"Regenerated Kubernetes {k8s_version} ({tag}) in {pkg_root}")


if __name__ == "__main__":
    app()
