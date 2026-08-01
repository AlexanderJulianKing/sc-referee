from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from sc_referee.core.errors import RecordValidationError


class LocalSchemaRegistry:
    def __init__(self, schema_package_root: Path) -> None:
        self.root = schema_package_root
        catalog = json.loads((self.root / "schema-catalog.json").read_text(encoding="utf-8"))
        schema_version = catalog.get("schema_version")
        if not isinstance(schema_version, str) or not schema_version:
            raise RecordValidationError("Schema catalog has no non-empty schema_version")
        self.schema_dir = self.root / "schemas" / f"v{schema_version}"
        self.by_record_type: dict[str, dict[str, Any]] = {}
        resources: list[tuple[str, Resource[Any]]] = []
        for item in catalog["schemas"]:
            schema = json.loads((self.schema_dir / item["file"]).read_text(encoding="utf-8"))
            resources.append((schema["$id"], Resource.from_contents(schema)))
            if item["kind"] == "record":
                record_type = schema.get("properties", {}).get("record_type", {}).get("const")
                if isinstance(record_type, str):
                    self.by_record_type[record_type] = schema
        self.registry = Registry().with_resources(resources)

    def validate(self, record: dict[str, Any]) -> None:
        record_type = record.get("record_type")
        if not isinstance(record_type, str) or record_type not in self.by_record_type:
            raise RecordValidationError(f"Unknown public record_type: {record_type!r}")
        validator = Draft202012Validator(self.by_record_type[record_type], registry=self.registry)
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        if errors:
            detail = "; ".join(
                f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
                for error in errors[:10]
            )
            raise RecordValidationError(f"{record_type} failed validation: {detail}")

    def validate_example_directory(self) -> int:
        count = 0
        for path in sorted((self.root / "examples").glob("*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            self.validate(value)
            count += 1
        return count
