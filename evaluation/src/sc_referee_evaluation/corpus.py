from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import UUID

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once


class CorpusPreflightError(ValueError):
    """A local public-corpus package cannot enter answer-blind preparation."""


GENEBENCH_PUBLIC_SOURCE_URI = "https://huggingface.co/datasets/openai/genebench-pro-public-package"
_PREFLIGHT_VERSION = "0.2.0"
_MAX_METADATA_BYTES = 1_048_576
_SHA256 = re.compile(r"[0-9a-f]{64}")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_REVISION = re.compile(r"[0-9a-f]{40}")
_EVAL_ID = re.compile(r"[a-z0-9]+(?:_[a-z0-9]+)*")
_CHECKSUM_LINE = re.compile(r"([0-9a-f]{64})  (.+)")
_MANIFEST_KEYS = {"name", "version", "description", "problem_count", "layout", "problems"}
_LAYOUT_KEYS = {
    "problem_directories",
    "required_files_per_problem",
    "top_level_reference_files",
}
_PROBLEM_KEYS = {
    "release_order",
    "eval_id",
    "title",
    "domain",
    "eval_uuid",
    "problem_dir",
    "eval_config",
    "report",
    "data_files",
    "grader_type",
    "answer_fields",
    "files",
}
_PROBLEM_FILE_KEYS = {"path", "bytes", "sha256"}
_CONFIG_KEYS = {"id", "eval_uuid", "task", "data_files", "ground_truth", "grader"}
_ALLOWED_UNCHECKED_NAMES = {".DS_Store", "checksums.sha256"}


def preflight_genebench_public_package(
    package_root: Path,
    *,
    source_revision: str,
    expected_manifest_digest: str,
    expected_checksums_digest: str,
    output: Path | None = None,
) -> dict[str, Any]:
    """Verify a local public package without executing its grader or disclosing answers."""

    if output is not None and (output.exists() or output.is_symlink()):
        raise CorpusPreflightError(f"Corpus preflight output already exists: {output}")
    if not _REVISION.fullmatch(source_revision):
        raise CorpusPreflightError("Source revision must be one full lowercase Git commit digest.")
    for label, digest in (
        ("manifest", expected_manifest_digest),
        ("checksums", expected_checksums_digest),
    ):
        if not _DIGEST.fullmatch(digest):
            raise CorpusPreflightError(f"Expected {label} digest must be one sha256 digest.")

    root = _validated_root(package_root)
    if output is not None:
        resolved_output = output.parent.resolve() / output.name
        if resolved_output.is_relative_to(root):
            raise CorpusPreflightError(
                "Corpus preflight output must remain outside the package root."
            )
    manifest_bytes = _read_metadata(root, "manifest.json")
    checksums_bytes = _read_metadata(root, "checksums.sha256")
    if sha256_digest(manifest_bytes) != expected_manifest_digest:
        raise CorpusPreflightError("Package manifest does not match the supplied external digest.")
    if sha256_digest(checksums_bytes) != expected_checksums_digest:
        raise CorpusPreflightError("Package checksum inventory does not match the supplied digest.")

    manifest = _load_object(manifest_bytes, "manifest.json")
    _validate_manifest_header(manifest)
    checksums = _parse_checksums(checksums_bytes)
    ignored_paths = _validate_inventory(root, set(checksums))
    observed = _verify_checksums(root, checksums)
    problems = _validate_problems(root, manifest, checksums, observed)
    license_projection = _license_projection(root)
    structural_digest = semantic_digest(
        {
            "source_revision": source_revision,
            "manifest_digest": expected_manifest_digest,
            "checksums_digest": expected_checksums_digest,
            "problems": problems,
        }
    )
    run_admission = (
        "admitted_for_public_development_preparation"
        if license_projection["status"] == "consistent"
        else "requires_human_license_resolution"
    )
    report: dict[str, Any] = {
        "corpus_preflight_version": _PREFLIGHT_VERSION,
        "record_type": "evaluation_corpus_preflight",
        "preflight_id": stable_id(
            "corpus-preflight",
            GENEBENCH_PUBLIC_SOURCE_URI,
            source_revision,
            expected_manifest_digest,
            expected_checksums_digest,
            structural_digest,
        ),
        "source": {
            "uri": GENEBENCH_PUBLIC_SOURCE_URI,
            "revision": source_revision,
            "revision_binding_status": "declared_immutable_revision_with_supplied_payload_digests",
            "manifest_digest": expected_manifest_digest,
            "checksums_digest": expected_checksums_digest,
        },
        "package": {
            "name": manifest["name"],
            "version": manifest["version"],
            "problem_count": manifest["problem_count"],
        },
        "integrity": {
            "status": "verified",
            "checked_file_count": len(checksums),
            "checked_byte_count": sum(item["byte_size"] for item in observed.values()),
            "unexpected_file_count": 0,
            "ignored_platform_metadata_paths": ignored_paths,
        },
        "license": license_projection,
        "run_admission_status": run_admission,
        "corpus_partition_ceiling": "public_development",
        "held_out_eligible": False,
        "promotion_evidence_eligible": False,
        "answer_side_artifact": True,
        "agent_workspace_eligible": False,
        "ground_truth_disclosed_to_agent_workspace": False,
        "project_code_executed": False,
        "model_invoked": False,
        "problems": problems,
        "limitations": [
            "Ground truth, grader contracts, reference reports, and grader code are public and may have been seen during model training.",
            "This package can exercise public-development mechanics but cannot establish held-out qualification or promotion evidence.",
            "The supplied revision is declared; an external retrieval record must bind it to the verified payload digests.",
            "Preflight performs bounded static reads and checksum verification only; it does not execute or import the reference grader.",
            "Reviewer identity, independence, scientific label correctness, and execution evidence are not established by corpus preflight.",
        ],
    }
    report["preflight_digest"] = semantic_digest(report)
    if output is not None:
        write_normalized_json_once(output, report)
    return report


def _validated_root(package_root: Path) -> Path:
    if package_root.is_symlink() or not package_root.is_dir():
        raise CorpusPreflightError("Corpus package root must be one non-symlink directory.")
    return package_root.resolve()


def _read_metadata(root: Path, path_value: str) -> bytes:
    path = _resolve_regular(root, path_value)
    size = path.stat().st_size
    if size > _MAX_METADATA_BYTES:
        raise CorpusPreflightError(f"Corpus metadata file {path_value!r} exceeds the read limit.")
    return path.read_bytes()


def _load_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, CorpusPreflightError) as error:
        raise CorpusPreflightError(
            f"Corpus metadata {label!r} is not strict JSON: {error}"
        ) from error
    if not isinstance(value, dict):
        raise CorpusPreflightError(f"Corpus metadata {label!r} must contain one JSON object.")
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise CorpusPreflightError(f"Duplicate JSON key {key!r} is not permitted.")
        value[key] = item
    return value


def _validate_manifest_header(manifest: dict[str, Any]) -> None:
    if set(manifest) != _MANIFEST_KEYS:
        raise CorpusPreflightError("GeneBench package manifest has unexpected top-level fields.")
    if not all(
        isinstance(manifest.get(key), str) and manifest[key]
        for key in ("name", "version", "description")
    ):
        raise CorpusPreflightError("GeneBench package identity fields must be nonempty strings.")
    layout = manifest.get("layout")
    if not isinstance(layout, dict) or set(layout) != _LAYOUT_KEYS:
        raise CorpusPreflightError("GeneBench package layout is malformed.")
    if layout.get("problem_directories") != "problems/<eval_id>/":
        raise CorpusPreflightError("GeneBench problem-directory contract has changed.")
    if layout.get("required_files_per_problem") != [
        "eval_config.json",
        "data_files/",
        "report_public.pdf",
    ]:
        raise CorpusPreflightError("GeneBench required problem files have changed.")
    references = layout.get("top_level_reference_files")
    if (
        not isinstance(references, list)
        or not references
        or not all(isinstance(value, str) and value for value in references)
        or len(set(references)) != len(references)
    ):
        raise CorpusPreflightError("GeneBench top-level reference inventory is malformed.")
    problems = manifest.get("problems")
    if (
        not isinstance(problems, list)
        or not problems
        or manifest.get("problem_count") != len(problems)
    ):
        raise CorpusPreflightError("GeneBench problem count does not match its manifest.")


def _parse_checksums(payload: bytes) -> dict[str, str]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CorpusPreflightError("Checksum inventory is not UTF-8.") from error
    if not text.endswith("\n"):
        raise CorpusPreflightError("Checksum inventory must end with one newline.")
    checksums: dict[str, str] = {}
    paths: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = _CHECKSUM_LINE.fullmatch(line)
        if match is None:
            raise CorpusPreflightError(f"Malformed checksum inventory line {line_number}.")
        digest, path_value = match.groups()
        path = _safe_relative_path(path_value)
        normalized = path.as_posix()
        if normalized in checksums:
            raise CorpusPreflightError(f"Duplicate checksum path {normalized!r}.")
        if normalized == "checksums.sha256":
            raise CorpusPreflightError("Checksum inventory cannot recursively include itself.")
        checksums[normalized] = "sha256:" + digest
        paths.append(normalized)
    if not checksums or paths != sorted(paths):
        raise CorpusPreflightError("Checksum inventory must be nonempty and path-sorted.")
    return checksums


def _validate_inventory(root: Path, expected_paths: set[str]) -> list[str]:
    observed_paths: set[str] = set()
    ignored: list[str] = []
    for directory, names, files in os.walk(root, topdown=True, followlinks=False):
        directory_path = Path(directory)
        retained_names: list[str] = []
        for name in names:
            path = directory_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                raise CorpusPreflightError(f"Corpus package contains symlink {relative!r}.")
            if name == ".git" and directory_path == root:
                ignored.append(".git/")
                continue
            retained_names.append(name)
        names[:] = retained_names
        for name in files:
            path = directory_path / name
            relative = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                raise CorpusPreflightError(
                    f"Corpus package entry {relative!r} must be a regular file."
                )
            if name == ".DS_Store":
                ignored.append(relative)
                continue
            observed_paths.add(relative)
    expected_inventory = {*expected_paths, "checksums.sha256"}
    missing = sorted(expected_inventory - observed_paths)
    unexpected = sorted(observed_paths - expected_inventory)
    if missing or unexpected:
        raise CorpusPreflightError(
            f"Corpus package inventory drifted; missing={missing}, unexpected={unexpected}."
        )
    return sorted(ignored)


def _verify_checksums(root: Path, checksums: dict[str, str]) -> dict[str, dict[str, Any]]:
    observed: dict[str, dict[str, Any]] = {}
    for path_value, expected_digest in checksums.items():
        path = _resolve_regular(root, path_value)
        digest, byte_size = _stream_digest(path)
        if digest != expected_digest:
            raise CorpusPreflightError(f"Corpus file {path_value!r} has checksum drift.")
        observed[path_value] = {"content_digest": digest, "byte_size": byte_size}
    return observed


def _validate_problems(
    root: Path,
    manifest: dict[str, Any],
    checksums: dict[str, str],
    observed: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    layout = manifest["layout"]
    references = {
        _safe_relative_path(value).as_posix() for value in layout["top_level_reference_files"]
    }
    expected_references = {path for path in checksums if "/" not in path} | {"checksums.sha256"}
    if references != expected_references:
        raise CorpusPreflightError("Top-level reference files do not equal the checksum inventory.")

    manifest_problems = manifest["problems"]
    release_orders = [problem.get("release_order") for problem in manifest_problems]
    if release_orders != list(range(len(manifest_problems))):
        raise CorpusPreflightError("GeneBench release orders must be contiguous and ordered.")
    seen_ids: set[str] = set()
    seen_uuids: set[str] = set()
    problem_paths: set[str] = set()
    projections: list[dict[str, Any]] = []
    for problem in manifest_problems:
        if not isinstance(problem, dict) or set(problem) != _PROBLEM_KEYS:
            raise CorpusPreflightError("GeneBench problem manifest has unexpected fields.")
        projection, files = _validate_problem(root, problem, checksums, observed)
        eval_id = str(problem["eval_id"])
        eval_uuid = str(problem["eval_uuid"])
        if eval_id in seen_ids or eval_uuid in seen_uuids:
            raise CorpusPreflightError("GeneBench problem identities must be unique.")
        seen_ids.add(eval_id)
        seen_uuids.add(eval_uuid)
        problem_paths.update(files)
        projections.append(projection)
    checksum_problem_paths = {path for path in checksums if path.startswith("problems/")}
    if problem_paths != checksum_problem_paths:
        raise CorpusPreflightError("Problem manifests do not exactly cover checksum problem files.")
    return projections


def _validate_problem(
    root: Path,
    problem: dict[str, Any],
    checksums: dict[str, str],
    observed: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], set[str]]:
    eval_id = problem.get("eval_id")
    if not isinstance(eval_id, str) or _EVAL_ID.fullmatch(eval_id) is None:
        raise CorpusPreflightError("GeneBench eval_id is not one safe identifier.")
    try:
        parsed_uuid = UUID(str(problem.get("eval_uuid", "")))
    except ValueError as error:
        raise CorpusPreflightError(f"GeneBench problem {eval_id!r} has an invalid UUID.") from error
    if str(parsed_uuid) != problem.get("eval_uuid"):
        raise CorpusPreflightError(f"GeneBench problem {eval_id!r} UUID is not canonical.")
    if not all(
        isinstance(problem.get(key), str) and problem[key]
        for key in ("title", "domain", "grader_type")
    ):
        raise CorpusPreflightError(f"GeneBench problem {eval_id!r} metadata is incomplete.")

    problem_dir = f"problems/{eval_id}"
    config_path = f"{problem_dir}/eval_config.json"
    report_path = f"{problem_dir}/report_public.pdf"
    if (
        problem.get("problem_dir") != problem_dir
        or problem.get("eval_config") != config_path
        or problem.get("report") != report_path
    ):
        raise CorpusPreflightError(f"GeneBench problem {eval_id!r} path contract drifted.")
    data_files = _string_list(problem.get("data_files"), f"{eval_id} data files")
    if not data_files or len(set(data_files)) != len(data_files):
        raise CorpusPreflightError(
            f"GeneBench problem {eval_id!r} data files are empty or duplicated."
        )
    for path_value in data_files:
        path = _safe_relative_path(path_value).as_posix()
        if not path.startswith(f"{problem_dir}/data_files/"):
            raise CorpusPreflightError(
                f"GeneBench problem {eval_id!r} has an out-of-scope data path."
            )

    files = problem.get("files")
    if not isinstance(files, list) or not files:
        raise CorpusPreflightError(f"GeneBench problem {eval_id!r} file manifest is empty.")
    file_paths: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or set(item) != _PROBLEM_FILE_KEYS:
            raise CorpusPreflightError(f"GeneBench problem {eval_id!r} file entry is malformed.")
        path_value = _safe_relative_path(str(item.get("path", ""))).as_posix()
        if path_value in file_paths or not path_value.startswith(problem_dir + "/"):
            raise CorpusPreflightError(f"GeneBench problem {eval_id!r} file path is invalid.")
        byte_size = item.get("bytes")
        raw_digest = item.get("sha256")
        if (
            not isinstance(byte_size, int)
            or isinstance(byte_size, bool)
            or byte_size < 0
            or not isinstance(raw_digest, str)
            or _SHA256.fullmatch(raw_digest) is None
            or checksums.get(path_value) != "sha256:" + raw_digest
            or observed.get(path_value)
            != {"content_digest": "sha256:" + raw_digest, "byte_size": byte_size}
        ):
            raise CorpusPreflightError(f"GeneBench problem {eval_id!r} file identity drifted.")
        file_paths.add(path_value)
    expected_files = {config_path, report_path, *data_files}
    if file_paths != expected_files:
        raise CorpusPreflightError(f"GeneBench problem {eval_id!r} file set is incomplete.")

    config_bytes = _read_metadata(root, config_path)
    config = _load_object(config_bytes, config_path)
    if set(config) != _CONFIG_KEYS:
        raise CorpusPreflightError(f"GeneBench problem {eval_id!r} config fields changed.")
    if config.get("id") != eval_id or config.get("eval_uuid") != problem["eval_uuid"]:
        raise CorpusPreflightError(f"GeneBench problem {eval_id!r} config identity drifted.")
    task = config.get("task")
    ground_truth = config.get("ground_truth")
    grader = config.get("grader")
    if (
        not isinstance(task, str)
        or not task
        or not isinstance(ground_truth, dict)
        or not ground_truth
        or not isinstance(grader, dict)
        or set(grader) != {"type", "config"}
        or grader.get("type") != problem["grader_type"]
        or not isinstance(grader.get("config"), dict)
    ):
        raise CorpusPreflightError(
            f"GeneBench problem {eval_id!r} answer-side config is malformed."
        )
    answer_fields = _string_list(problem.get("answer_fields"), f"{eval_id} answer fields")
    if (
        not answer_fields
        or len(set(answer_fields)) != len(answer_fields)
        or set(answer_fields) != set(ground_truth)
    ):
        raise CorpusPreflightError(f"GeneBench problem {eval_id!r} answer fields drifted.")
    config_data_files = _string_list(config.get("data_files"), f"{eval_id} config data files")
    resolved_config_files = [
        f"{problem_dir}/{_safe_relative_path(path_value).as_posix()}"
        for path_value in config_data_files
    ]
    if resolved_config_files != data_files:
        raise CorpusPreflightError(f"GeneBench problem {eval_id!r} visible data set drifted.")

    visible_inputs = [
        {
            "source_path": path_value,
            "workspace_path": path_value.removeprefix(problem_dir + "/"),
            **observed[path_value],
        }
        for path_value in sorted(data_files)
    ]
    return (
        {
            "release_order": problem["release_order"],
            "eval_id": eval_id,
            "eval_uuid": problem["eval_uuid"],
            "title": problem["title"],
            "domain": problem["domain"],
            "answer_fields": sorted(answer_fields),
            "eval_config": {
                "path": config_path,
                "content_digest": observed[config_path]["content_digest"],
                "semantic_digest": semantic_digest(config),
            },
            "task": {
                "workspace_path": "task.md",
                "content_digest": sha256_digest(task),
                "byte_size": len(task.encode("utf-8")),
            },
            "ground_truth_semantic_digest": semantic_digest(ground_truth),
            "grader_semantic_digest": semantic_digest(grader),
            "visible_inputs": visible_inputs,
            "runner_only_paths": sorted(
                {
                    config_path,
                    report_path,
                    *[str(value) for value in manifest_reference_paths(root)],
                }
            ),
            "blind_workspace_plan": {
                "task_output_path": "task.md",
                "visible_data_paths": [item["workspace_path"] for item in visible_inputs],
                "answer_side_config_copied": False,
                "reference_report_copied": False,
                "reference_grader_copied": False,
                "project_code_execution_authorized": False,
            },
        },
        file_paths,
    )


def manifest_reference_paths(root: Path) -> list[str]:
    manifest = _load_object(_read_metadata(root, "manifest.json"), "manifest.json")
    layout = manifest.get("layout")
    if not isinstance(layout, dict):  # pragma: no cover - validated before problem projection
        raise CorpusPreflightError("GeneBench package layout is malformed.")
    return _string_list(layout.get("top_level_reference_files"), "top-level reference files")


def _license_projection(root: Path) -> dict[str, Any]:
    readme = _read_metadata(root, "README.md")
    license_payload = _read_metadata(root, "LICENSE")
    metadata_identifier = _card_license(readme)
    detected_identifier = _license_identifier(license_payload)
    status = (
        "consistent"
        if _normalized_license(metadata_identifier) == _normalized_license(detected_identifier)
        else "conflicted_metadata_and_license_file"
    )
    return {
        "metadata_identifier": metadata_identifier,
        "license_file_identifier": detected_identifier,
        "license_file_digest": sha256_digest(license_payload),
        "status": status,
        "redistribution_permitted_by_sc_referee": False,
        "legal_conclusion_made": False,
    }


def _card_license(payload: bytes) -> str:
    try:
        lines = payload.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise CorpusPreflightError("Dataset card is not UTF-8.") from error
    if not lines or lines[0] != "---":
        raise CorpusPreflightError("Dataset card has no bounded metadata front matter.")
    closing = next((index for index, line in enumerate(lines[1:], start=1) if line == "---"), None)
    if closing is None:
        raise CorpusPreflightError("Dataset card metadata front matter is unterminated.")
    values = [
        line.split(":", 1)[1].strip() for line in lines[1:closing] if line.startswith("license:")
    ]
    if len(values) != 1 or not values[0] or any(character.isspace() for character in values[0]):
        raise CorpusPreflightError("Dataset card license metadata is missing or ambiguous.")
    return values[0]


def _license_identifier(payload: bytes) -> str:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CorpusPreflightError("License file is not UTF-8.") from error
    if text.startswith("MIT License\n"):
        return "MIT"
    if "Creative Commons Attribution 4.0 International" in text:
        return "CC-BY-4.0"
    return "unrecognized"


def _normalized_license(value: str) -> str:
    return value.casefold().replace("_", "-")


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise CorpusPreflightError(f"GeneBench {label} must be nonempty strings.")
    return value


def _resolve_regular(root: Path, path_value: str) -> Path:
    relative = _safe_relative_path(path_value)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise CorpusPreflightError(f"Corpus path {path_value!r} crosses a symlink.")
    if not current.is_file():
        raise CorpusPreflightError(f"Corpus path {path_value!r} is not one regular file.")
    return current


def _safe_relative_path(path_value: str) -> PurePosixPath:
    path = PurePosixPath(path_value)
    if (
        not path_value
        or "\\" in path_value
        or path.is_absolute()
        or path.as_posix() != path_value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise CorpusPreflightError(f"Unsafe corpus-relative path {path_value!r}.")
    return path


def _stream_digest(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1_048_576):
            digest.update(chunk)
            byte_size += len(chunk)
    return "sha256:" + digest.hexdigest(), byte_size


__all__ = [
    "GENEBENCH_PUBLIC_SOURCE_URI",
    "CorpusPreflightError",
    "preflight_genebench_public_package",
]
