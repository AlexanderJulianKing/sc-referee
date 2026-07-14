from dataclasses import replace

import pytest

from sc_referee import statuses as S
from sc_referee.checks.confounding import OMITTED_R2_MAJOR
from sc_referee.checks.confounding_random_intercept import ConfoundingRandomInterceptCheck
from sc_referee.checks.confounding_random_intercept_conditional import (
    CHECK_ID,
    ConfoundingRandomInterceptConditionalCheck,
)
from sc_referee.registry import checks_for
from tests.csp_factories import bind_ratified_between_group_contract
from tests.factories import (
    fixed_and_random_certified_fixture,
    pseudobulk_confounding_bundle,
    random_intercept_design,
)


def _material_case(*, ratified=False):
    bundle = pseudobulk_confounding_bundle()
    design = replace(random_intercept_design(bundle, adjusted=["condition"]),
                     estimand_id="condition-effect/v1")
    if ratified:
        design = bind_ratified_between_group_contract(design, bundle, batch="run")
    return design, bundle


def test_ratified_material_re_only_batch_is_conditional_major_end_to_end():
    design, bundle = _material_case(ratified=True)
    finding = ConfoundingRandomInterceptConditionalCheck().run(design, bundle)
    assert (
        finding.status, finding.coverage, finding.applicability,
        finding.judgment, S.human_state(finding),
    ) == (S.MAJOR, S.COMPLETE, S.APPLIES, S.VIOLATION, S.FLAGGED)
    assert finding.check_id == CHECK_ID
    assert "conditional on your confirmation that" in finding.verdict.lower()
    assert "arbitrary differences among run groups must be removed" in finding.verdict.lower()
    assert finding.metrics["contract_id"] == design.csp_contracts[0].contract_id
    assert finding.metrics["contract_type"] == "between_group_adjustment_obligation/v1"
    assert finding.metrics["decisive_fields"] == {
        "between_group_policy": "remove_arbitrary",
        "may_rely_on_re_exogeneity": False,
    }
    assert finding.metrics["batch_outcome"]["batch_partial_r2"] >= OMITTED_R2_MAJOR
    assert finding.conditional_on.contract_id == finding.metrics["contract_id"]


def test_same_batch_without_obligation_is_unchanged_stage1_not_checked_only():
    design, bundle = _material_case(ratified=False)
    ids = [check.id for check in checks_for(design, bundle)]
    assert "confounding_random_intercept" in ids
    assert CHECK_ID not in ids
    finding = ConfoundingRandomInterceptCheck().run(design, bundle)
    assert (
        finding.status, finding.coverage, finding.applicability,
        finding.judgment, S.human_state(finding),
    ) == (S.NEEDS_EVIDENCE, S.NOT_RUN, S.UNKNOWN, None, S.NOT_CHECKED)
    assert finding.metrics["machine_reason"] == "material_association"
    assert finding.conditional_on is None


def test_ratified_route_has_stage2_and_not_stage1_proposal():
    design, bundle = _material_case(ratified=True)
    ids = [check.id for check in checks_for(design, bundle)]
    assert CHECK_ID in ids
    assert "confounding_random_intercept" not in ids


@pytest.mark.parametrize("column", ["condition", "run"])
def test_assignment_reshuffle_invalidates_contract_and_routes_stage1_not_checked(column):
    design, bundle = _material_case(ratified=True)
    bundle.observations[column] = bundle.observations[column].iloc[::-1].to_numpy()
    ids = [check.id for check in checks_for(design, bundle)]
    assert CHECK_ID not in ids and "confounding_random_intercept" in ids
    finding = ConfoundingRandomInterceptCheck().run(design, bundle)
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )


def test_mixed_ratification_routes_each_batch_exactly_once():
    from sc_referee.engine import build_pseudobulk_sample_rows

    design, bundle = _material_case(ratified=False)
    bundle.observations["site"] = bundle.observations["run"].map({"R1": "S1", "R2": "S2"})
    rows = build_pseudobulk_sample_rows(bundle.observations, design)
    run_entry = design.fitted_design.batch_modeling["run"]
    site_entry = replace(
        run_entry, source_column="site", random_group_column="site",
        row_ledger_identity=rows.row_ledger_identity,
    )
    fitted = replace(
        design.fitted_design,
        column_kinds={**design.fitted_design.column_kinds, "site": "categorical"},
        categorical_levels={**design.fitted_design.categorical_levels,
                            "site": ("S1", "S2")},
        transforms={**design.fitted_design.transforms, "site": "identity"},
        batch_modeling={"run": run_entry, "site": site_entry},
    )
    design = replace(design, batch=["run", "site"], fitted_design=fitted)
    design = bind_ratified_between_group_contract(design, bundle, batch="run")

    ids = [check.id for check in checks_for(design, bundle)]
    assert ids.count(CHECK_ID) == 1
    assert ids.count("confounding_random_intercept") == 1
    stage1 = ConfoundingRandomInterceptCheck().run(design, bundle)
    stage2 = ConfoundingRandomInterceptConditionalCheck().run(design, bundle)
    assert [row["batch"] for row in stage1.metrics["batch_outcomes"]] == ["site"]
    assert stage2.metrics["batch_outcome"]["batch"] == "run"


@pytest.mark.parametrize("answer", [True, None])
def test_wrong_or_uncertain_teach_back_never_unlocks_major(answer):
    design, bundle = _material_case(ratified=True)
    record = design.csp_contracts[0]
    field = record.fields["may_rely_on_re_exogeneity"]
    state = (field.state if answer is True else
             __import__("sc_referee.csp", fromlist=["CspFieldState"]).CspFieldState.UNRESOLVED)
    altered = replace(field, value=answer, state=state, confidence="low",
                      selected_teach_back_id="may_rely" if answer is True else None)
    design = replace(design, csp_contracts=(replace(
        record, fields={**record.fields, "may_rely_on_re_exogeneity": altered}),))
    ids = [check.id for check in checks_for(design, bundle)]
    assert CHECK_ID not in ids
    assert S.human_state(ConfoundingRandomInterceptCheck().run(design, bundle)) == S.NOT_CHECKED


def test_bare_high_confidence_batch_declaration_is_not_the_obligation():
    design, bundle = _material_case(ratified=False)
    design.confidence["batch"] = "high"
    assert design.batch == ["run"]
    assert CHECK_ID not in [check.id for check in checks_for(design, bundle)]
    assert S.human_state(ConfoundingRandomInterceptCheck().run(design, bundle)) == S.NOT_CHECKED


def test_scope_change_clears_flag_to_stage1_proposal():
    design, bundle = _material_case(ratified=True)
    assert S.human_state(ConfoundingRandomInterceptConditionalCheck().run(design, bundle)) == S.FLAGGED
    changed = replace(design, estimand_id="changed-estimand/v2")
    ids = [check.id for check in checks_for(changed, bundle)]
    assert CHECK_ID not in ids and "confounding_random_intercept" in ids
    finding = ConfoundingRandomInterceptCheck().run(changed, bundle)
    assert (finding.status, finding.coverage, finding.applicability,
            finding.judgment, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.UNKNOWN, None, S.NOT_CHECKED,
    )


@pytest.mark.parametrize("scope_field", [
    "fitted_result_id", "target_coefficient", "row_ledger_identity",
    "estimand_id", "exposure_column", "group_source_column",
])
def test_each_bound_scope_identity_change_clears_to_stage1_not_checked(scope_field):
    design, bundle = _material_case(ratified=True)
    record = design.csp_contracts[0]
    stale_scope = replace(
        record.scope, **{scope_field: getattr(record.scope, scope_field) + "-changed"}
    )
    changed = replace(design, csp_contracts=(replace(record, scope=stale_scope),))
    ids = [check.id for check in checks_for(changed, bundle)]
    assert CHECK_ID not in ids and "confounding_random_intercept" in ids
    finding = ConfoundingRandomInterceptCheck().run(changed, bundle)
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED,
    )
    assert finding.conditional_on is None


def test_g_fixed_span_ratified_certified_batch_defers_to_strong_clear():
    design, bundle = fixed_and_random_certified_fixture()
    design = replace(design, estimand_id="condition-effect/v1")
    design = bind_ratified_between_group_contract(design, bundle, batch="run")
    assert CHECK_ID in [check.id for check in checks_for(design, bundle)]
    finding = ConfoundingRandomInterceptConditionalCheck().run(design, bundle)
    assert (finding.status, finding.coverage, finding.applicability,
            finding.judgment, S.human_state(finding)) == (
        S.PASS, S.COMPLETE, S.NOT_APPLICABLE, None, S.N_A,
    )
    assert finding.conditional_on is None
    assert S.human_state(finding) != S.FLAGGED


def test_direct_stage2_abstention_and_narrow_clear_pin_all_axes():
    design, bundle = _material_case(ratified=False)
    abstain = ConfoundingRandomInterceptConditionalCheck().run(design, bundle)
    assert (abstain.status, abstain.coverage, abstain.applicability,
            abstain.judgment, S.human_state(abstain)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.UNKNOWN, None, S.NOT_CHECKED,
    )
    with_w = pseudobulk_confounding_bundle(with_w=True)
    clear_design = replace(random_intercept_design(
        with_w, adjusted=["W", "condition"], with_w=True),
        estimand_id="condition-effect/v1",
    )
    clear_design = bind_ratified_between_group_contract(clear_design, with_w)
    clear = ConfoundingRandomInterceptConditionalCheck().run(clear_design, with_w)
    assert (clear.status, clear.coverage, clear.applicability,
            clear.judgment, S.human_state(clear)) == (
        S.PASS, S.COMPLETE, S.APPLIES, S.CONFORMANT, S.CLEAR,
    )
    assert clear.conditional_on is None


def test_severity_caps_remain_separate():
    assert ConfoundingRandomInterceptConditionalCheck.max_status == S.MAJOR
    assert ConfoundingRandomInterceptCheck.max_status == S.NEEDS_EVIDENCE


def test_arithmetic_strong_major_remains_autonomous_without_marker():
    from sc_referee.checks.confounding_strong import ConfoundingStrongCheck
    from tests.test_confounding_strong import _strong_design

    arithmetic = ConfoundingStrongCheck().run(
        _strong_design(adjusted=["condition"]), pseudobulk_confounding_bundle()
    )
    conditional_design, bundle = _material_case(ratified=True)
    conditional = ConfoundingRandomInterceptConditionalCheck().run(conditional_design, bundle)
    assert arithmetic.status == conditional.status == S.MAJOR
    assert arithmetic.conditional_on is None
    assert conditional.conditional_on is not None


def _wizard_design(tmp_path, teach_back):
    import yaml
    from sc_referee.config import load_designs
    from sc_referee.wizard import answers_to_config
    from tests.test_wizard_csp import _proposal_with_csp
    from tests.test_wizard_random_intercept_ledger import _answers

    bundle = pseudobulk_confounding_bundle()
    config = answers_to_config(
        _answers() | {
            "csp.run.between_group_policy": "remove_arbitrary",
            "csp.run.may_rely_on_re_exogeneity": teach_back,
            "csp.run.authority_attested": "yes",
            "csp.run.consequence_acknowledged": "yes",
        },
        bundle.observations,
        proposed_config=_proposal_with_csp(),
    )
    path = tmp_path / f"{teach_back}.yaml"
    path.write_text(yaml.safe_dump(config))
    return load_designs(path)[0], bundle


def test_complete_wizard_ceremony_unlocks_the_end_to_end_conditional_major(tmp_path):
    design, bundle = _wizard_design(tmp_path, "must_not_rely")
    ids = [check.id for check in checks_for(design, bundle)]
    assert CHECK_ID in ids and "confounding_random_intercept" not in ids
    assert S.human_state(
        ConfoundingRandomInterceptConditionalCheck().run(design, bundle)
    ) == S.FLAGGED


@pytest.mark.parametrize("teach_back", ["may_rely", "not_sure"])
def test_wrong_or_not_sure_wizard_teach_back_routes_to_stage1_not_checked(
    tmp_path, teach_back
):
    design, bundle = _wizard_design(tmp_path, teach_back)
    ids = [check.id for check in checks_for(design, bundle)]
    assert CHECK_ID not in ids and "confounding_random_intercept" in ids
    finding = ConfoundingRandomInterceptCheck().run(design, bundle)
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED,
    )


@pytest.mark.parametrize("case, expected", [
    ("absent", (S.NOT_AUDITED, S.NOT_RUN, S.UNKNOWN, None, S.NOT_CHECKED)),
    ("material", (S.MAJOR, S.COMPLETE, S.APPLIES, S.VIOLATION, S.FLAGGED)),
    ("clear", (S.PASS, S.COMPLETE, S.APPLIES, S.CONFORMANT, S.CLEAR)),
    ("fixed_certified", (S.PASS, S.COMPLETE, S.NOT_APPLICABLE, None, S.N_A)),
    ("structure_unavailable", (S.NOT_AUDITED, S.NOT_RUN, S.UNKNOWN, None, S.NOT_CHECKED)),
])
def test_direct_stage2_verdict_table_pins_all_five_axes(case, expected):
    if case == "absent":
        design, bundle = _material_case(ratified=False)
    elif case == "material":
        design, bundle = _material_case(ratified=True)
    elif case == "clear":
        bundle = pseudobulk_confounding_bundle(with_w=True)
        design = replace(random_intercept_design(
            bundle, adjusted=["W", "condition"], with_w=True
        ), estimand_id="condition-effect/v1")
        design = bind_ratified_between_group_contract(design, bundle)
    elif case == "fixed_certified":
        design, bundle = fixed_and_random_certified_fixture()
        design = bind_ratified_between_group_contract(
            replace(design, estimand_id="condition-effect/v1"), bundle
        )
    else:
        bundle = pseudobulk_confounding_bundle()
        design = random_intercept_design(
            bundle, adjusted=["condition"], modeled_as="fixed_and_random_intercept",
            fixed_source_columns=("run",),
        )
        design = bind_ratified_between_group_contract(
            replace(design, estimand_id="condition-effect/v1"), bundle
        )
    finding = ConfoundingRandomInterceptConditionalCheck().run(design, bundle)
    actual = (finding.status, finding.coverage, finding.applicability,
              finding.judgment, S.human_state(finding))
    assert actual == expected
    if case != "material":
        assert finding.conditional_on is None
