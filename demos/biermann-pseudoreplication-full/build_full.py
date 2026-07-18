"""Rebuild the Biermann audit from the official full public processed count matrix.

Large source and output files stay local. The compact sibling capsule remains the quick demo; this
builder is the auditable lineage proof and exercises Referee's sparse full-cell ingestion path.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
import urllib.request

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.io import mmread


HERE = Path(__file__).resolve().parent
COMPACT = HERE.parent / "biermann-pseudoreplication"
SOURCE = HERE / "source"
OUTPUT = HERE / "biermann_tumor_cells_full.h5ad"
PROVENANCE = HERE / "provenance.json"

BASE = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE200nnn/GSE200218/suppl"
FILES = {
    "counts": "GSE200218_sc_sn_counts.mtx.gz",
    "genes": "GSE200218_sc_sn_gene_names.csv.gz",
    "metadata": "GSE200218_sc_sn_metadata.csv.gz",
}
EXPECTED_SHA256 = {
    "counts": "0fd38ec2f2523e88479d7d01dd879a21c398a57d1cfb03d2c0bec5f1f65d6f19",
    "genes": "d6e5de2c92e857f8e00816897e5486bda46eb231b3c730eca7230a3c430115ad",
    "metadata": "950a8d8b636544126249253e30c331c07e99167c8da7bd9ee63d9b79d6913c93",
}
OBS_COLUMNS = (
    "orig.ident", "patient", "ID", "batch", "sequencing", "organ", "doublet",
    "malignant", "cell_type_main", "cell_type_fine",
)


def sha256(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(name: str, destination: Path) -> None:
    if destination.exists():
        print(f"using existing {destination} ({destination.stat().st_size / 2**20:,.1f} MiB)")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    url = f"{BASE}/{name}"
    print(f"downloading {url}")
    try:
        with urllib.request.urlopen(url) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output, length=8 * 1024 * 1024)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def load_metadata(path: Path) -> pd.DataFrame:
    metadata = pd.read_csv(
        path, index_col=0, low_memory=False,
        usecols=lambda column: column.startswith("Unnamed:") or column in OBS_COLUMNS,
    )
    missing = sorted(set(OBS_COLUMNS) - set(metadata.columns))
    if missing:
        raise ValueError(f"official metadata is missing required columns: {missing}")
    if len(metadata) != 145_555 or metadata.index.has_duplicates:
        raise ValueError(
            f"unexpected metadata ledger: {len(metadata):,} rows, "
            f"duplicates={metadata.index.has_duplicates}"
        )
    return metadata.loc[:, OBS_COLUMNS]


def collapse_duplicate_gene_columns(matrix, genes: pd.Index):
    unique = pd.Index(pd.unique(genes), dtype=str)
    codes = unique.get_indexer(genes)
    if (codes < 0).any():
        raise ValueError("could not map the GEO gene ledger onto its unique ordered ledger")
    mapping = sparse.csr_matrix(
        (np.ones(len(genes), dtype=np.int8), (np.arange(len(genes)), codes)),
        shape=(len(genes), len(unique)),
    )
    return (matrix @ mapping).tocsr(), unique


def patient_aggregate(matrix, obs: pd.DataFrame, genes: pd.Index) -> ad.AnnData:
    patients = pd.Index(pd.unique(obs["patient"].astype(str)), name="patient")
    rows = []
    organs = []
    patient_values = obs["patient"].astype(str).to_numpy()
    for patient in patients:
        positions = np.flatnonzero(patient_values == patient)
        rows.append(np.asarray(matrix[positions].sum(axis=0)).ravel())
        values = obs.iloc[positions]["organ"].dropna().astype(str).unique()
        if len(values) != 1:
            raise ValueError(f"patient {patient!r} does not have exactly one organ label: {values}")
        organs.append(values[0])
    counts = np.vstack(rows)
    aggregate_obs = pd.DataFrame({"organ": organs, "patient": patients}, index=patients.copy())
    aggregate_obs.index.name = "cell_id"
    return ad.AnnData(X=counts, obs=aggregate_obs, var=pd.DataFrame(index=genes.copy()))


def assert_same_compact(rebuilt: ad.AnnData) -> dict:
    compact = ad.read_h5ad(COMPACT / "patient_pseudobulk_counts.h5ad")
    same_genes = rebuilt.var_names.equals(compact.var_names)
    same_obs = rebuilt.obs.astype(str).equals(compact.obs.astype(str))
    same_counts = np.array_equal(np.asarray(rebuilt.X), np.asarray(compact.X))
    result = {"genes": same_genes, "observations": same_obs, "counts": same_counts}
    if not all(result.values()):
        raise ValueError(f"full-data rebuild does not reproduce the compact capsule: {result}")
    return result


def copy_audit_contract() -> None:
    for relative in (
        Path("sc-referee.yaml"), Path("original_analysis.R"),
        Path("results/original_table_s3_snrna.csv"),
    ):
        destination = HERE / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(COMPACT / relative, destination)


def build(*, force: bool = False) -> None:
    SOURCE.mkdir(parents=True, exist_ok=True)
    paths = {key: SOURCE / filename for key, filename in FILES.items()}
    for path in paths.values():
        download(path.name, path)

    source_digests = {key: sha256(path) for key, path in paths.items()}
    for key, expected in EXPECTED_SHA256.items():
        if source_digests[key] != expected:
            raise ValueError(
                f"{paths[key].name} digest changed: expected {expected}, got {source_digests[key]}"
            )

    if OUTPUT.exists() and not force:
        raise FileExistsError(f"{OUTPUT} already exists; pass --force to rebuild it")

    metadata = load_metadata(paths["metadata"])
    genes = pd.Index(pd.read_csv(paths["genes"]).iloc[:, 0].astype(str), dtype=str)
    if len(genes) != 35_652:
        raise ValueError(f"expected 35,652 source genes, found {len(genes):,}")

    selected = metadata["sequencing"].eq("Single nuclei") & metadata["cell_type_main"].eq("Tumor cells")
    if int(selected.sum()) != 82_783:
        raise ValueError(f"expected 82,783 selected tumor nuclei, found {int(selected.sum()):,}")

    print("reading the official 35,652 x 145,555 sparse Matrix Market file")
    with gzip.open(paths["counts"], "rb") as handle:
        genes_by_cells = mmread(handle)
    if genes_by_cells.shape != (35_652, 145_555):
        raise ValueError(f"unexpected count-matrix shape: {genes_by_cells.shape}")

    # Transposing a CSC matrix yields the CSR layout Referee needs for efficient cell-group sums.
    cells_by_genes = genes_by_cells.tocsc().T.tocsr()
    del genes_by_cells
    tumor = cells_by_genes[np.flatnonzero(selected.to_numpy())]
    del cells_by_genes
    tumor, unique_genes = collapse_duplicate_gene_columns(tumor, genes)
    tumor_obs = metadata.loc[selected].copy()
    # GEO metadata mixes missing values with strings in fields such as `batch`. AnnData/HDF5 needs
    # one stable transport type; these columns are descriptive labels, not numeric measurements.
    for column in tumor_obs.columns:
        tumor_obs[column] = tumor_obs[column].fillna("NA").astype(str)

    rebuilt = patient_aggregate(tumor, tumor_obs, unique_genes)
    equality = assert_same_compact(rebuilt)
    print("verified: full public matrix exactly reproduces the committed patient-level capsule")

    full = ad.AnnData(X=tumor, obs=tumor_obs, var=pd.DataFrame(index=unique_genes))
    full.uns["sc_referee_source"] = {
        "accession": "GSE200218",
        "filter": 'sequencing == "Single nuclei" and cell_type_main == "Tumor cells"',
        "source_cells": 145_555,
        "selected_cells": 82_783,
    }
    temporary = OUTPUT.with_suffix(".h5ad.part")
    temporary.unlink(missing_ok=True)
    print(f"writing sparse full-cell audit input to {OUTPUT}")
    full.write_h5ad(temporary, compression="gzip")
    temporary.replace(OUTPUT)
    copy_audit_contract()

    record = {
        "schema_version": 1,
        "accession": "GSE200218",
        "source": {
            key: {
                "url": f"{BASE}/{FILES[key]}",
                "bytes": paths[key].stat().st_size,
                "sha256": source_digests[key],
            }
            for key in FILES
        },
        "matrix": {
            "source_shape_genes_by_cells": [35_652, 145_555],
            "source_nonzero_entries": 417_902_887,
            "filter": {"sequencing": "Single nuclei", "cell_type_main": "Tumor cells"},
            "output_shape_cells_by_genes": [82_783, 35_650],
            "duplicate_source_gene_labels_summed": ["1-Mar", "2-Mar"],
            "output_path": OUTPUT.name,
            "output_bytes": OUTPUT.stat().st_size,
            "output_sha256": sha256(OUTPUT),
        },
        "compact_capsule_exact_match": equality,
        "expected_audit": {
            "reported_significant": 16_289,
            "patient_level_survivors": 770,
            "survival_rate": 0.0473,
        },
    }
    PROVENANCE.write_text(json.dumps(record, indent=2) + "\n")
    print(f"wrote {PROVENANCE}")
    referee = Path(sys.executable).with_name("sc-referee")
    print(f"next: {referee} audit {HERE} --json {HERE / 'full-audit.json'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="replace an existing full H5AD")
    args = parser.parse_args()
    build(force=args.force)


if __name__ == "__main__":
    main()
