from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sc_referee_evaluation.prospective_qualification_v2 import (
    CASE_EVIDENCE_CONTRACT_VERSION,
)

from sc_referee.core.ids import semantic_digest


def _historical_freeze(project_root: Path) -> dict[str, Any]:
    path = (
        project_root
        / "evaluation"
        / "qualification"
        / "complete-domain-exposure-denominator-v1.1.0-precase"
        / "FREEZE_MANIFEST.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_historical_v2_precase_freeze_remains_self_authenticating(
    project_root: Path,
) -> None:
    freeze = _historical_freeze(project_root)
    declared_digest = freeze.pop("freeze_digest")

    assert declared_digest == semantic_digest(freeze)
    assert declared_digest == (
        "sha256:55a515535246aa1a4d1c091ed020e8a087b78552b727ee947439b26a01142ae8"
    )
    assert freeze["source_commit"] == "f6d5adb6d6314f58fa2ea9a09e721015732ed2c4"


def test_historical_v2_precase_freeze_has_zero_authority_and_is_not_current(
    project_root: Path,
) -> None:
    freeze = _historical_freeze(project_root)

    assert freeze["envelope"]["case_evidence_contract_version"] == "2.0.0"
    assert CASE_EVIDENCE_CONTRACT_VERSION == "3.0.0"
    assert freeze["metric_case_count"] == 0
    assert freeze["scientific_label_count"] == 0
    assert freeze["detector_outcome_count"] == 0
    assert freeze["qualification_authority"] == "none_precase_freeze_only"
    assert freeze["detector"]["production_finding_permitted"] is False
