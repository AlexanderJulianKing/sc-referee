from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from sc_referee.core.ids import semantic_digest
from sc_referee.detectors import method_conflict_grant_pins
from sc_referee.lineage import LINEAGE_GRADE_DIMENSIONS, derive_aggregate_lineage_status
from sc_referee.qualification_metrics import (
    QualificationMetricInvariantError,
    validate_detector_case_outcome_projection,
    verify_qualification_metric_set,
)
from sc_referee.storage.sqlite_index import record_identity


class ReportContractError(ValueError):
    """Raised when records would produce an epistemically invalid public report."""


_PROHIBITED_STRENGTHENING = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bthe biological conclusion is false\b",
        r"\bthe effect is biased (upward|downward)\b",
        r"\bthe (entire )?(paper|manuscript|analysis) is invalid\b",
        r"\bthe analysis is (correct|safe|publication[- ]ready)\b",
        r"\bno (scientific )?issues? (were )?found\b",
    )
]


def validate_report_contract(bundle: Mapping[str, Any]) -> None:
    """Enforce report-level invariants that span multiple public records."""

    coverage_records = bundle.get("coverage_records")
    if not isinstance(coverage_records, list) or len(coverage_records) != 1:
        raise ReportContractError("exactly one CoverageRecord is required for this report")
    coverage = coverage_records[0]
    if not isinstance(coverage, Mapping):
        raise ReportContractError("CoverageRecord is malformed")

    expected_counts = {
        "findings": _list_length(bundle, "findings"),
        "conditional_concerns": _list_length(bundle, "conditional_concerns"),
        "material_questions": _list_length(bundle, "material_questions"),
        "disclosures": _list_length(bundle, "disclosures"),
    }
    if coverage.get("assessment_counts") != expected_counts:
        raise ReportContractError("CoverageRecord assessment counts do not match the bundle")
    _validate_claim_lineage(bundle, coverage)
    _validate_lineage_plane_references(bundle)
    _validate_detector_projection(bundle)
    _validate_root_cause_projection(bundle)
    _validate_fixture_proof_projection(bundle)
    _validate_static_proof_projection(bundle)
    _validate_stage3_projection(bundle)
    _validate_qualification_projection(bundle)
    _validate_performance_projection(bundle)
    interpretation = coverage.get("interpretation_policy")
    if not isinstance(interpretation, Mapping) or (
        interpretation.get("correctness_conclusion_allowed") is not False
        or interpretation.get("global_risk_rating_allowed") is not False
    ):
        raise ReportContractError(
            "coverage interpretation policy permits a prohibited global claim"
        )

    question_ids = {
        item.get("question_id")
        for item in _records(bundle, "material_questions")
        if isinstance(item.get("question_id"), str)
    }
    for finding in _records(bundle, "findings"):
        _reject_strengthening(
            [
                finding.get("title"),
                finding.get("summary"),
                finding.get("logical_basis"),
                finding.get("next_action"),
            ]
        )
        admission = finding.get("admission")
        if not isinstance(admission, Mapping) or not admission.get("non_inferences"):
            raise ReportContractError("every Finding requires explicit non-inferences")
        _require_source_evidence(
            finding,
            allow_method_record_evidence=_finding_links_qualified_method_result(finding, bundle),
        )

    for concern in _records(bundle, "conditional_concerns"):
        statement = concern.get("conditional_statement")
        if not isinstance(statement, str) or not statement.lstrip().lower().startswith("if "):
            raise ReportContractError("ConditionalConcern wording must begin with an explicit if")
        if "severity" in concern:
            raise ReportContractError("ConditionalConcern must not expose Finding severity")
        if concern.get("material_question_id") not in question_ids:
            raise ReportContractError(
                "ConditionalConcern is not linked to a bundled MaterialQuestion"
            )
        _reject_strengthening([concern.get("title"), statement, concern.get("why_material")])

    for question in _records(bundle, "material_questions"):
        if "severity" in question:
            raise ReportContractError("MaterialQuestion must not expose Finding severity")
        _reject_strengthening([question.get("question"), question.get("why_it_matters")])

    for disclosure in _records(bundle, "disclosures"):
        if disclosure.get("non_accusatory") is not True or "severity" in disclosure:
            raise ReportContractError("Disclosure must remain non-accusatory and severity-free")
        _reject_strengthening(
            [
                disclosure.get("title"),
                disclosure.get("description"),
                disclosure.get("interpretive_consequence"),
            ]
        )


def _validate_claim_lineage(bundle: Mapping[str, Any], coverage: Mapping[str, Any]) -> None:
    claims = _records(bundle, "claims")
    statuses = ("complete", "partial", "missing", "unavailable", "opaque")
    expected_grade_counts: dict[str, dict[str, int]] = {}
    for dimension in LINEAGE_GRADE_DIMENSIONS:
        counts = {status: 0 for status in statuses}
        for claim in claims:
            lineage = claim.get("lineage")
            if not isinstance(lineage, Mapping):
                raise ReportContractError("Claim lineage is malformed")
            grades = lineage.get("grades")
            if not isinstance(grades, Mapping):
                raise ReportContractError("Claim lineage grades are missing")
            statuses_by_dimension = {
                key: grade.get("status")
                for key, grade in grades.items()
                if isinstance(key, str) and isinstance(grade, Mapping)
            }
            try:
                derived = derive_aggregate_lineage_status(statuses_by_dimension)  # type: ignore[arg-type]
            except ValueError as error:
                raise ReportContractError(str(error)) from error
            if lineage.get("status") != derived:
                raise ReportContractError("Claim aggregate lineage is not derived from its grades")
            status = statuses_by_dimension.get(dimension)
            if status not in counts:
                raise ReportContractError(f"Claim {dimension} grade is invalid")
            counts[str(status)] += 1
        counts["total"] = len(claims)
        expected_grade_counts[dimension] = counts
    claim_coverage = coverage.get("claim_coverage")
    if not isinstance(claim_coverage, Mapping):
        raise ReportContractError("CoverageRecord Claim coverage is malformed")
    if claim_coverage.get("lineage_grade_counts") != expected_grade_counts:
        raise ReportContractError("CoverageRecord lineage grade counts do not match Claims")
    if claim_coverage.get("claims_total") != len(claims):
        raise ReportContractError("CoverageRecord Claim total does not match the bundle")
    complete = sum(claim.get("lineage", {}).get("status") == "complete" for claim in claims)
    if claim_coverage.get("claims_with_complete_lineage") != complete:
        raise ReportContractError("CoverageRecord complete-lineage count does not match Claims")


def _validate_lineage_plane_references(bundle: Mapping[str, Any]) -> None:
    identities: set[tuple[str, str]] = set()
    for value in bundle.values():
        if not isinstance(value, list):
            continue
        for record in value:
            if not isinstance(record, Mapping) or not isinstance(record.get("record_type"), str):
                continue
            try:
                identities.add(record_identity(record))
            except ValueError as error:
                raise ReportContractError(str(error)) from error

    records_to_check = [
        *_records(bundle, "claims"),
        *_records(bundle, "detector_results"),
        *_records(bundle, "data_assets"),
        *_records(bundle, "variables"),
        *_records(bundle, "analysis_decisions"),
        *_records(bundle, "selection_envelopes"),
        *_records(bundle, "executions"),
        *_records(bundle, "environments"),
        *_records(bundle, "reproduction_requests"),
        *_records(bundle, "cache_entries"),
        *_records(bundle, "agent_reviews"),
        *_records(bundle, "adjudicated_root_causes"),
        *_records(bundle, "benchmark_adjudications"),
        *_records(bundle, "benchmark_fixtures"),
    ]
    for record in records_to_check:
        for record_type, record_id in _typed_refs(record):
            if (record_type, record_id) not in identities:
                raise ReportContractError(
                    f"typed reference does not resolve: {record_type}/{record_id}"
                )


def _validate_detector_projection(bundle: Mapping[str, Any]) -> None:
    manifests = {
        str(manifest["detector_id"]): manifest
        for manifest in _records(bundle, "detector_manifests")
        if isinstance(manifest.get("detector_id"), str)
    }
    detector_results = _records(bundle, "detector_results")
    result_ids = [result.get("result_id") for result in detector_results]
    if any(not isinstance(result_id, str) or not result_id for result_id in result_ids) or len(
        set(result_ids)
    ) != len(result_ids):
        raise ReportContractError("DetectorResult identities are missing or duplicated")
    result_by_id = {str(result["result_id"]): result for result in detector_results}
    for result in result_by_id.values():
        maturity = result.get("detector_maturity")
        if maturity == "experimental" and result.get("state") == "finding_candidate":
            raise ReportContractError(
                "an experimental DetectorResult cannot expose a production finding candidate"
            )
        if result.get("state") == "evaluation_finding_candidate":
            if maturity != "experimental":
                raise ReportContractError(
                    "an evaluation Finding candidate must retain experimental maturity"
                )
            candidate = result.get("candidate")
            if not isinstance(candidate, Mapping) or candidate.get("assessment_type") != "finding":
                raise ReportContractError("evaluation detector candidate is malformed")
            _reject_strengthening([candidate.get("title"), candidate.get("bounded_statement")])
        detector_id = str(result.get("detector_id", ""))
        manifest = manifests.get(detector_id)
        public_experimental = (
            result.get("extensions", {}).get("x-detector-profile")
            == "bounded_report_mean_direction_v1"
        )
        method_conflict = (
            result.get("extensions", {}).get("x-detector-profile")
            == "bounded_analysis_method_conflict_v1"
        )
        if result.get("extensions", {}).get("x-production-finding-permitted") is True and not (
            method_conflict
        ):
            raise ReportContractError(
                "production Finding permission is not linked to a method-conflict grant"
            )
        if method_conflict:
            _validate_method_conflict_result(result, manifest)
        if public_experimental and manifest is None:
            raise ReportContractError(
                "an experimental DetectorResult requires its exact bundled DetectorManifest"
            )
        if (
            public_experimental
            and manifest is not None
            and (
                result.get("detector_version") != manifest.get("detector_version")
                or maturity != manifest.get("maturity")
                or result.get("detector_manifest_digest") != semantic_digest(manifest)
            )
        ):
            raise ReportContractError(
                "DetectorResult identity does not match its bundled DetectorManifest"
            )
        if (
            public_experimental
            and manifest is not None
            and maturity == "experimental"
            and "finding" in manifest.get("permitted_output_types", [])
        ):
            raise ReportContractError("an experimental DetectorManifest cannot permit Findings")

    for finding in _records(bundle, "findings"):
        for result_id in finding.get("detector_result_ids", []):
            referenced_result = result_by_id.get(str(result_id))
            if (
                referenced_result is not None
                and referenced_result.get("detector_maturity") == "experimental"
            ):
                raise ReportContractError(
                    "a production Finding cannot cite an experimental DetectorResult"
                )


def _validate_method_conflict_result(
    result: Mapping[str, Any], manifest: Mapping[str, Any] | None
) -> None:
    if manifest is None:
        raise ReportContractError(
            "a method-conflict DetectorResult requires its exact bundled DetectorManifest"
        )
    if (
        manifest.get("maturity") != "experimental"
        or result.get("detector_version") != manifest.get("detector_version")
        or result.get("detector_manifest_digest") != semantic_digest(manifest)
    ):
        raise ReportContractError(
            "method-conflict DetectorResult identity does not match its experimental manifest"
        )
    extensions = result.get("extensions")
    if not isinstance(extensions, Mapping):
        raise ReportContractError("method-conflict DetectorResult extensions are malformed")
    permitted = extensions.get("x-production-finding-permitted")
    if permitted is False:
        if (
            result.get("detector_maturity") != "experimental"
            or result.get("state") == "finding_candidate"
        ):
            raise ReportContractError(
                "unqualified method-conflict result cannot carry production maturity"
            )
        return
    if permitted is not True:
        raise ReportContractError("method-conflict result has no closed production authority state")
    if result.get("state") != "finding_candidate" or result.get("detector_maturity") not in {
        "validated",
        "publication_grade",
    }:
        raise ReportContractError("qualified method-conflict result has an invalid maturity pair")
    binding_id = extensions.get("x-method-conflict-binding-id")
    pin = (
        method_conflict_grant_pins.GRANT_PINS.get(str(binding_id))
        if isinstance(binding_id, str)
        else None
    )
    if pin is None or not method_conflict_grant_pins.installed_pin_matches_live_identity(pin):
        raise ReportContractError("qualified method-conflict result has no installed exact grant")
    expected = {
        "x-method-conflict-binding-id": pin.binding_id,
        "x-method-conflict-binding-digest": pin.binding_digest,
        "x-detector-qualification-id": pin.qualification_id,
        "x-detector-qualification-digest": pin.qualification_digest,
        "x-qualification-metric-set-id": pin.metric_set_id,
        "x-qualification-metric-set-digest": pin.metric_set_digest,
        "x-threshold-policy-digest": pin.threshold_policy_digest,
    }
    if any(extensions.get(key) != value for key, value in expected.items()):
        raise ReportContractError("qualified method-conflict result grant linkage drifted")
    if (
        pin.detector_id != result.get("detector_id")
        or pin.detector_version != result.get("detector_version")
        or pin.detector_manifest_digest != result.get("detector_manifest_digest")
    ):
        raise ReportContractError("qualified method-conflict result detector grant drifted")


def _validate_root_cause_projection(bundle: Mapping[str, Any]) -> None:
    roots = _records(bundle, "adjudicated_root_causes")
    root_ids = {
        str(root["adjudicated_root_cause_id"])
        for root in roots
        if isinstance(root.get("adjudicated_root_cause_id"), str)
    }
    if len(root_ids) != len(roots):
        raise ReportContractError("AdjudicatedRootCause identities are missing or duplicated")
    for root in roots:
        if (
            root.get("material_dissent") is not False
            or root.get("confidence_used_for_identity") is not False
        ):
            raise ReportContractError(
                "an adjudicated root cause cannot retain dissent or use confidence as identity"
            )
        if not root.get("evidence") or not root.get("stronger_claims_excluded"):
            raise ReportContractError(
                "an adjudicated root cause requires evidence and stronger-claim exclusions"
            )
        _reject_strengthening(
            [root.get("bounded_statement"), *root.get("stronger_claims_excluded", [])]
        )

    for adjudication in _records(bundle, "benchmark_adjudications"):
        if adjudication.get("review_basis") == "agent_panel":
            disclosure = adjudication.get("agent_only_disclosure")
            providers = adjudication.get("provider_families")
            if (
                not isinstance(disclosure, str)
                or "not" not in disclosure.lower()
                or "human expert" not in disclosure.lower()
                or not isinstance(providers, list)
                or len(set(providers)) < 2
            ):
                raise ReportContractError(
                    "agent-panel adjudication lacks provider and non-human-expert disclosure"
                )
        refs = adjudication.get("adjudicated_root_cause_refs", [])
        referenced = {
            str(ref.get("record_id"))
            for ref in refs
            if isinstance(ref, Mapping) and ref.get("record_type") == "adjudicated_root_cause"
        }
        if not referenced <= root_ids:
            raise ReportContractError("BenchmarkAdjudication cites an absent AdjudicatedRootCause")
    for fixture in _records(bundle, "benchmark_fixtures"):
        refs = fixture.get("expected_root_cause_refs", [])
        referenced = {
            str(ref.get("record_id"))
            for ref in refs
            if isinstance(ref, Mapping) and ref.get("record_type") == "adjudicated_root_cause"
        }
        if not referenced <= root_ids:
            raise ReportContractError("BenchmarkFixture cites an absent AdjudicatedRootCause")


def _validate_stage3_projection(bundle: Mapping[str, Any]) -> None:
    candidates = _records(bundle, "detector_evaluation_candidates")
    reviews = _records(bundle, "stage3_comparison_reviews")
    outcomes = _records(bundle, "detector_case_outcomes")
    metric_sets = _records(bundle, "qualification_metric_sets")
    fixtures = _records(bundle, "benchmark_fixtures")

    candidate_ids = _unique_ids(candidates, "evaluation_candidate_id", "evaluation candidate")
    review_ids = _unique_ids(reviews, "comparison_review_id", "Stage-3 review")
    outcome_ids = _unique_ids(outcomes, "case_outcome_id", "detector case outcome")
    fixture_ids = _unique_ids(fixtures, "fixture_id", "benchmark fixture")
    fixture_by_id = {str(fixture["fixture_id"]): fixture for fixture in fixtures}
    outcome_by_id = {str(outcome["case_outcome_id"]): outcome for outcome in outcomes}
    candidate_projection: dict[str, tuple[Mapping[str, Any], str]] = {}

    for candidate in candidates:
        admission_checks = candidate.get("admission_checks")
        if (
            candidate.get("maturity_gate_bypassed_for_evaluation") is not True
            or candidate.get("production_admission_permitted") is not False
            or candidate.get("production_finding_ref") is not None
        ):
            raise ReportContractError(
                "an evaluation candidate cannot grant production Finding authority"
            )
        non_inferences = (
            admission_checks.get("non_inferences", [])
            if isinstance(admission_checks, Mapping)
            else []
        )
        if not non_inferences:
            raise ReportContractError("an evaluation candidate requires explicit non-inferences")

    for review in reviews:
        access = review.get("comparison_access")
        if (
            review.get("confidence_used_for_equivalence") is not False
            or review.get("all_candidates_accounted_for") is not True
            or review.get("all_roots_accounted_for") is not True
            or not isinstance(access, Mapping)
            or access.get("other_stage3_reviews_hidden") is not True
            or access.get("prior_review_context_reused") is not False
        ):
            raise ReportContractError("a Stage-3 review violates its closed comparison boundary")
        _require_local_refs(
            review.get("candidate_refs"), "detector_evaluation_candidate", candidate_ids
        )

    for outcome in outcomes:
        fixture_ref = outcome.get("fixture_ref")
        if (
            not isinstance(fixture_ref, Mapping)
            or fixture_ref.get("record_type") != "benchmark_fixture"
            or str(fixture_ref.get("record_id")) not in fixture_ids
        ):
            raise ReportContractError(
                "a detector case outcome has no exact bundled BenchmarkFixture"
            )
        fixture = fixture_by_id[str(fixture_ref["record_id"])]
        if (
            outcome.get("fixture_semantic_digest") != semantic_digest(dict(fixture))
            or outcome.get("qualification_proof_status")
            != fixture.get("qualification_proof_status")
            or outcome.get("problem_id") != fixture.get("problem_id")
            or outcome.get("corpus_partition") != fixture.get("corpus_partition")
            or outcome.get("fixture_kind") != fixture.get("fixture_kind")
        ):
            raise ReportContractError(
                "a detector case outcome fixture digest, proof status, or scope has drifted"
            )
        proof_evidence = fixture.get("proof_evidence")
        public_inputs = (
            proof_evidence.get("public_inputs") if isinstance(proof_evidence, Mapping) else None
        )
        static_proofs = (
            public_inputs.get("static_qualification_proofs")
            if isinstance(public_inputs, Mapping)
            else []
        )
        expected_static_ref = (
            static_proofs[0].get("record_ref")
            if isinstance(static_proofs, list)
            and len(static_proofs) == 1
            and isinstance(static_proofs[0], Mapping)
            else None
        )
        if outcome.get("static_qualification_proof_ref") != expected_static_ref:
            raise ReportContractError(
                "a detector case outcome static proof differs from its fixture proof input"
            )
        comparison_status = outcome.get("comparison_status")
        metric_eligible = outcome.get("metric_eligible")
        if outcome.get("model_free_reconciliation") is not True:
            raise ReportContractError("a detector case outcome was not reconciled model-free")
        try:
            validate_detector_case_outcome_projection(dict(outcome))
        except QualificationMetricInvariantError as error:
            raise ReportContractError(str(error)) from error
        if comparison_status == "reconciled":
            if outcome.get("exact_cross_provider_agreement") is not True:
                raise ReportContractError(
                    "a reconciled detector case lacks exact cross-provider agreement"
                )
            if outcome.get("metric_input_status") == "complete" and metric_eligible is not True:
                raise ReportContractError(
                    "a complete reconciled detector case is metric-ineligible"
                )
            if outcome.get("metric_input_status") == "legacy_source_projection_unavailable" and (
                metric_eligible is not False
                or outcome.get("promotion_evidence_eligible") is not False
            ):
                raise ReportContractError("a legacy detector case does not remain fail-closed")
        elif comparison_status == "comparison_excluded":
            if (
                metric_eligible is not False
                or outcome.get("exact_cross_provider_agreement") is not False
            ):
                raise ReportContractError("an excluded detector comparison is metric-eligible")
        else:
            raise ReportContractError("a detector case outcome has an unknown comparison status")
        if (
            outcome.get("corpus_partition") == "public_development"
            and outcome.get("promotion_evidence_eligible") is not False
        ):
            raise ReportContractError("public development outcomes cannot support promotion")
        _require_local_refs(
            outcome.get("candidate_refs"), "detector_evaluation_candidate", candidate_ids
        )
        _require_local_refs(
            outcome.get("comparison_review_refs"), "stage3_comparison_review", review_ids
        )
        projections = outcome.get("detector_result_outcomes")
        if not isinstance(projections, list):  # checked above; keeps narrowing explicit
            raise ReportContractError("detector-result opportunity projections are malformed")
        for projection in projections:
            if not isinstance(projection, Mapping):
                raise ReportContractError("detector-result opportunity projection is malformed")
            result_ref = projection.get("detector_result_ref")
            result_digest = projection.get("detector_result_digest")
            refs = projection.get("evaluation_candidate_refs")
            if (
                not isinstance(result_ref, Mapping)
                or not isinstance(result_digest, str)
                or not isinstance(refs, list)
            ):
                raise ReportContractError("detector-result opportunity projection is malformed")
            _require_local_refs(refs, "detector_evaluation_candidate", candidate_ids)
            for ref in refs:
                candidate_id = str(ref["record_id"])
                if candidate_id in candidate_projection:
                    raise ReportContractError(
                        "an evaluation candidate maps to multiple detector opportunities"
                    )
                candidate_projection[candidate_id] = (result_ref, result_digest)

    for candidate in candidates:
        candidate_id = str(candidate["evaluation_candidate_id"])
        projection = candidate_projection.get(candidate_id)
        if projection is None:
            raise ReportContractError(
                "an evaluation candidate is absent from exact detector-result projections"
            )
        if (
            candidate.get("source_detector_result_ref") != projection[0]
            or candidate.get("source_detector_result_digest") != projection[1]
        ):
            raise ReportContractError(
                "an evaluation candidate source does not match its detector-result projection"
            )

    for metric_set in metric_sets:
        if (
            metric_set.get("promotion_permitted") is not False
            or metric_set.get("numeric_threshold_policy") != "deferred_until_pilot_threshold_adr"
            or not metric_set.get("non_inferences")
        ):
            raise ReportContractError(
                "a qualification metric set grants unsupported promotion authority"
            )
        inputs = metric_set.get("case_outcome_inputs")
        if not isinstance(inputs, list) or not all(isinstance(item, Mapping) for item in inputs):
            raise ReportContractError("qualification metric-set inputs are malformed")
        _require_local_refs(
            [item.get("case_outcome_ref") for item in inputs],
            "detector_case_outcome",
            outcome_ids,
        )
        input_ids = [str(item["case_outcome_ref"]["record_id"]) for item in inputs]
        if len(set(input_ids)) != len(input_ids):
            raise ReportContractError("qualification metric-set inputs are duplicated")
        try:
            verify_qualification_metric_set(
                metric_set,
                [dict(outcome_by_id[outcome_id]) for outcome_id in input_ids],
            )
        except (KeyError, QualificationMetricInvariantError) as error:
            raise ReportContractError(str(error)) from error


def _validate_qualification_projection(bundle: Mapping[str, Any]) -> None:
    profiles = _records(bundle, "static_qualification_profiles")
    profile_ids = _unique_ids(profiles, "profile_id", "static qualification profile")
    for qualification in _records(bundle, "detector_qualifications"):
        families = qualification.get("qualification_proof_families")
        disclosure = qualification.get("static_scope_disclosure")
        gates = qualification.get("safety_gates")
        if not isinstance(families, list) or not isinstance(gates, Mapping):
            raise ReportContractError("detector qualification proof-family projection is malformed")
        if "static_closed_scope" in families:
            if (
                not isinstance(disclosure, Mapping)
                or disclosure.get("execution_claimed") is not False
                or disclosure.get("global_correctness_claimed") is not False
                or gates.get("proof_families_stratified") is not True
            ):
                raise ReportContractError(
                    "static detector qualification lacks its non-executing stratified disclosure"
                )
            refs = disclosure.get("profile_refs")
            if not isinstance(refs, list) or not refs:
                raise ReportContractError("static detector qualification has no exact profile")
            _require_local_refs(refs, "static_qualification_profile", profile_ids)
        elif disclosure is not None:
            raise ReportContractError(
                "non-static detector qualification carries a static-scope disclosure"
            )


def _validate_fixture_proof_projection(bundle: Mapping[str, Any]) -> None:
    proof_items: list[Mapping[str, Any]] = []
    for fixture in _records(bundle, "benchmark_fixtures"):
        status = fixture.get("qualification_proof_status")
        proof = fixture.get("proof_evidence")
        if status != "complete":
            if proof is not None:
                raise ReportContractError(
                    "an incomplete BenchmarkFixture carries a proof projection"
                )
            continue
        if not isinstance(proof, Mapping):
            raise ReportContractError("a complete BenchmarkFixture has no proof projection")
        public_inputs = proof.get("public_inputs")
        if not isinstance(public_inputs, Mapping):
            raise ReportContractError("fixture public proof inputs are malformed")
        for values in public_inputs.values():
            if not isinstance(values, list):
                raise ReportContractError("fixture public proof input category is malformed")
            for item in values:
                if not isinstance(item, Mapping) or not isinstance(item.get("record_ref"), Mapping):
                    raise ReportContractError("fixture public proof input is malformed")
                proof_items.append(item)

    required_identities = {
        (
            str(item["record_ref"].get("record_type", "")),
            str(item["record_ref"].get("record_id", "")),
        )
        for item in proof_items
    }
    records_by_identity: dict[tuple[str, str], Mapping[str, Any]] = {}
    for value in bundle.values():
        if not isinstance(value, list):
            continue
        for record in value:
            if not isinstance(record, Mapping) or not isinstance(record.get("record_type"), str):
                continue
            try:
                identity = record_identity(record)
            except ValueError as error:
                raise ReportContractError(str(error)) from error
            if identity not in required_identities:
                continue
            existing = records_by_identity.get(identity)
            if existing is not None and semantic_digest(dict(existing)) != semantic_digest(
                dict(record)
            ):
                raise ReportContractError(
                    f"conflicting bundled proof identity: {identity[0]}/{identity[1]}"
                )
            records_by_identity[identity] = record

    for item in proof_items:
        ref = item["record_ref"]
        key = (str(ref.get("record_type", "")), str(ref.get("record_id", "")))
        record = records_by_identity.get(key)
        if record is None:
            raise ReportContractError(f"fixture proof input does not resolve: {key[0]}/{key[1]}")
        if item.get("semantic_digest") != semantic_digest(dict(record)):
            raise ReportContractError(f"fixture proof input digest drifted: {key[0]}/{key[1]}")


def _validate_static_proof_projection(bundle: Mapping[str, Any]) -> None:
    profiles = _records(bundle, "static_qualification_profiles")
    proofs = _records(bundle, "static_qualification_proofs")
    bound_values: list[object] = []
    for profile in profiles:
        target = profile.get("target_detector")
        if isinstance(target, Mapping):
            bound_values.append(target.get("manifest"))
            parser_manifests = target.get("parser_manifests")
            if isinstance(parser_manifests, list):
                bound_values.extend(parser_manifests)
    for proof in proofs:
        bound_values.extend((proof.get("profile"), proof.get("snapshot")))
        retained = proof.get("retained_bytes")
        if isinstance(retained, list):
            for item in retained:
                if isinstance(item, Mapping):
                    bound_values.extend((item.get("file_record"), item.get("asset_identity")))
    required_identities = {
        (
            str(value["record_ref"].get("record_type", "")),
            str(value["record_ref"].get("record_id", "")),
        )
        for value in bound_values
        if isinstance(value, Mapping) and isinstance(value.get("record_ref"), Mapping)
    }

    records: dict[tuple[str, str], Mapping[str, Any]] = {}
    for value in bundle.values():
        if not isinstance(value, list):
            continue
        for record in value:
            if not isinstance(record, Mapping) or not isinstance(record.get("record_type"), str):
                continue
            try:
                identity = record_identity(record)
            except ValueError as error:
                raise ReportContractError(str(error)) from error
            if identity not in required_identities:
                continue
            existing = records.get(identity)
            if existing is not None and semantic_digest(dict(existing)) != semantic_digest(
                dict(record)
            ):
                raise ReportContractError(
                    f"conflicting bundled static-proof identity: {identity[0]}/{identity[1]}"
                )
            records[identity] = record

    profile_ids = _unique_ids(profiles, "profile_id", "static qualification profile")
    proof_ids = _unique_ids(proofs, "proof_id", "static qualification proof")
    if len(profile_ids) != len(profiles) or len(proof_ids) != len(proofs):
        raise ReportContractError("static qualification identities are incomplete")
    for profile in profiles:
        target = profile.get("target_detector")
        if not isinstance(target, Mapping):
            raise ReportContractError("static qualification profile target is malformed")
        _require_bound_record(target.get("manifest"), records)
        parser_manifests = target.get("parser_manifests")
        if not isinstance(parser_manifests, list) or not parser_manifests:
            raise ReportContractError("static qualification parser envelope is absent")
        for bound in parser_manifests:
            _require_bound_record(bound, records)
        detector_ref = target["manifest"]["record_ref"]
        detector = records[(str(detector_ref["record_type"]), str(detector_ref["record_id"]))]
        implementation = detector.get("implementation")
        if not isinstance(implementation, Mapping) or target.get(
            "implementation_digest"
        ) != implementation.get("implementation_digest"):
            raise ReportContractError("static profile detector implementation identity drifted")
    for proof in proofs:
        _require_bound_record(proof.get("profile"), records)
        _require_bound_record(proof.get("snapshot"), records)
        retained = proof.get("retained_bytes")
        if not isinstance(retained, list):
            raise ReportContractError("static proof retained-byte inventory is malformed")
        for item in retained:
            if not isinstance(item, Mapping):
                raise ReportContractError("static proof retained-byte entry is malformed")
            _require_bound_record(item.get("file_record"), records)
            _require_bound_record(item.get("asset_identity"), records)
            file_ref = item["file_record"]["record_ref"]
            identity_ref = item["asset_identity"]["record_ref"]
            file_record = records[(str(file_ref["record_type"]), str(file_ref["record_id"]))]
            asset_identity = records[
                (str(identity_ref["record_type"]), str(identity_ref["record_id"]))
            ]
            evidence = asset_identity.get("identity_evidence")
            if (
                file_record.get("path") != item.get("path")
                or file_record.get("byte_size") != item.get("byte_size")
                or not isinstance(evidence, Mapping)
                or evidence.get("kind") != "full_digest"
                or evidence.get("digest") != item.get("content_digest")
            ):
                raise ReportContractError("static proof retained-byte identity projection drifted")


def _require_bound_record(
    value: object,
    records: Mapping[tuple[str, str], Mapping[str, Any]],
) -> None:
    if not isinstance(value, Mapping) or not isinstance(value.get("record_ref"), Mapping):
        raise ReportContractError("static qualification bound record is malformed")
    reference = value["record_ref"]
    key = (str(reference.get("record_type", "")), str(reference.get("record_id", "")))
    record = records.get(key)
    if record is None:
        raise ReportContractError(
            f"static qualification dependency does not resolve: {key[0]}/{key[1]}"
        )
    if value.get("semantic_digest") != semantic_digest(dict(record)):
        raise ReportContractError(
            f"static qualification dependency digest drifted: {key[0]}/{key[1]}"
        )


def _unique_ids(records: list[Mapping[str, Any]], field: str, label: str) -> set[str]:
    identities = {str(record[field]) for record in records if isinstance(record.get(field), str)}
    if len(identities) != len(records):
        raise ReportContractError(f"{label} identities are missing or duplicated")
    return identities


def _require_local_refs(value: Any, record_type: str, identities: set[str]) -> None:
    if not isinstance(value, list):
        raise ReportContractError(f"{record_type} references are malformed")
    observed = {
        str(ref.get("record_id"))
        for ref in value
        if isinstance(ref, Mapping) and ref.get("record_type") == record_type
    }
    if len(observed) != len(value) or not observed <= identities:
        raise ReportContractError(f"a {record_type} reference does not resolve in the bundle")


def _validate_performance_projection(bundle: Mapping[str, Any]) -> None:
    run_id = bundle.get("audit_run_id")
    records = _records(bundle, "performance_records")
    if records and len(records) != 1:
        raise ReportContractError(
            "a measured semantic-lock report requires exactly one bounded PerformanceRecord"
        )
    for record in records:
        extensions = record.get("extensions", {})
        termination = record.get("termination", {})
        timings = record.get("stage_timings", [])
        if record.get("audit_run_id") != run_id:
            raise ReportContractError("PerformanceRecord belongs to another AuditRun")
        if (
            not isinstance(extensions, Mapping)
            or extensions.get("x-measurement-boundary") != "semantic_lock"
            or extensions.get("x-postlock-elapsed-included") is not False
            or extensions.get("x-io-measurement-scope") != "snapshot_identity_reads_only"
            or extensions.get("x-cache-scope") != "current_audit_run_parser_cache_only"
            or extensions.get("x-model-usage-scope") != "controller_initiated_provider_calls_only"
        ):
            raise ReportContractError("PerformanceRecord does not identify its bounded lock scope")
        if (
            not isinstance(termination, Mapping)
            or termination.get("state") != "partial"
            or termination.get("reason") != "other"
        ):
            raise ReportContractError("PerformanceRecord overstates its measurement interval")
        if (
            not isinstance(timings, list)
            or len(timings) != 1
            or not isinstance(timings[0], Mapping)
            or timings[0].get("stage") != "through_semantic_lock"
            or timings[0].get("state") != "complete"
            or timings[0].get("elapsed_seconds") != record.get("user_visible_elapsed_seconds")
        ):
            raise ReportContractError("PerformanceRecord stage boundary is malformed")
        model_usage = record.get("model_usage")
        if not isinstance(model_usage, Mapping) or model_usage.get("calls") != 0:
            raise ReportContractError(
                "PerformanceRecord model usage exceeds the controller-observed call scope"
            )


def _typed_refs(value: Any) -> Iterable[tuple[str, str]]:
    if isinstance(value, Mapping):
        record_type = value.get("record_type")
        record_id = value.get("record_id")
        if isinstance(record_type, str) and isinstance(record_id, str):
            yield record_type, record_id
            return
        for item in value.values():
            yield from _typed_refs(item)
    elif isinstance(value, list):
        for item in value:
            yield from _typed_refs(item)


def _finding_links_qualified_method_result(
    finding: Mapping[str, Any], bundle: Mapping[str, Any]
) -> bool:
    extensions = finding.get("extensions")
    result_ids = finding.get("detector_result_ids")
    if (
        finding.get("issue_class") != "x-review-scoped-analysis-method-requirement-mismatch"
        or not isinstance(extensions, Mapping)
        or not isinstance(result_ids, list)
        or len(result_ids) != 1
        or not isinstance(result_ids[0], str)
    ):
        return False
    matches = [
        result
        for result in _records(bundle, "detector_results")
        if result.get("result_id") == result_ids[0]
    ]
    if len(matches) != 1:
        return False
    result_extensions = matches[0].get("extensions")
    return (
        matches[0].get("state") == "finding_candidate"
        and isinstance(result_extensions, Mapping)
        and result_extensions.get("x-production-finding-permitted") is True
        and result_extensions.get("x-method-conflict-binding-id")
        == extensions.get("x-method-conflict-binding-id")
        and result_extensions.get("x-method-conflict-binding-digest")
        == extensions.get("x-method-conflict-binding-digest")
    )


def _require_source_evidence(
    finding: Mapping[str, Any], *, allow_method_record_evidence: bool = False
) -> None:
    evidence = finding.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ReportContractError("every Finding requires evidence")
    source_bearing = 0
    for item in evidence:
        if not isinstance(item, Mapping):
            raise ReportContractError("every Finding evidence item requires a source reference")
        if item.get("source_refs"):
            source_bearing += 1
        elif not allow_method_record_evidence or not item.get("record_refs"):
            raise ReportContractError("every Finding evidence item requires a source reference")
    if allow_method_record_evidence and source_bearing == 0:
        raise ReportContractError("a method-conflict Finding requires source-bearing evidence")


def _reject_strengthening(values: Iterable[Any]) -> None:
    for value in values:
        if not isinstance(value, str):
            continue
        if any(pattern.search(value) for pattern in _PROHIBITED_STRENGTHENING):
            raise ReportContractError(f"prohibited report strengthening: {value}")


def _list_length(bundle: Mapping[str, Any], field: str) -> int:
    value = bundle.get(field)
    if not isinstance(value, list):
        raise ReportContractError(f"bundle field is not an array: {field}")
    return len(value)


def _records(bundle: Mapping[str, Any], field: str) -> list[Mapping[str, Any]]:
    value = bundle.get(field)
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        raise ReportContractError(f"bundle field contains malformed records: {field}")
    return value
