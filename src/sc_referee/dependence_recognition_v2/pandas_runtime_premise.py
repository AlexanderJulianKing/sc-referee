"""Immutable development-only pandas runtime premise for Growth 14.

This module is a literal proof premise.  It does not import pandas, inspect an
external environment, install a package, or confer production/qualification
authority.  It may derive import suffixes from the running proof interpreter
only after that interpreter matches the pinned Python identity.  The liveness
probe for these literals belongs to the development test gate.
"""

from __future__ import annotations

import importlib.machinery
import sys
import sysconfig
from dataclasses import asdict, dataclass

from sc_referee.core.ids import semantic_digest


@dataclass(frozen=True, order=True)
class PandasDevelopmentRuntimePremise:
    premise_id: str
    python_version: str
    python_implementation: str
    python_cache_tag: str
    python_soabi: str
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
    python_implementation="cpython",
    python_cache_tag="cpython-311",
    python_soabi="cpython-311-darwin",
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


@dataclass(frozen=True)
class PinnedPythonImportSuffixVocabulary:
    """Importer-reported module suffixes from the matching proof interpreter."""

    source_suffixes: tuple[str, ...]
    bytecode_suffixes: tuple[str, ...]
    extension_suffixes: tuple[str, ...]

    @property
    def all_suffixes(self) -> tuple[str, ...]:
        return self.source_suffixes + self.bytecode_suffixes + self.extension_suffixes


def derive_pinned_python_import_suffix_vocabulary() -> PinnedPythonImportSuffixVocabulary | None:
    """Return the matching interpreter's unambiguous import suffix vocabulary."""

    premise = PANDAS_DEVELOPMENT_RUNTIME_PREMISE
    try:
        running_version = ".".join(str(part) for part in sys.version_info[:3])
        if (
            running_version != premise.python_version
            or sys.implementation.name != premise.python_implementation
            or sys.implementation.cache_tag != premise.python_cache_tag
            or sysconfig.get_config_var("SOABI") != premise.python_soabi
        ):
            return None
        source_suffixes = tuple(importlib.machinery.SOURCE_SUFFIXES)
        bytecode_suffixes = tuple(importlib.machinery.BYTECODE_SUFFIXES)
        extension_suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)
        all_suffixes = tuple(importlib.machinery.all_suffixes())
    except (AttributeError, TypeError, ValueError):
        return None
    categories = (source_suffixes, bytecode_suffixes, extension_suffixes)
    derived = source_suffixes + bytecode_suffixes + extension_suffixes
    if (
        any(not category for category in categories)
        or all_suffixes != derived
        or any(
            not isinstance(suffix, str)
            or not suffix.startswith(".")
            or "/" in suffix
            or "\\" in suffix
            or "\x00" in suffix
            for suffix in derived
        )
        or len(set(derived)) != len(derived)
    ):
        return None
    return PinnedPythonImportSuffixVocabulary(
        source_suffixes=source_suffixes,
        bytecode_suffixes=bytecode_suffixes,
        extension_suffixes=extension_suffixes,
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
