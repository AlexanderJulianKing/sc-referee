import ast
from dataclasses import replace
from pathlib import Path

import pytest

from sc_referee import statuses as S
from sc_referee.checks.confounding import (
    OMITTED_R2_MAJOR, _dummy_block, _partial_r2, _r2, _with_intercept,
)
from sc_referee.checks.confounding_random_intercept import ConfoundingRandomInterceptCheck
from sc_referee.checks.confounding_strong import ConfoundingStrongCheck
from tests.factories import (
    fitted_design_declaration,
    fixed_and_random_certified_fixture,
    make_design,
    pseudobulk_confounding_bundle,
    random_intercept_batch_declaration,
    random_intercept_design,
)


def test_g_scope_requires_condition_de_and_high_ratified_random_mode():
    bundle = pseudobulk_confounding_bundle()
    check = ConfoundingRandomInterceptCheck()
    absent = make_design(batch=("run",), fitted_design=fitted_design_declaration())
    random = random_intercept_design(bundle, adjusted=["condition"])
    low_entry = replace(
        random.fitted_design.batch_modeling["run"],
        field_confidence={**random.fitted_design.batch_modeling["run"].field_confidence,
                          "modeled_as": "low"},
    )
    low = replace(random, fitted_design=replace(random.fitted_design,
                                                batch_modeling={"run": low_entry}))
    assert not check.applies_to(absent, bundle)
    for mode in ("fixed", "absent", "upstream_handled", "unsupported"):
        scoped_out = replace(absent, fitted_design=replace(
            absent.fitted_design,
            batch_modeling={"run": random_intercept_batch_declaration(modeled_as=mode)},
        ))
        assert not check.applies_to(scoped_out, bundle)
    wrong_key = replace(absent, fitted_design=replace(
        absent.fitted_design,
        batch_modeling={"plate": random_intercept_batch_declaration(source_column="plate")},
    ))
    assert not check.applies_to(wrong_key, bundle)
    assert not check.applies_to(low, bundle)
    assert not check.applies_to(replace(random, analysis_type="marker_detection"), bundle)
    assert check.applies_to(random, bundle)


def test_random_intercept_only_material_batch_is_not_checked_proposal():
    bundle = pseudobulk_confounding_bundle()
    design = random_intercept_design(bundle, adjusted=["condition"])
    finding = ConfoundingRandomInterceptCheck().run(design, bundle)
    assert (finding.status, finding.coverage, finding.applicability, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.UNKNOWN, S.NOT_CHECKED,
    )
    assert finding.metrics["batch_outcomes"][0]["batch_partial_r2"] >= OMITTED_R2_MAJOR
    assert ("a random intercept partial-pools; it does not project. this does not condition on "
            "the batch the way a fixed effect does.") in finding.verdict.lower()
    for forbidden in ("biased", "bias", "omitted", "major", "blocker", "magnitude"):
        assert forbidden not in finding.verdict.lower()


def test_random_intercept_only_nonmaterial_batch_is_narrow_clear_using_partial_r2():
    bundle = pseudobulk_confounding_bundle(with_w=True)
    design = random_intercept_design(bundle, adjusted=["W", "condition"], with_w=True)
    sub = bundle.observations.reset_index(drop=True)
    t = (sub["condition"] == "stim").to_numpy(dtype=float)
    marginal = _r2(t, _with_intercept(_dummy_block(sub, ["run"]), len(sub)))
    partial = _partial_r2(sub, t, ["W"], ["run"])
    finding = ConfoundingRandomInterceptCheck().run(design, bundle)
    assert marginal >= OMITTED_R2_MAJOR and partial < OMITTED_R2_MAJOR
    assert (finding.status, finding.coverage, finding.applicability, S.human_state(finding)) == (
        S.PASS, S.COMPLETE, S.APPLIES, S.CLEAR,
    )
    assert finding.judgment == S.CONFORMANT
    assert finding.metrics["batch_outcomes"][0]["batch_partial_r2"] == partial
    assert finding.verdict == (
        "This specific random-intercept-on-a-materially-associated-batch concern was not "
        "triggered; the exact condition–batch partial R² was below the frozen threshold."
    )


def test_fixed_and_random_certified_span_defers_to_a():
    design, bundle = fixed_and_random_certified_fixture()
    stage1 = ConfoundingRandomInterceptCheck().run(design, bundle)
    strong = ConfoundingStrongCheck().run(design, bundle)
    assert (stage1.status, stage1.coverage, stage1.applicability, S.human_state(stage1)) == (
        S.PASS, S.COMPLETE, S.NOT_APPLICABLE, S.N_A,
    )
    assert strong.status == S.PASS and S.human_state(strong) == S.CLEAR


def _mutated_case(mutation):
    bundle = pseudobulk_confounding_bundle()
    design = random_intercept_design(bundle, adjusted=["condition"])
    entry = mutation(design.fitted_design.batch_modeling["run"])
    return replace(design, fitted_design=replace(design.fitted_design,
                                                 batch_modeling={"run": entry})), bundle


@pytest.mark.parametrize("mutation,machine_reason", [
    (lambda entry: replace(entry, field_confidence={**entry.field_confidence, "rows_exact": "low"}),
     "batch_ledger_unratified"),
    (lambda entry: replace(entry, rows_exact=False), "batch_rows_not_exact"),
    (lambda entry: replace(entry, row_ledger_identity="stale"), "batch_row_identity_mismatch"),
    (lambda entry: replace(entry, unsupported_components=("random_slope",)),
     "unsupported_batch_component"),
    (lambda entry: replace(entry, fixed_source_columns=None), "fixed_sources_unresolved"),
])
def test_inexact_or_unsupported_ledger_is_not_audited(mutation, machine_reason):
    design, bundle = _mutated_case(mutation)
    finding = ConfoundingRandomInterceptCheck().run(design, bundle)
    assert (finding.status, finding.coverage, finding.applicability, S.human_state(finding)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.UNKNOWN, S.NOT_CHECKED,
    )
    assert finding.metrics["machine_reason"] == machine_reason


def test_formula_random_intercept_never_upgrades_missing_ledger():
    bundle = pseudobulk_confounding_bundle()
    design = make_design(batch=("run",), fitted_design=fitted_design_declaration())
    design = replace(design, model="~ condition + (1|run)")
    check = ConfoundingRandomInterceptCheck()
    assert not check.applies_to(design, bundle)
    finding = check.run(design, bundle)
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.NOT_CHECKED,
    )
    assert finding.metrics["machine_reason"] == "batch_ledger_unratified"


def test_random_intercept_with_certified_fixed_proxy_span_is_n_a():
    bundle = pseudobulk_confounding_bundle()
    design = random_intercept_design(
        bundle, adjusted=["run", "condition"], operator_kind="ordinary_fixed_effects",
        modeled_as="random_intercept", fixed_source_columns=("run",),
    )
    finding = ConfoundingRandomInterceptCheck().run(design, bundle)
    assert (finding.status, finding.coverage, finding.applicability, S.human_state(finding)) == (
        S.PASS, S.COMPLETE, S.NOT_APPLICABLE, S.N_A,
    )


def test_fixed_and_random_without_certified_span_is_not_audited():
    bundle = pseudobulk_confounding_bundle()
    design = random_intercept_design(
        bundle, adjusted=["condition"], modeled_as="fixed_and_random_intercept",
        fixed_source_columns=("run",),
    )
    finding = ConfoundingRandomInterceptCheck().run(design, bundle)
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.NOT_CHECKED,
    )
    assert finding.metrics["machine_reason"] == "fixed_span_not_certified"


def test_multi_batch_abstention_is_not_hidden_by_a_narrow_clear():
    bundle = pseudobulk_confounding_bundle(with_w=True)
    design = random_intercept_design(bundle, adjusted=["W", "condition"], with_w=True)
    design = replace(design, batch=["run", "plate"])
    finding = ConfoundingRandomInterceptCheck().run(design, bundle)
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.NOT_CHECKED,
    )
    assert [row["category"] for row in finding.metrics["batch_outcomes"]] == ["clear", "abstain"]


def test_nothing_stage1_can_render_flagged_or_emit_an_adverse_status():
    bundle = pseudobulk_confounding_bundle()
    with_w_bundle = pseudobulk_confounding_bundle(with_w=True)
    fixed_unverified = random_intercept_design(
        bundle, adjusted=["condition"], modeled_as="fixed_and_random_intercept",
        fixed_source_columns=("run",),
    )
    proxy = random_intercept_design(
        bundle, adjusted=["run", "condition"], operator_kind="ordinary_fixed_effects",
        fixed_source_columns=("run",),
    )
    designs = [
        (random_intercept_design(bundle, adjusted=["condition"]), bundle),
        (random_intercept_design(with_w_bundle, adjusted=["W", "condition"], with_w=True),
         with_w_bundle),
        (_mutated_case(lambda entry: replace(entry, rows_exact=False))[0], bundle),
        (fixed_and_random_certified_fixture()[0], bundle),
        (fixed_unverified, bundle),
        (proxy, bundle),
    ]
    findings = [ConfoundingRandomInterceptCheck().run(design, case_bundle)
                for design, case_bundle in designs]
    assert all(S.human_state(finding) != S.FLAGGED for finding in findings)
    assert all(finding.status in {S.PASS, S.NOT_AUDITED, S.NEEDS_EVIDENCE} for finding in findings)
    assert all(finding.judgment not in {S.VIOLATION, S.CONCERN} for finding in findings)
    assert ConfoundingRandomInterceptCheck.max_status == S.NEEDS_EVIDENCE


def test_stage1_source_has_no_adverse_or_later_policy_symbols():
    source = Path("src/sc_referee/checks/confounding_random_intercept.py").read_text()
    tree = ast.parse(source)
    attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
             and isinstance(node.value, ast.Name) and node.value.id == "S"}
    assert not attrs & {"MAJOR", "BLOCKER", "INFORMATIONAL", "VIOLATION", "CONCERN"}
    assert ConfoundingRandomInterceptCheck.max_status == S.NEEDS_EVIDENCE
