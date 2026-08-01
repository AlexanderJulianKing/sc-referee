from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.adapter_common import adapter_implementation_digest
from sc_referee.scientific_checks.python_founder_adapter import (
    PYTHON_FOUNDER_ADAPTER_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.rmarkdown_mvmr_adapter import (
    RMARKDOWN_MVMR_ADAPTER_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.selected_report_adapter import (
    SELECTED_REPORT_ADAPTER_IMPLEMENTATION_DIGEST,
)


def test_adapter_implementation_identities_are_isolated(tmp_path: Path) -> None:
    package = Path(__file__).resolve().parents[1] / "src" / "sc_referee" / "scientific_checks"
    founder_path = package / "python_founder_adapter.py"
    rmarkdown_path = package / "rmarkdown_mvmr_adapter.py"
    report_path = package / "selected_report_adapter.py"

    assert PYTHON_FOUNDER_ADAPTER_IMPLEMENTATION_DIGEST == sha256_digest(founder_path.read_bytes())
    assert RMARKDOWN_MVMR_ADAPTER_IMPLEMENTATION_DIGEST == adapter_implementation_digest(
        rmarkdown_path
    )
    assert SELECTED_REPORT_ADAPTER_IMPLEMENTATION_DIGEST == adapter_implementation_digest(
        report_path
    )
    assert (
        len(
            {
                PYTHON_FOUNDER_ADAPTER_IMPLEMENTATION_DIGEST,
                RMARKDOWN_MVMR_ADAPTER_IMPLEMENTATION_DIGEST,
                SELECTED_REPORT_ADAPTER_IMPLEMENTATION_DIGEST,
            }
        )
        == 3
    )

    mutated_report = tmp_path / "selected_report_adapter.py"
    mutated_report.write_bytes(report_path.read_bytes() + b"\n# isolated test mutation\n")

    assert adapter_implementation_digest(mutated_report) != (
        SELECTED_REPORT_ADAPTER_IMPLEMENTATION_DIGEST
    )
    assert sha256_digest(founder_path.read_bytes()) == (
        PYTHON_FOUNDER_ADAPTER_IMPLEMENTATION_DIGEST
    )
    assert adapter_implementation_digest(rmarkdown_path) == (
        RMARKDOWN_MVMR_ADAPTER_IMPLEMENTATION_DIGEST
    )
