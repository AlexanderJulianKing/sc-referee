"""Load + validate against the packaged JSON schemas.

Schemas ship *inside* the package (src/sc_referee/schemas/) so they resolve at runtime
whether installed or run from a checkout.
"""
from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files

import jsonschema


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict:
    return json.loads((files("sc_referee") / "schemas" / name).read_text())


def _report_validation_error(message: str) -> None:
    raise jsonschema.ValidationError(message)


def _report_coverage(findings: list[dict]) -> dict:
    from collections import Counter

    from sc_referee import statuses as S

    status_counts = Counter(finding["status"] for finding in findings)
    human_counts = Counter(finding["human_state"] for finding in findings)
    return {
        "findings": len(findings),
        "human_states": {
            state: human_counts[state] for state in S.HUMAN_STATES if human_counts[state]
        },
        "statuses": {status: status_counts[status] for status in S.STATUSES if status_counts[status]},
    }


def _validate_report_semantics(report: dict) -> None:
    """Recompute report authority fields instead of trusting caller-supplied summaries."""
    from types import SimpleNamespace

    from sc_referee import statuses as S

    findings = report["findings"]
    expected_worst = max(
        (finding["status"] for finding in findings), key=lambda status: S.SEVERITY[status]
    )
    if report["worst_status"] != expected_worst:
        _report_validation_error(
            f"worst_status must be derived from findings ({expected_worst!r})")

    proved_pass = any(
        finding["status"] == S.PASS
        and finding["applicability"] == S.APPLIES
        and finding["coverage"] == S.COMPLETE
        and finding["judgment"] in (None, S.CONFORMANT)
        for finding in findings
    )
    expected_ci_fails = (
        not report["confirmed_by_human"]
        or not proved_pass
        or any(finding["status"] in S.FAIL_ON_DEFAULT for finding in findings)
    )
    if report["ci_fails"] is not expected_ci_fails:
        _report_validation_error("ci_fails contradicts the finding statuses")
    if expected_ci_fails and report["ci_conclusion"] != "fail":
        _report_validation_error("a non-certifying report requires ci_conclusion='fail'")
    if not expected_ci_fails and report["ci_conclusion"] == "fail":
        _report_validation_error("ci_conclusion='fail' requires a non-certifying condition")
    if report["ci_conclusion"] == "pass" and not proved_pass:
        _report_validation_error("ci_conclusion='pass' requires an applicable proved PASS")

    expected_fully_audited = not any(
        finding["status"] == S.NOT_AUDITED for finding in findings
    )
    if report["fully_audited"] is not expected_fully_audited:
        _report_validation_error("fully_audited contradicts the finding coverage")

    for finding in findings:
        expected_state = S.human_state(SimpleNamespace(**finding))
        if finding["human_state"] != expected_state:
            _report_validation_error(
                f"finding {finding['check_id']!r} has contradictory human_state")

    expected_coverage = _report_coverage(findings)
    if report["coverage"] != expected_coverage:
        _report_validation_error("top-level coverage does not match findings")

    flattened = []
    for analysis in report["analyses"]:
        if analysis["coverage"] != _report_coverage(analysis["findings"]):
            _report_validation_error("analysis coverage does not match its findings")
        flattened.extend(analysis["findings"])
    if flattened != findings:
        _report_validation_error("analysis findings do not exactly project the top-level findings")


def validate(instance, schema_name: str) -> None:
    """Raise jsonschema.ValidationError if `instance` does not conform."""
    jsonschema.validate(instance, load_schema(schema_name))
    if schema_name == "report.schema.json":
        _validate_report_semantics(instance)
