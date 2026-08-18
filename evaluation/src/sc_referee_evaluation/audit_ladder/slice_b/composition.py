"""Independent Slice-B CSV composition and post-report answer disposition.

The composition path deliberately does not import a primary verifier.  It reparses
the retained frozen preimages, reconstructs all four renderer observations, and
compares them with the primary records before applying the sole question rule.

Answer-tree normalization is a separate post-report operation.  No answer value is
accepted by, or flows into, the composition or renderer interfaces.
"""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Literal, cast

from sc_referee.controller import (
    FrozenFileManifestInput,
    ManifestBoundFrozenInspectionContext,
)
from sc_referee.core.ids import canonical_json
from sc_referee.scientific_checks.core import FrozenBaseRecord, FrozenMaterialInput, RecordRef
from sc_referee_evaluation.audit_ladder.slice_b.renderer import (
    CsvComparisonGroupSizesObservationV1,
    CsvSelectedCardinalitiesObservationV1,
    CsvTableShapeObservationV1,
    CsvUnitComparisonIncidenceObservationV1,
    SliceBObservationSetV1,
    SliceBPrimaryRefusalReasonV1,
    SliceBQuestionRenderIRV1,
)

_HASH_PATTERN: Final = re.compile(r"sha256:[0-9a-f]{64}\Z", flags=re.ASCII)
_OBSERVATION_VERSION: Final = "slice-b-observation-v1"
_MAX_CSV_BYTES: Final = 1_048_576
_MAX_DATA_ROWS: Final = 100_000
_MAX_COLUMNS: Final = 64
_MAX_FIELD_BYTES: Final = 256
_MAX_SCOPE_PATHS: Final = 8

_QUESTION_RULE_ID: Final = "csv-repeated-candidate-across-comparison-question-v1"
_QUESTION_TEMPLATE_ID: Final = "slice-b-csv-question-block-v3"
_ANSWER_DOMAIN_ID: Final = "slice-b-used-unit-conclusion-comparison-dependence-answer-tree-v1"
_UNRESOLVED_CONSEQUENCE_ID: Final = "slice-b-scientific-conclusion-support-unresolved-v1"
_SCOPE_PROFILE: Final = "slice-b-explicit-material-input-selection-v1"


class SliceBCompositionContractError(ValueError):
    """The caller did not supply the closed Slice-B composition interface."""


class SliceBAnswerTreeContractError(ValueError):
    """The raw answer tuple is outside the closed Section-14 domain."""


class SliceBCompositionDispositionV1(StrEnum):
    """Closed outcomes needed to populate the seeded renderer interface."""

    QUESTION = "question"
    NO_QUESTION = "no-question"
    QUESTION_SCOPE_UNRESOLVED = "slice-b-question-scope-unresolved"
    OBSERVATION_REDERIVATION_MISMATCH = "slice-b-observation-rederivation-mismatch"


@dataclass(frozen=True, slots=True)
class SliceBCompositionResultV1:
    """One closed composition result, expressed in renderer-native record types."""

    disposition: SliceBCompositionDispositionV1
    observations: SliceBObservationSetV1 | None
    question: SliceBQuestionRenderIRV1 | None
    primary_refusal: SliceBPrimaryRefusalReasonV1 | None
    question_scope_unresolved: bool

    def __post_init__(self) -> None:
        if type(self.disposition) is not SliceBCompositionDispositionV1:
            raise SliceBCompositionContractError("composition disposition is not closed")
        if type(self.question_scope_unresolved) is not bool:
            raise SliceBCompositionContractError("composition scope flag is not closed")

        has_observations = _is_exact_observation_tuple(self.observations)
        if self.disposition is SliceBCompositionDispositionV1.QUESTION:
            legal = (
                has_observations
                and type(self.question) is SliceBQuestionRenderIRV1
                and self.primary_refusal is None
                and not self.question_scope_unresolved
            )
        elif self.disposition is SliceBCompositionDispositionV1.NO_QUESTION:
            legal = (
                has_observations
                and self.question is None
                and self.primary_refusal is None
                and not self.question_scope_unresolved
            )
        elif self.disposition is SliceBCompositionDispositionV1.QUESTION_SCOPE_UNRESOLVED:
            legal = (
                has_observations
                and self.question is None
                and self.primary_refusal is None
                and self.question_scope_unresolved
            )
        else:
            legal = (
                self.observations is None
                and self.question is None
                and self.primary_refusal
                is SliceBPrimaryRefusalReasonV1.OBSERVATION_REDERIVATION_MISMATCH
                and not self.question_scope_unresolved
            )
        if not legal:
            raise SliceBCompositionContractError("composition result fields conflict")


SliceBAnswerTokenV1 = Literal["yes", "no", "unknown", "not-applicable"]
SliceBAnswerTupleV1 = tuple[
    SliceBAnswerTokenV1,
    SliceBAnswerTokenV1,
    SliceBAnswerTokenV1,
    SliceBAnswerTokenV1,
]


class SliceBAnswerDispositionV1(StrEnum):
    """Closed post-report dispositions from binding memo Section 14.1."""

    RESOLVED_INAPPLICABLE = "resolved-inapplicable"
    RETAINS_MATERIAL_QUESTION = "retains-material-question"
    RESOLVED_DEPENDENCE_ACCOUNTED = "resolved-dependence-accounted"
    REQUIRES_FURTHER_EVIDENCE = "requires-further-evidence"


@dataclass(frozen=True, slots=True)
class SliceBAnswerTreeResolutionV1:
    """Normalized answers and their one deterministic post-report disposition."""

    normalized_answers: SliceBAnswerTupleV1
    disposition: SliceBAnswerDispositionV1

    def __post_init__(self) -> None:
        answers = _require_raw_answer_tuple(self.normalized_answers)
        if type(self.disposition) is not SliceBAnswerDispositionV1:
            raise SliceBAnswerTreeContractError("answer disposition is not closed")
        for index, answer in enumerate(answers):
            if answer == "not-applicable" and "no" not in answers[:index]:
                raise SliceBAnswerTreeContractError(
                    "normalized not-applicable requires an earlier no"
                )
        first_no = next((index for index in range(3) if answers[index] == "no"), None)
        if first_no is not None:
            expected = (
                SliceBAnswerDispositionV1.RESOLVED_INAPPLICABLE
                if answers[first_no + 1 :] == ("not-applicable",) * (3 - first_no)
                else None
            )
        elif "unknown" in answers[:3]:
            expected = SliceBAnswerDispositionV1.RETAINS_MATERIAL_QUESTION
        elif answers[3] == "yes":
            expected = SliceBAnswerDispositionV1.RESOLVED_DEPENDENCE_ACCOUNTED
        elif answers[3] == "no":
            expected = SliceBAnswerDispositionV1.REQUIRES_FURTHER_EVIDENCE
        elif answers[3] == "unknown":
            expected = SliceBAnswerDispositionV1.RETAINS_MATERIAL_QUESTION
        else:
            expected = None
        if self.disposition is not expected:
            raise SliceBAnswerTreeContractError("normalized answers and disposition conflict")


@dataclass(frozen=True, slots=True)
class _SelectedFrozenCsvV1:
    snapshot_record: FrozenBaseRecord
    selected_file_record: FrozenBaseRecord
    selected_identity_record: FrozenBaseRecord
    material: FrozenMaterialInput
    content_digest: str


@dataclass(frozen=True, slots=True)
class _CsvFactsV1:
    data_row_count: int
    column_count: int
    candidate_unit_distinct_count: int
    comparison_distinct_count: int
    sorted_group_sizes: tuple[int, ...]
    repeated_candidate_value_count: int
    cross_comparison_candidate_value_count: int
    comparison_values_per_candidate_histogram: tuple[tuple[int, int], ...]


def compose_slice_b_question_v1(
    *,
    context: ManifestBoundFrozenInspectionContext,
    selected_path: str,
    candidate_unit_column_index: int,
    comparison_column_index: int,
    primary_observations: object,
) -> SliceBCompositionResultV1:
    """Independently validate and apply the sole Slice-B question rule.

    Invalid request scalars are caller contract errors.  Any inability to replay the
    selected bytes or match all four primary records is the renderer's existing
    observation-rederivation primary refusal.  Valid observations with unresolved
    explicit material-input selection retain the observations and select exactly the
    secondary scope Coverage disposition.
    """

    _require_composition_request(
        context=context,
        selected_path=selected_path,
        candidate_unit_column_index=candidate_unit_column_index,
        comparison_column_index=comparison_column_index,
    )

    try:
        selected = _validate_selected_frozen_csv(context, selected_path)
        table = _parse_csv_bytes(selected.material.content)
        facts = _derive_csv_facts(
            table,
            candidate_unit_column_index=candidate_unit_column_index,
            comparison_column_index=comparison_column_index,
        )
    except _CompositionReplayError:
        return _rederivation_mismatch()

    scope_digest = _derive_review_scope_digest(context, selected_path)
    expected = _derive_observations(
        context=context,
        selected=selected,
        facts=facts,
        candidate_unit_column_index=candidate_unit_column_index,
        comparison_column_index=comparison_column_index,
        review_scope_selection_evidence_digest=(
            scope_digest if scope_digest is not None else "unresolved"
        ),
    )
    if not _primary_observations_match(primary_observations, expected):
        return _rederivation_mismatch()

    if scope_digest is None:
        return SliceBCompositionResultV1(
            disposition=SliceBCompositionDispositionV1.QUESTION_SCOPE_UNRESOLVED,
            observations=expected,
            question=None,
            primary_refusal=None,
            question_scope_unresolved=True,
        )

    if not _question_predicate(facts):
        return SliceBCompositionResultV1(
            disposition=SliceBCompositionDispositionV1.NO_QUESTION,
            observations=expected,
            question=None,
            primary_refusal=None,
            question_scope_unresolved=False,
        )

    question = _derive_question(expected, scope_digest)
    return SliceBCompositionResultV1(
        disposition=SliceBCompositionDispositionV1.QUESTION,
        observations=expected,
        question=question,
        primary_refusal=None,
        question_scope_unresolved=False,
    )


def resolve_slice_b_answer_tree_v1(raw_answers: object) -> SliceBAnswerTreeResolutionV1:
    """Normalize one legal raw answer tuple with Section-14 first-``no`` precedence.

    This post-report function is intentionally not called by the composition path.
    """

    answers = _require_raw_answer_tuple(raw_answers)
    for index, answer in enumerate(answers):
        if answer == "not-applicable" and "no" not in answers[:index]:
            raise SliceBAnswerTreeContractError("not-applicable requires a raw earlier no")

    for index in range(3):
        if answers[index] == "no":
            normalized = cast(
                SliceBAnswerTupleV1,
                answers[: index + 1] + ("not-applicable",) * (3 - index),
            )
            return SliceBAnswerTreeResolutionV1(
                normalized_answers=normalized,
                disposition=SliceBAnswerDispositionV1.RESOLVED_INAPPLICABLE,
            )

    if "unknown" in answers[:3]:
        return SliceBAnswerTreeResolutionV1(
            normalized_answers=answers,
            disposition=SliceBAnswerDispositionV1.RETAINS_MATERIAL_QUESTION,
        )

    branch_four = answers[3]
    if branch_four == "yes":
        disposition = SliceBAnswerDispositionV1.RESOLVED_DEPENDENCE_ACCOUNTED
    elif branch_four == "no":
        disposition = SliceBAnswerDispositionV1.REQUIRES_FURTHER_EVIDENCE
    elif branch_four == "unknown":
        disposition = SliceBAnswerDispositionV1.RETAINS_MATERIAL_QUESTION
    else:
        # The raw not-applicable rule above makes this unreachable, but retaining an
        # explicit closed guard prevents a future domain widening.
        raise SliceBAnswerTreeContractError(
            "branch-four not-applicable is illegal without an earlier no"
        )
    return SliceBAnswerTreeResolutionV1(
        normalized_answers=answers,
        disposition=disposition,
    )


class _CompositionReplayError(ValueError):
    """Expected fail-closed replay refusal, never rendered as free text."""


def _rederivation_mismatch() -> SliceBCompositionResultV1:
    return SliceBCompositionResultV1(
        disposition=SliceBCompositionDispositionV1.OBSERVATION_REDERIVATION_MISMATCH,
        observations=None,
        question=None,
        primary_refusal=SliceBPrimaryRefusalReasonV1.OBSERVATION_REDERIVATION_MISMATCH,
        question_scope_unresolved=False,
    )


def _require_composition_request(
    *,
    context: object,
    selected_path: object,
    candidate_unit_column_index: object,
    comparison_column_index: object,
) -> None:
    if type(context) is not ManifestBoundFrozenInspectionContext:
        raise SliceBCompositionContractError("exact manifest-bound context required")
    if not _safe_path(selected_path, ascii_only=True, max_bytes=512):
        raise SliceBCompositionContractError("selected path is outside the closed request")
    if (
        type(candidate_unit_column_index) is not int
        or type(comparison_column_index) is not int
        or not 0 <= candidate_unit_column_index < _MAX_COLUMNS
        or not 0 <= comparison_column_index < _MAX_COLUMNS
        or candidate_unit_column_index == comparison_column_index
    ):
        raise SliceBCompositionContractError("selected column roles are outside the request")


def _validate_selected_frozen_csv(
    context: ManifestBoundFrozenInspectionContext,
    selected_path: str,
) -> _SelectedFrozenCsvV1:
    try:
        snapshot_digest = context.snapshot_digest
        if type(snapshot_digest) is not str or _HASH_PATTERN.fullmatch(snapshot_digest) is None:
            raise _CompositionReplayError
        parsed_records = _parse_base_records(context.base_records)
        snapshots = [
            (record, payload)
            for record, payload in parsed_records
            if record.ref.record_type == "repository_snapshot"
        ]
        if len(snapshots) != 1:
            raise _CompositionReplayError
        snapshot_record, snapshot = snapshots[0]
        if (
            snapshot.get("snapshot_id") != snapshot_record.ref.record_id
            or snapshot.get("snapshot_digest") != snapshot_digest
            or snapshot.get("immutability") is not True
        ):
            raise _CompositionReplayError

        manifest_input = context.file_manifest_input
        if type(manifest_input) is not FrozenFileManifestInput:
            raise _CompositionReplayError
        manifest_ref, manifest_bytes, _manifest_digest = _validate_manifest_capability(
            manifest_input
        )
        if snapshot.get("file_manifest_ref") != manifest_ref:
            raise _CompositionReplayError

        joined = _manifest_record_bijection(
            parsed_records,
            snapshot_ref=snapshot_record.ref.to_dict(),
            manifest_bytes=manifest_bytes,
        )
        selected_rows = [row for row in joined if row[1]["path"] == selected_path]
        if len(selected_rows) != 1:
            raise _CompositionReplayError
        selected_file_record, selected_file = selected_rows[0]
        if selected_file.get("entry_kind") != "regular_file":
            raise _CompositionReplayError

        selected_identity_record, selected_identity = _selected_full_digest_identity(
            parsed_records,
            joined,
            selected_file_record=selected_file_record,
            selected_file_payload=selected_file,
        )
        material = _selected_material_input(
            context.material_inputs,
            selected_path=selected_path,
            selected_file_record=selected_file_record,
            selected_identity_record=selected_identity_record,
        )
        content_digest = _digest_bytes(material.content)
        evidence = selected_identity.get("identity_evidence")
        if (
            type(material.content_digest) is not str
            or material.content_digest != content_digest
            or type(selected_file.get("byte_size")) is not int
            or selected_file["byte_size"] != len(material.content)
            or type(evidence) is not dict
            or evidence.get("kind") != "full_digest"
            or evidence.get("digest") != content_digest
        ):
            raise _CompositionReplayError
        return _SelectedFrozenCsvV1(
            snapshot_record=snapshot_record,
            selected_file_record=selected_file_record,
            selected_identity_record=selected_identity_record,
            material=material,
            content_digest=content_digest,
        )
    except _CompositionReplayError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise _CompositionReplayError from error


def _parse_base_records(
    base_records: object,
) -> tuple[tuple[FrozenBaseRecord, dict[str, object]], ...]:
    if type(base_records) is not tuple:
        raise _CompositionReplayError
    parsed: list[tuple[FrozenBaseRecord, dict[str, object]]] = []
    references: set[tuple[str, str]] = set()
    for record in base_records:
        if type(record) is not FrozenBaseRecord or type(record.ref) is not RecordRef:
            raise _CompositionReplayError
        if (
            type(record.ref.record_type) is not str
            or not record.ref.record_type
            or type(record.ref.record_id) is not str
            or not record.ref.record_id
            or type(record.canonical_payload) is not bytes
            or type(record.payload_digest) is not str
            or _HASH_PATTERN.fullmatch(record.payload_digest) is None
            or _digest_bytes(record.canonical_payload) != record.payload_digest
        ):
            raise _CompositionReplayError
        reference = (record.ref.record_type, record.ref.record_id)
        if reference in references:
            raise _CompositionReplayError
        references.add(reference)
        payload = _parse_canonical_object(record.canonical_payload)
        parsed.append((record, payload))
    return tuple(parsed)


def _validate_manifest_capability(
    manifest_input: FrozenFileManifestInput,
) -> tuple[str, bytes, str]:
    manifest_ref = manifest_input.file_manifest_ref
    manifest_bytes = manifest_input.canonical_jsonl_bytes
    manifest_digest = manifest_input.manifest_digest
    if (
        not _safe_path(manifest_ref, ascii_only=False, max_bytes=None)
        or type(manifest_bytes) is not bytes
        or not manifest_bytes
        or manifest_bytes[-1:] != b"\n"
        or type(manifest_digest) is not str
        or _HASH_PATTERN.fullmatch(manifest_digest) is None
        or _digest_bytes(manifest_bytes) != manifest_digest
    ):
        raise _CompositionReplayError
    return manifest_ref, manifest_bytes, manifest_digest


def _manifest_record_bijection(
    parsed_records: tuple[tuple[FrozenBaseRecord, dict[str, object]], ...],
    *,
    snapshot_ref: dict[str, str],
    manifest_bytes: bytes,
) -> tuple[tuple[FrozenBaseRecord, dict[str, object]], ...]:
    associated: dict[str, tuple[FrozenBaseRecord, dict[str, object]]] = {}
    associated_paths: set[str] = set()
    for record, payload in parsed_records:
        if record.ref.record_type != "file_record" or payload.get("snapshot_ref") != snapshot_ref:
            continue
        _validate_file_record(record, payload, snapshot_ref)
        identifier = cast(str, payload["file_record_id"])
        path = cast(str, payload["path"])
        if identifier in associated or path in associated_paths:
            raise _CompositionReplayError
        associated[identifier] = (record, payload)
        associated_paths.add(path)
    if not associated:
        raise _CompositionReplayError

    joined: list[tuple[FrozenBaseRecord, dict[str, object]]] = []
    manifest_ids: set[str] = set()
    manifest_paths: set[str] = set()
    for encoded in manifest_bytes[:-1].split(b"\n"):
        if not encoded:
            raise _CompositionReplayError
        entry = _parse_canonical_object(encoded)
        manifest_identifier = entry.get("file_record_id")
        manifest_path = entry.get("path")
        if (
            entry.get("record_type") != "file_record"
            or entry.get("snapshot_ref") != snapshot_ref
            or type(manifest_identifier) is not str
            or manifest_identifier in manifest_ids
            or type(manifest_path) is not str
            or manifest_path in manifest_paths
        ):
            raise _CompositionReplayError
        match = associated.get(manifest_identifier)
        if match is None or match[0].canonical_payload != encoded:
            raise _CompositionReplayError
        manifest_ids.add(manifest_identifier)
        manifest_paths.add(manifest_path)
        joined.append(match)
    if manifest_ids != set(associated) or len(joined) != len(associated):
        raise _CompositionReplayError
    return tuple(joined)


def _validate_file_record(
    record: FrozenBaseRecord,
    payload: dict[str, object],
    snapshot_ref: dict[str, str],
) -> None:
    identifier = payload.get("file_record_id")
    path = payload.get("path")
    byte_size = payload.get("byte_size")
    identity_ref = payload.get("asset_identity_ref")
    if (
        payload.get("record_type") != "file_record"
        or type(identifier) is not str
        or identifier != record.ref.record_id
        or not _safe_path(path, ascii_only=False, max_bytes=None)
        or type(payload.get("entry_kind")) is not str
        or not payload["entry_kind"]
        or type(byte_size) is not int
        or byte_size < 0
        or payload.get("snapshot_ref") != snapshot_ref
        or not _exact_ref_mapping(identity_ref, "asset_identity")
    ):
        raise _CompositionReplayError


def _selected_full_digest_identity(
    parsed_records: tuple[tuple[FrozenBaseRecord, dict[str, object]], ...],
    joined_files: tuple[tuple[FrozenBaseRecord, dict[str, object]], ...],
    *,
    selected_file_record: FrozenBaseRecord,
    selected_file_payload: dict[str, object],
) -> tuple[FrozenBaseRecord, dict[str, object]]:
    file_ref = selected_file_record.ref.to_dict()
    claims = [
        (record, payload)
        for record, payload in parsed_records
        if record.ref.record_type == "asset_identity" and payload.get("asset_ref") == file_ref
    ]
    if len(claims) != 1:
        raise _CompositionReplayError
    identity_record, identity = claims[0]
    identity_ref = selected_file_payload.get("asset_identity_ref")
    evidence = identity.get("identity_evidence")
    if (
        identity_ref != identity_record.ref.to_dict()
        or identity.get("record_type") != "asset_identity"
        or identity.get("asset_identity_id") != identity_record.ref.record_id
        or identity.get("tier") != "full_digest"
        or identity.get("asset_ref") != file_ref
        or type(evidence) is not dict
        or evidence.get("kind") != "full_digest"
        or type(evidence.get("digest")) is not str
        or _HASH_PATTERN.fullmatch(cast(str, evidence["digest"])) is None
    ):
        raise _CompositionReplayError
    association_count = sum(
        payload.get("asset_identity_ref") == identity_record.ref.to_dict()
        for _record, payload in joined_files
    )
    if association_count != 1:
        raise _CompositionReplayError
    return identity_record, identity


def _selected_material_input(
    material_inputs: object,
    *,
    selected_path: str,
    selected_file_record: FrozenBaseRecord,
    selected_identity_record: FrozenBaseRecord,
) -> FrozenMaterialInput:
    if type(material_inputs) is not tuple:
        raise _CompositionReplayError
    matches = [item for item in material_inputs if getattr(item, "path", None) == selected_path]
    if len(matches) != 1 or type(matches[0]) is not FrozenMaterialInput:
        raise _CompositionReplayError
    material = matches[0]
    if (
        type(material.path) is not str
        or material.path != selected_path
        or type(material.file_ref) is not RecordRef
        or material.file_ref != selected_file_record.ref
        or type(material.asset_identity_ref) is not RecordRef
        or material.asset_identity_ref != selected_identity_record.ref
        or type(material.content) is not bytes
    ):
        raise _CompositionReplayError
    return material


def _derive_review_scope_digest(
    context: ManifestBoundFrozenInspectionContext,
    selected_path: str,
) -> str | None:
    """Reparse every retained scope preimage; return no carried or supplied digest."""

    try:
        selected = _validate_selected_frozen_csv(context, selected_path)
        # Reparse the snapshot bytes instead of consuming the earlier parsed mapping.
        snapshot = _parse_canonical_object(selected.snapshot_record.canonical_payload)
        extensions = snapshot.get("extensions")
        if type(extensions) is not dict:
            raise _CompositionReplayError
        paths = extensions.get("x-material-full-digest-paths")
        identities = extensions.get("x-material-input-identities")
        if (
            type(paths) is not list
            or not 1 <= len(paths) <= _MAX_SCOPE_PATHS
            or any(not _safe_path(path, ascii_only=True, max_bytes=512) for path in paths)
            or paths != sorted(paths)
            or len(paths) != len(set(paths))
        ):
            raise _CompositionReplayError
        expected_identities = [
            {"path": path, "tier": "full_digest"} for path in cast(list[str], paths)
        ]
        if type(identities) is not list or identities != expected_identities:
            raise _CompositionReplayError
        for identity in identities:
            if type(identity) is not dict or set(identity) != {"path", "tier"}:
                raise _CompositionReplayError

        material_inputs = context.material_inputs
        if type(material_inputs) is not tuple or not 1 <= len(material_inputs) <= _MAX_SCOPE_PATHS:
            raise _CompositionReplayError
        material_paths: list[str] = []
        for material in material_inputs:
            if (
                type(material) is not FrozenMaterialInput
                or not _safe_path(material.path, ascii_only=True, max_bytes=512)
                or type(material.content) is not bytes
                or type(material.content_digest) is not str
                or _digest_bytes(material.content) != material.content_digest
            ):
                raise _CompositionReplayError
            material_paths.append(material.path)
        if material_paths != paths or material_paths.count(selected_path) != 1:
            raise _CompositionReplayError

        manifest_input = context.file_manifest_input
        if type(manifest_input) is not FrozenFileManifestInput:
            raise _CompositionReplayError
        manifest_ref, manifest_bytes, manifest_digest = _validate_manifest_capability(
            manifest_input
        )
        if snapshot.get("file_manifest_ref") != manifest_ref:
            raise _CompositionReplayError
        # The recomputation below deliberately uses the bytes, not either carried
        # payload/manifest/content digest field.
        scope_preimage = {
            "profile": _SCOPE_PROFILE,
            "snapshot_ref": selected.snapshot_record.ref.to_dict(),
            "snapshot_payload_digest": _digest_bytes(selected.snapshot_record.canonical_payload),
            "file_manifest_ref": manifest_ref,
            "manifest_digest": _digest_bytes(manifest_bytes),
            "selected_path": selected_path,
            "selected_file_ref": selected.selected_file_record.ref.to_dict(),
            "selected_asset_identity_ref": selected.selected_identity_record.ref.to_dict(),
            "selected_content_digest": _digest_bytes(selected.material.content),
        }
        if manifest_digest != scope_preimage["manifest_digest"]:
            raise _CompositionReplayError
        return _digest_canonical(scope_preimage)
    except _CompositionReplayError:
        return None
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        return None


def _parse_csv_bytes(content: bytes) -> tuple[tuple[bytes, ...], ...]:
    if type(content) is not bytes or not 1 <= len(content) <= _MAX_CSV_BYTES:
        raise _CompositionReplayError
    if content[-1:] != b"\n" or any(byte != 0x0A and not 0x20 <= byte <= 0x7E for byte in content):
        raise _CompositionReplayError
    if b'"' in content:
        raise _CompositionReplayError
    physical_lines = content[:-1].split(b"\n")
    if not physical_lines or any(not line for line in physical_lines):
        raise _CompositionReplayError

    rows: list[tuple[bytes, ...]] = []
    for line in physical_lines:
        row = tuple(line.split(b","))
        if any(not field or len(field) > _MAX_FIELD_BYTES for field in row):
            raise _CompositionReplayError
        rows.append(row)
    header = rows[0]
    if not 2 <= len(header) <= _MAX_COLUMNS or len(set(header)) != len(header):
        raise _CompositionReplayError
    data = rows[1:]
    if not 1 <= len(data) <= _MAX_DATA_ROWS or any(len(row) != len(header) for row in data):
        raise _CompositionReplayError
    return tuple(rows)


def _derive_csv_facts(
    table: tuple[tuple[bytes, ...], ...],
    *,
    candidate_unit_column_index: int,
    comparison_column_index: int,
) -> _CsvFactsV1:
    header = table[0]
    if candidate_unit_column_index >= len(header) or comparison_column_index >= len(header):
        raise _CompositionReplayError
    rows = table[1:]
    candidates = [row[candidate_unit_column_index] for row in rows]
    comparisons = [row[comparison_column_index] for row in rows]
    candidate_counts = Counter(candidates)
    comparison_counts = Counter(comparisons)
    candidate_comparisons: dict[bytes, set[bytes]] = {}
    for candidate, comparison in zip(candidates, comparisons, strict=True):
        candidate_comparisons.setdefault(candidate, set()).add(comparison)
    histogram_counts = Counter(len(values) for values in candidate_comparisons.values())
    return _CsvFactsV1(
        data_row_count=len(rows),
        column_count=len(header),
        candidate_unit_distinct_count=len(candidate_counts),
        comparison_distinct_count=len(comparison_counts),
        sorted_group_sizes=tuple(sorted(comparison_counts.values())),
        repeated_candidate_value_count=sum(count > 1 for count in candidate_counts.values()),
        cross_comparison_candidate_value_count=sum(
            len(values) > 1 for values in candidate_comparisons.values()
        ),
        comparison_values_per_candidate_histogram=tuple(sorted(histogram_counts.items())),
    )


def _derive_observations(
    *,
    context: ManifestBoundFrozenInspectionContext,
    selected: _SelectedFrozenCsvV1,
    facts: _CsvFactsV1,
    candidate_unit_column_index: int,
    comparison_column_index: int,
    review_scope_selection_evidence_digest: str,
) -> SliceBObservationSetV1:
    common: dict[str, object] = {
        "observation_version": _OBSERVATION_VERSION,
        "snapshot_digest": context.snapshot_digest,
        "file_record_ref_digest": _digest_canonical(selected.selected_file_record.ref.to_dict()),
        "content_digest": selected.content_digest,
        "selected_file_ordinal": 1,
        "review_scope_selection_evidence_digest": review_scope_selection_evidence_digest,
        "finding_eligible": False,
    }

    shape_projection = {
        **common,
        "observation_type": "csv-table-shape-v1",
        "verifier_id": "slice-b-csv-shape-verifier-v1",
        "data_row_count": facts.data_row_count,
        "column_count": facts.column_count,
    }
    shape = CsvTableShapeObservationV1(
        observation_version=_OBSERVATION_VERSION,
        observation_type="csv-table-shape-v1",
        verifier_id="slice-b-csv-shape-verifier-v1",
        snapshot_digest=context.snapshot_digest,
        file_record_ref_digest=cast(str, common["file_record_ref_digest"]),
        content_digest=selected.content_digest,
        selected_file_ordinal=1,
        review_scope_selection_evidence_digest=review_scope_selection_evidence_digest,
        data_row_count=facts.data_row_count,
        column_count=facts.column_count,
        observation_id=_digest_canonical(shape_projection),
        finding_eligible=False,
    )

    cardinality_projection = {
        **common,
        "observation_type": "csv-selected-cardinalities-v1",
        "verifier_id": "slice-b-csv-cardinality-verifier-v1",
        "candidate_unit_column_index": candidate_unit_column_index,
        "comparison_column_index": comparison_column_index,
        "candidate_unit_distinct_count": facts.candidate_unit_distinct_count,
        "comparison_distinct_count": facts.comparison_distinct_count,
    }
    cardinality = CsvSelectedCardinalitiesObservationV1(
        observation_version=_OBSERVATION_VERSION,
        observation_type="csv-selected-cardinalities-v1",
        verifier_id="slice-b-csv-cardinality-verifier-v1",
        snapshot_digest=context.snapshot_digest,
        file_record_ref_digest=cast(str, common["file_record_ref_digest"]),
        content_digest=selected.content_digest,
        selected_file_ordinal=1,
        review_scope_selection_evidence_digest=review_scope_selection_evidence_digest,
        candidate_unit_column_index=candidate_unit_column_index,
        comparison_column_index=comparison_column_index,
        candidate_unit_distinct_count=facts.candidate_unit_distinct_count,
        comparison_distinct_count=facts.comparison_distinct_count,
        observation_id=_digest_canonical(cardinality_projection),
        finding_eligible=False,
    )

    group_projection = {
        **common,
        "observation_type": "csv-comparison-group-sizes-v1",
        "verifier_id": "slice-b-csv-group-size-verifier-v1",
        "comparison_column_index": comparison_column_index,
        "sorted_group_sizes": facts.sorted_group_sizes,
    }
    group_sizes = CsvComparisonGroupSizesObservationV1(
        observation_version=_OBSERVATION_VERSION,
        observation_type="csv-comparison-group-sizes-v1",
        verifier_id="slice-b-csv-group-size-verifier-v1",
        snapshot_digest=context.snapshot_digest,
        file_record_ref_digest=cast(str, common["file_record_ref_digest"]),
        content_digest=selected.content_digest,
        selected_file_ordinal=1,
        review_scope_selection_evidence_digest=review_scope_selection_evidence_digest,
        comparison_column_index=comparison_column_index,
        sorted_group_sizes=facts.sorted_group_sizes,
        observation_id=_digest_canonical(group_projection),
        finding_eligible=False,
    )

    incidence_projection = {
        **common,
        "observation_type": "csv-unit-comparison-incidence-v1",
        "verifier_id": "slice-b-csv-incidence-verifier-v1",
        "candidate_unit_column_index": candidate_unit_column_index,
        "comparison_column_index": comparison_column_index,
        "repeated_candidate_value_count": facts.repeated_candidate_value_count,
        "cross_comparison_candidate_value_count": (facts.cross_comparison_candidate_value_count),
        "comparison_values_per_candidate_histogram": (
            facts.comparison_values_per_candidate_histogram
        ),
    }
    incidence = CsvUnitComparisonIncidenceObservationV1(
        observation_version=_OBSERVATION_VERSION,
        observation_type="csv-unit-comparison-incidence-v1",
        verifier_id="slice-b-csv-incidence-verifier-v1",
        snapshot_digest=context.snapshot_digest,
        file_record_ref_digest=cast(str, common["file_record_ref_digest"]),
        content_digest=selected.content_digest,
        selected_file_ordinal=1,
        review_scope_selection_evidence_digest=review_scope_selection_evidence_digest,
        candidate_unit_column_index=candidate_unit_column_index,
        comparison_column_index=comparison_column_index,
        repeated_candidate_value_count=facts.repeated_candidate_value_count,
        cross_comparison_candidate_value_count=facts.cross_comparison_candidate_value_count,
        comparison_values_per_candidate_histogram=(facts.comparison_values_per_candidate_histogram),
        observation_id=_digest_canonical(incidence_projection),
        finding_eligible=False,
    )
    return shape, cardinality, group_sizes, incidence


def _primary_observations_match(
    primary: object,
    expected: SliceBObservationSetV1,
) -> bool:
    if not _is_exact_observation_tuple(primary):
        return False
    typed_primary = cast(SliceBObservationSetV1, primary)
    try:
        return all(
            _closed_value_equal(actual, derived)
            and _canonical_bytes(_dataclass_projection(actual))
            == _canonical_bytes(_dataclass_projection(derived))
            for actual, derived in zip(typed_primary, expected, strict=True)
        )
    except (AttributeError, TypeError, ValueError, RecursionError):
        return False


def _is_exact_observation_tuple(value: object) -> bool:
    return (
        type(value) is tuple
        and len(value) == 4
        and type(value[0]) is CsvTableShapeObservationV1
        and type(value[1]) is CsvSelectedCardinalitiesObservationV1
        and type(value[2]) is CsvComparisonGroupSizesObservationV1
        and type(value[3]) is CsvUnitComparisonIncidenceObservationV1
    )


def _closed_value_equal(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if type(expected) is tuple:
        actual_tuple = cast(tuple[object, ...], actual)
        expected_tuple = cast(tuple[object, ...], expected)
        return len(actual_tuple) == len(expected_tuple) and all(
            _closed_value_equal(left, right)
            for left, right in zip(actual_tuple, expected_tuple, strict=True)
        )
    if hasattr(type(expected), "__dataclass_fields__"):
        field_names = cast(dict[str, object], type(expected).__dict__["__dataclass_fields__"])
        return all(
            _closed_value_equal(getattr(actual, name), getattr(expected, name))
            for name in field_names
        )
    return actual == expected


def _dataclass_projection(value: object) -> dict[str, object]:
    field_names = cast(dict[str, object], getattr(type(value), "__dataclass_fields__", {}))
    if not field_names:
        raise TypeError("closed observation dataclass required")
    return {name: getattr(value, name) for name in field_names}


def _question_predicate(facts: _CsvFactsV1) -> bool:
    return (
        facts.data_row_count >= 2
        and facts.candidate_unit_distinct_count < facts.data_row_count
        and facts.comparison_distinct_count >= 2
        and facts.repeated_candidate_value_count >= 1
        and facts.cross_comparison_candidate_value_count >= 1
    )


def _derive_question(
    observations: SliceBObservationSetV1,
    scope_digest: str,
) -> SliceBQuestionRenderIRV1:
    basis = cast(tuple[str, str, str, str], tuple(item.observation_id for item in observations))
    projection = {
        "ir_schema": "slice-b-question-render-ir-v1",
        "grade": "MATERIAL QUESTION",
        "rule_id": _QUESTION_RULE_ID,
        "render_template_id": _QUESTION_TEMPLATE_ID,
        "basis_observation_ids": basis,
        "review_scope_selection_evidence_digest": scope_digest,
        "answer_domain_id": _ANSWER_DOMAIN_ID,
        "unresolved_consequence_id": _UNRESOLVED_CONSEQUENCE_ID,
        "finding_eligible": False,
    }
    return SliceBQuestionRenderIRV1(
        ir_schema="slice-b-question-render-ir-v1",
        grade="MATERIAL QUESTION",
        rule_id=_QUESTION_RULE_ID,
        render_template_id=_QUESTION_TEMPLATE_ID,
        basis_observation_ids=basis,
        review_scope_selection_evidence_digest=scope_digest,
        answer_domain_id=_ANSWER_DOMAIN_ID,
        unresolved_consequence_id=_UNRESOLVED_CONSEQUENCE_ID,
        finding_eligible=False,
        question_id=_digest_canonical(projection),
    )


def _require_raw_answer_tuple(raw_answers: object) -> SliceBAnswerTupleV1:
    allowed = {"yes", "no", "unknown", "not-applicable"}
    if (
        type(raw_answers) is not tuple
        or len(raw_answers) != 4
        or any(type(answer) is not str or answer not in allowed for answer in raw_answers)
        or raw_answers[0] == "not-applicable"
    ):
        raise SliceBAnswerTreeContractError("raw answers are outside the closed token domain")
    return cast(SliceBAnswerTupleV1, raw_answers)


def _parse_canonical_object(payload: bytes) -> dict[str, object]:
    try:
        decoded = payload.decode("utf-8", errors="strict")
        value = json.loads(decoded, parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise _CompositionReplayError from error
    if type(value) is not dict or canonical_json(value).encode("utf-8") != payload:
        raise _CompositionReplayError
    return cast(dict[str, object], value)


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"noncanonical JSON constant: {value}")


def _exact_ref_mapping(value: object, record_type: str) -> bool:
    return (
        type(value) is dict
        and set(value) == {"record_type", "record_id"}
        and value.get("record_type") == record_type
        and type(value.get("record_id")) is str
        and bool(value["record_id"])
    )


def _safe_path(value: object, *, ascii_only: bool, max_bytes: int | None) -> bool:
    if type(value) is not str or not value or value == "." or value.startswith("/"):
        return False
    try:
        encoded = value.encode("ascii" if ascii_only else "utf-8")
    except UnicodeEncodeError:
        return False
    if max_bytes is not None and len(encoded) > max_bytes:
        return False
    if ascii_only and any(byte < 0x20 or byte > 0x7E for byte in encoded):
        return False
    return ".." not in value.split("/") and posixpath.normpath(value) == value and "//" not in value


def _digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _digest_canonical(value: object) -> str:
    return _digest_bytes(_canonical_bytes(value))
