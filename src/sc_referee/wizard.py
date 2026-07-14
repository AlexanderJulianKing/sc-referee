"""The design wizard: a plain-language browser questionnaire that confirms the experimental
design before the audit.

A front-end over init.propose / init.synthesize_config / init.confirm_config. propose() drafts a
design; the wizard turns its roles into plain-language questions (the data's columns as dropdowns),
serves them as an HTML form on a localhost http.server, and re-synthesizes a
`confirmed_by_human: true` config from the human's answers. Answering the questions IS ratifying the
design — which is what lets the report block.
"""
from __future__ import annotations

import html as _html
import re
import threading
import urllib.parse
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer


@dataclass(frozen=True)
class Question:
    role: str
    prompt: str
    why: str
    kind: str                      # column | columns | level | radio | choice | file
    options: tuple = ()
    default: object = None
    required: bool = False
    proposal_source: str | None = None
    more_options: tuple = ()       # extra choices offered behind an escape hatch (batch: every other column)


@dataclass(frozen=True)
class ReviewFact:
    label: str
    value: str
    caution: bool = False


@dataclass(frozen=True)
class ReviewClaim:
    label: str
    title: str
    facts: tuple[ReviewFact, ...] = ()


def csp_questions(config, *, group_source_column: str | None = None,
                  proposal: dict | None = None) -> list[Question]:
    """Fixed, in-domain ceremony dispatched by exact CSP contract version."""
    if proposal and proposal.get("contract_type") == "contamination_basis_obligation/v1":
        from sc_referee.csp_contracts.contamination_basis_obligation_v1 import (
            CAUSAL_FIELDS, MANIFEST, MEASUREMENT_FIELDS,
        )

        boundary = (
            "Ambient enrichment does not prove non-expression; continuous and thresholded "
            "bases are different; association does not establish causal role; adjusting for a "
            "mediator or estimand component can remove the intended effect; Not sure renders "
            "not_checked; confirmation can authorize a conditional MAJOR."
        )
        questions: list[Question] = []
        for field_id in MEASUREMENT_FIELDS + CAUSAL_FIELDS:
            section = "measurement" if field_id in MEASUREMENT_FIELDS else "causal"
            prefix = f"csp.contamination.{section}.{field_id}"
            questions.extend([
                Question(
                    prefix,
                    f"Do you confirm the exact {field_id.replace('_', ' ')} for this scope?",
                    boundary,
                    "csp_semantic", ("not_sure", "yes", "no"), "not_sure", True,
                ),
                Question(
                    prefix + ".evidence",
                    f"Evidence identity for {field_id.replace('_', ' ')}",
                    "This evidence is field-specific; another field's evidence cannot substitute.",
                    "text", (), None, True,
                ),
                Question(
                    prefix + ".teach_back",
                    f"Select the teach-back for {field_id.replace('_', ' ')}",
                    boundary,
                    "csp_ceremony", ("not_sure", MANIFEST.teach_back_ids[field_id]),
                    "not_sure", True,
                ),
                Question(
                    prefix + ".consequence",
                    "A yes may authorize a conditional finding for this exact field and scope.",
                    "Invalidating either component removes authorization for an adverse finding.",
                    "csp_ceremony", ("not_sure", "yes"), "not_sure", True,
                ),
            ])
        questions.append(Question(
            "csp.contamination.authority_attested",
            MANIFEST.authority_attestation,
            "Authority is bound to this exact measurement, basis, fit, rows, and estimand.",
            "csp_ceremony", ("not_sure", "yes"), "not_sure", True,
        ))
        return questions
    if proposal and proposal.get("contract_type") == "target_population_estimand/v1":
        from sc_referee.csp_contracts.target_population_estimand_v1 import MANIFEST

        prefix = "csp.target_population."
        population = str(proposal["target_population_id"])
        registry_name = population.split(":", 2)[1].replace("_", " ").title()
        columns = " × ".join(proposal["census_stratum_columns"])
        teach_back = (
            f"Should this describe the average across the {registry_name} registry's {columns} "
            "categories using that registry's counts, rather than the proportions in these donors?"
        )
        values = {
            "functional": proposal["functional_candidate"],
            "reported_scalar_id": proposal["reported_scalar_id"],
            "target_population_id": proposal["target_population_id"],
            "census_stratum_columns": proposal["census_stratum_columns"],
            "evaluation_stratum_columns": proposal["evaluation_stratum_columns"],
            "stratum_levels": proposal["stratum_levels"],
            "stratum_ledger_identity": proposal["stratum_ledger_identity"],
            "census_artifact_identity": proposal["census_artifact_identity"],
            "census_count_ledger_identity": proposal["census_count_ledger_identity"],
            "census_total_n": proposal["census_total_n"],
            "census_stratum_counts": proposal["census_stratum_counts"],
            "weight_vector_identity": proposal["weight_vector_identity"],
            "weight_vector": proposal["weight_vector"],
            "support_policy": proposal["support_policy_candidate"],
        }
        questions = []
        for field_id in MANIFEST.required_fields:
            expected = MANIFEST.teach_back_ids[field_id]
            options = (("not_sure", "population_average_exact_census", "across_population")
                       if field_id == "functional" else ("not_sure", expected))
            questions.append(Question(
                prefix + field_id,
                f"Confirm {field_id.replace('_', ' ')}: {values[field_id]!r}",
                teach_back,
                "csp_semantic", options, "not_sure", True,
            ))
        questions.extend([
            Question(
                prefix + "consequence_acknowledged",
                "Confirmation may allow target_population to use this exact population premise.",
                "It applies only to the exact result, coefficient, rows, estimand, census, strata, and weights shown.",
                "csp_ceremony", ("not_sure", "yes"), "not_sure", True,
            ),
            Question(
                prefix + "authority_attested",
                MANIFEST.authority_attestation,
                "This is a self-attestation for the exact scientific premise.",
                "csp_ceremony", ("not_sure", "yes"), "not_sure", True,
            ),
        ])
        return questions

    """Fixed, in-domain ceremony for the registered two-field premise."""
    group = str(group_source_column)
    return [
        Question(
            f"csp.{group}.between_group_policy",
            f"For this condition comparison, must arbitrary differences among {group} groups be removed?",
            f"Choose this only if donor, plate, or {group} baseline differences are nuisance differences "
            "the analysis must remove.",
            "csp_semantic", ("not_sure", "remove_arbitrary"), "not_sure", True,
        ),
        Question(
            f"csp.{group}.may_rely_on_re_exogeneity",
            f"Does this result require exact fixed-effect-equivalent projection of {group}?",
            "A random intercept never satisfies this obligation, no matter how close its estimates "
            "look. A tolerance-level fixed-effect sensitivity is not exact projection and is not "
            "what this contract means.",
            "csp_semantic", ("not_sure", "must_not_rely", "may_rely",
                             "sensitivity_at_tolerance_is_sufficient"), "not_sure", True,
        ),
        Question(
            f"csp.{group}.consequence_acknowledged",
            "Confirmation may allow confounding_random_intercept_conditional to flag this result.",
            "This consequence applies only to the exact result, coefficient, rows, estimand, and group shown.",
            "csp_ceremony", ("not_sure", "yes"), "not_sure", True,
        ),
        Question(
            f"csp.{group}.authority_attested",
            "I am responsible for this result's scientific interpretation",
            "This is a self-attestation for the exact scientific premise.",
            "csp_ceremony", ("not_sure", "yes"), "not_sure", True,
        ),
    ]


def _required(role, config) -> bool:
    """A role we could not settle (or settled only tentatively) must be answered, never silently
    accepted — we don't ratify a guess."""
    if role in (config.get("unresolved") or []):
        return True
    return (config.get("confidence") or {}).get(role) == "low"


def _technical_column_candidates(columns, declared=()) -> tuple:
    """Prefer metadata names that plausibly encode processing, while retaining declared batches."""
    terms = (
        "batch", "run", "lane", "plate", "library", "chemistry", "prep", "sequenc",
        "capture", "flowcell", "chip", "well", "day", "site", "center", "centre",
    )
    ordered = []
    for column in (*tuple(declared or ()), *tuple(columns)):
        name = str(column).lower()
        if column not in ordered and (column in tuple(declared or ()) or any(t in name for t in terms)):
            ordered.append(column)
    return tuple(ordered)


def design_questions(config, columns, *, analysis_types) -> list:
    """Turn a proposed config (from init.propose) + the data's columns into the ordered question
    list, each prefilled with the tool's guess and flagged required when the guess is uncertain."""
    columns = list(columns)
    design = config.get("design") or {}
    contrast = (config.get("contrasts") or [{}])[0]
    reported = config.get("reported_results") or {}
    analysis_type = config.get("analysis_type")
    analysis_names = {
        "condition_contrast_DE": "differential expression between conditions",
        "marker_detection": "marker detection",
        "differential_abundance": "differential abundance",
        "trajectory": "trajectory analysis",
        "other": "another analysis type",
    }
    condition = design.get("condition")
    replicate = (design.get("replicate_unit") or [None])[0]
    reference = contrast.get("reference")
    test = contrast.get("test")
    analysis_required = _required("analysis_type", config)
    condition_required = _required("condition", config)
    reference_required = _required("reference", config)
    replicate_required = _required("replicate_unit", config)
    declared_batches = tuple(design.get("batch") or ())
    batch_options = _technical_column_candidates(columns, declared_batches)
    questions = [
        Question("analysis_type",
                 (f"I read this as {analysis_names.get(analysis_type, str(analysis_type))}. "
                  "Is that right?" if analysis_type and not analysis_required else
                  "What kind of analysis is this?"),
                 "It selects which statistical checks apply.", "choice",
                 tuple(analysis_types), analysis_type,
                 analysis_required),
        Question("condition",
                 (f'I found “{condition}” as the column defining the groups being compared. '
                  "Is that right?" if condition and not condition_required else
                  "Which column defines the groups you're comparing?"),
                 "It's the biological variable whose effect you're measuring.", "column",
                 tuple(columns), condition, condition_required),
        Question("reference",
                 (f'I found “{reference}” as the baseline group. Is that right?'
                  if reference and not reference_required else
                  "Which group is the baseline?"),
                 "The effect is measured against this group.", "level",
                 (), reference, reference_required),
        Question("test",
                 (f'I found “{test}” as the group compared with the baseline. Is that right?'
                  if test and not reference_required else
                  "Which group is being compared with the baseline?"),
                 "The effect is measured for this group versus the baseline.", "level",
                 (), test, reference_required),
        Question("replicate_unit",
                 (f'I found “{replicate}” as one independent biological replicate. Is that right?'
                  if replicate and not replicate_required else
                  "What counts as one independent biological replicate?"),
                 "Usually a donor or subject; it sets your real sample size (n).", "column",
                 tuple(columns), replicate,
                 replicate_required),
        Question("batch",
                 "Does the supplied metadata include technical processing batches — such as "
                 "sequencing runs, days, plates, or 10x lanes? Select every column that records one.",
                 "A batch that lines up with the comparison can look like a biological effect. "
                 "Choose an explicit answer so Referee can distinguish no recorded batch from "
                 "scientific uncertainty.",
                 "columns", batch_options, declared_batches,
                 _required("batch", config),
                 # Escape hatch: every column NOT in the concise technical list stays reachable,
                 # so a batch column with an unconventional name is never silently unselectable.
                 more_options=tuple(c for c in columns if c not in batch_options)),
    ]
    if config.get("analysis_type") == "condition_contrast_DE":
        proposed = contrast.get("analyst_adjusted_for")
        proposed_extra = tuple(value for value in (proposed or ()) if value != condition)
        excluded = {condition, replicate}
        adjustment_options = tuple(dict.fromkeys(
            (*proposed_extra, *(column for column in columns if column not in excluded))
        ))
        if proposed is not None and len(proposed) == 0:
            adjusted_prompt = ("I read your model as adjusting for nothing beyond the comparison "
                               "itself. Confirm whether it included any additional covariates.")
        elif proposed_extra:
            adjusted_prompt = ("I read your model as adjusting for: " + ", ".join(proposed_extra) +
                               ". Confirm or correct the full list of variables it accounted for, "
                               "besides the comparison itself.")
        else:
            adjusted_prompt = ("Which variables did your analysis's model account for, besides the "
                               "comparison itself? Check every covariate that was in your model.")
        questions.append(
            Question(
                "analyst_adjusted_for",
                adjusted_prompt,
                "I compare this against the technical variables to see if anything confounding was "
                "left out of your model.",
                "columns",
                adjustment_options,
                proposed_extra if proposed is not None else None,
                _required("analyst_adjusted_for", config),
            )
        )
        if config.get("batch_modeling"):
            questions.append(
                Question(
                    "aggregation_key",
                    "Which columns identify each final fitted sample row?",
                    "The confirmed final row key is required to bind component facts exactly.",
                    "columns", tuple(columns), tuple(contrast.get("aggregation_key") or ()), True,
                )
            )
    proposed_unit = reported.get("unit_of_test")
    replicate_label = replicate or "for example, a patient"
    if proposed_unit == "cell":
        unit_prompt = ("I read your code as testing each CELL as a data point — not each biological "
                       f"replicate ({replicate_label}). Is that right?")
    elif proposed_unit == "sample":
        unit_prompt = ("I read your analysis as testing at the SAMPLE level — one value per "
                       f"replicate ({replicate_label}), not per cell. Is that right?")
    else:
        unit_prompt = ("Did your test treat each cell as a data point, or each biological replicate "
                       f"({replicate_label})?")
    questions.append(
        Question("unit_of_test", unit_prompt,
                 "Testing cells as if they were independent replicates inflates significance "
                 "(pseudoreplication) — the most common single-cell DE error.", "radio",
                 ("cell", "sample"), proposed_unit,
                 _required("unit_of_test", config))
    )
    proposals = {
        item.get("source_column"): item
        for item in (config.get("batch_modeling") or [])
        if isinstance(item, dict)
    }
    for batch in design.get("batch") or []:
        proposed = proposals.get(batch, {})
        prefix = f"batch_modeling.{batch}."
        questions.extend([
            Question(prefix + "modeled_as", f"How was {batch} modeled?",
                     "A random intercept may partially pool groups; this confirms structure only.",
                     "choice", ("fixed", "random_intercept", "fixed_and_random_intercept",
                                "absent", "upstream_handled", "unsupported"),
                     proposed.get("modeled_as"), True),
            Question(prefix + "random_group_column", "Which exact column defines its random groups?",
                     "This binds the proposed component to an observation column.", "column",
                     tuple(columns), proposed.get("random_group_column"), True),
            Question(prefix + "fixed_source_columns", "Which exact columns supply its fixed component?",
                     "This records provenance; a separate certificate decides any span.", "columns",
                     tuple(columns), tuple(proposed.get("fixed_source_columns") or ()), True),
            Question(prefix + "rows_exact", "Do these component facts cover the exact fitted rows?",
                     "Exact row coverage is required before deterministic row binding.", "radio",
                     ("yes", "no"), None, True),
            Question(prefix + "contrast_name", "Which contrast does this component belong to?",
                     "Component scope must match the audited contrast exactly.", "text", (),
                     (proposed.get("component_scope") or {}).get("contrast_name"), True),
            Question(prefix + "target_coefficient", "Which target coefficient does it belong to?",
                     "Component scope must match the audited target exactly.", "text", (),
                     (proposed.get("component_scope") or {}).get("target_coefficient"), True),
            Question(prefix + "fitted_result_id", "Which fitted result does it belong to?",
                     "This identifies the exact fitted-result scope.", "text", (),
                     (proposed.get("component_scope") or {}).get("fitted_result_id"), True),
            Question(prefix + "unsupported_components", "List any unsupported component categories.",
                     "The inventory must be explicit; an empty answer confirms none.", "columns",
                     ("random_slope", "correlated_random_effects", "crossed_random_effects",
                      "nested_random_effects", "glmm_integration", "penalty", "weight", "offset",
                      "transform", "upstream_operator", "other"),
                     tuple(proposed.get("unsupported_components") or ()), True),
        ])
    for proposal in config.get("csp_proposals") or []:
        if proposal.get("contract_type") in {
            "target_population_estimand/v1", "contamination_basis_obligation/v1"
        }:
            questions.extend(csp_questions(config, proposal=proposal))
        else:
            group = proposal.get("group_source_column")
            if group:
                questions.extend(csp_questions(config, group_source_column=group))
    return questions


def _roles_from_answers(answers):
    """The human's answers as a `Roles` — the semantic assignments; `synthesize_config` derives every
    formula from these + the data. Note `Roles` has no `test`: synthesize_config makes one contrast
    per non-reference level, and `answers_to_config` keeps the human's chosen one."""
    from sc_referee.roles import Roles

    batch = answers.get("batch")
    batch = (batch,) if isinstance(batch, str) else tuple(batch or ())
    batch_answered = "batch_answered" in answers
    rep = answers.get("replicate_unit")
    adjusted_answered = ("analyst_adjusted_for" in answers
                         or "analyst_adjusted_for_answered" in answers)
    adjusted = answers.get("analyst_adjusted_for")
    adjusted = (adjusted,) if isinstance(adjusted, str) else tuple(adjusted or ())
    condition = answers.get("condition")
    reference = answers.get("reference")
    unit_of_test = answers.get("unit_of_test")
    confidence = {
        "condition": "high" if condition else "low",
        "replicate_unit": "high" if rep else "low",
        "reference": "high" if reference is not None else "low",
        "unit_of_test": "high" if unit_of_test else "low",
        "batch": "high" if batch_answered else "low",
        "analyst_adjusted_for": "high" if adjusted_answered else "low",
    }
    unresolved = [role for role, captured in (
        ("condition", bool(condition)), ("replicate_unit", bool(rep)),
        ("reference", reference is not None), ("unit_of_test", bool(unit_of_test)),
        ("batch", batch_answered),
        ("analyst_adjusted_for", adjusted_answered),
    ) if not captured]
    return Roles(
        analysis_type=answers["analysis_type"],
        condition=condition,
        replicate_unit=(rep,) if rep else (),
        batch=batch,
        analyst_adjusted_for=adjusted if adjusted_answered else None,
        reference=reference,
        unit_of_test=unit_of_test,
        type_confidence="high",
        type_evidence=("human ratified the setup form",),
        plain_summary="The experimental design was reviewed and confirmed by a person.",
        confidence=confidence,
        unresolved=tuple(unresolved),
    )


def _normalize_form_answers(answers) -> dict:
    """Translate explicit UI states into the existing exact-or-unresolved role contract."""
    normalized = dict(answers)

    invalid_bindings = [
        role for role in _CORRECTABLE_BINDING_ROLES
        if normalized.get(role) in _MAPPING_SENTINELS
    ]
    if invalid_bindings:
        raise ValueError(
            "Referee cannot run with an unresolved design mapping: "
            + ", ".join(sorted(invalid_bindings))
        )

    batch_status = normalized.pop("batch_status", None)
    if batch_status == "none_recorded":
        normalized.pop("batch", None)
        normalized["batch_answered"] = "1"
    elif batch_status == "recorded":
        if normalized.get("batch"):
            normalized["batch_answered"] = "1"
        else:
            normalized.pop("batch_answered", None)
    elif batch_status == "not_sure":
        normalized.pop("batch", None)
        normalized.pop("batch_answered", None)
    elif "batch" in normalized:  # legacy callers/tests with an explicit batch answer
        normalized["batch_answered"] = "1"

    adjustment_status = normalized.pop("adjustment_status", None)
    if adjustment_status == "none":
        normalized.pop("analyst_adjusted_for", None)
        normalized["analyst_adjusted_for_answered"] = "1"
    elif adjustment_status == "selected":
        if normalized.get("analyst_adjusted_for"):
            normalized["analyst_adjusted_for_answered"] = "1"
        else:
            normalized.pop("analyst_adjusted_for_answered", None)
    elif adjustment_status == "not_sure":
        normalized.pop("analyst_adjusted_for", None)
        normalized.pop("analyst_adjusted_for_answered", None)

    return normalized


def answers_to_config(answers, observations, code_signals=None, reported=None,
                      proposed_config=None) -> dict:
    """Turn the human's answers into a `confirmed_by_human: true` config, re-synthesized from the
    roles so the derived fields (model, target_coefficient, sample_unit) stay consistent. Answering
    the questions IS the ratification."""
    from sc_referee.init import synthesize_config

    answers = _normalize_form_answers(answers)
    config = synthesize_config(_roles_from_answers(answers), observations, code_signals or {}, reported)
    test = answers.get("test")
    if test and len(config.get("contrasts") or []) > 1:
        chosen = [c for c in config["contrasts"] if c.get("test") == test]
        if chosen:
            config["contrasts"] = chosen
    config["confirmed_by_human"] = True
    if config.get("contrasts"):
        proposed_contrast = ((proposed_config or {}).get("contrasts") or [{}])[0]
        config["contrasts"][0]["estimand_id"] = (
            proposed_contrast.get("estimand_id") or "condition-effect/v1"
        )
    if (proposed_config or {}).get("claims"):
        from copy import deepcopy

        claims = deepcopy(proposed_config["claims"])
        old_contrast = (((proposed_config or {}).get("contrasts") or [{}])[0].get("name"))
        new_contrast = ((config.get("contrasts") or [{}])[0].get("name"))
        for claim in claims:
            if old_contrast and new_contrast and claim.get("contrast") == old_contrast:
                claim["contrast"] = new_contrast
        config["claims"] = claims
    _ratify_batch_modeling(config, answers, observations, proposed_config=proposed_config)
    _ratify_csp(config, answers, observations, proposed_config=proposed_config)
    return config


def _ratify_csp(config, answers, observations, *, proposed_config=None) -> None:
    _ratify_between_group_csp(
        config, answers, observations, proposed_config=proposed_config)
    _ratify_target_population_csp(
        config, answers, observations, proposed_config=proposed_config)
    _ratify_contamination_csp(
        config, answers, observations, proposed_config=proposed_config)


def _ratify_contamination_csp(
    config, answers, observations, *, proposed_config=None
) -> None:
    """Persist an exact field-by-field ceremony; proposal guesses never become values."""
    from datetime import datetime, timezone
    import hashlib

    from sc_referee.csp import (
        CspContractRecord, CspFieldRecord, CspFieldState, CspScope,
        component_identities_for,
    )
    from sc_referee.csp_contracts.contamination_basis_obligation_v1 import (
        CAUSAL_FIELDS, MANIFEST, MEASUREMENT_FIELDS,
    )

    proposals = [item for item in ((proposed_config or {}).get("csp_proposals") or [])
                 if item.get("contract_type") == MANIFEST.contract_type]
    if not proposals or not config.get("contrasts"):
        return
    contrast = config["contrasts"][0]
    now = datetime.now(timezone.utc).isoformat()
    records = []
    for proposal in proposals:
        released_values = {}
        fields = {}
        authority = answers.get("csp.contamination.authority_attested") == "yes"
        all_confirmed = authority
        for field_id in MANIFEST.required_fields:
            section = "measurement" if field_id in MEASUREMENT_FIELDS else "causal"
            prefix = f"csp.contamination.{section}.{field_id}"
            answer = answers.get(prefix, "not_sure")
            evidence = answers.get(prefix + ".evidence")
            teach_back = answers.get(prefix + ".teach_back")
            consequence = answers.get(prefix + ".consequence") == "yes"
            supplied_value = answers.get(prefix + ".value")
            confirmed = (
                authority and answer == "yes" and bool(evidence)
                and teach_back == MANIFEST.teach_back_ids[field_id]
                and consequence and supplied_value is not None
            )
            benign = field_id in {
                "non_descendancy", "outside_estimand_pathway", "required_adjustment"
            } and answer == "no"
            state = ("confirmed_high" if confirmed else
                     "declined_for_consumer" if benign else "unresolved")
            value = supplied_value if confirmed else None
            released_values[field_id] = value
            fields[field_id] = {
                "field_id": field_id, "value": value, "state": state,
                "confidence": "high" if confirmed else "low",
                "evidence_ids": [evidence] if evidence else [],
                "evidence_basis": "human_reviewed_field_evidence" if evidence else None,
                "selected_teach_back_id": teach_back if teach_back != "not_sure" else None,
                "consequence_acknowledged": consequence,
                "presentation_event_id": None, "answer_event_id": None,
                "confirmation_event_id": None,
                "actor": "self-attested scientific interpreter" if authority else None,
                "confirmed_at": now if confirmed else None,
            }
            all_confirmed = all_confirmed and confirmed

        # Exact scope comes only from human-supplied structured values, never from the guess.
        axis = released_values.get("axis_identity") or {}
        rows = released_values.get("rows_and_aggregation") or {}
        basis = released_values.get("basis_identity") or {}
        causal_scope = released_values.get("causal_scope_authority") or {}
        if all_confirmed:
            try:
                scope = CspScope(
                    fitted_result_id=causal_scope["fitted_result_id"],
                    contrast_name=contrast["name"],
                    target_coefficient=causal_scope["target_coefficient"],
                    exposure_column=causal_scope["exposure_column"],
                    row_ledger_identity=causal_scope["row_ledger_identity"],
                    estimand_id=causal_scope["estimand_id"],
                    group_source_column=proposal["source_mapping_fields"][0],
                    assignment_identity=(released_values["assignment_context"]
                                         ["assignment_identity"]),
                    contract_scope={
                        "measurement_artifact_identity": axis["artifact_id"],
                        "measurement_run_identity": axis["run_id"],
                        "raw_source_ledger_identity": rows["input_row_ledger_identity"],
                        "measurement_vector_ledger_identity": rows["output_row_ledger_identity"],
                        "transformed_basis_ledger_identity": basis["basis_ledger_identity"],
                        "basis_output_digest": basis["output_digest"],
                        "fitted_design_identity": causal_scope["fitted_design_identity"],
                    },
                )
            except (KeyError, TypeError, ValueError):
                all_confirmed = False
        if not all_confirmed:
            # Keep an auditable, non-authorizing record on the proposal's exact display scope.
            scope = CspScope(
                fitted_result_id=proposal["fitted_result_id"],
                contrast_name=contrast["name"],
                target_coefficient=proposal["target_coefficient"],
                exposure_column=proposal["exposure_column"],
                row_ledger_identity=proposal["row_ledger_identity"],
                estimand_id=proposal["estimand_id"],
                group_source_column=proposal["source_mapping_fields"][0],
                assignment_identity="proposal:" + hashlib.sha256(
                    repr(sorted(proposal.items())).encode("utf-8")
                ).hexdigest(),
                contract_scope={
                    "measurement_artifact_identity": proposal["artifact_identity"],
                    "measurement_run_identity": "unresolved:measurement-run",
                    "raw_source_ledger_identity": "unresolved:raw-source",
                    "measurement_vector_ledger_identity": "unresolved:vector-ledger",
                    "transformed_basis_ledger_identity": "unresolved:basis-ledger",
                    "basis_output_digest": "unresolved:basis-output",
                    "fitted_design_identity": proposal["fitted_design_identity"],
                },
            )
        for field_id, field in fields.items():
            token = hashlib.sha256(
                f"{scope.fingerprint}:{field_id}:{now}".encode("utf-8")
            ).hexdigest()[:16]
            field["scope_fingerprint"] = scope.fingerprint
            field["presentation_event_id"] = f"present-{token}"
            field["answer_event_id"] = f"answer-{token}"
            if field["state"] == "confirmed_high":
                field["confirmation_event_id"] = f"confirm-{token}"

        record_id = "csp-" + hashlib.sha256(
            (scope.fingerprint + MANIFEST.contract_type).encode("utf-8")
        ).hexdigest()[:20]
        component_identities = {}
        validator_result = list(MANIFEST.validate_values(released_values))
        if all_confirmed and not validator_result:
            typed_fields = {
                field_id: CspFieldRecord(
                    field_id=field_id, value=field["value"],
                    state=CspFieldState(field["state"]), confidence=field["confidence"],
                    scope_fingerprint=field["scope_fingerprint"],
                    evidence_ids=tuple(field["evidence_ids"]),
                    evidence_basis=field["evidence_basis"],
                    selected_teach_back_id=field["selected_teach_back_id"],
                    consequence_acknowledged=field["consequence_acknowledged"],
                    confirmation_event_id=field["confirmation_event_id"], actor=field["actor"],
                    confirmed_at=field["confirmed_at"],
                    presentation_event_id=field["presentation_event_id"],
                    answer_event_id=field["answer_event_id"],
                ) for field_id, field in fields.items()
            }
            typed_record = CspContractRecord(
                contract_id=record_id, contract_type=MANIFEST.contract_type, scope=scope,
                fields=typed_fields, authorized_consumers=(MANIFEST.authorized_consumer,),
                authority_attested=True, authority_attestation=MANIFEST.authority_attestation,
                validator_version=MANIFEST.validator_version, validator_result=(), active=True,
                created_at=now,
            )
            component_identities = dict(component_identities_for(typed_record, MANIFEST))
        records.append({
            "contract_id": record_id, "contract_type": MANIFEST.contract_type,
            "scope": {
                "fitted_result_id": scope.fitted_result_id,
                "contrast_name": scope.contrast_name,
                "target_coefficient": scope.target_coefficient,
                "exposure_column": scope.exposure_column,
                "row_ledger_identity": scope.row_ledger_identity,
                "estimand_id": scope.estimand_id,
                "group_source_column": scope.group_source_column,
                "assignment_identity": scope.assignment_identity,
                "contract_scope": dict(scope.contract_scope),
                "scope_fingerprint": scope.fingerprint,
            },
            "fields": fields, "component_identities": component_identities,
            "authorized_consumers": [MANIFEST.authorized_consumer],
            "authority_attested": authority,
            "authority_attestation": MANIFEST.authority_attestation if authority else None,
            "validator_version": MANIFEST.validator_version,
            "validator_result": validator_result,
            "active": True, "created_at": now,
        })
    contrast.setdefault("csp_contracts", []).extend(records)


def _ratify_between_group_csp(config, answers, observations, *, proposed_config=None) -> None:
    """Persist field-level answers; only the deterministic CSP reader derives authority."""
    from datetime import datetime, timezone
    import hashlib
    import tempfile
    from pathlib import Path

    import yaml

    from sc_referee.config import load_designs
    from sc_referee.csp_contracts.between_group_adjustment_obligation_v1 import (
        AUTHORITY_ATTESTATION, AUTHORIZED_CONSUMER, CONTRACT_TYPE, validate_values,
    )

    proposals = [item for item in ((proposed_config or {}).get("csp_proposals") or [])
                 if item.get("contract_type") == CONTRACT_TYPE]
    if not proposals or not config.get("contrasts"):
        return
    # Load the already-bound batch ledger so CSP scope uses the identical canonical rows.
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "sc-referee.yaml"
        path.write_text(yaml.safe_dump(config))
        design = load_designs(path)[0]
    contrast = config["contrasts"][0]
    records = []
    now = datetime.now(timezone.utc).isoformat()
    for proposal in proposals:
        group = proposal["group_source_column"]
        entry = (design.fitted_design.batch_modeling.get(group)
                 if design.fitted_design is not None else None)
        if entry is None or not entry.row_ledger_identity:
            continue
        from sc_referee.csp import CspScope, assignment_identity
        from sc_referee.engine import build_pseudobulk_sample_rows
        exposure, _, _ = design.contrast_column_and_levels()
        fitted_rows = build_pseudobulk_sample_rows(observations, design)
        scope = CspScope(
            fitted_result_id=entry.component_scope.fitted_result_id,
            contrast_name=design.name,
            target_coefficient=design.target_coefficient,
            exposure_column=exposure,
            row_ledger_identity=entry.row_ledger_identity,
            estimand_id=design.estimand_id,
            group_source_column=group,
            assignment_identity=assignment_identity(fitted_rows.rows, exposure, group),
        )
        prefix = f"csp.{group}."
        policy_answer = answers.get(prefix + "between_group_policy", "not_sure")
        teach_answer = answers.get(prefix + "may_rely_on_re_exogeneity", "not_sure")
        authority = answers.get(prefix + "authority_attested") == "yes"
        consequence = answers.get(prefix + "consequence_acknowledged") == "yes"
        evidence = tuple(proposal.get("evidence_locations") or ())
        ceremony = authority and consequence and bool(evidence)

        def field(field_id, answer, value, correct_id, *, declined=False):
            confirmed = ceremony and answer == correct_id
            if confirmed:
                state, confidence = "confirmed_high", "high"
            elif declined:
                state, confidence = "declined_for_consumer", "low"
            else:
                state, confidence = "unresolved", "low"
            token = hashlib.sha256(
                f"{scope.fingerprint}:{field_id}:{now}".encode("utf-8")
            ).hexdigest()[:16]
            return {
                "field_id": field_id, "value": value, "state": state,
                "confidence": confidence, "scope_fingerprint": scope.fingerprint,
                "evidence_ids": list(evidence),
                "evidence_basis": "human_reviewed_analysis" if evidence else None,
                "selected_teach_back_id": answer if answer != "not_sure" else None,
                "consequence_acknowledged": consequence,
                "presentation_event_id": f"present-{token}",
                "answer_event_id": f"answer-{token}",
                "confirmation_event_id": f"confirm-{token}" if confirmed else None,
                "actor": "self-attested scientific interpreter" if authority else None,
                "confirmed_at": now if confirmed else None,
            }

        policy_value = "remove_arbitrary" if policy_answer == "remove_arbitrary" else None
        teach_value = (False if teach_answer == "must_not_rely"
                       else True if teach_answer in (
                           "may_rely", "sensitivity_at_tolerance_is_sufficient"
                       ) else None)
        fields = {
            "between_group_policy": field(
                "between_group_policy", policy_answer, policy_value, "remove_arbitrary"
            ),
            "may_rely_on_re_exogeneity": field(
                "may_rely_on_re_exogeneity", teach_answer, teach_value, "must_not_rely",
                declined=teach_answer in (
                    "may_rely", "sensitivity_at_tolerance_is_sufficient"
                ),
            ),
        }
        values = {key: item["value"] for key, item in fields.items()}
        record_id = "csp-" + hashlib.sha256(
            (scope.fingerprint + CONTRACT_TYPE).encode("utf-8")
        ).hexdigest()[:20]
        records.append({
            "contract_id": record_id, "contract_type": CONTRACT_TYPE,
            "scope": {
                "fitted_result_id": scope.fitted_result_id,
                "contrast_name": scope.contrast_name,
                "target_coefficient": scope.target_coefficient,
                "exposure_column": scope.exposure_column,
                "row_ledger_identity": scope.row_ledger_identity,
                "estimand_id": scope.estimand_id,
                "group_source_column": scope.group_source_column,
                "assignment_identity": scope.assignment_identity,
                "scope_fingerprint": scope.fingerprint,
            },
            "fields": fields, "authorized_consumers": [AUTHORIZED_CONSUMER],
            "authority_attested": authority,
            "authority_attestation": AUTHORITY_ATTESTATION if authority else None,
            "validator_version": "between-group-obligation-v1",
            "validator_result": list(validate_values(values)),
            "active": True, "created_at": now,
        })
    if records:
        contrast.setdefault("csp_contracts", []).extend(records)


def _ratify_target_population_csp(
    config, answers, observations, *, proposed_config=None
) -> None:
    """Project exact-version target fields without performing target arithmetic."""
    from datetime import datetime, timezone
    import hashlib
    import tempfile
    from pathlib import Path

    import yaml

    from sc_referee.config import load_designs
    from sc_referee.csp import CspScope, assignment_identity
    from sc_referee.csp_contracts.target_population_estimand_v1 import MANIFEST
    from sc_referee.engine import build_pseudobulk_sample_rows

    proposals = [item for item in ((proposed_config or {}).get("csp_proposals") or [])
                 if item.get("contract_type") == MANIFEST.contract_type]
    if not proposals or not config.get("contrasts"):
        return

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "sc-referee.yaml"
        path.write_text(yaml.safe_dump(config))
        design = load_designs(path)[0]
    entries = list((design.fitted_design.batch_modeling.values()
                    if design.fitted_design is not None else ()))
    if not entries or not entries[0].row_ledger_identity:
        config.setdefault("unresolved", []).append("csp_proposals")
        return
    entry = entries[0]
    fitted_rows = build_pseudobulk_sample_rows(observations, design)
    exposure, _, _ = design.contrast_column_and_levels()
    identity_rows = fitted_rows.rows.copy()
    identity_rows["__not_applicable__"] = "__not_applicable__"
    contrast = config["contrasts"][0]
    now = datetime.now(timezone.utc).isoformat()

    def candidate_values(proposal):
        return {
            "functional": proposal.get("functional_candidate"),
            "reported_scalar_id": proposal.get("reported_scalar_id"),
            "target_population_id": proposal.get("target_population_id"),
            "census_stratum_columns": tuple(proposal.get("census_stratum_columns", ())),
            "evaluation_stratum_columns": tuple(proposal.get("evaluation_stratum_columns", ())),
            "stratum_levels": tuple(tuple(level) if isinstance(level, (list, tuple)) else level
                                    for level in proposal.get("stratum_levels", ())),
            "stratum_ledger_identity": proposal.get("stratum_ledger_identity"),
            "census_artifact_identity": proposal.get("census_artifact_identity"),
            "census_count_ledger_identity": proposal.get("census_count_ledger_identity"),
            "census_total_n": proposal.get("census_total_n"),
            "census_stratum_counts": tuple(proposal.get("census_stratum_counts", ())),
            "weight_vector_identity": proposal.get("weight_vector_identity"),
            "weight_vector": tuple(tuple(pair) if isinstance(pair, (list, tuple)) else pair
                                   for pair in proposal.get("weight_vector", ())),
            "support_policy": proposal.get("support_policy_candidate"),
        }

    records = []
    for proposal in proposals:
        values = candidate_values(proposal)
        invalid = tuple(MANIFEST.validate_values(values))
        evaluation_columns = values["evaluation_stratum_columns"]
        if invalid or any(column not in observations.columns for column in evaluation_columns):
            if "csp_proposals" not in config.setdefault("unresolved", []):
                config["unresolved"].append("csp_proposals")
            continue
        contract_scope = {
            key: values[field_id]
            for key, field_id in MANIFEST.scope_field_bindings.items()
        }
        scope = CspScope(
            fitted_result_id=entry.component_scope.fitted_result_id,
            contrast_name=design.name,
            target_coefficient=design.target_coefficient,
            exposure_column=exposure,
            row_ledger_identity=entry.row_ledger_identity,
            estimand_id=design.estimand_id,
            group_source_column="__not_applicable__",
            assignment_identity=assignment_identity(
                identity_rows, exposure, "__not_applicable__"),
            contract_scope=contract_scope,
        )
        prefix = "csp.target_population."
        authority = answers.get(prefix + "authority_attested") == "yes"
        consequence = answers.get(prefix + "consequence_acknowledged") == "yes"
        evidence = tuple(proposal.get("evidence_locations") or ())
        ceremony = authority and consequence and bool(evidence)
        fields = {}
        for field_id in MANIFEST.required_fields:
            answer = answers.get(prefix + field_id, "not_sure")
            expected = MANIFEST.teach_back_ids[field_id]
            confirmed = ceremony and answer == expected
            declined = answer not in ("not_sure", expected)
            state = ("confirmed_high" if confirmed else
                     "declined_for_consumer" if declined else "unresolved")
            token = hashlib.sha256(
                f"{scope.fingerprint}:{field_id}:{now}".encode("utf-8")
            ).hexdigest()[:16]
            fields[field_id] = {
                "field_id": field_id,
                "value": values[field_id] if confirmed else None,
                "state": state,
                "confidence": "high" if confirmed else "low",
                "scope_fingerprint": scope.fingerprint,
                "evidence_ids": list(evidence),
                "evidence_basis": "human_reviewed_target_population" if evidence else None,
                "selected_teach_back_id": answer if answer != "not_sure" else None,
                "consequence_acknowledged": consequence,
                "presentation_event_id": f"present-{token}",
                "answer_event_id": f"answer-{token}",
                "confirmation_event_id": f"confirm-{token}" if confirmed else None,
                "actor": "self-attested scientific interpreter" if authority else None,
                "confirmed_at": now if confirmed else None,
            }
        released_values = {key: field["value"] for key, field in fields.items()}
        record_id = "csp-" + hashlib.sha256(
            (scope.fingerprint + MANIFEST.contract_type).encode("utf-8")
        ).hexdigest()[:20]
        records.append({
            "contract_id": record_id,
            "contract_type": MANIFEST.contract_type,
            "scope": {
                "fitted_result_id": scope.fitted_result_id,
                "contrast_name": scope.contrast_name,
                "target_coefficient": scope.target_coefficient,
                "exposure_column": scope.exposure_column,
                "row_ledger_identity": scope.row_ledger_identity,
                "estimand_id": scope.estimand_id,
                "group_source_column": scope.group_source_column,
                "assignment_identity": scope.assignment_identity,
                "contract_scope": dict(scope.contract_scope),
                "scope_fingerprint": scope.fingerprint,
            },
            "fields": fields,
            "authorized_consumers": [MANIFEST.authorized_consumer],
            "authority_attested": authority,
            "authority_attestation": MANIFEST.authority_attestation if authority else None,
            "validator_version": MANIFEST.validator_version,
            "validator_result": list(MANIFEST.validate_values(released_values)),
            "active": True,
            "created_at": now,
        })
    if records:
        contrast.setdefault("csp_contracts", []).extend(records)


def _ratify_batch_modeling(config, answers, observations, *, proposed_config=None) -> None:
    """Project only complete explicit answers, then bind their canonical fitted-row digest."""
    from sc_referee.config import load_designs
    from sc_referee.engine import build_pseudobulk_sample_rows
    import tempfile
    from pathlib import Path
    import yaml

    contrasts = config.get("contrasts") or []
    if not contrasts:
        return
    contrast = contrasts[0]
    batches = list((config.get("design") or {}).get("batch") or [])
    semantic = ("modeled_as", "random_group_column", "fixed_source_columns", "rows_exact",
                "contrast_name", "target_coefficient", "fitted_result_id", "unsupported_components")
    unresolved = config.setdefault("unresolved", [])
    entries = {}
    proposals = {
        item.get("source_column"): item
        for item in ((proposed_config or {}).get("batch_modeling") or [])
        if isinstance(item, dict)
    }
    aggregation = answers.get("aggregation_key")
    aggregation = [aggregation] if isinstance(aggregation, str) else list(aggregation or [])
    for batch in batches:
        prefix = f"batch_modeling.{batch}."
        normalized_answers = dict(answers)
        for name in ("fixed_source_columns", "unsupported_components"):
            key = prefix + name
            if key not in normalized_answers and normalized_answers.get(key + "_answered"):
                normalized_answers[key] = []
        missing = [prefix + name for name in semantic if prefix + name not in normalized_answers]
        if not aggregation:
            missing.append("aggregation_key")
        if missing:
            for name in missing:
                if name not in unresolved:
                    unresolved.append(name)
            continue
        entries[batch] = {
            "source_column": batch,
            "modeled_as": normalized_answers[prefix + "modeled_as"],
            "random_group_column": normalized_answers[prefix + "random_group_column"] or None,
            "fixed_source_columns": list(normalized_answers[prefix + "fixed_source_columns"] or []),
            "rows_exact": normalized_answers[prefix + "rows_exact"] == "yes",
            "row_ledger_identity": None,
            "component_scope": {
                "contrast_name": normalized_answers[prefix + "contrast_name"],
                "target_coefficient": normalized_answers[prefix + "target_coefficient"],
                "fitted_result_id": normalized_answers[prefix + "fitted_result_id"],
            },
            "unsupported_components": list(normalized_answers[prefix + "unsupported_components"] or []),
            "field_confidence": {
                "source_column": "high", "modeled_as": "high", "random_group_column": "high",
                "fixed_source_columns": "high", "rows_exact": "high",
                "row_ledger_identity": "low", "component_scope": "high",
                "unsupported_components": "high",
            },
            "evidence_locations": dict(proposals.get(batch, {}).get("evidence_locations") or {}),
        }
    if aggregation:
        contrast["aggregation_key"] = aggregation
    else:
        # The closed schema represents an unknown aggregation key by absence, not YAML null.
        # Keeping a stale proposed value would be equally unsafe after the reviewer leaves it blank.
        contrast.pop("aggregation_key", None)
    config.setdefault("confidence", {})["aggregation_key"] = "high" if aggregation else "low"
    kinds = {str(column): ("continuous" if observations[column].dtype.kind in "iufc" else "categorical")
             for column in observations.columns}
    levels = {column: list(observations[column].dropna().unique())
              for column, kind in kinds.items() if kind == "categorical"}
    unsupported_operator = any(
        entry["unsupported_components"] for entry in entries.values()
    )
    operator_kind = (
        "unsupported" if unsupported_operator else
        "ordinary_fixed_effects" if any(
            entry["modeled_as"] in ("fixed", "fixed_and_random_intercept")
            for entry in entries.values()
        ) else "random_intercept_only"
    )
    contrast["fitted_design"] = {
        "rows_exact": True,
        "operator_kind": operator_kind,
        "intercept": True, "column_kinds": kinds, "categorical_levels": levels,
        "transforms": {column: "identity" for column in kinds}, "batch_modeling": entries,
    }
    if unsupported_operator:
        contrast["fitted_design"]["unsupported_reason"] = (
            "unsupported_nonadditive_operator"
        )
    config.setdefault("confidence", {})["fitted_design"] = "high" if entries else "low"
    if not entries:
        return
    # Load the same closed config shape the audit will consume; this is deterministic and does not
    # inspect model/formula text. The temporary file is only a schema/constructor adapter.
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "sc-referee.yaml"
        path.write_text(yaml.safe_dump(config))
        design = load_designs(path)[0]
    rows = build_pseudobulk_sample_rows(observations, design)
    if not rows.exact:
        for entry in entries.values():
            entry["rows_exact"] = False
            entry["field_confidence"]["row_ledger_identity"] = "low"
        return
    for entry in entries.values():
        if entry["rows_exact"]:
            entry["row_ledger_identity"] = rows.row_ledger_identity
            entry["field_confidence"]["row_ledger_identity"] = "high"


# Precision-instrument aesthetic — the wizard shares the results page's system: a
# light-first datasheet where you "configure the instrument before a run". Each design role is a
# parameter row (mono key + human prompt + why + input). Self-contained + offline.
_CSS = """
:root{color-scheme:light dark;
 --paper:#f4f5f3;--ink:#191b1f;--mut:#5f6670;--dim:#626a74;--rule:#dcdfd9;--rule2:#c3c7c0;--accent:#9a6b00;
 --field:#fbfbfa;
 --mono:"JetBrains Mono","SFMono-Regular","Cascadia Code",ui-monospace,Menlo,Consolas,monospace;
 --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
@media(prefers-color-scheme:dark){:root{
 --paper:#111317;--ink:#e7e9ec;--mut:#aeb4bd;--dim:#a2a9b3;--rule:#2a2e35;--rule2:#3a3f47;--accent:#e0b654;
 --field:#191c22}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;
 line-height:1.55;-webkit-font-smoothing:antialiased}
main{max-width:800px;margin:0 auto;padding:0 24px 72px}
header{display:flex;align-items:baseline;justify-content:space-between;gap:16px;
 padding:22px 0 11px;border-bottom:1px solid var(--rule2)}
.brand{font-family:var(--mono);font-size:12px;letter-spacing:.24em;text-transform:uppercase;color:var(--mut)}
.brand b{color:var(--ink);font-weight:600}
.hlabel{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
.intro{color:var(--mut);font-size:14px;margin:18px 0 4px;line-height:1.5;max-width:62ch}
.claim-summary{margin:38px 0 8px;padding:0 0 25px;border-bottom:1px solid var(--rule2)}
.claim-label{font-family:var(--mono);font-size:10.5px;letter-spacing:.15em;text-transform:uppercase;
 color:var(--dim);margin-bottom:9px}.claim-title{font-size:clamp(30px,5vw,43px);line-height:1.05;
 letter-spacing:-.035em;font-weight:650}
.claim-facts{display:flex;flex-wrap:wrap;gap:9px 24px;margin-top:17px;font-family:var(--mono);
 font-size:11.5px;color:var(--mut)}.claim-facts b{font-weight:500;color:var(--ink)}
.claim-fact{white-space:nowrap}.fact-label{color:var(--mut)}.claim-facts b.caution{color:var(--accent)}
.claim-facts em{font-style:normal;color:var(--accent);font-size:10px;letter-spacing:.06em;
 text-transform:uppercase;margin-left:5px}
.section{margin-top:36px}
.section+.section{margin-top:46px;padding-top:4px}
.section-kicker{font-family:var(--mono);font-size:10.5px;letter-spacing:.15em;text-transform:uppercase;
 color:var(--dim);margin-bottom:5px}
.section h1{font-size:24px;line-height:1.2;letter-spacing:-.025em;margin:0 0 7px;font-weight:650}
.section-note{color:var(--mut);font-size:13.5px;line-height:1.48;margin:0 0 18px;max-width:60ch}
.param{padding:18px 0;border-top:1px solid var(--rule);display:grid;
 grid-template-columns:minmax(0,1fr) minmax(250px,310px);gap:30px;align-items:start}
.param:first-of-type{border-top:none}
.p-head{display:flex;align-items:baseline;gap:10px;margin-bottom:6px}
.p-key{font-family:var(--mono);font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:var(--dim)}
.p-req{font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
.p-found{font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;
 color:var(--mut)}
.p-prompt{display:block;font-size:15px;font-weight:550;color:var(--ink);margin:0 0 3px;line-height:1.42}
.p-why{color:var(--mut);font-size:12.5px;margin:0;line-height:1.45;max-width:48ch}
.role-unit_of_test .p-key,.role-unit_of_test .p-found{color:var(--accent)}
.param-control{padding-top:2px}
/* inputs read as clearly editable (faint fill + inset) — a non-CLI user must see these are fields */
select,input[type=text]{font-family:var(--mono);font-size:13px;color:var(--ink);background:var(--field);
 padding:10px 11px;width:100%;min-width:0;max-width:100%;border:1px solid var(--rule2);border-radius:2px;
 box-shadow:inset 0 1px 2px rgba(0,0,0,.05);transition:border-color .12s,box-shadow .12s}
select:hover,input[type=text]:hover{border-color:var(--mut)}
select:focus,input[type=text]:focus{outline:none;border-color:var(--ink);
 box-shadow:0 0 0 3px color-mix(in srgb,var(--ink) 14%,transparent)}
select:user-invalid,input[type=text]:user-invalid{border-color:var(--accent);
 box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 16%,transparent)}
.mapping-recovery{margin-top:10px;padding:12px 14px;background:color-mix(in srgb,var(--accent) 9%,var(--paper));
 border:1px solid color-mix(in srgb,var(--accent) 45%,var(--rule));font-size:12.5px;line-height:1.45}
.mapping-recovery strong{display:block;color:var(--ink);margin-bottom:3px}.mapping-recovery span{color:var(--mut)}
.mapping-recovery .not-listed-copy,.mapping-recovery .not-sure-copy{display:none}
.mapping-recovery[data-state="__not_listed__"] .not-listed-copy,
.mapping-recovery[data-state="__not_sure__"] .not-sure-copy{display:block}
.checks{display:flex;flex-wrap:wrap;gap:9px 20px}
.checks label,.radios label{font-family:var(--mono);font-size:13px;display:inline-flex;align-items:center;
 gap:7px;color:var(--ink);cursor:pointer}
.radios{display:flex;gap:12px 22px;flex-wrap:wrap}
input[type=checkbox],input[type=radio]{accent-color:var(--ink);width:15px;height:15px;flex:none}
.choice-stack{display:flex;flex-direction:column;gap:9px}.choice{display:flex;align-items:flex-start;gap:8px;
 font-family:var(--mono);font-size:12.5px;line-height:1.4;cursor:pointer}.choice input{margin-top:2px}
.subchoices{margin:5px 0 0 23px;padding:11px 13px;background:var(--field);border:1px solid var(--rule)}
.subchoices>span{display:block;font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;
 text-transform:uppercase;color:var(--dim);margin-bottom:8px}.empty-options{margin:4px 0 0 23px;
 color:var(--mut);font-size:12.5px;line-height:1.4}
.more-columns{margin:6px 0 0 23px}
.more-columns summary{cursor:pointer;list-style:none;font-family:var(--mono);font-size:11.5px;
 color:var(--mut);padding:5px 0}.more-columns summary::-webkit-details-marker{display:none}
.more-columns summary::after{content:" +";color:var(--dim);letter-spacing:.04em}
.more-columns[open] summary::after{content:" −"}.more-columns .checks{margin:7px 0 3px}
.design-details{margin-top:18px;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.design-details summary{cursor:pointer;list-style:none;padding:14px 0;font-family:var(--mono);font-size:12px;
 color:var(--ink);display:flex;align-items:center;justify-content:space-between;gap:18px}
.design-details summary::-webkit-details-marker{display:none}.design-details summary::after{content:"Review details  +";
 color:var(--dim);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase}
.design-details[open] summary::after{content:"Hide details  −"}.design-details .details-body{padding-bottom:4px}
.run{margin-top:38px;font-family:var(--mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;
 color:var(--paper);background:var(--ink);border:none;border-radius:2px;padding:14px 22px;cursor:pointer;
 transition:background-color 160ms ease-out,color 160ms ease-out,transform 120ms ease-out}
.run:hover{background:var(--accent)}.run:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
.run:active{transform:translateY(1px)}
.run:disabled{background:var(--rule2);color:var(--mut);cursor:not-allowed;transform:none}
@media(max-width:650px){main{padding-left:20px;padding-right:20px}.param{grid-template-columns:1fr;gap:12px}
 .claim-summary{margin-top:30px}.section{margin-top:31px}.param-control{padding-top:0}
 .design-details summary::after{content:"+"}.design-details[open] summary::after{content:"−"}}
@media(prefers-reduced-motion:reduce){.run{transition:none}}
"""


_READBACK_ROLES = frozenset({
    "analysis_type", "condition", "reference", "test", "replicate_unit",
    "analyst_adjusted_for", "unit_of_test",
})

_MAPPING_SENTINELS = frozenset({"__not_listed__", "__not_sure__"})
_CORRECTABLE_BINDING_ROLES = frozenset({"analysis_type", "condition", "replicate_unit"})


def _is_readback(q) -> bool:
    """A confident, populated proposal is shown as an editable read-back, not a cold question.

    Required means the proposal is unresolved/low-confidence, so it stays in the human-input section
    even when a tentative default exists. Batch is deliberately excluded: an unrecorded processing
    schedule is the canonical fact only the experimenter may know.
    """
    return q.role in _READBACK_ROLES and q.default is not None and not q.required


def _option_label(value) -> str:
    labels = {
        "condition_contrast_DE": "Differential expression",
        "marker_detection": "Marker detection",
        "cell": "Individual cells",
        "sample": "Biological samples",
    }
    return labels.get(str(value), str(value))


def _field(q, *, readback=False, readback_label="proposed", confirmed=False) -> str:
    """One design role as an instrument parameter row: mono key + human prompt + why + input."""
    # A required core role is unresolved or low-confidence. Show the guess in the prose if useful,
    # but require an active choice instead of silently laundering it through a preselected input.
    default = (None if q.required and q.role in _READBACK_ROLES else q.default)
    req = '<span class="p-req">· needs your answer</span>' if q.required else ''
    found = (f'<span class="p-found">· {_html.escape(readback_label)}</span>' if readback else '')
    reqattr = " required" if q.required else ""
    head = (f'<div class="p-head"><span class="p-key">{_html.escape(q.role.replace("_", " "))}</span>'
            f'{found}{req}</div>'
            f'<span class="p-prompt">{_html.escape(q.prompt)}</span>'
            f'<div class="p-why">{_html.escape(q.why)}</div>')
    if q.role == "batch":
        status = "recorded" if default else ("none_recorded" if confirmed else "not_sure")
        status_options = (
            ("none_recorded", "No technical batch column is recorded"),
            ("recorded", "The metadata records technical batches"),
            ("not_sure", "Not sure — leave batch confounding unevaluated"),
        )
        status_radios = "".join(
            f'<label class="choice"><input type="radio" name="batch_status" value="{value}"'
            f'{" checked" if value == status else ""}> <span>{label}</span></label>'
            for value, label in status_options
        )
        boxes = "".join(
            f'<label><input type="checkbox" name="batch" value="{_html.escape(str(o))}"'
            f'{" checked" if o in (default or ()) else ""}> {_html.escape(str(o))}</label>'
            for o in q.options
        )
        candidates = (f'<div class="subchoices"><span>Recorded batch columns</span>'
                      f'<div class="checks">{boxes}</div></div>' if boxes else
                      '<div class="empty-options">No likely technical batch columns were found.</div>')
        # F1 escape hatch: reveal every remaining metadata column so an unconventionally-named
        # technical batch column stays selectable. Native <details> — keyboard- and SR-accessible.
        more_boxes = "".join(
            f'<label><input type="checkbox" name="batch" value="{_html.escape(str(o))}"'
            f'{" checked" if o in (default or ()) else ""}> {_html.escape(str(o))}</label>'
            for o in q.more_options
        )
        more = (f'<details class="more-columns"'
                f'{" open" if any(o in (default or ()) for o in q.more_options) else ""}>'
                '<summary>A different column records batch…</summary>'
                f'<div class="checks">{more_boxes}</div></details>' if more_boxes else "")
        inp = f'<div class="choice-stack">{status_radios}{candidates}{more}</div>'
    elif q.role == "analyst_adjusted_for":
        status = "selected" if default else ("none" if default is not None else "not_sure")
        status_options = (
            ("none", "No additional covariates"),
            ("selected", "The model included additional covariates"),
            ("not_sure", "Not sure — leave this model detail unresolved"),
        )
        status_radios = "".join(
            f'<label class="choice"><input type="radio" name="adjustment_status" value="{value}"'
            f'{" checked" if value == status else ""}> <span>{label}</span></label>'
            for value, label in status_options
        )
        boxes = "".join(
            f'<label><input type="checkbox" name="analyst_adjusted_for" '
            f'value="{_html.escape(str(o))}"'
            f'{" checked" if o in (default or ()) else ""}> {_html.escape(str(o))}</label>'
            for o in q.options
        )
        candidates = (f'<div class="subchoices"><span>Additional covariates</span>'
                      f'<div class="checks">{boxes}</div></div>' if boxes else
                      '<div class="empty-options">No additional candidate covariates were found.</div>')
        inp = f'<div class="choice-stack">{status_radios}{candidates}</div>'
    elif q.kind in ("column", "choice"):
        opts = "".join(
            f'<option value="{_html.escape(str(o))}"'
            f'{" selected" if o == default else ""}>{_html.escape(_option_label(o))}</option>'
            for o in q.options)
        if q.role in _CORRECTABLE_BINDING_ROLES:
            opts += ('<option value="__not_listed__">Correct value isn’t listed</option>'
                     '<option value="__not_sure__">Not sure</option>')
        blank = "" if default else '<option value="" selected disabled>choose…</option>'
        recovery = (f'<div class="mapping-recovery" data-mapping-recovery="{q.role}" hidden>'
                    '<strong>Referee cannot safely use this mapping.</strong>'
                    '<span class="not-listed-copy">The correct value is not available in the loaded '
                    'analysis table. Add it to the supplied metadata or choose a different analysis '
                    'folder, then restart. Referee will not guess.</span>'
                    '<span class="not-sure-copy">This role is required to bind the scientific design. '
                    'The review will remain stopped until it can be established.</span></div>'
                    if q.role in _CORRECTABLE_BINDING_ROLES else "")
        inp = (f'<select name="{q.role}" data-binding-role="{q.role}"{reqattr}>'
               f'{blank}{opts}</select>{recovery}')
    elif q.kind == "columns":
        boxes = "".join(
            f'<label><input type="checkbox" name="{q.role}" value="{_html.escape(str(o))}"'
            f'{" checked" if o in (default or ()) else ""}> {_html.escape(str(o))}</label>'
            for o in q.options)
        answered = (f'<input type="hidden" name="{q.role}_answered" value="1">'
                    if q.role.startswith("batch_modeling.")
                    else "")
        inp = f'{answered}<div class="checks">{boxes}</div>'
    elif q.kind in ("radio", "csp_semantic", "csp_ceremony"):
        labels = {
            "not_sure": "Not sure — leave this check not checked",
            "remove_arbitrary": "Yes — arbitrary group differences must be removed",
            "must_not_rely": "No — the result may not rely on unrelated group baselines",
            "may_rely": "I'm comfortable assuming baselines are unrelated to condition",
            "yes": "Yes",
        }
        radios = "".join(
            f'<label><input type="radio" name="{q.role}" value="{o}"'
            f'{" checked" if o == default else ""}{reqattr}> '
            f'{_html.escape(labels.get(str(o), _option_label(o)))}</label>'
            for o in q.options)
        inp = f'<div class="radios">{radios}</div>'
    else:
        val = "" if default is None else _html.escape(str(default))
        inp = f'<input type="text" name="{q.role}" value="{val}"{reqattr}>'
    role_class = "role-" + re.sub(r"[^a-zA-Z0-9_-]", "-", q.role)
    return (f'<div class="param {role_class}"><div class="param-copy">{head}</div>'
            f'<div class="param-control">{inp}</div></div>')


def _claim_summary(questions, claim: ReviewClaim | None = None) -> str:
    if claim is not None:
        facts = []
        for fact in claim.facts:
            caution = " class='caution'" if fact.caution else ""
            facts.append(
                '<span class="claim-fact"><span class="fact-label">'
                f'{_html.escape(str(fact.label))}:</span> '
                f'<b{caution}>{_html.escape(str(fact.value))}</b></span>'
            )
        return (
            "<section class='claim-summary'><div class='claim-label'>"
            f"{_html.escape(str(claim.label))}</div>"
            f"<div class='claim-title'>{_html.escape(str(claim.title))}</div>"
            f"<div class='claim-facts'>{''.join(facts)}</div></section>"
        )
    by_role = {q.role: q for q in questions}
    reference = getattr(by_role.get("reference"), "default", None)
    test = getattr(by_role.get("test"), "default", None)
    replicate = getattr(by_role.get("replicate_unit"), "default", None)
    condition = getattr(by_role.get("condition"), "default", None)
    unit = getattr(by_role.get("unit_of_test"), "default", None)
    analysis_type = getattr(by_role.get("analysis_type"), "default", None)
    if reference is None or test is None:
        return ""
    facts = []
    if condition:
        facts.append('<span class="claim-fact"><span class="fact-label">Comparison column:</span> '
                     f'<b data-summary-condition>{_html.escape(str(condition))}</b></span>')
    if replicate:
        facts.append('<span class="claim-fact"><span class="fact-label">Biological replicate:</span> '
                     f'<b data-summary-replicate>{_html.escape(str(replicate))}</b></span>')
    if unit:
        unit_text = "individual cells" if unit == "cell" else "biological samples"
        caution = " class='caution'" if unit == "cell" else ""
        review = '<em>· review</em>' if unit == "cell" else ""
        facts.append(f'<span class="claim-fact"><span class="fact-label">Reported test unit:</span> '
                     f'<b{caution} data-summary-unit>{unit_text}</b>'
                     f'<em data-summary-unit-review{"" if review else " hidden"}>· review</em></span>')
    claim_label = ("Differential expression under review"
                   if analysis_type == "condition_contrast_DE" else "Scientific claim under review")
    return (f"<section class='claim-summary'><div class='claim-label' data-summary-analysis>"
            f"{claim_label}</div><div class='claim-title'><span data-summary-test>"
            f"{_html.escape(str(test))}</span> vs. "
            f"<span data-summary-reference>{_html.escape(str(reference))}</span></div>"
            f"<div class='claim-facts'>{''.join(facts)}</div></section>")


def render_form(questions, *, claim: ReviewClaim | None = None,
                reconstruction: str | None = None) -> str:
    """A self-contained, offline HTML page in the precision-instrument aesthetic — one
    parameter row per Question, prefilled with the tool's guesses, required roles marked."""
    questions = list(questions)
    source = next((q.proposal_source for q in questions if q.proposal_source), None)
    confirmed_mode = source == "confirmed_config"
    source_intro = {
        "claude": ("Claude inspected the supplied folder and prepared a scientific design for "
                   "your review."),
        "hard_signals": ("Referee found an unambiguous design in the supplied metadata and code "
                         "without needing a model."),
        "heuristic_no_llm": ("Claude was not available for this run. Referee prepared a cautious "
                             "draft from the metadata and code; uncertain items remain below."),
        "confirmed_config": ("This folder already contains a human-confirmed design. Referee loaded "
                             "it unchanged for this review."),
    }.get(source, "I inspected the analysis folder and prepared a design for review.")
    readbacks = [q for q in questions if _is_readback(q) or (
        confirmed_mode and q.role == "batch" and q.default is not None and not q.required
    )]
    asks = [q for q in questions if q not in readbacks]
    sections = []
    if reconstruction and not readbacks:
        sections.append(
            "<section class='section readback'><div class='section-kicker'>What Referee found</div>"
            "<h1>Review my read of your analysis</h1>"
            f"<p class='section-note'>{_html.escape(reconstruction)}</p></section>"
        )
    if readbacks:
        if confirmed_mode:
            detail_fields = "".join(
                _field(q, readback=True, readback_label="previously confirmed", confirmed=True)
                for q in readbacks
            )
            sections.append(
                "<section class='section readback'><div class='section-kicker'>Confirmed design</div>"
                "<h1>Ready to review again</h1>"
                "<p class='section-note'>Run the audit with the design summarized above, or open the "
                "details to review and change the previous confirmation.</p>"
                "<details class='design-details'><summary>Previously confirmed design</summary>"
                f"<div class='details-body'>{detail_fields}</div></details></section>"
            )
        else:
            sections.append(
                "<section class='section readback'><div class='section-kicker'>What Referee found</div>"
                "<h1>Review my read of your analysis</h1>"
                "<p class='section-note'>These answers came from the supplied data, results, or code. "
                "They are editable — correct anything I misunderstood.</p>" +
                "".join(_field(q, readback=True, readback_label="proposed")
                        for q in readbacks) + "</section>"
            )
    if asks:
        sections.append(
            "<section class='section'><div class='section-kicker'>Scientific context</div>"
            "<h1>What the folder cannot establish</h1>"
            "<p class='section-note'>These details are not recoverable from the supplied files. "
            "Answer what you know; “Not sure” leaves the affected check explicitly unevaluated.</p>" +
            "".join(_field(q) for q in asks) + "</section>"
        )
    fields = "".join(sections)
    action = ("Run review with this design" if confirmed_mode else
              "Confirm design and run review")
    intro_suffix = (" Run it as confirmed, or review the design details before continuing."
                    if confirmed_mode else
                    " Confirm the interpretation below before Referee recomputes the result.")
    default_action = action + "  →"
    change_script = (
        "<script>const form=document.querySelector('form');const run=document.querySelector('.run');"
        f"const confirmed={str(confirmed_mode).lower()};const defaultAction={default_action!r};"
        "let dirty=false;const selects=[...form.querySelectorAll('[data-binding-role]')];"
        "const field=name=>form.querySelector('[name=\"'+name+'\"]');"
        "const clean=value=>(value==='__not_listed__'||value==='__not_sure__')?'unresolved':value;"
        "const put=(selector,value)=>{const node=document.querySelector(selector);if(node)node.textContent=value;};"
        "const updateSummary=()=>{const analysis=field('analysis_type');if(analysis){const value=clean(analysis.value);"
        "put('[data-summary-analysis]',value==='unresolved'?'Analysis mapping unresolved':"
        "analysis.options[analysis.selectedIndex].text+' under review');}"
        "const condition=field('condition');if(condition)put('[data-summary-condition]',clean(condition.value));"
        "const replicate=field('replicate_unit');if(replicate)put('[data-summary-replicate]',clean(replicate.value));"
        "const reference=field('reference');if(reference)put('[data-summary-reference]',reference.value||'unresolved');"
        "const test=field('test');if(test)put('[data-summary-test]',test.value||'unresolved');"
        "const unit=form.querySelector('[name=\"unit_of_test\"]:checked');const unitNode=document.querySelector("
        "'[data-summary-unit]');const review=document.querySelector('[data-summary-unit-review]');if(unit&&unitNode){"
        "const isCell=unit.value==='cell';unitNode.textContent=isCell?'individual cells':'biological samples';"
        "unitNode.classList.toggle('caution',isCell);if(review)review.hidden=!isCell;}};"
        "const sync=()=>{let blocked=false;selects.forEach(select=>{const panel=form.querySelector("
        "'[data-mapping-recovery=\"'+select.dataset.bindingRole+'\"]');const value=select.value;"
        "const unresolved=value==='__not_listed__'||value==='__not_sure__';"
        # A non-correctable column/choice select (e.g. a batch_modeling.* ceremony field) carries
        # data-binding-role but has NO mapping-recovery panel; guard the null so sync() never throws.
        "if(panel){panel.hidden=!unresolved;panel.dataset.state=unresolved?value:'';}"
        "blocked=blocked||unresolved;});run.disabled=blocked;"
        "run.textContent=blocked?'Resolve mapping before review':"
        "(confirmed&&dirty?'Save changes and run review  →':defaultAction);updateSummary();};"
        "form.addEventListener('change',()=>{dirty=true;sync();});form.addEventListener('input',()=>{dirty=true;sync();});"
        "sync();</script>"
    )
    return ("<!doctype html>\n<html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>sc-referee — set up</title>"
            f"<style>{_CSS}</style></head><body><main>"
            "<header><span class='brand'>sc<b>·</b>referee</span>"
            "<span class='hlabel'>set up · design</span></header>"
            f"<p class='intro'>{_html.escape(source_intro + intro_suffix)}</p>"
            f"{_claim_summary(questions, claim)}"
            f"<form method='post' action='submit'>{fields}"
            f"<button class='run' type='submit'>{action}&nbsp; →</button></form>"
            f"{change_script}</main></body></html>\n")


def _confirm_page(*, workload: str | None = None, estimate: str | None = None,
                  poll: bool = False) -> str:
    """Immediate, honest handoff from ratification to computation.

    There is no invented percentage: without engine progress events, an indeterminate readout plus a
    workload-derived time range is more trustworthy. The unified friendly app polls real completion
    state and replaces this page with the report; the legacy wizard still opens its report separately.
    """
    workload_line = (_html.escape(workload) if workload else "the supplied count matrix")
    estimate_line = (_html.escape(estimate) if estimate else
                     "Most reviews finish within a minute; large matrices can take several minutes.")
    script = ("<script>const check=async()=>{try{const r=await fetch('/status',{cache:'no-store'});"
              "const s=await r.json();if(s.stage==='done'){location.replace('/report');return;}"
              "if(s.stage==='error'){location.replace('/error');return;}}catch(e){}"
              "setTimeout(check,700)};check();</script>" if poll else "")
    return ("<!doctype html>\n<html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>sc-referee — running</title>"
            f"<style>{_CSS}"
            ".done{padding-top:0}.run-state{padding:76px 0 38px;border-bottom:1px solid var(--rule2)}"
            ".run-kicker{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;"
            "color:var(--accent);margin-bottom:14px}.done h1{font-size:clamp(34px,6vw,52px);line-height:1;"
            "letter-spacing:-.04em;font-weight:650;margin:0 0 20px;max-width:11ch}"
            ".done .lede{font-size:17px;line-height:1.55;color:var(--mut);max-width:51ch;margin:0}"
            ".work{font-family:var(--mono);font-size:12px;color:var(--ink);margin-top:24px}"
            ".estimate{font-size:13px;color:var(--mut);margin:7px 0 0}.track{height:2px;background:var(--rule);"
            "overflow:hidden;margin-top:32px}.runner{height:100%;width:34%;background:var(--accent)}"
            ".run-facts{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;padding:25px 0}"
            ".run-fact b{display:block;font-family:var(--mono);font-size:10px;letter-spacing:.12em;"
            "text-transform:uppercase;color:var(--dim);margin-bottom:7px}.run-fact span{font-size:13px;"
            "line-height:1.5;color:var(--mut)}@media(prefers-reduced-motion:no-preference){.runner{"
            "animation:scan 1.6s cubic-bezier(.45,0,.55,1) infinite alternate}@keyframes scan{from{"
            "transform:translateX(-100%)}to{transform:translateX(294%)}}}"
            "@media(max-width:620px){.run-state{padding-top:48px}.run-facts{grid-template-columns:1fr;gap:17px}}"
            "</style></head><body><main class='done'>"
            "<header><span class='brand'>sc<b>·</b>referee</span><span class='hlabel'>audit running</span></header>"
            "<section class='run-state'><div class='run-kicker'>Design confirmed</div>"
            "<h1>Recomputing the evidence.</h1>"
            "<p class='lede'>Referee is testing the reported result at the biological replicate level. "
            "This page will become the finished report automatically.</p>"
            f"<div class='work'>{workload_line}</div><p class='estimate'>{estimate_line}</p>"
            "<div class='track' role='progressbar' aria-label='Audit in progress'><div class='runner'></div></div>"
            "</section><section class='run-facts'>"
            "<div class='run-fact'><b>Now</b><span>Aggregate counts and fit the corrected model.</span></div>"
            "<div class='run-fact'><b>Then</b><span>Check confounding, multiplicity, effect size, and pairing.</span></div>"
            "<div class='run-fact'><b>Verdict</b><span>Arithmetic decides. Claude does not score the result.</span></div>"
            f"</section></main>{script}</body></html>\n")


def serve_wizard(questions, *, browser_open=webbrowser.open, host="127.0.0.1", port=0) -> dict:
    """Serve the form on a localhost ephemeral port, open the browser, block until the human submits,
    return the parsed answers, then shut the server down. Localhost-bound, single-submission."""
    result: dict = {}
    done = threading.Event()
    page = render_form(questions).encode()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):        # keep the terminal quiet
            pass

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page)

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
            parsed = urllib.parse.parse_qs(body, keep_blank_values=True)
            # single-value fields collapse to a string; multi-value (checkbox columns) stay lists
            result.update({k: (v if len(v) > 1 else v[0]) for k, v in parsed.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(_confirm_page().encode())
            done.set()

    server = HTTPServer((host, port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    browser_open(f"http://{host}:{server.server_port}/")
    done.wait()
    server.shutdown()
    return result


SUPPORTED_TYPES = ("condition_contrast_DE", "marker_detection")


def _existing_confirmed_config(folder) -> dict | None:
    from pathlib import Path

    import yaml

    path = Path(folder) / "sc-referee.yaml"
    if not path.is_file():
        return None
    try:
        config = yaml.safe_load(path.read_text())
    except (OSError, UnicodeError, yaml.YAMLError):
        return None
    return config if isinstance(config, dict) and config.get("confirmed_by_human") is True else None


def _reported_for_folder(config, folder) -> dict | None:
    """Keep a report binding portable when a proposer returned an absolute discovery path."""
    from pathlib import Path

    reported = dict(config.get("reported_results") or {})
    raw_path = reported.get("path")
    if not raw_path:
        return reported or None
    path, root = Path(raw_path), Path(folder).resolve()
    if path.is_absolute():
        try:
            reported["path"] = str(path.resolve().relative_to(root))
        except ValueError:
            pass
    return reported


def run_wizard(folder, *, propose=None, serve=serve_wizard, analysis_types=SUPPORTED_TYPES):
    """Ingest the folder, propose a design, ask the questions, and write a `confirmed_by_human: true`
    sc-referee.yaml. Returns its path, or None if the human cancelled (submitted nothing)."""
    from pathlib import Path

    import yaml

    from sc_referee.ingest import ingest

    if propose is None:
        from sc_referee import init as _init
        propose = _init.propose
        existing = _existing_confirmed_config(folder)
        config, source = ((existing, "confirmed_config") if existing is not None
                          else propose(folder))
    else:
        config, source = propose(folder)

    folder = Path(folder)
    bundle = ingest(folder)
    columns = list(bundle.observations.columns)
    questions = design_questions(config, columns, analysis_types=analysis_types)
    if questions:
        from dataclasses import replace
        questions[0] = replace(questions[0], proposal_source=source)

    answers = serve(questions)
    if not answers:
        return None                                   # cancelled: write nothing

    confirmed = answers_to_config(answers, bundle.observations,
                                  code_signals=getattr(bundle, "code_signals", {}),
                                  reported=_reported_for_folder(config, folder),
                                  proposed_config=config)
    out = folder / "sc-referee.yaml"
    out.write_text(yaml.safe_dump(confirmed, sort_keys=False))
    return out
