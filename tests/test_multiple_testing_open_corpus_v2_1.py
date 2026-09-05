from __future__ import annotations

import hashlib
import json
import runpy
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import canonical_json

_ROOT = Path("evaluation/development/multitest-open-corpus-v1")


def test_open_corpus_adapter_replay_is_custody_pinned_and_false_accusation_free(
    tmp_path: Path,
) -> None:
    labels = json.loads((_ROOT / "specs" / "labels.json").read_text(encoding="utf-8"))
    assert Counter(item["label"] for item in labels.values()) == {
        "correct": 25,
        "misstep": 25,
    }
    assert hashlib.sha256((_ROOT / "specs" / "labels.json").read_bytes()).hexdigest() == (
        "f9d2d33ba3b8247b0d0d65e5f72f765af02bfca6dc932f895010d79129f36f80"
    )
    assert hashlib.sha256((_ROOT / "baseline_1_1.json").read_bytes()).hexdigest() == (
        "b2ab49cd1bea5fe27a9a738d380432fe8164facaa73096020f3c1a7f08165cf6"
    )

    namespace = runpy.run_path(str(_ROOT / "adapter_replay.py"))
    replay = cast(Callable[..., dict[str, dict[str, Any]]], namespace["replay_open_corpus"])
    observed = replay(
        corpus_root=_ROOT,
        scratch_root=tmp_path / "replay",
        schema_root=Path("reference/schemas-v0.21.0"),
    )
    expected = json.loads((_ROOT / "adapter_replay_records.json").read_text(encoding="utf-8"))
    expected.update(
        json.loads((_ROOT / "adapter_replay_records_v2_1.json").read_text(encoding="utf-8"))
    )
    assert canonical_json({key: observed[key] for key in expected}) == canonical_json(expected)

    assert observed["1.1.0"]["correct_candidates"] == 0
    assert observed["1.1.0"]["misstep_candidates"] == 0
    assert observed["2.0.0"]["correct_candidates"] == 0
    assert observed["2.0.0"]["misstep_candidates"] == 2
    assert observed["2.1.0"]["correct_candidates"] == 0
    assert observed["2.1.0"]["misstep_candidates"] == 19
    assert observed["2.0.0"]["results"]["spec-14"] == [
        "abstain",
        "test-operand-lineage-unresolved",
    ]
    assert observed["2.0.0"]["results"]["spec-36"] == [
        "abstain",
        "test-operand-lineage-unresolved",
    ]
    assert {
        spec for spec, result in observed["2.0.0"]["results"].items() if result[0] == "candidate"
    } == {"spec-19", "spec-33"}
    assert {
        spec for spec, result in observed["2.1.0"]["results"].items() if result[0] == "candidate"
    } == {
        "spec-01",
        "spec-03",
        "spec-05",
        "spec-07",
        "spec-09",
        "spec-11",
        "spec-15",
        "spec-17",
        "spec-19",
        "spec-21",
        "spec-25",
        "spec-27",
        "spec-31",
        "spec-33",
        "spec-35",
        "spec-41",
        "spec-43",
        "spec-45",
        "spec-49",
    }
    assert observed["2.1.0"]["results"]["spec-21"] == ["candidate", "strict_subset"]
    assert observed["2.1.0"]["results"]["spec-43"] == ["candidate", "strict_subset"]
    assert {
        spec: observed["2.1.0"]["results"][spec]
        for spec in ("spec-13", "spec-23", "spec-29", "spec-37", "spec-39", "spec-47")
    } == {
        "spec-13": ["abstain", "test-battery-cardinality-unresolved"],
        "spec-23": ["abstain", "pvalue-scalar-cast-or-rounding-unsupported"],
        "spec-29": ["abstain", "unresolved-decision-threshold"],
        "spec-37": ["abstain", "selected-group-row-completeness-unproven"],
        "spec-39": ["abstain", "api-resolution-ambiguous"],
        "spec-47": ["abstain", "unresolved-decision-threshold"],
    }
    correct_specs = {spec for spec, metadata in labels.items() if metadata["label"] == "correct"}
    changed_correct = {
        "spec-28": ["abstain", "unresolved-decision-threshold"],
        "spec-42": ["abstain", "unresolved-manual-correction-present"],
        "spec-48": ["abstain", "unresolved-decision-threshold"],
    }
    for spec in sorted(correct_specs):
        if spec in changed_correct:
            assert observed["2.1.0"]["results"][spec] == changed_correct[spec]
        else:
            assert observed["2.1.0"]["results"][spec] == observed["2.0.0"]["results"][spec]
