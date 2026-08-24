from __future__ import annotations

import ast
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation import analysis_method_qualification as qualification_module
from sc_referee_evaluation.analysis_method_qualification import (
    AnalysisMethodQualificationError,
    freeze_bounded_analysis_method_profile,
    freeze_protocol_artifact,
    revalidate_analysis_method_proof,
    verify_bounded_analysis_method_case,
)
from sc_referee_evaluation.cli import main as evaluation_main

from sc_referee.controller import run_audit
from sc_referee.interaction import (
    create_structured_answer,
    lock_semantics,
    record_answer,
    resume_semantics,
    submit_proposal,
    work_packet,
    work_queue,
)
from sc_referee.records.observed import build_file_records
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.snapshot.repository import capture_repository
from sc_referee.version import SCHEMA_VERSION

DIRECT = "use_supplied_founder_alleles_directly_in_hmm_emission"
REPAIRED = "repair_ril_founder_orientation_before_hmm_emission"
CHECK_ID = "check:founder-orientation-before-hmm-emission"

# The frozen v0.1 verifier under test carries its own closed sentence grammar,
# so the qualification-stage bytes below stay exactly as it qualified them.
# The live audit that supplies the human question now recognizes the operand
# from arithmetic instead (ADR-0069 check v2.0.0), so the audit-stage report
# states the accounting: 372 of 480 markers agree, and the emission rate is
# either 372 / 480 = 0.775 or its complement 108 / 480 = 0.225.
_AUDIT_ACCOUNTING = (
    "The parental marker panel and the progeny calls were compared marker by marker: "
    "372 of the 480 markers agree.\n\n"
    "The emission model used a per-marker agreement rate of {rate}.\n"
)
AUDIT_DIRECT_REPORT = _AUDIT_ACCOUNTING.format(rate="0.775")
AUDIT_COMPLEMENT_REPORT = _AUDIT_ACCOUNTING.format(rate="0.225")


@pytest.fixture(autouse=True)
def _pin_historical_qualification_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the superseded v0.1 verifier on the schema it actually qualified."""

    monkeypatch.setattr(qualification_module, "SCHEMA_VERSION", "0.16.0")


@pytest.fixture
def schema_root(project_root: Path) -> Path:
    return project_root / "reference" / "schemas-v0.16.0"


def _collection(project_root: Path, name: str) -> list[dict[str, Any]]:
    path = project_root / "src" / "sc_referee" / "resources" / "capability-manifests-v1" / name
    return json.loads(path.read_text(encoding="utf-8"))["records"]


def _one(records: list[dict[str, Any]], field: str, identity: str) -> dict[str, Any]:
    return deepcopy(next(record for record in records if record[field] == identity))


def _proposal(packet: dict[str, Any], operand: str) -> dict[str, Any]:
    work_item = packet["work_item"]
    bounded = work_item["packet"]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "semantic_assertion",
        "assertion_id": "assertion:model-method-proposal",
        "audit_run_id": packet["audit_run_id"],
        "subject_ref": deepcopy(work_item["target_refs"][0]),
        "predicate": "proposed_scale_and_orientation",
        "object": operand,
        "semantic_role": "inferred",
        "assertion_class": "implicit_scientific_inference",
        "epistemic_status": "proposed",
        "authority_scope": "none",
        "independently_checkable": False,
        "finding_eligibility": "ineligible",
        "verification": {"status": "not_checked", "method": "not_applicable"},
        "certainty": {"level": "low", "basis": "The scientist must decide."},
        "rationale": "A bounded proposal carries no scientific authority.",
        "source_refs": [deepcopy(bounded["source_refs"][0])],
        "provenance": {
            "actor": {"actor_kind": "model", "actor_id": "model:test"},
            "method": "bounded_semantic_proposal",
            "created_at": "2026-07-31T17:05:00Z",
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


def _source(operand: str, *, second_writer: bool = False, unsupported: bool = False) -> str:
    founder = "sample.founder_alleles[0]"
    repair = ""
    if operand == REPAIRED:
        repair = "    repaired = orient_ril_founder_alleles(sample.founder_alleles)\n"
        founder = "repaired[0]"
    writer = (
        "    (ROOT / report_name).write_text(REPORT)\n"
        if unsupported
        else "    (ROOT / 'report.md').write_text(REPORT)\n"
    )
    extra = "\n(ROOT / 'report.md').write_text(REPORT)\n" if second_writer else ""
    return (
        "from pathlib import Path\n"
        "ROOT = Path(__file__).resolve().parent\n"
        "REPORT = 'The founder-origin HMM was fitted using the supplied founder alleles.\\n'\n"
        "def emission_matrix(observed, founder_state, error):\n"
        "    return observed == founder_state\n"
        "def fit(sample, observed):\n"
        f"{repair}"
        f"    return emission_matrix(observed, {founder}, 0.01)\n"
        "def main():\n"
        f"{writer}"
        "if __name__ == '__main__':\n"
        "    main()\n"
        f"{extra}"
    )


def _audit_source(operand: str, **options: bool) -> str:
    """``_source`` plus an emission the live founder dataflow trace can read.

    From ADR-0069 check v2.0.1 the report plane never resolves alone, so the
    audit stage that supplies the human question needs a source whose
    orientation the bounded trace resolves. These bytes belong to the audit
    stage only; the repository is rewritten to the exact ``_source`` bytes the
    frozen v0.1 verifier qualified before the qualification snapshot.

    From check v2.1.0 the emission sits at module level and its value is
    written out directly. The earlier shape computed it inside
    ``emission_likelihood()``, a closure over the module-level ``rows``, which
    the default-deny trust model no longer supports: which panel such a name
    holds when the call runs is decided by the module's binding order at run
    time. The comparison and the panel it reads are unchanged.
    """

    panel = "rows"
    stage = ""
    if operand == REPAIRED:
        stage = "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        panel = "panel"
    # From check v2.1.2 an unrecognized comparison over two different names
    # abstains (the helper-emission belt), and an unrecognized call anywhere
    # abstains. The audit-stage copy therefore replaces the decorative
    # comparison and the undefined repair helper with whitelisted
    # equivalents; the repository itself is still rewritten to the exact
    # ``_source`` bytes before the qualification snapshot.
    audit_base = (
        _source(operand, **options)
        .replace(
            "    return observed == founder_state\n",
            "    return 1.0 - abs(observed - founder_state) * error\n",
        )
        .replace(
            "    repaired = orient_ril_founder_alleles(sample.founder_alleles)\n",
            "    repaired = [1 - value for value in sample]\n",
        )
    )
    return (
        "import csv\n"
        "import math\n"
        + audit_base
        + "rows = list(csv.DictReader((ROOT / 'markers.csv').open()))\n"
        + stage
        + "LIKELIHOOD = math.prod(\n"
        + f"    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in {panel}\n"
        + ")\n"
        + "(ROOT / 'likelihood.txt').write_text(str(LIKELIHOOD))\n"
    )


def _inputs(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    *,
    report_operand: str = DIRECT,
    source_operand: str = DIRECT,
    requirement_operand: str = REPAIRED,
    second_writer: bool = False,
    unsupported_writer: bool = False,
    qualification_report_text: str | None = None,
    qualification_source_text: str | None = None,
    qualification_extra_bytes: tuple[str, bytes] | None = None,
) -> dict[str, Any]:
    active_schema_root = project_root / "reference" / "schemas-v0.21.0"
    repository = tmp_path / "repository"
    repository.mkdir(parents=True)
    requested_report = (
        "The founder-origin HMM was fitted using the supplied founder alleles.\n"
        if report_operand == DIRECT
        else "Founder alleles were orientation-repaired before the HMM emission.\n"
    )
    audit_report = AUDIT_DIRECT_REPORT if source_operand == DIRECT else AUDIT_COMPLEMENT_REPORT
    (repository / "report.md").write_text(audit_report, encoding="utf-8")
    (repository / "analysis.py").write_text(
        _audit_source(
            source_operand,
            second_writer=second_writer,
            unsupported=unsupported_writer,
        ),
        encoding="utf-8",
    )
    source_audit = tmp_path / "source-audit"
    initial = run_audit(repository, source_audit, active_schema_root, report="report.md")
    question = next(
        item
        for item in initial["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id") == CHECK_ID
    )
    session = tmp_path / "session"
    resume_semantics(
        source_audit,
        repository,
        session,
        active_schema_root,
        created_at="2026-07-31T17:04:00Z",
    )
    item = work_queue(session, active_schema_root)["work_items"][0]
    packet = work_packet(session, str(item["work_item_id"]), active_schema_root)
    submit_proposal(
        session,
        str(item["work_item_id"]),
        _proposal(packet, source_operand),
        active_schema_root,
        submitted_at="2026-07-31T17:05:00Z",
    )
    answer = create_structured_answer(
        session,
        str(question["question_id"]),
        {"scale_and_orientation": requirement_operand},
        "scientist:test",
        active_schema_root,
        answered_at="2026-07-31T17:06:00Z",
    )
    record_answer(session, answer, active_schema_root)
    bundle = lock_semantics(session, active_schema_root, locked_at="2026-07-31T17:07:00Z")

    # A hard-negative proof may expose disagreement that the production question scheduler
    # suppresses. Preserve the already-frozen human authority while presenting those exact
    # independently assigned case bytes to the qualification verifier. The audit-stage
    # emission workflow is not part of those bytes.
    (repository / "analysis.py").write_text(
        _source(
            source_operand,
            second_writer=second_writer,
            unsupported=unsupported_writer,
        ),
        encoding="utf-8",
    )
    (repository / "report.md").write_text(
        qualification_report_text if qualification_report_text is not None else requested_report,
        encoding="utf-8",
    )
    if qualification_source_text is not None:
        (repository / "analysis.py").write_text(qualification_source_text, encoding="utf-8")
    if qualification_extra_bytes is not None:
        extra_path, payload = qualification_extra_bytes
        (repository / extra_path).write_bytes(payload)

    captured = capture_repository(
        repository,
        tmp_path / "qualification-snapshot",
        "audit:method-qualification",
        captured_at="2026-07-31T17:08:00Z",
    )
    files = build_file_records(
        captured.file_records,
        captured.asset_identity_records,
        str(captured.snapshot_record["snapshot_id"]),
        "2026-07-31T17:08:00Z",
    )
    frozen = (
        project_root
        / "evaluation"
        / "qualification"
        / "bounded-analysis-method-conflict-v0.1.0-readiness-pilot"
    )
    detector = json.loads((frozen / "detector-manifest.json").read_text(encoding="utf-8"))
    selected_parsers = [
        json.loads((frozen / "parser-manifest.markdown.json").read_text(encoding="utf-8")),
        json.loads((frozen / "parser-manifest.python.json").read_text(encoding="utf-8")),
    ]
    selected_profiles = [
        json.loads((frozen / "semantic-profile-manifest.json").read_text(encoding="utf-8"))
    ]
    selected_versions = [json.loads((frozen / "version-manifest.json").read_text(encoding="utf-8"))]
    selection = freeze_protocol_artifact(
        "corpus_selection_protocol",
        "selection-protocol:bounded-analysis-method-v1",
        "2026-07-31T17:09:00Z",
        {"selection_rule": "opaque_assignment_before_case_inspection"},
    )
    profile = freeze_bounded_analysis_method_profile(
        detector,
        selected_parsers,
        selected_profiles,
        selected_versions,
        selection,
        frozen_at="2026-07-31T17:10:00Z",
    )
    assignment = freeze_protocol_artifact(
        "opaque_case_assignment",
        "case-assignment:bounded-analysis-method-1",
        "2026-07-31T17:11:00Z",
        {
            "selection_protocol_artifact_id": selection["artifact_id"],
            "selection_protocol_artifact_digest": selection["content_digest"],
            "selected_report_path": "report.md",
        },
    )
    label = freeze_protocol_artifact(
        "scientific_label_freeze",
        "label-freeze:bounded-analysis-method-1",
        "2026-07-31T17:12:00Z",
        {"case_id": "case:method-1", "label_status": "verified_good_eligible"},
    )
    return {
        "workspace": captured.materialized_root,
        "snapshot": captured.snapshot_record,
        "files": files,
        "identities": captured.asset_identity_records,
        "questions": bundle["material_questions"],
        "answers": bundle["answers"],
        "contracts": bundle["scientific_contracts"],
        "assertions": bundle["semantic_assertions"],
        "detector": detector,
        "parsers": selected_parsers,
        "profiles": selected_profiles,
        "versions": selected_versions,
        "profile": profile,
        "selection": selection,
        "assignment": assignment,
        "label": label,
    }


def _verify(inputs: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    values = {**inputs, **overrides}
    return verify_bounded_analysis_method_case(
        values["workspace"],
        values["profile"],
        values["assignment"],
        values["label"],
        values["snapshot"],
        values["files"],
        values["identities"],
        values["questions"],
        values["answers"],
        values["contracts"],
        values["assertions"],
        detector_manifest=values["detector"],
        parser_manifests=values["parsers"],
        semantic_profile_manifests=values["profiles"],
        version_manifests=values["versions"],
        proof_frozen_at=values.get("proof_frozen_at", "2026-07-31T17:13:00Z"),
    )


def test_complete_conflict_proof_rederives_bytes_and_human_requirement(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(project_root, schema_root, tmp_path)
    proof = _verify(inputs)

    assert proof["proof_status"] == "complete", proof["limitations"]
    assert proof["derived_facts"]["report_operand"] == DIRECT
    assert proof["derived_facts"]["source_operand"] == DIRECT
    assert proof["derived_facts"]["requirement_operand"] == REPAIRED
    assert not (inputs["workspace"] / "PROJECT_CODE_EXECUTED").exists()
    LocalSchemaRegistry(schema_root).validate(inputs["profile"])
    LocalSchemaRegistry(schema_root).validate(proof)
    assert (
        revalidate_analysis_method_proof(
            proof,
            inputs["workspace"],
            inputs["profile"],
            inputs["assignment"],
            inputs["label"],
            inputs["snapshot"],
            inputs["files"],
            inputs["identities"],
            inputs["questions"],
            inputs["answers"],
            inputs["contracts"],
            inputs["assertions"],
            inputs["detector"],
            inputs["parsers"],
            inputs["profiles"],
            inputs["versions"],
        )
        == proof
    )


def test_report_source_disagreement_remains_complete_and_visible(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(
        project_root,
        schema_root,
        tmp_path,
        report_operand=REPAIRED,
        source_operand=DIRECT,
    )
    proof = _verify(inputs)
    relation = next(
        item
        for item in proof["applicability_results"]
        if item["check_id"] == "observed_plane_agreement"
    )
    assert proof["proof_status"] == "complete"
    assert relation["outcome"] == "conflict_present"


@pytest.mark.parametrize("option", ["second_writer", "unsupported_writer"])
def test_competing_or_dynamic_selected_report_writer_fails_closed(
    project_root: Path, schema_root: Path, tmp_path: Path, option: str
) -> None:
    inputs = _inputs(project_root, schema_root, tmp_path, **{option: True})
    proof = _verify(inputs)
    assert proof["proof_status"] == "unavailable"
    check = next(
        item
        for item in proof["applicability_results"]
        if item["check_id"] == "unique_selected_output_writer"
    )
    assert check["completion_status"] == "unavailable"


def test_nonhuman_or_tampered_answer_fails_closed(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(project_root, schema_root, tmp_path)
    answers = deepcopy(inputs["answers"])
    answers[0]["respondent"]["actor_kind"] = "model"
    proof = _verify(inputs, answers=answers)
    assert proof["proof_status"] == "unavailable"
    assert (
        next(
            item
            for item in proof["applicability_results"]
            if item["check_id"] == "answer_authority_complete"
        )["completion_status"]
        == "unavailable"
    )


@pytest.mark.parametrize(
    ("report_text", "source_text", "failed_check"),
    [
        (
            "A descriptive report with no founder-orientation declaration.\n",
            None,
            "report_operand_unique",
        ),
        (
            None,
            (
                "from pathlib import Path\n"
                "ROOT = Path(__file__).resolve().parent\n"
                "def main():\n"
                "    (ROOT / 'report.md').write_text('descriptive')\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            "source_operand_unique",
        ),
        (
            None,
            (
                "from pathlib import Path\n"
                "ROOT = Path(__file__).resolve().parent\n"
                "def first(obs, state):\n"
                "    return obs == state\n"
                "def second(obs, state):\n"
                "    return obs == state\n"
                "def fit(sample, obs):\n"
                "    repaired = orient_ril_founder_alleles(sample.founder_alleles)\n"
                "    return first(obs, sample.founder_alleles[0]), second(obs, repaired[0])\n"
                "def main():\n"
                "    (ROOT / 'report.md').write_text('descriptive')\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            "source_operand_unique",
        ),
        (
            None,
            (
                "from pathlib import Path\n"
                "ROOT = Path(__file__).resolve().parent\n"
                "def emission(obs, state):\n"
                "    return obs == state\n"
                "def fit(sample, obs, choose):\n"
                "    return emission(obs, sample.founder_alleles[0] if choose else obs)\n"
                "def main():\n"
                "    (ROOT / 'report.md').write_text('descriptive')\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            "source_operand_unique",
        ),
        (
            (
                "The founder-origin HMM was fitted using the supplied founder alleles.\n"
                "Founder alleles were orientation-repaired before the HMM emission.\n"
            ),
            None,
            "report_operand_unique",
        ),
    ],
)
def test_report_only_source_only_competing_and_unsupported_cases_fail_closed(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    report_text: str | None,
    source_text: str | None,
    failed_check: str,
) -> None:
    inputs = _inputs(
        project_root,
        schema_root,
        tmp_path,
        qualification_report_text=report_text,
        qualification_source_text=source_text,
    )
    proof = _verify(inputs)
    assert proof["proof_status"] == "unavailable"
    check = next(
        item for item in proof["applicability_results"] if item["check_id"] == failed_check
    )
    assert check["completion_status"] == "unavailable"


@pytest.mark.parametrize("authority_kind", ["question", "contract", "assertion"])
def test_question_contract_and_assertion_authority_drift_fail_closed(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    authority_kind: str,
) -> None:
    inputs = _inputs(project_root, schema_root, tmp_path)
    overrides: dict[str, Any] = {}
    if authority_kind == "question":
        records = deepcopy(inputs["questions"])
        target = next(
            item
            for item in records
            if item.get("extensions", {}).get("x-scientific-check-id") == CHECK_ID
        )
        target["extensions"]["x-posthoc-comparison-forms"] = {
            "scale_and_orientation": "set_relation"
        }
        overrides["questions"] = records
    elif authority_kind == "contract":
        records = deepcopy(inputs["contracts"])
        target = next(item for item in records if item.get("scope", {}).get("level") == "analysis")
        target["dimensions"]["scale_and_orientation"]["state"] = "unknown"
        overrides["contracts"] = records
    else:
        records = deepcopy(inputs["assertions"])
        target = next(
            item
            for item in records
            if item.get("predicate") == "verified_intended_scale_and_orientation"
        )
        target["epistemic_status"] = "proposed"
        overrides["assertions"] = records
    proof = _verify(inputs, **overrides)
    assert proof["proof_status"] == "unavailable"
    assert (
        next(
            item
            for item in proof["applicability_results"]
            if item["check_id"] == "answer_authority_complete"
        )["completion_status"]
        == "unavailable"
    )


@pytest.mark.parametrize(
    "check_id",
    [
        "alternate_or_superseding_intent",
        "governing_protocol_amendment",
        "approved_method_deviation",
        "conditional_applicability",
        "sensitivity_or_unsupported_qualifier",
    ],
)
def test_each_counterevidence_class_is_recorded_without_hiding_the_proof(
    project_root: Path, schema_root: Path, tmp_path: Path, check_id: str
) -> None:
    inputs = _inputs(project_root, schema_root, tmp_path)
    assertions = deepcopy(inputs["assertions"])
    requirement = next(
        item
        for item in assertions
        if item.get("predicate") == "verified_intended_scale_and_orientation"
    )
    if check_id == "sensitivity_or_unsupported_qualifier":
        reported = next(item for item in assertions if item.get("semantic_role") == "reported")
        reported["extensions"]["x-sensitivity-only"] = True
    else:
        signal = deepcopy(requirement)
        signal["assertion_id"] = f"assertion:{check_id}"
        if check_id == "alternate_or_superseding_intent":
            signal["object"] = DIRECT
        elif check_id == "governing_protocol_amendment":
            signal["predicate"] = "governing_protocol_amendment"
            signal["object"] = "present"
        elif check_id == "approved_method_deviation":
            signal["predicate"] = "approved_method_deviation"
            signal["object"] = "present"
        else:
            signal["predicate"] = "method_obligation_applicability"
            signal["object"] = "conditional"
        assertions.append(signal)

    proof = _verify(inputs, assertions=assertions)
    check = next(item for item in proof["counterevidence_results"] if item["check_id"] == check_id)
    assert proof["proof_status"] == "complete"
    assert check["outcome"] == "counterevidence_present"


def test_byte_drift_and_chronology_are_rejected(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(project_root, schema_root, tmp_path)
    proof = _verify(inputs)
    (inputs["workspace"] / "report.md").write_text("changed\n", encoding="utf-8")
    with pytest.raises(AnalysisMethodQualificationError, match="does not replay"):
        revalidate_analysis_method_proof(
            proof,
            inputs["workspace"],
            inputs["profile"],
            inputs["assignment"],
            inputs["label"],
            inputs["snapshot"],
            inputs["files"],
            inputs["identities"],
            inputs["questions"],
            inputs["answers"],
            inputs["contracts"],
            inputs["assertions"],
            inputs["detector"],
            inputs["parsers"],
            inputs["profiles"],
            inputs["versions"],
        )
    with pytest.raises(AnalysisMethodQualificationError, match="chronology"):
        _verify(inputs, proof_frozen_at="2026-07-31T17:11:30Z")


def test_identity_inventory_utf8_and_budget_boundaries_fail_closed(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    weak_inputs = _inputs(project_root, schema_root, tmp_path / "weak")
    weak_identities = deepcopy(weak_inputs["identities"])
    weak_identities[0]["tier"] = "weak_fingerprint"
    assert _verify(weak_inputs, identities=weak_identities)["proof_status"] == "unavailable"

    inventory_inputs = _inputs(project_root, schema_root, tmp_path / "inventory")
    (inventory_inputs["workspace"] / "report.md").unlink()
    assert _verify(inventory_inputs)["proof_status"] == "unavailable"

    utf8_inputs = _inputs(
        project_root,
        schema_root,
        tmp_path / "utf8",
        qualification_extra_bytes=("opaque.md", b"\xff\xfe"),
    )
    utf8_proof = _verify(utf8_inputs)
    assert utf8_proof["proof_status"] == "unavailable"
    assert (
        next(
            item
            for item in utf8_proof["applicability_results"]
            if item["check_id"] == "strict_utf8_complete"
        )["completion_status"]
        == "unavailable"
    )

    budget_inputs = _inputs(project_root, schema_root, tmp_path / "budget")
    small_profile = freeze_bounded_analysis_method_profile(
        budget_inputs["detector"],
        budget_inputs["parsers"],
        budget_inputs["profiles"],
        budget_inputs["versions"],
        budget_inputs["selection"],
        frozen_at="2026-07-31T17:10:00Z",
        max_total_bytes=1,
    )
    assert _verify(budget_inputs, profile=small_profile)["proof_status"] == "unavailable"


def test_verifier_imports_no_production_fact_deriver(project_root: Path) -> None:
    source = (
        project_root
        / "evaluation"
        / "src"
        / "sc_referee_evaluation"
        / "analysis_method_qualification.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and isinstance(node.module, str)
    }
    assert not any(
        module.startswith("sc_referee.scientific_checks")
        or module.startswith("sc_referee.detectors")
        or module.startswith("sc_referee.posthoc_method_ledger")
        for module in imports
    )


def test_analysis_method_static_case_cli_writes_the_same_proof(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(
        project_root,
        schema_root,
        tmp_path,
        requirement_operand=DIRECT,
    )
    expected = _verify(inputs)
    paths: dict[str, Path] = {}
    for name in ("profile", "assignment", "label", "snapshot", "detector"):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(inputs[name]), encoding="utf-8")
        paths[name] = path
    for name, key in (
        ("files", "files"),
        ("identities", "identities"),
        ("questions", "questions"),
        ("answers", "answers"),
        ("contracts", "contracts"),
        ("assertions", "assertions"),
    ):
        path = tmp_path / f"{name}.jsonl"
        path.write_text(
            "".join(json.dumps(item) + "\n" for item in inputs[key]),
            encoding="utf-8",
        )
        paths[name] = path
    manifest_options: list[str] = []
    for option, key in (
        ("--parser-manifest", "parsers"),
        ("--semantic-profile-manifest", "profiles"),
        ("--version-manifest", "versions"),
    ):
        for index, record in enumerate(inputs[key]):
            path = tmp_path / f"{key}-{index}.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            manifest_options.extend([option, str(path)])
    output = tmp_path / "method-proof.json"
    arguments = [
        "verify-analysis-method-static-case",
        "--materialized-root",
        str(inputs["workspace"]),
        "--profile",
        str(paths["profile"]),
        "--detector-manifest",
        str(paths["detector"]),
        *manifest_options,
        "--case-assignment-artifact",
        str(paths["assignment"]),
        "--label-freeze-artifact",
        str(paths["label"]),
        "--snapshot",
        str(paths["snapshot"]),
        "--file-records-jsonl",
        str(paths["files"]),
        "--asset-identities-jsonl",
        str(paths["identities"]),
        "--material-questions-jsonl",
        str(paths["questions"]),
        "--answers-jsonl",
        str(paths["answers"]),
        "--scientific-contracts-jsonl",
        str(paths["contracts"]),
        "--semantic-assertions-jsonl",
        str(paths["assertions"]),
        "--proof-frozen-at",
        "2026-07-31T17:13:00Z",
        "--output",
        str(output),
    ]
    assert evaluation_main(arguments) == 0
    assert json.loads(output.read_text(encoding="utf-8")) == expected
