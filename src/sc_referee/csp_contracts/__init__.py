"""Closed CSP manifest registry."""
from .between_group_adjustment_obligation_v1 import (
    CONTRACT_TYPE as BETWEEN_GROUP_CONTRACT_TYPE,
    MANIFEST as BETWEEN_GROUP_MANIFEST,
)
from .target_population_estimand_v1 import (
    CONTRACT_TYPE as TARGET_POPULATION_CONTRACT_TYPE,
    MANIFEST as TARGET_POPULATION_MANIFEST,
)
from .contamination_basis_obligation_v1 import (
    CONTRACT_TYPE as CONTAMINATION_BASIS_CONTRACT_TYPE,
    MANIFEST as CONTAMINATION_BASIS_MANIFEST,
)


_MANIFESTS = {
    BETWEEN_GROUP_CONTRACT_TYPE: BETWEEN_GROUP_MANIFEST,
    TARGET_POPULATION_CONTRACT_TYPE: TARGET_POPULATION_MANIFEST,
    CONTAMINATION_BASIS_CONTRACT_TYPE: CONTAMINATION_BASIS_MANIFEST,
}


def get_manifest(contract_type: str):
    try:
        return _MANIFESTS[contract_type]
    except KeyError as exc:
        raise KeyError(f"unknown CSP contract type/version: {contract_type}") from exc


def registered_contract_types() -> tuple[str, ...]:
    return tuple(_MANIFESTS)
