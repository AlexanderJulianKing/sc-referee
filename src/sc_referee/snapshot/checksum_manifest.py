from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath

from sc_referee.core.ids import sha256_digest

CHECKSUM_MANIFEST_PROFILE = "root-sha256sum-two-space-v1"
_CHECKSUM_LINE = re.compile(r"^([a-f0-9]{64})  (.+)$")


@dataclass(frozen=True)
class ChecksumDeclaration:
    target_path: str
    target_digest: str
    manifest_path: str
    manifest_content_digest: str
    line_number: int
    quoted_text: str

    @property
    def source_ref(self) -> dict[str, object]:
        return {
            "source_kind": "file_span",
            "locator": f"{self.manifest_path}:{self.line_number}",
            "path": self.manifest_path,
            "start_line": self.line_number,
            "end_line": self.line_number,
            "content_digest": self.manifest_content_digest,
            "quoted_text": self.quoted_text,
        }


@dataclass(frozen=True)
class ChecksumManifestInspection:
    declarations: Mapping[str, ChecksumDeclaration]
    candidate_paths: tuple[str, ...]
    parsed_paths: tuple[str, ...]
    invalid_paths: tuple[str, ...]
    unavailable_paths: tuple[str, ...]
    ambiguous_targets: tuple[str, ...]

    def public_summary(self, *, upgraded_targets: Sequence[str]) -> dict[str, object]:
        return {
            "profile": CHECKSUM_MANIFEST_PROFILE,
            "candidate_paths": list(self.candidate_paths),
            "parsed_paths": list(self.parsed_paths),
            "invalid_paths": list(self.invalid_paths),
            "unavailable_paths": list(self.unavailable_paths),
            "ambiguous_targets": list(self.ambiguous_targets),
            "unambiguous_declarations": len(self.declarations),
            "upgraded_targets": sorted(upgraded_targets),
        }


def is_root_checksum_manifest(path: str) -> bool:
    """Recognize only an explicit root-level SHA-256 checksum-manifest profile."""

    if "/" in path:
        return False
    lower_name = path.lower()
    return lower_name in {"sha256sums", "sha256sums.txt"} or lower_name.endswith(".sha256")


def inspect_checksum_manifests(
    candidate_paths: Sequence[str],
    full_payloads: Mapping[str, bytes],
) -> ChecksumManifestInspection:
    """Parse fully captured root manifests; malformed or ambiguous declarations fail closed."""

    declarations_by_target: dict[str, list[ChecksumDeclaration]] = {}
    parsed_paths: list[str] = []
    invalid_paths: list[str] = []
    unavailable_paths: list[str] = []
    for manifest_path in sorted(set(candidate_paths)):
        payload = full_payloads.get(manifest_path)
        if payload is None:
            unavailable_paths.append(manifest_path)
            continue
        parsed = _parse_manifest(manifest_path, payload)
        if parsed is None:
            invalid_paths.append(manifest_path)
            continue
        parsed_paths.append(manifest_path)
        for declaration in parsed:
            declarations_by_target.setdefault(declaration.target_path, []).append(declaration)

    ambiguous_targets = sorted(
        target for target, declarations in declarations_by_target.items() if len(declarations) != 1
    )
    unambiguous = {
        target: declarations[0]
        for target, declarations in declarations_by_target.items()
        if len(declarations) == 1
    }
    return ChecksumManifestInspection(
        declarations=unambiguous,
        candidate_paths=tuple(sorted(set(candidate_paths))),
        parsed_paths=tuple(parsed_paths),
        invalid_paths=tuple(invalid_paths),
        unavailable_paths=tuple(unavailable_paths),
        ambiguous_targets=tuple(ambiguous_targets),
    )


def _parse_manifest(manifest_path: str, payload: bytes) -> list[ChecksumDeclaration] | None:
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    manifest_content_digest = sha256_digest(payload)
    declarations: list[ChecksumDeclaration] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line or line.startswith("#"):
            continue
        match = _CHECKSUM_LINE.fullmatch(line)
        if match is None:
            return None
        target_path = match.group(2)
        if not _safe_repository_relative_path(target_path) or target_path == manifest_path:
            return None
        declarations.append(
            ChecksumDeclaration(
                target_path=target_path,
                target_digest=f"sha256:{match.group(1)}",
                manifest_path=manifest_path,
                manifest_content_digest=manifest_content_digest,
                line_number=line_number,
                quoted_text=line,
            )
        )
    return declarations or None


def _safe_repository_relative_path(value: str) -> bool:
    if not value or value != value.strip() or "\\" in value or "\x00" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and path.as_posix() == value
        and all(part not in {"", ".", ".."} for part in path.parts)
    )
