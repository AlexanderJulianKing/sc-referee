from __future__ import annotations

import pytest

from sc_referee.csp_contracts.contamination_basis_obligation_v1 import CAUSAL_FIELDS
from sc_referee.wizard import answers_to_config, csp_questions, design_questions
from tests.contamination_factories import complete_contamination_answers
from tests.factories import pseudobulk_confounding_bundle
from tests.test_init_contamination_csp import contamination_proposal
from tests.test_wizard_random_intercept_ledger import _answers, _proposal


CAUSAL = {
    "pre_exposure", "non_descendancy", "outside_estimand_pathway",
    "required_adjustment", "assignment_context", "exact_basis_adequacy",
}


def _ceremony_proposal():
    proposal = contamination_proposal()
    proposal.update({
        "artifact_identity": "artifact:gbp07-empty-drops:v1",
        "source_mapping_fields": ["donor_id"],
        "fitted_result_id": "fit:gbp07:v1",
        "row_ledger_identity": "rows:donors:v1",
        "fitted_design_identity": "design:gbp07:v1",
        "estimand_id": "estimand:gbp07:v1",
        "target_coefficient": "condition[T.stim]",
    })
    return proposal


def test_causal_path_cannot_be_rubber_stamped():
    by_role = {q.role: q for q in csp_questions({}, proposal=_ceremony_proposal())}
    assert "csp.contamination.accept_all" not in by_role
    for field in CAUSAL:
        question = by_role[f"csp.contamination.causal.{field}"]
        assert question.default == "not_sure"
        assert question.options[0] == "not_sure"
        assert question.required
    assert all(q.default != "yes" for q in by_role.values() if ".causal." in q.role)


def test_teach_back_copy_states_all_six_boundaries():
    copy = " ".join(
        q.prompt + " " + q.why
        for q in csp_questions({}, proposal=_ceremony_proposal())
    ).lower()
    for phrase in (
        "enrichment does not prove non-expression", "continuous and thresholded",
        "association does not establish causal role", "mediator", "not_checked",
        "conditional major",
    ):
        assert phrase in copy


def ceremony_record(answer_overrides=None):
    bundle = pseudobulk_confounding_bundle()
    observations = bundle.observations.assign(rho_external=[.1, .2, .3, .4, .6, .7, .8, .9])
    proposed = _proposal()
    proposed["contrasts"][0]["estimand_id"] = "estimand:gbp07:v1"
    proposed["csp_proposals"] = [_ceremony_proposal()]
    answers = _answers() | complete_contamination_answers() | (answer_overrides or {})
    config = answers_to_config(answers, observations, proposed_config=proposed)
    return next(record for record in config["contrasts"][0]["csp_contracts"]
                if record["contract_type"] == "contamination_basis_obligation/v1")


@pytest.mark.parametrize("field", CAUSAL)
def test_each_causal_yes_requires_own_evidence_and_teach_back(field):
    record = ceremony_record({f"csp.contamination.causal.{field}.evidence": None})
    assert record["fields"][field]["state"] == "unresolved"
    assert record["fields"][field]["value"] is None
    assert record["component_identities"] == {}


@pytest.mark.parametrize("field", ["non_descendancy", "outside_estimand_pathway", "required_adjustment"])
def test_benign_causal_no_is_value_free_decline(field):
    record = ceremony_record({f"csp.contamination.causal.{field}": "no"})
    assert record["fields"][field]["state"] == "declined_for_consumer"
    assert record["fields"][field]["value"] is None
    assert record["component_identities"] == {}


def test_complete_ceremony_computes_both_identities_only_at_end():
    record = ceremony_record()
    assert all(field["state"] == "confirmed_high" for field in record["fields"].values())
    assert set(record["component_identities"]) == {
        "measurement_contract_identity", "causal_contract_identity"
    }


def test_complete_ceremony_uses_live_contrast_name_not_fitted_result_id():
    record = ceremony_record()
    assert record["scope"]["contrast_name"] == "stim_vs_ctrl"
    assert record["scope"]["contrast_name"] != record["scope"]["fitted_result_id"]


def test_complete_live_bound_ceremony_reaches_conditional_pass(tmp_path):
    import yaml

    from sc_referee import statuses as S
    from sc_referee.checks.contamination_confound import ContaminationConfoundCheck
    from sc_referee.column_space import NUMERIC_POLICY_V1, _canonical_matrix_digest
    from sc_referee.config import load_designs
    from sc_referee.csp import assignment_identity
    from sc_referee.engine import build_pseudobulk_sample_rows
    from sc_referee.fitted_design import reconstruct_nuisance_design, request_from_confirmed_design
    from tests.contamination_factories import complete_contamination_values

    bundle = pseudobulk_confounding_bundle()
    observations = bundle.observations.assign(
        rho_external=[.1, .2, .3, .4, .6, .7, .8, .9]
    )
    proposed = _proposal()
    proposed["contrasts"][0]["estimand_id"] = "estimand:gbp07:v1"
    proposed["csp_proposals"] = [_ceremony_proposal()]
    base_answers = _answers() | {
        "analyst_adjusted_for": ["condition", "rho_external"],
        "batch_modeling.run.modeled_as": "fixed",
        "batch_modeling.run.fixed_source_columns": ["run"],
    }
    base_proposed = _proposal()
    base_proposed["contrasts"][0]["estimand_id"] = "estimand:gbp07:v1"
    base_config = answers_to_config(base_answers, observations, proposed_config=base_proposed)
    base_path = tmp_path / "base.yaml"
    base_path.write_text(yaml.safe_dump(base_config))
    base_design = load_designs(base_path)[0]
    rows = build_pseudobulk_sample_rows(observations, base_design)
    reconstruction = reconstruct_nuisance_design(
        rows.rows, base_design, request_from_confirmed_design(base_design, rows)
    )
    assert reconstruction.artifact is not None
    rho = observations["rho_external"].to_numpy(dtype=float)[:, None]
    digest = _canonical_matrix_digest(rho, policy_version=NUMERIC_POLICY_V1.version)
    live_assignment = assignment_identity(rows.rows, "condition", "donor_id")

    values = complete_contamination_values()
    values["axis_identity"] = {
        **values["axis_identity"], "vector_field": "rho_external", "value_digest": digest,
    }
    values["rows_and_aggregation"] = {
        **values["rows_and_aggregation"],
        "output_row_ledger_identity": rows.row_ledger_identity,
        "output_vector_digest": digest,
    }
    values["transform_detail"] = {
        "source_vector_digest": digest, "output_digest": digest,
    }
    values["basis_identity"] = {**values["basis_identity"], "output_digest": digest}
    values["assignment_context"] = {
        **values["assignment_context"], "assignment_identity": live_assignment,
    }
    values["causal_scope_authority"] = {
        **values["causal_scope_authority"],
        "fitted_result_id": "fit:gbp07:v1",
        "target_coefficient": base_design.target_coefficient,
        "exposure_column": "condition",
        "row_ledger_identity": rows.row_ledger_identity,
        "estimand_id": base_design.estimand_id,
        "fitted_design_identity": reconstruction.artifact.matrix_digest,
    }
    ceremony_answers = dict(base_answers) | complete_contamination_answers()
    from sc_referee.csp_contracts.contamination_basis_obligation_v1 import (
        CAUSAL_FIELDS, MEASUREMENT_FIELDS,
    )
    for field_id in MEASUREMENT_FIELDS + CAUSAL_FIELDS:
        section = "measurement" if field_id in MEASUREMENT_FIELDS else "causal"
        ceremony_answers[f"csp.contamination.{section}.{field_id}.value"] = values[field_id]
    final_config = answers_to_config(
        ceremony_answers, observations, proposed_config=proposed
    )
    final_path = tmp_path / "final.yaml"
    final_path.write_text(yaml.safe_dump(final_config))
    final_design = load_designs(final_path)[0]
    final_record = next(record for record in final_design.csp_contracts
                        if record.contract_type == "contamination_basis_obligation/v1")
    assert final_record.validator_result == (), final_record.validator_result
    bundle.observations = observations
    finding = ContaminationConfoundCheck().run(final_design, bundle)
    assert (finding.status, S.human_state(finding)) == (S.PASS, S.CLEAR), finding.metrics
    assert finding.conditional_on.component_identities


def test_design_questions_dispatches_exact_contamination_contract():
    proposed = _proposal()
    proposed["csp_proposals"] = [_ceremony_proposal()]
    roles = {q.role for q in design_questions(
        proposed,
        pseudobulk_confounding_bundle().observations.assign(rho_external=.1).columns,
        analysis_types=("condition_contrast_DE",),
    )}
    assert "csp.contamination.causal.pre_exposure" in roles


def test_complete_contamination_record_round_trips_through_config(tmp_path):
    import yaml
    from sc_referee.config import load_designs

    bundle = pseudobulk_confounding_bundle()
    observations = bundle.observations.assign(rho_external=[.1, .2, .3, .4, .6, .7, .8, .9])
    proposed = _proposal()
    proposed["csp_proposals"] = [_ceremony_proposal()]
    config = answers_to_config(
        _answers() | complete_contamination_answers(), observations,
        proposed_config=proposed,
    )
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(config))
    records = load_designs(path)[0].csp_contracts
    contamination = next(record for record in records
                         if record.contract_type == "contamination_basis_obligation/v1")
    assert len(contamination.component_identities) == 2
