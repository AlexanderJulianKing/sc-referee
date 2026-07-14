"""The D1 guaranteed-blocker fixture (C9).

`culture_condition` is completely aliased with `processing_run`: all 4 control donors were
processed in run R1, all 4 stim donors in run R2. No model — not a better one, not an
LLM's — can separate the condition effect from the run effect. `confounding` must emit a
power-INDEPENDENT `blocker`. Deterministic; the dummy counts are never used by the check.

Run directly to (re)generate the committed fixture:  python fixtures/confounding_alias/make_fixture.py
"""
from __future__ import annotations

import json
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import yaml

N_GENES = 5
CELLS_PER_DONOR = 3
SEED = 0


def build(outdir) -> Path:
    outdir = Path(outdir)
    (outdir / "results").mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    donors = [f"D{i}" for i in range(1, 9)]
    condition = ["ctrl"] * 4 + ["stim"] * 4          # D1-4 ctrl, D5-8 stim
    run = ["R1"] * 4 + ["R2"] * 4                     # ... completely aliased with the run
    donor_meta = dict(zip(donors, zip(condition, run)))

    rows = []
    cell_ids = []
    k = 0
    for d in donors:
        cond, r = donor_meta[d]
        for _ in range(CELLS_PER_DONOR):
            rows.append((d, cond, r))
            cell_ids.append(f"cell{k}")
            k += 1
    obs = pd.DataFrame(rows, columns=["donor_id", "culture_condition", "processing_run"], index=cell_ids)

    X = rng.integers(0, 50, size=(len(obs), N_GENES)).astype("int32")
    var = pd.DataFrame(index=[f"GENE{i}" for i in range(N_GENES)])
    adata = ad.AnnData(X=X, obs=obs, var=var)
    adata.write_h5ad(outdir / "confounding_alias.h5ad")

    # a trivial reported DE table so folder discovery has a `reported` role to resolve
    pd.DataFrame(
        {
            "gene": [f"GENE{i}" for i in range(N_GENES)],
            "pvalue": [1e-3] * N_GENES,
            "padj": [1e-2] * N_GENES,
            "log2fc": [1.5] * N_GENES,
        }
    ).to_csv(outdir / "results" / "de.csv", index=False)

    cfg = {
        "analysis_type": "condition_contrast_DE",
        "confirmed_by_human": True,
        "design": {
            "replicate_unit": ["donor_id"],
            "condition": "culture_condition",
            "batch": ["processing_run"],
        },
        "contrasts": [
            {
                "name": "stim_vs_ctrl",
                "reference": "ctrl",
                "test": "stim",
                "replicate_unit": ["donor_id"],
                "sample_unit": ["donor_id"],
                "pairing_unit": ["donor_id"],
                "model": "~ culture_condition",
                "target_coefficient": "culture_condition[T.stim]",
            }
        ],
        "reported_results": {"path": "results/de.csv", "gene_col": "gene",
                             "padj_col": "padj", "unit_of_test": "sample"},
        "confidence": {"replicate_unit": "high", "condition": "high"},
        "unresolved": [],
    }
    (outdir / "sc-referee.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))

    expected = {
        "checks": {"confounding": {"status": "blocker"}},
        "provenance_must_include": ["data", "reported"],
    }
    (outdir / "expected_report.json").write_text(json.dumps(expected, indent=2) + "\n")
    return outdir


if __name__ == "__main__":
    out = build(Path(__file__).parent)
    print(f"wrote confounding_alias fixture to {out}")
