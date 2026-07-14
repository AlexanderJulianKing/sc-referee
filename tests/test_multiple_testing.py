"""`multiple_testing` — recompute BH over the analyst's OWN p-values.

Pure arithmetic on the reported table: no data, no code parsing, no LLM. This is the
most-covered error class in the expert rubrics (26/50) and the cheapest to check exactly.
"""
import numpy as np
import pandas as pd
import pytest
from statsmodels.stats.multitest import multipletests

from sc_referee import statuses as S
from sc_referee.checks.multiple_testing import evaluate_multiple_testing
from sc_referee.design import MultiplicityContract
from tests.factories import make_design


def _bh_contract(**overrides):
    values = dict(
        claim_type="error_controlled_discovery", error_criterion="fdr",
        adjustment_method="benjamini_hochberg", family_complete=True,
    )
    values.update(overrides)
    return MultiplicityContract(**values)


def _reported(p, padj=None, n_null=400):
    """`p` are the claimed-significant raw p-values; pad with nulls so the FDR family exists."""
    rng = np.random.default_rng(0)
    p_all = np.concatenate([np.asarray(p, dtype=float), rng.uniform(0.06, 1.0, n_null)])
    padj_all = p_all if padj is None else np.asarray(padj, dtype=float)
    return pd.DataFrame({
        "feature_id": [f"g{i}" for i in range(len(p_all))],
        "pvalue": p_all, "padj": padj_all, "effect": np.ones(len(p_all)),
    })


def test_unbound_adjusted_column_cannot_earn_correction_pass():
    p = [1e-9] * 30
    rep = _reported(p)
    rep["padj"] = multipletests(rep["pvalue"].to_numpy(), method="fdr_bh")[1]
    f = evaluate_multiple_testing(rep, make_design())
    assert (f.status, f.coverage, S.human_state(f)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )


def test_exact_bh_reproduction_under_bound_contract_passes():
    rep = _reported([1e-9] * 30)
    rep["padj"] = multipletests(rep["pvalue"].to_numpy(), method="fdr_bh")[1]
    f = evaluate_multiple_testing(rep, make_design(multiplicity_contract=_bh_contract()))
    assert f.status == S.PASS, f.verdict
    assert "reproduces" in f.verdict.lower()


def test_zero_reported_calls_does_not_bypass_fabricated_adjustment_validation():
    p = np.array([1e-12] * 10 + [0.5] * 90)
    rep = pd.DataFrame({"feature_id": [f"g{i}" for i in range(100)], "pvalue": p,
                        "padj": np.ones(100), "effect": np.ones(100)})
    f = evaluate_multiple_testing(rep, make_design())
    assert (f.status, f.coverage, S.human_state(f)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )
    assert f.metrics["claimed"] == 0


def test_uncorrected_claims_that_collapse_under_bh_is_a_blocker():
    """40 genes at raw p just under 0.05, in a family of 440 -> almost none survive BH."""
    f = evaluate_multiple_testing(
        _reported([0.04] * 40), make_design(multiplicity_contract=_bh_contract())
    )
    assert f.status == S.BLOCKER, f.verdict
    assert f.metrics["corrected"] is False
    assert f.metrics["survivors"] == 0
    assert "declares" in f.verdict.lower()
    assert "false positive" not in f.verdict.lower()


def test_uncorrected_but_claims_survive_bh_anyway_is_informational():
    """Forgetting BH is harmless when every claim is overwhelmingly significant."""
    f = evaluate_multiple_testing(_reported([1e-12] * 30), make_design())
    assert f.status == S.INFORMATIONAL, f.verdict
    assert f.metrics["survival_rate"] == pytest.approx(1.0)
    assert (f.coverage, f.judgment, S.human_state(f)) == (S.COMPLETE, None, S.CLEAR)


def test_partial_survival_is_major():
    f = evaluate_multiple_testing(
        _reported([1e-9] * 20 + [0.045] * 20),
        make_design(multiplicity_contract=_bh_contract()),
    )
    assert f.status == S.MAJOR, f.verdict
    assert 0.10 < f.metrics["survival_rate"] < 0.60


def test_nothing_blocks_before_a_human_confirms():
    f = evaluate_multiple_testing(
        _reported([0.04] * 40),
        make_design(confirmed=False, multiplicity_contract=_bh_contract()),
    )
    assert f.status == S.NEEDS_EVIDENCE
    assert (f.coverage, S.human_state(f)) == (S.NOT_RUN, S.NOT_CHECKED)


def test_significant_only_table_cannot_rebuild_the_family():
    rep = _reported([0.04] * 40, n_null=0)          # no non-significant rows
    f = evaluate_multiple_testing(rep, make_design())
    assert f.status == S.NEEDS_EVIDENCE
    assert f.coverage == S.NOT_RUN
    assert S.human_state(f) == "not_checked"
    assert "tested" in f.verdict.lower()


def test_no_raw_p_values_means_we_cannot_recompute():
    rep = _reported([1e-9] * 10)
    rep["pvalue"] = np.nan
    f = evaluate_multiple_testing(rep, make_design())
    assert f.status == S.NEEDS_EVIDENCE
    assert f.coverage == S.NOT_RUN
    assert S.human_state(f) == "not_checked"


def test_missing_report_is_not_checked_without_changing_shipped_status():
    finding = evaluate_multiple_testing(None, make_design())
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, "not_checked")


def test_adjusted_values_below_raw_p_are_not_universally_impossible():
    rng = np.random.default_rng(0)
    p = np.concatenate([[0.04], rng.uniform(0.2, 1.0, 100)])
    rep = pd.DataFrame({"feature_id": [f"g{i}" for i in range(len(p))], "pvalue": p,
                        "padj": np.concatenate([[0.001], np.ones(100)]), "effect": np.ones(len(p))})

    f = evaluate_multiple_testing(rep, make_design())
    assert (f.status, f.coverage, S.human_state(f)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )
    assert "impossible" not in f.verdict.lower()


def test_storey_q_values_below_raw_p_are_legitimate():
    p = np.concatenate([np.full(90, 0.04), np.ones(10)])
    q = np.concatenate([np.full(90, 0.009), np.ones(10)])
    rep = pd.DataFrame({
        "feature_id": [f"g{i}" for i in range(100)], "pvalue": p, "padj": q,
        "effect": np.ones(100),
    })
    contract = MultiplicityContract(
        claim_type="error_controlled_discovery", error_criterion="fdr",
        adjustment_method="storey", family_complete=True,
    )
    f = evaluate_multiple_testing(rep, make_design(multiplicity_contract=contract))
    assert f.status not in (S.BLOCKER, S.MAJOR)
    assert "impossible" not in f.verdict.lower()


@pytest.mark.parametrize("contract", [
    MultiplicityContract(
        claim_type="nominal_discovery", error_criterion="nominal",
        adjustment_method="none", family_complete=True,
    ),
    MultiplicityContract(
        claim_type="error_controlled_discovery", error_criterion="fwer",
        adjustment_method="bonferroni", family_complete=True,
    ),
])
def test_bh_attrition_under_a_different_declared_contract_abstains(contract):
    f = evaluate_multiple_testing(
        _reported([0.04] * 40), make_design(multiplicity_contract=contract)
    )
    assert (f.status, f.coverage, S.human_state(f)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )


def test_a_less_conservative_but_legitimate_correction_is_not_accused():
    """Storey q-values are <= BH-adjusted p BY CONSTRUCTION. Flagging that as an error would be a
    false accusation on a valid method. Report it; never fault it."""
    p = np.concatenate([np.full(40, 0.01), np.linspace(0.2, 1.0, 400)])
    bh = multipletests(p, method="fdr_bh")[1]
    padj = np.maximum(p, bh * 0.3)                      # valid (>= p) but more liberal than BH
    rep = pd.DataFrame({"feature_id": [f"g{i}" for i in range(len(p))], "pvalue": p,
                        "padj": padj, "effect": np.ones(len(p))})

    f = evaluate_multiple_testing(rep, make_design())
    assert f.status == S.INFORMATIONAL, f.verdict
    assert S.human_state(f) == S.CLEAR
    assert f.status not in (S.BLOCKER, S.MAJOR)
    assert "storey" in f.verdict.lower()


def test_bh_is_always_recomputed_even_when_the_table_claims_correction():
    rep = _reported([1e-9] * 30)
    rep["padj"] = multipletests(rep["pvalue"].to_numpy(), method="fdr_bh")[1]
    f = evaluate_multiple_testing(rep, make_design())
    assert f.metrics["survivors"] == f.metrics["claimed"]   # the recompute actually ran


def test_carries_a_real_citation():
    f = evaluate_multiple_testing(_reported([0.04] * 40), make_design())
    assert any("Benjamini" in c for c in f.citations)
