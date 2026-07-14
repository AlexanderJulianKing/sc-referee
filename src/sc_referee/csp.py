"""Deterministic Confirmed Scientific Premise records and exact-scope reads.

CSP records are data, not verdicts.  Consumers receive values only after every
field-level ceremony and exact identity check succeeds; all other paths return a
typed abstention without exposing draft values.
"""
from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass, field, replace
from enum import Enum
from types import MappingProxyType
from typing import Any, Literal, Mapping


def _freeze_json(value: Any) -> Any:
    """Recursively freeze supported typed JSON-like values."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("CSP structured value mapping keys must be strings")
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    raise TypeError(f"unsupported CSP structured value: {type(value).__name__}")


def _canonical_json_value(value: Any) -> Any:
    """Return a JSON-serializable typed projection without changing ordered sequences."""
    if isinstance(value, Mapping):
        return {key: _canonical_json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical_json_value(item) for item in value]
    return value


class CspFieldState(str, Enum):
    ABSENT = "absent"
    PROPOSED_UNCONFIRMED = "proposed_unconfirmed"
    PRESENTED = "presented"
    CONFIRMED_HIGH = "confirmed_high"
    UNRESOLVED = "unresolved"
    DECLINED_FOR_CONSUMER = "declined_for_consumer"
    INVALIDATED = "invalidated"


_TRANSITIONS = {
    (CspFieldState.ABSENT, "propose"): CspFieldState.PROPOSED_UNCONFIRMED,
    (CspFieldState.PROPOSED_UNCONFIRMED, "present"): CspFieldState.PRESENTED,
    (CspFieldState.PRESENTED, "confirm_high"): CspFieldState.CONFIRMED_HIGH,
    (CspFieldState.PRESENTED, "not_sure"): CspFieldState.UNRESOLVED,
    (CspFieldState.PRESENTED, "skip"): CspFieldState.UNRESOLVED,
    (CspFieldState.PRESENTED, "decline_for_consumer"):
        CspFieldState.DECLINED_FOR_CONSUMER,
    **{
        (state, "scope_identity_changed"): CspFieldState.INVALIDATED
        for state in (
            CspFieldState.PROPOSED_UNCONFIRMED,
            CspFieldState.PRESENTED,
            CspFieldState.CONFIRMED_HIGH,
            CspFieldState.UNRESOLVED,
            CspFieldState.DECLINED_FOR_CONSUMER,
        )
    },
}


def transition_field(state: CspFieldState, event: str) -> CspFieldState:
    try:
        return _TRANSITIONS[(state, event)]
    except KeyError as exc:
        raise ValueError(f"illegal CSP transition: {state.value} + {event}") from exc


@dataclass(frozen=True)
class CspScope:
    fitted_result_id: str
    contrast_name: str
    target_coefficient: str
    exposure_column: str
    row_ledger_identity: str
    estimand_id: str
    group_source_column: str
    assignment_identity: str
    contract_scope: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if any(not isinstance(value, str) or not value.strip() for value in (
            self.fitted_result_id, self.contrast_name, self.target_coefficient,
            self.exposure_column, self.row_ledger_identity, self.estimand_id,
            self.group_source_column,
            self.assignment_identity,
        )):
            raise ValueError("CSP scope requires every exact identity")
        extension = dict(self.contract_scope)
        allowed = {
            "reported_scalar_id", "target_population_id", "census_artifact_identity",
            "census_count_ledger_identity", "stratum_ledger_identity",
            "weight_vector_identity",
        }
        contamination_allowed = {
            "measurement_artifact_identity", "measurement_run_identity",
            "raw_source_ledger_identity", "measurement_vector_ledger_identity",
            "transformed_basis_ledger_identity", "basis_output_digest",
            "fitted_design_identity",
        }
        if extension and set(extension) not in {frozenset(allowed), frozenset(contamination_allowed)}:
            raise ValueError("CSP contract scope extension must be complete and closed")
        if any(not isinstance(value, str) or not value.strip()
               for value in extension.values()):
            raise ValueError("CSP target scope extension requires exact identities")
        object.__setattr__(self, "contract_scope", MappingProxyType(extension))

    @property
    def fingerprint(self) -> str:
        payload = {
            "schema_version": "csp-scope/v2",
            "fitted_result_id": self.fitted_result_id,
            "contrast_name": self.contrast_name,
            "target_coefficient": self.target_coefficient,
            "exposure_column": self.exposure_column,
            "row_ledger_identity": self.row_ledger_identity,
            "estimand_id": self.estimand_id,
            "group_source_column": self.group_source_column,
            "assignment_identity": self.assignment_identity,
        }
        if self.contract_scope:
            payload["contract_scope"] = dict(self.contract_scope)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False).encode("utf-8")
        return "csp-scope:v2:" + hashlib.sha256(canonical).hexdigest()


def assignment_identity(rows, exposure_column: str, group_source_column: str) -> str:
    """Digest exact typed exposure/group assignments on the ordered fitted rows."""
    if exposure_column not in rows.columns or group_source_column not in rows.columns:
        raise ValueError("assignment identity columns are unavailable")

    def encoded(value) -> bytes:
        if hasattr(value, "item"):
            try:
                value = value.item()
            except Exception:
                # Any scalar-conversion hook failure is tolerated here: the kept value then
                # encodes by type below, or raises the expected ValueError for an un-encodable
                # type. This lets callers catch a specific expected exception rather than a
                # blanket Exception (which would mask genuine internal defects).
                pass
        if value is None:
            return b"null:none"
        if isinstance(value, float) and value != value:
            return b"null:float"
        if isinstance(value, bool):
            return b"bool:1" if value else b"bool:0"
        if isinstance(value, int):
            return b"int:" + str(value).encode("ascii")
        if isinstance(value, float):
            return b"float:" + struct.pack("<d", value)
        if isinstance(value, str):
            return b"str:" + value.encode("utf-8")
        raise ValueError(f"unsupported assignment value type: {type(value).__name__}")

    digest = hashlib.sha256()
    digest.update(b"sc-referee-csp-assignment-identity-v1\0")
    for label in (exposure_column, group_source_column):
        item = label.encode("utf-8")
        digest.update(struct.pack("<Q", len(item)))
        digest.update(item)
    digest.update(struct.pack("<Q", len(rows)))
    for exposure, group in zip(rows[exposure_column], rows[group_source_column]):
        for value in (exposure, group):
            item = encoded(value)
            digest.update(struct.pack("<Q", len(item)))
            digest.update(item)
    return "csp-assign:v1:" + digest.hexdigest()


@dataclass(frozen=True)
class CspFieldRecord:
    field_id: str
    value: Any
    state: CspFieldState
    confidence: Literal["high", "low"]
    scope_fingerprint: str
    evidence_ids: tuple[str, ...]
    evidence_basis: str | None
    selected_teach_back_id: str | None
    consequence_acknowledged: bool
    confirmation_event_id: str | None
    actor: str | None
    confirmed_at: str | None
    presentation_event_id: str | None = None
    answer_event_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _freeze_json(self.value))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
        if self.confidence not in ("high", "low"):
            raise ValueError("invalid CSP field confidence")


@dataclass(frozen=True)
class CspContractRecord:
    contract_id: str
    contract_type: str
    scope: CspScope
    fields: Mapping[str, CspFieldRecord]
    authorized_consumers: tuple[str, ...]
    authority_attested: bool
    authority_attestation: str | None
    validator_version: str
    validator_result: tuple[str, ...]
    active: bool
    created_at: str
    component_identities: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        fields = dict(self.fields)
        if any(key != record.field_id for key, record in fields.items()):
            raise ValueError("CSP field key must equal field_id")
        object.__setattr__(self, "fields", MappingProxyType(fields))
        object.__setattr__(self, "authorized_consumers", tuple(self.authorized_consumers))
        object.__setattr__(self, "validator_result", tuple(self.validator_result))
        object.__setattr__(self, "component_identities",
                           MappingProxyType(dict(self.component_identities)))


@dataclass(frozen=True)
class CspReadRequest:
    contract_type: str
    scope: CspScope
    required_fields: tuple[str, ...]
    consumer_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "required_fields", tuple(self.required_fields))


@dataclass(frozen=True)
class RatifiedFactSet:
    contract_id: str
    contract_type: str
    scope: CspScope
    values: Mapping[str, Any]
    component_identities: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _freeze_json(self.values))
        object.__setattr__(self, "component_identities",
                           MappingProxyType(dict(self.component_identities)))


@dataclass(frozen=True)
class CspAbstention:
    reason: str
    contract_id: str | None
    kind: str = "needs_evidence"


def component_identities_for(record: CspContractRecord, manifest) -> Mapping[str, str]:
    """Hash each declared component over exact scope and ordered, frozen field values."""
    identities: dict[str, str] = {}
    for identity_name, ordered_fields in manifest.component_field_groups.items():
        payload = {
            "domain": "sc-referee-csp-component-identity-v1",
            "contract_type": record.contract_type,
            "validator_version": record.validator_version,
            "scope_fingerprint": record.scope.fingerprint,
            "component_identity_name": identity_name,
            "ordered_fields": [
                [field_id, _canonical_json_value(record.fields[field_id].value)]
                for field_id in ordered_fields
            ],
        }
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        identities[identity_name] = "sha256:" + hashlib.sha256(encoded).hexdigest()
    return MappingProxyType(identities)


def invalidate_contract_for_scope(
    record: CspContractRecord, current_scope: CspScope
) -> CspContractRecord:
    """Invalidate, never migrate, every active field after any bound identity changes."""
    if record.scope == current_scope:
        return record
    fields = {
        field_id: replace(field, state=CspFieldState.INVALIDATED, confidence="low")
        for field_id, field in record.fields.items()
    }
    return replace(record, fields=fields, active=False)


def read_ratified_contract(
    records: tuple[CspContractRecord, ...] | list[CspContractRecord],
    request: CspReadRequest,
) -> RatifiedFactSet | CspAbstention:
    """Return exact ratified facts or a value-free, typed abstention."""
    from sc_referee.csp_contracts import get_manifest

    try:
        manifest = get_manifest(request.contract_type)
    except KeyError:
        return CspAbstention("unknown_contract_type", None)
    candidates = [record for record in records if record.contract_type == request.contract_type]
    if not candidates:
        return CspAbstention("contract_absent", None)
    exact = [record for record in candidates if record.scope == request.scope]
    if not exact:
        return CspAbstention("scope_mismatch", candidates[0].contract_id)
    active_exact = [record for record in exact if record.active]
    if len(active_exact) > 1:
        return CspAbstention("ambiguous_contracts", None)
    record = active_exact[0] if active_exact else exact[0]
    if record.scope.fingerprint != request.scope.fingerprint:
        return CspAbstention("scope_fingerprint_mismatch", record.contract_id)
    if not record.active:
        return CspAbstention("contract_invalidated", record.contract_id)
    if record.validator_version != manifest.validator_version:
        return CspAbstention("validator_version_mismatch", record.contract_id)
    if (tuple(record.authorized_consumers) != (manifest.authorized_consumer,)
            or request.consumer_id != manifest.authorized_consumer):
        return CspAbstention("consumer_not_authorized", record.contract_id)
    if not record.authority_attested or record.authority_attestation != manifest.authority_attestation:
        return CspAbstention("self_attestation_missing", record.contract_id)
    if tuple(request.required_fields) != tuple(manifest.required_fields):
        return CspAbstention("required_fields_mismatch", record.contract_id)
    benign_fields = {
        "non_descendancy", "outside_estimand_pathway", "required_adjustment"
    } if request.contract_type == "contamination_basis_obligation/v1" else set()
    for field_id in benign_fields:
        field = record.fields.get(field_id)
        if field is not None and field.state is CspFieldState.DECLINED_FOR_CONSUMER:
            return CspAbstention(
                f"benign_non_authorization:{field_id}", record.contract_id,
                kind="benign_non_authorization",
            )
    values: dict[str, Any] = {}
    for field_id in request.required_fields:
        field = record.fields.get(field_id)
        if field is None:
            return CspAbstention("required_field_missing", record.contract_id)
        if field.state is CspFieldState.INVALIDATED:
            return CspAbstention("field_invalidated", record.contract_id)
        if field.state is not CspFieldState.CONFIRMED_HIGH:
            return CspAbstention("field_not_confirmed_high", record.contract_id)
        if field.confidence != "high":
            return CspAbstention("field_confidence_not_high", record.contract_id)
        if field.value is None:
            return CspAbstention("field_value_missing", record.contract_id)
        if field.scope_fingerprint != request.scope.fingerprint:
            return CspAbstention("field_scope_mismatch", record.contract_id)
        if not field.evidence_ids or not field.evidence_basis:
            return CspAbstention("evidence_basis_missing", record.contract_id)
        expected_teach_back = manifest.teach_back_ids[field_id]
        if field.selected_teach_back_id != expected_teach_back:
            return CspAbstention("teach_back_failed", record.contract_id)
        if not field.consequence_acknowledged:
            return CspAbstention("consequence_not_acknowledged", record.contract_id)
        if (not field.presentation_event_id or not field.answer_event_id
                or not field.confirmation_event_id or not field.actor or not field.confirmed_at):
            return CspAbstention("confirmation_metadata_missing", record.contract_id)
        values[field_id] = field.value
    for scope_key, field_id in manifest.scope_field_bindings.items():
        if request.scope.contract_scope.get(scope_key) != values.get(field_id):
            return CspAbstention("scope_value_mismatch", record.contract_id)
    validation = tuple(manifest.validate_values(values))
    if validation or tuple(record.validator_result) != validation:
        return CspAbstention("inconsistent_values", record.contract_id)
    if manifest.component_field_groups:
        expected_identities = dict(component_identities_for(record, manifest))
        if dict(record.component_identities) != expected_identities:
            return CspAbstention("component_identity_mismatch", record.contract_id)
    return RatifiedFactSet(
        record.contract_id, record.contract_type, record.scope, values,
        component_identities=record.component_identities,
    )
