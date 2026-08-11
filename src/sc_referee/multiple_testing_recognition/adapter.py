"""Unregistered report-only shadow adapter for multiple-testing recognition v1.

This module has no scientific-check or detector registration side effect. It
orchestrates the untrusted static analyzer, controller-owned p-value facts and
family authority, and the certificate kernel. Candidate and coverage payloads
require an accepted certificate with a matching conclusion. Questions and
unsupported cases remain non-accusatory and do not require kernel acceptance.
Every ``BaseException`` at an orchestration boundary becomes a named
abstention; project-authored code is never imported or executed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.multiple_testing_recognition.ir import (
    RecordRef,
    VerifiedMultipleTestingCertificate,
)
from sc_referee.multiple_testing_recognition.python_analyzer import (
    DischargedMultipleTestingAnalysis,
    PythonMultipleTestingAnalysis,
    analyze_multiple_testing_python,
    discharge_multiple_testing_proposal,
)
from sc_referee.scientific_checks.core import FrozenInspectionContext

ShadowPayload = dict[str, Any]
ShadowPayloadType = Literal[
    "shadow_candidate",
    "material_question",
    "abstention",
    "coverage_note",
]

_HERE = Path(__file__).resolve().parent
_REPOSITORY_ROOT = _HERE.parents[2]
_EXPERIMENT_PATH = "docs/implementation/EXPERIMENT-0059-MULTIPLE-TESTING-SEMANTIC-V1-SHADOW.md"

# Deliberately package-local. No dependence, founder, registry, production
# integration, or calculation-check file is admitted to this shadow closure.
MULTIPLE_TESTING_RECOGNITION_PACKAGE_FILES: tuple[str, ...] = (
    "__init__.py",
    "adapter.py",
    "certificate.py",
    "ir.py",
    "pvalue_domain.py",
    "test_argument_domain.py",
    "python_analyzer.py",
)
MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_FILES: tuple[str, ...] = (
    *(
        f"src/sc_referee/multiple_testing_recognition/{name}"
        for name in MULTIPLE_TESTING_RECOGNITION_PACKAGE_FILES
    ),
    _EXPERIMENT_PATH,
)

_NON_INFERENCES: tuple[str, ...] = (
    "Project-authored code was not executed.",
    "The supported normal-path expansion is not a claim of historical execution.",
    "No numerical impact, bias direction, scientific invalidity, or required repair is inferred.",
    "The shadow result is not a Finding and grants no production admission authority.",
)
_SUPPORTED_PYTHON_PARSER_IDENTITIES = frozenset({("python-ast", "3.11")})


def multiple_testing_recognition_dependency_closure() -> dict[str, str]:
    """Return exact hashes for only this package and Experiment 0059."""

    return {
        relative_path: sha256_digest((_REPOSITORY_ROOT / relative_path).read_bytes())
        for relative_path in MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_FILES
    }


MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_CLOSURE = multiple_testing_recognition_dependency_closure()
MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST = semantic_digest(
    {"dependency_closure": MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_CLOSURE}
)
MULTIPLE_TESTING_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST = (
    MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST
)


@dataclass(frozen=True)
class MultipleTestingRecognitionShadowAdapter:
    """Project one bounded static multiple-testing case onto the shadow plane."""

    adapter_id: str = "multiple-testing-recognition-semantic-shadow"
    adapter_version: str = "1.1.0"

    @property
    def implementation_digest(self) -> str:
        return MULTIPLE_TESTING_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST

    def inspect(self, context: FrozenInspectionContext) -> ShadowPayload:
        """Inspect frozen material without executing author code; never raise."""

        try:
            parser_id, parser_version = _closed_python_parser_identity(context)
            analysis = analyze_multiple_testing_python(
                context,
                parser_id=parser_id,
                parser_version=parser_version,
            )
        except BaseException:
            return self._exception_abstention("analyzer-exception")

        try:
            discharged = discharge_multiple_testing_proposal(analysis, context)
        except BaseException:
            # The digest-bound prover and certificate kernel are both inside
            # this controller boundary, so either failure takes the same safe route.
            return self._exception_abstention("controller-discharge-exception")

        try:
            return self._project(analysis, discharged)
        except BaseException:
            return self._exception_abstention("shadow-projection-exception")

    def _project(
        self,
        analysis: PythonMultipleTestingAnalysis,
        discharged: DischargedMultipleTestingAnalysis,
    ) -> ShadowPayload:
        if discharged.outcome in {"evaluation_candidate", "covered_negative"}:
            verified = discharged.verified_certificate
            if (
                analysis.state != "proposal"
                or analysis.certificate is None
                or discharged.state != "verified"
                or discharged.certificate is None
                or verified is None
            ):
                return self._abstention(
                    reason_code="verified_certificate_required",
                    basis=(
                        "A candidate or coverage projection requires one accepted "
                        "multiple-testing certificate."
                    ),
                    coverage_classes=("verified-certificate-required",),
                )
            proposal = analysis.certificate
            if (proposal.source_path, proposal.source_digest, proposal.proposed_case_digest) != (
                discharged.certificate.source_path,
                discharged.certificate.source_digest,
                discharged.certificate.proposed_case_digest,
            ) or (verified.source_path, verified.source_digest, verified.proposed_case_digest) != (
                proposal.source_path,
                proposal.source_digest,
                proposal.proposed_case_digest,
            ):
                return self._abstention(
                    reason_code="analysis-discharge-binding-mismatch",
                    basis=(
                        "The verified controller result did not bind the analyzer proposal "
                        "for this exact source and case."
                    ),
                    coverage_classes=("analysis-discharge-binding-mismatch",),
                )
            expected_conclusion = (
                "correction_subset"
                if discharged.outcome == "evaluation_candidate"
                else "complete_family_correction"
            )
            if verified.conclusion != expected_conclusion:
                return self._abstention(
                    reason_code="conclusion-outcome-mismatch",
                    basis=(
                        "The accepted certificate conclusion did not match the controller "
                        "outcome, so the shadow adapter emitted no candidate or coverage note."
                    ),
                    coverage_classes=("conclusion-outcome-mismatch",),
                    case_digest=verified.proposed_case_digest,
                )
            if discharged.outcome == "evaluation_candidate":
                return self._candidate(verified)
            return self._coverage_note(verified)

        if discharged.outcome == "question":
            return self._question(analysis, discharged)
        if discharged.outcome in {"unsupported", "not_applicable"}:
            return self._unsupported(analysis, discharged)
        return self._abstention(
            reason_code="unrecognized-controller-outcome",
            basis="The controller returned no closed v1 shadow outcome.",
            coverage_classes=("unrecognized-controller-outcome",),
        )

    def _candidate(
        self,
        verified: VerifiedMultipleTestingCertificate,
    ) -> ShadowPayload:
        body = {
            "record_type": "multiple_testing_shadow_candidate",
            "candidate_id": (
                "multiple-testing-shadow-candidate:"
                + semantic_digest(
                    {
                        "case_digest": verified.proposed_case_digest,
                        "source_digest": verified.source_digest,
                        "corrected_positions": verified.corrected_positions,
                    }
                )
            ),
            "report_only": True,
            "promotion_state": "unregistered_shadow_only",
            "statement": (
                "The accepted static certificate establishes that, on supported normal "
                "paths reaching the correction call, the correction input is a strict "
                "position-derived subset of the certified ordered test battery while the "
                "selected sink binds the complete battery."
            ),
            **_verified_projection(verified),
        }
        return self._payload(
            payload_type="shadow_candidate",
            outcome="evaluation_candidate",
            reason_code="strict_subset_correction",
            basis=(
                "Kernel replay proved a nonempty strict correction subset and an exact "
                "complete-family report binding."
            ),
            case_digest=verified.proposed_case_digest,
            body=body,
        )

    def _coverage_note(
        self,
        verified: VerifiedMultipleTestingCertificate,
    ) -> ShadowPayload:
        body = {
            "record_type": "multiple_testing_shadow_coverage_note",
            "coverage_class": "complete_family_correction",
            "report_only": True,
            "statement": (
                "The accepted static certificate establishes that, on supported normal "
                "paths reaching the correction call, the complete certified ordered test "
                "battery enters the correction call and reaches the selected sink binding."
            ),
            **_verified_projection(verified),
        }
        return self._payload(
            payload_type="coverage_note",
            outcome="covered_negative",
            reason_code="complete_family_correction",
            basis="Kernel replay proved exact full-family correction and report binding.",
            case_digest=verified.proposed_case_digest,
            body=body,
        )

    def _question(
        self,
        analysis: PythonMultipleTestingAnalysis,
        discharged: DischargedMultipleTestingAnalysis,
    ) -> ShadowPayload:
        batteries = tuple(dict.fromkeys(analysis.candidate_battery_ids))
        columns = tuple(dict.fromkeys(analysis.candidate_family_key_columns))
        unresolved = tuple(sorted(set(analysis.unresolved_dimensions)))
        body = {
            "record_type": "multiple_testing_shadow_material_question",
            "question_id": (
                "multiple-testing-shadow-question:"
                + semantic_digest(
                    {
                        "candidate_batteries": batteries,
                        "candidate_family_key_columns": columns,
                        "unresolved_dimensions": unresolved,
                    }
                )
            ),
            "unknown_semantic_dimension": "authorized_pvalue_family",
            "prompt": (
                "Which candidate battery, if any, is the human-authorized all-rows "
                "p-value family for this exact analysis and correction procedure?"
            ),
            "candidate_batteries": [
                {
                    "battery_construct_id": battery_id,
                    "selection_state": "unresolved",
                    "candidate_family_key_columns": list(columns),
                }
                for battery_id in batteries
            ],
            "candidate_family_key_columns": list(columns),
            "candidate_dimensions": [
                {"column": column, "selection_state": "unresolved"} for column in columns
            ],
            "none_of_these_option": True,
            "ranking": None,
            "unresolved_dimensions": list(unresolved),
        }
        return self._payload(
            payload_type="material_question",
            outcome="question",
            reason_code="family_definition_unresolved",
            basis=discharged.basis,
            case_digest=None,
            body=body,
        )

    def _unsupported(
        self,
        analysis: PythonMultipleTestingAnalysis,
        discharged: DischargedMultipleTestingAnalysis,
    ) -> ShadowPayload:
        coverage_classes = tuple(
            sorted(
                {
                    *analysis.unsupported_constructs,
                    *((discharged.failure_class,) if discharged.failure_class else ()),
                    *(
                        ("no-registered-test-battery",)
                        if discharged.outcome == "not_applicable"
                        else ()
                    ),
                }
            )
        ) or ("unsupported-multiple-testing-recognition-path",)
        return self._abstention(
            reason_code=(
                "not_applicable"
                if discharged.outcome == "not_applicable"
                else "unsupported_static_path"
            ),
            basis=discharged.basis,
            coverage_classes=coverage_classes,
        )

    def _exception_abstention(self, failure_class: str) -> ShadowPayload:
        return self._abstention(
            reason_code="adapter_pipeline_exception",
            basis=(
                "The shadow adapter caught an internal analysis boundary exception and "
                "produced no scientific assertion."
            ),
            coverage_classes=(failure_class,),
        )

    def _abstention(
        self,
        *,
        reason_code: str,
        basis: str,
        coverage_classes: tuple[str, ...],
        case_digest: str | None = None,
    ) -> ShadowPayload:
        body = {
            "record_type": "multiple_testing_recognition_shadow_abstention",
            "coverage_classes": list(coverage_classes),
            "accusatory_output": False,
            "statement": (
                "The static multiple-testing recognizer abstained because the workflow is "
                "outside a closed v1 evidence path; no adverse scientific conclusion is "
                "asserted."
            ),
        }
        return self._payload(
            payload_type="abstention",
            outcome="unsupported",
            reason_code=reason_code,
            basis=basis,
            case_digest=case_digest,
            body=body,
        )

    def _payload(
        self,
        *,
        payload_type: ShadowPayloadType,
        outcome: str,
        reason_code: str,
        basis: str,
        case_digest: str | None,
        body: dict[str, Any],
    ) -> ShadowPayload:
        return {
            "record_type": "multiple_testing_recognition_shadow_result",
            "schema_version": "1.0.0",
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "adapter_implementation_digest": self.implementation_digest,
            "implementation_dependency_closure_digest": (
                MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST
            ),
            "implementation_dependency_closure": dict(
                MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_CLOSURE
            ),
            "delivery_plane": "unregistered_shadow_report_only",
            "outcome": outcome,
            "payload_type": payload_type,
            "reason_code": reason_code,
            "basis": basis,
            "case_digest": case_digest,
            "output_ceiling": "report_only",
            "wording_ceiling": "supported_normal_path_static_relationship_only",
            "non_inferences": list(_NON_INFERENCES),
            "payload": body,
        }


def _ref_dict(value: RecordRef) -> dict[str, str]:
    return {"record_type": value.record_type, "record_id": value.record_id}


def _closed_python_parser_identity(context: FrozenInspectionContext) -> tuple[str, str]:
    """Select one exact allowlisted parser identity or force analyzer refusal."""

    identities: set[tuple[str, str]] = set()
    for document in context.documents:
        if document.media_type != "text/x-python":
            continue
        try:
            payload = json.loads(document.parser_result_payload or b"")
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
            return ("unsupported-python-parser", "unsupported")
        if not isinstance(payload, dict):
            return ("unsupported-python-parser", "unsupported")
        parser_id = payload.get("parser_id")
        parser_version = payload.get("parser_version")
        if not isinstance(parser_id, str) or not isinstance(parser_version, str):
            return ("unsupported-python-parser", "unsupported")
        identities.add((parser_id, parser_version))
    if not identities:
        return ("python-ast", "3.11")
    if len(identities) != 1:
        return ("unsupported-python-parser", "unsupported")
    identity = next(iter(identities))
    return (
        identity
        if identity in _SUPPORTED_PYTHON_PARSER_IDENTITIES
        else ("unsupported-python-parser", "unsupported")
    )


def _verified_projection(
    verified: VerifiedMultipleTestingCertificate,
) -> dict[str, Any]:
    """Project exact accepted bindings, derived positions, and evidence spans."""

    binding = verified.case_binding
    fact = verified.family_fact
    argument_fact = verified.test_argument_fact
    authority = verified.family_authorization
    return {
        "source_path": verified.source_path,
        "source_digest": verified.source_digest,
        "analysis_target_ref": _ref_dict(binding.analysis_target_ref),
        "correction_procedure_ref": _ref_dict(binding.correction_procedure_ref),
        "affected_target_ref": _ref_dict(binding.affected_target_ref),
        "family_definition_id": binding.family_definition_id,
        "battery_construct_id": binding.battery_construct_id,
        "iterable_row_domain": binding.iterable_row_domain,
        "authorized_family_key_columns": list(binding.authorized_family_key_columns),
        "family_authorization": {
            "record_id": authority.record_id,
            "actor_id": authority.actor_id,
            "family_member_rule": authority.family_member_rule,
        },
        "input_binding": {"path": fact.path, "content_digest": fact.content_digest},
        "measurement_input_binding": {
            "path": argument_fact.path,
            "content_digest": argument_fact.content_digest,
        },
        "measurement_key_columns": list(argument_fact.measurement_key_columns),
        "left_measurement_columns": list(argument_fact.left_measurement_columns),
        "right_measurement_columns": list(argument_fact.right_measurement_columns),
        "argument_vector_tokens": [
            list(position.argument_vector_tokens) for position in verified.test_result_positions
        ],
        "performed_count": len(verified.performed_result_tokens),
        "corrected_count": len(verified.corrected_result_tokens),
        "corrected_positions": list(verified.corrected_positions),
        "sink_tokens": list(verified.sink_tokens),
        "proposed_case_digest": verified.proposed_case_digest,
        "evidence_declarations": [
            {
                "evidence_id": declaration.evidence_id,
                "path": declaration.point.path,
                "start_line": declaration.point.start_line,
                "end_line": declaration.point.end_line,
                "start_column": declaration.point.start_column,
                "end_column": declaration.point.end_column,
            }
            for declaration in verified.evidence
        ],
    }


__all__ = [
    "MULTIPLE_TESTING_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST",
    "MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST",
    "MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_FILES",
    "MULTIPLE_TESTING_RECOGNITION_PACKAGE_FILES",
    "MultipleTestingRecognitionShadowAdapter",
    "multiple_testing_recognition_dependency_closure",
]
