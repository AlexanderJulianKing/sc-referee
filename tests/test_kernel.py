"""Unit and frozen-oracle parity tests for the functional-dependency micro-kernel."""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd
import pytest

from sc_referee import statuses as S
from sc_referee.bundle import Bundle, Measure
from sc_referee.checks.base import Finding
from sc_referee.citations import CITATIONS
from sc_referee.design import apply_subset, confidence_high
from sc_referee.kernel import (
    FunctionalDependencyRule,
    FunctionalDependencySpec,
    OffendingGroup,
    ProofState,
)
from tests.factories import make_design, paired_crossed_obs, unpaired_crossed_obs


RULE = FunctionalDependencyRule()


def _spec(det=("key",), dep=("value",), maximum=1):
    return FunctionalDependencySpec(tuple(det), tuple(dep), maximum)


def test_functional_dependency_violation():
    result = RULE.evaluate(pd.DataFrame({"key": ["A", "A"], "value": [1, 2]}), _spec())
    assert result.state is ProofState.PROVED_VIOLATION
    assert result.violation_count == 1
    assert result.offending_groups == (OffendingGroup(("A",), 2),)


def test_functional_dependency_conformant():
    result = RULE.evaluate(pd.DataFrame({"key": ["A", "B"], "value": [1, 2]}), _spec())
    assert result.state is ProofState.PROVED_CONFORMANT
    assert result.violation_count == 0


def test_empty_complete_relation_is_conformant():
    result = RULE.evaluate(pd.DataFrame(columns=["key", "value"]), _spec())
    assert result.state is ProofState.PROVED_CONFORMANT
    assert result.coverage_complete


def test_values_are_not_string_coerced():
    result = RULE.evaluate(pd.DataFrame({"key": ["A", "A"], "value": [1, "1"]}), _spec())
    assert result.state is ProofState.PROVED_VIOLATION
    assert result.offending_groups[0].distinct_dependents == 2


def test_tuple_valued_scalar_determinant_is_not_flattened():
    key = ("donor", "visit")
    result = RULE.evaluate(pd.DataFrame({"key": [key, key], "value": [1, 2]}), _spec())
    assert result.offending_groups == (OffendingGroup((key,), 2),)


def test_multi_column_dependent_identity_is_counted_as_a_tuple():
    table = pd.DataFrame({
        "key": ["A", "A", "A"],
        "left": [1, 1, 2],
        "right": ["x", "y", "x"],
    })
    result = RULE.evaluate(table, _spec(dep=("left", "right"), maximum=2))
    assert result.state is ProofState.PROVED_VIOLATION
    assert result.offending_groups == (OffendingGroup(("A",), 3),)


def test_duplicate_rows_are_idempotent():
    table = pd.DataFrame({"key": ["A", "A", "A"], "value": [1, 1, 2]})
    result = RULE.evaluate(table, _spec())
    assert result.offending_groups == (OffendingGroup(("A",), 2),)


def test_missing_column_is_unresolved():
    result = RULE.evaluate(pd.DataFrame({"key": ["A"]}), _spec())
    assert result.state is ProofState.UNRESOLVED
    assert not result.coverage_complete
    assert result.missing_fields == ("value",)


def test_residual_null_is_unresolved_not_dropped():
    result = RULE.evaluate(pd.DataFrame({"key": ["A", np.nan], "value": [1, 2]}), _spec())
    assert result.state is ProofState.UNRESOLVED
    assert result.reason == "null_in_referenced_columns"


def test_categorical_grouping_uses_observed_levels_only():
    table = pd.DataFrame({
        "key": pd.Categorical(["A", "A"], categories=["unused", "A", "also_unused"]),
        "value": [1, 2],
    })
    result = RULE.evaluate(table, _spec())
    assert result.offending_groups == (OffendingGroup(("A",), 2),)


def test_offending_groups_follow_first_appearance_order():
    table = pd.DataFrame({
        "key": ["B", "A", "B", "A", "C", "C"],
        "value": [1, 1, 2, 2, 1, 2],
    })
    result = RULE.evaluate(table, _spec())
    assert [g.determinant_values for g in result.offending_groups] == [("B",), ("A",), ("C",)]


# ---------------------------------------------------------------------------
# Frozen legacy reference — copied from the pre-kernel arithmetic at d226552.
# It lives only in tests and is deliberately independent of the new relation preparation.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _LegacyOutcome:
    category: str  # not_applicable | unresolved | conformant | violation
    offending_groups: tuple[tuple[object, ...], ...] = ()

    @property
    def violation_count(self):
        return len(self.offending_groups)


def _key_tuple(key):
    return key if isinstance(key, tuple) else (key,)


def _typed_groups(groups):
    """Comparison signature that distinguishes, for example, integer 1 from string '1'."""
    return tuple(tuple((type(value), value) for value in group) for group in groups)


def _legacy_merge_outcome(design, bundle):
    from sc_referee.checks.pseudobulk_integrity import _countmodel_uses

    obs = bundle.observations
    declared = list(design.aggregation_key or [])
    if not declared or not _countmodel_uses(bundle):
        return _LegacyOutcome("not_applicable")
    if any(k not in obs.columns for k in declared):
        return _LegacyOutcome("unresolved")
    contrast_col, ref, test = design.contrast_column_and_levels()
    if contrast_col in declared or contrast_col not in obs.columns or ref == test:
        return _LegacyOutcome("not_applicable")
    sub = apply_subset(obs, design)
    work = sub[[contrast_col, *declared]].copy()
    work["_ref"] = (sub[contrast_col] == ref).to_numpy()
    work["_test"] = (sub[contrast_col] == test).to_numpy()
    work = work[work["_ref"] | work["_test"]]
    if work.empty:
        return _LegacyOutcome("conformant")
    grouped = work.groupby(declared, observed=True)
    spans = grouped["_ref"].any() & grouped["_test"].any()
    groups = tuple(_key_tuple(key) for key, fires in spans.items() if bool(fires))
    return _LegacyOutcome("violation" if groups else "conformant", groups)


def _new_merge_outcome(design, bundle):
    from sc_referee.checks.pseudobulk_integrity import _countmodel_uses, _merge_dependency_proof

    obs = bundle.observations
    declared = list(design.aggregation_key or [])
    if not declared or not _countmodel_uses(bundle):
        return _LegacyOutcome("not_applicable")
    if any(k not in obs.columns for k in declared):
        return _LegacyOutcome("unresolved")
    contrast_col, ref, test = design.contrast_column_and_levels()
    if contrast_col in declared or contrast_col not in obs.columns or ref == test:
        return _LegacyOutcome("not_applicable")
    proof = _merge_dependency_proof(apply_subset(obs, design), declared, contrast_col, ref, test)
    if proof.state is ProofState.UNRESOLVED:
        return _LegacyOutcome("unresolved")
    groups = tuple(group.determinant_values for group in proof.offending_groups)
    return _LegacyOutcome("violation" if groups else "conformant", groups)


def _legacy_merge_finding(design, bundle, cites):
    """Frozen pre-kernel `_merge_finding`, including its exact user-facing Finding."""
    from sc_referee.checks.pseudobulk_integrity import _countmodel_uses

    obs = bundle.observations
    declared = list(design.aggregation_key or [])
    if not declared or not _countmodel_uses(bundle):
        return None
    missing = [k for k in declared if k not in obs.columns]
    if missing:
        return Finding("pseudobulk_integrity", S.NEEDS_EVIDENCE,
                       f"the ratified aggregation key {declared} names column(s) absent from .obs "
                       f"({missing}); the actual pseudobulk grouping cannot be reconstructed, so the "
                       f"merge check did not run.", metrics={"aggregation_key": declared}, citations=cites)
    contrast_col, ref, test = design.contrast_column_and_levels()
    if contrast_col in declared or contrast_col not in obs.columns or ref == test:
        return None
    sub = apply_subset(obs, design)
    work = sub[[contrast_col, *declared]].copy()
    work["_ref"] = (sub[contrast_col] == ref).to_numpy()
    work["_test"] = (sub[contrast_col] == test).to_numpy()
    work = work[work["_ref"] | work["_test"]]
    if work.empty:
        return None
    grouped = work.groupby(declared, observed=True)
    n_merged = int((grouped["_ref"].any() & grouped["_test"].any()).sum())
    if not n_merged:
        return None
    blocker_allowed = design.confirmed_by_human and confidence_high(design, "aggregation_key")
    note = "" if blocker_allowed else (" — but the aggregation key is not human-confirmed / low "
                                       "confidence, so no blocker is asserted.")
    return Finding(
        "pseudobulk_integrity", S.BLOCKER if blocker_allowed else S.NEEDS_EVIDENCE,
        f"{n_merged} pseudobulk sample(s) aggregate cells from BOTH the {ref} and {test} arms: the "
        f"confirmed aggregation key {declared} excludes the contrast column {contrast_col!r}, so each "
        f"such sample mixes the two conditions and the DE contrast is applied to mislabeled samples — the "
        f"comparison is structurally invalid regardless of biology. Aggregate by a key that includes "
        f"{contrast_col!r}." + note,
        metrics={"aggregation_key": declared, "contrast": contrast_col, "merged_samples": n_merged},
        citations=cites)


def _legacy_pseudobulk_finding(design, bundle):
    from sc_referee.checks.pseudobulk_integrity import evaluate_pseudobulk_integrity

    merge = _legacy_merge_finding(design, bundle, CITATIONS["pseudobulk_integrity"])
    if merge is not None:
        return merge
    # aggregation_key is used only by the replaced merge invariant.  Disabling it reaches the unchanged
    # assay/key-integrity tail and gives the exact legacy Finding for non-merge cases.
    return evaluate_pseudobulk_integrity(replace(design, aggregation_key=None), bundle)


def _legacy_pairing_outcome(design, bundle):
    obs = bundle.observations
    pairing = list(design.pairing_unit or [])
    agg = list(design.aggregation_key or [])
    if not pairing or not agg:
        return _LegacyOutcome("not_applicable")
    if any(c not in obs.columns for c in agg + pairing):
        return _LegacyOutcome("not_applicable")
    contrast_col, ref, test = design.contrast_column_and_levels()
    if not (set(pairing) <= set(agg)) or contrast_col not in agg or contrast_col not in obs.columns \
            or ref == test:
        return _LegacyOutcome("not_applicable")
    sub = apply_subset(obs, design)
    arms = sub[(sub[contrast_col] == ref) | (sub[contrast_col] == test)]
    arms = arms.dropna(subset=agg)
    if arms.empty:
        return _LegacyOutcome("not_applicable")
    samples = arms[agg].drop_duplicates()
    n_per_arm = samples.groupby([*pairing, contrast_col], observed=True).size().reset_index(name="_n")
    arms_per_level = (samples.groupby(pairing, observed=True)[contrast_col].nunique()
                      .reset_index(name="_arms"))
    merged = n_per_arm.merge(arms_per_level, on=pairing)
    violating = merged[(merged["_n"] > 1) & (merged["_arms"] == 2)]
    groups = tuple(tuple(row[c] for c in [*pairing, contrast_col])
                   for _, row in violating.iterrows())
    return _LegacyOutcome("violation" if groups else "conformant", groups)


def _new_pairing_outcome(design, bundle):
    from sc_referee.checks.pairing import _duplicated_pairing

    proof = _duplicated_pairing(design, bundle)
    if proof is None:
        return _LegacyOutcome("not_applicable")
    if proof.state is ProofState.UNRESOLVED:
        return _LegacyOutcome("unresolved")
    groups = tuple(group.determinant_values for group in proof.offending_groups)
    return _LegacyOutcome("violation" if groups else "conformant", groups)


def _legacy_pairing_finding(design, bundle):
    """Frozen pre-kernel `evaluate_pairing`; its duplicated-pairing arithmetic is the frozen
    `_legacy_pairing_outcome` above (NOT the production `_duplicated_pairing`), so this oracle stays
    independent of the new kernel path."""
    from sc_referee.checks.pairing import _pair_spans

    cites = CITATIONS["pairing"]
    key, complete, incomplete = _pair_spans(design, bundle)
    if key is None:
        return Finding("pairing", S.PASS, "no pairing key is available to assess (no replicate/pairing "
                       "column in .obs).", citations=cites)
    metrics = {"pairing_key": key, "complete_pairs": complete, "unmatched_levels": incomplete}

    if not design.pairing_unit:
        if complete >= 1:
            return Finding("pairing", S.NEEDS_EVIDENCE,
                           f"the model is unpaired, but {complete} level(s) of {key} appear in BOTH arms "
                           f"— the data is paired-capable. Ignoring the within-subject structure can be "
                           f"inefficient or anti-conservative; consider a paired/mixed sensitivity fit.",
                           metrics=metrics, citations=cites)
        return Finding("pairing", S.PASS, f"the design is genuinely unpaired: no level of {key} spans "
                       f"both arms, so an unpaired model is appropriate.", metrics=metrics, citations=cites)

    outcome = _legacy_pairing_outcome(design, bundle)
    dup = outcome.violation_count
    if dup:
        within_pair = design.pairing_estimand == "within_pair"
        one_to_one = design.pairing_mechanics == "one_to_one"
        blocker_allowed = (design.confirmed_by_human and confidence_high(design, "aggregation_key")
                           and within_pair and one_to_one)
        if blocker_allowed:
            note = ""
        elif not within_pair:
            note = (" — but the analysis is not confirmed as a one-to-one paired estimand "
                    "(`pairing_estimand: within_pair`); a mixed/repeated-measures model may handle this, "
                    "so it is flagged for review, not blocked.")
        else:
            note = " — but the aggregation key is not human-confirmed / low confidence, so no blocker."
        return Finding(
            "pairing", S.BLOCKER if blocker_allowed else S.NEEDS_EVIDENCE,
            f"{dup} complete pairing level(s) map to MORE THAN ONE pseudobulk sample in an arm under the "
            f"confirmed aggregation key {list(design.aggregation_key)}: the one-to-one pairing on {key} "
            f"is ambiguous (which sample in one arm pairs with which in the other?). Aggregate to exactly "
            f"one sample per (pairing level, arm), or model the extra structure explicitly." + note,
            metrics={"pairing_key": key, "ambiguous_pairs": dup,
                     "aggregation_key": list(design.aggregation_key or []),
                     "pairing_estimand": design.pairing_estimand,
                     "pairing_mechanics": design.pairing_mechanics}, citations=cites,
            coverage=S.COMPLETE if blocker_allowed else S.NOT_RUN)

    if complete == 0:
        return Finding("pairing", S.NEEDS_EVIDENCE,
                       f"the paired key {key} yields NO complete pairs across the two arms — the paired "
                       f"contrast cannot be formed (see the confounding check for the rank deficiency).",
                       metrics=metrics, citations=cites)
    if incomplete:
        return Finding("pairing", S.INFORMATIONAL,
                       f"{complete} complete pair(s); {incomplete} level(s) of {key} appear in only one "
                       f"arm and cannot contribute to the within-pair contrast (a paired method drops "
                       f"them).", metrics=metrics, citations=cites)
    return Finding("pairing", S.PASS, f"paired design is well-formed: {complete} complete pairs across "
                   f"the two arms.", metrics=metrics, citations=cites)


_DDS = ("from pydeseq2.dds import DeseqDataSet\n"
        "dds = DeseqDataSet(counts=pb, metadata=m, design='~condition')\n")


def _pseudobulk_bundle(obs, *, countmodel=True):
    genes = ["g1", "g2"]
    bundle = Bundle(observations=obs, measure=Measure("counts", np.ones((len(obs), 2), dtype="int64"),
                                                     None, genes),
                    feature_metadata=pd.DataFrame(index=genes), replicate_var="donor_id")
    source = _DDS if countmodel else "from scipy.stats import ttest_ind\nttest_ind(a, b)\n"
    bundle.code_signals = {"sources": [source], "de_calls": ["deseqdataset"], "files": ["de.py"]}
    return bundle


def _pairing_bundle(obs):
    genes = ["g1", "g2"]
    return Bundle(observations=obs, measure=Measure("counts", np.ones((len(obs), 2), dtype="int64"),
                                                    None, genes),
                  feature_metadata=pd.DataFrame(index=genes), replicate_var="donor_id")


def _merge_cases():
    mixed = pd.DataFrame({"donor_id": ["D1", "D1", "D2", "D2"],
                          "condition": [1, 1, "1", "1"]})
    null_key = pd.DataFrame({
        "donor_id": ["D1", "D1", "D2", "D3"],
        "condition": ["ctrl", "stim", "ctrl", "stim"],
        "batch": [np.nan, np.nan, "b1", "b1"],
    })
    composite = pd.DataFrame({
        "donor_id": ["D1", "D1", "D2", "D3"],
        "condition": ["ctrl", "stim", "ctrl", "stim"],
        "cell_type": ["T", "T", "T", "T"],
    })
    categorical = pd.DataFrame({
        "donor_id": pd.Categorical(["D1", "D1"], categories=["unused", "D1"]),
        "condition": pd.Categorical(["ctrl", "stim"], categories=["ctrl", "stim", "other"]),
    })
    return [
        ("merged", make_design(unit_of_test="sample", sample_unit=["donor_id"],
                               aggregation_key=["donor_id"]), paired_crossed_obs(), True),
        ("contrast_in_key", make_design(unit_of_test="sample", sample_unit=["donor_id"],
                                        aggregation_key=["donor_id", "condition"]),
         paired_crossed_obs(), True),
        ("between_subject", make_design(unit_of_test="sample", sample_unit=["donor_id"],
                                        aggregation_key=["donor_id"]), unpaired_crossed_obs(), True),
        ("unconfirmed", make_design(unit_of_test="sample", sample_unit=["donor_id"],
                                    aggregation_key=["donor_id"], confirmed=False),
         paired_crossed_obs(), True),
        ("missing_key", make_design(unit_of_test="sample", sample_unit=["donor_id"],
                                    aggregation_key=["donor_id", "arm_alias"]),
         paired_crossed_obs(), True),
        ("mixed_values", make_design(unit_of_test="sample", sample_unit=["donor_id"],
                                     aggregation_key=["donor_id"], reference=1, test="1"), mixed, True),
        ("null_key", make_design(unit_of_test="sample", sample_unit=["donor_id"],
                                 aggregation_key=["donor_id", "batch"]), null_key, True),
        ("composite", make_design(unit_of_test="sample", sample_unit=["donor_id"],
                                  aggregation_key=["donor_id", "cell_type"]), composite, True),
        ("categorical", make_design(unit_of_test="sample", sample_unit=["donor_id"],
                                    aggregation_key=["donor_id"]), categorical, True),
        ("no_countmodel", make_design(unit_of_test="sample", sample_unit=["donor_id"],
                                      aggregation_key=["donor_id"]), paired_crossed_obs(), False),
    ]


def _pairing_cases():
    duplicate = pd.DataFrame({
        "donor_id": ["D1", "D1", "D1", "D2", "D2", "D2"],
        "condition": ["ctrl", "ctrl", "stim", "ctrl", "ctrl", "stim"],
        "batch": ["b1", "b2", "b1", "b1", "b2", "b1"],
    })
    unmatched = pd.DataFrame({
        "donor_id": ["D1", "D1", "D2", "D2", "D3", "D3", "D4", "D4"],
        "condition": ["ctrl", "stim", "ctrl", "stim", "ctrl", "stim", "ctrl", "ctrl"],
        "batch": ["b1", "b1", "b1", "b1", "b1", "b1", "b1", "b2"],
    })
    null_key = pd.DataFrame({"donor_id": ["D1", "D1", "D1"],
                             "condition": ["ctrl", "ctrl", "stim"],
                             "batch": ["b1", np.nan, "b1"]})
    lanes = pd.DataFrame({
        "donor_id": ["D1"] * 4 + ["D2"] * 4,
        "condition": ["ctrl", "ctrl", "stim", "stim"] * 2,
        "lane": ["L1", "L2", "L1", "L2"] * 2,
    })
    composite = pd.DataFrame({
        "donor_id": ["D1", "D1", "D1", "D1"],
        "site": ["A", "A", "A", "A"],
        "condition": ["ctrl", "ctrl", "stim", "stim"],
        "batch": ["b1", "b2", "b1", "b1"],
    })
    both_duplicated = pd.DataFrame({
        "donor_id": ["D1"] * 4,
        "condition": ["ctrl", "ctrl", "stim", "stim"],
        "batch": ["b1", "b2", "b1", "b2"],
    })
    categorical_mixed = pd.DataFrame({
        "donor_id": pd.Categorical(["D1"] * 4, categories=["unused", "D1"]),
        "condition": [1, 1, "1", "1"],
        "batch": pd.Categorical(["b1", "b2", "b1", "b2"], categories=["b1", "b2", "unused"]),
    })
    partial = paired_crossed_obs()
    partial = partial[~((partial["donor_id"] == "D4") & (partial["condition"] == "stim"))]
    unpaired = replace(make_design(unit_of_test="sample"), pairing_unit=[])
    return [
        ("duplicate", make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                                  aggregation_key=["donor_id", "condition", "batch"],
                                  pairing_estimand="within_pair",
                                  pairing_mechanics="one_to_one"), duplicate),
        ("no_estimand", make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                                    aggregation_key=["donor_id", "condition", "batch"]), duplicate),
        ("unmatched_duplicate", make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                                            aggregation_key=["donor_id", "condition", "batch"],
                                            pairing_estimand="within_pair"), unmatched),
        ("null_key", make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                                 aggregation_key=["donor_id", "condition", "batch"],
                                 pairing_estimand="within_pair"), null_key),
        ("one_sample", make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                                   aggregation_key=["donor_id", "condition"],
                                   pairing_estimand="within_pair"), paired_crossed_obs()),
        ("two_stage", make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                                  aggregation_key=["donor_id", "condition"],
                                  pairing_estimand="within_pair"), lanes),
        ("unconfirmed", make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                                    aggregation_key=["donor_id", "condition", "batch"],
                                    pairing_estimand="within_pair", pairing_mechanics="one_to_one",
                                    confirmed=False), duplicate),
        ("no_aggregation", make_design(unit_of_test="sample", pairing_unit=["donor_id"]),
         paired_crossed_obs()),
        ("composite", make_design(unit_of_test="sample", pairing_unit=["donor_id", "site"],
                                  aggregation_key=["donor_id", "site", "condition", "batch"],
                                  pairing_estimand="within_pair",
                                  pairing_mechanics="one_to_one"), composite),
        ("both_arms_duplicated", make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                                             aggregation_key=["donor_id", "condition", "batch"],
                                             pairing_estimand="within_pair",
                                             pairing_mechanics="one_to_one"), both_duplicated),
        ("categorical_mixed", make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                                          aggregation_key=["donor_id", "condition", "batch"],
                                          pairing_estimand="within_pair", pairing_mechanics="one_to_one",
                                          reference=1, test="1"),
         categorical_mixed),
        ("unpaired_capable", unpaired, paired_crossed_obs()),
        ("genuinely_unpaired", unpaired, unpaired_crossed_obs()),
        ("partial", make_design(unit_of_test="sample", pairing_unit=["donor_id"]), partial),
    ]


@pytest.mark.parametrize("name,design,obs,countmodel", _merge_cases(),
                         ids=lambda value: value if isinstance(value, str) else None)
def test_pseudobulk_merge_kernel_matches_frozen_legacy(name, design, obs, countmodel):
    from sc_referee.checks.pseudobulk_integrity import evaluate_pseudobulk_integrity

    bundle = _pseudobulk_bundle(obs, countmodel=countmodel)
    legacy = _legacy_merge_outcome(design, bundle)
    current = _new_merge_outcome(design, bundle)
    assert current.category == legacy.category
    assert current.violation_count == legacy.violation_count
    assert _typed_groups(current.offending_groups) == _typed_groups(legacy.offending_groups)
    # Behavior parity: the merge OUTCOME (category/violation/offending, asserted above) plus the
    # Finding's behavioral fields (status, metrics) must match the pre-kernel legacy. Verdict TEXT is
    # intentionally evolving (the plain-language voice rollout) and is pinned by
    # tests/test_pseudobulk_integrity.py; `coverage` is an InitVar excluded from Finding equality and
    # legitimately differs between the with-key and no-key design variants.
    cur, leg = (evaluate_pseudobulk_integrity(design, bundle),
                _legacy_pseudobulk_finding(design, bundle))
    assert (cur.status, cur.metrics) == (leg.status, leg.metrics)


@pytest.mark.parametrize("name,design,obs", _pairing_cases(),
                         ids=lambda value: value if isinstance(value, str) else None)
def test_pairing_kernel_matches_frozen_legacy(name, design, obs):
    from sc_referee.checks.pairing import evaluate_pairing

    bundle = _pairing_bundle(obs)
    legacy = _legacy_pairing_outcome(design, bundle)
    current = _new_pairing_outcome(design, bundle)
    assert current.category == legacy.category
    assert current.violation_count == legacy.violation_count
    assert _typed_groups(current.offending_groups) == _typed_groups(legacy.offending_groups)
    # Behavior parity with the pre-kernel legacy: status, coverage, and metrics must match exactly.
    # Verdict TEXT is presentation and is intentionally allowed to evolve (the plain-language voice
    # rollout); its content is pinned by the per-check tests in test_pairing.py, not this guard.
    cur, leg = evaluate_pairing(design, bundle), _legacy_pairing_finding(design, bundle)
    assert (cur.status, cur.coverage, cur.metrics) == (leg.status, leg.coverage, leg.metrics)
