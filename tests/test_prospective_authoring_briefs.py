from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sc_referee_evaluation.prospective_qualification import REQUIRED_CELL_TYPES

from sc_referee.core.ids import semantic_digest

_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE_PATH = (
    _ROOT
    / "evaluation"
    / "prospective-qualification-v1"
    / "benchmark-blind-authoring-briefs.template.json"
)


def _template() -> dict[str, Any]:
    return json.loads(_TEMPLATE_PATH.read_text(encoding="utf-8"))


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for item in value.values() for key in _keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in _keys(item)}
    return set()


def test_authoring_brief_template_is_self_digested_and_has_no_authority() -> None:
    template = _template()
    declared_digest = template.pop("template_digest")
    assert semantic_digest(template) == declared_digest
    assert template["qualification_authority"] == "none_template_only"
    assert template["matrix_contract"]["evidence_status"].startswith(
        "This template and any unreviewed authored case are study materials only"
    )


def test_authoring_briefs_cover_the_exact_ten_by_seven_by_two_matrix() -> None:
    template = _template()
    relations = template["relation_briefs"]
    cells = template["cell_briefs"]
    blocks = template["study_blocks"]

    assert len(relations) == 10
    assert len({item["blind_envelope_id"] for item in relations}) == 10
    assert {item["cell_type"] for item in cells} == set(REQUIRED_CELL_TYPES)
    assert len(cells) == len(REQUIRED_CELL_TYPES) == 7
    assert {item["block_role"] for item in blocks} == {
        "threshold_pilot",
        "qualification_heldout",
    }

    matrix = template["matrix_contract"]
    assert matrix["relation_count"] == len(relations)
    assert matrix["cell_types_per_relation_per_block"] == len(cells)
    assert matrix["block_count"] == len(blocks)
    assert matrix["total_assignments_after_protocol_freeze"] == (
        len(relations) * len(cells) * len(blocks)
    )


def test_author_visible_template_exposes_no_detector_or_answer_side_identifiers() -> None:
    template = _template()
    serialized = json.dumps(template, sort_keys=True).lower()
    forbidden_keys = {
        "binding_digest",
        "candidate_id",
        "check_id",
        "detector_id",
        "detector_output",
        "expected_detector_result",
        "expected_label",
        "scientific_label",
    }
    forbidden_source_identities = (
        "genebench",
        "scienceagentbench",
        "task-0012",
        "task-0070",
    )
    recognizer_fragments = ("(?i", "(?is", "\\b", "match_scope", "reportoperandrule")

    assert not (_keys(template) & forbidden_keys)
    assert all(value not in serialized for value in forbidden_source_identities)
    assert all(value not in serialized for value in recognizer_fragments)


def test_each_relation_brief_is_semantic_and_case_scoped() -> None:
    for relation in _template()["relation_briefs"]:
        assert set(relation) == {
            "blind_envelope_id",
            "display_name",
            "governed_premise",
            "contrasting_construction",
            "semantic_roles",
            "relation_that_must_be_clear_when_supported",
            "generalization_guidance",
        }
        assert len(relation["semantic_roles"]) >= 5
        assert len(set(relation["semantic_roles"])) == len(relation["semantic_roles"])
        assert "For this case's primary" in relation["governed_premise"]
        assert relation["governed_premise"] != relation["contrasting_construction"]
        assert "detector" not in json.dumps(relation).lower()
        assert "finding" not in json.dumps(relation).lower()


def test_cell_briefs_enforce_pairing_and_independent_rewrite_boundaries() -> None:
    cells = {item["cell_type"]: item for item in _template()["cell_briefs"]}

    corrected = cells["corrected_twin"]
    assert "same author" in " ".join(corrected["must_include"]).lower()
    assert corrected["paired_case_access"] == "the referenced error-bearing case only"
    assert "only the governed method relation" in corrected["author_task"]

    rewritten = cells["renamed_implementation"]
    rewritten_text = json.dumps(rewritten).lower()
    assert "distinct from the referenced error-bearing case" in rewritten_text
    assert "different terminology" in rewritten_text
    assert "mere synonym replacement" in rewritten_text
    assert rewritten["paired_case_access"] == (
        "private protocol reference only; the author receives no paired-case content"
    )


def test_cell_briefs_do_not_encode_adjudication_or_detector_answers() -> None:
    cell_text = json.dumps(_template()["cell_briefs"], sort_keys=True).lower()
    prohibited_answers = (
        '"expected_label"',
        '"expected_detector',
        '"finding"',
        '"no_finding"',
        '"issue_present"',
        '"issue_absent"',
        '"indeterminate"',
    )
    assert all(value not in cell_text for value in prohibited_answers)
    assert "desired detector response or the adjudication answer" not in cell_text


def test_heldout_author_access_excludes_pilot_material_and_results() -> None:
    heldout = next(
        item
        for item in _template()["study_blocks"]
        if item["block_role"] == "qualification_heldout"
    )
    rule = heldout["author_access_rule"].lower()
    assert all(
        value in rule
        for value in ("pilot cases", "pilot reviews", "thresholds", "detector observations")
    )
