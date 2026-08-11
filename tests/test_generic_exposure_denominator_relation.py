from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.prospective_selected_result_verifier import (
    PYTHON_STATIC_MARKED_REPORT_PROFILE,
    freeze_independent_selected_result_derivation,
    revalidate_independent_selected_result_derivation,
)

import sc_referee.controller as controller
from sc_referee.controller import replay, run_audit
from sc_referee.method_contract_run import run_method_contract
from sc_referee.scientific_requirement_contract import (
    SCIENTIFIC_REQUIREMENT_PROFILE_ID,
    SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
)

CHECK_ID = "check:complete-domain-exposure-denominator"
REQUIRED_CANDIDATE_ID = "complete-declared-domain-exposure"
RETAINED_SUBSET_CANDIDATE_ID = "retained-observed-subset-exposure"
REQUIRED_OPERAND = "complete_declared_domain_exposure"
CONFLICTING_OPERAND = "retained_observed_subset_exposure_only"
GENERIC_WRITER = (
    "from pathlib import Path\nPath('report.md').write_text('generated\\n', encoding='utf-8')\n"
)


@pytest.fixture(autouse=True)
def _retain_detector_only_development_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep this retained corpus focused on pre-promotion detector semantics."""

    monkeypatch.setattr(
        controller,
        "_promote_method_conflict_evaluation",
        lambda _locked, evaluation: (deepcopy(evaluation.result), None),
    )


CONFLICT_REPORTS = (
    (
        "acoustic survey",
        """# Acoustic recurrence summary

The deployment scheduled 120 listening windows for the season. The screening step kept 90
windows with usable recordings and removed 30 windows. Detections occurred in 36 of the kept
windows. The primary detection rate for the full scheduled deployment is 0.40.
""",
    ),
    (
        "microscopy transect",
        """# Punctum spacing

Imaging planned 64 grid fields across the specimen. Quality screening retained 48 fields and
dropped 16 fields. Puncta were present in 12 retained fields. The selected presence proportion
for the complete planned grid is 0.25.
""",
    ),
    (
        "environmental timeline",
        """# Transition interval

The monitoring calendar comprised 200 scheduled intervals. Sensor validation kept 150 intervals
and excluded 50. Transitions were recorded in 45 validated intervals. The reported transition
proportion for the whole monitoring calendar is 0.30.
""",
    ),
)

CORRECTED_REPORTS = (
    (
        "orbital timeline",
        """# Event recurrence

The observation plan comprised 80 scheduled passes. Screening kept 60 passes and set aside 20.
Events were recorded in 16 passes. The primary event proportion for the complete observation
plan is 0.20, using every scheduled pass in the denominator.
""",
    ),
    (
        "survey route",
        """# Spacing estimate

The survey planned 50 route segments. Ground checks retained 35 segments and rejected 15.
Markers were found in 14 segments. The selected marker proportion for the full planned route is
0.28, computed over all planned segments including the rejected ones.
""",
    ),
)


def _write_project(
    repository: Path,
    report: str,
    *,
    report_path: str = "report.md",
    writer: str = GENERIC_WRITER,
) -> None:
    repository.mkdir()
    (repository / "task.md").write_text(
        "Apply the scientist-authorized denominator-domain requirement.\n",
        encoding="utf-8",
    )
    (repository / report_path).write_text(report, encoding="utf-8")
    (repository / "analysis.py").write_text(writer, encoding="utf-8")


def _contract(
    repository: Path,
    output: Path,
    schema_root: Path,
    *,
    candidate_id: str = REQUIRED_CANDIDATE_ID,
) -> Path:
    contract = run_method_contract(
        repository,
        "task.md",
        output,
        schema_root,
        profile={
            "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            "check_id": CHECK_ID,
            "candidate_id": candidate_id,
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


def _result(
    bundle: dict[str, Any],
    *,
    required_operand: str = REQUIRED_OPERAND,
) -> dict[str, Any] | None:
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
        if ledger is not None and ledger["observed_value"]["requirement"] == required_operand:
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

The plan listed 100 collection sessions; screening kept 70 and discarded 30. Signals occurred
in 21 kept sessions. One summary line reports the signal proportion as 0.30 while another
reports the study-wide proportion as 0.21, and the report does not reconcile the two.
""",
            "ambiguous",
        ),
        (
            """# Opaque exposure

Sensor identifiers active this cycle: 3 5 7 11 13 17 19 23 29 31 37 41 43 47 53 59 61 67 71 73
79 83 89 97 101 103 107 109 113 127 131 137 139 149 151 157 163 167 173 179 181 191 193 197
199 211 223 227 229 233 239 241 251 257 263. The proportion of flagged sensors was 0.30.
""",
            "unsupported",
        ),
        (
            """# Unrelated retention summary

The survey planned 120 visits, retained 90 after consent checks, and set aside 30. Follow-up
was reported descriptively; no normalized rate, proportion, or interval estimate is selected.
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


def test_report_filename_and_list_layout_are_not_scientific_authority(
    schema_root: Path,
    tmp_path: Path,
) -> None:
    repository = tmp_path / "project"
    report_path = "final_cycle_summary.md"
    report = """# Equipment-cycle recurrence

The maintenance plan covered 45 equipment cycles.

- Kept after log screening: 36 cycles.
- Discarded for missing logs: 9 cycles.
- Cycles with a fault event: 27.
- Selected fault proportion for the complete maintenance plan: 0.75.
"""
    writer = (
        "from pathlib import Path\n"
        "destination = Path('final_cycle_summary.md')\n"
        "destination.write_text('generated\\n', encoding='utf-8')\n"
    )
    _write_project(repository, report, report_path=report_path, writer=writer)
    lock_path = _contract(repository, tmp_path / "contract", schema_root)

    output = tmp_path / "audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report=report_path,
        method_contract_lock=lock_path,
    )

    result = _result(bundle)
    assert result is not None
    assert result["state"] == "evaluation_finding_candidate"
    assert result["extensions"]["x-production-finding-permitted"] is False
    assert bundle["findings"] == []


def test_scientist_authorized_conditional_domain_is_a_valid_alternative(
    schema_root: Path,
    tmp_path: Path,
) -> None:
    repository = tmp_path / "project"
    report = """# Conditional observation-window rate

The selected estimate is explicitly conditional on the screened subset. The campaign planned 90
watch windows; screening kept 72 and removed 18. Events occurred in 24 kept windows, and the
conditional event proportion among kept windows is 0.33. Windows outside the screened subset
are outside this conditional estimand.
"""
    _write_project(repository, report)
    lock_path = _contract(
        repository,
        tmp_path / "contract",
        schema_root,
        candidate_id=RETAINED_SUBSET_CANDIDATE_ID,
    )

    output = tmp_path / "audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report="report.md",
        method_contract_lock=lock_path,
    )

    result = _result(bundle, required_operand=CONFLICTING_OPERAND)
    assert result is not None
    assert result["state"] == "no_issue_detected_within_coverage"
    assert bundle["findings"] == []


def test_close_retention_language_is_clean_when_complete_denominator_is_explicit(
    schema_root: Path,
    tmp_path: Path,
) -> None:
    repository = tmp_path / "project"
    report = """# Sensor-event recurrence

The season scheduled 140 sensor shifts; validation retained 105 shifts and quarantined 35 for a
separate quality-control diagnostic table. Events occurred in 42 shifts. The primary event
proportion for the complete scheduled season is 0.30, computed over every scheduled shift
including the quarantined ones.
"""
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

    result = _result(bundle)
    assert result is not None
    assert result["state"] == "no_issue_detected_within_coverage"
    assert bundle["findings"] == []


def test_source_identifier_noise_cannot_create_denominator_evidence(
    schema_root: Path,
    tmp_path: Path,
) -> None:
    repository = tmp_path / "project"
    report = """# Retention inventory

The final analysis reports counts of records that passed consent and quality checks. No rate,
spacing, recurrence, distance, transition, or normalized interval estimate is selected.
"""
    writer = """from pathlib import Path

retained_observed_subset_exposure_only = 12
complete_declared_domain_exposure = 20
exposure_denominator = retained_observed_subset_exposure_only
Path('report.md').write_text('generated\\n', encoding='utf-8')
"""
    _write_project(repository, report, writer=writer)
    lock_path = _contract(repository, tmp_path / "contract", schema_root)

    output = tmp_path / "audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report="report.md",
        method_contract_lock=lock_path,
    )

    assert _result(bundle) is None
    assert bundle["findings"] == []


def test_independently_written_development_style_is_recognized_without_case_metadata(
    schema_root: Path,
    tmp_path: Path,
) -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "evaluation"
        / "development-cases"
        / "complete-domain-exposure-independent-style-1"
    )
    manifest = json.loads((source / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["development_only"] is True
    assert manifest["metric_eligible"] is False
    assert manifest["public_benchmark"] is False

    repository = tmp_path / "project"
    shutil.copytree(source, repository)
    lock_path = _contract(repository, tmp_path / "contract", schema_root)

    output = tmp_path / "audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report=manifest["selected_report_path"],
        method_contract_lock=lock_path,
    )

    result = _result(bundle)
    assert result is not None
    assert result["state"] == "evaluation_finding_candidate"
    assert result["extensions"]["x-production-finding-permitted"] is False
    assert bundle["findings"] == []
    assert bundle["executions"] == []


def test_development_control_has_one_replayable_selected_result_and_static_producer() -> None:
    case_root = (
        Path(__file__).resolve().parents[1]
        / "evaluation"
        / "development-controls"
        / "complete-domain-exposure-v1.1.0"
        / "case"
    )
    derivation = freeze_independent_selected_result_derivation(
        case_root,
        {
            "case_id": "case:0123456789abcdefabcd",
            "validator_identity": {
                "validator_id": "actor:development-validator",
                "provider": "development-only",
                "execution_context_id": "context:development-only",
                "identity_evidence_digest": "sha256:" + "d" * 64,
            },
            "profile_id": PYTHON_STATIC_MARKED_REPORT_PROFILE,
            "selected_report_path": "report.md",
            "derived_at": "2026-08-04T20:00:00Z",
        },
        frozen_at="2026-08-04T20:01:00Z",
    )

    assert derivation["derivation_status"] == "one_selected_result_rederived"
    assert len(derivation["candidate_bindings"]) == 1
    assert derivation["project_code_executed"] is False
    assert revalidate_independent_selected_result_derivation(derivation, case_root) == derivation


COMPUTING_WRITER = """import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/data.csv').open()))
planned = len(rows)
retained = [row for row in rows if row['kept'] == 'yes']
events = sum(1 for row in retained if row['event'] == 'yes')
rate = events / len(retained)
report = f'planned {planned} events {events} rate {rate}\\n'
Path('report.md').write_text(report, encoding='utf-8')
"""

COMPUTING_CSV = (
    "plot,kept,event\n"
    + "\n".join(
        f"p{i},{'yes' if i <= 8 else 'no'},{'yes' if i <= 6 else 'no'}" for i in range(1, 11)
    )
    + "\n"
)


def _write_computing_project(repository: Path, report: str) -> None:
    _write_project(repository, report, writer=COMPUTING_WRITER)
    (repository / "inputs").mkdir()
    (repository / "inputs/data.csv").write_text(COMPUTING_CSV, encoding="utf-8")


def test_bare_integer_rate_is_recognized_from_source_dataflow(
    schema_root: Path,
    tmp_path: Path,
) -> None:
    """A rate stated without a decimal point or percent marker cannot be
    reconciled on the report plane, but the workflow's own division names the
    retained subset as its denominator, so the conflict still fires."""

    repository = tmp_path / "project"
    report = """# Plot survey

Planned plots: 10. Retained after screening: 8. Removed: 2. Plots with the event: 6.

The event rate for the complete planned set of plots is 75.
"""
    _write_computing_project(repository, report)
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
    assert result is not None
    assert result["state"] == "evaluation_finding_candidate"
    ledger = next(
        item
        for item in result["evidence"]
        if item["evidence_id"] == "evidence:analysis-method-ledger"
    )
    assert ledger["observed_value"]["observed"] == CONFLICTING_OPERAND
    cited_paths = {
        ref.get("path") for item in result["evidence"] for ref in item.get("source_refs", [])
    }
    assert "analysis.py" in cited_paths
    assert bundle["findings"] == []
    assert bundle["executions"] == []


def test_report_arithmetic_and_source_dataflow_disagreement_is_ambiguous(
    schema_root: Path,
    tmp_path: Path,
) -> None:
    """The report's numbers reconcile as a complete-domain rate while the
    code divides by the screened subset; the planes disagree, so the check
    abstains instead of picking a side."""

    repository = tmp_path / "project"
    report = """# Plot survey

Planned plots: 10. Retained after screening: 8. Removed: 2. Plots with the event: 6.

The event rate for the complete planned set of plots is 0.60.
"""
    _write_computing_project(repository, report)
    lock_path = _contract(repository, tmp_path / "contract", schema_root)

    output = tmp_path / "audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report="report.md",
        method_contract_lock=lock_path,
    )

    assert _module(output / "semantic.lock.json")["state"] == "ambiguous"
    assert _result(bundle) is None
    assert bundle["findings"] == []
