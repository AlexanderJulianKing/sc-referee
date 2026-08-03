from __future__ import annotations

import csv
import io
import math
import re
from dataclasses import dataclass
from pathlib import Path
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
from sc_referee.calculation_checks.delimited import bounded_table_text
from sc_referee.calculation_checks.material_context import MaterialCalculationContext
from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.delimited_io import classify_delimited_path

MAX_TABLE_BYTES = 8 * 1024 * 1024
MAX_TABLE_ROWS = 250_000
MAX_TABLE_COLUMNS = 64
MIN_BACKGROUND_PAIRS = 50
HIC_LOOP_CHECK_ID = "calculation-check:hic-loop-strength-v1"

_BLOCK = re.compile(
    r"```sc-referee-hic-loop-strength-v1\s*\n(?P<body>.*?)\n```",
    re.IGNORECASE | re.DOTALL,
)
_REQUIRED_KEYS = {
    "contacts_table",
    "bins_table",
    "results_table",
    "replicate_columns",
    "condition_column",
    "reference_level",
    "test_level",
    "genome_assembly",
    "resolution_bp",
    "target_bin_i",
    "target_bin_j",
    "background_view_start",
    "background_view_end",
    "expected_model",
    "mask_policy",
    "zero_policy",
    "pseudocount",
    "target_statistic",
    "replicate_functional",
    "reported_delta_tolerance",
    "tolerance_authority",
    "claim_semantics",
    "producer_binding",
}
_SUPPORTED = {
    "expected_model": "cis_exact_distance_arithmetic_mean_target_excluded_v1",
    "mask_policy": "exclude_if_either_bin_masked_v1",
    "zero_policy": "dense_including_zeros",
    "target_statistic": "single_pixel",
    "replicate_functional": "equal_weight_mean_log2_oe_v1",
    "tolerance_authority": "rounding_absolute_log2_ratio_delta",
}
_RECOGNITION_GRAMMAR_DIGEST = semantic_digest(
    {
        "block_pattern": _BLOCK.pattern,
        "required_keys": sorted(_REQUIRED_KEYS),
        "supported_profile": _SUPPORTED,
        "minimum_background_pairs": MIN_BACKGROUND_PAIRS,
        "claim_semantics": ["loop_strength_delta", "descriptive_contact_map", "unresolved"],
        "producer_binding": ["exact", "unresolved"],
        "ceilings": {
            "table_bytes": MAX_TABLE_BYTES,
            "table_rows": MAX_TABLE_ROWS,
            "table_columns": MAX_TABLE_COLUMNS,
        },
    }
)


class HiCLoopStrengthError(ValueError):
    """Raised when a Hi-C loop-strength input escapes the closed contract."""


@dataclass(frozen=True)
class _Contract:
    contacts_table: str
    bins_table: str
    results_table: str
    replicate_columns: tuple[str, ...]
    condition_column: str
    reference_level: str
    test_level: str
    genome_assembly: str
    resolution_bp: int
    target_bin_i: str
    target_bin_j: str
    background_view_start: int
    background_view_end: int
    expected_model: str
    mask_policy: str
    zero_policy: str
    pseudocount: float
    target_statistic: str
    replicate_functional: str
    reported_delta_tolerance: float
    tolerance_authority: str
    claim_semantics: str
    producer_binding: str
    source_ref: dict[str, Any]


@dataclass(frozen=True)
class _Recompute:
    reported_delta: float
    recomputed_delta: float
    absolute_error: float
    within_tolerance: bool
    distance_bp: int
    background_pairs: int
    sample_labels: tuple[str, ...]
    sample_conditions: tuple[str, ...]
    sample_strengths: tuple[float, ...]
    reference_replicates: int
    test_replicates: int
    reference_mean: float
    test_mean: float


class DeclaredHiCLoopStrengthAdapter:
    def __init__(self) -> None:
        self.manifest = CalculationAdapterManifest(
            adapter_id="calculation-adapter:declared-hic-loop-strength-v1",
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
            raise HiCLoopStrengthError("selected report is not strict UTF-8") from error
        matches = list(_BLOCK.finditer(report))
        if not matches:
            return None
        if len(matches) != 1:
            return self._unsupported(
                context,
                context.selected_report.source_ref,
                "unique_hic_loop_contract",
                "The selected report contains more than one Hi-C loop-strength contract.",
            )
        match = matches[0]
        source_ref = _block_source(context.selected_report, report, match)
        try:
            contract = _parse_contract(match.group("body"), source_ref)
        except HiCLoopStrengthError as error:
            return self._unsupported(context, source_ref, "hic_loop_contract_valid", str(error))
        return self.inspect_normalized(context, contract)

    def inspect_normalized(
        self,
        context: CalculationContext,
        contract: _Contract,
    ) -> CalculationObservation:
        source_ref = contract.source_ref
        if contract.claim_semantics == "descriptive_contact_map":
            return self._not_applicable(context, contract)
        if contract.claim_semantics == "unresolved" or contract.producer_binding == "unresolved":
            return self._unsupported(
                context,
                source_ref,
                "hic_claim_and_producer_resolved",
                "The loop-strength claim or exact report-producer binding remains unresolved.",
            )
        if not isinstance(context, MaterialCalculationContext):
            return self._unsupported(
                context,
                source_ref,
                "material_calculation_context_available",
                "The explicitly selected Hi-C tables were not available in the frozen material-input view.",
            )
        selected = tuple(
            _unique_material(context, path)
            for path in (contract.contacts_table, contract.bins_table, contract.results_table)
        )
        if any(item is None for item in selected):
            return self._unsupported(
                context,
                source_ref,
                "declared_hic_tables_bound",
                "Exactly one fully identified contacts, bins, and result table could not be bound.",
                inputs=tuple(item for item in selected if item is not None),
            )
        contacts, bins, results = selected
        assert contacts is not None and bins is not None and results is not None
        try:
            recompute = _recompute(contacts, bins, results, contract)
        except HiCLoopStrengthError as error:
            return self._unsupported(
                context,
                source_ref,
                "complete_hic_loop_recompute",
                str(error),
                inputs=(contacts, bins, results),
            )
        sources = (source_ref, contacts.source_ref, bins.source_ref, results.source_ref)
        return CalculationObservation(
            applicability="applicable",
            comparison_outcome="conformant" if recompute.within_tolerance else "nonconformant",
            target_ref=context.selected_surface_ref,
            input_refs=(
                context.selected_artifact_ref,
                contacts.artifact_ref,
                bins.artifact_ref,
                results.artifact_ref,
            ),
            source_refs=sources,
            operands=(
                NamedOperand("contacts_table_path", "string", contacts.path),
                NamedOperand("bins_table_path", "string", bins.path),
                NamedOperand("results_table_path", "string", results.path),
                NamedOperand("target_bin_i", "string", contract.target_bin_i),
                NamedOperand("target_bin_j", "string", contract.target_bin_j),
                NamedOperand("distance_bp", "integer", recompute.distance_bp),
                NamedOperand("background_pairs", "integer", recompute.background_pairs),
                NamedOperand("reported_delta", "finite_number", recompute.reported_delta),
                NamedOperand("recomputed_delta", "finite_number", recompute.recomputed_delta),
                NamedOperand("absolute_error", "finite_number", recompute.absolute_error),
                NamedOperand(
                    "reported_delta_tolerance",
                    "finite_number",
                    contract.reported_delta_tolerance,
                ),
                NamedOperand("within_tolerance", "boolean", recompute.within_tolerance),
                NamedOperand("sample_labels", "string_array", list(recompute.sample_labels)),
                NamedOperand(
                    "sample_conditions", "string_array", list(recompute.sample_conditions)
                ),
                NamedOperand(
                    "sample_log2_observed_expected",
                    "finite_number_array",
                    list(recompute.sample_strengths),
                ),
                NamedOperand("reference_replicates", "integer", recompute.reference_replicates),
                NamedOperand("test_replicates", "integer", recompute.test_replicates),
                NamedOperand("reference_mean_log2_oe", "finite_number", recompute.reference_mean),
                NamedOperand("test_mean_log2_oe", "finite_number", recompute.test_mean),
            ),
            receipts=(
                ObservationReceipt(
                    "applicability",
                    "explicit_hic_loop_strength_contract",
                    "passed",
                    (source_ref,),
                    "One closed declaration binds the exact target, resolution, background, masking, zero, replicate, tolerance, and report semantics.",
                ),
                ObservationReceipt(
                    "completeness",
                    "complete_dense_distance_strata",
                    "passed",
                    (contacts.source_ref, bins.source_ref),
                    "Every retained replicate contained one unique target and all zero-inclusive same-distance pairs in the complete bin grid.",
                ),
                ObservationReceipt(
                    "completeness",
                    "unique_reported_target_delta",
                    "passed",
                    (results.source_ref,),
                    "Exactly one finite reported delta matched the declared assembly, resolution, target, and contrast.",
                ),
                ObservationReceipt(
                    "counterevidence",
                    "alternate_hic_estimators_or_masks",
                    "passed",
                    (source_ref,),
                    "Any alternate estimator, mask, zero, pseudocount, target, replicate, or tolerance contract would have forced abstention.",
                ),
            ),
            lineage_status="complete",
            limitations=(
                "This recomputation covers one cis, single-pixel, exact-distance arithmetic-background estimator only; balanced contacts, other expected models, matrices, domains, stripes, covariates, and adjusted or paired designs abstain.",
                "Numerical disagreement does not identify its causal step, prove project execution, or establish biological truth.",
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
                    "claim_is_descriptive_contact_map",
                    "not_applicable",
                    (contract.source_ref,),
                    "The report does not declare a quantitative loop-strength delta.",
                ),
            ),
            lineage_status="not_applicable",
            limitations=("No loop-strength delta comparison applies to a descriptive map.",),
        )

    def _unsupported(
        self,
        context: CalculationContext,
        source_ref: dict[str, Any],
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
            source_refs=(source_ref, *(item.source_ref for item in inputs)),
            operands=(),
            receipts=(
                ObservationReceipt(
                    "completeness",
                    predicate,
                    "unsupported",
                    (source_ref, *(item.source_ref for item in inputs)),
                    detail,
                ),
            ),
            lineage_status="incomplete",
            limitations=(detail, "No Hi-C loop-strength disagreement was inferred."),
        )


class SelectedSidecarHiCLoopStrengthAdapter:
    def __init__(self) -> None:
        self.manifest = sidecar_adapter_manifest(
            family="hic-loop-strength",
            implementation_digest=sha256_digest(Path(__file__).read_bytes()),
        )
        self._evaluator = DeclaredHiCLoopStrengthAdapter()

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        sidecar = selected_sidecar_contract(context, check_id=HIC_LOOP_CHECK_ID)
        if sidecar is None:
            return None
        contract = _parse_contract_value(sidecar.value, sidecar.source_ref)
        return with_sidecar_lineage(
            self._evaluator.inspect_normalized(context, contract),
            sidecar,
        )


def hic_loop_strength_registry() -> CalculationCheckRegistry:
    adapter = DeclaredHiCLoopStrengthAdapter()
    check = CalculationCheckManifest(
        check_id=HIC_LOOP_CHECK_ID,
        check_version="1.0.0",
        implementation_digest=sha256_digest(Path(__file__).read_bytes()),
        comparison_relation="declared_hic_loop_strength_delta_conformance",
        output_ceiling="disclosure_only",
        permitted_wording=(
            "The uniquely bound reported Hi-C loop-strength delta differs from the independent exact-distance arithmetic-background recomputation beyond the declared tolerance."
        ),
    )
    return CalculationCheckRegistry(
        (CalculationCheckModule(check, (adapter,)),),
        profile_id="deterministic_hic_loop_strength_v1",
    )


def _parse_contract(body: str, source_ref: dict[str, Any]) -> _Contract:
    try:
        value = yaml.safe_load(body)
    except yaml.YAMLError as error:
        raise HiCLoopStrengthError("Hi-C contract is not valid YAML") from error
    if not isinstance(value, dict):
        raise HiCLoopStrengthError("Hi-C contract must be a mapping")
    return _parse_contract_value(value, source_ref)


def _parse_contract_value(value: dict[str, Any], source_ref: dict[str, Any]) -> _Contract:
    if set(value) != _REQUIRED_KEYS:
        raise HiCLoopStrengthError("Hi-C contract keys are missing or extra")
    text_keys = _REQUIRED_KEYS - {
        "replicate_columns",
        "resolution_bp",
        "background_view_start",
        "background_view_end",
        "pseudocount",
        "reported_delta_tolerance",
    }
    if any(not isinstance(value[key], str) or not value[key].strip() for key in text_keys):
        raise HiCLoopStrengthError("Hi-C text values must be nonempty strings")
    for key in ("contacts_table", "bins_table", "results_table"):
        path = str(value[key])
        if path.startswith("/") or ".." in path.split("/") or classify_delimited_path(path) is None:
            raise HiCLoopStrengthError("Hi-C input paths must be bounded CSV or TSV paths")
    replicates = value["replicate_columns"]
    if (
        not isinstance(replicates, list)
        or not replicates
        or len(replicates) > 8
        or any(not isinstance(item, str) or not item.strip() for item in replicates)
        or len(set(replicates)) != len(replicates)
    ):
        raise HiCLoopStrengthError("replicate columns must be one bounded unique string list")
    integers: dict[str, int] = {}
    for key in ("resolution_bp", "background_view_start", "background_view_end"):
        item = value[key]
        if isinstance(item, bool) or not isinstance(item, int):
            raise HiCLoopStrengthError(f"{key} must be an integer")
        integers[key] = item
    if (
        integers["resolution_bp"] <= 0
        or integers["background_view_start"] < 0
        or integers["background_view_end"] <= integers["background_view_start"]
        or (integers["background_view_end"] - integers["background_view_start"])
        % integers["resolution_bp"]
    ):
        raise HiCLoopStrengthError("resolution and background view are inconsistent")
    if value["target_bin_i"] == value["target_bin_j"]:
        raise HiCLoopStrengthError("target bins must differ")
    for key, supported in _SUPPORTED.items():
        if value[key] != supported:
            raise HiCLoopStrengthError(f"{key} is outside the closed supported profile")
    pseudocount = _finite(value["pseudocount"], "pseudocount")
    tolerance = _finite(value["reported_delta_tolerance"], "reported delta tolerance")
    if pseudocount != 0 or tolerance < 0:
        raise HiCLoopStrengthError("pseudocount or tolerance is outside the supported range")
    if value["claim_semantics"] not in {
        "loop_strength_delta",
        "descriptive_contact_map",
        "unresolved",
    }:
        raise HiCLoopStrengthError("claim semantics are outside the closed vocabulary")
    if value["producer_binding"] not in {"exact", "unresolved"}:
        raise HiCLoopStrengthError("producer binding is outside the closed vocabulary")
    return _Contract(
        contacts_table=str(value["contacts_table"]).strip(),
        bins_table=str(value["bins_table"]).strip(),
        results_table=str(value["results_table"]).strip(),
        replicate_columns=tuple(item.strip() for item in replicates),
        condition_column=str(value["condition_column"]).strip(),
        reference_level=str(value["reference_level"]).strip(),
        test_level=str(value["test_level"]).strip(),
        genome_assembly=str(value["genome_assembly"]).strip(),
        resolution_bp=integers["resolution_bp"],
        target_bin_i=str(value["target_bin_i"]).strip(),
        target_bin_j=str(value["target_bin_j"]).strip(),
        background_view_start=integers["background_view_start"],
        background_view_end=integers["background_view_end"],
        expected_model=str(value["expected_model"]).strip(),
        mask_policy=str(value["mask_policy"]).strip(),
        zero_policy=str(value["zero_policy"]).strip(),
        pseudocount=pseudocount,
        target_statistic=str(value["target_statistic"]).strip(),
        replicate_functional=str(value["replicate_functional"]).strip(),
        reported_delta_tolerance=tolerance,
        tolerance_authority=str(value["tolerance_authority"]).strip(),
        claim_semantics=str(value["claim_semantics"]).strip(),
        producer_binding=str(value["producer_binding"]).strip(),
        source_ref=source_ref,
    )


def _recompute(
    contacts_table: FrozenCalculationInput,
    bins_table: FrozenCalculationInput,
    results_table: FrozenCalculationInput,
    contract: _Contract,
) -> _Recompute:
    bins = _rows(bins_table, {"bin_id", "chrom", "start", "masked"})
    by_id: dict[str, tuple[str, int, bool]] = {}
    starts: dict[int, str] = {}
    for row in bins:
        bin_id = row["bin_id"]
        start = _integer(row["start"], "bin start")
        masked = _boolean(row["masked"], "masked")
        if not bin_id or bin_id in by_id or start in starts:
            raise HiCLoopStrengthError("bin IDs or starts are empty or duplicated")
        by_id[bin_id] = (row["chrom"], start, masked)
        starts[start] = bin_id
    if contract.target_bin_i not in by_id or contract.target_bin_j not in by_id:
        raise HiCLoopStrengthError("target bins are unavailable")
    left = by_id[contract.target_bin_i]
    right = by_id[contract.target_bin_j]
    if left[0] != right[0] or left[2] or right[2]:
        raise HiCLoopStrengthError("target is trans or masked")
    distance = abs(left[1] - right[1])
    if distance <= 0 or distance % contract.resolution_bp:
        raise HiCLoopStrengthError("target distance is off the resolution grid")
    expected_starts = list(
        range(
            contract.background_view_start,
            contract.background_view_end,
            contract.resolution_bp,
        )
    )
    if sorted(starts) != expected_starts:
        raise HiCLoopStrengthError("background bins are not one complete exact view grid")
    all_pairs = [
        _pair(starts[start], starts[start + distance])
        for start in expected_starts
        if start + distance in starts
    ]
    target = _pair(contract.target_bin_i, contract.target_bin_j)
    if target not in all_pairs:
        raise HiCLoopStrengthError("target is outside the exact-distance view")
    background = [
        pair
        for pair in all_pairs
        if pair != target and not by_id[pair[0]][2] and not by_id[pair[1]][2]
    ]
    if len(background) < MIN_BACKGROUND_PAIRS:
        raise HiCLoopStrengthError("fewer than fifty eligible background pairs remain")

    required_contacts = {
        *contract.replicate_columns,
        contract.condition_column,
        "bin_i",
        "bin_j",
        "observed_count",
    }
    contacts = _rows(contacts_table, required_contacts)
    samples: dict[tuple[str, ...], dict[tuple[str, str], int]] = {}
    sample_conditions: dict[tuple[str, ...], str] = {}
    for row in contacts:
        condition = row[contract.condition_column]
        if condition not in {contract.reference_level, contract.test_level}:
            continue
        key = tuple(row[column] for column in contract.replicate_columns)
        if any(not item for item in key):
            raise HiCLoopStrengthError("replicate identity contains an empty value")
        pair = _pair(row["bin_i"], row["bin_j"])
        count = _integer(row["observed_count"], "observed count")
        if count < 0 or pair[0] not in by_id or pair[1] not in by_id:
            raise HiCLoopStrengthError("contact count or bin reference is invalid")
        if key in sample_conditions and sample_conditions[key] != condition:
            raise HiCLoopStrengthError("one replicate identity maps to both conditions")
        sample_conditions[key] = condition
        bucket = samples.setdefault(key, {})
        if pair in bucket:
            raise HiCLoopStrengthError("one sample contains a duplicate unordered pixel")
        bucket[pair] = count
    strengths: list[tuple[tuple[str, ...], str, float]] = []
    required_pairs = set(all_pairs)
    for key, counts in sorted(samples.items()):
        if not required_pairs.issubset(counts):
            raise HiCLoopStrengthError("a replicate lacks a dense zero-inclusive distance stratum")
        observed = counts[target]
        expected = sum(counts[pair] for pair in background) / len(background)
        if observed <= 0 or expected <= 0:
            raise HiCLoopStrengthError(
                "target observed or background expected count is not positive"
            )
        strengths.append((key, sample_conditions[key], math.log2(observed / expected)))
    reference_values = [
        value for _, condition, value in strengths if condition == contract.reference_level
    ]
    test_values = [value for _, condition, value in strengths if condition == contract.test_level]
    if not reference_values or not test_values:
        raise HiCLoopStrengthError("one or both contrast levels have no replicates")
    reference_mean = sum(reference_values) / len(reference_values)
    test_mean = sum(test_values) / len(test_values)
    recomputed = test_mean - reference_mean
    reported = _reported_delta(results_table, contract)
    absolute_error = abs(reported - recomputed)
    numerical = 1e-9 * max(1.0, abs(reported), abs(recomputed))
    return _Recompute(
        reported_delta=reported,
        recomputed_delta=recomputed,
        absolute_error=absolute_error,
        within_tolerance=absolute_error <= contract.reported_delta_tolerance + numerical,
        distance_bp=distance,
        background_pairs=len(background),
        sample_labels=tuple("|".join(key) for key, _, _ in strengths),
        sample_conditions=tuple(condition for _, condition, _ in strengths),
        sample_strengths=tuple(value for _, _, value in strengths),
        reference_replicates=len(reference_values),
        test_replicates=len(test_values),
        reference_mean=reference_mean,
        test_mean=test_mean,
    )


def _reported_delta(table: FrozenCalculationInput, contract: _Contract) -> float:
    required = {
        "genome_assembly",
        "resolution_bp",
        "bin_i",
        "bin_j",
        "reference",
        "test",
        "delta",
    }
    rows = _rows(table, required)
    target = _pair(contract.target_bin_i, contract.target_bin_j)
    matches = [
        row
        for row in rows
        if row["genome_assembly"] == contract.genome_assembly
        and _integer(row["resolution_bp"], "reported resolution") == contract.resolution_bp
        and _pair(row["bin_i"], row["bin_j"]) == target
        and row["reference"] == contract.reference_level
        and row["test"] == contract.test_level
    ]
    if len(matches) != 1:
        raise HiCLoopStrengthError("reported target delta is absent or non-unique")
    return _finite(matches[0]["delta"], "reported delta")


def _rows(table: FrozenCalculationInput, required: set[str]) -> list[dict[str, str]]:
    text, delimiter = bounded_table_text(
        table,
        byte_ceiling=MAX_TABLE_BYTES,
        error_type=HiCLoopStrengthError,
        label="declared Hi-C table",
    )
    reader = csv.DictReader(
        io.StringIO(text, newline=""),
        delimiter=delimiter,
    )
    header = reader.fieldnames
    if (
        header is None
        or len(header) > MAX_TABLE_COLUMNS
        or len(set(header)) != len(header)
        or not required.issubset(header)
    ):
        raise HiCLoopStrengthError("declared Hi-C table columns are unavailable or ambiguous")
    rows: list[dict[str, str]] = []
    for index, row in enumerate(reader, start=1):
        if index > MAX_TABLE_ROWS:
            raise HiCLoopStrengthError("declared Hi-C table exceeds the row ceiling")
        rows.append(
            {key: str(value or "").strip() for key, value in row.items() if key is not None}
        )
    if not rows:
        raise HiCLoopStrengthError("declared Hi-C table has no data rows")
    return rows


def _pair(left: str, right: str) -> tuple[str, str]:
    if not left or not right or left == right:
        raise HiCLoopStrengthError("contact bin pair is empty or degenerate")
    return (left, right) if left < right else (right, left)


def _integer(value: object, label: str) -> int:
    try:
        number = int(str(value).strip())
    except ValueError as error:
        raise HiCLoopStrengthError(f"{label} is not an integer") from error
    if str(number) != str(value).strip():
        raise HiCLoopStrengthError(f"{label} is not a canonical integer")
    return number


def _boolean(value: object, label: str) -> bool:
    normalized = str(value).strip().casefold()
    if normalized not in {"true", "false"}:
        raise HiCLoopStrengthError(f"{label} is not true or false")
    return normalized == "true"


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise HiCLoopStrengthError(f"{label} is not numeric")
    try:
        number = float(str(value).strip())
    except ValueError as error:
        raise HiCLoopStrengthError(f"{label} is not numeric") from error
    if not math.isfinite(number):
        raise HiCLoopStrengthError(f"{label} is not finite")
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
