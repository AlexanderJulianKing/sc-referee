from __future__ import annotations

import csv
import io
import math
import re
import warnings
from dataclasses import dataclass
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path, PurePosixPath
from statistics import NormalDist
from typing import Any, Protocol

import h5py  # type: ignore[import-untyped]
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
from sc_referee.calculation_checks.delimited import bounded_table_text
from sc_referee.calculation_checks.material_context import MaterialCalculationContext
from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.delimited_io import classify_delimited_path

MAX_SENSITIVITY_TABLE_BYTES = 8 * 1024 * 1024
MAX_SENSITIVITY_TABLE_ROWS = 50_000
MAX_SENSITIVITY_TABLE_COLUMNS = 64
MAX_SENSITIVITY_MATRIX_ELEMENTS = 2_000_000
MAX_SENSITIVITY_MATRIX_BYTES = 16 * 1024 * 1024
MAX_SENSITIVITY_TEXT_BYTES = 2 * 1024 * 1024
SINGLE_CELL_SENSITIVITY_CHECK_ID = "calculation-check:single-cell-replicate-sensitivity-v1"

_BLOCK = re.compile(
    r"```sc-referee-single-cell-sensitivity-v1\s*\n(?P<body>.*?)\n```",
    re.IGNORECASE | re.DOTALL,
)
_REQUIRED_KEYS = {
    "reported_table",
    "count_matrix",
    "feature_id_column",
    "reported_adjusted_p_column",
    "reported_effect_column",
    "matrix_feature_index",
    "replicate_field",
    "condition_field",
    "reference_level",
    "test_level",
    "model",
    "alpha",
    "reference_effect",
    "target_power",
    "minimum_powered_fraction",
    "reported_unit",
    "producer_binding",
    "dependence_semantics",
}
_RECOGNITION_GRAMMAR_DIGEST = semantic_digest(
    {
        "block_pattern": _BLOCK.pattern,
        "required_keys": sorted(_REQUIRED_KEYS),
        "reported_unit": ["observation", "biological_replicate", "unresolved"],
        "producer_binding": ["exact", "unresolved"],
        "dependence_semantics": ["iid_rows", "dependence_aware", "unresolved"],
        "ceilings": {
            "table_bytes": MAX_SENSITIVITY_TABLE_BYTES,
            "table_rows": MAX_SENSITIVITY_TABLE_ROWS,
            "table_columns": MAX_SENSITIVITY_TABLE_COLUMNS,
            "matrix_elements": MAX_SENSITIVITY_MATRIX_ELEMENTS,
            "matrix_bytes": MAX_SENSITIVITY_MATRIX_BYTES,
            "text_bytes": MAX_SENSITIVITY_TEXT_BYTES,
        },
    }
)


class SingleCellSensitivityError(ValueError):
    """Raised when a sensitivity input escapes the closed adapter contract."""


@dataclass(frozen=True)
class SensitivityRecomputeInput:
    counts: np.ndarray[Any, np.dtype[np.integer[Any]]]
    feature_ids: tuple[str, ...]
    replicate_ids: tuple[str, ...]
    levels: tuple[str, ...]
    condition_name: str
    reference_level: str
    test_level: str
    model: str

    def __post_init__(self) -> None:
        if self.counts.ndim != 2 or self.counts.shape != (
            len(self.replicate_ids),
            len(self.feature_ids),
        ):
            raise SingleCellSensitivityError("recompute matrix axes are inconsistent")
        if self.counts.dtype.kind not in {"i", "u"} or bool(np.any(self.counts < 0)):
            raise SingleCellSensitivityError("recompute counts must be nonnegative integers")
        if len(set(self.feature_ids)) != len(self.feature_ids):
            raise SingleCellSensitivityError("recompute feature IDs must be unique")
        if len(set(self.replicate_ids)) != len(self.replicate_ids):
            raise SingleCellSensitivityError("recompute replicate IDs must be unique")
        if len(self.levels) != len(self.replicate_ids):
            raise SingleCellSensitivityError("recompute condition levels are inconsistent")


@dataclass(frozen=True)
class SensitivityRecomputeResult:
    feature_ids: tuple[str, ...]
    adjusted_p_values: tuple[float | None, ...]
    standard_errors: tuple[float | None, ...]
    n_reference: int
    n_test: int
    engine_id: str
    engine_version: str

    def __post_init__(self) -> None:
        if not (len(self.feature_ids) == len(self.adjusted_p_values) == len(self.standard_errors)):
            raise SingleCellSensitivityError("recompute result axes are inconsistent")
        if len(set(self.feature_ids)) != len(self.feature_ids):
            raise SingleCellSensitivityError("recompute result feature IDs must be unique")
        if self.n_reference < 1 or self.n_test < 1:
            raise SingleCellSensitivityError("recompute result requires both contrast levels")
        for value in self.adjusted_p_values:
            if value is not None and (not math.isfinite(value) or value < 0 or value > 1):
                raise SingleCellSensitivityError("adjusted p-values must be finite in [0, 1]")
        for value in self.standard_errors:
            if value is not None and (not math.isfinite(value) or value <= 0):
                raise SingleCellSensitivityError("standard errors must be finite and positive")


class SensitivityRecomputeEngine(Protocol):
    engine_id: str
    engine_version: str
    implementation_digest: str

    def recompute(self, request: SensitivityRecomputeInput) -> SensitivityRecomputeResult: ...


class PyDESeq2SensitivityEngine:
    engine_id = "sensitivity-engine:pydeseq2-nb-wald-v1"
    engine_version = "0.5-series"
    implementation_digest = semantic_digest(
        {
            "engine": engine_id,
            "algorithm": "PyDESeq2 one-factor negative-binomial Wald; one CPU",
            "nonzero_filter": "sum_gt_zero",
            "missing_outputs": "unavailable_not_significant",
        }
    )

    def recompute(self, request: SensitivityRecomputeInput) -> SensitivityRecomputeResult:
        try:
            pd = import_module("pandas")
            DeseqDataSet = import_module("pydeseq2.dds").DeseqDataSet
            DeseqStats = import_module("pydeseq2.ds").DeseqStats
        except (AttributeError, ImportError) as error:
            raise SingleCellSensitivityError(
                "optional single-cell recomputation dependencies are unavailable"
            ) from error
        sample_ids = [f"s{index}" for index in range(len(request.replicate_ids))]
        counts = pd.DataFrame(request.counts, index=sample_ids, columns=request.feature_ids)
        metadata = pd.DataFrame(
            {request.condition_name: request.levels},
            index=sample_ids,
        )
        nonzero = counts.sum(axis=0) > 0
        if int(nonzero.sum()) < 1:
            raise SingleCellSensitivityError("no nonzero features remain for recomputation")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dataset = DeseqDataSet(
                    counts=counts.loc[:, nonzero],
                    metadata=metadata,
                    design=request.model,
                    quiet=True,
                    n_cpus=1,
                )
                dataset.deseq2()
                statistics = DeseqStats(
                    dataset,
                    contrast=[
                        request.condition_name,
                        request.test_level,
                        request.reference_level,
                    ],
                    quiet=True,
                    n_cpus=1,
                )
                statistics.summary()
        except Exception as error:
            raise SingleCellSensitivityError(
                f"PyDESeq2 recomputation failed locally: {type(error).__name__}"
            ) from error
        results = statistics.results_df.reindex(request.feature_ids)
        adjusted = tuple(_optional_float(value) for value in results["padj"].tolist())
        standard_errors = tuple(
            _optional_positive_float(value) for value in results["lfcSE"].tolist()
        )
        try:
            installed_version = version("pydeseq2")
        except PackageNotFoundError:
            installed_version = self.engine_version
        return SensitivityRecomputeResult(
            feature_ids=request.feature_ids,
            adjusted_p_values=adjusted,
            standard_errors=standard_errors,
            n_reference=sum(level == request.reference_level for level in request.levels),
            n_test=sum(level == request.test_level for level in request.levels),
            engine_id=self.engine_id,
            engine_version=installed_version,
        )


@dataclass(frozen=True)
class _Contract:
    reported_table: str
    count_matrix: str
    feature_id_column: str
    reported_adjusted_p_column: str
    reported_effect_column: str
    matrix_feature_index: str
    replicate_field: str
    condition_field: str
    reference_level: str
    test_level: str
    model: str
    alpha: float
    reference_effect: float
    target_power: float
    minimum_powered_fraction: float
    reported_unit: str
    producer_binding: str
    dependence_semantics: str
    source_ref: dict[str, Any]


@dataclass(frozen=True)
class _ReportedFamily:
    adjusted_by_feature: dict[str, float]
    row_count: int


class DeclaredSingleCellSensitivityAdapter:
    def __init__(self, *, engine: SensitivityRecomputeEngine | None = None) -> None:
        self.engine = engine or PyDESeq2SensitivityEngine()
        self.manifest = CalculationAdapterManifest(
            adapter_id="calculation-adapter:declared-single-cell-sensitivity-v1",
            adapter_version="1.0.0",
            implementation_digest=semantic_digest(
                {
                    "adapter_source": sha256_digest(Path(__file__).read_bytes()),
                    "engine_id": self.engine.engine_id,
                    "engine_version": self.engine.engine_version,
                    "engine_implementation_digest": self.engine.implementation_digest,
                }
            ),
            recognition_grammar_digest=_RECOGNITION_GRAMMAR_DIGEST,
        )

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        try:
            report = context.selected_report.content.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise SingleCellSensitivityError("selected report is not strict UTF-8") from error
        matches = list(_BLOCK.finditer(report))
        if not matches:
            return None
        if len(matches) != 1:
            return self._unsupported(
                context,
                context.selected_report.source_ref,
                "unique_single_cell_sensitivity_contract",
                "The selected report contains more than one single-cell sensitivity contract.",
            )
        match = matches[0]
        block_source = _block_source(context.selected_report, report, match)
        try:
            contract = _parse_contract(match.group("body"), block_source)
        except SingleCellSensitivityError as error:
            return self._unsupported(
                context,
                block_source,
                "single_cell_sensitivity_contract_valid",
                str(error),
            )
        return self.inspect_normalized(context, contract)

    def inspect_normalized(
        self,
        context: CalculationContext,
        contract: _Contract,
    ) -> CalculationObservation:
        block_source = contract.source_ref
        if contract.reported_unit == "biological_replicate":
            return self._not_applicable(context, contract)
        if contract.reported_unit != "observation":
            return self._unsupported(
                context,
                block_source,
                "reported_unit_resolved",
                "The declared reported unit remains unresolved; no sensitivity comparison ran.",
            )
        if not isinstance(context, MaterialCalculationContext):
            return self._unsupported(
                context,
                block_source,
                "material_calculation_context_available",
                "The declared material inputs were not available in the frozen calculation view.",
            )
        table = _unique_material(context, contract.reported_table)
        matrix = _unique_material(context, contract.count_matrix)
        if table is None or matrix is None:
            return self._unsupported(
                context,
                block_source,
                "declared_material_inputs_bound",
                "Exactly one fully identified reported table and count matrix could not be bound.",
                inputs=tuple(item for item in (table, matrix) if item is not None),
            )
        try:
            family = _parse_reported_family(table, contract)
            recompute_input, matrix_sum = _parse_recompute_input(matrix, contract)
            result = self.engine.recompute(recompute_input)
            metrics = _sensitivity_metrics(family, result, contract)
        except (SingleCellSensitivityError, OSError, ValueError) as error:
            return self._unsupported(
                context,
                block_source,
                "single_cell_sensitivity_completed",
                str(error),
                inputs=(table, matrix),
            )
        source_refs = (block_source, table.source_ref, matrix.source_ref)
        limitations = [
            "This auditor-owned calculation is a declared replicate-level sensitivity analysis; "
            "it does not prove which code produced the reported table or which covariance model ran.",
            "No project-authored code was executed, and no scientific-error Finding is permitted "
            "from this calculation module.",
        ]
        if not metrics["recompute_powered"]:
            limitations.append(
                "The declared replicate-level recomputation is underpowered at the declared "
                "reference effect; disappearance of reported discoveries is not conclusive."
            )
        return CalculationObservation(
            applicability="applicable",
            comparison_outcome=(
                "conformant"
                if metrics["replicate_level_survivors"] == metrics["reported_significant_testable"]
                else "nonconformant"
            ),
            target_ref=context.selected_surface_ref,
            input_refs=(context.selected_artifact_ref, table.artifact_ref, matrix.artifact_ref),
            source_refs=source_refs,
            operands=(
                NamedOperand("reported_table_path", "string", table.path),
                NamedOperand("count_matrix_path", "string", matrix.path),
                NamedOperand("reported_family_rows", "integer", family.row_count),
                NamedOperand("matrix_observations", "integer", recompute_input.counts.shape[0]),
                NamedOperand("matrix_features", "integer", recompute_input.counts.shape[1]),
                NamedOperand("matrix_count_sum", "integer", matrix_sum),
                NamedOperand("alpha", "finite_number", contract.alpha),
                NamedOperand(
                    "reported_significant_testable",
                    "integer",
                    metrics["reported_significant_testable"],
                ),
                NamedOperand(
                    "replicate_level_survivors", "integer", metrics["replicate_level_survivors"]
                ),
                NamedOperand("survival_rate", "finite_number", metrics["survival_rate"]),
                NamedOperand("powered_fraction", "finite_number", metrics["powered_fraction"]),
                NamedOperand("recompute_powered", "boolean", metrics["recompute_powered"]),
                NamedOperand("reference_effect", "finite_number", contract.reference_effect),
                NamedOperand("target_power", "finite_number", contract.target_power),
                NamedOperand(
                    "minimum_powered_fraction", "finite_number", contract.minimum_powered_fraction
                ),
                NamedOperand("reference_replicates", "integer", result.n_reference),
                NamedOperand("test_replicates", "integer", result.n_test),
                NamedOperand("reported_unit", "string", contract.reported_unit),
                NamedOperand("producer_binding", "string", contract.producer_binding),
                NamedOperand("dependence_semantics", "string", contract.dependence_semantics),
                NamedOperand("recompute_engine_id", "string", result.engine_id),
                NamedOperand("recompute_engine_version", "string", result.engine_version),
            ),
            receipts=(
                ObservationReceipt(
                    "applicability",
                    "explicit_single_cell_sensitivity_contract",
                    "passed",
                    (block_source,),
                    "One closed sensitivity contract declared paths, columns, axes, contrast, model, unit, and power thresholds.",
                ),
                ObservationReceipt(
                    "completeness",
                    "fully_identified_material_inputs",
                    "passed",
                    (table.source_ref, matrix.source_ref),
                    "The exact declared table and H5AD bytes were available inside the material-input budget.",
                ),
                ObservationReceipt(
                    "completeness",
                    "complete_reported_family_parsed",
                    "passed",
                    (table.source_ref,),
                    f"The complete declared result table parsed within {MAX_SENSITIVITY_TABLE_ROWS} rows.",
                ),
                ObservationReceipt(
                    "completeness",
                    "bounded_replicate_matrix_parsed",
                    "passed",
                    (matrix.source_ref,),
                    "The dense nonnegative integer matrix, unique feature index, replicate IDs, and condition levels were fully parsed.",
                ),
                ObservationReceipt(
                    "counterevidence",
                    "underpowering_reported_separately",
                    "passed" if metrics["recompute_powered"] else "triggered",
                    source_refs,
                    "Power was evaluated independently of the observed survival rate and cannot be reversed into evidence of error.",
                ),
            ),
            lineage_status="complete",
            limitations=tuple(limitations),
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
                    "reported_unit_is_biological_replicate",
                    "not_applicable",
                    (contract.source_ref,),
                    "The contract declares that the reported family already uses the biological replicate as its test unit.",
                ),
            ),
            lineage_status="not_applicable",
            limitations=(
                "No observation-level versus replicate-level sensitivity comparison was applicable.",
            ),
        )

    def _unsupported(
        self,
        context: CalculationContext,
        report_source: dict[str, Any],
        predicate: str,
        detail: str,
        *,
        inputs: tuple[FrozenCalculationInput, ...] = (),
    ) -> CalculationObservation:
        return CalculationObservation(
            applicability="unsupported",
            comparison_outcome="unknown",
            target_ref=context.selected_surface_ref,
            input_refs=(context.selected_artifact_ref, *(item.artifact_ref for item in inputs)),
            source_refs=(report_source, *(item.source_ref for item in inputs)),
            operands=(),
            receipts=(
                ObservationReceipt(
                    "completeness",
                    predicate,
                    "unsupported",
                    (report_source, *(item.source_ref for item in inputs)),
                    detail,
                ),
            ),
            lineage_status="incomplete",
            limitations=(detail, "No numerical or scientific disagreement was inferred."),
        )


class SelectedSidecarSingleCellSensitivityAdapter:
    def __init__(self, *, engine: SensitivityRecomputeEngine | None = None) -> None:
        self._evaluator = DeclaredSingleCellSensitivityAdapter(engine=engine)
        self.manifest = sidecar_adapter_manifest(
            family="single-cell-replicate-sensitivity",
            implementation_digest=semantic_digest(
                {
                    "adapter_source": sha256_digest(Path(__file__).read_bytes()),
                    "engine_id": self._evaluator.engine.engine_id,
                    "engine_version": self._evaluator.engine.engine_version,
                    "engine_implementation_digest": (self._evaluator.engine.implementation_digest),
                }
            ),
        )

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        sidecar = selected_sidecar_contract(
            context,
            check_id=SINGLE_CELL_SENSITIVITY_CHECK_ID,
        )
        if sidecar is None:
            return None
        contract = _parse_contract_value(sidecar.value, sidecar.source_ref)
        return with_sidecar_lineage(
            self._evaluator.inspect_normalized(context, contract),
            sidecar,
        )


def single_cell_sensitivity_registry(
    *, adapter: DeclaredSingleCellSensitivityAdapter | None = None
) -> CalculationCheckRegistry:
    active_adapter = adapter or DeclaredSingleCellSensitivityAdapter()
    check = CalculationCheckManifest(
        check_id=SINGLE_CELL_SENSITIVITY_CHECK_ID,
        check_version="1.0.0",
        implementation_digest=sha256_digest(Path(__file__).read_bytes()),
        comparison_relation="reported_vs_declared_replicate_level_discovery_equivalence",
        output_ceiling="disclosure_only",
        permitted_wording=(
            "The explicitly declared reported discovery set changed under the bounded, "
            "replicate-level sensitivity calculation; power and producer limitations are separate."
        ),
    )
    return CalculationCheckRegistry(
        (CalculationCheckModule(check, (active_adapter,)),),
        profile_id="deterministic_single_cell_sensitivity_v1",
    )


def _parse_contract(body: str, source_ref: dict[str, Any]) -> _Contract:
    try:
        value = yaml.safe_load(body)
    except yaml.YAMLError as error:
        raise SingleCellSensitivityError(
            "sensitivity contract is not valid bounded YAML"
        ) from error
    if not isinstance(value, dict):
        raise SingleCellSensitivityError("sensitivity contract must be a mapping")
    return _parse_contract_value(value, source_ref)


def _parse_contract_value(value: dict[str, Any], source_ref: dict[str, Any]) -> _Contract:
    if set(value) != _REQUIRED_KEYS:
        raise SingleCellSensitivityError(
            "sensitivity contract keys are missing, extra, or duplicated"
        )
    texts = {
        key: value[key]
        for key in _REQUIRED_KEYS
        if key not in {"alpha", "reference_effect", "target_power", "minimum_powered_fraction"}
    }
    if any(not isinstance(item, str) or not item.strip() for item in texts.values()):
        raise SingleCellSensitivityError(
            "sensitivity contract text values must be nonempty strings"
        )
    for key in ("reported_table", "count_matrix"):
        path = PurePosixPath(str(value[key]))
        if path.is_absolute() or ".." in path.parts:
            raise SingleCellSensitivityError("sensitivity input paths must be bounded and relative")
    if classify_delimited_path(str(value["reported_table"])) is None:
        raise SingleCellSensitivityError("reported sensitivity table must be CSV or TSV")
    if PurePosixPath(str(value["count_matrix"])).suffix.casefold() != ".h5ad":
        raise SingleCellSensitivityError("sensitivity count matrix must be H5AD")
    if not str(value["matrix_feature_index"]).startswith("var/"):
        raise SingleCellSensitivityError("matrix feature index must name one var field")
    if not str(value["replicate_field"]).startswith("obs/") or not str(
        value["condition_field"]
    ).startswith("obs/"):
        raise SingleCellSensitivityError("replicate and condition fields must name obs fields")
    condition_name = str(value["condition_field"]).removeprefix("obs/")
    if str(value["model"]).strip() != f"~ {condition_name}":
        raise SingleCellSensitivityError(
            "initial sensitivity model must be the declared one-factor condition model"
        )
    if value["reported_unit"] not in {"observation", "biological_replicate", "unresolved"}:
        raise SingleCellSensitivityError("reported_unit is outside the closed vocabulary")
    if value["producer_binding"] not in {"exact", "unresolved"}:
        raise SingleCellSensitivityError("producer_binding is outside the closed vocabulary")
    if value["dependence_semantics"] not in {"iid_rows", "dependence_aware", "unresolved"}:
        raise SingleCellSensitivityError("dependence_semantics is outside the closed vocabulary")
    alpha = _bounded_number(value["alpha"], "alpha", lower=0, upper=1)
    reference_effect = _bounded_number(
        value["reference_effect"], "reference_effect", lower=0, upper=None
    )
    target_power = _bounded_number(value["target_power"], "target_power", lower=0, upper=1)
    minimum_powered_fraction = _bounded_number(
        value["minimum_powered_fraction"], "minimum_powered_fraction", lower=0, upper=1
    )
    if value["reference_level"] == value["test_level"]:
        raise SingleCellSensitivityError("reference and test levels must differ")
    return _Contract(
        **{key: str(value[key]).strip() for key in texts},
        alpha=alpha,
        reference_effect=reference_effect,
        target_power=target_power,
        minimum_powered_fraction=minimum_powered_fraction,
        source_ref=source_ref,
    )


def _parse_reported_family(table: FrozenCalculationInput, contract: _Contract) -> _ReportedFamily:
    text, delimiter = bounded_table_text(
        table,
        byte_ceiling=MAX_SENSITIVITY_TABLE_BYTES,
        error_type=SingleCellSensitivityError,
        label="declared reported table",
    )
    reader = csv.DictReader(
        io.StringIO(text, newline=""),
        delimiter=delimiter,
    )
    header = reader.fieldnames
    required = {
        contract.feature_id_column,
        contract.reported_adjusted_p_column,
        contract.reported_effect_column,
    }
    if (
        header is None
        or len(header) > MAX_SENSITIVITY_TABLE_COLUMNS
        or len(set(header)) != len(header)
        or not required.issubset(header)
    ):
        raise SingleCellSensitivityError(
            "declared reported table columns are unavailable or ambiguous"
        )
    adjusted: dict[str, float] = {}
    for index, row in enumerate(reader, start=1):
        if index > MAX_SENSITIVITY_TABLE_ROWS:
            raise SingleCellSensitivityError("declared reported table exceeds the row ceiling")
        feature = str(row.get(contract.feature_id_column, "")).strip()
        if not feature or feature in adjusted:
            raise SingleCellSensitivityError("reported feature identifiers are empty or duplicated")
        adjusted[feature] = _probability(
            row.get(contract.reported_adjusted_p_column), "reported adjusted p-value"
        )
        _finite_number(row.get(contract.reported_effect_column), "reported effect")
    if not adjusted:
        raise SingleCellSensitivityError("declared reported table has no data rows")
    return _ReportedFamily(adjusted, len(adjusted))


def _parse_recompute_input(
    material: FrozenCalculationInput, contract: _Contract
) -> tuple[SensitivityRecomputeInput, int]:
    try:
        handle = h5py.File(io.BytesIO(material.content), "r")
    except (OSError, ValueError) as error:
        raise SingleCellSensitivityError("declared count matrix is not readable HDF5") from error
    with handle:
        if _attr_text(handle.attrs.get("encoding-type")) != "anndata":
            raise SingleCellSensitivityError("declared count matrix is not encoded as AnnData")
        matrix = handle.get("X")
        if not isinstance(matrix, h5py.Dataset) or len(matrix.shape) != 2:
            raise SingleCellSensitivityError("H5AD X is not one dense two-dimensional dataset")
        n_obs, n_vars = int(matrix.shape[0]), int(matrix.shape[1])
        if (
            n_obs < 1
            or n_vars < 1
            or n_obs * n_vars > MAX_SENSITIVITY_MATRIX_ELEMENTS
            or int(matrix.nbytes) > MAX_SENSITIVITY_MATRIX_BYTES
            or matrix.dtype.kind not in {"i", "u"}
            or matrix.is_virtual
        ):
            raise SingleCellSensitivityError("H5AD X exceeds the supported dense integer profile")
        counts = np.asarray(matrix[...])
        if bool(np.any(counts < 0)):
            raise SingleCellSensitivityError("H5AD X contains negative values")
        feature_ids = _axis_values(handle, contract.matrix_feature_index, n_vars)
        replicate_ids = _axis_values(handle, contract.replicate_field, n_obs)
        levels = _axis_values(handle, contract.condition_field, n_obs)
    if len(set(feature_ids)) != len(feature_ids):
        raise SingleCellSensitivityError("H5AD feature index is not unique")
    if len(set(replicate_ids)) != len(replicate_ids):
        raise SingleCellSensitivityError(
            "initial sensitivity input requires one already-aggregated row per replicate"
        )
    allowed_levels = {contract.reference_level, contract.test_level}
    if set(levels) != allowed_levels:
        raise SingleCellSensitivityError(
            "H5AD condition field does not contain exactly the declared levels"
        )
    if min(levels.count(contract.reference_level), levels.count(contract.test_level)) < 3:
        raise SingleCellSensitivityError(
            "fewer than three declared biological replicates occur in one contrast level"
        )
    request = SensitivityRecomputeInput(
        counts=counts,
        feature_ids=feature_ids,
        replicate_ids=replicate_ids,
        levels=levels,
        condition_name=contract.condition_field.removeprefix("obs/"),
        reference_level=contract.reference_level,
        test_level=contract.test_level,
        model=contract.model,
    )
    return request, int(counts.sum(dtype=object))


def _axis_values(handle: h5py.File, path: str, expected_length: int) -> tuple[str, ...]:
    value = handle.get(path)
    if isinstance(value, h5py.Dataset):
        if len(value.shape) != 1 or int(value.shape[0]) != expected_length:
            raise SingleCellSensitivityError(f"H5AD field {path!r} has an inconsistent axis")
        try:
            values = tuple(
                str(item) for item in value.asstr(encoding="utf-8", errors="strict")[...]
            )
        except (OSError, TypeError, UnicodeError) as error:
            raise SingleCellSensitivityError(f"H5AD field {path!r} is not strict UTF-8") from error
    elif (
        isinstance(value, h5py.Group)
        and _attr_text(value.attrs.get("encoding-type")) == "categorical"
    ):
        categories = value.get("categories")
        codes = value.get("codes")
        if not isinstance(categories, h5py.Dataset) or not isinstance(codes, h5py.Dataset):
            raise SingleCellSensitivityError(f"H5AD categorical field {path!r} is incomplete")
        try:
            category_values = tuple(
                str(item) for item in categories.asstr(encoding="utf-8", errors="strict")[...]
            )
        except (OSError, TypeError, UnicodeError) as error:
            raise SingleCellSensitivityError(f"H5AD field {path!r} is not strict UTF-8") from error
        code_values = np.asarray(codes[...])
        if len(code_values.shape) != 1 or int(code_values.shape[0]) != expected_length:
            raise SingleCellSensitivityError(
                f"H5AD categorical field {path!r} has inconsistent codes"
            )
        if code_values.size and (
            int(code_values.min()) < 0 or int(code_values.max()) >= len(category_values)
        ):
            raise SingleCellSensitivityError(f"H5AD categorical field {path!r} has invalid codes")
        values = tuple(category_values[int(code)] for code in code_values)
    else:
        raise SingleCellSensitivityError(f"H5AD field {path!r} is unavailable or unsupported")
    if any(not item for item in values):
        raise SingleCellSensitivityError(f"H5AD field {path!r} contains an empty value")
    if sum(len(item.encode("utf-8")) for item in values) > MAX_SENSITIVITY_TEXT_BYTES:
        raise SingleCellSensitivityError(f"H5AD field {path!r} exceeds the text ceiling")
    return values


def _sensitivity_metrics(
    family: _ReportedFamily,
    result: SensitivityRecomputeResult,
    contract: _Contract,
) -> dict[str, int | float | bool]:
    result_index = {feature: index for index, feature in enumerate(result.feature_ids)}
    valid: list[int] = []
    for feature, reported_adjusted in family.adjusted_by_feature.items():
        index = result_index.get(feature)
        if index is None or reported_adjusted > contract.alpha:
            continue
        adjusted = result.adjusted_p_values[index]
        standard_error = result.standard_errors[index]
        if adjusted is not None and standard_error is not None:
            valid.append(index)
    if not valid:
        raise SingleCellSensitivityError(
            "no reported significant features were matched and testable"
        )
    survivors = 0
    for index in valid:
        adjusted = result.adjusted_p_values[index]
        assert adjusted is not None
        survivors += int(adjusted <= contract.alpha)
    critical_value = NormalDist().inv_cdf(1 - contract.alpha / 2) + NormalDist().inv_cdf(
        contract.target_power
    )
    detectable = 0
    for index in valid:
        standard_error = result.standard_errors[index]
        assert standard_error is not None
        detectable += int(standard_error * critical_value <= contract.reference_effect)
    powered_fraction = detectable / len(valid)
    return {
        "reported_significant_testable": len(valid),
        "replicate_level_survivors": survivors,
        "survival_rate": survivors / len(valid),
        "powered_fraction": powered_fraction,
        "recompute_powered": powered_fraction >= contract.minimum_powered_fraction,
    }


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


def _bounded_number(value: Any, name: str, *, lower: float, upper: float | None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SingleCellSensitivityError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number) or number <= lower or (upper is not None and number >= upper):
        raise SingleCellSensitivityError(f"{name} is outside its open finite interval")
    return number


def _finite_number(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise SingleCellSensitivityError(f"{name} is not numeric") from error
    if not math.isfinite(number):
        raise SingleCellSensitivityError(f"{name} is not finite")
    return number


def _probability(value: Any, name: str) -> float:
    number = _finite_number(value, name)
    if number < 0 or number > 1:
        raise SingleCellSensitivityError(f"{name} is outside [0, 1]")
    return number


def _optional_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and 0 <= number <= 1 else None


def _optional_positive_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def _attr_text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="strict")
    return value if isinstance(value, str) else ""
