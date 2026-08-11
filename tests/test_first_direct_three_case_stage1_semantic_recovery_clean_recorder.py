from __future__ import annotations

import json
import shutil
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from sc_referee_evaluation.capture import load_review_capture
from sc_referee_evaluation.review_protocol import validate_stage1_freeze_evidence

import scripts.record_first_direct_three_case_stage1_semantic_recovery_clean as stage1_recorder
from sc_referee.core.ids import semantic_digest
from scripts.build_first_direct_three_case_stage1_protocol import CASE_IDS
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_protocol import (
    ACTIVE_REVIEWERS,
    REVIEW_RELATIVE,
)
from scripts.record_first_direct_three_case_stage1_semantic_recovery_clean import (
    PROTOCOL_DIGEST,
    build_stage1_call_capture,
    finalize_stage1_panel,
    record_stage1_call,
    validate_stage1_call_capture,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_RELATIVE = Path("reference/schemas-v0.19.0")


@pytest.fixture(autouse=True)
def _current_schema_for_new_review_projection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(stage1_recorder, "SCHEMA_RELATIVE", SCHEMA_RELATIVE)


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _render_timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _copy_protocol_project(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    source_root = PROJECT_ROOT / REVIEW_RELATIVE
    target_root = tmp_path / REVIEW_RELATIVE
    target_root.mkdir(parents=True)
    shutil.copy2(
        source_root / "STAGE1_REVIEW_PROTOCOL.json",
        target_root / "STAGE1_REVIEW_PROTOCOL.json",
    )
    shutil.copytree(source_root / "stage1-packets", target_root / "stage1-packets")
    protocol = _load(target_root / "STAGE1_REVIEW_PROTOCOL.json")
    for binding in protocol["source_case_bindings"]:
        relative = Path(str(binding["source_workspace_relative_path"]))
        shutil.copytree(PROJECT_ROOT / relative, tmp_path / relative)
    for item in protocol["controller_implementation"]:
        relative = Path(str(item["path"]))
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT_ROOT / relative, destination)
    shutil.copytree(
        PROJECT_ROOT / SCHEMA_RELATIVE,
        tmp_path / SCHEMA_RELATIVE,
        dirs_exist_ok=True,
    )
    return tmp_path, protocol


def _first_nonempty_span(path: Path, relative: str) -> dict[str, Any]:
    for line_number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if text:
            return {
                "path": relative,
                "start_line": line_number,
                "end_line": line_number,
                "quoted_text": text,
            }
    raise AssertionError(f"Synthetic evidence file is empty: {path}")


def _semantic_payload(
    project_root: Path,
    protocol: dict[str, Any],
    call: dict[str, Any],
) -> dict[str, Any]:
    bindings = {str(item["case_id"]): item for item in protocol["source_case_bindings"]}
    reviews = []
    for case_id in call["case_order"]:
        workspace = project_root / str(bindings[case_id]["source_workspace_relative_path"])
        reviews.append(
            {
                "case_id": case_id,
                "verdict": "no_demonstrated_issue_within_scope",
                "bounded_statement": None,
                "root_cause": None,
                "issue_class": None,
                "evidence_atoms": [
                    {
                        "description": "The visible task defines the requested scientific scope.",
                        "source_spans": [_first_nonempty_span(workspace / "task.md", "task.md")],
                    }
                ],
                "counterevidence_atoms": [
                    {
                        "description": "The selected report was checked against that scope.",
                        "source_spans": [
                            _first_nonempty_span(
                                workspace / "results/report.md", "results/report.md"
                            )
                        ],
                    }
                ],
                "falsification_attempt": (
                    "Checked whether the visible task instead made the requested rate conditional "
                    "on the retained subset."
                ),
                "cross_case_evidence_used": False,
                "unresolved_material_questions": [],
                "self_reported_confidence": "high",
            }
        )
    return {
        "reviewer_participant_id": call["participant_id"],
        "reviews": reviews,
    }


def _call_capture(
    project_root: Path,
    protocol: dict[str, Any],
    call: dict[str, Any],
    *,
    minute: int,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = json.dumps(
        payload or _semantic_payload(project_root, protocol, call),
        sort_keys=True,
    ).encode("utf-8")
    frozen_at = datetime.fromisoformat(str(protocol["frozen_at"]).replace("Z", "+00:00"))
    started_at = frozen_at + timedelta(minutes=minute)
    return build_stage1_call_capture(
        project_root,
        str(call["participant_id"]),
        response,
        started_at=_render_timestamp(started_at),
        completed_at=_render_timestamp(started_at + timedelta(seconds=30)),
        captured_at=_render_timestamp(started_at + timedelta(seconds=31)),
        transport={"surface": "synthetic_test_only", "model_call_performed": False},
    )


def test_semantic_recovery_clean_recorder_rejects_one_invalid_review_without_partial_admission(
    tmp_path: Path,
) -> None:
    assert ACTIVE_REVIEWERS == [
        "actor:stage1-recovery-claude-01",
        "actor:stage1-recovery-claude-03",
        "actor:stage1-recovery-codex-03",
        "actor:stage1-recovery-codex-04",
    ]
    project_root, protocol = _copy_protocol_project(tmp_path)
    assert protocol["protocol_digest"] == PROTOCOL_DIGEST
    call = protocol["calls"][0]
    payload = _semantic_payload(project_root, protocol, call)
    payload["reviews"][1]["unresolved_material_questions"] = [
        "A material question that could reverse this eligible verdict remains unresolved."
    ]
    capture = _call_capture(
        project_root,
        protocol,
        call,
        minute=1,
        payload=payload,
    )
    incoming = project_root / "incoming-invalid.json"
    incoming.write_text(json.dumps(capture), encoding="utf-8")

    with pytest.raises(ValueError, match="semantic payload is invalid"):
        validate_stage1_call_capture(project_root, deepcopy(capture))
    with pytest.raises(ValueError, match="semantic payload is invalid"):
        record_stage1_call(project_root, incoming)

    review_root = project_root / REVIEW_RELATIVE
    assert not (review_root / "stage1-captures").exists()
    assert not (review_root / "stage1-call-ledgers").exists()


def test_semantic_recovery_clean_recorder_captures_and_freezes_complete_panel(
    tmp_path: Path,
) -> None:
    project_root, protocol = _copy_protocol_project(tmp_path)
    review_root = project_root / REVIEW_RELATIVE
    for index, call in enumerate(protocol["calls"], start=1):
        capture = _call_capture(
            project_root,
            protocol,
            call,
            minute=index + 1,
        )
        reviews = validate_stage1_call_capture(project_root, deepcopy(capture))
        assert len(reviews) == len(CASE_IDS)
        assert all(not review["unresolved_material_questions"] for review in reviews)
        incoming = project_root / f"incoming-{index}.json"
        incoming.write_text(json.dumps(capture), encoding="utf-8")
        ledger = record_stage1_call(project_root, incoming)
        assert ledger["review_count"] == len(CASE_IDS)
        assert ledger["scientific_label_count"] == ledger["detector_outcome_count"] == 0

    protocol_frozen_at = datetime.fromisoformat(str(protocol["frozen_at"]).replace("Z", "+00:00"))
    panel = finalize_stage1_panel(
        project_root,
        frozen_at=_render_timestamp(protocol_frozen_at + timedelta(minutes=10)),
    )
    assert panel["protocol_digest"] == PROTOCOL_DIGEST
    assert panel["model_call_count"] == len(ACTIVE_REVIEWERS)
    assert panel["review_count"] == len(ACTIVE_REVIEWERS) * len(CASE_IDS)
    assert panel["stage1_freeze_count"] == len(CASE_IDS)
    assert panel["verdict_counts"] == {
        "no_demonstrated_issue_within_scope": len(ACTIVE_REVIEWERS) * len(CASE_IDS)
    }
    assert panel["semantic_contract"] == "stage1-semantic-payload-v2"

    protocol_calls = {str(item["participant_id"]): item for item in protocol["calls"]}
    for case_panel in panel["case_panels"]:
        case_id = str(case_panel["case_id"])
        reviews = []
        packets = []
        manifests = []
        for participant_id in ACTIVE_REVIEWERS:
            call = protocol_calls[participant_id]
            packet_ref = next(item for item in call["packet_refs"] if item["case_id"] == case_id)
            destination = next(
                destination
                for item, destination in zip(
                    call["packet_refs"], call["capture_destinations"], strict=True
                )
                if item["case_id"] == case_id
            )
            review, packet, manifest = load_review_capture(
                review_root / destination,
                project_root / SCHEMA_RELATIVE,
            )
            assert packet["packet_digest"] == packet_ref["packet_digest"]
            reviews.append(review)
            packets.append(packet)
            manifests.append(manifest)
        frozen = _load(review_root / str(case_panel["freeze_relative_path"]))
        validate_stage1_freeze_evidence(
            frozen,
            reviews,
            packets,
            manifests,
            project_root / SCHEMA_RELATIVE,
        )
        assert frozen["freeze_digest"] == case_panel["freeze_digest"]
        assert frozen["provider_participation"] == {"Anthropic": 2, "OpenAI": 2}
        assert semantic_digest(frozen) != frozen["freeze_digest"]
