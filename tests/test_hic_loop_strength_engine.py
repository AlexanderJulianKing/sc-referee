"""Arithmetic facts from the exact supported Hi-C expected model."""
import pytest

from tests.factories import hic_contact_bundle, make_hic_design


@pytest.mark.parametrize(
    "seed,n_replicates,effect,distance_bins",
    [(0, 2, 1, 3), (4, 3, 2, 5), (9, 4, -1, 7)],
)
def test_exact_distance_mean_of_log_recomputes_the_known_relation(
        seed, n_replicates, effect, distance_bins):
    from sc_referee.engines.hic_loop_strength import recompute_hic_loop_strength

    bundle = hic_contact_bundle(
        reference_strengths=tuple([1] * n_replicates),
        test_strengths=tuple([1 + effect] * n_replicates),
        distance_bins=distance_bins,
        seed=seed,
    )
    design = make_hic_design(hic_target_bin_j=f"b{20 + distance_bins}")
    result = recompute_hic_loop_strength(bundle, design)

    assert result.identified
    assert result.background_pairs >= 50
    assert result.recomputed_delta == pytest.approx(effect)
    assert result.condition_means["stim"] - result.condition_means["ctrl"] == pytest.approx(effect)


def test_reversed_contact_orientation_is_canonicalized_as_one_unordered_pair():
    from sc_referee.engines.hic_loop_strength import recompute_hic_loop_strength

    bundle = hic_contact_bundle(seed=23)
    result = recompute_hic_loop_strength(bundle, make_hic_design())

    assert result.identified
    assert result.recomputed_delta == pytest.approx(1.0)


def test_dense_zero_inclusive_universe_is_required():
    from sc_referee.engines.hic_loop_strength import recompute_hic_loop_strength

    bundle = hic_contact_bundle(seed=31)
    bundle.hic.contacts = bundle.hic.contacts.iloc[1:].copy()
    result = recompute_hic_loop_strength(bundle, make_hic_design())

    assert not result.identified
    assert result.reason == "dense_zero_inclusive_distance_stratum_incomplete"


def test_fewer_than_50_background_pairs_is_not_identified():
    from sc_referee.engines.hic_loop_strength import recompute_hic_loop_strength

    bundle = hic_contact_bundle(n_bins=54, masked_indices=(), seed=37)
    design = make_hic_design(hic_background_view_end=540_000)
    result = recompute_hic_loop_strength(bundle, design)

    assert not result.identified
    assert result.background_pairs < 50
    assert result.reason == "fewer_than_50_eligible_background_pairs"


def test_duplicate_reversed_pixel_is_unresolved_not_summed():
    import pandas as pd
    from sc_referee.engines.hic_loop_strength import recompute_hic_loop_strength

    bundle = hic_contact_bundle(seed=41)
    row = bundle.hic.contacts.iloc[[0]].copy()
    row[["bin_i", "bin_j"]] = row[["bin_j", "bin_i"]].to_numpy()
    bundle.hic.contacts = pd.concat([bundle.hic.contacts, row], ignore_index=True)
    result = recompute_hic_loop_strength(bundle, make_hic_design())

    assert not result.identified
    assert result.reason == "duplicate_unordered_contact_pixel"
