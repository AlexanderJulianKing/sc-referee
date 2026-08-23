from __future__ import annotations

import ast
import errno
import importlib
import json
import os
import stat
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from conftest import StaticWorld1Case
from sc_referee_evaluation.audit_ladder.slice_c import transaction as transaction_module
from sc_referee_evaluation.audit_ladder.slice_c.composition import SliceCCompositionResultV1
from sc_referee_evaluation.audit_ladder.slice_c.core import (
    RefusalFacetV1,
    SliceCContractError,
    WorkerControllerResultV1,
    canonical_frame,
    sha256,
)
from sc_referee_evaluation.audit_ladder.slice_c.launcher import _worker_source
from sc_referee_evaluation.audit_ladder.slice_c.observations import (
    observation_runtime_premise_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.renderer import (
    SliceCRendererError,
    render_world1_report_v1,
    renderer_runtime_premise_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.repository import load_registry_bundle_v1
from sc_referee_evaluation.audit_ladder.slice_c.runtime import (
    read_runtime_artifacts_v1,
    runtime_root_path_v1,
    validate_prelaunch_provenance_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.transaction import render_slice_c_report_v1


def _success(case: StaticWorld1Case, request_raw: bytes) -> WorkerControllerResultV1:
    response = canonical_frame(
        {
            "facts": case.h5ad_facts.to_dict(),
            "schema": "slice-c-worker-success-v1",
            "worker_request_sha256": sha256(request_raw),
        }
    )
    return WorkerControllerResultV1(
        facts=case.h5ad_facts,
        refusal=None,
        request_sha256=sha256(request_raw),
        response_sha256=sha256(response),
    )


def test_actual_entrypoint_transaction_with_authenticated_worker_boundary(
    static_world1_case: StaticWorld1Case,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launches: list[tuple[str, str]] = []

    def worker(*, registry_raw: bytes, request_raw: bytes) -> WorkerControllerResultV1:
        launches.append((sha256(registry_raw), sha256(request_raw)))
        return _success(static_world1_case, request_raw)

    monkeypatch.setattr(
        "sc_referee_evaluation.audit_ladder.slice_c.transaction.run_isolated_worker_v1",
        worker,
    )
    first = render_slice_c_report_v1(
        static_world1_case.context,
        static_world1_case.request,
    )
    second = render_slice_c_report_v1(
        static_world1_case.context,
        static_world1_case.request,
    )
    assert first == second
    assert (len(first), sha256(first)) == (
        49_609,
        "sha256:217e40ce0a4f9781191bac82d8e81410aa981186b3fec57593bb53896e45b3ca",
    )
    assert len(launches) == 10
    assert set(launches) == {
        (
            "sha256:9446a9c727342487ff78dc1907b588ebcab9ce51a144054baeb2fd4c8df8641b",
            "sha256:9bce5ddb0f09e5b2563aa842fc729376c8c08cffc460d7fb75dbce2c143f39fd",
        )
    }


def test_authenticated_worker_program_is_compile_closed() -> None:
    source = _worker_source()
    raw = source.encode("utf-8", "strict")
    assert (len(raw), sha256(raw)) == (
        47_838,
        "sha256:fcb341d6729712833964012a8fc4d46e28fc296188753fe20dcebcd7c4e94362",
    )
    compile(source, "<slice-c-isolated-worker>", "exec", dont_inherit=True, optimize=0)


def test_destination_premise_is_exact_seven_field_transform_and_self_digest() -> None:
    old_path = Path(
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime/"
        "h5ad-tier1-scanpy1115-premise.json"
    )
    old_raw = old_path.read_bytes()
    assert (len(old_raw), sha256(old_raw)) == (
        3_625,
        "sha256:9fd7af5c11a073183d61135d1473a785a1628ffbb59ae33f407b7d974be7a4a0",
    )
    candidate = json.loads(old_raw)
    old_prefix = "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime"
    new_prefix = "/Users/alexanderking/sc-referee-runtimes"
    changed_paths = (
        ("launch", "manual_site_packages"),
        ("manifests", "cpython", "path"),
        ("manifests", "record_reconciliation", "path"),
        ("manifests", "runtime", "path"),
        ("manifests", "wheels", "path"),
        ("measurement", "path"),
        ("python", "base_prefix"),
    )
    for path in changed_paths:
        parent = candidate
        for member in path[:-1]:
            parent = parent[member]
        value = parent[path[-1]]
        assert type(value) is str and value.startswith(old_prefix)
        parent[path[-1]] = new_prefix + value[len(old_prefix) :]
    candidate.pop("premise_digest")
    unsigned = canonical_frame(candidate)[:-1]
    candidate["premise_digest"] = sha256(unsigned)
    expected = canonical_frame(candidate)
    actual = read_runtime_artifacts_v1()["premise"]
    assert actual == expected
    assert (len(actual), sha256(actual), candidate["premise_digest"]) == (
        3_443,
        "sha256:0f3db3490b640ed80a12c94038c3d78f18d5aa431cab42e8ec73ee2b54b21d04",
        "sha256:09fe04ea03c03221bf20c00b5e45cd8f66f00d7476f98da64df5dcde79dc7eeb",
    )
    assert old_prefix.encode() not in actual
    assert actual.count(new_prefix.encode()) == 7


def test_relocated_seal_probe_and_all_descriptor_roots_are_exact() -> None:
    artifacts = read_runtime_artifacts_v1()
    registry = load_registry_bundle_v1()
    validate_prelaunch_provenance_v1(
        runtime_artifacts=artifacts,
        protocol=registry.protocol,
        root_seal_bytes=registry.root_seal_bytes,
        root_seal=registry.root_seal,
        renderer=registry.renderer,
        observation_premise=observation_runtime_premise_v1(),
        renderer_premise=renderer_runtime_premise_v1(),
    )
    assert (len(artifacts["root_seal"]), sha256(artifacts["root_seal"])) == (
        960,
        "sha256:07dd8873f3b5ce4b94ca4b536bb2cbaeafc7f9be42dad2f16b1be495d4fba4e6",
    )

    parent = runtime_root_path_v1().parent
    probe = parent / "slice-c-mode-probe-20260820-b65306bc0c8f4a539d9e74866f1ae84b"
    probe_info = probe.lstat()
    assert (
        probe_info.st_dev,
        probe_info.st_ino,
        probe_info.st_uid,
        probe_info.st_gid,
        stat.S_IMODE(probe_info.st_mode),
        probe_info.st_mtime_ns,
        probe_info.st_ctime_ns,
    ) == (
        16_777_233,
        394_647_425,
        501,
        20,
        0o555,
        1_787_214_595_709_651_075,
        1_787_214_595_709_710_158,
    )

    root_expectations = (
        (parent, 394_647_424, 0o755),
        (parent / "h5ad-tier1-scanpy1115-final-sandbox", 394_647_433, None),
        (runtime_root_path_v1() / "python", 394_647_434, None),
        (runtime_root_path_v1() / "venv", 394_650_585, None),
    )
    modes: list[int] = []
    for path, inode, fixed_mode in root_expectations:
        visible = path.lstat()
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            opened = os.fstat(fd)
        finally:
            os.close(fd)
        assert (opened.st_dev, opened.st_ino, opened.st_uid, opened.st_gid) == (
            16_777_233,
            inode,
            501,
            20,
        )
        assert (visible.st_dev, visible.st_ino) == (opened.st_dev, opened.st_ino)
        mode = stat.S_IMODE(opened.st_mode)
        if fixed_mode is not None:
            assert mode == fixed_mode
        modes.append(mode)
    assert tuple(modes) in {(0o755, 0o755, 0o700, 0o700), (0o755, 0o555, 0o555, 0o555)}


def test_old_target_symlink_and_path_disguise_are_inert() -> None:
    sandbox = runtime_root_path_v1()
    link = sandbox / "venv" / "bin" / "python3.11"
    disguise = sandbox / "python" / ".." / "venv" / "bin" / "python3.11"
    expected_target = (
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime/"
        "h5ad-tier1-scanpy1115-final-sandbox/python/bin/python3.11"
    )
    assert link.is_symlink()
    assert os.readlink(link) == expected_target
    for candidate in (link, disguise):
        with pytest.raises(OSError) as caught:
            os.open(candidate, os.O_RDONLY | os.O_NOFOLLOW)
        assert caught.value.errno == errno.ELOOP

    source_root = Path(__file__).resolve().parents[4] / "src" / "sc_referee_evaluation"
    launcher = (source_root / "audit_ladder" / "slice_c" / "launcher.py").read_text()
    worker = (source_root / "audit_ladder" / "slice_c" / "_worker.py").read_text()
    assert launcher.count('os.execve("python/bin/python3.11"') == 1
    assert "venv/bin/python3.11" not in launcher
    assert worker.count('sys.path.insert(0, "venv/lib/python3.11/site-packages")') == 1
    assert "venv/bin/python3.11" not in worker


@pytest.mark.parametrize(
    "carrier",
    [
        "premise",
        "seal",
        "protocol",
        "root-seal-object",
        "observation",
        "renderer-provenance",
        "renderer-disclosure",
    ],
)
def test_every_stale_premise_carrier_refuses_before_any_worker_or_output(
    static_world1_case: StaticWorld1Case,
    monkeypatch: pytest.MonkeyPatch,
    carrier: str,
) -> None:
    artifacts = read_runtime_artifacts_v1()
    registry = load_registry_bundle_v1()
    old_premise = Path(
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime/"
        "h5ad-tier1-scanpy1115-premise.json"
    ).read_bytes()
    old_seal = Path(
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-design-memos/"
        "audit-report-ladder-slice-c-runtime-root-seal-v1.json"
    ).read_bytes()
    assert (len(old_premise), sha256(old_premise)) == (
        3_625,
        "sha256:9fd7af5c11a073183d61135d1473a785a1628ffbb59ae33f407b7d974be7a4a0",
    )
    assert (len(old_seal), sha256(old_seal)) == (
        1_064,
        "sha256:1cad483b8a71ae3fdf60d020f5f23d871ec82a6c5fe268cc220939fd596e594b",
    )
    if carrier == "premise":
        artifacts["premise"] = old_premise
    elif carrier == "seal":
        artifacts["root_seal"] = old_seal
    elif carrier == "protocol":
        protocol = deepcopy(registry.protocol)
        protocol["artifacts"]["premise"] = {  # type: ignore[index]
            "byte_size": len(old_premise),
            "sha256": sha256(old_premise),
        }
        registry = replace(registry, protocol=protocol)
    elif carrier == "root-seal-object":
        registry = replace(
            registry,
            root_seal_bytes=old_seal,
            root_seal=json.loads(old_seal),
        )
    elif carrier == "observation":
        monkeypatch.setattr(
            transaction_module,
            "observation_runtime_premise_v1",
            lambda: (
                "scanpy-1.11.5-cpython-3.11.15-macos-arm64-v1",
                "sha256:e1acbb22d48f974bcb75d7e2547cbc87910a63b0e63b3ce77687e714c006dc09",
            ),
        )
    elif carrier == "renderer-provenance":
        monkeypatch.setattr(
            transaction_module,
            "renderer_runtime_premise_v1",
            lambda: (
                "scanpy-1.11.5-cpython-3.11.15-macos-arm64-v1",
                "sha256:e1acbb22d48f974bcb75d7e2547cbc87910a63b0e63b3ce77687e714c006dc09",
            ),
        )
    else:
        renderer = deepcopy(registry.renderer)
        renderer["disclosures"][2] = renderer["disclosures"][2].replace(  # type: ignore[index,union-attr]
            "sha256:09fe04ea03c03221bf20c00b5e45cd8f66f00d7476f98da64df5dcde79dc7eeb",
            "sha256:e1acbb22d48f974bcb75d7e2547cbc87910a63b0e63b3ce77687e714c006dc09",
        )
        registry = replace(registry, renderer=renderer)

    monkeypatch.setattr(transaction_module, "read_runtime_artifacts_v1", lambda: artifacts)
    monkeypatch.setattr(transaction_module, "load_registry_bundle_v1", lambda: registry)
    reached = {"request": 0, "worker": 0, "observation": 0, "composition": 0, "render": 0}

    def forbidden(stage: str) -> object:
        reached[stage] += 1
        raise AssertionError(f"stale carrier reached {stage}")

    monkeypatch.setattr(
        transaction_module,
        "build_worker_request_v1",
        lambda **_kwargs: forbidden("request"),
    )
    monkeypatch.setattr(
        transaction_module,
        "run_isolated_worker_v1",
        lambda **_kwargs: forbidden("worker"),
    )
    monkeypatch.setattr(
        transaction_module,
        "build_observations_v1",
        lambda *_args, **_kwargs: forbidden("observation"),
    )
    monkeypatch.setattr(
        transaction_module,
        "compose_world1_v1",
        lambda **_kwargs: forbidden("composition"),
    )
    monkeypatch.setattr(
        transaction_module,
        "render_world1_report_v1",
        lambda **_kwargs: forbidden("render"),
    )
    rendered = transaction_module._render_slice_c_artifacts_v1(
        static_world1_case.context,
        static_world1_case.request,
    )
    assert rendered is None
    assert render_slice_c_report_v1(static_world1_case.context, static_world1_case.request) == b""
    assert reached == {"request": 0, "worker": 0, "observation": 0, "composition": 0, "render": 0}


def test_worker_has_one_bytesio_reader_and_no_network_subprocess_or_scanpy_import() -> None:
    tree = ast.parse(_worker_source(), filename="<slice-c-isolated-worker>")
    imports: set[str] = set()
    bytesio_calls = 0
    reader_calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "io"
                and node.func.attr == "BytesIO"
            ):
                bytesio_calls += 1
            if node.func.attr == "read_h5ad":
                reader_calls += 1
    assert "socket" not in imports
    assert "subprocess" not in imports
    assert "scanpy" not in imports
    assert bytesio_calls == 1
    assert reader_calls == 1


@pytest.mark.parametrize("refusal", list(RefusalFacetV1))
def test_every_worker_refusal_produces_zero_report(
    static_world1_case: StaticWorld1Case,
    monkeypatch: pytest.MonkeyPatch,
    refusal: RefusalFacetV1,
) -> None:
    monkeypatch.setattr(
        "sc_referee_evaluation.audit_ladder.slice_c.transaction.run_isolated_worker_v1",
        lambda **_kwargs: WorkerControllerResultV1(facts=None, refusal=refusal),
    )
    assert render_slice_c_report_v1(static_world1_case.context, static_world1_case.request) == b""


@pytest.mark.parametrize(
    "changes",
    [
        {"conditional_concern": False},
        {"missing_premises": ()},
        {"missing_premises": ("world1.animal-id-is-independent-unit.v1", "second")},
        {"finding_count": 1},
        {"material_question_count": 1},
        {"rule_id": "alternate.rule"},
    ],
)
def test_all_non_m3_composition_states_are_unconstructable(changes: dict[str, object]) -> None:
    values: dict[str, object] = {
        "rule_id": "world1.row-level-independent-samples.slice-c.v1",
        "conditional_concern": True,
        "missing_premises": ("world1.animal-id-is-independent-unit.v1",),
        "finding_count": 0,
        "material_question_count": 0,
    }
    values.update(changes)
    with pytest.raises(SliceCContractError):
        SliceCCompositionResultV1(**values)  # type: ignore[arg-type]


def test_renderer_registry_grade_order_and_template_tampering_refuse(
    static_world1_case: StaticWorld1Case,
) -> None:
    case = static_world1_case
    mutations: list[dict[str, object]] = []
    for key, value in (
        ("header", "attacker header"),
        ("terminal_lf_count", 2),
        ("appendix_indent", "```"),
        ("m3_concern", "- **Finding:** forged"),
        ("m3_coverage", "forged coverage"),
        ("unknown", "metadata"),
    ):
        candidate = dict(case.registry.renderer)
        candidate[key] = value
        mutations.append(candidate)
    reordered = dict(case.registry.renderer)
    reordered["headings"] = list(reversed(reordered["headings"]))  # type: ignore[arg-type]
    mutations.append(reordered)
    grades = dict(case.registry.renderer)
    grades["grade_prefixes"] = {
        **grades["grade_prefixes"],  # type: ignore[dict-item]
        "conditional_concern": "- **Finding:** ",
    }
    mutations.append(grades)
    for mutation in mutations:
        registry = replace(case.registry, renderer=mutation)
        with pytest.raises(SliceCRendererError):
            render_world1_report_v1(
                registry=registry,
                materials=case.materials,
                request_digest=case.request_digest,
                observations=case.observations,
                composition=case.composition,
            )
    assert len(mutations) == 8


def test_production_package_cannot_reach_slice_c() -> None:
    before = set(sys.modules)
    production = importlib.import_module("sc_referee")
    after = set(sys.modules)
    assert not hasattr(production, "render_slice_c_report_v1")
    assert not any(
        name.startswith("sc_referee_evaluation.audit_ladder.slice_c") for name in after - before
    )
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("sc_referee.audit_ladder.slice_c")


def test_no_slice_c_file_exists_in_production_tree() -> None:
    repository = Path(__file__).resolve().parents[5]
    production = repository / "src" / "sc_referee"
    assert not any("slice_c" in path.parts for path in production.rglob("*"))
