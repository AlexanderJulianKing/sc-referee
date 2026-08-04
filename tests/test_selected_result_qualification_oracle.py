from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest
from sc_referee_evaluation.selected_result_qualification_oracle import (
    ConstructionCertificate,
    FileCertificate,
    PositiveBindingCertificate,
    QualificationOracleError,
    SpanCertificate,
    seal_construction_certificate,
    verify_construction_certificate,
)


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _positive_certificate(root: Path) -> ConstructionCertificate:
    source = b"operand = 2\nresult = operand + 1\nwrite(result)\n"
    report = b"selected result: 3\n"
    (root / "analysis.py").write_bytes(source)
    (root / "report.txt").write_bytes(report)

    def span(span_id: str, path: str, needle: bytes, payload: bytes) -> SpanCertificate:
        start = payload.index(needle)
        return SpanCertificate(span_id, path, start, start + len(needle), _digest(needle))

    return seal_construction_certificate(
        ConstructionCertificate(
            case_id="qualification-case:positive-1",
            expected_state="V",
            files=(
                FileCertificate("analysis.py", len(source), _digest(source)),
                FileCertificate("report.txt", len(report), _digest(report)),
            ),
            spans=(
                span("operand", "analysis.py", b"operand = 2", source),
                span("producer", "analysis.py", b"result = operand + 1", source),
                span("result", "analysis.py", b"result", source),
                span("report", "report.txt", report.rstrip(b"\n"), report),
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


def test_positive_certificate_emits_exact_verified_binding(tmp_path: Path) -> None:
    certificate = _positive_certificate(tmp_path)

    result = verify_construction_certificate(certificate, tmp_path)

    assert result.expected_state == "V"
    assert result.reason_codes == ()
    assert result.qualification_authority == "none_tooling_only"
    assert result.positive_binding is not None
    assert result.positive_binding.result.path == "analysis.py"
    assert result.positive_binding.producer.span_id == "producer"
    assert tuple(item.span_id for item in result.positive_binding.operands) == ("operand",)
    assert result.positive_binding.report.sha256 == _digest(b"selected result: 3")


def test_oracle_uses_descriptor_rooted_tree_not_path_reopens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    certificate = _positive_certificate(tmp_path)

    def forbidden_path_access(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("oracle reopened case evidence through pathlib")

    monkeypatch.setattr(Path, "read_bytes", forbidden_path_access)
    monkeypatch.setattr(Path, "rglob", forbidden_path_access)

    result = verify_construction_certificate(certificate, tmp_path)

    assert result.expected_state == "V"


@pytest.mark.parametrize("state", ["A", "I", "U"])
def test_nonverify_states_are_closed_and_carry_no_binding(tmp_path: Path, state: str) -> None:
    payload = b"intentionally non-verifying case\n"
    (tmp_path / "case.txt").write_bytes(payload)
    certificate = seal_construction_certificate(
        ConstructionCertificate(
            case_id=f"qualification-case:{state.lower()}-1",
            expected_state=state,  # type: ignore[arg-type]
            files=(FileCertificate("case.txt", len(payload), _digest(payload)),),
            spans=(),
            positive_binding=None,
            reason_codes=(f"expected_{state.lower()}",),
        )
    )

    result = verify_construction_certificate(certificate, tmp_path)

    assert result.expected_state == state
    assert result.positive_binding is None


def test_rejects_file_mutation_and_extra_inventory_entry(tmp_path: Path) -> None:
    certificate = _positive_certificate(tmp_path)
    (tmp_path / "analysis.py").write_bytes(b"changed\n")

    with pytest.raises(QualificationOracleError, match="File identity differs"):
        verify_construction_certificate(certificate, tmp_path)

    (tmp_path / "analysis.py").write_bytes(b"operand = 2\nresult = operand + 1\nwrite(result)\n")
    (tmp_path / "unexpected.txt").write_text("extra", encoding="utf-8")
    with pytest.raises(QualificationOracleError, match="inventory differs"):
        verify_construction_certificate(certificate, tmp_path)


def test_rejects_span_and_certificate_digest_drift(tmp_path: Path) -> None:
    certificate = _positive_certificate(tmp_path)
    bad_span = replace(certificate.spans[0], sha256="0" * 64)
    resealed = seal_construction_certificate(
        replace(certificate, spans=(bad_span, *certificate.spans[1:]), certificate_digest="")
    )

    with pytest.raises(QualificationOracleError, match="Byte-span identity differs"):
        verify_construction_certificate(resealed, tmp_path)

    with pytest.raises(QualificationOracleError, match="digest does not replay"):
        verify_construction_certificate(replace(certificate, case_id="changed"), tmp_path)


def test_rejects_invalid_state_binding_contracts(tmp_path: Path) -> None:
    certificate = _positive_certificate(tmp_path)

    invalid = seal_construction_certificate(
        replace(certificate, expected_state="A", reason_codes=("ambiguous",))
    )
    with pytest.raises(QualificationOracleError, match="forbid a binding"):
        verify_construction_certificate(invalid, tmp_path)

    invalid = seal_construction_certificate(
        replace(certificate, positive_binding=None, certificate_digest="")
    )
    with pytest.raises(QualificationOracleError, match="requires one binding"):
        verify_construction_certificate(invalid, tmp_path)


def test_rejects_symlinks_without_following_them(tmp_path: Path) -> None:
    certificate = _positive_certificate(tmp_path)
    (tmp_path / "alias.py").symlink_to(tmp_path / "analysis.py")

    with pytest.raises(QualificationOracleError, match="Symlinks are unsupported"):
        verify_construction_certificate(certificate, tmp_path)


def test_module_has_no_production_or_prospective_imports(project_root: Path) -> None:
    source = (
        project_root
        / "evaluation"
        / "src"
        / "sc_referee_evaluation"
        / "selected_result_qualification_oracle.py"
    ).read_text(encoding="utf-8")

    assert "prospective_selected_result_verifier" not in source
    assert "from sc_referee." not in source
    assert "import sc_referee." not in source
    assert "import ast" not in source
