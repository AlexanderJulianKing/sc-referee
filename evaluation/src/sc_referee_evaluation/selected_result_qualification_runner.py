from __future__ import annotations

import argparse
import hashlib
import importlib.resources
import importlib.util
import json
import locale
import os
import platform
import stat
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee_evaluation.qualification_identity import (
    IDENTITY_REGISTRY_VERSION,
    SESSION_RECEIPT_VERSION,
    validate_identity_registry,
    validate_registrar_signed_receipt,
)
from sc_referee_evaluation.selected_result_qualification_io import (
    RootedReader,
    canonical_relative_path,
    write_canonical_json_exclusive,
)
from sc_referee_evaluation.selected_result_qualification_trust import (
    APPROVED_LAUNCH_RECEIPT,
    OFFICIAL_RUNNER_FREEZE_DIGEST,
)
from sc_referee_evaluation.selected_result_verifier_qualification import (
    FROZEN_ASSIGNMENT_DIGEST,
    freeze_oracle_proof,
    freeze_qualification_validation,
    freeze_verifier_comparison,
    parse_construction_certificate,
)

RUNNER_VERSION = "1.1.0-development"
_TARGET_AUTHORIZATION_SCHEMA_CONTENT_DIGEST = (
    "sha256:82ff25bb509eeec2cd261e33264115b9e30556b40ff1de1310e02f898ccfebd6"
)
_TARGET_AUTHORIZATION_SCHEMA_DIGEST = (
    "sha256:0c0f26e8dace6c291f8e3cdac6269c4a88223ea9dbcea7c8a644c4082687dc3d"
)
_TARGET_AUTHORIZATION_FIELD_PROJECTION_DIGEST = (
    "sha256:00a0640d8dc7cbdbb54a6b36af7e22527ac5fbaa3b0d2de45fd60bc46203f68a"
)
_TARGET_AUTHORIZATION_FORBIDDEN_FIELD_NAME_FRAGMENTS = [
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
]
_TARGET_OCI_ENVIRONMENT = {
    "inherit_host": False,
    "values": [
        "LANG=C.UTF-8",
        "LC_ALL=C.UTF-8",
        "PYTHONHASHSEED=0",
        "PYTHONNOUSERSITE=1",
    ],
}


def _load(path: Path) -> dict[str, Any]:
    before = path.lstat()
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Expected one real JSON file: {path}")
    payload = path.read_bytes()
    after = path.lstat()
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_mode,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_mode,
    ):
        raise ValueError(f"JSON file changed while it was read: {path}")
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError(f"Expected one JSON object: {path}")
    return value


def _load_rooted(root: Path, relative_path: str, label: str) -> dict[str, Any]:
    with RootedReader(root) as reader:
        rooted = reader.read(relative_path)
    try:
        value = json.loads(rooted.data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is not valid JSON.") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be one JSON object.")
    return value


def _load_rooted_with_digest(
    root: Path, relative_path: str, label: str
) -> tuple[dict[str, Any], str]:
    with RootedReader(root) as reader:
        rooted = reader.read(relative_path)
    try:
        value = json.loads(rooted.data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is not valid JSON.") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be one JSON object.")
    return value, rooted.content_digest


def _self_digested(value: dict[str, Any], digest_field: str, label: str) -> dict[str, Any]:
    result = dict(value)
    supplied = result.pop(digest_field, None)
    if supplied != semantic_digest(result):
        raise ValueError(f"{label} self-digest does not replay.")
    result[digest_field] = supplied
    return result


def _require_sha256_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        raise ValueError(f"{label} must be one sha256 digest.")
    try:
        int(value.removeprefix("sha256:"), 16)
    except ValueError as error:
        raise ValueError(f"{label} must be one sha256 digest.") from error
    return value


def _validated_assignments(path: Path) -> dict[str, Any]:
    assignments = _self_digested(_load(path), "assignment_digest", "assignment manifest")
    if (
        assignments["assignment_digest"] != FROZEN_ASSIGNMENT_DIGEST
        or assignments.get("artifact_kind") != "selected_result_verifier_opaque_assignments"
        or assignments.get("case_count") != 96
        or assignments.get("case_replacement_permitted") is not False
        or assignments.get("case_bytes_present") is not False
        or assignments.get("target_outputs_present") is not False
    ):
        raise ValueError("Assignment manifest is not the frozen qualification study.")
    return assignments


def _validated_runner_freeze(
    path: Path,
    assignments: dict[str, Any],
    *,
    assignments_path: Path,
) -> dict[str, Any]:
    freeze = _self_digested(_load(path), "runner_freeze_digest", "runner freeze")
    if (
        OFFICIAL_RUNNER_FREEZE_DIGEST == "UNFROZEN"
        or freeze["runner_freeze_digest"] != OFFICIAL_RUNNER_FREEZE_DIGEST
    ):
        raise ValueError("Runner freeze is not the one officially approved execution tuple.")
    assignment_ref = freeze.get("assignment_ref")
    identity_registry_ref = freeze.get("identity_registry_ref")
    modules = freeze.get("modules")
    resources = freeze.get("resources")
    target_authorization_contract = freeze.get("target_authorization_contract")
    expected_module_roles = {
        "safe_io",
        "qualification_identity",
        "semantic_review",
        "byte_oracle",
        "qualification_controller",
        "target_verifier",
        "target_worker",
        "phase_runner",
        "package_initializer",
    }
    expected_resources = {
        "semantic-review-contract.json",
        "provider-pack-schema.json",
        "target-authorization-schema.json",
        "case-author-prompt.txt",
        "semantic-validator-prompt.txt",
        "target-runner-prompt.txt",
        "validation-runner-prompt.txt",
        "comparison-prompt.txt",
    }
    if (
        freeze.get("artifact_kind") != "selected_result_verifier_runner_freeze"
        or freeze.get("runner_version") != RUNNER_VERSION
        or freeze.get("freeze_identity") != "selected-result-verifier-v1.1.0-execution-tuple"
        or freeze.get("target_outputs_present") is not False
        or freeze.get("case_bytes_present") is not False
        or freeze.get("qualification_authority") != "none_runner_freeze_only"
        or not isinstance(assignment_ref, dict)
        or assignment_ref.get("assignment_digest") != assignments["assignment_digest"]
        or assignment_ref.get("case_count") != assignments["case_count"]
        or assignment_ref.get("assignment_version") != assignments["assignment_version"]
        or assignment_ref.get("content_digest") != sha256_digest(assignments_path.read_bytes())
        or not isinstance(identity_registry_ref, dict)
        or identity_registry_ref.get("identity_registry_version") != IDENTITY_REGISTRY_VERSION
        or _require_sha256_digest(
            identity_registry_ref.get("identity_registry_digest"),
            "identity registry digest",
        )
        != identity_registry_ref.get("identity_registry_digest")
        or _require_sha256_digest(
            identity_registry_ref.get("content_digest"),
            "identity registry content digest",
        )
        != identity_registry_ref.get("content_digest")
        or not isinstance(modules, dict)
        or set(modules) != expected_module_roles
        or not isinstance(resources, dict)
        or set(resources) != expected_resources
        or not isinstance(target_authorization_contract, dict)
        or target_authorization_contract.get("authorization_version") != "1.0.0"
        or target_authorization_contract.get("schema_content_digest")
        != _TARGET_AUTHORIZATION_SCHEMA_CONTENT_DIGEST
        or target_authorization_contract.get("schema_semantic_digest")
        != _TARGET_AUTHORIZATION_SCHEMA_DIGEST
        or target_authorization_contract.get("field_projection_digest")
        != _TARGET_AUTHORIZATION_FIELD_PROJECTION_DIGEST
        or target_authorization_contract.get("recursively_forbidden_field_name_fragments")
        != _TARGET_AUTHORIZATION_FORBIDDEN_FIELD_NAME_FRAGMENTS
    ):
        raise ValueError("Runner freeze does not bind this qualification study.")
    for label, module in modules.items():
        if not isinstance(module, dict) or not isinstance(module.get("module_name"), str):
            raise ValueError(f"Frozen qualification {label} module lock is malformed.")
        spec = importlib.util.find_spec(str(module["module_name"]))
        if spec is None or spec.origin is None:
            raise ValueError(f"Frozen qualification {label} module is not installed.")
        module_path = Path(spec.origin)
        observed = module_path.lstat()
        if (
            not module_path.is_file()
            or module_path.is_symlink()
            or module.get("content_digest") != sha256_digest(module_path.read_bytes())
            or module.get("size_bytes") != observed.st_size
            or module.get("mode") != stat.S_IMODE(observed.st_mode)
            or not isinstance(module.get("entry_points"), list)
        ):
            raise ValueError(f"Frozen qualification {label} bytes have drifted.")
    resource_root = importlib.resources.files(
        "sc_referee_evaluation.qualification_resources.selected_result_v1_1"
    )
    for name, lock in resources.items():
        if not isinstance(lock, dict):
            raise ValueError(f"Frozen resource lock is malformed: {name}")
        resource = resource_root.joinpath(name)
        payload = resource.read_bytes()
        if lock.get("content_digest") != sha256_digest(payload) or lock.get("size_bytes") != len(
            payload
        ):
            raise ValueError(f"Frozen qualification resource has drifted: {name}")
    runtime = freeze.get("runtime_lock")
    if runtime != {
        "implementation": platform.python_implementation(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "abi_flags": getattr(sys, "abiflags", ""),
        "line_separator": os.linesep,
        "locale_encoding": locale.getencoding(),
    }:
        raise ValueError("Frozen qualification runtime has drifted.")
    isolation = freeze.get("isolation_backend")
    if (
        not isinstance(isolation, dict)
        or isolation.get("kind") != "rootless_oci"
        or isolation.get("runtime_profile") != "podman-rootless-v1"
        or isolation.get("network") != "none"
        or isolation.get("root_filesystem") != "read_only"
        or isolation.get("uid") != "non_root"
        or isolation.get("target_mounts")
        != ["target_authorization:ro", "case_snapshots:ro", "output:rw"]
        or isolation.get("forbidden_mounts")
        != ["provider_pack", "oracle_phase", "semantic_panel", "host_repo"]
        or isolation.get("rootless_probe") != ["info", "--format", "{{.Host.Security.Rootless}}"]
        or isolation.get("image_probe")
        != ["image", "inspect", "<image-digest>", "--format", "{{.Digest}}"]
        or isolation.get("worker_entrypoint") != "sc-referee-eval-selected-result-target-worker"
        or isolation.get("environment") != _TARGET_OCI_ENVIRONMENT
        or isolation.get("capabilities") != "drop_all"
        or isolation.get("no_new_privileges") is not True
        or isolation.get("pid_limit") != 64
        or isolation.get("temporary_filesystem") != "tmpfs:/tmp:noexec,nosuid,nodev,size=16m"
        or isolation.get("unsafe_fallback") is not False
    ):
        raise ValueError("Frozen qualification isolation backend is unsafe or incomplete.")
    runtime_lock = isolation.get("runtime_executable")
    if not isinstance(runtime_lock, dict):
        raise ValueError("Frozen qualification OCI runtime lock is absent.")
    runtime_path = Path(str(runtime_lock.get("path", "")))
    if not runtime_path.is_absolute():
        raise ValueError("Frozen qualification OCI runtime path is not absolute.")
    observed = runtime_path.lstat()
    if (
        runtime_path.name != "podman"
        or runtime_path.is_symlink()
        or not runtime_path.is_file()
        or not observed.st_mode & 0o111
        or runtime_lock.get("content_digest") != sha256_digest(runtime_path.read_bytes())
        or runtime_lock.get("size_bytes") != observed.st_size
        or runtime_lock.get("mode") != stat.S_IMODE(observed.st_mode)
    ):
        raise ValueError("Frozen qualification OCI runtime bytes have drifted.")
    completed = subprocess.run(
        [str(runtime_path), "--version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0 or completed.stdout.strip() != runtime_lock.get("version_output"):
        raise ValueError("Frozen qualification OCI runtime version has drifted.")
    target_runtime_lock = isolation.get("target_runtime_manifest")
    if (
        not isinstance(target_runtime_lock, dict)
        or target_runtime_lock.get("runtime_manifest_version") != "1.0.0"
        or target_runtime_lock.get("distribution_names")
        != ["cryptography", "sc-referee", "sc-referee-evaluation"]
        or target_runtime_lock.get("module_names")
        != [
            "cryptography",
            "sc_referee.core.ids",
            "sc_referee_evaluation.prospective_selected_result_verifier",
            "sc_referee_evaluation.selected_result_qualification_target_worker",
        ]
        or target_runtime_lock.get("probe_command_profile") != "rootless-oci-runtime-manifest-v1"
        or _require_sha256_digest(
            target_runtime_lock.get("target_runtime_manifest_digest"),
            "target runtime manifest digest",
        )
        != target_runtime_lock.get("target_runtime_manifest_digest")
        or _require_sha256_digest(
            target_runtime_lock.get("content_digest"),
            "target runtime manifest content digest",
        )
        != target_runtime_lock.get("content_digest")
    ):
        raise ValueError("Frozen target image runtime manifest lock is incomplete.")
    return freeze


def _validated_frozen_identity_registry(freeze: dict[str, Any]) -> dict[str, Any]:
    reference = freeze.get("identity_registry_ref")
    if not isinstance(reference, dict):
        raise ValueError("Runner freeze has no identity-registry lock.")
    path = Path(str(reference.get("path", "")))
    if not path.is_absolute():
        raise ValueError("Frozen identity-registry path is not absolute.")
    payload = path.read_bytes()
    if sha256_digest(payload) != reference.get("content_digest"):
        raise ValueError("Frozen identity-registry bytes have drifted.")
    registry = validate_identity_registry(_load(path))
    if registry.get("identity_registry_version") != reference.get(
        "identity_registry_version"
    ) or registry.get("identity_registry_digest") != reference.get("identity_registry_digest"):
        raise ValueError("Frozen identity-registry record does not replay its lock.")
    return registry


def _frozen_identity_registry_digest(freeze: dict[str, Any]) -> str:
    reference = freeze.get("identity_registry_ref")
    if not isinstance(reference, dict):
        raise ValueError("Runner freeze has no identity-registry lock.")
    return _require_sha256_digest(
        reference.get("identity_registry_digest"),
        "frozen identity-registry digest",
    )


def _validated_rootless_podman(freeze: dict[str, Any]) -> tuple[Path, str]:
    isolation = freeze.get("isolation_backend")
    if not isinstance(isolation, dict):
        raise ValueError("Frozen qualification isolation backend is absent.")
    runtime_lock = isolation.get("runtime_executable")
    if not isinstance(runtime_lock, dict):
        raise ValueError("Frozen qualification OCI runtime lock is absent.")
    runtime = Path(str(runtime_lock.get("path", "")))
    image_digest = str(isolation.get("image_digest", ""))
    if os.geteuid() == 0:
        raise ValueError("Metric-eligible target execution cannot run from a root host session.")
    rootless = subprocess.run(
        [str(runtime), "info", "--format", "{{.Host.Security.Rootless}}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if rootless.returncode != 0 or rootless.stdout.strip().casefold() != "true":
        raise ValueError("The frozen podman backend is not operating rootlessly.")
    image = subprocess.run(
        [str(runtime), "image", "inspect", image_digest, "--format", "{{.Digest}}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if image.returncode != 0 or image.stdout.strip() != image_digest:
        raise ValueError("The exact frozen target-worker OCI image is unavailable.")
    return runtime, image_digest


def _run_target_worker_in_oci(
    *,
    freeze: dict[str, Any],
    authorization_path: Path,
    snapshot_root: Path,
    output_parent: Path,
    snapshot_inventory_digest: str,
) -> dict[str, Any]:
    runtime, image_digest = _validated_rootless_podman(freeze)
    runtime_evidence = _probe_target_runtime_manifest(
        freeze=freeze,
        runtime=runtime,
        image_digest=image_digest,
    )
    for path in (authorization_path.parent, snapshot_root, output_parent):
        if "," in str(path) or "\n" in str(path) or "\r" in str(path):
            raise ValueError("OCI qualification mount paths contain unsupported characters.")
    uid = os.geteuid()
    gid = os.getegid()
    command = [
        str(runtime),
        "run",
        "--rm",
        "--pull=never",
        "--network=none",
        "--read-only",
        "--userns=keep-id",
        "--user",
        f"{uid}:{gid}",
        "--cap-drop=all",
        "--security-opt=no-new-privileges",
        "--pids-limit=64",
        "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16m",
        "--unsetenv-all",
        "--env=LANG=C.UTF-8",
        "--env=LC_ALL=C.UTF-8",
        "--env=PYTHONHASHSEED=0",
        "--env=PYTHONNOUSERSITE=1",
        "--mount",
        f"type=bind,src={authorization_path.parent},dst=/qualification/input,ro=true",
        "--mount",
        f"type=bind,src={snapshot_root},dst=/qualification/snapshots,ro=true",
        "--mount",
        f"type=bind,src={output_parent},dst=/qualification/output,rw=true",
        image_digest,
        "sc-referee-eval-selected-result-target-worker",
        "--target-authorization",
        f"/qualification/input/{authorization_path.name}",
        "--target-snapshot-root",
        "/qualification/snapshots",
        "--output",
        "/qualification/output/worker-output",
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-2000:]
        raise ValueError(f"Isolated target worker failed closed: {detail}")
    isolation = freeze["isolation_backend"]
    runtime_lock = isolation["runtime_executable"]
    return {
        "isolation_receipt_version": "1.0.0",
        "runtime_profile": isolation["runtime_profile"],
        "runtime_content_digest": runtime_lock["content_digest"],
        "runtime_version_output": runtime_lock["version_output"],
        "image_digest": image_digest,
        "rootless_probe_output": "true",
        "image_probe_output": image_digest,
        **runtime_evidence,
        "target_worker_command_profile": "rootless-oci-target-worker-v1",
        "environment": _TARGET_OCI_ENVIRONMENT,
        "mount_projection": [
            "target_authorization:ro",
            "case_snapshots:ro",
            "output:rw",
        ],
        "target_authorization_content_digest": sha256_digest(authorization_path.read_bytes()),
        "snapshot_inventory_digest": snapshot_inventory_digest,
        "network": "none",
        "root_filesystem": "read_only",
        "uid": "non_root",
        "capabilities": "drop_all",
        "no_new_privileges": True,
        "pid_limit": 64,
        "temporary_filesystem": "tmpfs:/tmp:noexec,nosuid,nodev,size=16m",
        "unsafe_fallback_used": False,
    }


def _probe_target_runtime_manifest(
    *,
    freeze: dict[str, Any],
    runtime: Path,
    image_digest: str,
) -> dict[str, str]:
    isolation = freeze.get("isolation_backend")
    if not isinstance(isolation, dict):
        raise ValueError("Frozen qualification isolation backend is absent.")
    expected = isolation.get("target_runtime_manifest")
    if not isinstance(expected, dict):
        raise ValueError("Frozen target runtime manifest lock is absent.")
    with tempfile.TemporaryDirectory(prefix="sc-referee-target-runtime-") as temporary:
        output_root = Path(temporary)
        command = [
            str(runtime),
            "run",
            "--rm",
            "--pull=never",
            "--network=none",
            "--read-only",
            "--userns=keep-id",
            "--cap-drop=all",
            "--security-opt=no-new-privileges",
            "--pids-limit=64",
            "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16m",
            "--unsetenv-all",
            "--env=LANG=C.UTF-8",
            "--env=LC_ALL=C.UTF-8",
            "--env=PYTHONHASHSEED=0",
            "--env=PYTHONNOUSERSITE=1",
            "--volume",
            f"{output_root}:/qualification-runtime:rw",
            image_digest,
            "sc-referee-eval-selected-result-target-worker",
            "--runtime-manifest",
            "/qualification-runtime/runtime-manifest.json",
        ]
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()[-2000:]
            raise ValueError(f"Target image runtime-manifest probe failed closed: {detail}")
        value, content_digest = _load_rooted_with_digest(
            output_root,
            "runtime-manifest.json",
            "target image runtime manifest",
        )
        with RootedReader(output_root) as reader:
            payload = reader.read_bytes("runtime-manifest.json")
        if payload != (canonical_json(value) + "\n").encode("utf-8"):
            raise ValueError("Target image runtime manifest is not canonical JSON.")
        manifest = _self_digested(
            value,
            "target_runtime_manifest_digest",
            "target image runtime manifest",
        )
        if (
            manifest.get("artifact_kind") != "selected_result_verifier_target_runtime_manifest"
            or manifest.get("runtime_manifest_version") != "1.0.0"
            or manifest.get("input_projection") != "installed_runtime_only"
            or manifest.get("project_code_executed") is not False
            or manifest.get("target_runtime_manifest_digest")
            != expected.get("target_runtime_manifest_digest")
            or content_digest != expected.get("content_digest")
        ):
            raise ValueError("Target image runtime manifest does not replay the frozen tuple.")
        return {
            "target_runtime_manifest_digest": str(manifest["target_runtime_manifest_digest"]),
            "target_runtime_manifest_content_digest": content_digest,
            "target_runtime_probe_command_profile": str(expected["probe_command_profile"]),
        }


def _validated_pilot_decision(
    path: Path,
    *,
    assignments: dict[str, Any],
    runner_freeze: dict[str, Any],
    runner_freeze_digest: str,
    provider_run_roots: Sequence[Path],
) -> dict[str, Any]:
    decision = _self_digested(_load(path), "pilot_decision_digest", "pilot qualification decision")
    try:
        rebuilt = freeze_pilot_decision(
            provider_run_roots=provider_run_roots,
            assignments=assignments,
            runner_freeze=runner_freeze,
            runner_freeze_digest=runner_freeze_digest,
            decision_identity=decision.get("decision_identity"),
            decided_at=str(decision.get("decided_at", "")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(
            "Held-out block lacks a replayable evidence-backed pilot decision."
        ) from error
    if rebuilt != decision or decision.get("decision") != "pass":
        raise ValueError("Held-out block lacks an exact passing frozen pilot decision.")
    return decision


def freeze_pilot_decision(
    *,
    provider_run_roots: Sequence[Path],
    assignments: dict[str, Any],
    runner_freeze: dict[str, Any],
    runner_freeze_digest: str,
    decision_identity: Any,
    decided_at: str,
) -> dict[str, Any]:
    """Reconstruct the pilot outcome from both complete retained provider bundles."""

    if len(provider_run_roots) != 2:
        raise ValueError("Pilot decision requires exactly two provider run bundles.")
    if runner_freeze.get("runner_freeze_digest") != runner_freeze_digest:
        raise ValueError("Pilot decision runner-freeze binding has drifted.")
    identity = _identity_value(decision_identity, "pilot decision identity")
    provider_evidence = [
        _pilot_bundle_evidence(
            root,
            assignments=assignments,
            runner_freeze=runner_freeze,
            runner_freeze_digest=runner_freeze_digest,
        )
        for root in provider_run_roots
    ]
    provider_evidence.sort(key=lambda item: str(item["provider_slot"]))
    if [item["provider_slot"] for item in provider_evidence] != [
        "provider-family-1",
        "provider-family-2",
    ]:
        raise ValueError("Pilot bundles do not cover both frozen provider slots.")
    cases = [case for provider in provider_evidence for case in provider["case_evidence"]]
    expected = [
        item for item in _all_assigned_cases(assignments, block="pilot") if isinstance(item, dict)
    ]
    expected_by_id = {str(item["case_id"]): item for item in expected}
    if (
        len(cases) != 48
        or len({str(item["case_id"]) for item in cases}) != 48
        or {str(item["case_id"]) for item in cases} != set(expected_by_id)
    ):
        raise ValueError("Pilot evidence does not cover the exact 48 frozen assignments.")
    cases.sort(key=lambda item: int(expected_by_id[str(item["case_id"])]["assignment_position"]))
    state_counts = {state: 0 for state in ("V", "A", "I", "U")}
    for item in cases:
        state = str(item["expected_state"])
        if state not in state_counts:
            raise ValueError("Pilot comparison contains an unknown expected state.")
        state_counts[state] += 1
    failures = [item for item in cases if item["comparison_outcome"] != "exact_match"]
    u_cell_counts, family_counts, cluster_counts, diversity_passed = _pilot_diversity(cases)
    pass_decision = (
        not failures and state_counts == {"V": 12, "A": 8, "I": 8, "U": 20} and diversity_passed
    )
    decided = _iso(_timestamp(decided_at))
    result: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_pilot_qualification_decision",
        "decision_version": "1.1.0-development",
        "assignment_digest": assignments["assignment_digest"],
        "runner_freeze_digest": runner_freeze_digest,
        "provider_bundles": [
            {
                key: item[key]
                for key in (
                    "provider_slot",
                    "provider_pack_sha256",
                    "oracle_phase_digest",
                    "target_phase_digest",
                    "validation_phase_digest",
                    "comparison_phase_digest",
                    "fresh_location_replay_manifest_digest",
                    "bundle_evidence_digest",
                )
            }
            for item in provider_evidence
        ],
        "pilot_case_evidence_digest": semantic_digest(cases),
        "pilot_case_count": len(cases),
        "state_counts": state_counts,
        "u_cell_counts": u_cell_counts,
        "construction_family_counts": dict(sorted(family_counts.items())),
        "construction_cluster_counts": cluster_counts,
        "global_diversity_passed": diversity_passed,
        "exact_v_binding_count": sum(
            item["expected_state"] == "V" and item["binding_matches"] is True for item in cases
        ),
        "exact_match_count": sum(item["comparison_outcome"] == "exact_match" for item in cases),
        "false_completion_count": sum(
            item["comparison_outcome"] == "false_complete" for item in cases
        ),
        "failure_count": len(failures),
        "fresh_location_replay_count": sum(
            int(item["fresh_location_replay_count"]) for item in provider_evidence
        ),
        "decision": "pass" if pass_decision else "fail",
        "held_out_open_authorized": pass_decision,
        "decision_identity": identity,
        "decided_at": decided,
        "qualification_authority": "none_pilot_decision_only",
    }
    result["pilot_decision_digest"] = semantic_digest(result)
    return result


def _pilot_diversity(
    cases: Sequence[dict[str, Any]],
) -> tuple[dict[str, int], dict[str, int], dict[str, int], bool]:
    cells = (
        "dynamic_or_opaque_structure",
        "role_or_source_artifact_boundary",
        "encoding_newline_or_runtime_boundary",
        "syntax_value_or_finite_budget_boundary",
        "mode_or_role_boundary",
    )
    u_cell_counts = {cell: sum(item.get("u_cell") == cell for item in cases) for cell in cells}
    family_counts: dict[str, int] = {}
    clusters: dict[str, set[str]] = {state: set() for state in ("V", "A", "I", "U")}
    malformed = False
    for item in cases:
        family = item.get("construction_family")
        cluster = item.get("construction_cluster")
        state = item.get("expected_state")
        if (
            not isinstance(family, str)
            or not family
            or not isinstance(cluster, str)
            or not cluster
            or state not in clusters
        ):
            malformed = True
            continue
        family_counts[family] = family_counts.get(family, 0) + 1
        clusters[str(state)].add(cluster)
    cluster_counts = {state: len(clusters[state]) for state in ("V", "A", "I", "U")}
    passed = (
        not malformed
        and u_cell_counts == {cell: 4 for cell in cells}
        and all(count <= 24 for count in family_counts.values())
        and all(count >= 4 for count in cluster_counts.values())
    )
    return u_cell_counts, family_counts, cluster_counts, passed


def _fresh_replay_case_projection(
    *,
    oracle_proof: dict[str, Any],
    target_record: dict[str, Any],
    validation_record: dict[str, Any],
    comparison_record: dict[str, Any],
) -> dict[str, Any]:
    reconciliations = oracle_proof.get("semantic_reconciliations")
    target = target_record.get("target_derivation")
    validation = validation_record.get("target_validation")
    oracle_result = oracle_proof.get("oracle_result")
    if (
        not isinstance(reconciliations, list)
        or len(reconciliations) != 2
        or not isinstance(target, dict)
        or not isinstance(validation, dict)
        or not isinstance(oracle_result, dict)
    ):
        raise ValueError("Fresh-replay source records are incomplete.")
    semantic_projection: list[dict[str, Any]] = []
    for reconciliation in reconciliations:
        if not isinstance(reconciliation, dict):
            raise ValueError("Fresh-replay semantic reconciliation is malformed.")
        review = reconciliation.get("blind_review")
        if not isinstance(review, dict):
            raise ValueError("Fresh-replay blind review is absent.")
        semantic_projection.append(
            {
                "case_inventory": review.get("case_inventory"),
                "semantic_conclusion": review.get("semantic_conclusion"),
                "binding_evidence": review.get("binding_evidence"),
                "rule_trace": review.get("rule_trace"),
                "independence_declaration": review.get("independence_declaration"),
                "certificate_conclusion": reconciliation.get("certificate_conclusion"),
                "agrees_with_construction_certificate": reconciliation.get(
                    "agrees_with_construction_certificate"
                ),
            }
        )
    semantic_projection.sort(key=semantic_digest)
    target_fields = (
        "profile_id",
        "profile_digest",
        "case_id",
        "selected_report_path",
        "candidate_bindings",
        "candidate_binding_digests",
        "derivation_status",
        "reason_codes",
        "retained_files",
        "case_tree_digest",
        "locator_receipts",
        "implementation_lock",
        "project_code_executed",
    )
    validation_fields = (
        "case_contract_digest",
        "status",
        "selected_result_binding_digest",
        "case_tree_digest",
        "reason_codes",
        "qualification_authority",
    )
    comparison_fields = (
        "case_id",
        "assignment_binding",
        "expected_state",
        "observed_state",
        "expected_reason_codes",
        "observed_reason_codes",
        "expected_validation_status",
        "observed_validation_status",
        "expected_validation_reason_codes",
        "observed_validation_reason_codes",
        "state_matches",
        "reason_codes_match",
        "validation_matches",
        "binding_matches",
        "comparison_outcome",
    )
    for value, fields, label in (
        (target, target_fields, "target"),
        (validation, validation_fields, "validation"),
        (comparison_record, comparison_fields, "comparison"),
    ):
        missing = set(fields) - set(value)
        if missing:
            raise ValueError(f"Fresh-replay {label} projection is missing fields.")
    result: dict[str, Any] = {
        "case_id": comparison_record.get("case_id"),
        "semantic_reviews": semantic_projection,
        "oracle_result": oracle_result,
        "target": {field: target[field] for field in target_fields},
        "case_contract": validation_record.get("case_contract"),
        "validation": {field: validation[field] for field in validation_fields},
        "comparison": {field: comparison_record[field] for field in comparison_fields},
    }
    result["projection_digest"] = semantic_digest(result)
    return result


def _pilot_bundle_evidence(
    root: Path,
    *,
    assignments: dict[str, Any],
    runner_freeze: dict[str, Any],
    runner_freeze_digest: str,
    require_fresh_replays: bool = True,
) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Pilot provider run root is absent or a symbolic link.")
    pack_root = _safe_pack_path(root, "provider-pack", "pilot provider-pack root")
    pack = _load_rooted(pack_root, "pack-manifest.json", "pilot pack manifest")
    pack_digest = _verify_pack_seal(pack_root, pack)
    phase_specs = {
        "oracle": ("ORACLE_PHASE_MANIFEST.json", "oracle_phase_digest"),
        "target": ("TARGET_PHASE_MANIFEST.json", "target_phase_digest"),
        "validation": ("VALIDATION_PHASE_MANIFEST.json", "validation_phase_digest"),
        "comparison": ("COMPARISON_PHASE_MANIFEST.json", "comparison_phase_digest"),
    }
    manifests: dict[str, dict[str, Any]] = {}
    for phase, (name, digest_field) in phase_specs.items():
        phase_root = _safe_pack_path(root, phase, f"pilot {phase} phase root")
        manifests[phase] = _self_digested(
            _load_rooted(phase_root, name, f"pilot {phase} manifest"),
            digest_field,
            f"pilot {phase} manifest",
        )
    slots = {str(item.get("provider_slot")) for item in manifests.values()}
    if len(slots) != 1:
        raise ValueError("Pilot phase manifests disagree on provider slot.")
    provider_slot = slots.pop()
    pairs = _ordered_pairs(
        assignments,
        pack,
        block="pilot",
        provider_slot=provider_slot,
    )
    expected_cases = [str(item["case_id"]) for item, _ in pairs]
    pair_by_id = {str(assignment["case_id"]): (assignment, case) for assignment, case in pairs}
    oracle = manifests["oracle"]
    target = manifests["target"]
    validation = manifests["validation"]
    comparison = manifests["comparison"]
    if (
        any(item.get("block") != "pilot" for item in manifests.values())
        or any(
            item.get("assignment_digest") != assignments["assignment_digest"]
            or item.get("runner_freeze_digest") != runner_freeze_digest
            for item in manifests.values()
        )
        or target.get("oracle_phase_digest") != oracle["oracle_phase_digest"]
        or validation.get("target_phase_digest") != target["target_phase_digest"]
        or comparison.get("oracle_phase_digest") != oracle["oracle_phase_digest"]
        or comparison.get("target_phase_digest") != target["target_phase_digest"]
        or comparison.get("validation_phase_digest") != validation["validation_phase_digest"]
        or oracle.get("proof_count") != 24
        or target.get("record_count") != 24
        or validation.get("record_count") != 24
        or comparison.get("comparison_count") != 24
        or pack.get("assignment_manifest_digest") != assignments["assignment_digest"]
        or any(item.get("pack_manifest_sha256") != pack_digest for item in manifests.values())
    ):
        raise ValueError("Pilot predecessor manifest chain is incomplete or inconsistent.")
    identity_registry = _validated_frozen_identity_registry(runner_freeze)
    phase_names = {
        "oracle": "freeze-oracles",
        "target": "run-targets",
        "validation": "run-validations",
        "comparison": "compare",
    }
    phase_identities = {
        phase: _manifest_phase_identity(
            manifest,
            phase=phase_names[phase],
            runner_freeze_digest=runner_freeze_digest,
            assignment_digest=str(assignments["assignment_digest"]),
            identity_registry=identity_registry,
        )
        for phase, manifest in manifests.items()
    }
    if (
        len({item["actor_id"] for item in phase_identities.values()}) != 4
        or len({item["execution_context_id"] for item in phase_identities.values()}) != 4
        or len({item["identity_evidence_digest"] for item in phase_identities.values()}) != 4
    ):
        raise ValueError("Pilot deterministic phases reused a launcher identity receipt.")
    for manifest in manifests.values():
        receipt = manifest["phase_launch_receipt"]
        if _timestamp(str(receipt["issued_at"])) > _timestamp(str(manifest["phase_completed_at"])):
            raise ValueError("Pilot phase completed before its trusted launch receipt.")
    _validate_inventory(
        root / "oracle",
        oracle.get("proof_inventory"),
        expected_case_ids=expected_cases,
        label="pilot oracle proof",
    )
    _validate_inventory(
        root / "target",
        target.get("record_inventory"),
        expected_case_ids=expected_cases,
        label="pilot target record",
    )
    target_authorization = _validate_target_phase_bundle(
        root / "target",
        target,
        expected_case_ids=expected_cases,
        runner_freeze=runner_freeze,
    )
    _validate_inventory(
        root / "validation",
        validation.get("record_inventory"),
        expected_case_ids=expected_cases,
        label="pilot validation record",
    )
    _validate_inventory(
        root / "comparison",
        comparison.get("comparison_inventory"),
        expected_case_ids=expected_cases,
        label="pilot comparison",
    )
    if not (
        _timestamp(str(oracle["phase_completed_at"]))
        <= _timestamp(str(target["phase_completed_at"]))
        <= _timestamp(str(validation["phase_completed_at"]))
        <= _timestamp(str(comparison["phase_completed_at"]))
    ):
        raise ValueError("Pilot phase chronology is invalid.")
    case_evidence: list[dict[str, Any]] = []
    replay_projection: list[dict[str, Any]] = []
    comparison_inventory = comparison.get("comparison_inventory")
    if not isinstance(comparison_inventory, list):
        raise ValueError("Pilot comparison inventory is absent.")
    for inventory_item in comparison_inventory:
        if not isinstance(inventory_item, dict):
            raise ValueError("Pilot comparison inventory entry is malformed.")
        inventory_case_id = inventory_item.get("case_id")
        if not isinstance(inventory_case_id, str):
            raise ValueError("Pilot comparison inventory case identity is malformed.")
        record = _self_digested(
            _inventory_record(
                root / "comparison",
                comparison_inventory,
                case_id=inventory_case_id,
                label="pilot comparison",
            ),
            "comparison_digest",
            "pilot comparison",
        )
        case_id = str(record.get("case_id"))
        assignment, case = pair_by_id.get(case_id, ({}, {}))
        expected_binding = {
            "assignment_digest": assignments["assignment_digest"],
            "block": "pilot",
            "provider_slot": provider_slot,
            "assignment_position": assignment.get("assignment_position"),
            "case_id": assignment.get("case_id"),
            "target_packet": assignment.get("target_packet"),
        }
        required_flags = (
            record.get("state_matches") is True
            and record.get("reason_codes_match") is True
            and record.get("validation_matches") is True
            and record.get("binding_matches") is True
        )
        if (
            record.get("artifact_kind") != "selected_result_verifier_qualification_comparison"
            or record.get("case_id") != inventory_item.get("case_id")
            or record.get("runner_freeze_digest") != runner_freeze_digest
            or record.get("assignment_binding") != expected_binding
            or record.get("expected_state") != case.get("expected_state")
            or not required_flags
        ):
            raise ValueError("Pilot comparison record is not an exact replayed opportunity.")
        oracle_proof = _inventory_record(
            root / "oracle",
            oracle.get("proof_inventory"),
            case_id=case_id,
            label="pilot oracle proof",
        )
        target_record = _inventory_record(
            root / "target",
            target.get("record_inventory"),
            case_id=case_id,
            label="pilot target record",
        )
        validation_record = _inventory_record(
            root / "validation",
            validation.get("record_inventory"),
            case_id=case_id,
            label="pilot validation record",
        )
        comparison_identity = record.get("comparison_identity")
        if not isinstance(comparison_identity, dict):
            raise ValueError("Pilot comparison has no replayable comparison identity.")
        target_identity = phase_identities["target"]
        expected_target_identity = {
            "validator_id": target_identity["actor_id"],
            "provider": target_identity["provider"],
            "execution_context_id": target_identity["execution_context_id"],
            "identity_evidence_digest": target_identity["identity_evidence_digest"],
        }
        target_derivation = target_record.get("target_derivation")
        if (
            oracle_proof.get("oracle_identity") != phase_identities["oracle"]
            or target_authorization.get("target_identity") != expected_target_identity
            or not isinstance(target_derivation, dict)
            or target_derivation.get("validator_identity") != expected_target_identity
            or validation_record.get("validation_identity") != phase_identities["validation"]
            or comparison_identity != phase_identities["comparison"]
        ):
            raise ValueError("Pilot case identities do not derive from retained launch receipts.")
        case_tree = _target_snapshot_case_root(
            root / "target",
            target,
            case_id=case_id,
        )
        rebuilt = freeze_verifier_comparison(
            case_root=case_tree,
            oracle_proof=oracle_proof,
            target_derivation=target_record,
            target_validation=validation_record,
            comparison_identity=comparison_identity,
            compared_at=str(record.get("compared_at", "")),
            assignment_manifest=assignments,
            frozen_identity_registry_digest=_frozen_identity_registry_digest(runner_freeze),
        )
        if rebuilt != record:
            raise ValueError("Pilot comparison does not replay from retained phase evidence.")
        replay_projection.append(
            _fresh_replay_case_projection(
                oracle_proof=oracle_proof,
                target_record=target_record,
                validation_record=validation_record,
                comparison_record=record,
            )
        )
        case_evidence.append(
            {
                "case_id": case_id,
                "expected_state": record["expected_state"],
                "u_cell": case.get("u_cell"),
                "construction_family": case.get("construction_family"),
                "construction_cluster": case.get("construction_cluster"),
                "binding_matches": record["binding_matches"],
                "comparison_outcome": record["comparison_outcome"],
                "comparison_digest": record["comparison_digest"],
            }
        )
    replay_projection.sort(key=lambda item: str(item["case_id"]))
    replay_projection_digest = semantic_digest(replay_projection)
    if not require_fresh_replays:
        direct_result: dict[str, Any] = {
            "provider_slot": provider_slot,
            "provider_pack_sha256": pack_digest,
            "oracle_phase_digest": oracle["oracle_phase_digest"],
            "target_phase_digest": target["target_phase_digest"],
            "validation_phase_digest": validation["validation_phase_digest"],
            "comparison_phase_digest": comparison["comparison_phase_digest"],
            "fresh_location_replay_manifest_digest": None,
            "fresh_location_replay_count": 0,
            "fresh_replay_projection": replay_projection,
            "fresh_replay_projection_digest": replay_projection_digest,
            "case_evidence": case_evidence,
        }
        direct_result["bundle_evidence_digest"] = semantic_digest(direct_result)
        return direct_result
    replay = _self_digested(
        _load_rooted(
            root,
            "replays/FRESH_LOCATION_REPLAYS.json",
            "pilot fresh-location replay manifest",
        ),
        "fresh_location_replay_manifest_digest",
        "fresh-location replay manifest",
    )
    entries = replay.get("replays")
    if (
        replay.get("artifact_kind") != "selected_result_verifier_fresh_location_replay_manifest"
        or replay.get("assignment_digest") != assignments["assignment_digest"]
        or replay.get("runner_freeze_digest") != runner_freeze_digest
        or replay.get("provider_slot") != provider_slot
        or replay.get("original_projection_digest") != replay_projection_digest
        or replay.get("qualification_authority") != "none_fresh_location_replay_only"
        or not isinstance(entries, list)
        or len(entries) != 2
        or len({str(item.get("location_id")) for item in entries if isinstance(item, dict)}) != 2
    ):
        raise ValueError("Pilot fresh-location replay evidence is incomplete.")
    replay_roots: list[Path] = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {
            "location_id",
            "path",
            "projection_digest",
        }:
            raise ValueError("Fresh-location replay entry is malformed.")
        if not isinstance(entry["location_id"], str) or not entry["location_id"]:
            raise ValueError("Fresh-location replay identity is malformed.")
        replay_root = _safe_pack_path(root, entry["path"], "fresh-location replay root")
        replay_roots.append(replay_root)
        replay_evidence = _pilot_bundle_evidence(
            replay_root,
            assignments=assignments,
            runner_freeze=runner_freeze,
            runner_freeze_digest=runner_freeze_digest,
            require_fresh_replays=False,
        )
        if (
            replay_evidence["provider_slot"] != provider_slot
            or replay_evidence["provider_pack_sha256"] != pack_digest
            or replay_evidence["fresh_replay_projection"] != replay_projection
            or replay_evidence["fresh_replay_projection_digest"] != replay_projection_digest
            or entry["projection_digest"] != replay_projection_digest
        ):
            raise ValueError("Fresh-location replay records are not canonically identical.")
    identities = [(item.stat().st_dev, item.stat().st_ino) for item in [root, *replay_roots]]
    if len(set(identities)) != 3:
        raise ValueError("Fresh-location replay roots are not physically distinct directories.")
    result: dict[str, Any] = {
        "provider_slot": provider_slot,
        "provider_pack_sha256": pack_digest,
        "oracle_phase_digest": oracle["oracle_phase_digest"],
        "target_phase_digest": target["target_phase_digest"],
        "validation_phase_digest": validation["validation_phase_digest"],
        "comparison_phase_digest": comparison["comparison_phase_digest"],
        "fresh_location_replay_manifest_digest": replay["fresh_location_replay_manifest_digest"],
        "fresh_location_replay_count": len(entries),
        "fresh_replay_projection": replay_projection,
        "fresh_replay_projection_digest": replay_projection_digest,
        "case_evidence": case_evidence,
    }
    result["bundle_evidence_digest"] = semantic_digest(result)
    return result


def _all_assigned_cases(assignments: dict[str, Any], *, block: str) -> list[dict[str, Any]]:
    blocks = assignments.get("blocks")
    if not isinstance(blocks, list):
        raise ValueError("Assignment blocks are absent.")
    selected = [item for item in blocks if isinstance(item, dict) and item.get("block") == block]
    if len(selected) != 1 or not isinstance(selected[0].get("assignments"), list):
        raise ValueError("Expected exactly one assigned qualification block.")
    return [dict(item) for item in selected[0]["assignments"] if isinstance(item, dict)]


def _identity_value(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {
        "actor_id",
        "provider",
        "execution_context_id",
        "identity_evidence_digest",
    }:
        raise ValueError(f"{label} is malformed.")
    result = {key: str(item) for key, item in value.items()}
    if not all(result.values()):
        raise ValueError(f"{label} is incomplete.")
    return result


def _safe_pack_path(pack_root: Path, raw: Any, label: str) -> Path:
    if pack_root.is_symlink() or not pack_root.is_dir():
        raise ValueError(f"{label} root must be a real non-symlink directory.")
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"{label} must be a non-empty relative path.")
    posix = PurePosixPath(raw)
    if (
        posix.is_absolute()
        or ".." in posix.parts
        or "." in posix.parts
        or "\\" in raw
        or "\x00" in raw
        or "//" in raw
        or posix.as_posix() != raw
    ):
        raise ValueError(f"{label} escapes the provider pack.")
    candidate = pack_root.joinpath(*posix.parts)
    cursor = pack_root
    for part in posix.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"{label} traverses a symbolic link.")
    return candidate


def _validate_inventory(
    phase_root: Path,
    inventory: Any,
    *,
    expected_case_ids: list[str],
    label: str,
) -> None:
    if not isinstance(inventory, list) or len(inventory) != len(expected_case_ids):
        raise ValueError(f"{label} inventory is incomplete.")
    observed_ids: list[str] = []
    with RootedReader(phase_root) as reader:
        for item in inventory:
            if not isinstance(item, dict):
                raise ValueError(f"{label} inventory entry is malformed.")
            case_id = item.get("case_id")
            if not isinstance(case_id, str):
                raise ValueError(f"{label} inventory case identity is malformed.")
            path = item.get("path")
            if not isinstance(path, str):
                raise ValueError(f"{label} inventory path is malformed.")
            rooted = reader.read(path)
            if item.get("content_digest") != rooted.content_digest:
                raise ValueError(f"{label} inventory content digest has drifted.")
            observed_ids.append(case_id)
    if observed_ids != expected_case_ids or len(set(observed_ids)) != len(observed_ids):
        raise ValueError(f"{label} inventory does not follow frozen assignment order.")


def _inventory_record(
    phase_root: Path,
    inventory: Any,
    *,
    case_id: str,
    label: str,
) -> dict[str, Any]:
    if not isinstance(inventory, list):
        raise ValueError(f"{label} inventory is absent.")
    matches = [
        item for item in inventory if isinstance(item, dict) and item.get("case_id") == case_id
    ]
    if len(matches) != 1 or not isinstance(matches[0].get("path"), str):
        raise ValueError(f"{label} inventory does not uniquely bind the case.")
    with RootedReader(phase_root) as reader:
        rooted = reader.read(str(matches[0]["path"]))
    if matches[0].get("content_digest") != rooted.content_digest:
        raise ValueError(f"{label} inventory record bytes have drifted.")
    value = json.loads(rooted.data)
    if rooted.data != (canonical_json(value) + "\n").encode("utf-8"):
        raise ValueError(f"{label} inventory record is not canonical JSON.")
    if not isinstance(value, dict):
        raise ValueError(f"{label} record is not one JSON object.")
    return value


def _target_snapshot_case_root(
    phase_root: Path,
    target_manifest: dict[str, Any],
    *,
    case_id: str,
) -> Path:
    release_ref = target_manifest.get("target_release_manifest")
    if not isinstance(release_ref, dict) or not isinstance(release_ref.get("path"), str):
        raise ValueError("Target phase has no retained release manifest.")
    with RootedReader(phase_root) as reader:
        rooted = reader.read(str(release_ref["path"]))
    if release_ref.get("content_digest") != rooted.content_digest:
        raise ValueError("Target release-manifest bytes have drifted.")
    release = json.loads(rooted.data)
    if not isinstance(release, dict):
        raise ValueError("Target release manifest is not one JSON object.")
    release = _self_digested(
        release,
        "target_release_manifest_digest",
        "target release manifest",
    )
    authorization_ref = target_manifest.get("target_authorization")
    if not isinstance(authorization_ref, dict):
        raise ValueError("Target phase has no retained authorization reference.")
    entries = release.get("snapshot_inventory")
    matches = (
        [item for item in entries if isinstance(item, dict) and item.get("case_id") == case_id]
        if isinstance(entries, list)
        else []
    )
    if (
        release_ref.get("target_release_manifest_digest")
        != release["target_release_manifest_digest"]
        or release.get("release_gate_digest") != target_manifest.get("release_gate_digest")
        or release.get("target_authorization_digest")
        != authorization_ref.get("target_authorization_digest")
        or len(matches) != 1
        or not isinstance(matches[0].get("snapshot_path"), str)
    ):
        raise ValueError("Target release manifest does not bind one exact case snapshot.")
    return _safe_pack_path(
        phase_root,
        f"control/snapshots/{matches[0]['snapshot_path']}",
        "target case-snapshot path",
    )


def _validated_target_authorization_contract(
    runner_freeze: dict[str, Any],
) -> dict[str, Any]:
    from sc_referee_evaluation.selected_result_qualification_target_worker import (
        TARGET_AUTHORIZATION_FIELD_PROJECTION_DIGEST,
        TARGET_AUTHORIZATION_FORBIDDEN_FIELD_NAME_FRAGMENTS,
        TARGET_AUTHORIZATION_SCHEMA_CONTENT_DIGEST,
        TARGET_AUTHORIZATION_SCHEMA_DIGEST,
        TARGET_AUTHORIZATION_VERSION,
        load_target_authorization_schema,
    )

    contract = runner_freeze.get("target_authorization_contract")
    expected_contract = {
        "authorization_version": TARGET_AUTHORIZATION_VERSION,
        "schema_content_digest": TARGET_AUTHORIZATION_SCHEMA_CONTENT_DIGEST,
        "schema_semantic_digest": TARGET_AUTHORIZATION_SCHEMA_DIGEST,
        "field_projection_digest": TARGET_AUTHORIZATION_FIELD_PROJECTION_DIGEST,
        "recursively_forbidden_field_name_fragments": list(
            TARGET_AUTHORIZATION_FORBIDDEN_FIELD_NAME_FRAGMENTS
        ),
    }
    load_target_authorization_schema()
    if contract != expected_contract:
        raise ValueError("Target authorization contract does not replay the installed worker.")
    return expected_contract


def _validate_target_phase_bundle(
    phase_root: Path,
    target_manifest: dict[str, Any],
    *,
    expected_case_ids: list[str],
    runner_freeze: dict[str, Any],
) -> dict[str, Any]:
    from sc_referee_evaluation.selected_result_qualification_target_worker import (
        TARGET_WORKER_VERSION,
        validate_target_authorization,
    )

    _validated_target_authorization_contract(runner_freeze)
    authorization_ref = target_manifest.get("target_authorization")
    worker_ref = target_manifest.get("target_worker_manifest")
    if (
        not isinstance(authorization_ref, dict)
        or not isinstance(authorization_ref.get("path"), str)
        or not isinstance(worker_ref, dict)
        or not isinstance(worker_ref.get("path"), str)
    ):
        raise ValueError("Target phase lacks its authorization or worker manifest.")
    authorization_value, authorization_content_digest = _load_rooted_with_digest(
        phase_root,
        str(authorization_ref["path"]),
        "target authorization",
    )
    authorization = validate_target_authorization(authorization_value)
    identity_registry = _validated_frozen_identity_registry(runner_freeze)
    phase_identity = _manifest_phase_identity(
        target_manifest,
        phase="run-targets",
        runner_freeze_digest=str(target_manifest.get("runner_freeze_digest", "")),
        assignment_digest=str(target_manifest.get("assignment_digest", "")),
        identity_registry=identity_registry,
    )
    expected_target_identity = {
        "validator_id": phase_identity["actor_id"],
        "provider": phase_identity["provider"],
        "execution_context_id": phase_identity["execution_context_id"],
        "identity_evidence_digest": phase_identity["identity_evidence_digest"],
    }
    worker_value, worker_content_digest = _load_rooted_with_digest(
        phase_root,
        str(worker_ref["path"]),
        "target-worker manifest",
    )
    worker = _self_digested(
        worker_value,
        "target_worker_manifest_digest",
        "target-worker manifest",
    )
    if (
        authorization_ref.get("content_digest") != authorization_content_digest
        or authorization_ref.get("target_authorization_digest")
        != authorization["target_authorization_digest"]
        or worker_ref.get("content_digest") != worker_content_digest
        or worker_ref.get("target_worker_manifest_digest")
        != worker["target_worker_manifest_digest"]
        or authorization.get("assignment_digest") != target_manifest.get("assignment_digest")
        or authorization.get("runner_freeze_digest") != target_manifest.get("runner_freeze_digest")
        or authorization.get("release_gate_digest") != target_manifest.get("release_gate_digest")
        or authorization.get("block") != target_manifest.get("block")
        or authorization.get("provider_slot") != target_manifest.get("provider_slot")
        or authorization.get("target_identity") != expected_target_identity
        or [str(item.get("case_id")) for item in authorization["cases"]] != expected_case_ids
        or worker.get("target_worker_version") != TARGET_WORKER_VERSION
        or worker.get("assignment_digest") != authorization["assignment_digest"]
        or worker.get("runner_freeze_digest") != authorization["runner_freeze_digest"]
        or worker.get("release_gate_digest") != authorization["release_gate_digest"]
        or worker.get("target_authorization_digest") != authorization["target_authorization_digest"]
        or worker.get("project_code_executed") is not False
    ):
        raise ValueError("Target phase authorization and worker chain does not replay.")
    worker_inventory = worker.get("record_inventory")
    _validate_inventory(
        phase_root / "results" / "worker-output",
        worker_inventory,
        expected_case_ids=expected_case_ids,
        label="target-worker record",
    )
    if not isinstance(worker_inventory, list):
        raise ValueError("Target-worker record inventory is absent.")
    expected_inventory = [
        {**item, "path": f"results/worker-output/{item['path']}"}
        for item in worker_inventory
        if isinstance(item, dict)
    ]
    isolation = runner_freeze.get("isolation_backend")
    if not isinstance(isolation, dict):
        raise ValueError("Target phase runner isolation lock is absent.")
    runtime = isolation.get("runtime_executable")
    if not isinstance(runtime, dict):
        raise ValueError("Target phase runner runtime lock is absent.")
    target_runtime = isolation.get("target_runtime_manifest")
    release_ref = target_manifest.get("target_release_manifest")
    if not isinstance(target_runtime, dict) or not isinstance(release_ref, dict):
        raise ValueError("Target phase runtime or release evidence is absent.")
    release_value, release_content_digest = _load_rooted_with_digest(
        phase_root,
        str(release_ref.get("path", "")),
        "target release manifest",
    )
    release = _self_digested(
        release_value,
        "target_release_manifest_digest",
        "target release manifest",
    )
    expected_isolation_receipt = {
        "isolation_receipt_version": "1.0.0",
        "runtime_profile": isolation["runtime_profile"],
        "runtime_content_digest": runtime["content_digest"],
        "runtime_version_output": runtime["version_output"],
        "image_digest": isolation["image_digest"],
        "rootless_probe_output": "true",
        "image_probe_output": isolation["image_digest"],
        "target_runtime_manifest_digest": target_runtime["target_runtime_manifest_digest"],
        "target_runtime_manifest_content_digest": target_runtime["content_digest"],
        "target_runtime_probe_command_profile": target_runtime["probe_command_profile"],
        "target_worker_command_profile": "rootless-oci-target-worker-v1",
        "environment": _TARGET_OCI_ENVIRONMENT,
        "mount_projection": [
            "target_authorization:ro",
            "case_snapshots:ro",
            "output:rw",
        ],
        "target_authorization_content_digest": authorization_content_digest,
        "snapshot_inventory_digest": release.get("snapshot_inventory_digest"),
        "network": "none",
        "root_filesystem": "read_only",
        "uid": "non_root",
        "capabilities": "drop_all",
        "no_new_privileges": True,
        "pid_limit": 64,
        "temporary_filesystem": "tmpfs:/tmp:noexec,nosuid,nodev,size=16m",
        "unsafe_fallback_used": False,
    }
    if (
        release_ref.get("content_digest") != release_content_digest
        or release_ref.get("target_release_manifest_digest")
        != release.get("target_release_manifest_digest")
        or target_manifest.get("record_inventory") != expected_inventory
        or target_manifest.get("record_count") != len(expected_inventory)
        or target_manifest.get("uncontrolled_failure_count")
        != worker.get("uncontrolled_failure_count")
        or target_manifest.get("phase_completed_at") != worker.get("phase_completed_at")
        or target_manifest.get("isolation_receipt") != expected_isolation_receipt
    ):
        raise ValueError("Target phase wrapper does not replay the isolated worker output.")
    for case_id in expected_case_ids:
        _target_snapshot_case_root(phase_root, target_manifest, case_id=case_id)
        target_record = _inventory_record(
            phase_root,
            target_manifest.get("record_inventory"),
            case_id=case_id,
            label="target record",
        )
        derivation = target_record.get("target_derivation")
        retained_identity = (
            derivation.get("validator_identity")
            if isinstance(derivation, dict)
            else target_record.get("target_identity")
        )
        if retained_identity != expected_target_identity:
            raise ValueError("Target record identity does not derive from its launch receipt.")
    return authorization


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Qualification phase timestamps require timezones.")
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _identity(arguments: argparse.Namespace) -> dict[str, str]:
    receipt = getattr(arguments, "launch_receipt", None)
    if not isinstance(receipt, dict):
        raise ValueError("Qualification phase has no trusted launcher receipt.")
    return _identity_from_launch_receipt(receipt)


def _identity_from_launch_receipt(receipt: dict[str, Any]) -> dict[str, str]:
    return {
        "actor_id": str(receipt["actor_id"]),
        "provider": str(receipt["provider"]),
        "execution_context_id": str(receipt["execution_context_id"]),
        "identity_evidence_digest": semantic_digest(receipt),
    }


def _validated_launch_receipt(
    value: Any,
    *,
    phase: str,
    block: str,
    provider_slot: str,
    runner_freeze_digest: str,
    assignment_digest: str,
    identity_registry: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Qualification must be started by the trusted pre-import launcher.")
    try:
        receipt = validate_registrar_signed_receipt(
            value,
            registry=identity_registry,
            expected_kind="qualification_phase_launch_receipt",
        )
    except ValueError as error:
        raise ValueError(
            f"Qualification phase launch receipt is not registrar-authenticated: {error}"
        ) from error
    if (
        set(receipt)
        != {
            "artifact_kind",
            "receipt_version",
            "identity_registry_digest",
            "registrar_id",
            "runner_freeze_digest",
            "assignment_digest",
            "phase",
            "block",
            "provider_slot",
            "actor_id",
            "provider",
            "execution_context_id",
            "session_nonce",
            "event_index",
            "predecessor_artifact_digest",
            "issued_at",
            "qualification_authority",
            "signature_base64",
        }
        or receipt.get("artifact_kind") != "qualification_phase_launch_receipt"
        or receipt.get("receipt_version") != SESSION_RECEIPT_VERSION
        or receipt.get("identity_registry_digest")
        != identity_registry.get("identity_registry_digest")
        or receipt.get("registrar_id") != identity_registry.get("registrar_id")
        or receipt.get("runner_freeze_digest") != runner_freeze_digest
        or receipt.get("assignment_digest") != assignment_digest
        or receipt.get("phase") != phase
        or receipt.get("block") != block
        or receipt.get("provider_slot") != provider_slot
        or receipt.get("actor_id") != f"qualification-role:{phase}"
        or receipt.get("provider") != "trusted-pre-import-launcher"
        or receipt.get("execution_context_id")
        != f"qualification-context:{receipt.get('session_nonce')}"
        or receipt.get("qualification_authority") != "none_phase_launch_receipt_only"
        or not isinstance(receipt.get("session_nonce"), str)
        or not str(receipt["session_nonce"])
        or not isinstance(receipt.get("event_index"), int)
        or isinstance(receipt.get("event_index"), bool)
        or int(receipt["event_index"]) < 0
    ):
        raise ValueError("Trusted launcher receipt does not bind this qualification phase.")
    _require_sha256_digest(
        receipt.get("predecessor_artifact_digest"),
        "phase predecessor artifact digest",
    )
    _timestamp(str(receipt["issued_at"]))
    return receipt


def _manifest_phase_identity(
    manifest: dict[str, Any],
    *,
    phase: str,
    runner_freeze_digest: str,
    assignment_digest: str,
    identity_registry: dict[str, Any],
) -> dict[str, str]:
    receipt = _validated_launch_receipt(
        manifest.get("phase_launch_receipt"),
        phase=phase,
        block=str(manifest.get("block", "")),
        provider_slot=str(manifest.get("provider_slot", "")),
        runner_freeze_digest=runner_freeze_digest,
        assignment_digest=assignment_digest,
        identity_registry=identity_registry,
    )
    return _identity_from_launch_receipt(receipt)


def _require_launch_predecessor(arguments: argparse.Namespace, digest: Any) -> None:
    expected = _require_sha256_digest(digest, "phase predecessor artifact digest")
    receipt = getattr(arguments, "launch_receipt", None)
    if not isinstance(receipt, dict) or receipt.get("predecessor_artifact_digest") != expected:
        raise ValueError("Phase-launch receipt does not bind the exact predecessor artifact.")


def _assigned_cases(
    assignments: dict[str, Any], *, block: str, provider_slot: str
) -> list[dict[str, Any]]:
    blocks = assignments.get("blocks")
    if not isinstance(blocks, list):
        raise ValueError("Assignment blocks are absent.")
    selected = [item for item in blocks if isinstance(item, dict) and item.get("block") == block]
    if len(selected) != 1 or not isinstance(selected[0].get("assignments"), list):
        raise ValueError("Expected exactly one assigned qualification block.")
    result = [
        item
        for item in selected[0]["assignments"]
        if isinstance(item, dict) and item.get("provider_slot") == provider_slot
    ]
    if len(result) != 24:
        raise ValueError("Expected exactly 24 assignments for one provider-family slot.")
    return result


def _pack_cases(pack: dict[str, Any]) -> list[dict[str, Any]]:
    cases = pack.get("cases")
    if (
        not isinstance(cases, list)
        or len(cases) != 24
        or not all(isinstance(item, dict) for item in cases)
    ):
        raise ValueError("Provider pack must retain exactly 24 ordered cases.")
    return cases


def _verify_pack_seal(pack_root: Path, pack: dict[str, Any]) -> str:
    with RootedReader(pack_root) as reader:
        payload = reader.read_bytes("pack-manifest.json")
        seal_payload = reader.read_bytes("pack-manifest.sha256")
    digest = hashlib.sha256(payload).hexdigest()
    try:
        seal = seal_payload.decode("ascii").strip().split()[0]
    except (UnicodeDecodeError, IndexError) as error:
        raise ValueError("Provider pack manifest seal is malformed.") from error
    if seal != digest:
        raise ValueError("Provider pack manifest seal does not replay.")
    semantic_basis = dict(pack)
    semantic_seal = semantic_basis.pop("manifest_self_digest", None)
    if semantic_seal != semantic_digest(semantic_basis):
        raise ValueError("Provider pack semantic self-digest does not replay.")
    if pack.get("replacement_permitted") is not False or pack.get("case_count") != 24:
        raise ValueError("Provider pack replacement or case-count contract drifted.")
    return digest


def _ordered_pairs(
    assignments: dict[str, Any],
    pack: dict[str, Any],
    *,
    block: str,
    provider_slot: str,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    assigned = _assigned_cases(assignments, block=block, provider_slot=provider_slot)
    cases = _pack_cases(pack)
    _validate_provider_pack_contract(
        pack,
        cases,
        block=block,
        provider_slot=provider_slot,
    )
    pairs = list(zip(assigned, cases, strict=True))
    for assignment, case in pairs:
        packet = assignment.get("target_packet")
        if (
            not isinstance(packet, dict)
            or case.get("case_id") != assignment.get("case_id")
            or case.get("assignment_position") != assignment.get("assignment_position")
            or case.get("selected_report_path") != packet.get("selected_report_path")
            or case.get("provider_slot") != provider_slot
        ):
            raise ValueError("Provider pack does not follow the frozen assignment order.")
    return pairs


def _validate_provider_pack_contract(
    pack: dict[str, Any],
    cases: list[dict[str, Any]],
    *,
    block: str,
    provider_slot: str,
) -> None:
    author = pack.get("author_identity")
    if (
        pack.get("block") != block
        or pack.get("provider_slot") != provider_slot
        or pack.get("replacement_permitted") is not False
        or not isinstance(author, dict)
        or author.get("provider") != pack.get("provider_family")
    ):
        raise ValueError("Provider pack identity or authorship contract has drifted.")
    state_counts = {state: 0 for state in ("V", "A", "I", "U")}
    u_cells = {
        "dynamic_or_opaque_structure": 0,
        "role_or_source_artifact_boundary": 0,
        "encoding_newline_or_runtime_boundary": 0,
        "syntax_value_or_finite_budget_boundary": 0,
        "mode_or_role_boundary": 0,
    }
    families: dict[str, int] = {}
    clusters: dict[str, set[str]] = {state: set() for state in state_counts}
    for case in cases:
        state = case.get("expected_state")
        family = case.get("construction_family")
        cluster = case.get("construction_cluster")
        if (
            state not in state_counts
            or not isinstance(family, str)
            or not family
            or not isinstance(cluster, str)
            or not cluster
        ):
            raise ValueError("Provider case diversity metadata is malformed.")
        state_counts[str(state)] += 1
        families[family] = families.get(family, 0) + 1
        clusters[str(state)].add(cluster)
        if state == "U":
            cell = case.get("u_cell")
            if cell not in u_cells:
                raise ValueError("Provider U case has no registered U cell.")
            u_cells[str(cell)] += 1
        elif case.get("u_cell") is not None:
            raise ValueError("Only U cases may carry a U-cell label.")
    if (
        state_counts != {"V": 6, "A": 4, "I": 4, "U": 10}
        or u_cells != {key: 2 for key in u_cells}
        or any(count > 12 for count in families.values())
        or any(len(values) < 2 for values in clusters.values())
        or pack.get("state_counts") != state_counts
        or pack.get("u_cell_counts") != u_cells
    ):
        raise ValueError("Provider pack state, cell, family, or cluster quotas have drifted.")


def _target_projection_pairs(
    assignments: dict[str, Any],
    projection: dict[str, Any],
    *,
    block: str,
    provider_slot: str,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    projection = _self_digested(
        projection,
        "target_input_projection_digest",
        "target-input projection",
    )
    if (
        projection.get("artifact_kind") != "selected_result_verifier_target_input_projection"
        or projection.get("block") != block
        or projection.get("provider_slot") != provider_slot
        or projection.get("assignment_digest") != assignments["assignment_digest"]
        or projection.get("case_count") != 24
        or projection.get("oracle_fields_present") is not False
        or projection.get("qualification_authority") != "none_target_input_projection_only"
    ):
        raise ValueError("Target-input projection identity has drifted.")
    cases = projection.get("cases")
    if not isinstance(cases, list) or len(cases) != 24:
        raise ValueError("Target-input projection is incomplete.")
    assigned = _assigned_cases(assignments, block=block, provider_slot=provider_slot)
    pairs = list(zip(assigned, cases, strict=True))
    for assignment, case in pairs:
        if not isinstance(case, dict) or set(case) != {
            "case_id",
            "assignment_position",
            "snapshot_path",
            "snapshot_tree_digest",
            "file_count",
            "total_bytes",
            "target_packet",
        }:
            raise ValueError("Target-input projection entry is malformed.")
        if (
            case["case_id"] != assignment.get("case_id")
            or case["assignment_position"] != assignment.get("assignment_position")
            or case["target_packet"] != assignment.get("target_packet")
        ):
            raise ValueError("Target-input projection does not replay the assignment.")
        canonical_relative_path(str(case["snapshot_path"]))
        _require_sha256_digest(case["snapshot_tree_digest"], "snapshot_tree_digest")
        if (
            not isinstance(case["file_count"], int)
            or isinstance(case["file_count"], bool)
            or not 1 <= case["file_count"] <= 32
            or not isinstance(case["total_bytes"], int)
            or isinstance(case["total_bytes"], bool)
            or not 0 <= case["total_bytes"] <= 50 * 1024 * 1024
        ):
            raise ValueError("Target-input projection snapshot bounds are malformed.")
    return pairs


def _semantic_reconciliations_for_case(
    panel_root: Path,
    manifest: dict[str, Any],
    *,
    case_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cases = manifest.get("cases")
    if not isinstance(cases, list):
        raise ValueError("Semantic-panel cases are absent.")
    matches = [item for item in cases if isinstance(item, dict) and item.get("case_id") == case_id]
    if len(matches) != 1:
        raise ValueError("Semantic-panel case binding is not unique.")
    case_entry = matches[0]
    references = case_entry.get("reconciliations")
    if not isinstance(references, list) or len(references) != 2:
        raise ValueError("Each case requires exactly two semantic reconciliations.")
    result: list[dict[str, Any]] = []
    for reference in references:
        if not isinstance(reference, dict):
            raise ValueError("Semantic-reconciliation reference is malformed.")
        relative = reference.get("path")
        if not isinstance(relative, str):
            raise ValueError("Semantic-reconciliation path is malformed.")
        record, content_digest = _load_rooted_with_digest(
            panel_root,
            relative,
            "semantic reconciliation",
        )
        if reference.get("content_digest") != content_digest:
            raise ValueError("Semantic-reconciliation bytes have drifted.")
        if reference.get("semantic_reconciliation_digest") != record.get(
            "semantic_reconciliation_digest"
        ):
            raise ValueError("Semantic-reconciliation digest binding has drifted.")
        result.append(record)
    reveal_reference = case_entry.get("certificate_reveal_evidence")
    if not isinstance(reveal_reference, dict) or not isinstance(reveal_reference.get("path"), str):
        raise ValueError("Semantic-panel case has no certificate-reveal evidence.")
    reveal, reveal_content_digest = _load_rooted_with_digest(
        panel_root,
        str(reveal_reference["path"]),
        "certificate reveal evidence",
    )
    if reveal_reference.get("content_digest") != reveal_content_digest or reveal_reference.get(
        "reveal_evidence_digest"
    ) != reveal.get("reveal_evidence_digest"):
        raise ValueError("Certificate-reveal evidence binding has drifted.")
    return result, reveal


def freeze_oracle_phase(arguments: argparse.Namespace) -> dict[str, Any]:
    if arguments.output.exists() or arguments.output.is_symlink():
        raise FileExistsError(f"Oracle phase output already exists: {arguments.output}")
    assignments = _validated_assignments(arguments.assignments)
    pack = _load_rooted(arguments.pack_root, "pack-manifest.json", "provider pack manifest")
    pack_digest = _verify_pack_seal(arguments.pack_root, pack)
    if pack.get("assignment_manifest_digest") != assignments.get("assignment_digest"):
        raise ValueError("Provider pack assignment digest has drifted.")
    pairs = _ordered_pairs(
        assignments,
        pack,
        block=arguments.block,
        provider_slot=arguments.provider_slot,
    )
    expected_case_ids = [str(assignment["case_id"]) for assignment, _case in pairs]
    author_identity = pack.get("author_identity")
    if not isinstance(author_identity, dict):
        raise ValueError("Provider pack author identity is absent.")
    semantic_manifest = _self_digested(
        _load_rooted(
            arguments.semantic_panel,
            "SEMANTIC_PANEL_MANIFEST.json",
            "semantic-panel manifest",
        ),
        "semantic_panel_manifest_digest",
        "semantic-panel manifest",
    )
    if (
        semantic_manifest.get("artifact_kind") != "selected_result_verifier_semantic_panel_manifest"
        or semantic_manifest.get("assignment_digest") != assignments["assignment_digest"]
        or semantic_manifest.get("runner_freeze_digest") != arguments.runner_freeze_digest
        or semantic_manifest.get("block") != arguments.block
        or semantic_manifest.get("provider_slot") != arguments.provider_slot
        or semantic_manifest.get("pack_manifest_sha256") != pack_digest
        or semantic_manifest.get("case_count") != 24
        or semantic_manifest.get("blind_review_count") != 48
        or semantic_manifest.get("reconciliation_count") != 48
        or semantic_manifest.get("blind_barrier_sealed") is not True
        or semantic_manifest.get("certificate_reveal_after_blind_barrier") is not True
        or semantic_manifest.get("target_outputs_present") is not False
    ):
        raise ValueError("Semantic-panel manifest does not bind this provider pack.")
    _require_launch_predecessor(
        arguments,
        semantic_manifest.get("semantic_panel_manifest_digest"),
    )
    contract_ref = semantic_manifest.get("semantic_contract")
    registry_ref = semantic_manifest.get("identity_registry")
    if not isinstance(contract_ref, dict) or not isinstance(registry_ref, dict):
        raise ValueError("Semantic panel lacks its contract or identity registry.")
    if not isinstance(contract_ref.get("path"), str) or not isinstance(
        registry_ref.get("path"), str
    ):
        raise ValueError("Semantic-panel contract or registry path is malformed.")
    semantic_contract, contract_content_digest = _load_rooted_with_digest(
        arguments.semantic_panel,
        str(contract_ref["path"]),
        "semantic contract",
    )
    identity_registry, registry_content_digest = _load_rooted_with_digest(
        arguments.semantic_panel,
        str(registry_ref["path"]),
        "identity registry",
    )
    if (
        contract_ref.get("content_digest") != contract_content_digest
        or registry_ref.get("content_digest") != registry_content_digest
    ):
        raise ValueError("Semantic-panel contract or identity-registry bytes have drifted.")
    contract_ref = assignments.get("semantic_review_contract_ref")
    runner_freeze = getattr(arguments, "runner_freeze_record", None)
    if (
        not isinstance(contract_ref, dict)
        or not isinstance(runner_freeze, dict)
        or semantic_contract.get("contract_version") != contract_ref.get("contract_version")
        or semantic_contract.get("contract_digest") != contract_ref.get("contract_digest")
        or semantic_contract.get("contract_digest") != runner_freeze.get("semantic_contract_digest")
    ):
        raise ValueError("Semantic panel does not use the exact frozen normative contract.")
    frozen_registry_ref = runner_freeze.get("identity_registry_ref")
    if (
        not isinstance(frozen_registry_ref, dict)
        or identity_registry.get("identity_registry_version")
        != frozen_registry_ref.get("identity_registry_version")
        or identity_registry.get("identity_registry_digest")
        != frozen_registry_ref.get("identity_registry_digest")
        or registry_content_digest != frozen_registry_ref.get("content_digest")
    ):
        raise ValueError("Semantic panel does not use the frozen identity registry.")
    completed = _timestamp(arguments.phase_started_at)
    arguments.output.mkdir(parents=True)
    snapshot_root = arguments.output / "case-snapshots"
    snapshot_root.mkdir()
    snapshot_by_case: dict[str, dict[str, Any]] = {}
    with RootedReader(arguments.pack_root) as pack_reader:
        for assignment, case in pairs:
            case_id = str(assignment["case_id"])
            case_tree = case.get("case_tree")
            if not isinstance(case_tree, str):
                raise ValueError("Provider case has no canonical case-tree path.")
            relative_snapshot = case_id.removeprefix("case:")
            destination = snapshot_root / relative_snapshot
            destination.mkdir()
            snapshot = pack_reader.snapshot_case_tree(case_tree, destination)
            snapshot_by_case[case_id] = {
                "snapshot_path": f"case-snapshots/{relative_snapshot}",
                "snapshot_tree_digest": snapshot["case_tree_digest"],
                "file_count": snapshot["file_count"],
                "total_bytes": snapshot["total_bytes"],
            }
    target_inputs: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_target_input_projection",
        "block": arguments.block,
        "provider_slot": arguments.provider_slot,
        "assignment_digest": assignments["assignment_digest"],
        "runner_freeze_digest": arguments.runner_freeze_digest,
        "pack_manifest_sha256": pack_digest,
        "cases": [
            {
                "case_id": assignment["case_id"],
                "assignment_position": assignment["assignment_position"],
                **snapshot_by_case[str(assignment["case_id"])],
                "target_packet": assignment["target_packet"],
            }
            for assignment, _case in pairs
        ],
        "case_count": len(pairs),
        "oracle_fields_present": False,
        "qualification_authority": "none_target_input_projection_only",
    }
    target_inputs["target_input_projection_digest"] = semantic_digest(target_inputs)
    target_input_path = arguments.output / "TARGET_INPUTS.json"
    write_normalized_json_once(target_input_path, target_inputs)
    proofs_root = arguments.output / "oracle-proofs"
    proofs_root.mkdir()
    proof_inventory: list[dict[str, Any]] = []
    with RootedReader(arguments.pack_root) as pack_reader:
        for offset, (assignment, case) in enumerate(pairs):
            case_id = str(assignment["case_id"])
            certificate_info = case.get("certificate")
            if not isinstance(certificate_info, dict) or not isinstance(
                certificate_info.get("path"), str
            ):
                raise ValueError("Provider case certificate reference is absent.")
            certificate_read = pack_reader.read(str(certificate_info["path"]))
            if certificate_read.content_digest != "sha256:" + str(certificate_info["sha256"]):
                raise ValueError("Provider certificate file digest has drifted.")
            certificate_value = json.loads(certificate_read.data)
            if not isinstance(certificate_value, dict):
                raise ValueError("Provider construction certificate is not one JSON object.")
            certificate = parse_construction_certificate(certificate_value)
            author_evidence_info = case.get("author_identity_evidence")
            if not isinstance(author_evidence_info, dict) or not isinstance(
                author_evidence_info.get("path"), str
            ):
                raise ValueError("Provider case author-session evidence is absent.")
            author_evidence_read = pack_reader.read(str(author_evidence_info["path"]))
            if author_evidence_read.content_digest != "sha256:" + str(
                author_evidence_info.get("sha256")
            ) or len(author_evidence_read.data) != author_evidence_info.get("size_bytes"):
                raise ValueError("Provider case author-session evidence bytes have drifted.")
            author_identity_evidence = json.loads(author_evidence_read.data)
            if not isinstance(author_identity_evidence, dict):
                raise ValueError("Provider case author-session evidence is not one JSON object.")
            semantic_reconciliations, certificate_reveal_evidence = (
                _semantic_reconciliations_for_case(
                    arguments.semantic_panel,
                    semantic_manifest,
                    case_id=case_id,
                )
            )
            proof = freeze_oracle_proof(
                case_root=arguments.output / snapshot_by_case[case_id]["snapshot_path"],
                certificate=certificate,
                target_packet=assignment["target_packet"],
                oracle_identity=_identity(arguments),
                completed_at=_iso(completed + timedelta(seconds=offset)),
                assignment_manifest=assignments,
                block=arguments.block,
                provider_slot=arguments.provider_slot,
                runner_freeze_digest=arguments.runner_freeze_digest,
                author_identity=author_identity,
                author_identity_evidence=author_identity_evidence,
                semantic_contract=semantic_contract,
                identity_registry=identity_registry,
                frozen_identity_registry_digest=_frozen_identity_registry_digest(runner_freeze),
                semantic_reconciliations=semantic_reconciliations,
                certificate_reveal_evidence=certificate_reveal_evidence,
            )
            output = proofs_root / f"{case_id.removeprefix('case:')}.json"
            write_normalized_json_once(output, proof)
            proof_inventory.append(
                {
                    "case_id": case_id,
                    "path": output.relative_to(arguments.output).as_posix(),
                    "content_digest": sha256_digest(output.read_bytes()),
                    "oracle_proof_digest": proof["oracle_proof_digest"],
                }
            )
    manifest: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_oracle_phase_manifest",
        "block": arguments.block,
        "provider_slot": arguments.provider_slot,
        "assignment_digest": assignments["assignment_digest"],
        "runner_freeze_digest": arguments.runner_freeze_digest,
        "pack_manifest_sha256": pack_digest,
        "semantic_panel_manifest_digest": semantic_manifest["semantic_panel_manifest_digest"],
        "case_snapshot_inventory": [
            {"case_id": case_id, **snapshot_by_case[case_id]} for case_id in expected_case_ids
        ],
        "case_snapshot_inventory_digest": semantic_digest(
            [{"case_id": case_id, **snapshot_by_case[case_id]} for case_id in expected_case_ids]
        ),
        "target_input_projection": {
            "path": target_input_path.relative_to(arguments.output).as_posix(),
            "content_digest": sha256_digest(target_input_path.read_bytes()),
            "target_input_projection_digest": target_inputs["target_input_projection_digest"],
        },
        "proof_inventory": proof_inventory,
        "proof_count": len(proof_inventory),
        "phase_launch_receipt": dict(arguments.launch_receipt),
        "phase_completed_at": _iso(completed + timedelta(seconds=len(proof_inventory))),
        "target_outputs_present": False,
        "qualification_authority": "none_oracle_phase_only",
    }
    manifest["oracle_phase_digest"] = semantic_digest(manifest)
    write_normalized_json_once(arguments.output / "ORACLE_PHASE_MANIFEST.json", manifest)
    return manifest


def run_target_phase(arguments: argparse.Namespace) -> dict[str, Any]:
    from sc_referee_evaluation.selected_result_qualification_target_worker import (
        TARGET_WORKER_VERSION,
        validate_target_authorization,
    )

    if arguments.output.exists() or arguments.output.is_symlink():
        raise FileExistsError(f"Target phase output already exists: {arguments.output}")
    assignments = _validated_assignments(arguments.assignments)
    oracle_manifest = _self_digested(
        _load_rooted(arguments.oracle_phase, "ORACLE_PHASE_MANIFEST.json", "oracle manifest"),
        "oracle_phase_digest",
        "oracle phase manifest",
    )
    projection_ref = oracle_manifest.get("target_input_projection")
    if not isinstance(projection_ref, dict):
        raise ValueError("Oracle phase did not seal a target-input projection.")
    projection_path = _safe_pack_path(
        arguments.oracle_phase,
        projection_ref.get("path"),
        "target-input projection path",
    )
    if (
        not projection_path.is_file()
        or projection_path.is_symlink()
        or projection_ref.get("content_digest") != sha256_digest(projection_path.read_bytes())
    ):
        raise ValueError("Target-input projection bytes have drifted.")
    projection = _self_digested(
        _load(projection_path),
        "target_input_projection_digest",
        "target-input projection",
    )
    if (
        projection_ref.get("target_input_projection_digest")
        != projection["target_input_projection_digest"]
        or projection.get("runner_freeze_digest") != arguments.runner_freeze_digest
    ):
        raise ValueError("Target-input projection digest binding has drifted.")
    pairs = _target_projection_pairs(
        assignments,
        projection,
        block=arguments.block,
        provider_slot=arguments.provider_slot,
    )
    pack_digest = projection.get("pack_manifest_sha256")
    if not isinstance(pack_digest, str):
        raise ValueError("Target release projection has no provider-pack commitment.")
    expected_snapshots = [
        {
            "case_id": case["case_id"],
            "snapshot_path": case["snapshot_path"],
            "snapshot_tree_digest": case["snapshot_tree_digest"],
            "file_count": case["file_count"],
            "total_bytes": case["total_bytes"],
        }
        for _assignment, case in pairs
    ]
    if (
        oracle_manifest.get("proof_count") != 24
        or oracle_manifest.get("target_outputs_present") is not False
        or oracle_manifest.get("assignment_digest") != assignments.get("assignment_digest")
        or oracle_manifest.get("runner_freeze_digest") != arguments.runner_freeze_digest
        or oracle_manifest.get("pack_manifest_sha256") != pack_digest
        or oracle_manifest.get("block") != arguments.block
        or oracle_manifest.get("provider_slot") != arguments.provider_slot
        or oracle_manifest.get("case_snapshot_inventory") != expected_snapshots
        or oracle_manifest.get("case_snapshot_inventory_digest")
        != semantic_digest(expected_snapshots)
    ):
        raise ValueError("Complete oracle phase has not frozen against this pack.")
    _require_launch_predecessor(arguments, oracle_manifest.get("oracle_phase_digest"))
    expected_case_ids = [str(assignment["case_id"]) for assignment, _ in pairs]
    _validate_inventory(
        arguments.oracle_phase,
        oracle_manifest.get("proof_inventory"),
        expected_case_ids=expected_case_ids,
        label="oracle proof",
    )
    oracle_identity = _manifest_phase_identity(
        oracle_manifest,
        phase="freeze-oracles",
        runner_freeze_digest=arguments.runner_freeze_digest,
        assignment_digest=str(assignments["assignment_digest"]),
        identity_registry=arguments.identity_registry_record,
    )
    for case_id in expected_case_ids:
        proof = _inventory_record(
            arguments.oracle_phase,
            oracle_manifest.get("proof_inventory"),
            case_id=case_id,
            label="oracle proof",
        )
        if proof.get("oracle_identity") != oracle_identity:
            raise ValueError("Oracle proof identity does not derive from its launch receipt.")
    derived = _timestamp(arguments.phase_started_at)
    if derived < _timestamp(str(oracle_manifest.get("phase_completed_at", ""))):
        raise ValueError("Target phase predates the complete oracle phase.")
    arguments.output.mkdir(parents=True)
    control_root = arguments.output / "control"
    input_root = control_root / "input"
    snapshot_root = control_root / "snapshots"
    result_parent = arguments.output / "results"
    input_root.mkdir(parents=True)
    snapshot_root.mkdir()
    result_parent.mkdir()
    snapshot_inventory: list[dict[str, Any]] = []
    authorization_cases: list[dict[str, Any]] = []
    with RootedReader(arguments.oracle_phase) as snapshot_reader:
        for offset, (assignment, case) in enumerate(pairs):
            case_id = str(assignment["case_id"])
            snapshot_path = case_id.removeprefix("case:")
            snapshot_destination = snapshot_root / snapshot_path
            snapshot_destination.mkdir()
            source_snapshot = case.get("snapshot_path")
            if not isinstance(source_snapshot, str):
                raise ValueError("Target release projection has no canonical snapshot path.")
            snapshot = snapshot_reader.snapshot_case_tree(source_snapshot, snapshot_destination)
            if (
                snapshot["case_tree_digest"] != case.get("snapshot_tree_digest")
                or snapshot["file_count"] != case.get("file_count")
                or snapshot["total_bytes"] != case.get("total_bytes")
            ):
                raise ValueError("Target release snapshot does not replay the oracle snapshot.")
            snapshot_inventory.append(
                {
                    "case_id": case_id,
                    "assignment_position": assignment["assignment_position"],
                    "snapshot_path": snapshot_path,
                    "snapshot_tree_digest": snapshot["case_tree_digest"],
                    "file_count": snapshot["file_count"],
                    "total_bytes": snapshot["total_bytes"],
                }
            )
            authorization_cases.append(
                {
                    "case_id": case_id,
                    "assignment_position": assignment["assignment_position"],
                    "snapshot_path": snapshot_path,
                    "snapshot_tree_digest": snapshot["case_tree_digest"],
                    "target_packet": assignment["target_packet"],
                    "derived_at": _iso(derived + timedelta(seconds=offset * 2)),
                    "frozen_at": _iso(derived + timedelta(seconds=offset * 2 + 1)),
                }
            )
    release_basis: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_target_release_gate",
        "block": arguments.block,
        "provider_slot": arguments.provider_slot,
        "assignment_digest": assignments["assignment_digest"],
        "runner_freeze_digest": arguments.runner_freeze_digest,
        "pack_manifest_sha256": pack_digest,
        "oracle_phase_digest": oracle_manifest["oracle_phase_digest"],
        "target_input_projection_digest": projection["target_input_projection_digest"],
        "snapshot_inventory_digest": semantic_digest(snapshot_inventory),
        "case_count": len(snapshot_inventory),
        "qualification_authority": "none_target_release_gate_only",
    }
    release_gate_digest = semantic_digest(release_basis)
    raw_identity = _identity(arguments)
    authorization: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_target_authorization",
        "authorization_version": "1.0.0",
        "block": arguments.block,
        "provider_slot": arguments.provider_slot,
        "assignment_digest": assignments["assignment_digest"],
        "runner_freeze_digest": arguments.runner_freeze_digest,
        "release_gate_digest": release_gate_digest,
        "target_identity": {
            "validator_id": raw_identity["actor_id"],
            "provider": raw_identity["provider"],
            "execution_context_id": raw_identity["execution_context_id"],
            "identity_evidence_digest": raw_identity["identity_evidence_digest"],
        },
        "cases": authorization_cases,
        "case_count": len(authorization_cases),
        "case_replacement_permitted": False,
        "qualification_authority": "none_target_release_authorization_only",
    }
    authorization["target_authorization_digest"] = semantic_digest(authorization)
    authorization = validate_target_authorization(authorization)
    authorization_path = input_root / "TARGET_AUTHORIZATION.json"
    write_canonical_json_exclusive(input_root, authorization_path.name, authorization)
    runner_freeze = getattr(arguments, "runner_freeze_record", None)
    if not isinstance(runner_freeze, dict):
        raise ValueError("Target phase has no validated runner freeze.")
    _validated_target_authorization_contract(runner_freeze)
    isolation_receipt = _run_target_worker_in_oci(
        freeze=runner_freeze,
        authorization_path=authorization_path,
        snapshot_root=snapshot_root,
        output_parent=result_parent,
        snapshot_inventory_digest=release_basis["snapshot_inventory_digest"],
    )
    worker_root = result_parent / "worker-output"
    worker_manifest = _self_digested(
        _load_rooted(worker_root, "TARGET_WORKER_MANIFEST.json", "target-worker manifest"),
        "target_worker_manifest_digest",
        "target-worker manifest",
    )
    if (
        worker_manifest.get("artifact_kind") != "selected_result_verifier_target_worker_manifest"
        or worker_manifest.get("target_worker_version") != TARGET_WORKER_VERSION
        or worker_manifest.get("block") != arguments.block
        or worker_manifest.get("provider_slot") != arguments.provider_slot
        or worker_manifest.get("assignment_digest") != assignments["assignment_digest"]
        or worker_manifest.get("runner_freeze_digest") != arguments.runner_freeze_digest
        or worker_manifest.get("release_gate_digest") != release_gate_digest
        or worker_manifest.get("target_authorization_digest")
        != authorization["target_authorization_digest"]
        or worker_manifest.get("record_count") != 24
        or worker_manifest.get("project_code_executed") is not False
    ):
        raise ValueError("Isolated target-worker manifest does not bind its release gate.")
    _validate_inventory(
        worker_root,
        worker_manifest.get("record_inventory"),
        expected_case_ids=expected_case_ids,
        label="target-worker record",
    )
    raw_inventory = worker_manifest.get("record_inventory")
    if not isinstance(raw_inventory, list):
        raise ValueError("Target-worker record inventory is absent.")
    inventory = [
        {**item, "path": f"results/worker-output/{item['path']}"}
        for item in raw_inventory
        if isinstance(item, dict)
    ]
    if len(inventory) != 24:
        raise ValueError("Target-worker record inventory is incomplete.")
    snapshot_manifest: dict[str, Any] = {
        **release_basis,
        "release_gate_digest": release_gate_digest,
        "snapshot_inventory": snapshot_inventory,
        "target_authorization_digest": authorization["target_authorization_digest"],
    }
    snapshot_manifest["target_release_manifest_digest"] = semantic_digest(snapshot_manifest)
    snapshot_manifest_path = control_root / "TARGET_RELEASE_MANIFEST.json"
    write_normalized_json_once(snapshot_manifest_path, snapshot_manifest)
    manifest: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_target_phase_manifest",
        "block": arguments.block,
        "provider_slot": arguments.provider_slot,
        "assignment_digest": assignments["assignment_digest"],
        "runner_freeze_digest": arguments.runner_freeze_digest,
        "oracle_phase_digest": oracle_manifest["oracle_phase_digest"],
        "pack_manifest_sha256": pack_digest,
        "target_input_projection_digest": projection["target_input_projection_digest"],
        "release_gate_digest": release_gate_digest,
        "target_authorization": {
            "path": authorization_path.relative_to(arguments.output).as_posix(),
            "content_digest": sha256_digest(authorization_path.read_bytes()),
            "target_authorization_digest": authorization["target_authorization_digest"],
        },
        "target_release_manifest": {
            "path": snapshot_manifest_path.relative_to(arguments.output).as_posix(),
            "content_digest": sha256_digest(snapshot_manifest_path.read_bytes()),
            "target_release_manifest_digest": snapshot_manifest["target_release_manifest_digest"],
        },
        "target_worker_manifest": {
            "path": (worker_root / "TARGET_WORKER_MANIFEST.json")
            .relative_to(arguments.output)
            .as_posix(),
            "content_digest": sha256_digest(
                (worker_root / "TARGET_WORKER_MANIFEST.json").read_bytes()
            ),
            "target_worker_manifest_digest": worker_manifest["target_worker_manifest_digest"],
        },
        "isolation_receipt": isolation_receipt,
        "record_inventory": inventory,
        "record_count": len(inventory),
        "phase_launch_receipt": dict(arguments.launch_receipt),
        "uncontrolled_failure_count": sum(
            item["record_kind"] == "uncontrolled_failure" for item in inventory
        ),
        "phase_completed_at": worker_manifest["phase_completed_at"],
        "qualification_authority": "none_target_phase_only",
    }
    _validate_target_phase_bundle(
        arguments.output,
        manifest,
        expected_case_ids=expected_case_ids,
        runner_freeze=runner_freeze,
    )
    manifest["target_phase_digest"] = semantic_digest(manifest)
    write_normalized_json_once(arguments.output / "TARGET_PHASE_MANIFEST.json", manifest)
    return manifest


def run_validation_phase(arguments: argparse.Namespace) -> dict[str, Any]:
    if arguments.output.exists() or arguments.output.is_symlink():
        raise FileExistsError(f"Validation phase output already exists: {arguments.output}")
    assignments = _validated_assignments(arguments.assignments)
    pack = _load_rooted(arguments.pack_root, "pack-manifest.json", "provider pack manifest")
    pack_digest = _verify_pack_seal(arguments.pack_root, pack)
    pairs = _ordered_pairs(
        assignments,
        pack,
        block=arguments.block,
        provider_slot=arguments.provider_slot,
    )
    target_manifest = _self_digested(
        _load_rooted(arguments.target_phase, "TARGET_PHASE_MANIFEST.json", "target manifest"),
        "target_phase_digest",
        "target phase manifest",
    )
    expected_case_ids = [str(assignment["case_id"]) for assignment, _ in pairs]
    if (
        target_manifest.get("block") != arguments.block
        or target_manifest.get("provider_slot") != arguments.provider_slot
        or target_manifest.get("assignment_digest") != assignments["assignment_digest"]
        or target_manifest.get("runner_freeze_digest") != arguments.runner_freeze_digest
        or target_manifest.get("pack_manifest_sha256") != pack_digest
        or target_manifest.get("record_count") != 24
    ):
        raise ValueError("Validation phase does not bind the complete target phase.")
    _require_launch_predecessor(arguments, target_manifest.get("target_phase_digest"))
    _validate_inventory(
        arguments.target_phase,
        target_manifest.get("record_inventory"),
        expected_case_ids=expected_case_ids,
        label="target record",
    )
    runner_freeze = getattr(arguments, "runner_freeze_record", None)
    if not isinstance(runner_freeze, dict):
        raise ValueError("Validation phase has no validated runner freeze.")
    _validate_target_phase_bundle(
        arguments.target_phase,
        target_manifest,
        expected_case_ids=expected_case_ids,
        runner_freeze=runner_freeze,
    )
    started = _timestamp(arguments.phase_started_at)
    if started < _timestamp(str(target_manifest.get("phase_completed_at", ""))):
        raise ValueError("Validation phase predates the complete target phase.")
    arguments.output.mkdir(parents=True)
    records_root = arguments.output / "validation-records"
    records_root.mkdir()
    inventory: list[dict[str, Any]] = []
    for offset, (assignment, case) in enumerate(pairs):
        case_id = str(assignment["case_id"])
        name = f"{case_id.removeprefix('case:')}.json"
        target_record = _inventory_record(
            arguments.target_phase,
            target_manifest.get("record_inventory"),
            case_id=case_id,
            label="target record",
        )
        contract_info = case.get("case_contract")
        if not isinstance(contract_info, dict) or not isinstance(contract_info.get("path"), str):
            raise ValueError("Provider case contract reference is absent.")
        case_contract, contract_digest = _load_rooted_with_digest(
            arguments.pack_root,
            str(contract_info["path"]),
            "provider case contract",
        )
        if contract_digest != "sha256:" + str(contract_info.get("sha256")):
            raise ValueError("Provider case-contract bytes have drifted.")
        record_path = records_root / name
        try:
            record = freeze_qualification_validation(
                case_root=_target_snapshot_case_root(
                    arguments.target_phase,
                    target_manifest,
                    case_id=case_id,
                ),
                case_contract=case_contract,
                qualification_target_output=target_record,
                assignment_manifest=assignments,
                validation_identity=_identity(arguments),
                declaration_revealed_at=_iso(started + timedelta(seconds=offset * 2)),
                compared_at=_iso(started + timedelta(seconds=offset * 2 + 1)),
            )
            record_kind = "validation"
        except Exception as error:
            record = {
                "artifact_kind": "selected_result_verifier_uncontrolled_validation_failure",
                "case_id": case_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "qualification_outcome": "uncontrolled_failure",
                "completed_at": _iso(started + timedelta(seconds=offset * 2 + 1)),
                "qualification_authority": "none_validation_failure_only",
            }
            record["failure_digest"] = semantic_digest(record)
            record_kind = "uncontrolled_failure"
        write_normalized_json_once(record_path, record)
        inventory.append(
            {
                "case_id": case_id,
                "path": record_path.relative_to(arguments.output).as_posix(),
                "record_kind": record_kind,
                "content_digest": sha256_digest(record_path.read_bytes()),
            }
        )
    manifest: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_validation_phase_manifest",
        "block": arguments.block,
        "provider_slot": arguments.provider_slot,
        "assignment_digest": assignments["assignment_digest"],
        "runner_freeze_digest": arguments.runner_freeze_digest,
        "pack_manifest_sha256": pack_digest,
        "target_phase_digest": target_manifest["target_phase_digest"],
        "record_inventory": inventory,
        "record_count": len(inventory),
        "phase_launch_receipt": dict(arguments.launch_receipt),
        "uncontrolled_failure_count": sum(
            item["record_kind"] == "uncontrolled_failure" for item in inventory
        ),
        "phase_completed_at": _iso(started + timedelta(seconds=len(inventory) * 2)),
        "qualification_authority": "none_validation_phase_only",
    }
    manifest["validation_phase_digest"] = semantic_digest(manifest)
    write_normalized_json_once(arguments.output / "VALIDATION_PHASE_MANIFEST.json", manifest)
    return manifest


def compare_phase(arguments: argparse.Namespace) -> dict[str, Any]:
    if arguments.output.exists() or arguments.output.is_symlink():
        raise FileExistsError(f"Comparison output already exists: {arguments.output}")
    assignments = _validated_assignments(arguments.assignments)
    pack = _load_rooted(arguments.pack_root, "pack-manifest.json", "provider pack manifest")
    pairs = _ordered_pairs(
        assignments,
        pack,
        block=arguments.block,
        provider_slot=arguments.provider_slot,
    )
    oracle_manifest = _self_digested(
        _load_rooted(arguments.oracle_phase, "ORACLE_PHASE_MANIFEST.json", "oracle manifest"),
        "oracle_phase_digest",
        "oracle phase manifest",
    )
    target_manifest = _self_digested(
        _load_rooted(arguments.target_phase, "TARGET_PHASE_MANIFEST.json", "target manifest"),
        "target_phase_digest",
        "target phase manifest",
    )
    validation_manifest = _self_digested(
        _load_rooted(
            arguments.validation_phase,
            "VALIDATION_PHASE_MANIFEST.json",
            "validation manifest",
        ),
        "validation_phase_digest",
        "validation phase manifest",
    )
    compared = _timestamp(arguments.phase_started_at)
    expected_case_ids = [str(assignment["case_id"]) for assignment, _ in pairs]
    if (
        oracle_manifest.get("block") != arguments.block
        or oracle_manifest.get("provider_slot") != arguments.provider_slot
        or oracle_manifest.get("assignment_digest") != assignments["assignment_digest"]
        or oracle_manifest.get("runner_freeze_digest") != arguments.runner_freeze_digest
        or target_manifest.get("block") != arguments.block
        or target_manifest.get("provider_slot") != arguments.provider_slot
        or target_manifest.get("assignment_digest") != assignments["assignment_digest"]
        or target_manifest.get("runner_freeze_digest") != arguments.runner_freeze_digest
        or target_manifest.get("oracle_phase_digest") != oracle_manifest["oracle_phase_digest"]
        or target_manifest.get("record_count") != 24
        or validation_manifest.get("block") != arguments.block
        or validation_manifest.get("provider_slot") != arguments.provider_slot
        or validation_manifest.get("assignment_digest") != assignments["assignment_digest"]
        or validation_manifest.get("runner_freeze_digest") != arguments.runner_freeze_digest
        or validation_manifest.get("target_phase_digest") != target_manifest["target_phase_digest"]
        or validation_manifest.get("record_count") != 24
    ):
        raise ValueError("Comparison predecessor manifests do not share one frozen assignment.")
    _require_launch_predecessor(
        arguments,
        validation_manifest.get("validation_phase_digest"),
    )
    _validate_inventory(
        arguments.oracle_phase,
        oracle_manifest.get("proof_inventory"),
        expected_case_ids=expected_case_ids,
        label="oracle proof",
    )
    _validate_inventory(
        arguments.target_phase,
        target_manifest.get("record_inventory"),
        expected_case_ids=expected_case_ids,
        label="target record",
    )
    runner_freeze = getattr(arguments, "runner_freeze_record", None)
    if not isinstance(runner_freeze, dict):
        raise ValueError("Comparison phase has no validated runner freeze.")
    _validate_target_phase_bundle(
        arguments.target_phase,
        target_manifest,
        expected_case_ids=expected_case_ids,
        runner_freeze=runner_freeze,
    )
    _validate_inventory(
        arguments.validation_phase,
        validation_manifest.get("record_inventory"),
        expected_case_ids=expected_case_ids,
        label="validation record",
    )
    oracle_identity = _manifest_phase_identity(
        oracle_manifest,
        phase="freeze-oracles",
        runner_freeze_digest=arguments.runner_freeze_digest,
        assignment_digest=str(assignments["assignment_digest"]),
        identity_registry=arguments.identity_registry_record,
    )
    validation_identity = _manifest_phase_identity(
        validation_manifest,
        phase="run-validations",
        runner_freeze_digest=arguments.runner_freeze_digest,
        assignment_digest=str(assignments["assignment_digest"]),
        identity_registry=arguments.identity_registry_record,
    )
    for case_id in expected_case_ids:
        proof = _inventory_record(
            arguments.oracle_phase,
            oracle_manifest.get("proof_inventory"),
            case_id=case_id,
            label="oracle proof",
        )
        validation_record = _inventory_record(
            arguments.validation_phase,
            validation_manifest.get("record_inventory"),
            case_id=case_id,
            label="validation record",
        )
        if (
            proof.get("oracle_identity") != oracle_identity
            or validation_record.get("validation_identity") != validation_identity
        ):
            raise ValueError(
                "Oracle or validation identity does not derive from its launch receipt."
            )
    if compared < _timestamp(str(validation_manifest.get("phase_completed_at", ""))):
        raise ValueError("Comparison phase predates the complete validation phase.")
    arguments.output.mkdir(parents=True)
    records_root = arguments.output / "comparison-records"
    records_root.mkdir()
    inventory: list[dict[str, Any]] = []
    outcomes: dict[str, int] = {}
    for offset, (assignment, _case) in enumerate(pairs):
        case_id = str(assignment["case_id"])
        name = f"{case_id.removeprefix('case:')}.json"
        oracle_proof = _inventory_record(
            arguments.oracle_phase,
            oracle_manifest.get("proof_inventory"),
            case_id=case_id,
            label="oracle proof",
        )
        target_record = _inventory_record(
            arguments.target_phase,
            target_manifest.get("record_inventory"),
            case_id=case_id,
            label="target record",
        )
        validation_record = _inventory_record(
            arguments.validation_phase,
            validation_manifest.get("record_inventory"),
            case_id=case_id,
            label="validation record",
        )
        if (
            target_record.get("artifact_kind")
            == "selected_result_verifier_uncontrolled_target_failure"
            or validation_record.get("artifact_kind")
            == "selected_result_verifier_uncontrolled_validation_failure"
        ):
            record: dict[str, Any] = {
                "artifact_kind": "selected_result_verifier_qualification_comparison",
                "case_id": case_id,
                "oracle_proof_digest": oracle_proof["oracle_proof_digest"],
                "assignment_binding": target_record.get("assignment_binding"),
                "runner_freeze_digest": arguments.runner_freeze_digest,
                "comparison_identity": _identity(arguments),
                "target_or_validation_failure_digest": target_record.get(
                    "failure_digest", validation_record.get("failure_digest")
                ),
                "comparison_outcome": "uncontrolled_failure",
                "compared_at": _iso(compared + timedelta(seconds=offset)),
                "qualification_authority": "none_case_comparison_only",
            }
            record["comparison_digest"] = semantic_digest(record)
        else:
            record = freeze_verifier_comparison(
                case_root=_target_snapshot_case_root(
                    arguments.target_phase,
                    target_manifest,
                    case_id=case_id,
                ),
                oracle_proof=oracle_proof,
                target_derivation=target_record,
                target_validation=validation_record,
                comparison_identity=_identity(arguments),
                compared_at=_iso(compared + timedelta(seconds=offset)),
                assignment_manifest=assignments,
                frozen_identity_registry_digest=_frozen_identity_registry_digest(runner_freeze),
            )
        outcome = str(record["comparison_outcome"])
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        record_path = records_root / name
        write_normalized_json_once(record_path, record)
        inventory.append(
            {
                "case_id": case_id,
                "path": record_path.relative_to(arguments.output).as_posix(),
                "comparison_outcome": outcome,
                "content_digest": sha256_digest(record_path.read_bytes()),
            }
        )
    manifest: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_comparison_phase_manifest",
        "block": arguments.block,
        "provider_slot": arguments.provider_slot,
        "assignment_digest": assignments["assignment_digest"],
        "runner_freeze_digest": arguments.runner_freeze_digest,
        "oracle_phase_digest": oracle_manifest["oracle_phase_digest"],
        "target_phase_digest": target_manifest["target_phase_digest"],
        "validation_phase_digest": validation_manifest["validation_phase_digest"],
        "comparison_inventory": inventory,
        "comparison_count": len(inventory),
        "phase_launch_receipt": dict(arguments.launch_receipt),
        "outcome_counts": outcomes,
        "phase_completed_at": _iso(compared + timedelta(seconds=len(inventory))),
        "qualification_authority": "none_comparison_phase_only",
    }
    manifest["comparison_phase_digest"] = semantic_digest(manifest)
    write_normalized_json_once(arguments.output / "COMPARISON_PHASE_MANIFEST.json", manifest)
    return manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one frozen verifier qualification phase.")
    parser.add_argument(
        "phase", choices=("freeze-oracles", "run-targets", "run-validations", "compare")
    )
    parser.add_argument("--assignments", type=Path, required=True)
    parser.add_argument("--runner-freeze", type=Path, required=True)
    parser.add_argument("--phase-launch-receipt", type=Path, required=True)
    parser.add_argument("--pack-root", type=Path)
    parser.add_argument("--block", required=True, choices=("pilot", "held_out"))
    parser.add_argument("--provider-slot", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--oracle-phase", type=Path)
    parser.add_argument("--semantic-panel", type=Path)
    parser.add_argument("--target-phase", type=Path)
    parser.add_argument("--validation-phase", type=Path)
    parser.add_argument("--pilot-decision", type=Path)
    parser.add_argument("--pilot-provider-run", type=Path, action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    assignments = _validated_assignments(arguments.assignments)
    runner_freeze = _validated_runner_freeze(
        arguments.runner_freeze,
        assignments,
        assignments_path=arguments.assignments,
    )
    arguments.runner_freeze_digest = runner_freeze["runner_freeze_digest"]
    arguments.runner_freeze_record = runner_freeze
    arguments.identity_registry_record = _validated_frozen_identity_registry(runner_freeze)
    arguments.launch_receipt = _validated_launch_receipt(
        APPROVED_LAUNCH_RECEIPT,
        phase=arguments.phase,
        block=arguments.block,
        provider_slot=arguments.provider_slot,
        runner_freeze_digest=arguments.runner_freeze_digest,
        assignment_digest=str(assignments["assignment_digest"]),
        identity_registry=arguments.identity_registry_record,
    )
    arguments.phase_started_at = str(arguments.launch_receipt["issued_at"])
    if arguments.block == "held_out":
        if arguments.pilot_decision is None:
            raise ValueError("Held-out execution requires --pilot-decision.")
        pilot_decision = _validated_pilot_decision(
            arguments.pilot_decision,
            assignments=assignments,
            runner_freeze=runner_freeze,
            runner_freeze_digest=arguments.runner_freeze_digest,
            provider_run_roots=arguments.pilot_provider_run,
        )
        arguments.pilot_decision_digest = pilot_decision["pilot_decision_digest"]
    else:
        arguments.pilot_decision_digest = None
    if arguments.phase == "freeze-oracles":
        if arguments.pack_root is None:
            raise ValueError("freeze-oracles requires --pack-root.")
        if arguments.semantic_panel is None:
            raise ValueError("freeze-oracles requires --semantic-panel.")
        result = freeze_oracle_phase(arguments)
    elif arguments.phase == "run-targets":
        if arguments.pack_root is not None:
            raise ValueError("run-targets forbids --pack-root.")
        if arguments.oracle_phase is None:
            raise ValueError("run-targets requires --oracle-phase.")
        result = run_target_phase(arguments)
    elif arguments.phase == "run-validations":
        if arguments.pack_root is None:
            raise ValueError("run-validations requires --pack-root.")
        if arguments.target_phase is None:
            raise ValueError("run-validations requires --target-phase.")
        result = run_validation_phase(arguments)
    else:
        if arguments.pack_root is None:
            raise ValueError("compare requires --pack-root.")
        if (
            arguments.oracle_phase is None
            or arguments.target_phase is None
            or arguments.validation_phase is None
        ):
            raise ValueError(
                "compare requires --oracle-phase, --target-phase, and --validation-phase."
            )
        result = compare_phase(arguments)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    raise SystemExit(main())
