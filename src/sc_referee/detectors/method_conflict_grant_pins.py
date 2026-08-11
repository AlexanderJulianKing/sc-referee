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


_DEPENDENCE_PIN = GrantPin(
    binding_id=(
        "method-conflict-binding:authorized-independent-unit-entry-into-row-independent-"
        "procedure-v1"
    ),
    binding_digest="sha256:56e8ccdef15d3c2371864e02cab92becb0c6859091ee782c94be2ac9b4b1a43d",
    check_id="check:authorized-independent-unit-entry-into-row-independent-procedure",
    check_version="1.1.0",
    check_manifest_digest=(
        "sha256:4f48a3104693cd6cdcf215bd620b59449ee87c3cd969ddbe7285f168e598ab21"
    ),
    detector_id="detector:bounded-analysis-method-conflict",
    detector_version="0.3.0",
    detector_manifest_digest=(
        "sha256:9c6270f47a2ab2d2a75183a9e4a2d2a955974e5968bacc2ba75778a1ae8ab3fb"
    ),
    qualification_id="qualification:authorized-independent-unit-entry-v110-round2",
    qualification_digest=(
        "sha256:a9114559f7b4ba0b75d704f0b6ba746e2150a8cb32da0cf3e8a9e975c541f9ba"
    ),
    metric_set_id="qualification-metric-set:ca098eea52a6cb1d4e62",
    metric_set_digest=("sha256:27ac7cc5d1112661cef27a88694fef711f62877213f791e44a614ff52953f1ed"),
    threshold_policy_digest=(
        "sha256:92af51be5f6d5e5127337963025cf0932747b4a088e7376f6d22d9d68d0ff644"
    ),
    exam_adapter_identity=(
        ExamAdapterIdentity(
            adapter_id=(
                "adapter:authorized-independent-unit-entry-into-row-independent-procedure:"
                "dependence-semantic-v1"
            ),
            adapter_version="1.1.0",
            implementation_digest=(
                "sha256:d5d22803d309ddda51651bcc033cb3e5aa4e093988550fb489b7e9671e289c54"
            ),
            manifest_digest=(
                "sha256:81df54974a949648f6f86287df725c1a69ce63f41100480d299680f92eee3776"
            ),
            recognition_grammar_digest=(
                "sha256:bb3b283145ec1420491771ca49fbd2214e553602a735af2a6f7027980c8be873"
            ),
        ),
    ),
    absolute_missed_roots=0,
    required_roots=2,
)

_COMPLETE_DOMAIN_PIN = GrantPin(
    binding_id="method-conflict-binding:complete-domain-exposure-denominator-v1",
    binding_digest="sha256:d67b3bb459c32f84f4d920cffc9b56ab68d96741932bf3771926070342ff94e2",
    check_id="check:complete-domain-exposure-denominator",
    check_version="2.0.7",
    check_manifest_digest=(
        "sha256:c3ef7acd8597c86e8a121ba43e94d4f2a2993c08cd2c14981b85b13c431841a9"
    ),
    detector_id="detector:bounded-analysis-method-conflict",
    detector_version="0.3.0",
    detector_manifest_digest=(
        "sha256:9c6270f47a2ab2d2a75183a9e4a2d2a955974e5968bacc2ba75778a1ae8ab3fb"
    ),
    qualification_id="qualification:complete-domain-exposure-denominator-v207-round2",
    qualification_digest=(
        "sha256:3a44dbdb144c152b7185c0dccc6bf855346093341324acfd443689982dd02dbe"
    ),
    metric_set_id="qualification-metric-set:cbb01f0b08e407f6a4f8",
    metric_set_digest=("sha256:50fda7205c683b49fc42351de25c7b98a46bd8ef62b7ca9379703c55e12e67a1"),
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
        pin.binding_id,
        pin.binding_digest,
        pin.check_id,
        pin.check_version,
        pin.check_manifest_digest,
        pin.detector_id,
        pin.detector_version,
        pin.detector_manifest_digest,
    ) == (
        binding.binding_id,
        binding.binding_digest,
        binding.check_id,
        binding.check_version,
        binding.check_manifest_digest,
        binding.detector_id,
        binding.detector_version,
        binding.detector_manifest_digest,
    ) and live_adapter_identity(binding) == pin.exam_adapter_identity


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
    return {
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
