from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from sc_referee.core.ids import semantic_digest, sha256_digest
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
    ScopeJoinEdge,
)

SELECTED_REPORT_ADAPTER_IMPLEMENTATION_DIGEST = adapter_implementation_digest(Path(__file__))


@dataclass(frozen=True)
class ReportOperandRule:
    operand: CanonicalOperand
    required_patterns: tuple[str, ...]
    match_scope: Literal["paragraph", "document"] = "paragraph"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "operand": self.operand.to_dict(),
            "required_patterns": list(self.required_patterns),
        }
        if self.match_scope != "paragraph":
            payload["match_scope"] = self.match_scope
        return payload


@dataclass(frozen=True)
class SelectedReportMethodAdapter:
    """Recognize one enumerated method declaration in the exact selected report bytes."""

    check_manifest: CheckManifest
    adapter_manifest: AdapterManifest
    rules: tuple[ReportOperandRule, ...]
    role_bindings: tuple[RoleBinding, ...]
    trigger_patterns: tuple[str, ...]

    @property
    def adapter_id(self) -> str:
        return self.adapter_manifest.adapter_id

    @property
    def adapter_version(self) -> str:
        return self.adapter_manifest.adapter_version

    @property
    def implementation_digest(self) -> str:
        return SELECTED_REPORT_ADAPTER_IMPLEMENTATION_DIGEST

    @property
    def recognition_grammar_digest(self) -> str:
        return report_recognition_grammar_digest(
            self.rules, self.role_bindings, self.trigger_patterns
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
        matches: list[tuple[ReportOperandRule, int, int]] = []
        paragraphs = _paragraphs(text)
        for rule in self.rules:
            scopes = ((0, len(text), text),) if rule.match_scope == "document" else paragraphs
            for start, end, scope_text in scopes:
                pattern_matches = [
                    re.search(pattern, scope_text) for pattern in rule.required_patterns
                ]
                if all(item is not None for item in pattern_matches):
                    if rule.match_scope == "document":
                        matched = [item for item in pattern_matches if item is not None]
                        start = min(item.start() for item in matched)
                        end = max(item.end() for item in matched)
                    matches.append((rule, start, end))
        if len(matches) > 1:
            return self._abstain(
                "ambiguous",
                "More than one supported method declaration is present in the selected report.",
                document=document,
            )
        if not matches:
            triggered = any(
                re.search(pattern, text) is not None for pattern in self.trigger_patterns
            )
            return self._abstain(
                "unsupported" if triggered else "not_applicable",
                (
                    "Method-like wording is present, but no enumerated exact declaration is supported."
                    if triggered
                    else "The selected report contains no trigger for this exact method check."
                ),
                document=document,
            )
        rule, start, end = matches[0]
        target = context.selected_artifact_ref
        span = _evidence_span(document, text, start, end)
        scope_path = (
            ScopeJoinEdge(
                source_ref=target,
                relation="selected_by_publication_surface",
                target_ref=context.selected_surface_ref,
            ),
        )
        if not selected_surface_owns_artifact(context):
            return self._abstain(
                "unsupported",
                "The selected report Artifact is not owned by the resolved PublicationSurface selection.",
                document=document,
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
                        "span": span.to_dict(),
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
            role_bindings=self.role_bindings,
            observed_operand=rule.operand,
            evidence_spans=(span,),
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


def _paragraphs(text: str) -> list[tuple[int, int, str]]:
    matches = list(re.finditer(r"(?ms)(?:^|\n[ \t]*\n)([^\n].*?)(?=\n[ \t]*\n|\Z)", text))
    paragraphs: list[tuple[int, int, str]] = []
    for match in matches:
        start = match.start(1)
        paragraph = match.group(1).rstrip("\r\n")
        paragraphs.append((start, start + len(paragraph), paragraph))
    return paragraphs


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


def report_recognition_grammar_digest(
    rules: tuple[ReportOperandRule, ...],
    role_bindings: tuple[RoleBinding, ...],
    trigger_patterns: tuple[str, ...],
) -> str:
    return semantic_digest(
        {
            "rules": [item.to_dict() for item in rules],
            "role_bindings": [item.to_dict() for item in role_bindings],
            "trigger_patterns": list(trigger_patterns),
        }
    )
