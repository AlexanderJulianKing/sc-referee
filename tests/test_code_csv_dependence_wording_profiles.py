from __future__ import annotations

import json
from pathlib import Path

import pytest

from sc_referee.detectors.method_conflict_finding import (
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST,
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_ID,
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST,
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID,
    draft_method_conflict_finding,
)
from sc_referee.scientific_checks.core import MethodConflictBinding

_ENVELOPE_5 = Path("evaluation/development/blind-envelope-5-2026-08-22/cases")
_QUALIFIED_CASES = (
    "0b4876ceca6b0a9aede7",
    "1975f22bc0022b19331f",
    "2448bea72701b75fce2a",
    "a1541d5c671f3d6d58ce",
)
_CHECK_ID = "check:authorized-independent-unit-entry-into-row-independent-procedure"
_TITLE = "Analysis code contradicts the frozen one-row-per-authorized-unit requirement"


def _binding(payload: dict[str, object]) -> MethodConflictBinding:
    return MethodConflictBinding(
        binding_id=str(payload["binding_id"]),
        check_id=str(payload["check_id"]),
        check_version=str(payload["check_version"]),
        check_manifest_digest=str(payload["check_manifest_digest"]),
        detector_id=str(payload["detector_id"]),
        detector_version=str(payload["detector_version"]),
        detector_manifest_digest=str(payload["detector_manifest_digest"]),
        dimension=str(payload["dimension"]),
        comparison_form=str(payload["comparison_form"]),
        operand_kind=str(payload["operand_kind"]),  # type: ignore[arg-type]
        required_evidence_planes=tuple(payload["required_evidence_planes"]),  # type: ignore[arg-type]
        required_semantic_roles=tuple(payload["required_semantic_roles"]),  # type: ignore[arg-type]
        required_assertion_roles=tuple(payload["required_assertion_roles"]),  # type: ignore[arg-type]
        counterevidence_predicates=tuple(payload["counterevidence_predicates"]),  # type: ignore[arg-type]
        forbidden_members=tuple(payload["forbidden_members"]),  # type: ignore[arg-type]
        production_finding_permitted=bool(payload["production_finding_permitted"]),
    )


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

    draft = draft_method_conflict_finding(
        old_results[0],
        _binding(old_bindings[0]),
        work_packet={
            "semantic_assertions": bundle["semantic_assertions"],
            "answers": bundle["answers"],
        },
    )
    assert draft["title"] == _TITLE
    assert draft["extensions"]["x-finding-wording-profile-id"] == (
        CODE_CSV_DEPENDENCE_FINDING_PROFILE_ID
    )
    assert draft["extensions"]["x-finding-wording-profile-digest"] == (
        CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST
    )
    assert "component of a composite key" not in draft["summary"]
