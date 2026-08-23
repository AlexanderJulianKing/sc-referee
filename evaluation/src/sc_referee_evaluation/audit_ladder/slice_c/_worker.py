"""Isolated Slice-C worker program.

This file is never imported.  The controller authenticates its bytes and supplies
them to the sealed interpreter with ``-c``.  It writes exactly one canonical frame
to stdout and never writes explanatory text.
"""

from __future__ import annotations

import base64
import binascii
import csv
import hashlib
import io
import json
import os
import resource
import stat
import sys
import unicodedata
import warnings
from collections import Counter
from collections.abc import Iterable
from typing import Any, NoReturn

REQUEST_LIMIT = 22_371_000
EXPECTED_ENV = {
    "LC_ALL": "C",
    "PATH": "/usr/bin:/bin",
    "TZ": "UTC",
    "__CF_USER_TEXT_ENCODING": "0x1F5:0x0:0x0",
}
POST_IMPORT_ENV = {
    **EXPECTED_ENV,
    "KMP_DUPLICATE_LIB_OK": "True",
    "KMP_INIT_AT_FORK": "FALSE",
}
ARTIFACTS = {
    "cpython_manifest": (
        807_212,
        "sha256:4cccef84e310d2c40935e77b92343833bf5050c42feb325afde5385242e2c388",
    ),
    "premise": (3_443, "sha256:0f3db3490b640ed80a12c94038c3d78f18d5aa431cab42e8ec73ee2b54b21d04"),
    "record_reconciliation": (
        7_745,
        "sha256:ad8671d57e252a7d0eeb28b6b3c8d964ce5615a8e3fad890c83cbe1084b66b97",
    ),
    "root_seal": (960, "sha256:07dd8873f3b5ce4b94ca4b536bb2cbaeafc7f9be42dad2f16b1be495d4fba4e6"),
    "runtime_manifest": (
        3_394_894,
        "sha256:dcb663037d60a94cf48a34f335a857f2fa8a710a1fc712611891a884dfcab6e1",
    ),
    "semantic_measurement": (
        12_975,
        "sha256:ccd2f42d1542e075b18f020e93f84533159cfff536ba760013c76d781e3f9a91",
    ),
    "wheel_manifest": (
        6_612,
        "sha256:5fd6106fdd73c3e11ac3030d078640c6b7e9fa85b926ac6f74d04c0c7e9b5d1e",
    ),
}
CONTROLLER = {
    "registry-invalid",
    "request-bytes",
    "request-frame",
    "request-protocol",
    "decoded-bytes",
    "cpu",
    "wall",
    "rss",
    "stdout",
    "stderr",
    "nofile",
    "fsize",
    "core",
    "process-status",
    "response-frame",
    "response-protocol",
    "post-run-identity",
}
WORKER = {
    "artifact-authentication",
    "inventory-identity",
    "private-request",
    "h5ad-payload-authentication",
    "runtime-identity",
    "h5ad-semantics-not-closed",
    "worker-internal",
}
ROOTS = {
    ".": (16_777_233, 394_647_433, 501, 20, 0o555),
    "python": (16_777_233, 394_647_434, 501, 20, 0o555),
    "venv": (16_777_233, 394_650_585, 501, 20, 0o555),
    "..": (16_777_233, 394_647_424, 501, 20, 0o755),
}
SANDBOX_PATH = "/Users/alexanderking/sc-referee-runtimes/h5ad-tier1-scanpy1115-final-sandbox"
EXPECTED_SYS_PATH = [
    "venv/lib/python3.11/site-packages",
    SANDBOX_PATH + "/python/lib/python311.zip",
    SANDBOX_PATH + "/python/lib/python3.11",
    SANDBOX_PATH + "/python/lib/python3.11/lib-dynload",
]


class Reject(Exception):
    def __init__(self, facet: str) -> None:
        self.facet = facet


def reject(facet: str) -> NoReturn:
    if facet not in WORKER:
        facet = "worker-internal"
    raise Reject(facet)


def digest(raw: bytes | bytearray | memoryview) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8", "strict")


def emit(value: dict[str, Any]) -> None:
    raw = canonical(value) + b"\n"
    offset = 0
    while offset < len(raw):
        offset += os.write(1, raw[offset:])


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate")
        value[key] = item
    return value


def parse_frame(raw: bytes, facet: str) -> dict[str, Any]:
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r" in raw:
        reject(facet)
    try:
        value = json.loads(raw[:-1], object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        reject(facet)
    if type(value) is not dict or canonical(value) + b"\n" != raw:
        reject(facet)
    return value


def exact_keys(value: object, keys: Iterable[str], facet: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(keys):
        reject(facet)
    return value


def safe_path(value: object, facet: str) -> str:
    if type(value) is not str:
        reject(facet)
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeEncodeError:
        reject(facet)
    if (
        not 1 <= len(encoded) <= 512
        or value.startswith("/")
        or "\\" in value
        or "\0" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        reject(facet)
    return value


def safe_string(value: object, facet: str) -> str:
    if type(value) is not str:
        reject(facet)
    try:
        encoded = value.encode("utf-8", "strict")
    except UnicodeEncodeError:
        reject(facet)
    if (
        len(encoded) > 1_024
        or unicodedata.normalize("NFC", value) != value
        or any(unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for char in value)
    ):
        reject(facet)
    return value


def text_wrapper(value: object, facet: str) -> bytes:
    value = exact_keys(value, {"byte_size", "sha256", "utf8"}, facet)
    if (
        type(value["byte_size"]) is not int
        or type(value["sha256"]) is not str
        or type(value["utf8"]) is not str
    ):
        reject(facet)
    try:
        raw = value["utf8"].encode("utf-8", "strict")
    except UnicodeEncodeError:
        reject(facet)
    if value["byte_size"] != len(raw) or value["sha256"] != digest(raw):
        reject(facet)
    return raw


def canonical_json(raw: bytes, jsonl: bool, facet: str) -> Any:
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r" in raw:
        reject(facet)
    lines = raw[:-1].split(b"\n") if jsonl else [raw[:-1]]
    values = []
    for line in lines:
        try:
            value = json.loads(line, object_pairs_hook=unique_object)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            reject(facet)
        if type(value) is not dict or canonical(value) != line:
            reject(facet)
        values.append(value)
    return values if jsonl else values[0]


def decode_payload(value: object) -> bytes:
    value = exact_keys(value, {"byte_size", "payload_b64", "sha256"}, "h5ad-payload-authentication")
    if (
        type(value["byte_size"]) is not int
        or value["byte_size"] < 0
        or type(value["payload_b64"]) is not str
    ):
        reject("h5ad-payload-authentication")
    if any(char.isspace() for char in value["payload_b64"]):
        reject("h5ad-payload-authentication")
    try:
        raw = base64.b64decode(value["payload_b64"], validate=True)
    except (binascii.Error, ValueError):
        reject("h5ad-payload-authentication")
    if (
        base64.b64encode(raw).decode("ascii") != value["payload_b64"]
        or len(raw) != value["byte_size"]
        or digest(raw) != value["sha256"]
    ):
        reject("h5ad-payload-authentication")
    return bytes(raw)


def authenticate_artifacts(request: dict[str, Any]) -> dict[str, bytes]:
    artifacts = exact_keys(request.get("artifacts"), ARTIFACTS, "artifact-authentication")
    result: dict[str, bytes] = {}
    for name, (size, sha) in ARTIFACTS.items():
        raw = text_wrapper(artifacts[name], "artifact-authentication")
        if len(raw) != size or digest(raw) != sha:
            reject("artifact-authentication")
        result[name] = raw
    canonical_json(result["premise"], False, "artifact-authentication")
    canonical_json(result["root_seal"], False, "artifact-authentication")
    canonical_json(result["record_reconciliation"], False, "artifact-authentication")
    canonical_json(result["semantic_measurement"], False, "artifact-authentication")
    for name in ("runtime_manifest", "cpython_manifest", "wheel_manifest"):
        canonical_json(result[name], True, "artifact-authentication")
    return result


def parse_inner_wrapper(wrapper: object, facet: str) -> tuple[bytes, dict[str, Any]]:
    raw = text_wrapper(wrapper, facet)
    try:
        value = json.loads(raw, object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        reject(facet)
    if type(value) is not dict or canonical(value) != raw:
        reject(facet)
    return raw, value


def record_ref(value: object, record_type: str, facet: str) -> str:
    value = exact_keys(value, {"record_id", "record_type"}, facet)
    if value["record_type"] != record_type or type(value["record_id"]) is not str:
        reject(facet)
    return value["record_id"]


def authenticate_repository(
    request: dict[str, Any], source_raw: bytes, h5ad_raw: bytes
) -> list[str]:
    facet = "inventory-identity"
    repository = exact_keys(
        request.get("repository"),
        {
            "file_manifest",
            "file_records",
            "selected_materials",
            "snapshot_identity",
            "snapshot_ref",
        },
        facet,
    )
    manifest = exact_keys(
        repository["file_manifest"],
        {"byte_size", "entry_count", "file_manifest_ref", "sha256", "utf8"},
        facet,
    )
    if type(manifest["utf8"]) is not str:
        reject(facet)
    manifest_raw = manifest["utf8"].encode("utf-8", "strict")
    if (
        manifest["byte_size"] != len(manifest_raw)
        or manifest["sha256"] != digest(manifest_raw)
        or type(manifest["entry_count"]) is not int
        or manifest["entry_count"] < 1
        or manifest["file_manifest_ref"] != "observed/files.jsonl"
        or not manifest_raw.endswith(b"\n")
        or manifest_raw.endswith(b"\n\n")
    ):
        reject(facet)
    lines = manifest_raw[:-1].split(b"\n")
    if len(lines) != manifest["entry_count"]:
        reject(facet)
    records = repository["file_records"]
    if type(records) is not list or len(records) != len(lines):
        reject(facet)
    file_values: list[dict[str, Any]] = []
    previous = ""
    for line, wrapper in zip(lines, records, strict=True):
        raw, value = parse_inner_wrapper(wrapper, facet)
        if raw != line or set(value) != {
            "asset_identity_ref",
            "byte_size",
            "entry_kind",
            "file_record_id",
            "path",
            "record_type",
            "snapshot_ref",
        }:
            reject(facet)
        path = safe_path(value.get("path"), facet)
        if path <= previous:
            reject(facet)
        previous = path
        file_values.append(value)
    snapshot_raw, snapshot = parse_inner_wrapper(repository["snapshot_identity"], facet)
    if (
        repository["snapshot_ref"] != "snapshot:" + digest(snapshot_raw)[7:27]
        or set(snapshot) != {"files", "schema"}
        or snapshot.get("schema") != "slice-c-snapshot-identity-v1"
        or type(snapshot.get("files")) is not list
        or len(snapshot["files"]) != len(file_values)
    ):
        reject(facet)
    identities: list[dict[str, Any]] = []
    previous = ""
    for identity in snapshot["files"]:
        identity = exact_keys(identity, {"byte_size", "path", "schema", "sha256"}, facet)
        path = safe_path(identity["path"], facet)
        if (
            path <= previous
            or identity["schema"] != "slice-c-material-identity-v1"
            or type(identity["byte_size"]) is not int
            or identity["byte_size"] < 0
            or type(identity["sha256"]) is not str
        ):
            reject(facet)
        previous = path
        identities.append(identity)
    if [item["path"] for item in identities] != [item["path"] for item in file_values]:
        reject(facet)
    for file_value, identity in zip(file_values, identities, strict=True):
        suffix = digest(canonical(identity))[7:27]
        if (
            file_value["record_type"] != "file_record"
            or file_value["file_record_id"] != "file:" + suffix
            or type(file_value["byte_size"]) is not int
            or file_value["byte_size"] != identity["byte_size"]
            or file_value["entry_kind"] not in {"regular_file", "directory", "symlink", "special"}
            or record_ref(file_value["snapshot_ref"], "repository_snapshot", facet)
            != repository["snapshot_ref"]
            or record_ref(file_value["asset_identity_ref"], "asset_identity", facet)
            != "asset-identity:" + suffix
        ):
            reject(facet)
    selected = exact_keys(repository["selected_materials"], {"h5ad", "source"}, facet)
    payloads = {"source": source_raw, "h5ad": h5ad_raw}
    private = request.get("slice_c_request")
    if type(private) is not dict:
        reject(facet)
    paths = {
        "source": safe_path(private.get("source_path"), facet),
        "h5ad": safe_path(private.get("h5ad_path"), facet),
    }
    for role in ("source", "h5ad"):
        value = exact_keys(
            selected[role],
            {"asset_identity", "frozen_material", "material_ref"},
            facet,
        )
        _asset_raw, asset = parse_inner_wrapper(value["asset_identity"], facet)
        frozen_raw, frozen = parse_inner_wrapper(value["frozen_material"], facet)
        matches = [item for item in file_values if item.get("path") == paths[role]]
        identity_matches = [item for item in identities if item.get("path") == paths[role]]
        if len(identity_matches) != 1:
            reject(facet)
        suffix = digest(canonical(identity_matches[0]))[7:27]
        file_ref = "file:" + suffix
        asset_ref = "asset-identity:" + suffix
        if (
            len(matches) != 1
            or matches[0].get("entry_kind") != "regular_file"
            or identity_matches[0].get("byte_size") != len(payloads[role])
            or identity_matches[0].get("sha256") != digest(payloads[role])
            or set(asset)
            != {
                "asset_identity_id",
                "asset_ref",
                "identity_evidence",
                "record_type",
                "tier",
            }
            or set(frozen)
            != {
                "asset_identity_ref",
                "byte_size",
                "content_member",
                "file_ref",
                "path",
                "schema",
                "sha256",
            }
            or frozen.get("path") != paths[role]
            or frozen.get("byte_size") != len(payloads[role])
            or frozen.get("sha256") != digest(payloads[role])
            or frozen.get("content_member") != role + "_payload"
            or frozen.get("schema") != "slice-c-frozen-material-v1"
            or value["material_ref"] != "material:" + digest(frozen_raw)[7:27]
            or matches[0].get("file_record_id") != file_ref
            or record_ref(frozen.get("file_ref"), "file_record", facet) != file_ref
            or record_ref(frozen.get("asset_identity_ref"), "asset_identity", facet) != asset_ref
            or asset.get("asset_identity_id") != asset_ref
            or asset.get("record_type") != "asset_identity"
            or asset.get("tier") != "full_digest"
            or record_ref(asset.get("asset_ref"), "file_record", facet) != file_ref
            or asset.get("identity_evidence")
            != {"digest": digest(payloads[role]), "kind": "full_digest"}
        ):
            reject(facet)
    return [item["path"] for item in file_values]


def authenticate_private(request: dict[str, Any]) -> dict[str, Any]:
    private = exact_keys(
        request.get("slice_c_request"),
        {"h5ad_path", "obs_column", "schema", "source_path"},
        "private-request",
    )
    source_path = safe_path(private["source_path"], "private-request")
    h5ad_path = safe_path(private["h5ad_path"], "private-request")
    obs_column = safe_string(private["obs_column"], "private-request")
    try:
        obs_column.encode("ascii", "strict")
    except UnicodeEncodeError:
        reject("private-request")
    if private["schema"] != "slice-c-request-v1" or source_path == h5ad_path:
        reject("private-request")
    return private


def manifest_rows(raw: bytes, root_id: str) -> dict[bytes, dict[str, Any]]:
    values = canonical_json(raw, True, "runtime-identity")
    rows: dict[bytes, dict[str, Any]] = {}
    previous: bytes | None = None
    for value in values:
        if value.get("root_id") != root_id or type(value.get("path_b64")) is not str:
            reject("runtime-identity")
        try:
            path = base64.b64decode(value["path_b64"], validate=True)
        except (binascii.Error, ValueError):
            reject("runtime-identity")
        if base64.b64encode(path).decode("ascii") != value["path_b64"]:
            reject("runtime-identity")
        if not path or any(
            part in {b"", b".", b".."} or b"\0" in part for part in path.split(b"/")
        ):
            reject("runtime-identity")
        if path in rows or (previous is not None and path <= previous):
            reject("runtime-identity")
        previous = path
        rows[path] = value
    return rows


OPEN_DIR = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
OPEN_FILE = os.O_RDONLY | os.O_NOFOLLOW


def hash_file(parent: int, name: bytes, expected: os.stat_result) -> tuple[int, str]:
    fd = os.open(name, OPEN_FILE, dir_fd=parent)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or (before.st_dev, before.st_ino) != (
            expected.st_dev,
            expected.st_ino,
        ):
            reject("runtime-identity")
        h = hashlib.sha256()
        size = 0
        while True:
            block = os.read(fd, 1_048_576)
            if not block:
                break
            h.update(block)
            size += len(block)
        after = os.fstat(fd)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            reject("runtime-identity")
        return size, h.hexdigest()
    finally:
        os.close(fd)


def verify_tree(
    root_name: str,
    manifest_raw: bytes,
    root_id: str,
    counts: tuple[int, int, int, int],
) -> dict[bytes, tuple[int, str]]:
    rows = manifest_rows(manifest_raw, root_id)
    root = os.open(root_name, OPEN_DIR)
    actual: set[bytes] = set()
    owners: set[tuple[int, int]] = set()
    regular: dict[bytes, tuple[int, str]] = {}
    census: Counter[str] = Counter()

    def walk(parent: int, prefix: bytes) -> None:
        names = sorted(os.fsencode(name) for name in os.listdir(parent))
        for name in names:
            path = name if not prefix else prefix + b"/" + name
            row = rows.get(path)
            if row is None:
                reject("runtime-identity")
            actual.add(path)
            info = os.stat(name, dir_fd=parent, follow_symlinks=False)
            owners.add((info.st_uid, info.st_gid))
            mode = format(stat.S_IMODE(info.st_mode), "04o")
            if mode != row.get("mode"):
                reject("runtime-identity")
            if stat.S_ISDIR(info.st_mode):
                if row.get("entry_kind") != "directory" or set(row) != {
                    "entry_kind",
                    "mode",
                    "path_b64",
                    "root_id",
                }:
                    reject("runtime-identity")
                census["directory"] += 1
                child = os.open(name, OPEN_DIR, dir_fd=parent)
                try:
                    opened = os.fstat(child)
                    if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                        reject("runtime-identity")
                    walk(child, path)
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode):
                expected_keys = {"byte_size", "entry_kind", "mode", "path_b64", "root_id", "sha256"}
                if row.get("entry_kind") != "regular-file" or set(row) != expected_keys:
                    reject("runtime-identity")
                size, sha = hash_file(parent, name, info)
                if row.get("byte_size") != size or row.get("sha256") != "sha256:" + sha:
                    reject("runtime-identity")
                census["regular-file"] += 1
                regular[path] = (size, sha)
            elif stat.S_ISLNK(info.st_mode):
                expected_keys = {"entry_kind", "mode", "path_b64", "root_id", "target_b64"}
                target = os.fsencode(os.readlink(name, dir_fd=parent))
                if (
                    row.get("entry_kind") != "symlink"
                    or set(row) != expected_keys
                    or row.get("target_b64") != base64.b64encode(target).decode("ascii")
                ):
                    reject("runtime-identity")
                census["symlink"] += 1
            else:
                reject("runtime-identity")

    try:
        walk(root, b"")
    finally:
        os.close(root)
    if (
        actual != set(rows)
        or owners != {(501, 20)}
        or (len(actual), census["directory"], census["regular-file"], census["symlink"]) != counts
    ):
        reject("runtime-identity")
    return regular


def open_dir_path(root: int, path: bytes) -> int:
    current = os.dup(root)
    try:
        for part in path.split(b"/"):
            following = os.open(part, OPEN_DIR, dir_fd=current)
            os.close(current)
            current = following
        return current
    except BaseException:
        os.close(current)
        raise


def verify_wheels(raw: bytes) -> None:
    rows = canonical_json(raw, True, "runtime-identity")
    if len(rows) != 42:
        reject("runtime-identity")
    parent = os.open("..", OPEN_DIR)
    try:
        artifacts = os.open("h5ad-tier1-scanpy1115-artifacts", OPEN_DIR, dir_fd=parent)
    finally:
        os.close(parent)
    try:
        expected: list[str] = []
        previous = ""
        for row in rows:
            if set(row) != {"byte_size", "filename", "sha256"}:
                reject("runtime-identity")
            name = row.get("filename")
            if type(name) is not str or not name or "/" in name or name <= previous:
                reject("runtime-identity")
            previous = name
            expected.append(name)
            info = os.stat(name, dir_fd=artifacts, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or (info.st_uid, info.st_gid) != (501, 20):
                reject("runtime-identity")
            size, sha = hash_file(artifacts, os.fsencode(name), info)
            if row.get("byte_size") != size or row.get("sha256") != "sha256:" + sha:
                reject("runtime-identity")
        if sorted(os.listdir(artifacts)) != expected:
            reject("runtime-identity")
    finally:
        os.close(artifacts)


def normalize_record(path: str) -> bytes:
    parts = ["lib", "python3.11", "site-packages"]
    for part in path.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                reject("runtime-identity")
            parts.pop()
        else:
            parts.append(part)
    return "/".join(parts).encode("utf-8", "strict")


def record_digest(value: str) -> str:
    if not value.startswith("sha256="):
        reject("runtime-identity")
    encoded = value[7:]
    try:
        raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    except (binascii.Error, ValueError):
        reject("runtime-identity")
    if len(raw) != 32 or base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii") != encoded:
        reject("runtime-identity")
    return raw.hex()


def verify_records(regular: dict[bytes, tuple[int, str]], raw: bytes) -> None:
    reconciliation = canonical_json(raw, False, "runtime-identity")
    record_files = reconciliation.get("record_files")
    if type(record_files) is not list or len(record_files) != 42:
        reject("runtime-identity")
    root = os.open("venv", OPEN_DIR)
    owners: dict[bytes, bytes] = {}
    record_targets: set[bytes] = set()
    totals: Counter[str] = Counter()
    hashed_bytes = 0
    try:
        for record in record_files:
            if type(record) is not dict or set(record) != {"byte_size", "path", "sha256"}:
                reject("runtime-identity")
            path = record.get("path")
            if type(path) is not str or path.encode() not in regular:
                reject("runtime-identity")
            path_raw = path.encode()
            size, sha = regular[path_raw]
            if record.get("byte_size") != size or record.get("sha256") != "sha256:" + sha:
                reject("runtime-identity")
            record_targets.add(path_raw)
            parent_path, name = path_raw.rsplit(b"/", 1)
            parent = open_dir_path(root, parent_path)
            try:
                fd = os.open(name, OPEN_FILE, dir_fd=parent)
                chunks = []
                try:
                    while True:
                        block = os.read(fd, 65_536)
                        if not block:
                            break
                        chunks.append(block)
                finally:
                    os.close(fd)
            finally:
                os.close(parent)
            try:
                rows = list(
                    csv.reader(
                        io.StringIO(b"".join(chunks).decode("utf-8"), newline=""), strict=True
                    )
                )
            except (UnicodeDecodeError, csv.Error):
                reject("runtime-identity")
            for row in rows:
                totals["record_rows"] += 1
                if len(row) != 3 or not row[0]:
                    reject("runtime-identity")
                target = normalize_record(row[0])
                if row[1] == "" and row[2] == "":
                    totals["unhashed_rows"] += 1
                    if target != path_raw:
                        reject("runtime-identity")
                    continue
                if not row[1] or not row[2].isascii() or not row[2].isdigit():
                    reject("runtime-identity")
                claim = (int(row[2]), record_digest(row[1]))
                if regular.get(target) != claim or target in owners:
                    reject("runtime-identity")
                owners[target] = path_raw
                totals["hashed_rows"] += 1
                hashed_bytes += claim[0]
    finally:
        os.close(root)
    scaffold = {
        base64.b64decode(value, validate=True)
        for value in reconciliation.get("unrecorded_runtime_scaffold_paths_b64", [])
    }
    site = {path for path in regular if path.startswith(b"lib/python3.11/site-packages/")}
    if site - set(owners) - record_targets or set(regular) - site - set(owners) - scaffold:
        reject("runtime-identity")
    expected = {
        "record_rows": 11_561,
        "hashed_rows": 11_519,
        "unhashed_rows": 42,
    }
    if dict(totals) != expected or hashed_bytes != 423_831_072:
        reject("runtime-identity")


def verify_root(path: str, expected: tuple[int, int, int, int, int]) -> None:
    info = os.stat(path, follow_symlinks=False)
    actual = (info.st_dev, info.st_ino, info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode))
    if not stat.S_ISDIR(info.st_mode) or actual != expected:
        reject("runtime-identity")


def verify_runtime(
    artifacts: dict[str, bytes],
) -> tuple[dict[bytes, tuple[int, str]], dict[str, Any]]:
    if dict(os.environ) != EXPECTED_ENV:
        reject("runtime-identity")
    if (
        sys.flags.isolated != 1
        or sys.flags.no_site != 1
        or sys.flags.dont_write_bytecode != 1
        or not sys.flags.safe_path
        or sys.flags.utf8_mode != 1
        or resource.getrlimit(resource.RLIMIT_CPU) != (60, 60)
        or resource.getrlimit(resource.RLIMIT_NOFILE) != (128, 128)
        or resource.getrlimit(resource.RLIMIT_FSIZE) != (0, 0)
        or resource.getrlimit(resource.RLIMIT_CORE) != (0, 0)
    ):
        reject("runtime-identity")
    for path, expected in ROOTS.items():
        verify_root(path, expected)
    root_seal = canonical_json(artifacts["root_seal"], False, "runtime-identity")
    if (
        root_seal.get("premise_digest")
        != "sha256:09fe04ea03c03221bf20c00b5e45cd8f66f00d7476f98da64df5dcde79dc7eeb"
    ):
        reject("runtime-identity")
    runtime = verify_tree(
        "venv",
        artifacts["runtime_manifest"],
        "scanpy-1.11.5-venv",
        (12_687, 1_117, 11_567, 3),
    )
    cpython = verify_tree(
        "python",
        artifacts["cpython_manifest"],
        "cpython-3.11.15-prefix",
        (3_149, 312, 2_828, 9),
    )
    if any(path.endswith(b".pyc") or path.endswith(b".pth") for path in runtime):
        reject("runtime-identity")
    if (
        cpython.get(b"bin/python3.11", (0, ""))[1]
        != "68100c5188b837802c7ae52398389d121b1c063ed244dec11649775b539c3a30"
    ):
        reject("runtime-identity")
    verify_wheels(artifacts["wheel_manifest"])
    verify_records(runtime, artifacts["record_reconciliation"])
    parent = os.open("..", OPEN_DIR)
    try:
        for name, expected_digest in (
            (
                "h5ad-tier1-scanpy1115-input-requirements.txt",
                "sha256:3af777d44112f2e8fe4a6488b7cfc29a99af1115de1da1311bd85720d35e58a1",
            ),
            (
                "h5ad-tier1-scanpy1115-resolved-requirements.txt",
                "sha256:0858441c3c36cd6460a9c68f982012a9e73c8e645c15513373325a2eede9aace",
            ),
        ):
            info = os.stat(name, dir_fd=parent, follow_symlinks=False)
            _size, sha = hash_file(parent, os.fsencode(name), info)
            if "sha256:" + sha != expected_digest:
                reject("runtime-identity")
    finally:
        os.close(parent)
    premise = canonical_json(artifacts["premise"], False, "runtime-identity")
    measurement = canonical_json(artifacts["semantic_measurement"], False, "runtime-identity")
    if (
        premise.get("premise_digest") != root_seal.get("premise_digest")
        or premise.get("premise_id") != "scanpy-1.11.5-cpython-3.11.15-macos-arm64-v1"
        or measurement.get("schema") != "scanpy-1.11.5-premise-measurement-v1"
    ):
        reject("runtime-identity")
    return runtime, measurement


def relative_origin(value: object) -> str:
    if type(value) is not str:
        reject("runtime-identity")
    absolute = os.path.realpath(value)
    root = os.path.realpath(".") + os.sep
    if not absolute.startswith(root):
        reject("runtime-identity")
    return absolute[len(root) :]


def callable_identity(
    value: Any,
    expected: dict[str, Any],
    runtime: dict[bytes, tuple[int, str]],
) -> None:
    code = getattr(value, "__code__", None)
    source = relative_origin(__import__("inspect").getsourcefile(value))
    row = runtime.get(os.fsencode(source))
    if (
        code is None
        or digest(code.co_code) != expected.get("code_sha256")
        or getattr(value, "__module__", None) != expected.get("module")
        or getattr(value, "__qualname__", None) != expected.get("qualname")
        or row is None
        or "sha256:" + row[1] != expected.get("source_sha256")
    ):
        reject("runtime-identity")


def normalize_sys_path(value: object, sandbox_path: object) -> str:
    if type(value) is not str or not value or "\0" in value:
        reject("runtime-identity")
    if type(sandbox_path) is not str or not sandbox_path or "\0" in sandbox_path:
        reject("runtime-identity")
    try:
        value.encode("utf-8", "strict")
        sandbox_path.encode("utf-8", "strict")
        candidate = value if os.path.isabs(value) else os.path.join(sandbox_path, value)
        normalized = os.path.realpath(os.path.abspath(candidate))
    except (OSError, TypeError, UnicodeError, ValueError):
        reject("runtime-identity")
    if type(normalized) is not str or not normalized or "\0" in normalized:
        reject("runtime-identity")
    return normalized


def verify_sys_path(value: object, sandbox_path: object) -> None:
    if (
        type(value) is not list
        or len(value) != len(EXPECTED_SYS_PATH)
        or any(type(item) is not str for item in value)
        or value != EXPECTED_SYS_PATH
        or type(sandbox_path) is not str
        or sandbox_path != SANDBOX_PATH
    ):
        reject("runtime-identity")
    normalized = tuple(normalize_sys_path(item, sandbox_path) for item in value)
    expected = tuple(normalize_sys_path(item, SANDBOX_PATH) for item in EXPECTED_SYS_PATH)
    if normalized != expected or expected != (
        SANDBOX_PATH + "/venv/lib/python3.11/site-packages",
        SANDBOX_PATH + "/python/lib/python311.zip",
        SANDBOX_PATH + "/python/lib/python3.11",
        SANDBOX_PATH + "/python/lib/python3.11/lib-dynload",
    ):
        reject("runtime-identity")


def verify_packages(
    runtime: dict[bytes, tuple[int, str]],
    measurement: dict[str, Any],
    inventory: list[str],
) -> tuple[Any, Any, Any, Any]:
    verify_sys_path(sys.path, os.getcwd())
    warnings.filterwarnings("ignore")
    import importlib.machinery
    import importlib.metadata

    import anndata  # type: ignore[import-not-found]
    import h5py  # type: ignore[import-untyped]
    import numpy as np
    import scipy  # type: ignore[import-untyped]
    import scipy.sparse  # type: ignore[import-untyped]
    import scipy.stats  # type: ignore[import-untyped]

    if "scanpy" in sys.modules or dict(os.environ) != POST_IMPORT_ENV:
        reject("runtime-identity")
    expected_importer = measurement.get("importer", {})
    if (
        importlib.machinery.SOURCE_SUFFIXES != expected_importer.get("source_suffixes")
        or importlib.machinery.BYTECODE_SUFFIXES != expected_importer.get("bytecode_suffixes")
        or importlib.machinery.EXTENSION_SUFFIXES != expected_importer.get("extension_suffixes")
        or importlib.machinery.all_suffixes() != expected_importer.get("all_suffixes")
        or sorted(sys.stdlib_module_names) != expected_importer.get("stdlib_top_level_names")
    ):
        reject("runtime-identity")
    distributions = {
        item.metadata["Name"]: item.version for item in importlib.metadata.distributions()
    }
    if distributions != measurement.get("distributions"):
        reject("runtime-identity")
    package_map = {
        name: sorted(values)
        for name, values in sorted(importlib.metadata.packages_distributions().items())
        if any(value in distributions for value in values)
    }
    if package_map != expected_importer.get("distribution_top_level_map"):
        reject("runtime-identity")
    modules = measurement.get("modules", {})
    for name, module, version in (
        ("anndata", anndata, anndata.__version__),
        ("h5py", h5py, h5py.__version__),
        ("numpy", np, np.__version__),
        ("scipy", scipy, scipy.__version__),
    ):
        expected = modules.get(name, {})
        origin = relative_origin(module.__file__)
        if version != expected.get("version") or runtime.get(os.fsencode(origin)) is None:
            reject("runtime-identity")
    callables = measurement.get("callables", {})
    callable_identity(anndata.read_h5ad, callables.get("anndata.read_h5ad", {}), runtime)
    callable_identity(
        anndata.AnnData.__getitem__, callables.get("anndata.AnnData.__getitem__", {}), runtime
    )
    callable_identity(scipy.stats.ttest_ind, callables.get("scipy.stats.ttest_ind", {}), runtime)
    if callables.get("scanpy.read_h5ad") != callables.get("anndata.read_h5ad"):
        reject("runtime-identity")
    plugin_paths = [os.fsdecode(h5py.h5pl.get(index)) for index in range(h5py.h5pl.size())]
    expected_hdf5 = measurement.get("hdf5", {})
    if (
        h5py.version.hdf5_version != expected_hdf5.get("runtime_version")
        or h5py.version.api_version != expected_hdf5.get("api_version")
        or plugin_paths != expected_hdf5.get("plugin_paths")
        or any(os.path.exists(path) for path in plugin_paths)
    ):
        reject("runtime-identity")
    top_levels = set(expected_importer.get("stdlib_top_level_names", [])) | set(package_map)
    suffixes = expected_importer.get("all_suffixes", [])
    candidates = {name + suffix for name in top_levels for suffix in suffixes} | top_levels
    if any(path in candidates for path in inventory):
        reject("inventory-identity")
    return anndata, h5py, np, scipy.sparse


def require_attr(obj: Any, key: str, expected: object) -> None:
    if key not in obj.attrs:
        reject("h5ad-semantics-not-closed")
    actual = obj.attrs[key]
    if isinstance(actual, bytes):
        actual = actual.decode("utf-8", "strict")
    if isinstance(expected, list):
        actual = list(actual.tolist())
        actual = [item.decode("utf-8") if isinstance(item, bytes) else item for item in actual]
    if actual != expected:
        reject("h5ad-semantics-not-closed")


def decode_strings(dataset: Any, np: Any) -> list[str]:
    values = np.asarray(dataset[...]).reshape(-1).tolist()
    result: list[str] = []
    for value in values:
        if isinstance(value, bytes):
            try:
                result.append(value.decode("utf-8", "strict"))
            except UnicodeDecodeError:
                reject("h5ad-semantics-not-closed")
        elif isinstance(value, str):
            result.append(value)
        else:
            reject("h5ad-semantics-not-closed")
    for value in result:
        safe_string(value, "h5ad-semantics-not-closed")
    return result


def validate_h5ad(
    raw: bytes,
    column_name: str,
    anndata: Any,
    h5py: Any,
    np: Any,
    sparse: Any,
) -> dict[str, Any]:
    private = bytes(raw)
    stream = io.BytesIO(private)
    try:
        handle = h5py.File(stream, "r")
    except BaseException:
        stream.close()
        reject("h5ad-semantics-not-closed")
    try:

        def visit_links(group: Any) -> None:
            for name in group:
                link = group.get(name, getlink=True)
                if not isinstance(link, h5py.HardLink):
                    reject("h5ad-semantics-not-closed")
                obj = group[name]
                if isinstance(obj, h5py.Dataset):
                    if (
                        obj.is_virtual
                        or obj.external
                        or any(
                            value not in (None, False, 0)
                            for value in (
                                obj.compression,
                                obj.shuffle,
                                obj.fletcher32,
                                obj.scaleoffset,
                            )
                        )
                    ):
                        reject("h5ad-semantics-not-closed")
                elif isinstance(obj, h5py.Group):
                    visit_links(obj)
                else:
                    reject("h5ad-semantics-not-closed")

        visit_links(handle)
        require_attr(handle, "encoding-type", "anndata")
        require_attr(handle, "encoding-version", "0.1.0")
        if set(handle) != {"X", "layers", "obs", "obsm", "obsp", "uns", "var", "varm", "varp"}:
            reject("h5ad-semantics-not-closed")
        for name in ("layers", "obsm", "obsp", "uns", "varm", "varp"):
            obj = handle[name]
            if not isinstance(obj, h5py.Group) or len(obj) != 0:
                reject("h5ad-semantics-not-closed")
            require_attr(obj, "encoding-type", "dict")
            require_attr(obj, "encoding-version", "0.1.0")
        x = handle["X"]
        if not isinstance(x, h5py.Group) or set(x) != {"data", "indices", "indptr"}:
            reject("h5ad-semantics-not-closed")
        require_attr(x, "encoding-type", "csr_matrix")
        require_attr(x, "encoding-version", "0.1.0")
        shape = tuple(int(item) for item in np.asarray(x.attrs.get("shape", [])).tolist())
        if len(shape) != 2 or not 1 <= shape[0] <= 100_000 or not 1 <= shape[1] <= 1_024:
            reject("h5ad-semantics-not-closed")
        data = np.asarray(x["data"][...])
        indices = np.asarray(x["indices"][...])
        indptr = np.asarray(x["indptr"][...])
        if (
            data.ndim != 1
            or indices.ndim != 1
            or indptr.ndim != 1
            or data.dtype != np.dtype("float32")
            or indices.dtype != np.dtype("int32")
            or indptr.dtype != np.dtype("int32")
            or data.size > 8_000_000
            or not np.isfinite(data).all()
            or len(indptr) != shape[0] + 1
            or indptr[0] != 0
            or indptr[-1] != len(data)
            or len(indices) != len(data)
            or np.any(np.diff(indptr) < 0)
        ):
            reject("h5ad-semantics-not-closed")
        for row in range(shape[0]):
            row_indices = indices[indptr[row] : indptr[row + 1]]
            if (
                np.any(row_indices < 0)
                or np.any(row_indices >= shape[1])
                or (row_indices.size > 1 and np.any(np.diff(row_indices) <= 0))
            ):
                reject("h5ad-semantics-not-closed")
        obs = handle["obs"]
        var = handle["var"]
        if not isinstance(obs, h5py.Group) or not isinstance(var, h5py.Group):
            reject("h5ad-semantics-not-closed")
        for frame in (obs, var):
            require_attr(frame, "encoding-type", "dataframe")
            require_attr(frame, "encoding-version", "0.2.0")
        obs_index = obs.attrs.get("_index")
        var_index = var.attrs.get("_index")
        if isinstance(obs_index, bytes):
            obs_index = obs_index.decode("utf-8", "strict")
        if isinstance(var_index, bytes):
            var_index = var_index.decode("utf-8", "strict")
        if type(obs_index) is not str or type(var_index) is not str:
            reject("h5ad-semantics-not-closed")
        if set(obs) != {obs_index, column_name} or set(var) != {var_index}:
            reject("h5ad-semantics-not-closed")
        require_attr(obs, "column-order", [column_name])
        require_attr(var, "column-order", [])
        for dataset in (obs[obs_index], var[var_index]):
            require_attr(dataset, "encoding-type", "string-array")
            require_attr(dataset, "encoding-version", "0.2.0")
        obs_names = decode_strings(obs[obs_index], np)
        var_names = decode_strings(var[var_index], np)
        if len(obs_names) != shape[0] or len(set(obs_names)) != len(obs_names):
            reject("h5ad-semantics-not-closed")
        if len(var_names) != shape[1] or len(set(var_names)) != len(var_names):
            reject("h5ad-semantics-not-closed")
        column = obs[column_name]
        if not isinstance(column, h5py.Group) or set(column) != {"categories", "codes"}:
            reject("h5ad-semantics-not-closed")
        require_attr(column, "encoding-type", "categorical")
        require_attr(column, "encoding-version", "0.2.0")
        ordered = column.attrs.get("ordered")
        if not isinstance(ordered, (bool, np.bool_)):
            reject("h5ad-semantics-not-closed")
        require_attr(column["categories"], "encoding-type", "string-array")
        require_attr(column["categories"], "encoding-version", "0.2.0")
        require_attr(column["codes"], "encoding-type", "array")
        require_attr(column["codes"], "encoding-version", "0.2.0")
        categories = decode_strings(column["categories"], np)
        if not 2 <= len(categories) <= 1_024 or len(set(categories)) != len(categories):
            reject("h5ad-semantics-not-closed")
        codes = np.asarray(column["codes"][...])
        if (
            codes.ndim != 1
            or codes.dtype.kind not in {"i", "u"}
            or len(codes) != shape[0]
            or np.any(codes < 0)
            or np.any(codes >= len(categories))
            or set(int(item) for item in np.unique(codes)) != set(range(len(categories)))
        ):
            reject("h5ad-semantics-not-closed")
        values = [categories[int(code)] for code in codes]
        if sum(len(value.encode("utf-8")) for value in values) > 4_194_304:
            reject("h5ad-semantics-not-closed")
    finally:
        handle.close()
    if digest(stream.getbuffer()) != digest(private):
        stream.close()
        reject("h5ad-payload-authentication")
    stream.seek(0)
    try:
        reader = anndata.read_h5ad(stream)
    except BaseException:
        stream.close()
        reject("h5ad-semantics-not-closed")
    if (
        tuple(reader.shape) != shape
        or not sparse.issparse(reader.X)
        or not isinstance(reader.X, sparse.csr_matrix)
        or reader.X.dtype != np.dtype("float32")
        or [str(item) for item in reader.obs[column_name].tolist()] != values
        or [str(item) for item in reader.obs_names] != obs_names
        or [str(item) for item in reader.var_names] != var_names
        or digest(stream.getbuffer()) != digest(private)
    ):
        stream.close()
        reject("h5ad-semantics-not-closed")
    group_counts = Counter(values)
    groups = [
        {"count": group_counts[value], "value": value}
        for value in sorted(group_counts, key=canonical)
    ]
    facts = {
        "matrix-shape": {"column_count": shape[1], "row_count": shape[0]},
        "obs-column-cardinality": {
            "column": column_name,
            "distinct_count": len(groups),
            "n_obs": len(values),
        },
        "obs-column-quoted-values": {
            "column": column_name,
            "n_obs": len(values),
            "values": values,
        },
        "obs-group-sizes": {"column": column_name, "groups": groups, "n_obs": len(values)},
    }
    if digest(stream.getbuffer()) != digest(private):
        stream.close()
        reject("h5ad-payload-authentication")
    stream.close()
    return facts


def main() -> None:
    raw = sys.stdin.buffer.read(REQUEST_LIMIT + 1)
    if len(raw) > REQUEST_LIMIT:
        reject("worker-internal")
    request = parse_frame(raw, "worker-internal")
    if set(request) != {
        "artifacts",
        "h5ad_payload",
        "repository",
        "schema",
        "slice_c_request",
        "source_payload",
    }:
        reject("worker-internal")
    if request.get("schema") != "slice-c-worker-request-v1":
        reject("worker-internal")
    artifacts = authenticate_artifacts(request)
    source_raw = text_wrapper(request.get("source_payload"), "artifact-authentication")
    h5ad_raw = decode_payload(request.get("h5ad_payload"))
    inventory = authenticate_repository(request, source_raw, h5ad_raw)
    private = authenticate_private(request)
    runtime, measurement = verify_runtime(artifacts)
    sys.path.insert(0, "venv/lib/python3.11/site-packages")
    anndata, h5py, np, sparse = verify_packages(runtime, measurement, inventory)
    facts = validate_h5ad(h5ad_raw, private["obs_column"], anndata, h5py, np, sparse)
    for path, expected in ROOTS.items():
        verify_root(path, expected)
    emit(
        {
            "facts": facts,
            "schema": "slice-c-worker-success-v1",
            "worker_request_sha256": digest(raw),
        }
    )


try:
    main()
except Reject as error:
    emit({"facet": error.facet, "schema": "slice-c-worker-refusal-v1"})
except BaseException:
    emit({"facet": "worker-internal", "schema": "slice-c-worker-refusal-v1"})
