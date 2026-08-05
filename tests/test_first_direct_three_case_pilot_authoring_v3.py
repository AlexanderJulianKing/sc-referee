from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from sc_referee.core.ids import semantic_digest
from scripts.build_first_direct_three_case_pilot_authoring_v2 import (
    PILOT_AUTHORING_V2_RELATIVE,
)
from scripts.build_first_direct_three_case_pilot_authoring_v3 import (
    AUTHOR_REPLACEMENTS,
    PILOT_AUTHORING_V3_RELATIVE,
    V2_FAILURE_LEDGER_DIGEST,
    build_first_direct_three_case_pilot_authoring_v3,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _visible_briefs(prompt: str) -> list[dict]:
    marker = "Author-visible briefs:\n"
    start = prompt.index(marker) + len(marker)
    end = prompt.index("\n\nReturn only one unfenced JSON object", start)
    return json.loads(prompt[start:end])


def test_v3_authoring_artifacts_replay_generated_freeze(project_root: Path) -> None:
    built = build_first_direct_three_case_pilot_authoring_v3(project_root)
    root = project_root / PILOT_AUTHORING_V3_RELATIVE
    assert built == {name: _load(root / name) for name in built}
    amendment = built["PILOT_AUTHORING_RESTART_AMENDMENT.json"]
    protocol = built["PILOT_AUTHORING_PROTOCOL.json"]
    assert amendment["failed_v2_authoring_intake_ledger_digest"] == V2_FAILURE_LEDGER_DIGEST
    assert amendment["scientific_briefs_changed"] is False
    assert amendment["detector_or_verifier_changed"] is False
    assert protocol["execution_state"] == "frozen_not_started"
    assert protocol["execution_policy"]["repair_retry_or_replacement_permitted"] is False
    assert amendment["amendment_digest"] == semantic_digest(
        {key: value for key, value in amendment.items() if key != "amendment_digest"}
    )
    assert protocol["protocol_digest"] == semantic_digest(
        {key: value for key, value in protocol.items() if key != "protocol_digest"}
    )


def test_v3_uses_fresh_opaque_identities_and_unchanged_scientific_briefs(
    project_root: Path,
) -> None:
    built = build_first_direct_three_case_pilot_authoring_v3(project_root)
    amendment = built["PILOT_AUTHORING_RESTART_AMENDMENT.json"]
    protocol = built["PILOT_AUTHORING_PROTOCOL.json"]
    v2_protocol = _load(
        project_root / PILOT_AUTHORING_V2_RELATIVE / "PILOT_AUTHORING_PROTOCOL.json"
    )
    v2_briefs = {
        brief["case_id"]: brief
        for assignment in v2_protocol["author_assignments"]
        for brief in _visible_briefs(assignment["prompt"])
    }
    v3_briefs = {
        brief["case_id"]: brief
        for assignment in protocol["author_assignments"]
        for brief in _visible_briefs(assignment["prompt"])
    }
    assert {
        item["participant"]["participant_id"] for item in protocol["author_assignments"]
    } == set(AUTHOR_REPLACEMENTS.values())
    assert all(
        "-03" in item["participant"]["participant_id"] for item in protocol["author_assignments"]
    )
    for assignment in amendment["restart_assignments"]:
        old = deepcopy(v2_briefs[assignment["superseded_failed_case_id"]])
        new = deepcopy(v3_briefs[assignment["case_id"]])
        old.pop("case_id")
        old.pop("brief_version")
        new.pop("case_id")
        new.pop("brief_version")
        assert new == old


def _minimal_response(assignment: dict) -> dict:
    case_id = assignment["case_ids"][0]
    return {
        "author_participant_id": assignment["participant"]["participant_id"],
        "authored_cases": [
            {
                "case_id": case_id,
                "input_file": {
                    "relative_path": "inputs/data.csv",
                    "content_lines": ["a,b", "1,2"],
                },
                "producer_file": {
                    "relative_path": "workflow/analysis.py",
                    "content_lines": ["from pathlib import Path"],
                },
                "report_file": {
                    "relative_path": "results/report.md",
                    "content_lines": ["[selected-result] x"],
                },
                "author_declaration": {
                    "declaration_state": "one_selected_result",
                    "selected_result_projection": {
                        "result_span": {"start_line": 1, "end_line": 1},
                        "producer_span": {"start_line": 1, "end_line": 1},
                    },
                    "candidate_result_spans": [],
                    "unsupported_producer_spans": [],
                },
            }
        ],
    }


def test_v3_schema_enforces_exact_roles_and_escape_free_physical_lines(
    project_root: Path,
) -> None:
    protocol = build_first_direct_three_case_pilot_authoring_v3(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]
    assignment = next(item for item in protocol["author_assignments"] if len(item["case_ids"]) == 1)
    response = _minimal_response(assignment)
    validator = Draft202012Validator(assignment["output_schema"])
    assert not list(validator.iter_errors(response))

    wrong_path = deepcopy(response)
    wrong_path["authored_cases"][0]["producer_file"]["relative_path"] = "analysis.py"
    assert list(validator.iter_errors(wrong_path))

    embedded_lf = deepcopy(response)
    embedded_lf["authored_cases"][0]["producer_file"]["content_lines"][0] = "x\ny"
    assert list(validator.iter_errors(embedded_lf))

    reverse_solidus = deepcopy(response)
    reverse_solidus["authored_cases"][0]["producer_file"]["content_lines"][0] = "x\\y"
    assert list(validator.iter_errors(reverse_solidus))


def test_v3_prompt_pins_escape_free_lf_and_final_writer_span(project_root: Path) -> None:
    protocol = build_first_direct_three_case_pilot_authoring_v3(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]
    for assignment in protocol["author_assignments"]:
        prompt = assignment["prompt"]
        assert "LF = SOURCE_TEXT[len(SOURCE_LINES[0])]" in prompt
        assert "Path('results/report.md').write_text(REPORT_TEXT)" in prompt
        assert "producer_span is exactly the single final writer line" in prompt
        assert "inputs/data.csv, workflow/analysis.py, and results/report.md" in prompt
