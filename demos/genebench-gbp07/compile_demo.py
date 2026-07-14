"""Runnable end-to-end GB-P07 compiler demo, with an offline structural proposal fallback."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
from zipfile import BadZipFile, ZipFile

import pandas as pd

from sc_referee.compiler.binding_proposal import (
    BindingProposal,
    Destination,
    Evidence,
    Locator,
    Proposer,
    RequestedBinding,
    SCHEMA_ID,
    TOOL_SCHEMA_ID,
)
from sc_referee.compiler.inventory import Inventory
from sc_referee.compiler.pipeline import run_compile_audit
from sc_referee.csp_contracts.contamination_condensed_ceremony import (
    CondensedAnswer,
    CondensedGroup,
)
from sc_referee.derivations.gbp07_compile import gbp07_zip_path


RAW_FOLDER = Path(__file__).with_name("raw_compile_input")
MEMBERS = ("cells.csv.gz", "donors.csv.gz", "empty_drops.csv.gz")
METHOD = (
    "Fit donor-level eQTL models using genotype column g. "
    "The target coefficient is genotype for CXCL10. "
    "No ambient adjustment was included. "
    "Apply genebench_gbp07_public_estimator/v1 to empty droplets.\n"
)


def build_raw_folder(archive_path: Path, folder: Path = RAW_FOLDER) -> Path:
    """Idempotently materialize the raw-shaped five-file compiler input."""

    folder.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive_path) as archive:
        for member in MEMBERS:
            (folder / member).write_bytes(archive.read(member))
    pd.DataFrame({
        "feature": ["CXCL10"],
        "target_coefficient": ["genotype"],
        "submitted_effect": [0.4839],
    }).to_csv(folder / "submission.csv", index=False)
    (folder / "method.txt").write_text(METHOD, encoding="utf-8")
    return folder


def _proposal_id(inventory: Inventory) -> str:
    seed = f"gbp07-offline-canned-v1\0{inventory.inventory_identity}".encode("utf-8")
    return "sha256:" + hashlib.sha256(seed).hexdigest()


def canned_gbp07_proposal(inventory: Inventory) -> BindingProposal:
    """Return the bundled, evidence-bound structural proposal used when Claude is offline."""

    artifacts = {item.relative_path: item for item in inventory.artifacts}

    def evidence(path: str, kind: str, value: str) -> tuple[Evidence, ...]:
        artifact = artifacts[path]
        return (Evidence(
            artifact_identity=artifact.artifact_identity,
            path=path,
            locator=Locator(kind=kind, value=value),
            evidence_digest=artifact.artifact_identity,
        ),)

    values = (
        ("analysis-type", "design", "analysis_type", "eqtl",
         evidence("method.txt", "documentation_span", "eQTL")),
        ("cell-table", "detector_input", "cell_table", {
            "artifact_path": "cells.csv.gz",
            "columns": {"cell_id": "cell_id", "donor": "donor", "total_umi": "total_umi", "hbb": "HBB"},
        }, evidence("cells.csv.gz", "header", "cell_id")),
        ("donor-table", "detector_input", "donor_table", {
            "artifact_path": "donors.csv.gz",
            "columns": {"donor": "donor", "genotype": "g"},
        }, evidence("donors.csv.gz", "header", "g")),
        ("empty-table", "empty_droplet", "empty_droplet_table", {
            "artifact_path": "empty_drops.csv.gz",
            "columns": {
                "total_umi": "total_umi",
                "panel": {gene: gene for gene in ("HBB", "IFI6", "ISG15", "LST1", "CXCL10")},
            },
        }, evidence("empty_drops.csv.gz", "header", "total_umi")),
        ("genotype-column", "design", "genotype_column", "g",
         evidence("donors.csv.gz", "header", "g")),
        ("target-feature", "design", "target_feature", "CXCL10",
         evidence("submission.csv", "table_cell", "feature=CXCL10")),
        ("submitted-result", "reported_claim", "submitted_result_artifact", "submission.csv",
         evidence("submission.csv", "header", "submitted_effect")),
        ("target-coefficient", "reported_claim", "target_coefficient", "genotype",
         evidence("method.txt", "documentation_span", "target coefficient is genotype")),
        ("fitted-method", "fitted_design", "method_evidence_span",
         "Fit donor-level eQTL models using genotype column g. No ambient adjustment was included.",
         evidence("method.txt", "documentation_span", "No ambient adjustment was included.")),
        ("derivation", "detector_input", "derivation_id",
         "genebench_gbp07_public_estimator/v1",
         evidence("method.txt", "documentation_span", "genebench_gbp07_public_estimator/v1")),
    )
    bindings = tuple(RequestedBinding(
        binding_id=binding_id,
        destination=Destination(authority, field),
        candidate_value=value,
        confidence="high",
        evidence=binding_evidence,
    ) for binding_id, authority, field, value, binding_evidence in values)
    sources = tuple({
        "artifact_identity": artifact.artifact_identity,
        "path": artifact.relative_path,
        "kind": artifact.kind,
    } for artifact in inventory.artifacts)
    return BindingProposal(
        schema_id=SCHEMA_ID,
        proposal_id=_proposal_id(inventory),
        revision=2,
        inventory_identity=inventory.inventory_identity,
        confirmed_organizational_bindings=False,
        source_artifacts=sources,
        requested_bindings=bindings,
        proposer=Proposer(
            kind="claude",
            model="bundled-canned-proposal-v1",
            tool_schema_id=TOOL_SCHEMA_ID,
        ),
    )


def main() -> int:
    archive_path = gbp07_zip_path()
    if not archive_path.exists():
        print(
            f"GB-P07 bytes are unavailable at {archive_path}. "
            "Set GBP07_ZIP to GB-P07-data.zip; demo skipped."
        )
        return 0
    try:
        folder = build_raw_folder(archive_path)
    except (BadZipFile, KeyError, OSError) as exc:
        print(f"GB-P07 bytes could not be prepared ({exc}); demo skipped.")
        return 0

    answers = {group: CondensedAnswer.YES for group in CondensedGroup}
    injected = None if os.environ.get("ANTHROPIC_API_KEY") else canned_gbp07_proposal
    result = run_compile_audit(folder, answers=answers, proposer=injected)
    print(result.summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
