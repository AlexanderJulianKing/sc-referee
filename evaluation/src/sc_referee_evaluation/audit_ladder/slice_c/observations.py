"""Closed Finding-ineligible observation records and identity replay."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final, TypeAlias, cast

from sc_referee_evaluation.audit_ladder.slice_c.core import (
    FactV1,
    H5adFactsV1,
    MatrixShapeFactV1,
    ObsColumnCardinalityFactV1,
    ObsColumnQuotedValuesFactV1,
    ObsGroupSizesFactV1,
    SliceCContractError,
    canonical_json_bytes,
    is_sha256,
    sha256,
    validate_h5ad_facts,
)
from sc_referee_evaluation.audit_ladder.slice_c.repository import CapturedWorld1MaterialsV1
from sc_referee_evaluation.audit_ladder.slice_c.source import SourceFlowFactV1

_RUNTIME_PREMISE_ID: Final = "scanpy-1.11.5-cpython-3.11.15-macos-arm64-v1"
_RUNTIME_PREMISE_DIGEST: Final = (
    "sha256:09fe04ea03c03221bf20c00b5e45cd8f66f00d7476f98da64df5dcde79dc7eeb"
)
_H5AD_SCHEMA: Final = "slice-c-h5ad-observation-v1"
_SOURCE_SCHEMA: Final = "slice-c-source-observation-v1"
_H5AD_VERIFIER: Final = "slice-c-h5ad-v1"
_SOURCE_VERIFIER: Final = "slice-c-source-v1"
_H5AD_KINDS: Final = (
    "matrix-shape",
    "obs-column-cardinality",
    "obs-group-sizes",
    "obs-column-quoted-values",
)
_EXPECTED_OBSERVATION_IDS: Final = (
    "obs:1d6a83a034d0d3b0705b",
    "obs:232ffa8bb5506c13888e",
    "obs:08dd62bb5effa4255b37",
    "obs:761e7b80857df5fde69a",
    "obs:56249cd61506b8fb3f02",
)


@dataclass(frozen=True, slots=True)
class H5adObservationV1:
    schema: str
    observation_id: str
    request_digest: str
    snapshot_ref: str
    file_ref: str
    file_sha256: str
    kind: str
    fact: FactV1
    verifier_version: str
    runtime_premise_id: str
    runtime_premise_digest: str
    finding_eligible: bool

    def to_dict(self, *, include_id: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "fact": self.fact.to_dict(),
            "file_ref": self.file_ref,
            "file_sha256": self.file_sha256,
            "finding_eligible": self.finding_eligible,
            "kind": self.kind,
            "request_digest": self.request_digest,
            "runtime_premise_digest": self.runtime_premise_digest,
            "runtime_premise_id": self.runtime_premise_id,
            "schema": self.schema,
            "snapshot_ref": self.snapshot_ref,
            "verifier_version": self.verifier_version,
        }
        if include_id:
            value["observation_id"] = self.observation_id
        return value


@dataclass(frozen=True, slots=True)
class SourceObservationV1:
    schema: str
    observation_id: str
    request_digest: str
    snapshot_ref: str
    file_ref: str
    file_sha256: str
    kind: str
    fact: SourceFlowFactV1
    verifier_version: str
    finding_eligible: bool

    def to_dict(self, *, include_id: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "fact": self.fact.to_dict(),
            "file_ref": self.file_ref,
            "file_sha256": self.file_sha256,
            "finding_eligible": self.finding_eligible,
            "kind": self.kind,
            "request_digest": self.request_digest,
            "schema": self.schema,
            "snapshot_ref": self.snapshot_ref,
            "verifier_version": self.verifier_version,
        }
        if include_id:
            value["observation_id"] = self.observation_id
        return value


ObservationV1: TypeAlias = H5adObservationV1 | SourceObservationV1
ObservationSetV1: TypeAlias = tuple[
    H5adObservationV1,
    H5adObservationV1,
    H5adObservationV1,
    H5adObservationV1,
    SourceObservationV1,
]


def observation_runtime_premise_v1() -> tuple[str, str]:
    """Return the independently fixed observation provenance carrier."""

    return _RUNTIME_PREMISE_ID, _RUNTIME_PREMISE_DIGEST


def _observation_id(value: ObservationV1) -> str:
    return "obs:" + sha256(canonical_json_bytes(value.to_dict(include_id=False)))[7:27]


def _build_h5ad_observation(
    materials: CapturedWorld1MaterialsV1,
    request_digest: str,
    kind: str,
    fact: FactV1,
) -> H5adObservationV1:
    provisional = H5adObservationV1(
        schema=_H5AD_SCHEMA,
        observation_id="",
        request_digest=request_digest,
        snapshot_ref=materials.snapshot_ref,
        file_ref=materials.h5ad_file_ref,
        file_sha256=materials.h5ad_digest,
        kind=kind,
        fact=fact,
        verifier_version=_H5AD_VERIFIER,
        runtime_premise_id=_RUNTIME_PREMISE_ID,
        runtime_premise_digest=_RUNTIME_PREMISE_DIGEST,
        finding_eligible=False,
    )
    return replace(provisional, observation_id=_observation_id(provisional))


def build_observations_v1(
    materials: CapturedWorld1MaterialsV1,
    request_digest: str,
    h5ad_facts: H5adFactsV1,
    source_fact: SourceFlowFactV1,
) -> ObservationSetV1:
    """Construct the exact ranked observation set from independently verified facts."""

    validate_h5ad_facts(h5ad_facts)
    h5ad: tuple[tuple[str, FactV1], ...] = (
        ("matrix-shape", h5ad_facts.matrix_shape),
        ("obs-column-cardinality", h5ad_facts.cardinality),
        ("obs-group-sizes", h5ad_facts.group_sizes),
        ("obs-column-quoted-values", h5ad_facts.quoted_values),
    )
    primary = tuple(
        _build_h5ad_observation(materials, request_digest, kind, fact) for kind, fact in h5ad
    )
    source_provisional = SourceObservationV1(
        schema=_SOURCE_SCHEMA,
        observation_id="",
        request_digest=request_digest,
        snapshot_ref=materials.snapshot_ref,
        file_ref=materials.source_file_ref,
        file_sha256=materials.source_digest,
        kind="world1-closed-flow",
        fact=source_fact,
        verifier_version=_SOURCE_VERIFIER,
        finding_eligible=False,
    )
    source = replace(source_provisional, observation_id=_observation_id(source_provisional))
    result = cast(ObservationSetV1, (*primary, source))
    validate_observations_v1(result, materials=materials, request_digest=request_digest)
    return result


def validate_observations_v1(
    observations: ObservationSetV1,
    *,
    materials: CapturedWorld1MaterialsV1,
    request_digest: str,
) -> None:
    if type(observations) is not tuple or len(observations) != 5 or not is_sha256(request_digest):
        raise SliceCContractError("observation set shape or request identity differs")
    for index, observation in enumerate(observations[:4]):
        if (
            type(observation) is not H5adObservationV1
            or observation.schema != _H5AD_SCHEMA
            or observation.kind != _H5AD_KINDS[index]
            or observation.verifier_version != _H5AD_VERIFIER
            or observation.request_digest != request_digest
            or observation.snapshot_ref != materials.snapshot_ref
            or observation.file_ref != materials.h5ad_file_ref
            or observation.file_sha256 != materials.h5ad_digest
            or observation.runtime_premise_id != _RUNTIME_PREMISE_ID
            or observation.runtime_premise_digest != _RUNTIME_PREMISE_DIGEST
            or observation.finding_eligible is not False
            or observation.observation_id != _observation_id(observation)
        ):
            raise SliceCContractError("H5AD observation provenance or identity differs")
    expected_fact_types = (
        MatrixShapeFactV1,
        ObsColumnCardinalityFactV1,
        ObsGroupSizesFactV1,
        ObsColumnQuotedValuesFactV1,
    )
    if any(
        type(observation.fact) is not expected
        for observation, expected in zip(observations[:4], expected_fact_types, strict=True)
    ):
        raise SliceCContractError("H5AD observation fact variant differs")
    source = observations[4]
    if (
        type(source) is not SourceObservationV1
        or source.schema != _SOURCE_SCHEMA
        or source.kind != "world1-closed-flow"
        or type(source.fact) is not SourceFlowFactV1
        or source.verifier_version != _SOURCE_VERIFIER
        or source.request_digest != request_digest
        or source.snapshot_ref != materials.snapshot_ref
        or source.file_ref != materials.source_file_ref
        or source.file_sha256 != materials.source_digest
        or source.finding_eligible is not False
        or source.observation_id != _observation_id(source)
    ):
        raise SliceCContractError("source observation provenance or identity differs")
    if (
        tuple(observation.observation_id for observation in observations)
        != _EXPECTED_OBSERVATION_IDS
    ):
        raise SliceCContractError("world-1 observation identities differ")


def canonical_observation_bytes_v1(observation: ObservationV1) -> bytes:
    if type(observation) not in {H5adObservationV1, SourceObservationV1}:
        raise SliceCContractError("unknown observation type")
    if observation.observation_id != _observation_id(observation):
        raise SliceCContractError("observation identity differs")
    return canonical_json_bytes(observation.to_dict())


__all__ = [
    "H5adObservationV1",
    "ObservationSetV1",
    "ObservationV1",
    "SourceObservationV1",
    "build_observations_v1",
    "canonical_observation_bytes_v1",
    "observation_runtime_premise_v1",
    "validate_observations_v1",
]
