from dataclasses import replace
from pathlib import Path

import pytest

from sc_referee.empty_droplet.confirmation import (
    confirm_declaration, load_declaration, validate_declaration_integrity,
)
from sc_referee.empty_droplet.ingest import ingest_empty_droplet_counts, verify_artifact_integrity
from sc_referee.empty_droplet.proposal import propose_empty_droplet_roles
from sc_referee.empty_droplet.schema import EmptyDropletValidationError
from tests.empty_droplet_fixtures import confirmed_declaration, proposed_declaration, write_contamination_fixture


def test_confirmation_records_both_source_hashes_and_semantic_digest(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    path = proposed_declaration(tmp_path, fixture)
    confirmed = confirm_declaration(
        path, confirmer_actor_id="analyst:alice", confirmation_event_id="confirm:001"
    )
    assert confirmed.confirmed_by_human is True
    assert confirmed.integrity.source_sha256.startswith("sha256:")
    assert confirmed.integrity.filtered_source_sha256.startswith("sha256:")
    assert confirmed.integrity.semantic_digest.startswith("sha256:")
    assert load_declaration(path) == confirmed


def test_post_confirmation_byte_drift_is_integrity_drift(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    declaration = confirm_declaration(
        proposed_declaration(tmp_path, fixture),
        confirmer_actor_id="analyst:alice", confirmation_event_id="confirm:001",
    )
    fixture.empty_drops.write_text(
        fixture.empty_drops.read_text().replace("empty_2,9", "empty_2,10")
    )
    with pytest.raises(EmptyDropletValidationError) as error:
        validate_declaration_integrity(tmp_path, declaration)
    assert error.value.reason_code.value == "integrity_drift"


@pytest.mark.parametrize("unsafe", ["../empty_drops.csv", "/tmp/empty_drops.csv"])
def test_confirmation_rejects_unsafe_paths(tmp_path, unsafe):
    fixture = write_contamination_fixture(tmp_path)
    path = proposed_declaration(tmp_path, fixture, source_path=unsafe)
    with pytest.raises(ValueError):
        confirm_declaration(path, confirmer_actor_id="analyst:a", confirmation_event_id="c:1")


def test_donor_exposure_values_cannot_change_any_artifact_identity(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    declaration = confirm_declaration(
        proposed_declaration(tmp_path, fixture), confirmer_actor_id="analyst:a",
        confirmation_event_id="confirm:1", confirmed_at="2026-07-11T00:00:00Z",
    )
    before = ingest_empty_droplet_counts(tmp_path, declaration, fixture.bundle).artifact
    fixture.donors.write_text(fixture.donors.read_text().replace("D1,0", "D1,2"))
    after = ingest_empty_droplet_counts(tmp_path, declaration, fixture.bundle).artifact
    assert before.artifact_content_identity == after.artifact_content_identity
    assert before.attestation_identity == after.attestation_identity


def test_proposer_and_ingest_never_open_donors_csv(tmp_path, monkeypatch):
    fixture = write_contamination_fixture(tmp_path)
    declaration = confirmed_declaration(tmp_path, fixture)
    original_open = Path.open
    touched = []

    def watched_open(path, *args, **kwargs):
        touched.append(path.name)
        if path.name == "donors.csv":
            raise AssertionError("donors.csv must remain blind")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", watched_open)
    propose_empty_droplet_roles(tmp_path, client=None)
    result = ingest_empty_droplet_counts(tmp_path, declaration, fixture.bundle)
    assert hasattr(result, "artifact")
    assert "donors.csv" not in touched


def test_artifact_is_defensive_read_only_and_forged_digest_is_detected(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    artifact = ingest_empty_droplet_counts(
        tmp_path, confirmed_declaration(tmp_path, fixture), fixture.bundle
    ).artifact
    identity = artifact.artifact_content_identity
    fixture.bundle.measure.counts[:] = 0
    fixture.bundle.observations.index = ["x", "y"]
    assert artifact.artifact_content_identity == identity
    assert artifact.filtered_bundle_link.shared_count_coherent is True
    with pytest.raises(ValueError):
        artifact.counts.data[0] = 0
    with pytest.raises(ValueError):
        artifact.total_counts[0] = 0
    forged = replace(artifact, digests=replace(artifact.digests, matrix_digest="sha256:" + "0" * 64))
    assert verify_artifact_integrity(forged) is False


def test_human_confirmation_cannot_bless_malformed_arithmetic(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    fixture.empty_drops.write_text(fixture.empty_drops.read_text().replace("empty_1,12,5", "empty_1,12,5.5"))
    declaration = confirmed_declaration(tmp_path, fixture)
    result = ingest_empty_droplet_counts(tmp_path, declaration, fixture.bundle)
    assert result.reason_code.value == "not_raw_integer_counts"
    assert not hasattr(result, "artifact")
