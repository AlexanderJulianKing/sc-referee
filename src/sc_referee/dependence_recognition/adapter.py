"""Unregistered report-only shadow adapter for dependence recognition v1.

This module has no scientific-check or detector registration side effect.  It
orchestrates the untrusted static analyzer, controller-owned trusted channels,
the certificate kernel, and the unchanged domain-neutral dependence evaluator.
Every exception at those boundaries becomes a named non-accusatory abstention.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.dependence_core import DependenceEvaluation, evaluate_dependence_case
from sc_referee.dependence_recognition.ir import RecordRef, VerifiedDependenceCertificate
from sc_referee.dependence_recognition.python_analyzer import (
    DischargedDependenceAnalysis,
    PythonDependenceAnalysis,
    analyze_dependence_python,
    discharge_dependence_proposal,
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
_EXPERIMENT_PATH = "docs/implementation/EXPERIMENT-0058-DEPENDENCE-SEMANTIC-V1-SHADOW.md"
_PACKAGED_EXPERIMENT_PATH = (
    _HERE.parent / "resources" / "dependence-recognition" / Path(_EXPERIMENT_PATH).name
)

# Deliberately package-local.  The binding directive excludes founder files,
# dependence_core.py, registry resources, and every production integration.
DEPENDENCE_RECOGNITION_PACKAGE_FILES: tuple[str, ...] = (
    "__init__.py",
    "adapter.py",
    "certificate.py",
    "csv_domain.py",
    "ir.py",
    "python_analyzer.py",
)
DEPENDENCE_RECOGNITION_DEPENDENCY_FILES: tuple[str, ...] = (
    *(
        f"src/sc_referee/dependence_recognition/{name}"
        for name in DEPENDENCE_RECOGNITION_PACKAGE_FILES
    ),
    _EXPERIMENT_PATH,
)

_NON_INFERENCES: tuple[str, ...] = (
    "Project-authored code was not executed.",
    "The shadow result does not establish that a published value came from the inspected code.",
    "No numerical impact, bias direction, biological truth, or global invalidity is inferred.",
    "The shadow result is not a Finding and grants no production admission authority.",
)
_SUPPORTED_PYTHON_PARSER_IDENTITIES = frozenset(
    {
        ("python-ast", "3.11"),
        ("parser:python-ast-tokenize", "0.15.1"),
    }
)


def dependence_recognition_dependency_closure() -> dict[str, str]:
    """Return exact hashes for only this package and its experiment record."""

    return {
        **{
            f"src/sc_referee/dependence_recognition/{name}": sha256_digest(
                (_HERE / name).read_bytes()
            )
            for name in DEPENDENCE_RECOGNITION_PACKAGE_FILES
        },
        _EXPERIMENT_PATH: sha256_digest(
            (
                _REPOSITORY_ROOT / _EXPERIMENT_PATH
                if (_REPOSITORY_ROOT / _EXPERIMENT_PATH).is_file()
                else _PACKAGED_EXPERIMENT_PATH
            ).read_bytes()
        ),
    }


DEPENDENCE_RECOGNITION_DEPENDENCY_CLOSURE = dependence_recognition_dependency_closure()
DEPENDENCE_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST = semantic_digest(
    {"dependency_closure": DEPENDENCE_RECOGNITION_DEPENDENCY_CLOSURE}
)
DEPENDENCE_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST = (
    DEPENDENCE_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST
)


@dataclass(frozen=True)
class DependenceRecognitionShadowAdapter:
    """Project one bounded static dependence case onto the shadow plane."""

    adapter_id: str = "dependence-recognition-semantic-shadow"
    adapter_version: str = "1.1.0"

    @property
    def implementation_digest(self) -> str:
        return DEPENDENCE_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST

    def inspect(self, context: FrozenInspectionContext) -> ShadowPayload:
        """Inspect frozen material without executing author code; never raise."""

        try:
            parser_id, parser_version = _closed_python_parser_identity(context)
            analysis = analyze_dependence_python(
                context,
                parser_id=parser_id,
                parser_version=parser_version,
            )
        except BaseException:
            return self._exception_abstention("analyzer-exception")

        try:
            discharged = discharge_dependence_proposal(analysis, context)
        except BaseException:
            # The prover and certificate kernel are both inside this
            # controller boundary, so either failure has the same safe route.
            return self._exception_abstention("controller-discharge-exception")

        if discharged.case is None:
            coverage_class = (
                "no-supported-dependence-lineage"
                if discharged.state == "not_applicable"
                else "dependence-case-unavailable"
            )
            return self._abstention(
                reason_code="case_unavailable",
                basis=discharged.basis,
                coverage_classes=(coverage_class,),
            )

        try:
            evaluation = evaluate_dependence_case(discharged.case)
        except BaseException:
            return self._exception_abstention("dependence-core-exception")

        try:
            return self._project(analysis, discharged, evaluation)
        except BaseException:
            return self._exception_abstention("shadow-projection-exception")

    def _project(
        self,
        analysis: PythonDependenceAnalysis,
        discharged: DischargedDependenceAnalysis,
        evaluation: DependenceEvaluation,
    ) -> ShadowPayload:
        if evaluation.outcome in {"evaluation_candidate", "covered_negative"}:
            verified = discharged.verified_certificate
            if discharged.state != "verified" or verified is None:
                return self._abstention(
                    reason_code="verified_certificate_required",
                    basis=(
                        "A candidate or covered-negative projection requires one accepted "
                        "dependence certificate."
                    ),
                    coverage_classes=("verified-certificate-required",),
                    case_digest=evaluation.case_digest,
                )
            expected_conclusion = (
                "repeated_units"
                if evaluation.outcome == "evaluation_candidate"
                else "one_observation_per_unit"
            )
            if verified.conclusion != expected_conclusion:
                return self._abstention(
                    reason_code="conclusion-outcome-mismatch",
                    basis=(
                        "The accepted certificate conclusion did not match the unchanged "
                        "dependence evaluator outcome, so the shadow adapter emitted no "
                        "candidate or clearance."
                    ),
                    coverage_classes=("conclusion-outcome-mismatch",),
                    case_digest=evaluation.case_digest,
                )
            if evaluation.outcome == "evaluation_candidate":
                return self._candidate(evaluation, verified)
            return self._coverage_note(evaluation, verified)

        if evaluation.outcome == "question":
            return self._question(analysis, evaluation)
        return self._unsupported(analysis, discharged, evaluation)

    def _candidate(
        self,
        evaluation: DependenceEvaluation,
        verified: VerifiedDependenceCertificate,
    ) -> ShadowPayload:
        body = {
            "record_type": "dependence_shadow_candidate",
            "candidate_id": f"dependence-shadow-candidate:{semantic_digest({'case_digest': evaluation.case_digest, 'source_digest': verified.source_digest})}",
            "report_only": True,
            "promotion_state": "unregistered_shadow_only",
            "statement": (
                "The accepted static certificate relates repeated rows sharing the "
                "human-authorized independent-unit key to separate inputs of the exact "
                f"{verified.procedure_call.resolved_callable} call whose result token reaches "
                "the selected sink; no registered v1 safeguard form was present in that "
                "closed static slice."
            ),
            **_verified_projection(verified),
            "repeated_independent_unit_ids": list(evaluation.repeated_independent_unit_ids),
            "applicable_safeguard_ids": list(evaluation.applicable_safeguard_ids),
        }
        return self._payload(
            payload_type="shadow_candidate",
            outcome=evaluation.outcome,
            reason_code=evaluation.reason_code,
            basis=evaluation.basis,
            case_digest=evaluation.case_digest,
            body=body,
        )

    def _coverage_note(
        self,
        evaluation: DependenceEvaluation,
        verified: VerifiedDependenceCertificate,
    ) -> ShadowPayload:
        applicable_safeguards = verified.applicable_safeguard_ids
        coverage_class = "one_observation_per_independent_unit"
        statement = (
            "The accepted static certificate and digest-bound membership proof establish "
            "one analyzed observation per human-authorized independent unit."
        )
        body = {
            "record_type": "dependence_shadow_coverage_note",
            "coverage_class": coverage_class,
            "core_reason_code": evaluation.reason_code,
            "report_only": True,
            "statement": statement,
            **_verified_projection(verified),
            "applicable_safeguard_ids": list(applicable_safeguards),
            "repeated_independent_unit_ids": list(evaluation.repeated_independent_unit_ids),
        }
        return self._payload(
            payload_type="coverage_note",
            outcome=evaluation.outcome,
            reason_code=evaluation.reason_code,
            basis=evaluation.basis,
            case_digest=evaluation.case_digest,
            body=body,
        )

    def _question(
        self,
        analysis: PythonDependenceAnalysis,
        evaluation: DependenceEvaluation,
    ) -> ShadowPayload:
        candidates = tuple(dict.fromkeys(analysis.candidate_key_columns))
        unresolved = tuple(
            sorted({*analysis.unresolved_dimensions, *evaluation.unresolved_dimensions})
        )
        body = {
            "record_type": "dependence_shadow_material_question",
            "question_id": f"dependence-shadow-question:{semantic_digest({'case_digest': evaluation.case_digest, 'candidate_key_columns': candidates, 'unresolved_dimensions': unresolved})}",
            "unknown_semantic_dimension": "independent_unit_definition",
            "prompt": (
                "Which ordered CSV column tuple, if any, is the human-authorized "
                "independent-unit key for this exact analysis and procedure?"
            ),
            "candidate_key_columns": list(candidates),
            "candidate_dimensions": [
                {"column": column, "selection_state": "unresolved"} for column in candidates
            ],
            "ordered_composite_key_state": "unresolved",
            "none_of_these_option": True,
            "ranking": None,
            "unresolved_dimensions": list(unresolved),
        }
        return self._payload(
            payload_type="material_question",
            outcome=evaluation.outcome,
            reason_code=evaluation.reason_code,
            basis=evaluation.basis,
            case_digest=evaluation.case_digest,
            body=body,
        )

    def _unsupported(
        self,
        analysis: PythonDependenceAnalysis,
        discharged: DischargedDependenceAnalysis,
        evaluation: DependenceEvaluation,
    ) -> ShadowPayload:
        case_constructs = (
            discharged.case.unsupported_constructs if discharged.case is not None else ()
        )
        coverage_classes = tuple(
            sorted(
                {
                    *analysis.unsupported_constructs,
                    *case_constructs,
                    *evaluation.unsupported_constructs,
                }
            )
        ) or ("unsupported-dependence-recognition-path",)
        return self._abstention(
            reason_code=evaluation.reason_code,
            basis=evaluation.basis,
            coverage_classes=coverage_classes,
            case_digest=evaluation.case_digest,
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
            "record_type": "dependence_recognition_shadow_abstention",
            "coverage_classes": list(coverage_classes),
            "accusatory_output": False,
            "statement": (
                "The static dependence recognizer abstained because the workflow is outside "
                "a closed v1 evidence path; no adverse scientific conclusion is asserted."
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
            "record_type": "dependence_recognition_shadow_result",
            "schema_version": "1.1.0",
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "adapter_implementation_digest": self.implementation_digest,
            "implementation_dependency_closure_digest": (
                DEPENDENCE_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST
            ),
            "implementation_dependency_closure": dict(DEPENDENCE_RECOGNITION_DEPENDENCY_CLOSURE),
            "delivery_plane": "unregistered_shadow_report_only",
            "outcome": outcome,
            "payload_type": payload_type,
            "reason_code": reason_code,
            "basis": basis,
            "case_digest": case_digest,
            "output_ceiling": "evaluation_candidate",
            "wording_ceiling": "static_code_relationship_only",
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


def _verified_projection(verified: VerifiedDependenceCertificate) -> dict[str, Any]:
    """Project the exact accepted certificate bindings and evidence declarations."""

    binding = verified.case_binding
    fact = verified.domain_fact
    return {
        "source_path": verified.source_path,
        "source_digest": verified.source_digest,
        "analysis_target_ref": _ref_dict(binding.analysis_target_ref),
        "procedure_ref": _ref_dict(binding.procedure_ref),
        "affected_target_ref": _ref_dict(binding.affected_target_ref),
        "independent_unit_definition_id": binding.independent_unit_definition_id,
        "authorized_key_columns": list(binding.authorized_key_columns),
        "input_binding": {"path": fact.path, "content_digest": fact.content_digest},
        "resolved_callable": verified.procedure_call.resolved_callable,
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
