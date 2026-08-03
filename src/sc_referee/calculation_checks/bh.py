from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any, Literal

from sc_referee.calculation_checks.contracts import (
    selected_sidecar_contract,
    sidecar_adapter_manifest,
    with_sidecar_lineage,
)
from sc_referee.calculation_checks.core import (
    CalculationAdapterManifest,
    CalculationCheckContractError,
    CalculationContext,
    CalculationObservation,
    FrozenCalculationInput,
    NamedOperand,
    ObservationReceipt,
)
from sc_referee.calculation_checks.delimited import bounded_table_text
from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.delimited_io import classify_delimited_path
from sc_referee.scientific_checks import RecordRef

MAX_TABLE_BYTES = 1_000_000
MAX_ROWS = 10_000
MAX_COLUMNS = 64
BH_ADAPTER_IMPLEMENTATION_DIGEST = sha256_digest(Path(__file__).read_bytes())
BH_CHECK_ID = "calculation-check:benjamini-hochberg-complete-family-v1"

_COMPLETE = re.compile(
    r"Multiplicity\s+contract:\s*Benjamini-Hochberg\s+false-discovery-rate\s+control\s+"
    r"at\s+alpha\s+(?P<alpha>(?:0(?:\.\d+)?|1(?:\.0+)?))\s+over\s+the\s+complete\s+"
    r"tested\s+family\s+in\s+`(?P<path>[^`]+)`\.\s+Raw\s+p-values\s+are\s+in\s+"
    r"`(?P<raw>[^`]+)`,\s+reported\s+adjusted\s+p-values\s+are\s+in\s+"
    r"`(?P<adjusted>[^`]+)`,\s+and\s+final\s+discovery\s+calls\s+are\s+in\s+"
    r"`(?P<call>[^`]+)`\.",
    re.IGNORECASE,
)
_ONE_PRIMARY = re.compile(
    r"one\s+preregistered\s+primary\s+hypothesis.*?"
    r"no\s+multiple-testing\s+adjustment\s+governs\s+this\s+decision",
    re.IGNORECASE | re.DOTALL,
)
_INCOMPLETE = re.compile(
    r"only\s+selected\s+hits.*?complete\s+set\s+of\s+tested\s+hypotheses.*?unavailable",
    re.IGNORECASE | re.DOTALL,
)
_UNSUPPORTED_PROCEDURE = re.compile(
    r"\b(?:Storey|weighted|hierarchical|Bonferroni|Holm|Benjamini-Yekutieli)\b",
    re.IGNORECASE,
)
BH_RECOGNITION_GRAMMAR_DIGEST = semantic_digest(
    {
        "complete": _COMPLETE.pattern,
        "one_primary": _ONE_PRIMARY.pattern,
        "incomplete": _INCOMPLETE.pattern,
        "unsupported_procedure": _UNSUPPORTED_PROCEDURE.pattern,
        "max_table_bytes": MAX_TABLE_BYTES,
        "max_rows": MAX_ROWS,
        "max_columns": MAX_COLUMNS,
    }
)

_SIDECAR_KEYS = {
    "procedure",
    "family",
    "alpha",
    "table",
    "id_column",
    "raw_pvalue_column",
    "adjusted_pvalue_column",
    "call_column",
}


@dataclass(frozen=True)
class NormalizedBHInput:
    alpha: str
    table_path: str
    id_column: str
    raw_column: str
    adjusted_column: str
    call_column: str
    source_ref: dict[str, Any]


class DeclaredBHTableAdapter:
    manifest = CalculationAdapterManifest(
        adapter_id="calculation-adapter:declared-bh-table-v1",
        adapter_version="1.0.0",
        implementation_digest=BH_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=BH_RECOGNITION_GRAMMAR_DIGEST,
    )

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        try:
            report = context.selected_report.content.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise CalculationCheckContractError("selected report is not strict UTF-8") from error
        report_source = context.selected_report.source_ref
        complete_matches = list(_COMPLETE.finditer(report))
        one_primary = _ONE_PRIMARY.search(report)
        incomplete = _INCOMPLETE.search(report)

        recognized = (
            len(complete_matches) + int(one_primary is not None) + int(incomplete is not None)
        )
        if recognized == 0:
            return None
        if recognized > 1 or len(complete_matches) > 1:
            return self._boundary_observation(
                context,
                applicability="ambiguous",
                report_source=report_source,
                predicate="unique_multiplicity_contract",
                detail="The selected report contains multiple supported multiplicity declarations.",
            )
        if one_primary is not None:
            return self._boundary_observation(
                context,
                applicability="not_applicable",
                report_source=_match_source(context, report, one_primary),
                predicate="single_preregistered_primary_declared",
                detail="The selected report explicitly limits the decision to one primary hypothesis.",
            )
        if incomplete is not None:
            return self._boundary_observation(
                context,
                applicability="ambiguous",
                report_source=_match_source(context, report, incomplete),
                predicate="complete_testing_family_available",
                detail="The selected report explicitly says that only selected hits are available.",
            )

        match = complete_matches[0]
        declaration_source = _match_source(context, report, match)
        if _UNSUPPORTED_PROCEDURE.search(report) is not None:
            return self._boundary_observation(
                context,
                applicability="ambiguous",
                report_source=declaration_source,
                predicate="single_supported_adjustment_procedure",
                detail="The selected report also names a multiplicity procedure outside this adapter.",
            )
        normalized = NormalizedBHInput(
            alpha=match.group("alpha"),
            table_path=match.group("path"),
            id_column="test_id",
            raw_column=match.group("raw"),
            adjusted_column=match.group("adjusted"),
            call_column=match.group("call"),
            source_ref=declaration_source,
        )
        return self.inspect_normalized(context, normalized)

    def inspect_normalized(
        self,
        context: CalculationContext,
        normalized: NormalizedBHInput,
    ) -> CalculationObservation:
        declaration_source = normalized.source_ref
        relative = normalized.table_path
        if (
            relative.startswith("/")
            or ".." in relative.split("/")
            or classify_delimited_path(relative) is None
        ):
            return self._unsupported(
                context,
                declaration_source,
                "declared_table_path_supported",
                "The declared table path is not a bounded relative CSV/TSV path.",
            )
        tables = [item for item in context.tabular_inputs if item.path == relative]
        if len(tables) != 1:
            return self._unsupported(
                context,
                declaration_source,
                "unique_declared_table_bound",
                "Exactly one fully digested table could not be bound to the declared path.",
            )
        table = tables[0]
        source_refs = (declaration_source, table.source_ref)
        try:
            alpha = _decimal(normalized.alpha, "alpha")
            if alpha <= 0 or alpha >= 1:
                raise CalculationCheckContractError("alpha must be strictly between zero and one")
            rows = _parse_table(
                table,
                id_column=normalized.id_column,
                raw_column=normalized.raw_column,
                adjusted_column=normalized.adjusted_column,
                call_column=normalized.call_column,
            )
        except CalculationCheckContractError as error:
            return self._unsupported(
                context,
                declaration_source,
                "declared_table_fully_parsed",
                str(error),
                table=table,
            )
        raw_values = tuple(row[1] for row in rows)
        reported_adjusted = tuple(row[2] for row in rows)
        reported_calls = tuple(row[3] for row in rows)
        recomputed_adjusted = benjamini_hochberg(raw_values)
        recomputed_calls = tuple(value <= alpha for value in recomputed_adjusted)
        adjusted_mismatches = tuple(
            index
            for index, (reported, recomputed) in enumerate(
                zip(reported_adjusted, recomputed_adjusted, strict=True), start=1
            )
            if reported != recomputed
        )
        call_mismatches = tuple(
            index
            for index, (reported, recomputed) in enumerate(
                zip(reported_calls, recomputed_calls, strict=True), start=1
            )
            if reported is not recomputed
        )
        return CalculationObservation(
            applicability="applicable",
            comparison_outcome=(
                "conformant" if not adjusted_mismatches and not call_mismatches else "nonconformant"
            ),
            target_ref=context.selected_surface_ref,
            input_refs=(context.selected_artifact_ref, table.artifact_ref),
            source_refs=source_refs,
            operands=(
                NamedOperand("declared_table_path", "string", table.path),
                NamedOperand("alpha", "string", _decimal_text(alpha)),
                NamedOperand("test_ids", "string_array", [row[0] for row in rows]),
                NamedOperand(
                    "raw_p_values", "string_array", [_decimal_text(value) for value in raw_values]
                ),
                NamedOperand(
                    "reported_adjusted_p_values",
                    "string_array",
                    [_decimal_text(value) for value in reported_adjusted],
                ),
                NamedOperand(
                    "recomputed_adjusted_p_values",
                    "string_array",
                    [_decimal_text(value) for value in recomputed_adjusted],
                ),
                NamedOperand("reported_calls", "boolean_array", list(reported_calls)),
                NamedOperand("recomputed_calls", "boolean_array", list(recomputed_calls)),
                NamedOperand("reported_discovery_count", "integer", sum(reported_calls)),
                NamedOperand("recomputed_discovery_count", "integer", sum(recomputed_calls)),
                NamedOperand(
                    "adjusted_mismatch_indices", "integer_array", list(adjusted_mismatches)
                ),
                NamedOperand("call_mismatch_indices", "integer_array", list(call_mismatches)),
            ),
            receipts=(
                ObservationReceipt(
                    "applicability",
                    "explicit_complete_family_bh_contract",
                    "passed",
                    (declaration_source,),
                    "The selected report declares BH/FDR, alpha, complete family, path, and columns.",
                ),
                ObservationReceipt(
                    "ambiguity",
                    "unique_supported_contract_declaration",
                    "passed",
                    (declaration_source,),
                    "Exactly one supported contract declaration was present.",
                ),
                ObservationReceipt(
                    "completeness",
                    "unique_fully_digested_table",
                    "passed",
                    (table.source_ref,),
                    f"The declared table parsed completely within {MAX_ROWS} rows.",
                ),
                ObservationReceipt(
                    "counterevidence",
                    "unsupported_adjustment_declaration_absent",
                    "passed",
                    (declaration_source,),
                    "No supported conflicting multiplicity declaration was found in the report.",
                ),
            ),
            lineage_status="complete",
            limitations=(
                "The calculation checks only the explicitly declared table and BH contract.",
                "It does not establish that the table drove a publication or that BH was scientifically required.",
            ),
        )

    def _boundary_observation(
        self,
        context: CalculationContext,
        *,
        applicability: Literal["ambiguous", "not_applicable"],
        report_source: dict[str, Any],
        predicate: str,
        detail: str,
    ) -> CalculationObservation:
        if applicability not in {"ambiguous", "not_applicable"}:
            raise CalculationCheckContractError("invalid boundary applicability")
        return CalculationObservation(
            applicability=applicability,
            comparison_outcome="unknown" if applicability == "ambiguous" else "not_applicable",
            target_ref=context.selected_surface_ref,
            input_refs=(context.selected_artifact_ref,),
            source_refs=(report_source,),
            operands=(),
            receipts=(
                ObservationReceipt(
                    "ambiguity" if applicability == "ambiguous" else "applicability",
                    predicate,
                    "triggered" if applicability == "ambiguous" else "not_applicable",
                    (report_source,),
                    detail,
                ),
            ),
            lineage_status="incomplete" if applicability == "ambiguous" else "not_applicable",
            limitations=(
                "No adverse calculation conclusion is permitted from this boundary state.",
            ),
        )

    def _unsupported(
        self,
        context: CalculationContext,
        report_source: dict[str, Any],
        predicate: str,
        detail: str,
        *,
        table: FrozenCalculationInput | None = None,
    ) -> CalculationObservation:
        input_refs: tuple[RecordRef, ...] = (context.selected_artifact_ref,)
        source_refs: tuple[dict[str, Any], ...] = (report_source,)
        if table is not None:
            input_refs = (*input_refs, table.artifact_ref)
            source_refs = (*source_refs, table.source_ref)
        return CalculationObservation(
            applicability="unsupported",
            comparison_outcome="unknown",
            target_ref=context.selected_surface_ref,
            input_refs=input_refs,
            source_refs=source_refs,
            operands=(),
            receipts=(
                ObservationReceipt(
                    "completeness",
                    predicate,
                    "unsupported",
                    source_refs,
                    detail,
                ),
            ),
            lineage_status="incomplete",
            limitations=(detail, "No numerical disagreement was inferred."),
        )


class SelectedSidecarBHTableAdapter:
    manifest = sidecar_adapter_manifest(
        family="bh-complete-family",
        implementation_digest=BH_ADAPTER_IMPLEMENTATION_DIGEST,
    )

    def __init__(self) -> None:
        self._evaluator = DeclaredBHTableAdapter()

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        sidecar = selected_sidecar_contract(context, check_id=BH_CHECK_ID)
        if sidecar is None:
            return None
        value = sidecar.value
        if set(value) != _SIDECAR_KEYS or any(
            not isinstance(value.get(key), str) or not str(value[key]).strip()
            for key in _SIDECAR_KEYS
        ):
            raise CalculationCheckContractError("BH sidecar contract keys must be exact strings")
        if value["procedure"] != "benjamini_hochberg" or value["family"] != "complete":
            raise CalculationCheckContractError(
                "BH sidecar requires a complete benjamini_hochberg family"
            )
        normalized = NormalizedBHInput(
            alpha=str(value["alpha"]).strip(),
            table_path=str(value["table"]).strip(),
            id_column=str(value["id_column"]).strip(),
            raw_column=str(value["raw_pvalue_column"]).strip(),
            adjusted_column=str(value["adjusted_pvalue_column"]).strip(),
            call_column=str(value["call_column"]).strip(),
            source_ref=sidecar.source_ref,
        )
        return with_sidecar_lineage(
            self._evaluator.inspect_normalized(context, normalized),
            sidecar,
        )


def benjamini_hochberg(values: tuple[Decimal, ...]) -> tuple[Decimal, ...]:
    if not values:
        raise CalculationCheckContractError("BH requires at least one p-value")
    if any(not value.is_finite() or value < 0 or value > 1 for value in values):
        raise CalculationCheckContractError("BH p-values must be finite values in [0, 1]")
    order = sorted(range(len(values)), key=lambda index: (values[index], index))
    adjusted = [Decimal(1)] * len(values)
    running = Decimal(1)
    with localcontext() as context:
        context.prec = 50
        for rank, index in reversed(list(enumerate(order, start=1))):
            running = min(running, values[index] * Decimal(len(values)) / Decimal(rank), Decimal(1))
            adjusted[index] = running
    return tuple(adjusted)


def _parse_table(
    table: FrozenCalculationInput,
    *,
    id_column: str,
    raw_column: str,
    adjusted_column: str,
    call_column: str,
) -> tuple[tuple[str, Decimal, Decimal, bool], ...]:
    text, delimiter = bounded_table_text(
        table,
        byte_ceiling=MAX_TABLE_BYTES,
        error_type=CalculationCheckContractError,
        label="declared table",
    )
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    try:
        header = next(reader)
    except (StopIteration, csv.Error) as error:
        raise CalculationCheckContractError("declared table header is unavailable") from error
    if not header or len(header) > MAX_COLUMNS or len(header) != len(set(header)):
        raise CalculationCheckContractError(
            "declared table header is empty, duplicated, or over budget"
        )
    required = (id_column, raw_column, adjusted_column, call_column)
    if len(set(required)) != len(required) or any(name not in header for name in required):
        raise CalculationCheckContractError(
            "declared table column binding is incomplete or overlapping"
        )
    indexes = tuple(header.index(name) for name in required)
    rows: list[tuple[str, Decimal, Decimal, bool]] = []
    seen: set[str] = set()
    try:
        for row_number, row in enumerate(reader, start=2):
            if row_number > MAX_ROWS + 1:
                raise CalculationCheckContractError("declared table exceeds the row ceiling")
            if len(row) != len(header):
                raise CalculationCheckContractError("declared table has an inconsistent row width")
            identifier = row[indexes[0]]
            if not identifier or identifier in seen:
                raise CalculationCheckContractError("test identifiers are empty or duplicated")
            seen.add(identifier)
            raw = _decimal(row[indexes[1]], "raw p-value")
            adjusted = _decimal(row[indexes[2]], "adjusted p-value")
            if not (Decimal(0) <= raw <= Decimal(1)) or not (Decimal(0) <= adjusted <= Decimal(1)):
                raise CalculationCheckContractError("p-values must be in [0, 1]")
            call_text = row[indexes[3]].casefold()
            if call_text not in {"true", "false"}:
                raise CalculationCheckContractError("discovery calls must use true or false")
            rows.append((identifier, raw, adjusted, call_text == "true"))
    except csv.Error as error:
        raise CalculationCheckContractError(
            "declared table could not be parsed completely"
        ) from error
    if not rows:
        raise CalculationCheckContractError("declared table has no hypothesis rows")
    return tuple(rows)


def _decimal(value: str, field: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise CalculationCheckContractError(f"{field} is not an exact decimal") from error
    if not parsed.is_finite():
        raise CalculationCheckContractError(f"{field} must be finite")
    return parsed


def _decimal_text(value: Decimal) -> str:
    text = format(value, "f").rstrip("0").rstrip(".")
    return text or "0"


def _match_source(context: CalculationContext, report: str, match: re.Match[str]) -> dict[str, Any]:
    start_line = report.count("\n", 0, match.start()) + 1
    end_line = report.count("\n", 0, match.end()) + 1
    return {
        "source_kind": "file_span",
        "locator": f"{context.selected_report.path}:{start_line}-{end_line}",
        "path": context.selected_report.path,
        "content_digest": context.selected_report.content_digest,
        "start_line": start_line,
        "end_line": end_line,
        "quoted_text": match.group(0),
    }
