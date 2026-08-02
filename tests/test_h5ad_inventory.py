from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import pytest

from sc_referee.calculation_checks.core import (
    CalculationAdapterManifest,
    CalculationCheckManifest,
    CalculationCheckModule,
    CalculationCheckRegistry,
    CalculationContext,
    CalculationObservation,
    NamedOperand,
    ObservationReceipt,
)
from sc_referee.controller import replay, run_audit
from sc_referee.h5ad_inventory import (
    MAX_H5AD_LOGICAL_READ_BYTES,
    MAX_H5AD_READ_CHUNK_BYTES,
    inspect_h5ad_inventory,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.snapshot.repository import capture_repository

_TEST_DIGEST = "sha256:" + "1" * 64


class _MaterialInputEchoAdapter:
    manifest = CalculationAdapterManifest(
        adapter_id="calculation-adapter:test-material-input-echo-v1",
        adapter_version="1.0.0",
        implementation_digest=_TEST_DIGEST,
        recognition_grammar_digest=_TEST_DIGEST,
    )

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        material_inputs = getattr(context, "material_inputs", ())
        if not material_inputs:
            return None
        return CalculationObservation(
            applicability="applicable",
            comparison_outcome="conformant",
            target_ref=context.selected_surface_ref,
            input_refs=(
                context.selected_artifact_ref,
                *(item.artifact_ref for item in material_inputs),
            ),
            source_refs=tuple(item.source_ref for item in material_inputs),
            operands=(
                NamedOperand(
                    "material_paths",
                    "string_array",
                    [item.path for item in material_inputs],
                ),
            ),
            receipts=(
                ObservationReceipt(
                    "completeness",
                    "selected_material_inputs_frozen",
                    "passed",
                    tuple(item.source_ref for item in material_inputs),
                    "The explicitly selected material inputs were frozen with exact digests.",
                ),
            ),
            lineage_status="complete",
            limitations=("This test adapter assigns no scientific meaning to the inputs.",),
        )


def _material_echo_registry() -> CalculationCheckRegistry:
    check = CalculationCheckManifest(
        check_id="calculation-check:test-material-input-echo-v1",
        check_version="1.0.0",
        implementation_digest=_TEST_DIGEST,
        comparison_relation="selected_material_input_echo",
        output_ceiling="disclosure_only",
        permitted_wording="The selected material inputs were made available to the adapter.",
    )
    return CalculationCheckRegistry(
        (CalculationCheckModule(check, (_MaterialInputEchoAdapter(),)),),
        profile_id="test_material_input_context_v1",
    )


def _write_dense_h5ad(
    path: Path,
    *,
    duplicate_features: bool = False,
    duplicate_observations: bool = False,
) -> None:
    string_dtype = h5py.string_dtype(encoding="utf-8")
    with h5py.File(path, "w") as handle:
        handle.attrs["encoding-type"] = "anndata"
        handle.attrs["encoding-version"] = "0.1.0"
        matrix = handle.create_dataset(
            "X",
            data=np.asarray([[1, 0], [2, 4], [0, 3]], dtype=np.int64),
        )
        matrix.attrs["encoding-type"] = "array"
        matrix.attrs["encoding-version"] = "0.2.0"

        obs = handle.create_group("obs")
        obs.attrs["encoding-type"] = "dataframe"
        obs.attrs["encoding-version"] = "0.2.0"
        obs.attrs["_index"] = "sample_id"
        obs.attrs["column-order"] = np.asarray(["organ", "patient"], dtype=object)
        sample_id = obs.create_dataset(
            "sample_id",
            data=np.asarray(
                ["s1", "s1" if duplicate_observations else "s2", "s3"],
                dtype=object,
            ),
            dtype=string_dtype,
        )
        sample_id.attrs["encoding-type"] = "string-array"
        sample_id.attrs["encoding-version"] = "0.2.0"
        patient = obs.create_dataset(
            "patient",
            data=np.asarray(["p1", "p2", "p3"], dtype=object),
            dtype=string_dtype,
        )
        patient.attrs["encoding-type"] = "string-array"
        patient.attrs["encoding-version"] = "0.2.0"
        organ = obs.create_group("organ")
        organ.attrs["encoding-type"] = "categorical"
        organ.attrs["encoding-version"] = "0.2.0"
        organ.attrs["ordered"] = False
        categories = organ.create_dataset(
            "categories",
            data=np.asarray(["brain", "blood"], dtype=object),
            dtype=string_dtype,
        )
        categories.attrs["encoding-type"] = "string-array"
        categories.attrs["encoding-version"] = "0.2.0"
        codes = organ.create_dataset("codes", data=np.asarray([0, 0, 1], dtype=np.int8))
        codes.attrs["encoding-type"] = "array"
        codes.attrs["encoding-version"] = "0.2.0"

        var = handle.create_group("var")
        var.attrs["encoding-type"] = "dataframe"
        var.attrs["encoding-version"] = "0.2.0"
        var.attrs["_index"] = "_index"
        var.attrs["column-order"] = np.asarray([], dtype=np.float64)
        features = ["gene-a", "gene-a" if duplicate_features else "gene-b"]
        index = var.create_dataset(
            "_index",
            data=np.asarray(features, dtype=object),
            dtype=string_dtype,
        )
        index.attrs["encoding-type"] = "string-array"
        index.attrs["encoding-version"] = "0.2.0"


def _write_sparse_h5ad(
    path: Path,
    *,
    storage: str = "csr_matrix",
    shape: tuple[int, int] = (3, 2),
    data: np.ndarray | None = None,
    indices: np.ndarray | None = None,
    indptr: np.ndarray | None = None,
    large_repeated_obs: bool = False,
) -> None:
    if storage == "csr_matrix":
        default_indices = np.asarray([0, 0, 1, 1], dtype=np.int64)
        default_indptr = np.asarray([0, 1, 3, 4], dtype=np.int64)
    else:
        default_indices = np.asarray([0, 1, 1, 2], dtype=np.int64)
        default_indptr = np.asarray([0, 2, 4], dtype=np.int64)
    values = np.asarray([1, 2, 4, 3], dtype=np.int64) if data is None else data
    column_or_row_indices = default_indices if indices is None else indices
    pointers = default_indptr if indptr is None else indptr
    string_dtype = h5py.string_dtype(encoding="utf-8")
    with h5py.File(path, "w") as handle:
        handle.attrs["encoding-type"] = "anndata"
        handle.attrs["encoding-version"] = "0.1.0"
        matrix = handle.create_group("X")
        matrix.attrs["encoding-type"] = storage
        matrix.attrs["encoding-version"] = "0.1.0"
        matrix.attrs["shape"] = np.asarray(shape, dtype=np.int64)
        matrix.create_dataset("data", data=values, compression="gzip")
        matrix.create_dataset("indices", data=column_or_row_indices, compression="gzip")
        matrix.create_dataset("indptr", data=pointers, compression="gzip")

        obs = handle.create_group("obs")
        obs.attrs["encoding-type"] = "dataframe"
        obs.attrs["encoding-version"] = "0.2.0"
        obs.attrs["_index"] = "sample_id"
        obs.attrs["column-order"] = np.asarray([], dtype=np.float64)
        if large_repeated_obs:
            sample_id = obs.create_group("sample_id")
            sample_id.attrs["encoding-type"] = "categorical"
            sample_id.attrs["encoding-version"] = "0.2.0"
            sample_id.attrs["ordered"] = False
            sample_id.create_dataset(
                "categories",
                data=np.asarray(["repeated"], dtype=object),
                dtype=string_dtype,
            )
            sample_id.create_dataset(
                "codes",
                shape=(shape[0],),
                dtype=np.int8,
                chunks=(min(shape[0], 65_536),),
                compression="gzip",
                fillvalue=0,
            )
        else:
            sample_id = obs.create_dataset(
                "sample_id",
                data=np.asarray([f"s{index + 1}" for index in range(shape[0])], dtype=object),
                dtype=string_dtype,
            )
            sample_id.attrs["encoding-type"] = "string-array"
            sample_id.attrs["encoding-version"] = "0.2.0"

        var = handle.create_group("var")
        var.attrs["encoding-type"] = "dataframe"
        var.attrs["encoding-version"] = "0.2.0"
        var.attrs["_index"] = "_index"
        var.attrs["column-order"] = np.asarray([], dtype=np.float64)
        feature_count = shape[1]
        features = var.create_dataset(
            "_index",
            data=np.asarray([f"gene-{index + 1}" for index in range(feature_count)], dtype=object),
            dtype=string_dtype,
        )
        features.attrs["encoding-type"] = "string-array"
        features.attrs["encoding-version"] = "0.2.0"


def test_selected_dense_h5ad_is_inventory_only_and_structurally_bounded(
    schema_root: Path, tmp_path: Path
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _write_dense_h5ad(source / "counts.h5ad")
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-08-01T01:00:00Z",
        material_full_digest_paths=("counts.h5ad",),
    )

    output = inspect_h5ad_inventory(snapshot, [], "run:test", "2026-08-01T01:00:00Z")

    assert output.inspected_paths == ("counts.h5ad",)
    assert output.unavailable_paths == ()
    assert output.unsupported_paths == ()
    assert len(output.artifacts) == len(output.asset_identities) == len(output.data_assets) == 1
    structure = output.structures[0]
    assert structure.path == "counts.h5ad"
    assert structure.matrix_path == "X"
    assert structure.shape == (3, 2)
    assert structure.matrix_storage == "dense"
    assert structure.matrix_dtype == "int64"
    assert structure.matrix_nonnegative is True
    assert structure.matrix_integer_valued is True
    assert structure.obs_fields == ("organ", "patient", "sample_id")
    assert structure.obs_index == "sample_id"
    assert structure.var_index == "_index"
    assert structure.feature_index_unique is True
    assert structure.matrix_sum == 10

    data_asset = output.data_assets[0]
    assert data_asset["format"] == "matrix"
    assert data_asset["role"] == "unknown"
    assert data_asset["structure_status"] == "complete"
    assert {item["observed_name"] for item in output.variables} == {
        "obs/organ",
        "obs/patient",
        "obs/sample_id",
        "var/_index",
    }
    storage_by_name = {item["observed_name"]: item["storage_type"] for item in output.variables}
    assert storage_by_name["obs/organ"] == "categorical"
    assert storage_by_name["obs/patient"] == "string"
    assert all(item["scientific_meaning_status"] == "unresolved" for item in output.variables)

    validator = LocalSchemaRegistry(schema_root)
    for record in [
        *output.artifacts,
        *output.asset_identities,
        *output.data_assets,
        *output.variables,
    ]:
        validator.validate(record)


def test_selected_csr_and_csc_h5ad_are_scanned_without_dense_materialization(
    tmp_path: Path,
) -> None:
    for storage, expected in (("csr_matrix", "csr"), ("csc_matrix", "csc")):
        source = tmp_path / storage
        source.mkdir()
        _write_sparse_h5ad(source / "counts.h5ad", storage=storage)
        snapshot = capture_repository(
            source,
            tmp_path / f"snapshot-{storage}",
            f"run:{expected}",
            captured_at="2026-08-02T21:00:00Z",
            material_full_digest_paths=("counts.h5ad",),
        )

        output = inspect_h5ad_inventory(
            snapshot,
            [],
            f"run:{expected}",
            "2026-08-02T21:00:00Z",
        )

        assert output.inspected_paths == ("counts.h5ad",)
        structure = output.structures[0]
        assert structure.matrix_storage == expected
        assert structure.shape == (3, 2)
        assert structure.matrix_stored_values == 4
        assert structure.matrix_sum == 10
        assert structure.matrix_nonnegative is True
        assert structure.observation_index_unique is True
        assert structure.feature_index_unique is True
        receipt = output.read_receipts[0]
        assert receipt.status == "inspected"
        assert 0 < receipt.logical_bytes_read <= receipt.logical_byte_ceiling
        assert receipt.read_chunks >= 5
        assert receipt.chunk_byte_ceiling == MAX_H5AD_READ_CHUNK_BYTES


def test_million_scale_sparse_shape_stays_chunked_and_records_duplicate_cells(
    tmp_path: Path,
) -> None:
    source = tmp_path / "million-scale"
    source.mkdir()
    n_obs = 1_000_001
    pointers = np.zeros(n_obs + 1, dtype=np.int64)
    pointers[-1] = 2
    _write_sparse_h5ad(
        source / "counts.h5ad",
        shape=(n_obs, 2),
        data=np.asarray([1, 2], dtype=np.int64),
        indices=np.asarray([0, 1], dtype=np.int64),
        indptr=pointers,
        large_repeated_obs=True,
    )
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot-million-scale",
        "run:million-scale",
        captured_at="2026-08-02T21:00:00Z",
        material_full_digest_paths=("counts.h5ad",),
    )

    output = inspect_h5ad_inventory(
        snapshot,
        [],
        "run:million-scale",
        "2026-08-02T21:00:00Z",
    )

    structure = output.structures[0]
    assert structure.shape == (n_obs, 2)
    assert structure.matrix_storage == "csr"
    assert structure.matrix_stored_values == 2
    assert structure.matrix_sum == 3
    assert structure.observation_index_unique is False
    assert output.data_assets[0]["structure_status"] == "partial"
    assert any(
        "observation index is not unique" in item for item in output.data_assets[0]["limitations"]
    )
    receipt = output.read_receipts[0]
    assert receipt.read_chunks > 10
    assert receipt.logical_bytes_read < MAX_H5AD_LOGICAL_READ_BYTES


def test_sparse_pointer_chunk_boundary_mutation_is_localized(tmp_path: Path) -> None:
    source = tmp_path / "boundary"
    source.mkdir()
    n_obs = 131_073
    pointers = np.arange(n_obs + 1, dtype=np.int64)
    pointers[131_072] = 5
    _write_sparse_h5ad(
        source / "counts.h5ad",
        shape=(n_obs, 1),
        data=np.ones(n_obs, dtype=np.int64),
        indices=np.zeros(n_obs, dtype=np.int64),
        indptr=pointers,
        large_repeated_obs=True,
    )
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot-boundary",
        "run:boundary",
        captured_at="2026-08-02T21:00:00Z",
        material_full_digest_paths=("counts.h5ad",),
    )

    output = inspect_h5ad_inventory(
        snapshot,
        [],
        "run:boundary",
        "2026-08-02T21:00:00Z",
    )

    assert output.inspected_paths == ()
    assert output.unsupported_paths == ("counts.h5ad",)
    assert output.structures == ()
    assert output.read_receipts[0].status == "unsupported"
    assert output.read_receipts[0].read_chunks >= 4


def test_sparse_compression_cannot_bypass_logical_read_budget(tmp_path: Path) -> None:
    source = tmp_path / "compression-budget"
    source.mkdir()
    with h5py.File(source / "counts.h5ad", "w") as handle:
        handle.attrs["encoding-type"] = "anndata"
        matrix = handle.create_group("X")
        matrix.attrs["encoding-type"] = "csr_matrix"
        matrix.attrs["shape"] = np.asarray([1, 2_000_000], dtype=np.int64)
        matrix.create_dataset(
            "data",
            shape=(5_000_000,),
            dtype=np.int64,
            chunks=(65_536,),
            compression="gzip",
            fillvalue=0,
        )
        matrix.create_dataset(
            "indices",
            shape=(5_000_000,),
            dtype=np.int64,
            chunks=(65_536,),
            compression="gzip",
            fillvalue=0,
        )
        matrix.create_dataset("indptr", data=np.asarray([0, 5_000_000], dtype=np.int64))
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot-compression-budget",
        "run:compression-budget",
        captured_at="2026-08-02T21:00:00Z",
        material_full_digest_paths=("counts.h5ad",),
    )

    output = inspect_h5ad_inventory(
        snapshot,
        [],
        "run:compression-budget",
        "2026-08-02T21:00:00Z",
    )

    assert output.unsupported_paths == ("counts.h5ad",)
    receipt = output.read_receipts[0]
    assert receipt.raw_file_bytes < 1_000_000
    assert receipt.logical_byte_ceiling == MAX_H5AD_LOGICAL_READ_BYTES
    assert receipt.logical_bytes_read == 0
    assert receipt.termination_reason == "unsupported_layout_or_budget"


def test_h5ad_reader_propagates_injected_cancellation_between_chunks(tmp_path: Path) -> None:
    source = tmp_path / "cancel"
    source.mkdir()
    _write_sparse_h5ad(source / "counts.h5ad")
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot-cancel",
        "run:cancel",
        captured_at="2026-08-02T21:00:00Z",
        material_full_digest_paths=("counts.h5ad",),
    )
    calls = 0

    class _Cancelled(RuntimeError):
        pass

    def checkpoint() -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise _Cancelled("stop")

    with pytest.raises(_Cancelled, match="stop"):
        inspect_h5ad_inventory(
            snapshot,
            [],
            "run:cancel",
            "2026-08-02T21:00:00Z",
            read_checkpoint=checkpoint,
        )
    assert calls == 2


def test_unselected_or_unsupported_h5ad_never_gets_semantic_structure(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _write_dense_h5ad(source / "unselected.h5ad")
    with h5py.File(source / "sparse.h5ad", "w") as handle:
        handle.attrs["encoding-type"] = "anndata"
        handle.create_group("X").attrs["encoding-type"] = "csr_matrix"
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-08-01T01:00:00Z",
        material_full_digest_paths=("sparse.h5ad",),
    )

    output = inspect_h5ad_inventory(snapshot, [], "run:test", "2026-08-01T01:00:00Z")

    assert output.inspected_paths == ()
    assert output.unsupported_paths == ("sparse.h5ad",)
    assert output.unavailable_paths == ()
    assert output.structures == ()
    assert output.artifacts == []
    assert output.data_assets == []
    assert "unselected.h5ad" not in repr(output)


def test_duplicate_feature_index_is_localized_as_partial_structure(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _write_dense_h5ad(source / "counts.h5ad", duplicate_features=True)
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-08-01T01:00:00Z",
        material_full_digest_paths=("counts.h5ad",),
    )

    output = inspect_h5ad_inventory(snapshot, [], "run:test", "2026-08-01T01:00:00Z")

    assert output.inspected_paths == ("counts.h5ad",)
    assert output.structures[0].feature_index_unique is False
    assert output.data_assets[0]["structure_status"] == "partial"
    assert any(
        "feature index is not unique" in item for item in output.data_assets[0]["limitations"]
    )


def test_audit_integrates_only_explicit_h5ad_material_input(
    schema_root: Path, tmp_path: Path
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "report.md").write_text("# Results\n\nNo scientific claim.\n", encoding="utf-8")
    _write_dense_h5ad(source / "counts.h5ad")

    selected_output = tmp_path / "selected"
    selected = run_audit(
        source,
        selected_output,
        schema_root,
        report="report.md",
        material_inputs=("counts.h5ad",),
    )
    unselected = run_audit(
        source,
        tmp_path / "unselected",
        schema_root,
        report="report.md",
    )

    selected_h5ad = [item for item in selected["data_assets"] if item["path"] == "counts.h5ad"]
    assert len(selected_h5ad) == 1
    assert selected_h5ad[0]["format"] == "matrix"
    assert all(item.get("path") != "counts.h5ad" for item in unselected["data_assets"])
    assert any(
        "H5AD" in gap and "scientific meaning" in gap
        for gap in selected["coverage_records"][0]["known_gaps"]
    )
    receipts = selected["repository_snapshots"][0]["extensions"]["x-h5ad-read-receipts"]
    assert len(receipts) == 1
    assert receipts[0]["path"] == "counts.h5ad"
    assert receipts[0]["status"] == "inspected"
    (source / "counts.h5ad").write_bytes(b"changed after semantic lock")
    replayed = replay(
        selected_output / "semantic.lock.json",
        tmp_path / "selected-replay",
        schema_root,
    )
    assert replayed["repository_snapshots"][0]["extensions"]["x-h5ad-read-receipts"] == receipts
    assert selected["findings"] == unselected["findings"] == []


def test_calculation_context_exposes_only_exact_selected_material_inputs(
    schema_root: Path, tmp_path: Path
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "report.md").write_text("# Results\n\nNo scientific claim.\n", encoding="utf-8")
    (source / "results.csv").write_text("gene,padj\ngene-a,0.01\n", encoding="utf-8")
    (source / "unselected.csv").write_text("gene,padj\ngene-b,0.02\n", encoding="utf-8")
    _write_dense_h5ad(source / "counts.h5ad")

    bundle = run_audit(
        source,
        tmp_path / "audit",
        schema_root,
        report="report.md",
        material_inputs=("counts.h5ad", "results.csv"),
        calculation_check_registry=_material_echo_registry(),
    )

    observation = bundle["deterministic_check_observations"][0]
    paths = next(
        item["value"] for item in observation["operands"] if item["name"] == "material_paths"
    )
    assert paths == ["counts.h5ad", "results.csv"]
    assert "unselected.csv" not in paths
    assert observation["production_finding_permitted"] is False
    assert bundle["findings"] == []
