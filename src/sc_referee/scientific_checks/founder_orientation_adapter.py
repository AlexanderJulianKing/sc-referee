"""ADR-0069 founder-orientation recognition for the pre-emission orientation check.

This adapter recognizes which founder-allele orientation governs an emission
computation from operations and arithmetic, never from nomenclature. It reads
two planes, but only one of them can decide.

The source plane is the bounded static resolver in
``founder_orientation_dataflow``: it decides, name-agnostically, whether a
value-inverting involutive transform sits between the staged input read and
exactly one operand of the emission comparison. This plane is the only one
that resolves. When it does not resolve uniquely the adapter abstains, in the
resolver's own terms: nothing seen at all is not applicable, an unreadable
transform or untraceable control flow is unsupported, and workflow
comparisons that disagree with each other are ambiguous.

The reported-text plane reads the selected report's number tokens and looks
for one orientation accounting: a marker total ``N``, a per-marker agreement
count ``E`` stated as its own token, and a stated rate ``r``. When ``r``
reconciles with ``E / N`` the report is consistent with reading the supplied
founder panel directly; when it reconciles with ``(N - E) / N`` the report is
consistent with the complement of that panel. Three free numbers joined by
one ratio reconcile by coincidence often enough that this plane cannot carry
a classification by itself: a sensitivity of 0.90 on 90 of 100 cases is an
ordinary sentence about something else entirely, and it reconciles just as
well as a genuine founder accounting does. So the report plane has three jobs
and no more. It corroborates when its own unique reading agrees with the
workflow, it contradicts when its unique reading disagrees, and otherwise it
is silent.

From v2.1.0 the source plane is default-deny: it models an explicit whitelist
of statement and expression forms, and any form outside that whitelist
anywhere in the workflow leaves the document unsupported. A second
adversarial review of v2.0.1 demonstrated thirteen ordinary workflows -- alias
mutation through a parameter, a container, a comprehension target and a
closure, a ``match`` guard, a walrus inside a ``print``, a higher-order
parameter, a duplicated definition, a ``functools.reduce``, a write inside an
uncalled function, a path name rebound to a buffer, and an imported helper
named ``reader`` -- where this adapter returned an applicable orientation
opposite to what the workflow computes at run time. Each of them was an
unlisted form the old deny-list waved through.

v2.2.0 widens the source plane by five narrow forms without touching that
trust model: a path ``read_text().splitlines()`` chain feeding a ``csv``
reader, module-level names assigned once to a literal, a ``zip`` pairing of
two single-assignment column-values lists of one named row set, the
arithmetic-encoded selector ``A + (B - A) * FLAG``, and a two-parameter
helper that binds its comparison to one local before returning the selector.
Each is modelled in one exact shape, and anything outside that shape abstains
exactly as it did in v2.1.5.

v2.2.2 widens it by four more on the same terms: ``dict(row)`` as the identity
row rebuild, ``close()`` on a file handle the modelled ``open()`` bound, a
one-parameter helper that extracts one column of the row it is handed, and
the multiply-complement selector ``A * FLAG + B * (1 - FLAG)``.

v2.2.3 widens it by ten more, again one exact shape each: exact-numeric module
constants in selector branches, helper parameters proven path-like at their
call sites, ``.splitlines()`` on a name holding a ``read_text`` result, a bare
``mkdir()``, a report write routed through a two-parameter helper, an
elementwise recode of a column-values list, the ``range(len(...))`` spelling of
a ``zip`` pairing, accumulation loops that consume a list the way ``sum`` does,
and ``print`` with ``sep``, ``end``, or ``flush``.

v2.2.5 widens it by four more: a per-scope single-assignment count, so a
helper's own parameter or local no longer costs the module a pairable list;
a selector helper that casts its flag and holds one further constant-derived
local; a report-write helper whose body creates the directory, writes once,
echoes, and returns the size; and ``[A[i] * S[i] for i in range(N)]``, the
selector-weighted column product, whose accumulation reads the selectors that
list multiplied.

Even a silent report has to account for the workflow's reading: the adapter
classifies on the dataflow alone only when some stated marker total,
agreement count, and rate reconcile in the direction the workflow computed.
A report that states no such accounting leaves the question not applicable,
because nothing published turns on the orientation the workflow used.

Nothing is inferred from unstated quantities, and no variable, file, or
column name gates recognition.
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
        "grammar_version": "2.2.6",
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
            "only the source dataflow resolves; the report plane corroborates a "
            "unique dataflow reading, contradicts it as ambiguous, or is silent; "
            "a non-unique dataflow abstains in the resolver's own terms; a "
            "dataflow-only classification requires a stated marker-total, "
            "agreement-count, and rate accounting that reconciles in the "
            "direction the dataflow computed"
        ),
        "source_trust_model": (
            "default deny: the source plane models an explicit whitelist of "
            "statement and expression forms, and any form outside it anywhere in "
            "the workflow leaves the document unsupported, so the report plane "
            "never sees a reading the trace could not fully account for"
        ),
        "source_parse_guard": (
            "a source the parser cannot finish reading, including one that "
            "exhausts the interpreter stack or memory, abstains as unsupported"
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
        reconciliations = _orientations(
            integers,
            rates,
            direct_operand=str(self.direct_operand.value),
            repaired_operand=str(self.repaired_operand.value),
        )
        interpretations, _report_had_conflict = _identified_orientations(
            integers,
            rates,
            direct_operand=str(self.direct_operand.value),
            repaired_operand=str(self.repaired_operand.value),
        )
        report_operands = sorted({item.operand_value for item in interpretations})
        try:
            flow = resolve_founder_orientation_dataflow(
                context,
                direct_operand=str(self.direct_operand.value),
                repaired_operand=str(self.repaired_operand.value),
                parser_id=PYTHON_PARSER_ID,
                parser_version=PYTHON_PARSER_VERSION,
            )
        except (RecursionError, MemoryError, OverflowError):
            # The resolver guards its own parsing, but a source deep or large
            # enough to exhaust the stack or memory anywhere in the trace is an
            # abstention at this boundary too, never a crashed inspection.
            return self._abstain(
                "unsupported",
                (
                    "The workflow source could not be read within the bounded static "
                    "trace's stack and memory limits."
                ),
                document=document,
            )
        # The report plane never resolves alone. Report numbers reconcile with
        # an orientation ratio by coincidence far too readily for three free
        # numbers to carry a classification, so a dataflow that does not
        # resolve uniquely ends the inspection in the resolver's own terms.
        if flow.state == "ambiguous":
            return self._abstain(
                "ambiguous",
                (
                    "The workflow source computes emission comparisons under conflicting "
                    "founder-panel orientations."
                ),
                document=document,
            )
        if flow.state == "unsupported":
            return self._abstain(
                "unsupported",
                (
                    "The workflow source uses transforms or control flow beyond the supported "
                    "dataflow trace, and the report arithmetic cannot stand in for it."
                ),
                document=document,
            )
        if flow.state != "unique":
            return self._abstain(
                "not_applicable",
                (
                    "The workflow source states no emission comparison whose founder-panel "
                    "orientation this trace resolves."
                ),
                document=document,
            )
        if len(report_operands) == 1 and report_operands[0] != flow.operand_value:
            return self._abstain(
                "ambiguous",
                (
                    "The report arithmetic and the workflow-source dataflow disagree on the "
                    "founder-panel orientation the emission uses."
                ),
                document=document,
            )
        corroborated = len(report_operands) == 1
        if not corroborated and not any(
            item.operand_value == flow.operand_value for item in reconciliations
        ):
            # A resolved workflow orientation is reviewable only when the
            # report states an accounting that reconciles with it; without
            # one, nothing published turns on the orientation.
            return self._abstain(
                "not_applicable",
                (
                    "The workflow dataflow resolves a founder-panel orientation, but the "
                    "selected report states no marker-total, agreement-count, and rate "
                    "accounting that reconciles with it."
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
        operand_value = flow.operand_value
        basis = "report_arithmetic_and_source_dataflow" if corroborated else "source_dataflow"
        operand = (
            self.repaired_operand
            if operand_value == str(self.repaired_operand.value)
            else self.direct_operand
        )
        chosen = interpretations[0] if corroborated else None
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
