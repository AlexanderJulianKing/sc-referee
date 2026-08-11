from __future__ import annotations

from copy import deepcopy

import pytest

from sc_referee.controller import (
    _build_contract_questions,
    _derive_posthoc_ledger_disclosures,
)
from sc_referee.core.ids import semantic_digest
from sc_referee.interaction import (
    _answer_authority,
    _apply_structured_contract_answer,
    _build_work_item,
    _derive_verified_posthoc_intent_assertions,
)
from sc_referee.method_contracts import SCIENTIFIC_CONTRACT_DIMENSIONS
from sc_referee.posthoc_method_ledger import (
    POSTHOC_METHOD_LEDGER_MANIFEST,
    PosthocMethodLedgerError,
    project_analysis_posthoc_method_ledger,
    project_posthoc_method_ledger,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.version import SCHEMA_VERSION


def _source(line: int) -> dict[str, object]:
    return {
        "source_kind": "file_span",
        "locator": f"report.md:{line}",
        "path": "report.md",
        "content_digest": "sha256:" + "a" * 64,
        "start_line": line,
        "end_line": line,
        "quoted_text": "Exact bounded method declaration.",
    }


def _case(
    *,
    dimension: str,
    required: object,
    reported: object,
    state: str = "known",
) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    claim = {
        "claim_id": "claim:posthoc",
        "scientific_contract_id": "contract:posthoc",
    }
    requirement_id = f"assertion:required:{dimension}"
    requirement = {
        "record_type": "semantic_assertion",
        "assertion_id": requirement_id,
        "subject_ref": {"record_type": "claim", "record_id": "claim:posthoc"},
        "predicate": f"verified_intended_{dimension}",
        "object": required,
        "semantic_role": "intended",
        "assertion_class": "deterministic_derivation",
        "epistemic_status": "accepted",
        "authority_scope": "scientific_intent",
        "independently_checkable": True,
        "finding_eligibility": "eligible",
        "verification": {"status": "verified", "method": "deterministic_comparison"},
        "source_refs": [_source(1)],
        "provenance": {"actor": {"actor_kind": "controller"}},
        "extensions": {
            "x-answer-ref": {"record_type": "answer", "record_id": "answer:posthoc"},
            "x-answer-digest": "sha256:" + "b" * 64,
        },
    }
    observed = {
        "record_type": "semantic_assertion",
        "assertion_id": f"assertion:reported:{dimension}",
        "subject_ref": {"record_type": "claim", "record_id": "claim:posthoc"},
        "predicate": f"reported_{dimension}",
        "object": reported,
        "semantic_role": "reported",
        "assertion_class": "explicit_text_extraction",
        "epistemic_status": "accepted",
        "authority_scope": "reported_wording",
        "independently_checkable": True,
        "finding_eligibility": "eligible",
        "verification": {"status": "verified", "method": "structural_parser"},
        "source_refs": [_source(2)],
        "provenance": {"actor": {"actor_kind": "parser"}},
    }
    slot: dict[str, object]
    if state == "known":
        slot = {
            "state": "known",
            "assertion_ids": [requirement_id],
            "accepted_assertion_ids": [requirement_id],
        }
    elif state == "not_applicable":
        slot = {
            "state": "not_applicable",
            "reason": "The scientist explicitly marked this dimension not applicable.",
            "searched_source_refs": [_source(1)],
        }
    else:
        slot = {
            "state": "unknown",
            "reason": "The scientist retained this dimension as unknown.",
            "searched_source_refs": [_source(1)],
        }
    contract = {
        "contract_id": "contract:posthoc",
        "scope": {
            "level": "claim",
            "subject_refs": [{"record_type": "claim", "record_id": "claim:posthoc"}],
        },
        "dimensions": {dimension: slot},
        "source_refs": [_source(1)],
    }
    return claim, contract, [requirement, observed]


def _project(
    claim: dict[str, object],
    contract: dict[str, object],
    assertions: list[dict[str, object]],
    *,
    dimension: str,
    form: str,
    forbidden: tuple[str, ...] = (),
) -> dict[str, object]:
    return project_posthoc_method_ledger(
        claim=claim,
        contract=contract,
        assertions=assertions,
        dimension=dimension,
        comparison_form=form,
        forbidden_members=forbidden,
    )


def _analysis_case(
    *, observed: str, state: str = "known"
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]], str]:
    subject = {"record_type": "publication_surface", "record_id": "surface:analysis"}
    scope_join = [
        {
            "source_ref": {"record_type": "operation", "record_id": "operation:method"},
            "relation": "writes_selected_artifact",
            "target_ref": subject,
        }
    ]
    scope_digest = semantic_digest(scope_join)
    requirement = {
        "record_type": "semantic_assertion",
        "assertion_id": "assertion:analysis-required",
        "subject_ref": subject,
        "predicate": "verified_intended_scale_and_orientation",
        "object": "repair_before_emission",
        "semantic_role": "intended",
        "assertion_class": "deterministic_derivation",
        "epistemic_status": "accepted",
        "authority_scope": "scientific_intent",
        "independently_checkable": True,
        "finding_eligibility": "ineligible",
        "verification": {"status": "verified", "method": "deterministic_comparison"},
        "source_refs": [_source(1)],
        "provenance": {"actor": {"actor_kind": "controller"}},
        "extensions": {
            "x-answer-ref": {"record_type": "answer", "record_id": "answer:analysis"},
            "x-answer-digest": "sha256:" + "b" * 64,
            "x-scientific-check-id": "check:founder-orientation",
            "x-scientific-check-manifest-digest": "sha256:" + "c" * 64,
            "x-scientific-check-scope-join-digest": scope_digest,
        },
    }
    static = {
        "record_type": "semantic_assertion",
        "assertion_id": "assertion:analysis-static",
        "subject_ref": {"record_type": "operation", "record_id": "operation:method"},
        "predicate": "statically_observed_scale_and_orientation",
        "object": observed,
        "semantic_role": "observed",
        "assertion_class": "deterministic_derivation",
        "epistemic_status": "accepted",
        "authority_scope": "none",
        "independently_checkable": True,
        "finding_eligibility": "ineligible",
        "verification": {"status": "verified", "method": "structural_parser"},
        "source_refs": [_source(2)],
        "provenance": {"actor": {"actor_kind": "controller"}},
        "extensions": {
            "x-scientific-check-id": "check:founder-orientation",
            "x-scientific-check-scope-join-digest": scope_digest,
        },
    }
    slot: dict[str, object]
    if state == "known":
        slot = {
            "state": "known",
            "assertion_ids": [requirement["assertion_id"]],
            "accepted_assertion_ids": [requirement["assertion_id"]],
        }
    else:
        slot = {
            "state": "unknown",
            "reason": "The scientist retained this review requirement as unknown.",
            "searched_source_refs": [_source(1)],
        }
    contract = {
        "contract_id": "contract:analysis",
        "scope": {"level": "analysis", "subject_refs": [subject]},
        "dimensions": {"scale_and_orientation": slot},
        "source_refs": [_source(1)],
    }
    return contract, [requirement, static], scope_join, scope_digest


def test_manifest_defines_only_three_forms_and_disallows_production_findings() -> None:
    assert set(POSTHOC_METHOD_LEDGER_MANIFEST["comparison_forms"]) == {
        "value_equals",
        "set_relation",
        "step_precedes",
    }
    assert POSTHOC_METHOD_LEDGER_MANIFEST["project_code_execution"] is False
    assert POSTHOC_METHOD_LEDGER_MANIFEST["production_finding_permitted"] is False


def test_analysis_scoped_static_operand_projects_review_incompatibility() -> None:
    contract, assertions, scope_join, scope_digest = _analysis_case(observed="supplied_directly")

    result = project_analysis_posthoc_method_ledger(
        analysis_subject_ref={
            "record_type": "publication_surface",
            "record_id": "surface:analysis",
        },
        contract=contract,
        assertions=assertions,
        observed_assertion_ids=["assertion:analysis-static"],
        dimension="scale_and_orientation",
        comparison_form="value_equals",
        scope_join_path=scope_join,
        scope_join_digest=scope_digest,
    )

    assert result["outcome"] == "exact_conflict_candidate"
    assert result["authority"]["observed"] == "verified_static_source"
    assert "statically inspected operand is incompatible" in result["basis"]
    assert result["production_finding_permitted"] is False
    assert "claim_id" not in result


def test_analysis_scoped_unknown_never_becomes_a_conflict() -> None:
    contract, assertions, scope_join, scope_digest = _analysis_case(
        observed="supplied_directly", state="unknown"
    )

    result = project_analysis_posthoc_method_ledger(
        analysis_subject_ref={
            "record_type": "publication_surface",
            "record_id": "surface:analysis",
        },
        contract=contract,
        assertions=assertions,
        observed_assertion_ids=["assertion:analysis-static"],
        dimension="scale_and_orientation",
        comparison_form="value_equals",
        scope_join_path=scope_join,
        scope_join_digest=scope_digest,
    )

    assert result["outcome"] == "unresolved_obligation"


def test_analysis_scope_join_and_cross_plane_disagreement_fail_closed() -> None:
    contract, assertions, scope_join, scope_digest = _analysis_case(observed="supplied_directly")
    reported = deepcopy(assertions[1])
    reported.update(
        {
            "assertion_id": "assertion:analysis-report",
            "subject_ref": {"record_type": "artifact", "record_id": "artifact:report"},
            "predicate": "reported_scale_and_orientation",
            "object": "repair_before_emission",
            "semantic_role": "reported",
            "assertion_class": "explicit_text_extraction",
            "authority_scope": "reported_wording",
            "verification": {"status": "verified", "method": "exact_quote_match"},
            "provenance": {"actor": {"actor_kind": "parser"}},
        }
    )
    result = project_analysis_posthoc_method_ledger(
        analysis_subject_ref={
            "record_type": "publication_surface",
            "record_id": "surface:analysis",
        },
        contract=contract,
        assertions=[*assertions, reported],
        observed_assertion_ids=["assertion:analysis-static", "assertion:analysis-report"],
        dimension="scale_and_orientation",
        comparison_form="value_equals",
        scope_join_path=scope_join,
        scope_join_digest=scope_digest,
    )
    assert result["outcome"] == "unresolved_obligation"
    assert "disagree" in result["basis"]

    mutated_join = deepcopy(scope_join)
    mutated_join[0]["relation"] = "co_present_in_repository"
    with pytest.raises(PosthocMethodLedgerError, match="scope-join digest mismatch"):
        project_analysis_posthoc_method_ledger(
            analysis_subject_ref={
                "record_type": "publication_surface",
                "record_id": "surface:analysis",
            },
            contract=contract,
            assertions=assertions,
            observed_assertion_ids=["assertion:analysis-static"],
            dimension="scale_and_orientation",
            comparison_form="value_equals",
            scope_join_path=mutated_join,
            scope_join_digest=scope_digest,
        )


def test_analysis_scoped_question_answer_and_work_item_validate_under_active_schema(
    schema_root,
) -> None:
    run_id = "audit:analysis-interaction"
    created_at = "2026-07-29T20:00:00Z"
    snapshot_digest = "sha256:" + "d" * 64
    surface_ref = {
        "record_type": "publication_surface",
        "record_id": "publication-surface:analysis",
    }
    scope_join = [
        {
            "source_ref": {"record_type": "operation", "record_id": "operation:method"},
            "relation": "writes_selected_artifact",
            "target_ref": surface_ref,
        }
    ]
    scope_digest = semantic_digest(scope_join)
    dimensions = {
        dimension: {
            "state": "unknown",
            "reason": "No scope-bound scientist requirement has been supplied.",
            "searched_source_refs": [_source(1)],
        }
        for dimension in SCIENTIFIC_CONTRACT_DIMENSIONS
    }
    contract = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "scientific_contract",
        "contract_id": "contract:analysis-interaction",
        "audit_run_id": run_id,
        "title": "Analysis-scoped method requirement",
        "status": "draft",
        "scope": {"level": "analysis", "subject_refs": [surface_ref]},
        "dimensions": dimensions,
        "source_refs": [_source(1)],
        "created_at": created_at,
    }
    question = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "material_question",
        "question_id": "question:analysis-interaction",
        "audit_run_id": run_id,
        "question": "Which orientation governs this selected analysis?",
        "unknown_semantic_dimension": "scientific_contract",
        "why_it_matters": "The exact static operand can be compared only after this choice.",
        "candidate_answers": [
            {
                "answer_id": "answer-option:repair",
                "label": "Repair before emission",
                "value": {"scale_and_orientation": "repair_before_emission"},
            },
            {
                "answer_id": "answer-option:unknown",
                "label": "Retain unknown",
                "value": {"action": "retain_unknown"},
            },
        ],
        "evidence_searched": [
            {"source": "immutable Python source", "result": "One exact operand was observed."}
        ],
        "blocked_detector_ids": [],
        "affected_claim_ids": [],
        "linked_conditional_concern_ids": [],
        "priority": "high",
        "status": "open",
        "answer_ids": [],
        "created_at": created_at,
        "provenance": {
            "actor": {"actor_kind": "controller", "actor_id": "controller:sc-referee"},
            "method": "deterministic_analysis_question_generation",
            "created_at": created_at,
            "tool": "sc-referee",
            "tool_version": "0.3.0.dev0",
        },
        "extensions": {
            "x-contract-ref": {
                "record_type": "scientific_contract",
                "record_id": contract["contract_id"],
            },
            "x-unresolved-dimensions": ["scale_and_orientation"],
            "x-analysis-subject-ref": surface_ref,
            "x-posthoc-ledger-profile": "posthoc_method_ledger_v1",
            "x-posthoc-comparison-forms": {"scale_and_orientation": "value_equals"},
            "x-posthoc-reported-assertion-ids": {
                "scale_and_orientation": ["assertion:analysis-static"]
            },
            "x-scientific-check-id": "check:founder-orientation",
            "x-scientific-check-manifest-digest": "sha256:" + "e" * 64,
            "x-scientific-check-adapter-bindings": [
                {"adapter_id": "adapter:python", "observation_digest": "sha256:" + "f" * 64}
            ],
            "x-scientific-check-scope-join-path": scope_join,
            "x-scientific-check-scope-join-digest": scope_digest,
        },
    }
    answer = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "answer",
        "answer_id": "answer:analysis-interaction",
        "audit_run_id": run_id,
        "question_ref": {
            "record_type": "material_question",
            "record_id": question["question_id"],
        },
        "source_snapshot_digest": snapshot_digest,
        "answer_kind": "structured_value",
        "answer_value": {"scale_and_orientation": "repair_before_emission"},
        "respondent": {"actor_kind": "human", "actor_id": "scientist:test"},
        "response_source": "provided_answer_file",
        "authority_scope": {
            "authority_kind": "scientific_intent",
            "subject_refs": [surface_ref],
            "semantic_dimensions": ["scale_and_orientation"],
        },
        "certainty": {"level": "explicit", "basis": "Scientist supplied the value."},
    }
    answer["answer_digest"] = semantic_digest(answer)
    surface = {
        "publication_surface_id": "publication-surface:analysis",
        "status": "resolved",
    }

    assertions = _apply_structured_contract_answer(
        answer,
        question,
        [],
        [contract],
        run_id,
        created_at,
        snapshot_digest,
        publication_surfaces=[surface],
    )

    assert len(assertions) == 2
    derived = next(item for item in assertions if item["predicate"].startswith("verified_"))
    assert derived["subject_ref"] == surface_ref
    assert derived["finding_eligibility"] == "ineligible"
    assert derived["extensions"]["x-scientific-check-scope-join-digest"] == scope_digest
    assert contract["status"] == "draft"

    parent_bundle = {"scientific_contracts": [contract]}
    assert _answer_authority(parent_bundle, question) == ([surface_ref], "scientific_intent")
    work_item = _build_work_item(
        {
            "audit_run_id": run_id,
            "source_snapshot_digest": snapshot_digest,
            "prompt_template": {
                "prompt_template_id": "prompt:analysis",
                "prompt_template_digest": "sha256:" + "1" * 64,
            },
        },
        parent_bundle,
        question,
        created_at,
    )
    assert work_item["target_refs"] == [surface_ref]
    registry = LocalSchemaRegistry(schema_root)
    for record in [question, *assertions, contract, work_item]:
        registry.validate(record)


def test_question_is_scheduled_only_from_one_exact_closed_reported_assertion() -> None:
    claim, contract, assertions = _case(
        dimension="adjustment_set",
        required=["batch"],
        reported=["batch"],
        state="unknown",
    )
    claim.update(
        {
            "record_type": "claim",
            "claim_status": "final",
            "claim_kind": "quantitative",
            "extensions": {},
        }
    )
    assertions = assertions[1:]
    assertions[0]["extensions"] = {"x-posthoc-comparison-form": "set_relation"}

    questions = _build_contract_questions(
        "audit:posthoc",
        "2026-07-29T16:00:00Z",
        [claim],
        [contract],
        assertions,
    )

    assert len(questions) == 1
    question = questions[0]
    assert question["extensions"]["x-posthoc-comparison-forms"] == {
        "adjustment_set": "set_relation"
    }
    assert question["extensions"]["x-posthoc-reported-assertion-ids"] == {
        "adjustment_set": ["assertion:reported:adjustment_set"]
    }
    assert question["extensions"]["x-posthoc-ledger-profile"] == "posthoc_method_ledger_v1"

    duplicate = deepcopy(assertions[0])
    duplicate["assertion_id"] = "assertion:reported:adjustment-set:duplicate"
    conflicted = _build_contract_questions(
        "audit:posthoc",
        "2026-07-29T16:00:00Z",
        [claim],
        [contract],
        [*assertions, duplicate],
    )[0]
    assert "x-posthoc-comparison-forms" not in conflicted["extensions"]


def test_verified_scientist_answer_projects_into_exact_ledger(schema_root) -> None:
    claim, contract, assertions = _case(
        dimension="adjustment_set",
        required=["batch", "sex"],
        reported=["batch", "sex"],
        state="unknown",
    )
    assertions[1]["extensions"] = {"x-posthoc-comparison-form": "set_relation"}
    question = {
        "question_id": "question:posthoc",
        "affected_claim_ids": ["claim:posthoc"],
        "extensions": {
            "x-posthoc-comparison-forms": {"adjustment_set": "set_relation"},
            "x-posthoc-reported-assertion-ids": {
                "adjustment_set": ["assertion:reported:adjustment_set"]
            },
        },
    }
    answer = {
        "answer_id": "answer:posthoc",
        "audit_run_id": "audit:posthoc",
        "question_ref": {"record_type": "material_question", "record_id": "question:posthoc"},
        "source_snapshot_digest": "sha256:" + "c" * 64,
        "answer_value": {"adjustment_set": ["batch", "sex"]},
        "respondent": {"actor_kind": "human", "actor_id": "scientist:test"},
        "response_source": "interactive_scientist",
        "authority_scope": {
            "authority_kind": "scientific_intent",
            "subject_refs": [{"record_type": "claim", "record_id": "claim:posthoc"}],
            "semantic_dimensions": ["adjustment_set"],
        },
        "certainty": {"level": "explicit", "basis": "Scientist supplied the value."},
    }
    answer["answer_digest"] = semantic_digest(answer)
    declaration = {
        "assertion_id": "assertion:scientist:adjustment_set",
        "predicate": "intended_adjustment_set",
        "object": ["batch", "sex"],
        "assertion_class": "scientist_declaration",
        "finding_eligibility": "ineligible",
        "provenance": {"actor": {"actor_kind": "human"}},
        "extensions": {"x-answer-ref": {"record_type": "answer", "record_id": "answer:posthoc"}},
    }

    derived = _derive_verified_posthoc_intent_assertions(
        answer=answer,
        question=question,
        claim=claim,
        contract=contract,
        scientist_assertions=[declaration],
        run_id="audit:posthoc",
        created_at="2026-07-29T16:01:00Z",
        source_snapshot_digest="sha256:" + "c" * 64,
    )

    assert len(derived) == 1
    assert derived[0]["extensions"]["x-answer-digest"] == answer["answer_digest"]
    assert derived[0]["extensions"]["x-posthoc-comparison-form"] == "set_relation"
    slot = contract["dimensions"]["adjustment_set"]
    slot.clear()
    slot.update(
        {
            "state": "known",
            "assertion_ids": [declaration["assertion_id"], derived[0]["assertion_id"]],
            "accepted_assertion_ids": [
                declaration["assertion_id"],
                derived[0]["assertion_id"],
            ],
        }
    )
    result = _project(
        claim,
        contract,
        [assertions[1], declaration, derived[0]],
        dimension="adjustment_set",
        form="set_relation",
    )
    assert result["outcome"] == "covered_negative"
    disclosures = _derive_posthoc_ledger_disclosures(
        {
            "audit_run_id": "audit:posthoc",
            "locked_at": "2026-07-29T16:02:00Z",
            "claims": [claim],
            "scientific_contracts": [contract],
            "semantic_assertions": [assertions[1], declaration, derived[0]],
        }
    )
    assert len(disclosures) == 1
    LocalSchemaRegistry(schema_root).validate(disclosures[0])
    assert disclosures[0]["coverage_status"] == "covered"
    assert disclosures[0]["extensions"]["x-posthoc-method-ledger"]["outcome"] == (
        "covered_negative"
    )


@pytest.mark.parametrize(
    ("reported", "outcome"),
    [("full_map", "covered_negative"), ("called_span", "exact_conflict_candidate")],
)
def test_value_equals_is_exact_replay_stable(reported: str, outcome: str) -> None:
    claim, contract, assertions = _case(
        dimension="denominator_or_universe",
        required="full_map",
        reported=reported,
    )

    first = _project(
        claim,
        contract,
        assertions,
        dimension="denominator_or_universe",
        form="value_equals",
    )
    second = _project(
        deepcopy(claim),
        deepcopy(contract),
        deepcopy(assertions),
        dimension="denominator_or_universe",
        form="value_equals",
    )

    assert first == second
    assert first["outcome"] == outcome
    assert first["production_finding_permitted"] is False
    assert first["authority"]["historical_intent_established"] is False
    assert first["authority"]["execution_established"] is False


def test_set_relation_checks_required_and_forbidden_members() -> None:
    claim, contract, assertions = _case(
        dimension="adjustment_set",
        required=["batch", "sex"],
        reported=["batch", "site", "sex"],
    )

    covered = _project(
        claim,
        contract,
        assertions,
        dimension="adjustment_set",
        form="set_relation",
        forbidden=("technical_pool",),
    )
    assertions[1]["object"] = ["batch", "technical_pool"]
    conflict = _project(
        claim,
        contract,
        assertions,
        dimension="adjustment_set",
        form="set_relation",
        forbidden=("technical_pool",),
    )

    assert covered["outcome"] == "covered_negative"
    assert conflict["outcome"] == "exact_conflict_candidate"
    assert conflict["comparison"]["missing_required_members"] == ["sex"]
    assert conflict["comparison"]["present_forbidden_members"] == ["technical_pool"]


@pytest.mark.parametrize(
    ("observed", "outcome"),
    [
        (["harmonize_labels", "aggregate_exposure"], "covered_negative"),
        (["aggregate_exposure", "harmonize_labels"], "exact_conflict_candidate"),
        (["aggregate_exposure"], "unsupported_path"),
    ],
)
def test_step_precedes_distinguishes_reversal_from_missing_evidence(
    observed: list[str], outcome: str
) -> None:
    claim, contract, assertions = _case(
        dimension="selection_process",
        required=["harmonize_labels", "aggregate_exposure"],
        reported=observed,
    )

    result = _project(
        claim,
        contract,
        assertions,
        dimension="selection_process",
        form="step_precedes",
    )

    assert result["outcome"] == outcome


@pytest.mark.parametrize(
    ("state", "outcome"),
    [("unknown", "unresolved_obligation"), ("not_applicable", "not_applicable")],
)
def test_unknown_and_not_applicable_never_become_conflicts(state: str, outcome: str) -> None:
    claim, contract, assertions = _case(
        dimension="control_set",
        required=["negative_controls"],
        reported=["negative_controls"],
        state=state,
    )

    result = _project(
        claim,
        contract,
        assertions,
        dimension="control_set",
        form="set_relation",
    )

    assert result["outcome"] == outcome
    assert result["production_finding_permitted"] is False


def test_missing_or_conflicting_reported_value_fails_closed() -> None:
    claim, contract, assertions = _case(
        dimension="measurement_model",
        required="negative_binomial",
        reported="poisson",
    )
    missing = _project(
        claim,
        contract,
        assertions[:1],
        dimension="measurement_model",
        form="value_equals",
    )
    duplicate = deepcopy(assertions[1])
    duplicate["assertion_id"] = "assertion:reported:measurement-model:duplicate"
    conflicting = _project(
        claim,
        contract,
        [*assertions, duplicate],
        dimension="measurement_model",
        form="value_equals",
    )

    assert missing["outcome"] == "unsupported_path"
    assert conflicting["outcome"] == "unresolved_obligation"


@pytest.mark.parametrize(
    "mutation",
    ["scope", "model_authority", "nonfinite", "duplicate_steps", "wrong_form_dimension"],
)
def test_scope_authority_operand_and_form_mutations_fail_closed(mutation: str) -> None:
    claim, contract, assertions = _case(
        dimension="selection_process",
        required=["calibrate", "aggregate"],
        reported=["calibrate", "aggregate"],
    )
    dimension = "selection_process"
    form = "step_precedes"
    if mutation == "scope":
        contract["scope"]["subject_refs"] = [{"record_type": "claim", "record_id": "claim:other"}]
    elif mutation == "model_authority":
        assertions[0]["provenance"] = {"actor": {"actor_kind": "model"}}
    elif mutation == "nonfinite":
        claim, contract, assertions = _case(
            dimension="measurement_model",
            required=float("nan"),
            reported=1.0,
        )
        dimension = "measurement_model"
        form = "value_equals"
    elif mutation == "duplicate_steps":
        assertions[1]["object"] = ["calibrate", "calibrate"]
    else:
        claim, contract, assertions = _case(
            dimension="target_population",
            required=["calibrate", "aggregate"],
            reported=["calibrate", "aggregate"],
        )
        dimension = "target_population"

    with pytest.raises(PosthocMethodLedgerError):
        _project(
            claim,
            contract,
            assertions,
            dimension=dimension,
            form=form,
        )
