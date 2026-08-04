from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import stat
import sys
from pathlib import Path

import pytest
import sc_referee_evaluation.selected_result_qualification_runner as qualification_runner
from sc_referee_evaluation.selected_result_qualification_target_worker import (
    TARGET_AUTHORIZATION_FIELD_PROJECTION_DIGEST,
    TARGET_AUTHORIZATION_FORBIDDEN_FIELD_NAME_FRAGMENTS,
    TARGET_AUTHORIZATION_SCHEMA_CONTENT_DIGEST,
    TARGET_AUTHORIZATION_SCHEMA_DIGEST,
    TARGET_AUTHORIZATION_VERSION,
)
from sc_referee_evaluation.selected_result_qualification_trust import (
    OFFICIAL_RUNNER_FREEZE_DIGEST,
)
from selected_result_qualification_support import build_test_identity_registry

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_selected_result_verifier_runner_freeze import (
    _MODULES,
    _RESOURCES,
    build_selected_result_verifier_runner_freeze,
)
from scripts.run_selected_result_verifier_qualification_block import (
    LAUNCHER_VERSION,
    REQUIRED_DISTRIBUTIONS,
)

_FAKE_ROOTLESS_OCI_DIGEST = "sha256:" + ("0" * 64)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _fake_podman(tmp_path: Path) -> Path:
    runtime = tmp_path / "podman"
    manifest: dict[str, object] = {
        "artifact_kind": "selected_result_verifier_target_runtime_manifest",
        "runtime_manifest_version": "1.0.0",
        "target_worker_version": "1.1.0-development",
        "python_runtime": {"implementation": "fake-image-python"},
        "module_files": [
            {"module_name": name}
            for name in (
                "cryptography",
                "sc_referee.core.ids",
                "sc_referee_evaluation.prospective_selected_result_verifier",
                "sc_referee_evaluation.selected_result_qualification_target_worker",
            )
        ],
        "distributions": [
            {"requested_name": name}
            for name in ("cryptography", "sc-referee", "sc-referee-evaluation")
        ],
        "distribution_count": 3,
        "distribution_file_count": 12,
        "distribution_total_file_bytes": 1024,
        "input_projection": "installed_runtime_only",
        "project_code_executed": False,
        "qualification_authority": "none_target_runtime_evidence_only",
    }
    manifest["target_runtime_manifest_digest"] = semantic_digest(manifest)
    payload = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    encoded_payload = base64.b64encode(payload).decode("ascii")
    invocation_path = tmp_path / "podman-run-arguments.json"
    runtime.write_text(
        "\n".join(
            [
                f"#!{sys.executable}",
                "import base64",
                "import json",
                "import sys",
                "from pathlib import Path",
                "arguments = sys.argv[1:]",
                "if arguments == ['--version']:",
                "    print('podman version test-1.0')",
                "elif arguments[:2] == ['info', '--format']:",
                "    print('true')",
                "elif arguments[:2] == ['image', 'inspect']:",
                "    print(arguments[2])",
                "elif arguments and arguments[0] == 'run':",
                f"    Path({str(invocation_path)!r}).write_text(json.dumps(arguments), encoding='utf-8')",
                "    volume = arguments[arguments.index('--volume') + 1]",
                "    host_root = Path(volume.split(':', 1)[0])",
                f"    (host_root / 'runtime-manifest.json').write_bytes(base64.b64decode({encoded_payload!r}))",
                "else:",
                "    raise SystemExit(2)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    runtime.chmod(0o700)
    return runtime


def _identity_registry(tmp_path: Path) -> Path:
    value, _keys = build_test_identity_registry([("test-reviewer", "test-provider")])
    path = tmp_path / "identity-registry.json"
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    return path


def _record_hash(payload: bytes) -> str:
    encoded = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=")
    return "sha256=" + encoded.decode("ascii")


def _fake_distribution_root(tmp_path: Path) -> Path:
    root = tmp_path / "site-packages"
    root.mkdir(exist_ok=True)
    for distribution_name in REQUIRED_DISTRIBUTIONS:
        package_name = distribution_name.replace("-", "_")
        dist_info_name = distribution_name.replace("-", "_") + "-1.0.0.dist-info"
        files = {
            f"{package_name}/__init__.py": f'NAME = "{distribution_name}"\n'.encode(),
            f"{dist_info_name}/METADATA": (
                f"Metadata-Version: 2.1\nName: {distribution_name}\nVersion: 1.0.0\n"
            ).encode(),
            f"{dist_info_name}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\n",
        }
        for relative_path, payload in files.items():
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        record_path = f"{dist_info_name}/RECORD"
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        for relative_path, payload in sorted(files.items()):
            writer.writerow((relative_path, _record_hash(payload), len(payload)))
        writer.writerow((record_path, "", ""))
        (root / record_path).write_text(output.getvalue(), encoding="utf-8", newline="")
    return root


def _v1_1_paths(project_root: Path) -> tuple[Path, Path, Path]:
    qualification = project_root / "evaluation" / "qualification"
    return (
        qualification / "selected-result-verifier-v1.1.0-precase",
        qualification / "selected-result-verifier-v1.1.0-study",
        (
            project_root
            / "evaluation"
            / "src"
            / "sc_referee_evaluation"
            / "qualification_resources"
            / "selected_result_v1_1"
        ),
    )


def test_v1_1_runner_freeze_binds_complete_tuple_and_assignments(
    project_root: Path,
    tmp_path: Path,
) -> None:
    pre_case, study, package_resources = _v1_1_paths(project_root)
    assignments_path = study / "opaque-assignments.json"
    output = tmp_path / "runner-freeze.json"
    distribution_root = _fake_distribution_root(tmp_path)

    value = build_selected_result_verifier_runner_freeze(
        project_root,
        assignments_path,
        _identity_registry(tmp_path),
        output,
        oci_image_digest=_FAKE_ROOTLESS_OCI_DIGEST,
        oci_runtime_path=_fake_podman(tmp_path),
        distribution_search_paths=[distribution_root],
    )

    assert _load(output) == value
    basis = dict(value)
    supplied = basis.pop("runner_freeze_digest")
    assert supplied == semantic_digest(basis)
    assert value["case_bytes_present"] is False
    assert value["target_outputs_present"] is False
    assert value["qualification_authority"] == "none_runner_freeze_only"
    launcher = value["pre_import_launcher"]
    assert isinstance(launcher, dict)
    assert launcher == {
        "launcher_version": LAUNCHER_VERSION,
        "trust_root": "external_one_way_anchor_outside_locked_distributions",
        "qualification_imports_before_verification": False,
    }
    distribution_records = value["distribution_records"]
    assert isinstance(distribution_records, dict)
    assert set(distribution_records) == set(REQUIRED_DISTRIBUTIONS)
    for name, record in distribution_records.items():
        assert isinstance(record, dict)
        assert record["distribution_name"] == name
        assert record["metadata_name"] == name
        assert record["version"] == "1.0.0"
        assert record["editable_install"] is False
        assert record["record_content_digest"].startswith("sha256:")
        assert record["record_entry_count"] == 4
        assert set(record) == {
            "artifact_kind",
            "distribution_name",
            "metadata_name",
            "version",
            "record_path",
            "record_content_digest",
            "record_size_bytes",
            "record_entry_count",
            "record_paths_digest",
            "editable_install",
        }

    authorization_contract = value["target_authorization_contract"]
    assert authorization_contract == {
        "authorization_version": TARGET_AUTHORIZATION_VERSION,
        "schema_content_digest": TARGET_AUTHORIZATION_SCHEMA_CONTENT_DIGEST,
        "schema_semantic_digest": TARGET_AUTHORIZATION_SCHEMA_DIGEST,
        "field_projection_digest": TARGET_AUTHORIZATION_FIELD_PROJECTION_DIGEST,
        "recursively_forbidden_field_name_fragments": list(
            TARGET_AUTHORIZATION_FORBIDDEN_FIELD_NAME_FRAGMENTS
        ),
    }

    assignments = _load(assignments_path)
    assignment_ref = value["assignment_ref"]
    assert isinstance(assignment_ref, dict)
    assert assignment_ref["assignment_digest"] == assignments["assignment_digest"]
    assert assignment_ref["assignment_version"] == "1.1.0"
    assert assignment_ref["case_count"] == 96
    assert assignment_ref["content_digest"] == sha256_digest(assignments_path.read_bytes())
    assert assignment_ref["size_bytes"] == assignments_path.stat().st_size

    registry_ref = value["identity_registry_ref"]
    assert isinstance(registry_ref, dict)
    registry_path = Path(str(registry_ref["path"]))
    registry = _load(registry_path)
    assert registry_ref["identity_registry_version"] == "1.1.0"
    assert registry_ref["identity_registry_digest"] == registry["identity_registry_digest"]
    assert registry_ref["content_digest"] == sha256_digest(registry_path.read_bytes())

    contract = _load(pre_case / "semantic-review-contract.json")
    assert value["semantic_contract_digest"] == contract["contract_digest"]
    assert assignments["semantic_review_contract_ref"] == {
        "contract_version": contract["contract_version"],
        "contract_digest": contract["contract_digest"],
    }

    modules = value["modules"]
    assert isinstance(modules, dict)
    assert set(modules) == set(_MODULES)
    assert {
        "safe_io",
        "qualification_identity",
        "semantic_review",
        "byte_oracle",
        "qualification_controller",
        "target_verifier",
        "target_worker",
        "phase_runner",
        "package_initializer",
    }.issubset(modules)
    for role, (relative_path, entry_points) in _MODULES.items():
        lock = modules[role]
        assert isinstance(lock, dict)
        module_path = project_root / relative_path
        observed = module_path.lstat()
        assert lock["path"] == relative_path
        assert lock["content_digest"] == sha256_digest(module_path.read_bytes())
        assert lock["size_bytes"] == observed.st_size
        assert lock["mode"] == stat.S_IMODE(observed.st_mode)
        assert lock["entry_points"] == list(entry_points)

    resources = value["resources"]
    assert isinstance(resources, dict)
    assert set(resources) == set(_RESOURCES)
    for name in _RESOURCES:
        lock = resources[name]
        assert isinstance(lock, dict)
        resource_path = package_resources / name
        observed = resource_path.lstat()
        assert lock["content_digest"] == sha256_digest(resource_path.read_bytes())
        assert lock["size_bytes"] == observed.st_size
        assert lock["mode"] == stat.S_IMODE(observed.st_mode)

    isolation = value["isolation_backend"]
    assert isinstance(isolation, dict)
    assert isolation["kind"] == "rootless_oci"
    assert isolation["runtime_profile"] == "podman-rootless-v1"
    runtime = isolation["runtime_executable"]
    assert isinstance(runtime, dict)
    assert Path(str(runtime["path"])).name == "podman"
    assert runtime["version_output"] == "podman version test-1.0"
    assert isolation["image_digest"] == _FAKE_ROOTLESS_OCI_DIGEST
    assert isolation["network"] == "none"
    assert isolation["root_filesystem"] == "read_only"
    assert isolation["uid"] == "non_root"
    assert isolation["target_mounts"] == [
        "target_authorization:ro",
        "case_snapshots:ro",
        "output:rw",
    ]
    assert isolation["forbidden_mounts"] == [
        "provider_pack",
        "oracle_phase",
        "semantic_panel",
        "host_repo",
    ]
    assert isolation["environment"] == {
        "inherit_host": False,
        "values": [
            "LANG=C.UTF-8",
            "LC_ALL=C.UTF-8",
            "PYTHONHASHSEED=0",
            "PYTHONNOUSERSITE=1",
        ],
    }
    assert isolation["capabilities"] == "drop_all"
    assert isolation["no_new_privileges"] is True
    assert isolation["pid_limit"] == 64
    assert isolation["temporary_filesystem"] == "tmpfs:/tmp:noexec,nosuid,nodev,size=16m"
    assert isolation["unsafe_fallback"] is False
    target_runtime = isolation["target_runtime_manifest"]
    assert isinstance(target_runtime, dict)
    assert target_runtime["runtime_manifest_version"] == "1.0.0"
    assert target_runtime["distribution_names"] == [
        "cryptography",
        "sc-referee",
        "sc-referee-evaluation",
    ]
    assert target_runtime["module_names"] == [
        "cryptography",
        "sc_referee.core.ids",
        "sc_referee_evaluation.prospective_selected_result_verifier",
        "sc_referee_evaluation.selected_result_qualification_target_worker",
    ]
    assert target_runtime["probe_command_profile"] == "rootless-oci-runtime-manifest-v1"
    assert str(target_runtime["target_runtime_manifest_digest"]).startswith("sha256:")
    assert str(target_runtime["content_digest"]).startswith("sha256:")

    run_arguments = json.loads((tmp_path / "podman-run-arguments.json").read_text())
    assert run_arguments[:15] == [
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
    ]
    assert run_arguments[15] == "--volume"
    assert str(run_arguments[16]).endswith(":/qualification-runtime:rw")
    assert run_arguments[17:] == [
        _FAKE_ROOTLESS_OCI_DIGEST,
        "sc-referee-eval-selected-result-target-worker",
        "--runtime-manifest",
        "/qualification-runtime/runtime-manifest.json",
    ]


def test_v1_1_runner_freeze_never_overwrites(project_root: Path, tmp_path: Path) -> None:
    _, study, _ = _v1_1_paths(project_root)
    assignments_path = study / "opaque-assignments.json"
    output = tmp_path / "runner-freeze.json"
    distribution_root = _fake_distribution_root(tmp_path)
    build_selected_result_verifier_runner_freeze(
        project_root,
        assignments_path,
        _identity_registry(tmp_path),
        output,
        oci_image_digest=_FAKE_ROOTLESS_OCI_DIGEST,
        oci_runtime_path=_fake_podman(tmp_path),
        distribution_search_paths=[distribution_root],
    )

    with pytest.raises(FileExistsError):
        build_selected_result_verifier_runner_freeze(
            project_root,
            assignments_path,
            _identity_registry(tmp_path),
            output,
            oci_image_digest=_FAKE_ROOTLESS_OCI_DIGEST,
            oci_runtime_path=_fake_podman(tmp_path),
            distribution_search_paths=[distribution_root],
        )


def test_unfrozen_trust_anchor_rejects_self_consistent_ad_hoc_freeze(
    project_root: Path,
    tmp_path: Path,
) -> None:
    _, study, _ = _v1_1_paths(project_root)
    assignments_path = study / "opaque-assignments.json"
    output = tmp_path / "ad-hoc-runner-freeze.json"
    distribution_root = _fake_distribution_root(tmp_path)
    build_selected_result_verifier_runner_freeze(
        project_root,
        assignments_path,
        _identity_registry(tmp_path),
        output,
        oci_image_digest=_FAKE_ROOTLESS_OCI_DIGEST,
        oci_runtime_path=_fake_podman(tmp_path),
        distribution_search_paths=[distribution_root],
    )

    assert OFFICIAL_RUNNER_FREEZE_DIGEST == "UNFROZEN"
    with pytest.raises(
        ValueError,
        match="not the one officially approved execution tuple",
    ):
        qualification_runner._validated_runner_freeze(
            output,
            qualification_runner._validated_assignments(assignments_path),
            assignments_path=assignments_path,
        )


def test_v1_1_builder_and_runtime_validator_agree_on_complete_tuple(
    project_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, study, _ = _v1_1_paths(project_root)
    assignments_path = study / "opaque-assignments.json"
    output = tmp_path / "candidate-runner-freeze.json"
    distribution_root = _fake_distribution_root(tmp_path)
    value = build_selected_result_verifier_runner_freeze(
        project_root,
        assignments_path,
        _identity_registry(tmp_path),
        output,
        oci_image_digest=_FAKE_ROOTLESS_OCI_DIGEST,
        oci_runtime_path=_fake_podman(tmp_path),
        distribution_search_paths=[distribution_root],
    )
    candidate_digest = value["runner_freeze_digest"]
    assert isinstance(candidate_digest, str)
    monkeypatch.setattr(
        qualification_runner,
        "OFFICIAL_RUNNER_FREEZE_DIGEST",
        candidate_digest,
    )

    assert (
        qualification_runner._validated_runner_freeze(
            output,
            qualification_runner._validated_assignments(assignments_path),
            assignments_path=assignments_path,
        )
        == value
    )


def test_packaged_v1_1_resources_are_byte_identical_to_precase_sources(
    project_root: Path,
) -> None:
    pre_case, _, package_resources = _v1_1_paths(project_root)

    assert set(_RESOURCES) == {
        "semantic-review-contract.json",
        "provider-pack-schema.json",
        "target-authorization-schema.json",
        "case-author-prompt.txt",
        "semantic-validator-prompt.txt",
        "target-runner-prompt.txt",
        "validation-runner-prompt.txt",
        "comparison-prompt.txt",
    }
    for name in _RESOURCES:
        assert (package_resources / name).read_bytes() == (pre_case / name).read_bytes()


def test_v1_1_has_no_official_runner_freeze_artifact(project_root: Path) -> None:
    _, study, _ = _v1_1_paths(project_root)

    assert OFFICIAL_RUNNER_FREEZE_DIGEST == "UNFROZEN"
    assert list(study.glob("runner-freeze*.json")) == []
