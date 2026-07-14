"""Conservative cross-step artifact identity and reaching-writer resolution."""
from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch


@dataclass(frozen=True)
class ArtifactId:
    manifest_path: str
    logical_role: str
    format: str
    schema_digest: str
    content_digest: str


@dataclass(frozen=True)
class SerializerContract:
    contract_id: str
    format: str
    version: str
    digest: str


@dataclass(frozen=True)
class ArtifactWrite:
    write_id: str
    artifact: ArtifactId
    path: str
    serializer: SerializerContract
    fields: tuple[str, ...]
    schema_digest: str
    content_digest: str
    mode: str
    workflow_index: int
    exact_path: bool = True
    possible_mutation: bool = False


@dataclass(frozen=True)
class ArtifactRead:
    read_id: str
    artifact: ArtifactId
    path: str
    deserializer: SerializerContract
    field: str
    expected_schema_digest: str
    expected_content_digest: str
    workflow_index: int
    exact_path: bool = True


@dataclass(frozen=True)
class UnknownArtifactProducer:
    read_id: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ArtifactResolution:
    possible_producers: frozenset[ArtifactWrite]
    must_producer: ArtifactWrite | None
    unknown_producer: UnknownArtifactProducer | None
    obligations: tuple[str, ...]


@dataclass(frozen=True)
class ArtifactState:
    writes: tuple[ArtifactWrite, ...] = ()


def _could_name_same_path(read: ArtifactRead, write: ArtifactWrite) -> bool:
    if not read.exact_path or not write.exact_path:
        return fnmatch(write.path, read.path) or fnmatch(read.path, write.path) or True
    return read.path == write.path


def resolve_artifact_flow(read: ArtifactRead, state: ArtifactState) -> ArtifactResolution:
    """Return a must writer only when every §3.7 premise is exact.

    Ambiguity is never resolved by matching a path or field name. All path-compatible writers remain
    possible and an explicit unknown producer records the unresolved remainder.
    """
    before_read = tuple(write for write in state.writes if write.workflow_index < read.workflow_index)
    possible = frozenset(write for write in before_read if _could_name_same_path(read, write))
    matching_identity = tuple(write for write in possible if write.artifact == read.artifact)
    reasons: list[str] = []

    if not read.exact_path or any(token in read.path for token in ("*", "?", "[")):
        reasons.append("dynamic_or_glob_path")
    if len(matching_identity) != 1:
        reasons.append("writer_not_unique")
    writer = matching_identity[0] if len(matching_identity) == 1 else None
    if writer is not None:
        if not writer.exact_path or writer.path != read.path:
            reasons.append("writer_path_unresolved")
        if writer.serializer != read.deserializer:
            reasons.append("serializer_deserializer_mismatch")
        if writer.artifact.format != read.deserializer.format:
            reasons.append("format_mismatch")
        if read.field not in writer.fields:
            reasons.append("field_correspondence_unproved")
        if (writer.schema_digest != read.expected_schema_digest
                or writer.artifact.schema_digest != read.expected_schema_digest):
            reasons.append("schema_digest_mismatch")
        if (writer.content_digest != read.expected_content_digest
                or writer.artifact.content_digest != read.expected_content_digest):
            reasons.append("content_digest_mismatch")
        if writer.mode != "write":
            reasons.append("non_replacing_write_mode")
        if writer.possible_mutation:
            reasons.append("possible_in_place_mutation")
        later = tuple(candidate for candidate in possible
                      if candidate.write_id != writer.write_id
                      and candidate.workflow_index > writer.workflow_index)
        if later:
            reasons.append("possible_intervening_writer")
        # A distinct artifact identity at the same path means path reuse/collision, even if its write
        # precedes the selected writer. The content reached by the read is no longer uniquely named.
        if any(candidate.artifact != read.artifact for candidate in possible):
            reasons.append("same_path_unrelated_artifact")
    elif not possible:
        reasons.append("no_reaching_writer")

    unique_reasons = tuple(dict.fromkeys(reasons))
    if writer is not None and not unique_reasons:
        return ArtifactResolution(possible, writer, None, ())
    unknown = UnknownArtifactProducer(read.read_id, unique_reasons or ("artifact_resolution_incomplete",))
    return ArtifactResolution(possible, None, unknown, unknown.reasons)

