"""Capture a REAL Claude response for the ambiguous_group fixture into tests/cassettes/.

Run once (needs ANTHROPIC_API_KEY) to record the exact wire shape the `init` LLM path must handle;
the recorded JSON is replayed by tests/test_init_cassette.py (invariant I11) with NO key and NO
network. This is the antidote to mock drift — the four `init` bugs (temperature; type_evidence as a
string; unresolved as prose; model as prose) all passed a hand-built fake because the fake returned
the shapes we imagined, not the shapes the API sends. A frozen real recording cannot drift.

    ANTHROPIC_API_KEY=... PYTHONPATH=src:. python scripts/capture_cassette.py
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import anthropic

from fixtures.ambiguous_group.make_fixture import build
from sc_referee.init import (DEFAULT_MODEL, PROPOSAL_TOOL, SYSTEM_PROMPT, build_init_input,
                             proposal_tool_schema)

OUT = Path(__file__).resolve().parents[1] / "tests" / "cassettes" / "init_ambiguous_group.json"


def main() -> None:
    with tempfile.TemporaryDirectory() as d:
        build(Path(d))
        init_input = build_init_input(Path(d))

    msg = anthropic.Anthropic().messages.create(
        model=DEFAULT_MODEL, max_tokens=2000, system=SYSTEM_PROMPT,
        tools=[{"name": PROPOSAL_TOOL,
                "description": "Propose the analysis type and experimental design for a human to ratify.",
                "input_schema": proposal_tool_schema()}],
        tool_choice={"type": "tool", "name": PROPOSAL_TOOL},
        messages=[{"role": "user", "content": json.dumps(init_input, indent=2, default=str)}])

    uses = [b for b in msg.content if getattr(b, "type", None) == "tool_use" and b.name == PROPOSAL_TOOL]
    if not uses:
        raise SystemExit("the model did not call propose_design (returned prose) — nothing to record")

    cassette = {
        "_note": ("RECORDED real Claude response for the ambiguous_group fixture — replayed by "
                  "tests/test_init_cassette.py (invariant I11). Do not hand-edit; re-capture with "
                  "scripts/capture_cassette.py."),
        "model": msg.model, "stop_reason": msg.stop_reason,
        "tool_name": PROPOSAL_TOOL, "input": uses[0].input,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cassette, indent=2) + "\n")
    print(f"wrote {OUT}  (condition -> {uses[0].input.get('design', {}).get('condition')!r})")


if __name__ == "__main__":
    main()
