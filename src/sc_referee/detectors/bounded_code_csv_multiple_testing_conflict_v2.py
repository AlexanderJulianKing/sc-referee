from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_dependence_conflict import (
    BoundedCodeCsvDependenceConflictDetector,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v2 import (
    COMPLETE_FAMILY_CORRECTION_OPERAND,
    MULTIPLE_TESTING_CODE_CHECK_ID,
    NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND,
    STRICT_SUBSET_FAMILY_CORRECTION_OPERAND,
)


class BoundedCodeCsvMultipleTestingConflictV2Detector(BoundedCodeCsvDependenceConflictDetector):
    """Evaluate only the frozen complete-family correction scalar conflict."""

    detector_id = "detector:bounded-code-csv-multiple-testing-conflict"
    detector_version = "2.0.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v2:"
        "BoundedCodeCsvMultipleTestingConflictV2Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())

    def evaluate(
        self, locked_case: Mapping[str, Any], question: Mapping[str, Any]
    ) -> dict[str, Any]:
        extensions = question.get("extensions")
        if (
            not isinstance(extensions, Mapping)
            or extensions.get("x-scientific-check-id") != MULTIPLE_TESTING_CODE_CHECK_ID
        ):
            raise ValueError("multiple-testing detector received an unregistered check target")
        observed = extensions.get("x-posthoc-reported-assertion-ids")
        if not isinstance(observed, Mapping):
            raise ValueError("multiple-testing detector target has no observed assertion map")
        assertion_ids = observed.get("selection_process")
        if (
            not isinstance(assertion_ids, Sequence)
            or isinstance(assertion_ids, (str, bytes))
            or len(assertion_ids) != 1
        ):
            raise ValueError("multiple-testing detector requires one observed family operand")
        expected_id = str(assertion_ids[0])
        assertions = locked_case.get("semantic_assertions")
        if not isinstance(assertions, Sequence) or isinstance(assertions, (str, bytes)):
            raise ValueError("multiple-testing detector assertion collection is unavailable")
        matches = [
            item
            for item in assertions
            if isinstance(item, Mapping) and item.get("assertion_id") == expected_id
        ]
        allowed = {
            COMPLETE_FAMILY_CORRECTION_OPERAND,
            NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND,
            STRICT_SUBSET_FAMILY_CORRECTION_OPERAND,
        }
        if len(matches) != 1 or matches[0].get("object") not in allowed:
            raise ValueError("multiple-testing detector observed operand is outside its registry")
        return super().evaluate(locked_case, question)
