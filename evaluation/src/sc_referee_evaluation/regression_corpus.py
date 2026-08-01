from __future__ import annotations

import ast
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any, cast
from urllib.parse import urlsplit

from sc_referee.calculation_checks.profiles import default_calculation_check_registry
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.scientific_checks.profiles import default_scientific_check_registry

REGRESSION_CORPUS_LEDGER_VERSION = "1.0.0"
DEFAULT_REGRESSION_CORPUS_LEDGER = Path("evaluation/regression-corpus-v1/ledger.json")

_MAX_LEDGER_BYTES = 4_194_304
_MAX_PYTEST_SOURCE_BYTES = 4_194_304
_MAX_TREE_FILE_BYTES = 16_777_216
_MAX_TREE_BYTES = 134_217_728
_MAX_TREE_FILES = 10_000
_TOP_LEVEL_KEYS = {
    "ledger_id",
    "ledger_version",
    "record_type",
    "qualification_use_permitted",
    "component_inventory",
    "sources",
    "cases",
    "known_gaps",
    "ledger_digest",
}
_COMPONENT_KEYS = {
    "component_kind",
    "component_id",
    "component_version",
    "manifest_digest",
}
_LOCAL_SOURCE_KEYS = {
    "source_id",
    "source_kind",
    "path",
    "content_digest",
    "provenance_class",
    "answer_side",
    "benchmark_derived",
    "qualification_status",
    "exclusion_reason",
}
_TREE_SOURCE_KEYS = (_LOCAL_SOURCE_KEYS - {"content_digest"}) | {"tree_digest"}
_EXTERNAL_SOURCE_KEYS = {
    "source_id",
    "source_kind",
    "uri",
    "revision",
    "content_digest",
    "provenance_class",
    "answer_side",
    "benchmark_derived",
    "qualification_status",
    "exclusion_reason",
}
_CASE_KEYS = {
    "case_id",
    "component_refs",
    "source_ref",
    "selector",
    "case_role",
    "expected_applicability",
    "assessment_ceiling",
    "qualification_status",
    "exclusion_reason",
}
_PROVENANCE_CLASSES = {
    "synthetic_test",
    "public_development_control",
    "frozen_failed_workflow",
    "corrected_twin",
    "independent_repository",
    "benchmark_derived",
}
_CASE_ROLES = {
    "positive",
    "corrected_twin",
    "hard_negative",
    "ambiguous",
    "unsupported",
    "counterevidence",
    "removal",
    "mutation",
    "replay",
    "independent_false_positive",
    "mixed_regression",
}
_APPLICABILITY_STATES = {"applicable", "not_applicable", "ambiguous", "unsupported"}
_ASSESSMENT_CEILINGS = {"material_question", "disclosure"}
_TOKEN = re.compile(r"[a-z0-9][a-z0-9._:-]*")
_VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_REVISION = re.compile(r"[0-9a-f]{40}")
_PYTEST_SELECTOR = re.compile(r"test_[A-Za-z0-9_]+")


class RegressionCorpusLedgerError(ValueError):
    """A regression-corpus ledger escaped its closed, non-qualifying contract."""


def validate_regression_corpus_ledger(
    ledger_path: Path = DEFAULT_REGRESSION_CORPUS_LEDGER,
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Validate one immutable development ledger without executing a retained workflow."""

    root = (project_root or Path.cwd()).resolve()
    path = _resolve_ledger_path(ledger_path, root)
    payload = _bounded_read(path, "regression-corpus ledger", _MAX_LEDGER_BYTES)
    ledger = _load_canonical_object(payload)
    _require_exact_keys(ledger, _TOP_LEVEL_KEYS, "regression-corpus ledger")
    _validate_header(ledger)

    components = _validate_components(ledger.get("component_inventory"))
    expected_components = _active_component_inventory()
    if components != expected_components:
        raise RegressionCorpusLedgerError(
            "Regression-corpus component inventory has drifted from the active registries."
        )

    sources = _validate_sources(ledger.get("sources"), root)
    cases = _validate_cases(ledger.get("cases"), sources, components, root)
    referenced_sources = {str(item["source_ref"]) for item in cases}
    unused_sources = sorted(set(sources) - referenced_sources)
    if unused_sources:
        raise RegressionCorpusLedgerError(
            "Retained sources lack a regression case: " + ", ".join(unused_sources)
        )
    covered = {component for item in cases for component in item["component_refs"]}
    missing = sorted(set(components) - covered)
    if missing:
        raise RegressionCorpusLedgerError(
            "Active components lack a retained regression case: " + ", ".join(missing)
        )

    gaps = _string_array(ledger.get("known_gaps"), "known_gaps", require_nonempty=True)
    if gaps != sorted(gaps):
        raise RegressionCorpusLedgerError("Regression-corpus known gaps must be sorted.")

    digest_input = dict(ledger)
    declared_digest = digest_input.pop("ledger_digest")
    _require_digest(declared_digest, "ledger_digest")
    if declared_digest != semantic_digest(digest_input):
        raise RegressionCorpusLedgerError("Regression-corpus ledger digest mismatch.")
    return ledger


def regression_tree_digest(root: Path) -> str:
    """Hash a retained directory by safe relative paths and exact regular-file bytes."""

    if root.is_symlink() or not root.is_dir():
        raise RegressionCorpusLedgerError("Retained tree must be one non-symlink directory.")
    entries: list[dict[str, str]] = []
    total_bytes = 0
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise RegressionCorpusLedgerError(
                f"Retained tree contains a forbidden symlink: {relative}"
            )
        if path.is_dir():
            continue
        if not path.is_file():
            raise RegressionCorpusLedgerError(
                f"Retained tree contains a non-regular entry: {relative}"
            )
        if len(entries) >= _MAX_TREE_FILES:
            raise RegressionCorpusLedgerError("Retained tree exceeds its regular-file limit.")
        try:
            size = path.stat().st_size
        except OSError as error:
            raise RegressionCorpusLedgerError(
                f"Retained tree file is unavailable: {relative}"
            ) from error
        if size > _MAX_TREE_FILE_BYTES:
            raise RegressionCorpusLedgerError(
                f"Retained tree file exceeds its byte limit: {relative}"
            )
        total_bytes += size
        if total_bytes > _MAX_TREE_BYTES:
            raise RegressionCorpusLedgerError("Retained tree exceeds its aggregate byte limit.")
        entries.append(
            {
                "path": relative,
                "content_digest": sha256_digest(
                    _bounded_read(path, "retained tree file", _MAX_TREE_FILE_BYTES)
                ),
            }
        )
    if not entries:
        raise RegressionCorpusLedgerError("Retained tree must contain at least one regular file.")
    return semantic_digest(entries)


def _resolve_ledger_path(path: Path, root: Path) -> Path:
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve()
    if candidate.is_symlink() or not candidate.is_file():
        raise RegressionCorpusLedgerError(
            "Regression-corpus ledger must be one regular non-symlink file."
        )
    return resolved


def _bounded_read(path: Path, label: str, limit: int) -> bytes:
    try:
        size = path.stat().st_size
    except OSError as error:
        raise RegressionCorpusLedgerError(f"{label.capitalize()} is unavailable.") from error
    if size > limit:
        raise RegressionCorpusLedgerError(f"{label.capitalize()} exceeds its byte limit.")
    try:
        return path.read_bytes()
    except OSError as error:
        raise RegressionCorpusLedgerError(f"{label.capitalize()} is unreadable.") from error


def _load_canonical_object(payload: bytes) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, RegressionCorpusLedgerError) as error:
        raise RegressionCorpusLedgerError(
            f"Regression-corpus ledger is not strict JSON: {error}"
        ) from error
    if not isinstance(value, dict):
        raise RegressionCorpusLedgerError("Regression-corpus ledger must contain one JSON object.")
    if payload != canonical_json(value).encode("utf-8") + b"\n":
        raise RegressionCorpusLedgerError(
            "Regression-corpus ledger must be canonical JSON ending in one newline."
        )
    return cast(dict[str, Any], value)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RegressionCorpusLedgerError(f"Duplicate JSON key {key!r} is not permitted.")
        value[key] = item
    return value


def _validate_header(ledger: Mapping[str, Any]) -> None:
    _require_token(ledger.get("ledger_id"), "ledger_id")
    if ledger.get("ledger_version") != REGRESSION_CORPUS_LEDGER_VERSION:
        raise RegressionCorpusLedgerError("Unsupported regression-corpus ledger version.")
    if ledger.get("record_type") != "regression_corpus_ledger":
        raise RegressionCorpusLedgerError("Unexpected regression-corpus record type.")
    if ledger.get("qualification_use_permitted") is not False:
        raise RegressionCorpusLedgerError(
            "Development regression cases cannot be admitted as qualification evidence."
        )


def _active_component_inventory() -> dict[str, dict[str, str]]:
    scientific = default_scientific_check_registry()
    calculation = default_calculation_check_registry()
    entries = [
        {
            "component_kind": "scientific_check",
            "component_id": module.manifest.check_id,
            "component_version": module.manifest.check_version,
            "manifest_digest": module.declared_manifest_digest,
        }
        for module in scientific.canonical_modules
    ]
    entries.extend(
        {
            "component_kind": "calculation_check",
            "component_id": module.manifest.check_id,
            "component_version": module.manifest.check_version,
            "manifest_digest": module.manifest.manifest_digest,
        }
        for module in sorted(calculation.modules, key=lambda item: item.manifest.check_id)
    )
    return {str(entry["component_id"]): entry for entry in entries}


def _validate_components(value: object) -> dict[str, dict[str, str]]:
    items = _object_array(value, "component_inventory")
    normalized: dict[str, dict[str, str]] = {}
    order: list[tuple[str, str]] = []
    for item in items:
        _require_exact_keys(item, _COMPONENT_KEYS, "component inventory entry")
        kind = item.get("component_kind")
        if kind not in {"scientific_check", "calculation_check"}:
            raise RegressionCorpusLedgerError("Unknown component kind in regression corpus.")
        component_id = _require_token(item.get("component_id"), "component_id")
        version = _require_version(item.get("component_version"), "component_version")
        digest = _require_digest(item.get("manifest_digest"), "manifest_digest")
        if component_id in normalized:
            raise RegressionCorpusLedgerError(f"Duplicate component ID {component_id!r}.")
        normalized[component_id] = {
            "component_kind": str(kind),
            "component_id": component_id,
            "component_version": version,
            "manifest_digest": digest,
        }
        order.append((str(kind), component_id))
    if order != sorted(order):
        raise RegressionCorpusLedgerError("Component inventory must be sorted by kind and ID.")
    return normalized


def _validate_sources(value: object, root: Path) -> dict[str, dict[str, Any]]:
    items = _object_array(value, "sources")
    normalized: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for item in items:
        kind = item.get("source_kind")
        if kind == "pytest_module":
            _require_exact_keys(item, _LOCAL_SOURCE_KEYS, "pytest source")
        elif kind == "repository_tree":
            _require_exact_keys(item, _TREE_SOURCE_KEYS, "repository-tree source")
        elif kind == "external_revision":
            _require_exact_keys(item, _EXTERNAL_SOURCE_KEYS, "external source")
        else:
            raise RegressionCorpusLedgerError("Unknown regression-corpus source kind.")

        source_id = _require_token(item.get("source_id"), "source_id")
        if source_id in normalized:
            raise RegressionCorpusLedgerError(f"Duplicate source ID {source_id!r}.")
        provenance = item.get("provenance_class")
        if provenance not in _PROVENANCE_CLASSES:
            raise RegressionCorpusLedgerError(f"Unknown provenance class for {source_id!r}.")
        if not isinstance(item.get("answer_side"), bool) or not isinstance(
            item.get("benchmark_derived"), bool
        ):
            raise RegressionCorpusLedgerError(
                f"Source {source_id!r} requires explicit answer-side and benchmark labels."
            )
        if provenance == "benchmark_derived" and item["benchmark_derived"] is not True:
            raise RegressionCorpusLedgerError(
                f"Source {source_id!r} has inconsistent benchmark provenance labels."
            )
        _require_excluded(item, f"source {source_id!r}")

        if kind in {"pytest_module", "repository_tree"}:
            source_path = _resolve_local_source(
                _require_text(item.get("path"), "source path"), root, str(kind)
            )
            if kind == "pytest_module":
                declared = _require_digest(item.get("content_digest"), "source content_digest")
                if (
                    sha256_digest(
                        _bounded_read(source_path, "pytest source", _MAX_PYTEST_SOURCE_BYTES)
                    )
                    != declared
                ):
                    raise RegressionCorpusLedgerError(
                        f"Retained source digest mismatch for {source_id!r}."
                    )
            else:
                declared = _require_digest(item.get("tree_digest"), "source tree_digest")
                if regression_tree_digest(source_path) != declared:
                    raise RegressionCorpusLedgerError(
                        f"Retained tree digest mismatch for {source_id!r}."
                    )
        else:
            uri = _require_text(item.get("uri"), "external source URI")
            parsed_uri = urlsplit(uri)
            if (
                parsed_uri.scheme != "https"
                or parsed_uri.hostname is None
                or parsed_uri.username is not None
                or parsed_uri.password is not None
                or parsed_uri.fragment
            ):
                raise RegressionCorpusLedgerError(
                    "External source URI must be one credential-free HTTPS locator."
                )
            revision = item.get("revision")
            if not isinstance(revision, str) or not _REVISION.fullmatch(revision):
                raise RegressionCorpusLedgerError(
                    "External source revision must be one full lowercase Git commit digest."
                )
            _require_digest(item.get("content_digest"), "external content_digest")

        normalized[source_id] = dict(item)
        order.append(source_id)
    if order != sorted(order):
        raise RegressionCorpusLedgerError("Regression-corpus sources must be sorted by source ID.")
    return normalized


def _validate_cases(
    value: object,
    sources: Mapping[str, Mapping[str, Any]],
    components: Mapping[str, Mapping[str, str]],
    root: Path,
) -> list[dict[str, Any]]:
    items = _object_array(value, "cases")
    seen: set[str] = set()
    order: list[str] = []
    normalized: list[dict[str, Any]] = []
    parsed_pytest_sources: dict[str, set[str]] = {}
    for item in items:
        _require_exact_keys(item, _CASE_KEYS, "regression case")
        case_id = _require_token(item.get("case_id"), "case_id")
        if case_id in seen:
            raise RegressionCorpusLedgerError(f"Duplicate regression case ID {case_id!r}.")
        seen.add(case_id)
        order.append(case_id)

        component_refs = _string_array(
            item.get("component_refs"), "component_refs", require_nonempty=True
        )
        if component_refs != sorted(component_refs):
            raise RegressionCorpusLedgerError(f"Component references for {case_id!r} are unsorted.")
        unknown = sorted(set(component_refs) - set(components))
        if unknown:
            raise RegressionCorpusLedgerError(
                f"Regression case {case_id!r} references unknown components: {', '.join(unknown)}"
            )

        source_ref = _require_token(item.get("source_ref"), "source_ref")
        source = sources.get(source_ref)
        if source is None:
            raise RegressionCorpusLedgerError(
                f"Regression case {case_id!r} references unknown source {source_ref!r}."
            )
        selector = _require_text(item.get("selector"), "case selector")
        _validate_selector(selector, source, root, parsed_pytest_sources)

        if item.get("case_role") not in _CASE_ROLES:
            raise RegressionCorpusLedgerError(f"Unknown case role for {case_id!r}.")
        states = _string_array(
            item.get("expected_applicability"),
            "expected_applicability",
            require_nonempty=True,
        )
        if set(states) - _APPLICABILITY_STATES:
            raise RegressionCorpusLedgerError(f"Unknown applicability state for {case_id!r}.")
        ceiling = item.get("assessment_ceiling")
        if ceiling not in _ASSESSMENT_CEILINGS:
            raise RegressionCorpusLedgerError(f"Unknown assessment ceiling for {case_id!r}.")
        expected_ceilings = {
            str(components[component]["component_kind"]) for component in component_refs
        }
        required_ceiling = (
            "material_question"
            if expected_ceilings == {"scientific_check"}
            else "disclosure"
            if expected_ceilings == {"calculation_check"}
            else None
        )
        if required_ceiling is None or ceiling != required_ceiling:
            raise RegressionCorpusLedgerError(
                f"Regression case {case_id!r} exceeds or mixes component authority ceilings."
            )
        _require_excluded(item, f"case {case_id!r}")
        normalized.append({**item, "component_refs": component_refs})
    if order != sorted(order):
        raise RegressionCorpusLedgerError("Regression cases must be sorted by case ID.")
    return normalized


def _validate_selector(
    selector: str,
    source: Mapping[str, Any],
    root: Path,
    parsed_pytest_sources: dict[str, set[str]],
) -> None:
    source_kind = source["source_kind"]
    source_id = str(source["source_id"])
    if source_kind == "pytest_module":
        if not _PYTEST_SELECTOR.fullmatch(selector):
            raise RegressionCorpusLedgerError(f"Invalid pytest selector {selector!r}.")
        functions = parsed_pytest_sources.get(source_id)
        if functions is None:
            path = _resolve_local_source(str(source["path"]), root, "pytest_module")
            try:
                syntax_tree = ast.parse(
                    _bounded_read(path, "pytest source", _MAX_PYTEST_SOURCE_BYTES),
                    filename=str(path),
                )
            except (OSError, SyntaxError, ValueError) as error:
                raise RegressionCorpusLedgerError(
                    f"Retained pytest source {source_id!r} cannot be parsed statically."
                ) from error
            functions = {
                node.name
                for node in syntax_tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            parsed_pytest_sources[source_id] = functions
        if selector not in functions:
            raise RegressionCorpusLedgerError(
                f"Retained pytest selector {selector!r} does not exist in {source_id!r}."
            )
    elif source_kind == "repository_tree":
        retained_tree = _resolve_local_source(str(source["path"]), root, "repository_tree")
        selected = _resolve_relative_selector(selector, retained_tree)
        if not selected.exists() or selected.is_symlink():
            raise RegressionCorpusLedgerError(
                f"Retained tree selector {selector!r} is unavailable or unsafe."
            )
    elif not selector.strip():
        raise RegressionCorpusLedgerError("External source selector must not be empty.")


def _resolve_local_source(path_value: str, root: Path, kind: str) -> Path:
    relative = _safe_relative(path_value, "source path")
    candidate = root.joinpath(*relative.parts)
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise RegressionCorpusLedgerError("Retained source escapes the project root.")
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise RegressionCorpusLedgerError("Retained source paths cannot contain symlinks.")
    if kind == "pytest_module":
        if not resolved.is_file() or resolved.suffix != ".py":
            raise RegressionCorpusLedgerError("Pytest source must be one regular Python file.")
    elif not resolved.is_dir():
        raise RegressionCorpusLedgerError("Repository-tree source must be one directory.")
    return resolved


def _resolve_relative_selector(selector: str, root: Path) -> Path:
    relative = _safe_relative(selector, "tree selector")
    candidate = root.joinpath(*relative.parts)
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise RegressionCorpusLedgerError("Tree selector escapes its retained source.")
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise RegressionCorpusLedgerError("Tree selectors cannot traverse symlinks.")
    return resolved


def _safe_relative(value: str, label: str) -> PurePosixPath:
    if "\\" in value:
        raise RegressionCorpusLedgerError(f"{label.capitalize()} must use POSIX separators.")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise RegressionCorpusLedgerError(f"{label.capitalize()} must be bounded and relative.")
    return path


def _require_excluded(item: Mapping[str, Any], label: str) -> None:
    if item.get("qualification_status") != "excluded":
        raise RegressionCorpusLedgerError(
            f"Development {label} cannot count toward detector qualification."
        )
    _require_text(item.get("exclusion_reason"), "qualification exclusion reason")


def _object_array(value: object, label: str) -> list[dict[str, Any]]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not value
        or not all(isinstance(item, dict) for item in value)
    ):
        raise RegressionCorpusLedgerError(f"{label} must be a nonempty array of objects.")
    return [cast(dict[str, Any], item) for item in value]


def _string_array(value: object, label: str, *, require_nonempty: bool) -> list[str]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or (require_nonempty and not value)
        or not all(isinstance(item, str) and item.strip() == item and item for item in value)
    ):
        raise RegressionCorpusLedgerError(f"{label} must be an array of nonempty strings.")
    normalized = [str(item) for item in value]
    if len(normalized) != len(set(normalized)):
        raise RegressionCorpusLedgerError(f"{label} entries must be unique.")
    return normalized


def _require_exact_keys(value: Mapping[str, Any], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise RegressionCorpusLedgerError(f"{label.capitalize()} has unexpected fields.")


def _require_token(value: object, label: str) -> str:
    if not isinstance(value, str) or not _TOKEN.fullmatch(value):
        raise RegressionCorpusLedgerError(f"{label} must be one lowercase identifier token.")
    return value


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise RegressionCorpusLedgerError(f"{label} must be nonempty normalized text.")
    return value


def _require_version(value: object, label: str) -> str:
    if not isinstance(value, str) or not _VERSION.fullmatch(value):
        raise RegressionCorpusLedgerError(f"{label} must be a three-part numeric version.")
    return value


def _require_digest(value: object, label: str) -> str:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise RegressionCorpusLedgerError(f"{label} must be one lowercase sha256 digest.")
    return value
