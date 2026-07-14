"""Persisted certificate schema and replayed external-status gate."""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256


class CertificateIntegrityError(ValueError):
    pass


class ClaimRootGrade(Enum):
    ACCUSATION_GRADE = "accusation_grade"
    CLEAN_ONLY = "clean_only"
    DIAGNOSTIC_ONLY = "diagnostic_only"


@dataclass(frozen=True)
class ClaimRootBinding:
    kind: str
    claim_id: str
    report_artifact_digest: str
    report_locator_digest: str
    producing_value_digest: str


@dataclass(frozen=True)
class Certificate:
    policy_id: str
    outcome: str
    max_external_status: str
    claim_root_grade: ClaimRootGrade
    claim_root_binding: ClaimRootBinding | None
    claim_root_digest: str
    claim_root_ratification: str | None
    external_fact_ratifications: tuple[str, ...]
    all_external_facts_ratified: bool
    closed_world_complete: bool
    inventory_complete: bool
    observed_report_artifact_digest: str
    observed_report_locator_digest: str
    observed_producing_value_digest: str

    def to_json(self) -> str:
        body = _certificate_dict(self)
        body["certificate_digest"] = _digest(body)
        return json.dumps(body, sort_keys=True, separators=(",", ":"))


def _certificate_dict(certificate: Certificate) -> dict[str, object]:
    value = dataclasses.asdict(certificate)
    value["claim_root_grade"] = certificate.claim_root_grade.value
    return value


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "sha256:" + sha256(payload.encode()).hexdigest()


def external_status(certificate: Certificate) -> str:
    if not certificate.inventory_complete:
        return "not_audited"
    if certificate.outcome == "CLEAN_PROOF":
        return certificate.max_external_status
    if certificate.outcome != "VIOLATION_WITNESS":
        return "needs_evidence"
    if certificate.max_external_status != "blocker":
        return certificate.max_external_status
    binding = certificate.claim_root_binding
    blocker_entitled = (
        certificate.claim_root_grade is ClaimRootGrade.ACCUSATION_GRADE
        and bool(certificate.claim_root_digest)
        and bool(certificate.claim_root_ratification)
        and certificate.claim_root_ratification in certificate.external_fact_ratifications
        and certificate.all_external_facts_ratified
        and certificate.closed_world_complete
        and binding is not None
        and binding.kind == "structured"
        and bool(binding.report_artifact_digest)
        and bool(binding.report_locator_digest)
        and bool(binding.producing_value_digest)
        and binding.report_artifact_digest == certificate.observed_report_artifact_digest
        and binding.report_locator_digest == certificate.observed_report_locator_digest
        and binding.producing_value_digest == certificate.observed_producing_value_digest
    )
    return "blocker" if blocker_entitled else "needs_evidence"


def load_certificate(payload: str) -> tuple[Certificate, str]:
    try:
        body = json.loads(payload)
        if not isinstance(body, dict):
            raise TypeError("certificate must be an object")
        stored_digest = body.pop("certificate_digest")
        if not isinstance(stored_digest, str) or stored_digest != _digest(body):
            raise CertificateIntegrityError("certificate digest mismatch")
        expected = {field.name for field in dataclasses.fields(Certificate)}
        if set(body) != expected:
            raise CertificateIntegrityError("certificate schema mismatch")
        binding_value = body["claim_root_binding"]
        if binding_value is not None and not isinstance(binding_value, dict):
            raise TypeError("claim root binding must be an object or null")
        body["claim_root_binding"] = (
            ClaimRootBinding(**binding_value) if binding_value is not None else None
        )
        body["claim_root_grade"] = ClaimRootGrade(body["claim_root_grade"])
        body["external_fact_ratifications"] = tuple(body["external_fact_ratifications"])
        certificate = Certificate(**body)
    except CertificateIntegrityError:
        raise
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise CertificateIntegrityError(f"invalid certificate: {error}") from error
    return certificate, external_status(certificate)


def build_certificate(**values) -> Certificate:
    return Certificate(**values)
