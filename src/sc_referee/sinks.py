"""Typed sink contracts — the shared foundation for the next wave of checks.

The provenance engine's reusable abstraction is not `DataDerived`; it is
`source/selection -> derived value -> inferential SINK + overlap + calibration contract + report
binding`. So the engine needs TYPED SINKS as much as more taint sources: a check must know, for a call,
whether it is inferential at all, which argument is the response / grouping / block, what input scale
and unit the method assumes, whether it emits calibrated p-values, whether it is selection-aware, and
where its output lands for claim attribution. This module is that registry.

The invariant that keeps the expansion honest: a check may only reach `blocker` when the contract is
resolved to an EXACT symbol + compatible version (`resolve_sink_status` returns status `"exact"`). An
unknown symbol, or a version outside the contract's spec, resolves to `None` -> the caller emits
`needs_evidence` ("unknown means review"). No blocker is ever built on an unresolved contract.
(error-catalog round-2 spec; the design notes §3.2; adversarial design consult.)
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class ValueType:
    """What a value IS, for overlap/scale/unit reasoning. Fields may be `unknown`; feature/observation
    sets may be symbolic (`hvg_set@call_12`, `cells[donor=D1]`) — an `unknown` set can't establish the
    overlap a blocker needs."""
    kind: str = "unknown"          # counts|continuous|labels|embedding|graph|proportions|pvalue|qvalue|effect|statistic
    modality: str = "unknown"      # RNA|ADT|ATAC|spatial|metadata|unknown
    scale: str = "unknown"         # raw_counts|normalized_counts|log_normalized|residualized|imputed|integrated|probability|unknown
    unit: str = "unknown"          # cell|spot|sample|aggregate|feature|unknown
    origins: frozenset = frozenset({"unknown"})   # primary_data|metadata|external|selected|imputed|integrated|held_out|unknown
    artifact_id: str | None = None
    feature_set: frozenset | None = None
    observation_set: frozenset | None = None


@dataclass(frozen=True)
class PortLocator:
    """WHERE a port's argument sits in the call. `kind`: "kw" (a keyword arg `name`), "arg" (positional
    `index`), or "receiver" (a true method call's object — reserved for `obj.method(...)`, NOT free
    functions like scanpy/scipy). A port lists ALTERNATIVES; the binder tries keyword before positional,
    and only uses positional when the version's positional slot is stable. (adversarial review Q3.)"""
    kind: str                      # "kw" | "arg" | "receiver"
    name: str | None = None
    index: int | None = None


def _kw(name: str) -> PortLocator:
    return PortLocator("kw", name=name)


def _arg(index: int) -> PortLocator:
    return PortLocator("arg", index=index)


@dataclass(frozen=True)
class InputPort:
    role: str                      # response|response_a|response_b|grouping|design|block|offset|weights|selection|train|test|universe
    locators: tuple = ()           # ordered PortLocator alternatives; keyword wins over positional
    accepted_kinds: frozenset = frozenset()
    accepted_modalities: frozenset = frozenset({"RNA", "unknown"})
    accepted_scales: frozenset = frozenset()
    accepted_units: frozenset = frozenset()
    required: bool = True


@dataclass(frozen=True)
class CalibrationContract:
    output_kind: str = "pvalue"    # unknown|none|pvalue|qvalue|confidence_interval|score
    null_family: str = "two_group_difference"   # ...|association|enrichment|prediction_error|differential_abundance|custom
    independence_semantics: str = "iid_rows"    # iid_rows|clustered|paired|blocked|restricted_permutation|none|unknown
    block_port: str | None = None
    internal_multiplicity: str = "none"         # none|bh|bonferroni|method_specific


@dataclass(frozen=True)
class SelectionContract:
    handling: str = "naive"        # naive|independent_split|selective_inference|internally_joint|descriptive|unknown
    protected_selection_kinds: frozenset = frozenset()   # clustering|feature_selection|trajectory|domain_selection|model_selection|any
    proof_obligations: tuple = ()


@dataclass(frozen=True)
class ReportContract:
    output_location: str = "return"   # return|return.column|receiver.uns|receiver.obs|side_effect
    pvalue_fields: tuple = ()
    qvalue_fields: tuple = ()
    effect_fields: tuple = ()
    grouping_field: str | None = None


@dataclass(frozen=True)
class SinkContract:
    contract_id: str
    module: str
    symbol: str
    sink_kind: str                 # de|marker|bayesian_de|descriptive_ranking|da|correlation|enrichment|permutation|classifier|aggregation|trajectory_test
    inputs: tuple = ()
    calibration: CalibrationContract = field(default_factory=CalibrationContract)
    selection: SelectionContract = field(default_factory=SelectionContract)
    report: ReportContract = field(default_factory=ReportContract)
    versions: str = ""             # PEP 440 specifier (">=1.9,<2"); "" = any
    language: str = "python"
    source_digest: str | None = None

    @property
    def evidence_level(self) -> str:
        """Whether this entry is eligible for exact resolution."""
        return "inferred" if self.contract_id in _INFERRED_CONTRACT_IDS else "verified"


@dataclass(frozen=True)
class _ConditionalVariant:
    """Literal-argument specialization for a multiplexed public API."""
    contract_id: str
    argument_values: frozenset
    sink_kind: str
    inputs: tuple
    calibration: CalibrationContract
    selection: SelectionContract
    report: ReportContract


# --- initial registry (intentionally small; unknown calls abstain) -------------------------------
# Locators verified against the actual signatures (adversarial review consult, web-checked):
#   scanpy.tl.rank_genes_groups(adata, groupby, *, ...)   scipy.stats.ttest_ind(a, b, *, ...)
#   scipy.stats.mannwhitneyu(x, y, *, ...)   pydeseq2.dds.DeseqDataSet(*, counts, metadata, design, ...)
#   Seurat::FindMarkers(object, ident.1, ...)  <- R, so grouping is bound by NAME only (no positional guess)
_CONTINUOUS = frozenset({"normalized_counts", "log_normalized", "residualized"})

_RANK_GENES_GROUPS = SinkContract(
    contract_id="scanpy.tl.rank_genes_groups.v1", module="scanpy.tl", symbol="rank_genes_groups",
    sink_kind="marker",
    inputs=(
        InputPort(role="response", locators=(_kw("adata"), _arg(0)),
                  accepted_kinds=frozenset({"counts", "continuous"}),
                  accepted_scales=frozenset({"raw_counts", "normalized_counts", "log_normalized"}),
                  accepted_units=frozenset({"cell"})),
        InputPort(role="grouping", locators=(_kw("groupby"), _arg(1)),
                  accepted_kinds=frozenset({"labels"}), accepted_units=frozenset({"cell"})),
    ),
    calibration=CalibrationContract(output_kind="pvalue", null_family="two_group_difference",
                                    independence_semantics="iid_rows", internal_multiplicity="bh"),
    selection=SelectionContract(handling="naive", protected_selection_kinds=frozenset({"clustering"})),
    report=ReportContract(output_location="receiver.uns", pvalue_fields=("pvals", "pvals_adj"),
                          grouping_field="groupby"),
    versions=">=1.9,<2",
)

_FINDMARKERS = SinkContract(
    # test.use changes both calibration and expression slot. This base is deliberately non-asserting.
    contract_id="seurat.FindMarkers.v4.unresolved", module="Seurat", symbol="FindMarkers",
    sink_kind="marker",
    language="r",
    inputs=(
        InputPort(role="response", locators=(_kw("object"), _arg(0)),
                  accepted_kinds=frozenset(), accepted_scales=frozenset(),
                  accepted_units=frozenset({"cell"})),
        # R group semantics differ across ident.1 / group.by / cells.1 — bind the named arg, never guess
        # a positional slot (adversarial review Q3). No R AST binder yet, so a positional-only call abstains.
        InputPort(role="grouping", locators=(_kw("ident.1"),), accepted_kinds=frozenset({"labels"}),
                  accepted_units=frozenset({"cell"})),
    ),
    calibration=CalibrationContract(output_kind="unknown", null_family="custom",
                                    independence_semantics="unknown", internal_multiplicity="unknown"),
    selection=SelectionContract(handling="unknown"),
    report=ReportContract(output_location="return.column"),
    versions=">=4,<6",
)

_FINDMARKERS_GROUPING = next(port for port in _FINDMARKERS.inputs if port.role == "grouping")


def _findmarkers_response(kinds, scales):
    return InputPort(role="response", locators=(_kw("object"), _arg(0)),
                     accepted_kinds=frozenset(kinds), accepted_scales=frozenset(scales),
                     accepted_units=frozenset({"cell"}))


_FINDMARKERS_PVALUE = CalibrationContract(
    output_kind="pvalue", null_family="two_group_difference",
    independence_semantics="iid_rows", internal_multiplicity="bonferroni")
_FINDMARKERS_NAIVE = SelectionContract(
    handling="naive", protected_selection_kinds=frozenset({"clustering"}))
_FINDMARKERS_PVALUE_REPORT = ReportContract(
    output_location="return.column", pvalue_fields=("p_val", "p_val_adj"),
    effect_fields=("avg_log2FC",))

_FINDMARKERS_VARIANTS = (
    _ConditionalVariant(
        contract_id="seurat.FindMarkers.v4.wilcox",
        argument_values=frozenset({"wilcox"}), sink_kind="marker",
        inputs=(_findmarkers_response(
            {"continuous"}, {"log_normalized", "normalized_counts"}), _FINDMARKERS_GROUPING),
        calibration=_FINDMARKERS_PVALUE, selection=_FINDMARKERS_NAIVE,
        report=_FINDMARKERS_PVALUE_REPORT,
    ),
    _ConditionalVariant(
        contract_id="seurat.FindMarkers.v4.count",
        argument_values=frozenset({"negbinom", "DESeq2"}), sink_kind="marker",
        inputs=(_findmarkers_response({"counts"}, {"raw_counts"}), _FINDMARKERS_GROUPING),
        calibration=_FINDMARKERS_PVALUE, selection=_FINDMARKERS_NAIVE,
        report=_FINDMARKERS_PVALUE_REPORT,
    ),
    _ConditionalVariant(
        contract_id="seurat.FindMarkers.v4.roc",
        argument_values=frozenset({"roc"}), sink_kind="classifier",
        # Slot/scale and output-column details were not runtime-verified: force scale/report abstention.
        inputs=(_findmarkers_response(set(), set()), _FINDMARKERS_GROUPING),
        calibration=CalibrationContract(
            output_kind="score", null_family="prediction_error",
            independence_semantics="none", internal_multiplicity="none"),
        selection=SelectionContract(
            handling="descriptive", protected_selection_kinds=frozenset({"clustering"})),
        report=ReportContract(output_location="return.column"),
    ),
)

_TTEST_IND = SinkContract(
    contract_id="scipy.stats.ttest_ind.v1", module="scipy.stats", symbol="ttest_ind", sink_kind="de",
    inputs=(
        InputPort(role="response_a", locators=(_kw("a"), _arg(0)), accepted_kinds=frozenset({"continuous"}),
                  accepted_scales=_CONTINUOUS, accepted_units=frozenset({"cell", "sample", "aggregate"})),
        InputPort(role="response_b", locators=(_kw("b"), _arg(1)), accepted_kinds=frozenset({"continuous"}),
                  accepted_scales=_CONTINUOUS, accepted_units=frozenset({"cell", "sample", "aggregate"})),
    ),
    calibration=CalibrationContract(independence_semantics="iid_rows"),
    report=ReportContract(output_location="return"),
    versions=">=1.9,<2",
)

_MANNWHITNEYU = SinkContract(
    contract_id="scipy.stats.mannwhitneyu.v1", module="scipy.stats", symbol="mannwhitneyu", sink_kind="de",
    inputs=(
        InputPort(role="response_a", locators=(_kw("x"), _arg(0)),
                  accepted_kinds=frozenset({"continuous", "statistic"}),
                  accepted_scales=_CONTINUOUS | frozenset({"raw_counts"}),
                  accepted_units=frozenset({"cell", "sample", "aggregate"})),
        InputPort(role="response_b", locators=(_kw("y"), _arg(1)),
                  accepted_kinds=frozenset({"continuous", "statistic"}),
                  accepted_scales=_CONTINUOUS | frozenset({"raw_counts"}),
                  accepted_units=frozenset({"cell", "sample", "aggregate"})),
    ),
    calibration=CalibrationContract(independence_semantics="iid_rows"),
    versions=">=1.9,<2",
)

_DESEQ = SinkContract(
    contract_id="pydeseq2.DeseqDataSet.v1", module="pydeseq2.dds", symbol="DeseqDataSet", sink_kind="de",
    inputs=(
        # counts is the primary raw-count response; `adata` is the alternate AnnData-based response
        # source (both keyword-only in current pydeseq2). Scale verification is deferred to later checks.
        InputPort(role="response", locators=(_kw("counts"), _kw("adata")),
                  accepted_kinds=frozenset({"counts"}), accepted_scales=frozenset({"raw_counts"}),
                  accepted_units=frozenset({"sample", "aggregate"})),
        InputPort(role="design", locators=(_kw("design"), _kw("design_factors")),
                  accepted_kinds=frozenset({"labels", "metadata"}), required=False),
    ),
    calibration=CalibrationContract(null_family="two_group_difference", independence_semantics="iid_rows",
                                    internal_multiplicity="bh"),
    report=ReportContract(output_location="return.column", pvalue_fields=("pvalue", "padj")),
)

_SCVI_DIFFERENTIAL_EXPRESSION = SinkContract(
    contract_id="scvi.model.SCVI.differential_expression.v1", module="scvi.model.SCVI",
    symbol="differential_expression", sink_kind="bayesian_de", inputs=(),
    calibration=CalibrationContract(
        output_kind="score", null_family="custom", independence_semantics="unknown",
        internal_multiplicity="none"),
    selection=SelectionContract(handling="unknown"),
    # Posterior probabilities/Bayes factors/posterior-FDR flags are never frequentist p/q fields.
    report=ReportContract(output_location="return"),
)

_SCANVI_DIFFERENTIAL_EXPRESSION = replace(
    _SCVI_DIFFERENTIAL_EXPRESSION,
    contract_id="scvi.model.SCANVI.differential_expression.v1", module="scvi.model.SCANVI")

_RANK_VELOCITY_GENES = SinkContract(
    contract_id="scvelo.tl.rank_velocity_genes.v1", module="scvelo.tl",
    symbol="rank_velocity_genes", sink_kind="descriptive_ranking", inputs=(),
    calibration=CalibrationContract(
        output_kind="score", null_family="custom", independence_semantics="unknown",
        internal_multiplicity="none"),
    selection=SelectionContract(
        handling="descriptive", protected_selection_kinds=frozenset({"trajectory"})),
    report=ReportContract(output_location="receiver.uns"),
)

_REGISTRY = (
    _RANK_GENES_GROUPS, _FINDMARKERS, _TTEST_IND, _MANNWHITNEYU, _DESEQ,
    _SCVI_DIFFERENTIAL_EXPRESSION, _SCANVI_DIFFERENTIAL_EXPRESSION,
    _RANK_VELOCITY_GENES,
)

_CONDITIONAL_VARIANTS = {
    _FINDMARKERS.contract_id: ("test.use", "wilcox", _FINDMARKERS_VARIANTS),
}

# All semantic/version details for these entries are cataloged as inferred. They are discoverable but
# may never resolve to blocker-grade evidence until runtime verification promotes them.
_INFERRED_CONTRACT_IDS = frozenset({
    _SCVI_DIFFERENTIAL_EXPRESSION.contract_id,
    _SCANVI_DIFFERENTIAL_EXPRESSION.contract_id,
    _RANK_VELOCITY_GENES.contract_id,
})


def _module_ok(contract_module: str, module) -> bool:
    # EXACT match (module is already canonicalized by resolve_callee). Suffix matching let
    # `project.scipy.stats` masquerade as `scipy.stats` (adversarial re-review blocker #4). module=None is the
    # symbol-only path used by direct callers/tests, not by import-resolved binding.
    return module is None or module == contract_module


def _version_check(spec: str, version):
    """True = compatible, False = outside spec, None = cannot determine (no packaging / unparseable
    version). A version we cannot confirm must NOT be treated as compatible (adversarial re-review #7)."""
    try:
        from packaging.specifiers import InvalidSpecifier, SpecifierSet
        from packaging.version import InvalidVersion, Version
        try:
            v = Version(str(version))
            return v in SpecifierSet(spec)
        except (InvalidVersion, InvalidSpecifier):
            return None
    except Exception:                      # packaging unavailable -> cannot confirm
        return None


def sink_symbols() -> frozenset:
    """The lowercased symbols the registry knows — used to flag a sink-NAMED call that failed to resolve
    (so it becomes a review candidate rather than silently vanishing)."""
    return frozenset(c.symbol.lower() for c in _REGISTRY)


def sink_contract_candidates(symbol, module=None) -> tuple:
    """Identity-matching entries, including inferred candidates that cannot resolve exactly."""
    return tuple(c for c in _REGISTRY
                 if c.symbol == str(symbol) and _module_ok(c.module, module))


def _specialize_condition(contract, arguments):
    conditional = _CONDITIONAL_VARIANTS.get(contract.contract_id)
    if conditional is None:
        return contract, "exact"
    argument_name, default_value, variants = conditional
    # None = no argument evidence. {} = the call was inspected and the library default applies.
    if arguments is None:
        return None, "argument_unknown"
    value = arguments.get(argument_name, default_value)
    if not isinstance(value, str):
        return None, "argument_unknown"
    for variant in variants:
        if value in variant.argument_values:
            return replace(
                contract, contract_id=variant.contract_id, sink_kind=variant.sink_kind,
                inputs=variant.inputs, calibration=variant.calibration,
                selection=variant.selection, report=variant.report), "exact"
    return None, "argument_mismatch"


def resolve_sink_status(symbol, module=None, version=None, arguments=None):
    """Resolve a contract and its blocker-eligibility status. Status is:
      "exact"           — symbol+module matched and, for a pinned contract, the version is CONFIRMED
                          compatible, with conditional literal arguments confirmed;
      "version_unknown" — symbol matched a pinned contract but no version was supplied to confirm it;
                          the contract is returned for structural use but MAY NOT underpin a blocker;
      "version_mismatch"— symbol matched but the stated version is OUTSIDE the pin (contract is None);
      "argument_unknown"— no literal argument evidence for a conditional calibration;
      "argument_mismatch"— the literal argument is outside the verified conditional set;
      "needs_evidence"  — an inferred catalog candidate matched and cannot resolve exactly;
      "unknown_symbol"  — no contract for this symbol/module.
    Only "exact" may underpin a blocker — an unconfirmed version must not be laundered as exact (adversarial review
    review #5). The reason is returned explicitly rather than inferred from a bare `None`."""
    # case-SENSITIVE identity: Python/R are case-sensitive, so `DESEQDATASET` is not `DeseqDataSet`
    # (adversarial re-review #7). Lowercasing is only for the candidate-detection net, never for binding.
    for c in _REGISTRY:
        if c.symbol != str(symbol) or not _module_ok(c.module, module):
            continue
        if c.contract_id in _INFERRED_CONTRACT_IDS:
            return None, "needs_evidence"
        if not c.versions:
            return _specialize_condition(c, arguments)
        if version is None:
            return ((None, "version_unknown") if c.contract_id in _CONDITIONAL_VARIANTS
                    else (c, "version_unknown"))
        chk = _version_check(c.versions, version)
        if chk is None:
            return ((None, "version_unknown") if c.contract_id in _CONDITIONAL_VARIANTS
                    else (c, "version_unknown"))
        if not chk:
            return None, "version_mismatch"
        return _specialize_condition(c, arguments)
    return None, "unknown_symbol"


def resolve_sink(symbol, module=None, version=None, arguments=None):
    """Resolved contract, with structural fallback for legacy no-version registry inspection."""
    contract, status = resolve_sink_status(symbol, module, version, arguments)
    if contract is None and status == "version_unknown" and version is None:
        candidates = sink_contract_candidates(symbol, module)
        return candidates[0] if candidates else None
    return contract
