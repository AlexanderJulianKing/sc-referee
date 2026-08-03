from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKET_ROOT = ROOT / "evaluation" / "scienceagentbench-public-v1"


def _digest(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _manifest() -> dict[str, Any]:
    value = json.loads((PACKET_ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_scienceagentbench_public_packet_is_answer_isolated_and_pinned() -> None:
    manifest = _manifest()

    assert manifest["manifest_version"] == "scienceagentbench-public-recurrence-v1"
    assert manifest["corpus_role"] == "public_development"
    assert manifest["source"] == {
        "dataset_revision": "9c6e96c9e74572e979b0930ee735041cef528cb7",
        "dataset_uri": "https://huggingface.co/datasets/osunlp/ScienceAgentBench",
        "license": "CC-BY-4.0-with-upstream-per-task-exceptions",
        "repository_revision": "c26e151ed601ba109dc4d35e057ff8e73fec469d",
        "repository_uri": "https://github.com/OSU-NLP-Group/ScienceAgentBench",
    }
    assert manifest["redistribution"] == {
        "benchmark_archive_permitted": False,
        "gold_programs_permitted": False,
        "local_packet_permitted": True,
    }

    cases = manifest["cases"]
    assert isinstance(cases, list) and [case["instance_id"] for case in cases] == [12, 70]
    for case in cases:
        assert case["benchmark_derived"] is True
        assert case["answer_side_present"] is False
        assert case["qualification_status"] == "excluded"

        packet_path = PACKET_ROOT / case["author_packet_path"]
        assert packet_path.is_file() and not packet_path.is_symlink()
        assert _digest(packet_path) == case["author_packet_digest"]

    retained_files = {
        path.relative_to(PACKET_ROOT).as_posix()
        for path in PACKET_ROOT.rglob("*")
        if path.is_file()
    }
    assert retained_files == {
        "README.md",
        "manifest.json",
        "task-0012/agent-task.md",
        "task-0070/agent-task.md",
    }


def test_scienceagentbench_packet_preserves_development_only_ceiling() -> None:
    readme = (PACKET_ROOT / "README.md").read_text(encoding="utf-8")
    tasks = [
        (PACKET_ROOT / case["author_packet_path"]).read_text(encoding="utf-8")
        for case in _manifest()["cases"]
    ]

    assert "Qualification status: excluded" in readme
    assert all("ineligible for detector qualification or promotion" in task for task in tasks)
    assert all("do not execute" in task.casefold() for task in tasks)
