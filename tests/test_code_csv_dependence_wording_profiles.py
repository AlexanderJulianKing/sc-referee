from __future__ import annotations

import json
from pathlib import Path

import pytest

from sc_referee.detectors.method_conflict_finding import (
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST,
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_ID,
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST,
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID,
)

_ENVELOPE_5 = Path("evaluation/development/blind-envelope-5-2026-08-22/cases")
_QUALIFIED_CASES = (
    "0b4876ceca6b0a9aede7",
    "1975f22bc0022b19331f",
    "2448bea72701b75fce2a",
    "a1541d5c671f3d6d58ce",
)
_CHECK_ID = "check:authorized-independent-unit-entry-into-row-independent-procedure"
_TITLE = "Analysis code contradicts the frozen one-row-per-authorized-unit requirement"


def test_v1_wording_profile_bytes_remain_frozen() -> None:
    assert CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST == (
        "sha256:0440fdb918eb04ff975e7129c4152a2d681f3f4203ae8c7a1f8fc9ebf8916288"
    )
    assert CODE_CSV_DEPENDENCE_FINDING_PROFILE_ID.endswith("requirement-conflict-v1")
    assert CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID.endswith("requirement-conflict-v2")
    assert CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST != (
        CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST
    )


@pytest.mark.parametrize("case_id", _QUALIFIED_CASES)
def test_frozen_2_1_lane_audit_still_has_one_v1_finding(case_id: str) -> None:
    root = _ENVELOPE_5 / case_id / "audit-run-step11-installed"
    bundle = json.loads((root / "audit.bundle.json").read_text(encoding="utf-8"))
    lock = json.loads((root / "semantic.lock.json").read_text(encoding="utf-8"))
    old_bindings = [
        item
        for item in lock["scientific_check_registry"]["method_conflict_bindings"]
        if item["check_id"] == _CHECK_ID
        and item["detector_id"] == "detector:bounded-code-csv-dependence-conflict"
    ]
    old_results = [
        item
        for item in bundle["detector_results"]
        if item.get("detector_id") == "detector:bounded-code-csv-dependence-conflict"
    ]
    assert len(old_bindings) == len(old_results) == 1
    assert old_bindings[0]["detector_version"] == old_results[0]["detector_version"] == "2.1.0"
    assert [item["title"] for item in bundle["findings"]] == [_TITLE]

    frozen_finding = bundle["findings"][0]
    assert frozen_finding["title"] == _TITLE
    assert frozen_finding["extensions"]["x-finding-wording-profile-id"] == (
        CODE_CSV_DEPENDENCE_FINDING_PROFILE_ID
    )
    assert frozen_finding["extensions"]["x-finding-wording-profile-digest"] == (
        CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST
    )
    assert "component of a composite key" not in frozen_finding["summary"]
