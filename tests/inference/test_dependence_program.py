from __future__ import annotations

import pytest


def test_dependence_edge_class_set_is_closed_and_complete():
    from sc_referee.inference.analysis.dependence import EdgeKind

    assert {kind.value for kind in EdgeKind} == {
        "VALUE", "CONTROL", "ALIAS", "MUTATION", "FIELD", "FITTED_STATE",
        "ARTIFACT", "SERIALIZE", "CONFIG", "FORMAT",
    }


def test_derivation_is_or_of_guarded_alternatives_with_typed_requirements():
    from sc_referee.inference.analysis.dependence import (
        AllOf, Alternative, Atom, ChoiceOf, Derivation, EdgeKind, Guard, TransformBinding, Unknown,
    )

    exact = Atom("value:x", EdgeKind.VALUE)
    unknown = Unknown("boundary:1", "opaque read")
    requirements = ChoiceOf((exact, AllOf((exact, unknown), consumption_complete=False)))
    alternatives = (
        Alternative("alt:1", Guard("g1", feasible=True, pinned=True), "def:1", requirements,
                    TransformBinding("affine_linear_q.v1", "identity")),
        Alternative("alt:2", Guard("g2", feasible=False, pinned=True), "def:2", exact,
                    TransformBinding("affine_linear_q.v1", "negate")),
    )
    derivation = Derivation("value:y", alternatives)

    assert derivation.target == "value:y"
    assert derivation.alternatives == alternatives
    assert requirements.items[1].consumption_complete is False


def test_every_edge_kind_round_trips_through_a_derivation():
    from sc_referee.inference.analysis.dependence import (
        AllOf, Alternative, Atom, Derivation, EdgeKind, Guard, TransformBinding,
    )

    atoms = tuple(Atom(f"node:{kind.value}", kind) for kind in EdgeKind)
    derivation = Derivation("root", (
        Alternative("alt", Guard("guard", True, True), "definition",
                    AllOf(atoms, consumption_complete=True),
                    TransformBinding("affine_linear_q.v1", "add")),
    ))
    assert {atom.edge_kind for atom in derivation.alternatives[0].requirements.items} == set(EdgeKind)


def test_every_abstract_read_has_requirements_or_an_explicit_unknown_boundary():
    from sc_referee.inference.analysis.dependence import (
        Atom, DependenceBuilder, EdgeKind, Unknown,
    )

    builder = DependenceBuilder()
    builder.record_read("read:exact", Atom("value:x", EdgeKind.VALUE))
    builder.record_read("read:opaque", None, boundary_id="opaque:1", reason="opaque call")
    program = builder.build()
    program.validate()

    assert isinstance(program.reads["read:opaque"], Unknown)
    assert program.reads["read:exact"].node == "value:x"

    broken = DependenceBuilder()
    broken.declare_read("read:missing")
    with pytest.raises(ValueError, match="read:missing"):
        broken.build().validate()


def test_build_dependence_records_dynamic_and_exact_ast_reads_without_execution():
    from sc_referee.inference import AnalysisRequest, analyze
    from sc_referee.inference.analysis.dependence import Unknown

    snapshot = analyze(AnalysisRequest((
        "x = data.obs['group']\ny = data.obs[key]\nz = opaque(x)\n",
    )))
    snapshot.dependence.validate()
    assert snapshot.dependence.reads
    assert any(isinstance(requirements, Unknown)
               for requirements in snapshot.dependence.reads.values())
    assert snapshot.outcome == "ABSTAIN"
