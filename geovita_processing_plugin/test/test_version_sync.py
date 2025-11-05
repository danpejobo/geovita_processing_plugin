"""Tests ensuring version consistency across metadata sources."""
from __future__ import annotations

import configparser
from pathlib import Path

import geovita_processing_plugin as plugin

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT_FILE = REPO_ROOT / "pyproject.toml"
METADATA_FILE = REPO_ROOT / "geovita_processing_plugin" / "metadata.txt"


def read_version_from_pyproject() -> str:
    with PYPROJECT_FILE.open("rb") as fh:
        data = tomllib.load(fh)
    return data["project"]["version"]


def read_version_from_metadata() -> str:
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(METADATA_FILE)
    return parser.get("general", "version")


def test_package_version_matches_pyproject():
    assert plugin.__version__ == read_version_from_pyproject()


def test_metadata_version_matches_pyproject():
    assert read_version_from_metadata() == read_version_from_pyproject()


def test_package_version_matches_metadata():
    assert plugin.__version__ == read_version_from_metadata()
