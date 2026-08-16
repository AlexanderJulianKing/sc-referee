"""Isolation and transport regressions for the non-measurement wall corpus."""

from __future__ import annotations

import ast
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.scientific_checks.core import FrozenInspectionContext
from scripts import wall_mining_corpus as corpus

PINNED_SCIPY_PYTHON = (
    Path.home() / "Desktop/random_stuff/sc-referee-pilot-runtime/scipy114-venv/bin/python"
)

VALID_SOURCE = """import csv
from pathlib import Path
from scipy import stats

def load_groups(path):
    groups = {}
    with Path(path).open(newline="", encoding="ascii") as handle:
        for row in csv.DictReader(handle):
            if row["include"] == "yes":
                groups.setdefault(row["arm"], []).append(float(row["value"]))
    return groups

groups = load_groups("data/input.csv")
left = groups["A"]
right = groups["B"]
result = stats.ttest_ind(left, right)
Path("results").mkdir(parents=True, exist_ok=True)
Path("results/report.md").write_text(f"# Result\\n\\n{result}\\n", encoding="utf-8")
"""

VALID_CSV = "unit_id,arm,value,include\nu1,A,1.0,yes\nu2,A,2.0,yes\nu3,B,3.0,yes\nu4,B,4.0,yes\n"
VALID_DESCRIPTION = "A small plant comparison.\nIndependent unit column: unit_id\n"


def _generated_case(
    *,
    source: str = VALID_SOURCE,
    data_csv: str = VALID_CSV,
    description: str = VALID_DESCRIPTION,
) -> dict[str, str]:
    return {
        "domain": "plant physiology",
        "analysis_py": source,
        "data_csv": data_csv,
        "data_description_md": description,
    }


def _fake_generation(run_name: str, index: int = 0) -> dict[str, Any]:
    return {
        "record_type": "development_wall_mining_generation",
        "record_purpose": corpus.RECORD_PURPOSE,
        "non_measurement_notice": corpus.NON_MEASUREMENT,
        "run_name": run_name,
        "case_identity": f"{run_name}:{index + 1:04d}",
        "case_index": index,
        "model_alias": corpus.MODEL_ALIAS,
        "session_id": f"session:{run_name}:{index}",
        "prompt_digest": semantic_digest({"prompt": index}),
        "argv_digest": semantic_digest({"argv": index}),
        "stdout_digest": semantic_digest({"stdout": index}),
        "stderr_digest": semantic_digest({"stderr": index}),
        "served_model_ids": ["claude-haiku-test"],
        "generated_at": "2026-08-15T00:00:00Z",
        "project_code_executed": False,
        "measurement_authority": "none",
    }


def _install_fake_claude(tmp_path: Path, monkeypatch: Any) -> list[list[str]]:
    binary = tmp_path / "claude"
    binary.write_text("stub", encoding="utf-8")
    monkeypatch.setattr(corpus, "CLAUDE_PINNED", binary)
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        calls.append(argv)
        envelope = {
            "result": json.dumps(_generated_case()),
            "modelUsage": {"claude-haiku-test": {}},
        }
        return subprocess.CompletedProcess(argv, 0, json.dumps(envelope).encode(), b"")

    monkeypatch.setattr(corpus.subprocess, "run", fake_run)
    return calls


def test_wall_mining_prompt_is_open_and_carries_only_study_authority() -> None:
    prompt = corpus._prompt(0, 40)
    folded = prompt.casefold()
    for forbidden in (
        "sc-referee",
        "error class",
        "recognizer",
        "role",
        "label",
        "blind",
        "catch",
        "miss",
        "expected outcome",
    ):
        assert forbidden not in folded
    assert "two independent groups" in folded
    assert "from scipy import stats" in prompt
    assert "stats.ttest_ind" in prompt
    assert "stats.mannwhitneyu" in prompt
    assert "Independent unit column: COLUMN" in prompt
    assert "exactly one direct call" in folded


def test_python311_ast_envelope_is_exact_and_recursively_default_deny(
    monkeypatch: Any,
) -> None:
    assert len(corpus._ADMITTED_AST_FIELDS) == 82
    assert all(cls._fields == fields for cls, fields in corpus._ADMITTED_AST_FIELDS.items())
    tree = ast.parse(VALID_SOURCE)
    assert corpus._validate_ast_envelope(tree)

    class Unknown(ast.AST):
        _fields = ()

    assert not corpus._validate_ast_envelope(Unknown())
    original = ast.Assign._fields
    monkeypatch.setattr(ast.Assign, "_fields", (*original, "future_field"))
    assert not corpus._validate_ast_envelope(tree)


def test_valid_helper_procedure_transport_is_occurrence_counted() -> None:
    assert corpus._procedure_transport(VALID_SOURCE) == (("scipy.stats.ttest_ind",), ())


@pytest.mark.parametrize(
    "import_statement",
    [
        "import stats",
        "import stats.helpers",
        "import math as stats",
    ],
)
def test_procedure_transport_refuses_imports_bound_to_stats(import_statement: str) -> None:
    source = f"from scipy import stats\n{import_statement}\nresult = stats.ttest_ind([1], [2])\n"
    assert corpus._procedure_transport(source) == (
        (),
        ("procedure-authority-root-not-closed",),
    )


def test_procedure_transport_accepts_nonreplacing_stats_import_alias() -> None:
    source = "from scipy import stats\nimport stats as other\nresult = stats.ttest_ind([1], [2])\n"
    assert corpus._procedure_transport(source) == (("scipy.stats.ttest_ind",), ())


@pytest.mark.parametrize(
    ("source", "expected_reasons"),
    [
        (
            "from scipy import stats\na=stats.ttest_ind([1],[2])\nb=stats.ttest_ind([1],[2])\n",
            (
                "procedure-authority-root-not-closed",
                "procedure-call-missing-or-ambiguous",
            ),
        ),
        (
            "from scipy import stats\na=stats.ttest_ind([1],[2])\nb=stats.mannwhitneyu([1],[2])\n",
            (
                "procedure-authority-root-not-closed",
                "procedure-call-missing-or-ambiguous",
            ),
        ),
        (
            "from scipy import stats\nstats = object()\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nstats: object\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nstats += 1\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\n(stats := object())\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\ndef f(stats):\n return stats\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nfor stats in []:\n pass\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nx=[1 for stats in []]\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nwith open('x') as stats:\n pass\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\ntry:\n pass\nexcept Exception as stats:\n pass\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\ndef stats():\n pass\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nclass stats:\n pass\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nf=lambda stats: stats\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nstats.ttest_ind=lambda a,b: 0\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nimport scipy as sp\nsp.stats.ttest_ind=lambda a,b: 0\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-import-not-canonical",),
        ),
        (
            "from scipy import stats\nimport scipy.stats as spstats\nspstats.ttest_ind=lambda a,b: 0\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-import-not-canonical",),
        ),
        (
            "from scipy.stats import ttest_ind\nr=ttest_ind([1],[2])\n",
            ("procedure-call-missing-or-ambiguous", "procedure-import-not-canonical"),
        ),
        (
            "import scipy as sp\nr=sp.stats.ttest_ind([1],[2])\n",
            ("procedure-call-missing-or-ambiguous", "procedure-import-not-canonical"),
        ),
        (
            "from scipy import stats\nf=stats.ttest_ind\nr=f([1],[2])\n",
            (
                "procedure-authority-root-not-closed",
                "procedure-call-missing-or-ambiguous",
            ),
        ),
        (
            "from scipy import stats\nr=stats.pearsonr([1],[2])\n",
            (
                "procedure-authority-root-not-closed",
                "procedure-call-missing-or-ambiguous",
            ),
        ),
        (
            "from scipy import stats\nx=1\n",
            ("procedure-call-missing-or-ambiguous",),
        ),
        (
            "if True:\n from scipy import stats\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-import-not-canonical",),
        ),
        (
            "from scipy import stats\nexec('x=1')\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nglobals()['x']=1\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nsetattr(object(),'x',1)\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nx=object().__dict__\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nx=e.tb_frame\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-authority-root-not-closed",),
        ),
        (
            "from scipy import stats\nimport importlib\nr=stats.ttest_ind([1],[2])\n",
            ("procedure-import-not-canonical",),
        ),
    ],
)
def test_procedure_transport_refuses_binding_import_and_dynamic_siblings(
    source: str, expected_reasons: tuple[str, ...]
) -> None:
    procedures, reasons = corpus._procedure_transport(source)
    assert procedures == ()
    assert reasons == expected_reasons


@pytest.mark.parametrize(
    "source",
    [
        "from scipy import stats\ndel stats\nr=stats.ttest_ind([1],[2])\n",
        "from scipy import stats\ndef f():\n global stats\nr=stats.ttest_ind([1],[2])\n",
        "from scipy import stats\ndef outer():\n x=1\n def inner():\n  nonlocal x\n  return x\n return inner\nr=stats.ttest_ind([1],[2])\n",
        "from scipy import stats\nasync def f():\n pass\nr=stats.ttest_ind([1],[2])\n",
        "from scipy import stats\nasync def f(xs):\n async for x in xs:\n  pass\nr=stats.ttest_ind([1],[2])\n",
        "from scipy import stats\nasync def f(x):\n async with x:\n  pass\nr=stats.ttest_ind([1],[2])\n",
        "from scipy import stats\nasync def f(x):\n return await x\nr=stats.ttest_ind([1],[2])\n",
        "from scipy import stats\ndef f():\n yield 1\nr=stats.ttest_ind([1],[2])\n",
        "from scipy import stats\ndef f():\n yield from []\nr=stats.ttest_ind([1],[2])\n",
        "from scipy import stats\nmatch 1:\n case 1: pass\nr=stats.ttest_ind([1],[2])\n",
        "from scipy import stats\ntry:\n pass\nexcept* Exception:\n pass\nr=stats.ttest_ind([1],[2])\n",
    ],
)
def test_explicitly_excluded_syntax_families_default_to_no_lock(source: str) -> None:
    assert corpus._procedure_transport(source) == (
        (),
        ("procedure-authority-ast-outside-safe-language",),
    )


def test_uncompilable_source_has_its_own_transport_diagnostic() -> None:
    assert corpus._procedure_transport("def broken(:\n") == (
        (),
        ("procedure-source-not-compilable",),
    )


@pytest.mark.parametrize(
    ("description", "data", "expected_reasons"),
    [
        ("No declaration\n", VALID_CSV.encode(), ("unit-declaration-missing",)),
        (
            "Independent unit column: unit_id\nIndependent unit column: unit_id\n",
            VALID_CSV.encode(),
            ("unit-declaration-duplicate-prefix",),
        ),
        (
            "independent unit column: unit_id\n",
            VALID_CSV.encode(),
            ("unit-declaration-syntax-outside-closed-grammar",),
        ),
        (
            VALID_DESCRIPTION,
            VALID_CSV.replace("unit_id", "Unit_ID").encode(),
            ("unit-column-not-in-csv-header",),
        ),
        (
            VALID_DESCRIPTION,
            b"unit_id,unit_id,value\nu1,A,1\n",
            ("unit-column-duplicated-in-csv-header",),
        ),
        (VALID_DESCRIPTION, b"unit_id,,value\nu1,A,1\n", ("unit-csv-invalid-or-incomplete",)),
        (VALID_DESCRIPTION, b"unit_id,arm,value\n,A,1\n", ("unit-csv-invalid-or-incomplete",)),
        (VALID_DESCRIPTION, b"unit_id,arm,value\nu1,A\n", ("unit-csv-invalid-or-incomplete",)),
        (VALID_DESCRIPTION, b"unit_id,arm\nu1,A,extra\n", ("unit-csv-invalid-or-incomplete",)),
        (VALID_DESCRIPTION, b"unit_id,arm\n\xff,A\n", ("unit-csv-invalid-or-incomplete",)),
        (VALID_DESCRIPTION, b'unit_id,arm\n"u1,A\n', ("unit-csv-invalid-or-incomplete",)),
        (VALID_DESCRIPTION, b"unit_id,arm\nu1,A\x00\n", ("unit-csv-invalid-or-incomplete",)),
        (VALID_DESCRIPTION, b"unit_id,arm\n", ("unit-csv-invalid-or-incomplete",)),
    ],
)
def test_strict_whole_stream_csv_and_declaration_siblings(
    description: str, data: bytes, expected_reasons: tuple[str, ...]
) -> None:
    unit, reasons = corpus._unit_transport(description, data)
    assert unit is None
    assert reasons == expected_reasons


def test_strict_csv_accepts_a_complete_quoted_multiline_stream() -> None:
    data = b'unit_id,note\nu1,"first\nline"\nu2,second\n'
    assert corpus._unit_transport(VALID_DESCRIPTION, data) == ("unit_id", ())


@pytest.mark.parametrize(
    "run_name",
    [
        "",
        "run-",
        "other-1",
        "Run-one",
        "run-UPPER",
        "run-a.b",
        "run-../escape",
        "run-a/b",
        "run-a\\b",
        "run-" + "a" * 64,
    ],
)
def test_invalid_run_names_fail_before_binary_filesystem_or_model(
    tmp_path: Path, monkeypatch: Any, run_name: str
) -> None:
    called = False

    def fake_is_file() -> bool:
        nonlocal called
        called = True
        return True

    class BinaryProbe:
        is_file = staticmethod(fake_is_file)

    monkeypatch.setattr(corpus, "CLAUDE_PINNED", BinaryProbe())
    with pytest.raises(ValueError):
        corpus.build_corpus(tmp_path, 1, run_name)
    assert not called
    assert not (tmp_path / "evaluation").exists()


def test_invalid_count_fails_before_binary_filesystem_or_model(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setattr(corpus, "CLAUDE_PINNED", Path("must-not-be-inspected"))
    with pytest.raises(ValueError, match="count"):
        corpus.build_corpus(tmp_path, 0, "run-zero")
    assert not (tmp_path / "evaluation").exists()


def test_symlinked_corpus_parent_is_refused_before_generation(
    tmp_path: Path, monkeypatch: Any
) -> None:
    calls = _install_fake_claude(tmp_path, monkeypatch)
    outside = tmp_path / "outside"
    outside.mkdir()
    parent = tmp_path / "evaluation/development"
    parent.mkdir(parents=True)
    (parent / "wall-mining-corpus").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="unsafe"):
        corpus.build_corpus(tmp_path, 1, "run-safe")
    assert calls == []
    assert list(outside.iterdir()) == []


def test_existing_and_dangling_run_paths_are_refused_before_generation(
    tmp_path: Path, monkeypatch: Any
) -> None:
    calls = _install_fake_claude(tmp_path, monkeypatch)
    corpus_root = tmp_path / corpus.CORPUS_ROOT
    corpus_root.mkdir(parents=True)
    (corpus_root / "run-existing").mkdir()
    with pytest.raises(FileExistsError):
        corpus.build_corpus(tmp_path, 1, "run-existing")
    (corpus_root / "run-dangling").symlink_to(tmp_path / "missing-target")
    assert os.path.lexists(corpus_root / "run-dangling")
    with pytest.raises(FileExistsError):
        corpus.build_corpus(tmp_path, 1, "run-dangling")
    assert calls == []


def test_valid_fixture_compiles_and_executes_in_pinned_scipy114(tmp_path: Path) -> None:
    assert PINNED_SCIPY_PYTHON.is_file()
    (tmp_path / "workflow").mkdir()
    (tmp_path / "data").mkdir()
    source_path = tmp_path / "workflow/analysis.py"
    source_path.write_text(VALID_SOURCE, encoding="utf-8")
    (tmp_path / "data/input.csv").write_text(VALID_CSV, encoding="utf-8")
    compile(VALID_SOURCE, str(source_path), "exec")
    completed = subprocess.run(
        [str(PINNED_SCIPY_PYTHON), str(source_path)],
        cwd=tmp_path,
        capture_output=True,
        check=False,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    report = (tmp_path / "results/report.md").read_text(encoding="utf-8")
    assert report.startswith("# Result\n")
    assert "TtestResult" in report


def test_valid_transport_observes_exact_shadow_outcome(tmp_path: Path) -> None:
    run_root = tmp_path / "run-observed"
    run_root.mkdir()
    shadow = corpus._write_case(
        run_root,
        "run-observed",
        0,
        _generated_case(),
        _fake_generation("run-observed"),
    )
    translation = json.loads((run_root / "cases/0001/lock-translation.json").read_text())
    assert translation["translation_outcome"] == "lock-projected"
    assert translation["translation_reasons"] == []
    assert translation["v1_translation_outcome"] is None
    assert translation["v1_lock_digest"] is None
    assert translation["v2_translation_outcome"] == "lock-projected"
    assert translation["v2_translation_reasons"] == []
    assert translation["v2_lock_digest"] == translation["lock_digest"]
    assert translation["translation_version"] == "2.0.0-development"
    assert translation["description_content_digest"] == sha256_digest(VALID_DESCRIPTION.encode())
    assert translation["input_content_digest"] == sha256_digest(VALID_CSV.encode())
    assert translation["parsed_header_digest"] == semantic_digest(
        ["unit_id", "arm", "value", "include"]
    )
    assert translation["lock_projection_digest"] == translation["lock_digest"]
    assert translation["v2_lock_projection_digest"] == translation["lock_digest"]
    assert translation["v2_translation_receipt"] == {
        "declaration_byte_span": [26, 58],
        "declaration_form_id": "wall-census-standalone-v1",
        "extracted_token": "unit_id",
        "logical_header": ["unit_id", "arm", "value", "include"],
        "parsed_header_digest": semantic_digest(["unit_id", "arm", "value", "include"]),
        "quoted_declaration": "Independent unit column: unit_id",
        "translation_version": "2.0.0-development",
    }
    payload = shadow["shadow_payload"]
    assert payload["outcome"] == "unsupported"
    assert payload["reason_code"] == "module-constant-not-closed"
    assert payload["abstention_reasons"] == ["module-constant-not-closed"]


def test_invalid_transport_has_no_lock_and_observed_authority_free_question(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run-invalid"
    run_root.mkdir()
    invalid = _generated_case(description="No unit declaration.\n")
    shadow = corpus._write_case(
        run_root,
        "run-invalid",
        0,
        invalid,
        _fake_generation("run-invalid"),
    )
    case_root = run_root / "cases/0001"
    assert not (case_root / "authorization-lock.json").exists()
    translation = json.loads((case_root / "lock-translation.json").read_text())
    assert translation["translation_outcome"] == "no-lock"
    assert translation["translation_reasons"] == ["unit-declaration-missing"]
    payload = shadow["shadow_payload"]
    assert payload["outcome"] == "question"
    assert payload["reason_code"] == "independent-unit-definition-unresolved"
    assert payload["abstention_reasons"] == []


def test_default_bound_stats_import_writes_no_lock_and_passes_authority_free_context(
    tmp_path: Path, monkeypatch: Any
) -> None:
    run_root = tmp_path / "run-default-bound-import"
    run_root.mkdir()
    inspected: list[FrozenInspectionContext] = []

    def inspect(_adapter: Any, context: FrozenInspectionContext) -> dict[str, Any]:
        inspected.append(context)
        return {"outcome": "question", "abstention_reasons": []}

    monkeypatch.setattr(corpus.DependenceRecognitionV2ShadowAdapter, "inspect", inspect)
    source = VALID_SOURCE.replace(
        "from scipy import stats\n", "from scipy import stats\nimport stats\n"
    )
    corpus._write_case(
        run_root,
        "run-default-bound-import",
        0,
        _generated_case(source=source),
        _fake_generation("run-default-bound-import"),
    )

    case_root = run_root / "cases/0001"
    assert not (case_root / "authorization-lock.json").exists()
    translation = json.loads((case_root / "lock-translation.json").read_text())
    assert translation["translation_outcome"] == "no-lock"
    assert translation["translation_reasons"] == ["procedure-authority-root-not-closed"]
    assert translation["v2_translation_receipt"] is None
    assert len(inspected) == 1
    authority_types = {"analysis", "procedure", "result", "human_method_authorization"}
    assert all(
        record.ref.record_type not in authority_types for record in inspected[0].base_records
    )


def test_run_bound_lock_translation_shadow_and_inner_refs_replay_exactly(
    tmp_path: Path, monkeypatch: Any
) -> None:
    calls = _install_fake_claude(tmp_path, monkeypatch)
    inspected: list[FrozenInspectionContext] = []

    def inspect(_adapter: Any, context: FrozenInspectionContext) -> dict[str, Any]:
        inspected.append(context)
        return {"outcome": "question", "abstention_reasons": ["observed-wall"]}

    monkeypatch.setattr(corpus.DependenceRecognitionV2ShadowAdapter, "inspect", inspect)
    roots = [
        corpus.build_corpus(tmp_path, 1, "run-alpha"),
        corpus.build_corpus(tmp_path, 1, "run-beta"),
    ]
    assert len(calls) == 2
    assert len(inspected) == 2

    generations = [json.loads((root / "cases/0001/generation.json").read_text()) for root in roots]
    locks = [
        json.loads((root / "cases/0001/authorization-lock.json").read_text()) for root in roots
    ]
    translations = [
        json.loads((root / "cases/0001/lock-translation.json").read_text()) for root in roots
    ]
    shadows = [json.loads((root / "cases/0001/shadow-result.json").read_text()) for root in roots]

    assert generations[0]["session_id"] != generations[1]["session_id"]
    assert locks[0]["lock_digest"] != locks[1]["lock_digest"]
    assert translations[0]["translation_digest"] != translations[1]["translation_digest"]
    assert shadows[0]["observation_digest"] != shadows[1]["observation_digest"]
    assert inspected[0].snapshot_digest != inspected[1].snapshot_digest

    for position, run_name in enumerate(("run-alpha", "run-beta")):
        identity = f"{run_name}:0001"
        case_id = f"case:wall-mining:{identity}"
        root = roots[position]
        context = inspected[position]
        generation = generations[position]
        lock = locks[position]
        translation = translations[position]
        shadow = shadows[position]
        base_context = corpus._context(VALID_SOURCE, VALID_CSV.encode(), run_name, identity)

        assert generation["run_name"] == run_name
        assert generation["case_identity"] == identity
        assert lock["case_id"] == case_id
        assert lock["snapshot_digest"] == base_context.snapshot_digest == context.snapshot_digest
        for record in base_context.base_records:
            assert identity in record.ref.record_id
        for document in base_context.documents:
            assert identity in document.file_ref.record_id
            assert identity in document.parser_result_ref.record_id
        for material in base_context.material_inputs:
            assert identity in material.file_ref.record_id
            assert identity in material.asset_identity_ref.record_id

        authority_types = {"analysis", "procedure", "result", "human_method_authorization"}
        authority_records = [
            item for item in context.base_records if item.ref.record_type in authority_types
        ]
        assert len(authority_records) == 4
        assert {item.ref.record_type for item in authority_records} == authority_types
        for lock_record in lock["records"]:
            assert identity in lock_record["record_id"]
            matches = [
                item
                for item in authority_records
                if item.ref.record_type == lock_record["record_type"]
                and item.ref.record_id == lock_record["record_id"]
            ]
            assert len(matches) == 1
            assert matches[0].canonical_payload == canonical_json(lock_record).encode()
        humans = [
            json.loads(item.canonical_payload)
            for item in context.base_records
            if item.ref.record_type == "human_method_authorization"
        ]
        assert len(humans) == 1
        assert humans[0]["actor_id"] == lock["approval"]["actor_id"]
        assert "translator" not in humans[0]["actor_id"]

        lock_bytes = (root / "cases/0001/authorization-lock.json").read_bytes()
        assert translation["authorization_lock_path"] == "cases/0001/authorization-lock.json"
        assert translation["authorization_case_id"] == case_id
        assert translation["authorization_snapshot_digest"] == lock["snapshot_digest"]
        assert translation["lock_digest"] == lock["lock_digest"]
        assert (
            translation["approved_projection_digest"]
            == lock["approval"]["approved_projection_digest"]
        )
        assert translation["authorization_lock_content_digest"] == sha256_digest(lock_bytes)
        replay = dict(translation)
        digest = replay.pop("translation_digest")
        assert digest == semantic_digest(replay)
        assert shadow["run_name"] == run_name
        assert shadow["case_identity"] == identity
        assert shadow["lock_digest"] == lock["lock_digest"]
        assert shadow["translation_digest"] == translation["translation_digest"]
        observation_replay = dict(shadow)
        observation_digest = observation_replay.pop("observation_digest")
        assert observation_digest == semantic_digest(observation_replay)

    base_contexts = [
        corpus._context(VALID_SOURCE, VALID_CSV.encode(), "run-alpha", "run-alpha:0001"),
        corpus._context(VALID_SOURCE, VALID_CSV.encode(), "run-beta", "run-beta:0001"),
    ]
    assert (
        base_contexts[0].documents[0].content_digest == base_contexts[1].documents[0].content_digest
    )
    assert (
        base_contexts[0].material_inputs[0].content_digest
        == base_contexts[1].material_inputs[0].content_digest
    )
    assert (
        base_contexts[0].material_inputs[1].content_digest
        == base_contexts[1].material_inputs[1].content_digest
    )


def test_census_keeps_transport_refusals_separate_from_recognizer_walls(
    tmp_path: Path, monkeypatch: Any
) -> None:
    calls = _install_fake_claude(tmp_path, monkeypatch)
    generated = [_generated_case(), _generated_case(description="No declaration.\n")]

    def fake_call(run_name: str, index: int, count: int) -> tuple[dict[str, Any], dict[str, Any]]:
        assert count == 2
        return generated[index], _fake_generation(run_name, index)

    monkeypatch.setattr(corpus, "_call_haiku", fake_call)
    run_root = corpus.build_corpus(tmp_path, 2, "run-frequency")
    assert calls == []
    census = json.loads((run_root / "wall-frequency-census.json").read_text())
    assert census["case_count"] == 2
    assert census["generation_calls"] == 2
    assert census["measurement_authority"] == "none"
    assert census["transport_failure_frequencies"] == {"unit-declaration-missing": 1}
    assert "independent-unit-definition-unresolved" not in census["wall_frequencies"]
    assert sum(census["wall_frequencies"].values()) >= 1
    for path in run_root.rglob("*.json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        if path.name != "authorization-lock.json":
            assert value["record_purpose"] == corpus.RECORD_PURPOSE, path
    markdown = (run_root / "wall-frequency-census.md").read_text(encoding="utf-8")
    assert "non-measurement" in markdown
    assert "Transport refusal" in markdown
    assert corpus.MAX_CONCURRENCY == 3
    assert not (tmp_path / "evaluation/qualification").exists()


def test_build_uses_one_model_call_per_case_and_preserves_generation_isolation(
    tmp_path: Path, monkeypatch: Any
) -> None:
    calls = _install_fake_claude(tmp_path, monkeypatch)
    run_root = corpus.build_corpus(tmp_path, 2, "run-isolation")
    assert len(calls) == 2
    assert all(argv[argv.index("--model") + 1] == "haiku" for argv in calls)
    assert all(argv[argv.index("--tools") + 1] == "" for argv in calls)
    generations = [
        json.loads(path.read_text()) for path in run_root.glob("cases/*/generation.json")
    ]
    assert all(item["project_code_executed"] is False for item in generations)
    assert all(item["measurement_authority"] == "none" for item in generations)
    assert all(item["run_name"] == "run-isolation" for item in generations)
