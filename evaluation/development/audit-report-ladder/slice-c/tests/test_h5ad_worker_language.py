from __future__ import annotations

import ast
import copy
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import h5py
import numpy as np
import pytest
from conftest import H5AD_PATH, StaticWorld1Case
from sc_referee_evaluation.audit_ladder.slice_c.protocol import build_worker_request_v1
from sc_referee_evaluation.audit_ladder.slice_c.runtime import read_runtime_artifacts_v1


@pytest.fixture(scope="module")
def worker_namespace() -> dict[str, Any]:
    worker_path = (
        Path(__file__).resolve().parents[4]
        / "src"
        / "sc_referee_evaluation"
        / "audit_ladder"
        / "slice_c"
        / "_worker.py"
    )
    tree = ast.parse(worker_path.read_bytes(), filename="<slice-c-worker-test>")
    assert isinstance(tree.body[-1], ast.Try)
    tree.body.pop()
    ast.fix_missing_locations(tree)
    namespace: dict[str, Any] = {"__name__": "slice_c_worker_test"}
    exec(compile(tree, "<slice-c-worker-test>", "exec"), namespace)
    return namespace


class _FakeMatrix:
    dtype = np.dtype("float32")


class _FakeSparse:
    csr_matrix = _FakeMatrix

    @staticmethod
    def issparse(value: object) -> bool:
        return isinstance(value, _FakeMatrix)


class _FakeColumn:
    def __init__(self, values: list[str]) -> None:
        self._values = values

    def tolist(self) -> list[str]:
        return self._values


def _reader(
    *,
    shape: tuple[int, int] = (4_000, 3),
    values: list[str] | None = None,
    obs_names: list[str] | None = None,
    var_names: list[str] | None = None,
    matrix: object | None = None,
) -> object:
    values = values or ["Animal_1"] * 2_000 + ["Animal_2"] * 2_000
    result = SimpleNamespace(
        shape=shape,
        X=_FakeMatrix() if matrix is None else matrix,
        obs={"animal_id": _FakeColumn(values)},
        obs_names=obs_names or [f"Cell_{index:04d}" for index in range(4_000)],
        var_names=var_names or [f"Gene_{index}" for index in range(3)],
    )
    return SimpleNamespace(read_h5ad=lambda _stream: result)


def _validate(namespace: dict[str, Any], raw: bytes, reader: object | None = None) -> object:
    return namespace["validate_h5ad"](
        raw,
        "animal_id",
        reader or _reader(),
        h5py,
        np,
        _FakeSparse,
    )


def _expected_sys_path(namespace: dict[str, Any]) -> list[str]:
    return list(namespace["EXPECTED_SYS_PATH"])


def test_exact_relocated_sys_path_with_sc_referee_prefix_is_accepted(
    worker_namespace: dict[str, Any],
) -> None:
    sandbox = worker_namespace["SANDBOX_PATH"]
    expected = _expected_sys_path(worker_namespace)
    assert "sc-referee" in sandbox
    assert expected == [
        "venv/lib/python3.11/site-packages",
        sandbox + "/python/lib/python311.zip",
        sandbox + "/python/lib/python3.11",
        sandbox + "/python/lib/python3.11/lib-dynload",
    ]
    assert worker_namespace["verify_sys_path"](expected, sandbox) is None


@pytest.mark.parametrize(
    "mutation",
    [
        lambda paths, _sandbox: [
            paths[0],
            "/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext/src",
            *paths[2:],
        ],
        lambda paths, _sandbox: [
            paths[0],
            "/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext/evaluation/src",
            *paths[2:],
        ],
        lambda paths, _sandbox: [*paths, "/unexpected"],
        lambda paths, _sandbox: paths[:-1],
        lambda paths, _sandbox: [paths[0], paths[2], paths[1], paths[3]],
        lambda paths, _sandbox: [paths[0], 1, paths[2], paths[3]],
        lambda paths, sandbox: [
            paths[0],
            paths[1].replace(sandbox, sandbox + "-sibling"),
            *paths[2:],
        ],
        lambda paths, sandbox: [
            paths[0],
            sandbox + "/python/lib/python3.11/../../../../evaluation",
            *paths[2:],
        ],
    ],
    ids=(
        "repository",
        "evaluation",
        "extra",
        "missing",
        "reordered",
        "wrong-entry-type",
        "sibling-runtime",
        "normalization-disguise-wrong-target",
    ),
)
def test_nonexact_sys_path_sequences_refuse_runtime_identity(
    worker_namespace: dict[str, Any],
    mutation: Callable[[list[str], str], object],
) -> None:
    sandbox = worker_namespace["SANDBOX_PATH"]
    changed = mutation(_expected_sys_path(worker_namespace), sandbox)
    with pytest.raises(worker_namespace["Reject"]) as caught:
        worker_namespace["verify_sys_path"](changed, sandbox)
    assert caught.value.facet == "runtime-identity"


def test_wrong_sys_path_container_type_refuses_runtime_identity(
    worker_namespace: dict[str, Any],
) -> None:
    sandbox = worker_namespace["SANDBOX_PATH"]
    with pytest.raises(worker_namespace["Reject"]) as caught:
        worker_namespace["verify_sys_path"](
            tuple(_expected_sys_path(worker_namespace)),
            sandbox,
        )
    assert caught.value.facet == "runtime-identity"


def test_sys_path_normalization_is_fail_closed_on_wrong_resolved_target(
    worker_namespace: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sandbox = worker_namespace["SANDBOX_PATH"]
    expected = _expected_sys_path(worker_namespace)
    original = worker_namespace["os"].path.realpath

    def disguised(value: str) -> str:
        normalized = original(value)
        if normalized == expected[2]:
            return "/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext/evaluation"
        return normalized

    monkeypatch.setattr(worker_namespace["os"].path, "realpath", disguised)
    with pytest.raises(worker_namespace["Reject"]) as caught:
        worker_namespace["verify_sys_path"](expected, sandbox)
    assert caught.value.facet == "runtime-identity"


def test_exact_h5ad_reconstructs_only_four_closed_facts(
    worker_namespace: dict[str, Any],
) -> None:
    facts = _validate(worker_namespace, H5AD_PATH.read_bytes())
    assert set(facts) == {
        "matrix-shape",
        "obs-column-cardinality",
        "obs-column-quoted-values",
        "obs-group-sizes",
    }
    assert facts["matrix-shape"] == {"column_count": 3, "row_count": 4_000}
    assert facts["obs-column-cardinality"] == {
        "column": "animal_id",
        "distinct_count": 2,
        "n_obs": 4_000,
    }
    assert facts["obs-group-sizes"] == {
        "column": "animal_id",
        "groups": [
            {"count": 2_000, "value": "Animal_1"},
            {"count": 2_000, "value": "Animal_2"},
        ],
        "n_obs": 4_000,
    }


def test_worker_independently_reauthenticates_world1_repository_preimages(
    worker_namespace: dict[str, Any],
    static_world1_case: StaticWorld1Case,
) -> None:
    case = static_world1_case
    value, _raw = build_worker_request_v1(
        registry=case.registry,
        materials=case.materials,
        request=case.request,
        runtime_artifacts=read_runtime_artifacts_v1(),
    )
    assert worker_namespace["authenticate_repository"](
        value,
        case.materials.source_bytes,
        case.materials.h5ad_bytes,
    ) == ["analysis.py", "sc_reads.h5ad"]
    assert worker_namespace["authenticate_private"](value) == case.request.to_dict()

    mutations: list[dict[str, Any]] = []
    for apply in (
        lambda item: item["repository"]["file_records"].reverse(),
        lambda item: item["repository"]["file_records"].pop(),
        lambda item: item["repository"]["file_manifest"].update(entry_count=1),
        lambda item: item["repository"].update(snapshot_ref="snapshot:" + "0" * 20),
        lambda item: item["repository"]["selected_materials"]["source"].update(
            material_ref="material:" + "0" * 20
        ),
        lambda item: item["repository"]["selected_materials"]["h5ad"]["asset_identity"].update(
            byte_size=0
        ),
    ):
        item = copy.deepcopy(value)
        apply(item)
        mutations.append(item)
    for mutation in mutations:
        with pytest.raises(worker_namespace["Reject"]) as caught:
            worker_namespace["authenticate_repository"](
                mutation,
                case.materials.source_bytes,
                case.materials.h5ad_bytes,
            )
        assert caught.value.facet == "inventory-identity"


@pytest.mark.parametrize(
    "reader",
    [
        _reader(shape=(4, 3), values=["Animal_1"] * 2 + ["Animal_2"] * 2),
        _reader(matrix=object()),
        _reader(values=["Animal_2"] * 2_000 + ["Animal_1"] * 2_000),
        _reader(obs_names=["forged"] * 4_000),
        _reader(var_names=["forged"] * 3),
    ],
)
def test_alternate_reader_object_and_two_by_two_routes_refuse(
    worker_namespace: dict[str, Any],
    reader: object,
) -> None:
    with pytest.raises(worker_namespace["Reject"]) as caught:
        _validate(worker_namespace, H5AD_PATH.read_bytes(), reader)
    assert caught.value.facet == "h5ad-semantics-not-closed"


Mutator = Callable[[h5py.File], None]


def _set_root_encoding(handle: h5py.File) -> None:
    handle.attrs["encoding-version"] = "9.9.9"


def _remove_x(handle: h5py.File) -> None:
    del handle["X"]


def _make_dense_x(handle: h5py.File) -> None:
    del handle["X"]
    handle.create_dataset("X", data=np.zeros((4_000, 3), dtype=np.float32))


def _make_csc(handle: h5py.File) -> None:
    handle["X"].attrs["encoding-type"] = "csc_matrix"


def _zero_dimension(handle: h5py.File) -> None:
    handle["X"].attrs["shape"] = np.asarray([0, 3], dtype=np.int64)


def _float64_data(handle: h5py.File) -> None:
    values = handle["X/data"][...].astype(np.float64)
    del handle["X/data"]
    handle["X"].create_dataset("data", data=values)


def _nonfinite_data(handle: h5py.File) -> None:
    handle["X/data"][0] = np.nan


def _malformed_indptr(handle: h5py.File) -> None:
    handle["X/indptr"][-1] = 0


def _malformed_indices(handle: h5py.File) -> None:
    handle["X/indices"][0] = 999


def _missing_code(handle: h5py.File) -> None:
    handle["obs/animal_id/codes"][0] = -1


def _unused_category(handle: h5py.File) -> None:
    group = handle["obs/animal_id"]
    attrs = dict(group["categories"].attrs)
    del group["categories"]
    dataset = group.create_dataset(
        "categories",
        data=np.asarray(["Animal_1", "Animal_2", "Animal_3"], dtype=h5py.string_dtype()),
    )
    for key, value in attrs.items():
        dataset.attrs[key] = value


def _numeric_category(handle: h5py.File) -> None:
    group = handle["obs/animal_id"]
    attrs = dict(group["categories"].attrs)
    del group["categories"]
    dataset = group.create_dataset("categories", data=np.asarray([1, 2], dtype=np.int64))
    for key, value in attrs.items():
        dataset.attrs[key] = value


def _bool_codes(handle: h5py.File) -> None:
    group = handle["obs/animal_id"]
    attrs = dict(group["codes"].attrs)
    values = group["codes"][...].astype(np.bool_)
    del group["codes"]
    dataset = group.create_dataset("codes", data=values)
    for key, value in attrs.items():
        dataset.attrs[key] = value


def _column_as_dataset(handle: h5py.File) -> None:
    del handle["obs/animal_id"]
    handle["obs"].create_dataset("animal_id", data=np.zeros(4_000, dtype=np.int8))


def _missing_column(handle: h5py.File) -> None:
    del handle["obs/animal_id"]


def _duplicate_obs_index(handle: h5py.File) -> None:
    handle["obs/cell_id"][1] = handle["obs/cell_id"][0]


def _unsafe_category(handle: h5py.File) -> None:
    handle["obs/animal_id/categories"][0] = "bad\nvalue"


def _nonnfc_category(handle: h5py.File) -> None:
    handle["obs/animal_id/categories"][0] = "e\N{COMBINING ACUTE ACCENT}"


def _bidi_category(handle: h5py.File) -> None:
    handle["obs/animal_id/categories"][0] = "x\N{RIGHT-TO-LEFT OVERRIDE}y"


def _oversized_category(handle: h5py.File) -> None:
    handle["obs/animal_id/categories"][0] = "x" * 1_025


def _raw_group(handle: h5py.File) -> None:
    handle.create_group("raw")


def _layer(handle: h5py.File) -> None:
    handle["layers"].create_dataset("forged", data=np.asarray([1], dtype=np.int8))


def _auxiliary(handle: h5py.File) -> None:
    handle["obsm"].create_dataset("forged", data=np.asarray([1], dtype=np.int8))


def _compressed(handle: h5py.File) -> None:
    handle["uns"].create_dataset(
        "compressed",
        data=np.asarray([1], dtype=np.int8),
        compression="gzip",
    )


def _soft_link(handle: h5py.File) -> None:
    handle["uns/soft"] = h5py.SoftLink("/X/data")


def _external_link(handle: h5py.File) -> None:
    handle["uns/external"] = h5py.ExternalLink("other.h5", "/X")


def _virtual_dataset(handle: h5py.File) -> None:
    layout = h5py.VirtualLayout(shape=(1,), dtype=np.int32)
    source = h5py.VirtualSource(str(handle.filename), "/X/indices", shape=(12_000,))
    layout[:] = source[:1]
    handle.create_virtual_dataset("uns/virtual", layout)


def _wrong_column_order(handle: h5py.File) -> None:
    handle["obs"].attrs["column-order"] = np.asarray([], dtype=np.float64)


def _missing_index(handle: h5py.File) -> None:
    del handle["var/gene_id"]


@pytest.mark.parametrize(
    "mutator",
    [
        _set_root_encoding,
        _remove_x,
        _make_dense_x,
        _make_csc,
        _zero_dimension,
        _float64_data,
        _nonfinite_data,
        _malformed_indptr,
        _malformed_indices,
        _missing_code,
        _unused_category,
        _numeric_category,
        _bool_codes,
        _column_as_dataset,
        _missing_column,
        _duplicate_obs_index,
        _unsafe_category,
        _nonnfc_category,
        _bidi_category,
        _oversized_category,
        _raw_group,
        _layer,
        _auxiliary,
        _compressed,
        _soft_link,
        _external_link,
        _virtual_dataset,
        _wrong_column_order,
        _missing_index,
    ],
    ids=lambda item: item.__name__.removeprefix("_"),
)
def test_default_deny_h5ad_sibling_families(
    worker_namespace: dict[str, Any],
    tmp_path: Path,
    mutator: Mutator,
) -> None:
    target = tmp_path / "sibling.h5ad"
    target.write_bytes(H5AD_PATH.read_bytes())
    with h5py.File(target, "r+") as handle:
        mutator(handle)
    with pytest.raises(worker_namespace["Reject"]) as caught:
        _validate(worker_namespace, target.read_bytes())
    assert caught.value.facet == "h5ad-semantics-not-closed"


def test_h5ad_payload_byte_forgery_never_returns_facts(worker_namespace: dict[str, Any]) -> None:
    raw = bytearray(H5AD_PATH.read_bytes())
    raw[0] ^= 1
    with pytest.raises(worker_namespace["Reject"]):
        _validate(worker_namespace, bytes(raw))
