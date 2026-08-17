"""Growth-15 abort-only guards and ordinary group-fact replay regressions."""

from __future__ import annotations

import ast
import csv
import io
import json
import os
import random
import re
import subprocess
import textwrap
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition.ir import (
    MAX_DEPENDENCE_CSV_DOMAIN_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELDS,
    MAX_DEPENDENCE_CSV_DOMAIN_ROWS,
    MAX_V1_MEMBERSHIPS,
)
from sc_referee.dependence_recognition_v2.adapter import DependenceRecognitionV2ShadowAdapter
from sc_referee.dependence_recognition_v2.certificate import (
    _kernel_replay_group_fact,
    verify_dependence_growth_certificate,
)
from sc_referee.dependence_recognition_v2.csv_domain import (
    prove_group_value_sequences_with_reason,
)
from sc_referee.dependence_recognition_v2.ir import (
    MAX_V2_GROUPS,
    DependenceGrowthCertificate,
    GroupValueSequence,
    GroupValueSequenceFact,
    GroupValueSequenceObligation,
)
from sc_referee.dependence_recognition_v2.python_analyzer import (
    _analyzer_abort_only_guard_statement,
    _analyzer_abort_only_raise_wall,
    _trusted_v2_authorizations,
    _trusted_v2_procedure_sets,
    analyze_dependence_growth_python,
    discharge_dependence_growth_analysis,
)
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    InspectionDocument,
    RecordRef,
    ScientificCheckContractError,
)

_DATA_PATH = "inputs/data.csv"
_RUNTIME = Path(
    os.environ.get(
        "SC_REFEREE_DEPENDENCE_V2_SANDBOX_PYTHON",
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime/"
        "scipy114-venv/bin/python",
    )
)
_ADVERSE = b"unit_id,arm,value\nu1,A,1\nu1,A,2\nu2,B,3\nu3,B,4\n"
_COVERED = b"unit_id,arm,value\nu1,A,1\nu2,A,2\nu3,B,3\nu4,B,4\n"
_ATTEMPT3 = b"unit_id,arm,value\nu1,A,1\nu2,B,2\nu3,B,3\nu3,B,4\nu4,B,5\n"


def _source(
    guards: str = "",
    *,
    line_model: str = "csv_newline",
    cast_kind: str = "float",
    predeclared: bool = False,
    operand_form: str = "aliases",
) -> str:
    if line_model == "csv_newline":
        reader = """    with INPUT.open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))"""
    else:
        reader = """    rows = list(
        csv.DictReader(INPUT.read_text(encoding="ascii").splitlines())
    )"""
    declaration = 'groups = {"A": [], "B": []}' if predeclared else "groups = {}"
    append = (
        f'groups[row["arm"]].append({cast_kind}(row["value"]))'
        if predeclared
        else f'groups.setdefault(row["arm"], []).append({cast_kind}(row["value"]))'
    )
    if operand_form == "aliases":
        operands = "    left = groups[LEFT]\n    right = groups[RIGHT]"
        call = "stats.ttest_ind(left, right)"
    elif operand_form == "sorted":
        operands = "    (_, left), (_, right) = sorted(groups.items())"
        call = "stats.ttest_ind(left, right)"
    elif operand_form in {"array", "asarray"}:
        operands = (
            f"    left = np.{operand_form}(groups[LEFT], dtype=float)\n"
            f"    right = np.{operand_form}(groups[RIGHT], dtype=float)"
        )
        call = "stats.ttest_ind(left, right)"
    else:
        operands = ""
        call = "stats.ttest_ind(groups[LEFT], groups[RIGHT])"
    numpy_import = "import numpy as np\n" if operand_form in {"array", "asarray"} else ""
    guard_block = "\n".join(f"    {line}" if line else "" for line in guards.splitlines())
    if guard_block:
        guard_block += "\n"
    return f"""import csv
{numpy_import}from pathlib import Path
from scipy import stats

INPUT = Path("inputs/data.csv")
LEFT = "A"
RIGHT = "B"
REPORT = Path("results/report.md")

def main():
{reader}
    {declaration}
    for row in rows:
        {append}
{operands}
{guard_block}    result = {call}
    REPORT.write_text(str(result), encoding="utf-8")

main()
"""


def _context(
    source: str,
    data: bytes,
    *,
    unit_column: str = "unit_id",
    data_path: str = _DATA_PATH,
) -> FrozenInspectionContext:
    suffix = semantic_digest(
        {"source": source, "data_digest": sha256_digest(data), "unit": unit_column}
    )[-16:]
    surface = RecordRef("publication_surface", f"surface:g15:{suffix}")
    artifact = RecordRef("artifact", f"artifact:g15:{suffix}")
    snapshot = RecordRef("repository_snapshot", f"snapshot:g15:{suffix}")
    source_file = RecordRef("file_record", f"file:g15-source:{suffix}")
    parser = RecordRef("parser_result", f"parser:g15:{suffix}")
    data_file = RecordRef("file_record", f"file:g15-data:{suffix}")
    data_identity = RecordRef("asset_identity", f"asset:g15-data:{suffix}")
    requirements_file = RecordRef("file_record", f"file:g15-requirements:{suffix}")
    requirements_identity = RecordRef("asset_identity", f"asset:g15-requirements:{suffix}")
    analysis = RecordRef("analysis", f"analysis:g15:{suffix}")
    procedure = RecordRef("procedure", f"procedure-v2:g15:{suffix}")
    result = RecordRef("result", f"result-v2:g15:{suffix}")
    authority = RecordRef("human_method_authorization", f"authorization-v2:g15:{suffix}")
    data_digest = sha256_digest(data)
    requirements = b"scipy==1.14.0\n"
    requirements_digest = sha256_digest(requirements)
    source_bytes = source.encode("utf-8")
    parser_payload = canonical_json(
        {"parser_id": "python-ast", "parser_version": "3.11", "state": "parsed"}
    ).encode()
    records: list[tuple[RecordRef, dict[str, object]]] = [
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
                "identity_evidence": {"kind": "full_digest", "digest": requirements_digest},
            },
        ),
        (source_file, {"file_record_id": source_file.record_id}),
        (parser, {"parser_result_id": parser.record_id}),
        (analysis, {"analysis_id": analysis.record_id}),
        (
            procedure,
            {
                "procedure_id": procedure.record_id,
                "resolved_callable": "scipy.stats.ttest_ind",
            },
        ),
        (result, {"result_id": result.record_id, "path": "results/report.md"}),
        (
            authority,
            {
                "record_type": "human_method_authorization",
                "record_id": authority.record_id,
                "actor_id": "human:method-owner",
                "authority_state": "authorized",
                "analysis_target_ref": analysis.to_dict(),
                "procedure_ref": procedure.to_dict(),
                "independent_unit_definition_id": "unit-definition:g15",
                "authorized_key_columns": [unit_column],
                "input_path": data_path,
                "input_content_digest": data_digest,
            },
        ),
    ]
    return FrozenInspectionContext(
        snapshot_digest=sha256_digest(f"snapshot:{suffix}".encode()),
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
        base_records=tuple(FrozenBaseRecord.from_record(ref, value) for ref, value in records),
        material_inputs=(
            FrozenMaterialInput(data_path, data_file, data_identity, data, data_digest),
            FrozenMaterialInput(
                "requirements.txt",
                requirements_file,
                requirements_identity,
                requirements,
                requirements_digest,
            ),
        ),
    )


def _data_material(context: FrozenInspectionContext, path: str = _DATA_PATH) -> FrozenMaterialInput:
    return next(item for item in context.material_inputs if item.path == path)


def _fact(
    context: FrozenInspectionContext, obligation: GroupValueSequenceObligation
) -> GroupValueSequenceFact:
    fact, reason = prove_group_value_sequences_with_reason(
        _data_material(context, obligation.path), obligation=obligation
    )
    assert reason is None and fact is not None
    return fact


def _conclusion(fact: GroupValueSequenceFact) -> str:
    repeated = any(
        count > 1 for group in fact.groups for count in Counter(group.authorized_unit_ids).values()
    )
    return "repeated_units" if repeated else "one_observation_per_unit"


def _final_certificate(
    certificate: DependenceGrowthCertificate, fact: GroupValueSequenceFact
) -> DependenceGrowthCertificate:
    conclusion = cast(Any, _conclusion(fact))
    certificate = replace(certificate, conclusion=conclusion)
    return replace(
        certificate,
        certificate_id=(
            "dependence-growth-certificate:"
            + semantic_digest(
                {
                    "source_digest": certificate.source_digest,
                    "fact": fact.evidence_id,
                    "bindings": [asdict(item) for item in certificate.operand_bindings],
                    "abort_only_guard_tokens": [
                        asdict(item) for item in certificate.abort_only_guard_tokens
                    ],
                    "conclusion": conclusion,
                }
            )
        ),
    )


def _verify(
    certificate: DependenceGrowthCertificate,
    fact: GroupValueSequenceFact,
    context: FrozenInspectionContext,
    *,
    facts: tuple[GroupValueSequenceFact, ...] | None = None,
    materials: tuple[FrozenMaterialInput, ...] | None = None,
) -> tuple[object | None, list[str]]:
    failures: list[str] = []
    verified = verify_dependence_growth_certificate(
        certificate,
        trusted_group_facts=(fact,) if facts is None else facts,
        trusted_material_inputs=(
            (_data_material(context, certificate.obligation.path),)
            if materials is None
            else materials
        ),
        trusted_authorizations=_trusted_v2_authorizations(context),
        trusted_procedure_sets=_trusted_v2_procedure_sets(context),
        source_bytes=context.documents[0].content,
        _failure_reasons=failures,
    )
    return verified, failures


@pytest.mark.parametrize(
    ("data", "conclusion"),
    [(_ADVERSE, "repeated_units"), (_COVERED, "one_observation_per_unit")],
)
def test_false_len_guards_preserve_existing_conclusions(data: bytes, conclusion: str) -> None:
    guards = """if len(left) < 2 or len(right) < 2:
    raise ValueError("short group")
if len(groups) != 2:
    raise SystemExit("wrong group count")"""
    context = _context(_source(guards), data)
    analysis = analyze_dependence_growth_python(context)
    assert analysis.certificate is not None
    assert len(analysis.certificate.abort_only_guard_tokens) == 2
    assert [item.guard_ordinal for item in analysis.certificate.abort_only_guard_tokens] == [0, 1]
    discharged = discharge_dependence_growth_analysis(analysis, context)
    assert discharged.state == "verified"
    assert discharged.verified_certificate is not None
    assert discharged.verified_certificate.conclusion == conclusion
    assert discharged.verified_certificate.abort_only_guard_tokens == (
        analysis.certificate.abort_only_guard_tokens
    )
    for token in analysis.certificate.abort_only_guard_tokens:
        assert set(asdict(token)) == {
            "source_path",
            "source_span",
            "lexical_scope",
            "call_path_id",
            "guard_ordinal",
            "condition_ast_digest",
            "raise_ast_digest",
            "name_roles",
        }


def test_direct_helper_guard_replays_lexical_and_call_path_identity() -> None:
    source = (
        _source()
        .replace(
            "def main():",
            """def validate_groups(left, right):
    if len(left) < 2 or len(right) < 2:
        raise ValueError("short")

def main():""",
        )
        .replace(
            "    result = stats.ttest_ind(left, right)",
            "    validate_groups(left, right)\n    result = stats.ttest_ind(left, right)",
        )
    )
    context = _context(source, _ADVERSE)
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    assert len(analysis.certificate.abort_only_guard_tokens) == 1
    token = analysis.certificate.abort_only_guard_tokens[0]
    assert token.lexical_scope == "validate_groups"
    assert token.call_path_id.startswith("inline-call-path:main:")
    assert "/validate_groups:" in token.call_path_id
    discharged = discharge_dependence_growth_analysis(analysis, context)
    assert discharged.verified_certificate is not None
    assert discharged.verified_certificate.conclusion == "repeated_units"


def test_direct_module_guard_is_syntax_only_when_existing_module_wall_precedes() -> None:
    function_source = _source(
        """if len(left) < 2:
    raise ValueError("short")"""
    )
    prefix, remainder = function_source.split("def main():\n", 1)
    body, suffix = remainder.rsplit("\nmain()\n", 1)
    assert suffix == ""
    source = prefix + textwrap.dedent(body) + "\n"
    assert not _analyzer_abort_only_raise_wall(ast.parse(source))
    analysis = analyze_dependence_growth_python(_context(source, _ADVERSE))
    assert analysis.certificate is None
    assert analysis.abstention_reasons == ("module-constant-not-closed",)


def test_structural_source_order_and_inventory_siblings_remain_unmodeled() -> None:
    helper = _source().replace(
        "def main():",
        """def validate_groups(left):
    if len(left) < 2:
        raise ValueError("short")

def main():""",
    )
    variants = {
        "two-body": _source(
            """if len(left) < 2:
    raise ValueError("short")
    pass"""
        ),
        "else": _source(
            """if len(left) < 2:
    raise ValueError("short")
else:
    pass"""
        ),
        "elif": _source(
            """if len(left) < 2:
    raise ValueError("short")
elif len(right) < 2:
    raise ValueError("short right")"""
        ),
        "cause": _source(
            """if len(left) < 2:
    raise ValueError("short") from RuntimeError("cause")"""
        ),
        "unconditional": _source('raise ValueError("stop")'),
        "nested-if": _source(
            """if True:
    if len(left) < 2:
        raise ValueError("short")"""
        ),
        "loop": _source(
            """for item in left:
    if len(left) < 2:
        raise ValueError("short")"""
        ),
        "try": _source(
            """try:
    if len(left) < 2:
        raise ValueError("short")
except ValueError:
    pass"""
        ),
        "with": _source(
            """with INPUT.open(encoding="ascii") as other:
    if len(left) < 2:
        raise ValueError("short")"""
        ),
        "dynamic-message": _source(
            """if len(left) < 2:
    raise ValueError(make_message())"""
        ),
        "mixed": _source(
            """if len(left) < 2:
    raise ValueError("short")
if left in groups:
    raise ValueError("membership")"""
        ),
        "caught-helper": helper.replace(
            "    result = stats.ttest_ind(left, right)",
            """    try:
        validate_groups(left)
    except ValueError:
        pass
    result = stats.ttest_ind(left, right)""",
        ),
        "post-sink": _source().replace(
            '    REPORT.write_text(str(result), encoding="utf-8")',
            """    REPORT.write_text(str(result), encoding="utf-8")
    if len(left) < 2:
        raise ValueError("short")""",
        ),
        "unknown-match-shape": _source(
            """match len(left):
    case 0:
        raise ValueError("short")"""
        ),
    }
    for label, source in variants.items():
        analysis = analyze_dependence_growth_python(_context(source, _ADVERSE))
        assert analysis.certificate is None, label
        assert "raise-guard-not-modeled" in analysis.abstention_reasons, (
            label,
            analysis.abstention_reasons,
        )


def test_attempt3_true_guard_uses_replayed_1_4_fact_and_returns_only_control_reason() -> None:
    source = _source(
        """if len(left) < 2 or len(right) < 2:
    raise ValueError("short group")"""
    )
    context = _context(source, _ATTEMPT3)
    analysis = analyze_dependence_growth_python(context)
    assert analysis.certificate is not None and analysis.obligation is not None
    fact = _fact(context, cast(GroupValueSequenceObligation, analysis.obligation))
    assert tuple(len(item.row_indices) for item in fact.groups) == (1, 4)
    discharged = discharge_dependence_growth_analysis(analysis, context)
    assert discharged.verified_certificate is None
    assert discharged.abstention_reasons == ("sink-controls-operand-flow",)


def test_valid_row_sequence_lencompare_true_guard_returns_only_control_reason() -> None:
    context = _context(
        _source(
            """if len(rows) != 2:
    raise SystemExit("wrong row count")"""
        ),
        _ADVERSE,
    )
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    role = analysis.certificate.abort_only_guard_tokens[0].name_roles
    assert [(item.name, item.role_kind, item.operand_position) for item in role] == [
        ("__dependence_v2_1_rows", "row_sequence", None)
    ]
    discharged = discharge_dependence_growth_analysis(analysis, context)
    assert discharged.verified_certificate is None
    assert discharged.abstention_reasons == ("sink-controls-operand-flow",)


def test_multiple_true_guards_collapse_to_one_control_reason() -> None:
    context = _context(
        _source(
            """if len(left) < 2:
    raise ValueError("short group")
if len(rows) != 2:
    raise SystemExit("wrong row count")"""
        ),
        _ATTEMPT3,
    )
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    assert len(analysis.certificate.abort_only_guard_tokens) == 2
    discharged = discharge_dependence_growth_analysis(analysis, context)
    assert discharged.verified_certificate is None
    assert discharged.abstention_reasons == ("sink-controls-operand-flow",)


def test_kernel_returns_a_distinct_replayed_fact_object() -> None:
    context = _context(_source(), _ADVERSE)
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    fact = _fact(context, analysis.certificate.obligation)
    certificate = _final_certificate(analysis.certificate, fact)
    verified, failures = _verify(certificate, fact, context)
    assert failures == []
    assert verified is not None
    returned_fact = cast(Any, verified).fact
    assert returned_fact == fact
    assert returned_fact is not fact


def test_certificate_identity_is_bound_to_the_complete_guard_tuple() -> None:
    context = _context(
        _source(
            """if len(left) < 2:
    raise ValueError("short")"""
        ),
        _ADVERSE,
    )
    analysis = analyze_dependence_growth_python(context)
    discharged = discharge_dependence_growth_analysis(analysis, context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    assert discharged.verified_certificate is not None
    fact = discharged.verified_certificate.fact
    old_identity = "dependence-growth-certificate:" + semantic_digest(
        {
            "source_digest": analysis.certificate.source_digest,
            "fact": fact.evidence_id,
            "bindings": [asdict(item) for item in discharged.verified_certificate.operand_bindings],
            "conclusion": discharged.verified_certificate.conclusion,
        }
    )
    certificate = replace(
        analysis.certificate,
        certificate_id=old_identity,
        operand_bindings=discharged.verified_certificate.operand_bindings,
        conclusion=discharged.verified_certificate.conclusion,
    )
    verified, failures = _verify(certificate, fact, context)
    assert verified is None
    assert failures == ["certificate-identity"]


def _move_parallel_tuple(
    fact: GroupValueSequenceFact, source_index: int, destination_index: int
) -> GroupValueSequenceFact:
    source = fact.groups[source_index]
    destination = fact.groups[destination_index]
    moved = tuple(
        values[0]
        for values in (
            source.row_indices,
            source.observation_ids,
            source.authorized_unit_ids,
            source.source_values,
            source.cast_value_reprs,
        )
    )
    shortened = replace(
        source,
        row_indices=source.row_indices[1:],
        observation_ids=source.observation_ids[1:],
        authorized_unit_ids=source.authorized_unit_ids[1:],
        source_values=source.source_values[1:],
        cast_value_reprs=source.cast_value_reprs[1:],
    )
    extended = replace(
        destination,
        row_indices=(*destination.row_indices, cast(int, moved[0])),
        observation_ids=(*destination.observation_ids, cast(str, moved[1])),
        authorized_unit_ids=(*destination.authorized_unit_ids, cast(str, moved[2])),
        source_values=(*destination.source_values, cast(str, moved[3])),
        cast_value_reprs=(*destination.cast_value_reprs, cast(str, moved[4])),
    )
    groups = list(fact.groups)
    groups[source_index] = shortened
    groups[destination_index] = extended
    return replace(fact, groups=tuple(groups))


def _parallel_tuple(group: GroupValueSequence, index: int) -> tuple[int, str, str, str, str]:
    return (
        group.row_indices[index],
        group.observation_ids[index],
        group.authorized_unit_ids[index],
        group.source_values[index],
        group.cast_value_reprs[index],
    )


def _group_from_parallel_tuples(
    group: GroupValueSequence, values: list[tuple[int, str, str, str, str]]
) -> GroupValueSequence:
    return replace(
        group,
        row_indices=tuple(item[0] for item in values),
        observation_ids=tuple(item[1] for item in values),
        authorized_unit_ids=tuple(item[2] for item in values),
        source_values=tuple(item[3] for item in values),
        cast_value_reprs=tuple(item[4] for item in values),
    )


def test_exact_attempt3_1_4_to_2_3_supplied_tuple_move_closes_at_fact_closure() -> None:
    source = _source(
        """if len(left) < 2 or len(right) < 2:
    raise ValueError("short group")"""
    )
    context = _context(source, _ATTEMPT3)
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    authentic = _fact(context, analysis.certificate.obligation)
    moved = _move_parallel_tuple(authentic, 1, 0)
    assert tuple(len(item.row_indices) for item in authentic.groups) == (1, 4)
    assert tuple(len(item.row_indices) for item in moved.groups) == (2, 3)
    assert _conclusion(authentic) == _conclusion(moved) == "repeated_units"
    certificate = _final_certificate(analysis.certificate, moved)
    verified, failures = _verify(certificate, moved, context)
    assert verified is None
    assert failures == ["fact-closure"]


def test_every_group_fact_top_level_and_nested_field_is_closed_by_replay() -> None:
    context = _context(_source(), _ADVERSE)
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    fact = _fact(context, analysis.certificate.obligation)
    certificate = _final_certificate(analysis.certificate, fact)
    first = fact.groups[0]
    top_level = {
        "evidence_id": replace(fact, evidence_id="other"),
        "path": replace(fact, path="other.csv"),
        "content_digest": replace(fact, content_digest="sha256:" + "0" * 64),
        "file_ref": replace(fact, file_ref=RecordRef("file_record", "other")),
        "asset_identity_ref": replace(
            fact, asset_identity_ref=RecordRef("asset_identity", "other")
        ),
        "line_model": replace(fact, line_model="splitlines"),
        "reader_form": replace(fact, reader_form="csv_dictreader_splitlines"),
        "encoding": replace(fact, encoding="utf-8"),
        "ascii_bytes_proven": replace(fact, ascii_bytes_proven=False),
        "header": replace(fact, header=(*fact.header, "extra")),
        "authorized_unit_column": replace(fact, authorized_unit_column="other_unit"),
        "group_key_column": replace(fact, group_key_column="other_group"),
        "value_column": replace(fact, value_column="other_value"),
        "cast_kind": replace(fact, cast_kind="int"),
        "row_count": replace(fact, row_count=fact.row_count + 1),
        "groups": replace(fact, groups=tuple(reversed(fact.groups))),
        "predeclared_bucket_keys": replace(fact, predeclared_bucket_keys=("A", "B")),
    }
    nested = {
        "group_key": replace(first, group_key="Z"),
        "row_indices": replace(first, row_indices=tuple(reversed(first.row_indices))),
        "observation_ids": replace(first, observation_ids=tuple(reversed(first.observation_ids))),
        "authorized_unit_ids": replace(
            first,
            authorized_unit_ids=("other-unit", *first.authorized_unit_ids[1:]),
        ),
        "source_values": replace(first, source_values=tuple(reversed(first.source_values))),
        "cast_value_reprs": replace(
            first, cast_value_reprs=tuple(reversed(first.cast_value_reprs))
        ),
    }
    mutations = dict(top_level)
    mutations.update(
        {
            f"nested-{name}": replace(fact, groups=(group, *fact.groups[1:]))
            for name, group in nested.items()
        }
    )
    mutations.update(
        {
            "group-omission": replace(fact, groups=fact.groups[:1]),
            "group-duplication": replace(fact, groups=(*fact.groups, fact.groups[0])),
            "tuple-omission": replace(
                fact,
                groups=(replace(first, source_values=first.source_values[:-1]), *fact.groups[1:]),
            ),
            "cross-field-substitution": replace(
                fact,
                groups=(
                    replace(first, observation_ids=first.authorized_unit_ids),
                    *fact.groups[1:],
                ),
            ),
        }
    )
    left, right = fact.groups
    left_tuples = [_parallel_tuple(left, index) for index in range(len(left.row_indices))]
    right_tuples = [_parallel_tuple(right, index) for index in range(len(right.row_indices))]
    swapped_left = list(left_tuples)
    swapped_right = list(right_tuples)
    swapped_left[0], swapped_right[-1] = swapped_right[-1], swapped_left[0]
    mutations.update(
        {
            "cardinality-preserving-cross-group-swap": replace(
                fact,
                groups=(
                    _group_from_parallel_tuples(left, swapped_left),
                    _group_from_parallel_tuples(right, swapped_right),
                ),
            ),
            "row-tuple-reordering": replace(
                fact,
                groups=(left, _group_from_parallel_tuples(right, list(reversed(right_tuples)))),
            ),
            "complete-tuple-duplication": replace(
                fact,
                groups=(
                    left,
                    _group_from_parallel_tuples(right, [*right_tuples, right_tuples[-1]]),
                ),
            ),
        }
    )
    for name, mutation in mutations.items():
        verified, failures = _verify(certificate, mutation, context)
        assert verified is None, name
        assert failures == ["fact-closure"], name


def test_material_omission_duplication_binding_bytes_and_refs_close() -> None:
    context = _context(_source(), _ADVERSE)
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    fact = _fact(context, analysis.certificate.obligation)
    certificate = _final_certificate(analysis.certificate, fact)
    material = _data_material(context)
    material_envelopes = {"missing-material": (), "duplicate-material": (material, material)}
    for name, materials in material_envelopes.items():
        verified, failures = _verify(certificate, fact, context, materials=materials)
        assert verified is None, name
        assert failures == ["envelope-binding"], name
    fact_envelopes = {"missing-fact": (), "duplicate-fact": (fact, fact)}
    for name, facts in fact_envelopes.items():
        verified, failures = _verify(certificate, fact, context, facts=facts)
        assert verified is None, name
        assert failures == ["envelope-binding"], name
    changed_bytes = material.content + b"\n"
    fact_cases = {
        "path": replace(material, path="other.csv"),
        "bytes-and-declared-digest": replace(
            material,
            content=changed_bytes,
            content_digest=sha256_digest(changed_bytes),
        ),
        "file-ref": replace(material, file_ref=RecordRef("file_record", "other")),
        "asset-ref": replace(material, asset_identity_ref=RecordRef("asset_identity", "other")),
    }
    for name, mutation in fact_cases.items():
        verified, failures = _verify(certificate, fact, context, materials=(mutation,))
        assert verified is None, name
        assert failures == ["fact-closure"], name


def test_context_rejects_material_reference_substitution_before_selection() -> None:
    context = _context(_source(), _ADVERSE)
    material = _data_material(context)
    substituted = replace(
        material,
        file_ref=RecordRef("file_record", "file:substituted"),
        asset_identity_ref=RecordRef("asset_identity", "asset:substituted"),
    )
    remaining = tuple(item for item in context.material_inputs if item is not material)
    with pytest.raises(
        ScientificCheckContractError,
        match="inspection material input is not an admitted regular file",
    ):
        replace(context, material_inputs=(substituted, *remaining))


def test_coordinated_recomputed_material_digest_still_requires_original_authority() -> None:
    context = _context(_source(), _ADVERSE)
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    authentic_material = _data_material(context)
    changed_bytes = authentic_material.content + b"u9,B,9\n"
    changed_material = replace(
        authentic_material,
        content=changed_bytes,
        content_digest=sha256_digest(changed_bytes),
    )
    changed_obligation = replace(
        analysis.certificate.obligation,
        content_digest=changed_material.content_digest,
    )
    changed_fact, reason = prove_group_value_sequences_with_reason(
        changed_material, obligation=changed_obligation
    )
    assert reason is None and changed_fact is not None
    certificate = _final_certificate(
        replace(analysis.certificate, obligation=changed_obligation), changed_fact
    )
    verified, failures = _verify(
        certificate,
        changed_fact,
        context,
        materials=(changed_material,),
    )
    assert verified is None
    assert failures == ["authority-binding"]


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"unit_id,arm,value\n", "group-domain-unproven"),
        (b"unit_id,arm,value\nu1,A,1\nu2,A,2\n", "group-operand-arity-mismatch"),
        (
            b"unit_id,arm,value\nu1,A,1\nu2,B,2\nu3,C,3\n",
            "group-operand-arity-mismatch",
        ),
    ],
)
def test_fact_and_domain_refusals_precede_guard_truth(data: bytes, expected: str) -> None:
    source = _source(
        """if len(left) < 2 or len(right) < 2:
    raise ValueError("short")"""
    )
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(source, data))
    assert payload["abstention_reasons"] == [expected]
    assert "sink-controls-operand-flow" not in payload["abstention_reasons"]


def test_unpopulated_predeclared_bucket_precedes_guard_truth() -> None:
    source = _source(
        """if len(left) < 2 or len(right) < 2:
    raise ValueError("short")""",
        predeclared=True,
    )
    data = b"unit_id,arm,value\nu1,A,1\nu2,A,2\n"
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(source, data))
    assert payload["abstention_reasons"] == ["group-bucket-unpopulated"]


def test_notname_is_syntax_only_and_never_creates_a_token() -> None:
    guarded = _source(
        """if not left or not right:
    raise ValueError("empty")"""
    )
    analysis = analyze_dependence_growth_python(_context(guarded, _ADVERSE))
    assert analysis.certificate is None
    assert analysis.abstention_reasons == ("raise-guard-not-modeled",)

    downstream_wall = guarded.replace(
        "    result = stats.ttest_ind(left, right)",
        "    total = 0\n    total += len(left)\n    result = stats.ttest_ind(left, right)",
    )
    decomposed = analyze_dependence_growth_python(_context(downstream_wall, _ADVERSE))
    assert decomposed.certificate is None
    assert decomposed.abstention_reasons == ("augmented-assignment-not-modeled",)


@pytest.mark.parametrize("wrapper", ["array", "asarray"])
def test_numpy_notname_reviewer_counterexample_remains_full_path_unmodeled(
    wrapper: str,
) -> None:
    baseline = _source(operand_form=wrapper)
    assert (
        DependenceRecognitionV2ShadowAdapter().inspect(_context(baseline, _ADVERSE))["outcome"]
        == "evaluation_candidate"
    )
    guarded = _source(
        """if not left or not right:
    raise ValueError("empty")""",
        operand_form=wrapper,
    )
    analysis = analyze_dependence_growth_python(_context(guarded, _ADVERSE))
    assert analysis.certificate is None
    assert analysis.abstention_reasons == ("raise-guard-not-modeled",)


def test_all_former_notname_provenances_remain_without_full_authority() -> None:
    guard = """if not left or not right:
    raise ValueError("empty")"""
    baseline = _source(guard)
    truth_class = """class TruthWrapper:
    def __init__(self, value):
        self.value = value

    def __bool__(self):
        return bool(self.value)

"""
    length_class = """class LengthWrapper:
    def __init__(self, value):
        self.value = value

    def __len__(self):
        return len(self.value)

"""
    sources = {
        "row-list": _source(
            """if not rows:
    raise ValueError("empty")"""
        ),
        "group-dict": _source(
            """if not groups:
    raise ValueError("empty")"""
        ),
        "group-subscript-alias": baseline,
        "plain-alias": baseline.replace(
            "    left = groups[LEFT]", "    raw_left = groups[LEFT]\n    left = raw_left"
        ),
        "mapping-get": baseline.replace(
            "    left = groups[LEFT]", "    left = groups.get(LEFT, [])"
        ),
        "numpy-array": _source(guard, operand_form="array"),
        "numpy-asarray": _source(guard, operand_form="asarray"),
        "unenumerated-wrapper": baseline.replace(
            "    left = groups[LEFT]", "    left = tuple(groups[LEFT])"
        ),
        "custom-bool": truth_class
        + baseline.replace("    left = groups[LEFT]", "    left = TruthWrapper(groups[LEFT])"),
        "custom-len-truth": length_class
        + baseline.replace("    left = groups[LEFT]", "    left = LengthWrapper(groups[LEFT])"),
    }
    for label, source in sources.items():
        analysis = analyze_dependence_growth_python(_context(source, _ADVERSE))
        assert analysis.certificate is None, label
        assert analysis.state == "unsupported", label


def test_runtime_false_and_true_builtin_notname_are_control_flow_only(
    tmp_path: Path,
) -> None:
    guard = """if not left or not right:
    raise ValueError("empty")"""
    false = _run_instrumented(_source(guard), _ADVERSE, tmp_path)
    true_data = b"unit_id,arm,value\nu1,A,1\nu2,A,2\n"
    true = _run_instrumented(_source(guard, predeclared=True), true_data, tmp_path)
    assert false["error"] is None and false["report"] is True
    assert len(cast(list[object], false["calls"])) == 1
    assert true["error"] == "ValueError:empty"
    assert true["calls"] == [] and true["report"] is False


@pytest.mark.parametrize(
    "condition",
    [
        "len(left) < 1",
        "len(left) <= 2",
        "2 > len(left)",
        "len(left) == 2",
        "len(left) < 2 and len(right) < 2",
        "left",
        "left in groups",
        "len(set(left)) < 2",
        "len(holder.left) < 2",
        "len(groups['A']) < 2",
        "size(left) < 2",
        "(value := len(left)) < 2",
        "len([item for item in left]) < 2",
    ],
)
def test_condition_siblings_are_outside_the_exact_full_and_standalone_grammar(
    condition: str,
) -> None:
    statement = ast.parse(f"if {condition}:\n    raise ValueError('invalid')\n").body[0]
    assert not _analyzer_abort_only_guard_statement(statement, allow_not_name=True)


@pytest.mark.parametrize(
    "snippet",
    [
        "len = list",
        "len: object = list",
        "len += 1",
        "len, *rest = values",
        "(len := list)",
        "for len in values:\n    pass",
        "with manager() as len:\n    pass",
        "try:\n    pass\nexcept Exception as len:\n    pass",
        "[item for len in values]",
        "global len",
        "nonlocal len",
        "match values:\n    case [*len]:\n        pass",
        "del len",
    ],
)
def test_function_scope_len_binding_siblings_are_syntax_unmodeled(snippet: str) -> None:
    source = (
        "def main():\n"
        "    values = []\n"
        + textwrap.indent(snippet, "    ")
        + """
    if len(values) < 2:
        raise ValueError("short")

main()
"""
    )
    assert _analyzer_abort_only_raise_wall(ast.parse(source))


@pytest.mark.parametrize(
    "source",
    [
        """def len(value):
    return 3

def main():
    values = []
    if len(values) < 2:
        raise ValueError("short")

main()
""",
        """def main(len):
    values = []
    if len(values) < 2:
        raise ValueError("short")

main(list)
""",
        """def main(len, /):
    values = []
    if len(values) < 2:
        raise ValueError("short")

main(list)
""",
        """def main(*, len):
    values = []
    if len(values) < 2:
        raise ValueError("short")

main(len=list)
""",
        """def main(*len):
    values = []
    if len(values) < 2:
        raise ValueError("short")

main()
""",
        """def main(**len):
    values = []
    if len(values) < 2:
        raise ValueError("short")

main()
""",
        """class len:
    pass

def main():
    values = []
    if len(values) < 2:
        raise ValueError("short")

main()
""",
        """import builtins as len

def main():
    values = []
    if len(values) < 2:
        raise ValueError("short")

main()
""",
    ],
)
def test_module_helper_parameter_class_and_import_named_len_are_unmodeled(source: str) -> None:
    assert _analyzer_abort_only_raise_wall(ast.parse(source))


def test_real_builtin_len_binding_is_enforced_on_full_analyzer_paths() -> None:
    guard = """if len(left) < 2:
    raise ValueError("short")"""
    baseline = _source(guard)
    sources = {
        "module-helper": baseline.replace(
            "def main():", "def len(value):\n    return 3\n\ndef main():"
        ),
        "parameter": baseline.replace("def main():", "def main(len):").replace(
            "main()", "main(list)"
        ),
        "assignment": baseline.replace(
            "    left = groups[LEFT]", "    len = list\n    left = groups[LEFT]"
        ),
        "comprehension-target": baseline.replace(
            "    left = groups[LEFT]",
            "    ignored = [item for len in rows]\n    left = groups[LEFT]",
        ),
        "import": baseline.replace("import csv", "import csv\nimport builtins as len"),
    }
    for label, source in sources.items():
        analysis = analyze_dependence_growth_python(_context(source, _ADVERSE))
        assert analysis.certificate is None, label
        if label != "import":
            assert "raise-guard-not-modeled" in analysis.abstention_reasons, label
        else:
            assert analysis.abstention_reasons == ("unsupported-import-form",)


def test_guard_token_field_omit_add_reorder_and_role_mutations_refuse_source_replay() -> None:
    guards = """if len(left) < 2 or len(right) < 2:
    raise ValueError("short")
if len(groups) != 2:
    raise SystemExit("groups")"""
    context = _context(_source(guards), _ADVERSE)
    analysis = analyze_dependence_growth_python(context)
    discharged = discharge_dependence_growth_analysis(analysis, context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    assert discharged.verified_certificate is not None
    fact = discharged.verified_certificate.fact
    certificate = replace(
        analysis.certificate,
        certificate_id=discharged.verified_certificate.certificate_id,
        operand_bindings=discharged.verified_certificate.operand_bindings,
        conclusion=discharged.verified_certificate.conclusion,
    )
    first, second = certificate.abort_only_guard_tokens
    role = first.name_roles[0]
    mutations = {
        "path": replace(first, source_path="other.py"),
        "span": replace(first, source_span=(0, 0, 0, 0)),
        "scope": replace(first, lexical_scope="other"),
        "call-path": replace(first, call_path_id="other"),
        "ordinal": replace(first, guard_ordinal=99),
        "condition": replace(first, condition_ast_digest="sha256:" + "0" * 64),
        "raise": replace(first, raise_ast_digest="sha256:" + "0" * 64),
        "role-name": replace(
            first, name_roles=(replace(role, name="other"), *first.name_roles[1:])
        ),
        "role-kind": replace(
            first,
            name_roles=(replace(role, role_kind="group_container"), *first.name_roles[1:]),
        ),
        "role-position": replace(
            first, name_roles=(replace(role, operand_position=1), *first.name_roles[1:])
        ),
        "role-omit": replace(first, name_roles=first.name_roles[1:]),
        "role-duplicate": replace(first, name_roles=(*first.name_roles, role)),
        "role-reorder": replace(first, name_roles=tuple(reversed(first.name_roles))),
    }
    certificate_mutations = {
        name: replace(certificate, abort_only_guard_tokens=(token, second))
        for name, token in mutations.items()
    }
    certificate_mutations.update(
        {
            "omit": replace(certificate, abort_only_guard_tokens=(first,)),
            "add": replace(certificate, abort_only_guard_tokens=(first, second, second)),
            "reorder": replace(certificate, abort_only_guard_tokens=(second, first)),
        }
    )
    for name, mutation in certificate_mutations.items():
        verified, failures = _verify(mutation, fact, context)
        assert verified is None, name
        assert failures == ["source-semantic-replay"], name


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("len(left) < 2", "len(left) != 2"),
        ("len(left) < 2", "len(right) < 2"),
        ("short", "changed"),
        ("len(right) < 2", "len(right) < 3"),
        ('ValueError("short")', 'SystemExit("short")'),
        ("left = groups[LEFT]", "left = groups[RIGHT]"),
    ],
)
def test_source_condition_name_operator_literal_and_message_mutations_refuse_replay(
    old: str, new: str
) -> None:
    source = _source(
        """if len(left) < 2 or len(right) < 2:
    raise ValueError("short")"""
    )
    context = _context(source, _ADVERSE)
    analysis = analyze_dependence_growth_python(context)
    discharged = discharge_dependence_growth_analysis(analysis, context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    assert discharged.verified_certificate is not None
    certificate = replace(
        analysis.certificate,
        certificate_id=discharged.verified_certificate.certificate_id,
        operand_bindings=discharged.verified_certificate.operand_bindings,
        conclusion=discharged.verified_certificate.conclusion,
    )
    mutated_source = source.replace(old, new)
    mutated_context = _context(mutated_source, _ADVERSE)
    mutated = replace(
        certificate,
        source_digest=mutated_context.documents[0].content_digest,
        source_extent=(0, len(mutated_context.documents[0].content)),
        analysis_target_ref=_trusted_v2_authorizations(mutated_context)[0].analysis_target_ref,
        procedure_ref=_trusted_v2_authorizations(mutated_context)[0].procedure_ref,
        authority_record_id=_trusted_v2_authorizations(mutated_context)[0].record_id,
    )
    fact = _fact(mutated_context, mutated.obligation)
    verified, failures = _verify(mutated, fact, mutated_context)
    assert verified is None
    assert failures == ["source-semantic-replay"]


def _retarget_certificate_source(
    certificate: DependenceGrowthCertificate, context: FrozenInspectionContext
) -> DependenceGrowthCertificate:
    authority = _trusted_v2_authorizations(context)[0]
    document = context.documents[0]
    return replace(
        certificate,
        source_digest=document.content_digest,
        source_extent=(0, len(document.content)),
        analysis_target_ref=authority.analysis_target_ref,
        procedure_ref=authority.procedure_ref,
        authority_record_id=authority.record_id,
    )


def test_caught_nested_shadowed_and_post_sink_analyzer_bypasses_refuse_source_replay() -> None:
    guard = """if len(left) < 2:
    raise ValueError("short")"""
    source = _source(guard)
    base_context = _context(source, _ADVERSE)
    analysis = analyze_dependence_growth_python(base_context)
    discharged = discharge_dependence_growth_analysis(analysis, base_context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    assert discharged.verified_certificate is not None
    certificate = replace(
        analysis.certificate,
        certificate_id=discharged.verified_certificate.certificate_id,
        operand_bindings=discharged.verified_certificate.operand_bindings,
        conclusion=discharged.verified_certificate.conclusion,
    )
    helper = _source().replace(
        "def main():",
        """def validate_groups(left):
    if len(left) < 2:
        raise ValueError("short")

def main():""",
    )
    variants = {
        "shadowed": source.replace("from pathlib", "len = list\nfrom pathlib"),
        "nested": _source(
            """if True:
    if len(left) < 2:
        raise ValueError("short")"""
        ),
        "caught": helper.replace(
            "    result = stats.ttest_ind(left, right)",
            """    try:
        validate_groups(left)
    except ValueError:
        pass
    result = stats.ttest_ind(left, right)""",
        ),
        "post-sink": _source().replace(
            '    REPORT.write_text(str(result), encoding="utf-8")',
            """    REPORT.write_text(str(result), encoding="utf-8")
    if len(left) < 2:
        raise ValueError("short")""",
        ),
    }
    for label, mutated_source in variants.items():
        context = _context(mutated_source, _ADVERSE)
        mutation = _retarget_certificate_source(certificate, context)
        fact = _fact(context, mutation.obligation)
        verified, failures = _verify(mutation, fact, context)
        assert verified is None, label
        assert failures == ["source-semantic-replay"], label


def test_analyzer_guard_collector_bypass_cannot_authorize_notname(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valid_context = _context(
        _source(
            """if len(left) < 2 or len(right) < 2:
    raise ValueError("short")"""
        ),
        _ADVERSE,
    )
    valid = analyze_dependence_growth_python(valid_context)
    assert isinstance(valid.certificate, DependenceGrowthCertificate)
    forged_tokens = valid.certificate.abort_only_guard_tokens
    notname = _source(
        """if not left or not right:
    raise ValueError("empty")"""
    )
    context = _context(notname, _ADVERSE)
    monkeypatch.setattr(
        "sc_referee.dependence_recognition_v2.python_analyzer._collect_full_abort_only_guard_tokens",
        lambda *_args, **_kwargs: forged_tokens,
    )
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    discharged = discharge_dependence_growth_analysis(analysis, context)
    assert discharged.verified_certificate is None
    assert discharged.abstention_reasons == ("certificate-kernel-refusal:source-semantic-replay",)


def test_standalone_collector_bypass_cannot_reach_certificate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source(
        """if left in groups:
    raise ValueError("membership")"""
    )
    monkeypatch.setattr(
        "sc_referee.dependence_recognition_v2.python_analyzer._analyzer_abort_only_raise_wall",
        lambda _tree: False,
    )
    analysis = analyze_dependence_growth_python(_context(source, _ADVERSE))
    assert analysis.certificate is None
    assert analysis.state == "unsupported"


@pytest.mark.parametrize(
    ("line_model", "cast_kind", "predeclared", "operand_form"),
    [
        ("csv_newline", "float", False, "aliases"),
        ("csv_newline", "float", False, "direct"),
        ("csv_newline", "float", False, "sorted"),
        ("csv_newline", "float", False, "array"),
        ("csv_newline", "float", False, "asarray"),
        ("splitlines", "float", False, "aliases"),
        ("csv_newline", "int", False, "aliases"),
        ("csv_newline", "float", True, "aliases"),
    ],
)
@pytest.mark.parametrize(
    ("data", "conclusion"),
    [(_ADVERSE, "repeated_units"), (_COVERED, "one_observation_per_unit")],
)
def test_controller_and_kernel_fact_parity_across_supported_forms(
    line_model: str,
    cast_kind: str,
    predeclared: bool,
    operand_form: str,
    data: bytes,
    conclusion: str,
) -> None:
    source = _source(
        line_model=line_model,
        cast_kind=cast_kind,
        predeclared=predeclared,
        operand_form=operand_form,
    )
    context = _context(source, data)
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    controller = _fact(context, analysis.certificate.obligation)
    replayed = _kernel_replay_group_fact(_data_material(context), analysis.certificate.obligation)
    assert replayed == controller
    discharged = discharge_dependence_growth_analysis(analysis, context)
    assert discharged.verified_certificate is not None
    assert discharged.verified_certificate.conclusion == conclusion


def test_deterministic_byte_domain_parity_fuzz() -> None:
    rng = random.Random(150016)
    for index in range(300):
        line_model = rng.choice(("csv_newline", "splitlines"))
        cast_kind = rng.choice(("float", "int", "none"))
        encoding = rng.choice(("ascii", "utf-8", "latin-1"))
        header = rng.choice(
            (
                ("unit_id", "arm", "value"),
                ("unit_id", "arm", "value", "extra"),
                ("unit_id", "arm", "arm"),
                ("unit_id", "", "value"),
            )
        )
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator=rng.choice(("\n", "\r\n")))
        writer.writerow(header)
        alphabet = ("A", "B", "C", "", "Å", "x,y", 'q"z')
        for _row in range(rng.randrange(0, 12)):
            row = [
                rng.choice((f"u{rng.randrange(5)}", "")),
                rng.choice(alphabet),
                rng.choice((str(rng.randrange(-3, 6)), "1.5", "nan", "bad", "")),
            ]
            if len(header) == 4:
                row.append(rng.choice(alphabet))
            if rng.random() < 0.08:
                row.append("ragged")
            writer.writerow(row)
        data = output.getvalue().encode("utf-8")
        if rng.random() < 0.04:
            data = b"\xef\xbb\xbf" + data
        material = _domain_material(data, suffix=f"fuzz:{index}")
        obligation = _domain_obligation(
            material,
            line_model=line_model,
            encoding=encoding,
            cast_kind=cast_kind,
            predeclared_bucket_keys=rng.choice(((), ("A", "B"), ("A", "B", "C"))),
        )
        controller, _reason = prove_group_value_sequences_with_reason(
            material, obligation=obligation
        )
        assert _kernel_replay_group_fact(material, obligation) == controller, index


def _domain_material(
    content: bytes, *, path: str = _DATA_PATH, suffix: str = "domain"
) -> FrozenMaterialInput:
    return FrozenMaterialInput(
        path,
        RecordRef("file_record", f"file:{suffix}"),
        RecordRef("asset_identity", f"asset:{suffix}"),
        content,
        sha256_digest(content),
    )


def _domain_obligation(
    material: FrozenMaterialInput,
    *,
    line_model: str = "csv_newline",
    encoding: str = "ascii",
    cast_kind: str = "float",
    authorized_unit_column: str = "unit_id",
    group_key_column: str = "arm",
    value_column: str = "value",
    predeclared_bucket_keys: tuple[str, ...] = (),
) -> GroupValueSequenceObligation:
    return GroupValueSequenceObligation(
        path=material.path,
        content_digest=material.content_digest,
        line_model=line_model,
        reader_form=(
            "csv_dictreader_file" if line_model == "csv_newline" else "csv_dictreader_splitlines"
        ),
        encoding=encoding,
        authorized_unit_column=authorized_unit_column,
        group_key_column=group_key_column,
        value_column=value_column,
        cast_kind=cast(Any, cast_kind),
        predeclared_bucket_keys=predeclared_bucket_keys,
    )


def test_exact_supported_byte_domain_parity_matrix() -> None:
    cases: list[tuple[str, FrozenMaterialInput, GroupValueSequenceObligation]] = []
    base = b"unit_id,arm,value,extra\nu1,B,01.0,x\nu1,B,-0,y\nu2,A,1e3,z\n"
    for line_model in ("csv_newline", "splitlines"):
        material = _domain_material(base, suffix=f"valid:{line_model}")
        cases.append((line_model, material, _domain_obligation(material, line_model=line_model)))
    integer = _domain_material(
        b"unit_id,arm,value\nu1,B,+01\nu2,A,-0\nu3,A,2\n", suffix="valid:int"
    )
    cases.append(
        (
            "int-predeclared",
            integer,
            _domain_obligation(integer, cast_kind="int", predeclared_bucket_keys=("A", "B")),
        )
    )
    utf8 = _domain_material("unit_id,arm,value\nü1,Å,1.5\nü2,B,2.5\n".encode(), suffix="valid:utf8")
    cases.append(("utf8", utf8, _domain_obligation(utf8, encoding="utf-8")))
    special = _domain_material(
        b"unit_id,arm,value\nu1,A,nan\nu2,A,inf\nu3,B,-inf\nu4,B,-0\n",
        suffix="valid:special",
    )
    cases.append(("float-special", special, _domain_obligation(special)))
    crlf = _domain_material(b"unit_id,arm,value\r\nu1,A,1\r\nu2,B,2\r\n", suffix="valid:crlf")
    cases.append(("crlf", crlf, _domain_obligation(crlf)))
    separator = _domain_material(
        'unit_id,arm,value,extra\nu1,A,1,"x\x85y"\nu2,B,2,z\n'.encode(),
        suffix="valid:separator",
    )
    cases.append(
        ("csv-newline-separator", separator, _domain_obligation(separator, encoding="utf-8"))
    )
    assert len(cases) == 7
    for label, material, obligation in cases:
        controller, reason = prove_group_value_sequences_with_reason(
            material, obligation=obligation
        )
        assert reason is None and controller is not None, label
        assert _kernel_replay_group_fact(material, obligation) == controller, label


def test_exact_refusal_byte_domain_parity_matrix() -> None:
    cases: list[tuple[str, FrozenMaterialInput, GroupValueSequenceObligation, str]] = []

    def add(label: str, content: bytes, reason: str, **updates: object) -> None:
        path = cast(str, updates.pop("path", _DATA_PATH))
        material = _domain_material(content, path=path, suffix=f"invalid:{label}")
        obligation = _domain_obligation(material)
        cases.append((label, material, replace(obligation, **cast(Any, updates)), reason))

    separator = 'unit_id,arm,value,extra\nu1,A,1,"x\x85y"\nu2,B,2,z\n'.encode()
    add("bom", b"\xef\xbb\xbfunit_id,arm,value\nu1,A,1\n", "bom-unsupported", encoding="utf-8")
    add(
        "splitlines-only-separator",
        separator,
        "group-domain-unproven",
        line_model="splitlines",
        reader_form="csv_dictreader_splitlines",
        encoding="utf-8",
    )
    add("malformed-unclosed-quote", b'unit_id,arm,value\n"u1,A,1\n', "ragged-row")
    add("ragged-extra", b"unit_id,arm,value\nu1,A,1,x\n", "ragged-row")
    add("ragged-missing", b"unit_id,arm,value\nu1,A\n", "ragged-row")
    add("empty-domain", b"unit_id,arm,value\n", "group-domain-unproven")
    add("duplicate-header", b"unit_id,arm,arm\nu1,A,1\n", "duplicate-header")
    add("empty-header", b"unit_id,,value\nu1,A,1\n", "group-domain-unproven")
    add("missing-required-header", b"unit_id,arm,other\nu1,A,1\n", "group-domain-unproven")
    add("empty-unit", b"unit_id,arm,value\n,A,1\n", "group-key-or-unit-cell-empty")
    add("empty-group", b"unit_id,arm,value\nu1,,1\n", "group-key-or-unit-cell-empty")
    add("empty-value", b"unit_id,arm,value\nu1,A,\n", "group-value-cast-unproven")
    add("invalid-cast", b"unit_id,arm,value\nu1,A,nope\n", "group-value-cast-unproven")
    add(
        "ascii-nonascii",
        "unit_id,arm,value\nü1,A,1\n".encode(),
        "reader-bytes-not-ascii",
    )
    add(
        "unsupported-encoding",
        b"unit_id,arm,value\nu1,A,1\n",
        "unsupported-reader-encoding",
        encoding="latin-1",
    )
    add(
        "wrong-extension",
        b"unit_id,arm,value\nu1,A,1\n",
        "group-domain-unproven",
        path="inputs/data.txt",
    )
    add(
        "group-equals-value",
        b"unit_id,arm,value\nu1,A,1\n",
        "group-key-equals-value-column",
        value_column="arm",
    )
    add(
        "group-equals-unit",
        b"unit_id,arm,value\nu1,A,1\n",
        "group-key-is-unit-column",
        group_key_column="unit_id",
    )
    add(
        "predeclared-unexpected",
        b"unit_id,arm,value\nu1,A,1\nu2,C,2\n",
        "group-set-not-closed",
        predeclared_bucket_keys=("A", "B"),
    )
    add(
        "predeclared-unpopulated",
        b"unit_id,arm,value\nu1,A,1\n",
        "group-bucket-unpopulated",
        predeclared_bucket_keys=("A", "B"),
    )
    too_many_headers = (
        ",".join(["unit_id", "arm", "value", *[f"c{i}" for i in range(254)]])
        + "\n"
        + ",".join(["u1", "A", "1", *(["x"] * 254)])
        + "\n"
    ).encode()
    assert MAX_DEPENDENCE_CSV_DOMAIN_FIELDS == 256
    add("header-count-overflow", too_many_headers, "group-domain-unproven")
    long_header = b"h" * (MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES + 1)
    add(
        "header-size-overflow",
        b"unit_id,arm,value," + long_header + b"\nu1,A,1,x\n",
        "group-domain-unproven",
    )
    long_field = b"x" * (MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES + 1)
    add(
        "field-size-overflow",
        b"unit_id,arm,value,extra\nu1,A,1," + long_field + b"\n",
        "group-domain-unproven",
    )
    membership_overflow = b"unit_id,arm,value\n" + b"".join(
        f"u{index % 4},{'A' if index % 2 == 0 else 'B'},{index}\n".encode()
        for index in range(MAX_V1_MEMBERSHIPS + 1)
    )
    add("membership-overflow", membership_overflow, "group-domain-unproven")
    row_overflow = b"unit_id,arm,value\n" + b"".join(
        f"u{index % 4},{'A' if index % 2 == 0 else 'B'},1\n".encode()
        for index in range(MAX_DEPENDENCE_CSV_DOMAIN_ROWS + 1)
    )
    add("row-overflow", row_overflow, "group-domain-unproven")
    distinct_overflow = b"unit_id,arm,value\n" + b"".join(
        f"u{index},{'A' if index % 2 == 0 else 'B'},{index}\n".encode() for index in range(5_001)
    )
    add("distinct-unit-overflow", distinct_overflow, "group-domain-unproven")
    group_overflow = b"unit_id,arm,value\n" + b"".join(
        f"u{index},g{index},{index}\n".encode() for index in range(MAX_V2_GROUPS + 1)
    )
    add("group-overflow", group_overflow, "group-operand-arity-mismatch")
    bounded_field = b"x" * MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES
    byte_overflow = b"unit_id,arm,value,extra\n" + b"".join(
        b"u1,A,1," + bounded_field + b"\n" for _index in range(129)
    )
    assert len(byte_overflow) > MAX_DEPENDENCE_CSV_DOMAIN_BYTES
    add("byte-overflow", byte_overflow, "group-domain-unproven")

    assert len(cases) == 28
    for label, material, obligation, expected_reason in cases:
        controller, reason = prove_group_value_sequences_with_reason(
            material, obligation=obligation
        )
        assert controller is None and reason == expected_reason, label
        assert _kernel_replay_group_fact(material, obligation) is None, label


def test_stale_digest_byte_mutation_is_independently_rejected() -> None:
    authentic = _domain_material(b"unit_id,arm,value\nu1,A,1\nu2,B,2\n", suffix="stale:authentic")
    stale = object.__new__(FrozenMaterialInput)
    object.__setattr__(stale, "path", authentic.path)
    object.__setattr__(stale, "file_ref", authentic.file_ref)
    object.__setattr__(stale, "asset_identity_ref", authentic.asset_identity_ref)
    object.__setattr__(stale, "content", authentic.content + b"u3,B,3\n")
    object.__setattr__(stale, "content_digest", authentic.content_digest)
    obligation = _domain_obligation(authentic)
    controller, reason = prove_group_value_sequences_with_reason(stale, obligation=obligation)
    assert controller is None and reason == "group-domain-binding-mismatch"
    assert _kernel_replay_group_fact(stale, obligation) is None


def test_coordinated_reader_form_line_model_encoding_cast_and_keys_cannot_move_source_claim() -> (
    None
):
    data = b"unit_id,arm,value,other\nu1,A,1,11\nu1,A,2,12\nu2,B,3,13\nu3,B,4,14\n"
    context = _context(_source(), data)
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    variants = (
        replace(
            analysis.certificate.obligation,
            reader_form="csv_dictreader_splitlines",
        ),
        replace(
            analysis.certificate.obligation,
            line_model="splitlines",
        ),
        replace(
            analysis.certificate.obligation,
            line_model="splitlines",
            reader_form="csv_dictreader_splitlines",
        ),
        replace(analysis.certificate.obligation, encoding="utf-8"),
        replace(analysis.certificate.obligation, cast_kind="int"),
        replace(analysis.certificate.obligation, group_key_column="other"),
        replace(analysis.certificate.obligation, value_column="other"),
        replace(
            analysis.certificate.obligation,
            predeclared_bucket_keys=("A", "B"),
        ),
    )
    for obligation in variants:
        supplied, reason = prove_group_value_sequences_with_reason(
            _data_material(context), obligation=obligation
        )
        assert reason is None and supplied is not None
        certificate = _final_certificate(
            replace(analysis.certificate, obligation=obligation), supplied
        )
        verified, failures = _verify(certificate, supplied, context)
        assert verified is None, obligation
        assert failures == ["source-semantic-replay"], obligation


def test_controller_selected_material_is_passed_to_kernel_without_replacement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context(_source(), _ADVERSE)
    analysis = analyze_dependence_growth_python(context)
    selected = _data_material(context)
    observed: list[FrozenMaterialInput] = []

    def capture(*_args: object, **kwargs: object) -> None:
        materials = kwargs["trusted_material_inputs"]
        assert isinstance(materials, tuple) and len(materials) == 1
        observed.append(materials[0])
        failures = kwargs["_failure_reasons"]
        assert isinstance(failures, list)
        failures.append("fact-closure")

    monkeypatch.setattr(
        "sc_referee.dependence_recognition_v2.python_analyzer.verify_dependence_growth_certificate",
        capture,
    )
    discharged = discharge_dependence_growth_analysis(analysis, context)
    assert discharged.abstention_reasons == ("certificate-kernel-refusal:fact-closure",)
    assert observed == [selected]
    assert observed[0] is selected


def test_kernel_fact_replay_is_independent_of_controller_fact_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context(_source(), _ADVERSE)
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    material = _data_material(context)
    obligation = analysis.certificate.obligation
    baseline = _kernel_replay_group_fact(material, obligation)
    assert baseline is not None

    def poisoned(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("controller helper reached from certificate kernel")

    monkeypatch.setattr("sc_referee.dependence_recognition_v2.csv_domain._apply_cast", poisoned)
    monkeypatch.setattr(
        "sc_referee.dependence_recognition_v2.csv_domain._parse_unit_key_domain",
        poisoned,
    )
    assert _kernel_replay_group_fact(material, obligation) == baseline


def test_poisoned_controller_fact_builder_cannot_feed_guard_or_conclusion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source(
        """if len(left) < 2 or len(right) < 2:
    raise ValueError("short")"""
    )
    context = _context(source, _ATTEMPT3)
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    authentic = _fact(context, analysis.certificate.obligation)
    forged = _move_parallel_tuple(authentic, 1, 0)
    assert tuple(len(item.row_indices) for item in forged.groups) == (2, 3)
    monkeypatch.setattr(
        "sc_referee.dependence_recognition_v2.python_analyzer."
        "prove_group_value_sequences_with_reason",
        lambda *_args, **_kwargs: (forged, None),
    )
    discharged = discharge_dependence_growth_analysis(analysis, context)
    assert discharged.verified_certificate is None
    assert discharged.abstention_reasons == ("certificate-kernel-refusal:fact-closure",)


def _run_instrumented(source: str, data: bytes, tmp_path: Path) -> dict[str, object]:
    if not _RUNTIME.is_file():
        pytest.fail(f"missing pinned SciPy runtime: {_RUNTIME}")
    case = tmp_path / semantic_digest({"source": source, "data_digest": sha256_digest(data)})[-12:]
    (case / "inputs").mkdir(parents=True)
    (case / "workflow").mkdir()
    (case / "results").mkdir()
    (case / "inputs/data.csv").write_bytes(data)
    (case / "workflow/analysis.py").write_text(source, encoding="utf-8")
    harness = """import json, runpy
import scipy.stats
calls = []
original = scipy.stats.ttest_ind
def tracked(*args, **kwargs):
    calls.append([list(args[0]), list(args[1])])
    return original(*args, **kwargs)
scipy.stats.ttest_ind = tracked
error = None
try:
    runpy.run_path("workflow/analysis.py", run_name="__main__")
except Exception as exc:
    error = type(exc).__name__ + ":" + str(exc)
print(json.dumps({"calls": calls, "error": error,
                  "report": __import__("pathlib").Path("results/report.md").exists()}))
"""
    completed = subprocess.run(
        [str(_RUNTIME), "-I", "-c", harness],
        cwd=case,
        capture_output=True,
        check=False,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    return cast(dict[str, object], json.loads(completed.stdout.strip().splitlines()[-1]))


def test_runtime_false_and_true_len_guards_match_adapter_control_flow(tmp_path: Path) -> None:
    source = _source(
        """if len(left) < 2 or len(right) < 2:
    raise ValueError("short")"""
    )
    false = _run_instrumented(source, _ADVERSE, tmp_path)
    true = _run_instrumented(source, _ATTEMPT3, tmp_path)
    assert false["error"] is None and false["report"] is True
    assert len(cast(list[object], false["calls"])) == 1
    assert true["error"] == "ValueError:short"
    assert true["calls"] == [] and true["report"] is False


def test_runtime_numpy_notname_aborts_before_instrumented_procedure(tmp_path: Path) -> None:
    source = _source(
        """if not left or not right:
    raise ValueError("empty")""",
        operand_form="array",
    )
    runtime = _run_instrumented(source, _ADVERSE, tmp_path)
    assert cast(str, runtime["error"]).startswith("ValueError:The truth value of an array")
    assert runtime["calls"] == [] and runtime["report"] is False


_CENSUS_MOVEMENTS = {
    "0002": ("function-globals-read", "function-return-shape"),
    "0007": ("augmented-assignment-not-modeled",),
    "0011": ("reader-form-unsupported",),
    "0021": ("reader-form-unsupported",),
    "0028": ("function-globals-read",),
    "0033": ("augmented-assignment-not-modeled",),
    "0034": ("function-globals-read", "function-return-shape"),
}

_FROZEN_RAISE_CASES = {
    ("batch-c", "41cfd59360a1ca24ca4b"): (
        "function-return-shape",
        "raise-guard-not-modeled",
    ),
    ("batch-d", "7da68ec265e1bb2f6640"): ("raise-guard-not-modeled",),
    ("batch-d", "f75b02bd61e813195904"): (
        "function-globals-read",
        "raise-guard-not-modeled",
    ),
    ("batch-e1", "acea1e7265fd2ac91a43"): (
        "function-globals-read",
        "raise-guard-not-modeled",
    ),
    ("batch-e1", "f203d7292f9530cbdf48"): ("raise-guard-not-modeled",),
    ("batch-e2", "102f7842bc112abba84f"): ("raise-guard-not-modeled",),
    ("batch-e2", "18f0af8326d59d579c43"): (
        "function-return-shape",
        "raise-guard-not-modeled",
    ),
    ("batch-e2", "e57e3c73264eda49b3cc"): ("raise-guard-not-modeled",),
    ("batch-f1", "c2db115846830b7d908c"): ("raise-guard-not-modeled",),
    ("batch-f1", "f68415be40b9234987de"): ("raise-guard-not-modeled",),
    ("batch-f2", "605c4c08512e4489cc9a"): (
        "count-predicate-not-closed",
        "raise-guard-not-modeled",
    ),
    ("batch-f2", "b24355b160cf4665b929"): ("raise-guard-not-modeled",),
    ("batch-g1", "2ddf508d135fd7fce5df"): ("raise-guard-not-modeled",),
    ("batch-g2", "a8b660a9685f13f0187f"): ("augmented-assignment-not-modeled",),
    ("batch-h2", "4da6848cdd3a5d975d87"): (
        "count-predicate-not-closed",
        "function-return-shape",
        "raise-guard-not-modeled",
    ),
    ("batch-h2", "78bfad17cf5492340eb0"): (
        "function-default-params",
        "function-return-shape",
        "raise-guard-not-modeled",
    ),
    ("batch-i2", "6aac19a2a2aa18f85740"): ("raise-guard-not-modeled",),
    ("batch-j1", "eb93048bfef98eab102f"): (
        "function-closure",
        "function-globals-read",
        "function-return-shape",
        "raise-guard-not-modeled",
    ),
    ("batch-j2", "729d2099346c87040906"): (
        "count-predicate-not-closed",
        "procedure-call-unresolved",
    ),
}


def _case_context(case: Path) -> FrozenInspectionContext:
    description = (case / "data-description.md").read_text(encoding="utf-8")
    match = re.search(r"(?i)Independent unit column:[ \t]*([^\r\n]+)", description)
    assert match is not None
    return _context(
        (case / "workflow/analysis.py").read_text(encoding="utf-8"),
        (case / "data/input.csv").read_bytes(),
        unit_column=match.group(1).strip().strip("`"),
        data_path="data/input.csv",
    )


def test_exact_nine_syntax_movements_and_all_frozen_raise_sets(
    project_root: Path,
) -> None:
    census = project_root / "evaluation/development/wall-mining-corpus/run-40-authority-2/cases"
    census_payloads = {
        case_id: DependenceRecognitionV2ShadowAdapter().inspect(_case_context(census / case_id))
        for case_id in _CENSUS_MOVEMENTS
    }
    observed_census = {
        case_id: tuple(payload["abstention_reasons"])
        for case_id, payload in census_payloads.items()
    }
    assert observed_census == _CENSUS_MOVEMENTS

    growth = project_root / "evaluation/development/dependence-growth-loop"
    frozen_payloads = {
        key: DependenceRecognitionV2ShadowAdapter().inspect(
            _case_context(growth / key[0] / "authoring/cases" / key[1])
        )
        for key in _FROZEN_RAISE_CASES
    }
    observed_frozen = {
        key: tuple(payload["abstention_reasons"]) for key, payload in frozen_payloads.items()
    }
    assert observed_frozen == _FROZEN_RAISE_CASES
    assert len(_FROZEN_RAISE_CASES) == 19
    assert (
        sum(
            sum(
                isinstance(node, ast.Raise)
                for node in ast.walk(
                    ast.parse(
                        (
                            growth / lane / "authoring/cases" / case_id / "workflow/analysis.py"
                        ).read_text(encoding="utf-8")
                    )
                )
            )
            for lane, case_id in _FROZEN_RAISE_CASES
        )
        == 46
    )
    assert len(_CENSUS_MOVEMENTS) + len(_FROZEN_RAISE_CASES) == 26
    assert len(_FROZEN_RAISE_CASES) - 2 == 17
    all_payloads = (*census_payloads.values(), *frozen_payloads.values())
    assert all(payload["outcome"] == "unsupported" for payload in all_payloads)
    assert all(payload["production_finding_permitted"] is False for payload in all_payloads)


def test_all_lane_planted_positive_inventory_remains_non_accusatory(
    project_root: Path,
) -> None:
    root = project_root / "evaluation/development/dependence-growth-loop"
    positive_labels: list[tuple[Path, str]] = []
    for ledger_path in sorted(root.glob("batch-*/SCIENTIFIC_LABEL_LEDGER.json")):
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        positive_labels.extend(
            (ledger_path.parent, entry["case_id"].removeprefix("case:"))
            for entry in ledger["entries"]
            if entry["label_status"] == "positive_demonstrated"
        )
    materialized = [
        (batch, case_id)
        for batch, case_id in positive_labels
        if (batch / "authoring/cases" / case_id).is_dir()
    ]
    recorded_outcomes: list[str | None] = []
    for batch, case_id in materialized:
        result = json.loads(
            (batch / "detector-run/case-results" / f"{case_id}.json").read_text(encoding="utf-8")
        )
        payload = result.get("development_v2_shadow_payload")
        recorded_outcomes.append(payload.get("outcome") if isinstance(payload, dict) else None)
    assert len(positive_labels) == 54
    assert len(materialized) == 53
    assert "evaluation_candidate" not in recorded_outcomes


def test_no_material_free_verified_compatibility_signature() -> None:
    context = _context(_source(), _ADVERSE)
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    fact = _fact(context, analysis.certificate.obligation)
    certificate = _final_certificate(analysis.certificate, fact)
    with pytest.raises(TypeError, match="trusted_material_inputs"):
        verify_dependence_growth_certificate(  # type: ignore[call-arg]
            certificate,
            trusted_group_facts=(fact,),
            trusted_authorizations=_trusted_v2_authorizations(context),
            source_bytes=context.documents[0].content,
        )
