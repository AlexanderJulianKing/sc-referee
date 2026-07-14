"""Premise-gated exact containment of a ratified contamination nuisance basis."""
from __future__ import annotations

from dataclasses import asdict

import numpy as np

from sc_referee import statuses as S
from sc_referee.checks.base import ConditionalPremise, Finding
from sc_referee.column_space import (
    NUMERIC_POLICY_V1,
    CertificationState,
    _canonical_matrix_digest,
    certify_column_space,
)
from sc_referee.csp import (
    CspAbstention, CspReadRequest, RatifiedFactSet, assignment_identity,
    read_ratified_contract,
)
from sc_referee.csp_contracts.contamination_basis_obligation_v1 import (
    CONTRACT_TYPE,
    MANIFEST,
    PREMISE_TEMPLATE,
    REQUIRED_FIELDS,
)
from sc_referee.engine import build_pseudobulk_sample_rows
from sc_referee.fitted_design import reconstruct_nuisance_design, request_from_confirmed_design
from sc_referee.citations import CITATIONS


CHECK_ID = "contamination_confound"
_FITTED_RESULT_BINDING = (
    "matrix_digest_plus_ordered_row_ledger;live_result_id_unavailable"
)


def _finding(status, verdict, metrics, *, applicability, coverage, judgment=S.UNRESOLVED,
             conditional_on=None):
    if status == S.MAJOR:
        required_identities = {
            "measurement_contract_identity", "causal_contract_identity"
        }
        premise = "" if conditional_on is None else conditional_on.plain_language_premise.lower()
        valid = (
            conditional_on is not None
            and set(metrics.get("component_identities", ())) == required_identities
            and set(conditional_on.component_identities) == required_identities
            and dict(conditional_on.component_identities) == metrics["component_identities"]
            and dict(conditional_on.scope) == metrics.get("arithmetic_scope")
            and "valid measurement" in premise
            and "conditioning on that exact basis is required" in premise
        )
        if not valid:
            raise ValueError("dual-premise conditional MAJOR is incomplete or scope-mismatched")
    return Finding(
        CHECK_ID, status, verdict, metrics=metrics, citations=CITATIONS[CHECK_ID], fix=None,
        applicability=applicability, coverage=coverage, judgment=judgment,
        proof_grade=S.EXACT if coverage == S.COMPLETE else None,
        conditional_on=conditional_on,
    )


def _not_checked(status, reason, verdict, *, applicability=S.UNKNOWN, extra=None):
    return _finding(
        status, verdict, {"machine_reason": reason, **(extra or {})},
        applicability=applicability, coverage=S.NOT_RUN, judgment=S.UNRESOLVED,
    )


def _digest(matrix) -> str:
    return _canonical_matrix_digest(
        np.asarray(matrix, dtype=np.float64), policy_version=NUMERIC_POLICY_V1.version
    )


def _axis_on_fitted_rows(observations, fitted_rows, columns):
    """Bind already-supplied values to exact groups; never estimate, impute, or drop."""
    if any(column not in observations.columns for column in columns):
        raise ValueError("measurement_axis_column_missing")
    output = []
    for positions in fitted_rows.group_positions:
        group = observations.iloc[positions]
        row = []
        for column in columns:
            values = group[column].to_numpy()
            if len(values) == 0 or any(value != values[0] for value in values[1:]):
                raise ValueError("measurement_axis_not_constant_within_fitted_unit")
            row.append(values[0])
        output.append(row)
    array = np.asarray(output)
    if array.dtype.kind in "bOcUSV" or not np.issubdtype(array.dtype, np.number):
        raise ValueError("measurement_axis_not_numeric")
    array = np.asarray(array, dtype=np.float64)
    if not np.isfinite(array).all():
        raise ValueError("measurement_axis_nonfinite")
    return array


def _replay_h(observations, fitted_rows, values):
    axis = values["axis_identity"]
    rows_and_aggregation = values["rows_and_aggregation"]
    transform = values["transform_kind"]
    detail = values["transform_detail"]
    basis = values["basis_identity"]
    if transform == "frozen_external_basis":
        h = _axis_on_fitted_rows(observations, fitted_rows, tuple(basis["ordered_columns"]))
        source = h
    else:
        source = _axis_on_fitted_rows(observations, fitted_rows, (axis["vector_field"],))
        if transform == "continuous_identity":
            h = source.copy()
        elif transform == "binary_threshold":
            if detail["numeric_representation"] != "float64":
                raise ValueError("binary_numeric_representation_mismatch")
            h = (source > np.float64(detail["threshold"])).astype(np.float64)
        else:
            raise ValueError("unsupported_ratified_transform")
    if _digest(source) != axis["value_digest"]:
        raise ValueError("measurement_vector_digest_mismatch")
    if _digest(source) != rows_and_aggregation["output_vector_digest"]:
        raise ValueError("output_vector_digest_mismatch")
    if _digest(source) != detail["source_vector_digest"]:
        raise ValueError("transform_source_digest_mismatch")
    if _digest(h) != detail["output_digest"] or _digest(h) != basis["output_digest"]:
        raise ValueError("basis_output_digest_mismatch")
    if h.shape[1] != len(basis["ordered_columns"]):
        raise ValueError("basis_column_order_mismatch")
    return h, tuple(basis["ordered_columns"])


def _scope_matches(facts, design, fitted_rows, exposure, live_assignment_identity):
    scope = facts.scope
    values = facts.values
    axis = values["axis_identity"]
    rows = values["rows_and_aggregation"]
    basis = values["basis_identity"]
    causal = values["causal_scope_authority"]
    assignment = values["assignment_context"]
    extension = scope.contract_scope
    return (
        scope.contrast_name == design.name
        and scope.target_coefficient == design.target_coefficient
        and scope.exposure_column == exposure
        and scope.row_ledger_identity == fitted_rows.row_ledger_identity
        and scope.estimand_id == design.estimand_id
        # There is no separate live aggregation-artifact ID in Design. Bind the strongest
        # available declaration exactly: the ordered final aggregation key plus the ordered
        # fitted-row ledger. Multi-key aggregation cannot be represented by CspScope v2's single
        # group_source_column and therefore abstains rather than being narrowed.
        and tuple(design.aggregation_key or ()) == (scope.group_source_column,)
        and scope.assignment_identity == live_assignment_identity
        and assignment["assignment_identity"] == live_assignment_identity
        and rows["output_row_ledger_identity"] == fitted_rows.row_ledger_identity
        and extension["measurement_artifact_identity"] == axis["artifact_id"]
        and extension["measurement_run_identity"] == axis["run_id"]
        and extension["raw_source_ledger_identity"] == rows["input_row_ledger_identity"]
        and extension["measurement_vector_ledger_identity"]
            == rows["output_row_ledger_identity"]
        and extension["transformed_basis_ledger_identity"]
            == basis["basis_ledger_identity"]
        and extension["basis_output_digest"] == basis["output_digest"]
        and causal["fitted_result_id"] == scope.fitted_result_id
        and causal["target_coefficient"] == scope.target_coefficient
        and causal["exposure_column"] == scope.exposure_column
        and causal["row_ledger_identity"] == scope.row_ledger_identity
        and causal["estimand_id"] == scope.estimand_id
        and causal["measurement_basis_identity"] == basis["basis_ledger_identity"]
        and causal["fitted_design_identity"] == extension["fitted_design_identity"]
    )


def _scope_payload(facts):
    scope = facts.scope
    return {
        "fitted_result_id": scope.fitted_result_id,
        "contrast_name": scope.contrast_name,
        "target_coefficient": scope.target_coefficient,
        "exposure_column": scope.exposure_column,
        "row_ledger_identity": scope.row_ledger_identity,
        "estimand_id": scope.estimand_id,
        "measurement_vector_ledger_identity": scope.contract_scope[
            "measurement_vector_ledger_identity"
        ],
        "transformed_basis_ledger_identity": scope.contract_scope[
            "transformed_basis_ledger_identity"
        ],
        "fitted_design_identity": scope.contract_scope["fitted_design_identity"],
        "fitted_result_binding": _FITTED_RESULT_BINDING,
        "assignment_identity": scope.assignment_identity,
        "group_source_column": scope.group_source_column,
        "aggregation_binding": "exact_single_final_key_plus_ordered_row_ledger",
    }


def _marker(facts):
    return ConditionalPremise(
        contract_id=facts.contract_id,
        contract_type=facts.contract_type,
        decisive_fields={
            "measurement_contract_identity": facts.component_identities[
                "measurement_contract_identity"
            ],
            "causal_contract_identity": facts.component_identities["causal_contract_identity"],
        },
        plain_language_premise=PREMISE_TEMPLATE,
        scope=_scope_payload(facts),
        component_identities=facts.component_identities,
    )


class ContaminationConfoundCheck:
    id = CHECK_ID
    analysis_types = ("condition_contrast_DE", "eqtl")
    audit_dimensions = ("conditioning_set",)
    proof_basis = "exact ratified-basis column-space containment certificate"
    contract_fields = (
        "condition", "analyst_adjusted_for", "aggregation_key", "fitted_design",
        "estimand_id", "csp_contracts",
    )
    max_status = S.MAJOR

    def applies_to(self, design, bundle):
        return design.analysis_type in self.analysis_types and any(
            record.contract_type == CONTRACT_TYPE for record in design.csp_contracts
        )

    def cannot_evaluate(self, design, bundle):
        return None

    def run(self, design, bundle, reported=None):
        if design.analysis_type not in self.analysis_types:
            return _not_checked(
                S.NOT_AUDITED, "outside_declared_scope",
                "This check is outside the declared analysis scope.",
                applicability=S.NOT_APPLICABLE,
            )
        candidates = [record for record in design.csp_contracts
                      if record.contract_type == CONTRACT_TYPE]
        if not candidates:
            return _not_checked(
                S.NEEDS_EVIDENCE, "contamination_premise_absent",
                "The exact contamination measurement and causal premises were not ratified."
            )
        if len(candidates) != 1:
            return _not_checked(
                S.NEEDS_EVIDENCE, "ambiguous_contamination_contracts",
                "More than one contamination premise matched; no premise was consumed."
            )
        record = candidates[0]
        read = read_ratified_contract(
            design.csp_contracts,
            CspReadRequest(CONTRACT_TYPE, record.scope, REQUIRED_FIELDS, CHECK_ID),
        )
        if isinstance(read, CspAbstention):
            if read.kind == "benign_non_authorization":
                return _not_checked(
                    S.NOT_AUDITED, read.reason,
                    "The confirmed causal answer does not authorize this obligation check."
                )
            return _not_checked(
                S.NEEDS_EVIDENCE, read.reason,
                "The exact contamination measurement and causal premises remain unratified."
            )
        facts: RatifiedFactSet = read
        if design.subset is not None:
            return _not_checked(
                S.NOT_AUDITED, "subset_axis_mapping_unsupported",
                "The exact measurement-to-fitted-row mapping under a subset was unavailable.",
                applicability=S.APPLIES,
            )
        try:
            fitted_rows = build_pseudobulk_sample_rows(bundle.observations, design)
        except Exception:
            return _not_checked(
                S.NOT_AUDITED, "fitted_rows_unavailable",
                "The exact fitted rows could not be bound after premise ratification.",
                applicability=S.APPLIES,
            )
        exposure, _, _ = design.contrast_column_and_levels()
        try:
            live_assignment = assignment_identity(
                fitted_rows.rows, exposure, facts.scope.group_source_column
            )
        # assignment_identity normalizes scalar-conversion failures internally and raises only
        # ValueError/TypeError for a genuinely un-encodable or unavailable assignment; catch exactly
        # those so an unexpected internal defect surfaces loudly instead of being masked as not_checked.
        except (TypeError, ValueError):
            live_assignment = None
        if (not fitted_rows.exact or live_assignment is None
                or not _scope_matches(facts, design, fitted_rows, exposure, live_assignment)):
            return _not_checked(
                S.NEEDS_EVIDENCE, "ratified_scope_or_rows_mismatch",
                "A bound identity changed after ratification; a new ceremony is required."
            )
        reconstruction = reconstruct_nuisance_design(
            fitted_rows.rows, design, request_from_confirmed_design(design, fitted_rows)
        )
        if reconstruction.state is CertificationState.NOT_AUDITED:
            return _not_checked(
                S.NOT_AUDITED, reconstruction.machine_reason, reconstruction.reason,
                applicability=S.APPLIES,
            )
        artifact = reconstruction.artifact
        # Design currently exposes no independent live fitted-result ID. Do not pretend the
        # record's fitted_result_id is self-authenticating: the strongest live binding available
        # is the exact reconstructed nuisance-matrix digest plus its ordered fitted-row ledger.
        if artifact.matrix_digest != facts.scope.contract_scope["fitted_design_identity"]:
            return _not_checked(
                S.NEEDS_EVIDENCE, "fitted_design_identity_mismatch",
                "The fitted nuisance design identity changed after ratification."
            )
        try:
            h, h_mapping = _replay_h(bundle.observations, fitted_rows, facts.values)
        except (KeyError, TypeError, ValueError) as error:
            return _not_checked(
                S.NOT_AUDITED, str(error),
                "The exact ratified basis could not be replayed without substitution.",
                applicability=S.APPLIES,
            )
        try:
            certificate = certify_column_space(
                artifact.c, h,
                c_columns=artifact.c_column_ids,
                excluded_exposure_columns=artifact.excluded_exposure_columns,
                h_mapping=h_mapping,
                row_ledger_identity=artifact.row_ledger_identity,
                exact=True,
            )
        except (TypeError, ValueError):
            return _not_checked(
                S.NOT_AUDITED, "column_space_input_invalid",
                "The exact column-space certificate inputs were invalid.",
                applicability=S.APPLIES,
            )
        witness = None if certificate.witness is None else asdict(certificate.witness)
        metrics = {
            "machine_reason": certificate.machine_reason,
            "column_space_state": certificate.state.value,
            "certificate_reason": certificate.reason,
            "row_ledger_identity": artifact.row_ledger_identity,
            "target_coefficient": design.target_coefficient,
            "fitted_design_identity": artifact.matrix_digest,
            "fitted_result_binding": _FITTED_RESULT_BINDING,
            "group_source_column": facts.scope.group_source_column,
            "aggregation_key": list(design.aggregation_key or ()),
            "aggregation_binding": "exact_single_final_key_plus_ordered_row_ledger",
            "excluded_exposure_columns": list(artifact.excluded_exposure_columns),
            "component_identities": dict(facts.component_identities),
            "arithmetic_scope": _scope_payload(facts),
            "witness": witness,
        }
        if certificate.state is CertificationState.NOT_AUDITED:
            return _not_checked(
                S.NOT_AUDITED, certificate.machine_reason, certificate.reason,
                applicability=S.APPLIES, extra=metrics,
            )
        marker = _marker(facts)
        if certificate.state is CertificationState.CERTIFIED:
            return _finding(
                S.PASS,
                "You confirmed that the specified basis measures pre-exposure contamination and "
                "that this analysis should adjust for it. Referee verified that the fitted model "
                "includes that basis.",
                metrics, applicability=S.APPLIES, coverage=S.COMPLETE,
                judgment=S.CONFORMANT, conditional_on=marker,
            )
        return _finding(
            S.MAJOR,
            "You confirmed that the specified basis measures pre-exposure contamination and that "
            "this analysis should adjust for it. Referee verified that the fitted model does not "
            "include that basis.",
            metrics, applicability=S.APPLIES, coverage=S.COMPLETE,
            judgment=S.VIOLATION, conditional_on=marker,
        )
