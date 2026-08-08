"""ADR-0069 quantity-consistency recognition for denominator-domain checks.

This adapter recognizes an analysis-method declaration from the arithmetic
relations among the quantities a selected report states, never from
nomenclature. It searches the report's number tokens for one complete
accounting (a complete count N, a retained count M, a stated removed count
K with N = M + K, and an event count E with E <= M < N) and one stated rate
that reconciles, within the rate's own stated precision, with exactly one of
E/M (the retained subset exposure) or E/N (the complete domain exposure).
Variable names, unit nouns, and domain nouns never gate recognition; a date
or an incidental integer cannot form an interpretation unless the additive
accounting relation and the ratio relation both hold. Conflicting
reconciliations abstain as ambiguous; an absent accounting abstains as
not applicable; nothing is inferred from unstated quantities.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.parsers.python_ast import PARSER_ID as PYTHON_PARSER_ID
from sc_referee.parsers.python_ast import PARSER_VERSION as PYTHON_PARSER_VERSION
from sc_referee.scientific_checks.adapter_common import (
    adapter_implementation_digest,
    receipt_description,
    receipt_kind,
    selected_report_document,
    selected_surface_owns_artifact,
)
from sc_referee.scientific_checks.core import (
    AdapterManifest,
    CanonicalOperand,
    CheckManifest,
    EvidenceSpan,
    FrozenInspectionContext,
    InspectionDocument,
    InspectionReceipt,
    NormalizedMethodObservation,
    RoleBinding,
)
from sc_referee.scientific_checks.quantity_dataflow_adapter import (
    QUANTITY_DATAFLOW_IMPLEMENTATION_DIGEST,
    quantity_dataflow_grammar,
    resolve_dataflow_operand,
)
from sc_referee.scientific_checks.scope_joins import selected_publication_path

QUANTITY_CONSISTENCY_ADAPTER_IMPLEMENTATION_DIGEST = adapter_implementation_digest(Path(__file__))

# A digit glued to a word by a hyphen ("interval-2") is an identifier suffix,
# not a stated quantity; a comma-grouped number ("1,900") is one number.
_NUMBER_PATTERN = (
    r"(?<![\w.])(?<!\w-)(?<!\d-)(?<!-)"
    r"(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)"
    r"(?!\w|\.\d|,\d{3}|-[A-Za-z0-9])"
)
# A slash-separated date such as 08/07/2026 contributes no counts; a single
# slash with spaces or one separator ("15/60") stays a legitimate fraction.
_SLASH_DATE_PATTERN = r"(?<![\d/])\d{1,4}/\d{1,2}/\d{1,4}(?![\d/])"
# Standardized measurement notation (SI and common laboratory unit symbols,
# plus the percent sign) is closed international notation, not free
# nomenclature: a unit-suffixed number is a measurement, never a unit count,
# and a percent-suffixed number is a rate statement. Alternatives are ordered
# longest first so a shorter symbol cannot shadow a longer one.
_UNIT_SUFFIX_PATTERN = (
    r"\s*(?:km2|ppt|ppm|ppb|km|cm|mm|nm|um|µm|kg|mg|ug|µg|ng|g|ms|min|hrs|hr|h|s|"
    r"ha|mL|ml|L|kbp|mbp|bp)\b"
)
_PERCENT_SUFFIX_PATTERN = r"\s*(?:%|percent\b)"
_MAX_DISTINCT_INTEGERS = 48
_MAX_RATE_TOKENS = 32

QUANTITY_COUNTEREVIDENCE = (
    "bounded-number-token-scan-complete",
    "single-consistent-reconciliation",
    "alternative-denominator-refuted",
    "selected-surface-identity-complete",
)


@dataclass(frozen=True)
class _NumberToken:
    value: float
    raw: str
    start: int
    end: int
    is_integer: bool
    decimals: int
    is_percent: bool = False


@dataclass(frozen=True)
class _Interpretation:
    complete_count: int
    retained_count: int
    removed_count: int
    event_count: int
    rate_token: _NumberToken
    rate_value: float
    operand_value: str
    count_tokens: tuple[_NumberToken, ...]


def quantity_recognition_grammar(complete_operand: str, retained_operand: str) -> dict[str, Any]:
    return {
        "grammar_id": "quantity-accounting-reconciliation",
        "grammar_version": "1.0.0",
        "number_token_pattern": _NUMBER_PATTERN,
        "unit_suffix_exclusion": _UNIT_SUFFIX_PATTERN,
        "percent_suffix": _PERCENT_SUFFIX_PATTERN,
        "count_source": "integer_tokens_without_unit_or_percent_suffix",
        "rate_source": "decimal_point_or_percent_suffixed_tokens_direct_or_percent_scaled",
        "relations": [
            "complete_count == retained_count + removed_count",
            "1 <= event_count <= retained_count < complete_count",
            "each accounting quantity is a distinct number-token occurrence",
            "rate reconciles with exactly one of event/retained or event/complete",
            "operand ties break only via another document's quantity-multiset support",
        ],
        "tolerance": "half_unit_in_last_stated_decimal_of_the_rate_token",
        "operand_by_relation": {
            "event_over_retained": retained_operand,
            "event_over_complete": complete_operand,
        },
        "bounds": {
            "max_distinct_integers": _MAX_DISTINCT_INTEGERS,
            "max_rate_tokens": _MAX_RATE_TOKENS,
        },
        "source_dataflow": quantity_dataflow_grammar(complete_operand, retained_operand),
        "source_dataflow_implementation_digest": QUANTITY_DATAFLOW_IMPLEMENTATION_DIGEST,
        "plane_fusion": (
            "either plane resolves alone; a unique source dataflow breaks report "
            "ties; disagreement between planes abstains as ambiguous; a "
            "dataflow-only classification requires a stated complete accounting"
        ),
        "additional_exclusions": ["signed values", "slash-separated dates"],
        "nomenclature_authority": "none",
    }


def quantity_recognition_grammar_digest(complete_operand: str, retained_operand: str) -> str:
    return semantic_digest(quantity_recognition_grammar(complete_operand, retained_operand))


@dataclass(frozen=True)
class QuantityConsistencyReportAdapter:
    """Recognize the selected denominator's domain from quantity arithmetic alone."""

    check_manifest: CheckManifest
    adapter_manifest: AdapterManifest
    complete_operand: CanonicalOperand
    retained_operand: CanonicalOperand

    @property
    def adapter_id(self) -> str:
        return self.adapter_manifest.adapter_id

    @property
    def adapter_version(self) -> str:
        return self.adapter_manifest.adapter_version

    @property
    def implementation_digest(self) -> str:
        return QUANTITY_CONSISTENCY_ADAPTER_IMPLEMENTATION_DIGEST

    @property
    def recognition_grammar_digest(self) -> str:
        return quantity_recognition_grammar_digest(
            str(self.complete_operand.value), str(self.retained_operand.value)
        )

    def inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        document = selected_report_document(context)
        if document is None:
            return self._abstain(
                "unsupported",
                "The selected report has no exact supported immutable text and parser identity.",
            )
        try:
            text = document.content.decode("utf-8")
        except UnicodeDecodeError:
            return self._abstain(
                "unsupported",
                "The selected report is not strict UTF-8 text.",
                document=document,
            )
        tokens = _number_tokens(text)
        integers = [item for item in tokens if item.is_integer and not item.is_percent]
        rates = [item for item in tokens if not item.is_integer or item.is_percent]
        if len({int(item.value) for item in integers}) > _MAX_DISTINCT_INTEGERS:
            return self._abstain(
                "unsupported",
                "The selected report exceeds the bounded distinct-integer scan.",
                document=document,
            )
        if len(rates) > _MAX_RATE_TOKENS:
            return self._abstain(
                "unsupported",
                "The selected report exceeds the bounded rate-token scan.",
                document=document,
            )
        interpretations = _interpretations(
            integers,
            rates,
            complete_operand=str(self.complete_operand.value),
            retained_operand=str(self.retained_operand.value),
        )
        report_operands = sorted({item.operand_value for item in interpretations})
        report_had_conflict = len(report_operands) > 1
        flow = resolve_dataflow_operand(
            context,
            complete_operand=str(self.complete_operand.value),
            retained_operand=str(self.retained_operand.value),
            parser_id=PYTHON_PARSER_ID,
            parser_version=PYTHON_PARSER_VERSION,
        )
        if flow.state == "ambiguous":
            return self._abstain(
                "ambiguous",
                "The workflow source computes rates over conflicting exposure domains.",
                document=document,
            )
        if len(report_operands) > 1:
            # Tie-breaks, in order: a unique source-dataflow classification,
            # then another captured document's quantity-multiset support. A
            # coincidental reconciliation reuses a report number in two roles
            # or invents an accounting the rest of the repository never
            # states; nomenclature still plays no part.
            if flow.state == "unique":
                interpretations = [
                    item for item in interpretations if item.operand_value == flow.operand_value
                ]
            else:
                inventories = _corroborating_inventories(context, document.path)
                interpretations = [
                    item
                    for item in interpretations
                    if any(_supports(inventory, item) for inventory in inventories)
                ]
            report_operands = sorted({item.operand_value for item in interpretations})
        if len(report_operands) > 1:
            return self._abstain(
                "ambiguous",
                (
                    "The stated quantities reconcile with more than one exposure domain "
                    "and neither the workflow dataflow nor another captured document "
                    "resolves exactly one."
                ),
                document=document,
            )
        if report_operands and flow.state == "unique" and report_operands[0] != flow.operand_value:
            return self._abstain(
                "ambiguous",
                (
                    "The report arithmetic and the workflow-source dataflow disagree "
                    "on the exposure domain."
                ),
                document=document,
            )
        if not report_operands and flow.state == "unique" and not _accounting_present(integers):
            # The dataflow plane alone may classify only when the report
            # itself states a complete accounting (a strict subset with a
            # stated removed count); without one, a tautologically
            # conditioned subset could otherwise fire on clean work.
            return self._abstain(
                "not_applicable",
                (
                    "The workflow dataflow resolves an exposure domain, but the "
                    "selected report states no complete planned-unit accounting."
                ),
                document=document,
            )
        if not report_operands and flow.state != "unique":
            if report_had_conflict:
                return self._abstain(
                    "ambiguous",
                    (
                        "The stated quantities reconcile with more than one exposure "
                        "domain and no tie-break resolves exactly one."
                    ),
                    document=document,
                )
            if flow.state == "unsupported":
                return self._abstain(
                    "unsupported",
                    (
                        "No reconcilable report accounting exists and the workflow "
                        "source uses control flow beyond the supported dataflow trace."
                    ),
                    document=document,
                )
            return self._abstain(
                "not_applicable",
                (
                    "Neither the selected report's quantities nor the workflow "
                    "source's dataflow states a retained-subset or complete-domain "
                    "rate exposure."
                ),
                document=document,
            )
        target = context.selected_artifact_ref
        scope_path = selected_publication_path(
            context.scope_join_graph,
            selected_artifact_ref=target,
            selected_surface_ref=context.selected_surface_ref,
            relation="selected_by_publication_surface",
        )
        if not scope_path or not selected_surface_owns_artifact(context):
            return self._abstain(
                "unsupported",
                "The selected report Artifact is not owned by the resolved "
                "PublicationSurface selection.",
                document=document,
            )
        operand_value = report_operands[0] if report_operands else flow.operand_value
        basis = (
            "report_arithmetic_and_source_dataflow"
            if report_operands and flow.state == "unique"
            else "report_arithmetic"
            if report_operands
            else "source_dataflow"
        )
        operand = (
            self.retained_operand
            if operand_value == str(self.retained_operand.value)
            else self.complete_operand
        )
        chosen = interpretations[0] if interpretations else None
        report_spans = (
            tuple(
                _evidence_span(document, text, token.start, token.end)
                for token in sorted(
                    {chosen.rate_token, *chosen.count_tokens}, key=lambda item: item.start
                )
            )
            if chosen is not None
            else ()
        )
        spans = report_spans + (flow.spans if flow.state == "unique" else ())
        if chosen is not None:
            role_bindings = (
                RoleBinding(
                    "selected_rate_or_spacing_estimate",
                    f"stated_rate_token:{chosen.rate_token.raw}",
                ),
                RoleBinding(
                    "exposure_denominator",
                    "reconciled_denominator_count:"
                    + str(
                        chosen.retained_count
                        if chosen.operand_value == str(self.retained_operand.value)
                        else chosen.complete_count
                    ),
                ),
                RoleBinding(
                    "declared_domain",
                    f"complete_accounting_count:{chosen.complete_count}",
                ),
                RoleBinding(
                    "retained_observed_subset",
                    f"retained_count:{chosen.retained_count}",
                ),
            )
        else:
            denominator = (
                "count_of_screened_subset"
                if operand_value == str(self.retained_operand.value)
                else "count_of_full_row_set"
            )
            role_bindings = (
                RoleBinding(
                    "selected_rate_or_spacing_estimate",
                    f"source_rate_division:{flow.source_path}",
                ),
                RoleBinding(
                    "exposure_denominator",
                    f"division_denominator_provenance:{denominator}",
                ),
                RoleBinding(
                    "declared_domain",
                    "full_row_set_of_staged_input",
                ),
                RoleBinding(
                    "retained_observed_subset",
                    "screened_subset_by_filtering_comprehension",
                ),
            )
        reconciliation: dict[str, Any] = {"basis": basis, "operand": operand_value}
        if chosen is not None:
            reconciliation.update(
                {
                    "complete_count": chosen.complete_count,
                    "retained_count": chosen.retained_count,
                    "removed_count": chosen.removed_count,
                    "event_count": chosen.event_count,
                    "rate_token": chosen.rate_token.raw,
                }
            )
        if flow.state == "unique":
            reconciliation["source_path"] = flow.source_path
        receipts = tuple(
            InspectionReceipt(
                receipt_id=receipt_id,
                kind=receipt_kind(receipt_id),
                state="passed",
                evidence_digest=semantic_digest(
                    {
                        "receipt_id": receipt_id,
                        "content_digest": document.content_digest,
                        "reconciliation": reconciliation,
                    }
                ),
                description=receipt_description(receipt_id),
            )
            for receipt_id in self.adapter_manifest.counterevidence_profiles
        )
        return NormalizedMethodObservation(
            check_id=self.check_manifest.check_id,
            check_version=self.check_manifest.check_version,
            check_manifest_digest=self.check_manifest.manifest_digest,
            check_implementation_digest=self.check_manifest.implementation_digest,
            adapter_id=self.adapter_id,
            adapter_version=self.adapter_version,
            adapter_manifest_digest=self.adapter_manifest.manifest_digest,
            adapter_implementation_digest=self.implementation_digest,
            parser_id=self.adapter_manifest.parser_id,
            parser_version=self.adapter_manifest.parser_version,
            applicability="applicable",
            completeness="complete",
            evidence_plane="reported_text",
            method_target_ref=target,
            role_bindings=role_bindings,
            observed_operand=operand,
            evidence_spans=spans,
            scope_join_path=scope_path,
            receipts=receipts,
            non_inferences=self.check_manifest.prohibited_inferences,
            output_ceiling="question_only",
        )

    def _abstain(
        self,
        state: str,
        reason: str,
        *,
        document: InspectionDocument | None = None,
    ) -> NormalizedMethodObservation:
        return NormalizedMethodObservation(
            check_id=self.check_manifest.check_id,
            check_version=self.check_manifest.check_version,
            check_manifest_digest=self.check_manifest.manifest_digest,
            check_implementation_digest=self.check_manifest.implementation_digest,
            adapter_id=self.adapter_id,
            adapter_version=self.adapter_version,
            adapter_manifest_digest=self.adapter_manifest.manifest_digest,
            adapter_implementation_digest=self.implementation_digest,
            parser_id=self.adapter_manifest.parser_id,
            parser_version=self.adapter_manifest.parser_version,
            applicability=state,  # type: ignore[arg-type]
            completeness="not_applicable" if state == "not_applicable" else "incomplete",
            evidence_plane="reported_text",
            method_target_ref=None,
            role_bindings=(),
            observed_operand=None,
            evidence_spans=(),
            scope_join_path=(),
            receipts=(
                InspectionReceipt(
                    receipt_id="closed-abstention",
                    kind="counterevidence",
                    state="not_applicable" if state == "not_applicable" else "unsupported",
                    evidence_digest=(
                        document.content_digest
                        if document is not None
                        else sha256_digest("selected-report-unavailable")
                    ),
                    description=reason,
                ),
            ),
            non_inferences=self.check_manifest.prohibited_inferences,
            output_ceiling="question_only",
            abstention_reason=reason,
        )


def _number_tokens(text: str) -> list[_NumberToken]:
    tokens: list[_NumberToken] = []
    date_spans = [(item.start(), item.end()) for item in re.finditer(_SLASH_DATE_PATTERN, text)]
    for match in re.finditer(_NUMBER_PATTERN, text):
        if any(start <= match.start(1) < end for start, end in date_spans):
            continue
        raw = match.group(1).replace(",", "")
        trailing = text[match.end(1) :]
        if re.match(_UNIT_SUFFIX_PATTERN, trailing):
            continue
        is_integer = "." not in raw
        decimals = 0 if is_integer else len(raw.split(".", 1)[1])
        tokens.append(
            _NumberToken(
                value=float(raw),
                raw=raw,
                start=match.start(1),
                end=match.end(1),
                is_integer=is_integer,
                decimals=decimals,
                is_percent=re.match(_PERCENT_SUFFIX_PATTERN, trailing) is not None,
            )
        )
    return tokens


def _rate_candidates(token: _NumberToken) -> list[tuple[float, float]]:
    """Candidate (rate, tolerance) pairs for one stated rate token."""

    tolerance = 0.5 * (10.0**-token.decimals)
    if token.is_percent:
        if 0.0 < token.value <= 100.0:
            return [(token.value / 100.0, tolerance / 100.0)]
        return []
    candidates: list[tuple[float, float]] = []
    if 0.0 < token.value <= 1.0:
        candidates.append((token.value, tolerance))
    if 1.0 < token.value <= 100.0:
        candidates.append((token.value / 100.0, tolerance / 100.0))
    return candidates


def _interpretations(
    integers: list[_NumberToken],
    rates: list[_NumberToken],
    *,
    complete_operand: str,
    retained_operand: str,
) -> list[_Interpretation]:
    occurrences: dict[int, list[_NumberToken]] = {}
    for token in integers:
        value = int(token.value)
        if value >= 1:
            occurrences.setdefault(value, []).append(token)
    values = sorted(occurrences)
    interpretations: list[_Interpretation] = []
    for complete_count in values:
        for retained_count in values:
            if not 1 <= retained_count < complete_count:
                continue
            removed_count = complete_count - retained_count
            if removed_count not in occurrences:
                continue
            for event_count in values:
                if not 1 <= event_count <= retained_count:
                    continue
                # Each accounting quantity must be its own stated number: a
                # value reused across roles needs that many distinct token
                # occurrences, so one incidental integer cannot play two
                # roles in a single interpretation.
                quantities = (complete_count, retained_count, removed_count, event_count)
                counts: dict[int, int] = {}
                for value in quantities:
                    counts[value] = counts.get(value, 0) + 1
                if any(len(occurrences[value]) < need for value, need in counts.items()):
                    continue
                subset_ratio = event_count / retained_count
                complete_ratio = event_count / complete_count
                for rate_token in rates:
                    for rate_value, tolerance in _rate_candidates(rate_token):
                        margin = tolerance + 1e-12
                        subset_match = abs(rate_value - subset_ratio) <= margin
                        complete_match = abs(rate_value - complete_ratio) <= margin
                        if subset_match == complete_match:
                            continue
                        used: dict[int, int] = {}
                        count_tokens: list[_NumberToken] = []
                        for value in quantities:
                            count_tokens.append(occurrences[value][used.get(value, 0)])
                            used[value] = used.get(value, 0) + 1
                        interpretations.append(
                            _Interpretation(
                                complete_count=complete_count,
                                retained_count=retained_count,
                                removed_count=removed_count,
                                event_count=event_count,
                                rate_token=rate_token,
                                rate_value=rate_value,
                                operand_value=(
                                    retained_operand if subset_match else complete_operand
                                ),
                                count_tokens=tuple(count_tokens),
                            )
                        )
    return interpretations


def _accounting_present(integers: list[_NumberToken]) -> bool:
    """A stated N = M + K accounting with an event count and distinct tokens."""

    occurrences: dict[int, int] = {}
    for token in integers:
        value = int(token.value)
        if value >= 1:
            occurrences[value] = occurrences.get(value, 0) + 1
    values = sorted(occurrences)
    for complete_count in values:
        for retained_count in values:
            if not 1 <= retained_count < complete_count:
                continue
            removed_count = complete_count - retained_count
            if removed_count not in occurrences:
                continue
            for event_count in values:
                if not 1 <= event_count <= retained_count:
                    continue
                needed: dict[int, int] = {}
                for value in (complete_count, retained_count, removed_count, event_count):
                    needed[value] = needed.get(value, 0) + 1
                if all(occurrences[value] >= need for value, need in needed.items()):
                    return True
    return False


def _corroborating_inventories(
    context: FrozenInspectionContext, selected_path: str
) -> list[dict[int, int]]:
    """Integer-token occurrence counts for every captured document except the report."""

    inventories: list[dict[int, int]] = []
    for item in context.documents:
        if item.path == selected_path:
            continue
        try:
            text = item.content.decode("utf-8")
        except UnicodeDecodeError:
            continue
        inventory: dict[int, int] = {}
        for token in _number_tokens(text):
            if token.is_integer and token.value >= 1:
                value = int(token.value)
                inventory[value] = inventory.get(value, 0) + 1
        if inventory:
            inventories.append(inventory)
    return inventories


def _supports(inventory: dict[int, int], interpretation: _Interpretation) -> bool:
    quantities = (
        interpretation.complete_count,
        interpretation.retained_count,
        interpretation.removed_count,
        interpretation.event_count,
    )
    needed: dict[int, int] = {}
    for value in quantities:
        needed[value] = needed.get(value, 0) + 1
    return all(inventory.get(value, 0) >= need for value, need in needed.items())


def _evidence_span(document: InspectionDocument, text: str, start: int, end: int) -> EvidenceSpan:
    start_line = text.count("\n", 0, start) + 1
    end_line = text.count("\n", 0, end) + 1
    start_column = start - text.rfind("\n", 0, start)
    end_column = end - text.rfind("\n", 0, end)
    assert document.parser_result_ref is not None
    assert document.source_location is not None
    return EvidenceSpan(
        file_ref=document.file_ref,
        path=document.path,
        content_digest=document.source_location.content_digest,
        start_line=start_line + document.line_offset,
        end_line=end_line + document.line_offset,
        start_column=start_column,
        end_column=end_column,
        parser_result_ref=document.parser_result_ref,
    )
