from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "/Users/alexanderking/.cache/recon-scratch/work")
from mut import report  # noqa: E402

CASES = Path(
    "/Users/alexanderking/.cache/recon-scratch/vnext/evaluation/development/"
    "multitest-open-corpus-v1/cases"
)
LABELS = json.loads((CASES.parent / "specs" / "labels.json").read_text())

want = sys.argv[1] if len(sys.argv) > 1 else "all"
for spec in sorted(LABELS):
    label = LABELS[spec]["label"]
    if want != "all" and want != label:
        continue
    print(f"{label:8s} {report(spec, CASES / spec / 'analysis.py')}")
