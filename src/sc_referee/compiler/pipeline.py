"""End-to-end orchestration for the explicit ``referee compile`` path.

Claude is confined to structural binding proposals.  Organizational confirmation and the
four-decision scientific ceremony are deliberately separate steps, and capsule replay never calls
a model.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
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
from sc_referee.compiler.proposer import propose_bindings
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
    organizational_bindings: tuple[RequestedBinding, ...],
) -> BindingProposal:
    """Confirm that a human accepts Claude's structural bindings without changing them.

    This is an organizational confirmation only.  It does not ratify any scientific premise and
    cannot turn an unresolved or conflicting proposal into a compilable one.
    """

    validate_binding_proposal(proposal)
    echoed = tuple(organizational_bindings)
    if echoed != proposal.requested_bindings:
        raise ValueError("organizational confirmation must echo the proposed bindings exactly")
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

    decisions = _normalized_answers(answers)
    proposed = _run_proposer(
        resolved.inventory,
        resolved.proposal,
        client=client,
        proposer=proposer,
    )
    proposal = confirm_organizational_bindings(proposed, proposed.requested_bindings)
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
    "confirm_organizational_bindings",
    "render_compile_summary",
    "run_compile_audit",
]
