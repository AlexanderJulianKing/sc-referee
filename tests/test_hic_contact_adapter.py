"""Thin canonical CSV adapter for the non-single-cell Hi-C bundle."""
from tests.factories import hic_contact_bundle


def test_hic_adapter_loads_parallel_bundle_and_binds_report(tmp_path):
    from sc_referee.adapters.hic_contact_adapter import read_hic_contact_folder
    from sc_referee.bundle import HiCBundle

    source = hic_contact_bundle(seed=2)
    source.hic.contacts.to_csv(tmp_path / "hic_contacts.csv", index=False)
    source.hic.bins.to_csv(tmp_path / "hic_bins.csv", index=False)
    source.reported_results.to_csv(tmp_path / "hic_report.csv", index=False)

    bundle = read_hic_contact_folder(tmp_path)

    assert isinstance(bundle, HiCBundle)
    assert list(bundle.hic.contacts.columns) == [
        "replicate", "condition", "bin_i", "bin_j", "observed_count"]
    assert list(bundle.hic.bins.columns) == ["bin_id", "chrom", "start", "masked"]
    assert bundle.reported_results.iloc[0]["delta"] == 1.0
    assert bundle.hic.contacts_digest and bundle.hic.bins_digest
    assert bundle.provenance["data"]["path"] == "hic_contacts.csv, hic_bins.csv"


def test_hic_adapter_preserves_missing_inputs_for_rich_not_audited_finding(tmp_path):
    from sc_referee.adapters.hic_contact_adapter import read_hic_contact_folder

    bundle = read_hic_contact_folder(tmp_path)

    assert bundle.hic.contacts is None and bundle.hic.bins is None
    assert bundle.provenance["data"]["path"] is None
