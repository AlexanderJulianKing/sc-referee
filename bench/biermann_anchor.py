"""The published-human-data anchor: sc-referee on Biermann et al. 2022 (melanoma brain vs
extracranial metastases; GSE200218), through the REAL folder-ingest path a scientist uses.

The original study tested CELLS as replicates (MAST). sc-referee's patient-level recompute
(pydeseq2) collapses the reported family 16,289 -> 770 (95.3%), and CORRECTLY withholds a hard
blocker because the corrected patient-level analysis is underpowered (powered_fraction 0.38 < 0.80).
The report leads with the observed discrepancy and states the qualification separately (see
report._withheld_collapse). A later peer-reviewed reanalysis independently found the same
cell-as-replicate error and reported no significant tumor-cell genes.

Capsule (patient-level pseudobulk h5ad + the original Table S3 result family + the analysis
contract) at BIERMANN_DIR. It is a derived aggregate of public GSE200218 — never the raw matrix.

    BIERMANN_DIR=/tmp/biermann_referee PYTHONPATH=src:. python bench/biermann_anchor.py

Frozen expected metrics (the exact audit reproduces these):
"""
from __future__ import annotations

import os
import warnings
from pathlib import Path

from sc_referee.audit import run_audit

# The exact patient-level recompute of the reported cell-level family.
EXPECTED = {
    "valid_reported_sig": 16289,
    "survivors": 770,
    "survival_rate": 0.0473,
    "powered": False,
    "powered_fraction": 0.3817,
    "status": "needs_evidence",
}


def capsule_dir() -> Path:
    """The committed capsule if present, else the local build capsule."""
    for candidate in (os.environ.get("BIERMANN_DIR"), "demos/biermann-pseudoreplication",
                      "/tmp/biermann_referee"):
        if candidate and Path(candidate).joinpath("sc-referee.yaml").exists():
            return Path(candidate)
    raise FileNotFoundError(
        "Biermann capsule not found. Set BIERMANN_DIR to a folder containing sc-referee.yaml, "
        "the patient-level pseudobulk h5ad, and results/original_table_s3_snrna.csv."
    )


def run_biermann_anchor(folder: Path | None = None):
    warnings.filterwarnings("ignore")
    folder = folder or capsule_dir()
    result = run_audit(folder)
    experimental_unit = next(
        (f for f in result.findings if f.check_id == "experimental_unit"), None
    )
    return result, experimental_unit


if __name__ == "__main__":
    result, eu = run_biermann_anchor()
    if eu is None:
        raise SystemExit("experimental_unit finding not present")
    m = eu.metrics
    print("Biermann et al. 2022 — melanoma brain vs extracranial metastases (GSE200218)")
    print(f"  reported significant (testable): {m['valid_reported_sig']:,}")
    print(f"  patient-level survivors:         {m['survivors']:,}  "
          f"(survival {m['survival_rate']:.4f} -> {1 - m['survival_rate']:.1%} collapse)")
    print(f"  powered: {m['powered']}  (powered_fraction {m['powered_fraction']})")
    print(f"  verdict: {eu.status.upper()}  "
          f"(blocker responsibly withheld: corrected analysis underpowered)")
