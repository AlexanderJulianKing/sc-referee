"""Roles-only inventory and proposal validation with no semantic authority."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


PROPOSAL_SCHEMA_ID = "sc-referee/empty-droplet-proposal/v1"
_ALLOWED_FIELDS = frozenset({
    "schema_id", "confirmed_by_human", "inventory", "source_path", "filtered_path",
    "source_format", "filtered_format", "source_compression", "filtered_compression",
    "barcode_key_column", "cell_key_column", "total_count_column",
    "gene_count_columns", "namespace", "membership_method_id", "proposer_kind",
    "proposer_id", "evidence",
})
_FORMATS = frozenset({"dense_csv/v1", "gbp07_cells_csv/v1"})
_COMPRESSIONS = frozenset({"none", "gzip"})
_METHODS = frozenset({"explicit_empty_table_rows/v1"})


@dataclass(frozen=True)
class EmptyDropletRoleProposal:
    schema_id: str
    confirmed_by_human: bool
    inventory: tuple[str, ...]
    headers: Mapping[str, tuple[str, ...]]
    inspected_value_columns: tuple[str, ...]
    membership_method_id: str
    source_path: str | None = None
    filtered_path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "inventory", tuple(self.inventory))
        object.__setattr__(self, "headers", MappingProxyType({
            key: tuple(value) for key, value in dict(self.headers).items()
        }))
        object.__setattr__(self, "inspected_value_columns", tuple(self.inspected_value_columns))


def validate_proposal(value: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("proposal must be an object")
    unknown = set(value) - _ALLOWED_FIELDS
    if unknown:
        raise ValueError(f"proposal contains forbidden or unknown fields: {sorted(unknown)}")
    if value.get("schema_id") != PROPOSAL_SCHEMA_ID:
        raise ValueError("unsupported proposal schema")
    if value.get("confirmed_by_human", False) is not False:
        raise ValueError("a proposal cannot confirm itself")
    if "membership_method_id" in value and value["membership_method_id"] not in _METHODS:
        raise ValueError("unsupported membership method")
    for key in ("source_format", "filtered_format"):
        if key in value and value[key] not in _FORMATS:
            raise ValueError(f"unsupported {key}")
    for key in ("source_compression", "filtered_compression"):
        if key in value and value[key] not in _COMPRESSIONS:
            raise ValueError(f"unsupported {key}")
    for key in ("source_path", "filtered_path"):
        if key in value and (not isinstance(value[key], str) or not value[key]):
            raise ValueError(f"{key} must name an existing relative identity")
    if "gene_count_columns" in value:
        columns = value["gene_count_columns"]
        if not isinstance(columns, (tuple, list)) or not columns or not all(
            isinstance(column, str) and column for column in columns
        ):
            raise ValueError("gene_count_columns must be existing column identities")
    return MappingProxyType(dict(value))


def propose_empty_droplet_roles(root: Path, client=None) -> EmptyDropletRoleProposal:
    root = Path(root)
    inventory = tuple(sorted(
        path.relative_to(root).as_posix()
        for path in root.iterdir()
        if path.is_file() and (path.name.endswith(".csv") or path.name.endswith(".csv.gz"))
    ))
    # The deterministic fallback intentionally does not open any table, infer a role from
    # a basename, or inspect donor/exposure/outcome/target-bearing values.
    return EmptyDropletRoleProposal(
        schema_id=PROPOSAL_SCHEMA_ID,
        confirmed_by_human=False,
        inventory=inventory,
        headers={},
        inspected_value_columns=(),
        membership_method_id="explicit_empty_table_rows/v1",
    )
