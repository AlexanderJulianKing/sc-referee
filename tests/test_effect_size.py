"""Item 4: effect_size_threshold — the silent green in the discrimination table.

With enough cells, a |log2FC| ~ 0.01 gene reaches FDR significance. Reporting it as a "discovery"
is significance-without-an-effect-gate: statistically real, biologically empty. This check reads the
reported table and flags when claimed-significant discoveries are dominated by NEGLIGIBLE effects.
It is ADVISORY — an effect-size cutoff is a policy choice — so it never blocks (max_status = major).
"""
import numpy as np
import pandas as pd

from sc_referee import statuses as S
from sc_referee.design import EffectRelevanceContract
from tests.factories import make_design


def _reported(effects, padj):
    n = len(effects)
    return pd.DataFrame({"feature_id": [f"g{i}" for i in range(n)],
                         "pvalue": np.asarray(padj, float), "padj": np.asarray(padj, float),
                         "effect": np.asarray(effects, float)})


def test_claims_with_real_effects_pass():
    from sc_referee.checks.effect_size import evaluate_effect_size

    rep = _reported(effects=[2.0, -1.8, 1.5, -2.2] * 5, padj=[1e-4] * 20)
    finding = evaluate_effect_size(make_design(), rep)
    assert finding.status == S.PASS
    assert "real effect" not in finding.verdict.lower()
    assert "magnitude" in finding.verdict.lower()


def test_small_effects_without_relevance_contract_are_not_checked():
    from sc_referee.checks.effect_size import evaluate_effect_size

    rep = _reported(effects=[0.20, -0.20] * 50, padj=[1e-4] * 100)
    f = evaluate_effect_size(make_design(), rep)
    assert (f.status, f.coverage, S.human_state(f)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )


def test_mismatched_effect_scale_contract_abstains():
    from sc_referee.checks.effect_size import evaluate_effect_size

    contract = EffectRelevanceContract(
        claim_type="biologically_relevant_discovery",
        threshold=0.25,
        threshold_scale="log2_fold_change",
        reported_effect_scale="natural_log_fold_change",
    )
    f = evaluate_effect_size(
        make_design(effect_relevance_contract=contract),
        _reported(effects=[0.01, -0.02] * 50, padj=[1e-4] * 100),
    )
    assert (f.status, f.coverage, S.human_state(f)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )


def test_bound_relevance_contract_retains_true_positive_major():
    from sc_referee.checks.effect_size import evaluate_effect_size

    contract = EffectRelevanceContract(
        claim_type="biologically_relevant_discovery",
        threshold=0.25,
        threshold_scale="log2_fold_change",
        reported_effect_scale="log2_fold_change",
    )
    rep = _reported(effects=[0.01, -0.02, 0.03, -0.01] * 25, padj=[1e-4] * 100)
    f = evaluate_effect_size(make_design(effect_relevance_contract=contract), rep)
    assert f.status == S.MAJOR
    assert f.judgment == S.CONCERN
    assert f.metrics["threshold_log2fc"] == 0.25
    assert "declared" in f.verdict.lower()


def test_no_effect_column_cannot_be_assessed():
    from sc_referee.checks.effect_size import evaluate_effect_size

    rep = pd.DataFrame({"feature_id": ["g0", "g1"], "pvalue": [1e-3, 1e-3],
                        "padj": [1e-3, 1e-3], "effect": [np.nan, np.nan]})
    finding = evaluate_effect_size(make_design(), rep)
    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == "not_checked"


def test_missing_effect_or_significance_columns_are_not_checked_coverage_gaps():
    from sc_referee.checks.effect_size import evaluate_effect_size

    no_effect = pd.DataFrame({"feature_id": ["g0"], "pvalue": [0.01]})
    no_significance = pd.DataFrame({"feature_id": ["g0"], "effect": [1.0]})

    findings = [
        evaluate_effect_size(make_design(), no_effect),
        evaluate_effect_size(make_design(), no_significance),
    ]
    assert [(f.status, f.coverage, S.human_state(f)) for f in findings] == [
        (S.NEEDS_EVIDENCE, S.NOT_RUN, "not_checked"),
        (S.NEEDS_EVIDENCE, S.NOT_RUN, "not_checked"),
    ]


def test_nothing_significant_passes():
    from sc_referee.checks.effect_size import evaluate_effect_size

    rep = _reported(effects=[0.01, 0.02, 0.03], padj=[0.9, 0.8, 0.7])
    assert evaluate_effect_size(make_design(), rep).status == S.PASS


def test_policy_only_descriptive_minority_is_a_clear_non_defect():
    from sc_referee.checks.effect_size import evaluate_effect_size

    rep = _reported(effects=[0.01] + [1.0] * 9, padj=[1e-4] * 10)
    finding = evaluate_effect_size(make_design(), rep)
    assert (finding.status, finding.coverage, finding.judgment, S.human_state(finding)) == (
        S.INFORMATIONAL, S.COMPLETE, None, S.CLEAR
    )


def test_reachable_from_registry_and_carries_a_citation():
    from sc_referee.citations import CITATIONS
    from sc_referee.registry import build_checks

    assert "effect_size_threshold" in {c.id for c in build_checks("pydeseq2")}
    assert CITATIONS.get("effect_size_threshold")


def test_block_entitlement_is_major_never_blocker():
    from sc_referee.checks.effect_size import EffectSizeCheck

    assert EffectSizeCheck().max_status == S.MAJOR
