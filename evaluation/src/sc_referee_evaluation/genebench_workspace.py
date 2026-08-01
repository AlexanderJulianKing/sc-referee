from __future__ import annotations

import json
import shutil
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.records.normalization import (
    normalized_json_bytes,
    write_normalized_json,
    write_normalized_json_once,
)
from sc_referee.records.observed import build_file_records
from sc_referee.snapshot.repository import AssetIdentityPolicy, capture_repository
from sc_referee.storage.atomic import atomic_write_bytes
from sc_referee_evaluation.corpus import (
    GENEBENCH_PUBLIC_SOURCE_URI,
    CorpusPreflightError,
    preflight_genebench_public_package,
)
from sc_referee_evaluation.workspace import BlindWorkspaceError, build_blind_workspace


class GeneBenchWorkspaceError(ValueError):
    """One GeneBench case cannot enter the answer-isolated workspace boundary."""


_PREPARATION_VERSION = "0.1.0"
_PREFLIGHT_VERSION = "0.2.0"


def prepare_genebench_public_case(
    package_root: Path,
    preflight: dict[str, Any],
    eval_id: str,
    output_root: Path,
    *,
    created_at: str,
) -> dict[str, Any]:
    """Build one exact visible workspace and keep every answer-side artifact outside it."""

    if output_root.exists() or output_root.is_symlink():
        raise GeneBenchWorkspaceError(f"Case preparation output already exists: {output_root}")
    package = package_root.resolve()
    destination = output_root.resolve(strict=False)
    if destination.is_relative_to(package):
        raise GeneBenchWorkspaceError("Case preparation output must remain outside the package.")

    try:
        verified = verify_genebench_public_preflight(package, preflight)
    except CorpusPreflightError as error:
        raise GeneBenchWorkspaceError(str(error)) from error
    problem = _problem(verified, eval_id)
    config_path = str(problem["eval_config"]["path"])
    config_payload = _read_exact(
        package,
        config_path,
        str(problem["eval_config"]["content_digest"]),
    )
    config = _load_object(config_payload, config_path)
    task = config.get("task")
    ground_truth = config.get("ground_truth")
    if not isinstance(task, str) or not task or not isinstance(ground_truth, dict):
        raise GeneBenchWorkspaceError(
            "Verified case config no longer contains task and ground truth."
        )
    if sha256_digest(task) != problem["task"]["content_digest"]:
        raise GeneBenchWorkspaceError("Case task does not match the verified preflight projection.")

    run_id = stable_id(
        "evaluation-case-run",
        str(verified["preflight_id"]),
        eval_id,
        created_at,
    )
    output_root.parent.mkdir(parents=True, exist_ok=True)
    output_root.mkdir()
    try:
        runner_source = output_root / "runner-source"
        runner_source.mkdir()
        atomic_write_bytes(runner_source / "task.md", task.encode("utf-8"))

        selected_files = [{"path": "task.md", "role": "scientific_task"}]
        for visible in problem["visible_inputs"]:
            source_path = str(visible["source_path"])
            workspace_path = str(visible["workspace_path"])
            payload = _read_exact(package, source_path, str(visible["content_digest"]))
            if len(payload) != visible["byte_size"]:
                raise GeneBenchWorkspaceError(
                    f"Visible input {source_path!r} changed size after preflight."
                )
            atomic_write_bytes(runner_source / workspace_path, payload)
            selected_files.append({"path": workspace_path, "role": "staged_data"})

        report_path = f"problems/{eval_id}/report_public.pdf"
        report_payload = _read_regular(package, report_path)
        grader_payload = _read_regular(package, "reference_grader.py")
        ground_truth_payload = normalized_json_bytes(ground_truth)
        hidden_payloads = {
            ".answer-side/eval_config.json": config_payload,
            ".answer-side/ground_truth.json": ground_truth_payload,
            ".answer-side/reference_grader.py": grader_payload,
            ".answer-side/report_public.pdf": report_payload,
        }
        for path_value, payload in hidden_payloads.items():
            atomic_write_bytes(runner_source / path_value, payload)

        full_digest_budget = sum(
            path.stat().st_size for path in runner_source.rglob("*") if path.is_file()
        )
        captured = capture_repository(
            runner_source,
            output_root / "snapshot",
            run_id,
            captured_at=created_at,
            identity_policy=AssetIdentityPolicy(
                full_digest_byte_budget=full_digest_budget,
                sampled_fingerprint_byte_budget=0,
            ),
        )
        file_records = build_file_records(
            captured.file_records,
            captured.asset_identity_records,
            str(captured.snapshot_record["snapshot_id"]),
            created_at,
        )
        write_normalized_json(output_root / "snapshot.json", captured.snapshot_record)
        atomic_write_bytes(
            output_root / "file-records.jsonl",
            b"".join(normalized_json_bytes(record) for record in file_records),
        )
        atomic_write_bytes(
            output_root / "asset-identities.jsonl",
            b"".join(normalized_json_bytes(record) for record in captured.asset_identity_records),
        )

        workspace_manifest = build_blind_workspace(
            captured.materialized_root,
            output_root / "workspace",
            output_root / "workspace-manifest.json",
            selected_files,
            snapshot=captured.snapshot_record,
            file_records=file_records,
            asset_identities=captured.asset_identity_records,
            created_at=created_at,
            forbidden_source_paths=set(hidden_payloads),
            forbidden_digests={sha256_digest(payload) for payload in hidden_payloads.values()},
            forbidden_markers={canonical_json(ground_truth)},
        )
        workspace_paths = sorted(str(item["path"]) for item in workspace_manifest["files"])
        expected_workspace_paths = sorted(str(item["path"]) for item in selected_files)
        if workspace_paths != expected_workspace_paths:
            raise GeneBenchWorkspaceError("Blind workspace does not equal the preflight allowlist.")

        record: dict[str, Any] = {
            "case_preparation_version": _PREPARATION_VERSION,
            "record_type": "evaluation_genebench_case_preparation",
            "preparation_id": stable_id(
                "genebench-case-preparation",
                str(verified["preflight_id"]),
                eval_id,
                str(workspace_manifest["manifest_digest"]),
            ),
            "created_at": created_at,
            "source": {
                "uri": GENEBENCH_PUBLIC_SOURCE_URI,
                "revision": verified["source"]["revision"],
                "preflight_id": verified["preflight_id"],
                "preflight_digest": verified["preflight_digest"],
            },
            "case": {
                "eval_id": eval_id,
                "eval_uuid": problem["eval_uuid"],
                "title": problem["title"],
                "domain": problem["domain"],
            },
            "corpus_partition": "public_development",
            "held_out_eligible": False,
            "promotion_evidence_eligible": False,
            "workspace": {
                "relative_path": "workspace",
                "workspace_id": workspace_manifest["workspace_id"],
                "manifest_digest": workspace_manifest["manifest_digest"],
                "visible_paths": workspace_paths,
                "agent_workspace_eligible": True,
            },
            "runner_side": {
                "relative_paths": sorted(hidden_payloads),
                "source_snapshot_id": captured.snapshot_record["snapshot_id"],
                "source_snapshot_digest": semantic_digest(captured.snapshot_record),
                "agent_workspace_eligible": False,
            },
            "ground_truth_disclosed_to_agent_workspace": False,
            "reference_report_copied_to_agent_workspace": False,
            "reference_grader_copied_to_agent_workspace": False,
            "project_code_executed": False,
            "model_invoked": False,
            "limitations": [
                "The public task and answers may have been present in model training data.",
                "Filesystem or process isolation must expose only the workspace directory to an external agent.",
                "Preparation does not establish reviewer identity, scientific correctness, or detector qualification.",
            ],
        }
        record["preparation_digest"] = semantic_digest(record)
        write_normalized_json_once(output_root / "case-preparation.json", record)
        return record
    except (BlindWorkspaceError, CorpusPreflightError, OSError, ValueError, KeyError) as error:
        shutil.rmtree(output_root, ignore_errors=True)
        if isinstance(error, GeneBenchWorkspaceError):
            raise
        raise GeneBenchWorkspaceError(str(error)) from error


def verify_genebench_public_preflight(
    package_root: Path, preflight: dict[str, Any]
) -> dict[str, Any]:
    """Revalidate one canonical public-development preflight against current package bytes."""

    payload = dict(preflight)
    supplied_digest = payload.pop("preflight_digest", None)
    if supplied_digest != semantic_digest(payload):
        raise GeneBenchWorkspaceError("GeneBench preflight digest is invalid.")
    source = preflight.get("source")
    if (
        preflight.get("corpus_preflight_version") != _PREFLIGHT_VERSION
        or preflight.get("record_type") != "evaluation_corpus_preflight"
        or not isinstance(source, dict)
        or source.get("uri") != GENEBENCH_PUBLIC_SOURCE_URI
        or preflight.get("run_admission_status") != "admitted_for_public_development_preparation"
        or preflight.get("corpus_partition_ceiling") != "public_development"
        or preflight.get("held_out_eligible") is not False
        or preflight.get("promotion_evidence_eligible") is not False
        or preflight.get("answer_side_artifact") is not True
        or preflight.get("agent_workspace_eligible") is not False
        or preflight.get("project_code_executed") is not False
        or preflight.get("model_invoked") is not False
    ):
        raise GeneBenchWorkspaceError("GeneBench preflight is not eligible for case preparation.")
    current = preflight_genebench_public_package(
        package_root,
        source_revision=str(source.get("revision", "")),
        expected_manifest_digest=str(source.get("manifest_digest", "")),
        expected_checksums_digest=str(source.get("checksums_digest", "")),
    )
    if current != preflight:
        raise GeneBenchWorkspaceError("GeneBench package no longer matches its supplied preflight.")
    return current


def _problem(preflight: dict[str, Any], eval_id: str) -> dict[str, Any]:
    matches = [item for item in preflight.get("problems", []) if item.get("eval_id") == eval_id]
    if len(matches) != 1:
        raise GeneBenchWorkspaceError(f"Unknown or ambiguous GeneBench eval_id {eval_id!r}.")
    return dict(matches[0])


def _read_exact(root: Path, path_value: str, expected_digest: str) -> bytes:
    payload = _read_regular(root, path_value)
    if sha256_digest(payload) != expected_digest:
        raise GeneBenchWorkspaceError(f"Package path {path_value!r} changed after preflight.")
    return payload


def _read_regular(root: Path, path_value: str) -> bytes:
    relative = PurePosixPath(path_value)
    if (
        not path_value
        or relative.is_absolute()
        or relative.as_posix() != path_value
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise GeneBenchWorkspaceError(f"Unsafe package path {path_value!r}.")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise GeneBenchWorkspaceError(f"Package path {path_value!r} crosses a symlink.")
    if not current.is_file():
        raise GeneBenchWorkspaceError(f"Package path {path_value!r} is not a regular file.")
    return current.read_bytes()


def _load_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GeneBenchWorkspaceError(f"Case metadata {label!r} is not valid JSON.") from error
    if not isinstance(value, dict):
        raise GeneBenchWorkspaceError(f"Case metadata {label!r} is not a JSON object.")
    return value


__all__ = [
    "GeneBenchWorkspaceError",
    "prepare_genebench_public_case",
    "verify_genebench_public_preflight",
]
