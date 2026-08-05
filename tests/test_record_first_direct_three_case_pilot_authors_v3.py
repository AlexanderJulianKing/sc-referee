from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from scripts.build_first_direct_three_case_pilot_authoring_v3 import (
    build_first_direct_three_case_pilot_authoring_v3,
)
from scripts.record_first_direct_three_case_pilot_authors import PilotAuthorRecordError
from scripts.record_first_direct_three_case_pilot_authors_v2 import _validate_static_case
from scripts.record_first_direct_three_case_pilot_authors_v3 import (
    normalize_v3_author_response,
)


def _assignment(project_root: Path) -> dict:
    protocol = build_first_direct_three_case_pilot_authoring_v3(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]
    return next(item for item in protocol["author_assignments"] if len(item["case_ids"]) == 1)


def _valid_response(assignment: dict) -> dict:
    case_id = assignment["case_ids"][0]
    return {
        "author_participant_id": assignment["participant"]["participant_id"],
        "authored_cases": [
            {
                "case_id": case_id,
                "input_file": {
                    "relative_path": "inputs/data.csv",
                    "content_lines": ["scheduled,eligible,events", "96,72,18"],
                },
                "producer_file": {
                    "relative_path": "workflow/analysis.py",
                    "content_lines": [
                        "from pathlib import Path",
                        "SOURCE_TEXT = Path('inputs/data.csv').read_text()",
                        "SOURCE_LINES = SOURCE_TEXT.splitlines()",
                        "SOURCE_LINE_COUNT = len(SOURCE_LINES)",
                        "LF = SOURCE_TEXT[len(SOURCE_LINES[0])]",
                        (
                            "RESULT_LINE = f'[selected-result] Input lines including header: "
                            "{SOURCE_LINE_COUNT}; target=signal-eligible; events=18; exposure=72; "
                            "rate=0.25' + LF"
                        ),
                        "REPORT_TEXT = RESULT_LINE",
                        "Path('results/report.md').write_text(REPORT_TEXT)",
                    ],
                },
                "report_file": {
                    "relative_path": "results/report.md",
                    "content_lines": [
                        "[selected-result] Input lines including header: 2; "
                        "target=signal-eligible; events=18; exposure=72; rate=0.25"
                    ],
                },
                "author_declaration": {
                    "declaration_state": "one_selected_result",
                    "selected_result_projection": {
                        "result_span": {"start_line": 1, "end_line": 1},
                        "producer_span": {"start_line": 8, "end_line": 8},
                    },
                    "candidate_result_spans": [],
                    "unsupported_producer_spans": [],
                },
            }
        ],
    }


def _static_arguments(assignment: dict) -> dict:
    return {
        "participant": assignment["participant"],
        "authored_at": "2026-08-05T04:50:00Z",
        "schedule": {
            "author_frozen_at": "2026-08-05T04:51:00Z",
            "coordinated_at": "2026-08-05T04:51:01Z",
            "contract_frozen_at": "2026-08-05T04:51:02Z",
            "derived_at": "2026-08-05T04:51:03Z",
            "derivation_frozen_at": "2026-08-05T04:51:04Z",
            "declaration_revealed_at": "2026-08-05T04:51:05Z",
            "compared_at": "2026-08-05T04:51:06Z",
        },
        "validator_identity": {
            "validator_id": "actor:selected-result-validator-01",
            "provider": "Local deterministic software",
            "execution_context_id": "context:selected-result-validator-v2",
            "identity_evidence_digest": "sha256:" + "a" * 64,
        },
        "envelope": {
            "envelope_id": "relation-envelope:complete-domain-exposure-denominator",
            "check_id": "check:complete-domain-exposure-denominator",
            "candidate_id": "complete-declared-domain-exposure",
            "binding_digest": "sha256:" + "b" * 64,
        },
    }


def test_escape_free_fixture_normalizes_and_replays_verified_complete(
    project_root: Path,
) -> None:
    assignment = _assignment(project_root)
    normalized = normalize_v3_author_response(_valid_response(assignment), assignment)
    assert normalized[0]["input_file"]["content"].endswith("\n")
    assert "\\" not in normalized[0]["producer_file"]["content"]
    frozen = _validate_static_case(normalized[0], **_static_arguments(assignment))
    assert frozen["derivation"]["derivation_status"] == "one_selected_result_rederived"
    assert frozen["validation"]["status"] == "verified_complete"


def test_v3_rejects_reverse_solidus_and_wrong_role_path(project_root: Path) -> None:
    assignment = _assignment(project_root)
    reverse_solidus = _valid_response(assignment)
    reverse_solidus["authored_cases"][0]["producer_file"]["content_lines"][5] = (
        "RESULT_LINE = 'bad\\n'"
    )
    with pytest.raises(PilotAuthorRecordError, match="schema failed"):
        normalize_v3_author_response(reverse_solidus, assignment)

    wrong_path = _valid_response(assignment)
    wrong_path["authored_cases"][0]["producer_file"]["relative_path"] = "analysis.py"
    with pytest.raises(PilotAuthorRecordError, match="schema failed"):
        normalize_v3_author_response(wrong_path, assignment)


def test_v3_rejects_nonfinal_selected_producer_span(project_root: Path) -> None:
    assignment = _assignment(project_root)
    response = _valid_response(assignment)
    response["authored_cases"][0]["author_declaration"]["selected_result_projection"][
        "producer_span"
    ] = {"start_line": 6, "end_line": 6}
    with pytest.raises(PilotAuthorRecordError, match="exactly the final writer"):
        normalize_v3_author_response(response, assignment)


def test_v3_rejects_non_ascii_or_embedded_terminator(project_root: Path) -> None:
    assignment = _assignment(project_root)
    non_ascii = _valid_response(assignment)
    non_ascii["authored_cases"][0]["report_file"]["content_lines"][0] += " café"
    with pytest.raises(PilotAuthorRecordError, match="ASCII physical lines"):
        normalize_v3_author_response(non_ascii, assignment)

    embedded = _valid_response(assignment)
    embedded["authored_cases"][0]["report_file"]["content_lines"][0] += "\nnext"
    with pytest.raises(PilotAuthorRecordError, match="schema failed"):
        normalize_v3_author_response(embedded, assignment)


def test_v3_final_writer_is_exact_not_merely_prefix(project_root: Path) -> None:
    assignment = _assignment(project_root)
    response = deepcopy(_valid_response(assignment))
    response["authored_cases"][0]["producer_file"]["content_lines"][-1] += " + LF"
    with pytest.raises(PilotAuthorRecordError, match="exact final writer"):
        normalize_v3_author_response(response, assignment)
