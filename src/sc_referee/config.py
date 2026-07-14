"""Load a confirmed sc-referee.yaml into one flat `Design` per contrast. (C2)

Top-level fields (batch/condition/confirmed_by_human/confidence) are shared; contrast
fields (reference/test/model/...) are per-contrast. `replicate_unit` in both `design:` and
a contrast -> the contrast wins (top-level is only the proposal's seed default).
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json

import jsonschema
import yaml

from sc_referee.design import (
    BatchComponentScope,
    BatchModelingDeclaration,
    Design,
    EffectRelevanceContract,
    FittedDesignDeclaration,
    MultiplicityContract,
    ReportInferenceContract,
    DesignError,
)
from sc_referee.csp import CspContractRecord, CspFieldRecord, CspFieldState, CspScope
from sc_referee.schema_validation import validate
from sc_referee.row_ledger import (
    AggregationOperation, CompleteCaseOperation, EvaluationRelation,
    QcThresholdOperation, RowLedgerDeclaration, SubsetOperation, TypedScalar,
    ZeroCountOperation,
)


def _as_list(v):
    if v is None:
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]


def _typed_scalar(raw):
    if isinstance(raw, dict):
        if set(raw) != {"tag", "value"}:
            raise DesignError("typed row-ledger scalar requires exactly tag and value")
        return TypedScalar(raw["tag"], raw["value"])
    return TypedScalar.from_value(raw)


def _row_ledger_declaration(raw):
    if raw is None:
        return None
    operations = []
    for item in raw["operations"]:
        kind = item["kind"]
        common = (item["operation_id"],)
        if kind == "declared_subset":
            operations.append(SubsetOperation(*common, item["column_id"],
                tuple(_typed_scalar(x) for x in item["allowed_values"]), item["confidence"]))
        elif kind == "declared_qc_threshold":
            operations.append(QcThresholdOperation(*common, item["column_id"], item["comparison"],
                _typed_scalar(item["threshold"]), item["missing_policy"], item["confidence"]))
        elif kind == "complete_case":
            operations.append(CompleteCaseOperation(*common, tuple(item["column_ids"]), item["confidence"]))
        elif kind == "aggregation":
            operations.append(AggregationOperation(*common, tuple(item["key_columns"]),
                item["order"], item["confidence"]))
        elif kind == "zero_count_row":
            operations.append(ZeroCountOperation(*common, item["policy"],
                item["count_layer_identity"], item["confidence"]))
        else:
            raise DesignError("unsupported row-ledger operation")
    return RowLedgerDeclaration(
        schema_version=raw["schema_version"],
        source_snapshot_identity=raw["source_snapshot_identity"],
        count_layer_identity=raw["count_layer_identity"],
        source_occurrence_id_columns=tuple(raw["source_occurrence_id_columns"]),
        fitted_source_occurrence_ids=tuple(tuple(_typed_scalar(x) for x in oid)
                                           for oid in raw["fitted_source_occurrence_ids"]),
        operations=tuple(operations),
        evaluation_relation=EvaluationRelation(raw["evaluation_relation"]),
        evaluation_relation_confidence=raw["evaluation_relation_confidence"],
        fitted_result_id=raw["fitted_result_id"],
        target_coefficient=raw["target_coefficient"],
        field_confidence=raw["field_confidence"],
    )


_VERDICT_CONFIG_KEYS = (
    "analysis_type", "design", "contrasts", "reported_results", "claims", "confidence",
    "unresolved", "batch_modeling", "csp_proposals",
)


def semantic_digest(raw: dict) -> str:
    """Canonical integrity identity for all config semantics consumed by audit decisions."""
    payload = {key: raw[key] for key in _VERDICT_CONFIG_KEYS if key in raw}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                         default=str).encode("utf-8")
    return f"config:v1:{hashlib.sha256(encoded).hexdigest()}"


def _validate_confirmation_digest(raw: dict, path) -> None:
    declared = raw.get("confirmation_digest")
    # Legacy confirmed configs remain loadable, but only the confirm flow can mint bound authority.
    # Once a digest exists, stripping/changing verdict semantics is a typed config refusal.
    if raw.get("confirmed_by_human") is True and declared is not None:
        actual = semantic_digest(raw)
        if declared != actual:
            raise DesignError(
                f"{path}: sc-referee.yaml changed after confirmation (semantic digest mismatch); "
                "re-run `sc-referee confirm` to ratify the new design")


def confirmed_reported_path(path) -> str | None:
    """Return the human-confirmed reported-claim path, if one is declared.

    This deliberately does not validate or otherwise interpret the design: ``ingest`` runs before
    ``load_designs`` in the shipped audit spine, and malformed YAML must continue to be diagnosed by
    the normal config-loading path. An unconfirmed proposal has no authority to select a claim.
    """
    try:
        raw = yaml.safe_load(Path(path).read_text())
    except (OSError, UnicodeError, yaml.YAMLError):
        return None
    if not isinstance(raw, dict) or raw.get("confirmed_by_human") is not True:
        return None
    _validate_confirmation_digest(raw, path)
    reported = raw.get("reported_results")
    if not isinstance(reported, dict):
        return None
    declared = reported.get("path")
    return declared if isinstance(declared, str) and declared.strip() else None


def confirmed_reported_claims(path) -> tuple[dict, ...]:
    """Return the explicit multi-claim manifest from a confirmed canonical config.

    The legacy singular ``reported_results`` declaration is intentionally not projected here:
    callers use :func:`confirmed_reported_path` for that byte-stable path.  As with the singular
    helper, this is only an ingest-order projection; full shape validation remains owned by
    ``load_designs`` and the JSON schema.
    """
    try:
        raw = yaml.safe_load(Path(path).read_text())
    except (OSError, UnicodeError, yaml.YAMLError):
        return ()
    if not isinstance(raw, dict) or raw.get("confirmed_by_human") is not True:
        return ()
    _validate_confirmation_digest(raw, path)
    claims = raw.get("claims")
    if not isinstance(claims, list):
        return ()
    return tuple(dict(claim) for claim in claims if isinstance(claim, dict))


def load_designs(path) -> list:
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as e:
        raise DesignError(f"{path}: sc-referee.yaml could not be read as UTF-8 YAML: {e}") from e
    try:
        validate(raw, "sc_referee.schema.json")
    except jsonschema.ValidationError as e:
        raise DesignError(f"{path}: sc-referee.yaml failed schema validation: {e.message}") from e
    _validate_confirmation_digest(raw, path)
    dsn = raw.get("design", {}) or {}
    condition = dsn.get("condition")
    batch = _as_list(dsn.get("batch"))
    top_replicate = _as_list(dsn.get("replicate_unit"))
    reported = raw.get("reported_results") or {}
    claims = raw.get("claims") or []
    first_claim = claims[0] if claims and isinstance(claims[0], dict) else {}
    unit_of_test = reported.get("unit_of_test", first_claim.get("unit_of_test"))

    designs = []
    for c in raw.get("contrasts", []):
        is_eqtl = raw["analysis_type"] == "eqtl"
        replicate_unit = _as_list(c.get("replicate_unit")) or top_replicate
        test = c.get("test")
        frequency_interval = c.get("effect_allele_frequency_interval")
        if frequency_interval is not None:
            frequency_interval = tuple(float(x) for x in frequency_interval)
            if frequency_interval[0] > frequency_interval[1]:
                raise DesignError(
                    f"{path}: effect_allele_frequency_interval lower bound exceeds upper bound")
        fitted_raw = c.get("fitted_design")
        row_ledger = _row_ledger_declaration(c.get("row_ledger"))
        effect_raw = c.get("effect_relevance_contract")
        effect_relevance_contract = (None if effect_raw is None else EffectRelevanceContract(
            claim_type=effect_raw["claim_type"],
            threshold=float(effect_raw["threshold"]),
            threshold_scale=effect_raw["threshold_scale"],
            reported_effect_scale=effect_raw["reported_effect_scale"],
        ))
        multiplicity_raw = c.get("multiplicity_contract")
        multiplicity_contract = (None if multiplicity_raw is None else MultiplicityContract(
            claim_type=multiplicity_raw["claim_type"],
            error_criterion=multiplicity_raw["error_criterion"],
            adjustment_method=multiplicity_raw["adjustment_method"],
            family_complete=multiplicity_raw["family_complete"],
        ))
        inference_raw = c.get("report_inference_contract")
        report_inference_contract = (None if inference_raw is None else ReportInferenceContract(
            producer_binding=inference_raw["producer_binding"],
            response_scale=inference_raw["response_scale"],
            method_family=inference_raw["method_family"],
            dependence_semantics=inference_raw["dependence_semantics"],
        ))
        fitted_design = None
        if fitted_raw is not None:
            batch_modeling = {}
            for source, entry in (fitted_raw.get("batch_modeling") or {}).items():
                scope = entry["component_scope"]
                batch_modeling[source] = BatchModelingDeclaration(
                    source_column=entry["source_column"],
                    modeled_as=entry["modeled_as"],
                    random_group_column=entry.get("random_group_column"),
                    fixed_source_columns=(None if entry.get("fixed_source_columns") is None
                                          else tuple(entry["fixed_source_columns"])),
                    rows_exact=entry["rows_exact"],
                    row_ledger_identity=entry.get("row_ledger_identity"),
                    component_scope=BatchComponentScope(
                        contrast_name=scope["contrast_name"],
                        target_coefficient=scope["target_coefficient"],
                        fitted_result_id=scope["fitted_result_id"],
                    ),
                    unsupported_components=tuple(entry["unsupported_components"]),
                    field_confidence=entry["field_confidence"],
                    evidence_locations={k: tuple(v) for k, v in
                                        entry.get("evidence_locations", {}).items()},
                )
            fitted_design = FittedDesignDeclaration(
                rows_exact=fitted_raw["rows_exact"],
                operator_kind=fitted_raw["operator_kind"],
                intercept=fitted_raw["intercept"],
                column_kinds=fitted_raw["column_kinds"],
                categorical_levels={k: tuple(v) for k, v in fitted_raw["categorical_levels"].items()},
                transforms=fitted_raw["transforms"],
                weight_role=fitted_raw.get("weight_role"),
                offset_role=fitted_raw.get("offset_role"),
                unsupported_reason=fitted_raw.get("unsupported_reason"),
                batch_modeling=batch_modeling,
            )
        csp_contracts = []
        for contract_raw in c.get("csp_contracts") or []:
            scope_raw = contract_raw["scope"]
            scope = CspScope(
                fitted_result_id=scope_raw["fitted_result_id"],
                contrast_name=scope_raw["contrast_name"],
                target_coefficient=scope_raw["target_coefficient"],
                exposure_column=scope_raw["exposure_column"],
                row_ledger_identity=scope_raw["row_ledger_identity"],
                estimand_id=scope_raw["estimand_id"],
                group_source_column=scope_raw["group_source_column"],
                assignment_identity=scope_raw["assignment_identity"],
                contract_scope=scope_raw.get("contract_scope") or {},
            )
            if scope_raw["scope_fingerprint"] != scope.fingerprint:
                raise DesignError(f"{path}: CSP scope fingerprint does not match exact scope")
            fields = {}
            for field_id, field_raw in contract_raw["fields"].items():
                fields[field_id] = CspFieldRecord(
                    field_id=field_raw["field_id"], value=field_raw.get("value"),
                    state=CspFieldState(field_raw["state"]),
                    confidence=field_raw["confidence"],
                    scope_fingerprint=field_raw["scope_fingerprint"],
                    evidence_ids=tuple(field_raw["evidence_ids"]),
                    evidence_basis=field_raw.get("evidence_basis"),
                    selected_teach_back_id=field_raw.get("selected_teach_back_id"),
                    consequence_acknowledged=field_raw["consequence_acknowledged"],
                    confirmation_event_id=field_raw.get("confirmation_event_id"),
                    actor=field_raw.get("actor"), confirmed_at=field_raw.get("confirmed_at"),
                    presentation_event_id=field_raw.get("presentation_event_id"),
                    answer_event_id=field_raw.get("answer_event_id"),
                )
            csp_contracts.append(CspContractRecord(
                contract_id=contract_raw["contract_id"],
                contract_type=contract_raw["contract_type"], scope=scope, fields=fields,
                authorized_consumers=tuple(contract_raw["authorized_consumers"]),
                authority_attested=contract_raw["authority_attested"],
                authority_attestation=contract_raw.get("authority_attestation"),
                validator_version=contract_raw["validator_version"],
                validator_result=tuple(contract_raw["validator_result"]),
                active=contract_raw["active"], created_at=contract_raw["created_at"],
                component_identities=contract_raw.get("component_identities") or {},
            ))
        designs.append(
            Design(
                analysis_type=raw["analysis_type"],
                confirmed_by_human=bool(raw.get("confirmed_by_human", False)),
                confidence=raw.get("confidence", {}) or {},
                condition=condition,
                batch=batch,
                replicate_unit=replicate_unit,
                reference=c.get("reference"),
                test=test,
                model=c.get("model") or (None if is_eqtl else f"~ {condition}"),
                target_coefficient=(c.get("target_coefficient")
                                    or (None if is_eqtl else f"{condition}[T.{test}]")),
                sample_unit=_as_list(c.get("sample_unit")) or replicate_unit,
                # An EXPLICIT `pairing_unit: []` means UNPAIRED and must survive. Absence is also
                # non-asserting: never manufacture a paired model from `replicate_unit`. The unpaired
                # pairing check still uses the replicate key to diagnose paired-capable data.
                pairing_unit=(_as_list(c["pairing_unit"]) if "pairing_unit" in c else []),
                subset=c.get("subset"),
                name=c.get("name", "contrast"),
                unit_of_test=unit_of_test,
                analyst_adjusted_for=c.get("analyst_adjusted_for"),
                fitted_design=fitted_design,
                row_ledger=row_ledger,
                estimand_id=c.get("estimand_id"),
                csp_contracts=tuple(csp_contracts),
                # the FINAL post-collapse sample key at the sink (human-ratified), distinct from
                # sample_unit; only present when the human confirms it — absence keeps the checks
                # diagnostic. See Design.aggregation_key for the "final key" semantics.
                aggregation_key=(_as_list(c["aggregation_key"]) if "aggregation_key" in c else None),
                pairing_estimand=c.get("pairing_estimand"),
                pairing_mechanics=c.get("pairing_mechanics"),
                effect_relevance_contract=effect_relevance_contract,
                multiplicity_contract=multiplicity_contract,
                report_inference_contract=report_inference_contract,
                variant_id=c.get("variant_id"),
                genotype_column=c.get("genotype_column"),
                target_feature=c.get("target_feature"),
                effect_allele=c.get("effect_allele"),
                dosage_counts_allele=c.get("dosage_counts_allele"),
                variant_alleles=(tuple(c["variant_alleles"]) if "variant_alleles" in c else None),
                dosage_ploidy=c.get("dosage_ploidy"),
                effect_allele_frequency_interval=frequency_interval,
                effect_allele_frequency_scope=c.get("effect_allele_frequency_scope"),
                eqtl_estimator=c.get("eqtl_estimator"),
                eqtl_outcome_scale=c.get("eqtl_outcome_scale"),
                hic_genome_assembly=c.get("hic_genome_assembly"),
                hic_resolution_bp=c.get("hic_resolution_bp"),
                hic_target_bin_i=c.get("hic_target_bin_i"),
                hic_target_bin_j=c.get("hic_target_bin_j"),
                hic_background_view_start=c.get("hic_background_view_start"),
                hic_background_view_end=c.get("hic_background_view_end"),
                hic_contact_scale=c.get("hic_contact_scale"),
                hic_expected_model=c.get("hic_expected_model"),
                hic_mask_policy=c.get("hic_mask_policy"),
                hic_zero_policy=c.get("hic_zero_policy"),
                hic_pseudocount=c.get("hic_pseudocount"),
                hic_target_statistic=c.get("hic_target_statistic"),
                hic_replicate_functional=c.get("hic_replicate_functional"),
                hic_report_delta_tolerance=c.get("hic_report_delta_tolerance"),
                hic_report_delta_tolerance_authority=c.get(
                    "hic_report_delta_tolerance_authority"
                ),
            )
        )
    return designs
