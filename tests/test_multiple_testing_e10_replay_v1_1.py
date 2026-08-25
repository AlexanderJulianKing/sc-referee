from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.method_contract_run import run_method_contract

_CHECK_ID = "check:authorized-complete-family-correction-over-code-test-battery"
_ROOT = Path("evaluation/development/blind-envelope-10-2026-08-24")


@pytest.mark.parametrize(
    ("case_id", "expected"),
    [
        ("ebbb8a5dbc2664257144", "authorized-reader-lineage-unavailable"),
        ("104493a5d99796a002c0", "test-battery-cardinality-unresolved"),
        ("3ff45fce2a45e0959fdb", "test-battery-cardinality-unresolved"),
        ("7296b0e2cf7faeefca64", "test-battery-cardinality-unresolved"),
        ("c51d08801b3d0ba4e532", "analysis-scope-structure-unsupported"),
        ("f4cf62caeb8ad68dc5b3", "analysis-scope-structure-unsupported"),
        ("cb2e207276a0dc3247bb", "helper-call-site-reentry-unsupported"),
        ("9be74afbe9659bd50580", "test-battery-cardinality-unresolved"),
        ("b787314c170f8f690060", "test-battery-cardinality-unresolved"),
        ("60f96fabb7129d662b23", "extra-registered-test-outside-authorized-family"),
        ("8d83210468ecde012e4a", "test-battery-cardinality-unresolved"),
        ("4907932548f745afe942", "authorized-family-test-census-incomplete"),
        ("6d2fdc67ab98bc0e0e6e", "statistics-api-imported-outside-analysis-py"),
        ("dfc9f20a94ecefc7f7b5", "analysis-scope-structure-unsupported"),
        ("e1bce32a32e3b2df475e", "test-battery-cardinality-unresolved"),
    ],
)
def test_opened_e10_public_adapter_oracle_and_replay(
    case_id: str, expected: str, schema_root: Path, tmp_path: Path
) -> None:
    source_case = _ROOT / "cases" / case_id
    project = tmp_path / "project"
    shutil.copytree(source_case / "project", project)
    (project / "auditor-task.txt").write_bytes((source_case / "PROMPT.txt").read_bytes())
    profile: dict[str, Any] = json.loads(
        (source_case / "profile_1_2_0.json").read_text(encoding="utf-8")
    )
    material_path = profile["semantic_role_authority"]["authorized_test_family"][
        "material_input_path"
    ]
    contract = tmp_path / "contract"
    run_method_contract(
        project,
        "auditor-task.txt",
        contract,
        schema_root,
        profile=profile,
        actor_id="human:e10-replay",
        created_at="2026-08-25T00:00:00Z",
    )
    audit = tmp_path / "audit"
    bundle = run_audit(
        project,
        audit,
        schema_root,
        material_inputs=(material_path,),
        method_contract_lock=contract / "semantic.lock.json",
        scientific_check_lane="development",
    )
    lock = json.loads((audit / "semantic.lock.json").read_text(encoding="utf-8"))
    module = next(
        item
        for item in lock["scientific_check_registry"]["evaluation"]["modules"]
        if item["check_id"] == _CHECK_ID
    )
    assert module["state"] == "unsupported"
    assert module["observations"][0]["abstention_reason"] == expected
    assert [
        item
        for item in bundle["detector_results"]
        if item["detector_id"] == "detector:bounded-code-csv-multiple-testing-conflict"
    ] == []
    assert bundle["findings"] == []

    replayed = replay(audit / "semantic.lock.json", tmp_path / "replay", schema_root)
    replay_lock = json.loads(
        (tmp_path / "replay" / "semantic.lock.json").read_text(encoding="utf-8")
    )
    replay_module = next(
        item
        for item in replay_lock["scientific_check_registry"]["evaluation"]["modules"]
        if item["check_id"] == _CHECK_ID
    )
    assert canonical_json(replay_module) == canonical_json(module)
    assert replayed["findings"] == []


def test_historical_e10_artifact_anchor_is_immutable() -> None:
    expected = {
        "AUDIT_RESULTS.json": "sha256:6bfd70dda4d7977b1ad3e1729722179f03381714c7fef74e9781091752ca6b5b",
        "ROLE_MAP.json": "sha256:ced43841cb53e3527812e6dc5b4e361e635ca77fc7ca64129cae80d5c226c648",
        "ENVELOPE_MANIFEST.json": "sha256:a0223468c9ee76d07cb5717f975c4a0e34ec9c44ad64f674ea671c14f5020af2",
    }
    for name, digest in expected.items():
        assert sha256_digest((_ROOT / name).read_bytes()) == digest

    audit = json.loads((_ROOT / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
    for item in audit["cases"]:
        case = _ROOT / "cases" / item["case_id"]
        first = json.loads((case / "audit-run-1" / "semantic.lock.json").read_text())
        second = json.loads((case / "audit-run-2" / "semantic.lock.json").read_text())
        first_module = next(
            value
            for value in first["scientific_check_registry"]["evaluation"]["modules"]
            if value["check_id"] == _CHECK_ID
        )
        second_module = next(
            value
            for value in second["scientific_check_registry"]["evaluation"]["modules"]
            if value["check_id"] == _CHECK_ID
        )
        assert first_module["module_evaluation_digest"] == second_module["module_evaluation_digest"]
