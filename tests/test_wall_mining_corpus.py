"""Isolation and transport regressions for the non-measurement wall corpus."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from scripts import wall_mining_corpus as corpus


def _generated_case() -> dict[str, str]:
    return {
        "domain": "plant physiology",
        "analysis_py": """import csv
from pathlib import Path
from scipy import stats

with Path("data/input.csv").open(newline="", encoding="ascii") as handle:
    rows = list(csv.DictReader(handle))
groups = {}
for row in rows:
    groups.setdefault(row["arm"], []).append(float(row["value"]))
left = groups["A"]
right = groups["B"]
result = stats.ttest_ind(left, right)
Path("results/report.md").write_text(str(result), encoding="utf-8")
""",
        "data_csv": "unit_id,arm,value\nu1,A,1.0\nu2,A,2.0\nu3,B,3.0\nu4,B,4.0\n",
        "data_description_md": "A small plant comparison.\nIndependent unit column: unit_id\n",
    }


def test_wall_mining_prompt_is_open_and_omits_recognizer_taxonomy() -> None:
    prompt = corpus._prompt(0, 40).casefold()
    assert "sc-referee" not in prompt
    assert "error class" not in prompt
    assert "role" not in prompt
    assert "label" not in prompt
    assert "blind" not in prompt


def test_wall_mining_builds_isolated_purpose_stamped_census(
    tmp_path: Path, monkeypatch: Any
) -> None:
    binary = tmp_path / "claude"
    binary.write_text("stub", encoding="utf-8")
    monkeypatch.setattr(corpus, "CLAUDE_PINNED", binary)
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        calls.append(argv)
        envelope = {
            "result": json.dumps(_generated_case()),
            "modelUsage": {"claude-haiku-test": {}},
        }
        return subprocess.CompletedProcess(argv, 0, json.dumps(envelope).encode(), b"")

    monkeypatch.setattr(corpus.subprocess, "run", fake_run)
    run_root = corpus.build_corpus(tmp_path, 2)
    assert run_root == tmp_path / "evaluation/development/wall-mining-corpus/run-2"
    assert len(calls) == 2
    assert all(argv[argv.index("--model") + 1] == "haiku" for argv in calls)
    assert corpus.MAX_CONCURRENCY == 3
    assert not (tmp_path / "evaluation/qualification").exists()
    for path in run_root.rglob("*.json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        assert value["record_purpose"] == "development_wall_mining", path
    census = json.loads((run_root / "wall-frequency-census.json").read_text())
    assert census["case_count"] == 2
    assert census["generation_calls"] == 2
    assert census["measurement_authority"] == "none"
    markdown = (run_root / "wall-frequency-census.md").read_text(encoding="utf-8")
    assert "non-measurement" in markdown
    translations = list(run_root.glob("cases/*/lock-translation.json"))
    assert len(translations) == 2
    assert all(
        json.loads(path.read_text())["translation_outcome"] == "lock-projected"
        for path in translations
    )
