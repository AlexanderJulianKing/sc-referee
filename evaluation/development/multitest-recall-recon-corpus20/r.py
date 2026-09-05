"""Run the v2 analyzer on a spec with an optional replacement source file."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "/Users/alexanderking/.cache/recon-scratch/work")
from h import reason  # noqa: E402

if __name__ == "__main__":
    spec = sys.argv[1]
    src = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    print(f"{spec} {src.name if src else 'ORIGINAL':24s} -> {reason(spec, src)}")
