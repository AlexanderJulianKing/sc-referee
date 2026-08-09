"""Shadow v3 adapter for proof-producing founder-orientation recognition.

The frozen v2 adapter remains registered unchanged.  This adapter emits an
independent observation from the semantic certificate kernel.  The registry's
ordinary multi-adapter reduction is the shadow fusion boundary: disagreement
is ``ambiguous`` and no adapter votes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.parsers.python_ast import PARSER_ID as PYTHON_PARSER_ID
from sc_referee.parsers.python_ast import PARSER_VERSION as PYTHON_PARSER_VERSION
from sc_referee.scientific_checks.adapter_common import (
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
from sc_referee.scientific_checks.founder_orientation_adapter import (
    _identified_orientations,
    _orientations,
)
from sc_referee.scientific_checks.founder_orientation_semantic import (
    FOUNDER_ORIENTATION_SEMANTIC_IMPLEMENTATION_DIGEST,
    founder_orientation_semantic_grammar,
    resolve_founder_orientation_semantic,
)
from sc_referee.scientific_checks.quantity_consistency_adapter import _number_tokens
from sc_referee.scientific_checks.scope_joins import selected_publication_path

_HERE = Path(__file__).resolve().parent
_SEMANTIC_DEPENDENCY_FILES = (
    "founder_orientation_semantic_adapter.py",
    "founder_orientation_semantic.py",
    "founder_orientation_certificate.py",
    "founder_orientation_semantic_ir.py",
    "founder_orientation_adapter.py",
    "founder_orientation_dataflow.py",
    "quantity_consistency_adapter.py",
)


def founder_orientation_semantic_dependency_closure() -> dict[str, str]:
    """Every source file whose semantics can affect a v3 observation."""

    return {
        f"scientific_checks/{name}": sha256_digest((_HERE / name).read_bytes())
        for name in _SEMANTIC_DEPENDENCY_FILES
    }


FOUNDER_ORIENTATION_SEMANTIC_ADAPTER_IMPLEMENTATION_DIGEST = semantic_digest(
    {"dependency_closure": founder_orientation_semantic_dependency_closure()}
)

FOUNDER_ORIENTATION_SEMANTIC_COUNTEREVIDENCE = (
    "semantic-certificate-kernel-accepted",
    "report-reaching-comparison-set-complete",
    "relevant-opaque-effects-refuted",
    "shadow-adapter-source-report-fusion-complete",
)

_MAX_DISTINCT_INTEGERS = 48
_MAX_RATE_TOKENS = 32


def founder_orientation_semantic_recognition_grammar(
    direct_operand: str, repaired_operand: str
) -> dict[str, Any]:
    return {
        "grammar_id": "founder-orientation-semantic-shadow-fusion",
        "grammar_version": "3.0.0",
        "semantic_source": founder_orientation_semantic_grammar(direct_operand, repaired_operand),
        "semantic_source_implementation_digest": (
            FOUNDER_ORIENTATION_SEMANTIC_IMPLEMENTATION_DIGEST
        ),
        "implementation_dependency_closure": founder_orientation_semantic_dependency_closure(),
        "report_plane": (
            "the frozen bounded N/E/r reconciliation corroborates or contradicts but never "
            "classifies without an accepted source certificate"
        ),
        "shadow_fusion": (
            "v2 and v3 produce independent observations; different applicable operands or "
            "an explicit ambiguity reduce to ambiguity; no voting or precedence"
        ),
        "nomenclature_authority": "none",
    }


def founder_orientation_semantic_recognition_grammar_digest(
    direct_operand: str, repaired_operand: str
) -> str:
    return semantic_digest(
        founder_orientation_semantic_recognition_grammar(direct_operand, repaired_operand)
    )


@dataclass(frozen=True)
class FounderOrientationSemanticReportAdapter:
    """Fuse a verified v3 source certificate with bounded report arithmetic."""

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
        return FOUNDER_ORIENTATION_SEMANTIC_ADAPTER_IMPLEMENTATION_DIGEST

    @property
    def recognition_grammar_digest(self) -> str:
        return founder_orientation_semantic_recognition_grammar_digest(
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
                "unsupported", "The selected report is not strict UTF-8 text.", document=document
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
        direct = str(self.direct_operand.value)
        repaired = str(self.repaired_operand.value)
        reconciliations = _orientations(
            integers, rates, direct_operand=direct, repaired_operand=repaired
        )
        interpretations, _report_had_conflict = _identified_orientations(
            integers, rates, direct_operand=direct, repaired_operand=repaired
        )
        report_operands = sorted({item.operand_value for item in interpretations})
        if not report_operands and not reconciliations:
            return self._abstain(
                "not_applicable",
                "The selected report states no bounded founder-orientation accounting.",
                document=document,
            )
        flow = resolve_founder_orientation_semantic(
            context,
            direct_operand=direct,
            repaired_operand=repaired,
            parser_id=PYTHON_PARSER_ID,
            parser_version=PYTHON_PARSER_VERSION,
        )
        if flow.state == "ambiguous":
            return self._abstain(
                "ambiguous",
                "The verified semantic certificates disagree on the report-reaching orientation.",
                document=document,
            )
        if flow.state == "unsupported":
            return self._abstain(
                "unsupported",
                "No complete founder-orientation semantic certificate survived the trusted kernel.",
                document=document,
            )
        if flow.state != "unique":
            return self._abstain(
                "not_applicable",
                "No report-reaching staged-column emission comparison was certified.",
                document=document,
            )
        if len(report_operands) == 1 and report_operands[0] != flow.operand_value:
            return self._abstain(
                "ambiguous",
                "The report arithmetic and the v3 semantic certificate disagree.",
                document=document,
            )
        corroborated = len(report_operands) == 1
        if not corroborated and not any(
            item.operand_value == flow.operand_value for item in reconciliations
        ):
            return self._abstain(
                "not_applicable",
                "The source certificate is complete, but the selected report states no bounded "
                "accounting that reconciles with it.",
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
                "The selected report Artifact is not owned by the resolved PublicationSurface.",
                document=document,
            )
        operand_value = flow.operand_value
        operand = self.repaired_operand if operand_value == repaired else self.direct_operand
        chosen = interpretations[0] if corroborated else None
        report_spans = (
            tuple(
                _evidence_span(document, text, start, end)
                for start, end in sorted(chosen.token_spans)
            )
            if chosen is not None
            else ()
        )
        spans = report_spans + flow.spans
        role_bindings = (
            RoleBinding("founder_allele_input", f"staged_panel_column_read:{flow.source_path}"),
            RoleBinding("hmm_emission", "verified_report_reaching_selector_fold"),
            RoleBinding(
                "orientation_step",
                "verified_odd_projection_parity"
                if flow.orientation == "repaired"
                else "verified_even_projection_parity",
            ),
        )
        reconciliation = {
            "basis": (
                "semantic_certificate_and_report_arithmetic"
                if corroborated
                else "semantic_certificate"
            ),
            "operand": operand_value,
            "source_path": flow.source_path,
            "source_orientation": flow.orientation,
            "certificate_comparisons": (
                list(flow.certificate.comparison_tokens) if flow.certificate else []
            ),
            "certificate_selectors": (
                list(flow.certificate.selector_tokens) if flow.certificate else []
            ),
            "certificate_folds": list(flow.certificate.fold_tokens) if flow.certificate else [],
        }
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
