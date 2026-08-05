from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_three_case_pilot_authoring_v2 import (
    FAILED_INTAKE_LEDGER_DIGEST,
    PILOT_AUTHORING_V2_RELATIVE,
    build_first_direct_three_case_pilot_authoring_v2,
)


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_second_authoring_iteration_rebuilds_exactly(project_root: Path) -> None:
    built = build_first_direct_three_case_pilot_authoring_v2(project_root)
    for name, value in built.items():
        assert value == _load(project_root / PILOT_AUTHORING_V2_RELATIVE / name)


def test_restart_retains_failed_iteration_and_uses_new_opaque_cases(
    project_root: Path,
) -> None:
    restart = build_first_direct_three_case_pilot_authoring_v2(project_root)[
        "PILOT_AUTHORING_RESTART_AMENDMENT.json"
    ]
    digest = restart.pop("amendment_digest")
    assert digest == semantic_digest(restart)
    assert restart["failed_selected_result_intake_ledger_digest"] == (FAILED_INTAKE_LEDGER_DIGEST)
    assignments = restart["restart_assignments"]
    assert len(assignments) == 3
    assert len({item["case_id"] for item in assignments}) == 3
    assert not {item["case_id"] for item in assignments} & {
        item["superseded_failed_case_id"] for item in assignments
    }
    assert {item["cell_type"] for item in assignments} == {
        "error_bearing",
        "corrected_twin",
        "valid_alternative",
    }
    assert restart["failed_iteration_retained"] is True
    assert restart["failed_case_bytes_repaired_or_reused"] is False
    assert restart["scientific_briefs_changed"] is False
    assert restart["scientific_label_count_at_freeze"] == 0
    assert restart["detector_outcome_count_at_freeze"] == 0


def test_v2_protocol_uses_two_fresh_authors_and_line_array_transport(
    project_root: Path,
) -> None:
    protocol = build_first_direct_three_case_pilot_authoring_v2(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]
    digest = protocol.pop("protocol_digest")
    assert digest == semantic_digest(protocol)
    assignments = protocol["author_assignments"]
    assert {item["participant"]["participant_id"] for item in assignments} == {
        "actor:pilot-author-claude-02",
        "actor:pilot-author-codex-02",
    }
    assert sum(len(item["case_ids"]) for item in assignments) == 3
    for assignment in assignments:
        assert assignment["prompt_digest"] == sha256_digest(assignment["prompt"])
        assert assignment["output_schema_digest"] == semantic_digest(assignment["output_schema"])
        file_schema = assignment["output_schema"]["properties"]["authored_cases"]["items"][
            "properties"
        ]["producer_file"]
        assert "content_lines" in file_schema["properties"]
        assert "exactly: from pathlib import Path" in assignment["prompt"]
        assert ".write_text(REPORT_TEXT)" in assignment["prompt"]
        assert "answer key" in assignment["prompt"]
    policy = protocol["execution_policy"]
    assert policy["one_attempt_per_author_context"] is True
    assert policy["repair_retry_or_replacement_permitted"] is False
    assert policy["failed_iteration_access_permitted"] is False
    assert policy["heldout_brief_access_permitted"] is False


def test_v2_author_prompts_do_not_expose_controller_scientific_fields(
    project_root: Path,
) -> None:
    protocol = build_first_direct_three_case_pilot_authoring_v2(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]
    forbidden = (
        "cell_type",
        "block_id",
        "relation-envelope:",
        "check:",
        "canonical_issue_class",
        "heldout",
        "hard_negative",
        "renamed_implementation",
        "python_source_parse_failed",
        "unsupported_selected_report_writer_signature",
    )
    for assignment in protocol["author_assignments"]:
        prompt = assignment["prompt"].casefold()
        assert not any(term.casefold() in prompt for term in forbidden)
