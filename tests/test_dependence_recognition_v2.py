"""Adversarial tests for the unregistered dependence growth-1 shadow."""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from sc_referee_evaluation import lean_pipeline as evaluation_pipeline

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition.python_analyzer import _trusted_authorizations
from sc_referee.dependence_recognition_v2.adapter import DependenceRecognitionV2ShadowAdapter
from sc_referee.dependence_recognition_v2.certificate import (
    verify_dependence_growth_certificate,
)
from sc_referee.dependence_recognition_v2.ir import (
    DEPENDENCE_V2_KERNEL_REFUSAL_OBLIGATIONS,
    DEPENDENCE_V2_REASON_REGISTRY,
)
from sc_referee.dependence_recognition_v2.python_analyzer import (
    analyze_dependence_growth_python,
    discharge_dependence_growth_analysis,
)
from sc_referee.detectors.method_conflict_grant_pins import (
    GRANT_PINS,
    installed_pin_matches_live_identity,
)
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    InspectionDocument,
    RecordRef,
)
from scripts.lean_pipeline import (
    default_dependence_free_b_config,
    default_dependence_free_config,
)

_DATA = "inputs/data.csv"
_RUNTIME = Path(
    os.environ.get(
        "SC_REFEREE_DEPENDENCE_V2_SANDBOX_PYTHON",
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime/"
        "scipy114-venv/bin/python",
    )
)


def _require_runtime() -> Path:
    if not _RUNTIME.is_file():
        pytest.fail(
            "dependence v2 runtime-differential coverage requires "
            f"SC_REFEREE_DEPENDENCE_V2_SANDBOX_PYTHON={_RUNTIME}"
        )
    return _RUNTIME


def _source(*, encoding: str = "ascii", group_key: str = "arm", value: str = "value") -> str:
    return f'''import csv
from pathlib import Path
from scipy import stats

INPUT = Path("inputs/data.csv")
LEFT = "A"
RIGHT = "B"
REPORT = Path("results/report.md")

def main():
    with INPUT.open(newline="", encoding="{encoding}") as handle:
        rows = list(csv.DictReader(handle))
    groups = {{}}
    for row in rows:
        groups.setdefault(row["{group_key}"], []).append(float(row["{value}"]))
    left = groups[LEFT]
    right = groups[RIGHT]
    result = stats.ttest_ind(left, right)
    REPORT.write_text(str(result), encoding="utf-8")

main()
'''


def _context(
    source: str,
    data: bytes,
    *,
    unit_column: str = "unit_id",
    authority: bool = True,
    data_path: str = _DATA,
) -> FrozenInspectionContext:
    surface = RecordRef("publication_surface", "surface:v2")
    artifact = RecordRef("artifact", "artifact:v2-report")
    snapshot = RecordRef("repository_snapshot", "snapshot:v2")
    source_file = RecordRef("file_record", "file:v2-source")
    parser = RecordRef("parser_result", "parser:v2-source")
    data_file = RecordRef("file_record", "file:v2-data")
    data_identity = RecordRef("asset_identity", "asset:v2-data")
    requirements_file = RecordRef("file_record", "file:v2-requirements")
    requirements_identity = RecordRef("asset_identity", "asset:v2-requirements")
    analysis = RecordRef("analysis", "analysis:v2")
    procedure = RecordRef("procedure", "procedure:v2")
    result = RecordRef("result", "result:v2")
    data_digest = sha256_digest(data)
    requirements = b"scipy==1.14.0\n"
    requirements_digest = sha256_digest(requirements)
    parser_payload = canonical_json(
        {"parser_id": "python-ast", "parser_version": "3.11", "state": "parsed"}
    ).encode()
    source_bytes = source.encode()
    values: list[tuple[RecordRef, dict[str, object]]] = [
        (
            surface,
            {
                "publication_surface_id": surface.record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [artifact.to_dict()]},
            },
        ),
        (
            artifact,
            {"artifact_id": artifact.record_id, "kind": "report", "path": "results/report.md"},
        ),
        (
            snapshot,
            {
                "snapshot_id": snapshot.record_id,
                "extensions": {"x-material-full-digest-paths": [data_path, "requirements.txt"]},
            },
        ),
        (
            data_file,
            {
                "file_record_id": data_file.record_id,
                "path": data_path,
                "entry_kind": "regular_file",
                "asset_identity_ref": data_identity.to_dict(),
            },
        ),
        (
            data_identity,
            {
                "asset_identity_id": data_identity.record_id,
                "tier": "full_digest",
                "asset_ref": data_file.to_dict(),
                "identity_evidence": {"kind": "full_digest", "digest": data_digest},
            },
        ),
        (
            requirements_file,
            {
                "file_record_id": requirements_file.record_id,
                "path": "requirements.txt",
                "entry_kind": "regular_file",
                "asset_identity_ref": requirements_identity.to_dict(),
            },
        ),
        (
            requirements_identity,
            {
                "asset_identity_id": requirements_identity.record_id,
                "tier": "full_digest",
                "asset_ref": requirements_file.to_dict(),
                "identity_evidence": {
                    "kind": "full_digest",
                    "digest": requirements_digest,
                },
            },
        ),
        (source_file, {"file_record_id": source_file.record_id}),
        (parser, {"parser_result_id": parser.record_id}),
        (analysis, {"analysis_id": analysis.record_id}),
        (procedure, {"procedure_id": procedure.record_id}),
        (result, {"result_id": result.record_id, "path": "results/report.md"}),
    ]
    if authority:
        values.append(
            (
                RecordRef("human_method_authorization", "authorization-v2:test"),
                {
                    "record_type": "human_method_authorization",
                    "record_id": "authorization-v2:test",
                    "actor_id": "human:method-owner",
                    "authority_state": "authorized",
                    "analysis_target_ref": analysis.to_dict(),
                    "procedure_ref": procedure.to_dict(),
                    "independent_unit_definition_id": "unit-definition:v2",
                    "authorized_key_columns": [unit_column],
                    "input_path": data_path,
                    "input_content_digest": data_digest,
                },
            )
        )
    return FrozenInspectionContext(
        snapshot_digest=sha256_digest(b"v2-snapshot"),
        selected_surface_ref=surface,
        selected_artifact_ref=artifact,
        documents=(
            InspectionDocument(
                path="workflow/analysis.py",
                file_ref=source_file,
                content=source_bytes,
                content_digest=sha256_digest(source_bytes),
                media_type="text/x-python",
                parser_result_ref=parser,
                parser_result_payload=parser_payload,
                parser_result_digest=sha256_digest(parser_payload),
            ),
        ),
        base_records=tuple(FrozenBaseRecord.from_record(ref, value) for ref, value in values),
        material_inputs=(
            FrozenMaterialInput(
                path=data_path,
                file_ref=data_file,
                asset_identity_ref=data_identity,
                content=data,
                content_digest=data_digest,
            ),
            FrozenMaterialInput(
                path="requirements.txt",
                file_ref=requirements_file,
                asset_identity_ref=requirements_identity,
                content=requirements,
                content_digest=requirements_digest,
            ),
        ),
    )


_ADVERSE = b"unit_id,arm,value\nu1,A,1\nu1,A,2\nu2,B,3\nu3,B,4\n"
_COVERED = b"unit_id,arm,value\nu1,A,1\nu2,A,2\nu3,B,3\nu4,B,4\n"


@pytest.mark.parametrize(
    ("data", "payload_type", "outcome"),
    [
        (_ADVERSE, "shadow_candidate", "evaluation_candidate"),
        (_COVERED, "coverage_note", "covered_negative"),
    ],
)
def test_positive_function_and_transform_fixtures_certify(
    data: bytes, payload_type: str, outcome: str, tmp_path: Path
) -> None:
    source = _source()
    case = tmp_path / "case"
    (case / "inputs").mkdir(parents=True)
    (case / "workflow").mkdir()
    (case / "results").mkdir()
    (case / "inputs/data.csv").write_bytes(data)
    (case / "workflow/analysis.py").write_text(source, encoding="ascii")
    completed = subprocess.run(
        [str(_require_runtime()), "-I", "workflow/analysis.py"],
        cwd=case,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode()
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(source, data))
    assert payload["payload_type"] == payload_type
    assert payload["outcome"] == outcome


def test_paired_crossover_abstains_when_unit_spans_operands() -> None:
    data = b"unit_id,arm,value\nu1,A,1\nu1,B,2\nu2,A,3\nu2,B,4\n"
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(_source(), data))
    assert payload["payload_type"] == "abstention"
    assert payload["abstention_reasons"] == ["unit-spans-multiple-operands"]


@pytest.mark.parametrize(
    ("source", "data", "unit", "reason"),
    [
        (
            _source().replace(
                'groups.setdefault(row["arm"], []).append(float(row["value"]))',
                'groups.setdefault(row["arm"], set()).add(float(row["value"]))',
            ),
            _ADVERSE,
            "unit_id",
            "group-container-not-list",
        ),
        (
            _source().replace(
                'groups.setdefault(row["arm"], []).append(float(row["value"]))',
                'groups[row["arm"]] = [float(row["value"])]',
            ),
            _ADVERSE,
            "unit_id",
            "group-accumulator-not-total",
        ),
        (_source(), b"unit_id,arm,value\nu1,A,\nu2,B,2\n", "unit_id", "group-value-cast-unproven"),
        (
            _source(group_key="value", value="value"),
            _ADVERSE,
            "unit_id",
            "group-key-equals-value-column",
        ),
        (_source(group_key="unit_id"), _ADVERSE, "unit_id", "group-key-is-unit-column"),
        (_source(), b"unit_id,arm,arm\nu1,A,1\n", "unit_id", "duplicate-header"),
        (_source(), b"unit_id,arm,value\nu1,A,1,extra\n", "unit_id", "ragged-row"),
        (
            _source(encoding="ascii"),
            "unit_id,arm,value\nu1,A,é\n".encode(),
            "unit_id",
            "reader-bytes-not-ascii",
        ),
    ],
)
def test_named_structural_and_domain_abstentions(
    source: str, data: bytes, unit: str, reason: str
) -> None:
    payload = DependenceRecognitionV2ShadowAdapter().inspect(
        _context(source, data, unit_column=unit)
    )
    assert reason in payload["abstention_reasons"]


def test_named_abstention_probes_are_actually_invoked_in_the_sandbox(tmp_path: Path) -> None:
    probes = {
        "paired": (_source(), b"unit_id,arm,value\nu1,A,1\nu1,B,2\nu2,A,3\nu2,B,4\n"),
        "set-bucket": (
            _source().replace(
                'groups.setdefault(row["arm"], []).append(float(row["value"]))',
                'groups.setdefault(row["arm"], set()).add(float(row["value"]))',
            ),
            _ADVERSE,
        ),
        "dict-overwrite": (
            _source().replace(
                'groups.setdefault(row["arm"], []).append(float(row["value"]))',
                'groups[row["arm"]] = [float(row["value"])]',
            ),
            _ADVERSE,
        ),
        "empty-float": (_source(), b"unit_id,arm,value\nu1,A,\nu2,B,2\n"),
        "non-ascii-ascii-reader": (
            _source(),
            "unit_id,arm,value\nu1,A,é\nu2,B,2\n".encode(),
        ),
    }
    observed_exit_states: dict[str, bool] = {}
    for name, (source, data) in probes.items():
        case = tmp_path / name
        (case / "inputs").mkdir(parents=True)
        (case / "workflow").mkdir()
        (case / "results").mkdir()
        (case / "inputs/data.csv").write_bytes(data)
        (case / "workflow/analysis.py").write_text(source, encoding="ascii")
        completed = subprocess.run(
            [str(_require_runtime()), "-I", "workflow/analysis.py"],
            cwd=case,
            capture_output=True,
            check=False,
        )
        observed_exit_states[name] = completed.returncode == 0
    assert observed_exit_states == {
        "paired": True,
        "set-bucket": False,
        "dict-overwrite": True,
        "empty-float": False,
        "non-ascii-ascii-reader": False,
    }


def test_predeclared_bucket_closure_and_three_group_arity() -> None:
    source = (
        _source()
        .replace("groups = {}", 'groups = {"A": [], "B": []}')
        .replace(
            'groups.setdefault(row["arm"], []).append(float(row["value"]))',
            'groups[row["arm"]].append(float(row["value"]))',
        )
    )
    unexpected = b"unit_id,arm,value\nu1,A,1\nu2,C,2\n"
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(source, unexpected))
    assert payload["abstention_reasons"] == ["group-set-not-closed"]
    three = b"unit_id,arm,value\nu1,A,1\nu2,B,2\nu3,C,3\n"
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(_source(), three))
    assert payload["abstention_reasons"] == ["group-operand-arity-mismatch"]


def test_split_group_operand_and_bucket_reasons_are_granular() -> None:
    aliased = _source().replace(
        "    left = groups[LEFT]\n    right = groups[RIGHT]",
        "    buckets = groups\n    left = buckets[LEFT]\n    right = buckets[RIGHT]",
    )
    assert DependenceRecognitionV2ShadowAdapter().inspect(_context(aliased, _ADVERSE))[
        "abstention_reasons"
    ] == ["group-container-aliased"]

    sliced = _source().replace("left = groups[LEFT]", "left = groups[LEFT][:]")
    assert DependenceRecognitionV2ShadowAdapter().inspect(_context(sliced, _ADVERSE))[
        "abstention_reasons"
    ] == ["group-operand-sliced"]

    empty_bucket = (
        _source()
        .replace("groups = {}", 'groups = {"A": [], "B": [], "C": []}')
        .replace(
            'groups.setdefault(row["arm"], []).append(float(row["value"]))',
            'groups[row["arm"]].append(float(row["value"]))',
        )
    )
    assert DependenceRecognitionV2ShadowAdapter().inspect(_context(empty_bucket, _ADVERSE))[
        "abstention_reasons"
    ] == ["group-bucket-unpopulated"]


def test_empty_unit_or_group_cell_is_not_reported_as_cast_failure() -> None:
    for data in (
        b"unit_id,arm,value\n,A,1\nu2,B,2\n",
        b"unit_id,arm,value\nu1,,1\nu2,B,2\n",
    ):
        payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(_source(), data))
        assert payload["abstention_reasons"] == ["group-key-or-unit-cell-empty"]


def test_two_group_sorted_tuple_binding_and_numpy_wrappers_certify() -> None:
    tuple_source = _source().replace(
        "    left = groups[LEFT]\n    right = groups[RIGHT]",
        "    (_, left), (_, right) = sorted(groups.items())",
    )
    assert (
        DependenceRecognitionV2ShadowAdapter().inspect(_context(tuple_source, _ADVERSE))["outcome"]
        == "evaluation_candidate"
    )
    for wrapper in ("array", "asarray"):
        wrapped = (
            _source()
            .replace("import csv", "import csv\nimport numpy as np")
            .replace(
                "stats.ttest_ind(left, right)",
                f"stats.ttest_ind(np.{wrapper}(groups[LEFT], dtype=float), "
                f"np.{wrapper}(groups[RIGHT]))",
            )
        )
        assert (
            DependenceRecognitionV2ShadowAdapter().inspect(_context(wrapped, _ADVERSE))["outcome"]
            == "evaluation_candidate"
        )


def test_main_guard_pathlib_constant_and_direct_procedure_import_certify() -> None:
    source = (
        _source()
        .replace("from pathlib import Path", "import pathlib")
        .replace('Path("inputs/data.csv")', 'pathlib.Path("inputs/data.csv")')
        .replace('Path("results/report.md")', 'pathlib.Path("results/report.md")')
        .replace("from scipy import stats", "from scipy.stats import ttest_ind")
        .replace("stats.ttest_ind", "ttest_ind")
        .replace("\nmain()\n", '\nif __name__ == "__main__":\n    main()\n')
    )
    assert (
        DependenceRecognitionV2ShadowAdapter().inspect(_context(source, _ADVERSE))["outcome"]
        == "evaluation_candidate"
    )


def test_three_group_tuple_unpack_abstains_on_registered_arity() -> None:
    source = _source().replace(
        "    left = groups[LEFT]\n    right = groups[RIGHT]",
        "    (_, left), (_, right), (_, extra) = sorted(groups.items())",
    )
    data = b"unit_id,arm,value\nu1,A,1\nu2,B,2\nu3,C,3\n"
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(source, data))
    assert payload["abstention_reasons"] == ["group-operand-arity-mismatch"]


def test_final_with_return_dead_function_and_sink_helper_inline_and_certify() -> None:
    source = (
        _source()
        .replace('    REPORT.write_text(str(result), encoding="utf-8")', "    emit(result)")
        .replace(
            'def main():\n    with INPUT.open(newline="", encoding="ascii") as handle:\n        rows = list(csv.DictReader(handle))',
            """def load(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))

def emit(result):
    REPORT.write_text(str(result), encoding="utf-8")

def unused():
    return "provably dead"

def main():
    rows = load(INPUT)""",
        )
    )
    analysis = analyze_dependence_growth_python(_context(source, _ADVERSE))
    assert analysis.certificate is not None
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(source, _ADVERSE))
    assert payload["outcome"] == "evaluation_candidate"
    assert payload["abstention_reasons"] == []


def test_batch_a_rq1_rq3_are_executable_and_pin_full_sorted_wall_sets(
    project_root: Path, tmp_path: Path
) -> None:
    cases = {
        "rq1": (
            "6da5419523f5f9dbedf9",
            "jar_id",
            ["function-return-shape"],
        ),
        "rq3": (
            "d1d4ed0e518ad533a2dc",
            "tank_id",
            ["reader-form-unsupported"],
        ),
    }
    frozen_root = (
        project_root / "evaluation/development/dependence-growth-loop/batch-a/authoring/cases"
    )
    for role, (slug, unit_column, expected) in cases.items():
        frozen_case = frozen_root / slug
        execution_case = tmp_path / role
        shutil.copytree(frozen_case, execution_case)
        completed = subprocess.run(
            [str(_require_runtime()), "-I", "workflow/analysis.py"],
            cwd=execution_case,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr.decode()
        source = (frozen_case / "workflow/analysis.py").read_text(encoding="utf-8")
        data = (frozen_case / "data/input.csv").read_bytes()
        payload = DependenceRecognitionV2ShadowAdapter().inspect(
            _context(source, data, unit_column=unit_column, data_path="data/input.csv")
        )
        assert payload["abstention_reasons"] == expected


def test_kernel_rejects_length_binding_conclusion_and_source_mutations() -> None:
    context = _context(_source(), _ADVERSE)
    analysis = analyze_dependence_growth_python(context)
    discharged = discharge_dependence_growth_analysis(analysis, context)
    verified = discharged.verified_certificate
    assert verified is not None and analysis.certificate is not None
    fact = verified.fact
    certificate = replace(
        analysis.certificate,
        certificate_id=verified.certificate_id,
        operand_bindings=verified.operand_bindings,
        conclusion=verified.conclusion,
    )
    source_bytes = context.documents[0].content
    authorities = _trusted_authorizations(context)
    material = next(item for item in context.material_inputs if item.path == fact.path)
    assert (
        verify_dependence_growth_certificate(
            certificate,
            trusted_group_facts=(fact,),
            trusted_material_inputs=(material,),
            trusted_authorizations=authorities,
            source_bytes=source_bytes,
        )
        is not None
    )
    assert (
        verify_dependence_growth_certificate(
            certificate,
            trusted_group_facts=(fact,),
            trusted_material_inputs=(material,),
            trusted_authorizations=(replace(authorities[0], input_path="other.csv"),),
            source_bytes=source_bytes,
        )
        is None
    )
    failure_reasons: list[str] = []
    assert (
        verify_dependence_growth_certificate(
            certificate,
            trusted_group_facts=(fact,),
            trusted_material_inputs=(material,),
            trusted_authorizations=(replace(authorities[0], input_path="other.csv"),),
            source_bytes=source_bytes,
            _failure_reasons=failure_reasons,
        )
        is None
    )
    assert failure_reasons == ["authority-binding"]
    bad_sequence = replace(fact.groups[0], row_indices=fact.groups[0].row_indices[:-1])
    assert (
        verify_dependence_growth_certificate(
            certificate,
            trusted_group_facts=(replace(fact, groups=(bad_sequence, *fact.groups[1:])),),
            trusted_material_inputs=(material,),
            trusted_authorizations=authorities,
            source_bytes=source_bytes,
        )
        is None
    )
    assert (
        verify_dependence_growth_certificate(
            replace(certificate, conclusion="one_observation_per_unit"),
            trusted_group_facts=(fact,),
            trusted_material_inputs=(material,),
            trusted_authorizations=authorities,
            source_bytes=source_bytes,
        )
        is None
    )
    assert (
        verify_dependence_growth_certificate(
            certificate,
            trusted_group_facts=(fact,),
            trusted_material_inputs=(material,),
            trusted_authorizations=authorities,
            source_bytes=source_bytes + b"\n",
        )
        is None
    )
    mutated_source = source_bytes.replace(
        b"    result = stats.ttest_ind(left, right)",
        b"    left = right\n    result = stats.ttest_ind(left, right)",
    )
    mutated_digest = sha256_digest(mutated_source)
    mutated_certificate = replace(
        certificate,
        source_digest=mutated_digest,
        source_extent=(0, len(mutated_source)),
    )
    mutated_certificate = replace(
        mutated_certificate,
        certificate_id=(
            "dependence-growth-certificate:"
            + semantic_digest(
                {
                    "source_digest": mutated_digest,
                    "fact": fact.evidence_id,
                    "bindings": [
                        {
                            "position": item.position,
                            "argument_name": item.argument_name,
                            "group_key": item.group_key,
                        }
                        for item in certificate.operand_bindings
                    ],
                    "conclusion": certificate.conclusion,
                }
            )
        ),
    )
    assert (
        verify_dependence_growth_certificate(
            mutated_certificate,
            trusted_group_facts=(fact,),
            trusted_material_inputs=(material,),
            trusted_authorizations=authorities,
            source_bytes=mutated_source,
        )
        is None
    )


@pytest.mark.parametrize(
    ("insertion", "data"),
    [
        (
            "    rows = rows[:4]\n    groups = {}",
            b"unit_id,arm,value\nu1,A,1\nu2,A,2\nu3,B,3\nu4,B,4\nu1,A,5\n",
        ),
        ("    left = groups[LEFT]\n    left = [0.0]", _ADVERSE),
        ("    right = groups[RIGHT]\n    right = []", _ADVERSE),
        ("    rows = list(rows)\n    groups = {}", _ADVERSE),
    ],
)
def test_plain_operand_name_rebindings_abstain(
    insertion: str,
    data: bytes,
) -> None:
    source = _source()
    if insertion.startswith("    rows"):
        source = source.replace("    groups = {}", insertion)
    elif insertion.startswith("    left"):
        source = source.replace("    left = groups[LEFT]", insertion)
    else:
        source = source.replace("    right = groups[RIGHT]", insertion)
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(source, data))
    assert payload["abstention_reasons"] == ["operand-name-rebound"]


def test_kernel_independently_rejects_analyzer_bypass_certificate_with_rebind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source().replace(
        "    left = groups[LEFT]", "    left = groups[LEFT]\n    left = [0.0]"
    )
    monkeypatch.setattr(
        "sc_referee.dependence_recognition_v2.python_analyzer._rebound_operand_names",
        lambda _body, _operands: set(),
    )
    context = _context(source, _ADVERSE)
    proposal = analyze_dependence_growth_python(context)
    assert proposal.certificate is not None
    discharged = discharge_dependence_growth_analysis(proposal, context)
    assert discharged.verified_certificate is None
    assert discharged.abstention_reasons == ("certificate-kernel-refusal:source-semantic-replay",)


def test_discharger_surfaces_the_specific_kernel_obligation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context(_source(), _ADVERSE)
    analysis = analyze_dependence_growth_python(context)
    assert analysis.state == "proposal"

    def refuse(*_args: object, **kwargs: object) -> None:
        failure_reasons = kwargs["_failure_reasons"]
        assert isinstance(failure_reasons, list)
        failure_reasons.append("fact-closure")

    monkeypatch.setattr(
        "sc_referee.dependence_recognition_v2.python_analyzer.verify_dependence_growth_certificate",
        refuse,
    )
    discharged = discharge_dependence_growth_analysis(analysis, context)
    assert discharged.abstention_reasons == ("certificate-kernel-refusal:fact-closure",)


def test_function_and_import_granular_reasons() -> None:
    variants = {
        "function-argument-not-simple": _source()
        .replace("def main():", "def main(value):")
        .replace("\nmain()\n", "\nmain(str(1))\n"),
        "function-parameter-rebound": _source()
        .replace("def main():", "def main(value):\n    value = 2")
        .replace("\nmain()\n", "\nmain(1)\n"),
        "function-globals-read": _source().replace(
            "    with INPUT.open", "    print(DATA)\n    with INPUT.open"
        ),
        "import-name-collision": _source()
        .replace("def main():", "def main(csv):")
        .replace("\nmain()\n", "\nmain(1)\n"),
        "unsupported-import-form": _source().replace(
            "from scipy import stats", "import scipy.stats as stats"
        ),
    }
    for reason, source in variants.items():
        analysis = analyze_dependence_growth_python(_context(source, _ADVERSE))
        assert reason in analysis.abstention_reasons


@pytest.mark.parametrize(
    ("reason", "source"),
    [
        ("function-nonpositional-params", _source().replace("def main():", "def main(value, /):")),
        ("function-default-params", _source().replace("def main():", "def main(value=1):")),
        ("function-star-params", _source().replace("def main():", "def main(*values):")),
        (
            "function-recursive",
            _source().replace("def main():", "def main():\n    main()"),
        ),
        (
            "function-closure",
            _source().replace("def main():", "def main():\n    def nested():\n        return 1"),
        ),
        (
            "function-globals-write",
            _source().replace("def main():", "def main():\n    global INPUT"),
        ),
        (
            "function-return-shape",
            _source().replace("def main():", "def main():\n    return 1"),
        ),
        (
            "function-not-provably-dead",
            _source().replace(
                "def main():",
                "def helper():\n    return 1\n\ndef unused():\n    return helper()\n\ndef main():",
            ),
        ),
        (
            "function-inline-depth-exceeded",
            _source().replace(
                "def main():",
                "def h3():\n    return\n\ndef h2():\n    h3()\n\ndef h1():\n    h2()\n\ndef main():\n    h1()",
            ),
        ),
        (
            "sink-classification-unresolved",
            _source()
            .replace("import csv", "import csv\nimport math")
            .replace("def main():", "def main():\n    math.sqrt(4)"),
        ),
    ],
)
def test_all_function_wall_names_are_preserved(reason: str, source: str) -> None:
    analysis = analyze_dependence_growth_python(_context(source, _ADVERSE))
    assert reason in analysis.abstention_reasons


def test_bom_and_raw_string_operands_abstain() -> None:
    bom = DependenceRecognitionV2ShadowAdapter().inspect(
        _context(
            _source(encoding="utf-8"),
            b"\xef\xbb\xbfunit_id,arm,value\nu1,A,1\nu2,B,2\n",
        )
    )
    assert "bom-unsupported" in bom["abstention_reasons"]
    raw = _source().replace('float(row["value"])', 'row["value"]')
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(raw, _ADVERSE))
    assert payload["abstention_reasons"] == ["group-value-cast-absent"]
    string_cast = _source().replace('float(row["value"])', 'str(row["value"])')
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(string_cast, _ADVERSE))
    assert payload["abstention_reasons"] == ["group-value-cast-absent"]
    na = DependenceRecognitionV2ShadowAdapter().inspect(
        _context(_source(), b"unit_id,arm,value\nu1,A,NA\nu2,B,2\n")
    )
    assert na["abstention_reasons"] == ["group-value-cast-unproven"]
    integer_source = _source().replace('float(row["value"])', 'int(row["value"])')
    fractional = DependenceRecognitionV2ShadowAdapter().inspect(
        _context(integer_source, b"unit_id,arm,value\nu1,A,1.5\nu2,B,2\n")
    )
    assert fractional["abstention_reasons"] == ["group-value-cast-unproven"]


def test_live_mutation_outside_closed_basis_abstains_and_kernel_replays_it() -> None:
    source = _source().replace(
        "    result = stats.ttest_ind(left, right)",
        "    left = right\n    result = stats.ttest_ind(left, right)",
    )
    analysis = analyze_dependence_growth_python(_context(source, _ADVERSE))
    assert analysis.abstention_reasons == ("group-container-aliased",)


def test_development_hook_is_opt_in_and_cannot_be_enabled_for_production() -> None:
    config = default_dependence_free_config()
    assert config.dependence_v2_development_shadow is False
    payloads: list[dict[str, object]] = []
    observer = evaluation_pipeline._dependence_v2_observer(
        replace(config, dependence_v2_development_shadow=True), payloads
    )
    assert observer is not None
    observer(_context(_source(), _ADVERSE))
    assert [item["outcome"] for item in payloads] == ["evaluation_candidate"]
    with pytest.raises(
        evaluation_pipeline.LeanPipelineError,
        match="restricted to development-loop envelopes",
    ):
        evaluation_pipeline._dependence_v2_observer(
            replace(
                config,
                development_loop=False,
                dependence_v2_development_shadow=True,
            ),
            [],
        )


def test_batch_b_config_is_batch_a_with_only_fresh_seats_lane_and_v2_observer() -> None:
    batch_a = default_dependence_free_config()
    batch_b = default_dependence_free_b_config()
    assert batch_a.dependence_v2_development_shadow is False
    assert batch_b.dependence_v2_development_shadow is True
    assert batch_b.envelope_id == "development-dependence-growth-loop-batch-b-v1"
    assert str(batch_b.pipeline_relative).endswith("dependence-growth-loop/batch-b")
    assert sorted(batch_b.authors) == [
        f"actor:dependence-free-batch-b-author-opus-{ordinal}" for ordinal in range(33, 39)
    ]
    assert batch_b.reviewer.participant_id.endswith("reviewer-fable-18")
    assert batch_b.hostile_answer_key_reviewer is not None
    assert batch_b.hostile_answer_key_reviewer.participant_id.endswith("hostile-fable-19")
    assert batch_b.escalation_reviewer.participant_id.endswith("escalation-opus-14")
    ignored = {
        "envelope_id",
        "pipeline_relative",
        "authors",
        "author_roles",
        "reviewer",
        "hostile_answer_key_reviewer",
        "escalation_reviewer",
        "dependence_v2_development_shadow",
    }
    assert {key: value for key, value in batch_a.__dict__.items() if key not in ignored} == {
        key: value for key, value in batch_b.__dict__.items() if key not in ignored
    }


def test_v1_dependence_closure_is_byte_frozen(project_root: Path) -> None:
    expected = {
        "src/sc_referee/dependence_recognition/__init__.py": "sha256:818bee2ee623afae37fb4595c28c96592bbe49a9ce818204d611452beb740f32",
        "src/sc_referee/dependence_recognition/adapter.py": "sha256:6564eb97bee53576ef19a9dd38b54afd1a2a7855b40e586298a14223068d5c58",
        "src/sc_referee/dependence_recognition/authority_lock.py": "sha256:94a57302013629c3ecb64a92f3528c52e94da545a9e5ce743093982c2239471f",
        "src/sc_referee/dependence_recognition/certificate.py": "sha256:eacafce34cb9eb2ec4d578a36f01bf19fc24fdef3c2fb57c9f9afeec69355a50",
        "src/sc_referee/dependence_recognition/csv_domain.py": "sha256:23c4accf0b55b0bec93b58a1de3bd498dec19e857a47b1a68547f9d8541091d3",
        "src/sc_referee/dependence_recognition/ir.py": "sha256:afa035806b39c3cc2d8f70bbb4850eb75f295909a7d0127bb6a43deef43adc00",
        "src/sc_referee/dependence_recognition/python_analyzer.py": "sha256:55340b634c8ab10cd8bd34431361175cfe52a6966937b012fc0561df28df0355",
        "docs/implementation/EXPERIMENT-0058-DEPENDENCE-SEMANTIC-V1-SHADOW.md": "sha256:35bc4a39a69096965e403d1c66a4bc0185b9db7614cff3a813006cd6febf0884",
    }
    assert {
        path: sha256_digest((project_root / path).read_bytes()) for path in expected
    } == expected


def _production_import_closure(project_root: Path, roots: tuple[str, ...]) -> set[str]:
    source_root = project_root / "src"

    def module_path(name: str) -> Path | None:
        relative = Path(*name.split("."))
        module = source_root / relative.with_suffix(".py")
        package = source_root / relative / "__init__.py"
        return module if module.is_file() else (package if package.is_file() else None)

    pending = list(roots)
    seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        path = module_path(name)
        if path is None:
            continue
        seen.add(name)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        is_package = path.name == "__init__.py"
        package = name if is_package else name.rpartition(".")[0]
        for node in ast.walk(tree):
            candidates: list[str] = []
            if isinstance(node, ast.Import):
                candidates.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    parts = package.split(".") if package else []
                    if node.level > len(parts):
                        continue
                    base = ".".join(parts[: len(parts) - node.level + 1])
                    target = ".".join(part for part in (base, node.module or "") if part)
                else:
                    target = node.module or ""
                if target:
                    candidates.append(target)
                    candidates.extend(f"{target}.{alias.name}" for alias in node.names)
            pending.extend(
                candidate
                for candidate in candidates
                if candidate.startswith("sc_referee") and module_path(candidate) is not None
            )
    return seen


def test_code_lane_dependence_pin_is_live_and_v2_growth_is_unregistered(
    project_root: Path,
) -> None:
    binding = "method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1"
    assert installed_pin_matches_live_identity(GRANT_PINS[binding]) is True
    registry = json.loads(
        (
            project_root / "src/sc_referee/resources/scientific-check-manifests-v1/registry.json"
        ).read_text(encoding="utf-8")
    )
    assert all("v2-growth" not in canonical_json(item) for item in registry["modules"])
    assert all(
        "v2-growth" not in canonical_json(item) for item in registry["method_conflict_bindings"]
    )
    closure = _production_import_closure(
        project_root,
        (
            "sc_referee.controller",
            "sc_referee.cli",
            "sc_referee.capability_matrix",
        ),
    )
    assert not any(name.startswith("sc_referee.dependence_recognition_v2") for name in closure)
    isolated = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import sc_referee.controller, sc_referee.cli, "
                "sc_referee.capability_matrix; "
                "assert not any(name.startswith('sc_referee.dependence_recognition_v2') "
                "for name in sys.modules)"
            ),
        ],
        cwd=project_root,
        env={**os.environ, "PYTHONPATH": ".:src:evaluation/src"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert isolated.returncode == 0, isolated.stderr


def test_adapter_payload_is_deterministic() -> None:
    context = _context(_source(), _ADVERSE)
    first = DependenceRecognitionV2ShadowAdapter().inspect(context)
    second = DependenceRecognitionV2ShadowAdapter().inspect(context)
    assert canonical_json(first) == canonical_json(second)


def test_adapter_exception_keeps_the_full_common_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(_context: FrozenInspectionContext) -> None:
        raise RuntimeError("injected")

    monkeypatch.setattr(
        "sc_referee.dependence_recognition_v2.adapter.analyze_dependence_growth_python",
        explode,
    )
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(_source(), _ADVERSE))
    assert payload["abstention_reasons"] == ["v2-shadow-pipeline-exception"]
    assert payload["delivery_plane"] == "unregistered_development_shadow_only"
    assert payload["report_only"] is True
    assert payload["production_finding_permitted"] is False
    assert payload["adapter_id"] == "dependence-recognition-semantic-v2-growth-shadow"
    assert payload["adapter_version"] == "2.5.0-development"
    assert payload["adapter_implementation_digest"].startswith("sha256:")
    assert payload["implementation_dependency_closure"]


def test_reason_registry_equals_the_package_emission_vocabulary(project_root: Path) -> None:
    emitted_literals: set[str] = set()
    for relative in (
        "src/sc_referee/dependence_recognition_v2/python_analyzer.py",
        "src/sc_referee/dependence_recognition_v2/csv_domain.py",
        "src/sc_referee/dependence_recognition_v2/count_domain.py",
        "src/sc_referee/dependence_recognition_v2/adapter.py",
        "src/sc_referee/dependence_recognition_v2/intake_declaration.py",
        "src/sc_referee/dependence_recognition_v2/paired_domain.py",
    ):
        tree = ast.parse((project_root / relative).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                function_name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else (node.func.attr if isinstance(node.func, ast.Attribute) else None)
                )
                if function_name in {
                    "_Refusal",
                    "_refusal",
                    "_abstention",
                    "_discharged_unsupported",
                    "_unsupported",
                }:
                    emitted_literals.update(
                        argument.value
                        for argument in node.args
                        if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
                    )
                    emitted_literals.update(
                        element.value
                        for argument in node.args
                        if isinstance(argument, ast.Tuple)
                        for element in argument.elts
                        if isinstance(element, ast.Constant) and isinstance(element.value, str)
                    )
                if (
                    function_name == "add"
                    and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "reasons"
                ):
                    emitted_literals.update(
                        argument.value
                        for argument in node.args
                        if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
                    )
            if relative.endswith(("csv_domain.py", "paired_domain.py")) and (
                isinstance(node, ast.Return)
                and isinstance(node.value, ast.Tuple)
                and len(node.value.elts) == 2
                and isinstance(node.value.elts[1], ast.Constant)
                and isinstance(node.value.elts[1].value, str)
            ):
                emitted_literals.add(node.value.elts[1].value)
            if (
                relative.endswith(("csv_domain.py", "paired_domain.py"))
                and isinstance(node, ast.Return)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                emitted_literals.add(node.value.value)
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values, strict=True):
                    if (
                        isinstance(key, ast.Constant)
                        and key.value == "reason_code"
                        and isinstance(value, ast.Constant)
                        and isinstance(value.value, str)
                    ):
                        emitted_literals.add(value.value)
    emitted_literals.add("dependence-v2-shadow-abstention")
    emitted_literals.update(
        {
            "count-procedure-trial-declaration-missing",
            "repeated-unit-rows-counted-as-independent-binomtest-trials",
            "repeated-unit-rows-enter-independent-fisher-cells",
        }
    )
    emitted_literals.update(
        f"certificate-kernel-refusal:{item}" for item in DEPENDENCE_V2_KERNEL_REFUSAL_OBLIGATIONS
    )
    assert emitted_literals == set(DEPENDENCE_V2_REASON_REGISTRY)
