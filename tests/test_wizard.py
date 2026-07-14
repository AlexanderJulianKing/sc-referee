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
    # The comparison itself is not presented as an "additional" covariate.
    assert qs["analyst_adjusted_for"].default == ("processing_run",)
    assert "culture_condition" not in qs["analyst_adjusted_for"].options
    assert qs["batch"].options == ("processing_run",)
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
    validate(config, "sc_referee.schema.json")


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


def test_explicit_not_sure_states_remain_unresolved():
    answers = {
        "analysis_type": "condition_contrast_DE",
        "condition": "culture_condition", "reference": "ctrl", "test": "stim",
        "replicate_unit": "donor_id", "unit_of_test": "sample",
        "batch_status": "not_sure", "adjustment_status": "not_sure",
    }

    config = answers_to_config(answers, _obs())

    assert "batch" in config["unresolved"]
    assert "analyst_adjusted_for" in config["unresolved"]
    assert config["confidence"]["batch"] == "low"
    assert config["confidence"]["analyst_adjusted_for"] == "low"


def test_explicit_none_states_are_confirmed_empty_answers():
    answers = {
        "analysis_type": "condition_contrast_DE",
        "condition": "culture_condition", "reference": "ctrl", "test": "stim",
        "replicate_unit": "donor_id", "unit_of_test": "sample",
        "batch_status": "none_recorded", "adjustment_status": "none",
    }

    config = answers_to_config(answers, _obs())

    assert config["design"]["batch"] == []
    assert config["contrasts"][0]["analyst_adjusted_for"] == []
    assert "batch" not in config["unresolved"]
    assert "analyst_adjusted_for" not in config["unresolved"]


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
    assert "What the folder cannot establish" in html
    assert "Scientific claim under review" in html
    assert html.index("condition") < html.index("batch")
    assert "· proposed" in html
    assert "· needs your answer" in html
    # A required tentative value is not laundered into Referee's confident read-back.
    readback = html.split("What the folder cannot establish", 1)[0]
    assert "unit of test" not in readback
    missing = html.split("What the folder cannot establish", 1)[1]
    assert 'value="cell" checked' not in missing
    assert 'value="sample" checked' not in missing


def test_confirmed_design_is_collapsed_and_uses_rerun_action():
    questions = [
        Question("analysis_type", "Analysis?", "why", "choice",
                 ("condition_contrast_DE",), "condition_contrast_DE", False,
                 proposal_source="confirmed_config"),
        Question("condition", "Condition?", "why", "column", ("organ",), "organ", False),
        Question("reference", "Baseline?", "why", "level", (), "Peripheral", False),
        Question("test", "Test?", "why", "level", (), "Brain", False),
        Question("batch", "Batch?", "why", "columns", (), (), False),
    ]

    html = render_form(questions)

    assert "Ready to review again" in html
    assert "<details class='design-details'>" in html
    assert "· previously confirmed" in html
    assert "Run review with this design" in html
    assert "Save changes and run review" in html
    assert "What the folder cannot establish" not in html


def test_explicit_batch_and_adjustment_states_are_rendered():
    questions = [
        Question("batch", "Batch?", "why", "columns", ("processing_run",), (), False),
        Question("analyst_adjusted_for", "Adjusted?", "why", "columns",
                 ("processing_run",), (), False),
    ]

    html = render_form(questions)

    assert 'name="batch_status"' in html
    assert "No technical batch column is recorded" in html
    assert "Not sure — leave batch confounding unevaluated" in html
    assert 'name="adjustment_status"' in html
    assert "No additional covariates" in html


def test_consequential_bindings_have_fail_closed_escape_hatches():
    questions = [
        Question("analysis_type", "Analysis?", "why", "choice",
                 ("condition_contrast_DE",), "condition_contrast_DE", False),
        Question("condition", "Condition?", "why", "column", ("organ",), "organ", False),
        Question("replicate_unit", "Replicate?", "why", "column", ("patient",), "patient", False),
    ]

    html = render_form(questions)

    assert html.count("Correct value isn’t listed") == 3
    assert html.count("Referee cannot safely use this mapping") == 3
    assert "Resolve mapping before review" in html
    assert 'value="__not_listed__"' in html
    assert 'value="__not_sure__"' in html


def test_claim_summary_uses_consistent_label_value_grammar():
    questions = [
        Question("analysis_type", "Analysis?", "why", "choice",
                 ("condition_contrast_DE",), "condition_contrast_DE", False),
        Question("condition", "Condition?", "why", "column", ("organ",), "organ", False),
        Question("reference", "Baseline?", "why", "level", (), "Peripheral", False),
        Question("test", "Test?", "why", "level", (), "Brain", False),
        Question("replicate_unit", "Replicate?", "why", "column", ("patient",), "patient", False),
        Question("unit_of_test", "Unit?", "why", "radio", ("cell", "sample"), "cell", False),
    ]

    html = render_form(questions)

    assert "Comparison column:" in html
    assert "Biological replicate:" in html
    assert "Reported test unit:" in html
    assert ("<b class='caution' data-summary-unit>individual cells</b>"
            "<em data-summary-unit-review>· review</em>") in html
    assert "</span> vs. <span data-summary-reference>" in html
    assert "relative to" not in html
    assert "data-summary-condition" in html
    assert "data-summary-replicate" in html
    assert "data-summary-test" in html
    assert "updateSummary" in html


def test_unresolved_binding_sentinels_cannot_reach_the_design():
    answers = {
        "analysis_type": "condition_contrast_DE", "condition": "__not_listed__",
        "reference": "ctrl", "test": "stim", "replicate_unit": "donor_id",
        "unit_of_test": "sample", "batch_status": "none_recorded",
        "adjustment_status": "none",
    }

    with pytest.raises(ValueError, match="unresolved design mapping: condition"):
        answers_to_config(answers, _obs())


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


# ── F1: batch-column escape hatch ────────────────────────────────────────────────────────────────
# The concise auto-detected technical list must never be the ONLY way to name a batch: a technical
# column with an unconventional name has to stay selectable, and a declared batch column must remain
# retained in the visible list regardless of its name.

def _batch_config(batch):
    return {
        "analysis_type": "condition_contrast_DE",
        "design": {"condition": "culture_condition", "replicate_unit": ["donor_id"],
                   "batch": list(batch)},
        "contrasts": [{"reference": "ctrl", "test": "stim", "analyst_adjusted_for": []}],
        "reported_results": {"path": "results/de.csv", "unit_of_test": "sample"},
        "confidence": {"condition": "high"},
        "unresolved": [],
    }


def test_unconventional_batch_column_is_recoverable_via_escape_hatch():
    # "collection_wave" matches no technical name token, so it is kept out of the concise list...
    columns = ["donor_id", "culture_condition", "processing_run", "collection_wave", "n_genes"]
    qs = {q.role: q for q in design_questions(_batch_config(["processing_run"]), columns,
                                              analysis_types=["condition_contrast_DE"])}
    batch = qs["batch"]
    assert "collection_wave" not in batch.options            # not auto-detected as technical
    assert "collection_wave" in batch.more_options           # ...but still offered, not lost

    html = render_form(list(qs.values()))
    assert "A different column records batch" in html        # accessible disclosure present
    assert 'name="batch" value="collection_wave"' in html    # selectable as a batch column
    # the escape-hatch checkbox lives inside the disclosure, after its summary
    assert html.index("A different column records batch") < html.index(
        'name="batch" value="collection_wave"')


def test_declared_batch_column_is_retained_even_with_an_unconventional_name():
    # A batch the design already declares must stay in the concise visible list and stay checked,
    # never demoted behind the escape hatch, even though "collection_wave" matches no name token.
    columns = ["donor_id", "culture_condition", "collection_wave", "n_genes"]
    qs = {q.role: q for q in design_questions(_batch_config(["collection_wave"]), columns,
                                              analysis_types=["condition_contrast_DE"])}
    batch = qs["batch"]
    assert "collection_wave" in batch.options                # retained in the visible list
    assert "collection_wave" in (batch.default or ())        # and pre-checked
    assert "collection_wave" not in batch.more_options       # not demoted to the escape hatch

    html = render_form(list(qs.values()))
    assert 'value="collection_wave" checked' in html


def test_escape_hatch_batch_selection_reaches_the_confirmed_design():
    # Selecting an unconventionally-named column through the escape hatch must actually BIND it as a
    # batch in the confirmed design — selectable AND effective, not a decorative control.
    obs = pd.DataFrame({
        "donor_id": ["d1", "d1", "d2", "d2"],
        "culture_condition": ["ctrl", "stim", "ctrl", "stim"],
        "collection_wave": ["w1", "w1", "w2", "w2"],
    })
    answers = {
        "analysis_type": "condition_contrast_DE",
        "condition": "culture_condition", "reference": "ctrl", "test": "stim",
        "replicate_unit": "donor_id", "unit_of_test": "sample",
        "batch_status": "recorded", "batch": "collection_wave",
        "adjustment_status": "none",
    }
    config = answers_to_config(answers, obs)
    assert config["design"]["batch"] == ["collection_wave"]
    assert "batch" not in config["unresolved"]


def test_batch_modeling_select_without_recovery_panel_keeps_sync_alive():
    # Regression (wizard live-summary + client Run-gating): a batch-modeling ceremony renders
    # column/choice selects (e.g. batch_modeling.<batch>.modeled_as) that carry data-binding-role
    # but have NO mapping-recovery panel. sync() previously dereferenced the missing panel and threw
    # a TypeError mid-loop, silently killing live-summary updates and the client Run gate. Reproduce
    # that exact DOM condition and prove the script guards the null, so the code AFTER the loop
    # (run.disabled=blocked + updateSummary()) is always reached. Runtime behaviour is additionally
    # verified in the browser smoke; this pins the structural fix so it cannot regress.
    import re

    config = {
        "analysis_type": "condition_contrast_DE",
        "design": {"condition": "stim_state", "replicate_unit": ["donor_id"], "batch": ["seq_run"]},
        "contrasts": [{"reference": "ctrl", "test": "stim", "analyst_adjusted_for": ["seq_run"]}],
        "reported_results": {"path": "results/de.csv", "unit_of_test": "sample"},
        "confidence": {"analysis_type": "high", "condition": "high", "replicate_unit": "high",
                       "reference": "high", "analyst_adjusted_for": "high"},
        "unresolved": [],
    }
    columns = ["donor_id", "stim_state", "seq_run", "n_genes"]
    html = render_form(design_questions(config, columns, analysis_types=["condition_contrast_DE"]))

    binding_roles = set(re.findall(r'data-binding-role="([^"]+)"', html))
    panels = set(re.findall(r'data-mapping-recovery="([^"]+)"', html))
    unpanelled = binding_roles - panels
    # The bug's DOM condition is genuinely reproduced: a batch-modeling select with a binding role
    # but no recovery panel would have made the old sync() throw.
    assert any(r.startswith("batch_modeling.") and r.endswith(".modeled_as") for r in unpanelled), \
        f"expected a batch_modeling.*.modeled_as binding-role without a panel; got {sorted(unpanelled)}"
    # sync() now null-guards the panel, so it cannot throw on that select...
    assert "if(panel){" in html
    # ...and the Run-gate + live-summary run after the loop, so they stay reachable.
    assert "run.disabled=blocked" in html and "updateSummary();" in html
