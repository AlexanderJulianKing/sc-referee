from __future__ import annotations

import ast
import base64
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts import run_selected_result_verifier_qualification_block as launcher


def _record_hash(payload: bytes) -> str:
    encoded = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=")
    return "sha256=" + encoded.decode("ascii")


def _write_distribution(root: Path, distribution_name: str, *, version: str = "1.0.0") -> None:
    package_name = distribution_name.replace("-", "_")
    dist_info_name = distribution_name.replace("-", "_") + f"-{version}.dist-info"
    files = {
        f"{package_name}/__init__.py": f'NAME = "{distribution_name}"\n'.encode(),
        f"{dist_info_name}/METADATA": (
            f"Metadata-Version: 2.1\nName: {distribution_name}\nVersion: {version}\n"
        ).encode(),
        f"{dist_info_name}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\n",
    }
    if distribution_name == "sc-referee-evaluation":
        files["sc_referee_evaluation/selected_result_qualification_runner.py"] = b"RUNNER = True\n"
        files["sc_referee_evaluation/qualification_identity.py"] = b"IDENTITY = True\n"
    for relative_path, payload in files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    record_path = f"{dist_info_name}/RECORD"
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    for relative_path, payload in sorted(files.items()):
        writer.writerow((relative_path, _record_hash(payload), len(payload)))
    writer.writerow((record_path, "", ""))
    (root / record_path).write_text(output.getvalue(), encoding="utf-8", newline="")


def _distribution_root(tmp_path: Path, name: str = "site-packages") -> Path:
    root = tmp_path / name
    root.mkdir()
    for distribution_name in launcher.REQUIRED_DISTRIBUTIONS:
        _write_distribution(root, distribution_name)
    return root


def _candidate_freeze(root: Path) -> dict[str, Any]:
    value: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_runner_freeze",
        "runner_version": "1.1.0-development",
        "freeze_identity": "selected-result-verifier-v1.1.0-execution-tuple",
        "distribution_records": {
            name: launcher.freeze_distribution_record(name, search_paths=[root])
            for name in launcher.REQUIRED_DISTRIBUTIONS
        },
    }
    value["runner_freeze_digest"] = launcher._semantic_digest(value)
    return value


def _write_freeze(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8")


def _clear_launcher_approval() -> None:
    main_module = sys.modules.get("__main__")
    if main_module is not None and hasattr(main_module, launcher.APPROVED_DIGEST_ATTRIBUTE):
        delattr(main_module, launcher.APPROVED_DIGEST_ATTRIBUTE)
    if main_module is not None and hasattr(main_module, launcher.APPROVED_LAUNCH_RECEIPT_ATTRIBUTE):
        delattr(main_module, launcher.APPROVED_LAUNCH_RECEIPT_ATTRIBUTE)


def _launch_arguments(path: Path, receipt: Path) -> list[str]:
    return [
        "freeze-oracles",
        "--runner-freeze",
        str(path),
        "--phase-launch-receipt",
        str(receipt),
        "--block",
        "pilot",
        "--provider-slot",
        "provider-family-1",
    ]


def test_launcher_module_imports_no_qualification_or_third_party_code(
    project_root: Path,
) -> None:
    path = project_root / "scripts" / "run_selected_result_verifier_qualification_block.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported_roots: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= set(sys.stdlib_module_names) | {"__future__"}
    assert not {name for name in imported_roots if name.startswith("sc_referee")}


def test_unfrozen_anchor_rejects_before_distribution_discovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "candidate.json"
    value: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_runner_freeze",
        "runner_version": "1.1.0-development",
        "freeze_identity": "selected-result-verifier-v1.1.0-execution-tuple",
        "distribution_records": {},
    }
    value["runner_freeze_digest"] = launcher._semantic_digest(value)
    _write_freeze(path, value)

    def forbidden_discovery(**_: Any) -> Any:
        raise AssertionError("Distribution discovery occurred before the official anchor check.")

    monkeypatch.setattr(launcher.importlib.metadata, "distributions", forbidden_discovery)
    assert launcher.OFFICIAL_RUNNER_FREEZE_DIGEST == "UNFROZEN"
    with pytest.raises(launcher.QualificationLauncherError, match="officially approved"):
        launcher.validate_pre_import_environment(path)


def test_launcher_verifies_all_records_before_importing_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _distribution_root(tmp_path)
    freeze = _candidate_freeze(root)
    path = tmp_path / "candidate.json"
    _write_freeze(path, freeze)
    monkeypatch.setattr(
        launcher,
        "OFFICIAL_RUNNER_FREEZE_DIGEST",
        freeze["runner_freeze_digest"],
    )
    calls: list[str] = []
    receipt_path = tmp_path / "phase-receipt.json"
    receipt_path.write_text("{}", encoding="utf-8")
    receipt = {"artifact_kind": "qualification_phase_launch_receipt"}

    monkeypatch.setattr(
        launcher,
        "_validated_external_launch_receipt",
        lambda *_args, **_kwargs: receipt,
    )

    def fake_import(name: str) -> SimpleNamespace:
        calls.append(name)
        main_module = sys.modules["__main__"]
        assert (
            getattr(main_module, launcher.APPROVED_DIGEST_ATTRIBUTE)
            == freeze["runner_freeze_digest"]
        )
        return SimpleNamespace(
            __file__=str(
                root / "sc_referee_evaluation" / "selected_result_qualification_runner.py"
            ),
            main=lambda argv: 17,
        )

    monkeypatch.setattr(launcher.importlib, "import_module", fake_import)
    try:
        assert (
            launcher.launch(
                _launch_arguments(path, receipt_path),
                search_paths=[root],
            )
            == 17
        )
    finally:
        _clear_launcher_approval()
    assert calls == ["sc_referee_evaluation.selected_result_qualification_runner"]


def test_payload_drift_rejects_before_runner_import(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _distribution_root(tmp_path)
    freeze = _candidate_freeze(root)
    path = tmp_path / "candidate.json"
    _write_freeze(path, freeze)
    monkeypatch.setattr(
        launcher,
        "OFFICIAL_RUNNER_FREEZE_DIGEST",
        freeze["runner_freeze_digest"],
    )
    (root / "cryptography" / "__init__.py").write_text("DRIFT = True\n", encoding="utf-8")
    receipt_path = tmp_path / "phase-receipt.json"
    receipt_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        launcher.importlib,
        "import_module",
        lambda name: pytest.fail(f"Imported qualification runner after payload drift: {name}"),
    )

    with pytest.raises(launcher.QualificationLauncherError, match="has drifted"):
        launcher.launch(
            _launch_arguments(path, receipt_path),
            search_paths=[root],
        )


def test_record_drift_rejects_before_runner_import(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _distribution_root(tmp_path)
    freeze = _candidate_freeze(root)
    path = tmp_path / "candidate.json"
    _write_freeze(path, freeze)
    monkeypatch.setattr(
        launcher,
        "OFFICIAL_RUNNER_FREEZE_DIGEST",
        freeze["runner_freeze_digest"],
    )
    record = next(root.glob("cffi-*.dist-info/RECORD"))
    record.write_bytes(record.read_bytes() + b"\n")
    receipt_path = tmp_path / "phase-receipt.json"
    receipt_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        launcher.importlib,
        "import_module",
        lambda name: pytest.fail(f"Imported qualification runner after RECORD drift: {name}"),
    )

    with pytest.raises(launcher.QualificationLauncherError, match=r"RECORD|does not replay"):
        launcher.launch(
            _launch_arguments(path, receipt_path),
            search_paths=[root],
        )


def test_duplicate_distribution_is_rejected(tmp_path: Path) -> None:
    first = _distribution_root(tmp_path, "first")
    second = _distribution_root(tmp_path, "second")

    with pytest.raises(launcher.QualificationLauncherError, match="found 2"):
        launcher.freeze_distribution_record("sc-referee", search_paths=[first, second])


def test_editable_or_startup_hook_distribution_is_rejected(tmp_path: Path) -> None:
    root = _distribution_root(tmp_path)
    dist_info = next(root.glob("sc_referee-*.dist-info"))
    record = dist_info / "RECORD"
    startup_path = root / "__editable__.sc_referee.pth"
    startup_payload = b"/untrusted/source/tree\n"
    startup_path.write_bytes(startup_payload)
    rows = list(csv.reader(io.StringIO(record.read_text(encoding="utf-8"), newline="")))
    rows.insert(0, (startup_path.name, _record_hash(startup_payload), str(len(startup_payload))))
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerows(rows)
    record.write_text(output.getvalue(), encoding="utf-8", newline="")

    with pytest.raises(launcher.QualificationLauncherError, match="editable or startup-hook"):
        launcher.freeze_distribution_record("sc-referee", search_paths=[root])
