from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from sc_referee.design_matrix import DesignMatrixError, build_fixed_effect_matrix


def test_builder_preserves_continuous_values_and_treatment_codes_categories():
    rows = pd.DataFrame(
        {
            "age": [20.0, 40.0, 60.0, 80.0],
            "batch": ["b", "a", "b", "a"],
        },
        index=["r3", "r1", "r4", "r2"],
    )
    built = build_fixed_effect_matrix(
        rows,
        source_columns=("age", "batch"),
        column_kinds={"age": "continuous", "batch": "categorical"},
        categorical_levels={"batch": ("a", "b")},
        intercept=True,
    )

    assert built.column_ids == ("intercept", "age", "batch[level=b]")
    np.testing.assert_array_equal(built.matrix[:, 1], rows["age"].to_numpy())
    np.testing.assert_array_equal(built.matrix[:, 2], [1.0, 0.0, 1.0, 0.0])
    assert built.source_slices == {"age": (1,), "batch": (2,)}
    assert built.row_identity.index_labels == ("r3", "r1", "r4", "r2")


@pytest.mark.parametrize("bad", ["missing", "age + batch", "scale(age)"])
def test_builder_accepts_only_exact_column_labels(bad):
    rows = pd.DataFrame({"age": [20.0, 40.0]})
    with pytest.raises(DesignMatrixError):
        build_fixed_effect_matrix(
            rows,
            source_columns=(bad,),
            column_kinds={bad: "continuous"},
            categorical_levels={},
            intercept=True,
        )


def test_explicit_category_level_order_is_authoritative():
    rows = pd.DataFrame({"group": [2, 1, 3, 2]})
    built = build_fixed_effect_matrix(
        rows,
        source_columns=("group",),
        column_kinds={"group": "categorical"},
        categorical_levels={"group": (2, 3, 1)},
        intercept=True,
    )

    assert built.column_ids == ("intercept", "group[level=3]", "group[level=1]")
    np.testing.assert_array_equal(
        built.matrix,
        np.array(
            [
                [1.0, 0.0, 0.0],
                [1.0, 0.0, 1.0],
                [1.0, 1.0, 0.0],
                [1.0, 0.0, 0.0],
            ]
        ),
    )


@pytest.mark.parametrize(
    ("values", "levels", "match"),
    [
        (["a", "c"], ("a", "b"), "unlisted"),
        (["a", "b"], ("a", "b", "c"), "unused"),
        (["a", None], ("a", "b"), "missing"),
    ],
)
def test_categorical_values_must_match_the_complete_level_ledger(values, levels, match):
    rows = pd.DataFrame({"group": values})
    with pytest.raises(DesignMatrixError, match=match):
        build_fixed_effect_matrix(
            rows,
            source_columns=("group",),
            column_kinds={"group": "categorical"},
            categorical_levels={"group": levels},
            intercept=True,
        )


@pytest.mark.parametrize(
    ("values", "kind"),
    [
        ([True, False], "continuous"),
        ([True, False], "categorical"),
        ([1.0, np.nan], "continuous"),
        ([1.0, np.inf], "continuous"),
    ],
)
def test_boolean_missing_and_nonfinite_sources_are_rejected(values, kind):
    rows = pd.DataFrame({"value": values})
    levels = {"value": tuple(values)} if kind == "categorical" else {}
    with pytest.raises(DesignMatrixError):
        build_fixed_effect_matrix(
            rows,
            source_columns=("value",),
            column_kinds={"value": kind},
            categorical_levels=levels,
            intercept=True,
        )


@pytest.mark.parametrize(
    ("kinds", "match"),
    [
        ({}, "missing"),
        ({"age": "continuous", "extra": "continuous"}, "extra"),
        ({"age": "ordinal"}, "invalid"),
    ],
)
def test_column_kind_ledger_must_be_exact(kinds, match):
    rows = pd.DataFrame({"age": [20.0, 40.0]})
    with pytest.raises(DesignMatrixError, match=match):
        build_fixed_effect_matrix(
            rows,
            source_columns=("age",),
            column_kinds=kinds,
            categorical_levels={},
            intercept=True,
        )


def test_integer_coded_source_remains_categorical_when_ratified_as_such():
    rows = pd.DataFrame({"site": [10, 20, 10, 20]})
    built = build_fixed_effect_matrix(
        rows,
        source_columns=("site",),
        column_kinds={"site": "categorical"},
        categorical_levels={"site": (10, 20)},
        intercept=False,
    )

    assert built.column_ids == ("site[level=20]",)
    np.testing.assert_array_equal(built.matrix[:, 0], [0.0, 1.0, 0.0, 1.0])


def test_duplicate_source_names_are_not_silently_deduplicated():
    rows = pd.DataFrame({"age": [20.0, 40.0]})
    with pytest.raises(DesignMatrixError, match="duplicate"):
        build_fixed_effect_matrix(
            rows,
            source_columns=("age", "age"),
            column_kinds={"age": "continuous"},
            categorical_levels={},
            intercept=True,
        )


def test_empty_source_list_builds_intercept_only():
    rows = pd.DataFrame(index=["s2", "s1", "s3"])
    built = build_fixed_effect_matrix(
        rows,
        source_columns=(),
        column_kinds={},
        categorical_levels={},
        intercept=True,
    )

    assert built.column_ids == ("intercept",)
    assert built.source_slices == {}
    np.testing.assert_array_equal(built.matrix, np.ones((3, 1)))


def test_row_identity_is_stable_and_sensitive_to_order():
    rows = pd.DataFrame({"age": [20.0, 40.0]}, index=["s2", "s1"])
    kwargs = dict(
        source_columns=("age",),
        column_kinds={"age": "continuous"},
        categorical_levels={},
        intercept=True,
    )

    first = build_fixed_effect_matrix(rows, **kwargs)
    second = build_fixed_effect_matrix(rows.copy(), **kwargs)
    reordered = build_fixed_effect_matrix(rows.iloc[::-1], **kwargs)

    assert first.row_identity == second.row_identity
    assert first.row_identity.digest.startswith("sha256:")
    assert first.row_identity.digest != reordered.row_identity.digest


def test_reference_to_test_contrast_has_exact_coefficient_orientation():
    rows = pd.DataFrame({"group": ["a", "b", "c", "a"]})
    built = build_fixed_effect_matrix(
        rows,
        source_columns=("group",),
        column_kinds={"group": "categorical"},
        categorical_levels={"group": ("a", "b", "c")},
        intercept=True,
    )

    np.testing.assert_array_equal(
        built.reference_to_test_contrast("group", "a", "c"), [0.0, 0.0, 1.0]
    )
    np.testing.assert_array_equal(
        built.reference_to_test_contrast("group", "b", "c"), [0.0, -1.0, 1.0]
    )
    with pytest.raises(DesignMatrixError):
        built.reference_to_test_contrast("group", "missing", "c")
