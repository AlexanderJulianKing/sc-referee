"""Deliberately regenerate the frozen legacy outputs.

Run only when establishing or explicitly reviewing the migration oracle; normal tests never update it.
"""
from __future__ import annotations

import json
from pathlib import Path

from sc_referee.checks.confounding import evaluate_confounding
from sc_referee.provenance import groupby_provenance
from sc_referee.sink_use import bind_sinks
from tests.frozen_oracles.cases import confounding_cases, source_cases
from tests.inference._serialization import public_bytes


def build():
    payload = {"schema_version": 1, "collected_test_count": 586, "sources": {}, "confounding": {}}
    for name, sources in source_cases():
        payload["sources"][name] = {
            "groupby_provenance": public_bytes(groupby_provenance(sources)).decode(),
            "bind_sinks": public_bytes(bind_sinks(sources)).decode(),
        }
    for name, observations, design in confounding_cases():
        payload["confounding"][name] = public_bytes(
            evaluate_confounding(observations, design)).decode()
    return payload


if __name__ == "__main__":
    path = Path(__file__).with_name("legacy_oracles.json")
    path.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n")
