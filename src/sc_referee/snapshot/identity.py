from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.version import SCHEMA_VERSION, __version__

DataIdentityTier = Literal[
    "full_digest",
    "immutable_external",
    "manifest",
    "weak_fingerprint",
    "unidentified",
]

_DIGEST_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")


@dataclass(frozen=True)
class AssetIdentityEvidence:
    """Validated evidence for one normative asset-identity tier."""

    tier: DataIdentityTier
    identity_evidence: dict[str, Any]
    limitations: tuple[str, ...] = ()
    extensions: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        kind = self.identity_evidence.get("kind")
        if kind != self.tier:
            raise ValueError(f"identity evidence kind {kind!r} does not match tier {self.tier!r}")
        if self.tier == "full_digest":
            _require_digest_field(self.identity_evidence, "digest", "full digest")
        elif self.tier == "immutable_external":
            _require_nonempty_field(self.identity_evidence, "external_identifier")
            _require_nonempty_field(self.identity_evidence, "version")
            digest = self.identity_evidence.get("digest")
            if digest is not None:
                if not isinstance(digest, str):
                    raise ValueError("immutable external digest must be a string")
                _require_digest(digest, "immutable external digest")
        elif self.tier == "manifest":
            if not isinstance(self.identity_evidence.get("manifest_ref"), Mapping):
                raise ValueError("manifest identity requires a source reference")
            _require_digest_field(self.identity_evidence, "manifest_digest", "manifest digest")
        elif self.tier == "weak_fingerprint":
            _require_nonempty_field(self.identity_evidence, "path")
            size_bytes = self.identity_evidence.get("size_bytes")
            if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < 0:
                raise ValueError("weak fingerprint size must be a nonnegative integer")
            _require_digest_field(
                self.identity_evidence, "sampled_fingerprint", "sampled fingerprint"
            )
        elif self.tier == "unidentified":
            _require_nonempty_field(self.identity_evidence, "reason")
        if self.tier == "weak_fingerprint" and not self.limitations:
            raise ValueError("weak fingerprint identity requires at least one limitation")
        if any(not limitation for limitation in self.limitations):
            raise ValueError("asset identity limitations must be non-empty strings")


def full_digest_evidence(digest: str) -> AssetIdentityEvidence:
    _require_digest(digest, "full digest")
    return AssetIdentityEvidence(
        tier="full_digest",
        identity_evidence={"kind": "full_digest", "digest": digest},
    )


def immutable_external_evidence(
    external_identifier: str,
    version: str,
    *,
    digest: str | None = None,
    limitations: tuple[str, ...] = (),
) -> AssetIdentityEvidence:
    if not external_identifier or not version:
        raise ValueError("immutable external identity requires an identifier and version")
    evidence: dict[str, Any] = {
        "kind": "immutable_external",
        "external_identifier": external_identifier,
        "version": version,
    }
    if digest is not None:
        _require_digest(digest, "immutable external digest")
        evidence["digest"] = digest
    return AssetIdentityEvidence(
        tier="immutable_external",
        identity_evidence=evidence,
        limitations=limitations,
    )


def manifest_evidence(
    manifest_ref: Mapping[str, Any],
    manifest_digest: str,
    *,
    limitations: tuple[str, ...] = (),
    extensions: Mapping[str, Any] | None = None,
) -> AssetIdentityEvidence:
    _require_digest(manifest_digest, "manifest digest")
    return AssetIdentityEvidence(
        tier="manifest",
        identity_evidence={
            "kind": "manifest",
            "manifest_ref": dict(manifest_ref),
            "manifest_digest": manifest_digest,
        },
        limitations=limitations,
        extensions=extensions,
    )


def weak_fingerprint_evidence(
    path: str,
    size_bytes: int,
    sampled_fingerprint: str,
    *,
    modified_at: str | None = None,
    limitations: tuple[str, ...],
    profile: str,
) -> AssetIdentityEvidence:
    if not path or size_bytes < 0:
        raise ValueError("weak fingerprint identity requires a path and nonnegative size")
    _require_digest(sampled_fingerprint, "sampled fingerprint")
    evidence: dict[str, Any] = {
        "kind": "weak_fingerprint",
        "path": path,
        "size_bytes": size_bytes,
        "sampled_fingerprint": sampled_fingerprint,
    }
    if modified_at is not None:
        evidence["modified_at"] = modified_at
    return AssetIdentityEvidence(
        tier="weak_fingerprint",
        identity_evidence=evidence,
        limitations=limitations,
        extensions={"x-sampled-fingerprint-profile": profile},
    )


def unidentified_evidence(
    reason: str,
    *,
    reported_location: str | None = None,
    limitations: tuple[str, ...] = (),
) -> AssetIdentityEvidence:
    if not reason:
        raise ValueError("unidentified identity requires a reason")
    evidence: dict[str, Any] = {"kind": "unidentified", "reason": reason}
    if reported_location is not None:
        evidence["reported_location"] = reported_location
    return AssetIdentityEvidence(
        tier="unidentified",
        identity_evidence=evidence,
        limitations=limitations,
    )


def build_asset_identity(
    *,
    audit_run_id: str,
    asset_record_type: str,
    asset_record_id: str,
    evidence: AssetIdentityEvidence,
    created_at: str,
) -> dict[str, Any]:
    """Create one stable public AssetIdentity record from independently checkable evidence."""

    asset_ref = {"record_type": asset_record_type, "record_id": asset_record_id}
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "asset_identity",
        "asset_identity_id": stable_id(
            "asset-identity",
            audit_run_id,
            asset_record_type,
            asset_record_id,
            evidence.tier,
            semantic_digest(evidence.identity_evidence),
        ),
        "audit_run_id": audit_run_id,
        "asset_ref": asset_ref,
        "tier": evidence.tier,
        "identity_evidence": dict(evidence.identity_evidence),
        "limitations": list(evidence.limitations),
        "created_at": created_at,
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-controller",
                "display_name": "sc-referee controller",
            },
            "method": "deterministic_asset_identity",
            "created_at": created_at,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }
    if evidence.extensions:
        record["extensions"] = dict(evidence.extensions)
    return record


def _require_digest(value: str, label: str) -> None:
    if not _DIGEST_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must be a canonical sha256 digest")


def _require_digest_field(value: Mapping[str, Any], field: str, label: str) -> None:
    digest = value.get(field)
    if not isinstance(digest, str):
        raise ValueError(f"{label} must be a string")
    _require_digest(digest, label)


def _require_nonempty_field(value: Mapping[str, Any], field: str) -> None:
    if not isinstance(value.get(field), str) or not value[field]:
        raise ValueError(f"identity evidence requires non-empty {field}")
