"""Regression tests for the adversarial review findings (adversarial review, 2026-07-08).

Every one of these was a false verdict, a false claim, or a silent skip. They are pinned here so
they cannot return. Each test names the failure it prevents.
"""
import numpy as np
import pandas as pd
import pytest
from dataclasses import replace

from sc_referee import statuses as S
from sc_referee.audit import AuditResult
from sc_referee.checks.base import Finding
from sc_referee.checks.confounding import evaluate_confounding
from sc_referee.checks.count_model import CountModelCheck
from sc_referee.checks.experimental_unit import ExperimentalUnitCheck
from sc_referee.code_signals import unit_of_test_from
from sc_referee.design import DesignError, validate_design_against
from sc_referee.engine import aggregate_to_pseudobulk
from tests.factories import make_design, paired_count_bundle


# --------------------------------------------------------------------------- #
# A1 — the recompute must see the same cells the design does
# --------------------------------------------------------------------------- #
def test_aggregation_honours_the_design_subset():
    """`confounding` honoured `subset`; `aggregate_to_pseudobulk` did not. Estimability was judged
    on T cells while the recompute ran on ALL cells — grading the analyst against an analysis they
    never performed, on the most common real design (cell-type-specific DE)."""
    bundle = paired_count_bundle(n_donors=4)
    bundle.observations = bundle.observations.assign(
        cell_type=["T"] * (len(bundle.observations) // 2) + ["B"] * (len(bundle.observations) // 2))

    base = make_design(sample_unit=("donor_id", "condition"))
    subset = replace(base, subset={"cell_type": "T"})

    pb_all, _ = aggregate_to_pseudobulk(bundle, base)
    pb_sub, _ = aggregate_to_pseudobulk(bundle, subset)
    assert pb_sub.values.sum() < pb_all.values.sum()      # the subset actually removed cells


# --------------------------------------------------------------------------- #
# A2 — a config error is not a scientific finding
# --------------------------------------------------------------------------- #
def test_a_level_absent_from_the_data_is_a_config_error():
    """`blocker` must mean "your science is wrong", never "your YAML is wrong"."""
    obs = pd.DataFrame({"donor_id": [f"D{i}" for i in range(6)],
                        "condition": ["ctrl", "stim"] * 3})
    good = make_design(batch=(), sample_unit=("donor_id",))
    validate_design_against(obs, good)                    # no raise

    typo = make_design(reference="control", batch=(), sample_unit=("donor_id",))
    with pytest.raises(DesignError, match="reference level 'control' is not present"):
        validate_design_against(obs, typo)


def test_confounding_never_fabricates_metrics():
    obs = pd.DataFrame({"donor_id": [f"D{i}" for i in range(6)], "condition": ["ctrl"] * 6})
    f = evaluate_confounding(obs, make_design(batch=(), sample_unit=("donor_id",)))
    assert f.status == S.NEEDS_EVIDENCE
    assert f.metrics.get("r2") is None and f.metrics.get("vif") is None


# --------------------------------------------------------------------------- #
# A3 — the leakage decision must not depend on nuisance cardinality
# --------------------------------------------------------------------------- #
def test_a_high_cardinality_omitted_batch_is_flagged_despite_a_tiny_lambda():
    """40 runs, 39 of them condition-pure, `run` declared as batch and OMITTED from the model.
    Partial R² ≈ 0.97 — a severe confound. But λ_j ≈ 2/n_levels, so max|λ| ≈ 0.05, UNDER the old
    0.10 cut, and the tool used to answer, in its own voice, "an efficiency cost, not a confound."
    (At 20 runs λ = 0.105 and it squeaked through; the metric was measuring cardinality, not bias.)
    """
    rows = []
    for r in range(40):
        if r < 20:
            conds = ["ctrl", "ctrl"]
        elif r < 39:
            conds = ["stim", "stim"]
        else:
            conds = ["ctrl", "stim"]          # one bridging run
        rows += [(f"D{r}_{k}", c, f"R{r}") for k, c in enumerate(conds)]
    obs = pd.DataFrame(rows, columns=["donor_id", "condition", "run"])

    f = evaluate_confounding(obs, make_design(model="~ condition", batch=("run",),
                                              sample_unit=("donor_id",),
                                              analyst_adjusted_for=["condition"]))
    assert f.metrics["omitted_partial_r2"] > 0.9        # severely confounded
    assert f.metrics["max_leakage"] < 0.10              # ...yet max|λ| is below the OLD cut
    assert f.status == S.MAJOR, f.verdict               # the new statistic catches it
    assert "not a confound" not in f.verdict


# --------------------------------------------------------------------------- #
# A4 — "couldn't look" is not "nothing to look at"
# --------------------------------------------------------------------------- #
def test_unrecorded_replicate_yields_not_audited_not_a_silent_pass():
    """A cell-level analysis whose replicate cannot be identified — the design names none, or names a
    column absent from .obs (e.g. a cohort column `orig.ident` that init never resolved) — must be
    `not_audited`, NEVER a silent pass. (The design is now authoritative: a NAMED replicate present
    in .obs runs even if the adapter's name-heuristic missed it — 2026-07-08.)"""
    bundle = paired_count_bundle(n_donors=4)
    bundle.replicate_var = None
    design = make_design(unit_of_test="cell", replicate_unit=("orig.ident",))   # not a column in .obs

    check = ExperimentalUnitCheck()
    assert check.applies_to(design, bundle) is False        # it cannot run...
    reason = check.cannot_evaluate(design, bundle)
    assert reason and "NOT check" in reason                 # ...and it says so

    result = AuditResult(findings=[Finding("experimental_unit", S.NOT_AUDITED, reason)])
    assert result.fully_audited() is False
    assert result.ci_conclusion() == "neutral"
    assert result.worst_status() != S.PASS


def test_an_unresolved_unit_of_test_is_not_audited():
    bundle = paired_count_bundle(n_donors=4)
    design = make_design(unit_of_test=None)
    assert ExperimentalUnitCheck().cannot_evaluate(design, bundle)
    assert CountModelCheck().cannot_evaluate(design, bundle)


# --------------------------------------------------------------------------- #
# A5 — one broken check must not destroy the report
# --------------------------------------------------------------------------- #
def test_code_bug_surfaces_but_known_optional_dependency_degrades_to_needs_evidence():
    from sc_referee.audit import _safe_run

    class Boom:
        id = "boom"
        def run(self, *a, **k): raise RuntimeError("kaboom")

    class NoDep:
        id = "nodep"
        def run(self, *a, **k):
            raise ModuleNotFoundError("No module named 'pydeseq2'", name="pydeseq2")

    with pytest.raises(RuntimeError, match="kaboom"):
        _safe_run(Boom(), None, None, None)
    f = _safe_run(NoDep(), None, None, None)
    assert f.status == S.NEEDS_EVIDENCE and "--engine simple" in f.verdict


def test_every_registered_check_has_a_hard_mapped_citation():
    """The guard must fire at import, not mid-audit after a pydeseq2 recompute."""
    from sc_referee.citations import CITATIONS
    from sc_referee.registry import CHECKS
    assert {c.id for c in CHECKS} <= set(CITATIONS)


# --------------------------------------------------------------------------- #
# A6 — count_model must be REACHABLE by the routing init actually produces
# --------------------------------------------------------------------------- #
def test_count_model_is_reachable_from_derived_routing():
    """`ttest_ind` was classified as a per-cell call, so a pseudobulk t-test routed to
    `experimental_unit` — whose recompute agrees on the unit and finds nothing. The check built
    for the measured frontier failure could never fire. The discrimination harness hid this by
    injecting `unit_of_test="sample"` instead of deriving it."""
    bundle = paired_count_bundle(n_donors=4)
    bundle.code_signals = {"de_calls": ["pseudobulk", "ttest_ind"]}

    unit = unit_of_test_from(bundle.code_signals)
    assert unit == "sample"

    design = make_design(unit_of_test=unit)
    assert CountModelCheck().applies_to(design, bundle) is True
    assert ExperimentalUnitCheck().applies_to(design, bundle) is False   # not pseudoreplication


# --------------------------------------------------------------------------- #
# B — the benchmark's specificity arm must be able to fail
# --------------------------------------------------------------------------- #
@pytest.mark.filterwarnings("ignore")
def test_the_correct_analysis_arm_is_not_the_recompute_echoed_back():
    """`reported_from_recompute` made survival_rate == 1.0 by identity, so specificity could not
    be anything but 1.0. The correct-unit arm must be an INDEPENDENT replicate-aware estimator."""
    pytest.importorskip("pydeseq2")
    from bench.analyses import bench_design, bundle_from, reported_from_recompute, reported_pseudobulk_ttest
    from bench.muscat_sim import simulate
    from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute

    adata = simulate(n_donors=6, n_genes=300, cells_per_donor=60, frac_DE=0.05, seed=0)
    bundle, design = bundle_from(adata), bench_design()
    pb, meta = aggregate_to_pseudobulk(bundle, design)
    res = pydeseq2_recompute(pb, meta, design)

    echo = reported_from_recompute(res)
    independent = reported_pseudobulk_ttest(pb, meta, design)

    nb_hits = set(res.table.index[(res.table["padj"] <= 0.05) & res.table["testable"].astype(bool)])
    echo_hits = set(echo["feature_id"][echo["padj"] <= 0.05])
    tt_hits = set(independent["feature_id"][independent["padj"] <= 0.05])

    assert echo_hits == nb_hits                 # the echo is an identity — unusable as a measurement
    assert tt_hits != nb_hits                   # the independent estimator genuinely disagrees
    assert len(tt_hits) > 0                     # ...but it is a real, replicate-aware analysis
