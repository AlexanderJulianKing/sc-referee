from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from sc_referee.calculation_checks.core import (
    CalculationAdapterManifest,
    CalculationCheckContractError,
    CalculationContext,
    CalculationObservation,
    FrozenCalculationInput,
)
from sc_referee.calculation_checks.material_context import MaterialCalculationContext
from sc_referee.core.ids import semantic_digest, sha256_digest

SIDECAR_MARKER = "sc_referee_calculation_contracts"
SIDECAR_VERSION = 1
MAX_SIDECAR_BYTES = 256 * 1024
MAX_SIDECAR_CONTRACTS = 32
_ROOT_KEYS = {SIDECAR_MARKER, "contracts"}
_ENTRY_KEYS = {"check_id", "contract"}
SIDECAR_RECOGNITION_GRAMMAR_DIGEST = semantic_digest(
    {
        "marker": SIDECAR_MARKER,
        "version": SIDECAR_VERSION,
        "root_keys": sorted(_ROOT_KEYS),
        "entry_keys": sorted(_ENTRY_KEYS),
        "extensions": [".yaml", ".yml"],
        "max_bytes": MAX_SIDECAR_BYTES,
        "max_contracts": MAX_SIDECAR_CONTRACTS,
        "selection_requirement": "exact_material_input_scope",
    }
)


@dataclass(frozen=True)
class SidecarContract:
    check_id: str
    value: dict[str, Any]
    input: FrozenCalculationInput

    @property
    def source_ref(self) -> dict[str, Any]:
        return self.input.source_ref


def sidecar_adapter_manifest(
    *, family: str, implementation_digest: str
) -> CalculationAdapterManifest:
    return CalculationAdapterManifest(
        adapter_id=f"calculation-adapter:selected-sidecar-{family}-v1",
        adapter_version="1.0.0",
        implementation_digest=semantic_digest(
            {
                "family_implementation_digest": implementation_digest,
                "sidecar_parser_digest": sha256_digest(__file_bytes()),
                "recognition_grammar_digest": SIDECAR_RECOGNITION_GRAMMAR_DIGEST,
            }
        ),
        recognition_grammar_digest=SIDECAR_RECOGNITION_GRAMMAR_DIGEST,
    )


def with_sidecar_lineage(
    observation: CalculationObservation,
    sidecar: SidecarContract,
) -> CalculationObservation:
    if sidecar.input.artifact_ref in observation.input_refs:
        return observation
    return replace(
        observation,
        input_refs=(*observation.input_refs, sidecar.input.artifact_ref),
    )


def selected_sidecar_contract(
    context: CalculationContext,
    *,
    check_id: str,
) -> SidecarContract | None:
    if not isinstance(context, MaterialCalculationContext):
        return None
    marked: list[tuple[FrozenCalculationInput, dict[str, Any]]] = []
    for item in context.material_inputs:
        if PurePosixPath(item.path).suffix.casefold() not in {".yaml", ".yml"}:
            continue
        value = _load_possible_sidecar(item)
        if value is not None:
            marked.append((item, value))
    if not marked:
        return None
    if len(marked) != 1:
        raise CalculationCheckContractError(
            "more than one selected calculation-contract sidecar is marked"
        )
    item, root = marked[0]
    entries = root["contracts"]
    matches = [entry for entry in entries if entry["check_id"] == check_id]
    if not matches:
        return None
    if len(matches) != 1:
        raise CalculationCheckContractError("calculation sidecar check IDs must be unique")
    contract = matches[0]["contract"]
    assert isinstance(contract, dict)
    return SidecarContract(check_id, contract, item)


def _load_possible_sidecar(item: FrozenCalculationInput) -> dict[str, Any] | None:
    if len(item.content) > MAX_SIDECAR_BYTES:
        # An over-budget YAML file is irrelevant unless its bounded prefix claims the marker.
        prefix = item.content[: min(len(item.content), 4096)]
        if SIDECAR_MARKER.encode("utf-8") in prefix:
            raise CalculationCheckContractError("calculation-contract sidecar exceeds byte ceiling")
        return None
    try:
        text = item.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise CalculationCheckContractError(
            "selected YAML material input is not strict UTF-8"
        ) from error
    try:
        value = yaml.safe_load(text)
    except yaml.YAMLError as error:
        if SIDECAR_MARKER in text:
            raise CalculationCheckContractError(
                "calculation-contract sidecar is not valid YAML"
            ) from error
        return None
    if not isinstance(value, dict) or SIDECAR_MARKER not in value:
        return None
    if set(value) != _ROOT_KEYS or value[SIDECAR_MARKER] != SIDECAR_VERSION:
        raise CalculationCheckContractError("calculation-contract sidecar root is invalid")
    entries = value["contracts"]
    if not isinstance(entries, list) or not entries or len(entries) > MAX_SIDECAR_CONTRACTS:
        raise CalculationCheckContractError("calculation-contract sidecar entry count is invalid")
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != _ENTRY_KEYS:
            raise CalculationCheckContractError("calculation-contract sidecar entry is invalid")
        check = entry["check_id"]
        contract = entry["contract"]
        if not isinstance(check, str) or not check or any(char.isspace() for char in check):
            raise CalculationCheckContractError("calculation-contract check ID is invalid")
        if check in seen:
            raise CalculationCheckContractError("calculation sidecar check IDs must be unique")
        if not isinstance(contract, dict):
            raise CalculationCheckContractError("calculation sidecar contract must be a mapping")
        seen.add(check)
    return value


def __file_bytes() -> bytes:
    return Path(__file__).read_bytes()
