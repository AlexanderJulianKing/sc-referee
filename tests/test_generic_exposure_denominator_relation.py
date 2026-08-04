from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from sc_referee.controller import replay, run_audit
from sc_referee.method_contract_run import run_method_contract
from sc_referee.scientific_requirement_contract import (
    SCIENTIFIC_REQUIREMENT_PROFILE_ID,
    SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
)

CHECK_ID = "check:complete-domain-exposure-denominator"
REQUIRED_CANDIDATE_ID = "complete-declared-domain-exposure"
REQUIRED_OPERAND = "complete_declared_domain_exposure"
CONFLICTING_OPERAND = "retained_observed_subset_exposure_only"
GENERIC_WRITER = (
    "from pathlib import Path\nPath('report.md').write_text('generated\\n', encoding='utf-8')\n"
)

CONFLICT_REPORTS = (
    (
        "acoustic survey",
        """# Acoustic recurrence summary

The primary recurrence estimate is the mean time between detected acoustic events.
It was calculated from the duration of retained high-confidence windows divided by the event
count. Masked low-confidence intervals were excluded from the exposure denominator.
""",
    ),
    (
        "microscopy transect",
        """# Punctum spacing

The selected spacing result describes distance between puncta along the imaging field. The
calculation uses only retained observed bins. Missing bins were omitted from the total length in
the denominator.
""",
    ),
    (
        "environmental timeline",
        """# Transition interval

The reported transition-time estimate divides the summed lengths of eligible measured intervals
by the transition count. Filtered intervals were not included in the exposure denominator.
""",
    ),
)

CORRECTED_REPORTS = (
    (
        "orbital timeline",
        """# Event recurrence

The primary recurrence estimate was computed over the complete declared timeline, including
masked low-confidence intervals, and divided by the event count.
""",
    ),
    (
        "survey route",
        """# Spacing estimate

The selected spacing estimate was calculated using the full declared route, including dropped
segments without retained measurements.
""",
    ),
)


def _write_project(repository: Path, report: str) -> None:
    repository.mkdir()
    (repository / "task.md").write_text(
        "Apply the scientist-authorized denominator-domain requirement.\n",
        encoding="utf-8",
    )
    (repository / "report.md").write_text(report, encoding="utf-8")
    (repository / "analysis.py").write_text(GENERIC_WRITER, encoding="utf-8")


def _contract(repository: Path, output: Path, schema_root: Path) -> Path:
    contract = run_method_contract(
        repository,
        "task.md",
        output,
        schema_root,
        profile={
            "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            "check_id": CHECK_ID,
            "candidate_id": REQUIRED_CANDIDATE_ID,
        },
        actor_id="scientist:generic-exposure-test",
    )
    assert contract["findings"] == []
    return output / "semantic.lock.json"


def _module(lock_path: Path) -> dict[str, Any]:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    return next(
        module
        for module in lock["scientific_check_registry"]["evaluation"]["modules"]
        if module["check_id"] == CHECK_ID
    )


def _result(bundle: dict[str, Any]) -> dict[str, Any] | None:
    for result in bundle["detector_results"]:
        if result["detector_id"] != "detector:bounded-analysis-method-conflict":
            continue
        ledger = next(
            (
                evidence
                for evidence in result["evidence"]
                if evidence["evidence_id"] == "evidence:analysis-method-ledger"
            ),
            None,
        )
        if ledger is not None and ledger["observed_value"]["requirement"] == REQUIRED_OPERAND:
            return result
    return None


@pytest.mark.parametrize(("variant", "report"), CONFLICT_REPORTS, ids=lambda value: value)
def test_generic_renamed_conflicts_emit_development_detector_results(
    schema_root: Path,
    tmp_path: Path,
    variant: str,
    report: str,
) -> None:
    repository = tmp_path / "project"
    _write_project(repository, report)
    lock_path = _contract(repository, tmp_path / "contract", schema_root)

    output = tmp_path / "audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report="report.md",
        method_contract_lock=lock_path,
    )

    assert _module(output / "semantic.lock.json")["state"] == "applicable"
    result = _result(bundle)
    assert result is not None, variant
    assert result["state"] == "evaluation_finding_candidate"
    assert result["extensions"]["x-production-finding-permitted"] is False
    ledger = next(
        item
        for item in result["evidence"]
        if item["evidence_id"] == "evidence:analysis-method-ledger"
    )
    assert ledger["observed_value"]["observed"] == CONFLICTING_OPERAND
    assert bundle["findings"] == []
    assert bundle["executions"] == []

    replayed = replay(output / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["detector_results"] == bundle["detector_results"]


@pytest.mark.parametrize(("variant", "report"), CORRECTED_REPORTS, ids=lambda value: value)
def test_generic_corrected_variants_are_covered_negatives(
    schema_root: Path,
    tmp_path: Path,
    variant: str,
    report: str,
) -> None:
    repository = tmp_path / "project"
    _write_project(repository, report)
    lock_path = _contract(repository, tmp_path / "contract", schema_root)

    output = tmp_path / "audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report="report.md",
        method_contract_lock=lock_path,
    )

    assert _module(output / "semantic.lock.json")["state"] == "applicable"
    result = _result(bundle)
    assert result is not None, variant
    assert result["state"] == "no_issue_detected_within_coverage"
    assert "evaluation_candidate" not in result
    assert bundle["findings"] == []
    assert bundle["executions"] == []


@pytest.mark.parametrize(
    ("report", "expected_state"),
    (
        (
            """# Ambiguous exposure

The primary recurrence estimate uses retained observed intervals. Missing intervals are omitted
from the exposure denominator. The selected recurrence calculation was also computed over the
complete declared timeline, including missing intervals.
""",
            "ambiguous",
        ),
        (
            """# Opaque exposure

The primary recurrence estimate uses an exposure denominator assembled from retained and missing
intervals, but the report does not state how those intervals enter the denominator.
""",
            "unsupported",
        ),
        (
            """# Unrelated retention summary

The primary survival analysis retained observed records after consent checks. Follow-up time was
reported descriptively; no normalized event-frequency calculation was selected.
""",
            "not_applicable",
        ),
    ),
)
def test_generic_relation_abstains_without_reversing_unknowns(
    schema_root: Path,
    tmp_path: Path,
    report: str,
    expected_state: str,
) -> None:
    repository = tmp_path / "project"
    _write_project(repository, report)
    lock_path = _contract(repository, tmp_path / "contract", schema_root)

    output = tmp_path / "audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report="report.md",
        method_contract_lock=lock_path,
    )

    assert _module(output / "semantic.lock.json")["state"] == expected_state
    assert _result(bundle) is None
    assert bundle["findings"] == []
    assert bundle["executions"] == []
