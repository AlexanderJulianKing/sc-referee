from __future__ import annotations

import json
import os
import zipfile
from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sc_referee.cli import app
from sc_referee.controller import run_demo
from sc_referee.core.ids import canonical_json
from sc_referee.ro_crate import export_ro_crate, validate_ro_crate

_AUTHOR_NAME = "Example audit curator"
_LICENSE_URI = "https://spdx.org/licenses/Apache-2.0.html"
_LICENSE_NAME = "Apache License 2.0"


def _audit(project_root: Path, schema_root: Path, tmp_path: Path) -> Path:
    audit_root = tmp_path / "audit"
    run_demo(project_root / "examples" / "walking-skeleton", audit_root, schema_root)
    return audit_root


def _export(audit_root: Path, schema_root: Path, output: Path) -> dict[str, object]:
    return export_ro_crate(
        audit_root,
        output,
        schema_root,
        author_name=_AUTHOR_NAME,
        license_uri=_LICENSE_URI,
        license_name=_LICENSE_NAME,
    )


def _rewrite_member(
    archive: Path, member: str, transform: Callable[[bytes], bytes] | bytes
) -> None:
    with zipfile.ZipFile(archive, "r") as source:
        entries = {info.filename: (info, source.read(info.filename)) for info in source.infolist()}
    payloads = {name: payload for name, (_, payload) in entries.items()}
    if callable(transform):
        payloads[member] = transform(payloads[member])
    else:
        assert isinstance(transform, bytes)
        payloads[member] = transform
    temporary = archive.with_suffix(".rewrite")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED) as target:
        for name in sorted(payloads):
            original = entries[name][0]
            info = zipfile.ZipInfo(name, date_time=original.date_time)
            info.compress_type = original.compress_type
            info.create_system = original.create_system
            info.external_attr = original.external_attr
            target.writestr(info, payloads[name])
    os.replace(temporary, archive)


def test_ro_crate_export_is_deterministic_valid_and_preserves_native_bytes(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    audit_root = _audit(project_root, schema_root, tmp_path)
    source_bundle = (audit_root / "audit.bundle.json").read_bytes()
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    record = _export(audit_root, schema_root, first)
    _export(audit_root, schema_root, second)
    validated = validate_ro_crate(first, schema_root)

    assert first.read_bytes() == second.read_bytes()
    assert validated == record
    assert record["validation_status"] == "valid"
    assert record["native_records_included"] is True
    assert record["ro_crate_version"] == "1.3"
    assert record["extensions"] == {
        "x-authorship-declared-not-authenticated": True,
        "x-content-digest-profile": ("canonical-json-file-inventory-excluding-ro-crate-export-v1"),
        "x-content-digest-self-excluded-path": "ro-crate-export.json",
        "x-native-audit-root": "native/",
        "x-third-party-ro-crate-validation": "not_performed",
    }
    with zipfile.ZipFile(first, "r") as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert "audit.db" not in "\n".join(names)
        assert archive.read("native/audit.bundle.json") == source_bundle
        metadata = json.loads(archive.read("ro-crate-metadata.json"))
        root = next(item for item in metadata["@graph"] if item["@id"] == "./")
        author = next(item for item in metadata["@graph"] if item["@id"] == "#author")
        license_entity = next(item for item in metadata["@graph"] if item["@id"] == _LICENSE_URI)
        assert metadata["@context"] == "https://w3id.org/ro/crate/1.3/context"
        assert root["author"] == {"@id": "#author"}
        assert root["license"] == {"@id": _LICENSE_URI}
        assert author["name"] == _AUTHOR_NAME
        assert license_entity["name"] == _LICENSE_NAME

        source_manifest = json.loads((audit_root / "audit.bundle.json").read_text())[
            "storage_manifests"
        ][0]
        paths = [entry["path"] for entry in source_manifest["extensions"]["x-canonical-files"]]
        paths.append("derived/storage-manifest.jsonl")
        for relative in paths:
            assert archive.read(f"native/{relative}") == (audit_root / relative).read_bytes()

    assert (audit_root / "audit.bundle.json").read_bytes() == source_bundle
    assert json.loads(source_bundle)["ro_crate_exports"] == []


@pytest.mark.parametrize(
    ("member", "transform", "message"),
    [
        (
            "native/audit.bundle.json",
            lambda payload: payload + b" ",
            "native file",
        ),
        (
            "native/report.html",
            lambda payload: payload + b"tampered",
            "native file",
        ),
        (
            "ro-crate-metadata.json",
            lambda payload: (
                canonical_json(
                    {
                        **json.loads(payload),
                        "@context": "https://w3id.org/ro/crate/1.2/context",
                    }
                )
                + "\n"
            ).encode(),
            "RO-Crate 1.3 context",
        ),
        (
            "ro-crate-export.json",
            lambda payload: (
                canonical_json(
                    {
                        **json.loads(payload),
                        "content_digest": "sha256:" + "0" * 64,
                    }
                )
                + "\n"
            ).encode(),
            "content digest",
        ),
    ],
)
def test_ro_crate_validation_rejects_tampering(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    member: str,
    transform: Callable[[bytes], bytes] | bytes,
    message: str,
) -> None:
    audit_root = _audit(project_root, schema_root, tmp_path)
    archive = tmp_path / "audit.zip"
    _export(audit_root, schema_root, archive)
    _rewrite_member(archive, member, transform)

    with pytest.raises(ValueError, match=message):
        validate_ro_crate(archive, schema_root)


def test_ro_crate_export_never_overwrites_an_existing_path(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    audit_root = _audit(project_root, schema_root, tmp_path)
    archive = tmp_path / "audit.zip"
    archive.write_bytes(b"keep")

    with pytest.raises(FileExistsError):
        _export(audit_root, schema_root, archive)

    assert archive.read_bytes() == b"keep"

    sentinel = tmp_path / "sentinel"
    sentinel.write_bytes(b"also keep")
    link = tmp_path / "linked.zip"
    link.symlink_to(sentinel)
    with pytest.raises(FileExistsError):
        _export(audit_root, schema_root, link)
    assert link.is_symlink()
    assert sentinel.read_bytes() == b"also keep"


def test_ro_crate_export_never_writes_inside_the_source_audit(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    audit_root = _audit(project_root, schema_root, tmp_path)

    with pytest.raises(ValueError, match="outside the source audit root"):
        _export(audit_root, schema_root, audit_root / "export.zip")

    assert not (audit_root / "export.zip").exists()


def test_ro_crate_export_rejects_tampered_source_report(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    audit_root = _audit(project_root, schema_root, tmp_path)
    (audit_root / "report.html").write_text("<html>tampered</html>", encoding="utf-8")

    with pytest.raises(ValueError, match="report bytes"):
        _export(audit_root, schema_root, tmp_path / "audit.zip")


@pytest.mark.parametrize(
    ("author_id", "license_uri", "message"),
    [
        ("relative-author", _LICENSE_URI, "author identifier"),
        ("javascript:alert(1)", _LICENSE_URI, "unsupported URI scheme"),
        ("#author", "relative-license", "license URI"),
        ("#author", "https://user:secret@example.test/license", "credentials"),
    ],
)
def test_ro_crate_export_rejects_unsafe_declared_metadata(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    author_id: str,
    license_uri: str,
    message: str,
) -> None:
    audit_root = _audit(project_root, schema_root, tmp_path)

    with pytest.raises(ValueError, match=message):
        export_ro_crate(
            audit_root,
            tmp_path / "audit.zip",
            schema_root,
            author_id=author_id,
            author_name=_AUTHOR_NAME,
            license_uri=license_uri,
            license_name=_LICENSE_NAME,
        )


def test_ro_crate_validation_rejects_unsafe_or_duplicate_archive_members(
    schema_root: Path, tmp_path: Path
) -> None:
    unsafe = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(unsafe, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("../escape", b"unsafe")
    with pytest.raises(ValueError, match="unsafe RO-Crate archive member"):
        validate_ro_crate(unsafe, schema_root)

    duplicate = tmp_path / "duplicate.zip"
    with pytest.warns(UserWarning, match="Duplicate name"):
        with zipfile.ZipFile(duplicate, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr("same", b"one")
            archive.writestr("same", b"two")
    with pytest.raises(ValueError, match="sorted and unique"):
        validate_ro_crate(duplicate, schema_root)


def test_ro_crate_cli_exports_and_validates_offline(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    audit_root = _audit(project_root, schema_root, tmp_path)
    archive = tmp_path / "audit.zip"
    runner = CliRunner()

    exported = runner.invoke(
        app,
        [
            "export-ro-crate",
            str(audit_root),
            "--output",
            str(archive),
            "--author-name",
            _AUTHOR_NAME,
            "--license-uri",
            _LICENSE_URI,
            "--license-name",
            _LICENSE_NAME,
            "--schema-root",
            str(schema_root),
        ],
    )
    validated = runner.invoke(
        app,
        ["validate-ro-crate", str(archive), "--schema-root", str(schema_root)],
    )

    assert exported.exit_code == 0, exported.output
    assert archive.is_file()
    assert validated.exit_code == 0, validated.output
    payload = json.loads(validated.output)
    assert payload["record_type"] == "ro_crate_export"
    assert payload["validation_status"] == "valid"
