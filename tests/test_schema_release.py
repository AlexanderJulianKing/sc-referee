from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_schema_release import RELEASE_VERSION, build_release


def test_committed_release_is_accepted_exact_v060(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.6.0"
    status = json.loads((release / "RELEASE_STATUS.json").read_text(encoding="utf-8"))
    assert status == {
        "accepted": True,
        "amending_adrs": ["docs/implementation/ADR-0003-UNAVAILABLE-PUBLICATION-SURFACE.md"],
        "baseline_version": "0.5.0",
        "public_release": True,
        "release_version": "0.6.0",
        "source_adr": "docs/implementation/ADR-0002-OBSERVED-PLANE-PROMOTION.md",
    }
    assert RELEASE_VERSION == "0.6.0"
    assert LocalSchemaRegistry(release).validate_example_directory() == 50


def test_release_manifest_binds_every_file(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.6.0"
    manifest = {}
    for line in (release / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", maxsplit=1)
        manifest[relative] = digest
    actual = {
        path.relative_to(release).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in release.rglob("*")
        if path.is_file()
        and path.name != "MANIFEST.sha256"
        and not any(part.startswith(".") or part == "__pycache__" for part in path.parts)
    }
    assert manifest == actual


def test_release_builder_is_reproducible_and_preserves_v05(
    project_root: Path, tmp_path: Path
) -> None:
    baseline_catalog = project_root / "reference" / "schemas-v0.5.0" / "schema-catalog.json"
    before = baseline_catalog.read_bytes()
    output = tmp_path / "schemas-v0.6.0"
    assert build_release(output) == 50
    committed = project_root / "reference" / "schemas-v0.6.0"
    generated_files = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    committed_files = {
        path.relative_to(committed).as_posix(): path.read_bytes()
        for path in committed.rglob("*")
        if path.is_file()
        and not any(part.startswith(".") or part == "__pycache__" for part in path.parts)
    }
    assert generated_files == committed_files
    assert baseline_catalog.read_bytes() == before
