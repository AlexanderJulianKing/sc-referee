from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from shutil import copytree
from typing import Any

import pytest
import sc_referee_evaluation.prospective_selected_result_verifier as verifier_module
from sc_referee_evaluation.prospective_qualification_v2 import (
    ProspectiveQualificationV2Error,
    freeze_case_evidence_contract,
    freeze_stage2_scientific_label,
)
from sc_referee_evaluation.prospective_selected_result_verifier import (
    MAX_CANDIDATE_BINDINGS,
    MAX_MODULE_STATEMENTS,
    MAX_TEXT_LINES,
    PYTHON_STATIC_MARKED_REPORT_PROFILE,
    ProspectiveSelectedResultVerifierError,
    freeze_independent_selected_result_derivation,
    freeze_selected_result_validation,
    revalidate_independent_selected_result_derivation,
    validate_independent_selected_result_derivation,
    validate_selected_result_validation,
)

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id

CASE_ID = "case:fedcba9876543210abcd"
ISSUE_CLASS = "issue-class:retained-subset-for-complete-domain"
DIGEST_A = "sha256:" + "a" * 64
REPORT = b"[selected-result] all,100\n"
SOURCE = b"domain,total\nall,100\n"
PRODUCER = (
    b"from pathlib import Path\n"
    b"table = Path('inputs/map.csv').read_text()\n"
    b"value = table.splitlines()[1]\n"
    b"report = f'[selected-result] {value}\\n'\n"
    b"Path('results/report.md').write_text(report)\n"
)
ALTERNATIVE = (
    b"from pathlib import Path\n"
    b"rows = Path('inputs/map.csv').read_text().splitlines()\n"
    b"report = '[selected-result] ' + rows[1] + '\\n'\n"
    b"Path('results/report.md').write_text(report)\n"
)


def _locator(path: str, payload: bytes, start: int, end: int) -> dict[str, Any]:
    return {
        "path": path,
        "content_digest": sha256_digest(payload),
        "start_line": start,
        "end_line": end,
    }


def _binding(
    *,
    producer_path: str = "workflow/analysis.py",
    producer_payload: bytes = PRODUCER,
    producer_line: int = 5,
    alternatives: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "binding_profile": "exact_selected_report_result_static_producer_v1",
        "selection_status": "one_selected_result",
        "report_locator": _locator("results/report.md", REPORT, 1, 1),
        "result_locator": _locator("results/report.md", REPORT, 1, 1),
        "producer_locator": _locator(producer_path, producer_payload, producer_line, producer_line),
        "source_operands": [
            {
                "operand_id": stable_id("operand", "inputs/map.csv", sha256_digest(SOURCE)),
                "record_ref": {
                    "record_type": "file_record",
                    "record_id": stable_id("file", "inputs/map.csv", sha256_digest(SOURCE)),
                },
                "source_locator": _locator("inputs/map.csv", SOURCE, 1, 2),
            }
        ],
        "alternative_producer_locators": alternatives or [],
        "declared_dynamic_selection": False,
    }


def _write_case(
    root: Path,
    *,
    report: bytes = REPORT,
    producer: bytes = PRODUCER,
    include_alternative: bool = False,
) -> Path:
    (root / "results").mkdir(parents=True)
    (root / "workflow").mkdir()
    (root / "inputs").mkdir()
    (root / "results" / "report.md").write_bytes(report)
    (root / "workflow" / "analysis.py").write_bytes(producer)
    (root / "inputs" / "map.csv").write_bytes(SOURCE)
    if include_alternative:
        (root / "workflow" / "alternative.py").write_bytes(ALTERNATIVE)
    return root


def _case_contract(binding: dict[str, Any] | None = None) -> dict[str, Any]:
    return freeze_case_evidence_contract(
        {
            "case_id": CASE_ID,
            "envelope": {
                "envelope_id": "relation-envelope:complete-domain-exposure-denominator",
                "check_id": "check:complete-domain-exposure-denominator",
                "candidate_id": "complete-declared-domain-exposure",
                "binding_digest": DIGEST_A,
            },
            "canonical_issue_class": ISSUE_CLASS,
            "selected_result_binding": binding or _binding(),
            "authorship": {
                "author_id": "actor:prospective-author",
                "provider": "Author Provider",
                "execution_context_id": "context:author",
                "identity_evidence_digest": DIGEST_A,
            },
            "authored_at": "2026-08-05T00:00:00Z",
        },
        frozen_at="2026-08-05T01:00:00Z",
    )


def _derivation_spec(
    *,
    validator_id: str = "actor:independent-evidence-validator",
    provider: str = "Provider C",
) -> dict[str, Any]:
    return {
        "case_id": CASE_ID,
        "validator_identity": {
            "validator_id": validator_id,
            "provider": provider,
            "execution_context_id": "context:validator",
            "identity_evidence_digest": "sha256:" + "c" * 64,
        },
        "profile_id": PYTHON_STATIC_MARKED_REPORT_PROFILE,
        "selected_report_path": "results/report.md",
        "derived_at": "2026-08-05T02:00:00Z",
    }


def _derive(root: Path, **identity: str) -> dict[str, Any]:
    return freeze_independent_selected_result_derivation(
        root,
        _derivation_spec(**identity),
        frozen_at="2026-08-05T03:00:00Z",
    )


def _validation(root: Path, contract: dict[str, Any], derivation: dict[str, Any]) -> dict[str, Any]:
    return freeze_selected_result_validation(
        root,
        contract,
        derivation,
        declaration_revealed_at="2026-08-05T04:00:00Z",
        compared_at="2026-08-05T05:00:00Z",
    )


def _digested(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = deepcopy(value)
    result[field] = semantic_digest(result)
    return result


def _review(reviewer_id: str, provider: str, binding_digest: str) -> dict[str, Any]:
    return _digested(
        {
            "reviewer_id": reviewer_id,
            "provider": provider,
            "completed_at": "2026-08-05T06:00:00Z",
            "scientific_label": "issue_present",
            "issue_class_id": ISSUE_CLASS,
            "selected_result_binding_digest": binding_digest,
            "selected_result_binding_status": "verified",
            "finite_counterevidence_status": "complete",
            "bounded_description": "The selected result has the canonical issue.",
        },
        "review_digest",
    )


def _label_spec(contract: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    binding_digest = str(contract["selected_result_binding_digest"])
    return {
        "case_id": contract["case_id"],
        "envelope_id": contract["envelope"]["envelope_id"],
        "case_contract_digest": contract["contract_digest"],
        "reviews": [
            _review("actor:stage2-a", "Provider A", binding_digest),
            _review("actor:stage2-b", "Provider B", binding_digest),
        ],
        "independent_evidence_validation": validation,
    }


def test_verifier_derives_binding_from_bytes_and_enables_label(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    contract = _case_contract()
    derivation = _derive(root)

    assert derivation["derivation_status"] == "one_selected_result_rederived"
    assert derivation["candidate_bindings"] == [contract["selected_result_binding"]]
    assert derivation["project_code_executed"] is False
    assert revalidate_independent_selected_result_derivation(derivation, root) == derivation

    validation = _validation(root, contract, derivation)
    assert validation["status"] == "verified_complete"
    assert (
        validate_selected_result_validation(validation, case_root=root, case_contract=contract)
        == validation
    )
    label = freeze_stage2_scientific_label(
        _label_spec(contract, validation),
        case_root=root,
        case_contract=contract,
        frozen_at="2026-08-05T07:00:00Z",
    )
    assert label["scientific_label"] == "issue_present"


def test_caller_cannot_supply_candidate_bindings_or_failure_reasons(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    for field, value in (
        ("candidate_bindings", [_binding()]),
        ("unsupported_constructs", ["caller_asserted"]),
        ("unavailable_evidence", ["caller_asserted"]),
    ):
        spec = _derivation_spec()
        spec[field] = value
        with pytest.raises(ProspectiveSelectedResultVerifierError, match="unsupported shape"):
            freeze_independent_selected_result_derivation(
                root, spec, frozen_at="2026-08-05T03:00:00Z"
            )


def test_omitted_alternative_cannot_turn_ambiguity_into_complete(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case", include_alternative=True)
    derivation = _derive(root)

    assert derivation["derivation_status"] == "ambiguous_selected_result"
    assert len(derivation["candidate_bindings"]) == 2
    assert {item["producer_locator"]["path"] for item in derivation["candidate_bindings"]} == {
        "workflow/analysis.py",
        "workflow/alternative.py",
    }
    validation = _validation(root, _case_contract(), derivation)
    assert validation["status"] == "ambiguous_selected_result"
    assert validation["selected_result_binding_digest"] is None


def test_unsupported_alternative_writer_cannot_be_silently_omitted(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    (root / "workflow" / "legacy.py").write_bytes(
        b"open('results/report.md', 'w').write('alternate')\n"
    )
    derivation = _derive(root)
    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["opaque_or_unallowlisted_python_call"]


def test_python_module_without_selected_writer_cannot_be_silently_ignored(
    tmp_path: Path,
) -> None:
    root = _write_case(tmp_path / "case")
    (root / "workflow" / "plugin.py").write_bytes(b"import arbitrary_plugin\n")

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["python_module_without_selected_report_writer"]


def test_constructed_path_in_opaque_call_cannot_hide_an_alternative(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    (root / "workflow" / "opaque.py").write_bytes(
        b"from pathlib import Path\n"
        b"source = Path('inputs/map.csv').read_text()\n"
        b"publish('results/' + 'report.md', source)\n"
    )
    derivation = _derive(root)
    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["opaque_or_unallowlisted_python_call"]


def test_non_python_alternative_producer_cannot_be_silently_ignored(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    (root / "workflow" / "alternative.sh").write_bytes(
        b"printf '[selected-result] all,100\\n' > results/report.md\n"
    )

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["unsupported_non_python_source_artifact"]


def test_executable_operand_cannot_hide_an_alternative_producer(tmp_path: Path) -> None:
    disguised_payload = b"#!/bin/sh\nprintf '[selected-result] all,100\\n' > results/report.md\n"
    root = _write_case(tmp_path / "case", report=REPORT + disguised_payload)
    disguised = root / "inputs" / "disguised.csv"
    disguised.write_bytes(disguised_payload)
    disguised.chmod(0o755)
    producer = (
        b"from pathlib import Path\n"
        b"source = Path('inputs/map.csv').read_text()\n"
        b"disguised = Path('inputs/disguised.csv').read_text()\n"
        b"report = '[selected-result] ' + source.splitlines()[1] + '\\n' + disguised\n"
        b"Path('results/report.md').write_text(report)\n"
    )
    (root / "workflow" / "analysis.py").write_bytes(producer)

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["unsupported_source_operand_role"]


def test_unclassified_case_file_cannot_be_declared_inert_by_omission(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    (root / "README.txt").write_bytes(b"unclassified case material\n")

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["unclassified_case_artifact"]


def test_retained_report_must_equal_the_static_writer_output(tmp_path: Path) -> None:
    root = _write_case(
        tmp_path / "case",
        report=b"[selected-result] claimed value = 999\n",
    )
    derivation = _derive(root)
    assert derivation["derivation_status"] == "insufficient_evidence"
    assert derivation["reason_codes"] == ["selected_report_bytes_do_not_match_static_writer"]


@pytest.mark.parametrize(
    ("source", "reason"),
    (
        (b"domain,total\r\nall,100\r\n", "non_lf_normalized_text_evidence"),
        ("domain,total\nall,café\n".encode(), "non_ascii_text_evidence"),
    ),
)
def test_text_io_requires_ascii_lf_operands(tmp_path: Path, source: bytes, reason: str) -> None:
    root = _write_case(tmp_path / "case")
    (root / "inputs" / "map.csv").write_bytes(source)

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == [reason]


def test_runtime_encoding_must_map_ascii_bytes_to_ascii_codepoints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _write_case(tmp_path / "case")
    monkeypatch.setattr(verifier_module.locale, "getencoding", lambda: "cp037")

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["text_io_runtime_unsupported"]


def test_writer_must_carry_the_selected_marker_and_be_unconditional(tmp_path: Path) -> None:
    missing_marker = (
        b"from pathlib import Path\n"
        b"source = Path('inputs/map.csv').read_text()\n"
        b"Path('results/report.md').write_text(source)\n"
    )
    root = _write_case(tmp_path / "missing-marker", producer=missing_marker)
    derivation = _derive(root)
    assert derivation["derivation_status"] == "insufficient_evidence"
    assert derivation["reason_codes"] == ["selected_report_bytes_do_not_match_static_writer"]

    nested = (
        b"from pathlib import Path\n"
        b"source = Path('inputs/map.csv').read_text()\n"
        b"report = '[selected-result] ' + source\n"
        b"if False:\n"
        b"    Path('results/report.md').write_text(report)\n"
    )
    root = _write_case(tmp_path / "nested", producer=nested)
    derivation = _derive(root)
    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["non_straight_line_module_statement"]


def test_control_flow_cannot_supply_a_selected_report_dependency(tmp_path: Path) -> None:
    producer = (
        b"from pathlib import Path\n"
        b"source = Path('inputs/map.csv').read_text()\n"
        b"if False:\n"
        b"    report = '[selected-result] ' + source\n"
        b"Path('results/report.md').write_text(report)\n"
    )
    root = _write_case(tmp_path / "case", producer=producer)
    derivation = _derive(root)
    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["non_straight_line_module_statement"]


@pytest.mark.parametrize(
    "producer",
    (
        PRODUCER.replace(b"from pathlib import Path", b"from evil import Path"),
        PRODUCER + b"later = 'opaque'.strip()\n",
    ),
)
def test_import_binding_and_post_writer_statements_are_closed(
    tmp_path: Path, producer: bytes
) -> None:
    root = _write_case(tmp_path / "case", producer=producer)
    derivation = _derive(root)
    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"][0] in {
        "non_straight_line_module_statement",
        "unsupported_python_import_binding",
    }


def test_numeric_conversion_failure_is_localized(tmp_path: Path) -> None:
    producer = (
        b"from pathlib import Path\n"
        b"source = Path('inputs/map.csv').read_text()\n"
        b"value = int(source)\n"
        b"report = f'[selected-result] {value}\\n'\n"
        b"Path('results/report.md').write_text(report)\n"
    )
    root = _write_case(tmp_path / "case", producer=producer)
    derivation = _derive(root)
    assert derivation["derivation_status"] == "insufficient_evidence"
    assert derivation["reason_codes"] == ["static_numeric_conversion_failed"]


def test_unencodable_static_text_is_localized(tmp_path: Path) -> None:
    producer = (
        b"from pathlib import Path\n"
        b"source = Path('inputs/map.csv').read_text()\n"
        b"report = '[selected-result] ' + '\\ud800' + source\n"
        b"Path('results/report.md').write_text(report)\n"
    )
    root = _write_case(tmp_path / "case", producer=producer)

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["selected_report_text_not_utf8_encodable"]


def test_forward_reference_is_not_treated_as_executable_dataflow(tmp_path: Path) -> None:
    producer = (
        b"from pathlib import Path\n"
        b"report = '[selected-result] ' + source.splitlines()[1] + '\\n'\n"
        b"source = Path('inputs/map.csv').read_text()\n"
        b"Path('results/report.md').write_text(report)\n"
    )
    root = _write_case(tmp_path / "case", producer=producer)

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["unsupported_selected_report_dependency_flow"]


def test_path_binding_cannot_be_shadowed(tmp_path: Path) -> None:
    producer = (
        b"from pathlib import Path\n"
        b"Path = 'not pathlib.Path'\n"
        b"source = Path('inputs/map.csv').read_text()\n"
        b"report = '[selected-result] ' + source.splitlines()[1] + '\\n'\n"
        b"Path('results/report.md').write_text(report)\n"
    )
    root = _write_case(tmp_path / "case", producer=producer)

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["reserved_python_binding_reassigned"]


def test_path_cannot_be_used_before_its_exact_import(tmp_path: Path) -> None:
    producer = (
        b"source = Path('inputs/map.csv').read_text()\n"
        b"from pathlib import Path\n"
        b"report = '[selected-result] ' + source.splitlines()[1] + '\\n'\n"
        b"Path('results/report.md').write_text(report)\n"
    )
    root = _write_case(tmp_path / "case", producer=producer)

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["unsupported_python_import_binding"]


@pytest.mark.parametrize(
    "producer",
    (
        b"# coding: cp037\n" + PRODUCER,
        b"\xef\xbb\xbf" + PRODUCER,
    ),
)
def test_python_encoding_declaration_cannot_change_executable_source_semantics(
    tmp_path: Path, producer: bytes
) -> None:
    root = _write_case(tmp_path / "case", producer=producer)

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["unsupported_python_encoding_declaration"]


def test_candidate_ceiling_is_enforced_before_cartesian_materialization(tmp_path: Path) -> None:
    report = b"".join(
        f"[selected-result] row-{index}\n".encode() for index in range(MAX_CANDIDATE_BINDINGS + 1)
    )
    root = _write_case(tmp_path / "case", report=report)

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["selected_result_candidate_ceiling_exceeded"]


def test_line_ceiling_is_enforced_before_split_materialization(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case", report=b"x\n" * (MAX_TEXT_LINES + 1))

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["selected_result_line_ceiling_exceeded"]


def test_selected_report_cannot_also_be_an_executable_script(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case", report=b"#!/bin/sh\n" + REPORT)
    (root / "results" / "report.md").chmod(0o755)

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["unsupported_selected_report_role"]


def test_static_value_growth_is_bounded(tmp_path: Path) -> None:
    assignments = [b"padding = ' '\n"]
    assignments.extend(
        f"padding_{index} = {('padding' if index == 0 else f'padding_{index - 1}')} + "
        f"{('padding' if index == 0 else f'padding_{index - 1}')}\n".encode()
        for index in range(25)
    )
    producer = b"".join(
        [
            b"from pathlib import Path\n",
            *assignments,
            b"source = Path('inputs/map.csv').read_text()\n",
            b"report = '[selected-result] ' + source.splitlines()[1] + '\\n' + "
            b"padding_24.strip()\n",
            b"Path('results/report.md').write_text(report)\n",
        ]
    )
    root = _write_case(tmp_path / "case", producer=producer)

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["static_value_byte_ceiling_exceeded"]


def test_module_statement_budget_is_cumulative(tmp_path: Path) -> None:
    aliases = [b"value_0 = source\n"]
    aliases.extend(
        f"value_{index} = value_{index - 1}\n".encode() for index in range(1, MAX_MODULE_STATEMENTS)
    )
    producer = b"".join(
        [
            b"from pathlib import Path\n",
            b"source = Path('inputs/map.csv').read_text()\n",
            *aliases,
            b"report = '[selected-result] ' + value_63.splitlines()[1] + '\\n'\n",
            b"Path('results/report.md').write_text(report)\n",
        ]
    )
    root = _write_case(tmp_path / "case", producer=producer)

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["python_module_statement_ceiling_exceeded"]


def test_unbounded_join_grammar_is_rejected_before_allocation(tmp_path: Path) -> None:
    producer = (
        b"from pathlib import Path\n"
        b"source = Path('inputs/map.csv').read_text()\n"
        b"rows = source.splitlines()\n"
        b"report = ''.join(rows)\n"
        b"Path('results/report.md').write_text(report)\n"
    )
    root = _write_case(tmp_path / "case", producer=producer)

    derivation = _derive(root)

    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["opaque_or_unallowlisted_python_call"]


@pytest.mark.parametrize(
    ("report", "producer", "expected"),
    (
        (b"No selected marker.\n", PRODUCER, "insufficient_evidence"),
        (
            REPORT,
            b"from pathlib import Path\n"
            b"report = '[selected-result] fixed\\n'\n"
            b"Path('results/report.md').write_text(report)\n",
            "insufficient_evidence",
        ),
        (
            REPORT,
            b"from pathlib import Path\n"
            b"target = 'results/report.md'\n"
            b"source = Path('inputs/map.csv').read_text()\n"
            b"Path(target).write_text(source)\n",
            "unsupported_structure",
        ),
    ),
)
def test_missing_or_unsupported_structure_never_verifies(
    tmp_path: Path, report: bytes, producer: bytes, expected: str
) -> None:
    root = _write_case(tmp_path / "case", report=report, producer=producer)
    derivation = _derive(root)
    assert derivation["derivation_status"] == expected
    validation = _validation(root, _case_contract(), derivation)
    assert validation["status"] == expected
    assert validation["selected_result_binding_digest"] is None


def test_forged_self_digested_derivation_cannot_bypass_byte_replay(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    derivation = _derive(root)
    forged = deepcopy(derivation)
    forged["candidate_bindings"][0]["producer_locator"]["start_line"] = 4
    forged["candidate_bindings"][0]["producer_locator"]["end_line"] = 4
    forged["candidate_binding_digests"] = [semantic_digest(forged["candidate_bindings"][0])]
    forged["derivation_digest"] = semantic_digest(
        {key: value for key, value in forged.items() if key != "derivation_digest"}
    )

    assert validate_independent_selected_result_derivation(forged) == forged
    with pytest.raises(ProspectiveSelectedResultVerifierError, match="does not replay"):
        _validation(root, _case_contract(), forged)


def test_byte_drift_and_unlisted_file_break_replay(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    derivation = _derive(root)
    (root / "inputs" / "map.csv").write_bytes(SOURCE + b"extra,1\n")
    with pytest.raises(ProspectiveSelectedResultVerifierError, match="does not replay"):
        revalidate_independent_selected_result_derivation(derivation, root)


def test_derivation_replays_from_an_identical_tree_at_a_new_location(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    derivation = _derive(root)
    copied = copytree(root, tmp_path / "copied-case")

    assert revalidate_independent_selected_result_derivation(derivation, copied) == derivation

    root = _write_case(tmp_path / "second-case")
    derivation = _derive(root)
    (root / "unlisted.txt").write_text("new evidence\n", encoding="utf-8")
    with pytest.raises(ProspectiveSelectedResultVerifierError, match="does not replay"):
        revalidate_independent_selected_result_derivation(derivation, root)


def test_root_and_child_symlinks_are_rejected(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    root_link = tmp_path / "case-link"
    root_link.symlink_to(root, target_is_directory=True)
    with pytest.raises(ProspectiveSelectedResultVerifierError, match="root cannot"):
        _derive(root_link)

    (root / "linked.py").symlink_to(root / "workflow" / "analysis.py")
    with pytest.raises(ProspectiveSelectedResultVerifierError, match="symbolic links"):
        _derive(root)


def test_directory_depth_is_bounded(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    nested = root
    for index in range(10):
        nested = nested / f"nested-{index}"
        nested.mkdir()
    with pytest.raises(ProspectiveSelectedResultVerifierError, match="depth ceiling"):
        _derive(root)


def test_project_code_is_never_executed(tmp_path: Path) -> None:
    marker = tmp_path / "project-code-ran"
    producer = PRODUCER + b"assert False, 'project code executed'\n"
    root = _write_case(tmp_path / "case", producer=producer)
    derivation = _derive(root)
    assert derivation["derivation_status"] == "unsupported_structure"
    assert derivation["reason_codes"] == ["non_straight_line_module_statement"]
    assert not marker.exists()


def test_binding_mismatch_is_insufficient_not_verified(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    contract_binding = _binding()
    contract_binding["producer_locator"]["start_line"] = 4
    contract_binding["producer_locator"]["end_line"] = 4
    contract = _case_contract(contract_binding)
    validation = _validation(root, contract, _derive(root))
    assert validation["status"] == "insufficient_evidence"
    assert validation["selected_result_binding_digest"] is None


def test_author_independence_and_blind_chronology_are_enforced(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    contract = _case_contract()
    derivation = _derive(root, provider="Author Provider")
    with pytest.raises(ProspectiveSelectedResultVerifierError, match="independent"):
        _validation(root, contract, derivation)

    derivation = _derive(root)
    with pytest.raises(ProspectiveSelectedResultVerifierError, match="revealed before"):
        freeze_selected_result_validation(
            root,
            contract,
            derivation,
            declaration_revealed_at="2026-08-05T02:30:00Z",
            compared_at="2026-08-05T05:00:00Z",
        )


def test_legacy_handwritten_validation_summary_is_rejected(tmp_path: Path) -> None:
    root = _write_case(tmp_path / "case")
    contract = _case_contract()
    valid = _validation(root, contract, _derive(root))
    legacy = _digested(
        {
            "validator_id": valid["validator_id"],
            "provider": valid["provider"],
            "completed_at": valid["completed_at"],
            "case_contract_digest": valid["case_contract_digest"],
            "status": "verified_complete",
            "selected_result_binding_digest": valid["selected_result_binding_digest"],
        },
        "validation_digest",
    )
    with pytest.raises(ProspectiveQualificationV2Error, match="Unsupported"):
        freeze_stage2_scientific_label(
            _label_spec(contract, legacy),
            case_root=root,
            case_contract=contract,
            frozen_at="2026-08-05T07:00:00Z",
        )
