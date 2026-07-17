"""Tests for correction-coverage v0.

Static only: no data is bound anywhere in this file, because the scanner needs none.
"""
import json
import re

from sc_referee.inference.correction_coverage import (
    STATUS_COMPLETE,
    STATUS_NO_IN_SCOPE_CONSTRUCT,
    STATUS_PRECONDITION_FAILED,
    scan,
)

# The benchmark shape: a factor built for five keys, applied to two, with the three skipped ones
# read by the gate that selects the analysis population.
PARTIAL = '''
genes = ["HBB","IFI6","ISG15","LST1","CXCL10"]
p_amb = {g: empty[g].sum()/empty.total_umi.sum() for g in genes}
feats = np.column_stack([np.log1p(c[g]/c.total_umi*1000) for g in ["IFI6","ISG15","LST1"]])
gm = GaussianMixture(n_components=2).fit(feats)
amb = rho*tu*p_amb["CXCL10"]
rho = c.HBB/(c.total_umi*p_amb["HBB"])
'''


def test_partial_application_is_the_fact():
    rec = scan(PARTIAL)
    assert rec.status == STATUS_COMPLETE
    assert len(rec.producers) == 1
    p = rec.producers[0]
    assert p.name == "p_amb"
    assert set(p.computed_keys) == {"HBB", "IFI6", "ISG15", "LST1", "CXCL10"}
    assert set(p.applied_keys) == {"HBB", "CXCL10"}
    assert set(p.unapplied_keys) == {"IFI6", "ISG15", "LST1"}
    assert len(rec.disclosures) == 1


def test_links_unapplied_keys_to_the_selecting_construct():
    rec = scan(PARTIAL)
    text = rec.disclosures[0]["text"]
    assert "read by the construct at line" in text
    for gene in ("IFI6", "ISG15", "LST1"):
        assert gene in text


def test_full_application_says_nothing():
    src = '''
genes = ["HBB","CXCL10"]
p_amb = {g: empty[g].sum()/empty.total_umi.sum() for g in genes}
a = p_amb["HBB"]
b = p_amb["CXCL10"]
'''
    rec = scan(src)
    assert rec.producers[0].unapplied_keys == ()
    assert rec.disclosures == ()


def test_zero_application_is_not_this_fact():
    """Computed and never applied at all is dead or duplicated code, not an inconsistency.

    Admitting it produced 6 disclosures on one benchmark transcript, 5 of them noise.
    """
    src = '''
genes = ["HBB","CXCL10"]
p_amb = {g: empty[g].sum()/empty.total_umi.sum() for g in genes}
'''
    rec = scan(src)
    assert rec.producers[0].applied_keys == ()
    assert rec.disclosures == ()
    scope = {s["construct_class"]: s["found"] for s in rec.scan_scope}
    assert scope["unused_producer"] == 1          # recorded...
    assert scope["partially_applied_producer"] == 0  # ...but not disclosed


def test_identical_facts_from_two_producers_are_one_fact():
    """Run B of the benchmark builds the same profile twice."""
    src = PARTIAL + '''
amb2 = {g: empty[g].sum()/empty.total_umi.sum() for g in genes}
z = amb2["CXCL10"] + amb2["HBB"]
'''
    rec = scan(src)
    assert len(rec.producers) == 2
    assert len(rec.disclosures) == 1   # deduped by (computed, applied)


def test_series_shaped_producer_is_recognised():
    """`amb = empty[genes].sum()/empty['total_umi'].sum()` — runs B and C use this shape."""
    src = '''
genes = ["HBB","IFI6","CXCL10"]
amb = empty[genes].sum()/empty['total_umi'].sum()
x = amb['CXCL10']
'''
    rec = scan(src)
    assert set(rec.producers[0].computed_keys) == {"HBB", "IFI6", "CXCL10"}
    assert set(rec.producers[0].unapplied_keys) == {"HBB", "IFI6"}


def test_one_hop_alias_counts_as_application():
    src = '''
genes = ["HBB","CXCL10"]
amb = {g: empty[g].sum()/empty.total_umi.sum() for g in genes}
b = amb
x = b["CXCL10"]
'''
    rec = scan(src)
    assert set(rec.producers[0].applied_keys) == {"CXCL10"}
    assert set(rec.producers[0].unapplied_keys) == {"HBB"}


def test_no_producer_is_not_clean():
    rec = scan("x = 1")
    assert rec.status == STATUS_NO_IN_SCOPE_CONSTRUCT
    assert all(s["found"] == 0 for s in rec.scan_scope)


def test_unparseable_source_fails_loudly():
    rec = scan("def broken(:")
    assert rec.status == STATUS_PRECONDITION_FAILED


def test_renders_no_judgment():
    rec = scan(PARTIAL)
    blob = rec.to_json().lower()
    for phrase in ("does not establish that the unapplied keys should have been corrected",
                   "does not establish"):
        assert phrase in blob
    stripped = blob.replace(
        "this diagnostic reports coverage only. it does not establish that the unapplied keys "
        "should have been corrected, nor that the analysis is incorrect.", "").replace(
        "reported as a dependency fact; whether the selection should read a corrected form is "
        "not established here.", "")
    for word in ("violation", "blocker", "invalid", "wrong", "bug", "must",
                 "should", "confounder", "detected", "failure"):
        assert not re.search(rf"\b{word}\b", stripped), f"judgment word {word!r} in output"


def test_needs_no_data():
    """The whole point: this reaches 4/4 benchmark transcripts with nothing bound."""
    rec = scan(PARTIAL)               # no dataframes, no paths, no arguments beyond source
    assert rec.disclosures
    json.loads(rec.to_json())


def test_source_digest_binds_the_record():
    a, b = scan(PARTIAL), scan(PARTIAL + "\nq = 1\n")
    assert a.source_digest != b.source_digest
