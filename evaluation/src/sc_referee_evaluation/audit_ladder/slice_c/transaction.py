"""One all-or-nothing Slice-C verify, compose, and render transaction."""

from __future__ import annotations

from sc_referee.controller import ManifestBoundFrozenInspectionContext
from sc_referee_evaluation.audit_ladder.slice_c.composition import compose_world1_v1
from sc_referee_evaluation.audit_ladder.slice_c.core import (
    H5adFactsV1,
    SliceCContractError,
    SliceCRequestV1,
    WorkerControllerResultV1,
    canonical_json_bytes,
    sha256,
    validate_slice_c_request,
)
from sc_referee_evaluation.audit_ladder.slice_c.launcher import run_isolated_worker_v1
from sc_referee_evaluation.audit_ladder.slice_c.observations import (
    build_observations_v1,
    observation_runtime_premise_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.protocol import build_worker_request_v1
from sc_referee_evaluation.audit_ladder.slice_c.renderer import (
    RenderedSliceCReportV1,
    SliceCRendererError,
    render_world1_report_v1,
    renderer_runtime_premise_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.repository import (
    RepositoryAuthenticationError,
    authenticate_world1_context_v1,
    load_registry_bundle_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.runtime import (
    RuntimeAuthenticationError,
    read_runtime_artifacts_v1,
    validate_prelaunch_provenance_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.source import (
    SourceVerificationError,
    verify_world1_source_v1,
)


def _require_success(result: WorkerControllerResultV1) -> H5adFactsV1:
    if (
        type(result) is not WorkerControllerResultV1
        or result.facts is None
        or result.refusal is not None
    ):
        raise SliceCContractError("isolated worker did not produce authenticated facts")
    return result.facts


def _render_slice_c_artifacts_v1(
    context: ManifestBoundFrozenInspectionContext,
    request: SliceCRequestV1,
) -> RenderedSliceCReportV1 | None:
    # This check intentionally precedes resource/context inspection and any worker.
    validate_slice_c_request(request)
    try:
        registry = load_registry_bundle_v1()
        materials = authenticate_world1_context_v1(context, request, registry)
        private_request = request.to_dict()
        request_preimage = canonical_json_bytes(private_request)
        request_digest = sha256(request_preimage)
        if (
            len(request_preimage) != 112
            or request_digest
            != "sha256:f99eeb5740c53cf66e701cf06be40ad041c854f7f610f0bba7c90362dcf19f3b"
        ):
            raise SliceCContractError("private world-1 request identity differs")
        runtime_artifacts = read_runtime_artifacts_v1()
        validate_prelaunch_provenance_v1(
            runtime_artifacts=runtime_artifacts,
            protocol=registry.protocol,
            root_seal_bytes=registry.root_seal_bytes,
            root_seal=registry.root_seal,
            renderer=registry.renderer,
            observation_premise=observation_runtime_premise_v1(),
            renderer_premise=renderer_runtime_premise_v1(),
        )
        request_value, worker_request = build_worker_request_v1(
            registry=registry,
            materials=materials,
            request=request,
            runtime_artifacts=runtime_artifacts,
        )
        if request_value["slice_c_request"] != private_request:
            raise SliceCContractError("worker private request differs")

        primary_results = tuple(
            run_isolated_worker_v1(
                registry_raw=registry.protocol_bytes,
                request_raw=worker_request,
            )
            for _ in range(4)
        )
        primary_facts = tuple(_require_success(result) for result in primary_results)
        combined = H5adFactsV1(
            matrix_shape=primary_facts[0].matrix_shape,
            cardinality=primary_facts[1].cardinality,
            group_sizes=primary_facts[2].group_sizes,
            quoted_values=primary_facts[3].quoted_values,
        )
        source_fact = verify_world1_source_v1(materials.source_bytes)
        primary_observations = build_observations_v1(
            materials,
            request_digest,
            combined,
            source_fact,
        )

        replay_facts = _require_success(
            run_isolated_worker_v1(
                registry_raw=registry.protocol_bytes,
                request_raw=worker_request,
            )
        )
        replay_source = verify_world1_source_v1(materials.source_bytes)
        replay_observations = build_observations_v1(
            materials,
            request_digest,
            replay_facts,
            replay_source,
        )
        composition = compose_world1_v1(
            materials=materials,
            request_digest=request_digest,
            primary_observations=primary_observations,
            replay_h5ad_facts=replay_facts,
            replay_source_fact=replay_source,
            replay_observations=replay_observations,
        )
        return render_world1_report_v1(
            registry=registry,
            materials=materials,
            request_digest=request_digest,
            observations=primary_observations,
            composition=composition,
        )
    except (
        KeyError,
        OSError,
        RepositoryAuthenticationError,
        RuntimeAuthenticationError,
        SliceCContractError,
        SliceCRendererError,
        SourceVerificationError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return None


def render_slice_c_report_v1(
    context: ManifestBoundFrozenInspectionContext,
    request: SliceCRequestV1,
) -> bytes:
    """Return the exact M3 report or no bytes; invalid request objects raise."""

    validate_slice_c_request(request)
    rendered = _render_slice_c_artifacts_v1(context, request)
    return rendered.report_bytes if rendered is not None else b""


__all__ = ["render_slice_c_report_v1"]
