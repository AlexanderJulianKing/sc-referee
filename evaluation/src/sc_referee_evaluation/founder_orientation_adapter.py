from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee_evaluation.analysis_method_qualification import (
    AnalysisMethodQualificationError,
    _report_declarations,
    _source_closure,
    _Unavailable,
)
from sc_referee_evaluation.typed_method_qualification import (
    IndependentDeclaration,
    IndependentObservation,
    TypedMethodQualificationError,
)

_ADAPTER_ID = "qualification-adapter:founder-orientation-python-v1"
_ADAPTER_VERSION = "1.0.0"
_CHECK_ID = "check:founder-orientation-before-hmm-emission"
_DIMENSION = "scale_and_orientation"
_RELATIONS = (
    "contains_unique_static_selected_output_writer",
    "declares_selected_output_artifact",
    "selected_by_publication_surface",
)


def founder_orientation_dependency_closure() -> tuple[dict[str, str], ...]:
    """Return the exact independent semantic implementation files for this adapter."""

    adapter_path = Path(__file__)
    legacy_path = adapter_path.with_name("analysis_method_qualification.py")
    return (
        {
            "path": "sc_referee_evaluation/analysis_method_qualification.py",
            "content_digest": sha256_digest(legacy_path.read_bytes()),
        },
        {
            "path": "sc_referee_evaluation/founder_orientation_adapter.py",
            "content_digest": sha256_digest(adapter_path.read_bytes()),
        },
    )


class FounderOrientationQualificationAdapter:
    """Independently extract the closed founder-orientation report and Python operands."""

    adapter_id = _ADAPTER_ID
    adapter_version = _ADAPTER_VERSION

    @property
    def implementation_digest(self) -> str:
        return semantic_digest(founder_orientation_dependency_closure())

    def inspect(
        self,
        retained_bytes: Mapping[str, bytes],
        assignment: Mapping[str, Any],
        binding: Mapping[str, Any],
    ) -> tuple[IndependentObservation, ...]:
        _validate_binding(binding)
        payload = _assignment_payload(assignment)
        selected_report = _required_path(payload.get("selected_report_path"))
        decoded = _strict_utf8_candidates(retained_bytes)
        try:
            report_operand, report_declarations = _report_declarations(selected_report, decoded)
            source_operand, source_declarations, writer_path, _ = _source_closure(
                selected_report, decoded
            )
        except (_Unavailable, AnalysisMethodQualificationError) as error:
            raise TypedMethodQualificationError(
                f"founder-orientation qualification extraction is unavailable: {error}"
            ) from error
        if source_declarations[0].get("path") != writer_path:
            raise TypedMethodQualificationError(
                "founder-orientation source and selected-output writer are not one file"
            )
        if payload.get("scope_source_path") != writer_path:
            raise TypedMethodQualificationError(
                "qualification scope does not bind the independently resolved writer path"
            )
        if payload.get("scope_artifact_path") != selected_report:
            raise TypedMethodQualificationError(
                "qualification scope does not bind the assigned selected report"
            )
        scope_path = _scope_path(payload)
        candidate_paths = tuple(sorted(decoded))
        report_text = decoded[selected_report]
        report_items = tuple(
            IndependentDeclaration(
                evidence_plane="reported_text",
                path=selected_report,
                start_line=_line_number(report_text, int(item["start"])),
                end_line=_line_number(report_text, max(int(item["end"]) - 1, 0)),
                retained_text=str(item["sentence"]),
            )
            for item in report_declarations
        )
        source_items = tuple(
            IndependentDeclaration(
                evidence_plane="static_source",
                path=str(item["path"]),
                start_line=int(item["start_line"]),
                end_line=int(item["end_line"]),
                retained_text=_retained_lines(
                    decoded[str(item["path"])],
                    int(item["start_line"]),
                    int(item["end_line"]),
                ),
            )
            for item in source_declarations
        )
        return (
            IndependentObservation(
                evidence_plane="reported_text",
                operand_kind="canonical_scalar",
                operand=report_operand,
                declarations=report_items,
                candidate_paths=candidate_paths,
                scope_join_path=(scope_path[-1],),
            ),
            IndependentObservation(
                evidence_plane="static_source",
                operand_kind="canonical_scalar",
                operand=source_operand,
                declarations=source_items,
                candidate_paths=candidate_paths,
                scope_join_path=scope_path,
            ),
        )


def _validate_binding(binding: Mapping[str, Any]) -> None:
    if (
        binding.get("check_id") != _CHECK_ID
        or binding.get("dimension") != _DIMENSION
        or binding.get("comparison_form") != "value_equals"
        or binding.get("operand_kind") != "canonical_scalar"
        or binding.get("required_evidence_planes") != ["reported_text", "static_source"]
    ):
        raise TypedMethodQualificationError(
            "founder-orientation qualification binding is unsupported or drifted"
        )


def _assignment_payload(assignment: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = assignment.get("payload", assignment)
    if not isinstance(payload, Mapping):
        raise TypedMethodQualificationError("qualification assignment payload is malformed")
    return payload


def _strict_utf8_candidates(retained_bytes: Mapping[str, bytes]) -> dict[str, str]:
    if not retained_bytes:
        raise TypedMethodQualificationError("qualification retained-byte inventory is empty")
    decoded: dict[str, str] = {}
    for path, value in sorted(retained_bytes.items()):
        normalized = _required_path(path)
        if normalized != path or not isinstance(value, bytes):
            raise TypedMethodQualificationError(
                "qualification retained-byte inventory is noncanonical"
            )
        try:
            decoded[path] = value.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise TypedMethodQualificationError(
                f"qualification candidate is not strict UTF-8: {path}"
            ) from error
    return decoded


def _scope_path(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    raw = payload.get("scope_join_path")
    if (
        not isinstance(raw, Sequence)
        or isinstance(raw, (str, bytes))
        or len(raw) != len(_RELATIONS)
        or not all(isinstance(item, Mapping) for item in raw)
    ):
        raise TypedMethodQualificationError("qualification scope path is unavailable")
    path = tuple(dict(item) for item in raw if isinstance(item, Mapping))
    if tuple(item.get("relation") for item in path) != _RELATIONS:
        raise TypedMethodQualificationError("qualification scope relation sequence drifted")
    if any(
        path[index].get("target_ref") != path[index + 1].get("source_ref")
        for index in range(len(path) - 1)
    ):
        raise TypedMethodQualificationError("qualification scope path is discontinuous")
    if payload.get("scope_join_digest") != semantic_digest(path):
        raise TypedMethodQualificationError("qualification scope digest drifted")
    return path


def _required_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise TypedMethodQualificationError("qualification path is invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise TypedMethodQualificationError("qualification path is unsafe or noncanonical")
    return value


def _line_number(text: str, offset: int) -> int:
    if offset < 0 or offset > len(text):
        raise TypedMethodQualificationError("qualification declaration offset is invalid")
    return text.count("\n", 0, offset) + 1


def _retained_lines(text: str, start_line: int, end_line: int) -> str:
    lines = text.splitlines()
    retained = "\n".join(lines[start_line - 1 : end_line]).strip()
    if not retained:
        raise TypedMethodQualificationError("qualification source declaration is empty")
    return retained
