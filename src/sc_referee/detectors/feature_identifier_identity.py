from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from sc_referee.calculation_checks.feature_identifier_identity import (
    EXACT_IDENTITY_RELATION,
    FEATURE_IDENTIFIER_IDENTITY_CHECK_ID,
    FEATURE_IDENTIFIER_IDENTITY_DIMENSION,
)
from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.version import SCHEMA_VERSION, __version__


class FeatureIdentifierIdentityDetectorError(ValueError):
    """Raised when the feature-identity detector manifest or target drifts."""


class BoundedFeatureIdentifierIdentityDetector:
    """Bind one exact set comparison to one review-scoped human requirement."""

    detector_id = "detector:bounded-feature-identifier-identity"
    detector_version = "0.1.0"
    entry_point = (
        "sc_referee.detectors.feature_identifier_identity:BoundedFeatureIdentifierIdentityDetector"
    )
    maturity = "experimental"
    check_ids = (
        "check:feature-identity-human-requirement",
        "check:feature-identity-material-inputs",
        "check:feature-identity-unique-axes",
        "check:feature-identity-alternate-mapping",
        "check:feature-identity-complete-comparison",
    )

    def __init__(self, manifest: Mapping[str, Any]) -> None:
        self.manifest = deepcopy(dict(manifest))
        self._validate_manifest()
        self.manifest_digest = semantic_digest(self.manifest)

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())

    def evaluate(
        self,
        locked_case: Mapping[str, Any],
        observation: Mapping[str, Any],
    ) -> dict[str, Any]:
        question = _linked_question(locked_case, observation)
        answers = _linked_answers(locked_case, question)
        work_packet = {
            "profile": "bounded_feature_identifier_identity_work_packet_v1",
            "audit_run_id": str(locked_case["audit_run_id"]),
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "detector_manifest_digest": self.manifest_digest,
            "observation": deepcopy(dict(observation)),
            "question": deepcopy(question) if question is not None else None,
            "answers": deepcopy(answers),
        }
        input_digest = semantic_digest(work_packet)
        observation_id = str(observation.get("deterministic_check_observation_id", "unknown"))
        result_id = stable_id(
            "detector-result",
            self.detector_id,
            self.detector_version,
            observation_id,
            input_digest,
        )
        target_ref = typed_ref("deterministic_check_observation", observation_id)
        base = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "detector_result",
            "result_id": result_id,
            "audit_run_id": str(locked_case["audit_run_id"]),
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "detector_manifest_digest": self.manifest_digest,
            "detector_maturity": self.maturity,
            "target_refs": [target_ref],
            "evaluated_at": str(locked_case["locked_at"]),
            "runtime_mode": "static",
            "deterministic_input_digest": input_digest,
            "provenance": {
                "actor": {"actor_kind": "detector", "actor_id": self.detector_id},
                "method": "deterministic_bounded_feature_identifier_identity_evaluation",
                "created_at": str(locked_case["locked_at"]),
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "extensions": {
                "x-evaluation-only": True,
                "x-production-finding-permitted": False,
                "x-detector-profile": "bounded_feature_identifier_identity_v1",
                "x-calculation-observation-ref": target_ref,
                "x-publication-surface-id": str(
                    observation.get("target_ref", {}).get("record_id", "surface:unknown")
                ),
            },
        }

        problem = _observation_problem(observation)
        if problem is not None:
            return self._terminal(
                base,
                state="unsupported_path",
                applicability_status="not_applicable",
                basis=problem,
                unsupported=[problem],
                premises=[],
                evidence=[],
                checks=_unavailable_checks(self.check_ids, problem),
                gaps=[problem],
            )
        if question is None:
            problem = "The exact nonconformant comparison has no uniquely linked material question."
            return self._terminal(
                base,
                state="insufficient_semantics",
                applicability_status="uncertain",
                basis=problem,
                unsupported=[],
                premises=[
                    _premise(
                        "premise:feature-identity-review-requirement",
                        "Exact identifier-set equality governs this review.",
                        "unknown",
                        True,
                        [],
                    )
                ],
                evidence=_observation_evidence(observation, target_ref),
                checks=_unavailable_checks(self.check_ids, problem),
                gaps=[problem],
            )
        if len(answers) != 1:
            problem = (
                "The material question has no exact human Answer."
                if not answers
                else "The material question has more than one active Answer."
            )
            evidence = _observation_evidence(observation, target_ref)
            return self._terminal(
                base,
                state="insufficient_semantics",
                applicability_status="uncertain",
                basis=problem,
                unsupported=[],
                premises=[
                    _premise(
                        "premise:feature-identity-review-requirement",
                        "Exact identifier-set equality governs this review.",
                        "unknown",
                        True,
                        [],
                    )
                ],
                evidence=evidence,
                checks=_unavailable_checks(self.check_ids, problem),
                gaps=[problem],
            )

        answer = answers[0]
        relationship = _answer_relationship(answer)
        answer_evidence = _answer_evidence(question, answer, observation)
        observation_evidence = _observation_evidence(observation, target_ref)
        evidence = [answer_evidence, *observation_evidence]
        if relationship == "not_required":
            return self._terminal(
                base,
                state="not_applicable",
                applicability_status="not_applicable",
                basis=(
                    "The human Answer explicitly states that exact identifier-set equality is not required for this review."
                ),
                unsupported=[],
                premises=[
                    _premise(
                        "premise:feature-identity-review-requirement",
                        "Exact identifier-set equality governs this review.",
                        "refuted",
                        True,
                        ["evidence:feature-identity-human-answer"],
                    )
                ],
                evidence=evidence,
                checks=_not_applicable_checks(self.check_ids),
                gaps=[],
            )
        if relationship == "alternate_mapping":
            problem = "The human Answer states that an alternate mapping or normalization governs; the mapping is outside this exact-identity profile."
            checks = _unavailable_checks(self.check_ids, problem)
            checks[0] = _completed_check(
                self.check_ids[0], ["evidence:feature-identity-human-answer"]
            )
            checks[3] = {
                "check_id": self.check_ids[3],
                "status": "completed",
                "outcome": "counterevidence_found",
                "evidence_ids": ["evidence:feature-identity-human-answer"],
                "notes": problem,
            }
            return self._terminal(
                base,
                state="unsupported_path",
                applicability_status="not_applicable",
                basis=problem,
                unsupported=[problem],
                premises=[
                    _premise(
                        "premise:feature-identity-review-requirement",
                        "Exact identifier-set equality governs this review.",
                        "unknown",
                        True,
                        ["evidence:feature-identity-human-answer"],
                    )
                ],
                evidence=evidence,
                checks=checks,
                gaps=[problem],
            )
        if relationship != EXACT_IDENTITY_RELATION:
            problem = "The human Answer retained the exact identity requirement as unknown."
            return self._terminal(
                base,
                state="insufficient_semantics",
                applicability_status="uncertain",
                basis=problem,
                unsupported=[],
                premises=[
                    _premise(
                        "premise:feature-identity-review-requirement",
                        "Exact identifier-set equality governs this review.",
                        "unknown",
                        True,
                        ["evidence:feature-identity-human-answer"],
                    )
                ],
                evidence=evidence,
                checks=_unavailable_checks(self.check_ids, problem),
                gaps=[problem],
            )

        operands = _operands(observation)
        required_names = {
            "left_input_path",
            "left_identifier_column",
            "right_input_path",
            "right_identifier_field",
            "comparison_relation",
            "left_identifier_count",
            "right_identifier_count",
            "overlap_count",
            "left_only_count",
            "right_only_count",
        }
        if not required_names.issubset(operands):
            problem = "The deterministic observation lacks one required typed operand."
            return self._terminal(
                base,
                state="unsupported_path",
                applicability_status="not_applicable",
                basis=problem,
                unsupported=[problem],
                premises=[],
                evidence=evidence,
                checks=_unavailable_checks(self.check_ids, problem),
                gaps=[problem],
            )
        if operands["comparison_relation"] != EXACT_IDENTITY_RELATION:
            problem = "The deterministic observation uses a comparison outside the exact identity profile."
            return self._terminal(
                base,
                state="unsupported_path",
                applicability_status="not_applicable",
                basis=problem,
                unsupported=[problem],
                premises=[],
                evidence=evidence,
                checks=_unavailable_checks(self.check_ids, problem),
                gaps=[problem],
            )

        nonconformant = observation.get("comparison", {}).get("outcome") == "nonconformant"
        premises = [
            _premise(
                "premise:feature-identity-review-requirement",
                "Exact identifier-set equality governs this review.",
                "established",
                True,
                ["evidence:feature-identity-human-answer"],
            ),
            _premise(
                "premise:left-feature-identifier-set-complete",
                "The complete unique left identifier set was parsed from the exact selected bytes.",
                "established",
                True,
                ["evidence:left-feature-identifier-set"],
            ),
            _premise(
                "premise:right-feature-identifier-set-complete",
                "The complete unique right identifier set was parsed from the exact selected bytes.",
                "established",
                True,
                ["evidence:right-feature-identifier-set"],
            ),
            _premise(
                "premise:feature-identifier-set-comparison",
                (
                    "The exact selected identifier sets differ."
                    if nonconformant
                    else "The exact selected identifier sets are equal."
                ),
                "established",
                True,
                ["evidence:complete-feature-identifier-set-comparison"],
            ),
        ]
        checks = [
            _completed_check(self.check_ids[0], ["evidence:feature-identity-human-answer"]),
            _completed_check(
                self.check_ids[1],
                ["evidence:left-feature-identifier-set", "evidence:right-feature-identifier-set"],
            ),
            _completed_check(
                self.check_ids[2],
                ["evidence:left-feature-identifier-set", "evidence:right-feature-identifier-set"],
            ),
            _completed_check(self.check_ids[3], ["evidence:feature-identity-human-answer"]),
            _completed_check(
                self.check_ids[4], ["evidence:complete-feature-identifier-set-comparison"]
            ),
        ]
        basis = "One exact human review requirement, both full-digest complete unique identifier axes, the no-normalization boundary, and the complete exact set comparison all resolve."
        if not nonconformant:
            return self._terminal(
                base,
                state="no_issue_detected_within_coverage",
                applicability_status="applicable",
                basis=basis,
                unsupported=[],
                premises=premises,
                evidence=evidence,
                checks=checks,
                gaps=[],
            )

        bounded = (
            f"The human requirement governing this review requires exact identifier-set equality "
            f"between {operands['left_input_path']} column {operands['left_identifier_column']!r} "
            f"and {operands['right_input_path']} field {operands['right_identifier_field']!r}. "
            f"The complete unique sets contain {operands['left_identifier_count']} and "
            f"{operands['right_identifier_count']} identifiers with {operands['overlap_count']} "
            f"in common; {operands['left_only_count']} occur only on the left and "
            f"{operands['right_only_count']} occur only on the right."
        )
        candidate = {
            "assessment_type": "finding",
            "title": "Selected feature identifier sets conflict with the review requirement",
            "bounded_statement": bounded,
            "material_premise_ids": [str(item["premise_id"]) for item in premises],
            "unresolved_material_premise_ids": [],
        }
        return self._terminal(
            base,
            state="evaluation_finding_candidate",
            applicability_status="applicable",
            basis=basis,
            unsupported=[],
            premises=premises,
            evidence=evidence,
            checks=checks,
            gaps=[],
            candidate=candidate,
        )

    def finding_draft(self, result: Mapping[str, Any]) -> dict[str, Any]:
        """Build the bounded draft used only by shared admission/qualification checks."""

        candidate = result.get("candidate")
        if not isinstance(candidate, Mapping):
            raise FeatureIdentifierIdentityDetectorError("detector result has no Finding candidate")
        target_ref = deepcopy(result["target_refs"][0])
        created_at = str(result["evaluated_at"])
        return {
            "schema_version": SCHEMA_VERSION,
            "record_type": "finding",
            "finding_id": stable_id("finding", str(result["result_id"])),
            "audit_run_id": str(result["audit_run_id"]),
            "grouping_key": (
                f"{self.detector_id}|{target_ref['record_id']}|feature_identifier_identity"
            ),
            "issue_class": "x-feature-identifier-identity-conflict",
            "title": str(candidate["title"]),
            "summary": str(candidate["bounded_statement"]),
            "demonstration_status": "demonstrated",
            "subject_refs": [target_ref],
            "affected_descendants": [],
            "root_cause": {
                "root_ref": target_ref,
                "violated_semantic_dimension": "data_identity",
                "explanation": (
                    "The complete selected identifier sets are unequal under the exact human equality requirement governing this review."
                ),
            },
            "evidence": deepcopy(result["evidence"]),
            "logical_basis": (
                "Human-authorized exact set equality AND complete unequal selected identifier sets entails one bounded review-scoped identity conflict."
            ),
            "severity": {
                "level": "minor",
                "rationale": (
                    "The demonstrated issue is localized to identifier identity; downstream scientific impact is not established."
                ),
            },
            "publication_materiality": {
                "state": "assessed",
                "level": "local",
                "rationale": (
                    "The evidence establishes a local selected-artifact identity conflict only."
                ),
                "publication_surface_ids": [
                    str(
                        result.get("extensions", {}).get(
                            "x-publication-surface-id", "surface:unknown"
                        )
                    )
                ],
            },
            "detector_result_ids": [str(result["result_id"])],
            "coverage_limitations": [
                "No producer lineage, direction of repair, biological meaning, numerical impact, or publication-level consequence is established."
            ],
            "next_action": (
                "Determine which identifier representation governs the selected artifacts before joining or interpreting the affected features."
            ),
            "created_at": created_at,
            "provenance": controller_provenance(
                "bounded_feature_identifier_identity_finding_draft_v1", created_at
            ),
        }

    def _terminal(
        self,
        base: dict[str, Any],
        *,
        state: str,
        applicability_status: str,
        basis: str,
        unsupported: list[str],
        premises: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        checks: list[dict[str, Any]],
        gaps: list[str],
        candidate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = deepcopy(base)
        record.update(
            {
                "state": state,
                "applicability": {
                    "status": applicability_status,
                    "basis": basis,
                    "unsupported_constructs": unsupported,
                },
                "premise_evaluations": premises,
                "evidence": evidence,
                "counterevidence_execution": checks,
                "coverage": {
                    "status": "covered" if applicability_status == "applicable" else "not_covered",
                    "basis": basis,
                    "gaps": gaps,
                },
                "unavailable_evidence": gaps,
            }
        )
        if candidate is not None:
            record["candidate"] = candidate
        return record

    def _validate_manifest(self) -> None:
        expected = {
            "record_type": "detector_manifest",
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "maturity": self.maturity,
        }
        for key, value in expected.items():
            if self.manifest.get(key) != value:
                raise FeatureIdentifierIdentityDetectorError(
                    f"feature-identity detector manifest has invalid {key}"
                )
        implementation = self.manifest.get("implementation")
        if not isinstance(implementation, Mapping):
            raise FeatureIdentifierIdentityDetectorError(
                "feature-identity detector manifest lacks implementation identity"
            )
        if implementation.get("entry_point") != self.entry_point:
            raise FeatureIdentifierIdentityDetectorError("detector manifest entry point mismatch")
        if implementation.get("deterministic") is not True:
            raise FeatureIdentifierIdentityDetectorError(
                "feature-identity detector must be deterministic"
            )
        if implementation.get("implementation_digest") != self.implementation_digest():
            raise FeatureIdentifierIdentityDetectorError(
                "feature-identity detector implementation digest mismatch"
            )
        declared_checks = tuple(
            str(item.get("check_id"))
            for item in self.manifest.get("counterevidence_protocol", [])
            if isinstance(item, Mapping)
        )
        if declared_checks != self.check_ids:
            raise FeatureIdentifierIdentityDetectorError(
                "feature-identity counterevidence protocol mismatch"
            )
        outputs = self.manifest.get("permitted_output_types")
        if not isinstance(outputs, list) or "finding" in outputs:
            raise FeatureIdentifierIdentityDetectorError(
                "experimental feature-identity detector cannot permit Findings"
            )
        extensions = self.manifest.get("extensions")
        if (
            not isinstance(extensions, Mapping)
            or extensions.get("x-production-finding-permitted") is not False
        ):
            raise FeatureIdentifierIdentityDetectorError(
                "experimental feature-identity detector must deny production Finding permission"
            )


def _observation_problem(observation: Mapping[str, Any]) -> str | None:
    check_manifest = observation.get("check_manifest")
    if (
        observation.get("record_type") != "deterministic_check_observation"
        or not isinstance(check_manifest, Mapping)
        or check_manifest.get("check_id") != FEATURE_IDENTIFIER_IDENTITY_CHECK_ID
        or observation.get("output_ceiling") != "evaluation_candidate"
        or observation.get("production_finding_permitted") is not False
        or observation.get("applicability") != "applicable"
        or observation.get("lineage_status") != "complete"
        or observation.get("comparison", {}).get("outcome") not in {"conformant", "nonconformant"}
    ):
        return "The target is outside the complete selected feature-identity observation profile."
    return None


def _linked_question(
    locked_case: Mapping[str, Any], observation: Mapping[str, Any]
) -> dict[str, Any] | None:
    observation_ref = typed_ref(
        "deterministic_check_observation",
        str(observation.get("deterministic_check_observation_id", "")),
    )
    matches = [
        item
        for item in locked_case.get("material_questions", [])
        if isinstance(item, Mapping)
        and item.get("unknown_semantic_dimension") == FEATURE_IDENTIFIER_IDENTITY_DIMENSION
        and item.get("extensions", {}).get("x-calculation-observation-ref") == observation_ref
    ]
    return deepcopy(dict(matches[0])) if len(matches) == 1 else None


def _linked_answers(
    locked_case: Mapping[str, Any], question: Mapping[str, Any] | None
) -> list[dict[str, Any]]:
    if question is None:
        return []
    question_ref = typed_ref("material_question", str(question["question_id"]))
    return [
        deepcopy(dict(item))
        for item in locked_case.get("answers", [])
        if isinstance(item, Mapping) and item.get("question_ref") == question_ref
    ]


def _answer_relationship(answer: Mapping[str, Any]) -> str:
    if answer.get("answer_kind") == "unknown":
        return "unknown"
    value = answer.get("answer_value")
    if not isinstance(value, Mapping):
        return "unknown"
    relationship = value.get("relationship")
    return str(relationship) if isinstance(relationship, str) else "unknown"


def _operands(observation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        str(item["name"]): item.get("value")
        for item in observation.get("operands", [])
        if isinstance(item, Mapping) and isinstance(item.get("name"), str)
    }


def _observation_evidence(
    observation: Mapping[str, Any], target_ref: dict[str, str]
) -> list[dict[str, Any]]:
    operands = _operands(observation)
    source_refs = [deepcopy(ref) for ref in observation.get("source_refs", [])]
    left_source = source_refs[1:2] or source_refs[:1]
    right_source = source_refs[2:3] or source_refs[:1]
    return [
        {
            "evidence_id": "evidence:left-feature-identifier-set",
            "description": "The complete unique left identifier set was parsed from the exact selected delimited bytes.",
            "support_role": "supports",
            "source_refs": left_source,
            "record_refs": [target_ref],
            "observed_value": {
                "path": operands.get("left_input_path"),
                "field": operands.get("left_identifier_column"),
                "count": operands.get("left_identifier_count"),
                "set_digest": operands.get("left_identifier_set_digest"),
            },
        },
        {
            "evidence_id": "evidence:right-feature-identifier-set",
            "description": "The complete unique right identifier set was parsed from the exact selected H5AD bytes.",
            "support_role": "supports",
            "source_refs": right_source,
            "record_refs": [target_ref],
            "observed_value": {
                "path": operands.get("right_input_path"),
                "field": operands.get("right_identifier_field"),
                "count": operands.get("right_identifier_count"),
                "set_digest": operands.get("right_identifier_set_digest"),
            },
        },
        {
            "evidence_id": "evidence:complete-feature-identifier-set-comparison",
            "description": "The complete unique sets were compared exactly without normalization or order sensitivity.",
            "support_role": "supports",
            "source_refs": source_refs,
            "record_refs": [target_ref],
            "observed_value": {
                "overlap_count": operands.get("overlap_count"),
                "left_only_count": operands.get("left_only_count"),
                "right_only_count": operands.get("right_only_count"),
                "left_only_examples": operands.get("left_only_examples"),
                "right_only_examples": operands.get("right_only_examples"),
            },
        },
    ]


def _answer_evidence(
    question: Mapping[str, Any],
    answer: Mapping[str, Any],
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    source_refs = [deepcopy(ref) for ref in observation.get("source_refs", [])]
    return {
        "evidence_id": "evidence:feature-identity-human-answer",
        "description": "The human respondent selected the exact identifier relationship governing this review.",
        "support_role": "supports",
        "source_refs": source_refs[:1],
        "record_refs": [
            typed_ref("material_question", str(question["question_id"])),
            typed_ref("answer", str(answer["answer_id"])),
        ],
        "observed_value": deepcopy(answer.get("answer_value")),
    }


def _premise(
    premise_id: str,
    statement: str,
    state: str,
    material: bool,
    evidence_ids: list[str],
) -> dict[str, Any]:
    return {
        "premise_id": premise_id,
        "statement": statement,
        "state": state,
        "material": material,
        "evidence_ids": evidence_ids,
    }


def _completed_check(check_id: str, evidence_ids: list[str]) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "completed",
        "outcome": "no_counterevidence",
        "evidence_ids": evidence_ids,
        "notes": "The exact bounded check completed without a suppressor.",
    }


def _unavailable_checks(check_ids: tuple[str, ...], reason: str) -> list[dict[str, Any]]:
    return [
        {
            "check_id": check_id,
            "status": "unavailable",
            "outcome": "inconclusive",
            "evidence_ids": [],
            "notes": reason,
        }
        for check_id in check_ids
    ]


def _not_applicable_checks(check_ids: tuple[str, ...]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": check_id,
            "status": "not_applicable",
            "outcome": "not_applicable",
            "evidence_ids": [],
            "notes": "The human Answer makes exact identifier-set equality not applicable.",
        }
        for check_id in check_ids
    ]
