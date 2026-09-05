"""Re-execute and verify every recorded E14 recon result without writing evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import census
import ladders
import sweep

ROOT = Path(__file__).parent


def _load(name: str) -> dict[str, Any]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main() -> None:
    census_expected = _load("census_results.json")
    census_actual = census.execute()
    compact_census = [
        [
            row["role"],
            row["case_id"],
            row["authorized_count"],
            row["resolved_call_count"],
            row["census_reason"],
            row["adapter_outcome"],
            row["adapter_reason_or_classification"],
        ]
        for row in census_actual["cases"]
    ]
    assert compact_census == census_expected["cases"]

    ladder_expected = _load("ladder_results.json")
    ladder_actual = ladders.execute()
    compact_ladders = {
        role: [
            [row["rung"], row["outcome"][0], row["outcome"][1]]
            for row in ladder_actual["ladders"][role]
        ]
        for role in ladder_actual["ladders"]
    }
    assert compact_ladders == ladder_expected["ladders"]

    sweep_expected = _load("sweep_results.json")
    sweep_actual = sweep.execute()
    proposal = "D14-A-singleton-projection-generator"
    proposal_counts = sweep_actual["none_flip"][proposal]
    assert proposal_counts["corpus_correct"] == {"candidates": 0, "executed": 25}
    assert proposal_counts["opened_negatives"] == {"candidates": 0, "executed": 45}
    assert proposal_counts["historical_fa"]["executed"] == 22
    assert proposal_counts["historical_fa"]["candidates"] == 0
    assert proposal_counts["d14_fa"]["executed"] == 6
    assert proposal_counts["d14_fa"]["candidates"] == 0
    assert proposal_counts["d14_fa"]["outcomes"] == sweep_expected["D14_A_FA_outcomes"]
    assert sweep_actual["corpus_movements"][proposal] == {}
    assert sweep_actual["opened_movements"][proposal] == sweep_expected["opened_movements"]
    assert {
        role: values[proposal] for role, values in sweep_actual["miss_projection"].items()
    } == sweep_expected["miss_projection"]
    print("verified: 15 census rows, 18 adapter rungs, 98 proposal none-flip cases")


if __name__ == "__main__":
    main()
