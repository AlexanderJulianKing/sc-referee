from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ErrorCode(StrEnum):
    PARSER_UNSUPPORTED = "parser_unsupported"
    PARSER_MALFORMED_SOURCE = "parser_malformed_source"
    PARSER_DEFECT = "parser_defect"
    ASSET_MISSING = "asset_missing"
    OPAQUE_OPERATION = "opaque_operation"
    MATERIAL_UNKNOWN = "material_unknown"
    DETECTOR_NOT_APPLICABLE = "detector_not_applicable"
    DETECTOR_ABSTAINED = "detector_abstained"
    DETECTOR_DEFECT = "detector_defect"
    DEADLINE_EXHAUSTED = "deadline_exhausted"
    HOST_MODEL_LIMIT = "host_model_limit"
    SANDBOX_UNAVAILABLE = "sandbox_unavailable"
    CONTROLLER_INTEGRITY_FAILURE = "controller_integrity_failure"


class ScRefereeError(RuntimeError):
    """Base class for controller errors."""


class InvalidTransitionError(ScRefereeError):
    """Raised when the controller attempts an illegal state transition."""


class DeadlineExceededError(ScRefereeError):
    """Raised when user-visible elapsed time exceeds the hard deadline."""


class CancellationRequestedError(ScRefereeError):
    """Raised after a requested cancellation has been durably checkpointed."""


class HostModelLimitError(ScRefereeError):
    """Raised after host-model exhaustion has been durably checkpointed."""


class RecordValidationError(ScRefereeError):
    """Raised when a record fails its declared schema."""


@dataclass(frozen=True)
class TypedFailure:
    code: ErrorCode
    message: str
    affected_path: str | None = None
    recoverable: bool = True
