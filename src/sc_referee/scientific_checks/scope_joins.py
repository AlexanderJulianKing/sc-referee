from __future__ import annotations

import ast
import copy
import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    InspectionDocument,
    RecordRef,
    ScopeJoinEdge,
    ScopeJoinProof,
    StaticScopeJoinGraph,
)

PUBLICATION_PROFILE = "exact-publication-surface-selection"
CELL_PROFILE = "verified-active-cell-containment"
STATIC_WRITER_SOURCE_PROFILE = "unique-reachable-static-writer-source"
STATIC_WRITER_OUTPUT_PROFILE = "mutual-static-writer-output"
FULL_DIGEST_PROFILE = "full-digest-snapshot-identity"
EXECUTION_INPUT_PROFILE = "exact-execution-input-reference"
EXECUTION_OUTPUT_PROFILE = "exact-execution-output-reference"
EXECUTION_ENVIRONMENT_PROFILE = "exact-execution-environment-reference"
REVIEW_SELECTION_PROFILES = {
    "analysis_source": "selected-analysis-source-for-review",
    "material_input": "selected-material-input-for-review",
    "analysis_output": "selected-analysis-output-for-review",
}

_SELECTION_LIMITATION = (
    "Review selection does not establish execution, lineage, scientific intent, materiality, "
    "or correctness."
)
_STATIC_LIMITATION = (
    "Static connectivity does not establish that project code ran or produced snapshotted bytes."
)
_IDENTITY_LIMITATION = (
    "Full-digest identity establishes exact snapshotted bytes, not analysis use or semantics."
)
_EXECUTION_LIMITATION = (
    "An exact imported record reference is bounded evidence only and does not independently "
    "establish trustworthy execution."
)


def build_static_scope_join_graph(
    *,
    snapshot_digest: str,
    snapshot_ref: RecordRef,
    selected_surface_ref: RecordRef,
    selected_artifact_ref: RecordRef,
    documents: tuple[InspectionDocument, ...],
    base_records: tuple[FrozenBaseRecord, ...],
    scope_selections: dict[str, Any] | None = None,
) -> StaticScopeJoinGraph:
    """Compile closed, independently checked static edges from one immutable base view."""

    records = _base_record_index(base_records)
    proofs: list[ScopeJoinProof] = []
    publication = _publication_proof(
        snapshot_digest=snapshot_digest,
        selected_surface_ref=selected_surface_ref,
        selected_artifact_ref=selected_artifact_ref,
        records=records,
    )
    if publication is not None:
        proofs.append(publication)
        proofs.extend(
            _cell_proofs(
                snapshot_digest=snapshot_digest,
                selected_artifact_ref=selected_artifact_ref,
                documents=documents,
                records=records,
            )
        )
        proofs.extend(
            _static_writer_proofs(
                snapshot_digest=snapshot_digest,
                selected_artifact_ref=selected_artifact_ref,
                documents=documents,
                records=records,
            )
        )
    proofs.extend(
        _full_digest_proofs(
            snapshot_digest=snapshot_digest,
            snapshot_ref=snapshot_ref,
            records=records,
        )
    )
    proofs.extend(
        _review_selection_proofs(
            snapshot_digest=snapshot_digest,
            selected_surface_ref=selected_surface_ref,
            scope_selections=scope_selections,
            records=records,
        )
    )
    proofs.extend(_execution_proofs(snapshot_digest=snapshot_digest, records=records))
    return StaticScopeJoinGraph(
        snapshot_digest=snapshot_digest,
        proofs=_canonical_nonconflicting_proofs(proofs),
    )


def selected_publication_path(
    graph: StaticScopeJoinGraph | None,
    *,
    selected_artifact_ref: RecordRef,
    selected_surface_ref: RecordRef,
    relation: str,
) -> tuple[ScopeJoinEdge, ...]:
    if graph is None:
        return ()
    path = graph.unique_path(
        selected_artifact_ref,
        selected_surface_ref,
        profiles=(PUBLICATION_PROFILE,),
    )
    if len(path) != 1:
        return ()
    return (ScopeJoinEdge(selected_artifact_ref, relation, selected_surface_ref),)


def selected_container_path(
    graph: StaticScopeJoinGraph | None,
    *,
    document: InspectionDocument,
    selected_artifact_ref: RecordRef,
    selected_surface_ref: RecordRef,
) -> tuple[ScopeJoinEdge, ...]:
    if graph is None or document.parser_result_ref is None:
        return ()
    path = graph.unique_path(
        document.parser_result_ref,
        selected_surface_ref,
        profiles=(CELL_PROFILE, PUBLICATION_PROFILE),
    )
    if (
        len(path) != 2
        or path[0].edge.target_ref != selected_artifact_ref
        or path[1].edge.source_ref != selected_artifact_ref
    ):
        return ()
    return (
        ScopeJoinEdge(
            source_ref=document.file_ref,
            relation="contained_in_selected_source_artifact",
            target_ref=selected_artifact_ref,
        ),
        ScopeJoinEdge(
            source_ref=selected_artifact_ref,
            relation="selected_by_publication_surface",
            target_ref=selected_surface_ref,
        ),
    )


def selected_static_writer_path(
    graph: StaticScopeJoinGraph | None,
    *,
    document: InspectionDocument,
    selected_artifact_ref: RecordRef,
    selected_surface_ref: RecordRef,
) -> tuple[ScopeJoinEdge, ...]:
    if graph is None:
        return ()
    path = graph.unique_path(
        document.file_ref,
        selected_surface_ref,
        profiles=(
            STATIC_WRITER_SOURCE_PROFILE,
            STATIC_WRITER_OUTPUT_PROFILE,
            PUBLICATION_PROFILE,
        ),
    )
    if (
        len(path) != 3
        or path[1].edge.target_ref != selected_artifact_ref
        or path[2].edge.source_ref != selected_artifact_ref
    ):
        return ()
    return tuple(item.edge for item in path)


def selected_review_path(
    graph: StaticScopeJoinGraph | None,
    *,
    kind: str,
    source_ref: RecordRef,
    selected_surface_ref: RecordRef,
) -> tuple[ScopeJoinProof, ...]:
    profile = REVIEW_SELECTION_PROFILES.get(kind)
    if graph is None or profile is None:
        return ()
    return graph.unique_path(source_ref, selected_surface_ref, profiles=(profile,))


def full_digest_identity_path(
    graph: StaticScopeJoinGraph | None,
    *,
    source_ref: RecordRef,
    snapshot_ref: RecordRef,
) -> tuple[ScopeJoinProof, ...]:
    if graph is None:
        return ()
    return graph.unique_path(source_ref, snapshot_ref, profiles=(FULL_DIGEST_PROFILE,))


def _publication_proof(
    *,
    snapshot_digest: str,
    selected_surface_ref: RecordRef,
    selected_artifact_ref: RecordRef,
    records: dict[RecordRef, dict[str, Any]],
) -> ScopeJoinProof | None:
    surface = records.get(selected_surface_ref)
    artifact = records.get(selected_artifact_ref)
    identity_ref = _full_digest_identity_ref(artifact, selected_artifact_ref, records)
    if (
        surface is None
        or artifact is None
        or surface.get("status") != "resolved"
        or surface.get("selection", {}).get("selected_surface_refs")
        != [selected_artifact_ref.to_dict()]
        or identity_ref is None
    ):
        return None
    return _scope_proof(
        edge=ScopeJoinEdge(
            selected_artifact_ref,
            "selected_by_publication_surface",
            selected_surface_ref,
        ),
        profile=PUBLICATION_PROFILE,
        evidence_refs=(selected_artifact_ref, identity_ref, selected_surface_ref),
        records=records,
        snapshot_digest=snapshot_digest,
        authority_limitations=(_SELECTION_LIMITATION,),
    )


def _cell_proofs(
    *,
    snapshot_digest: str,
    selected_artifact_ref: RecordRef,
    documents: tuple[InspectionDocument, ...],
    records: dict[RecordRef, dict[str, Any]],
) -> list[ScopeJoinProof]:
    artifact = records.get(selected_artifact_ref)
    identity_ref = _full_digest_identity_ref(artifact, selected_artifact_ref, records)
    if artifact is None or identity_ref is None:
        return []
    digest = _full_digest(identity_ref, records)
    proofs: list[ScopeJoinProof] = []
    for document in documents:
        location = document.source_location
        if (
            location is None
            or location.source_kind not in {"notebook_cell", "document_chunk"}
            or document.parser_result_ref is None
            or document.parser_result_payload is None
            or artifact.get("kind") != "report"
            or artifact.get("path") != document.path
            or location.content_digest != digest
        ):
            continue
        try:
            parser = json.loads(document.parser_result_payload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        virtual = parser.get("extensions", {}).get("x-virtual-source")
        if not isinstance(virtual, dict) or virtual.get("executes_project_code") is not False:
            continue
        execution = virtual.get("execution_declaration")
        if (
            location.source_kind == "document_chunk"
            and isinstance(execution, dict)
            and execution.get("kind") == "quarto_eval_option"
            and execution.get("state") == "disabled_declared"
        ):
            continue
        proofs.append(
            _scope_proof(
                edge=ScopeJoinEdge(
                    document.parser_result_ref,
                    "contained_in_selected_source_artifact",
                    selected_artifact_ref,
                ),
                profile=CELL_PROFILE,
                evidence_refs=(document.file_ref, document.parser_result_ref, identity_ref),
                records=records,
                snapshot_digest=snapshot_digest,
                authority_limitations=(_STATIC_LIMITATION,),
            )
        )
    return proofs


def _static_writer_proofs(
    *,
    snapshot_digest: str,
    selected_artifact_ref: RecordRef,
    documents: tuple[InspectionDocument, ...],
    records: dict[RecordRef, dict[str, Any]],
) -> list[ScopeJoinProof]:
    selected = records.get(selected_artifact_ref)
    if selected is None or selected.get("kind") != "report":
        return []
    producer_values = selected.get("producer_operation_refs")
    if not isinstance(producer_values, list) or len(producer_values) != 1:
        return []
    producer_ref = _ref(producer_values[0])
    producer = records.get(producer_ref) if producer_ref is not None else None
    if producer_ref is None or producer is None:
        return []
    implementation = producer.get("implementation")
    implementation_name = (
        implementation.get("name") if isinstance(implementation, dict) else implementation
    )
    if (
        producer.get("inspection_status") != "supported"
        or not isinstance(implementation_name, str)
        or not implementation_name.endswith((".write_text", ".write_bytes"))
        or producer.get("output_refs") != [selected_artifact_ref.to_dict()]
    ):
        return []
    matched = [
        document
        for document in documents
        if _operation_belongs_to_document(producer, document)
        and _writer_is_statically_reachable(document, producer)
    ]
    if len(matched) != 1:
        return []
    document = matched[0]
    evidence = [document.file_ref, producer_ref, selected_artifact_ref]
    if document.parser_result_ref is not None:
        evidence.append(document.parser_result_ref)
    return [
        _scope_proof(
            edge=ScopeJoinEdge(
                document.file_ref,
                "contains_unique_static_selected_output_writer",
                producer_ref,
            ),
            profile=STATIC_WRITER_SOURCE_PROFILE,
            evidence_refs=evidence,
            records=records,
            snapshot_digest=snapshot_digest,
            authority_limitations=(_STATIC_LIMITATION,),
        ),
        _scope_proof(
            edge=ScopeJoinEdge(
                producer_ref,
                "declares_selected_output_artifact",
                selected_artifact_ref,
            ),
            profile=STATIC_WRITER_OUTPUT_PROFILE,
            evidence_refs=(producer_ref, selected_artifact_ref),
            records=records,
            snapshot_digest=snapshot_digest,
            authority_limitations=(_STATIC_LIMITATION,),
        ),
    ]


def _full_digest_proofs(
    *,
    snapshot_digest: str,
    snapshot_ref: RecordRef,
    records: dict[RecordRef, dict[str, Any]],
) -> list[ScopeJoinProof]:
    proofs: list[ScopeJoinProof] = []
    path_groups: dict[tuple[str, str], set[RecordRef]] = defaultdict(set)
    for ref, record in records.items():
        if ref.record_type in {"artifact", "file_record"} and _safe_path(record.get("path")):
            path_groups[(ref.record_type, str(record["path"]))].add(ref)
    for ref, record in records.items():
        if ref.record_type not in {"artifact", "file_record"}:
            continue
        path = record.get("path")
        if not _safe_path(path) or len(path_groups[(ref.record_type, str(path))]) != 1:
            continue
        identity_ref = _full_digest_identity_ref(record, ref, records)
        if identity_ref is None:
            continue
        proofs.append(
            _scope_proof(
                edge=ScopeJoinEdge(ref, "has_full_digest_in_snapshot", snapshot_ref),
                profile=FULL_DIGEST_PROFILE,
                evidence_refs=(ref, identity_ref, snapshot_ref),
                records=records,
                snapshot_digest=snapshot_digest,
                authority_limitations=(_IDENTITY_LIMITATION,),
            )
        )
    return proofs


def _review_selection_proofs(
    *,
    snapshot_digest: str,
    selected_surface_ref: RecordRef,
    scope_selections: dict[str, Any] | None,
    records: dict[RecordRef, dict[str, Any]],
) -> list[ScopeJoinProof]:
    if scope_selections is None:
        return []
    projection = copy.deepcopy(scope_selections)
    recorded_digest = projection.pop("projection_digest", None)
    if (
        semantic_digest(projection) != recorded_digest
        or scope_selections.get("profile") != "bounded-review-scope-selection-v1"
        or scope_selections.get("source_snapshot_digest") != snapshot_digest
    ):
        return []
    selections = scope_selections.get("selections")
    if not isinstance(selections, dict):
        return []
    proofs: list[ScopeJoinProof] = []
    for kind, profile in REVIEW_SELECTION_PROFILES.items():
        entry = selections.get(kind)
        if not isinstance(entry, dict) or entry.get("status") not in {
            "selected",
            "selected_explicit_invocation",
        }:
            continue
        refs = entry.get("selected_record_refs")
        identities = entry.get("selected_identity_refs")
        paths = entry.get("selected_paths")
        if not (
            isinstance(refs, list)
            and isinstance(identities, list)
            and isinstance(paths, list)
            and len(refs) == len(identities) == len(paths)
        ):
            continue
        for value, identity_value, path in zip(refs, identities, paths, strict=True):
            ref = _ref(value)
            identity_ref = _ref(identity_value)
            record = records.get(ref) if ref is not None else None
            same_path_refs = {
                candidate_ref
                for candidate_ref, candidate in records.items()
                if candidate_ref.record_type == (ref.record_type if ref is not None else "")
                and candidate.get("path") == path
            }
            if (
                ref is None
                or identity_ref is None
                or record is None
                or not _safe_path(path)
                or record.get("path") != path
                or len(same_path_refs) != 1
                or _full_digest_identity_ref(record, ref, records) != identity_ref
            ):
                continue
            evidence_refs = [ref, identity_ref, selected_surface_ref]
            for field in ("question_ref", "answer_ref"):
                evidence_ref = _ref(entry.get(field))
                if evidence_ref is not None and evidence_ref in records:
                    evidence_refs.append(evidence_ref)
            proofs.append(
                _scope_proof(
                    edge=ScopeJoinEdge(
                        ref,
                        f"selected_{kind}_for_review",
                        selected_surface_ref,
                    ),
                    profile=profile,
                    evidence_refs=evidence_refs,
                    records=records,
                    extra_payload_digests=(str(scope_selections["projection_digest"]),),
                    snapshot_digest=snapshot_digest,
                    authority_limitations=(_SELECTION_LIMITATION,),
                )
            )
    return proofs


def _execution_proofs(
    *, snapshot_digest: str, records: dict[RecordRef, dict[str, Any]]
) -> list[ScopeJoinProof]:
    proofs: list[ScopeJoinProof] = []
    for execution_ref, execution in records.items():
        if execution_ref.record_type != "execution":
            continue
        for value in _exact_ref_list(execution.get("input_refs"), records):
            proofs.append(
                _scope_proof(
                    edge=ScopeJoinEdge(value, "declared_input_of_execution", execution_ref),
                    profile=EXECUTION_INPUT_PROFILE,
                    evidence_refs=(value, execution_ref),
                    records=records,
                    snapshot_digest=snapshot_digest,
                    authority_limitations=(_EXECUTION_LIMITATION,),
                )
            )
        for value in _exact_ref_list(execution.get("output_refs"), records):
            proofs.append(
                _scope_proof(
                    edge=ScopeJoinEdge(execution_ref, "declared_output_of_execution", value),
                    profile=EXECUTION_OUTPUT_PROFILE,
                    evidence_refs=(execution_ref, value),
                    records=records,
                    snapshot_digest=snapshot_digest,
                    authority_limitations=(_EXECUTION_LIMITATION,),
                )
            )
        environment_ref = _ref(execution.get("environment_ref"))
        if environment_ref is not None and environment_ref in records:
            proofs.append(
                _scope_proof(
                    edge=ScopeJoinEdge(
                        execution_ref,
                        "declares_execution_environment",
                        environment_ref,
                    ),
                    profile=EXECUTION_ENVIRONMENT_PROFILE,
                    evidence_refs=(execution_ref, environment_ref),
                    records=records,
                    snapshot_digest=snapshot_digest,
                    authority_limitations=(_EXECUTION_LIMITATION,),
                )
            )
    return proofs


def _scope_proof(
    *,
    edge: ScopeJoinEdge,
    profile: str,
    evidence_refs: Iterable[RecordRef],
    records: dict[RecordRef, dict[str, Any]],
    snapshot_digest: str,
    authority_limitations: Iterable[str],
    extra_payload_digests: Iterable[str] = (),
) -> ScopeJoinProof:
    refs = tuple(evidence_refs)
    return ScopeJoinProof.create(
        edge=edge,
        profile=profile,
        evidence_refs=refs,
        evidence_payload_digests=(
            *(semantic_digest(records[ref]) for ref in refs),
            *extra_payload_digests,
        ),
        snapshot_digest=snapshot_digest,
        authority_limitations=tuple(authority_limitations),
    )


def _operation_belongs_to_document(operation: dict[str, Any], document: InspectionDocument) -> bool:
    refs = operation.get("source_refs")
    return (
        isinstance(refs, list)
        and len(refs) == 1
        and isinstance(refs[0], dict)
        and refs[0].get("source_kind") == "file_span"
        and refs[0].get("path") == document.path
        and refs[0].get("content_digest") == document.content_digest
    )


def _writer_is_statically_reachable(
    document: InspectionDocument, operation: dict[str, Any]
) -> bool:
    """Accept a module writer or one exact zero-argument guarded entrypoint."""

    try:
        tree = ast.parse(document.content.decode("utf-8"), filename=document.path)
    except (SyntaxError, UnicodeDecodeError):
        return False
    refs = operation.get("source_refs")
    if not isinstance(refs, list) or len(refs) != 1 or not isinstance(refs[0], dict):
        return False
    source = refs[0]
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"write_text", "write_bytes"}
        and node.lineno == source.get("start_line")
        and getattr(node, "end_lineno", node.lineno) == source.get("end_line")
        and node.col_offset + 1 == source.get("start_column")
        and getattr(node, "end_col_offset", node.col_offset) + 1 == source.get("end_column")
    ]
    if len(matches) != 1:
        return False
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    expression = parents.get(matches[0])
    if not isinstance(expression, ast.Expr):
        return False
    container = parents.get(expression)
    if isinstance(container, ast.Module):
        return True
    if not isinstance(container, ast.FunctionDef) or expression not in container.body:
        return False
    if container.decorator_list or not _zero_argument_function(container):
        return False
    definitions = [
        item
        for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == container.name
    ]
    guarded_calls = [
        item
        for statement in tree.body
        if isinstance(statement, ast.If) and _is_main_guard(statement)
        for item in statement.body
        if isinstance(item, ast.Expr)
        and isinstance(item.value, ast.Call)
        and isinstance(item.value.func, ast.Name)
        and item.value.func.id == container.name
        and not item.value.args
        and not item.value.keywords
    ]
    all_calls = [
        item
        for item in ast.walk(tree)
        if isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id == container.name
    ]
    return len(definitions) == len(guarded_calls) == len(all_calls) == 1


def _zero_argument_function(function: ast.FunctionDef) -> bool:
    arguments = function.args
    return not (
        arguments.posonlyargs
        or arguments.args
        or arguments.vararg is not None
        or arguments.kwonlyargs
        or arguments.kwarg is not None
        or arguments.defaults
        or any(item is not None for item in arguments.kw_defaults)
    )


def _is_main_guard(statement: ast.If) -> bool:
    test = statement.test
    return (
        not statement.orelse
        and isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == len(test.comparators) == 1
        and isinstance(test.ops[0], ast.Eq)
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def _base_record_index(
    records: tuple[FrozenBaseRecord, ...],
) -> dict[RecordRef, dict[str, Any]]:
    result: dict[RecordRef, dict[str, Any]] = {}
    for item in records:
        value = json.loads(item.canonical_payload)
        if isinstance(value, dict):
            result[item.ref] = value
    return result


def _full_digest_identity_ref(
    record: dict[str, Any] | None,
    record_ref: RecordRef,
    records: dict[RecordRef, dict[str, Any]],
) -> RecordRef | None:
    if record is None:
        return None
    identity_ref = _ref(record.get("asset_identity_ref"))
    identity = records.get(identity_ref) if identity_ref is not None else None
    evidence = identity.get("identity_evidence") if identity is not None else None
    if (
        identity_ref is None
        or identity is None
        or identity.get("tier") != "full_digest"
        or identity.get("asset_ref") != record_ref.to_dict()
        or not isinstance(evidence, dict)
        or evidence.get("kind") not in {None, "full_digest"}
        or not isinstance(evidence.get("digest"), str)
    ):
        return None
    return identity_ref


def _full_digest(identity_ref: RecordRef, records: dict[RecordRef, dict[str, Any]]) -> str | None:
    value = records.get(identity_ref, {}).get("identity_evidence", {}).get("digest")
    return str(value) if isinstance(value, str) else None


def _exact_ref_list(
    values: object, records: dict[RecordRef, dict[str, Any]]
) -> tuple[RecordRef, ...]:
    if not isinstance(values, list):
        return ()
    refs = tuple(value for item in values if (value := _ref(item)) is not None)
    if (
        len(refs) != len(values)
        or len(set(refs)) != len(refs)
        or any(value not in records for value in refs)
    ):
        return ()
    return refs


def _ref(value: object) -> RecordRef | None:
    if not isinstance(value, dict):
        return None
    record_type = value.get("record_type")
    record_id = value.get("record_id")
    if not isinstance(record_type, str) or not isinstance(record_id, str):
        return None
    try:
        return RecordRef(record_type, record_id)
    except ValueError:
        return None


def _safe_path(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts


def _canonical_nonconflicting_proofs(
    proofs: Iterable[ScopeJoinProof],
) -> tuple[ScopeJoinProof, ...]:
    grouped: dict[str, dict[str, ScopeJoinProof]] = defaultdict(dict)
    for proof in proofs:
        logical = canonical_json({"edge": proof.edge.to_dict(), "profile": proof.profile})
        grouped[logical][canonical_json(proof.to_dict())] = proof
    accepted = [next(iter(values.values())) for values in grouped.values() if len(values) == 1]
    return tuple(sorted(accepted, key=lambda item: canonical_json(item.to_dict())))
