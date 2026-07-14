from datetime import datetime, timezone

from sc_referee.csp import CspContractRecord, CspFieldRecord, CspFieldState
from sc_referee.csp_contracts.between_group_adjustment_obligation_v1 import CONTRACT_TYPE
from sc_referee.csp_contracts.target_population_estimand_v1 import (
    AUTHORIZED_CONSUMER as TARGET_CONSUMER,
    CONTRACT_TYPE as TARGET_TYPE,
    MANIFEST as TARGET_MANIFEST,
    REQUIRED_FIELDS as TARGET_FIELDS,
)


TARGET_VALUES = {
    "functional": "population_average",
    "reported_scalar_id": "results.csv#IL7R:effect",
    "target_population_id": "registry:california:v4",
    "census_stratum_columns": ("registry.age_band", "registry.sex"),
    "evaluation_stratum_columns": ("donors.age_band", "donors.sex"),
    "stratum_levels": (("18-39", "F"), ("18-39", "M"), ("40-64", "F"), ("40-64", "M")),
    "stratum_ledger_identity": "strata:v1:age-sex:abc123",
    "census_artifact_identity": "artifact:registry-v4:sha256:abc123",
    "census_count_ledger_identity": "counts:v1:sha256:def456",
    "census_total_n": 1000,
    "census_stratum_counts": (300, 200, 325, 175),
    "weight_vector_identity": "weights:v1:sha256:fedcba",
    "weight_vector": ((300, 1000), (200, 1000), (325, 1000), (175, 1000)),
    "support_policy": "require_observed_evaluation_support",
}


def target_scope():
    return __import__("sc_referee.csp", fromlist=["CspScope"]).CspScope(
        fitted_result_id="fit:de:v7", contrast_name="stim-v-control",
        target_coefficient="condition[T.stim]", exposure_column="condition",
        row_ledger_identity="rows:v1:sha256:123",
        estimand_id="registry-standardized-effect/v1",
        group_source_column="__not_applicable__",
        assignment_identity="csp-assign:v1:" + "0" * 64,
        contract_scope={
            "reported_scalar_id": TARGET_VALUES["reported_scalar_id"],
            "target_population_id": TARGET_VALUES["target_population_id"],
            "census_artifact_identity": TARGET_VALUES["census_artifact_identity"],
            "census_count_ledger_identity": TARGET_VALUES["census_count_ledger_identity"],
            "stratum_ledger_identity": TARGET_VALUES["stratum_ledger_identity"],
            "weight_vector_identity": TARGET_VALUES["weight_vector_identity"],
        },
    )


def ratified_target_population_contract(*, scope=None, contract_id="csp-target-1"):
    scope = scope or target_scope()
    now = datetime(2026, 7, 12, tzinfo=timezone.utc).isoformat()
    fields = {
        field_id: CspFieldRecord(
            field_id=field_id, value=value, state=CspFieldState.CONFIRMED_HIGH,
            confidence="high", scope_fingerprint=scope.fingerprint,
            evidence_ids=("registry.yaml:1", "results.csv:IL7R"),
            evidence_basis="human_reviewed_target_population",
            selected_teach_back_id=TARGET_MANIFEST.teach_back_ids[field_id],
            consequence_acknowledged=True,
            confirmation_event_id=f"evt-confirm-{field_id}",
            actor="scientific_interpreter", confirmed_at=now,
            presentation_event_id=f"evt-present-{field_id}",
            answer_event_id=f"evt-answer-{field_id}",
        ) for field_id, value in TARGET_VALUES.items()
    }
    return CspContractRecord(
        contract_id=contract_id, contract_type=TARGET_TYPE, scope=scope, fields=fields,
        authorized_consumers=(TARGET_CONSUMER,), authority_attested=True,
        authority_attestation=TARGET_MANIFEST.authority_attestation,
        validator_version=TARGET_MANIFEST.validator_version, validator_result=(),
        active=True, created_at=now,
    )


def ratified_between_group_contract(*, scope, contract_id="csp-between-group-1"):
    now = datetime(2026, 7, 11, tzinfo=timezone.utc).isoformat()
    common = dict(
        state=CspFieldState.CONFIRMED_HIGH,
        confidence="high",
        scope_fingerprint=scope.fingerprint,
        evidence_ids=("analysis.R:42",),
        evidence_basis="human_reviewed_analysis",
        consequence_acknowledged=True,
        actor="scientific_interpreter",
        confirmed_at=now,
        presentation_event_id="evt-presented",
        answer_event_id="evt-answered",
    )
    fields = {
        "between_group_policy": CspFieldRecord(
            field_id="between_group_policy", value="remove_arbitrary",
            selected_teach_back_id="remove_arbitrary", confirmation_event_id="evt-policy",
            **common,
        ),
        "may_rely_on_re_exogeneity": CspFieldRecord(
            field_id="may_rely_on_re_exogeneity", value=False,
            selected_teach_back_id="must_not_rely", confirmation_event_id="evt-teachback",
            **common,
        ),
    }
    return CspContractRecord(
        contract_id=contract_id,
        contract_type=CONTRACT_TYPE,
        scope=scope,
        fields=fields,
        authorized_consumers=("confounding_random_intercept_conditional",),
        authority_attested=True,
        authority_attestation="I am responsible for this result's scientific interpretation",
        validator_version="between-group-obligation-v1",
        validator_result=(),
        active=True,
        created_at=now,
    )


def scope_from_design(design, bundle=None, *, batch="run", row_ledger_identity=None):
    from sc_referee.csp import assignment_identity
    from sc_referee.engine import build_pseudobulk_sample_rows
    from tests.factories import pseudobulk_confounding_bundle

    entry = design.fitted_design.batch_modeling[batch]
    exposure, _, _ = design.contrast_column_and_levels()
    source = bundle if bundle is not None else pseudobulk_confounding_bundle()
    rows = build_pseudobulk_sample_rows(source.observations, design)
    return __import__("sc_referee.csp", fromlist=["CspScope"]).CspScope(
        fitted_result_id=entry.component_scope.fitted_result_id,
        contrast_name=design.name,
        target_coefficient=design.target_coefficient,
        exposure_column=exposure,
        row_ledger_identity=row_ledger_identity or entry.row_ledger_identity,
        estimand_id=design.estimand_id,
        group_source_column=batch,
        assignment_identity=assignment_identity(rows.rows, exposure, batch),
    )


def bind_ratified_between_group_contract(design, bundle=None, *, batch="run"):
    from dataclasses import replace

    scope = scope_from_design(design, bundle, batch=batch)
    return replace(design, csp_contracts=(ratified_between_group_contract(scope=scope),))


def _record_yaml(record):
    scope = {
        "fitted_result_id": record.scope.fitted_result_id,
        "contrast_name": record.scope.contrast_name,
        "target_coefficient": record.scope.target_coefficient,
        "exposure_column": record.scope.exposure_column,
        "row_ledger_identity": record.scope.row_ledger_identity,
        "estimand_id": record.scope.estimand_id,
        "group_source_column": record.scope.group_source_column,
        "assignment_identity": record.scope.assignment_identity,
        "scope_fingerprint": record.scope.fingerprint,
    }
    if record.scope.contract_scope:
        scope["contract_scope"] = dict(record.scope.contract_scope)
    return {
        "contract_id": record.contract_id,
        "contract_type": record.contract_type,
        "scope": scope,
        "fields": {
            field_id: {
                "field_id": field.field_id,
                "value": field.value,
                "state": field.state.value,
                "confidence": field.confidence,
                "scope_fingerprint": field.scope_fingerprint,
                "evidence_ids": list(field.evidence_ids),
                "evidence_basis": field.evidence_basis,
                "selected_teach_back_id": field.selected_teach_back_id,
                "consequence_acknowledged": field.consequence_acknowledged,
                "confirmation_event_id": field.confirmation_event_id,
                "actor": field.actor,
                "confirmed_at": field.confirmed_at,
                "presentation_event_id": field.presentation_event_id,
                "answer_event_id": field.answer_event_id,
            } for field_id, field in record.fields.items()
        },
        "authorized_consumers": list(record.authorized_consumers),
        "authority_attested": record.authority_attested,
        "authority_attestation": record.authority_attestation,
        "validator_version": record.validator_version,
        "validator_result": list(record.validator_result),
        "active": record.active,
        "created_at": record.created_at,
    }


def ratified_contract_yaml(*, include_csp=True):
    from dataclasses import replace
    from tests.factories import pseudobulk_confounding_bundle, random_intercept_design

    bundle = pseudobulk_confounding_bundle()
    design = replace(random_intercept_design(bundle, adjusted=["condition"]),
                     estimand_id="condition-effect/v1")
    entry = design.fitted_design.batch_modeling["run"]
    fitted = design.fitted_design
    csp = ratified_between_group_contract(scope=scope_from_design(design))
    contrast = {
        "name": design.name, "reference": design.reference, "test": design.test,
        "replicate_unit": design.replicate_unit, "sample_unit": design.sample_unit,
        "pairing_unit": design.pairing_unit, "aggregation_key": design.aggregation_key,
        "model": design.model, "target_coefficient": design.target_coefficient,
        "analyst_adjusted_for": design.analyst_adjusted_for,
        "estimand_id": design.estimand_id,
        "fitted_design": {
            "rows_exact": fitted.rows_exact, "operator_kind": fitted.operator_kind,
            "intercept": fitted.intercept, "column_kinds": dict(fitted.column_kinds),
            "categorical_levels": {k: list(v) for k, v in fitted.categorical_levels.items()},
            "transforms": dict(fitted.transforms),
            "batch_modeling": {"run": {
                "source_column": entry.source_column, "modeled_as": entry.modeled_as,
                "random_group_column": entry.random_group_column,
                "fixed_source_columns": list(entry.fixed_source_columns),
                "rows_exact": entry.rows_exact, "row_ledger_identity": entry.row_ledger_identity,
                "component_scope": {
                    "contrast_name": entry.component_scope.contrast_name,
                    "target_coefficient": entry.component_scope.target_coefficient,
                    "fitted_result_id": entry.component_scope.fitted_result_id,
                },
                "unsupported_components": list(entry.unsupported_components),
                "field_confidence": dict(entry.field_confidence),
                "evidence_locations": {k: list(v) for k, v in entry.evidence_locations.items()},
            }},
        },
    }
    if include_csp:
        contrast["csp_contracts"] = [_record_yaml(csp)]
    return {
        "analysis_type": "condition_contrast_DE", "confirmed_by_human": True,
        "design": {"condition": "condition", "batch": ["run"],
                   "replicate_unit": ["donor_id"]},
        "confidence": dict(design.confidence), "contrasts": [contrast],
    }


def ratified_target_contract_yaml():
    raw = ratified_contract_yaml(include_csp=False)
    raw["contrasts"][0]["csp_contracts"] = [
        _record_yaml(ratified_target_population_contract())
    ]
    return raw
