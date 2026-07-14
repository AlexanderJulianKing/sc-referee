"""Computation-free policy declaration schema."""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping


ScalarLiteral = str | int | bool | None | tuple[int, int]


@dataclass(frozen=True)
class FactRef:
    fact_type: str
    selector: Mapping[str, ScalarLiteral]

    def __post_init__(self):
        object.__setattr__(self, "selector", MappingProxyType(dict(self.selector)))


@dataclass(frozen=True)
class RelationPremise:
    relation: str
    arguments: tuple[FactRef | ScalarLiteral, ...]


@dataclass(frozen=True)
class ProviderInvocation:
    provider_id: str
    provider_version: str
    provider_digest: str
    inputs: Mapping[str, FactRef | ScalarLiteral]
    expected_relation: str

    def __post_init__(self):
        object.__setattr__(self, "inputs", MappingProxyType(dict(self.inputs)))


@dataclass(frozen=True)
class ProofRule:
    id: str
    premises: tuple[RelationPremise, ...]
    discharge: tuple[ProviderInvocation, ...]
    outcome: str
    max_external_status: str
    required_assumptions: tuple[str, ...]


@dataclass(frozen=True)
class ValidityPolicy:
    id: str
    scope: tuple[RelationPremise, ...]
    rules: tuple[ProofRule, ...]
    required_coverage: frozenset[str]


@dataclass(frozen=True)
class Judgment:
    outcome: str = "ABSTAIN"
    max_external_status: str = "not_audited"
    derivation: object | None = None
    assumptions: frozenset[str] = frozenset()
    obligations: tuple[str, ...] = ()


def _walk(value):
    yield value
    if dataclasses.is_dataclass(value):
        for item in dataclasses.fields(value):
            yield from _walk(getattr(value, item.name))
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield from _walk(key)
            yield from _walk(item)
    elif isinstance(value, (tuple, list, set, frozenset)):
        for item in value:
            yield from _walk(item)


def assert_no_callables(value) -> None:
    if any(callable(item) for item in _walk(value)):
        raise TypeError("policy declarations may not contain a callable")


def _json_value(value):
    if dataclasses.is_dataclass(value):
        return {item.name: _json_value(getattr(value, item.name)) for item in dataclasses.fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_json_value(item) for item in value), key=repr)
    if isinstance(value, Enum):
        return value.value
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"policy value is not immutable JSON data: {type(value)!r}")


def canonical_policy_json(policy: ValidityPolicy) -> str:
    assert_no_callables(policy)
    return json.dumps(_json_value(policy), sort_keys=True, separators=(",", ":"), allow_nan=False)


def validate_policy(policy: ValidityPolicy) -> None:
    assert_no_callables(policy)
    if not policy.id or any(rule.outcome not in {"CLEAN_PROOF", "VIOLATION_WITNESS", "ABSTAIN"}
                            for rule in policy.rules):
        raise ValueError("invalid policy declaration")
    canonical_policy_json(policy)
