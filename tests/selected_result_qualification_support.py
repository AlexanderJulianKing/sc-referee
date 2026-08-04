from __future__ import annotations

import base64
import json
import stat
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from sc_referee_evaluation.qualification_identity import (
    case_author_session_binding,
    signed_receipt_payload,
)

from sc_referee.core.ids import semantic_digest, sha256_digest


def build_test_identity_registry(
    actors: Sequence[tuple[str, str]],
) -> tuple[dict[str, Any], dict[str, Ed25519PrivateKey]]:
    keys: dict[str, Ed25519PrivateKey] = {}
    registrar_private_key = Ed25519PrivateKey.generate()
    registrar_public_bytes = registrar_private_key.public_key().public_bytes(
        Encoding.Raw, PublicFormat.Raw
    )
    credentials: list[dict[str, Any]] = []
    for actor_id, provider in actors:
        private_key = Ed25519PrivateKey.generate()
        keys[actor_id] = registrar_private_key
        public_bytes = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        credentials.append(
            {
                "credential_id": f"credential:{actor_id}",
                "actor_id": actor_id,
                "provider": provider,
                "public_key_base64": base64.b64encode(public_bytes).decode("ascii"),
                "eligible_roles": [
                    "case-author" if actor_id == "case-author" else "semantic-reviewer"
                ],
                "active": True,
            }
        )
    credentials.sort(key=lambda item: str(item["credential_id"]))
    registry: dict[str, Any] = {
        "artifact_kind": "qualification_identity_registry",
        "identity_registry_version": "1.1.0",
        "registrar_id": "test-registrar",
        "registrar_public_key_base64": base64.b64encode(registrar_public_bytes).decode("ascii"),
        "credentials": credentials,
        "frozen_at": "2026-08-04T19:00:00Z",
        "qualification_authority": "none_identity_registry_only",
    }
    registry["identity_registry_digest"] = semantic_digest(registry)
    registry["registrar_signature_base64"] = base64.b64encode(
        registrar_private_key.sign(signed_receipt_payload(registry))
    ).decode("ascii")
    return registry, keys


def build_test_provider_session_evidence(
    *,
    registry: Mapping[str, Any],
    private_key: Ed25519PrivateKey,
    actor_id: str,
    provider: str,
    execution_context_id: str,
    case_id: str,
    target_packet: Mapping[str, Any],
    assignment_binding: Mapping[str, Any],
    runner_freeze_digest: str,
    semantic_contract: Mapping[str, Any],
    case_root: Path,
    semantic_conclusion: Mapping[str, Any],
    binding_evidence: Mapping[str, Any] | None,
    rule_trace: Sequence[Mapping[str, Any]],
    independence_declaration: Mapping[str, Any],
    index: int,
) -> tuple[dict[str, str], dict[str, Any]]:
    inventory = []
    for path in sorted(item for item in case_root.rglob("*") if item.is_file()):
        payload = path.read_bytes()
        inventory.append(
            {
                "path": path.relative_to(case_root).as_posix(),
                "size": len(payload),
                "sha256": sha256_digest(payload),
                "mode": stat.S_IMODE(path.lstat().st_mode),
            }
        )
    input_manifest_digest = semantic_digest(
        {
            "case_inventory": inventory,
            "target_packet": dict(target_packet),
            "assignment_binding": dict(assignment_binding),
            "runner_freeze_digest": runner_freeze_digest,
            "semantic_contract_digest": semantic_contract["contract_digest"],
        }
    )
    review_content_digest = semantic_digest(
        {
            "input_manifest_digest": input_manifest_digest,
            "semantic_conclusion": dict(semantic_conclusion),
            "binding_evidence": dict(binding_evidence) if binding_evidence is not None else None,
            "rule_trace": [dict(item) for item in rule_trace],
            "independence_declaration": dict(independence_declaration),
        }
    )
    launch: dict[str, Any] = {
        "artifact_kind": "qualification_session_launch_receipt",
        "receipt_version": "1.1.0",
        "credential_id": f"credential:{actor_id}",
        "actor_id": actor_id,
        "provider": provider,
        "execution_context_id": execution_context_id,
        "role": "semantic-reviewer",
        "case_id": case_id,
        "target_packet_digest": semantic_digest(dict(target_packet)),
        "assignment_digest": assignment_binding["assignment_digest"],
        "semantic_contract_digest": semantic_contract["contract_digest"],
        "input_manifest_digest": input_manifest_digest,
        "session_nonce": f"nonce:{actor_id}:{index}",
        "event_index": index * 2,
        "predecessor_event_digest": "sha256:" + str(index) * 64,
        "issued_at": f"2026-08-04T19:4{index}:00Z",
    }
    launch["signature_base64"] = base64.b64encode(
        private_key.sign(signed_receipt_payload(launch))
    ).decode("ascii")
    launch_digest = semantic_digest(launch)
    provider_request = json.dumps(
        {"target_packet": dict(target_packet), "input_manifest_digest": input_manifest_digest},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    provider_response = json.dumps(
        {"actor_id": actor_id, "semantic_conclusion": dict(semantic_conclusion)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    raw_transcript = provider_request + b"\n" + provider_response
    completion: dict[str, Any] = {
        "artifact_kind": "qualification_session_completion_receipt",
        "receipt_version": "1.1.0",
        "credential_id": f"credential:{actor_id}",
        "actor_id": actor_id,
        "provider": provider,
        "execution_context_id": execution_context_id,
        "role": "semantic-reviewer",
        "case_id": case_id,
        "launch_receipt_digest": launch_digest,
        "provider_request_id": f"request:{actor_id}:{index}",
        "provider_request_digest": sha256_digest(provider_request),
        "provider_response_digest": sha256_digest(provider_response),
        "raw_transcript_digest": sha256_digest(raw_transcript),
        "review_content_digest": review_content_digest,
        "event_index": index * 2 + 1,
        "predecessor_event_digest": launch_digest,
        "issued_at": f"2026-08-04T19:5{index}:00Z",
    }
    completion["signature_base64"] = base64.b64encode(
        private_key.sign(signed_receipt_payload(completion))
    ).decode("ascii")
    evidence: dict[str, Any] = {
        "artifact_kind": "provider_session_identity_evidence",
        "identity_evidence_version": "1.1.0",
        "identity_registry_digest": registry["identity_registry_digest"],
        "credential_id": f"credential:{actor_id}",
        "launch_receipt": launch,
        "completion_receipt": completion,
        "retained_capture": {
            "provider_request_base64": base64.b64encode(provider_request).decode("ascii"),
            "provider_response_base64": base64.b64encode(provider_response).decode("ascii"),
            "raw_transcript_base64": base64.b64encode(raw_transcript).decode("ascii"),
        },
        "authentication_method": "registrar_ed25519_signed_session_with_retained_capture",
        "qualification_authority": "none_identity_evidence_only",
    }
    evidence["identity_evidence_digest"] = semantic_digest(evidence)
    identity = {
        "actor_id": actor_id,
        "provider": provider,
        "execution_context_id": execution_context_id,
        "identity_evidence_digest": evidence["identity_evidence_digest"],
    }
    return identity, evidence


def build_test_case_author_session_evidence(
    *,
    registry: Mapping[str, Any],
    private_key: Ed25519PrivateKey,
    actor_id: str,
    provider: str,
    execution_context_id: str,
    case_id: str,
    target_packet: Mapping[str, Any],
    assignment_binding: Mapping[str, Any],
    runner_freeze_digest: str,
    semantic_contract: Mapping[str, Any],
    case_root: Path,
    construction_certificate: Mapping[str, Any],
    index: int = 0,
) -> tuple[dict[str, str], dict[str, Any]]:
    inventory = []
    for path in sorted(item for item in case_root.rglob("*") if item.is_file()):
        payload = path.read_bytes()
        inventory.append(
            {
                "path": path.relative_to(case_root).as_posix(),
                "size": len(payload),
                "sha256": sha256_digest(payload),
                "mode": stat.S_IMODE(path.lstat().st_mode),
            }
        )
    binding = case_author_session_binding(
        case_id=case_id,
        target_packet=target_packet,
        assignment_binding=assignment_binding,
        runner_freeze_digest=runner_freeze_digest,
        semantic_contract_digest=str(semantic_contract["contract_digest"]),
        case_inventory=inventory,
        construction_certificate=construction_certificate,
    )
    launch: dict[str, Any] = {
        "artifact_kind": "qualification_session_launch_receipt",
        "receipt_version": "1.1.0",
        "credential_id": f"credential:{actor_id}",
        "actor_id": actor_id,
        "provider": provider,
        "execution_context_id": execution_context_id,
        "role": "case-author",
        "case_id": case_id,
        "target_packet_digest": semantic_digest(dict(target_packet)),
        "assignment_digest": assignment_binding["assignment_digest"],
        "semantic_contract_digest": semantic_contract["contract_digest"],
        "input_manifest_digest": binding.input_manifest_digest,
        "session_nonce": f"nonce:{actor_id}:{index}",
        "event_index": index * 2,
        "predecessor_event_digest": "sha256:" + str(index) * 64,
        "issued_at": "2026-08-04T19:30:00Z",
    }
    launch["signature_base64"] = base64.b64encode(
        private_key.sign(signed_receipt_payload(launch))
    ).decode("ascii")
    launch_digest = semantic_digest(launch)
    completion: dict[str, Any] = {
        "artifact_kind": "qualification_session_completion_receipt",
        "receipt_version": "1.1.0",
        "credential_id": f"credential:{actor_id}",
        "actor_id": actor_id,
        "provider": provider,
        "execution_context_id": execution_context_id,
        "role": "case-author",
        "case_id": case_id,
        "launch_receipt_digest": launch_digest,
        "provider_request_id": f"request:{actor_id}:{index}",
        "provider_request_digest": sha256_digest(binding.provider_request),
        "provider_response_digest": sha256_digest(binding.provider_response),
        "raw_transcript_digest": sha256_digest(binding.raw_transcript),
        "review_content_digest": binding.author_content_digest,
        "event_index": index * 2 + 1,
        "predecessor_event_digest": launch_digest,
        "issued_at": "2026-08-04T19:31:00Z",
    }
    completion["signature_base64"] = base64.b64encode(
        private_key.sign(signed_receipt_payload(completion))
    ).decode("ascii")
    evidence: dict[str, Any] = {
        "artifact_kind": "provider_session_identity_evidence",
        "identity_evidence_version": "1.1.0",
        "identity_registry_digest": registry["identity_registry_digest"],
        "credential_id": f"credential:{actor_id}",
        "launch_receipt": launch,
        "completion_receipt": completion,
        "retained_capture": {
            "provider_request_base64": base64.b64encode(binding.provider_request).decode("ascii"),
            "provider_response_base64": base64.b64encode(binding.provider_response).decode("ascii"),
            "raw_transcript_base64": base64.b64encode(binding.raw_transcript).decode("ascii"),
        },
        "authentication_method": "registrar_ed25519_signed_session_with_retained_capture",
        "qualification_authority": "none_identity_evidence_only",
    }
    evidence["identity_evidence_digest"] = semantic_digest(evidence)
    identity = {
        "actor_id": actor_id,
        "provider": provider,
        "execution_context_id": execution_context_id,
        "identity_evidence_digest": evidence["identity_evidence_digest"],
    }
    return identity, evidence


def build_test_certificate_reveal_evidence(
    *,
    registry: Mapping[str, Any],
    private_key: Ed25519PrivateKey,
    case_id: str,
    assignment_digest: str,
    runner_freeze_digest: str,
    certificate_digest: str,
    blind_reviews: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    completions = [
        dict(review["validator_identity_evidence"]["completion_receipt"])
        for review in blind_reviews
    ]
    completion_digests = sorted(semantic_digest(item) for item in completions)
    event: dict[str, Any] = {
        "artifact_kind": "qualification_certificate_reveal_event",
        "receipt_version": "1.1.0",
        "case_id": case_id,
        "assignment_digest": assignment_digest,
        "runner_freeze_digest": runner_freeze_digest,
        "certificate_digest": certificate_digest,
        "blind_review_digests": sorted(
            str(review["blind_review_digest"]) for review in blind_reviews
        ),
        "completion_receipt_digests": completion_digests,
        "event_index": max(int(item["event_index"]) for item in completions) + 1,
        "predecessor_event_digests": completion_digests,
        "issued_at": "2026-08-04T19:53:00Z",
    }
    event["signature_base64"] = base64.b64encode(
        private_key.sign(signed_receipt_payload(event))
    ).decode("ascii")
    evidence: dict[str, Any] = {
        "artifact_kind": "qualification_certificate_reveal_evidence",
        "reveal_evidence_version": "1.1.0",
        "identity_registry_digest": registry["identity_registry_digest"],
        "reveal_event": event,
        "qualification_authority": "none_certificate_reveal_evidence_only",
    }
    evidence["reveal_evidence_digest"] = semantic_digest(evidence)
    return evidence
