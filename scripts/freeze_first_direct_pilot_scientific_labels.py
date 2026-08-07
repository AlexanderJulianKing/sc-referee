from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from sc_referee_evaluation.capture import load_review_capture
from sc_referee_evaluation.review_protocol_cross_model import (
    build_adjudicated_root_cause_cross_model,
    freeze_scientific_label_cross_model,
)
from sc_referee_evaluation.validation import _validate_eligible_panel

from sc_referee.core.ids import semantic_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage2_cross_model_protocol import (
    AUTHORING_RELATIVE,
    STAGE2_REVIEW_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_protocol import (
    CANONICAL_ISSUE_CLASS,
    CASE_IDS,
    LANE_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol import (
    REVIEW_RELATIVE as STAGE1_REVIEW_RELATIVE,
)

LABELS_RELATIVE = LANE_RELATIVE / "pilot-scientific-labels-three-case"
ADR_REFERENCE = "ADR-0066-CROSS-MODEL-SINGLE-PROVIDER-REVIEW-PANEL.md"
PANEL_LEDGER_DIGEST = "sha256:b5a8a566bb8c4430d087e13833cab113639b3418788c65983fb91ad5a8e7d3c9"
STAGE2_PROTOCOL_DIGEST = "sha256:49ff4ccff416b1d2794b497953b22eded3bed69a81f0e2d3c2637db0e221639c"
# The intended case roles from the frozen pilot-scope amendment become label
# statuses only now, after all eighteen reviews independently support them.
LABEL_STATUS_BY_CASE = {
    "case:35069763f06891dba5a3": "positive_demonstrated",
    "case:2e26bf5ece15be03717f": "verified_good_eligible",
    "case:b036fd64c647dfd93e35": "verified_good_eligible",
}
ADJUDICATED_AT = "2026-08-07T20:06:00Z"
FROZEN_AT = "2026-08-07T20:06:01Z"
AGENT_ONLY_DISCLOSURE = (
    "This label was established by a pinned agent-only panel of six calibrated reviewer "
    "configurations from one provider (Anthropic) across two model families (Claude Opus 5 "
    "and Claude Fable 5) under ADR-0066; it is not represented as human expert review or as "
    "cross-provider review."
)
STRONGER_CLAIMS_EXCLUDED = [
    "This label asserts only the in-scope retained-subset-for-complete-domain conflict in the "
    "selected report; no claim about intent, other error classes, or the numerically correct "
    "complete-domain value is adjudicated."
]


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def _stage1_inputs(
    project_root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    root = project_root / STAGE1_REVIEW_RELATIVE
    panel = _load(root / "STAGE1_PANEL_LEDGER.json")
    _replay(panel, "ledger_digest", PANEL_LEDGER_DIGEST, "The Stage-1 panel ledger")
    freezes: dict[str, dict[str, Any]] = {}
    for entry in panel["case_panels"]:
        case_id = str(entry["case_id"])
        frozen = _load(root / str(entry["freeze_relative_path"]))
        supplied = dict(frozen)
        digest = supplied.pop("freeze_digest", None)
        if digest != entry["freeze_digest"] or digest != semantic_digest(supplied):
            raise ValueError(f"The Stage-1 freeze for {case_id} does not replay.")
        freezes[case_id] = frozen
    reviews: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in CASE_IDS}
    for ledger_ref in panel["call_ledgers"]:
        participant_id = str(ledger_ref["participant_id"])
        call_ledger = _load(
            root / "stage1-call-ledgers" / f"{participant_id.removeprefix('actor:')}.json"
        )
        for entry in call_ledger["entries"]:
            case_id = str(entry["case_id"])
            review = _load(root / str(entry["relative_capture_path"]) / "review.json")
            if semantic_digest(review) != entry["review_digest"]:
                raise ValueError(f"A Stage-1 review drifted for {participant_id} {case_id}.")
            reviews[case_id].append(review)
    return freezes, reviews


def _stage2_inputs(
    project_root: Path,
) -> dict[str, list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]]:
    root = project_root / STAGE2_REVIEW_RELATIVE
    schema_root = project_root / "reference/schemas-v0.18.0"
    captures: dict[str, list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]] = {
        case_id: [] for case_id in CASE_IDS
    }
    for ledger_path in sorted((root / "stage2-call-ledgers").glob("*.json")):
        ledger = _load(ledger_path)
        supplied = dict(ledger)
        digest = supplied.pop("ledger_digest", None)
        if digest != semantic_digest(supplied):
            raise ValueError(f"A Stage-2 call ledger does not replay: {ledger_path.name}")
        if ledger["protocol_digest"] != STAGE2_PROTOCOL_DIGEST:
            raise ValueError("A Stage-2 call ledger is outside the frozen v2 protocol.")
        for entry in ledger["entries"]:
            case_id = str(entry["case_id"])
            loaded = load_review_capture(root / str(entry["relative_capture_path"]), schema_root)
            review, _packet, _manifest = loaded
            if semantic_digest(review) != entry["review_digest"]:
                raise ValueError(f"A Stage-2 review drifted for {case_id}.")
            captures[case_id].append(loaded)
    if any(len(items) != 2 for items in captures.values()):
        raise ValueError("Stage-2 does not supply exactly two admitted reviews per case.")
    return captures


def _answer_side_refs(project_root: Path, case_id: str) -> list[dict[str, str]]:
    slug = case_id.removeprefix("case:")
    declaration = _load(project_root / AUTHORING_RELATIVE / "author-declarations" / f"{slug}.json")
    validation = _load(
        project_root / AUTHORING_RELATIVE / "selected-result-validations" / f"{slug}.json"
    )
    return [
        {
            "record_type": "author_selected_result_declaration",
            "record_id": str(declaration["declaration_digest"]),
        },
        {
            "record_type": "selected_result_validation",
            "record_id": str(validation["validation_digest"]),
        },
    ]


def _reference_agent_configuration(
    stage1_reviews: list[dict[str, Any]], stage2_reviews: list[dict[str, Any]]
) -> list[dict[str, str]]:
    rows: dict[tuple[str, str], dict[str, str]] = {}
    for review in [*stage1_reviews, *stage2_reviews]:
        agent = review["reviewer_agent"]
        key = (str(agent["provider"]), str(agent["model_id"]))
        rows[key] = {
            "agent_surface": str(agent["agent_surface"]),
            "model_id": str(agent["model_id"]),
            "model_name": str(agent["model_name"]),
            "provider": str(agent["provider"]),
        }
    return [rows[key] for key in sorted(rows)]


def freeze_first_direct_pilot_scientific_labels(project_root: Path) -> dict[str, Any]:
    output_root = project_root / LABELS_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"Scientific-label output already exists: {output_root}")
    schema_root = project_root / "reference/schemas-v0.18.0"
    freezes, stage1_reviews = _stage1_inputs(project_root)
    stage2 = _stage2_inputs(project_root)

    output_root.mkdir(parents=True)
    rows: list[dict[str, Any]] = []
    try:
        for case_id in CASE_IDS:
            slug = case_id.removeprefix("case:")
            label_status = LABEL_STATUS_BY_CASE[case_id]
            stage2_reviews = [item[0] for item in stage2[case_id]]
            stage2_packets = [item[1] for item in stage2[case_id]]
            stage2_manifests = [item[2] for item in stage2[case_id]]
            case_stage1 = stage1_reviews[case_id]

            roots: list[dict[str, Any]] = []
            if label_status == "positive_demonstrated":
                statement_source = sorted(str(review["review_id"]) for review in stage2_reviews)[0]
                root = build_adjudicated_root_cause_cross_model(
                    case_stage1,
                    stage2_reviews,
                    schema_root,
                    adjudicated_at=ADJUDICATED_AT,
                    statement_source_review_id=statement_source,
                    required_scientific_premises=[],
                    stronger_claims_excluded=list(STRONGER_CLAIMS_EXCLUDED),
                    output=output_root / f"{slug}.adjudicated-root-cause.json",
                )
                roots = [root]

            _validate_eligible_panel(label_status, roots, case_stage1, stage2_reviews)

            adjudication: dict[str, Any] = {
                "schema_version": "0.18.0",
                "record_type": "evaluation_benchmark_adjudication",
                "adr_reference": ADR_REFERENCE,
                "public_benchmark_adjudication_deferred_reason": (
                    "The immutable public BenchmarkAdjudication schema requires a "
                    "cross-provider panel; ADR-0066 authorizes this evaluation-private "
                    "cross-model record instead, and public issuance is deferred until a "
                    "cross-provider panel or an accepted v0.19 schema ADR exists."
                ),
                "adjudication_id": f"benchmark-adjudication:{slug}-pilot-v1",
                "case_id": case_id,
                "protocol_version": "1.0.0",
                "review_basis": "agent_panel",
                "stage1_review_refs": [
                    {"record_type": "agent_review", "record_id": str(review["review_id"])}
                    for review in sorted(case_stage1, key=lambda item: str(item["review_id"]))
                ],
                "stage2_review_refs": [
                    {"record_type": "agent_review", "record_id": str(review["review_id"])}
                    for review in sorted(stage2_reviews, key=lambda item: str(item["review_id"]))
                ],
                "provider_families": ["Anthropic"],
                "model_families": [
                    "Anthropic:Claude Fable 5",
                    "Anthropic:Claude Opus 5",
                ],
                "provider_participation": [
                    {
                        "provider_family": "Anthropic",
                        "stage1_review_count": 4,
                        "stage2_review_count": 2,
                        "distinct_execution_context_count": 6,
                    }
                ],
                "label_status": label_status,
                "agreement": {
                    "cross_provider_support": False,
                    "cross_model_support": True,
                    "material_disagreement": False,
                    "unresolved_dissent_excluded": True,
                    "notes": (
                        "Single-provider cross-model panel under ADR-0066: reviewers from "
                        "two distinct Claude model families independently support this label."
                    ),
                },
                "deterministic_checks": {
                    "bounded_entailment_checked": True,
                    "claim_output_agreement_checked": True,
                    "counterevidence_checked": True,
                    "falsification_records_complete": True,
                    "fixture_scope_complete": True,
                    "source_references_resolved": True,
                },
                "majority_vote_permitted": False,
                "agent_only_disclosure": AGENT_ONLY_DISCLOSURE,
                "answer_side_evidence_refs": _answer_side_refs(project_root, case_id),
                "reference_agent_configuration": _reference_agent_configuration(
                    case_stage1, stage2_reviews
                ),
                "adjudicated_at": ADJUDICATED_AT,
                "provenance": {
                    "actor": {
                        "actor_kind": "controller",
                        "actor_id": "software:sc-referee-eval",
                        "display_name": "sc-referee evaluation controller",
                    },
                    "method": "deterministic_evaluation_runner",
                    "created_at": ADJUDICATED_AT,
                    "tool": "sc-referee-eval",
                    "tool_version": "0.1.0",
                },
                "adjudicated_root_cause_refs": [
                    {
                        "record_type": "adjudicated_root_cause",
                        "record_id": str(root["adjudicated_root_cause_id"]),
                    }
                    for root in roots
                ],
                "root_cause_reconciliation_status": ("verified" if roots else "not_applicable"),
                "exclusion_reason": None,
            }
            write_normalized_json_once(
                output_root / f"{slug}.benchmark-adjudication.json", adjudication
            )

            frozen = freeze_scientific_label_cross_model(
                adjudication,
                freezes[case_id],
                stage2_reviews,
                stage2_packets,
                stage2_manifests,
                schema_root,
                frozen_at=FROZEN_AT,
                output=output_root / f"{slug}.scientific-label-freeze.json",
                stage1_reviews=case_stage1,
                adjudicated_root_causes=roots,
            )
            rows.append(
                {
                    "case_id": case_id,
                    "label_status": label_status,
                    "adjudication_id": adjudication["adjudication_id"],
                    "adjudication_digest": semantic_digest(adjudication),
                    "adjudicated_root_cause_ids": [
                        str(root["adjudicated_root_cause_id"]) for root in roots
                    ],
                    "label_freeze_digest": frozen["freeze_digest"],
                }
            )

        ledger: dict[str, Any] = {
            "artifact_kind": "direct_qualification_pilot_scientific_label_ledger",
            "ledger_version": "1.0.0",
            "adr_reference": ADR_REFERENCE,
            "stage1_panel_ledger_digest": PANEL_LEDGER_DIGEST,
            "stage2_protocol_digest": STAGE2_PROTOCOL_DIGEST,
            "canonical_issue_class_scope": CANONICAL_ISSUE_CLASS,
            "entries": rows,
            "label_count": len(rows),
            "eligible_label_count": sum(
                1
                for row in rows
                if row["label_status"] in {"positive_demonstrated", "verified_good_eligible"}
            ),
            "detector_output_observed": False,
            "scientific_label_count": len(rows),
            "detector_outcome_count": 0,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_scientific_labels_only",
        }
        ledger["ledger_digest"] = semantic_digest(ledger)
        write_normalized_json_once(output_root / "SCIENTIFIC_LABEL_LEDGER.json", ledger)
        return ledger
    except BaseException:
        import shutil

        shutil.rmtree(output_root, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    ledger = freeze_first_direct_pilot_scientific_labels(arguments.project_root.resolve())
    print(ledger["ledger_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
