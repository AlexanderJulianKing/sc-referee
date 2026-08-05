from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.build_first_direct_three_case_pilot_authoring_v4 import (
    PILOT_AUTHORING_V4_RELATIVE,
    build_first_direct_three_case_pilot_authoring_v4,
)
from scripts.record_first_direct_three_case_pilot_authors import PilotAuthorRecordError
from scripts.record_first_direct_three_case_pilot_authors_v2 import _validate_static_case
from scripts.record_first_direct_three_case_pilot_authors_v4 import (
    PROTOCOL_DIGEST,
    RESTART_AMENDMENT_DIGEST,
    normalize_v4_author_response,
    validate_v4_author_attempt,
)


def _assignment(project_root: Path) -> dict:
    protocol = build_first_direct_three_case_pilot_authoring_v4(project_root)[
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
                        "EVENTS = 18",
                        "EXPOSURE = 72",
                        (
                            "RESULT_LINE = f'[selected-result] Input lines including header: "
                            "{SOURCE_LINE_COUNT}; target=signal-eligible; events={EVENTS}; "
                            "exposure={EXPOSURE}.' + LF"
                        ),
                        "REPORT_TEXT = RESULT_LINE",
                        "Path('results/report.md').write_text(REPORT_TEXT)",
                    ],
                },
                "report_file": {
                    "relative_path": "results/report.md",
                    "content_lines": [
                        "[selected-result] Input lines including header: 2; "
                        "target=signal-eligible; events=18; exposure=72."
                    ],
                },
                "author_declaration": {
                    "declaration_state": "one_selected_result",
                    "selected_result_projection": {
                        "result_span": {"start_line": 1, "end_line": 1},
                        "producer_span": {"start_line": 10, "end_line": 10},
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
        "authored_at": "2026-08-05T05:40:00Z",
        "schedule": {
            "author_frozen_at": "2026-08-05T05:41:00Z",
            "coordinated_at": "2026-08-05T05:41:01Z",
            "contract_frozen_at": "2026-08-05T05:41:02Z",
            "derived_at": "2026-08-05T05:41:03Z",
            "derivation_frozen_at": "2026-08-05T05:41:04Z",
            "declaration_revealed_at": "2026-08-05T05:41:05Z",
            "compared_at": "2026-08-05T05:41:06Z",
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


def test_v4_protocol_constants_match_generated_freeze(project_root: Path) -> None:
    root = project_root / PILOT_AUTHORING_V4_RELATIVE
    amendment = json.loads(
        (root / "PILOT_AUTHORING_RESTART_AMENDMENT.json").read_text(encoding="utf-8")
    )
    protocol = json.loads((root / "PILOT_AUTHORING_PROTOCOL.json").read_text(encoding="utf-8"))
    assert amendment["amendment_digest"] == RESTART_AMENDMENT_DIGEST
    assert protocol["protocol_digest"] == PROTOCOL_DIGEST


def test_v4_render_fixture_normalizes_and_replays_verified_complete(
    project_root: Path,
) -> None:
    assignment = _assignment(project_root)
    normalized = normalize_v4_author_response(_valid_response(assignment), assignment)
    frozen = _validate_static_case(normalized[0], **_static_arguments(assignment))
    assert frozen["derivation"]["derivation_status"] == "one_selected_result_rederived"
    assert frozen["validation"]["status"] == "verified_complete"


@pytest.mark.parametrize(
    "replacement",
    [
        "EVENTS = SOURCE_LINES[1][-1]",
        "EVENTS = int('18')",
        "EVENTS = SOURCE_TEXT.strip()",
        "EVENTS = -18",
    ],
)
def test_v4_rejects_post_prefix_parsing_even_when_python_is_valid(
    project_root: Path, replacement: str
) -> None:
    assignment = _assignment(project_root)
    response = _valid_response(assignment)
    response["authored_cases"][0]["producer_file"]["content_lines"][5] = replacement
    with pytest.raises(PilotAuthorRecordError, match="V4 render grammar failed"):
        normalize_v4_author_response(response, assignment)


def test_v4_rejects_wrong_path_reverse_solidus_and_nonfinal_span(project_root: Path) -> None:
    assignment = _assignment(project_root)
    wrong_path = deepcopy(_valid_response(assignment))
    wrong_path["authored_cases"][0]["producer_file"]["relative_path"] = "analysis.py"
    with pytest.raises(PilotAuthorRecordError, match="schema failed"):
        normalize_v4_author_response(wrong_path, assignment)

    reverse_solidus = deepcopy(_valid_response(assignment))
    reverse_solidus["authored_cases"][0]["producer_file"]["content_lines"][5] = "EVENTS = '1\\8'"
    with pytest.raises(PilotAuthorRecordError, match="schema failed"):
        normalize_v4_author_response(reverse_solidus, assignment)

    wrong_span = deepcopy(_valid_response(assignment))
    wrong_span["authored_cases"][0]["author_declaration"]["selected_result_projection"][
        "producer_span"
    ] = {"start_line": 9, "end_line": 9}
    with pytest.raises(PilotAuthorRecordError, match="exactly the final writer"):
        normalize_v4_author_response(wrong_span, assignment)


def test_v4_attempt_binding_is_exact(project_root: Path) -> None:
    assignment = _assignment(project_root)
    response = _valid_response(assignment)
    attempt = {
        "participant_id": assignment["participant"]["participant_id"],
        "call_identity_id": assignment["call_identity_id"],
        "protocol_digest": PROTOCOL_DIGEST,
        "configuration_digest": assignment["participant"]["configuration_digest"],
        "prompt_digest": assignment["prompt_digest"],
        "output_schema_digest": assignment["output_schema_digest"],
        "started_at": "2026-08-05T05:40:00Z",
        "completed_at": "2026-08-05T05:41:00Z",
        "exit_code": 0,
        "raw_response": json.dumps(response, sort_keys=True),
        "attempt_status": "response_retained",
        "replacement_count": 0,
    }
    assert len(validate_v4_author_attempt(attempt, assignment)) == 1
    attempt["prompt_digest"] = "sha256:" + "0" * 64
    with pytest.raises(PilotAuthorRecordError, match="prompt_digest does not match"):
        validate_v4_author_attempt(attempt, assignment)
