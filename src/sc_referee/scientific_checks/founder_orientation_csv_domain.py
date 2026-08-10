"""Bounded staged-CSV domain proofs for founder-orientation semantic v3.1.

This module reads immutable controller-frozen data bytes.  It never imports or
executes project-authored code and never derives an orientation from data
values.  Its only positive result is an exact binary-domain fact for one named
column of one path-and-digest-bound CSV.

The fact must describe the same rows the certified reader actually produces at
runtime, so the prover reproduces the exact runtime line model the analyzer
certified for that staged read.  A ``splitlines`` reader
(``<path-like>.read_text(...).splitlines()`` fed to ``csv.DictReader``) breaks
lines on Python ``str.splitlines()`` boundaries, which include code points that
``csv``'s own newline handling does not treat as row boundaries.  A
``csv_newline`` reader (``csv.DictReader`` over an open file) breaks lines on
``csv``'s newline model.  Proving under the wrong model could describe rows the
runtime never sees, so every mismatch or unknown model abstains.
"""

from __future__ import annotations

import csv
import io

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.core import FrozenMaterialInput
from sc_referee.scientific_checks.founder_orientation_semantic_ir import (
    CsvBinaryDomainFact,
)

MAX_FOUNDER_CSV_DOMAIN_BYTES = 8 * 1024 * 1024
MAX_FOUNDER_CSV_DOMAIN_ROWS = 100_000
MAX_FOUNDER_CSV_DOMAIN_FIELDS = 256
MAX_FOUNDER_CSV_DOMAIN_FIELD_BYTES = 64 * 1024
RECOGNIZED_BINARY_CSV_VALUES = ("0", "1")
RECOGNIZED_LINE_MODELS = ("splitlines", "csv_newline")

# Code points on which Python ``str.splitlines()`` starts a new line but on which
# ``csv``'s own newline handling does not.  ``str.splitlines()`` additionally
# breaks on ``\n``, ``\r``, and ``\r\n`` -- exactly the boundaries ``csv`` also
# recognizes -- so those are omitted here.  When any of these appears anywhere in
# the decoded bytes, ``str.splitlines()`` and ``csv``'s newline model can enumerate
# different rows, so a ``splitlines`` proof abstains rather than risk describing
# rows the runtime never produces.
SPLITLINES_ONLY_SEPARATORS = (
    "\x0b",  # LINE TABULATION (vertical tab)
    "\x0c",  # FORM FEED
    "\x1c",  # FILE SEPARATOR
    "\x1d",  # GROUP SEPARATOR
    "\x1e",  # RECORD SEPARATOR
    "\x85",  # NEXT LINE (NEL)
    "\u2028",  # LINE SEPARATOR
    "\u2029",  # PARAGRAPH SEPARATOR
)


def prove_binary_csv_column(
    material: FrozenMaterialInput,
    *,
    path: str,
    content_digest: str,
    column: str,
    line_model: str,
) -> CsvBinaryDomainFact | None:
    """Prove one exact CSV column is a nonempty subset of ``{"0", "1"}``.

    ``line_model`` is the exact runtime line model the analyzer certified for the
    staged read (:data:`RECOGNIZED_LINE_MODELS`).  The prover enumerates rows
    under that same model so the fact describes the rows the certified reader
    actually produces at runtime.  An unrecognized model produces no fact.

    Every failure is an abstention: wrong binding, digest drift, unsupported
    encoding or layout, a ``splitlines``-only line separator that could make the
    two parsers disagree, ragged rows, non-binary data, or any resource ceiling.
    """

    if (
        line_model not in RECOGNIZED_LINE_MODELS
        or path != material.path
        or content_digest != material.content_digest
        or not column
        or not path.lower().endswith(".csv")
        or len(material.content) > MAX_FOUNDER_CSV_DOMAIN_BYTES
        or sha256_digest(material.content) != content_digest
    ):
        return None
    try:
        text = material.content.decode("utf-8", errors="strict")
        reader = _line_model_reader(text, line_model)
        if reader is None:
            return None
        header = reader.fieldnames
        if (
            header is None
            or not header
            or len(header) > MAX_FOUNDER_CSV_DOMAIN_FIELDS
            or len(set(header)) != len(header)
            or column not in header
            or any(
                not item or len(item.encode("utf-8")) > MAX_FOUNDER_CSV_DOMAIN_FIELD_BYTES
                for item in header
            )
        ):
            return None
        row_count = 0
        for row_count, row in enumerate(reader, start=1):
            if row_count > MAX_FOUNDER_CSV_DOMAIN_ROWS or None in row:
                return None
            values = tuple(row.get(name) for name in header)
            if any(value is None for value in values):
                return None
            fields = tuple(str(value) for value in values)
            if any(
                len(value.encode("utf-8")) > MAX_FOUNDER_CSV_DOMAIN_FIELD_BYTES for value in fields
            ):
                return None
            if str(row[column]) not in RECOGNIZED_BINARY_CSV_VALUES:
                return None
        if row_count == 0:
            return None
    except (csv.Error, UnicodeError, ValueError, OverflowError):
        return None
    return CsvBinaryDomainFact(
        path=path,
        content_digest=content_digest,
        column=column,
        row_count=row_count,
        recognized_values=RECOGNIZED_BINARY_CSV_VALUES,
        line_model=line_model,
    )


def _line_model_reader(text: str, line_model: str) -> csv.DictReader[str] | None:
    """A ``csv.DictReader`` over ``text`` under the certified runtime line model.

    For ``splitlines`` the reader is ``csv.DictReader(text.splitlines())`` -- the
    exact runtime construction -- but only after confirming the decoded text
    holds none of the :data:`SPLITLINES_ONLY_SEPARATORS`.  Those code points are
    row boundaries for ``str.splitlines()`` yet not for ``csv``'s own newline
    handling, so their presence means the two parsers could enumerate different
    rows; the prover abstains (``None``) rather than certify a possibly divergent
    row model.  For ``csv_newline`` the reader uses ``csv``'s newline model over
    the untranslated text.
    """

    if line_model == "splitlines":
        if any(separator in text for separator in SPLITLINES_ONLY_SEPARATORS):
            return None
        return csv.DictReader(text.splitlines())
    if line_model == "csv_newline":
        return csv.DictReader(io.StringIO(text, newline=""))
    return None
