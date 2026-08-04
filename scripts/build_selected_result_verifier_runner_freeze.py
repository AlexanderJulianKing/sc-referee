from __future__ import annotations

import argparse
import json
import locale
import os
import platform
import stat
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from sc_referee_evaluation.qualification_identity import validate_identity_registry

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.run_selected_result_verifier_qualification_block import (
    LAUNCHER_VERSION,
    REQUIRED_DISTRIBUTIONS,
    freeze_distribution_record,
)

FROZEN_AT = "2026-08-04T23:30:00Z"
RUNNER_VERSION = "1.1.0-development"

_MODULES: dict[str, tuple[str, tuple[str, ...]]] = {
    "safe_io": (
        "evaluation/src/sc_referee_evaluation/selected_result_qualification_io.py",
        (
            "RootedReader",
            "write_canonical_json_exclusive",
        ),
    ),
    "qualification_identity": (
        "evaluation/src/sc_referee_evaluation/qualification_identity.py",
        (
            "validate_identity_registry",
            "validate_provider_session_identity_evidence",
        ),
    ),
    "semantic_review": (
        "evaluation/src/sc_referee_evaluation/selected_result_semantic_review.py",
        (
            "freeze_blind_semantic_review",
            "reconcile_blind_semantic_review",
            "revalidate_semantic_reconciliation",
        ),
    ),
    "byte_oracle": (
        "evaluation/src/sc_referee_evaluation/selected_result_qualification_oracle.py",
        ("verify_construction_certificate",),
    ),
    "qualification_controller": (
        "evaluation/src/sc_referee_evaluation/selected_result_verifier_qualification.py",
        (
            "freeze_oracle_proof",
            "parse_construction_certificate",
            "freeze_qualification_validation",
            "freeze_verifier_comparison",
        ),
    ),
    "target_verifier": (
        "evaluation/src/sc_referee_evaluation/prospective_selected_result_verifier.py",
        (
            "freeze_independent_selected_result_derivation",
            "freeze_selected_result_validation",
        ),
    ),
    "target_worker": (
        "evaluation/src/sc_referee_evaluation/selected_result_qualification_target_worker.py",
        (
            "validate_target_authorization",
            "run_target_worker",
            "entrypoint",
        ),
    ),
    "phase_runner": (
        "evaluation/src/sc_referee_evaluation/selected_result_qualification_runner.py",
        ("entrypoint",),
    ),
    "package_initializer": (
        "evaluation/src/sc_referee_evaluation/__init__.py",
        ("__getattr__",),
    ),
}

_RESOURCES = (
    "semantic-review-contract.json",
    "provider-pack-schema.json",
    "target-authorization-schema.json",
    "case-author-prompt.txt",
    "semantic-validator-prompt.txt",
    "target-runner-prompt.txt",
    "validation-runner-prompt.txt",
    "comparison-prompt.txt",
)

_TARGET_RUNTIME_DISTRIBUTIONS = {"cryptography", "sc-referee", "sc-referee-evaluation"}
_TARGET_RUNTIME_MODULES = {
    "cryptography",
    "sc_referee.core.ids",
    "sc_referee_evaluation.prospective_selected_result_verifier",
    "sc_referee_evaluation.selected_result_qualification_target_worker",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected one JSON object: {path}")
    return value


def _self_digested(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    supplied = result.pop(field, None)
    if supplied != semantic_digest(result):
        raise ValueError(f"{field} does not replay.")
    result[field] = supplied
    return result


def _locked_file(path: Path, *, recorded_path: str) -> dict[str, Any]:
    before = path.lstat()
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Frozen tuple path is absent or unsafe: {recorded_path}")
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
        raise ValueError(f"Frozen tuple path changed during read: {recorded_path}")
    return {
        "path": recorded_path,
        "content_digest": sha256_digest(payload),
        "size_bytes": len(payload),
        "mode": stat.S_IMODE(before.st_mode),
    }


def _file_lock(project_root: Path, relative_path: str) -> dict[str, Any]:
    return _locked_file(project_root / relative_path, recorded_path=relative_path)


def _podman_runtime_lock(path: Path) -> dict[str, Any]:
    runtime = path.resolve()
    observed = runtime.lstat()
    if runtime.name != "podman" or runtime.is_symlink() or not runtime.is_file():
        raise ValueError("The frozen OCI runtime must be one real podman executable.")
    if not observed.st_mode & 0o111:
        raise ValueError("The frozen podman runtime is not executable.")
    payload = runtime.read_bytes()
    after = runtime.lstat()
    if (
        observed.st_dev,
        observed.st_ino,
        observed.st_size,
        observed.st_mtime_ns,
        observed.st_mode,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_mode,
    ):
        raise ValueError("The podman runtime changed while it was frozen.")
    completed = subprocess.run(
        [str(runtime), "--version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    version_output = completed.stdout.strip()
    if (
        completed.returncode != 0
        or not version_output
        or "\n" in version_output
        or "\r" in version_output
    ):
        raise ValueError("The frozen podman runtime did not report one exact version.")
    return {
        "path": str(runtime),
        "content_digest": sha256_digest(payload),
        "size_bytes": len(payload),
        "mode": stat.S_IMODE(observed.st_mode),
        "version_output": version_output,
    }


def _target_image_runtime_lock(runtime_path: Path, image_digest: str) -> dict[str, Any]:
    rootless = subprocess.run(
        [str(runtime_path), "info", "--format", "{{.Host.Security.Rootless}}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if rootless.returncode != 0 or rootless.stdout.strip() != "true":
        raise ValueError("The qualification OCI runtime is not operating rootlessly.")
    inspected = subprocess.run(
        [str(runtime_path), "image", "inspect", image_digest, "--format", "{{.Digest}}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if inspected.returncode != 0 or inspected.stdout.strip() != image_digest:
        raise ValueError("The qualification OCI image digest does not replay.")
    with tempfile.TemporaryDirectory(prefix="sc-referee-target-runtime-") as temporary:
        output_root = Path(temporary)
        command = [
            str(runtime_path),
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
            raise ValueError("The qualification image runtime-manifest probe failed closed.")
        manifest_path = output_root / "runtime-manifest.json"
        lock = _locked_file(manifest_path, recorded_path="runtime-manifest.json")
        payload = manifest_path.read_bytes()
        try:
            manifest = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Target runtime manifest is not valid JSON.") from error
        if not isinstance(manifest, dict) or payload != (canonical_json(manifest) + "\n").encode():
            raise ValueError("Target runtime manifest is not canonical JSON.")
        basis = dict(manifest)
        supplied = basis.pop("target_runtime_manifest_digest", None)
        distributions = manifest.get("distributions")
        modules = manifest.get("module_files")
        distribution_names = (
            {str(item.get("requested_name")) for item in distributions if isinstance(item, dict)}
            if isinstance(distributions, list)
            else set()
        )
        module_names = (
            {str(item.get("module_name")) for item in modules if isinstance(item, dict)}
            if isinstance(modules, list)
            else set()
        )
        if (
            supplied != semantic_digest(basis)
            or manifest.get("artifact_kind") != "selected_result_verifier_target_runtime_manifest"
            or manifest.get("runtime_manifest_version") != "1.0.0"
            or manifest.get("input_projection") != "installed_runtime_only"
            or manifest.get("project_code_executed") is not False
            or distribution_names != _TARGET_RUNTIME_DISTRIBUTIONS
            or module_names != _TARGET_RUNTIME_MODULES
        ):
            raise ValueError("Target runtime manifest does not bind the required image tuple.")
        return {
            **lock,
            "target_runtime_manifest_digest": supplied,
            "runtime_manifest_version": manifest["runtime_manifest_version"],
            "distribution_names": sorted(distribution_names),
            "module_names": sorted(module_names),
            "probe_command_profile": "rootless-oci-runtime-manifest-v1",
        }


def build_selected_result_verifier_runner_freeze(
    project_root: Path,
    assignments_path: Path,
    identity_registry_path: Path,
    output: Path,
    *,
    oci_image_digest: str,
    oci_runtime_path: Path,
    distribution_search_paths: Sequence[Path] | None = None,
    frozen_at: str = FROZEN_AT,
) -> dict[str, Any]:
    """Build the full execution tuple; a separate trust anchor approves its digest."""

    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Qualification runner freeze already exists: {output}")
    if not oci_image_digest.startswith("sha256:") or len(oci_image_digest) != 71:
        raise ValueError("A complete rootless-OCI image digest is required.")
    assignments = _self_digested(_load(assignments_path), "assignment_digest")
    if (
        assignments.get("artifact_kind") != "selected_result_verifier_opaque_assignments"
        or assignments.get("assignment_version") != "1.1.0"
        or assignments.get("case_count") != 96
        or assignments.get("case_bytes_present") is not False
        or assignments.get("target_outputs_present") is not False
    ):
        raise ValueError("Assignments are not the answer-blind v1.1 study assignments.")

    source_resource_root = (
        project_root / "evaluation" / "qualification" / "selected-result-verifier-v1.1.0-precase"
    )
    package_resource_root = (
        project_root
        / "evaluation"
        / "src"
        / "sc_referee_evaluation"
        / "qualification_resources"
        / "selected_result_v1_1"
    )
    resources: dict[str, Any] = {}
    for name in _RESOURCES:
        source = source_resource_root / name
        packaged = package_resource_root / name
        if source.read_bytes() != packaged.read_bytes():
            raise ValueError(f"Installed qualification resource copy drifted: {name}")
        resources[name] = _file_lock(
            project_root,
            packaged.relative_to(project_root).as_posix(),
        )

    semantic_contract = _self_digested(
        _load(package_resource_root / "semantic-review-contract.json"),
        "contract_digest",
    )
    if assignments.get("semantic_review_contract_ref") != {
        "contract_version": semantic_contract.get("contract_version"),
        "contract_digest": semantic_contract.get("contract_digest"),
    }:
        raise ValueError("Assignments do not bind the packaged semantic contract.")
    identity_registry = validate_identity_registry(_load(identity_registry_path))
    resolved_identity_registry_path = identity_registry_path.resolve()
    identity_registry_lock = _locked_file(
        resolved_identity_registry_path,
        recorded_path=str(resolved_identity_registry_path),
    )

    modules: dict[str, Any] = {}
    for role, (relative_path, entry_points) in _MODULES.items():
        lock = _file_lock(project_root, relative_path)
        lock["module_name"] = (
            "sc_referee_evaluation." + Path(relative_path).stem
            if Path(relative_path).name != "__init__.py"
            else "sc_referee_evaluation"
        )
        lock["entry_points"] = list(entry_points)
        modules[role] = lock

    assignment_lock = _file_lock(
        project_root,
        assignments_path.relative_to(project_root).as_posix(),
    )
    distribution_records = {
        name: freeze_distribution_record(
            name,
            search_paths=distribution_search_paths,
        )
        for name in REQUIRED_DISTRIBUTIONS
    }
    from sc_referee_evaluation.selected_result_qualification_target_worker import (
        TARGET_AUTHORIZATION_FIELD_PROJECTION_DIGEST,
        TARGET_AUTHORIZATION_FORBIDDEN_FIELD_NAME_FRAGMENTS,
        TARGET_AUTHORIZATION_SCHEMA_CONTENT_DIGEST,
        TARGET_AUTHORIZATION_SCHEMA_DIGEST,
        TARGET_AUTHORIZATION_VERSION,
        load_target_authorization_schema,
    )

    load_target_authorization_schema()
    target_authorization_contract = {
        "authorization_version": TARGET_AUTHORIZATION_VERSION,
        "schema_content_digest": TARGET_AUTHORIZATION_SCHEMA_CONTENT_DIGEST,
        "schema_semantic_digest": TARGET_AUTHORIZATION_SCHEMA_DIGEST,
        "field_projection_digest": TARGET_AUTHORIZATION_FIELD_PROJECTION_DIGEST,
        "recursively_forbidden_field_name_fragments": list(
            TARGET_AUTHORIZATION_FORBIDDEN_FIELD_NAME_FRAGMENTS
        ),
    }
    oci_runtime_lock = _podman_runtime_lock(oci_runtime_path)
    target_runtime_lock = _target_image_runtime_lock(
        Path(str(oci_runtime_lock["path"])),
        oci_image_digest,
    )
    result: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_runner_freeze",
        "runner_version": RUNNER_VERSION,
        "freeze_identity": "selected-result-verifier-v1.1.0-execution-tuple",
        "assignment_ref": {
            **assignment_lock,
            "assignment_digest": assignments["assignment_digest"],
            "assignment_version": assignments["assignment_version"],
            "case_count": assignments["case_count"],
        },
        "semantic_contract_digest": semantic_contract["contract_digest"],
        "identity_registry_ref": {
            **identity_registry_lock,
            "identity_registry_version": identity_registry["identity_registry_version"],
            "identity_registry_digest": identity_registry["identity_registry_digest"],
        },
        "pre_import_launcher": {
            "launcher_version": LAUNCHER_VERSION,
            "trust_root": "external_one_way_anchor_outside_locked_distributions",
            "qualification_imports_before_verification": False,
        },
        "distribution_records": distribution_records,
        "target_authorization_contract": target_authorization_contract,
        "modules": modules,
        "resources": resources,
        "phase_graph": [
            {"phase": "blind-review-barrier", "predecessors": []},
            {"phase": "certificate-reconciliation", "predecessors": ["blind-review-barrier"]},
            {"phase": "freeze-oracles", "predecessors": ["certificate-reconciliation"]},
            {"phase": "run-targets", "predecessors": ["freeze-oracles"]},
            {"phase": "run-validations", "predecessors": ["run-targets"]},
            {"phase": "compare", "predecessors": ["run-validations"]},
        ],
        "identity_policy": {
            "registrar_signature": "Ed25519 over registry, sessions, and reveal event",
            "retained_provider_capture_required": True,
            "author_reviewer_provider_separation": True,
            "two_reviewer_provider_separation": True,
            "deterministic_phase_contexts_issued_by_pre_import_launcher": True,
        },
        "pass_rule": {
            "cases_per_block": 48,
            "exact_matches_required": 48,
            "uncontrolled_failures_permitted": 0,
            "false_completions_permitted": 0,
            "fresh_location_replays_required": 2,
        },
        "runtime_lock": {
            "implementation": platform.python_implementation(),
            "python_version": sys.version,
            "platform": platform.platform(),
            "abi_flags": getattr(sys, "abiflags", ""),
            "line_separator": os.linesep,
            "locale_encoding": locale.getencoding(),
        },
        "isolation_backend": {
            "kind": "rootless_oci",
            "runtime_profile": "podman-rootless-v1",
            "runtime_executable": oci_runtime_lock,
            "image_digest": oci_image_digest,
            "target_runtime_manifest": target_runtime_lock,
            "network": "none",
            "root_filesystem": "read_only",
            "uid": "non_root",
            "target_mounts": ["target_authorization:ro", "case_snapshots:ro", "output:rw"],
            "forbidden_mounts": ["provider_pack", "oracle_phase", "semantic_panel", "host_repo"],
            "rootless_probe": ["info", "--format", "{{.Host.Security.Rootless}}"],
            "image_probe": ["image", "inspect", "<image-digest>", "--format", "{{.Digest}}"],
            "worker_entrypoint": "sc-referee-eval-selected-result-target-worker",
            "environment": {
                "inherit_host": False,
                "values": [
                    "LANG=C.UTF-8",
                    "LC_ALL=C.UTF-8",
                    "PYTHONHASHSEED=0",
                    "PYTHONNOUSERSITE=1",
                ],
            },
            "capabilities": "drop_all",
            "no_new_privileges": True,
            "pid_limit": 64,
            "temporary_filesystem": "tmpfs:/tmp:noexec,nosuid,nodev,size=16m",
            "unsafe_fallback": False,
        },
        "frozen_at": frozen_at,
        "case_bytes_present": False,
        "target_outputs_present": False,
        "qualification_authority": "none_runner_freeze_only",
    }
    result["runner_freeze_digest"] = semantic_digest(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_normalized_json_once(output, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a complete selected-result qualification execution tuple."
    )
    project_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--project-root", type=Path, default=project_root)
    parser.add_argument(
        "--assignments",
        type=Path,
        default=(
            project_root
            / "evaluation"
            / "qualification"
            / "selected-result-verifier-v1.1.0-study"
            / "opaque-assignments.json"
        ),
    )
    parser.add_argument("--oci-image-digest", required=True)
    parser.add_argument("--oci-runtime-path", type=Path, required=True)
    parser.add_argument("--identity-registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frozen-at", default=FROZEN_AT)
    arguments = parser.parse_args()
    result = build_selected_result_verifier_runner_freeze(
        arguments.project_root.resolve(),
        arguments.assignments.resolve(),
        arguments.identity_registry.resolve(),
        arguments.output.resolve(),
        oci_image_digest=arguments.oci_image_digest,
        oci_runtime_path=arguments.oci_runtime_path,
        frozen_at=arguments.frozen_at,
    )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
