from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, sha256_digest, stable_id
from sc_referee.detectors import method_conflict_grant_pins
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.storage.atomic import atomic_create_bytes
from sc_referee.version import SCHEMA_VERSION, __version__


class CapabilityMatrixError(ValueError):
    """Raised when capability source manifests cannot support their public claims."""


_COLLECTION_KINDS = {
    "parser_manifests": "parser_manifest_collection",
    "profile_manifests": "semantic_profile_manifest_collection",
    "detector_manifests": "detector_manifest_collection",
    "qualification_manifests": "detector_qualification_manifest_collection",
    "version_manifests": "version_manifest_collection",
}
_PROFILE_STATES = {
    "syntax_recognition": {
        "not_started",
        "planned",
        "partial",
        "validated",
        "complete_for_declared_forms",
    },
    "operation_extraction": {
        "not_started",
        "planned",
        "partial",
        "validated",
        "complete_for_declared_forms",
    },
    "semantic_modeling": {
        "not_started",
        "planned",
        "partial",
        "validated",
        "complete_for_declared_contract",
    },
}
_OUTPUT_RANK = {
    "none": 0,
    "disclosure": 1,
    "material_question": 2,
    "conditional_concern": 3,
    "finding": 4,
}


def default_capability_manifest_root() -> Path:
    return Path(__file__).resolve().parent / "resources" / "capability-manifests-v1"


def generate_capability_matrix(
    manifest_root: Path,
    schema_root: Path,
) -> dict[str, Any]:
    """Project one closed release-manifest set into a public CapabilityMatrix."""

    root = manifest_root.resolve()
    if not root.is_dir() or manifest_root.is_symlink():
        raise CapabilityMatrixError("capability manifest root must be a non-symlink directory")
    set_path = root / "manifest-set.json"
    manifest_set = _load_canonical_object(set_path, "manifest set")
    _require_exact_keys(
        manifest_set,
        {
            "profile",
            "manifest_set_id",
            "schema_version",
            "release_version",
            "generated_at",
            "collections",
        },
        "manifest set",
    )
    if manifest_set["profile"] != "sc-referee-capability-source-v1":
        raise CapabilityMatrixError("unsupported capability manifest-set profile")
    if manifest_set["schema_version"] != SCHEMA_VERSION:
        raise CapabilityMatrixError("capability manifest-set schema version does not match runtime")
    for field in ("manifest_set_id", "release_version", "generated_at"):
        _require_string(manifest_set.get(field), f"manifest set {field}")

    descriptors = manifest_set.get("collections")
    if not isinstance(descriptors, list) or len(descriptors) != len(_COLLECTION_KINDS):
        raise CapabilityMatrixError("manifest set must bind exactly five collections")
    collection_values: dict[str, dict[str, Any]] = {}
    collection_digests: dict[str, str] = {}
    observed_kinds: list[str] = []
    for descriptor in descriptors:
        if not isinstance(descriptor, dict):
            raise CapabilityMatrixError("collection descriptor must be an object")
        _require_exact_keys(descriptor, {"kind", "path", "digest"}, "collection descriptor")
        kind = _require_string(descriptor.get("kind"), "collection kind")
        if kind not in _COLLECTION_KINDS or kind in collection_values:
            raise CapabilityMatrixError(f"unexpected or duplicate collection kind: {kind}")
        relative_path = _safe_relative_path(_require_string(descriptor.get("path"), f"{kind} path"))
        path = root / relative_path
        if path.parent != root or path.is_symlink() or not path.is_file():
            raise CapabilityMatrixError(f"{kind} must be one regular file in the manifest root")
        payload = path.read_bytes()
        expected_digest = _require_digest(descriptor.get("digest"), f"{kind} digest")
        if sha256_digest(payload) != expected_digest:
            raise CapabilityMatrixError(f"{kind} collection digest mismatch")
        collection = _load_canonical_object(path, kind)
        _require_exact_keys(
            collection,
            {"manifest_kind", "manifest_version", "records"},
            kind,
        )
        if collection["manifest_kind"] != _COLLECTION_KINDS[kind]:
            raise CapabilityMatrixError(f"{kind} has the wrong manifest_kind")
        if collection["manifest_version"] != "1.0.0":
            raise CapabilityMatrixError(f"{kind} has an unsupported manifest version")
        if not isinstance(collection["records"], list):
            raise CapabilityMatrixError(f"{kind} records must be an array")
        observed_kinds.append(kind)
        collection_values[kind] = collection
        collection_digests[kind] = expected_digest
    if observed_kinds != sorted(_COLLECTION_KINDS):
        raise CapabilityMatrixError("collection descriptors must be sorted by kind")

    registry = LocalSchemaRegistry(schema_root)
    parsers = _public_records(
        collection_values["parser_manifests"]["records"],
        "parser_manifest",
        "parser_id",
        registry,
    )
    detector_history = _public_versioned_records(
        collection_values["detector_manifests"]["records"],
        "detector_manifest",
        "detector_id",
        "detector_version",
        registry,
    )
    qualifications = _public_records(
        collection_values["qualification_manifests"]["records"],
        "detector_qualification",
        "qualification_id",
        registry,
    )
    profiles = _private_records(collection_values["profile_manifests"]["records"], "profile_id")
    versions = _private_records(
        collection_values["version_manifests"]["records"], "version_manifest_id"
    )
    _verify_builtin_implementation_digests(parsers)

    parser_by_id = {str(record["parser_id"]): record for record in parsers}
    qualification_by_id = {str(record["qualification_id"]): record for record in qualifications}
    detectors = _qualified_or_latest_detector_records(detector_history, qualification_by_id)
    detector_by_id = {str(record["detector_id"]): record for record in detectors}
    version_by_id = _validate_version_manifests(versions)
    profile_ids = {str(profile.get("profile_id")) for profile in profiles}
    if {str(version.get("profile_ref")) for version in versions} != profile_ids:
        raise CapabilityMatrixError(
            "version manifests must form an exact one-to-one mapping with semantic profiles"
        )

    entries = [
        _build_entry(
            profile,
            parser_by_id,
            detector_by_id,
            qualification_by_id,
            version_by_id,
        )
        for profile in profiles
    ]
    entries.sort(key=lambda entry: str(entry["entry_id"]))
    if not entries:
        raise CapabilityMatrixError("capability matrix requires at least one narrow profile")

    generated_refs = [
        *(
            {"record_type": "parser_manifest", "record_id": str(record["parser_id"])}
            for record in parsers
        ),
        *(
            {"record_type": "detector_manifest", "record_id": str(record["detector_id"])}
            for record in detectors
        ),
        *(
            {
                "record_type": "detector_qualification",
                "record_id": str(record["qualification_id"]),
            }
            for record in qualifications
        ),
    ]
    generated_refs.sort(key=lambda ref: (str(ref["record_type"]), str(ref["record_id"])))
    if not generated_refs:
        raise CapabilityMatrixError("manifest set has no public source records")

    set_digest = sha256_digest(set_path.read_bytes())
    generated_at = str(manifest_set["generated_at"])
    matrix = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "capability_matrix",
        "matrix_id": stable_id(
            "capability-matrix", str(manifest_set["manifest_set_id"]), set_digest
        ),
        "release_version": manifest_set["release_version"],
        "generated_at": generated_at,
        "generated_from_manifest_refs": generated_refs,
        "entries": entries,
        "domain_wide_support_claim_allowed": False,
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-capability-generator",
                "display_name": "sc-referee capability generator",
            },
            "method": "deterministic_manifest_projection",
            "created_at": generated_at,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": {
            "x-generator-profile": "sc-referee-capability-source-v1",
            "x-manifest-set-id": manifest_set["manifest_set_id"],
            "x-manifest-set-digest": set_digest,
            "x-collection-digests": collection_digests,
            "x-source-profile-ids": sorted(profile_ids),
            "x-source-version-manifest-ids": sorted(version_by_id),
            "x-parser-supported-versions-are-not-tested-versions": True,
            "x-empty-detector-state-preserved": not detectors,
            "x-domain-wide-inference-prohibited": True,
        },
    }
    registry.validate(matrix)
    return matrix


def _qualified_or_latest_detector_records(
    records: list[dict[str, Any]],
    qualification_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Prefer one installed qualified identity; otherwise expose the newest development one."""

    latest = {
        str(item["detector_id"]): item
        for item in _latest_version_records(records, "detector_id", "detector_version")
    }
    by_id: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_id.setdefault(str(record["detector_id"]), []).append(record)
    selected: list[dict[str, Any]] = []
    for detector_id, history in sorted(by_id.items()):
        qualified = [
            record for record in history if _binding_grant_entries(record, qualification_by_id)
        ]
        if len(qualified) > 1:
            raise CapabilityMatrixError(
                f"detector has multiple installed qualified identities: {detector_id}"
            )
        selected.append(qualified[0] if qualified else latest[detector_id])
    return selected


def write_capability_matrix(
    output: Path,
    manifest_root: Path,
    schema_root: Path,
) -> dict[str, Any]:
    matrix = generate_capability_matrix(manifest_root, schema_root)
    atomic_create_bytes(output, (canonical_json(matrix) + "\n").encode("utf-8"))
    return matrix


def load_capability_detector_manifest(
    manifest_root: Path,
    schema_root: Path,
    detector_id: str,
    *,
    detector_version: str | None = None,
) -> dict[str, Any]:
    """Load one detector only after the complete capability source set validates."""

    generate_capability_matrix(manifest_root, schema_root)
    collection = _load_canonical_object(
        manifest_root.resolve() / "detector-manifests.json", "detector_manifests"
    )
    matches = [
        record
        for record in collection["records"]
        if isinstance(record, dict)
        and record.get("detector_id") == detector_id
        and (detector_version is None or record.get("detector_version") == detector_version)
    ]
    if not matches:
        raise CapabilityMatrixError(
            f"capability source set does not contain detector {detector_id!r}"
        )
    latest = (
        matches
        if detector_version is not None
        else _latest_version_records(matches, "detector_id", "detector_version")
    )
    if len(latest) != 1:
        raise CapabilityMatrixError(
            f"capability source set does not resolve one live detector {detector_id!r}"
        )
    return deepcopy(latest[0])


def validate_capability_matrix(
    path: Path,
    manifest_root: Path,
    schema_root: Path,
) -> dict[str, Any]:
    observed = _load_canonical_object(path, "capability matrix")
    LocalSchemaRegistry(schema_root).validate(observed)
    expected = generate_capability_matrix(manifest_root, schema_root)
    if observed != expected:
        raise CapabilityMatrixError(
            "capability matrix does not equal deterministic manifest projection"
        )
    return observed


def _build_entry(
    profile: dict[str, Any],
    parser_by_id: dict[str, dict[str, Any]],
    detector_by_id: dict[str, dict[str, Any]],
    qualification_by_id: dict[str, dict[str, Any]],
    version_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    _require_exact_keys(
        profile,
        {
            "profile_id",
            "capability_entry_id",
            "domain",
            "language",
            "package",
            "parser_refs",
            "detector_refs",
            "operation_scope",
            "syntax_recognition",
            "operation_extraction",
            "semantic_modeling",
            "known_gaps",
            "abstention_conditions",
            "version_manifest_ref",
        },
        "semantic profile",
    )
    profile_id = _require_string(profile.get("profile_id"), "profile_id")
    entry_id = _require_string(profile.get("capability_entry_id"), "capability_entry_id")
    domain = _require_string(profile.get("domain"), f"{profile_id} domain")
    language = profile.get("language")
    package = profile.get("package")
    if language is not None:
        _require_string(language, f"{profile_id} language")
    if package is not None:
        _require_string(package, f"{profile_id} package")
    operation_scope = _string_list(profile.get("operation_scope"), "operation_scope", nonempty=True)
    for field, permitted in _PROFILE_STATES.items():
        if profile.get(field) not in permitted:
            raise CapabilityMatrixError(f"{profile_id} has invalid {field}")

    parser_refs = _record_refs(profile.get("parser_refs"), "parser_manifest", "parser_refs", True)
    parsers = _resolve_refs(parser_refs, parser_by_id, "parser")
    if language is not None and any(
        str(parser["language_or_surface"]).casefold() != str(language).casefold()
        for parser in parsers
    ):
        raise CapabilityMatrixError(f"{profile_id} parser language does not match profile")
    if profile["operation_extraction"] not in {"not_started", "planned"} and not any(
        "operation_extraction" in parser["capabilities"] for parser in parsers
    ):
        raise CapabilityMatrixError(f"{profile_id} claims operation extraction without a parser")
    if profile["syntax_recognition"] not in {"not_started", "planned"} and not any(
        {"inventory", "syntax_tree"}.intersection(parser["capabilities"]) for parser in parsers
    ):
        raise CapabilityMatrixError(f"{profile_id} claims syntax recognition without a parser")

    detector_refs = _record_refs(
        profile.get("detector_refs"), "detector_manifest", "detector_refs", False
    )
    detectors = _resolve_refs(detector_refs, detector_by_id, "detector")
    detector_entries = [
        _detector_entry(
            profile_id,
            domain,
            language,
            package,
            operation_scope,
            detector,
            qualification_by_id,
        )
        for detector in detectors
    ]
    detector_entries.sort(key=lambda item: str(item["detector_id"]))

    version_ref = _require_string(
        profile.get("version_manifest_ref"), f"{profile_id} version_manifest_ref"
    )
    version_manifest = version_by_id.get(version_ref)
    if version_manifest is None or version_manifest.get("profile_ref") != profile_id:
        raise CapabilityMatrixError(f"{profile_id} version manifest does not resolve exactly")

    known_gaps = [
        *_string_list(profile.get("known_gaps"), "known_gaps"),
        *_string_list(version_manifest.get("known_gaps"), "version known_gaps"),
    ]
    for parser in parsers:
        parser_id = str(parser["parser_id"])
        known_gaps.extend(
            f"Parser limitation ({parser_id}): {value}"
            for value in _string_list(parser.get("limitations", []), "parser limitations")
        )
        known_gaps.extend(
            f"Unsupported parser construct ({parser_id}): {value}"
            for value in _string_list(
                parser.get("unsupported_constructs", []), "unsupported constructs"
            )
        )
    for detector in detectors:
        detector_id = str(detector["detector_id"])
        known_gaps.extend(
            f"Detector limitation ({detector_id}): {value}"
            for value in _string_list(detector.get("limitations", []), "detector limitations")
        )
    abstention_conditions = _string_list(
        profile.get("abstention_conditions"), "abstention_conditions"
    )
    for detector in detectors:
        abstention_conditions.extend(
            _string_list(detector.get("abstain_when"), "detector abstain_when", nonempty=True)
        )
    if not detectors:
        known_gaps.append(
            "No production detector manifest is attached; no detector-dependent issue class was checked."
        )
        abstention_conditions.append(
            "Detector-dependent assessment is unavailable because this profile has no detector manifest."
        )

    return {
        "entry_id": entry_id,
        "domain": domain,
        "language": language,
        "package": package,
        "operation_scope": operation_scope,
        "syntax_recognition": profile["syntax_recognition"],
        "operation_extraction": profile["operation_extraction"],
        "semantic_modeling": profile["semantic_modeling"],
        "detectors": detector_entries,
        "known_gaps": sorted(set(known_gaps)),
        "abstention_conditions": sorted(set(abstention_conditions)),
        "tested_versions": _string_list(version_manifest.get("tested_versions"), "tested_versions"),
        "inferred_compatibility": _string_list(
            version_manifest.get("inferred_compatibility"), "inferred_compatibility"
        ),
        "domain_wide_validation_claim_allowed": False,
    }


def _detector_entry(
    profile_id: str,
    domain: str,
    language: Any,
    package: Any,
    operation_scope: list[str],
    detector: dict[str, Any],
    qualification_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    detector_id = str(detector["detector_id"])
    if domain not in detector["domains"]:
        raise CapabilityMatrixError(f"{detector_id} does not declare {profile_id} domain")
    if language is not None and detector["languages"] and language not in detector["languages"]:
        raise CapabilityMatrixError(f"{detector_id} does not declare {profile_id} language")
    if not set(operation_scope).issubset(detector["supported_operations"]):
        raise CapabilityMatrixError(f"{detector_id} does not cover the profile operation scope")
    if package is not None and not any(
        str(package).casefold() in str(value).casefold()
        for value in detector["package_constraints"]
    ):
        raise CapabilityMatrixError(f"{detector_id} has no matching package constraint")

    maturity = str(detector["maturity"])
    outputs = _string_list(detector.get("permitted_output_types"), "permitted_output_types", True)
    strongest = max(outputs, key=lambda output: _OUTPUT_RANK[output])
    binding_grants = _binding_grant_entries(detector, qualification_by_id)
    if maturity == "experimental":
        if strongest == "finding":
            raise CapabilityMatrixError("experimental detector cannot expose Finding capability")
        entry: dict[str, Any] = {
            "detector_id": detector_id,
            "maturity": maturity,
            "qualification_ref": None,
            "strongest_output_type": strongest,
            "review_basis": "not_qualified",
        }
        if binding_grants:
            entry["binding_grants"] = binding_grants
        return entry
    if maturity not in {"validated", "publication_grade"}:
        raise CapabilityMatrixError(f"unsupported detector maturity: {maturity}")
    validation = detector.get("validation")
    if not isinstance(validation, dict):
        raise CapabilityMatrixError(f"{detector_id} lacks validation metadata")
    qualification_id = validation.get("qualification_record_ref")
    if not isinstance(qualification_id, str):
        raise CapabilityMatrixError(f"{detector_id} lacks an exact qualification reference")
    qualification = qualification_by_id.get(qualification_id)
    if qualification is None:
        raise CapabilityMatrixError(f"{detector_id} qualification reference is unresolved")
    if (
        qualification.get("detector_id") != detector_id
        or qualification.get("detector_version") != detector.get("detector_version")
        or qualification.get("outcome") != "promoted"
        or qualification.get("effective_maturity") != maturity
        or qualification.get("review_basis") != validation.get("qualification_review_basis")
    ):
        raise CapabilityMatrixError(f"{detector_id} qualification envelope does not match")
    entry = {
        "detector_id": detector_id,
        "maturity": maturity,
        "qualification_ref": qualification_id,
        "strongest_output_type": strongest,
        "review_basis": qualification["review_basis"],
    }
    if binding_grants:
        entry["binding_grants"] = binding_grants
    return entry


def _binding_grant_entries(
    detector: dict[str, Any], qualification_by_id: dict[str, dict[str, Any]]
) -> list[dict[str, str]]:
    validation = detector.get("validation")
    if not isinstance(validation, dict):
        raise CapabilityMatrixError(f"{detector.get('detector_id')} lacks validation metadata")
    qualification_ids = validation.get("qualification_record_refs", [])
    if not isinstance(qualification_ids, list) or not all(
        isinstance(item, str) and item for item in qualification_ids
    ):
        raise CapabilityMatrixError("qualification_record_refs must be an array of identifiers")
    if qualification_ids != sorted(set(qualification_ids)):
        raise CapabilityMatrixError("qualification_record_refs must be unique and sorted")

    grants: list[dict[str, str]] = []
    for qualification_id in qualification_ids:
        qualification = qualification_by_id.get(qualification_id)
        scope = qualification.get("binding_scope") if isinstance(qualification, dict) else None
        if not isinstance(scope, dict):
            raise CapabilityMatrixError("binding-scoped qualification reference is unresolved")
        binding_id = scope.get("binding_id")
        check_id = scope.get("check_id")
        pin = (
            method_conflict_grant_pins.GRANT_PINS.get(binding_id)
            if isinstance(binding_id, str)
            else None
        )
        if pin is not None and not method_conflict_grant_pins.installed_pin_matches_live_identity(
            pin
        ):
            # Retained qualification history is not an installed live grant after a
            # check/adapter version change.  It contributes no capability authority.
            continue
        evidence = (
            method_conflict_grant_pins.load_method_conflict_grant_evidence(pin)
            if pin is not None
            else None
        )
        if (
            not isinstance(binding_id, str)
            or not isinstance(check_id, str)
            or pin is None
            or evidence is None
            or dict(evidence[0]) != qualification
            or qualification.get("detector_id") != detector.get("detector_id")
            or qualification.get("detector_version") != detector.get("detector_version")
            or qualification.get("outcome") != "promoted"
            or qualification.get("effective_maturity") not in {"validated", "publication_grade"}
            or pin.qualification_id != qualification_id
        ):
            raise CapabilityMatrixError("binding-scoped qualification has no exact installed grant")
        grants.append(
            {
                "binding_id": binding_id,
                "check_id": check_id,
                "qualification_ref": qualification_id,
                "strongest_output_type": "finding",
            }
        )
    grants.sort(key=lambda item: item["binding_id"])
    if len({item["binding_id"] for item in grants}) != len(grants):
        raise CapabilityMatrixError("detector has duplicate binding-scoped grants")
    return grants


def _validate_version_manifests(
    versions: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    required = {
        "version_manifest_id",
        "profile_ref",
        "tested_versions",
        "inferred_compatibility",
        "evidence_refs",
        "known_gaps",
    }
    for version in versions:
        _require_exact_keys(version, required, "version manifest")
        identifier = _require_string(version.get("version_manifest_id"), "version_manifest_id")
        _require_string(version.get("profile_ref"), f"{identifier} profile_ref")
        tested = _string_list(version.get("tested_versions"), "tested_versions")
        inferred = _string_list(version.get("inferred_compatibility"), "inferred_compatibility")
        _string_list(version.get("evidence_refs"), "evidence_refs")
        _string_list(version.get("known_gaps"), "version known_gaps")
        if set(tested).intersection(inferred):
            raise CapabilityMatrixError("tested and inferred versions must remain distinct")
        result[identifier] = version
    return result


def _verify_builtin_implementation_digests(parsers: list[dict[str, Any]]) -> None:
    package_root = Path(__file__).resolve().parent
    for parser in parsers:
        extensions = parser.get("extensions")
        resource = (
            extensions.get("x-implementation-resource") if isinstance(extensions, dict) else None
        )
        if not isinstance(resource, str):
            raise CapabilityMatrixError("parser manifest lacks x-implementation-resource")
        relative = _safe_resource_path(resource)
        path = package_root / relative
        if (
            not path.is_file()
            or path.is_symlink()
            or not path.resolve().is_relative_to(package_root)
        ):
            raise CapabilityMatrixError("parser implementation resource does not resolve safely")
        if sha256_digest(path.read_bytes()) != parser.get("implementation_digest"):
            raise CapabilityMatrixError(
                f"parser implementation digest mismatch: {parser.get('parser_id')}"
            )


def _public_records(
    values: Any,
    record_type: str,
    id_field: str,
    registry: LocalSchemaRegistry,
) -> list[dict[str, Any]]:
    records = _private_records(values, id_field)
    for record in records:
        if record.get("record_type") != record_type:
            raise CapabilityMatrixError(f"expected {record_type} record")
        registry.validate(record)
    return records


def _public_versioned_records(
    values: Any,
    record_type: str,
    id_field: str,
    version_field: str,
    registry: LocalSchemaRegistry,
) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        raise CapabilityMatrixError("manifest records must be an array")
    records: list[dict[str, Any]] = []
    keys: list[tuple[str, str]] = []
    for value in values:
        if not isinstance(value, dict):
            raise CapabilityMatrixError("manifest record must be an object")
        identifier = _require_string(value.get(id_field), id_field)
        version = _require_string(value.get(version_field), version_field)
        key = (identifier, version)
        if key in keys:
            raise CapabilityMatrixError(
                f"duplicate versioned manifest record ID: {identifier}@{version}"
            )
        if value.get("record_type") != record_type:
            raise CapabilityMatrixError(f"expected {record_type} record")
        registry.validate(value)
        keys.append(key)
        records.append(value)
    if keys != sorted(keys, key=lambda item: (item[0], _semantic_version_key(item[1]))):
        raise CapabilityMatrixError(f"{id_field} records must be sorted by ID and semantic version")
    return records


def _latest_version_records(
    records: list[dict[str, Any]],
    id_field: str,
    version_field: str,
) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        identifier = _require_string(record.get(id_field), id_field)
        version = _require_string(record.get(version_field), version_field)
        current = by_id.get(identifier)
        if current is None or _semantic_version_key(version) > _semantic_version_key(
            _require_string(current.get(version_field), version_field)
        ):
            by_id[identifier] = record
    return [by_id[identifier] for identifier in sorted(by_id)]


def _semantic_version_key(value: str) -> tuple[int, int, int]:
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise CapabilityMatrixError(f"unsupported semantic version: {value!r}")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def _private_records(values: Any, id_field: str) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        raise CapabilityMatrixError("manifest records must be an array")
    records: list[dict[str, Any]] = []
    identifiers: list[str] = []
    for value in values:
        if not isinstance(value, dict):
            raise CapabilityMatrixError("manifest record must be an object")
        identifier = _require_string(value.get(id_field), id_field)
        if identifier in identifiers:
            raise CapabilityMatrixError(f"duplicate manifest record ID: {identifier}")
        identifiers.append(identifier)
        records.append(value)
    if identifiers != sorted(identifiers):
        raise CapabilityMatrixError(f"{id_field} records must be sorted")
    return records


def _record_refs(values: Any, record_type: str, field: str, nonempty: bool) -> list[dict[str, Any]]:
    if not isinstance(values, list) or (nonempty and not values):
        raise CapabilityMatrixError(
            f"{field} must be an array" + (" with entries" if nonempty else "")
        )
    refs: list[dict[str, Any]] = []
    identifiers: list[str] = []
    for value in values:
        if not isinstance(value, dict):
            raise CapabilityMatrixError(f"{field} entry must be an object")
        _require_exact_keys(value, {"record_type", "record_id"}, f"{field} entry")
        if value.get("record_type") != record_type:
            raise CapabilityMatrixError(f"{field} must reference {record_type}")
        identifier = _require_string(value.get("record_id"), f"{field} record_id")
        if identifier in identifiers:
            raise CapabilityMatrixError(f"{field} contains a duplicate reference")
        identifiers.append(identifier)
        refs.append(value)
    if identifiers != sorted(identifiers):
        raise CapabilityMatrixError(f"{field} must be sorted")
    return refs


def _resolve_refs(
    refs: list[dict[str, Any]],
    records: dict[str, dict[str, Any]],
    label: str,
) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for ref in refs:
        record = records.get(str(ref["record_id"]))
        if record is None:
            raise CapabilityMatrixError(f"unresolved {label} manifest reference")
        resolved.append(record)
    return resolved


def _load_canonical_object(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise CapabilityMatrixError(f"{label} must be a regular file")
    payload = path.read_bytes()
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, CapabilityMatrixError) as error:
        raise CapabilityMatrixError(f"{label} is not strict JSON") from error
    if not isinstance(value, dict):
        raise CapabilityMatrixError(f"{label} must be a JSON object")
    if payload != (canonical_json(value) + "\n").encode("utf-8"):
        raise CapabilityMatrixError(f"{label} must use canonical JSON bytes")
    return value


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CapabilityMatrixError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> Any:
    raise CapabilityMatrixError(f"non-finite JSON constant: {value}")


def _require_exact_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    observed = set(value)
    if observed != required:
        missing = sorted(required - observed)
        extra = sorted(observed - required)
        raise CapabilityMatrixError(f"{label} keys differ; missing={missing}, extra={extra}")


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise CapabilityMatrixError(f"{label} must be a non-empty string")
    return value


def _require_digest(value: Any, label: str) -> str:
    digest = _require_string(value, label)
    if len(digest) != 71 or not digest.startswith("sha256:"):
        raise CapabilityMatrixError(f"{label} must be a SHA-256 digest")
    try:
        int(digest[7:], 16)
    except ValueError as error:
        raise CapabilityMatrixError(f"{label} must be a SHA-256 digest") from error
    return digest


def _string_list(value: Any, label: str, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        raise CapabilityMatrixError(f"{label} must be a string array")
    if not all(isinstance(item, str) and item for item in value):
        raise CapabilityMatrixError(f"{label} must contain only non-empty strings")
    result = [str(item) for item in value]
    if len(result) != len(set(result)):
        raise CapabilityMatrixError(f"{label} contains duplicates")
    return result


def _safe_relative_path(value: str) -> Path:
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts or len(candidate.parts) != 1:
        raise CapabilityMatrixError("capability collection path must be one safe filename")
    return Path(candidate.as_posix())


def _safe_resource_path(value: str) -> Path:
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise CapabilityMatrixError("implementation resource must be a safe relative path")
    return Path(candidate.as_posix())
