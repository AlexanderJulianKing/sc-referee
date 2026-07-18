"""Canonical table-binding values shared by proposers and compilers."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


_TABLE_COLUMN_ROLES = {
    "cell_table": {
        "required_scalar": ("cell_id", "donor", "total_umi", "marker"),
        "optional_scalar": (),
        "optional_nested": (),
    },
    "donor_table": {
        "required_scalar": ("donor", "genotype"),
        "optional_scalar": (),
        "optional_nested": (),
    },
    "empty_droplet_table": {
        "required_scalar": ("total_umi",),
        "optional_scalar": ("id", "barcode", "marker"),
        "optional_nested": ("panel",),
    },
}


@dataclass(frozen=True)
class TableBinding:
    """A confined artifact name and its semantic-to-source column bindings."""

    artifact_path: str
    columns: Mapping[str, object]


def parse_table_binding(value: object, label: str) -> TableBinding:
    """Parse the one canonical table value shape used by every table destination."""

    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    unexpected = set(value).difference({"artifact_path", "columns"})
    if unexpected:
        raise ValueError(
            f"{label} has unexpected field(s): {', '.join(sorted(map(str, unexpected)))}"
        )
    path = value.get("artifact_path")
    columns = value.get("columns")
    if not isinstance(path, str) or not path or not isinstance(columns, Mapping):
        raise ValueError(f"{label} requires artifact_path and columns")
    roles = _TABLE_COLUMN_ROLES.get(label)
    if roles is None:
        raise ValueError(f"unknown table-binding role: {label}")
    required = set(roles["required_scalar"])
    expected = set((
        *roles["required_scalar"],
        *roles["optional_scalar"],
        *roles["optional_nested"],
    ))
    actual = set(columns)
    if not required.issubset(actual) or not actual.issubset(expected):
        missing = sorted(map(str, required.difference(actual)))
        extra = sorted(map(str, actual.difference(expected)))
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if extra:
            details.append(f"unexpected {', '.join(extra)}")
        raise ValueError(f"{label}.columns has invalid roles: {'; '.join(details)}")
    for role in (*roles["required_scalar"], *roles["optional_scalar"]):
        if role not in columns:
            continue
        column = columns[role]
        if not isinstance(column, str) or not column:
            raise ValueError(f"{label}.columns.{role} must be a non-empty column name")
    for role in roles["optional_nested"]:
        if role not in columns:
            continue
        nested = columns[role]
        if (
            not isinstance(nested, Mapping)
            or not nested
            or any(
                not isinstance(key, str) or not key
                or not isinstance(column, str) or not column
                for key, column in nested.items()
            )
        ):
            raise ValueError(
                f"{label}.columns.{role} must map non-empty roles to column names"
            )
    return TableBinding(path, columns)


def table_binding_value_schema(label: str) -> dict[str, Any]:
    """Build the JSON Schema counterpart of :func:`parse_table_binding`."""

    roles = _TABLE_COLUMN_ROLES[label]
    column_name = {"type": "string", "minLength": 1}
    properties: dict[str, Any] = {
        role: column_name
        for role in (*roles["required_scalar"], *roles["optional_scalar"])
    }
    properties.update({
        role: {
            "type": "object",
            "minProperties": 1,
            "additionalProperties": column_name,
        }
        for role in roles["optional_nested"]
    })
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["artifact_path", "columns"],
        "properties": {
            "artifact_path": {"type": "string", "minLength": 1},
            "columns": {
                "type": "object",
                "additionalProperties": False,
                "required": [*roles["required_scalar"]],
                "properties": properties,
            },
        },
    }


__all__ = ["TableBinding", "parse_table_binding", "table_binding_value_schema"]
