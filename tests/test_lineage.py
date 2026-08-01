from __future__ import annotations

import pytest

from sc_referee.lineage import LINEAGE_GRADE_DIMENSIONS, derive_aggregate_lineage_status


def _grades(default: str, **overrides: str) -> dict[str, str]:
    return {dimension: overrides.get(dimension, default) for dimension in LINEAGE_GRADE_DIMENSIONS}


@pytest.mark.parametrize(
    ("grades", "expected"),
    [
        (_grades("complete"), "complete"),
        (_grades("missing"), "missing"),
        (_grades("unavailable"), "unavailable"),
        (_grades("opaque"), "partial"),
        (_grades("complete", execution_origin="missing"), "partial"),
        (_grades("unavailable", execution_origin="missing"), "missing"),
        (_grades("complete", semantic_origin="partial"), "partial"),
    ],
)
def test_multidimensional_lineage_aggregate_is_fail_closed(
    grades: dict[str, str], expected: str
) -> None:
    assert derive_aggregate_lineage_status(grades) == expected  # type: ignore[arg-type]


def test_multidimensional_lineage_aggregate_rejects_missing_or_extra_dimensions() -> None:
    missing = _grades("complete")
    missing.pop("semantic_origin")
    with pytest.raises(ValueError, match="exactly the six"):
        derive_aggregate_lineage_status(missing)  # type: ignore[arg-type]

    extra = _grades("complete")
    extra["invented_origin"] = "complete"
    with pytest.raises(ValueError, match="exactly the six"):
        derive_aggregate_lineage_status(extra)  # type: ignore[arg-type]


def test_multidimensional_lineage_aggregate_rejects_unknown_status() -> None:
    invalid = _grades("complete", semantic_origin="confident")
    with pytest.raises(ValueError, match="unsupported status"):
        derive_aggregate_lineage_status(invalid)  # type: ignore[arg-type]
