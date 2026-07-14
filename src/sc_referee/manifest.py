"""The multi-file manifest — a DECLARATION of disk layout, separate from `sc-referee.yaml` (which
confirms statistical design). (spec v2 §4)

The manifest names each shard and the CONSTANTS that turn 'one file per mouse' into real obs columns,
plus the assembly policy the deterministic assembler enforces. It declares only the semantically
undecidable axes; the assembler re-derives everything checkable (counts-ness, gene alignment,
cell-id uniqueness, the expected sample set). Roles (which column is condition/replicate) live in
`sc-referee.yaml`, never here — single design authority.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

MODALITIES = frozenset({"RNA", "ADT", "ATAC", "spatial", "metadata"})


@dataclass
class Shard:
    path: str                                  # relative to the manifest/analysis root
    format: str = "h5ad"                       # h5ad | csv | tsv   (10x_mtx | xlsx | parquet deferred)
    constants: dict = field(default_factory=dict)   # materialized as obs columns on every cell
    orientation: str = "cells_x_genes"         # | genes_x_cells | long_triplet (v1: cells_x_genes)
    layer: str | None = None                   # h5ad: which layer is raw counts (else raw.X -> X)
    count_type: str = "raw_counts"             # declared; VERIFIED at assembly
    modality: str = "RNA"                      # only RNA enters the DEG matrix
    obs_path: str | None = None                # optional per-shard metadata file
    obs_join_on: str = "cell_id"
    sha256: str | None = None                  # counts-file hash, recorded at confirm; audit refuses on drift
    obs_sha256: str | None = None              # obs-file hash (if any), recorded at confirm


@dataclass
class Manifest:
    shards: list                               # list[Shard]
    expected_sample_ids: list | None = None    # the declared, complete sample set (multi-shard)
    gene_axis: str = "require_identical"       # | intersect | union_zero_fill  (v1: require_identical)
    cell_ids: str = "prefix_by_sample_id"      # | already_global
    exhaustive: bool = True
    excluded: list = field(default_factory=list)   # [{path, reason}] supported files deliberately out of scope
    confirmed_by_human: bool = False
    confirmed_digest: str | None = None        # digest of the semantic content at confirm; audit refuses on edits
    confidence: dict = field(default_factory=dict) # per-role confidence from the proposer (in-memory)
    unresolved: list = field(default_factory=list) # roles the proposer could not settle; the human fills them


def load_manifest(path) -> Manifest:
    """Parse `sc-referee.manifest.yaml` into the layout model. Roles are NOT read here — the manifest
    declares layout; `sc-referee.yaml` names the design."""
    from sc_referee.ingest import IngestError

    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise IngestError(f"{path}: invalid manifest bytes/YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise IngestError(f"{path}: manifest top level must be a mapping, got {type(raw).__name__}")
    if raw.get("shards") is not None and not isinstance(raw["shards"], list):
        raise IngestError(f"{path}: manifest 'shards' must be a list")
    for key in ("assembly", "expected", "confidence"):
        if raw.get(key) is not None and not isinstance(raw[key], dict):
            raise IngestError(f"{path}: manifest {key!r} must be a mapping")
    for key in ("excluded", "unresolved"):
        if raw.get(key) is not None and not isinstance(raw[key], list):
            raise IngestError(f"{path}: manifest {key!r} must be a list")
    for key in ("confirmed_by_human", "exhaustive"):
        if raw.get(key) is not None and not isinstance(raw[key], bool):
            raise IngestError(f"{path}: manifest {key!r} must be boolean")
    expected = raw.get("expected") or {}
    if expected.get("sample_ids") is not None and not isinstance(expected["sample_ids"], list):
        raise IngestError(f"{path}: manifest expected.sample_ids must be a list")
    for index, entry in enumerate(raw.get("excluded") or []):
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) \
                or not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            raise IngestError(
                f"{path}: excluded[{index}] must be a mapping with non-empty path and reason strings")
    assembly = raw.get("assembly") or {}
    shards = []
    for index, sd in enumerate(raw.get("shards") or []):
        if not isinstance(sd, dict):
            raise IngestError(f"{path}: shards[{index}] must be a mapping")
        if not isinstance(sd.get("path"), str) or not sd["path"].strip():
            raise IngestError(f"{path}: shards[{index}].path must be a non-empty string")
        if sd.get("constants") is not None and not isinstance(sd["constants"], dict):
            raise IngestError(f"{path}: shards[{index}].constants must be a mapping")
        obs = sd.get("obs") or {}
        if not isinstance(obs, dict):
            raise IngestError(f"{path}: shards[{index}].obs must be a mapping")
        modality = sd.get("modality", "RNA")
        if modality not in MODALITIES:
            raise IngestError(
                f"{path}: shards[{index}].modality {modality!r} is unknown or case-mismatched; "
                f"expected one of {sorted(MODALITIES)}")
        shards.append(Shard(
            path=sd["path"],
            format=sd.get("format", "h5ad"),
            constants=sd.get("constants") or {},
            orientation=sd.get("orientation", "cells_x_genes"),
            layer=sd.get("layer"),
            count_type=sd.get("count_type", "raw_counts"),
            modality=modality,
            obs_path=obs.get("path"),
            obs_join_on=obs.get("join_on", "cell_id"),
            sha256=sd.get("sha256"),
        ))
    for sd, s in zip(raw.get("shards") or [], shards):
        s.sha256 = sd.get("sha256")
        s.obs_sha256 = sd.get("obs_sha256")
    return Manifest(
        shards=shards,
        expected_sample_ids=(raw.get("expected") or {}).get("sample_ids"),
        gene_axis=assembly.get("gene_axis", "require_identical"),
        cell_ids=assembly.get("cell_ids", "prefix_by_sample_id"),
        exhaustive=raw.get("exhaustive", True),
        excluded=raw.get("excluded") or [],
        confirmed_by_human=raw.get("confirmed_by_human", False),
        confirmed_digest=raw.get("confirmed_digest"),
        confidence=raw.get("confidence") or {},
        unresolved=raw.get("unresolved") or [],
    )


def semantic_digest(manifest: Manifest) -> str:
    """A sha256 over the ASSEMBLY-DETERMINING content of the manifest (paths, constants, obs joins,
    assembly policy, expected set) — everything that changes WHAT gets assembled. Excludes the file
    hashes and confirm bookkeeping, so a post-confirm edit to a constant (e.g. flipping WT<->KO) or a
    dropped shard changes the digest and is caught at audit."""
    payload = {
        "assembly": {"gene_axis": manifest.gene_axis, "cell_ids": manifest.cell_ids},
        "exhaustive": manifest.exhaustive,
        "expected_sample_ids": sorted(map(str, manifest.expected_sample_ids or [])),
        "excluded": sorted((e.get("path", "") for e in manifest.excluded)),
        "shards": [
            {"path": s.path, "format": s.format, "modality": s.modality, "count_type": s.count_type,
             "orientation": s.orientation, "layer": s.layer, "obs_path": s.obs_path,
             "obs_join_on": s.obs_join_on, "constants": dict(sorted(s.constants.items()))}
            for s in manifest.shards
        ],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def discover_matrix_files(folder) -> list:
    """Every candidate count matrix in a folder, as (path, format): h5ad (top + one level down) and
    counts/matrix CSV/TSV shards. Shared by init/scan/draft/exhaustive so they see the same files."""
    folder = Path(folder)
    h5 = sorted(folder.glob("*.h5ad")) + sorted(folder.glob("*/*.h5ad"))
    csv = []
    for pat in ("counts*", "matrix*"):
        for ext in (".csv", ".tsv"):
            csv += sorted(folder.glob(f"{pat}{ext}")) + sorted(folder.glob(f"*/{pat}{ext}"))
    return ([(p, "h5ad") for p in h5]
            + [(p, "csv" if p.suffix == ".csv" else "tsv") for p in sorted(set(csv))])


def draft_manifest(folder) -> Manifest:
    """The deterministic (no-LLM) layout draft: enumerate the multi-file shards so the human doesn't
    hand-list them. Each matrix becomes one shard with `sample_id` from its filename stem (a namespacing
    id, not a semantic label). The SEMANTIC constants (condition/replicate/batch) are left for the human
    to fill or Claude to propose — they cannot be read off a filename. Never confirmed."""
    folder = Path(folder)
    files = discover_matrix_files(folder)
    if len(files) < 2:
        raise ValueError(f"{folder}: draft_manifest is for multi-file analyses "
                         f"(found {len(files)} matrices — a single matrix needs no manifest).")
    shards, sample_ids = [], []
    for p, fmt in files:
        sid = p.stem
        sample_ids.append(sid)
        shards.append(Shard(path=p.relative_to(folder).as_posix(), format=fmt,
                            constants={"sample_id": sid}))
    return Manifest(shards=shards, expected_sample_ids=sample_ids, confirmed_by_human=False)


def write_manifest(manifest: Manifest, path) -> None:
    """Serialize a Manifest to `sc-referee.manifest.yaml` (unconfirmed until `sc-referee confirm`)."""
    def _shard(s: Shard) -> dict:
        d = {"path": s.path, "format": s.format, "orientation": s.orientation, "modality": s.modality,
             "count_type": s.count_type, "constants": s.constants}
        if s.layer:
            d["layer"] = s.layer
        if s.obs_path:
            d["obs"] = {"path": s.obs_path, "join_on": s.obs_join_on}
        if s.sha256:
            d["sha256"] = s.sha256
        if s.obs_sha256:
            d["obs_sha256"] = s.obs_sha256
        return d

    payload = {
        "manifest_version": 1,
        "confirmed_by_human": manifest.confirmed_by_human,
        "exhaustive": manifest.exhaustive,
        "expected": {"sample_ids": manifest.expected_sample_ids},
        "assembly": {"gene_axis": manifest.gene_axis, "cell_ids": manifest.cell_ids},
        "shards": [_shard(s) for s in manifest.shards],
    }
    if manifest.excluded:
        payload["excluded"] = manifest.excluded
    if manifest.confidence:
        payload["confidence"] = manifest.confidence
    if manifest.unresolved:
        payload["unresolved"] = manifest.unresolved      # persist so the human sees them at confirm
    if manifest.confirmed_digest:
        payload["confirmed_digest"] = manifest.confirmed_digest
    Path(path).write_text(yaml.safe_dump(payload, sort_keys=False))


def record_hashes(manifest: Manifest, folder, *, verified_hashes=None) -> Manifest:
    """Bind the confirmed scope to the bytes AND to the manifest's semantic content: record each
    shard's counts + obs file hash, and the semantic digest, so a later audit refuses if a file was
    replaced or the manifest was edited (e.g. a flipped condition constant) after confirmation."""
    folder = Path(folder)

    def _within(rel):
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            raise ValueError(f"{rel}: shard paths must be relative and within the folder.")
        return folder / rel

    for s in manifest.shards:
        if verified_hashes is not None:
            try:
                s.sha256 = verified_hashes[(s.path, "data")]
                s.obs_sha256 = (verified_hashes[(s.obs_path, "obs")] if s.obs_path else None)
            except KeyError as exc:
                raise ValueError(f"{s.path}: no verified ingest snapshot hash is available") from exc
        else:
            s.sha256 = hashlib.sha256(_within(s.path).read_bytes()).hexdigest()
            s.obs_sha256 = (hashlib.sha256(_within(s.obs_path).read_bytes()).hexdigest()
                            if s.obs_path else None)
    manifest.confirmed_digest = semantic_digest(manifest)
    return manifest
