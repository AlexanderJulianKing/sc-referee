"""Named v2.0.4 regressions for the copy-dosage dataflow grammar.

The workflows below are parsed as source and statically traced. They are never
executed.
"""

from __future__ import annotations

import ast

from sc_referee.scientific_checks.copy_dosage_dataflow import (
    _document_dose_representations,
)

EXPECTATION = "posterior_expectation"

_HEAD = """import numpy as np
import pandas as pd
import statsmodels.api as sm
from pathlib import Path
from sklearn.linear_model import LogisticRegression, RidgeCV

frame = pd.read_csv(Path('inputs/assay.csv'))
features = frame[['marker_a', 'marker_b']]
outcome = frame['phenotype']
"""
_CLASSIFIER = "classifier = LogisticRegression().fit(features, frame['copy_state'])\n"
_PROBABILITIES = "probabilities = classifier.predict_proba(features)\n"
_EXPECTED = "expected = probabilities @ np.array([0, 1, 2])\n"
_CALIBRATOR = "calibrator = RidgeCV().fit(features, frame['copy_index'])\n"
_TAIL = "Path('results/report.md').write_text(f'coefficient {fit.params[1]}')\n"


def _fit(design: str = "dosage") -> str:
    return f"fit = sm.OLS(outcome, sm.add_constant({design})).fit()\n"


def _calibration_workflow(body: str) -> str:
    return _HEAD + _CALIBRATOR + body + _fit() + _TAIL


def _resolve(source: str) -> tuple[bool, set[str]]:
    outcome = _document_dose_representations(ast.parse(source))
    return outcome["unsupported"], {item.state for item in outcome["classifications"]}


def _assert_abstains(source: str) -> None:
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def _residual_workflow(expression: str, *, prelude: str = "") -> str:
    return (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "residual_model = RidgeCV().fit(features, frame['residual'])\n"
        + "residual = residual_model.predict(features)\n"
        + prelude
        + f"dosage = {expression}\n"
        + _fit()
        + _TAIL
    )


def test_regression_round5_f1_zero_left_factor_abstains() -> None:
    """Reviewer spelling: ``expected.round() + 0 * residual``."""

    _assert_abstains(_residual_workflow("expected.round() + 0 * residual"))


def test_regression_round5_f1_zero_right_factor_abstains() -> None:
    """Reviewer spelling: ``expected.round() + residual * 0.0``."""

    _assert_abstains(_residual_workflow("expected.round() + residual * 0.0"))


def test_regression_round5_f1_zero_exponent_abstains() -> None:
    """Reviewer spelling: ``expected.round() * residual ** 0``."""

    _assert_abstains(_residual_workflow("expected.round() * residual ** 0"))


def test_regression_round5_f1_collapsing_numpy_clip_abstains() -> None:
    """Reviewer spelling: ``expected.round() + np.clip(residual, 0, 0)``."""

    _assert_abstains(_residual_workflow("expected.round() + np.clip(residual, 0, 0)"))


def test_regression_round5_f1_floor_plus_zero_factor_abstains() -> None:
    """Reviewer spelling: ``np.floor(expected) + 0 * residual``."""

    _assert_abstains(_residual_workflow("np.floor(expected) + 0 * residual"))


def test_regression_round5_f1_bound_zero_factor_abstains() -> None:
    """Reviewer spelling: ``w = 0.0; expected.round() + w * residual``."""

    _assert_abstains(_residual_workflow("expected.round() + w * residual", prelude="w = 0.0\n"))


def test_regression_round5_f1_collapsing_method_clip_abstains() -> None:
    """The collapse rule covers the method spelling as a category."""

    _assert_abstains(_residual_workflow("expected.round() + residual.clip(0, 0)"))


def test_regression_round5_f1_bound_collapsing_clip_abstains() -> None:
    """Exact clip bounds reached through names cannot hide a collapse."""

    _assert_abstains(
        _residual_workflow(
            "expected.round() + np.clip(residual, lower, upper)",
            prelude="lower = 0.0\nupper = 0.0\n",
        )
    )


def test_regression_round5_f1_unread_clip_bounds_abstain() -> None:
    """A clip range not proved non-collapsing cannot restore continuity."""

    _assert_abstains(
        _residual_workflow(
            "expected.round() + np.clip(residual, lower, upper)",
            prelude="lower = frame['lower']\nupper = frame['upper']\n",
        )
    )


def test_regression_round5_f1_dependent_residual_control_still_abstains() -> None:
    """Held control: the same residual added and removed is not restoration."""

    _assert_abstains(_residual_workflow("expected.round() + residual - residual"))


def test_regression_round5_f1_exact_nonzero_factor_may_restore() -> None:
    """Exact nonzero constants remain distinguishable from exact zeros."""

    unsupported, states = _resolve(_residual_workflow("expected.round() + 0.5 * residual"))
    assert not unsupported
    assert states == {EXPECTATION}


def test_regression_round5_f3_restoration_origin_is_operand_order_independent() -> None:
    """Swapping arithmetic operands cannot change the asserted representation."""

    left = _resolve(_residual_workflow("expected.round() + 0.5 * residual"))
    right = _resolve(_residual_workflow("0.5 * residual + expected.round()"))
    assert left == right == (False, {EXPECTATION})


def _estimator_drift_workflow(estimator_definitions: str) -> str:
    return _calibration_workflow(
        "raw = calibrator.predict(features)\n"
        + estimator_definitions
        + "drift = second.predict(features) - third.predict(features)\n"
        + "dosage = raw.round() + drift\n"
    )


def test_regression_round5_f2_chained_fit_idiom_merges_second_and_third() -> None:
    """Reviewer chained spelling: two equal RidgeCV fits are one identity."""

    _assert_abstains(
        _estimator_drift_workflow(
            "second = RidgeCV().fit(features, frame['copy_index'])\n"
            "third = RidgeCV().fit(features, frame['copy_index'])\n"
        )
    )


def test_regression_round5_f2_reassigned_fit_idiom_merges_second_and_third() -> None:
    """Idiom matrix: ``c = C(); c = c.fit(X, y)``."""

    _assert_abstains(
        _estimator_drift_workflow(
            "second = RidgeCV()\n"
            "second = second.fit(features, frame['copy_index'])\n"
            "third = RidgeCV()\n"
            "third = third.fit(features, frame['copy_index'])\n"
        )
    )


def test_regression_round5_f2_helper_bare_fit_idiom_merges_second_and_third() -> None:
    """Idiom matrix: a builder returns a receiver fitted by a bare call."""

    _assert_abstains(
        _estimator_drift_workflow(
            "def build(values, labels):\n"
            "    model = RidgeCV()\n"
            "    model.fit(values, labels)\n"
            "    return model\n\n"
            "second = build(features, frame['copy_index'])\n"
            "third = build(features, frame['copy_index'])\n"
        )
    )


def test_regression_round5_f2_bare_fit_idiom_merges_second_and_third() -> None:
    """Reviewer bare-statement spelling: the receiver gains its fitted identity."""

    _assert_abstains(
        _estimator_drift_workflow(
            "second = RidgeCV()\n"
            "second.fit(features, frame['copy_index'])\n"
            "third = RidgeCV()\n"
            "third.fit(features, frame['copy_index'])\n"
        )
    )
