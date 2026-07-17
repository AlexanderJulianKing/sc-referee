"""Claude-backed structural binding proposer for the opt-in compiler path.

The model may organize inventory evidence into the narrow binding destinations below.  It cannot
author proposal identity/proposer metadata, confirm scientific authority, or emit executable code,
CSP state, or a verdict.  Those boundaries are enforced again after the forced tool call.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

import jsonschema
import pandas as pd

from sc_referee.compiler.binding_proposal import (
    BindingConflict,
    BindingProposal,
    ConflictCandidate,
    Destination,
    Evidence,
    Locator,
    Proposer,
    RequestedBinding,
    TOOL_SCHEMA_ID,
    binding_proposal_schema,
    validate_binding_proposal,
)
from sc_referee.compiler.inventory import Inventory
from sc_referee.compiler.table_bindings import table_binding_value_schema


DEFAULT_MODEL = "claude-opus-4-8"
PROPOSAL_TOOL = "propose_compiler_bindings"

# This cycle intentionally targets the released GB-P07-shaped eQTL-contamination workflow.  New
# registered derivations can add destinations in a later additive schema revision.
REQUIRED_DESTINATIONS = (
    Destination("design", "analysis_type"),
    Destination("detector_input", "cell_table"),
    Destination("detector_input", "donor_table"),
    Destination("empty_droplet", "empty_droplet_table"),
    Destination("design", "genotype_column"),
    Destination("design", "target_feature"),
    Destination("reported_claim", "submitted_result_artifact"),
    Destination("reported_claim", "target_coefficient"),
    Destination("fitted_design", "method_evidence_span"),
    Destination("detector_input", "derivation_id"),
)

SYSTEM_PROMPT = """You organize structural compiler bindings from a bounded file inventory.
Call the required tool and emit no prose. Bind only facts grounded in the supplied inventory.
Every candidate needs evidence whose artifact_identity and path exactly match one inventory
artifact. Header locators must name a listed header; documentation spans must be verbatim spans in
the supplied documentation text. A table_cell locator value is canonical compact JSON with exactly
column and zero-based row keys (for example {"column":"g","row":0}); a code_span locator value is
canonical compact JSON with exactly start_line and end_line one-based inclusive keys. The compiler
resolves those locators and mints evidence digests; do not supply a digest. Never guess an
ungroundable value: put its authority.field in
unresolved instead. Retain differing candidates for one destination as a conflict.

For a GB-P07-shaped workflow, represent every table candidate identically as an object containing
artifact_path and a columns object. The cell-table columns object contains cell_id, donor,
total_umi, and hbb; the donor-table columns object contains donor and genotype; the empty-droplet
columns object contains total_umi and may identify an id or barcode column. Do not enumerate gene
panels: the compiler deterministically discovers count columns from the bound tables. A legacy
panel object is accepted only as advisory evidence and is not load-bearing.
Other candidates are scalar strings. analysis_type is eqtl and the only
currently registered derivation is genebench_gbp07_public_estimator/v1. This is structural
organization only: never emit a verdict, status, severity, CSP state, confirmed_by_human, code, or
an authority attestation.
"""


def binding_proposal_tool_schema() -> dict[str, Any]:
    """Return the exact closed input schema for the forced Claude tool call.

    It reuses the packaged contract definitions, but exposes only model-authored structural lists.
    Proposal identity, inventory identity, source artifacts, revision, organizational completeness,
    recovered authorities, and proposer metadata are deliberately absent.
    """
    contract = binding_proposal_schema()
    definitions = json.loads(json.dumps(contract["$defs"]))
    # The inventory currently exposes notebook identity but no notebook-cell content.  Do not ask a
    # model for a locator the proposer cannot ground.
    definitions["locator"]["properties"]["kind"]["enum"] = [
        "header", "table_cell", "code_span", "documentation_span",
    ]
    allowed_destinations = [
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["authority", "field"],
            "properties": {
                "authority": {"const": destination.authority},
                "field": {"const": destination.field},
            },
        }
        for destination in REQUIRED_DESTINATIONS
    ]
    definitions["destination"] = {"oneOf": allowed_destinations}
    # Evidence digests are compiler output, not something an LLM can calculate reliably.  The
    # forced tool call supplies a locator; the compiler resolves that locator against inventoried
    # bytes and mints the digest from the canonical excerpt.
    definitions["evidence"]["required"].remove("evidence_digest")
    definitions["evidence"]["properties"].pop("evidence_digest")

    table_values = {
        ("detector_input", "cell_table"): table_binding_value_schema("cell_table"),
        ("detector_input", "donor_table"): table_binding_value_schema("donor_table"),
        ("empty_droplet", "empty_droplet_table"): table_binding_value_schema(
            "empty_droplet_table"
        ),
    }

    def destination_schema(destination: Destination) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["authority", "field"],
            "properties": {
                "authority": {"const": destination.authority},
                "field": {"const": destination.field},
            },
        }

    base_binding = definitions["binding"]
    binding_variants = []
    for destination in REQUIRED_DESTINATIONS:
        variant = json.loads(json.dumps(base_binding))
        variant["properties"]["destination"] = destination_schema(destination)
        variant["properties"]["candidate_value"] = table_values.get(
            (destination.authority, destination.field),
            {"type": "string", "minLength": 1},
        )
        binding_variants.append(variant)
    definitions["binding"] = {"oneOf": binding_variants}

    base_conflict = definitions["conflict"]
    conflict_variants = []
    for destination in REQUIRED_DESTINATIONS:
        candidate = json.loads(json.dumps(definitions["conflict_candidate"]))
        candidate["properties"]["candidate_value"] = table_values.get(
            (destination.authority, destination.field),
            {"type": "string", "minLength": 1},
        )
        variant = json.loads(json.dumps(base_conflict))
        variant["properties"]["destination"] = destination_schema(destination)
        variant["properties"]["candidates"]["items"] = candidate
        conflict_variants.append(variant)
    definitions["conflict"] = {"oneOf": conflict_variants}
    return {
        "$schema": contract["$schema"],
        "$id": "sc-referee/compiler-binding-proposal-tool/v1",
        "type": "object",
        "additionalProperties": False,
        "required": ["requested_bindings", "conflicts", "unresolved"],
        "properties": {
            "requested_bindings": {
                "type": "array", "items": {"$ref": "#/$defs/binding"},
            },
            "conflicts": {
                "type": "array", "items": {"$ref": "#/$defs/conflict"},
            },
            "unresolved": {
                "type": "array", "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
        },
        "$defs": definitions,
    }


def _default_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    return anthropic.Anthropic()


def _destination_key(destination: Destination) -> str:
    return f"{destination.authority}.{destination.field}"


def _evidence_from_payload(payload: Mapping[str, Any], inventory: Inventory) -> Evidence:
    locator = payload["locator"]
    evidence = Evidence(
        artifact_identity=payload["artifact_identity"],
        path=payload["path"],
        locator=Locator(kind=locator["kind"], value=locator["value"]),
        evidence_digest="sha256:" + "0" * 64,
    )
    return replace(evidence, evidence_digest=_canonical_evidence_digest(evidence, inventory))


def _binding_from_payload(payload: Mapping[str, Any], inventory: Inventory) -> RequestedBinding:
    destination = payload["destination"]
    return RequestedBinding(
        binding_id=payload["binding_id"],
        destination=Destination(destination["authority"], destination["field"]),
        candidate_value=payload["candidate_value"],
        confidence=payload["confidence"],
        evidence=tuple(_evidence_from_payload(item, inventory) for item in payload["evidence"]),
        state=payload["state"],
    )


def _conflict_from_payload(payload: Mapping[str, Any], inventory: Inventory) -> BindingConflict:
    destination = payload["destination"]
    return BindingConflict(
        destination=Destination(destination["authority"], destination["field"]),
        candidates=tuple(ConflictCandidate(
            candidate_value=item["candidate_value"],
            evidence=tuple(_evidence_from_payload(evidence, inventory)
                           for evidence in item["evidence"]),
        ) for item in payload["candidates"]),
        resolution=payload["resolution"],
        load_bearing=payload["load_bearing"],
    )


def _source_artifacts(inventory: Inventory) -> tuple[Mapping[str, str], ...]:
    return tuple({
        "artifact_identity": artifact.artifact_identity,
        "path": artifact.relative_path,
        "kind": artifact.kind,
    } for artifact in inventory.artifacts)


def _read_inventoried_path(inventory: Inventory, evidence: Evidence, artifact) -> Path:
    if inventory.root_path is None:
        raise ValueError("compiler proposer: inventory has no source root for evidence grounding")
    root = Path(inventory.root_path).resolve(strict=True)
    path = root.joinpath(*evidence.path.split("/")).resolve(strict=True)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("compiler proposer: evidence path escapes the inventory root") from exc
    digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != artifact.artifact_identity:
        raise ValueError(
            f"compiler proposer: inventoried artifact changed after inventory: {evidence.path!r}"
        )
    return path


def _structured_locator(locator: Locator, expected_keys: set[str]) -> dict[str, Any]:
    try:
        value = json.loads(locator.value)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"compiler proposer: {locator.kind} locator must be canonical JSON"
        ) from exc
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise ValueError(
            f"compiler proposer: {locator.kind} locator requires exactly "
            f"{sorted(expected_keys)}"
        )
    if locator.value != json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False):
        raise ValueError(f"compiler proposer: {locator.kind} locator is not canonical JSON")
    return value


def _canonical_excerpt(evidence: Evidence, inventory: Inventory, artifact) -> str:
    locator = evidence.locator
    if locator.kind == "header":
        if locator.value not in artifact.columns:
            raise ValueError(
                f"compiler proposer: header evidence {locator.value!r} is not in {evidence.path!r}"
            )
        return locator.value
    if locator.kind == "documentation_span":
        if not artifact.documentation_text or locator.value not in artifact.documentation_text:
            raise ValueError(
                f"compiler proposer: documentation span is not present in {evidence.path!r}"
            )
        return locator.value

    path = _read_inventoried_path(inventory, evidence, artifact)
    if locator.kind == "code_span":
        if artifact.kind not in {"python", "r", "r_markdown"}:
            raise ValueError(
                f"compiler proposer: code-span evidence points to non-code {evidence.path!r}"
            )
        span = _structured_locator(locator, {"end_line", "start_line"})
        start, end = span["start_line"], span["end_line"]
        if (not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int)
                or isinstance(end, bool) or start < 1 or end < start):
            raise ValueError("compiler proposer: code-span line range is invalid")
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        if end > len(lines):
            raise ValueError("compiler proposer: code-span line range is out of bounds")
        return "".join(lines[start - 1:end])
    if locator.kind == "table_cell":
        if artifact.kind != "delimited_table":
            raise ValueError(
                f"compiler proposer: table-cell evidence points to non-table {evidence.path!r}"
            )
        cell = _structured_locator(locator, {"column", "row"})
        column, row = cell["column"], cell["row"]
        if (not isinstance(column, str) or column not in artifact.columns
                or not isinstance(row, int) or isinstance(row, bool) or row < 0):
            raise ValueError("compiler proposer: table-cell locator is invalid")
        separator = "\t" if path.name.removesuffix(".gz").lower().endswith(".tsv") else ","
        frame = pd.read_csv(
            path, sep=separator, dtype=str, keep_default_na=False, nrows=row + 1,
            encoding="utf-8-sig",
        )
        if row >= len(frame):
            raise ValueError("compiler proposer: table-cell row is out of bounds")
        return json.dumps(
            {"column": column, "row": row, "value": str(frame.iloc[row][column])},
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        )
    raise ValueError(f"compiler proposer: unsupported evidence locator {locator.kind!r}")


def _canonical_evidence_digest(evidence: Evidence, inventory: Inventory) -> str:
    by_path = {artifact.relative_path: artifact for artifact in inventory.artifacts}
    artifact = by_path.get(evidence.path)
    if artifact is None or artifact.artifact_identity != evidence.artifact_identity:
        raise ValueError(
            "compiler proposer: evidence does not identify an artifact in the supplied inventory: "
            f"{evidence.path!r}"
        )
    excerpt = _canonical_excerpt(evidence, inventory, artifact)
    payload = json.dumps({
        "artifact_identity": artifact.artifact_identity,
        "locator": {"kind": evidence.locator.kind, "value": evidence.locator.value},
        "excerpt": excerpt,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_evidence_is_in_inventory(evidence: Evidence, inventory: Inventory) -> None:
    by_path = {artifact.relative_path: artifact for artifact in inventory.artifacts}
    artifact = by_path.get(evidence.path)
    if artifact is None or artifact.artifact_identity != evidence.artifact_identity:
        raise ValueError(
            "compiler proposer: evidence does not identify an artifact in the supplied inventory: "
            f"{evidence.path!r}"
        )
    expected_digest = _canonical_evidence_digest(evidence, inventory)
    if evidence.evidence_digest != expected_digest:
        raise ValueError(
            f"compiler proposer: evidence digest does not match grounded excerpt in {evidence.path!r}"
        )


def validate_proposal_grounding(proposal: BindingProposal, inventory: Inventory) -> None:
    """Verify every proposal locator and digest against the current inventoried bytes."""
    if proposal.inventory_identity != inventory.inventory_identity:
        raise ValueError("compiler proposer: proposal belongs to a different inventory")
    for binding in proposal.requested_bindings:
        for evidence in binding.evidence:
            _validate_evidence_is_in_inventory(evidence, inventory)
    for conflict in proposal.conflicts:
        for candidate in conflict.candidates:
            for evidence in candidate.evidence:
                _validate_evidence_is_in_inventory(evidence, inventory)


def _canonical_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _deduplicate_candidates(candidates: list[ConflictCandidate]) -> tuple[ConflictCandidate, ...]:
    by_value: dict[str, ConflictCandidate] = {}
    for candidate in candidates:
        key = _canonical_value(candidate.candidate_value)
        if key not in by_value:
            by_value[key] = candidate
        else:
            existing = by_value[key]
            evidence = tuple(dict.fromkeys((*existing.evidence, *candidate.evidence)))
            by_value[key] = replace(existing, evidence=evidence)
    return tuple(by_value.values())


def _proposal_id(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _merge_proposal(
    inventory: Inventory,
    recovered: BindingProposal,
    tool_payload: Mapping[str, Any],
    model: str,
) -> BindingProposal:
    bindings = [*recovered.requested_bindings]
    bindings.extend(_binding_from_payload(item, inventory)
                    for item in tool_payload["requested_bindings"])
    conflicts = [*recovered.conflicts]
    conflicts.extend(_conflict_from_payload(item, inventory)
                     for item in tool_payload["conflicts"])

    candidates_by_destination: dict[Destination, list[ConflictCandidate]] = {}
    bindings_by_destination: dict[Destination, list[RequestedBinding]] = {}
    for binding in bindings:
        bindings_by_destination.setdefault(binding.destination, []).append(binding)
    for conflict in conflicts:
        candidates_by_destination.setdefault(conflict.destination, []).extend(conflict.candidates)

    retained_bindings: list[RequestedBinding] = []
    retained_conflicts: list[BindingConflict] = []
    all_destinations = dict.fromkeys((*bindings_by_destination, *candidates_by_destination))
    for destination in all_destinations:
        destination_bindings = bindings_by_destination.get(destination, [])
        candidates = candidates_by_destination.get(destination, [])
        candidates.extend(ConflictCandidate(binding.candidate_value, binding.evidence)
                          for binding in destination_bindings)
        distinct = _deduplicate_candidates(candidates)
        if len(distinct) > 1:
            retained_conflicts.append(BindingConflict(
                destination=destination,
                candidates=distinct,
                resolution="unresolved",
                load_bearing=True,
            ))
        elif destination_bindings and destination not in candidates_by_destination:
            # Equal duplicate proposals are one binding, never a last-writer-wins update.
            retained_bindings.append(destination_bindings[0])
        elif len(distinct) == 1:
            # A pre-existing conflict cannot become resolved through model output.
            retained_conflicts.append(BindingConflict(
                destination=destination,
                candidates=distinct,
                resolution="unresolved",
                load_bearing=True,
            ))

    required = set(REQUIRED_DESTINATIONS)
    proposed = {
        binding.destination for binding in retained_bindings if binding.state == "proposed"
    }
    conflict_destinations = {conflict.destination for conflict in retained_conflicts}
    unresolved = list(dict.fromkeys((
        *recovered.unresolved,
        *tool_payload["unresolved"],
        *(_destination_key(binding.destination) for binding in retained_bindings
          if binding.state != "proposed"),
        *(_destination_key(destination) for destination in REQUIRED_DESTINATIONS
          if destination not in proposed or destination in conflict_destinations),
    )))
    fully_resolved = required.issubset(proposed) and not unresolved and not retained_conflicts

    seed = {
        "schema_id": recovered.schema_id,
        "revision": recovered.revision + 1,
        "inventory_identity": inventory.inventory_identity,
        "source_artifacts": list(_source_artifacts(inventory)),
        "recovered_authorities": list(recovered.recovered_authorities),
        "requested_bindings": [
            {
                "binding_id": binding.binding_id,
                "destination": {
                    "authority": binding.destination.authority,
                    "field": binding.destination.field,
                },
                "candidate_value": binding.candidate_value,
            }
            for binding in retained_bindings
        ],
        "conflicts": [
            {"destination": _destination_key(conflict.destination),
             "candidate_values": [candidate.candidate_value for candidate in conflict.candidates]}
            for conflict in retained_conflicts
        ],
        "unresolved": unresolved,
        "model": model,
    }
    proposal = BindingProposal(
        schema_id=recovered.schema_id,
        proposal_id=_proposal_id(seed),
        revision=recovered.revision + 1,
        confirmed_organizational_bindings=False,
        inventory_identity=inventory.inventory_identity,
        source_artifacts=_source_artifacts(inventory),
        recovered_authorities=recovered.recovered_authorities,
        requested_bindings=tuple(retained_bindings),
        conflicts=tuple(retained_conflicts),
        unresolved=tuple(unresolved),
        proposer=Proposer(kind="claude", model=model, tool_schema_id=TOOL_SCHEMA_ID),
    )
    validate_binding_proposal(proposal)
    validate_proposal_grounding(proposal, inventory)
    return proposal


def _inventory_input(inventory: Inventory, recovered: BindingProposal) -> dict[str, Any]:
    resolved = {
        _destination_key(binding.destination)
        for binding in recovered.requested_bindings if binding.state == "proposed"
    }
    return {
        "inventory": inventory.to_dict(),
        "recovered_proposal": recovered.to_dict(),
        "required_destinations": [_destination_key(item) for item in REQUIRED_DESTINATIONS],
        "missing_destinations": [
            _destination_key(item) for item in REQUIRED_DESTINATIONS
            if _destination_key(item) not in resolved
        ],
    }


def _resolves_required_destinations(proposal: BindingProposal) -> bool:
    proposed = {
        binding.destination
        for binding in proposal.requested_bindings
        if binding.state == "proposed"
    }
    return (
        set(REQUIRED_DESTINATIONS).issubset(proposed)
        and not proposal.unresolved
        and not proposal.conflicts
        and all(binding.state == "proposed" for binding in proposal.requested_bindings)
    )


def propose_bindings(
    inventory: Inventory,
    recovered: BindingProposal | None = None,
    *,
    client="auto",
    model: str | None = None,
) -> BindingProposal:
    """Fill missing structural compiler bindings using a forced Claude tool call.

    A complete recovered proposal is returned byte-for-byte at the Python object boundary without
    constructing a model client.  There is deliberately no no-model heuristic.
    """
    if recovered is None:
        recovered = BindingProposal.empty(inventory.inventory_identity, _source_artifacts(inventory))
    validate_binding_proposal(recovered)
    if recovered.inventory_identity != inventory.inventory_identity:
        raise ValueError("compiler proposer: recovered proposal belongs to a different inventory")
    validate_proposal_grounding(recovered, inventory)
    if not recovered.blocks_compilation or _resolves_required_destinations(recovered):
        return recovered

    if client == "auto":
        client = _default_client()
    if client is None:
        raise RuntimeError(
            "compiler proposer needs a model; provide a client or set ANTHROPIC_API_KEY "
            "with the anthropic package installed"
        )
    selected_model = model or os.environ.get("SC_REFEREE_MODEL", DEFAULT_MODEL)
    schema = binding_proposal_tool_schema()
    message = client.messages.create(
        model=selected_model,
        max_tokens=5000,
        system=SYSTEM_PROMPT,
        tools=[{
            "name": PROPOSAL_TOOL,
            "description": (
                "Propose only evidence-grounded structural bindings needed by the compiler."
            ),
            "input_schema": schema,
        }],
        tool_choice={"type": "tool", "name": PROPOSAL_TOOL},
        messages=[{
            "role": "user",
            "content": json.dumps(_inventory_input(inventory, recovered), indent=2),
        }],
    )
    uses = [block for block in message.content
            if getattr(block, "type", None) == "tool_use"
            and getattr(block, "name", None) == PROPOSAL_TOOL]
    if not uses:
        raise ValueError(
            "compiler proposer: the model did not call `propose_compiler_bindings` "
            "(returned prose instead)"
        )
    payload = uses[0].input
    try:
        jsonschema.validate(payload, schema)
    except jsonschema.ValidationError as exc:
        raise ValueError(
            "compiler proposer: the model's binding proposal failed schema validation: "
            f"{exc.message}"
        ) from exc
    try:
        return _merge_proposal(inventory, recovered, payload, selected_model)
    except jsonschema.ValidationError as exc:
        raise ValueError(
            "compiler proposer: the model's binding proposal failed contract validation: "
            f"{exc.message}"
        ) from exc
