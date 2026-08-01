from __future__ import annotations

import argparse
import csv
import io
import json
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.storage.atomic import atomic_create_bytes

FAMILY_ID = "control-family:multiple-testing-bh-v1"
FROZEN_AT = "2026-07-31T23:30:00Z"
ALPHA = Decimal("0.05")
RAW_P_VALUES = (
    "0.001",
    "0.01",
    "0.02",
    "0.04",
    "0.2",
    "0.4",
    "0.6",
    "0.8",
    "0.9",
    "0.95",
)


def benjamini_hochberg_oracle(p_values: tuple[str, ...]) -> tuple[str, ...]:
    """Independent exact-decimal BH oracle for the frozen evaluator-owned controls."""

    if not p_values:
        raise ValueError("BH requires at least one p-value.")
    parsed = tuple(Decimal(value) for value in p_values)
    if any(not value.is_finite() or value < 0 or value > 1 for value in parsed):
        raise ValueError("BH p-values must be finite values in [0, 1].")
    order = sorted(range(len(parsed)), key=lambda index: (parsed[index], index))
    adjusted = [Decimal(1)] * len(parsed)
    running = Decimal(1)
    with localcontext() as context:
        context.prec = 50
        for reverse_rank, index in reversed(list(enumerate(order, start=1))):
            candidate = parsed[index] * Decimal(len(parsed)) / Decimal(reverse_rank)
            running = min(running, candidate, Decimal(1))
            adjusted[index] = running
    return tuple(_decimal_text(value) for value in adjusted)


def build_multiple_testing_control_family(
    output: Path,
    *,
    frozen_at: str = FROZEN_AT,
) -> dict[str, Any]:
    """Create a no-replace four-role development family without production labels in workspaces."""

    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Control-family output already exists: {output}")
    output.mkdir(parents=True)

    bh_adjusted = benjamini_hochberg_oracle(RAW_P_VALUES)
    raw_significant = tuple(Decimal(value) <= ALPHA for value in RAW_P_VALUES)
    bh_significant = tuple(Decimal(value) <= ALPHA for value in bh_adjusted)
    common_report = (
        "# Differential-expression results\n\n"
        "Multiplicity contract: Benjamini-Hochberg false-discovery-rate control at alpha 0.05 "
        "over the complete tested family in `results.csv`. Raw p-values are in `p_value`, "
        "reported adjusted p-values are in `adjusted_p_value`, and final discovery calls are "
        "in `significant`.\n"
    )
    cases = (
        {
            "case_id": "multiple-testing-positive",
            "role": "positive",
            "contract_status": "complete_bh_fdr",
            "expected_outcome": "nonconformant",
            "report": common_report,
            "rows": _rows(RAW_P_VALUES, RAW_P_VALUES, raw_significant),
            "reason": (
                "The complete-family BH/FDR contract is explicit, but the adjusted column equals "
                "the raw p-values and four calls are reported although only two survive BH."
            ),
        },
        {
            "case_id": "multiple-testing-corrected-twin",
            "role": "verified_good",
            "contract_status": "complete_bh_fdr",
            "expected_outcome": "conformant",
            "report": common_report,
            "rows": _rows(RAW_P_VALUES, bh_adjusted, bh_significant),
            "reason": ("The same raw p-values use the independently derived BH values and calls."),
        },
        {
            "case_id": "multiple-testing-hard-negative",
            "role": "hard_negative",
            "contract_status": "single_preregistered_primary",
            "expected_outcome": "not_applicable",
            "report": (
                "# Primary endpoint\n\n"
                "This table reports the one preregistered primary hypothesis. No family of "
                "secondary discoveries is claimed, so no multiple-testing adjustment governs "
                "this decision.\n"
            ),
            "rows": _rows(("0.03",), ("0.03",), (True,)),
            "reason": (
                "A p-value below 0.05 is present, but the declared decision is one primary "
                "hypothesis rather than a multiplicity-controlled discovery family."
            ),
        },
        {
            "case_id": "multiple-testing-ambiguous",
            "role": "ambiguous",
            "contract_status": "family_incomplete",
            "expected_outcome": "insufficient_evidence",
            "report": (
                "# Selected discoveries\n\n"
                "`results.csv` contains only selected hits. The complete set of tested hypotheses "
                "and the governing multiplicity procedure are unavailable.\n"
            ),
            "rows": _rows(("0.001", "0.01"), ("", ""), (True, True)),
            "reason": (
                "The retained hits cannot establish the complete testing family or a governing "
                "adjustment method."
            ),
        },
    )

    case_records: list[dict[str, Any]] = []
    for case in cases:
        workspace = output / "cases" / str(case["case_id"]) / "workspace"
        workspace.mkdir(parents=True)
        _write_once(workspace / "report.md", str(case["report"]).encode("utf-8"))
        _write_once(workspace / "results.csv", _csv_bytes(case["rows"]))
        case_records.append(
            {
                "case_id": case["case_id"],
                "role": case["role"],
                "workspace": f"cases/{case['case_id']}/workspace",
                "selected_report": "report.md",
                "contract_status": case["contract_status"],
                "expected_outcome": case["expected_outcome"],
                "reason": case["reason"],
                "raw_p_values_digest": semantic_digest([row["p_value"] for row in case["rows"]]),
            }
        )

    oracle = {
        "oracle_id": "oracle:multiple-testing-bh-exact-decimal-v1",
        "oracle_scope": "evaluation_only",
        "algorithm": (
            "Sort finite p-values ascending, compute p*m/rank, apply reverse cumulative minima, "
            "cap at one, and restore original order."
        ),
        "alpha": _decimal_text(ALPHA),
        "raw_p_values": list(RAW_P_VALUES),
        "bh_adjusted_p_values": list(bh_adjusted),
        "raw_discovery_count": sum(raw_significant),
        "bh_discovery_count": sum(bh_significant),
        "implementation_independence": (
            "This evaluator-owned script imports no production detector, scientific adapter, or "
            "multiple-testing implementation."
        ),
    }
    _write_json_once(output / "ORACLE.json", oracle)
    specification = {
        "control_family_id": FAMILY_ID,
        "family_version": "1.0.0",
        "frozen_at": frozen_at,
        "scientific_scope": "benjamini_hochberg_complete_family_fdr_conformance",
        "cases": case_records,
        "controls": {
            "one_material_difference_per_twin": True,
            "labels_outside_workspaces": True,
            "project_code_execution": False,
            "production_finding_permission": False,
            "old_public_repository_is_authority": False,
        },
        "limitations": [
            "These evaluator-owned controls establish mechanism behavior, not natural-workflow recognition rates.",
            "The positive and corrected twin share one small ordered p-value family.",
            "Storey q-values, weighted procedures, hierarchical testing, dependence corrections, and adaptive families are outside this control family.",
            "A later detector must still prove exact table binding and complete-family authority before any adverse output.",
        ],
        "oracle_ref": "ORACLE.json",
    }
    _write_json_once(output / "CONTROL_SPEC.json", specification)
    _write_once(
        output / "README.md",
        (
            b"# Multiple-testing BH control family v1\n\n"
            b"This no-replace evaluator-owned family freezes a positive, corrected twin, hard "
            b"negative, and ambiguous case before production detector implementation. Labels and "
            b"the independent exact-decimal oracle remain outside each audit workspace. The family "
            b"does not qualify a detector or grant Finding authority.\n"
        ),
    )
    inventory = _inventory(output)
    manifest = {
        "control_family_id": FAMILY_ID,
        "frozen_at": frozen_at,
        "inventory": inventory,
        "inventory_digest": semantic_digest(inventory),
    }
    _write_json_once(output / "MANIFEST.json", manifest)
    return manifest


def _rows(
    raw: tuple[str, ...],
    adjusted: tuple[str, ...],
    significant: tuple[bool, ...],
) -> tuple[dict[str, str], ...]:
    if not (len(raw) == len(adjusted) == len(significant)):
        raise ValueError("Control columns must have identical lengths.")
    return tuple(
        {
            "test_id": f"gene_{index:02d}",
            "p_value": p_value,
            "adjusted_p_value": adjusted_value,
            "significant": "true" if called else "false",
        }
        for index, (p_value, adjusted_value, called) in enumerate(
            zip(raw, adjusted, significant, strict=True), start=1
        )
    )


def _csv_bytes(rows: object) -> bytes:
    if not isinstance(rows, tuple):
        raise TypeError("Control rows must be immutable tuples.")
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(
        handle,
        fieldnames=("test_id", "p_value", "adjusted_p_value", "significant"),
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8")


def _decimal_text(value: Decimal) -> str:
    text = format(value, "f").rstrip("0").rstrip(".")
    return text or "0"


def _write_json_once(path: Path, value: dict[str, Any]) -> None:
    _write_once(path, (canonical_json(value) + "\n").encode("utf-8"))


def _write_once(path: Path, payload: bytes) -> None:
    atomic_create_bytes(path, payload)


def _inventory(output: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(output).as_posix(),
            "content_digest": sha256_digest(path.read_bytes()),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "MANIFEST.json"
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the frozen multiple-testing control family."
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frozen-at", default=FROZEN_AT)
    arguments = parser.parse_args()
    result = build_multiple_testing_control_family(
        arguments.output.resolve(), frozen_at=arguments.frozen_at
    )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
