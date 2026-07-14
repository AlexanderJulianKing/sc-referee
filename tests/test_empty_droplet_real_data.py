"""Read-only opt-in GB-P07 ingestion gate; private data and hashes never enter the repo."""
from __future__ import annotations

import zipfile

import pytest

from bench.gbp07_anchor import _build_bundle, _load, default_zip
from sc_referee.empty_droplet.ingest import ingest_empty_droplet_counts
from sc_referee.empty_droplet.schema import Available
from tests.empty_droplet_fixtures import GBP07Fixture, confirmed_declaration


pytestmark = pytest.mark.skipif(
    not default_zip().exists(),
    reason="GB-P07 data not present — set GBP07_ZIP; private bytes remain outside the repo",
)


def test_real_gbp07_empty_table_links_exactly_to_existing_filtered_bundle(tmp_path):
    members = ("cells.csv.gz", "donors.csv.gz", "empty_drops.csv.gz")
    with zipfile.ZipFile(default_zip()) as archive:
        assert set(members) <= set(archive.namelist())
        for member in members:
            (tmp_path / member).write_bytes(archive.read(member))

    cells, donors = _load(default_zip())
    bundle = _build_bundle(cells, donors)
    fixture = GBP07Fixture(
        cells=tmp_path / "cells.csv.gz", donors=tmp_path / "donors.csv.gz",
        empty_drops=tmp_path / "empty_drops.csv.gz", bundle=bundle,
    )
    declaration = confirmed_declaration(
        tmp_path, fixture,
        source_path="empty_drops.csv.gz", source_compression="gzip",
        filtered_path="cells.csv.gz", filtered_compression="gzip",
    )
    result = ingest_empty_droplet_counts(tmp_path, declaration, bundle)
    assert isinstance(result, Available)
    assert tuple(feature.feature_id for feature in result.artifact.feature_ledger) == (
        "HBB", "IFI6", "ISG15", "LST1", "CXCL10"
    )
