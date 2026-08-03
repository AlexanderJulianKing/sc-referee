from __future__ import annotations

import json
import zipfile
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.capture import capture_review_submission, load_review_capture
from sc_referee_evaluation.cli import main as evaluation_main
from sc_referee_evaluation.fixture import (
    FixtureGenerationError,
    FixtureProofInputs,
    generate_control_fixture,
    generate_static_control_fixture,
    revalidate_fixture_proof,
)
from sc_referee_evaluation.founder_orientation_adapter import (
    FounderOrientationQualificationAdapter,
)
from sc_referee_evaluation.review_protocol import (
    build_stage1_review_packet,
    build_stage2_review_packet,
    freeze_scientific_label,
    freeze_stage1_panel,
)
from sc_referee_evaluation.stage3 import (
    build_stage3_review_packet,
    reconcile_detector_case,
)
from sc_referee_evaluation.static_qualification import (
    freeze_bounded_direction_profile,
    freeze_protocol_artifact,
    verify_bounded_direction_case,
)
from sc_referee_evaluation.typed_method_qualification import (
    freeze_typed_method_profile,
    verify_registered_typed_method_case,
)
from sc_referee_evaluation.workspace import build_blind_workspace

from sc_referee.controller import run_audit, run_demo
from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.interaction import (
    create_structured_answer,
    lock_semantics,
    record_answer,
    resume_semantics,
    submit_proposal,
    work_packet,
    work_queue,
)
from sc_referee.records.normalization import write_normalized_json
from sc_referee.records.observed import build_file_records
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.reporting.html import render_report
from sc_referee.reporting.policy import ReportContractError
from sc_referee.ro_crate import export_ro_crate, validate_ro_crate
from sc_referee.snapshot.repository import capture_repository
from sc_referee.storage.integrity import build_storage_manifest, verify_sqlite_index
from sc_referee.storage.jsonl import JsonlRecordStore
from sc_referee.storage.layout import AuditLayout
from sc_referee.storage.sqlite_index import rebuild_sqlite
from sc_referee.version import SCHEMA_VERSION


def _example(project_root: Path, name: str) -> dict[str, Any]:
    return json.loads(
        (project_root / "reference" / "schemas-v0.18.0" / "examples" / name).read_text(
            encoding="utf-8"
        )
    )


def _sorted_objects(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(values, key=semantic_digest)


def _negative_panel(
    project_root: Path,
    case_id: str,
    source_ref: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    stage1_template = _example(project_root, "agent-review.example.json")
    stage2_template = _example(project_root, "agent-review.stage2.example.json")
    reviews: list[dict[str, Any]] = []
    for provider, model, surface in (
        ("Anthropic", "claude-opus-5", "Claude Code"),
        ("OpenAI", "gpt-5.6-sol", "Codex"),
    ):
        for index in (1, 2):
            review = deepcopy(stage1_template)
            review["review_id"] = f"review:{case_id}:{provider.lower()}:stage1:{index}"
            review["case_id"] = case_id
            review["reviewer_agent"].update(
                {
                    "provider": provider,
                    "model_id": model,
                    "agent_surface": surface,
                    "execution_context_id": f"context:{case_id}:{provider}:stage1:{index}",
                }
            )
            review["completed_at"] = f"2026-07-27T18:0{index}:00Z"
            _make_negative_review(review, source_ref)
            reviews.append(review)
        review = deepcopy(stage2_template)
        review["review_id"] = f"review:{case_id}:{provider.lower()}:stage2"
        review["case_id"] = case_id
        review["reviewer_agent"].update(
            {
                "provider": provider,
                "model_id": model,
                "agent_surface": surface,
                "execution_context_id": f"context:{case_id}:{provider}:stage2",
            }
        )
        review["completed_at"] = "2026-07-27T18:30:00Z"
        _make_negative_review(review, source_ref)
        review["falsification_attempt"].update(
            {
                "outcome": "label_reversed",
                "material_dissent": False,
                "evidence_tested": [deepcopy(review["evidence"][0])],
            }
        )
        reviews.append(review)

    adjudication = _example(project_root, "benchmark-adjudication.example.json")
    adjudication.update(
        {
            "adjudication_id": f"benchmark-adjudication:{case_id}",
            "case_id": case_id,
            "label_status": "verified_good_eligible",
            "adjudicated_root_cause_refs": [],
            "root_cause_reconciliation_status": "not_applicable",
            "exclusion_reason": None,
            "stage1_review_refs": [
                {"record_type": "agent_review", "record_id": review["review_id"]}
                for review in reviews
                if review["stage"] == "stage1_blind"
            ],
            "stage2_review_refs": [
                {"record_type": "agent_review", "record_id": review["review_id"]}
                for review in reviews
                if review["stage"] == "stage2_scientific_adjudication"
            ],
        }
    )
    return reviews, adjudication


def _make_negative_review(review: dict[str, Any], source_ref: dict[str, Any]) -> None:
    review.update(
        {
            "verdict": "no_demonstrated_issue_within_scope",
            "bounded_statement": "No demonstrated issue was found within the declared scope.",
            "root_cause": None,
            "root_cause_identity": None,
            "issue_class": None,
        }
    )
    review["evidence"] = [
        {
            "evidence_id": f"evidence:{review['review_id']}",
            "description": "The exact output agrees with the declared claim in this scope.",
            "support_role": "supports",
            "source_refs": [deepcopy(source_ref)],
            "record_refs": [{"record_type": "claim", "record_id": "claim:1"}],
        }
    ]
    review["counterevidence_considered"] = []


def _lock_method_authority(repository: Path, schema_root: Path, tmp_path: Path) -> dict[str, Any]:
    source = tmp_path / "method-source-audit"
    initial = run_audit(repository, source, schema_root, report="report.md")
    question = next(
        item
        for item in initial["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id")
        == "check:founder-orientation-before-hmm-emission"
    )
    session = tmp_path / "method-authority-session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-27T16:40:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, str(item["work_item_id"]), schema_root)
    work_item = packet["work_item"]
    bounded = work_item["packet"]
    proposal = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "semantic_assertion",
        "assertion_id": "assertion:model-method-control-proposal",
        "audit_run_id": packet["audit_run_id"],
        "subject_ref": deepcopy(work_item["target_refs"][0]),
        "predicate": "proposed_scale_and_orientation",
        "object": "use_supplied_founder_alleles_directly_in_hmm_emission",
        "semantic_role": "inferred",
        "assertion_class": "implicit_scientific_inference",
        "epistemic_status": "proposed",
        "authority_scope": "none",
        "independently_checkable": False,
        "finding_eligibility": "ineligible",
        "verification": {"status": "not_checked", "method": "not_applicable"},
        "certainty": {"level": "low", "basis": "The scientist must decide."},
        "rationale": "The model proposal has no scientific authority.",
        "source_refs": [deepcopy(bounded["source_refs"][0])],
        "provenance": {
            "actor": {"actor_kind": "model", "actor_id": "model:test"},
            "method": "bounded_semantic_proposal",
            "created_at": "2026-07-27T16:41:00Z",
            "tool": "test-model-adapter",
            "tool_version": "1.0.0",
        },
        "extensions": {
            "x-work-item-ref": {
                "record_type": "work_item",
                "record_id": work_item["work_item_id"],
            },
            "x-packet-digest": bounded["packet_digest"],
            "x-prompt-template-digest": bounded["prompt_template_digest"],
        },
    }
    submit_proposal(
        session,
        str(item["work_item_id"]),
        proposal,
        schema_root,
        submitted_at="2026-07-27T16:41:00Z",
    )
    answer = create_structured_answer(
        session,
        str(question["question_id"]),
        {"scale_and_orientation": ("use_supplied_founder_alleles_directly_in_hmm_emission")},
        "scientist:test",
        schema_root,
        answered_at="2026-07-27T16:42:00Z",
    )
    record_answer(session, answer, schema_root)
    return lock_semantics(session, schema_root, locked_at="2026-07-27T16:43:00Z")


def _build_control_inputs(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    *,
    fixture_kind: str = "verified_good_fixture",
    method_static: bool = False,
) -> dict[str, Any]:
    is_static = fixture_kind.startswith("static_scope_")
    if method_static and not is_static:
        raise ValueError("Method-profile controls are static only.")
    detector_manifest: dict[str, Any] | None = None
    parser_manifests: list[dict[str, Any]] = []
    semantic_profile_manifests: list[dict[str, Any]] = []
    version_manifests: list[dict[str, Any]] = []
    selection_artifact: dict[str, Any] | None = None
    static_profile: dict[str, Any] | None = None
    assignment_artifact: dict[str, Any] | None = None
    if is_static:
        manifest_root = (
            project_root / "src" / "sc_referee" / "resources" / "capability-manifests-v1"
        )

        def records(name: str) -> list[dict[str, Any]]:
            return json.loads((manifest_root / name).read_text(encoding="utf-8"))["records"]

        detector_manifest = next(
            deepcopy(record)
            for record in records("detector-manifests.json")
            if record["detector_id"]
            == (
                "detector:bounded-analysis-method-conflict"
                if method_static
                else "detector:bounded-report-mean-direction"
            )
        )
        parser_ids = {"parser:markdown-inventory", "parser:python-ast-tokenize"}
        if not method_static:
            parser_ids.add("parser:tabular-delimited-header-inventory")
        parser_manifests = [
            deepcopy(record)
            for record in records("parser-manifests.json")
            if record["parser_id"] in parser_ids
        ]
        semantic_profile_manifests = [
            deepcopy(record)
            for record in records("profile-manifests.json")
            if record["profile_id"]
            == (
                "semantic-profile:bounded-analysis-method-conflict-v1"
                if method_static
                else "semantic-profile:bounded-report-mean-direction-v1"
            )
        ]
        version_manifests = [
            deepcopy(record)
            for record in records("version-manifests.json")
            if record["version_manifest_id"]
            == (
                "version-manifest:bounded-analysis-method-conflict-v1"
                if method_static
                else "version-manifest:bounded-report-mean-direction-v1"
            )
        ]
        if method_static:
            frozen_root = (
                project_root
                / "evaluation"
                / "qualification"
                / "bounded-analysis-method-conflict-v0.2.0-precase"
            )
            detector_manifest = json.loads(
                (frozen_root / "detector-manifest.json").read_text(encoding="utf-8")
            )
            parser_manifests = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in sorted(frozen_root.glob("parser-manifest.*.json"))
            ]
            semantic_profile_manifests = [
                json.loads(
                    (frozen_root / "semantic-profile-manifest.json").read_text(encoding="utf-8")
                )
            ]
            version_manifests = [
                json.loads((frozen_root / "version-manifest.json").read_text(encoding="utf-8"))
            ]
            for manifest in [
                detector_manifest,
                *parser_manifests,
                *semantic_profile_manifests,
                *version_manifests,
            ]:
                manifest["schema_version"] = "0.18.0"
        selection_artifact = freeze_protocol_artifact(
            "corpus_selection_protocol",
            "selection-protocol:static-control",
            "2026-07-27T16:50:00Z",
            {
                "selection_rule": (
                    "preassigned_bounded_analysis_method_control"
                    if method_static
                    else "preassigned_bounded_direction_control"
                )
            },
        )
        if method_static:
            binding = json.loads(
                (
                    project_root
                    / "evaluation"
                    / "qualification"
                    / "bounded-analysis-method-conflict-v0.2.0-precase"
                    / "method-conflict-binding.json"
                ).read_text(encoding="utf-8")
            )
            qualification_adapter = FounderOrientationQualificationAdapter()
            binding.pop("binding_digest")
            binding["detector_manifest_digest"] = semantic_digest(detector_manifest)
            binding["binding_digest"] = semantic_digest(binding)
            static_profile = freeze_typed_method_profile(
                binding=binding,
                adapter=qualification_adapter,
                detector_manifest=detector_manifest,
                parser_manifests=parser_manifests,
                semantic_profile_manifests=semantic_profile_manifests,
                version_manifests=version_manifests,
                selection_protocol_artifact=selection_artifact,
                candidate_suffixes=(".md", ".py"),
                frozen_at="2026-07-27T16:51:00Z",
            )
        else:
            static_profile = freeze_bounded_direction_profile(
                detector_manifest,
                parser_manifests,
                semantic_profile_manifests,
                version_manifests,
                selection_artifact,
                frozen_at="2026-07-27T16:51:00Z",
            )
        assignment_artifact = freeze_protocol_artifact(
            "opaque_case_assignment",
            "case-assignment:static-control",
            "2026-07-27T16:52:00Z",
            {
                "selected_report_path": "report.md",
                "selection_protocol_artifact_id": selection_artifact["artifact_id"],
                "selection_protocol_artifact_digest": selection_artifact["content_digest"],
            },
        )
    repository = tmp_path / "control-repository"
    repository.mkdir()
    if method_static:
        report_text = "The founder-origin HMM was fitted using the supplied founder alleles.\n"
        source_text = (
            "from pathlib import Path\n"
            "ROOT = Path(__file__).resolve().parent\n"
            "def emission_matrix(observed, founder_state, error):\n"
            "    return observed == founder_state\n"
            "def fit(sample, observed):\n"
            "    return emission_matrix(observed, sample.founder_alleles[0], 0.01)\n"
            "def main():\n"
            "    (ROOT / 'report.md').write_text(\n"
            "        'The founder-origin HMM was fitted using the supplied founder alleles.\\n'\n"
            "    )\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )
        (repository / "analysis.py").write_text(source_text, encoding="utf-8")
        (repository / "report.md").write_text(report_text, encoding="utf-8")
        evidence_text = report_text.strip()
        evidence_path = "report.md"
        evidence_line = 1
    elif is_static:
        report_text = (
            "# Results\n\ntreated increased expression relative to control.\n\nDifference: 2.0\n"
        )
        source_text = (
            "from pathlib import Path\n"
            "import csv\n"
            "def difference(path):\n"
            "    rows = list(csv.DictReader(path.open()))\n"
            "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
            "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
            "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
            "Path('PROJECT_CODE_EXECUTED').write_text('unsafe')\n"
            "Path('report.md').write_text(f'# Results\\n\\ntreated increased expression relative to control."
            "\\n\\nDifference: {difference(Path(\"data.csv\"))}\\n', encoding='utf-8')\n"
        )
        (repository / "analysis.py").write_text(source_text, encoding="utf-8")
        (repository / "data.csv").write_text(
            "group,expression\ntreated,3\ntreated,5\ncontrol,1\ncontrol,3\n",
            encoding="utf-8",
        )
        (repository / "report.md").write_text(report_text, encoding="utf-8")
        evidence_text = "treated increased expression relative to control."
        evidence_path = "report.md"
        evidence_line = 3
    else:
        source_text = "effect = 0.42\n"
        (repository / "analysis.py").write_text(source_text, encoding="utf-8")
        evidence_text = "effect = 0.42"
        evidence_path = "analysis.py"
        evidence_line = 1
    method_bundle = (
        _lock_method_authority(repository, schema_root, tmp_path) if method_static else None
    )
    snapshot_result = capture_repository(
        repository,
        tmp_path / "control-captured",
        "audit:control-fixture",
        captured_at="2026-07-27T17:00:00Z",
    )
    public_files = build_file_records(
        snapshot_result.file_records,
        snapshot_result.asset_identity_records,
        str(snapshot_result.snapshot_record["snapshot_id"]),
        "2026-07-27T17:00:00Z",
    )
    source_ref = {
        "source_kind": "file_span",
        "locator": f"{evidence_path}:{evidence_line}",
        "path": evidence_path,
        "content_digest": sha256_digest((repository / evidence_path).read_bytes()),
        "start_line": evidence_line,
        "end_line": evidence_line,
        "quoted_text": evidence_text,
    }
    reviews, adjudication = _negative_panel(project_root, "case:control", source_ref)
    if fixture_kind in {"hard_negative_fixture", "static_scope_hard_negative"}:
        adjudication["label_status"] = "hard_negative_eligible"

    workspace_manifest = build_blind_workspace(
        snapshot_result.materialized_root,
        tmp_path / "control-workspace",
        tmp_path / "control-workspace.manifest.json",
        (
            [
                {"path": "analysis.py", "role": "workflow_source"},
                {"path": "data.csv", "role": "staged_data"},
                {"path": "report.md", "role": "report"},
            ]
            if is_static and not method_static
            else (
                [
                    {"path": "analysis.py", "role": "workflow_source"},
                    {"path": "report.md", "role": "report"},
                ]
                if method_static
                else [{"path": "analysis.py", "role": "workflow_source"}]
            )
        ),
        snapshot=snapshot_result.snapshot_record,
        file_records=public_files,
        asset_identities=snapshot_result.asset_identity_records,
        created_at="2026-07-27T17:05:00Z",
    )

    if method_static:
        assert method_bundle is not None
        material_questions = [
            deepcopy(item)
            for item in method_bundle["material_questions"]
            if item.get("extensions", {}).get("x-scientific-check-id")
            == "check:founder-orientation-before-hmm-emission"
        ]
        answers = [deepcopy(item) for item in method_bundle["answers"]]
        semantic_assertions = [deepcopy(item) for item in method_bundle["semantic_assertions"]]
        contract_id = material_questions[0]["extensions"]["x-contract-ref"]["record_id"]
        contract = deepcopy(
            next(
                item
                for item in method_bundle["scientific_contracts"]
                if item["contract_id"] == contract_id
            )
        )
        operation_id = material_questions[0]["extensions"]["x-scientific-check-scope-join-path"][0][
            "target_ref"
        ]["record_id"]
        operation = deepcopy(
            next(
                item for item in method_bundle["operations"] if item["operation_id"] == operation_id
            )
        )
    else:
        material_questions = []
        answers = []
        semantic_assertions = []
        contract = _example(project_root, "scientific-contract.example.json")
        contract["source_refs"] = [deepcopy(source_ref)]
        operation = _example(project_root, "operation.example.json")
        operation["operation_id"] = "operation:control"
        operation["source_refs"] = [deepcopy(source_ref)]
    operation_ref = {"record_type": "operation", "record_id": operation["operation_id"]}
    contract_ref = {
        "record_type": "scientific_contract",
        "record_id": contract["contract_id"],
    }
    claim = _example(project_root, "claim.example.json")
    if is_static and not method_static:
        claim["text"] = evidence_text
        claim["source_refs"] = [deepcopy(source_ref)]
    if method_static:
        question_ref = {
            "record_type": "material_question",
            "record_id": material_questions[0]["question_id"],
        }
        for review in reviews:
            review["evidence"][0]["record_refs"] = [deepcopy(question_ref)]

    environment = _example(project_root, "environment.example.json")
    environment.update(
        {
            "environment_id": "environment:project-control",
            "environment_kind": "project_runtime",
            "identity_status": "exact",
            "limitations": [],
        }
    )
    environment["provenance"]["created_at"] = "2026-07-27T17:10:00Z"
    capability = _example(project_root, "sandbox-capability.example.json")
    capability["sandbox_capability_id"] = "sandbox:control-rootless"
    capability["captured_at"] = "2026-07-27T17:20:00Z"
    execution = _example(project_root, "execution.auditor-verification.example.json")
    execution.update(
        {
            "execution_id": "execution:project-control",
            "execution_kind": "project_workflow",
            "actor": "project_workflow",
            "method": "authorized_project_workflow_capture",
            "environment_ref": {
                "record_type": "environment",
                "record_id": environment["environment_id"],
            },
            "input_refs": [{"record_type": "claim", "record_id": "claim:1"}],
            "output_refs": [{"record_type": "claim", "record_id": "claim:1"}],
            "identity_strength": "exact",
            "limitations": [],
            "timing": {
                "state": "observed",
                "started_at": "2026-07-27T17:30:00Z",
                "finished_at": "2026-07-27T17:40:00Z",
            },
            "exit": {"state": "succeeded", "code": 0},
            "sandbox": {
                "project_code_executed": True,
                "authorization_status": "authorized",
                "network_policy": "denied",
                "sandbox_capability_ref": {
                    "record_type": "sandbox_capability",
                    "record_id": capability["sandbox_capability_id"],
                },
            },
        }
    )

    hard_evidence = {
        "suspicious_pattern": [],
        "decisive_innocent_explanation": [],
    }
    if fixture_kind in {"hard_negative_fixture", "static_scope_hard_negative"}:
        hard_evidence = {
            "suspicious_pattern": [
                {
                    "evidence_id": "evidence:suspicious-sign",
                    "description": "The negative lexical pattern could trigger a sign detector.",
                    "support_role": "context",
                    "source_refs": [deepcopy(source_ref)],
                }
            ],
            "decisive_innocent_explanation": [
                {
                    "evidence_id": "evidence:innocent-orientation",
                    "description": "The declared orientation makes the observed sign correct.",
                    "support_role": "counterevidence",
                    "record_refs": [deepcopy(contract_ref)],
                }
            ],
        }
    answer_refs = _sorted_objects(
        [
            deepcopy(contract_ref),
            *(
                [
                    {
                        "record_type": "material_question",
                        "record_id": item["question_id"],
                    }
                    for item in material_questions
                ]
                if method_static
                else []
            ),
            *(
                [{"record_type": "answer", "record_id": item["answer_id"]} for item in answers]
                if method_static
                else []
            ),
            *(
                [
                    {
                        "record_type": "semantic_assertion",
                        "record_id": item["assertion_id"],
                    }
                    for item in semantic_assertions
                ]
                if method_static
                else []
            ),
            *[
                deepcopy(ref)
                for category in hard_evidence.values()
                for item in category
                for ref in item.get("record_refs", [])
            ],
            *(
                [
                    {
                        "record_type": "file_record",
                        "record_id": next(
                            record["file_record_id"]
                            for record in public_files
                            if record["path"] == evidence_path
                        ),
                    }
                ]
                if hard_evidence["suspicious_pattern"]
                else []
            ),
        ]
    )
    answer_refs = list({semantic_digest(ref): ref for ref in answer_refs}.values())
    answer_refs = _sorted_objects(answer_refs)
    execution_ref = {"record_type": "execution", "record_id": execution["execution_id"]}
    adjudication["answer_side_evidence_refs"] = deepcopy(answer_refs)

    stage1_reviews = [review for review in reviews if review["stage"] == "stage1_blind"]
    stage2_reviews = [
        review for review in reviews if review["stage"] == "stage2_scientific_adjudication"
    ]
    stage1_packets: list[dict[str, Any]] = []
    stage1_manifests: list[dict[str, Any]] = []
    stage1_capture_paths: list[Path] = []
    for index, review in enumerate(stage1_reviews, start=1):
        packet = build_stage1_review_packet(
            str(review["case_id"]),
            workspace_manifest,
            review["reviewer_agent"],
            "Review only the supplied control workflow.",
            created_at="2026-07-27T17:10:00Z",
        )
        review["reviewer_agent"] = deepcopy(packet["expected_reviewer_agent"])
        review["extensions"] = {"x-review-packet-digest": packet["packet_digest"]}
        transcript = tmp_path / f"control-stage1-{index}.txt"
        transcript.write_text(f"Control Stage-1 transcript {index}.\n", encoding="utf-8")
        review["transcript_digest"] = sha256_digest(transcript.read_bytes())
        destination = tmp_path / f"control-stage1-{index}.capture"
        manifest = capture_review_submission(
            review,
            packet,
            transcript,
            schema_root,
            captured_at="2026-07-27T18:05:00Z",
            destination=destination,
        )
        stage1_packets.append(packet)
        stage1_manifests.append(manifest)
        stage1_capture_paths.append(destination)
    stage1_freeze = freeze_stage1_panel(
        stage1_reviews,
        stage1_packets,
        stage1_manifests,
        schema_root,
        frozen_at="2026-07-27T18:10:00Z",
        output=tmp_path / "control-stage1.freeze.json",
    )
    stage2_capture_paths: list[Path] = []
    stage2_packets: list[dict[str, Any]] = []
    stage2_manifests: list[dict[str, Any]] = []
    for index, review in enumerate(stage2_reviews, start=1):
        packet = build_stage2_review_packet(
            stage1_freeze,
            stage1_reviews,
            review["reviewer_agent"],
            "Adjudicate the frozen control evidence.",
            created_at="2026-07-27T18:11:00Z",
            answer_side_evidence_refs=answer_refs,
            reference_analysis_refs=([] if method_static else [deepcopy(operation_ref)]),
            execution_comparison_refs=([] if is_static else [deepcopy(execution_ref)]),
        )
        review["reviewer_agent"] = deepcopy(packet["expected_reviewer_agent"])
        review["extensions"] = {
            "x-review-packet-digest": packet["packet_digest"],
            "x-stage1-freeze-digest": stage1_freeze["freeze_digest"],
        }
        transcript = tmp_path / f"control-stage2-{index}.txt"
        transcript.write_text(f"Control Stage-2 transcript {index}.\n", encoding="utf-8")
        review["transcript_digest"] = sha256_digest(transcript.read_bytes())
        destination = tmp_path / f"control-stage2-{index}.capture"
        manifest = capture_review_submission(
            review,
            packet,
            transcript,
            schema_root,
            captured_at="2026-07-27T18:40:00Z",
            destination=destination,
        )
        stage2_packets.append(packet)
        stage2_manifests.append(manifest)
        stage2_capture_paths.append(destination)

    scientific_label_freeze = None
    static_label_artifact = None
    static_proof = None
    if is_static:
        scientific_label_freeze = freeze_scientific_label(
            adjudication,
            stage1_freeze,
            stage2_reviews,
            stage2_packets,
            stage2_manifests,
            schema_root,
            frozen_at="2026-07-27T19:05:00Z",
            output=tmp_path / "static-control.label-freeze.json",
        )
        static_label_artifact = freeze_protocol_artifact(
            "scientific_label_freeze",
            "label-artifact:static-control",
            "2026-07-27T19:06:00Z",
            {
                "adjudication_digest": semantic_digest(adjudication),
                "adjudication_id": adjudication["adjudication_id"],
                "case_id": adjudication["case_id"],
                "label_status": adjudication["label_status"],
                "scientific_label_freeze_digest": scientific_label_freeze["freeze_digest"],
            },
        )
        assert static_profile is not None
        assert assignment_artifact is not None
        assert detector_manifest is not None
        if method_static:
            static_proof = verify_registered_typed_method_case(
                workspace_root=snapshot_result.materialized_root,
                profile=static_profile,
                adapter=FounderOrientationQualificationAdapter(),
                case_assignment_artifact=assignment_artifact,
                label_freeze_artifact=static_label_artifact,
                snapshot=snapshot_result.snapshot_record,
                file_records=public_files,
                asset_identities=snapshot_result.asset_identity_records,
                material_questions=material_questions,
                answers=answers,
                scientific_contracts=[contract],
                semantic_assertions=semantic_assertions,
                detector_manifest=detector_manifest,
                parser_manifests=parser_manifests,
                semantic_profile_manifests=semantic_profile_manifests,
                version_manifests=version_manifests,
                proof_frozen_at="2026-07-27T19:07:00Z",
            )
        else:
            static_proof = verify_bounded_direction_case(
                snapshot_result.materialized_root,
                static_profile,
                assignment_artifact,
                static_label_artifact,
                snapshot_result.snapshot_record,
                public_files,
                snapshot_result.asset_identity_records,
                detector_manifest=detector_manifest,
                parser_manifests=parser_manifests,
                semantic_profile_manifests=semantic_profile_manifests,
                version_manifests=version_manifests,
                proof_frozen_at="2026-07-27T19:07:00Z",
            )

    fixture_spec = {
        "problem_id": "problem:control-compiler",
        "fixture_kind": fixture_kind,
        "declared_scope": {
            "claim_refs": (
                [] if method_static else [{"record_type": "claim", "record_id": "claim:1"}]
            ),
            "detector_ids": (
                ["detector:bounded-analysis-method-conflict"]
                if method_static
                else ["detector:bounded-report-mean-direction"]
                if is_static
                else ["detector:claim-sign"]
            ),
            "issue_classes": [
                "x-review-scoped-analysis-method-requirement-mismatch"
                if method_static
                else "claim_result_disagreement"
                if is_static
                else "claim_result_agreement"
            ],
            "operation_refs": [] if method_static else [operation_ref],
        },
        "scientific_contract_refs": [contract_ref],
        "execution_evidence": "not_executed" if is_static else "clean_environment_executed",
        "hard_negative_evidence": hard_evidence,
        "limitations": ["The control is bounded to one claim and one operation."],
    }
    return {
        "adjudication": adjudication,
        "stage1_capture_directories": stage1_capture_paths,
        "stage2_capture_directories": stage2_capture_paths,
        "stage1_freeze": stage1_freeze,
        "workspace_manifests": [workspace_manifest],
        "snapshot": snapshot_result.snapshot_record,
        "file_records": public_files,
        "asset_identities": snapshot_result.asset_identity_records,
        "materialized_root": snapshot_result.materialized_root,
        "scientific_contracts": [contract],
        "operations": [] if method_static else [operation],
        "environments": [] if is_static else [environment],
        "executions": [] if is_static else [execution],
        "sandbox_capabilities": [] if is_static else [capability],
        "evidence_records": [] if method_static else [claim],
        "material_questions": material_questions,
        "answers": answers,
        "semantic_assertions": semantic_assertions,
        "fixture_spec": fixture_spec,
        "schema_root": schema_root,
        "created_at": "2026-07-27T20:00:00Z",
        "static_qualification_profile": static_profile,
        "static_qualification_proof": static_proof,
        "case_assignment_artifact": assignment_artifact,
        "static_label_freeze_artifact": static_label_artifact,
        "scientific_label_freeze": scientific_label_freeze,
        "detector_manifest": detector_manifest,
        "parser_manifests": parser_manifests,
        "semantic_profile_manifests": semantic_profile_manifests,
        "version_manifests": version_manifests,
    }


def _generate(inputs: dict[str, Any], output: Path) -> dict[str, Any]:
    static_fields = {
        "static_qualification_profile",
        "static_qualification_proof",
        "case_assignment_artifact",
        "static_label_freeze_artifact",
        "scientific_label_freeze",
        "detector_manifest",
        "parser_manifests",
        "semantic_profile_manifests",
        "version_manifests",
        "material_questions",
        "answers",
        "semantic_assertions",
    }
    return generate_control_fixture(
        **{key: value for key, value in inputs.items() if key not in static_fields},
        output=output,
    )


def _proof_inputs(inputs: dict[str, Any]) -> FixtureProofInputs:
    return FixtureProofInputs(
        stage1_capture_directories=inputs["stage1_capture_directories"],
        stage2_capture_directories=inputs["stage2_capture_directories"],
        stage1_freeze=inputs["stage1_freeze"],
        workspace_manifests=inputs["workspace_manifests"],
        snapshot=inputs["snapshot"],
        file_records=inputs["file_records"],
        asset_identities=inputs["asset_identities"],
        materialized_root=inputs["materialized_root"],
        scientific_contracts=inputs["scientific_contracts"],
        operations=inputs["operations"],
        environments=inputs["environments"],
        executions=inputs["executions"],
        sandbox_capabilities=inputs["sandbox_capabilities"],
        evidence_records=inputs["evidence_records"],
        static_qualification_profile=inputs.get("static_qualification_profile"),
        static_qualification_proof=inputs.get("static_qualification_proof"),
        case_assignment_artifact=inputs.get("case_assignment_artifact"),
        static_label_freeze_artifact=inputs.get("static_label_freeze_artifact"),
        scientific_label_freeze=inputs.get("scientific_label_freeze"),
        detector_manifest=inputs.get("detector_manifest"),
        parser_manifests=inputs.get("parser_manifests", []),
        semantic_profile_manifests=inputs.get("semantic_profile_manifests", []),
        version_manifests=inputs.get("version_manifests", []),
        material_questions=inputs.get("material_questions", []),
        answers=inputs.get("answers", []),
        semantic_assertions=inputs.get("semantic_assertions", []),
    )


def test_verified_good_control_compiles_exact_clean_execution_proof(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _build_control_inputs(project_root, schema_root, tmp_path)

    fixture = _generate(inputs, tmp_path / "verified-good.json")

    assert fixture["fixture_kind"] == "verified_good_fixture"
    assert fixture["qualification_proof_status"] == "complete"
    assert fixture["execution_evidence"] == "clean_environment_executed"
    proof = fixture["proof_evidence"]
    assert len(proof["public_inputs"]["executions"]) == 1
    assert len(proof["public_inputs"]["environments"]) == 1
    assert len(proof["public_inputs"]["sandbox_capabilities"]) == 1
    assert len(proof["protocol_artifacts"]["review_captures"]) == 6
    assert fixture["global_correctness_claim_allowed"] is False
    report = revalidate_fixture_proof(
        fixture,
        inputs["adjudication"],
        [],
        _proof_inputs(inputs),
        schema_root,
    )
    assert report["label_admission"] == "admitted_for_declared_fixture_scope"

    drifted = deepcopy(fixture)
    drifted["proof_evidence"]["public_inputs"]["executions"][0]["semantic_digest"] = (
        "sha256:" + "0" * 64
    )
    with pytest.raises(FixtureGenerationError, match="does not equal"):
        revalidate_fixture_proof(
            drifted,
            inputs["adjudication"],
            [],
            _proof_inputs(inputs),
            schema_root,
        )


@pytest.mark.parametrize(
    "fixture_kind",
    ["static_scope_verified_good", "static_scope_hard_negative"],
)
def test_static_control_compiles_and_replays_without_execution_authority(
    project_root: Path, schema_root: Path, tmp_path: Path, fixture_kind: str
) -> None:
    inputs = _build_control_inputs(
        project_root,
        schema_root,
        tmp_path,
        fixture_kind=fixture_kind,
    )
    proof_inputs = _proof_inputs(inputs)
    fixture = generate_static_control_fixture(
        inputs["adjudication"],
        [],
        proof_inputs,
        inputs["fixture_spec"],
        schema_root,
        created_at=inputs["created_at"],
        output=tmp_path / "static-control.json",
    )

    assert fixture["fixture_kind"] == fixture_kind
    assert fixture["execution_evidence"] == "not_executed"
    public_inputs = fixture["proof_evidence"]["public_inputs"]
    assert public_inputs["environments"] == []
    assert public_inputs["executions"] == []
    assert public_inputs["sandbox_capabilities"] == []
    assert len(public_inputs["static_qualification_proofs"]) == 1
    hard_evidence = fixture["proof_evidence"]["hard_negative_evidence"]
    assert bool(hard_evidence["suspicious_pattern"]) is fixture_kind.endswith("hard_negative")
    assert not (tmp_path / "PROJECT_CODE_EXECUTED").exists()
    report = revalidate_fixture_proof(
        fixture,
        inputs["adjudication"],
        [],
        proof_inputs,
        schema_root,
    )
    assert report["label_admission"] == "admitted_for_declared_fixture_scope"


def test_analysis_method_static_control_compiles_and_replays_exact_authority(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _build_control_inputs(
        project_root,
        schema_root,
        tmp_path,
        fixture_kind="static_scope_verified_good",
        method_static=True,
    )
    proof_inputs = _proof_inputs(inputs)
    fixture = generate_static_control_fixture(
        inputs["adjudication"],
        [],
        proof_inputs,
        inputs["fixture_spec"],
        schema_root,
        created_at=inputs["created_at"],
        output=tmp_path / "static-method-control.json",
    )

    public = fixture["proof_evidence"]["public_inputs"]
    assert fixture["declared_scope"]["detector_ids"] == [
        "detector:bounded-analysis-method-conflict"
    ]
    assert len(public["material_questions"]) == 1
    assert len(public["answers"]) == 1
    assert public["semantic_assertions"]
    assert public["executions"] == []
    assert inputs["static_qualification_profile"]["profile_kind"] == (
        "typed_static_method_conflict_v1"
    )
    assert inputs["static_qualification_proof"]["proof_profile_kind"] == (
        "typed_static_method_conflict_v1"
    )
    assert inputs["static_qualification_proof"]["proof_status"] == "complete"
    assert inputs["static_qualification_proof"]["derived_facts"]["comparison"]["outcome"] == (
        "covered_negative"
    )
    assert (
        revalidate_fixture_proof(
            fixture,
            inputs["adjudication"],
            [],
            proof_inputs,
            schema_root,
        )["label_admission"]
        == "admitted_for_declared_fixture_scope"
    )


def test_typed_method_static_cli_verifies_and_replays_exact_proof(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _build_control_inputs(
        project_root,
        schema_root,
        tmp_path,
        fixture_kind="static_scope_verified_good",
        method_static=True,
    )

    def write_object(name: str, value: dict[str, Any]) -> Path:
        path = tmp_path / f"cli-{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def write_jsonl(name: str, values: list[dict[str, Any]]) -> Path:
        path = tmp_path / f"cli-{name}.jsonl"
        path.write_text("".join(json.dumps(item) + "\n" for item in values), encoding="utf-8")
        return path

    objects = {
        name: write_object(name, inputs[key])
        for name, key in (
            ("profile", "static_qualification_profile"),
            ("assignment", "case_assignment_artifact"),
            ("label", "static_label_freeze_artifact"),
            ("snapshot", "snapshot"),
            ("detector", "detector_manifest"),
        )
    }
    collections = {
        name: write_jsonl(name, inputs[key])
        for name, key in (
            ("files", "file_records"),
            ("identities", "asset_identities"),
            ("questions", "material_questions"),
            ("answers", "answers"),
            ("contracts", "scientific_contracts"),
            ("assertions", "semantic_assertions"),
        )
    }
    manifest_options: list[str] = []
    for option, key in (
        ("--parser-manifest", "parser_manifests"),
        ("--semantic-profile-manifest", "semantic_profile_manifests"),
        ("--version-manifest", "version_manifests"),
    ):
        for index, record in enumerate(inputs[key]):
            path = write_object(f"{key}-{index}", record)
            manifest_options.extend([option, str(path)])

    common = [
        "--materialized-root",
        str(inputs["materialized_root"]),
        "--profile",
        str(objects["profile"]),
        "--detector-manifest",
        str(objects["detector"]),
        *manifest_options,
        "--case-assignment-artifact",
        str(objects["assignment"]),
        "--label-freeze-artifact",
        str(objects["label"]),
        "--snapshot",
        str(objects["snapshot"]),
        "--file-records-jsonl",
        str(collections["files"]),
        "--asset-identities-jsonl",
        str(collections["identities"]),
        "--material-questions-jsonl",
        str(collections["questions"]),
        "--answers-jsonl",
        str(collections["answers"]),
        "--scientific-contracts-jsonl",
        str(collections["contracts"]),
        "--semantic-assertions-jsonl",
        str(collections["assertions"]),
    ]
    proof_path = tmp_path / "cli-typed-proof.json"
    assert (
        evaluation_main(
            [
                "verify-typed-method-static-case",
                *common,
                "--proof-frozen-at",
                "2026-07-27T19:07:00Z",
                "--output",
                str(proof_path),
            ]
        )
        == 0
    )
    expected = inputs["static_qualification_proof"]
    assert json.loads(proof_path.read_text(encoding="utf-8")) == expected

    replay_path = tmp_path / "cli-typed-proof-replay.json"
    assert (
        evaluation_main(
            [
                "replay-typed-method-static-case",
                "--source-proof",
                str(proof_path),
                *common,
                "--output",
                str(replay_path),
            ]
        )
        == 0
    )
    assert replay_path.read_bytes() == proof_path.read_bytes()


def test_static_control_rejects_execution_inputs_and_proof_drift(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _build_control_inputs(
        project_root,
        schema_root,
        tmp_path,
        fixture_kind="static_scope_verified_good",
    )
    proof_inputs = _proof_inputs(inputs)
    fixture = generate_static_control_fixture(
        inputs["adjudication"],
        [],
        proof_inputs,
        inputs["fixture_spec"],
        schema_root,
        created_at=inputs["created_at"],
        output=tmp_path / "static-control.json",
    )

    with_execution = FixtureProofInputs(
        **{
            **proof_inputs.__dict__,
            "environments": [_example(project_root, "environment.example.json")],
        }
    )
    with pytest.raises(FixtureGenerationError, match="execution, environment, or sandbox"):
        revalidate_fixture_proof(
            fixture,
            inputs["adjudication"],
            [],
            with_execution,
            schema_root,
        )

    changed = deepcopy(proof_inputs.static_qualification_proof)
    assert changed is not None
    changed["limitations"].append("mutation")
    drifted = FixtureProofInputs(**{**proof_inputs.__dict__, "static_qualification_proof": changed})
    with pytest.raises(FixtureGenerationError, match="Static qualification proof replay failed"):
        revalidate_fixture_proof(
            fixture,
            inputs["adjudication"],
            [],
            drifted,
            schema_root,
        )


@pytest.mark.parametrize("method_static", [False, True])
def test_report_names_static_scope_without_claiming_execution(
    project_root: Path, schema_root: Path, tmp_path: Path, method_static: bool
) -> None:
    inputs = _build_control_inputs(
        project_root,
        schema_root,
        tmp_path,
        fixture_kind="static_scope_verified_good",
        method_static=method_static,
    )
    bundle = _example(project_root, "audit-bundle.example.json")
    bundle["detector_manifests"].append(inputs["detector_manifest"])
    bundle["parser_manifests"] = inputs["parser_manifests"]
    bundle["repository_snapshots"] = [inputs["snapshot"]]
    bundle["file_records"] = inputs["file_records"]
    bundle["asset_identities"] = inputs["asset_identities"]
    bundle["static_qualification_profiles"] = [inputs["static_qualification_profile"]]
    bundle["static_qualification_proofs"] = [inputs["static_qualification_proof"]]
    claim = bundle["claims"][0]
    claim["lineage"]["input_refs"] = []
    claim["lineage"]["operation_refs"] = []
    claim["lineage"]["result_refs"] = []
    claim["report_ref"] = {"record_type": "artifact", "record_id": "artifact:report"}
    bundle["artifacts"] = [
        {
            "record_type": "artifact",
            "artifact_id": "artifact:report",
        }
    ]
    bundle["reproduction_requests"] = []
    grade_counts = bundle["coverage_records"][0]["claim_coverage"]["lineage_grade_counts"]
    statuses = ("complete", "partial", "missing", "unavailable", "opaque")
    for dimension in grade_counts:
        counts = {status: 0 for status in statuses}
        for claim in bundle["claims"]:
            counts[claim["lineage"]["grades"][dimension]["status"]] += 1
        counts["total"] = len(bundle["claims"])
        grade_counts[dimension] = counts
    bundle["coverage_records"][0]["claim_coverage"]["claims_total"] = len(bundle["claims"])
    bundle["coverage_records"][0]["claim_coverage"]["claims_with_complete_lineage"] = sum(
        claim["lineage"]["status"] == "complete" for claim in bundle["claims"]
    )
    bundle["coverage_records"][0]["extensions"] = {
        "x-run-state": "complete",
        "x-pending-work": [],
    }

    report = tmp_path / "static-proof-report.html"
    render_report(bundle, report)
    html = report.read_text(encoding="utf-8")
    assert "Static qualification proof records" in html
    assert "does not claim project execution" in html
    assert "No project-authored code was executed by this proof" in html

    drifted = deepcopy(bundle)
    drifted["static_qualification_proofs"][0]["retained_bytes"][0]["content_digest"] = (
        "sha256:" + "0" * 64
    )
    with pytest.raises(ReportContractError):
        render_report(drifted, tmp_path / "static-proof-drift.html")


@pytest.mark.parametrize("method_static", [False, True])
def test_static_proof_records_round_trip_canonical_jsonl_and_disposable_sqlite(
    project_root: Path, schema_root: Path, tmp_path: Path, method_static: bool
) -> None:
    inputs = _build_control_inputs(
        project_root,
        schema_root,
        tmp_path,
        fixture_kind="static_scope_verified_good",
        method_static=method_static,
    )
    records = [
        inputs["static_qualification_profile"],
        inputs["static_qualification_proof"],
    ]
    store = JsonlRecordStore(tmp_path / "records")
    for record in records:
        store.append(record)

    assert list(store.iter_records()) == sorted(records, key=lambda item: item["record_type"])
    sqlite_path = tmp_path / "audit.db"
    assert rebuild_sqlite(sqlite_path, records) == 2
    verify_sqlite_index(sqlite_path, records)


def test_analysis_method_static_records_round_trip_attached_ro_crate(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _build_control_inputs(
        project_root,
        schema_root,
        tmp_path,
        fixture_kind="static_scope_verified_good",
        method_static=True,
    )
    profile = inputs["static_qualification_profile"]
    proof = inputs["static_qualification_proof"]
    assert isinstance(profile, dict)
    assert isinstance(proof, dict)

    audit_root = tmp_path / "crate-audit"
    bundle = run_demo(project_root / "examples" / "walking-skeleton", audit_root, schema_root)
    bundle["detector_manifests"] = [inputs["detector_manifest"]]
    bundle["parser_manifests"] = inputs["parser_manifests"]
    bundle["repository_snapshots"].append(inputs["snapshot"])
    bundle["file_records"].extend(inputs["file_records"])
    bundle["asset_identities"].extend(inputs["asset_identities"])
    bundle["static_qualification_profiles"] = [profile]
    bundle["static_qualification_proofs"] = [proof]
    derived_store = JsonlRecordStore(audit_root / "derived")
    for record in [
        inputs["detector_manifest"],
        *inputs["parser_manifests"],
        inputs["snapshot"],
        *inputs["file_records"],
        *inputs["asset_identities"],
        profile,
        proof,
    ]:
        derived_store.append(record)

    layout = AuditLayout(audit_root)
    manifest = build_storage_manifest(layout, bundle["audit_run_id"], bundle["generated_at"])
    bundle["storage_manifests"] = [manifest]
    registry = LocalSchemaRegistry(schema_root)
    registry.validate(manifest)
    registry.validate(bundle)
    write_normalized_json(audit_root / "derived" / "storage-manifest.jsonl", manifest)
    write_normalized_json(audit_root / "audit.bundle.json", bundle)
    records = [
        record
        for value in bundle.values()
        if isinstance(value, list)
        for record in value
        if isinstance(record, dict) and isinstance(record.get("record_type"), str)
    ]
    rebuild_sqlite(audit_root / "audit.db", records)
    render_report(bundle, audit_root / "report.html")

    archive = tmp_path / "method-static-proof.zip"
    exported = export_ro_crate(
        audit_root,
        archive,
        schema_root,
        author_name="Static qualification test",
        license_uri="https://spdx.org/licenses/Apache-2.0.html",
        license_name="Apache License 2.0",
    )
    assert validate_ro_crate(archive, schema_root) == exported
    assert {
        ("static_qualification_profile", profile["profile_id"]),
        ("static_qualification_proof", proof["proof_id"]),
    } <= {(item["record_type"], item["record_id"]) for item in exported["entity_refs"]}
    with zipfile.ZipFile(archive) as crate:
        assert "native/derived/static-qualification-profile.jsonl" in crate.namelist()
        assert "native/derived/static-qualification-proof.jsonl" in crate.namelist()


def test_control_fixture_cli_preserves_the_complete_proof_projection(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _build_control_inputs(project_root, schema_root, tmp_path)
    object_paths: dict[str, list[Path]] = {}
    for name, records in {
        "adjudication": [inputs["adjudication"]],
        "stage1-freeze": [inputs["stage1_freeze"]],
        "workspace-manifest": inputs["workspace_manifests"],
        "snapshot": [inputs["snapshot"]],
        "scientific-contract": inputs["scientific_contracts"],
        "operation": inputs["operations"],
        "environment": inputs["environments"],
        "execution": inputs["executions"],
        "sandbox-capability": inputs["sandbox_capabilities"],
        "evidence-record": inputs["evidence_records"],
        "fixture-spec": [inputs["fixture_spec"]],
    }.items():
        paths: list[Path] = []
        for index, record in enumerate(records):
            path = tmp_path / f"cli-{name}-{index}.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            paths.append(path)
        object_paths[name] = paths

    file_records_path = tmp_path / "cli-file-records.jsonl"
    identities_path = tmp_path / "cli-asset-identities.jsonl"
    file_records_path.write_text(
        "".join(json.dumps(record) + "\n" for record in inputs["file_records"]),
        encoding="utf-8",
    )
    identities_path.write_text(
        "".join(json.dumps(record) + "\n" for record in inputs["asset_identities"]),
        encoding="utf-8",
    )
    output = tmp_path / "cli-control-fixture.json"
    arguments = [
        "generate-control-fixture",
        "--adjudication",
        str(object_paths["adjudication"][0]),
        "--stage1-freeze",
        str(object_paths["stage1-freeze"][0]),
        "--snapshot",
        str(object_paths["snapshot"][0]),
        "--file-records-jsonl",
        str(file_records_path),
        "--asset-identities-jsonl",
        str(identities_path),
        "--materialized-root",
        str(inputs["materialized_root"]),
        "--fixture-spec",
        str(object_paths["fixture-spec"][0]),
        "--schema-root",
        str(schema_root),
        "--created-at",
        str(inputs["created_at"]),
        "--output",
        str(output),
    ]
    for capture in inputs["stage1_capture_directories"]:
        arguments.extend(["--stage1-capture", str(capture)])
    for capture in inputs["stage2_capture_directories"]:
        arguments.extend(["--stage2-capture", str(capture)])
    for option in (
        "workspace-manifest",
        "scientific-contract",
        "operation",
        "environment",
        "execution",
        "sandbox-capability",
        "evidence-record",
    ):
        for path in object_paths[option]:
            arguments.extend([f"--{option}", str(path)])

    assert evaluation_main(arguments) == 0
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["qualification_proof_status"] == "complete"
    assert persisted["proof_evidence"]["protocol_artifacts"]["review_captures"]
    assert (
        revalidate_fixture_proof(
            persisted,
            inputs["adjudication"],
            [],
            _proof_inputs(inputs),
            schema_root,
        )["label_admission"]
        == "admitted_for_declared_fixture_scope"
    )


@pytest.mark.parametrize(
    ("static_control", "method_static"),
    [(False, False), (True, False), (True, True)],
)
def test_stage3_replays_complete_control_proof_before_metric_admission(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    static_control: bool,
    method_static: bool,
) -> None:
    inputs = _build_control_inputs(
        project_root,
        schema_root,
        tmp_path,
        fixture_kind=("static_scope_verified_good" if static_control else "verified_good_fixture"),
        method_static=method_static,
    )
    fixture = (
        generate_static_control_fixture(
            inputs["adjudication"],
            [],
            _proof_inputs(inputs),
            inputs["fixture_spec"],
            schema_root,
            created_at=inputs["created_at"],
            output=tmp_path / "stage3-control-fixture.json",
        )
        if static_control
        else _generate(inputs, tmp_path / "stage3-control-fixture.json")
    )
    stage1_reviews = [
        load_review_capture(path, schema_root)[0] for path in inputs["stage1_capture_directories"]
    ]
    stage2_material = [
        load_review_capture(path, schema_root) for path in inputs["stage2_capture_directories"]
    ]
    label_freeze = (
        inputs["scientific_label_freeze"]
        if static_control
        else freeze_scientific_label(
            inputs["adjudication"],
            inputs["stage1_freeze"],
            [review for review, _packet, _manifest in stage2_material],
            [packet for _review, packet, _manifest in stage2_material],
            [manifest for _review, _packet, manifest in stage2_material],
            schema_root,
            frozen_at="2026-07-27T19:05:00Z",
            output=tmp_path / "control-label-freeze.json",
            stage1_reviews=stage1_reviews,
            adjudicated_root_causes=[],
        )
    )
    audit_bundle = _example(project_root, "audit-bundle.example.json")
    detector_result = _example(project_root, "detector-result.evaluation-candidate.example.json")
    detector_result["state"] = "no_issue_detected_within_coverage"
    detector_result.pop("candidate")
    if static_control:
        manifest = inputs["detector_manifest"]
        detector_result.update(
            {
                "detector_id": manifest["detector_id"],
                "detector_version": manifest["detector_version"],
                "detector_manifest_digest": semantic_digest(manifest),
            }
        )
        detector_result["provenance"]["actor"]["actor_id"] = manifest["detector_id"]
        audit_bundle["detector_manifests"] = [manifest]
        audit_bundle["static_qualification_profiles"] = [inputs["static_qualification_profile"]]
        audit_bundle["static_qualification_proofs"] = [inputs["static_qualification_proof"]]
    audit_bundle["detector_results"] = [detector_result]
    detector_id = str(detector_result["detector_id"])

    review_packets: list[dict[str, Any]] = []
    comparison_reviews: list[dict[str, Any]] = []
    for index, provider in enumerate(("Anthropic", "OpenAI"), start=1):
        reviewer = deepcopy(
            _example(project_root, "stage3-comparison-review.example.json")["reviewer_agent"]
        )
        reviewer.update(
            {
                "provider": provider,
                "model_id": f"model:{provider.lower()}:control",
                "model_name": f"Synthetic {provider} control reviewer",
                "execution_context_id": f"context:stage3:control:{provider.lower()}",
            }
        )
        packet = build_stage3_review_packet(
            fixture,
            inputs["adjudication"],
            inputs["stage1_freeze"],
            label_freeze,
            audit_bundle,
            [],
            [],
            detector_id,
            reviewer,
            "Account for the detector abstention against the frozen control label.",
            schema_root,
            created_at=f"2026-07-27T20:2{index}:00Z",
        )
        review = deepcopy(_example(project_root, "stage3-comparison-review.example.json"))
        review.update(
            {
                "comparison_review_id": f"stage3-review:control:{provider.lower()}",
                "case_id": inputs["adjudication"]["case_id"],
                "reviewer_agent": deepcopy(packet["expected_reviewer_agent"]),
                "fixture_ref": deepcopy(packet["fixture"]["fixture_ref"]),
                "adjudication_ref": deepcopy(packet["adjudication"]["adjudication_ref"]),
                "adjudication_digest": packet["adjudication"]["adjudication_digest"],
                "scientific_label_freeze_digest": label_freeze["freeze_digest"],
                "audit_bundle_ref": deepcopy(packet["detector_output"]["audit_bundle_ref"]),
                "audit_bundle_digest": packet["detector_output"]["audit_bundle_digest"],
                "detector_id": detector_id,
                "detector_version": packet["detector_output"]["detector_version"],
                "detector_manifest_digest": packet["detector_output"]["detector_manifest_digest"],
                "root_cause_refs": [],
                "candidate_refs": [],
                "candidate_mappings": [],
                "unmatched_root_cause_refs": [],
                "material_ambiguity_retained": False,
                "all_candidates_accounted_for": True,
                "all_roots_accounted_for": True,
                "comparison_access": deepcopy(packet["comparison_access_required"]),
                "packet_digest": packet["packet_digest"],
                "completed_at": f"2026-07-27T20:3{index}:00Z",
            }
        )
        review_packets.append(packet)
        comparison_reviews.append(review)

    outcome = reconcile_detector_case(
        fixture,
        inputs["adjudication"],
        inputs["stage1_freeze"],
        label_freeze,
        audit_bundle,
        [],
        [],
        detector_id,
        comparison_reviews,
        review_packets,
        schema_root,
        reconciled_at="2026-07-27T21:00:00Z",
        output=tmp_path / "control-outcome.json",
        fixture_proof_inputs=_proof_inputs(inputs),
    )
    assert outcome["qualification_proof_status"] == "complete"
    assert outcome["metric_input_status"] == "complete"
    assert outcome["metric_eligible"] is True
    assert outcome["qualification_proof_family"] == (
        "static_closed_scope" if static_control else "clean_execution"
    )
    assert (outcome["static_qualification_proof_ref"] is not None) is static_control
    assert outcome["detector_result_outcomes"][0]["state"] == ("no_issue_detected_within_coverage")


def test_scope_verified_good_accepts_only_bounded_imported_execution(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _build_control_inputs(project_root, schema_root, tmp_path)
    inputs["fixture_spec"].update(
        {
            "fixture_kind": "scope_verified_good",
            "execution_evidence": "documented_external_execution",
        }
    )
    inputs["environments"][0]["environment_kind"] = "imported_runtime"
    execution = inputs["executions"][0]
    execution.update(
        {
            "execution_kind": "imported",
            "actor": "external_import",
            "identity_strength": "imported_strong",
            "authorization_evidence_status": "imported",
            "limitations": [
                "Imported execution verifies only the declared claim and operation scope."
            ],
        }
    )
    execution["timing"]["state"] = "imported"
    execution["sandbox"] = {
        "project_code_executed": False,
        "authorization_status": "not_required",
        "network_policy": "unknown",
    }
    inputs["sandbox_capabilities"] = []

    fixture = _generate(inputs, tmp_path / "scope-control.json")

    assert fixture["fixture_kind"] == "scope_verified_good"
    assert fixture["execution_evidence"] == "documented_external_execution"
    assert fixture["qualification_proof_status"] == "complete"
    assert fixture["proof_evidence"]["public_inputs"]["sandbox_capabilities"] == []

    unbounded = deepcopy(inputs)
    unbounded["executions"][0]["limitations"] = []
    with pytest.raises(FixtureGenerationError, match="with limitations"):
        _generate(unbounded, tmp_path / "unbounded-scope-control.json")


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda inputs: inputs["executions"][0].update(
                {"execution_kind": "auditor_verification", "actor": "sc_referee_auditor"}
            ),
            "project-workflow|failed validation",
        ),
        (
            lambda inputs: inputs["executions"][0]["exit"].update({"state": "failed", "code": 1}),
            "failed Execution",
        ),
        (
            lambda inputs: inputs["executions"][0]["sandbox"].update({"network_policy": "allowed"}),
            "rootless-OCI control envelope",
        ),
        (
            lambda inputs: inputs["sandbox_capabilities"][0].update(
                {"unsafe_fallback_available": True}
            ),
            "schema validation|unsafe_fallback",
        ),
        (
            lambda inputs: inputs["sandbox_capabilities"][0].update(
                {"backend_kind": "auditor_subprocess"}
            ),
            "failed validation|rootless-OCI",
        ),
        (
            lambda inputs: inputs["fixture_spec"]["scientific_contract_refs"][0].update(
                {"record_id": "contract:missing"}
            ),
            "do not exactly equal",
        ),
        (
            lambda inputs: inputs["fixture_spec"]["declared_scope"]["operation_refs"][0].update(
                {"record_id": "operation:missing"}
            ),
            "does not exactly equal",
        ),
    ],
)
def test_clean_control_rejects_nonqualifying_execution_or_unresolved_scope(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    mutate: Any,
    message: str,
) -> None:
    inputs = _build_control_inputs(project_root, schema_root, tmp_path)
    mutate(inputs)

    with pytest.raises(FixtureGenerationError, match=message):
        _generate(inputs, tmp_path / "rejected-control.json")


@pytest.mark.parametrize("fixture_kind", ["verified_good_fixture", "hard_negative_fixture"])
def test_v014_deliberately_rejects_a_complete_static_control(
    project_root: Path, schema_root: Path, tmp_path: Path, fixture_kind: str
) -> None:
    inputs = _build_control_inputs(project_root, schema_root, tmp_path, fixture_kind=fixture_kind)
    fixture = _generate(inputs, tmp_path / f"{fixture_kind}-execution-backed.json")
    LocalSchemaRegistry(schema_root).validate(fixture)

    fixture["execution_evidence"] = "not_executed"
    fixture["proof_evidence"]["public_inputs"].update(
        {"environments": [], "executions": [], "sandbox_capabilities": []}
    )
    with pytest.raises(RecordValidationError):
        LocalSchemaRegistry(schema_root).validate(fixture)

    inputs["fixture_spec"]["execution_evidence"] = "not_executed"
    inputs["environments"] = []
    inputs["executions"] = []
    inputs["sandbox_capabilities"] = []
    with pytest.raises(FixtureGenerationError, match="Only static control fixture kinds"):
        _generate(inputs, tmp_path / f"{fixture_kind}-static-rejected.json")


def test_hard_negative_requires_both_exact_evidence_classes_and_rejects_mutation(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _build_control_inputs(
        project_root, schema_root, tmp_path, fixture_kind="hard_negative_fixture"
    )
    fixture = _generate(inputs, tmp_path / "hard-negative.json")
    proof = fixture["proof_evidence"]["hard_negative_evidence"]
    assert proof["suspicious_pattern"]
    assert proof["decisive_innocent_explanation"]
    assert fixture["proof_obligations"]["hard_negative_pattern_documented"] is True

    missing = deepcopy(inputs)
    missing["fixture_spec"]["hard_negative_evidence"]["suspicious_pattern"] = []
    with pytest.raises(FixtureGenerationError, match="requires both"):
        _generate(missing, tmp_path / "missing-hard-negative.json")

    drifted = deepcopy(inputs)
    drifted["fixture_spec"]["hard_negative_evidence"]["suspicious_pattern"][0]["source_refs"][0][
        "content_digest"
    ] = "sha256:" + "0" * 64
    with pytest.raises(FixtureGenerationError, match="source evidence failed"):
        _generate(drifted, tmp_path / "drifted-hard-negative.json")
