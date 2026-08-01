from __future__ import annotations

from scripts.verify_handoff import (
    V014_TO_V015_TARGET_SCHEMA_ROOT,
    V015_TO_V016_TARGET_SCHEMA_ROOT,
    V016_TO_V017_TARGET_SCHEMA_ROOT,
    V017_TO_V018_TARGET_SCHEMA_ROOT,
)


def test_handoff_migration_targets_preserve_each_public_schema_boundary() -> None:
    assert V014_TO_V015_TARGET_SCHEMA_ROOT == "reference/schemas-v0.15.0"
    assert V015_TO_V016_TARGET_SCHEMA_ROOT == "reference/schemas-v0.16.0"
    assert V016_TO_V017_TARGET_SCHEMA_ROOT == "reference/schemas-v0.17.0"
    assert V017_TO_V018_TARGET_SCHEMA_ROOT == "reference/schemas-v0.18.0"
