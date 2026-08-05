from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_three_case_pilot_authoring import PILOT_AUTHORING_RELATIVE
from scripts.build_first_direct_three_case_pilot_intake_recovery import (
    FAILED_CLAUDE_CAPTURE_DIGEST,
    FAILED_CLAUDE_RAW_DIGEST,
    PARENT_PROTOCOL_DIGEST,
    build_first_direct_three_case_pilot_intake_recovery,
)


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_intake_recovery_amendment_rebuilds_exactly(project_root: Path) -> None:
    rebuilt = build_first_direct_three_case_pilot_intake_recovery(project_root)
    retained = _load(
        project_root / PILOT_AUTHORING_RELATIVE / "AUTHORING_INTAKE_RECOVERY_AMENDMENT.json"
    )
    assert rebuilt == retained
    digest = rebuilt.pop("amendment_digest")
    assert digest == semantic_digest(rebuilt)


def test_recovery_is_bound_to_pre_admission_transport_failure(project_root: Path) -> None:
    amendment = build_first_direct_three_case_pilot_intake_recovery(project_root)
    trigger = amendment["triggering_attempt"]
    policy = amendment["execution_policy"]
    state = amendment["freeze_state"]
    assert amendment["parent_protocol_digest"] == PARENT_PROTOCOL_DIGEST
    assert trigger["input_capture_digest"] == FAILED_CLAUDE_CAPTURE_DIGEST
    assert trigger["raw_response_digest"] == FAILED_CLAUDE_RAW_DIGEST
    assert trigger["failure_class"] == "invalid_json_before_schema_or_scientific_admission"
    assert trigger["retained_unchanged"] is True
    assert policy["additional_attempt_count"] == 1
    assert policy["further_repair_retry_or_replacement_permitted"] is False
    assert policy["scientific_feedback_visible_to_recovery_author"] is False
    assert policy["heldout_brief_access_permitted"] is False
    assert policy["excluded_pilot_brief_access_permitted"] is False
    assert state == {
        "admitted_case_count": 0,
        "scientific_review_count": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "scientific_content_selection_criterion_used": False,
    }


def test_recovery_changes_transport_instructions_not_briefs_or_schema(
    project_root: Path,
) -> None:
    amendment = build_first_direct_three_case_pilot_intake_recovery(project_root)
    protocol = _load(project_root / PILOT_AUTHORING_RELATIVE / "PILOT_AUTHORING_PROTOCOL.json")
    original = next(
        item
        for item in protocol["author_assignments"]
        if item["participant"]["provider"] == "Anthropic"
    )
    recovery = amendment["transport_recovery_assignment"]
    assert recovery["case_ids"] == original["case_ids"]
    assert recovery["author_visible_brief_digests"] == original["author_visible_brief_digests"]
    assert recovery["output_schema"] == original["output_schema"]
    assert recovery["output_schema_digest"] == original["output_schema_digest"]
    assert recovery["prompt_digest"] == sha256_digest(recovery["prompt"])
    assert "Return syntactically valid JSON" in recovery["prompt"]
    assert "no scientific feedback" in recovery["prompt"]
    assert recovery["replacement_count"] == 1


def test_codex_canonicalization_is_metadata_only_and_conflict_rejecting(
    project_root: Path,
) -> None:
    rule = build_first_direct_three_case_pilot_intake_recovery(project_root)[
        "codex_declaration_canonicalization"
    ]
    assert rule["canonical_candidate_result_spans"] == []
    assert rule["distinct_or_conflicting_candidate_span_rejected"] is True
    assert rule["selected_result_projection_unchanged"] is True
    assert rule["file_content_unchanged"] is True
    assert rule["scientific_content_unchanged"] is True
