"""Evaluation-private byte oracle for selected-result verifier qualification.

This module validates construction certificates; it does not infer selected-result
semantics from project code. It deliberately has no dependency on production or
prospective parsing and verification implementations.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Literal

from sc_referee_evaluation.selected_result_qualification_io import (
    QualificationIOError,
    RootedReader,
)

OracleState = Literal["V", "A", "I", "U"]

CERTIFICATE_VERSION = "selected-result-qualification-certificate-v1"
MAX_FILES = 512
MAX_TOTAL_BYTES = 256 * 1024 * 1024
MAX_SPANS = 128
MAX_REASON_CODES = 16


class QualificationOracleError(ValueError):
    """Raised when a construction certificate cannot support an oracle result."""


@dataclass(frozen=True)
class FileCertificate:
    """Expected identity of one regular file in the complete case inventory."""

    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class SpanCertificate:
    """Expected identity of one half-open byte span in an inventoried file."""

    span_id: str
    path: str
    start: int
    end: int
    sha256: str


@dataclass(frozen=True)
class PositiveBindingCertificate:
    """References the exact retained spans that constitute a positive binding."""

    result_span_id: str
    producer_span_id: str
    operand_span_ids: tuple[str, ...]
    report_span_id: str


@dataclass(frozen=True)
class ConstructionCertificate:
    """Closed construction truth supplied independently of the verifier under test."""

    case_id: str
    expected_state: OracleState
    files: tuple[FileCertificate, ...]
    spans: tuple[SpanCertificate, ...]
    positive_binding: PositiveBindingCertificate | None
    reason_codes: tuple[str, ...]
    certificate_version: str = CERTIFICATE_VERSION
    certificate_digest: str = ""


@dataclass(frozen=True)
class VerifiedSpan:
    """A byte span whose bounds and digest were checked against the case bytes."""

    span_id: str
    path: str
    start: int
    end: int
    sha256: str


@dataclass(frozen=True)
class ExactPositiveBinding:
    """The verified byte-level description emitted only for oracle state V."""

    result: VerifiedSpan
    producer: VerifiedSpan
    operands: tuple[VerifiedSpan, ...]
    report: VerifiedSpan


@dataclass(frozen=True)
class OracleResult:
    """Closed expected result for one independently constructed qualification case."""

    case_id: str
    expected_state: OracleState
    positive_binding: ExactPositiveBinding | None
    reason_codes: tuple[str, ...]
    certificate_digest: str
    inventory_digest: str
    qualification_authority: Literal["none_tooling_only"] = "none_tooling_only"


def seal_construction_certificate(certificate: ConstructionCertificate) -> ConstructionCertificate:
    """Return a certificate carrying the digest of its semantic fields."""

    return replace(certificate, certificate_digest=_certificate_digest(certificate))


def verify_construction_certificate(
    certificate: ConstructionCertificate, case_root: Path
) -> OracleResult:
    """Verify a sealed certificate against retained bytes and emit its closed oracle state."""

    _validate_certificate_shape(certificate)
    expected_digest = _certificate_digest(certificate)
    if certificate.certificate_digest != expected_digest:
        raise QualificationOracleError("Construction certificate digest does not replay.")

    try:
        with RootedReader(case_root) as reader:
            case_tree = reader.read_case_tree(
                max_files=MAX_FILES,
                max_file_bytes=MAX_TOTAL_BYTES,
                max_total_bytes=MAX_TOTAL_BYTES,
            )
    except QualificationIOError as error:
        if "symbolic links" in str(error):
            raise QualificationOracleError("Symlinks are unsupported in case inventory.") from error
        raise QualificationOracleError(
            "Case tree could not be read as one immutable descriptor-rooted inventory."
        ) from error

    observed_paths = case_tree.paths
    expected_paths = tuple(item.path for item in certificate.files)
    if observed_paths != expected_paths:
        raise QualificationOracleError("Case file inventory differs from the certificate.")

    payloads: dict[str, bytes] = {}
    inventory_records: list[dict[str, object]] = []
    for file_certificate in certificate.files:
        payload = case_tree.read_bytes(file_certificate.path)
        actual_digest = _sha256(payload)
        if len(payload) != file_certificate.size or actual_digest != file_certificate.sha256:
            raise QualificationOracleError(f"File identity differs for {file_certificate.path!r}.")
        payloads[file_certificate.path] = payload
        inventory_records.append(
            {
                "path": file_certificate.path,
                "size": len(payload),
                "sha256": actual_digest,
            }
        )

    verified_spans: dict[str, VerifiedSpan] = {}
    for span_certificate in certificate.spans:
        payload = payloads[span_certificate.path]
        if span_certificate.end > len(payload):
            raise QualificationOracleError(
                f"Span {span_certificate.span_id!r} exceeds its file bytes."
            )
        actual_digest = _sha256(payload[span_certificate.start : span_certificate.end])
        if actual_digest != span_certificate.sha256:
            raise QualificationOracleError(
                f"Byte-span identity differs for {span_certificate.span_id!r}."
            )
        verified_spans[span_certificate.span_id] = VerifiedSpan(
            span_id=span_certificate.span_id,
            path=span_certificate.path,
            start=span_certificate.start,
            end=span_certificate.end,
            sha256=actual_digest,
        )

    binding = _verified_binding(certificate.positive_binding, verified_spans)
    return OracleResult(
        case_id=certificate.case_id,
        expected_state=certificate.expected_state,
        positive_binding=binding,
        reason_codes=certificate.reason_codes,
        certificate_digest=expected_digest,
        inventory_digest=_json_digest(inventory_records),
    )


def _validate_certificate_shape(certificate: ConstructionCertificate) -> None:
    if certificate.certificate_version != CERTIFICATE_VERSION:
        raise QualificationOracleError("Unsupported construction certificate version.")
    if not certificate.case_id or certificate.case_id.strip() != certificate.case_id:
        raise QualificationOracleError("case_id must be non-empty canonical text.")
    if certificate.expected_state not in {"V", "A", "I", "U"}:
        raise QualificationOracleError("Expected state must be one of V, A, I, or U.")
    if not certificate.files or len(certificate.files) > MAX_FILES:
        raise QualificationOracleError("File inventory is empty or exceeds its finite ceiling.")
    if len(certificate.spans) > MAX_SPANS:
        raise QualificationOracleError("Byte-span inventory exceeds its finite ceiling.")
    if len(certificate.reason_codes) > MAX_REASON_CODES:
        raise QualificationOracleError("Reason-code inventory exceeds its finite ceiling.")

    file_paths = tuple(_relative_path(item.path) for item in certificate.files)
    if file_paths != tuple(sorted(set(file_paths))):
        raise QualificationOracleError("File inventory paths must be unique and sorted.")
    for file_certificate in certificate.files:
        if file_certificate.size < 0:
            raise QualificationOracleError("File sizes cannot be negative.")
        _digest(file_certificate.sha256, "file sha256")

    span_ids: set[str] = set()
    for span_certificate in certificate.spans:
        if not span_certificate.span_id or span_certificate.span_id in span_ids:
            raise QualificationOracleError("Byte-span identifiers must be non-empty and unique.")
        span_ids.add(span_certificate.span_id)
        if _relative_path(span_certificate.path) not in file_paths:
            raise QualificationOracleError("Every byte span must reference an inventoried file.")
        if span_certificate.start < 0 or span_certificate.end <= span_certificate.start:
            raise QualificationOracleError("Byte spans must be non-empty half-open ranges.")
        _digest(span_certificate.sha256, "span sha256")

    if len(set(certificate.reason_codes)) != len(certificate.reason_codes):
        raise QualificationOracleError("Reason codes must be unique.")
    if any(not code or code.strip() != code for code in certificate.reason_codes):
        raise QualificationOracleError("Reason codes must be non-empty canonical text.")

    if certificate.expected_state == "V":
        if certificate.positive_binding is None or certificate.reason_codes:
            raise QualificationOracleError("State V requires one binding and no failure reasons.")
        _binding_span_ids(certificate.positive_binding, span_ids)
    elif certificate.positive_binding is not None or not certificate.reason_codes:
        raise QualificationOracleError("States A, I, and U require reasons and forbid a binding.")


def _verified_binding(
    binding: PositiveBindingCertificate | None,
    spans: dict[str, VerifiedSpan],
) -> ExactPositiveBinding | None:
    if binding is None:
        return None
    return ExactPositiveBinding(
        result=spans[binding.result_span_id],
        producer=spans[binding.producer_span_id],
        operands=tuple(spans[item] for item in binding.operand_span_ids),
        report=spans[binding.report_span_id],
    )


def _binding_span_ids(binding: PositiveBindingCertificate, available: set[str]) -> None:
    identifiers = (
        binding.result_span_id,
        binding.producer_span_id,
        *binding.operand_span_ids,
        binding.report_span_id,
    )
    if not binding.operand_span_ids:
        raise QualificationOracleError("A positive binding requires at least one operand span.")
    if any(identifier not in available for identifier in identifiers):
        raise QualificationOracleError("Positive binding references an undeclared byte span.")


def _relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or path.as_posix() != value:
        raise QualificationOracleError("Inventory paths must be canonical relative POSIX paths.")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise QualificationOracleError("Inventory paths cannot contain empty or dot components.")
    return value


def _digest(value: str, name: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise QualificationOracleError(f"{name} must be a lowercase SHA-256 hex digest.")
    return value


def _certificate_digest(certificate: ConstructionCertificate) -> str:
    value = asdict(certificate)
    value.pop("certificate_digest")
    return _json_digest(value)


def _json_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return _sha256(encoded)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
