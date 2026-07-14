from __future__ import annotations


def _exact_region():
    from sc_referee.inference.domains.region import Region, SetBounds

    return Region(
        rows=SetBounds.exact("rows", {"r1", "r2"}),
        patients=SetBounds.exact("patients", {"p1"}),
        time=SetBounds.exact("time", {"t1"}),
        features=SetBounds.exact("features", {"g1", "g2"}),
    )


def _binding(symbol="test"):
    from sc_referee.inference.contracts.schema import SummaryBinding

    return SummaryBinding("pkg.stats", symbol, "1", "sha256:pkg", f"sha256:{symbol}")


def test_grouping_refinement_comes_from_actual_value_not_variable_or_method_name():
    from sc_referee.inference.domains.bilattice import MayMust
    from sc_referee.inference.domains.origin import OriginAtom
    from sc_referee.inference.domains.selection import SelectionEvent
    from sc_referee.inference.domains.unit import UnitRef
    from sc_referee.inference.domains.value import AbsValue
    from sc_referee.inference.refinement.infer import infer_grouping_type

    origin = OriginAtom("primary_data", "artifact:adata", "obs.cluster")
    unit = UnitRef("artifact:adata", ("cell_id",), "cell", "observation")
    selection = SelectionEvent("selection:1", "clustering", ("matrix",), "labels")
    value = AbsValue(
        origins=frozenset({origin}), must_origins=frozenset({origin}), region=_exact_region(),
        units=MayMust(frozenset({unit}), frozenset({unit})),
        selection_events=MayMust(frozenset({selection}), frozenset({selection})),
    )

    named_cluster = infer_grouping_type(value, value_id="v1", source_name="leiden")
    named_design = infer_grouping_type(value, value_id="v1", source_name="predefined_design")
    assert named_cluster == named_design
    assert named_cluster.origin.must == frozenset({origin})
    assert named_cluster.selection_events.must == frozenset({selection})
    assert named_cluster.unit.must == frozenset({unit})
    assert named_cluster.rows == value.region.rows


def test_unknown_grouping_facets_remain_explicit_unknowns():
    from sc_referee.inference.domains.origin import OriginAtom
    from sc_referee.inference.domains.value import AbsValue
    from sc_referee.inference.refinement.infer import infer_grouping_type

    grouping = infer_grouping_type(AbsValue(unknown=True), value_id="v:unknown",
                                   source_name="condition")
    assert grouping.origin.must == frozenset()
    assert any(isinstance(atom, OriginAtom) and atom.kind == "unknown"
               for atom in grouping.origin.may)
    assert grouping.selection_events.must == frozenset()
    assert grouping.rows.boundaries and grouping.features.boundaries


def test_test_type_requires_an_exact_summary_and_ignores_candidate_symbol_name():
    from sc_referee.inference.refinement.infer import TestSummary, infer_test_type
    from sc_referee.inference.refinement.types import (
        DependenceModel, NullContract, SamplingRegime, Statistic,
    )

    summary = TestSummary(
        binding=_binding("rank_test"), statistic=Statistic.RANK_STATISTIC,
        null=NullContract("equality"), sampling_regime=SamplingRegime.IID_ROWS,
        dependence_model=DependenceModel("none_known"), calibration_handling="naive",
    )
    exact = infer_test_type(
        summary, response="value:y", grouping_or_design="value:g", block=None,
        selection_events=None, candidate_symbol="custom_name",
    )
    assert exact.statistic is Statistic.RANK_STATISTIC
    assert exact.response == "value:y" and exact.grouping_or_design == "value:g"

    incomplete = TestSummary(
        binding=type(summary.binding)("pkg.stats", "rank_test", "", "", ""),
        statistic=Statistic.WALD, null=NullContract("equality"),
        sampling_regime=SamplingRegime.IID_ROWS,
        dependence_model=DependenceModel("none_known"), calibration_handling="naive",
    )
    assert infer_test_type(incomplete, response="value:y", grouping_or_design=None,
                           block=None, selection_events=None,
                           candidate_symbol="ttest_ind") is None
    assert infer_test_type(None, response="value:y", grouping_or_design=None,
                           block=None, selection_events=None,
                           candidate_symbol="ttest_ind") is None


def test_pvalue_calibration_requires_exact_test_summary_or_verified_safeguard():
    from sc_referee.inference.domains.calibration import Naive, Valid
    from sc_referee.inference.refinement.infer import (
        TestSummary, VerifiedSafeguard, infer_pvalue_type, infer_test_type,
    )
    from sc_referee.inference.refinement.types import (
        DependenceModel, NullContract, SamplingRegime, Statistic,
    )

    summary = TestSummary(
        _binding("wald"), Statistic.WALD, NullContract("equality"),
        SamplingRegime.CLUSTERED, DependenceModel("cluster_robust", unit="donor"), "naive",
    )
    test = infer_test_type(summary, response="y", grouping_or_design="design", block="donor",
                           selection_events=None, candidate_symbol="anything")
    pvalue = infer_pvalue_type(test, summary, test_event_id="test:1", safeguards=())
    assert pvalue.calibration.modes.must == frozenset({Naive(summary.binding.symbol)})

    safeguard = VerifiedSafeguard("split:1", _binding("split"), "valid",
                                  assumptions=frozenset({"independent_split"}))
    protected = infer_pvalue_type(test, summary, test_event_id="test:1", safeguards=(safeguard,))
    assert protected.calibration.modes.must == frozenset({Valid("split:1", frozenset({"independent_split"}))})
    assert protected.assumptions == frozenset({"independent_split"})


def test_report_claim_type_uses_exact_egress_binding_and_backward_slice():
    from sc_referee.inference.analysis.dependence import (
        Alternative, Atom, DependenceProgram, Derivation, Guard, TransformBinding,
    )
    from sc_referee.inference.claims.inventory import ClaimRootGrade, ReportClaim
    from sc_referee.inference.claims.slice import slice_claim
    from sc_referee.inference.refinement.infer import infer_report_claim_type
    from sc_referee.inference.refinement.types import BindingStatus

    program = DependenceProgram({
        "reported": Derivation("reported", (
            Alternative("a", Guard("g", True, True), "d", Atom("producer"),
                        TransformBinding("affine_linear_q.v1", "identity")),
        )),
    }, {}, frozenset({"producer"}))
    claim = ReportClaim("claim:1", "reported", "pvalue", ClaimRootGrade.ACCUSATION_GRADE, True)
    claim_slice = slice_claim(program, claim)
    refined = infer_report_claim_type(claim, claim_slice)
    assert refined.report_binding is BindingStatus.EXACT
    assert refined.possible_producers == frozenset({"producer"})
    assert refined.unavoidable_producers == frozenset({"producer"})

    inexact = infer_report_claim_type(
        ReportClaim("claim:2", "reported", "pvalue", ClaimRootGrade.DIAGNOSTIC_ONLY, False),
        claim_slice,
    )
    assert inexact.report_binding is BindingStatus.UNKNOWN
    assert inexact.unavoidable_producers == frozenset()


def test_legacy_value_type_projection_discards_rich_facts_without_name_inference():
    from sc_referee.inference.domains.value import AbsValue
    from sc_referee.inference.refinement.infer import infer_grouping_type, project_value_type

    unknown = infer_grouping_type(AbsValue(unknown=True), value_id="v", source_name="genotype")
    projected = project_value_type(unknown)
    assert projected.kind == "labels"
    assert projected.origins == frozenset({"unknown"})
    assert projected.unit == "unknown"


def test_infer_refinements_populates_only_supplied_abstract_facts():
    from sc_referee.inference.domains.value import AbsValue
    from sc_referee.inference.refinement.infer import RefinementFacts, infer_refinements

    facts = RefinementFacts(grouping_values={"g": AbsValue(unknown=True)})
    index = infer_refinements(facts)
    assert set(index.groupings) == {"g"}
    assert index.tests == {} and index.pvalues == {} and index.report_claims == {}


def test_analyze_carries_the_rich_refinement_index_but_guesses_no_facets():
    from sc_referee.inference import AnalysisRequest, analyze
    from sc_referee.inference.refinement.types import RefinementIndex

    snapshot = analyze(AnalysisRequest(("group = condition\n",)))
    assert isinstance(snapshot.refinements, RefinementIndex)
    assert snapshot.refinements.groupings == {}
    assert snapshot.outcome == "ABSTAIN"


def test_increment_9_snapshot_without_a_policy_contract_still_abstains():
    from sc_referee.inference.api import ANALYZER_VERSION, AnalysisRequest, analyze

    assert "increment-9" in ANALYZER_VERSION
    assert analyze(AnalysisRequest(("x = 1",))).outcome == "ABSTAIN"
