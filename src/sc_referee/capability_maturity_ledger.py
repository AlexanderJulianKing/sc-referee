from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest

DimensionState = Literal["supported", "not_evidenced"]

DIMENSIONS = (
    "inventoried",
    "recognized",
    "structurally_verified",
    "impact_tested",
    "evaluation_candidate",
    "finding_qualified",
)


class CapabilityMaturityLedgerError(ValueError):
    """Raised when the private maturity ledger cannot be derived fail-closed."""


def default_capability_maturity_source_root() -> Path:
    return Path(__file__).resolve().parent / "resources"


def build_capability_maturity_ledger(source_root: Path) -> dict[str, Any]:
    """Build a private documentation ledger without changing public record meaning."""

    root = source_root.resolve()
    source_paths = {
        "calculation_registry": root / "calculation-check-manifests-v13" / "registry.json",
        "scientific_registry": root / "scientific-check-manifests-v1" / "registry.json",
        "capability_profiles": root / "capability-manifests-v1" / "profile-manifests.json",
        "capability_detectors": root / "capability-manifests-v1" / "detector-manifests.json",
        "capability_qualifications": root
        / "capability-manifests-v1"
        / "qualification-manifests.json",
    }
    sources = {key: _load_canonical_object(path) for key, path in source_paths.items()}
    entries = [
        *_calculation_entries(sources["calculation_registry"]),
        *_scientific_check_entries(sources["scientific_registry"]),
        *_capability_profile_entries(
            _records(sources["capability_profiles"], "profile manifests"),
            _records(sources["capability_detectors"], "detector manifests"),
            _records(sources["capability_qualifications"], "qualification manifests"),
        ),
    ]
    entries.sort(key=lambda item: (str(item["capability_kind"]), str(item["capability_id"])))
    _require_unique_ids(entries)
    ledger: dict[str, Any] = {
        "profile": "sc-referee-private-capability-maturity-ledger-v1",
        "dimensions": list(DIMENSIONS),
        "entries": entries,
        "source_digests": {
            key: sha256_digest(path.read_bytes()) for key, path in sorted(source_paths.items())
        },
        "non_inferences": [
            "A supported earlier dimension does not establish any later dimension.",
            "A supported dimension describes a bounded implementation path, not completion in every audit.",
            "A not_evidenced dimension is not converted into a pass, negative result, or correctness claim.",
            "This private documentation ledger grants no detector or Finding authority.",
        ],
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    return ledger


def _calculation_entries(registry: dict[str, Any]) -> list[dict[str, Any]]:
    modules = registry.get("modules")
    if not isinstance(modules, list):
        raise CapabilityMaturityLedgerError("calculation registry modules must be an array")
    production_permitted = registry.get("production_finding_permitted") is True
    entries: list[dict[str, Any]] = []
    for module in modules:
        if not isinstance(module, dict):
            raise CapabilityMaturityLedgerError("calculation module must be an object")
        manifest = module.get("check_manifest")
        if not isinstance(manifest, dict) or not isinstance(manifest.get("check_id"), str):
            raise CapabilityMaturityLedgerError("calculation module lacks one check manifest")
        check_id = str(manifest["check_id"])
        adapter_ids = _string_ids(module.get("adapter_manifests"), "adapter_id")
        comparison = module.get("comparison_relation")
        output_ceiling = module.get("output_ceiling")
        entries.append(
            _entry(
                check_id,
                "calculation_check",
                {
                    "inventoried": _supported(f"check manifest {check_id}"),
                    "recognized": (
                        _supported(*(f"adapter {item}" for item in adapter_ids))
                        if adapter_ids
                        else _not_evidenced("no calculation adapter is registered")
                    ),
                    "structurally_verified": _not_evidenced(
                        "the calculation registry declares no applicability-and-safeguard verifier"
                    ),
                    "impact_tested": (
                        _supported(f"exact comparison relation {comparison}")
                        if isinstance(comparison, str) and comparison
                        else _not_evidenced("no exact comparison relation is registered")
                    ),
                    "evaluation_candidate": (
                        _supported("calculation output ceiling is evaluation_candidate")
                        if output_ceiling == "evaluation_candidate"
                        else _not_evidenced(
                            "calculation output ceiling is not evaluation_candidate"
                        )
                    ),
                    "finding_qualified": (
                        _supported("calculation registry explicitly permits production Findings")
                        if production_permitted
                        else _not_evidenced(
                            "calculation registry explicitly denies production Finding permission"
                        )
                    ),
                },
            )
        )
    return entries


def _scientific_check_entries(registry: dict[str, Any]) -> list[dict[str, Any]]:
    modules = registry.get("modules")
    bindings = registry.get("method_conflict_bindings")
    if not isinstance(modules, list) or not isinstance(bindings, list):
        raise CapabilityMaturityLedgerError("scientific registry collections must be arrays")
    binding_by_check: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        if not isinstance(binding, dict) or not isinstance(binding.get("check_id"), str):
            raise CapabilityMaturityLedgerError("method-conflict binding lacks a check ID")
        check_id = str(binding["check_id"])
        if check_id in binding_by_check:
            raise CapabilityMaturityLedgerError("duplicate method-conflict binding for one check")
        binding_by_check[check_id] = binding

    entries: list[dict[str, Any]] = []
    for module in modules:
        if not isinstance(module, dict) or not isinstance(module.get("check_id"), str):
            raise CapabilityMaturityLedgerError("scientific module lacks a check ID")
        check_id = str(module["check_id"])
        adapters = _string_ids(module.get("adapters"), "adapter_id")
        structural_basis = _binding_structural_basis(module, binding_by_check.get(check_id))
        entries.append(
            _entry(
                check_id,
                "scientific_check",
                {
                    "inventoried": _supported(f"scientific check manifest {check_id}"),
                    "recognized": (
                        _supported(*(f"adapter {item}" for item in adapters))
                        if adapters
                        else _not_evidenced("no scientific evidence adapter is registered")
                    ),
                    "structurally_verified": (
                        _supported(*structural_basis)
                        if structural_basis
                        else _not_evidenced(
                            "no exact digest-bound finite method-conflict binding is registered"
                        )
                    ),
                    "impact_tested": _not_evidenced(
                        "the scientific-check registry declares no impact adapter"
                    ),
                    "evaluation_candidate": _not_evidenced(
                        "the check binding does not independently declare candidate qualification evidence"
                    ),
                    "finding_qualified": _not_evidenced(
                        "the check binding does not independently declare a promoted qualification"
                    ),
                },
            )
        )
    return entries


def _capability_profile_entries(
    profiles: list[dict[str, Any]],
    detectors: list[dict[str, Any]],
    qualifications: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    detector_by_id = _index(detectors, "detector_id", "detector")
    qualification_by_id = _index(qualifications, "qualification_id", "qualification")
    entries: list[dict[str, Any]] = []
    for profile in profiles:
        capability_id = profile.get("capability_entry_id")
        if not isinstance(capability_id, str) or not capability_id:
            raise CapabilityMaturityLedgerError("capability profile lacks an entry ID")
        parser_ids = _record_ref_ids(profile.get("parser_refs"), "parser_manifest")
        detector_ids = _record_ref_ids(profile.get("detector_refs"), "detector_manifest")
        bound_detectors = [detector_by_id[item] for item in detector_ids if item in detector_by_id]
        inventoried = bool(parser_ids) and profile.get("syntax_recognition") != "not_started"
        recognized = (
            profile.get("operation_extraction") != "not_started"
            and profile.get("semantic_modeling") != "not_started"
        )
        structural_detectors = [
            item for item in bound_detectors if _detector_has_structural_evidence(item)
        ]
        candidate_detectors = [
            item for item in bound_detectors if _detector_has_evaluation_evidence(item)
        ]
        qualified_detectors = [
            item
            for item in bound_detectors
            if _detector_has_qualification(item, qualification_by_id)
        ]
        entries.append(
            _entry(
                capability_id,
                "capability_profile",
                {
                    "inventoried": (
                        _supported(*(f"parser {item}" for item in parser_ids))
                        if inventoried
                        else _not_evidenced("profile has no active syntax-inventory path")
                    ),
                    "recognized": (
                        _supported(
                            f"operation_extraction={profile.get('operation_extraction')}",
                            f"semantic_modeling={profile.get('semantic_modeling')}",
                        )
                        if recognized
                        else _not_evidenced(
                            "operation extraction and semantic modeling are not both active"
                        )
                    ),
                    "structurally_verified": (
                        _supported(
                            *(
                                f"finite detector envelope {item['detector_id']}"
                                for item in structural_detectors
                            )
                        )
                        if structural_detectors
                        else _not_evidenced(
                            "no bound detector declares finite counterevidence and control fixtures"
                        )
                    ),
                    "impact_tested": _not_evidenced(
                        "capability manifests contain no explicit impact-adapter reference"
                    ),
                    "evaluation_candidate": (
                        _supported(
                            *(
                                f"development evaluation {item['detector_id']}"
                                for item in candidate_detectors
                            )
                        )
                        if candidate_detectors
                        else _not_evidenced(
                            "no bound detector declares a positive development evaluation path"
                        )
                    ),
                    "finding_qualified": (
                        _supported(
                            *(
                                f"promoted qualification for {item['detector_id']}"
                                for item in qualified_detectors
                            )
                        )
                        if qualified_detectors
                        else _not_evidenced(
                            "no exact promoted qualification is bound to a Finding-permitted detector"
                        )
                    ),
                },
            )
        )
    return entries


def _entry(
    capability_id: str, capability_kind: str, dimensions: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    if tuple(dimensions) != DIMENSIONS:
        raise CapabilityMaturityLedgerError("entry must report exactly six ordered dimensions")
    return {
        "capability_id": capability_id,
        "capability_kind": capability_kind,
        "dimensions": dimensions,
    }


def _supported(*basis: str) -> dict[str, Any]:
    return {"state": "supported", "basis": list(basis)}


def _not_evidenced(reason: str) -> dict[str, Any]:
    return {"state": "not_evidenced", "basis": [], "reason": reason}


def _binding_structural_basis(module: dict[str, Any], binding: dict[str, Any] | None) -> list[str]:
    if binding is None:
        return []
    exact_identity = binding.get("check_version") == module.get("check_version") and binding.get(
        "check_manifest_digest"
    ) == module.get("manifest_digest")
    finite = all(
        isinstance(binding.get(field), list) and bool(binding[field])
        for field in (
            "counterevidence_predicates",
            "required_assertion_roles",
            "required_evidence_planes",
            "required_semantic_roles",
        )
    )
    if not exact_identity or not finite:
        return []
    return [
        f"binding {binding.get('binding_id')}",
        f"detector {binding.get('detector_id')}",
    ]


def _detector_has_structural_evidence(detector: dict[str, Any]) -> bool:
    fixtures = detector.get("test_fixtures")
    return (
        isinstance(detector.get("counterevidence_protocol"), list)
        and bool(detector["counterevidence_protocol"])
        and isinstance(detector.get("required_evidence"), list)
        and bool(detector["required_evidence"])
        and isinstance(fixtures, dict)
        and all(
            bool(fixtures.get(role))
            for role in ("positive", "counterevidence", "verified_good_negative")
        )
    )


def _detector_has_evaluation_evidence(detector: dict[str, Any]) -> bool:
    validation = detector.get("validation")
    fixtures = detector.get("test_fixtures")
    extensions = detector.get("extensions")
    return (
        detector.get("maturity") == "experimental"
        and isinstance(validation, dict)
        and validation.get("status") == "development_only"
        and isinstance(validation.get("evaluation_ref"), str)
        and bool(validation["evaluation_ref"])
        and isinstance(fixtures, dict)
        and bool(fixtures.get("positive"))
        and isinstance(extensions, dict)
        and extensions.get("x-production-finding-permitted") is False
    )


def _detector_has_qualification(
    detector: dict[str, Any], qualification_by_id: dict[str, dict[str, Any]]
) -> bool:
    validation = detector.get("validation")
    extensions = detector.get("extensions")
    if not isinstance(validation, dict) or not isinstance(extensions, dict):
        return False
    qualification_id = validation.get("qualification_record_ref")
    if not isinstance(qualification_id, str) or not qualification_id:
        return False
    qualification = qualification_by_id.get(qualification_id)
    return bool(
        qualification
        and qualification.get("detector_id") == detector.get("detector_id")
        and qualification.get("outcome") == "promoted"
        and qualification.get("effective_maturity") == "validated"
        and extensions.get("x-production-finding-permitted") is True
    )


def _load_canonical_object(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise CapabilityMaturityLedgerError(f"missing regular source file: {path}")
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CapabilityMaturityLedgerError(f"invalid JSON source: {path}") from error
    if not isinstance(value, dict) or canonical_json(value).encode("utf-8") != raw.rstrip(b"\n"):
        raise CapabilityMaturityLedgerError(f"source is not one canonical JSON object: {path}")
    return value


def _records(collection: dict[str, Any], label: str) -> list[dict[str, Any]]:
    records = collection.get("records")
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise CapabilityMaturityLedgerError(f"{label} must contain object records")
    return records


def _string_ids(value: object, key: str) -> list[str]:
    if not isinstance(value, list):
        return []
    result = [
        str(item[key])
        for item in value
        if isinstance(item, dict) and isinstance(item.get(key), str)
    ]
    return sorted(set(result))


def _record_ref_ids(value: object, record_type: str) -> list[str]:
    if not isinstance(value, list):
        return []
    result = [
        str(item["record_id"])
        for item in value
        if isinstance(item, dict)
        and item.get("record_type") == record_type
        and isinstance(item.get("record_id"), str)
    ]
    return sorted(set(result))


def _index(records: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        value = record.get(key)
        if not isinstance(value, str) or not value or value in result:
            raise CapabilityMaturityLedgerError(f"invalid or duplicate {label} ID")
        result[value] = record
    return result


def _require_unique_ids(entries: list[dict[str, Any]]) -> None:
    identities = [(str(item["capability_kind"]), str(item["capability_id"])) for item in entries]
    if len(identities) != len(set(identities)):
        raise CapabilityMaturityLedgerError("capability ledger identities must be unique")
