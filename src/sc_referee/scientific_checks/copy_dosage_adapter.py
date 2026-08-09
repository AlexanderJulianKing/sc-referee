"""ADR-0069 copy-dosage representation recognition from operations and arithmetic.

This adapter recognizes which calibrated copy-number representation supplies
the quantitative exposure of a reported model, from operations and
arithmetic, never from nomenclature. It reads two planes, but only one of
them can decide.

The source plane is the bounded static resolver in ``copy_dosage_dataflow``:
it decides, name-agnostically, whether the value reaching the exposure
operand of a report-reaching fit is confined to a finite set of literal
values, is a posterior expectation over ordered copy states, or is a direct
continuous calibration prediction. This plane is the only one that resolves.
When it does not resolve uniquely the adapter abstains, in the resolver's own
terms: nothing seen at all is not applicable, an unreadable step or
untraceable control flow is unsupported, and fits that disagree with each
other are ambiguous.

The reported-text plane reads the selected report's number tokens and looks
for one hard-state accounting: per-state counts ``n0``, ``n1``, and ``n2``,
a cohort total ``N`` with ``N == n0 + n1 + n2``, and a stated mean dosage
``m`` with ``m * N == n1 + 2 * n2`` inside half a unit of the mean's last
stated decimal. Only an integer-valued dosage can be tabulated that way, so
such an accounting is evidence for the hard-state representation. Four free
numbers joined by two relations still reconcile by coincidence often enough
that this plane cannot carry a classification by itself, so it gets three
jobs and no more. It corroborates when its own unique reading agrees with
the workflow, it contradicts when it disagrees, and otherwise it is silent.
A stated standard deviation that reconciles with the same accounting is
recorded as a third point of support; it never changes the decision.

Nothing is inferred from unstated quantities, and no variable, file, or
column name gates recognition.
"""

from __future__ import annotations

import math
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
from sc_referee.scientific_checks.copy_dosage_dataflow import (
    COPY_DOSAGE_DATAFLOW_IMPLEMENTATION_DIGEST,
    copy_dosage_dataflow_grammar,
    resolve_copy_dosage_dataflow,
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
from sc_referee.scientific_checks.quantity_consistency_adapter import _number_tokens
from sc_referee.scientific_checks.scope_joins import selected_publication_path

COPY_DOSAGE_ADAPTER_IMPLEMENTATION_DIGEST = adapter_implementation_digest(Path(__file__))

_MAX_DISTINCT_INTEGERS = 48
_MAX_RATE_TOKENS = 32
_MAX_ACCOUNTINGS = 4096
# The ordered copy states ADR-0024 names. A hard-state accounting tabulates a
# count for each of them.
_COPY_STATES = (0, 1, 2)

COPY_DOSAGE_COUNTEREVIDENCE = (
    "bounded-number-token-scan-complete",
    "single-consistent-representation-resolution",
    "alternative-copy-representation-refuted",
    "selected-surface-identity-complete",
)

_STATE_QUANTIZED = "integer_hard_state"


@dataclass(frozen=True)
class _Accounting:
    """One stated per-state count table with its reconciling mean."""

    counts: tuple[int, ...]
    total: int
    mean_raw: str
    mean_value: float
    sd_raw: str | None
    token_spans: tuple[tuple[int, int], ...]


def copy_dosage_recognition_grammar(
    hard_operand: str, expectation_operand: str, calibration_operand: str
) -> dict[str, Any]:
    return {
        "grammar_id": "copy-dosage-representation-reconciliation",
        "grammar_version": "2.0.2",
        "count_source": "integer_tokens_without_unit_or_percent_suffix",
        "mean_source": "decimal_point_tokens_without_percent_suffix",
        "copy_states": list(_COPY_STATES),
        "relations": [
            "total == n0 + n1 + n2",
            "at least two of the per-state counts are non-zero",
            "the per-state counts and the total are distinct number-token occurrences",
            "the stated mean reconciles with (n1 + 2 * n2) / total",
            "exactly one per-state accounting reconciles in the whole report",
            "a stated standard deviation reconciling with the same accounting is "
            "recorded as additional support and never decides",
        ],
        "tolerance": "half_unit_in_last_stated_decimal_of_the_mean_token",
        "operand_by_relation": {"stated_per_state_accounting": hard_operand},
        "bounds": {
            "max_distinct_integers": _MAX_DISTINCT_INTEGERS,
            "max_rate_tokens": _MAX_RATE_TOKENS,
            "max_accountings": _MAX_ACCOUNTINGS,
        },
        "source_dataflow": copy_dosage_dataflow_grammar(
            hard_operand, expectation_operand, calibration_operand
        ),
        "source_dataflow_implementation_digest": COPY_DOSAGE_DATAFLOW_IMPLEMENTATION_DIGEST,
        "plane_fusion": (
            "only the source dataflow resolves; the report plane corroborates a "
            "quantized dataflow reading, contradicts any reading as ambiguous, or "
            "is silent; a non-unique dataflow abstains in the resolver's own terms"
        ),
        "contract_operand_distinctness": (
            "the three contract operand strings must be pairwise distinct; a contract "
            "that names one operand twice cannot say which representation a resolved "
            "reading reports, so the adapter abstains as unsupported"
        ),
        "additional_exclusions": ["signed values", "slash-separated dates", "unit-suffixed values"],
        "nomenclature_authority": "none",
    }


def copy_dosage_recognition_grammar_digest(
    hard_operand: str, expectation_operand: str, calibration_operand: str
) -> str:
    return semantic_digest(
        copy_dosage_recognition_grammar(hard_operand, expectation_operand, calibration_operand)
    )


@dataclass(frozen=True)
class CopyDosageReportAdapter:
    """Recognize the copy-dosage exposure representation from operations alone."""

    check_manifest: CheckManifest
    adapter_manifest: AdapterManifest
    hard_operand: CanonicalOperand
    expectation_operand: CanonicalOperand
    calibration_operand: CanonicalOperand
    role_bindings: tuple[RoleBinding, ...]

    @property
    def adapter_id(self) -> str:
        return self.adapter_manifest.adapter_id

    @property
    def adapter_version(self) -> str:
        return self.adapter_manifest.adapter_version

    @property
    def implementation_digest(self) -> str:
        return COPY_DOSAGE_ADAPTER_IMPLEMENTATION_DIGEST

    @property
    def recognition_grammar_digest(self) -> str:
        return copy_dosage_recognition_grammar_digest(*self._operand_values)

    @property
    def _operand_values(self) -> tuple[str, str, str]:
        return (
            str(self.hard_operand.value),
            str(self.expectation_operand.value),
            str(self.calibration_operand.value),
        )

    def inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        try:
            return self._inspect(context)
        except (RecursionError, MemoryError, OverflowError):
            # A report or a workflow source too deep or too large for the
            # bounded scans abstains in this adapter's own terms. Letting it
            # reach the registry's generic guard would report a crash where
            # the honest answer is an unsupported coverage record.
            return self._abstain(
                "unsupported",
                "The selected report or workflow source exceeds the bounded scans.",
            )

    def _inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        if len(set(self._operand_values)) != len(self._operand_values):
            # The three operands are how a resolved reading is reported. A
            # contract that spells two of them the same way cannot say which
            # representation a resolved reading names, and picking either one
            # would report a representation the trace did not resolve.
            return self._abstain(
                "unsupported",
                (
                    "The frozen contract's three copy-dosage operand values are not "
                    "pairwise distinct, so a resolved representation cannot be reported."
                ),
            )
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
        decimals = [item for item in tokens if not item.is_integer and not item.is_percent]
        if len({int(item.value) for item in integers}) > _MAX_DISTINCT_INTEGERS:
            return self._abstain(
                "unsupported",
                "The selected report exceeds the bounded distinct-integer scan.",
                document=document,
            )
        if len([item for item in tokens if not item.is_integer or item.is_percent]) > (
            _MAX_RATE_TOKENS
        ):
            return self._abstain(
                "unsupported",
                "The selected report exceeds the bounded rate-token scan.",
                document=document,
            )
        accountings = _accountings(integers, decimals)
        if accountings is None:
            return self._abstain(
                "unsupported",
                "The selected report exceeds the bounded per-state accounting scan.",
                document=document,
            )
        identified = _identified_accounting(accountings)
        hard, expectation, calibration = self._operand_values
        flow = resolve_copy_dosage_dataflow(
            context,
            hard_operand=hard,
            expectation_operand=expectation,
            calibration_operand=calibration,
            parser_id=PYTHON_PARSER_ID,
            parser_version=PYTHON_PARSER_VERSION,
        )
        # The report plane never resolves alone. A per-state count table plus a
        # stated mean reconciles by coincidence readily enough that it cannot
        # carry a classification, so a dataflow that does not resolve uniquely
        # ends the inspection in the resolver's own terms.
        if flow.state == "ambiguous":
            return self._abstain(
                "ambiguous",
                (
                    "The workflow source supplies conflicting copy-dosage representations to "
                    "report-reaching model fits."
                ),
                document=document,
            )
        if flow.state == "unsupported":
            return self._abstain(
                "unsupported",
                (
                    "The workflow source uses steps or control flow beyond the supported "
                    "dataflow trace, and the report arithmetic cannot stand in for it."
                ),
                document=document,
            )
        if flow.state != "unique":
            return self._abstain(
                "not_applicable",
                (
                    "The workflow source states no model fit whose copy-dosage exposure "
                    "representation this trace resolves."
                ),
                document=document,
            )
        corroborated = identified is not None and flow.representation == _STATE_QUANTIZED
        if identified is not None and not corroborated:
            return self._abstain(
                "ambiguous",
                (
                    "The report states a per-state hard-call accounting for the dosage while "
                    "the workflow-source dataflow supplies a continuous exposure."
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
        operand_value = str(flow.operand_value)
        operand = {
            hard: self.hard_operand,
            expectation: self.expectation_operand,
            calibration: self.calibration_operand,
        }[operand_value]
        basis = "report_arithmetic_and_source_dataflow" if corroborated else "source_dataflow"
        chosen = identified if corroborated else None
        report_spans = (
            tuple(
                _evidence_span(document, text, start, end)
                for start, end in sorted(chosen.token_spans)
            )
            if chosen is not None
            else ()
        )
        spans = report_spans + flow.spans
        role_bindings = _role_bindings(flow, chosen)
        reconciliation: dict[str, Any] = {
            "basis": basis,
            "operand": operand_value,
            "source_representation": flow.representation,
            "source_path": flow.source_path,
        }
        if flow.operation is not None:
            reconciliation["exposure_operation"] = flow.operation
        if chosen is not None:
            reconciliation.update(
                {
                    "state_counts": list(chosen.counts),
                    "cohort_total": chosen.total,
                    "mean_token": chosen.mean_raw,
                    "standard_deviation_token": chosen.sd_raw,
                }
            )
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


def _role_bindings(flow: Any, chosen: _Accounting | None) -> tuple[RoleBinding, ...]:
    calibration_output = {
        "integer_hard_state": "finite_valued_copy_state_assignment",
        "posterior_expectation": "class_probability_matrix_over_ordered_copy_states",
        "direct_calibration": "continuous_calibration_prediction",
    }[str(flow.representation)]
    exposure = (
        f"quantizing_operation_on_the_exposure_path:{flow.operation}"
        if flow.representation == _STATE_QUANTIZED and flow.operation
        else f"continuous_exposure_path:{flow.representation}"
    )
    dosage = (
        f"stated_per_state_accounting:{'/'.join(str(item) for item in chosen.counts)}"
        f"_of_{chosen.total}_mean_{chosen.mean_raw}"
        if chosen is not None
        else f"traced_exposure_operand:{flow.source_path}"
    )
    return (
        RoleBinding("copy_state_calibration_labels", "ordered_integer_copy_states"),
        RoleBinding("calibration_model_output", calibration_output),
        RoleBinding("quantitative_copy_dosage", dosage),
        RoleBinding("downstream_model_exposure", exposure),
    )


def _accountings(integers: list[Any], decimals: list[Any]) -> list[_Accounting] | None:
    """Every reconciliation of a stated per-state count table with a stated mean.

    Returns ``None`` when the bounded enumeration would exceed its ceiling.
    """

    occurrences: dict[int, list[Any]] = {}
    for token in integers:
        value = int(token.value)
        if value >= 0:
            occurrences.setdefault(value, []).append(token)
    values = sorted(occurrences)
    found: list[_Accounting] = []
    for total in values:
        if total < len(_COPY_STATES):
            continue
        for first in values:
            if first > total:
                continue
            for second in values:
                third = total - first - second
                if third < 0 or third not in occurrences:
                    continue
                counts = (first, second, third)
                if sum(1 for item in counts if item > 0) < 2:
                    continue
                # Each accounting quantity must be its own stated number: a
                # value reused across roles needs that many distinct token
                # occurrences, so one incidental integer cannot play two roles.
                needed: dict[int, int] = {}
                for value in (*counts, total):
                    needed[value] = needed.get(value, 0) + 1
                if any(len(occurrences[value]) < need for value, need in needed.items()):
                    continue
                weighted = sum(
                    state * count for state, count in zip(_COPY_STATES, counts, strict=True)
                )
                mean = weighted / total
                variance = (
                    sum(
                        count * (state - mean) ** 2
                        for state, count in zip(_COPY_STATES, counts, strict=True)
                    )
                    / total
                )
                for token in decimals:
                    tolerance = 0.5 * (10.0**-token.decimals) + 1e-12
                    if abs(token.value - mean) > tolerance:
                        continue
                    used: dict[int, int] = {}
                    count_tokens: list[Any] = []
                    for value in (*counts, total):
                        count_tokens.append(occurrences[value][used.get(value, 0)])
                        used[value] = used.get(value, 0) + 1
                    found.append(
                        _Accounting(
                            counts=counts,
                            total=total,
                            mean_raw=token.raw,
                            mean_value=token.value,
                            sd_raw=_supporting_deviation(decimals, token, variance),
                            token_spans=(
                                *((item.start, item.end) for item in count_tokens),
                                (token.start, token.end),
                            ),
                        )
                    )
                    if len(found) > _MAX_ACCOUNTINGS:
                        return None
    return found


def _supporting_deviation(decimals: list[Any], mean_token: Any, variance: float) -> str | None:
    """A stated standard deviation that reconciles with the same accounting."""

    deviation = math.sqrt(variance)
    for token in decimals:
        if token is mean_token:
            continue
        tolerance = 0.5 * (10.0**-token.decimals) + 1e-12
        if abs(token.value - deviation) <= tolerance:
            return str(token.raw)
    return None


def _identified_accounting(accountings: list[_Accounting]) -> _Accounting | None:
    """The one accounting a report identifies, or nothing.

    A report stating more than one reconciling per-state table identifies none
    of them: the second table is evidence that the numbers reconcile by
    coincidence.
    """

    if not accountings:
        return None
    if len({(item.counts, item.total) for item in accountings}) > 1:
        return None
    return accountings[0]


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
