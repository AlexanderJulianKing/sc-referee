"""A green run must never mean "checked and clean" when nothing was checked.

`not_audited` is a first-class status: a recognised analysis type with no methods check
available yet is POSTED, never silently passed. The scientific status remains `not_audited`,
while the stricter certification gate fails closed. This matters more, not less, as analysis types
accrete — most real analyses will hit the "no check applies" path first.
"""
import json

import yaml

from fixtures.confounding_alias.make_fixture import build
from sc_referee import statuses as S
from sc_referee.audit import run_audit
from sc_referee.report import to_json


def _retype(folder, analysis_type):
    path = folder / "sc-referee.yaml"
    raw = yaml.safe_load(path.read_text())
    raw["analysis_type"] = analysis_type
    path.write_text(yaml.safe_dump(raw))


def test_unhandled_analysis_type_is_not_audited_not_pass(tmp_path):
    build(tmp_path)
    _retype(tmp_path, "marker_detection")  # in the schema, but no check covers it yet

    result = run_audit(tmp_path)

    assert [f.status for f in result.findings] == [S.NOT_AUDITED]
    assert result.worst_status() == S.NOT_AUDITED
    assert result.worst_status() != S.PASS          # the bug: it used to report `pass`
    assert result.fully_audited() is False


def test_not_audited_fails_certification_without_becoming_a_blocker(tmp_path):
    build(tmp_path)
    _retype(tmp_path, "trajectory")

    result = run_audit(tmp_path)
    assert result.ci_fails() is True
    assert result.ci_conclusion() == "fail"
    assert result.worst_status() == S.NOT_AUDITED   # uncertainty was not relabeled a blocker
    assert result.fully_audited() is False

    payload = json.loads(to_json(result))
    assert payload["fully_audited"] is False
    assert payload["worst_status"] == S.NOT_AUDITED


def test_not_audited_verdict_names_the_type_and_says_it_was_not_checked(tmp_path):
    build(tmp_path)
    # Differential abundance now receives the outcome-independent contrast checks; trajectory
    # remains the representative recognised type whose policy must explicitly abstain here.
    _retype(tmp_path, "trajectory")
    verdict = run_audit(tmp_path).findings[0].verdict
    assert "trajectory" in verdict
    assert "not audited" in verdict.lower()


def test_legacy_config_keeps_layer1_verdict_but_strong_coverage_is_explicit(tmp_path):
    build(tmp_path)
    result = run_audit(tmp_path)

    assert "confounding" in {f.check_id for f in result.findings}
    assert result.fully_audited() is False
    assert next(f for f in result.findings if f.check_id == "confounding_strong").status == S.NOT_AUDITED
    assert result.worst_status() == S.BLOCKER
    assert result.ci_fails() is True


def test_default_ci_conclusion_is_fail_closed_or_proved_pass():
    from sc_referee.audit import AuditResult
    from sc_referee.checks.base import Finding

    def result(*statuses, confirmed=True):
        return AuditResult(findings=[Finding("c", s, "v") for s in statuses], confirmed_by_human=confirmed)

    assert result(S.BLOCKER).ci_conclusion() == "fail"
    assert result(S.MAJOR).ci_conclusion() == "fail"
    assert result(S.NEEDS_EVIDENCE).ci_conclusion() == "fail"
    assert result(S.NOT_AUDITED).ci_conclusion() == "fail"
    assert result(S.INFORMATIONAL).ci_conclusion() == "fail"  # no applicable proved PASS
    assert result().ci_conclusion() == "fail"
    not_applicable = AuditResult(
        findings=[Finding("c", S.PASS, "not applicable", applicability=S.NOT_APPLICABLE)],
        confirmed_by_human=True,
    )
    assert not_applicable.ci_conclusion() == "fail"  # status spelling alone is not a proof
    assert result(S.PASS).ci_conclusion() == "pass"
    assert result(S.INFORMATIONAL, S.PASS).ci_conclusion() == "pass"   # a fact, not a defect
    assert result(S.BLOCKER, S.PASS).ci_conclusion() == "fail"
    # a clean `pass` requires ratification — an UNCONFIRMED design/manifest is never a clean bill.
    assert result(S.PASS, confirmed=False).ci_conclusion() == "fail"

    assert result(S.MAJOR).ci_fails() is True
    assert result(S.BLOCKER).ci_fails() is True


def test_nonapplicable_and_explicit_strong_abstention_remain_distinct(tmp_path):
    build(tmp_path)  # fixture reports unit_of_test: sample
    result = run_audit(tmp_path)
    assert result.fully_audited() is False
    assert [f.check_id for f in result.findings if f.status == S.NOT_AUDITED] == ["confounding_strong"]
