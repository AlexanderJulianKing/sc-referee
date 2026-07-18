from tests.empty_droplet_fixtures import write_contamination_fixture

import dataclasses
import numpy as np
import pytest
from scipy import sparse


def test_contamination_fixture_has_the_real_three_table_schema(tmp_path):
    paths = write_contamination_fixture(tmp_path)
    assert paths.cells.read_text().splitlines()[0] == (
        "cell_id,donor,total_umi,HBB,IFI6,ISG15,LST1,CXCL10"
    )
    assert paths.donors.read_text().splitlines()[0] == "donor,g,sex,age,bmi"
    assert paths.empty_drops.read_text().splitlines()[0] == (
        "barcode,total_umi,HBB,IFI6,ISG15,LST1,CXCL10"
    )


def test_unavailable_cannot_carry_or_coerce_a_partial_artifact():
    from sc_referee.empty_droplet.schema import (
        ArtifactUnavailable, EmptyDropletUnavailableReason,
    )

    unavailable = ArtifactUnavailable(
        reason_code=EmptyDropletUnavailableReason.RAW_MATRIX_ABSENT,
        message="no empty table", evidence=(), actionability="supply_and_confirm",
    )
    assert not hasattr(unavailable, "artifact")
    assert not hasattr(unavailable, "available")
    with pytest.raises(dataclasses.FrozenInstanceError):
        unavailable.message = "pretend available"


def test_freezing_defensively_copies_every_numeric_buffer():
    from sc_referee.empty_droplet.schema import freeze_csr, freeze_u64_vector

    source = sparse.csr_matrix(np.array([[1, 0], [0, 2]], dtype=np.uint64))
    totals = np.array([10, 20], dtype=np.uint64)
    frozen = freeze_csr(source)
    frozen_totals = freeze_u64_vector(totals, name="total_counts")
    source.data[0] = 99
    totals[0] = 99
    assert frozen[0, 0] == 1 and frozen_totals.tolist() == [10, 20]
    assert not frozen.data.flags.writeable
    assert not frozen.indices.flags.writeable
    assert not frozen.indptr.flags.writeable
    assert not frozen_totals.flags.writeable
    with pytest.raises(ValueError):
        frozen.data[0] = 7
    with pytest.raises(ValueError):
        frozen.data.flags.writeable = True
    with pytest.raises(ValueError):
        frozen_totals.flags.writeable = True
    with pytest.raises(ValueError):
        frozen.data = np.array([7, 2], dtype=np.uint64)


def test_reason_vocabulary_is_closed_and_complete():
    from sc_referee.empty_droplet.schema import EmptyDropletUnavailableReason

    assert len(EmptyDropletUnavailableReason) == 26
    assert {r.value for r in EmptyDropletUnavailableReason} >= {
        "source_unreadable_or_unsafe", "integrity_drift", "empty_cell_overlap",
        "filtered_link_mismatch", "digest_failure",
    }
