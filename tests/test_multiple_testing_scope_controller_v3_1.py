from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json
from sc_referee.method_contract_run import run_method_contract
from sc_referee.multiple_testing_scope_attestations_v1 import (
    ATTESTATION_PROFILE,
    ATTESTATION_PROFILE_VERSION,
    CERTAINTY_BASIS,
    COMPLETE_OPTION,
    INCOMPLETE_OPTION,
    MultipleTestingAttestationError,
)

_SCHEMAS = Path("reference/schemas-v0.21.0")
_CASE = Path("evaluation/development/blind-envelope-13-2026-08-26/cases/b7d38f6e9284abfd3ee6")
_CHECK_ID = "check:authorized-complete-family-correction-over-code-test-battery"
_ATTESTATION_ORACLE = json.loads(
    Path("evaluation/development/multitest-code-slice-v3_1/ATTESTATION_ORACLE.json").read_text(
        encoding="utf-8"
    )
)


def _project_and_contract(tmp_path: Path) -> tuple[Path, Path, str]:
    project = tmp_path / "project"
    shutil.copytree(_CASE / "project", project)
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
        actor_id="human:mt31-controller-fixture",
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


def _answer_file(
    path: Path,
    question: dict[str, Any],
    *,
    option: str,
    claim_span: dict[str, int] | None = None,
    factor_kind: str = "correction_input_count",
    factor_value: int | None = None,
    factor_span: dict[str, int] | None = None,
) -> None:
    extensions = question["extensions"]
    claim = None
    if option == COMPLETE_OPTION:
        span = claim_span or extensions["x-source-span"]
        claim = {
            "path": "analysis.py",
            "analysis_content_digest": extensions["x-analysis-content-digest"],
            "source_span": span,
            "factor": {
                "kind": factor_kind,
                "value": (
                    factor_value if factor_value is not None else extensions["x-authorized-count"]
                ),
                "source_span": factor_span or span,
            },
        }
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
                "answer": option,
                "respondent": {
                    "actor_kind": "human",
                    "actor_id": "human:mt31-controller-fixture",
                },
                "certainty": {"level": "explicit", "basis": CERTAINTY_BASIS},
                "timestamp_status": "unavailable",
                "supersedes_answer_digest": None,
                "claimed_correction": claim,
            }
        ],
    }
    path.write_text(canonical_json(value), encoding="utf-8")


def _ast_span(source: str, node: ast.AST) -> dict[str, int]:
    positioned = node
    assert hasattr(positioned, "lineno")
    return {
        "start_line": positioned.lineno,
        "start_column": positioned.col_offset + 1,
        "end_line": positioned.end_lineno,
        "end_column": positioned.end_col_offset + 1,
    }


def _family_size_pointer(source: str) -> dict[str, int]:
    tree = ast.parse(source, filename="analysis.py", mode="exec", type_comments=True)
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "len"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "OUTCOMES"
    ]
    assert matches
    return _ast_span(source, matches[0])


def test_controller_adds_question_then_applies_b_without_changing_source_row(
    tmp_path: Path,
) -> None:
    project, contract, material_path = _project_and_contract(tmp_path)
    first_output = tmp_path / "audit-no-answer"
    first = run_audit(
        project,
        first_output,
        _SCHEMAS,
        material_inputs=(material_path,),
        method_contract_lock=contract / "semantic.lock.json",
        scientific_check_lane="development",
    )
    first_lock = json.loads((first_output / "semantic.lock.json").read_text(encoding="utf-8"))
    question = _scope_question(first)
    assert question["status"] == "open"
    assert len(first["conditional_concerns"]) == 1
    assert first["answers"] == []
    assert first["findings"] == []
    assert _mt_module(first_lock)["state"] == "unsupported"
    assert _mt_module(first_lock)["observations"][0]["abstention_reason"] == (
        "correction-family-lineage-unresolved"
    )

    attestation = tmp_path / "answer-complete.json"
    _answer_file(attestation, question, option=COMPLETE_OPTION)
    second_output = tmp_path / "audit-with-answer"
    second = run_audit(
        project,
        second_output,
        _SCHEMAS,
        material_inputs=(material_path,),
        method_contract_lock=contract / "semantic.lock.json",
        scientific_check_lane="development",
        attestations=attestation,
    )
    second_lock = json.loads((second_output / "semantic.lock.json").read_text(encoding="utf-8"))
    answered = _scope_question(second)
    assert answered["status"] == "answered"
    assert len(second["answers"]) == 1
    assert second["conditional_concerns"] == []
    assert [item["disclosure_kind"] for item in second["disclosures"]] == [
        item["disclosure_kind"] for item in first["disclosures"]
    ]
    assert not any(
        item.get("extensions", {}).get("x-question-purpose") == "multiple_testing_correction_scope"
        for item in second["disclosures"]
    )
    assert second["findings"] == []
    assert canonical_json(_mt_module(second_lock)) == canonical_json(_mt_module(first_lock))
    receipt = second_lock["multiple_testing_attestation"]["application"]
    assert receipt["guided_proof"] == {
        "status": "complete",
        "corrected_positions": [0, 1, 2, 3, 4],
        "proof_root_span": {
            "start_line": 79,
            "start_column": 39,
            "end_line": 79,
            "end_column": 66,
        },
        "proof_digest": receipt["guided_proof"]["proof_digest"],
        "failure_code": None,
        "answer_removal_equivalent": True,
    }
    assert receipt["source_classification_changed"] is False

    replay_output = tmp_path / "attested-replay"
    replayed = replay(second_output / "semantic.lock.json", replay_output, _SCHEMAS)
    assert canonical_json(replayed["material_questions"]) == canonical_json(
        second["material_questions"]
    )
    assert canonical_json(replayed["answers"]) == canonical_json(second["answers"])
    assert canonical_json(replayed["conditional_concerns"]) == canonical_json(
        second["conditional_concerns"]
    )
    assert canonical_json(replayed["disclosures"]) == canonical_json(second["disclosures"])
    assert replayed["findings"] == []
    assert canonical_json(replayed["storage_manifests"]) == canonical_json(
        second["storage_manifests"]
    )
    assert (replay_output / "semantic.lock.json").read_bytes() == (
        second_output / "semantic.lock.json"
    ).read_bytes()
    assert (replay_output / "observed/inputs/multiple-testing-attestations.json").read_bytes() == (
        second_output / "observed/inputs/multiple-testing-attestations.json"
    ).read_bytes()


def test_all_fifteen_attested_bundles_replay_byte_identically(
    tmp_path: Path,
) -> None:
    assert len(_ATTESTATION_ORACLE["rows"]) == 15
    project, contract, material_path = _project_and_contract(tmp_path)
    source = (project / "analysis.py").read_text(encoding="utf-8")
    family_size_span = _family_size_pointer(source)
    base_output = tmp_path / "fifteen-base"
    base = run_audit(
        project,
        base_output,
        _SCHEMAS,
        material_inputs=(material_path,),
        method_contract_lock=contract / "semantic.lock.json",
        scientific_check_lane="development",
    )
    question = _scope_question(base)

    for index, row in enumerate(_ATTESTATION_ORACLE["rows"]):
        route = row["route"]
        if route is None:
            output = base_output
            bundle = base
        else:
            answer_path = tmp_path / f"fifteen-answer-{index}.json"
            claim_span = None
            factor_kind = "correction_input_count"
            factor_span = None
            if route == COMPLETE_OPTION and row["proof_status"] == "unverified":
                claim_span = family_size_span
                factor_kind = "contract_family_size"
                factor_span = family_size_span
            _answer_file(
                answer_path,
                question,
                option=route,
                claim_span=claim_span,
                factor_kind=factor_kind,
                factor_span=factor_span,
            )
            output = tmp_path / f"fifteen-audit-{index}"
            bundle = run_audit(
                project,
                output,
                _SCHEMAS,
                material_inputs=(material_path,),
                method_contract_lock=contract / "semantic.lock.json",
                scientific_check_lane="development",
                attestations=answer_path,
            )

        current_question = _scope_question(bundle)
        assert current_question["status"] == row["question_status"], row["name"]
        matching_disclosures = [
            item
            for item in bundle["disclosures"]
            if item.get("extensions", {}).get("x-question-purpose")
            == "multiple_testing_correction_scope"
        ]
        assert bool(matching_disclosures) is row["disclosure"], row["name"]
        assert current_question["record_type"] == "material_question"
        assert all(item["record_type"] == "answer" for item in bundle["answers"])
        assert all(
            item["record_type"] == "conditional_concern" for item in bundle["conditional_concerns"]
        )
        assert all(item["record_type"] == "disclosure" for item in matching_disclosures)
        assert bundle["findings"] == []
        assert bundle["detector_evaluation_candidates"] == []
        assert bundle["detector_case_outcomes"] == []
        assert bundle["detector_qualifications"] == []
        assert bundle["qualification_metric_sets"] == []
        if route is not None:
            assert len(bundle["answers"]) == 1, row["name"]
            lock = json.loads((output / "semantic.lock.json").read_text(encoding="utf-8"))
            receipt = lock["multiple_testing_attestation"]["application"]
            proof = receipt["guided_proof"]
            assert (proof["status"] if proof is not None else None) == row["proof_status"]
            if proof is not None and proof["status"] == "complete":
                assert proof["answer_removal_equivalent"] is True

        replay_output = tmp_path / f"fifteen-replay-{index}"
        replayed = replay(output / "semantic.lock.json", replay_output, _SCHEMAS)
        assert canonical_json(replayed) == canonical_json(bundle), row["name"]
        assert canonical_json(replayed["storage_manifests"]) == canonical_json(
            bundle["storage_manifests"]
        ), row["name"]
        for relative in ("semantic.lock.json", "audit.bundle.json", "report.html"):
            assert (replay_output / relative).read_bytes() == (output / relative).read_bytes(), (
                row["name"],
                relative,
            )


def test_a_path_and_invalid_binding_are_all_or_nothing(tmp_path: Path) -> None:
    project, contract, material_path = _project_and_contract(tmp_path)
    base_output = tmp_path / "base"
    base = run_audit(
        project,
        base_output,
        _SCHEMAS,
        material_inputs=(material_path,),
        method_contract_lock=contract / "semantic.lock.json",
        scientific_check_lane="development",
    )
    question = _scope_question(base)
    valid_path = tmp_path / "answer-incomplete.json"
    _answer_file(valid_path, question, option=INCOMPLETE_OPTION)
    valid_output = tmp_path / "answer-a"
    answered = run_audit(
        project,
        valid_output,
        _SCHEMAS,
        material_inputs=(material_path,),
        method_contract_lock=contract / "semantic.lock.json",
        scientific_check_lane="development",
        attestations=valid_path,
    )
    concern = answered["conditional_concerns"][0]
    assert concern["extensions"]["x-report-label"] == ("Author attestation — not a tool Finding")
    assert concern["condition"]["premise_state"] == "unknown"
    assert "severity" not in concern
    assert answered["findings"] == []
    report_html = (valid_output / "report.html").read_text(encoding="utf-8")
    assert "Author attestation — not a tool Finding" in report_html
    assert "Findings" in report_html
    assert "Material questions" in report_html

    invalid = json.loads(valid_path.read_text(encoding="utf-8"))
    invalid["answers"][0]["question_id"] = "material-question:wrong"
    invalid_path = tmp_path / "answer-invalid.json"
    invalid_path.write_text(canonical_json(invalid), encoding="utf-8")
    refused_output = tmp_path / "refused"
    with pytest.raises(MultipleTestingAttestationError) as caught:
        run_audit(
            project,
            refused_output,
            _SCHEMAS,
            material_inputs=(material_path,),
            method_contract_lock=contract / "semantic.lock.json",
            scientific_check_lane="development",
            attestations=invalid_path,
        )
    assert caught.value.category == "attestations-question-not-open"
    assert not refused_output.exists()

    qualified_output = tmp_path / "qualified-refused"
    with pytest.raises(ValueError, match="attestations-qualified-lane"):
        run_audit(
            project,
            qualified_output,
            _SCHEMAS,
            material_inputs=(material_path,),
            method_contract_lock=contract / "semantic.lock.json",
            attestations=valid_path,
        )
    assert not qualified_output.exists()
