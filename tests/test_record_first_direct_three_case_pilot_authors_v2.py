from __future__ import annotations

from pathlib import Path

import pytest

from scripts.build_first_direct_three_case_pilot_authoring_v2 import (
    build_first_direct_three_case_pilot_authoring_v2,
)
from scripts.record_first_direct_three_case_pilot_authors import PilotAuthorRecordError
from scripts.record_first_direct_three_case_pilot_authors_v2 import (
    _validate_static_case,
    normalize_line_author_response,
)


def _valid_line_case(case_id: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "input_file": {
            "relative_path": "inputs/stations.csv",
            "content_lines": ["scheduled,eligible,events", "96,72,18"],
        },
        "producer_file": {
            "relative_path": "workflow/analysis.py",
            "content_lines": [
                "from pathlib import Path",
                "SOURCE_TEXT = Path('inputs/stations.csv').read_text()",
                "SOURCE_LINES = SOURCE_TEXT.splitlines()",
                "SOURCE_LINE_COUNT = len(SOURCE_LINES)",
                (
                    "REPORT_TEXT = f'Input lines including header: {SOURCE_LINE_COUNT}\\n"
                    "[selected-result] target=all; events=18; exposure=72; rate=0.25\\n'"
                ),
                "Path('results/report.md').write_text(REPORT_TEXT)",
            ],
        },
        "report_file": {
            "relative_path": "results/report.md",
            "content_lines": [
                "Input lines including header: 2",
                "[selected-result] target=all; events=18; exposure=72; rate=0.25",
            ],
        },
        "author_declaration": {
            "declaration_state": "one_selected_result",
            "selected_result_projection": {
                "result_span": {"start_line": 2, "end_line": 2},
                "producer_span": {"start_line": 6, "end_line": 6},
            },
            "candidate_result_spans": [],
            "unsupported_producer_spans": [],
        },
    }


def _assignment(project_root: Path) -> dict[str, object]:
    return build_first_direct_three_case_pilot_authoring_v2(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]["author_assignments"][1]


def test_line_array_response_normalizes_to_exact_lf_files(project_root: Path) -> None:
    assignment = _assignment(project_root)
    case = _valid_line_case(assignment["case_ids"][0])
    response = {
        "author_participant_id": assignment["participant"]["participant_id"],
        "authored_cases": [case],
    }
    normalized = normalize_line_author_response(response, assignment)
    assert normalized[0]["input_file"]["content"].endswith("\n")
    assert normalized[0]["producer_file"]["content"].splitlines()[-1] == (
        "Path('results/report.md').write_text(REPORT_TEXT)"
    )
    assert normalized[0]["report_file"]["content"].count("[selected-result]") == 1


def test_line_array_response_rejects_embedded_terminators(project_root: Path) -> None:
    assignment = _assignment(project_root)
    case = _valid_line_case(assignment["case_ids"][0])
    case["report_file"]["content_lines"][0] = "bad\nline"
    response = {
        "author_participant_id": assignment["participant"]["participant_id"],
        "authored_cases": [case],
    }
    with pytest.raises(PilotAuthorRecordError, match="without terminators"):
        normalize_line_author_response(response, assignment)


def test_static_intake_accepts_exact_supported_writer(project_root: Path) -> None:
    assignment = _assignment(project_root)
    case = _valid_line_case(assignment["case_ids"][0])
    response = {
        "author_participant_id": assignment["participant"]["participant_id"],
        "authored_cases": [case],
    }
    normalized = normalize_line_author_response(response, assignment)[0]
    frozen = _validate_static_case(
        normalized,
        participant=assignment["participant"],
        authored_at="2026-08-05T02:30:00Z",
        schedule={
            "author_frozen_at": "2026-08-05T02:31:00Z",
            "coordinated_at": "2026-08-05T02:31:01Z",
            "contract_frozen_at": "2026-08-05T02:31:02Z",
            "derived_at": "2026-08-05T02:31:03Z",
            "derivation_frozen_at": "2026-08-05T02:31:04Z",
            "declaration_revealed_at": "2026-08-05T02:31:05Z",
            "compared_at": "2026-08-05T02:31:06Z",
        },
        validator_identity={
            "validator_id": "actor:selected-result-validator-01",
            "provider": "Local deterministic software",
            "execution_context_id": "context:selected-result-validator-v2",
            "identity_evidence_digest": "sha256:" + "a" * 64,
        },
        envelope={
            "envelope_id": "relation-envelope:complete-domain-exposure-denominator",
            "check_id": "check:complete-domain-exposure-denominator",
            "candidate_id": "complete-declared-domain-exposure",
            "binding_digest": "sha256:" + "b" * 64,
        },
    )
    assert frozen["derivation"]["derivation_status"] == "one_selected_result_rederived"
    assert frozen["validation"]["status"] == "verified_complete"


def test_static_intake_rejects_writer_keyword_arguments(project_root: Path) -> None:
    assignment = _assignment(project_root)
    case = _valid_line_case(assignment["case_ids"][0])
    case["producer_file"]["content_lines"][-1] = (
        "Path('results/report.md').write_text(REPORT_TEXT, encoding='ascii')"
    )
    response = {
        "author_participant_id": assignment["participant"]["participant_id"],
        "authored_cases": [case],
    }
    normalized = normalize_line_author_response(response, assignment)[0]
    with pytest.raises(PilotAuthorRecordError, match="unsupported_structure"):
        _validate_static_case(
            normalized,
            participant=assignment["participant"],
            authored_at="2026-08-05T02:30:00Z",
            schedule={
                "author_frozen_at": "2026-08-05T02:31:00Z",
                "coordinated_at": "2026-08-05T02:31:01Z",
                "contract_frozen_at": "2026-08-05T02:31:02Z",
                "derived_at": "2026-08-05T02:31:03Z",
                "derivation_frozen_at": "2026-08-05T02:31:04Z",
                "declaration_revealed_at": "2026-08-05T02:31:05Z",
                "compared_at": "2026-08-05T02:31:06Z",
            },
            validator_identity={
                "validator_id": "actor:selected-result-validator-01",
                "provider": "Local deterministic software",
                "execution_context_id": "context:selected-result-validator-v2",
                "identity_evidence_digest": "sha256:" + "a" * 64,
            },
            envelope={
                "envelope_id": "relation-envelope:complete-domain-exposure-denominator",
                "check_id": "check:complete-domain-exposure-denominator",
                "candidate_id": "complete-declared-domain-exposure",
                "binding_digest": "sha256:" + "b" * 64,
            },
        )
