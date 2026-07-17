"""Permanent inventory for emitted tuples and their canonical presentation."""
from __future__ import annotations

import ast
import json
from collections import defaultdict
from pathlib import Path

import pytest
from rich.console import Console

from sc_referee import statuses as S
from sc_referee.audit import AuditResult
from sc_referee.report import render_tty, to_html, to_json, to_md
from tests.finding_cases import LITERAL_EMITTER_CLASSIFICATION, finding_cases


CASES = finding_cases()


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.emitter_id)
def test_real_emitter_tuple_and_semantic_projection(case):
    finding = case.scenario()
    actual = (finding.status, finding.coverage, finding.applicability, finding.judgment)

    assert finding.check_id == case.check_id
    assert actual == case.expected
    assert S.human_state(finding) == case.expected_human_state

    if case.semantic_class in {"non_defect", "abstention"}:
        assert S.human_state(finding) != S.FLAGGED
    if case.semantic_class in {"concern", "violation"}:
        assert S.human_state(finding) != S.CLEAR
    if case.semantic_class == "abstention":
        assert finding.status != S.INFORMATIONAL
        assert finding.coverage == S.NOT_RUN
        assert not (finding.status == S.NEEDS_EVIDENCE and finding.coverage == S.COMPLETE)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.emitter_id)
def test_every_renderer_uses_the_same_human_state(case):
    finding = case.scenario()
    result = AuditResult(findings=[finding])
    state = case.expected_human_state
    label = {S.N_A: "N/A"}.get(state, state.replace("_", " ").upper())

    payload = json.loads(to_json(result))
    assert payload["findings"][0]["human_state"] == state

    console = Console(record=True, width=120, color_system=None)
    render_tty(result, console)
    assert label in console.export_text()
    assert f"`{state}`" in to_md(result)
    assert label in to_html(result)


def test_refuted_good_explicit_abstentions_remain_not_checked():
    refuted_good = [
        case for case in CASES
        if case.emitter_id in {
            "confounding_strong.explicit_abstention",
            "confounding_stage1.explicit_abstention",
            "confounding_stage2.explicit_abstention",
        }
    ]
    assert len(refuted_good) == 3
    for case in refuted_good:
        finding = case.scenario()
        assert finding.coverage == S.NOT_RUN
        assert S.human_state(finding) == S.NOT_CHECKED


def test_all_contamination_abstentions_are_not_checked():
    cases = [case for case in CASES
             if case.emitter_id.startswith("contamination_confound.")
             and case.semantic_class == "abstention"]
    assert len(cases) == 5
    for case in cases:
        finding = case.scenario()
        assert (
            finding.coverage, finding.judgment,
            S.human_state(finding), finding.conditional_on,
        ) == (S.NOT_RUN, S.UNRESOLVED, S.NOT_CHECKED, None)


def _literal_emitters():
    root = Path(__file__).parents[1] / "src" / "sc_referee" / "checks"
    found = []
    for path in sorted(root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        rows = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            statuses = {
                child.attr
                for child in ast.walk(node)
                if isinstance(child, ast.Attribute)
                and isinstance(child.value, ast.Name)
                and child.value.id == "S"
                and child.attr in {"INFORMATIONAL", "NEEDS_EVIDENCE"}
            }
            if not statuses:
                continue
            owner = node
            while owner is not None and not isinstance(owner, (ast.FunctionDef, ast.AsyncFunctionDef)):
                owner = parents.get(owner)
            rows.extend((node.lineno, owner.name if owner else "<module>", status)
                        for status in statuses)
        ordinals = defaultdict(int)
        for _, owner, status in sorted(rows):
            key = (owner, status)
            ordinals[key] += 1
            found.append(f"{path.name}:{owner}:{status}:{ordinals[key]}")
    return set(found)


def test_new_literal_information_or_evidence_emitter_requires_classification():
    discovered = _literal_emitters()
    classified = set(LITERAL_EMITTER_CLASSIFICATION)
    assert discovered == classified, (
        "literal INFORMATIONAL/NEEDS_EVIDENCE emitter inventory changed; classify each new emitter "
        f"before shipping (unclassified={sorted(discovered - classified)}, "
        f"stale={sorted(classified - discovered)})"
    )
    assert set(LITERAL_EMITTER_CLASSIFICATION.values()) <= {
        "non_defect", "abstention", "concern", "violation", "n_a",
    }
