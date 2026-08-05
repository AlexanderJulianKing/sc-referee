from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_three_case_pilot_authoring import (
    ACTIVE_REVIEWER_LEDGER_DIGEST,
    ELIGIBLE_CELL_TYPES,
    PILOT_AUTHORING_RELATIVE,
    build_first_direct_three_case_pilot_authoring,
)


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_three_case_pilot_authoring_artifacts_rebuild_exactly(project_root: Path) -> None:
    rebuilt = build_first_direct_three_case_pilot_authoring(project_root)
    for name, artifact in rebuilt.items():
        assert artifact == _load(project_root / PILOT_AUTHORING_RELATIVE / name)


def test_three_case_scope_retains_surplus_assignments_unopened(project_root: Path) -> None:
    scope = build_first_direct_three_case_pilot_authoring(project_root)[
        "PILOT_SCOPE_AMENDMENT.json"
    ]
    digest = scope.pop("amendment_digest")
    assert digest == semantic_digest(scope)
    assert tuple(scope["eligible_cell_types"]) == ELIGIBLE_CELL_TYPES
    assert len(scope["eligible_assignments"]) == 3
    assert len(scope["excluded_unopened_assignments"]) == 4
    assert {item["state"] for item in scope["excluded_unopened_assignments"]} == {
        "unopened_metric_ineligible"
    }
    assert scope["other_envelopes_authorized"] is False
    assert scope["preexposure_state"] == {
        "author_brief_exposure_count": 0,
        "authored_case_count": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
    }


def test_authoring_protocol_exposes_only_three_briefs_to_two_authors(project_root: Path) -> None:
    protocol = build_first_direct_three_case_pilot_authoring(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]
    digest = protocol.pop("protocol_digest")
    assert digest == semantic_digest(protocol)
    assignments = protocol["author_assignments"]
    assert len(assignments) == 2
    assert sorted(len(item["case_ids"]) for item in assignments) == [1, 2]
    assert sum(len(item["case_ids"]) for item in assignments) == 3
    assert {item["participant"]["provider"] for item in assignments} == {
        "Anthropic",
        "OpenAI",
    }
    assert protocol["active_reviewer_calibration_ledger_digest"] == (ACTIVE_REVIEWER_LEDGER_DIGEST)
    assert protocol["execution_policy"]["exact_case_count"] == 3
    assert protocol["execution_policy"]["heldout_brief_access_permitted"] is False
    assert protocol["execution_policy"]["excluded_pilot_brief_access_permitted"] is False
    assert protocol["execution_state"] == "frozen_not_started"
    assert protocol["qualification_authority"] == "none_authoring_protocol_only"


def test_author_prompts_have_exact_digests_and_no_controller_fields(project_root: Path) -> None:
    protocol = build_first_direct_three_case_pilot_authoring(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]
    forbidden = (
        "cell_type",
        "block_id",
        "relation-envelope:",
        "check:",
        "detector:",
        "canonical_issue_class",
        "heldout",
        "hard_negative",
        "ambiguous",
        "renamed_implementation",
    )
    for assignment in protocol["author_assignments"]:
        prompt = assignment["prompt"]
        assert assignment["prompt_digest"] == sha256_digest(prompt)
        assert assignment["output_schema_digest"] == semantic_digest(assignment["output_schema"])
        serialized = prompt.casefold()
        assert not any(term.casefold() in serialized for term in forbidden)
        assert set(assignment["case_ids"]) == set(
            assignment["output_schema"]["properties"]["authored_cases"]["items"]["properties"][
                "case_id"
            ]["enum"]
        )


def test_only_the_unavailable_claude_author_surface_is_replaced(project_root: Path) -> None:
    protocol = build_first_direct_three_case_pilot_authoring(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]
    replacements = protocol["author_configuration_replacements"]
    assert len(replacements) == 1
    assert replacements[0]["participant_id"] == "actor:pilot-author-claude-01"
    participants = {
        item["participant"]["provider"]: item["participant"]
        for item in protocol["author_assignments"]
    }
    assert participants["Anthropic"]["agent_surface"] == "Claude Desktop App chat"
    assert participants["Anthropic"]["agent_version"] == "1.25927.0"
    assert participants["OpenAI"]["agent_surface"] == "Codex CLI"
    assert participants["OpenAI"]["agent_version"] == "0.144.0"
