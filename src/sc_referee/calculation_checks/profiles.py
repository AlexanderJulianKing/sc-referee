from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sc_referee.calculation_checks.bh import (
    BH_CHECK_ID,
    DeclaredBHTableAdapter,
    SelectedSidecarBHTableAdapter,
)
from sc_referee.calculation_checks.core import (
    CalculationCheckContractError,
    CalculationCheckManifest,
    CalculationCheckModule,
    CalculationCheckRegistry,
)
from sc_referee.calculation_checks.count_model_compatibility import (
    SelectedSidecarCountModelCompatibilityAdapter,
    count_model_compatibility_registry,
)
from sc_referee.calculation_checks.design_integrity import (
    SelectedSidecarDesignIntegrityAdapter,
    design_integrity_registry,
)
from sc_referee.calculation_checks.effect_size_summary import (
    SelectedSidecarEffectSizeSummaryAdapter,
    effect_size_summary_registry,
)
from sc_referee.calculation_checks.eqtl_sign import (
    SelectedSidecarEqtlSignAdapter,
    eqtl_sign_registry,
)
from sc_referee.calculation_checks.hic_loop_strength import (
    SelectedSidecarHiCLoopStrengthAdapter,
    hic_loop_strength_registry,
)
from sc_referee.calculation_checks.selection_reuse import (
    SelectedSidecarSelectionReuseAdapter,
    selection_reuse_registry,
)
from sc_referee.calculation_checks.single_cell_sensitivity import (
    SelectedSidecarSingleCellSensitivityAdapter,
    single_cell_sensitivity_registry,
)
from sc_referee.core.ids import canonical_json, sha256_digest

_CORE_IMPLEMENTATION_DIGEST = sha256_digest(
    (Path(__file__).resolve().parent / "core.py").read_bytes()
)
_CONTEXT_IMPLEMENTATION_FILES = {
    "calculation_checks/core.py": _CORE_IMPLEMENTATION_DIGEST,
    "calculation_checks/integration.py": sha256_digest(
        (Path(__file__).resolve().parent / "integration.py").read_bytes()
    ),
    "calculation_checks/material_context.py": sha256_digest(
        (Path(__file__).resolve().parent / "material_context.py").read_bytes()
    ),
    "scientific_checks/scope_joins.py": sha256_digest(
        (
            Path(__file__).resolve().parent.parent / "scientific_checks" / "scope_joins.py"
        ).read_bytes()
    ),
}
_RELEASE_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "calculation-check-manifests-v1"
    / "registry.json"
)
_SINGLE_CELL_RELEASE_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "calculation-check-manifests-v2"
    / "registry.json"
)
_SINGLE_CELL_RELEASE_MANIFEST_V9 = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "calculation-check-manifests-v9"
    / "registry.json"
)
_EFFECT_SIZE_RELEASE_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "calculation-check-manifests-v3"
    / "registry.json"
)
_DESIGN_INTEGRITY_RELEASE_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "calculation-check-manifests-v4"
    / "registry.json"
)
_COUNT_MODEL_RELEASE_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "calculation-check-manifests-v5"
    / "registry.json"
)
_SELECTION_REUSE_RELEASE_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "calculation-check-manifests-v6"
    / "registry.json"
)
_EQTL_SIGN_RELEASE_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "calculation-check-manifests-v7"
    / "registry.json"
)
_HIC_LOOP_RELEASE_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "calculation-check-manifests-v8"
    / "registry.json"
)
_GENERALIZED_RELEASE_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "calculation-check-manifests-v10"
    / "registry.json"
)


def calculation_check_release_registry() -> CalculationCheckRegistry:
    check = CalculationCheckManifest(
        check_id=BH_CHECK_ID,
        check_version="1.0.0",
        implementation_digest=_CORE_IMPLEMENTATION_DIGEST,
        comparison_relation="benjamini_hochberg_complete_family_conformance",
        output_ceiling="disclosure_only",
        permitted_wording=(
            "The explicitly declared complete-family BH outputs do not equal the auditor's "
            "bounded exact-decimal recomputation."
        ),
    )
    return CalculationCheckRegistry(
        modules=(CalculationCheckModule(check, (DeclaredBHTableAdapter(),)),)
    )


def default_calculation_check_registry() -> CalculationCheckRegistry:
    base = calculation_check_release_registry()
    single_cell = single_cell_sensitivity_registry()
    effect_size = effect_size_summary_registry()
    design_integrity = design_integrity_registry()
    count_model = count_model_compatibility_registry()
    selection_reuse = selection_reuse_registry()
    eqtl_sign = eqtl_sign_registry()
    hic_loop = hic_loop_strength_registry()
    verify_calculation_check_release_manifest(base)
    verify_single_cell_calculation_release_manifest_v9(single_cell)
    verify_effect_size_calculation_release_manifest(effect_size)
    verify_design_integrity_calculation_release_manifest(design_integrity)
    verify_count_model_calculation_release_manifest(count_model)
    verify_selection_reuse_calculation_release_manifest(selection_reuse)
    verify_eqtl_sign_calculation_release_manifest(eqtl_sign)
    verify_hic_loop_calculation_release_manifest(hic_loop)
    generalized = _generalized_calculation_check_registry(
        base=base,
        single_cell=single_cell,
        effect_size=effect_size,
        design_integrity=design_integrity,
        count_model=count_model,
        selection_reuse=selection_reuse,
        eqtl_sign=eqtl_sign,
        hic_loop=hic_loop,
    )
    verify_generalized_calculation_release_manifest(generalized)
    return generalized


def generalized_calculation_check_registry() -> CalculationCheckRegistry:
    return _generalized_calculation_check_registry(
        base=calculation_check_release_registry(),
        single_cell=single_cell_sensitivity_registry(),
        effect_size=effect_size_summary_registry(),
        design_integrity=design_integrity_registry(),
        count_model=count_model_compatibility_registry(),
        selection_reuse=selection_reuse_registry(),
        eqtl_sign=eqtl_sign_registry(),
        hic_loop=hic_loop_strength_registry(),
    )


def _generalized_calculation_check_registry(
    *,
    base: CalculationCheckRegistry,
    single_cell: CalculationCheckRegistry,
    effect_size: CalculationCheckRegistry,
    design_integrity: CalculationCheckRegistry,
    count_model: CalculationCheckRegistry,
    selection_reuse: CalculationCheckRegistry,
    eqtl_sign: CalculationCheckRegistry,
    hic_loop: CalculationCheckRegistry,
) -> CalculationCheckRegistry:
    return CalculationCheckRegistry(
        (
            CalculationCheckModule(
                base.modules[0].manifest,
                (*base.modules[0].adapters, SelectedSidecarBHTableAdapter()),
            ),
            CalculationCheckModule(
                single_cell.modules[0].manifest,
                (
                    *single_cell.modules[0].adapters,
                    SelectedSidecarSingleCellSensitivityAdapter(),
                ),
            ),
            CalculationCheckModule(
                effect_size.modules[0].manifest,
                (
                    *effect_size.modules[0].adapters,
                    SelectedSidecarEffectSizeSummaryAdapter(),
                ),
            ),
            CalculationCheckModule(
                design_integrity.modules[0].manifest,
                (
                    *design_integrity.modules[0].adapters,
                    SelectedSidecarDesignIntegrityAdapter(),
                ),
            ),
            CalculationCheckModule(
                count_model.modules[0].manifest,
                (
                    *count_model.modules[0].adapters,
                    SelectedSidecarCountModelCompatibilityAdapter(),
                ),
            ),
            CalculationCheckModule(
                selection_reuse.modules[0].manifest,
                (
                    *selection_reuse.modules[0].adapters,
                    SelectedSidecarSelectionReuseAdapter(),
                ),
            ),
            CalculationCheckModule(
                eqtl_sign.modules[0].manifest,
                (
                    *eqtl_sign.modules[0].adapters,
                    SelectedSidecarEqtlSignAdapter(),
                ),
            ),
            CalculationCheckModule(
                hic_loop.modules[0].manifest,
                (
                    *hic_loop.modules[0].adapters,
                    SelectedSidecarHiCLoopStrengthAdapter(),
                ),
            ),
        ),
        profile_id="deterministic_calculation_check_v10",
    )


def generalized_calculation_release_projection(
    registry: CalculationCheckRegistry,
) -> dict[str, Any]:
    value = calculation_check_release_projection(registry)
    value["manifest_set_id"] = "calculation-check-manifest-set:v10-normalized-layout-adapters"
    return value


def verify_generalized_calculation_release_manifest(
    registry: CalculationCheckRegistry,
    *,
    manifest_path: Path = _GENERALIZED_RELEASE_MANIFEST,
) -> None:
    try:
        payload = manifest_path.read_bytes()
        expected = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise CalculationCheckContractError(
            "generalized calculation-check release manifest is unavailable or invalid"
        ) from error
    if not isinstance(expected, dict) or canonical_json(expected).encode("utf-8") != payload.rstrip(
        b"\n"
    ):
        raise CalculationCheckContractError(
            "generalized calculation-check release manifest is not canonical JSON"
        )
    if expected != generalized_calculation_release_projection(registry):
        raise CalculationCheckContractError(
            "generalized calculation-check release manifest or implementation drift"
        )


def calculation_check_release_projection(
    registry: CalculationCheckRegistry,
) -> dict[str, Any]:
    return {
        "manifest_set_id": "calculation-check-manifest-set:v1",
        "profile_id": registry.profile_id,
        "implementation_files": _CONTEXT_IMPLEMENTATION_FILES,
        "modules": [
            {
                "check_manifest": module.manifest.to_dict(),
                "comparison_relation": module.manifest.comparison_relation,
                "output_ceiling": module.manifest.output_ceiling,
                "adapter_manifests": [
                    adapter.manifest.to_dict()
                    for adapter in sorted(
                        module.adapters, key=lambda item: item.manifest.adapter_id
                    )
                ],
            }
            for module in sorted(registry.modules, key=lambda item: item.manifest.check_id)
        ],
        "production_finding_permitted": False,
    }


def verify_calculation_check_release_manifest(
    registry: CalculationCheckRegistry,
    *,
    manifest_path: Path = _RELEASE_MANIFEST,
) -> None:
    try:
        payload = manifest_path.read_bytes()
        expected = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise CalculationCheckContractError(
            "calculation-check release manifest is unavailable or invalid"
        ) from error
    if not isinstance(expected, dict) or canonical_json(expected).encode("utf-8") != payload.rstrip(
        b"\n"
    ):
        raise CalculationCheckContractError(
            "calculation-check release manifest is not canonical JSON"
        )
    if expected != calculation_check_release_projection(registry):
        raise CalculationCheckContractError(
            "calculation-check release manifest or implementation drift"
        )


def single_cell_calculation_release_projection(
    registry: CalculationCheckRegistry,
) -> dict[str, Any]:
    value = calculation_check_release_projection(registry)
    value["manifest_set_id"] = "calculation-check-manifest-set:v2-single-cell-sensitivity"
    return value


def verify_single_cell_calculation_release_manifest(
    registry: CalculationCheckRegistry,
    *,
    manifest_path: Path = _SINGLE_CELL_RELEASE_MANIFEST,
) -> None:
    try:
        payload = manifest_path.read_bytes()
        expected = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise CalculationCheckContractError(
            "single-cell calculation-check release manifest is unavailable or invalid"
        ) from error
    if not isinstance(expected, dict) or canonical_json(expected).encode("utf-8") != payload.rstrip(
        b"\n"
    ):
        raise CalculationCheckContractError(
            "single-cell calculation-check release manifest is not canonical JSON"
        )
    if expected != single_cell_calculation_release_projection(registry):
        raise CalculationCheckContractError(
            "single-cell calculation-check release manifest or implementation drift"
        )


def single_cell_calculation_release_projection_v9(
    registry: CalculationCheckRegistry,
) -> dict[str, Any]:
    value = calculation_check_release_projection(registry)
    value["manifest_set_id"] = (
        "calculation-check-manifest-set:v9-single-cell-optional-import-boundary"
    )
    return value


def verify_single_cell_calculation_release_manifest_v9(
    registry: CalculationCheckRegistry,
    *,
    manifest_path: Path = _SINGLE_CELL_RELEASE_MANIFEST_V9,
) -> None:
    try:
        payload = manifest_path.read_bytes()
        expected = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise CalculationCheckContractError(
            "v9 single-cell calculation-check release manifest is unavailable or invalid"
        ) from error
    if not isinstance(expected, dict) or canonical_json(expected).encode("utf-8") != payload.rstrip(
        b"\n"
    ):
        raise CalculationCheckContractError(
            "v9 single-cell calculation-check release manifest is not canonical JSON"
        )
    if expected != single_cell_calculation_release_projection_v9(registry):
        raise CalculationCheckContractError(
            "v9 single-cell calculation-check release manifest or implementation drift"
        )


def effect_size_calculation_release_projection(
    registry: CalculationCheckRegistry,
) -> dict[str, Any]:
    value = calculation_check_release_projection(registry)
    value["manifest_set_id"] = "calculation-check-manifest-set:v3-effect-size-summary"
    return value


def verify_effect_size_calculation_release_manifest(
    registry: CalculationCheckRegistry,
    *,
    manifest_path: Path = _EFFECT_SIZE_RELEASE_MANIFEST,
) -> None:
    try:
        payload = manifest_path.read_bytes()
        expected = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise CalculationCheckContractError(
            "effect-size calculation-check release manifest is unavailable or invalid"
        ) from error
    if not isinstance(expected, dict) or canonical_json(expected).encode("utf-8") != payload.rstrip(
        b"\n"
    ):
        raise CalculationCheckContractError(
            "effect-size calculation-check release manifest is not canonical JSON"
        )
    if expected != effect_size_calculation_release_projection(registry):
        raise CalculationCheckContractError(
            "effect-size calculation-check release manifest or implementation drift"
        )


def design_integrity_calculation_release_projection(
    registry: CalculationCheckRegistry,
) -> dict[str, Any]:
    value = calculation_check_release_projection(registry)
    value["manifest_set_id"] = "calculation-check-manifest-set:v4-design-integrity"
    return value


def verify_design_integrity_calculation_release_manifest(
    registry: CalculationCheckRegistry,
    *,
    manifest_path: Path = _DESIGN_INTEGRITY_RELEASE_MANIFEST,
) -> None:
    try:
        payload = manifest_path.read_bytes()
        expected = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise CalculationCheckContractError(
            "design-integrity calculation-check release manifest is unavailable or invalid"
        ) from error
    if not isinstance(expected, dict) or canonical_json(expected).encode("utf-8") != payload.rstrip(
        b"\n"
    ):
        raise CalculationCheckContractError(
            "design-integrity calculation-check release manifest is not canonical JSON"
        )
    if expected != design_integrity_calculation_release_projection(registry):
        raise CalculationCheckContractError(
            "design-integrity calculation-check release manifest or implementation drift"
        )


def count_model_calculation_release_projection(
    registry: CalculationCheckRegistry,
) -> dict[str, Any]:
    value = calculation_check_release_projection(registry)
    value["manifest_set_id"] = "calculation-check-manifest-set:v5-r-count-model"
    return value


def verify_count_model_calculation_release_manifest(
    registry: CalculationCheckRegistry,
    *,
    manifest_path: Path = _COUNT_MODEL_RELEASE_MANIFEST,
) -> None:
    try:
        payload = manifest_path.read_bytes()
        expected = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise CalculationCheckContractError(
            "count-model calculation-check release manifest is unavailable or invalid"
        ) from error
    if not isinstance(expected, dict) or canonical_json(expected).encode("utf-8") != payload.rstrip(
        b"\n"
    ):
        raise CalculationCheckContractError(
            "count-model calculation-check release manifest is not canonical JSON"
        )
    if expected != count_model_calculation_release_projection(registry):
        raise CalculationCheckContractError(
            "count-model calculation-check release manifest or implementation drift"
        )


def selection_reuse_calculation_release_projection(
    registry: CalculationCheckRegistry,
) -> dict[str, Any]:
    value = calculation_check_release_projection(registry)
    value["manifest_set_id"] = "calculation-check-manifest-set:v6-selection-reuse"
    return value


def verify_selection_reuse_calculation_release_manifest(
    registry: CalculationCheckRegistry,
    *,
    manifest_path: Path = _SELECTION_REUSE_RELEASE_MANIFEST,
) -> None:
    try:
        payload = manifest_path.read_bytes()
        expected = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise CalculationCheckContractError(
            "selection-reuse calculation-check release manifest is unavailable or invalid"
        ) from error
    if not isinstance(expected, dict) or canonical_json(expected).encode("utf-8") != payload.rstrip(
        b"\n"
    ):
        raise CalculationCheckContractError(
            "selection-reuse calculation-check release manifest is not canonical JSON"
        )
    if expected != selection_reuse_calculation_release_projection(registry):
        raise CalculationCheckContractError(
            "selection-reuse calculation-check release manifest or implementation drift"
        )


def eqtl_sign_calculation_release_projection(
    registry: CalculationCheckRegistry,
) -> dict[str, Any]:
    value = calculation_check_release_projection(registry)
    value["manifest_set_id"] = "calculation-check-manifest-set:v7-donor-eqtl-sign"
    return value


def verify_eqtl_sign_calculation_release_manifest(
    registry: CalculationCheckRegistry,
    *,
    manifest_path: Path = _EQTL_SIGN_RELEASE_MANIFEST,
) -> None:
    try:
        payload = manifest_path.read_bytes()
        expected = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise CalculationCheckContractError(
            "eQTL-sign calculation-check release manifest is unavailable or invalid"
        ) from error
    if not isinstance(expected, dict) or canonical_json(expected).encode("utf-8") != payload.rstrip(
        b"\n"
    ):
        raise CalculationCheckContractError(
            "eQTL-sign calculation-check release manifest is not canonical JSON"
        )
    if expected != eqtl_sign_calculation_release_projection(registry):
        raise CalculationCheckContractError(
            "eQTL-sign calculation-check release manifest or implementation drift"
        )


def hic_loop_calculation_release_projection(
    registry: CalculationCheckRegistry,
) -> dict[str, Any]:
    value = calculation_check_release_projection(registry)
    value["manifest_set_id"] = "calculation-check-manifest-set:v8-hic-loop-strength"
    return value


def verify_hic_loop_calculation_release_manifest(
    registry: CalculationCheckRegistry,
    *,
    manifest_path: Path = _HIC_LOOP_RELEASE_MANIFEST,
) -> None:
    try:
        payload = manifest_path.read_bytes()
        expected = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise CalculationCheckContractError(
            "Hi-C loop calculation-check release manifest is unavailable or invalid"
        ) from error
    if not isinstance(expected, dict) or canonical_json(expected).encode("utf-8") != payload.rstrip(
        b"\n"
    ):
        raise CalculationCheckContractError(
            "Hi-C loop calculation-check release manifest is not canonical JSON"
        )
    if expected != hic_loop_calculation_release_projection(registry):
        raise CalculationCheckContractError(
            "Hi-C loop calculation-check release manifest or implementation drift"
        )
