from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from sc_referee.calculation_checks.core import CalculationCheckRegistry
from sc_referee.calculation_checks.profiles import (
    compressed_calculation_check_registry,
    default_calculation_check_registry,
    sequence_boundary_calculation_check_registry,
    sequence_boundary_calculation_release_projection,
    verify_sequence_boundary_calculation_release_manifest,
)
from sc_referee.calculation_checks.sequence_record_boundary import (
    SEQUENCE_RECORD_BOUNDARY_CHECK_ID,
    sequence_record_boundary_registry,
)
from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json

SEQUENCE = "ACDEFGHIKLMNPQRSTVWY" * 3
LABEL = "Example target protein-1"


def _write_workspace(
    root: Path,
    *,
    source: str,
    record: str = f"{SEQUENCE}\n{LABEL}\n",
    record_path: str = "target-record.txt",
) -> None:
    root.mkdir()
    (root / "report.md").write_text("# Selected analysis\n", encoding="utf-8")
    selected_record = root / record_path
    selected_record.parent.mkdir(parents=True, exist_ok=True)
    selected_record.write_text(record, encoding="utf-8")
    (root / "analysis.py").write_text(source, encoding="utf-8")


def _unsafe_source(*, record_path: str = "target-record.txt") -> str:
    return f'''from pathlib import Path

record_path = Path("{record_path}")
lines = record_path.read_text(encoding="utf-8").splitlines()
sequence = "".join(
    line.strip()
    for line in lines
    if line.strip() and not line.lstrip().startswith(">")
)
'''


def _audit(
    workspace: Path,
    output: Path,
    schema_root: Path,
    *,
    record_path: str = "target-record.txt",
) -> dict[str, object]:
    return run_audit(
        workspace,
        output,
        schema_root,
        report="report.md",
        material_inputs=(record_path, "analysis.py"),
        calculation_check_registry=sequence_record_boundary_registry(),
    )


def _sequence_observation(bundle: dict[str, object]) -> dict[str, object]:
    observations = bundle["deterministic_check_observations"]
    assert isinstance(observations, list)
    return next(
        item
        for item in observations
        if item["check_manifest"]["check_id"] == SEQUENCE_RECORD_BOUNDARY_CHECK_ID
    )


def _operand(observation: dict[str, object], name: str) -> object:
    operands = observation["operands"]
    assert isinstance(operands, list)
    return next(item["value"] for item in operands if item["name"] == name)


def test_selected_nonsequence_record_line_is_disclosed_without_finding_and_replays(
    schema_root: Path, tmp_path: Path
) -> None:
    workspace = tmp_path / "positive"
    _write_workspace(workspace, source=_unsafe_source())

    output = tmp_path / "audit"
    bundle = _audit(workspace, output, schema_root)
    observation = _sequence_observation(bundle)

    assert observation["applicability"] == "applicable"
    assert observation["comparison"]["outcome"] == "nonconformant"
    assert observation["output_ceiling"] == "disclosure_only"
    assert observation["production_finding_permitted"] is False
    assert _operand(observation, "record_path") == "target-record.txt"
    assert _operand(observation, "record_line_count") == 2
    assert _operand(observation, "sequence_line_length") == len(SEQUENCE)
    assert _operand(observation, "non_sequence_line") == LABEL
    assert bundle["findings"] == []
    assert any(
        item["title"] == "Selected parser includes a non-sequence record line"
        for item in bundle["disclosures"]
    )

    lock = json.loads((output / "semantic.lock.json").read_text(encoding="utf-8"))
    assert lock["model_calls"] == []
    assert lock["model_access_after_lock"] is False
    replayed = replay(output / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in (
        "deterministic_check_observations",
        "disclosures",
        "findings",
        "coverage_records",
    ):
        assert replayed[field] == bundle[field]


def test_corrected_first_line_selection_does_not_produce_boundary_observation(
    schema_root: Path, tmp_path: Path
) -> None:
    workspace = tmp_path / "corrected"
    _write_workspace(
        workspace,
        source="""from pathlib import Path

record_path = Path("target-record.txt")
lines = record_path.read_text(encoding="utf-8").splitlines()
sequence = lines[0].strip().upper()
label = lines[1].strip()
""",
    )

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    assert bundle["deterministic_check_observations"] == []
    assert bundle["findings"] == []


def test_fresh_corrected_two_line_parser_is_false_positive_control(
    schema_root: Path, tmp_path: Path
) -> None:
    workspace = tmp_path / "fresh-corrected-control"
    _write_workspace(
        workspace,
        source="""from pathlib import Path

def load_target(path: Path) -> tuple[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) != 2:
        raise ValueError("expected one value line and one label line")
    sequence = lines[0].strip().upper()
    label = lines[1].strip()
    return label, sequence

target_name, target_sequence = load_target(Path("target-record.txt"))
""",
    )

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    assert bundle["deterministic_check_observations"] == []
    assert bundle["material_questions"] == []
    assert bundle["findings"] == []
    assert bundle["executions"] == []


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            """from argparse import ArgumentParser
from pathlib import Path

def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "--target-record",
        type=Path,
        default=Path("inputs/target-record.txt"),
    )
    return parser.parse_args()

def load_sequence(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    return "".join(line.strip() for line in lines if line.strip())

def main() -> str:
    args = parse_args()
    return load_sequence(args.target_record)
""",
            id="single-call-argparse-default",
        ),
        pytest.param(
            """from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Inputs:
    target_record: Path

def resolve_inputs(root: Path) -> Inputs:
    return Inputs(target_record=root / "target-record.txt")

def load_sequence(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    return "".join(line.strip() for line in lines if line.strip())

def main() -> str:
    inputs = resolve_inputs(Path("inputs"))
    return load_sequence(inputs.target_record)
""",
            id="single-call-constructor-field",
        ),
    ],
)
def test_single_call_path_bindings_remain_exact_and_nonexecuting(
    schema_root: Path,
    tmp_path: Path,
    source: str,
) -> None:
    workspace = tmp_path / "single-call"
    record_path = "inputs/target-record.txt"
    _write_workspace(workspace, source=source, record_path=record_path)

    bundle = _audit(
        workspace,
        tmp_path / "audit",
        schema_root,
        record_path=record_path,
    )

    observation = _sequence_observation(bundle)
    assert observation["comparison"]["outcome"] == "nonconformant"
    assert _operand(observation, "record_path") == record_path
    assert bundle["executions"] == []
    assert bundle["findings"] == []


@pytest.mark.parametrize(
    ("record", "source"),
    [
        pytest.param(
            f"{SEQUENCE}\n{SEQUENCE}\n",
            _unsafe_source(),
            id="second-line-is-sequence-alphabet",
        ),
        pytest.param(
            f"{SEQUENCE}\n>Example target protein-1\n",
            _unsafe_source(),
            id="second-line-is-fasta-header",
        ),
        pytest.param(
            f"{SEQUENCE}\n{LABEL}\n",
            _unsafe_source(record_path="other-record.txt"),
            id="selected-record-identity-not-bound",
        ),
        pytest.param(
            f"{SEQUENCE}\n{LABEL}\n",
            """from pathlib import Path

selected_record = Path("target-record.txt")
other_record = Path("other-record.txt")
lines = other_record.read_text(encoding="utf-8").splitlines()
sequence = "".join(line.strip() for line in lines if line.strip())
""",
            id="selected-record-literal-does-not-bind-other-reader",
        ),
        pytest.param(
            f"{SEQUENCE}\n{LABEL}\n",
            """from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class SelectedConfig:
    target_record: Path

@dataclass(frozen=True)
class RuntimeConfig:
    target_record: Path

def runtime_config() -> RuntimeConfig:
    return RuntimeConfig(Path("other-record.txt"))

def load_sequence(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    return "".join(line.strip() for line in lines if line.strip())

selected = SelectedConfig(target_record=Path("target-record.txt"))
runtime = runtime_config()
sequence = load_sequence(runtime.target_record)
""",
            id="same-named-unrelated-constructor-field-does-not-bind-reader",
        ),
        pytest.param(
            f"{SEQUENCE}\n{LABEL}\n",
            """from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Inputs:
    target_record: Path

def resolve_inputs(root: Path) -> Inputs:
    return Inputs(target_record=root / "target-record.txt")

def load_sequence(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    return "".join(line.strip() for line in lines if line.strip())

inputs = resolve_inputs(Path("other"))
sequence = load_sequence(inputs.target_record)
""",
            id="constructor-parent-directory-must-match-selected-record",
        ),
        pytest.param(
            f"{SEQUENCE}\n{LABEL}\n",
            """from argparse import ArgumentParser
from pathlib import Path

def runtime_config():
    return object()

def config():
    parser = ArgumentParser()
    parser.add_argument("--target-record", default=Path("target-record.txt"))
    return runtime_config()

args = config()
lines = args.target_record.read_text(encoding="utf-8").splitlines()
sequence = "".join(line.strip() for line in lines if line.strip())
""",
            id="unreturned-argparse-default-does-not-bind-runtime-object",
        ),
        pytest.param(
            f"{SEQUENCE}\n{LABEL}\n",
            """from pathlib import Path

record_path = Path("other-record.txt")
lines = record_path.read_text(encoding="utf-8").splitlines()
sequence = "".join(line.strip() for line in lines if line.strip())
record_path = Path("target-record.txt")
""",
            id="reassigned-path-name-is-not-a-stable-binding",
        ),
        pytest.param(
            f"{SEQUENCE}\n{LABEL}\n",
            """from pathlib import Path

record_path = Path("target-record.txt")
lines = record_path.read_text(encoding="utf-8").splitlines()
sequence = "".join(line.strip() for line in lines if line.strip() and line.isalpha())
""",
            id="additional-line-validation-is-outside-adverse-grammar",
        ),
    ],
)
def test_finite_counterevidence_controls_suppress_boundary_conclusion(
    schema_root: Path,
    tmp_path: Path,
    record: str,
    source: str,
) -> None:
    workspace = tmp_path / "counterevidence"
    _write_workspace(workspace, source=source, record=record)

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    assert bundle["deterministic_check_observations"] == []
    assert bundle["findings"] == []


def test_multiple_candidate_consumers_remain_ambiguous(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "ambiguous"
    _write_workspace(workspace, source=_unsafe_source())
    (workspace / "alternate.py").write_text(_unsafe_source(), encoding="utf-8")

    bundle = run_audit(
        workspace,
        tmp_path / "audit",
        schema_root,
        report="report.md",
        material_inputs=("target-record.txt", "analysis.py", "alternate.py"),
        calculation_check_registry=sequence_record_boundary_registry(),
    )
    observation = _sequence_observation(bundle)

    assert observation["applicability"] == "ambiguous"
    assert observation["comparison"]["outcome"] == "unknown"
    assert observation["operands"] == []
    assert bundle["findings"] == []


def test_unparseable_selected_python_is_localized_as_unsupported(
    schema_root: Path, tmp_path: Path
) -> None:
    workspace = tmp_path / "unsupported"
    _write_workspace(
        workspace,
        source='record_path = "target-record.txt"\nif invalid python\n',
    )

    bundle = _audit(workspace, tmp_path / "audit", schema_root)
    observation = _sequence_observation(bundle)

    assert observation["applicability"] == "unsupported"
    assert observation["comparison"]["outcome"] == "unknown"
    assert observation["operands"] == []
    assert bundle["findings"] == []


def test_project_source_is_never_executed(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "no-execution"
    sentinel = workspace / "executed.txt"
    _write_workspace(
        workspace,
        source=(
            _unsafe_source()
            + '\nPath("executed.txt").write_text("project code ran", encoding="utf-8")\n'
        ),
    )

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    assert _sequence_observation(bundle)["comparison"]["outcome"] == "nonconformant"
    assert not sentinel.exists()
    assert bundle["executions"] == []
    assert bundle["findings"] == []


def test_sequence_module_removal_preserves_sibling_calculation_observation(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    source = (
        project_root
        / "evaluation"
        / "development-controls"
        / "multiple-testing-bh-v1"
        / "cases"
        / "multiple-testing-positive"
        / "workspace"
    )
    workspace = tmp_path / "sibling"
    shutil.copytree(source, workspace)
    (workspace / "target-record.txt").write_text(f"{SEQUENCE}\n{LABEL}\n", encoding="utf-8")
    (workspace / "analysis.py").write_text(_unsafe_source(), encoding="utf-8")

    current = run_audit(
        workspace,
        tmp_path / "current-audit",
        schema_root,
        report="report.md",
        material_inputs=("target-record.txt", "analysis.py"),
        calculation_check_registry=sequence_boundary_calculation_check_registry(),
    )
    removed = run_audit(
        workspace,
        tmp_path / "removed-audit",
        schema_root,
        report="report.md",
        material_inputs=("target-record.txt", "analysis.py"),
        calculation_check_registry=compressed_calculation_check_registry(),
    )

    current_siblings = [
        item
        for item in current["deterministic_check_observations"]
        if item["check_manifest"]["check_id"] != SEQUENCE_RECORD_BOUNDARY_CHECK_ID
    ]
    assert len(current_siblings) == 1
    assert current_siblings[0]["check_manifest"]["check_id"] == (
        "calculation-check:benjamini-hochberg-complete-family-v1"
    )
    removed_sibling = removed["deterministic_check_observations"][0]
    for field in (
        "check_manifest",
        "adapter_manifest",
        "applicability",
        "comparison",
        "operands",
        "receipts",
        "limitations",
        "output_ceiling",
        "production_finding_permitted",
    ):
        assert current_siblings[0][field] == removed_sibling[field]
    assert current["findings"] == removed["findings"] == []


def test_empty_registry_removes_sequence_observation(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "removed"
    _write_workspace(workspace, source=_unsafe_source())

    bundle = run_audit(
        workspace,
        tmp_path / "audit",
        schema_root,
        report="report.md",
        material_inputs=("target-record.txt", "analysis.py"),
        calculation_check_registry=CalculationCheckRegistry((), profile_id="empty"),
    )

    assert bundle["deterministic_check_observations"] == []
    assert bundle["findings"] == []


def test_adapter_identity_is_not_benchmark_specific(project_root: Path) -> None:
    source = (
        (project_root / "src" / "sc_referee" / "calculation_checks" / "sequence_record_boundary.py")
        .read_text(encoding="utf-8")
        .casefold()
    )

    assert "scienceagentbench" not in source
    assert "covid" not in source
    assert "drug" not in source


def test_v12_release_manifest_is_canonical_complete_and_current(project_root: Path) -> None:
    manifest_path = (
        project_root
        / "src"
        / "sc_referee"
        / "resources"
        / "calculation-check-manifests-v12"
        / "registry.json"
    )
    payload = manifest_path.read_bytes()
    expected = json.loads(payload)
    registry = sequence_boundary_calculation_check_registry()

    assert canonical_json(expected).encode("utf-8") == payload.rstrip(b"\n")
    assert expected == sequence_boundary_calculation_release_projection(registry)
    assert expected["manifest_set_id"] == (
        "calculation-check-manifest-set:v12-selected-sequence-record-boundary"
    )
    assert expected["profile_id"] == "deterministic_calculation_check_v12"
    assert len(expected["modules"]) == 9
    assert expected["production_finding_permitted"] is False
    verify_sequence_boundary_calculation_release_manifest(registry)


def test_default_registry_uses_v12_disclosure_only_profile() -> None:
    registry = default_calculation_check_registry()
    sequence_module = next(
        module
        for module in registry.modules
        if module.manifest.check_id == SEQUENCE_RECORD_BOUNDARY_CHECK_ID
    )

    assert registry.profile_id == "deterministic_calculation_check_v12"
    assert len(registry.modules) == 9
    assert sequence_module.manifest.output_ceiling == "disclosure_only"
