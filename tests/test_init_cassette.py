"""Invariant I11: the `init` LLM path, tested against a RECORDED real Claude response.

Every other test of the Claude path uses a hand-built fake that returns the shapes we chose — and
that fake hid four real bugs until the first live call (temperature; type_evidence as a string;
unresolved as prose; model as prose). This test replays a FROZEN real recording
(tests/cassettes/init_ambiguous_group.json, captured by scripts/capture_cassette.py) with no key and
no network, so the wire shape under test is the one the API actually sends — it cannot drift.
"""
import json
from pathlib import Path
from types import SimpleNamespace

from fixtures.ambiguous_group.make_fixture import build
from sc_referee.init import propose
from sc_referee.schema_validation import validate

CASSETTE = Path(__file__).parent / "cassettes" / "init_ambiguous_group.json"
ROLES = {"analysis_type", "condition", "replicate_unit", "batch", "analyst_adjusted_for",
         "reference", "unit_of_test"}


def _replay_client(cassette):
    """A client that replays the recorded tool_use response — and asserts the call shape the REAL
    API demands (no `temperature`; a forced tool call), pinning bug 1."""
    def create(**kw):
        assert "temperature" not in kw, "the API rejects temperature for this model"
        assert kw.get("tool_choice", {}).get("name") == cassette["tool_name"], "must force the tool call"
        block = SimpleNamespace(type="tool_use", name=cassette["tool_name"], input=cassette["input"])
        return SimpleNamespace(content=[block])
    return SimpleNamespace(messages=SimpleNamespace(create=create))


def test_the_recorded_response_has_the_real_wire_shapes():
    """The shapes the hand-built mock got wrong are exactly what this recording pins."""
    payload = json.loads(CASSETTE.read_text())["input"]
    assert isinstance(payload["type_evidence"], list)                 # bug 2: was a bare string
    assert isinstance(payload["unresolved"], list)
    assert set(payload["unresolved"]) <= ROLES                        # bug 3: role names, not prose
    for forbidden in ("model", "contrasts", "target_coefficient"):    # bug 4: no LLM-authored formula
        assert forbidden not in payload


def test_recorded_real_response_round_trips_to_a_valid_config(tmp_path):
    cassette = json.loads(CASSETTE.read_text())
    build(tmp_path)

    proposal, source = propose(tmp_path, client=_replay_client(cassette))

    assert source == "claude"
    assert proposal["design"]["condition"] == "group"                 # the model resolved the ambiguous column
    assert proposal["contrasts"], "arithmetic synthesized the contrasts the model never authored"
    validate(proposal, "sc_referee.schema.json")                      # ...into a schema-valid config
