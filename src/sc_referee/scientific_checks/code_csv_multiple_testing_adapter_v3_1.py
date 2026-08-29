"""Multiple-testing 3.1 adapter identity over the byte-frozen 3.0 source result."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest
from sc_referee.scientific_checks.adapter_common import adapter_implementation_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3 import (
    _CLOSED_REASONS,
    COMPLETE_FAMILY_CORRECTION_OPERAND,
    MULTIPLE_TESTING_CODE_ADAPTER_ID,
    MULTIPLE_TESTING_CODE_CANDIDATE_ID,
    MULTIPLE_TESTING_CODE_CHECK_ID,
    MULTIPLE_TESTING_CODE_COUNTEREVIDENCE,
    MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    MULTIPLE_TESTING_CODE_SEMANTIC_ROLES,
    NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND,
    STRICT_SUBSET_FAMILY_CORRECTION_OPERAND,
    MultipleTestingCodeEvidenceProjection,
    MultipleTestingCodeObservation,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3 import (
    COMPLETE_FAMILY_CORRECTION_OPERAND as _COMPLETE,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3 import (
    NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND as _NONE,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3 import (
    STRICT_SUBSET_FAMILY_CORRECTION_OPERAND as _SUBSET,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3 import (
    CodeCsvMultipleTestingAdapter as _FrozenV3Adapter,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3 import (
    code_csv_multiple_testing_grammar as _frozen_v3_grammar,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_1 import (
    CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST,
)

MULTIPLE_TESTING_CODE_CHECK_VERSION = "3.1.0"
MULTIPLE_TESTING_CODE_ADAPTER_VERSION = "3.1.0"
CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS = frozenset(_CLOSED_REASONS)


def code_csv_multiple_testing_grammar() -> dict[str, Any]:
    """Return the frozen source grammar with only the versioned 3.1 identity fields changed."""

    value = _frozen_v3_grammar()
    value["grammar_version"] = MULTIPLE_TESTING_CODE_ADAPTER_VERSION
    value["dataflow_implementation_digest"] = (
        CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST
    )
    value["question_layer"] = {
        "profile": "material-question:multiple-testing-correction-scope-v1",
        "runs_after_frozen_source_result": True,
        "source_classification_changes": False,
    }
    return value


def code_csv_multiple_testing_grammar_digest() -> str:
    return semantic_digest(code_csv_multiple_testing_grammar())


CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST = adapter_implementation_digest(
    Path(__file__)
)


class CodeCsvMultipleTestingAdapter(_FrozenV3Adapter):
    """Use the frozen 3.0 inspection implementation under a distinct 3.1 manifest identity."""

    @property
    def implementation_digest(self) -> str:
        return CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST

    @property
    def recognition_grammar_digest(self) -> str:
        return code_csv_multiple_testing_grammar_digest()


assert COMPLETE_FAMILY_CORRECTION_OPERAND == _COMPLETE
assert NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND == _NONE
assert STRICT_SUBSET_FAMILY_CORRECTION_OPERAND == _SUBSET

__all__ = [
    "CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS",
    "CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST",
    "COMPLETE_FAMILY_CORRECTION_OPERAND",
    "MULTIPLE_TESTING_CODE_ADAPTER_ID",
    "MULTIPLE_TESTING_CODE_ADAPTER_VERSION",
    "MULTIPLE_TESTING_CODE_CANDIDATE_ID",
    "MULTIPLE_TESTING_CODE_CHECK_ID",
    "MULTIPLE_TESTING_CODE_CHECK_VERSION",
    "MULTIPLE_TESTING_CODE_COUNTEREVIDENCE",
    "MULTIPLE_TESTING_CODE_ROLE_BINDINGS",
    "MULTIPLE_TESTING_CODE_SEMANTIC_ROLES",
    "NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND",
    "STRICT_SUBSET_FAMILY_CORRECTION_OPERAND",
    "CodeCsvMultipleTestingAdapter",
    "MultipleTestingCodeEvidenceProjection",
    "MultipleTestingCodeObservation",
    "code_csv_multiple_testing_grammar",
    "code_csv_multiple_testing_grammar_digest",
]
