from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from sc_referee_evaluation.prospective_qualification_v2 import (
    freeze_author_selected_result_declaration,
    freeze_case_evidence_contract,
)
from sc_referee_evaluation.selected_result_qualification_oracle import (
    ConstructionCertificate,
    FileCertificate,
    PositiveBindingCertificate,
    SpanCertificate,
    seal_construction_certificate,
    verify_construction_certificate,
)
from sc_referee_evaluation.selected_result_semantic_review import (
    certificate_binding_evidence,
    freeze_blind_semantic_review,
    reconcile_blind_semantic_review,
)
from sc_referee_evaluation.selected_result_verifier_qualification import (
    SelectedResultVerifierQualificationError,
    freeze_oracle_proof,
    freeze_qualification_validation,
    freeze_target_output,
    freeze_verifier_comparison,
    load_construction_certificate,
)
from selected_result_qualification_support import (
    build_test_case_author_session_evidence,
    build_test_certificate_reveal_evidence,
    build_test_identity_registry,
    build_test_provider_session_evidence,
)

from sc_referee.core.ids import semantic_digest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENTS = json.loads(
    (
        PROJECT_ROOT
        / "evaluation"
        / "qualification"
        / "selected-result-verifier-v1.1.0-study"
        / "opaque-assignments.json"
    ).read_text(encoding="utf-8")
)
SEMANTIC_CONTRACT = json.loads(
    (
        PROJECT_ROOT
        / "evaluation"
        / "qualification"
        / "selected-result-verifier-v1.1.0-precase"
        / "semantic-review-contract.json"
    ).read_text(encoding="utf-8")
)
CASE_ID = "case:70fd69d373e2b888bc07"
IDENTITY_REGISTRY, IDENTITY_KEYS = build_test_identity_registry(
    [
        ("case-author", "Author Provider"),
        ("semantic-validator-1", "Review Provider 1"),
        ("semantic-validator-2", "Review Provider 2"),
    ]
)
FROZEN_IDENTITY_REGISTRY_DIGEST = str(IDENTITY_REGISTRY["identity_registry_digest"])
BLOCK = "pilot"
PROVIDER_SLOT = "provider-family-1"
RUNNER_FREEZE_DIGEST = "sha256:" + "b" * 64
REVEAL_EVIDENCE: dict[str, dict[str, object]] = {}
AUTHOR_SESSIONS: dict[str, tuple[dict[str, str], dict[str, object]]] = {}
SOURCE = b"name,value\nall,100\n"
REPORT = b"[selected-result] all,100\n"
PRODUCER = (
    b"from pathlib import Path\n"
    b"rows = Path('inputs/table.csv').read_text().splitlines()\n"
    b"answer = rows[1]\n"
    b"report = f'[selected-result] {answer}\\n'\n"
    b"Path('results/report.md').write_text(report)\n"
)


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _span(span_id: str, path: str, payload: bytes, start: int, end: int) -> SpanCertificate:
    return SpanCertificate(span_id, path, start, end, _digest(payload[start:end]))


def _write_positive(root: Path) -> ConstructionCertificate:
    (root / "inputs").mkdir(parents=True)
    (root / "results").mkdir()
    (root / "workflow").mkdir()
    (root / "inputs" / "table.csv").write_bytes(SOURCE)
    (root / "results" / "report.md").write_bytes(REPORT)
    (root / "workflow" / "analysis.py").write_bytes(PRODUCER)
    writer = b"Path('results/report.md').write_text(report)"
    writer_start = PRODUCER.index(writer)
    return seal_construction_certificate(
        ConstructionCertificate(
            case_id=CASE_ID,
            expected_state="V",
            files=(
                FileCertificate("inputs/table.csv", len(SOURCE), _digest(SOURCE)),
                FileCertificate("results/report.md", len(REPORT), _digest(REPORT)),
                FileCertificate("workflow/analysis.py", len(PRODUCER), _digest(PRODUCER)),
            ),
            spans=(
                _span("operand", "inputs/table.csv", SOURCE, 0, len(SOURCE)),
                _span("producer", "workflow/analysis.py", PRODUCER, writer_start, len(PRODUCER)),
                _span("report", "results/report.md", REPORT, 0, len(REPORT)),
                _span("result", "results/report.md", REPORT, 0, len(REPORT)),
            ),
            positive_binding=PositiveBindingCertificate(
                result_span_id="result",
                producer_span_id="producer",
                operand_span_ids=("operand",),
                report_span_id="report",
            ),
            reason_codes=(),
        )
    )


def _packet() -> dict[str, str]:
    return {
        "case_id": CASE_ID,
        "profile_id": "selected-result-profile:python-static-marked-report-v1",
        "selected_report_path": "results/report.md",
    }


def _identity(actor_id: str, *, provider: str = "Independent Provider") -> dict[str, str]:
    return {
        "actor_id": actor_id,
        "provider": provider,
        "execution_context_id": f"context:{actor_id}",
        "identity_evidence_digest": semantic_digest({"identity_actor": actor_id}),
    }


def _author_identity() -> dict[str, str]:
    return _identity("case-author", provider="Author Provider")


def _author_session(
    root: Path, certificate: ConstructionCertificate
) -> tuple[dict[str, str], dict[str, object]]:
    cached = AUTHOR_SESSIONS.get(certificate.certificate_digest)
    if cached is None:
        identity, evidence = build_test_case_author_session_evidence(
            registry=IDENTITY_REGISTRY,
            private_key=IDENTITY_KEYS["case-author"],
            actor_id="case-author",
            provider="Author Provider",
            execution_context_id="context:case-author",
            case_id=CASE_ID,
            target_packet=_packet(),
            assignment_binding=_assignment_binding(),
            runner_freeze_digest=RUNNER_FREEZE_DIGEST,
            semantic_contract=SEMANTIC_CONTRACT,
            case_root=root,
            construction_certificate=asdict(certificate),
        )
        cached = (identity, evidence)
        AUTHOR_SESSIONS[certificate.certificate_digest] = cached
    return cached


def _independence() -> dict[str, bool]:
    return {
        "case_bytes_inspected": True,
        "semantic_contract_inspected": True,
        "construction_certificate_seen": False,
        "target_source_seen": False,
        "target_tests_seen": False,
        "target_output_seen": False,
        "other_review_seen": False,
    }


def _assignment_binding() -> dict[str, object]:
    assignment = next(
        item
        for block in ASSIGNMENTS["blocks"]
        if block["block"] == BLOCK
        for item in block["assignments"]
        if item["case_id"] == CASE_ID
    )
    return {
        "assignment_digest": ASSIGNMENTS["assignment_digest"],
        "block": BLOCK,
        "provider_slot": PROVIDER_SLOT,
        "assignment_position": assignment["assignment_position"],
        "case_id": CASE_ID,
        "target_packet": _packet(),
    }


def _first_evidence(root: Path) -> dict[str, object]:
    path = sorted(item for item in root.rglob("*") if item.is_file())[0]
    payload = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "start": 0,
        "end": len(payload),
        "sha256": "sha256:" + _digest(payload),
    }


def _reconciliations(root: Path, certificate: ConstructionCertificate) -> list[dict[str, object]]:
    author_identity, _author_evidence = _author_session(root, certificate)
    result = verify_construction_certificate(certificate, root)
    binding = certificate_binding_evidence(certificate)
    conclusion = {
        "expected_state": result.expected_state,
        "reason_codes": list(result.reason_codes),
        "positive_binding_digest": semantic_digest(binding) if binding is not None else None,
    }
    rule_trace = [
        {
            "rule_id": (
                "supported_single_binding"
                if result.expected_state == "V"
                else result.reason_codes[0]
            ),
            "outcome": "matched",
            "evidence": [_first_evidence(root)],
        }
    ]
    reviews = []
    for index in (1, 2):
        actor = f"semantic-validator-{index}"
        provider = f"Review Provider {index}"
        identity, evidence = build_test_provider_session_evidence(
            registry=IDENTITY_REGISTRY,
            private_key=IDENTITY_KEYS[actor],
            actor_id=actor,
            provider=provider,
            execution_context_id=f"context:{actor}",
            case_id=CASE_ID,
            target_packet=_packet(),
            assignment_binding=_assignment_binding(),
            runner_freeze_digest=RUNNER_FREEZE_DIGEST,
            semantic_contract=SEMANTIC_CONTRACT,
            case_root=root,
            semantic_conclusion=conclusion,
            binding_evidence=binding,
            rule_trace=rule_trace,
            independence_declaration=_independence(),
            index=index,
        )
        reviews.append(
            freeze_blind_semantic_review(
                case_root=root,
                target_packet=_packet(),
                assignment_binding=_assignment_binding(),
                runner_freeze_digest=RUNNER_FREEZE_DIGEST,
                semantic_contract=SEMANTIC_CONTRACT,
                identity_registry=IDENTITY_REGISTRY,
                author_identity=author_identity,
                validator_identity=identity,
                validator_identity_evidence=evidence,
                semantic_conclusion=conclusion,
                binding_evidence=binding,
                rule_trace=rule_trace,
                independence_declaration=_independence(),
                completed_at=f"2026-08-04T19:5{index}:00Z",
            )
        )
    reconciliations = [
        reconcile_blind_semantic_review(
            blind_review=review,
            case_root=root,
            certificate=certificate,
            target_packet=_packet(),
            assignment_binding=_assignment_binding(),
            runner_freeze_digest=RUNNER_FREEZE_DIGEST,
            semantic_contract=SEMANTIC_CONTRACT,
            identity_registry=IDENTITY_REGISTRY,
            author_identity=author_identity,
            certificate_revealed_at="2026-08-04T19:53:00Z",
            reconciled_at=f"2026-08-04T19:5{index + 3}:00Z",
        )
        for index, review in enumerate(reviews, start=1)
    ]
    REVEAL_EVIDENCE[certificate.certificate_digest] = build_test_certificate_reveal_evidence(
        registry=IDENTITY_REGISTRY,
        private_key=IDENTITY_KEYS["semantic-validator-1"],
        case_id=CASE_ID,
        assignment_digest=str(ASSIGNMENTS["assignment_digest"]),
        runner_freeze_digest=RUNNER_FREEZE_DIGEST,
        certificate_digest=certificate.certificate_digest,
        blind_reviews=reviews,
    )
    return reconciliations


def _reveal(certificate: ConstructionCertificate) -> dict[str, object]:
    return REVEAL_EVIDENCE[certificate.certificate_digest]


def _case_contract(target: dict[str, object]) -> dict[str, object]:
    derivation = target["target_derivation"]
    assert isinstance(derivation, dict)
    candidates = derivation["candidate_bindings"]
    assert isinstance(candidates, list) and len(candidates) == 1
    binding = candidates[0]
    declaration = freeze_author_selected_result_declaration(
        {
            "case_id": CASE_ID,
            "declaration_state": "one_selected_result",
            "selected_result_binding": binding,
            "candidate_result_locators": [],
            "unsupported_producer_locators": [],
            "authorship": {
                "author_id": "case-author",
                "provider": "Author Provider",
                "execution_context_id": "context:case-author",
                "identity_evidence_digest": "sha256:" + "a" * 64,
            },
            "authored_at": "2026-08-04T18:50:00Z",
        },
        frozen_at="2026-08-04T19:00:00Z",
    )
    return freeze_case_evidence_contract(
        {
            "case_id": CASE_ID,
            "envelope": {
                "envelope_id": "relation-envelope:stopped-verifier-development",
                "check_id": "check:stopped-verifier-development",
                "candidate_id": "stopped-verifier-development",
                "binding_digest": "sha256:" + "b" * 64,
            },
            "canonical_issue_class": "issue-class:stopped-verifier-development",
            "author_declaration": declaration,
            "coordinated_at": "2026-08-04T19:10:00Z",
        },
        frozen_at="2026-08-04T19:20:00Z",
    )


def _validation(root: Path, target: dict[str, object]) -> dict[str, object]:
    return freeze_qualification_validation(
        case_root=root,
        case_contract=_case_contract(target),
        qualification_target_output=target,
        assignment_manifest=ASSIGNMENTS,
        validation_identity=_identity("validation-runner"),
        declaration_revealed_at="2026-08-04T20:02:30Z",
        compared_at="2026-08-04T20:02:40Z",
    )


def _placeholder_case_contract() -> dict[str, object]:
    locator = {
        "path": "placeholder.txt",
        "content_digest": "sha256:" + "0" * 64,
        "start_line": 1,
        "end_line": 1,
    }
    binding = {
        "binding_profile": "exact_selected_report_result_static_producer_v1",
        "selection_status": "one_selected_result",
        "report_locator": locator,
        "result_locator": locator,
        "producer_locator": {
            **locator,
            "path": "placeholder.py",
        },
        "source_operands": [
            {
                "operand_id": "operand:00000000000000000000",
                "record_ref": {
                    "record_type": "file_record",
                    "record_id": "file:00000000000000000000",
                },
                "source_locator": {**locator, "path": "placeholder.csv"},
            }
        ],
        "alternative_producer_locators": [],
        "declared_dynamic_selection": False,
    }
    declaration = freeze_author_selected_result_declaration(
        {
            "case_id": CASE_ID,
            "declaration_state": "one_selected_result",
            "selected_result_binding": binding,
            "candidate_result_locators": [],
            "unsupported_producer_locators": [],
            "authorship": {
                "author_id": "case-author",
                "provider": "Author Provider",
                "execution_context_id": "context:case-author",
                "identity_evidence_digest": "sha256:" + "a" * 64,
            },
            "authored_at": "2026-08-04T18:50:00Z",
        },
        frozen_at="2026-08-04T19:00:00Z",
    )
    return freeze_case_evidence_contract(
        {
            "case_id": CASE_ID,
            "envelope": {
                "envelope_id": "relation-envelope:stopped-verifier-development",
                "check_id": "check:stopped-verifier-development",
                "candidate_id": "stopped-verifier-development",
                "binding_digest": "sha256:" + "b" * 64,
            },
            "canonical_issue_class": "issue-class:stopped-verifier-development",
            "author_declaration": declaration,
            "coordinated_at": "2026-08-04T19:10:00Z",
        },
        frozen_at="2026-08-04T19:20:00Z",
    )


def test_exact_positive_oracle_target_and_comparison_replay(tmp_path: Path) -> None:
    certificate = _write_positive(tmp_path)
    certificate_path = tmp_path.parent / "certificate.json"
    certificate_path.write_text(json.dumps(asdict(certificate)), encoding="utf-8")
    loaded = load_construction_certificate(certificate_path)
    assert loaded == certificate

    proof = freeze_oracle_proof(
        case_root=tmp_path,
        certificate=loaded,
        target_packet=_packet(),
        oracle_identity=_identity("oracle-validator"),
        completed_at="2026-08-04T20:00:00Z",
        assignment_manifest=ASSIGNMENTS,
        block=BLOCK,
        provider_slot=PROVIDER_SLOT,
        runner_freeze_digest=RUNNER_FREEZE_DIGEST,
        author_identity=_author_session(tmp_path, loaded)[0],
        author_identity_evidence=_author_session(tmp_path, loaded)[1],
        semantic_contract=SEMANTIC_CONTRACT,
        identity_registry=IDENTITY_REGISTRY,
        frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
        semantic_reconciliations=_reconciliations(tmp_path, loaded),
        certificate_reveal_evidence=_reveal(loaded),
    )
    target = freeze_target_output(
        case_root=tmp_path,
        target_packet=_packet(),
        validator_identity=_identity("target-runner"),
        derived_at="2026-08-04T20:01:00Z",
        frozen_at="2026-08-04T20:02:00Z",
        assignment_manifest=ASSIGNMENTS,
        block=BLOCK,
        provider_slot=PROVIDER_SLOT,
        runner_freeze_digest=RUNNER_FREEZE_DIGEST,
    )
    validation = _validation(tmp_path, target)
    comparison = freeze_verifier_comparison(
        case_root=tmp_path,
        oracle_proof=proof,
        target_derivation=target,
        target_validation=validation,
        comparison_identity=_identity("comparison-runner"),
        compared_at="2026-08-04T20:03:00Z",
        frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
        assignment_manifest=ASSIGNMENTS,
    )

    assert proof["author_identity_evidence"] == _author_session(tmp_path, loaded)[1]
    assert proof["case_inventory_digest"] == semantic_digest(proof["case_inventory"])
    assert [item["path"] for item in proof["case_inventory"]] == [
        "inputs/table.csv",
        "results/report.md",
        "workflow/analysis.py",
    ]
    assert target["target_derivation"]["derivation_status"] == "one_selected_result_rederived"
    assert comparison["comparison_outcome"] == "exact_match"
    assert comparison["state_matches"] is True
    assert comparison["reason_codes_match"] is True
    assert comparison["validation_matches"] is True
    assert comparison["observed_validation_status"] == "verified_complete"
    assert comparison["binding_matches"] is True
    digest_basis = dict(comparison)
    supplied = digest_basis.pop("comparison_digest")
    assert supplied == semantic_digest(digest_basis)

    with pytest.raises(
        SelectedResultVerifierQualificationError,
        match="does not match the frozen runner binding",
    ):
        freeze_verifier_comparison(
            case_root=tmp_path,
            oracle_proof=proof,
            target_derivation=target,
            target_validation=validation,
            comparison_identity=_identity("comparison-runner"),
            compared_at="2026-08-04T20:03:00Z",
            frozen_identity_registry_digest="sha256:" + "0" * 64,
            assignment_manifest=ASSIGNMENTS,
        )


def test_forged_or_mutated_oracle_proof_cannot_compare(tmp_path: Path) -> None:
    certificate = _write_positive(tmp_path)
    proof = freeze_oracle_proof(
        case_root=tmp_path,
        certificate=certificate,
        target_packet=_packet(),
        oracle_identity=_identity("oracle-validator"),
        completed_at="2026-08-04T20:00:00Z",
        assignment_manifest=ASSIGNMENTS,
        block=BLOCK,
        provider_slot=PROVIDER_SLOT,
        runner_freeze_digest=RUNNER_FREEZE_DIGEST,
        author_identity=_author_session(tmp_path, certificate)[0],
        author_identity_evidence=_author_session(tmp_path, certificate)[1],
        semantic_contract=SEMANTIC_CONTRACT,
        identity_registry=IDENTITY_REGISTRY,
        frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
        semantic_reconciliations=_reconciliations(tmp_path, certificate),
        certificate_reveal_evidence=_reveal(certificate),
    )
    target = freeze_target_output(
        case_root=tmp_path,
        target_packet=_packet(),
        validator_identity=_identity("target-runner"),
        derived_at="2026-08-04T20:01:00Z",
        frozen_at="2026-08-04T20:02:00Z",
        assignment_manifest=ASSIGNMENTS,
        block=BLOCK,
        provider_slot=PROVIDER_SLOT,
        runner_freeze_digest=RUNNER_FREEZE_DIGEST,
    )
    validation = _validation(tmp_path, target)

    forged = dict(proof)
    forged["oracle_result"] = {**proof["oracle_result"], "expected_state": "I"}
    forged["oracle_proof_digest"] = semantic_digest(
        {key: value for key, value in forged.items() if key != "oracle_proof_digest"}
    )
    with pytest.raises(SelectedResultVerifierQualificationError, match="does not replay"):
        freeze_verifier_comparison(
            case_root=tmp_path,
            oracle_proof=forged,
            target_derivation=target,
            target_validation=validation,
            comparison_identity=_identity("comparison-runner"),
            compared_at="2026-08-04T20:03:00Z",
            frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
            assignment_manifest=ASSIGNMENTS,
        )

    mutated = replace(certificate, case_id="case:fedcba9876543210abcd")
    proof["construction_certificate"] = asdict(mutated)
    with pytest.raises(SelectedResultVerifierQualificationError, match="digest does not replay"):
        freeze_verifier_comparison(
            case_root=tmp_path,
            oracle_proof=proof,
            target_derivation=target,
            target_validation=validation,
            comparison_identity=_identity("comparison-runner"),
            compared_at="2026-08-04T20:03:00Z",
            frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
            assignment_manifest=ASSIGNMENTS,
        )


def test_target_cannot_receive_oracle_fields(tmp_path: Path) -> None:
    _write_positive(tmp_path)
    packet = _packet()
    packet["expected_state"] = "V"
    with pytest.raises(SelectedResultVerifierQualificationError, match="unsupported shape"):
        freeze_target_output(
            case_root=tmp_path,
            target_packet=packet,
            validator_identity=_identity("target-runner"),
            derived_at="2026-08-04T20:01:00Z",
            frozen_at="2026-08-04T20:02:00Z",
            assignment_manifest=ASSIGNMENTS,
            block=BLOCK,
            provider_slot=PROVIDER_SLOT,
            runner_freeze_digest=RUNNER_FREEZE_DIGEST,
        )


def test_target_must_run_after_oracle_freeze(tmp_path: Path) -> None:
    certificate = _write_positive(tmp_path)
    proof = freeze_oracle_proof(
        case_root=tmp_path,
        certificate=certificate,
        target_packet=_packet(),
        oracle_identity=_identity("oracle-validator"),
        completed_at="2026-08-04T20:02:00Z",
        assignment_manifest=ASSIGNMENTS,
        block=BLOCK,
        provider_slot=PROVIDER_SLOT,
        runner_freeze_digest=RUNNER_FREEZE_DIGEST,
        author_identity=_author_session(tmp_path, certificate)[0],
        author_identity_evidence=_author_session(tmp_path, certificate)[1],
        semantic_contract=SEMANTIC_CONTRACT,
        identity_registry=IDENTITY_REGISTRY,
        frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
        semantic_reconciliations=_reconciliations(tmp_path, certificate),
        certificate_reveal_evidence=_reveal(certificate),
    )
    target = freeze_target_output(
        case_root=tmp_path,
        target_packet=_packet(),
        validator_identity=_identity("target-runner"),
        derived_at="2026-08-04T20:00:00Z",
        frozen_at="2026-08-04T20:01:00Z",
        assignment_manifest=ASSIGNMENTS,
        block=BLOCK,
        provider_slot=PROVIDER_SLOT,
        runner_freeze_digest=RUNNER_FREEZE_DIGEST,
    )
    validation = freeze_qualification_validation(
        case_root=tmp_path,
        case_contract=_case_contract(target),
        qualification_target_output=target,
        assignment_manifest=ASSIGNMENTS,
        validation_identity=_identity("validation-runner"),
        declaration_revealed_at="2026-08-04T20:01:30Z",
        compared_at="2026-08-04T20:01:40Z",
    )
    with pytest.raises(SelectedResultVerifierQualificationError, match="predates"):
        freeze_verifier_comparison(
            case_root=tmp_path,
            oracle_proof=proof,
            target_derivation=target,
            target_validation=validation,
            comparison_identity=_identity("comparison-runner"),
            compared_at="2026-08-04T20:03:00Z",
            frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
            assignment_manifest=ASSIGNMENTS,
        )


def test_non_v_validation_wrapper_cannot_false_complete(tmp_path: Path) -> None:
    (tmp_path / "workflow").mkdir()
    source = b"from pathlib import Path\n"
    (tmp_path / "workflow" / "analysis.py").write_bytes(source)
    certificate = seal_construction_certificate(
        ConstructionCertificate(
            case_id=CASE_ID,
            expected_state="I",
            files=(
                FileCertificate(
                    "workflow/analysis.py",
                    len(source),
                    _digest(source),
                ),
            ),
            spans=(),
            positive_binding=None,
            reason_codes=("selected_report_missing",),
        )
    )
    proof = freeze_oracle_proof(
        case_root=tmp_path,
        certificate=certificate,
        target_packet=_packet(),
        oracle_identity=_identity("oracle-validator"),
        completed_at="2026-08-04T20:00:00Z",
        assignment_manifest=ASSIGNMENTS,
        block=BLOCK,
        provider_slot=PROVIDER_SLOT,
        runner_freeze_digest=RUNNER_FREEZE_DIGEST,
        author_identity=_author_session(tmp_path, certificate)[0],
        author_identity_evidence=_author_session(tmp_path, certificate)[1],
        semantic_contract=SEMANTIC_CONTRACT,
        identity_registry=IDENTITY_REGISTRY,
        frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
        semantic_reconciliations=_reconciliations(tmp_path, certificate),
        certificate_reveal_evidence=_reveal(certificate),
    )
    target = freeze_target_output(
        case_root=tmp_path,
        target_packet=_packet(),
        validator_identity=_identity("target-runner"),
        derived_at="2026-08-04T20:01:00Z",
        frozen_at="2026-08-04T20:02:00Z",
        assignment_manifest=ASSIGNMENTS,
        block=BLOCK,
        provider_slot=PROVIDER_SLOT,
        runner_freeze_digest=RUNNER_FREEZE_DIGEST,
    )
    validation = freeze_qualification_validation(
        case_root=tmp_path,
        case_contract=_placeholder_case_contract(),
        qualification_target_output=target,
        assignment_manifest=ASSIGNMENTS,
        validation_identity=_identity("validation-runner"),
        declaration_revealed_at="2026-08-04T20:02:30Z",
        compared_at="2026-08-04T20:02:40Z",
    )
    comparison = freeze_verifier_comparison(
        case_root=tmp_path,
        oracle_proof=proof,
        target_derivation=target,
        target_validation=validation,
        comparison_identity=_identity("comparison-runner"),
        compared_at="2026-08-04T20:03:00Z",
        frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
        assignment_manifest=ASSIGNMENTS,
    )

    assert comparison["comparison_outcome"] == "exact_match"
    assert comparison["observed_state"] == "I"
    assert comparison["observed_validation_status"] == "insufficient_evidence"
    assert comparison["validation_matches"] is True
