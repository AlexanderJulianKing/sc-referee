"""Pinned, schema-valid literal configuration reads."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class ConfigState:
    values: Mapping[str, object] = field(default_factory=dict)
    schema_paths: frozenset[str] = frozenset()


@dataclass(frozen=True)
class UnknownConfig:
    path: str
    reason: str


@dataclass(frozen=True)
class ConfigRead:
    path: str
    value: object | None
    exact: bool
    unknown: UnknownConfig | None


def read_config(state: ConfigState, path: str, *, literal_path: bool) -> ConfigRead:
    if not literal_path:
        return ConfigRead(path, None, False, UnknownConfig(path, "dynamic_config_path"))
    if path not in state.schema_paths:
        return ConfigRead(path, None, False, UnknownConfig(path, "schema_path_unverified"))
    if path not in state.values:
        return ConfigRead(path, None, False, UnknownConfig(path, "pinned_value_missing"))
    return ConfigRead(path, state.values[path], True, None)
