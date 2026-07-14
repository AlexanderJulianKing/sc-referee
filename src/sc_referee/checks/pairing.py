"""pairing — is the pairing structure of a condition contrast sound?

Increment 1 (diagnostic; never blocks). A adversarial boundary consult established that none of the arithmetic
patterns available now is a sound BLOCKER: a few unmatched pairs do not invalidate the matched ones;
duplicated aggregate keys need the actual report-bound one-to-one pairing (not yet bound); zero complete
pairs in a PAIRED model is a rank deficiency the `confounding` check already owns. So this check does the
two sound things it can, and the blocker waits on the report-bound sample table + exchangeability confirm.

  - OMITTED PAIRING (needs_evidence): the analyst's model is UNPAIRED (`pairing_unit` empty) but the data
    is PAIRED-CAPABLE — the replicate key spans BOTH contrast arms. This is the genuinely new catch;
    `confounding` stays silent because an unpaired model is full rank, yet ignoring within-subject
    structure can be inefficient or anti-conservative. Advisory: consider a paired/mixed sensitivity fit.
  - PARTIAL MATCHING (informational): a PAIRED design where some replicate levels appear in only one arm
    — a reported fact, not a defect (a paired method simply drops them).

False-accuse guards: a genuinely unpaired design (no replicate level spans both arms) and a well-formed
paired design (every level in both arms) are `pass`, never flagged. All judgements are on the confirmed
subset + the two confirmed contrast levels only.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.citations import CITATIONS
from sc_referee.design import Design, apply_subset, confidence_high
from sc_referee.kernel import FunctionalDependencyRule, FunctionalDependencySpec, ProofState

CHECK_ID = "pairing"


@dataclass(frozen=True)
class _PairSpanResult:
    key: list[str] | None
    complete: int = 0
    incomplete: int = 0
    coverage_complete: bool = True
    missing_fields: tuple[str, ...] = ()
    reason: str | None = None

    def __iter__(self):
        """Keep the legacy arithmetic oracle's three-value unpacking stable."""
        yield self.key
        yield self.complete
        yield self.incomplete


def _duplicated_pairing(design: Design, bundle):
    """Proof that complete (pairing level, arm) groups map to at most one aggregated sample, or None
    when it cannot be assessed. Sound only under the ratified aggregation_key + pairing_unit
    contract (adversarial review pairing consult): the pairing must be at the sample level (pairing_unit ⊆
    aggregation_key) and the contrast must be IN the key (so arms aren't merged — the pseudobulk merge
    blocker's job). If a level that is present in BOTH arms has an arm with >1 distinct aggregated sample,
    its one-to-one matching is ambiguous (which of donor D1's two control samples pairs with its stim?).

    Two guards learned from the adversarial review: an INCOMPLETE level (present in only one arm) is
    dropped by a paired analysis, so its duplicates never fire (review #1); and rows with a NaN in any
    aggregation-key column are dropped first, matching pandas groupby's default so a NaN cannot fabricate
    a phantom extra sample (review #3)."""
    obs = bundle.observations
    pairing = list(design.pairing_unit or [])
    agg = list(design.aggregation_key or [])
    if not pairing or not agg:
        return None                                   # needs both a paired model and a ratified key
    if any(c not in obs.columns for c in agg + pairing):
        return None                                   # a key column we can't see -> abstain
    contrast_col, ref, test = design.contrast_column_and_levels()
    if not (set(pairing) <= set(agg)) or contrast_col not in agg or contrast_col not in obs.columns \
            or ref == test:
        return None                                   # pairing not at sample level, or arms merged/degenerate
    sub = apply_subset(obs, design)
    arms = sub[(sub[contrast_col] == ref) | (sub[contrast_col] == test)]   # value equality, not str()
    arms = arms.dropna(subset=agg)                    # review #3: match real groupby's NaN handling
    if arms.empty:
        return None
    samples = arms[agg].drop_duplicates()             # the distinct aggregated pseudobulk samples
    arms_per_level = (samples.groupby(pairing, observed=True)[contrast_col].nunique()
                      .reset_index(name="_arms"))
    # review #1: only levels present in BOTH arms (complete pairs) can be ambiguously matched
    complete = arms_per_level[arms_per_level["_arms"] == 2][pairing]
    complete_samples = samples.merge(complete, on=pairing, how="inner", sort=False)
    return FunctionalDependencyRule().evaluate(
        complete_samples,
        FunctionalDependencySpec(
            determinant_columns=tuple([*pairing, contrast_col]),
            dependent_columns=tuple(agg),
            max_distinct=1,
        ),
    )


def _pair_spans(design: Design, bundle):
    """Pair coverage on the complete declared key and exact contrast values.

    The result carries complete/incomplete level counts plus an explicit coverage state. No key is
    genuinely not applicable; a declared key with missing columns is unresolved and must not be reduced.
    """
    obs = apply_subset(bundle.observations, design)
    contrast_col, ref, test = design.contrast_column_and_levels()
    if contrast_col not in obs.columns:
        return _PairSpanResult(None)
    key = list(design.pairing_unit or design.replicate_unit or [])
    if not key:
        return _PairSpanResult(None)
    missing = tuple(k for k in key if k not in obs.columns)
    if missing:
        return _PairSpanResult(
            key,
            coverage_complete=False,
            missing_fields=missing,
            reason="missing_pairing_key_columns",
        )
    if ref == test:
        return _PairSpanResult(key)
    arm_col = "__sc_referee_pairing_arm__"
    while arm_col in key:
        arm_col += "_"
    reference_rows = obs.loc[obs[contrast_col] == ref, key].copy()
    reference_rows[arm_col] = 0
    test_rows = obs.loc[obs[contrast_col] == test, key].copy()
    test_rows[arm_col] = 1
    arms = pd.concat([reference_rows, test_rows], ignore_index=True)
    arms = arms.dropna(subset=key)
    if arms.empty:
        return _PairSpanResult(key)
    per_level = arms.groupby(key, observed=True)[arm_col].nunique()
    complete = int((per_level == 2).sum())
    incomplete = int((per_level == 1).sum())
    return _PairSpanResult(key, complete, incomplete)


def _cols(names) -> str:
    """Column names as plain English, never a ['list'] literal — the reader may not recognize
    their own (possibly agentically-generated) variable names."""
    names = [str(n) for n in (names if isinstance(names, (list, tuple, set)) else [names]) if n is not None]
    if not names:
        return "the pairing key"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def evaluate_pairing(design: Design, bundle, reported=None) -> Finding:
    cites = CITATIONS[CHECK_ID]
    span = _pair_spans(design, bundle)
    key, complete, incomplete = span
    if not span.coverage_complete:
        return Finding(
            CHECK_ID,
            S.NEEDS_EVIDENCE,
            f"I couldn't check the pairing: the pairing key you declared ({_cols(key)}) is missing "
            f"from the data — column(s) {_cols(span.missing_fields)} aren't in .obs. I'm not making "
            f"any pairing claim either way.",
            metrics={
                "pairing_key": key,
                "missing_fields": list(span.missing_fields),
                "coverage_reason": span.reason,
            },
            citations=cites,
            coverage=S.NOT_RUN,
        )
    if key is None:
        return Finding(CHECK_ID, S.NEEDS_EVIDENCE,
                       "no replicate or pairing key is declared, so pairing was not checked.",
                       citations=cites, coverage=S.NOT_RUN)
    metrics = {"pairing_key": key, "complete_pairs": complete, "unmatched_levels": incomplete}

    if not design.pairing_unit:                       # the analyst's model is UNPAIRED
        if complete >= 1:
            return Finding(CHECK_ID, S.NEEDS_EVIDENCE,
                           f"your model treats the samples as unpaired, but {complete} subject(s) "
                           f"(values of {_cols(key)}) actually appear in BOTH groups — so the data is "
                           f"really paired. Ignoring that within-subject link can lose power or make the "
                           f"test too liberal; consider a paired (or mixed-model) sensitivity check.",
                           metrics=metrics, citations=cites, judgment=S.CONCERN)
        return Finding(CHECK_ID, S.PASS, f"the design really is unpaired: no {_cols(key)} appears in "
                       f"both groups, so an unpaired model is the right choice.",
                       metrics=metrics, citations=cites, judgment=S.CONFORMANT)

    # the analyst's model is PAIRED
    duplicate_proof = _duplicated_pairing(design, bundle)
    if duplicate_proof is not None and duplicate_proof.state is ProofState.UNRESOLVED:
        return Finding(CHECK_ID, S.NEEDS_EVIDENCE,
                       f"the duplicated-pairing relation could not be evaluated "
                       f"({duplicate_proof.reason}); no blocker is asserted.",
                       metrics=metrics, citations=cites, coverage=S.NOT_RUN)
    dup = (duplicate_proof.violation_count
           if duplicate_proof is not None
           and duplicate_proof.state is ProofState.PROVED_VIOLATION else 0)
    if dup:
        # >1 sample per (complete pairing level, arm). This is a mechanical error only under an explicit
        # one-to-one mechanics contract. A within-pair estimand is also compatible with a valid mixed /
        # repeated-measures model, so it cannot imply mechanics by itself.
        within_pair = design.pairing_estimand == "within_pair"
        one_to_one = design.pairing_mechanics == "one_to_one"
        blocker_allowed = (design.confirmed_by_human and confidence_high(design, "aggregation_key")
                           and within_pair and one_to_one)
        if blocker_allowed:
            note = ""
        elif not within_pair:
            note = (" — but no within-pair estimand is confirmed, so this arithmetic does not establish "
                    "a one-to-one pairing defect.")
        elif design.pairing_mechanics == "repeated_measures":
            note = (" — the declared repeated-measures mechanics may model multiple visits per arm, "
                    "so a one-to-one defect is not asserted.")
        elif not one_to_one:
            note = (" — `pairing_estimand: within_pair` does not imply one-to-one mechanics; without an "
                    "explicit `pairing_mechanics: one_to_one` contract, a repeated-measures model may "
                    "handle these samples, so no blocker is asserted.")
        else:
            note = " — but the aggregation key is not human-confirmed / low confidence, so no blocker."
        return Finding(
            CHECK_ID, S.BLOCKER if blocker_allowed else S.NEEDS_EVIDENCE,
            f"{dup} pairing group(s) map to MORE THAN ONE sample per arm under your aggregation key "
            f"({_cols(design.aggregation_key)}): the one-to-one pairing on {_cols(key)} is then "
            f"ambiguous — which sample in one group pairs with which in the other? Aggregate to exactly "
            f"one sample per (pairing group, arm), or model the extra structure explicitly." + note,
            metrics={"pairing_key": key, "ambiguous_pairs": dup,
                     "aggregation_key": list(design.aggregation_key or []),
                     "pairing_estimand": design.pairing_estimand,
                     "pairing_mechanics": design.pairing_mechanics}, citations=cites,
            coverage=S.COMPLETE if blocker_allowed else S.NOT_RUN,
            judgment=S.VIOLATION if blocker_allowed else None)

    if complete == 0:
        # zero complete pairs is a rank deficiency the confounding check already owns; stay quiet on the
        # blocker, but do not certify a broken pairing as clean.
        return Finding(CHECK_ID, S.NEEDS_EVIDENCE,
                       f"your pairing key ({_cols(key)}) forms NO complete pairs across the two groups "
                       f"— every subject appears in only one group — so a paired comparison can't be "
                       f"built at all. (The confounding check explains the underlying rank problem.)",
                       metrics=metrics, citations=cites, judgment=S.CONCERN)
    if incomplete:
        return Finding(CHECK_ID, S.INFORMATIONAL,
                       f"{complete} complete pair(s); {incomplete} level(s) of {key} appear in only one "
                       f"arm and cannot contribute to the within-pair contrast (a paired method drops "
                       f"them).", metrics=metrics, citations=cites)
    return Finding(CHECK_ID, S.PASS, f"paired design is well-formed: {complete} complete pairs across "
                   f"the two arms.", metrics=metrics, citations=cites, judgment=S.CONFORMANT)


class PairingCheck:
    """Assesses the pairing structure of a condition contrast: omitted pairing (paired-capable data, an
    unpaired model) and partial matching. Never blocks in increment 1 (adversarial boundary consult)."""

    id = CHECK_ID
    analysis_types = ("condition_contrast_DE",)
    audit_dimensions = ("unit_of_independence", "estimand")
    proof_basis = "independent recompute"
    contract_fields = ("condition", "reference", "test", "replicate_unit", "pairing_unit",
                       "pairing_estimand", "pairing_mechanics", "aggregation_key", "subset")
    # BLOCKER-entitled: a ratified aggregation_key that makes the confirmed 1:1 pairing ambiguous earns it
    # (adversarial review pairing consult, case 2). Omitted/partial pairing stay diagnostic.
    max_status = S.BLOCKER

    def applies_to(self, design: Design, bundle) -> bool:
        if design.analysis_type in self.analysis_types and bundle is not None:
            return True
        from sc_referee.checks.experimental_unit import marker_unit_concern_is_proved
        return marker_unit_concern_is_proved(design, bundle)

    def run(self, design: Design, bundle, reported=None) -> Finding:
        return evaluate_pairing(design, bundle, reported)
