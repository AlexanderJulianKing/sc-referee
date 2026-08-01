from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.records.evaluation_candidate import evaluation_candidate_id
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.root_cause import adjudicated_root_cause_id
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.version import SCHEMA_VERSION

if TYPE_CHECKING:
    from sc_referee_evaluation.fixture import FixtureProofInputs


class Stage3ProtocolError(ValueError):
    """A Stage-3 packet, review, or case reconciliation failed closed."""


_REVIEWER_REQUIRED = {
    "provider",
    "agent_surface",
    "model_name",
    "model_id",
    "agent_version",
    "execution_context_id",
    "independent_context",
    "system_prompt_digest",
    "tool_policy_digest",
    "environment_digest",
}
_COMPARISON_ACCESS = {
    "scientific_label_frozen_before_detector_output": True,
    "detector_output_visible": True,
    "canonical_root_causes_visible": True,
    "other_stage3_reviews_hidden": True,
    "prior_review_context_reused": False,
}
_UNRESOLVED_DECISIONS = {
    "scientific_relation": "unresolved",
    "statement_boundedness": "unresolved",
    "affected_scope": "unresolved",
    "issue_class_relationship": "unresolved",
}
_EXCLUDED_LABELS = {"ambiguous_excluded", "insufficient_evidence", "adjudication_failed"}
_NONPOSITIVE_FIXTURES = {
    "verified_good_fixture",
    "scope_verified_good",
    "hard_negative_fixture",
    "ambiguous_fixture",
}
_QUALIFICATION_PROOF_FAMILIES = {
    "verified_good_fixture": "clean_execution",
    "hard_negative_fixture": "clean_execution",
    "scope_verified_good": "documented_external_execution",
    "static_scope_verified_good": "static_closed_scope",
    "static_scope_hard_negative": "static_closed_scope",
    "positive_issue_fixture": "positive_issue",
    "ambiguous_fixture": "excluded_ambiguous",
}


def build_stage3_review_packet(
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    stage1_freeze: dict[str, Any],
    scientific_label_freeze: dict[str, Any],
    audit_bundle: dict[str, Any],
    candidates: list[dict[str, Any]],
    adjudicated_root_causes: list[dict[str, Any]],
    detector_id: str,
    reviewer_agent: dict[str, Any],
    prompt_text: str,
    schema_root: Path,
    *,
    created_at: str,
) -> dict[str, Any]:
    """Build one post-freeze, answer-visible packet for a fresh Stage-3 context."""

    inputs = _validate_stage3_inputs(
        fixture,
        adjudication,
        stage1_freeze,
        scientific_label_freeze,
        audit_bundle,
        candidates,
        adjudicated_root_causes,
        detector_id,
        schema_root,
    )
    normalized_prompt = _normalize_prompt(prompt_text)
    missing = sorted(_REVIEWER_REQUIRED - set(reviewer_agent))
    context_id = str(reviewer_agent.get("execution_context_id", ""))
    provider = str(reviewer_agent.get("provider", ""))
    if missing or reviewer_agent.get("independent_context") is not True:
        raise Stage3ProtocolError(
            f"Stage-3 reviewer configuration is incomplete or not independent: {missing}"
        )
    if provider not in inputs["provider_families"]:
        raise Stage3ProtocolError(
            "Stage-3 reviewer provider is not represented in the scientific adjudication."
        )
    if context_id in inputs["prior_context_ids"]:
        raise Stage3ProtocolError("Stage-3 reviewer reuses a Stage-1 or Stage-2 context.")
    if _timestamp(created_at) <= _timestamp(str(scientific_label_freeze["frozen_at"])):
        raise Stage3ProtocolError("Stage-3 packet creation must follow scientific-label freeze.")

    expected_reviewer = deepcopy(reviewer_agent)
    expected_reviewer["task_prompt_digest"] = sha256_digest(normalized_prompt)
    packet: dict[str, Any] = {
        "evaluation_protocol_version": "0.2.0",
        "packet_kind": "stage3_detector_comparison",
        "case_id": adjudication["case_id"],
        "stage": "stage3_detector_comparison",
        "packet_created_at": created_at,
        "comparison_input_digest": inputs["comparison_input_digest"],
        "fixture": {
            "fixture_ref": _ref("benchmark_fixture", str(fixture["fixture_id"])),
            "fixture_digest": semantic_digest(fixture),
            "problem_id": fixture["problem_id"],
            "fixture_kind": fixture["fixture_kind"],
            "corpus_partition": fixture["corpus_partition"],
            "declared_scope": deepcopy(fixture["declared_scope"]),
        },
        "adjudication": {
            "adjudication_ref": _ref(
                "benchmark_adjudication", str(adjudication["adjudication_id"])
            ),
            "adjudication_digest": semantic_digest(adjudication),
            "label_status": adjudication["label_status"],
        },
        "scientific_label_freeze": {
            "freeze_digest": scientific_label_freeze["freeze_digest"],
            "frozen_at": scientific_label_freeze["frozen_at"],
            "stage1_freeze_digest": scientific_label_freeze["stage1_freeze_digest"],
            "detector_output_observed": scientific_label_freeze["detector_output_observed"],
        },
        "adjudicated_root_causes": [
            {"record": deepcopy(root), "record_digest": semantic_digest(root)}
            for root in inputs["roots"]
        ],
        "detector_output": {
            "audit_bundle_ref": _ref("audit_bundle", str(audit_bundle["bundle_id"])),
            "audit_bundle_digest": semantic_digest(audit_bundle),
            "semantic_lock_digest": audit_bundle["semantic_lock_digest"],
            "detector_id": detector_id,
            "detector_version": inputs["detector_version"],
            "detector_manifest_digest": inputs["detector_manifest_digest"],
            "source_detector_results": [deepcopy(value) for value in inputs["detector_results"]],
            "evaluation_candidates": [deepcopy(value) for value in inputs["candidates"]],
        },
        "root_cause_refs": [
            _ref("adjudicated_root_cause", str(root["adjudicated_root_cause_id"]))
            for root in inputs["roots"]
        ],
        "candidate_refs": [
            _ref("detector_evaluation_candidate", str(value["evaluation_candidate_id"]))
            for value in inputs["candidates"]
        ],
        "frozen_evidence": deepcopy(inputs["frozen_evidence"]),
        "prior_scientific_review_context_ids": sorted(inputs["prior_context_ids"]),
        "comparison_access_required": deepcopy(_COMPARISON_ACCESS),
        "prompt": {
            "normalized_text": normalized_prompt,
            "prompt_digest": sha256_digest(normalized_prompt),
        },
        "expected_reviewer_agent": expected_reviewer,
        "required_output": {
            "record_type": "stage3_comparison_review",
            "stage": "stage3_detector_comparison",
            "all_roots_accounted_for": True,
            "all_candidates_accounted_for": True,
            "confidence_used_for_equivalence": False,
            "other_stage3_reviews_hidden": True,
        },
    }
    packet["packet_digest"] = semantic_digest(packet)
    return packet


def validate_stage3_review_submission(
    review: dict[str, Any], packet: dict[str, Any], schema_root: Path
) -> None:
    """Validate one public Stage-3 review against its exact frozen packet."""

    _validate_packet_digest(packet)
    if packet.get("packet_kind") != "stage3_detector_comparison":
        raise Stage3ProtocolError("Stage-3 review packet has the wrong kind.")
    try:
        LocalSchemaRegistry(schema_root).validate(review)
    except RecordValidationError as error:
        raise Stage3ProtocolError(str(error)) from error
    if review.get("stage") != "stage3_detector_comparison" or review.get("case_id") != packet.get(
        "case_id"
    ):
        raise Stage3ProtocolError(
            "Stage-3 review stage or case identity does not match its packet."
        )
    if review.get("reviewer_agent") != packet.get("expected_reviewer_agent"):
        raise Stage3ProtocolError("Stage-3 reviewer configuration drifted from its packet.")
    if review.get("packet_digest") != packet.get("packet_digest"):
        raise Stage3ProtocolError("Stage-3 review packet digest does not match its submission.")
    if review.get("comparison_access") != packet.get("comparison_access_required"):
        raise Stage3ProtocolError("Stage-3 review does not preserve the required access boundary.")

    fixture = packet["fixture"]
    adjudication = packet["adjudication"]
    freeze = packet["scientific_label_freeze"]
    detector_output = packet["detector_output"]
    exact_fields = {
        "fixture_ref": fixture["fixture_ref"],
        "adjudication_ref": adjudication["adjudication_ref"],
        "adjudication_digest": adjudication["adjudication_digest"],
        "scientific_label_freeze_digest": freeze["freeze_digest"],
        "audit_bundle_ref": detector_output["audit_bundle_ref"],
        "audit_bundle_digest": detector_output["audit_bundle_digest"],
        "detector_id": detector_output["detector_id"],
        "detector_version": detector_output["detector_version"],
        "detector_manifest_digest": detector_output["detector_manifest_digest"],
        "root_cause_refs": packet["root_cause_refs"],
        "candidate_refs": packet["candidate_refs"],
    }
    for field, expected in exact_fields.items():
        observed = review.get(field)
        if isinstance(expected, list):
            if _canonical_objects(observed) != _canonical_objects(expected):
                raise Stage3ProtocolError(f"Stage-3 review {field} differs from its packet.")
        elif observed != expected:
            raise Stage3ProtocolError(f"Stage-3 review {field} differs from its packet.")

    if review.get("confidence_used_for_equivalence") is not False:
        raise Stage3ProtocolError("Confidence cannot establish Stage-3 equivalence.")
    if _timestamp(str(review["completed_at"])) <= _timestamp(str(packet["packet_created_at"])):
        raise Stage3ProtocolError("Stage-3 review must complete after packet creation.")

    candidate_refs = _ref_keys(packet["candidate_refs"])
    root_refs = _ref_keys(packet["root_cause_refs"])
    mappings = _objects(review.get("candidate_mappings"), "candidate mappings")
    mapped_candidates = [_ref_key(mapping.get("candidate_ref")) for mapping in mappings]
    if len(set(mapped_candidates)) != len(mapped_candidates) or set(mapped_candidates) != (
        candidate_refs
    ):
        raise Stage3ProtocolError("Every Stage-3 candidate must be accounted for exactly once.")

    allowed_evidence = {
        semantic_digest(value)
        for value in _objects(packet.get("frozen_evidence"), "frozen evidence")
    }
    matched_roots: set[tuple[str, str]] = set()
    any_ambiguity = False
    for mapping in mappings:
        root_ref = mapping.get("root_cause_ref")
        if root_ref is not None and _ref_key(root_ref) not in root_refs:
            raise Stage3ProtocolError("Stage-3 mapping cites a root outside the frozen packet.")
        _validate_mapping_semantics(mapping, root_ref is not None)
        evidence = _objects(mapping.get("evidence"), "mapping evidence")
        if any(semantic_digest(value) not in allowed_evidence for value in evidence):
            raise Stage3ProtocolError("Stage-3 mapping cites evidence outside the frozen packet.")
        if mapping["scientific_relation"] == "same_first_material_divergence":
            assert root_ref is not None
            matched_roots.add(_ref_key(root_ref))
        any_ambiguity = any_ambiguity or bool(mapping["material_ambiguity"])

    unmatched_roots = _ref_keys(review.get("unmatched_root_cause_refs"))
    if unmatched_roots != root_refs - matched_roots:
        raise Stage3ProtocolError("Stage-3 unmatched roots do not complete exact root accounting.")
    if review.get("material_ambiguity_retained") is not any_ambiguity:
        raise Stage3ProtocolError("Stage-3 material-ambiguity aggregate does not match mappings.")
    if (
        review.get("all_candidates_accounted_for") is not True
        or review.get("all_roots_accounted_for") is not True
    ):
        raise Stage3ProtocolError("Stage-3 review does not affirm complete closed accounting.")


def reconcile_detector_case(
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    stage1_freeze: dict[str, Any],
    scientific_label_freeze: dict[str, Any],
    audit_bundle: dict[str, Any],
    candidates: list[dict[str, Any]],
    adjudicated_root_causes: list[dict[str, Any]],
    detector_id: str,
    reviews: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    schema_root: Path,
    *,
    reconciled_at: str,
    output: Path | None = None,
    expected_outcome: dict[str, Any] | None = None,
    fixture_proof_inputs: FixtureProofInputs | None = None,
) -> dict[str, Any]:
    """Reconcile exact cross-provider Stage-3 decisions without a model or similarity rule."""

    if output is not None and (output.exists() or output.is_symlink()):
        raise Stage3ProtocolError(f"DetectorCaseOutcome output already exists: {output}")
    proof_status = fixture.get("qualification_proof_status")
    if proof_status == "complete":
        if fixture_proof_inputs is None:
            raise Stage3ProtocolError(
                "A complete fixture requires exact proof inputs before Stage-3 reconciliation."
            )
        from sc_referee_evaluation.fixture import (
            FixtureGenerationError,
            revalidate_fixture_proof,
        )

        try:
            if (
                fixture.get("fixture_kind")
                in {
                    "static_scope_verified_good",
                    "static_scope_hard_negative",
                }
                and fixture_proof_inputs.scientific_label_freeze != scientific_label_freeze
            ):
                raise Stage3ProtocolError(
                    "Static fixture proof inputs do not equal the supplied scientific-label freeze."
                )
            revalidate_fixture_proof(
                fixture,
                adjudication,
                adjudicated_root_causes,
                fixture_proof_inputs,
                schema_root,
            )
        except FixtureGenerationError as error:
            raise Stage3ProtocolError(f"Fixture proof replay failed: {error}") from error
    elif fixture_proof_inputs is not None:
        raise Stage3ProtocolError(
            "Non-complete fixtures cannot acquire qualification authority from proof inputs."
        )
    inputs = _validate_stage3_inputs(
        fixture,
        adjudication,
        stage1_freeze,
        scientific_label_freeze,
        audit_bundle,
        candidates,
        adjudicated_root_causes,
        detector_id,
        schema_root,
    )
    if len(reviews) != len(packets) or len(reviews) < 2:
        raise Stage3ProtocolError("Stage-3 reconciliation requires at least two exact captures.")
    packets_by_digest = {str(packet.get("packet_digest")): packet for packet in packets}
    if len(packets_by_digest) != len(packets):
        raise Stage3ProtocolError("Stage-3 packets must have unique exact digests.")

    providers: set[str] = set()
    contexts: set[str] = set()
    projections: list[dict[str, Any]] = []
    review_refs: list[dict[str, str]] = []
    for review in reviews:
        packet = packets_by_digest.get(str(review.get("packet_digest")))
        if packet is None:
            raise Stage3ProtocolError("Stage-3 review has no exact supplied packet digest.")
        validate_stage3_review_submission(review, packet, schema_root)
        if packet.get("comparison_input_digest") != inputs["comparison_input_digest"]:
            raise Stage3ProtocolError("Stage-3 packet binds a different comparison input.")
        provider = str(review["reviewer_agent"]["provider"])
        context = str(review["reviewer_agent"]["execution_context_id"])
        if context in contexts or context in inputs["prior_context_ids"]:
            raise Stage3ProtocolError("Stage-3 reconciliation observed a reused review context.")
        providers.add(provider)
        contexts.add(context)
        projections.append(_decision_projection(review))
        review_refs.append(_ref("stage3_comparison_review", str(review["comparison_review_id"])))
    if set(packets_by_digest) != {str(review.get("packet_digest")) for review in reviews}:
        raise Stage3ProtocolError("Every Stage-3 packet must have exactly one captured review.")
    if providers != inputs["provider_families"]:
        raise Stage3ProtocolError(
            "Stage-3 reconciliation requires every scientific provider family."
        )
    if qualification_proof_family := _QUALIFICATION_PROOF_FAMILIES.get(
        str(fixture.get("fixture_kind", ""))
    ):
        if qualification_proof_family == "static_closed_scope":
            assert fixture_proof_inputs is not None
            _validate_static_stage3_boundary(
                fixture,
                audit_bundle,
                inputs["detector_results"],
                packets,
                fixture_proof_inputs,
            )
    if _timestamp(reconciled_at) <= max(
        _timestamp(str(review["completed_at"])) for review in reviews
    ):
        raise Stage3ProtocolError("Case reconciliation must follow every Stage-3 review.")

    exact_agreement = all(projection == projections[0] for projection in projections[1:])
    exclusion_reasons: list[str] = []
    if not exact_agreement:
        exclusion_reasons.append("Cross-provider Stage-3 decisions are not exactly identical.")
    elif _projection_is_unresolved(projections[0]):
        exclusion_reasons.append(
            "Stage-3 review retains material ambiguity or unresolved evidence."
        )
    if (
        adjudication["label_status"] in _EXCLUDED_LABELS
        or fixture["fixture_kind"] == "ambiguous_fixture"
    ):
        exclusion_reasons.append("The frozen scientific label is excluded from detector metrics.")
    exclusion_reasons = sorted(set(exclusion_reasons))
    comparison_status = "comparison_excluded" if exclusion_reasons else "reconciled"

    root_refs = [
        _ref("adjudicated_root_cause", str(root["adjudicated_root_cause_id"]))
        for root in inputs["roots"]
    ]
    candidate_refs = [
        _ref("detector_evaluation_candidate", str(value["evaluation_candidate_id"]))
        for value in inputs["candidates"]
    ]
    if comparison_status == "reconciled":
        candidate_outcomes, root_outcomes = _derive_reconciled_outcomes(
            inputs["candidates"], inputs["roots"], projections[0]["candidate_mappings"]
        )
    else:
        candidate_outcomes = [
            {"candidate_ref": ref, "status": "unresolved", "root_cause_ref": None}
            for ref in candidate_refs
        ]
        root_outcomes = [
            {"root_cause_ref": ref, "status": "unresolved", "matched_candidate_refs": []}
            for ref in root_refs
        ]

    detector_run_outcome = _detector_run_outcome(inputs["detector_results"])
    detector_result_outcomes = _detector_result_outcomes(
        inputs["detector_results"], inputs["candidates"]
    )
    fixture_digest = semantic_digest(fixture)
    qualification_proof_family = _qualification_proof_family(fixture)
    static_qualification_proof_ref = _static_qualification_proof_ref(fixture)
    proof_status = str(fixture["qualification_proof_status"])
    metric_eligible = comparison_status == "reconciled" and proof_status == "complete"
    promotion_eligible = metric_eligible and fixture["corpus_partition"] != "public_development"
    metric_input_status = (
        "complete" if proof_status == "complete" else "legacy_source_projection_unavailable"
    )
    authoritative_detector_result_outcomes = (
        detector_result_outcomes if metric_input_status == "complete" else []
    )
    identity_payload = {
        "case_id": adjudication["case_id"],
        "problem_id": fixture["problem_id"],
        "fixture_ref": _ref("benchmark_fixture", str(fixture["fixture_id"])),
        "fixture_semantic_digest": fixture_digest,
        "qualification_proof_status": proof_status,
        "qualification_proof_family": qualification_proof_family,
        "static_qualification_proof_ref": static_qualification_proof_ref,
        "scientific_label_freeze_digest": scientific_label_freeze["freeze_digest"],
        "audit_bundle_digest": semantic_digest(audit_bundle),
        "detector_id": detector_id,
        "detector_version": inputs["detector_version"],
        "detector_manifest_digest": inputs["detector_manifest_digest"],
        "comparison_review_digests": sorted(semantic_digest(review) for review in reviews),
        "comparison_status": comparison_status,
        "candidate_outcomes": candidate_outcomes,
        "root_outcomes": root_outcomes,
        "detector_run_outcome": detector_run_outcome,
        "metric_input_status": metric_input_status,
        "detector_result_outcomes": authoritative_detector_result_outcomes,
    }
    outcome: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "detector_case_outcome",
        "case_outcome_id": stable_id(
            "detector-case-outcome",
            str(adjudication["case_id"]),
            detector_id,
            semantic_digest(identity_payload),
        ),
        "case_id": adjudication["case_id"],
        "problem_id": fixture["problem_id"],
        "corpus_partition": fixture["corpus_partition"],
        "fixture_kind": fixture["fixture_kind"],
        "fixture_ref": _ref("benchmark_fixture", str(fixture["fixture_id"])),
        "fixture_semantic_digest": fixture_digest,
        "qualification_proof_status": proof_status,
        "qualification_proof_family": qualification_proof_family,
        "static_qualification_proof_ref": static_qualification_proof_ref,
        "adjudication_ref": _ref("benchmark_adjudication", str(adjudication["adjudication_id"])),
        "scientific_label_freeze_digest": scientific_label_freeze["freeze_digest"],
        "audit_bundle_ref": _ref("audit_bundle", str(audit_bundle["bundle_id"])),
        "audit_bundle_digest": semantic_digest(audit_bundle),
        "detector_id": detector_id,
        "detector_version": inputs["detector_version"],
        "detector_manifest_digest": inputs["detector_manifest_digest"],
        "comparison_review_refs": sorted(review_refs, key=lambda value: value["record_id"]),
        "provider_families": sorted(providers),
        "fresh_contexts_verified": True,
        "exact_cross_provider_agreement": exact_agreement,
        "comparison_status": comparison_status,
        "exclusion_reasons": exclusion_reasons,
        "root_cause_refs": root_refs,
        "candidate_refs": candidate_refs,
        "root_outcomes": root_outcomes,
        "candidate_outcomes": candidate_outcomes,
        "metric_input_status": metric_input_status,
        "detector_result_outcomes": authoritative_detector_result_outcomes,
        "detector_run_outcome": detector_run_outcome,
        "metric_eligible": metric_eligible,
        "promotion_evidence_eligible": promotion_eligible,
        "detector_output_observed": True,
        "model_free_reconciliation": True,
        "reconciled_at": reconciled_at,
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-eval",
                "display_name": "sc-referee evaluation controller",
            },
            "method": "deterministic_stage3_case_reconciliation",
            "created_at": reconciled_at,
            "tool": "sc-referee-eval",
            "tool_version": "0.1.0",
        },
    }
    try:
        LocalSchemaRegistry(schema_root).validate(outcome)
    except RecordValidationError as error:  # pragma: no cover - construction invariant
        raise Stage3ProtocolError(str(error)) from error
    if expected_outcome is not None and outcome != expected_outcome:
        raise Stage3ProtocolError("Model-free Stage-3 replay does not equal the source outcome.")
    if output is not None:
        write_normalized_json_once(output, outcome)
    return outcome


def _qualification_proof_family(fixture: Mapping[str, Any]) -> str:
    kind = str(fixture.get("fixture_kind", ""))
    try:
        return _QUALIFICATION_PROOF_FAMILIES[kind]
    except KeyError as error:
        raise Stage3ProtocolError(f"Unsupported fixture proof family for {kind!r}.") from error


def _static_qualification_proof_ref(
    fixture: Mapping[str, Any],
) -> dict[str, str] | None:
    if _qualification_proof_family(fixture) != "static_closed_scope":
        return None
    proof_evidence = fixture.get("proof_evidence")
    public_inputs = (
        proof_evidence.get("public_inputs") if isinstance(proof_evidence, Mapping) else None
    )
    proofs = (
        public_inputs.get("static_qualification_proofs")
        if isinstance(public_inputs, Mapping)
        else None
    )
    if not isinstance(proofs, list) or len(proofs) != 1:
        raise Stage3ProtocolError("A static control requires one exact static proof reference.")
    bound = proofs[0]
    reference = bound.get("record_ref") if isinstance(bound, Mapping) else None
    if (
        not isinstance(reference, Mapping)
        or reference.get("record_type") != "static_qualification_proof"
        or not isinstance(reference.get("record_id"), str)
    ):
        raise Stage3ProtocolError("Static control proof reference is malformed.")
    return {"record_type": "static_qualification_proof", "record_id": str(reference["record_id"])}


def _validate_static_stage3_boundary(
    fixture: Mapping[str, Any],
    audit_bundle: Mapping[str, Any],
    detector_results: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    proof_inputs: FixtureProofInputs,
) -> None:
    profile = proof_inputs.static_qualification_profile
    proof = proof_inputs.static_qualification_proof
    manifest = proof_inputs.detector_manifest
    if not all(isinstance(value, Mapping) for value in (profile, proof, manifest)):
        raise Stage3ProtocolError("Static Stage-3 boundary lacks its exact proof records.")
    assert isinstance(profile, Mapping)
    assert isinstance(proof, Mapping)
    assert isinstance(manifest, Mapping)
    bundled_profiles = audit_bundle.get("static_qualification_profiles")
    bundled_proofs = audit_bundle.get("static_qualification_proofs")
    if bundled_profiles != [profile] or bundled_proofs != [proof]:
        raise Stage3ProtocolError(
            "Static Stage-3 bundle does not carry the exact profile and proof."
        )
    target = profile.get("target_detector")
    if (
        not isinstance(target, Mapping)
        or target.get("detector_id") != manifest.get("detector_id")
        or target.get("detector_version") != manifest.get("detector_version")
        or not any(item == manifest for item in audit_bundle.get("detector_manifests", []))
    ):
        raise Stage3ProtocolError("Static proof target does not equal the evaluated detector.")
    expected_ref = _static_qualification_proof_ref(fixture)
    if expected_ref != {
        "record_type": "static_qualification_proof",
        "record_id": proof.get("proof_id"),
    }:
        raise Stage3ProtocolError("Static Stage-3 fixture proof identity drifted.")
    chronology = proof.get("chronology")
    if (
        not isinstance(chronology, Mapping)
        or chronology.get("detector_dispatched_at") is not None
        or chronology.get("stage3_started_at") is not None
    ):
        raise Stage3ProtocolError("Static proof contains an authoritative post-proof timestamp.")
    proof_time = _timestamp(str(chronology.get("proof_frozen_at", "")))
    detector_times = [
        _timestamp(str(result.get("evaluated_at", ""))) for result in detector_results
    ]
    if not detector_times or proof_time >= min(detector_times):
        raise Stage3ProtocolError("Detector evaluation does not follow the static proof freeze.")
    if any(
        _timestamp(str(packet.get("packet_created_at", ""))) <= max(detector_times)
        for packet in packets
    ):
        raise Stage3ProtocolError("Stage-3 packet does not follow detector evaluation.")
    for result in detector_results:
        if _contains_record_type(
            result, {"static_qualification_profile", "static_qualification_proof"}
        ):
            raise Stage3ProtocolError(
                "Production detector output treats a static qualification record as a semantic input."
            )


def _contains_record_type(value: object, forbidden: set[str]) -> bool:
    if isinstance(value, Mapping):
        if value.get("record_type") in forbidden:
            return True
        return any(_contains_record_type(item, forbidden) for item in value.values())
    if isinstance(value, list):
        return any(_contains_record_type(item, forbidden) for item in value)
    return False


def _validate_stage3_inputs(
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    stage1_freeze: dict[str, Any],
    label_freeze: dict[str, Any],
    audit_bundle: dict[str, Any],
    candidates: list[dict[str, Any]],
    roots: list[dict[str, Any]],
    detector_id: str,
    schema_root: Path,
) -> dict[str, Any]:
    registry = LocalSchemaRegistry(schema_root)
    try:
        for record in [fixture, adjudication, audit_bundle, *roots, *candidates]:
            registry.validate(record)
    except RecordValidationError as error:
        raise Stage3ProtocolError(str(error)) from error
    _validate_self_digest(stage1_freeze, "freeze_digest", "Stage-1 freeze")
    _validate_self_digest(label_freeze, "freeze_digest", "scientific-label freeze")
    if stage1_freeze.get("record_type") != "evaluation_stage1_freeze":
        raise Stage3ProtocolError("Stage-1 freeze record kind is invalid.")
    if label_freeze.get("record_type") != "evaluation_scientific_label_freeze":
        raise Stage3ProtocolError("Scientific-label freeze record kind is invalid.")
    if label_freeze.get("detector_output_observed") is not False or label_freeze.get(
        "stage1_freeze_digest"
    ) != stage1_freeze.get("freeze_digest"):
        raise Stage3ProtocolError(
            "Scientific-label freeze chronology or Stage-1 binding is invalid."
        )
    if fixture.get("adjudication_ref") != _ref(
        "benchmark_adjudication", str(adjudication.get("adjudication_id"))
    ) or adjudication.get("case_id") != label_freeze.get("case_id"):
        raise Stage3ProtocolError(
            "Fixture, adjudication, and scientific freeze do not share a case."
        )
    if label_freeze.get("adjudication_ref") != _ref(
        "benchmark_adjudication", str(adjudication.get("adjudication_id"))
    ) or label_freeze.get("adjudication_digest") != semantic_digest(adjudication):
        raise Stage3ProtocolError("Scientific-label freeze does not bind the exact adjudication.")

    sorted_roots = sorted(roots, key=lambda value: str(value["adjudicated_root_cause_id"]))
    root_refs = {_ref_key(ref) for ref in adjudication.get("adjudicated_root_cause_refs", [])}
    supplied_root_refs = {
        ("adjudicated_root_cause", str(root["adjudicated_root_cause_id"])) for root in sorted_roots
    }
    frozen_root_entries = {
        _ref_key(item.get("root_cause_ref")): item.get("root_cause_digest")
        for item in label_freeze.get("adjudicated_root_causes", [])
    }
    if root_refs != supplied_root_refs or frozen_root_entries != {
        ("adjudicated_root_cause", str(root["adjudicated_root_cause_id"])): semantic_digest(root)
        for root in sorted_roots
    }:
        raise Stage3ProtocolError("Stage-3 roots do not equal the frozen adjudicated roots.")
    if any(root.get("case_id") != adjudication.get("case_id") for root in sorted_roots):
        raise Stage3ProtocolError("An adjudicated root belongs to another case.")
    for root in sorted_roots:
        expected_root_id = adjudicated_root_cause_id(
            str(root["case_id"]),
            str(root["issue_class"]),
            _objects(root.get("stage1_candidate_refs"), "root Stage-1 candidate refs"),
        )
        if root.get("adjudicated_root_cause_id") != expected_root_id:
            raise Stage3ProtocolError("Adjudicated root ID does not match its exact candidate set.")
    expected_fixture_roots = _ref_keys(fixture.get("expected_root_cause_refs", []))
    if expected_fixture_roots != supplied_root_refs:
        raise Stage3ProtocolError("Fixture expected roots differ from the frozen adjudication.")

    bundle_digest = semantic_digest(audit_bundle)
    results = _objects(audit_bundle.get("detector_results"), "AuditBundle detector results")
    selected_results = sorted(
        [record for record in results if record.get("detector_id") == detector_id],
        key=lambda value: str(value.get("result_id")),
    )
    if not selected_results:
        raise Stage3ProtocolError("AuditBundle has no result for the declared Stage-3 detector.")
    versions = {str(record.get("detector_version")) for record in selected_results}
    manifests = {str(record.get("detector_manifest_digest")) for record in selected_results}
    if len(versions) != 1 or len(manifests) != 1:
        raise Stage3ProtocolError("Stage-3 requires one exact detector version and manifest.")
    results_by_id = {str(record.get("result_id")): record for record in selected_results}
    if len(results_by_id) != len(selected_results):
        raise Stage3ProtocolError("Stage-3 detector result identities are not unique.")

    sorted_candidates = sorted(candidates, key=lambda value: str(value["evaluation_candidate_id"]))
    for candidate in sorted_candidates:
        if candidate.get("evaluation_candidate_id") != evaluation_candidate_id(candidate):
            raise Stage3ProtocolError("Evaluation candidate ID does not match its exact content.")
        source_ref = candidate.get("source_detector_result_ref", {})
        source = results_by_id.get(str(source_ref.get("record_id")))
        if source_ref.get("record_type") != "detector_result" or source is None:
            raise Stage3ProtocolError("Evaluation candidate source DetectorResult is unresolved.")
        if source.get("state") != "evaluation_finding_candidate":
            raise Stage3ProtocolError(
                "Evaluation candidate source is not an evaluation_finding_candidate result."
            )
        if semantic_digest(source) != candidate.get("source_detector_result_digest"):
            raise Stage3ProtocolError("Evaluation candidate source DetectorResult digest drifted.")
        if (
            candidate.get("case_id") != adjudication.get("case_id")
            or candidate.get("fixture_ref")
            != _ref("benchmark_fixture", str(fixture.get("fixture_id")))
            or candidate.get("scientific_label_freeze_digest") != label_freeze.get("freeze_digest")
            or candidate.get("audit_bundle_ref")
            != _ref("audit_bundle", str(audit_bundle.get("bundle_id")))
            or candidate.get("audit_bundle_digest") != bundle_digest
            or candidate.get("semantic_lock_digest") != audit_bundle.get("semantic_lock_digest")
            or candidate.get("detector_id") != detector_id
            or candidate.get("detector_version") != next(iter(versions))
            or candidate.get("detector_manifest_digest") != next(iter(manifests))
        ):
            raise Stage3ProtocolError(
                "Evaluation candidate identity or frozen input binding drifted."
            )
        if _timestamp(str(candidate["candidate_created_at"])) <= _timestamp(
            str(label_freeze["frozen_at"])
        ):
            raise Stage3ProtocolError("Evaluation candidate must be created after label freeze.")
        if (
            candidate.get("maturity_gate_bypassed_for_evaluation") is not True
            or candidate.get("production_admission_permitted") is not False
            or candidate.get("production_finding_ref") is not None
        ):
            raise Stage3ProtocolError("Evaluation candidate grants prohibited Finding authority.")

    prior_context_ids = {
        str(item.get("execution_context_id")) for item in stage1_freeze.get("reviews", [])
    } | {str(item.get("execution_context_id")) for item in label_freeze.get("stage2_reviews", [])}
    if "" in prior_context_ids or "None" in prior_context_ids:
        raise Stage3ProtocolError("Scientific freezes omit a prior execution-context identity.")
    provider_families = {str(value) for value in adjudication.get("provider_families", [])}
    if len(provider_families) < 2:
        raise Stage3ProtocolError("Stage-3 requires at least two scientific provider families.")

    evidence = _canonical_objects(
        [
            item
            for record in [*sorted_candidates, *sorted_roots]
            for item in _objects(record.get("evidence"), "frozen record evidence")
        ]
    )
    if sorted_candidates and not evidence:
        raise Stage3ProtocolError("Stage-3 candidate comparison has no frozen exact evidence.")
    comparison_input = {
        "fixture_digest": semantic_digest(fixture),
        "adjudication_digest": semantic_digest(adjudication),
        "stage1_freeze_digest": stage1_freeze["freeze_digest"],
        "scientific_label_freeze_digest": label_freeze["freeze_digest"],
        "audit_bundle_digest": bundle_digest,
        "detector_id": detector_id,
        "detector_version": next(iter(versions)),
        "detector_manifest_digest": next(iter(manifests)),
        "candidate_digests": [semantic_digest(value) for value in sorted_candidates],
        "root_digests": [semantic_digest(value) for value in sorted_roots],
    }
    return {
        "comparison_input_digest": semantic_digest(comparison_input),
        "detector_version": next(iter(versions)),
        "detector_manifest_digest": next(iter(manifests)),
        "detector_results": selected_results,
        "candidates": sorted_candidates,
        "roots": sorted_roots,
        "frozen_evidence": evidence,
        "prior_context_ids": prior_context_ids,
        "provider_families": provider_families,
    }


def _validate_mapping_semantics(mapping: dict[str, Any], has_root: bool) -> None:
    decisions = {
        key: mapping.get(key)
        for key in (
            "scientific_relation",
            "statement_boundedness",
            "affected_scope",
            "issue_class_relationship",
        )
    }
    unresolved = any(decisions[key] == value for key, value in _UNRESOLVED_DECISIONS.items())
    if bool(mapping.get("material_ambiguity")) != unresolved:
        raise Stage3ProtocolError(
            "Stage-3 material ambiguity must exactly track unresolved mapping decisions."
        )
    relation = decisions["scientific_relation"]
    if relation == "same_first_material_divergence" and not has_root:
        raise Stage3ProtocolError("A same-divergence mapping requires one exact root.")
    if relation == "no_adjudicated_root" and has_root:
        raise Stage3ProtocolError("A no-root mapping cannot cite an adjudicated root.")
    if decisions["affected_scope"] == "outside_declared_scope" and has_root:
        raise Stage3ProtocolError("An out-of-scope candidate cannot map to a root.")


def _decision_projection(review: dict[str, Any]) -> dict[str, Any]:
    mappings = []
    for mapping in review["candidate_mappings"]:
        mappings.append(
            {
                "candidate_ref": deepcopy(mapping["candidate_ref"]),
                "root_cause_ref": deepcopy(mapping["root_cause_ref"]),
                "scientific_relation": mapping["scientific_relation"],
                "statement_boundedness": mapping["statement_boundedness"],
                "affected_scope": mapping["affected_scope"],
                "issue_class_relationship": mapping["issue_class_relationship"],
                "material_ambiguity": mapping["material_ambiguity"],
            }
        )
    return {
        "candidate_mappings": sorted(
            mappings, key=lambda value: str(value["candidate_ref"]["record_id"])
        ),
        "unmatched_root_cause_refs": _canonical_objects(review["unmatched_root_cause_refs"]),
        "material_ambiguity_retained": review["material_ambiguity_retained"],
    }


def _projection_is_unresolved(projection: dict[str, Any]) -> bool:
    return bool(projection["material_ambiguity_retained"]) or any(
        bool(mapping["material_ambiguity"])
        or mapping["scientific_relation"] == "unresolved"
        or mapping["statement_boundedness"] == "unresolved"
        or mapping["affected_scope"] == "unresolved"
        or mapping["issue_class_relationship"] == "unresolved"
        for mapping in projection["candidate_mappings"]
    )


def _derive_reconciled_outcomes(
    candidates: list[dict[str, Any]],
    roots: list[dict[str, Any]],
    mappings: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    mappings_by_candidate = {
        str(mapping["candidate_ref"]["record_id"]): mapping for mapping in mappings
    }
    candidate_outcomes: list[dict[str, Any]] = []
    bounded_by_root: dict[str, list[dict[str, str]]] = {}
    overstated_by_root: dict[str, list[dict[str, str]]] = {}
    for candidate in candidates:
        candidate_ref = _ref(
            "detector_evaluation_candidate", str(candidate["evaluation_candidate_id"])
        )
        mapping = mappings_by_candidate[str(candidate["evaluation_candidate_id"])]
        root_ref = mapping["root_cause_ref"]
        if mapping["affected_scope"] == "outside_declared_scope":
            status = "out_of_declared_scope"
            outcome_root_ref = None
        else:
            same_root = (
                root_ref is not None
                and mapping["scientific_relation"] == "same_first_material_divergence"
                and mapping["issue_class_relationship"] == "exact"
            )
            if (
                same_root
                and mapping["statement_boundedness"] == "within_adjudicated_bounds"
                and mapping["affected_scope"] in {"within_adjudicated_scope", "not_applicable"}
            ):
                status = "bounded_root_match"
                outcome_root_ref = deepcopy(root_ref)
                bounded_by_root.setdefault(str(root_ref["record_id"]), []).append(candidate_ref)
            elif same_root and (
                mapping["statement_boundedness"] == "exceeds_adjudicated_bounds"
                or mapping["affected_scope"] == "exceeds_adjudicated_scope"
            ):
                status = "overstated_root_match"
                outcome_root_ref = deepcopy(root_ref)
                overstated_by_root.setdefault(str(root_ref["record_id"]), []).append(candidate_ref)
            else:
                status = "false_root_localization"
                outcome_root_ref = None
        candidate_outcomes.append(
            {
                "candidate_ref": candidate_ref,
                "status": status,
                "root_cause_ref": outcome_root_ref,
            }
        )

    root_outcomes: list[dict[str, Any]] = []
    for root in roots:
        root_id = str(root["adjudicated_root_cause_id"])
        bounded = bounded_by_root.get(root_id, [])
        overstated = overstated_by_root.get(root_id, [])
        if bounded:
            status = "boundedly_localized"
            matched = [*bounded, *overstated]
        elif overstated:
            status = "localized_but_overstated"
            matched = overstated
        else:
            status = "missed"
            matched = []
        root_outcomes.append(
            {
                "root_cause_ref": _ref("adjudicated_root_cause", root_id),
                "status": status,
                "matched_candidate_refs": sorted(matched, key=lambda value: value["record_id"]),
            }
        )
    return candidate_outcomes, root_outcomes


def _detector_run_outcome(results: list[dict[str, Any]]) -> dict[str, str]:
    execution_status = (
        "detector_error"
        if any(value.get("state") == "detector_error" for value in results)
        else "completed"
    )
    applicability = {str(value.get("applicability", {}).get("status")) for value in results}
    if "uncertain" in applicability:
        applicability_status = "uncertain"
    elif "applicable" in applicability:
        applicability_status = "applicable"
    else:
        applicability_status = "not_applicable"
    coverage = {str(value.get("coverage", {}).get("status")) for value in results}
    if coverage == {"covered"}:
        coverage_status = "covered"
    elif coverage == {"not_covered"}:
        coverage_status = "not_covered"
    elif "unknown" in coverage or not coverage:
        coverage_status = "unknown"
    else:
        coverage_status = "partially_covered"
    return {
        "execution_status": execution_status,
        "applicability_status": applicability_status,
        "coverage_status": coverage_status,
    }


def _detector_result_outcomes(
    results: list[dict[str, Any]], candidates: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    candidates_by_result: dict[str, list[dict[str, str]]] = {}
    for candidate in candidates:
        source_ref = candidate.get("source_detector_result_ref")
        if not isinstance(source_ref, dict) or source_ref.get("record_type") != "detector_result":
            raise Stage3ProtocolError("Evaluation candidate has no exact source DetectorResult.")
        result_id = str(source_ref.get("record_id"))
        candidates_by_result.setdefault(result_id, []).append(
            _ref("detector_evaluation_candidate", str(candidate["evaluation_candidate_id"]))
        )

    projections = []
    result_ids = {str(result["result_id"]) for result in results}
    if set(candidates_by_result) - result_ids:
        raise Stage3ProtocolError("Evaluation candidate cites an unprojected DetectorResult.")
    for result in sorted(results, key=lambda value: str(value["result_id"])):
        result_id = str(result["result_id"])
        candidate_refs = sorted(
            candidates_by_result.get(result_id, []), key=lambda value: value["record_id"]
        )
        if result.get("state") == "evaluation_finding_candidate" and not candidate_refs:
            raise Stage3ProtocolError(
                "An evaluation_finding_candidate result lacks its evaluation projection."
            )
        applicability = result.get("applicability")
        coverage = result.get("coverage")
        if not isinstance(applicability, dict) or not isinstance(coverage, dict):
            raise Stage3ProtocolError("DetectorResult applicability or coverage is unavailable.")
        projections.append(
            {
                "detector_result_ref": _ref("detector_result", result_id),
                "detector_result_digest": semantic_digest(result),
                "state": result["state"],
                "applicability_status": applicability["status"],
                "coverage_status": coverage["status"],
                "evaluation_candidate_refs": candidate_refs,
                "execution_class": (
                    "detector_error" if result.get("state") == "detector_error" else "completed"
                ),
            }
        )
    return projections


def _validate_packet_digest(packet: dict[str, Any]) -> None:
    _validate_self_digest(packet, "packet_digest", "Stage-3 packet")


def _validate_self_digest(value: dict[str, Any], field: str, label: str) -> None:
    digest_input = dict(value)
    expected = digest_input.pop(field, None)
    if expected != semantic_digest(digest_input):
        raise Stage3ProtocolError(f"{label} digest is invalid.")


def _ref(record_type: str, record_id: str) -> dict[str, str]:
    return {"record_type": record_type, "record_id": record_id}


def _ref_key(value: Any) -> tuple[str, str]:
    if not isinstance(value, dict):
        raise Stage3ProtocolError("Expected one exact typed record reference.")
    record_type = value.get("record_type")
    record_id = value.get("record_id")
    if not isinstance(record_type, str) or not isinstance(record_id, str):
        raise Stage3ProtocolError("Expected one exact typed record reference.")
    return record_type, record_id


def _ref_keys(value: Any) -> set[tuple[str, str]]:
    if not isinstance(value, list):
        raise Stage3ProtocolError("Expected a list of exact typed record references.")
    keys = [_ref_key(item) for item in value]
    if len(keys) != len(set(keys)):
        raise Stage3ProtocolError("Typed record references must be unique.")
    return set(keys)


def _objects(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise Stage3ProtocolError(f"Expected {label} to be a list of objects.")
    return value


def _canonical_objects(value: Any) -> list[dict[str, Any]]:
    objects = _objects(value, "canonical objects")
    return sorted(deepcopy(objects), key=semantic_digest)


def _normalize_prompt(value: str) -> str:
    normalized = "\n".join(line.rstrip() for line in value.replace("\r\n", "\n").split("\n"))
    normalized = normalized.strip()
    if not normalized:
        raise Stage3ProtocolError("Stage-3 prompt must be non-empty.")
    return normalized


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise Stage3ProtocolError(f"Invalid Stage-3 timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise Stage3ProtocolError("Stage-3 timestamps must include an offset.")
    return parsed
