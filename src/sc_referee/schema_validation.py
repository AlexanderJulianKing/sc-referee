"""Load + validate against the packaged JSON schemas.

Schemas ship *inside* the package (src/sc_referee/schemas/) so they resolve at runtime
whether installed or run from a checkout.
"""
from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files

import jsonschema


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict:
    return json.loads((files("sc_referee") / "schemas" / name).read_text())


def validate(instance, schema_name: str) -> None:
    """Raise jsonschema.ValidationError if `instance` does not conform."""
    jsonschema.validate(instance, load_schema(schema_name))
