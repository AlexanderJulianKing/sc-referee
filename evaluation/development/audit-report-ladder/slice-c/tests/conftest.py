from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from sc_referee_evaluation.audit_ladder.slice_c.composition import (
    SliceCCompositionResultV1,
    compose_world1_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.core import (
    GroupSizeV1,
    H5adFactsV1,
    MatrixShapeFactV1,
    ObsColumnCardinalityFactV1,
    ObsColumnQuotedValuesFactV1,
    ObsGroupSizesFactV1,
    SliceCRequestV1,
    canonical_json_bytes,
    sha256,
)
from sc_referee_evaluation.audit_ladder.slice_c.fixture import (
    capture_world1_fixture_context_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.observations import (
    ObservationSetV1,
    build_observations_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.repository import (
    CapturedWorld1MaterialsV1,
    RegistryBundleV1,
    authenticate_world1_context_v1,
    load_registry_bundle_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.source import (
    SourceFlowFactV1,
    verify_world1_source_v1,
)

WORLD1_ROOT = Path(__file__).resolve().parents[2] / "world1"
REPOSITORY_ROOT = WORLD1_ROOT / "repository"
SOURCE_PATH = REPOSITORY_ROOT / "analysis.py"
H5AD_PATH = REPOSITORY_ROOT / "sc_reads.h5ad"


@dataclass(frozen=True, slots=True)
class StaticWorld1Case:
    context: object
    request: SliceCRequestV1
    registry: RegistryBundleV1
    materials: CapturedWorld1MaterialsV1
    request_digest: str
    h5ad_facts: H5adFactsV1
    source_fact: SourceFlowFactV1
    observations: ObservationSetV1
    composition: SliceCCompositionResultV1


@pytest.fixture(scope="session")
def static_world1_case() -> StaticWorld1Case:
    request = SliceCRequestV1(
        source_path="analysis.py",
        h5ad_path="sc_reads.h5ad",
        obs_column="animal_id",
    )
    context = capture_world1_fixture_context_v1(REPOSITORY_ROOT)
    registry = load_registry_bundle_v1()
    materials = authenticate_world1_context_v1(context, request, registry)
    request_digest = sha256(canonical_json_bytes(request.to_dict()))
    h5ad_facts = H5adFactsV1(
        matrix_shape=MatrixShapeFactV1(row_count=4_000, column_count=3),
        cardinality=ObsColumnCardinalityFactV1(column="animal_id", n_obs=4_000, distinct_count=2),
        group_sizes=ObsGroupSizesFactV1(
            column="animal_id",
            n_obs=4_000,
            groups=(GroupSizeV1("Animal_1", 2_000), GroupSizeV1("Animal_2", 2_000)),
        ),
        quoted_values=ObsColumnQuotedValuesFactV1(
            column="animal_id",
            n_obs=4_000,
            values=("Animal_1",) * 2_000 + ("Animal_2",) * 2_000,
        ),
    )
    source_fact = verify_world1_source_v1(materials.source_bytes)
    observations = build_observations_v1(
        materials,
        request_digest,
        h5ad_facts,
        source_fact,
    )
    composition = compose_world1_v1(
        materials=materials,
        request_digest=request_digest,
        primary_observations=observations,
        replay_h5ad_facts=h5ad_facts,
        replay_source_fact=source_fact,
        replay_observations=observations,
    )
    return StaticWorld1Case(
        context=context,
        request=request,
        registry=registry,
        materials=materials,
        request_digest=request_digest,
        h5ad_facts=h5ad_facts,
        source_fact=source_fact,
        observations=observations,
        composition=composition,
    )
