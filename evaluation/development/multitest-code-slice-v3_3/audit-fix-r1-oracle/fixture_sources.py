"""Deterministic source recipes for the independent MT 3.3 audit-fix oracle."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
E16 = REPO / "evaluation/development/blind-envelope-16-2026-08-30/cases"
P3 = E16 / "5a9c5b4377c33916d672/project/analysis.py"
P4 = E16 / "9ced761b41ef93485acf/project/analysis.py"
MATCH = (
    REPO
    / "evaluation/development/multitest-code-slice-v3_3/prototype-sweep/fixtures"
    / "frozen-gate-match-subject-and-guard.py"
)


def _replace_once(source: bytes, old: bytes, new: bytes, name: str) -> bytes:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{name}: replacement anchor count is {count}")
    return source.replace(old, new, 1)


def _count_consumer(source: bytes, *, imports: bytes, statement: bytes, name: str) -> bytes:
    if imports:
        source = _replace_once(source, b"import pandas as pd\n", imports, name + "-import")
    anchor = b'    n_significant = sum(1 for result in results if result["p_value"] < ALPHA)\n'
    return _replace_once(source, anchor, anchor + statement, name)


def fixture_sources() -> dict[str, tuple[str, bytes]]:
    p3 = P3.read_bytes()
    p4 = P4.read_bytes()
    logging_import = b"import logging\nimport pandas as pd\n"
    sys_import = b"import sys\nimport pandas as pd\n"
    warnings_import = b"import warnings\nimport pandas as pd\n"
    values: dict[str, tuple[str, bytes]] = {
        "correct-terminal-count-logging-info": (
            "E16:P4:9ced761b41ef93485acf",
            _count_consumer(
                p4,
                imports=logging_import,
                statement=b'    logging.info("significant count: %s", n_significant)\n',
                name="logging-info",
            ),
        ),
        "correct-terminal-count-warnings-warn": (
            "E16:P4:9ced761b41ef93485acf",
            _count_consumer(
                p4,
                imports=warnings_import,
                statement=b'    warnings.warn(f"significant count: {n_significant}")\n',
                name="warnings-warn",
            ),
        ),
        "correct-terminal-count-sys-stderr-write": (
            "E16:P4:9ced761b41ef93485acf",
            _count_consumer(
                p4,
                imports=sys_import,
                statement=b'    sys.stderr.write(f"significant count: {n_significant}\\n")\n',
                name="sys-stderr-write",
            ),
        ),
        "correct-terminal-count-file-write": (
            "E16:P4:9ced761b41ef93485acf",
            _count_consumer(
                p4,
                imports=sys_import,
                statement=(
                    b"    output_file = sys.stderr\n"
                    b'    output_file.write(f"significant count: {n_significant}\\n")\n'
                ),
                name="file-write",
            ),
        ),
        "correct-terminal-count-logging-warning": (
            "E16:P4:9ced761b41ef93485acf",
            _count_consumer(
                p4,
                imports=logging_import,
                statement=b'    logging.warning("significant count: %s", n_significant)\n',
                name="logging-warning",
            ),
        ),
        "correct-terminal-count-cardinality-summary-warning-branch": (
            "E16:P4:9ced761b41ef93485acf",
            _count_consumer(
                p4,
                imports=b"",
                statement=(
                    b'    summary = "all" if n_significant == len(OUTCOMES) else "partial"\n'
                    b'    if summary == "all":\n'
                    b'        print("warning: all outcomes crossed the threshold")\n'
                ),
                name="cardinality-summary-warning",
            ),
        ),
        "correct-terminal-count-cardinality-and-print": (
            "E16:P4:9ced761b41ef93485acf",
            _count_consumer(
                p4,
                imports=b"",
                statement=b'    n_significant and print("warning: significant outcomes")\n',
                name="cardinality-and-print",
            ),
        ),
        "correct-terminal-count-cardinality-or-print": (
            "E16:P4:9ced761b41ef93485acf",
            _count_consumer(
                p4,
                imports=b"",
                statement=b'    n_significant or print("warning: no significant outcomes")\n',
                name="cardinality-or-print",
            ),
        ),
    }

    fold = _replace_once(
        p4,
        b"    results = test_outcomes(data, OUTCOMES)\n",
        b"    results = test_outcomes(data, OUTCOMES)\n    presentation_fold = []\n",
        "condition-4-fold-init",
    )
    fold = _replace_once(
        fold,
        b'            direction = "higher" if result["difference"] > 0 else "lower"\n',
        b'            direction = "higher" if result["difference"] > 0 else "lower"\n'
        b"            presentation_fold.append(direction)\n",
        "condition-4-fold-consumer",
    )
    values["correct-terminal-presentation-store-consumed-by-later-fold-minimal"] = (
        "E16:P4:9ced761b41ef93485acf",
        fold,
    )

    two_calls = _replace_once(
        p3,
        b"    results = {outcome: compare(data, outcome) for outcome in OUTCOMES}\n",
        b"    diagnostic = compare(data, OUTCOMES[0])\n"
        b"    results = {outcome: compare(data, outcome) for outcome in OUTCOMES}\n",
        "helper-two-call-sites",
    )
    values["correct-helper-record-two-call-sites-gate"] = (
        "E16:P3:5a9c5b4377c33916d672",
        two_calls,
    )
    values["correct-versioned-hierarchy-match-gate"] = (
        "E10:P4:7296b0e2cf7faeefca64",
        MATCH.read_bytes(),
    )

    twice = _replace_once(
        p4,
        b"\ndef main():\n",
        b"\ndef emit_twice(value):\n    print(value)\n    print(value)\n\ndef main():\n",
        "twice-helper-definition",
    )
    twice = twice.replace(b"            print(\n", b"            emit_twice(\n")
    if twice.count(b"emit_twice(") != 3:
        raise ValueError("twice-helper: expected one definition and two arm calls")
    values["positive-terminal-helper-two-prints-frozen-path"] = (
        "E16:P4:9ced761b41ef93485acf",
        twice,
    )
    return values


__all__ = ["fixture_sources"]
