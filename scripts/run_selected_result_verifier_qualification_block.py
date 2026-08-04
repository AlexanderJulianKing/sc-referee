from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import importlib
import importlib.machinery
import importlib.metadata
import io
import json
import os
import re
import stat
import sys
import sysconfig
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

# This script is the deliberately small trust root outside the core and evaluation
# distributions that it verifies. Updating this one-way anchor does not alter either
# locked distribution and therefore cannot create a digest cycle.
OFFICIAL_RUNNER_FREEZE_DIGEST = "UNFROZEN"
LAUNCHER_VERSION = "1.0.0-development"
APPROVED_DIGEST_ATTRIBUTE = "_sc_referee_approved_runner_freeze_digest"
APPROVED_LAUNCH_RECEIPT_ATTRIBUTE = "_sc_referee_qualification_launch_receipt"
PHASE_LAUNCH_RECEIPT_VERSION = "1.1.0"

REQUIRED_DISTRIBUTIONS = (
    "annotated-types",
    "attrs",
    "cffi",
    "cryptography",
    "h5py",
    "jinja2",
    "jsonschema",
    "jsonschema-specifications",
    "markupsafe",
    "numpy",
    "pycparser",
    "pydantic",
    "pydantic-core",
    "pyyaml",
    "referencing",
    "rpds-py",
    "sc-referee",
    "sc-referee-evaluation",
    "tree-sitter",
    "tree-sitter-r",
    "typing-extensions",
    "typing-inspection",
)
REQUIRED_IMPORT_PACKAGES = {
    "sc-referee": "sc_referee",
    "sc-referee-evaluation": "sc_referee_evaluation",
}

_MAX_FREEZE_BYTES = 4 * 1024 * 1024
_CANONICAL_NAME_PATTERN = re.compile(r"[-_.]+")


class QualificationLauncherError(ValueError):
    """Raised before qualification code is imported when the trusted tuple does not replay."""


def _canonical_name(value: str) -> str:
    return _CANONICAL_NAME_PATTERN.sub("-", value).lower()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_digest(value: bytes | str) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _semantic_digest(value: Any) -> str:
    return _sha256_digest(_canonical_json(value))


def _stable_file_bytes(path: Path, label: str) -> bytes:
    before = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(before.st_mode):
        raise QualificationLauncherError(f"{label} is absent, a symlink, or not a regular file.")
    with path.open("rb") as handle:
        payload = handle.read()
        after = os.fstat(handle.fileno())
    if (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise QualificationLauncherError(f"{label} changed while it was read.")
    return payload


def _json_object(path: Path) -> dict[str, Any]:
    payload = _stable_file_bytes(path, "Runner freeze")
    if len(payload) > _MAX_FREEZE_BYTES:
        raise QualificationLauncherError("Runner freeze exceeds the launcher byte ceiling.")

    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise QualificationLauncherError(f"Runner freeze repeats JSON key {key!r}.")
            result[key] = value
        return result

    try:
        value = json.loads(
            payload.decode("utf-8", errors="strict"), object_pairs_hook=no_duplicates
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationLauncherError(
            "Runner freeze is not one strict UTF-8 JSON value."
        ) from error
    if not isinstance(value, dict):
        raise QualificationLauncherError("Runner freeze must be one JSON object.")
    return value


def _distributions(
    distribution_name: str,
    *,
    search_paths: Sequence[Path] | None,
) -> list[importlib.metadata.Distribution]:
    requested = _canonical_name(distribution_name)
    kwargs: dict[str, Any] = {}
    if search_paths is not None:
        kwargs["path"] = [str(path) for path in search_paths]
    return [
        distribution
        for distribution in importlib.metadata.distributions(**kwargs)
        if _canonical_name(distribution.metadata.get("Name", "")) == requested
    ]


def _one_distribution(
    distribution_name: str,
    *,
    search_paths: Sequence[Path] | None,
) -> importlib.metadata.Distribution:
    matches = _distributions(distribution_name, search_paths=search_paths)
    if len(matches) != 1:
        raise QualificationLauncherError(
            f"Expected exactly one installed {distribution_name} distribution; found {len(matches)}."
        )
    return matches[0]


def _record_path(distribution: importlib.metadata.Distribution) -> tuple[str, Path]:
    metadata_root_value = getattr(distribution, "_path", None)
    if not isinstance(metadata_root_value, Path) or not metadata_root_value.name.endswith(
        ".dist-info"
    ):
        raise QualificationLauncherError(
            "Installed distribution is not one filesystem-backed dist-info directory."
        )
    installed_root = Path(distribution.locate_file(""))
    try:
        recorded = (metadata_root_value / "RECORD").relative_to(installed_root).as_posix()
    except ValueError as error:
        raise QualificationLauncherError(
            "Installed distribution RECORD escapes its root."
        ) from error
    return recorded, metadata_root_value / "RECORD"


def _record_rows(payload: bytes, record_path: str) -> list[tuple[str, str, int | None]]:
    try:
        text = payload.decode("utf-8", errors="strict")
        parsed = list(csv.reader(io.StringIO(text, newline="")))
    except (UnicodeDecodeError, csv.Error) as error:
        raise QualificationLauncherError("Distribution RECORD is not strict UTF-8 CSV.") from error
    rows: list[tuple[str, str, int | None]] = []
    paths: set[str] = set()
    for row in parsed:
        if len(row) != 3:
            raise QualificationLauncherError("Distribution RECORD row does not have three fields.")
        path, encoded_hash, size_text = row
        pure = PurePosixPath(path)
        if (
            not path
            or "\\" in path
            or pure.is_absolute()
            or "" in pure.parts
            or "." in pure.parts
            or path in paths
        ):
            raise QualificationLauncherError("Distribution RECORD contains a noncanonical path.")
        paths.add(path)
        if path == record_path:
            if encoded_hash or size_text:
                raise QualificationLauncherError(
                    "Distribution RECORD must leave its own hash empty."
                )
            rows.append((path, "", None))
            continue
        if not encoded_hash.startswith("sha256=") or not size_text.isdecimal():
            raise QualificationLauncherError(
                "Every non-RECORD distribution entry requires a sha256 hash and size."
            )
        rows.append((path, encoded_hash.removeprefix("sha256="), int(size_text)))
    if len(rows) < 3 or sum(path == record_path for path, _, _ in rows) != 1:
        raise QualificationLauncherError("Distribution RECORD is incomplete.")
    return rows


def _urlsafe_sha256(payload: bytes) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode("ascii")


def _validate_record_payloads(
    distribution: importlib.metadata.Distribution,
    rows: Sequence[tuple[str, str, int | None]],
    record_path: str,
) -> None:
    for path, expected_hash, expected_size in rows:
        if path == record_path:
            continue
        installed_path = Path(distribution.locate_file(path))
        payload = _stable_file_bytes(installed_path, f"Installed distribution entry {path}")
        if len(payload) != expected_size or _urlsafe_sha256(payload) != expected_hash:
            raise QualificationLauncherError(f"Installed distribution entry has drifted: {path}")


def freeze_distribution_record(
    distribution_name: str,
    *,
    search_paths: Sequence[Path] | None = None,
) -> dict[str, Any]:
    """Build one exact installed-distribution RECORD lock using only standard-library code."""

    canonical_name = _canonical_name(distribution_name)
    distribution = _one_distribution(canonical_name, search_paths=search_paths)
    metadata_name = distribution.metadata.get("Name", "")
    if _canonical_name(metadata_name) != canonical_name:
        raise QualificationLauncherError("Installed distribution metadata name does not match.")
    record_path, installed_record_path = _record_path(distribution)
    record_payload = _stable_file_bytes(installed_record_path, f"{canonical_name} RECORD")
    rows = _record_rows(record_payload, record_path)
    _validate_record_payloads(distribution, rows, record_path)
    recorded_paths = [path for path, _, _ in rows]
    if canonical_name in REQUIRED_IMPORT_PACKAGES:
        package = REQUIRED_IMPORT_PACKAGES[canonical_name]
        required_init = f"{package}/__init__.py"
        if required_init not in recorded_paths:
            raise QualificationLauncherError(
                f"{canonical_name} is editable or does not RECORD its import package."
            )
    if any(
        PurePosixPath(path).name.startswith("__editable__") or path.endswith(".pth")
        for path in recorded_paths
    ):
        raise QualificationLauncherError(
            f"{canonical_name} uses an editable or startup-hook installation."
        )
    return {
        "artifact_kind": "installed_distribution_record_lock",
        "distribution_name": canonical_name,
        "metadata_name": metadata_name,
        "version": distribution.version,
        "record_path": record_path,
        "record_content_digest": _sha256_digest(record_payload),
        "record_size_bytes": len(record_payload),
        "record_entry_count": len(rows),
        "record_paths_digest": _semantic_digest(recorded_paths),
        "editable_install": False,
    }


def validate_distribution_record(
    value: Any,
    *,
    search_paths: Sequence[Path] | None = None,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise QualificationLauncherError("Distribution lock is not an object.")
    expected_keys = {
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
    if set(value) != expected_keys:
        raise QualificationLauncherError("Distribution lock fields are incomplete or unexpected.")
    name = value.get("distribution_name")
    if not isinstance(name, str) or _canonical_name(name) != name:
        raise QualificationLauncherError("Distribution lock name is not canonical.")
    rebuilt = freeze_distribution_record(name, search_paths=search_paths)
    if rebuilt != value:
        raise QualificationLauncherError(f"Installed distribution lock does not replay: {name}")
    return rebuilt


def validate_pre_import_environment(
    runner_freeze_path: Path,
    *,
    search_paths: Sequence[Path] | None = None,
) -> dict[str, Any]:
    freeze = _json_object(runner_freeze_path)
    basis = dict(freeze)
    supplied = basis.pop("runner_freeze_digest", None)
    if supplied != _semantic_digest(basis):
        raise QualificationLauncherError("Runner freeze self-digest does not replay.")
    if OFFICIAL_RUNNER_FREEZE_DIGEST == "UNFROZEN" or supplied != OFFICIAL_RUNNER_FREEZE_DIGEST:
        raise QualificationLauncherError("Runner freeze is not the officially approved tuple.")
    if (
        freeze.get("artifact_kind") != "selected_result_verifier_runner_freeze"
        or freeze.get("runner_version") != "1.1.0-development"
        or freeze.get("freeze_identity") != "selected-result-verifier-v1.1.0-execution-tuple"
    ):
        raise QualificationLauncherError("Runner freeze identity is unsupported.")
    distribution_records = freeze.get("distribution_records")
    if not isinstance(distribution_records, dict) or set(distribution_records) != set(
        REQUIRED_DISTRIBUTIONS
    ):
        raise QualificationLauncherError("Runner freeze does not lock the required distributions.")
    for name in REQUIRED_DISTRIBUTIONS:
        record = distribution_records.get(name)
        if not isinstance(record, dict) or record.get("distribution_name") != name:
            raise QualificationLauncherError("Runner freeze distribution lock is miskeyed.")
        validate_distribution_record(record, search_paths=search_paths)
    return freeze


def _locked_import_paths(*, search_paths: Sequence[Path] | None) -> tuple[list[str], Path, Path]:
    roots = {
        Path(_one_distribution(name, search_paths=search_paths).locate_file("")).resolve()
        for name in REQUIRED_DISTRIBUTIONS
    }
    evaluation_distribution = _one_distribution("sc-referee-evaluation", search_paths=search_paths)
    evaluation_root = Path(evaluation_distribution.locate_file("")).resolve()
    package_init = evaluation_root / "sc_referee_evaluation" / "__init__.py"
    runner_path = (
        evaluation_root / "sc_referee_evaluation" / "selected_result_qualification_runner.py"
    )
    recorded_path, record_file = _record_path(evaluation_distribution)
    rows = _record_rows(
        _stable_file_bytes(record_file, "sc-referee-evaluation RECORD"),
        recorded_path,
    )
    recorded_paths = {path for path, _digest, _size in rows}
    for expected in (
        "sc_referee_evaluation/__init__.py",
        "sc_referee_evaluation/selected_result_qualification_runner.py",
    ):
        if expected not in recorded_paths:
            raise QualificationLauncherError(
                "The qualification import target is absent from the verified distribution RECORD."
            )
    package_spec = importlib.machinery.PathFinder.find_spec(
        "sc_referee_evaluation", [str(item) for item in sorted(roots)]
    )
    if package_spec is None or package_spec.origin is None:
        raise QualificationLauncherError("The verified qualification package cannot be resolved.")
    if Path(package_spec.origin).resolve() != package_init.resolve():
        raise QualificationLauncherError(
            "Qualification package import origin is not the verified distribution."
        )
    runner_spec = importlib.machinery.PathFinder.find_spec(
        "sc_referee_evaluation.selected_result_qualification_runner",
        [str(package_init.parent)],
    )
    if runner_spec is None or runner_spec.origin is None:
        raise QualificationLauncherError("The verified qualification runner cannot be resolved.")
    if Path(runner_spec.origin).resolve() != runner_path.resolve():
        raise QualificationLauncherError(
            "Qualification runner import origin is not the verified distribution."
        )
    standard_roots = {
        Path(value).resolve()
        for key in ("stdlib", "platstdlib")
        if isinstance((value := sysconfig.get_path(key)), str)
    }
    return [str(item) for item in sorted(roots | standard_roots)], package_init, runner_path


def _validated_external_launch_receipt(
    receipt_path: Path,
    *,
    freeze: dict[str, Any],
    phase: str,
    block: str,
    provider_slot: str,
) -> dict[str, Any]:
    registry_ref = freeze.get("identity_registry_ref")
    if not isinstance(registry_ref, dict):
        raise QualificationLauncherError("Runner freeze has no identity-registry lock.")
    registry_path = Path(str(registry_ref.get("path", "")))
    if not registry_path.is_absolute():
        raise QualificationLauncherError("Frozen identity-registry path is not absolute.")
    registry_payload = _stable_file_bytes(registry_path, "Frozen identity registry")
    if _sha256_digest(registry_payload) != registry_ref.get("content_digest"):
        raise QualificationLauncherError("Frozen identity-registry bytes have drifted.")
    receipt_payload = _stable_file_bytes(receipt_path, "Phase-launch receipt")
    try:
        registry = json.loads(registry_payload.decode("utf-8", errors="strict"))
        receipt = json.loads(receipt_payload.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationLauncherError(
            "Identity registry or phase-launch receipt is not strict JSON."
        ) from error
    if not isinstance(registry, dict) or not isinstance(receipt, dict):
        raise QualificationLauncherError(
            "Identity registry and phase-launch receipt must be JSON objects."
        )
    from sc_referee_evaluation.qualification_identity import (
        validate_identity_registry,
        validate_registrar_signed_receipt,
    )

    try:
        frozen_registry = validate_identity_registry(registry)
        verified = validate_registrar_signed_receipt(
            receipt,
            registry=frozen_registry,
            expected_kind="qualification_phase_launch_receipt",
        )
    except ValueError as error:
        raise QualificationLauncherError(
            f"Phase-launch receipt is not registrar-authenticated: {error}"
        ) from error
    expected_keys = {
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
    assignment_ref = freeze.get("assignment_ref")
    if (
        set(verified) != expected_keys
        or verified.get("receipt_version") != PHASE_LAUNCH_RECEIPT_VERSION
        or verified.get("identity_registry_digest")
        != frozen_registry.get("identity_registry_digest")
        or verified.get("registrar_id") != frozen_registry.get("registrar_id")
        or verified.get("runner_freeze_digest") != freeze.get("runner_freeze_digest")
        or not isinstance(assignment_ref, dict)
        or verified.get("assignment_digest") != assignment_ref.get("assignment_digest")
        or verified.get("phase") != phase
        or verified.get("block") != block
        or verified.get("provider_slot") != provider_slot
        or verified.get("actor_id") != f"qualification-role:{phase}"
        or verified.get("provider") != "trusted-pre-import-launcher"
        or verified.get("execution_context_id")
        != f"qualification-context:{verified.get('session_nonce')}"
        or verified.get("qualification_authority") != "none_phase_launch_receipt_only"
        or not isinstance(verified.get("event_index"), int)
        or isinstance(verified.get("event_index"), bool)
        or int(verified["event_index"]) < 0
    ):
        raise QualificationLauncherError(
            "Registrar-signed phase-launch receipt does not bind this execution."
        )
    for field in ("session_nonce", "predecessor_artifact_digest"):
        value = verified.get(field)
        if not isinstance(value, str) or not value:
            raise QualificationLauncherError("Phase-launch receipt is incomplete.")
    predecessor = str(verified["predecessor_artifact_digest"])
    if not predecessor.startswith("sha256:") or len(predecessor) != 71:
        raise QualificationLauncherError("Phase predecessor digest is invalid.")
    try:
        int(predecessor[7:], 16)
        datetime.fromisoformat(str(verified["issued_at"]).replace("Z", "+00:00"))
    except ValueError as error:
        raise QualificationLauncherError(
            "Phase-launch receipt timestamp or digest is invalid."
        ) from error
    return verified


def launch(
    argv: list[str] | None = None,
    *,
    search_paths: Sequence[Path] | None = None,
) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "phase", choices=("freeze-oracles", "run-targets", "run-validations", "compare")
    )
    parser.add_argument("--runner-freeze", type=Path, required=True)
    parser.add_argument("--phase-launch-receipt", type=Path, required=True)
    parser.add_argument("--block", required=True, choices=("pilot", "held_out"))
    parser.add_argument("--provider-slot", required=True)
    launcher_arguments, _ = parser.parse_known_args(arguments)
    freeze = validate_pre_import_environment(
        launcher_arguments.runner_freeze,
        search_paths=search_paths,
    )
    locked_paths, _package_init, runner_path = _locked_import_paths(search_paths=search_paths)
    original_sys_path = list(sys.path)
    try:
        sys.path[:] = locked_paths
        launch_receipt = _validated_external_launch_receipt(
            launcher_arguments.phase_launch_receipt,
            freeze=freeze,
            phase=launcher_arguments.phase,
            block=launcher_arguments.block,
            provider_slot=launcher_arguments.provider_slot,
        )
        main_module = sys.modules.get("__main__")
        if main_module is None:
            raise QualificationLauncherError("Python __main__ module is unavailable.")
        setattr(main_module, APPROVED_DIGEST_ATTRIBUTE, freeze["runner_freeze_digest"])
        setattr(main_module, APPROVED_LAUNCH_RECEIPT_ATTRIBUTE, launch_receipt)
        runner = importlib.import_module(
            "sc_referee_evaluation.selected_result_qualification_runner"
        )
        imported_path = Path(str(getattr(runner, "__file__", ""))).resolve()
        if imported_path != runner_path.resolve():
            raise QualificationLauncherError(
                "Imported qualification runner is not the verified distribution file."
            )
        return int(runner.main(arguments))
    finally:
        sys.path[:] = original_sys_path


def main(argv: list[str] | None = None) -> int:
    return launch(argv)


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    raise SystemExit(main())
