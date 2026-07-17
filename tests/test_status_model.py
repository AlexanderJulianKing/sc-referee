"""Frozen Phase 2 contract for canonical finding axes and report-only human states."""
from __future__ import annotations

from dataclasses import replace
import json

import pytest

from sc_referee import statuses as S
from sc_referee.audit import AuditResult
from sc_referee.checks.base import Finding
from sc_referee.report import to_json


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (S.PASS, "clear"),
        (S.NOT_AUDITED, "not_checked"),
        (S.NEEDS_EVIDENCE, "not_checked"),
        (S.MAJOR, "flagged"),
        (S.BLOCKER, "flagged"),
        (S.INFORMATIONAL, "clear"),
    ],
)
def test_default_axes_preserve_the_complete_shipped_status_mapping(status, expected):
    finding = Finding("check", status, "verdict")

    assert finding.applicability == S.APPLIES
    assert finding.judgment is None
    assert finding.coverage == S.COMPLETE
    assert finding.proof_grade == (S.ADVISORY if status == S.INFORMATIONAL else None)
    assert S.human_state(finding) == expected


def test_column_space_abstention_rendering_guard_at_integration_seam():
    bare_needs_evidence = Finding("bare-gap", S.NEEDS_EVIDENCE, "verdict")
    informational = Finding("info", S.INFORMATIONAL, "verdict")
    covered_gap = Finding(
        "covered-gap", S.NEEDS_EVIDENCE, "verdict", coverage=S.NOT_RUN
    )
    not_audited = Finding("not-audited", S.NOT_AUDITED, "verdict")

    assert S.human_state(bare_needs_evidence) == S.NOT_CHECKED
    assert S.human_state(informational) == S.CLEAR
    assert S.human_state(covered_gap) == S.NOT_CHECKED
    assert S.human_state(not_audited) == S.NOT_CHECKED


def test_axis_derivation_is_total_and_never_hides_a_supported_concern():
    default = Finding("check", S.NEEDS_EVIDENCE, "verdict")

    cases = [
        (replace(default, applicability=S.NOT_APPLICABLE), "n_a"),
        (replace(default, applicability=S.UNKNOWN, coverage=S.PARTIAL), "not_checked"),
        (replace(default, coverage=S.NOT_RUN), "not_checked"),
        (replace(default, judgment=S.CONFORMANT), "clear"),
        (replace(default, judgment=S.VIOLATION), "flagged"),
        (replace(default, judgment=S.CONCERN), "flagged"),
        # Concern takes precedence over missing coverage: an annotation can never hide evidence.
        (replace(default, judgment=S.CONCERN, coverage=S.NOT_RUN), "flagged"),
        (replace(default, judgment=S.UNRESOLVED), "not_checked"),
        # Only NEEDS_EVIDENCE abstentions may reclassify; shipped concern statuses fail closed.
        (Finding("major", S.MAJOR, "supported", coverage=S.NOT_RUN), "flagged"),
    ]

    assert [S.human_state(finding) for finding, _ in cases] == [
        expected for _, expected in cases
    ]


def test_human_axes_do_not_change_any_gating_result():
    statuses = [S.PASS, S.NOT_AUDITED, S.NEEDS_EVIDENCE, S.INFORMATIONAL, S.MAJOR, S.BLOCKER]
    legacy = AuditResult(
        findings=[Finding(str(i), status, "same") for i, status in enumerate(statuses)],
        confirmed_by_human=True,
    )
    classified = AuditResult(
        findings=[
            replace(
                finding,
                applicability=S.UNKNOWN,
                judgment=S.UNRESOLVED,
                coverage=S.NOT_RUN,
                proof_grade=S.ADVISORY,
            )
            for finding in legacy.findings
        ],
        confirmed_by_human=True,
    )

    assert [finding.status for finding in classified.findings] == statuses
    assert classified.worst_status() == legacy.worst_status() == S.BLOCKER
    assert classified.ci_fails() == legacy.ci_fails() is True
    assert classified.ci_conclusion() == legacy.ci_conclusion() == "fail"
    assert classified.fully_audited() == legacy.fully_audited() is False
    assert S.FAIL_ON_DEFAULT == (S.BLOCKER, S.MAJOR, S.NEEDS_EVIDENCE, S.NOT_AUDITED)


def test_json_exposes_axes_human_state_and_legacy_status_while_coverage_counts_human_states():
    findings = [
        Finding("clear", S.PASS, "clear verdict", judgment=S.CONFORMANT, proof_grade=S.EXACT),
        Finding("flag", S.MAJOR, "flag verdict", judgment=S.CONCERN, proof_grade=S.ADVISORY),
        Finding("gap", S.NEEDS_EVIDENCE, "gap verdict", coverage=S.NOT_RUN),
        Finding("na", S.PASS, "not applicable", applicability=S.NOT_APPLICABLE),
    ]

    payload = json.loads(to_json(AuditResult(findings=findings)))

    assert [(f["check_id"], f["human_state"], f["status"]) for f in payload["findings"]] == [
        ("clear", "clear", "pass"),
        ("flag", "flagged", "major"),
        ("gap", "not_checked", "needs_evidence"),
        ("na", "n_a", "pass"),
    ]
    assert payload["coverage"]["human_states"] == {
        "clear": 1,
        "flagged": 1,
        "not_checked": 1,
        "n_a": 1,
    }
    assert payload["coverage"]["statuses"] == {
        "major": 1,
        "needs_evidence": 1,
        "pass": 2,
    }
    assert payload["findings"][0] | {} == {
        "check_id": "clear",
        "status": "pass",
        "human_state": "clear",
        "applicability": "applies",
        "judgment": "conformant",
        "coverage": "complete",
        "proof_grade": "exact",
        "verdict": "clear verdict",
        "metrics": {},
        "citations": [],
        "fix": None,
    }


def test_material_random_intercept_finding_serializes_as_not_checked():
    from sc_referee.checks.confounding_random_intercept import ConfoundingRandomInterceptCheck
    from tests.factories import pseudobulk_confounding_bundle, random_intercept_design
    bundle = pseudobulk_confounding_bundle()
    finding = ConfoundingRandomInterceptCheck().run(
        random_intercept_design(bundle, adjusted=["condition"]), bundle
    )
    payload = json.loads(to_json(AuditResult([finding], confirmed_by_human=True)))
    item = payload["findings"][0]
    assert (item["status"], item["coverage"], item["human_state"]) == (
        "needs_evidence", "not_run", "not_checked",
    )


@pytest.mark.parametrize(
    "status",
    [S.MAJOR, S.BLOCKER],
)
def test_default_concerns_stay_flagged_even_with_advisory_proof(status):
    finding = Finding("concern", status, "supported", proof_grade=S.ADVISORY)
    assert S.human_state(finding) == "flagged"


def test_every_frozen_confounding_fixture_has_an_explicit_human_state():
    from sc_referee.checks.confounding import evaluate_confounding
    from tests.frozen_oracles.cases import confounding_cases

    expected = {
        "alias_confirmed": (S.BLOCKER, "flagged"),
        "paired_crossed": (S.PASS, "clear"),
        "alias_unconfirmed": (S.NEEDS_EVIDENCE, "not_checked"),
        "alias_low_condition": (S.NEEDS_EVIDENCE, "not_checked"),
        "alias_low_replicate": (S.BLOCKER, "flagged"),
        "missing_level": (S.NEEDS_EVIDENCE, "not_checked"),
        "varying_covariate": (S.NEEDS_EVIDENCE, "not_checked"),
        "weak_omitted": (S.PASS, "clear"),
        "near_adjusted": (S.PASS, "clear"),
        "near_omitted": (S.MAJOR, "flagged"),
        "partial_omitted": (S.MAJOR, "flagged"),
        "partial_adjusted": (S.PASS, "clear"),
        "partial_patsy": (S.PASS, "clear"),
        "xor_additive": (S.PASS, "clear"),
        "one_per_cell": (S.PASS, "clear"),
        "unpaired_crossed": (S.PASS, "clear"),
        "unpaired_no_batch": (S.PASS, "clear"),
        "donor_in_model": (S.BLOCKER, "flagged"),
        "single_bridge": (S.MAJOR, "flagged"),
        "high_cardinality": (S.MAJOR, "flagged"),
        "clean_reverse_contrast": (S.PASS, "clear"),
        "fixture_confounding_alias": (S.BLOCKER, "flagged"),
    }

    actual = {
        name: (finding.status, S.human_state(finding))
        for name, observations, design in confounding_cases()
        for finding in [evaluate_confounding(observations, design)]
    }
    assert actual == expected
