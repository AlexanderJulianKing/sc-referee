"""End-to-end orchestration for the explicit ``referee compile`` path.

Claude is confined to structural binding proposals.  Organizational confirmation and the
four-decision scientific ceremony are deliberately separate steps, and capsule replay never calls
a model.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.compiler.binding_proposal import (
    BindingProposal,
    RequestedBinding,
    validate_binding_proposal,
)
from sc_referee.compiler.capsule import (
    Capsule,
    ReplayStatus,
    freeze_capsule,
    replay_capsule,
)
from sc_referee.compiler.inventory import Inventory
from sc_referee.compiler.proposer import propose_bindings, validate_proposal_grounding
from sc_referee.compiler.resolve import CompileNeeded, NoCompileNeeded, resolve_for_compile
from sc_referee.csp_contracts.contamination_condensed_ceremony import (
    CondensedAnswer,
    CondensedGroup,
)
from sc_referee.derivations.gbp07_compile import (
    Gbp07Compilation,
    ProposalCompilationAbstention,
    compile_from_proposal,
)


InjectedProposer = Callable[[Inventory], BindingProposal]
OrganizationalReviewer = Callable[[BindingProposal], "OrganizationalConfirmation | None"]


@dataclass(frozen=True)
class OrganizationalConfirmation:
    """Receipt for one explicit human review of one exact structural proposal."""

    proposal_id: str
    inventory_identity: str
    requested_bindings_digest: str
    actor: str


def _requested_bindings_digest(proposal: BindingProposal) -> str:
    payload = [
        {
            "binding_id": binding.binding_id,
            "destination": {
                "authority": binding.destination.authority,
                "field": binding.destination.field,
            },
            "candidate_value": binding.candidate_value,
            "confidence": binding.confidence,
            "evidence": [
                {
                    "artifact_identity": evidence.artifact_identity,
                    "path": evidence.path,
                    "locator": {
                        "kind": evidence.locator.kind,
                        "value": evidence.locator.value,
                    },
                    "evidence_digest": evidence.evidence_digest,
                }
                for evidence in binding.evidence
            ],
            "state": binding.state,
        }
        for binding in proposal.requested_bindings
    ]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def record_organizational_confirmation(
    proposal: BindingProposal,
    *,
    actor: str,
) -> OrganizationalConfirmation:
    """Record an external review action after the exact proposal has been displayed."""
    if not isinstance(actor, str) or not actor.strip():
        raise ValueError("organizational confirmation requires a non-empty human actor")
    return OrganizationalConfirmation(
        proposal_id=proposal.proposal_id,
        inventory_identity=proposal.inventory_identity,
        requested_bindings_digest=_requested_bindings_digest(proposal),
        actor=actor.strip(),
    )


def render_organizational_review(proposal: BindingProposal) -> str:
    """Render the exact structural authority a reviewer is being asked to accept."""
    lines = [
        "STRUCTURAL BINDINGS — REVIEW REQUIRED",
        f"proposal_id: {proposal.proposal_id}",
        f"inventory_identity: {proposal.inventory_identity}",
        f"requested_bindings_digest: {_requested_bindings_digest(proposal)}",
    ]
    for binding in proposal.requested_bindings:
        destination = f"{binding.destination.authority}.{binding.destination.field}"
        evidence = ", ".join(
            f"{item.path}:{item.locator.kind}:{item.locator.value} [{item.evidence_digest}]"
            for item in binding.evidence
        )
        lines.append(
            f"  {destination} = {_binding_value(binding)}\n"
            f"    confidence={binding.confidence}; evidence={evidence}"
        )
    for conflict in proposal.conflicts:
        lines.append(
            f"  CONFLICT {conflict.destination.authority}.{conflict.destination.field}: "
            f"{len(conflict.candidates)} candidates ({conflict.resolution})"
        )
    for unresolved in proposal.unresolved:
        lines.append(f"  UNRESOLVED {unresolved}")
    return "\n".join(lines)


@dataclass(frozen=True)
class CompileAuditResult:
    """The complete compiler outcome, or an explicit hand-off to the ordinary audit path."""

    normal_audit_applies: bool
    proposal: BindingProposal | None
    finding: Finding | None
    capsule: Capsule | None
    replay_status: ReplayStatus | None
    summary: str
    compilation: Gbp07Compilation | None = None
    abstention: ProposalCompilationAbstention | None = None

    @property
    def rendered_summary(self) -> str:
        """Readable alias for callers that prefer to name the rendered artifact explicitly."""

        return self.summary


def confirm_organizational_bindings(
    proposal: BindingProposal,
    confirmation: OrganizationalConfirmation,
) -> BindingProposal:
    """Confirm that a human accepts Claude's structural bindings without changing them.

    This is an organizational confirmation only.  It does not ratify any scientific premise and
    cannot turn an unresolved or conflicting proposal into a compilable one.
    """

    validate_binding_proposal(proposal)
    if not isinstance(confirmation, OrganizationalConfirmation):
        raise TypeError("organizational confirmation requires an explicit review receipt")
    if confirmation.proposal_id != proposal.proposal_id:
        raise ValueError("organizational confirmation belongs to a different proposal")
    if confirmation.inventory_identity != proposal.inventory_identity:
        raise ValueError("organizational confirmation belongs to a different inventory")
    if confirmation.requested_bindings_digest != _requested_bindings_digest(proposal):
        raise ValueError("organizational confirmation does not match the proposed bindings")
    if not confirmation.actor.strip():
        raise ValueError("organizational confirmation has no human actor")
    if proposal.unresolved or proposal.conflicts:
        raise ValueError("unresolved or conflicting organizational bindings cannot be confirmed")
    if any(binding.state != "proposed" for binding in proposal.requested_bindings):
        raise ValueError("only proposed organizational bindings can be confirmed")
    return replace(proposal, confirmed_organizational_bindings=True)


def _normalized_answers(
    answers: Mapping[object, object],
) -> dict[CondensedGroup, CondensedAnswer]:
    decisions: dict[CondensedGroup, CondensedAnswer] = {}
    for key, value in answers.items():
        try:
            group = key if isinstance(key, CondensedGroup) else CondensedGroup(str(key).title())
        except ValueError as exc:
            raise ValueError(f"unknown condensed ceremony group: {key!r}") from exc
        if isinstance(value, CondensedAnswer):
            answer = value
        else:
            normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
            try:
                answer = CondensedAnswer(normalized)
            except ValueError as exc:
                raise ValueError(f"invalid answer for {group.value}: {value!r}") from exc
        decisions[group] = answer
    missing = set(CondensedGroup).difference(decisions)
    extra = set(decisions).difference(CondensedGroup)
    if missing or extra:
        labels = ", ".join(sorted(group.value for group in missing))
        raise ValueError(f"compile requires exactly four ceremony answers; missing: {labels}")
    return {group: decisions[group] for group in CondensedGroup}


def _run_proposer(
    inventory: Inventory,
    empty_proposal: BindingProposal,
    *,
    client: Any,
    proposer: InjectedProposer | Any | None,
) -> BindingProposal:
    if proposer is None:
        return propose_bindings(inventory, empty_proposal, client=client)
    if callable(proposer):
        return proposer(inventory)
    method = getattr(proposer, "propose_bindings", None)
    if callable(method):
        return method(inventory=inventory, empty_proposal=empty_proposal)
    raise TypeError("injected proposer must be callable or expose propose_bindings")


def _binding_value(binding: RequestedBinding) -> str:
    value = binding.candidate_value
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def render_compile_summary(
    proposal: BindingProposal,
    answers: Mapping[CondensedGroup, CondensedAnswer],
    finding: Finding,
    replay_status: ReplayStatus,
) -> str:
    """Render the bounded compile claim without causal or benchmark-answer overreach."""

    lines = ["STRUCTURAL BINDINGS — proposed by Claude"]
    for binding in proposal.requested_bindings:
        destination = f"{binding.destination.authority}.{binding.destination.field}"
        lines.append(f"  {destination}: {_binding_value(binding)}")

    lines.extend(("", "SCIENTIFIC CEREMONY — human confirmations"))
    for group in CondensedGroup:
        lines.append(f"  {group.value}: {answers[group].value.upper()}")

    human_state = S.human_state(finding)
    lines.extend(("", f"CONDITIONAL FINDING: {human_state.upper()} ({finding.status.upper()})"))
    if human_state == S.FLAGGED and finding.status == S.MAJOR:
        lines.append(
            "Conditional on the ratified premises, the submitted fitted design does not contain "
            "the exact ratified contamination basis."
        )
    elif human_state == S.CLEAR:
        lines.append(
            "Conditional on the ratified premises, the submitted fitted design contains the exact "
            "ratified contamination basis."
        )
    else:
        lines.append(
            "The four scientific premises were not all ratified, so the conditional check was "
            "NOT_CHECKED."
        )
    lines.append(f"replayed without a model: {replay_status.value.upper()}")
    return "\n".join(lines)


def run_compile_audit(
    folder: str | Path,
    *,
    answers: Mapping[object, object],
    client: Any = "auto",
    proposer: InjectedProposer | Any | None = None,
    organizational_reviewer: OrganizationalReviewer | None = None,
) -> CompileAuditResult:
    """Resolve, propose, confirm, compile, freeze, and model-free replay one raw folder."""

    resolved = resolve_for_compile(folder)
    if isinstance(resolved, NoCompileNeeded):
        return CompileAuditResult(
            normal_audit_applies=True,
            proposal=None,
            finding=None,
            capsule=None,
            replay_status=None,
            summary=(
                "No compile needed: deterministic ingest recognized this folder. "
                "Use the normal deterministic audit path."
            ),
        )
    if not isinstance(resolved, CompileNeeded):  # pragma: no cover - closed resolver result
        raise TypeError(f"unexpected compile resolver result: {type(resolved).__name__}")

    # Validate ceremony completeness before any optional model call.  The decisions are consumed
    # only after organizational review below, but a non-interactive caller that supplied none must
    # receive the ordinary actionable error without spending model tokens.
    _normalized_answers(answers)

    proposed = _run_proposer(
        resolved.inventory,
        resolved.proposal,
        client=client,
        proposer=proposer,
    )
    validate_binding_proposal(proposed)
    validate_proposal_grounding(proposed, resolved.inventory)
    # A proposer is never an authority source, even if an injected implementation sets the bit.
    proposed = replace(proposed, confirmed_organizational_bindings=False)
    if organizational_reviewer is None:
        return CompileAuditResult(
            normal_audit_applies=False,
            proposal=proposed,
            finding=None,
            capsule=None,
            replay_status=None,
            summary=render_organizational_review(proposed) +
                    "\n\nNOT_CHECKED: explicit organizational confirmation required.",
        )
    confirmation = organizational_reviewer(proposed)
    if confirmation is None:
        return CompileAuditResult(
            normal_audit_applies=False,
            proposal=proposed,
            finding=None,
            capsule=None,
            replay_status=None,
            summary=render_organizational_review(proposed) +
                    "\n\nNOT_CHECKED: organizational bindings were not accepted.",
        )
    proposal = confirm_organizational_bindings(proposed, confirmation)
    decisions = _normalized_answers(answers)
    compilation = compile_from_proposal(proposal, folder, decisions)
    if isinstance(compilation, ProposalCompilationAbstention):
        reason = f"{compilation.reason_code.value}: {compilation.message}"
        return CompileAuditResult(
            normal_audit_applies=False,
            proposal=proposal,
            finding=None,
            capsule=None,
            replay_status=None,
            summary=f"NOT_CHECKED / could not compile: {reason}",
            abstention=compilation,
        )
    if compilation.finding is None:  # pragma: no cover - Gbp07Compilation invariant
        raise RuntimeError("proposal compilation returned no finding")

    capsule = freeze_capsule(compilation, proposal, decisions, folder)
    replay = replay_capsule(capsule, folder)
    assert replay.status is ReplayStatus.MATCH, (
        "fresh compiler capsule did not replay exactly: "
        f"{replay.status.value}: {replay.message}"
    )
    summary = render_compile_summary(proposal, decisions, compilation.finding, replay.status)
    return CompileAuditResult(
        normal_audit_applies=False,
        proposal=proposal,
        finding=compilation.finding,
        capsule=capsule,
        replay_status=replay.status,
        summary=summary,
        compilation=compilation,
    )


__all__ = [
    "CompileAuditResult",
    "OrganizationalConfirmation",
    "confirm_organizational_bindings",
    "record_organizational_confirmation",
    "render_organizational_review",
    "render_compile_summary",
    "run_compile_audit",
]
