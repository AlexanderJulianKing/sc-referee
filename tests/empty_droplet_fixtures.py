from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from sc_referee.bundle import Bundle, Measure


CELLS = """cell_id,donor,total_umi,HBB,IFI6,ISG15,LST1,CXCL10
cell_A,D1,100,10,2,3,4,5
cell_B,D2,80,8,1,2,3,4
"""
DONORS = """donor,g,sex,age,bmi
D1,0,F,40,22.0
D2,2,M,50,25.0
"""
EMPTY_DROPS = """barcode,total_umi,HBB,IFI6,ISG15,LST1,CXCL10
empty_1,12,5,0,1,0,2
empty_2,9,3,1,0,1,1
"""


@dataclass(frozen=True)
class GBP07Fixture:
    cells: Path
    donors: Path
    empty_drops: Path
    bundle: Bundle


def _bundle() -> Bundle:
    observations = pd.DataFrame(
        {"donor": ["D2", "D1"]}, index=pd.Index(["cell_B", "cell_A"], name="cell_id")
    )
    features = ["CXCL10", "HBB", "LST1", "IFI6", "ISG15"]
    counts = np.array([[4, 8, 3, 1, 2], [5, 10, 4, 2, 3]], dtype=np.uint64)
    feature_metadata = pd.DataFrame(
        {"id_type": ["gene_symbol"] * 5, "gene": features},
        index=pd.Index(features, name="feature_id"),
    )
    return Bundle(
        observations=observations,
        measure=Measure("counts", counts, None, features),
        feature_metadata=feature_metadata,
    )


def write_gbp07_fixture(root: Path) -> GBP07Fixture:
    root = Path(root)
    cells = root / "cells.csv"
    donors = root / "donors.csv"
    empty_drops = root / "empty_drops.csv"
    cells.write_text(CELLS, encoding="utf-8")
    donors.write_text(DONORS, encoding="utf-8")
    empty_drops.write_text(EMPTY_DROPS, encoding="utf-8")
    return GBP07Fixture(cells, donors, empty_drops, _bundle())


def proposed_declaration(
    root: Path,
    fixture: GBP07Fixture,
    *,
    source_path: str = "empty_drops.csv",
    source_compression: str = "none",
    filtered_path: str = "cells.csv",
    filtered_compression: str = "none",
    empty_genes: list[str] | None = None,
) -> Path:
    genes = empty_genes or ["HBB", "IFI6", "ISG15", "LST1", "CXCL10"]
    value = {
        "schema_id": "sc-referee/empty-droplet-ingest-declaration/v1",
        "confirmed_by_human": False,
        "source": {
            "role": "explicit_empty_droplet_count_table", "format": "dense_csv/v1",
            "compression": source_compression, "path": source_path,
            "barcode_key_column": "barcode", "total_count_column": "total_umi",
            "gene_count_columns": genes, "namespace": "",
        },
        "membership": {"method_id": "explicit_empty_table_rows/v1"},
        "filtered_link": {
            "path": filtered_path, "format": "gbp07_cells_csv/v1",
            "compression": filtered_compression, "cell_key_column": "cell_id",
            "total_count_column": "total_umi",
            "gene_count_columns": ["HBB", "IFI6", "ISG15", "LST1", "CXCL10"],
            "namespace": "",
        },
        "proposal": {
            "proposer_kind": "deterministic", "proposer_id": "sc-referee",
            "evidence": ["inventory/header identities only"],
        },
        "confirmation": {
            "confirmer_actor_id": "", "confirmation_event_id": "", "confirmed_at": "",
        },
        "integrity": {"source_sha256": "", "filtered_source_sha256": "", "semantic_digest": ""},
    }
    path = Path(root) / "empty-droplet-ingest.yaml"
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    return path


def confirmed_declaration(root: Path, fixture: GBP07Fixture, **kwargs):
    from sc_referee.empty_droplet.confirmation import confirm_declaration

    path = proposed_declaration(root, fixture, **kwargs)
    return confirm_declaration(
        path, confirmer_actor_id="analyst:test", confirmation_event_id="confirm:test-001",
        confirmed_at="2026-07-11T00:00:00Z",
    )
