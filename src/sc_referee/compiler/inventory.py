"""Bounded, content-addressed inventory for the opt-in compiler path.

Delimited matrices are inspected with ``nrows=0``: only their header/parser metadata is created as a
DataFrame.  File hashing streams bytes.  Documentation text is evidence, never an instruction.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import pandas as pd

DOCUMENTATION_LIMIT_BYTES = 64 * 1024


class InventoryPathError(ValueError):
    """A requested or discovered inventory path escapes the supplied root."""


@dataclass(frozen=True)
class InventoryArtifact:
    relative_path: str
    artifact_identity: str
    size: int
    kind: str
    compression: str | None = None
    columns: tuple[str, ...] = ()
    dtypes: tuple[tuple[str, str], ...] = ()
    metadata_error: str | None = None
    evidence_trust: str | None = None
    documentation_text: str | None = None
    documentation_truncated: bool = False


@dataclass(frozen=True)
class Inventory:
    schema_id: str
    inventory_identity: str
    artifacts: tuple[InventoryArtifact, ...]
    deterministic_facts: dict[str, Any]
    root_path: str | None = field(default=None, repr=False, compare=False)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("root_path", None)
        return json.loads(json.dumps(payload, ensure_ascii=False))


def confine_inventory_path(root: str | Path, relative_path: str | Path) -> Path:
    """Resolve one caller-supplied relative path, rejecting absolute, parent, and symlink escapes."""
    raw = str(relative_path)
    relative = PurePosixPath(raw)
    if relative.is_absolute() or not raw or ".." in relative.parts or "\\" in raw:
        raise InventoryPathError(f"inventory paths must be confined POSIX relative paths: {raw!r}")
    canonical_root = Path(root).resolve(strict=True)
    candidate = canonical_root.joinpath(*relative.parts)
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise InventoryPathError(f"inventory path cannot be safely resolved: {raw!r}") from exc
    try:
        resolved.relative_to(canonical_root)
    except ValueError as exc:
        raise InventoryPathError(f"inventory path escapes the analysis root: {raw!r}") from exc
    return resolved


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _kind(path: Path) -> tuple[str, str | None]:
    name = path.name.lower()
    compression = "gzip" if name.endswith(".gz") else None
    logical = name[:-3] if compression else name
    suffix = Path(logical).suffix
    kinds = {
        ".csv": "delimited_table", ".tsv": "delimited_table", ".h5ad": "anndata",
        ".txt": "text", ".md": "markdown", ".rst": "text", ".yaml": "yaml", ".yml": "yaml",
        ".json": "json", ".ipynb": "notebook", ".py": "python", ".r": "r", ".rmd": "r_markdown",
    }
    return kinds.get(suffix, "unsupported"), compression


def _table_metadata(path: Path) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...], str | None]:
    logical_name = path.name[:-3] if path.name.lower().endswith(".gz") else path.name
    separator = "\t" if logical_name.lower().endswith(".tsv") else ","
    try:
        # Header-only parsing is gzip-aware and never materializes a table row or matrix value.
        header = pd.read_csv(path, sep=separator, nrows=0, encoding="utf-8-sig")
    except (OSError, UnicodeError, ValueError, pd.errors.ParserError,
            pd.errors.EmptyDataError) as exc:
        return (), (), f"header metadata unavailable: {type(exc).__name__}: {exc}"
    columns = tuple(map(str, header.columns))
    dtypes = tuple((str(column), str(header.dtypes.iloc[index]))
                   for index, column in enumerate(header.columns))
    return columns, dtypes, None


def _is_documentation(path: Path) -> bool:
    low = path.name.lower()
    return low.startswith("readme") or low.startswith("method") or path.suffix.lower() == ".txt"


def _documentation(path: Path) -> tuple[str, bool]:
    with path.open("rb") as handle:
        content = handle.read(DOCUMENTATION_LIMIT_BYTES + 1)
    truncated = len(content) > DOCUMENTATION_LIMIT_BYTES
    return content[:DOCUMENTATION_LIMIT_BYTES].decode("utf-8", errors="replace"), truncated


def _deterministic_facts(artifacts: tuple[InventoryArtifact, ...]) -> dict[str, Any]:
    matrix_candidates = []
    reported_candidates = []
    code_artifacts = []
    documentation_artifacts = []
    for artifact in artifacts:
        path = PurePosixPath(artifact.relative_path)
        logical_name = path.name[:-3] if path.name.lower().endswith(".gz") else path.name
        stem = Path(logical_name).stem.lower()
        if artifact.kind == "anndata" or (
            artifact.kind == "delimited_table" and stem in {"counts", "matrix"}
        ):
            matrix_candidates.append(artifact.relative_path)
        if artifact.kind == "delimited_table" and artifact.columns:
            from sc_referee import synonyms
            if synonyms.is_reported_de(artifact.columns):
                reported_candidates.append(artifact.relative_path)
        if artifact.kind in {"python", "r", "r_markdown", "notebook"}:
            code_artifacts.append(artifact.relative_path)
        if artifact.evidence_trust == "untrusted_documentation":
            documentation_artifacts.append(artifact.relative_path)
    return {
        "recognized_matrix_candidates": sorted(matrix_candidates),
        "recognized_reported_table_candidates": sorted(reported_candidates),
        "recognized_code_artifacts": sorted(code_artifacts),
        "untrusted_documentation_artifacts": sorted(documentation_artifacts),
    }


def build_inventory(folder: str | Path) -> Inventory:
    """Enumerate and hash files under ``folder`` without following any escape from that root."""
    root = Path(folder)
    if not root.is_dir():
        raise InventoryPathError(f"inventory root is not a directory: {folder}")
    canonical_root = root.resolve(strict=True)
    artifacts = []
    for discovered in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = discovered.relative_to(root).as_posix()
        # Validate symlinks before filtering directories: a symlinked directory is itself an escape.
        resolved = confine_inventory_path(canonical_root, relative)
        if resolved.is_dir():
            continue
        if not resolved.is_file():
            continue
        kind, compression = _kind(discovered)
        columns: tuple[str, ...] = ()
        dtypes: tuple[tuple[str, str], ...] = ()
        metadata_error = None
        if kind == "delimited_table":
            columns, dtypes, metadata_error = _table_metadata(resolved)
        evidence_trust = None
        documentation_text = None
        documentation_truncated = False
        if _is_documentation(discovered):
            evidence_trust = "untrusted_documentation"
            documentation_text, documentation_truncated = _documentation(resolved)
        artifacts.append(InventoryArtifact(
            relative_path=relative,
            artifact_identity=_sha256(resolved),
            size=resolved.stat().st_size,
            kind=kind,
            compression=compression,
            columns=columns,
            dtypes=dtypes,
            metadata_error=metadata_error,
            evidence_trust=evidence_trust,
            documentation_text=documentation_text,
            documentation_truncated=documentation_truncated,
        ))
    frozen_artifacts = tuple(artifacts)
    facts = _deterministic_facts(frozen_artifacts)
    identity_payload = {
        "schema_id": "sc-referee/compiler-inventory/v1",
        "artifacts": [asdict(artifact) for artifact in frozen_artifacts],
        "deterministic_facts": facts,
    }
    canonical = json.dumps(identity_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    identity = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return Inventory(
        schema_id="sc-referee/compiler-inventory/v1",
        inventory_identity=identity,
        artifacts=frozen_artifacts,
        deterministic_facts=facts,
        root_path=str(canonical_root),
    )
