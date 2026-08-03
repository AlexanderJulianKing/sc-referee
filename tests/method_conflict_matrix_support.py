from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

from sc_referee.core.ids import semantic_digest
from sc_referee.scientific_checks.core import MethodConflictBinding
from sc_referee.scientific_checks.profiles import scientific_check_release_registry


@dataclass(frozen=True)
class TargetRelation:
    relation_id: str
    check_id: str
    required_candidate_id: str
    conflicting_candidate_id: str


TARGET_RELATIONS = (
    TargetRelation(
        "founder-orientation",
        "check:founder-orientation-before-hmm-emission",
        "repair-before-emission",
        "use-supplied-orientation",
    ),
    TargetRelation(
        "directional-observation-error",
        "check:directional-measurement-error-interpretation",
        "direction-specific-decomposition",
        "symmetric-reported-average",
    ),
    TargetRelation(
        "within-stratum-calibration",
        "check:poststratified-misclassification-estimator",
        "constrained-cellwise-calibration-then-standardize",
        "aggregate-then-joint-calibration",
    ),
    TargetRelation(
        "model-based-expected-count",
        "check:expected-count-background-construction",
        "negative-binomial-model-prediction",
        "same-stratum-arithmetic-mean",
    ),
    TargetRelation(
        "recovered-technical-group-adjustment",
        "check:recoverable-technical-group-adjustment",
        "include-recovered-technical-group",
        "omit-unobserved-or-unlinked-technical-group",
    ),
    TargetRelation(
        "phase-split-mvmr-instrument-construction",
        "check:phase-split-mvmr-instrument-construction",
        "phase1-ld-conditional-signals-phase2-joint-coefficients",
        "phase1-marginal-signal-union-phase2-marginal-coefficients",
    ),
    TargetRelation(
        "direct-continuous-copy-dosage",
        "check:classifier-derived-copy-dosage-representation",
        "direct-continuous-calibrated-copy-dosage",
        "continuous-posterior-expected-copy-dosage",
    ),
    TargetRelation(
        "purity-copy-adjusted-clonality",
        "check:somatic-clonality-representation",
        "purity-copy-adjusted-clonal-fraction-window",
        "direct-local-copy-number-ceiling",
    ),
    TargetRelation(
        "joint-local-perturbation-model",
        "check:local-perturbation-regression-specification",
        "joint-target-axes-with-guide-nuisance-terms",
        "external-subtraction-then-single-axis",
    ),
    TargetRelation(
        "full-map-exposure",
        "check:full-map-ancestry-exposure",
        "full-map-exposure",
        "called-tract-exposure",
    ),
)


def binding_for(relation: TargetRelation) -> MethodConflictBinding:
    return next(
        binding
        for binding in scientific_check_release_registry().method_conflict_bindings
        if binding.check_id == relation.check_id
    )


def operand_for(relation: TargetRelation, candidate_id: str) -> object:
    module = next(
        module
        for module in scientific_check_release_registry().modules
        if module.manifest.check_id == relation.check_id
    )
    return next(
        candidate.operand.value
        for candidate in module.manifest.requirement_candidates
        if candidate.candidate_id == candidate_id
    )


def method_conflict_case(
    relation: TargetRelation,
    *,
    required_candidate_id: str,
    observed_candidate_id: str,
    namespace: str = "primary",
    layout: Literal["writer_chain", "direct_artifact"] = "writer_chain",
) -> tuple[dict[str, Any], dict[str, Any]]:
    binding = binding_for(relation)
    requirement = operand_for(relation, required_candidate_id)
    observed = operand_for(relation, observed_candidate_id)
    subject = _ref("publication_surface", f"publication-surface:{namespace}")
    source_ref = _ref("file_record", f"file:{namespace}")
    operation_ref = _ref("operation", f"operation:{namespace}")
    artifact_ref = _ref("artifact", f"artifact:{namespace}")
    if layout == "writer_chain":
        scope_path = [
            {
                "source_ref": source_ref,
                "relation": "contains_unique_static_selected_output_writer",
                "target_ref": operation_ref,
            },
            {
                "source_ref": operation_ref,
                "relation": "declares_selected_output_artifact",
                "target_ref": artifact_ref,
            },
            {
                "source_ref": artifact_ref,
                "relation": "selected_by_publication_surface",
                "target_ref": subject,
            },
        ]
        static_subject = source_ref
    else:
        scope_path = [
            {
                "source_ref": artifact_ref,
                "relation": "selected_source_artifact_of_publication_surface",
                "target_ref": subject,
            }
        ]
        static_subject = artifact_ref
    scope_digest = semantic_digest(scope_path)
    question_id = f"question:{namespace}"
    answer_id = f"answer:{namespace}"
    contract_id = f"contract:{namespace}"
    requirement_id = f"assertion-verified-posthoc-intent:{namespace}"
    answer_digest = "sha256:" + "c" * 64
    requirement_assertion = {
        "assertion_id": requirement_id,
        "subject_ref": subject,
        "predicate": f"verified_intended_{binding.dimension}",
        "object": requirement,
        "semantic_role": "intended",
        "assertion_class": "deterministic_derivation",
        "epistemic_status": "accepted",
        "authority_scope": "scientific_intent",
        "independently_checkable": True,
        "finding_eligibility": "ineligible",
        "verification": {"status": "verified", "method": "deterministic_comparison"},
        "source_refs": [_source(f"protocol-{namespace}.md", 3, "a")],
        "provenance": {"actor": {"actor_kind": "controller"}},
        "extensions": {
            "x-answer-ref": _ref("answer", answer_id),
            "x-answer-digest": answer_digest,
            "x-scientific-check-id": relation.check_id,
            "x-scientific-check-manifest-digest": binding.check_manifest_digest,
            "x-scientific-check-scope-join-digest": scope_digest,
        },
    }
    assertions = [requirement_assertion]
    observed_ids: list[str] = []
    for plane in binding.required_evidence_planes:
        assertion_id = f"assertion:{namespace}:{plane}"
        if plane == "reported_text":
            assertion = {
                "assertion_id": assertion_id,
                "subject_ref": artifact_ref,
                "predicate": f"reported_{binding.dimension}",
                "object": observed,
                "semantic_role": "reported",
                "assertion_class": "explicit_text_extraction",
                "epistemic_status": "accepted",
                "authority_scope": "reported_wording",
                "independently_checkable": True,
                "finding_eligibility": "ineligible",
                "verification": {"status": "verified", "method": "exact_quote_match"},
                "source_refs": [_source(f"report-{namespace}.md", 7, "b")],
                "provenance": {"actor": {"actor_kind": "parser"}},
                "extensions": {
                    "x-scientific-check-id": relation.check_id,
                    "x-scientific-check-scope-join-digest": scope_digest,
                },
            }
        else:
            assertion = {
                "assertion_id": assertion_id,
                "subject_ref": static_subject,
                "predicate": f"statically_observed_{binding.dimension}",
                "object": observed,
                "semantic_role": "observed",
                "assertion_class": "deterministic_derivation",
                "epistemic_status": "accepted",
                "authority_scope": "none",
                "independently_checkable": True,
                "finding_eligibility": "ineligible",
                "verification": {"status": "verified", "method": "structural_parser"},
                "source_refs": [_source(f"analysis-{namespace}.py", 11, "d")],
                "provenance": {"actor": {"actor_kind": "controller"}},
                "extensions": {
                    "x-scientific-check-id": relation.check_id,
                    "x-scientific-check-scope-join-digest": scope_digest,
                },
            }
        assertions.append(assertion)
        observed_ids.append(assertion_id)
    answer = {
        "answer_id": answer_id,
        "question_ref": _ref("material_question", question_id),
        "answer_value": {binding.dimension: requirement},
        "answer_digest": answer_digest,
        "respondent": {"actor_kind": "human", "actor_id": "scientist:matrix-reviewer"},
        "authority_scope": {
            "authority_kind": "scientific_intent",
            "subject_refs": [subject],
            "semantic_dimensions": [binding.dimension],
        },
    }
    contract = {
        "contract_id": contract_id,
        "scope": {"level": "analysis", "subject_refs": [subject]},
        "dimensions": {
            binding.dimension: {
                "state": "known",
                "assertion_ids": [requirement_id],
                "accepted_assertion_ids": [requirement_id],
            }
        },
    }
    locked = {
        "audit_run_id": f"audit:{namespace}",
        "locked_at": "2026-08-03T20:00:00Z",
        "scientific_contracts": [contract],
        "semantic_assertions": assertions,
        "answers": [answer],
        "file_records": [
            {
                "file_record_id": source_ref["record_id"],
                "entry_kind": "regular_file",
                "asset_identity_ref": _ref("asset_identity", f"identity:source:{namespace}"),
            }
        ],
        "operations": [
            {
                "operation_id": operation_ref["record_id"],
                "inspection_status": "supported",
                "implementation": {"name": "python.call:<dynamic>.write_text"},
                "output_refs": [artifact_ref],
            }
        ],
        "artifacts": [
            {
                "artifact_id": artifact_ref["record_id"],
                "kind": "report",
                "producer_operation_refs": [operation_ref],
                "asset_identity_ref": _ref("asset_identity", f"identity:artifact:{namespace}"),
            }
        ],
        "publication_surfaces": [
            {
                "publication_surface_id": subject["record_id"],
                "status": "resolved",
                "selection": {"kind": "resolved", "selected_surface_refs": [artifact_ref]},
            }
        ],
        "asset_identities": [
            {
                "asset_identity_id": f"identity:source:{namespace}",
                "asset_ref": source_ref,
                "tier": "full_digest",
            },
            {
                "asset_identity_id": f"identity:artifact:{namespace}",
                "asset_ref": artifact_ref,
                "tier": "full_digest",
            },
        ],
    }
    question = {
        "record_type": "material_question",
        "question_id": question_id,
        "status": "answered",
        "extensions": {
            "x-analysis-subject-ref": subject,
            "x-contract-ref": _ref("scientific_contract", contract_id),
            "x-output-ceiling": "question_only",
            "x-posthoc-comparison-forms": {binding.dimension: binding.comparison_form},
            "x-posthoc-reported-assertion-ids": {binding.dimension: observed_ids},
            "x-scientific-check-id": relation.check_id,
            "x-scientific-check-scope-join-path": scope_path,
            "x-scientific-check-scope-join-digest": scope_digest,
        },
    }
    return locked, question


def selected_report_assertion(locked: dict[str, Any]) -> dict[str, Any]:
    return next(
        assertion
        for assertion in locked["semantic_assertions"]
        if assertion.get("semantic_role") == "reported"
    )


def add_ambiguous_report_declaration(locked: dict[str, Any], namespace: str) -> None:
    copied = deepcopy(selected_report_assertion(locked))
    copied["assertion_id"] = f"assertion:{namespace}:extra-reported"
    locked["semantic_assertions"].append(copied)


def _ref(record_type: str, record_id: str) -> dict[str, str]:
    return {"record_type": record_type, "record_id": record_id}


def _source(path: str, line: int, digest_character: str) -> dict[str, Any]:
    return {
        "source_kind": "file_span",
        "path": path,
        "locator": f"{path}:{line}-{line}",
        "content_digest": "sha256:" + digest_character * 64,
        "start_line": line,
        "end_line": line,
        "quoted_text": "bounded method declaration",
    }
