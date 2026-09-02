"""Deterministic adapter-level replay harness for the open MT corpus."""

from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any

from sc_referee.controller import run_audit
from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.method_contract_run import (
    preflight_frozen_scientific_requirement,
    run_method_contract,
)
from sc_referee.scientific_checks import code_csv_multiple_testing_adapter_v1_1 as adapter_v1_1
from sc_referee.scientific_checks import code_csv_multiple_testing_adapter_v2 as adapter_v2
from sc_referee.scientific_checks import code_csv_multiple_testing_adapter_v2_1 as adapter_v2_1
from sc_referee.scientific_checks import code_csv_multiple_testing_adapter_v2_2 as adapter_v2_2
from sc_referee.scientific_checks import code_csv_multiple_testing_adapter_v2_3 as adapter_v2_3
from sc_referee.scientific_checks import code_csv_multiple_testing_adapter_v3 as adapter_v3
from sc_referee.scientific_checks import code_csv_multiple_testing_adapter_v3_1 as adapter_v3_1
from sc_referee.scientific_checks import code_csv_multiple_testing_adapter_v3_2 as adapter_v3_2
from sc_referee.scientific_checks import code_csv_multiple_testing_adapter_v3_3 as adapter_v3_3
from sc_referee.scientific_checks import code_csv_multiple_testing_adapter_v3_4 as adapter_v3_4
from sc_referee.scientific_checks.core import CanonicalOperand
from sc_referee.scientific_checks.integration import build_frozen_inspection_context
from sc_referee.scientific_checks.profiles import scientific_check_release_registry

CHECK_ID = "check:authorized-complete-family-correction-over-code-test-battery"


def _authority(case: Path) -> tuple[str, tuple[str, ...]]:
    with (case / "data.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 5 or len({len(row) for row in rows}) != 1:
        raise ValueError(f"open-corpus CSV shape changed: {case}")
    header = tuple(rows[0])
    group_index = 1
    if len(Counter(row[group_index] for row in rows[1:])) != 2:
        raise ValueError(f"open-corpus group column is not binary: {case}")
    outcomes = tuple(
        column
        for index, column in enumerate(header)
        if index not in {0, group_index} and all(_finite_decimal(row[index]) for row in rows[1:])
    )
    if len(outcomes) < 3:
        raise ValueError(f"open-corpus outcome family is too small: {case}")
    return header[group_index], outcomes


def _finite_decimal(value: str) -> bool:
    try:
        number = float(value)
    except ValueError:
        return False
    return number == number and number not in {float("inf"), float("-inf")}


def _profile(group_column: str, outcomes: tuple[str, ...]) -> dict[str, Any]:
    return {
        "profile_id": "scientific_check_requirement_v1",
        "profile_version": "1.2.0",
        "check_id": CHECK_ID,
        "candidate_id": "complete-correction-over-authorized-outcome-family",
        "semantic_role_authority": {
            "authorized_test_family": {
                "material_input_path": "data.csv",
                "group_contrast_column": group_column,
                "outcome_columns": list(outcomes),
                "family_member_rule": "one-two-group-test-per-named-outcome-column",
                "correction_scope": "complete-authorized-family",
            }
        },
    }


def _classification(observation: Any) -> list[str]:
    if observation.abstention_reason is not None:
        return ["abstain", observation.abstention_reason]
    assert observation.multiple_testing_evidence is not None
    classification = observation.multiple_testing_evidence.correction_classification
    return ["covered" if classification == "complete" else "candidate", classification]


def replay_open_corpus(
    *, corpus_root: Path, scratch_root: Path, schema_root: Path
) -> dict[str, dict[str, Any]]:
    labels_path = corpus_root / "specs" / "labels.json"
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    if not isinstance(labels, dict) or len(labels) != 50:
        raise ValueError("open-corpus labels must contain exactly 50 cases")
    registry = scientific_check_release_registry()
    module = next(
        item
        for item in registry.modules_for_lane("development")
        if item.manifest.check_id == CHECK_ID
    )
    active_adapter = module.adapters[0]
    if not isinstance(active_adapter, adapter_v3_4.CodeCsvMultipleTestingAdapter):
        raise TypeError("the active development adapter is not MT 3.4")
    historical_v1_1_manifest = replace(
        module.adapter_manifests[0],
        adapter_version=adapter_v1_1.MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
        implementation_digest=adapter_v1_1.CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=adapter_v1_1.code_csv_multiple_testing_grammar_digest(),
    )
    historical_adapter = adapter_v1_1.CodeCsvMultipleTestingAdapter(
        check_manifest=module.manifest,
        adapter_manifest=historical_v1_1_manifest,
        complete_operand=CanonicalOperand.scalar(adapter_v1_1.COMPLETE_FAMILY_CORRECTION_OPERAND),
        none_operand=CanonicalOperand.scalar(adapter_v1_1.NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND),
        strict_subset_operand=CanonicalOperand.scalar(
            adapter_v1_1.STRICT_SUBSET_FAMILY_CORRECTION_OPERAND
        ),
        role_bindings=adapter_v1_1.MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    )
    historical_v2_manifest = replace(
        module.adapter_manifests[0],
        adapter_version=adapter_v2.MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
        implementation_digest=adapter_v2.CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=adapter_v2.code_csv_multiple_testing_grammar_digest(),
    )
    historical_v2_adapter = adapter_v2.CodeCsvMultipleTestingAdapter(
        check_manifest=module.manifest,
        adapter_manifest=historical_v2_manifest,
        complete_operand=CanonicalOperand.scalar(adapter_v2.COMPLETE_FAMILY_CORRECTION_OPERAND),
        none_operand=CanonicalOperand.scalar(adapter_v2.NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND),
        strict_subset_operand=CanonicalOperand.scalar(
            adapter_v2.STRICT_SUBSET_FAMILY_CORRECTION_OPERAND
        ),
        role_bindings=adapter_v2.MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    )
    historical_v2_1_manifest = replace(
        module.adapter_manifests[0],
        adapter_version=adapter_v2_1.MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
        implementation_digest=adapter_v2_1.CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=adapter_v2_1.code_csv_multiple_testing_grammar_digest(),
    )
    historical_v2_1_adapter = adapter_v2_1.CodeCsvMultipleTestingAdapter(
        check_manifest=module.manifest,
        adapter_manifest=historical_v2_1_manifest,
        complete_operand=CanonicalOperand.scalar(adapter_v2_1.COMPLETE_FAMILY_CORRECTION_OPERAND),
        none_operand=CanonicalOperand.scalar(adapter_v2_1.NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND),
        strict_subset_operand=CanonicalOperand.scalar(
            adapter_v2_1.STRICT_SUBSET_FAMILY_CORRECTION_OPERAND
        ),
        role_bindings=adapter_v2_1.MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    )
    historical_v2_2_manifest = replace(
        module.adapter_manifests[0],
        adapter_version=adapter_v2_2.MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
        implementation_digest=adapter_v2_2.CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=adapter_v2_2.code_csv_multiple_testing_grammar_digest(),
    )
    historical_v2_2_adapter = adapter_v2_2.CodeCsvMultipleTestingAdapter(
        check_manifest=module.manifest,
        adapter_manifest=historical_v2_2_manifest,
        complete_operand=CanonicalOperand.scalar(adapter_v2_2.COMPLETE_FAMILY_CORRECTION_OPERAND),
        none_operand=CanonicalOperand.scalar(adapter_v2_2.NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND),
        strict_subset_operand=CanonicalOperand.scalar(
            adapter_v2_2.STRICT_SUBSET_FAMILY_CORRECTION_OPERAND
        ),
        role_bindings=adapter_v2_2.MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    )
    historical_v2_3_manifest = replace(
        module.adapter_manifests[0],
        adapter_version=adapter_v2_3.MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
        implementation_digest=adapter_v2_3.CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=adapter_v2_3.code_csv_multiple_testing_grammar_digest(),
    )
    historical_v2_3_adapter = adapter_v2_3.CodeCsvMultipleTestingAdapter(
        check_manifest=module.manifest,
        adapter_manifest=historical_v2_3_manifest,
        complete_operand=CanonicalOperand.scalar(adapter_v2_3.COMPLETE_FAMILY_CORRECTION_OPERAND),
        none_operand=CanonicalOperand.scalar(adapter_v2_3.NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND),
        strict_subset_operand=CanonicalOperand.scalar(
            adapter_v2_3.STRICT_SUBSET_FAMILY_CORRECTION_OPERAND
        ),
        role_bindings=adapter_v2_3.MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    )
    historical_v3_manifest = replace(
        module.adapter_manifests[0],
        adapter_version=adapter_v3.MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
        implementation_digest=adapter_v3.CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=adapter_v3.code_csv_multiple_testing_grammar_digest(),
    )
    historical_v3_adapter = adapter_v3.CodeCsvMultipleTestingAdapter(
        check_manifest=module.manifest,
        adapter_manifest=historical_v3_manifest,
        complete_operand=CanonicalOperand.scalar(adapter_v3.COMPLETE_FAMILY_CORRECTION_OPERAND),
        none_operand=CanonicalOperand.scalar(adapter_v3.NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND),
        strict_subset_operand=CanonicalOperand.scalar(
            adapter_v3.STRICT_SUBSET_FAMILY_CORRECTION_OPERAND
        ),
        role_bindings=adapter_v3.MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    )
    historical_v3_1_manifest = replace(
        module.adapter_manifests[0],
        adapter_version=adapter_v3_1.MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
        implementation_digest=adapter_v3_1.CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=adapter_v3_1.code_csv_multiple_testing_grammar_digest(),
    )
    historical_v3_1_adapter = adapter_v3_1.CodeCsvMultipleTestingAdapter(
        check_manifest=module.manifest,
        adapter_manifest=historical_v3_1_manifest,
        complete_operand=CanonicalOperand.scalar(adapter_v3_1.COMPLETE_FAMILY_CORRECTION_OPERAND),
        none_operand=CanonicalOperand.scalar(adapter_v3_1.NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND),
        strict_subset_operand=CanonicalOperand.scalar(
            adapter_v3_1.STRICT_SUBSET_FAMILY_CORRECTION_OPERAND
        ),
        role_bindings=adapter_v3_1.MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    )
    historical_v3_2_manifest = replace(
        module.adapter_manifests[0],
        adapter_version=adapter_v3_2.MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
        implementation_digest=adapter_v3_2.CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=adapter_v3_2.code_csv_multiple_testing_grammar_digest(),
    )
    historical_v3_2_adapter = adapter_v3_2.CodeCsvMultipleTestingAdapter(
        check_manifest=module.manifest,
        adapter_manifest=historical_v3_2_manifest,
        complete_operand=CanonicalOperand.scalar(adapter_v3_2.COMPLETE_FAMILY_CORRECTION_OPERAND),
        none_operand=CanonicalOperand.scalar(adapter_v3_2.NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND),
        strict_subset_operand=CanonicalOperand.scalar(
            adapter_v3_2.STRICT_SUBSET_FAMILY_CORRECTION_OPERAND
        ),
        role_bindings=adapter_v3_2.MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    )
    historical_v3_3_manifest = replace(
        module.adapter_manifests[0],
        adapter_version=adapter_v3_3.MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
        implementation_digest=adapter_v3_3.CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=adapter_v3_3.code_csv_multiple_testing_grammar_digest(),
    )
    historical_v3_3_adapter = adapter_v3_3.CodeCsvMultipleTestingAdapter(
        check_manifest=module.manifest,
        adapter_manifest=historical_v3_3_manifest,
        complete_operand=CanonicalOperand.scalar(adapter_v3_3.COMPLETE_FAMILY_CORRECTION_OPERAND),
        none_operand=CanonicalOperand.scalar(adapter_v3_3.NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND),
        strict_subset_operand=CanonicalOperand.scalar(
            adapter_v3_3.STRICT_SUBSET_FAMILY_CORRECTION_OPERAND
        ),
        role_bindings=adapter_v3_3.MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    )
    results: dict[str, dict[str, list[str]]] = {
        "1.1.0": {},
        "2.0.0": {},
        "2.1.0": {},
        "2.2.0": {},
        "2.3.0": {},
        "3.0.0": {},
        "3.1.0": {},
        "3.2.0": {},
        "3.3.0": {},
        "3.4.0": {},
    }
    source_map: dict[str, str] = {}
    for spec, metadata in sorted(labels.items()):
        if metadata.get("label") not in {"correct", "misstep"}:
            raise ValueError(f"open-corpus label is invalid: {spec}")
        source_case = corpus_root / "cases" / spec
        source_map[f"cases/{spec}/analysis.py"] = sha256_digest(
            (source_case / "analysis.py").read_bytes()
        ).removeprefix("sha256:")
        case_root = scratch_root / spec
        project = case_root / "project"
        shutil.copytree(source_case, project)
        (project / "task.txt").write_bytes((corpus_root / "specs" / f"{spec}.txt").read_bytes())
        group_column, outcomes = _authority(source_case)
        contract = case_root / "contract"
        run_method_contract(
            project,
            "task.txt",
            contract,
            schema_root,
            profile=_profile(group_column, outcomes),
            actor_id="human:multitest-open-corpus",
            created_at="2026-08-25T00:00:00Z",
        )
        audit = case_root / "audit"
        run_audit(
            project,
            audit,
            schema_root,
            material_inputs=("data.csv",),
            method_contract_lock=contract / "semantic.lock.json",
            scientific_check_lane="development",
        )
        lock = json.loads((audit / "semantic.lock.json").read_text(encoding="utf-8"))
        context = build_frozen_inspection_context(
            snapshot_root=audit / "observed" / "snapshot" / "materialized",
            snapshot_digest=lock["snapshot_digest"],
            file_records=lock["file_records"],
            asset_identities=lock["asset_identities"],
            parser_results=lock["parser_results"],
            operations=lock["operations"],
            artifacts=lock["artifacts"],
            publication_surface=lock["publication_surfaces"][0],
            repository_snapshot=lock["repository_snapshot"],
            executions=lock["executions"],
            environments=lock["environments"],
            scope_selections=lock["scope_selections"],
            selection_evidence_records=lock["material_questions"],
        )
        if context is None:
            raise ValueError(f"open-corpus inspection context is unavailable: {spec}")
        context = preflight_frozen_scientific_requirement(
            lock_path=contract / "semantic.lock.json",
            schema_root=schema_root,
            context=context,
            file_records=lock["file_records"],
            asset_identities=lock["asset_identities"],
            scientific_check_registry=registry,
            scientific_check_lane="development",
        )
        for version, adapter in (
            ("1.1.0", historical_adapter),
            ("2.0.0", historical_v2_adapter),
            ("2.1.0", historical_v2_1_adapter),
            ("2.2.0", historical_v2_2_adapter),
            ("2.3.0", historical_v2_3_adapter),
            ("3.0.0", historical_v3_adapter),
            ("3.1.0", historical_v3_1_adapter),
            ("3.2.0", historical_v3_2_adapter),
            ("3.3.0", historical_v3_3_adapter),
            ("3.4.0", active_adapter),
        ):
            first = adapter.inspect(context)
            second = adapter.inspect(context)
            if canonical_json(first.to_dict()) != canonical_json(second.to_dict()):
                raise ValueError(f"open-corpus adapter replay drift: {version} {spec}")
            results[version][spec] = _classification(first)
    source_payload = canonical_json(dict(sorted(source_map.items()))) + "\n"
    if sha256_digest(source_payload) != (
        "sha256:7888b72a6ac1ec70830d4041517a977b8ea8ff6c4294a7d13a734ab9af377a2e"
    ):
        raise ValueError("open-corpus source-set digest changed")
    output: dict[str, dict[str, Any]] = {}
    for version in (
        "1.1.0",
        "2.0.0",
        "2.1.0",
        "2.2.0",
        "2.3.0",
        "3.0.0",
        "3.1.0",
        "3.2.0",
        "3.3.0",
        "3.4.0",
    ):
        values = results[version]
        output[version] = {
            "profile": "multitest-open-corpus-adapter-replay-v1",
            "adapter_version": version,
            "label_digest": sha256_digest(labels_path.read_bytes()),
            "source_set_digest": sha256_digest(source_payload),
            "correct_candidates": sum(
                values[spec][0] == "candidate"
                for spec, metadata in labels.items()
                if metadata["label"] == "correct"
            ),
            "misstep_candidates": sum(
                values[spec][0] == "candidate"
                for spec, metadata in labels.items()
                if metadata["label"] == "misstep"
            ),
            "results": values,
        }
    return output
