import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


def test_provisional_schemas_are_well_formed(project_root: Path) -> None:
    root = project_root / "provisional-schemas" / "v0.1.0"
    resources = []
    schemas = []
    for path in sorted(root.glob("*.schema.json")):
        schema = json.loads(path.read_text())
        Draft202012Validator.check_schema(schema)
        schemas.append(schema)
        resources.append((schema["$id"], Resource.from_contents(schema)))
    assert len(schemas) >= 6
    assert Registry().with_resources(resources)
