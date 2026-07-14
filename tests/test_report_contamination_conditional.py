from __future__ import annotations

import json

from rich.console import Console

from sc_referee.audit import AuditResult
from sc_referee.checks.contamination_confound import ContaminationConfoundCheck
from sc_referee.report import render_tty, to_html, to_json, to_md
from tests.contamination_factories import contamination_case


def _tty(result):
    console = Console(record=True, width=160, color_system=None)
    render_tty(result, console)
    return console.export_text()


def test_all_renderers_show_both_identities_adjacent_to_condition():
    design, bundle = contamination_case(adjusted=("condition",), ratified=True)
    finding = ContaminationConfoundCheck().run(design, bundle)
    result = AuditResult(findings=[finding])
    identities = dict(finding.conditional_on.component_identities)
    payload = json.loads(to_json(result))["findings"][0]
    assert payload["conditional_on"]["component_identities"] == identities
    for rendered in (to_md(result), to_html(result), _tty(result)):
        assert "CONDITIONAL ON BOTH RATIFIED PREMISES" in rendered
        assert all(value in rendered for value in identities.values())
        assert "invalidating either removes authorization" in rendered.lower()


def test_conditional_pass_also_renders_dual_premise():
    design, bundle = contamination_case(
        adjusted=("condition", "rho_external"), ratified=True
    )
    finding = ContaminationConfoundCheck().run(design, bundle)
    assert finding.conditional_on.component_identities
    assert "CONDITIONAL ON BOTH RATIFIED PREMISES" in to_md(AuditResult([finding]))
