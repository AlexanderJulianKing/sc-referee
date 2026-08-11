from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.record_first_direct_three_case_stage1_reviews as stage1_recorder
from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_three_case_stage1_codex_recovery import (
    AMENDMENT_NAME,
    FAILURE_LEDGER_DIGEST,
    SOURCE_COMMIT,
    build_stage1_codex_transport_recovery_amendment,
)
from scripts.build_first_direct_three_case_stage1_protocol import REVIEW_RELATIVE
from scripts.record_first_direct_three_case_stage1_reviews import (
    PROTOCOL_DIGEST,
    validate_stage1_call_capture,
)
from scripts.run_first_direct_three_case_stage1_codex import _codex_argv


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_codex_recovery_amendment_changes_transport_only(project_root: Path) -> None:
    amendment = build_stage1_codex_transport_recovery_amendment(project_root)
    assert amendment["source_commit"] == SOURCE_COMMIT
    assert amendment["protocol_digest"] == PROTOCOL_DIGEST
    assert amendment["retained_failure_ledger_digest"] == FAILURE_LEDGER_DIGEST
    assert amendment["eligibility_basis"] == {
        "failed_attempt_count": 2,
        "model_inference_started_count": 0,
        "reviewer_response_count": 0,
        "review_admitted_count": 0,
        "failure_reason_code": "api_rejected_unsupported_allof_keyword",
    }
    assert all(amendment["semantic_invariants"].values()) is False
    assert amendment["semantic_invariants"]["prompt_bytes_unchanged"] is True
    assert amendment["semantic_invariants"]["semantic_output_schema_unchanged"] is True
    assert amendment["semantic_invariants"]["controller_semantic_repair_permitted"] is False
    assert amendment["semantic_invariants"]["scientific_content_changed"] is False
    assert amendment["transport_delta"]["api_output_schema_argument_present"] is False
    assert len(amendment["recovery_calls"]) == 2
    assert len({item["transport_attempt_identity_id"] for item in amendment["recovery_calls"]}) == 2
    assert len({item["fresh_transport_context_id"] for item in amendment["recovery_calls"]}) == 2
    assert amendment["amendment_digest"] == semantic_digest(
        {key: value for key, value in amendment.items() if key != "amendment_digest"}
    )


def test_recovery_cli_omits_only_api_output_schema_argument(project_root: Path) -> None:
    protocol = _load(project_root / REVIEW_RELATIVE / "STAGE1_REVIEW_PROTOCOL.json")
    call = next(
        item for item in protocol["calls"] if item["participant_id"] == "actor:stage1-codex-01"
    )
    working = Path("/tmp/fresh-stage1-context")
    schema_path = working / "schema.json"
    final_path = working / "response.json"
    original = _codex_argv(
        call,
        "base",
        working,
        schema_path,
        final_path,
        enforce_output_schema=True,
    )
    recovery = _codex_argv(
        call,
        "base",
        working,
        schema_path,
        final_path,
        enforce_output_schema=False,
    )
    output_index = original.index("--output-schema")
    assert original[:output_index] + original[output_index + 2 :] == recovery
    assert "--output-schema" not in recovery
    assert recovery[-1] == call["prompt"]


def test_frozen_recovery_amendment_replays_and_is_write_once(project_root: Path) -> None:
    path = project_root / REVIEW_RELATIVE / AMENDMENT_NAME
    if not path.exists():
        pytest.skip("Generated amendment is checked after its prospective freeze.")
    frozen = _load(path)
    supplied = frozen.pop("amendment_digest")
    assert supplied == semantic_digest(frozen)
    generated = build_stage1_codex_transport_recovery_amendment(project_root)
    assert generated == {**frozen, "amendment_digest": supplied}
    assert sha256_digest(path.read_bytes()).startswith("sha256:")


@pytest.mark.parametrize(
    "participant_slug,expected_ledger_digest",
    [
        (
            "stage1-codex-01",
            "sha256:0acf3d7435637cabb4dbd3e74d47664f34cc10973293f57488acd5b4673e0a25",
        ),
        (
            "stage1-codex-02",
            "sha256:d53bad1d4e09a29b7b6fafbbecb5581b5b479cb756f42a1b6164e4aa05c0463f",
        ),
    ],
)
def test_retained_codex_recovery_reviews_replay_under_unchanged_local_validator(
    project_root: Path,
    participant_slug: str,
    expected_ledger_digest: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(stage1_recorder, "SCHEMA_RELATIVE", Path("reference/schemas-v0.19.0"))
    root = project_root / REVIEW_RELATIVE
    incoming = _load(root / "incoming" / f"{participant_slug}.json")
    reviews = validate_stage1_call_capture(project_root, incoming)
    assert len(reviews) == 3
    assert {review["case_id"] for review in reviews} == {
        "case:2e26bf5ece15be03717f",
        "case:35069763f06891dba5a3",
        "case:b036fd64c647dfd93e35",
    }
    assert [review["verdict"] for review in reviews].count("demonstrated_issue") == 1
    ledger = _load(root / "stage1-call-ledgers" / f"{participant_slug}.json")
    supplied = ledger.pop("ledger_digest")
    assert supplied == expected_ledger_digest == semantic_digest(ledger)
    assert ledger["review_count"] == 3
    assert ledger["scientific_label_count"] == 0
    assert ledger["detector_outcome_count"] == 0
