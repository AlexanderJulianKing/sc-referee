from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sc_referee.core.ids import stable_id
from sc_referee.version import SCHEMA_VERSION


def build_directional_claim(
    *,
    literal: Mapping[str, Any],
    audit_run_id: str,
    scientific_contract_id: str,
    report_artifact_id: str,
    result_record_id: str,
    operation_record_id: str,
    input_artifact_ids: Sequence[str],
    result_scale: str,
    declared_comparison: str,
) -> dict[str, Any]:
    """Build a public Claim from exact text plus deterministic graph linkage."""

    source_ref = literal.get("source_ref")
    text = literal.get("text")
    subject = literal.get("literal_subject")
    predicate = literal.get("literal_predicate")
    comparison = literal.get("literal_comparison")
    direction = literal.get("direction")
    literal_object = literal.get("literal_object")
    if (
        not isinstance(source_ref, Mapping)
        or not isinstance(text, str)
        or not isinstance(subject, str)
        or not isinstance(predicate, str)
        or not isinstance(comparison, str)
        or not declared_comparison
        or direction not in {"positive", "negative"}
        or not isinstance(literal_object, str)
        or literal_object.casefold() != result_scale.casefold()
        or not input_artifact_ids
    ):
        raise ValueError(
            "directional claim requires exact literal fields and a matching observed scale label"
        )
    content_digest = source_ref.get("content_digest")
    start_line = source_ref.get("start_line")
    if not isinstance(content_digest, str) or not isinstance(start_line, int):
        raise ValueError("directional claim source identity is incomplete")
    claim_id = stable_id("claim", content_digest, str(start_line), text)
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "claim",
        "claim_id": claim_id,
        "audit_run_id": audit_run_id,
        "report_ref": {"record_type": "artifact", "record_id": report_artifact_id},
        "claim_status": "final",
        "claim_kind": "directional",
        "text": text,
        "source_refs": [dict(source_ref)],
        "scientific_contract_id": scientific_contract_id,
        "proposition": {
            "subject": subject,
            "predicate": predicate,
            "claim_strength": "ambiguous",
            "comparison": declared_comparison,
            "direction": direction,
            "scale": result_scale,
        },
        "lineage": {
            "status": "partial",
            "result_refs": [{"record_type": "observed_result", "record_id": result_record_id}],
            "operation_refs": [{"record_type": "operation", "record_id": operation_record_id}],
            "input_refs": [
                {"record_type": "artifact", "record_id": artifact_id}
                for artifact_id in input_artifact_ids
            ],
            "missing_links": [
                "The synthetic fixture has no project workflow Execution record or observed report-generation edge."
            ],
            "opaque_dependency_refs": [],
            "grades": {
                "report_origin": {
                    "status": "complete",
                    "record_refs": [{"record_type": "artifact", "record_id": report_artifact_id}],
                    "source_refs": [dict(source_ref)],
                    "limitations": [],
                },
                "result_origin": {
                    "status": "partial",
                    "record_refs": [
                        {"record_type": "observed_result", "record_id": result_record_id}
                    ],
                    "source_refs": [],
                    "limitations": [
                        "The fixture binds the result deterministically but does not observe report generation."
                    ],
                },
                "computational_origin": {
                    "status": "complete",
                    "record_refs": [{"record_type": "operation", "record_id": operation_record_id}],
                    "source_refs": [],
                    "limitations": [],
                },
                "input_origin": {
                    "status": "complete",
                    "record_refs": [
                        {"record_type": "artifact", "record_id": artifact_id}
                        for artifact_id in input_artifact_ids
                    ],
                    "source_refs": [],
                    "limitations": [],
                },
                "execution_origin": {
                    "status": "missing",
                    "record_refs": [],
                    "source_refs": [],
                    "limitations": ["No project workflow Execution record exists."],
                },
                "semantic_origin": {
                    "status": "partial",
                    "record_refs": [],
                    "source_refs": [dict(source_ref)],
                    "limitations": [
                        "The fixture declares comparison semantics while scientific strength remains unresolved."
                    ],
                },
            },
        },
        "extraction": {
            "method": "deterministic",
            "explicit_source_meaning": True,
            "independently_verified": True,
            "semantic_assertion_ids": [],
        },
        "extensions": {
            "x-extraction-basis": literal["extraction_basis"],
            "x-lineage-link-basis": "unique_supported_fixture_claim_and_result_path",
            "x-comparison-basis": "synthetic_fixture_semantic_declaration",
            "x-literal-comparison": comparison,
            "x-scientific-strength-unresolved": True,
        },
    }
