from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.adapter_common import (
    adapter_implementation_digest,
    receipt_description,
    receipt_kind,
    selected_surface_document,
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
from sc_referee.scientific_checks.scope_joins import selected_publication_path

RMARKDOWN_MVMR_ADAPTER_IMPLEMENTATION_DIGEST = adapter_implementation_digest(Path(__file__))


@dataclass(frozen=True)
class _RMarkdownCallShape:
    operand: CanonicalOperand
    spans: tuple[EvidenceSpan, ...]


@dataclass(frozen=True)
class RMarkdownMVMRCovarianceAdapter:
    """Connect selected R Markdown chunks to one exact MVMR covariance operand."""

    check_manifest: CheckManifest
    adapter_manifest: AdapterManifest
    zero_operand: CanonicalOperand
    provided_operand: CanonicalOperand
    role_bindings: tuple[RoleBinding, ...]

    @property
    def adapter_id(self) -> str:
        return self.adapter_manifest.adapter_id

    @property
    def adapter_version(self) -> str:
        return self.adapter_manifest.adapter_version

    @property
    def implementation_digest(self) -> str:
        return RMARKDOWN_MVMR_ADAPTER_IMPLEMENTATION_DIGEST

    @property
    def recognition_grammar_digest(self) -> str:
        return rmarkdown_mvmr_recognition_grammar_digest(
            self.zero_operand, self.provided_operand, self.role_bindings
        )

    def inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        document = selected_surface_document(
            context,
            parser_id="parser:rmarkdown-selected-report-inventory",
            parser_version="0.1.0",
            media_type="text/x-r-markdown",
        )
        if document is None:
            return self._abstain(
                "not_applicable",
                "The selected publication surface is not a supported immutable R Markdown source.",
            )
        try:
            text = document.content.decode("utf-8")
            parser = json.loads(document.parser_result_payload or b"{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._abstain(
                "unsupported",
                "The selected R Markdown source or parser inventory is invalid.",
                document=document,
            )
        if parser.get("state") != "parsed":
            return self._abstain(
                "unsupported",
                "The selected R Markdown parser inventory did not complete.",
                document=document,
            )
        chunks = parser.get("extensions", {}).get("x-rmarkdown-chunks")
        if not isinstance(chunks, list):
            return self._abstain(
                "unsupported",
                "The selected R Markdown parser inventory has no bounded chunk list.",
                document=document,
            )
        shapes, triggered, unsupported = _mvmr_covariance_shapes(
            document,
            text,
            chunks,
            zero_operand=self.zero_operand,
            provided_operand=self.provided_operand,
        )
        if unsupported:
            return self._abstain(
                "unsupported",
                "An active MVMR diagnostic call is present but its gencov operand is outside the closed grammar.",
                document=document,
            )
        operands = {shape.operand.canonical_value for shape in shapes}
        if len(operands) > 1:
            return self._abstain(
                "ambiguous",
                "Active MVMR diagnostic targets use contradictory covariance operands.",
                document=document,
            )
        if not shapes:
            return self._abstain(
                "unsupported" if triggered else "not_applicable",
                (
                    "MVMR diagnostic wording is present, but no active supported gencov call was established."
                    if triggered
                    else "No active supported MVMR covariance diagnostic target is present."
                ),
                document=document,
            )
        if not selected_surface_owns_artifact(context):
            return self._abstain(
                "unsupported",
                "The selected R Markdown Artifact is not owned by the resolved PublicationSurface selection.",
                document=document,
            )
        operand = shapes[0].operand
        spans = tuple(
            sorted(
                {span for shape in shapes for span in shape.spans},
                key=lambda item: (
                    item.path,
                    item.start_line,
                    item.start_column,
                    item.end_line,
                    item.end_column,
                ),
            )
        )
        scope_path = selected_publication_path(
            context.scope_join_graph,
            selected_artifact_ref=context.selected_artifact_ref,
            selected_surface_ref=context.selected_surface_ref,
            relation="selected_source_artifact_of_publication_surface",
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
                        "spans": [item.to_dict() for item in spans],
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
            evidence_plane="static_source",
            method_target_ref=context.selected_artifact_ref,
            role_bindings=self.role_bindings,
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
            evidence_plane="static_source",
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
                        else sha256_digest("selected-rmarkdown-unavailable")
                    ),
                    description=reason,
                ),
            ),
            non_inferences=self.check_manifest.prohibited_inferences,
            output_ceiling="question_only",
            abstention_reason=reason,
        )


def rmarkdown_mvmr_recognition_grammar_digest(
    zero_operand: CanonicalOperand,
    provided_operand: CanonicalOperand,
    role_bindings: tuple[RoleBinding, ...],
) -> str:
    return semantic_digest(
        {
            "profile": "selected-rmarkdown-mvmr-cross-exposure-covariance-v1",
            "diagnostic_calls": ["strength_mvmr", "pleiotropy_mvmr"],
            "optional_namespace": "MVMR::",
            "required_named_argument": "gencov",
            "zero_literals": ["0", "0.0"],
            "provided_constructors": ["phenocov_mvmr", "snpcov_mvmr"],
            "active_chunks_only": True,
            "single_line_calls_only": True,
            "zero_operand": zero_operand.to_dict(),
            "provided_operand": provided_operand.to_dict(),
            "role_bindings": [item.to_dict() for item in role_bindings],
            "project_execution": False,
        }
    )


def _mvmr_covariance_shapes(
    document: InspectionDocument,
    text: str,
    chunks: list[object],
    *,
    zero_operand: CanonicalOperand,
    provided_operand: CanonicalOperand,
) -> tuple[list[_RMarkdownCallShape], bool, bool]:
    lines = text.splitlines()
    origins: dict[str, EvidenceSpan] = {}
    shapes: list[_RMarkdownCallShape] = []
    triggered = False
    unsupported = False
    for chunk in chunks:
        if not isinstance(chunk, dict) or chunk.get("evaluation_state") != "enabled":
            continue
        start = chunk.get("code_start_line")
        end = chunk.get("code_end_line")
        if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start - 1:
            unsupported = True
            continue
        if end == start - 1:
            continue
        for line_number in range(start, min(end, len(lines)) + 1):
            original = lines[line_number - 1]
            code = _mask_r_strings_and_comment(original)
            if not code.strip():
                continue
            assignment = re.match(
                r"^\s*(?P<name>[A-Za-z.][A-Za-z0-9._]*)\s*(?:<-|=)\s*"
                r"(?:(?:MVMR)::)?(?P<constructor>phenocov_mvmr|snpcov_mvmr)\s*\(",
                code,
            )
            generic_assignment = re.match(r"^\s*(?P<name>[A-Za-z.][A-Za-z0-9._]*)\s*(?:<-|=)", code)
            if generic_assignment is not None:
                name = generic_assignment.group("name")
                if assignment is None:
                    origins.pop(name, None)
                else:
                    origins[name] = _line_evidence_span(
                        document,
                        line_number,
                        original,
                        assignment.start(),
                        len(code.rstrip()),
                    )
            if re.search(r"\b(?:strength_mvmr|pleiotropy_mvmr)\b", code) is None:
                continue
            triggered = True
            call = re.fullmatch(
                r"\s*(?:[A-Za-z.][A-Za-z0-9._]*\s*(?:<-|=)\s*)?"
                r"(?P<call>(?:(?:MVMR)::)?"
                r"(?P<function>strength_mvmr|pleiotropy_mvmr)\s*"
                r"\((?P<arguments>[^()]*)\))\s*",
                code,
            )
            if call is None:
                unsupported = True
                continue
            argument = re.search(
                r"(?:^|,)\s*gencov\s*=\s*(?P<value>[^,\s)]+)",
                call.group("arguments"),
            )
            if argument is None:
                unsupported = True
                continue
            value = argument.group("value")
            call_span = _line_evidence_span(
                document,
                line_number,
                original,
                call.start("call"),
                call.end("call"),
            )
            if re.fullmatch(r"0(?:[.]0+)?", value) is not None:
                shapes.append(_RMarkdownCallShape(zero_operand, (call_span,)))
                continue
            if re.fullmatch(r"[A-Za-z.][A-Za-z0-9._]*", value) is not None and value in origins:
                shapes.append(_RMarkdownCallShape(provided_operand, (origins[value], call_span)))
                continue
            unsupported = True
    return shapes, triggered, unsupported


def _mask_r_strings_and_comment(line: str) -> str:
    masked = list(line)
    quote: str | None = None
    escaped = False
    for index, character in enumerate(line):
        if quote is not None:
            masked[index] = " "
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if character in {"'", '"'}:
            quote = character
            masked[index] = " "
            continue
        if character == "#":
            masked[index:] = [" "] * (len(masked) - index)
            break
    return "".join(masked)


def _line_evidence_span(
    document: InspectionDocument,
    line_number: int,
    line: str,
    start_column: int,
    end_column: int,
) -> EvidenceSpan:
    assert document.parser_result_ref is not None
    assert document.source_location is not None
    return EvidenceSpan(
        file_ref=document.file_ref,
        path=document.path,
        content_digest=document.source_location.content_digest,
        start_line=line_number + document.line_offset,
        end_line=line_number + document.line_offset,
        start_column=min(start_column + 1, len(line) + 1),
        end_column=min(max(end_column + 1, start_column + 1), len(line) + 1),
        parser_result_ref=document.parser_result_ref,
    )
