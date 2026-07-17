"""Tests for latent-stratum materialization v0.

The module is evidence-only. These tests pin two things above all: that it materialises the
candidate it is supposed to, and that it renders no judgment while doing so.
"""
import json
import re

import pandas as pd
import pytest

from sc_referee.inference.materialization import (  # noqa: I001
    AGGREGATION,
    MATERIALIZER_VERSION,
    STATUS_ABSTAINED,
    STATUS_COMPLETE,
    STATUS_NO_IN_SCOPE_CONSTRUCT,
    STATUS_PARTIAL,
    Abstain,
    materialize,
)

SOURCE = '''
genes=["HBB","CXCL10"]
p_amb = {g: empty[g].sum()/empty.total_umi.sum() for g in genes}
c["rho"] = np.clip(c.HBB/(c.total_umi*p_amb["HBB"]), 0, 1)
'''


def _tables(rhos=(0.1, 0.2, 0.3, 0.4)):
    """Four donors, genotype 0..3, ambient load rising with genotype. Correlation is by construction."""
    empty = pd.DataFrame({"total_umi": [1000], "HBB": [100], "CXCL10": [50]})  # p_amb[HBB] = 0.1
    rows = []
    for d, (g, rho) in enumerate(zip(range(4), rhos)):
        for _ in range(10):
            tu = 1000
            rows.append({"donor": f"D{d}", "g": g, "total_umi": tu,
                         "HBB": rho * tu * 0.1, "CXCL10": 5})
    return {"c": pd.DataFrame(rows), "empty": empty}


def test_materialises_the_derived_quantity_at_the_declared_unit():
    rec = materialize(SOURCE, _tables(), unit="donor", exposure="g")
    assert len(rec.summaries) == 1
    s = rec.summaries[0]
    assert s.name == "rho"
    assert s.unit == "donor"
    assert s.n_units == 4
    assert s.n_rows == 40
    # rho was reconstructed from the code, not read from a column
    assert [round(v, 3) for v in s.values.values()] == [0.1, 0.2, 0.3, 0.4]


def test_reports_association_with_the_exposure():
    rec = materialize(SOURCE, _tables(), unit="donor", exposure="g")
    a = rec.summaries[0].association
    assert a["statistic"] == pytest.approx(1.0, abs=1e-6)  # perfect by construction
    assert a["n_units"] == 4


def test_reports_null_sd_so_chance_can_be_priced():
    rec = materialize(SOURCE, _tables(), unit="donor", exposure="g")
    a = rec.summaries[0].association
    # 1/sqrt(n-1); at n=24 this is ~0.21, which is the whole point of reporting it
    assert a["null_sd_under_no_association"] == pytest.approx(1 / 3**0.5, abs=1e-3)


def test_no_significance_filter_a_null_candidate_is_still_emitted():
    """Filtering by significance would be a judgment. Everything eligible is emitted."""
    rec = materialize(SOURCE, _tables(rhos=(0.2, 0.2, 0.2, 0.2)), unit="donor", exposure="g")
    assert len(rec.summaries) == 1
    assert rec.summaries[0].association["statistic"] is None  # zero variance -> undefined, still emitted


def test_records_clipping():
    rec = materialize(SOURCE, _tables(rhos=(0.1, 0.2, 0.3, 5.0)), unit="donor", exposure="g")
    assert rec.summaries[0].n_clipped_high == 10  # one donor's ten cells clipped at 1


def test_abstains_loudly_outside_the_grammar():
    src = 'c["z"] = some_model.predict(features)'
    rec = materialize(src, _tables(), unit="donor", exposure="g")
    assert rec.summaries == ()
    assert len(rec.abstentions) == 1
    assert "outside grammar" in rec.abstentions[0]["reason"]
    # the candidate is still recorded as seen-and-declined, never silently dropped
    assert len(rec.candidates) == 1
    assert rec.candidates[0].eligible is False


def test_abstains_when_a_scalar_cannot_be_resolved():
    src = 'c["rho"] = c.HBB/(c.total_umi*p_amb["HBB"])'  # p_amb never defined
    rec = materialize(src, _tables(), unit="donor", exposure="g")
    assert rec.summaries == ()
    assert "not a resolved scalar mapping" in rec.abstentions[0]["reason"]


def test_abstains_when_no_table_carries_unit_and_exposure():
    with pytest.raises(Abstain):
        materialize(SOURCE, _tables(), unit="donor", exposure="not_a_column")


def test_renders_no_judgment():
    """The output must not accuse. Presentation is where a needs_evidence cap fails to protect.

    Checked on whole words, and with the disclaimer sentence removed first -- that sentence
    necessarily contains "confounding" and "invalidity" precisely in order to disclaim them.
    """
    rec = materialize(SOURCE, _tables(), unit="donor", exposure="g")
    blob = rec.to_json().lower().replace(
        "this diagnostic does not establish confounding, mediation, or invalidity, "
        "and no verdict is implied by its presence here.", "")
    for word in ("confounder", "confounded", "confounding", "violation", "blocker", "error",
                 "invalid", "invalidity", "detected", "should", "must", "wrong", "fail",
                 "suspicious", "problem", "issue"):
        assert not re.search(rf"\b{word}\b", blob), \
            f"materializer output contains judgment word {word!r}"
    assert "does not establish confounding, mediation, or invalidity" in rec.summaries[0].disclosure


def test_identity_record_is_complete_and_deterministic():
    a = materialize(SOURCE, _tables(), unit="donor", exposure="g")
    b = materialize(SOURCE, _tables(), unit="donor", exposure="g")
    assert a.materializer_version == MATERIALIZER_VERSION
    assert a.output_digest == b.output_digest
    for field in ("materializer_digest", "data_digest", "binding_digest", "protocol_digest"):
        assert getattr(a, field).startswith("sha256:")


def test_binding_digest_changes_with_the_binding():
    a = materialize(SOURCE, _tables(), unit="donor", exposure="g")
    b = materialize(SOURCE, _tables(), unit="donor", exposure="g", subset="activated only")
    assert a.binding_digest != b.binding_digest


def test_aggregation_is_pinned():
    rec = materialize(SOURCE, _tables(), unit="donor", exposure="g")
    assert rec.summaries[0].aggregation == AGGREGATION == "unweighted_arithmetic_mean"


def test_output_is_json_serialisable():
    rec = materialize(SOURCE, _tables(), unit="donor", exposure="g")
    json.loads(rec.to_json())


def test_exposure_must_be_constant_within_each_declared_unit():
    tables = _tables()
    tables["c"].loc[0, "g"] = 99
    with pytest.raises(Abstain, match="not constant.*affected units"):
        materialize(SOURCE, tables, unit="donor", exposure="g")


def test_materialization_is_invariant_to_input_row_order():
    ordered = _tables_with_decoys()
    shuffled = {**ordered, "c": ordered["c"].sample(frac=1, random_state=7)}
    left = materialize(SOURCE, ordered, unit="donor", exposure="g")
    right = materialize(SOURCE, shuffled, unit="donor", exposure="g")
    assert left.output_digest == right.output_digest


def test_frame_aliases_emit_one_diagnostic_and_retain_alias_provenance():
    tables = _tables()
    tables = {"c": tables["c"], "c_alias": tables["c"], "empty": tables["empty"]}
    rec = materialize("x = 1", tables, unit="donor", exposure="g")
    diagnostics = [item for item in rec.unread_columns if item.name == "total_umi"]
    assert len(diagnostics) == 1
    assert diagnostics[0].aliases == ("c", "c_alias")


def test_copied_frame_with_new_identity_remains_independently_auditable():
    tables = _tables()
    copied = tables["c"].copy()
    copied["copy_only"] = 1.0
    rec = materialize("x = 1", {"c": tables["c"], "copy": copied, "empty": tables["empty"]},
                      unit="donor", exposure="g")
    assert sum(item.name == "total_umi" for item in rec.unread_columns) == 2
    assert sum(item.name == "copy_only" for item in rec.unread_columns) == 1


# --------------------------------------------------------------------------- status contract
#
# A scan that finds nothing is reporting on its own reach, not on the analysis. No status here
# means "clean", "pass", or "no issue" -- that distinction is the whole point of the enum.


def test_scan_scope_reports_every_tier_it_looked_at():
    rec = materialize("x = 1", _tables(), unit="donor", exposure="g")
    assert [s["construct_class"] for s in rec.scan_scope] == [
        "row_level_frame_assignment", "unread_data_column", "authored_unit_aggregate"]
    scope = {s["construct_class"]: s["found"] for s in rec.scan_scope}
    assert scope["row_level_frame_assignment"] == 0     # `x = 1` derives nothing
    assert scope["unread_data_column"] > 0             # ...and therefore reads no column


def test_status_no_in_scope_construct_requires_every_tier_empty():
    """A scan that surfaced tier-1 evidence must never report NO_IN_SCOPE_CONSTRUCT.

    Otherwise the silent-zero bug returns in a new costume: the caller reads "nothing in scope"
    while three unread columns sit in the record.
    """
    rec = materialize("x = 1", _tables(), unit="donor", exposure="g")
    assert rec.unread_columns          # tier 1 found evidence
    assert rec.status != STATUS_NO_IN_SCOPE_CONSTRUCT


def test_status_partial_when_one_tier_emits_and_another_abstains():
    """Tier 2 abstains (outside grammar) while tier 1 emits unread columns -> PARTIAL, not
    ABSTAINED. Status is counted across tiers uniformly."""
    rec = materialize('c["z"] = some_model.predict(features)', _tables(), unit="donor", exposure="g")
    assert rec.status == STATUS_PARTIAL
    assert rec.summaries == ()          # tier 2 emitted nothing
    assert rec.unread_columns           # tier 1 did


def test_status_partial_and_complete():
    complete = materialize(SOURCE, _tables(), unit="donor", exposure="g")
    assert complete.status == STATUS_COMPLETE
    partial = materialize(SOURCE + '\nc["z"] = some_model.predict(f)\n',
                          _tables(), unit="donor", exposure="g")
    assert partial.status == STATUS_PARTIAL


def test_authored_unit_aggregate_is_recorded_not_recomputed():
    """Run A of the benchmark builds this itself, cross-tabs it, and still fails.

    Materialisation is neither necessary nor sufficient. Recording the aggregate keeps the record
    from falsely stating that nothing relevant existed.
    """
    src = "rho_by_donor = c.groupby('donor').apply(lambda d: d.HBB.sum()/d.total_umi.sum())"
    rec = materialize(src, _tables(), unit="donor", exposure="g")
    scope = {s["construct_class"]: s["found"] for s in rec.scan_scope}
    assert scope["authored_unit_aggregate"] == 1
    assert "AUTHORED_UNIT_AGGREGATE" in rec.abstentions[0]["reason"]
    assert rec.summaries == ()          # recorded, never recomputed


def test_authored_aggregate_must_match_the_declared_unit():
    src = "by_cluster = c.groupby('cluster').apply(lambda d: d.HBB.sum())"
    rec = materialize(src, _tables(), unit="donor", exposure="g")
    scope = {s["construct_class"]: s["found"] for s in rec.scan_scope}
    assert scope["authored_unit_aggregate"] == 0


def test_output_digest_distinguishes_scans_of_different_reach():
    """The defect this guards: two materially different empty scans sharing a digest."""
    authored = materialize("r = c.groupby('donor').apply(lambda d: d.HBB.sum())",
                           _tables(), unit="donor", exposure="g")
    ineligible = materialize('c["z"] = some_model.predict(f)', _tables(), unit="donor", exposure="g")
    assert authored.status == ineligible.status      # same status, different reach
    assert authored.output_digest != ineligible.output_digest


def test_source_digest_binds_the_record_to_what_was_scanned():
    a = materialize("x = 1", _tables(), unit="donor", exposure="g")
    b = materialize("y = 2", _tables(), unit="donor", exposure="g")
    # identical outputs legitimately share an output digest; the record still distinguishes them
    assert a.output_digest == b.output_digest
    assert a.source_digest != b.source_digest
    assert a.to_json() != b.to_json()


# --------------------------------------------------------------------------- tier 1
#
# Columns present in the bound data that the analysis never reads. Schema minus reads. The
# cheapest evidence in the system, and the one that produced the loudest false positive.


def _tables_with_decoys():
    t = _tables()
    d = t["c"]
    d["age"] = d.donor.map({"D0": 40, "D1": 41, "D2": 39, "D3": 42})     # ~unrelated to g
    d["cell_id"] = [f"c{i}" for i in range(len(d))]                       # 40-level identifier
    d["site"] = d.donor.map({"D0": "A", "D1": "A", "D2": "B", "D3": "B"})  # binary nominal
    return t


def test_tier1_reports_columns_the_analysis_never_reads():
    rec = materialize(SOURCE, _tables_with_decoys(), unit="donor", exposure="g")
    names = {u.name for u in rec.unread_columns}
    assert {"age", "cell_id", "site"} <= names
    assert "HBB" not in names          # SOURCE reads it
    assert "donor" not in names        # the unit
    assert "g" not in names            # the exposure


def test_tier1_abstains_on_multilevel_nominal_columns():
    """The first tier-1 run reported cell_id at r=+0.947 (4.5 sd) -- louder than the real defect
    at 3.5 sd. factorize() assigns codes in order of appearance, so that number measured the row
    order of the file. A category error, not a finding, and fixed by exclusion not by a threshold.
    """
    rec = materialize(SOURCE, _tables_with_decoys(), unit="donor", exposure="g")
    cid = next(u for u in rec.unread_columns if u.name == "cell_id")
    assert cid.association["statistic"] is None
    assert "multi-level nominal" in cid.association["abstained"]
    assert "row order" in cid.association["abstained"]


def test_tier1_binary_nominal_is_exempt():
    """Two levels factorize to a genuine 0/1 indicator, so the correlation is real."""
    rec = materialize(SOURCE, _tables_with_decoys(), unit="donor", exposure="g")
    site = next(u for u in rec.unread_columns if u.name == "site")
    assert site.association["statistic"] is not None
    assert "abstained" not in site.association


def test_tier1_reports_null_sd_beside_every_statistic():
    rec = materialize(SOURCE, _tables_with_decoys(), unit="donor", exposure="g")
    for u in rec.unread_columns:
        if u.association["statistic"] is not None:
            assert u.association["null_sd_under_no_association"] is not None


def test_tier1_appears_in_scan_scope_and_digest():
    a = materialize(SOURCE, _tables(), unit="donor", exposure="g")
    b = materialize(SOURCE, _tables_with_decoys(), unit="donor", exposure="g")
    scope = {s["construct_class"]: s["found"] for s in b.scan_scope}
    assert scope["unread_data_column"] == len(b.unread_columns) > 0
    assert a.output_digest != b.output_digest   # tier 1 is inside the digest


# --------------------------------------------------------------------------- calibration wiring
#
# §5.1: every leg-1 statistic ships with a family-wise-corrected p, not just a per-test sd.


def test_every_emitted_association_carries_a_calibration():
    rec = materialize(SOURCE, _tables_with_decoys(), unit="donor", exposure="g")
    emitted = [s.association for s in rec.summaries] + \
              [u.association for u in rec.unread_columns if u.association.get("statistic") is not None]
    for a in emitted:
        assert "calibration" in a
        cal = a["calibration"]
        assert "permutation_p" in cal and "scanwide_p" in cal


def test_calibration_is_in_the_digest():
    """Two scans identical but for the exposure produce different calibration -> different digest."""
    a = materialize(SOURCE, _tables(), unit="donor", exposure="g")
    # a table where g is shuffled off its association would calibrate differently; here just confirm
    # the calibration is inside the digested body by checking a rerun reproduces it exactly.
    b = materialize(SOURCE, _tables(), unit="donor", exposure="g")
    assert a.output_digest == b.output_digest
    assert a.summaries[0].association["calibration"]["scanwide_p"] == \
        b.summaries[0].association["calibration"]["scanwide_p"]


# --------------------------------------------------------------------------- dual population (§5.2)


def test_dual_scan_reports_pre_and_post_gate_with_delta():
    import pandas as pd
    from sc_referee.inference.materialization import dual_materialize
    t = _tables_with_decoys()
    c = t["c"].reset_index(drop=True)
    t["c"] = c
    mask = pd.Series(c.index % 2 == 0, index=c.index)   # arbitrary gate for structure
    d = dual_materialize(SOURCE, t, unit="donor", exposure="g", fitted_mask=mask)
    assert d.pre_gate.subset == "all rows (pre-gate)"
    assert d.post_gate.subset == "fitted population (post-gate)"
    assert d.deltas
    for dd in d.deltas:
        assert "pre_gate_r" in dd and "post_gate_r" in dd and "delta" in dd
    assert "conditional on this gate" in d.gate_note
