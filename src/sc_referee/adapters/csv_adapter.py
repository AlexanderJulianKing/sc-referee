"""CSV/TSV adapter — a count matrix + a cell-metadata table, emitting the canonical Bundle.

Raw formats (CSV, 10x mtx) don't carry the experimental design the way AnnData's `.obs` does, so
the design lives in a SEPARATE metadata file. Filenames are explicit (never guess which CSV is
which — that would violate the never-silently-guess-wrong stance):

    counts.{csv,tsv}  or  matrix.{csv,tsv}   — cells x genes, first column = cell_id, header = genes
    obs.{csv,tsv}  or  metadata.{csv,tsv}  or  cells.{csv,tsv}  or  coldata.{csv,tsv}  — the design

Non-integer values reuse item 2 (kind="normalized", counts=None).
"""
from __future__ import annotations

import csv as _csv
import re
from pathlib import Path

import pandas as pd

from sc_referee.adapters._common import detect_replicate_var, id_type, measure_from_matrix
from sc_referee.bundle import Bundle

COUNTS_NAMES = ("counts", "matrix")
OBS_NAMES = ("obs", "metadata", "cells", "coldata")
_SEP = {".csv": ",", ".tsv": "\t"}

# The first column of a counts CSV must be cell ids. We accept these labels for it (matched after
# stripping non-alphanumerics, so "Cell ID"/"cell-barcode"/"barcode_id" all pass), plus an empty/
# unnamed index (pandas renders it "Unnamed: 0"). Anything else (e.g. a gene name) signals a matrix
# exported with NO cell-id column, which would use gene expression as cell ids.
_CELL_ID_HEADERS = {"cellid", "cell", "cells", "barcode", "barcodes", "cellbarcode", "barcodeid",
                    "cellbarcodes", "index", "obs", "obsname", "obsnames", "cellname", "cellnames"}


def _looks_like_cell_id_header(name) -> bool:
    n = re.sub(r"[^a-z0-9]", "", str(name).strip().lower())
    return n == "" or n.startswith("unnamed") or n in _CELL_ID_HEADERS


def _find(folder: Path, stems) -> tuple:
    for stem in stems:
        for ext, sep in _SEP.items():
            p = folder / f"{stem}{ext}"
            if p.exists():
                return p, sep
    return None, None


def raw_header(path, sep=None) -> list[str]:
    """Read one real UTF-8/BOM/quoting-aware header before pandas can mangle duplicates."""
    path = Path(path)
    delimiter = sep or _SEP.get(path.suffix.lower())
    if delimiter is None:
        raise ValueError(f"{path}: unsupported delimited-table suffix")
    try:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            header = next(_csv.reader(fh, delimiter=delimiter))
    except StopIteration as exc:
        raise ValueError(f"{path}: empty table (no header)") from exc
    if not header or not any(str(value).strip() for value in header):
        raise ValueError(f"{path}: empty table header")
    return list(map(str, header))


def _duplicate_labels(labels) -> list[str]:
    seen, duplicates = set(), []
    for label in labels:
        if label in seen and label not in duplicates:
            duplicates.append(label)
        seen.add(label)
    return duplicates


def find_counts_file(folder) -> "Path | None":
    """The count-matrix path if a CSV/TSV analysis is present — used by ingest to route."""
    return _find(Path(folder), COUNTS_NAMES)[0]


def find_counts_candidates(folder) -> list:
    """EVERY top-level counts/matrix file (any supported ext) — used by ingest to detect ambiguity
    (more than one candidate matrix means the scope is not self-evident)."""
    folder = Path(folder)
    return [folder / f"{stem}{ext}"
            for stem in COUNTS_NAMES for ext in _SEP
            if (folder / f"{stem}{ext}").exists()]


def bundle_from_csv_files(counts_path, obs_path=None, csep=",", osep=",", obs_join_on="cell_id") -> Bundle:
    """Build a Bundle from ONE counts file (+ optional per-cell metadata file). Shared by the folder
    path (`read_csv`) and the multi-file assembler. `obs_path=None` -> obs is the bare cell index (a
    shard whose design columns come from manifest constants); `obs_join_on` names the obs column that
    keys to the count cell_ids (default: the first column)."""
    counts_path = Path(counts_path)
    # Read the RAW header (BOM-stripped, quoting-aware) to (a) detect duplicate genes pandas would
    # silently rename `g0,g0`->`g0,g0.1`, and (b) sanity-check the first column really is cell ids.
    counts_header = raw_header(counts_path, csep)
    raw_genes = counts_header[1:]
    if not _looks_like_cell_id_header(counts_header[0]):
        raise ValueError(f"{counts_path.name}: the first column header {counts_header[0]!r} is not a "
                         f"recognized cell-id label — a matrix with no cell_id column would use gene "
                         f"expression as cell ids. The first column must be cell_ids.")
    if len(set(raw_genes)) != len(raw_genes):
        seen, dups = set(), []
        for g in raw_genes:
            if g in seen and g not in dups:
                dups.append(g)
            seen.add(g)
        raise ValueError(f"{counts_path.name}: duplicate gene column(s) {dups[:3]} in the header — "
                         f"pandas would split one gene across features. Make gene columns unique.")
    # Read the cell_id column as STRING (via pandas' OWN first-column name, so a BOM or unnamed index
    # still matches) so numeric-looking ids don't collapse (`001` and `1` -> int 1).
    pandas_cols = pd.read_csv(counts_path, sep=csep, nrows=0, encoding="utf-8-sig").columns
    counts_df = pd.read_csv(counts_path, sep=csep, index_col=0, encoding="utf-8-sig",
                           dtype={pandas_cols[0]: str})
    counts_df.index = counts_df.index.astype(str)
    numeric = counts_df.apply(pd.to_numeric, errors="coerce")
    introduced_null = numeric.isna() & ~counts_df.isna()
    if introduced_null.any().any():
        row, col = introduced_null.stack()[lambda values: values].index[0]
        raise ValueError(
            f"{counts_path.name}: nonnumeric count value at cell {row!r}, feature {col!r}; "
            "count matrices must contain numeric values")
    counts_df = numeric

    # Orientation: verify when an axis is typed. If the ROW index looks like Ensembl GENE ids, this is
    # a genes×cells (transposed) matrix read as cells×genes — refuse rather than scramble it.
    if id_type(list(map(str, counts_df.index))) in ("ensembl", "ensembl_mouse"):
        raise ValueError(
            f"{counts_path.name}: the row index looks like GENE ids (Ensembl) — this appears to be a "
            f"genes×cells (transposed) matrix. Provide cells×genes (first column = cell_id).")

    # Cell-id integrity — a duplicated or mismatched index silently double-counts or drops cells,
    # auditing the wrong scope. Refuse rather than reindex over the problem.
    if counts_df.index.duplicated().any():
        dups = counts_df.index[counts_df.index.duplicated()].unique().tolist()
        raise ValueError(
            f"{counts_path.name}: duplicate cell_id(s) in the count matrix (e.g. {dups[:3]}). "
            f"Each cell must appear once, or it is double-counted.")

    if obs_path is not None:
        obs_path = Path(obs_path)
        obs_raw = raw_header(obs_path, osep)
        duplicates = _duplicate_labels(obs_raw)
        if duplicates:
            raise ValueError(
                f"{obs_path.name}: duplicate metadata header(s) {duplicates[:3]}; refusing before "
                "pandas can rename them and silently bind the wrong design column")
        obs_pandas_cols = list(pd.read_csv(obs_path, sep=osep, nrows=0, encoding="utf-8-sig").columns)
        # key the metadata by the DECLARED join column; an EXPLICIT key that is absent is a typo -> refuse
        # (only the default `cell_id` silently falls back to the first column).
        if obs_join_on in obs_raw:
            pos = obs_raw.index(obs_join_on)
        elif obs_join_on and obs_join_on != "cell_id":
            raise ValueError(f"{obs_path.name}: the declared obs join key {obs_join_on!r} is not a "
                             f"column (columns: {obs_raw}). Fix the manifest's obs.join_on.")
        else:
            pos = 0
        key = obs_pandas_cols[pos]                            # pandas' own name (handles BOM/unnamed)
        obs = pd.read_csv(obs_path, sep=osep, encoding="utf-8-sig", dtype={key: str}).set_index(key)
        obs.index = obs.index.astype(str)
        if obs.index.duplicated().any():
            dups = obs.index[obs.index.duplicated()].unique().tolist()
            raise ValueError(
                f"{obs_path.name}: duplicate cell_id(s) in the metadata (e.g. {dups[:3]}); cannot align to cells.")
        counts_ids, obs_ids = set(counts_df.index), set(obs.index)
        missing = [c for c in counts_df.index if c not in obs_ids]
        if missing:
            raise ValueError(
                f"{obs_path.name} is missing metadata for {len(missing)} cell(s) in {counts_path.name} "
                f"(e.g. {missing[:3]}). The cell_id index must match.")
        extra = [c for c in obs.index if c not in counts_ids]
        if extra:
            raise ValueError(
                f"{obs_path.name}: describes {len(extra)} cell(s) absent from {counts_path.name} "
                f"(e.g. {extra[:3]}). sc-referee will not audit a subset of your metadata's cells — a "
                f"global metadata table over one matrix hides a partial-scope audit. Subset the metadata "
                f"to the matrix's cells, or declare a manifest.")
        obs = obs.reindex(counts_df.index)                  # a pure reorder (sets equal, both unique)
    else:
        obs = pd.DataFrame(index=counts_df.index)           # constants will supply the design columns

    feat_idx = list(map(str, counts_df.columns))
    feature_metadata = pd.DataFrame(index=feat_idx)
    feature_metadata["id_type"] = id_type(feat_idx)
    return Bundle(
        observations=obs,
        measure=measure_from_matrix(counts_df.to_numpy(), feat_idx),
        feature_metadata=feature_metadata,
        replicate_var=detect_replicate_var(list(obs.columns)),
    )


def read_csv(folder) -> Bundle:
    folder = Path(folder)
    counts_path, csep = _find(folder, COUNTS_NAMES)
    if counts_path is None:
        raise FileNotFoundError(
            f"{folder}: no count matrix found. Expected one of "
            f"{[f'{s}.csv' for s in COUNTS_NAMES]} (cells x genes, first column = cell_id).")
    obs_candidates = [folder / f"{stem}{ext}" for stem in OBS_NAMES for ext in _SEP
                      if (folder / f"{stem}{ext}").is_file()]
    if not obs_candidates:
        raise FileNotFoundError(
            f"{folder}: found {counts_path.name} but no cell-metadata table. Add one of "
            f"{[f'{s}.csv' for s in OBS_NAMES]} (first column = cell_id, plus the design columns "
            f"like donor_id / condition).")
    if len(obs_candidates) > 1:
        from sc_referee.ingest import IngestError
        names = ", ".join(path.name for path in obs_candidates)
        raise IngestError(
            f"{folder}: competing metadata tables found ({names}); sc-referee will not choose by "
            "filename precedence. Keep exactly one supported metadata table.")
    obs_path = obs_candidates[0]
    osep = _SEP[obs_path.suffix.lower()]
    return bundle_from_csv_files(counts_path, obs_path, csep, osep)
