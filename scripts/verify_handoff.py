from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from sc_referee.audit_diff import verify_audit_diff  # noqa: E402
from sc_referee.cache_auth import (  # noqa: E402
    CACHE_AUTHENTICATION_ENV,
    encode_cache_authentication_key,
)
from sc_referee.core.deadline_ledger import (  # noqa: E402
    LEDGER_FILENAME,
    load_deadline_ledger,
)
from sc_referee.version import SCHEMA_VERSION, __version__  # noqa: E402

_HANDOFF_CACHE_AUTHENTICATION_KEY = encode_cache_authentication_key(secrets.token_bytes(32))
V014_TO_V015_TARGET_SCHEMA_ROOT = "reference/schemas-v0.15.0"
V015_TO_V016_TARGET_SCHEMA_ROOT = "reference/schemas-v0.16.0"
V016_TO_V017_TARGET_SCHEMA_ROOT = "reference/schemas-v0.17.0"
V017_TO_V018_TARGET_SCHEMA_ROOT = "reference/schemas-v0.18.0"
_V1_1_QUALIFICATION_MODULES = frozenset(
    {
        "sc_referee_evaluation/prospective_selected_result_verifier.py",
        "sc_referee_evaluation/qualification_identity.py",
        "sc_referee_evaluation/selected_result_qualification_io.py",
        "sc_referee_evaluation/selected_result_qualification_oracle.py",
        "sc_referee_evaluation/selected_result_qualification_runner.py",
        "sc_referee_evaluation/selected_result_qualification_target_worker.py",
        "sc_referee_evaluation/selected_result_qualification_trust.py",
        "sc_referee_evaluation/selected_result_semantic_review.py",
        "sc_referee_evaluation/selected_result_verifier_qualification.py",
    }
)
_V1_1_QUALIFICATION_RESOURCE_ROOT = (
    "sc_referee_evaluation/qualification_resources/selected_result_v1_1"
)
_V1_1_QUALIFICATION_RESOURCES = frozenset(
    {
        f"{_V1_1_QUALIFICATION_RESOURCE_ROOT}/__init__.py",
        f"{_V1_1_QUALIFICATION_RESOURCE_ROOT}/case-author-prompt.txt",
        f"{_V1_1_QUALIFICATION_RESOURCE_ROOT}/comparison-prompt.txt",
        f"{_V1_1_QUALIFICATION_RESOURCE_ROOT}/provider-pack-schema.json",
        f"{_V1_1_QUALIFICATION_RESOURCE_ROOT}/semantic-review-contract.json",
        f"{_V1_1_QUALIFICATION_RESOURCE_ROOT}/semantic-validator-prompt.txt",
        f"{_V1_1_QUALIFICATION_RESOURCE_ROOT}/target-authorization-schema.json",
        f"{_V1_1_QUALIFICATION_RESOURCE_ROOT}/target-runner-prompt.txt",
        f"{_V1_1_QUALIFICATION_RESOURCE_ROOT}/validation-runner-prompt.txt",
    }
)
_V1_1_QUALIFICATION_ENTRY_POINTS = {
    "sc-referee-eval-selected-result": (
        "sc_referee_evaluation.selected_result_qualification_runner:entrypoint"
    ),
    "sc-referee-eval-selected-result-target-worker": (
        "sc_referee_evaluation.selected_result_qualification_target_worker:entrypoint"
    ),
}


def run(*args: str) -> None:
    env = dict(os.environ)
    env.setdefault(CACHE_AUTHENTICATION_ENV, _HANDOFF_CACHE_AUTHENTICATION_KEY)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(SRC) + (os.pathsep + existing if existing else "")
    subprocess.run([sys.executable, *args], cwd=ROOT, env=env, check=True)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_built_wheel() -> None:
    with tempfile.TemporaryDirectory(prefix="sc-referee-wheel-") as temp:
        temp_root = Path(temp)
        wheel_root = temp_root / "wheel"
        install_root = temp_root / "install"
        wheel_root.mkdir()
        run(
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            ".",
            "--wheel-dir",
            str(wheel_root),
        )
        wheels = list(wheel_root.glob("sc_referee-*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(f"Expected one built wheel, found {len(wheels)}")
        with zipfile.ZipFile(wheels[0]) as archive:
            wheel_names = archive.namelist()
            if any(name.startswith("sc_referee_evaluation/") for name in wheel_names):
                raise RuntimeError("Production wheel contains answer-side evaluation code")
            required_r_resources = {
                "sc_referee/resources/r-helper/base_parse_data.R",
                "sc_referee/resources/third-party/tree-sitter-r/LICENSE.txt",
                "sc_referee/resources/third-party/tree-sitter-r/provenance.json",
            }
            if not required_r_resources.issubset(wheel_names):
                raise RuntimeError("Production wheel omitted R parser provenance or helper files")
            if "sc_referee/relation_case.py" not in wheel_names:
                raise RuntimeError("Production wheel omitted the generic relation-case seam")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--target",
                str(install_root),
                str(wheels[0]),
            ],
            cwd=ROOT,
            check=True,
        )
        verification_code = "\n".join(
            [
                "import os, sys",
                "from pathlib import Path",
                f"sys.path.insert(0, {str(install_root)!r})",
                f"os.chdir({str(temp_root)!r})",
                "import sc_referee",
                "from typer.testing import CliRunner",
                "from sc_referee.capability_matrix import (",
                "    default_capability_manifest_root,",
                "    validate_capability_matrix,",
                "    write_capability_matrix,",
                ")",
                "from sc_referee.cli import _default_schema_root, app",
                "from sc_referee.controller import run_audit, run_demo",
                "from sc_referee.method_contract_run import run_method_contract",
                "from sc_referee.relation_case import evaluate_closed_relation",
                "from sc_referee.records.schema_registry import LocalSchemaRegistry",
                "from sc_referee.ro_crate import export_ro_crate, validate_ro_crate",
                "from sc_referee.scientific_checks.profiles import scientific_check_release_registry",
                f"assert sc_referee.__version__ == {__version__!r}",
                f"installed = Path({str(install_root)!r}).resolve()",
                "assert Path(sc_referee.__file__).resolve().is_relative_to(installed)",
                "root = _default_schema_root()",
                "assert root.resolve().is_relative_to(installed)",
                "assert LocalSchemaRegistry(root).validate_example_directory() == 79",
                "manifest_root = default_capability_manifest_root()",
                "assert manifest_root.resolve().is_relative_to(installed)",
                f"capability = Path({str(temp_root)!r}) / 'capability-matrix.json'",
                "generated = write_capability_matrix(capability, manifest_root, root)",
                "assert validate_capability_matrix(capability, manifest_root, root) == generated",
                "assert len(generated['entries']) == 16",
                "obligation = next(entry for entry in generated['entries'] if entry['entry_id'] == 'capability:bounded-expected-count-unresolved-obligation-v1')",
                "assert obligation['detectors'] == []",
                "assert obligation['operation_scope'] == ['bounded_expected_count_unresolved_obligation_v1']",
                "assert any(entry['language'] == 'delimited_table' for entry in generated['entries'])",
                "assert any(entry['language'] == 'nextflow_trace' for entry in generated['entries'])",
                "r_entries = [entry for entry in generated['entries'] if entry['language'] == 'r']",
                "assert {entry['package'] for entry in r_entries} == {'DESeq2', 'edgeR', 'limma'}",
                "assert all(entry['detectors'] == [] for entry in r_entries)",
                "assert all(entry['tested_versions'] == [] and entry['inferred_compatibility'] == [] for entry in r_entries)",
                "notebook_entry = next(entry for entry in generated['entries'] if entry['language'] == 'jupyter_notebook')",
                "assert notebook_entry['detectors'] == []",
                "assert notebook_entry['operation_extraction'] == 'not_started'",
                "quarto_entry = next(entry for entry in generated['entries'] if entry['language'] == 'quarto')",
                "assert quarto_entry['detectors'] == []",
                "assert quarto_entry['operation_extraction'] == 'not_started'",
                "bridge_entry = next(entry for entry in generated['entries'] if entry['language'] == 'container_cell')",
                "assert bridge_entry['detectors'] == []",
                "assert bridge_entry['operation_extraction'] == 'partial'",
                "assert bridge_entry['semantic_modeling'] == 'not_started'",
                "detectors = [detector for entry in generated['entries'] for detector in entry['detectors']]",
                "assert {item['detector_id'] for item in detectors} == {",
                "    'detector:bounded-analysis-method-conflict',",
                "    'detector:bounded-feature-identifier-identity',",
                "    'detector:bounded-report-mean-direction',",
                "    'detector:bounded-reported-method-contract-conflict',",
                "}",
                "assert all(item['maturity'] == 'experimental' for item in detectors)",
                "assert all(item['qualification_ref'] is None for item in detectors)",
                "assert callable(evaluate_closed_relation)",
                "assert 'check:complete-domain-exposure-denominator' in {module.manifest.check_id for module in scientific_check_release_registry().modules}",
                "help_result = CliRunner().invoke(app, ['--help'])",
                "assert help_result.exit_code == 0",
                "assert all(command not in help_result.output for command in (",
                "    'probe-execution-capability', 'request-execution',",
                "    'authorize-execution', 'execute-authorized',",
                "))",
                "assert 'method-contract' in help_result.output",
                f"method_project = Path({str(temp_root)!r}) / 'method-project'",
                "method_project.mkdir()",
                "(method_project / 'task.md').write_text('Define the expected-count method.\\n', encoding='utf-8')",
                f"method_output = Path({str(temp_root)!r}) / 'method-contract'",
                "method_bundle = run_method_contract(method_project, 'task.md', method_output, root)",
                "assert method_bundle['claims'] == []",
                "assert method_bundle['publication_surfaces'] == []",
                "assert len(method_bundle['material_questions']) == 1",
                f"large_project = Path({str(temp_root)!r}) / 'large-data-project'",
                "large_project.mkdir()",
                "(large_project / 'report.md').write_text(",
                "    '# Results\\n\\nTreatment increased yield relative to control.\\n',",
                "    encoding='utf-8',",
                ")",
                "execution_marker = large_project / 'must-not-exist'",
                "(large_project / 'existing-results.csv').write_text(",
                "    'contrast,effect\\ntreated-control,1.25\\n',",
                "    encoding='utf-8',",
                ")",
                "(large_project / 'analysis.py').write_text(",
                "    f\"from pathlib import Path\\nPath({str(execution_marker)!r}).write_text('executed')\\n\",",
                "    encoding='utf-8',",
                ")",
                "(large_project / 'analysis.R').write_text(",
                "    f\"system('touch {execution_marker.as_posix()}')\\n\",",
                "    encoding='utf-8',",
                ")",
                "(large_project / 'analysis.ipynb').write_text(",
                "    __import__('json').dumps({'cells': [{'cell_type': 'code', 'id': 'inert', 'metadata': {}, 'source': \"raise RuntimeError('must remain inert')\\n\", 'execution_count': None, 'outputs': []}], 'metadata': {'language_info': {'name': 'python'}}, 'nbformat': 4, 'nbformat_minor': 5}),",
                "    encoding='utf-8',",
                ")",
                "(large_project / 'analysis.qmd').write_text(",
                "    '```{python}\\nraise RuntimeError(\"must remain inert\")\\n```\\n',",
                "    encoding='utf-8',",
                ")",
                "(large_project / 'trace.txt').write_text(",
                "    'task_id\\thash\\tnative_id\\tname\\tstatus\\texit\\tsubmit\\tduration\\trealtime\\t%cpu\\tpeak_rss\\tpeak_vmem\\trchar\\twchar\\n'",
                "    '19\\t45/ab752a\\t2032\\tanalysis\\tCOMPLETED\\t0\\t2026-07-29 16:33:16.288\\t1m\\t5s\\t0.0%\\t29.8 MB\\t354 MB\\t33.3 MB\\t0\\n',",
                "    encoding='utf-8',",
                ")",
                "analysis_source = large_project / 'analysis.py'",
                "analysis_source.write_text(",
                "    analysis_source.read_text(encoding='utf-8') + \"Path('existing-results.csv').write_text('runtime output')\\n\",",
                "    encoding='utf-8',",
                ")",
                "large_asset = large_project / 'ten-billion-byte-dataset.h5ad'",
                "with large_asset.open('wb') as handle: handle.truncate(10_000_000_000)",
                f"large_audit = Path({str(temp_root)!r}) / 'large-data-audit'",
                "large_bundle = run_audit(large_project, large_audit, root, report='report.md')",
                "assert not execution_marker.exists()",
                "assert large_bundle['findings'] == []",
                "r_results = [item for item in large_bundle['parser_results'] if item['source_ref']['path'] == 'analysis.R']",
                "assert {item['parser_id'] for item in r_results} == {'parser:r-tree-sitter-inventory', 'parser:r-base-parse-data'}",
                "assert next(item for item in r_results if item['parser_id'] == 'parser:r-tree-sitter-inventory')['state'] == 'parsed'",
                "large_lock = __import__('json').loads((large_audit / 'semantic.lock.json').read_text(encoding='utf-8'))",
                "assert 'analysis.R' in large_lock['cache_summary']['uncacheable_paths']",
                "notebook_result = next(item for item in large_bundle['parser_results'] if item['source_ref']['path'] == 'analysis.ipynb' and item['parser_id'] == 'parser:jupyter-notebook-inventory')",
                "assert notebook_result['parser_id'] == 'parser:jupyter-notebook-inventory'",
                "assert notebook_result['state'] == 'parsed'",
                "quarto_result = next(item for item in large_bundle['parser_results'] if item['source_ref']['path'] == 'analysis.qmd' and item['parser_id'] == 'parser:quarto-source-inventory')",
                "assert quarto_result['parser_id'] == 'parser:quarto-source-inventory'",
                "assert quarto_result['state'] == 'parsed'",
                "cell_python_results = [item for item in large_bundle['parser_results'] if item['parser_id'] == 'parser:python-ast-tokenize' and item['source_ref'].get('source_kind') in {'notebook_cell', 'document_chunk'}]",
                "assert {item['source_ref']['source_kind'] for item in cell_python_results} == {'notebook_cell', 'document_chunk'}",
                "assert all(item['extensions']['x-virtual-source']['executes_project_code'] is False for item in cell_python_results)",
                "assert len(large_bundle['detector_results']) == 1",
                "assert large_bundle['detector_results'][0]['detector_maturity'] == 'experimental'",
                "assert large_bundle['repository_snapshots'][0]['extensions']['x-identity-byte-reads']['sampled_fingerprint'] == 12_288",
                "assert any(identity['tier'] == 'weak_fingerprint' for identity in large_bundle['asset_identities'])",
                "table = next(item for item in large_bundle['data_assets'] if item.get('path') == 'existing-results.csv')",
                "assert table['role'] == 'output' and table['structure_status'] == 'partial'",
                "assert {item['observed_name'] for item in large_bundle['variables']} >= {'contrast', 'effect'}",
                "imported = [item for item in large_bundle['executions'] if item['execution_kind'] == 'imported']",
                "assert len(imported) == 1 and imported[0]['identity_strength'] == 'imported_weak'",
                "assert imported[0]['input_refs'] == [] and imported[0]['output_refs'] == []",
                "assert imported[0]['execution_id'] not in repr(large_bundle['claims'])",
                "assert not (large_audit / 'observed' / 'snapshot' / 'materialized' / large_asset.name).exists()",
                "declared_digest = 'sha256:' + 'e' * 64",
                "(large_project / 'checksums.sha256').write_text(",
                "    f\"{declared_digest.removeprefix('sha256:')}  {large_asset.name}\\n\",",
                "    encoding='utf-8',",
                ")",
                f"manifest_audit = Path({str(temp_root)!r}) / 'manifest-data-audit'",
                "manifest_bundle = run_audit(large_project, manifest_audit, root, report='report.md')",
                "manifest_file = next(item for item in manifest_bundle['file_records'] if item['path'] == large_asset.name)",
                "manifest_identity = next(item for item in manifest_bundle['asset_identities'] if item['asset_ref']['record_id'] == manifest_file['file_record_id'])",
                "assert manifest_identity['tier'] == 'manifest'",
                "assert manifest_identity['identity_evidence']['manifest_digest'] == declared_digest",
                "assert 'does not verify the target bytes' in manifest_identity['limitations'][0]",
                "assert not (manifest_audit / 'observed' / 'snapshot' / 'materialized' / large_asset.name).exists()",
                f"audit = Path({str(temp_root)!r}) / 'wheel-audit'",
                f"crate = Path({str(temp_root)!r}) / 'wheel-audit.zip'",
                f"run_demo(Path({str(ROOT)!r}) / 'examples' / 'walking-skeleton', audit, root)",
                "exported = export_ro_crate(",
                "    audit, crate, root,",
                "    author_name='Wheel handoff verifier',",
                "    license_uri='https://spdx.org/licenses/Apache-2.0.html',",
                "    license_name='Apache License 2.0',",
                ")",
                "assert validate_ro_crate(crate, root) == exported",
            ]
        )
        subprocess.run([sys.executable, "-c", verification_code], cwd=temp_root, check=True)


def _install_evaluation_smoke_wheels(
    core_wheel: Path,
    evaluation_wheel: Path,
    install_root: Path,
) -> None:
    for wheel in (core_wheel, evaluation_wheel):
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--target",
                str(install_root),
                str(wheel),
            ],
            cwd=ROOT,
            check=True,
        )


def _install_evaluation_smoke_venv(
    core_wheel: Path,
    evaluation_wheel: Path,
    environment_root: Path,
) -> Path:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "venv",
            str(environment_root),
        ],
        cwd=ROOT,
        check=True,
    )
    scripts_root = environment_root / ("Scripts" if os.name == "nt" else "bin")
    python_name = "python.exe" if os.name == "nt" else "python"
    environment_python = scripts_root / python_name
    if os.name == "nt":
        environment_site_packages = environment_root / "Lib" / "site-packages"
    else:
        python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
        environment_site_packages = environment_root / "lib" / python_version / "site-packages"
    dependency_roots = sorted(
        {
            str(Path(item).resolve())
            for item in sys.path
            if item and "site-packages" in Path(item).parts and Path(item).is_dir()
        }
    )
    if not dependency_roots:
        raise RuntimeError("Evaluation-wheel smoke environment has no dependency runtime.")
    (environment_site_packages / "handoff-dependency-runtime.pth").write_text(
        "".join(f"{item}\n" for item in dependency_roots),
        encoding="utf-8",
    )
    for wheel in (core_wheel, evaluation_wheel):
        subprocess.run(
            [
                str(environment_python),
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--force-reinstall",
                str(wheel),
            ],
            cwd=ROOT,
            check=True,
        )
    return environment_python


def _clean_subprocess_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


def _build_local_wheel(source: Path, wheel_root: Path) -> None:
    uv_executable = shutil.which("uv")
    if uv_executable is not None:
        subprocess.run(
            [
                uv_executable,
                "build",
                "--wheel",
                "--no-build-isolation",
                "--python",
                str(getattr(sys, "_base_executable", sys.executable)),
                "--out-dir",
                str(wheel_root),
                str(source),
            ],
            cwd=ROOT,
            check=True,
        )
        return
    run(
        "-m",
        "pip",
        "wheel",
        "--no-deps",
        "--no-build-isolation",
        str(source),
        "--wheel-dir",
        str(wheel_root),
    )


def verify_built_evaluation_wheel() -> None:
    with tempfile.TemporaryDirectory(prefix="sc-referee-evaluation-wheel-") as temp:
        temp_root = Path(temp)
        wheel_root = temp_root / "wheel"
        wheel_root.mkdir()
        _build_local_wheel(ROOT, wheel_root)
        _build_local_wheel(ROOT / "evaluation", wheel_root)
        wheels = list(wheel_root.glob("sc_referee_evaluation-*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(f"Expected one evaluation wheel, found {len(wheels)}")
        core_wheels = list(wheel_root.glob("sc_referee-*.whl"))
        if len(core_wheels) != 1:
            raise RuntimeError(f"Expected one production wheel, found {len(core_wheels)}")
        with zipfile.ZipFile(wheels[0]) as archive:
            names = set(archive.namelist())
            if "sc_referee_evaluation/validation.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its validation module")
            if "sc_referee_evaluation/workspace.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its blind-workspace module")
            if "sc_referee_evaluation/review_protocol.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its review-protocol module")
            if "sc_referee_evaluation/comparison.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its detector-comparison module")
            if "sc_referee_evaluation/capture.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its review-capture module")
            if "sc_referee_evaluation/grader.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its exact-JSON grader module")
            if "sc_referee_evaluation/snapshot_evidence.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its snapshot-evidence module")
            if "sc_referee_evaluation/fixture.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its fixture-generation module")
            if "sc_referee_evaluation/root_cause.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its root-cause reconciliation module")
            if "sc_referee_evaluation/stage3.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its Stage-3 reconciliation module")
            if "sc_referee_evaluation/candidate.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its candidate-projection module")
            if "sc_referee_evaluation/metrics.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its exact-metric module")
            if "sc_referee_evaluation/corpus.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its public-corpus preflight module")
            if "sc_referee_evaluation/genebench_workspace.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its GeneBench workspace module")
            if "sc_referee_evaluation/genebench_grader.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its GeneBench answer grader module")
            if "sc_referee_evaluation/method_contract_diagnostic.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its method-contract diagnostic module")
            if "sc_referee_evaluation/source_method_probe.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its static source-method probe module")
            if "sc_referee_evaluation/static_qualification.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its static-qualification module")
            if "sc_referee_evaluation/typed_method_qualification.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its typed-method verifier module")
            if "sc_referee_evaluation/qualification_adapter_registry.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its qualification-adapter registry")
            if "sc_referee_evaluation/founder_orientation_adapter.py" not in names:
                raise RuntimeError("Evaluation wheel omitted its founder qualification adapter")
            if "sc_referee_evaluation/prospective_qualification_v2.py" not in names:
                raise RuntimeError("Evaluation wheel omitted the v2 prospective contract")
            if "sc_referee_evaluation/prospective_selected_result_verifier.py" not in names:
                raise RuntimeError("Evaluation wheel omitted the selected-result verifier")
            missing_modules = sorted(_V1_1_QUALIFICATION_MODULES - names)
            if missing_modules:
                raise RuntimeError(
                    "Evaluation wheel omitted v1.1 qualification modules: "
                    + ", ".join(missing_modules)
                )
            missing_resources = sorted(_V1_1_QUALIFICATION_RESOURCES - names)
            if missing_resources:
                raise RuntimeError(
                    "Evaluation wheel omitted v1.1 qualification resources: "
                    + ", ".join(missing_resources)
                )
            entry_point_names = [
                name for name in names if name.endswith(".dist-info/entry_points.txt")
            ]
            if len(entry_point_names) != 1:
                raise RuntimeError("Evaluation wheel has no unique entry-point manifest")
            entry_points = archive.read(entry_point_names[0]).decode("utf-8")
            for command, target in _V1_1_QUALIFICATION_ENTRY_POINTS.items():
                if f"{command} = {target}" not in entry_points:
                    raise RuntimeError(
                        f"Evaluation wheel omitted qualification entry point: {command}"
                    )
            if any(name.startswith("sc_referee/") for name in names):
                raise RuntimeError("Evaluation wheel vendors the production package")
        environment_root = temp_root / "venv"
        environment_python = _install_evaluation_smoke_venv(
            core_wheels[0], wheels[0], environment_root
        )
        fresh_cwd = temp_root / "fresh-cwd"
        fresh_cwd.mkdir()
        clean_environment = _clean_subprocess_environment()
        installed_package_root = environment_root.resolve()
        verification_code = "\n".join(
            [
                "import importlib",
                "import importlib.metadata",
                "import importlib.resources",
                "from pathlib import Path",
                "import sys",
                "import sc_referee_evaluation",
                "from sc_referee_evaluation.cli import main",
                "from sc_referee_evaluation.comparison import compare_detector_output",
                "from sc_referee_evaluation.candidate import project_evaluation_candidate",
                "from sc_referee_evaluation.capture import load_review_capture",
                "from sc_referee_evaluation.corpus import (",
                "    CorpusPreflightError,",
                "    preflight_genebench_public_package,",
                ")",
                "from sc_referee_evaluation.genebench_workspace import (",
                "    GeneBenchWorkspaceError,",
                "    prepare_genebench_public_case,",
                ")",
                "from sc_referee_evaluation.genebench_grader import (",
                "    GeneBenchNumericGradeError,",
                "    grade_genebench_public_answer,",
                "    grade_genebench_public_numeric_answer,",
                ")",
                "from sc_referee_evaluation.method_contract_diagnostic import (",
                "    MethodContractDiagnosticError,",
                "    diagnose_genebench_method_contract_conflict,",
                ")",
                "from sc_referee_evaluation.prospective_qualification_v2 import (",
                "    freeze_case_evidence_contract,",
                "    freeze_stage2_scientific_label,",
                ")",
                "from sc_referee_evaluation.prospective_selected_result_verifier import (",
                "    freeze_independent_selected_result_derivation,",
                "    freeze_selected_result_validation,",
                "    revalidate_independent_selected_result_derivation,",
                ")",
                "from sc_referee_evaluation.source_method_probe import (",
                "    SourceMethodProbeError,",
                "    probe_python_method_shapes,",
                ")",
                "from sc_referee_evaluation.static_qualification import (",
                "    freeze_bounded_direction_profile,",
                "    freeze_protocol_artifact,",
                "    revalidate_static_proof,",
                "    verify_bounded_direction_case,",
                ")",
                "from sc_referee_evaluation.qualification_adapter_registry import (",
                "    registered_qualification_adapter,",
                ")",
                "from sc_referee_evaluation.typed_method_qualification import (",
                "    freeze_typed_method_profile,",
                "    revalidate_registered_typed_method_proof,",
                "    verify_registered_typed_method_case,",
                ")",
                "from sc_referee_evaluation.grader import grade_exact_json_output",
                "from sc_referee_evaluation.fixture import (",
                "    FixtureProofInputs,",
                "    generate_ambiguous_fixture,",
                "    generate_control_fixture,",
                "    generate_positive_fixture,",
                "    revalidate_fixture_proof,",
                ")",
                "from sc_referee_evaluation.review_protocol import freeze_scientific_label",
                "from sc_referee_evaluation.root_cause import build_adjudicated_root_cause",
                "from sc_referee_evaluation.metrics import build_qualification_metric_set",
                "from sc_referee_evaluation.stage3 import (",
                "    build_stage3_review_packet,",
                "    reconcile_detector_case,",
                "    validate_stage3_review_submission,",
                ")",
                "from sc_referee_evaluation.workspace import build_blind_workspace",
                f"installed_root = Path({str(installed_package_root)!r})",
                "qualification_modules = (",
                "    'sc_referee_evaluation.qualification_identity',",
                "    'sc_referee_evaluation.selected_result_qualification_io',",
                "    'sc_referee_evaluation.selected_result_qualification_oracle',",
                "    'sc_referee_evaluation.selected_result_qualification_runner',",
                "    'sc_referee_evaluation.selected_result_qualification_target_worker',",
                "    'sc_referee_evaluation.selected_result_qualification_trust',",
                "    'sc_referee_evaluation.selected_result_semantic_review',",
                "    'sc_referee_evaluation.selected_result_verifier_qualification',",
                ")",
                "for module_name in qualification_modules:",
                "    module = importlib.import_module(module_name)",
                "    assert Path(module.__file__).resolve().is_relative_to(installed_root)",
                "resource_root = importlib.resources.files(",
                "    'sc_referee_evaluation.qualification_resources.selected_result_v1_1'",
                ")",
                "required_resources = {",
                "    'case-author-prompt.txt',",
                "    'comparison-prompt.txt',",
                "    'provider-pack-schema.json',",
                "    'semantic-review-contract.json',",
                "    'semantic-validator-prompt.txt',",
                "    'target-authorization-schema.json',",
                "    'target-runner-prompt.txt',",
                "    'validation-runner-prompt.txt',",
                "}",
                "assert all(resource_root.joinpath(name).read_bytes() for name in required_resources)",
                "entry_points = {",
                "    item.name: item.value",
                "    for item in importlib.metadata.distribution('sc-referee-evaluation').entry_points",
                "    if item.group == 'console_scripts'",
                "}",
                f"assert entry_points | {dict(_V1_1_QUALIFICATION_ENTRY_POINTS)!r} == entry_points",
                "assert callable(sc_referee_evaluation.validate_case_packet)",
                "assert callable(main)",
                "assert callable(compare_detector_output)",
                "assert callable(project_evaluation_candidate)",
                "assert callable(load_review_capture)",
                "assert CorpusPreflightError is not None",
                "assert callable(preflight_genebench_public_package)",
                "assert GeneBenchWorkspaceError is not None",
                "assert callable(prepare_genebench_public_case)",
                "assert GeneBenchNumericGradeError is not None",
                "assert callable(grade_genebench_public_answer)",
                "assert callable(grade_genebench_public_numeric_answer)",
                "assert MethodContractDiagnosticError is not None",
                "assert callable(diagnose_genebench_method_contract_conflict)",
                "assert callable(freeze_case_evidence_contract)",
                "assert callable(freeze_stage2_scientific_label)",
                "assert callable(freeze_independent_selected_result_derivation)",
                "assert callable(freeze_selected_result_validation)",
                "assert callable(revalidate_independent_selected_result_derivation)",
                "assert SourceMethodProbeError is not None",
                "assert callable(probe_python_method_shapes)",
                "assert callable(freeze_bounded_direction_profile)",
                "assert callable(freeze_protocol_artifact)",
                "assert callable(revalidate_static_proof)",
                "assert callable(verify_bounded_direction_case)",
                "assert callable(registered_qualification_adapter)",
                "assert callable(freeze_typed_method_profile)",
                "assert callable(revalidate_registered_typed_method_proof)",
                "assert callable(verify_registered_typed_method_case)",
                "assert callable(grade_exact_json_output)",
                "assert FixtureProofInputs is not None",
                "assert callable(generate_ambiguous_fixture)",
                "assert callable(generate_control_fixture)",
                "assert callable(generate_positive_fixture)",
                "assert callable(revalidate_fixture_proof)",
                "assert callable(freeze_scientific_label)",
                "assert callable(build_adjudicated_root_cause)",
                "assert callable(build_qualification_metric_set)",
                "assert callable(build_stage3_review_packet)",
                "assert callable(reconcile_detector_case)",
                "assert callable(validate_stage3_review_submission)",
                "assert callable(build_blind_workspace)",
            ]
        )
        subprocess.run(
            [str(environment_python), "-I", "-c", verification_code],
            cwd=fresh_cwd,
            env=clean_environment,
            check=True,
        )
        scripts_root = environment_python.parent
        for command in _V1_1_QUALIFICATION_ENTRY_POINTS:
            executable = scripts_root / (f"{command}.exe" if os.name == "nt" else command)
            subprocess.run(
                [str(executable), "--help"],
                cwd=fresh_cwd,
                env=clean_environment,
                check=True,
                capture_output=True,
                text=True,
            )
        runtime_manifest_path = fresh_cwd / "TARGET_RUNTIME_MANIFEST.json"
        worker_command = "sc-referee-eval-selected-result-target-worker"
        worker_executable = scripts_root / (
            f"{worker_command}.exe" if os.name == "nt" else worker_command
        )
        subprocess.run(
            [str(worker_executable), "--runtime-manifest", str(runtime_manifest_path)],
            cwd=fresh_cwd,
            env=clean_environment,
            check=True,
            capture_output=True,
            text=True,
        )
        runtime_payload = runtime_manifest_path.read_bytes()
        full_runtime_manifest = json.loads(runtime_payload)
        canonical_full_runtime = json.dumps(
            full_runtime_manifest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        assert runtime_payload == (canonical_full_runtime + "\n").encode("utf-8")
        runtime_manifest = dict(full_runtime_manifest)
        runtime_digest = runtime_manifest.pop("target_runtime_manifest_digest")
        canonical_runtime = json.dumps(
            runtime_manifest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        assert (
            runtime_digest
            == "sha256:" + hashlib.sha256(canonical_runtime.encode("utf-8")).hexdigest()
        )
        assert runtime_manifest["artifact_kind"] == (
            "selected_result_verifier_target_runtime_manifest"
        )
        assert set(runtime_manifest) == {
            "artifact_kind",
            "runtime_manifest_version",
            "target_worker_version",
            "python_runtime",
            "module_files",
            "distributions",
            "distribution_count",
            "distribution_file_count",
            "distribution_total_file_bytes",
            "input_projection",
            "project_code_executed",
            "qualification_authority",
        }
        assert runtime_manifest["input_projection"] == "installed_runtime_only"
        assert runtime_manifest["project_code_executed"] is False
        assert runtime_manifest["distribution_count"] == 3
        assert {item["requested_name"] for item in runtime_manifest["distributions"]} == {
            "cryptography",
            "sc-referee",
            "sc-referee-evaluation",
        }
        assert {item["module_name"] for item in runtime_manifest["module_files"]} == {
            "cryptography",
            "sc_referee.core.ids",
            "sc_referee_evaluation.prospective_selected_result_verifier",
            "sc_referee_evaluation.selected_result_qualification_target_worker",
        }


def main() -> int:
    run("-m", "ruff", "check", ".")
    run("-m", "ruff", "format", "--check", ".")
    run("-m", "mypy", "src")
    run("-m", "mypy", "--config-file", "evaluation/pyproject.toml", "evaluation/src")
    run("-m", "pytest", "-q")
    run("-m", "compileall", "-q", "src", "evaluation/src", "tests", "scripts")
    run("scripts/validate_starter.py")
    run("scripts/validate_regression_corpus.py")
    run("scripts/run_regression_corpus.py")
    run("-m", "sc_referee.cli", "validate-schemas")
    verify_built_wheel()
    verify_built_evaluation_wheel()

    with tempfile.TemporaryDirectory(prefix="sc-referee-handoff-") as temp:
        temp_root = Path(temp)
        first = temp_root / "demo"
        second = temp_root / "replay"
        general = temp_root / "general-static"
        general_replay = temp_root / "general-static-replay"
        general_diff = temp_root / "general-static-diff.json"
        general_project = temp_root / "general-project"
        unresolved = temp_root / "general-unresolved"
        interaction = temp_root / "semantic-interaction"
        interaction_replay = temp_root / "semantic-interaction-replay"
        contract_interaction = temp_root / "contract-interaction"
        contract_replay = temp_root / "contract-interaction-replay"
        proposal_path = temp_root / "semantic-proposal.json"
        values_path = temp_root / "scientist-contract-values.json"
        observed_migration = temp_root / "public-v0.5-to-v0.6"
        interaction_migration = temp_root / "public-v0.6-to-v0.7"
        lineage_migration = temp_root / "public-v0.7-to-v0.8"
        root_cause_migration = temp_root / "public-v0.8-to-v0.9"
        stage3_migration = temp_root / "public-v0.9-to-v0.10"
        metric_migration = temp_root / "public-v0.10-to-v0.11"
        fixture_proof_migration = temp_root / "public-v0.11-to-v0.12"
        execution_migration = temp_root / "public-v0.12-to-v0.13"
        work_item_migration = temp_root / "public-v0.13-to-v0.14"
        static_qualification_migration = temp_root / "public-v0.14-to-v0.15"
        second_static_qualification_migration = temp_root / "public-v0.15-to-v0.16"
        modular_method_migration = temp_root / "public-v0.16-to-v0.17"
        calculation_check_migration = temp_root / "public-v0.17-to-v0.18"
        ro_crate = temp_root / "demo-ro-crate.zip"
        capability_matrix = temp_root / "capability-matrix.json"
        shutil.copytree(
            ROOT / "examples" / "general-static",
            general_project,
            ignore=shutil.ignore_patterns(".sc-referee", ".scientific-audit"),
        )
        run("-m", "sc_referee.cli", "demo", "examples/walking-skeleton", "--output", str(first))
        run(
            "-m",
            "sc_referee.cli",
            "replay",
            str(first / "semantic.lock.json"),
            "--output",
            str(second),
        )
        run(
            "-m",
            "sc_referee.cli",
            "export-ro-crate",
            str(first),
            "--output",
            str(ro_crate),
            "--author-name",
            "Handoff verifier",
            "--license-uri",
            "https://spdx.org/licenses/Apache-2.0.html",
            "--license-name",
            "Apache License 2.0",
        )
        run("-m", "sc_referee.cli", "validate-ro-crate", str(ro_crate))
        run(
            "-m",
            "sc_referee.cli",
            "generate-capability-matrix",
            "--output",
            str(capability_matrix),
        )
        run(
            "-m",
            "sc_referee.cli",
            "validate-capability-matrix",
            str(capability_matrix),
        )
        capability_document = json.loads(capability_matrix.read_text(encoding="utf-8"))
        capability_detectors = [
            detector for entry in capability_document["entries"] for detector in entry["detectors"]
        ]
        expected_capability_detectors = [
            {
                "detector_id": "detector:bounded-analysis-method-conflict",
                "maturity": "experimental",
                "qualification_ref": None,
                "review_basis": "not_qualified",
                "strongest_output_type": "disclosure",
            },
            {
                "detector_id": "detector:bounded-feature-identifier-identity",
                "maturity": "experimental",
                "qualification_ref": None,
                "review_basis": "not_qualified",
                "strongest_output_type": "disclosure",
            },
            {
                "detector_id": "detector:bounded-report-mean-direction",
                "maturity": "experimental",
                "qualification_ref": None,
                "review_basis": "not_qualified",
                "strongest_output_type": "disclosure",
            },
            {
                "detector_id": "detector:bounded-reported-method-contract-conflict",
                "maturity": "experimental",
                "qualification_ref": None,
                "review_basis": "not_qualified",
                "strongest_output_type": "disclosure",
            },
        ]
        if sorted(capability_detectors, key=lambda item: item["detector_id"]) != (
            expected_capability_detectors
        ):
            raise RuntimeError(
                "Bundled capability matrix detector exceeded the experimental unqualified ceiling"
            )
        if any(
            entry["tested_versions"] or entry["inferred_compatibility"]
            for entry in capability_document["entries"]
        ):
            raise RuntimeError("Bundled capability matrix invented version evidence")
        if capability_document["domain_wide_support_claim_allowed"] is not False:
            raise RuntimeError("Bundled capability matrix allowed a domain-wide support claim")
        with zipfile.ZipFile(ro_crate, "r") as archive:
            if (
                archive.read("native/audit.bundle.json")
                != first.joinpath("audit.bundle.json").read_bytes()
            ):
                raise RuntimeError("RO-Crate changed the native audit bundle bytes")
            if archive.read("native/report.html") != first.joinpath("report.html").read_bytes():
                raise RuntimeError("RO-Crate changed the native report bytes")
            if any(name.endswith("audit.db") for name in archive.namelist()):
                raise RuntimeError("RO-Crate included disposable SQLite state")

        names = [
            "detector-result.jsonl",
            "finding.jsonl",
            "conditional-concern.jsonl",
            "material-question.jsonl",
            "disclosure.jsonl",
            "coverage-record.jsonl",
        ]
        for name in names:
            left = first / "derived" / name
            right = second / "derived" / name
            if digest(left) != digest(right):
                raise RuntimeError(f"Deterministic replay mismatch: {name}")

        for name in (
            "asset-identity.jsonl",
            "files.jsonl",
            "operation.jsonl",
            "artifact.jsonl",
            "observed-result.jsonl",
        ):
            left = first / "observed" / name
            right = second / "observed" / name
            if digest(left) != digest(right):
                raise RuntimeError(f"Observed-record replay mismatch: {name}")

        bundle = json.loads((first / "audit.bundle.json").read_text(encoding="utf-8"))
        expected = {
            "findings": 1,
            "conditional_concerns": 1,
            "material_questions": 1,
            "disclosures": 1,
            "detector_results": 2,
            "coverage_records": 1,
            "storage_manifests": 1,
            "parser_results": 2,
            "audit_runs": 8,
            "stage_results": 7,
            "file_records": 10,
            "operations": 17,
            "artifacts": 4,
            "observed_results": 1,
            "data_assets": 0,
            "variables": 0,
            "analysis_decisions": 0,
            "selection_envelopes": 0,
            "executions": 0,
            "environments": 0,
            "reproduction_requests": 0,
            "performance_records": 0,
            "cache_entries": 0,
            "cache_policies": 0,
            "work_items": 0,
            "answers": 0,
            "agent_reviews": 0,
            "adjudicated_root_causes": 0,
            "detector_evaluation_candidates": 0,
            "stage3_comparison_reviews": 0,
            "detector_case_outcomes": 0,
            "qualification_metric_sets": 0,
            "benchmark_adjudications": 0,
            "benchmark_fixtures": 0,
            "detector_qualifications": 0,
            "project_execution_authorizations": 0,
            "static_qualification_profiles": 0,
            "static_qualification_proofs": 0,
        }
        actual = {field: len(bundle[field]) for field in expected}
        if actual != expected:
            raise RuntimeError(f"Unexpected walking-skeleton counts: {actual!r}")

        run(
            "-m",
            "sc_referee.cli",
            "audit",
            str(general_project),
            "--output",
            str(general),
            "--report",
            "report.md",
        )
        run(
            "-m",
            "sc_referee.cli",
            "replay",
            str(general / "semantic.lock.json"),
            "--output",
            str(general_replay),
        )
        run(
            "-m",
            "sc_referee.cli",
            "diff",
            str(general),
            str(general_replay),
            "--output",
            str(general_diff),
        )
        diff_document = json.loads(general_diff.read_text(encoding="utf-8"))
        verify_audit_diff(diff_document)
        if diff_document["paths"]["changed"]:
            raise RuntimeError("General replay audit diff reported a changed source path")
        run("-m", "sc_referee.cli", "status", str(general), "--json")
        general_bundle = json.loads((general / "audit.bundle.json").read_text(encoding="utf-8"))
        replayed_general_bundle = json.loads(
            (general_replay / "audit.bundle.json").read_text(encoding="utf-8")
        )
        for field in (
            "scientific_contracts",
            "claims",
            "findings",
            "conditional_concerns",
            "material_questions",
            "disclosures",
            "coverage_records",
            "publication_surfaces",
            "parser_results",
            "operations",
            "artifacts",
            "observed_results",
            "data_assets",
            "variables",
            "analysis_decisions",
            "selection_envelopes",
            "executions",
            "environments",
            "reproduction_requests",
            "performance_records",
            "cache_entries",
            "cache_policies",
            "agent_reviews",
            "adjudicated_root_causes",
            "detector_evaluation_candidates",
            "stage3_comparison_reviews",
            "detector_case_outcomes",
            "qualification_metric_sets",
            "benchmark_adjudications",
            "benchmark_fixtures",
        ):
            if general_bundle[field] != replayed_general_bundle[field]:
                raise RuntimeError(f"General static replay mismatch: {field}")
        if general_bundle["findings"] or general_bundle["conditional_concerns"]:
            raise RuntimeError("General static audit invented an assessment")
        if len(general_bundle["observed_results"]) != 1:
            raise RuntimeError("General static audit did not emit one bounded verified result")
        if general_bundle["observed_results"][0].get("scalar_value") != 2.0:
            raise RuntimeError("General static audit bounded scalar was not independently verified")
        if len(general_bundle["data_assets"]) != 1 or len(general_bundle["executions"]) != 1:
            raise RuntimeError("General static audit omitted its public data or execution plane")
        if {item.get("environment_kind") for item in general_bundle["environments"]} != {
            "auditor_runtime",
            "project_runtime",
        }:
            raise RuntimeError("General static audit omitted an auditor or project Environment")
        if (
            len(general_bundle["reproduction_requests"]) != 1
            or general_bundle["reproduction_requests"][0]
            .get("extensions", {})
            .get("x-no-execution-authorization")
            is not True
        ):
            raise RuntimeError(
                "General static audit omitted its nonauthorizing reproduction request"
            )
        general_execution = general_bundle["executions"][0]
        if (
            general_execution.get("execution_kind") != "auditor_verification"
            or general_execution.get("sandbox", {}).get("project_code_executed") is not False
        ):
            raise RuntimeError("Auditor verification was mislabeled as project execution")
        if (
            len(general_bundle["claims"]) != 1
            or general_bundle["claims"][0].get("lineage", {}).get("status") != "partial"
        ):
            raise RuntimeError("General static audit overstated or omitted bounded claim lineage")
        if general_bundle["coverage_records"][0]["overall_status"] != (
            "partial_evidence_unavailable"
        ):
            raise RuntimeError("General static audit overstated coverage")
        general_lock = json.loads((general / "semantic.lock.json").read_text(encoding="utf-8"))
        if general_lock.get("model_calls") != []:
            raise RuntimeError("General static audit unexpectedly recorded a model call")
        general_performance = general_bundle["performance_records"]
        if len(general_performance) != 1:
            raise RuntimeError("General static audit omitted its bounded PerformanceRecord")
        if (
            general_performance[0].get("extensions", {}).get("x-measurement-boundary")
            != "semantic_lock"
            or general_performance[0].get("extensions", {}).get("x-postlock-elapsed-included")
            is not False
            or general_performance[0].get("model_usage", {}).get("calls") != 0
        ):
            raise RuntimeError("General PerformanceRecord overstated its measured scope")
        if "not total run duration" not in (general / "report.html").read_text(encoding="utf-8"):
            raise RuntimeError("General report omitted the PerformanceRecord boundary warning")
        if digest(general / "derived" / "performance-record.jsonl") != digest(
            general_replay / "derived" / "performance-record.jsonl"
        ):
            raise RuntimeError("General PerformanceRecord replay was not byte-identical")

        run(
            "-m",
            "sc_referee.cli",
            "audit",
            str(general_project),
            "--output",
            str(unresolved),
        )
        run(
            "-m",
            "sc_referee.cli",
            "resume",
            str(unresolved),
            "--repository",
            str(general_project),
            "--output",
            str(interaction),
        )
        run("-m", "sc_referee.cli", "work-queue", str(interaction))
        ready_work_item = json.loads(
            (interaction / "derived" / "work-item.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()[0]
        )
        work_item_id = str(ready_work_item["work_item_id"])
        run(
            "-m",
            "sc_referee.cli",
            "work-packet",
            str(interaction),
            "--work-item-id",
            work_item_id,
        )
        unresolved_bundle = json.loads(
            (unresolved / "audit.bundle.json").read_text(encoding="utf-8")
        )
        question = unresolved_bundle["material_questions"][0]
        report_option = next(
            item for item in question["candidate_answers"] if item["label"] == "report.md"
        )
        packet = ready_work_item["packet"]
        proposal = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "semantic_assertion",
            "assertion_id": "assertion:handoff-publication-proposal",
            "audit_run_id": ready_work_item["audit_run_id"],
            "subject_ref": ready_work_item["target_refs"][0],
            "predicate": "proposed_publication_surface",
            "object": report_option["value"],
            "semantic_role": "inferred",
            "assertion_class": "implicit_scientific_inference",
            "epistemic_status": "proposed",
            "authority_scope": "none",
            "independently_checkable": False,
            "finding_eligibility": "ineligible",
            "verification": {"status": "not_checked", "method": "not_applicable"},
            "certainty": {
                "level": "low",
                "basis": "Filename evidence is nonauthoritative and requires a scientist Answer.",
            },
            "rationale": "The bounded source is a possible final report, pending human authority.",
            "source_refs": [packet["source_refs"][0]],
            "provenance": {
                "actor": {"actor_kind": "model", "actor_id": "model:handoff"},
                "method": "bounded_semantic_proposal",
                "created_at": question["created_at"],
                "tool": "handoff-verifier",
                "tool_version": __version__,
            },
            "extensions": {
                "x-work-item-ref": {
                    "record_type": "work_item",
                    "record_id": work_item_id,
                },
                "x-packet-digest": packet["packet_digest"],
                "x-prompt-template-digest": packet["prompt_template_digest"],
            },
        }
        proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
        run(
            "-m",
            "sc_referee.cli",
            "submit-proposals",
            str(interaction),
            "--work-item-id",
            work_item_id,
            "--proposal",
            str(proposal_path),
        )
        run(
            "-m",
            "sc_referee.cli",
            "record-answer",
            str(interaction),
            "--question-id",
            str(question["question_id"]),
            "--select-option",
            str(report_option["answer_id"]),
            "--actor-id",
            "scientist:handoff-verifier",
        )
        run("-m", "sc_referee.cli", "lock-semantics", str(interaction))
        interaction_ledger = load_deadline_ledger(interaction / "observed" / LEDGER_FILENAME)
        if interaction_ledger is None or interaction_ledger["segments"][-1]["state"] != (
            "complete"
        ):
            raise RuntimeError("Interaction deadline ledger was not durably completed")
        run("-m", "sc_referee.cli", "status", str(interaction), "--json")
        run(
            "-m",
            "sc_referee.cli",
            "replay",
            str(interaction / "semantic.lock.json"),
            "--output",
            str(interaction_replay),
        )
        answered_bundle = json.loads(
            (interaction / "audit.bundle.json").read_text(encoding="utf-8")
        )
        interaction_lock = json.loads(
            (interaction / "semantic.lock.json").read_text(encoding="utf-8")
        )
        expected_parent = {
            "record_type": "audit_run",
            "record_id": unresolved_bundle["audit_run_id"],
        }
        if not answered_bundle["audit_runs"] or any(
            item.get("parent_run_ref") != expected_parent for item in answered_bundle["audit_runs"]
        ):
            raise RuntimeError("Answered audit did not preserve its parent-run linkage")
        answered_selection = answered_bundle["publication_surfaces"][0]["selection"]
        if not answered_bundle["answers"] or answered_selection.get(
            "scientist_answer_id"
        ) != answered_bundle["answers"][0].get("answer_id"):
            raise RuntimeError("Interaction audit did not bind the public scientist Answer")
        if answered_bundle["semantic_assertions"] != [proposal]:
            raise RuntimeError("Interaction audit altered or omitted its model proposal")
        if answered_bundle["observed_results"] != unresolved_bundle["observed_results"]:
            raise RuntimeError("Interaction audit altered its precomputed observed result")
        for field in (
            "data_assets",
            "variables",
            "analysis_decisions",
            "selection_envelopes",
            "executions",
            "environments",
        ):
            if answered_bundle[field] != unresolved_bundle[field]:
                raise RuntimeError(f"Interaction audit altered its precomputed {field}")
        if answered_bundle["claims"][0].get("lineage", {}).get("status") != "partial":
            raise RuntimeError("Interaction audit did not bind bounded partial claim lineage")
        interaction_performance = answered_bundle["performance_records"]
        if (
            len(interaction_performance) != 1
            or interaction_performance[0].get("model_usage", {}).get("calls") != 0
            or interaction_performance[0].get("cache_usage")
            != {"hits": 0, "misses": 0, "invalidations": 0}
            or interaction_performance[0].get("extensions", {}).get("x-deadline-ledger-digest")
            != interaction_lock["deadline_ledger"]["ledger_digest"]
        ):
            raise RuntimeError("Interaction PerformanceRecord exceeded its current-run scope")
        replayed_interaction = json.loads(
            (interaction_replay / "audit.bundle.json").read_text(encoding="utf-8")
        )
        for field in ("semantic_assertions", "work_items", "answers", "performance_records"):
            if replayed_interaction[field] != answered_bundle[field]:
                raise RuntimeError(f"Interaction replay mismatch: {field}")

        contract_question = next(
            item
            for item in answered_bundle["material_questions"]
            if item.get("status") == "open"
            and item.get("unknown_semantic_dimension") == "scientific_contract"
        )
        run(
            "-m",
            "sc_referee.cli",
            "resume",
            str(interaction),
            "--repository",
            str(general_project),
            "--output",
            str(contract_interaction),
            "--question-id",
            str(contract_question["question_id"]),
        )
        contract_work_item = json.loads(
            (contract_interaction / "derived" / "work-item.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()[0]
        )
        contract_packet = contract_work_item["packet"]
        contract_proposal = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "semantic_assertion",
            "assertion_id": "assertion:handoff-contract-proposal",
            "audit_run_id": contract_work_item["audit_run_id"],
            "subject_ref": contract_work_item["target_refs"][0],
            "predicate": "proposed_scientific_contract",
            "object": {"target_population": "Model-proposed population"},
            "semantic_role": "inferred",
            "assertion_class": "implicit_scientific_inference",
            "epistemic_status": "proposed",
            "authority_scope": "none",
            "independently_checkable": False,
            "finding_eligibility": "ineligible",
            "verification": {"status": "not_checked", "method": "not_applicable"},
            "certainty": {
                "level": "low",
                "basis": "The model proposal cannot establish scientist intent.",
            },
            "rationale": "The exact claim span supports only a bounded proposal.",
            "source_refs": [contract_packet["source_refs"][0]],
            "provenance": {
                "actor": {"actor_kind": "model", "actor_id": "model:handoff"},
                "method": "bounded_semantic_proposal",
                "created_at": contract_question["created_at"],
                "tool": "handoff-verifier",
                "tool_version": __version__,
            },
            "extensions": {
                "x-work-item-ref": {
                    "record_type": "work_item",
                    "record_id": contract_work_item["work_item_id"],
                },
                "x-packet-digest": contract_packet["packet_digest"],
                "x-prompt-template-digest": contract_packet["prompt_template_digest"],
            },
        }
        proposal_path.write_text(json.dumps(contract_proposal), encoding="utf-8")
        run(
            "-m",
            "sc_referee.cli",
            "submit-proposals",
            str(contract_interaction),
            "--work-item-id",
            str(contract_work_item["work_item_id"]),
            "--proposal",
            str(proposal_path),
        )
        contract_values = {
            dimension: f"Scientist-declared {dimension.replace('_', ' ')}"
            for dimension in contract_packet["unresolved_dimensions"]
        }
        values_path.write_text(json.dumps(contract_values), encoding="utf-8")
        run(
            "-m",
            "sc_referee.cli",
            "record-structured-answer",
            str(contract_interaction),
            "--question-id",
            str(contract_question["question_id"]),
            "--values",
            str(values_path),
            "--actor-id",
            "scientist:handoff-verifier",
        )
        run("-m", "sc_referee.cli", "lock-semantics", str(contract_interaction))
        contract_ledger = load_deadline_ledger(contract_interaction / "observed" / LEDGER_FILENAME)
        if contract_ledger is None or len(contract_ledger["segments"]) != 2:
            raise RuntimeError("Linked interaction deadline history was not preserved")
        run(
            "-m",
            "sc_referee.cli",
            "replay",
            str(contract_interaction / "semantic.lock.json"),
            "--output",
            str(contract_replay),
        )
        contract_bundle = json.loads(
            (contract_interaction / "audit.bundle.json").read_text(encoding="utf-8")
        )
        if contract_bundle["scientific_contracts"][0].get("status") != "resolved":
            raise RuntimeError("Structured Answer did not resolve the complete contract fixture")
        accepted_assertions = [
            item
            for item in contract_bundle["semantic_assertions"]
            if item.get("epistemic_status") == "accepted"
        ]
        if len(accepted_assertions) != len(contract_values) or contract_bundle["findings"]:
            raise RuntimeError("Structured contract resolution changed authority or Findings")
        contract_grades = contract_bundle["claims"][0]["lineage"]["grades"]
        if (
            contract_grades["semantic_origin"]["status"] != "complete"
            or contract_grades["execution_origin"]["status"] != "missing"
        ):
            raise RuntimeError("Scientist intent changed a non-semantic lineage authority")
        replayed_contract = json.loads(
            (contract_replay / "audit.bundle.json").read_text(encoding="utf-8")
        )
        if not {item["assertion_id"] for item in answered_bundle["semantic_assertions"]}.issubset(
            {item["assertion_id"] for item in contract_bundle["semantic_assertions"]}
        ):
            raise RuntimeError("Linked interaction omitted prior semantic evidence")
        for field in (
            "semantic_assertions",
            "scientific_contracts",
            "answers",
            "performance_records",
        ):
            if replayed_contract[field] != contract_bundle[field]:
                raise RuntimeError(f"Contract interaction replay mismatch: {field}")

        run(
            "scripts/migrate_v0_5_to_v0_6.py",
            "reference/schemas-v0.5.0/examples/audit-bundle.example.json",
            "--source-schemas",
            "reference/schemas-v0.5.0",
            "--target-schemas",
            "reference/schemas-v0.6.0",
            "--output",
            str(observed_migration),
        )
        migration_report = json.loads(
            (observed_migration / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
        )
        if migration_report.get("validation") != "passed":
            raise RuntimeError("Public v0.5.0 to v0.6.0 migration did not validate")
        if migration_report.get("observed_plane_evidence_invented") is not False:
            raise RuntimeError("Public migration must not invent observed-plane records")
        run(
            "scripts/migrate_v0_6_to_v0_7.py",
            "reference/schemas-v0.6.0/examples/audit-bundle.example.json",
            "--source-schemas",
            "reference/schemas-v0.6.0",
            "--target-schemas",
            "reference/schemas-v0.7.0",
            "--output",
            str(interaction_migration),
        )
        interaction_migration_report = json.loads(
            (interaction_migration / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
        )
        if interaction_migration_report.get("interaction_history_invented") is not False:
            raise RuntimeError("Public migration must not invent interaction history")
        run(
            "scripts/migrate_v0_7_to_v0_8.py",
            "reference/schemas-v0.7.0/examples/audit-bundle.example.json",
            "--source-schemas",
            "reference/schemas-v0.7.0",
            "--target-schemas",
            "reference/schemas-v0.8.0",
            "--output",
            str(lineage_migration),
        )
        lineage_migration_report = json.loads(
            (lineage_migration / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
        )
        if lineage_migration_report.get("observed_graph_history_invented") is not False:
            raise RuntimeError("Public migration must not invent lineage-plane records")
        run(
            "scripts/migrate_v0_8_to_v0_9.py",
            "reference/schemas-v0.8.0/examples/audit-bundle.example.json",
            "--source-schemas",
            "reference/schemas-v0.8.0",
            "--target-schemas",
            "reference/schemas-v0.9.0",
            "--output",
            str(root_cause_migration),
        )
        root_cause_migration_report = json.loads(
            (root_cause_migration / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
        )
        if (
            root_cause_migration_report.get("root_cause_equivalence_invented") is not False
            or root_cause_migration_report.get("legacy_positive_labels_admitted") is not False
        ):
            raise RuntimeError("Public root-cause migration invented positive equivalence")
        run(
            "scripts/migrate_v0_9_to_v0_10.py",
            "reference/schemas-v0.9.0/examples/audit-bundle.example.json",
            "--source-schemas",
            "reference/schemas-v0.9.0",
            "--target-schemas",
            "reference/schemas-v0.10.0",
            "--output",
            str(stage3_migration),
        )
        stage3_migration_report = json.loads(
            (stage3_migration / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
        )
        if any(
            stage3_migration_report.get(field) is not False
            for field in (
                "evaluation_candidates_invented",
                "detector_root_equivalence_invented",
                "case_outcomes_invented",
                "qualification_metrics_invented",
                "legacy_promotions_retained",
                "held_out_status_invented",
            )
        ):
            raise RuntimeError("Public Stage-3 migration invented qualification evidence")
        run(
            "scripts/migrate_v0_10_to_v0_11.py",
            "reference/schemas-v0.10.0/examples/audit-bundle.example.json",
            "--source-schemas",
            "reference/schemas-v0.10.0",
            "--target-schemas",
            "reference/schemas-v0.11.0",
            "--output",
            str(metric_migration),
        )
        metric_migration_report = json.loads(
            (metric_migration / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
        )
        if any(
            metric_migration_report.get(field) is not False
            for field in (
                "detector_result_states_invented",
                "evaluation_candidates_invented",
                "opportunity_projections_invented",
                "equivalence_decisions_invented",
                "qualification_metrics_invented",
                "legacy_metric_sets_authoritative",
            )
        ):
            raise RuntimeError("Public metric migration invented v0.11 qualification evidence")
        run(
            "scripts/migrate_v0_11_to_v0_12.py",
            "reference/schemas-v0.11.0/examples/audit-bundle.example.json",
            "--source-schemas",
            "reference/schemas-v0.11.0",
            "--target-schemas",
            "reference/schemas-v0.12.0",
            "--output",
            str(fixture_proof_migration),
        )
        fixture_proof_migration_report = json.loads(
            (fixture_proof_migration / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
        )
        if any(
            fixture_proof_migration_report.get(field) is not False
            for field in (
                "fixture_proof_invented",
                "capture_identity_invented",
                "chronology_invented",
                "clean_execution_invented",
                "hard_negative_evidence_invented",
                "qualification_metrics_invented",
                "legacy_metric_sets_authoritative",
                "storage_manifest_carried_forward",
            )
        ):
            raise RuntimeError("Public fixture-proof migration invented v0.12 evidence")
        run(
            "scripts/migrate_v0_12_to_v0_13.py",
            "reference/schemas-v0.12.0/examples/audit-bundle.example.json",
            "--source-schema-root",
            "reference/schemas-v0.12.0",
            "--target-schema-root",
            "reference/schemas-v0.13.0",
            "--output",
            str(execution_migration),
        )
        execution_migration_report = json.loads(
            (execution_migration / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
        )
        if any(
            execution_migration_report.get(field) is not False
            for field in (
                "authorization_invented",
                "capability_probe_invented",
                "controller_registry_entry_created",
                "execution_launched",
                "linked_run_invented",
                "storage_manifest_carried_forward",
            )
        ):
            raise RuntimeError("Public execution migration invented v0.13 authority")
        run(
            "scripts/migrate_v0_13_to_v0_14.py",
            "reference/schemas-v0.13.0/examples/audit-bundle.example.json",
            "--source-schema-root",
            "reference/schemas-v0.13.0",
            "--target-schema-root",
            "reference/schemas-v0.14.0",
            "--output",
            str(work_item_migration),
        )
        work_item_migration_report = json.loads(
            (work_item_migration / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
        )
        if any(
            work_item_migration_report.get(field) is not False
            for field in (
                "authorization_authority_invented",
                "controller_registry_entry_created",
                "execution_launched",
                "execution_work_item_invented",
                "storage_manifest_carried_forward",
                "work_item_digest_invented",
            )
        ):
            raise RuntimeError("Public WorkItem migration invented v0.14 authority")
        run(
            "scripts/migrate_v0_14_to_v0_15.py",
            "reference/schemas-v0.14.0/examples/audit-bundle.example.json",
            "--source-schema-root",
            "reference/schemas-v0.14.0",
            "--target-schema-root",
            V014_TO_V015_TARGET_SCHEMA_ROOT,
            "--output",
            str(static_qualification_migration),
        )
        static_qualification_migration_report = json.loads(
            (static_qualification_migration / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
        )
        if any(
            static_qualification_migration_report.get(field) is not False
            for field in (
                "execution_launched",
                "finding_authority_created",
                "static_fixture_created",
                "static_profile_created",
                "static_proof_created",
                "storage_manifest_carried_forward",
            )
        ):
            raise RuntimeError("Public static-qualification migration invented v0.15 authority")
        run(
            "scripts/migrate_v0_15_to_v0_16.py",
            "reference/schemas-v0.15.0/examples/audit-bundle.example.json",
            "--source-schema-root",
            "reference/schemas-v0.15.0",
            "--target-schema-root",
            V015_TO_V016_TARGET_SCHEMA_ROOT,
            "--output",
            str(second_static_qualification_migration),
        )
        second_static_qualification_migration_report = json.loads(
            (second_static_qualification_migration / "MIGRATION_REPORT.json").read_text(
                encoding="utf-8"
            )
        )
        if any(
            second_static_qualification_migration_report.get(field) is not False
            for field in (
                "answer_invented",
                "execution_launched",
                "finding_authority_created",
                "profile_or_proof_invented",
                "storage_manifest_carried_forward",
            )
        ):
            raise RuntimeError("Public second-static-profile migration invented v0.16 authority")
        run(
            "scripts/migrate_v0_16_to_v0_17.py",
            "reference/schemas-v0.16.0/examples/audit-bundle.example.json",
            "--source-schema-root",
            "reference/schemas-v0.16.0",
            "--target-schema-root",
            V016_TO_V017_TARGET_SCHEMA_ROOT,
            "--output",
            str(modular_method_migration),
        )
        modular_method_migration_report = json.loads(
            (modular_method_migration / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
        )
        if any(
            modular_method_migration_report.get(field) is not False
            for field in (
                "answer_invented",
                "binding_invented",
                "execution_launched",
                "finding_authority_created",
                "profile_or_proof_invented",
                "qualification_adapter_invented",
                "storage_manifest_carried_forward",
            )
        ):
            raise RuntimeError("Public modular-method migration invented v0.17 authority")
        run(
            "scripts/migrate_v0_17_to_v0_18.py",
            "reference/schemas-v0.17.0/examples/audit-bundle.example.json",
            "--source-schema-root",
            "reference/schemas-v0.17.0",
            "--target-schema-root",
            V017_TO_V018_TARGET_SCHEMA_ROOT,
            "--output",
            str(calculation_check_migration),
        )
        calculation_check_migration_report = json.loads(
            (calculation_check_migration / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
        )
        if any(
            calculation_check_migration_report.get(field) is not False
            for field in (
                "calculation_observation_invented",
                "execution_launched",
                "finding_authority_created",
                "storage_manifest_carried_forward",
            )
        ):
            raise RuntimeError("Public calculation-check migration invented v0.18 authority")

    verification = {
        "starter_version": "0.1.0",
        "tool_version": __version__,
        "pytest": "passed",
        "compileall": "passed",
        "public_schema_examples": 79,
        "built_wheel_schema_resources": "passed",
        "isolated_answer_side_evaluation_wheel": "passed",
        "genebench_public_preflight": "passed_synthetic_package_only",
        "genebench_public_package_acquired": "external_temporary_preflight_recorded_not_bundled",
        "genebench_public_package_license_status": "consistent_cc_by_4_0_at_pinned_revision",
        "genebench_current_head_integrity_status": "rejected_stale_license_and_readme_checksums",
        "genebench_public_grader_contracts": (
            "closed_single_multi_numeric_and_two_required_composites_tested"
        ),
        "genebench_static_source_method_probe": "four_closed_evaluation_only_profiles_tested",
        "answer_side_panel_reconciliation": "passed",
        "answer_side_snapshot_evidence_resolution": "passed",
        "answer_blind_workspace_isolation": "passed",
        "answer_side_two_stage_review_chronology": "passed",
        "canonical_root_cause_reconciliation": "passed",
        "public_development_positive_fixture_compilation": "passed",
        "evidence_bound_control_fixture_compilation": "passed",
        "fixture_proof_model_free_replay": "passed",
        "static_qualification_proof_model_free_replay": "passed",
        "static_qualification_control_compilation": "passed_synthetic_only",
        "evaluation_only_candidate_projection": "passed",
        "exact_result_opportunity_projection": "passed",
        "deterministic_clustered_qualification_metrics": "passed",
        "independent_report_metric_recomputation": "passed",
        "model_free_scientific_label_replay": "passed",
        "walking_skeleton": "passed",
        "arbitrary_repository_static_audit": "passed",
        "arbitrary_repository_replay": "passed",
        "typed_agent_status": "passed",
        "typed_prelock_interaction_and_linked_resume": "passed",
        "typed_scientific_contract_resolution": "passed",
        "bounded_static_selection_recognition": "passed",
        "bounded_conjunctive_selection_recognition": "passed",
        "nested_static_environment_profiles": "passed",
        "static_report_output_path_lineage": "passed",
        "static_report_result_artifact_flow": "passed",
        "static_report_single_assignment_flow": "passed",
        "static_report_assignment_chain_flow": "passed",
        "static_report_result_literal_parameter_flow": "passed",
        "static_report_literal_path_parameter_flow": "passed",
        "static_report_exact_keyword_binding_flow": "passed",
        "static_report_direct_formatter_flow": "passed",
        "static_report_single_formatter_assignment_flow": "passed",
        "static_report_formatter_assignment_chain_flow": "passed",
        "deterministic_ro_crate_1_3_export": "passed_bounded_offline_profile",
        "third_party_ro_crate_validation": "not_claimed",
        "generated_multidimensional_capability_matrix": "passed_fail_closed_manifest_profile",
        "capability_matrix_detector_qualification": "none_declared",
        "capability_matrix_tested_versions": "none_declared",
        "project_cache_writer_coordination": "passed",
        "project_cache_external_key_authentication": "passed",
        "repository_codex_skill_structure": "passed",
        "repository_codex_plugin_package": "passed",
        "evidence_first_mpp_adr_accepted": True,
        "built_wheel_post_mpp_execution_commands_hidden": "passed",
        "built_wheel_large_data_bounded_audit": "passed_10_billion_bytes_12_288_sampled",
        "built_wheel_root_checksum_manifest_identity": (
            "passed_repository_declared_without_target_byte_verification"
        ),
        "built_wheel_delimited_header_inventory": (
            "passed_exact_names_without_rows_types_or_execution"
        ),
        "built_wheel_nextflow_trace_import": (
            "passed_weak_import_without_observed_execution_or_claim_lineage"
        ),
        "project_execution_mpp_capability": "not_exposed",
        "linked_execution_closure_adr_status": "deferred",
        "trusted_capability_probe_adr_status": "deferred",
        "deterministic_replay": "passed",
        "verified_assessment_counts": expected,
        "ruff": "passed",
        "ruff_format": "passed",
        "mypy": "passed",
        "public_detector_qualification": "not_claimed",
        "public_schema_release": "0.18.0",
        "public_v0.5_to_v0.6_migration": "passed",
        "public_v0.6_to_v0.7_migration": "passed",
        "public_v0.7_to_v0.8_migration": "passed",
        "public_v0.8_to_v0.9_migration": "passed",
        "public_v0.9_to_v0.10_migration": "passed",
        "public_v0.10_to_v0.11_migration": "passed",
        "public_v0.11_to_v0.12_migration": "passed",
        "public_v0.12_to_v0.13_migration": "passed",
        "public_v0.13_to_v0.14_migration": "passed",
        "public_v0.14_to_v0.15_migration": "passed_fail_closed",
        "public_v0.15_to_v0.16_migration": "passed_fail_closed",
        "public_v0.16_to_v0.17_migration": "passed_fail_closed",
        "public_v0.17_to_v0.18_migration": "passed_fail_closed",
        "interaction_schema_adr_accepted": True,
        "lineage_schema_adr_accepted": True,
        "performance_projection_adr_accepted": True,
        "cache_authentication_adr_accepted": True,
        "root_cause_reconciliation_adr_accepted": True,
        "stage3_qualification_adr_accepted": True,
        "experimental_candidate_state_adr_accepted": True,
        "qualification_metric_inputs_adr_accepted": True,
        "fixture_proof_evidence_adr_accepted": True,
        "authorized_rootless_oci_execution_adr_accepted": True,
        "static_closed_scope_qualification_adr_accepted": True,
        "second_static_qualification_profile_adr_accepted": True,
        "modular_method_check_extension_adr_accepted": True,
        "deterministic_calculation_check_adr_accepted": True,
        "sequence_record_boundary_adr_accepted": True,
        "bounded_bh_control_family": "passed_disclosure_only_zero_findings",
        "post_mpp_regression_corpus": (
            "147_declared_cases_103_pytest_selectors_4_direct_audit_replays_passed"
        ),
        "post_mpp_module_baselines": "31_of_31_complete_development_only",
    }
    (ROOT / "HANDOFF_VERIFICATION.json").write_text(
        json.dumps(verification, indent=2) + "\n", encoding="utf-8"
    )
    print("Handoff verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
