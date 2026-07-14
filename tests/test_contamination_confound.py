from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import numpy as np
import pytest

from sc_referee import statuses as S
from sc_referee.checks.contamination_confound import ContaminationConfoundCheck
from sc_referee.checks.base import ConditionalPremise
from tests.contamination_factories import contamination_case
from tests.contamination_factories import ratified_contamination_record


def test_same_rows_and_coefficient_flip_only_on_containment():
    no_rho, bundle = contamination_case(adjusted=("condition",), ratified=True)
    with_rho, with_bundle = contamination_case(
        adjusted=("condition", "rho_external"), ratified=True
    )
    major = ContaminationConfoundCheck().run(no_rho, bundle)
    clear = ContaminationConfoundCheck().run(with_rho, with_bundle)
    assert (major.status, major.coverage, major.judgment, S.human_state(major)) == (
        S.MAJOR, S.COMPLETE, S.VIOLATION, S.FLAGGED,
    )
    assert (clear.status, clear.coverage, clear.judgment, S.human_state(clear)) == (
        S.PASS, S.COMPLETE, S.CONFORMANT, S.CLEAR,
    )
    assert major.metrics["row_ledger_identity"] == clear.metrics["row_ledger_identity"]
    assert major.metrics["target_coefficient"] == clear.metrics["target_coefficient"]


def test_live_fitted_result_binding_is_described_at_its_honest_ceiling():
    design, bundle = contamination_case(adjusted=("condition",), ratified=True)
    finding = ContaminationConfoundCheck().run(design, bundle)
    expected = "matrix_digest_plus_ordered_row_ledger;live_result_id_unavailable"
    assert finding.metrics["fitted_result_binding"] == expected
    assert finding.conditional_on.scope["fitted_result_binding"] == expected
    assert finding.metrics["fitted_design_identity"] == \
        design.csp_contracts[0].scope.contract_scope["fitted_design_identity"]


def test_swapped_live_exposure_assignments_invalidate_ratified_causal_scope():
    design, bundle = contamination_case(adjusted=("condition",), ratified=True)
    bundle.observations["condition"] = bundle.observations["condition"].iloc[::-1].to_numpy()
    finding = ContaminationConfoundCheck().run(design, bundle)
    assert finding.metrics["machine_reason"] == "ratified_scope_or_rows_mismatch"
    assert (finding.coverage, finding.judgment, S.human_state(finding), finding.conditional_on) == (
        S.NOT_RUN, S.UNRESOLVED, S.NOT_CHECKED, None,
    )


def test_live_assignment_scalar_with_broken_item_does_not_crash():
    # A scalar's identity is its VALUE; a broken .item() hook is irrelevant to it and must not crash
    # the check. The exact value "D1" is used, so the check proceeds to its real verdict.
    class ExplodingStr(str):
        def item(self):
            raise RuntimeError("crafted scalar conversion failure")

    design, bundle = contamination_case(adjusted=("condition",), ratified=True)
    first = bundle.observations.index[0]
    bundle.observations.at[first, "donor_id"] = ExplodingStr("D1")
    finding = ContaminationConfoundCheck().run(design, bundle)          # must not raise
    assert finding.metrics["machine_reason"] in {"certified", "not_certified"}


def test_genuine_assignment_defect_surfaces_instead_of_being_masked(monkeypatch):
    # The narrowed catch (TypeError/ValueError only) must let a genuine internal defect propagate,
    # rather than silently converting it to not_checked and withholding a valid verdict.
    design, bundle = contamination_case(adjusted=("condition",), ratified=True)

    def boom(*args, **kwargs):
        raise RuntimeError("internal regression")

    monkeypatch.setattr(
        "sc_referee.checks.contamination_confound.assignment_identity", boom
    )
    with pytest.raises(RuntimeError, match="internal regression"):
        ContaminationConfoundCheck().run(design, bundle)


def test_identical_values_under_different_group_name_do_not_bind_aggregation_scope():
    from sc_referee.csp import assignment_identity
    from sc_referee.engine import build_pseudobulk_sample_rows
    from tests.test_contamination_confound_redteam import _thaw

    design, bundle = contamination_case(adjusted=("condition",), ratified=True)
    bundle.observations["donor_alias"] = bundle.observations["donor_id"]
    design = replace(design, replicate_unit=["donor_id", "donor_alias"])
    rows = build_pseudobulk_sample_rows(bundle.observations, design)
    alias_assignment = assignment_identity(rows.rows, "condition", "donor_alias")
    original = design.csp_contracts[0]
    values = {field: _thaw(entry.value) for field, entry in original.fields.items()}
    values["assignment_context"]["assignment_identity"] = alias_assignment
    scope = replace(
        original.scope, group_source_column="donor_alias",
        assignment_identity=alias_assignment,
    )
    alias_record = ratified_contamination_record(scope=scope, values=values)
    finding = ContaminationConfoundCheck().run(
        replace(design, csp_contracts=(alias_record,)), bundle
    )
    assert finding.metrics["machine_reason"] == "ratified_scope_or_rows_mismatch"
    assert S.human_state(finding) == S.NOT_CHECKED


def test_rows_output_vector_digest_is_enforced_during_replay():
    from tests.test_contamination_confound_redteam import _thaw

    design, bundle = contamination_case(adjusted=("condition",), ratified=True)
    original = design.csp_contracts[0]
    values = {field: _thaw(entry.value) for field, entry in original.fields.items()}
    values["rows_and_aggregation"]["output_vector_digest"] = "sha256:" + "0" * 64
    stale = ratified_contamination_record(scope=original.scope, values=values)
    finding = ContaminationConfoundCheck().run(
        replace(design, csp_contracts=(stale,)), bundle
    )
    assert finding.metrics["machine_reason"] == "output_vector_digest_mismatch"
    assert (finding.coverage, S.human_state(finding), finding.conditional_on) == (
        S.NOT_RUN, S.NOT_CHECKED, None,
    )


def test_unratified_noncontainment_never_calls_geometry():
    design, bundle = contamination_case(adjusted=("condition",), ratified=False)
    with patch(
        "sc_referee.checks.contamination_confound.certify_column_space",
        side_effect=AssertionError("geometry unreachable"),
    ):
        finding = ContaminationConfoundCheck().run(design, bundle)
    assert (
        finding.status, finding.coverage, finding.applicability,
        finding.judgment, S.human_state(finding),
    ) == (S.NEEDS_EVIDENCE, S.NOT_RUN, S.UNKNOWN, S.UNRESOLVED, S.NOT_CHECKED)


def test_random_intercept_is_not_fixed_conditioning():
    design, bundle = contamination_case(ratified=True, operator_kind="random_intercept_only")
    finding = ContaminationConfoundCheck().run(design, bundle)
    assert (finding.status, finding.coverage, finding.judgment, S.human_state(finding)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.UNRESOLVED, S.NOT_CHECKED,
    )
    assert finding.metrics["machine_reason"] == "no_verified_conditioning_operator"


@pytest.mark.parametrize("role", ["weight_role", "offset_role"])
def test_weight_or_offset_abstains(role):
    kwargs = {role: "analysis_weight"}
    design, bundle = contamination_case(ratified=True, **kwargs)
    finding = ContaminationConfoundCheck().run(design, bundle)
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.NOT_CHECKED,
    )


def test_equivalent_reparameterization_that_spans_h_passes():
    rho = np.asarray([.05, .13, .22, .31, .57, .68, .79, .91])
    design, bundle = contamination_case(adjusted=("condition", "rho_external"), rho_values=2*rho+1)
    finding = ContaminationConfoundCheck().run(design, bundle)
    assert (finding.status, S.human_state(finding)) == (S.PASS, S.CLEAR)


def test_exposure_equal_h_cannot_certify_through_exposure():
    exposure = [0., 0., 0., 0., 1., 1., 1., 1.]
    design, bundle = contamination_case(adjusted=("condition",), rho_values=exposure)
    finding = ContaminationConfoundCheck().run(design, bundle)
    assert finding.status == S.MAJOR
    assert "condition" in finding.metrics["excluded_exposure_columns"]


def test_nonfinite_h_abstains_without_geometry():
    design, bundle = contamination_case(ratified=True)
    bundle.observations.loc[bundle.observations.index[0], "rho_external"] = np.nan
    with patch(
        "sc_referee.checks.contamination_confound.certify_column_space",
        side_effect=AssertionError("geometry unreachable"),
    ):
        finding = ContaminationConfoundCheck().run(design, bundle)
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.NOT_CHECKED,
    )


def test_stale_vector_digest_is_value_free_not_checked():
    design, bundle = contamination_case(ratified=True)
    record = design.csp_contracts[0]
    axis = dict(record.fields["axis_identity"].value)
    axis["value_digest"] = "sha256:" + "0" * 64
    changed = replace(record.fields["axis_identity"], value=axis)
    stale = replace(record, fields={**record.fields, "axis_identity": changed})
    finding = ContaminationConfoundCheck().run(
        replace(design, csp_contracts=(stale,)), bundle
    )
    assert (finding.status, finding.coverage, finding.judgment, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.UNRESOLVED, S.NOT_CHECKED,
    )
    assert finding.conditional_on is None


@pytest.mark.parametrize("contained", [True, False])
def test_honest_ceiling_forbids_bias_or_remedy(contained):
    adjusted = ("condition", "rho_external") if contained else ("condition",)
    design, bundle = contamination_case(adjusted=adjusted, ratified=True)
    finding = ContaminationConfoundCheck().run(design, bundle)
    text = (finding.verdict + repr(finding.metrics)).lower()
    for forbidden in (
        "biased your result", "spurious", "caused the effect", "add rho", "rerun",
        "recover truth", "percent contamination", "bias magnitude",
    ):
        assert forbidden not in text
    assert finding.fix is None


@pytest.mark.parametrize("damage", [
    "missing_marker", "missing_measurement_identity", "missing_causal_identity",
    "measurement_scope_mismatch", "causal_scope_mismatch", "vague_premise",
])
def test_major_rejects_incomplete_dual_premise(damage):
    from sc_referee.checks.contamination_confound import _finding

    design, bundle = contamination_case(adjusted=("condition",), ratified=True)
    complete = ContaminationConfoundCheck().run(design, bundle)
    marker = complete.conditional_on
    metrics = dict(complete.metrics)
    if damage == "missing_marker":
        marker = None
    elif damage in {"missing_measurement_identity", "missing_causal_identity"}:
        identities = dict(marker.component_identities)
        identities.pop("measurement_contract_identity" if damage.startswith("missing_measurement")
                       else "causal_contract_identity")
        marker = replace(marker, component_identities=identities)
    elif damage in {"measurement_scope_mismatch", "causal_scope_mismatch"}:
        scope = dict(marker.scope)
        scope["fitted_design_identity" if damage.startswith("measurement")
              else "estimand_id"] += ":changed"
        marker = replace(marker, scope=scope)
    else:
        marker = replace(marker, plain_language_premise="Conditional on user input")
    with pytest.raises(ValueError, match="dual-premise conditional MAJOR"):
        _finding(
            S.MAJOR, complete.verdict, metrics, applicability=S.APPLIES,
            coverage=S.COMPLETE, judgment=S.VIOLATION, conditional_on=marker,
        )
