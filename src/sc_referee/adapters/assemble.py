"""The deterministic multi-file assembler (spec v2 §6).

Reads the shards a confirmed manifest declares and emits ONE canonical `Bundle` — the same object
every check already consumes, so no check changes. It is *verified, not trusted*: it re-derives
counts-ness, gene alignment, and cell-id uniqueness rather than taking the manifest's word, and
refuses (raises `IngestError`) on anything that would silently corrupt or partial-scope the audit.

Increment 1: h5ad shards, `constants` materialized as obs columns, cell-ids prefixed by sample,
`gene_axis=require_identical` (same gene set, reordered by label), and the `expected.sample_ids`
completeness invariant. CSV shards, per-shard obs, orientation/modality handling, `intersect`, and
sha256 land in later increments.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

from sc_referee.adapters._common import detect_replicate_var, id_type
from sc_referee.adapters.anndata_adapter import read_anndata
from sc_referee.bundle import Bundle, Measure
from sc_referee.ingest import IngestError


def _resolve_within(folder: Path, rel_path: str) -> Path:
    """A shard path must be relative and resolve INSIDE the analysis root — no `..`, no absolute
    path, no symlink escaping the folder — so a confirmed manifest can't be pointed at external,
    mutable data while its provenance still looks local."""
    p = Path(rel_path)
    if p.is_absolute() or ".." in p.parts:
        raise IngestError(f"{rel_path}: shard paths must be relative and within the analysis root "
                          f"(no '..' or absolute paths).")
    root = folder.resolve()
    resolved = (folder / p).resolve()
    if resolved != root and root not in resolved.parents:
        raise IngestError(f"{rel_path}: resolves outside the analysis root — refusing to read "
                          f"external data through the manifest.")
    return folder / p


def _read_shard(shard, folder: Path, *, data_path=None, obs_data_path=None):
    _validate_shard_declaration(shard)
    path = _resolve_within(folder, shard.path)
    try:
        if shard.format == "h5ad":
            return read_anndata(data_path or path, layer=shard.layer)
        from sc_referee.adapters.csv_adapter import bundle_from_csv_files
        sep = "," if shard.format == "csv" else "\t"
        obs_path = (obs_data_path if shard.obs_path and obs_data_path is not None
                    else (_resolve_within(folder, shard.obs_path) if shard.obs_path else None))
        osep = "\t" if (shard.obs_path or "").endswith(".tsv") else ","
        return bundle_from_csv_files(data_path or path, obs_path, sep, osep,
                                     obs_join_on=shard.obs_join_on)
    except (OSError, UnicodeError, ValueError, pd.errors.ParserError,
            pd.errors.EmptyDataError) as e:
        raise IngestError(f"{shard.path}: {e}") from e


def _validate_shard_declaration(shard):
    if shard.orientation != "cells_x_genes":
        raise IngestError(f"{shard.path}: orientation={shard.orientation!r} is not supported in v1 "
                          f"(cells_x_genes only; declared transposes land next).")
    if shard.format not in ("h5ad", "csv", "tsv"):
        raise IngestError(f"{shard.path}: unsupported shard format {shard.format!r} "
                          f"(v1 assembles h5ad and csv/tsv shards; 10x/xlsx land next).")
    # Keep every declared shard on the DISCOVERY surface (top level or one subdir, right suffix, and
    # counts*/matrix* for CSV) so `exhaustive` discovery finds every matrix — otherwise a deeper or
    # oddly-named matrix (declared or a forgotten sibling) silently narrows the audited scope.
    if len(Path(shard.path).parts) > 2:
        raise IngestError(f"{shard.path}: shard paths must be at the top level or one subdirectory "
                          f"deep, so the exhaustive-scope check can discover them.")
    if not shard.path.endswith({"h5ad": ".h5ad", "csv": ".csv", "tsv": ".tsv"}.get(shard.format, "\0")):
        raise IngestError(f"{shard.path}: file suffix does not match declared format {shard.format!r}.")
    if shard.format == "h5ad" and shard.obs_path:
        raise IngestError(f"{shard.path}: a per-shard obs file is not supported for an h5ad shard — its "
                          f"design must live in the file's embedded .obs (or in manifest constants).")
    if shard.format in ("csv", "tsv") and not Path(shard.path).name.startswith(("counts", "matrix")):
        raise IngestError(f"{shard.path}: a CSV/TSV count matrix must be named counts*/matrix* so the "
                          f"exhaustive-scope check can find it. Rename it, or provide an h5ad.")


def _snapshot(source: Path, destination: Path) -> str:
    """Copy one opened byte stream while hashing; callers parse this exact private copy."""
    digest = hashlib.sha256()
    with source.open("rb") as src, destination.open("wb") as dst:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            dst.write(chunk)
    return digest.hexdigest()


def _snapshot_declared(folder: Path, declared: str, destination: Path) -> str:
    try:
        return _snapshot(_resolve_within(folder, declared), destination)
    except OSError as exc:
        raise IngestError(f"{declared}: could not read declared shard bytes: {exc}") from exc


def assemble(manifest, folder, *, confirming=False) -> Bundle:
    folder = Path(folder)
    if not manifest.shards:
        raise IngestError("manifest declares no shards — nothing to assemble.")

    # The same file listed twice would be assembled as two samples (duplicated data, contradictory
    # labels). Compare RESOLVED targets so `M1.h5ad` / `./M1.h5ad` / a same-target symlink all collide.
    resolved = [(folder / s.path).resolve() for s in manifest.shards]
    if len(set(resolved)) != len(resolved):
        seen, dups = set(), []
        for r, s in zip(resolved, manifest.shards):
            if r in seen and s.path not in dups:
                dups.append(s.path)
            seen.add(r)
        raise IngestError(f"duplicate shard path(s) {sorted(dups)} — the same file is listed more than "
                          f"once (possibly via `./` or a symlink).")

    # Every supported matrix must be accounted for even when a draft says exhaustive:false. A draft
    # may assemble all listed matrices, but only confirmed+bound exhaustive authority may exclude a
    # competing matrix from the audited RNA scope.
    from sc_referee.manifest import discover_matrix_files
    included = {s.path for s in manifest.shards}
    excluded = {e.get("path") for e in manifest.excluded if isinstance(e, dict)}
    on_disk = {p.relative_to(folder).as_posix() for p, _ in discover_matrix_files(folder)}
    unlisted = sorted(on_disk - included - excluded)
    if unlisted:
        raise IngestError(
            f"exhaustive manifest scope does not account for candidate matrix/matrices {unlisted}; list every matrix "
            "as a shard or, after confirmation, as an intentional exclusion")
    authority = (manifest.exhaustive and manifest.confirmed_by_human and manifest.confirmed_digest)
    if excluded and not (authority or (confirming and manifest.exhaustive)):
        raise IngestError(
            f"manifest exclusions {sorted(excluded)} cannot resolve competing matrix scope until "
            "the manifest is exhaustive, integrity-bound, and confirmed")
    declared_layers = [shard.path for shard in manifest.shards if shard.layer]
    if declared_layers and not (authority or (confirming and manifest.exhaustive)):
        raise IngestError(
            f"manifest layer declarations for {declared_layers} cannot resolve internal matrix "
            "ambiguity until the exhaustive manifest is integrity-bound and confirmed")

    # Only RNA enters the DEG matrix. Account for non-RNA declarations explicitly before excluding
    # them from RNA assembly; the closed vocabulary was validated by load_manifest.
    # so a normalized protein shard doesn't trip the raw-counts refuse; if nothing RNA remains, refuse.
    rna = [s for s in manifest.shards if s.modality == "RNA"]
    if not rna:
        raise IngestError("no RNA shards to assemble — an RNA DEG audit needs RNA count shards "
                          "(all declared shards are a non-RNA modality).")
    # --- integrity: a manifest that carries confirm bookkeeping is bound to its semantic content AND
    #     its files. A post-confirm edit (a flipped constant, a swapped shard, an edited obs table)
    #     would audit a DIFFERENT analysis than the human ratified -> refuse. (A draft has neither the
    #     digest nor the hashes, so this is skipped for unconfirmed manifests.)
    if manifest.confirmed_by_human:
        from sc_referee.manifest import semantic_digest
        # A confirmed manifest MUST carry its integrity fields — stripping them cannot be a bypass.
        if not manifest.confirmed_digest or any(s.sha256 is None for s in manifest.shards) \
                or any(s.obs_path and s.obs_sha256 is None for s in manifest.shards):
            raise IngestError(
                "confirmed manifest is missing its integrity digest/hashes — it was edited or written "
                "by an old version. Re-run `sc-referee confirm` to re-ratify it.")
        if semantic_digest(manifest) != manifest.confirmed_digest:
            raise IngestError(
                "the manifest was edited after confirmation — its content no longer matches the "
                "confirmed digest (a changed constant, path, exclusion, or assembly policy). Re-run "
                "`sc-referee confirm` to ratify the new layout.")
    # Snapshot and hash BEFORE parsing. Hashing path B and reopening path A is a TOCTOU bug; every
    # adapter below consumes only the immutable private bytes created from this single open stream.
    snapshots = tempfile.TemporaryDirectory(prefix="sc-referee-audit-")
    snap_paths = {}
    verified_hashes = {}
    try:
        root = Path(snapshots.name)
        for index, shard in enumerate(manifest.shards):
            _validate_shard_declaration(shard)
            data_snapshot = root / f"{index}-data{Path(shard.path).suffix}"
            actual = _snapshot_declared(folder, shard.path, data_snapshot)
            verified_hashes[(shard.path, "data")] = actual
            if shard.sha256 and actual != shard.sha256:
                raise IngestError(
                    f"{shard.path}: content changed since confirmation (sha256 {actual[:12]}… != "
                    f"declared {shard.sha256[:12]}…). Re-confirm before auditing.")
            obs_snapshot = None
            if shard.obs_path:
                obs_snapshot = root / f"{index}-obs{Path(shard.obs_path).suffix}"
                obs_actual = _snapshot_declared(folder, shard.obs_path, obs_snapshot)
                verified_hashes[(shard.obs_path, "obs")] = obs_actual
                if shard.obs_sha256 and obs_actual != shard.obs_sha256:
                    raise IngestError(
                        f"{shard.obs_path}: metadata changed since confirmation (sha256 drift). "
                        "Re-confirm before auditing.")
            snap_paths[id(shard)] = (data_snapshot, obs_snapshot)
        read = [(shard, _read_shard(
            shard, folder, data_path=snap_paths[id(shard)][0],
            obs_data_path=snap_paths[id(shard)][1])) for shard in rna]
    finally:
        snapshots.cleanup()

    # --- verify count-type: every RNA shard must be raw counts; a normalized/mixed shard refuses ---
    for s, b in read:
        if b.measure.kind != "counts":
            raise IngestError(
                f"{s.path}: matrix is {b.measure.kind}, not raw counts. The DEG recompute needs raw "
                f"integer counts in every shard; a normalized shard cannot silently join the matrix.")

    # --- gene axis: build the canonical gene order per policy; align each shard to it by LABEL ------
    first = list(read[0][1].measure.feature_index)
    if manifest.gene_axis == "require_identical":
        canon_set = set(first)
        for s, b in read:
            if set(b.measure.feature_index) != canon_set:
                raise IngestError(
                    f"{s.path}: its gene set differs from the first shard, but "
                    f"gene_axis=require_identical. Make the shards share one gene set, or declare "
                    f"gene_axis=intersect.")
        canonical = first
    elif manifest.gene_axis == "intersect":
        common = set(first)
        for _, b in read:
            common &= set(b.measure.feature_index)
        if not common:
            raise IngestError("gene_axis=intersect: the shards share no genes — there is no common "
                              "axis to assemble on (mismatched feature-id types or genome builds?).")
        canonical = [g for g in first if g in common]       # intersection, in the first shard's order
    else:
        raise IngestError(f"gene_axis={manifest.gene_axis!r} is not supported "
                          f"(require_identical | intersect).")

    # --- per-shard: materialize constants, prefix cell-ids, align gene columns --------------------
    mats, obses, sample_ids = [], [], []
    for s, b in read:
        feats = list(b.measure.feature_index)
        col = [feats.index(g) for g in canonical]                 # reorder columns by label
        mats.append(np.asarray(b.measure.counts)[:, col])

        obs = b.observations.copy()
        for key, value in s.constants.items():
            # A constant must not silently overwrite real, disagreeing metadata (e.g. a constant
            # condition=WT over an embedded column that varies) — that would mislabel cells.
            if key in obs.columns and not (obs[key].astype(str) == str(value)).all():
                raise IngestError(
                    f"{s.path}: constant {key}={value!r} disagrees with the shard's embedded '{key}' "
                    f"column (which is not uniformly {value!r}). Refusing to overwrite real metadata — "
                    f"drop the constant or fix the shard.")
            obs[key] = value                                      # file identity -> real obs column
        sid = str(s.constants.get("sample_id", s.path))
        sample_ids.append(sid)
        if manifest.cell_ids == "prefix_by_sample_id":
            obs.index = [f"{sid}:{c}" for c in obs.index]
        obses.append(obs)

    # --- distinct samples: two shards under one sample_id double-count cells under one label -------
    if len(set(sample_ids)) != len(sample_ids):
        dups = sorted({s for s in sample_ids if sample_ids.count(s) > 1})
        raise IngestError(
            f"duplicate sample_id(s) {dups} across shards — each shard must be a distinct sample, or "
            f"its cells are double-counted under one label. Give each shard a unique sample_id.")

    # --- completeness invariant: the assembled sample set must equal the declared one -------------
    if manifest.expected_sample_ids is not None:
        got, want = sorted(sample_ids), sorted(map(str, manifest.expected_sample_ids))
        if got != want:
            raise IngestError(
                f"assembled sample set {got} != expected {want} — a shard is missing, duplicated, or "
                f"mislabeled. Refusing rather than audit a partial or wrong scope.")

    counts = np.vstack(mats)
    obs_all = pd.concat(obses, axis=0)

    # --- global cell-id uniqueness (after namespacing) --------------------------------------------
    if obs_all.index.duplicated().any():
        dups = obs_all.index[obs_all.index.duplicated()].unique().tolist()
        raise IngestError(
            f"cell-id collision after assembly (e.g. {dups[:3]}) — prefixing did not make cells "
            f"unique. Distinct samples must have distinct sample_ids.")

    feat_meta = pd.DataFrame(index=canonical)
    feat_meta["id_type"] = id_type(canonical)
    bundle = Bundle(
        observations=obs_all,
        measure=Measure(kind="counts", counts=counts, long=None, feature_index=canonical),
        feature_metadata=feat_meta,
        replicate_var=detect_replicate_var(list(obs_all.columns)),
    )
    bundle.manifest_accounting = [
        {"path": shard.path,
         "modality": shard.modality,
         "disposition": ("included_in_rna" if shard.modality == "RNA" else "excluded_non_rna")}
        for shard in manifest.shards
    ]
    bundle.manifest_hashes = verified_hashes
    return bundle
