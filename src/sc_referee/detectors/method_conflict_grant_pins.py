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
    binding_digest="sha256:85c270872730d6ce8cf6cc62b79a54140b2a6121d98d7be35764db6d61f5b989",
    check_id="check:authorized-independent-unit-entry-into-row-independent-procedure",
    check_version="2.1.0",
    check_manifest_digest=(
        "sha256:8b9ce5f53203c99bd0d24fcf0169e841905cb2aa034e858516bcf48105e4d6c2"
    ),
    detector_id="detector:bounded-code-csv-dependence-conflict",
    detector_version="2.1.0",
    detector_manifest_digest=(
        "sha256:8824f6c48ac7b014383967e03774b9ef227dc265fa4754f5ce79ff1571304b05"
    ),
    qualification_id="qualification:authorized-independent-unit-entry-v210-code-csv-envelope5",
    qualification_digest=(
        "sha256:0e52eb7a7661646aaf30ba4484b81d10cfb1f8cb3f86caa0e4f14c0bd5c43bbb"
    ),
    metric_set_id="qualification-metric-set:authorized-independent-unit-entry-v210-envelope5",
    metric_set_digest=("sha256:b11f7152edd1e6ea4cacd13d1c0b67ecfaf56ffbece7839246c762ec3c2909b4"),
    threshold_policy_digest=(
        "sha256:7fe65c8b07a4154c63f432112873e212568815834b9402f8dd33c8670b03d918"
    ),
    exam_adapter_identity=(
        ExamAdapterIdentity(
            adapter_id=(
                "adapter:authorized-independent-unit-entry-into-row-independent-procedure:"
                "code-csv-rowwise-two-sample-v1"
            ),
            adapter_version="2.1.0",
            implementation_digest=(
                "sha256:986f4862d5bc63cda2a61f5bf1d7df2d46e137b38de753edac5c2208f2705b54"
            ),
            manifest_digest=(
                "sha256:591a0bf3e7ca93b8166ad6a7a8779e937e48b5295b81ca0f433b02d28fc1c65c"
            ),
            recognition_grammar_digest=(
                "sha256:e135a5182ebba66ffc987f8867c468c54a9a1ab72d34f76dedee9867c4c3b10e"
            ),
        ),
    ),
    absolute_missed_roots=2,
    required_roots=6,
    finding_profile_id="method-conflict-finding:code-csv-authorized-unit-requirement-conflict-v1",
    finding_profile_digest=(
        "sha256:0440fdb918eb04ff975e7129c4152a2d681f3f4203ae8c7a1f8fc9ebf8916288"
    ),
)

_COMPLETE_DOMAIN_PIN = GrantPin(
    binding_id="method-conflict-binding:complete-domain-exposure-denominator-v1",
    binding_digest="sha256:9c7fd700782f78aa9dbc7033149ccca61255c23f551a994e6d30c42e20266600",
    check_id="check:complete-domain-exposure-denominator",
    check_version="2.0.7",
    check_manifest_digest=(
        "sha256:c3ef7acd8597c86e8a121ba43e94d4f2a2993c08cd2c14981b85b13c431841a9"
    ),
    detector_id="detector:bounded-analysis-method-conflict",
    detector_version="0.3.0",
    detector_manifest_digest=(
        "sha256:5f3c4ad77d9878a4f6d88f9db20539d2ee05be885d36f0df0a00b2ce08ea94eb"
    ),
    qualification_id="qualification:complete-domain-exposure-denominator-v207-round2",
    qualification_digest=(
        "sha256:9a5dbdc6ae3a255c6541761fa276377b384aacbfb64ae5ffe538debe38d9d6e6"
    ),
    metric_set_id="qualification-metric-set:329715c3cf01ed499eb5",
    metric_set_digest=("sha256:d6c94f419625aecd52ae0c886ac0452037e7eae14bbcfa7cb57e741b7e1ad9ed"),
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
