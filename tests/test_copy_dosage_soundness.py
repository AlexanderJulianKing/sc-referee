"""Soundness controls for the copy-dosage representation dataflow trace.

The invariant under test: the trace either classifies correctly or abstains;
it never answers wrongly and never crashes. The cardinal rule is that
``continuous`` is never a fallthrough, because a continuous reading under a
continuous method contract is a clean bill of health.

The first block is the wrong-answer family the audit of the retired v1.x
static-source recognizer found. Each shape rounded a continuous exposure onto
the integers on the path into the fitted model, and each one was reported as
a continuous representation, because the old recognizer read a cast as
inheriting its input's category and keyed the exposure on a variable whose
name contained ``dosage``.

The later blocks are the five soundness risks the rebuild recon raised: a
quantization that only reaches a printed table, a genuinely integer input
with no quantizer anywhere, a quantizer followed by a re-expansion, an
unreadable step on the exposure path, and a multi-regressor fit whose
exposure operand is not uniquely identifiable.
"""

from __future__ import annotations

import ast
from dataclasses import replace

import pytest

from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.parsers.python_ast import PARSER_ID as PYTHON_PARSER_ID
from sc_referee.parsers.python_ast import PARSER_VERSION as PYTHON_PARSER_VERSION
from sc_referee.scientific_checks import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    InspectionDocument,
    RecordRef,
)
from sc_referee.scientific_checks.copy_dosage_adapter import (
    _accountings,
    _identified_accounting,
)
from sc_referee.scientific_checks.copy_dosage_dataflow import (
    _CALL_READ_ONLY_ARITY,
    _METHOD_READ_ONLY_ARITY,
    _RECOGNIZED_CALL_PATHS,
    _RECOGNIZED_METHODS,
    _TEXT,
    _cast,
    _Col,
    _document_dose_representations,
    resolve_copy_dosage_dataflow,
)
from sc_referee.scientific_checks.profiles import default_scientific_check_registry
from sc_referee.scientific_checks.quantity_consistency_adapter import _number_tokens
from sc_referee.scientific_checks.scope_joins import build_static_scope_join_graph

COPY_CHECK = "check:classifier-derived-copy-dosage-representation"
HARD_OPERAND = "integer_hard_copy_state_as_numeric_dosage"
EXPECTATION_OPERAND = "continuous_posterior_expected_copy_dosage"
CALIBRATION_OPERAND = "direct_continuous_calibrated_copy_dosage"

QUANTIZED = "integer_hard_state"
EXPECTATION = "posterior_expectation"
CALIBRATION = "direct_calibration"

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


def _posterior_workflow(body: str, design: str = "dosage") -> str:
    return _HEAD + _CLASSIFIER + _PROBABILITIES + _EXPECTED + body + _fit(design) + _TAIL


def _calibration_workflow(body: str, design: str = "dosage") -> str:
    return _HEAD + _CALIBRATOR + body + _fit(design) + _TAIL


def _resolve(source: str) -> tuple[bool, set[str]]:
    outcome = _document_dose_representations(ast.parse(source))
    return outcome["unsupported"], {item.state for item in outcome["classifications"]}


def _assert_abstains(source: str) -> None:
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def _fused_observation(
    report_text: str, analysis_text: str = "value = 1\n"
) -> tuple[str, str | None]:
    """Run the released copy-dosage adapter over one report and one workflow."""

    report = report_text.encode("utf-8")
    analysis = analysis_text.encode("utf-8")
    surface_ref = RecordRef("publication_surface", "publication-surface:soundness")
    artifact_ref = RecordRef("artifact", "artifact:soundness-report")
    identity_ref = RecordRef("asset_identity", "asset-identity:soundness-report")
    report_file_ref = RecordRef("file_record", "file:soundness-report")
    report_parser_ref = RecordRef("parser_result", "parser-result:soundness-report")
    analysis_file_ref = RecordRef("file_record", "file:soundness-analysis")
    analysis_parser_ref = RecordRef("parser_result", "parser-result:soundness-analysis")
    snapshot_ref = RecordRef("repository_snapshot", "snapshot:soundness")
    report_parser = canonical_json(
        {
            "parser_id": "parser:markdown-inventory",
            "parser_version": "0.2.0",
            "state": "parsed",
        }
    ).encode("utf-8")
    analysis_parser = canonical_json(
        {
            "parser_id": PYTHON_PARSER_ID,
            "parser_version": PYTHON_PARSER_VERSION,
            "state": "parsed",
        }
    ).encode("utf-8")
    records = (
        (
            surface_ref,
            {
                "publication_surface_id": surface_ref.record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [artifact_ref.to_dict()]},
            },
        ),
        (
            artifact_ref,
            {
                "artifact_id": artifact_ref.record_id,
                "kind": "report",
                "path": "report.md",
                "asset_identity_ref": identity_ref.to_dict(),
            },
        ),
        (
            identity_ref,
            {
                "asset_identity_id": identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": artifact_ref.to_dict(),
                "identity_evidence": {"kind": "full_digest", "digest": sha256_digest(report)},
            },
        ),
        (snapshot_ref, {"snapshot_id": snapshot_ref.record_id}),
        (report_file_ref, {"file_record_id": report_file_ref.record_id}),
        (report_parser_ref, {"parser_result_id": report_parser_ref.record_id}),
        (analysis_file_ref, {"file_record_id": analysis_file_ref.record_id}),
        (analysis_parser_ref, {"parser_result_id": analysis_parser_ref.record_id}),
    )
    context = FrozenInspectionContext(
        snapshot_digest=sha256_digest("snapshot"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(
            InspectionDocument(
                path="report.md",
                file_ref=report_file_ref,
                content=report,
                content_digest=sha256_digest(report),
                media_type="text/markdown",
                parser_result_ref=report_parser_ref,
                parser_result_payload=report_parser,
                parser_result_digest=sha256_digest(report_parser),
            ),
            InspectionDocument(
                path="analysis.py",
                file_ref=analysis_file_ref,
                content=analysis,
                content_digest=sha256_digest(analysis),
                media_type="text/x-python",
                parser_result_ref=analysis_parser_ref,
                parser_result_payload=analysis_parser,
                parser_result_digest=sha256_digest(analysis_parser),
            ),
        ),
        base_records=tuple(FrozenBaseRecord.from_record(ref, value) for ref, value in records),
    )
    context = replace(
        context,
        scope_join_graph=build_static_scope_join_graph(
            snapshot_digest=context.snapshot_digest,
            snapshot_ref=snapshot_ref,
            selected_surface_ref=surface_ref,
            selected_artifact_ref=artifact_ref,
            documents=context.documents,
            base_records=context.base_records,
        ),
    )
    module = next(
        item
        for item in default_scientific_check_registry().modules
        if item.manifest.check_id == COPY_CHECK
    )
    observation = module.adapters[0].inspect(context)
    operand = observation.observed_operand
    return observation.applicability, None if operand is None else str(operand.value)


def _report_accounting(text: str) -> tuple[tuple[int, ...], int] | None:
    tokens = _number_tokens(text)
    integers = [item for item in tokens if item.is_integer and not item.is_percent]
    decimals = [item for item in tokens if not item.is_integer and not item.is_percent]
    found = _accountings(integers, decimals)
    assert found is not None
    identified = _identified_accounting(found)
    return None if identified is None else (identified.counts, identified.total)


# ---------------------------------------------------------------------------
# The wrong-answer family: quantizers the retired recognizer read as continuous.


def test_posterior_expectation_cast_to_integer_is_the_hard_state_reading() -> None:
    """``expected.astype(int)``: the shape the retired recognizer read as continuous."""

    unsupported, states = _resolve(_posterior_workflow("dosage = expected.astype(int)\n"))
    assert not unsupported
    assert states == {QUANTIZED}


def test_clipped_posterior_expectation_cast_to_integer_is_the_hard_state_reading() -> None:
    """Clipping to the copy range does not restore the continuous scale."""

    unsupported, states = _resolve(
        _posterior_workflow("dosage = expected.clip(0, 2).astype(int)\n")
    )
    assert not unsupported
    assert states == {QUANTIZED}


def test_continuous_calibration_prediction_cast_to_integer_is_the_hard_state_reading() -> None:
    """``RidgeCV().predict(...).astype(int)`` is a hard call, not a calibration."""

    unsupported, states = _resolve(
        _calibration_workflow("dosage = calibrator.predict(features).astype(int)\n")
    )
    assert not unsupported
    assert states == {QUANTIZED}


def test_a_classifier_on_unrelated_data_named_for_a_dosage_emits_nothing() -> None:
    """The retired recognizer keyed the exposure on a name containing ``dosage``.

    Nothing here computes a copy dosage: the classifier predicts a treatment
    arm and the regression exposure is a staged column. Recognition that keys
    on names would answer anyway.
    """

    source = (
        _HEAD
        + "drug_dosage = LogisticRegression().fit(features, frame['arm'])\n"
        + "fit = sm.OLS(outcome, sm.add_constant(frame['age'])).fit()\n"
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == set()


def test_probabilities_from_an_unestablished_estimator_abstain() -> None:
    """A ``predict_proba`` on a handle whose construction this trace never saw.

    The value is dose-shaped and unreadable, so it abstains; reading it as a
    continuous posterior expectation would clear a workflow this trace has not
    actually read.
    """

    source = (
        _HEAD
        + "import joblib\n"
        + "classifier = joblib.load('model.pkl')\n"
        + "dosage = classifier.predict_proba(features) @ np.array([0, 1, 2])\n"
        + _fit()
        + _TAIL
    )
    _assert_abstains(source)


# ---------------------------------------------------------------------------
# The three representations, read from operations alone.


def test_posterior_expectation_product_is_the_posterior_representation() -> None:
    unsupported, states = _resolve(_posterior_workflow("dosage = expected\n"))
    assert not unsupported
    assert states == {EXPECTATION}


def test_elementwise_weighting_then_row_sum_is_the_posterior_representation() -> None:
    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + ("dosage = (probabilities * np.array([0, 1, 2])).sum(axis=1)\n")
        + _fit()
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {EXPECTATION}


def test_continuous_calibration_prediction_is_the_direct_representation() -> None:
    unsupported, states = _resolve(_calibration_workflow("dosage = calibrator.predict(features)\n"))
    assert not unsupported
    assert states == {CALIBRATION}


def test_a_classifier_prediction_is_the_hard_state_representation() -> None:
    source = _HEAD + _CLASSIFIER + "dosage = classifier.predict(features)\n" + _fit() + _TAIL
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


@pytest.mark.parametrize(
    "expression",
    [
        "np.round(expected)",
        "np.rint(expected)",
        "np.floor(expected)",
        "np.trunc(expected)",
        "expected.round()",
        "round(expected)",
        "expected.astype('int64')",
        "expected.astype(np.int32)",
        "np.digitize(expected, [0.5, 1.5])",
        "np.searchsorted([0.5, 1.5], expected)",
        "probabilities.argmax(axis=1)",
        "expected.idxmax()",
        "np.where(expected > 1.5, 2, np.where(expected > 0.5, 1, 0))",
        "expected.map({0: 0, 1: 1, 2: 2})",
        "pd.cut(expected, [-1, 0.5, 1.5, 3], labels=[0, 1, 2])",
        "pd.qcut(expected, 3, labels=[0, 1, 2])",
        "np.array([0, 1, 2])[np.digitize(expected, [0.5, 1.5])]",
        "(expected * 2) // 1",
        "(expected > 1.0).astype(int)",
        "np.round(expected).astype(float)",
    ],
)
def test_each_quantizing_operation_reads_as_the_hard_state(expression: str) -> None:
    unsupported, states = _resolve(_posterior_workflow(f"dosage = {expression}\n"))
    assert not unsupported
    assert states == {QUANTIZED}


@pytest.mark.parametrize(
    "expression",
    [
        "expected",
        "expected.round(2)",
        "np.round(expected, 3)",
        "expected.clip(0, 2)",
        "expected * 2.0",
        "expected.astype(float)",
        "np.clip(expected, 0, 2)",
        "expected.reshape(-1, 1)",
    ],
)
def test_each_scale_preserving_operation_stays_continuous(expression: str) -> None:
    unsupported, states = _resolve(_posterior_workflow(f"dosage = {expression}\n"))
    assert not unsupported
    assert states == {EXPECTATION}


# ---------------------------------------------------------------------------
# Recon soundness risk 1: display-only quantization.


def test_a_rounded_value_written_to_a_table_is_not_the_model_exposure() -> None:
    """The continuous value feeds the fit; only the printed table is rounded."""

    source = (
        _HEAD
        + _CALIBRATOR
        + "dosage = calibrator.predict(features)\n"
        + "shown = dosage.round()\n"
        + _fit()
        + "Path('results/report.md').write_text(f'{shown} {fit.params[1]}')\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {CALIBRATION}


def test_a_rounded_value_that_does_feed_the_model_is_the_hard_state() -> None:
    """The mirror of the display-only case, to show the distinction is real."""

    source = (
        _HEAD
        + _CALIBRATOR
        + "dosage = calibrator.predict(features)\n"
        + "shown = dosage.round()\n"
        + _fit("shown")
        + "Path('results/report.md').write_text(f'{shown} {fit.params[1]}')\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


# ---------------------------------------------------------------------------
# Recon soundness risk 2: genuinely integer input with no quantizer.

_CSV_HEAD = """import csv
import numpy as np
import statsmodels.api as sm
from pathlib import Path
from sklearn.linear_model import RidgeCV

rows = list(csv.DictReader(Path('inputs/assay.csv').open()))
outcome = [float(row['phenotype']) for row in rows]
"""


def test_an_established_integer_column_feeding_the_fit_unchanged_is_the_hard_state() -> None:
    """The assay is integer-coded and the workflow never rounds.

    Parsing an integer out of staged text establishes the coding, so under a
    continuous method contract this is still the hard-state operand.
    """

    source = _CSV_HEAD + "dosage = [int(row['copy_state']) for row in rows]\n" + _fit() + _TAIL
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


def test_int_of_a_staged_text_column_is_a_parse_and_not_a_quantizer() -> None:
    """``int(row['copy_state'])`` on the label path leaves the dosage continuous.

    Treating the parse as a quantizer would classify this calibration workflow
    as a hard call, which is the mirror image of the retired cast bug.
    """

    source = (
        _CSV_HEAD
        + "labels = [int(row['copy_state']) for row in rows]\n"
        + "signal = [float(row['signal']) for row in rows]\n"
        + "calibrator = RidgeCV().fit(signal, labels)\n"
        + "dosage = calibrator.predict(signal)\n"
        + _fit()
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {CALIBRATION}


def test_a_staged_table_column_of_unestablished_type_is_never_classified() -> None:
    """Nothing here establishes whether the column was integer or float.

    A dtype guess is the one thing this recognizer may not do, so the column
    is neither a hard state nor a continuous exposure and nothing applies.
    """

    source = _HEAD + "dosage = frame['copy_state'].astype(int)\n" + _fit() + _TAIL
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == set()


def test_an_established_integer_column_that_is_rescaled_is_not_the_unchanged_path() -> None:
    """The parse establishes integer coding; the division does not survive it."""

    source = _CSV_HEAD + "dosage = [int(row['copy_state']) / 2 for row in rows]\n" + _fit() + _TAIL
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == set()


# ---------------------------------------------------------------------------
# Recon soundness risk 3: re-expansion after a quantizer.


def test_binning_followed_by_a_continuous_centre_table_is_still_a_binning() -> None:
    """``centers[digitize(x)]`` assigns a bin centre; it does not re-expand.

    Expectation changed in v2.0.1 under the ruling on finding 6. The claim
    this check implements reads "hard or binned dosage used for a continuous
    target", so a literal lookup table always bins: three bin centres are
    three levels whether they are written 0, 1, 2 or 0.12, 0.98, 1.93. The
    v2.0.0 carve-out for a table holding a non-integral value read this as
    the continuous posterior expectation, which cleared a workflow that
    delivers three distinct values to the model.
    """

    source = _posterior_workflow(
        "centers = np.array([0.12, 0.98, 1.93])\n"
        "dosage = centers[np.digitize(expected, [0.5, 1.5])]\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


def test_binning_followed_by_an_integral_table_is_still_the_hard_state() -> None:
    """A lookup table of whole numbers is another way of writing the hard call."""

    source = _posterior_workflow(
        "states = np.array([0, 1, 2])\ndosage = states[np.digitize(expected, [0.5, 1.5])]\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


def test_a_residual_against_the_rounded_value_abstains() -> None:
    """``raw - raw.round()`` subtracts a value descended from ``raw`` itself.

    Expectation changed in v2.0.1 under the ruling on finding 1. Arithmetic
    restores the continuous scale only against an operand that descends from
    no source the quantized operand descends from. Reading this pair by tag
    alone also reads ``x - x % 1``, which is ``floor(x)``, as continuous, so
    the whole family abstains.
    """

    source = _calibration_workflow(
        "raw = calibrator.predict(features)\ndosage = raw - raw.round()\n"
    )
    _assert_abstains(source)


def test_scaling_a_quantized_value_by_a_constant_does_not_restore_the_scale() -> None:
    """A finite set of values scaled by a literal is still a finite set."""

    source = _posterior_workflow("dosage = expected.round() * 0.5\n")
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


# ---------------------------------------------------------------------------
# Recon soundness risk 4: unreadable steps on the exposure path.


@pytest.mark.parametrize(
    "body",
    [
        "dosage = expected.apply(lambda value: int(value))\n",
        "dosage = expected.map(runtime_lookup)\n",
        "dosage = pd.cut(expected, [-1, 0.5, 1.5, 3])\n",
        "dosage = recode(expected)\n",
        "dosage = np.polyval(coefficients, expected)\n",
    ],
)
def test_an_unreadable_step_on_the_exposure_path_abstains(body: str) -> None:
    _assert_abstains(_posterior_workflow(body))


def test_a_pipeline_wrapped_estimator_abstains() -> None:
    """A pipeline's fitted terminal stage is not readable from its construction."""

    source = (
        _HEAD
        + "from sklearn.pipeline import make_pipeline\n"
        + "from sklearn.preprocessing import StandardScaler\n"
        + "classifier = make_pipeline(StandardScaler(), LogisticRegression())\n"
        + "classifier.fit(features, frame['copy_state'])\n"
        + "dosage = classifier.predict_proba(features) @ np.array([0, 1, 2])\n"
        + _fit()
        + _TAIL
    )
    _assert_abstains(source)


def test_an_ordered_state_vector_weighted_by_an_unestablished_value_abstains() -> None:
    source = (
        _HEAD
        + "weights = load_weights('weights.npy')\n"
        + "dosage = weights @ np.array([0, 1, 2])\n"
        + _fit()
        + _TAIL
    )
    _assert_abstains(source)


def test_a_helper_applying_a_quantizer_is_read_from_its_body() -> None:
    """A readable helper is not an unreadable step, whatever it is called."""

    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "def harmonise(value):\n    return value.round()\n\n"
        + "dosage = harmonise(expected)\n"
        + _fit()
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


def test_a_helper_whose_body_is_unreadable_abstains() -> None:
    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "def harmonise(value):\n    return custom_transform(value)\n\n"
        + "dosage = harmonise(expected)\n"
        + _fit()
        + _TAIL
    )
    _assert_abstains(source)


def test_a_recursive_helper_abstains_instead_of_crashing() -> None:
    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "def harmonise(value):\n    return harmonise(value)\n\n"
        + "dosage = harmonise(expected)\n"
        + _fit()
        + _TAIL
    )
    _assert_abstains(source)


def test_a_rebound_callable_name_is_opaque_everywhere() -> None:
    """``keep = flip`` decides at run time which body the exposure path runs."""

    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "def keep(value):\n    return value\n\n"
        + "def flip(value):\n    return value.round()\n\n"
        + "keep = flip\n"
        + "dosage = keep(expected)\n"
        + _fit()
        + _TAIL
    )
    _assert_abstains(source)


def test_a_deeply_composed_exposure_expression_abstains_without_recursion_error() -> None:
    source = _posterior_workflow("dosage = expected" + " + 1" * 1100 + "\n")
    _assert_abstains(source)


# ---------------------------------------------------------------------------
# Recon soundness risk 5: multi-regressor fits.


def test_a_multi_regressor_fit_with_a_binned_covariate_classifies_on_the_dose() -> None:
    """The binned covariate is quantized but descends from no copy model."""

    source = _posterior_workflow(
        "dosage = expected.astype(int)\nage_band = np.digitize(frame['age'], [40, 60])\n",
        design="np.column_stack([dosage, age_band])",
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


def test_a_multi_regressor_fit_with_two_copy_derived_regressors_abstains() -> None:
    """No structural rule names the exposure, and nomenclature never may."""

    source = _posterior_workflow(
        "dosage = expected.astype(int)\nhard = classifier.predict(features)\n",
        design="np.column_stack([dosage, hard])",
    )
    _assert_abstains(source)


def test_a_multi_regressor_fit_with_opaque_covariates_classifies_on_the_dose() -> None:
    source = _posterior_workflow(
        "dosage = expected.astype(int)\n",
        design="np.column_stack([dosage, frame['age'], frame['sex']])",
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


def test_two_established_integer_columns_in_one_fit_abstain() -> None:
    """Without a calibration model, two integer-coded columns are indistinguishable."""

    source = (
        _CSV_HEAD
        + "dosage = [int(row['copy_state']) for row in rows]\n"
        + "counts = [int(row['sibling_count']) for row in rows]\n"
        + _fit("np.column_stack([dosage, counts])")
        + _TAIL
    )
    _assert_abstains(source)


# ---------------------------------------------------------------------------
# Report reachability, aliasing, and assignment forms.


def test_a_fit_that_never_reaches_the_report_never_classifies() -> None:
    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "dosage = expected.astype(int)\n"
        + _fit()
        + "Path('results/report.md').write_text('a static summary')\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == set()


def test_a_write_into_an_in_memory_buffer_does_not_reach_the_report() -> None:
    source = (
        _HEAD
        + "import io\n"
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "dosage = expected.astype(int)\n"
        + _fit()
        + "buffer = io.StringIO()\n"
        + "buffer.write(f'{fit.params[1]}')\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == set()


def test_a_return_from_a_function_nobody_calls_does_not_reach_the_report() -> None:
    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "dosage = expected.astype(int)\n\n"
        + "def diagnostic():\n"
        + "    return sm.OLS(outcome, sm.add_constant(dosage)).fit()\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == set()


def test_a_return_from_a_called_function_still_reaches_the_report() -> None:
    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "dosage = expected.astype(int)\n\n"
        + "def association():\n"
        + "    return sm.OLS(outcome, sm.add_constant(dosage)).fit()\n\n"
        + "fit = association()\n"
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


def test_conflicting_report_reaching_fits_abstain() -> None:
    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "hard = expected.astype(int)\n"
        + "quantized_fit = sm.OLS(outcome, sm.add_constant(hard)).fit()\n"
        + "continuous_fit = sm.OLS(outcome, sm.add_constant(expected)).fit()\n"
        + "Path('results/report.md').write_text(\n"
        + "    f'{quantized_fit.params[1]} {continuous_fit.params[1]}'\n"
        + ")\n"
    )
    _unsupported, states = _resolve(source)
    assert states == {QUANTIZED, EXPECTATION}


def test_mutating_a_table_through_an_alias_invalidates_every_name() -> None:
    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "frame['dose'] = expected\n"
        + "alias = frame\n"
        + "alias.update(supplementary)\n"
        + _fit("frame[['dose']]")
        + _TAIL
    )
    _assert_abstains(source)


def test_an_in_place_table_operation_invalidates_the_provenance() -> None:
    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "frame['dose'] = expected\n"
        + "frame.fillna(0, inplace=True)\n"
        + _fit("frame[['dose']]")
        + _TAIL
    )
    _assert_abstains(source)


def test_a_literal_table_column_assignment_is_followed_exactly() -> None:
    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "frame['dose'] = expected.astype(int)\n"
        + _fit("frame[['dose']]")
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


@pytest.mark.parametrize(
    "assignment",
    [
        "dosage, spare = (expected.round(), None)",
        "dosage = spare = expected.round()",
        "dosage: object = expected.round()",
        "dosage = (staged := expected.round())",
    ],
)
def test_assignment_forms_the_environment_cannot_follow_abstain(assignment: str) -> None:
    _assert_abstains(_posterior_workflow(assignment + "\n"))


def test_a_guarded_rebinding_of_the_exposure_abstains() -> None:
    source = _posterior_workflow(
        "dosage = expected\nif len(features) > 10:\n    dosage = expected.round()\n"
    )
    unsupported, _states = _resolve(source)
    assert unsupported


def test_a_conditional_expression_choosing_the_exposure_abstains() -> None:
    source = _posterior_workflow(
        "harden = True\ndosage = expected.round() if harden else expected\n"
    )
    _assert_abstains(source)


def test_an_exposure_arriving_as_a_parameter_abstains_inside_the_helper() -> None:
    """The helper body is traced with its parameters masked.

    The call site still classifies, because there the argument's provenance is
    known; the masked body contributes nothing rather than letting a module
    global stand in for the parameter.
    """

    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "def association(dose):\n"
        + "    return sm.OLS(outcome, sm.add_constant(dose)).fit()\n\n"
        + "fit = association(expected)\n"
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {EXPECTATION}


# ---------------------------------------------------------------------------
# The report plane.


_HARD_STATE_REPORT = (
    "Copy state was 0 in 120 participants, 1 in 260, and 2 in 120 of the 500 genotyped "
    "participants; the mean dosage entered in the association model was 1.00.\n"
)
_HARD_STATE_REPORT_WITH_DEVIATION = (
    "Copy state was 0 in 120 participants, 1 in 260, and 2 in 120 of the 500 genotyped "
    "participants; the dosage entered in the association model had mean 1.00 and "
    "standard deviation 0.69.\n"
)
_SILENT_REPORT = (
    "The association model used the calibrated copy dosage across the cohort; the "
    "estimated coefficient was 0.42.\n"
)

_QUANTIZED_WORKFLOW = _posterior_workflow("dosage = expected.astype(int)\n")
_CONTINUOUS_WORKFLOW = _posterior_workflow("dosage = expected\n")
_CALIBRATION_WORKFLOW = _calibration_workflow("dosage = calibrator.predict(features)\n")


def test_a_stated_per_state_accounting_is_recognized() -> None:
    assert _report_accounting(_HARD_STATE_REPORT) == ((120, 260, 120), 500)


def test_a_stated_accounting_with_a_reconciling_deviation_is_recognized() -> None:
    assert _report_accounting(_HARD_STATE_REPORT_WITH_DEVIATION) == ((120, 260, 120), 500)


def test_a_report_whose_mean_does_not_reconcile_is_silent() -> None:
    text = (
        "Copy state was 0 in 120 participants, 1 in 260, and 2 in 120 of the 500 genotyped "
        "participants; the mean dosage was 1.37.\n"
    )
    assert _report_accounting(text) is None


def test_a_report_with_two_reconciling_accountings_identifies_neither() -> None:
    text = (
        "Copy state was 0 in 120 participants, 1 in 260, and 2 in 120 of the 500 genotyped "
        "participants. A replication cohort held 30, 65, and 30 of its 125 participants. "
        "The mean dosage was 1.00.\n"
    )
    assert _report_accounting(text) is None


@pytest.mark.parametrize(
    "text",
    [
        "The cohort held 500 participants and the coefficient was 0.42.\n",
        "Three sites contributed 120, 260, and 120 samples.\n",
        "The mean dosage was 1.00 across the cohort.\n",
    ],
)
def test_a_report_without_a_complete_accounting_is_silent(text: str) -> None:
    assert _report_accounting(text) is None


@pytest.mark.parametrize(
    "report_text",
    [_HARD_STATE_REPORT, _SILENT_REPORT],
)
def test_a_report_alone_never_resolves_the_representation(report_text: str) -> None:
    """Without a workflow the report cannot classify, however it reconciles."""

    applicability, operand = _fused_observation(report_text)
    assert applicability == "not_applicable"
    assert operand is None


def test_a_report_corroborating_a_quantized_workflow_resolves() -> None:
    assert _fused_observation(_HARD_STATE_REPORT, _QUANTIZED_WORKFLOW) == (
        "applicable",
        HARD_OPERAND,
    )


@pytest.mark.parametrize(
    ("workflow", "expected_operand"),
    [
        (_QUANTIZED_WORKFLOW, HARD_OPERAND),
        (_CONTINUOUS_WORKFLOW, EXPECTATION_OPERAND),
        (_CALIBRATION_WORKFLOW, CALIBRATION_OPERAND),
    ],
)
def test_a_silent_report_resolves_on_the_workflow_alone(
    workflow: str, expected_operand: str
) -> None:
    assert _fused_observation(_SILENT_REPORT, workflow) == ("applicable", expected_operand)


@pytest.mark.parametrize("workflow", [_CONTINUOUS_WORKFLOW, _CALIBRATION_WORKFLOW])
def test_a_report_contradicting_the_workflow_abstains(workflow: str) -> None:
    assert _fused_observation(_HARD_STATE_REPORT, workflow) == ("ambiguous", None)


def test_an_unsupported_workflow_is_not_reversed_by_a_reconciling_report() -> None:
    workflow = _posterior_workflow("dosage = expected.apply(lambda value: int(value))\n")
    assert _fused_observation(_HARD_STATE_REPORT, workflow) == ("unsupported", None)


def test_conflicting_workflow_fits_abstain_as_ambiguous() -> None:
    workflow = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "hard = expected.astype(int)\n"
        + "quantized_fit = sm.OLS(outcome, sm.add_constant(hard)).fit()\n"
        + "continuous_fit = sm.OLS(outcome, sm.add_constant(expected)).fit()\n"
        + "Path('results/report.md').write_text(\n"
        + "    f'{quantized_fit.params[1]} {continuous_fit.params[1]}'\n"
        + ")\n"
    )
    assert _fused_observation(_SILENT_REPORT, workflow) == ("ambiguous", None)


def test_a_workflow_with_no_resolvable_fit_is_not_applicable() -> None:
    assert _fused_observation(_SILENT_REPORT, "value = 1\n") == ("not_applicable", None)


def test_a_report_with_an_astronomically_large_integer_is_scanned_without_crashing() -> None:
    text = (
        "Copy state was 0 in 120 participants, 1 in 260, and 2 in 120 of the 500 genotyped "
        "participants; the mean dosage was 1.00. A run identifier of " + "9" * 400 + " was "
        "recorded.\n"
    )
    assert _report_accounting(text) == ((120, 260, 120), 500)


# ---------------------------------------------------------------------------
# v2.0.1: the nine wrong-answer families the second adversarial review
# demonstrated.
#
# Every case below is a workflow shape whose run-time behaviour differs from
# what v2.0.0 reported. None of them is executed here. ``_resolve`` parses the
# source and runs the static trace over the syntax tree, so shapes that need
# pandas, scikit-learn, or statsmodels at run time are still exact tests of
# the recognizer: the recognizer never imports them either. Only numpy is
# installed in this environment, and nothing here depends on that.


def _dataflow_context(
    sources: dict[str, str], *, unparsed: frozenset[str] = frozenset()
) -> FrozenInspectionContext:
    """A context holding one report and the given Python documents.

    A path listed in ``unparsed`` carries a parser result the resolver does
    not accept, which is how a document the parser skipped is modelled.
    """

    report = _SILENT_REPORT.encode("utf-8")
    surface_ref = RecordRef("publication_surface", "publication-surface:multi")
    artifact_ref = RecordRef("artifact", "artifact:multi-report")
    identity_ref = RecordRef("asset_identity", "asset-identity:multi-report")
    report_file_ref = RecordRef("file_record", "file:multi-report")
    report_parser_ref = RecordRef("parser_result", "parser-result:multi-report")
    snapshot_ref = RecordRef("repository_snapshot", "snapshot:multi")
    report_parser = canonical_json(
        {"parser_id": "parser:markdown-inventory", "parser_version": "0.2.0", "state": "parsed"}
    ).encode("utf-8")
    documents = [
        InspectionDocument(
            path="report.md",
            file_ref=report_file_ref,
            content=report,
            content_digest=sha256_digest(report),
            media_type="text/markdown",
            parser_result_ref=report_parser_ref,
            parser_result_payload=report_parser,
            parser_result_digest=sha256_digest(report_parser),
        )
    ]
    records: list[tuple[RecordRef, dict[str, object]]] = [
        (
            surface_ref,
            {
                "publication_surface_id": surface_ref.record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [artifact_ref.to_dict()]},
            },
        ),
        (
            artifact_ref,
            {
                "artifact_id": artifact_ref.record_id,
                "kind": "report",
                "path": "report.md",
                "asset_identity_ref": identity_ref.to_dict(),
            },
        ),
        (
            identity_ref,
            {
                "asset_identity_id": identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": artifact_ref.to_dict(),
                "identity_evidence": {"kind": "full_digest", "digest": sha256_digest(report)},
            },
        ),
        (snapshot_ref, {"snapshot_id": snapshot_ref.record_id}),
        (report_file_ref, {"file_record_id": report_file_ref.record_id}),
        (report_parser_ref, {"parser_result_id": report_parser_ref.record_id}),
    ]
    for index, (path, text) in enumerate(sources.items()):
        file_ref = RecordRef("file_record", f"file:multi-{index}")
        parser_ref = RecordRef("parser_result", f"parser-result:multi-{index}")
        payload = canonical_json(
            {
                "parser_id": PYTHON_PARSER_ID,
                "parser_version": PYTHON_PARSER_VERSION,
                "state": "unsupported" if path in unparsed else "parsed",
            }
        ).encode("utf-8")
        blob = text.encode("utf-8")
        documents.append(
            InspectionDocument(
                path=path,
                file_ref=file_ref,
                content=blob,
                content_digest=sha256_digest(blob),
                media_type="text/x-python",
                parser_result_ref=parser_ref,
                parser_result_payload=payload,
                parser_result_digest=sha256_digest(payload),
            )
        )
        records.append((file_ref, {"file_record_id": file_ref.record_id}))
        records.append((parser_ref, {"parser_result_id": parser_ref.record_id}))
    context = FrozenInspectionContext(
        snapshot_digest=sha256_digest("snapshot"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=tuple(documents),
        base_records=tuple(FrozenBaseRecord.from_record(ref, value) for ref, value in records),
    )
    return replace(
        context,
        scope_join_graph=build_static_scope_join_graph(
            snapshot_digest=context.snapshot_digest,
            snapshot_ref=snapshot_ref,
            selected_surface_ref=surface_ref,
            selected_artifact_ref=artifact_ref,
            documents=context.documents,
            base_records=context.base_records,
        ),
    )


def _dataflow_state(sources: dict[str, str], *, unparsed: frozenset[str] = frozenset()) -> str:
    resolution = resolve_copy_dosage_dataflow(
        _dataflow_context(sources, unparsed=unparsed),
        hard_operand=HARD_OPERAND,
        expectation_operand=EXPECTATION_OPERAND,
        calibration_operand=CALIBRATION_OPERAND,
        parser_id=PYTHON_PARSER_ID,
        parser_version=PYTHON_PARSER_VERSION,
    )
    return resolution.state


_CALIBRATION_SOURCE = _calibration_workflow("dosage = calibrator.predict(features)\n")


# ---------------------------------------------------------------------------
# Family 1: arithmetic that cancels its own quantizer.


@pytest.mark.parametrize(
    "expression",
    [
        "expected - expected % 1",
        "expected - np.mod(expected, 1)",
        "expected + (expected.round() - expected)",
        "expected - (expected - expected.astype(int))",
        "expected.round() + (expected - expected)",
        "expected * (expected.round() / expected)",
    ],
)
def test_arithmetic_against_a_value_of_the_same_provenance_abstains(expression: str) -> None:
    """``x - x % 1`` is ``floor(x)``, and reading it by tag alone says continuous.

    Each of these evaluates, at run time, to the rounded or truncated value,
    yet each pairs a quantized operand with a continuous one. Restoration is
    admitted only against an operand descended from a different source.
    """

    _assert_abstains(_posterior_workflow(f"dosage = {expression}\n"))


@pytest.mark.parametrize(
    "expression",
    ["raw + (raw.round() - raw)", "raw - raw % 1"],
)
def test_the_same_cancellation_on_the_calibration_origin_abstains(expression: str) -> None:
    source = _calibration_workflow(f"raw = calibrator.predict(features)\ndosage = {expression}\n")
    _assert_abstains(source)


def test_an_independently_traced_continuous_addend_still_restores_the_scale() -> None:
    """The rule narrows re-expansion; it does not remove it.

    The addend descends from a second calibration, not from the rounded
    value, so nothing about it can cancel the fraction the rounding removed.
    """

    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + _EXPECTED
        + "residual_model = RidgeCV().fit(features, frame['residual'])\n"
        + "residual = residual_model.predict(features)\n"
        + "dosage = expected.round() + residual\n"
        + _fit()
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {EXPECTATION}


def test_a_quantized_value_scaled_by_a_literal_is_still_read_as_quantized() -> None:
    """A literal operand carries no provenance, so it never triggers the rule."""

    unsupported, states = _resolve(_posterior_workflow("dosage = np.floor(expected) + 0.0\n"))
    assert not unsupported
    assert states == {QUANTIZED}


# ---------------------------------------------------------------------------
# Family 2: in-place mutation through calls the vocabulary never listed.


@pytest.mark.parametrize(
    "body",
    [
        "dosage = expected * 1.0\nnp.copyto(dosage, np.round(dosage))\n",
        "dosage = expected * 1.0\nnp.round(expected, out=dosage)\n",
        "dosage = expected * 1.0\nnp.rint(expected, dosage)\n",
        "dosage = expected * 1.0\nnp.put(dosage, [0, 1], np.round(expected))\n",
        "dosage = expected * 1.0\ndosage.fill(1)\n",
        "dosage = expected * 1.0\ndosage.itemset(0, 1)\n",
        "dosage = expected * 1.0\ndosage.partition(1)\n",
        "dosage = expected * 1.0\ndosage.resize(4)\n",
        "dosage = expected * 1.0\ndosage.sort()\n",
    ],
)
def test_an_in_place_write_to_the_exposure_array_abstains(body: str) -> None:
    """Mutation is default-deny; no list of in-place APIs is being maintained.

    Each of these rewrites ``dosage`` after it was tagged, and v2.0.0 went on
    reporting the value the array used to hold.
    """

    _assert_abstains(_posterior_workflow(body))


def test_an_out_target_inside_a_helper_reaches_the_callers_array() -> None:
    source = _posterior_workflow(
        "def harmonise(target, source):\n    return np.floor(source, out=target)\n\n"
        "dosage = expected * 1.0\nspare = harmonise(dosage, expected)\n"
    )
    _assert_abstains(source)


# ---------------------------------------------------------------------------
# Family 3: one runtime object reached through a second name.


def test_a_bare_helper_call_that_rounds_a_column_reaches_the_callers_frame() -> None:
    """``harmonise(frame)`` mutates the caller's own table, not a copy."""

    source = (
        _HEAD
        + _CALIBRATOR
        + "frame['dose'] = calibrator.predict(features)\n"
        + "def harmonise(table):\n    table['dose'] = table['dose'].round()\n\n"
        + "harmonise(frame)\n"
        + _fit("frame[['dose']]")
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


def test_a_returning_helper_also_mutates_the_argument_it_was_given() -> None:
    """The fit reads the original name, which is the object the helper changed."""

    source = (
        _HEAD
        + _CALIBRATOR
        + "frame['dose'] = calibrator.predict(features)\n"
        + "def harmonise(table):\n"
        + "    table['dose'] = table['dose'].round()\n"
        + "    return table\n\n"
        + "staged = harmonise(frame)\n"
        + _fit("frame[['dose']]")
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


def test_the_returned_handle_of_a_mutating_helper_still_reads_correctly() -> None:
    """The control for the two above: reading the return value agrees with them."""

    source = (
        _HEAD
        + _CALIBRATOR
        + "frame['dose'] = calibrator.predict(features)\n"
        + "def harmonise(table):\n"
        + "    table['dose'] = table['dose'].round()\n"
        + "    return table\n\n"
        + "staged = harmonise(frame)\n"
        + _fit("staged[['dose']]")
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


def test_a_helper_whose_body_cannot_be_completed_invalidates_its_argument() -> None:
    source = (
        _HEAD
        + _CALIBRATOR
        + "frame['dose'] = calibrator.predict(features)\n"
        + "def harmonise(table):\n    return custom_transform(table)\n\n"
        + "harmonise(frame)\n"
        + _fit("frame[['dose']]")
        + _TAIL
    )
    _assert_abstains(source)


@pytest.mark.parametrize(
    "container",
    [
        "tables = [frame]\ntables[0]['dose'] = tables[0]['dose'].round()\n",
        "holder = {'t': frame}\nholder['t']['dose'] = holder['t']['dose'].round()\n",
        "pair = (frame, frame)\npair[1]['dose'] = pair[1]['dose'].round()\n",
    ],
)
def test_a_frame_mutated_through_a_container_reference_abstains(container: str) -> None:
    """A container literal holding the table is a second name for the table."""

    source = (
        _HEAD
        + _CALIBRATOR
        + "frame['dose'] = calibrator.predict(features)\n"
        + container
        + _fit("frame[['dose']]")
        + _TAIL
    )
    _assert_abstains(source)


# ---------------------------------------------------------------------------
# Family 4: an integer dtype spelled as a keyword.


@pytest.mark.parametrize(
    "expression",
    [
        "np.array(expected, dtype=int)",
        "np.array(expected, dtype='int64')",
        "np.array(expected, int)",
        "np.asarray(expected, dtype=np.int32)",
        "expected.to_numpy(dtype=int)",
        "expected.to_numpy('int64')",
    ],
)
def test_an_integer_dtype_argument_quantizes_exactly_as_a_cast_does(expression: str) -> None:
    """``np.array(x, dtype=int)`` truncates; only its spelling differs from astype."""

    unsupported, states = _resolve(_posterior_workflow(f"dosage = {expression}\n"))
    assert not unsupported
    assert states == {QUANTIZED}


def test_an_integer_dtype_argument_on_the_calibration_origin_quantizes() -> None:
    source = _calibration_workflow("dosage = np.array(calibrator.predict(features), dtype=int)\n")
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


@pytest.mark.parametrize(
    "expression",
    ["np.array(expected, dtype=chosen_dtype)", "expected.to_numpy(dtype=chosen_dtype)"],
)
def test_a_dtype_this_trace_cannot_read_abstains(expression: str) -> None:
    """An unread dtype may be an integer dtype, and an integer dtype truncates."""

    _assert_abstains(_posterior_workflow(f"dosage = {expression}\n"))


def test_a_float_dtype_argument_leaves_the_continuous_reading_alone() -> None:
    unsupported, states = _resolve(
        _posterior_workflow("dosage = np.array(expected, dtype=float)\n")
    )
    assert not unsupported
    assert states == {EXPECTATION}


# ---------------------------------------------------------------------------
# Family 5: the decimal count of a rounding call.


@pytest.mark.parametrize(
    "expression",
    [
        "expected.round(-1)",
        "np.round(expected, -1)",
        "np.around(expected, decimals=-2)",
        "round(expected, -1)",
        "expected.round(0)",
    ],
)
def test_rounding_to_zero_or_fewer_decimals_lands_on_levels(expression: str) -> None:
    """Rounding to tens bins as surely as rounding to units."""

    unsupported, states = _resolve(_posterior_workflow(f"dosage = {expression}\n"))
    assert not unsupported
    assert states == {QUANTIZED}


@pytest.mark.parametrize(
    "expression",
    [
        "expected.round(precision)",
        "np.round(expected, precision)",
        "np.around(expected, decimals=precision)",
        "round(expected, precision)",
    ],
)
def test_a_decimal_count_this_trace_cannot_read_abstains(expression: str) -> None:
    """A count that is not written as a literal may be zero."""

    _assert_abstains(_posterior_workflow(f"precision = 2\ndosage = {expression}\n"))


# ---------------------------------------------------------------------------
# Family 6: a literal table is a binning, whatever its values are.


@pytest.mark.parametrize(
    "body",
    [
        "centers = np.array([0.12, 0.98, 1.93])\ndosage = centers[expected.round().astype(int)]\n",
        "dosage = expected.round().map({0: 0.12, 1: 0.98, 2: 1.93})\n",
        "dosage = np.where(expected > 1.0, 1.93, 0.12)\n",
        "dosage = pd.cut(expected, [-1, 0.5, 1.5, 3], labels=[0.12, 0.98, 1.93])\n",
        "dosage = pd.qcut(expected, 3, labels=[0.12, 0.98, 1.93])\n",
    ],
)
def test_a_literal_table_of_non_integral_levels_is_still_a_binning(body: str) -> None:
    """Three bin centres are three levels; the model sees three distinct values.

    Under the ruling on finding 6, the v2.0.0 carve-out that read a table of
    non-integral values as a re-expansion is gone. The claim this check
    implements covers hard *or binned* dosage used for a continuous target.
    """

    unsupported, states = _resolve(_posterior_workflow(body))
    assert not unsupported
    assert states == {QUANTIZED}


def test_a_literal_centre_table_on_the_calibration_origin_is_a_binning() -> None:
    source = _calibration_workflow(
        "raw = calibrator.predict(features)\n"
        "centers = np.array([0.12, 0.98, 1.93])\n"
        "dosage = centers[raw.round().astype(int)]\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


# ---------------------------------------------------------------------------
# Family 7: constants that are not written as constants.


@pytest.mark.parametrize(
    "expression",
    [
        "np.where(expected > 1.0, 3 / 2, 2)",
        "np.where(expected > 1.0, int(1.5), 3)",
        "np.where(expected > 1.0, 1 + 1, 3)",
    ],
)
def test_a_branch_value_that_is_not_a_literal_abstains(expression: str) -> None:
    """No arithmetic is folded and no call is evaluated to reach a level value."""

    _assert_abstains(_posterior_workflow(f"dosage = {expression}\n"))


@pytest.mark.parametrize(
    "expression",
    ["np.where(expected > 1.0, 1.5, 2)", "np.where(expected > 1.0, 1, 3)"],
)
def test_literal_branch_values_read_as_a_two_level_table(expression: str) -> None:
    unsupported, states = _resolve(_posterior_workflow(f"dosage = {expression}\n"))
    assert not unsupported
    assert states == {QUANTIZED}


def test_a_state_vector_assembled_by_arithmetic_is_not_the_ordered_vector() -> None:
    """``[0, 1, 1 + 1]`` is not read as ``[0, 1, 2]``; the trace folds nothing."""

    source = (
        _HEAD
        + _CLASSIFIER
        + _PROBABILITIES
        + "dosage = probabilities @ np.array([0, 1, 1 + 1])\n"
        + _fit()
        + _TAIL
    )
    _assert_abstains(source)


# ---------------------------------------------------------------------------
# Family 8: imports the trace cannot see through.


def test_a_python_document_the_parser_skipped_leaves_the_case_unsupported() -> None:
    """An unread document can hold the estimator, the rounding, or a shadow.

    A shadowing ``sklearn/linear_model.py`` whose parser result the resolver
    does not accept was reported as a clean continuous calibration in v2.0.0,
    because the document was silently skipped instead of abstaining.
    """

    shadow = "import numpy as np\n\n\nclass RidgeCV:\n    def predict(self, X):\n        return X\n"
    assert (
        _dataflow_state(
            {"analysis.py": _CALIBRATION_SOURCE, "helpers.py": shadow},
            unparsed=frozenset({"helpers.py"}),
        )
        == "unsupported"
    )


def test_a_case_document_shadowing_an_imported_module_leaves_the_case_unsupported() -> None:
    """``sklearn/linear_model.py`` in the case is what ``import sklearn`` resolves to."""

    shadow = "def RidgeCV():\n    return None\n"
    assert (
        _dataflow_state({"analysis.py": _CALIBRATION_SOURCE, "sklearn/linear_model.py": shadow})
        == "unsupported"
    )


def test_a_bare_case_directory_named_for_a_module_leaves_the_case_unsupported() -> None:
    """A directory alone is a namespace package, so it shadows too."""

    assert (
        _dataflow_state({"analysis.py": _CALIBRATION_SOURCE, "numpy/notes.py": "value = 1\n"})
        == "unsupported"
    )


def test_an_unshadowed_multi_document_case_still_resolves() -> None:
    """The control: an ordinary second document changes nothing."""

    assert (
        _dataflow_state({"analysis.py": _CALIBRATION_SOURCE, "figures.py": "value = 1\n"})
        == "unique"
    )


@pytest.mark.parametrize(
    "statement",
    [
        "import joblib\n",
        "import os\n",
        "from . import helpers\n",
        "from .helpers import recode\n",
        "from numpy import *\n",
        "import matplotlib.pyplot as plt\n",
    ],
)
def test_an_import_outside_the_modelled_stack_leaves_the_document_unsupported(
    statement: str,
) -> None:
    """Importing a module executes it, and an unmodelled module is unread."""

    _assert_abstains(statement + _CALIBRATION_SOURCE)


@pytest.mark.parametrize(
    "statement",
    [
        "import scipy.stats\n",
        "from scipy import stats\n",
        "import statistics\n",
        "from decimal import Decimal\n",
        "import io\n",
    ],
)
def test_an_import_inside_the_modelled_stack_still_resolves(statement: str) -> None:
    unsupported, states = _resolve(statement + _CALIBRATION_SOURCE)
    assert not unsupported
    assert states == {CALIBRATION}


# ---------------------------------------------------------------------------
# Family 9: sources that used to raise instead of abstaining.


@pytest.mark.parametrize(
    "body",
    [
        "threshold = " + "9" * 400 + "\ndosage = expected\n",
        "table = np.array([0, 1, " + "9" * 400 + "])\ndosage = expected\n",
        "mask = 0x" + "f" * 400 + "\ndosage = expected\n",
    ],
)
def test_an_astronomically_large_literal_is_discarded_rather_than_converted(body: str) -> None:
    """``float()`` of a wide enough integer raises; the trace never calls it."""

    unsupported, states = _resolve(_posterior_workflow(body))
    assert not unsupported
    assert states == {EXPECTATION}


def test_a_source_too_deep_for_the_parser_abstains_in_the_resolvers_own_terms() -> None:
    """A valid but deeply nested source exhausts the stack inside ``ast`` itself."""

    deep = "x = " + "-" * 5000 + "1\n"
    assert _dataflow_state({"analysis.py": _CALIBRATION_SOURCE, "deep.py": deep}) == "unsupported"


def test_the_adapter_abstains_rather_than_raising_on_an_oversized_literal() -> None:
    """The abstention is this adapter's own, not the registry's generic guard."""

    workflow = "run_identifier = " + "9" * 400 + "\n"
    assert _fused_observation(_SILENT_REPORT, workflow) == ("not_applicable", None)


def test_the_adapter_abstains_rather_than_raising_on_a_source_too_deep_to_parse() -> None:
    workflow = "x = " + "-" * 5000 + "1\n"
    assert _fused_observation(_SILENT_REPORT, workflow) == ("unsupported", None)


# ---------------------------------------------------------------------------
# v2.0.2: the six wrong-answer families a third adversarial review
# demonstrated, and the four latent gaps it named.
#
# Every case below runs at run time to something other than what v2.0.1
# reported. As above, none of them is executed here: ``_resolve`` parses the
# source and runs the static trace over the syntax tree.


_LEVEL_TABLE_WHERE = "np.where(expected > 1.5, 2, np.where(expected > 0.5, 1, 0))"


# ---------------------------------------------------------------------------
# Family 10: a keyword this trace cannot name.


@pytest.mark.parametrize(
    "body",
    [
        "dosage = np.array(expected, **{'dtype': int})\n",
        "dosage = np.asarray(expected, **{'dtype': 'int64'})\n",
        "dosage = expected.astype(**{'dtype': int})\n",
        "dosage = expected.to_numpy(**{'dtype': int})\n",
        "dosage = pd.cut(expected, [-1, 0.5, 1.5, 3], **{'labels': [0, 1, 2]})\n",
        "dosage = harmonise(**{'value': expected})\n",
    ],
)
def test_a_dict_unpacked_keyword_leaves_the_operation_unread(body: str) -> None:
    """``f(x, **options)`` states no keyword names, so it states no operation.

    v2.0.1 read every keyword by scanning ``node.keywords`` for a name, and a
    ``**`` unpacking has no name to find. ``np.array(expected, **{'dtype':
    int})`` truncates to the integers and was reported as the continuous
    posterior expectation.
    """

    source = _posterior_workflow(
        "def harmonise(value):\n    return value.round()\n\n" + body,
    )
    _assert_abstains(source)


def test_a_dict_unpacked_destination_reaches_the_exposure_array() -> None:
    """``np.round(expected, 0, **{'out': dosage})`` rewrites ``dosage``."""

    source = _posterior_workflow(
        "dosage = expected * 1.0\nnp.round(expected, 0, **{'out': dosage})\n"
    )
    _assert_abstains(source)


def test_a_dict_unpacked_decimal_count_abstains_instead_of_finding() -> None:
    """The false-finding direction of the same gap.

    ``expected.round(**{'decimals': 2})`` preserves the continuous scale, and
    v2.0.1 found no decimal count, read the call as a bare ``round()``, and
    reported a hard-state exposure for a workflow that never quantized.
    """

    _assert_abstains(_posterior_workflow("dosage = expected.round(**{'decimals': 2})\n"))


def test_a_dict_unpacked_keyword_invalidates_what_the_call_names() -> None:
    """An unnameable keyword is a destination this trace cannot rule out."""

    source = _posterior_workflow(
        "dosage = expected * 1.0\nnp.copyto(**{'dst': dosage, 'src': np.round(dosage)})\n"
    )
    _assert_abstains(source)


# ---------------------------------------------------------------------------
# Family 11: positional destinations.


@pytest.mark.parametrize(
    "call",
    [
        "expected.round(0, dosage)",
        "expected.clip(0, 2, dosage)",
        "probabilities.argmax(1, dosage)",
        "expected.astype(int, dosage)",
        "np.round(expected, 0, dosage)",
        "np.dot(probabilities, np.array([0, 1, 2]), dosage)",
        "np.mean(expected, 0, float, dosage)",
        "np.argmax(probabilities, 1, dosage)",
    ],
)
def test_a_positional_destination_rewrites_the_exposure_array(call: str) -> None:
    """A recognized call's destination rides past the arguments it reads.

    v2.0.1 knew this for ``numpy``'s rounding and scale-preserving ufuncs and
    for nothing else, so ``expected.round(0, dosage)`` filled ``dosage`` with
    the rounded value while the trace went on reporting the continuous one.
    Every recognized call and method now states the positional arity it
    reads, and anything past that arity is a write.
    """

    _assert_abstains(_posterior_workflow(f"dosage = expected * 1.0\n{call}\n"))


def test_an_in_place_keyword_rewrites_the_exposure_array() -> None:
    """``copy=False`` turns a call that returns a new array into a write."""

    _assert_abstains(
        _posterior_workflow("dosage = expected * 1.0\nnp.nan_to_num(dosage, copy=False)\n")
    )


def test_every_recognized_call_and_method_states_a_read_only_arity() -> None:
    """The closure is the table's completeness, not the table's contents.

    A vocabulary entry whose destination position was never stated reads as a
    write, so this invariant is what keeps a future addition from silently
    inheriting the permissive default.
    """

    assert _RECOGNIZED_CALL_PATHS == frozenset(_CALL_READ_ONLY_ARITY)
    assert _RECOGNIZED_METHODS == frozenset(_METHOD_READ_ONLY_ARITY)


# ---------------------------------------------------------------------------
# Family 12: a view is a second handle on one array.


@pytest.mark.parametrize(
    "view",
    [
        "view = dosage.ravel()",
        "view = dosage.reshape(-1, 1)",
        "view = dosage.T",
        "view = dosage.values",
        "view = np.ravel(dosage)",
        "view = dosage[0:4]",
    ],
)
def test_a_view_shares_the_invalidation_group_of_the_array_it_views(view: str) -> None:
    """Aliasing follows provenance, not assignment syntax.

    v2.0.1 joined alias groups only for ``alias = name`` and for container
    literals, so every numpy view was a second handle the model never joined:
    the write through ``view`` rewrote ``dosage`` while the trace reported the
    value ``dosage`` used to hold.
    """

    source = _posterior_workflow(
        f"dosage = expected * 1.0\n{view}\nnp.copyto(view, np.round(view))\n"
    )
    _assert_abstains(source)


def test_a_copy_does_not_join_the_group_of_what_it_copied() -> None:
    """The control: over-linking is cheap, but a copy is a different object."""

    source = _posterior_workflow(
        "dosage = expected * 1.0\nspare = dosage.copy()\nnp.copyto(spare, np.round(spare))\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {EXPECTATION}


def test_a_copy_still_carries_the_provenance_of_the_value_it_copied() -> None:
    """A copy is a different object and the same numbers.

    Two copies of one array differ by exactly zero, so admitting their
    difference as an independent continuous addend would re-open the
    cancellation family. Handles say a copy is its own object; provenance ids
    say it descends from what it copied, and the arithmetic rule reads the
    ids.
    """

    source = _posterior_workflow(
        "first = expected.copy()\n"
        "second = expected.copy()\n"
        "dosage = expected.round() + (first - second)\n"
    )
    _assert_abstains(source)


# ---------------------------------------------------------------------------
# Family 13: one estimator evaluation is one value.


def test_repeated_identical_predictions_cancel_instead_of_restoring() -> None:
    """Three deterministic re-predictions supply a drift that is exactly zero.

    v2.0.1 minted a fresh provenance id per prediction call site, so
    ``one - two`` over two identical predictions read as an independently
    traced continuous addend and restored the scale of a rounded exposure that
    run time leaves rounded.
    """

    source = _calibration_workflow(
        "raw = calibrator.predict(features)\n"
        "replicate_one = calibrator.predict(features)\n"
        "replicate_two = calibrator.predict(features)\n"
        "batch_drift = replicate_one - replicate_two\n"
        "dosage = raw.round() + batch_drift\n"
    )
    _assert_abstains(source)


def test_a_second_identically_fitted_estimator_shares_the_first_ones_identity() -> None:
    """v2.0.3 expectation change: identity is what an estimator is, not where.

    Under v2.0.2 this read as the direct calibration, because a second
    ``RidgeCV()`` minted provenance of its own and the difference of the two
    predictions then read as an independent continuous addend. Two estimators
    of the same class fitted on the same values are one value written twice,
    and for a deterministic estimator that difference is identically zero, so
    the reading was wrong. Estimator ids are now keyed on the constructor path
    and the fit-call argument signature, which makes the two predictions
    intersect and the subtraction unreadable.

    Fresh ids are minted only when the constructor path or the fit signature
    differs; the two tests below are the controls for each half of that key.
    """

    source = _calibration_workflow(
        "raw = calibrator.predict(features)\n"
        "second_model = RidgeCV().fit(features, frame['copy_index'])\n"
        "dosage = raw - second_model.predict(features)\n"
    )
    _assert_abstains(source)


def test_a_second_estimator_of_a_different_class_still_mints_fresh_provenance() -> None:
    """Half one of the identity key: a different constructor path."""

    source = _calibration_workflow(
        "raw = calibrator.predict(features)\n"
        "second_model = LinearRegression().fit(features, frame['copy_index'])\n"
        "dosage = raw - second_model.predict(features)\n"
    ).replace(
        "from sklearn.linear_model import LogisticRegression, RidgeCV",
        "from sklearn.linear_model import LinearRegression, LogisticRegression, RidgeCV",
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {CALIBRATION}


def test_a_second_estimator_fitted_on_other_values_still_mints_fresh_provenance() -> None:
    """Half two of the identity key: the same class, a different fit."""

    source = _calibration_workflow(
        "replicate = pd.read_csv(Path('inputs/replicate.csv'))\n"
        "raw = calibrator.predict(features)\n"
        "second_model = RidgeCV().fit(\n"
        "    replicate[['marker_a', 'marker_b']], replicate['copy_index']\n"
        ")\n"
        "dosage = raw - second_model.predict(features)\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {CALIBRATION}


def test_a_prediction_on_a_different_argument_still_mints_fresh_provenance() -> None:
    """The identity is keyed on the arguments too, not on the estimator alone."""

    source = _calibration_workflow(
        "replicate = pd.read_csv(Path('inputs/replicate.csv'))\n"
        "raw = calibrator.predict(features)\n"
        "other = calibrator.predict(replicate[['marker_a', 'marker_b']])\n"
        "dosage = raw - other\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {CALIBRATION}


# ---------------------------------------------------------------------------
# Family 14: selection is not arithmetic.


@pytest.mark.parametrize(
    "expression",
    [
        "np.where(mask, np.round(expected), expected)",
        "np.where(mask, expected, np.round(expected))",
        "np.where(mask, expected, expected)",
        "np.where(mask, 0, expected)",
        "np.where(mask, expected, 2.0)",
    ],
)
def test_a_where_whose_branches_are_not_all_levels_abstains(expression: str) -> None:
    """A guard is a run-time value, so the branch each element takes is unread.

    v2.0.1 read a mixed branch pair by the more permissive of the two tags and
    reported the continuous branch, while run time delivers the rounded branch
    wherever the guard held.
    """

    source = _posterior_workflow(f"mask = frame['qc_pass'] == 1\ndosage = {expression}\n")
    _assert_abstains(source)


@pytest.mark.parametrize(
    "expression",
    [
        "np.where(mask, expected.round(), 0)",
        "np.where(mask, expected.astype(int), expected.round())",
        _LEVEL_TABLE_WHERE,
    ],
)
def test_a_where_between_level_branches_still_bins(expression: str) -> None:
    """The one case where the unread guard does not matter.

    Both branches are confined to levels, so every element of the result comes
    from one finite level set or the other whatever the guard decides. This is
    narrower than the ruling on finding 5, which would have abstained here
    too: a nested ``where`` is the ordinary spelling of a three-level hard
    call, and abstaining on it would drop a true reading for no soundness
    gain.
    """

    source = _posterior_workflow(f"mask = frame['qc_pass'] == 1\ndosage = {expression}\n")
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


# ---------------------------------------------------------------------------
# Family 15: a subscript indexed by a traced value gathers.


@pytest.mark.parametrize(
    "body",
    [
        "raw = calibrator.predict(features)\n"
        "centres = raw[0:3]\n"
        "dosage = centres[raw.round().astype(int)]\n",
        "raw = calibrator.predict(features)\ndosage = raw[raw.round().astype(int)]\n",
        "raw = calibrator.predict(features)\norder = raw.argsort()\ndosage = raw[order]\n",
    ],
)
def test_a_gather_from_a_traced_table_abstains(body: str) -> None:
    """Three values read out of a three-entry table are three levels.

    v2.0.1 read every subscript of a traced value as a row selection, which
    preserves the scale. A table built at run time is not a literal table, so
    the level rule never fired either, and the gather was reported as the
    continuous calibration it was built from.
    """

    _assert_abstains(_calibration_workflow(body))


@pytest.mark.parametrize(
    "expression",
    ["expected[0:3]", "expected[2]", "expected[:]", "expected[0:2, 1]", "expected[mask]"],
)
def test_a_literal_index_or_a_comparison_mask_still_selects_rows(expression: str) -> None:
    """The control: row selection preserves the scale, and still reads.

    v2.0.3 expectation change: the mask here is now built from ``expected``,
    which this trace watched a comparison produce. Under v2.0.2 the case was
    written ``mask = frame['qc_pass'] == 1``, whose operands are opaque staged
    columns, so the comparison produced no mask at all and the subscript read
    as a row selection only because the index had lost its provenance. That is
    the permissive branch ruling 6 withdrew; the case it stood for is now
    ``test_an_unproven_mask_index_abstains``.
    """

    source = _posterior_workflow(f"mask = expected > 0.5\ndosage = {expression}\n")
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {EXPECTATION}


# ---------------------------------------------------------------------------
# The four latent gaps the same review named.


def test_a_staged_parse_carries_the_staged_values_provenance() -> None:
    """Latent: both staged-parse branches dropped their input's provenance.

    A value parsed out of staged text descends from that text. Minting it
    without ids made every value parsed from one staged read read as
    independent of every other, which is the shape the cancellation rule
    exists to catch.
    """

    node = ast.parse("value").body[0]
    staged = _Col(_TEXT, staged=True, unchanged=True, ids=frozenset({-1}))
    for dtype in ("int", "float"):
        parsed = _cast(staged, dtype, node)
        assert isinstance(parsed, _Col)
        assert parsed.ids == staged.ids


def test_a_document_named_for_the_module_it_imports_leaves_the_case_unsupported() -> None:
    """Latent: the shadowing scan exempted the scanning document's own stem.

    A workflow stored as ``numpy.py`` is what its own ``import numpy``
    resolves to, so the exemption cleared exactly the document that shadows
    the module it reads.
    """

    assert _dataflow_state({"numpy.py": _CALIBRATION_SOURCE}) == "unsupported"


def test_a_document_named_for_no_imported_module_still_resolves() -> None:
    """The control for the exemption's removal."""

    assert _dataflow_state({"analysis.py": _CALIBRATION_SOURCE}) == "unique"


def test_a_helper_effect_on_an_unnameable_argument_invalidates_it() -> None:
    """Latent: a recorded mutation was dropped when its argument was not a name.

    The trace watched the helper mutate the object it was handed. There is no
    caller binding to write the new value back to, so the values the argument
    expression names lose their provenance instead of keeping the value the
    object used to hold.
    """

    source = (
        _HEAD
        + _CALIBRATOR
        + "frame['dose'] = calibrator.predict(features)\n"
        + "def harmonise(values):\n    del values[0]\n\n"
        + "harmonise(frame['dose'])\n"
        + _fit("frame[['dose']]")
        + _TAIL
    )
    _assert_abstains(source)


def test_a_contract_whose_operand_values_are_not_distinct_is_unsupported() -> None:
    """Latent: the operand lookup collapsed when two contract operands matched.

    The three operand strings are how a resolved reading is reported. A
    contract that spells two of them the same way cannot say which
    representation a resolved reading names, so the adapter abstains rather
    than reporting whichever key the mapping kept.
    """

    module = next(
        item
        for item in default_scientific_check_registry().modules
        if item.manifest.check_id == COPY_CHECK
    )
    adapter = replace(module.adapters[0], calibration_operand=module.adapters[0].hard_operand)
    observation = adapter.inspect(_dataflow_context({"analysis.py": _QUANTIZED_WORKFLOW}))
    assert observation.applicability == "unsupported"
    assert observation.observed_operand is None


# ---------------------------------------------------------------------------
# v2.0.3: the six wrong-answer families a fourth adversarial review
# demonstrated.
#
# Every case below runs at run time to something other than what v2.0.2
# reported. None of them is executed here: ``_resolve`` parses the source and
# runs the static trace over the syntax tree.


# ---------------------------------------------------------------------------
# Family 16: a conversion is a view unless it always writes its own buffer.


_ASARRAY_DTYPE_REPRODUCTION = _posterior_workflow(
    "values = np.asarray(expected, dtype=float)\n"
    "np.round(values, 0, out=values)\n"
    "dosage = expected\n"
)
_CHKFINITE_REPRODUCTION = _posterior_workflow(
    "values = np.asarray_chkfinite(expected)\nnp.round(values, 0, out=values)\ndosage = expected\n"
)


@pytest.mark.parametrize(
    "conversion",
    [
        "np.asarray(expected, dtype=float)",
        "np.asarray(expected, dtype='float64')",
        "np.asarray(expected, np.float64)",
        "np.asfarray(expected)",
        "np.asfarray(expected, dtype=float)",
        "np.asarray_chkfinite(expected)",
    ],
)
def test_a_conversion_that_can_return_its_input_keeps_its_handle(conversion: str) -> None:
    """``numpy.asarray`` is the identity whenever the dtype already matches.

    v2.0.2 minted a fresh handle for every ``asarray`` carrying a dtype,
    because it routed the dtype through the same cast path ``numpy.array``
    uses. ``numpy.array`` copies; ``numpy.asarray`` does not. The second name
    is a second handle on one buffer, so the ``out=`` write through it lands
    in the exposure array, and the workflow was reported as the continuous
    posterior expectation while run time rounds it.

    ``numpy.asarray_chkfinite`` reads its input for non-finite entries and
    then returns ``numpy.asarray`` of it, so it is the same identity.
    """

    source = _posterior_workflow(
        f"values = {conversion}\nnp.round(values, 0, out=values)\ndosage = expected\n"
    )
    _assert_abstains(source)


@pytest.mark.parametrize(
    "conversion",
    [
        "np.array(expected, dtype=float)",
        "np.array(expected)",
        "np.copy(expected)",
        "expected.copy()",
        "expected.flatten()",
    ],
)
def test_a_conversion_that_always_writes_its_own_buffer_still_mints(conversion: str) -> None:
    """The boundary: only a call that always copies breaks the handle.

    ``numpy.array`` copies unless told not to, ``numpy.copy`` is a copy by
    name, and ``ndarray.copy``/``ndarray.flatten`` are copies by definition.
    A write through the new name therefore does not reach the exposure array.
    """

    source = _posterior_workflow(
        f"values = {conversion}\nnp.round(values, 0, out=values)\ndosage = expected\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {EXPECTATION}


@pytest.mark.parametrize(
    ("conversion", "state"),
    [
        ("np.asarray(expected, dtype=int)", QUANTIZED),
        ("np.asarray(expected, dtype='int64')", QUANTIZED),
        ("np.asfarray(expected, dtype=int)", QUANTIZED),
        ("np.array(expected, dtype=int)", QUANTIZED),
        ("np.asarray_chkfinite(expected)", EXPECTATION),
        ("np.asarray(expected)", EXPECTATION),
    ],
)
def test_the_dtype_reading_of_a_conversion_is_unchanged(conversion: str, state: str) -> None:
    """Only the handle moved. An integer dtype still truncates, view or not."""

    unsupported, states = _resolve(_posterior_workflow(f"dosage = {conversion}\n"))
    assert not unsupported
    assert states == {state}


# ---------------------------------------------------------------------------
# Family 17: a ``*`` unpacking states no argument positions.


_STARRED_DESTINATION_REPRODUCTION = _posterior_workflow(
    "spec = (expected, 0, expected)\nnp.round(*spec)\ndosage = expected\n"
)


@pytest.mark.parametrize(
    "body",
    [
        # Call form: the unpacked sequence supplies the ``out`` destination.
        "spec = (expected, 0, expected)\nnp.round(*spec)\ndosage = expected\n",
        # Method form: the same, written through the receiver.
        "spec = (0, expected)\ndosage = expected * 1.0\ndosage.round(*spec)\n",
        # The unpacked sequence may equally supply the decimal count that bins.
        "spec = [expected]\ndosage = np.round(*spec)\n",
        # Or the dtype that truncates.
        "spec = (expected, int)\ndosage = np.asarray(*spec)\n",
        # A local helper reached through an unpacking is unread the same way.
        "def harmonise(value):\n    return value * 1.0\n\n"
        "spec = [expected]\ndosage = harmonise(*spec)\n",
    ],
)
def test_a_star_unpacked_argument_leaves_the_call_unread(body: str) -> None:
    """``f(*spec)`` states no argument positions, so it states no operation.

    v2.0.2 counted ``node.args`` to decide whether a call reached past its
    read-only arity, and a ``*`` unpacking is one element of ``node.args``
    holding a sequence of unknown length. ``np.round(*spec)`` with a
    three-element ``spec`` writes its third element and was reported as the
    continuous posterior expectation. This is the positional twin of the
    ``**`` rule: the call's result is unreadable and every traced value its
    subtree names is presumed written.
    """

    _assert_abstains(_posterior_workflow(body))


def test_a_star_unpacked_prediction_is_unreadable_rather_than_fresh() -> None:
    """An evaluation whose arguments do not resolve is a step, not a value."""

    _assert_abstains(
        _calibration_workflow("argv = [features]\ndosage = calibrator.predict(*argv)\n")
    )


def test_the_same_calls_without_an_unpacking_still_read() -> None:
    """The boundary: only the unpacking is at issue."""

    unsupported, states = _resolve(
        _posterior_workflow("spec = expected\ndosage = np.round(spec, 2)\n")
    )
    assert not unsupported
    assert states == {EXPECTATION}


# ---------------------------------------------------------------------------
# Family 18: an evaluation is keyed on its arguments' values, not their
# spelling.


_TWO_SPELLINGS_REPRODUCTION = _calibration_workflow(
    "argv = [features]\n"
    "raw = calibrator.predict(features)\n"
    "drift = calibrator.predict(X=features) - calibrator.predict(*argv)\n"
    "dosage = raw.round() + drift\n"
)


def test_one_evaluation_written_in_two_spellings_cancels() -> None:
    """``predict(features)`` and ``predict(X=features)`` are one value.

    v2.0.2 keyed the evaluation cache on ``(position, ids)`` and
    ``(keyword name, ids)``, so moving one argument from a position to a
    keyword minted a second identity for the same call. Their difference is
    identically zero at run time, and it read as an independent continuous
    addend that restored the scale a ``round()`` had removed.
    """

    _assert_abstains(
        _calibration_workflow(
            "raw = calibrator.predict(features)\n"
            "drift = calibrator.predict(X=features) - calibrator.predict(features)\n"
            "dosage = raw.round() + drift\n"
        )
    )


def test_the_two_spellings_reproduction_abstains() -> None:
    """The review's consolidated form, which also carries the ``*`` spelling."""

    _assert_abstains(_TWO_SPELLINGS_REPRODUCTION)


def test_an_evaluation_on_different_values_still_mints_fresh_provenance() -> None:
    """The boundary: the signature still separates different argument values."""

    source = _calibration_workflow(
        "replicate = pd.read_csv(Path('inputs/replicate.csv'))\n"
        "raw = calibrator.predict(features)\n"
        "dosage = raw - calibrator.predict(X=replicate[['marker_a', 'marker_b']])\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {CALIBRATION}


# ---------------------------------------------------------------------------
# Family 19: two identically constructed and fitted estimators are one
# estimator written twice.


_TWO_ESTIMATORS_REPRODUCTION = _calibration_workflow(
    "raw = calibrator.predict(features)\n"
    "second = RidgeCV().fit(features, frame['copy_index'])\n"
    "third = RidgeCV().fit(features, frame['copy_index'])\n"
    "dosage = raw.round() + (second.predict(features) - third.predict(features))\n"
)


def test_two_identically_fitted_estimators_cancel_into_abstention() -> None:
    """A deterministic estimator fitted twice on one dataset is one estimator.

    v2.0.2 minted an identity per construction site, so the difference of the
    two predictions read as an independent continuous addend and restored the
    scale a ``round()`` had removed. At run time that difference is
    identically zero for any deterministic estimator; for a nondeterministic
    one it is unknown, which is not a continuous repair either. Merging the
    identities can only add abstention, never a classification.
    """

    _assert_abstains(_TWO_ESTIMATORS_REPRODUCTION)


def test_an_estimator_fitted_by_keyword_shares_the_positional_fits_identity() -> None:
    """The fit signature discards names and positions too."""

    source = _calibration_workflow(
        "raw = calibrator.predict(features)\n"
        "second = RidgeCV().fit(X=features, y=frame['copy_index'])\n"
        "dosage = raw - second.predict(features)\n"
    )
    _assert_abstains(source)


# ---------------------------------------------------------------------------
# Family 20: row selection is reserved for index forms this trace read in
# full.


_UNREAD_INDEX_REPRODUCTION = _posterior_workflow(
    "centres = expected[0:3]\n"
    "level = expected.round().astype(int)\n"
    "key = level & 1\n"
    "dosage = centres[key]\n"
)


@pytest.mark.parametrize(
    "body",
    [
        # The review's form: the index is a bit operation this trace lost.
        "centres = expected[0:3]\n"
        "level = expected.round().astype(int)\n"
        "key = level & 1\n"
        "dosage = centres[key]\n",
        # An index the trace never bound at all.
        "dosage = expected[picks]\n",
        # An index built by a call whose result the trace could not read.
        "dosage = expected[np.argsort(expected)]\n",
        # A comparison this trace did not watch produce a mask: its operands
        # are opaque staged columns, so no mask was established.
        "mask = frame['qc_pass'] == 1\ndosage = expected[mask]\n",
        # A slice whose bounds are not literal.
        "cut = expected.size // 2\ndosage = expected[0:cut]\n",
    ],
)
def test_an_index_this_trace_could_not_read_gathers(body: str) -> None:
    """An index the trace lost is an index it cannot rule out.

    v2.0.2 asked whether the index subtree held a *traced* value, so an index
    whose provenance the trace had already dropped -- an opaque column, an
    unreadable step, a name bound nowhere -- fell through to the row-selection
    reading and the gather was reported as the receiver's own continuous
    scale. A gather repeats and reorders whatever entries the index picked
    out, so it is neither the receiver's scale nor a reading this trace can
    complete.
    """

    _assert_abstains(_posterior_workflow(body))


# ---------------------------------------------------------------------------
# The fused adapter over every reproduction the review consolidated.


@pytest.mark.parametrize(
    ("label", "workflow"),
    [
        ("asarray with a dtype", _ASARRAY_DTYPE_REPRODUCTION),
        ("asarray_chkfinite", _CHKFINITE_REPRODUCTION),
        ("star-unpacked destination", _STARRED_DESTINATION_REPRODUCTION),
        ("one evaluation in two spellings", _TWO_SPELLINGS_REPRODUCTION),
        ("two identically fitted estimators", _TWO_ESTIMATORS_REPRODUCTION),
        ("an index the trace could not read", _UNREAD_INDEX_REPRODUCTION),
    ],
)
def test_the_released_adapter_abstains_on_every_v203_reproduction(
    label: str, workflow: str
) -> None:
    """Each of these resolved to an operand under v2.0.2, and each was wrong."""

    assert _fused_observation(_SILENT_REPORT, workflow) == ("unsupported", None), label


# ---------------------------------------------------------------------------
# The fused adapter over every reproduction the review consolidated.


@pytest.mark.parametrize(
    ("label", "workflow"),
    [
        (
            "repeated predictions",
            _calibration_workflow(
                "raw = calibrator.predict(features)\n"
                "replicate_one = calibrator.predict(features)\n"
                "replicate_two = calibrator.predict(features)\n"
                "batch_drift = replicate_one - replicate_two\n"
                "dosage = raw.round() + batch_drift\n"
            ),
        ),
        (
            "dict-unpacked dtype",
            _posterior_workflow("dosage = np.array(expected, **{'dtype': int})\n"),
        ),
        (
            "dict-unpacked destination",
            _posterior_workflow(
                "dosage = expected * 1.0\nnp.round(expected, 0, **{'out': dosage})\n"
            ),
        ),
        (
            "dict-unpacked decimal count",
            _posterior_workflow("dosage = expected.round(**{'decimals': 2})\n"),
        ),
        (
            "positional destination",
            _posterior_workflow("dosage = expected * 1.0\nexpected.round(0, dosage)\n"),
        ),
        (
            "numpy view",
            _posterior_workflow(
                "dosage = expected * 1.0\nview = dosage.ravel()\nnp.copyto(view, np.round(view))\n"
            ),
        ),
        (
            "mixed where branches",
            _posterior_workflow(
                "mask = frame['qc_pass'] == 1\n"
                "dosage = np.where(mask, np.round(expected), expected)\n"
            ),
        ),
        (
            "table gather",
            _calibration_workflow(
                "raw = calibrator.predict(features)\n"
                "centres = raw[0:3]\n"
                "dosage = centres[raw.round().astype(int)]\n"
            ),
        ),
    ],
)
def test_the_released_adapter_abstains_on_every_reproduction(label: str, workflow: str) -> None:
    """Each of these resolved to an operand under v2.0.1, and each was wrong."""

    assert _fused_observation(_SILENT_REPORT, workflow) == ("unsupported", None), label
