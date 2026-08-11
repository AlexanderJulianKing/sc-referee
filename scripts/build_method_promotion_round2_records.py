from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from sc_referee_evaluation.complete_domain_promotion import (
    build_round2_records as build_complete_domain_round2_records,
)
from sc_referee_evaluation.dependence_promotion import (
    build_round2_records as build_dependence_round2_records,
)

from sc_referee.records.normalization import write_normalized_json_once

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "reference/schemas-v0.19.0"

_COMPLETE_LANE = ROOT / (
    "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2"
)
_DEPENDENCE_LANE = ROOT / (
    "evaluation/qualification/authorized-independent-unit-entry-into-row-independent-"
    "procedure-v1.1.0-direct-lane"
)

Round2Builder = Callable[..., tuple[dict[str, Any], dict[str, Any]]]


def _build_one(
    builder: Round2Builder,
    *,
    ledger: Path,
    authoring_protocol: Path,
    recorded_at: str,
    output: Path,
) -> None:
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"Round-2 output must be absent or empty: {output}")
    metric_set, qualification = builder(
        ledger,
        authoring_protocol,
        recorded_at=recorded_at,
        schema_root=SCHEMA_ROOT,
    )
    output.mkdir(parents=True, exist_ok=True)
    write_normalized_json_once(output / "QUALIFICATION_METRIC_SET.json", metric_set)
    write_normalized_json_once(output / "DETECTOR_QUALIFICATION.json", qualification)


def main() -> None:
    _build_one(
        build_complete_domain_round2_records,
        ledger=(_COMPLETE_LANE / "heldout-v207-seven-case/detector-run/DETECTOR_RUN_LEDGER.json"),
        authoring_protocol=(
            _COMPLETE_LANE / "heldout-v207-seven-case/authoring/AUTHORING_PROTOCOL.json"
        ),
        recorded_at="2026-08-10T15:22:54Z",
        output=_COMPLETE_LANE / "promotion-round2",
    )
    _build_one(
        build_dependence_round2_records,
        ledger=(_DEPENDENCE_LANE / "heldout-seven-case/detector-run/DETECTOR_RUN_LEDGER.json"),
        authoring_protocol=(
            _DEPENDENCE_LANE / "heldout-seven-case/authoring/AUTHORING_PROTOCOL.json"
        ),
        recorded_at="2026-08-11T00:51:15Z",
        output=_DEPENDENCE_LANE / "promotion-round2",
    )
    print("Built both schema-v0.19 Round-2 promotion record sets without installing grants.")


if __name__ == "__main__":
    main()
