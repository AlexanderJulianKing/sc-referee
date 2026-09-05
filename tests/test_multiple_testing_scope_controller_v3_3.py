from __future__ import annotations

import ast
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

import sc_referee.controller as controller_module
from sc_referee.controller import run_audit
from sc_referee.core.ids import canonical_json
from sc_referee.method_contract_run import run_method_contract
from sc_referee.multiple_testing_scope_attestations_v1 import (
    ATTESTATION_PROFILE,
    ATTESTATION_PROFILE_VERSION,
    CERTAINTY_BASIS,
    COMPLETE_OPTION,
)
from sc_referee.multiple_testing_scope_attestations_v3_3 import (
    apply_attestation as apply_attestation_v3_3,
)

_SCHEMAS = Path("reference/schemas-v0.21.0")
_CASE = Path("evaluation/development/blind-envelope-15-2026-08-29/cases/81980e878c1bc8cc216b")
_CHECK_ID = "check:authorized-complete-family-correction-over-code-test-battery"
_ORACLE_ROOT = Path(
    "evaluation/development/multitest-code-slice-v3_2/audit-fix-r1-oracle"
).resolve()
sys.path.insert(0, str(_ORACLE_ROOT))
try:
    from fixture_sources import attestation_fixture_sources
finally:
    sys.path.remove(str(_ORACLE_ROOT))
_ORACLE = json.loads((_ORACLE_ROOT / "EXPECTED_ROWS.json").read_text(encoding="utf-8"))
_ATTESTATION_ROWS = {row["fixture_name"]: row for row in _ORACLE["attestation_rows"]}


def _project_and_contract(tmp_path: Path, source: bytes) -> tuple[Path, Path, str]:
    project = tmp_path / "project"
    shutil.copytree(_CASE / "project", project)
    (project / "analysis.py").write_bytes(source)
    (project / "task.txt").write_bytes((_CASE / "PROMPT.txt").read_bytes())
    profile: dict[str, Any] = json.loads((_CASE / "profile_1_2_0.json").read_text(encoding="utf-8"))
    material_path = profile["semantic_role_authority"]["authorized_test_family"][
        "material_input_path"
    ]
    contract = tmp_path / "contract"
    run_method_contract(
        project,
        "task.txt",
        contract,
        _SCHEMAS,
        profile=profile,
        actor_id="human:mt32-controller-fixture",
        created_at="2026-08-29T00:00:00Z",
    )
    return project, contract, material_path


def _scope_question(bundle: dict[str, Any]) -> dict[str, Any]:
    matches = [
        item
        for item in bundle["material_questions"]
        if item.get("extensions", {}).get("x-question-purpose")
        == "multiple_testing_correction_scope"
    ]
    assert len(matches) == 1
    return matches[0]


def _mt_module(lock: dict[str, Any]) -> dict[str, Any]:
    return next(
        item
        for item in lock["scientific_check_registry"]["evaluation"]["modules"]
        if item["check_id"] == _CHECK_ID
    )


def _ast_span(node: ast.AST) -> dict[str, int]:
    assert hasattr(node, "lineno")
    return {
        "start_line": node.lineno,
        "start_column": node.col_offset + 1,
        "end_line": node.end_lineno or node.lineno,
        "end_column": (node.end_col_offset or node.col_offset + 1) + 1,
    }


def _factor_span(source: bytes, correction_span: dict[str, int]) -> dict[str, int]:
    roots = [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.expr) and _ast_span(node) == correction_span
    ]
    assert len(roots) == 1
    factors = [
        node
        for node in ast.walk(roots[0])
        if isinstance(node, ast.Name) and node.id == "FAMILY_SIZE"
    ]
    assert len(factors) == 1
    return _ast_span(factors[0])


def _answer_file(
    path: Path,
    question: dict[str, Any],
    *,
    source: bytes,
) -> None:
    extensions = question["extensions"]
    correction_span = extensions["x-source-span"]
    value = {
        "profile": ATTESTATION_PROFILE,
        "profile_version": ATTESTATION_PROFILE_VERSION,
        "answers": [
            {
                "question_id": question["question_id"],
                "source_snapshot_digest": extensions["x-source-snapshot-digest"],
                "analysis_content_digest": extensions["x-analysis-content-digest"],
                "question_evidence_digest": extensions["x-question-evidence-digest"],
                "authority_binding_digest": extensions["x-authority-binding-digest"],
                "answer": COMPLETE_OPTION,
                "respondent": {
                    "actor_kind": "human",
                    "actor_id": "human:mt32-controller-fixture",
                },
                "certainty": {"level": "explicit", "basis": CERTAINTY_BASIS},
                "timestamp_status": "unavailable",
                "supersedes_answer_digest": None,
                "claimed_correction": {
                    "path": "analysis.py",
                    "analysis_content_digest": extensions["x-analysis-content-digest"],
                    "source_span": correction_span,
                    "factor": {
                        "kind": "contract_family_size",
                        "value": extensions["x-authorized-count"],
                        "source_span": _factor_span(source, correction_span),
                    },
                },
            }
        ],
    }
    path.write_text(canonical_json(value), encoding="utf-8")


def test_controller_reaches_v3_3_ap_failure_without_clearance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "controller-answer-b-fails-ap-raw-consumer"
    row = _ATTESTATION_ROWS[name]
    _, source = attestation_fixture_sources()[name]
    assert "sha256:" + hashlib.sha256(source).hexdigest() == row["fixture_source_sha256"]
    project, contract, material_path = _project_and_contract(tmp_path, source)

    base_output = tmp_path / "audit-no-answer"
    base = run_audit(
        project,
        base_output,
        _SCHEMAS,
        material_inputs=(material_path,),
        method_contract_lock=contract / "semantic.lock.json",
        scientific_check_lane="development",
    )
    question = _scope_question(base)
    assert question["status"] == "open"
    base_lock = json.loads((base_output / "semantic.lock.json").read_text(encoding="utf-8"))
    assert _mt_module(base_lock)["observations"][0]["abstention_reason"] == (
        "unresolved-manual-correction-present"
    )

    attestation = tmp_path / "answer-complete.json"
    _answer_file(attestation, question, source=source)
    calls: list[dict[str, Any]] = []
    # This is the frozen-3.3 replay path. The development controller advances
    # independently; route this historical assertion through the frozen implementation.

    def observed_v3_3_call(*args: Any, **kwargs: Any) -> Any:
        calls.append(kwargs)
        return apply_attestation_v3_3(*args, **kwargs)

    monkeypatch.setattr(controller_module, "apply_attestation", observed_v3_3_call)
    answered_output = tmp_path / "audit-with-answer"
    answered = run_audit(
        project,
        answered_output,
        _SCHEMAS,
        material_inputs=(material_path,),
        method_contract_lock=contract / "semantic.lock.json",
        scientific_check_lane="development",
        attestations=attestation,
    )
    assert len(calls) == 1
    assert calls[0]["ap_context"] is not None

    answered_question = _scope_question(answered)
    # Mutation-kill: the auditor's failed-proof-to-complete mutation makes this assertion fail by
    # closing the question (or makes the paired-equivalence receipt assertion below false).
    assert answered_question["status"] == row["expected_question_status"] == "open"
    assert answered["findings"] == []
    assert answered["detector_evaluation_candidates"] == []
    matching_disclosures = [
        item
        for item in answered["disclosures"]
        if item.get("extensions", {}).get("x-question-purpose")
        == "multiple_testing_correction_scope"
    ]
    assert bool(matching_disclosures) is row["expected_disclosure"] is True
    assert all(item["non_accusatory"] is True for item in matching_disclosures)

    answered_lock = json.loads((answered_output / "semantic.lock.json").read_text(encoding="utf-8"))
    proof = answered_lock["multiple_testing_attestation"]["application"]["guided_proof"]
    assert proof["status"] == row["expected_proof_status"] == "unverified"
    assert proof["corrected_positions"] == row["expected_corrected_positions"] == []
    assert proof["answer_removal_equivalent"] is row["expected_answer_removal_equivalent"] is True
    assert canonical_json(_mt_module(answered_lock)) == canonical_json(_mt_module(base_lock))
