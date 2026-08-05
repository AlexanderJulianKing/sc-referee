from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from sc_referee_evaluation.authoring_render_grammar import RENDER_ONLY_PROFILE_ID

from sc_referee.core.ids import semantic_digest
from scripts.build_first_direct_three_case_pilot_authoring_v3 import (
    PILOT_AUTHORING_V3_RELATIVE,
)
from scripts.build_first_direct_three_case_pilot_authoring_v4 import (
    AUTHOR_REPLACEMENTS,
    PILOT_AUTHORING_V4_RELATIVE,
    SOURCE_COMMIT,
    V3_FAILURE_LEDGER_DIGEST,
    _visible_briefs,
    build_first_direct_three_case_pilot_authoring_v4,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v4_authoring_artifacts_replay_generated_freeze(project_root: Path) -> None:
    built = build_first_direct_three_case_pilot_authoring_v4(project_root)
    root = project_root / PILOT_AUTHORING_V4_RELATIVE
    assert built == {name: _load(root / name) for name in built}
    amendment = built["PILOT_AUTHORING_RESTART_AMENDMENT.json"]
    protocol = built["PILOT_AUTHORING_PROTOCOL.json"]
    assert amendment["failed_v3_authoring_intake_ledger_digest"] == V3_FAILURE_LEDGER_DIGEST
    assert amendment["scientific_briefs_changed"] is False
    assert amendment["detector_or_selected_result_verifier_changed"] is False
    assert amendment["render_grammar_source_commit"] == SOURCE_COMMIT
    assert protocol["render_grammar_profile_id"] == RENDER_ONLY_PROFILE_ID
    assert protocol["execution_state"] == "frozen_not_started"
    assert protocol["execution_policy"]["repair_retry_or_replacement_permitted"] is False
    assert amendment["amendment_digest"] == semantic_digest(
        {key: value for key, value in amendment.items() if key != "amendment_digest"}
    )
    assert protocol["protocol_digest"] == semantic_digest(
        {key: value for key, value in protocol.items() if key != "protocol_digest"}
    )


def test_v4_uses_fresh_identities_and_preserves_scientific_briefs(project_root: Path) -> None:
    built = build_first_direct_three_case_pilot_authoring_v4(project_root)
    amendment = built["PILOT_AUTHORING_RESTART_AMENDMENT.json"]
    protocol = built["PILOT_AUTHORING_PROTOCOL.json"]
    v3_protocol = _load(
        project_root / PILOT_AUTHORING_V3_RELATIVE / "PILOT_AUTHORING_PROTOCOL.json"
    )
    v3_briefs = {
        brief["case_id"]: brief
        for assignment in v3_protocol["author_assignments"]
        for brief in _visible_briefs(assignment["prompt"])
    }
    v4_briefs = {
        brief["case_id"]: brief
        for assignment in protocol["author_assignments"]
        for brief in _visible_briefs(assignment["prompt"])
    }
    assert {
        item["participant"]["participant_id"] for item in protocol["author_assignments"]
    } == set(AUTHOR_REPLACEMENTS.values())
    for assignment in amendment["restart_assignments"]:
        old = deepcopy(v3_briefs[assignment["superseded_failed_case_id"]])
        new = deepcopy(v4_briefs[assignment["case_id"]])
        old.pop("case_id")
        old.pop("brief_version")
        new.pop("case_id")
        new.pop("brief_version")
        assert new == old


def test_v4_prompt_freezes_the_small_generic_render_grammar(project_root: Path) -> None:
    protocol = build_first_direct_three_case_pilot_authoring_v4(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]
    for assignment in protocol["author_assignments"]:
        prompt = assignment["prompt"]
        assert "After line 5, do not read, parse, split, strip, convert, index, slice" in prompt
        assert "SOURCE_LINE_COUNT and LF are the only prefix names" in prompt
        assert "REPORT_TEXT exactly once as the last render assignment" in prompt
        assert "producer_span is exactly the single final writer line" in prompt
        assert "inputs/data.csv, workflow/analysis.py, and results/report.md" in prompt


def test_v4_new_case_ids_are_disjoint_from_v3(project_root: Path) -> None:
    protocol = build_first_direct_three_case_pilot_authoring_v4(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]
    v3_protocol = _load(
        project_root / PILOT_AUTHORING_V3_RELATIVE / "PILOT_AUTHORING_PROTOCOL.json"
    )
    v4_ids = {case_id for item in protocol["author_assignments"] for case_id in item["case_ids"]}
    v3_ids = {case_id for item in v3_protocol["author_assignments"] for case_id in item["case_ids"]}
    assert len(v4_ids) == 3
    assert v4_ids.isdisjoint(v3_ids)
