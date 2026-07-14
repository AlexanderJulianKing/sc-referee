import pandas as pd

from sc_referee import statuses as S
from sc_referee.checks.confounding import evaluate_confounding
from tests.factories import make_design


def _obs():
    rows = []
    for run in range(40):
        conditions = (["ctrl", "ctrl"] if run < 20
                      else (["stim", "stim"] if run < 39 else ["ctrl", "stim"]))
        rows += [(f"D{run}_{index}", condition, f"R{run}")
                 for index, condition in enumerate(conditions)]
    return pd.DataFrame(rows, columns=["donor", "condition", "run"])


def test_major_when_analyst_omitted_the_confounded_batch():
    design = make_design(
        model="~ condition",
        batch=("run",),
        sample_unit=("donor",),
        analyst_adjusted_for=["condition"],
    )

    finding = evaluate_confounding(_obs(), design)

    assert finding.status == S.MAJOR
    assert "run" in finding.metrics["omitted"]


def test_abstains_when_analyst_model_uncaptured():
    design = make_design(
        model="~ condition",
        batch=("run",),
        sample_unit=("donor",),
        analyst_adjusted_for=None,
    )

    finding = evaluate_confounding(_obs(), design)

    # Abstain must render as NOT-CHECKED (needs-your-input), never FLAGGED — else a clean analysis
    # whose model wasn't captured would be false-flagged.
    assert finding.status == S.NEEDS_EVIDENCE
    assert S.human_state(finding) == "not_checked"
    assert finding.metrics["analyst_model_captured"] is False


def test_no_major_when_analyst_adjusted_for_the_batch():
    design = make_design(
        model="~ run + condition",
        batch=("run",),
        sample_unit=("donor",),
        analyst_adjusted_for=["run", "condition"],
    )

    finding = evaluate_confounding(_obs(), design)

    assert finding.status != S.MAJOR
    assert finding.metrics["omitted"] == []


def test_abstains_when_adjusted_for_not_specifically_ratified():
    design = make_design(
        model="~ condition",
        batch=("run",),
        sample_unit=("donor",),
        analyst_adjusted_for=["condition"],
        confidence={"condition": "high", "analyst_adjusted_for": "low"},
    )

    finding = evaluate_confounding(_obs(), design)

    assert finding.status == S.NEEDS_EVIDENCE
    assert S.human_state(finding) == "not_checked"
    assert finding.metrics["analyst_model_captured"] is False


def test_any_unknown_adjusted_for_label_invalidates_the_whole_set():
    design = make_design(
        model="~ condition",
        batch=("run",),
        sample_unit=("donor",),
        analyst_adjusted_for=["condition", "C(run)"],
    )

    finding = evaluate_confounding(_obs(), design)

    assert finding.status == S.NEEDS_EVIDENCE
    assert S.human_state(finding) == "not_checked"
    assert finding.metrics["included"] == []
    assert finding.metrics["omitted"] == []
    assert finding.metrics["analyst_model_captured"] is False


def test_clean_uncaptured_design_is_not_flagged():
    """SPECIFICITY GUARD (the false-flag the abstain fix closes): a clean, estimable, CONFIRMED design
    whose analyst model is uncaptured must render as NOT-CHECKED — never FLAGGED."""
    clean = pd.DataFrame({
        "donor": [f"D{i}" for i in range(8)],
        "condition": ["ctrl", "stim"] * 4,
        "run": ["a", "a", "b", "b", "c", "c", "d", "d"],   # batch crossed with condition -> estimable
    })
    design = make_design(sample_unit=("donor",), analyst_adjusted_for=None)   # confirmed, uncaptured
    finding = evaluate_confounding(clean, design)
    assert S.human_state(finding) != "flagged"
    assert S.human_state(finding) == "not_checked"
