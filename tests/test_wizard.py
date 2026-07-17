"""The design wizard: plain-language design questions → a confirmed sc-referee.yaml, before the audit."""
from __future__ import annotations

import pytest

from sc_referee.wizard import design_questions, Question

_CONFIG = {
    "analysis_type": "condition_contrast_DE",
    "design": {"condition": "culture_condition", "replicate_unit": ["donor_id"],
               "batch": ["processing_run"]},
    "contrasts": [{"reference": "ctrl", "test": "stim",
                   "analyst_adjusted_for": ["processing_run", "culture_condition"]}],
    "reported_results": {"path": "results/de.csv", "unit_of_test": "sample"},
    "confidence": {"condition": "high", "replicate_unit": "low"},
    "unresolved": ["replicate_unit"],
}
_COLUMNS = ["donor_id", "culture_condition", "processing_run", "n_genes"]


def test_design_questions_prefill_and_required():
    qs = {q.role: q for q in design_questions(_CONFIG, _COLUMNS,
                                              analysis_types=["condition_contrast_DE", "marker_detection"])}
    # condition question is a column dropdown prefilled with the proposed column
    assert qs["condition"].kind == "column"
    assert qs["condition"].default == "culture_condition"
    assert "donor_id" in qs["condition"].options       # every column is selectable
    # an unresolved / low-confidence role is REQUIRED and not silently accepted
    assert qs["replicate_unit"].required is True
    # a confident role is prefilled and not forced
    assert qs["condition"].required is False
    # batch is a multi-select
    assert qs["batch"].kind == "columns"
    # the analyst's fitted covariates are separately surfaced for field-specific ratification
    assert qs["analyst_adjusted_for"].kind == "columns"
    assert "adjust" in qs["analyst_adjusted_for"].prompt.lower()
    assert qs["analyst_adjusted_for"].default == ("processing_run", "culture_condition")
    # the two contrast levels become their own questions
    assert qs["reference"].default == "ctrl" and qs["reference"].kind == "level"
    # every question carries a plain-language "why"
    assert all(q.why for q in qs.values())


import pandas as pd

from sc_referee.wizard import _reported_for_folder, answers_to_config
from sc_referee.schema_validation import validate


def _obs():
    return pd.DataFrame({
        "donor_id": ["d1", "d1", "d2", "d2"],
        "culture_condition": ["ctrl", "stim", "ctrl", "stim"],
        "processing_run": ["r1", "r1", "r2", "r2"],
    })


def test_answers_to_config_is_confirmed_and_synthesized():
    answers = {
        "analysis_type": "condition_contrast_DE",
        "condition": "culture_condition", "reference": "ctrl", "test": "stim",
        "replicate_unit": "donor_id", "batch": ["processing_run"], "unit_of_test": "sample",
        "analyst_adjusted_for": ["processing_run", "culture_condition"],
    }
    config = answers_to_config(answers, _obs(), code_signals={}, reported={"path": "results/de.csv"})
    assert config["confirmed_by_human"] is True
    assert config["analysis_type"] == "condition_contrast_DE"
    assert config["design"]["condition"] == "culture_condition"
    assert list(config["design"]["replicate_unit"]) == ["donor_id"]
    assert list(config["design"]["batch"]) == ["processing_run"]
    # the derived science came from synthesize_config, not hand-built here
    assert config["contrasts"][0]["reference"] == "ctrl"
    assert config["contrasts"][0]["test"] == "stim"
    assert "model" in config["contrasts"][0]
    assert config["contrasts"][0]["analyst_adjusted_for"] == [
        "processing_run", "culture_condition"
    ]
    assert config["confidence"]["analyst_adjusted_for"] == "high"
    assert config["type_confidence"] == "high"
    assert config["confidence"]["condition"] == "high"
    assert config["confidence"]["replicate_unit"] == "high"
    assert config["confidence"]["reference"] == "high"
    assert config["confidence"]["unit_of_test"] == "high"
    assert not {"condition", "replicate_unit", "reference", "unit_of_test",
                "analyst_adjusted_for"}.intersection(config["unresolved"])
    assert "aggregation_key" not in config["contrasts"][0]
    from sc_referee.config import semantic_digest
    assert config["confirmation_digest"] == semantic_digest(config)
    validate(config, "sc_referee.schema.json")


@pytest.mark.parametrize("selected", ["TYPO", "Stim", "ctrl"])
def test_unrecognized_comparison_cannot_confirm_all_synthesized_contrasts(selected):
    observations = pd.concat([
        _obs(),
        pd.DataFrame({
            "donor_id": ["d1", "d2"], "culture_condition": ["drug", "drug"],
            "processing_run": ["r1", "r2"],
        }),
    ], ignore_index=True)
    answers = {
        "analysis_type": "condition_contrast_DE", "condition": "culture_condition",
        "reference": "ctrl", "test": selected, "replicate_unit": "donor_id",
        "batch": ["processing_run"], "unit_of_test": "sample",
        "analyst_adjusted_for": [],
    }

    with pytest.raises(ValueError, match="requires exactly one exact match"):
        answers_to_config(answers, observations)


def test_duplicate_synthesized_comparison_cannot_be_confirmed(monkeypatch):
    from sc_referee import init

    base = {
        "analysis_type": "condition_contrast_DE", "design": {},
        "contrasts": [{"name": "one", "reference": "ctrl", "test": "stim"},
                      {"name": "two", "reference": "ctrl", "test": "stim"}],
        "confidence": {}, "unresolved": [], "batch_modeling": [], "csp_proposals": [],
    }
    monkeypatch.setattr(init, "synthesize_config", lambda *args, **kwargs: base)

    with pytest.raises(ValueError, match="matched 2 available contrasts"):
        answers_to_config({
            "analysis_type": "condition_contrast_DE", "condition": "culture_condition",
            "reference": "ctrl", "test": "stim", "replicate_unit": "donor_id",
            "unit_of_test": "sample", "analyst_adjusted_for": [],
        }, _obs())


def test_rerating_unchanged_comparison_preserves_external_contracts_and_remints_digest():
    from copy import deepcopy
    from sc_referee.config import semantic_digest

    answers = {
        "analysis_type": "condition_contrast_DE", "condition": "culture_condition",
        "reference": "ctrl", "test": "stim", "replicate_unit": "donor_id",
        "batch": ["processing_run"], "unit_of_test": "sample",
        "analyst_adjusted_for": [],
    }
    proposed = answers_to_config(answers, _obs())
    proposed = deepcopy(proposed)
    proposed["contrasts"][0]["multiplicity_contract"] = {
        "claim_type": "error_controlled_discovery", "error_criterion": "fdr",
        "adjustment_method": "benjamini_hochberg", "family_complete": True,
    }
    proposed["contrasts"][0]["report_inference_contract"] = {
        "producer_binding": "exact", "response_scale": "raw_counts",
        "method_family": "negative_binomial", "dependence_semantics": "iid_rows",
    }
    proposed["reported_results"]["path"] = "results/original.csv"
    proposed["external_reference"] = {"label": "Published table", "body": "Reference only"}
    proposed["confirmation_digest"] = semantic_digest(proposed)

    rerated = answers_to_config(answers, _obs(), proposed_config=proposed)

    assert rerated["contrasts"][0]["multiplicity_contract"] == \
        proposed["contrasts"][0]["multiplicity_contract"]
    assert rerated["contrasts"][0]["report_inference_contract"] == \
        proposed["contrasts"][0]["report_inference_contract"]
    assert rerated["reported_results"]["path"] == "results/original.csv"
    assert rerated["external_reference"] == proposed["external_reference"]
    assert rerated["confirmation_digest"] == semantic_digest(rerated)
    validate(rerated, "sc_referee.schema.json")


def test_changed_comparison_cannot_silently_rebind_an_external_contract():
    observations = pd.concat([
        _obs(),
        pd.DataFrame({
            "donor_id": ["d1", "d2"], "culture_condition": ["drug", "drug"],
            "processing_run": ["r1", "r2"],
        }),
    ], ignore_index=True)
    proposed = {
        "analysis_type": "condition_contrast_DE",
        "design": {"condition": "culture_condition", "replicate_unit": ["donor_id"],
                   "batch": ["processing_run"]},
        "contrasts": [{
            "name": "stim_vs_ctrl", "reference": "ctrl", "test": "stim",
            "multiplicity_contract": {
                "claim_type": "error_controlled_discovery", "error_criterion": "fdr",
                "adjustment_method": "benjamini_hochberg", "family_complete": True,
            },
        }],
    }
    answers = {
        "analysis_type": "condition_contrast_DE", "condition": "culture_condition",
        "reference": "ctrl", "test": "drug", "replicate_unit": "donor_id",
        "batch": ["processing_run"], "unit_of_test": "sample", "analyst_adjusted_for": [],
    }

    with pytest.raises(ValueError, match="detach previously confirmed contract fields"):
        answers_to_config(answers, observations, proposed_config=proposed)


def test_unknown_prior_extension_is_rejected_instead_of_silently_dropped():
    proposed = dict(_CONFIG, vendor_contract={"opaque": True})
    answers = {
        "analysis_type": "condition_contrast_DE", "condition": "culture_condition",
        "reference": "ctrl", "test": "stim", "replicate_unit": "donor_id",
        "batch": ["processing_run"], "unit_of_test": "sample", "analyst_adjusted_for": [],
    }

    with pytest.raises(ValueError, match="cannot safely preserve"):
        answers_to_config(answers, _obs(), proposed_config=proposed)


def test_selecting_one_comparison_cannot_strand_claims_from_another():
    observations = pd.concat([
        _obs(),
        pd.DataFrame({
            "donor_id": ["d1", "d2"], "culture_condition": ["drug", "drug"],
            "processing_run": ["r1", "r2"],
        }),
    ], ignore_index=True)
    proposed = {
        "analysis_type": "condition_contrast_DE",
        "design": {"condition": "culture_condition", "replicate_unit": ["donor_id"],
                   "batch": ["processing_run"]},
        "contrasts": [
            {"name": "stim_vs_ctrl", "reference": "ctrl", "test": "stim"},
            {"name": "drug_vs_ctrl", "reference": "ctrl", "test": "drug"},
        ],
        "claims": [
            {"name": "stim claim", "path": "results/stim.csv", "contrast": "stim_vs_ctrl"},
            {"name": "drug claim", "path": "results/drug.csv", "contrast": "drug_vs_ctrl"},
        ],
    }
    answers = {
        "analysis_type": "condition_contrast_DE", "condition": "culture_condition",
        "reference": "ctrl", "test": "stim", "replicate_unit": "donor_id",
        "batch": ["processing_run"], "unit_of_test": "sample", "analyst_adjusted_for": [],
    }

    with pytest.raises(ValueError, match="strand existing claims"):
        answers_to_config(answers, observations, proposed_config=proposed)


def test_missing_adjusted_for_answer_stays_uncaptured_and_unresolved():
    answers = {
        "analysis_type": "condition_contrast_DE",
        "condition": "culture_condition", "reference": "ctrl", "test": "stim",
        "replicate_unit": "donor_id", "batch": ["processing_run"], "unit_of_test": "sample",
    }

    config = answers_to_config(answers, _obs())

    assert config["contrasts"][0]["analyst_adjusted_for"] is None
    assert "analyst_adjusted_for" in config["unresolved"]
    assert config["confidence"]["analyst_adjusted_for"] == "low"


def test_explicit_no_adjustment_answer_stays_empty_not_none():
    answers = {
        "analysis_type": "condition_contrast_DE",
        "condition": "culture_condition", "reference": "ctrl", "test": "stim",
        "replicate_unit": "donor_id", "batch": ["processing_run"], "unit_of_test": "sample",
        "analyst_adjusted_for": [],
    }

    config = answers_to_config(answers, _obs())

    assert config["contrasts"][0]["analyst_adjusted_for"] == []
    assert config["confidence"]["analyst_adjusted_for"] == "high"


def test_report_binding_inside_analysis_folder_is_written_portably(tmp_path):
    report = tmp_path / "results" / "de.csv"
    report.parent.mkdir()
    report.touch()
    config = {"reported_results": {"path": str(report), "gene_col": "gene"}}

    assert _reported_for_folder(config, tmp_path)["path"] == "results/de.csv"


def test_human_review_preserves_explicit_multi_claim_inventory():
    answers = {
        "analysis_type": "condition_contrast_DE", "condition": "culture_condition",
        "reference": "ctrl", "test": "stim", "replicate_unit": "donor_id",
        "batch": ["processing_run"], "unit_of_test": "cell",
        "analyst_adjusted_for": [],
    }
    proposed = {
        "contrasts": [{"name": "old_contrast"}],
        "claims": [
            {"name": "gene_expression", "path": "results/de.csv",
             "contrast": "old_contrast", "unit_of_test": "cell"},
            {"name": "alternative_splicing", "path": "results/splicing.csv",
             "contrast": "old_contrast", "unit_of_test": "cell", "value_kind": "derived_ratio"},
        ],
    }

    config = answers_to_config(answers, _obs(), proposed_config=proposed)

    assert [claim["name"] for claim in config["claims"]] == [
        "gene_expression", "alternative_splicing",
    ]
    assert {claim["contrast"] for claim in config["claims"]} == {
        config["contrasts"][0]["name"],
    }


import urllib.parse
import urllib.request

from sc_referee.wizard import render_form, serve_wizard


def _questions():
    return [
        Question("condition", "Which column is the condition?", "why", "column",
                 ("a", "b"), "a", False),
        Question("unit_of_test", "Cell or sample?", "why", "radio", ("cell", "sample"),
                 "sample", True),
    ]


def test_render_form_is_self_contained_and_prefilled():
    html = render_form(_questions())
    assert html.lstrip().lower().startswith("<!doctype html>")
    assert "Which column is the condition?" in html
    assert 'value="a" selected' in html                 # prefilled
    assert "http://" not in html and "https://" not in html   # offline
    assert "<form" in html and "submit" in html.lower()


def test_render_form_separates_confident_readback_from_missing_context():
    questions = [
        Question("condition", 'I found “organ” as the comparison.', "why", "column",
                 ("organ", "patient"), "organ", False),
        Question("reference", "Baseline?", "why", "level", (), "Peripheral", False),
        Question("test", "Compared group?", "why", "level", (), "Brain", False),
        Question("batch", "Were there unrecorded technical batches?", "why", "columns",
                 ("organ", "patient"), (), False),
        Question("unit_of_test", "Cell or sample?", "why", "radio", ("cell", "sample"),
                 "cell", True),
    ]

    html = render_form(questions)

    assert "What Referee found" in html
    assert "What I still need from you" in html
    assert "Scientific claim under review" in html
    assert html.index("condition") < html.index("batch")
    assert "· proposed" in html
    assert "· needs your answer" in html
    # A required tentative value is not laundered into Referee's confident read-back.
    readback = html.split("What I still need from you", 1)[0]
    assert "unit of test" not in readback
    missing = html.split("What I still need from you", 1)[1]
    assert 'value="cell" checked' not in missing
    assert 'value="sample" checked' not in missing


def test_render_form_names_cautious_fallback_instead_of_implying_claude_ran():
    questions = [
        Question("analysis_type", "What kind of analysis is this?", "why", "choice",
                 ("condition_contrast_DE",), "condition_contrast_DE", True,
                 proposal_source="heuristic_no_llm"),
    ]

    html = render_form(questions)

    assert "Claude was not available for this run" in html
    assert "cautious draft" in html


def test_serve_wizard_returns_the_submitted_answers():
    def fake_browser(url):
        data = urllib.parse.urlencode({"condition": "b", "unit_of_test": "cell"}).encode()
        urllib.request.urlopen(url + "submit", data=data, timeout=5)

    answers = serve_wizard(_questions(), browser_open=fake_browser)
    assert answers["condition"] == "b"
    assert answers["unit_of_test"] == "cell"


import yaml
from pathlib import Path

from fixtures.confounding_alias.make_fixture import build
from sc_referee.wizard import run_wizard

_FAKE_CONFIG = {
    "analysis_type": "condition_contrast_DE",
    "design": {"condition": "culture_condition", "replicate_unit": ["donor_id"],
               "batch": ["processing_run"]},
    "contrasts": [{"reference": "ctrl", "test": "stim"}],
    "reported_results": {"path": "de.csv", "unit_of_test": "sample"},
    "confidence": {}, "unresolved": [],
}
_FAKE_ANSWERS = {
    "analysis_type": "condition_contrast_DE", "condition": "culture_condition",
    "reference": "ctrl", "test": "stim", "replicate_unit": "donor_id",
    "batch": ["processing_run"], "unit_of_test": "sample",
}


def test_run_wizard_writes_a_confirmed_design(tmp_path):
    build(tmp_path)
    out = run_wizard(tmp_path,
                     propose=lambda folder: (_FAKE_CONFIG, "heuristic_no_llm"),
                     serve=lambda questions: _FAKE_ANSWERS)
    assert out == tmp_path / "sc-referee.yaml"
    written = yaml.safe_load(out.read_text())
    assert written["confirmed_by_human"] is True
    assert written["design"]["condition"] == "culture_condition"


def test_run_wizard_cancelled_writes_nothing(tmp_path):
    build(tmp_path)
    (tmp_path / "sc-referee.yaml").unlink()          # so we can prove the wizard wrote nothing
    out = run_wizard(tmp_path,
                     propose=lambda folder: (_FAKE_CONFIG, "heuristic_no_llm"),
                     serve=lambda questions: {})      # human closed the tab
    assert out is None
    assert not (tmp_path / "sc-referee.yaml").exists()
