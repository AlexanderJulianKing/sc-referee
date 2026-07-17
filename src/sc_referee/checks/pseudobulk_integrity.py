"""pseudobulk_integrity — is the pseudobulk the count-model sink consumes structurally sound?

Increment 1 (needs_evidence-only). The catalog frames this as a blocker-capable [R-S] check with five
invariants, but the two that would BLOCK each require machinery SinkUse v1 defers (Codex design consult):

  - the ASSAY CONTRACT would need field-sensitive reaching SCALE — `bundle.measure.kind` is the FINAL
    `.X` state, not the scale at the sink, so `DeseqDataSet(counts=adata.X); normalize_total(adata)`
    ran on raw counts yet reads normalized; a blocker there would false-accuse;
  - the AGGREGATION MERGE would need a ratified `actual_aggregation_key` bound to the sink — the confirmed
    `Design.sample_unit` is the referee's RECOMPUTE key, so a mismatch may be a config/DesignError rather
    than a scientific error (design.py already treats an unrealizable design as a config error).

So increment 1 does the two SOUND things it can, and never blocks (max_status is the honest ceiling):

  - ASSAY SMELL: a count-model sink (response accepts raw_counts ONLY — DESeq2/edgeR-style) whose
    `counts` response DIRECTLY reads `.X`/`.raw.X` while the matrix's final state is not raw counts ->
    needs_evidence. It does NOT flag a response that reads a raw LAYER (`layers['counts']`): SinkUse binds
    the actual response expression, so raw-in-layer + normalized-.X is correctly left alone. That
    layer-vs-.X distinction is exactly what the typed-sink foundation buys (the false-accuse guard).
  - KEY INTEGRITY: a missing value in the aggregation key silently drops cells from every pseudobulk.

When `actual_aggregation_key` and reaching-scale land, this check owns the merge / assay BLOCKERS and
`experimental_unit` defers to its shared precondition rather than duplicating it.
"""
from __future__ import annotations

import ast

import pandas as pd

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.citations import CITATIONS
from sc_referee.design import Design, apply_subset, confidence_high
from sc_referee.kernel import FunctionalDependencyRule, FunctionalDependencySpec, ProofState

CHECK_ID = "pseudobulk_integrity"


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


def _is_countmodel(contract) -> bool:
    """A sink that accepts raw counts ONLY as its response — an NB count model (DESeq2/edgeR), where a
    non-count response is a definite assay error rather than a modelling choice."""
    return any(p.role in ("response", "response_a", "response_b")
               and p.accepted_scales == frozenset({"raw_counts"})
               for p in contract.inputs)


def _countmodel_uses(bundle) -> list:
    sources = (getattr(bundle, "code_signals", None) or {}).get("sources", [])
    if not sources:
        return []
    from sc_referee.sink_use import bind_sinks
    return [u for u in bind_sinks(sources).uses if _is_countmodel(u.contract)]


def _reads_expression_matrix(expr) -> bool:
    """An `.X`/`.raw.X` attribute read ANYWHERE in the response expression — so `.X.copy()`, a slice, or
    a direct wrapper is caught too, not just a top-level `adata.X` (Codex sign-off). A raw layer
    (`layers['counts']`) has no `.X` attribute, so it is correctly left alone. Matching incidentally is
    safe: it only ever yields needs_evidence (review), never a blocker."""
    return any(isinstance(n, ast.Attribute) and n.attr == "X" for n in ast.walk(expr))


def _merge_dependency_proof(sub, declared, contrast_col, ref, test):
    """The pure relational fact used by the merge check, after its domain guards have passed.

    Arm identity is canonicalized from VALUE comparisons.  A row matching both values is emitted twice,
    once under each internal arm token, exactly preserving the old `_ref.any() & _test.any()` semantics.
    Null determinant rows are removed HERE (not by the generic rule), matching pandas groupby's default.
    """
    arm_column = "__sc_referee_arm_role__"
    while arm_column in declared:
        arm_column += "_"

    keys = sub.loc[:, declared].copy()
    ref_match = sub[contrast_col] == ref
    test_match = sub[contrast_col] == test
    ref_rows = keys.loc[ref_match].copy()
    test_rows = keys.loc[test_match].copy()
    ref_rows[arm_column] = 0
    test_rows[arm_column] = 1
    relation = pd.concat([ref_rows, test_rows], ignore_index=True)
    relation = relation.dropna(subset=declared)

    return FunctionalDependencyRule().evaluate(
        relation,
        FunctionalDependencySpec(
            determinant_columns=tuple(declared),
            dependent_columns=(arm_column,),
            max_distinct=1,
        ),
    )


def _merge_finding(design: Design, bundle, cites):
    """The aggregation-MERGE check — the sound blocker this check earns once the analyst's ACTUAL
    aggregation key is ratified (Codex pseudobulk-integrity consult). If the confirmed `aggregation_key`
    EXCLUDES the contrast column and some aggregated group (within the subset, over the two confirmed
    arms) contains cells from BOTH arms, then that pseudobulk sample mixes the two conditions and the DE
    contrast is applied to mislabeled samples — structurally invalid regardless of biology, the analog of
    confounding's aliasing. Returns a Finding (blocker, or capped needs_evidence when unconfirmed), or
    None when it does not apply/fire. False-accuse guards: a key that INCLUDES the contrast (each output
    pure), or a between-subject design (no group spans both arms), never fire."""
    obs = bundle.observations
    declared = list(design.aggregation_key or [])
    if not declared or not _countmodel_uses(bundle):
        return None                               # no ratified key, or no count-model sink bound
    missing = [k for k in declared if k not in obs.columns]
    if missing:
        # a ratified key column we cannot see means we cannot reconstruct the REAL grouping. Dropping it
        # and grouping by the reduced key would false-accuse a correct donor x arm analysis (Codex
        # keystone review #1) — abstain, never block on a reduced key.
        return Finding(CHECK_ID, S.NEEDS_EVIDENCE,
                       f"the sample-grouping key you confirmed ({_cols(declared)}) includes "
                       f"column(s) that aren't in the data ({_cols(missing)}), so I can't "
                       f"reconstruct how cells were actually grouped into samples — I did NOT run "
                       f"the merge check. Add the missing column(s), or fix the key, and re-run.",
                       metrics={"aggregation_key": declared}, citations=cites,
                       coverage=S.NOT_RUN)
    contrast_col, ref, test = design.contrast_column_and_levels()
    if contrast_col in declared or contrast_col not in obs.columns or ref == test:
        return None                               # key includes the contrast (pure outputs), or degenerate
    sub = apply_subset(obs, design)
    # VALUE equality, not str() coercion: distinct levels like int 1 vs str "1" must never collapse into
    # one arm and fabricate a spurious "spans both" (Codex keystone review #2).
    proof = _merge_dependency_proof(sub, declared, contrast_col, ref, test)
    if proof.state is ProofState.UNRESOLVED:
        return Finding(CHECK_ID, S.NEEDS_EVIDENCE,
                       f"I couldn't work out whether any sample ends up mixing the two conditions "
                       f"({proof.reason}), so I'm not asserting a blocker.",
                       metrics={"aggregation_key": declared, "contrast": contrast_col},
                       citations=cites, coverage=S.NOT_RUN)
    if proof.state is ProofState.PROVED_CONFORMANT:
        return None                               # no output spans both arms (e.g. between-subject)
    n_merged = proof.violation_count
    blocker_allowed = design.confirmed_by_human and confidence_high(design, "aggregation_key")
    note = "" if blocker_allowed else (" — but you haven't confirmed the grouping key yet (or it's "
                                       "low-confidence), so I'm flagging this for review rather than "
                                       "blocking.")
    return Finding(
        CHECK_ID, S.BLOCKER if blocker_allowed else S.NEEDS_EVIDENCE,
        f"{n_merged} of your samples end up built from cells of BOTH the {ref} and {test} groups: "
        f"the key you group by ({_cols(declared)}) leaves out the condition column ({contrast_col}), "
        f"so cells from the two conditions get added into the same sample. The comparison is then "
        f"run on samples that are each a blend of both conditions, which is invalid no matter what "
        f"the biology is. Group samples by a key that also includes {contrast_col}, so each sample "
        f"is all-{ref} or all-{test}." + note,
        metrics={"aggregation_key": declared, "contrast": contrast_col, "merged_samples": n_merged},
        citations=cites,
        coverage=S.COMPLETE if blocker_allowed else S.NOT_RUN,
        judgment=S.VIOLATION if blocker_allowed else None)


def evaluate_pseudobulk_integrity(design: Design, bundle, reported=None) -> Finding:
    cites = CITATIONS[CHECK_ID]
    merge = _merge_finding(design, bundle, cites)   # the blocker-capable invariant takes precedence
    if merge is not None:
        return merge
    uses = _countmodel_uses(bundle)
    concerns = []
    abstentions = []

    for u in uses:
        resp = u.bound_ports.get("response")
        if resp is None or resp.status != "bound":
            # the response could not be pinned to an expression (splat / ambiguous / invalid), so its
            # input scale cannot be checked — abstain, never certify (Codex sign-off, unknown => review).
            abstentions.append(
                f"your count model ({u.symbol}) needs raw counts, but I couldn't pin down exactly "
                f"what was passed in as its counts (binding: "
                f"{resp.status if resp is not None else 'absent'}), so I couldn't confirm raw counts "
                f"reached it.")
        elif _reads_expression_matrix(resp.expr) and bundle.measure.kind != "counts":
            abstentions.append(
                f"your count model ({u.symbol}) reads the main matrix (.X) as its counts, but that "
                f"matrix ends up '{bundle.measure.kind}', not raw whole-number counts. Count models "
                f"like DESeq2/edgeR require raw counts; if a normalization or log step ran before the "
                f"test, transformed values may have reached the model. I can't yet trace the exact "
                f"values at that point, so confirm raw counts reached the model, or feed it a "
                f"raw-count layer (e.g. layers['counts']).")

    obs = bundle.observations
    declared = list(design.sample_unit or [])
    present = [k for k in declared if k in obs.columns]
    missing_cols = [k for k in declared if k not in obs.columns]
    if not declared:
        abstentions.append("no sample-grouping key (sample_unit) is declared, so I can't verify how "
                           "cells are grouped into the samples a count model needs. Declare the key "
                           "that defines one sample (e.g. donor_id).")
    elif missing_cols:
        abstentions.append(f"the sample-grouping key ({_cols(declared)}) includes column(s) that "
                           f"aren't in the data ({_cols(missing_cols)}), so the grouping into samples "
                           f"can't be verified.")
    else:
        sub = apply_subset(obs, design)
        n_missing = int(sub[present].isna().any(axis=1).sum())
        if n_missing:
            concerns.append(
                f"{n_missing} cell(s) have a missing value in the sample-grouping key "
                f"({_cols(present)}); grouping silently drops those cells, so they vanish from "
                f"every sample. Fill in or remove the cells with a missing key value.")

    metrics = {"countmodel_sinks": [u.symbol for u in uses]}
    if concerns:
        return Finding(CHECK_ID, S.NEEDS_EVIDENCE, " ".join(concerns + abstentions),
                       metrics=metrics, citations=cites, judgment=S.CONCERN)
    if abstentions:
        return Finding(CHECK_ID, S.NEEDS_EVIDENCE, " ".join(abstentions), metrics=metrics,
                       citations=cites, coverage=S.NOT_RUN)
    return Finding(CHECK_ID, S.PASS,
                   "the way cells are combined into samples shows no structural red flag: the count "
                   "model isn't reading the normalized main matrix, and the sample-grouping key has "
                   "no missing values. (A deeper check of the exact values reaching the model is a "
                   "later increment.)",
                   metrics=metrics, citations=cites, judgment=S.CONFORMANT)


class PseudobulkIntegrityCheck:
    """Validates the pseudobulk a count-model DE sink consumes. Applies only when a raw-counts-only sink
    (DESeq2/edgeR) is resolved in the code — otherwise there is no count-model assay contract to check."""

    id = CHECK_ID
    analysis_types = ("condition_contrast_DE",)
    audit_dimensions = ("unit_of_independence", "scale")
    proof_basis = "provenance/static"
    proof_basis_by_status = {S.BLOCKER: "independent recompute"}
    contract_fields = ("condition", "reference", "test", "sample_unit", "aggregation_key",
                       "unit_of_test", "subset")
    # BLOCKER-entitled: the aggregation-MERGE invariant earns it (structural, like confounding) once the
    # analyst's aggregation_key is ratified. The assay-smell / key-integrity paths stay needs_evidence.
    max_status = S.BLOCKER

    def applies_to(self, design: Design, bundle) -> bool:
        return (design.analysis_type in self.analysis_types and bundle is not None
                and bool(_countmodel_uses(bundle)))

    def run(self, design: Design, bundle, reported=None) -> Finding:
        return evaluate_pseudobulk_integrity(design, bundle, reported)
