from __future__ import annotations

import jsonschema
import pandas as pd
import pytest

from sc_referee.compiler.binding_proposal import (
    BindingConflict,
    BindingProposal,
    ConflictCandidate,
    Destination,
    Evidence,
    Locator,
    validate_binding_proposal,
)
from sc_referee.compiler.inventory import (
    InventoryPathError,
    build_inventory,
    confine_inventory_path,
)
from sc_referee.compiler.resolve import CompileNeeded, NoCompileNeeded, resolve_for_compile


def _digest(char: str = "a") -> str:
    return "sha256:" + char * 64


def _evidence(path="donors.csv.gz", char="b") -> Evidence:
    return Evidence(
        artifact_identity=_digest(char),
        path=path,
        locator=Locator(kind="header", value="g"),
        evidence_digest=_digest("c"),
    )


def _binding_payload() -> dict:
    payload = BindingProposal.empty(_digest()).to_dict()
    payload["requested_bindings"] = [{
        "binding_id": "genotype-column",
        "destination": {"authority": "design", "field": "genotype_column"},
        "candidate_value": "g",
        "confidence": "high",
        "evidence": [{
            "artifact_identity": _digest("b"),
            "path": "donors.csv.gz",
            "locator": {"kind": "header", "value": "g"},
            "evidence_digest": _digest("c"),
        }],
        "state": "proposed",
    }]
    return payload


@pytest.mark.parametrize("forbidden", [
    "confirmed_by_human", "field_state", "status", "severity", "applicability",
    "coverage", "judgment", "verdict", "code_expression", "confirmation_state",
])
def test_binding_proposal_cannot_carry_authority_verdict_or_code_state(forbidden):
    payload = _binding_payload()
    payload["requested_bindings"][0]["candidate_value"] = {forbidden: "not allowed"}
    with pytest.raises(jsonschema.ValidationError, match="cannot carry"):
        validate_binding_proposal(payload)


def test_binding_proposal_rejects_candidate_without_evidence():
    payload = _binding_payload()
    payload["requested_bindings"][0]["evidence"] = []
    with pytest.raises(jsonschema.ValidationError):
        validate_binding_proposal(payload)


def test_binding_proposal_rejects_csp_field_state_record():
    payload = _binding_payload()
    payload["requested_bindings"][0]["destination"] = {
        "authority": "csp_proposal", "field": "genotype_interpretation",
    }
    payload["requested_bindings"][0]["candidate_value"] = {
        "value": "dosage", "state": "confirmed_high", "confidence": "high",
    }
    with pytest.raises(jsonschema.ValidationError, match="CSP field state"):
        validate_binding_proposal(payload)


def test_binding_proposal_rejects_free_form_code_destination():
    payload = _binding_payload()
    payload["requested_bindings"][0]["destination"]["field"] = "code_expression"
    payload["requested_bindings"][0]["candidate_value"] = "lambda table: table['g']"
    with pytest.raises(jsonschema.ValidationError, match="free-form code expression"):
        validate_binding_proposal(payload)


def test_binding_proposal_rejects_unknown_field():
    payload = _binding_payload()
    payload["requested_bindings"][0]["surprise"] = True
    with pytest.raises(jsonschema.ValidationError):
        validate_binding_proposal(payload)


def test_conflicts_retain_every_candidate_and_block_compilation():
    conflict = BindingConflict(
        destination=Destination("design", "genotype_column"),
        candidates=(
            ConflictCandidate("dosage", (_evidence(char="b"),)),
            ConflictCandidate("alt_count", (_evidence(char="d"),)),
        ),
        resolution="unresolved",
        load_bearing=True,
    )
    base = BindingProposal.empty(_digest())
    proposal = BindingProposal(
        schema_id=base.schema_id,
        proposal_id=base.proposal_id,
        revision=base.revision,
        confirmed_organizational_bindings=False,
        inventory_identity=base.inventory_identity,
        conflicts=(conflict,),
    )
    validate_binding_proposal(proposal)
    values = [candidate["candidate_value"]
              for candidate in proposal.to_dict()["conflicts"][0]["candidates"]]
    assert values == ["dosage", "alt_count"]
    assert proposal.blocks_compilation is True


def _write_raw_shaped_folder(folder):
    pd.DataFrame({
        "cell_id": ["c1", "c2"], "donor": ["d1", "d2"], "total_umi": [10, 12],
        "HBB": [1, 2], "IFI6": [0, 1],
    }).to_csv(folder / "cells.csv.gz", index=False, compression="gzip")
    pd.DataFrame({
        "donor": ["d1", "d2"], "g": [0, 2], "sex": ["F", "M"], "age": [40, 50],
    }).to_csv(folder / "donors.csv.gz", index=False, compression="gzip")
    pd.DataFrame({
        "barcode": ["e1", "e2"], "total_umi": [2, 3], "HBB": [1, 1], "IFI6": [0, 0],
    }).to_csv(folder / "empty_drops.csv.gz", index=False, compression="gzip")
    pd.DataFrame({
        "gene": ["HBB"], "pvalue": [0.01], "effect": [0.4],
    }).to_csv(folder / "submission.csv", index=False)
    (folder / "method.txt").write_text("Fit donor-level eQTL models using genotype column g.\n")


def test_raw_shaped_folder_builds_complete_gzip_aware_inventory_and_empty_proposal(tmp_path):
    _write_raw_shaped_folder(tmp_path)

    result = resolve_for_compile(tmp_path)

    assert isinstance(result, CompileNeeded)
    inventory = result.inventory
    assert inventory.inventory_identity.startswith("sha256:")
    assert build_inventory(tmp_path).inventory_identity == inventory.inventory_identity
    by_path = {artifact.relative_path: artifact for artifact in inventory.artifacts}
    assert set(by_path) == {
        "cells.csv.gz", "donors.csv.gz", "empty_drops.csv.gz", "submission.csv", "method.txt",
    }
    assert by_path["cells.csv.gz"].compression == "gzip"
    assert by_path["cells.csv.gz"].columns == ("cell_id", "donor", "total_umi", "HBB", "IFI6")
    assert by_path["donors.csv.gz"].columns == ("donor", "g", "sex", "age")
    assert len(by_path["cells.csv.gz"].dtypes) == len(by_path["cells.csv.gz"].columns)
    assert by_path["method.txt"].evidence_trust == "untrusted_documentation"
    assert "donor-level eQTL" in by_path["method.txt"].documentation_text
    assert inventory.deterministic_facts["recognized_matrix_candidates"] == []
    assert inventory.deterministic_facts["recognized_reported_table_candidates"] == ["submission.csv"]
    assert result.proposal.requested_bindings == ()
    assert result.proposal.conflicts == ()
    assert result.proposal.confirmed_organizational_bindings is False
    assert result.proposal.proposer.kind == "deterministic"
    assert result.proposal.proposer.model is None


def test_inventory_rejects_absolute_parent_and_escaping_symlink_paths(tmp_path):
    root = tmp_path / "analysis"
    root.mkdir()
    (root / "inside.txt").write_text("inside")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside")
    (root / "escape.txt").symlink_to(outside)

    with pytest.raises(InventoryPathError):
        confine_inventory_path(root, "/absolute.csv")
    with pytest.raises(InventoryPathError):
        confine_inventory_path(root, "../outside.txt")
    with pytest.raises(InventoryPathError, match="escapes"):
        build_inventory(root)


def test_known_layout_skips_compile_and_normal_audit_bytes_stay_stable(tmp_path):
    from sc_referee.audit import run_audit
    from sc_referee.report import to_json
    from fixtures.confounding_alias.make_fixture import build

    build(tmp_path)
    before = to_json(run_audit(tmp_path, engine="simple"))
    resolved = resolve_for_compile(tmp_path)
    after = to_json(run_audit(tmp_path, engine="simple"))

    assert isinstance(resolved, NoCompileNeeded)
    assert resolved.bundle.measure.counts.shape[0] > 0
    assert after == before


def test_malformed_supported_matrix_is_not_recast_as_compile_needed(tmp_path):
    (tmp_path / "counts.csv").write_text("cell_id,gene\nc1,not-a-number\n")
    (tmp_path / "obs.csv").write_text("cell_id,condition\nc1,control\n")
    with pytest.raises(Exception, match="could not ingest delimited matrix"):
        resolve_for_compile(tmp_path)


def test_compile_cli_is_explicit_and_makes_no_model_call(tmp_path):
    from typer.testing import CliRunner
    from sc_referee.cli import app

    _write_raw_shaped_folder(tmp_path)
    result = CliRunner().invoke(app, ["compile", str(tmp_path)])
    assert result.exit_code == 0
    assert "compile needed" in result.stdout.lower()
    assert "no claude/model call was made" in result.stdout.lower()
