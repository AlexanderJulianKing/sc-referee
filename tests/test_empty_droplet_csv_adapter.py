from dataclasses import replace
import gzip

import numpy as np
import pytest

from sc_referee.empty_droplet.csv_adapter import parse_empty_droplet_csv
from sc_referee.empty_droplet.schema import EmptyDropletValidationError
from tests.empty_droplet_fixtures import confirmed_declaration, write_gbp07_fixture


def test_parse_gbp07_empty_table_preserves_confirmed_row_and_gene_order(tmp_path):
    fixture = write_gbp07_fixture(tmp_path)
    declaration = confirmed_declaration(tmp_path, fixture)
    parsed = parse_empty_droplet_csv(tmp_path, declaration.source)
    assert [(k.namespace, k.native_barcode) for k in parsed.barcode_ledger] == [
        ("", "empty_1"), ("", "empty_2")
    ]
    assert [f.feature_id for f in parsed.feature_ledger] == [
        "HBB", "IFI6", "ISG15", "LST1", "CXCL10"
    ]
    np.testing.assert_array_equal(parsed.counts.toarray(), [[5, 0, 1, 0, 2], [3, 1, 0, 1, 1]])
    np.testing.assert_array_equal(parsed.total_counts, [12, 9])
    assert parsed.counts.dtype == np.uint64


@pytest.mark.parametrize("replacement", ["5.5", "-1", "NaN", "Inf", "1e2", str(2**64)])
def test_invalid_count_lexemes_are_not_raw_integer_counts(tmp_path, replacement):
    fixture = write_gbp07_fixture(tmp_path)
    fixture.empty_drops.write_text(
        fixture.empty_drops.read_text().replace("empty_1,12,5", f"empty_1,12,{replacement}")
    )
    with pytest.raises(EmptyDropletValidationError) as error:
        parse_empty_droplet_csv(tmp_path, confirmed_declaration(tmp_path, fixture).source)
    assert error.value.reason_code.value == "not_raw_integer_counts"


def test_total_umi_is_its_own_vector_not_the_panel_sum_golden(tmp_path):
    fixture = write_gbp07_fixture(tmp_path)
    parsed = parse_empty_droplet_csv(tmp_path, confirmed_declaration(tmp_path, fixture).source)
    assert parsed.total_counts.tolist() == [12, 9]
    assert parsed.counts.sum(axis=1).A1.tolist() == [8, 6]


def test_uint64_parse_never_round_trips_through_float(tmp_path):
    fixture = write_gbp07_fixture(tmp_path)
    exact = 2**53 + 1
    fixture.empty_drops.write_text(fixture.empty_drops.read_text().replace("empty_1,12,5", f"empty_1,12,{exact}"))
    parsed = parse_empty_droplet_csv(tmp_path, confirmed_declaration(tmp_path, fixture).source)
    assert int(parsed.counts[0, 0]) == exact


def test_corrupt_truncated_and_concatenated_gzip_fail_closed(tmp_path):
    fixture = write_gbp07_fixture(tmp_path)
    raw = fixture.empty_drops.read_bytes()
    gz = tmp_path / "empty_drops.csv.gz"
    gz.write_bytes(gzip.compress(raw, mtime=0)[:-5])
    declaration = confirmed_declaration(
        tmp_path, fixture, source_path="empty_drops.csv.gz", source_compression="gzip"
    )
    with pytest.raises(EmptyDropletValidationError) as error:
        parse_empty_droplet_csv(tmp_path, declaration.source)
    assert error.value.reason_code.value == "source_unreadable_or_unsafe"

    gz.write_bytes(gzip.compress(raw, mtime=0) + gzip.compress(raw, mtime=0))
    declaration = confirmed_declaration(
        tmp_path, fixture, source_path="empty_drops.csv.gz", source_compression="gzip"
    )
    with pytest.raises(EmptyDropletValidationError) as error:
        parse_empty_droplet_csv(tmp_path, declaration.source)
    assert error.value.reason_code.value == "source_unreadable_or_unsafe"
