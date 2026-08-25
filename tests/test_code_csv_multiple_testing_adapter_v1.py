from __future__ import annotations

import pytest

from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v1 import _parse_csv

BASE = b"group,m1,m2,m3\na,1,2,3\na,2,3,4\nb,4,5,6\nb,5,6,7\n"


def test_authorized_csv_domain_derives_only_group_domain_and_finite_family_cells() -> None:
    facts = _parse_csv(
        BASE,
        group_column="group",
        outcome_columns=("m1", "m2", "m3"),
    )
    assert not isinstance(facts, str)
    assert facts.header == ("group", "m1", "m2", "m3")
    assert facts.row_count == 4
    assert facts.group_values == ("a", "b")
    assert facts.group_counts == (2, 2)


@pytest.mark.parametrize("value", [b"", b"nan", b"NaN", b"inf", b"-inf", b"text"])
def test_every_authorized_outcome_cell_must_be_finite_numeric(value: bytes) -> None:
    mutated = BASE.replace(b"a,1,2,3", b"a," + value + b",2,3")
    assert (
        _parse_csv(
            mutated,
            group_column="group",
            outcome_columns=("m1", "m2", "m3"),
        )
        == "authorized-family-csv-domain-unavailable"
    )


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (
            b"group,m1,m2,m3\na,1,2,3\nb,4,5,6\nb,5,6,7\n",
            "authorized-family-csv-domain-unavailable",
        ),
        (
            BASE + b"c,7,8,9\nc,8,9,10\n",
            "authorized-group-domain-not-exactly-two",
        ),
    ],
)
def test_group_domain_requires_exactly_two_values_and_two_rows_each(
    content: bytes, expected: str
) -> None:
    reason = _parse_csv(
        content,
        group_column="group",
        outcome_columns=("m1", "m2", "m3"),
    )
    assert reason == expected


def test_ordered_outcome_headers_must_all_exist() -> None:
    assert (
        _parse_csv(
            BASE,
            group_column="group",
            outcome_columns=("m1", "m2", "missing"),
        )
        == "authorized-family-csv-domain-unavailable"
    )
