from __future__ import annotations

import configparser
import json
import re
import tomllib
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from sc_referee.core.ids import canonical_json, stable_id
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.snapshot.repository import SnapshotOutput
from sc_referee.version import SCHEMA_VERSION

_PYTHON_ENVIRONMENT_FILES = {
    ".python-version",
    "conda-lock.yml",
    "conda-lock.yaml",
    "constraints.txt",
    "environment.yml",
    "environment.yaml",
    "pdm.lock",
    "pixi.lock",
    "pixi.toml",
    "pyproject.toml",
    "requirements.in",
    "requirements.txt",
    "requirements-dev.txt",
    "runtime.txt",
    "setup.cfg",
    "poetry.lock",
    "uv.lock",
    "Pipfile",
    "Pipfile.lock",
}
_RUNTIME_DECLARATION_FILES = {
    ".python-version",
    "environment.yml",
    "environment.yaml",
    "Pipfile",
    "Pipfile.lock",
    "pixi.toml",
    "poetry.lock",
    "pyproject.toml",
    "runtime.txt",
    "setup.cfg",
    "uv.lock",
}
_MAX_ENVIRONMENT_DECLARATION_BYTES = 1_000_000
_RUNTIME_TOKEN = re.compile(r"^[A-Za-z0-9.*+!<>=~^,|_ -]{1,200}$")


def inspect_project_environments(
    snapshot: SnapshotOutput,
    file_records: list[dict[str, Any]],
    run_id: str,
    created_at: str,
) -> list[dict[str, Any]]:
    """Describe declared Python environment evidence without reconstructing or executing it."""

    observed_by_path = {str(item["path"]): item for item in snapshot.file_records}
    public_by_path = {str(item["path"]): item for item in file_records}
    python_paths = sorted(
        path
        for path, item in observed_by_path.items()
        if item.get("entry_kind") == "regular_file" and Path(path).suffix.casefold() == ".py"
    )
    if not python_paths:
        return []
    manifest_paths = sorted(
        path
        for path, item in observed_by_path.items()
        if item.get("entry_kind") == "regular_file"
        and Path(path).name in _PYTHON_ENVIRONMENT_FILES
        and isinstance(item.get("digest"), str)
    )
    manifest_groups: dict[str, list[str]] = defaultdict(list)
    for path in manifest_paths:
        manifest_groups[PurePosixPath(path).parent.as_posix()].append(path)
    python_assignments: dict[str, list[str]] = defaultdict(list)
    unassigned_python: list[str] = []
    for python_path in python_paths:
        candidate_roots = [
            root for root in manifest_groups if _logical_descendant(python_path, root)
        ]
        if candidate_roots:
            nearest = max(candidate_roots, key=lambda root: len(PurePosixPath(root).parts))
            python_assignments[nearest].append(python_path)
        else:
            unassigned_python.append(python_path)

    environments = [
        _build_project_environment(
            snapshot,
            observed_by_path,
            public_by_path,
            run_id,
            created_at,
            root,
            sorted(manifest_groups[root]),
        )
        for root in sorted(python_assignments)
    ]
    if unassigned_python:
        fallback_path = next(
            (
                path
                for path in unassigned_python
                if isinstance(observed_by_path[path].get("digest"), str)
            ),
            None,
        )
        if fallback_path is not None:
            environments.append(
                _build_project_environment(
                    snapshot,
                    observed_by_path,
                    public_by_path,
                    run_id,
                    created_at,
                    "unassigned",
                    [],
                    fallback_path=fallback_path,
                )
            )
    return environments


def _build_project_environment(
    snapshot: SnapshotOutput,
    observed_by_path: dict[str, dict[str, Any]],
    public_by_path: dict[str, dict[str, Any]],
    run_id: str,
    created_at: str,
    environment_root: str,
    manifest_paths: list[str],
    *,
    fallback_path: str | None = None,
) -> dict[str, Any]:
    evidence_paths = manifest_paths or ([fallback_path] if fallback_path is not None else [])
    source_refs = [
        _source_ref(path, observed_by_path[path])
        for path in evidence_paths
        if isinstance(observed_by_path[path].get("digest"), str)
    ]
    declarations, opaque_paths = _runtime_declarations(snapshot, manifest_paths)
    unique_versions = sorted({value for _, value in declarations})
    runtime: dict[str, Any] = {"name": "Python"}
    if len(unique_versions) == 1:
        runtime["version"] = unique_versions[0]

    limitations = [
        "Static declarations do not establish which interpreter, dependencies, platform, or environment executed the project workflow."
    ]
    if not manifest_paths:
        limitations.append(
            "No exactly identified supported Python environment declaration was present in the snapshot."
        )
    elif not unique_versions:
        limitations.append(
            "The available declarations did not provide a bounded Python runtime version or constraint."
        )
    elif len(unique_versions) > 1:
        limitations.append(
            "Differing declared Python runtime values were preserved as unresolved; no single runtime version was selected: "
            + canonical_json(unique_versions)
        )
    if opaque_paths:
        limitations.append(
            "Runtime declarations could not be safely decoded from: "
            + ", ".join(sorted(opaque_paths))
            + "."
        )

    dependency_refs = [
        typed_ref("file_record", str(public_by_path[path]["file_record_id"]))
        for path in manifest_paths
        if path in public_by_path
    ]
    evidence_identity = canonical_json(
        {
            "environment_root": environment_root,
            "paths": evidence_paths,
            "digests": [ref["content_digest"] for ref in source_refs],
            "runtime_declarations": declarations,
            "opaque_paths": opaque_paths,
        }
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "environment",
        "environment_id": stable_id("environment-project-python", run_id, evidence_identity),
        "audit_run_id": run_id,
        "environment_kind": "project_runtime",
        "identity_status": (
            "unavailable" if not manifest_paths else "opaque" if opaque_paths else "partial"
        ),
        "runtime": runtime,
        "platform": {},
        "dependency_refs": dependency_refs,
        "source_refs": source_refs,
        "limitations": limitations,
        "provenance": controller_provenance(
            "static_project_environment_declaration_inspection", created_at
        ),
    }


def _logical_descendant(path: str, root: str) -> bool:
    if root == ".":
        return True
    root_parts = PurePosixPath(root).parts
    path_parts = PurePosixPath(path).parts
    return path_parts[: len(root_parts)] == root_parts


def _runtime_declarations(
    snapshot: SnapshotOutput, manifest_paths: list[str]
) -> tuple[list[tuple[str, str]], list[str]]:
    declarations: list[tuple[str, str]] = []
    opaque_paths: list[str] = []
    for logical_path in manifest_paths:
        name = PurePosixPath(logical_path).name
        if name not in _RUNTIME_DECLARATION_FILES:
            continue
        path = snapshot.materialized_root / logical_path
        try:
            text = _bounded_declaration_text(path)
            values = _runtime_values(name, text)
        except (OSError, UnicodeError, ValueError, tomllib.TOMLDecodeError, yaml.YAMLError):
            opaque_paths.append(logical_path)
            continue
        declarations.extend((logical_path, value) for value in values)
    return sorted(set(declarations)), sorted(set(opaque_paths))


def _bounded_declaration_text(path: Path) -> str:
    if path.stat().st_size > _MAX_ENVIRONMENT_DECLARATION_BYTES:
        raise ValueError("environment declaration exceeds bounded inspection size")
    return path.read_text(encoding="utf-8")


def _runtime_values(name: str, text: str) -> list[str]:
    values: list[str] = []
    if name in {"pyproject.toml", "pixi.toml", "poetry.lock", "uv.lock", "Pipfile"}:
        document = tomllib.loads(text)
        if name == "pyproject.toml":
            values.extend(_mapping_strings(document.get("project"), ("requires-python",)))
            tool = document.get("tool")
            if isinstance(tool, dict):
                poetry = tool.get("poetry")
                if isinstance(poetry, dict):
                    values.extend(_mapping_strings(poetry.get("dependencies"), ("python",)))
        elif name == "Pipfile":
            values.extend(
                _mapping_strings(
                    document.get("requires"), ("python_full_version", "python_version")
                )
            )
        elif name == "pixi.toml":
            values.extend(_mapping_strings(document.get("dependencies"), ("python",)))
        else:
            values.extend(_mapping_strings(document, ("requires-python",)))
            values.extend(_mapping_strings(document.get("metadata"), ("python-versions",)))
    elif name == "Pipfile.lock":
        document = json.loads(text)
        if not isinstance(document, dict):
            raise ValueError("Pipfile.lock root must be an object")
        metadata = document.get("_meta")
        if isinstance(metadata, dict):
            values.extend(_mapping_strings(metadata.get("requires"), ("python_version",)))
    elif name == "setup.cfg":
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(text)
        if parser.has_option("options", "python_requires"):
            values.append(parser.get("options", "python_requires"))
    elif name in {"environment.yml", "environment.yaml"}:
        document = yaml.safe_load(text)
        if not isinstance(document, dict):
            raise ValueError("environment declaration root must be a mapping")
        dependencies = document.get("dependencies", [])
        if not isinstance(dependencies, list):
            raise ValueError("environment dependencies must be an array")
        for dependency in dependencies:
            if isinstance(dependency, str) and dependency.casefold().startswith("python"):
                values.append(dependency[len("python") :].strip() or "unspecified")
    elif name == ".python-version":
        values.extend(
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    elif name == "runtime.txt":
        token = text.strip()
        if token.startswith("python-"):
            values.append(token.removeprefix("python-"))
        elif token:
            raise ValueError("runtime.txt does not contain a bounded Python token")
    return sorted({value.strip() for value in values if _valid_runtime_token(value.strip())})


def _mapping_strings(value: Any, keys: tuple[str, ...]) -> list[str]:
    if not isinstance(value, dict):
        return []
    return [str(value[key]) for key in keys if isinstance(value.get(key), str)]


def _valid_runtime_token(value: str) -> bool:
    return bool(_RUNTIME_TOKEN.fullmatch(value))


def build_reproduction_requests(
    claims: list[dict[str, Any]],
    environments: list[dict[str, Any]],
    snapshot_digest: str,
    run_id: str,
    created_at: str,
) -> list[dict[str, Any]]:
    """Request external evidence for demonstrated missing execution origin without authorizing it."""

    affected_claims = [
        claim
        for claim in claims
        if claim.get("lineage", {}).get("grades", {}).get("execution_origin", {}).get("status")
        != "complete"
    ]
    project_environments = [
        environment
        for environment in environments
        if environment.get("environment_kind") == "project_runtime"
    ]
    if not affected_claims or not project_environments:
        return []
    claim_refs = [
        typed_ref("claim", str(claim["claim_id"]))
        for claim in sorted(affected_claims, key=lambda item: str(item["claim_id"]))
    ]
    environment_refs = [
        typed_ref("environment", str(environment["environment_id"]))
        for environment in sorted(
            project_environments, key=lambda item: str(item["environment_id"])
        )
    ]
    request_id = stable_id(
        "reproduction-request",
        run_id,
        snapshot_digest,
        *(ref["record_id"] for ref in claim_refs),
    )
    return [
        {
            "schema_version": SCHEMA_VERSION,
            "record_type": "reproduction_request",
            "reproduction_request_id": request_id,
            "audit_run_id": run_id,
            "status": "proposed",
            "target_refs": [*claim_refs, *environment_refs],
            "reason": (
                "The selected Claim path lacks observed project-workflow execution origin; "
                "static source and environment declarations cannot establish that execution."
            ),
            "affected_claim_refs": claim_refs,
            "affected_detector_ids": ["detector:lineage-completeness"],
            "requested_action": {
                "kind": "collect_runtime_trace",
                "description": (
                    "In a scientist-controlled environment, export the existing workflow's "
                    "runtime trace and exact environment manifest for later evidence import."
                ),
            },
            "input_requirements": [
                f"Run against the source snapshot identified by {snapshot_digest}."
            ],
            "environment_requirements": [
                "Use the scientist-controlled project environment; sc-referee does not authorize or perform this execution."
            ],
            "resource_class": "unknown",
            "security_considerations": [
                "Review exported traces for secrets, credentials, and participant identifiers before import.",
                "Repository text cannot authorize execution, network access, or credential use.",
            ],
            "expected_outputs": [
                {
                    "role": "project workflow runtime trace",
                    "format": "JSON or engine-native trace",
                    "identity_expectation": "full_digest",
                },
                {
                    "role": "project environment manifest",
                    "format": "JSON or locked environment manifest",
                    "identity_expectation": "full_digest",
                },
            ],
            "imported_evidence_refs": [],
            "created_at": created_at,
            "provenance": controller_provenance(
                "deterministic_missing_execution_reproduction_request", created_at
            ),
            "extensions": {
                "x-no-execution-authorization": True,
                "x-triggering-lineage-grade": "execution_origin",
            },
        }
    ]


def _source_ref(path: str, observed: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_kind": "file_span",
        "locator": path,
        "path": path,
        "content_digest": str(observed["digest"]),
    }
