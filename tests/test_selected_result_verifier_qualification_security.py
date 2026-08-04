from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest
from sc_referee_evaluation.prospective_qualification_v2 import (
    freeze_author_selected_result_declaration,
    freeze_case_evidence_contract,
)
from sc_referee_evaluation.qualification_identity import signed_receipt_payload
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
    _REASON_CODES_BY_STATE,
    SelectedResultVerifierQualificationError,
    freeze_oracle_proof,
    freeze_qualification_validation,
    freeze_target_output,
    freeze_verifier_comparison,
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
        ("semantic-validator", "Review Provider"),
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
PROFILE_ID = "selected-result-profile:python-static-marked-report-v1"
SOURCE = b"name,value\nall,100\n"
REPORT = b"[selected-result] all,100\n"
PRODUCER = (
    b"from pathlib import Path\n"
    b"rows = Path('inputs/table.csv').read_text().splitlines()\n"
    b"answer = rows[1]\n"
    b"report = f'[selected-result] {answer}\\n'\n"
    b"Path('results/report.md').write_text(report)\n"
)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_positive_case(root: Path) -> None:
    (root / "inputs").mkdir(parents=True)
    (root / "results").mkdir()
    (root / "workflow").mkdir()
    (root / "inputs" / "table.csv").write_bytes(SOURCE)
    (root / "results" / "report.md").write_bytes(REPORT)
    (root / "workflow" / "analysis.py").write_bytes(PRODUCER)


def _files() -> tuple[FileCertificate, ...]:
    return (
        FileCertificate("inputs/table.csv", len(SOURCE), _sha256(SOURCE)),
        FileCertificate("results/report.md", len(REPORT), _sha256(REPORT)),
        FileCertificate("workflow/analysis.py", len(PRODUCER), _sha256(PRODUCER)),
    )


def _span(span_id: str, path: str, payload: bytes, start: int, end: int) -> SpanCertificate:
    return SpanCertificate(span_id, path, start, end, _sha256(payload[start:end]))


def _positive_certificate(*, one_byte_locators: bool = False) -> ConstructionCertificate:
    writer_start = PRODUCER.index(b"Path('results/report.md')")
    producer_end = writer_start + 1 if one_byte_locators else len(PRODUCER)
    report_end = 1 if one_byte_locators else len(REPORT)
    return seal_construction_certificate(
        ConstructionCertificate(
            case_id=CASE_ID,
            expected_state="V",
            files=_files(),
            spans=(
                _span("operand", "inputs/table.csv", SOURCE, 0, len(SOURCE)),
                _span(
                    "producer",
                    "workflow/analysis.py",
                    PRODUCER,
                    writer_start,
                    producer_end,
                ),
                _span("report", "results/report.md", REPORT, 0, report_end),
                _span("result", "results/report.md", REPORT, 0, report_end),
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


def _packet(selected_report_path: str = "results/report.md") -> dict[str, str]:
    return {
        "case_id": CASE_ID,
        "profile_id": PROFILE_ID,
        "selected_report_path": selected_report_path,
    }


def _identity(actor_id: str, *, provider: str | None = None) -> dict[str, str]:
    return {
        "actor_id": actor_id,
        "provider": provider or f"provider:{actor_id}",
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
        "sha256": "sha256:" + _sha256(payload),
    }


def _reconciliations(
    root: Path,
    certificate: ConstructionCertificate,
    *,
    author_identity: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    if author_identity is None:
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


def test_semantic_gate_rejects_author_supplied_state_and_unregistered_reason(
    tmp_path: Path,
) -> None:
    _write_positive_case(tmp_path)
    conclusion = {
        "expected_state": "U",
        "reason_codes": ["invented_reason_not_derived_from_bytes"],
        "positive_binding_digest": None,
    }
    rule_trace = [
        {
            "rule_id": "invented_reason_not_derived_from_bytes",
            "outcome": "matched",
            "evidence": [_first_evidence(tmp_path)],
        }
    ]
    identity, evidence = build_test_provider_session_evidence(
        registry=IDENTITY_REGISTRY,
        private_key=IDENTITY_KEYS["semantic-validator"],
        actor_id="semantic-validator",
        provider="Review Provider",
        execution_context_id="context:semantic-validator",
        case_id=CASE_ID,
        target_packet=_packet(),
        assignment_binding=_assignment_binding(),
        runner_freeze_digest=RUNNER_FREEZE_DIGEST,
        semantic_contract=SEMANTIC_CONTRACT,
        case_root=tmp_path,
        semantic_conclusion=conclusion,
        binding_evidence=None,
        rule_trace=rule_trace,
        independence_declaration=_independence(),
        index=1,
    )
    with pytest.raises(ValueError):
        freeze_blind_semantic_review(
            case_root=tmp_path,
            target_packet=_packet(),
            assignment_binding=_assignment_binding(),
            runner_freeze_digest=RUNNER_FREEZE_DIGEST,
            semantic_contract=SEMANTIC_CONTRACT,
            identity_registry=IDENTITY_REGISTRY,
            author_identity=_author_identity(),
            validator_identity=identity,
            validator_identity_evidence=evidence,
            semantic_conclusion=conclusion,
            binding_evidence=None,
            rule_trace=rule_trace,
            independence_declaration=_independence(),
            completed_at="2026-08-04T19:59:00Z",
        )


def test_blind_review_rejects_false_registered_absence_reason(tmp_path: Path) -> None:
    _write_positive_case(tmp_path)
    conclusion = {
        "expected_state": "U",
        "reason_codes": ["python_source_absent"],
        "positive_binding_digest": None,
    }
    rule_trace = [
        {
            "rule_id": "python_source_absent",
            "outcome": "matched",
            "evidence": [_first_evidence(tmp_path)],
        }
    ]
    identity, evidence = build_test_provider_session_evidence(
        registry=IDENTITY_REGISTRY,
        private_key=IDENTITY_KEYS["semantic-validator"],
        actor_id="semantic-validator",
        provider="Review Provider",
        execution_context_id="context:semantic-validator",
        case_id=CASE_ID,
        target_packet=_packet(),
        assignment_binding=_assignment_binding(),
        runner_freeze_digest=RUNNER_FREEZE_DIGEST,
        semantic_contract=SEMANTIC_CONTRACT,
        case_root=tmp_path,
        semantic_conclusion=conclusion,
        binding_evidence=None,
        rule_trace=rule_trace,
        independence_declaration=_independence(),
        index=1,
    )

    with pytest.raises(ValueError, match="does not demonstrate python_source_absent"):
        freeze_blind_semantic_review(
            case_root=tmp_path,
            target_packet=_packet(),
            assignment_binding=_assignment_binding(),
            runner_freeze_digest=RUNNER_FREEZE_DIGEST,
            semantic_contract=SEMANTIC_CONTRACT,
            identity_registry=IDENTITY_REGISTRY,
            author_identity=_author_identity(),
            validator_identity=identity,
            validator_identity_evidence=evidence,
            semantic_conclusion=conclusion,
            binding_evidence=None,
            rule_trace=rule_trace,
            independence_declaration=_independence(),
            completed_at="2026-08-04T19:59:00Z",
        )


def test_blind_review_rejects_forged_provider_session_signature(tmp_path: Path) -> None:
    _write_positive_case(tmp_path)
    certificate = _positive_certificate()
    binding = certificate_binding_evidence(certificate)
    assert binding is not None
    conclusion = {
        "expected_state": "V",
        "reason_codes": [],
        "positive_binding_digest": semantic_digest(binding),
    }
    rule_trace = [
        {
            "rule_id": "supported_single_binding",
            "outcome": "matched",
            "evidence": [_first_evidence(tmp_path)],
        }
    ]
    identity, evidence = build_test_provider_session_evidence(
        registry=IDENTITY_REGISTRY,
        private_key=IDENTITY_KEYS["semantic-validator"],
        actor_id="semantic-validator",
        provider="Review Provider",
        execution_context_id="context:semantic-validator",
        case_id=CASE_ID,
        target_packet=_packet(),
        assignment_binding=_assignment_binding(),
        runner_freeze_digest=RUNNER_FREEZE_DIGEST,
        semantic_contract=SEMANTIC_CONTRACT,
        case_root=tmp_path,
        semantic_conclusion=conclusion,
        binding_evidence=binding,
        rule_trace=rule_trace,
        independence_declaration=_independence(),
        index=1,
    )
    forged_evidence = dict(evidence)
    forged_completion = dict(forged_evidence["completion_receipt"])
    signature = str(forged_completion["signature_base64"])
    forged_completion["signature_base64"] = ("A" if signature[0] != "A" else "B") + signature[1:]
    forged_evidence["completion_receipt"] = forged_completion
    forged_evidence["identity_evidence_digest"] = semantic_digest(
        {key: value for key, value in forged_evidence.items() if key != "identity_evidence_digest"}
    )
    forged_identity = dict(identity)
    forged_identity["identity_evidence_digest"] = forged_evidence["identity_evidence_digest"]

    with pytest.raises(ValueError, match="signature is invalid"):
        freeze_blind_semantic_review(
            case_root=tmp_path,
            target_packet=_packet(),
            assignment_binding=_assignment_binding(),
            runner_freeze_digest=RUNNER_FREEZE_DIGEST,
            semantic_contract=SEMANTIC_CONTRACT,
            identity_registry=IDENTITY_REGISTRY,
            author_identity=_author_identity(),
            validator_identity=forged_identity,
            validator_identity_evidence=forged_evidence,
            semantic_conclusion=conclusion,
            binding_evidence=binding,
            rule_trace=rule_trace,
            independence_declaration=_independence(),
            completed_at="2026-08-04T19:59:00Z",
        )


def test_oracle_freeze_requires_authenticated_case_author_session(tmp_path: Path) -> None:
    _write_positive_case(tmp_path)
    certificate = _positive_certificate()
    reconciliations = _reconciliations(tmp_path, certificate)

    with pytest.raises(
        SelectedResultVerifierQualificationError,
        match="Registrar-authenticated case-author session evidence is required",
    ):
        freeze_oracle_proof(
            case_root=tmp_path,
            certificate=certificate,
            target_packet=_packet(),
            oracle_identity=_identity("oracle"),
            completed_at="2026-08-04T20:00:00Z",
            assignment_manifest=ASSIGNMENTS,
            block=BLOCK,
            provider_slot=PROVIDER_SLOT,
            runner_freeze_digest=RUNNER_FREEZE_DIGEST,
            author_identity=_author_session(tmp_path, certificate)[0],
            semantic_contract=SEMANTIC_CONTRACT,
            identity_registry=IDENTITY_REGISTRY,
            frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
            semantic_reconciliations=reconciliations,
            certificate_reveal_evidence=_reveal(certificate),
        )


def test_oracle_freeze_rejects_identity_registry_outside_frozen_binding(
    tmp_path: Path,
) -> None:
    _write_positive_case(tmp_path)
    certificate = _positive_certificate()
    author_identity, author_evidence = _author_session(tmp_path, certificate)

    with pytest.raises(
        SelectedResultVerifierQualificationError,
        match="does not match the frozen runner binding",
    ):
        freeze_oracle_proof(
            case_root=tmp_path,
            certificate=certificate,
            target_packet=_packet(),
            oracle_identity=_identity("oracle"),
            completed_at="2026-08-04T20:00:00Z",
            assignment_manifest=ASSIGNMENTS,
            block=BLOCK,
            provider_slot=PROVIDER_SLOT,
            runner_freeze_digest=RUNNER_FREEZE_DIGEST,
            author_identity=author_identity,
            author_identity_evidence=author_evidence,
            semantic_contract=SEMANTIC_CONTRACT,
            identity_registry=IDENTITY_REGISTRY,
            frozen_identity_registry_digest="sha256:" + "0" * 64,
        )


def test_oracle_freeze_rejects_forged_case_author_signature(tmp_path: Path) -> None:
    _write_positive_case(tmp_path)
    certificate = _positive_certificate()
    reconciliations = _reconciliations(tmp_path, certificate)
    author_identity, author_evidence = _author_session(tmp_path, certificate)
    forged_evidence = dict(author_evidence)
    forged_completion = dict(forged_evidence["completion_receipt"])
    signature = str(forged_completion["signature_base64"])
    forged_completion["signature_base64"] = ("A" if signature[0] != "A" else "B") + signature[1:]
    forged_evidence["completion_receipt"] = forged_completion
    forged_evidence["identity_evidence_digest"] = semantic_digest(
        {key: value for key, value in forged_evidence.items() if key != "identity_evidence_digest"}
    )
    forged_identity = dict(author_identity)
    forged_identity["identity_evidence_digest"] = forged_evidence["identity_evidence_digest"]

    with pytest.raises(
        SelectedResultVerifierQualificationError,
        match="signature is invalid",
    ):
        freeze_oracle_proof(
            case_root=tmp_path,
            certificate=certificate,
            target_packet=_packet(),
            oracle_identity=_identity("oracle"),
            completed_at="2026-08-04T20:00:00Z",
            assignment_manifest=ASSIGNMENTS,
            block=BLOCK,
            provider_slot=PROVIDER_SLOT,
            runner_freeze_digest=RUNNER_FREEZE_DIGEST,
            author_identity=forged_identity,
            author_identity_evidence=forged_evidence,
            semantic_contract=SEMANTIC_CONTRACT,
            identity_registry=IDENTITY_REGISTRY,
            frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
            semantic_reconciliations=reconciliations,
            certificate_reveal_evidence=_reveal(certificate),
        )


def test_oracle_freeze_rejects_case_author_session_for_other_certificate(
    tmp_path: Path,
) -> None:
    _write_positive_case(tmp_path)
    authored_certificate = _positive_certificate()
    substituted_certificate = _positive_certificate(one_byte_locators=True)
    reconciliations = _reconciliations(tmp_path, authored_certificate)
    author_identity, author_evidence = _author_session(tmp_path, authored_certificate)

    with pytest.raises(
        SelectedResultVerifierQualificationError,
        match="Case-author identity and retained session evidence do not replay",
    ):
        freeze_oracle_proof(
            case_root=tmp_path,
            certificate=substituted_certificate,
            target_packet=_packet(),
            oracle_identity=_identity("oracle"),
            completed_at="2026-08-04T20:00:00Z",
            assignment_manifest=ASSIGNMENTS,
            block=BLOCK,
            provider_slot=PROVIDER_SLOT,
            runner_freeze_digest=RUNNER_FREEZE_DIGEST,
            author_identity=author_identity,
            author_identity_evidence=author_evidence,
            semantic_contract=SEMANTIC_CONTRACT,
            identity_registry=IDENTITY_REGISTRY,
            frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
            semantic_reconciliations=reconciliations,
            certificate_reveal_evidence=_reveal(authored_certificate),
        )


@pytest.mark.parametrize(
    ("author_completed_at", "expected_error"),
    [
        (
            "2026-08-04T19:45:00Z",
            "Case-author completion must predate every independent reviewer launch",
        ),
        (
            "2026-08-04T20:01:00Z",
            "Case-author completion must predate the oracle proof",
        ),
    ],
)
def test_oracle_freeze_rejects_post_hoc_case_author_session(
    tmp_path: Path,
    author_completed_at: str,
    expected_error: str,
) -> None:
    _write_positive_case(tmp_path)
    certificate = _positive_certificate()
    author_identity, author_evidence = _author_session(tmp_path, certificate)
    late_evidence = dict(author_evidence)
    late_completion = dict(late_evidence["completion_receipt"])
    late_completion["issued_at"] = author_completed_at
    late_completion["signature_base64"] = base64.b64encode(
        IDENTITY_KEYS["case-author"].sign(signed_receipt_payload(late_completion))
    ).decode("ascii")
    late_evidence["completion_receipt"] = late_completion
    late_evidence["identity_evidence_digest"] = semantic_digest(
        {key: value for key, value in late_evidence.items() if key != "identity_evidence_digest"}
    )
    late_identity = dict(author_identity)
    late_identity["identity_evidence_digest"] = late_evidence["identity_evidence_digest"]
    reconciliations = _reconciliations(
        tmp_path,
        certificate,
        author_identity=late_identity,
    )

    with pytest.raises(SelectedResultVerifierQualificationError, match=expected_error):
        freeze_oracle_proof(
            case_root=tmp_path,
            certificate=certificate,
            target_packet=_packet(),
            oracle_identity=_identity("oracle"),
            completed_at="2026-08-04T20:00:00Z",
            assignment_manifest=ASSIGNMENTS,
            block=BLOCK,
            provider_slot=PROVIDER_SLOT,
            runner_freeze_digest=RUNNER_FREEZE_DIGEST,
            author_identity=late_identity,
            author_identity_evidence=late_evidence,
            semantic_contract=SEMANTIC_CONTRACT,
            identity_registry=IDENTITY_REGISTRY,
            frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
            semantic_reconciliations=reconciliations,
            certificate_reveal_evidence=_reveal(certificate),
        )


def test_one_byte_spans_cannot_compare_as_an_exact_binding(tmp_path: Path) -> None:
    _write_positive_case(tmp_path)
    certificate = _positive_certificate(one_byte_locators=True)

    try:
        proof = freeze_oracle_proof(
            case_root=tmp_path,
            certificate=certificate,
            target_packet=_packet(),
            oracle_identity=_identity("oracle"),
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
    except ValueError:
        return

    target = freeze_target_output(
        case_root=tmp_path,
        target_packet=_packet(),
        validator_identity=_identity("target"),
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

    assert comparison["comparison_outcome"] != "exact_match"
    assert comparison["binding_matches"] is False


def test_comparison_rejects_different_oracle_and_target_packets(tmp_path: Path) -> None:
    _write_positive_case(tmp_path)
    certificate = _positive_certificate()
    proof = freeze_oracle_proof(
        case_root=tmp_path,
        certificate=certificate,
        target_packet=_packet(),
        oracle_identity=_identity("oracle"),
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
    forged_proof = dict(proof)
    forged_packet = dict(proof["target_packet"])
    forged_packet["selected_report_path"] = "outputs/final.txt"
    forged_binding = dict(proof["assignment_binding"])
    forged_binding["target_packet"] = forged_packet
    forged_proof["target_packet"] = forged_packet
    forged_proof["assignment_binding"] = forged_binding
    forged_proof["oracle_proof_digest"] = semantic_digest(
        {key: value for key, value in forged_proof.items() if key != "oracle_proof_digest"}
    )
    target = freeze_target_output(
        case_root=tmp_path,
        target_packet=_packet(),
        validator_identity=_identity("target"),
        derived_at="2026-08-04T20:01:00Z",
        frozen_at="2026-08-04T20:02:00Z",
        assignment_manifest=ASSIGNMENTS,
        block=BLOCK,
        provider_slot=PROVIDER_SLOT,
        runner_freeze_digest=RUNNER_FREEZE_DIGEST,
    )
    validation = _validation(tmp_path, target)

    with pytest.raises(SelectedResultVerifierQualificationError):
        freeze_verifier_comparison(
            case_root=tmp_path,
            oracle_proof=forged_proof,
            target_derivation=target,
            target_validation=validation,
            comparison_identity=_identity("comparison-runner"),
            compared_at="2026-08-04T20:03:00Z",
            frozen_identity_registry_digest=FROZEN_IDENTITY_REGISTRY_DIGEST,
            assignment_manifest=ASSIGNMENTS,
        )


def test_public_controller_rejects_an_unassigned_case(tmp_path: Path) -> None:
    _write_positive_case(tmp_path)

    with pytest.raises(SelectedResultVerifierQualificationError):
        freeze_target_output(
            case_root=tmp_path,
            target_packet=_packet(),
            validator_identity=_identity("target"),
            derived_at="2026-08-04T20:01:00Z",
            frozen_at="2026-08-04T20:02:00Z",
        )


def test_oracle_phase_import_does_not_import_target_verifier(project_root: Path) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        (
            str(project_root / "src"),
            str(project_root / "evaluation" / "src"),
        )
    )
    command = (
        "import sys; "
        "from sc_referee_evaluation.selected_result_verifier_qualification "
        "import freeze_oracle_proof; "
        "print('sc_referee_evaluation.prospective_selected_result_verifier' in sys.modules)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=project_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "False"


def test_actual_phase_runner_import_keeps_target_and_worker_absent(project_root: Path) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        (
            str(project_root / "src"),
            str(project_root / "evaluation" / "src"),
        )
    )
    command = (
        "import sys; "
        "import sc_referee_evaluation.selected_result_qualification_runner; "
        "blocked = {"
        "'sc_referee_evaluation.prospective_selected_result_verifier',"
        "'sc_referee_evaluation.selected_result_qualification_target_worker'"
        "}; "
        "print(sorted(blocked.intersection(sys.modules)))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=project_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "[]"


def test_semantic_review_contract_replays_and_matches_controller_taxonomy(
    project_root: Path,
) -> None:
    path = (
        project_root
        / "evaluation"
        / "qualification"
        / "selected-result-verifier-v1.1.0-precase"
        / "semantic-review-contract.json"
    )
    contract = json.loads(path.read_text(encoding="utf-8"))
    supplied = contract.pop("contract_digest")
    assert supplied == semantic_digest(contract)
    assert {
        state: frozenset(reasons) for state, reasons in contract["reason_codes_by_state"].items()
    } == _REASON_CODES_BY_STATE
