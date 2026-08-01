from __future__ import annotations

import copy
import fcntl
import os
import stat
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.cache_auth import (
    CACHE_AUTHENTICATION_PROFILE,
    CacheAuthenticationKey,
    CacheKeyProvider,
    EnvironmentOrPlatformCacheKeyProvider,
    authenticate_cache_document,
    verify_cache_document,
)
from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.parsers.cell_language_bridge import inspect_embedded_cell_sources
from sc_referee.parsers.jupyter_inventory import inspect_jupyter
from sc_referee.parsers.markdown_claims import inspect_markdown
from sc_referee.parsers.python_ast import PARSER_ID as PYTHON_PARSER_ID
from sc_referee.parsers.python_ast import PARSER_VERSION as PYTHON_PARSER_VERSION
from sc_referee.parsers.python_ast import inspect_python
from sc_referee.parsers.quarto_inventory import inspect_quarto
from sc_referee.parsers.r_dual import inspect_r
from sc_referee.parsers.rmarkdown_inventory import inspect_rmarkdown
from sc_referee.records.normalization import write_normalized_json
from sc_referee.snapshot.repository import SnapshotOutput
from sc_referee.version import SCHEMA_VERSION, __version__

_CACHE_FORMAT = "sc-referee-project-parser-cache-v3"
_INDEX_FORMAT = "sc-referee-project-parser-index-v3"
_DESCENDANT_CACHE_FORMAT = "sc-referee-project-descendant-cache-v2"
_DESCENDANT_INDEX_FORMAT = "sc-referee-project-descendant-index-v2"
_CACHE_RELATIVE_ROOT = Path(".sc-referee") / "cache" / "v1"
_CACHE_LEASE_FILENAME = ".writer.lock"
_PARSER_COMPONENTS = {
    ".ipynb": ("parser:jupyter-notebook-inventory", "0.2.0"),
    ".py": (PYTHON_PARSER_ID, PYTHON_PARSER_VERSION),
    ".qmd": ("parser:quarto-source-inventory", "0.2.0"),
    ".md": ("parser:markdown-inventory", "0.2.0"),
    ".markdown": ("parser:markdown-inventory", "0.2.0"),
    ".r": ("parser:r-dual-static-inventory", "0.1.0"),
    ".rmd": ("parser:rmarkdown-selected-report-inventory", "0.1.0"),
}


@dataclass
class ProjectCacheLease:
    """One nonblocking project-cache writer lease held across a controller cache phase."""

    descriptor: int
    path: Path
    _closed: bool = field(default=False, init=False)

    def close(self) -> None:
        if self._closed:
            return
        try:
            fcntl.flock(self.descriptor, fcntl.LOCK_UN)
        finally:
            os.close(self.descriptor)
            self._closed = True


@dataclass(frozen=True)
class ParserCacheResult:
    parser_results: list[dict[str, Any]]
    cache_entries: list[dict[str, Any]]
    cache_policy: dict[str, Any]
    summary: dict[str, Any]
    cache_root: Path | None
    project_identity: str
    policy_digest: str
    cache_keys_by_path: dict[str, str]
    cache_lease: ProjectCacheLease | None = field(repr=False, compare=False)
    authentication_key: CacheAuthenticationKey | None = field(repr=False, compare=False)

    def close(self) -> None:
        if self.cache_lease is not None:
            self.cache_lease.close()


@dataclass(frozen=True)
class DescendantCacheHandle:
    category: str
    scope_key: str
    component_id: str
    component_version: str
    input_digests: tuple[str, ...]
    cache_key: str
    cache_status: str
    replaced: bool
    cacheable: bool


@dataclass
class DescendantCacheSession:
    """Cache deterministic public-record descendants under exact project-local keys."""

    cache_root: Path | None
    project_identity: str
    policy_digest: str
    created_at: str
    authentication_key: CacheAuthenticationKey | None = field(repr=False)
    previous_index: dict[str, dict[str, Any]] = field(init=False)
    current_index: dict[str, dict[str, Any]] = field(default_factory=dict, init=False)
    cache_entries: list[dict[str, Any]] = field(default_factory=list, init=False)
    hits: list[str] = field(default_factory=list, init=False)
    misses: list[str] = field(default_factory=list, init=False)
    uncacheable: list[str] = field(default_factory=list, init=False)
    invalidations: set[str] = field(default_factory=set, init=False)

    def __post_init__(self) -> None:
        self.previous_index = (
            _load_descendant_index(
                self.cache_root,
                self.project_identity,
                self.authentication_key,
            )
            if self.cache_root is not None and self.authentication_key is not None
            else {}
        )

    @classmethod
    def from_parser_cache(
        cls, parser_cache: ParserCacheResult, created_at: str
    ) -> DescendantCacheSession:
        return cls(
            cache_root=parser_cache.cache_root,
            project_identity=parser_cache.project_identity,
            policy_digest=parser_cache.policy_digest,
            created_at=created_at,
            authentication_key=parser_cache.authentication_key,
        )

    def resolve(
        self,
        *,
        category: str,
        scope_key: str,
        component_id: str,
        component_version: str,
        input_digests: list[str],
        compute: Callable[[], dict[str, Any]],
    ) -> tuple[dict[str, Any], DescendantCacheHandle]:
        normalized_inputs = tuple(sorted(set(input_digests)))
        cacheable = (
            self.cache_root is not None
            and bool(normalized_inputs)
            and all(value.startswith("sha256:") for value in normalized_inputs)
        )
        cache_key = semantic_digest(
            {
                "cache_format": _DESCENDANT_CACHE_FORMAT,
                "project_identity": self.project_identity,
                "category": category,
                "scope_key": scope_key,
                "component_id": component_id,
                "component_version": component_version,
                "tool_version": __version__,
                "schema_version": SCHEMA_VERSION,
                "input_digests": normalized_inputs,
                "policy_digest": self.policy_digest,
            }
        )
        index_key = f"{category}:{scope_key}"
        previous = self.previous_index.get(index_key)
        replaced = previous is not None and previous.get("cache_key") != cache_key
        if replaced:
            self.invalidations.add(index_key)
        index_matches = previous == {
            "cache_key": cache_key,
            "category": category,
            "scope_key": scope_key,
            "input_digests": list(normalized_inputs),
        }
        cached = (
            _load_descendant_payload(
                self.cache_root,
                cache_key,
                project_identity=self.project_identity,
                category=category,
                scope_key=scope_key,
                input_digests=normalized_inputs,
                policy_digest=self.policy_digest,
                authentication_key=self.authentication_key,
            )
            if cacheable and index_matches
            else None
        )
        if cached is None:
            payload = compute()
            cache_status = "miss"
            persisted = False
            if cacheable and self.cache_root is not None:
                persisted = _write_descendant_payload(
                    self.cache_root,
                    cache_key,
                    project_identity=self.project_identity,
                    category=category,
                    scope_key=scope_key,
                    input_digests=normalized_inputs,
                    policy_digest=self.policy_digest,
                    payload=payload,
                    authentication_key=self.authentication_key,
                )
            if cacheable:
                self.misses.append(index_key)
                if not persisted:
                    self.uncacheable.append(index_key)
            else:
                self.uncacheable.append(index_key)
        else:
            payload = cached
            cache_status = "hit"
            persisted = True
            self.hits.append(index_key)
        effective_cacheable = cacheable and persisted
        if effective_cacheable:
            self.current_index[index_key] = {
                "cache_key": cache_key,
                "category": category,
                "scope_key": scope_key,
                "input_digests": list(normalized_inputs),
            }
        return payload, DescendantCacheHandle(
            category=category,
            scope_key=scope_key,
            component_id=component_id,
            component_version=component_version,
            input_digests=normalized_inputs,
            cache_key=cache_key,
            cache_status=cache_status,
            replaced=replaced,
            cacheable=effective_cacheable,
        )

    def record_outputs(
        self, handle: DescendantCacheHandle, output_records: list[dict[str, Any]]
    ) -> None:
        if not handle.cacheable:
            return
        self.cache_entries.append(
            _descendant_cache_entry(
                handle=handle,
                output_records=output_records,
                project_identity=self.project_identity,
                policy_digest=self.policy_digest,
                created_at=self.created_at,
            )
        )

    def finalize(self) -> dict[str, Any]:
        for index_key in self.previous_index:
            if index_key not in self.current_index:
                self.invalidations.add(index_key)
        if self.cache_root is not None:
            _write_descendant_index(
                self.cache_root,
                self.project_identity,
                self.current_index,
                self.authentication_key,
            )
        return {
            "cache_format": _DESCENDANT_CACHE_FORMAT,
            "hits": len(self.hits),
            "misses": len(self.misses),
            "invalidations": len(self.invalidations),
            "hit_keys": sorted(self.hits),
            "miss_keys": sorted(self.misses),
            "invalidated_keys": sorted(self.invalidations),
            "uncacheable_keys": sorted(self.uncacheable),
        }


def inspect_supported_sources_with_cache(
    snapshot: SnapshotOutput,
    repository: Path,
    run_id: str,
    created_at: str,
    *,
    key_provider: CacheKeyProvider | None = None,
) -> ParserCacheResult:
    """Parse supported immutable files with a repository-bound content-addressed cache."""

    repository = repository.resolve()
    project_identity = sha256_digest(str(repository))
    authentication_key: CacheAuthenticationKey | None
    unavailable_reason: str | None
    try:
        key_resolution = (key_provider or EnvironmentOrPlatformCacheKeyProvider()).resolve()
    except Exception:
        authentication_key = None
        unavailable_reason = "The cache authentication provider failed closed."
    else:
        authentication_key = key_resolution.key
        unavailable_reason = key_resolution.unavailable_reason
    authentication_key_id = (
        authentication_key.key_id if authentication_key is not None else "unavailable"
    )
    authentication_provider = (
        authentication_key.provider_id if authentication_key is not None else "unavailable"
    )
    policy_digest = semantic_digest(
        {
            "cache_format": _CACHE_FORMAT,
            "schema_version": SCHEMA_VERSION,
            "tool_version": __version__,
            "components": _PARSER_COMPONENTS,
            "source_derived_scope": "project_local_only",
            "cross_repository_reuse": False,
            "writer_coordination": "nonblocking_exclusive_project_lease_v1",
            "authentication": CACHE_AUTHENTICATION_PROFILE,
            "authentication_key_id": authentication_key_id,
        }
    )
    cache_root: Path | None = None
    if authentication_key is not None:
        cache_root, cache_root_reason = _safe_cache_root(repository)
        if cache_root_reason is not None:
            unavailable_reason = cache_root_reason
    cache_lease: ProjectCacheLease | None = None
    if cache_root is not None:
        try:
            cache_lease = acquire_project_cache_lease(cache_root)
        except BlockingIOError:
            unavailable_reason = "Project-local cache is busy in another audit."
            cache_root = None
        except OSError as error:
            unavailable_reason = (
                f"Project-local cache writer lease unavailable: {type(error).__name__}"
            )
            cache_root = None
    try:
        previous_index = (
            _load_index(cache_root, project_identity, authentication_key)
            if cache_root is not None and authentication_key is not None
            else {}
        )
        current_index: dict[str, dict[str, Any]] = {}
        parser_results: list[dict[str, Any]] = []
        cache_entries: list[dict[str, Any]] = []
        hit_paths: list[str] = []
        miss_paths: list[str] = []
        uncacheable_paths: list[str] = []
        invalidated_paths: set[str] = set()
        cache_keys_by_path: dict[str, str] = {}
        snapshot_files = {str(record["path"]): record for record in snapshot.file_records}

        supported_paths: set[str] = set()
        for file_record in sorted(snapshot.file_records, key=lambda item: str(item["path"])):
            if file_record.get("entry_kind") != "regular_file":
                continue
            relative_path = str(file_record["path"])
            suffix = PurePosixPath(relative_path).suffix.lower()
            component = _PARSER_COMPONENTS.get(suffix)
            if component is None:
                continue
            materialized = snapshot.materialized_root / relative_path
            if not materialized.is_file() or materialized.is_symlink():
                continue
            supported_paths.add(relative_path)
            if suffix == ".r":
                parser_results.extend(inspect_r(materialized, run_id, source_path=relative_path))
                miss_paths.append(relative_path)
                uncacheable_paths.append(relative_path)
                continue
            input_digest = file_record.get("digest")
            if not isinstance(input_digest, str):
                result = _inspect(materialized, relative_path, run_id, suffix)
                children = inspect_embedded_cell_sources(materialized, result, run_id)
                parser_results.extend([result, *children])
                uncacheable_paths.append(relative_path)
                continue

            component_id, component_version = component
            index_key = f"{component_id}:{relative_path}"
            previous = previous_index.get(index_key)
            prior_dependency_paths = (
                [str(value) for value in previous.get("dependency_paths", [])]
                if previous is not None
                else []
            )
            dependency_identities, dependencies_exact = _dependency_identities(
                prior_dependency_paths, snapshot_files
            )
            cache_key = _parser_cache_key(
                project_identity=project_identity,
                component_id=component_id,
                component_version=component_version,
                source_path=relative_path,
                input_digest=input_digest,
                dependency_identities=dependency_identities,
                policy_digest=policy_digest,
            )

            cached = None
            if dependencies_exact and previous is not None:
                cached = _load_cached_result(
                    cache_root,
                    cache_key,
                    project_identity=project_identity,
                    source_path=relative_path,
                    input_digest=input_digest,
                    dependency_identities=dependency_identities,
                    policy_digest=policy_digest,
                    authentication_key=authentication_key,
                )
            if cached is None:
                result = _inspect(materialized, relative_path, run_id, suffix)
                children = inspect_embedded_cell_sources(materialized, result, run_id)
                dependency_paths = _parser_dependency_paths([result, *children], relative_path)
                dependency_identities, dependencies_exact = _dependency_identities(
                    dependency_paths, snapshot_files
                )
                cache_key = _parser_cache_key(
                    project_identity=project_identity,
                    component_id=component_id,
                    component_version=component_version,
                    source_path=relative_path,
                    input_digest=input_digest,
                    dependency_identities=dependency_identities,
                    policy_digest=policy_digest,
                )
                miss_paths.append(relative_path)
                cache_status = "miss"
                persisted = False
                if cache_root is not None and dependencies_exact:
                    persisted = _write_cached_result(
                        cache_root,
                        cache_key,
                        project_identity=project_identity,
                        source_path=relative_path,
                        input_digest=input_digest,
                        dependency_identities=dependency_identities,
                        policy_digest=policy_digest,
                        parser_result=result,
                        authentication_key=authentication_key,
                    )
                    if not persisted:
                        uncacheable_paths.append(relative_path)
                elif not dependencies_exact:
                    uncacheable_paths.append(relative_path)
            else:
                result = _rebind_run(cached, run_id)
                children = inspect_embedded_cell_sources(materialized, result, run_id)
                dependency_paths = prior_dependency_paths
                hit_paths.append(relative_path)
                cache_status = "hit"
                persisted = True
            if previous is not None and previous.get("cache_key") != cache_key:
                invalidated_paths.add(relative_path)
            parser_results.extend([result, *children])
            indexed = dependencies_exact and (cache_root is None or persisted)
            if indexed:
                current_index[index_key] = {
                    "cache_key": cache_key,
                    "input_digest": input_digest,
                    "source_path": relative_path,
                    "dependency_paths": dependency_paths,
                    "dependency_identities": dependency_identities,
                }
                cache_keys_by_path[relative_path] = cache_key
            if cache_root is not None and dependencies_exact and persisted:
                cache_entries.append(
                    _cache_entry(
                        cache_key=cache_key,
                        input_digest=input_digest,
                        dependency_identities=dependency_identities,
                        policy_digest=policy_digest,
                        output=result,
                        component_id=component_id,
                        component_version=component_version,
                        source_path=relative_path,
                        project_identity=project_identity,
                        cache_status=cache_status,
                        replaced=relative_path in invalidated_paths,
                        created_at=created_at,
                    )
                )

        for key, prior in previous_index.items():
            prior_path = prior.get("source_path")
            if key not in current_index and isinstance(prior_path, str):
                invalidated_paths.add(prior_path)
        if cache_root is not None:
            assert authentication_key is not None
            _write_index(cache_root, project_identity, current_index, authentication_key)

        summary = {
            "cache_format": _CACHE_FORMAT,
            "audit_run_id": run_id,
            "project_identity": project_identity,
            "policy_digest": policy_digest,
            "cache_root": _CACHE_RELATIVE_ROOT.as_posix(),
            "available": cache_root is not None,
            "unavailable_reason": unavailable_reason,
            "hits": len(hit_paths),
            "misses": len(miss_paths),
            "invalidations": len(invalidated_paths),
            "hit_paths": sorted(hit_paths),
            "miss_paths": sorted(miss_paths),
            "invalidated_paths": sorted(invalidated_paths),
            "uncacheable_paths": sorted(uncacheable_paths),
            "supported_paths": sorted(supported_paths),
        }
        return ParserCacheResult(
            parser_results=parser_results,
            cache_entries=cache_entries,
            cache_policy=_cache_policy(
                created_at,
                project_identity,
                unavailable_reason,
                authentication_key_id,
                authentication_provider,
            ),
            summary=summary,
            cache_root=cache_root,
            project_identity=project_identity,
            policy_digest=policy_digest,
            cache_keys_by_path=cache_keys_by_path,
            cache_lease=cache_lease,
            authentication_key=authentication_key,
        )
    except BaseException:
        if cache_lease is not None:
            cache_lease.close()
        raise


def acquire_project_cache_lease(cache_root: Path) -> ProjectCacheLease:
    """Acquire one fail-fast writer lease without allowing a symlink lock target."""

    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if nofollow == 0:
        raise OSError("O_NOFOLLOW is required for the project-cache writer lease")
    lock_path = cache_root / _CACHE_LEASE_FILENAME
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT | nofollow, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError("project-cache writer lease is not a regular file")
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BaseException:
        os.close(descriptor)
        raise
    return ProjectCacheLease(descriptor=descriptor, path=lock_path)


def _safe_cache_root(repository: Path) -> tuple[Path | None, str | None]:
    audit_root = repository / ".sc-referee"
    cache_parent = audit_root / "cache"
    cache_root = cache_parent / "v1"
    for path in (audit_root, cache_parent, cache_root):
        if path.is_symlink():
            return None, f"Unsafe symbolic-link cache boundary: {path.relative_to(repository)}"
        if path.exists() and not path.is_dir():
            return None, f"Cache boundary is not a directory: {path.relative_to(repository)}"
    try:
        cache_root.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        return None, f"Project-local cache unavailable: {type(error).__name__}"
    if any(path.is_symlink() for path in (audit_root, cache_parent, cache_root)):
        return None, "Project-local cache boundary changed during initialization."
    return cache_root, None


def _load_index(
    cache_root: Path,
    project_identity: str,
    authentication_key: CacheAuthenticationKey,
) -> dict[str, dict[str, Any]]:
    path = cache_root / "parser-index.json"
    value = _read_authenticated_object(path, authentication_key, cache_root)
    if (
        value is None
        or value.get("index_format") != _INDEX_FORMAT
        or value.get("project_identity") != project_identity
        or not isinstance(value.get("entries"), dict)
    ):
        return {}
    entries: dict[str, dict[str, Any]] = {}
    for key, item in value["entries"].items():
        if not isinstance(key, str) or not isinstance(item, dict):
            return {}
        if (
            not all(
                isinstance(item.get(field), str)
                for field in ("cache_key", "input_digest", "source_path")
            )
            or not isinstance(item.get("dependency_paths"), list)
            or not all(isinstance(value, str) for value in item["dependency_paths"])
            or not isinstance(item.get("dependency_identities"), dict)
            or not all(
                isinstance(path, str) and isinstance(identity, str)
                for path, identity in item["dependency_identities"].items()
            )
        ):
            return {}
        entries[key] = {
            "cache_key": item["cache_key"],
            "input_digest": item["input_digest"],
            "source_path": item["source_path"],
            "dependency_paths": list(item["dependency_paths"]),
            "dependency_identities": dict(item["dependency_identities"]),
        }
    return entries


def _write_index(
    cache_root: Path,
    project_identity: str,
    entries: dict[str, dict[str, Any]],
    authentication_key: CacheAuthenticationKey,
) -> None:
    _write_authenticated_object(
        cache_root / "parser-index.json",
        {
            "index_format": _INDEX_FORMAT,
            "project_identity": project_identity,
            "entries": {key: entries[key] for key in sorted(entries)},
        },
        authentication_key,
        cache_root,
    )


def _load_cached_result(
    cache_root: Path | None,
    cache_key: str,
    *,
    project_identity: str,
    source_path: str,
    input_digest: str,
    dependency_identities: dict[str, str],
    policy_digest: str,
    authentication_key: CacheAuthenticationKey | None,
) -> dict[str, Any] | None:
    if cache_root is None or authentication_key is None:
        return None
    value = _read_authenticated_object(
        _cache_blob_path(cache_root, cache_key), authentication_key, cache_root
    )
    if value is None:
        return None
    expected = {
        "cache_format": _CACHE_FORMAT,
        "cache_key": cache_key,
        "project_identity": project_identity,
        "source_path": source_path,
        "input_digest": input_digest,
        "dependency_identities": dependency_identities,
        "policy_digest": policy_digest,
    }
    if any(value.get(key) != item for key, item in expected.items()):
        return None
    result = value.get("parser_result")
    if not isinstance(result, dict) or value.get("result_digest") != semantic_digest(result):
        return None
    return result


def _write_cached_result(
    cache_root: Path,
    cache_key: str,
    *,
    project_identity: str,
    source_path: str,
    input_digest: str,
    dependency_identities: dict[str, str],
    policy_digest: str,
    parser_result: dict[str, Any],
    authentication_key: CacheAuthenticationKey | None,
) -> bool:
    if authentication_key is None:
        return False
    return _write_authenticated_object(
        _cache_blob_path(cache_root, cache_key),
        {
            "cache_format": _CACHE_FORMAT,
            "cache_key": cache_key,
            "project_identity": project_identity,
            "source_path": source_path,
            "input_digest": input_digest,
            "dependency_identities": dependency_identities,
            "policy_digest": policy_digest,
            "result_digest": semantic_digest(parser_result),
            "parser_result": parser_result,
        },
        authentication_key,
        cache_root,
    )


def _cache_blob_path(cache_root: Path, cache_key: str) -> Path:
    digest = cache_key.removeprefix("sha256:")
    return cache_root / "parser" / digest[:2] / f"{digest}.json"


def _load_descendant_index(
    cache_root: Path,
    project_identity: str,
    authentication_key: CacheAuthenticationKey,
) -> dict[str, dict[str, Any]]:
    value = _read_authenticated_object(
        cache_root / "descendant-index.json", authentication_key, cache_root
    )
    if (
        value is None
        or value.get("index_format") != _DESCENDANT_INDEX_FORMAT
        or value.get("project_identity") != project_identity
        or not isinstance(value.get("entries"), dict)
    ):
        return {}
    entries: dict[str, dict[str, Any]] = {}
    for key, item in value["entries"].items():
        if (
            not isinstance(key, str)
            or not isinstance(item, dict)
            or not all(
                isinstance(item.get(field), str) for field in ("cache_key", "category", "scope_key")
            )
            or not isinstance(item.get("input_digests"), list)
            or not all(isinstance(value, str) for value in item["input_digests"])
        ):
            return {}
        entries[key] = {
            "cache_key": item["cache_key"],
            "category": item["category"],
            "scope_key": item["scope_key"],
            "input_digests": list(item["input_digests"]),
        }
    return entries


def _write_descendant_index(
    cache_root: Path,
    project_identity: str,
    entries: dict[str, dict[str, Any]],
    authentication_key: CacheAuthenticationKey | None,
) -> None:
    if authentication_key is None:
        return
    _write_authenticated_object(
        cache_root / "descendant-index.json",
        {
            "index_format": _DESCENDANT_INDEX_FORMAT,
            "project_identity": project_identity,
            "entries": {key: entries[key] for key in sorted(entries)},
        },
        authentication_key,
        cache_root,
    )


def _load_descendant_payload(
    cache_root: Path | None,
    cache_key: str,
    *,
    project_identity: str,
    category: str,
    scope_key: str,
    input_digests: tuple[str, ...],
    policy_digest: str,
    authentication_key: CacheAuthenticationKey | None,
) -> dict[str, Any] | None:
    if cache_root is None or authentication_key is None:
        return None
    value = _read_authenticated_object(
        _descendant_blob_path(cache_root, category, cache_key),
        authentication_key,
        cache_root,
    )
    if value is None:
        return None
    expected: dict[str, Any] = {
        "cache_format": _DESCENDANT_CACHE_FORMAT,
        "cache_key": cache_key,
        "project_identity": project_identity,
        "category": category,
        "scope_key": scope_key,
        "input_digests": list(input_digests),
        "policy_digest": policy_digest,
    }
    if any(value.get(key) != item for key, item in expected.items()):
        return None
    payload = value.get("payload")
    if not isinstance(payload, dict) or value.get("payload_digest") != semantic_digest(payload):
        return None
    return payload


def _write_descendant_payload(
    cache_root: Path,
    cache_key: str,
    *,
    project_identity: str,
    category: str,
    scope_key: str,
    input_digests: tuple[str, ...],
    policy_digest: str,
    payload: dict[str, Any],
    authentication_key: CacheAuthenticationKey | None,
) -> bool:
    if authentication_key is None:
        return False
    return _write_authenticated_object(
        _descendant_blob_path(cache_root, category, cache_key),
        {
            "cache_format": _DESCENDANT_CACHE_FORMAT,
            "cache_key": cache_key,
            "project_identity": project_identity,
            "category": category,
            "scope_key": scope_key,
            "input_digests": list(input_digests),
            "policy_digest": policy_digest,
            "payload_digest": semantic_digest(payload),
            "payload": payload,
        },
        authentication_key,
        cache_root,
    )


def _descendant_blob_path(cache_root: Path, category: str, cache_key: str) -> Path:
    safe_category = category.replace("/", "-").replace("..", "-")
    digest = cache_key.removeprefix("sha256:")
    return cache_root / "descendant" / safe_category / digest[:2] / f"{digest}.json"


def _read_authenticated_object(
    path: Path,
    authentication_key: CacheAuthenticationKey,
    cache_root: Path,
) -> dict[str, Any] | None:
    if (
        not _safe_cache_parent(path, cache_root, create=False)
        or not path.is_file()
        or path.is_symlink()
    ):
        return None
    try:
        payload = path.read_bytes()
    except OSError:
        return None
    return verify_cache_document(payload, authentication_key)


def _write_authenticated_object(
    path: Path,
    content: dict[str, Any],
    authentication_key: CacheAuthenticationKey,
    cache_root: Path,
) -> bool:
    if not _safe_cache_parent(path, cache_root, create=True):
        return False
    try:
        write_normalized_json(path, authenticate_cache_document(content, authentication_key))
    except OSError:
        return False
    return True


def _safe_cache_parent(path: Path, cache_root: Path, *, create: bool) -> bool:
    try:
        relative = path.relative_to(cache_root)
    except ValueError:
        return False
    current = cache_root
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            return False
        if create:
            try:
                current.mkdir(exist_ok=True)
            except OSError:
                return False
            if current.is_symlink() or not current.is_dir():
                return False
        elif not current.is_dir():
            return False
    return True


def _inspect(path: Path, source_path: str, run_id: str, suffix: str) -> dict[str, Any]:
    if suffix == ".ipynb":
        return inspect_jupyter(path, run_id, source_path=source_path)
    if suffix == ".py":
        return inspect_python(path, run_id, source_path=source_path)
    if suffix == ".qmd":
        return inspect_quarto(path, run_id, source_path=source_path)
    if suffix == ".rmd":
        return inspect_rmarkdown(path, run_id, source_path=source_path)
    return inspect_markdown(path, run_id, source_path=source_path)


def _parser_dependency_paths(results: list[dict[str, Any]], source_path: str) -> list[str]:
    paths = {
        str(artifact["path"])
        for result in results
        for artifact in result.get("extensions", {}).get("x-artifacts", [])
        if isinstance(artifact, dict)
        and isinstance(artifact.get("path"), str)
        and artifact["path"] != source_path
    }
    return sorted(paths)


def _dependency_identities(
    dependency_paths: list[str], snapshot_files: dict[str, dict[str, Any]]
) -> tuple[dict[str, str], bool]:
    identities: dict[str, str] = {}
    exact = True
    for path in sorted(set(dependency_paths)):
        record = snapshot_files.get(path)
        if record is None:
            identities[path] = "absent_from_snapshot"
            continue
        digest = record.get("digest")
        if not isinstance(digest, str):
            identities[path] = f"non_exact:{record.get('file_id', 'unknown')}"
            exact = False
            continue
        identities[path] = digest
    return identities, exact


def _parser_cache_key(
    *,
    project_identity: str,
    component_id: str,
    component_version: str,
    source_path: str,
    input_digest: str,
    dependency_identities: dict[str, str],
    policy_digest: str,
) -> str:
    return semantic_digest(
        {
            "cache_format": _CACHE_FORMAT,
            "project_identity": project_identity,
            "component_id": component_id,
            "component_version": component_version,
            "tool_version": __version__,
            "schema_version": SCHEMA_VERSION,
            "source_path": source_path,
            "input_digest": input_digest,
            "dependency_identities": dependency_identities,
            "policy_digest": policy_digest,
        }
    )


def rebind_run(
    value: dict[str, Any], run_id: str, *, controller_created_at: str | None = None
) -> dict[str, Any]:
    """Rebind only explicit run-owner fields in a validated cache payload copy."""

    rebound = copy.deepcopy(value)

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            provenance = item.get("provenance")
            if controller_created_at is not None and isinstance(provenance, dict):
                actor = provenance.get("actor", {})
                if isinstance(actor, dict) and actor.get("actor_kind") in {
                    "controller",
                    "runtime",
                }:
                    provenance["created_at"] = controller_created_at
            for key, child in item.items():
                if key in {"audit_run_id", "run_id"}:
                    item[key] = run_id
                else:
                    visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(rebound)
    return rebound


def _rebind_run(value: dict[str, Any], run_id: str) -> dict[str, Any]:
    return rebind_run(value, run_id)


def _cache_entry(
    *,
    cache_key: str,
    input_digest: str,
    dependency_identities: dict[str, str],
    policy_digest: str,
    output: dict[str, Any],
    component_id: str,
    component_version: str,
    source_path: str,
    project_identity: str,
    cache_status: str,
    replaced: bool,
    created_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "cache_entry",
        "cache_entry_id": stable_id("cache-entry", project_identity, cache_key),
        "cache_scope": "project_local",
        "content_class": "source_derived",
        "input_digests": sorted(
            {
                input_digest,
                policy_digest,
                semantic_digest(dependency_identities),
                *(value for value in dependency_identities.values() if value.startswith("sha256:")),
            }
        ),
        "dependency_keys": [
            f"{component_id}@{component_version}",
            f"sc-referee@{__version__}",
            f"schema@{SCHEMA_VERSION}",
            *(f"source-dependency:{path}" for path in sorted(dependency_identities)),
        ],
        "output_refs": [
            {
                "record_type": "parser_result",
                "record_id": str(output["parser_result_id"]),
            }
        ],
        "contains_source_derived_information": True,
        "cross_repository_reuse_allowed": False,
        "created_at": created_at,
        "last_validated_at": created_at,
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-controller",
                "display_name": "sc-referee controller",
            },
            "method": "deterministic_project_local_parser_cache",
            "created_at": created_at,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": {
            "x-cache-key": cache_key,
            "x-cache-status": cache_status,
            "x-source-path": source_path,
            "x-source-dependencies": sorted(dependency_identities),
            "x-project-identity": project_identity,
            "x-replaced-prior-key": replaced,
            "x-persisted": True,
        },
    }


def _descendant_cache_entry(
    *,
    handle: DescendantCacheHandle,
    output_records: list[dict[str, Any]],
    project_identity: str,
    policy_digest: str,
    created_at: str,
) -> dict[str, Any]:
    output_refs = {_record_ref_key(record): _record_ref(record) for record in output_records}
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "cache_entry",
        "cache_entry_id": stable_id("cache-entry", project_identity, handle.cache_key),
        "cache_scope": "project_local",
        "content_class": "source_derived",
        "input_digests": sorted({*handle.input_digests, policy_digest}),
        "dependency_keys": [
            f"{handle.component_id}@{handle.component_version}",
            f"sc-referee@{__version__}",
            f"schema@{SCHEMA_VERSION}",
        ],
        "output_refs": [output_refs[key] for key in sorted(output_refs)],
        "contains_source_derived_information": True,
        "cross_repository_reuse_allowed": False,
        "created_at": created_at,
        "last_validated_at": created_at,
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-controller",
                "display_name": "sc-referee controller",
            },
            "method": "deterministic_project_local_descendant_cache",
            "created_at": created_at,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": {
            "x-cache-key": handle.cache_key,
            "x-cache-category": handle.category,
            "x-cache-scope-key": handle.scope_key,
            "x-cache-status": handle.cache_status,
            "x-project-identity": project_identity,
            "x-replaced-prior-key": handle.replaced,
            "x-persisted": True,
        },
    }


def _record_ref(record: dict[str, Any]) -> dict[str, str]:
    record_type = record.get("record_type")
    if not isinstance(record_type, str):
        raise ValueError("cached descendant output has no record type")
    identity_fields = [key for key in record if key.endswith("_id") and key != "audit_run_id"]
    if len(identity_fields) != 1 or not isinstance(record.get(identity_fields[0]), str):
        raise ValueError("cached descendant output has no unique record identity")
    return {"record_type": record_type, "record_id": str(record[identity_fields[0]])}


def _record_ref_key(record: dict[str, Any]) -> str:
    ref = _record_ref(record)
    return f"{ref['record_type']}:{ref['record_id']}"


def _cache_policy(
    created_at: str,
    project_identity: str,
    unavailable_reason: str | None,
    authentication_key_id: str,
    authentication_provider: str,
) -> dict[str, Any]:
    extensions: dict[str, Any] = {
        "x-project-identity": project_identity,
        "x-cache-format": _CACHE_FORMAT,
        "x-writer-coordination": "nonblocking_exclusive_project_lease_v1",
        "x-contended-run-behavior": "cache_unavailable_no_wait",
        "x-authentication-profile": CACHE_AUTHENTICATION_PROFILE,
        "x-authentication-key-id": authentication_key_id,
        "x-authentication-provider": authentication_provider,
    }
    if unavailable_reason is not None:
        extensions["x-unavailable-reason"] = unavailable_reason
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "cache_policy",
        "cache_policy_id": "cache-policy:project-local-v1",
        "project_store_root": ".sc-referee/",
        "source_derived_scope": "project_local_only",
        "cross_repository_source_derived_reuse": False,
        "project_local_categories": [
            "parser_results",
            "claims",
            "semantic_assertions",
            "scientific_contracts",
            "model_packets_and_outputs",
            "detector_results",
            "reports",
            "source_derived_objects",
        ],
        "global_cache_allowed_classes": [
            "parser_binaries_and_grammars",
            "public_package_downloads",
            "isolated_dependency_environments",
            "public_external_evidence",
            "tool_owned_immutable_assets",
        ],
        "global_cache_root": "${platform_user_cache}/sc-referee",
        "cache_key_requirements": {
            "content_digests": True,
            "component_versions": True,
            "policy_digest": True,
            "semantic_dependencies": True,
        },
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-controller",
                "display_name": "sc-referee controller",
            },
            "method": "deterministic_project_local_cache_policy",
            "created_at": created_at,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": extensions,
    }
