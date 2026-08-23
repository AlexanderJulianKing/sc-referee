"""The sole world-1 Slice-C composition rule."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from sc_referee_evaluation.audit_ladder.slice_c.core import H5adFactsV1, SliceCContractError
from sc_referee_evaluation.audit_ladder.slice_c.observations import (
    ObservationSetV1,
    canonical_observation_bytes_v1,
    validate_observations_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.repository import CapturedWorld1MaterialsV1
from sc_referee_evaluation.audit_ladder.slice_c.source import SourceFlowFactV1

_RULE_ID: Final = "world1.row-level-independent-samples.slice-c.v1"
_MISSING_PREMISE: Final = "world1.animal-id-is-independent-unit.v1"


@dataclass(frozen=True, slots=True)
class SliceCCompositionResultV1:
    rule_id: str
    conditional_concern: bool
    missing_premises: tuple[str, ...]
    finding_count: int
    material_question_count: int

    def __post_init__(self) -> None:
        if (
            type(self) is not SliceCCompositionResultV1
            or self.rule_id != _RULE_ID
            or self.conditional_concern is not True
            or self.missing_premises != (_MISSING_PREMISE,)
            or self.finding_count != 0
            or self.material_question_count != 0
        ):
            raise SliceCContractError("composition result is outside the sole M3 state")


def compose_world1_v1(
    *,
    materials: CapturedWorld1MaterialsV1,
    request_digest: str,
    primary_observations: ObservationSetV1,
    replay_h5ad_facts: H5adFactsV1,
    replay_source_fact: SourceFlowFactV1,
    replay_observations: ObservationSetV1,
) -> SliceCCompositionResultV1:
    """Apply the single rule after independent fact and observation replay."""

    validate_observations_v1(
        primary_observations,
        materials=materials,
        request_digest=request_digest,
    )
    validate_observations_v1(
        replay_observations,
        materials=materials,
        request_digest=request_digest,
    )
    if tuple(canonical_observation_bytes_v1(item) for item in primary_observations) != tuple(
        canonical_observation_bytes_v1(item) for item in replay_observations
    ):
        raise SliceCContractError("composition observation replay differs")
    shape = replay_h5ad_facts.matrix_shape
    cardinality = replay_h5ad_facts.cardinality
    groups = replay_h5ad_facts.group_sizes
    quoted = replay_h5ad_facts.quoted_values
    source = replay_source_fact
    if (
        materials.source_digest
        != "sha256:c5f3bb51457ace3e4b979b69739f212b9d0c7a12baba62033859d31f5b2ade18"
        or materials.h5ad_digest
        != "sha256:f94ddd1bc2c7d1d690d5c054caf924a2c531a0e7d191da9ca7a7b786fee0e887"
        or len(materials.source_bytes) != 1_015
        or len(materials.h5ad_bytes) != 330_008
        or shape.row_count != 4_000
        or shape.column_count != 3
        or cardinality.column != "animal_id"
        or cardinality.n_obs != 4_000
        or cardinality.distinct_count != 2
        or groups.column != "animal_id"
        or groups.n_obs != 4_000
        or tuple((item.value, item.count) for item in groups.groups)
        != (("Animal_1", 2_000), ("Animal_2", 2_000))
        or quoted.column != "animal_id"
        or quoted.n_obs != 4_000
        or quoted.values[:2_000] != ("Animal_1",) * 2_000
        or quoted.values[2_000:] != ("Animal_2",) * 2_000
        or source.source_sha256 != materials.source_digest
        or source.h5ad_read_literal != "sc_reads.h5ad"
        or source.obs_column != "animal_id"
        or source.selection_literals != ("Animal_1", "Animal_2")
        or source.subset_bindings != ("cells_animal1", "cells_animal2")
        or source.vector_bindings != ("expr_1", "expr_2")
        or source.procedure != "scipy.stats.ttest_ind"
        or source.call_argument_order != source.vector_bindings
        or any(observation.finding_eligible is not False for observation in primary_observations)
    ):
        raise SliceCContractError("world-1 composition conjunction is not fully discharged")
    return SliceCCompositionResultV1(
        rule_id=_RULE_ID,
        conditional_concern=True,
        missing_premises=(_MISSING_PREMISE,),
        finding_count=0,
        material_question_count=0,
    )


__all__ = ["SliceCCompositionResultV1", "compose_world1_v1"]
