from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from sc_referee.core.ids import semantic_digest, sha256_digest

IDENTITY_REGISTRY_VERSION = "1.1.0"
SESSION_RECEIPT_VERSION = "1.1.0"
MAX_CAPTURE_BYTES = 4 * 1024 * 1024


class QualificationIdentityError(ValueError):
    """Raised when qualification actor/session evidence is not authenticated."""


@dataclass(frozen=True)
class CaseAuthorSessionBinding:
    """Exact signed digests and retained bytes for one case-author session."""

    input_manifest_digest: str
    author_content_digest: str
    provider_request: bytes
    provider_response: bytes
    raw_transcript: bytes


def validate_identity_registry(value: Mapping[str, Any]) -> dict[str, Any]:
    """Replay one registrar-key registry used by a frozen qualification study."""

    registry = dict(value)
    _exact_keys(
        registry,
        {
            "artifact_kind",
            "identity_registry_version",
            "registrar_id",
            "registrar_public_key_base64",
            "credentials",
            "frozen_at",
            "qualification_authority",
            "identity_registry_digest",
            "registrar_signature_base64",
        },
        "identity registry",
    )
    if (
        registry["artifact_kind"] != "qualification_identity_registry"
        or registry["identity_registry_version"] != IDENTITY_REGISTRY_VERSION
        or registry["qualification_authority"] != "none_identity_registry_only"
    ):
        raise QualificationIdentityError("Unsupported qualification identity registry.")
    _text(registry["registrar_id"], "registrar_id")
    registrar_public_key = _public_key(
        _text(registry["registrar_public_key_base64"], "registrar_public_key_base64")
    )
    unsigned = dict(registry)
    signature_text = unsigned.pop("registrar_signature_base64")
    supplied_digest = unsigned.pop("identity_registry_digest")
    if supplied_digest != semantic_digest(unsigned):
        raise QualificationIdentityError("identity_registry_digest does not replay.")
    unsigned["identity_registry_digest"] = supplied_digest
    try:
        signature = base64.b64decode(str(signature_text), validate=True)
        registrar_public_key.verify(signature, signed_receipt_payload(unsigned))
    except (binascii.Error, InvalidSignature, ValueError) as error:
        raise QualificationIdentityError("Identity registry signature is invalid.") from error
    _timestamp(_text(registry["frozen_at"], "registry frozen_at"))
    raw_credentials = registry["credentials"]
    if not isinstance(raw_credentials, list) or not raw_credentials:
        raise QualificationIdentityError("Identity registry has no credentials.")
    credentials = [_credential(item) for item in raw_credentials]
    if credentials != raw_credentials:
        raise QualificationIdentityError("Identity registry credentials are not canonical.")
    for field in ("credential_id", "actor_id", "public_key_base64"):
        if len({str(item[field]) for item in credentials}) != len(credentials):
            raise QualificationIdentityError(f"Identity registry repeats {field}.")
    return registry


def validate_provider_session_identity_evidence(
    value: Mapping[str, Any],
    *,
    registry: Mapping[str, Any],
    identity: Mapping[str, str],
    role: str,
    case_id: str,
    target_packet_digest: str,
    assignment_digest: str,
    semantic_contract_digest: str,
    input_manifest_digest: str,
    review_content_digest: str,
) -> dict[str, Any]:
    """Verify registrar-signed launch and completion receipts for one provider session."""

    frozen_registry = validate_identity_registry(registry)
    evidence = _self_digested(value, "identity_evidence_digest")
    _exact_keys(
        evidence,
        {
            "artifact_kind",
            "identity_evidence_version",
            "identity_registry_digest",
            "credential_id",
            "launch_receipt",
            "completion_receipt",
            "retained_capture",
            "authentication_method",
            "qualification_authority",
            "identity_evidence_digest",
        },
        "provider-session identity evidence",
    )
    if (
        evidence["artifact_kind"] != "provider_session_identity_evidence"
        or evidence["identity_evidence_version"] != SESSION_RECEIPT_VERSION
        or evidence["identity_registry_digest"] != frozen_registry["identity_registry_digest"]
        or evidence["authentication_method"]
        != "registrar_ed25519_signed_session_with_retained_capture"
        or evidence["qualification_authority"] != "none_identity_evidence_only"
        or evidence["identity_evidence_digest"] != identity["identity_evidence_digest"]
    ):
        raise QualificationIdentityError(
            "Provider-session identity evidence is not bound to the frozen registry and actor."
        )
    credential = _registered_credential(
        frozen_registry,
        _text(evidence["credential_id"], "credential_id"),
    )
    if (
        credential["actor_id"] != identity["actor_id"]
        or credential["provider"] != identity["provider"]
        or role not in credential["eligible_roles"]
        or credential["active"] is not True
    ):
        raise QualificationIdentityError(
            "Registered credential is not eligible for this actor, provider, and role."
        )
    public_key = _public_key(
        _text(frozen_registry["registrar_public_key_base64"], "registrar_public_key_base64")
    )
    launch = _signed_receipt(
        evidence["launch_receipt"],
        expected_kind="qualification_session_launch_receipt",
        public_key=public_key,
    )
    expected_launch = {
        "artifact_kind": "qualification_session_launch_receipt",
        "receipt_version": SESSION_RECEIPT_VERSION,
        "credential_id": credential["credential_id"],
        "actor_id": identity["actor_id"],
        "provider": identity["provider"],
        "execution_context_id": identity["execution_context_id"],
        "role": role,
        "case_id": case_id,
        "target_packet_digest": target_packet_digest,
        "assignment_digest": assignment_digest,
        "semantic_contract_digest": semantic_contract_digest,
        "input_manifest_digest": input_manifest_digest,
        "session_nonce": launch["session_nonce"],
        "event_index": launch["event_index"],
        "predecessor_event_digest": launch["predecessor_event_digest"],
        "issued_at": launch["issued_at"],
    }
    if _receipt_payload(launch) != expected_launch:
        raise QualificationIdentityError("Session launch receipt binding has drifted.")
    _text(launch["session_nonce"], "session_nonce")
    if not isinstance(launch["event_index"], int) or isinstance(launch["event_index"], bool):
        raise QualificationIdentityError("Session launch event index is invalid.")
    _digest(launch["predecessor_event_digest"], "predecessor_event_digest")
    launch_time = _timestamp(_text(launch["issued_at"], "launch issued_at"))

    completion = _signed_receipt(
        evidence["completion_receipt"],
        expected_kind="qualification_session_completion_receipt",
        public_key=public_key,
    )
    capture = _retained_capture(evidence["retained_capture"])
    launch_digest = semantic_digest(launch)
    expected_completion = {
        "artifact_kind": "qualification_session_completion_receipt",
        "receipt_version": SESSION_RECEIPT_VERSION,
        "credential_id": credential["credential_id"],
        "actor_id": identity["actor_id"],
        "provider": identity["provider"],
        "execution_context_id": identity["execution_context_id"],
        "role": role,
        "case_id": case_id,
        "launch_receipt_digest": launch_digest,
        "provider_request_id": completion["provider_request_id"],
        "provider_request_digest": completion["provider_request_digest"],
        "provider_response_digest": completion["provider_response_digest"],
        "raw_transcript_digest": completion["raw_transcript_digest"],
        "review_content_digest": review_content_digest,
        "event_index": completion["event_index"],
        "predecessor_event_digest": launch_digest,
        "issued_at": completion["issued_at"],
    }
    if _receipt_payload(completion) != expected_completion:
        raise QualificationIdentityError("Session completion receipt binding has drifted.")
    _text(completion["provider_request_id"], "provider_request_id")
    if (
        _digest(completion["provider_request_digest"], "provider_request_digest")
        != sha256_digest(capture["provider_request"])
        or _digest(completion["provider_response_digest"], "provider_response_digest")
        != sha256_digest(capture["provider_response"])
        or _digest(completion["raw_transcript_digest"], "raw_transcript_digest")
        != sha256_digest(capture["raw_transcript"])
    ):
        raise QualificationIdentityError("Retained session capture bytes do not match receipts.")
    if completion["event_index"] != launch["event_index"] + 1:
        raise QualificationIdentityError("Session receipt event chain is not contiguous.")
    completion_time = _timestamp(_text(completion["issued_at"], "completion issued_at"))
    if completion_time < launch_time:
        raise QualificationIdentityError("Session completion predates launch.")
    return evidence


def case_author_session_binding(
    *,
    case_id: str,
    target_packet: Mapping[str, Any],
    assignment_binding: Mapping[str, Any],
    runner_freeze_digest: str,
    semantic_contract_digest: str,
    case_inventory: Sequence[Mapping[str, Any]],
    construction_certificate: Mapping[str, Any],
) -> CaseAuthorSessionBinding:
    """Build the canonical material a registrar binds for one case-author session."""

    case = _text(case_id, "case_id")
    packet = dict(target_packet)
    assignment = dict(assignment_binding)
    inventory = _case_inventory(case_inventory)
    certificate = dict(construction_certificate)
    if (
        packet.get("case_id") != case
        or assignment.get("case_id") != case
        or assignment.get("target_packet") != packet
        or certificate.get("case_id") != case
    ):
        raise QualificationIdentityError(
            "Case-author session inputs do not describe one exact assigned case."
        )
    assignment_digest = _digest(assignment.get("assignment_digest"), "assignment_digest")
    runner_digest = _digest(runner_freeze_digest, "runner_freeze_digest")
    contract_digest = _digest(semantic_contract_digest, "semantic_contract_digest")
    input_manifest = {
        "artifact_kind": "qualification_case_author_input_manifest",
        "case_id": case,
        "target_packet": packet,
        "assignment_binding": assignment,
        "assignment_digest": assignment_digest,
        "runner_freeze_digest": runner_digest,
        "semantic_contract_digest": contract_digest,
        "case_inventory": inventory,
        "case_inventory_digest": semantic_digest(inventory),
    }
    input_manifest_digest = semantic_digest(input_manifest)
    author_content = {
        "artifact_kind": "qualification_case_author_content",
        "case_id": case,
        "input_manifest_digest": input_manifest_digest,
        "construction_certificate": certificate,
    }
    author_content_digest = semantic_digest(author_content)
    provider_request = _canonical_capture_bytes(input_manifest)
    provider_response = _canonical_capture_bytes(author_content)
    return CaseAuthorSessionBinding(
        input_manifest_digest=input_manifest_digest,
        author_content_digest=author_content_digest,
        provider_request=provider_request,
        provider_response=provider_response,
        raw_transcript=provider_request + b"\n" + provider_response,
    )


def validate_case_author_session_identity_evidence(
    value: Mapping[str, Any],
    *,
    registry: Mapping[str, Any],
    identity: Mapping[str, str],
    case_id: str,
    target_packet: Mapping[str, Any],
    assignment_binding: Mapping[str, Any],
    runner_freeze_digest: str,
    semantic_contract_digest: str,
    case_inventory: Sequence[Mapping[str, Any]],
    construction_certificate: Mapping[str, Any],
) -> dict[str, Any]:
    """Authenticate a retained case-author session against its complete authored case."""

    binding = case_author_session_binding(
        case_id=case_id,
        target_packet=target_packet,
        assignment_binding=assignment_binding,
        runner_freeze_digest=runner_freeze_digest,
        semantic_contract_digest=semantic_contract_digest,
        case_inventory=case_inventory,
        construction_certificate=construction_certificate,
    )
    evidence = validate_provider_session_identity_evidence(
        value,
        registry=registry,
        identity=identity,
        role="case-author",
        case_id=case_id,
        target_packet_digest=semantic_digest(dict(target_packet)),
        assignment_digest=_digest(assignment_binding.get("assignment_digest"), "assignment_digest"),
        semantic_contract_digest=_digest(semantic_contract_digest, "semantic_contract_digest"),
        input_manifest_digest=binding.input_manifest_digest,
        review_content_digest=binding.author_content_digest,
    )
    capture = _retained_capture(evidence["retained_capture"])
    if capture != {
        "provider_request": binding.provider_request,
        "provider_response": binding.provider_response,
        "raw_transcript": binding.raw_transcript,
    }:
        raise QualificationIdentityError(
            "Retained case-author capture does not encode its exact inputs and certificate."
        )
    return evidence


def validate_certificate_reveal_evidence(
    value: Mapping[str, Any],
    *,
    registry: Mapping[str, Any],
    case_id: str,
    assignment_digest: str,
    runner_freeze_digest: str,
    certificate_digest: str,
    blind_review_digests: Sequence[str],
    completion_receipts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Verify the registrar event that opens a certificate after both blind completions."""

    frozen_registry = validate_identity_registry(registry)
    evidence = _self_digested(value, "reveal_evidence_digest")
    _exact_keys(
        evidence,
        {
            "artifact_kind",
            "reveal_evidence_version",
            "identity_registry_digest",
            "reveal_event",
            "qualification_authority",
            "reveal_evidence_digest",
        },
        "certificate reveal evidence",
    )
    if (
        evidence["artifact_kind"] != "qualification_certificate_reveal_evidence"
        or evidence["reveal_evidence_version"] != SESSION_RECEIPT_VERSION
        or evidence["identity_registry_digest"] != frozen_registry["identity_registry_digest"]
        or evidence["qualification_authority"] != "none_certificate_reveal_evidence_only"
    ):
        raise QualificationIdentityError(
            "Certificate reveal evidence is not frozen-registry evidence."
        )
    if len(blind_review_digests) != 2 or len(completion_receipts) != 2:
        raise QualificationIdentityError("Certificate reveal requires two blind completions.")
    sorted_reviews = sorted(_digest(item, "blind_review_digest") for item in blind_review_digests)
    completions = [dict(item) for item in completion_receipts]
    completion_digests = sorted(semantic_digest(item) for item in completions)
    completion_indices: list[int] = []
    completion_times: list[datetime] = []
    for completion in completions:
        if (
            completion.get("artifact_kind") != "qualification_session_completion_receipt"
            or not isinstance(completion.get("event_index"), int)
            or isinstance(completion.get("event_index"), bool)
        ):
            raise QualificationIdentityError("Certificate reveal predecessor is not a completion.")
        completion_indices.append(int(completion["event_index"]))
        completion_times.append(
            _timestamp(_text(completion.get("issued_at"), "completion issued_at"))
        )
    registrar_key = _public_key(
        _text(frozen_registry["registrar_public_key_base64"], "registrar_public_key_base64")
    )
    event = _signed_receipt(
        evidence["reveal_event"],
        expected_kind="qualification_certificate_reveal_event",
        public_key=registrar_key,
    )
    expected_event = {
        "artifact_kind": "qualification_certificate_reveal_event",
        "receipt_version": SESSION_RECEIPT_VERSION,
        "case_id": case_id,
        "assignment_digest": _digest(assignment_digest, "assignment_digest"),
        "runner_freeze_digest": _digest(runner_freeze_digest, "runner_freeze_digest"),
        "certificate_digest": _text(certificate_digest, "certificate_digest"),
        "blind_review_digests": sorted_reviews,
        "completion_receipt_digests": completion_digests,
        "event_index": event["event_index"],
        "predecessor_event_digests": event["predecessor_event_digests"],
        "issued_at": event["issued_at"],
    }
    if _receipt_payload(event) != expected_event:
        raise QualificationIdentityError("Certificate reveal event binding has drifted.")
    if (
        event["predecessor_event_digests"] != completion_digests
        or event["event_index"] != max(completion_indices) + 1
    ):
        raise QualificationIdentityError("Certificate reveal event chain is not contiguous.")
    reveal_time = _timestamp(_text(event["issued_at"], "certificate reveal issued_at"))
    if reveal_time < max(completion_times):
        raise QualificationIdentityError("Certificate reveal predates a blind completion.")
    return evidence


def signed_receipt_payload(value: Mapping[str, Any]) -> bytes:
    """Return canonical bytes that a registrar signs for tests and acquisition tooling."""

    payload = dict(value)
    payload.pop("signature_base64", None)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def validate_registrar_signed_receipt(
    value: Mapping[str, Any],
    *,
    registry: Mapping[str, Any],
    expected_kind: str,
) -> dict[str, Any]:
    """Verify one exact registrar-signed receipt against a frozen identity registry."""

    frozen_registry = validate_identity_registry(registry)
    public_key = _public_key(
        _text(frozen_registry["registrar_public_key_base64"], "registrar_public_key_base64")
    )
    return _signed_receipt(
        value,
        expected_kind=_text(expected_kind, "expected receipt kind"),
        public_key=public_key,
    )


def _canonical_capture_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _signed_receipt(
    value: Any, *, expected_kind: str, public_key: Ed25519PublicKey
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise QualificationIdentityError("Signed session receipt must be an object.")
    receipt = dict(value)
    signature_text = receipt.get("signature_base64")
    if not isinstance(signature_text, str):
        raise QualificationIdentityError("Signed session receipt has no signature.")
    try:
        signature = base64.b64decode(signature_text, validate=True)
    except (binascii.Error, ValueError) as error:
        raise QualificationIdentityError("Session receipt signature is not base64.") from error
    try:
        public_key.verify(signature, signed_receipt_payload(receipt))
    except InvalidSignature as error:
        raise QualificationIdentityError("Session receipt signature is invalid.") from error
    if receipt.get("artifact_kind") != expected_kind:
        raise QualificationIdentityError("Session receipt kind is invalid.")
    return receipt


def _receipt_payload(receipt: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(receipt)
    payload.pop("signature_base64", None)
    return payload


def _retained_capture(value: Any) -> dict[str, bytes]:
    if not isinstance(value, Mapping):
        raise QualificationIdentityError("Retained session capture must be an object.")
    capture = dict(value)
    _exact_keys(
        capture,
        {"provider_request_base64", "provider_response_base64", "raw_transcript_base64"},
        "retained session capture",
    )
    result: dict[str, bytes] = {}
    for encoded_name, output_name in (
        ("provider_request_base64", "provider_request"),
        ("provider_response_base64", "provider_response"),
        ("raw_transcript_base64", "raw_transcript"),
    ):
        encoded = capture[encoded_name]
        if not isinstance(encoded, str):
            raise QualificationIdentityError("Retained session capture is not base64 text.")
        try:
            payload = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as error:
            raise QualificationIdentityError("Retained session capture is not base64.") from error
        if not payload or len(payload) > MAX_CAPTURE_BYTES:
            raise QualificationIdentityError("Retained session capture violates its byte budget.")
        result[output_name] = payload
    return result


def _case_inventory(value: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    inventory = [dict(item) for item in value]
    paths: list[str] = []
    for item in inventory:
        _exact_keys(item, {"path", "size", "sha256", "mode"}, "case-author inventory item")
        path = _text(item["path"], "case-author inventory path")
        if (
            "\\" in path
            or path.startswith("/")
            or any(part in {"", ".", ".."} for part in path.split("/"))
        ):
            raise QualificationIdentityError(
                "Case-author inventory paths must be canonical relative POSIX paths."
            )
        if (
            not isinstance(item["size"], int)
            or isinstance(item["size"], bool)
            or item["size"] < 0
            or not isinstance(item["mode"], int)
            or isinstance(item["mode"], bool)
            or not 0 <= item["mode"] <= 0o7777
        ):
            raise QualificationIdentityError("Case-author inventory metadata is invalid.")
        _digest(item["sha256"], "case-author inventory sha256")
        paths.append(path)
    if not inventory or paths != sorted(set(paths)):
        raise QualificationIdentityError(
            "Case-author inventory must be non-empty, unique, and sorted."
        )
    return inventory


def _credential(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise QualificationIdentityError("Registry credential must be an object.")
    credential = dict(value)
    _exact_keys(
        credential,
        {
            "credential_id",
            "actor_id",
            "provider",
            "public_key_base64",
            "eligible_roles",
            "active",
        },
        "registry credential",
    )
    for field in ("credential_id", "actor_id", "provider", "public_key_base64"):
        _text(credential[field], field)
    roles = credential["eligible_roles"]
    if (
        not isinstance(roles, list)
        or not roles
        or not all(isinstance(item, str) and item for item in roles)
        or roles != sorted(set(roles))
    ):
        raise QualificationIdentityError("Credential roles are not canonical.")
    if credential["active"] is not True:
        raise QualificationIdentityError("Registry contains an inactive credential.")
    _public_key(str(credential["public_key_base64"]))
    return credential


def _registered_credential(registry: Mapping[str, Any], credential_id: str) -> dict[str, Any]:
    credentials = [
        item
        for item in registry["credentials"]
        if isinstance(item, dict) and item.get("credential_id") == credential_id
    ]
    if len(credentials) != 1:
        raise QualificationIdentityError("Session credential is not uniquely registered.")
    return credentials[0]


def _public_key(value: str) -> Ed25519PublicKey:
    try:
        payload = base64.b64decode(value, validate=True)
        return Ed25519PublicKey.from_public_bytes(payload)
    except (binascii.Error, ValueError) as error:
        raise QualificationIdentityError("Registry public key is invalid.") from error


def _self_digested(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    supplied = result.pop(field, None)
    if supplied != semantic_digest(result):
        raise QualificationIdentityError(f"{field} does not replay.")
    result[field] = supplied
    return result


def _digest(value: Any, label: str) -> str:
    text = _text(value, label)
    if not text.startswith("sha256:") or len(text) != 71:
        raise QualificationIdentityError(f"{label} must be a SHA-256 digest.")
    try:
        int(text[7:], 16)
    except ValueError as error:
        raise QualificationIdentityError(f"{label} must be a SHA-256 digest.") from error
    return text


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise QualificationIdentityError("Timestamp is invalid.") from error
    if parsed.tzinfo is None:
        raise QualificationIdentityError("Timestamp requires a timezone.")
    return parsed.astimezone(UTC)


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\n" in value or "\r" in value:
        raise QualificationIdentityError(f"{label} must be non-empty one-line text.")
    return value


def _exact_keys(value: Mapping[str, Any], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise QualificationIdentityError(f"{label} has an unsupported shape.")


__all__ = [
    "IDENTITY_REGISTRY_VERSION",
    "SESSION_RECEIPT_VERSION",
    "QualificationIdentityError",
    "signed_receipt_payload",
    "validate_case_author_session_identity_evidence",
    "validate_certificate_reveal_evidence",
    "validate_identity_registry",
    "validate_provider_session_identity_evidence",
    "validate_registrar_signed_receipt",
]
