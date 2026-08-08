"""Soundness controls for the quantity dataflow trace.

Every case here is a demonstrated wrong-operand or crash counterexample from
the adversarial review of detector v2.0.4. The invariant under test: the
trace either classifies correctly or abstains; it never answers wrongly and
never crashes.
"""

from __future__ import annotations

import ast

from sc_referee.scientific_checks.quantity_consistency_adapter import _number_tokens
from sc_referee.scientific_checks.quantity_dataflow_adapter import _document_divisions

COMPLETE = "COMPLETE"
RETAINED = "RETAINED"


def _resolve(source: str) -> tuple[bool, set[str]]:
    outcome = _document_divisions(
        ast.parse(source), complete_operand=COMPLETE, retained_operand=RETAINED
    )
    return outcome["unsupported_flow"], {item.operand_value for item in outcome["divisions"]}


def test_diagnostic_division_never_becomes_the_operand() -> None:
    """A subset division whose value is never written must not classify."""

    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))
kept = [r for r in rows if r['ok'] == 'yes']
events = sum(1 for r in kept if r['event'] == 'yes')
diagnostic = events / len(kept)
selected = 'static text'
Path('results/report.md').write_text(selected)
"""
    _unsupported, operands = _resolve(source)
    assert operands == set()


def test_written_division_still_classifies() -> None:
    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))
kept = [r for r in rows if r['ok'] == 'yes']
events = sum(1 for r in kept if r['event'] == 'yes')
rate = events / len(kept)
report = f'rate {rate}'
Path('results/report.md').write_text(report)
"""
    unsupported, operands = _resolve(source)
    assert not unsupported
    assert operands == {RETAINED}


def test_conditional_return_helper_is_opaque() -> None:
    """A helper whose returns disagree must not adopt either branch's tag."""

    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))
kept = [r for r in rows if r['ok'] == 'yes']
events = sum(1 for r in kept if r['event'] == 'yes')

def denominator(all_rows, kept_rows, use_full):
    if use_full:
        return len(all_rows)
    return len(kept_rows)

rate = events / denominator(rows, kept, True)
Path('results/report.md').write_text(f'{rate}')
"""
    _unsupported, operands = _resolve(source)
    assert RETAINED not in operands
    assert COMPLETE not in operands


def test_keyword_call_binds_by_name_not_by_global() -> None:
    """Keyword arguments must bind; globals must never leak into parameters."""

    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))
kept = [r for r in rows if r['ok'] == 'yes']
denominator = len(kept)
events = sum(1 for r in kept if r['event'] == 'yes')
planned = len(rows)

def rate_of(events, denominator):
    return events / denominator

selected = rate_of(events=events, denominator=planned)
Path('results/report.md').write_text(f'{selected}')
"""
    _unsupported, operands = _resolve(source)
    assert operands == {COMPLETE}


def test_consumed_iterator_loses_full_provenance() -> None:
    """next(reader) before list(reader) means the rows are not the full set."""

    source = """import csv
from pathlib import Path
handle = Path('inputs/data.csv').open()
reader = csv.DictReader(handle)
first = next(reader)
rows = list(reader)
events = sum(1 for r in rows if r['event'] == 'yes')
rate = events / len(rows)
Path('results/report.md').write_text(f'{rate}')
"""
    _unsupported, operands = _resolve(source)
    assert COMPLETE not in operands


def test_deletion_in_loop_invalidates_the_collection() -> None:
    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))
events = 3
for row in rows[:]:
    if row.get('bad') == 'yes':
        del rows[0]
rate = events / len(rows)
Path('results/report.md').write_text(f'{rate}')
"""
    unsupported, operands = _resolve(source)
    assert not (not unsupported and operands == {COMPLETE})


def test_mutation_through_local_helper_invalidates_the_argument() -> None:
    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))
events = 3

def prune(xs):
    for row in xs[:]:
        if row.get('bad') == 'yes':
            xs.remove(row)

prune(rows)
rate = events / len(rows)
Path('results/report.md').write_text(f'{rate}')
"""
    unsupported, operands = _resolve(source)
    assert not (not unsupported and operands == {COMPLETE})


def test_recursive_helper_abstains_instead_of_crashing() -> None:
    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))

def spiral(n):
    return spiral(n)

value = spiral(3)
rate = value / len(rows)
Path('results/report.md').write_text(f'{rate}')
"""
    _unsupported, operands = _resolve(source)
    assert operands == set()


def test_lambda_bodies_never_classify() -> None:
    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))
kept = [r for r in rows if r['ok'] == 'yes']
events = sum(1 for r in kept if r['event'] == 'yes')
f = lambda events, kept: events / len(kept)
rate = f(events, kept)
Path('results/report.md').write_text(f'{rate}')
"""
    _unsupported, operands = _resolve(source)
    assert operands == set()


def test_helper_computed_rate_still_reaches_the_report() -> None:
    """A rate computed inside a helper and written by the caller classifies."""

    source = """import csv
from fractions import Fraction
from pathlib import Path

def load(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))

def rate_of(events, denominator):
    return Fraction(events, denominator)

rows = load(Path('inputs/data.csv'))
kept = [r for r in rows if r['ok'] == 'yes']
events = sum(1 for r in kept if r['event'] == 'yes')
rate = rate_of(events, len(kept))
Path('results/report.md').write_text(f'{rate}')
"""
    unsupported, operands = _resolve(source)
    assert not unsupported
    assert operands == {RETAINED}


def test_signed_and_slash_date_tokens_are_excluded() -> None:
    text = (
        "Coefficient -0.5 on 08/07/2026; planned 40, retained 32, removed 8, "
        "events 24, rate 0.75, fraction 24/32."
    )
    values = [token.raw for token in _number_tokens(text)]
    assert "0.5" not in values
    for date_part in ("08", "07", "2026"):
        assert date_part not in values
    for kept_value in ("40", "32", "8", "24", "0.75"):
        assert kept_value in values


def test_exhaustive_dict_counter_counts_the_source() -> None:
    """+= 1 in both branches counts every row; a subset tag would be wrong."""

    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))
counts = {"den": 0, "events": 0}
for row in rows:
    if row['ok'] == 'yes':
        counts["den"] += 1
        counts["events"] += 1
    else:
        counts["den"] += 1
rate = counts["events"] / counts["den"]
Path('results/report.md').write_text(f'{rate}')
"""
    unsupported, operands = _resolve(source)
    assert not unsupported
    assert operands == {COMPLETE}


def test_guarded_dict_counter_counts_a_subset() -> None:
    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))
counts = {"den": 0, "events": 0}
for row in rows:
    if row['ok'] == 'yes':
        counts["den"] += 1
        if row['event'] == 'yes':
            counts["events"] += 1
rate = counts["events"] / counts["den"]
Path('results/report.md').write_text(f'{rate}')
"""
    unsupported, operands = _resolve(source)
    assert not unsupported
    assert operands == {RETAINED}


def test_exhaustive_append_copies_the_source() -> None:
    """append in both branches copies every row; a subset tag would be wrong."""

    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))
kept = []
for row in rows:
    if row['ok'] == 'yes':
        kept.append(row)
    else:
        kept.append(row)
events = sum(1 for r in kept if r['event'] == 'yes')
rate = events / len(kept)
Path('results/report.md').write_text(f'{rate}')
"""
    unsupported, operands = _resolve(source)
    assert not unsupported
    assert operands == {COMPLETE}


def test_guarded_append_builds_a_subset() -> None:
    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))
kept = []
for row in rows:
    if row['ok'] == 'yes':
        kept.append(row)
events = sum(1 for r in kept if r['event'] == 'yes')
rate = events / len(kept)
Path('results/report.md').write_text(f'{rate}')
"""
    unsupported, operands = _resolve(source)
    assert not unsupported
    assert operands == {RETAINED}


def test_post_loop_mutation_invalidates_the_accumulator() -> None:
    """clear()+extend(rows) after the loop makes kept the full set; the
    stale subset tag must not survive."""

    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))
kept = []
for row in rows:
    if row['ok'] == 'yes':
        kept.append(row)
kept.clear()
kept.extend(rows)
events = 3
rate = events / len(kept)
Path('results/report.md').write_text(f'{rate}')
"""
    _unsupported, operands = _resolve(source)
    assert RETAINED not in operands


def test_loop_local_shadowing_a_tagged_name_is_rejected() -> None:
    """A loop-local assignment reusing a provenance-tagged name rejects the
    loop rather than silently rebinding provenance."""

    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/data.csv').open()))
kept = [r for r in rows if r['ok'] == 'yes']
counter = 0
for row in rows:
    kept = row
    counter += 1
events = 3
rate = events / len(kept)
Path('results/report.md').write_text(f'{rate}')
"""
    unsupported, operands = _resolve(source)
    assert not (not unsupported and operands == {RETAINED})
