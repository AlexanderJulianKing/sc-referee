"""The `count_model` check — right unit, wrong model.

The measured frontier failure. On BiomniBench's `da-17-3` (Perez 2022 SLE, 261 donors),
gpt-5.5 aggregated raw counts per donor CORRECTLY — and then ran OLS on log2(CPM+1) with a
t-test. The judge: *"not a count-based method"*, yielding 2,352 up / 732 down, *"not matching a
proper count-based analysis"*. gpt-5.4 went further and aggregated normalized values.

The unit was right. The model was wrong. `experimental_unit` cannot see this, because the
recompute agrees with the reported result on the *unit* — so nothing collapses.

DETECTION REQUIRES THE CODE. From counts alone, a negative-binomial fit and a t-test on log-CPM
are indistinguishable in the reported table. When no code is present we return `needs_evidence`,
never `pass`: absence of evidence is not a clean bill of health.

Advisory by construction: a t-test on log-CPM is suboptimal, not un-fixable. This check never
emits a `blocker` (the BiomniBench judge graded it "suboptimal but acceptable").
"""
from __future__ import annotations

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.citations import CITATIONS
from sc_referee.code_signals import COUNT_METHODS, NON_COUNT_TESTS
from sc_referee.design import Design
from sc_referee.engine import aggregate_to_pseudobulk

CHECK_ID = "count_model"
ALPHA = 0.05


def _f(status, verdict, *, coverage=S.COMPLETE, judgment=None, **metrics) -> Finding:
    if judgment is None:
        judgment = {S.MAJOR: S.CONCERN, S.PASS: S.CONFORMANT}.get(status)
    return Finding(CHECK_ID, status, verdict, metrics=metrics, citations=CITATIONS[CHECK_ID],
                   coverage=coverage, judgment=judgment)


def _methods(bundle):
    de = {str(c).lower() for c in (bundle.code_signals or {}).get("de_calls", [])}
    return sorted(de & set(COUNT_METHODS)), sorted(de & set(NON_COUNT_TESTS))


def evaluate_count_model(design: Design, bundle, reported, engine: str = "pydeseq2") -> Finding:
    if reported is None or len(reported) == 0:
        return _f(S.NEEDS_EVIDENCE, "I couldn't find a results table in this folder to check against",
                  coverage=S.NOT_RUN)

    if not (bundle.code_signals or {}).get("de_calls"):
        # NB the trigger is "no differential-expression test call was recognized", which is NOT the
        # same as "no code" — code can be present without a test call we recognize. Say which.
        has_code = bool((bundle.code_signals or {}).get("files"))
        where = ("your analysis code, but no differential-expression test in it that I recognize"
                 if has_code else "your results table, but no analysis code")
        return _f(S.NEEDS_EVIDENCE,
                  f"I found {where} — so I can't tell which statistical method produced these "
                  f"differential-expression numbers, and it matters. A method built for count data "
                  f"(like DESeq2) and a generic one (a t-test on log-normalized values) can disagree, "
                  f"sometimes misleadingly, yet look identical in a results table. Add the analysis "
                  f"code that ran the test (a .py or .R file) so I can check the method.",
                  coverage=S.NOT_RUN)

    count_methods, non_count = _methods(bundle)
    contract = design.report_inference_contract
    if contract is not None and contract.response_scale in (
            "transformed_continuous", "normalized_continuous"):
        return _f(
            S.NEEDS_EVIDENCE,
            "the exact report producer is declared on a continuous transformed response. A Gaussian, "
            "voom, or other adequately specified continuous analysis is not categorically incompatible "
            "with that scale, so the negative-binomial sensitivity recompute is diagnostic only",
            coverage=S.NOT_RUN,
            response_scale=contract.response_scale,
            method_family=contract.method_family,
        )
    if count_methods and non_count:
        # The code mentions both. We cannot tell which produced the reported table, and a
        # stray `import pydeseq2` must not launder a t-test into a pass. (adversarial review.)
        return _f(S.NEEDS_EVIDENCE,
                  f"your code uses both a proper count model ({', '.join(count_methods)}) and a "
                  f"method that isn't one ({', '.join(non_count)}), and I can't tell from the code "
                  f"which produced your results table. Make sure the reported numbers come from the "
                  f"count model, or point me at the exact script that generated them.",
                  coverage=S.NOT_RUN, count_methods=count_methods, non_count_tests=non_count)
    if count_methods:
        count_producer_bound = bool(
            design.confirmed_by_human and contract is not None
            and contract.producer_binding == "exact"
            and contract.response_scale == "raw_counts"
            and contract.method_family == "negative_binomial"
        )
        if not count_producer_bound:
            return _f(
                S.NEEDS_EVIDENCE,
                f"the code mentions a count method ({', '.join(count_methods)}), but that name is "
                "not bound as the exact producer of this reported result. I did not infer which "
                "method generated the table from a stray call or import.",
                coverage=S.NOT_RUN, count_methods=count_methods,
            )
        return _f(S.PASS, f"the exact bound report producer is declared as a negative-binomial "
                  f"raw-count method, matching the recognized calls ({', '.join(count_methods)}).",
                  count_methods=count_methods)
    if not non_count:
        return _f(S.NEEDS_EVIDENCE, "I can see analysis code, but I can't identify from it which "
                  "statistical test produced these results — so I can't confirm the method suits "
                  "count data", coverage=S.NOT_RUN)

    incompatible_contract = bool(
        design.confirmed_by_human
        and contract is not None
        and contract.producer_binding == "exact"
        and contract.response_scale == "raw_counts"
        and contract.method_family in ("gaussian", "rank_based")
    )
    if not incompatible_contract:
        return _f(
            S.NEEDS_EVIDENCE,
            "a generic test appears in the code, but it is not bound as the exact producer of this "
            "report on a raw-count response with a categorically incompatible method contract. The "
            "negative-binomial recompute cannot establish a model defect from overlap alone",
            coverage=S.NOT_RUN,
            non_count_tests=non_count,
        )

    # A null grouping component makes pandas groupby silently drop observations.  The
    # legacy pseudobulk adapter does not expose its exactness result to this check, so
    # fail closed before recomputing rather than adjudicating a collapsed subset.
    grouping_key = list(design.aggregation_key or design.sample_unit or [])
    observations = bundle.observations
    null_key_columns = [
        column for column in grouping_key
        if column in observations.columns and observations[column].isna().any()
    ]
    if null_key_columns:
        return _f(
            S.NOT_AUDITED,
            "the confirmed sample-grouping identity contains a null value, so I can't "
            "faithfully reconstruct the ratified pseudobulk samples and did NOT run the "
            "count-model recompute",
            coverage=S.NOT_RUN,
            machine_reason="invalid_aggregation_key_value",
            grouping_key=grouping_key,
            null_key_columns=null_key_columns,
        )

    # Recompute with a proper count model and show what it would have found.
    pb, meta = aggregate_to_pseudobulk(bundle, design)
    if engine == "pydeseq2":
        from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute
        res = pydeseq2_recompute(pb, meta, design)
    else:
        from sc_referee.engine import simple_recompute
        res = simple_recompute(pb, meta, design)

    table = res.table
    rep = reported.dropna(subset=["feature_id"]).drop_duplicates("feature_id").set_index("feature_id")
    sig_col = "padj" if "padj" in rep.columns and rep["padj"].notna().any() else "pvalue"
    claimed = {f for f in rep.index[rep[sig_col] <= ALPHA] if f in table.index}
    nb_sig = set(table.index[(table["padj"] <= ALPHA) & table["testable"].astype(bool)])

    survivors = claimed & nb_sig
    missed = nb_sig - claimed
    metrics = dict(non_count_tests=non_count, count_methods=[], claimed=len(claimed),
                   nb_significant=len(nb_sig), survivors=len(survivors), missed_by_you=len(missed),
                   engine=engine)

    return _f(S.MAJOR,
              f"the exact report producer is bound to {', '.join(non_count)} applied directly to a "
              f"raw count response, while its declared {contract.method_family} method family requires "
              f"a continuous/rank response rather than raw counts. That categorical method/scale "
              f"incompatibility is the concern. As a diagnostic only, a negative-binomial recompute "
              f"found {len(survivors)} of {len(claimed)} reported discoveries and {len(missed)} additional "
              f"discoveries ({len(nb_sig)} significant in total); overlap does not authorize the verdict.",
              **metrics)


class CountModelCheck:
    """Fires only on a sample-level (already aggregated) count analysis. A cell-level analysis is
    pseudoreplication — `experimental_unit`'s territory, not ours."""

    id = CHECK_ID
    analysis_types = ("condition_contrast_DE",)
    audit_dimensions = ("scale",)
    proof_basis = "independent recompute"
    proof_basis_by_status = {S.PASS: "provenance/static"}
    contract_fields = ("condition", "reference", "test", "replicate_unit", "sample_unit",
                       "unit_of_test", "subset", "report_inference_contract")
    max_status = S.MAJOR   # reports the missed NB hits; a wrong test model is `major`, never a blocker

    def __init__(self, engine: str = "pydeseq2"):
        self.engine = engine

    def applies_to(self, design: Design, bundle) -> bool:
        return (design.analysis_type in self.analysis_types
                and design.unit_of_test == "sample"
                and bundle is not None
                and getattr(bundle.measure, "kind", None) == "counts")

    def cannot_evaluate(self, design: Design, bundle):
        if design.analysis_type not in self.analysis_types or bundle is None:
            return None
        kind = getattr(bundle.measure, "kind", None)
        if kind == "normalized" and design.unit_of_test == "sample":
            return ("your data looks already normalized, not raw counts — but checking whether the "
                    "right count model was used needs the raw integer counts, so I did NOT check it. "
                    "Provide the raw counts in layers['counts'] or raw.X and I can.")
        if kind != "counts":
            return None                          # not a raw-count analysis; nothing to say
        if design.unit_of_test is None:
            return ("I couldn't tell whether the unit of analysis is the cell or the sample, so I "
                    "could NOT check whether a count model was needed")
        return None

    def run(self, design: Design, bundle, reported=None) -> Finding:
        return evaluate_count_model(design, bundle, reported, engine=self.engine)
