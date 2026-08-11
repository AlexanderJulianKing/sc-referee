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


# Deliberately empty in Round 2, Stages 7-8. Installing authority is a later,
# separately reviewed operation; project inputs cannot populate this table.
GRANT_PINS: Mapping[str, GrantPin] = MappingProxyType({})


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
    """Return controller-installed qualification records for ``pin``.

    Stages 7-8 intentionally install no record source. Keeping this loader
    closed prevents project-supplied qualification records from becoming an
    authority channel; a later stage must replace it with reviewed resources.
    """

    del pin
    return None
