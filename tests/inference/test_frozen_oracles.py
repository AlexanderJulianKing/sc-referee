from __future__ import annotations

import json
from pathlib import Path

from sc_referee.checks.confounding import evaluate_confounding
from sc_referee.provenance import groupby_provenance
from sc_referee.sink_use import bind_sinks
from tests.frozen_oracles.cases import confounding_cases, source_cases
from tests.inference._serialization import public_bytes


ORACLE_PATH = Path(__file__).parents[1] / "frozen_oracles" / "legacy_oracles.json"


def test_frozen_oracle_corpus_covers_every_current_input_family():
    assert len(source_cases()) == 56
    assert len(confounding_cases()) == 22


def test_frozen_legacy_outputs_are_byte_exact():
    frozen = json.loads(ORACLE_PATH.read_text())
    assert frozen["collected_test_count"] == 586
    assert [name for name, _ in source_cases()] == list(frozen["sources"])
    assert [name for name, _, _ in confounding_cases()] == list(frozen["confounding"])

    for name, sources in source_cases():
        expected = frozen["sources"][name]
        assert public_bytes(groupby_provenance(sources)).decode() == expected["groupby_provenance"]
        assert public_bytes(bind_sinks(sources)).decode() == expected["bind_sinks"]

    for name, observations, design in confounding_cases():
        expected = frozen["confounding"][name]
        assert public_bytes(evaluate_confounding(observations, design)).decode() == expected
