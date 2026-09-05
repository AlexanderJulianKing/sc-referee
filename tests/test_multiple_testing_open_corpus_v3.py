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
_FROZEN = {
    _ROOT / "adapter_replay_records_v2_1.json": (
        "7c37669c8ccfdb0b754aa03ee1dbcee1dac78fa4bb44105e17c5d1886aaed502"
    ),
    Path("evaluation/development/blind-envelope-12-2026-08-26/adapter_replay_records_v2_2.json"): (
        "f8b7808b3baee264e9c496e2e899686af235e72c37b9647ce4255d10adbb02d8"
    ),
    Path("evaluation/development/blind-envelope-13-2026-08-26/adapter_replay_records_v2_3.json"): (
        "d171c40e0715ff2b0f4c65bb667e817b78575ea1f2d73a8bc9af0869d3143489"
    ),
}


def test_open_corpus_v3_is_adapter_level_byte_equal_to_v2_3(tmp_path: Path) -> None:
    labels = json.loads((_ROOT / "specs" / "labels.json").read_text(encoding="utf-8"))
    assert Counter(value["label"] for value in labels.values()) == {
        "correct": 25,
        "misstep": 25,
    }
    for path, digest in _FROZEN.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest

    namespace = runpy.run_path(str(_ROOT / "adapter_replay.py"))
    replay = cast(Callable[..., dict[str, dict[str, Any]]], namespace["replay_open_corpus"])
    observed = replay(
        corpus_root=_ROOT,
        scratch_root=tmp_path / "replay",
        schema_root=Path("reference/schemas-v0.21.0"),
    )
    frozen = json.loads((_ROOT / "adapter_replay_records_v2_1.json").read_text(encoding="utf-8"))
    assert canonical_json({key: observed[key] for key in frozen}) == canonical_json(frozen)
    assert observed["2.2.0"]["results"] == observed["2.1.0"]["results"]
    assert observed["2.3.0"]["results"] == observed["2.2.0"]["results"]
    assert observed["3.0.0"]["results"] == observed["2.3.0"]["results"]
    assert observed["3.0.0"]["correct_candidates"] == 0
    assert observed["3.0.0"]["misstep_candidates"] == 19
