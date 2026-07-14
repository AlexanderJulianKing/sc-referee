"""Adversarial MV-0 contract for the matrix-version domain.

Each test names the red-team/spec obligation whose false-positive route it closes.
"""
from __future__ import annotations

from dataclasses import replace
from itertools import product

import pytest

from sc_referee.inference.domains.matrix_version import (
    AncestorInfluence,
    ComponentKind,
    ComponentRef,
    DerivationEdge,
    DerivationKind,
    EvidenceKind,
    GuardedVersion,
    ImmediateVersionRelation,
    JointCoordinateBounds,
    JointInfluenceMap,
    MatrixRead,
    MeasurementDigestKind,
    MeasurementPair,
    MeasurementPairInventory,
    MeasurementRelation,
    NoiseEngineStatus,
    NoiseUnit,
    NoiseUnitKind,
    StatisticalMatrixVersion,
    VersionBoundary,
    VersionPairInventory,
    VersionValue,
    aggregate_judgments,
    aggregate_measurement_relation,
    ancestor_version_ids,
    compare_immediate_versions,
    judge_measurement_pair,
)
from sc_referee.inference.domains.region import SetBounds


def _version(
    name: str,
    *,
    measurement_kind: MeasurementDigestKind = MeasurementDigestKind.RECIPE,
    evidence_kind: EvidenceKind = EvidenceKind.CANONICAL_ARTIFACT,
) -> StatisticalMatrixVersion:
    return StatisticalMatrixVersion(
        root_artifact_digest=f"root:{name}",
        row_identity_digest=f"rows:{name}",
        feature_identity_digest=f"features:{name}",
        measurement_value_digest=f"measurement:{name}",
        noise_unit_digest=f"noise:{name}",
        transform_lineage_digest=f"lineage:{name}",
        measurement_digest_kind=measurement_kind,
        evidence_kind=evidence_kind,
    )


def _value(*versions: StatisticalMatrixVersion) -> VersionValue:
    return VersionValue(
        frozenset(GuardedVersion(f"guard:{index}", version) for index, version in enumerate(versions))
    )


def _read(
    version: StatisticalMatrixVersion,
    influences: dict[StatisticalMatrixVersion, JointCoordinateBounds],
    *,
    lineage_complete: bool = True,
    map_boundaries: frozenset[VersionBoundary] = frozenset(),
) -> MatrixRead:
    return MatrixRead(
        component=ComponentRef("heap:adata", ComponentKind.X),
        versions=_value(version),
        row_region=SetBounds.exact("rows", {"r0", "r1"}),
        feature_region=SetBounds.exact("features", {"A", "B"}),
        influence_map=JointInfluenceMap(
            frozenset(AncestorInfluence(ancestor.version_id, region) for ancestor, region in influences.items()),
            map_boundaries,
        ),
        lineage_complete=lineage_complete,
    )


def _pair(selection: MatrixRead, test: MatrixRead) -> MeasurementPair:
    return MeasurementPair(
        selection,
        next(iter(selection.versions.alternatives)),
        test,
        next(iter(test.versions.alternatives)),
    )


def _shared_pair() -> tuple[MeasurementPair, frozenset[DerivationEdge]]:
    version = _version("shared")
    region = JointCoordinateBounds.exact({("r0", "A")})
    return _pair(_read(version, {version: region}), _read(version, {version: region})), frozenset()


def test_empty_jointly_feasible_pair_set_is_unknown_not_vacuously_shared():
    """[rt4-A / contract 1] Universal lifting has an explicit nonempty premise."""
    inventory = MeasurementPairInventory(frozenset(), complete=True)
    assert aggregate_measurement_relation(inventory, frozenset()) is MeasurementRelation.UNKNOWN


@pytest.mark.parametrize(
    "boundary",
    ["recursion", "resource-exhaustion", "unbounded-occurrences", "dynamic-occurrences", "feasibility"],
)
def test_incomplete_pair_inventory_is_unknown_even_when_known_pairs_share(boundary):
    """[rt4-A / contract 2] Partial universals never lift to an affirmative."""
    pair, edges = _shared_pair()
    inventory = MeasurementPairInventory(
        frozenset({pair}), complete=False, unknown_boundaries=frozenset({VersionBoundary(boundary)})
    )
    assert aggregate_measurement_relation(inventory, edges) is MeasurementRelation.UNKNOWN


def test_one_unknown_pair_forces_universal_aggregate_to_unknown():
    """[rt3-2 / contract 3] There is no existential lift from one shared pair."""
    shared, edges = _shared_pair()
    other = _version("other")
    unknown = _pair(
        _read(other, {other: JointCoordinateBounds.exact({("r0", "A")})}),
        _read(other, {other: JointCoordinateBounds.dynamic("unrepresentable")}),
    )
    inventory = MeasurementPairInventory(frozenset({shared, unknown}), complete=True)
    assert judge_measurement_pair(shared, edges) is MeasurementRelation.PROVED_SHARED
    assert judge_measurement_pair(unknown, edges) is MeasurementRelation.UNKNOWN
    assert aggregate_measurement_relation(inventory, edges) is MeasurementRelation.UNKNOWN


def test_nonempty_complete_all_shared_is_the_only_positive_aggregation_path():
    """[rt2/rt3 / contract 4] The full positive conjunction permits PROVED_SHARED."""
    pair, edges = _shared_pair()
    inventory = MeasurementPairInventory(frozenset({pair}), complete=True)
    assert {relation.name for relation in MeasurementRelation} == {"PROVED_SHARED", "UNKNOWN"}
    assert aggregate_measurement_relation(inventory, edges) is MeasurementRelation.PROVED_SHARED


def test_joint_coordinates_not_overlapping_marginals_decide_overlap():
    """[rt3-B / contract 5] Paired indices with equal marginals remain joint-disjoint."""
    version = _version("paired")
    selection_joint = JointCoordinateBounds.exact({("r0", "A"), ("r1", "B")})
    test_joint = JointCoordinateBounds.exact({("r0", "B"), ("r1", "A")})
    selection = _read(version, {version: selection_joint})
    test = _read(version, {version: test_joint})
    assert selection.row_region == test.row_region
    assert selection.feature_region == test.feature_region
    assert judge_measurement_pair(_pair(selection, test), frozenset()) is MeasurementRelation.UNKNOWN


def test_proved_rectangular_marginal_product_can_prove_joint_overlap():
    """[rt3-B boundary / contract 6] A proved product is a legitimate joint representation."""
    version = _version("rectangle")
    region = JointCoordinateBounds.from_rectangular_marginals(
        SetBounds.exact("rows", {"r0", "r1"}),
        SetBounds.exact("features", {"A", "B"}),
        proved_rectangular=True,
    )
    pair = _pair(_read(version, {version: region}), _read(version, {version: region}))
    assert region.proved_rectangular is True
    assert judge_measurement_pair(pair, frozenset()) is MeasurementRelation.PROVED_SHARED


@pytest.mark.parametrize("selector", ["fancy", "paired", "boolean-mask", "non-rectangular"])
def test_unrepresentable_joint_selector_abstains(selector):
    """[rt3-B / contract 7] Marginals cannot fill an unknown joint relation."""
    version = _version(selector)
    unknown = JointCoordinateBounds.from_rectangular_marginals(
        SetBounds.exact("rows", {"r0"}),
        SetBounds.exact("features", {"A"}),
        proved_rectangular=False,
        boundary_id=f"unrepresentable:{selector}",
    )
    pair = _pair(_read(version, {version: unknown}), _read(version, {version: unknown}))
    assert judge_measurement_pair(pair, frozenset()) is MeasurementRelation.UNKNOWN


def test_unknown_composition_boundary_is_sticky_across_later_rectangular_projection():
    """[rt4-B / contract 8] concat→fancy→mask→projection cannot regain a product proof."""
    ancestor = _version("chain-root")
    initial = JointInfluenceMap(
        frozenset(
            {AncestorInfluence(ancestor.version_id, JointCoordinateBounds.exact({("r0", "A")}))}
        )
    )
    fancy = initial.project(
        frozenset(), relation_representable=False, boundary_id="fancy-relation-unknown"
    )
    rectangular_looking = AncestorInfluence(
        ancestor.version_id,
        JointCoordinateBounds.from_rectangular_marginals(
            SetBounds.exact("rows", {"r0"}),
            SetBounds.exact("features", {"A"}),
            proved_rectangular=True,
        ),
    )
    after_mask = fancy.project(
        frozenset({rectangular_looking}), relation_representable=True
    )
    after_mask_and_projection = after_mask.project(
        frozenset({rectangular_looking}), relation_representable=True
    )
    selection = replace(_read(ancestor, {ancestor: rectangular_looking.region}), influence_map=after_mask_and_projection)
    test = _read(ancestor, {ancestor: rectangular_looking.region})
    assert after_mask_and_projection.unknown_boundaries
    assert judge_measurement_pair(_pair(selection, test), frozenset()) is MeasurementRelation.UNKNOWN


def test_shared_ancestor_older_than_both_immediate_versions_is_found_by_closure():
    """[spec §4 / contract 9] Reflexive-transitive closure, not immediate equality, is load-bearing."""
    root, v2_material, pca_material, v3_material = map(
        _version, ("v1", "v2", "pca", "v3")
    )
    v2_edge = DerivationEdge(
        root,
        v2_material,
        DerivationKind.INPLACE_TRANSFORM,
        "summary:norm",
        "occ:norm",
        "map:norm",
    )
    pca_edge = DerivationEdge(
        v2_edge.child,
        pca_material,
        DerivationKind.DERIVED_COMPONENT,
        "summary:pca",
        "occ:pca",
        "map:pca",
    )
    v3_edge = DerivationEdge(
        root,
        v3_material,
        DerivationKind.INPLACE_TRANSFORM,
        "summary:other",
        "occ:other",
        "map:other",
    )
    edges = frozenset({v2_edge, pca_edge, v3_edge})
    overlap = JointCoordinateBounds.exact({("r0", "A")})
    pair = _pair(_read(pca_edge.child, {root: overlap}), _read(v3_edge.child, {root: overlap}))
    assert judge_measurement_pair(pair, edges) is MeasurementRelation.PROVED_SHARED


def test_whole_row_influence_shares_with_a_different_gene_test():
    """[spec §3 / contract 10] normalize_total couples each output to every included gene."""
    version = _version("normalized")
    whole_row = JointCoordinateBounds.exact({("r0", "A"), ("r0", "B")})
    gene_b = JointCoordinateBounds.exact({("r0", "B")})
    pair = _pair(_read(version, {version: whole_row}), _read(version, {version: gene_b}))
    assert judge_measurement_pair(pair, frozenset()) is MeasurementRelation.PROVED_SHARED


def test_version_value_join_and_immediate_comparison_rules():
    """[rt2-7 / contract 11] Join is union; comparison is universal over feasible pairs."""
    a, b = _version("a"), _version("b")
    left, same, different = _value(a), _value(a), _value(b)
    joined = left.join(different)
    assert joined.alternatives == left.alternatives | different.alternatives
    assert {guarded.version for guarded in joined.alternatives} == {a, b}
    assert compare_immediate_versions(VersionPairInventory.cartesian(left, same)) is ImmediateVersionRelation.SAME_VERSION
    assert compare_immediate_versions(VersionPairInventory.cartesian(left, different)) is ImmediateVersionRelation.DIFFERENT_VERSION
    mixed = VersionPairInventory.cartesian(joined, same)
    assert compare_immediate_versions(mixed) is ImmediateVersionRelation.UNKNOWN


def test_unknown_feasibility_keeps_cartesian_product_and_adds_boundary():
    """[rt2-7 / contract 11] Solver uncertainty cannot discard the unequal pair to manufacture SAME."""
    a, b = _version("guard-a"), _version("guard-b")
    left, right = _value(a, b), _value(a, b)
    partial_solver_answer = frozenset(
        {(next(iter(left.alternatives)), next(iter(right.alternatives)))}
    )
    inventory = VersionPairInventory.from_feasibility(
        left,
        right,
        feasible_pairs=partial_solver_answer,
        feasibility_complete=False,
        boundary_id="sat-exhausted",
    )
    assert inventory.pairs == frozenset(product(left.alternatives, right.alternatives))
    assert inventory.unknown_boundaries == frozenset({VersionBoundary("sat-exhausted")})
    assert compare_immediate_versions(inventory) is ImmediateVersionRelation.UNKNOWN


def test_different_immediate_version_never_blocks_a_shared_ancestor():
    """[spec §3 / contract 12] DIFFERENT_VERSION is audit-only, never independence."""
    root, selection_material, test_material = map(
        _version, ("different-root", "selection", "test")
    )
    selection_edge = DerivationEdge(
        root,
        selection_material,
        DerivationKind.PROJECTION,
        "summary:s",
        "occ:s",
        "map:s",
    )
    test_edge = DerivationEdge(
        root,
        test_material,
        DerivationKind.COPY,
        "summary:t",
        "occ:t",
        "map:t",
    )
    selection_version, test_version = selection_edge.child, test_edge.child
    edges = frozenset({selection_edge, test_edge})
    immediate = VersionPairInventory.cartesian(_value(selection_version), _value(test_version))
    overlap = JointCoordinateBounds.exact({("r0", "A")})
    pair = _pair(_read(selection_version, {root: overlap}), _read(test_version, {root: overlap}))
    assert compare_immediate_versions(immediate) is ImmediateVersionRelation.DIFFERENT_VERSION
    assert judge_measurement_pair(pair, edges) is MeasurementRelation.PROVED_SHARED


def test_digest_kind_and_evidence_kind_are_domain_separated_in_version_id():
    """[rt2-MAJOR2 / contract 13] Recipe/content and evidence domains cannot collide."""
    base = _version("digest", measurement_kind=MeasurementDigestKind.RECIPE)
    content = replace(base, measurement_digest_kind=MeasurementDigestKind.CONTENT)
    snapshot = replace(base, evidence_kind=EvidenceKind.INSTRUMENTED_SNAPSHOT)
    assert len({base.version_id, content.version_id, snapshot.version_id}) == 3
    assert compare_immediate_versions(
        VersionPairInventory.cartesian(_value(base), _value(content))
    ) is ImmediateVersionRelation.DIFFERENT_VERSION
    assert compare_immediate_versions(
        VersionPairInventory.cartesian(_value(base), _value(snapshot))
    ) is ImmediateVersionRelation.DIFFERENT_VERSION


def test_distinct_dynamic_occurrences_cannot_collapse_to_false_proved_shared():
    """[blocker / contract 14] Distinct transitions cannot share a child version identity."""
    parent_1, parent_2 = _version("dynamic-parent-1"), _version("dynamic-parent-2")
    identical_child_material = _version("dynamic-child")
    edge_1 = DerivationEdge(
        parent_1,
        identical_child_material,
        DerivationKind.SPLIT_CHILD,
        "summary:split",
        "occ:1",
        "map:split",
        split_event_id="split:1",
    )
    edge_2 = DerivationEdge(
        parent_2,
        identical_child_material,
        DerivationKind.SPLIT_CHILD,
        "summary:split",
        "occ:2",
        "map:split",
        split_event_id="split:2",
    )
    overlap = JointCoordinateBounds.exact({("r0", "A")})
    pair = _pair(
        _read(edge_1.child, {edge_1.child: overlap}),
        _read(edge_2.child, {edge_2.child: overlap}),
    )

    assert (
        edge_1.child.version_id == edge_2.child.version_id,
        judge_measurement_pair(pair, frozenset({edge_1, edge_2})),
    ) == (False, MeasurementRelation.UNKNOWN)


def test_occurrence_and_split_event_are_committed_to_child_version_identity():
    """[rt4 acceptance iii / contract 14] Dynamic occurrences and split events cannot conflate."""
    parent, identical_child_material = _version("edge-parent"), _version("edge-child")
    edge = DerivationEdge(
        parent,
        identical_child_material,
        DerivationKind.SPLIT_CHILD,
        "summary:split",
        "occ:1",
        "map:split",
        split_event_id="split:1",
    )
    other_occurrence = replace(edge, occurrence_id="occ:2")
    other_split = replace(edge, split_event_id="split:2")
    assert len(
        {
            edge.child.transform_lineage_digest,
            other_occurrence.child.transform_lineage_digest,
            other_split.child.transform_lineage_digest,
        }
    ) == 3
    assert len(
        {edge.child.version_id, other_occurrence.child.version_id, other_split.child.version_id}
    ) == 3
    assert edge.transition_commitment_digest == edge.child.transform_lineage_digest
    assert edge.committed_transform_lineage_digest == edge.transition_commitment_digest
    assert edge.transform_lineage_digest != edge.transition_commitment_digest
    assert compare_immediate_versions(
        VersionPairInventory.cartesian(_value(edge.child), _value(other_occurrence.child))
    ) is ImmediateVersionRelation.DIFFERENT_VERSION

    edges = frozenset({edge, other_occurrence, other_split})
    assert ancestor_version_ids(edge.child, edges) == frozenset(
        {edge.child.version_id, parent.version_id}
    )
    assert ancestor_version_ids(other_occurrence.child, edges) == frozenset(
        {other_occurrence.child.version_id, parent.version_id}
    )


def test_noise_unit_engine_status_has_no_proved_valid_state():
    """[spec §4 / contract 15] Recognition records structure, never statistical validity."""
    assert {status.name for status in NoiseEngineStatus} == {"RECOGNIZED", "UNKNOWN"}
    assert not hasattr(NoiseEngineStatus, "PROVED_VALID")
    recognized = NoiseUnit(
        NoiseUnitKind.COUNT_SPLIT,
        "root-measurement",
        "partition",
        engine_status=NoiseEngineStatus.RECOGNIZED,
        complement_digest="complement",
    )
    assert recognized.engine_status is NoiseEngineStatus.RECOGNIZED
    with pytest.raises((TypeError, ValueError)):
        replace(recognized, engine_status="PROVED_VALID")


def test_soundness_meta_never_affirms_without_the_full_positive_conjunction():
    """[cardinal contract 16] Broad table: no false PROVED_SHARED from universal aggregation."""
    judgments = (MeasurementRelation.PROVED_SHARED, MeasurementRelation.UNKNOWN)
    for complete, boundary, size in product((False, True), (False, True), range(5)):
        for values in product(judgments, repeat=size):
            boundaries = frozenset({VersionBoundary("meta-boundary")}) if boundary else frozenset()
            actual = aggregate_judgments(
                values, pair_inventory_complete=complete, unknown_boundaries=boundaries
            )
            positive_conjunction = complete and not boundary and bool(values) and all(
                value is MeasurementRelation.PROVED_SHARED for value in values
            )
            assert (actual is MeasurementRelation.PROVED_SHARED) is positive_conjunction


def test_pairwise_soundness_meta_requires_complete_lineages_common_ancestor_and_joint_overlap():
    """[cardinal contract 16] Pairwise affirmative requires every conjunct, with UNKNOWN as default."""
    root, selection_material, test_material = map(
        _version, ("meta-root", "meta-selection", "meta-test")
    )
    selection_edge = DerivationEdge(
        root, selection_material, DerivationKind.PROJECTION, "s", "s:1", "s-map"
    )
    test_edge = DerivationEdge(
        root, test_material, DerivationKind.PROJECTION, "t", "t:1", "t-map"
    )
    selection_version, test_version = selection_edge.child, test_edge.child
    connected_edges = frozenset({selection_edge, test_edge})
    overlap = JointCoordinateBounds.exact({("r0", "A")})
    disjoint = JointCoordinateBounds.exact({("r1", "B")})
    for selection_complete, test_complete, connected, relation_kind, boundary in product(
        (False, True), (False, True), (False, True), ("overlap", "disjoint", "unknown"), (False, True)
    ):
        selection_region = overlap
        test_region = overlap if relation_kind == "overlap" else disjoint
        if relation_kind == "unknown":
            test_region = JointCoordinateBounds.dynamic("meta-joint-unknown")
        map_boundaries = frozenset({VersionBoundary("meta-map")}) if boundary else frozenset()
        selection_ancestor = root if connected else selection_version
        test_ancestor = root if connected else test_version
        selection = _read(
            selection_version,
            {selection_ancestor: selection_region},
            lineage_complete=selection_complete,
            map_boundaries=map_boundaries,
        )
        test = _read(
            test_version,
            {test_ancestor: test_region},
            lineage_complete=test_complete,
        )
        actual = judge_measurement_pair(
            _pair(selection, test), connected_edges if connected else frozenset()
        )
        positive_conjunction = (
            selection_complete
            and test_complete
            and connected
            and relation_kind == "overlap"
            and not boundary
        )
        assert (actual is MeasurementRelation.PROVED_SHARED) is positive_conjunction


def test_pairwise_soundness_meta_binds_occurrence_and_split_to_child_version():
    """[cardinal contract 16] Transition identity cannot manufacture a common child ancestor."""
    parent = _version("meta-transition-parent")
    identical_child_material = _version("meta-transition-child")
    overlap = JointCoordinateBounds.exact({("r0", "A")})
    disjoint = JointCoordinateBounds.exact({("r1", "B")})

    for distinct_occurrence, distinct_split, relation_kind in product(
        (False, True), (False, True), ("overlap", "disjoint")
    ):
        edge_1 = DerivationEdge(
            parent,
            identical_child_material,
            DerivationKind.SPLIT_CHILD,
            "summary:meta-split",
            "occ:1",
            "map:meta-split",
            split_event_id="split:1",
        )
        edge_2 = DerivationEdge(
            parent,
            identical_child_material,
            DerivationKind.SPLIT_CHILD,
            "summary:meta-split",
            "occ:2" if distinct_occurrence else "occ:1",
            "map:meta-split",
            split_event_id="split:2" if distinct_split else "split:1",
        )
        test_region = overlap if relation_kind == "overlap" else disjoint
        pair = _pair(
            _read(edge_1.child, {edge_1.child: overlap}),
            _read(edge_2.child, {edge_2.child: test_region}),
        )
        actual = judge_measurement_pair(pair, frozenset({edge_1, edge_2}))
        same_transition = not distinct_occurrence and not distinct_split
        positive_conjunction = same_transition and relation_kind == "overlap"

        assert (actual is MeasurementRelation.PROVED_SHARED) is positive_conjunction
