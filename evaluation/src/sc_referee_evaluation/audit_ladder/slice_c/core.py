"""Closed scalar, request, fact, and outcome values for Slice C."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final, TypeAlias, final

_SHA256_RE: Final = re.compile(r"sha256:[0-9a-f]{64}\Z")
_REQUEST_SCHEMA: Final = "slice-c-request-v1"


class SliceCContractError(ValueError):
    """A caller-controlled value escaped the closed Slice-C contract."""


def canonical_json_bytes(value: Any) -> bytes:
    """Return the sole compact UTF-8 JSON preimage, without an LF."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8", "strict")


def canonical_frame(value: Any) -> bytes:
    """Return the sole protocol/artifact frame."""

    return canonical_json_bytes(value) + b"\n"


def sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def is_sha256(value: object) -> bool:
    return type(value) is str and _SHA256_RE.fullmatch(value) is not None


def require_safe_string(value: object, *, maximum: int = 1_024) -> str:
    if type(value) is not str:
        raise SliceCContractError("safe string has the wrong type")
    try:
        encoded = value.encode("utf-8", "strict")
    except UnicodeEncodeError as error:
        raise SliceCContractError("safe string is not strict UTF-8") from error
    if (
        len(encoded) > maximum
        or unicodedata.normalize("NFC", value) != value
        or any(
            unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for character in value
        )
    ):
        raise SliceCContractError("safe string is outside the closed language")
    return value


def _require_relative_ascii(value: object) -> str:
    if type(value) is not str:
        raise SliceCContractError("request path has the wrong type")
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeEncodeError as error:
        raise SliceCContractError("request path is not ASCII") from error
    components = value.split("/")
    if (
        not 1 <= len(encoded) <= 512
        or value.startswith("/")
        or "\\" in value
        or "\0" in value
        or unicodedata.normalize("NFC", value) != value
        or any(component in {"", ".", ".."} for component in components)
    ):
        raise SliceCContractError("request path is outside the closed domain")
    return value


@final
@dataclass(frozen=True, slots=True)
class SliceCRequestV1:
    """The only caller-supplied Slice-C value."""

    source_path: str
    h5ad_path: str
    obs_column: str
    schema: str = _REQUEST_SCHEMA

    def __post_init__(self) -> None:
        validate_slice_c_request(self)

    def to_dict(self) -> dict[str, str]:
        validate_slice_c_request(self)
        return {
            "h5ad_path": self.h5ad_path,
            "obs_column": self.obs_column,
            "schema": self.schema,
            "source_path": self.source_path,
        }


def validate_slice_c_request(request: SliceCRequestV1) -> None:
    if type(request) is not SliceCRequestV1:
        raise SliceCContractError("request is not the exact closed request type")
    if type(request.schema) is not str or request.schema != _REQUEST_SCHEMA:
        raise SliceCContractError("request schema differs")
    source_path = _require_relative_ascii(request.source_path)
    h5ad_path = _require_relative_ascii(request.h5ad_path)
    if source_path == h5ad_path:
        raise SliceCContractError("request paths must differ")
    if type(request.obs_column) is not str:
        raise SliceCContractError("observation column has the wrong type")
    try:
        encoded = request.obs_column.encode("ascii", "strict")
    except UnicodeEncodeError as error:
        raise SliceCContractError("observation column is not ASCII") from error
    if (
        not 1 <= len(encoded) <= 512
        or unicodedata.normalize("NFC", request.obs_column) != request.obs_column
    ):
        raise SliceCContractError("observation column is outside the closed domain")


class RefusalFacetV1(StrEnum):
    REGISTRY_INVALID = "registry-invalid"
    REQUEST_BYTES = "request-bytes"
    REQUEST_FRAME = "request-frame"
    REQUEST_PROTOCOL = "request-protocol"
    DECODED_BYTES = "decoded-bytes"
    CPU = "cpu"
    WALL = "wall"
    RSS = "rss"
    STDOUT = "stdout"
    STDERR = "stderr"
    NOFILE = "nofile"
    FSIZE = "fsize"
    CORE = "core"
    PROCESS_STATUS = "process-status"
    RESPONSE_FRAME = "response-frame"
    RESPONSE_PROTOCOL = "response-protocol"
    POST_RUN_IDENTITY = "post-run-identity"
    ARTIFACT_AUTHENTICATION = "artifact-authentication"
    INVENTORY_IDENTITY = "inventory-identity"
    PRIVATE_REQUEST = "private-request"
    H5AD_PAYLOAD_AUTHENTICATION = "h5ad-payload-authentication"
    RUNTIME_IDENTITY = "runtime-identity"
    H5AD_SEMANTICS_NOT_CLOSED = "h5ad-semantics-not-closed"
    WORKER_INTERNAL = "worker-internal"


CONTROLLER_FACETS: Final = tuple(
    RefusalFacetV1(item)
    for item in (
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
    )
)
WORKER_FACETS: Final = tuple(
    RefusalFacetV1(item)
    for item in (
        "artifact-authentication",
        "inventory-identity",
        "private-request",
        "h5ad-payload-authentication",
        "runtime-identity",
        "h5ad-semantics-not-closed",
        "worker-internal",
    )
)
ALL_FACETS: Final = CONTROLLER_FACETS + WORKER_FACETS
FACET_RANK: Final = {facet: index for index, facet in enumerate(ALL_FACETS)}


@final
@dataclass(frozen=True, slots=True)
class MatrixShapeFactV1:
    row_count: int
    column_count: int

    def to_dict(self) -> dict[str, int]:
        return {"column_count": self.column_count, "row_count": self.row_count}


@final
@dataclass(frozen=True, slots=True)
class ObsColumnCardinalityFactV1:
    column: str
    n_obs: int
    distinct_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {"column": self.column, "distinct_count": self.distinct_count, "n_obs": self.n_obs}


@final
@dataclass(frozen=True, slots=True)
class GroupSizeV1:
    value: str
    count: int

    def to_dict(self) -> dict[str, int | str]:
        return {"count": self.count, "value": self.value}


@final
@dataclass(frozen=True, slots=True)
class ObsGroupSizesFactV1:
    column: str
    n_obs: int
    groups: tuple[GroupSizeV1, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "column": self.column,
            "groups": [group.to_dict() for group in self.groups],
            "n_obs": self.n_obs,
        }


@final
@dataclass(frozen=True, slots=True)
class ObsColumnQuotedValuesFactV1:
    column: str
    n_obs: int
    values: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"column": self.column, "n_obs": self.n_obs, "values": list(self.values)}


@final
@dataclass(frozen=True, slots=True)
class H5adFactsV1:
    matrix_shape: MatrixShapeFactV1
    cardinality: ObsColumnCardinalityFactV1
    group_sizes: ObsGroupSizesFactV1
    quoted_values: ObsColumnQuotedValuesFactV1

    def to_dict(self) -> dict[str, object]:
        return {
            "matrix-shape": self.matrix_shape.to_dict(),
            "obs-column-cardinality": self.cardinality.to_dict(),
            "obs-column-quoted-values": self.quoted_values.to_dict(),
            "obs-group-sizes": self.group_sizes.to_dict(),
        }


@final
@dataclass(frozen=True, slots=True)
class WorkerControllerResultV1:
    """Exactly one authenticated fact bundle or one closed refusal."""

    facts: H5adFactsV1 | None
    refusal: RefusalFacetV1 | None
    request_sha256: str | None = None
    response_sha256: str | None = None

    def __post_init__(self) -> None:
        if type(self) is not WorkerControllerResultV1 or (self.facts is None) == (
            self.refusal is None
        ):
            raise SliceCContractError("worker result must contain exactly one closed outcome")
        if self.facts is not None:
            validate_h5ad_facts(self.facts)
            if not is_sha256(self.request_sha256) or not is_sha256(self.response_sha256):
                raise SliceCContractError("successful worker result lacks frame identities")
        elif (
            type(self.refusal) is not RefusalFacetV1
            or self.request_sha256 is not None
            or self.response_sha256 is not None
        ):
            raise SliceCContractError("refusal result carries non-refusal state")


def _bounded_int(value: object, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high


def validate_h5ad_facts(facts: H5adFactsV1) -> None:
    if type(facts) is not H5adFactsV1:
        raise SliceCContractError("fact bundle has the wrong type")
    shape = facts.matrix_shape
    cardinality = facts.cardinality
    groups = facts.group_sizes
    quoted = facts.quoted_values
    if (
        type(shape) is not MatrixShapeFactV1
        or not _bounded_int(shape.row_count, 1, 100_000)
        or not _bounded_int(shape.column_count, 1, 1_024)
        or type(cardinality) is not ObsColumnCardinalityFactV1
        or type(groups) is not ObsGroupSizesFactV1
        or type(quoted) is not ObsColumnQuotedValuesFactV1
    ):
        raise SliceCContractError("fact bundle dimensions are invalid")
    columns = (
        require_safe_string(cardinality.column),
        require_safe_string(groups.column),
        require_safe_string(quoted.column),
    )
    if len(set(columns)) != 1:
        raise SliceCContractError("fact columns differ")
    if (
        not _bounded_int(cardinality.n_obs, 1, 100_000)
        or not _bounded_int(groups.n_obs, 1, 100_000)
        or not _bounded_int(quoted.n_obs, 1, 100_000)
        or shape.row_count != cardinality.n_obs
        or shape.row_count != groups.n_obs
        or shape.row_count != quoted.n_obs
        or not _bounded_int(cardinality.distinct_count, 2, 1_024)
        or type(groups.groups) is not tuple
        or len(groups.groups) != cardinality.distinct_count
        or type(quoted.values) is not tuple
        or len(quoted.values) != quoted.n_obs
    ):
        raise SliceCContractError("fact row/cardinality algebra is invalid")
    group_values: list[str] = []
    group_counts: dict[str, int] = {}
    for group in groups.groups:
        if type(group) is not GroupSizeV1 or not _bounded_int(group.count, 1, 100_000):
            raise SliceCContractError("group fact is invalid")
        value = require_safe_string(group.value)
        if value in group_counts:
            raise SliceCContractError("group values are not distinct")
        group_values.append(value)
        group_counts[value] = group.count
    if (
        group_values != sorted(group_values, key=canonical_json_bytes)
        or sum(group_counts.values()) != groups.n_obs
    ):
        raise SliceCContractError("group ordering or total is invalid")
    counts: dict[str, int] = {}
    total_quoted_bytes = 0
    for value in quoted.values:
        safe = require_safe_string(value)
        total_quoted_bytes += len(safe.encode("utf-8"))
        counts[safe] = counts.get(safe, 0) + 1
    if counts != group_counts or total_quoted_bytes > 4_194_304:
        raise SliceCContractError("quoted values disagree with group facts")


FactV1: TypeAlias = (
    MatrixShapeFactV1
    | ObsColumnCardinalityFactV1
    | ObsGroupSizesFactV1
    | ObsColumnQuotedValuesFactV1
)


__all__ = [
    "ALL_FACETS",
    "CONTROLLER_FACETS",
    "FACET_RANK",
    "WORKER_FACETS",
    "GroupSizeV1",
    "H5adFactsV1",
    "MatrixShapeFactV1",
    "ObsColumnCardinalityFactV1",
    "ObsColumnQuotedValuesFactV1",
    "ObsGroupSizesFactV1",
    "RefusalFacetV1",
    "SliceCContractError",
    "SliceCRequestV1",
    "WorkerControllerResultV1",
    "canonical_frame",
    "canonical_json_bytes",
    "is_sha256",
    "require_safe_string",
    "sha256",
    "validate_h5ad_facts",
    "validate_slice_c_request",
]
