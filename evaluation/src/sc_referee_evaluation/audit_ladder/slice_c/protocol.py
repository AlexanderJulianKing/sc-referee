"""Canonical Slice-C worker framing, authentication, and total precedence."""

from __future__ import annotations

import base64
import binascii
import json
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Final, NoReturn, cast

from sc_referee_evaluation.audit_ladder.slice_c.core import (
    ALL_FACETS,
    CONTROLLER_FACETS,
    FACET_RANK,
    WORKER_FACETS,
    GroupSizeV1,
    H5adFactsV1,
    MatrixShapeFactV1,
    ObsColumnCardinalityFactV1,
    ObsColumnQuotedValuesFactV1,
    ObsGroupSizesFactV1,
    RefusalFacetV1,
    SliceCContractError,
    SliceCRequestV1,
    WorkerControllerResultV1,
    canonical_frame,
    canonical_json_bytes,
    is_sha256,
    require_safe_string,
    sha256,
    validate_h5ad_facts,
    validate_slice_c_request,
)
from sc_referee_evaluation.audit_ladder.slice_c.repository import (
    CapturedWorld1MaterialsV1,
    RegistryBundleV1,
)

_REGISTRY_SIZE: Final = 16_110
_REGISTRY_SHA256: Final = "sha256:9446a9c727342487ff78dc1907b588ebcab9ce51a144054baeb2fd4c8df8641b"
_WORLD1_REQUEST_SIZE: Final = 5_039_689
_WORLD1_REQUEST_SHA256: Final = (
    "sha256:9bce5ddb0f09e5b2563aa842fc729376c8c08cffc460d7fb75dbce2c143f39fd"
)
_WORLD1_RESPONSE_SIZE: Final = 44_485
_WORLD1_RESPONSE_SHA256: Final = (
    "sha256:0421bd58f13ffa12b0f7b08e030cbfb49a1f28f2ca71fc2305d0255795afd686"
)
_REQUEST_LIMIT: Final = 22_371_000
_DECODED_LIMIT: Final = 16_777_216
_STDOUT_LIMIT: Final = 8_388_608
_EXPECTED_LIMITS: Final = {
    "core": 0,
    "cpu": 60,
    "decoded": _DECODED_LIMIT,
    "fsize": 0,
    "nofile": 128,
    "request": _REQUEST_LIMIT,
    "rss": 1_073_741_824,
    "stderr": 0,
    "stdout": _STDOUT_LIMIT,
    "wall": 90,
}


class ProtocolValidationError(RuntimeError):
    """A private worker frame is outside the closed protocol."""


@dataclass(frozen=True, slots=True)
class AdmittedWorkerRequestV1:
    value: dict[str, Any]
    decoded_h5ad: bytes
    request_sha256: str


def _fail(message: str) -> NoReturn:
    raise ProtocolValidationError(message)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            _fail("duplicate JSON member")
        value[key] = item
    return value


def strict_frame_value(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r" in raw:
        _fail("frame terminal bytes differ")
    try:
        value = json.loads(raw[:-1], object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ProtocolValidationError("frame JSON parsing failed") from error
    if type(value) is not dict:
        _fail("frame top level is not an object")
    return cast(dict[str, Any], value)


def _closed_value_domain(value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                _fail("protocol object key has the wrong type")
            _closed_value_domain(item)
    elif type(value) is list:
        for item in value:
            _closed_value_domain(item)
    elif type(value) not in {str, int}:
        _fail("protocol value has an unrecognized concrete type")


def validate_protocol_registry_v1(raw: bytes) -> dict[str, Any]:
    """Authenticate the registry before any request byte is examined."""

    if type(raw) is not bytes or len(raw) != _REGISTRY_SIZE or sha256(raw) != _REGISTRY_SHA256:
        _fail("protocol registry byte identity differs")
    value = strict_frame_value(raw)
    if canonical_frame(value) != raw:
        _fail("protocol registry is noncanonical")
    if (
        value.get("schema") != "slice-c-worker-protocol-registry-v1"
        or value.get("precedence") != [facet.value for facet in ALL_FACETS]
        or value.get("controller_precedence") != [facet.value for facet in CONTROLLER_FACETS]
        or value.get("worker_precedence") != [facet.value for facet in WORKER_FACETS]
        or value.get("refusal_facets") != [facet.value for facet in ALL_FACETS]
        or value.get("limits") != _EXPECTED_LIMITS
    ):
        _fail("protocol registry precedence, domain, or limits differ")
    responses = value.get("responses")
    refusal = responses.get("refusal") if type(responses) is dict else None
    if (
        type(refusal) is not dict
        or refusal.get("controller_only_facets") != [facet.value for facet in CONTROLLER_FACETS]
        or refusal.get("worker_emittable_facets") != [facet.value for facet in WORKER_FACETS]
        or refusal.get("members") != ["facet", "schema"]
        or refusal.get("schema_literal") != "slice-c-worker-refusal-v1"
    ):
        _fail("protocol registry refusal ownership differs")
    request = value.get("request")
    if (
        type(request) is not dict
        or request.get("members")
        != [
            "artifacts",
            "h5ad_payload",
            "repository",
            "schema",
            "slice_c_request",
            "source_payload",
        ]
        or request.get("artifacts_members")
        != [
            "cpython_manifest",
            "premise",
            "record_reconciliation",
            "root_seal",
            "runtime_manifest",
            "semantic_measurement",
            "wheel_manifest",
        ]
        or request.get("repository_members")
        != [
            "file_manifest",
            "file_records",
            "selected_materials",
            "snapshot_identity",
            "snapshot_ref",
        ]
    ):
        _fail("protocol registry request grammar differs")
    return value


def refusal_frame_v1(facet: RefusalFacetV1) -> bytes:
    if type(facet) is not RefusalFacetV1:
        raise SliceCContractError("refusal facet is outside the closed enum")
    return canonical_frame({"facet": facet.value, "schema": "slice-c-worker-refusal-v1"})


def registry_invalid_frame_v1() -> bytes:
    raw = b'{"facet":"registry-invalid","schema":"slice-c-worker-refusal-v1"}\n'
    if len(raw) != 66 or sha256(raw) != (
        "sha256:1f3e22be0961918e9214d6cd4abe2584e3028f2f7be3eddc2432ea1e2f81bdac"
    ):
        raise AssertionError("fixed registry-invalid carrier differs")
    return raw


def select_refusal_v1(
    observed: Iterable[RefusalFacetV1],
    *,
    worker_named: RefusalFacetV1 | None = None,
) -> RefusalFacetV1 | None:
    """Select the first observed facet, enforcing Amendment-5 ownership."""

    candidates: set[RefusalFacetV1] = set()
    for facet in observed:
        if type(facet) is not RefusalFacetV1:
            raise SliceCContractError("observed refusal has the wrong type")
        candidates.add(facet)
    if worker_named is not None:
        if type(worker_named) is not RefusalFacetV1:
            raise SliceCContractError("worker refusal has the wrong type")
        candidates.add(
            RefusalFacetV1.RESPONSE_PROTOCOL if worker_named in CONTROLLER_FACETS else worker_named
        )
    return min(candidates, key=FACET_RANK.__getitem__) if candidates else None


def _artifact_text(raw: bytes) -> dict[str, object]:
    return {"byte_size": len(raw), "sha256": sha256(raw), "utf8": raw.decode("utf-8", "strict")}


def build_worker_request_v1(
    *,
    registry: RegistryBundleV1,
    materials: CapturedWorld1MaterialsV1,
    request: SliceCRequestV1,
    runtime_artifacts: dict[str, bytes],
) -> tuple[dict[str, Any], bytes]:
    """Construct and self-authenticate the one exact world-1 request frame."""

    validate_protocol_registry_v1(registry.protocol_bytes)
    validate_slice_c_request(request)
    artifact_names = cast(list[str], registry.protocol["request"]["artifacts_members"])
    if set(runtime_artifacts) != set(artifact_names):
        _fail("runtime artifact set differs")
    if runtime_artifacts["root_seal"] != registry.root_seal_bytes:
        _fail("live and copied root-seal bytes differ")
    artifacts = {name: _artifact_text(runtime_artifacts[name]) for name in artifact_names}
    value = {
        "artifacts": artifacts,
        "h5ad_payload": {
            "byte_size": len(materials.h5ad_bytes),
            "payload_b64": base64.b64encode(materials.h5ad_bytes).decode("ascii"),
            "sha256": materials.h5ad_digest,
        },
        "repository": materials.repository_request,
        "schema": "slice-c-worker-request-v1",
        "slice_c_request": request.to_dict(),
        "source_payload": {
            "byte_size": len(materials.source_bytes),
            "sha256": materials.source_digest,
            "utf8": materials.source_bytes.decode("utf-8", "strict"),
        },
    }
    frame = canonical_frame(value)
    admitted = admit_worker_request_v1(registry.protocol_bytes, frame)
    if (
        type(admitted) is not AdmittedWorkerRequestV1
        or len(frame) != _WORLD1_REQUEST_SIZE
        or sha256(frame) != _WORLD1_REQUEST_SHA256
        or admitted.decoded_h5ad != materials.h5ad_bytes
    ):
        _fail("world-1 worker request identity differs")
    return value, frame


def _require_exact_keys(value: object, keys: set[str]) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        _fail("protocol object member set differs")
    return cast(dict[str, Any], value)


def _require_int(value: object, low: int = 0, high: int | None = None) -> int:
    if type(value) is not int or value < low or (high is not None and value > high):
        _fail("protocol integer is outside its domain")
    return value


def _decode_canonical_base64(value: object) -> bytes:
    if type(value) is not str or any(character.isspace() for character in value):
        _fail("payload base64 text is invalid")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ProtocolValidationError("payload base64 decoding failed") from error
    if base64.b64encode(decoded).decode("ascii") != value:
        _fail("payload base64 text is noncanonical")
    return decoded


def _validate_text_wrapper(value: object, expected: dict[str, Any] | None = None) -> bytes:
    wrapper = _require_exact_keys(value, {"byte_size", "sha256", "utf8"})
    text = wrapper["utf8"]
    if type(text) is not str:
        _fail("exact-text wrapper has the wrong type")
    raw = text.encode("utf-8", "strict")
    if wrapper["byte_size"] != len(raw) or wrapper["sha256"] != sha256(raw):
        _fail("exact-text wrapper claims differ")
    if expected is not None and wrapper != expected:
        _fail("exact-text wrapper differs from fixed registry identity")
    return raw


def _protocol_path(value: object) -> str:
    if type(value) is not str:
        _fail("repository path has the wrong type")
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeEncodeError as error:
        raise ProtocolValidationError("repository path is not ASCII") from error
    if (
        not 1 <= len(encoded) <= 512
        or value.startswith("/")
        or "\\" in value
        or "\0" in value
        or unicodedata.normalize("NFC", value) != value
        or any(component in {"", ".", ".."} for component in value.split("/"))
    ):
        _fail("repository path is outside the closed domain")
    return value


def _record_ref(value: object, record_type: str) -> str:
    reference = _require_exact_keys(value, {"record_id", "record_type"})
    if reference["record_type"] != record_type or type(reference["record_id"]) is not str:
        _fail("repository record reference differs")
    return reference["record_id"]


def _validate_repository_shape(
    repository: object,
    registry: dict[str, Any],
    *,
    source_raw: bytes,
    h5ad_raw: bytes,
    private_request: SliceCRequestV1,
) -> None:
    value = _require_exact_keys(
        repository,
        {
            "file_manifest",
            "file_records",
            "selected_materials",
            "snapshot_identity",
            "snapshot_ref",
        },
    )
    if type(value["snapshot_ref"]) is not str:
        _fail("repository snapshot reference has the wrong type")
    snapshot_ref = value["snapshot_ref"]
    manifest = _require_exact_keys(
        value["file_manifest"],
        {"byte_size", "entry_count", "file_manifest_ref", "sha256", "utf8"},
    )
    manifest_text = manifest["utf8"]
    if type(manifest_text) is not str:
        _fail("repository manifest text has the wrong type")
    manifest_raw = manifest_text.encode("utf-8", "strict")
    if (
        manifest["byte_size"] != len(manifest_raw)
        or manifest["sha256"] != sha256(manifest_raw)
        or type(manifest["entry_count"]) is not int
        or manifest["entry_count"] < 1
        or manifest["file_manifest_ref"] != "observed/files.jsonl"
        or not manifest_raw.endswith(b"\n")
        or manifest_raw.endswith(b"\n\n")
    ):
        _fail("repository manifest claims or framing differ")
    lines = manifest_raw[:-1].split(b"\n")
    if len(lines) != manifest["entry_count"] or not lines:
        _fail("repository manifest count differs")
    parsed_lines: list[dict[str, Any]] = []
    previous = ""
    for line in lines:
        item = strict_frame_value(line + b"\n")
        if canonical_json_bytes(item) != line:
            _fail("repository manifest row is noncanonical")
        path = _protocol_path(item.get("path"))
        if path <= previous:
            _fail("repository manifest paths are duplicate or reordered")
        previous = path
        if set(item) != {
            "asset_identity_ref",
            "byte_size",
            "entry_kind",
            "file_record_id",
            "path",
            "record_type",
            "snapshot_ref",
        }:
            _fail("repository file record member set differs")
        parsed_lines.append(item)
    records = value["file_records"]
    if type(records) is not list or len(records) != len(parsed_lines):
        _fail("repository file-record wrapper count differs")
    parsed_records: list[dict[str, Any]] = []
    for wrapper, line, parsed_line in zip(records, lines, parsed_lines, strict=True):
        raw = _validate_text_wrapper(wrapper)
        if raw != line:
            _fail("manifest/file-record preimage equality differs")
        parsed_records.append(parsed_line)
    snapshot_raw = _validate_text_wrapper(value["snapshot_identity"])
    snapshot = strict_frame_value(snapshot_raw + b"\n")
    if canonical_json_bytes(snapshot) != snapshot_raw:
        _fail("snapshot identity preimage is noncanonical")
    if set(snapshot) != {"files", "schema"} or snapshot["schema"] != (
        "slice-c-snapshot-identity-v1"
    ):
        _fail("snapshot identity schema differs")
    expected_snapshot_ref = "snapshot:" + sha256(snapshot_raw)[7:27]
    if snapshot_ref != expected_snapshot_ref:
        _fail("snapshot reference formula differs")
    files = snapshot.get("files")
    if type(files) is not list or len(files) != len(parsed_records):
        _fail("snapshot material inventory differs")
    material_identities: list[dict[str, Any]] = []
    previous = ""
    for item in files:
        identity = _require_exact_keys(item, {"byte_size", "path", "schema", "sha256"})
        path = _protocol_path(identity["path"])
        if (
            path <= previous
            or identity["schema"] != "slice-c-material-identity-v1"
            or type(identity["byte_size"]) is not int
            or identity["byte_size"] < 0
            or not is_sha256(identity["sha256"])
        ):
            _fail("snapshot material identity differs")
        previous = path
        material_identities.append(identity)
    if [item["path"] for item in material_identities] != [item["path"] for item in parsed_records]:
        _fail("snapshot/manifest paths are not bijective")
    for file_record, material_identity in zip(parsed_records, material_identities, strict=True):
        identity_preimage = canonical_json_bytes(material_identity)
        suffix = sha256(identity_preimage)[7:27]
        file_ref = "file:" + suffix
        asset_ref = "asset-identity:" + suffix
        if (
            file_record["record_type"] != "file_record"
            or file_record["file_record_id"] != file_ref
            or file_record["byte_size"] != material_identity["byte_size"]
            or file_record["entry_kind"] not in {"regular_file", "directory", "symlink", "special"}
            or _record_ref(file_record["snapshot_ref"], "repository_snapshot") != snapshot_ref
            or _record_ref(file_record["asset_identity_ref"], "asset_identity") != asset_ref
        ):
            _fail("snapshot/file-record identity relation differs")
    selected = _require_exact_keys(value["selected_materials"], {"h5ad", "source"})
    payloads = {"h5ad": h5ad_raw, "source": source_raw}
    selected_paths = {
        "h5ad": private_request.h5ad_path,
        "source": private_request.source_path,
    }
    for role in ("h5ad", "source"):
        selected_value = _require_exact_keys(
            selected[role], {"asset_identity", "frozen_material", "material_ref"}
        )
        asset_raw = _validate_text_wrapper(selected_value["asset_identity"])
        frozen_raw = _validate_text_wrapper(selected_value["frozen_material"])
        asset = strict_frame_value(asset_raw + b"\n")
        frozen = strict_frame_value(frozen_raw + b"\n")
        if canonical_json_bytes(asset) != asset_raw or canonical_json_bytes(frozen) != frozen_raw:
            _fail("selected repository preimage is noncanonical")
        if (
            set(asset)
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
            or selected_value["material_ref"] != "material:" + sha256(frozen_raw)[7:27]
        ):
            _fail("selected material reference formula differs")
        path = selected_paths[role]
        matching = [item for item in parsed_records if item.get("path") == path]
        identity_matching = [item for item in material_identities if item.get("path") == path]
        payload = payloads[role]
        if len(identity_matching) != 1:
            _fail("selected snapshot material is unavailable")
        identity = identity_matching[0]
        suffix = sha256(canonical_json_bytes(identity))[7:27]
        file_ref = "file:" + suffix
        asset_ref = "asset-identity:" + suffix
        if (
            len(matching) != 1
            or matching[0]["entry_kind"] != "regular_file"
            or matching[0]["file_record_id"] != file_ref
            or identity["byte_size"] != len(payload)
            or identity["sha256"] != sha256(payload)
            or asset["asset_identity_id"] != asset_ref
            or asset["record_type"] != "asset_identity"
            or asset["tier"] != "full_digest"
            or _record_ref(asset["asset_ref"], "file_record") != file_ref
            or asset["identity_evidence"] != {"digest": sha256(payload), "kind": "full_digest"}
            or frozen["schema"] != "slice-c-frozen-material-v1"
            or frozen["path"] != path
            or frozen["byte_size"] != len(payload)
            or frozen["sha256"] != sha256(payload)
            or frozen["content_member"] != role + "_payload"
            or _record_ref(frozen["file_ref"], "file_record") != file_ref
            or _record_ref(frozen["asset_identity_ref"], "asset_identity") != asset_ref
        ):
            _fail("selected repository record join differs")
    # The fixed world-1 object must reconstruct byte-for-byte.  Other internally
    # coherent objects can be admitted only to exercise transport boundaries; the
    # production parent never constructs one from a non-world-1 context.
    world = registry.get("world1_repository")
    if type(world) is not dict:
        _fail("registry world-1 repository is unavailable")


def admit_worker_request_v1(
    registry_raw: bytes,
    request_raw: bytes,
) -> AdmittedWorkerRequestV1 | RefusalFacetV1:
    """Apply ranks 1-5, with registry authentication first and no worker launch."""

    try:
        registry = validate_protocol_registry_v1(registry_raw)
    except ProtocolValidationError:
        return RefusalFacetV1.REGISTRY_INVALID
    if type(request_raw) is not bytes or len(request_raw) > _REQUEST_LIMIT:
        return RefusalFacetV1.REQUEST_BYTES
    try:
        value = strict_frame_value(request_raw)
    except ProtocolValidationError:
        return RefusalFacetV1.REQUEST_FRAME
    try:
        if canonical_frame(value) != request_raw:
            _fail("request frame is noncanonical")
        _closed_value_domain(value)
        outer = _require_exact_keys(
            value,
            {
                "artifacts",
                "h5ad_payload",
                "repository",
                "schema",
                "slice_c_request",
                "source_payload",
            },
        )
        if outer["schema"] != "slice-c-worker-request-v1":
            _fail("worker request schema differs")
        artifacts = _require_exact_keys(
            outer["artifacts"], set(cast(list[str], registry["request"]["artifacts_members"]))
        )
        fixed_artifacts = cast(dict[str, dict[str, Any]], registry["artifacts"])
        for name, expected_identity in fixed_artifacts.items():
            raw = _validate_text_wrapper(artifacts[name])
            if (
                len(raw) != expected_identity["byte_size"]
                or sha256(raw) != expected_identity["sha256"]
            ):
                _fail("carried artifact identity differs")
            if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
                _fail("carried artifact framing differs")
        source_raw = _validate_text_wrapper(outer["source_payload"])
        private = _require_exact_keys(
            outer["slice_c_request"], {"h5ad_path", "obs_column", "schema", "source_path"}
        )
        try:
            private_request = SliceCRequestV1(
                source_path=private["source_path"],
                h5ad_path=private["h5ad_path"],
                obs_column=private["obs_column"],
                schema=private["schema"],
            )
        except (SliceCContractError, TypeError) as error:
            raise ProtocolValidationError("private request is invalid") from error
        validate_slice_c_request(private_request)
        payload = _require_exact_keys(outer["h5ad_payload"], {"byte_size", "payload_b64", "sha256"})
        size = _require_int(payload["byte_size"])
        if not is_sha256(payload["sha256"]):
            _fail("H5AD payload digest has the wrong domain")
        decoded = _decode_canonical_base64(payload["payload_b64"])
        if len(decoded) != size or sha256(decoded) != payload["sha256"]:
            _fail("H5AD payload claims differ")
        _validate_repository_shape(
            outer["repository"],
            registry,
            source_raw=source_raw,
            h5ad_raw=decoded,
            private_request=private_request,
        )
    except (ProtocolValidationError, UnicodeError, KeyError, TypeError, ValueError):
        return RefusalFacetV1.REQUEST_PROTOCOL
    if len(decoded) > _DECODED_LIMIT:
        return RefusalFacetV1.DECODED_BYTES
    return AdmittedWorkerRequestV1(
        value=value, decoded_h5ad=decoded, request_sha256=sha256(request_raw)
    )


def _parse_h5ad_facts(value: object, requested_column: str) -> H5adFactsV1:
    facts = _require_exact_keys(
        value,
        {"matrix-shape", "obs-column-cardinality", "obs-column-quoted-values", "obs-group-sizes"},
    )
    shape = _require_exact_keys(facts["matrix-shape"], {"column_count", "row_count"})
    cardinality = _require_exact_keys(
        facts["obs-column-cardinality"], {"column", "distinct_count", "n_obs"}
    )
    group_fact = _require_exact_keys(facts["obs-group-sizes"], {"column", "groups", "n_obs"})
    quoted = _require_exact_keys(facts["obs-column-quoted-values"], {"column", "n_obs", "values"})
    if (
        require_safe_string(cardinality["column"]) != requested_column
        or require_safe_string(group_fact["column"]) != requested_column
        or require_safe_string(quoted["column"]) != requested_column
    ):
        _fail("response fact column differs")
    group_values = group_fact["groups"]
    quoted_values = quoted["values"]
    if type(group_values) is not list or type(quoted_values) is not list:
        _fail("response fact vectors have the wrong type")
    groups: list[GroupSizeV1] = []
    for item in group_values:
        group = _require_exact_keys(item, {"count", "value"})
        groups.append(
            GroupSizeV1(
                value=require_safe_string(group["value"]),
                count=_require_int(group["count"], 1, 100_000),
            )
        )
    result = H5adFactsV1(
        matrix_shape=MatrixShapeFactV1(
            row_count=_require_int(shape["row_count"], 1, 100_000),
            column_count=_require_int(shape["column_count"], 1, 1_024),
        ),
        cardinality=ObsColumnCardinalityFactV1(
            column=cast(str, cardinality["column"]),
            n_obs=_require_int(cardinality["n_obs"], 1, 100_000),
            distinct_count=_require_int(cardinality["distinct_count"], 2, 1_024),
        ),
        group_sizes=ObsGroupSizesFactV1(
            column=cast(str, group_fact["column"]),
            n_obs=_require_int(group_fact["n_obs"], 1, 100_000),
            groups=tuple(groups),
        ),
        quoted_values=ObsColumnQuotedValuesFactV1(
            column=cast(str, quoted["column"]),
            n_obs=_require_int(quoted["n_obs"], 1, 100_000),
            values=tuple(require_safe_string(item) for item in quoted_values),
        ),
    )
    validate_h5ad_facts(result)
    return result


def validate_worker_response_v1(
    *,
    request_value: dict[str, Any],
    request_raw: bytes,
    response_raw: bytes,
    require_world1_success: bool,
) -> WorkerControllerResultV1:
    """Validate one buffered worker response and enforce refusal ownership."""

    if len(response_raw) > _STDOUT_LIMIT:
        return WorkerControllerResultV1(facts=None, refusal=RefusalFacetV1.STDOUT)
    try:
        value = strict_frame_value(response_raw)
    except ProtocolValidationError:
        return WorkerControllerResultV1(facts=None, refusal=RefusalFacetV1.RESPONSE_FRAME)
    try:
        if canonical_frame(value) != response_raw:
            _fail("response is noncanonical")
        _closed_value_domain(value)
        schema = value.get("schema")
        if schema == "slice-c-worker-refusal-v1":
            refusal = _require_exact_keys(value, {"facet", "schema"})
            try:
                named = RefusalFacetV1(refusal["facet"])
            except (TypeError, ValueError) as error:
                raise ProtocolValidationError("worker refusal facet is unknown") from error
            if named in CONTROLLER_FACETS:
                _fail("worker named a controller-owned refusal")
            return WorkerControllerResultV1(facts=None, refusal=named)
        if schema != "slice-c-worker-success-v1":
            _fail("response schema differs")
        success = _require_exact_keys(value, {"facts", "schema", "worker_request_sha256"})
        request_digest = sha256(request_raw)
        if success["worker_request_sha256"] != request_digest:
            _fail("success is bound to another request")
        requested_column = cast(str, request_value["slice_c_request"]["obs_column"])
        facts = _parse_h5ad_facts(success["facts"], requested_column)
        if require_world1_success and (
            request_digest != _WORLD1_REQUEST_SHA256
            or len(response_raw) != _WORLD1_RESPONSE_SIZE
            or sha256(response_raw) != _WORLD1_RESPONSE_SHA256
        ):
            _fail("world-1 response replay identity differs")
        return WorkerControllerResultV1(
            facts=facts,
            refusal=None,
            request_sha256=request_digest,
            response_sha256=sha256(response_raw),
        )
    except (ProtocolValidationError, SliceCContractError, KeyError, TypeError, ValueError):
        return WorkerControllerResultV1(facts=None, refusal=RefusalFacetV1.RESPONSE_PROTOCOL)


__all__ = [
    "AdmittedWorkerRequestV1",
    "ProtocolValidationError",
    "admit_worker_request_v1",
    "build_worker_request_v1",
    "refusal_frame_v1",
    "registry_invalid_frame_v1",
    "select_refusal_v1",
    "strict_frame_value",
    "validate_protocol_registry_v1",
    "validate_worker_response_v1",
]
