from __future__ import annotations

import copy
from dataclasses import replace
import os
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pandas as pd
import pytest
import jsonschema

from sc_referee.compiler.binding_proposal import validate_binding_proposal
from sc_referee.compiler.inventory import build_inventory
from sc_referee.compiler.proposer import (
    PROPOSAL_TOOL,
    REQUIRED_DESTINATIONS,
    binding_proposal_tool_schema,
    propose_bindings,
)
from sc_referee.compiler.pipeline import (
    confirm_organizational_bindings,
    record_organizational_confirmation,
)
from sc_referee.csp_contracts.contamination_condensed_ceremony import (
    CondensedAnswer,
    CondensedGroup,
)
from sc_referee.derivations.contamination_compile import CompiledDerivation, compile_from_proposal
from sc_referee import statuses as S


GBP07_ZIP = Path(os.environ.get(
    "GBP07_ZIP", "~/Desktop/genebench_phase1_inputs/GB-P07-data.zip"
)).expanduser()


class FakeClient:
    def __init__(self, payload=None, *, prose=False):
        self.payload = payload
        self.prose = prose
        self.calls = []
        self.messages = SimpleNamespace(create=self.create)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.prose:
            return SimpleNamespace(content=[SimpleNamespace(type="text", text="I propose...")])
        return SimpleNamespace(content=[SimpleNamespace(
            type="tool_use", name=PROPOSAL_TOOL, input=copy.deepcopy(self.payload),
        )])


def _write_raw_contamination(folder):
    pd.DataFrame({
        "cell_id": ["c1", "c2"], "donor": ["d1", "d2"], "total_umi": [10, 12],
        "HBB": [1, 2], "IFI6": [0, 1], "ISG15": [0, 0], "LST1": [2, 1],
        "CXCL10": [3, 4],
    }).to_csv(folder / "cells.csv.gz", index=False, compression="gzip")
    pd.DataFrame({
        "donor": ["d1", "d2"], "g": [0, 2], "sex": ["F", "M"],
    }).to_csv(folder / "donors.csv.gz", index=False, compression="gzip")
    pd.DataFrame({
        "barcode": ["e1", "e2"], "total_umi": [2, 3], "HBB": [1, 1],
        "IFI6": [0, 0], "ISG15": [0, 0], "LST1": [0, 1], "CXCL10": [0, 0],
    }).to_csv(folder / "empty_drops.csv.gz", index=False, compression="gzip")
    pd.DataFrame({
        "gene": ["CXCL10"], "pvalue": [0.01], "effect": [0.4],
    }).to_csv(folder / "submission.csv", index=False)
    (folder / "method.txt").write_text(
        "Fit donor-level eQTL models using genotype column g. "
        "The target coefficient is genotype for CXCL10. "
        "Apply ambient_contamination_estimator/v1 to empty droplets. "
        "Call a donor high-contamination above 0.18, "
        "per report_public.pdf equations 18-23.\n"
    )


@pytest.fixture
def inventory(tmp_path):
    _write_raw_contamination(tmp_path)
    return build_inventory(tmp_path)


def _ev(inventory, path, kind, value):
    artifact = next(item for item in inventory.artifacts if item.relative_path == path)
    return {
        "artifact_identity": artifact.artifact_identity,
        "path": path,
        "locator": {"kind": kind, "value": value},
    }


def _binding(inventory, binding_id, authority, field, value, evidence):
    return {
        "binding_id": binding_id,
        "destination": {"authority": authority, "field": field},
        "candidate_value": value,
        "confidence": "high",
        "evidence": evidence,
        "state": "proposed",
    }


def _complete_payload(inventory):
    method = "method.txt"
    return {
        "requested_bindings": [
            _binding(inventory, "analysis-type", "design", "analysis_type", "eqtl", [
                _ev(inventory, method, "documentation_span", "eQTL"),
            ]),
            _binding(inventory, "cell-table", "detector_input", "cell_table", {
                "artifact_path": "cells.csv.gz",
                "columns": {"cell_id": "cell_id", "donor": "donor",
                            "total_umi": "total_umi", "marker": "HBB"},
            }, [_ev(inventory, "cells.csv.gz", "header", column)
                for column in ("cell_id", "donor", "total_umi", "HBB")]),
            _binding(inventory, "donor-table", "detector_input", "donor_table", {
                "artifact_path": "donors.csv.gz",
                "columns": {"donor": "donor", "genotype": "g"},
            }, [_ev(inventory, "donors.csv.gz", "header", column)
                for column in ("donor", "g")]),
            _binding(inventory, "empty-table", "empty_droplet", "empty_droplet_table", {
                "artifact_path": "empty_drops.csv.gz",
                "columns": {
                    "total_umi": "total_umi",
                    "panel": {gene: gene for gene in (
                        "HBB", "IFI6", "ISG15", "LST1", "CXCL10",
                    )},
                },
            }, [_ev(inventory, "empty_drops.csv.gz", "header", "total_umi")]),
            _binding(inventory, "genotype-column", "design", "genotype_column", "g", [
                _ev(inventory, "donors.csv.gz", "header", "g"),
            ]),
            _binding(inventory, "target-feature", "design", "target_feature", "CXCL10", [
                _ev(inventory, "cells.csv.gz", "header", "CXCL10"),
            ]),
            _binding(inventory, "submitted-result", "reported_claim",
                     "submitted_result_artifact", "submission.csv", [
                _ev(inventory, "submission.csv", "header", "effect"),
            ]),
            _binding(inventory, "target-coefficient", "reported_claim", "target_coefficient",
                     "genotype", [
                _ev(inventory, method, "documentation_span", "target coefficient is genotype"),
            ]),
            _binding(inventory, "fitted-method", "fitted_design", "method_evidence_span",
                     "Fit donor-level eQTL models using genotype column g.", [
                _ev(inventory, method, "documentation_span",
                    "Fit donor-level eQTL models using genotype column g."),
            ]),
            _binding(inventory, "derivation", "detector_input", "derivation_id",
                     "ambient_contamination_estimator/v1", [
                _ev(inventory, method, "documentation_span",
                    "ambient_contamination_estimator/v1"),
            ]),
            _binding(inventory, "threshold", "detector_input", "contamination_threshold",
                     "0.18", [
                _ev(inventory, method, "documentation_span",
                    "Call a donor high-contamination above 0.18"),
            ]),
            _binding(inventory, "provenance", "detector_input", "method_provenance",
                     "report_public.pdf equations 18-23", [
                _ev(inventory, method, "documentation_span",
                    "per report_public.pdf equations 18-23"),
            ]),
        ],
        "conflicts": [],
        "unresolved": [],
    }


def test_complete_contamination_tool_payload_returns_grounded_binding_proposal(inventory):
    payload = _complete_payload(inventory)
    client = FakeClient(payload)

    proposal = propose_bindings(inventory, client=client)

    validate_binding_proposal(proposal)
    assert proposal.confirmed_organizational_bindings is False
    assert proposal.blocks_compilation is True
    assert {binding.destination for binding in proposal.requested_bindings} == set(
        REQUIRED_DESTINATIONS
    )
    artifacts = {(item.relative_path, item.artifact_identity) for item in inventory.artifacts}
    assert all((evidence.path, evidence.artifact_identity) in artifacts
               for binding in proposal.requested_bindings for evidence in binding.evidence)
    call = client.calls[0]
    assert call["tool_choice"] == {"type": "tool", "name": PROPOSAL_TOOL}
    assert call["tools"][0]["input_schema"] == binding_proposal_tool_schema()


def test_compiler_mints_content_bound_evidence_digests(inventory):
    proposal = propose_bindings(inventory, client=FakeClient(_complete_payload(inventory)))
    artifact_identities = {item.artifact_identity for item in inventory.artifacts}

    assert all(evidence.evidence_digest not in artifact_identities
               for binding in proposal.requested_bindings for evidence in binding.evidence)


def test_copied_model_evidence_digest_is_rejected_at_tool_boundary(inventory):
    payload = _complete_payload(inventory)
    payload["requested_bindings"][0]["evidence"][0]["evidence_digest"] = \
        payload["requested_bindings"][0]["evidence"][0]["artifact_identity"]

    with pytest.raises(ValueError, match="schema validation"):
        propose_bindings(inventory, client=FakeClient(payload))


def test_table_cell_locator_is_resolved_and_out_of_range_cells_are_rejected(inventory):
    payload = _complete_payload(inventory)
    evidence = payload["requested_bindings"][0]["evidence"][0]
    donor = next(item for item in inventory.artifacts if item.relative_path == "donors.csv.gz")
    evidence.update({
        "artifact_identity": donor.artifact_identity,
        "path": donor.relative_path,
        "locator": {"kind": "table_cell", "value": '{"column":"g","row":0}'},
    })
    proposal = propose_bindings(inventory, client=FakeClient(payload))
    assert proposal.requested_bindings[0].evidence[0].evidence_digest.startswith("sha256:")

    evidence["locator"]["value"] = '{"column":"g","row":999}'
    with pytest.raises(ValueError, match="row is out of bounds"):
        propose_bindings(inventory, client=FakeClient(payload))


def test_recovered_proposal_with_fabricated_evidence_digest_is_rejected(inventory):
    proposal = propose_bindings(inventory, client=FakeClient(_complete_payload(inventory)))
    first = proposal.requested_bindings[0]
    forged_evidence = replace(first.evidence[0], evidence_digest=first.evidence[0].artifact_identity)
    forged = replace(
        proposal,
        requested_bindings=(replace(first, evidence=(forged_evidence,)),
                            *proposal.requested_bindings[1:]),
    )

    with pytest.raises(ValueError, match="evidence digest does not match"):
        propose_bindings(inventory, forged, client=FakeClient(prose=True))


def test_tool_schema_does_not_require_empty_gene_panel(inventory):
    payload = _complete_payload(inventory)
    binding = next(
        item for item in payload["requested_bindings"]
        if item["destination"]["field"] == "empty_droplet_table"
    )
    binding["candidate_value"]["columns"] = {
        "total_umi": "total_umi",
        "barcode": "barcode",
    }

    jsonschema.validate(payload, binding_proposal_tool_schema())


@pytest.mark.skipif(not GBP07_ZIP.exists(), reason="GB-P07 data not present — set GBP07_ZIP")
def test_proposer_schema_valid_payload_compiles_real_contamination_to_conditional_major(tmp_path):
    with ZipFile(GBP07_ZIP) as archive:
        for member in ("cells.csv.gz", "donors.csv.gz", "empty_drops.csv.gz"):
            (tmp_path / member).write_bytes(archive.read(member))
    pd.DataFrame({"gene": ["CXCL10"], "effect": [0.4839]}).to_csv(
        tmp_path / "submission.csv", index=False
    )
    (tmp_path / "method.txt").write_text(
        "Fit donor-level eQTL models using genotype column g. "
        "The target coefficient is genotype for CXCL10. No ambient adjustment was included. "
        "Apply ambient_contamination_estimator/v1 to empty droplets. "
        "Call a donor high-contamination above 0.18, "
        "per report_public.pdf equations 18-23.\n",
        encoding="utf-8",
    )
    real_inventory = build_inventory(tmp_path)
    payload = _complete_payload(real_inventory)
    jsonschema.validate(payload, binding_proposal_tool_schema())
    proposal = propose_bindings(real_inventory, client=FakeClient(payload))
    proposal = confirm_organizational_bindings(
        proposal,
        record_organizational_confirmation(proposal, actor="test reviewer"),
    )

    result = compile_from_proposal(
        proposal,
        tmp_path,
        {group: CondensedAnswer.YES for group in CondensedGroup},
    )

    assert isinstance(result, CompiledDerivation)
    assert result.finding.status == S.MAJOR
    assert result.finding.conditional_on is not None


@pytest.mark.parametrize("field", ["cell_table", "donor_table", "empty_droplet_table"])
def test_tool_schema_requires_canonical_shape_for_every_table(inventory, field):
    payload = _complete_payload(inventory)
    binding = next(
        item for item in payload["requested_bindings"]
        if item["destination"]["field"] == field
    )
    binding["candidate_value"].update(binding["candidate_value"].pop("columns"))

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, binding_proposal_tool_schema())


def test_prose_without_tool_use_is_rejected(inventory):
    with pytest.raises(ValueError, match="returned prose"):
        propose_bindings(inventory, client=FakeClient(prose=True))


def test_candidate_without_evidence_is_rejected_by_tool_schema(inventory):
    payload = _complete_payload(inventory)
    payload["requested_bindings"][0]["evidence"] = []
    with pytest.raises(ValueError, match="schema validation"):
        propose_bindings(inventory, client=FakeClient(payload))


@pytest.mark.parametrize("forbidden", ["verdict", "status", "confirmed_by_human"])
def test_authority_or_verdict_assertions_are_rejected(inventory, forbidden):
    payload = _complete_payload(inventory)
    payload[forbidden] = True
    with pytest.raises(ValueError, match="schema validation"):
        propose_bindings(inventory, client=FakeClient(payload))


def test_differing_candidates_for_destination_become_retained_conflict(inventory):
    payload = _complete_payload(inventory)
    payload["requested_bindings"].append(_binding(
        inventory, "genotype-column-alternative", "design", "genotype_column", "sex",
        [_ev(inventory, "donors.csv.gz", "header", "sex")],
    ))

    proposal = propose_bindings(inventory, client=FakeClient(payload))

    conflict = next(item for item in proposal.conflicts
                    if item.destination.field == "genotype_column")
    assert [candidate.candidate_value for candidate in conflict.candidates] == ["g", "sex"]
    assert proposal.confirmed_organizational_bindings is False
    assert "design.genotype_column" in proposal.unresolved
    assert proposal.blocks_compilation is True


def test_ungroundable_required_binding_is_unresolved_not_guessed(inventory):
    payload = _complete_payload(inventory)
    payload["requested_bindings"] = [
        item for item in payload["requested_bindings"]
        if item["destination"]["field"] != "target_feature"
    ]
    payload["unresolved"] = ["design.target_feature"]

    proposal = propose_bindings(inventory, client=FakeClient(payload))

    assert "design.target_feature" in proposal.unresolved
    assert not any(binding.destination.field == "target_feature"
                   for binding in proposal.requested_bindings)
    assert proposal.confirmed_organizational_bindings is False


def test_no_model_fails_closed(inventory):
    with pytest.raises(RuntimeError, match="compiler proposer needs a model"):
        propose_bindings(inventory, client=None)


def test_complete_recovered_proposal_skips_model(inventory):
    complete = propose_bindings(inventory, client=FakeClient(_complete_payload(inventory)))
    recovered = replace(complete, confirmed_organizational_bindings=False)
    client = FakeClient(prose=True)

    assert propose_bindings(inventory, recovered, client=client) is recovered
    assert client.calls == []


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="needs live Claude API key")
def test_live_contamination_binding_proposer(tmp_path):
    _write_raw_contamination(tmp_path)
    inventory = build_inventory(tmp_path)

    proposal = propose_bindings(inventory)

    validate_binding_proposal(proposal)
    artifacts = {(item.relative_path, item.artifact_identity) for item in inventory.artifacts}
    assert proposal.requested_bindings
    assert all(binding.evidence for binding in proposal.requested_bindings)
    assert all((evidence.path, evidence.artifact_identity) in artifacts
               for binding in proposal.requested_bindings for evidence in binding.evidence)
