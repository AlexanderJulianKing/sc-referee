"""GB-P07 as a first-class compiled-analysis capsule for the friendly browser flow.

This module supplies the three GB-P07-specific pieces the general capsule bridge needs:

* ``canned_gbp07_proposal`` — the prepared, evidence-bound structural proposal (so the recording needs no
  live model call);
* ``prepare_gbp07_capsule`` — the ONE-TIME, off-camera materialization: it writes the canonical compiler
  artifacts from the released benchmark archive into a gitignored folder and emits the typed capsule
  manifest with recorded provenance digests; and
* the ``CapsuleKind`` registration that lets the manifest's ``capsule_kind`` resolve to a runner.

Nothing here runs during the demo except through the ordinary folder-picker path: after preparation, the
reviewer simply selects ``demos/genebench-gbp07`` in the browser.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping

import yaml

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
from sc_referee.compiler.capsule_kinds import CapsuleKind, register_capsule_kind
from sc_referee.compiler.capsule_manifest import CAPSULE_MANIFEST_NAME, CAPSULE_SCHEMA
from sc_referee.compiler.inventory import Inventory
from sc_referee.compiler.pipeline import CompileAuditResult, run_compile_audit
from sc_referee.derivations.gbp07_compile import gbp07_zip_path


CAPSULE_KIND = "gbp07_ambient_contamination/v1"
ARTIFACTS_DIRNAME = "raw_compile_input"
_ZIP_MEMBERS = ("cells.csv.gz", "donors.csv.gz", "empty_drops.csv.gz")

# Deterministic context artifacts (written as fixed bytes so recorded digests are stable).
_METHOD_TXT = (
    "Fit donor-level eQTL models using genotype column g. "
    "The target coefficient is genotype for CXCL10. "
    "No ambient adjustment was included. "
    "Apply genebench_gbp07_public_estimator/v1 to empty droplets.\n"
).encode("utf-8")
_SUBMISSION_CSV = b"feature,target_coefficient,submitted_effect\nCXCL10,genotype,0.4839\n"

# Fixed, benchmark-free boundary appended to a flagged finding's verdict (presentation only). The external
# reference answer is deliberately NOT modelled here — it belongs to demo-validation narration, never to a
# product payload — so nothing user-facing carries the held-out benchmark truth.
_FINDING_BOUNDARY = (
    "This establishes that the confirmed adjustment is missing, but not how the omission affected "
    "the reported coefficient."
)


def canned_gbp07_proposal(inventory: Inventory) -> BindingProposal:
    """The bundled, evidence-bound structural proposal used instead of a live model call."""

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


def _proposal_id(inventory: Inventory) -> str:
    seed = f"gbp07-offline-canned-v1\0{inventory.inventory_identity}".encode("utf-8")
    return "sha256:" + hashlib.sha256(seed).hexdigest()


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def run_gbp07_capsule(
    artifacts_dir: str | Path,
    answers: Mapping[object, object],
) -> CompileAuditResult:
    """Run this kind through the existing compiler with its prepared structural proposal."""

    return run_compile_audit(artifacts_dir, answers=answers, proposer=canned_gbp07_proposal)


def materialize_gbp07_artifacts(zip_path: str | Path, artifacts_dir: str | Path) -> dict[str, str]:
    """Write the five canonical compiler artifacts and return their recorded digests.

    Raises FileNotFoundError if the released archive is absent; the caller reports that honestly.
    """
    from zipfile import ZipFile

    archive_path = Path(zip_path).expanduser()
    if not archive_path.exists():
        raise FileNotFoundError(f"GB-P07 benchmark archive is not available at {archive_path}")
    folder = Path(artifacts_dir)
    folder.mkdir(parents=True, exist_ok=True)
    written: dict[str, bytes] = {}
    with ZipFile(archive_path) as archive:
        for member in _ZIP_MEMBERS:
            written[member] = archive.read(member)
    written["submission.csv"] = _SUBMISSION_CSV
    written["method.txt"] = _METHOD_TXT
    for name, raw in written.items():
        (folder / name).write_bytes(raw)
    return {name: _sha256(raw) for name, raw in sorted(written.items())}


def _gbp07_manifest(digests: dict[str, str]) -> dict:
    # Neutral, product-facing framing: an ordinary eQTL analysis whose folder Referee reconstructs and
    # then asks the scientific context it needs. Nothing here names a benchmark, a suspected defect, or a
    # verdict — the reviewer must experience this as an ordinary analysis folder.
    return {
        "capsule_schema": CAPSULE_SCHEMA,
        "capsule_kind": CAPSULE_KIND,
        "title": "CXCL10 eQTL analysis",
        "analysis": "eqtl",
        "reconstruction": (
            "I read this as a donor-level eQTL analysis estimating the association between genotype "
            "and CXCL10 expression. Is that right?"
        ),
        "presentation": {
            "claim_title": "CXCL10 expression ~ genotype",
            "recognition": "Genotype association with CXCL10 expression, evaluated per donor.",
            "facts": [
                {"label": "Biological replicate", "value": "donor"},
                {"label": "Analysis level", "value": "donor"},
            ],
        },
        "artifacts_dir": ARTIFACTS_DIRNAME,
        "provenance": {
            "source": (
                "GeneBench-Pro GB-P07 (external benchmark; released bytes are not redistributed)"
            ),
            "materialized_by": "sc-referee capsule preparation",
            "artifacts": digests,
        },
        "questions": [
            {"group": "Measurement",
             "prompt": "Is the HBB column a genuine measurement of ambient-RNA contamination in "
                       "these cells?",
             "why": "Referee would treat this column as the contamination signal; if it is not a real "
                    "ambient measurement, a confounding check on it would be meaningless.",
             "default": "yes"},
            {"group": "Timing",
             "prompt": "Was that contamination present before genotype — that is, it is not a "
                       "downstream consequence of genotype?",
             "why": "Contamination caused by genotype would be a mediator, not a confounder, and must "
                    "not be adjusted for.",
             "default": "yes"},
            {"group": "Estimand",
             "prompt": "For the effect this analysis targets, is adjusting for ambient-RNA "
                       "contamination a required part of the design?",
             "why": "Whether the contamination basis must appear in the fitted design depends on the "
                    "estimand you are after.",
             "default": "yes"},
            {"group": "Authority",
             "prompt": "Do you have the scientific authority to confirm this measurement and its "
                       "causal scope?",
             "why": "Referee will only ratify a confounding premise a qualified person stands behind.",
             "default": "yes"},
        ],
    }


def prepare_gbp07_capsule(folder: str | Path, zip_path: str | Path | None = None) -> Path:
    """One-time, off-camera preparation: materialize artifacts + write the capsule manifest.

    After this, ``folder`` (e.g. ``demos/genebench-gbp07``) is a self-contained capsule the reviewer can
    select in the browser with no env var or CLI ceremony. Returns the manifest path.
    """
    root = Path(folder)
    root.mkdir(parents=True, exist_ok=True)
    digests = materialize_gbp07_artifacts(
        gbp07_zip_path() if zip_path is None else zip_path, root / ARTIFACTS_DIRNAME)
    manifest_path = root / CAPSULE_MANIFEST_NAME
    manifest_path.write_text(yaml.safe_dump(_gbp07_manifest(digests), sort_keys=False, allow_unicode=True))
    return manifest_path


register_capsule_kind(CapsuleKind(
    kind=CAPSULE_KIND, runner=run_gbp07_capsule, finding_boundary=_FINDING_BOUNDARY))
