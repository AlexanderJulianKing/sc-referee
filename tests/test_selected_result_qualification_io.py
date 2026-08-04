from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.selected_result_qualification_io import (
    QualificationIOError,
    RootedReader,
    canonical_relative_path,
    write_canonical_json_exclusive,
)

from sc_referee.core.ids import semantic_digest, sha256_digest


def _write_case_tree(root: Path) -> tuple[Path, dict[str, bytes]]:
    case = root / "cases" / "case-a"
    (case / "inputs").mkdir(parents=True)
    (case / "results").mkdir()
    (case / "workflow").mkdir()
    payloads = {
        "inputs/data.csv": b"group,total\nall,2\n",
        "results/report.md": b"[selected-result] all,2\n",
        "workflow/analyze.py": (
            b"from pathlib import Path\n"
            b"value = Path('inputs/data.csv').read_text().splitlines()[1]\n"
            b"Path('results/report.md').write_text(f'[selected-result] {value}\\n')\n"
        ),
    }
    modes = {
        "inputs/data.csv": 0o640,
        "results/report.md": 0o600,
        "workflow/analyze.py": 0o750,
    }
    for relative, payload in payloads.items():
        path = case / relative
        path.write_bytes(payload)
        path.chmod(modes[relative])
    return case, payloads


def _expected_case_inventory(case: Path, payloads: dict[str, bytes]) -> list[dict[str, object]]:
    return [
        {
            "path": relative,
            "content_digest": sha256_digest(payloads[relative]),
            "byte_length": len(payloads[relative]),
            "executable": bool((case / relative).stat().st_mode & 0o111),
        }
        for relative in sorted(payloads)
    ]


@pytest.mark.parametrize(
    "raw",
    [
        "",
        ".",
        "..",
        "/absolute",
        "//absolute",
        "a/../b",
        "a/./b",
        "a//b",
        "a/b/",
        "a\\b",
        "a\x00b",
    ],
)
def test_canonical_relative_path_rejects_escapes_and_noncanonical_forms(raw: str) -> None:
    with pytest.raises(QualificationIOError):
        canonical_relative_path(raw)


def test_rooted_reader_reads_and_hashes_same_regular_file_descriptor(
    tmp_path: Path,
) -> None:
    root = tmp_path / "pack"
    nested = root / "records"
    nested.mkdir(parents=True)
    payload = b"qualification evidence\n"
    (nested / "case.json").write_bytes(payload)

    with RootedReader(root) as reader:
        result = reader.read("records/case.json", max_bytes=len(payload))
        assert result.relative_path == "records/case.json"
        assert result.data == payload
        assert result.content_digest == sha256_digest(payload)
        assert reader.read_bytes("records/case.json") == payload

    assert reader.closed


def test_rooted_reader_captures_one_immutable_case_tree(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    case, payloads = _write_case_tree(root)

    with RootedReader(case) as reader:
        tree = reader.read_case_tree()

    assert tree.paths == tuple(sorted(payloads))
    assert tree.total_bytes == sum(len(payload) for payload in payloads.values())
    for relative, payload in payloads.items():
        item = tree.read(relative)
        assert item.data == payload
        assert item.content_digest == sha256_digest(payload)
        assert tree.read_bytes(relative) == payload
    assert tuple(item.mode for item in tree.files) == tuple(
        stat.S_IMODE((case / relative).stat().st_mode) for relative in sorted(payloads)
    )


def test_rooted_reader_case_tree_rejects_drift_between_full_scans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "pack"
    case, _ = _write_case_tree(root)
    source = case / "inputs" / "data.csv"

    with RootedReader(case) as reader:
        original_scan = reader._scan_case_tree
        scan_count = 0

        def mutate_after_scan(**arguments: Any) -> None:
            nonlocal scan_count
            original_scan(**arguments)
            if arguments["depth"] == 0:
                scan_count += 1
                if scan_count == 1:
                    source.write_bytes(b"group,total\nall,999\n")

        monkeypatch.setattr(reader, "_scan_case_tree", mutate_after_scan)
        with pytest.raises(QualificationIOError, match="changed between"):
            reader.read_case_tree()


def test_rooted_reader_case_tree_rejects_descendant_symlink(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    case, _ = _write_case_tree(root)
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"outside\n")
    (case / "inputs" / "linked.txt").symlink_to(outside)

    with RootedReader(case) as reader:
        with pytest.raises(QualificationIOError, match="symbolic links"):
            reader.read_case_tree()


def test_rooted_reader_rejects_root_symlink(tmp_path: Path) -> None:
    real_root = tmp_path / "real"
    real_root.mkdir()
    linked_root = tmp_path / "linked"
    linked_root.symlink_to(real_root, target_is_directory=True)

    with pytest.raises(QualificationIOError, match="non-symlink directory"):
        RootedReader(linked_root)


def test_rooted_reader_rejects_non_directory_root(tmp_path: Path) -> None:
    root_file = tmp_path / "file"
    root_file.write_text("not a root", encoding="utf-8")

    with pytest.raises(QualificationIOError, match="non-symlink directory"):
        RootedReader(root_file)


def test_rooted_reader_rejects_descendant_directory_symlink(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "record.json").write_text("{}\n", encoding="utf-8")
    (root / "linked").symlink_to(outside, target_is_directory=True)

    with RootedReader(root) as reader:
        with pytest.raises(QualificationIOError, match="real directories"):
            reader.read("linked/record.json")


def test_rooted_reader_rejects_descendant_file_symlink(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    outside = tmp_path / "outside.json"
    root.mkdir()
    outside.write_text("{}\n", encoding="utf-8")
    (root / "record.json").symlink_to(outside)

    with RootedReader(root) as reader:
        with pytest.raises(QualificationIOError, match="regular file"):
            reader.read("record.json")


def test_rooted_reader_rejects_directory_as_final_input(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    (root / "record.json").mkdir(parents=True)

    with RootedReader(root) as reader:
        with pytest.raises(QualificationIOError, match="regular file"):
            reader.read("record.json")


def test_rooted_reader_enforces_byte_limit(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    root.mkdir()
    (root / "record.json").write_bytes(b"1234")

    with RootedReader(root) as reader:
        with pytest.raises(QualificationIOError, match="byte limit"):
            reader.read("record.json", max_bytes=3)


def test_rooted_reader_detects_in_place_mutation_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "pack"
    root.mkdir()
    path = root / "record.bin"
    path.write_bytes(b"original")
    original_read = os.read
    mutated = False

    def mutating_read(descriptor: int, count: int) -> bytes:
        nonlocal mutated
        result = original_read(descriptor, count)
        if result and not mutated:
            mutated = True
            path.write_bytes(b"changed-content")
        return result

    monkeypatch.setattr(os, "read", mutating_read)
    with RootedReader(root) as reader:
        with pytest.raises(QualificationIOError, match="mutated"):
            reader.read("record.bin")


def test_rooted_reader_detects_directory_entry_replacement_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "pack"
    root.mkdir()
    path = root / "record.bin"
    replacement = root / "replacement.bin"
    path.write_bytes(b"original")
    replacement.write_bytes(b"replacement")
    original_read = os.read
    replaced = False

    def replacing_read(descriptor: int, count: int) -> bytes:
        nonlocal replaced
        result = original_read(descriptor, count)
        if result and not replaced:
            replaced = True
            replacement.replace(path)
        return result

    monkeypatch.setattr(os, "read", replacing_read)
    with RootedReader(root) as reader:
        with pytest.raises(QualificationIOError, match=r"mutated|replaced"):
            reader.read("record.bin")


def test_rooted_reader_requires_canonical_json_bytes(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    root.mkdir()
    (root / "canonical.json").write_bytes(b'{"a":1,"b":2}\n')
    (root / "pretty.json").write_bytes(b'{"b": 2, "a": 1}\n')

    with RootedReader(root) as reader:
        assert reader.read_canonical_json("canonical.json") == {"a": 1, "b": 2}
        with pytest.raises(QualificationIOError, match="must be canonical"):
            reader.read_canonical_json("pretty.json")


def test_exclusive_json_output_is_canonical_and_never_overwrites(tmp_path: Path) -> None:
    root = tmp_path / "output"
    (root / "records").mkdir(parents=True)
    expected = b'{"a":1,"z":2}\n'

    digest = write_canonical_json_exclusive(root, "records/result.json", {"z": 2, "a": 1})

    assert (root / "records" / "result.json").read_bytes() == expected
    assert digest == sha256_digest(expected)
    with pytest.raises(QualificationIOError, match="overwrite is forbidden"):
        write_canonical_json_exclusive(root, "records/result.json", {"a": 3})
    assert (root / "records" / "result.json").read_bytes() == expected
    assert not list((root / "records").glob(".qualification-*.tmp"))


def test_exclusive_json_output_rejects_symlinked_parent(tmp_path: Path) -> None:
    root = tmp_path / "output"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(QualificationIOError, match="real directories"):
        write_canonical_json_exclusive(root, "linked/result.json", {"a": 1})
    assert not (outside / "result.json").exists()


def test_case_tree_snapshot_has_exact_verifier_digest_bytes_and_modes(
    tmp_path: Path,
) -> None:
    pack = tmp_path / "pack"
    case, payloads = _write_case_tree(pack)
    destination = tmp_path / "snapshot"
    destination.mkdir()
    expected = _expected_case_inventory(case, payloads)

    with RootedReader(pack) as reader:
        snapshot = reader.snapshot_case_tree("cases/case-a", destination)

    assert snapshot == {
        "source_relative_path": "cases/case-a",
        "retained_files": expected,
        "case_tree_digest": semantic_digest(expected),
        "file_count": len(expected),
        "total_bytes": sum(len(payload) for payload in payloads.values()),
    }
    for relative, payload in payloads.items():
        copied = destination / relative
        assert copied.read_bytes() == payload
        assert stat.S_IMODE(copied.stat().st_mode) == stat.S_IMODE((case / relative).stat().st_mode)


def test_case_tree_snapshot_rejects_source_mutation_during_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pack = tmp_path / "pack"
    case, _ = _write_case_tree(pack)
    destination = tmp_path / "snapshot"
    destination.mkdir()
    source = case / "inputs" / "data.csv"
    original_read = os.read
    mutated = False

    def mutating_read(descriptor: int, count: int) -> bytes:
        nonlocal mutated
        payload = original_read(descriptor, count)
        if payload and not mutated:
            mutated = True
            source.write_bytes(b"group,total\nall,999\n")
        return payload

    monkeypatch.setattr(os, "read", mutating_read)
    with RootedReader(pack) as reader:
        with pytest.raises(QualificationIOError, match="mutated"):
            reader.snapshot_case_tree("cases/case-a", destination)


def test_case_tree_snapshot_revalidates_source_additions_after_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pack = tmp_path / "pack"
    case, _ = _write_case_tree(pack)
    destination = tmp_path / "snapshot"
    destination.mkdir()

    with RootedReader(pack) as reader:
        original_verify = reader._verify_directories
        verification_count = 0

        def adding_after_first_copy(directories: Any) -> None:
            nonlocal verification_count
            original_verify(directories)
            verification_count += 1
            if verification_count == 1:
                (case / "added-after-copy.txt").write_bytes(b"late addition\n")

        monkeypatch.setattr(reader, "_verify_directories", adding_after_first_copy)
        with pytest.raises(QualificationIOError, match="changed after it was copied"):
            reader.snapshot_case_tree("cases/case-a", destination)


def test_case_tree_snapshot_rejects_source_replacement_during_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pack = tmp_path / "pack"
    case, _ = _write_case_tree(pack)
    destination = tmp_path / "snapshot"
    destination.mkdir()
    source = case / "inputs" / "data.csv"
    replacement = pack / "replacement.csv"
    replacement.write_bytes(b"group,total\nall,7\n")
    original_read = os.read
    replaced = False

    def replacing_read(descriptor: int, count: int) -> bytes:
        nonlocal replaced
        payload = original_read(descriptor, count)
        if payload and not replaced:
            replaced = True
            replacement.replace(source)
        return payload

    monkeypatch.setattr(os, "read", replacing_read)
    with RootedReader(pack) as reader:
        with pytest.raises(QualificationIOError, match=r"mutated|replaced"):
            reader.snapshot_case_tree("cases/case-a", destination)


def test_case_tree_snapshot_rejects_source_descendant_symlink(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    case, _ = _write_case_tree(pack)
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"outside\n")
    (case / "inputs" / "linked.txt").symlink_to(outside)
    destination = tmp_path / "snapshot"
    destination.mkdir()

    with RootedReader(pack) as reader:
        with pytest.raises(QualificationIOError, match="symbolic links"):
            reader.snapshot_case_tree("cases/case-a", destination)


def test_case_tree_snapshot_never_overwrites_nonempty_destination(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    _write_case_tree(pack)
    destination = tmp_path / "snapshot"
    destination.mkdir()
    marker = destination / "existing.txt"
    marker.write_bytes(b"keep me\n")

    with RootedReader(pack) as reader:
        with pytest.raises(QualificationIOError, match="destination must be empty"):
            reader.snapshot_case_tree("cases/case-a", destination)
    assert marker.read_bytes() == b"keep me\n"


def test_case_tree_snapshot_rejects_destination_root_symlink(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    _write_case_tree(pack)
    real_destination = tmp_path / "real-snapshot"
    real_destination.mkdir()
    linked_destination = tmp_path / "linked-snapshot"
    linked_destination.symlink_to(real_destination, target_is_directory=True)

    with RootedReader(pack) as reader:
        with pytest.raises(QualificationIOError, match="non-symlink directory"):
            reader.snapshot_case_tree("cases/case-a", linked_destination)
    assert not list(real_destination.iterdir())


def test_case_tree_snapshot_rejects_injected_destination_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pack = tmp_path / "pack"
    _write_case_tree(pack)
    destination = tmp_path / "snapshot"
    destination.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    original_mkdir = os.mkdir
    injected = False

    def injecting_mkdir(
        path: str | bytes,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> None:
        nonlocal injected
        if path == "inputs" and dir_fd is not None and not injected:
            injected = True
            (destination / "inputs").symlink_to(outside, target_is_directory=True)
            return
        original_mkdir(path, mode=mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "mkdir", injecting_mkdir)
    with RootedReader(pack) as reader:
        with pytest.raises(QualificationIOError, match="not a directory"):
            reader.snapshot_case_tree("cases/case-a", destination)
    assert not list(outside.iterdir())
