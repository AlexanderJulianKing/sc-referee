"""`init` — Claude proposes, a person confirms. (spec §[2]+[3], C7)

Shape of the trust:

  1. A DETERMINISTIC hard-signal pre-classifier runs FIRST. When the folder is unambiguous
     (exactly one column matches each role, cardinalities in range) it emits the proposal and
     Claude is never called. Cheap, reproducible, offline.
  2. Claude is invoked ONLY where the deterministic classifier cannot resolve a role — which
     is exactly where a name-matching regex would guess *wrong* rather than abstain. `group`
     is deliberately not a condition token: a regex cannot know whether it means condition,
     cluster, or batch, but Claude can reason across columns + cardinalities + parsed code.
  3. Claude's answer is REQUIRED to be a single JSON object, validated against
     sc_referee.schema.json. Prose is rejected. A schema violation is an error, not a guess.
  4. The result is written with `confirmed_by_human: false`. NOTHING can be blocked until a
     person ratifies it. The model never renders a verdict; it only ever drafts a proposal.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import jsonschema
import yaml

from sc_referee import synonyms
from sc_referee.code_signals import parse_code_signals, resolve_unit_of_test
from sc_referee.design import model_terms
from sc_referee.ingest import ingest
from sc_referee.roles import Roles
from sc_referee.schema_validation import validate

DEFAULT_MODEL = "claude-opus-4-8"

# Hard signals: case-insensitive SUBSTRING match on column names (unanchored, so
# `culture_condition`->condition, `processing_run`->batch, `donor_id`->replicate all hit).
# `group` is DELIBERATELY absent from CONDITION_TOKENS — see the module docstring.
REPLICATE_TOKENS = ("donor", "subject", "patient", "sample", "mouse", "animal", "individual",
                    "replicate")
CONDITION_TOKENS = ("condition", "treatment", "stim", "geno", "perturb", "status")
BATCH_TOKENS = ("batch", "run", "lane", "chip", "plate", "10x")

REPLICATE_RANGE = (2, 50)
CONDITION_RANGE = (2, 6)

REFERENCE_LEVELS = ("control", "ctrl", "rest", "untreated", "non-targeting", "wt", "vehicle", "dmso")

SYSTEM_PROMPT = """You are helping a non-expert ratify the design of a single-cell analysis.

You are given a deterministic summary of an analysis folder: its observation columns (with
dtypes, cardinalities, null counts and example values), the columns of any reported results
table, and signals parsed (never executed) from the analysis code.

Decide what kind of analysis this is and what the experimental design is. Reason across the
COMBINATION of signals -- column names alone are not enough. In particular, infer which column
is the biological CONDITION being contrasted, which is the biological REPLICATE unit (the
independent experimental unit, e.g. donor/subject/mouse), and which is a technical BATCH.

Rules:
- `unit_of_test` is "cell" if the code tests CELLS as replicates (rank_genes_groups, FindMarkers),
  "sample" if it aggregates to pseudobulk / uses a count model (DESeq2, edgeR, limma-voom).
  A bare `ttest_ind`/`wilcoxon` does NOT settle it -- decide from the surrounding code (was there
  an aggregation step?) and say so in type_evidence. If you truly cannot tell, use null and list
  "unit_of_test" in unresolved. Do not guess.
- `sample_unit` is the pseudobulk aggregation key; `replicate_unit` is what counts as n.
- `analyst_adjusted_for` is the observation-column labels the analyst's fitted model conditioned
  on. Use labels only, never formulas or expressions. If the fitted design is unclear, omit it,
  mark its confidence low, and list `analyst_adjusted_for` in unresolved.
- Set a role's confidence to "low" if you are guessing, and list it in `unresolved`.
- `plain_summary` must be ONE sentence a non-technical PI could ratify or correct.
- `type_evidence` must cite the concrete signals you used.
- `unresolved` lists only the ROLE NAMES you could not settle (its schema enumerates them).
  Never put commentary there. Observations about the analysis go in `type_evidence`.

Call the `propose_design` tool exactly once. Its schema defines every field and type;
`type_evidence` and `unresolved` are ARRAYS of strings, not prose.
analysis_type must be one of: condition_contrast_DE, marker_detection,
differential_abundance, trajectory, other."""

PROPOSAL_TOOL = "propose_design"

# The only values `unresolved` may contain: the ROLES the model actually decides and a human must
# correct before ratifying. Not free-text commentary (that belongs in `type_evidence`), and NOT the
# synthesized fields (`sample_unit`, `pairing_unit`, `test`, `model`, `target_coefficient`) — the
# model neither authors nor resolves those, so they are unrepresentable here. (invariant I1.)
ROLES = ("analysis_type", "condition", "replicate_unit", "batch", "analyst_adjusted_for",
         "reference", "unit_of_test")


# --------------------------------------------------------------------------- #
# the deterministic summary handed to a human (and, only if needed, to Claude)
# --------------------------------------------------------------------------- #
def build_init_input(folder) -> dict:
    return _init_input_from(ingest(Path(folder)), Path(folder))


def _init_input_from(bundle, folder: Path) -> dict:
    obs = bundle.observations

    columns = []
    for name in obs.columns:
        col = obs[name]
        columns.append(dict(
            name=str(name), dtype=str(col.dtype), n_unique=int(col.nunique()),
            n_null=int(col.isna().sum()),
            examples=[str(v) for v in col.dropna().unique()[:5]],
        ))

    return dict(
        columns=columns,
        n_observations=int(len(obs)),
        reported_columns=list(bundle.reported_columns),   # the ORIGINAL header, not our canonical one
        code_signals=bundle.code_signals or parse_code_signals(folder),
        candidate_files={role: meta["path"] for role, meta in bundle.provenance.items()},
    )


def _match_role(columns, tokens, cardinality=None):
    """Exactly one column whose name contains a token (and whose cardinality is in range)."""
    hits = []
    for col in columns:
        low = col["name"].lower()
        if any(tok in low for tok in tokens):
            if cardinality and not (cardinality[0] <= col["n_unique"] <= cardinality[1]):
                continue
            hits.append(col)
    return hits[0] if len(hits) == 1 else None


def _reported_binding(init_input):
    """The reported-results FILE binding — {path, gene_col, padj_col}. `unit_of_test` is added by
    `synthesize_config` (deterministic-wins), not here. None when there is no results table."""
    path = init_input["candidate_files"].get("reported")
    if not path:
        return None
    binding = synonyms.bind_columns(init_input["reported_columns"])
    return dict(path=str(path),
                gene_col=binding["gene"] or "gene",
                padj_col=binding["padj"] or binding["pval"] or "padj")


# --------------------------------------------------------------------------- #
# the three ROLE producers. Each returns `Roles` (or None); `synthesize_config` turns Roles +
# the DATA into the config. NONE of them writes a formula — that is synthesis's sole job. (§4)
# --------------------------------------------------------------------------- #
def hard_signal_proposal(init_input: dict):
    """`Roles`, or None when a role is ambiguous (0 or >1 candidates) — the case that must go to
    Claude. `reference`/`unit_of_test` are left for synthesis to resolve from the data + code."""
    columns = init_input["columns"]
    replicate = _match_role(columns, REPLICATE_TOKENS, REPLICATE_RANGE)
    fm = init_input["code_signals"].get("seurat_findmarkers") or {}
    identity_column = fm.get("identity_column")
    explicit_condition = next((column for column in columns
                               if column["name"] == identity_column), None)
    condition = explicit_condition or _match_role(columns, CONDITION_TOKENS, CONDITION_RANGE)
    if replicate is None or condition is None:
        return None
    batch = _match_role(columns, BATCH_TOKENS)
    det_uot = resolve_unit_of_test(init_input["code_signals"])
    adjusted = (tuple(fm["latent_vars"])
                if fm.get("latent_vars") is not None else None)
    reference = fm.get("ident_2")
    unresolved = []
    if det_uot is None:
        unresolved.append("unit_of_test")
    if adjusted is None:
        unresolved.append("analyst_adjusted_for")
    return Roles(
        analysis_type="condition_contrast_DE",
        condition=condition["name"],
        replicate_unit=(replicate["name"],),
        batch=(batch["name"],) if batch else (),
        analyst_adjusted_for=adjusted,
        reference=reference,
        unit_of_test=det_uot,
        type_confidence="high",
        type_evidence=(f"replicate={replicate['name']}", f"condition={condition['name']}",
                       *([f"FindMarkers ident.2={reference}"] if reference else ()),
                       *([f"batch={batch['name']}"] if batch else ())),
        plain_summary=(f"Looks like a condition contrast: cells from {replicate['n_unique']} "
                       f"{replicate['name']}s compared across {condition['name']}"
                       + (f", processed in {batch['n_unique']} {batch['name']}s." if batch else ".")),
        confidence={"replicate_unit": "high", "condition": "high",
                    "reference": "high" if reference else "low",
                    "analyst_adjusted_for": "high" if adjusted is not None else "low"},
        # An unresolved unit_of_test is NOT a silent skip: audit turns it into `not_audited`.
        unresolved=tuple(unresolved),
    )


def _heuristic_draft(init_input: dict) -> "Roles":
    """No model available: resolve what we can into `Roles`, stamp the rest `low`, and list it. (C7)"""
    columns = init_input["columns"]
    replicate = _match_role(columns, REPLICATE_TOKENS, REPLICATE_RANGE)
    condition = _match_role(columns, CONDITION_TOKENS, CONDITION_RANGE)
    batch = _match_role(columns, BATCH_TOKENS)

    unresolved = [r for r, v in (("replicate_unit", replicate), ("condition", condition)) if v is None]
    unresolved.append("analyst_adjusted_for")

    # Guess the condition by CARDINALITY among columns that are neither the replicate nor the batch.
    # It is a guess: stamped `low` and listed in `unresolved`.
    guess = condition
    if guess is None:
        taken = {c["name"] for c in (replicate, batch) if c}
        candidates = [c for c in columns
                      if c["name"] not in taken and CONDITION_RANGE[0] <= c["n_unique"] <= CONDITION_RANGE[1]]
        guess = candidates[0] if candidates else None

    return Roles(
        analysis_type="condition_contrast_DE",
        condition=guess["name"] if guess else None,
        replicate_unit=(replicate["name"],) if replicate else (),
        batch=(batch["name"],) if batch else (),
        analyst_adjusted_for=None,
        reference=None,
        unit_of_test=resolve_unit_of_test(init_input["code_signals"]),
        type_confidence="low",
        type_evidence=("no ANTHROPIC_API_KEY / no model client — deterministic heuristic only",),
        plain_summary=("Could not resolve the design without a model. Resolved: "
                       + ", ".join(k for k, v in (("replicate", replicate), ("condition", condition),
                                                  ("batch", batch)) if v)
                       + f". Unresolved: {', '.join(unresolved) or 'none'}. Please correct before confirming."),
        confidence={"replicate_unit": "high" if replicate else "low",
                    "condition": "high" if condition else "low",
                    "analyst_adjusted_for": "low"},
        unresolved=tuple(unresolved),
    )


# --------------------------------------------------------------------------- #
# synthesis — deterministic derivation of the config from ROLES + the DATA (§4.3)
# The single writer of every formula. An LLM never authors these fields.
# --------------------------------------------------------------------------- #
def observed_levels(observations, condition) -> list:
    """The condition's levels, read FROM THE DATA — not `examples[:5]`, which silently drops a 6th
    level and one contrast (invariant I5)."""
    if condition is None or condition not in observations.columns:
        return []
    return sorted(str(v) for v in observations[condition].dropna().unique())


def choose_reference(levels, llm_reference):
    """(reference, unresolved). The model's choice is honoured if it names a real level; a
    control-like name resolves deterministically; otherwise we do NOT silently pick `sorted()[0]`
    — a wrong reference flips the sign of every log2FC — we return unresolved=True so a human must
    choose. (§4.4, invariant I6.)"""
    levels = [str(lv) for lv in levels]
    if llm_reference is not None and str(llm_reference) in levels:
        return str(llm_reference), False
    control_like = [lv for lv in levels if lv.lower() in REFERENCE_LEVELS]
    if control_like:
        return control_like[0], False
    return (sorted(levels)[0] if levels else None), True


def synth_model(slice_obs, replicate, condition) -> str:
    """The recompute formula for ONE two-level contrast slice. The replicate term is added ONLY if
    it does not alias the target on THIS slice — reusing `confounding`'s exact R² algebra, so the
    formula synthesis emits and the verdict `confounding` will earn cannot disagree. This forecloses
    the false BLOCKER on a valid unpaired (or per-contrast-unpaired) design. (§4.3, invariant I4.)"""
    replicates = ([replicate] if isinstance(replicate, str)
                  else list(replicate or []))
    if not replicates or any(column not in slice_obs.columns for column in replicates):
        return f"~ {condition}"
    from sc_referee.checks.confounding import ALIAS_TOL, _dummy_block, _r2, _with_intercept

    levels = sorted(str(v) for v in slice_obs[condition].dropna().unique())
    if len(levels) < 2:
        return f"~ {condition}"
    t = (slice_obs[condition].astype(str) == levels[-1]).to_numpy(dtype=float)
    Z = _with_intercept(_dummy_block(slice_obs, replicates), len(slice_obs))
    r2 = _r2(t, Z)
    if r2 is None or r2 >= 1.0 - ALIAS_TOL:       # replicate aliased with condition ⇒ unpaired here
        return f"~ {condition}"
    return f"~ {' + '.join(replicates)} + {condition}"


def analyst_model_from(code_signals) -> str | None:
    """What the analyst ACTUALLY fit, from evidence — or None when unknown. `confounding` reads
    THIS (never the synthesized recompute `model`) to judge omitted-variable bias; None ⇒ it
    abstains (`informational`, never a false `major`). We do not yet parse a formula out of the
    code, so this is None until a parser lands — the safe, honest default. (§4.5.)"""
    return None


def validate_roles(roles: "Roles", observations) -> "Roles":
    """Demote any role naming a column ABSENT from the data to `unresolved` + low confidence, and
    drop it. Never raises (nothing can block regardless) and never retries — abstention is cheaper
    and more honest than discarding an otherwise-good proposal over one phantom field. (§4.6, Q1.)"""
    from dataclasses import replace

    cols = {str(c) for c in observations.columns}
    unresolved = list(dict.fromkeys(roles.unresolved))
    confidence = dict(roles.confidence)

    def _flag(role):
        confidence[role] = "low"
        if role not in unresolved:
            unresolved.append(role)

    condition = roles.condition
    if condition is not None and str(condition) not in cols:
        condition = None
        _flag("condition")
    replicate_unit = tuple(roles.replicate_unit)
    if replicate_unit and any(str(c) not in cols for c in replicate_unit):
        replicate_unit = ()
        _flag("replicate_unit")
    batch = tuple(b for b in roles.batch if str(b) in cols)
    if len(batch) != len(roles.batch):
        _flag("batch")

    analyst_adjusted_for = roles.analyst_adjusted_for
    if analyst_adjusted_for is None:
        _flag("analyst_adjusted_for")
    elif confidence.get("analyst_adjusted_for") != "high":
        analyst_adjusted_for = None
        _flag("analyst_adjusted_for")
    elif any(str(item) not in cols for item in analyst_adjusted_for):
        # G1/G3: one non-column label invalidates the whole set. Never drop-and-narrow.
        analyst_adjusted_for = None
        _flag("analyst_adjusted_for")

    # CSP proposals are atomic evidence envelopes.  A phantom identity invalidates the
    # whole proposal; deterministic code never narrows or repairs it.
    csp_proposals = tuple(roles.csp_proposals)
    def _valid_csp_proposal(item):
        if item.get("contract_type") == "between_group_adjustment_obligation/v1":
            return (set(item) == {"contract_type", "group_source_column", "evidence_locations"}
                    and item.get("group_source_column") in cols
                    and bool(item.get("evidence_locations")))
        if item.get("contract_type") == "contamination_basis_obligation/v1":
            expected = {
                "contract_type", "measurement_kind_candidate", "vector_field",
                "artifact_identity", "source_mapping_fields", "materialized_basis_columns",
                "transform_kind_candidate", "causal_role_guess", "fitted_result_id",
                "target_coefficient", "exposure_column", "estimand_id",
                "row_ledger_identity", "fitted_design_identity", "evidence_locations",
            }
            referenced_columns = (
                [item.get("vector_field"), item.get("exposure_column")]
                + list(item.get("source_mapping_fields") or ())
                + list(item.get("materialized_basis_columns") or ())
            )
            return (
                set(item) == expected
                and bool(item.get("evidence_locations"))
                and all(isinstance(value, str) and value.strip() for value in (
                    item.get("artifact_identity"), item.get("fitted_result_id"),
                    item.get("target_coefficient"), item.get("estimand_id"),
                    item.get("row_ledger_identity"), item.get("fitted_design_identity"),
                ))
                and all(column in cols for column in referenced_columns)
                and len(set(item.get("source_mapping_fields") or ()))
                    == len(item.get("source_mapping_fields") or ())
                and len(set(item.get("materialized_basis_columns") or ()))
                    == len(item.get("materialized_basis_columns") or ())
            )
        if item.get("contract_type") != "target_population_estimand/v1":
            return False
        expected = {
            "contract_type", "reported_scalar_id", "target_population_id",
            "census_stratum_columns", "evaluation_stratum_columns", "stratum_levels",
            "stratum_ledger_identity", "census_artifact_identity",
            "census_count_ledger_identity", "census_total_n", "census_stratum_counts",
            "weight_vector_identity", "weight_vector", "functional_candidate",
            "support_policy_candidate", "evidence_locations",
        }
        if set(item) != expected or not item.get("evidence_locations"):
            return False
        if any(column not in cols for column in item.get("evaluation_stratum_columns", ())):
            return False
        from sc_referee.csp_contracts.target_population_estimand_v1 import validate_values
        values = {
            "functional": item.get("functional_candidate"),
            "reported_scalar_id": item.get("reported_scalar_id"),
            "target_population_id": item.get("target_population_id"),
            "census_stratum_columns": tuple(item.get("census_stratum_columns", ())),
            "evaluation_stratum_columns": tuple(item.get("evaluation_stratum_columns", ())),
            "stratum_levels": tuple(
                tuple(level) if isinstance(level, (list, tuple)) else level
                for level in item.get("stratum_levels", ())
            ),
            "stratum_ledger_identity": item.get("stratum_ledger_identity"),
            "census_artifact_identity": item.get("census_artifact_identity"),
            "census_count_ledger_identity": item.get("census_count_ledger_identity"),
            "census_total_n": item.get("census_total_n"),
            "census_stratum_counts": tuple(item.get("census_stratum_counts", ())),
            "weight_vector_identity": item.get("weight_vector_identity"),
            "weight_vector": tuple(
                tuple(pair) if isinstance(pair, (list, tuple)) else pair
                for pair in item.get("weight_vector", ())
            ),
            "support_policy": item.get("support_policy_candidate"),
        }
        return not validate_values(values)

    if any(not _valid_csp_proposal(item) for item in csp_proposals):
        csp_proposals = ()
        _flag("csp_proposals")

    return replace(roles, condition=condition, replicate_unit=replicate_unit, batch=batch,
                   analyst_adjusted_for=analyst_adjusted_for,
                   csp_proposals=csp_proposals, confidence=confidence,
                   unresolved=tuple(unresolved))


def synthesize_config(roles, observations, code_signals=None, reported=None) -> dict:
    """Derive the full proposal dict from ROLES + the DATA. The ONLY place a formula is written.

    `roles` is a `Roles` (semantic assignments the model is trusted to make); every derived field —
    contrasts, model, target_coefficient, sample_unit, pairing_unit — is computed here, per contrast,
    on the two-level slice the checks will actually evaluate. `reported` is the results-file binding
    ({path, gene_col, padj_col}) from `_reported_binding`; `unit_of_test` is merged in below with the
    deterministic value winning. (design doc §4.3.)"""
    roles = validate_roles(roles, observations)      # phantom columns -> unresolved, not a formula
    condition = roles.condition
    replicates = list(roles.replicate_unit)
    levels = observed_levels(observations, condition)
    reference, ref_unresolved = choose_reference(levels, roles.reference)

    unresolved = list(dict.fromkeys(roles.unresolved))
    confidence = dict(roles.confidence)
    if ref_unresolved:
        if "reference" not in unresolved:
            unresolved.append("reference")
        confidence["reference"] = "low"

    contrasts = []
    for test in [lv for lv in levels if lv != reference]:
        sl = observations[observations[condition].isin([reference, test])] if condition else observations
        model = synth_model(sl, replicates, condition)
        paired = bool(replicates) and all(rep in model_terms(model) for rep in replicates)
        contrasts.append(dict(
            name=f"{test}_vs_{reference}", reference=reference, test=test,
            replicate_unit=list(replicates),
            sample_unit=[*replicates, condition] if replicates else [condition],
            pairing_unit=list(replicates) if paired else [],
            model=model,
            analyst_adjusted_for=(list(roles.analyst_adjusted_for)
                                  if roles.analyst_adjusted_for is not None else None),
            target_coefficient=f"{condition}[T.{test}]",
        ))

    det_uot = resolve_unit_of_test(code_signals) if code_signals else None
    unit_of_test = det_uot if det_uot is not None else roles.unit_of_test    # deterministic wins (§4.4)

    reported_results = None
    if reported or unit_of_test is not None:
        reported_results = dict(reported or {})
        if unit_of_test is not None:
            reported_results["unit_of_test"] = unit_of_test

    return dict(
        analysis_type=roles.analysis_type,
        type_confidence=roles.type_confidence,
        type_evidence=list(roles.type_evidence),
        plain_summary=roles.plain_summary,
        design=dict(replicate_unit=list(replicates),
                    condition=condition, batch=list(roles.batch)),
        contrasts=contrasts,
        reported_results=reported_results,
        confidence=confidence,
        unresolved=unresolved,
        batch_modeling=[dict(item) for item in roles.batch_modeling],
        csp_proposals=[dict(item) for item in roles.csp_proposals],
    )


# --------------------------------------------------------------------------- #
# the Claude proposal — the one load-bearing use of the model
# --------------------------------------------------------------------------- #
_ANALYSIS_TYPES = ["condition_contrast_DE", "marker_detection",
                   "differential_abundance", "trajectory", "other"]


def proposal_tool_schema() -> dict:
    """The Anthropic tool `input_schema` for what the model is trusted to propose: ROLES ONLY.

    Forcing a tool call makes the proposal WELL-TYPED AT THE API BOUNDARY — a constraint, not the
    request "a single JSON object and nothing else" (which returned a bare string, then prose, then
    a prose *formula*; bugs 2–4, 2026-07-08). And the schema deliberately OMITS `model`,
    `target_coefficient`, `sample_unit`, `pairing_unit`, `contrasts`, and `analyst_model`: an LLM
    cannot author what the schema cannot represent. It may propose `analyst_adjusted_for` only as a
    structured list of observation-column labels; the labels are never parsed or evaluated.
    Deterministic code (`synthesize_config`) derives every executable field from the roles and the
    DATA. `confirmed_by_human` is likewise absent — only a human sets it, via `sc-referee confirm`.
    (design doc §4.2, invariant I1.)
    """
    return {
        "type": "object",
        "required": ["analysis_type", "type_confidence", "type_evidence", "plain_summary",
                     "design", "confidence", "unresolved"],
        "properties": {
            "analysis_type": {"type": "string", "enum": _ANALYSIS_TYPES},
            "type_confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "type_evidence": {"type": "array", "items": {"type": "string"}},
            "plain_summary": {"type": "string"},
            "design": {
                "type": "object", "required": ["replicate_unit", "condition", "batch"],
                "properties": {
                    "replicate_unit": {"type": "array", "items": {"type": "string"}},
                    "condition": {"type": ["string", "null"]},
                    "batch": {"type": "array", "items": {"type": "string"}}}},
            # the reference LEVEL (control arm); a level value, not a column. null ⇒ we abstain (§4.4)
            "reference": {"type": ["string", "null"]},
            "unit_of_test": {"type": ["string", "null"], "enum": ["cell", "sample", None]},
            "analyst_adjusted_for": {"type": "array", "items": {"type": "string"}},
            "batch_modeling": {
                "type": "array",
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["source_column", "modeled_as", "random_group_column",
                                 "fixed_source_columns", "component_scope",
                                 "unsupported_components", "field_confidence",
                                 "evidence_locations"],
                    "properties": {
                        "source_column": {"type": "string"},
                        "modeled_as": {"enum": [
                            "fixed", "random_intercept", "fixed_and_random_intercept",
                            "absent", "upstream_handled", "unsupported",
                        ]},
                        "random_group_column": {"type": ["string", "null"]},
                        "fixed_source_columns": {
                            "type": ["array", "null"], "uniqueItems": True,
                            "items": {"type": "string"},
                        },
                        "component_scope": {
                            "type": "object", "additionalProperties": False,
                            "required": ["contrast_name", "target_coefficient", "fitted_result_id"],
                            "properties": {
                                "contrast_name": {"type": "string"},
                                "target_coefficient": {"type": "string"},
                                "fitted_result_id": {"type": "string"},
                            },
                        },
                        "unsupported_components": {
                            "type": "array", "uniqueItems": True,
                            "items": {"enum": [
                                "random_slope", "correlated_random_effects",
                                "crossed_random_effects", "nested_random_effects",
                                "glmm_integration", "penalty", "weight", "offset",
                                "transform", "upstream_operator", "other",
                            ]},
                        },
                        "field_confidence": {"type": "object"},
                        "evidence_locations": {
                            "type": "object",
                            "additionalProperties": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
            "csp_proposals": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {
                            "type": "object", "additionalProperties": False,
                            "required": ["contract_type", "group_source_column",
                                         "evidence_locations"],
                            "properties": {
                                "contract_type": {
                                    "const": "between_group_adjustment_obligation/v1"},
                                "group_source_column": {"type": "string", "minLength": 1},
                                "evidence_locations": {
                                    "type": "array", "minItems": 1,
                                    "items": {"type": "string", "minLength": 1},
                                },
                            },
                        },
                        {
                            "type": "object", "additionalProperties": False,
                            "required": [
                                "contract_type", "measurement_kind_candidate", "vector_field",
                                "artifact_identity", "source_mapping_fields",
                                "materialized_basis_columns", "transform_kind_candidate",
                                "causal_role_guess", "fitted_result_id", "target_coefficient",
                                "exposure_column", "estimand_id", "row_ledger_identity",
                                "fitted_design_identity", "evidence_locations",
                            ],
                            "properties": {
                                "contract_type": {
                                    "const": "contamination_basis_obligation/v1"},
                                "measurement_kind_candidate": {"enum": [
                                    "external_measurement_artifact",
                                    "orthogonal_origin_artifact",
                                    "expression_proxy_with_positive_nonexpression",
                                ]},
                                "vector_field": {"type": "string", "minLength": 1},
                                "artifact_identity": {"type": "string", "minLength": 1},
                                "source_mapping_fields": {
                                    "type": "array", "minItems": 1, "uniqueItems": True,
                                    "items": {"type": "string", "minLength": 1}},
                                "materialized_basis_columns": {
                                    "type": "array", "minItems": 1, "uniqueItems": True,
                                    "items": {"type": "string", "minLength": 1}},
                                "transform_kind_candidate": {"enum": [
                                    "continuous_identity", "binary_threshold",
                                    "frozen_external_basis",
                                ]},
                                "causal_role_guess": {
                                    "description": (
                                        "Display-only causal-role guess; never a confirmation "
                                        "or verdict premise."
                                    ),
                                    "enum": [
                                        "pre_exposure_nuisance", "descendant_or_pathway",
                                        "chance_imbalance", "unknown",
                                    ],
                                },
                                "fitted_result_id": {"type": "string", "minLength": 1},
                                "target_coefficient": {"type": "string", "minLength": 1},
                                "exposure_column": {"type": "string", "minLength": 1},
                                "estimand_id": {"type": "string", "minLength": 1},
                                "row_ledger_identity": {"type": "string", "minLength": 1},
                                "fitted_design_identity": {"type": "string", "minLength": 1},
                                "evidence_locations": {
                                    "type": "array", "minItems": 1,
                                    "items": {"type": "string", "minLength": 1}},
                            },
                        },
                        {
                            "type": "object", "additionalProperties": False,
                            "required": [
                                "contract_type", "reported_scalar_id", "target_population_id",
                                "census_stratum_columns", "evaluation_stratum_columns",
                                "stratum_levels", "stratum_ledger_identity",
                                "census_artifact_identity", "census_count_ledger_identity",
                                "census_total_n", "census_stratum_counts",
                                "weight_vector_identity", "weight_vector",
                                "functional_candidate", "support_policy_candidate",
                                "evidence_locations",
                            ],
                            "properties": {
                                "contract_type": {"const": "target_population_estimand/v1"},
                                "reported_scalar_id": {"type": "string", "pattern": "^(?=.+[:#]).+$"},
                                "target_population_id": {
                                    "type": "string", "pattern": "^(?!across the population$).+:.+$"},
                                "census_stratum_columns": {
                                    "type": "array", "minItems": 1, "uniqueItems": True,
                                    "items": {"type": "string", "minLength": 1}},
                                "evaluation_stratum_columns": {
                                    "type": "array", "minItems": 1, "uniqueItems": True,
                                    "items": {"type": "string", "minLength": 1}},
                                "stratum_levels": {
                                    "type": "array", "minItems": 1, "uniqueItems": True,
                                    "items": {"type": "array", "minItems": 1,
                                              "items": {"type": ["string", "number", "boolean", "null"]}}},
                                "stratum_ledger_identity": {"type": "string", "pattern": "^(?=.+[:#]).+$"},
                                "census_artifact_identity": {"type": "string", "pattern": "^(?=.+[:#]).+$"},
                                "census_count_ledger_identity": {"type": "string", "pattern": "^(?=.+[:#]).+$"},
                                "census_total_n": {"type": "integer", "minimum": 1},
                                "census_stratum_counts": {
                                    "type": "array", "items": {"type": "integer", "minimum": 0}},
                                "weight_vector_identity": {"type": "string", "pattern": "^(?=.+[:#]).+$"},
                                "weight_vector": {"type": "array", "items": {
                                    "type": "array", "minItems": 2, "maxItems": 2,
                                    "items": {"type": "integer"}}},
                                "functional_candidate": {"const": "population_average"},
                                "support_policy_candidate": {
                                    "const": "require_observed_evaluation_support"},
                                "evidence_locations": {
                                    "type": "array", "minItems": 1,
                                    "items": {"type": "string", "minLength": 1}},
                            },
                        },
                    ],
                },
            },
            "confidence": {"type": "object"},
            # ROLE NAMES only — never commentary (bug 3). An enum, because a type constraint cannot
            # catch a semantic error.
            "unresolved": {"type": "array", "items": {"type": "string", "enum": [
                *ROLES, "batch_modeling", "csp_proposals"
            ]}},
        },
    }


def _roles_from_payload(payload: dict) -> "Roles":
    """Build `Roles` from a `propose_design` tool payload. The payload is already schema-shaped
    (the API enforces `input_schema`); we validate again for the fake-client path in tests."""
    dsn = payload.get("design") or {}
    proposed_batch = tuple(dict(item) for item in (payload.get("batch_modeling") or ()))
    proposed_csp = tuple(dict(item) for item in (payload.get("csp_proposals") or ()))
    unresolved = list(payload.get("unresolved") or ())
    if "batch_modeling" in payload and not proposed_batch and "batch_modeling" not in unresolved:
        unresolved.append("batch_modeling")
    return Roles(
        analysis_type=payload["analysis_type"],
        condition=dsn.get("condition"),
        replicate_unit=tuple(dsn.get("replicate_unit") or ()),
        batch=tuple(dsn.get("batch") or ()),
        analyst_adjusted_for=(tuple(value)
                              if (value := payload.get("analyst_adjusted_for")) is not None else None),
        reference=payload.get("reference"),
        unit_of_test=payload.get("unit_of_test"),
        type_confidence=payload.get("type_confidence", "low"),
        type_evidence=tuple(payload.get("type_evidence") or ()),
        plain_summary=payload.get("plain_summary", ""),
        confidence=payload.get("confidence") or {},
        unresolved=tuple(unresolved),
        batch_modeling=proposed_batch,
        csp_proposals=proposed_csp,
    )


def _normalize_proposer_enums(payload: dict) -> dict:
    """Fail closed on provider enum drift before validating the tool response.

    The model is still not allowed to change shapes or author new fields. This normalization is
    intentionally limited to enum values, where a conservative value is well-defined: unknown
    analysis types route to no scientific check (``other``), unknown test units stay unresolved,
    and every non-high/low role confidence becomes low.
    """
    normalized = dict(payload)
    unresolved = normalized.get("unresolved")

    if normalized.get("analysis_type") not in _ANALYSIS_TYPES:
        normalized["analysis_type"] = "other"
        if isinstance(unresolved, list) and "analysis_type" not in unresolved:
            unresolved = [*unresolved, "analysis_type"]
    if normalized.get("type_confidence") not in {"high", "medium", "low"}:
        normalized["type_confidence"] = "low"
    if normalized.get("unit_of_test") not in {"cell", "sample", None}:
        normalized["unit_of_test"] = None
        if isinstance(unresolved, list) and "unit_of_test" not in unresolved:
            unresolved = [*unresolved, "unit_of_test"]

    confidence = normalized.get("confidence")
    if isinstance(confidence, dict):
        normalized["confidence"] = {
            role: value if value in {"high", "low"} else "low"
            for role, value in confidence.items()
        }

    if isinstance(unresolved, list):
        # An unknown unresolved-role label means the provider/schema versions disagree. Conservatively
        # leave every model-authored role unresolved; silently dropping the label could enable checks.
        normalized["unresolved"] = (
            list(ROLES) if any(role not in (*ROLES, "batch_modeling") for role in unresolved)
            else list(dict.fromkeys(unresolved))
        )
    return normalized


def claude_proposal(init_input: dict, client, model: str | None = None) -> "Roles":
    model = model or os.environ.get("SC_REFEREE_MODEL", DEFAULT_MODEL)
    # NO `temperature`: the API rejects it for claude-opus-4-8 with
    #   400 invalid_request_error: `temperature` is deprecated for this model.
    # We shipped `temperature=0` for days. Every test passed, because the fake client's
    # `lambda **kw: msg` swallows any kwarg — a mock cannot reject what the real API rejects.
    # Determinism is NOT sourced from temperature anyway: it comes from the human ratifying the
    # proposal, and from the fact that no verdict is ever rendered by the model.
    message = client.messages.create(
        model=model, max_tokens=2000, system=SYSTEM_PROMPT,
        tools=[{"name": PROPOSAL_TOOL,
                "description": "Propose the analysis type and experimental design for a human to ratify.",
                "input_schema": proposal_tool_schema()}],
        tool_choice={"type": "tool", "name": PROPOSAL_TOOL},
        messages=[{"role": "user", "content": json.dumps(init_input, indent=2, default=str)}],
    )
    uses = [b for b in message.content
            if getattr(b, "type", None) == "tool_use" and b.name == PROPOSAL_TOOL]
    if not uses:
        raise ValueError("init: the model did not call `propose_design` (returned prose instead)")
    payload = _normalize_proposer_enums(uses[0].input)
    try:
        jsonschema.validate(payload, proposal_tool_schema())   # the API enforces this; re-check for tests
    except jsonschema.ValidationError as e:
        raise ValueError(f"init: the model's roles proposal failed schema validation: {e.message}") from e
    return _roles_from_payload(payload)


def _default_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    return anthropic.Anthropic()


def propose(folder, client="auto", model: str | None = None):
    """Returns (proposal, source) with source in {hard_signals, claude, heuristic_no_llm}.

    Every producer yields `Roles`; `synthesize_config` turns Roles + the DATA into the config,
    deterministically. There is exactly ONE place a formula is written, and it is not a producer.
    """
    folder = Path(folder)
    bundle = ingest(folder)
    init_input = _init_input_from(bundle, folder)
    obs, cs, reported = bundle.observations, init_input["code_signals"], _reported_binding(init_input)

    roles = hard_signal_proposal(init_input)
    if roles is not None:
        return synthesize_config(roles, obs, cs, reported), "hard_signals"   # Claude never called

    if client == "auto":
        client = _default_client()
    if client is None:
        return synthesize_config(_heuristic_draft(init_input), obs, cs, reported), "heuristic_no_llm"

    return synthesize_config(claude_proposal(init_input, client, model), obs, cs, reported), "claude"


# --------------------------------------------------------------------------- #
# confirm — the safety valve
# --------------------------------------------------------------------------- #
def write_config(proposal: dict, out) -> Path:
    out = Path(out)
    payload = {"analysis_type": proposal["analysis_type"], "confirmed_by_human": False}
    payload.update({k: v for k, v in proposal.items() if k != "analysis_type"})
    validate(payload, "sc_referee.schema.json")
    out.write_text(yaml.safe_dump(payload, sort_keys=False))
    return out


def confirm_config(path) -> Path:
    # NOTE (adversarial-review round-3 #3, deliberately NOT hard-refused): a design's `unresolved` roles are
    # surfaced to the human at `init` ("correct these before confirming"); confirming anyway RATIFIES
    # them, consistent with propose->confirm->decide. A blanket refuse also breaks the common, SAFE
    # case of `unresolved: [unit_of_test]` — the checks that need it simply abstain when it is unset.
    path = Path(path)
    raw = yaml.safe_load(path.read_text())
    raw["confirmed_by_human"] = True
    from sc_referee.config import semantic_digest
    raw["confirmation_digest"] = semantic_digest(raw)
    validate(raw, "sc_referee.schema.json")
    path.write_text(yaml.safe_dump(raw, sort_keys=False))
    return path
