from __future__ import annotations


def test_structured_manifest_and_closed_egress_inventory_create_exact_roots():
    from sc_referee.inference.claims.inventory import (
        ClaimRootGrade, Egress, StructuredClaimManifest, StructuredClaimRoot, inventory_claims,
    )

    root = StructuredClaimRoot(
        claim_id="claim:1", report_artifact_digest="sha256:report", report_span_or_field="table.pvalue",
        producing_value="value:p", producer_binding_digest="sha256:producer", claim_role="pvalue",
        ratification_fact_id="fact:claim:1",
    )
    structured = inventory_claims(StructuredClaimManifest((root,)), (), egress_complete=False)
    assert structured.complete is True
    assert structured.claims[0].root_exact is True
    assert structured.claims[0].root_grade is ClaimRootGrade.ACCUSATION_GRADE

    egress = Egress("egress:1", "value:q", "table.qvalue", "qvalue", digest="sha256:egress")
    enumerated = inventory_claims(None, (egress,), egress_complete=True)
    assert enumerated.complete is True
    assert enumerated.claims[0].root_exact is True
    assert enumerated.claims[0].root_grade is ClaimRootGrade.CLEAN_ONLY

    incomplete = inventory_claims(None, (egress,), egress_complete=False)
    assert incomplete.complete is False
    assert incomplete.claims[0].root_exact is False
    assert incomplete.claims[0].root_grade is ClaimRootGrade.DIAGNOSTIC_ONLY
    assert incomplete.unknown_boundaries

    empty_structured = inventory_claims(StructuredClaimManifest(()), (), egress_complete=False)
    assert empty_structured.complete is False
    assert empty_structured.unknown_boundaries


def test_closed_sensitivity_solver_set_has_exactly_five_immutable_members():
    from sc_referee.inference.claims.sensitivity import (
        CLOSED_SOLVER_IDS, SensitivitySolverKind, SensitivitySolverSet,
    )

    assert CLOSED_SOLVER_IDS == frozenset({kind.value for kind in SensitivitySolverKind})
    assert {kind.value for kind in SensitivitySolverKind} == {
        "affine_linear_q.v1", "sign_monotone.v1", "exact_set_membership.v1",
        "unit_partition.v1", "exact_rational_rank.v1",
    }
    solvers = SensitivitySolverSet()
    assert all(solvers.supports(kind.value) for kind in SensitivitySolverKind)
    assert not hasattr(solvers, "register")


def test_sign_set_unit_and_exact_rational_rank_primitives_are_exact_or_unknown():
    from sc_referee.inference.claims.sensitivity import (
        exact_rational_rank, exact_rational_rank_sensitive, exact_set_membership_sensitive,
        sign_monotone_sensitive, unit_partition_sensitive,
    )
    from sc_referee.inference.domains.unit import (
        RelationSource, UnitRef, UnitRelationFact, UnitRelationKind,
    )

    assert sign_monotone_sensitive(("negate", "negate"), factor_signs=()) is True
    assert sign_monotone_sensitive(("multiply",), factor_signs=(0,)) is None
    assert exact_set_membership_sensitive(True, (("select", True), ("remove", True))) is False

    rows = UnitRef("a", ("row",), "cell", "observation")
    donors = UnitRef("a", ("donor",), "donor", "replication")
    exact_relation = UnitRelationFact(rows, donors, UnitRelationKind.STRICTLY_REFINES,
                                      RelationSource.RATIFIED_FACT, "fact:1")
    assert unit_partition_sensitive(exact_relation) is True

    full_rank = ((1, 0), (0, 1))
    aliased = ((1, 1), (2, 2))
    assert exact_rational_rank(full_rank) == 2
    assert exact_rational_rank_sensitive(full_rank, target_column=1) is True
    assert exact_rational_rank_sensitive(aliased, target_column=1) is False
    assert exact_rational_rank_sensitive((), target_column=0) is None
    assert exact_rational_rank_sensitive(((1.5, 0), (0, 1)), target_column=1) is None
    assert exact_rational_rank_sensitive(((1, 0), (1,)), target_column=1) is None
    assert unit_partition_sensitive(None) is None


def test_analyze_inventories_and_slices_structured_claims_but_remains_abstain():
    from sc_referee.inference import AnalysisRequest, analyze
    from sc_referee.inference.claims.inventory import StructuredClaimManifest, StructuredClaimRoot

    root = StructuredClaimRoot(
        "claim:1", "sha256:report", "table.pvalue", "reported", "sha256:producer",
        "pvalue", "fact:claim:1",
    )
    snapshot = analyze(AnalysisRequest(("reported = source\n",),
                                       claims=StructuredClaimManifest((root,))))
    assert snapshot.claims and snapshot.claims[0].claim_id == "claim:1"
    assert "claim:1" in snapshot.claim_slices
    assert snapshot.refinements.report_claims["claim:1"].report_binding.value == "exact"
    assert snapshot.refinements.report_claims["claim:1"].possible_producers == (
        snapshot.claim_slices["claim:1"].possible_producers
    )
    assert snapshot.outcome == "ABSTAIN"
