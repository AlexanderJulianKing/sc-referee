"""Immutable development-only pandas runtime premise for Growth 14.

This module is a literal proof premise.  It does not import pandas, inspect an
environment, install a package, or confer production/qualification authority.
The liveness probe for these literals belongs to the development test gate.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from sc_referee.core.ids import semantic_digest


@dataclass(frozen=True, order=True)
class PandasDevelopmentRuntimePremise:
    premise_id: str
    python_version: str
    pandas_version: str
    numpy_version: str
    scipy_version: str
    python_dateutil_version: str
    invocation_boundary: str
    pandas_metadata_sha256: str
    pandas_record_sha256: str
    pandas_wheel_sha256: str
    record_rows: int
    hashed_regular_files: int
    unhashed_rows: int
    hashed_regular_bytes: int
    missing_hashed_files: int
    digest_mismatches: int


PANDAS_DEVELOPMENT_RUNTIME_PREMISE = PandasDevelopmentRuntimePremise(
    premise_id="pandas-development-runtime-3.0.5-v1",
    python_version="3.11.15",
    pandas_version="3.0.5",
    numpy_version="2.2.6",
    scipy_version="1.14.0",
    python_dateutil_version="2.9.0.post0",
    invocation_boundary="declared-isolated-development-interpreter:-I",
    pandas_metadata_sha256=(
        "sha256:119bd5541f4e2d413f440c82ad75b7b0457602f368b4b02efb467297c3c4a5b1"
    ),
    pandas_record_sha256=(
        "sha256:d72bb52b0ccbd365b81ac3c28aeb237850b5fd01c1d99c567b2a7dc02b73789d"
    ),
    pandas_wheel_sha256=("sha256:1bf75f748e15745144a15e28d77bf06deda9df34f8e806ee9265f391f62ec8f2"),
    record_rows=2943,
    hashed_regular_files=1521,
    unhashed_rows=1422,
    hashed_regular_bytes=38_500_138,
    missing_hashed_files=0,
    digest_mismatches=0,
)

PANDAS_DEVELOPMENT_RUNTIME_PREMISE_DIGEST = semantic_digest(
    asdict(PANDAS_DEVELOPMENT_RUNTIME_PREMISE)
)

# pandas 3.0.5's complete default missing-token vocabulary.  Empty cells are
# also rejected structurally, but remain in this exact premise set.
PANDAS_3_0_5_DEFAULT_MISSING_TOKENS = frozenset(
    {
        "",
        "#N/A",
        "#N/A N/A",
        "#NA",
        "-1.#IND",
        "-1.#QNAN",
        "-NaN",
        "-nan",
        "1.#IND",
        "1.#QNAN",
        "<NA>",
        "N/A",
        "NA",
        "NULL",
        "NaN",
        "None",
        "n/a",
        "nan",
        "null",
    }
)

PANDAS_GROUP_LITERAL_PATTERN = r"[A-Za-z][A-Za-z0-9_]{0,31}"
PANDAS_VALUE_PATTERN = r"(?:0|[1-9][0-9]{0,2})(?:\.[0-9])?"
PANDAS_GROUP_CASEFOLD_REFUSALS = frozenset(
    {"true", "false", "nan", "na", "null", "none", "inf", "infinity"}
)
