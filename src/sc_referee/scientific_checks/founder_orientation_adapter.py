"""ADR-0069 founder-orientation recognition for the pre-emission orientation check.

This adapter recognizes which founder-allele orientation governs an emission
computation from operations and arithmetic, never from nomenclature. It fuses
two planes.

The reported-text plane reads the selected report's number tokens and looks
for one orientation accounting: a marker total ``N``, a per-marker agreement
count ``E`` stated as its own token, and a stated rate ``r``. When ``r``
reconciles with ``E / N`` the report is consistent with reading the supplied
founder panel directly; when it reconciles with ``(N - E) / N`` the report is
consistent with the complement of that panel. When both reconcile (the
``E = N / 2`` degeneracy) or neither does, the report plane says nothing.
Three free numbers joined by one ratio reconcile by coincidence far more
often than the four numbers of an additive accounting do, so the report plane
also says nothing when more than one ``N`` and ``E`` pair reconciles: a report
stating several candidate accountings identifies none of them.

The source plane is the bounded static resolver in
``founder_orientation_dataflow``: it decides, name-agnostically, whether a
value-inverting involutive transform sits between the staged input read and
exactly one operand of the emission comparison.

Fusion: either plane can resolve alone. A report-only resolution requires the
source plane not to contradict it; a source-only resolution requires the
report to state the marker-total and agreement-count accounting at all. A
unique source classification breaks a report tie. Disagreement between the
planes abstains as ambiguous. Nothing is inferred from unstated quantities,
and no variable, file, or column name gates recognition.
"""

from __future__ import annotations

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
from sc_referee.scientific_checks.founder_orientation_dataflow import (
    FOUNDER_ORIENTATION_DATAFLOW_IMPLEMENTATION_DIGEST,
    founder_orientation_dataflow_grammar,
    resolve_founder_orientation_dataflow,
)
from sc_referee.scientific_checks.quantity_consistency_adapter import _number_tokens
from sc_referee.scientific_checks.scope_joins import selected_publication_path

FOUNDER_ORIENTATION_ADAPTER_IMPLEMENTATION_DIGEST = adapter_implementation_digest(Path(__file__))

_MAX_DISTINCT_INTEGERS = 48
_MAX_RATE_TOKENS = 32

FOUNDER_ORIENTATION_COUNTEREVIDENCE = (
    "bounded-number-token-scan-complete",
    "single-consistent-orientation-reconciliation",
    "alternative-orientation-refuted",
    "selected-surface-identity-complete",
)


@dataclass(frozen=True)
class _Orientation:
    marker_total: int
    agreement_count: int
    rate_raw: str
    rate_value: float
    operand_value: str
    token_spans: tuple[tuple[int, int], ...]


def founder_orientation_recognition_grammar(
    direct_operand: str, repaired_operand: str
) -> dict[str, Any]:
    return {
        "grammar_id": "founder-orientation-reconciliation",
        "grammar_version": "1.0.0",
        "count_source": "integer_tokens_without_unit_or_percent_suffix",
        "rate_source": "decimal_point_or_percent_suffixed_tokens_direct_or_percent_scaled",
        "relations": [
            "1 <= agreement_count < marker_total",
            "the marker total and the agreement count are distinct number-token occurrences",
            "the stated rate reconciles with exactly one of agreement/total or "
            "(total - agreement)/total",
            "the agreement_count == marker_total / 2 degeneracy reconciles with both and is silent",
            "exactly one marker-total and agreement-count pair reconciles in the whole report",
        ],
        "tolerance": "half_unit_in_last_stated_decimal_of_the_rate_token",
        "operand_by_relation": {
            "agreement_over_total": direct_operand,
            "complement_agreement_over_total": repaired_operand,
        },
        "bounds": {
            "max_distinct_integers": _MAX_DISTINCT_INTEGERS,
            "max_rate_tokens": _MAX_RATE_TOKENS,
        },
        "source_dataflow": founder_orientation_dataflow_grammar(direct_operand, repaired_operand),
        "source_dataflow_implementation_digest": (
            FOUNDER_ORIENTATION_DATAFLOW_IMPLEMENTATION_DIGEST
        ),
        "plane_fusion": (
            "either plane resolves alone; a unique source dataflow breaks report "
            "ties; disagreement between planes abstains as ambiguous; a "
            "dataflow-only classification requires a stated marker-total and "
            "agreement-count accounting"
        ),
        "additional_exclusions": ["signed values", "slash-separated dates", "unit-suffixed values"],
        "nomenclature_authority": "none",
    }


def founder_orientation_recognition_grammar_digest(
    direct_operand: str, repaired_operand: str
) -> str:
    return semantic_digest(
        founder_orientation_recognition_grammar(direct_operand, repaired_operand)
    )


@dataclass(frozen=True)
class FounderOrientationReportAdapter:
    """Recognize the founder orientation governing an emission from operations alone."""

    check_manifest: CheckManifest
    adapter_manifest: AdapterManifest
    direct_operand: CanonicalOperand
    repaired_operand: CanonicalOperand
    role_bindings: tuple[RoleBinding, ...]

    @property
    def adapter_id(self) -> str:
        return self.adapter_manifest.adapter_id

    @property
    def adapter_version(self) -> str:
        return self.adapter_manifest.adapter_version

    @property
    def implementation_digest(self) -> str:
        return FOUNDER_ORIENTATION_ADAPTER_IMPLEMENTATION_DIGEST

    @property
    def recognition_grammar_digest(self) -> str:
        return founder_orientation_recognition_grammar_digest(
            str(self.direct_operand.value), str(self.repaired_operand.value)
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
        interpretations, report_had_conflict = _identified_orientations(
            integers,
            rates,
            direct_operand=str(self.direct_operand.value),
            repaired_operand=str(self.repaired_operand.value),
        )
        report_operands = sorted({item.operand_value for item in interpretations})
        flow = resolve_founder_orientation_dataflow(
            context,
            direct_operand=str(self.direct_operand.value),
            repaired_operand=str(self.repaired_operand.value),
            parser_id=PYTHON_PARSER_ID,
            parser_version=PYTHON_PARSER_VERSION,
        )
        if flow.state == "ambiguous":
            return self._abstain(
                "ambiguous",
                (
                    "The workflow source computes emission comparisons under conflicting "
                    "founder-panel orientations."
                ),
                document=document,
            )
        if len(report_operands) > 1:
            # The only tie-break is a unique source-dataflow classification: a
            # coincidental reconciliation reuses report numbers in two roles,
            # and nomenclature still plays no part.
            if flow.state == "unique":
                interpretations = [
                    item for item in interpretations if item.operand_value == flow.operand_value
                ]
            report_operands = sorted({item.operand_value for item in interpretations})
        if len(report_operands) > 1:
            return self._abstain(
                "ambiguous",
                (
                    "The stated quantities reconcile with both founder-panel orientations "
                    "and the workflow dataflow does not resolve exactly one."
                ),
                document=document,
            )
        if report_operands and flow.state == "unique" and report_operands[0] != flow.operand_value:
            return self._abstain(
                "ambiguous",
                (
                    "The report arithmetic and the workflow-source dataflow disagree on the "
                    "founder-panel orientation the emission uses."
                ),
                document=document,
            )
        if (
            not report_operands
            and flow.state == "unique"
            and not _accounting_present(integers, rates)
        ):
            # The dataflow plane alone may classify only when the report states
            # a marker-total and agreement-count accounting; without one, an
            # ordinary comparison loop could otherwise fire on clean work.
            return self._abstain(
                "not_applicable",
                (
                    "The workflow dataflow resolves a founder-panel orientation, but the "
                    "selected report states no marker-total and agreement-count accounting."
                ),
                document=document,
            )
        if not report_operands and flow.state != "unique":
            if report_had_conflict:
                return self._abstain(
                    "ambiguous",
                    (
                        "The stated quantities reconcile with both founder-panel orientations "
                        "and no tie-break resolves exactly one."
                    ),
                    document=document,
                )
            if flow.state == "unsupported":
                return self._abstain(
                    "unsupported",
                    (
                        "No reconcilable report accounting exists and the workflow source "
                        "uses transforms or control flow beyond the supported dataflow trace."
                    ),
                    document=document,
                )
            return self._abstain(
                "not_applicable",
                (
                    "Neither the selected report's quantities nor the workflow source's "
                    "dataflow states a founder-panel orientation for an emission comparison."
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
            self.repaired_operand
            if operand_value == str(self.repaired_operand.value)
            else self.direct_operand
        )
        chosen = interpretations[0] if interpretations else None
        report_spans = (
            tuple(
                _evidence_span(document, text, start, end)
                for start, end in sorted(chosen.token_spans)
            )
            if chosen is not None
            else ()
        )
        spans = report_spans + (flow.spans if flow.state == "unique" else ())
        if chosen is not None:
            role_bindings = (
                RoleBinding("founder_allele_input", f"stated_marker_total:{chosen.marker_total}"),
                RoleBinding(
                    "hmm_emission", f"stated_per_marker_agreement_count:{chosen.agreement_count}"
                ),
                RoleBinding("orientation_step", f"reconciled_rate_token:{chosen.rate_raw}"),
            )
        else:
            role_bindings = (
                RoleBinding("founder_allele_input", f"staged_panel_column_read:{flow.source_path}"),
                RoleBinding(
                    "hmm_emission",
                    "row_column_equality_selecting_emission_probabilities",
                ),
                RoleBinding(
                    "orientation_step",
                    "involutive_recode_on_one_comparison_operand_path"
                    if flow.orientation == "repaired"
                    else "identity_path_on_both_comparison_operands",
                ),
            )
        reconciliation: dict[str, Any] = {"basis": basis, "operand": operand_value}
        if chosen is not None:
            reconciliation.update(
                {
                    "marker_total": chosen.marker_total,
                    "agreement_count": chosen.agreement_count,
                    "rate_token": chosen.rate_raw,
                }
            )
        if flow.state == "unique":
            reconciliation["source_path"] = flow.source_path
            reconciliation["source_orientation"] = flow.orientation
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


def _rate_candidates(token: Any) -> list[tuple[float, float]]:
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


def _orientations(
    integers: list[Any],
    rates: list[Any],
    *,
    direct_operand: str,
    repaired_operand: str,
) -> list[_Orientation]:
    """Every reconciliation of a stated rate with one founder-panel orientation."""

    occurrences: dict[int, list[Any]] = {}
    for token in integers:
        value = int(token.value)
        if value >= 1:
            occurrences.setdefault(value, []).append(token)
    values = sorted(occurrences)
    found: list[_Orientation] = []
    for marker_total in values:
        for agreement_count in values:
            if not 1 <= agreement_count < marker_total:
                continue
            direct_ratio = agreement_count / marker_total
            complement_ratio = (marker_total - agreement_count) / marker_total
            for rate_token in rates:
                for rate_value, tolerance in _rate_candidates(rate_token):
                    margin = tolerance + 1e-12
                    direct_match = abs(rate_value - direct_ratio) <= margin
                    complement_match = abs(rate_value - complement_ratio) <= margin
                    if direct_match == complement_match:
                        # Both reconcile at the agreement == total / 2
                        # degeneracy, and neither reconciles otherwise.
                        continue
                    found.append(
                        _Orientation(
                            marker_total=marker_total,
                            agreement_count=agreement_count,
                            rate_raw=rate_token.raw,
                            rate_value=rate_value,
                            operand_value=(direct_operand if direct_match else repaired_operand),
                            token_spans=(
                                (
                                    occurrences[marker_total][0].start,
                                    occurrences[marker_total][0].end,
                                ),
                                (
                                    occurrences[agreement_count][0].start,
                                    occurrences[agreement_count][0].end,
                                ),
                                (rate_token.start, rate_token.end),
                            ),
                        )
                    )
    return found


def _identified_orientations(
    integers: list[Any],
    rates: list[Any],
    *,
    direct_operand: str,
    repaired_operand: str,
) -> tuple[list[_Orientation], bool]:
    """The reconciliations a report identifies, and whether they conflict.

    Three free numbers joined by one ratio reconcile by coincidence far more
    often than the four numbers of an additive accounting do, so a report
    stating more than one reconciling marker-total and agreement-count pair
    identifies none of them.
    """

    found = _orientations(
        integers, rates, direct_operand=direct_operand, repaired_operand=repaired_operand
    )
    conflicted = len({item.operand_value for item in found}) > 1
    if len({(item.marker_total, item.agreement_count) for item in found}) > 1:
        return [], conflicted
    return found, conflicted


def _accounting_present(integers: list[Any], rates: list[Any]) -> bool:
    """A stated marker total, a smaller stated agreement count, and a stated rate."""

    if not rates:
        return False
    values = sorted({int(token.value) for token in integers if token.value >= 1})
    return len(values) >= 2 and values[-1] > values[0] >= 1


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
