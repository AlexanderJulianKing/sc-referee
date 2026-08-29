from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from sc_referee.capability_matrix import (
    default_capability_manifest_root,
    load_capability_detector_manifest,
)
from sc_referee.core.ids import semantic_digest
from sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v3_1 import (
    BoundedCodeCsvMultipleTestingConflictV3_1Detector,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_1 import (
    MULTIPLE_TESTING_CODE_CHECK_ID,
)
from sc_referee.scientific_checks.profiles import scientific_check_release_registry


def _binding() -> Any:
    return next(
        item
        for item in scientific_check_release_registry().development_method_conflict_bindings
        if item.check_id == MULTIPLE_TESTING_CODE_CHECK_ID
    )


def _manifest(schema_root: Path) -> dict[str, Any]:
    return load_capability_detector_manifest(
        default_capability_manifest_root(),
        schema_root,
        BoundedCodeCsvMultipleTestingConflictV3_1Detector.detector_id,
        detector_version=BoundedCodeCsvMultipleTestingConflictV3_1Detector.detector_version,
    )


def _detector(schema_root: Path) -> BoundedCodeCsvMultipleTestingConflictV3_1Detector:
    return BoundedCodeCsvMultipleTestingConflictV3_1Detector(
        _manifest(schema_root),
        (_binding(),),
    )


def _question() -> dict[str, Any]:
    return {
        "extensions": {
            "x-scientific-check-id": MULTIPLE_TESTING_CODE_CHECK_ID,
            "x-posthoc-reported-assertion-ids": {
                "selection_process": ["assertion:observed-family"]
            },
        }
    }


def test_detector_identity_is_pinned_to_manifest_and_development_binding(
    schema_root: Path,
) -> None:
    manifest = _manifest(schema_root)
    binding = _binding()
    detector = _detector(schema_root)

    assert detector.detector_id == "detector:bounded-code-csv-multiple-testing-conflict"
    assert detector.detector_version == "3.1.0"
    assert detector.entry_point == (
        "sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v3_1:"
        "BoundedCodeCsvMultipleTestingConflictV3_1Detector"
    )
    assert detector.implementation_digest() == manifest["implementation"]["implementation_digest"]
    assert detector.manifest_digest == semantic_digest(manifest)
    assert detector.manifest_digest == binding.detector_manifest_digest
    assert binding.check_version == "3.1.0"
    module = next(
        item
        for item in scientific_check_release_registry().modules_for_lane("development")
        if item.manifest.check_id == MULTIPLE_TESTING_CODE_CHECK_ID
    )
    assert module.manifest.check_version == "3.1.0"
    assert module.adapter_manifests[0].adapter_version == "3.1.0"
    assert binding in scientific_check_release_registry().development_method_conflict_bindings
    assert binding not in scientific_check_release_registry().method_conflict_bindings


@pytest.mark.parametrize(
    ("locked_case", "question", "message"),
    [
        ({}, {}, "multiple-testing detector received an unregistered check target"),
        (
            {},
            {"extensions": {"x-scientific-check-id": MULTIPLE_TESTING_CODE_CHECK_ID}},
            "multiple-testing detector target has no observed assertion map",
        ),
        (
            {},
            {
                "extensions": {
                    "x-scientific-check-id": MULTIPLE_TESTING_CODE_CHECK_ID,
                    "x-posthoc-reported-assertion-ids": {"selection_process": []},
                }
            },
            "multiple-testing detector requires one observed family operand",
        ),
        (
            {"semantic_assertions": None},
            _question(),
            "multiple-testing detector assertion collection is unavailable",
        ),
        (
            {
                "semantic_assertions": [
                    {
                        "assertion_id": "assertion:observed-family",
                        "object": "outside_closed_operand_registry",
                    }
                ]
            },
            _question(),
            "multiple-testing detector observed operand is outside its registry",
        ),
    ],
)
def test_detector_value_error_guards_are_exact(
    schema_root: Path,
    locked_case: dict[str, Any],
    question: dict[str, Any],
    message: str,
) -> None:
    with pytest.raises(ValueError) as error:
        _detector(schema_root).evaluate(locked_case, question)
    assert str(error.value) == message
