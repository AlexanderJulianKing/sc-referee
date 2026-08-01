from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from sc_referee.core.errors import RecordValidationError


class ProvisionalSchemaRegistry:
    """Validate explicitly provisional records without presenting them as public schemas."""

    def __init__(self, provisional_root: Path, public_schema_root: Path) -> None:
        self.by_record_type: dict[str, dict[str, Any]] = {}
        resources: list[tuple[str, Resource[Any]]] = []
        public_dir = public_schema_root / "schemas" / "v0.5.0"
        for path in sorted(public_dir.glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            resources.append((schema["$id"], Resource.from_contents(schema)))
        for path in sorted(provisional_root.glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            resources.append((schema["$id"], Resource.from_contents(schema)))
            record_type = schema.get("properties", {}).get("record_type", {}).get("const")
            if isinstance(record_type, str):
                self.by_record_type[record_type] = schema
        self.registry = Registry().with_resources(resources)

    def validate(self, record: dict[str, Any]) -> None:
        record_type = record.get("record_type")
        if not isinstance(record_type, str) or record_type not in self.by_record_type:
            raise RecordValidationError(f"Unknown provisional record_type: {record_type!r}")
        validator = Draft202012Validator(self.by_record_type[record_type], registry=self.registry)
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        if errors:
            detail = "; ".join(
                f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
                for error in errors[:10]
            )
            raise RecordValidationError(f"{record_type} failed validation: {detail}")
