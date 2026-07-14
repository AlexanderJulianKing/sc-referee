from __future__ import annotations

from dataclasses import replace
from itertools import combinations
from math import inf

import pytest


def _maymust_values():
    from sc_referee.inference.domains.bilattice import MayMust

    universe = frozenset({"a", "b"})
    subsets = [frozenset(combo) for size in range(3) for combo in combinations(universe, size)]
    return [MayMust(may, must) for may in subsets for must in subsets if must <= may]


def test_maymust_cfg_join_lattice_laws_and_monotone_transfer_property():
    values = _maymust_values()

    for left in values:
        assert left.join(left) == left
        for right in values:
            assert left.join(right) == right.join(left)
            # transfer adds one possible fact and never invents a must fact
            transfer_left = left.add_possible("z")
            transfer_join = left.join(right).add_possible("z")
            assert transfer_left.leq(transfer_join)
            for third in values:
                assert left.join(right).join(third) == left.join(right.join(third))


def test_maymust_evidence_meet_laws_on_consistent_refinements():
    values = _maymust_values()
    for left in values:
        assert left.meet(left) == left
        for right in values:
            try:
                lr = left.meet(right)
                rl = right.meet(left)
            except ValueError:
                continue
            assert lr == rl
            for third in values:
                try:
                    assert left.meet(right).meet(third) == left.meet(right.meet(third))
                except ValueError:
                    pass  # contradictory evidence is represented by abstention, not a lattice value


def test_closed_setexpr_region_algebra_and_overlap_proofs():
    from sc_referee.inference.domains.region import (
        All, Difference, Exact, FieldEquals, Image, Intersection, Preimage, Region,
        SetBounds, Union, Unknown, overlap_relation,
    )

    a = SetBounds.exact("rows", {"r1", "r2"})
    b = SetBounds.exact("rows", {"r2", "r3"})
    c = SetBounds.exact("rows", {"r4"})
    assert a.join(b) == b.join(a)
    assert a.join(a) == a
    assert a.join(b).join(c) == a.join(b.join(c))
    assert overlap_relation(a, b) == "definite_overlap"
    assert overlap_relation(a, c) == "disjoint"
    assert overlap_relation(a, SetBounds.dynamic("rows", "mask")) == "unknown"
    assert SetBounds.dynamic("rows", "mask").boundaries == frozenset({"mask"})

    # Every constructor in the closed grammar is representable and remains symbolic when not finite.
    predicate = FieldEquals("rows", "condition", "stim")
    expressions = (
        Union(predicate, Exact("rows", frozenset({"r1"}))),
        Intersection(predicate, All("rows")),
        Difference(predicate, Exact("rows", frozenset({"r2"}))),
        Image("row_to_patient", predicate, "patients"),
        Preimage("row_to_patient", Exact("patients", frozenset({"p1"})), "rows"),
        Unknown("rows", "dynamic"),
    )
    assert len(set(expressions)) == len(expressions)

    region = Region(rows=a, patients=SetBounds.dynamic("patients", "unratified-map"),
                    time=SetBounds.exact("time", {"t1"}),
                    features=SetBounds.exact("features", {"g1"}))
    widened = region.widen(region.join(replace(region, rows=b)))
    assert widened.widened is True
    assert widened.rows.lower.is_empty()
    assert isinstance(widened.rows.upper, All)


def test_setbounds_reduction_rejects_provably_inconsistent_lower_upper():
    from sc_referee.inference.domains.region import Exact, SetBounds

    with pytest.raises(ValueError):
        SetBounds(Exact("rows", frozenset({"r1"})), Exact("rows", frozenset({"r2"})))


def test_patient_region_projection_requires_exact_or_ratified_row_mapping():
    from sc_referee.inference.domains.region import Image, SetBounds, patient_bounds_from_rows

    rows = SetBounds.exact("rows", {"r1", "r2"})
    unknown = patient_bounds_from_rows(rows, "row_to_patient", exact=False, ratified=False)
    assert unknown.lower.is_empty()
    assert unknown.boundaries
    exact = patient_bounds_from_rows(rows, "row_to_patient", exact=True, ratified=False)
    assert isinstance(exact.lower, Image) and isinstance(exact.upper, Image)
    assert exact.boundaries == frozenset()


def test_unit_relations_require_exact_or_ratified_evidence_never_names():
    from sc_referee.inference.domains.unit import (
        RelationSource, UnitRef, UnitRelationIndex, UnitRelationKind,
    )

    spots = UnitRef("artifact:spatial", ("spot_id",), "spot", "observation")
    donors = UnitRef("artifact:spatial", ("donor_id",), "donor", "replication")
    index = UnitRelationIndex()
    index.add(spots, donors, UnitRelationKind.STRICTLY_REFINES,
              source=RelationSource.EXACT_CONSTRUCTION, evidence_id="groupby:1")
    relation = index.relate(spots, donors)
    assert {fact.kind for fact in relation.must} == {UnitRelationKind.STRICTLY_REFINES}

    guessed = index.relate_from_names(
        UnitRef("other", ("spot",), "spot", "observation"),
        UnitRef("other", ("donor",), "donor", "replication"),
    )
    assert guessed.must == frozenset()
    with pytest.raises(ValueError):
        index.add(spots, donors, UnitRelationKind.STRICTLY_REFINES,
                  source="field_names", evidence_id="guess")


def test_calibration_naive_and_selection_must_require_exact_or_ratified_summaries():
    from sc_referee.inference.contracts.schema import SummaryBinding
    from sc_referee.inference.domains.calibration import Naive, UnknownCalibration, infer_calibration
    from sc_referee.inference.domains.selection import SelectionEvent, infer_selection_event

    exact = SummaryBinding("pkg", "test", "1", "sha256:pkg", "sha256:summary")
    unknown_calibration = infer_calibration(contract_id="candidate", handling=None, binding=None)
    assert unknown_calibration.modes.must == frozenset()
    assert any(isinstance(mode, UnknownCalibration) for mode in unknown_calibration.modes.may)
    naive = infer_calibration(contract_id="test.v1", handling="naive", binding=exact)
    assert naive.modes.must == frozenset({Naive("test.v1")})
    incomplete = SummaryBinding("pkg", "test", "", "", "")
    assert infer_calibration(contract_id="test.v1", handling="naive",
                             binding=incomplete).modes.must == frozenset()

    event = SelectionEvent("selection:1", "clustering", ("x",), "labels")
    by_name = infer_selection_event(event, method_name="leiden", binding=None, ratified=False)
    assert by_name.must == frozenset()
    exact_event = infer_selection_event(event, method_name="anything", binding=exact, ratified=False)
    assert exact_event.must == frozenset({event})
    assert infer_selection_event(event, method_name="anything", binding=incomplete,
                                 ratified=False).must == frozenset()
    ratified_event = infer_selection_event(event, method_name="custom", binding=None, ratified=True)
    assert ratified_event.must == frozenset({event})


def test_fitted_state_and_scalar_widening_only_lose_precision():
    from sc_referee.inference.contracts.schema import SummaryBinding
    from sc_referee.inference.domains.fitted import FittedState, infer_fitted_state
    from sc_referee.inference.domains.scalar import ScalarInterval

    fitted = FittedState("fit:1", ("train",), ("features",), ("params",))
    assert infer_fitted_state(fitted, binding=None).must == frozenset()
    exact = SummaryBinding("pkg", "fit", "1", "sha256:pkg", "sha256:summary")
    assert infer_fitted_state(fitted, binding=exact).must == frozenset({fitted})
    incomplete = SummaryBinding("pkg", "fit", "", "", "")
    assert infer_fitted_state(fitted, binding=incomplete).must == frozenset()

    narrow = ScalarInterval(0, 1)
    growing = ScalarInterval(-1, 2)
    widened = narrow.widen(growing)
    assert widened == ScalarInterval(-inf, inf, widened=True)
    assert widened.contains(narrow) and widened.contains(growing)


def test_reduced_value_and_effect_products_preserve_must_subset_may_under_join_and_widen():
    from sc_referee.inference.domains.effects import EffectValue
    from sc_referee.inference.domains.value import AbsValue

    left = AbsValue(points_to=frozenset({"a"}), origins=frozenset({"data"}),
                    must_points_to=frozenset({"a"}), must_origins=frozenset({"data"}))
    right = AbsValue(points_to=frozenset({"a", "b"}), origins=frozenset({"data", "unknown"}),
                     must_points_to=frozenset({"b"}), must_origins=frozenset())
    joined = left.join(right)
    assert joined.must_points_to == frozenset()
    assert joined.must_origins == frozenset()
    assert joined.must_points_to <= joined.points_to
    assert joined.must_origins <= joined.origins
    with pytest.raises(ValueError):
        AbsValue(points_to=frozenset(), must_points_to=frozenset({"impossible"}))

    effects = EffectValue(reads=frozenset({"a"}), writes=frozenset({"a"}),
                          must_reads=frozenset(), must_writes=frozenset())
    assert effects.must_reads <= effects.reads and effects.must_writes <= effects.writes
    with pytest.raises(ValueError):
        EffectValue(reads=frozenset(), must_reads=frozenset({"impossible"}))

    widened = left.widen(right)
    assert "<unknown-heap>" in widened.points_to
    assert widened.must_points_to == frozenset()
    assert "points_to" in widened.widened_facets


def test_worklist_widening_terminates_and_marks_the_precision_loss():
    from sc_referee.inference.analysis.fixpoint import solve
    from sc_referee.inference.domains.scalar import ScalarInterval

    successors = {"entry": ("loop",), "loop": ("loop", "exit"), "exit": ()}

    def transfer(block, state):
        if block == "loop" and state.upper != inf:
            return ScalarInterval(state.lower, state.upper + 1, state.widened)
        return state

    result = solve(
        successors=successors, entry="entry", initial=ScalarInterval(0, 0), transfer=transfer,
        join=lambda left, right: left.join(right), widen=lambda left, right: left.widen(right),
        growth_before_widen=2,
    )
    assert result.steps < 30
    assert "loop" in result.widened_points
    assert result.states["exit"].upper == inf
    assert result.states["exit"].widened is True


def test_fixpoint_runs_one_explicit_narrowing_pass_for_exact_guards():
    from sc_referee.inference.analysis.fixpoint import solve
    from sc_referee.inference.domains.scalar import ScalarInterval

    successors = {"entry": ("loop",), "loop": ("loop", "exit"), "exit": ()}

    def transfer(block, state):
        if block == "loop" and state.upper != inf:
            return ScalarInterval(state.lower, state.upper + 1, state.widened)
        return state

    guard = ScalarInterval(0, 10)
    result = solve(
        successors=successors, entry="entry", initial=ScalarInterval(0, 0), transfer=transfer,
        join=lambda left, right: left.join(right), widen=lambda left, right: left.widen(right),
        growth_before_widen=2,
        narrow=lambda block, state: state.meet(guard) if block in {"loop", "exit"} else state,
    )
    assert result.states["loop"].upper == 10
    assert result.narrowed_points == frozenset({"loop", "exit"})


def test_loop_must_fact_requires_proved_iteration_and_preservation():
    from sc_referee.inference.analysis.fixpoint import loop_may_must
    from sc_referee.inference.domains.bilattice import MayMust

    pre = MayMust(frozenset(), frozenset())
    body = MayMust(frozenset({"inside"}), frozenset({"inside"}))
    zero_or_more = loop_may_must(pre, body, at_least_one_iteration=False, preserved=True)
    not_preserved = loop_may_must(pre, body, at_least_one_iteration=True, preserved=False)
    definite = loop_may_must(pre, body, at_least_one_iteration=True, preserved=True)
    assert zero_or_more.must == frozenset()
    assert not_preserved.must == frozenset()
    assert definite.must == frozenset({"inside"})
    assert definite.must <= definite.may
    pre_fact = MayMust(frozenset({"pre"}), frozenset({"pre"}))
    body_fact = MayMust(frozenset({"pre"}), frozenset({"pre"}))
    assert loop_may_must(pre_fact, body_fact, at_least_one_iteration=True,
                         preserved=False).must == frozenset()
