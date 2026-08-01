from __future__ import annotations

import csv
import io
import math
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
import yaml

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

_BLOCK = re.compile(
    r"```sc-referee-eqtl-sign-v1\s*\n(?P<body>.*?)\n```",
    re.IGNORECASE | re.DOTALL,
)
_REQUIRED_KEYS = {
    "donor_table",
    "results_table",
    "donor_id_column",
    "genotype_column",
    "expression_column",
    "result_feature_column",
    "result_effect_column",
    "variant_id",
    "target_feature",
    "variant_alleles",
    "dosage_counts_allele",
    "effect_allele",
    "dosage_ploidy",
    "estimator",
    "outcome_scale",
    "minimum_donors_per_supported_class",
    "producer_binding",
    "orientation_binding",
}
_RECOGNITION_GRAMMAR_DIGEST = semantic_digest(
    {
        "block_pattern": _BLOCK.pattern,
        "required_keys": sorted(_REQUIRED_KEYS),
        "estimator": ["ols_with_intercept"],
        "outcome_scale": ["log2_cpm_plus_1"],
        "binding": ["exact", "unresolved"],
        "ceilings": {
            "table_bytes": MAX_TABLE_BYTES,
            "table_rows": MAX_TABLE_ROWS,
            "table_columns": MAX_TABLE_COLUMNS,
        },
    }
)


class EqtlSignError(ValueError):
    """Raised when an eQTL sign input escapes the closed contract."""


@dataclass(frozen=True)
class _Contract:
    donor_table: str
    results_table: str
    donor_id_column: str
    genotype_column: str
    expression_column: str
    result_feature_column: str
    result_effect_column: str
    variant_id: str
    target_feature: str
    variant_alleles: tuple[str, str]
    dosage_counts_allele: str
    effect_allele: str
    dosage_ploidy: int
    estimator: str
    outcome_scale: str
    minimum_donors_per_supported_class: int
    producer_binding: str
    orientation_binding: str
    source_ref: dict[str, Any]


@dataclass(frozen=True)
class _Recompute:
    n_donors: int
    class_labels: tuple[str, ...]
    class_counts: tuple[int, ...]
    raw_dosage_frequency: float
    transform: str
    slope: float
    slope_standard_error: float
    reported_effect: float


class DeclaredEqtlSignAdapter:
    def __init__(self) -> None:
        self.manifest = CalculationAdapterManifest(
            adapter_id="calculation-adapter:declared-donor-eqtl-sign-v1",
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
            raise EqtlSignError("selected report is not strict UTF-8") from error
        matches = list(_BLOCK.finditer(report))
        if not matches:
            return None
        if len(matches) != 1:
            return self._unsupported(
                context,
                context.selected_report.source_ref,
                "unique_eqtl_sign_contract",
                "The selected report contains more than one eQTL-sign contract.",
            )
        match = matches[0]
        source_ref = _block_source(context.selected_report, report, match)
        try:
            contract = _parse_contract(match.group("body"), source_ref)
        except EqtlSignError as error:
            return self._unsupported(
                context,
                source_ref,
                "eqtl_sign_contract_valid",
                str(error),
            )
        if (
            contract.producer_binding == "unresolved"
            or contract.orientation_binding == "unresolved"
        ):
            return self._unsupported(
                context,
                source_ref,
                "producer_and_orientation_bindings_resolved",
                "The exact result producer or allele-orientation binding remains unresolved.",
            )
        if not isinstance(context, MaterialCalculationContext):
            return self._unsupported(
                context,
                source_ref,
                "material_calculation_context_available",
                "The explicitly selected donor and result tables were not available in the frozen material-input view.",
            )
        donor_table = _unique_material(context, contract.donor_table)
        results_table = _unique_material(context, contract.results_table)
        if donor_table is None or results_table is None:
            return self._unsupported(
                context,
                source_ref,
                "declared_eqtl_inputs_bound",
                "Exactly one fully identified donor table and result table could not be bound.",
                inputs=tuple(item for item in (donor_table, results_table) if item is not None),
            )
        try:
            recompute = _recompute(donor_table, results_table, contract)
        except EqtlSignError as error:
            return self._unsupported(
                context,
                source_ref,
                "complete_donor_eqtl_recompute",
                str(error),
                inputs=(donor_table, results_table),
            )
        reported_sign = 1 if recompute.reported_effect > 0 else -1
        recomputed_sign = 1 if recompute.slope > 0 else -1
        agrees = reported_sign == recomputed_sign
        sources = (source_ref, donor_table.source_ref, results_table.source_ref)
        return CalculationObservation(
            applicability="applicable",
            comparison_outcome="conformant" if agrees else "nonconformant",
            target_ref=context.selected_surface_ref,
            input_refs=(
                context.selected_artifact_ref,
                donor_table.artifact_ref,
                results_table.artifact_ref,
            ),
            source_refs=sources,
            operands=(
                NamedOperand("donor_table_path", "string", donor_table.path),
                NamedOperand("results_table_path", "string", results_table.path),
                NamedOperand("variant_id", "string", contract.variant_id),
                NamedOperand("target_feature", "string", contract.target_feature),
                NamedOperand("effect_allele", "string", contract.effect_allele),
                NamedOperand("dosage_counts_allele", "string", contract.dosage_counts_allele),
                NamedOperand("orientation_transform", "string", recompute.transform),
                NamedOperand("donor_count", "integer", recompute.n_donors),
                NamedOperand("genotype_class_labels", "string_array", list(recompute.class_labels)),
                NamedOperand(
                    "genotype_class_counts", "integer_array", list(recompute.class_counts)
                ),
                NamedOperand(
                    "raw_dosage_allele_frequency",
                    "finite_number",
                    recompute.raw_dosage_frequency,
                ),
                NamedOperand("reported_effect", "finite_number", recompute.reported_effect),
                NamedOperand("reported_sign", "integer", reported_sign),
                NamedOperand("recomputed_slope", "finite_number", recompute.slope),
                NamedOperand("recomputed_sign", "integer", recomputed_sign),
                NamedOperand(
                    "recomputed_slope_standard_error",
                    "finite_number",
                    recompute.slope_standard_error,
                ),
                NamedOperand("sign_agreement", "boolean", agrees),
            ),
            receipts=(
                ObservationReceipt(
                    "applicability",
                    "explicit_donor_eqtl_sign_contract",
                    "passed",
                    (source_ref,),
                    "One closed declaration binds the variant, feature, alleles, dosage orientation, estimator, outcome scale, and exact tables.",
                ),
                ObservationReceipt(
                    "completeness",
                    "unique_donor_rows_and_target_result",
                    "passed",
                    (donor_table.source_ref, results_table.source_ref),
                    "Donor identities were unique and exactly one finite nonzero reported effect matched the target feature.",
                ),
                ObservationReceipt(
                    "completeness",
                    "supported_genotype_classes",
                    "passed",
                    (donor_table.source_ref,),
                    "At least two genotype classes met the declared finite donor-support floor.",
                ),
                ObservationReceipt(
                    "counterevidence",
                    "allele_orientation_and_model_scope",
                    "passed",
                    (source_ref,),
                    "Unresolved allele identity, an unsupported estimator or scale, or incomplete donor support would have forced abstention.",
                ),
            ),
            lineage_status="complete",
            limitations=(
                "This independently recomputes only the sign of one unadjusted donor-level OLS slope on the declared outcome scale; it does not reproduce the effect magnitude or support adjusted, mixed, nonlinear, or count-likelihood models.",
                "Allele declarations establish review-scoped orientation, not historical execution, variant authenticity, causal interpretation, or biological truth.",
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
            limitations=(detail, "No eQTL orientation disagreement was inferred."),
        )


def eqtl_sign_registry() -> CalculationCheckRegistry:
    adapter = DeclaredEqtlSignAdapter()
    check = CalculationCheckManifest(
        check_id="calculation-check:donor-eqtl-sign-v1",
        check_version="1.0.0",
        implementation_digest=sha256_digest(Path(__file__).read_bytes()),
        comparison_relation="declared_effect_allele_reported_vs_donor_ols_sign_conformance",
        output_ceiling="disclosure_only",
        permitted_wording=(
            "The reported target-effect sign differs from the independently recomputed donor-level OLS sign after applying the exact declared allele orientation."
        ),
    )
    return CalculationCheckRegistry(
        (CalculationCheckModule(check, (adapter,)),),
        profile_id="deterministic_donor_eqtl_sign_v1",
    )


def _parse_contract(body: str, source_ref: dict[str, Any]) -> _Contract:
    try:
        value = yaml.safe_load(body)
    except yaml.YAMLError as error:
        raise EqtlSignError("eQTL-sign contract is not valid YAML") from error
    if not isinstance(value, dict) or set(value) != _REQUIRED_KEYS:
        raise EqtlSignError("eQTL-sign contract keys are missing or extra")
    text_keys = _REQUIRED_KEYS - {
        "variant_alleles",
        "dosage_ploidy",
        "minimum_donors_per_supported_class",
    }
    if any(not isinstance(value[key], str) or not value[key].strip() for key in text_keys):
        raise EqtlSignError("eQTL-sign text values must be nonempty strings")
    for key in ("donor_table", "results_table"):
        path = PurePosixPath(str(value[key]))
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.suffix.casefold() not in {".csv", ".tsv"}
        ):
            raise EqtlSignError("eQTL input paths must be bounded CSV or TSV paths")
    alleles = value["variant_alleles"]
    if (
        not isinstance(alleles, list)
        or len(alleles) != 2
        or any(not isinstance(item, str) or not item.strip() for item in alleles)
        or alleles[0] == alleles[1]
    ):
        raise EqtlSignError("variant_alleles must contain two distinct nonempty strings")
    allele_tuple = (alleles[0].strip(), alleles[1].strip())
    if (
        value["dosage_counts_allele"] not in allele_tuple
        or value["effect_allele"] not in allele_tuple
    ):
        raise EqtlSignError("dosage and effect alleles must occur in variant_alleles")
    if value["dosage_ploidy"] != 2:
        raise EqtlSignError("initial eQTL sign profile supports diploid dosage only")
    support = value["minimum_donors_per_supported_class"]
    if isinstance(support, bool) or not isinstance(support, int) or support < 3 or support > 100:
        raise EqtlSignError("donor support floor must be an integer from 3 through 100")
    if value["estimator"] != "ols_with_intercept" or value["outcome_scale"] != "log2_cpm_plus_1":
        raise EqtlSignError("estimator or outcome scale is outside the closed initial profile")
    if value["producer_binding"] not in {"exact", "unresolved"} or value[
        "orientation_binding"
    ] not in {"exact", "unresolved"}:
        raise EqtlSignError("eQTL binding is outside the closed vocabulary")
    return _Contract(
        donor_table=str(value["donor_table"]).strip(),
        results_table=str(value["results_table"]).strip(),
        donor_id_column=str(value["donor_id_column"]).strip(),
        genotype_column=str(value["genotype_column"]).strip(),
        expression_column=str(value["expression_column"]).strip(),
        result_feature_column=str(value["result_feature_column"]).strip(),
        result_effect_column=str(value["result_effect_column"]).strip(),
        variant_id=str(value["variant_id"]).strip(),
        target_feature=str(value["target_feature"]).strip(),
        variant_alleles=allele_tuple,
        dosage_counts_allele=str(value["dosage_counts_allele"]).strip(),
        effect_allele=str(value["effect_allele"]).strip(),
        dosage_ploidy=2,
        estimator=str(value["estimator"]).strip(),
        outcome_scale=str(value["outcome_scale"]).strip(),
        minimum_donors_per_supported_class=support,
        producer_binding=str(value["producer_binding"]).strip(),
        orientation_binding=str(value["orientation_binding"]).strip(),
        source_ref=source_ref,
    )


def _recompute(
    donor_table: FrozenCalculationInput,
    results_table: FrozenCalculationInput,
    contract: _Contract,
) -> _Recompute:
    donor_rows = _rows(
        donor_table,
        {contract.donor_id_column, contract.genotype_column, contract.expression_column},
    )
    donor_ids: set[str] = set()
    raw_genotypes: list[float] = []
    expression: list[float] = []
    for row in donor_rows:
        donor = row[contract.donor_id_column].strip()
        if not donor or donor in donor_ids:
            raise EqtlSignError("donor identifiers are empty or duplicated")
        donor_ids.add(donor)
        genotype = _finite(row[contract.genotype_column], "genotype dosage")
        outcome = _finite(row[contract.expression_column], "donor expression")
        if genotype not in {0.0, 1.0, 2.0}:
            raise EqtlSignError("diploid genotype dosage must be exactly 0, 1, or 2")
        raw_genotypes.append(genotype)
        expression.append(outcome)
    if len(donor_ids) < 6:
        raise EqtlSignError("fewer than six unique donors are available")
    counts_by_class = {value: raw_genotypes.count(value) for value in (0.0, 1.0, 2.0)}
    supported = sum(
        count >= contract.minimum_donors_per_supported_class for count in counts_by_class.values()
    )
    if supported < 2:
        raise EqtlSignError("fewer than two genotype classes meet the donor-support floor")
    transform = (
        "identity"
        if contract.dosage_counts_allele == contract.effect_allele
        else "diploid_complement"
    )
    oriented = np.asarray(
        raw_genotypes if transform == "identity" else [2.0 - value for value in raw_genotypes],
        dtype=float,
    )
    outcomes = np.asarray(expression, dtype=float)
    design = np.column_stack((np.ones(len(oriented), dtype=float), oriented))
    if int(np.linalg.matrix_rank(design)) != 2:
        raise EqtlSignError("donor-level OLS design is rank deficient")
    coefficients, _, _, _ = np.linalg.lstsq(design, outcomes, rcond=None)
    residuals = outcomes - design @ coefficients
    degrees = len(outcomes) - 2
    if degrees <= 0:
        raise EqtlSignError("donor-level OLS has no residual degrees of freedom")
    variance = float(np.dot(residuals, residuals) / degrees)
    covariance = variance * np.linalg.inv(design.T @ design)
    slope = float(coefficients[1])
    standard_error = float(math.sqrt(max(0.0, covariance[1, 1])))
    if not math.isfinite(slope) or slope == 0 or not math.isfinite(standard_error):
        raise EqtlSignError("donor-level OLS slope has no finite nonzero direction")

    result_rows = _rows(
        results_table,
        {contract.result_feature_column, contract.result_effect_column},
    )
    matches = [
        row for row in result_rows if row[contract.result_feature_column] == contract.target_feature
    ]
    if len(matches) != 1:
        raise EqtlSignError("target feature does not have exactly one result row")
    reported = _finite(matches[0][contract.result_effect_column], "reported effect")
    if reported == 0:
        raise EqtlSignError("reported target effect has no direction")
    return _Recompute(
        n_donors=len(donor_ids),
        class_labels=("0", "1", "2"),
        class_counts=tuple(counts_by_class[value] for value in (0.0, 1.0, 2.0)),
        raw_dosage_frequency=sum(raw_genotypes) / (2 * len(raw_genotypes)),
        transform=transform,
        slope=slope,
        slope_standard_error=standard_error,
        reported_effect=reported,
    )


def _rows(table: FrozenCalculationInput, required: set[str]) -> list[dict[str, str]]:
    if len(table.content) > MAX_TABLE_BYTES:
        raise EqtlSignError("declared eQTL table exceeds the byte ceiling")
    try:
        text = table.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise EqtlSignError("declared eQTL table is not strict UTF-8") from error
    reader = csv.DictReader(
        io.StringIO(text, newline=""),
        delimiter="\t" if table.path.casefold().endswith(".tsv") else ",",
    )
    header = reader.fieldnames
    if (
        header is None
        or len(header) > MAX_TABLE_COLUMNS
        or len(set(header)) != len(header)
        or not required.issubset(header)
    ):
        raise EqtlSignError("declared eQTL table columns are unavailable or ambiguous")
    rows: list[dict[str, str]] = []
    for index, row in enumerate(reader, start=1):
        if index > MAX_TABLE_ROWS:
            raise EqtlSignError("declared eQTL table exceeds the row ceiling")
        rows.append(
            {key: str(value or "").strip() for key, value in row.items() if key is not None}
        )
    if not rows:
        raise EqtlSignError("declared eQTL table has no data rows")
    return rows


def _finite(value: object, label: str) -> float:
    try:
        number = float(str(value).strip())
    except ValueError as error:
        raise EqtlSignError(f"{label} is not numeric") from error
    if not math.isfinite(number):
        raise EqtlSignError(f"{label} is not finite")
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
