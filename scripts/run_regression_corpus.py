from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
EVALUATION_SRC = ROOT / "evaluation" / "src"
sys.path[:0] = [str(SRC), str(EVALUATION_SRC)]

from sc_referee_evaluation.regression_runner import (  # noqa: E402
    DEFAULT_REGRESSION_CORPUS_EXECUTION_PLAN,
    run_regression_corpus,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the answer-side, non-qualifying sc-referee regression corpus without "
            "executing retained target-project code."
        )
    )
    parser.add_argument(
        "--plan",
        type=Path,
        default=DEFAULT_REGRESSION_CORPUS_EXECUTION_PLAN,
        help="Canonical execution plan relative to the project root.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional create-once canonical JSON receipt path.",
    )
    arguments = parser.parse_args()
    receipt = run_regression_corpus(
        project_root=ROOT,
        plan_path=arguments.plan,
        output=arguments.output,
    )
    print(
        "Regression corpus passed: "
        f"{receipt['pytest_case_count']} ledger pytest cases through "
        f"{receipt['pytest_selector_count']} selectors; "
        f"{receipt['audit_replay_case_count']} direct audits replayed exactly; "
        "zero target-code execution, Findings, or model calls."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
