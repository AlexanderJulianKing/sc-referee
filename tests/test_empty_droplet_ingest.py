import gzip
import os
import subprocess
import sys

import numpy as np

from sc_referee.empty_droplet.ingest import ingest_empty_droplet_counts
from sc_referee.empty_droplet.schema import Available
from sc_referee.empty_droplet.serialization import canonical_artifact_bytes
from tests.empty_droplet_fixtures import confirmed_declaration, write_gbp07_fixture


def test_confirmed_gbp07_csv_and_cells_link_returns_available_artifact(tmp_path):
    fixture = write_gbp07_fixture(tmp_path)
    declaration = confirmed_declaration(tmp_path, fixture)
    before_counts = fixture.bundle.measure.counts.copy()
    before_cells = fixture.bundle.observations.index.tolist()
    result = ingest_empty_droplet_counts(tmp_path, declaration, fixture.bundle)
    assert isinstance(result, Available)
    artifact = result.artifact
    assert artifact.schema_id == "sc-referee/empty-droplet-counts-artifact/v1"
    assert artifact.digest_policy_id == "sc-referee/empty-droplet-digest/v1"
    assert artifact.shape == (2, 5)
    np.testing.assert_array_equal(artifact.empty_membership, [True, True])
    assert artifact.selected_barcodes == artifact.barcode_ledger
    assert artifact.membership_provenance.method_id == "explicit_empty_table_rows/v1"
    assert artifact.filtered_bundle_link.empty_vs_cell_disjoint is True
    assert artifact.filtered_bundle_link.shared_count_coherent is True
    assert artifact.artifact_content_identity.startswith("sha256:")
    assert artifact.attestation_identity.startswith("sha256:")
    assert artifact.artifact_content_identity != artifact.attestation_identity
    assert {record.relative_path for record in artifact.source_provenance} == {"empty_drops.csv", "cells.csv"}
    assert "donors.csv" not in repr(artifact.source_provenance)
    assert not hasattr(artifact, "finding") and not hasattr(artifact, "status")
    np.testing.assert_array_equal(fixture.bundle.measure.counts, before_counts)
    assert fixture.bundle.observations.index.tolist() == before_cells


def test_gzip_and_plain_share_content_but_not_source_or_attestation_golden(tmp_path):
    plain_root = tmp_path / "plain"
    gzip_root = tmp_path / "gzip"
    plain_root.mkdir(); gzip_root.mkdir()
    plain_fixture = write_gbp07_fixture(plain_root)
    gzip_fixture = write_gbp07_fixture(gzip_root)
    plain = ingest_empty_droplet_counts(
        plain_root, confirmed_declaration(plain_root, plain_fixture), plain_fixture.bundle
    ).artifact
    for name in ("empty_drops.csv", "cells.csv"):
        path = gzip_root / name
        (gzip_root / f"{name}.gz").write_bytes(gzip.compress(path.read_bytes(), mtime=123456))
    zipped_declaration = confirmed_declaration(
        gzip_root, gzip_fixture,
        source_path="empty_drops.csv.gz", source_compression="gzip",
        filtered_path="cells.csv.gz", filtered_compression="gzip",
    )
    zipped = ingest_empty_droplet_counts(gzip_root, zipped_declaration, gzip_fixture.bundle).artifact
    assert plain.artifact_content_identity == zipped.artifact_content_identity
    assert plain.digests.source_byte_hash != zipped.digests.source_byte_hash
    assert plain.digests.filtered_source_byte_hash != zipped.digests.filtered_source_byte_hash
    assert plain.attestation_identity != zipped.attestation_identity


def test_reingest_is_bit_identical(tmp_path):
    fixture = write_gbp07_fixture(tmp_path)
    declaration = confirmed_declaration(tmp_path, fixture)
    first = ingest_empty_droplet_counts(tmp_path, declaration, fixture.bundle).artifact
    second = ingest_empty_droplet_counts(tmp_path, declaration, fixture.bundle).artifact
    assert canonical_artifact_bytes(first) == canonical_artifact_bytes(second)
    assert first.digests == second.digests
    assert first.artifact_content_identity == second.artifact_content_identity
    assert first.attestation_identity == second.attestation_identity
    assert first.counts is not second.counts


def test_reingest_is_identical_across_python_hash_seeds(tmp_path):
    script = r'''
import hashlib
from pathlib import Path
import sys
from tests.empty_droplet_fixtures import confirmed_declaration, write_gbp07_fixture
from sc_referee.empty_droplet.ingest import ingest_empty_droplet_counts
from sc_referee.empty_droplet.serialization import canonical_artifact_bytes
root = Path(sys.argv[1])
fixture = write_gbp07_fixture(root)
artifact = ingest_empty_droplet_counts(root, confirmed_declaration(root, fixture), fixture.bundle).artifact
print(hashlib.sha256(canonical_artifact_bytes(artifact)).hexdigest())
'''
    outputs = []
    for seed in ("1", "987654"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH="src:.")
        outputs.append(subprocess.check_output(
            [sys.executable, "-c", script, str(tmp_path)], cwd=os.getcwd(), env=env, text=True
        ).strip())
    assert outputs[0] == outputs[1]
