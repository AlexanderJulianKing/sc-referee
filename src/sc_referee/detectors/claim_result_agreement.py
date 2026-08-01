from __future__ import annotations

from copy import deepcopy
from typing import Any

from sc_referee.core.ids import semantic_digest
from sc_referee.records.observed import known_semantic_value
from sc_referee.version import SCHEMA_VERSION, __version__

from .base import DetectionOutput
from .counterevidence import execute_counterevidence_protocol


class ClaimResultDirectionDetector:
    detector_id = "detector:claim-result-direction"
    detector_version = "0.1.0"
    fixture_id = "fixture:walking-skeleton-direction"
    counterevidence_check_ids = (
        "check:orientation",
        "check:scale",
        "check:report-qualification",
        "check:lineage-target",
    )
    non_inferences = (
        "This finding does not establish that the biological conclusion is false.",
        "This finding does not estimate the effect of correcting the report.",
    )

    def evaluate(self, locked_case: dict[str, Any]) -> DetectionOutput:
        claim = locked_case["claim"]
        result = locked_case["observed_result"]
        claim_direction = claim["proposition"].get("direction")
        claim_scale = claim["proposition"].get("scale")
        orientation = known_semantic_value(result.get("orientation"))
        result_scale = known_semantic_value(result.get("scale"))
        claim_comparison = claim["proposition"].get("comparison")
        result_comparison = known_semantic_value(result.get("comparison"))

        if orientation is None:
            result_record = self._result_record(
                locked_case,
                state="insufficient_semantics",
                applicability_status="uncertain",
                applicability_basis="Comparison orientation is unknown and could reverse the conclusion.",
                premises=[
                    self._premise(
                        "premise:reported-direction",
                        "The report states a direction.",
                        "established",
                        True,
                        ["evidence:report-text"],
                    ),
                    self._premise(
                        "premise:result-direction",
                        "The result direction under the report comparison is established.",
                        "unknown",
                        True,
                        [],
                    ),
                    self._premise(
                        "premise:scale-established",
                        "The claim and result scale are the same and established.",
                        "established" if claim_scale == result_scale else "conflicted",
                        True,
                        ["evidence:report-text", "evidence:result-sign"],
                    ),
                ],
                candidate=None,
            )
            question = deepcopy(locked_case["orientation_question"])
            return DetectionOutput(result_record, None, question)

        if (
            not isinstance(claim_scale, str)
            or not isinstance(result_scale, str)
            or claim_scale != result_scale
        ):
            premises = [
                self._premise(
                    "premise:reported-direction",
                    "The report states a direction.",
                    "established",
                    True,
                    ["evidence:report-text"],
                ),
                self._premise(
                    "premise:scale-established",
                    "The claim and linked result use the same established scale.",
                    "conflicted" if claim_scale and result_scale else "unknown",
                    True,
                    ["evidence:report-text", "evidence:result-sign"],
                ),
            ]
            result_record = self._result_record(
                locked_case,
                state="insufficient_semantics",
                applicability_status="uncertain",
                applicability_basis="Claim and result scale are not established as identical.",
                premises=premises,
                candidate=None,
            )
            return DetectionOutput(result_record, None, None)

        if (
            not isinstance(claim_comparison, str)
            or not isinstance(result_comparison, str)
            or _normalized_comparison(claim_comparison) != _normalized_comparison(result_comparison)
        ):
            premises = [
                self._premise(
                    "premise:reported-direction",
                    "The report states a direction.",
                    "established",
                    True,
                    ["evidence:report-text"],
                ),
                self._premise(
                    "premise:comparison-established",
                    "The report claim and linked result identify the same comparison.",
                    "conflicted"
                    if isinstance(claim_comparison, str) and isinstance(result_comparison, str)
                    else "unknown",
                    True,
                    ["evidence:report-text", "evidence:orientation"],
                ),
            ]
            result_record = self._result_record(
                locked_case,
                state="insufficient_semantics",
                applicability_status="uncertain",
                applicability_basis=(
                    "Claim and result comparison labels are not established as identical."
                ),
                premises=premises,
                candidate=None,
            )
            return DetectionOutput(result_record, None, None)

        normalized_value = (
            result["scalar_value"]
            if orientation == "treated_minus_control"
            else -result["scalar_value"]
        )
        normalized_direction = (
            "positive" if normalized_value > 0 else "negative" if normalized_value < 0 else "null"
        )
        contradiction = (
            claim_direction in {"positive", "negative"} and normalized_direction != claim_direction
        )
        premises = [
            self._premise(
                "premise:reported-direction",
                f"The report states a {claim_direction} direction.",
                "established",
                True,
                ["evidence:report-text"],
            ),
            self._premise(
                "premise:normalized-result-direction",
                f"The normalized result direction is {normalized_direction}.",
                "established",
                True,
                ["evidence:result-sign"],
            ),
            self._premise(
                "premise:orientation-established",
                f"The stored result uses {orientation} orientation.",
                "established",
                True,
                ["evidence:orientation"],
            ),
            self._premise(
                "premise:comparison-established",
                "The report claim and linked result identify the same comparison.",
                "established",
                True,
                ["evidence:report-text", "evidence:orientation"],
            ),
            self._premise(
                "premise:scale-established",
                f"The claim and result both use {result_scale}.",
                "established",
                True,
                ["evidence:report-text", "evidence:result-sign"],
            ),
        ]
        if not contradiction:
            result_record = self._result_record(
                locked_case,
                state="no_issue_detected_within_coverage",
                applicability_status="applicable",
                applicability_basis="Claim direction, scalar result, scale, and orientation are established.",
                premises=premises,
                candidate=None,
                normalized_value=normalized_value,
            )
            return DetectionOutput(result_record, None, None)

        bounded = (
            f"The report describes the linked treated-versus-control result as {claim_direction}, "
            f"while the normalized linked result is {normalized_direction} under the established orientation."
        )
        candidate = {
            "assessment_type": "finding",
            "title": "Reported direction disagrees with linked result",
            "bounded_statement": bounded,
            "material_premise_ids": [item["premise_id"] for item in premises],
            "unresolved_material_premise_ids": [],
        }
        result_record = self._result_record(
            locked_case,
            state="finding_candidate",
            applicability_status="applicable",
            applicability_basis="Claim direction, scalar result, scale, and orientation are established.",
            premises=premises,
            candidate=candidate,
            normalized_value=normalized_value,
        )
        finding_draft = self._finding_draft(
            locked_case, result_record, bounded, normalized_direction
        )
        return DetectionOutput(result_record, finding_draft, None)

    def _result_record(
        self,
        locked_case: dict[str, Any],
        *,
        state: str,
        applicability_status: str,
        applicability_basis: str,
        premises: list[dict[str, Any]],
        candidate: dict[str, Any] | None,
        normalized_value: float | None = None,
    ) -> dict[str, Any]:
        claim = locked_case["claim"]
        result = locked_case["observed_result"]
        timestamp = locked_case["locked_at"]
        evidence = [
            {
                "evidence_id": "evidence:report-text",
                "description": "The final report states an explicit direction.",
                "support_role": "supports",
                "source_refs": claim["source_refs"],
                "record_refs": [{"record_type": "claim", "record_id": claim["claim_id"]}],
                "observed_value": claim["proposition"].get("direction"),
            },
            {
                "evidence_id": "evidence:result-sign",
                "description": "The linked scalar result was read from the locked observed-result record.",
                "support_role": "supports",
                "source_refs": result["source_refs"],
                "record_refs": [{"record_type": "claim", "record_id": claim["claim_id"]}],
                "observed_value": result["scalar_value"],
            },
            {
                "evidence_id": "evidence:orientation",
                "description": "The comparison orientation used to normalize the scalar result.",
                "support_role": "supports",
                "source_refs": result["source_refs"],
                "record_refs": [{"record_type": "claim", "record_id": claim["claim_id"]}],
                "observed_value": known_semantic_value(result["orientation"]),
            },
        ]
        coverage_status = "covered" if applicability_status == "applicable" else "not_covered"
        record: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "detector_result",
            "result_id": "result:claim-result-direction",
            "audit_run_id": locked_case["audit_run_id"],
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "detector_manifest_digest": locked_case["detector_manifest_digest"],
            "detector_maturity": "validated",
            "target_refs": [{"record_type": "claim", "record_id": claim["claim_id"]}],
            "state": state,
            "evaluated_at": timestamp,
            "runtime_mode": "static",
            "deterministic_input_digest": semantic_digest(locked_case),
            "applicability": {
                "status": applicability_status,
                "basis": applicability_basis,
                "unsupported_constructs": [],
            },
            "premise_evaluations": premises,
            "evidence": evidence,
            "counterevidence_execution": execute_counterevidence_protocol(locked_case),
            "coverage": {
                "status": coverage_status,
                "basis": applicability_basis,
                "gaps": []
                if coverage_status == "covered"
                else ["comparison orientation unresolved"],
            },
            "unavailable_evidence": [],
            "provenance": {
                "actor": {"actor_kind": "detector", "actor_id": self.detector_id},
                "method": "deterministic_detection",
                "created_at": timestamp,
                "tool": "sc-referee",
                "tool_version": __version__,
            },
        }
        if candidate is not None:
            record["candidate"] = candidate
        if normalized_value is not None:
            record["extensions"] = {
                "x-normalized-result-value": normalized_value,
                "x-fixture-only-test-double": True,
            }
        return record

    @staticmethod
    def _premise(
        premise_id: str, statement: str, state: str, material: bool, evidence_ids: list[str]
    ) -> dict[str, Any]:
        return {
            "premise_id": premise_id,
            "statement": statement,
            "state": state,
            "material": material,
            "evidence_ids": evidence_ids,
        }

    def _finding_draft(
        self,
        locked_case: dict[str, Any],
        result_record: dict[str, Any],
        bounded: str,
        normalized_direction: str,
    ) -> dict[str, Any]:
        claim = locked_case["claim"]
        timestamp = locked_case["locked_at"]
        return {
            "schema_version": SCHEMA_VERSION,
            "record_type": "finding",
            "finding_id": "finding:claim-result-direction",
            "audit_run_id": locked_case["audit_run_id"],
            "grouping_key": f"{self.detector_id}|{claim['claim_id']}|scale_and_orientation",
            "issue_class": "claim_result_disagreement",
            "title": "Reported direction disagrees with linked result",
            "summary": bounded,
            "demonstration_status": "demonstrated",
            "severity": {
                "level": "major",
                "rationale": "The direction of one final reported effect disagrees with its linked result.",
            },
            "publication_materiality": {
                "state": "assessed",
                "level": "claim_material",
                "rationale": "The issue directly affects one explicitly selected report claim.",
                "publication_surface_ids": ["surface:walking-skeleton-report"],
            },
            "root_cause": {
                "root_ref": {"record_type": "claim", "record_id": claim["claim_id"]},
                "violated_semantic_dimension": "scale_and_orientation",
                "explanation": f"The report direction and normalized result direction ({normalized_direction}) disagree.",
            },
            "subject_refs": [{"record_type": "claim", "record_id": claim["claim_id"]}],
            "affected_descendants": [
                {
                    "target_ref": {"record_type": "claim", "record_id": claim["claim_id"]},
                    "relationship_path": [{"record_type": "claim", "record_id": claim["claim_id"]}],
                    "effect": "The final directional claim requires correction or relinking.",
                }
            ],
            "evidence": result_record["evidence"],
            "logical_basis": "Explicit report direction AND established normalized result direction under the same comparison and scale are opposite.",
            "detector_result_ids": [result_record["result_id"]],
            "coverage_limitations": [
                "This is a synthetic fixture-only test double, not a publicly qualified detector.",
                "The detector does not assess biological plausibility or whether another analysis result was intended.",
            ],
            "next_action": "Correct the claim wording or link it to the intended result.",
            "created_at": timestamp,
            "provenance": {
                "actor": {"actor_kind": "controller", "actor_id": "sc_referee.core"},
                "method": "deterministic_generation",
                "created_at": timestamp,
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "extensions": {
                "x-fixture-only-test-double": True,
                "x-fixture-id": locked_case.get("fixture_id"),
            },
        }


def _normalized_comparison(value: str) -> str:
    return " ".join(value.casefold().split())
