from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from sc_referee.scientific_checks.core import MethodConflictBinding


@dataclass(frozen=True, order=True)
class ExamAdapterIdentity:
    """Exact adapter bytes and recognition grammar examined for one grant."""

    adapter_id: str
    adapter_version: str
    implementation_digest: str
    manifest_digest: str
    recognition_grammar_digest: str


@dataclass(frozen=True)
class GrantPin:
    """Controller-installed authority for one exact qualified detector binding."""

    binding_id: str
    binding_digest: str
    check_id: str
    check_version: str
    check_manifest_digest: str
    detector_id: str
    detector_version: str
    detector_manifest_digest: str
    qualification_id: str
    qualification_digest: str
    metric_set_id: str
    metric_set_digest: str
    threshold_policy_digest: str
    exam_adapter_identity: tuple[ExamAdapterIdentity, ...]
    absolute_missed_roots: int
    required_roots: int
    finding_profile_id: str | None = None
    finding_profile_digest: str | None = None


_DEPENDENCE_PIN = GrantPin(
    binding_id=(
        "method-conflict-binding:authorized-independent-unit-entry-into-row-independent-"
        "procedure-v1"
    ),
    binding_digest="sha256:80e37baf47ba77f004441c4ca1d2daa7c8cc3b0b36d0cd33a0e334ddab7b58c0",
    check_id="check:authorized-independent-unit-entry-into-row-independent-procedure",
    check_version="3.1.0",
    check_manifest_digest=(
        "sha256:32831f748957b38eacceac8ea517612d49ad57b20562f4df072fd1f25a4df84a"
    ),
    detector_id="detector:bounded-code-csv-dependence-conflict",
    detector_version="3.1.0",
    detector_manifest_digest=(
        "sha256:43f5e88223dcd86af5b66baf41f0b6991ea28c782f3700dd224615e9c7085292"
    ),
    qualification_id="qualification:authorized-independent-unit-entry-v310-code-csv-envelope9",
    qualification_digest=(
        "sha256:a25edd25e5198a75d436a335313c7e40a695bac63860bc0e3af4ebb9b01b33f0"
    ),
    metric_set_id="qualification-metric-set:1f26a5f74b12d8750ebc",
    metric_set_digest=("sha256:494ee752e8a62770f444f62c5b1b317b52477ea2ad03c3a922e4285830a53f41"),
    threshold_policy_digest=(
        "sha256:819973ff04ad136c7b80bb23cb46ab67b5cfd3d3384656488094950498291d57"
    ),
    exam_adapter_identity=(
        ExamAdapterIdentity(
            adapter_id=(
                "adapter:authorized-independent-unit-entry-into-row-independent-procedure:"
                "code-csv-rowwise-two-sample-v1"
            ),
            adapter_version="3.1.0",
            implementation_digest=(
                "sha256:6900611a3ef6c06be5740df14333eac5d789c6c93165b8826c796a8b4de87170"
            ),
            manifest_digest=(
                "sha256:1523cb97fba6c235bb98912483dedb18ef598e61eaecc646eb428aa33bfa1a8d"
            ),
            recognition_grammar_digest=(
                "sha256:69256d48b46f16d7c144e01d5b4509470e9b187bf3db4f7e259d782459c2d476"
            ),
        ),
    ),
    absolute_missed_roots=0,
    required_roots=6,
    finding_profile_id="method-conflict-finding:code-csv-authorized-unit-requirement-conflict-v2",
    finding_profile_digest=(
        "sha256:1dad7c14985fbfb89a7f8fe24a5e7f36d07a7c9fc6f76b4d14951cc71337c04a"
    ),
)

_COMPLETE_DOMAIN_PIN = GrantPin(
    binding_id="method-conflict-binding:complete-domain-exposure-denominator-v1",
    binding_digest="sha256:48b5c2ea1ed1f376af6d5aa729078ed15f1cff4d54c04a8c161937474bc934ab",
    check_id="check:complete-domain-exposure-denominator",
    check_version="2.0.7",
    check_manifest_digest=(
        "sha256:c3ef7acd8597c86e8a121ba43e94d4f2a2993c08cd2c14981b85b13c431841a9"
    ),
    detector_id="detector:bounded-analysis-method-conflict",
    detector_version="0.3.0",
    detector_manifest_digest=(
        "sha256:df91936c23c9d7b56fcd483cf1aa053b8377e233b596c9f81424b5a26095015a"
    ),
    qualification_id="qualification:complete-domain-exposure-denominator-v207-round2",
    qualification_digest=(
        "sha256:562586ca6225eb91f665983c532da7ca3285723cec345a341df95f659ed602fe"
    ),
    metric_set_id="qualification-metric-set:329715c3cf01ed499eb5",
    metric_set_digest=("sha256:4c607d0df8c93c327e35ff954a70a41e47211782893a98c4d3797f9d951c129e"),
    threshold_policy_digest=(
        "sha256:fcf27c8d4d315fe836e0d35356ecadc496be4e53b607617d18c8c4bd670efc80"
    ),
    exam_adapter_identity=(
        ExamAdapterIdentity(
            adapter_id="adapter:complete-domain-exposure-denominator:quantity-consistency-v1",
            adapter_version="2.0.7",
            implementation_digest=(
                "sha256:cb6de94e39efdf726cc516178b77b85443044415b72c8671025ef9c2e6eef05c"
            ),
            manifest_digest=(
                "sha256:231046e541e1e84671b7fe716a2454c67d2d931f1cfe432e7de80512987d3a20"
            ),
            recognition_grammar_digest=(
                "sha256:c757692071a6925a5ca5e409dc0ad79f7421fcdbc93fb15c14efb30050524362"
            ),
        ),
    ),
    absolute_missed_roots=0,
    required_roots=2,
)


# This closed table is controller code. Project records cannot populate or alter it.
GRANT_PINS: Mapping[str, GrantPin] = MappingProxyType(
    {
        pin.binding_id: pin
        for pin in sorted((_DEPENDENCE_PIN, _COMPLETE_DOMAIN_PIN), key=lambda item: item.binding_id)
    }
)


def live_adapter_identity(
    binding: MethodConflictBinding,
) -> tuple[ExamAdapterIdentity, ...] | None:
    """Recompute the adapter identity for the live check named by ``binding``."""

    from sc_referee.scientific_checks.profiles import scientific_check_release_registry

    registry = scientific_check_release_registry()
    modules = [
        module
        for module in registry.modules
        if module.manifest.check_id == binding.check_id
        and module.manifest.check_version == binding.check_version
        and module.manifest.manifest_digest == binding.check_manifest_digest
    ]
    if len(modules) != 1:
        return None
    identities = tuple(
        sorted(
            (
                ExamAdapterIdentity(
                    adapter_id=adapter.adapter_id,
                    adapter_version=adapter.adapter_version,
                    implementation_digest=adapter.implementation_digest,
                    manifest_digest=adapter.manifest_digest,
                    recognition_grammar_digest=adapter.recognition_grammar_digest,
                )
                for adapter in modules[0].adapter_manifests
            ),
            key=lambda item: item.adapter_id,
        )
    )
    return identities or None


def installed_pin_matches_live_identity(pin: GrantPin) -> bool:
    """Recheck an installed pin against the live binding and adapter registry."""

    from sc_referee.scientific_checks.profiles import scientific_check_release_registry

    registry = scientific_check_release_registry()
    bindings = [
        item for item in registry.method_conflict_bindings if item.binding_id == pin.binding_id
    ]
    if len(bindings) != 1:
        return False
    binding = bindings[0]
    return (
        (
            pin.binding_id,
            pin.binding_digest,
            pin.check_id,
            pin.check_version,
            pin.check_manifest_digest,
            pin.detector_id,
            pin.detector_version,
            pin.detector_manifest_digest,
        )
        == (
            binding.binding_id,
            binding.binding_digest,
            binding.check_id,
            binding.check_version,
            binding.check_manifest_digest,
            binding.detector_id,
            binding.detector_version,
            binding.detector_manifest_digest,
        )
        and live_adapter_identity(binding) == pin.exam_adapter_identity
        and _finding_profile_matches(pin)
    )


def _finding_profile_matches(pin: GrantPin) -> bool:
    if pin.finding_profile_id is None and pin.finding_profile_digest is None:
        return True
    from sc_referee.detectors.method_conflict_finding import (
        CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST,
        CODE_CSV_DEPENDENCE_FINDING_PROFILE_ID,
        CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST,
        CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID,
        REPORT_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST,
        REPORT_CSV_DEPENDENCE_FINDING_PROFILE_ID,
    )

    if pin.detector_id == "detector:bounded-code-csv-dependence-conflict":
        expected = (
            (CODE_CSV_DEPENDENCE_FINDING_PROFILE_ID, CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST)
            if pin.detector_version == "2.1.0"
            else (
                CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID,
                CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST,
            )
            if pin.detector_version in {"2.3.0", "3.0.0", "3.1.0"}
            else None
        )
        return (
            expected is not None
            and pin.finding_profile_id == expected[0]
            and pin.finding_profile_digest == expected[1]
        )
    return (
        pin.finding_profile_id == REPORT_CSV_DEPENDENCE_FINDING_PROFILE_ID
        and pin.finding_profile_digest == REPORT_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST
    )


def load_method_conflict_grant_evidence(
    pin: GrantPin,
) -> tuple[Mapping[str, object], Mapping[str, object]] | None:
    """Return the exact controller-installed qualification records for ``pin``."""

    from sc_referee.qualification_grants import (
        QualificationGrantResourceError,
        load_installed_qualification_grants,
    )

    installed = GRANT_PINS.get(pin.binding_id)
    if installed != pin or not installed_pin_matches_live_identity(pin):
        return None
    try:
        evidence = load_installed_qualification_grants().get(pin.binding_id)
    except (OSError, QualificationGrantResourceError):
        return None
    if evidence is None or dict(evidence.grant) != _pin_payload(pin):
        return None
    return dict(evidence.qualification), dict(evidence.metric_set)


def _pin_payload(pin: GrantPin) -> dict[str, object]:
    value: dict[str, object] = {
        "absolute_missed_roots": pin.absolute_missed_roots,
        "binding_digest": pin.binding_digest,
        "binding_id": pin.binding_id,
        "check_id": pin.check_id,
        "check_manifest_digest": pin.check_manifest_digest,
        "check_version": pin.check_version,
        "detector_id": pin.detector_id,
        "detector_manifest_digest": pin.detector_manifest_digest,
        "detector_version": pin.detector_version,
        "exam_adapter_identity": [
            {
                "adapter_id": item.adapter_id,
                "adapter_version": item.adapter_version,
                "implementation_digest": item.implementation_digest,
                "manifest_digest": item.manifest_digest,
                "recognition_grammar_digest": item.recognition_grammar_digest,
            }
            for item in pin.exam_adapter_identity
        ],
        "metric_set_digest": pin.metric_set_digest,
        "metric_set_id": pin.metric_set_id,
        "qualification_digest": pin.qualification_digest,
        "qualification_id": pin.qualification_id,
        "required_roots": pin.required_roots,
        "threshold_policy_digest": pin.threshold_policy_digest,
    }
    if pin.finding_profile_id is not None or pin.finding_profile_digest is not None:
        if not pin.finding_profile_id or not pin.finding_profile_digest:
            return {}
        value["finding_profile_id"] = pin.finding_profile_id
        value["finding_profile_digest"] = pin.finding_profile_digest
    return value
