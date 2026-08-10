"""Question-only normalization of the dependence-recognition shadow result.

The package-local recognizer remains an evaluation-only producer.  This
wrapper calls it exactly once, refuses malformed or unscoped projections, and
converts only exact accepted certificate source declarations into the common
scientific-check observation protocol.  It never executes project code and
never emits a Finding.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.dependence_recognition.adapter import (
    DEPENDENCE_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST,
    DependenceRecognitionShadowAdapter,
)
from sc_referee.scientific_checks.adapter_common import (
    adapter_implementation_digest,
    receipt_description,
    receipt_kind,
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
    ObservationState,
    RoleBinding,
)
from sc_referee.scientific_checks.scope_joins import selected_static_writer_path

DEPENDENCE_RECOGNITION_CHECK_ID = (
    "check:authorized-independent-unit-entry-into-row-independent-procedure"
)
DEPENDENCE_RECOGNITION_CHECK_VERSION = "1.1.0"
DEPENDENCE_RECOGNITION_ADAPTER_ID = (
    "adapter:authorized-independent-unit-entry-into-row-independent-procedure:"
    "dependence-semantic-v1"
)
DEPENDENCE_RECOGNITION_ADAPTER_VERSION = "1.1.0"
DEPENDENCE_RECOGNITION_CANDIDATE_ID = "one-analyzed-row-per-authorized-independent-unit"
ONE_ROW_PER_AUTHORIZED_UNIT = "one_analyzed_row_per_authorized_independent_unit"
MULTIPLE_ROWS_PER_AUTHORIZED_UNIT = "multiple_analyzed_rows_per_authorized_independent_unit"
DEPENDENCE_RECOGNITION_SEMANTIC_ROLES = (
    "authorized_independent_unit_key",
    "analyzed_row_domain",
    "row_independent_procedure",
    "selected_result_sink",
)
DEPENDENCE_RECOGNITION_ROLE_BINDINGS = (
    RoleBinding("authorized_independent_unit_key", "human_authorized_independent_unit_key"),
    RoleBinding("analyzed_row_domain", "certified_complete_analyzed_row_domain"),
    RoleBinding("row_independent_procedure", "certified_row_independent_procedure_call"),
    RoleBinding("selected_result_sink", "certified_selected_result_sink"),
)
DEPENDENCE_RECOGNITION_COUNTEREVIDENCE = (
    "accepted-dependence-certificate",
    "exact-certificate-evidence-spans",
    "selected-static-writer-scope",
)

_EXPECTED_SHADOW_ID = "dependence-recognition-semantic-shadow"
_EXPECTED_SHADOW_VERSION = "1.1.0"
_EXPECTED_SHADOW_SCHEMA_VERSION = "1.1.0"
_EXPECTED_SHADOW_DELIVERY = "unregistered_shadow_report_only"
_EXPECTED_SHADOW_CEILING = "evaluation_candidate"
_EXPECTED_WORDING_CEILING = "static_code_relationship_only"
_EVIDENCE_KEYS = {
    "evidence_id",
    "path",
    "start_line",
    "end_line",
    "start_column",
    "end_column",
}


class _ShadowInspector(Protocol):
    def inspect(self, context: FrozenInspectionContext) -> dict[str, Any]: ...


def dependence_recognition_grammar() -> dict[str, Any]:
    """Return the complete registered normalization grammar."""

    return {
        "grammar_id": "bounded-dependence-semantic-certificate-v1",
        "grammar_version": DEPENDENCE_RECOGNITION_ADAPTER_VERSION,
        "shadow_adapter_id": _EXPECTED_SHADOW_ID,
        "shadow_adapter_version": _EXPECTED_SHADOW_VERSION,
        "shadow_implementation_digest": DEPENDENCE_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST,
        "outcome_mapping": {
            "shadow_candidate": {
                "applicability": "applicable",
                "operand": MULTIPLE_ROWS_PER_AUTHORIZED_UNIT,
            },
            "coverage_note": {
                "applicability": "applicable",
                "operand": ONE_ROW_PER_AUTHORIZED_UNIT,
            },
            "material_question": {"applicability": "ambiguous", "operand": None},
            "no-supported-dependence-lineage": {
                "applicability": "not_applicable",
                "operand": None,
            },
            "other_or_malformed": {"applicability": "unsupported", "operand": None},
        },
        "evidence_projection": "exact-accepted-source-evidence-declarations",
        "scope_join": "selected_static_writer_path",
        "semantic_roles": [item.to_dict() for item in DEPENDENCE_RECOGNITION_ROLE_BINDINGS],
        "output_ceiling": "question_only",
        "project_authored_code_execution": False,
    }


def dependence_recognition_grammar_digest() -> str:
    return semantic_digest(dependence_recognition_grammar())


DEPENDENCE_RECOGNITION_SCIENTIFIC_ADAPTER_IMPLEMENTATION_DIGEST = semantic_digest(
    {
        "registered_wrapper": adapter_implementation_digest(Path(__file__)),
        "dependence_shadow_adapter": DEPENDENCE_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST,
    }
)


@dataclass(frozen=True)
class DependenceRecognitionScientificAdapter:
    """Normalize one report-only shadow inspection into a question-only observation."""

    check_manifest: CheckManifest
    adapter_manifest: AdapterManifest
    one_row_operand: CanonicalOperand
    multiple_rows_operand: CanonicalOperand
    role_bindings: tuple[RoleBinding, ...] = DEPENDENCE_RECOGNITION_ROLE_BINDINGS
    shadow_adapter: _ShadowInspector = field(default_factory=DependenceRecognitionShadowAdapter)

    @property
    def adapter_id(self) -> str:
        return self.adapter_manifest.adapter_id

    @property
    def adapter_version(self) -> str:
        return self.adapter_manifest.adapter_version

    @property
    def implementation_digest(self) -> str:
        return DEPENDENCE_RECOGNITION_SCIENTIFIC_ADAPTER_IMPLEMENTATION_DIGEST

    @property
    def recognition_grammar_digest(self) -> str:
        return dependence_recognition_grammar_digest()

    def inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        """Call the shadow adapter once and fail closed while normalizing its result."""

        try:
            shadow = self.shadow_adapter.inspect(context)
        except BaseException:
            return self._abstain("unsupported", "dependence-shadow-inspection-exception")

        try:
            return self._normalize(context, shadow)
        except BaseException:
            return self._abstain("unsupported", "malformed-dependence-shadow-payload")

    def _normalize(
        self,
        context: FrozenInspectionContext,
        shadow: object,
    ) -> NormalizedMethodObservation:
        if not _valid_shadow_envelope(shadow):
            return self._abstain("unsupported", "malformed-dependence-shadow-payload")
        assert isinstance(shadow, Mapping)
        payload_type = shadow["payload_type"]
        body = shadow["payload"]
        assert isinstance(payload_type, str)
        assert isinstance(body, Mapping)

        if payload_type == "shadow_candidate":
            if shadow.get("outcome") != "evaluation_candidate":
                return self._abstain("unsupported", "shadow-outcome-payload-mismatch")
            return self._applicable(context, shadow, body, "shadow_candidate")
        if payload_type == "coverage_note":
            if shadow.get("outcome") != "covered_negative":
                return self._abstain("unsupported", "shadow-outcome-payload-mismatch")
            return self._applicable(context, shadow, body, "coverage_note")

        if payload_type == "material_question":
            if shadow.get("outcome") != "question":
                return self._abstain("unsupported", "shadow-outcome-payload-mismatch")
            if _question_source_document(context) is None:
                return self._abstain("unsupported", "dependence-source-or-parser-identity-mismatch")
            return self._abstain("ambiguous", "independent-unit-definition-unresolved")

        if payload_type == "abstention":
            coverage_classes = body.get("coverage_classes")
            if not _nonempty_string_list(coverage_classes):
                return self._abstain("unsupported", "malformed-dependence-shadow-abstention")
            assert isinstance(coverage_classes, list)
            if "no-supported-dependence-lineage" in coverage_classes:
                return self._abstain("not_applicable", "no-supported-dependence-lineage")
            if "paired-procedure-operand-unverified" in coverage_classes:
                return self._abstain("unsupported", "paired-procedure-operand-unverified")
            return self._abstain("unsupported", "dependence-shadow-abstention")

        return self._abstain("unsupported", "unsupported-dependence-shadow-payload-type")

    def _applicable(
        self,
        context: FrozenInspectionContext,
        shadow: Mapping[str, Any],
        body: Mapping[str, Any],
        payload_type: Literal["shadow_candidate", "coverage_note"],
    ) -> NormalizedMethodObservation:
        expected_record_type = (
            "dependence_shadow_candidate"
            if payload_type == "shadow_candidate"
            else "dependence_shadow_coverage_note"
        )
        if body.get("record_type") != expected_record_type or body.get("report_only") is not True:
            return self._abstain("unsupported", "malformed-dependence-certificate-projection")
        if not _valid_certificate_binding_projection(body):
            return self._abstain("unsupported", "malformed-dependence-certificate-projection")

        document = _source_document(context, body)
        if document is None:
            return self._abstain("unsupported", "dependence-source-or-parser-identity-mismatch")
        spans = _source_evidence_spans(document, body.get("evidence_declarations"))
        if not spans:
            return self._abstain("unsupported", "dependence-source-evidence-unavailable")
        scope_path = selected_static_writer_path(
            context.scope_join_graph,
            document=document,
            selected_artifact_ref=context.selected_artifact_ref,
            selected_surface_ref=context.selected_surface_ref,
        )
        if not scope_path:
            return self._abstain("unsupported", "selected-static-writer-scope-unavailable")

        operand = (
            self.multiple_rows_operand
            if payload_type == "shadow_candidate"
            else self.one_row_operand
        )
        receipt_basis = {
            "shadow_payload_digest": semantic_digest(dict(shadow)),
            "source_path": document.path,
            "source_digest": document.content_digest,
            "evidence_spans": [item.to_dict() for item in spans],
            "scope_join_path": [item.to_dict() for item in scope_path],
            "observed_operand": operand.to_dict(),
        }
        receipts = tuple(
            InspectionReceipt(
                receipt_id=receipt_id,
                kind=receipt_kind(receipt_id),
                state="passed",
                evidence_digest=semantic_digest(
                    {"receipt_id": receipt_id, "projection": receipt_basis}
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
            method_target_ref=document.file_ref,
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
        state: ObservationState,
        reason: str,
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
            applicability=state,
            completeness="not_applicable" if state == "not_applicable" else "incomplete",
            evidence_plane="static_source",
            method_target_ref=None,
            role_bindings=(),
            observed_operand=None,
            evidence_spans=(),
            scope_join_path=(),
            receipts=(
                InspectionReceipt(
                    receipt_id="closed-dependence-normalization-abstention",
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


def _valid_shadow_envelope(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    return (
        value.get("record_type") == "dependence_recognition_shadow_result"
        and value.get("schema_version") == _EXPECTED_SHADOW_SCHEMA_VERSION
        and value.get("adapter_id") == _EXPECTED_SHADOW_ID
        and value.get("adapter_version") == _EXPECTED_SHADOW_VERSION
        and value.get("adapter_implementation_digest")
        == DEPENDENCE_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST
        and value.get("delivery_plane") == _EXPECTED_SHADOW_DELIVERY
        and value.get("output_ceiling") == _EXPECTED_SHADOW_CEILING
        and value.get("wording_ceiling") == _EXPECTED_WORDING_CEILING
        and isinstance(value.get("payload_type"), str)
        and isinstance(value.get("payload"), Mapping)
    )


def _valid_certificate_binding_projection(body: Mapping[str, Any]) -> bool:
    required_text = (
        "source_path",
        "source_digest",
        "independent_unit_definition_id",
        "resolved_callable",
        "proposed_case_digest",
    )
    if any(not isinstance(body.get(key), str) or not body[key] for key in required_text):
        return False
    if not _relative_path(body["source_path"]):
        return False
    if not _sha256(body["source_digest"]) or not _sha256(body["proposed_case_digest"]):
        return False
    for key, expected_type in (
        ("analysis_target_ref", "analysis"),
        ("procedure_ref", "procedure"),
        ("affected_target_ref", None),
    ):
        if not _record_ref(body.get(key), expected_type):
            return False
    input_binding = body.get("input_binding")
    if (
        not isinstance(input_binding, Mapping)
        or set(input_binding) != {"path", "content_digest"}
        or not isinstance(input_binding.get("path"), str)
        or not _relative_path(input_binding["path"])
        or not isinstance(input_binding.get("content_digest"), str)
        or not _sha256(input_binding["content_digest"])
    ):
        return False
    return (
        _nonempty_string_list(body.get("authorized_key_columns"))
        and len(set(body["authorized_key_columns"])) == len(body["authorized_key_columns"])
        and _nonempty_string_list(body.get("sink_tokens"))
        and len(set(body["sink_tokens"])) == len(body["sink_tokens"])
        and isinstance(body.get("evidence_declarations"), list)
        and bool(body["evidence_declarations"])
    )


def _source_document(
    context: FrozenInspectionContext,
    body: Mapping[str, Any],
) -> InspectionDocument | None:
    source_path = body["source_path"]
    source_digest = body["source_digest"]
    matches = [
        document
        for document in context.documents
        if document.path == source_path
        and document.content_digest == source_digest
        and document.media_type == "text/x-python"
        and document.parser_result_ref is not None
        and document.parser_result_payload is not None
    ]
    if len(matches) != 1:
        return None
    document = matches[0]
    return document if _has_registered_capture_parser_identity(document) else None


def _question_source_document(context: FrozenInspectionContext) -> InspectionDocument | None:
    matches = [document for document in context.documents if document.media_type == "text/x-python"]
    if len(matches) != 1:
        return None
    document = matches[0]
    return document if _has_registered_capture_parser_identity(document) else None


def _has_registered_capture_parser_identity(document: InspectionDocument) -> bool:
    if document.parser_result_ref is None or document.parser_result_payload is None:
        return False
    try:
        parser = json.loads(document.parser_result_payload or b"{}")
    except (json.JSONDecodeError, MemoryError, RecursionError, TypeError, UnicodeDecodeError):
        return False
    return bool(
        isinstance(parser, Mapping)
        and parser.get("parser_id") == "parser:python-ast-tokenize"
        and parser.get("parser_version") == "0.15.1"
        and parser.get("state") == "parsed"
    )


def _source_evidence_spans(
    document: InspectionDocument,
    declarations: object,
) -> tuple[EvidenceSpan, ...]:
    if not isinstance(declarations, list) or not declarations:
        return ()
    evidence_ids: set[str] = set()
    source_declarations: list[Mapping[str, Any]] = []
    for declaration in declarations:
        if not isinstance(declaration, Mapping) or set(declaration) != _EVIDENCE_KEYS:
            return ()
        evidence_id = declaration.get("evidence_id")
        path = declaration.get("path")
        coordinates = tuple(
            declaration.get(key) for key in ("start_line", "end_line", "start_column", "end_column")
        )
        if (
            not isinstance(evidence_id, str)
            or not evidence_id
            or evidence_id in evidence_ids
            or not isinstance(path, str)
            or not _relative_path(path)
            or any(not isinstance(value, int) or isinstance(value, bool) for value in coordinates)
        ):
            return ()
        evidence_ids.add(evidence_id)
        if path == document.path:
            source_declarations.append(declaration)
    if not source_declarations or document.parser_result_ref is None:
        return ()

    try:
        text = document.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return ()
    lines = text.splitlines() or [""]
    spans: list[EvidenceSpan] = []
    seen_coordinates: set[tuple[int, int, int, int]] = set()
    for declaration in source_declarations:
        start_line = int(declaration["start_line"])
        end_line = int(declaration["end_line"])
        start_column = int(declaration["start_column"])
        end_column = int(declaration["end_column"])
        coordinates = (start_line, end_line, start_column, end_column)
        if (
            coordinates in seen_coordinates
            or start_line < 1
            or end_line < start_line
            or end_line > len(lines)
            or start_column < 1
            or end_column < 1
            or start_column > len(lines[start_line - 1]) + 1
            or end_column > len(lines[end_line - 1]) + 1
            or (start_line == end_line and end_column < start_column)
        ):
            return ()
        seen_coordinates.add(coordinates)
        assert document.source_location is not None
        spans.append(
            EvidenceSpan(
                file_ref=document.file_ref,
                path=document.path,
                content_digest=document.source_location.content_digest,
                start_line=start_line + document.line_offset,
                end_line=end_line + document.line_offset,
                start_column=start_column,
                end_column=end_column,
                parser_result_ref=document.parser_result_ref,
            )
        )
    return tuple(sorted(spans))


def _record_ref(value: object, expected_type: str | None) -> bool:
    return (
        isinstance(value, Mapping)
        and set(value) == {"record_type", "record_id"}
        and isinstance(value.get("record_type"), str)
        and bool(value["record_type"])
        and (expected_type is None or value["record_type"] == expected_type)
        and isinstance(value.get("record_id"), str)
        and bool(value["record_id"])
    )


def _nonempty_string_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and bool(item) for item in value)
    )


def _relative_path(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and not value.startswith("/")
        and "\\" not in value
        and all(segment not in {"", ".", ".."} for segment in value.split("/"))
    )


def _sha256(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    payload = value.removeprefix("sha256:")
    return len(payload) == 64 and all(character in "0123456789abcdef" for character in payload)
