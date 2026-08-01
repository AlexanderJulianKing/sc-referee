import json

import pytest

from sc_referee.core.errors import RecordValidationError
from sc_referee.records.schema_registry import LocalSchemaRegistry


def test_all_public_examples_validate(schema_root) -> None:
    assert LocalSchemaRegistry(schema_root).validate_example_directory() >= 30


def test_schema_registry_uses_catalog_version(tmp_path) -> None:
    schema_dir = tmp_path / "schemas" / "v9.8.7"
    schema_dir.mkdir(parents=True)
    catalog = {
        "schema_version": "9.8.7",
        "schemas": [
            {
                "name": "probe",
                "file": "probe.schema.json",
                "id": "urn:test:probe",
                "kind": "record",
            }
        ],
    }
    (tmp_path / "schema-catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:test:probe",
        "type": "object",
        "required": ["record_type"],
        "properties": {"record_type": {"const": "probe"}},
        "additionalProperties": False,
    }
    (schema_dir / "probe.schema.json").write_text(json.dumps(schema), encoding="utf-8")

    registry = LocalSchemaRegistry(tmp_path)
    registry.validate({"record_type": "probe"})


def test_schema_registry_rejects_catalog_without_version(tmp_path) -> None:
    (tmp_path / "schema-catalog.json").write_text('{"schemas": []}', encoding="utf-8")

    with pytest.raises(RecordValidationError, match="schema_version"):
        LocalSchemaRegistry(tmp_path)
