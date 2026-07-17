"""Renderer-independent proof-report facts built from real deterministic audit output."""
from dataclasses import FrozenInstanceError

import pytest


def _minimal_proof_report(ci_conclusion):
    from sc_referee.proof_report import ProofReport

    return ProofReport(
        analysis_type="condition_contrast_DE", overall_status="pass",
        ci_conclusion=ci_conclusion, replay_command="sc-referee audit .",
        input_digests=(), coverage=(), findings=(),
    )


@pytest.mark.parametrize("conclusion, phrase", [
    ("fail", "did not pass CI"),
    ("neutral", "not certified by CI"),
    ("pass", "passes CI"),
])
def test_proof_report_ci_phrase_is_exhaustive(conclusion, phrase):
    from sc_referee.proof_report import render_proof_report_html

    rendered = render_proof_report_html(_minimal_proof_report(conclusion))

    assert phrase in rendered
    if conclusion == "fail":
        assert "passes CI" not in rendered


def test_proof_report_rejects_an_unknown_ci_conclusion():
    from sc_referee.proof_report import render_proof_report_html

    with pytest.raises(ValueError, match="unknown proof-report CI conclusion"):
        render_proof_report_html(_minimal_proof_report("blocker"))


def test_status_to_proof_state_mapping_is_closed_and_pinned():
    from sc_referee.proof_report import PROOF_STATE_BY_STATUS

    assert PROOF_STATE_BY_STATUS == {
        "blocker": "PROVED_VIOLATION",
        "pass": "PROVED_CONFORMANT",
        "needs_evidence": "UNRESOLVED_CONTRACT",
        "not_audited": "NOT_AUDITED",
        "major": "PROVED_DEFECT",
        "informational": "INFORMATIONAL",
    }


def _by_id(report, check_id):
    return next(finding for finding in report.findings if finding.check_id == check_id)


def test_real_confounding_audit_builds_proof_states_contract_and_digests(tmp_path):
    from fixtures.confounding_alias.make_fixture import build
    from sc_referee.audit import run_audit
    from sc_referee.config import load_designs
    from sc_referee.ingest import ingest
    from sc_referee.proof_report import build_proof_report

    build(tmp_path)
    result = run_audit(tmp_path)
    (design,) = load_designs(tmp_path / "sc-referee.yaml")
    bundle = ingest(tmp_path)

    report = build_proof_report(result, design, bundle, folder=tmp_path)

    assert report.analysis_type == "condition_contrast_DE"
    assert report.overall_status == "blocker"
    assert report.ci_conclusion == "fail"
    assert report.replay_command == (
        f"sc-referee audit {tmp_path} --design {tmp_path / 'sc-referee.yaml'} "
        "--engine pydeseq2"
    )
    digests = {item.role: item for item in report.input_digests}
    assert len(digests["design"].sha256) == 64
    assert len(digests["data"].sha256) == 64
    assert digests["design"].available and digests["data"].available
    assert sum(item.count for item in report.coverage) == len(report.findings)

    confounding = _by_id(report, "confounding")
    assert confounding.proof_state == "PROVED_VIOLATION"
    assert confounding.raw_status == "blocker"
    assert confounding.audit_dimensions == ("conditioning_set",)
    assert confounding.dimensions_are_causal is True
    assert confounding.proof_basis == "design-matrix algebra"
    assert confounding.claim is None
    assert confounding.contract["confirmed_by_human"] is True
    assert confounding.contract["facts"]["condition"] == "culture_condition"
    assert confounding.contract["facts"]["batch"] == ["processing_run"]
    assert confounding.evidence["r2"] == pytest.approx(1.0)
    assert confounding.citations

    unresolved = _by_id(report, "count_model")
    assert unresolved.proof_state == "UNRESOLVED_CONTRACT"
    assert unresolved.proof_basis.startswith("abstention:")
    with pytest.raises(FrozenInstanceError):
        report.overall_status = "pass"


def test_composite_hic_nonconformance_never_claims_one_dimension_caused_it(tmp_path):
    from sc_referee.audit import AuditResult
    from sc_referee.checks.base import Finding
    from sc_referee.proof_report import build_proof_report
    from tests.factories import hic_contact_bundle, make_hic_design

    result = AuditResult(
        findings=[Finding(
            "hic_loop_strength", "blocker", "composite contract mismatch",
            metrics={"reported_delta": -1.0, "recomputed_delta": 1.0},
            citations=["method"],
        )],
        analysis_type="hic_loop_strength",
        confirmed_by_human=True,
        engine="simple",
    )
    report = build_proof_report(
        result, make_hic_design(), hic_contact_bundle(seed=3), folder=tmp_path)
    finding = report.findings[0]

    assert finding.audit_dimensions == ("inclusion_set", "scale", "weighting")
    assert finding.proof_state == "PROVED_VIOLATION"
    assert finding.dimensions_are_causal is False
    assert finding.proof_basis == "independent recompute"
    assert "loop-strength delta" in finding.claim


@pytest.mark.parametrize(
    "check_id,status,expected",
    [
        ("count_model", "pass", "provenance/static"),
        ("count_model", "major", "independent recompute"),
        ("pseudobulk_integrity", "blocker", "independent recompute"),
    ],
)
def test_branch_specific_proof_basis_is_structured_not_inferred_from_prose(
        check_id, status, expected, tmp_path):
    from sc_referee.audit import AuditResult
    from sc_referee.checks.base import Finding
    from sc_referee.proof_report import build_proof_report
    from tests.factories import make_design, paired_count_bundle

    result = AuditResult(
        findings=[Finding(check_id, status, "intentionally opaque verdict")],
        analysis_type="condition_contrast_DE",
        confirmed_by_human=True,
    )
    report = build_proof_report(
        result, make_design(), paired_count_bundle(n_donors=4), folder=tmp_path)

    assert report.findings[0].proof_basis == expected


def test_unavailable_provenance_input_has_an_explicit_digest_reason(tmp_path):
    from sc_referee.audit import AuditResult
    from sc_referee.bundle import Bundle, Measure
    from sc_referee.proof_report import build_proof_report
    from tests.factories import make_design
    import pandas as pd

    bundle = Bundle(
        observations=pd.DataFrame(),
        measure=Measure(kind="counts", counts=None, long=None, feature_index=[]),
        feature_metadata=pd.DataFrame(),
        provenance={"data": {"path": "missing-counts.csv", "reason": "declared data"}},
    )
    report = build_proof_report(
        AuditResult(analysis_type="condition_contrast_DE"),
        make_design(), bundle, folder=tmp_path,
    )

    missing = next(item for item in report.input_digests if item.role == "data")
    assert missing.available is False
    assert missing.sha256 is None
    assert "does not exist" in missing.reason


def test_relative_provenance_is_not_hashed_against_an_unrelated_working_directory(
        tmp_path, monkeypatch):
    from sc_referee.audit import AuditResult
    from sc_referee.bundle import Bundle, Measure
    from sc_referee.proof_report import build_proof_report
    from tests.factories import make_design
    import pandas as pd

    (tmp_path / "counts.csv").write_text("this is not the audited input")
    monkeypatch.chdir(tmp_path)
    bundle = Bundle(
        observations=pd.DataFrame(),
        measure=Measure(kind="counts", counts=None, long=None, feature_index=[]),
        feature_metadata=pd.DataFrame(),
        provenance={"data": {"path": "counts.csv", "reason": "relative audited input"}},
    )
    report = build_proof_report(
        AuditResult(analysis_type="condition_contrast_DE"), make_design(), bundle)

    data = next(item for item in report.input_digests if item.role == "data")
    assert data.available is False
    assert data.sha256 is None
    assert "cannot be resolved" in data.reason
