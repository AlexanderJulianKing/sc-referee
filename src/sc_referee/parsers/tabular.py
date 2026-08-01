from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

from sc_referee.core.ids import sha256_digest


def inspect_repeated_identifier(path: Path, column: str, run_id: str) -> dict[str, Any]:
    payload = path.read_bytes()
    text = payload.decode("utf-8")
    rows = list(csv.DictReader(text.splitlines()))
    if not rows or column not in rows[0]:
        return {
            "record_type": "repeated_identifier_observation",
            "run_id": run_id,
            "column": column,
            "state": "unavailable",
            "repeated_values": [],
            "source_refs": [],
        }
    counts = Counter(row[column] for row in rows)
    repeated = sorted(value for value, count in counts.items() if count > 1)
    line_count = max(1, len(text.splitlines()))
    return {
        "record_type": "repeated_identifier_observation",
        "run_id": run_id,
        "column": column,
        "state": "observed" if repeated else "not_observed",
        "repeated_values": repeated,
        "source_refs": [
            {
                "source_kind": "file_span",
                "locator": f"{path.name}:1-{line_count}",
                "path": path.name,
                "content_digest": sha256_digest(payload),
                "start_line": 1,
                "end_line": line_count,
                "quoted_text": text.strip(),
            }
        ],
    }
