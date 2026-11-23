from __future__ import annotations

import importlib.metadata
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from kubex_codegen.__main__ import app
from kubex_codegen.fetch_specs import DownloadedSpecs

runner = CliRunner()

# Rich colors typer's usage errors where it detects CI, splitting option names
# with escape codes.
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _plain(output: str) -> str:
    return _ANSI.sub("", output)


def _specs(tmp_path: Path, tag: str = "v1.35.4") -> DownloadedSpecs:
    return DownloadedSpecs(
        swagger_path=tmp_path / tag / "swagger.json",
        v3_dir=tmp_path / tag / "v3",
    )


@patch("kubex_codegen.__main__.run_verify")
@patch("kubex_codegen.__main__.run_generate")
@patch("kubex_codegen.fetch_specs.download_specs")
@patch("kubex_codegen.fetch_specs.resolve_latest_release")
def test_regenerate_fetches_generates_and_verifies(
    mock_resolve: MagicMock,
    mock_download: MagicMock,
    mock_generate: MagicMock,
    mock_verify: MagicMock,
    tmp_path: Path,
) -> None:
    specs = _specs(tmp_path)
    mock_resolve.return_value = "v1.35.4"
    mock_download.return_value = specs
    mock_generate.return_value = tmp_path / "repo"
    mock_verify.return_value = 0

    result = runner.invoke(
        app,
        [
            "regenerate",
            "--k8s-version",
            "1.35",
            "--package-dir",
            str(tmp_path / "repo"),
            "--cache-dir",
            str(tmp_path / "cache"),
        ],
    )

    assert result.exit_code == 0, result.output
    mock_resolve.assert_called_once_with("1.35")
    mock_download.assert_called_once_with("v1.35.4", tmp_path / "cache")
    gen_call = mock_generate.call_args
    assert gen_call.args == (specs.swagger_path, "1.35")
    assert gen_call.kwargs["v3_dir"] == specs.v3_dir
    assert gen_call.kwargs["package_dir"] == tmp_path / "repo"
    mock_verify.assert_called_once_with(tmp_path / "repo")
    assert "v1.35.4" in result.output


@patch("kubex_codegen.__main__.run_verify")
@patch("kubex_codegen.__main__.run_generate")
@patch("kubex_codegen.fetch_specs.download_specs")
@patch("kubex_codegen.fetch_specs.resolve_latest_release")
def test_regenerate_no_verify(
    mock_resolve: MagicMock,
    mock_download: MagicMock,
    mock_generate: MagicMock,
    mock_verify: MagicMock,
    tmp_path: Path,
) -> None:
    mock_resolve.return_value = "v1.35.4"
    mock_download.return_value = _specs(tmp_path)
    mock_generate.return_value = tmp_path

    result = runner.invoke(
        app,
        [
            "regenerate",
            "--k8s-version",
            "1.35",
            "--package-dir",
            str(tmp_path),
            "--no-verify",
        ],
    )

    assert result.exit_code == 0, result.output
    mock_generate.assert_called_once()
    mock_verify.assert_not_called()


def test_regenerate_requires_a_package_dir() -> None:
    # Never write a package (and its pyproject.toml) into the current
    # directory by accident.
    result = runner.invoke(app, ["regenerate", "--k8s-version", "1.35"])
    assert result.exit_code == 2
    assert "--package-dir" in _plain(result.output)


@pytest.mark.parametrize("version", ["", "1", "1.35.4", "v1.35", "1.x"])
@patch("kubex_codegen.fetch_specs.resolve_latest_release")
def test_regenerate_rejects_a_malformed_version(
    mock_resolve: MagicMock, version: str, tmp_path: Path
) -> None:
    result = runner.invoke(
        app,
        ["regenerate", "--k8s-version", version, "--package-dir", str(tmp_path)],
    )
    assert result.exit_code == 1
    assert "Kubernetes minor version" in result.output
    mock_resolve.assert_not_called()


@patch("kubex_codegen.__main__.run_verify")
@patch("kubex_codegen.__main__.run_generate")
@patch("kubex_codegen.fetch_specs.download_specs")
@patch("kubex_codegen.fetch_specs.resolve_latest_release")
def test_regenerate_fetch_failure(
    mock_resolve: MagicMock,
    mock_download: MagicMock,
    mock_generate: MagicMock,
    mock_verify: MagicMock,
    tmp_path: Path,
) -> None:
    mock_resolve.side_effect = RuntimeError("GitHub rate limited")

    result = runner.invoke(
        app,
        ["regenerate", "--k8s-version", "1.35", "--package-dir", str(tmp_path)],
    )

    assert result.exit_code == 1
    assert "Fetch failed for 1.35" in result.output
    assert "GitHub rate limited" in result.output
    mock_generate.assert_not_called()
    mock_verify.assert_not_called()


@patch("kubex_codegen.__main__.run_verify")
@patch("kubex_codegen.__main__.run_generate")
@patch("kubex_codegen.fetch_specs.download_specs")
@patch("kubex_codegen.fetch_specs.resolve_latest_release")
def test_regenerate_generate_failure(
    mock_resolve: MagicMock,
    mock_download: MagicMock,
    mock_generate: MagicMock,
    mock_verify: MagicMock,
    tmp_path: Path,
) -> None:
    mock_resolve.return_value = "v1.35.4"
    mock_download.return_value = _specs(tmp_path)
    mock_generate.side_effect = RuntimeError("codegen broke")

    result = runner.invoke(
        app,
        ["regenerate", "--k8s-version", "1.35", "--package-dir", str(tmp_path)],
    )

    assert result.exit_code == 1
    assert "Generation failed for 1.35: codegen broke" in result.output
    mock_verify.assert_not_called()


@patch("kubex_codegen.__main__.run_verify")
@patch("kubex_codegen.__main__.run_generate")
@patch("kubex_codegen.fetch_specs.download_specs")
@patch("kubex_codegen.fetch_specs.resolve_latest_release")
def test_regenerate_verify_failure(
    mock_resolve: MagicMock,
    mock_download: MagicMock,
    mock_generate: MagicMock,
    mock_verify: MagicMock,
    tmp_path: Path,
) -> None:
    mock_resolve.return_value = "v1.35.4"
    mock_download.return_value = _specs(tmp_path)
    mock_generate.return_value = tmp_path
    mock_verify.return_value = 1

    result = runner.invoke(
        app,
        ["regenerate", "--k8s-version", "1.35", "--package-dir", str(tmp_path)],
    )

    assert result.exit_code == 1
    assert "Verify failed for 1.35" in result.output


def test_generate_requires_a_package_dir(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "generate",
            "--swagger",
            str(tmp_path / "swagger.json"),
            "--k8s-version",
            "1.35",
        ],
    )
    assert result.exit_code == 2
    assert "--package-dir" in _plain(result.output)


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == importlib.metadata.version("kubex-codegen")
