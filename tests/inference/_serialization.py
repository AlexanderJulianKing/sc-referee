from __future__ import annotations

import ast
import dataclasses
import json
import math


def _public(value):
    if isinstance(value, ast.AST):
        return {"__ast__": ast.dump(value, annotate_fields=True, include_attributes=True)}
    if dataclasses.is_dataclass(value):
        return {
            "__type__": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": {field.name: _public(getattr(value, field.name)) for field in dataclasses.fields(value)},
        }
    if isinstance(value, dict):
        return {str(key): _public(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return {"__tuple__": [_public(item) for item in value]}
    if isinstance(value, list):
        return [_public(item) for item in value]
    if isinstance(value, (set, frozenset)):
        items = [_public(item) for item in value]
        items.sort(key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")))
        return {"__frozenset__" if isinstance(value, frozenset) else "__set__": items}
    if isinstance(value, float) and not math.isfinite(value):
        return {"__float__": "nan" if math.isnan(value) else ("inf" if value > 0 else "-inf")}
    if hasattr(value, "item") and type(value).__module__.startswith("numpy"):
        return _public(value.item())
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported public value: {type(value)!r}")


def public_bytes(value) -> bytes:
    return json.dumps(_public(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _normalize_sub_epsilon(value, atol=1e-12):
    """Canonicalize BLAS-level float noise before cross-platform oracle comparison."""
    if isinstance(value, dict):
        return {key: _normalize_sub_epsilon(item, atol) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_sub_epsilon(item, atol) for item in value]
    if isinstance(value, float) and math.isfinite(value):
        if abs(value) <= atol:
            return 0.0
        return round(value, 12)
    return value


def normalized_public_bytes(value) -> bytes:
    return json.dumps(_normalize_sub_epsilon(_public(value)), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def normalized_public_json(value: str) -> str:
    return json.dumps(_normalize_sub_epsilon(json.loads(value)), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)
