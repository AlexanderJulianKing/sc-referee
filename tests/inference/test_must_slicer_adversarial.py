from __future__ import annotations

import pytest

from sc_referee.inference.analysis.dependence import (
    AllOf, Alternative, Atom, DependenceProgram, Derivation, EdgeEvidence, EdgeKind, Guard,
    TransformBinding,
)
from sc_referee.inference.claims.inventory import ClaimRootGrade, ReportClaim
from sc_referee.inference.claims.sensitivity import SensitivitySolverKind
from sc_referee.inference.domains.scalar import ScalarInterval


AFFINE = SensitivitySolverKind.AFFINE_LINEAR_Q.value
SETS = SensitivitySolverKind.EXACT_SET_MEMBERSHIP.value


def _transform(solver=AFFINE, operation="identity", **parameters):
    return TransformBinding(solver, operation, tuple(parameters.items()))


def _alternative(identifier, requirements, *, transform=None, feasible=True, pinned=True):
    return Alternative(identifier, Guard(f"guard:{identifier}", feasible, pinned), f"def:{identifier}",
                       requirements, transform or _transform())


def _derivation(target, *alternatives):
    return Derivation(target, tuple(alternatives))


def _program(*derivations, producers=("p",), max_nodes=10000):
    return DependenceProgram({item.target: item for item in derivations}, {},
                             frozenset(producers), max_nodes)


def _claim(value="root", *, exact=True):
    return ReportClaim("claim:1", value, "pvalue", ClaimRootGrade.ACCUSATION_GRADE,
                       root_exact=exact)


def _slice(program, claim=None):
    from sc_referee.inference.claims.slice import slice_claim

    return slice_claim(program, claim or _claim())


def test_reconvergent_x_plus_negative_x_is_may_only_after_whole_dag_canonicalization():
    negative = _derivation("negative", _alternative("neg", Atom("p"),
                                                     transform=_transform(operation="negate")))
    root = _derivation("root", _alternative(
        "sum", AllOf((Atom("p"), Atom("negative")), consumption_complete=True),
        transform=_transform(operation="add"),
    ))
    result = _slice(_program(negative, root))
    assert result.possible_producers == frozenset({"p"})
    assert result.unavoidable_producers == frozenset()
    proof = result.composition_proofs["p"]
    assert proof.status == "REFUTED"
    assert proof.subdags[0].reachable_nodes == frozenset({"root", "negative", "p"})


def test_two_sequential_negations_remain_unavoidable():
    first = _derivation("neg1", _alternative("neg1", Atom("p"),
                                              transform=_transform(operation="negate")))
    second = _derivation("neg2", _alternative("neg2", Atom("neg1"),
                                               transform=_transform(operation="negate")))
    root = _derivation("root", _alternative("root", Atom("neg2")))
    result = _slice(_program(first, second, root))
    assert result.unavoidable_producers == frozenset({"p"})


def test_multiplication_by_possibly_zero_quantity_is_may_only():
    root = _derivation("root", _alternative(
        "mul", Atom("p"), transform=_transform(operation="multiply",
                                                factor=ScalarInterval(-1, 1)),
    ))
    result = _slice(_program(root))
    assert result.possible_producers == frozenset({"p"})
    assert result.unavoidable_producers == frozenset()


def test_selected_record_removed_by_later_exact_mask_is_may_only():
    selected = _derivation("selected", _alternative(
        "select", Atom("p"), transform=_transform(SETS, "select", members=frozenset({"p"})),
    ))
    root = _derivation("root", _alternative(
        "remove", Atom("selected"), transform=_transform(SETS, "remove", members=frozenset({"p"})),
    ))
    result = _slice(_program(selected, root))
    assert result.possible_producers == frozenset({"p"})
    assert result.unavoidable_producers == frozenset()


def test_mask_combined_with_unknown_predicate_is_may_only():
    root = _derivation("root", _alternative(
        "unknown-mask", Atom("p"), transform=_transform(SETS, "unknown_mask"),
    ))
    result = _slice(_program(root))
    assert result.unavoidable_producers == frozenset()
    assert result.coverage_complete is False
    assert result.unknown_boundaries


def test_sensitive_branch_cannot_compensate_for_feasible_bypass_branch():
    root = _derivation(
        "root",
        _alternative("uses-p", Atom("p")),
        _alternative("bypass", Atom("q")),
    )
    result = _slice(_program(root, producers=("p", "q")))
    assert result.possible_producers == frozenset({"p", "q"})
    assert result.unavoidable_producers == frozenset()


def test_alternative_reaching_definitions_are_unavoidable_only_when_every_one_uses_producer():
    mixed = _derivation("x", _alternative("p-def", Atom("p")),
                       _alternative("q-def", Atom("q")))
    root = _derivation("root", _alternative("root", Atom("x")))
    assert _slice(_program(mixed, root, producers=("p", "q"))).unavoidable_producers == frozenset()

    all_p = _derivation("x", _alternative("p-def-1", Atom("p")),
                       _alternative("p-def-2", Atom("p")))
    assert _slice(_program(all_p, root)).unavoidable_producers == frozenset({"p"})


def test_any_widened_facet_on_path_is_may_only():
    evidence = EdgeEvidence(widened=True)
    root = _derivation("root", _alternative("root", Atom("p", evidence=evidence)))
    result = _slice(_program(root))
    assert result.unavoidable_producers == frozenset()
    assert result.coverage_complete is False
    assert result.unknown_boundaries


@pytest.mark.parametrize("evidence", [
    EdgeEvidence(singleton_must_alias=False),
    EdgeEvidence(no_possible_overwrite=False),
])
def test_weak_alias_or_intervening_possible_overwrite_is_may_only(evidence):
    root = _derivation("root", _alternative("root", Atom("p", EdgeKind.MUTATION, evidence)))
    assert _slice(_program(root)).unavoidable_producers == frozenset()


def test_non_closed_nonlinear_or_opaque_transform_is_may_only():
    root = _derivation("root", _alternative(
        "nonlinear", Atom("p"), transform=_transform("nonlinear.custom", "square"),
    ))
    assert _slice(_program(root)).unavoidable_producers == frozenset()


def test_genuinely_definite_single_path_exact_field_affine_flow_is_unavoidable():
    evidence = EdgeEvidence(certified=True, exact_field=True, singleton_must_alias=True,
                            no_possible_overwrite=True, serializer_resolved=True,
                            fitted_state_resolved=True, widened=False, unknown_havoc=False)
    root = _derivation("root", _alternative(
        "exact", Atom("p", EdgeKind.FIELD, evidence), transform=_transform(operation="scale", factor=2),
    ))
    result = _slice(_program(root))
    assert result.possible_producers == frozenset({"p"})
    assert result.unavoidable_producers == frozenset({"p"})
    assert result.composition_proofs["p"].whole_subdag is True


def test_allof_without_complete_consumption_certificate_is_never_must():
    root = _derivation("root", _alternative(
        "uncertified-all", AllOf((Atom("p"), Atom("q")), consumption_complete=False),
        transform=_transform(operation="add"),
    ))
    result = _slice(_program(root, producers=("p", "q")))
    assert result.possible_producers == frozenset({"p", "q"})
    assert result.unavoidable_producers == frozenset()


@pytest.mark.parametrize("alternative", [
    _alternative("uncertified-edge", Atom("p", evidence=EdgeEvidence(certified=False))),
    _alternative("havoc", Atom("p", evidence=EdgeEvidence(unknown_havoc=True))),
    _alternative("ambiguous-field", Atom("p", evidence=EdgeEvidence(exact_field=False))),
    _alternative("serializer", Atom("p", evidence=EdgeEvidence(serializer_resolved=False))),
    _alternative("fitted", Atom("p", evidence=EdgeEvidence(fitted_state_resolved=False))),
    _alternative("artifact-writer", Atom("p", EdgeKind.ARTIFACT,
                                         EdgeEvidence(artifact_resolved=False))),
    _alternative("config", Atom("p", EdgeKind.CONFIG, EdgeEvidence(config_resolved=False))),
    _alternative("format", Atom("p", EdgeKind.FORMAT, EdgeEvidence(format_resolved=False))),
    _alternative("unresolved-guard", Atom("p"), feasible=None),
    _alternative("unpinned-guard", Atom("p"), pinned=False),
])
def test_every_composition_abstention_facet_forces_may_only(alternative):
    root = _derivation("root", alternative)
    result = _slice(_program(root))
    assert "p" in result.possible_producers
    assert result.unavoidable_producers == frozenset()


def test_mixed_solver_algebras_without_bridge_and_resource_exhaustion_are_may_only():
    set_node = _derivation("set-node", _alternative(
        "set", Atom("p"), transform=_transform(SETS, "select", members=frozenset({"p"})),
    ))
    mixed_root = _derivation("root", _alternative("affine", Atom("set-node")))
    assert _slice(_program(set_node, mixed_root)).unavoidable_producers == frozenset()

    chain = []
    previous = "p"
    for index in range(5):
        target = f"n{index}"
        chain.append(_derivation(target, _alternative(target, Atom(previous))))
        previous = target
    chain.append(_derivation("root", _alternative("root", Atom(previous))))
    assert _slice(_program(*chain, max_nodes=3)).unavoidable_producers == frozenset()


def test_inexact_claim_root_never_has_unavoidable_producers():
    root = _derivation("root", _alternative("root", Atom("p")))
    result = _slice(_program(root), _claim(exact=False))
    assert result.possible_producers == frozenset({"p"})
    assert result.unavoidable_producers == frozenset()


def test_unmodeled_alternative_constraints_force_may_only():
    constrained = Alternative(
        "constrained", Guard("guard:constrained", True, True), "def:constrained", Atom("p"),
        _transform(), constraints=("p_is_constant_on_feasible_domain",),
    )
    result = _slice(_program(_derivation("root", constrained)))
    assert result.possible_producers == frozenset({"p"})
    assert result.unavoidable_producers == frozenset()
    assert result.coverage_complete is False


def test_each_closed_solver_can_certify_only_its_exact_supported_slice():
    from sc_referee.inference.domains.unit import (
        RelationSource, UnitRef, UnitRelationFact, UnitRelationKind,
    )

    sign = SensitivitySolverKind.SIGN_MONOTONE.value
    sign_root = _derivation("root", _alternative(
        "sign", Atom("p"), transform=_transform(sign, "negate")))
    assert _slice(_program(sign_root)).unavoidable_producers == frozenset({"p"})

    set_root = _derivation("root", _alternative(
        "set", Atom("p"), transform=_transform(SETS, "select", members=frozenset({"p"}))))
    assert _slice(_program(set_root)).unavoidable_producers == frozenset({"p"})

    rows = UnitRef("a", ("row",), "cell", "observation")
    donors = UnitRef("a", ("donor",), "donor", "replication")
    relation = UnitRelationFact(rows, donors, UnitRelationKind.STRICTLY_REFINES,
                                RelationSource.RATIFIED_FACT, "fact:1")
    unit = SensitivitySolverKind.UNIT_PARTITION.value
    unit_root = _derivation("root", _alternative(
        "unit", Atom("p"), transform=_transform(unit, "relation", relation=relation)))
    assert _slice(_program(unit_root)).unavoidable_producers == frozenset({"p"})

    rank = SensitivitySolverKind.EXACT_RATIONAL_RANK.value
    rank_root = _derivation("root", _alternative(
        "rank", Atom("p"), transform=_transform(rank, "projection",
                                                matrix=((1, 0), (0, 1)), target_column=1)))
    assert _slice(_program(rank_root)).unavoidable_producers == frozenset({"p"})
