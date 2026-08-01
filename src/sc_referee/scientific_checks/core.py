from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest

ObservationState = Literal["applicable", "not_applicable", "ambiguous", "unsupported"]
CompletenessState = Literal["complete", "incomplete", "not_applicable"]
EvidencePlane = Literal["reported_text", "static_source"]
OutputCeiling = Literal["question_only", "qualified_detector_request"]
OperandKind = Literal["canonical_scalar", "unique_string_array", "ordered_step_names"]
ReceiptKind = Literal["ambiguity", "sibling", "suppressor", "counterevidence"]
ReceiptState = Literal["passed", "triggered", "not_applicable", "unsupported"]
METHOD_CONFLICT_COUNTEREVIDENCE_PREDICATES = (
    "approved_method_deviation",
    "governing_protocol_amendment",
    "method_obligation_applicability",
)


class ScientificCheckContractError(ValueError):
    """Raised when a scientific-check value escapes the accepted closed contract."""


@dataclass(frozen=True, order=True)
class RecordRef:
    record_type: str
    record_id: str

    def __post_init__(self) -> None:
        _require_identifier(self.record_type, "record_type")
        _require_identifier(self.record_id, "record_id")

    def to_dict(self) -> dict[str, str]:
        return {"record_type": self.record_type, "record_id": self.record_id}


@dataclass(frozen=True)
class FrozenBaseRecord:
    """One canonical public base record exposed as immutable bytes, never a mutable store view."""

    ref: RecordRef
    canonical_payload: bytes
    payload_digest: str

    @classmethod
    def from_record(cls, ref: RecordRef, record: Mapping[str, Any]) -> FrozenBaseRecord:
        payload = canonical_json(record).encode("utf-8")
        return cls(ref=ref, canonical_payload=payload, payload_digest=sha256_digest(payload))

    def __post_init__(self) -> None:
        if sha256_digest(self.canonical_payload) != self.payload_digest:
            raise ScientificCheckContractError("frozen base-record digest mismatch")
        _require_canonical_object(self.canonical_payload, "frozen base record")


@dataclass(frozen=True, order=True)
class FrozenSourceLocation:
    """One immutable public SourceRef that identifies the bytes presented separately."""

    canonical_payload: bytes
    payload_digest: str

    @classmethod
    def from_source_ref(cls, source_ref: Mapping[str, Any]) -> FrozenSourceLocation:
        payload = canonical_json(source_ref).encode("utf-8")
        return cls(canonical_payload=payload, payload_digest=sha256_digest(payload))

    def __post_init__(self) -> None:
        if sha256_digest(self.canonical_payload) != self.payload_digest:
            raise ScientificCheckContractError("frozen source-location digest mismatch")
        _require_canonical_object(self.canonical_payload, "frozen source location")
        value = self.to_dict()
        source_kind = value.get("source_kind")
        locator = value.get("locator")
        path = value.get("path")
        content_digest = value.get("content_digest")
        if source_kind not in {"file_span", "notebook_cell", "document_chunk"}:
            raise ScientificCheckContractError("inspection source kind is unsupported")
        if not isinstance(locator, str) or not locator:
            raise ScientificCheckContractError("inspection source locator must not be empty")
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
            raise ScientificCheckContractError(
                "inspection source path must be relative and bounded"
            )
        if not isinstance(content_digest, str):
            raise ScientificCheckContractError("inspection source digest is unavailable")
        _require_sha256(content_digest, "inspection source digest")
        if source_kind == "notebook_cell" and not all(
            isinstance(value.get(field), str) and value[field] for field in ("cell_id", "selector")
        ):
            raise ScientificCheckContractError(
                "notebook-cell source requires exact cell and selector identities"
            )
        if source_kind == "document_chunk" and not (
            isinstance(value.get("chunk_label"), str) and value["chunk_label"]
        ):
            raise ScientificCheckContractError(
                "document-chunk source requires an exact chunk label"
            )

    def to_dict(self) -> dict[str, Any]:
        value = json.loads(self.canonical_payload)
        assert isinstance(value, dict)
        return value

    @property
    def source_kind(self) -> str:
        return str(self.to_dict()["source_kind"])

    @property
    def locator(self) -> str:
        return str(self.to_dict()["locator"])

    @property
    def path(self) -> str:
        return str(self.to_dict()["path"])

    @property
    def content_digest(self) -> str:
        return str(self.to_dict()["content_digest"])


@dataclass(frozen=True)
class InspectionDocument:
    """Immutable source bytes and their controller-owned parser result, if supported."""

    path: str
    file_ref: RecordRef
    content: bytes
    content_digest: str
    media_type: str
    parser_result_ref: RecordRef | None = None
    parser_result_payload: bytes | None = None
    parser_result_digest: str | None = None
    source_location: FrozenSourceLocation | None = None
    line_offset: int = 0

    def __post_init__(self) -> None:
        if not self.path or self.path.startswith("/") or ".." in self.path.split("/"):
            raise ScientificCheckContractError(
                "inspection document path must be relative and bounded"
            )
        _require_identifier(self.media_type, "media_type")
        if sha256_digest(self.content) != self.content_digest:
            raise ScientificCheckContractError("inspection document content digest mismatch")
        if self.source_location is None:
            object.__setattr__(
                self,
                "source_location",
                FrozenSourceLocation.from_source_ref(
                    {
                        "source_kind": "file_span",
                        "locator": self.path,
                        "path": self.path,
                        "content_digest": self.content_digest,
                    }
                ),
            )
        assert self.source_location is not None
        if self.source_location.path != self.path:
            raise ScientificCheckContractError(
                "inspection document and source-location paths differ"
            )
        if self.line_offset < 0:
            raise ScientificCheckContractError("inspection document line offset is invalid")
        if self.source_location.source_kind == "file_span":
            if self.source_location.content_digest != self.content_digest or self.line_offset != 0:
                raise ScientificCheckContractError(
                    "whole-file inspection bytes must match their public source identity"
                )
        elif self.source_location.source_kind == "notebook_cell" and self.line_offset != 0:
            raise ScientificCheckContractError(
                "notebook-cell evidence coordinates must remain cell-relative"
            )
        parser_fields = (
            self.parser_result_ref,
            self.parser_result_payload,
            self.parser_result_digest,
        )
        if any(value is not None for value in parser_fields) and not all(
            value is not None for value in parser_fields
        ):
            raise ScientificCheckContractError("parser result identity must be complete or absent")
        if self.parser_result_payload is not None:
            if sha256_digest(self.parser_result_payload) != self.parser_result_digest:
                raise ScientificCheckContractError("parser-result digest mismatch")
            _require_canonical_object(self.parser_result_payload, "parser result")

    @property
    def document_identity(self) -> str:
        assert self.source_location is not None
        return canonical_json(
            {
                "source_location_digest": self.source_location.payload_digest,
                "parser_result_ref": (
                    self.parser_result_ref.to_dict() if self.parser_result_ref is not None else None
                ),
            }
        )

    def evidence_source_ref(self, span: EvidenceSpan) -> dict[str, Any]:
        """Bind one adapter span back to this document's exact public source location."""

        assert self.source_location is not None
        if (
            span.file_ref != self.file_ref
            or span.path != self.path
            or span.content_digest != self.source_location.content_digest
            or span.parser_result_ref != self.parser_result_ref
        ):
            raise ScientificCheckContractError(
                "evidence span does not belong to its inspection document"
            )
        try:
            text = self.content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ScientificCheckContractError(
                "evidence source bytes are not strict UTF-8"
            ) from error
        lines = text.splitlines()
        relative_start = span.start_line - self.line_offset
        relative_end = span.end_line - self.line_offset
        if relative_start < 1 or relative_end < relative_start or relative_end > max(1, len(lines)):
            raise ScientificCheckContractError(
                "evidence span escapes its independently inspected source bytes"
            )
        quoted = "\n".join(lines[relative_start - 1 : relative_end])
        value = self.source_location.to_dict()
        value.update(
            {
                "locator": (
                    f"{span.path}:{span.start_line}-{span.end_line}"
                    if self.source_location.source_kind == "file_span"
                    else (
                        f"{self.source_location.locator}:evidence:{span.start_line}-{span.end_line}"
                    )
                ),
                "path": span.path,
                "content_digest": span.content_digest,
                "start_line": span.start_line,
                "end_line": span.end_line,
                "start_column": span.start_column,
                "end_column": span.end_column,
                "quoted_text": quoted,
            }
        )
        return value


@dataclass(frozen=True, order=True)
class ScopeJoinEdge:
    source_ref: RecordRef
    relation: str
    target_ref: RecordRef

    def __post_init__(self) -> None:
        _require_identifier(self.relation, "scope-join relation")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_ref": self.source_ref.to_dict(),
            "relation": self.relation,
            "target_ref": self.target_ref.to_dict(),
        }


@dataclass(frozen=True, order=True)
class ScopeJoinProof:
    """One independently supported internal edge; never an execution or correctness claim."""

    edge: ScopeJoinEdge
    profile: str
    evidence_refs: tuple[RecordRef, ...]
    evidence_payload_digests: tuple[str, ...]
    evidence_digest: str
    snapshot_digest: str
    authority_limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.profile, "scope-join profile")
        _require_sha256(self.evidence_digest, "scope-join evidence digest")
        _require_sha256(self.snapshot_digest, "scope-join snapshot digest")
        _require_unique(
            (canonical_json(item.to_dict()) for item in self.evidence_refs),
            "scope-join evidence references",
        )
        if not self.evidence_refs:
            raise ScientificCheckContractError("scope-join proof requires exact evidence")
        if not self.evidence_payload_digests:
            raise ScientificCheckContractError("scope-join proof requires bound evidence payloads")
        for digest in self.evidence_payload_digests:
            _require_sha256(digest, "scope-join evidence payload digest")
        if (
            not self.authority_limitations
            or len(self.authority_limitations) != len(set(self.authority_limitations))
            or any(not item for item in self.authority_limitations)
        ):
            raise ScientificCheckContractError(
                "scope-join authority limitations must be unique non-empty text"
            )
        expected = semantic_digest(self.evidence_projection())
        if expected != self.evidence_digest:
            raise ScientificCheckContractError("scope-join evidence digest mismatch")

    @classmethod
    def create(
        cls,
        *,
        edge: ScopeJoinEdge,
        profile: str,
        evidence_refs: Sequence[RecordRef],
        evidence_payload_digests: Sequence[str],
        snapshot_digest: str,
        authority_limitations: Sequence[str],
    ) -> ScopeJoinProof:
        normalized_refs = tuple(sorted(evidence_refs))
        normalized_payload_digests = tuple(sorted(evidence_payload_digests))
        normalized_limitations = tuple(sorted(authority_limitations))
        projection = {
            "edge": edge.to_dict(),
            "profile": profile,
            "evidence_refs": [item.to_dict() for item in normalized_refs],
            "evidence_payload_digests": list(normalized_payload_digests),
            "snapshot_digest": snapshot_digest,
            "authority_limitations": list(normalized_limitations),
        }
        return cls(
            edge=edge,
            profile=profile,
            evidence_refs=normalized_refs,
            evidence_payload_digests=normalized_payload_digests,
            evidence_digest=semantic_digest(projection),
            snapshot_digest=snapshot_digest,
            authority_limitations=normalized_limitations,
        )

    def evidence_projection(self) -> dict[str, Any]:
        return {
            "edge": self.edge.to_dict(),
            "profile": self.profile,
            "evidence_refs": [item.to_dict() for item in self.evidence_refs],
            "evidence_payload_digests": list(self.evidence_payload_digests),
            "snapshot_digest": self.snapshot_digest,
            "authority_limitations": list(self.authority_limitations),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.evidence_projection(), "evidence_digest": self.evidence_digest}


@dataclass(frozen=True)
class StaticScopeJoinGraph:
    """Canonical bounded graph shared by scientific and calculation adapters."""

    snapshot_digest: str
    proofs: tuple[ScopeJoinProof, ...]
    profile: str = "general-static-scope-join-v1"
    max_path_edges: int = 8

    def __post_init__(self) -> None:
        _require_sha256(self.snapshot_digest, "scope-join graph snapshot digest")
        _require_identifier(self.profile, "scope-join graph profile")
        if self.max_path_edges < 1 or self.max_path_edges > 32:
            raise ScientificCheckContractError("scope-join path ceiling is outside the bound")
        if any(item.snapshot_digest != self.snapshot_digest for item in self.proofs):
            raise ScientificCheckContractError("scope-join proof snapshot mismatch")
        ordered = tuple(sorted(self.proofs, key=lambda item: canonical_json(item.to_dict())))
        if ordered != self.proofs:
            raise ScientificCheckContractError("scope-join proofs are not canonical")
        keys = [
            canonical_json(
                {
                    "edge": item.edge.to_dict(),
                    "profile": item.profile,
                }
            )
            for item in self.proofs
        ]
        _require_unique(keys, "scope-join logical edges")

    @property
    def graph_digest(self) -> str:
        return semantic_digest(self.to_manifest_projection())

    def to_manifest_projection(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "snapshot_digest": self.snapshot_digest,
            "max_path_edges": self.max_path_edges,
            "proofs": [item.to_dict() for item in self.proofs],
        }

    def to_lock_projection(self) -> dict[str, Any]:
        value = self.to_manifest_projection()
        value["graph_digest"] = semantic_digest(value)
        return value

    def unique_path(
        self,
        source_ref: RecordRef,
        target_ref: RecordRef,
        *,
        profiles: Sequence[str],
    ) -> tuple[ScopeJoinProof, ...]:
        """Return one finite acyclic path, or fail closed on absence or ambiguity."""

        allowed = set(profiles)
        if not allowed or any(not item for item in allowed):
            raise ScientificCheckContractError("scope-join path profiles are invalid")
        adjacency: dict[RecordRef, list[ScopeJoinProof]] = {}
        for proof in self.proofs:
            if proof.profile in allowed:
                adjacency.setdefault(proof.edge.source_ref, []).append(proof)
        paths: list[tuple[ScopeJoinProof, ...]] = []

        def walk(
            current: RecordRef,
            path: tuple[ScopeJoinProof, ...],
            visited: frozenset[RecordRef],
        ) -> None:
            if len(paths) > 1 or len(path) >= self.max_path_edges:
                return
            for proof in adjacency.get(current, []):
                next_ref = proof.edge.target_ref
                if next_ref in visited:
                    continue
                candidate = (*path, proof)
                if next_ref == target_ref:
                    paths.append(candidate)
                    if len(paths) > 1:
                        return
                else:
                    walk(next_ref, candidate, visited | {next_ref})

        if source_ref == target_ref:
            return ()
        walk(source_ref, (), frozenset({source_ref}))
        return paths[0] if len(paths) == 1 else ()

    def proofs_for_profile(self, profile: str) -> tuple[ScopeJoinProof, ...]:
        return tuple(item for item in self.proofs if item.profile == profile)


@dataclass(frozen=True)
class FrozenInspectionContext:
    """The complete capability surface visible to every adapter in one registry evaluation."""

    snapshot_digest: str
    selected_surface_ref: RecordRef
    selected_artifact_ref: RecordRef
    documents: tuple[InspectionDocument, ...]
    base_records: tuple[FrozenBaseRecord, ...]
    shared_derivations: tuple[FrozenBaseRecord, ...] = ()
    scope_join_graph: StaticScopeJoinGraph | None = None

    def __post_init__(self) -> None:
        _require_sha256(self.snapshot_digest, "snapshot_digest")
        _require_unique(
            (item.document_identity for item in self.documents),
            "inspection document source identities",
        )
        _require_unique(
            (canonical_json(item.ref.to_dict()) for item in self.base_records),
            "base record references",
        )
        _require_unique(
            (canonical_json(item.ref.to_dict()) for item in self.shared_derivations),
            "shared derivation references",
        )
        base_refs = {item.ref for item in self.base_records}
        if (
            self.selected_surface_ref not in base_refs
            or self.selected_artifact_ref not in base_refs
        ):
            raise ScientificCheckContractError(
                "selected publication surface and artifact must be present in the frozen base view"
            )
        if (
            self.scope_join_graph is not None
            and self.scope_join_graph.snapshot_digest != self.snapshot_digest
        ):
            raise ScientificCheckContractError("scope-join graph is bound to another snapshot")

    @property
    def context_digest(self) -> str:
        return semantic_digest(self.to_manifest_projection())

    def to_manifest_projection(self) -> dict[str, Any]:
        return {
            "snapshot_digest": self.snapshot_digest,
            "selected_surface_ref": self.selected_surface_ref.to_dict(),
            "selected_artifact_ref": self.selected_artifact_ref.to_dict(),
            "documents": [
                {
                    "path": item.path,
                    "file_ref": item.file_ref.to_dict(),
                    "content_digest": item.content_digest,
                    "media_type": item.media_type,
                    "parser_result_ref": (
                        item.parser_result_ref.to_dict()
                        if item.parser_result_ref is not None
                        else None
                    ),
                    "parser_result_digest": item.parser_result_digest,
                    "source_location": (
                        item.source_location.to_dict() if item.source_location is not None else None
                    ),
                    "source_location_digest": (
                        item.source_location.payload_digest
                        if item.source_location is not None
                        else None
                    ),
                    "line_offset": item.line_offset,
                }
                for item in sorted(
                    self.documents,
                    key=lambda value: value.document_identity,
                )
            ],
            "base_records": [
                {"ref": item.ref.to_dict(), "payload_digest": item.payload_digest}
                for item in sorted(self.base_records, key=lambda value: value.ref)
            ],
            "shared_derivations": [
                {"ref": item.ref.to_dict(), "payload_digest": item.payload_digest}
                for item in sorted(self.shared_derivations, key=lambda value: value.ref)
            ],
            "scope_join_graph": (
                self.scope_join_graph.to_lock_projection()
                if self.scope_join_graph is not None
                else None
            ),
        }


@dataclass(frozen=True, order=True)
class RoleBinding:
    role: str
    value: str

    def __post_init__(self) -> None:
        _require_identifier(self.role, "semantic role")
        if not self.value:
            raise ScientificCheckContractError("semantic-role value must not be empty")

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "value": self.value}


@dataclass(frozen=True)
class CanonicalOperand:
    kind: OperandKind
    canonical_value: str

    @classmethod
    def scalar(cls, value: str | int | float | bool) -> CanonicalOperand:
        return cls("canonical_scalar", canonical_json(value))

    @classmethod
    def string_set(cls, values: Sequence[str]) -> CanonicalOperand:
        normalized = _validated_strings(values, preserve_order=False)
        return cls("unique_string_array", canonical_json(normalized))

    @classmethod
    def ordered_steps(cls, values: Sequence[str]) -> CanonicalOperand:
        normalized = _validated_strings(values, preserve_order=True)
        return cls("ordered_step_names", canonical_json(normalized))

    def __post_init__(self) -> None:
        try:
            value = json.loads(self.canonical_value)
        except json.JSONDecodeError as error:
            raise ScientificCheckContractError("operand value is not canonical JSON") from error
        if canonical_json(value) != self.canonical_value:
            raise ScientificCheckContractError("operand value is not canonically encoded")
        if self.kind == "canonical_scalar":
            if not isinstance(value, (str, int, float, bool)) or value is None:
                raise ScientificCheckContractError("canonical scalar has an invalid value")
            if isinstance(value, float) and not math.isfinite(value):
                raise ScientificCheckContractError("canonical scalar must be finite")
        elif self.kind == "unique_string_array":
            _validated_strings(value, preserve_order=False)
            if value != sorted(value):
                raise ScientificCheckContractError("set operand must use canonical sorted order")
        elif self.kind == "ordered_step_names":
            _validated_strings(value, preserve_order=True)

    @property
    def value(self) -> object:
        return json.loads(self.canonical_value)

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "value": self.value}


@dataclass(frozen=True, order=True)
class EvidenceSpan:
    file_ref: RecordRef
    path: str
    content_digest: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    parser_result_ref: RecordRef

    def __post_init__(self) -> None:
        if not self.path or self.path.startswith("/") or ".." in self.path.split("/"):
            raise ScientificCheckContractError("evidence path must be relative and bounded")
        _require_sha256(self.content_digest, "evidence content digest")
        if self.start_line < 1 or self.end_line < self.start_line:
            raise ScientificCheckContractError("evidence line span is invalid")
        if self.start_column < 0 or self.end_column < 0:
            raise ScientificCheckContractError("evidence columns must be non-negative")
        if self.start_line == self.end_line and self.end_column < self.start_column:
            raise ScientificCheckContractError("evidence column span is invalid")

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_ref": self.file_ref.to_dict(),
            "path": self.path,
            "content_digest": self.content_digest,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_column": self.start_column,
            "end_column": self.end_column,
            "parser_result_ref": self.parser_result_ref.to_dict(),
        }


@dataclass(frozen=True, order=True)
class InspectionReceipt:
    receipt_id: str
    kind: ReceiptKind
    state: ReceiptState
    evidence_digest: str
    description: str

    def __post_init__(self) -> None:
        _require_identifier(self.receipt_id, "receipt_id")
        _require_sha256(self.evidence_digest, "receipt evidence digest")
        if not self.description:
            raise ScientificCheckContractError("receipt description must not be empty")

    def to_dict(self) -> dict[str, str]:
        return {
            "receipt_id": self.receipt_id,
            "kind": self.kind,
            "state": self.state,
            "evidence_digest": self.evidence_digest,
            "description": self.description,
        }


@dataclass(frozen=True)
class NormalizedMethodObservation:
    check_id: str
    check_version: str
    check_manifest_digest: str
    check_implementation_digest: str
    adapter_id: str
    adapter_version: str
    adapter_manifest_digest: str
    adapter_implementation_digest: str
    parser_id: str
    parser_version: str
    applicability: ObservationState
    completeness: CompletenessState
    evidence_plane: EvidencePlane
    method_target_ref: RecordRef | None
    role_bindings: tuple[RoleBinding, ...]
    observed_operand: CanonicalOperand | None
    evidence_spans: tuple[EvidenceSpan, ...]
    scope_join_path: tuple[ScopeJoinEdge, ...]
    receipts: tuple[InspectionReceipt, ...]
    non_inferences: tuple[str, ...]
    output_ceiling: OutputCeiling
    abstention_reason: str | None = None

    def __post_init__(self) -> None:
        for value, label in (
            (self.check_id, "check_id"),
            (self.check_version, "check_version"),
            (self.adapter_id, "adapter_id"),
            (self.adapter_version, "adapter_version"),
            (self.parser_id, "parser_id"),
            (self.parser_version, "parser_version"),
        ):
            _require_identifier(value, label)
        for value, label in (
            (self.check_manifest_digest, "check manifest digest"),
            (self.check_implementation_digest, "check implementation digest"),
            (self.adapter_manifest_digest, "adapter manifest digest"),
            (self.adapter_implementation_digest, "adapter implementation digest"),
        ):
            _require_sha256(value, label)
        _require_unique((item.role for item in self.role_bindings), "semantic roles")
        _require_unique((item.receipt_id for item in self.receipts), "inspection receipt IDs")
        if len(set(self.non_inferences)) != len(self.non_inferences) or any(
            not item for item in self.non_inferences
        ):
            raise ScientificCheckContractError("non-inferences must be unique non-empty text")
        material = (
            self.method_target_ref is not None
            and self.observed_operand is not None
            and bool(self.evidence_spans)
            and bool(self.scope_join_path)
        )
        if self.applicability == "applicable":
            if (
                self.completeness != "complete"
                or not material
                or self.abstention_reason is not None
            ):
                raise ScientificCheckContractError(
                    "applicable observation must be complete, evidenced, scoped, and non-abstaining"
                )
            if any(receipt.state not in {"passed", "not_applicable"} for receipt in self.receipts):
                raise ScientificCheckContractError(
                    "applicable observation has an unresolved finite inspection receipt"
                )
        else:
            if not self.abstention_reason:
                raise ScientificCheckContractError("closed abstention requires a reason")
            if self.applicability == "not_applicable" and self.observed_operand is not None:
                raise ScientificCheckContractError(
                    "not-applicable abstention cannot expose an observed operand"
                )
            if self.observed_operand is not None and (
                self.applicability != "unsupported"
                or self.method_target_ref is None
                or not self.evidence_spans
                or self.scope_join_path
                or self.completeness != "incomplete"
            ):
                raise ScientificCheckContractError(
                    "only an exact but unscoped unsupported observation may preserve an operand"
                )

    @property
    def observation_digest(self) -> str:
        return semantic_digest(self.to_dict())

    @property
    def equivalence_key(self) -> str:
        if self.applicability != "applicable":
            return self.observation_digest
        return semantic_digest(
            {
                "method_target_ref": (
                    self.method_target_ref.to_dict() if self.method_target_ref is not None else None
                ),
                "observed_operand": (
                    self.observed_operand.to_dict() if self.observed_operand is not None else None
                ),
                "evidence_plane": self.evidence_plane,
                "scope_join_path": [item.to_dict() for item in self.scope_join_path],
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_profile": "normalized_method_observation_v1",
            "check_id": self.check_id,
            "check_version": self.check_version,
            "check_manifest_digest": self.check_manifest_digest,
            "check_implementation_digest": self.check_implementation_digest,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "adapter_manifest_digest": self.adapter_manifest_digest,
            "adapter_implementation_digest": self.adapter_implementation_digest,
            "parser_id": self.parser_id,
            "parser_version": self.parser_version,
            "applicability": self.applicability,
            "completeness": self.completeness,
            "evidence_plane": self.evidence_plane,
            "method_target_ref": (
                self.method_target_ref.to_dict() if self.method_target_ref is not None else None
            ),
            "role_bindings": [item.to_dict() for item in sorted(self.role_bindings)],
            "observed_operand": (
                self.observed_operand.to_dict() if self.observed_operand is not None else None
            ),
            "evidence_spans": [item.to_dict() for item in sorted(self.evidence_spans)],
            "scope_join_path": [item.to_dict() for item in self.scope_join_path],
            "receipts": [item.to_dict() for item in sorted(self.receipts)],
            "non_inferences": sorted(self.non_inferences),
            "output_ceiling": self.output_ceiling,
            "abstention_reason": self.abstention_reason,
        }


@dataclass(frozen=True)
class RequirementCandidate:
    candidate_id: str
    label: str
    operand: CanonicalOperand
    authority_basis: str

    def __post_init__(self) -> None:
        _require_identifier(self.candidate_id, "candidate_id")
        if not self.label or not self.authority_basis:
            raise ScientificCheckContractError(
                "requirement candidate label and authority basis must not be empty"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "label": self.label,
            "operand": self.operand.to_dict(),
            "authority_basis": self.authority_basis,
        }


@dataclass(frozen=True)
class AdapterManifest:
    adapter_id: str
    adapter_version: str
    implementation_digest: str
    recognition_grammar_digest: str
    parser_id: str
    parser_version: str
    source_language: str
    evidence_plane: EvidencePlane
    semantic_roles: tuple[str, ...]
    applicability_profile: str
    counterevidence_profiles: tuple[str, ...]
    known_gaps: tuple[str, ...]

    def __post_init__(self) -> None:
        for value, label in (
            (self.adapter_id, "adapter_id"),
            (self.adapter_version, "adapter_version"),
            (self.parser_id, "parser_id"),
            (self.parser_version, "parser_version"),
            (self.source_language, "source_language"),
            (self.applicability_profile, "applicability_profile"),
        ):
            _require_identifier(value, label)
        _require_sha256(self.implementation_digest, "adapter implementation digest")
        _require_sha256(self.recognition_grammar_digest, "adapter recognition grammar digest")
        _require_unique(self.semantic_roles, "adapter semantic roles")
        _require_unique(self.counterevidence_profiles, "counterevidence profiles")
        if not self.semantic_roles or not self.counterevidence_profiles:
            raise ScientificCheckContractError(
                "adapter roles and finite counterevidence profiles must not be empty"
            )

    @property
    def manifest_digest(self) -> str:
        return semantic_digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "implementation_digest": self.implementation_digest,
            "recognition_grammar_digest": self.recognition_grammar_digest,
            "parser_id": self.parser_id,
            "parser_version": self.parser_version,
            "source_language": self.source_language,
            "evidence_plane": self.evidence_plane,
            "semantic_roles": sorted(self.semantic_roles),
            "applicability_profile": self.applicability_profile,
            "counterevidence_profiles": sorted(self.counterevidence_profiles),
            "known_gaps": sorted(self.known_gaps),
        }


@dataclass(frozen=True)
class CheckManifest:
    check_id: str
    check_version: str
    implementation_digest: str
    maturity_tier: OutputCeiling
    dimension: str
    comparison_form: str
    requirement_candidates: tuple[RequirementCandidate, ...]
    semantic_roles: tuple[str, ...]
    required_record_types: tuple[str, ...]
    permitted_wording: str
    prohibited_inferences: tuple[str, ...]
    production_finding_permitted: bool = False

    def __post_init__(self) -> None:
        for value, label in (
            (self.check_id, "check_id"),
            (self.check_version, "check_version"),
            (self.dimension, "dimension"),
            (self.comparison_form, "comparison_form"),
        ):
            _require_identifier(value, label)
        _require_sha256(self.implementation_digest, "check implementation digest")
        _require_unique(
            (item.candidate_id for item in self.requirement_candidates),
            "requirement candidate IDs",
        )
        _require_unique(self.semantic_roles, "check semantic roles")
        _require_unique(self.required_record_types, "required record types")
        if (
            not self.requirement_candidates
            or not self.semantic_roles
            or not self.required_record_types
        ):
            raise ScientificCheckContractError(
                "check candidates, semantic roles, and required record types must not be empty"
            )
        if not self.permitted_wording or not self.prohibited_inferences:
            raise ScientificCheckContractError(
                "check wording and prohibited inferences must be explicit"
            )
        if self.production_finding_permitted or self.maturity_tier != "question_only":
            raise ScientificCheckContractError(
                "the ADR-0020 first slice is experimental question-only and Finding-ineligible"
            )

    @property
    def manifest_digest(self) -> str:
        return semantic_digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "check_version": self.check_version,
            "implementation_digest": self.implementation_digest,
            "maturity_tier": self.maturity_tier,
            "dimension": self.dimension,
            "comparison_form": self.comparison_form,
            "requirement_candidates": [
                item.to_dict()
                for item in sorted(self.requirement_candidates, key=lambda item: item.candidate_id)
            ],
            "semantic_roles": sorted(self.semantic_roles),
            "required_record_types": sorted(self.required_record_types),
            "permitted_wording": self.permitted_wording,
            "prohibited_inferences": sorted(self.prohibited_inferences),
            "production_finding_permitted": self.production_finding_permitted,
        }


@dataclass(frozen=True)
class MethodConflictBinding:
    """One explicit, content-addressed route from a scientific check to a detector family."""

    binding_id: str
    check_id: str
    check_version: str
    check_manifest_digest: str
    detector_id: str
    detector_version: str
    detector_manifest_digest: str
    dimension: str
    comparison_form: str
    operand_kind: OperandKind
    required_evidence_planes: tuple[EvidencePlane, ...]
    required_semantic_roles: tuple[str, ...]
    required_assertion_roles: tuple[str, ...]
    counterevidence_predicates: tuple[str, ...]
    forbidden_members: tuple[str, ...] = ()
    production_finding_permitted: bool = False

    def __post_init__(self) -> None:
        for value, label in (
            (self.binding_id, "binding_id"),
            (self.check_id, "check_id"),
            (self.check_version, "check_version"),
            (self.detector_id, "detector_id"),
            (self.detector_version, "detector_version"),
            (self.dimension, "dimension"),
            (self.comparison_form, "comparison_form"),
        ):
            _require_identifier(value, label)
        _require_sha256(self.check_manifest_digest, "binding check manifest digest")
        _require_sha256(self.detector_manifest_digest, "binding detector manifest digest")
        _require_unique(self.required_evidence_planes, "binding evidence planes")
        _require_unique(self.required_semantic_roles, "binding semantic roles")
        _require_unique(self.required_assertion_roles, "binding assertion roles")
        _require_unique(self.counterevidence_predicates, "binding counterevidence predicates")
        _require_unique(self.forbidden_members, "binding forbidden members")
        if (
            not self.required_evidence_planes
            or not self.required_semantic_roles
            or not self.required_assertion_roles
            or not self.counterevidence_predicates
        ):
            raise ScientificCheckContractError(
                "method-conflict binding planes, roles, and counterevidence must be explicit"
            )
        expected_assertion_roles = {
            "reported" if plane == "reported_text" else "observed"
            for plane in self.required_evidence_planes
        }
        if set(self.required_assertion_roles) != expected_assertion_roles:
            raise ScientificCheckContractError(
                "method-conflict binding assertion roles must exactly match its evidence planes"
            )
        if self.comparison_form == "value_equals" and self.operand_kind != "canonical_scalar":
            raise ScientificCheckContractError("value_equals requires a canonical scalar binding")
        if self.comparison_form == "set_relation" and self.operand_kind != "unique_string_array":
            raise ScientificCheckContractError("set_relation requires a string-set binding")
        if self.comparison_form == "step_precedes" and self.operand_kind != "ordered_step_names":
            raise ScientificCheckContractError("step_precedes requires an ordered-step binding")
        if self.comparison_form not in {"value_equals", "set_relation", "step_precedes"}:
            raise ScientificCheckContractError("method-conflict comparison form is unsupported")
        if self.comparison_form != "set_relation" and self.forbidden_members:
            raise ScientificCheckContractError(
                "forbidden members are valid only for set-relation bindings"
            )
        if self.production_finding_permitted:
            raise ScientificCheckContractError(
                "experimental method-conflict bindings cannot permit Findings"
            )
        if set(self.counterevidence_predicates) != set(METHOD_CONFLICT_COUNTEREVIDENCE_PREDICATES):
            raise ScientificCheckContractError(
                "method-conflict binding must preserve the finite predicate protocol"
            )

    @property
    def binding_digest(self) -> str:
        return semantic_digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "check_id": self.check_id,
            "check_version": self.check_version,
            "check_manifest_digest": self.check_manifest_digest,
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "detector_manifest_digest": self.detector_manifest_digest,
            "dimension": self.dimension,
            "comparison_form": self.comparison_form,
            "operand_kind": self.operand_kind,
            "required_evidence_planes": sorted(self.required_evidence_planes),
            "required_semantic_roles": sorted(self.required_semantic_roles),
            "required_assertion_roles": sorted(self.required_assertion_roles),
            "counterevidence_predicates": sorted(self.counterevidence_predicates),
            "forbidden_members": sorted(self.forbidden_members),
            "production_finding_permitted": self.production_finding_permitted,
        }


class ScientificCheckAdapter(Protocol):
    @property
    def adapter_id(self) -> str: ...

    @property
    def adapter_version(self) -> str: ...

    @property
    def implementation_digest(self) -> str: ...

    @property
    def recognition_grammar_digest(self) -> str: ...

    def inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation: ...


@dataclass(frozen=True)
class ScientificCheckModule:
    manifest: CheckManifest
    declared_manifest_digest: str
    adapter_manifests: tuple[AdapterManifest, ...]
    adapters: tuple[ScientificCheckAdapter, ...]


def _require_identifier(value: str, label: str) -> None:
    if not value or value.strip() != value or any(character.isspace() for character in value):
        raise ScientificCheckContractError(f"{label} must be a non-empty token")


def _require_sha256(value: str, label: str) -> None:
    if len(value) != 71 or not value.startswith("sha256:"):
        raise ScientificCheckContractError(f"{label} must be a sha256 digest")
    try:
        int(value[7:], 16)
    except ValueError as error:
        raise ScientificCheckContractError(f"{label} must be a sha256 digest") from error


def _require_unique(values: Sequence[str] | Any, label: str) -> None:
    normalized = tuple(values)
    if len(normalized) != len(set(normalized)):
        raise ScientificCheckContractError(f"{label} must be unique")


def _require_canonical_object(payload: bytes, label: str) -> None:
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ScientificCheckContractError(f"{label} is not valid JSON") from error
    if not isinstance(value, Mapping) or canonical_json(value).encode("utf-8") != payload:
        raise ScientificCheckContractError(f"{label} is not a canonical JSON object")


def _validated_strings(value: object, *, preserve_order: bool) -> list[str]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not value
        or not all(isinstance(item, str) and item for item in value)
    ):
        raise ScientificCheckContractError("operand must be a non-empty string array")
    normalized = list(value)
    if len(normalized) != len(set(normalized)):
        raise ScientificCheckContractError("operand strings must be unique")
    return normalized if preserve_order else sorted(normalized)
