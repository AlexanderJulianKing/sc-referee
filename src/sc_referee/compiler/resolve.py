"""Explicit deterministic-first trigger for compilation.

The ordinary audit path does not import or call this module.  A caller opts in, legacy ingest runs
first, and only recognition/ambiguity refusals become compiler inventory work.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.compiler.binding_proposal import BindingProposal
from sc_referee.compiler.inventory import Inventory, build_inventory
from sc_referee.ingest import IngestError, ingest


@dataclass(frozen=True)
class NoCompileNeeded:
    bundle: Any


@dataclass(frozen=True)
class CompileNeeded:
    inventory: Inventory
    proposal: BindingProposal
    ingest_failure: str


_RECOGNITION_FILE_NOT_FOUND = (
    "no supported data matrix found",
    "no count matrix found",
    "but no cell-metadata table",
)
_RECOGNITION_AMBIGUITIES = (
    "candidate data matrices found",
    "competing metadata tables found",
    "multiple differing raw-count matrices are plausible",
    "multiple internal matrices exist but none is uniquely raw",
)


def _is_compile_trigger(exc: BaseException) -> bool:
    message = str(exc).lower()
    if isinstance(exc, FileNotFoundError):
        return any(marker in message for marker in _RECOGNITION_FILE_NOT_FOUND)
    if isinstance(exc, IngestError):
        return any(marker in message for marker in _RECOGNITION_AMBIGUITIES)
    return False


def resolve_for_compile(folder: str | Path) -> NoCompileNeeded | CompileNeeded:
    """Run legacy ingest and return a typed result; this function is the opt-in trigger."""
    root = Path(folder)
    try:
        return NoCompileNeeded(bundle=ingest(root))
    except (FileNotFoundError, IngestError) as exc:
        if not _is_compile_trigger(exc):
            raise
        inventory = build_inventory(root)
        sources = tuple({
            "artifact_identity": artifact.artifact_identity,
            "path": artifact.relative_path,
            "kind": artifact.kind,
        } for artifact in inventory.artifacts)
        return CompileNeeded(
            inventory=inventory,
            proposal=BindingProposal.empty(inventory.inventory_identity, sources),
            ingest_failure=str(exc),
        )
