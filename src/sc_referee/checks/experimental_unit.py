"""The `experimental_unit` check (pseudoreplication) — recompute, don't opine.

Aggregates cells to the pseudobulk sample_unit, re-runs the replicate-aware test, and
applies the earned-verdict rule. A `blocker` is emitted ONLY when a powered recompute of
the *claimed discoveries* collapses — otherwise the tool abstains (needs_evidence) or
advises (major). `--engine simple` may never block (capped here); the `pydeseq2` engine
is the one that can gate CI.
"""
from __future__ import annotations

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.checks.confounding import covariates_constant_within_sample_unit
from sc_referee.citations import CITATIONS
from sc_referee.design import Design, apply_subset, confidence_high, replicate_recorded
from sc_referee.engine import (
    aggregate_to_pseudobulk,
    build_panel,
    earned_verdict,
    simple_recompute,
)

CHECK_ID = "experimental_unit"


def _cols(names) -> str:
    """Column names as plain English, never a ['list'] literal — the reader may be auditing
    agentically-generated code and not recognize their own variable names."""
    names = [str(n) for n in names]
    if not names:
        return "the sample grouping"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def marker_unit_concern_is_proved(design: Design, bundle) -> bool:
    """Whether a marker workflow is structurally entitled to the unit/pairing cross-route.

    This is deliberately an allowlist for the newly widened surface.  The exact parsed sink must be
    per-cell; the report and human-ratified replicate role must exist; and the declared contrast must
    actually vary within at least one exact replicate key after applying the declared subset.
    """
    reported = getattr(bundle, "reported_results", None) if bundle is not None else None
    if (design.analysis_type != "marker_detection"
            or not design.confirmed_by_human
            or not confidence_high(design, "replicate_unit")
            or design.unit_of_test != "cell"
            or bundle is None
            or reported is None
            or not hasattr(reported, "__len__")
            or len(reported) == 0
            or not replicate_recorded(design, getattr(bundle, "observations", None))):
        return False

    # The pseudoreplication finding is earned by a replicate-aware recompute that aggregates RAW
    # counts to pseudobulk (aggregate_to_pseudobulk reads bundle.measure.counts, which is None on
    # the normalized path). Raw counts are therefore a precondition of this cross-route: without
    # them the check cannot be established, so it does NOT apply (never apply-and-guess). The legacy
    # condition_contrast_DE route enforces the same via cannot_evaluate; the marker route bypasses
    # cannot_evaluate (analysis_type is not in its analysis_types), so the guard belongs here.
    measure = getattr(bundle, "measure", None)
    if measure is not None and getattr(measure, "kind", "counts") != "counts":
        return False

    from sc_referee.code_signals import resolve_unit_of_test
    if resolve_unit_of_test(getattr(bundle, "code_signals", {}) or {}) != "cell":
        return False

    contrast_col, reference, test = design.contrast_column_and_levels()
    if contrast_col is None or reference == test:
        return False
    try:
        observations = apply_subset(bundle.observations, design)
    except (KeyError, ValueError):
        return False
    replicate = list(design.replicate_unit or ())
    if contrast_col not in observations.columns or not all(
            column in observations.columns for column in replicate):
        return False

    relevant = observations[
        (observations[contrast_col] == reference) | (observations[contrast_col] == test)
    ]
    present = set(relevant[contrast_col].dropna().unique())
    if reference not in present or test not in present:
        return False
    spans = relevant.groupby(replicate, sort=False, observed=True)[contrast_col].nunique()
    return bool((spans > 1).any())


def _reported_alpha(design: Design, default: float = 0.05) -> float:
    return default  # reported threshold; wired to the confirmed threshold when present


def evaluate_experimental_unit(design: Design, bundle, reported, engine: str = "pydeseq2",
                               recompute=None) -> Finding:
    """`recompute` lets a caller inject an already-computed RecomputeResult. The recompute
    depends only on (bundle, design) — never on the reported table — so the benchmark can
    audit two different reported analyses against one recompute instead of redoing it."""
    inference_contract = design.report_inference_contract
    iid_producer_bound = bool(
        design.confirmed_by_human
        and inference_contract is not None
        and inference_contract.producer_binding == "exact"
        and inference_contract.dependence_semantics == "iid_rows"
    )
    blocking_allowed = iid_producer_bound and confidence_high(design, "replicate_unit")
    citations = CITATIONS[CHECK_ID]

    cov_ok, offending = covariates_constant_within_sample_unit(bundle.observations, design)
    if not cov_ok:
        return Finding(CHECK_ID, S.NEEDS_EVIDENCE,
                       f"a variable your model adjusts for ({offending}) takes more than one value "
                       f"inside a single sample, so I can't collapse the cells into one clean "
                       f"value-per-sample to test — I did NOT check pseudoreplication here. Make "
                       f"{offending} constant within each sample (or drop it from the design) and "
                       f"re-run.", citations=citations, coverage=S.NOT_RUN)

    # The CONTRAST must also be constant within a sample unit, else aggregation would sum ctrl and
    # stim cells into one pseudobulk sample and label it by whichever cell came first. Abstain
    # rather than recompute nonsense. (Codex review 2026-07-08.)
    obs = bundle.observations
    contrast_col, _, _ = design.contrast_column_and_levels()
    keys = [c for c in design.sample_unit if c in obs.columns]
    if keys and contrast_col in obs.columns:
        if (obs.groupby(keys, sort=False, observed=True)[contrast_col].nunique() > 1).any():
            return Finding(CHECK_ID, S.NEEDS_EVIDENCE,
                           f"the condition you're comparing ({contrast_col}) varies within the "
                           f"sample unit (the columns that define one sample: {_cols(keys)}) — so "
                           f"combining cells into samples would pool both groups you're comparing "
                           f"into a single sample and label it by whichever cell came first. I did "
                           f"NOT check pseudoreplication. Group samples by a key that keeps each "
                           f"{contrast_col} group in its own sample, then re-run.",
                           citations=citations, coverage=S.NOT_RUN)

    if reported is None or len(reported) == 0:
        return Finding(CHECK_ID, S.NEEDS_EVIDENCE,
                       "I couldn't find a results table in this folder to re-test against, so I did "
                       "NOT run the pseudoreplication check. Add the differential-expression results "
                       "table and re-run.", citations=citations,
                       coverage=S.NOT_RUN)

    if recompute is not None:
        res = recompute
    else:
        pb, meta = aggregate_to_pseudobulk(bundle, design)
        if engine == "pydeseq2":
            from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute
            res = pydeseq2_recompute(pb, meta, design)
        else:
            res = simple_recompute(pb, meta, design)

    panel = build_panel(reported, res, design, bundle, alpha=_reported_alpha(design))
    status, reason = earned_verdict(panel)

    if not iid_producer_bound and not (
            inference_contract is None and status == S.NEEDS_EVIDENCE):
        dependence = (inference_contract.dependence_semantics
                      if inference_contract is not None else "unbound")
        status, reason = S.NEEDS_EVIDENCE, (
            f"I computed a sample-level sensitivity comparison ({panel.survivors} of "
            f"{panel.valid_reported_sig} reported discoveries survived), but the exact report "
            f"producer is not confirmed to use iid cell rows (declared dependence semantics: "
            f"{dependence}). Mixed, GEE, cluster-robust, paired, and other dependence-aware cell-level "
            "models can be valid, so this sensitivity result does not adjudicate the original "
            "covariance model."
        )

    note = ""
    if engine == "simple" and status == S.BLOCKER:
        status = S.MAJOR
        note = (" (heads-up: the quick `simple` engine never issues a hard block — re-run with "
                "--engine pydeseq2 for a verdict that can gate CI)")
    if status == S.BLOCKER and not blocking_allowed:
        status, reason = S.NEEDS_EVIDENCE, (
            "your claimed discoveries don't hold up when I re-test at the sample level, but you "
            "haven't confirmed the design yet (or the replicate column is low-confidence), so I "
            "won't hard-block. Confirm the design (sc-referee confirm) to turn this into a "
            "blocking verdict.")

    metrics = {
        "engine": engine,
        "valid_reported_sig": panel.valid_reported_sig,
        "survivors": panel.survivors,
        "survival_rate": round(panel.survival_rate, 4),
        "powered": panel.powered,
        "powered_fraction": None if panel.powered_fraction is None else round(panel.powered_fraction, 4),
        "n_replicates_per_arm": panel.n_biological_replicates_per_arm,
        "effect_corr": None if panel.effect_corr is None else round(panel.effect_corr, 3),
        "sign_flips": panel.sign_flips,
        "comparable": panel.comparable,
        # Exposed so the report can distinguish the underpower-after-collapse NE (the only case
        # that earns the "critical discrepancy" framing) from the earlier NE gates. Metadata only —
        # the verdict, status, and thresholds are unchanged.
        "covariates_constant": panel.covariates_constant,
        "replicate_recorded": panel.replicate_recorded,
    }
    coverage = S.NOT_RUN if status == S.NEEDS_EVIDENCE else S.COMPLETE
    judgment = {
        S.BLOCKER: S.VIOLATION,
        S.MAJOR: S.CONCERN,
        S.PASS: S.CONFORMANT,
    }.get(status)
    return Finding(CHECK_ID, status, reason + note, metrics=metrics, citations=citations,
                   coverage=coverage, judgment=judgment)


class ExperimentalUnitCheck:
    """Routes from a confirmed cell-level condition/perturbation contrast with a recorded
    replicate var. A valid replicate-aware analysis is NOT excluded by applies_to — it is
    protected by the earned verdict itself (its claims survive -> pass)."""

    id = CHECK_ID
    analysis_types = ("condition_contrast_DE",)
    audit_dimensions = ("unit_of_independence",)
    proof_basis = "independent recompute"
    contract_fields = ("condition", "reference", "test", "replicate_unit", "sample_unit",
                       "unit_of_test", "subset", "report_inference_contract")

    def __init__(self, engine: str = "pydeseq2"):
        self.engine = engine
        # The `simple` engine (paired-t advisory) may NEVER block; only the pydeseq2 NB recompute
        # can earn a blocker. (design doc §9.3.)
        self.max_status = S.BLOCKER if engine == "pydeseq2" else S.MAJOR

    def applies_to(self, design: Design, bundle) -> bool:
        """Fires only on a confirmed cell-level contrast whose replicate is recorded (the confirmed
        design names it and it is in .obs). A report ALREADY at the replicate level has no
        pseudoreplication to correct (C7)."""
        legacy_route = (design.analysis_type in self.analysis_types
                        and design.unit_of_test == "cell"
                        and bundle is not None
                        and replicate_recorded(design, bundle.observations))
        return legacy_route or marker_unit_concern_is_proved(design, bundle)

    def cannot_evaluate(self, design: Design, bundle):
        if design.analysis_type not in self.analysis_types:
            return None                          # genuinely not our business
        if design.unit_of_test is None:
            return ("I couldn't tell whether your test treats each cell or each sample as an "
                    "independent data point (the code doesn't settle it) — and that is exactly the "
                    "pseudoreplication question — so I did NOT check it. State the unit of analysis "
                    "(unit_of_test) in the design and re-run.")
        if design.unit_of_test == "cell":
            if bundle is not None and getattr(bundle.measure, "kind", "counts") != "counts":
                return ("your matrix looks already normalized, not raw whole-number counts, and "
                        "re-testing at the sample level needs the raw counts to add cells up per "
                        "sample — so I did NOT check pseudoreplication. Provide the raw counts in "
                        "layers['counts'] or raw.X and re-run.")
            obs = bundle.observations if bundle is not None else None
            if not replicate_recorded(design, obs):
                return ("this test treats each cell as a data point, but no biological replicate "
                        "(the thing that actually repeats — usually the donor or sample) is "
                        "recorded: replicate_unit is empty or names a column that isn't in the "
                        "data. I did NOT check pseudoreplication. Name the replicate column "
                        "(e.g. donor_id) in sc-referee.yaml and re-run.")
        return None

    def run(self, design: Design, bundle, reported=None) -> Finding:
        return evaluate_experimental_unit(design, bundle, reported, engine=self.engine)
