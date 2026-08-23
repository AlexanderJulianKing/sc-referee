from __future__ import annotations

from typing import Any, cast

import pytest

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.detectors.bounded_analysis_method_conflict import (
    BoundedAnalysisMethodConflictDetector,
)
from sc_referee.detectors.bounded_code_csv_dependence_conflict_v2_1 import (
    BoundedCodeCsvDependenceConflictV21Detector,
)
from sc_referee.detectors.method_conflict_grant_pins import (
    GRANT_PINS,
    installed_pin_matches_live_identity,
)
from sc_referee.scientific_checks.code_csv_dependence_dataflow import (
    select_code_source_envelope,
)
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    InspectionDocument,
    RecordRef,
)
from sc_referee.scientific_checks.profiles import scientific_check_release_registry
from sc_referee.scientific_checks.report_csv_dependence_adapter import _parse_csv

_CHECK_ID = "check:authorized-independent-unit-entry-into-row-independent-procedure"
_COMPLETE_BINDING_ID = "method-conflict-binding:complete-domain-exposure-denominator-v1"


def _file_record(path: str, identifier: str) -> FrozenBaseRecord:
    ref = RecordRef("file_record", identifier)
    return FrozenBaseRecord.from_record(
        ref,
        {
            "record_type": "file_record",
            "file_record_id": identifier,
            "path": path,
            "entry_kind": "regular_file",
        },
    )


def _analysis_document() -> InspectionDocument:
    return _python_document("analysis.py", b"import pandas as pd\n", "file:analysis")


def _python_document(path: str, content: bytes, identifier: str) -> InspectionDocument:
    content_digest = sha256_digest(content)
    parser_payload = canonical_json(
        {
            "parser_id": "parser:python-ast-tokenize",
            "parser_version": "0.15.1",
            "coverage_status": "covered",
            "source_ref": {
                "path": path,
                "content_digest": content_digest,
            },
        }
    ).encode()
    return InspectionDocument(
        path=path,
        file_ref=RecordRef("file_record", identifier),
        content=content,
        content_digest=content_digest,
        media_type="text/x-python",
        parser_result_ref=RecordRef("parser_result", "parser-result:analysis"),
        parser_result_payload=parser_payload,
        parser_result_digest=sha256_digest(parser_payload),
    )


class _ProsePayloadTripwire:
    path = "report.md"

    @property
    def content(self) -> bytes:
        raise AssertionError("code dependence lane touched a prose payload")


def test_section_12_1_prose_payload_tripwire_is_not_touched() -> None:
    envelope = select_code_source_envelope(
        base_records=(
            _file_record("analysis.py", "file:analysis"),
            _file_record("report.md", "file:report"),
        ),
        documents=(
            _analysis_document(),
            cast(InspectionDocument, cast(Any, _ProsePayloadTripwire())),
        ),
    )
    assert envelope.reason is None
    assert envelope.analysis is not None
    assert envelope.analysis.path == "analysis.py"


def test_report_absent_present_and_altered_leave_source_envelope_identical() -> None:
    analysis_record = _file_record("analysis.py", "file:analysis")
    absent = select_code_source_envelope(
        base_records=(analysis_record,),
        documents=(_analysis_document(),),
    )
    present = select_code_source_envelope(
        base_records=(analysis_record, _file_record("report.md", "file:report")),
        documents=(
            _analysis_document(),
            cast(InspectionDocument, cast(Any, _ProsePayloadTripwire())),
        ),
    )
    altered = select_code_source_envelope(
        base_records=(analysis_record, _file_record("notes.txt", "file:notes")),
        documents=(
            _analysis_document(),
            cast(InspectionDocument, cast(Any, _ProsePayloadTripwire())),
        ),
    )
    assert absent == present == altered


def test_alternate_analysis_extensions_abstain_without_opening_bytes() -> None:
    for path in ("notebook.ipynb", "model.R", "MODEL.r"):
        envelope = select_code_source_envelope(
            base_records=(
                _file_record("analysis.py", "file:analysis"),
                _file_record(path, "file:alternate"),
            ),
            documents=(_analysis_document(),),
        )
        assert envelope.reason == "alternate-analysis-file-present"


@pytest.mark.parametrize(
    "dynamic_source",
    [
        b'module = __import__("scipy.stats")\n',
        b'import importlib\nmodule = importlib.import_module("scipy.stats")\n',
        b'from importlib import import_module\nmodule = import_module("scipy.stats")\n',
    ],
)
def test_b5_dynamic_import_in_other_python_file_makes_e6_scan_incomplete(
    dynamic_source: bytes,
) -> None:
    envelope = select_code_source_envelope(
        base_records=(
            _file_record("analysis.py", "file:analysis"),
            _file_record("helper.py", "file:helper"),
        ),
        documents=(
            _analysis_document(),
            _python_document("helper.py", dynamic_source, "file:helper"),
        ),
    )
    assert envelope.reason == "other-python-statistics-scan-unavailable"


@pytest.mark.parametrize(
    "module",
    [
        "scipy",
        "scipy.stats",
        "statsmodels",
        "pingouin",
        "pymer4",
        "bambi",
        "linearmodels",
        "sklearn",
        "pymc",
        "numpyro",
        "stan",
        "cmdstanpy",
        "rpy2",
        "lifelines",
    ],
)
def test_every_e6_statistics_prefix_in_other_python_file_abstains(module: str) -> None:
    envelope = select_code_source_envelope(
        base_records=(
            _file_record("analysis.py", "file:analysis"),
            _file_record("helper.py", "file:helper"),
        ),
        documents=(
            _analysis_document(),
            _python_document("helper.py", f"import {module}\n".encode(), "file:helper"),
        ),
    )
    assert envelope.reason == "statistics-api-imported-outside-analysis-py"


def test_benign_other_python_import_does_not_suppress() -> None:
    envelope = select_code_source_envelope(
        base_records=(
            _file_record("analysis.py", "file:analysis"),
            _file_record("helper.py", "file:helper"),
        ),
        documents=(
            _analysis_document(),
            _python_document("helper.py", b"import decimal\n", "file:helper"),
        ),
    )
    assert envelope.reason is None


def test_d1_prime_regular_index_and_label_collision_outcomes() -> None:
    regular = _parse_csv(
        b"unit,group,visit,value\nA,x,1,10\nA,x,2,11\nB,y,1,20\nB,y,2,21\n",
        "unit",
        "group",
    )
    assert not isinstance(regular, str)
    assert regular.candidate_columns == ("visit",)
    assert regular.within_unit_index_columns == ("visit",)
    assert regular.unique_nonindex_columns == ()

    collision = _parse_csv(
        b"unit,group,site,value\nA,x,north,10\nA,x,south,11\nB,y,north,20\n",
        "unit",
        "group",
    )
    assert not isinstance(collision, str)
    assert collision.candidate_columns == ("site",)
    assert collision.unique_nonindex_columns == ("site",)


def test_code_lane_has_distinct_detector_binding_and_installed_grant() -> None:
    registry = scientific_check_release_registry()
    binding = next(item for item in registry.method_conflict_bindings if item.check_id == _CHECK_ID)
    assert binding.detector_id == BoundedCodeCsvDependenceConflictV21Detector.detector_id
    assert binding.detector_version == "2.1.0"
    assert binding.production_finding_permitted is False
    assert installed_pin_matches_live_identity(GRANT_PINS[binding.binding_id]) is True


def test_complete_domain_pin_and_detector_bytes_remain_live() -> None:
    registry = scientific_check_release_registry()
    binding = next(
        item
        for item in registry.method_conflict_bindings
        if item.binding_id == _COMPLETE_BINDING_ID
    )
    pin = GRANT_PINS[_COMPLETE_BINDING_ID]
    assert binding.detector_id == BoundedAnalysisMethodConflictDetector.detector_id
    assert binding.detector_manifest_digest == pin.detector_manifest_digest
    assert binding.binding_digest == pin.binding_digest
    assert installed_pin_matches_live_identity(pin) is True


def test_code_lane_detector_identity_is_content_addressed() -> None:
    registry = scientific_check_release_registry()
    binding = next(item for item in registry.method_conflict_bindings if item.check_id == _CHECK_ID)
    assert binding.detector_manifest_digest.startswith("sha256:")
    assert len(binding.detector_manifest_digest) == 71
    assert semantic_digest(binding.to_dict()) == binding.binding_digest
