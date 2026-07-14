import math
import pytest
from sc_referee.row_ledger_digest import canonical_bytes, ledger_digest


def test_digest_is_domain_separated_and_order_and_multiplicity_sensitive():
    values = {ledger_digest("source-occurrences", x) for x in
              (("c1", "c2"), ("c2", "c1"), ("c1", "c2", "c2"))}
    values.add(ledger_digest("fitted-occurrences", ("c1", "c2")))
    assert len(values) == 4
    assert all(value.startswith("sha256:") for value in values)


def test_scalar_tags_do_not_collapse_python_equal_values():
    assert canonical_bytes(True) != canonical_bytes(1)
    assert canonical_bytes(1) != canonical_bytes(1.0)
    assert canonical_bytes(None) != canonical_bytes("None")
    assert canonical_bytes(-0.0) != canonical_bytes(0.0)


def test_nonfinite_and_unordered_values_are_rejected():
    for value in (math.nan, math.inf, -math.inf, {"x"}, {"x": 1}):
        with pytest.raises((TypeError, ValueError)):
            canonical_bytes(value)


def test_digest_has_a_frozen_golden_vector():
    assert ledger_digest("source-occurrences", ("c1", 2, None)) == \
        "sha256:f6c71f79fba8372ce6a3f71a2c721b6dfd00d5d9ec3e1d0589bc9a2130739af4"
