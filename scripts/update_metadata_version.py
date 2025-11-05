#!/usr/bin/env python3
"""Synchronise metadata.txt version with pyproject.toml."""
from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_FILE = REPO_ROOT / "pyproject.toml"
METADATA_FILE = REPO_ROOT / "geovita_processing_plugin" / "metadata.txt"
VERSION_PATTERN = re.compile(r"^(version\s*=\s*)(.+)$", re.MULTILINE)


class MetadataVersionError(RuntimeError):
    """Raised when metadata synchronisation cannot be completed."""


def read_version_from_pyproject() -> str:
    if not PYPROJECT_FILE.is_file():
        raise MetadataVersionError(f"Missing pyproject: {PYPROJECT_FILE}")

    with PYPROJECT_FILE.open("rb") as fh:
        data = tomllib.load(fh)

    project = data.get("project")
    if not project or "version" not in project:
        raise MetadataVersionError("[project] table missing version")

    return project["version"]


def update_metadata_version(new_version: str) -> None:
    if not METADATA_FILE.is_file():
        raise MetadataVersionError(f"Missing metadata file: {METADATA_FILE}")

    contents = METADATA_FILE.read_text(encoding="utf-8")
    if "[general]" not in contents:
        raise MetadataVersionError("metadata.txt lacks [general] section")

    if "version=" not in contents:
        raise MetadataVersionError("metadata.txt lacks version entry")

    def _replace(match: re.Match[str]) -> str:
        return f"{match.group(1)}{new_version}"

    updated, count = VERSION_PATTERN.subn(_replace, contents, count=1)
    if count != 1:
        raise MetadataVersionError("Unexpected number of version entries updated")

    METADATA_FILE.write_text(updated, encoding="utf-8")


def main() -> None:
    version = read_version_from_pyproject()
    update_metadata_version(version)
    print(f"Updated metadata version to {version}")


if __name__ == "__main__":
    main()
