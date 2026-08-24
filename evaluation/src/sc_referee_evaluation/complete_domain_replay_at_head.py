"""Non-blind replay of the sealed complete-domain exam against current adapter bytes.

This evaluation-only harness does not reopen the examination and does not read model transports.
It copies the exact staged project tree retained for each sealed detector run, reruns the same
method-contract -> static audit -> semantic-lock replay path used by ``step_detector``, and compares
the outcome fields retained in the sealed detector ledger.  Project-authored code is never
executed.  The resulting record is drift-ruling evidence, not a fresh qualification attempt.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.method_contract_run import run_method_contract
from sc_referee.scientific_checks.profiles import default_scientific_check_registry
from sc_referee.scientific_requirement_contract import (
    SCIENTIFIC_REQUIREMENT_PROFILE_ID,
    SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
)
from sc_referee.storage.atomic import atomic_write_bytes


class CompleteDomainHeadReplayError(ValueError):
    """The sealed evidence, live identity, or deterministic replay is inconsistent."""


SEALED_EXAM_RELATIVE = Path(
    "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/"
    "heldout-v207-seven-case"
)
REPLAY_OUTPUT_RELATIVE = SEALED_EXAM_RELATIVE.with_name("heldout-v207-seven-case-replay-at-head")
REPLAY_ARTIFACT_NAME = "REPLAY_AT_HEAD.json"
REPLAY_PURPOSE = "drift-ruling evidence, not a fresh examination"
CHECK_ID = "check:complete-domain-exposure-denominator"
DETECTOR_ID = "detector:bounded-analysis-method-conflict"
SCHEMA_RELATIVE = Path("reference/schemas-v0.21.0")

_SEALED_DIGESTS = {
    "heldout_opening": "sha256:0daf0982bc0e15bb8aada0c6e0be143bea0f439494858f7dc3ffd53f0a3d08ec",
    "authoring_protocol": "sha256:6554e88100ee986e8b5f6357ae9fe07d53723654c4aa415df1810ecc56d19c06",
    "intake_ledger": "sha256:80a430261db7e3c4243c6d0413881f775044590ddda82bc787e2561c668dca0f",
    "review_ledger": "sha256:a75179780e1032804f29f73bce0bd81c98004e83fedbb7f0e355727ef9f99e77",
    "scientific_label_ledger": (
        "sha256:913c907ea9f39ecfb1291fb6c183e757180b32b4867f8632a9b91813fca50010"
    ),
    "detector_run_ledger": (
        "sha256:679cbc06c089ac8bccffbc89619bb4fdb67a722dcae0a47edcce205f87578048"
    ),
}
_SEALED_RECORDS = {
    "heldout_opening": (Path("HELDOUT_OPENING.json"), "semantic_digest"),
    "authoring_protocol": (Path("authoring/AUTHORING_PROTOCOL.json"), "protocol_digest"),
    "intake_ledger": (Path("authoring/INTAKE_LEDGER.json"), "ledger_digest"),
    "review_ledger": (Path("review/REVIEW_LEDGER.json"), "ledger_digest"),
    "scientific_label_ledger": (Path("SCIENTIFIC_LABEL_LEDGER.json"), "ledger_digest"),
    "detector_run_ledger": (Path("detector-run/DETECTOR_RUN_LEDGER.json"), "ledger_digest"),
}
_AGREEMENT_FIELDS = (
    "contract_candidate_id",
    "method_contract_applied",
    "finding_candidate_count",
    "detector_positive",
    "comparison_outcome",
    "production_findings",
    "project_code_executions",
    "replay_equal",
)
_HEAD_AUDIT_PATHS = ("src", "reference/schemas-v0.21.0")


def build_complete_domain_replay_at_head(
    project_root: Path,
    run_root: Path,
    *,
    recorded_at: str,
) -> dict[str, Any]:
    """Run the seven sealed projects with current code and return one digest-bound record."""

    project_root = project_root.resolve()
    if run_root.exists() or run_root.is_symlink():
        raise CompleteDomainHeadReplayError("The replay working directory must not already exist.")
    run_root.mkdir(parents=True)
    sealed_root = project_root / SEALED_EXAM_RELATIVE
    sealed_records = _load_sealed_records(sealed_root)
    detector_ledger = sealed_records["detector_run_ledger"]
    authoring_protocol = sealed_records["authoring_protocol"]
    entries = detector_ledger.get("entries")
    if not isinstance(entries, list) or len(entries) != 7:
        raise CompleteDomainHeadReplayError("The sealed detector ledger must contain seven cases.")
    by_case = _unique_case_entries(entries)
    if set(by_case) != set(authoring_protocol.get("case_role_assignments", {})):
        raise CompleteDomainHeadReplayError(
            "The sealed detector and authoring protocols bind different case sets."
        )

    head_identity = _current_head_identity(project_root, authoring_protocol)
    rows = [
        _replay_case(
            project_root=project_root,
            sealed_root=sealed_root,
            run_root=run_root,
            case_id=case_id,
            sealed=by_case[case_id],
        )
        for case_id in sorted(by_case)
    ]
    agreement_count = sum(item["agreement"] is True for item in rows)
    record: dict[str, Any] = {
        "artifact_kind": "complete_domain_sealed_case_replay_at_head",
        "artifact_version": "1.0.0",
        "purpose": REPLAY_PURPOSE,
        "non_blind": True,
        "fresh_examination_claimed": False,
        "qualification_authority": "none_drift_ruling_evidence_only",
        "project_authored_code_executed": False,
        "sealed_exam_relative": SEALED_EXAM_RELATIVE.as_posix(),
        "sealed_record_digests": dict(_SEALED_DIGESTS),
        "sealed_detector_tuple": authoring_protocol["detector_tuple"],
        "sealed_detector_tuple_digest": authoring_protocol["detector_tuple_digest"],
        "head_identity": head_identity,
        "comparison_contract": {
            "agreement_fields": list(_AGREEMENT_FIELDS),
            "excluded_fields": {
                "audit_lock_digest": (
                    "Expected to change when current adapter and shared-core identities replace "
                    "the exam-time implementation bytes."
                )
            },
            "label_source": "sealed_detector_run_ledger_only",
        },
        "entries": rows,
        "case_count": len(rows),
        "agreement_count": agreement_count,
        "all_cases_agree": agreement_count == len(rows),
        "current_production_finding_count": sum(
            int(item["current_outcome"]["production_findings"]) for item in rows
        ),
        "current_project_code_execution_count": sum(
            int(item["current_outcome"]["project_code_executions"]) for item in rows
        ),
        "recorded_at": recorded_at,
        "replay_harness_implementation_digest": sha256_digest(Path(__file__).read_bytes()),
    }
    record["semantic_digest"] = semantic_digest(record)
    return record


def write_complete_domain_replay_at_head(
    project_root: Path,
    output_root: Path,
    *,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    """Run once into a temporary workspace and retain only the canonical replay record."""

    if output_root.exists() or output_root.is_symlink():
        raise CompleteDomainHeadReplayError("The replay evidence output already exists.")
    timestamp = recorded_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    workspace = output_root.parent / f".{output_root.name}.working"
    if workspace.exists() or workspace.is_symlink():
        raise CompleteDomainHeadReplayError("The replay evidence working path already exists.")
    try:
        record = build_complete_domain_replay_at_head(
            project_root, workspace, recorded_at=timestamp
        )
        output_root.mkdir(parents=True)
        atomic_write_bytes(
            output_root / REPLAY_ARTIFACT_NAME,
            (canonical_json(record) + "\n").encode("utf-8"),
        )
    finally:
        if workspace.is_dir() and not workspace.is_symlink():
            shutil.rmtree(workspace)
    return record


def load_complete_domain_replay_at_head(path: Path) -> dict[str, Any]:
    """Load one canonical artifact and reverify its self-digest and closed purpose fields."""

    record = _load_json(path, "replay-at-HEAD artifact")
    supplied = record.get("semantic_digest")
    payload = {key: value for key, value in record.items() if key != "semantic_digest"}
    if supplied != semantic_digest(payload):
        raise CompleteDomainHeadReplayError("The replay-at-HEAD artifact digest does not replay.")
    if (
        record.get("artifact_kind") != "complete_domain_sealed_case_replay_at_head"
        or record.get("artifact_version") != "1.0.0"
        or record.get("purpose") != REPLAY_PURPOSE
        or record.get("non_blind") is not True
        or record.get("fresh_examination_claimed") is not False
        or record.get("qualification_authority") != "none_drift_ruling_evidence_only"
        or record.get("project_authored_code_executed") is not False
    ):
        raise CompleteDomainHeadReplayError("The replay-at-HEAD purpose boundary drifted.")
    return record


def _replay_case(
    *,
    project_root: Path,
    sealed_root: Path,
    run_root: Path,
    case_id: str,
    sealed: Mapping[str, Any],
) -> dict[str, Any]:
    slug = case_id.removeprefix("case:")
    if not slug or case_id != f"case:{slug}":
        raise CompleteDomainHeadReplayError(f"Malformed sealed case id {case_id!r}.")
    source = sealed_root / "detector-run" / "runs" / slug / "project"
    source_digest = _project_tree_digest(source)
    case_root = run_root / slug
    repository = case_root / "project"
    shutil.copytree(source, repository)
    if _project_tree_digest(repository) != source_digest:
        raise CompleteDomainHeadReplayError(f"The staged bytes drifted for {case_id}.")

    method_contract_applied = sealed.get("method_contract_applied") is True
    candidate_id = sealed.get("contract_candidate_id")
    contract_lock: Path | None = None
    if method_contract_applied:
        if not isinstance(candidate_id, str) or not candidate_id:
            raise CompleteDomainHeadReplayError(f"The sealed contract is malformed for {case_id}.")
        contract = run_method_contract(
            repository,
            "task.md",
            case_root / "contract",
            project_root / SCHEMA_RELATIVE,
            profile={
                "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
                "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
                "check_id": CHECK_ID,
                "candidate_id": candidate_id,
                "semantic_role_authority": {},
            },
            actor_id=(
                "scientist:lean-pipeline-complete-domain-exposure-denominator-v2.0.7-heldout"
            ),
        )
        if contract.get("findings"):
            raise CompleteDomainHeadReplayError(
                f"The method-contract replay emitted a Finding for {case_id}."
            )
        contract_lock = case_root / "contract" / "semantic.lock.json"
    elif candidate_id is not None:
        raise CompleteDomainHeadReplayError(
            f"A contract-free sealed case carries a candidate for {case_id}."
        )

    bundle = run_audit(
        repository,
        case_root / "audit",
        project_root / SCHEMA_RELATIVE,
        report="results/report.md",
        method_contract_lock=contract_lock,
        material_inputs=(),
    )
    replayed = replay(
        case_root / "audit" / "semantic.lock.json",
        case_root / "replay",
        project_root / SCHEMA_RELATIVE,
    )
    replay_equal = replayed.get("detector_results") == bundle.get("detector_results")
    if not replay_equal:
        raise CompleteDomainHeadReplayError(f"The current audit does not replay for {case_id}.")
    target_results = [
        item
        for item in bundle.get("detector_results", [])
        if isinstance(item, Mapping) and item.get("detector_id") == DETECTOR_ID
    ]
    fired = [item for item in target_results if item.get("state") == "evaluation_finding_candidate"]
    detector_positive = bool(fired)
    expected_positive = sealed.get("frozen_label_status") == "positive_demonstrated"
    comparison_outcome = (
        "true_positive"
        if detector_positive and expected_positive
        else "false_accusation"
        if detector_positive and not expected_positive
        else "missed_error"
        if not detector_positive and expected_positive
        else "true_negative"
    )
    current = {
        "contract_candidate_id": candidate_id,
        "method_contract_applied": method_contract_applied,
        "finding_candidate_count": len(fired),
        "detector_positive": detector_positive,
        "comparison_outcome": comparison_outcome,
        "production_findings": len(bundle.get("findings", [])),
        "project_code_executions": len(bundle.get("executions", [])),
        "replay_equal": replay_equal,
    }
    sealed_outcome = {field: sealed.get(field) for field in _AGREEMENT_FIELDS}
    mismatch_fields = [
        field for field in _AGREEMENT_FIELDS if current[field] != sealed_outcome[field]
    ]
    return {
        "case_id": case_id,
        "case_role": sealed.get("case_role"),
        "source_project_relative": source.relative_to(project_root).as_posix(),
        "source_project_digest": source_digest,
        "sealed_outcome": sealed_outcome,
        "current_outcome": current,
        "current_target_detector_states": sorted(str(item.get("state")) for item in target_results),
        "mismatch_fields": mismatch_fields,
        "agreement": not mismatch_fields,
    }


def _current_head_identity(
    project_root: Path, authoring_protocol: Mapping[str, Any]
) -> dict[str, Any]:
    _require_audit_paths_at_head(project_root)
    registry = default_scientific_check_registry()
    modules = [
        module for module in registry.canonical_modules if module.manifest.check_id == CHECK_ID
    ]
    if len(modules) != 1 or len(modules[0].adapter_manifests) != 1:
        raise CompleteDomainHeadReplayError("The live complete-domain adapter is not a singleton.")
    module = modules[0]
    adapter = module.adapter_manifests[0]
    detector_tuple = authoring_protocol.get("detector_tuple")
    if not isinstance(detector_tuple, Mapping):
        raise CompleteDomainHeadReplayError("The sealed detector tuple is malformed.")
    sealed_adapters = detector_tuple.get("adapters")
    if not isinstance(sealed_adapters, list) or len(sealed_adapters) != 1:
        raise CompleteDomainHeadReplayError("The sealed adapter identity is not a singleton.")
    sealed_adapter = sealed_adapters[0]
    if (
        not isinstance(sealed_adapter, Mapping)
        or sealed_adapter.get("adapter_id") != adapter.adapter_id
    ):
        raise CompleteDomainHeadReplayError("The sealed and live adapter ids differ.")
    registry_path = (
        project_root / "src/sc_referee/resources/scientific-check-manifests-v1/registry.json"
    )
    return {
        "git_head_commit": _git_output(project_root, "rev-parse", "HEAD"),
        "tracked_audit_paths_match_head": True,
        "registry_content_digest": sha256_digest(registry_path.read_bytes()),
        "check_id": module.manifest.check_id,
        "check_version": module.manifest.check_version,
        "check_manifest_digest": module.manifest.manifest_digest,
        "adapter": {
            "adapter_id": adapter.adapter_id,
            "adapter_version": adapter.adapter_version,
            "implementation_digest": adapter.implementation_digest,
            "manifest_digest": adapter.manifest_digest,
            "recognition_grammar_digest": adapter.recognition_grammar_digest,
        },
        "drift_from_sealed_adapter": {
            "implementation_digest_changed": (
                adapter.implementation_digest != sealed_adapter.get("implementation_digest")
            ),
            "manifest_digest_changed": adapter.manifest_digest
            != sealed_adapter.get("manifest_digest"),
            "recognition_grammar_digest_changed": (
                adapter.recognition_grammar_digest
                != sealed_adapter.get("recognition_grammar_digest")
            ),
        },
    }


def _require_audit_paths_at_head(project_root: Path) -> None:
    completed = subprocess.run(
        ["git", "-C", str(project_root), "diff", "--quiet", "HEAD", "--", *_HEAD_AUDIT_PATHS],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise CompleteDomainHeadReplayError(
            "Tracked audit implementation or schema bytes differ from HEAD."
        )


def _git_output(project_root: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(project_root), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise CompleteDomainHeadReplayError(
            "The replay could not resolve the HEAD revision."
        ) from error
    value = completed.stdout.strip()
    if not value:
        raise CompleteDomainHeadReplayError("The replay resolved an empty HEAD revision.")
    return value


def _load_sealed_records(sealed_root: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for name, (relative, digest_field) in _SEALED_RECORDS.items():
        record = _load_json(sealed_root / relative, name.replace("_", " "))
        supplied = record.get(digest_field)
        payload = {key: value for key, value in record.items() if key != digest_field}
        if supplied != _SEALED_DIGESTS[name] or semantic_digest(payload) != _SEALED_DIGESTS[name]:
            raise CompleteDomainHeadReplayError(f"The sealed {name} digest drifted.")
        records[name] = record
    return records


def _unique_case_entries(entries: list[Any]) -> dict[str, Mapping[str, Any]]:
    by_case: dict[str, Mapping[str, Any]] = {}
    for item in entries:
        if not isinstance(item, Mapping):
            raise CompleteDomainHeadReplayError("A sealed detector entry is malformed.")
        case_id = item.get("case_id")
        if not isinstance(case_id, str) or case_id in by_case:
            raise CompleteDomainHeadReplayError("Sealed case ids are missing or duplicated.")
        by_case[case_id] = item
    return by_case


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise CompleteDomainHeadReplayError(f"The {label} must be one regular file.")
    payload = path.read_bytes()
    try:
        value = json.loads(payload.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CompleteDomainHeadReplayError(f"The {label} is not strict UTF-8 JSON.") from error
    if not isinstance(value, dict):
        raise CompleteDomainHeadReplayError(f"The {label} must be one JSON object.")
    if payload != (canonical_json(value) + "\n").encode("utf-8"):
        raise CompleteDomainHeadReplayError(f"The {label} is not canonical JSON.")
    return value


def _project_tree_digest(root: Path) -> str:
    if root.is_symlink() or not root.is_dir():
        raise CompleteDomainHeadReplayError("A sealed case project is not one regular directory.")
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise CompleteDomainHeadReplayError("A sealed case project contains a symlink.")
        if path.is_dir():
            continue
        if not path.is_file():
            raise CompleteDomainHeadReplayError("A sealed case project contains a special file.")
        payload = path.read_bytes()
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "content_digest": sha256_digest(payload),
                "byte_count": len(payload),
            }
        )
    if not files:
        raise CompleteDomainHeadReplayError("A sealed case project is empty.")
    return str(semantic_digest({"files": files}))
