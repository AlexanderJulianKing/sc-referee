"""Six-role pilot fixtures for the dependence-recognition envelope.

Provider transport is recorded in-process, while every deterministic pipeline
step remains real.  Intake executes only the fixture workflows commissioned in
this file, under the dedicated SciPy 1.14.0 qualification interpreter.
"""

from __future__ import annotations

import json
import sys
import warnings
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation import lean_pipeline
from sc_referee_evaluation.lean_pipeline import (
    DEFAULT_ALLOWED_IMPORT_ROOTS,
    LeanPipelineError,
    _manifest_record,
    _probe_sandbox_runtime,
    step_authoring,
    step_authority,
    step_detector,
    step_intake,
    step_labels,
    step_review,
)

from sc_referee.controller import replay
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition.authority_lock import (
    AUTHORITY_LIMITATIONS,
    DECLARED_EXECUTION_ROOT,
    LOCK_KIND,
    approval_projection,
    lock_projection,
    verify_dependence_authorization_lock,
)
from sc_referee.dependence_recognition.python_analyzer import analyze_dependence_python
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    InspectionDocument,
    RecordRef,
)
from scripts.lean_pipeline import (
    DEPENDENCE_SANDBOX_PYTHON,
    ENVELOPE_CONFIGS,
    default_dependence_config,
)

_ROLES = (
    "error_bearing",
    "corrected_twin",
    "valid_alternative",
    "hard_negative",
    "ambiguous",
    "unsupported",
)
_CASE_BY_ROLE = {role: f"case:{index:020x}" for index, role in enumerate(_ROLES, start=1)}
_ROLE_BY_CASE = {case_id: role for role, case_id in _CASE_BY_ROLE.items()}
_LEFT = tuple(float(index) for index in range(1, 13))
_RIGHT = (2.0, 4.0, 3.0, 5.0, 7.0, 6.0, 9.0, 8.0, 11.0, 10.0, 13.0, 12.0)
_RESULTS = {
    "error_bearing": (
        "TtestResult(statistic=np.float64(-0.8581613266497022), "
        "pvalue=np.float64(0.3952529117073811), df=np.float64(46.0))"
    ),
    "corrected_twin": (
        "TtestResult(statistic=np.float64(-0.6793662204867575), "
        "pvalue=np.float64(0.5039915691282064), df=np.float64(22.0))"
    ),
    "valid_alternative": (
        "MannwhitneyuResult(statistic=np.float64(60.5), pvalue=np.float64(0.5243792697676437))"
    ),
    "hard_negative": (
        "TtestResult(statistic=np.float64(-0.8581613266497022), "
        "pvalue=np.float64(0.3952529117073811), df=np.float64(46.0))"
    ),
    "ambiguous": (
        "TtestResult(statistic=np.float64(-0.6793662204867575), "
        "pvalue=np.float64(0.5039915691282064), df=np.float64(22.0))"
    ),
    "unsupported": (
        "TtestResult(statistic=np.float64(-3.63318042491699), "
        "pvalue=np.float64(0.00393470596182021), df=np.int64(11))"
    ),
}
_CALLABLE_BY_ROLE = {
    "error_bearing": "scipy.stats.ttest_ind",
    "corrected_twin": "scipy.stats.ttest_ind",
    "valid_alternative": "scipy.stats.mannwhitneyu",
    "hard_negative": "scipy.stats.ttest_ind",
    "ambiguous": "scipy.stats.ttest_ind",
    "unsupported": "scipy.stats.ttest_rel",
}
_PROCEDURE_ATTRIBUTE_BY_ROLE = {
    role: value.rsplit(".", maxsplit=1)[-1] for role, value in _CALLABLE_BY_ROLE.items()
}
_ERROR_KEYS = (
    ("u01", "v07", "t01"),
    ("u01", "v08", "t02"),
    ("u02", "v09", "t03"),
    ("u02", "v10", "t04"),
    ("u03", "v11", "t05"),
    ("u03", "v12", "t06"),
    ("u04", "v13", "t07"),
    ("u04", "v14", "t08"),
    ("u05", "v15", "t09"),
    ("u05", "v16", "t10"),
    ("u06", "v17", "t11"),
    ("u06", "v18", "t12"),
    ("u07", "v19", "t13"),
    ("u07", "v20", "t14"),
    ("u08", "v21", "t15"),
    ("u08", "v22", "t16"),
    ("u09", "v23", "t17"),
    ("u09", "v24", "t18"),
    ("u10", "v01", "t19"),
    ("u10", "v02", "t20"),
    ("u11", "v03", "t21"),
    ("u11", "v04", "t22"),
    ("u12", "v05", "t23"),
    ("u12", "v06", "t24"),
)
_ERROR_LEFT = (
    1.0,
    1.5,
    2.0,
    2.5,
    3.0,
    3.5,
    4.0,
    4.5,
    5.0,
    5.5,
    6.0,
    6.5,
    7.0,
    7.5,
    8.0,
    8.5,
    9.0,
    9.5,
    10.0,
    10.5,
    11.0,
    11.5,
    12.0,
    12.5,
)
_ERROR_RIGHT = (
    2.0,
    2.25,
    4.0,
    4.25,
    3.0,
    3.25,
    5.0,
    5.25,
    7.0,
    7.25,
    6.0,
    6.25,
    9.0,
    9.25,
    8.0,
    8.25,
    11.0,
    11.25,
    10.0,
    10.25,
    13.0,
    13.25,
    12.0,
    12.25,
)
_TWIN_KEYS = (
    ("u01", "v07", "t01"),
    ("u02", "v09", "t03"),
    ("u03", "v11", "t05"),
    ("u04", "v13", "t07"),
    ("u05", "v15", "t09"),
    ("u06", "v17", "t11"),
    ("u07", "v19", "t13"),
    ("u08", "v21", "t15"),
    ("u09", "v23", "t17"),
    ("u10", "v01", "t19"),
    ("u11", "v03", "t21"),
    ("u12", "v05", "t23"),
)
_HARD_KEYS = (
    ("u07", "v12", "t01"),
    ("u08", "v13", "t02"),
    ("u09", "v14", "t03"),
    ("u10", "v15", "t04"),
    ("u11", "v16", "t05"),
    ("u12", "v17", "t06"),
    ("u01", "v18", "t07"),
    ("u02", "v19", "t08"),
    ("u03", "v20", "t09"),
    ("u06", "v21", "t10"),
    ("u05", "v22", "t11"),
    ("u04", "v23", "t12"),
    ("u19", "v24", "t13"),
    ("u20", "v01", "t14"),
    ("u21", "v02", "t15"),
    ("u22", "v03", "t16"),
    ("u23", "v04", "t17"),
    ("u24", "v05", "t18"),
    ("u13", "v06", "t19"),
    ("u14", "v07", "t20"),
    ("u15", "v08", "t21"),
    ("u18", "v09", "t22"),
    ("u17", "v10", "t23"),
    ("u16", "v11", "t24"),
)
_AMBIGUOUS_KEYS = (
    ("u01", "v07"),
    ("u01", "v11"),
    ("u02", "v06"),
    ("u02", "v09"),
    ("u03", "v01"),
    ("u03", "v12"),
    ("u04", "v05"),
    ("u04", "v03"),
    ("u05", "v10"),
    ("u05", "v04"),
    ("u06", "v08"),
    ("u06", "v02"),
)

_DEPENDENCE_SANDBOX_AVAILABLE = DEPENDENCE_SANDBOX_PYTHON.is_file()
DEPENDENCE_SANDBOX_AVAILABILITY_MARKER = (
    f"AVAILABLE: dependence sandbox runtime at {DEPENDENCE_SANDBOX_PYTHON}"
    if _DEPENDENCE_SANDBOX_AVAILABLE
    else (
        "PRE-PILOT BLOCKER: dedicated SciPy 1.14.0 dependence sandbox runtime is absent at "
        f"{DEPENDENCE_SANDBOX_PYTHON}"
    )
)
if not _DEPENDENCE_SANDBOX_AVAILABLE:
    warnings.warn(
        DEPENDENCE_SANDBOX_AVAILABILITY_MARKER,
        pytest.PytestWarning,
        stacklevel=1,
    )


def _keyed_rows(
    keys: tuple[tuple[str, str, str], ...],
    left: tuple[float, ...] = _LEFT,
    right: tuple[float, ...] = _RIGHT,
) -> list[tuple[str, str, str, float, float]]:
    return [(k1, k2, tag, a, b) for (k1, k2, tag), a, b in zip(keys, left, right, strict=True)]


def _rows(role: str) -> list[tuple[str, str, str, float, float]]:
    if role == "error_bearing":
        return _keyed_rows(_ERROR_KEYS, _ERROR_LEFT, _ERROR_RIGHT)
    if role == "hard_negative":
        return _keyed_rows(_HARD_KEYS, _ERROR_LEFT, _ERROR_RIGHT)
    if role == "ambiguous":
        return [
            (k1, k2, f"t{index + 1:02d}", _LEFT[index], _RIGHT[index])
            for index, (k1, k2) in enumerate(_AMBIGUOUS_KEYS)
        ]
    return _keyed_rows(_TWIN_KEYS)


def _csv(role: str) -> str:
    lines = ["k1,k2,tag,a,b"]
    lines.extend(f"{k1},{k2},{tag},{a},{b}" for k1, k2, tag, a, b in _rows(role))
    return "\n".join(lines) + "\n"


def _workflow(role: str) -> str:
    procedure = _PROCEDURE_ATTRIBUTE_BY_ROLE[role]
    return (
        "import csv\n"
        "from pathlib import Path\n"
        "import scipy.stats as st\n"
        'rows = list(csv.DictReader(Path("inputs/data.csv").read_text('
        'encoding="utf-8").splitlines()))\n'
        "staged = rows\n"
        'left = [float(row["a"]) for row in staged]\n'
        'right = [float(row["b"]) for row in staged]\n'
        f"result = st.{procedure}(left, right)\n"
        'Path("results/report.md").write_text(f"[selected-result] {result}\\n", '
        'encoding="utf-8")\n'
    )


def _authored_case(role: str) -> dict[str, Any]:
    return {
        "case_id": _CASE_BY_ROLE[role],
        "input_csv": _csv(role),
        "analysis_py": _workflow(role),
        "report_md": f"[selected-result] {_RESULTS[role]}\n",
        "selected_result_line": 1,
    }


def _authority_lock(
    case_id: str,
    role: str,
    input_digest: str,
    *,
    snapshot_digest: str,
    intake_recorded_at: str,
) -> dict[str, Any]:
    slug = case_id.removeprefix("case:")
    analysis_id = f"analysis:{slug}"
    procedure_id = f"procedure:{slug}"
    result_id = f"result:{slug}"
    authorization_id = f"authorization:{slug}"
    actor_id = "scientist:dependence-d-method-owner-01"
    value: dict[str, Any] = {
        "lock_kind": LOCK_KIND,
        "case_id": case_id,
        "snapshot_digest": snapshot_digest,
        "intake_recorded_at": intake_recorded_at,
        "declared_execution_root": DECLARED_EXECUTION_ROOT,
        "records": [
            {
                "record_type": "analysis",
                "record_id": analysis_id,
                "path": "workflow/analysis.py",
            },
            {
                "record_type": "procedure",
                "record_id": procedure_id,
                "resolved_callable": _CALLABLE_BY_ROLE[role],
            },
            {
                "record_type": "result",
                "record_id": result_id,
                "path": "results/report.md",
            },
            {
                "record_type": "human_method_authorization",
                "record_id": authorization_id,
                "actor_id": actor_id,
                "authority_state": "authorized",
                "analysis_target_ref": {
                    "record_type": "analysis",
                    "record_id": analysis_id,
                },
                "procedure_ref": {
                    "record_type": "procedure",
                    "record_id": procedure_id,
                },
                "independent_unit_definition_id": "unit-definition:k1-first-collection-source-item",
                "authorized_key_columns": ["k1"],
                "input_path": "inputs/data.csv",
                "input_content_digest": input_digest,
            },
        ],
        "approval": {
            "actor_kind": "human",
            "actor_id": actor_id,
            "approved_projection_digest": "sha256:" + "0" * 64,
            "approved_at": intake_recorded_at,
        },
        "authority_limitations": list(AUTHORITY_LIMITATIONS),
        "lock_digest": "sha256:" + "0" * 64,
    }
    value["approval"]["approved_projection_digest"] = semantic_digest(approval_projection(value))
    value["lock_digest"] = semantic_digest(lock_projection(value))
    return value


def _isolated_project_root(tmp_path: Path, project_root: Path) -> Path:
    (tmp_path / "src").symlink_to(project_root / "src")
    (tmp_path / "reference").symlink_to(project_root / "reference")
    return tmp_path


def _run_single_case_intake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
) -> dict[str, Any]:
    base = default_dependence_config()
    config = replace(
        base,
        pipeline_relative=Path("evaluation/qualification/dependence-frozen-workflow-test"),
        sandbox_python=Path(sys.executable),
        required_sandbox_distributions={},
    )
    participant_id = "actor:dependence-d-author-opus-19"
    case_id = "case:0000000000000000f102"
    role = "corrected_twin"
    authoring = tmp_path / config.pipeline_relative / "authoring"
    authoring.mkdir(parents=True)
    assignment = {
        "participant": {"participant_id": participant_id},
        "case_ids": [case_id],
        "prompt": "frozen workflow intake test",
        "prompt_digest": "sha256:" + "1" * 64,
        "output_schema": {"type": "object"},
        "call_identity_id": "00000000-0000-0000-0000-00000000f102",
    }
    protocol: dict[str, Any] = {
        "artifact_kind": "lean_pipeline_authoring_protocol",
        "envelope_id": config.envelope_id,
        "case_role_assignments": {case_id: role},
        "author_assignments": [assignment],
    }
    protocol["protocol_digest"] = semantic_digest(protocol)
    (authoring / "AUTHORING_PROTOCOL.json").write_text(
        canonical_json(protocol) + "\n", encoding="utf-8"
    )
    _manifest_record(
        tmp_path,
        config,
        "authoring",
        digest=str(protocol["protocol_digest"]),
        relative_path="authoring/AUTHORING_PROTOCOL.json",
    )
    report = f"[selected-result] {_RESULTS[role]}\n"
    response = {
        "participant_id": participant_id,
        "cases": [
            {
                "case_id": case_id,
                "input_csv": _csv(role),
                "analysis_py": source,
                "report_md": report,
                "selected_result_line": 1,
            }
        ],
    }
    attempt = {
        "participant_id": participant_id,
        "protocol_digest": protocol["protocol_digest"],
        "raw_response": canonical_json(response),
    }
    incoming = authoring / "incoming"
    incoming.mkdir()
    (incoming / "dependence-d-author-opus-19.json").write_text(
        canonical_json(attempt) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        lean_pipeline,
        "_sandbox_run",
        lambda _case_root, _sandbox_python: report.encode("utf-8"),
    )
    return step_intake(tmp_path, config)


def _preflight_context(role: str) -> FrozenInspectionContext:
    """Build only the frozen records required for an analyzer-envelope preflight."""

    source = _workflow(role).encode()
    data = _csv(role).encode()
    requirements = b"numpy==2.2.6\nscipy==1.14.0\n"
    data_digest = sha256_digest(data)
    requirements_digest = sha256_digest(requirements)
    surface_ref = RecordRef("publication_surface", "surface:pilot-d")
    artifact_ref = RecordRef("artifact", "artifact:pilot-d-report")
    snapshot_ref = RecordRef("repository_snapshot", "snapshot:pilot-d")
    analysis_file_ref = RecordRef("file_record", "file:pilot-d-analysis")
    parser_ref = RecordRef("parser_result", "parser:pilot-d-analysis")
    data_file_ref = RecordRef("file_record", "file:pilot-d-data")
    data_identity_ref = RecordRef("asset_identity", "asset:pilot-d-data")
    requirements_file_ref = RecordRef("file_record", "file:pilot-d-requirements")
    requirements_identity_ref = RecordRef("asset_identity", "asset:pilot-d-requirements")
    analysis_ref = RecordRef("analysis", "analysis:pilot-d")
    procedure_ref = RecordRef("procedure", "procedure:pilot-d")
    result_ref = RecordRef("result", "result:pilot-d")
    parser_payload = canonical_json(
        {"parser_id": "python-ast", "parser_version": "3.11", "state": "parsed"}
    ).encode()
    records: list[tuple[RecordRef, dict[str, object]]] = [
        (
            surface_ref,
            {
                "publication_surface_id": surface_ref.record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [artifact_ref.to_dict()]},
            },
        ),
        (
            artifact_ref,
            {
                "artifact_id": artifact_ref.record_id,
                "kind": "report",
                "path": "results/report.md",
            },
        ),
        (
            snapshot_ref,
            {
                "snapshot_id": snapshot_ref.record_id,
                "extensions": {
                    "x-material-full-digest-paths": ["inputs/data.csv", "requirements.txt"]
                },
            },
        ),
        (
            data_file_ref,
            {
                "file_record_id": data_file_ref.record_id,
                "path": "inputs/data.csv",
                "entry_kind": "regular_file",
                "asset_identity_ref": data_identity_ref.to_dict(),
            },
        ),
        (
            data_identity_ref,
            {
                "asset_identity_id": data_identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": data_file_ref.to_dict(),
                "identity_evidence": {"kind": "full_digest", "digest": data_digest},
            },
        ),
        (
            requirements_file_ref,
            {
                "file_record_id": requirements_file_ref.record_id,
                "path": "requirements.txt",
                "entry_kind": "regular_file",
                "asset_identity_ref": requirements_identity_ref.to_dict(),
            },
        ),
        (
            requirements_identity_ref,
            {
                "asset_identity_id": requirements_identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": requirements_file_ref.to_dict(),
                "identity_evidence": {
                    "kind": "full_digest",
                    "digest": requirements_digest,
                },
            },
        ),
        (analysis_file_ref, {"file_record_id": analysis_file_ref.record_id}),
        (parser_ref, {"parser_result_id": parser_ref.record_id}),
        (analysis_ref, {"analysis_id": analysis_ref.record_id}),
        (
            procedure_ref,
            {
                "procedure_id": procedure_ref.record_id,
                "resolved_callable": _CALLABLE_BY_ROLE[role],
            },
        ),
        (result_ref, {"result_id": result_ref.record_id, "path": "results/report.md"}),
    ]
    if role != "ambiguous":
        records.append(
            (
                RecordRef("human_method_authorization", "authorization:pilot-d"),
                {
                    "record_type": "human_method_authorization",
                    "record_id": "authorization:pilot-d",
                    "actor_id": "human:pilot-d-method-owner",
                    "authority_state": "authorized",
                    "analysis_target_ref": analysis_ref.to_dict(),
                    "procedure_ref": procedure_ref.to_dict(),
                    "independent_unit_definition_id": (
                        "unit-definition:k1-first-collection-source-item"
                    ),
                    "authorized_key_columns": ["k1"],
                    "input_path": "inputs/data.csv",
                    "input_content_digest": data_digest,
                },
            )
        )
    return FrozenInspectionContext(
        snapshot_digest=sha256_digest(b"pilot-d-preflight"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(
            InspectionDocument(
                path="workflow/analysis.py",
                file_ref=analysis_file_ref,
                content=source,
                content_digest=sha256_digest(source),
                media_type="text/x-python",
                parser_result_ref=parser_ref,
                parser_result_payload=parser_payload,
                parser_result_digest=sha256_digest(parser_payload),
            ),
        ),
        base_records=tuple(FrozenBaseRecord.from_record(ref, value) for ref, value in records),
        material_inputs=(
            FrozenMaterialInput(
                path="inputs/data.csv",
                file_ref=data_file_ref,
                asset_identity_ref=data_identity_ref,
                content=data,
                content_digest=data_digest,
            ),
            FrozenMaterialInput(
                path="requirements.txt",
                file_ref=requirements_file_ref,
                asset_identity_ref=requirements_identity_ref,
                content=requirements,
                content_digest=requirements_digest,
            ),
        ),
    )


def test_dependence_envelope_configuration_and_actor_seats() -> None:
    config = default_dependence_config()
    assert ENVELOPE_CONFIGS["dependence"] is default_dependence_config
    assert config.canonical_issue_class == (
        "issue-class:repeated-authorized-independent-unit-entry-into-row-independent-procedure"
    )
    assert config.envelope_id.endswith("-lean-d")
    assert config.pipeline_relative.as_posix().endswith("/pilot-d")
    assert config.roles == sorted(_ROLES)
    assert set(config.candidate_by_role) == set(_ROLES) - {"ambiguous"}
    assert set(config.candidate_by_role.values()) == {
        "one-analyzed-row-per-authorized-independent-unit"
    }
    assert config.mq_tolerant_roles == {"ambiguous", "unsupported"}
    assert config.contract_free_roles == {"ambiguous"}
    assert config.allowed_import_roots == DEFAULT_ALLOWED_IMPORT_ROOTS | {"scipy"}
    assert config.sandbox_python == DEPENDENCE_SANDBOX_PYTHON
    assert config.required_sandbox_distributions == {"numpy": "2.2.6", "scipy": "1.14.0"}
    assert config.controller_material_files == {
        "requirements.txt": b"numpy==2.2.6\nscipy==1.14.0\n"
    }
    assert config.material_input_paths == ("inputs/data.csv", "requirements.txt")
    assert config.input_csv_row_bounds == (1, 64)
    assert config.common_task == (
        "Treat `k1`, `k2`, and `tag` only as specified by the governing task and `a` and `b` "
        "as finite numeric measurements. Apply the procedure named in the case instructions "
        "to the complete staged row sequence and write its single selected result."
    )
    assert "Choose a neutral scientific subject area" not in config.common_task
    assert config.frozen_workflow_template is not None
    assert config.frozen_workflow_template.count("{procedure}") == 1
    assert set(config.frozen_workflow_procedure_by_role) == set(_ROLES)
    assert config.detector_id == "detector:bounded-analysis-method-conflict"
    assert sorted(config.authors) == [
        "actor:dependence-d-author-opus-19",
        "actor:dependence-d-author-opus-20",
    ]
    assert config.author_roles["actor:dependence-d-author-opus-19"] == [
        "error_bearing",
        "corrected_twin",
    ]
    assert config.author_roles["actor:dependence-d-author-opus-20"] == [
        "valid_alternative",
        "hard_negative",
        "ambiguous",
        "unsupported",
    ]
    assert config.reviewer.participant_id == "actor:dependence-d-reviewer-fable-12"
    assert config.escalation_reviewer.participant_id == "actor:dependence-d-reviewer-opus-09"
    assert (
        "Judge only whether this exact issue class is demonstrated in the selected report. "
        "Other methodological concerns, however serious, are outside this review and must "
        "not be recorded as this issue class."
    ) in config.review_instructions.replace("\n", " ")
    assert (
        "workflow/analysis.py must consist of exactly these lines, byte for byte, with "
        "PROCEDURE replaced by the procedure named in your case instructions and nothing "
        "else changed:"
    ) in config.author_case_requirements
    for role, result in _RESULTS.items():
        assert result in "\n".join(config.role_constraints[role])
    ambiguous = "\n".join(config.role_constraints["ambiguous"])
    for index, (k1, k2) in enumerate(_AMBIGUOUS_KEYS, start=1):
        triple = f"{k1},{k2},t{index:02d}"
        assert f"`{triple}`" in ambiguous
    assert "Do not substitute any author-chosen string" in ambiguous
    assert all(k1.removeprefix("u") != k2.removeprefix("v") for k1, k2 in _AMBIGUOUS_KEYS)
    for role, keys in {
        "error_bearing": _ERROR_KEYS,
        "corrected_twin": _TWIN_KEYS,
        "valid_alternative": _TWIN_KEYS,
        "hard_negative": _HARD_KEYS,
        "unsupported": _TWIN_KEYS,
    }.items():
        role_text = "\n".join(config.role_constraints[role])
        for k1, k2, tag in keys:
            assert f"`{k1},{k2},{tag}`" in role_text
    error_text = "\n".join(config.role_constraints["error_bearing"])
    assert f"`{', '.join(str(value) for value in _ERROR_LEFT)}`" in error_text
    assert f"`{', '.join(str(value) for value in _ERROR_RIGHT)}`" in error_text
    hard_text = "\n".join(config.role_constraints["hard_negative"])
    assert f"`{', '.join(str(value) for value in _ERROR_LEFT)}`" in hard_text
    assert f"`{', '.join(str(value) for value in _ERROR_RIGHT)}`" in hard_text
    protocol_note = " ".join((default_dependence_config.__doc__ or "").split())
    assert "primary and escalation reviewers were unanimous against the answer key" in protocol_note
    assert "retired attempt's verdicts are void" in protocol_note
    assert "known one-directional effect" in protocol_note
    assert "covered_negative`` result" in (default_dependence_config.__doc__ or "")


def test_dependence_pilot_d_tasks_data_and_workflow_are_frozen_to_two_collections() -> None:
    config = default_dependence_config()
    authorized = config.task_by_role["error_bearing"]
    assert "`k1` identifies a first-collection source item measured by column `a`" in authorized
    assert "`k2` identifies a second-collection source item measured by column `b`" in authorized
    assert "The two collections are disjoint." in authorized
    assert "`tag` is an opaque annotation." in authorized
    assert "The row pairing is a storage convention only" in authorized
    assert "no matching, pairing, block, or other relationship" in authorized
    ambiguous = config.task_by_role["ambiguous"]
    assert "two disjoint collections" in ambiguous
    assert "`tag` is an opaque annotation." in ambiguous
    assert "The row pairing is a storage convention only" in ambiguous
    assert "does not establish whether either code identifies a source item" in ambiguous
    assert "no matching, pairing, block, or other relationship" in ambiguous

    error = _rows("error_bearing")
    assert len(error) == 24
    assert tuple(row[:3] for row in error) == _ERROR_KEYS
    assert len({row[1] for row in error}) == 24
    assert len({row[2] for row in error}) == 24
    for index in range(0, 24, 2):
        first, second = error[index : index + 2]
        assert first[0] == second[0]
        assert first[1:] != second[1:]
        assert first[1] != second[1]
        assert first[2] != second[2]
        assert first[3] != second[3]
        assert first[4] != second[4]

    twin = _rows("corrected_twin")
    assert tuple(row[:3] for row in twin) == _TWIN_KEYS
    assert twin == error[::2]
    assert _rows("valid_alternative") == twin
    assert _rows("unsupported") == twin

    hard = _rows("hard_negative")
    assert tuple(row[:3] for row in hard) == _HARD_KEYS
    assert len(hard) == 24
    assert {row[0] for row in hard} == {f"u{index:02d}" for index in range(1, 25)}
    assert {row[1] for row in hard} == {f"v{index:02d}" for index in range(1, 25)}
    assert {row[2] for row in hard} == {f"t{index:02d}" for index in range(1, 25)}
    assert [row[3:] for row in hard] == [row[3:] for row in error]

    ambiguous_rows = _rows("ambiguous")
    assert tuple((row[0], row[1]) for row in ambiguous_rows) == _AMBIGUOUS_KEYS
    assert [row[2] for row in ambiguous_rows] == [f"t{index:02d}" for index in range(1, 13)]
    assert len({row[1] for row in ambiguous_rows}) == 12
    assert all(
        ambiguous_rows[index][0] == ambiguous_rows[index + 1][0] for index in range(0, 12, 2)
    )
    for role in _ROLES:
        assert all(row[0][1:] != row[1][1:] for row in _rows(role)), role

    expected_workflow = (
        "import csv\n"
        "from pathlib import Path\n"
        "import scipy.stats as st\n"
        'rows = list(csv.DictReader(Path("inputs/data.csv").read_text('
        'encoding="utf-8").splitlines()))\n'
        "staged = rows\n"
        'left = [float(row["a"]) for row in staged]\n'
        'right = [float(row["b"]) for row in staged]\n'
        "result = st.ttest_ind(left, right)\n"
        'Path("results/report.md").write_text(f"[selected-result] {result}\\n", '
        'encoding="utf-8")\n'
    )
    assert _workflow("corrected_twin") == expected_workflow
    assert config.frozen_workflow_template is not None
    author_facing_template = config.frozen_workflow_template.replace("{procedure}", "PROCEDURE")
    assert config.author_case_requirements.count(author_facing_template) == 1
    for role in _ROLES:
        assert _workflow(role) == config.frozen_workflow_template.replace(
            "{procedure}", config.frozen_workflow_procedure_by_role[role]
        )
    assert "must consist only of module-level imports and assignments" not in (
        config.author_case_requirements
    )
    assert "Zero or more row-sequence aliases" not in config.author_case_requirements


def test_dependence_frozen_workflow_template_match_passes_intake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = _run_single_case_intake(tmp_path, monkeypatch, _workflow("corrected_twin"))
    assert ledger["case_count"] == 1
    assert ledger["entries"][0]["sandbox_runs"] == 2


@pytest.mark.parametrize(
    ("variant", "source"),
    [
        (
            "from-import",
            _workflow("corrected_twin")
            .replace("import scipy.stats as st\n", "from scipy import stats\n")
            .replace("st.ttest_ind", "stats.ttest_ind"),
        ),
        ("added-docstring", '"""Authored workflow."""\n' + _workflow("corrected_twin")),
        ("added-comment", "# authored workflow\n" + _workflow("corrected_twin")),
    ],
)
def test_dependence_frozen_workflow_variants_refuse_intake_with_named_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    variant: str,
    source: str,
) -> None:
    del variant
    with pytest.raises(LeanPipelineError, match=r"^frozen-workflow-template-mismatch$"):
        _run_single_case_intake(tmp_path, monkeypatch, source)


@pytest.mark.parametrize("role", _ROLES)
def test_dependence_pilot_d_workflows_are_inside_the_static_preflight(role: str) -> None:
    analysis = analyze_dependence_python(_preflight_context(role))
    if role == "unsupported":
        assert analysis.state == "unsupported"
        assert analysis.unsupported_constructs == ("paired-procedure-operand-unverified",)
    else:
        assert analysis.unsupported_constructs == ()
        assert analysis.state == ("question" if role == "ambiguous" else "proposal")


@pytest.mark.skipif(
    not _DEPENDENCE_SANDBOX_AVAILABLE,
    reason="dedicated SciPy 1.14.0 qualification interpreter is absent",
)
def test_dependence_pilot_d_four_result_reprs_recompute_in_pinned_runtime(
    tmp_path: Path,
) -> None:
    observed: dict[str, str] = {}
    for role in (
        "error_bearing",
        "corrected_twin",
        "valid_alternative",
        "hard_negative",
        "unsupported",
    ):
        case_root = tmp_path / role
        (case_root / "inputs").mkdir(parents=True)
        (case_root / "workflow").mkdir()
        (case_root / "results").mkdir()
        (case_root / "inputs/data.csv").write_text(_csv(role), encoding="utf-8")
        source = _workflow(role)
        (case_root / "workflow/analysis.py").write_text(source, encoding="utf-8")
        lean_pipeline._static_guard(source, default_dependence_config().allowed_import_roots)
        observed[role] = lean_pipeline._sandbox_run(case_root, DEPENDENCE_SANDBOX_PYTHON).decode(
            "utf-8"
        )

    assert observed == {
        role: f"[selected-result] {_RESULTS[role]}\n"
        for role in (
            "error_bearing",
            "corrected_twin",
            "valid_alternative",
            "hard_negative",
            "unsupported",
        )
    }


@pytest.mark.skipif(
    not _DEPENDENCE_SANDBOX_AVAILABLE,
    reason="dedicated SciPy 1.14.0 qualification interpreter is absent",
)
def test_dependence_dedicated_runtime_probe_passes_for_real() -> None:
    pins = {"numpy": "2.2.6", "scipy": "1.14.0"}
    record = _probe_sandbox_runtime(DEPENDENCE_SANDBOX_PYTHON, pins)
    assert record["interpreter_path"] == DEPENDENCE_SANDBOX_PYTHON.as_posix()
    assert record["python_version"].startswith("3.11.15 ")
    assert record["required_distributions"] == pins
    assert record["observed_distributions"]["numpy"]["distribution_version"] == "2.2.6"
    assert record["observed_distributions"]["numpy"]["module_version"] == "2.2.6"
    assert record["observed_distributions"]["scipy"]["distribution_version"] == "1.14.0"
    assert record["observed_distributions"]["scipy"]["module_version"] == "1.14.0"
    assert record["probe_digest"] == semantic_digest(
        {key: value for key, value in record.items() if key != "probe_digest"}
    )


@pytest.mark.skipif(
    not _DEPENDENCE_SANDBOX_AVAILABLE,
    reason="dedicated SciPy 1.14.0 qualification interpreter is absent",
)
def test_dependence_six_role_fixture_runs_real_pipeline_without_findings(
    tmp_path: Path,
    project_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    isolated_root = _isolated_project_root(tmp_path, project_root)
    base = default_dependence_config()
    config = replace(
        base,
        pipeline_relative=Path("evaluation/qualification/dependence-stage3-six-role-fixture"),
        sealed_case_assignments={case_id: role for role, case_id in sorted(_CASE_BY_ROLE.items())},
    )
    monkeypatch.setattr(lean_pipeline, "ensure_calibrations", lambda _root, _config: {})

    def _recorded_author_transport(
        selected: Any,
        participant: Any,
        _prompt: str,
        _session_id: str,
        capture_root: Path,
    ) -> dict[str, Any]:
        roles = selected.author_roles[participant.participant_id]
        payload = {
            "participant_id": participant.participant_id,
            "cases": [_authored_case(role) for role in roles],
        }
        capture_root.mkdir(parents=True, exist_ok=True)
        return {
            "raw_response": canonical_json(payload),
            "transport_error": None,
            "process_record": {"capture_digest": semantic_digest(payload)},
            "started_at": "2026-08-10T12:01:00Z",
            "completed_at": "2026-08-10T12:01:01Z",
        }

    monkeypatch.setattr(lean_pipeline, "_call_cli", _recorded_author_transport)
    protocol = step_authoring(isolated_root, config)
    assert protocol["case_role_assignments"] == {
        case_id: _ROLE_BY_CASE[case_id] for case_id in sorted(_ROLE_BY_CASE)
    }

    intake = step_intake(isolated_root, config)
    assert intake["case_count"] == 6
    assert intake["ground_truth_execution"]["executed"] is True
    assert intake["ground_truth_execution"]["runs_per_case"] == 2
    assert intake["sandbox_runtime_probe"]["required_distributions"] == {
        "numpy": "2.2.6",
        "scipy": "1.14.0",
    }
    intake_by_case = {str(row["case_id"]): row for row in intake["entries"]}

    incoming_root = isolated_root / config.pipeline_relative / "authority/incoming"
    incoming_root.mkdir(parents=True)
    for case_id, role in sorted(_ROLE_BY_CASE.items()):
        if role == "ambiguous":
            continue
        input_digest = str(intake_by_case[case_id]["file_digests"]["inputs/data.csv"])
        lock = _authority_lock(
            case_id,
            role,
            input_digest,
            snapshot_digest=str(intake_by_case[case_id]["expected_audit_snapshot_digest"]),
            intake_recorded_at=str(intake["recorded_at"]),
        )
        lock_path = incoming_root / f"{case_id.removeprefix('case:')}.json"
        lock_path.write_text(canonical_json(lock) + "\n", encoding="utf-8")
        verified = verify_dependence_authorization_lock(
            lock_path,
            expected_case_id=case_id,
            expected_snapshot_digest=str(intake_by_case[case_id]["expected_audit_snapshot_digest"]),
            expected_intake_recorded_at=str(intake["recorded_at"]),
            source_paths=("workflow/analysis.py",),
            selected_report_path="results/report.md",
            material_input_digests={
                "inputs/data.csv": input_digest,
                "requirements.txt": str(
                    intake_by_case[case_id]["controller_material_file_digests"]["requirements.txt"]
                ),
            },
            forbidden_role_markers=config.roles,
        )
        assert verified.lock_digest == lock["lock_digest"]

    authority = step_authority(isolated_root, config)
    assert authority["frozen_before_review"] is True
    assert authority["authorized_count"] == 5
    assert authority["withheld_count"] == 1
    assert all("case_role" not in entry for entry in authority["entries"])
    assert {
        Path(str(entry["frozen_lock_relative"])).stem
        for entry in authority["entries"]
        if entry["frozen_lock_relative"] is not None
    } == {
        case_id.removeprefix("case:")
        for case_id, role in _ROLE_BY_CASE.items()
        if role != "ambiguous"
    }

    review_observed_frozen_authority: list[bool] = []

    def _recorded_review_transport(
        _project_root: Path,
        selected: Any,
        _review_root: Path,
        participant: Any,
        case_subset: list[str],
        _preparations_by_case: dict[str, dict[str, Any]],
        workspace_payloads: dict[str, dict[str, bytes]],
        _tuple_digest: str,
        label: str,
    ) -> dict[str, Any]:
        review_observed_frozen_authority.append(
            (isolated_root / config.pipeline_relative / "authority/AUTHORITY_LEDGER.json").is_file()
        )
        assert label == "primary"
        assert all(
            set(payloads)
            == {"task.md", "inputs/data.csv", "workflow/analysis.py", "results/report.md"}
            for payloads in workspace_payloads.values()
        )
        entries = []
        for index, case_id in enumerate(case_subset, start=1):
            role = _ROLE_BY_CASE[case_id]
            verdict = selected.expected_verdict(role)
            entries.append(
                {
                    "case_id": case_id,
                    "review_role": label,
                    "participant_id": participant.participant_id,
                    "review_id": f"review:{index:020x}",
                    "review_digest": "sha256:" + f"{index:064x}",
                    "packet_digest": "sha256:" + f"{index + 10:064x}",
                    "capture_digest": "sha256:" + f"{index + 20:064x}",
                    "verdict": verdict,
                    "issue_class": (
                        selected.canonical_issue_class if verdict == "demonstrated_issue" else None
                    ),
                    "unresolved_material_question_count": 0,
                }
            )
        return {
            "entries": entries,
            "call_identity_id": f"call:{label}",
            "prompt_digest": "sha256:" + "1" * 64,
            "output_schema_digest": "sha256:" + "2" * 64,
            "shared_transcript_digest": "sha256:" + "3" * 64,
            "packet_digests": {
                case_id: "sha256:" + f"{index + 10:064x}"
                for index, case_id in enumerate(case_subset, start=1)
            },
        }

    monkeypatch.setattr(lean_pipeline, "_run_review_call", _recorded_review_transport)
    review = step_review(isolated_root, config)
    assert review_observed_frozen_authority == [True]
    assert review["authority_ledger_digest"] == authority["ledger_digest"]
    assert review["unresolved_case_ids"] == []
    labels = step_labels(isolated_root, config)
    assert labels["label_count"] == 6

    detector = step_detector(isolated_root, config)
    rows_by_role = {str(row["case_role"]): row for row in detector["entries"]}
    assert rows_by_role["error_bearing"]["comparison_outcome"] == "true_positive"
    assert rows_by_role["error_bearing"]["finding_candidate_count"] == 1
    for role in set(_ROLES) - {"error_bearing"}:
        assert rows_by_role[role]["comparison_outcome"] == "true_negative"
        assert rows_by_role[role]["finding_candidate_count"] == 0
    assert detector["pilot_metrics"] == {
        "opportunity_count": 6,
        "true_positive_count": 1,
        "true_negative_count": 5,
        "false_accusation_count": 0,
        "missed_error_count": 0,
        "sensitivity": 1.0,
        "false_accusation_rate": 0.0,
    }
    assert detector["production_finding_count"] == 0
    assert all(row["production_findings"] == 0 for row in detector["entries"])
    assert all(row["replay_equal"] is True for row in detector["entries"])

    replayed_by_role: dict[str, dict[str, Any]] = {}
    semantic_locks_by_role: dict[str, dict[str, Any]] = {}
    for role, case_id in _CASE_BY_ROLE.items():
        slug = case_id.removeprefix("case:")
        lock_path = (
            isolated_root
            / config.pipeline_relative
            / "detector-run/runs"
            / slug
            / "audit/semantic.lock.json"
        )
        semantic_locks_by_role[role] = json.loads(lock_path.read_bytes())
        replayed_by_role[role] = replay(
            lock_path,
            isolated_root / "fixture-replay" / slug,
            isolated_root / "reference/schemas-v0.18.0",
        )

    detector_id = config.detector_id
    states_by_role = {
        role: [
            str(result["state"])
            for result in bundle["detector_results"]
            if result.get("detector_id") == detector_id
        ]
        for role, bundle in replayed_by_role.items()
    }
    assert states_by_role["error_bearing"] == ["evaluation_finding_candidate"]
    for role in ("corrected_twin", "valid_alternative", "hard_negative"):
        assert states_by_role[role] == ["no_issue_detected_within_coverage"]
    assert states_by_role["ambiguous"] == []
    assert states_by_role["unsupported"] == []
    ambiguous_module = next(
        item
        for item in semantic_locks_by_role["ambiguous"]["scientific_check_registry"]["evaluation"][
            "modules"
        ]
        if item["check_id"] == config.check_id
    )
    assert ambiguous_module["state"] == "ambiguous"
    assert [item["abstention_reason"] for item in ambiguous_module["observations"]] == [
        "independent-unit-definition-unresolved"
    ]
    assert any(
        disclosure.get("extensions", {}).get("x-scientific-check-id") == config.check_id
        and disclosure["extensions"]["x-scientific-check-state"] == "ambiguous"
        for disclosure in replayed_by_role["ambiguous"]["disclosures"]
    )
    unsupported_module = next(
        item
        for item in semantic_locks_by_role["unsupported"]["scientific_check_registry"][
            "evaluation"
        ]["modules"]
        if item["check_id"] == config.check_id
    )
    assert unsupported_module["state"] == "unsupported"
    assert [item["abstention_reason"] for item in unsupported_module["observations"]] == [
        "paired-procedure-operand-unverified"
    ]
    assert not [
        assertion
        for assertion in replayed_by_role["unsupported"]["semantic_assertions"]
        if assertion.get("extensions", {}).get("x-scientific-check-id") == config.check_id
    ]
    assert all(not bundle["findings"] for bundle in replayed_by_role.values())

    # The runtime and authored bytes are both bound into intake, while production
    # audit remains non-executing and replay-stable.
    for role, case_id in _CASE_BY_ROLE.items():
        intake_row = intake_by_case[case_id]
        assert intake_row["sandbox_report_digest"] == sha256_digest(
            f"[selected-result] {_RESULTS[role]}\n"
        )
        assert intake_row["sandbox_runs"] == 2
        assert rows_by_role[role]["project_code_executions"] == 0


def test_dependence_sandbox_execution_tests_cannot_silently_skip_when_runtime_exists() -> None:
    guarded_tests = (
        test_dependence_dedicated_runtime_probe_passes_for_real,
        test_dependence_pilot_d_four_result_reprs_recompute_in_pinned_runtime,
        test_dependence_six_role_fixture_runs_real_pipeline_without_findings,
    )
    skip_conditions: list[bool] = []
    for test in guarded_tests:
        marks = [mark for mark in getattr(test, "pytestmark", ()) if mark.name == "skipif"]
        assert len(marks) == 1
        skip_conditions.append(bool(marks[0].args[0]))

    if DEPENDENCE_SANDBOX_PYTHON.is_file():
        assert DEPENDENCE_SANDBOX_AVAILABILITY_MARKER.startswith("AVAILABLE:")
        assert skip_conditions == [False, False, False]
    else:
        assert DEPENDENCE_SANDBOX_AVAILABILITY_MARKER.startswith("PRE-PILOT BLOCKER:")
        assert skip_conditions == [True, True, True]


def test_dependence_review_subset_projects_through_real_run_review_call(
    tmp_path: Path,
    project_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pin the pilot-a harness bug: projection sees only the strict review subset."""

    config = default_dependence_config()
    all_cases = [f"case:{index:020x}" for index in range(101, 104)]
    case_subset = [all_cases[0], all_cases[2]]
    workspace_payloads = {
        case_id: {
            "task.md": f"Visible task for {case_id}.\n".encode(),
            "inputs/data.csv": _csv("corrected_twin").encode(),
            "workflow/analysis.py": _workflow("corrected_twin").encode(),
            "results/report.md": (f"[selected-result] {_RESULTS['corrected_twin']}\n").encode(),
        }
        for case_id in all_cases
    }
    workspace_payloads[all_cases[1]]["task.md"] = b"EXCLUDED-SUBSET-SENTINEL\n"
    preparations_by_case: dict[str, dict[str, Any]] = {}
    for case_id in all_cases:
        manifest: dict[str, Any] = {
            "record_type": "evaluation_blind_workspace_manifest",
            "workspace_id": f"workspace:{case_id.removeprefix('case:')}",
            "created_at": "2026-08-10T11:59:00Z",
            "source_snapshot_ref": {
                "record_type": "repository_snapshot",
                "record_id": f"snapshot:{case_id.removeprefix('case:')}",
            },
            "source_snapshot_digest": "sha256:" + "a" * 64,
            "files": [
                {
                    "path": path,
                    "content_digest": sha256_digest(payload),
                    "byte_size": len(payload),
                }
                for path, payload in sorted(workspace_payloads[case_id].items())
            ],
            "answer_side_content_copied": False,
            "project_code_executed": False,
        }
        manifest["manifest_digest"] = semantic_digest(manifest)
        preparations_by_case[case_id] = {"workspace_manifest": manifest}

    observed_prompts: list[str] = []

    def _transport(
        _config: Any,
        participant: Any,
        prompt: str,
        _session_id: str,
        _capture_root: Path,
    ) -> dict[str, Any]:
        observed_prompts.append(prompt)
        reviews = []
        for case_id in case_subset:
            payloads = workspace_payloads[case_id]
            task_line = payloads["task.md"].decode().strip()
            report_line = payloads["results/report.md"].decode().strip()
            reviews.append(
                {
                    "case_id": case_id,
                    "verdict": "no_demonstrated_issue_within_scope",
                    "bounded_statement": None,
                    "root_cause": None,
                    "issue_class": None,
                    "evidence_atoms": [
                        {
                            "description": "Visible task evidence.",
                            "source_spans": [
                                {
                                    "path": "task.md",
                                    "start_line": 1,
                                    "end_line": 1,
                                    "quoted_text": task_line,
                                }
                            ],
                        }
                    ],
                    "counterevidence_atoms": [
                        {
                            "description": "Visible selected-result counterevidence.",
                            "source_spans": [
                                {
                                    "path": "results/report.md",
                                    "start_line": 1,
                                    "end_line": 1,
                                    "quoted_text": report_line,
                                }
                            ],
                        }
                    ],
                    "falsification_attempt": "Checked the visible task against the report.",
                    "cross_case_evidence_used": False,
                    "unresolved_material_questions": [],
                    "self_reported_confidence": "high",
                }
            )
        response = {
            "reviewer_participant_id": participant.participant_id,
            "reviews": reviews,
        }
        return {
            "raw_response": canonical_json(response),
            "transport_error": None,
            "completed_at": "2026-08-10T12:00:02Z",
        }

    monkeypatch.setattr(lean_pipeline, "_call_cli", _transport)
    monkeypatch.setattr(lean_pipeline, "_now", lambda: "2026-08-10T12:00:02Z")
    review_root = tmp_path / "review"
    review_root.mkdir()
    result = lean_pipeline._run_review_call(
        project_root,
        config,
        review_root,
        config.escalation_reviewer,
        case_subset,
        preparations_by_case,
        workspace_payloads,
        "sha256:" + "b" * 64,
        "escalation",
    )

    assert [entry["case_id"] for entry in result["entries"]] == case_subset
    assert set(result["packet_digests"]) == set(case_subset)
    assert len(observed_prompts) == 1
    assert "EXCLUDED-SUBSET-SENTINEL" not in observed_prompts[0]
