from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest
from sc_referee.method_contracts import SCIENTIFIC_CONTRACT_DIMENSIONS
from sc_referee.version import SCHEMA_VERSION

POSTHOC_METHOD_LEDGER_PROFILE = "posthoc_method_ledger_v1"
POSTHOC_METHOD_LEDGER_VERSION = "1.0.0"

_VALUE_EQUALS_DIMENSIONS = SCIENTIFIC_CONTRACT_DIMENSIONS
_SET_RELATION_DIMENSIONS = (
    "adjustment_set",
    "control_set",
    "denominator_or_universe",
    "missingness_and_transport",
    "selection_process",
)
_STEP_PRECEDES_DIMENSIONS = (
    "adjustment_set",
    "measurement_model",
    "scale_and_orientation",
    "selection_process",
)

POSTHOC_METHOD_LEDGER_MANIFEST: dict[str, Any] = {
    "profile_id": POSTHOC_METHOD_LEDGER_PROFILE,
    "profile_version": POSTHOC_METHOD_LEDGER_VERSION,
    "scientific_contract_dimensions": list(SCIENTIFIC_CONTRACT_DIMENSIONS),
    "comparison_forms": {
        "value_equals": {
            "allowed_dimensions": list(_VALUE_EQUALS_DIMENSIONS),
            "required_operand": "canonical_scalar",
            "observed_operand": "canonical_scalar",
        },
        "set_relation": {
            "allowed_dimensions": list(_SET_RELATION_DIMENSIONS),
            "required_operand": "unique_string_array",
            "observed_operand": "unique_string_array",
            "relation": "all_required_present_and_no_forbidden_present",
        },
        "step_precedes": {
            "allowed_dimensions": list(_STEP_PRECEDES_DIMENSIONS),
            "required_operand": "two_unique_step_names",
            "observed_operand": "unique_ordered_step_names",
        },
    },
    "requirement_authority": {
        "assertion_predicate": "verified_intended_<dimension>",
        "assertion_class": "deterministic_derivation",
        "authority_scope": "scientific_intent",
        "source": "scope_bound_human_answer_verified_by_controller",
        "historical_intent_established": False,
        "execution_established": False,
    },
    "observed_authority": {
        "assertion_predicate": "reported_<dimension>",
        "assertion_class": "explicit_text_extraction",
        "authority_scope": "reported_wording",
        "execution_established": False,
    },
    "outcomes": [
        "covered_negative",
        "exact_conflict_candidate",
        "unresolved_obligation",
        "unsupported_path",
        "not_applicable",
    ],
    "project_code_execution": False,
    "production_finding_permitted": False,
}


class PosthocMethodLedgerError(ValueError):
    """Raised when a post-hoc obligation escapes the closed ledger profile."""


def posthoc_form_allowed(dimension: str, comparison_form: str) -> bool:
    """Return whether the closed manifest binds this form to this dimension."""

    try:
        _validate_form_binding(dimension, comparison_form)
    except PosthocMethodLedgerError:
        return False
    return True


def validate_posthoc_requirement(dimension: str, comparison_form: str, value: object) -> object:
    """Validate one scientist-specified operand without interpreting free text."""

    _validate_form_binding(dimension, comparison_form)
    if comparison_form == "value_equals":
        return _canonical_scalar(value, "required value")
    if comparison_form == "set_relation":
        return _unique_string_array(value, "required members", allow_empty=True)
    if comparison_form == "step_precedes":
        steps = _unique_string_array(
            value,
            "required step pair",
            allow_empty=False,
            preserve_order=True,
        )
        if len(steps) != 2:
            raise PosthocMethodLedgerError("step_precedes requires exactly two named steps")
        return steps
    raise PosthocMethodLedgerError("unsupported post-hoc comparison form")


def project_posthoc_method_ledger(
    *,
    claim: Mapping[str, object],
    contract: Mapping[str, object],
    assertions: Sequence[Mapping[str, object]],
    dimension: str,
    comparison_form: str,
    forbidden_members: Sequence[str] = (),
) -> dict[str, Any]:
    """Project one review-scoped obligation and compare it without model judgment."""

    _validate_form_binding(dimension, comparison_form)
    claim_id = _required_string(claim.get("claim_id"), "claim_id")
    contract_id = _required_string(contract.get("contract_id"), "contract_id")
    if claim.get("scientific_contract_id") != contract_id:
        raise PosthocMethodLedgerError("Claim and ScientificContract identities do not match")
    _validate_claim_scope(contract, claim_id)
    dimensions = contract.get("dimensions")
    if not isinstance(dimensions, Mapping) or dimension not in dimensions:
        raise PosthocMethodLedgerError("ScientificContract dimension is unavailable")
    slot = dimensions[dimension]
    if not isinstance(slot, Mapping):
        raise PosthocMethodLedgerError("ScientificContract dimension slot is malformed")

    base: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "projection_profile": POSTHOC_METHOD_LEDGER_PROFILE,
        "profile_version": POSTHOC_METHOD_LEDGER_VERSION,
        "profile_manifest_digest": semantic_digest(POSTHOC_METHOD_LEDGER_MANIFEST),
        "claim_id": claim_id,
        "contract_id": contract_id,
        "dimension": dimension,
        "comparison_form": comparison_form,
        "authority": {
            "requirement": "review_scoped_scientist_answer",
            "observed": "verified_reported_wording",
            "historical_intent_established": False,
            "execution_established": False,
        },
    }
    state = slot.get("state")
    if state == "not_applicable":
        return _terminal(
            base,
            outcome="not_applicable",
            basis="The exact ScientificContract dimension is explicitly not applicable.",
            requirement=None,
            observed=None,
            comparison=None,
            source_refs=_slot_sources(slot),
            assertion_refs=[],
        )
    if state == "unknown":
        return _terminal(
            base,
            outcome="unresolved_obligation",
            basis="No scope-bound governing requirement was supplied for this review.",
            requirement=None,
            observed=None,
            comparison=None,
            source_refs=_slot_sources(slot),
            assertion_refs=[],
        )
    if state != "known":
        raise PosthocMethodLedgerError("ScientificContract dimension has an unsupported state")

    by_id = {
        str(item.get("assertion_id")): item
        for item in assertions
        if isinstance(item.get("assertion_id"), str)
    }
    accepted_ids = slot.get("accepted_assertion_ids")
    if not isinstance(accepted_ids, Sequence) or isinstance(accepted_ids, (str, bytes)):
        raise PosthocMethodLedgerError("known dimension has no accepted assertion identities")
    requirement_candidates = [
        by_id[str(assertion_id)]
        for assertion_id in accepted_ids
        if str(assertion_id) in by_id
        and by_id[str(assertion_id)].get("predicate") == f"verified_intended_{dimension}"
    ]
    if len(requirement_candidates) != 1:
        return _terminal(
            base,
            outcome="unresolved_obligation",
            basis="The known dimension does not resolve to one controller-verified requirement.",
            requirement=None,
            observed=None,
            comparison=None,
            source_refs=_slot_sources(slot),
            assertion_refs=[],
        )
    requirement_assertion = requirement_candidates[0]
    _verify_requirement_assertion(requirement_assertion, claim_id, dimension)

    observed_candidates = [
        item
        for item in assertions
        if item.get("predicate") == f"reported_{dimension}"
        and item.get("epistemic_status") == "accepted"
        and _ref_equals(item.get("subject_ref"), "claim", claim_id)
    ]
    if len(observed_candidates) != 1:
        outcome = "unsupported_path" if not observed_candidates else "unresolved_obligation"
        basis = (
            "No exact supported reported value was verified for this dimension."
            if not observed_candidates
            else "More than one accepted reported value conflicts within this dimension."
        )
        return _terminal(
            base,
            outcome=outcome,
            basis=basis,
            requirement=deepcopy(requirement_assertion.get("object")),
            observed=None,
            comparison=None,
            source_refs=_assertion_sources(requirement_assertion),
            assertion_refs=[_assertion_ref(requirement_assertion)],
        )
    observed_assertion = observed_candidates[0]
    _verify_observed_assertion(observed_assertion, claim_id, dimension)

    requirement = deepcopy(requirement_assertion.get("object"))
    observed = deepcopy(observed_assertion.get("object"))
    comparison = _compare(
        comparison_form,
        requirement,
        observed,
        forbidden_members=forbidden_members,
    )
    outcome = str(comparison["outcome"])
    sources = _deduplicate_sources(
        [
            *_assertion_sources(requirement_assertion),
            *_assertion_sources(observed_assertion),
        ]
    )
    return _terminal(
        base,
        outcome=outcome,
        basis=str(comparison["basis"]),
        requirement=requirement,
        observed=observed,
        comparison=comparison["details"],
        source_refs=sources,
        assertion_refs=[
            _assertion_ref(requirement_assertion),
            _assertion_ref(observed_assertion),
        ],
    )


def project_analysis_posthoc_method_ledger(
    *,
    analysis_subject_ref: Mapping[str, object],
    contract: Mapping[str, object],
    assertions: Sequence[Mapping[str, object]],
    observed_assertion_ids: Sequence[str],
    dimension: str,
    comparison_form: str,
    scope_join_path: Sequence[Mapping[str, object]],
    scope_join_digest: str,
    forbidden_members: Sequence[str] = (),
) -> dict[str, Any]:
    """Compare one analysis-scoped scientist requirement with exact static/report evidence."""

    _validate_form_binding(dimension, comparison_form)
    subject = _analysis_subject(analysis_subject_ref)
    contract_id = _required_string(contract.get("contract_id"), "contract_id")
    _validate_analysis_scope(contract, subject)
    if semantic_digest(list(scope_join_path)) != scope_join_digest:
        raise PosthocMethodLedgerError("analysis scope-join digest mismatch")
    if not scope_join_path:
        raise PosthocMethodLedgerError("analysis scope-join path is unavailable")
    last_edge = scope_join_path[-1]
    if (
        not isinstance(last_edge, Mapping)
        or last_edge.get("target_ref") != subject
        or not all(
            isinstance(edge, Mapping)
            and _record_ref(edge.get("source_ref"))
            and isinstance(edge.get("relation"), str)
            and bool(edge.get("relation"))
            and _record_ref(edge.get("target_ref"))
            for edge in scope_join_path
        )
    ):
        raise PosthocMethodLedgerError("analysis scope-join path does not end at its subject")
    dimensions = contract.get("dimensions")
    if not isinstance(dimensions, Mapping) or dimension not in dimensions:
        raise PosthocMethodLedgerError("ScientificContract dimension is unavailable")
    slot = dimensions[dimension]
    if not isinstance(slot, Mapping):
        raise PosthocMethodLedgerError("ScientificContract dimension slot is malformed")

    base: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "projection_profile": POSTHOC_METHOD_LEDGER_PROFILE,
        "profile_version": POSTHOC_METHOD_LEDGER_VERSION,
        "profile_manifest_digest": semantic_digest(POSTHOC_METHOD_LEDGER_MANIFEST),
        "analysis_subject_ref": deepcopy(dict(subject)),
        "contract_id": contract_id,
        "dimension": dimension,
        "comparison_form": comparison_form,
        "scope_join_path": [deepcopy(dict(edge)) for edge in scope_join_path],
        "scope_join_digest": scope_join_digest,
        "authority": {
            "requirement": "review_scoped_scientist_answer",
            "observed": "unresolved_until_assertion_validation",
            "historical_intent_established": False,
            "execution_established": False,
        },
    }
    state = slot.get("state")
    if state == "not_applicable":
        return _terminal(
            base,
            outcome="not_applicable",
            basis="The exact analysis-scoped contract dimension is explicitly not applicable.",
            requirement=None,
            observed=None,
            comparison=None,
            source_refs=_slot_sources(slot),
            assertion_refs=[],
        )
    if state == "unknown":
        return _terminal(
            base,
            outcome="unresolved_obligation",
            basis="No analysis-scoped governing requirement was supplied for this review.",
            requirement=None,
            observed=None,
            comparison=None,
            source_refs=_slot_sources(slot),
            assertion_refs=[],
        )
    if state != "known":
        raise PosthocMethodLedgerError("ScientificContract dimension has an unsupported state")

    by_id = {
        str(item.get("assertion_id")): item
        for item in assertions
        if isinstance(item.get("assertion_id"), str)
    }
    accepted_ids = slot.get("accepted_assertion_ids")
    if not isinstance(accepted_ids, Sequence) or isinstance(accepted_ids, (str, bytes)):
        raise PosthocMethodLedgerError("known dimension has no accepted assertion identities")
    requirements = [
        by_id[str(assertion_id)]
        for assertion_id in accepted_ids
        if str(assertion_id) in by_id
        and by_id[str(assertion_id)].get("predicate") == f"verified_intended_{dimension}"
    ]
    if len(requirements) != 1:
        return _terminal(
            base,
            outcome="unresolved_obligation",
            basis="The analysis contract does not resolve to one verified review requirement.",
            requirement=None,
            observed=None,
            comparison=None,
            source_refs=_slot_sources(slot),
            assertion_refs=[],
        )
    requirement_assertion = requirements[0]
    _verify_analysis_requirement_assertion(requirement_assertion, subject, dimension)

    selected_ids = [str(value) for value in observed_assertion_ids]
    if not selected_ids or len(selected_ids) != len(set(selected_ids)):
        raise PosthocMethodLedgerError("observed assertion identities must be non-empty and unique")
    observed_candidates = [by_id[value] for value in selected_ids if value in by_id]
    if len(observed_candidates) != len(selected_ids):
        return _terminal(
            base,
            outcome="unsupported_path",
            basis="A bound observed assertion is unavailable.",
            requirement=deepcopy(requirement_assertion.get("object")),
            observed=None,
            comparison=None,
            source_refs=_assertion_sources(requirement_assertion),
            assertion_refs=[_assertion_ref(requirement_assertion)],
        )
    verified_planes = [
        _verify_analysis_observed_assertion(item, dimension, scope_join_digest)
        for item in observed_candidates
    ]
    observed_values = {canonical_json(item.get("object")) for item in observed_candidates}
    if len(observed_values) != 1:
        return _terminal(
            base,
            outcome="unresolved_obligation",
            basis="Bound report and static-source operands disagree for this analysis scope.",
            requirement=deepcopy(requirement_assertion.get("object")),
            observed=None,
            comparison=None,
            source_refs=_deduplicate_sources(
                [
                    *_assertion_sources(requirement_assertion),
                    *(
                        source
                        for assertion in observed_candidates
                        for source in _assertion_sources(assertion)
                    ),
                ]
            ),
            assertion_refs=[
                _assertion_ref(requirement_assertion),
                *(_assertion_ref(item) for item in observed_candidates),
            ],
        )

    requirement = deepcopy(requirement_assertion.get("object"))
    observed = deepcopy(observed_candidates[0].get("object"))
    comparison = _compare(
        comparison_form,
        requirement,
        observed,
        forbidden_members=forbidden_members,
    )
    outcome = str(comparison["outcome"])
    planes = sorted(set(verified_planes))
    base["authority"]["observed"] = (
        "verified_static_source"
        if planes == ["static_source"]
        else "verified_reported_wording"
        if planes == ["reported_text"]
        else "corroborated_report_and_static_source"
    )
    basis = str(comparison["basis"])
    if "static_source" in planes:
        if outcome == "covered_negative":
            basis = (
                "The exact statically inspected operand is compatible with the "
                "scientist-specified requirement governing this review."
            )
        elif outcome == "exact_conflict_candidate":
            basis = (
                "The exact statically inspected operand is incompatible with the "
                "scientist-specified requirement governing this review."
            )
    sources = _deduplicate_sources(
        [
            *_assertion_sources(requirement_assertion),
            *(
                source
                for assertion in observed_candidates
                for source in _assertion_sources(assertion)
            ),
        ]
    )
    return _terminal(
        base,
        outcome=outcome,
        basis=basis,
        requirement=requirement,
        observed=observed,
        comparison=comparison["details"],
        source_refs=sources,
        assertion_refs=[
            _assertion_ref(requirement_assertion),
            *(_assertion_ref(item) for item in observed_candidates),
        ],
    )


def _compare(
    comparison_form: str,
    requirement: object,
    observed: object,
    *,
    forbidden_members: Sequence[str],
) -> dict[str, Any]:
    if comparison_form == "value_equals":
        required_value = _canonical_scalar(requirement, "required value")
        observed_value = _canonical_scalar(observed, "observed value")
        equal = canonical_json(required_value) == canonical_json(observed_value)
        return {
            "outcome": "covered_negative" if equal else "exact_conflict_candidate",
            "basis": (
                "The exact reported value matches the scientist-specified review requirement."
                if equal
                else "The exact reported value conflicts with the scientist-specified review requirement."
            ),
            "details": {"values_equal": equal},
        }
    if comparison_form == "set_relation":
        required = _unique_string_array(requirement, "required members", allow_empty=True)
        observed_members = _unique_string_array(observed, "observed members", allow_empty=True)
        forbidden = _unique_string_array(
            list(forbidden_members), "forbidden members", allow_empty=True
        )
        overlap = sorted(set(required) & set(forbidden))
        if overlap:
            raise PosthocMethodLedgerError(
                f"set obligation requires and forbids the same members: {overlap}"
            )
        missing = sorted(set(required) - set(observed_members))
        present_forbidden = sorted(set(forbidden) & set(observed_members))
        compatible = not missing and not present_forbidden
        return {
            "outcome": "covered_negative" if compatible else "exact_conflict_candidate",
            "basis": (
                "Every required member is reported and no forbidden member is reported."
                if compatible
                else "The reported set is missing a required member or contains a forbidden member."
            ),
            "details": {
                "required_members": required,
                "forbidden_members": forbidden,
                "observed_members": observed_members,
                "missing_required_members": missing,
                "present_forbidden_members": present_forbidden,
            },
        }
    if comparison_form == "step_precedes":
        required_steps = _unique_string_array(
            requirement,
            "required step pair",
            allow_empty=False,
            preserve_order=True,
        )
        if len(required_steps) != 2:
            raise PosthocMethodLedgerError("step_precedes requires exactly two named steps")
        observed_steps = _unique_string_array(
            observed, "observed ordered steps", allow_empty=False, preserve_order=True
        )
        earlier, later = required_steps
        missing = [step for step in required_steps if step not in observed_steps]
        if missing:
            return {
                "outcome": "unsupported_path",
                "basis": "The exact reported step sequence does not verify both required steps.",
                "details": {
                    "earlier_step": earlier,
                    "later_step": later,
                    "observed_steps": observed_steps,
                    "missing_steps": missing,
                },
            }
        earlier_index = observed_steps.index(earlier)
        later_index = observed_steps.index(later)
        precedes = earlier_index < later_index
        return {
            "outcome": "covered_negative" if precedes else "exact_conflict_candidate",
            "basis": (
                "The exact reported step sequence has the required order."
                if precedes
                else "The exact reported step sequence reverses the required order."
            ),
            "details": {
                "earlier_step": earlier,
                "later_step": later,
                "observed_steps": observed_steps,
                "earlier_index": earlier_index,
                "later_index": later_index,
                "required_order_satisfied": precedes,
            },
        }
    raise PosthocMethodLedgerError("unsupported post-hoc comparison form")


def _terminal(
    base: Mapping[str, Any],
    *,
    outcome: str,
    basis: str,
    requirement: object,
    observed: object,
    comparison: object,
    source_refs: Sequence[Mapping[str, Any]],
    assertion_refs: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    result = deepcopy(dict(base))
    result.update(
        {
            "outcome": outcome,
            "basis": basis,
            "requirement": deepcopy(requirement),
            "observed": deepcopy(observed),
            "comparison": deepcopy(comparison),
            "source_refs": [deepcopy(dict(ref)) for ref in source_refs],
            "assertion_refs": [deepcopy(dict(ref)) for ref in assertion_refs],
            "production_finding_permitted": False,
        }
    )
    result["ledger_digest"] = semantic_digest(result)
    return result


def _validate_form_binding(dimension: str, comparison_form: str) -> None:
    forms = POSTHOC_METHOD_LEDGER_MANIFEST["comparison_forms"]
    if dimension not in SCIENTIFIC_CONTRACT_DIMENSIONS:
        raise PosthocMethodLedgerError("unsupported ScientificContract dimension")
    if comparison_form not in forms:
        raise PosthocMethodLedgerError("unsupported post-hoc comparison form")
    allowed = forms[comparison_form]["allowed_dimensions"]
    if dimension not in allowed:
        raise PosthocMethodLedgerError(
            f"{comparison_form} is not bound to ScientificContract dimension {dimension}"
        )


def _validate_claim_scope(contract: Mapping[str, object], claim_id: str) -> None:
    scope = contract.get("scope")
    if (
        not isinstance(scope, Mapping)
        or scope.get("level") != "claim"
        or scope.get("subject_refs") != [{"record_type": "claim", "record_id": claim_id}]
    ):
        raise PosthocMethodLedgerError("ScientificContract has the wrong Claim scope")


def _analysis_subject(value: Mapping[str, object]) -> dict[str, str]:
    if not _ref_type(value, "publication_surface"):
        raise PosthocMethodLedgerError("analysis subject must name one selected PublicationSurface")
    return {
        "record_type": "publication_surface",
        "record_id": _required_string(value.get("record_id"), "analysis subject record_id"),
    }


def _validate_analysis_scope(
    contract: Mapping[str, object], analysis_subject_ref: Mapping[str, str]
) -> None:
    scope = contract.get("scope")
    if (
        not isinstance(scope, Mapping)
        or scope.get("level") != "analysis"
        or scope.get("subject_refs") != [dict(analysis_subject_ref)]
    ):
        raise PosthocMethodLedgerError("ScientificContract has the wrong analysis scope")


def _verify_requirement_assertion(
    assertion: Mapping[str, object], claim_id: str, dimension: str
) -> None:
    verification = assertion.get("verification")
    extensions = assertion.get("extensions")
    if (
        not _ref_equals(assertion.get("subject_ref"), "claim", claim_id)
        or assertion.get("predicate") != f"verified_intended_{dimension}"
        or assertion.get("semantic_role") != "intended"
        or assertion.get("assertion_class") != "deterministic_derivation"
        or assertion.get("epistemic_status") != "accepted"
        or assertion.get("authority_scope") != "scientific_intent"
        or assertion.get("independently_checkable") is not True
        or assertion.get("finding_eligibility") != "eligible"
        or _actor_kind(assertion) != "controller"
        or not isinstance(verification, Mapping)
        or verification.get("status") != "verified"
        or verification.get("method") != "deterministic_comparison"
        or not isinstance(extensions, Mapping)
        or not _ref_type(extensions.get("x-answer-ref"), "answer")
        or not isinstance(extensions.get("x-answer-digest"), str)
    ):
        raise PosthocMethodLedgerError(
            "review requirement is not a controller-verified scope-bound scientist Answer"
        )
    _assertion_sources(assertion)


def _verify_analysis_requirement_assertion(
    assertion: Mapping[str, object],
    analysis_subject_ref: Mapping[str, str],
    dimension: str,
) -> None:
    verification = assertion.get("verification")
    extensions = assertion.get("extensions")
    if (
        assertion.get("subject_ref") != dict(analysis_subject_ref)
        or assertion.get("predicate") != f"verified_intended_{dimension}"
        or assertion.get("semantic_role") != "intended"
        or assertion.get("assertion_class") != "deterministic_derivation"
        or assertion.get("epistemic_status") != "accepted"
        or assertion.get("authority_scope") != "scientific_intent"
        or assertion.get("independently_checkable") is not True
        or assertion.get("finding_eligibility") != "ineligible"
        or _actor_kind(assertion) != "controller"
        or not isinstance(verification, Mapping)
        or verification.get("status") != "verified"
        or verification.get("method") != "deterministic_comparison"
        or not isinstance(extensions, Mapping)
        or not _ref_type(extensions.get("x-answer-ref"), "answer")
        or not isinstance(extensions.get("x-answer-digest"), str)
        or not isinstance(extensions.get("x-scientific-check-id"), str)
        or not isinstance(extensions.get("x-scientific-check-manifest-digest"), str)
        or not isinstance(extensions.get("x-scientific-check-scope-join-digest"), str)
    ):
        raise PosthocMethodLedgerError(
            "analysis requirement is not a controller-verified scope-bound scientist Answer"
        )
    _assertion_sources(assertion)


def _verify_observed_assertion(
    assertion: Mapping[str, object], claim_id: str, dimension: str
) -> None:
    verification = assertion.get("verification")
    if (
        not _ref_equals(assertion.get("subject_ref"), "claim", claim_id)
        or assertion.get("predicate") != f"reported_{dimension}"
        or assertion.get("semantic_role") != "reported"
        or assertion.get("assertion_class") != "explicit_text_extraction"
        or assertion.get("epistemic_status") != "accepted"
        or assertion.get("authority_scope") != "reported_wording"
        or assertion.get("independently_checkable") is not True
        or assertion.get("finding_eligibility") != "eligible"
        or _actor_kind(assertion) not in {"controller", "parser"}
        or not isinstance(verification, Mapping)
        or verification.get("status") != "verified"
        or verification.get("method")
        not in {"structural_parser", "exact_quote_match", "deterministic_comparison"}
    ):
        raise PosthocMethodLedgerError("reported value is not an exact verified extraction")
    _assertion_sources(assertion)


def _verify_analysis_observed_assertion(
    assertion: Mapping[str, object], dimension: str, scope_join_digest: str
) -> str:
    verification = assertion.get("verification")
    extensions = assertion.get("extensions")
    subject = assertion.get("subject_ref")
    if (
        assertion.get("epistemic_status") != "accepted"
        or assertion.get("independently_checkable") is not True
        or assertion.get("finding_eligibility") != "ineligible"
        or not isinstance(verification, Mapping)
        or verification.get("status") != "verified"
        or not isinstance(extensions, Mapping)
        or extensions.get("x-scientific-check-scope-join-digest") != scope_join_digest
        or not isinstance(extensions.get("x-scientific-check-id"), str)
        or not _record_ref(subject)
    ):
        raise PosthocMethodLedgerError(
            "analysis observation is not an exact verified static-source or report extraction"
        )
    static = (
        assertion.get("predicate") == f"statically_observed_{dimension}"
        and assertion.get("semantic_role") == "observed"
        and assertion.get("assertion_class") == "deterministic_derivation"
        and assertion.get("authority_scope") == "none"
        and verification.get("method") in {"structural_parser", "deterministic_comparison"}
        and isinstance(subject, Mapping)
        and subject.get("record_type") in {"artifact", "file_record", "operation"}
        and _actor_kind(assertion) == "controller"
    )
    reported = (
        assertion.get("predicate") == f"reported_{dimension}"
        and assertion.get("semantic_role") == "reported"
        and assertion.get("assertion_class") == "explicit_text_extraction"
        and assertion.get("authority_scope") == "reported_wording"
        and verification.get("method") in {"structural_parser", "exact_quote_match"}
        and isinstance(subject, Mapping)
        and subject.get("record_type") == "artifact"
        and _actor_kind(assertion) in {"controller", "parser"}
    )
    if not static and not reported:
        raise PosthocMethodLedgerError(
            "analysis observation is not an exact verified static-source or report extraction"
        )
    _assertion_sources(assertion)
    return "static_source" if static else "reported_text"


def _canonical_scalar(value: object, label: str) -> str | int | float | bool:
    if isinstance(value, bool) or isinstance(value, str):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise PosthocMethodLedgerError(f"{label} must be a canonical finite scalar")


def _unique_string_array(
    value: object,
    label: str,
    *,
    allow_empty: bool,
    preserve_order: bool = False,
) -> list[str]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not all(isinstance(item, str) and item for item in value)
    ):
        raise PosthocMethodLedgerError(f"{label} must be an array of non-empty strings")
    normalized = list(value)
    if not allow_empty and not normalized:
        raise PosthocMethodLedgerError(f"{label} must not be empty")
    if len(normalized) != len(set(normalized)):
        raise PosthocMethodLedgerError(f"{label} must contain unique strings")
    return normalized if preserve_order else sorted(normalized)


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise PosthocMethodLedgerError(f"{field} is unavailable")
    return value


def _assertion_sources(assertion: Mapping[str, object]) -> list[dict[str, Any]]:
    refs = assertion.get("source_refs")
    if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes)):
        raise PosthocMethodLedgerError("assertion source references are unavailable")
    values = [deepcopy(dict(ref)) for ref in refs if isinstance(ref, Mapping)]
    if not values:
        raise PosthocMethodLedgerError("assertion source references are unavailable")
    return values


def _slot_sources(slot: Mapping[str, object]) -> list[dict[str, Any]]:
    refs = slot.get("searched_source_refs", [])
    if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes)):
        return []
    return [deepcopy(dict(ref)) for ref in refs if isinstance(ref, Mapping)]


def _deduplicate_sources(refs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_value = {canonical_json(ref): deepcopy(dict(ref)) for ref in refs}
    return [by_value[key] for key in sorted(by_value)]


def _assertion_ref(assertion: Mapping[str, object]) -> dict[str, str]:
    return {
        "record_type": "semantic_assertion",
        "record_id": _required_string(assertion.get("assertion_id"), "assertion_id"),
    }


def _actor_kind(assertion: Mapping[str, object]) -> object:
    provenance = assertion.get("provenance")
    if not isinstance(provenance, Mapping):
        return None
    actor = provenance.get("actor")
    return actor.get("actor_kind") if isinstance(actor, Mapping) else None


def _ref_equals(value: object, record_type: str, record_id: str) -> bool:
    return (
        isinstance(value, Mapping)
        and value.get("record_type") == record_type
        and value.get("record_id") == record_id
    )


def _ref_type(value: object, record_type: str) -> bool:
    return (
        isinstance(value, Mapping)
        and value.get("record_type") == record_type
        and isinstance(value.get("record_id"), str)
        and bool(value.get("record_id"))
    )


def _record_ref(value: object) -> bool:
    return (
        isinstance(value, Mapping)
        and isinstance(value.get("record_type"), str)
        and bool(value.get("record_type"))
        and isinstance(value.get("record_id"), str)
        and bool(value.get("record_id"))
    )
