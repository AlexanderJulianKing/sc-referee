import pytest

from sc_referee.empty_droplet.proposal import propose_empty_droplet_roles, validate_proposal
from tests.empty_droplet_fixtures import write_contamination_fixture


def test_proposer_can_inventory_but_cannot_confirm(tmp_path):
    write_contamination_fixture(tmp_path)
    proposal = propose_empty_droplet_roles(tmp_path, client=None)
    assert proposal.confirmed_by_human is False
    assert set(proposal.inventory) == {"cells.csv", "donors.csv", "empty_drops.csv"}
    assert "g" not in proposal.inspected_value_columns
    assert proposal.membership_method_id == "explicit_empty_table_rows/v1"
    assert proposal.source_path is None
    assert not hasattr(proposal, "threshold")


@pytest.mark.parametrize("forbidden", [
    {"threshold": 100}, {"formula": "total_umi < 100"}, {"knee": 50},
    {"membership_values": ["empty_1"]}, {"set_operation": "cells complement"},
    {"target_gene": "CXCL10"}, {"verdict": "use"},
])
def test_proposal_schema_rejects_scientific_or_membership_authority(forbidden):
    with pytest.raises(ValueError):
        validate_proposal({"schema_id": "sc-referee/empty-droplet-proposal/v1", **forbidden})


def test_decoy_filenames_never_auto_confirm_or_select(tmp_path):
    write_contamination_fixture(tmp_path)
    (tmp_path / "ambient.csv").write_text("barcode,total_umi,HBB\nx,1,1\n")
    (tmp_path / "raw.csv").write_text("barcode,total_umi,HBB\ny,1,1\n")
    proposal = propose_empty_droplet_roles(tmp_path, client=None)
    assert proposal.source_path is None
    assert proposal.confirmed_by_human is False
