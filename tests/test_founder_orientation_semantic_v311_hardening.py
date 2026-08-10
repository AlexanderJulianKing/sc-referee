"""Regressions for the founder v3.1.1 reader-form / line-model binding.

The v3.1.0 CSV domain prover always parsed with ``csv``'s own newline model,
even for workflows whose certified reader is ``read_text().splitlines()`` fed to
``csv.DictReader``.  Python ``str.splitlines()`` breaks lines on more code points
than ``csv``'s newline handling, so the prover's row model and the workflow's
runtime row model were two different parsers whose equivalence was assumed.

v3.1.1 binds the proof to the reader form: the analyzer certifies which line
model each staged read uses, the prover reproduces exactly that model (and, for
the splitlines model, abstains when any splitlines-only separator could make the
two parsers disagree), and the kernel discharges an obligation only when the
proven fact's line model equals the certified one.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

import pytest

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks import FrozenMaterialInput, RecordRef
from sc_referee.scientific_checks.founder_orientation_csv_domain import (
    RECOGNIZED_LINE_MODELS,
    SPLITLINES_ONLY_SEPARATORS,
    prove_binary_csv_column,
)
from sc_referee.scientific_checks.founder_orientation_semantic import (
    resolve_founder_orientation_semantic,
)
from tests.test_founder_orientation_semantic_pilots import (
    CASES_E,
    ERROR_BEARING_E,
    REPORT_PATH,
    WORKFLOW_PATH,
    _resolution,
    _with_bound_csv,
)
from tests.test_founder_orientation_semantic_v301_hardening import (
    DIRECT_OPERAND,
    REPAIRED_OPERAND,
    _runtime_context,
)
from tests.test_founder_pilot_burned_case_regression import _inspection_context

_PARSER_ID = "parser:python-ast-tokenize"
_PARSER_VERSION = "1.0.0"


def _material(content: bytes) -> FrozenMaterialInput:
    return FrozenMaterialInput(
        path="inputs/data.csv",
        file_ref=RecordRef("file_record", "file:data"),
        asset_identity_ref=RecordRef("asset_identity", "identity:data"),
        content=content,
        content_digest=sha256_digest(content),
    )


def _prove(content: bytes, column: str, line_model: str):
    material = _material(content)
    return prove_binary_csv_column(
        material,
        path=material.path,
        content_digest=material.content_digest,
        column=column,
        line_model=line_model,
    )


# --- prover level -----------------------------------------------------------


@pytest.mark.parametrize("separator", SPLITLINES_ONLY_SEPARATORS)
def test_splitlines_only_separator_anywhere_abstains_under_the_splitlines_model(
    separator: str,
) -> None:
    """A splitlines-only separator, even in a non-compared field, gives no fact.

    Under the splitlines model the code point starts a new runtime row that
    ``csv``'s newline model never sees, so the two parsers could diverge and the
    prover must abstain rather than describe rows the runtime never produces.
    """

    content = ("call,founder,note\n0,0,a\n1,1,b\n0,0,c\n1,0,x" + separator + "y\n").encode("utf-8")
    assert _prove(content, "call", "splitlines") is None
    assert _prove(content, "founder", "splitlines") is None


@pytest.mark.parametrize("separator", SPLITLINES_ONLY_SEPARATORS)
def test_splitlines_only_separator_is_a_real_runtime_divergence(separator: str) -> None:
    """Document why the abstention is principled, not merely cautious.

    ``str.splitlines()`` splits on the separator and yields a row ``csv``'s
    newline model never produces; the runtime cast on the extra row then raises,
    so a false ``repaired`` was only incidentally avoided before v3.1.1.
    """

    text = "call,founder,note\n0,0,a\n1,1,b\n0,0,c\n1,0,x" + separator + "y\n"
    splitlines_rows = [dict(row) for row in csv.DictReader(text.splitlines())]
    csv_rows = [dict(row) for row in csv.DictReader(io.StringIO(text, newline=""))]
    assert splitlines_rows != csv_rows
    assert len(splitlines_rows) == len(csv_rows) + 1
    with pytest.raises((TypeError, ValueError)):
        for row in splitlines_rows:
            int(row["call"])
            int(row["founder"])


def test_csv_newline_model_handles_a_quoted_embedded_newline() -> None:
    """The csv-over-file model parses a quoted embedded newline and certifies.

    A quoted embedded newline in a non-compared field is one ``csv`` record at
    runtime (``csv.DictReader`` over the open file) and one prover record under
    the csv_newline model, so the compared column still proves binary.
    """

    content = b'call,founder,note\n0,0,"first line\nsecond line"\n1,1,plain\n'
    fact = _prove(content, "call", "csv_newline")
    assert fact is not None
    assert fact.row_count == 2
    assert fact.line_model == "csv_newline"
    # The exact runtime reader agrees on the row count.
    runtime_rows = list(csv.DictReader(io.StringIO(content.decode("utf-8"))))
    assert len(runtime_rows) == fact.row_count


def test_a_clean_csv_agrees_under_both_line_models() -> None:
    content = b"call,founder\n0,0\n1,1\n0,0\n1,0\n"
    for line_model in RECOGNIZED_LINE_MODELS:
        fact = _prove(content, "call", line_model)
        assert fact is not None
        assert fact.row_count == 4
        assert fact.line_model == line_model


def test_an_unrecognized_line_model_produces_no_fact() -> None:
    content = b"call,founder\n0,0\n1,1\n"
    assert _prove(content, "call", "universal") is None
    assert _prove(content, "call", "") is None


# --- end to end: splitlines pilots --------------------------------------------


def _pilot_e_context(project_root: Path, csv_bytes: bytes):
    case = project_root / CASES_E / ERROR_BEARING_E
    context = _inspection_context(
        (case / REPORT_PATH).read_bytes(),
        (case / WORKFLOW_PATH).read_bytes(),
    )
    return _with_bound_csv(context, csv_bytes)


def test_splitlines_pilot_still_certifies_over_clean_bytes(project_root: Path) -> None:
    case = project_root / CASES_E / ERROR_BEARING_E
    original = (case / "inputs/data.csv").read_bytes()
    resolution = _resolution(_pilot_e_context(project_root, original))
    assert resolution.state == "unique"
    assert resolution.orientation == "repaired"
    assert {fact.line_model for fact in resolution.certificate.domain_facts} == {"splitlines"}


def test_splitlines_pilot_abstains_when_a_noncompared_field_holds_a_separator(
    project_root: Path,
) -> None:
    """A separator in a non-compared field abstains even though csv's model would
    still read the compared columns as binary (the exact v3.1.0 seam)."""

    case = project_root / CASES_E / ERROR_BEARING_E
    original = (case / "inputs/data.csv").read_bytes()
    assert b"Permian" in original
    mutated = original.replace(b"Permian", b"Permi\x0ban", 1)
    assert mutated != original

    # The compared columns are still binary under csv's own newline model, so the
    # retired csv_newline-only prover would have manufactured a fact here.
    csv_text = mutated.decode("utf-8")
    csv_rows = list(csv.DictReader(io.StringIO(csv_text, newline="")))
    assert all(row["aerial_call"] in {"0", "1"} for row in csv_rows)
    assert all(row["panel_call"] in {"0", "1"} for row in csv_rows)
    # But the runtime splitlines reader diverges (an extra, short row).
    splitlines_rows = list(csv.DictReader(csv_text.splitlines()))
    assert len(splitlines_rows) == len(csv_rows) + 1

    resolution = _resolution(_pilot_e_context(project_root, mutated))
    assert resolution.state != "unique"
    assert resolution.orientation is None
    assert resolution.certificate is None


# --- end to end: ragged-tolerant readers --------------------------------------


def test_get_with_default_reader_abstains(tmp_path: Path) -> None:
    """A ``.get(col, default)`` compared read tolerates a short row at runtime, so
    the analyzer must abstain rather than trust the prover's ragged rejection."""

    source = """import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
score = sum(1 * (int(row['call']) == 1 - int(row.get('founder', '0'))) for row in rows)
rate = score / 4
report = f'[selected-result] Of 4 markers, {score} agree. Agreement rate {rate:.6f}. Score {score}.'
Path('results/report.md').write_text(report, encoding='ascii')
"""
    context = _runtime_context(tmp_path, source)
    resolution = resolve_founder_orientation_semantic(
        context,
        direct_operand=DIRECT_OPERAND,
        repaired_operand=REPAIRED_OPERAND,
        parser_id=_PARSER_ID,
        parser_version=_PARSER_VERSION,
    )
    assert resolution.state != "unique"
    assert resolution.orientation is None


def test_try_except_around_cast_reader_abstains(tmp_path: Path) -> None:
    """A ``try``/``except`` around the compared cast tolerates a bad row at
    runtime, so the analyzer must abstain."""

    source = """import csv
from pathlib import Path


def panel_reading(field):
    try:
        return 1 - int(field)
    except ValueError:
        return 0


rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
score = sum(1 * (int(row['call']) == panel_reading(row['founder'])) for row in rows)
rate = score / 4
report = f'[selected-result] Of 4 markers, {score} agree. Agreement rate {rate:.6f}. Score {score}.'
Path('results/report.md').write_text(report, encoding='ascii')
"""
    context = _runtime_context(tmp_path, source)
    resolution = resolve_founder_orientation_semantic(
        context,
        direct_operand=DIRECT_OPERAND,
        repaired_operand=REPAIRED_OPERAND,
        parser_id=_PARSER_ID,
        parser_version=_PARSER_VERSION,
    )
    assert resolution.state != "unique"
    assert resolution.orientation is None
