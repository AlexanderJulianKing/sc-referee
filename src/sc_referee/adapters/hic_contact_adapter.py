"""Canonical pre-extracted Hi-C contact-table adapter; no .cool/.hic parsing."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from sc_referee.bundle import HiCBundle, HiCContactData

CONTACTS_NAME = "hic_contacts.csv"
BINS_NAME = "hic_bins.csv"
REPORT_NAME = "hic_report.csv"


def _digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def _read(path: Path, *, string_columns=()):
    if not path.exists():
        return None
    dtype = {name: "string" for name in string_columns}
    return pd.read_csv(path, dtype=dtype or None)


def read_hic_contact_folder(folder) -> HiCBundle:
    folder = Path(folder)
    contacts_path = folder / CONTACTS_NAME
    bins_path = folder / BINS_NAME
    report_path = folder / REPORT_NAME
    contacts = _read(
        contacts_path, string_columns=("replicate", "condition", "bin_i", "bin_j"))
    bins = _read(bins_path, string_columns=("bin_id", "chrom"))
    reported = _read(
        report_path,
        string_columns=("genome_assembly", "bin_i", "bin_j", "reference", "test"),
    )
    present = [name for name, path in ((CONTACTS_NAME, contacts_path), (BINS_NAME, bins_path))
               if path.exists()]
    provenance = {
        "data": {
            "path": ", ".join(present) if present else None,
            "reason": "canonical pre-extracted Hi-C contacts + bin universe",
        }
    }
    if report_path.exists():
        provenance["reported"] = {
            "path": REPORT_NAME,
            "reason": "canonical report-bound Hi-C loop delta table",
        }
    return HiCBundle(
        hic=HiCContactData(
            contacts=contacts,
            bins=bins,
            contacts_digest=_digest(contacts_path),
            bins_digest=_digest(bins_path),
        ),
        reported_results=reported,
        reported_columns=[] if reported is None else list(map(str, reported.columns)),
        provenance=provenance,
    )


def validate_hic_design_against(bundle, design) -> None:
    """Type-level validation only; missing facts/data remain rich check findings, not config errors."""
    if not isinstance(bundle, HiCBundle) or design.analysis_type != "hic_loop_strength":
        raise TypeError("hic_loop_strength requires the parallel HiCBundle adapter")
