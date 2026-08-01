from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
EVALUATION_SRC = ROOT / "evaluation" / "src"
sys.path[:0] = [str(SRC), str(EVALUATION_SRC)]

from sc_referee_evaluation.regression_baseline import (  # noqa: E402
    validate_regression_module_baselines,
)
from sc_referee_evaluation.regression_corpus import (  # noqa: E402
    DEFAULT_REGRESSION_CORPUS_LEDGER,
    validate_regression_corpus_ledger,
)


def main() -> int:
    ledger = validate_regression_corpus_ledger(
        DEFAULT_REGRESSION_CORPUS_LEDGER,
        project_root=ROOT,
    )
    baseline = validate_regression_module_baselines(ledger)
    print(
        "Validated regression corpus ledger: "
        f"{len(ledger['component_inventory'])} components, "
        f"{len(ledger['sources'])} sources, {len(ledger['cases'])} cases; "
        f"all {len(baseline['modules'])} module baselines complete; "
        "qualification use forbidden."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
