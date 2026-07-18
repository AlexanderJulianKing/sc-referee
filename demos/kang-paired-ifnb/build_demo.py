"""Build the runnable Kang folder from the public H5AD already downloaded under data/."""
from pathlib import Path
import os
import shutil

from bench.analyses import per_cell_wilcoxon
from bench.kang_anchor import load_kang


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parents[1] / "data" / "kang.h5ad"
TARGET = ROOT / "kang.h5ad"
RESULT = ROOT / "results" / "per_cell_wilcoxon.csv"

if not SOURCE.exists():
    raise SystemExit(f"missing {SOURCE}; see bench/kang_anchor.py for the public download URL")
if not TARGET.exists():
    try:
        os.link(SOURCE, TARGET)
    except OSError:
        shutil.copy2(SOURCE, TARGET)

RESULT.parent.mkdir(exist_ok=True)
reported = per_cell_wilcoxon(load_kang(SOURCE))
reported = reported.rename(columns={"feature_id": "gene", "effect": "log2fc"})
reported.to_csv(RESULT, index=False)
print(f"wrote {RESULT} ({len(reported):,} tested genes)")
