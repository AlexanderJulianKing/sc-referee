"""Descriptor-anchored authentication for the Slice-C development runtime.

This module is deliberately private to the development audit ladder.  It neither
imports nor executes the pinned interpreter.  The sole mutating operation is the
one reviewed transition from the authenticated pre-restoration directory modes to
the immutable manifest modes.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
import stat
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Final, Literal, NoReturn, cast

_RUNTIME_PARENT: Final = Path("/Users/alexanderking/sc-referee-runtimes")
_SANDBOX_NAME: Final = "h5ad-tier1-scanpy1115-final-sandbox"
_ARTIFACTS_NAME: Final = "h5ad-tier1-scanpy1115-artifacts"
_MODE_PROBE_NAME: Final = "slice-c-mode-probe-20260820-b65306bc0c8f4a539d9e74866f1ae84b"
_MODE_PROBE_IDENTITY: Final = (
    16_777_233,
    394_647_425,
    501,
    20,
    0o555,
    1_787_214_595_709_650_000 + 1_075,
    1_787_214_595_709_710_000 + 158,
)
_RESOURCE_ROOT: Final = (
    Path(__file__).resolve().parents[5]
    / "evaluation"
    / "development"
    / "audit-report-ladder"
    / "world1"
    / "resources"
)

_ARTIFACT_PATHS: Final[dict[str, tuple[str, int, str]]] = {
    "premise": (
        "h5ad-tier1-scanpy1115-premise.json",
        3_443,
        "0f3db3490b640ed80a12c94038c3d78f18d5aa431cab42e8ec73ee2b54b21d04",
    ),
    "runtime_manifest": (
        "h5ad-tier1-scanpy1115-runtime-manifest.jsonl",
        3_394_894,
        "dcb663037d60a94cf48a34f335a857f2fa8a710a1fc712611891a884dfcab6e1",
    ),
    "cpython_manifest": (
        "h5ad-tier1-scanpy1115-cpython-manifest.jsonl",
        807_212,
        "4cccef84e310d2c40935e77b92343833bf5050c42feb325afde5385242e2c388",
    ),
    "wheel_manifest": (
        "h5ad-tier1-scanpy1115-wheel-manifest.jsonl",
        6_612,
        "5fd6106fdd73c3e11ac3030d078640c6b7e9fa85b926ac6f74d04c0c7e9b5d1e",
    ),
    "record_reconciliation": (
        "h5ad-tier1-scanpy1115-record-reconciliation.json",
        7_745,
        "ad8671d57e252a7d0eeb28b6b3c8d964ce5615a8e3fad890c83cbe1084b66b97",
    ),
    "semantic_measurement": (
        "h5ad-tier1-scanpy1115-measurement.json",
        12_975,
        "ccd2f42d1542e075b18f020e93f84533159cfff536ba760013c76d781e3f9a91",
    ),
    "root_seal": (
        "audit-report-ladder-slice-c-runtime-root-seal-v1.json",
        960,
        "07dd8873f3b5ce4b94ca4b536bb2cbaeafc7f9be42dad2f16b1be495d4fba4e6",
    ),
}

_REQUIREMENTS: Final[dict[str, tuple[str, str]]] = {
    "input": (
        "h5ad-tier1-scanpy1115-input-requirements.txt",
        "3af777d44112f2e8fe4a6488b7cfc29a99af1115de1da1311bd85720d35e58a1",
    ),
    "resolved": (
        "h5ad-tier1-scanpy1115-resolved-requirements.txt",
        "0858441c3c36cd6460a9c68f982012a9e73c8e645c15513373325a2eede9aace",
    ),
}

_ROOT_IDENTITIES: Final[dict[str, tuple[int, int, int, int]]] = {
    "parent": (16_777_233, 394_647_424, 501, 20),
    "sandbox": (16_777_233, 394_647_433, 501, 20),
    "python": (16_777_233, 394_647_434, 501, 20),
    "venv": (16_777_233, 394_650_585, 501, 20),
}
_PRE_ROOT_MODES: Final = {"parent": 0o755, "sandbox": 0o755, "python": 0o700, "venv": 0o700}
_SEALED_ROOT_MODES: Final = {
    "parent": 0o755,
    "sandbox": 0o555,
    "python": 0o555,
    "venv": 0o555,
}
_EXPECTED_OWNER: Final = (501, 20)
_EXPECTED_INTERPRETER_SHA: Final = (
    "68100c5188b837802c7ae52398389d121b1c063ed244dec11649775b539c3a30"
)
_EXPECTED_NATIVE: Final[dict[bytes, str]] = {
    b"lib/python3.11/site-packages/h5py/.dylibs/libhdf5.320.0.0.dylib": (
        "4195ec2a6e1a86bbb6c7c77b566c7fc7ae2c38ed5b6d5e67ccf55f657ad2934b"
    ),
    b"lib/python3.11/site-packages/h5py/.dylibs/libhdf5_hl.320.0.0.dylib": (
        "27a11fd1f8fdae2aaaca90fd331db52914f2bb9d3cafed6a7412de1277d46322"
    ),
    b"lib/python3.11/site-packages/h5py/.dylibs/libz.1.3.2.dylib": (
        "27780608222fb41d66d9c866fa3706f5d12d7e6002175a3bd4901ae6433c009c"
    ),
}

_OPEN_FLAGS: Final = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
_DIRECTORY_FLAGS: Final = _OPEN_FLAGS | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
_FILE_FLAGS: Final = _OPEN_FLAGS | getattr(os, "O_NOFOLLOW", 0)

RuntimeState = Literal["pre-restoration", "sealed"]


class RuntimeAuthenticationError(RuntimeError):
    """The external runtime failed the exact closed authentication contract."""


@dataclass(frozen=True, slots=True)
class RuntimeIdentityEvidence:
    """Bounded summary of a complete successful verification."""

    state: RuntimeState
    runtime_entries: int
    runtime_directories: int
    runtime_regular_files: int
    runtime_symlinks: int
    cpython_entries: int
    cpython_directories: int
    cpython_regular_files: int
    cpython_symlinks: int
    wheel_files: int
    record_files: int
    record_rows: int
    hashed_record_rows: int
    unhashed_record_rows: int
    owner_pairs: tuple[tuple[int, int], ...]
    pyc_files: int
    pth_files: int
    artifact_sha256: tuple[tuple[str, str], ...]


@dataclass(slots=True)
class _RootDescriptors:
    parent: int
    sandbox: int
    python: int
    venv: int

    def close(self) -> None:
        for fd in (self.venv, self.python, self.sandbox, self.parent):
            try:
                os.close(fd)
            except OSError:
                pass


@dataclass(slots=True)
class _TreeVerification:
    entries: int
    directories: int
    regular_files: int
    symlinks: int
    owners: set[tuple[int, int]]
    regular_rows: dict[bytes, tuple[int, str]]
    directory_fds: dict[bytes, int]
    directory_mode_mismatches: int
    pyc_files: int
    pth_files: int

    def close(self) -> None:
        for fd in self.directory_fds.values():
            try:
                os.close(fd)
            except OSError:
                pass
        self.directory_fds.clear()


def _fail(message: str) -> NoReturn:
    raise RuntimeAuthenticationError(message)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON member")
        result[key] = value
    return result


def _parse_canonical_json(raw: bytes, *, jsonl: bool) -> Any:
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r" in raw:
        _fail("artifact is not canonical LF JSON")
    if jsonl:
        values: list[Any] = []
        for line in raw[:-1].split(b"\n"):
            if not line:
                _fail("manifest has an empty JSONL row")
            try:
                value = json.loads(line, object_pairs_hook=_strict_object)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
                raise RuntimeAuthenticationError("manifest JSONL parsing failed") from error
            if _canonical(value) != line:
                _fail("manifest JSONL row is noncanonical")
            values.append(value)
        return values
    try:
        value = json.loads(raw[:-1], object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeAuthenticationError("artifact JSON parsing failed") from error
    if _canonical(value) != raw[:-1]:
        _fail("artifact JSON is noncanonical")
    return value


def _read_exact_file(path: Path, size: int, digest: str) -> bytes:
    before = os.stat(path, follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode):
        _fail("fixed artifact is not one regular file")
    fd = os.open(path, _FILE_FLAGS)
    try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            _fail("fixed artifact changed during descriptor acquisition")
        chunks: list[bytes] = []
        while True:
            block = os.read(fd, 1_048_576)
            if not block:
                break
            chunks.append(block)
        after = os.fstat(fd)
        if (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ) != (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
            opened.st_ctime_ns,
        ):
            _fail("fixed artifact changed during authentication")
    finally:
        os.close(fd)
    raw = b"".join(chunks)
    if len(raw) != size or _sha256(raw) != digest:
        _fail("fixed artifact identity differs")
    return raw


def read_runtime_artifacts_v1() -> dict[str, bytes]:
    """Read and authenticate the seven fixed worker artifacts exactly once."""

    result: dict[str, bytes] = {}
    for name, (filename, size, digest) in _ARTIFACT_PATHS.items():
        path = _RESOURCE_ROOT / filename if name == "root_seal" else _RUNTIME_PARENT / filename
        raw = _read_exact_file(path, size, digest)
        _parse_canonical_json(
            raw,
            jsonl=name in {"runtime_manifest", "cpython_manifest", "wheel_manifest"},
        )
        result[name] = raw
    for filename, digest in _REQUIREMENTS.values():
        path = _RUNTIME_PARENT / filename
        size = os.stat(path, follow_symlinks=False).st_size
        raw = _read_exact_file(path, size, digest)
        if _sha256(raw) != digest:
            _fail("requirements identity differs")
    return result


def validate_prelaunch_provenance_v1(
    *,
    runtime_artifacts: dict[str, bytes],
    protocol: dict[str, Any],
    root_seal_bytes: bytes,
    root_seal: dict[str, Any],
    renderer: dict[str, Any],
    observation_premise: tuple[str, str],
    renderer_premise: tuple[str, str],
) -> None:
    """Close every premise carrier before a worker can be launched."""

    if set(runtime_artifacts) != set(_ARTIFACT_PATHS):
        _fail("pre-launch runtime artifact set differs")
    wrappers = protocol.get("artifacts")
    if type(wrappers) is not dict or set(wrappers) != set(runtime_artifacts):
        _fail("pre-launch protocol artifact registry differs")
    for name, raw in runtime_artifacts.items():
        if wrappers.get(name) != {"byte_size": len(raw), "sha256": f"sha256:{_sha256(raw)}"}:
            _fail("pre-launch protocol artifact identity differs")

    premise_raw = runtime_artifacts["premise"]
    premise_value = _parse_canonical_json(premise_raw, jsonl=False)
    if type(premise_value) is not dict:
        _fail("runtime premise is not one object")
    premise = cast(dict[str, Any], premise_value)
    premise_digest = premise.get("premise_digest")
    unsigned = dict(premise)
    unsigned.pop("premise_digest", None)
    expected_premise = (
        "scanpy-1.11.5-cpython-3.11.15-macos-arm64-v1",
        "sha256:09fe04ea03c03221bf20c00b5e45cd8f66f00d7476f98da64df5dcde79dc7eeb",
    )
    if (
        premise.get("schema") != "scanpy-1.11.5-development-runtime-premise-v1"
        or premise.get("premise_id") != expected_premise[0]
        or premise_digest != expected_premise[1]
        or premise_digest != f"sha256:{_sha256(_canonical(unsigned))}"
    ):
        _fail("runtime premise self-identity differs")

    old_prefix = b"/Users/alexanderking/Desktop/" + b"random_stuff/sc-referee-pilot-runtime"
    new_prefix = b"/Users/alexanderking/sc-referee-runtimes"
    expected_paths = {
        ("launch", "manual_site_packages"): (
            f"{_RUNTIME_PARENT}/{_SANDBOX_NAME}/venv/lib/python3.11/site-packages"
        ),
        ("manifests", "cpython", "path"): (
            f"{_RUNTIME_PARENT}/h5ad-tier1-scanpy1115-cpython-manifest.jsonl"
        ),
        ("manifests", "record_reconciliation", "path"): (
            f"{_RUNTIME_PARENT}/h5ad-tier1-scanpy1115-record-reconciliation.json"
        ),
        ("manifests", "runtime", "path"): (
            f"{_RUNTIME_PARENT}/h5ad-tier1-scanpy1115-runtime-manifest.jsonl"
        ),
        ("manifests", "wheels", "path"): (
            f"{_RUNTIME_PARENT}/h5ad-tier1-scanpy1115-wheel-manifest.jsonl"
        ),
        ("measurement", "path"): f"{_RUNTIME_PARENT}/h5ad-tier1-scanpy1115-measurement.json",
        ("python", "base_prefix"): f"{_RUNTIME_PARENT}/{_SANDBOX_NAME}/python",
    }
    for path, expected in expected_paths.items():
        value: Any = premise
        for member in path:
            if type(value) is not dict or member not in value:
                _fail("runtime premise relocated path is absent")
            value = value[member]
        if value != expected:
            _fail("runtime premise relocated path differs")
    if old_prefix in premise_raw or premise_raw.count(new_prefix) != 7:
        _fail("runtime premise prefix cardinality differs")

    if runtime_artifacts["root_seal"] != root_seal_bytes:
        _fail("live and copied root-seal bytes differ")
    parsed_seal = _parse_canonical_json(root_seal_bytes, jsonl=False)
    expected_entries = [
        {
            "gid": identity[3],
            "initial_mode": initial,
            "label": label,
            "path": str(path),
            "sealed_mode": sealed,
            "st_dev": identity[0],
            "st_ino": identity[1],
            "uid": identity[2],
        }
        for label, path, initial, sealed, identity in (
            ("sandbox-parent", _RUNTIME_PARENT, "0755", "0755", _ROOT_IDENTITIES["parent"]),
            (
                "sandbox-root",
                _RUNTIME_PARENT / _SANDBOX_NAME,
                "0755",
                "0555",
                _ROOT_IDENTITIES["sandbox"],
            ),
            (
                "cpython-root",
                _RUNTIME_PARENT / _SANDBOX_NAME / "python",
                "0700",
                "0555",
                _ROOT_IDENTITIES["python"],
            ),
            (
                "venv-root",
                _RUNTIME_PARENT / _SANDBOX_NAME / "venv",
                "0700",
                "0555",
                _ROOT_IDENTITIES["venv"],
            ),
        )
    ]
    expected_seal = {
        "entries": expected_entries,
        "premise_digest": expected_premise[1],
        "schema": "slice-c-runtime-root-seal-v1",
    }
    if parsed_seal != expected_seal or root_seal != expected_seal:
        _fail("root seal and runtime premise disagree")
    if observation_premise != expected_premise or renderer_premise != expected_premise:
        _fail("observation or renderer premise provenance differs")
    disclosures = renderer.get("disclosures")
    expected_disclosure = (
        "The four H5AD observations depend on immutable development premise "
        f"{expected_premise[0]} with premise digest {expected_premise[1]}."
    )
    if (
        type(disclosures) is not list
        or len(disclosures) != 4
        or disclosures[2] != expected_disclosure
    ):
        _fail("renderer premise disclosure differs")


def _verify_retained_mode_probe(parent_fd: int) -> None:
    before = os.stat(_MODE_PROBE_NAME, dir_fd=parent_fd, follow_symlinks=False)
    fd = os.open(_MODE_PROBE_NAME, _DIRECTORY_FLAGS, dir_fd=parent_fd)
    try:
        opened = os.fstat(fd)
        actual = (
            opened.st_dev,
            opened.st_ino,
            opened.st_uid,
            opened.st_gid,
            stat.S_IMODE(opened.st_mode),
            opened.st_mtime_ns,
            opened.st_ctime_ns,
        )
        visible = (
            before.st_dev,
            before.st_ino,
            before.st_uid,
            before.st_gid,
            stat.S_IMODE(before.st_mode),
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        if (
            not stat.S_ISDIR(before.st_mode)
            or not stat.S_ISDIR(opened.st_mode)
            or actual != _MODE_PROBE_IDENTITY
            or visible != actual
        ):
            _fail("retained outside-iCloud mode probe identity differs")
    finally:
        os.close(fd)


def _open_roots(expected_modes: dict[str, int]) -> _RootDescriptors:
    parent = os.open(_RUNTIME_PARENT, _DIRECTORY_FLAGS)
    descriptors: list[int] = [parent]
    try:
        _verify_retained_mode_probe(parent)
        sandbox = os.open(_SANDBOX_NAME, _DIRECTORY_FLAGS, dir_fd=parent)
        descriptors.append(sandbox)
        python = os.open("python", _DIRECTORY_FLAGS, dir_fd=sandbox)
        descriptors.append(python)
        venv = os.open("venv", _DIRECTORY_FLAGS, dir_fd=sandbox)
        descriptors.append(venv)
        roots = _RootDescriptors(parent, sandbox, python, venv)
        for label, fd in (
            ("parent", parent),
            ("sandbox", sandbox),
            ("python", python),
            ("venv", venv),
        ):
            info = os.fstat(fd)
            identity = (info.st_dev, info.st_ino, info.st_uid, info.st_gid)
            if identity != _ROOT_IDENTITIES[label]:
                _fail("root descriptor identity differs")
            if stat.S_IMODE(info.st_mode) != expected_modes[label]:
                _fail("root descriptor mode differs")
            if not stat.S_ISDIR(info.st_mode):
                _fail("root descriptor is not a directory")
        return roots
    except BaseException:
        for fd in reversed(descriptors):
            try:
                os.close(fd)
            except OSError:
                pass
        raise


def _decode_manifest_path(value: Any) -> bytes:
    if type(value) is not str:
        _fail("manifest path is not a string")
    try:
        raw = base64.b64decode(value, validate=True)
    except ValueError as error:
        raise RuntimeAuthenticationError("manifest path base64 is invalid") from error
    if base64.b64encode(raw).decode("ascii") != value:
        _fail("manifest path base64 is noncanonical")
    parts = raw.split(b"/")
    if not raw or any(part in {b"", b".", b".."} or b"\0" in part for part in parts):
        _fail("manifest path escapes its root")
    return raw


def _open_child(parent_fd: int, name: bytes, *, directory: bool) -> int:
    flags = _DIRECTORY_FLAGS if directory else _FILE_FLAGS
    return os.open(name, flags, dir_fd=parent_fd)


def _hash_open_file(parent_fd: int, name: bytes, expected_stat: os.stat_result) -> tuple[int, str]:
    fd = _open_child(parent_fd, name, directory=False)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or (before.st_dev, before.st_ino) != (
            expected_stat.st_dev,
            expected_stat.st_ino,
        ):
            _fail("regular-file descriptor identity differs")
        digest = hashlib.sha256()
        size = 0
        while True:
            block = os.read(fd, 1_048_576)
            if not block:
                break
            digest.update(block)
            size += len(block)
        after = os.fstat(fd)
        if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) != (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ):
            _fail("regular file changed while authenticating")
        return size, digest.hexdigest()
    finally:
        os.close(fd)


def _manifest_rows(raw: bytes, root_id: str) -> dict[bytes, dict[str, Any]]:
    parsed = _parse_canonical_json(raw, jsonl=True)
    if type(parsed) is not list:
        _fail("manifest is not a row list")
    rows: dict[bytes, dict[str, Any]] = {}
    previous: bytes | None = None
    for value in parsed:
        if type(value) is not dict or value.get("root_id") != root_id:
            _fail("manifest row root or type differs")
        path = _decode_manifest_path(value.get("path_b64"))
        if path in rows or (previous is not None and path <= previous):
            _fail("manifest paths are duplicate or reordered")
        rows[path] = cast(dict[str, Any], value)
        previous = path
    return rows


def _verify_tree(
    root_fd: int,
    manifest_raw: bytes,
    *,
    root_id: str,
    state: RuntimeState,
    retain_directory_fds: bool,
) -> _TreeVerification:
    manifest = _manifest_rows(manifest_raw, root_id)
    directory_fds: dict[bytes, int] = {}
    actual_paths: set[bytes] = set()
    regular_rows: dict[bytes, tuple[int, str]] = {}
    owners: set[tuple[int, int]] = set()
    directory_mismatches = 0
    counts: Counter[str] = Counter()
    pyc_files = 0
    pth_files = 0

    def walk(parent_fd: int, prefix: bytes) -> None:
        nonlocal directory_mismatches, pyc_files, pth_files
        try:
            names = sorted(os.fsencode(name) for name in os.listdir(parent_fd))
        except OSError as error:
            raise RuntimeAuthenticationError("descriptor-relative enumeration failed") from error
        for name in names:
            if name in {b".", b".."} or b"/" in name or b"\0" in name:
                _fail("invalid directory entry name")
            path = name if not prefix else prefix + b"/" + name
            actual_paths.add(path)
            row = manifest.get(path)
            if row is None:
                _fail("runtime tree has an extra path")
            info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            owners.add((info.st_uid, info.st_gid))
            mode = stat.S_IMODE(info.st_mode)
            entry_kind = row.get("entry_kind")
            expected_mode = row.get("mode")
            if type(expected_mode) is not str or len(expected_mode) != 4:
                _fail("manifest mode is invalid")
            try:
                manifest_mode = int(expected_mode, 8)
            except ValueError as error:
                raise RuntimeAuthenticationError("manifest mode is invalid") from error
            expected_keys: set[str]
            if stat.S_ISDIR(info.st_mode):
                counts["directory"] += 1
                expected_keys = {"entry_kind", "mode", "path_b64", "root_id"}
                if entry_kind != "directory":
                    _fail("runtime entry kind differs")
                if mode != manifest_mode:
                    if state != "pre-restoration" or mode != 0o700 or manifest_mode != 0o555:
                        _fail("directory mode differs outside the authorized transition")
                    directory_mismatches += 1
                child_fd = _open_child(parent_fd, name, directory=True)
                child_info = os.fstat(child_fd)
                if (child_info.st_dev, child_info.st_ino) != (info.st_dev, info.st_ino):
                    os.close(child_fd)
                    _fail("directory descriptor identity differs")
                if retain_directory_fds:
                    directory_fds[path] = child_fd
                try:
                    walk(child_fd, path)
                finally:
                    if not retain_directory_fds:
                        os.close(child_fd)
            elif stat.S_ISREG(info.st_mode):
                counts["regular-file"] += 1
                expected_keys = {
                    "byte_size",
                    "entry_kind",
                    "mode",
                    "path_b64",
                    "root_id",
                    "sha256",
                }
                if entry_kind != "regular-file" or mode != manifest_mode:
                    _fail("regular-file kind or mode differs")
                size, digest = _hash_open_file(parent_fd, name, info)
                if (
                    type(row.get("byte_size")) is not int
                    or row["byte_size"] != size
                    or row.get("sha256") != f"sha256:{digest}"
                ):
                    _fail("regular-file size or digest differs")
                regular_rows[path] = (size, digest)
                pyc_files += int(path.endswith(b".pyc"))
                pth_files += int(path.endswith(b".pth"))
            elif stat.S_ISLNK(info.st_mode):
                counts["symlink"] += 1
                expected_keys = {"entry_kind", "mode", "path_b64", "root_id", "target_b64"}
                if entry_kind != "symlink" or mode != manifest_mode:
                    _fail("symlink kind or mode differs")
                target = os.readlink(name, dir_fd=parent_fd)
                target_raw = os.fsencode(target)
                target_b64 = base64.b64encode(target_raw).decode("ascii")
                if row.get("target_b64") != target_b64:
                    _fail("symlink target differs")
            else:
                _fail("runtime tree contains a special entry")
            if set(row) != expected_keys:
                _fail("manifest row member set differs")

    try:
        walk(root_fd, b"")
        if actual_paths != set(manifest):
            _fail("manifest and runtime tree are not bijective")
        if owners != {_EXPECTED_OWNER}:
            _fail("runtime ownership set differs")
        return _TreeVerification(
            entries=len(actual_paths),
            directories=counts["directory"],
            regular_files=counts["regular-file"],
            symlinks=counts["symlink"],
            owners=owners,
            regular_rows=regular_rows,
            directory_fds=directory_fds,
            directory_mode_mismatches=directory_mismatches,
            pyc_files=pyc_files,
            pth_files=pth_files,
        )
    except BaseException:
        for fd in directory_fds.values():
            try:
                os.close(fd)
            except OSError:
                pass
        raise


def _verify_wheels(parent_fd: int, wheel_raw: bytes) -> int:
    rows = _parse_canonical_json(wheel_raw, jsonl=True)
    if type(rows) is not list or len(rows) != 42:
        _fail("wheel manifest row count differs")
    artifacts_fd = os.open(_ARTIFACTS_NAME, _DIRECTORY_FLAGS, dir_fd=parent_fd)
    try:
        names = sorted(os.listdir(artifacts_fd))
        expected_names: list[str] = []
        previous: str | None = None
        for row in rows:
            if type(row) is not dict or set(row) != {"byte_size", "filename", "sha256"}:
                _fail("wheel manifest row shape differs")
            filename = row.get("filename")
            if (
                type(filename) is not str
                or not filename
                or "/" in filename
                or filename in {".", ".."}
                or (previous is not None and filename <= previous)
            ):
                _fail("wheel filename or ordering differs")
            previous = filename
            expected_names.append(filename)
            info = os.stat(filename, dir_fd=artifacts_fd, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or (info.st_uid, info.st_gid) != _EXPECTED_OWNER:
                _fail("wheel artifact kind or owner differs")
            size, digest = _hash_open_file(artifacts_fd, os.fsencode(filename), info)
            if row.get("byte_size") != size or row.get("sha256") != f"sha256:{digest}":
                _fail("wheel artifact identity differs")
        if names != expected_names:
            _fail("wheel artifact set is not bijective")
        return len(rows)
    finally:
        os.close(artifacts_fd)


def _normalise_record_target(record_path: bytes) -> bytes:
    base = PurePosixPath("lib/python3.11/site-packages")
    candidate = base / os.fsdecode(record_path)
    parts: list[str] = []
    for part in candidate.parts:
        if part in {"", ".", "/"}:
            continue
        if part == "..":
            if not parts:
                _fail("RECORD path traverses the runtime root")
            parts.pop()
        else:
            parts.append(part)
    if not parts:
        _fail("RECORD target is empty")
    return "/".join(parts).encode("utf-8", "strict")


def _decode_record_digest(value: str) -> str:
    if not value.startswith("sha256="):
        _fail("RECORD uses a non-SHA256 digest")
    encoded = value.removeprefix("sha256=")
    try:
        decoded = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    except ValueError as error:
        raise RuntimeAuthenticationError("RECORD digest base64 is invalid") from error
    if len(decoded) != 32:
        _fail("RECORD digest length differs")
    canonical = base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii")
    if canonical != encoded:
        _fail("RECORD digest base64 is noncanonical")
    return decoded.hex()


def _verify_records(
    venv_fd: int,
    regular_rows: dict[bytes, tuple[int, str]],
    reconciliation_raw: bytes,
) -> tuple[int, int, int, int]:
    value = _parse_canonical_json(reconciliation_raw, jsonl=False)
    if type(value) is not dict or value.get("schema") != "scanpy-1.11.5-record-reconciliation-v1":
        _fail("RECORD reconciliation schema differs")
    expected_keys = {
        "digest_mismatches",
        "duplicate_owners",
        "hashed_regular_bytes",
        "hashed_rows",
        "missing_record_targets",
        "record_file_count",
        "record_files",
        "record_rows",
        "schema",
        "unhashed_rows",
        "unrecorded_runtime_scaffold_paths_b64",
        "unrecorded_site_files",
    }
    if set(value) != expected_keys:
        _fail("RECORD reconciliation member set differs")
    record_files = value.get("record_files")
    if type(record_files) is not list or len(record_files) != 42:
        _fail("RECORD file list differs")

    owners: dict[bytes, bytes] = {}
    record_file_targets: set[bytes] = set()
    record_rows = 0
    hashed_rows = 0
    unhashed_rows = 0
    hashed_bytes = 0
    for record in record_files:
        if type(record) is not dict or set(record) != {"byte_size", "path", "sha256"}:
            _fail("RECORD file descriptor differs")
        path_value = record.get("path")
        if type(path_value) is not str:
            _fail("RECORD file path type differs")
        path = path_value.encode("utf-8", "strict")
        if path not in regular_rows:
            _fail("RECORD file is absent from runtime manifest")
        size, digest = regular_rows[path]
        if record.get("byte_size") != size or record.get("sha256") != f"sha256:{digest}":
            _fail("RECORD file identity differs")
        record_file_targets.add(path)
        parent_path, filename = path.rsplit(b"/", 1)
        parent_fd = _open_directory_path(venv_fd, parent_path)
        try:
            info = os.stat(filename, dir_fd=parent_fd, follow_symlinks=False)
            file_size, file_digest = _hash_open_file(parent_fd, filename, info)
            if (file_size, file_digest) != (size, digest):
                _fail("RECORD file changed during reconciliation")
            file_fd = _open_child(parent_fd, filename, directory=False)
            try:
                chunks: list[bytes] = []
                while True:
                    block = os.read(file_fd, 65_536)
                    if not block:
                        break
                    chunks.append(block)
                raw = b"".join(chunks)
            finally:
                os.close(file_fd)
        finally:
            os.close(parent_fd)
        try:
            text = raw.decode("utf-8", "strict")
            rows = list(csv.reader(io.StringIO(text, newline=""), strict=True))
        except (UnicodeDecodeError, csv.Error) as error:
            raise RuntimeAuthenticationError("RECORD parsing failed") from error
        for row in rows:
            record_rows += 1
            if len(row) != 3 or not row[0]:
                _fail("RECORD row shape differs")
            try:
                target_raw = row[0].encode("utf-8", "strict")
            except UnicodeEncodeError as error:
                raise RuntimeAuthenticationError("RECORD target is not UTF-8") from error
            target = _normalise_record_target(target_raw)
            if row[1] == "" and row[2] == "":
                unhashed_rows += 1
                if target != path:
                    _fail("only a RECORD file may have an unhashed row")
                continue
            if not row[1] or not row[2] or not row[2].isascii() or not row[2].isdigit():
                _fail("RECORD digest/size pair is malformed")
            digest_claim = _decode_record_digest(row[1])
            size_claim = int(row[2])
            actual = regular_rows.get(target)
            if actual is None or actual != (size_claim, digest_claim):
                _fail("RECORD target identity differs")
            if target in owners:
                _fail("RECORD target has duplicate owners")
            owners[target] = path
            hashed_rows += 1
            hashed_bytes += size_claim

    scaffold_b64 = value.get("unrecorded_runtime_scaffold_paths_b64")
    if type(scaffold_b64) is not list:
        _fail("RECORD scaffold list differs")
    scaffold = {_decode_manifest_path(item) for item in scaffold_b64}
    site_prefix = b"lib/python3.11/site-packages/"
    site_regular = {path for path in regular_rows if path.startswith(site_prefix)}
    if site_regular - set(owners) - record_file_targets:
        _fail("site-packages contains an unrecorded regular file")
    if set(regular_rows) - site_regular - set(owners) - scaffold:
        _fail("runtime scaffold regular-file set differs")
    actual_summary = {
        "digest_mismatches": 0,
        "duplicate_owners": 0,
        "hashed_regular_bytes": hashed_bytes,
        "hashed_rows": hashed_rows,
        "missing_record_targets": 0,
        "record_file_count": len(record_files),
        "record_rows": record_rows,
        "unhashed_rows": unhashed_rows,
        "unrecorded_site_files": 0,
    }
    for key, summary_value in actual_summary.items():
        if value.get(key) != summary_value:
            _fail("RECORD reconciliation total differs")
    return len(record_files), record_rows, hashed_rows, unhashed_rows


def _open_directory_path(root_fd: int, path: bytes) -> int:
    current = os.dup(root_fd)
    try:
        for component in path.split(b"/"):
            if component in {b"", b".", b".."}:
                _fail("descriptor-relative path is invalid")
            following = _open_child(current, component, directory=True)
            os.close(current)
            current = following
        return current
    except BaseException:
        try:
            os.close(current)
        except OSError:
            pass
        raise


def _verify_fixed_live_identities(
    roots: _RootDescriptors,
    runtime: _TreeVerification,
    cpython: _TreeVerification,
) -> None:
    interpreter = b"bin/python3.11"
    actual = cpython.regular_rows.get(interpreter)
    if actual is None or actual[1] != _EXPECTED_INTERPRETER_SHA:
        _fail("pinned interpreter identity differs")
    for path, expected_digest in _EXPECTED_NATIVE.items():
        actual = runtime.regular_rows.get(path)
        if actual is None or actual[1] != expected_digest:
            _fail("native-library identity differs")
    # The root descriptors are intentionally touched after all descendant reads so a
    # visible-path replacement cannot silently substitute a second tree.
    for label, fd in (("sandbox", roots.sandbox), ("python", roots.python), ("venv", roots.venv)):
        info = os.fstat(fd)
        if (info.st_dev, info.st_ino, info.st_uid, info.st_gid) != _ROOT_IDENTITIES[label]:
            _fail("root descriptor identity changed during verification")


def _verify_with_open_roots(
    roots: _RootDescriptors,
    artifacts: dict[str, bytes],
    *,
    state: RuntimeState,
    retain_directory_fds: bool,
) -> tuple[RuntimeIdentityEvidence, _TreeVerification, _TreeVerification]:
    runtime = _verify_tree(
        roots.venv,
        artifacts["runtime_manifest"],
        root_id="scanpy-1.11.5-venv",
        state=state,
        retain_directory_fds=retain_directory_fds,
    )
    try:
        cpython = _verify_tree(
            roots.python,
            artifacts["cpython_manifest"],
            root_id="cpython-3.11.15-prefix",
            state=state,
            retain_directory_fds=retain_directory_fds,
        )
    except BaseException:
        runtime.close()
        raise
    try:
        expected_runtime_mismatches = 1_117 if state == "pre-restoration" else 0
        expected_cpython_mismatches = 312 if state == "pre-restoration" else 0
        if (
            (runtime.entries, runtime.directories, runtime.regular_files, runtime.symlinks)
            != (12_687, 1_117, 11_567, 3)
            or (cpython.entries, cpython.directories, cpython.regular_files, cpython.symlinks)
            != (3_149, 312, 2_828, 9)
            or runtime.directory_mode_mismatches != expected_runtime_mismatches
            or cpython.directory_mode_mismatches != expected_cpython_mismatches
        ):
            _fail("manifest census or authorized directory-mode delta differs")
        if runtime.pyc_files != 0 or runtime.pth_files != 0:
            _fail("runtime contains forbidden cache or path files")
        wheels = _verify_wheels(roots.parent, artifacts["wheel_manifest"])
        record_files, rows, hashed_rows, unhashed_rows = _verify_records(
            roots.venv,
            runtime.regular_rows,
            artifacts["record_reconciliation"],
        )
        _verify_fixed_live_identities(roots, runtime, cpython)
        evidence = RuntimeIdentityEvidence(
            state=state,
            runtime_entries=runtime.entries,
            runtime_directories=runtime.directories,
            runtime_regular_files=runtime.regular_files,
            runtime_symlinks=runtime.symlinks,
            cpython_entries=cpython.entries,
            cpython_directories=cpython.directories,
            cpython_regular_files=cpython.regular_files,
            cpython_symlinks=cpython.symlinks,
            wheel_files=wheels,
            record_files=record_files,
            record_rows=rows,
            hashed_record_rows=hashed_rows,
            unhashed_record_rows=unhashed_rows,
            owner_pairs=tuple(sorted(runtime.owners | cpython.owners)),
            pyc_files=runtime.pyc_files,
            pth_files=runtime.pth_files,
            artifact_sha256=tuple(
                (name, f"sha256:{_sha256(raw)}") for name, raw in sorted(artifacts.items())
            ),
        )
        return evidence, runtime, cpython
    except BaseException:
        runtime.close()
        cpython.close()
        raise


def verify_runtime_identity_v1(state: RuntimeState = "sealed") -> RuntimeIdentityEvidence:
    """Recompute the complete external runtime identity without mutating it."""

    if state not in {"pre-restoration", "sealed"}:
        raise RuntimeAuthenticationError("unknown runtime state")
    artifacts = read_runtime_artifacts_v1()
    modes = _PRE_ROOT_MODES if state == "pre-restoration" else _SEALED_ROOT_MODES
    roots = _open_roots(modes)
    try:
        evidence, runtime, cpython = _verify_with_open_roots(
            roots,
            artifacts,
            state=state,
            retain_directory_fds=False,
        )
        runtime.close()
        cpython.close()
        return evidence
    finally:
        roots.close()


def restore_runtime_directory_modes_v1() -> tuple[RuntimeIdentityEvidence, RuntimeIdentityEvidence]:
    """Perform the one authorized, fully authenticated directory-mode transition."""

    artifacts = read_runtime_artifacts_v1()
    try:
        sealed_roots = _open_roots(_SEALED_ROOT_MODES)
        try:
            sealed, runtime, cpython = _verify_with_open_roots(
                sealed_roots,
                artifacts,
                state="sealed",
                retain_directory_fds=False,
            )
            runtime.close()
            cpython.close()
            return sealed, sealed
        finally:
            sealed_roots.close()
    except (OSError, RuntimeAuthenticationError):
        # Only an independently authenticated complete sealed state is idempotent.
        # The pre-restoration verifier below still refuses every mixed/unknown state.
        pass
    roots = _open_roots(_PRE_ROOT_MODES)
    try:
        before, runtime, cpython = _verify_with_open_roots(
            roots,
            artifacts,
            state="pre-restoration",
            retain_directory_fds=True,
        )
        try:
            combined = [(path, fd) for path, fd in runtime.directory_fds.items()]
            combined.extend((path, fd) for path, fd in cpython.directory_fds.items())
            for _path, fd in sorted(
                combined,
                key=lambda item: (item[0].count(b"/"), item[0]),
                reverse=True,
            ):
                os.fchmod(fd, 0o555)
            os.fchmod(roots.python, 0o555)
            os.fchmod(roots.venv, 0o555)
            os.fchmod(roots.sandbox, 0o555)
        finally:
            runtime.close()
            cpython.close()
    finally:
        roots.close()
    after = verify_runtime_identity_v1("sealed")
    return before, after


def runtime_root_path_v1() -> Path:
    """Return the fixed root for diagnostic display; never use it for launch."""

    return _RUNTIME_PARENT / _SANDBOX_NAME


__all__ = [
    "RuntimeAuthenticationError",
    "RuntimeIdentityEvidence",
    "read_runtime_artifacts_v1",
    "restore_runtime_directory_modes_v1",
    "runtime_root_path_v1",
    "validate_prelaunch_provenance_v1",
    "verify_runtime_identity_v1",
]
