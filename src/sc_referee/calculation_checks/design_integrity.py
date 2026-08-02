from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
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
MAX_TABLE_ROWS = 100_000
MAX_TABLE_COLUMNS = 64
MAX_DECLARED_COLUMNS = 16
DESIGN_INTEGRITY_CHECK_ID = "calculation-check:tabular-design-integrity-v1"

_BLOCK = re.compile(
    r"```sc-referee-design-integrity-v1\s*\n(?P<body>.*?)\n```",
    re.IGNORECASE | re.DOTALL,
)
_REQUIRED_KEYS = {
    "metadata_table",
    "condition_column",
    "reference_level",
    "test_level",
    "replicate_columns",
    "pairing_columns",
    "aggregation_columns",
    "required_categorical_adjustment_columns",
    "fitted_fixed_effect_columns",
    "fitted_random_intercept_columns",
    "comparison_mode",
    "aggregation_binding",
    "model_binding",
}
_RECOGNITION_GRAMMAR_DIGEST = semantic_digest(
    {
        "block_pattern": _BLOCK.pattern,
        "required_keys": sorted(_REQUIRED_KEYS),
        "comparison_mode": ["paired", "unpaired", "unresolved"],
        "binding": ["exact", "unresolved"],
        "adjustment_type": "categorical_main_effects",
        "ceilings": {
            "table_bytes": MAX_TABLE_BYTES,
            "table_rows": MAX_TABLE_ROWS,
            "table_columns": MAX_TABLE_COLUMNS,
            "declared_columns_per_role": MAX_DECLARED_COLUMNS,
        },
    }
)


class DesignIntegrityError(ValueError):
    """Raised when a design-integrity input escapes the closed contract."""


@dataclass(frozen=True)
class _Contract:
    metadata_table: str
    condition_column: str
    reference_level: str
    test_level: str
    replicate_columns: tuple[str, ...]
    pairing_columns: tuple[str, ...]
    aggregation_columns: tuple[str, ...]
    required_adjustment_columns: tuple[str, ...]
    fitted_fixed_effect_columns: tuple[str, ...]
    fitted_random_intercept_columns: tuple[str, ...]
    comparison_mode: str
    aggregation_binding: str
    model_binding: str
    source_ref: dict[str, Any]


@dataclass(frozen=True)
class _Metrics:
    row_count: int
    contrast_rows: int
    reference_rows: int
    test_rows: int
    missing_aggregation_rows: int
    merged_aggregation_groups: int
    complete_pairing_levels: int
    incomplete_pairing_levels: int
    pairing_omitted: bool
    paired_comparison_unusable: bool
    omitted_adjustments: tuple[str, ...]
    condition_aliased_with_adjustments: bool

    @property
    def nonconformant(self) -> bool:
        return bool(
            self.missing_aggregation_rows
            or self.merged_aggregation_groups
            or self.pairing_omitted
            or self.paired_comparison_unusable
            or self.omitted_adjustments
            or self.condition_aliased_with_adjustments
        )


class DeclaredDesignIntegrityAdapter:
    def __init__(self) -> None:
        self.manifest = CalculationAdapterManifest(
            adapter_id="calculation-adapter:declared-tabular-design-integrity-v1",
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
            raise DesignIntegrityError("selected report is not strict UTF-8") from error
        matches = list(_BLOCK.finditer(report))
        if not matches:
            return None
        if len(matches) != 1:
            return self._unsupported(
                context,
                context.selected_report.source_ref,
                "unique_design_integrity_contract",
                "The selected report contains more than one design-integrity contract.",
            )
        match = matches[0]
        source_ref = _block_source(context.selected_report, report, match)
        try:
            contract = _parse_contract(match.group("body"), source_ref)
        except DesignIntegrityError as error:
            return self._unsupported(
                context,
                source_ref,
                "design_integrity_contract_valid",
                str(error),
            )
        return self.inspect_normalized(context, contract)

    def inspect_normalized(
        self,
        context: CalculationContext,
        contract: _Contract,
    ) -> CalculationObservation:
        source_ref = contract.source_ref
        if (
            contract.comparison_mode == "unresolved"
            or contract.aggregation_binding == "unresolved"
            or contract.model_binding == "unresolved"
        ):
            return self._unsupported(
                context,
                source_ref,
                "design_and_producer_bindings_resolved",
                "The comparison mode, aggregation producer, or fitted-model binding remains unresolved; no structural conclusion was drawn.",
            )
        if not isinstance(context, MaterialCalculationContext):
            return self._unsupported(
                context,
                source_ref,
                "material_calculation_context_available",
                "The explicitly selected metadata table was not available in the frozen material-input view.",
            )
        table = _unique_material(context, contract.metadata_table)
        if table is None:
            return self._unsupported(
                context,
                source_ref,
                "declared_metadata_table_bound",
                "Exactly one fully identified declared metadata table could not be bound.",
            )
        try:
            metrics = _evaluate_table(table, contract)
        except DesignIntegrityError as error:
            return self._unsupported(
                context,
                source_ref,
                "complete_design_metadata_parsed",
                str(error),
                table=table,
            )
        sources = (source_ref, table.source_ref)
        return CalculationObservation(
            applicability="applicable",
            comparison_outcome="nonconformant" if metrics.nonconformant else "conformant",
            target_ref=context.selected_surface_ref,
            input_refs=(context.selected_artifact_ref, table.artifact_ref),
            source_refs=sources,
            operands=(
                NamedOperand("metadata_table_path", "string", table.path),
                NamedOperand("metadata_rows", "integer", metrics.row_count),
                NamedOperand("contrast_rows", "integer", metrics.contrast_rows),
                NamedOperand("reference_rows", "integer", metrics.reference_rows),
                NamedOperand("test_rows", "integer", metrics.test_rows),
                NamedOperand(
                    "missing_aggregation_rows", "integer", metrics.missing_aggregation_rows
                ),
                NamedOperand(
                    "merged_aggregation_groups", "integer", metrics.merged_aggregation_groups
                ),
                NamedOperand("complete_pairing_levels", "integer", metrics.complete_pairing_levels),
                NamedOperand(
                    "incomplete_pairing_levels", "integer", metrics.incomplete_pairing_levels
                ),
                NamedOperand("pairing_omitted", "boolean", metrics.pairing_omitted),
                NamedOperand(
                    "paired_comparison_unusable",
                    "boolean",
                    metrics.paired_comparison_unusable,
                ),
                NamedOperand(
                    "required_adjustments_omitted",
                    "string_array",
                    list(metrics.omitted_adjustments),
                ),
                NamedOperand(
                    "condition_aliased_with_required_adjustments",
                    "boolean",
                    metrics.condition_aliased_with_adjustments,
                ),
                NamedOperand("comparison_mode", "string", contract.comparison_mode),
                NamedOperand(
                    "aggregation_columns", "string_array", list(contract.aggregation_columns)
                ),
                NamedOperand("replicate_columns", "string_array", list(contract.replicate_columns)),
                NamedOperand("pairing_columns", "string_array", list(contract.pairing_columns)),
                NamedOperand(
                    "required_categorical_adjustment_columns",
                    "string_array",
                    list(contract.required_adjustment_columns),
                ),
            ),
            receipts=(
                ObservationReceipt(
                    "applicability",
                    "explicit_design_integrity_contract",
                    "passed",
                    (source_ref,),
                    "One closed declaration binds the contrast, identities, aggregation, pairing, required categorical adjustments, and fitted model fields.",
                ),
                ObservationReceipt(
                    "completeness",
                    "fully_identified_metadata_table",
                    "passed",
                    (table.source_ref,),
                    "The explicitly selected metadata table has a complete content digest.",
                ),
                ObservationReceipt(
                    "completeness",
                    "complete_contrast_metadata_parsed",
                    "passed",
                    (table.source_ref,),
                    f"All {metrics.row_count} metadata rows parsed and both exact contrast levels were present.",
                ),
                ObservationReceipt(
                    "counterevidence",
                    "alternate_design_semantics",
                    "passed",
                    (source_ref,),
                    "The finite check is limited to the explicitly bound aggregation and model semantics; unresolved or alternate semantics would have forced abstention.",
                ),
            ),
            lineage_status="complete",
            limitations=(
                "The aliasing calculation covers declared categorical main effects only; it does not interpret continuous covariates, interactions, arbitrary formulas, or hidden preprocessing.",
                "Pair availability and aggregation structure do not by themselves establish bias, numerical impact, execution, or universal method adequacy.",
                "No project-authored code was executed, and this module cannot emit a Finding.",
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
            limitations=(detail, "No design-integrity disagreement was inferred."),
        )


class SelectedSidecarDesignIntegrityAdapter:
    def __init__(self) -> None:
        self.manifest = sidecar_adapter_manifest(
            family="tabular-design-integrity",
            implementation_digest=sha256_digest(Path(__file__).read_bytes()),
        )
        self._evaluator = DeclaredDesignIntegrityAdapter()

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        sidecar = selected_sidecar_contract(context, check_id=DESIGN_INTEGRITY_CHECK_ID)
        if sidecar is None:
            return None
        contract = _parse_contract_value(sidecar.value, sidecar.source_ref)
        return with_sidecar_lineage(
            self._evaluator.inspect_normalized(context, contract),
            sidecar,
        )


def design_integrity_registry() -> CalculationCheckRegistry:
    adapter = DeclaredDesignIntegrityAdapter()
    check = CalculationCheckManifest(
        check_id=DESIGN_INTEGRITY_CHECK_ID,
        check_version="1.0.0",
        implementation_digest=sha256_digest(Path(__file__).read_bytes()),
        comparison_relation="declared_tabular_design_structure_conformance",
        output_ceiling="disclosure_only",
        permitted_wording=(
            "The explicitly bound metadata and design declaration contain one or more exact aggregation, pairing, required-adjustment, or categorical-aliasing incompatibilities."
        ),
    )
    return CalculationCheckRegistry(
        (CalculationCheckModule(check, (adapter,)),),
        profile_id="deterministic_tabular_design_integrity_v1",
    )


def _parse_contract(body: str, source_ref: dict[str, Any]) -> _Contract:
    try:
        value = yaml.safe_load(body)
    except yaml.YAMLError as error:
        raise DesignIntegrityError("design-integrity contract is not valid YAML") from error
    if not isinstance(value, dict):
        raise DesignIntegrityError("design-integrity contract must be a mapping")
    return _parse_contract_value(value, source_ref)


def _parse_contract_value(value: dict[str, Any], source_ref: dict[str, Any]) -> _Contract:
    if set(value) != _REQUIRED_KEYS:
        raise DesignIntegrityError("design-integrity contract keys are missing or extra")
    for key in {
        "metadata_table",
        "condition_column",
        "reference_level",
        "test_level",
        "comparison_mode",
        "aggregation_binding",
        "model_binding",
    }:
        if not isinstance(value[key], str) or not value[key].strip():
            raise DesignIntegrityError("design-integrity text values must be nonempty strings")
    path = PurePosixPath(str(value["metadata_table"]))
    if path.is_absolute() or ".." in path.parts or path.suffix.casefold() not in {".csv", ".tsv"}:
        raise DesignIntegrityError("metadata table path must be a bounded CSV or TSV path")
    if value["reference_level"] == value["test_level"]:
        raise DesignIntegrityError("reference and test levels must differ")
    if value["comparison_mode"] not in {"paired", "unpaired", "unresolved"}:
        raise DesignIntegrityError("comparison mode is outside the closed vocabulary")
    if value["aggregation_binding"] not in {"exact", "unresolved"} or value[
        "model_binding"
    ] not in {"exact", "unresolved"}:
        raise DesignIntegrityError("design binding is outside the closed vocabulary")
    lists = {
        key: _column_list(value[key], key)
        for key in {
            "replicate_columns",
            "pairing_columns",
            "aggregation_columns",
            "required_categorical_adjustment_columns",
            "fitted_fixed_effect_columns",
            "fitted_random_intercept_columns",
        }
    }
    if not lists["replicate_columns"] or not lists["aggregation_columns"]:
        raise DesignIntegrityError("replicate and aggregation column lists must be nonempty")
    if value["comparison_mode"] == "paired" and not lists["pairing_columns"]:
        raise DesignIntegrityError("a paired comparison requires pairing columns")
    return _Contract(
        metadata_table=str(value["metadata_table"]).strip(),
        condition_column=str(value["condition_column"]).strip(),
        reference_level=str(value["reference_level"]).strip(),
        test_level=str(value["test_level"]).strip(),
        replicate_columns=lists["replicate_columns"],
        pairing_columns=lists["pairing_columns"],
        aggregation_columns=lists["aggregation_columns"],
        required_adjustment_columns=lists["required_categorical_adjustment_columns"],
        fitted_fixed_effect_columns=lists["fitted_fixed_effect_columns"],
        fitted_random_intercept_columns=lists["fitted_random_intercept_columns"],
        comparison_mode=str(value["comparison_mode"]).strip(),
        aggregation_binding=str(value["aggregation_binding"]).strip(),
        model_binding=str(value["model_binding"]).strip(),
        source_ref=source_ref,
    )


def _column_list(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > MAX_DECLARED_COLUMNS:
        raise DesignIntegrityError(f"{label} must be a bounded list")
    columns = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    if len(columns) != len(value) or len(set(columns)) != len(columns):
        raise DesignIntegrityError(f"{label} contains an empty, non-text, or duplicate column")
    return columns


def _evaluate_table(table: FrozenCalculationInput, contract: _Contract) -> _Metrics:
    if len(table.content) > MAX_TABLE_BYTES:
        raise DesignIntegrityError("declared metadata table exceeds the byte ceiling")
    try:
        text = table.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise DesignIntegrityError("declared metadata table is not strict UTF-8") from error
    reader = csv.DictReader(
        io.StringIO(text, newline=""),
        delimiter="\t" if table.path.casefold().endswith(".tsv") else ",",
    )
    header = reader.fieldnames
    required = {
        contract.condition_column,
        *contract.replicate_columns,
        *contract.pairing_columns,
        *contract.aggregation_columns,
        *contract.required_adjustment_columns,
    }
    if (
        header is None
        or len(header) > MAX_TABLE_COLUMNS
        or len(set(header)) != len(header)
        or not required.issubset(header)
    ):
        raise DesignIntegrityError("declared metadata columns are unavailable or ambiguous")
    rows: list[dict[str, str]] = []
    row_count = 0
    for row_count, row in enumerate(reader, start=1):
        if row_count > MAX_TABLE_ROWS:
            raise DesignIntegrityError("declared metadata table exceeds the row ceiling")
        normalized = {
            key: str(value or "").strip() for key, value in row.items() if key is not None
        }
        level = normalized[contract.condition_column]
        if level in {contract.reference_level, contract.test_level}:
            rows.append(normalized)
    if row_count == 0:
        raise DesignIntegrityError("declared metadata table has no data rows")
    reference_rows = sum(row[contract.condition_column] == contract.reference_level for row in rows)
    test_rows = sum(row[contract.condition_column] == contract.test_level for row in rows)
    if reference_rows == 0 or test_rows == 0:
        raise DesignIntegrityError("both exact contrast levels must be present")

    missing_aggregation = sum(
        any(not row[column] for column in contract.aggregation_columns) for row in rows
    )
    aggregation_groups: dict[tuple[str, ...], set[str]] = {}
    for row in rows:
        key = tuple(row[column] for column in contract.aggregation_columns)
        if all(key):
            aggregation_groups.setdefault(key, set()).add(row[contract.condition_column])
    merged_groups = sum(len(levels) == 2 for levels in aggregation_groups.values())

    pair_columns = contract.pairing_columns or contract.replicate_columns
    if any(any(not row[column] for column in pair_columns) for row in rows):
        raise DesignIntegrityError(
            "pairing or replicate identity contains missing values; pair structure is unresolved"
        )
    pairing_levels: dict[tuple[str, ...], set[str]] = {}
    for row in rows:
        key = tuple(row[column] for column in pair_columns)
        pairing_levels.setdefault(key, set()).add(row[contract.condition_column])
    complete_pairs = sum(len(levels) == 2 for levels in pairing_levels.values())
    incomplete_pairs = sum(len(levels) == 1 for levels in pairing_levels.values())

    fitted = set(contract.fitted_fixed_effect_columns) | set(
        contract.fitted_random_intercept_columns
    )
    omitted = tuple(sorted(set(contract.required_adjustment_columns) - fitted))
    aliasing = _condition_in_adjustment_span(rows, contract)
    return _Metrics(
        row_count=row_count,
        contrast_rows=len(rows),
        reference_rows=reference_rows,
        test_rows=test_rows,
        missing_aggregation_rows=missing_aggregation,
        merged_aggregation_groups=merged_groups,
        complete_pairing_levels=complete_pairs,
        incomplete_pairing_levels=incomplete_pairs,
        pairing_omitted=contract.comparison_mode == "unpaired" and complete_pairs > 0,
        paired_comparison_unusable=contract.comparison_mode == "paired" and complete_pairs == 0,
        omitted_adjustments=omitted,
        condition_aliased_with_adjustments=aliasing,
    )


def _condition_in_adjustment_span(rows: list[dict[str, str]], contract: _Contract) -> bool:
    columns = contract.required_adjustment_columns
    if not columns:
        return False
    if any(any(not row[column] for column in columns) for row in rows):
        raise DesignIntegrityError(
            "required categorical adjustment values are missing; exact aliasing is unresolved"
        )
    design_columns: list[list[float]] = [[1.0] * len(rows)]
    for column in columns:
        levels = sorted({row[column] for row in rows})
        for level in levels[1:]:
            design_columns.append([float(row[column] == level) for row in rows])
    design = np.asarray(design_columns, dtype=float).T
    condition = np.asarray(
        [float(row[contract.condition_column] == contract.test_level) for row in rows],
        dtype=float,
    ).reshape((-1, 1))
    rank_without = int(np.linalg.matrix_rank(design))
    rank_with = int(np.linalg.matrix_rank(np.concatenate((design, condition), axis=1)))
    return rank_with == rank_without


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
