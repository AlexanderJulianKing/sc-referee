from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from sc_referee.records.observed import known_semantic_value

CheckStatus = Literal["completed", "not_applicable", "unavailable", "error"]
CheckOutcome = Literal[
    "no_counterevidence", "counterevidence_found", "inconclusive", "not_applicable"
]


@dataclass(frozen=True)
class CounterevidenceOutcome:
    check_id: str
    status: CheckStatus
    outcome: CheckOutcome
    evidence_ids: tuple[str, ...]
    notes: str | None = None

    def to_record(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "check_id": self.check_id,
            "status": self.status,
            "outcome": self.outcome,
            "evidence_ids": list(self.evidence_ids),
        }
        if self.notes is not None:
            record["notes"] = self.notes
        return record


def check_orientation(locked_case: dict[str, Any]) -> CounterevidenceOutcome:
    orientation = known_semantic_value(locked_case["observed_result"].get("orientation"))
    claim_comparison = locked_case["claim"].get("proposition", {}).get("comparison")
    result_comparison = known_semantic_value(locked_case["observed_result"].get("comparison"))
    if orientation not in {"treated_minus_control", "control_minus_treated"}:
        return CounterevidenceOutcome(
            "check:orientation",
            "unavailable",
            "inconclusive",
            ("evidence:orientation",),
            "Comparison orientation is not established.",
        )
    if not isinstance(claim_comparison, str) or not isinstance(result_comparison, str):
        return CounterevidenceOutcome(
            "check:orientation",
            "unavailable",
            "inconclusive",
            ("evidence:orientation", "evidence:report-text"),
            "Claim and result comparison labels are not both established.",
        )
    if _normalized_comparison(claim_comparison) != _normalized_comparison(result_comparison):
        return CounterevidenceOutcome(
            "check:orientation",
            "completed",
            "counterevidence_found",
            ("evidence:orientation", "evidence:report-text"),
            "The claim and result identify different comparisons.",
        )
    return CounterevidenceOutcome(
        "check:orientation",
        "completed",
        "no_counterevidence",
        ("evidence:orientation",),
        "The stored orientation was incorporated into deterministic normalization.",
    )


def _normalized_comparison(value: str) -> str:
    return " ".join(value.casefold().split())


def check_scale(locked_case: dict[str, Any]) -> CounterevidenceOutcome:
    claim_scale = locked_case["claim"]["proposition"].get("scale")
    result_scale = known_semantic_value(locked_case["observed_result"].get("scale"))
    if not isinstance(claim_scale, str) or not isinstance(result_scale, str):
        return CounterevidenceOutcome(
            "check:scale",
            "unavailable",
            "inconclusive",
            ("evidence:report-text", "evidence:result-sign"),
            "Claim and result scale are not both established.",
        )
    if claim_scale != result_scale:
        return CounterevidenceOutcome(
            "check:scale",
            "completed",
            "counterevidence_found",
            ("evidence:report-text", "evidence:result-sign"),
            "The claim and result use different recorded scales.",
        )
    return CounterevidenceOutcome(
        "check:scale",
        "completed",
        "no_counterevidence",
        ("evidence:report-text", "evidence:result-sign"),
    )


def check_report_qualification(locked_case: dict[str, Any]) -> CounterevidenceOutcome:
    claim = locked_case["claim"]
    extraction = claim.get("extraction", {})
    if (
        extraction.get("explicit_source_meaning") is not True
        or extraction.get("independently_verified") is not True
        or not claim.get("source_refs")
    ):
        return CounterevidenceOutcome(
            "check:report-qualification",
            "unavailable",
            "inconclusive",
            ("evidence:report-text",),
            "The explicit report proposition lacks independent source verification.",
        )
    return CounterevidenceOutcome(
        "check:report-qualification",
        "completed",
        "no_counterevidence",
        ("evidence:report-text",),
    )


def check_lineage_target(locked_case: dict[str, Any]) -> CounterevidenceOutcome:
    claim_lineage = locked_case["claim"].get("lineage", {})
    grades = claim_lineage.get("grades", {})
    result = locked_case["observed_result"]
    if (
        result.get("lineage_status") != "complete"
        or not claim_lineage.get("result_refs")
        or grades.get("result_origin", {}).get("status") not in {"complete", "partial"}
        or grades.get("computational_origin", {}).get("status") != "complete"
        or grades.get("input_origin", {}).get("status") != "complete"
    ):
        return CounterevidenceOutcome(
            "check:lineage-target",
            "unavailable",
            "inconclusive",
            ("evidence:result-sign",),
            "The exact result, computation, and input lineage needed for this detector is incomplete.",
        )
    return CounterevidenceOutcome(
        "check:lineage-target",
        "completed",
        "no_counterevidence",
        ("evidence:result-sign",),
    )


COUNTEREVIDENCE_CHECKS: tuple[Callable[[dict[str, Any]], CounterevidenceOutcome], ...] = (
    check_orientation,
    check_scale,
    check_report_qualification,
    check_lineage_target,
)


def execute_counterevidence_protocol(locked_case: dict[str, Any]) -> list[dict[str, Any]]:
    return [check(locked_case).to_record() for check in COUNTEREVIDENCE_CHECKS]
