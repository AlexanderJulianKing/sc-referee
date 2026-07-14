from __future__ import annotations

import json
from pathlib import Path

from tests.frozen_oracles.cases import source_cases
from tests.inference._serialization import public_bytes


ORACLE_PATH = Path(__file__).parents[1] / "frozen_oracles" / "legacy_oracles.json"


def test_may_must_join_and_refinement_enforce_the_invariant():
    import pytest

    from sc_referee.inference.domains.bilattice import MayMust

    left = MayMust(frozenset({"a", "b"}), frozenset({"a"}))
    right = MayMust(frozenset({"b", "c"}), frozenset({"b"}))
    assert left.join(right) == MayMust(frozenset({"a", "b", "c"}), frozenset())
    assert left.refine(MayMust(frozenset({"a"}), frozenset({"a"}))) == MayMust(
        frozenset({"a"}), frozenset({"a"}))
    with pytest.raises(ValueError):
        MayMust(frozenset(), frozenset({"impossible"}))


def test_literal_field_strong_update_dynamic_field_weak_update_and_havoc():
    from sc_referee.inference.analysis.memory import AbstractHeap
    from sc_referee.inference.domains.origin import OriginAtom
    from sc_referee.inference.domains.value import AbsValue

    heap = AbstractHeap()
    location = heap.allocate("obj:1")
    first = AbsValue(origins=frozenset({OriginAtom("literal", "one")}))
    second = AbsValue(origins=frozenset({OriginAtom("literal", "two")}))

    assert heap.write(frozenset({location}), "group", first, definition="d1", definite=True) is True
    assert heap.write(frozenset({location}), "group", second, definition="d2", definite=True) is True
    assert heap.read(frozenset({location}), "group").origins == second.origins
    assert heap.reaching_definitions(location, "group").must == frozenset({"d2"})

    assert heap.write(frozenset({location}), None, first, definition="d3", definite=True) is False
    assert heap.read(frozenset({location}), "group").origins == first.origins | second.origins
    assert heap.reaching_definitions(location, "group").must == frozenset()

    heap.havoc(frozenset({location}), "opaque:1")
    assert heap.read(frozenset({location}), "group").unknown is True
    assert heap.reaching_definitions(location, "group").must == frozenset()


def test_opaque_call_havocs_reachable_mutable_arguments_and_adds_unknown_return_origin():
    from sc_referee.inference.analysis.memory import AbstractHeap, opaque_call
    from sc_referee.inference.domains.origin import OriginAtom
    from sc_referee.inference.domains.value import AbsValue

    heap = AbstractHeap()
    location = heap.allocate("adata")
    argument = AbsValue(points_to=frozenset({location}),
                        origins=frozenset({OriginAtom("primary_data", "adata", "X")}))
    heap.write(argument.points_to, "obs.group", argument, definition="before", definite=True)

    returned, effects = opaque_call("call:opaque", (argument,), heap)

    assert effects.writes == frozenset({location})
    assert effects.unknown_effects == frozenset({"call:opaque"})
    assert returned.unknown is True
    assert argument.origins <= returned.origins
    assert heap.read(argument.points_to, "obs.group").unknown is True


def test_summary_resolution_requires_every_exact_identity_component():
    from sc_referee.inference.contracts.registry import SummaryRegistry
    from sc_referee.inference.contracts.schema import (
        CalleeBinding, EffectContract, FunctionSummary, SummaryBinding,
    )

    binding = SummaryBinding("pkg.mod", "fn", "1.2.3", "sha256:pkg", "sha256:summary")
    registry = SummaryRegistry((FunctionSummary(binding, EffectContract(return_from=(0,))),))
    exact = CalleeBinding("pkg.mod", "fn", "1.2.3", "sha256:pkg", "sha256:summary")
    wrong_digest = CalleeBinding("pkg.mod", "fn", "1.2.3", "sha256:other", "sha256:summary")

    assert registry.resolve_summary(exact).status == "exact"
    assert registry.resolve_summary(wrong_digest).status == "unresolved"


def test_analyze_records_opaque_call_effects_and_still_only_abstains():
    from sc_referee.inference import AnalysisRequest, analyze

    snapshot = analyze(AnalysisRequest(("x = opaque(data)\n",)))
    assert snapshot.outcome == "ABSTAIN"
    assert snapshot.coverage.call_effects_complete is False
    assert any(effect.unknown_effects for state in snapshot.states.values() for effect in state.effects)


def test_shadow_projects_opaque_obsm_as_unresolved_matching_provenance():
    """#47 lockstep: the shadow must classify a non-X_ opaque-embedding grouping as `unresolved`,
    byte-identically to the shipped groupby_provenance — the fix must never diverge the two oracles."""
    from sc_referee.inference import AnalysisRequest, analyze
    from sc_referee.inference.compatibility import project_legacy_marker_tests
    from sc_referee.provenance import groupby_provenance

    src = ("import scanpy as sc\n"
           "from sklearn.mixture import GaussianMixture\n"
           "adata.obsm['scVI'] = model.get_latent_representation()\n"
           "adata.obs['cluster'] = GaussianMixture(2).fit_predict(adata.obsm['scVI'])\n"
           "sc.tl.rank_genes_groups(adata, groupby='cluster')\n")
    snapshot = analyze(AnalysisRequest((src,), compatibility_profile="legacy-v1"))

    shadow = project_legacy_marker_tests(snapshot)
    legacy = groupby_provenance([src])
    assert shadow[0].origin == "unresolved"
    assert [m.origin for m in shadow] == [m.origin for m in legacy]


def test_shadow_projections_never_call_the_legacy_public_implementations(monkeypatch):
    import sc_referee.provenance as provenance
    import sc_referee.sink_use as sink_use
    from sc_referee.inference import AnalysisRequest, analyze
    from sc_referee.inference.compatibility import (
        project_legacy_marker_tests, project_legacy_sink_uses,
    )

    snapshot = analyze(AnalysisRequest((
        "import scanpy as sc\nlabels = cluster(adata.X)\nadata.obs['g'] = labels\n"
        "sc.tl.rank_genes_groups(adata, groupby='g')\n",
    ), compatibility_profile="legacy-v1"))
    monkeypatch.setattr(provenance, "groupby_provenance",
                        lambda *_: (_ for _ in ()).throw(AssertionError("legacy provenance called")))
    monkeypatch.setattr(sink_use, "bind_sinks",
                        lambda *_: (_ for _ in ()).throw(AssertionError("legacy sink binder called")))
    monkeypatch.setattr(sink_use, "groupby_provenance",
                        lambda *_: (_ for _ in ()).throw(AssertionError("legacy join called")))

    assert project_legacy_marker_tests(snapshot)[0].origin == "data_derived"
    assert project_legacy_sink_uses(snapshot).uses[0].bound_ports["grouping"].value_type.origins == frozenset(
        {"primary_data"})


def test_every_frozen_source_has_byte_exact_shadow_projections():
    from sc_referee.inference import (
        AnalysisRequest, analyze, project_legacy_marker_tests, project_legacy_sink_uses,
    )

    frozen = json.loads(ORACLE_PATH.read_text())["sources"]
    for name, sources in source_cases():
        snapshot = analyze(AnalysisRequest(tuple(sources), compatibility_profile="legacy-v1"))
        assert public_bytes(project_legacy_marker_tests(snapshot)).decode() == frozen[name]["groupby_provenance"], name
        assert public_bytes(project_legacy_sink_uses(snapshot)).decode() == frozen[name]["bind_sinks"], name
        assert snapshot.outcome == "ABSTAIN"
