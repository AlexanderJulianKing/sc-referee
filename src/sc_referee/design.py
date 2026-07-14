"""The human-confirmed Design — a flat view of one contrast from sc-referee.yaml.

A check runs PER CONTRAST. Top-level fields (batch/condition/confirmed_by_human/
confidence) and contrast-level fields (reference/test/model/... ) are flattened here so
checks receive everything they need without reaching back into the YAML. (C2)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, Mapping, Optional


_BATCH_MODELING_FIELDS = frozenset({
    "source_column", "modeled_as", "random_group_column", "fixed_source_columns",
    "rows_exact", "row_ledger_identity", "component_scope", "unsupported_components",
})
_BATCH_MODELING_MODES = frozenset({
    "fixed", "random_intercept", "fixed_and_random_intercept", "absent",
    "upstream_handled", "unsupported",
})
_UNSUPPORTED_BATCH_COMPONENTS = frozenset({
    "random_slope", "correlated_random_effects", "crossed_random_effects",
    "nested_random_effects", "glmm_integration", "penalty", "weight", "offset",
    "transform", "upstream_operator", "other",
})


@dataclass(frozen=True)
class EffectRelevanceContract:
    """An optional claim-bound floor for biologically relevant discoveries.

    The reported and threshold scales are separate on purpose: a threshold cannot authorize an
    accusation unless it is bound to the exact scale of the reported effect column.
    """

    claim_type: Literal["biologically_relevant_discovery"]
    threshold: float
    threshold_scale: Literal["log2_fold_change", "natural_log_fold_change"]
    reported_effect_scale: Literal["log2_fold_change", "natural_log_fold_change"]

    def __post_init__(self) -> None:
        if not isinstance(self.threshold, (int, float)) or isinstance(self.threshold, bool) \
                or self.threshold <= 0:
            raise ValueError("effect relevance threshold must be a positive finite number")


@dataclass(frozen=True)
class MultiplicityContract:
    """The exact error-control claim attached to one complete reported family."""

    claim_type: Literal["error_controlled_discovery", "nominal_discovery"]
    error_criterion: Literal["fdr", "fwer", "nominal"]
    adjustment_method: Literal["benjamini_hochberg", "storey", "bonferroni", "none", "other"]
    family_complete: bool


@dataclass(frozen=True)
class ReportInferenceContract:
    """Typed semantics for the exact producer of one reported claim."""

    producer_binding: Literal["exact"]
    response_scale: Literal["raw_counts", "transformed_continuous", "normalized_continuous", "unknown"]
    method_family: Literal[
        "negative_binomial", "gaussian", "rank_based", "mixed_model", "gee", "other",
    ]
    dependence_semantics: Literal[
        "iid_rows", "mixed_model", "gee", "cluster_robust", "paired", "unknown",
    ]


@dataclass(frozen=True)
class BatchComponentScope:
    contrast_name: str
    target_coefficient: str
    fitted_result_id: str

    def __post_init__(self) -> None:
        if not all(isinstance(value, str) and value.strip() for value in (
            self.contrast_name, self.target_coefficient, self.fitted_result_id
        )):
            raise ValueError("batch component scope requires exact non-empty labels")


@dataclass(frozen=True)
class BatchModelingDeclaration:
    source_column: str
    modeled_as: Literal[
        "fixed", "random_intercept", "fixed_and_random_intercept", "absent",
        "upstream_handled", "unsupported",
    ]
    random_group_column: str | None
    fixed_source_columns: tuple[str, ...] | None
    rows_exact: bool
    row_ledger_identity: str | None
    component_scope: BatchComponentScope
    unsupported_components: tuple[str, ...]
    field_confidence: Mapping[str, Literal["high", "low"]]
    evidence_locations: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        if not isinstance(self.source_column, str) or not self.source_column.strip():
            raise ValueError("source_column must be an exact non-empty label")
        if self.modeled_as not in _BATCH_MODELING_MODES:
            raise ValueError("invalid batch modeled_as value")
        if self.random_group_column is not None and (
            not isinstance(self.random_group_column, str) or not self.random_group_column.strip()
        ):
            raise ValueError("random_group_column must be an exact label or null")
        fixed = None if self.fixed_source_columns is None else tuple(self.fixed_source_columns)
        if fixed is not None and (
            any(not isinstance(value, str) or not value for value in fixed)
            or len(set(fixed)) != len(fixed)
        ):
            raise ValueError("fixed_source_columns must contain unique exact labels")
        unsupported = tuple(self.unsupported_components)
        if len(set(unsupported)) != len(unsupported) or any(
            value not in _UNSUPPORTED_BATCH_COMPONENTS for value in unsupported
        ):
            raise ValueError("invalid unsupported batch component inventory")
        confidence = dict(self.field_confidence)
        if set(confidence) != _BATCH_MODELING_FIELDS or any(
            value not in ("high", "low") for value in confidence.values()
        ):
            raise ValueError("field_confidence must cover every batch modeling semantic field")
        evidence = {key: tuple(values) for key, values in self.evidence_locations.items()}
        if any(not isinstance(key, str) or any(
            not isinstance(location, str) or not location for location in locations
        ) for key, locations in evidence.items()):
            raise ValueError("evidence locations must be exact strings")
        object.__setattr__(self, "fixed_source_columns", fixed)
        object.__setattr__(self, "unsupported_components", unsupported)
        object.__setattr__(self, "field_confidence", MappingProxyType(confidence))
        object.__setattr__(self, "evidence_locations", MappingProxyType(evidence))


@dataclass(frozen=True)
class FittedDesignDeclaration:
    rows_exact: bool
    operator_kind: Literal["ordinary_fixed_effects", "random_intercept_only", "unsupported"]
    intercept: bool
    column_kinds: Mapping[str, Literal["continuous", "categorical"]]
    categorical_levels: Mapping[str, tuple[object, ...]]
    transforms: Mapping[str, Literal["identity"]]
    weight_role: str | None = None
    offset_role: str | None = None
    unsupported_reason: str | None = None
    batch_modeling: Mapping[str, BatchModelingDeclaration] = field(default_factory=dict)

    def __post_init__(self) -> None:
        kinds = dict(self.column_kinds)
        transforms = dict(self.transforms)
        levels = {source: tuple(values) for source, values in self.categorical_levels.items()}
        batch_modeling = dict(self.batch_modeling)
        if set(transforms) != set(kinds) or any(value != "identity" for value in transforms.values()):
            raise ValueError("every fitted-design column requires an identity transform declaration")
        if any(kind not in ("continuous", "categorical") for kind in kinds.values()):
            raise ValueError("invalid fitted-design column kind")
        categorical = {source for source, kind in kinds.items() if kind == "categorical"}
        if set(levels) != categorical or any(
            not values or len(set(values)) != len(values) for values in levels.values()
        ):
            raise ValueError("categorical level ledger must be complete, non-empty, and unique")
        if any(key != entry.source_column for key, entry in batch_modeling.items()):
            raise ValueError("batch modeling ledger key must equal source_column")
        if any(not isinstance(entry, BatchModelingDeclaration) for entry in batch_modeling.values()):
            raise TypeError("batch modeling ledger values must be BatchModelingDeclaration objects")
        object.__setattr__(self, "column_kinds", MappingProxyType(kinds))
        object.__setattr__(self, "categorical_levels", MappingProxyType({
            source: tuple(values) for source, values in levels.items()
        }))
        object.__setattr__(self, "transforms", MappingProxyType(transforms))
        object.__setattr__(self, "batch_modeling", MappingProxyType(batch_modeling))


@dataclass
class Design:
    analysis_type: str
    confirmed_by_human: bool
    confidence: dict  # {"replicate_unit": "high"|"low", "condition": "high"|"low"}
    # top-level design
    condition: Optional[str]
    batch: list
    replicate_unit: list
    # contrast-level
    reference: object  # level value on the contrast column
    test: object  # a level value on `condition`, OR {col: val}
    model: Optional[str]  # patsy-style formula, e.g. "~ donor_id + condition"
    target_coefficient: Optional[str]  # e.g. "condition[T.stim]" — what confounding/DE tests
    sample_unit: list  # pseudobulk aggregation key the REFEREE recomputes on
    pairing_unit: Optional[list] = None
    subset: Optional[dict] = None
    name: str = "contrast"
    # The FINAL sample-identity key at the report-bound sink: the columns that identify each pseudobulk
    # sample AFTER every technical-replicate collapse/average — NOT an earlier intermediate cell-
    # aggregation key. A pipeline that sums lanes into donor×condition before the sink has a final key of
    # [donor, condition], WITHOUT lane. Human-ratified, distinct from `sample_unit` (the referee's
    # recompute key). When confirmed high-confidence it lets a check BLOCK — pseudobulk_integrity when the
    # key merges the arms, pairing when it makes a one-to-one match ambiguous. None = unconfirmed (the
    # checks stay diagnostic). Defining it as the FINAL key is what keeps a valid two-stage collapse from
    # a false blocker (adversarial pairing review); catalog §3.3.
    aggregation_key: Optional[list] = None
    # The pairing estimand says which contrast is targeted; it does NOT specify one-to-one mechanics.
    # A repeated-measures model may also target a within-pair estimand.
    pairing_estimand: Optional[str] = None
    # Closed mechanics contract. Only an explicit one_to_one declaration, together with a within-pair
    # estimand, can authorize a duplicate-pair blocker. Absence and repeated_measures abstain.
    pairing_mechanics: Literal["one_to_one", "repeated_measures"] | None = None
    # Optional and claim-bound. Absence never authorizes a relevance accusation.
    effect_relevance_contract: EffectRelevanceContract | None = None
    multiplicity_contract: MultiplicityContract | None = None
    report_inference_contract: ReportInferenceContract | None = None
    # "cell" when the reported analysis tested cells as replicates (a per-cell DE call);
    # "sample" when it is already replicate-level. Gates experimental_unit.applies_to. (C7)
    unit_of_test: Optional[str] = None
    # Nuisance columns the ANALYST fit conditioned on. None means the fitted design was not captured;
    # [] means the human explicitly confirmed that no nuisance columns were included.
    analyst_adjusted_for: Optional[list] = None
    fitted_design: FittedDesignDeclaration | None = None
    row_ledger: object | None = None
    # eQTL effect-allele orientation contract. All fields remain optional so an incomplete human
    # contract reaches the allele_orientation check as UNRESOLVED rather than failing config parsing.
    variant_id: Optional[str] = None
    genotype_column: Optional[str] = None
    target_feature: Optional[str] = None
    effect_allele: Optional[str] = None
    dosage_counts_allele: Optional[str] = None
    variant_alleles: Optional[tuple[str, str]] = None
    dosage_ploidy: Optional[int] = None
    effect_allele_frequency_interval: Optional[tuple[float, float]] = None
    effect_allele_frequency_scope: Optional[str] = None
    eqtl_estimator: Optional[str] = None
    eqtl_outcome_scale: Optional[str] = None
    # Hi-C loop-strength estimator contract. Optional so missing facts reach needs_evidence.
    hic_genome_assembly: Optional[str] = None
    hic_resolution_bp: Optional[int] = None
    hic_target_bin_i: Optional[str] = None
    hic_target_bin_j: Optional[str] = None
    hic_background_view_start: Optional[int] = None
    hic_background_view_end: Optional[int] = None
    hic_contact_scale: Optional[str] = None
    hic_expected_model: Optional[str] = None
    hic_mask_policy: Optional[str] = None
    hic_zero_policy: Optional[str] = None
    hic_pseudocount: Optional[float] = None
    hic_target_statistic: Optional[str] = None
    hic_replicate_functional: Optional[str] = None
    hic_report_delta_tolerance: Optional[float] = None
    hic_report_delta_tolerance_authority: Literal[
        "rounding_absolute_log2_ratio_delta"
    ] | None = None
    # Exact per-contrast scientific-premise binding.  Defaults preserve every legacy config.
    estimand_id: Optional[str] = None
    csp_contracts: tuple[object, ...] = ()

    def contrast_column_and_levels(self):
        """(contrast_column, reference_level, test_level).

        An eQTL's continuous contrast column is its genotype dosage; levels are inapplicable.
        Otherwise, if `test` is {col: val}, the contrast column is `col` with levels reference vs
        val. Otherwise it is a whole-condition contrast on `design.condition`. (C9)
        """
        if self.analysis_type == "eqtl":
            return self.genotype_column, None, None
        if isinstance(self.test, dict):
            (col, val), = self.test.items()
            return col, self.reference, val
        return self.condition, self.reference, self.test

    @property
    def target_term(self) -> str:
        """The model term being contrasted, e.g. 'condition' from 'condition[T.stim]'."""
        return (self.target_coefficient or "").split("[", 1)[0].strip()


def subset_mask(observations, design: Design):
    """Boolean row mask for `design.subset`. THE single definition — every consumer must use it.

    `aggregate_to_pseudobulk` previously ignored the subset while `confounding` honoured it, so
    estimability was judged on (say) T cells and the recompute ran on ALL cells. That grades the
    analyst against an analysis they never performed. (Opus review 2026-07-08.)
    """
    import numpy as np

    mask = np.ones(len(observations), dtype=bool)
    for col, val in (design.subset or {}).items():
        if col not in observations.columns:
            raise DesignError(
                f"subset column {col!r} is not present in the data — the confirmed subset "
                f"{design.subset} cannot be applied, so the audit would silently run on the FULL "
                f"dataset instead of the intended scope.")
        mask &= (observations[col] == val).to_numpy()
    return mask


def apply_subset(observations, design: Design):
    mask = subset_mask(observations, design)
    return observations if mask.all() else observations[mask]


class DesignError(ValueError):
    """The ratified design cannot be realized against this data. A CONFIG error, never a blocker.

    `blocker` must mean "your science is wrong", never "your YAML is wrong".
    """


def validate_design_against(observations, design: Design) -> None:
    """Raise DesignError if the declared contrast cannot be evaluated on these observations."""
    if design.analysis_type == "eqtl":
        # Missing orientation/data facts are verdict coverage, not malformed config. The eQTL check's
        # cannot_evaluate/UNRESOLVED split owns them. A declared subset is still authoritative and must
        # be realizable rather than silently discarded.
        apply_subset(observations, design)
        return
    contrast_col, reference, test = design.contrast_column_and_levels()
    if str(reference) == str(test):
        raise DesignError(
            f"reference and test levels must be distinct (both are {reference!r}); a degenerate "
            "contrast cannot be audited")
    if contrast_col not in observations.columns:
        raise DesignError(f"contrast column {contrast_col!r} is not present in the data "
                          f"(columns: {', '.join(map(str, observations.columns))})")
    obs = apply_subset(observations, design)
    present = set(map(str, obs[contrast_col].dropna().unique()))
    for role, level in (("reference", reference), ("test", test)):
        if str(level) not in present:
            raise DesignError(
                f"{role} level {level!r} is not present in column {contrast_col!r}"
                + (f" after applying subset {design.subset}" if design.subset else "")
                + f" (found: {', '.join(sorted(present)) or 'nothing'})")


def confidence_high(design: Design, role: str = "replicate_unit") -> bool:
    """Whether a check may emit a blocker, confidence-wise: is the human's ratification of the ROLE
    that check reasons about high-confidence? `confounding` passes `"condition"` (it reasons about
    condition/batch); `experimental_unit` passes `"replicate_unit"`. A missing key is not "high", so
    the gate is conservative (when in doubt, do not block). (Per-check gate, 2026-07-08 — replaced
    the single-key coupling that gated a condition/batch confounding blocker on replicate confidence.)"""
    return design.confidence.get(role) == "high"


def replicate_recorded(design: Design, observations) -> bool:
    """Is the biological replicate recorded? TRUE iff the human-confirmed `design.replicate_unit`
    names column(s) present in `.obs`. The design is authoritative — NOT the adapter's name-detection
    (`bundle.replicate_var`), which is only a hint for `init` and can miss a column named, say,
    `replicate`. (Coupling fix, 2026-07-08.)"""
    reps = list(design.replicate_unit or [])
    if not reps or observations is None:
        return False
    cols = {str(c) for c in observations.columns}
    return all(str(r) in cols for r in reps)


# patsy / R wrappers around a bare column name. `~ C(run) + condition` adjusts for `run`;
# failing to unwrap it makes the confounding check report `run` as OMITTED and emit a false
# `major` on a correctly-adjusted model. (adversarial review 2026-07-08.)
_WRAPPER = re.compile(
    r"^(?:C|factor|as\.factor|as_factor|categorical|scale|center|standardize)"
    r"\s*\(\s*([A-Za-z_]\w*)\s*(?:,[^)]*)?\)$"
)


def _unwrap(term: str) -> str:
    m = _WRAPPER.match(term)
    return m.group(1) if m else term


def model_terms(formula: str) -> set:
    """Parse the RHS of a patsy-style formula into its set of adjusted column names.

    '~ donor_id + condition' -> {'donor_id', 'condition'}
    '~ C(run) + condition'   -> {'run', 'condition'}      (the wrapper is not the variable)
    Interactions a:b / a*b are expanded into components; intercept tokens (1/0/-1) are dropped.
    """
    rhs = formula.split("~", 1)[1] if "~" in formula else formula
    terms: set = set()
    for part in rhs.split("+"):
        part = part.strip()
        if part in ("", "1", "0", "-1"):
            continue
        for sub in re.split(r"[:*]", part):
            sub = _unwrap(sub.strip())
            if sub and sub not in ("1", "0"):
                terms.add(sub)
    return terms
