from __future__ import annotations

from typing import Any

from sc_referee.core.ids import semantic_digest
from sc_referee.version import SCHEMA_VERSION, __version__


class SampleUnitDependenceQuestionDetector:
    detector_id = "detector:sample-unit-dependence"
    detector_version = "0.1.0"

    def evaluate(self, locked_case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
        observation = locked_case["repeated_identifier_observation"]
        question = locked_case["material_question"]
        operation_ref = locked_case.get(
            "dependence_operation_ref",
            {"record_type": "operation", "record_id": "operation:compute-difference"},
        )
        operation_id = operation_ref["record_id"]
        timestamp = locked_case["locked_at"]
        repeated = observation["state"] == "observed" and bool(observation["repeated_values"])
        premise_state = "unknown"
        state = "conditional_concern_candidate" if repeated else "no_issue_detected_within_coverage"
        candidate = None
        if repeated:
            candidate = {
                "assessment_type": "conditional_concern",
                "title": "Repeated identifiers may represent repeated biological units",
                "bounded_statement": "If sample_id identifies biological donors, repeated donor observations are aggregated without an explicit paired or clustered structure.",
                "material_premise_ids": [
                    "premise:repeated-sample-identifiers",
                    "premise:sample-id-is-donor",
                ],
                "unresolved_material_premise_ids": ["premise:sample-id-is-donor"],
            }
        result: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "detector_result",
            "result_id": "result:sample-unit-dependence",
            "audit_run_id": locked_case["audit_run_id"],
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "detector_manifest_digest": locked_case["dependence_detector_manifest_digest"],
            "detector_maturity": "validated",
            "target_refs": [operation_ref],
            "state": state,
            "evaluated_at": timestamp,
            "runtime_mode": "static",
            "deterministic_input_digest": semantic_digest(locked_case),
            "applicability": {
                "status": "uncertain" if repeated else "applicable",
                "basis": "Repeated sample_id values are observed, but the scientific unit represented by sample_id is unresolved."
                if repeated
                else "No repeated sample_id values were observed in the inspected table.",
                "unsupported_constructs": [],
            },
            "premise_evaluations": [
                {
                    "premise_id": "premise:repeated-sample-identifiers",
                    "statement": "The input table contains repeated sample_id values.",
                    "state": "established" if repeated else "refuted",
                    "material": True,
                    "evidence_ids": ["evidence:repeated-sample-identifiers"],
                },
                {
                    "premise_id": "premise:sample-id-is-donor",
                    "statement": "sample_id identifies biological donors.",
                    "state": premise_state,
                    "material": True,
                    "evidence_ids": [],
                },
            ],
            "evidence": [
                {
                    "evidence_id": "evidence:repeated-sample-identifiers",
                    "description": "Repeated sample_id values were observed in the input table.",
                    "support_role": "supports",
                    "source_refs": observation["source_refs"],
                    "record_refs": [
                        {"record_type": "claim", "record_id": locked_case["claim"]["claim_id"]}
                    ],
                    "observed_value": observation["repeated_values"],
                }
            ],
            "counterevidence_execution": [
                {
                    "check_id": "check:sample-unit-definition",
                    "status": "unavailable" if repeated else "not_applicable",
                    "outcome": "inconclusive" if repeated else "not_applicable",
                    "evidence_ids": [],
                },
                {
                    "check_id": "check:upstream-aggregation",
                    "status": "completed",
                    "outcome": "no_counterevidence",
                    "evidence_ids": ["evidence:repeated-sample-identifiers"],
                },
            ],
            "coverage": {
                "status": "partially_covered" if repeated else "covered",
                "basis": "Identifier repetition is observed; biological unit semantics remain unresolved."
                if repeated
                else "The repeated-unit pattern is absent in the inspected table.",
                "gaps": ["sample_id scientific meaning is unresolved"] if repeated else [],
            },
            "unavailable_evidence": ["An authoritative definition of sample_id."]
            if repeated
            else [],
            "provenance": {
                "actor": {"actor_kind": "detector", "actor_id": self.detector_id},
                "method": "deterministic_detection",
                "created_at": timestamp,
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "extensions": {"x-fixture-only-test-double": True},
        }
        if candidate is not None:
            result["candidate"] = candidate
        concern = None
        if repeated:
            concern = {
                "schema_version": SCHEMA_VERSION,
                "record_type": "conditional_concern",
                "concern_id": "concern:sample-unit-dependence",
                "audit_run_id": locked_case["audit_run_id"],
                "grouping_key": f"{self.detector_id}|{operation_id}|dependence_structure",
                "issue_class": "batch_nuisance_dependence_omission",
                "title": "If sample_id identifies donors, repeated donor observations are not modeled explicitly",
                "conditional_statement": "If sample_id identifies biological donors, repeated donor observations are aggregated without an explicit paired or clustered structure.",
                "condition": {
                    "premise_id": "premise:sample-id-is-donor",
                    "premise_state": "unknown",
                    "if_true": "sample_id identifies biological donors.",
                },
                "material_question_id": question["question_id"],
                "potential_impact": {
                    "level": "material_if_true",
                    "rationale": "The implemented row-level comparison would ignore within-donor pairing and could represent a different comparison or uncertainty structure.",
                },
                "review_priority": "high",
                "subject_refs": [operation_ref],
                "affected_descendants": [
                    {
                        "target_ref": {
                            "record_type": "claim",
                            "record_id": locked_case["claim"]["claim_id"],
                        },
                        "relationship_path": [
                            operation_ref,
                            {"record_type": "claim", "record_id": locked_case["claim"]["claim_id"]},
                        ],
                        "effect": "Interpretation of the reported comparison depends on the unresolved unit definition.",
                    }
                ],
                "evidence": result["evidence"],
                "why_material": "The unit definition could change whether a paired or clustered comparison is required.",
                "next_evidence_needed": [
                    "A data dictionary or scientist answer defining sample_id."
                ],
                "detector_result_ids": [result["result_id"]],
                "created_at": timestamp,
                "provenance": {
                    "actor": {"actor_kind": "controller", "actor_id": "sc_referee.core"},
                    "method": "deterministic_generation",
                    "created_at": timestamp,
                    "tool": "sc-referee",
                    "tool_version": __version__,
                },
                "extensions": {"x-fixture-only-test-double": True},
            }
        return result, concern
