from __future__ import annotations

import math
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.records.observed import known_semantic_value
from sc_referee.version import SCHEMA_VERSION, __version__


class BoundedDirectionDetectorError(ValueError):
    """Raised when the bound detector manifest or context is internally inconsistent."""


class BoundedReportMeanDirectionDetector:
    """Compare one explicit report direction with one exact raw mean difference."""

    detector_id = "detector:bounded-report-mean-direction"
    detector_version = "0.1.0"
    entry_point = (
        "sc_referee.detectors.bounded_report_mean_direction:BoundedReportMeanDirectionDetector"
    )
    maturity = "experimental"
    check_ids = (
        "check:literal-report-conflict",
        "check:exact-source-flow-binding",
        "check:group-orientation",
        "check:raw-value-column-binding",
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
        claim: Mapping[str, Any],
    ) -> dict[str, Any]:
        work_packet = self._work_packet(locked_case, claim)
        input_digest = semantic_digest(work_packet)
        result_id = stable_id(
            "detector-result",
            self.detector_id,
            self.detector_version,
            str(claim.get("claim_id", "unknown")),
            input_digest,
        )
        target_ref = {
            "record_type": "claim",
            "record_id": str(claim.get("claim_id", "unknown")),
        }
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
                "method": "deterministic_bounded_report_mean_direction_evaluation",
                "created_at": str(locked_case["locked_at"]),
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "extensions": {
                "x-evaluation-only": True,
                "x-production-finding-permitted": False,
                "x-detector-profile": "bounded_report_mean_direction_v1",
            },
        }

        claim_problem = _claim_problem(claim)
        if claim_problem is not None:
            return self._terminal(
                base,
                state="unsupported_path",
                applicability_status="not_applicable",
                basis=claim_problem,
                unsupported=[claim_problem],
                premises=[],
                evidence=[],
                checks=_unavailable_checks(self.check_ids, claim_problem),
                gaps=[claim_problem],
            )

        peers = _opposite_peer_claims(work_packet["claims"], claim)
        if peers:
            peer_evidence = {
                "evidence_id": "evidence:opposite-report-claim",
                "description": (
                    "The same selected publication surface contains an opposite-direction final "
                    "sentence for the same literal subject, outcome, and comparison."
                ),
                "support_role": "counterevidence",
                "source_refs": [
                    deepcopy(ref) for peer in peers for ref in peer.get("source_refs", [])
                ],
                "record_refs": [
                    {"record_type": "claim", "record_id": str(peer["claim_id"])} for peer in peers
                ],
                "observed_value": [str(peer["text"]) for peer in peers],
            }
            checks = _unavailable_checks(
                self.check_ids,
                "The decisive literal report conflict suppressed further candidate evaluation.",
            )
            checks[0] = {
                "check_id": self.check_ids[0],
                "status": "completed",
                "outcome": "counterevidence_found",
                "evidence_ids": [peer_evidence["evidence_id"]],
                "notes": "An exact opposite-direction sibling Claim was found.",
            }
            return self._terminal(
                base,
                state="insufficient_semantics",
                applicability_status="uncertain",
                basis=(
                    "The selected publication surface contains contradictory literal directions "
                    "for the same target."
                ),
                unsupported=[],
                premises=[
                    _premise(
                        "premise:unambiguous-report-direction",
                        "The selected publication surface has one unambiguous literal direction "
                        "for this target.",
                        "conflicted",
                        True,
                        [str(peer_evidence["evidence_id"])],
                    )
                ],
                evidence=[peer_evidence],
                checks=checks,
                gaps=["Opposite-direction sibling Claim on the same publication surface."],
            )

        linked = _resolve_linked_records(work_packet, claim)
        if linked["state"] != "resolved":
            state = (
                "unsupported_path" if linked["state"] == "unsupported" else "insufficient_semantics"
            )
            problem = str(linked["problem"])
            return self._terminal(
                base,
                state=state,
                applicability_status=(
                    "not_applicable" if state == "unsupported_path" else "uncertain"
                ),
                basis=problem,
                unsupported=[problem] if state == "unsupported_path" else [],
                premises=list(linked.get("premises", [])),
                evidence=list(linked.get("evidence", [])),
                checks=list(linked["checks"]),
                gaps=[problem],
            )

        result = linked["result"]
        operation = linked["operation"]
        writer = linked["writer"]
        assert isinstance(result, Mapping)
        assert isinstance(operation, Mapping)
        assert isinstance(writer, Mapping)
        scalar_value = float(result["scalar_value"])
        observed_direction = (
            "positive" if scalar_value > 0 else "negative" if scalar_value < 0 else "null"
        )
        reported_direction = str(claim["proposition"]["direction"])
        contradiction = observed_direction != reported_direction
        parameters = operation["literal_parameters"]
        left_group = str(parameters["left_group"])
        right_group = str(parameters["right_group"])
        outcome_column = str(parameters["outcome_column"])

        evidence = [
            {
                "evidence_id": "evidence:report-direction",
                "description": "The final report contains one explicit bounded directional sentence.",
                "support_role": "supports",
                "source_refs": deepcopy(claim["source_refs"]),
                "record_refs": [target_ref],
                "observed_value": reported_direction,
            },
            {
                "evidence_id": "evidence:raw-mean-difference",
                "description": (
                    "The auditor recomputed the exact supported left-group minus right-group raw "
                    "mean difference from the snapshotted input."
                ),
                "support_role": "supports",
                "source_refs": deepcopy(result["source_refs"]),
                "record_refs": [
                    {
                        "record_type": "observed_result",
                        "record_id": str(result["observed_result_id"]),
                    },
                    {"record_type": "operation", "record_id": str(operation["operation_id"])},
                ],
                "observed_value": scalar_value,
            },
            {
                "evidence_id": "evidence:static-report-result-flow",
                "description": (
                    "The supported static source graph carries the result Artifact into a writer "
                    "for the selected report path."
                ),
                "support_role": "supports",
                "source_refs": deepcopy(writer["source_refs"]),
                "record_refs": [
                    {"record_type": "operation", "record_id": str(writer["operation_id"])}
                ],
                "observed_value": "exact_static_result_artifact_flow",
            },
        ]
        premises = [
            _premise(
                "premise:explicit-report-direction",
                f"The final report sentence states a {reported_direction} direction.",
                "established",
                True,
                ["evidence:report-direction"],
            ),
            _premise(
                "premise:exact-literal-alignment",
                (
                    f"The sentence labels align exactly with raw column {outcome_column!r} and "
                    f"group order {left_group!r} minus {right_group!r}."
                ),
                "established",
                True,
                ["evidence:report-direction", "evidence:raw-mean-difference"],
            ),
            _premise(
                "premise:raw-result-direction",
                (
                    f"The auditor-recomputed {left_group!r} minus {right_group!r} raw mean "
                    f"difference is {observed_direction} ({scalar_value})."
                ),
                "established",
                True,
                ["evidence:raw-mean-difference"],
            ),
            _premise(
                "premise:static-report-result-flow",
                "The exact result Artifact flows statically into a writer for the selected report path.",
                "established",
                True,
                ["evidence:static-report-result-flow"],
            ),
        ]
        checks = [
            {
                "check_id": self.check_ids[0],
                "status": "completed",
                "outcome": "no_counterevidence",
                "evidence_ids": ["evidence:report-direction"],
                "notes": "No opposite-direction sibling Claim matched the same literal target.",
            },
            {
                "check_id": self.check_ids[1],
                "status": "completed",
                "outcome": "no_counterevidence",
                "evidence_ids": ["evidence:static-report-result-flow"],
                "notes": "One unique result and exact static report-writer flow were resolved.",
            },
            {
                "check_id": self.check_ids[2],
                "status": "completed",
                "outcome": "no_counterevidence",
                "evidence_ids": ["evidence:raw-mean-difference"],
                "notes": "Literal sentence and source operation use the same left/right group order.",
            },
            {
                "check_id": self.check_ids[3],
                "status": "completed",
                "outcome": "no_counterevidence",
                "evidence_ids": ["evidence:raw-mean-difference"],
                "notes": "Literal outcome and raw source column labels match exactly.",
            },
        ]
        basis = (
            "The exact bounded sentence, raw two-group mean difference, group order, outcome "
            "column, and static report-result flow are all resolved."
        )
        if not contradiction:
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
                extra_extensions={
                    "x-raw-mean-difference": scalar_value,
                    "x-observed-raw-direction": observed_direction,
                },
            )

        bounded = (
            f"The selected report states that {claim['proposition']['subject']} "
            f"{claim['proposition']['predicate']} relative to {right_group}, while the exact "
            f"supported source path passes a {left_group}-minus-{right_group} raw mean-difference "
            f"Artifact for column {outcome_column!r} into the selected report writer; the "
            f"auditor-recomputed value is {scalar_value} ({observed_direction})."
        )
        candidate = {
            "assessment_type": "finding",
            "title": "Report direction conflicts with the linked raw mean difference",
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
            extra_extensions={
                "x-raw-mean-difference": scalar_value,
                "x-observed-raw-direction": observed_direction,
            },
        )

    def _work_packet(
        self, locked_case: Mapping[str, Any], claim: Mapping[str, Any]
    ) -> dict[str, Any]:
        claim_id = str(claim.get("claim_id", ""))
        claims = [
            deepcopy(item)
            for item in locked_case.get("claims", [])
            if isinstance(item, Mapping)
            and (
                str(item.get("claim_id")) == claim_id
                or item.get("report_ref") == claim.get("report_ref")
            )
        ]
        return {
            "profile": "bounded_report_mean_direction_work_packet_v1",
            "audit_run_id": str(locked_case["audit_run_id"]),
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "detector_manifest_digest": self.manifest_digest,
            "target_claim_id": claim_id,
            "claims": claims,
            "observed_results": deepcopy(list(locked_case.get("observed_results", []))),
            "operations": deepcopy(list(locked_case.get("operations", []))),
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
        extra_extensions: Mapping[str, Any] | None = None,
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
                    "status": (
                        "covered" if applicability_status == "applicable" else "not_covered"
                    ),
                    "basis": basis,
                    "gaps": gaps,
                },
                "unavailable_evidence": gaps,
            }
        )
        if candidate is not None:
            record["candidate"] = candidate
        if extra_extensions:
            record["extensions"].update(deepcopy(dict(extra_extensions)))
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
                raise BoundedDirectionDetectorError(
                    f"bounded direction detector manifest has invalid {key}"
                )
        implementation = self.manifest.get("implementation")
        if not isinstance(implementation, Mapping):
            raise BoundedDirectionDetectorError("detector manifest lacks implementation identity")
        if implementation.get("entry_point") != self.entry_point:
            raise BoundedDirectionDetectorError("detector manifest entry point mismatch")
        if implementation.get("deterministic") is not True:
            raise BoundedDirectionDetectorError("detector implementation must be deterministic")
        if implementation.get("implementation_digest") != self.implementation_digest():
            raise BoundedDirectionDetectorError("detector implementation digest mismatch")
        declared_checks = tuple(
            str(item.get("check_id"))
            for item in self.manifest.get("counterevidence_protocol", [])
            if isinstance(item, Mapping)
        )
        if declared_checks != self.check_ids:
            raise BoundedDirectionDetectorError("detector counterevidence protocol mismatch")
        outputs = self.manifest.get("permitted_output_types")
        if not isinstance(outputs, list) or "finding" in outputs:
            raise BoundedDirectionDetectorError(
                "experimental detector manifest cannot permit Findings"
            )


def _claim_problem(claim: Mapping[str, Any]) -> str | None:
    proposition = claim.get("proposition")
    extraction = claim.get("extraction")
    extensions = claim.get("extensions")
    if (
        claim.get("record_type") != "claim"
        or claim.get("claim_status") != "final"
        or claim.get("claim_kind") != "directional"
        or not isinstance(proposition, Mapping)
        or proposition.get("direction") not in {"positive", "negative"}
        or not isinstance(proposition.get("subject"), str)
        or not isinstance(proposition.get("comparison"), str)
        or not isinstance(extraction, Mapping)
        or extraction.get("method") != "deterministic"
        or extraction.get("explicit_source_meaning") is not True
        or extraction.get("independently_verified") is not True
        or not isinstance(extensions, Mapping)
        or not isinstance(extensions.get("x-literal-object"), str)
    ):
        return "The target is outside the exact independently verified directional-Claim grammar."
    return None


def _opposite_peer_claims(
    claims: list[dict[str, Any]], target: Mapping[str, Any]
) -> list[dict[str, Any]]:
    target_key = _literal_claim_key(target)
    target_direction = target.get("proposition", {}).get("direction")
    return sorted(
        [
            claim
            for claim in claims
            if claim.get("claim_id") != target.get("claim_id")
            and _literal_claim_key(claim) == target_key
            and claim.get("proposition", {}).get("direction") in {"positive", "negative"}
            and claim.get("proposition", {}).get("direction") != target_direction
        ],
        key=lambda item: str(item.get("claim_id")),
    )


def _literal_claim_key(claim: Mapping[str, Any]) -> tuple[str, str, str] | None:
    proposition = claim.get("proposition")
    extensions = claim.get("extensions")
    if not isinstance(proposition, Mapping) or not isinstance(extensions, Mapping):
        return None
    values = (
        proposition.get("subject"),
        extensions.get("x-literal-object"),
        proposition.get("comparison"),
    )
    if not all(isinstance(value, str) for value in values):
        return None
    return tuple(_normalized(str(value)) for value in values)  # type: ignore[return-value]


def _resolve_linked_records(
    work_packet: Mapping[str, Any], claim: Mapping[str, Any]
) -> dict[str, Any]:
    result_refs = claim.get("lineage", {}).get("result_refs", [])
    if not isinstance(result_refs, list) or len(result_refs) != 1:
        return _unresolved_link(
            "The Claim lacks one unique exact ObservedResult binding.",
            check_index=1,
        )
    result_id = result_refs[0].get("record_id") if isinstance(result_refs[0], Mapping) else None
    results = [
        item
        for item in work_packet["observed_results"]
        if item.get("observed_result_id") == result_id
    ]
    if len(results) != 1:
        return _unresolved_link(
            "The Claim's ObservedResult reference does not resolve uniquely.",
            check_index=1,
        )
    result = results[0]
    if result.get("value_kind") != "scalar" or not isinstance(
        result.get("scalar_value"), (int, float)
    ):
        return _unresolved_link(
            "The linked result is outside the finite scalar profile.",
            check_index=1,
            unsupported=True,
        )
    if not math.isfinite(float(result["scalar_value"])):
        return _unresolved_link("The linked scalar is not finite.", check_index=1, unsupported=True)
    if (
        result.get("observation_method") != "deterministic_verification"
        or result.get("lineage_status") != "complete"
    ):
        return _unresolved_link(
            "The linked scalar lacks complete auditor-owned deterministic verification.",
            check_index=1,
        )

    operation_id = result.get("producing_operation_ref", {}).get("record_id")
    operations = [
        item for item in work_packet["operations"] if item.get("operation_id") == operation_id
    ]
    if len(operations) != 1:
        return _unresolved_link(
            "The linked result lacks one exact producing Operation.",
            check_index=1,
        )
    operation = operations[0]
    parameters = operation.get("literal_parameters")
    if (
        operation.get("kind") != "estimate"
        or operation.get("inspection_status") != "supported"
        or not isinstance(parameters, Mapping)
        or not all(
            isinstance(parameters.get(key), str)
            for key in ("outcome_column", "left_group", "right_group")
        )
    ):
        return _unresolved_link(
            "The producing Operation is outside the exact raw two-group mean-difference profile.",
            check_index=3,
            unsupported=True,
        )
    if claim.get("extensions", {}).get("x-static-report-result-artifact-flow-linked") is not True:
        return _unresolved_link(
            "Exact static result-Artifact flow into the selected report writer is unavailable.",
            check_index=1,
        )

    result_artifact = result.get("artifact_ref")
    writer_ids = {
        str(ref.get("record_id"))
        for ref in claim.get("lineage", {}).get("operation_refs", [])
        if isinstance(ref, Mapping) and ref.get("record_type") == "operation"
    }
    writers = [
        item
        for item in work_packet["operations"]
        if str(item.get("operation_id")) in writer_ids
        and item.get("kind") == "write"
        and result_artifact in item.get("input_refs", [])
    ]
    if len(writers) != 1:
        return _unresolved_link(
            "The selected report path lacks one exact result-consuming writer Operation.",
            check_index=1,
        )

    proposition = claim["proposition"]
    comparison = str(proposition["comparison"]).split(" versus ")
    result_comparison = known_semantic_value(result.get("comparison"))
    expected = f"{parameters['left_group']} versus {parameters['right_group']}"
    if (
        len(comparison) != 2
        or _normalized(comparison[0]) != _normalized(str(parameters["left_group"]))
        or _normalized(comparison[1]) != _normalized(str(parameters["right_group"]))
        or result_comparison is None
        or _normalized(result_comparison) != _normalized(expected)
    ):
        return _unresolved_link(
            "Literal group order and verified raw mean-difference order do not agree exactly.",
            check_index=2,
        )
    literal_object = str(claim["extensions"]["x-literal-object"])
    if _normalized(literal_object) != _normalized(str(parameters["outcome_column"])):
        return _unresolved_link(
            "Literal outcome label and raw value-column label do not agree exactly.",
            check_index=3,
        )

    return {
        "state": "resolved",
        "result": result,
        "operation": operation,
        "writer": writers[0],
    }


def _unresolved_link(
    problem: str, *, check_index: int, unsupported: bool = False
) -> dict[str, Any]:
    checks = _unavailable_checks(BoundedReportMeanDirectionDetector.check_ids, problem)
    checks[0] = {
        "check_id": BoundedReportMeanDirectionDetector.check_ids[0],
        "status": "completed",
        "outcome": "no_counterevidence",
        "evidence_ids": [],
        "notes": "No opposite-direction sibling Claim was present in the bounded target set.",
    }
    checks[check_index] = {
        "check_id": BoundedReportMeanDirectionDetector.check_ids[check_index],
        "status": "unavailable",
        "outcome": "inconclusive",
        "evidence_ids": [],
        "notes": problem,
    }
    return {
        "state": "unsupported" if unsupported else "unresolved",
        "problem": problem,
        "premises": [
            _premise(
                "premise:exact-applicability",
                "All exact bounded detector applicability records resolve.",
                "unknown",
                True,
                [],
            )
        ],
        "evidence": [],
        "checks": checks,
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


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())
