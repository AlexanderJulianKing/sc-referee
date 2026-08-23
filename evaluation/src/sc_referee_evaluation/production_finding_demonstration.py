"""Build and verify the first controller-published production Finding demonstrations.

The builder invokes the public method-contract, audit, and replay paths.  It never executes the
demonstration projects and exposes no timestamp override: every recorded time comes back from a
controller-produced record.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from uuid import uuid4

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition.authority_lock import (
    AUTHORITY_LIMITATIONS,
    DECLARED_EXECUTION_ROOT,
    LOCK_KIND,
    approval_projection,
    lock_projection,
)
from sc_referee.detectors.method_conflict_grant_pins import GRANT_PINS, GrantPin
from sc_referee.method_contract_run import run_method_contract
from sc_referee.reporting.policy import validate_report_contract
from sc_referee.scientific_requirement_contract import (
    LEGACY_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
    SCIENTIFIC_REQUIREMENT_PROFILE_ID,
    SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
)
from sc_referee.snapshot.repository import capture_repository

DEMONSTRATION_VERSION = "1.0.0"
COMPLETE_BINDING_ID = "method-conflict-binding:complete-domain-exposure-denominator-v1"
DEPENDENCE_BINDING_ID = (
    "method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1"
)
COMPLETE_CHECK_ID = "check:complete-domain-exposure-denominator"
DEPENDENCE_CHECK_ID = "check:authorized-independent-unit-entry-into-row-independent-procedure"
COMPLETE_CANDIDATE_ID = "complete-declared-domain-exposure"
DEPENDENCE_CANDIDATE_ID = "one-analyzed-row-per-authorized-independent-unit"
_METHOD_DETECTOR_ID = "detector:bounded-analysis-method-conflict"

_COMPLETE_TASK = "Apply the scientist-authorized complete-domain denominator requirement.\n"
_COMPLETE_ERROR_REPORT = """# Acoustic recurrence summary

The deployment scheduled 120 listening windows for the season. The screening step kept 90
windows with usable recordings and removed 30 windows. Detections occurred in 36 of the kept
windows. The primary detection rate for the full scheduled deployment is 0.40.
"""
_COMPLETE_CONTROL_REPORT = """# Acoustic recurrence summary

The deployment scheduled 120 listening windows for the season. The screening step kept 90
windows with usable recordings and removed 30 windows. Detections occurred in 36 windows. The
primary detection rate for the complete scheduled deployment is 0.30, computed over all 120
scheduled windows including the removed windows.
"""
_COMPLETE_WRITER = (
    'from pathlib import Path\n\nPath("report.md").write_text("generated\\n", encoding="utf-8")\n'
)

_DEPENDENCE_TASK = (
    "For this analysis, k1 identifies the authorized independent unit in the first collection.\n"
    "Use one analyzed row per authorized independent unit before applying the row-independent "
    "procedure.\n"
)
_DEPENDENCE_WORKFLOW = """import csv
from pathlib import Path

import scipy.stats as st

rows = list(csv.DictReader(Path("inputs/data.csv").read_text(encoding="utf-8").splitlines()))
staged = rows
left = [float(row["a"]) for row in staged]
right = [float(row["b"]) for row in staged]
result = st.ttest_ind(left, right)
Path("results/report.md").write_text(f"[selected-result] {result}\\n", encoding="utf-8")
"""
_DEPENDENCE_ERROR_CSV = """k1,k2,tag,a,b
u01,v03,t01,1.0,2.0
u01,v04,t02,1.5,2.25
u02,v05,t03,2.0,4.0
u02,v06,t04,2.5,4.25
"""
_DEPENDENCE_CONTROL_CSV = """k1,k2,tag,a,b
u01,v03,t01,1.0,2.0
u02,v05,t03,2.0,4.0
"""
_DEPENDENCE_ERROR_RESULT = (
    "TtestResult(statistic=np.float64(-2.0665401605809937), "
    "pvalue=np.float64(0.08429003959156793), df=np.float64(6.0))"
)
_DEPENDENCE_CONTROL_RESULT = (
    "TtestResult(statistic=np.float64(-1.3416407864998738), "
    "pvalue=np.float64(0.3117527983883147), df=np.float64(2.0))"
)
_DEPENDENCE_REQUIREMENTS = b"numpy==2.2.6\nscipy==1.14.0\n"
_DEPENDENCE_CASE_IDS = {
    "error": "case:7f3a0d27c81e4f709c11",
    "control": "case:b406195a88d743a5a122",
}
_DEPENDENCE_ACTOR_ID = "scientist:production-demonstration-dependence-owner"

_AUTHORITY_REFS = {
    "complete-domain": {
        "sealed_exam_opening": (
            "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-"
            "lane-v2/heldout-v207-seven-case/HELDOUT_OPENING.json"
        ),
        "sealed_exam_ledger": (
            "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-"
            "lane-v2/heldout-v207-seven-case/detector-run/DETECTOR_RUN_LEDGER.json"
        ),
        "promotion_adr": ("docs/implementation/ADR-0071-COMPLETE-DOMAIN-ENVELOPE-PROMOTION.md"),
        "install_adr": ("docs/implementation/ADR-0075-ROUND-2-PROMOTION-RECORD-REDERIVATION.md"),
    },
    "dependence": {
        "sealed_exam_opening": (
            "evaluation/qualification/authorized-independent-unit-entry-into-row-independent-"
            "procedure-v1.1.0-direct-lane/heldout-seven-case/opening/"
            "DEPENDENCE_HELDOUT_OPENING.json"
        ),
        "sealed_exam_ledger": (
            "evaluation/qualification/authorized-independent-unit-entry-into-row-independent-"
            "procedure-v1.1.0-direct-lane/heldout-seven-case/detector-run/"
            "DETECTOR_RUN_LEDGER.json"
        ),
        "promotion_adr": "docs/implementation/ADR-0073-DEPENDENCE-ENVELOPE-PROMOTION.md",
        "install_adr": ("docs/implementation/ADR-0075-ROUND-2-PROMOTION-RECORD-REDERIVATION.md"),
    },
}


class ProductionFindingDemonstrationError(ValueError):
    """The demonstration could not be built or no longer replays exactly."""


def build_production_finding_demonstration(
    output: Path,
    *,
    schema_root: Path,
) -> dict[str, Any]:
    """Run both promoted paths directly under their final evidence directory.

    Audit provenance records the resolved project root.  Building at the final path is therefore
    part of record truthfulness; an atomic staging-directory rename would leave a stale root in
    the committed AuditBundle.  The create-only output rule preserves any partial failure for
    inspection instead of rewriting it.
    """

    if output.exists() or output.is_symlink():
        raise ProductionFindingDemonstrationError("demonstration output must be absent")
    output.mkdir(parents=True)
    complete = _build_complete_domain(output / "complete-domain", schema_root)
    dependence = _build_dependence(output / "dependence", schema_root)
    record: dict[str, Any] = {
        "artifact_kind": "production_finding_demonstration_v1",
        "artifact_version": DEMONSTRATION_VERSION,
        "execution_policy": {
            "project_authored_code_executed": False,
            "production_run_audit_path_used": True,
            "timestamp_override_available": False,
        },
        "demonstrations": [complete, dependence],
    }
    record["record_digest"] = semantic_digest(record)
    _write_json(output / "DEMONSTRATION_RECORD.json", record)
    (output / "README.md").write_text(_readme(record), encoding="utf-8")
    _write_inner_manifest(output)
    verify_production_finding_demonstration(output, schema_root=schema_root)
    return record


def verify_production_finding_demonstration(
    root: Path,
    *,
    schema_root: Path,
) -> dict[str, Any]:
    """Reverify the committed record, inner manifest, policy, and audit/replay equality."""

    _verify_inner_manifest(root)
    record = _load_object(root / "DEMONSTRATION_RECORD.json")
    supplied_digest = record.pop("record_digest", None)
    if supplied_digest != semantic_digest(record):
        raise ProductionFindingDemonstrationError("demonstration record digest does not replay")
    record["record_digest"] = supplied_digest
    if record.get("artifact_kind") != "production_finding_demonstration_v1":
        raise ProductionFindingDemonstrationError("demonstration record kind is invalid")
    demonstrations = record.get("demonstrations")
    if not isinstance(demonstrations, list) or [item.get("key") for item in demonstrations] != [
        "complete-domain",
        "dependence",
    ]:
        raise ProductionFindingDemonstrationError("demonstration inventory is not exact")
    for demonstration in demonstrations:
        _verify_demonstration_entry(root, demonstration, schema_root)
    return record


def _build_complete_domain(root: Path, schema_root: Path) -> dict[str, Any]:
    pin = GRANT_PINS[COMPLETE_BINDING_ID]
    error = _run_complete_case(root / "error", schema_root, _COMPLETE_ERROR_REPORT, expected=1)
    control = _run_complete_case(
        root / "control", schema_root, _COMPLETE_CONTROL_REPORT, expected=0
    )
    return _demonstration_entry("complete-domain", pin, error, control)


def _run_complete_case(
    root: Path,
    schema_root: Path,
    report_text: str,
    *,
    expected: int,
) -> dict[str, Any]:
    project = root / "project"
    project.mkdir(parents=True)
    (project / "task.md").write_text(_COMPLETE_TASK, encoding="utf-8")
    (project / "analysis.py").write_text(_COMPLETE_WRITER, encoding="utf-8")
    (project / "report.md").write_text(report_text, encoding="utf-8")
    contract_root = root / "contract"
    contract = run_method_contract(
        project,
        "task.md",
        contract_root,
        schema_root,
        profile={
            "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            "check_id": COMPLETE_CHECK_ID,
            "candidate_id": COMPLETE_CANDIDATE_ID,
            "semantic_role_authority": {},
        },
        actor_id="scientist:production-demonstration-complete-owner",
    )
    if contract["findings"]:
        raise ProductionFindingDemonstrationError("method-contract run emitted a Finding")
    bundle = run_audit(
        project,
        root / "audit",
        schema_root,
        report="report.md",
        method_contract_lock=contract_root / "semantic.lock.json",
    )
    replayed = replay(root / "audit/semantic.lock.json", root / "replay", schema_root)
    return _case_record(root, bundle, replayed, expected=expected, binding_id=COMPLETE_BINDING_ID)


def _build_dependence(root: Path, schema_root: Path) -> dict[str, Any]:
    pin = GRANT_PINS[DEPENDENCE_BINDING_ID]
    error = _run_dependence_case(
        root / "error",
        schema_root,
        csv_text=_DEPENDENCE_ERROR_CSV,
        result_text=_DEPENDENCE_ERROR_RESULT,
        case_id=_DEPENDENCE_CASE_IDS["error"],
        expected=1,
    )
    control = _run_dependence_case(
        root / "control",
        schema_root,
        csv_text=_DEPENDENCE_CONTROL_CSV,
        result_text=_DEPENDENCE_CONTROL_RESULT,
        case_id=_DEPENDENCE_CASE_IDS["control"],
        expected=0,
    )
    return _demonstration_entry("dependence", pin, error, control)


def _run_dependence_case(
    root: Path,
    schema_root: Path,
    *,
    csv_text: str,
    result_text: str,
    case_id: str,
    expected: int,
) -> dict[str, Any]:
    project = root / "project"
    (project / "inputs").mkdir(parents=True)
    (project / "workflow").mkdir()
    (project / "results").mkdir()
    (project / "task.md").write_text(_DEPENDENCE_TASK, encoding="utf-8")
    (project / "inputs/data.csv").write_text(csv_text, encoding="utf-8")
    (project / "requirements.txt").write_bytes(_DEPENDENCE_REQUIREMENTS)
    (project / "workflow/analysis.py").write_text(_DEPENDENCE_WORKFLOW, encoding="utf-8")
    (project / "results/report.md").write_text(
        f"[selected-result] {result_text}\n", encoding="utf-8"
    )
    contract_root = root / "contract"
    contract = run_method_contract(
        project,
        "task.md",
        contract_root,
        schema_root,
        profile={
            "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "profile_version": LEGACY_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            "check_id": DEPENDENCE_CHECK_ID,
            "candidate_id": DEPENDENCE_CANDIDATE_ID,
        },
        actor_id=_DEPENDENCE_ACTOR_ID,
    )
    if contract["findings"]:
        raise ProductionFindingDemonstrationError("method-contract run emitted a Finding")
    with tempfile.TemporaryDirectory(prefix="dependence-snapshot-preview-") as raw:
        preview = capture_repository(
            project,
            Path(raw) / "snapshot",
            f"audit:{uuid4().hex}",
            preferred_full_digest_paths=("results/report.md",),
            material_full_digest_paths=("inputs/data.csv", "requirements.txt"),
        )
    lock = _dependence_lock(
        case_id=case_id,
        snapshot_digest=str(preview.snapshot_record["snapshot_digest"]),
        intake_recorded_at=str(preview.snapshot_record["captured_at"]),
        input_digest=sha256_digest((project / "inputs/data.csv").read_bytes()),
    )
    lock_path = root / "dependence-authorization-lock.json"
    _write_json(lock_path, lock)
    bundle = run_audit(
        project,
        root / "audit",
        schema_root,
        report="results/report.md",
        material_inputs=("inputs/data.csv", "requirements.txt"),
        method_contract_lock=contract_root / "semantic.lock.json",
        dependence_authorization_lock=lock_path,
        dependence_authorization_case_id=case_id,
    )
    replayed = replay(root / "audit/semantic.lock.json", root / "replay", schema_root)
    return _case_record(root, bundle, replayed, expected=expected, binding_id=DEPENDENCE_BINDING_ID)


def _dependence_lock(
    *, case_id: str, snapshot_digest: str, intake_recorded_at: str, input_digest: str
) -> dict[str, Any]:
    slug = case_id.removeprefix("case:")
    analysis_id = f"analysis:{slug}"
    procedure_id = f"procedure:{slug}"
    result_id = f"result:{slug}"
    value: dict[str, Any] = {
        "lock_kind": LOCK_KIND,
        "case_id": case_id,
        "snapshot_digest": snapshot_digest,
        "intake_recorded_at": intake_recorded_at,
        "declared_execution_root": DECLARED_EXECUTION_ROOT,
        "records": [
            {"record_type": "analysis", "record_id": analysis_id, "path": "workflow/analysis.py"},
            {
                "record_type": "procedure",
                "record_id": procedure_id,
                "resolved_callable": "scipy.stats.ttest_ind",
            },
            {"record_type": "result", "record_id": result_id, "path": "results/report.md"},
            {
                "record_type": "human_method_authorization",
                "record_id": f"authorization:{slug}",
                "actor_id": _DEPENDENCE_ACTOR_ID,
                "authority_state": "authorized",
                "analysis_target_ref": {"record_type": "analysis", "record_id": analysis_id},
                "procedure_ref": {"record_type": "procedure", "record_id": procedure_id},
                "independent_unit_definition_id": "unit-definition:k1-first-collection-item",
                "authorized_key_columns": ["k1"],
                "input_path": "inputs/data.csv",
                "input_content_digest": input_digest,
            },
        ],
        "approval": {
            "actor_kind": "human",
            "actor_id": _DEPENDENCE_ACTOR_ID,
            "approved_projection_digest": "sha256:" + "0" * 64,
            "approved_at": intake_recorded_at,
        },
        "authority_limitations": list(AUTHORITY_LIMITATIONS),
        "lock_digest": "sha256:" + "0" * 64,
    }
    value["approval"]["approved_projection_digest"] = semantic_digest(approval_projection(value))
    value["lock_digest"] = semantic_digest(lock_projection(value))
    return value


def _case_record(
    root: Path,
    bundle: dict[str, Any],
    replayed: dict[str, Any],
    *,
    expected: int,
    binding_id: str,
) -> dict[str, Any]:
    validate_report_contract(bundle)
    validate_report_contract(replayed)
    for key in ("detector_results", "findings", "coverage_records"):
        if bundle[key] != replayed[key]:
            raise ProductionFindingDemonstrationError(f"{key} did not replay")
    if len(bundle["findings"]) != expected or bundle["executions"]:
        raise ProductionFindingDemonstrationError("demonstration Finding/execution count is wrong")
    promoted = [
        result
        for result in bundle["detector_results"]
        if result.get("detector_id") == _METHOD_DETECTOR_ID
        and result.get("state") == "finding_candidate"
        and result.get("extensions", {}).get("x-method-conflict-binding-id") == binding_id
    ]
    if len(promoted) != expected:
        raise ProductionFindingDemonstrationError("promoted result count is wrong")
    if promoted and (
        promoted[0].get("detector_maturity") != "validated"
        or promoted[0].get("extensions", {}).get("x-production-finding-permitted") is not True
    ):
        raise ProductionFindingDemonstrationError("promoted result lacks production authority")
    audit_bundle = root / "audit/audit.bundle.json"
    audit_lock = root / "audit/semantic.lock.json"
    replay_bundle = root / "replay/audit.bundle.json"
    finding_text = None
    finding_id = None
    if expected:
        finding = bundle["findings"][0]
        finding_id = finding["finding_id"]
        finding_text = {
            "title": finding["title"],
            "summary": finding["summary"],
            "severity": finding["severity"],
            "publication_materiality": finding["publication_materiality"],
            "next_action": finding["next_action"],
        }
    return {
        "audit_bundle": audit_bundle.relative_to(root).as_posix(),
        "audit_bundle_digest": sha256_digest(audit_bundle.read_bytes()),
        "semantic_lock": audit_lock.relative_to(root).as_posix(),
        "semantic_lock_digest": sha256_digest(audit_lock.read_bytes()),
        "replay_bundle": replay_bundle.relative_to(root).as_posix(),
        "replay_bundle_digest": sha256_digest(replay_bundle.read_bytes()),
        "recorded_at": bundle["audit_runs"][0]["created_at"],
        "audit_run_id": bundle["audit_runs"][0]["audit_run_id"],
        "finding_count": expected,
        "finding_id": finding_id,
        "finding_text": finding_text,
        "project_file_digests": {
            path.relative_to(root / "project").as_posix(): sha256_digest(path.read_bytes())
            for path in sorted((root / "project").rglob("*"))
            if path.is_file()
        },
        "project_execution_count": len(bundle["executions"]),
        "report_policy_validated": True,
        "replay_verified": True,
    }


def _demonstration_entry(
    key: str,
    pin: GrantPin,
    error: dict[str, Any],
    control: dict[str, Any],
) -> dict[str, Any]:
    return {
        "key": key,
        "binding_id": pin.binding_id,
        "authority_chain": {
            **_AUTHORITY_REFS[key],
            "qualification_id": pin.qualification_id,
            "qualification_digest": pin.qualification_digest,
            "metric_set_id": pin.metric_set_id,
            "metric_set_digest": pin.metric_set_digest,
            "installed_pin_binding_digest": pin.binding_digest,
            "installed_pin_detector_manifest_digest": pin.detector_manifest_digest,
        },
        "error_run": error,
        "control_twin": control,
    }


def _verify_demonstration_entry(root: Path, entry: object, schema_root: Path) -> None:
    if not isinstance(entry, dict):
        raise ProductionFindingDemonstrationError("demonstration entry is malformed")
    key = entry.get("key")
    binding_id = entry.get("binding_id")
    if key not in {"complete-domain", "dependence"} or binding_id not in GRANT_PINS:
        raise ProductionFindingDemonstrationError("demonstration binding is not installed")
    pin = GRANT_PINS[str(binding_id)]
    authority = entry.get("authority_chain")
    if not isinstance(authority, dict) or authority != {
        **_AUTHORITY_REFS[str(key)],
        "qualification_id": pin.qualification_id,
        "qualification_digest": pin.qualification_digest,
        "metric_set_id": pin.metric_set_id,
        "metric_set_digest": pin.metric_set_digest,
        "installed_pin_binding_digest": pin.binding_digest,
        "installed_pin_detector_manifest_digest": pin.detector_manifest_digest,
    }:
        raise ProductionFindingDemonstrationError("authority chain drifted")
    detector_root = root / str(key)
    _verify_case(detector_root / "error", entry.get("error_run"), binding_id, expected=1)
    _verify_case(detector_root / "control", entry.get("control_twin"), binding_id, expected=0)
    for case in ("error", "control"):
        with tempfile.TemporaryDirectory(prefix="production-finding-replay-") as raw:
            replayed = replay(
                detector_root / case / "audit/semantic.lock.json",
                Path(raw) / "replay",
                schema_root,
            )
        committed = _load_object(detector_root / case / "replay/audit.bundle.json")
        for field in ("detector_results", "findings", "coverage_records"):
            if replayed[field] != committed[field]:
                raise ProductionFindingDemonstrationError(
                    f"committed {key} {case} replay drifted for {field}"
                )


def _verify_case(
    root: Path,
    case: object,
    binding_id: object,
    *,
    expected: int,
    validate_live_report_policy: bool = True,
) -> None:
    if not isinstance(case, dict):
        raise ProductionFindingDemonstrationError("demonstration case is malformed")
    audit_path = root / str(case.get("audit_bundle"))
    lock_path = root / str(case.get("semantic_lock"))
    replay_path = root / str(case.get("replay_bundle"))
    if (
        sha256_digest(audit_path.read_bytes()) != case.get("audit_bundle_digest")
        or sha256_digest(lock_path.read_bytes()) != case.get("semantic_lock_digest")
        or sha256_digest(replay_path.read_bytes()) != case.get("replay_bundle_digest")
    ):
        raise ProductionFindingDemonstrationError("demonstration case digest drifted")
    bundle = _load_object(audit_path)
    replayed = _load_object(replay_path)
    if validate_live_report_policy:
        validate_report_contract(bundle)
        validate_report_contract(replayed)
    if (
        len(bundle["findings"]) != expected
        or bundle["findings"] != replayed["findings"]
        or bundle["detector_results"] != replayed["detector_results"]
        or bundle["executions"]
        or case.get("project_execution_count") != 0
        or case.get("report_policy_validated") is not True
        or case.get("replay_verified") is not True
        or case.get("recorded_at") != bundle["audit_runs"][0]["created_at"]
        or case.get("audit_run_id") != bundle["audit_runs"][0]["audit_run_id"]
    ):
        raise ProductionFindingDemonstrationError("demonstration case claims do not replay")
    for path, digest in case.get("project_file_digests", {}).items():
        if sha256_digest((root / "project" / path).read_bytes()) != digest:
            raise ProductionFindingDemonstrationError("demonstration project bytes drifted")
    promoted = [
        result
        for result in bundle["detector_results"]
        if result.get("state") == "finding_candidate"
        and result.get("extensions", {}).get("x-method-conflict-binding-id") == binding_id
    ]
    if len(promoted) != expected:
        raise ProductionFindingDemonstrationError("demonstration promotion count drifted")
    if expected:
        finding = bundle["findings"][0]
        expected_text = {
            "title": finding["title"],
            "summary": finding["summary"],
            "severity": finding["severity"],
            "publication_materiality": finding["publication_materiality"],
            "next_action": finding["next_action"],
        }
        if (
            case.get("finding_id") != finding["finding_id"]
            or case.get("finding_text") != expected_text
        ):
            raise ProductionFindingDemonstrationError("published Finding text drifted")


def _readme(record: Mapping[str, Any]) -> str:
    sections = []
    for entry in record["demonstrations"]:
        error = entry["error_run"]
        text = error["finding_text"]
        authority = entry["authority_chain"]
        sections.append(
            f"""## {entry["key"]}

Recorded at `{error["recorded_at"]}` by AuditRun `{error["audit_run_id"]}`.

### Finding text as published

**{text["title"]}**

{text["summary"]}

**Severity:** {text["severity"]["level"]} — {text["severity"]["rationale"]}

**Publication materiality:** {text["publication_materiality"]["level"]} — {text["publication_materiality"]["rationale"]}

**Next action:** {text["next_action"]}

### Authority chain

1. Sealed examination: [`{authority["sealed_exam_opening"]}`](../../{authority["sealed_exam_opening"]}) and [`{authority["sealed_exam_ledger"]}`](../../{authority["sealed_exam_ledger"]}).
2. Promotion decision: [`{authority["promotion_adr"]}`](../../{authority["promotion_adr"]}).
3. Installed qualification: `{authority["qualification_id"]}` at `{authority["qualification_digest"]}` with metric set `{authority["metric_set_id"]}` at `{authority["metric_set_digest"]}`.
4. Installed external pin: binding `{entry["binding_id"]}` at `{authority["installed_pin_binding_digest"]}`, detector manifest `{authority["installed_pin_detector_manifest_digest"]}`.
5. Controller run: [`{entry["key"]}/error/audit/audit.bundle.json`]({entry["key"]}/error/audit/audit.bundle.json), replayed at [`{entry["key"]}/error/replay/audit.bundle.json`]({entry["key"]}/error/replay/audit.bundle.json).

The matched control twin is committed at [`{entry["key"]}/control/`]({entry["key"]}/control/) and produced zero Findings through the same contract, audit, policy, and replay path.
"""
        )
    joined_sections = "\n".join(sections)
    return f"""# First production Finding demonstrations

This directory records the first production-authorized Findings published by `sc-referee` for
the two exact binding-scoped grants installed under ADR-0075. Both positive workflows and both
matched control twins were passed through the real `run_audit` controller path. The controller
did not execute project-authored code. Each committed replay reproduces the original detector
results, Findings, and coverage record.

The timestamps below are **recorded, not declared**: the builder accepts no timestamp argument and
copies each value from the controller-created AuditRun. `DEMONSTRATION_RECORD.json` binds the
project bytes, audit bundle, semantic lock, replay bundle, installed grant identities, and exact
published wording. This directory's `MANIFEST.sha256` closes every committed file except itself.

{joined_sections}
## Scope

These are canonical demonstrations of two already-qualified, exact envelopes. They are not new
qualification cases, do not enlarge either recognition grammar, and make no claim about code
execution, numerical causality, bias direction, or scientific correctness outside each Finding's
stated scope.
"""


def _write_inner_manifest(root: Path) -> None:
    rows = [
        f"{sha256_digest(path.read_bytes()).removeprefix('sha256:')}  "
        f"{path.relative_to(root).as_posix()}"
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "MANIFEST.sha256"
    ]
    (root / "MANIFEST.sha256").write_text("\n".join(rows) + "\n", encoding="utf-8")


def _verify_inner_manifest(root: Path) -> None:
    manifest = root / "MANIFEST.sha256"
    if not manifest.is_file() or manifest.is_symlink():
        raise ProductionFindingDemonstrationError("demonstration manifest is unavailable")
    expected = {
        path.relative_to(root).as_posix(): sha256_digest(path.read_bytes()).removeprefix("sha256:")
        for path in root.rglob("*")
        if path.is_file() and path != manifest
    }
    observed: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, separator, path = line.partition("  ")
        if not separator or path in observed:
            raise ProductionFindingDemonstrationError("demonstration manifest is malformed")
        observed[path] = digest
    if observed != dict(sorted(expected.items())):
        raise ProductionFindingDemonstrationError("demonstration manifest does not replay")


def _load_object(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProductionFindingDemonstrationError(f"invalid JSON artifact: {path}") from error
    if not isinstance(value, dict) or payload != (canonical_json(value) + "\n").encode("utf-8"):
        raise ProductionFindingDemonstrationError(f"noncanonical JSON artifact: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")
