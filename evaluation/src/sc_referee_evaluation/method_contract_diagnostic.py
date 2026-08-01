from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from sc_referee.agent_protocol import load_audit_status
from sc_referee.capability_matrix import (
    default_capability_manifest_root,
    load_capability_detector_manifest,
)
from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.detectors.bounded_reported_method_contract import (
    BoundedReportedMethodContractConflictDetector,
)
from sc_referee.method_contracts import (
    EXPECTED_COUNT_PROFILE_ID,
    EXPECTED_COUNT_PROFILE_VERSION,
    EXPECTED_COUNT_REQUIRED_DIMENSIONS,
    expected_count_dimension_values,
    validate_expected_count_profile,
)
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.storage.layout import AuditLayout
from sc_referee.version import SCHEMA_VERSION

_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")


class MethodContractDiagnosticError(ValueError):
    """An answer-side method diagnostic violates the closed public-development profile."""


def diagnose_genebench_method_contract_conflict(
    audit_root: Path,
    schema_root: Path,
    reference_profile: object,
    *,
    reference_id: str,
    reference_content_digest: str,
    diagnosed_at: str,
    output: Path,
) -> dict[str, Any]:
    """Evaluate one post-lock reference profile without mutating production audit evidence."""

    if output.exists() or output.is_symlink():
        raise MethodContractDiagnosticError(f"diagnostic output already exists: {output}")
    if not reference_id.strip() or not _DIGEST.fullmatch(reference_content_digest):
        raise MethodContractDiagnosticError(
            "reference method requires a durable identifier and canonical content digest"
        )
    try:
        status = load_audit_status(audit_root, schema_root)
        profile = validate_expected_count_profile(reference_profile)
    except (OSError, ValueError) as error:
        raise MethodContractDiagnosticError(str(error)) from error
    if not status.terminal or status.model_access_after_lock is not False:
        raise MethodContractDiagnosticError(
            "diagnostic requires a terminal audit with verified absence of post-lock model access"
        )
    layout = AuditLayout(audit_root.resolve())
    bundle = _read_object(layout.bundle_path, "audit bundle")
    locked = _read_object(layout.lock_path, "semantic lock")
    if _timestamp(diagnosed_at) < _timestamp(str(locked.get("locked_at", ""))):
        raise MethodContractDiagnosticError("diagnostic cannot precede semantic lock")
    if bundle.get("findings") != []:
        raise MethodContractDiagnosticError(
            "diagnostic profile requires the unchanged zero-Finding production audit"
        )
    claims = [
        item
        for item in bundle.get("claims", [])
        if item.get("claim_kind") == "quantitative"
        and item.get("extensions", {}).get("x-method-profile-id") == EXPECTED_COUNT_PROFILE_ID
    ]
    if len(claims) != 1:
        raise MethodContractDiagnosticError(
            "diagnostic requires one exact expected-count quantitative Claim"
        )
    claim = copy.deepcopy(claims[0])
    production_results = [
        item
        for item in bundle.get("detector_results", [])
        if item.get("detector_id") == BoundedReportedMethodContractConflictDetector.detector_id
        and item.get("target_refs") == [typed_ref("claim", str(claim["claim_id"]))]
    ]
    if len(production_results) != 1 or production_results[0].get("state") != (
        "insufficient_semantics"
    ):
        raise MethodContractDiagnosticError(
            "production audit did not preserve the intended method as insufficient semantics"
        )
    contracts = [
        copy.deepcopy(item)
        for item in bundle.get("scientific_contracts", [])
        if item.get("contract_id") == claim.get("scientific_contract_id")
    ]
    if len(contracts) != 1:
        raise MethodContractDiagnosticError("diagnostic Claim contract is unavailable")
    contract = contracts[0]
    source_ref = {
        "source_kind": "external_uri",
        "locator": reference_id,
        "content_digest": reference_content_digest,
        "external": True,
    }
    intended_assertions: list[dict[str, Any]] = []
    for dimension, value in expected_count_dimension_values(profile).items():
        assertion_id = stable_id(
            "assertion-evaluation-reference-intent",
            status.semantic_lock_digest,
            reference_content_digest,
            dimension,
        )
        assertion = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "semantic_assertion",
            "assertion_id": assertion_id,
            "audit_run_id": str(locked["audit_run_id"]),
            "subject_ref": typed_ref("claim", str(claim["claim_id"])),
            "predicate": f"verified_intended_{dimension}",
            "object": value,
            "semantic_role": "intended",
            "assertion_class": "deterministic_derivation",
            "epistemic_status": "accepted",
            "authority_scope": "scientific_intent",
            "independently_checkable": True,
            "finding_eligibility": "eligible",
            "verification": {
                "status": "verified",
                "method": "deterministic_comparison",
                "validator_id": "evaluation:genebench-reference-method-profile-v1",
                "verified_at": diagnosed_at,
            },
            "certainty": {
                "level": "explicit",
                "basis": (
                    "The answer-side reference explicitly supplies the complete benchmark "
                    "scoring-method profile."
                ),
            },
            "rationale": (
                "This assertion exists only in an answer-side diagnostic copy. It establishes "
                "the public benchmark scoring contract, not production scientific intent."
            ),
            "source_refs": [copy.deepcopy(source_ref)],
            "provenance": controller_provenance(
                "evaluation_reference_method_projection_v1", diagnosed_at
            ),
            "extensions": {
                "x-evaluation-only": True,
                "x-reference-id": reference_id,
                "x-reference-content-digest": reference_content_digest,
                "x-production-intent-authority": False,
                "x-profile-id": EXPECTED_COUNT_PROFILE_ID,
                "x-profile-version": EXPECTED_COUNT_PROFILE_VERSION,
            },
        }
        intended_assertions.append(assertion)
        contract["dimensions"][dimension] = {
            "state": "known",
            "assertion_ids": [assertion_id],
            "accepted_assertion_ids": [assertion_id],
            "notes": "Answer-side benchmark diagnostic projection only.",
        }
    if set(EXPECTED_COUNT_REQUIRED_DIMENSIONS) != {
        item["predicate"].removeprefix("verified_intended_") for item in intended_assertions
    }:
        raise MethodContractDiagnosticError("reference method projection is incomplete")
    diagnostic_lock = copy.deepcopy(locked)
    diagnostic_lock["scientific_contracts"] = [contract]
    diagnostic_lock["semantic_assertions"] = [
        *[
            copy.deepcopy(item)
            for item in bundle.get("semantic_assertions", [])
            if item.get("subject_ref") == typed_ref("claim", str(claim["claim_id"]))
            and item.get("predicate") == "reported_expected_count_background_profile"
        ],
        *intended_assertions,
    ]
    diagnostic_lock["claims"] = [claim]
    manifest = load_capability_detector_manifest(
        default_capability_manifest_root(),
        schema_root,
        BoundedReportedMethodContractConflictDetector.detector_id,
    )
    detector = BoundedReportedMethodContractConflictDetector(manifest)
    result = detector.evaluate(diagnostic_lock, claim)
    LocalSchemaRegistry(schema_root).validate(result)
    if result.get("state") != "evaluation_finding_candidate":
        raise MethodContractDiagnosticError(
            "answer-side reference did not produce the expected exact conflict candidate"
        )

    diagnostic: dict[str, Any] = {
        "evaluation_protocol_version": "0.2.0",
        "method_contract_diagnostic_version": "0.1.0",
        "record_type": "evaluation_genebench_method_contract_diagnostic",
        "diagnostic_id": stable_id(
            "genebench-method-contract-diagnostic",
            status.semantic_lock_digest,
            reference_content_digest,
            str(result["result_id"]),
        ),
        "diagnosed_at": diagnosed_at,
        "case": {
            "reference_id": reference_id,
            "corpus_partition": "public_development",
        },
        "production_audit": {
            "audit_run_id": status.audit_run_id,
            "semantic_lock_digest": status.semantic_lock_digest,
            "model_access_after_lock": False,
            "finding_count": 0,
            "detector_result_id": production_results[0]["result_id"],
            "detector_state": production_results[0]["state"],
            "unchanged": True,
        },
        "answer_side_reference": {
            "content_digest": reference_content_digest,
            "profile": profile,
            "production_intent_authority": False,
        },
        "diagnostic_detector_result": result,
        "metric_eligible": False,
        "held_out_eligible": False,
        "promotion_evidence_eligible": False,
        "project_code_executed_by_diagnostic": False,
        "model_invoked_by_diagnostic": False,
        "non_inferences": [
            "The answer-side reference was not available to the production audit.",
            "The diagnostic candidate is not a production Finding.",
            "The comparison does not establish which code ran or why numeric values differed.",
            "A public-development case cannot qualify or promote the detector.",
        ],
    }
    diagnostic["diagnostic_digest"] = semantic_digest(diagnostic)
    write_normalized_json_once(output, diagnostic)
    return diagnostic


def _read_object(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise MethodContractDiagnosticError(f"{label} is unavailable or unsafe")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise MethodContractDiagnosticError(f"{label} must contain one JSON object")
    return value


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise MethodContractDiagnosticError(f"invalid timestamp: {value!r}") from error
    if parsed.tzinfo is None:
        raise MethodContractDiagnosticError("timestamps must include a timezone")
    return parsed


__all__ = [
    "MethodContractDiagnosticError",
    "diagnose_genebench_method_contract_conflict",
]
