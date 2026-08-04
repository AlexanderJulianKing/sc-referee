from __future__ import annotations

import argparse
import base64
import importlib.metadata
import importlib.resources
import importlib.util
import json
import os
import stat
import sys
import sysconfig
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee_evaluation.prospective_selected_result_verifier import (
    PYTHON_STATIC_MARKED_REPORT_PROFILE,
    freeze_independent_selected_result_derivation,
    revalidate_independent_selected_result_derivation,
)

TARGET_WORKER_VERSION = "1.1.0-development"
TARGET_AUTHORIZATION_VERSION = "1.0.0"
TARGET_RUNTIME_MANIFEST_VERSION = "1.0.0"
TARGET_AUTHORIZATION_SCHEMA_RESOURCE = "target-authorization-schema.json"
TARGET_AUTHORIZATION_SCHEMA_CONTENT_DIGEST = (
    "sha256:82ff25bb509eeec2cd261e33264115b9e30556b40ff1de1310e02f898ccfebd6"
)
TARGET_AUTHORIZATION_SCHEMA_DIGEST = (
    "sha256:0c0f26e8dace6c291f8e3cdac6269c4a88223ea9dbcea7c8a644c4082687dc3d"
)
MAX_TARGET_CASES = 24
MAX_TARGET_AUTHORIZATION_BYTES = 1024 * 1024
MAX_TARGET_IDENTITY_TEXT_CHARS = 512
MAX_TARGET_RELATIVE_PATH_UTF8_BYTES = 4096
MAX_RUNTIME_DISTRIBUTIONS = 3
MAX_RUNTIME_DISTRIBUTION_FILES = 4096
MAX_RUNTIME_FILE_BYTES = 64 * 1024 * 1024
MAX_RUNTIME_TOTAL_BYTES = 512 * 1024 * 1024
MAX_RUNTIME_PATH_UTF8_BYTES = 16 * 1024
_RUNTIME_DISTRIBUTIONS = (
    "cryptography",
    "sc-referee",
    "sc-referee-evaluation",
)
_RUNTIME_MODULES = (
    ("cryptography", "cryptography"),
    ("sc_referee.core.ids", "sc-referee"),
    (
        "sc_referee_evaluation.prospective_selected_result_verifier",
        "sc-referee-evaluation",
    ),
    (
        "sc_referee_evaluation.selected_result_qualification_target_worker",
        "sc-referee-evaluation",
    ),
)
TARGET_AUTHORIZATION_FIELDS = frozenset(
    {
        "artifact_kind",
        "authorization_version",
        "block",
        "provider_slot",
        "assignment_digest",
        "runner_freeze_digest",
        "release_gate_digest",
        "target_identity",
        "cases",
        "case_count",
        "case_replacement_permitted",
        "qualification_authority",
        "target_authorization_digest",
    }
)
TARGET_AUTHORIZATION_CASE_FIELDS = frozenset(
    {
        "case_id",
        "assignment_position",
        "snapshot_path",
        "snapshot_tree_digest",
        "target_packet",
        "derived_at",
        "frozen_at",
    }
)
TARGET_AUTHORIZATION_PACKET_FIELDS = frozenset({"case_id", "profile_id", "selected_report_path"})
TARGET_AUTHORIZATION_IDENTITY_FIELDS = frozenset(
    {"validator_id", "provider", "execution_context_id", "identity_evidence_digest"}
)
TARGET_AUTHORIZATION_FORBIDDEN_FIELD_NAME_FRAGMENTS = (
    "answer",
    "attestation",
    "binding",
    "certificate",
    "construction",
    "expected",
    "gold",
    "ground_truth",
    "issue",
    "label",
    "oracle",
    "outcome",
    "positive",
    "reason",
    "reconciliation",
    "semantic",
    "state",
    "author_declaration",
    "u_cell",
)


class SelectedResultTargetWorkerError(ValueError):
    """Raised when an isolated target-worker input or output cannot be replayed."""


def target_authorization_field_projection() -> dict[str, list[str]]:
    """Return the exact recursive field projection bound by the worker schema."""

    return {
        "authorization": sorted(TARGET_AUTHORIZATION_FIELDS),
        "case": sorted(TARGET_AUTHORIZATION_CASE_FIELDS),
        "identity": sorted(TARGET_AUTHORIZATION_IDENTITY_FIELDS),
        "packet": sorted(TARGET_AUTHORIZATION_PACKET_FIELDS),
    }


TARGET_AUTHORIZATION_FIELD_PROJECTION_DIGEST = semantic_digest(
    target_authorization_field_projection()
)


def load_target_authorization_schema() -> dict[str, Any]:
    """Load and replay the exact installed target-authorization schema bytes."""

    resource_root = importlib.resources.files(
        "sc_referee_evaluation.qualification_resources.selected_result_v1_1"
    )
    payload = resource_root.joinpath(TARGET_AUTHORIZATION_SCHEMA_RESOURCE).read_bytes()
    if sha256_digest(payload) != TARGET_AUTHORIZATION_SCHEMA_CONTENT_DIGEST:
        raise SelectedResultTargetWorkerError(
            "Installed target-authorization schema bytes have drifted."
        )
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SelectedResultTargetWorkerError(
            "Installed target-authorization schema is not valid JSON."
        ) from error
    if not isinstance(value, dict) or semantic_digest(value) != TARGET_AUTHORIZATION_SCHEMA_DIGEST:
        raise SelectedResultTargetWorkerError(
            "Installed target-authorization schema digest does not replay."
        )
    _validate_schema_field_projection(value)
    return deepcopy(value)


def freeze_target_runtime_manifest(*, output_path: Path) -> dict[str, Any]:
    """Emit answer-free evidence for the exact installed target-worker runtime."""

    if output_path.exists() or output_path.is_symlink():
        raise FileExistsError(f"Target runtime manifest already exists: {output_path}")
    if len(_RUNTIME_DISTRIBUTIONS) != MAX_RUNTIME_DISTRIBUTIONS:
        raise SelectedResultTargetWorkerError("Target runtime distribution inventory has drifted.")
    distributions = [_runtime_distribution_record(name) for name in sorted(_RUNTIME_DISTRIBUTIONS)]
    total_bytes = sum(int(item["total_file_bytes"]) for item in distributions)
    if total_bytes > MAX_RUNTIME_TOTAL_BYTES:
        raise SelectedResultTargetWorkerError(
            "Target runtime distribution inventory exceeds its total-byte ceiling."
        )
    installed_paths = {
        str(file_record["installed_path"]): str(distribution["requested_name"])
        for distribution in distributions
        for file_record in distribution["files"]
    }
    module_files = [
        _runtime_module_record(module_name, distribution_name)
        for module_name, distribution_name in _RUNTIME_MODULES
    ]
    for module in module_files:
        if installed_paths.get(str(module["installed_path"])) != module["distribution_name"]:
            raise SelectedResultTargetWorkerError(
                "Target runtime module is absent from its installed distribution inventory."
            )

    executable = Path(getattr(sys, "_base_executable", sys.executable)).resolve(strict=True)
    executable_record = _stable_runtime_file_record(
        executable,
        recorded_path=Path(sys.executable).as_posix(),
    )
    runtime: dict[str, Any] = {
        "implementation": sys.implementation.name,
        "implementation_version": [
            sys.implementation.version.major,
            sys.implementation.version.minor,
            sys.implementation.version.micro,
            sys.implementation.version.releaselevel,
            sys.implementation.version.serial,
        ],
        "python_version": sys.version,
        "version_info": [
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
            sys.version_info.releaselevel,
            sys.version_info.serial,
        ],
        "hexversion": sys.hexversion,
        "cache_tag": sys.implementation.cache_tag,
        "byteorder": sys.byteorder,
        "platform": sys.platform,
        "abi_flags": getattr(sys, "abiflags", ""),
        "soabi": sysconfig.get_config_var("SOABI"),
        "multiarch": sysconfig.get_config_var("MULTIARCH"),
        "prefix": Path(sys.prefix).resolve().as_posix(),
        "base_prefix": Path(sys.base_prefix).resolve().as_posix(),
        "exec_prefix": Path(sys.exec_prefix).resolve().as_posix(),
        "base_exec_prefix": Path(sys.base_exec_prefix).resolve().as_posix(),
        "executable": executable_record,
    }
    manifest: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_target_runtime_manifest",
        "runtime_manifest_version": TARGET_RUNTIME_MANIFEST_VERSION,
        "target_worker_version": TARGET_WORKER_VERSION,
        "python_runtime": runtime,
        "module_files": module_files,
        "distributions": distributions,
        "distribution_count": len(distributions),
        "distribution_file_count": sum(int(item["file_count"]) for item in distributions),
        "distribution_total_file_bytes": total_bytes,
        "input_projection": "installed_runtime_only",
        "project_code_executed": False,
        "qualification_authority": "none_target_runtime_evidence_only",
    }
    manifest["target_runtime_manifest_digest"] = semantic_digest(manifest)
    write_normalized_json_once(output_path, manifest)
    return manifest


def _runtime_distribution_record(requested_name: str) -> dict[str, Any]:
    try:
        distribution = importlib.metadata.distribution(requested_name)
    except importlib.metadata.PackageNotFoundError as error:
        raise SelectedResultTargetWorkerError(
            "Required target runtime distribution is not installed."
        ) from error
    metadata_name = distribution.metadata["Name"]
    if (
        not isinstance(metadata_name, str)
        or metadata_name.casefold().replace("_", "-") != requested_name
    ):
        raise SelectedResultTargetWorkerError("Target runtime distribution identity has drifted.")
    raw_files = distribution.files
    if raw_files is None or not 1 <= len(raw_files) <= MAX_RUNTIME_DISTRIBUTION_FILES:
        raise SelectedResultTargetWorkerError(
            "Target runtime distribution has no finite installed-file inventory."
        )
    ordered_files = sorted(raw_files, key=lambda item: str(item))
    if len({str(item) for item in ordered_files}) != len(ordered_files):
        raise SelectedResultTargetWorkerError(
            "Target runtime distribution file inventory is not unique."
        )
    files: list[dict[str, Any]] = []
    total_bytes = 0
    for item in ordered_files:
        recorded_path = _runtime_path_text(str(item), "distribution record path")
        installed = Path(str(distribution.locate_file(item)))
        try:
            observed = installed.lstat()
        except OSError as error:
            raise SelectedResultTargetWorkerError(
                "Target runtime distribution file is absent."
            ) from error
        if stat.S_ISLNK(observed.st_mode):
            raise SelectedResultTargetWorkerError(
                "Target runtime distribution file cannot be a symbolic link."
            )
        record = _stable_runtime_file_record(installed, recorded_path=recorded_path)
        recorded_size = item.size
        if recorded_size is not None and (
            not isinstance(recorded_size, int)
            or isinstance(recorded_size, bool)
            or recorded_size != record["byte_length"]
        ):
            raise SelectedResultTargetWorkerError(
                "Target runtime distribution file size disagrees with installed metadata."
            )
        recorded_hash: str | None = None
        if item.hash is not None:
            if item.hash.mode != "sha256":
                raise SelectedResultTargetWorkerError(
                    "Target runtime distribution uses an unsupported recorded hash."
                )
            try:
                decoded = base64.urlsafe_b64decode(item.hash.value + "===")
            except (ValueError, TypeError) as error:
                raise SelectedResultTargetWorkerError(
                    "Target runtime distribution recorded hash is malformed."
                ) from error
            recorded_hash = f"sha256:{decoded.hex()}"
            if recorded_hash != record["content_digest"]:
                raise SelectedResultTargetWorkerError(
                    "Target runtime distribution file disagrees with installed metadata."
                )
        record["recorded_sha256"] = recorded_hash
        record["recorded_size"] = recorded_size
        total_bytes += int(record["byte_length"])
        if total_bytes > MAX_RUNTIME_TOTAL_BYTES:
            raise SelectedResultTargetWorkerError(
                "Target runtime distribution exceeds its total-byte ceiling."
            )
        files.append(record)
    result: dict[str, Any] = {
        "requested_name": requested_name,
        "metadata_name": metadata_name,
        "version": _runtime_path_text(distribution.version, "distribution version"),
        "files": files,
        "file_count": len(files),
        "total_file_bytes": total_bytes,
        "file_inventory_digest": semantic_digest(files),
    }
    result["distribution_digest"] = semantic_digest(result)
    return result


def _runtime_module_record(module_name: str, distribution_name: str) -> dict[str, Any]:
    specification = importlib.util.find_spec(module_name)
    if specification is None or specification.origin is None:
        raise SelectedResultTargetWorkerError("Required target runtime module is not installed.")
    record = _stable_runtime_file_record(
        Path(specification.origin),
        recorded_path=module_name,
    )
    return {
        "module_name": module_name,
        "distribution_name": distribution_name,
        **record,
    }


def _stable_runtime_file_record(path: Path, *, recorded_path: str) -> dict[str, Any]:
    recorded = _runtime_path_text(recorded_path, "runtime recorded path")
    lexical = path.absolute()
    try:
        before = lexical.lstat()
    except OSError as error:
        raise SelectedResultTargetWorkerError("Target runtime file is absent.") from error
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise SelectedResultTargetWorkerError(
            "Target runtime evidence accepts only real regular files."
        )
    resolved = lexical.resolve(strict=True)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(resolved, flags)
    except OSError as error:
        raise SelectedResultTargetWorkerError(
            "Target runtime file cannot be opened without following a final link."
        ) from error
    payload = bytearray()
    try:
        opened = os.fstat(descriptor)
        if _runtime_stat_fingerprint(opened) != _runtime_stat_fingerprint(before):
            raise SelectedResultTargetWorkerError(
                "Target runtime file changed before its descriptor was opened."
            )
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            if len(payload) > MAX_RUNTIME_FILE_BYTES - len(chunk):
                raise SelectedResultTargetWorkerError(
                    "Target runtime file exceeds its finite byte ceiling."
                )
            payload.extend(chunk)
        after = os.fstat(descriptor)
        if len(payload) != opened.st_size or _runtime_stat_fingerprint(
            opened
        ) != _runtime_stat_fingerprint(after):
            raise SelectedResultTargetWorkerError(
                "Target runtime file changed while it was being read."
            )
    finally:
        os.close(descriptor)
    installed_path = _runtime_path_text(resolved.as_posix(), "runtime installed path")
    return {
        "recorded_path": recorded,
        "installed_path": installed_path,
        "content_digest": sha256_digest(bytes(payload)),
        "byte_length": len(payload),
        "mode": stat.S_IMODE(before.st_mode),
        "executable": bool(before.st_mode & 0o111),
    }


def _runtime_stat_fingerprint(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
        value.st_mode,
    )


def _runtime_path_text(value: Any, label: str) -> str:
    text = _text(value, label)
    if len(text.encode("utf-8")) > MAX_RUNTIME_PATH_UTF8_BYTES:
        raise SelectedResultTargetWorkerError(f"{label} exceeds its finite byte ceiling.")
    return text


def validate_target_authorization(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the complete answer-blind input accepted by the target worker."""

    load_target_authorization_schema()
    authorization = deepcopy(dict(value))
    _reject_forbidden_authorization_field_names(authorization)
    supplied_digest = authorization.pop("target_authorization_digest", None)
    if supplied_digest != semantic_digest(authorization):
        raise SelectedResultTargetWorkerError("Target authorization self-digest does not replay.")
    authorization["target_authorization_digest"] = supplied_digest
    _exact_keys(
        authorization,
        set(TARGET_AUTHORIZATION_FIELDS),
        "target authorization",
    )
    if (
        authorization["artifact_kind"] != "selected_result_verifier_target_authorization"
        or authorization["authorization_version"] != TARGET_AUTHORIZATION_VERSION
        or authorization["block"] not in {"pilot", "held_out"}
        or authorization["provider_slot"] not in {"provider-family-1", "provider-family-2"}
        or authorization["case_replacement_permitted"] is not False
        or authorization["qualification_authority"] != "none_target_release_authorization_only"
    ):
        raise SelectedResultTargetWorkerError("Target authorization identity has drifted.")
    _digest(authorization["assignment_digest"], "assignment_digest")
    _digest(authorization["runner_freeze_digest"], "runner_freeze_digest")
    _digest(authorization["release_gate_digest"], "release_gate_digest")
    authorization["target_identity"] = _target_identity(authorization["target_identity"])

    count = _integer(authorization["case_count"], "case_count")
    raw_cases = authorization["cases"]
    if (
        not isinstance(raw_cases, list)
        or not 1 <= count <= MAX_TARGET_CASES
        or len(raw_cases) != count
    ):
        raise SelectedResultTargetWorkerError(
            "Target authorization has an invalid finite case inventory."
        )
    cases = [_target_case(item) for item in raw_cases]
    positions = [int(item["assignment_position"]) for item in cases]
    case_ids = [str(item["case_id"]) for item in cases]
    snapshot_paths = [str(item["snapshot_path"]) for item in cases]
    if (
        cases != sorted(cases, key=lambda item: int(item["assignment_position"]))
        or len(set(positions)) != count
        or len(set(case_ids)) != count
        or len(set(snapshot_paths)) != count
    ):
        raise SelectedResultTargetWorkerError(
            "Target authorization case inventory is not canonical and unique."
        )
    authorization["cases"] = cases
    return authorization


def run_target_worker(
    *,
    authorization_path: Path,
    snapshot_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Run the selected-result target from its isolated, answer-blind projection."""

    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"Target-worker output already exists: {output_root}")
    authorization = _load_canonical_authorization(authorization_path)
    _real_directory(snapshot_root, "Target snapshot root")
    case_roots = [
        _safe_snapshot_path(snapshot_root, item["snapshot_path"]) for item in authorization["cases"]
    ]

    output_root.mkdir(parents=True)
    records_root = output_root / "target-records"
    records_root.mkdir()
    inventory: list[dict[str, Any]] = []
    completed_at: str | None = None
    for item, case_root in zip(authorization["cases"], case_roots, strict=True):
        record_path = records_root / f"{str(item['case_id']).removeprefix('case:')}.json"
        record_kind = "derivation"
        try:
            derivation = freeze_independent_selected_result_derivation(
                case_root,
                {
                    "case_id": item["case_id"],
                    "validator_identity": authorization["target_identity"],
                    "profile_id": item["target_packet"]["profile_id"],
                    "selected_report_path": item["target_packet"]["selected_report_path"],
                    "derived_at": item["derived_at"],
                },
                frozen_at=item["frozen_at"],
            )
            replayed = revalidate_independent_selected_result_derivation(derivation, case_root)
            if replayed["case_tree_digest"] != item["snapshot_tree_digest"]:
                raise SelectedResultTargetWorkerError(
                    "Authorized target snapshot bytes have drifted."
                )
            record = _target_record(authorization, item, replayed)
        except SelectedResultTargetWorkerError:
            raise
        except Exception as error:
            record_kind = "uncontrolled_failure"
            record = _uncontrolled_failure_record(authorization, item, error)
        write_normalized_json_once(record_path, record)
        inventory.append(
            {
                "case_id": item["case_id"],
                "path": record_path.relative_to(output_root).as_posix(),
                "record_kind": record_kind,
                "content_digest": sha256_digest(record_path.read_bytes()),
            }
        )
        completed_at = str(item["frozen_at"])

    if completed_at is None:
        raise SelectedResultTargetWorkerError("Target authorization contained no cases.")
    manifest: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_target_worker_manifest",
        "target_worker_version": TARGET_WORKER_VERSION,
        "block": authorization["block"],
        "provider_slot": authorization["provider_slot"],
        "assignment_digest": authorization["assignment_digest"],
        "runner_freeze_digest": authorization["runner_freeze_digest"],
        "release_gate_digest": authorization["release_gate_digest"],
        "target_authorization_digest": authorization["target_authorization_digest"],
        "record_inventory": inventory,
        "record_count": len(inventory),
        "uncontrolled_failure_count": sum(
            item["record_kind"] == "uncontrolled_failure" for item in inventory
        ),
        "phase_completed_at": completed_at,
        "project_code_executed": False,
        "qualification_authority": "none_target_worker_manifest_only",
    }
    manifest["target_worker_manifest_digest"] = semantic_digest(manifest)
    write_normalized_json_once(output_root / "TARGET_WORKER_MANIFEST.json", manifest)
    return manifest


def _target_record(
    authorization: Mapping[str, Any],
    case: Mapping[str, Any],
    derivation: Mapping[str, Any],
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_qualification_target_output",
        "target_worker_version": TARGET_WORKER_VERSION,
        "case_id": case["case_id"],
        "target_packet": dict(case["target_packet"]),
        "assignment_binding": _assignment_binding(authorization, case),
        "runner_freeze_digest": authorization["runner_freeze_digest"],
        "release_gate_digest": authorization["release_gate_digest"],
        "target_authorization_digest": authorization["target_authorization_digest"],
        "target_derivation": dict(derivation),
        "qualification_authority": "none_qualification_target_output_only",
    }
    record["qualification_target_output_digest"] = semantic_digest(record)
    return record


def _uncontrolled_failure_record(
    authorization: Mapping[str, Any],
    case: Mapping[str, Any],
    error: Exception,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_uncontrolled_target_failure",
        "target_worker_version": TARGET_WORKER_VERSION,
        "case_id": case["case_id"],
        "target_packet": dict(case["target_packet"]),
        "assignment_binding": _assignment_binding(authorization, case),
        "runner_freeze_digest": authorization["runner_freeze_digest"],
        "release_gate_digest": authorization["release_gate_digest"],
        "target_authorization_digest": authorization["target_authorization_digest"],
        "target_identity": dict(authorization["target_identity"]),
        "error_type": type(error).__name__,
        "qualification_outcome": "uncontrolled_failure",
        "completed_at": case["frozen_at"],
        "project_code_executed": False,
        "qualification_authority": "none_target_failure_only",
    }
    record["failure_digest"] = semantic_digest(record)
    return record


def _assignment_binding(
    authorization: Mapping[str, Any], case: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "assignment_digest": authorization["assignment_digest"],
        "block": authorization["block"],
        "provider_slot": authorization["provider_slot"],
        "assignment_position": case["assignment_position"],
        "case_id": case["case_id"],
        "target_packet": dict(case["target_packet"]),
    }


def _target_case(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise SelectedResultTargetWorkerError("Target authorization cases must be objects.")
    case = deepcopy(dict(value))
    _exact_keys(
        case,
        set(TARGET_AUTHORIZATION_CASE_FIELDS),
        "target authorization case",
    )
    case_id = _case_id(case["case_id"])
    position = _integer(case["assignment_position"], "assignment_position")
    if not 1 <= position <= 48:
        raise SelectedResultTargetWorkerError("Assignment position is outside its frozen block.")
    snapshot_path = _relative_path(case["snapshot_path"], "snapshot_path")
    snapshot_digest = _digest(case["snapshot_tree_digest"], "snapshot_tree_digest")
    packet = _target_packet(case["target_packet"])
    if packet["case_id"] != case_id:
        raise SelectedResultTargetWorkerError("Target packet case identity has drifted.")
    derived = _timestamp(case["derived_at"], "derived_at")
    frozen = _timestamp(case["frozen_at"], "frozen_at")
    if derived > frozen:
        raise SelectedResultTargetWorkerError("Target case chronology is invalid.")
    return {
        "case_id": case_id,
        "assignment_position": position,
        "snapshot_path": snapshot_path,
        "snapshot_tree_digest": snapshot_digest,
        "target_packet": packet,
        "derived_at": _iso(derived),
        "frozen_at": _iso(frozen),
    }


def _target_packet(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise SelectedResultTargetWorkerError("Target packet must be an object.")
    packet = dict(value)
    _exact_keys(packet, set(TARGET_AUTHORIZATION_PACKET_FIELDS), "target packet")
    result = {
        "case_id": _case_id(packet["case_id"]),
        "profile_id": _text(packet["profile_id"], "profile_id"),
        "selected_report_path": _relative_path(
            packet["selected_report_path"], "selected_report_path"
        ),
    }
    if result["profile_id"] != PYTHON_STATIC_MARKED_REPORT_PROFILE:
        raise SelectedResultTargetWorkerError("Target packet profile has drifted.")
    return result


def _target_identity(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise SelectedResultTargetWorkerError("Target identity must be an object.")
    identity = dict(value)
    _exact_keys(
        identity,
        set(TARGET_AUTHORIZATION_IDENTITY_FIELDS),
        "target identity",
    )
    result = {
        "validator_id": _text(identity["validator_id"], "validator_id"),
        "provider": _text(identity["provider"], "provider"),
        "execution_context_id": _text(identity["execution_context_id"], "execution_context_id"),
        "identity_evidence_digest": _digest(
            identity["identity_evidence_digest"], "identity_evidence_digest"
        ),
    }
    if any(
        len(result[key]) > MAX_TARGET_IDENTITY_TEXT_CHARS
        for key in ("validator_id", "provider", "execution_context_id")
    ):
        raise SelectedResultTargetWorkerError(
            "Target identity text exceeds its finite character ceiling."
        )
    return result


def _validate_schema_field_projection(schema: Mapping[str, Any]) -> None:
    expected_root_fields = set(TARGET_AUTHORIZATION_FIELDS)
    definitions = schema.get("$defs")
    properties = schema.get("properties")
    if (
        schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
        or schema.get("$id")
        != "https://sc-referee.dev/schemas/selected-result-verifier-target-authorization-v1.0.0.json"
        or schema.get("type") != "object"
        or schema.get("additionalProperties") is not False
        or not isinstance(schema.get("required"), list)
        or set(schema["required"]) != expected_root_fields
        or not isinstance(properties, Mapping)
        or set(properties) != expected_root_fields
        or not isinstance(definitions, Mapping)
        or set(definitions)
        != {
            "caseId",
            "normalizedRelativePath",
            "sha256Digest",
            "singleLineText",
            "targetCase",
            "targetIdentity",
            "targetPacket",
            "timestamp",
        }
        or schema.get("x-recursively-forbidden-field-name-fragments")
        != list(TARGET_AUTHORIZATION_FORBIDDEN_FIELD_NAME_FRAGMENTS)
    ):
        raise SelectedResultTargetWorkerError(
            "Installed target-authorization schema field projection has drifted."
        )
    _validate_schema_object(
        definitions["targetCase"],
        fields=TARGET_AUTHORIZATION_CASE_FIELDS,
        label="target case",
    )
    _validate_schema_object(
        definitions["targetIdentity"],
        fields=TARGET_AUTHORIZATION_IDENTITY_FIELDS,
        label="target identity",
    )
    _validate_schema_object(
        definitions["targetPacket"],
        fields=TARGET_AUTHORIZATION_PACKET_FIELDS,
        label="target packet",
    )
    cases = properties["cases"]
    if (
        not isinstance(cases, Mapping)
        or cases.get("type") != "array"
        or cases.get("minItems") != 1
        or cases.get("maxItems") != MAX_TARGET_CASES
        or cases.get("uniqueItems") is not True
        or cases.get("items") != {"$ref": "#/$defs/targetCase"}
    ):
        raise SelectedResultTargetWorkerError(
            "Installed target-authorization case-array schema has drifted."
        )


def _validate_schema_object(value: Any, *, fields: frozenset[str], label: str) -> None:
    if (
        not isinstance(value, Mapping)
        or value.get("type") != "object"
        or value.get("additionalProperties") is not False
        or not isinstance(value.get("required"), list)
        or set(value["required"]) != set(fields)
        or not isinstance(value.get("properties"), Mapping)
        or set(value["properties"]) != set(fields)
    ):
        raise SelectedResultTargetWorkerError(
            f"Installed target-authorization {label} schema has drifted."
        )


def _reject_forbidden_authorization_field_names(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise SelectedResultTargetWorkerError(
                    "Target authorization field names must be strings."
                )
            normalized = key.casefold()
            if any(
                fragment in normalized
                for fragment in TARGET_AUTHORIZATION_FORBIDDEN_FIELD_NAME_FRAGMENTS
            ):
                raise SelectedResultTargetWorkerError(
                    "Target authorization contains a recursively forbidden field name."
                )
            _reject_forbidden_authorization_field_names(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _reject_forbidden_authorization_field_names(child)


def _load_canonical_authorization(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise SelectedResultTargetWorkerError("Target authorization must be one real regular file.")
    payload = path.read_bytes()
    if len(payload) > MAX_TARGET_AUTHORIZATION_BYTES:
        raise SelectedResultTargetWorkerError(
            "Target authorization exceeds its finite byte ceiling."
        )
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SelectedResultTargetWorkerError("Target authorization is not valid JSON.") from error
    if not isinstance(value, dict) or payload != (canonical_json(value) + "\n").encode("utf-8"):
        raise SelectedResultTargetWorkerError(
            "Target authorization must be canonical JSON ending in one newline."
        )
    return validate_target_authorization(value)


def _safe_snapshot_path(root: Path, value: Any) -> Path:
    relative = _relative_path(value, "snapshot_path")
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        try:
            observed = current.lstat()
        except OSError as error:
            raise SelectedResultTargetWorkerError("Target snapshot path is absent.") from error
        if stat.S_ISLNK(observed.st_mode):
            raise SelectedResultTargetWorkerError(
                "Target snapshot path cannot traverse a symbolic link."
            )
    _real_directory(current, "Target case snapshot")
    return current


def _real_directory(path: Path, label: str) -> None:
    try:
        observed = path.lstat()
    except OSError as error:
        raise SelectedResultTargetWorkerError(f"{label} is absent.") from error
    if not stat.S_ISDIR(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
        raise SelectedResultTargetWorkerError(f"{label} must be a real non-symlink directory.")


def _case_id(value: Any) -> str:
    case_id = _text(value, "case_id")
    suffix = case_id.removeprefix("case:")
    if (
        not case_id.startswith("case:")
        or len(suffix) != 20
        or any(character not in "0123456789abcdef" for character in suffix)
    ):
        raise SelectedResultTargetWorkerError("Invalid opaque case identity.")
    return case_id


def _relative_path(value: Any, label: str) -> str:
    path = _text(value, label)
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or "\\" in path
        or len(path.encode("utf-8")) > MAX_TARGET_RELATIVE_PATH_UTF8_BYTES
        or path != pure.as_posix()
        or path in {"", "."}
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        raise SelectedResultTargetWorkerError(f"{label} is not a normalized relative path.")
    return path


def _digest(value: Any, label: str) -> str:
    digest = _text(value, label)
    payload = digest.removeprefix("sha256:")
    if (
        not digest.startswith("sha256:")
        or len(payload) != 64
        or any(character not in "0123456789abcdef" for character in payload)
    ):
        raise SelectedResultTargetWorkerError(f"{label} must be a SHA-256 digest.")
    return digest


def _timestamp(value: Any, label: str) -> datetime:
    text = _text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise SelectedResultTargetWorkerError(f"{label} is not a valid timestamp.") from error
    if parsed.tzinfo is None:
        raise SelectedResultTargetWorkerError(f"{label} must include a timezone.")
    result = parsed.astimezone(UTC)
    if text != _iso(result):
        raise SelectedResultTargetWorkerError(
            f"{label} must be a canonical UTC timestamp ending in Z."
        )
    return result


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _integer(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SelectedResultTargetWorkerError(f"{label} must be an integer.")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\n" in value or "\r" in value:
        raise SelectedResultTargetWorkerError(f"{label} must be non-empty single-line text.")
    return value


def _exact_keys(value: Mapping[str, Any], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise SelectedResultTargetWorkerError(f"{label} has an unsupported shape.")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the isolated selected-result qualification target worker."
    )
    parser.add_argument("--runtime-manifest", type=Path)
    parser.add_argument("--target-authorization", type=Path)
    parser.add_argument("--target-snapshot-root", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    execution_arguments = (
        arguments.target_authorization,
        arguments.target_snapshot_root,
        arguments.output,
    )
    if arguments.runtime_manifest is not None:
        if any(item is not None for item in execution_arguments):
            parser.error("--runtime-manifest cannot be combined with target execution inputs")
        freeze_target_runtime_manifest(output_path=arguments.runtime_manifest)
        return 0
    if any(item is None for item in execution_arguments):
        parser.error(
            "target execution requires --target-authorization, --target-snapshot-root, and --output"
        )
    if not all(isinstance(item, Path) for item in execution_arguments):
        raise SelectedResultTargetWorkerError("Target execution paths are malformed.")
    run_target_worker(
        authorization_path=arguments.target_authorization,
        snapshot_root=arguments.target_snapshot_root,
        output_root=arguments.output,
    )
    return 0


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
