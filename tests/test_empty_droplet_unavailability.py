import gzip

import pytest

from sc_referee.empty_droplet.ingest import ingest_empty_droplet_counts
from sc_referee.empty_droplet.schema import ArtifactUnavailable, EmptyDropletUnavailableReason
from tests.empty_droplet_fixtures import confirmed_declaration, write_contamination_fixture


def test_missing_declaration_is_typed_raw_absence_with_secondary(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    result = ingest_empty_droplet_counts(tmp_path, declaration=None, filtered_bundle=fixture.bundle)
    assert isinstance(result, ArtifactUnavailable)
    assert result.reason_code.value == "raw_matrix_absent"
    assert [reason.value for reason in result.secondary_reason_codes] == [
        "unfiltered_barcode_universe_absent"
    ]
    assert not hasattr(result, "artifact") and not hasattr(result, "counts")


@pytest.mark.parametrize("bad", ["5.5", "-1", "NaN", "1e2", str(2**64)])
def test_bad_count_yields_typed_not_raw_integer_counts(tmp_path, bad):
    fixture = write_contamination_fixture(tmp_path)
    fixture.empty_drops.write_text(
        fixture.empty_drops.read_text().replace("empty_1,12,5", f"empty_1,12,{bad}")
    )
    result = ingest_empty_droplet_counts(
        tmp_path, confirmed_declaration(tmp_path, fixture), fixture.bundle
    )
    assert isinstance(result, ArtifactUnavailable)
    assert result.reason_code.value == "not_raw_integer_counts"
    assert not hasattr(result, "artifact")


def test_corrupt_gzip_returns_source_unreadable_with_no_partial_rows(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    path = tmp_path / "empty_drops.csv.gz"
    path.write_bytes(gzip.compress(fixture.empty_drops.read_bytes(), mtime=0)[:-7])
    declaration = confirmed_declaration(
        tmp_path, fixture, source_path=path.name, source_compression="gzip"
    )
    result = ingest_empty_droplet_counts(tmp_path, declaration, fixture.bundle)
    assert isinstance(result, ArtifactUnavailable)
    assert result.reason_code.value == "source_unreadable_or_unsafe"
    assert not hasattr(result, "artifact") and not hasattr(result, "barcode_ledger")


def test_crc_corrupt_gzip_returns_source_unreadable_with_no_partial_rows(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    encoded = bytearray(gzip.compress(fixture.empty_drops.read_bytes(), mtime=0))
    encoded[-8] ^= 0x01
    path = tmp_path / "empty_drops.csv.gz"
    path.write_bytes(encoded)
    declaration = confirmed_declaration(
        tmp_path, fixture, source_path=path.name, source_compression="gzip"
    )
    result = ingest_empty_droplet_counts(tmp_path, declaration, fixture.bundle)
    assert result.reason_code.value == "source_unreadable_or_unsafe"
    assert not hasattr(result, "artifact") and not hasattr(result, "barcode_ledger")


def test_reason_enum_is_exhaustive_and_no_consumer_emitter_module_exists():
    assert len(EmptyDropletUnavailableReason) == 26
    with pytest.raises(ModuleNotFoundError):
        __import__("sc_referee.empty_droplet.consumer")


def test_integrity_precedes_malformed_and_retains_secondary(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    declaration = confirmed_declaration(tmp_path, fixture)
    fixture.empty_drops.write_text("not,the,confirmed,header\n")
    result = ingest_empty_droplet_counts(tmp_path, declaration, fixture.bundle)
    assert result.reason_code.value == "integrity_drift"
    assert "matrix_or_modality_ambiguous" in [
        reason.value for reason in result.secondary_reason_codes
    ]
