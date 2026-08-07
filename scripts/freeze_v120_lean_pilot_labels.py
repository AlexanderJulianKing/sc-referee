from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from sc_referee_evaluation.capture import load_review_capture

from sc_referee.core.ids import semantic_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_v120_lean_pilot_authoring import V120_AUTHORING_RELATIVE
from scripts.build_v120_lean_review import V120_REVIEW_RELATIVE
from scripts.run_record_v120_lean_review import (
    PROTOCOL_DIGEST as REVIEW_PROTOCOL_DIGEST,
)
from scripts.run_record_v120_lean_review import (
    _protocol as _review_protocol,
)
from scripts.run_v120_lean_pilot_authors import PROTOCOL_DIGEST as AUTHORING_PROTOCOL_DIGEST

V120_LABELS_RELATIVE = V120_REVIEW_RELATIVE.parent / "pilot-v120-lean-labels-three-case"
ADR_0066 = "ADR-0066-CROSS-MODEL-SINGLE-PROVIDER-REVIEW-PANEL.md"
ADR_0067 = "ADR-0067-LEAN-SINGLE-REVIEW-QUALIFICATION-PROTOCOL.md"
AUTHORING_LEDGER_DIGEST = "sha256:c6c2b109248982bad35efa80492f5e82f75a7bfbc3c937d5675e3bc346366b04"
REVIEW_LEDGER_DIGEST = "sha256:c6eac99004758201453c03e1dd752e416cfd66e1f152ef6c0da159f10ea42fbc"
CANONICAL_ISSUE_CLASS = "issue-class:retained-subset-for-complete-domain"
FROZEN_AT = "2026-08-07T21:39:10Z"
EXPECTED_VERDICT_BY_ROLE = {
    "error_bearing": "demonstrated_issue",
    "corrected_twin": "no_demonstrated_issue_within_scope",
    "valid_alternative": "no_demonstrated_issue_within_scope",
}
LABEL_STATUS_BY_ROLE = {
    "error_bearing": "positive_demonstrated",
    "corrected_twin": "verified_good_eligible",
    "valid_alternative": "verified_good_eligible",
}
LEAN_DISCLOSURE = (
    "This label was established under ADR-0067 by one calibrated blind reviewer "
    "(Anthropic:Claude Fable 5) with escalation reserved for non-clean results, and under "
    "ADR-0066 without cross-provider review; it is not represented as human expert review, "
    "as cross-provider review, or as a redundant-panel adjudication."
)


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def freeze_v120_lean_pilot_labels(project_root: Path) -> dict[str, Any]:
    output_root = project_root / V120_LABELS_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"V120 label output already exists: {output_root}")
    schema_root = project_root / "reference/schemas-v0.18.0"

    authoring = _load(project_root / V120_AUTHORING_RELATIVE / "PILOT_AUTHORING_PROTOCOL.json")
    _replay(
        authoring,
        "protocol_digest",
        cast(str, AUTHORING_PROTOCOL_DIGEST),
        "The v120 authoring protocol",
    )
    authoring_ledger = _load(project_root / V120_AUTHORING_RELATIVE / "AUTHORING_LEDGER.json")
    _replay(
        authoring_ledger,
        "ledger_digest",
        AUTHORING_LEDGER_DIGEST,
        "The v120 authoring ledger",
    )
    review_protocol = _review_protocol(project_root)
    review_root = project_root / V120_REVIEW_RELATIVE
    review_ledger = _load(review_root / "review-call-ledger.json")
    _replay(review_ledger, "ledger_digest", REVIEW_LEDGER_DIGEST, "The v120 review ledger")
    if review_ledger["protocol_digest"] != REVIEW_PROTOCOL_DIGEST:
        raise ValueError("The v120 review ledger is outside the frozen review protocol.")

    roles = {
        str(case_id): str(role) for case_id, role in authoring["case_role_assignments"].items()
    }
    if sorted(roles) != sorted(str(e["case_id"]) for e in review_ledger["entries"]):
        raise ValueError("The v120 review ledger does not cover the exact authored cases.")

    unblinding_rows: list[dict[str, Any]] = []
    label_rows: list[dict[str, Any]] = []
    reviews: dict[str, dict[str, Any]] = {}
    for entry in review_ledger["entries"]:
        case_id = str(entry["case_id"])
        review, _packet, _manifest = load_review_capture(
            review_root / str(entry["relative_capture_path"]), schema_root
        )
        if semantic_digest(review) != entry["review_digest"]:
            raise ValueError(f"The v120 review drifted for {case_id}.")
        reviews[case_id] = review
        role = roles[case_id]
        expected_verdict = EXPECTED_VERDICT_BY_ROLE[role]
        verdict = str(review["verdict"])
        issue_class_clean = (
            review.get("issue_class") == CANONICAL_ISSUE_CLASS
            if verdict == "demonstrated_issue"
            else review.get("issue_class") is None
        )
        clean = (
            verdict == expected_verdict
            and issue_class_clean
            and not review.get("unresolved_material_questions")
        )
        unblinding_rows.append(
            {
                "case_id": case_id,
                "case_role": role,
                "expected_verdict": expected_verdict,
                "observed_verdict": verdict,
                "observed_issue_class": review.get("issue_class"),
                "unresolved_material_question_count": len(
                    review.get("unresolved_material_questions") or []
                ),
                "clean": clean,
            }
        )
        if not clean:
            continue
        slug = case_id.removeprefix("case:")
        declaration = _load(
            project_root / V120_AUTHORING_RELATIVE / "author-declarations" / f"{slug}.json"
        )
        validation = _load(
            project_root / V120_AUTHORING_RELATIVE / "selected-result-validations" / f"{slug}.json"
        )
        label_rows.append(
            {
                "case_id": case_id,
                "case_role": role,
                "label_status": LABEL_STATUS_BY_ROLE[role],
                "issue_class": (CANONICAL_ISSUE_CLASS if role == "error_bearing" else None),
                "review_basis": "single_calibrated_blind_review_adr_0067",
                "review_id": str(review["review_id"]),
                "review_digest": str(entry["review_digest"]),
                "packet_digest": str(entry["packet_digest"]),
                "reviewer_model_family": "Anthropic:Claude Fable 5",
                "answer_side_evidence_refs": [
                    {
                        "record_type": "author_selected_result_declaration",
                        "record_id": str(declaration["declaration_digest"]),
                    },
                    {
                        "record_type": "selected_result_validation",
                        "record_id": str(validation["validation_digest"]),
                    },
                ],
                "agent_only_disclosure": LEAN_DISCLOSURE,
            }
        )

    escalation_required = any(not row["clean"] for row in unblinding_rows)
    if escalation_required:
        raise ValueError(
            "A v120 review is non-clean after unblinding; freeze the escalation review "
            "before creating labels."
        )
    if len(label_rows) != 3:
        raise ValueError("The v120 label freeze requires exactly three clean cases.")

    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_v120_lean_scientific_label_ledger",
        "ledger_version": "1.0.0",
        "adr_references": [ADR_0066, ADR_0067],
        "authoring_protocol_digest": AUTHORING_PROTOCOL_DIGEST,
        "authoring_ledger_digest": AUTHORING_LEDGER_DIGEST,
        "review_protocol_digest": review_protocol["protocol_digest"],
        "review_ledger_digest": REVIEW_LEDGER_DIGEST,
        "canonical_issue_class_scope": CANONICAL_ISSUE_CLASS,
        "unblinding_record": sorted(unblinding_rows, key=lambda row: str(row["case_id"])),
        "escalation_triggered": False,
        "escalation_review_refs": [],
        "entries": sorted(label_rows, key=lambda row: str(row["case_id"])),
        "label_count": len(label_rows),
        "eligible_label_count": len(label_rows),
        "detector_output_observed": False,
        "scientific_label_count": len(label_rows),
        "detector_outcome_count": 0,
        "frozen_at": FROZEN_AT,
        "qualification_authority": "none_scientific_labels_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    output_root.mkdir(parents=True)
    write_normalized_json_once(output_root / "SCIENTIFIC_LABEL_LEDGER.json", ledger)
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    ledger = freeze_v120_lean_pilot_labels(arguments.project_root.resolve())
    print(ledger["ledger_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
