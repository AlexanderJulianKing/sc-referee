from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.parsers.python_ast import PARSER_ID as PYTHON_PARSER_ID
from sc_referee.parsers.python_ast import PARSER_VERSION as PYTHON_PARSER_VERSION
from sc_referee.scientific_checks.core import (
    AdapterManifest,
    CanonicalOperand,
    CheckManifest,
    EvidenceSpan,
    FrozenInspectionContext,
    InspectionDocument,
    InspectionReceipt,
    NormalizedMethodObservation,
    ReceiptKind,
    RecordRef,
    RoleBinding,
    ScopeJoinEdge,
)
from sc_referee.scientific_checks.scope_joins import (
    selected_container_path,
    selected_publication_path,
    selected_static_writer_path,
)

_ADAPTER_IMPLEMENTATION_BYTES_DIGEST = sha256_digest(Path(__file__).read_bytes())
SELECTED_REPORT_ADAPTER_IMPLEMENTATION_DIGEST = _ADAPTER_IMPLEMENTATION_BYTES_DIGEST
PYTHON_FOUNDER_ADAPTER_IMPLEMENTATION_DIGEST = _ADAPTER_IMPLEMENTATION_BYTES_DIGEST
RMARKDOWN_MVMR_ADAPTER_IMPLEMENTATION_DIGEST = _ADAPTER_IMPLEMENTATION_BYTES_DIGEST


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
        return semantic_digest(
            {
                "rules": [item.to_dict() for item in self.rules],
                "role_bindings": [item.to_dict() for item in self.role_bindings],
                "trigger_patterns": list(self.trigger_patterns),
            }
        )

    def inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        document = _selected_report_document(context)
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
        scope_path = selected_publication_path(
            context.scope_join_graph,
            selected_artifact_ref=target,
            selected_surface_ref=context.selected_surface_ref,
            relation="selected_by_publication_surface",
        )
        if not _selected_surface_owns_artifact(context):
            return self._abstain(
                "unsupported",
                "The selected report Artifact is not owned by the resolved PublicationSurface selection.",
                document=document,
            )
        receipts = tuple(
            InspectionReceipt(
                receipt_id=receipt_id,
                kind=_receipt_kind(receipt_id),
                state="passed",
                evidence_digest=semantic_digest(
                    {
                        "receipt_id": receipt_id,
                        "content_digest": document.content_digest,
                        "span": span.to_dict(),
                    }
                ),
                description=_receipt_description(receipt_id),
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
        document = _selected_surface_document(
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
        if not _selected_surface_owns_artifact(context):
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
                kind=_receipt_kind(receipt_id),
                state="passed",
                evidence_digest=semantic_digest(
                    {
                        "receipt_id": receipt_id,
                        "content_digest": document.content_digest,
                        "spans": [item.to_dict() for item in spans],
                    }
                ),
                description=_receipt_description(receipt_id),
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


@dataclass(frozen=True)
class _StaticShape:
    operand: CanonicalOperand
    nodes: tuple[ast.AST, ...]


@dataclass(frozen=True)
class _ResolvedFounderArgument:
    state: str
    origin_key: str
    nodes: tuple[ast.AST, ...]


@dataclass(frozen=True)
class PythonFounderOrientationAdapter:
    """Inspect exact founder-input-to-emission AST roles without importing project code."""

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
        return PYTHON_FOUNDER_ADAPTER_IMPLEMENTATION_DIGEST

    @property
    def recognition_grammar_digest(self) -> str:
        return python_founder_recognition_grammar_digest(
            self.direct_operand, self.repaired_operand, self.role_bindings
        )

    def inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        shapes: list[tuple[InspectionDocument, _StaticShape]] = []
        triggered = False
        parse_failure = False
        for document in context.documents:
            if document.media_type != "text/x-python" or not _python_parser_supported(document):
                continue
            try:
                source = document.content.decode("utf-8")
                tree = ast.parse(source, filename=document.path, type_comments=True)
            except (SyntaxError, UnicodeDecodeError):
                parse_failure = True
                continue
            document_shapes = _founder_orientation_shapes(
                tree,
                direct_operand=self.direct_operand,
                repaired_operand=self.repaired_operand,
            )
            triggered = triggered or bool(document_shapes) or _founder_source_triggered(tree)
            shapes.extend((document, shape) for shape in document_shapes)
        if len(shapes) > 1:
            return self._abstain(
                "ambiguous",
                "More than one Python file contains a supported founder-orientation target.",
            )
        if not shapes:
            return self._abstain(
                "unsupported" if triggered or parse_failure else "not_applicable",
                (
                    "Founder-emission calls are present, but their exact data-flow roles are unsupported."
                    if triggered
                    else "A Python parser boundary prevented the finite source check."
                    if parse_failure
                    else "No exact founder-orientation-before-emission source target is present."
                ),
            )
        document, shape = shapes[0]
        spans = _ast_evidence_spans(document, shape.nodes)
        scope_path = _selected_container_scope_path(
            context, document
        ) or _selected_static_writer_scope_path(context, document)
        scope_supported = bool(scope_path)
        receipts = (
            InspectionReceipt(
                receipt_id="exact-founder-emission-role-binding",
                kind="counterevidence",
                state="passed",
                evidence_digest=semantic_digest([span.to_dict() for span in spans]),
                description=(
                    "The founder allele input and emission call roles were resolved by exact AST flow."
                ),
            ),
            InspectionReceipt(
                receipt_id="alternative-orientation-targets-absent",
                kind="sibling",
                state="passed",
                evidence_digest=semantic_digest(
                    {"path": document.path, "content_digest": document.content_digest}
                ),
                description="No competing supported founder-orientation target was present.",
            ),
            InspectionReceipt(
                receipt_id="source-to-analysis-scope-join",
                kind="counterevidence",
                state="passed" if scope_supported else "unsupported",
                evidence_digest=semantic_digest(
                    {
                        "file_ref": document.file_ref.to_dict(),
                        "source_location": (
                            document.source_location.to_dict()
                            if document.source_location is not None
                            else None
                        ),
                        "scope_join_path": [edge.to_dict() for edge in scope_path],
                        "selected_surface_ref": context.selected_surface_ref.to_dict(),
                    }
                ),
                description=(
                    "The exact source is connected to the selected Artifact by a closed static "
                    "scope proof; this does not establish execution or primary-analysis status."
                    if scope_supported
                    else (
                        "Existing typed records do not connect this algorithmic source target "
                        "to the selected report Artifact."
                    )
                ),
            ),
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
            applicability="applicable" if scope_supported else "unsupported",
            completeness="complete" if scope_supported else "incomplete",
            evidence_plane="static_source",
            method_target_ref=document.file_ref,
            role_bindings=self.role_bindings,
            observed_operand=shape.operand,
            evidence_spans=spans,
            scope_join_path=scope_path,
            receipts=receipts,
            non_inferences=self.check_manifest.prohibited_inferences,
            output_ceiling="question_only",
            abstention_reason=(
                None
                if scope_supported
                else (
                    "The exact source operand is preserved only as a suppressor because the typed "
                    "source-to-analysis scope join is unavailable."
                )
            ),
        )

    def _abstain(self, state: str, reason: str) -> NormalizedMethodObservation:
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
                    evidence_digest=sha256_digest(reason),
                    description=reason,
                ),
            ),
            non_inferences=self.check_manifest.prohibited_inferences,
            output_ceiling="question_only",
            abstention_reason=reason,
        )


def _python_parser_supported(document: InspectionDocument) -> bool:
    if document.parser_result_payload is None:
        return False
    value = json.loads(document.parser_result_payload)
    return (
        isinstance(value, dict)
        and value.get("parser_id") == PYTHON_PARSER_ID
        and value.get("parser_version") == PYTHON_PARSER_VERSION
        and value.get("state") == "parsed"
    )


def _founder_orientation_shapes(
    tree: ast.Module,
    *,
    direct_operand: CanonicalOperand,
    repaired_operand: CanonicalOperand,
) -> tuple[_StaticShape, ...]:
    orientation_calls = {
        "orient_ril_founder_alleles",
        "repair_ril_founder_orientation",
    }
    parent_map = _parent_map(tree)
    local_functions = _local_functions(tree)
    shapes: list[_StaticShape] = []
    for candidates in local_functions.values():
        if len(candidates) != 1:
            continue
        emission_function = candidates[0]
        emission_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and _terminal_call_name(node) == emission_function.name
            and len(node.args) >= 2
        ]
        shape = _founder_shape_for_target(
            tree=tree,
            emission_function=emission_function,
            emission_calls=emission_calls,
            parent_map=parent_map,
            local_functions=local_functions,
            orientation_calls=orientation_calls,
            direct_operand=direct_operand,
            repaired_operand=repaired_operand,
        )
        if shape is not None:
            shapes.append(shape)
    return tuple(shapes)


def _founder_shape_for_target(
    *,
    tree: ast.Module,
    emission_function: ast.FunctionDef | ast.AsyncFunctionDef,
    emission_calls: list[ast.Call],
    parent_map: dict[ast.AST, ast.AST],
    local_functions: dict[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]],
    orientation_calls: set[str],
    direct_operand: CanonicalOperand,
    repaired_operand: CanonicalOperand,
) -> _StaticShape | None:
    if not emission_calls:
        return None
    positional_parameters = (*emission_function.args.posonlyargs, *emission_function.args.args)
    if len(positional_parameters) < 2:
        return None
    observed_parameter = positional_parameters[0].arg
    founder_parameter = positional_parameters[1].arg
    direct_comparisons = [
        node
        for node in _nodes_in_scope(emission_function, parent_map)
        if isinstance(node, ast.Compare)
        and observed_parameter in _names(node)
        and founder_parameter in _names(node)
    ]
    if len(direct_comparisons) != 1:
        return None

    resolutions: list[_ResolvedFounderArgument] = []
    for call in emission_calls:
        scope = _enclosing_scope(tree, call, parent_map)
        resolved = _resolve_founder_argument(
            call.args[1],
            scope=scope,
            tree=tree,
            parent_map=parent_map,
            local_functions=local_functions,
            orientation_calls=orientation_calls,
            seen=frozenset(),
        )
        if resolved is None:
            return None
        resolutions.append(resolved)
    states = {item.state for item in resolutions}
    origins = {item.origin_key for item in resolutions}
    if len(states) != 1 or len(origins) != 1:
        return None
    state = next(iter(states))
    nodes = _unique_ast_nodes(
        (
            direct_comparisons[0],
            *emission_calls,
            *(node for item in resolutions for node in item.nodes),
        )
    )
    return _StaticShape(repaired_operand if state == "repaired" else direct_operand, nodes)


def _founder_source_triggered(tree: ast.Module) -> bool:
    has_founder_field = any(
        isinstance(node, ast.Attribute) and node.attr == "founder_alleles"
        for node in ast.walk(tree)
    )
    has_comparison = any(isinstance(node, ast.Compare) for node in ast.walk(tree))
    has_orientation_call = any(
        isinstance(node, ast.Call)
        and (
            _terminal_call_name(node)
            in {"orient_ril_founder_alleles", "repair_ril_founder_orientation"}
            or _orientation_call_semantics(_terminal_call_name(node))
        )
        for node in ast.walk(tree)
    )
    has_founder_semantics = has_founder_field or _founder_origin_expression(tree)
    return has_founder_semantics and (has_comparison or has_orientation_call)


def _resolve_founder_argument(
    expression: ast.expr,
    *,
    scope: ast.Module | ast.FunctionDef | ast.AsyncFunctionDef,
    tree: ast.Module,
    parent_map: dict[ast.AST, ast.AST],
    local_functions: dict[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]],
    orientation_calls: set[str],
    seen: frozenset[tuple[int, str]],
) -> _ResolvedFounderArgument | None:
    if isinstance(expression, ast.Call):
        call_name = _terminal_call_name(expression)
        if call_name in orientation_calls:
            resolved = _resolve_orientation_input(
                expression,
                scope=scope,
                tree=tree,
                parent_map=parent_map,
                local_functions=local_functions,
                orientation_calls=orientation_calls,
                seen=seen,
            )
            if resolved is not None:
                return _ResolvedFounderArgument(
                    state="repaired",
                    origin_key=resolved.origin_key,
                    nodes=(expression, *resolved.nodes),
                )
        if _orientation_call_semantics(call_name):
            resolved = _resolve_orientation_input(
                expression,
                scope=scope,
                tree=tree,
                parent_map=parent_map,
                local_functions=local_functions,
                orientation_calls=orientation_calls,
                seen=seen,
            )
            if resolved is not None:
                return _ResolvedFounderArgument(
                    state="repaired",
                    origin_key=resolved.origin_key,
                    nodes=(expression, *resolved.nodes),
                )
        if _founder_origin_expression(expression):
            return _ResolvedFounderArgument(
                state="direct",
                origin_key=f"founder-origin:{ast.dump(expression, include_attributes=False)}",
                nodes=(expression,),
            )
        return None
    if (
        isinstance(expression, ast.BinOp)
        and isinstance(expression.op, ast.Sub)
        and _numeric_literal(expression.left) == 1.0
    ):
        resolved = _resolve_founder_argument(
            expression.right,
            scope=scope,
            tree=tree,
            parent_map=parent_map,
            local_functions=local_functions,
            orientation_calls=orientation_calls,
            seen=seen,
        )
        if resolved is not None:
            return _ResolvedFounderArgument(
                state="repaired",
                origin_key=resolved.origin_key,
                nodes=(expression, *resolved.nodes),
            )
    if isinstance(expression, ast.Attribute):
        if expression.attr == "founder_alleles":
            return _ResolvedFounderArgument(
                state="direct",
                origin_key=(
                    f"{_scope_identity(scope)}:{ast.dump(expression, include_attributes=False)}"
                ),
                nodes=(expression,),
            )
        return _resolve_founder_argument(
            expression.value,
            scope=scope,
            tree=tree,
            parent_map=parent_map,
            local_functions=local_functions,
            orientation_calls=orientation_calls,
            seen=seen,
        )
    if isinstance(expression, ast.Subscript):
        return _resolve_founder_argument(
            expression.value,
            scope=scope,
            tree=tree,
            parent_map=parent_map,
            local_functions=local_functions,
            orientation_calls=orientation_calls,
            seen=seen,
        )
    if not isinstance(expression, ast.Name):
        return None
    seen_key = (id(scope), expression.id)
    if seen_key in seen:
        return None
    bindings = _name_bindings(scope, expression.id, parent_map)
    if not bindings:
        parameter_resolution = _resolve_parameter_from_callers(
            expression.id,
            scope=scope,
            tree=tree,
            parent_map=parent_map,
            local_functions=local_functions,
            orientation_calls=orientation_calls,
            seen=seen | {seen_key},
        )
        if parameter_resolution is not None:
            return parameter_resolution
        outer_scope = _lexical_parent_scope(scope, parent_map)
        if outer_scope is None:
            return None
        resolved = _resolve_founder_argument(
            expression,
            scope=outer_scope,
            tree=tree,
            parent_map=parent_map,
            local_functions=local_functions,
            orientation_calls=orientation_calls,
            seen=seen | {seen_key},
        )
        if resolved is None:
            return None
        return _ResolvedFounderArgument(
            state=resolved.state,
            origin_key=resolved.origin_key,
            nodes=resolved.nodes,
        )
    if len(bindings) != 1:
        return None
    assignment, value, tuple_index = bindings[0]
    next_seen = seen | {seen_key}
    if tuple_index is None:
        resolved = _resolve_founder_argument(
            value,
            scope=scope,
            tree=tree,
            parent_map=parent_map,
            local_functions=local_functions,
            orientation_calls=orientation_calls,
            seen=next_seen,
        )
    else:
        resolved = _resolve_call_return_component(
            value,
            tuple_index=tuple_index,
            tree=tree,
            parent_map=parent_map,
            local_functions=local_functions,
            orientation_calls=orientation_calls,
            seen=next_seen,
        )
    if resolved is None:
        return None
    return _ResolvedFounderArgument(
        state=resolved.state,
        origin_key=resolved.origin_key,
        nodes=(assignment, *resolved.nodes),
    )


def _resolve_orientation_input(
    expression: ast.Call,
    *,
    scope: ast.Module | ast.FunctionDef | ast.AsyncFunctionDef,
    tree: ast.Module,
    parent_map: dict[ast.AST, ast.AST],
    local_functions: dict[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]],
    orientation_calls: set[str],
    seen: frozenset[tuple[int, str]],
) -> _ResolvedFounderArgument | None:
    if len(expression.args) != 1 or expression.keywords:
        return None
    return _resolve_founder_argument(
        expression.args[0],
        scope=scope,
        tree=tree,
        parent_map=parent_map,
        local_functions=local_functions,
        orientation_calls=orientation_calls,
        seen=seen,
    )


def _resolve_parameter_from_callers(
    name: str,
    *,
    scope: ast.Module | ast.FunctionDef | ast.AsyncFunctionDef,
    tree: ast.Module,
    parent_map: dict[ast.AST, ast.AST],
    local_functions: dict[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]],
    orientation_calls: set[str],
    seen: frozenset[tuple[int, str]],
) -> _ResolvedFounderArgument | None:
    if isinstance(scope, ast.Module):
        return None
    positional = (*scope.args.posonlyargs, *scope.args.args)
    indexes = [index for index, parameter in enumerate(positional) if parameter.arg == name]
    if len(indexes) != 1:
        return None
    parameter_index = indexes[0]
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _terminal_call_name(node) == scope.name
    ]
    if not calls:
        return None
    resolutions: list[_ResolvedFounderArgument] = []
    for call in calls:
        argument = _call_argument(call, name=name, positional_index=parameter_index)
        if argument is None:
            return None
        caller_scope = _enclosing_scope(tree, call, parent_map)
        resolved = _resolve_founder_argument(
            argument,
            scope=caller_scope,
            tree=tree,
            parent_map=parent_map,
            local_functions=local_functions,
            orientation_calls=orientation_calls,
            seen=seen,
        )
        if resolved is None:
            return None
        resolutions.append(
            _ResolvedFounderArgument(
                state=resolved.state,
                origin_key=resolved.origin_key,
                nodes=(call, *resolved.nodes),
            )
        )
    return _collapse_founder_resolutions(resolutions)


def _call_argument(call: ast.Call, *, name: str, positional_index: int) -> ast.expr | None:
    if positional_index < len(call.args):
        return call.args[positional_index]
    matching_keywords = [item.value for item in call.keywords if item.arg == name]
    return matching_keywords[0] if len(matching_keywords) == 1 else None


def _collapse_founder_resolutions(
    resolutions: list[_ResolvedFounderArgument],
) -> _ResolvedFounderArgument | None:
    if not resolutions:
        return None
    states = {item.state for item in resolutions}
    origins = {item.origin_key for item in resolutions}
    if len(states) != 1 or len(origins) != 1:
        return None
    return _ResolvedFounderArgument(
        state=next(iter(states)),
        origin_key=next(iter(origins)),
        nodes=_unique_ast_nodes(tuple(node for item in resolutions for node in item.nodes)),
    )


def _lexical_parent_scope(
    scope: ast.Module | ast.FunctionDef | ast.AsyncFunctionDef,
    parent_map: dict[ast.AST, ast.AST],
) -> ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | None:
    if isinstance(scope, ast.Module):
        return None
    current: ast.AST = scope
    while current in parent_map:
        current = parent_map[current]
        if isinstance(current, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
    return None


def _orientation_call_semantics(name: str) -> bool:
    tokens = _identifier_tokens(name)
    return bool(tokens & {"complement", "flip", "invert", "orient", "orientation", "recode"})


def _founder_origin_expression(node: ast.AST) -> bool:
    tokens: set[str] = set()
    for item in ast.walk(node):
        if isinstance(item, ast.Name):
            tokens.update(_identifier_tokens(item.id))
        elif isinstance(item, ast.Attribute):
            tokens.update(_identifier_tokens(item.attr))
        elif isinstance(item, ast.Constant) and isinstance(item.value, str):
            tokens.update(_identifier_tokens(item.value))
    return bool(tokens & {"founder", "founders"})


def _identifier_tokens(value: str) -> set[str]:
    return {item for item in re.split(r"[^a-z0-9]+", value.casefold()) if item}


def _numeric_literal(node: ast.expr) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    return None


def _resolve_call_return_component(
    value: ast.expr,
    *,
    tuple_index: int,
    tree: ast.Module,
    parent_map: dict[ast.AST, ast.AST],
    local_functions: dict[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]],
    orientation_calls: set[str],
    seen: frozenset[tuple[int, str]],
) -> _ResolvedFounderArgument | None:
    if not isinstance(value, ast.Call):
        return None
    candidates = local_functions.get(_terminal_call_name(value), ())
    if len(candidates) != 1:
        return None
    function = candidates[0]
    returns = [
        node
        for node in _nodes_in_scope(function, parent_map)
        if isinstance(node, ast.Return) and node.value is not None
    ]
    if len(returns) != 1 or not isinstance(returns[0].value, (ast.Tuple, ast.List)):
        return None
    elements = returns[0].value.elts
    if tuple_index >= len(elements):
        return None
    resolved = _resolve_founder_argument(
        elements[tuple_index],
        scope=function,
        tree=tree,
        parent_map=parent_map,
        local_functions=local_functions,
        orientation_calls=orientation_calls,
        seen=seen,
    )
    if resolved is None:
        return None
    return _ResolvedFounderArgument(
        state=resolved.state,
        origin_key=resolved.origin_key,
        nodes=(value, returns[0], *resolved.nodes),
    )


def _parent_map(tree: ast.Module) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _local_functions(
    tree: ast.Module,
) -> dict[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]]:
    grouped: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            grouped.setdefault(node.name, []).append(node)
    return {name: tuple(values) for name, values in grouped.items()}


def _enclosing_scope(
    tree: ast.Module, node: ast.AST, parent_map: dict[ast.AST, ast.AST]
) -> ast.Module | ast.FunctionDef | ast.AsyncFunctionDef:
    current = node
    while current in parent_map:
        current = parent_map[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
    return tree


def _nodes_in_scope(
    scope: ast.Module | ast.FunctionDef | ast.AsyncFunctionDef,
    parent_map: dict[ast.AST, ast.AST],
) -> tuple[ast.AST, ...]:
    return tuple(
        node
        for node in ast.walk(scope)
        if node is scope or _enclosing_scope_for_parent_map(node, parent_map) is scope
    )


def _enclosing_scope_for_parent_map(
    node: ast.AST, parent_map: dict[ast.AST, ast.AST]
) -> ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | None:
    current = node
    while current in parent_map:
        current = parent_map[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            return current
    return None


def _name_bindings(
    scope: ast.Module | ast.FunctionDef | ast.AsyncFunctionDef,
    name: str,
    parent_map: dict[ast.AST, ast.AST],
) -> list[tuple[ast.Assign | ast.AnnAssign, ast.expr, int | None]]:
    values: list[tuple[ast.Assign | ast.AnnAssign, ast.expr, int | None]] = []
    for node in _nodes_in_scope(scope, parent_map):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        targets = (node.target,) if isinstance(node, ast.AnnAssign) else tuple(node.targets)
        for target in targets:
            if isinstance(target, ast.Name) and target.id == name:
                values.append((node, node.value, None))
            elif isinstance(target, (ast.Tuple, ast.List)):
                indexes = [
                    index
                    for index, item in enumerate(target.elts)
                    if isinstance(item, ast.Name) and item.id == name
                ]
                values.extend((node, node.value, index) for index in indexes)
    return values


def _scope_identity(scope: ast.Module | ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    if isinstance(scope, ast.Module):
        return "module"
    return f"{scope.name}:{scope.lineno}"


def _unique_ast_nodes(nodes: tuple[ast.AST, ...]) -> tuple[ast.AST, ...]:
    by_identity = {id(node): node for node in nodes}
    return tuple(
        sorted(
            by_identity.values(),
            key=lambda node: (
                getattr(node, "lineno", 0),
                getattr(node, "col_offset", 0),
                type(node).__name__,
            ),
        )
    )


def _terminal_call_name(node: ast.Call) -> str:
    target: ast.expr = node.func
    while isinstance(target, ast.Attribute):
        if target.attr:
            return target.attr
        target = target.value
    return target.id if isinstance(target, ast.Name) else "<dynamic>"


def _names(node: ast.AST) -> set[str]:
    return {item.id for item in ast.walk(node) if isinstance(item, ast.Name)}


def _ast_evidence_spans(
    document: InspectionDocument, nodes: tuple[ast.AST, ...]
) -> tuple[EvidenceSpan, ...]:
    candidates = _unique_ast_nodes(nodes)
    outermost = tuple(
        node
        for node in candidates
        if not any(
            other is not node
            and getattr(other, "lineno", 1) <= getattr(node, "lineno", 1)
            and getattr(other, "end_lineno", getattr(other, "lineno", 1))
            >= getattr(node, "end_lineno", getattr(node, "lineno", 1))
            and (
                getattr(other, "lineno", 1) < getattr(node, "lineno", 1)
                or getattr(other, "end_lineno", getattr(other, "lineno", 1))
                > getattr(node, "end_lineno", getattr(node, "lineno", 1))
            )
            for other in candidates
        )
    )
    ordered = sorted(
        outermost,
        key=lambda node: (
            0 if isinstance(node, ast.Call) else 1,
            getattr(node, "lineno", 0),
            getattr(node, "col_offset", 0),
            type(node).__name__,
        ),
    )
    return tuple(_ast_node_evidence_span(document, node) for node in ordered)


def _ast_node_evidence_span(document: InspectionDocument, node: ast.AST) -> EvidenceSpan:
    assert document.parser_result_ref is not None
    assert document.source_location is not None
    start_line = getattr(node, "lineno", 1)
    end_line = getattr(node, "end_lineno", start_line)
    lines = document.content.decode("utf-8").splitlines()
    if start_line == end_line and 1 <= start_line <= len(lines):
        start_column = 1
        end_column = len(lines[start_line - 1]) + 1
    else:
        start_column = getattr(node, "col_offset", 0) + 1
        end_column = getattr(node, "end_col_offset", getattr(node, "col_offset", 0)) + 1
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


def python_founder_recognition_grammar_digest(
    direct_operand: CanonicalOperand,
    repaired_operand: CanonicalOperand,
    role_bindings: tuple[RoleBinding, ...],
) -> str:
    return semantic_digest(
        {
            "profile": "python-founder-orientation-before-emission-ast-v4",
            "orientation_call_names": [
                "orient_ril_founder_alleles",
                "repair_ril_founder_orientation",
            ],
            "emission_target": (
                "one locally defined two-or-more-argument function whose first two formal roles "
                "are compared and whose second call argument has exact founder-semantic origin "
                "provenance through bounded local assignments, lexical closures, and call parameters"
            ),
            "orientation_transform_shapes": [
                "one-minus-founder-input",
                "single-argument call with orient, orientation, flip, invert, complement, or recode token",
            ],
            "symbol_identity_authoritative": False,
            "direct_operand": direct_operand.to_dict(),
            "repaired_operand": repaired_operand.to_dict(),
            "role_bindings": [item.to_dict() for item in role_bindings],
            "dynamic_dispatch_supported": False,
            "multiple_targets_supported": False,
            "interprocedural_limits": {
                "local_functions_only": True,
                "unique_bindings_only": True,
                "all_callers_must_resolve_to_one_origin_and_state": True,
                "variadic_arguments_supported": False,
            },
            "scope_profiles": [
                "exact-static-cell-contained-in-selected-source-artifact-v1",
                "exact-static-source-unique-selected-output-writer-v1",
            ],
            "scope_does_not_establish_execution_or_primary_status": True,
        }
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


def _selected_report_document(context: FrozenInspectionContext) -> InspectionDocument | None:
    return _selected_surface_document(
        context,
        parser_id="parser:markdown-inventory",
        parser_version="0.2.0",
        media_type="text/markdown",
    )


def _selected_surface_document(
    context: FrozenInspectionContext,
    *,
    parser_id: str,
    parser_version: str,
    media_type: str,
) -> InspectionDocument | None:
    artifact = _base_record(context, context.selected_artifact_ref)
    if artifact is None or artifact.get("kind") != "report":
        return None
    path = artifact.get("path")
    if not isinstance(path, str):
        return None
    matches = [
        item
        for item in context.documents
        if item.path == path
        and item.media_type == media_type
        and item.content_digest in _artifact_content_digests(context, artifact)
        and item.parser_result_ref is not None
        and item.parser_result_payload is not None
    ]
    if len(matches) != 1:
        return None
    parser = json.loads(matches[0].parser_result_payload or b"{}")
    if (
        parser.get("parser_id") != parser_id
        or parser.get("parser_version") != parser_version
        or parser.get("state") not in {"parsed", "partially_parsed"}
    ):
        return None
    return matches[0]


def _selected_surface_owns_artifact(context: FrozenInspectionContext) -> bool:
    return bool(
        selected_publication_path(
            context.scope_join_graph,
            selected_artifact_ref=context.selected_artifact_ref,
            selected_surface_ref=context.selected_surface_ref,
            relation="selected_by_publication_surface",
        )
    )


def _selected_container_scope_path(
    context: FrozenInspectionContext,
    document: InspectionDocument,
) -> tuple[ScopeJoinEdge, ...]:
    return selected_container_path(
        context.scope_join_graph,
        document=document,
        selected_artifact_ref=context.selected_artifact_ref,
        selected_surface_ref=context.selected_surface_ref,
    )


def _selected_static_writer_scope_path(
    context: FrozenInspectionContext,
    document: InspectionDocument,
) -> tuple[ScopeJoinEdge, ...]:
    return selected_static_writer_path(
        context.scope_join_graph,
        document=document,
        selected_artifact_ref=context.selected_artifact_ref,
        selected_surface_ref=context.selected_surface_ref,
    )


def _base_record(context: FrozenInspectionContext, ref: RecordRef) -> dict[str, Any] | None:
    matches = [item for item in context.base_records if item.ref == ref]
    if len(matches) != 1:
        return None
    value = json.loads(matches[0].canonical_payload)
    return value if isinstance(value, dict) else None


def _artifact_content_digests(
    context: FrozenInspectionContext, artifact: dict[str, Any]
) -> set[str]:
    identity_ref = artifact.get("asset_identity_ref")
    if not isinstance(identity_ref, dict):
        return set()
    identity = _base_record(
        context,
        RecordRef(str(identity_ref.get("record_type")), str(identity_ref.get("record_id"))),
    )
    if identity is None or identity.get("tier") != "full_digest":
        return set()
    digest = identity.get("identity_evidence", {}).get("digest")
    return {str(digest)} if isinstance(digest, str) else set()


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


def _receipt_kind(receipt_id: str) -> ReceiptKind:
    if "ambigu" in receipt_id:
        return "ambiguity"
    if "sibling" in receipt_id or "alternative" in receipt_id:
        return "sibling"
    if "suppress" in receipt_id:
        return "suppressor"
    return "counterevidence"


def _receipt_description(receipt_id: str) -> str:
    return {
        "exactly-one-supported-declaration": (
            "Exactly one enumerated method declaration matched the selected report."
        ),
        "contradictory-declaration-absent": (
            "No contradictory enumerated declaration matched the selected report."
        ),
        "selected-surface-identity-complete": (
            "The report bytes have a full digest and are the exact selected Artifact."
        ),
        "finite-paragraph-scan-complete": (
            "Every paragraph in the selected immutable report was checked."
        ),
    }.get(receipt_id, f"The finite {receipt_id} check completed.")


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
