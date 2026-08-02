from __future__ import annotations

import csv
import io
import math
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from sc_referee.calculation_checks.contracts import (
    selected_sidecar_contract,
    sidecar_adapter_manifest,
    with_sidecar_lineage,
)
from sc_referee.calculation_checks.core import (
    CalculationAdapterManifest,
    CalculationCheckManifest,
    CalculationCheckModule,
    CalculationCheckRegistry,
    CalculationContext,
    CalculationObservation,
    FrozenCalculationInput,
    NamedOperand,
    ObservationReceipt,
)
from sc_referee.calculation_checks.material_context import MaterialCalculationContext
from sc_referee.core.ids import semantic_digest, sha256_digest

MAX_TABLE_BYTES = 8 * 1024 * 1024
MAX_TABLE_ROWS = 50_000
MAX_TABLE_COLUMNS = 64
EFFECT_SIZE_CHECK_ID = "calculation-check:effect-size-relevance-summary-v1"

_BLOCK = re.compile(
    r"```sc-referee-effect-size-summary-v1\s*\n(?P<body>.*?)\n```",
    re.IGNORECASE | re.DOTALL,
)
_REQUIRED_KEYS = {
    "reported_table",
    "feature_id_column",
    "adjusted_p_column",
    "effect_column",
    "alpha",
    "effect_threshold",
    "effect_scale",
    "claim_semantics",
    "producer_binding",
}
_RECOGNITION_GRAMMAR_DIGEST = semantic_digest(
    {
        "block_pattern": _BLOCK.pattern,
        "required_keys": sorted(_REQUIRED_KEYS),
        "effect_scale": ["log2_fold_change"],
        "claim_semantics": [
            "biologically_relevant_discovery",
            "statistical_significance_only",
            "unresolved",
        ],
        "producer_binding": ["exact", "unresolved"],
        "ceilings": {
            "table_bytes": MAX_TABLE_BYTES,
            "table_rows": MAX_TABLE_ROWS,
            "table_columns": MAX_TABLE_COLUMNS,
        },
    }
)


class EffectSizeSummaryError(ValueError):
    """Raised when an effect-size declaration escapes the closed adapter contract."""


@dataclass(frozen=True)
class _Contract:
    reported_table: str
    feature_id_column: str
    adjusted_p_column: str
    effect_column: str
    alpha: float
    effect_threshold: float
    effect_scale: str
    claim_semantics: str
    producer_binding: str
    source_ref: dict[str, Any]


@dataclass(frozen=True)
class _Summary:
    row_count: int
    significant_count: int
    below_threshold_count: int
    below_threshold_fraction: float


class DeclaredEffectSizeSummaryAdapter:
    def __init__(self) -> None:
        self.manifest = CalculationAdapterManifest(
            adapter_id="calculation-adapter:declared-effect-size-summary-v1",
            adapter_version="1.0.0",
            implementation_digest=semantic_digest(
                {
                    "adapter_source": sha256_digest(Path(__file__).read_bytes()),
                    "recognition_grammar_digest": _RECOGNITION_GRAMMAR_DIGEST,
                }
            ),
            recognition_grammar_digest=_RECOGNITION_GRAMMAR_DIGEST,
        )

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        try:
            report = context.selected_report.content.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise EffectSizeSummaryError("selected report is not strict UTF-8") from error
        matches = list(_BLOCK.finditer(report))
        if not matches:
            return None
        if len(matches) != 1:
            return self._unsupported(
                context,
                context.selected_report.source_ref,
                "unique_effect_size_summary_contract",
                "The selected report contains more than one effect-size summary contract.",
            )
        match = matches[0]
        source_ref = _block_source(context.selected_report, report, match)
        try:
            contract = _parse_contract(match.group("body"), source_ref)
        except EffectSizeSummaryError as error:
            return self._unsupported(
                context,
                source_ref,
                "effect_size_summary_contract_valid",
                str(error),
            )
        return self.inspect_normalized(context, contract)

    def inspect_normalized(
        self,
        context: CalculationContext,
        contract: _Contract,
    ) -> CalculationObservation:
        source_ref = contract.source_ref
        if contract.claim_semantics == "statistical_significance_only":
            return self._not_applicable(context, contract)
        if contract.claim_semantics == "unresolved" or contract.producer_binding == "unresolved":
            return self._unsupported(
                context,
                source_ref,
                "effect_relevance_scope_resolved",
                "The biological-relevance claim or exact table binding remains unresolved; no relevance comparison ran.",
            )
        if not isinstance(context, MaterialCalculationContext):
            return self._unsupported(
                context,
                source_ref,
                "material_calculation_context_available",
                "The explicitly selected result table was not available in the frozen material-input view.",
            )
        table = _unique_material(context, contract.reported_table)
        if table is None:
            return self._unsupported(
                context,
                source_ref,
                "declared_result_table_bound",
                "Exactly one fully identified declared result table could not be bound.",
            )
        try:
            summary = _summarize(table, contract)
        except EffectSizeSummaryError as error:
            return self._unsupported(
                context,
                source_ref,
                "complete_effect_size_family_parsed",
                str(error),
                table=table,
            )
        sources = (source_ref, table.source_ref)
        return CalculationObservation(
            applicability="applicable",
            comparison_outcome=("nonconformant" if summary.below_threshold_count else "conformant"),
            target_ref=context.selected_surface_ref,
            input_refs=(context.selected_artifact_ref, table.artifact_ref),
            source_refs=sources,
            operands=(
                NamedOperand("reported_table_path", "string", table.path),
                NamedOperand("reported_family_rows", "integer", summary.row_count),
                NamedOperand("alpha", "finite_number", contract.alpha),
                NamedOperand("effect_threshold", "finite_number", contract.effect_threshold),
                NamedOperand("effect_scale", "string", contract.effect_scale),
                NamedOperand("significant_discoveries", "integer", summary.significant_count),
                NamedOperand(
                    "below_threshold_discoveries",
                    "integer",
                    summary.below_threshold_count,
                ),
                NamedOperand(
                    "below_threshold_fraction",
                    "finite_number",
                    summary.below_threshold_fraction,
                ),
                NamedOperand("claim_semantics", "string", contract.claim_semantics),
                NamedOperand("producer_binding", "string", contract.producer_binding),
            ),
            receipts=(
                ObservationReceipt(
                    "applicability",
                    "explicit_effect_relevance_contract",
                    "passed",
                    (source_ref,),
                    "One closed declaration names the exact result family, significance rule, effect scale, and relevance threshold.",
                ),
                ObservationReceipt(
                    "completeness",
                    "fully_identified_result_table",
                    "passed",
                    (table.source_ref,),
                    "The explicitly selected result table has a complete content digest.",
                ),
                ObservationReceipt(
                    "completeness",
                    "complete_declared_family_parsed",
                    "passed",
                    (table.source_ref,),
                    f"All {summary.row_count} rows parsed within the finite table ceilings.",
                ),
                ObservationReceipt(
                    "counterevidence",
                    "missing_or_nonfinite_significant_effects",
                    "passed",
                    sources,
                    "Every declared significant row had one finite effect value; none were silently omitted.",
                ),
            ),
            lineage_status="complete",
            limitations=(
                "This is an arithmetic comparison against the explicitly declared relevance floor; it does not establish that the floor is universally appropriate or that any effect is biologically real.",
                "No project-authored code was executed, and this module cannot emit a Finding.",
            ),
        )

    def _not_applicable(
        self, context: CalculationContext, contract: _Contract
    ) -> CalculationObservation:
        return CalculationObservation(
            applicability="not_applicable",
            comparison_outcome="not_applicable",
            target_ref=context.selected_surface_ref,
            input_refs=(context.selected_artifact_ref,),
            source_refs=(contract.source_ref,),
            operands=(),
            receipts=(
                ObservationReceipt(
                    "applicability",
                    "claim_is_statistical_significance_only",
                    "not_applicable",
                    (contract.source_ref,),
                    "The report does not declare its significant rows to satisfy a biological-relevance threshold.",
                ),
            ),
            lineage_status="not_applicable",
            limitations=(
                "No effect-relevance conformance comparison applies to a significance-only claim.",
            ),
        )

    def _unsupported(
        self,
        context: CalculationContext,
        source_ref: dict[str, Any],
        predicate: str,
        detail: str,
        *,
        table: FrozenCalculationInput | None = None,
    ) -> CalculationObservation:
        inputs = (
            (context.selected_artifact_ref,)
            if table is None
            else (
                context.selected_artifact_ref,
                table.artifact_ref,
            )
        )
        sources = (source_ref,) if table is None else (source_ref, table.source_ref)
        return CalculationObservation(
            applicability="unsupported",
            comparison_outcome="unknown",
            target_ref=context.selected_surface_ref,
            input_refs=inputs,
            source_refs=sources,
            operands=(),
            receipts=(
                ObservationReceipt("completeness", predicate, "unsupported", sources, detail),
            ),
            lineage_status="incomplete",
            limitations=(detail, "No effect-relevance disagreement was inferred."),
        )


class SelectedSidecarEffectSizeSummaryAdapter:
    def __init__(self) -> None:
        implementation_digest = sha256_digest(Path(__file__).read_bytes())
        self.manifest = sidecar_adapter_manifest(
            family="effect-size-summary",
            implementation_digest=implementation_digest,
        )
        self._evaluator = DeclaredEffectSizeSummaryAdapter()

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        sidecar = selected_sidecar_contract(context, check_id=EFFECT_SIZE_CHECK_ID)
        if sidecar is None:
            return None
        contract = _parse_contract_value(sidecar.value, sidecar.source_ref)
        return with_sidecar_lineage(
            self._evaluator.inspect_normalized(context, contract),
            sidecar,
        )


def effect_size_summary_registry() -> CalculationCheckRegistry:
    adapter = DeclaredEffectSizeSummaryAdapter()
    check = CalculationCheckManifest(
        check_id=EFFECT_SIZE_CHECK_ID,
        check_version="1.0.0",
        implementation_digest=sha256_digest(Path(__file__).read_bytes()),
        comparison_relation="declared_significant_family_effect_relevance_conformance",
        output_ceiling="disclosure_only",
        permitted_wording=(
            "Some discoveries in the explicitly bound significant family fall below the effect-size relevance floor declared for that report."
        ),
    )
    return CalculationCheckRegistry(
        (CalculationCheckModule(check, (adapter,)),),
        profile_id="deterministic_effect_size_summary_v1",
    )


def _parse_contract(body: str, source_ref: dict[str, Any]) -> _Contract:
    try:
        value = yaml.safe_load(body)
    except yaml.YAMLError as error:
        raise EffectSizeSummaryError("effect-size summary contract is not valid YAML") from error
    if not isinstance(value, dict):
        raise EffectSizeSummaryError("effect-size summary contract must be a mapping")
    return _parse_contract_value(value, source_ref)


def _parse_contract_value(value: dict[str, Any], source_ref: dict[str, Any]) -> _Contract:
    if set(value) != _REQUIRED_KEYS:
        raise EffectSizeSummaryError("effect-size summary contract keys are missing or extra")
    text_keys = _REQUIRED_KEYS - {"alpha", "effect_threshold"}
    if any(not isinstance(value[key], str) or not value[key].strip() for key in text_keys):
        raise EffectSizeSummaryError("effect-size summary text values must be nonempty strings")
    path = PurePosixPath(str(value["reported_table"]))
    if path.is_absolute() or ".." in path.parts or path.suffix.casefold() not in {".csv", ".tsv"}:
        raise EffectSizeSummaryError("reported table path must be a bounded CSV or TSV path")
    if value["effect_scale"] != "log2_fold_change":
        raise EffectSizeSummaryError("effect scale is outside the closed initial vocabulary")
    if value["claim_semantics"] not in {
        "biologically_relevant_discovery",
        "statistical_significance_only",
        "unresolved",
    }:
        raise EffectSizeSummaryError("claim semantics are outside the closed vocabulary")
    if value["producer_binding"] not in {"exact", "unresolved"}:
        raise EffectSizeSummaryError("producer binding is outside the closed vocabulary")
    alpha = _bounded_float(value["alpha"], "alpha", lower=0.0, upper=1.0, positive=True)
    threshold = _bounded_float(
        value["effect_threshold"],
        "effect threshold",
        lower=0.0,
        upper=None,
        positive=True,
    )
    return _Contract(
        reported_table=str(value["reported_table"]).strip(),
        feature_id_column=str(value["feature_id_column"]).strip(),
        adjusted_p_column=str(value["adjusted_p_column"]).strip(),
        effect_column=str(value["effect_column"]).strip(),
        alpha=alpha,
        effect_threshold=threshold,
        effect_scale=str(value["effect_scale"]).strip(),
        claim_semantics=str(value["claim_semantics"]).strip(),
        producer_binding=str(value["producer_binding"]).strip(),
        source_ref=source_ref,
    )


def _summarize(table: FrozenCalculationInput, contract: _Contract) -> _Summary:
    if len(table.content) > MAX_TABLE_BYTES:
        raise EffectSizeSummaryError("declared result table exceeds the byte ceiling")
    try:
        text = table.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise EffectSizeSummaryError("declared result table is not strict UTF-8") from error
    reader = csv.DictReader(
        io.StringIO(text, newline=""),
        delimiter="\t" if table.path.casefold().endswith(".tsv") else ",",
    )
    required = {
        contract.feature_id_column,
        contract.adjusted_p_column,
        contract.effect_column,
    }
    header = reader.fieldnames
    if (
        header is None
        or len(header) > MAX_TABLE_COLUMNS
        or len(set(header)) != len(header)
        or not required.issubset(header)
    ):
        raise EffectSizeSummaryError("declared result table columns are unavailable or ambiguous")
    identifiers: set[str] = set()
    significant = 0
    below = 0
    rows = 0
    for rows, row in enumerate(reader, start=1):
        if rows > MAX_TABLE_ROWS:
            raise EffectSizeSummaryError("declared result table exceeds the row ceiling")
        identifier = str(row.get(contract.feature_id_column, "")).strip()
        if not identifier or identifier in identifiers:
            raise EffectSizeSummaryError("result identifiers are empty or duplicated")
        identifiers.add(identifier)
        adjusted = _bounded_float(
            row.get(contract.adjusted_p_column),
            "adjusted p-value",
            lower=0.0,
            upper=1.0,
            positive=False,
        )
        effect = _finite_float(row.get(contract.effect_column), "effect value")
        if adjusted <= contract.alpha:
            significant += 1
            below += int(abs(effect) < contract.effect_threshold)
    if rows == 0:
        raise EffectSizeSummaryError("declared result table has no data rows")
    return _Summary(
        row_count=rows,
        significant_count=significant,
        below_threshold_count=below,
        below_threshold_fraction=(below / significant if significant else 0.0),
    )


def _bounded_float(
    value: object,
    label: str,
    *,
    lower: float,
    upper: float | None,
    positive: bool,
) -> float:
    number = _finite_float(value, label)
    if number < lower or (positive and number == lower) or (upper is not None and number > upper):
        raise EffectSizeSummaryError(f"{label} is outside the accepted range")
    return number


def _finite_float(value: object, label: str) -> float:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as error:
        raise EffectSizeSummaryError(f"{label} is not a finite number") from error
    if not math.isfinite(number):
        raise EffectSizeSummaryError(f"{label} is not a finite number")
    return number


def _unique_material(
    context: MaterialCalculationContext, path: str
) -> FrozenCalculationInput | None:
    matches = [item for item in context.material_inputs if item.path == path]
    return matches[0] if len(matches) == 1 else None


def _block_source(
    report: FrozenCalculationInput, text: str, match: re.Match[str]
) -> dict[str, Any]:
    start = text.count("\n", 0, match.start()) + 1
    end = text.count("\n", 0, match.end()) + 1
    return {
        "source_kind": "file_span",
        "locator": f"{report.path}:{start}-{end}",
        "path": report.path,
        "content_digest": report.content_digest,
        "start_line": start,
        "end_line": end,
        "quoted_text": match.group(0),
    }
