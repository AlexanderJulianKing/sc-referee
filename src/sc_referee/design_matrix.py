"""Formula-free construction of exact ordinary fixed-effect matrices."""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd


class DesignMatrixError(ValueError):
    """The structured fixed-effect request cannot be realized exactly."""


def _canonical_scalar(value: object) -> bytes:
    if isinstance(value, np.generic):
        value = value.item()
    if value is None:
        return b"n"
    if isinstance(value, bool):
        return b"b1" if value else b"b0"
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return b"s" + struct.pack("<Q", len(encoded)) + encoded
    if isinstance(value, bytes):
        return b"y" + struct.pack("<Q", len(value)) + value
    if isinstance(value, int):
        encoded = str(value).encode("ascii")
        return b"i" + struct.pack("<Q", len(encoded)) + encoded
    if isinstance(value, float):
        if not np.isfinite(value):
            raise DesignMatrixError("identity labels and category levels must be finite")
        return b"f" + struct.pack("<d", value)
    if isinstance(value, tuple):
        parts = [_canonical_scalar(item) for item in value]
        return b"t" + struct.pack("<Q", len(parts)) + b"".join(
            struct.pack("<Q", len(part)) + part for part in parts
        )
    raise DesignMatrixError(
        f"unsupported identity label or categorical level type: {type(value).__name__}"
    )


def _row_digest(labels: tuple[object, ...]) -> str:
    digest = hashlib.sha256()
    digest.update(b"sc-referee-row-identity-v1\0")
    digest.update(struct.pack("<Q", len(labels)))
    for label in labels:
        encoded = _canonical_scalar(label)
        digest.update(struct.pack("<Q", len(encoded)))
        digest.update(encoded)
    return f"sha256:{digest.hexdigest()}"


def _level_display(level: object) -> str:
    if isinstance(level, np.generic):
        level = level.item()
    if isinstance(level, str):
        return level
    if isinstance(level, (int, float)) and not isinstance(level, bool):
        return str(level)
    raise DesignMatrixError(
        f"unsupported categorical level type for canonical column ID: {type(level).__name__}"
    )


@dataclass(frozen=True)
class RowIdentity:
    index_labels: tuple[object, ...]
    digest: str


@dataclass(frozen=True)
class FixedEffectMatrix:
    matrix: np.ndarray
    column_ids: tuple[str, ...]
    source_column_indices: tuple[tuple[str, tuple[int, ...]], ...]
    categorical_level_ledger: tuple[tuple[str, tuple[object, ...]], ...]
    row_identity: RowIdentity

    @property
    def source_slices(self) -> dict[str, tuple[int, ...]]:
        return dict(self.source_column_indices)

    def reference_to_test_contrast(
        self, source_column: str, reference_level: object, test_level: object
    ) -> np.ndarray:
        level_ledgers = dict(self.categorical_level_ledger)
        if source_column not in level_ledgers:
            raise DesignMatrixError(
                f"contrast source {source_column!r} is not a categorical source"
            )
        levels = level_ledgers[source_column]
        keys = tuple(_canonical_scalar(level) for level in levels)
        reference_key = _canonical_scalar(reference_level)
        test_key = _canonical_scalar(test_level)
        if reference_key not in keys or test_key not in keys:
            raise DesignMatrixError("contrast reference and test levels must be in the level ledger")
        if reference_key == test_key:
            raise DesignMatrixError("contrast reference and test levels must differ")

        indices = self.source_slices[source_column]
        vector = np.zeros(len(self.column_ids), dtype=np.float64)
        reference_position = keys.index(reference_key)
        test_position = keys.index(test_key)
        if reference_position > 0:
            vector[indices[reference_position - 1]] -= 1.0
        if test_position > 0:
            vector[indices[test_position - 1]] += 1.0
        vector.flags.writeable = False
        return vector


def build_fixed_effect_matrix(
    rows: pd.DataFrame,
    *,
    source_columns: tuple[str, ...],
    column_kinds: Mapping[str, str],
    categorical_levels: Mapping[str, tuple[object, ...]],
    intercept: bool,
) -> FixedEffectMatrix:
    """Build deterministic continuous/treatment-coded fixed effects without formulas."""
    if not isinstance(rows, pd.DataFrame):
        raise DesignMatrixError("rows must be a pandas DataFrame")
    sources = tuple(source_columns)
    if len(set(sources)) != len(sources):
        raise DesignMatrixError("duplicate source column labels are not allowed")
    if not all(isinstance(source, str) and source for source in sources):
        raise DesignMatrixError("source columns must be non-empty exact string labels")
    if not rows.columns.is_unique:
        raise DesignMatrixError("dataframe column labels must be unique")
    missing_columns = [source for source in sources if source not in rows.columns]
    if missing_columns:
        raise DesignMatrixError(f"missing source columns: {missing_columns!r}")

    kinds = dict(column_kinds)
    missing_kinds = [source for source in sources if source not in kinds]
    extra_kinds = [source for source in kinds if source not in sources]
    if missing_kinds:
        raise DesignMatrixError(f"missing column_kinds entries: {missing_kinds!r}")
    if extra_kinds:
        raise DesignMatrixError(f"extra column_kinds entries: {extra_kinds!r}")
    invalid_kinds = [source for source, kind in kinds.items() if kind not in {"continuous", "categorical"}]
    if invalid_kinds:
        raise DesignMatrixError(f"invalid column_kinds entries: {invalid_kinds!r}")

    requested_levels = dict(categorical_levels)
    categorical_sources = {source for source in sources if kinds[source] == "categorical"}
    missing_level_ledgers = [source for source in sources if source in categorical_sources and source not in requested_levels]
    extra_level_ledgers = [source for source in requested_levels if source not in categorical_sources]
    if missing_level_ledgers:
        raise DesignMatrixError(f"missing categorical level ledgers: {missing_level_ledgers!r}")
    if extra_level_ledgers:
        raise DesignMatrixError(f"extra categorical level ledgers: {extra_level_ledgers!r}")

    arrays: list[np.ndarray] = []
    column_ids: list[str] = []
    if intercept:
        arrays.append(np.ones(len(rows), dtype=np.float64))
        column_ids.append("intercept")
    source_indices: list[tuple[str, tuple[int, ...]]] = []
    categorical_ledger: list[tuple[str, tuple[object, ...]]] = []

    for source in sources:
        series = rows[source]
        raw = series.to_numpy()
        if pd.api.types.is_bool_dtype(series.dtype) or any(
            isinstance(value, (bool, np.bool_)) for value in raw
        ):
            raise DesignMatrixError(f"boolean source {source!r} is unsupported")
        if series.isna().any():
            raise DesignMatrixError(f"missing values in source {source!r}")

        start = len(column_ids)
        if kinds[source] == "continuous":
            if not pd.api.types.is_numeric_dtype(series.dtype):
                raise DesignMatrixError(f"continuous source {source!r} must be numeric")
            values = np.asarray(raw, dtype=np.float64)
            if not np.isfinite(values).all():
                raise DesignMatrixError(f"non-finite values in source {source!r}")
            arrays.append(values)
            column_ids.append(source)
        else:
            levels = tuple(requested_levels[source])
            if not levels:
                raise DesignMatrixError(f"categorical source {source!r} has no requested levels")
            level_keys = tuple(_canonical_scalar(level) for level in levels)
            if len(set(level_keys)) != len(level_keys):
                raise DesignMatrixError(f"categorical source {source!r} has duplicate levels")
            observed_keys = tuple(_canonical_scalar(value) for value in raw)
            unlisted = set(observed_keys) - set(level_keys)
            unused = set(level_keys) - set(observed_keys)
            if unlisted:
                raise DesignMatrixError(f"present-but-unlisted category in source {source!r}")
            if unused:
                raise DesignMatrixError(f"unused requested level in source {source!r}")
            for level, level_key in zip(levels[1:], level_keys[1:]):
                arrays.append(
                    np.fromiter(
                        (float(value_key == level_key) for value_key in observed_keys),
                        dtype=np.float64,
                        count=len(rows),
                    )
                )
                column_ids.append(f"{source}[level={_level_display(level)}]")
            categorical_ledger.append((source, levels))
        source_indices.append((source, tuple(range(start, len(column_ids)))))

    if len(set(column_ids)) != len(column_ids):
        raise DesignMatrixError("canonical design column IDs are not unique")
    matrix = (
        np.column_stack(arrays).astype(np.float64, order="C", copy=False)
        if arrays
        else np.empty((len(rows), 0), dtype=np.float64)
    )
    matrix = np.ascontiguousarray(matrix, dtype=np.float64)
    matrix.flags.writeable = False
    index_labels = tuple(rows.index.tolist())
    row_identity = RowIdentity(
        index_labels=index_labels,
        digest=_row_digest(index_labels),
    )
    return FixedEffectMatrix(
        matrix=matrix,
        column_ids=tuple(column_ids),
        source_column_indices=tuple(source_indices),
        categorical_level_ledger=tuple(categorical_ledger),
        row_identity=row_identity,
    )
