from __future__ import annotations

import hashlib
from pathlib import Path

from scripts.build_code_lane_v310_schema_release import build_release

_V020_TREE_DIGEST = "cc924eefe740d3d411e8a8c93e968d046ab946dd409292778364293bb12ba343"


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for relative, payload in sorted(_tree_bytes(root).items()):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest()


def test_v021_release_is_reproducible_and_v020_is_immutable(
    project_root: Path, tmp_path: Path
) -> None:
    baseline = project_root / "reference/schemas-v0.20.0"
    accepted = project_root / "reference/schemas-v0.21.0"
    packaged = project_root / "src/sc_referee/resources/schemas-v0.21.0"
    before = _tree_bytes(baseline)
    assert _tree_digest(baseline) == _V020_TREE_DIGEST

    output = tmp_path / "schemas-v0.21.0"
    assert build_release(output) == 81

    assert _tree_bytes(baseline) == before
    assert _tree_digest(baseline) == _V020_TREE_DIGEST
    assert _tree_bytes(output) == _tree_bytes(accepted)
    assert _tree_bytes(packaged) == _tree_bytes(accepted)


def test_v021_code_lane_identity_pairs_are_exact(project_root: Path) -> None:
    root = project_root / "reference/schemas-v0.21.0"
    qualification = (
        root / "examples/detector-qualification.code-csv-dependence.example.json"
    ).read_text(encoding="utf-8")
    metric_set = (
        root / "examples/qualification-metric-set.code-csv-dependence.example.json"
    ).read_text(encoding="utf-8")
    for payload in (qualification, metric_set):
        assert '"detector_id":"detector:bounded-code-csv-dependence-conflict"' in payload
        assert '"detector_version":"3.1.0"' in payload
