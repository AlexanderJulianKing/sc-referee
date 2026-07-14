"""Freeze and replay proposal-driven compiler findings without a model call.

Byte-identical identity comparison is intentionally scoped to the exact numeric
environment recorded in the capsule.  A different environment is allowed to
replay, but its result is explicitly marked ``ENVIRONMENT_MISMATCH``.
"""
from __future__ import annotations

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import inspect
import json
import platform
from pathlib import Path
import sys
from types import MappingProxyType
from typing import Any, Mapping
from unittest.mock import patch

import numpy as np
import pandas as pd

from sc_referee.compiler.binding_proposal import BindingProposal
from sc_referee.compiler.inventory import confine_inventory_path
from sc_referee.csp_contracts.contamination_condensed_ceremony import (
    CondensedAnswer,
    CondensedGroup,
)
from sc_referee.derivations import gbp07_compile
from sc_referee.derivations import genebench_gbp07_public_estimator as gbp07_estimator


CAPSULE_SCHEMA_ID = "sc-referee/compiler-capsule/v1"


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _json_value(value: Any) -> Any:
    """Project compiler objects into deterministic JSON values."""

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not np.isfinite(value):
            raise ValueError("capsule semantic values must contain only finite floats")
        return value
    if isinstance(value, np.generic):
        return _json_value(value.item())
    if isinstance(value, np.ndarray):
        return [_json_value(item) for item in value.tolist()]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if is_dataclass(value):
        # Do not use asdict: MappingProxyType values cannot be deep-copied.
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    raise TypeError(f"unsupported capsule value: {type(value).__name__}")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _json_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _identity(value: Any) -> str:
    return _sha256(_canonical_bytes(value))


def environment_identity() -> Mapping[str, str]:
    """Return the numeric/runtime identity that scopes exact replay guarantees."""

    try:
        import scipy
        scipy_version = scipy.__version__
    except ImportError:
        scipy_version = "not-installed"
    return MappingProxyType({
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy_version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "byteorder": sys.byteorder,
    })


def derivation_registry_digest() -> str:
    """Bind the closed registry and the implementation source used by its entries."""

    entries = []
    for derivation_id, function in sorted(gbp07_compile.DERIVATION_REGISTRY.items()):
        entries.append({
            "derivation_id": derivation_id,
            "registered_callable": f"{function.__module__}.{function.__qualname__}",
            "registered_source": inspect.getsource(function),
        })
    # The registered adapter delegates to this estimator; include its implementation rather
    # than pretending that the one-line registry wrapper is the whole numeric policy.
    estimator = gbp07_compile.estimate_genebench_gbp07_public_contamination
    float_digest = gbp07_estimator.canonical_float_digest
    float_token = gbp07_estimator._canonical_float_token
    return _identity({
        "entries": entries,
        "estimator_callable": f"{estimator.__module__}.{estimator.__qualname__}",
        "estimator_source": inspect.getsource(estimator),
        "canonical_float_digest_callable": (
            f"{float_digest.__module__}.{float_digest.__qualname__}"
        ),
        "canonical_float_digest_source": inspect.getsource(float_digest),
        "canonical_float_token_source": inspect.getsource(float_token),
    })


def _answers_payload(answers: Mapping[CondensedGroup, CondensedAnswer]) -> Mapping[str, str]:
    if set(answers) != set(CondensedGroup):
        raise ValueError("a capsule requires exactly the four condensed ceremony answers")
    payload: dict[str, str] = {}
    for group in CondensedGroup:
        answer = answers[group]
        if not isinstance(answer, CondensedAnswer):
            try:
                answer = CondensedAnswer(answer)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid answer for {group.value}") from exc
        payload[group.value] = answer.value
    return MappingProxyType(payload)


def _finding_snapshot(compilation: gbp07_compile.Gbp07Compilation) -> Mapping[str, Any]:
    finding = compilation.finding
    if finding is None:
        raise ValueError("only a completed proposal compilation can be frozen")
    premise = getattr(finding, "conditional_on", None)
    metrics = _json_value(finding.metrics)
    return MappingProxyType({
        "status": finding.status,
        "applicability": getattr(finding, "applicability", None),
        "judgment": getattr(finding, "judgment", None),
        "coverage": getattr(finding, "coverage", None),
        "metrics_identity": _identity(metrics),
        "row_ledger_identity": metrics.get("row_ledger_identity"),
        "fitted_design_identity": metrics.get("fitted_design_identity"),
        "column_space_state": metrics.get("column_space_state"),
        "basis_digest": compilation.artifact.digests.binary_basis_digest,
        "conditional_premise": _json_value(premise),
        "conditional_premise_identity": _identity(premise),
    })


def _compiled_identities(compilation: gbp07_compile.Gbp07Compilation) -> Mapping[str, Any]:
    return MappingProxyType({
        "design_identity": _identity(compilation.design),
        "csp_identity": _identity(compilation.design.csp_contracts),
        "fitted_design_identity": compilation.scope.contract_scope["fitted_design_identity"],
        "row_ledger_identity": compilation.scope.row_ledger_identity,
        "assignment_identity": compilation.scope.assignment_identity,
        "target_coefficient": compilation.design.target_coefficient,
        "target_feature": compilation.design.target_feature,
        "estimand_id": compilation.design.estimand_id,
    })


def _estimator_identities(compilation: gbp07_compile.Gbp07Compilation) -> Mapping[str, Any]:
    return MappingProxyType({
        "artifact_identity": compilation.artifact.artifact_identity,
        "derivation_id": compilation.artifact.derivation_id,
        "digest_policy_id": compilation.artifact.digest_policy_id,
        "digests": _json_value(compilation.artifact.digests),
    })


def _semantic_members(capsule: "Capsule") -> Mapping[str, Any]:
    return {
        "schema_id": capsule.schema_id,
        "proposal": capsule.proposal.to_dict(),
        "proposal_identity": capsule.proposal_identity,
        "answers": dict(capsule.answers),
        "source_digests": dict(capsule.source_digests),
        "derivation_id": capsule.derivation_id,
        "registry_digest": capsule.registry_digest,
        "environment": dict(capsule.environment),
        "generated_code": capsule.generated_code,
        "estimator_identities": dict(capsule.estimator_identities),
        "compiled_identities": dict(capsule.compiled_identities),
        "finding": dict(capsule.finding),
    }


def _member_digests(members: Mapping[str, Any]) -> Mapping[str, str]:
    return {name: _identity(value) for name, value in members.items()}


@dataclass(frozen=True)
class Capsule:
    schema_id: str
    root_digest: str
    member_digests: Mapping[str, str]
    proposal: BindingProposal
    proposal_identity: str
    answers: Mapping[str, str]
    source_digests: Mapping[str, Any]
    derivation_id: str
    registry_digest: str
    environment: Mapping[str, str]
    generated_code: None
    estimator_identities: Mapping[str, Any]
    compiled_identities: Mapping[str, Any]
    finding: Mapping[str, Any]
    frozen_at: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "member_digests", "answers", "source_digests", "environment",
            "estimator_identities", "compiled_identities", "finding",
        ):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

    def to_dict(self) -> dict[str, Any]:
        return {
            **_json_value(_semantic_members(self)),
            "root_digest": self.root_digest,
            "member_digests": dict(self.member_digests),
            # Retained as non-semantic metadata and deliberately excluded from root_digest.
            "frozen_at": self.frozen_at,
        }

    def to_json(self) -> str:
        """Return the canonical JSON serialization of the logical capsule."""

        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        )


class ReplayStatus(str, Enum):
    MATCH = "match"
    INVALIDATED = "invalidated"
    ENVIRONMENT_MISMATCH = "environment_mismatch"
    MISMATCH = "mismatch"


class InvalidationReason(str, Enum):
    SOURCE_DRIFT = "changed_source_byte"
    PROPOSAL_IDENTITY_CHANGED = "changed_proposal_identity"
    ANSWER_CHANGED = "changed_answer"
    DERIVATION_REGISTRY_CHANGED = "changed_derivation_registry_digest"
    ENVIRONMENT_CHANGED = "changed_environment_identity"
    TARGET_COEFFICIENT_CHANGED = "changed_target_coefficient"
    GENOTYPE_ASSIGNMENT_CHANGED = "changed_genotype_assignment_identity"
    FINDING_CHANGED = "changed_finding_identity"
    CAPSULE_ROOT_MISMATCH = "capsule_root_mismatch"
    COMPILATION_ABSTAINED = "replay_compilation_abstained"


@dataclass(frozen=True)
class ReplayResult:
    status: ReplayStatus
    reason: InvalidationReason | None
    message: str
    compilation: gbp07_compile.Gbp07Compilation | None = None
    byte_identical_guaranteed: bool = False

    @property
    def finding(self):
        return None if self.compilation is None else self.compilation.finding


def freeze_capsule(
    compilation: gbp07_compile.Gbp07Compilation,
    proposal: BindingProposal,
    answers: Mapping[CondensedGroup, CondensedAnswer],
    folder: str | Path,
) -> Capsule:
    """Freeze every semantic input and output needed for model-free replay."""

    if compilation.proposal_identity != proposal.proposal_id:
        raise ValueError("compilation and proposal identities disagree")
    paths = compilation.source_digests.get("artifact_paths")
    if not isinstance(paths, Mapping):
        raise ValueError("capsules require proposal-bound raw source byte digests")
    if (
        compilation.source_digests.get("digest_policy_version")
        != gbp07_compile.SOURCE_DIGEST_POLICY_VERSION
    ):
        raise ValueError("capsule source digest policy is missing or unsupported")
    root = Path(folder).expanduser()
    for logical_name, relative_path in paths.items():
        if not isinstance(relative_path, str):
            raise ValueError("compilation source path is not text")
        live_digest = _sha256(confine_inventory_path(root, relative_path).read_bytes())
        if live_digest != compilation.source_digests.get(logical_name):
            raise ValueError(
                f"source bytes changed before capsule freeze: {logical_name}"
            )
    derivation_id = compilation.artifact.derivation_id
    placeholder = Capsule(
        schema_id=CAPSULE_SCHEMA_ID,
        root_digest="",
        member_digests={},
        proposal=proposal,
        proposal_identity=proposal.proposal_id,
        answers=_answers_payload(answers),
        source_digests=_json_value(compilation.source_digests),
        derivation_id=derivation_id,
        registry_digest=derivation_registry_digest(),
        environment=environment_identity(),
        generated_code=None,
        estimator_identities=_estimator_identities(compilation),
        compiled_identities=_compiled_identities(compilation),
        finding=_finding_snapshot(compilation),
    )
    members = _semantic_members(placeholder)
    digests = _member_digests(members)
    return Capsule(
        **{field.name: getattr(placeholder, field.name) for field in fields(Capsule)
           if field.name not in {"root_digest", "member_digests"}},
        member_digests=digests,
        root_digest=_identity(digests),
    )


def _changed_capsule_member(capsule: Capsule) -> str | None:
    current = _member_digests(_semantic_members(capsule))
    for name in sorted(set(current) | set(capsule.member_digests)):
        if current.get(name) != capsule.member_digests.get(name):
            return name
    if _identity(dict(capsule.member_digests)) != capsule.root_digest:
        return "root_digest"
    return None


def _capsule_change_reason(member: str) -> InvalidationReason:
    return {
        "proposal": InvalidationReason.PROPOSAL_IDENTITY_CHANGED,
        "proposal_identity": InvalidationReason.PROPOSAL_IDENTITY_CHANGED,
        "answers": InvalidationReason.ANSWER_CHANGED,
        "registry_digest": InvalidationReason.DERIVATION_REGISTRY_CHANGED,
        "environment": InvalidationReason.ENVIRONMENT_CHANGED,
    }.get(member, InvalidationReason.CAPSULE_ROOT_MISMATCH)


def _current_source_digests(capsule: Capsule, folder: str | Path) -> Mapping[str, str]:
    paths = capsule.source_digests.get("artifact_paths")
    if not isinstance(paths, Mapping):
        raise ValueError("capsule has no named source member paths")
    root = Path(folder).expanduser()
    result = {}
    for logical_name, relative_path in paths.items():
        if not isinstance(relative_path, str):
            raise ValueError("capsule source path is not text")
        result[str(logical_name)] = _sha256(
            confine_inventory_path(root, relative_path).read_bytes()
        )
    return result


def _answers_from_capsule(capsule: Capsule) -> Mapping[CondensedGroup, CondensedAnswer]:
    return {
        CondensedGroup(group): CondensedAnswer(answer)
        for group, answer in capsule.answers.items()
    }


def _forbid_model_client(*args, **kwargs):
    del args, kwargs
    raise RuntimeError("model client construction is prohibited during capsule replay")


@contextmanager
def _model_free_replay_guard():
    """Make every repository model-client resolver a hard-error during replay."""

    attempts: list[str] = []

    def prohibited(*args, **kwargs):
        attempts.append("model_client_resolution")
        return _forbid_model_client(*args, **kwargs)

    with ExitStack() as stack:
        stack.enter_context(patch("sc_referee.compiler.proposer._default_client", prohibited))
        stack.enter_context(patch("sc_referee.init._default_client", prohibited))
        yield attempts


def replay_capsule(capsule: Capsule, folder: str | Path) -> ReplayResult:
    """Replay a frozen proposal and answers; never resolve or construct a model client."""

    changed = _changed_capsule_member(capsule)
    if changed is not None:
        return ReplayResult(
            ReplayStatus.INVALIDATED, _capsule_change_reason(changed),
            f"capsule semantic member changed: {changed}",
        )

    if derivation_registry_digest() != capsule.registry_digest:
        return ReplayResult(
            ReplayStatus.INVALIDATED, InvalidationReason.DERIVATION_REGISTRY_CHANGED,
            "the registered derivation implementation changed",
        )

    try:
        current_sources = _current_source_digests(capsule, folder)
    except (OSError, ValueError) as exc:
        return ReplayResult(
            ReplayStatus.INVALIDATED, InvalidationReason.SOURCE_DRIFT,
            f"a frozen source member is unavailable: {exc}",
        )
    frozen_sources = {
        name: capsule.source_digests.get(name) for name in current_sources
    }
    if current_sources != frozen_sources:
        return ReplayResult(
            ReplayStatus.INVALIDATED, InvalidationReason.SOURCE_DRIFT,
            "one or more named source members changed bytes",
        )

    same_environment = dict(environment_identity()) == dict(capsule.environment)
    with _model_free_replay_guard() as model_attempts:
        replayed = gbp07_compile.compile_from_proposal(
            capsule.proposal, folder, _answers_from_capsule(capsule)
        )
    if model_attempts:
        # This remains a hard runtime failure even if a future compiler layer catches the
        # resolver's exception and tries to turn it into an ordinary abstention.
        raise RuntimeError("model client construction was attempted during capsule replay")
    if isinstance(replayed, gbp07_compile.ProposalCompilationAbstention):
        return ReplayResult(
            ReplayStatus.MISMATCH, InvalidationReason.COMPILATION_ABSTAINED,
            f"the frozen proposal abstained during replay: {replayed.reason_code.value}",
        )

    identities = _compiled_identities(replayed)
    if identities["target_coefficient"] != capsule.compiled_identities["target_coefficient"]:
        return ReplayResult(
            ReplayStatus.MISMATCH, InvalidationReason.TARGET_COEFFICIENT_CHANGED,
            "the replayed target coefficient identity changed", replayed,
        )
    if identities["assignment_identity"] != capsule.compiled_identities["assignment_identity"]:
        return ReplayResult(
            ReplayStatus.MISMATCH, InvalidationReason.GENOTYPE_ASSIGNMENT_CHANGED,
            "the replayed genotype assignment identity changed", replayed,
        )
    all_identities_match = not (
        dict(identities) != dict(capsule.compiled_identities)
        or dict(_estimator_identities(replayed)) != dict(capsule.estimator_identities)
        or dict(_finding_snapshot(replayed)) != dict(capsule.finding)
    )
    if not same_environment:
        observation = "matched" if all_identities_match else "differed"
        return ReplayResult(
            ReplayStatus.ENVIRONMENT_MISMATCH, InvalidationReason.ENVIRONMENT_CHANGED,
            "replay completed in a different numeric environment; captured identities "
            f"{observation}, but byte-identical identity guarantees require the frozen environment",
            replayed, byte_identical_guaranteed=False,
        )
    if not all_identities_match:
        return ReplayResult(
            ReplayStatus.MISMATCH, InvalidationReason.FINDING_CHANGED,
            "the replayed finding or captured identity changed", replayed,
        )
    return ReplayResult(
        ReplayStatus.MATCH, None, "all frozen finding and evidence identities match",
        replayed, byte_identical_guaranteed=True,
    )
