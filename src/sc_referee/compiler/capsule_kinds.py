"""Registry mapping a capsule *kind* to its runner.

A compiled-analysis capsule declares a ``capsule_kind`` in its manifest. This registry turns that kind
into the implementation the friendly bridge needs. Adding another compiled workflow means registering
another kind here; nothing in the browser path or the bridge is specialized to a particular workflow.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from sc_referee.compiler.pipeline import CompileAuditResult


class UnknownCapsuleKind(ValueError):
    """The manifest declares a capsule kind that no handler is registered for."""


@dataclass(frozen=True)
class CapsuleKind:
    """One supported compiled-analysis kind and the runner that implements it."""

    kind: str
    runner: Callable[[str | Path, Mapping[object, object]], CompileAuditResult]
    # A fixed, benchmark-free boundary sentence appended (presentation only) to a flagged finding's
    # verdict, so the report states what the structural result does NOT establish. Code-controlled — not
    # taken from the manifest — so it can never leak external truth or misrepresent the verifier.
    finding_boundary: str = ""


_REGISTRY: dict[str, CapsuleKind] = {}


def register_capsule_kind(kind: CapsuleKind) -> None:
    _REGISTRY[kind.kind] = kind


def _ensure_builtin_kinds() -> None:
    # Imported lazily to avoid a compiler -> derivations import cycle at module load.
    from sc_referee.derivations import gbp07_capsule  # noqa: F401  (registers on import)


def get_capsule_kind(name: str) -> CapsuleKind:
    if name not in _REGISTRY:
        _ensure_builtin_kinds()
    kind = _REGISTRY.get(name)
    if kind is None:
        raise UnknownCapsuleKind(
            f"no handler registered for capsule kind {name!r}; "
            f"known kinds: {sorted(_REGISTRY) or '(none)'}")
    return kind


def run_capsule_audit(
    kind: CapsuleKind,
    artifacts_dir: str | Path,
    answers: Mapping[object, object],
) -> CompileAuditResult:
    """Dispatch the audit to the runner registered for this capsule kind.

    ``answers`` are the human's ceremony confirmations. Each kind owns its complete execution strategy,
    so adding an unrelated kind does not require a conditional or compiler-specific behavior here.
    """
    return kind.runner(artifacts_dir, answers)
