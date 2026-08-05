from __future__ import annotations

import json
from pathlib import Path

import pytest
from sc_referee_evaluation.authoring_render_grammar import validate_render_only_producer
from sc_referee_evaluation.prospective_selected_result_verifier import (
    validate_selected_result_validation,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_three_case_pilot_authoring_v4 import (
    PILOT_AUTHORING_V4_RELATIVE,
)
from scripts.record_first_direct_three_case_pilot_authors_v4 import (
    record_first_direct_three_case_pilot_authors_v4,
    validate_v4_author_attempt,
)

EXPECTED_LEDGER_DIGEST = "sha256:6487d1b7cccfb1fdb90fc080b93ea84233b3f81543d17e7ac3a99f30f3270ebc"
EXPECTED_CAPTURE_DIGESTS = {
    "actor:pilot-author-claude-04": (
        "sha256:cb5081820c7700e5bb67af1c5cf280a29f6f775dd24c1629c7183b49a414f50f"
    ),
    "actor:pilot-author-codex-04": (
        "sha256:411c474f2cd0ff2409bc94a73a816ce2e49e613f919457288f31e0702ea51492"
    ),
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _root(project_root: Path) -> Path:
    return project_root / PILOT_AUTHORING_V4_RELATIVE


def test_v4_admission_ledger_is_exact_complete_and_authority_free(project_root: Path) -> None:
    ledger = _load(_root(project_root) / "AUTHORING_LEDGER.json")
    assert ledger["ledger_digest"] == EXPECTED_LEDGER_DIGEST
    assert ledger["ledger_digest"] == semantic_digest(
        {key: value for key, value in ledger.items() if key != "ledger_digest"}
    )
    assert ledger["summary"] == {
        "admitted_attempt_count": 2,
        "assigned_author_context_count": 2,
        "author_declaration_count": 3,
        "authored_case_count": 3,
        "detector_outcome_count": 0,
        "metric_eligible_case_count": 3,
        "model_attempt_count": 2,
        "render_grammar_valid_case_count": 3,
        "scientific_label_count": 0,
        "verified_selected_result_count": 3,
    }
    assert ledger["qualification_authority"] == "none_authoring_ledger_only"
    assert {entry["participant_id"] for entry in ledger["entries"]} == set(EXPECTED_CAPTURE_DIGESTS)
    assert all(entry["replacement_count"] == 0 for entry in ledger["entries"])
    assert all(
        entry["attempt_status"] == "admitted_after_frozen_render_and_static_intake"
        for entry in ledger["entries"]
    )


def test_v4_captures_replay_to_exact_materialized_case_bytes(project_root: Path) -> None:
    root = _root(project_root)
    protocol = _load(root / "PILOT_AUTHORING_PROTOCOL.json")
    normalized_by_case = {}
    for assignment in protocol["author_assignments"]:
        participant_id = assignment["participant"]["participant_id"]
        capture_path = root / "incoming" / f"{participant_id.removeprefix('actor:')}.json"
        assert sha256_digest(capture_path.read_bytes()) == EXPECTED_CAPTURE_DIGESTS[participant_id]
        attempt = _load(capture_path)
        assert attempt["replacement_count"] == 0
        for case in validate_v4_author_attempt(attempt, assignment):
            normalized_by_case[case["case_id"]] = case

    assert len(normalized_by_case) == 3
    for case_id, case in normalized_by_case.items():
        case_root = root / "cases" / case_id.removeprefix("case:")
        for role in ("input_file", "producer_file", "report_file"):
            record = case[role]
            assert (case_root / record["relative_path"]).read_text(encoding="ascii") == record[
                "content"
            ]


def test_v4_case_evidence_and_selected_result_validations_replay(project_root: Path) -> None:
    root = _root(project_root)
    ledger = _load(root / "AUTHORING_LEDGER.json")
    records = {
        record["case_id"]: record for entry in ledger["entries"] for record in entry["case_records"]
    }
    assert len(records) == 3
    for case_id, record in records.items():
        suffix = case_id.removeprefix("case:")
        case_root = root / "cases" / suffix
        declaration = _load(root / "author-declarations" / f"{suffix}.json")
        manifest = _load(root / "case-manifests" / f"{suffix}.json")
        contract = _load(root / "case-contracts" / f"{suffix}.json")
        derivation = _load(root / "selected-result-derivations" / f"{suffix}.json")
        validation = _load(root / "selected-result-validations" / f"{suffix}.json")

        assert declaration["declaration_digest"] == record["author_declaration_digest"]
        assert declaration["declaration_digest"] == semantic_digest(
            {key: value for key, value in declaration.items() if key != "declaration_digest"}
        )
        assert manifest["manifest_digest"] == record["case_manifest_digest"]
        assert manifest["manifest_digest"] == semantic_digest(
            {key: value for key, value in manifest.items() if key != "manifest_digest"}
        )
        assert contract["contract_digest"] == record["case_contract_digest"]
        assert derivation["derivation_digest"] == record["derivation_digest"]
        assert derivation["derivation_status"] == "one_selected_result_rederived"
        assert derivation["project_code_executed"] is False
        binding = derivation["candidate_bindings"]
        assert len(binding) == 1
        assert binding[0]["alternative_producer_locators"] == []
        assert [item["source_locator"]["path"] for item in binding[0]["source_operands"]] == [
            "inputs/data.csv"
        ]
        assert validation["validation_digest"] == record["validation_digest"]
        assert validation["status"] == "verified_complete"
        assert (
            validate_selected_result_validation(
                validation,
                case_root=case_root,
                case_contract=contract,
            )
            == validation
        )

        producer = (case_root / "workflow" / "analysis.py").read_text(encoding="ascii")
        grammar = validate_render_only_producer(producer.splitlines())
        assert grammar["validation_digest"] == record["render_grammar_validation_digest"]
        assert producer.splitlines()[-1] == ("Path('results/report.md').write_text(REPORT_TEXT)")
        report_lines = (
            (case_root / "results" / "report.md").read_text(encoding="ascii").splitlines()
        )
        assert sum(line.strip().startswith("[selected-result]") for line in report_lines) == 1


def test_v4_admission_is_immutable_and_contains_no_label_or_detector_artifact(
    project_root: Path,
) -> None:
    root = _root(project_root)
    assert {path.name for path in root.iterdir()} == {
        "AUTHORING_LEDGER.json",
        "PILOT_AUTHORING_PROTOCOL.json",
        "PILOT_AUTHORING_RESTART_AMENDMENT.json",
        "author-declarations",
        "case-contracts",
        "case-manifests",
        "cases",
        "incoming",
        "selected-result-derivations",
        "selected-result-validations",
    }
    before = {
        path.relative_to(root).as_posix(): sha256_digest(path.read_bytes())
        for path in root.rglob("*")
        if path.is_file()
    }
    with pytest.raises(FileExistsError, match="replace retained v4 authoring evidence"):
        record_first_direct_three_case_pilot_authors_v4(
            project_root, frozen_at="2026-08-05T05:50:00Z"
        )
    after = {
        path.relative_to(root).as_posix(): sha256_digest(path.read_bytes())
        for path in root.rglob("*")
        if path.is_file()
    }
    assert after == before
