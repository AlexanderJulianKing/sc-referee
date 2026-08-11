"""Load the closed, controller-installed method-conflict qualification grants."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.version import SCHEMA_VERSION


class QualificationGrantResourceError(ValueError):
    """The installed grant resource is absent, malformed, or digest-inconsistent."""


@dataclass(frozen=True)
class InstalledQualificationGrantEvidence:
    """One descriptor-bound qualification and metric-set pair."""

    grant: Mapping[str, object]
    qualification: Mapping[str, object]
    metric_set: Mapping[str, object]


def default_qualification_grant_root() -> Path:
    return Path(__file__).resolve().parent / "resources" / "qualification-grants-v1"


def default_qualification_manifest_path() -> Path:
    return (
        Path(__file__).resolve().parent
        / "resources"
        / "capability-manifests-v1"
        / "qualification-manifests.json"
    )


def default_schema_root() -> Path:
    return Path(__file__).resolve().parent / "resources" / f"schemas-v{SCHEMA_VERSION}"


def load_installed_qualification_grants(
    *,
    grant_root: Path | None = None,
    qualification_manifest_path: Path | None = None,
    schema_root: Path | None = None,
) -> Mapping[str, InstalledQualificationGrantEvidence]:
    """Load the package's digest-sealed records without consulting live adapter identity.

    Adapter-identity tamper evidence belongs to
    ``load_method_conflict_grant_evidence``; this lower resource loader closes only the
    canonical resource, schema, record-digest, and external-pin relationships.
    """

    root = (grant_root or default_qualification_grant_root()).resolve()
    qualifications_path = (
        qualification_manifest_path or default_qualification_manifest_path()
    ).resolve()
    schemas = (schema_root or default_schema_root()).resolve()
    if not root.is_dir() or root.is_symlink():
        raise QualificationGrantResourceError("grant root must be one non-symlink directory")

    descriptor_path = root / "grant-set.json"
    descriptor = _load_canonical_object(descriptor_path, "grant set")
    _require_exact_keys(
        descriptor,
        {
            "grant_set_kind",
            "grant_set_version",
            "schema_version",
            "qualification_manifest_digest",
            "metric_set_collection",
            "grants",
        },
        "grant set",
    )
    if descriptor["grant_set_kind"] != "method_conflict_qualification_grant_set_v1":
        raise QualificationGrantResourceError("grant set kind is unsupported")
    if descriptor["grant_set_version"] != "1.0.0":
        raise QualificationGrantResourceError("grant set version is unsupported")
    if descriptor["schema_version"] != SCHEMA_VERSION:
        raise QualificationGrantResourceError("grant set schema version does not match runtime")

    qualification_payload = _regular_file_bytes(qualifications_path, "qualification manifest")
    if sha256_digest(qualification_payload) != descriptor["qualification_manifest_digest"]:
        raise QualificationGrantResourceError("qualification manifest digest mismatch")
    qualification_collection = _load_canonical_object(qualifications_path, "qualification manifest")
    _require_collection(
        qualification_collection,
        kind="detector_qualification_manifest_collection",
        label="qualification manifest",
    )

    metric_descriptor = descriptor["metric_set_collection"]
    if not isinstance(metric_descriptor, dict):
        raise QualificationGrantResourceError("metric-set descriptor must be an object")
    _require_exact_keys(metric_descriptor, {"path", "digest"}, "metric-set descriptor")
    relative = _safe_relative(str(metric_descriptor["path"]))
    metric_path = root / relative
    if metric_path.parent != root:
        raise QualificationGrantResourceError("metric-set collection must be in the grant root")
    metric_payload = _regular_file_bytes(metric_path, "metric-set collection")
    if sha256_digest(metric_payload) != metric_descriptor["digest"]:
        raise QualificationGrantResourceError("metric-set collection digest mismatch")
    metric_collection = _load_canonical_object(metric_path, "metric-set collection")
    _require_collection(
        metric_collection,
        kind="qualification_metric_set_collection",
        label="metric-set collection",
    )

    registry = LocalSchemaRegistry(schemas)
    qualifications = _indexed_records(
        qualification_collection["records"], "qualification_id", "qualification"
    )
    metric_sets = _indexed_records(metric_collection["records"], "metric_set_id", "metric set")
    for record in qualifications.values():
        registry.validate(record)
    for record in metric_sets.values():
        registry.validate(record)

    grants = descriptor["grants"]
    if not isinstance(grants, list) or len(grants) != 2:
        raise QualificationGrantResourceError("grant set must contain exactly two grants")
    expected_grant_keys = {
        "binding_id",
        "binding_digest",
        "check_id",
        "check_version",
        "check_manifest_digest",
        "detector_id",
        "detector_version",
        "detector_manifest_digest",
        "qualification_id",
        "qualification_digest",
        "metric_set_id",
        "metric_set_digest",
        "threshold_policy_digest",
        "exam_adapter_identity",
        "absolute_missed_roots",
        "required_roots",
    }
    result: dict[str, InstalledQualificationGrantEvidence] = {}
    for grant in grants:
        if not isinstance(grant, dict):
            raise QualificationGrantResourceError("grant entry must be an object")
        _require_exact_keys(grant, expected_grant_keys, "grant entry")
        binding_id = grant.get("binding_id")
        qualification_id = grant.get("qualification_id")
        metric_set_id = grant.get("metric_set_id")
        if not all(
            isinstance(value, str) and value
            for value in (binding_id, qualification_id, metric_set_id)
        ):
            raise QualificationGrantResourceError("grant identifiers must be nonempty strings")
        if binding_id in result:
            raise QualificationGrantResourceError("grant binding IDs must be unique")
        qualification = qualifications.get(str(qualification_id))
        metric_set = metric_sets.get(str(metric_set_id))
        if qualification is None or metric_set is None:
            raise QualificationGrantResourceError("grant evidence reference is unresolved")
        _validate_grant_evidence(grant, qualification, metric_set)
        result[str(binding_id)] = InstalledQualificationGrantEvidence(
            grant=MappingProxyType(dict(grant)),
            qualification=MappingProxyType(dict(qualification)),
            metric_set=MappingProxyType(dict(metric_set)),
        )
    if list(result) != sorted(result):
        raise QualificationGrantResourceError("grant entries must be sorted by binding ID")
    if set(qualifications) != {str(item["qualification_id"]) for item in grants}:
        raise QualificationGrantResourceError("qualification collection exceeds the grant set")
    if set(metric_sets) != {str(item["metric_set_id"]) for item in grants}:
        raise QualificationGrantResourceError("metric-set collection exceeds the grant set")
    return MappingProxyType(result)


def _validate_grant_evidence(
    grant: dict[str, Any], qualification: dict[str, Any], metric_set: dict[str, Any]
) -> None:
    scope = qualification.get("binding_scope")
    policy = qualification.get("numeric_threshold_policy")
    counts = metric_set.get("counts")
    metric_refs = qualification.get("quantitative_metrics")
    if not isinstance(scope, dict) or not isinstance(policy, dict) or not isinstance(counts, dict):
        raise QualificationGrantResourceError("grant evidence has no closed scope/policy/counts")
    if not isinstance(metric_refs, dict):
        raise QualificationGrantResourceError("qualification has no metric reference")
    exact_scope = {
        "binding_id": "binding_id",
        "production_binding_digest": "binding_digest",
        "check_id": "check_id",
        "check_version": "check_version",
        "check_manifest_digest": "check_manifest_digest",
        "detector_id": "detector_id",
        "detector_version": "detector_version",
        "detector_manifest_digest": "detector_manifest_digest",
    }
    if any(scope.get(source) != grant.get(target) for source, target in exact_scope.items()):
        raise QualificationGrantResourceError("grant identity does not equal qualification scope")
    if (
        qualification.get("detector_id") != grant["detector_id"]
        or qualification.get("detector_version") != grant["detector_version"]
        or qualification.get("outcome") != "promoted"
        or qualification.get("effective_maturity") not in {"validated", "publication_grade"}
        or semantic_digest(qualification) != grant["qualification_digest"]
        or semantic_digest(metric_set) != grant["metric_set_digest"]
        or metric_set.get("detector_manifest_digest") != grant["detector_manifest_digest"]
        or metric_set.get("binding_scope") != scope
        or metric_set.get("numeric_threshold_policy") != policy
        or policy.get("policy_semantic_digest") != grant["threshold_policy_digest"]
        or metric_set.get("promotion_evidence_eligible") is not True
        or metric_set.get("promotion_permitted") is not True
        or counts.get("missed_roots") != grant["absolute_missed_roots"]
        or counts.get("adjudicated_roots") != grant["required_roots"]
    ):
        raise QualificationGrantResourceError("grant evidence does not match its external pins")
    refs = metric_refs.get("metric_set_refs")
    if (
        refs
        != [
            {
                "record_id": grant["metric_set_id"],
                "record_type": "qualification_metric_set",
            }
        ]
        or qualification.get("qualification_id") != grant["qualification_id"]
        or metric_set.get("metric_set_id") != grant["metric_set_id"]
    ):
        raise QualificationGrantResourceError("grant record references do not close")
    adapters = grant.get("exam_adapter_identity")
    if not isinstance(adapters, list) or not adapters:
        raise QualificationGrantResourceError("grant must pin at least one exam adapter")
    adapter_keys = {
        "adapter_id",
        "adapter_version",
        "implementation_digest",
        "manifest_digest",
        "recognition_grammar_digest",
    }
    for adapter in adapters:
        if not isinstance(adapter, dict):
            raise QualificationGrantResourceError("exam adapter pin must be an object")
        _require_exact_keys(adapter, adapter_keys, "exam adapter pin")
        if not all(isinstance(value, str) and value for value in adapter.values()):
            raise QualificationGrantResourceError("exam adapter pin fields must be strings")


def _indexed_records(records: object, key: str, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list):
        raise QualificationGrantResourceError(f"{label} records must be an array")
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get(key), str):
            raise QualificationGrantResourceError(f"{label} record lacks {key}")
        identifier = str(record[key])
        if identifier in result:
            raise QualificationGrantResourceError(f"duplicate {label} identifier")
        result[identifier] = record
    if list(result) != sorted(result):
        raise QualificationGrantResourceError(f"{label} records must be sorted")
    return result


def _require_collection(value: dict[str, Any], *, kind: str, label: str) -> None:
    _require_exact_keys(value, {"manifest_kind", "manifest_version", "records"}, label)
    if value["manifest_kind"] != kind or value["manifest_version"] != "1.0.0":
        raise QualificationGrantResourceError(f"{label} has unsupported collection metadata")


def _safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or len(path.parts) != 1
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise QualificationGrantResourceError("grant resource path must name one local file")
    return path


def _regular_file_bytes(path: Path, label: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise QualificationGrantResourceError(f"{label} must be one regular file")
    return path.read_bytes()


def _load_canonical_object(path: Path, label: str) -> dict[str, Any]:
    payload = _regular_file_bytes(path, label)
    try:
        value = json.loads(
            payload.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise QualificationGrantResourceError(f"{label} is not strict JSON") from error
    if not isinstance(value, dict) or payload != (canonical_json(value) + "\n").encode():
        raise QualificationGrantResourceError(f"{label} must be one canonical JSON object")
    return value


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise QualificationGrantResourceError(f"{label} fields are not closed")
