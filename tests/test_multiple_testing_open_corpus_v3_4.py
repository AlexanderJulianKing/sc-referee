from __future__ import annotations

import hashlib
import json
import runpy
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import canonical_json

_ROOT = Path("evaluation/development/multitest-open-corpus-v1")
_V3_2 = Path("evaluation/development/multitest-code-slice-v3_2/adapter_replay_records_v3_2.json")
_V3_3 = Path("evaluation/development/multitest-code-slice-v3_3/adapter_replay_records_v3_3.json")
_V3_4 = Path("evaluation/development/multitest-code-slice-v3_4/adapter_replay_records_v3_4.json")
_FROZEN = {
    _ROOT / "adapter_replay_records_v2_1.json": (
        "7c37669c8ccfdb0b754aa03ee1dbcee1dac78fa4bb44105e17c5d1886aaed502"
    ),
    _V3_2: "c3a0ea932f20b0d049f239dd3b7f58a5c304fed52b079b179dd5740564d14b92",
    _V3_3: "4b42ee3a517bd95591eac9f0d7bb9a497728f9df708c57fc99298d7205df83ce",
}


def test_open_corpus_is_byte_identical_to_v3_3(tmp_path: Path) -> None:
    for path, digest in _FROZEN.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    namespace = runpy.run_path(
        # The versioned 3.5 replay still emits the frozen 3.3.0 and 3.4.0 adapter rows;
        # only the active development adapter advanced past 3.4.
        "evaluation/development/multitest-code-slice-v3_5/adapter_replay_v3_5.py"
    )
    replay = cast(Callable[..., dict[str, dict[str, Any]]], namespace["replay_open_corpus"])
    observed = replay(
        corpus_root=_ROOT,
        scratch_root=tmp_path / "replay",
        schema_root=Path("reference/schemas-v0.21.0"),
    )
    v33 = json.loads(_V3_3.read_text(encoding="utf-8"))
    v34 = json.loads(_V3_4.read_text(encoding="utf-8"))
    assert canonical_json(observed["3.3.0"]) == canonical_json(v33)
    assert canonical_json(observed["3.4.0"]) == canonical_json(v34)
    # No 3.4 admission moves a single one of the fifty adapter rows.
    assert observed["3.4.0"]["results"] == observed["3.3.0"]["results"]
    assert observed["3.4.0"]["correct_candidates"] == 0
    assert observed["3.4.0"]["misstep_candidates"] == 19
    # The adapter-level spec-30 exception is preserved, not crossed.
    assert observed["3.4.0"]["results"]["spec-30"] == ["abstain", "api-resolution-ambiguous"]
