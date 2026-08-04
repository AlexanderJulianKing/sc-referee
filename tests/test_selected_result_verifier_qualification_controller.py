from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from sc_referee_evaluation.selected_result_qualification_oracle import (
    ConstructionCertificate,
    FileCertificate,
    PositiveBindingCertificate,
    SpanCertificate,
    seal_construction_certificate,
)
from sc_referee_evaluation.selected_result_verifier_qualification import (
    SelectedResultVerifierQualificationError,
    freeze_oracle_proof,
    freeze_target_output,
    freeze_verifier_comparison,
    load_construction_certificate,
)

from sc_referee.core.ids import semantic_digest

CASE_ID = "case:0123456789abcdefabcd"
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
                _span(
                    "producer", "workflow/analysis.py", PRODUCER, writer_start, len(PRODUCER) - 1
                ),
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


def _identity(actor_id: str) -> dict[str, str]:
    return {
        "actor_id": actor_id,
        "provider": "Independent Provider",
        "execution_context_id": f"context:{actor_id}",
        "identity_evidence_digest": "sha256:" + "a" * 64,
    }


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
    )
    target = freeze_target_output(
        case_root=tmp_path,
        target_packet=_packet(),
        validator_identity=_identity("target-runner"),
        derived_at="2026-08-04T20:01:00Z",
        frozen_at="2026-08-04T20:02:00Z",
    )
    comparison = freeze_verifier_comparison(
        case_root=tmp_path,
        oracle_proof=proof,
        target_derivation=target,
        compared_at="2026-08-04T20:03:00Z",
    )

    assert target["derivation_status"] == "one_selected_result_rederived"
    assert comparison["comparison_outcome"] == "exact_match"
    assert comparison["state_matches"] is True
    assert comparison["reason_codes_match"] is True
    assert comparison["binding_matches"] is True
    digest_basis = dict(comparison)
    supplied = digest_basis.pop("comparison_digest")
    assert supplied == semantic_digest(digest_basis)


def test_forged_or_mutated_oracle_proof_cannot_compare(tmp_path: Path) -> None:
    certificate = _write_positive(tmp_path)
    proof = freeze_oracle_proof(
        case_root=tmp_path,
        certificate=certificate,
        target_packet=_packet(),
        oracle_identity=_identity("oracle-validator"),
        completed_at="2026-08-04T20:00:00Z",
    )
    target = freeze_target_output(
        case_root=tmp_path,
        target_packet=_packet(),
        validator_identity=_identity("target-runner"),
        derived_at="2026-08-04T20:01:00Z",
        frozen_at="2026-08-04T20:02:00Z",
    )

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
            compared_at="2026-08-04T20:03:00Z",
        )

    mutated = replace(certificate, case_id="case:fedcba9876543210abcd")
    proof["construction_certificate"] = asdict(mutated)
    with pytest.raises(SelectedResultVerifierQualificationError, match="digest does not replay"):
        freeze_verifier_comparison(
            case_root=tmp_path,
            oracle_proof=proof,
            target_derivation=target,
            compared_at="2026-08-04T20:03:00Z",
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
        )


def test_target_must_run_after_oracle_freeze(tmp_path: Path) -> None:
    certificate = _write_positive(tmp_path)
    proof = freeze_oracle_proof(
        case_root=tmp_path,
        certificate=certificate,
        target_packet=_packet(),
        oracle_identity=_identity("oracle-validator"),
        completed_at="2026-08-04T20:02:00Z",
    )
    target = freeze_target_output(
        case_root=tmp_path,
        target_packet=_packet(),
        validator_identity=_identity("target-runner"),
        derived_at="2026-08-04T20:00:00Z",
        frozen_at="2026-08-04T20:01:00Z",
    )
    with pytest.raises(SelectedResultVerifierQualificationError, match="predates"):
        freeze_verifier_comparison(
            case_root=tmp_path,
            oracle_proof=proof,
            target_derivation=target,
            compared_at="2026-08-04T20:03:00Z",
        )
