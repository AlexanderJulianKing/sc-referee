from __future__ import annotations

from dataclasses import replace

from sc_referee.csp import (
    CspContractRecord,
    CspFieldRecord,
    CspFieldState,
    CspReadRequest,
    CspScope,
    component_identities_for,
)
from sc_referee.csp_contracts.contamination_basis_obligation_v1 import (
    CONTRACT_TYPE,
    MANIFEST,
    REQUIRED_FIELDS,
)


def complete_contamination_values() -> dict[str, object]:
    """Complete synthetic values for a GB-P07-kind, analyst-supplied axis."""
    return {
        "measurement_kind": "external_measurement_artifact",
        "axis_identity": {
            "artifact_id": "artifact:gbp07-empty-drops:v1",
            "run_id": "run:gbp07:v1",
            "version": "1",
            "vector_field": "mean_contamination_fraction",
            "unit": "fraction",
            "scale": "zero_to_one",
            "orientation": "higher_is_more_ambient",
            "value_digest": "sha256:" + "1" * 64,
        },
        "rows_and_aggregation": {
            "input_row_ledger_identity": "rows:empty-droplets:v1",
            "output_row_ledger_identity": "rows:donors:v1",
            "source_mapping_identity": "mapping:droplets-to-donors:v1",
            "aggregation_ledger_identity": "aggregation:per-donor-mean:v1",
            "aggregation_rule": "per_unit_mean",
            "exclusions": (),
            "missing_rule": "abstain",
            "output_vector_digest": "sha256:" + "1" * 64,
        },
        "transform_kind": "continuous_identity",
        "transform_detail": {
            "source_vector_digest": "sha256:" + "1" * 64,
            "output_digest": "sha256:" + "2" * 64,
        },
        "basis_identity": {
            "basis_ledger_identity": "basis:gbp07-rho-bar:v1",
            "ordered_columns": ("rho_external",),
            "output_digest": "sha256:" + "2" * 64,
        },
        "positive_evidence": {
            "kind": "empty_droplet_derived_external_fraction",
            "records": ("evidence:empty-droplet-method:v1",),
        },
        "population_state_evidence": {
            "required": False,
            "records": (),
            "coverage_policy": "not_expression_proxy",
        },
        "source_stratum_applicability": {
            "source_strata": ("pool:gbp07",),
            "mapping_identity": "mapping:droplets-to-donors:v1",
            "comparability_evidence": ("evidence:pool-comparability:v1",),
            "cross_stratum_rule": "single_source_stratum",
        },
        "blindness_attestation": {
            "blind_to": (
                "exposure", "outcomes", "target_results", "coefficient",
                "measurement_exposure_association", "containment", "desired_verdict",
            ),
            "evidence_id": "evidence:blind-selection:v1",
        },
        "measurement_scope_authority": {
            "scope_id": "scope:gbp07-measurement:v1",
            "authority_id": "authority:analyst:v1",
            "assay": "single-cell-rna",
            "population_state": "declared-study-population",
            "source": "empty-droplet-pool",
            "analysis_id": "analysis:gbp07:v1",
        },
        "pre_exposure": {"confirmed": True, "evidence_id": "evidence:timing:v1"},
        "non_descendancy": {"confirmed": True, "evidence_id": "evidence:non-descendant:v1"},
        "outside_estimand_pathway": {
            "confirmed": True,
            "evidence_id": "evidence:outside-estimand:v1",
        },
        "required_adjustment": {
            "required": True,
            "basis": "prespecified_design_obligation",
            "evidence_id": "evidence:design-obligation:v1",
        },
        "assignment_context": {
            "kind": "observational",
            "assignment_identity": "assignment:gbp07:v1",
            "compatibility_evidence": "evidence:assignment-compatibility:v1",
        },
        "exact_basis_adequacy": {
            "required_basis_identity": "basis:gbp07-rho-bar:v1",
            "transform_kind": "continuous_identity",
            "evidence_id": "evidence:exact-basis:v1",
        },
        "causal_scope_authority": {
            "scope_id": "scope:gbp07-causal:v1",
            "authority_id": "authority:analyst:v1",
            "fitted_result_id": "fit:gbp07:v1",
            "target_coefficient": "condition[T.case]",
            "exposure_column": "condition[T.case]",
            "row_ledger_identity": "rows:donors:v1",
            "estimand_id": "estimand:gbp07:v1",
            "measurement_basis_identity": "basis:gbp07-rho-bar:v1",
            "fitted_design_identity": "design:gbp07:v1",
        },
    }


CONTAMINATION_SCOPE_KEYS = (
    "measurement_artifact_identity",
    "measurement_run_identity",
    "raw_source_ledger_identity",
    "measurement_vector_ledger_identity",
    "transformed_basis_ledger_identity",
    "basis_output_digest",
    "fitted_design_identity",
)


def contamination_scope() -> CspScope:
    values = complete_contamination_values()
    return CspScope(
        fitted_result_id="fit:gbp07:v1",
        contrast_name="case_vs_control",
        target_coefficient="condition[T.case]",
        exposure_column="condition[T.case]",
        row_ledger_identity="rows:donors:v1",
        estimand_id="estimand:gbp07:v1",
        group_source_column="donor",
        assignment_identity="assignment:gbp07:v1",
        contract_scope={
            "measurement_artifact_identity": values["axis_identity"]["artifact_id"],
            "measurement_run_identity": values["axis_identity"]["run_id"],
            "raw_source_ledger_identity": values["rows_and_aggregation"]["input_row_ledger_identity"],
            "measurement_vector_ledger_identity": values["rows_and_aggregation"]["output_row_ledger_identity"],
            "transformed_basis_ledger_identity": values["basis_identity"]["basis_ledger_identity"],
            "basis_output_digest": values["basis_identity"]["output_digest"],
            "fitted_design_identity": values["causal_scope_authority"]["fitted_design_identity"],
        },
    )


def ratified_contamination_record(*, scope=None, values=None, contract_id="csp:contamination:v1"):
    scope = scope or contamination_scope()
    values = values or complete_contamination_values()
    fields = {
        field_id: CspFieldRecord(
            field_id=field_id,
            value=values[field_id],
            state=CspFieldState.CONFIRMED_HIGH,
            confidence="high",
            scope_fingerprint=scope.fingerprint,
            evidence_ids=(f"evidence:{field_id}:v1",),
            evidence_basis="human_reviewed_exact_evidence",
            selected_teach_back_id=MANIFEST.teach_back_ids[field_id],
            consequence_acknowledged=True,
            confirmation_event_id=f"confirm:{field_id}:v1",
            actor="analyst",
            confirmed_at="2026-07-12T00:00:00Z",
            presentation_event_id=f"present:{field_id}:v1",
            answer_event_id=f"answer:{field_id}:v1",
        )
        for field_id in REQUIRED_FIELDS
    }
    record = CspContractRecord(
        contract_id=contract_id,
        contract_type=CONTRACT_TYPE,
        scope=scope,
        fields=fields,
        authorized_consumers=(MANIFEST.authorized_consumer,),
        authority_attested=True,
        authority_attestation=MANIFEST.authority_attestation,
        validator_version=MANIFEST.validator_version,
        validator_result=(),
        active=True,
        created_at="2026-07-12T00:00:00Z",
    )
    return replace(record, component_identities=component_identities_for(record, MANIFEST))


def contamination_read_request(scope=None):
    return CspReadRequest(
        CONTRACT_TYPE,
        scope or contamination_scope(),
        REQUIRED_FIELDS,
        MANIFEST.authorized_consumer,
    )


def with_field_answer(record, field, *, state, value):
    changed = replace(
        record.fields[field], state=CspFieldState(state), value=value,
        confidence="high" if state == "confirmed_high" else "low",
    )
    return replace(record, fields={**record.fields, field: changed})


def complete_contamination_answers() -> dict[str, object]:
    values = complete_contamination_values()
    answers: dict[str, object] = {
        "csp.contamination.authority_attested": "yes",
    }
    for field_id in REQUIRED_FIELDS:
        section = "measurement" if field_id in MANIFEST.component_field_groups[
            "measurement_contract_identity"
        ] else "causal"
        prefix = f"csp.contamination.{section}.{field_id}"
        answers[prefix] = "yes"
        answers[prefix + ".value"] = values[field_id]
        answers[prefix + ".evidence"] = f"evidence:{field_id}:v1"
        answers[prefix + ".teach_back"] = MANIFEST.teach_back_ids[field_id]
        answers[prefix + ".consequence"] = "yes"
    return answers


def contamination_case(
    *, adjusted=("condition",), ratified=True, operator_kind="ordinary_fixed_effects",
    rho_values=None, weight_role=None, offset_role=None,
):
    import numpy as np

    from sc_referee.column_space import NUMERIC_POLICY_V1, _canonical_matrix_digest
    from sc_referee.engine import build_pseudobulk_sample_rows
    from sc_referee.csp import assignment_identity
    from sc_referee.fitted_design import reconstruct_nuisance_design, request_from_confirmed_design
    from tests.factories import (
        fitted_design_declaration, make_design, pseudobulk_confounding_bundle,
    )

    bundle = pseudobulk_confounding_bundle()
    rho = np.asarray(
        rho_values if rho_values is not None else [.05, .13, .22, .31, .57, .68, .79, .91],
        dtype=np.float64,
    )
    bundle.observations["rho_external"] = rho
    kinds = {"condition": "categorical", "rho_external": "continuous"}
    declaration = fitted_design_declaration(
        operator_kind=operator_kind,
        column_kinds=kinds,
        categorical_levels={"condition": ("ctrl", "stim")},
        transforms={"condition": "identity", "rho_external": "identity"},
        weight_role=weight_role,
        offset_role=offset_role,
        batch_modeling={},
    )
    design = make_design(
        batch=(), sample_unit=("donor_id",), aggregation_key=("donor_id",),
        analyst_adjusted_for=list(adjusted), fitted_design=declaration,
        estimand_id="estimand:gbp07:v1", csp_contracts=(),
        confidence={
            "condition": "high", "analyst_adjusted_for": "high",
            "aggregation_key": "high", "fitted_design": "high",
        },
    )
    if not ratified:
        return design, bundle
    rows = build_pseudobulk_sample_rows(bundle.observations, design)
    live_assignment_identity = assignment_identity(
        rows.rows, "condition", "donor_id"
    )
    reconstruction = reconstruct_nuisance_design(
        rows.rows, design, request_from_confirmed_design(design, rows)
    )
    fitted_identity = (
        reconstruction.artifact.matrix_digest if reconstruction.artifact is not None
        else "sha256:" + "9" * 64
    )
    vector_digest = _canonical_matrix_digest(
        rho[:, None], policy_version=NUMERIC_POLICY_V1.version
    )
    values = complete_contamination_values()
    values["axis_identity"] = {
        **values["axis_identity"], "vector_field": "rho_external",
        "value_digest": vector_digest,
    }
    values["rows_and_aggregation"] = {
        **values["rows_and_aggregation"],
        "output_row_ledger_identity": rows.row_ledger_identity,
        "output_vector_digest": vector_digest,
    }
    values["transform_detail"] = {
        "source_vector_digest": vector_digest, "output_digest": vector_digest,
    }
    values["basis_identity"] = {
        **values["basis_identity"], "output_digest": vector_digest,
    }
    values["causal_scope_authority"] = {
        **values["causal_scope_authority"],
        "fitted_result_id": "fit:gbp07:v1",
        "target_coefficient": design.target_coefficient,
        "exposure_column": "condition",
        "row_ledger_identity": rows.row_ledger_identity,
        "estimand_id": design.estimand_id,
        "fitted_design_identity": fitted_identity,
    }
    values["assignment_context"] = {
        **values["assignment_context"],
        "assignment_identity": live_assignment_identity,
    }
    scope = CspScope(
        fitted_result_id="fit:gbp07:v1", contrast_name=design.name,
        target_coefficient=design.target_coefficient, exposure_column="condition",
        row_ledger_identity=rows.row_ledger_identity, estimand_id=design.estimand_id,
        group_source_column="donor_id", assignment_identity=live_assignment_identity,
        contract_scope={
            "measurement_artifact_identity": values["axis_identity"]["artifact_id"],
            "measurement_run_identity": values["axis_identity"]["run_id"],
            "raw_source_ledger_identity": values["rows_and_aggregation"]["input_row_ledger_identity"],
            "measurement_vector_ledger_identity": rows.row_ledger_identity,
            "transformed_basis_ledger_identity": values["basis_identity"]["basis_ledger_identity"],
            "basis_output_digest": vector_digest,
            "fitted_design_identity": fitted_identity,
        },
    )
    record = ratified_contamination_record(scope=scope, values=values)
    return replace(design, csp_contracts=(record,)), bundle


def eqtl_contamination_case(*, adjusted, ratified=True):
    import numpy as np
    import pandas as pd

    from sc_referee.bundle import Bundle, Measure
    from sc_referee.column_space import NUMERIC_POLICY_V1, _canonical_matrix_digest
    from sc_referee.csp import assignment_identity
    from sc_referee.engine import build_pseudobulk_sample_rows
    from sc_referee.fitted_design import reconstruct_nuisance_design, request_from_confirmed_design
    from tests.factories import fitted_design_declaration, make_design

    donors = [f"D{i:02d}" for i in range(1, 25)]
    genotype = np.repeat(np.asarray([0, 1, 2], dtype=np.int64), 8)
    rho = np.asarray([
        .05, .13, .22, .31, .57, .68, .79, .91,
        .08, .17, .26, .38, .49, .62, .74, .88,
        .03, .15, .29, .42, .53, .66, .81, .95,
    ], dtype=np.float64)
    observations = pd.DataFrame({
        "donor": donors,
        "genotype": genotype,
        "rho_external": rho,
    }, index=[f"cell-{donor}" for donor in donors])
    counts = np.asarray([[10 + i, 40 - i] for i in range(24)], dtype=np.int64)
    bundle = Bundle(
        observations=observations,
        measure=Measure("counts", counts, None, ["target", "control"]),
        feature_metadata=pd.DataFrame(index=["target", "control"]),
        replicate_var="donor",
    )
    declaration = fitted_design_declaration(
        column_kinds={"genotype": "continuous", "rho_external": "continuous"},
        categorical_levels={},
        transforms={"genotype": "identity", "rho_external": "identity"},
        batch_modeling={},
    )
    design = make_design(
        analysis_type="eqtl", condition=None, reference=None, test=None, batch=(),
        replicate_unit=("donor",), sample_unit=("donor",), pairing_unit=(),
        aggregation_key=("donor",), model="~ genotype",
        analyst_adjusted_for=list(adjusted), fitted_design=declaration,
        target_coefficient="genotype", genotype_column="genotype",
        variant_id="rsGB-P07", target_feature="target",
        estimand_id="estimand:gbp07-eqtl:v1", csp_contracts=(),
        confidence={
            "analyst_adjusted_for": "high", "aggregation_key": "high",
            "fitted_design": "high",
        },
    )
    if not ratified:
        return design, bundle

    rows = build_pseudobulk_sample_rows(bundle.observations, design)
    live_assignment_identity = assignment_identity(rows.rows, "genotype", "donor")
    reconstruction = reconstruct_nuisance_design(
        rows.rows, design, request_from_confirmed_design(design, rows)
    )
    fitted_identity = (
        reconstruction.artifact.matrix_digest if reconstruction.artifact is not None
        else "sha256:" + "9" * 64
    )
    vector_digest = _canonical_matrix_digest(
        rho[:, None], policy_version=NUMERIC_POLICY_V1.version
    )
    values = complete_contamination_values()
    values["axis_identity"] = {
        **values["axis_identity"], "vector_field": "rho_external",
        "value_digest": vector_digest,
    }
    values["rows_and_aggregation"] = {
        **values["rows_and_aggregation"],
        "output_row_ledger_identity": rows.row_ledger_identity,
        "output_vector_digest": vector_digest,
    }
    values["transform_detail"] = {
        "source_vector_digest": vector_digest, "output_digest": vector_digest,
    }
    values["basis_identity"] = {
        **values["basis_identity"], "output_digest": vector_digest,
    }
    values["causal_scope_authority"] = {
        **values["causal_scope_authority"],
        "fitted_result_id": "fit:gbp07-eqtl:v1",
        "target_coefficient": design.target_coefficient,
        "exposure_column": "genotype",
        "row_ledger_identity": rows.row_ledger_identity,
        "estimand_id": design.estimand_id,
        "fitted_design_identity": fitted_identity,
    }
    values["assignment_context"] = {
        **values["assignment_context"],
        "assignment_identity": live_assignment_identity,
    }
    scope = CspScope(
        fitted_result_id="fit:gbp07-eqtl:v1", contrast_name=design.name,
        target_coefficient=design.target_coefficient, exposure_column="genotype",
        row_ledger_identity=rows.row_ledger_identity, estimand_id=design.estimand_id,
        group_source_column="donor", assignment_identity=live_assignment_identity,
        contract_scope={
            "measurement_artifact_identity": values["axis_identity"]["artifact_id"],
            "measurement_run_identity": values["axis_identity"]["run_id"],
            "raw_source_ledger_identity": values["rows_and_aggregation"]["input_row_ledger_identity"],
            "measurement_vector_ledger_identity": rows.row_ledger_identity,
            "transformed_basis_ledger_identity": values["basis_identity"]["basis_ledger_identity"],
            "basis_output_digest": vector_digest,
            "fitted_design_identity": fitted_identity,
        },
    )
    record = ratified_contamination_record(
        scope=scope, values=values, contract_id="csp:contamination:eqtl:v1"
    )
    return replace(design, csp_contracts=(record,)), bundle


def gbp07_obligation_pair():
    """GB-P07-shaped mechanism fixture only; not the live GB-P07 anchor or artifact."""
    without, without_bundle = contamination_case(
        adjusted=("condition",), ratified=True
    )
    with_basis, with_bundle = contamination_case(
        adjusted=("condition", "rho_external"), ratified=True
    )
    without_record = replace(
        without.csp_contracts[0], contract_id="csp:test-only:gbp07-shaped:without-rho"
    )
    with_record = replace(
        with_basis.csp_contracts[0], contract_id="csp:test-only:gbp07-shaped:with-rho"
    )
    return (
        replace(without, csp_contracts=(without_record,)), without_bundle,
        replace(with_basis, csp_contracts=(with_record,)), with_bundle,
    )
