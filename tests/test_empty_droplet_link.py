from dataclasses import replace

import numpy as np
import pytest
from scipy import sparse

from sc_referee.empty_droplet.bundle_identity import capture_filtered_bundle_identity
from sc_referee.empty_droplet.csv_adapter import parse_empty_droplet_csv
from sc_referee.empty_droplet.link import build_filtered_link
from sc_referee.empty_droplet.schema import EmptyDropletValidationError
from tests.empty_droplet_fixtures import confirmed_declaration, write_contamination_fixture


def test_filtered_identity_maps_reordered_bundle_to_cells_csv_by_exact_keys(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    declaration = confirmed_declaration(tmp_path, fixture)
    witness = capture_filtered_bundle_identity(tmp_path, declaration.filtered_link, fixture.bundle)
    assert witness.bundle_cell_to_cells_table_row.tolist() == [1, 0]
    assert [m.feature_key.feature_id for m in witness.bundle_feature_mapping] == [
        "CXCL10", "HBB", "LST1", "IFI6", "ISG15"
    ]
    assert [m.empty_feature_column for m in witness.bundle_feature_mapping] == [4, 0, 3, 1, 2]
    assert witness.shared_count_coherent is True
    assert witness.total_count_coherence == "not_comparable"


@pytest.mark.parametrize("matrix_type", [sparse.csr_matrix, sparse.csc_matrix])
def test_filtered_identity_accepts_sparse_counts_without_changing_identity(tmp_path, matrix_type):
    fixture = write_contamination_fixture(tmp_path)
    declaration = confirmed_declaration(tmp_path, fixture)
    dense = capture_filtered_bundle_identity(tmp_path, declaration.filtered_link, fixture.bundle)
    fixture.bundle.measure.counts = matrix_type(fixture.bundle.measure.counts)
    observed = capture_filtered_bundle_identity(tmp_path, declaration.filtered_link, fixture.bundle)
    assert observed.filtered_bundle_identity == dense.filtered_bundle_identity


def test_shared_gene_count_mismatch_fails_exactly(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    fixture.bundle.measure.counts[0, 0] += 1
    declaration = confirmed_declaration(tmp_path, fixture)
    with pytest.raises(EmptyDropletValidationError) as error:
        capture_filtered_bundle_identity(tmp_path, declaration.filtered_link, fixture.bundle)
    assert error.value.reason_code.value == "filtered_link_mismatch"


def test_witness_is_defensive_against_later_bundle_mutation(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    declaration = confirmed_declaration(tmp_path, fixture)
    witness = capture_filtered_bundle_identity(tmp_path, declaration.filtered_link, fixture.bundle)
    identity = witness.filtered_bundle_identity
    fixture.bundle.measure.counts[:] = 0
    fixture.bundle.observations.index = ["x", "y"]
    assert witness.filtered_bundle_identity == identity
    assert witness.bundle_cell_to_cells_table_row.tolist() == [1, 0]


def test_empty_barcode_colliding_with_analyzed_cell_abstains_whole_link(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    fixture.empty_drops.write_text(fixture.empty_drops.read_text().replace("empty_1", "cell_A"))
    declaration = confirmed_declaration(tmp_path, fixture)
    parsed = parse_empty_droplet_csv(tmp_path, declaration.source)
    witness = capture_filtered_bundle_identity(tmp_path, declaration.filtered_link, fixture.bundle)
    with pytest.raises(EmptyDropletValidationError) as error:
        build_filtered_link(parsed, witness, declaration.source, declaration.filtered_link)
    assert error.value.reason_code.value == "empty_cell_overlap"


def test_feature_mapping_is_exact_not_case_folded(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    fixture.empty_drops.write_text(fixture.empty_drops.read_text().replace("CXCL10", "Cxcl10"))
    declaration = confirmed_declaration(
        tmp_path, fixture, empty_genes=["HBB", "IFI6", "ISG15", "LST1", "Cxcl10"]
    )
    parsed = parse_empty_droplet_csv(tmp_path, declaration.source)
    witness = capture_filtered_bundle_identity(tmp_path, declaration.filtered_link, fixture.bundle)
    with pytest.raises(EmptyDropletValidationError) as error:
        build_filtered_link(parsed, witness, declaration.source, declaration.filtered_link)
    assert error.value.reason_code.value == "raw_filtered_feature_mismatch"


def test_link_asserts_disjointness_and_binds_both_vectors(tmp_path):
    fixture = write_contamination_fixture(tmp_path)
    declaration = confirmed_declaration(tmp_path, fixture)
    parsed = parse_empty_droplet_csv(tmp_path, declaration.source)
    witness = capture_filtered_bundle_identity(tmp_path, declaration.filtered_link, fixture.bundle)
    link = build_filtered_link(parsed, witness, declaration.source, declaration.filtered_link)
    assert link.empty_vs_cell_disjoint is True
    assert link.bundle_cell_to_cells_table_row.tolist() == [1, 0]
    assert [mapping.empty_feature_column for mapping in link.bundle_feature_mapping] == [4, 0, 3, 1, 2]
    assert link.link_digest.startswith("sha256:")
