"""The non-authoritative compiler binding-proposal contract.

A proposal can organize evidence and name destinations.  It cannot confirm scientific authority,
carry CSP state, or express a verdict.  The schema is deliberately closed at every object boundary.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import jsonschema

SCHEMA_ID = "sc-referee/compiler-binding-proposal/v1"
TOOL_SCHEMA_ID = "sc-referee/compiler-binding-proposal-tool/v1"

AUTHORITIES = frozenset({
    "design", "row_ledger", "fitted_design", "reported_claim", "empty_droplet",
    "csp_proposal", "detector_input",
})

# These names are forbidden recursively, including inside candidate values.  That prevents a thin
# organizational proposal from becoming an alternate authority or verdict object.
_FORBIDDEN_KEYS = frozenset({
    "confirmed_by_human", "csp_field_state", "field_state", "authority_attestation",
    "authority_attested", "confirmed_digest", "confirmation_state",
    "status", "severity", "applicability", "coverage", "judgment", "verdict",
    "code", "code_expression", "python", "python_expression", "generated_code", "expression",
})


@dataclass(frozen=True)
class Destination:
    authority: str
    field: str


@dataclass(frozen=True)
class Locator:
    kind: str
    value: str


@dataclass(frozen=True)
class Evidence:
    artifact_identity: str
    path: str
    locator: Locator
    evidence_digest: str


@dataclass(frozen=True)
class RequestedBinding:
    binding_id: str
    destination: Destination
    candidate_value: Any
    confidence: str
    evidence: tuple[Evidence, ...]
    state: str = "proposed"


@dataclass(frozen=True)
class ConflictCandidate:
    candidate_value: Any
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class BindingConflict:
    destination: Destination
    candidates: tuple[ConflictCandidate, ...]
    resolution: str = "unresolved"
    load_bearing: bool = True


@dataclass(frozen=True)
class Proposer:
    kind: str
    model: str | None
    tool_schema_id: str


@dataclass(frozen=True)
class BindingProposal:
    schema_id: str
    proposal_id: str
    revision: int
    inventory_identity: str
    confirmed_organizational_bindings: bool = False
    source_artifacts: tuple[Mapping[str, str], ...] = field(default_factory=tuple)
    recovered_authorities: tuple[str, ...] = field(default_factory=tuple)
    requested_bindings: tuple[RequestedBinding, ...] = field(default_factory=tuple)
    conflicts: tuple[BindingConflict, ...] = field(default_factory=tuple)
    unresolved: tuple[str, ...] = field(default_factory=tuple)
    proposer: Proposer = field(default_factory=lambda: Proposer(
        kind="deterministic", model=None, tool_schema_id=TOOL_SCHEMA_ID))

    @classmethod
    def empty(cls, inventory_identity: str, source_artifacts=()) -> "BindingProposal":
        """Create the typed, explicitly empty hand-off for the next-cycle Claude proposer."""
        seed = json.dumps({
            "schema_id": SCHEMA_ID,
            "revision": 1,
            "inventory_identity": inventory_identity,
            "source_artifacts": list(source_artifacts),
            "kind": "deterministic",
        }, sort_keys=True, separators=(",", ":"))
        proposal_id = "sha256:" + hashlib.sha256(seed.encode("utf-8")).hexdigest()
        proposal = cls(
            schema_id=SCHEMA_ID,
            proposal_id=proposal_id,
            revision=1,
            confirmed_organizational_bindings=False,
            inventory_identity=inventory_identity,
            source_artifacts=tuple(source_artifacts),
        )
        validate_binding_proposal(proposal)
        return proposal

    @property
    def blocks_compilation(self) -> bool:
        """Unresolved slots and every load-bearing unresolved conflict fail closed."""
        return bool(
            not self.confirmed_organizational_bindings
            or self.unresolved
            or any(binding.state != "proposed" for binding in self.requested_bindings)
            or any(conflict.load_bearing and conflict.resolution == "unresolved"
                   for conflict in self.conflicts)
        )

    def to_dict(self) -> dict[str, Any]:
        # The contract is JSON, so tuples in the frozen Python representation serialize as arrays.
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))


def binding_proposal_schema() -> dict[str, Any]:
    """Load the packaged JSON Schema used by both local validation and the future tool call."""
    return json.loads(
        (Path(__file__).parents[1] / "schemas" / "compiler-binding-proposal-v1.schema.json")
        .read_text(encoding="utf-8")
    )


def _validate_semantics(value: Any) -> None:
    if isinstance(value, Mapping):
        forbidden = _FORBIDDEN_KEYS.intersection(map(str, value.keys()))
        if forbidden:
            raise jsonschema.ValidationError(
                f"binding proposals cannot carry authority/verdict/code field(s): {sorted(forbidden)}")
        for nested in value.values():
            _validate_semantics(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _validate_semantics(nested)


def _validate_candidate_value(value: Any) -> None:
    """Candidate payloads cannot smuggle a CSP field record through the allowed binding state key."""
    if isinstance(value, Mapping):
        if "state" in value or "confidence" in value:
            raise jsonschema.ValidationError(
                "candidate values cannot carry CSP field state/confidence; bind the underlying value only")
        for nested in value.values():
            _validate_candidate_value(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _validate_candidate_value(nested)


def _validate_relative_path(path: str) -> None:
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or ".." in parsed.parts or not path or "\\" in path:
        raise jsonschema.ValidationError(f"evidence path must be a confined POSIX relative path: {path!r}")


def _validate_destination(destination: Mapping[str, Any]) -> None:
    field_name = str(destination["field"]).strip().lower()
    if field_name in _FORBIDDEN_KEYS or field_name in {
        "free_form_code", "script", "callable",
    }:
        raise jsonschema.ValidationError(
            f"binding destination {field_name!r} would carry authority state or a free-form code expression")


def validate_binding_proposal(proposal: BindingProposal | Mapping[str, Any]) -> None:
    payload = proposal.to_dict() if isinstance(proposal, BindingProposal) else dict(proposal)
    jsonschema.validate(payload, binding_proposal_schema())
    _validate_semantics(payload)
    for source in payload["source_artifacts"]:
        _validate_relative_path(source["path"])
    for binding in payload["requested_bindings"]:
        _validate_destination(binding["destination"])
        _validate_candidate_value(binding["candidate_value"])
        for evidence in binding["evidence"]:
            _validate_relative_path(evidence["path"])
    for conflict in payload["conflicts"]:
        _validate_destination(conflict["destination"])
        for candidate in conflict["candidates"]:
            _validate_candidate_value(candidate["candidate_value"])
            for evidence in candidate["evidence"]:
                _validate_relative_path(evidence["path"])


class BindingProposer:
    """Clearly named next-cycle seam; implementations fill only unresolved binding slots."""

    def propose_bindings(self, *, inventory: Any, empty_proposal: BindingProposal) -> BindingProposal:
        raise NotImplementedError("the Claude binding proposer is intentionally not implemented in M2 cycle 1")
