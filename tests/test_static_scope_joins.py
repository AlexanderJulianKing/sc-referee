from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.scientific_checks import (
    FrozenBaseRecord,
    RecordRef,
    ScientificCheckContractError,
    ScopeJoinEdge,
    ScopeJoinProof,
    StaticScopeJoinGraph,
)
from sc_referee.scientific_checks.scope_joins import (
    EXECUTION_INPUT_PROFILE,
    EXECUTION_OUTPUT_PROFILE,
    FULL_DIGEST_PROFILE,
    PUBLICATION_PROFILE,
    REVIEW_SELECTION_PROFILES,
    build_static_scope_join_graph,
    full_digest_identity_path,
    selected_review_path,
)

SNAPSHOT_DIGEST = sha256_digest("scope-join-test-snapshot")
LIMITATION = ("This test edge does not establish execution or correctness.",)


def _base(ref: RecordRef, value: dict[str, Any]) -> FrozenBaseRecord:
    return FrozenBaseRecord.from_record(ref, value)


def _identity(
    identity_ref: RecordRef,
    asset_ref: RecordRef,
    *,
    digest: str,
    tier: str = "full_digest",
) -> tuple[RecordRef, dict[str, Any]]:
    return (
        identity_ref,
        {
            "asset_identity_id": identity_ref.record_id,
            "tier": tier,
            "asset_ref": asset_ref.to_dict(),
            "identity_evidence": {
                "kind": "full_digest" if tier == "full_digest" else "sampled_fingerprint",
                "digest": digest,
            },
        },
    )


def _selection_projection(
    *, input_ref: RecordRef, identity_ref: RecordRef, path: str
) -> dict[str, Any]:
    empty = {
        "status": "unavailable",
        "selected_record_refs": [],
        "selected_identity_refs": [],
        "selected_paths": [],
        "selection_kind": "analysis_source",
    }
    value = {
        "profile": "bounded-review-scope-selection-v1",
        "source_snapshot_digest": SNAPSHOT_DIGEST,
        "snapshot_ref": {
            "record_type": "repository_snapshot",
            "record_id": "snapshot:test",
        },
        "selections": {
            "analysis_source": empty,
            "material_input": {
                "status": "selected_explicit_invocation",
                "selected_record_refs": [input_ref.to_dict()],
                "selected_identity_refs": [identity_ref.to_dict()],
                "selected_paths": [path],
                "selection_kind": "material_input",
            },
            "analysis_output": {**empty, "selection_kind": "analysis_output"},
        },
        "authority_limitation": "Review scope only.",
    }
    value["projection_digest"] = semantic_digest(value)
    return value


def _graph_fixture(
    *,
    include_selection: bool = True,
    imported_execution_refs: bool = True,
    broken_execution_input: bool = False,
) -> tuple[StaticScopeJoinGraph, dict[str, RecordRef]]:
    refs = {
        "snapshot": RecordRef("repository_snapshot", "snapshot:test"),
        "surface": RecordRef("publication_surface", "surface:test"),
        "report": RecordRef("artifact", "artifact:report"),
        "report_identity": RecordRef("asset_identity", "identity:report"),
        "input": RecordRef("artifact", "artifact:input"),
        "input_identity": RecordRef("asset_identity", "identity:input"),
        "execution": RecordRef("execution", "execution:imported"),
        "environment": RecordRef("environment", "environment:imported"),
    }
    records = [
        _base(refs["snapshot"], {"snapshot_id": refs["snapshot"].record_id}),
        _base(
            refs["surface"],
            {
                "publication_surface_id": refs["surface"].record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [refs["report"].to_dict()]},
            },
        ),
        _base(
            refs["report"],
            {
                "artifact_id": refs["report"].record_id,
                "kind": "report",
                "path": "report.md",
                "asset_identity_ref": refs["report_identity"].to_dict(),
            },
        ),
        _base(*_identity(refs["report_identity"], refs["report"], digest=sha256_digest("report"))),
        _base(
            refs["input"],
            {
                "artifact_id": refs["input"].record_id,
                "kind": "table",
                "path": "inputs.csv",
                "asset_identity_ref": refs["input_identity"].to_dict(),
            },
        ),
        _base(*_identity(refs["input_identity"], refs["input"], digest=sha256_digest("input"))),
        _base(
            refs["execution"],
            {
                "execution_id": refs["execution"].record_id,
                "input_refs": (
                    [
                        refs["input"].to_dict(),
                        RecordRef("artifact", "artifact:missing").to_dict(),
                    ]
                    if broken_execution_input
                    else [refs["input"].to_dict()]
                    if imported_execution_refs
                    else []
                ),
                "output_refs": [refs["report"].to_dict()] if imported_execution_refs else [],
                "environment_ref": refs["environment"].to_dict(),
            },
        ),
        _base(
            refs["environment"],
            {"environment_id": refs["environment"].record_id},
        ),
    ]
    graph = build_static_scope_join_graph(
        snapshot_digest=SNAPSHOT_DIGEST,
        snapshot_ref=refs["snapshot"],
        selected_surface_ref=refs["surface"],
        selected_artifact_ref=refs["report"],
        documents=(),
        base_records=tuple(records),
        scope_selections=(
            _selection_projection(
                input_ref=refs["input"],
                identity_ref=refs["input_identity"],
                path="inputs.csv",
            )
            if include_selection
            else None
        ),
    )
    return graph, refs


def _proof(
    source: RecordRef,
    relation: str,
    target: RecordRef,
    profile: str,
) -> ScopeJoinProof:
    return ScopeJoinProof.create(
        edge=ScopeJoinEdge(source, relation, target),
        profile=profile,
        evidence_refs=(source, target),
        evidence_payload_digests=(sha256_digest(f"{source.record_id}:{target.record_id}"),),
        snapshot_digest=SNAPSHOT_DIGEST,
        authority_limitations=LIMITATION,
    )


def test_general_graph_separates_identity_review_selection_and_execution_profiles() -> None:
    graph, refs = _graph_fixture()

    identity = full_digest_identity_path(
        graph,
        source_ref=refs["input"],
        snapshot_ref=refs["snapshot"],
    )
    selected = selected_review_path(
        graph,
        kind="material_input",
        source_ref=refs["input"],
        selected_surface_ref=refs["surface"],
    )
    execution = graph.unique_path(
        refs["input"],
        refs["surface"],
        profiles=(EXECUTION_INPUT_PROFILE, EXECUTION_OUTPUT_PROFILE, PUBLICATION_PROFILE),
    )

    assert [item.profile for item in identity] == [FULL_DIGEST_PROFILE]
    assert [item.profile for item in selected] == [REVIEW_SELECTION_PROFILES["material_input"]]
    assert [item.profile for item in execution] == [
        EXECUTION_INPUT_PROFILE,
        EXECUTION_OUTPUT_PROFILE,
        PUBLICATION_PROFILE,
    ]
    assert "does not establish execution" in selected[0].authority_limitations[0]


def test_multiparent_paths_and_cycles_fail_closed() -> None:
    source = RecordRef("artifact", "artifact:source")
    first = RecordRef("execution", "execution:first")
    second = RecordRef("execution", "execution:second")
    output = RecordRef("artifact", "artifact:output")
    surface = RecordRef("publication_surface", "surface:test")
    proofs = tuple(
        sorted(
            (
                _proof(source, "input_first", first, EXECUTION_INPUT_PROFILE),
                _proof(source, "input_second", second, EXECUTION_INPUT_PROFILE),
                _proof(first, "output_first", output, EXECUTION_OUTPUT_PROFILE),
                _proof(second, "output_second", output, EXECUTION_OUTPUT_PROFILE),
                _proof(output, "selected", surface, PUBLICATION_PROFILE),
                _proof(first, "cycle", source, EXECUTION_OUTPUT_PROFILE),
            ),
            key=lambda item: canonical_json(item.to_dict()),
        )
    )
    graph = StaticScopeJoinGraph(SNAPSHOT_DIGEST, proofs)

    assert (
        graph.unique_path(
            source,
            surface,
            profiles=(EXECUTION_INPUT_PROFILE, EXECUTION_OUTPUT_PROFILE, PUBLICATION_PROFILE),
        )
        == ()
    )


def test_same_path_record_conflict_and_weak_identity_are_not_admitted() -> None:
    graph, refs = _graph_fixture()
    first = RecordRef("artifact", "artifact:first-copy")
    second = RecordRef("artifact", "artifact:second-copy")
    first_identity = RecordRef("asset_identity", "identity:first-copy")
    second_identity = RecordRef("asset_identity", "identity:second-copy")
    weak = RecordRef("artifact", "artifact:weak")
    weak_identity = RecordRef("asset_identity", "identity:weak")
    base = [
        _base(refs["snapshot"], {"snapshot_id": refs["snapshot"].record_id}),
        *(
            _base(
                ref,
                {
                    "artifact_id": ref.record_id,
                    "path": "same.csv",
                    "asset_identity_ref": identity.to_dict(),
                },
            )
            for ref, identity in ((first, first_identity), (second, second_identity))
        ),
        _base(*_identity(first_identity, first, digest=sha256_digest("first"))),
        _base(*_identity(second_identity, second, digest=sha256_digest("second"))),
        _base(
            weak,
            {
                "artifact_id": weak.record_id,
                "path": "weak.csv",
                "asset_identity_ref": weak_identity.to_dict(),
            },
        ),
        _base(
            *_identity(
                weak_identity,
                weak,
                digest=sha256_digest("weak"),
                tier="sampled_fingerprint",
            )
        ),
    ]
    conflicted = build_static_scope_join_graph(
        snapshot_digest=SNAPSHOT_DIGEST,
        snapshot_ref=refs["snapshot"],
        selected_surface_ref=refs["surface"],
        selected_artifact_ref=refs["report"],
        documents=(),
        base_records=tuple(base),
    )

    assert not conflicted.proofs_for_profile(FULL_DIGEST_PROFILE)
    assert graph.proofs_for_profile(FULL_DIGEST_PROFILE)


def test_unselected_and_transformed_intermediate_paths_remain_disconnected() -> None:
    graph, refs = _graph_fixture(include_selection=False, imported_execution_refs=False)

    assert (
        selected_review_path(
            graph,
            kind="material_input",
            source_ref=refs["input"],
            selected_surface_ref=refs["surface"],
        )
        == ()
    )
    assert (
        graph.unique_path(
            refs["input"],
            refs["surface"],
            profiles=(EXECUTION_INPUT_PROFILE, EXECUTION_OUTPUT_PROFILE, PUBLICATION_PROFILE),
        )
        == ()
    )
    assert not graph.proofs_for_profile(EXECUTION_INPUT_PROFILE)
    assert not graph.proofs_for_profile(EXECUTION_OUTPUT_PROFILE)


def test_broken_execution_reference_list_does_not_admit_partial_input_edges() -> None:
    graph, _ = _graph_fixture(broken_execution_input=True)

    assert not graph.proofs_for_profile(EXECUTION_INPUT_PROFILE)
    assert graph.proofs_for_profile(EXECUTION_OUTPUT_PROFILE)


def test_profile_removal_is_local_and_graph_bytes_replay_deterministically() -> None:
    graph, refs = _graph_fixture()
    without_review = StaticScopeJoinGraph(
        snapshot_digest=graph.snapshot_digest,
        proofs=tuple(
            item
            for item in graph.proofs
            if item.profile != REVIEW_SELECTION_PROFILES["material_input"]
        ),
    )
    rebuilt, _ = _graph_fixture()

    assert (
        selected_review_path(
            without_review,
            kind="material_input",
            source_ref=refs["input"],
            selected_surface_ref=refs["surface"],
        )
        == ()
    )
    assert without_review.unique_path(
        refs["report"], refs["surface"], profiles=(PUBLICATION_PROFILE,)
    )
    assert canonical_json(graph.to_lock_projection()) == canonical_json(
        rebuilt.to_lock_projection()
    )
    assert graph.graph_digest == rebuilt.graph_digest


def test_proof_digest_mutation_is_rejected() -> None:
    graph, _ = _graph_fixture()
    with pytest.raises(ScientificCheckContractError, match="evidence digest mismatch"):
        replace(graph.proofs[0], authority_limitations=("Mutated limitation.",))
