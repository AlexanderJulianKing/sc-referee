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
from sc_referee.scientific_checks.copy_dosage_dataflow import _document_dose_representations
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


def test_binning_followed_by_a_continuous_centre_table_restores_the_scale() -> None:
    """``centers[digitize(x)]`` puts the value back on a continuous scale."""

    source = _posterior_workflow(
        "centers = np.array([0.12, 0.98, 1.93])\n"
        "dosage = centers[np.digitize(expected, [0.5, 1.5])]\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {EXPECTATION}


def test_binning_followed_by_an_integral_table_is_still_the_hard_state() -> None:
    """A lookup table of whole numbers is another way of writing the hard call."""

    source = _posterior_workflow(
        "states = np.array([0, 1, 2])\ndosage = states[np.digitize(expected, [0.5, 1.5])]\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {QUANTIZED}


def test_a_residual_against_the_rounded_value_restores_the_continuous_scale() -> None:
    """``raw - raw.round()`` is arithmetic against a traced continuous value."""

    source = _calibration_workflow(
        "raw = calibrator.predict(features)\ndosage = raw - raw.round()\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {CALIBRATION}


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
