"""Growth-14 exact pandas source, byte-domain, package, and kernel regressions."""

from __future__ import annotations

import ast
import copy
import json
import os
import re
import subprocess
import textwrap
from collections import Counter
from dataclasses import asdict, replace
from itertools import combinations
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.controller import (
    FrozenFileManifestInput,
    ManifestBoundFrozenInspectionContext,
)
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition_v2.adapter import DependenceRecognitionV2ShadowAdapter
from sc_referee.dependence_recognition_v2.certificate import (
    _kernel_node_token,
    _kernel_pandas_package_identity,
    _kernel_pandas_source_replay,
    _kernel_replay_pandas_group_fact,
    _kernel_statement_token,
    verify_dependence_growth_certificate,
)
from sc_referee.dependence_recognition_v2.csv_domain import (
    prove_group_value_sequences_with_reason,
)
from sc_referee.dependence_recognition_v2.ir import (
    DEPENDENCE_V2_REASON_REGISTRY,
    DependenceGrowthCertificate,
    GroupValueSequenceFact,
    PandasPackageIdentity,
    PandasSourceDescriptor,
)
from sc_referee.dependence_recognition_v2.pandas_runtime_premise import (
    PANDAS_3_0_5_DEFAULT_MISSING_TOKENS,
    PANDAS_DEVELOPMENT_RUNTIME_PREMISE,
    PANDAS_DEVELOPMENT_RUNTIME_PREMISE_DIGEST,
)
from sc_referee.dependence_recognition_v2.python_analyzer import (
    _analyzer_pandas_package_identity,
    _growth_certificate_identity,
    _trusted_v2_authorizations,
    _trusted_v2_procedure_sets,
    analyze_dependence_growth_python,
)
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    InspectionDocument,
    RecordRef,
)

_RUNTIME = Path(
    os.environ.get(
        "SC_REFEREE_DEPENDENCE_V2_SANDBOX_PYTHON",
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime/"
        "scipy114-venv/bin/python",
    )
)
_CENSUS = Path("evaluation/development/wall-mining-corpus/run-40-authority-2/cases")
_TARGETS = ("0006", "0012", "0025", "0030", "0035", "0038", "0039")
_EXCLUDED = {
    "0004": "pandas-frame-transform-not-closed",
    "0009": "raise-guard-not-modeled",
    "0014": "pandas-script-function-not-closed",
    "0016": "pandas-script-shape-not-closed",
    "0027": "raise-guard-not-modeled",
}
_INVENTORIES = {
    "0004": (7, "sha256:3ca5da68294251bf7dbc3359e517a3bfd173b1c56cf440f1d5971f4abf84c532"),
    "0006": (7, "sha256:45ca22e35f0273aef71f8b58250207c16e2dd9f795f2be0ce76d895a7cb0f1c7"),
    "0009": (7, "sha256:fecbc701f89d805b0a7d2b54b0aef445f9f654e9cec3e8e55b0aa4cf1408c842"),
    "0012": (7, "sha256:8d4ead0fe36ccdaca13abdc8d9d12de30ddc965b2c9a30cbb11a217af5e7e64a"),
    "0014": (7, "sha256:dabdeefd2278b330b3320d963571699f4eba0a5df2d656e22d1f0cb9329c2b72"),
    "0016": (7, "sha256:7ec53024264211dd29416aaaf7487dafd542b56b4308664b1755e90abdaae394"),
    "0025": (7, "sha256:4b4a547e1e772b2cddee2322125bde750a48aa5f61e0e1b02ecbdb53352b7da0"),
    "0027": (7, "sha256:846fc1eff067517765d435c8cfd4156b2a82b3878444f499f7003333807a3b57"),
    "0030": (6, "sha256:73dc027950c3209a8ac794ce81cf5a97ef44356504ff83b8a9527c1f47956879"),
    "0035": (7, "sha256:91eef7449ffa85d821ae5b28227778130e9f4c56abd80ffd2f4ea408325044a0"),
    "0038": (6, "sha256:5bb053891b186456fcec1f01c438e5857f9fd38845033dd81e91666107ccdc83"),
    "0039": (7, "sha256:6e2c62bca67abb8e16cb64989b2c3439a074eb836df0c8753cc95f2618bc6d66"),
}
_COVERED_DATA = b"unit_id,arm,value\nu1,A,1\nu2,A,2\nu3,B,3\nu4,B,4"
_REPEATED_DATA = b"unit_id,arm,value\nu1,A,1\nu1,A,2\nu2,B,3\nu3,B,4"
_CROSS_DATA = b"unit_id,arm,value\nu1,A,1\nu2,A,2\nu1,B,3\nu3,B,4"


def _record(ref: RecordRef, payload: dict[str, object]) -> FrozenBaseRecord:
    return FrozenBaseRecord.from_record(ref, payload)


def _context_from_inventory(
    *,
    source: bytes,
    data: bytes,
    unit_column: str,
    procedure: str,
    inventory: dict[str, bytes],
    snapshot_digest: str | None = None,
    extra_inventory_entries: tuple[tuple[str, str], ...] = (),
) -> FrozenInspectionContext:
    suffix = semantic_digest(
        {
            "source": sha256_digest(source),
            "data": sha256_digest(data),
            "unit": unit_column,
            "procedure": procedure,
            "inventory": sorted(inventory),
            "extra": extra_inventory_entries,
        }
    )[-20:]
    surface = RecordRef("publication_surface", f"surface:g14:{suffix}")
    artifact = RecordRef("artifact", f"artifact:g14:{suffix}")
    snapshot = RecordRef("repository_snapshot", f"snapshot:g14:{suffix}")
    parser = RecordRef("parser_result", f"parser:g14:{suffix}")
    analysis = RecordRef("analysis", f"analysis-v2:g14:{suffix}")
    procedure_ref = RecordRef("procedure", f"procedure-v2:g14:{suffix}")
    result = RecordRef("result", f"result-v2:g14:{suffix}")
    authority = RecordRef("human_method_authorization", f"authorization-v2:g14:{suffix}")
    snapshot_value = snapshot_digest or sha256_digest(f"snapshot:g14:{suffix}".encode())
    snapshot_ref = snapshot.to_dict()
    records = [
        _record(
            surface,
            {
                "publication_surface_id": surface.record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [artifact.to_dict()]},
            },
        ),
        _record(
            artifact,
            {
                "artifact_id": artifact.record_id,
                "kind": "report",
                "path": "results/report.md",
            },
        ),
        _record(
            snapshot,
            {
                "snapshot_id": snapshot.record_id,
                "snapshot_digest": snapshot_value,
                "included_roots": ["."],
                "file_manifest_ref": "observed/files.jsonl",
                "immutability": True,
                "extensions": {
                    "x-material-full-digest-paths": ["data/input.csv", "requirements.txt"]
                },
            },
        ),
    ]
    file_refs: dict[str, RecordRef] = {}
    identity_refs: dict[str, RecordRef] = {}
    for index, (path, content) in enumerate(sorted(inventory.items())):
        file_ref = RecordRef("file_record", f"file:g14:{suffix}:{index}")
        identity_ref = RecordRef("asset_identity", f"asset:g14:{suffix}:{index}")
        file_refs[path] = file_ref
        identity_refs[path] = identity_ref
        digest = sha256_digest(content)
        records.extend(
            (
                _record(
                    file_ref,
                    {
                        "record_type": "file_record",
                        "file_record_id": file_ref.record_id,
                        "path": path,
                        "entry_kind": "regular_file",
                        "byte_size": len(content),
                        "snapshot_ref": snapshot_ref,
                        "asset_identity_ref": identity_ref.to_dict(),
                    },
                ),
                _record(
                    identity_ref,
                    {
                        "record_type": "asset_identity",
                        "asset_identity_id": identity_ref.record_id,
                        "tier": "full_digest",
                        "asset_ref": file_ref.to_dict(),
                        "identity_evidence": {"kind": "full_digest", "digest": digest},
                    },
                ),
            )
        )
    for index, (path, entry_kind) in enumerate(extra_inventory_entries):
        file_ref = RecordRef("file_record", f"extra-file:g14:{suffix}:{index}")
        identity_ref = RecordRef("asset_identity", f"extra-asset:g14:{suffix}:{index}")
        records.extend(
            (
                _record(
                    file_ref,
                    {
                        "record_type": "file_record",
                        "file_record_id": file_ref.record_id,
                        "path": path,
                        "entry_kind": entry_kind,
                        "byte_size": 0,
                        "snapshot_ref": snapshot_ref,
                        "asset_identity_ref": identity_ref.to_dict(),
                    },
                ),
                _record(
                    identity_ref,
                    {
                        "record_type": "asset_identity",
                        "asset_identity_id": identity_ref.record_id,
                        "tier": "unidentified",
                        "asset_ref": file_ref.to_dict(),
                        "identity_evidence": {
                            "kind": "unidentified",
                            "reason": f"test {entry_kind} entry",
                        },
                    },
                ),
            )
        )
    requirements = b"scipy==1.14.0\n"
    requirements_file = RecordRef("file_record", f"requirements-file:g14:{suffix}")
    requirements_identity = RecordRef("asset_identity", f"requirements-asset:g14:{suffix}")
    records.extend(
        (
            _record(
                requirements_file,
                {
                    "file_record_id": requirements_file.record_id,
                    "path": "requirements.txt",
                    "entry_kind": "regular_file",
                    "asset_identity_ref": requirements_identity.to_dict(),
                },
            ),
            _record(
                requirements_identity,
                {
                    "asset_identity_id": requirements_identity.record_id,
                    "tier": "full_digest",
                    "asset_ref": requirements_file.to_dict(),
                    "identity_evidence": {
                        "kind": "full_digest",
                        "digest": sha256_digest(requirements),
                    },
                },
            ),
            _record(parser, {"parser_result_id": parser.record_id}),
            _record(analysis, {"analysis_id": analysis.record_id}),
            _record(
                procedure_ref,
                {
                    "procedure_id": procedure_ref.record_id,
                    "resolved_callable": procedure,
                },
            ),
            _record(result, {"result_id": result.record_id, "path": "results/report.md"}),
            _record(
                authority,
                {
                    "record_type": "human_method_authorization",
                    "record_id": authority.record_id,
                    "actor_id": "human:growth14-test",
                    "authority_state": "authorized",
                    "analysis_target_ref": analysis.to_dict(),
                    "procedure_ref": procedure_ref.to_dict(),
                    "independent_unit_definition_id": f"unit-definition:g14:{suffix}",
                    "authorized_key_columns": [unit_column],
                    "input_path": "data/input.csv",
                    "input_content_digest": sha256_digest(data),
                },
            ),
        )
    )
    parser_payload = canonical_json(
        {"parser_id": "python-ast", "parser_version": "3.11", "state": "parsed"}
    ).encode()
    manifest_bytes = b"".join(
        record.canonical_payload + b"\n"
        for record in records
        if record.ref.record_type == "file_record"
        and json.loads(record.canonical_payload).get("snapshot_ref") == snapshot_ref
    )
    return ManifestBoundFrozenInspectionContext(
        snapshot_digest=snapshot_value,
        selected_surface_ref=surface,
        selected_artifact_ref=artifact,
        documents=(
            InspectionDocument(
                path="workflow/analysis.py",
                file_ref=file_refs["workflow/analysis.py"],
                content=source,
                content_digest=sha256_digest(source),
                media_type="text/x-python",
                parser_result_ref=parser,
                parser_result_payload=parser_payload,
                parser_result_digest=sha256_digest(parser_payload),
            ),
        ),
        base_records=tuple(records),
        file_manifest_input=FrozenFileManifestInput(
            file_manifest_ref="observed/files.jsonl",
            canonical_jsonl_bytes=manifest_bytes,
            manifest_digest=sha256_digest(manifest_bytes),
        ),
        material_inputs=(
            FrozenMaterialInput(
                "data/input.csv",
                file_refs["data/input.csv"],
                identity_refs["data/input.csv"],
                data,
                sha256_digest(data),
            ),
            FrozenMaterialInput(
                "requirements.txt",
                requirements_file,
                requirements_identity,
                requirements,
                sha256_digest(requirements),
            ),
        ),
    )


def _synthetic_context(
    source: str,
    data: bytes = _COVERED_DATA,
    *,
    unit_column: str = "unit_id",
    procedure: str = "scipy.stats.ttest_ind",
    inventory_additions: dict[str, bytes] | None = None,
    extra_inventory_entries: tuple[tuple[str, str], ...] = (),
) -> FrozenInspectionContext:
    source_bytes = source.encode("utf-8")
    inventory = {
        "workflow/analysis.py": source_bytes,
        "data/input.csv": data,
        "data-description.md": f"Independent unit column: {unit_column}".encode(),
    }
    inventory.update(inventory_additions or {})
    return _context_from_inventory(
        source=source_bytes,
        data=data,
        unit_column=unit_column,
        procedure=procedure,
        inventory=inventory,
        extra_inventory_entries=extra_inventory_entries,
    )


def _source(
    *,
    projection: str = "series",
    procedure: str = "ttest_ind",
    keyword: str = "",
    summaries: str = "left_mean = left.mean()\nright_mean = right.mean()",
) -> str:
    if projection == "series":
        left = "left = frame[frame['arm'] == 'A']['value']"
        right = "right = frame[frame['arm'] == 'B']['value']"
    elif projection == "values":
        left = "left = frame[frame['arm'] == 'A']['value'].values"
        right = "right = frame[frame['arm'] == 'B']['value'].values"
    elif projection == "values_alias":
        left = "left_series = frame[frame['arm'] == 'A']['value']\nleft = left_series.values"
        right = "right_series = frame[frame['arm'] == 'B']['value']\nright = right_series.values"
    elif projection == "dropna":
        left = "left = frame[frame['arm'] == 'A']['value'].dropna()"
        right = "right = frame[frame['arm'] == 'B']['value'].dropna()"
    else:
        raise AssertionError(projection)
    call = f"stats.{procedure}(left, right{keyword})"
    left_block = textwrap.indent(left, "        ")
    right_block = textwrap.indent(right, "        ")
    summary_block = textwrap.indent(summaries, "        ")
    return textwrap.dedent(
        f"""\
        import pandas as pd
        from scipy import stats

        frame = pd.read_csv('data/input.csv')
{left_block}
{right_block}
        statistic, p_value = {call}
{summary_block}
        report = f"stat={{statistic}} p={{p_value}} left={{left_mean}} right={{right_mean}}"
        with open('results/report.md', 'w') as handle:
            handle.write(report)
        """
    )


def _source_groups(left_key: str, right_key: str, **kwargs: str) -> str:
    source = _source(**kwargs)
    source = source.replace("== 'A'", f"== {left_key!r}", 1)
    return source.replace("== 'B'", f"== {right_key!r}", 1)


def _group_data(left_key: str, right_key: str, values: tuple[str, str, str, str]) -> bytes:
    return (
        "unit_id,arm,value\n"
        f"u1,{left_key},{values[0]}\n"
        f"u2,{left_key},{values[1]}\n"
        f"u3,{right_key},{values[2]}\n"
        f"u4,{right_key},{values[3]}"
    ).encode("ascii")


def _case_context(case: Path) -> FrozenInspectionContext:
    inventory = {
        path.relative_to(case).as_posix(): path.read_bytes()
        for path in sorted(case.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }
    translation = json.loads(inventory["lock-translation.json"])
    if "authorization-lock.json" in inventory:
        lock = json.loads(inventory["authorization-lock.json"])
        authority = next(
            item
            for item in lock["records"]
            if item.get("record_type") == "human_method_authorization"
        )
        unit_column = authority["authorized_key_columns"][0]
        procedure_name = next(
            item for item in lock["records"] if item.get("record_type") == "procedure"
        )["resolved_callable"]
        snapshot_digest = lock["snapshot_digest"]
    else:
        match = re.search(
            rb"Independent unit column:[ \t]*([^\r\n]+)",
            inventory["data-description.md"],
        )
        assert match is not None
        unit_column = match.group(1).decode("ascii").strip()
        procedure_name = translation["resolved_procedures"][0]
        snapshot_digest = sha256_digest(f"growth14-scratch:{case.name}".encode())
    return _context_from_inventory(
        source=inventory["workflow/analysis.py"],
        data=inventory["data/input.csv"],
        unit_column=unit_column,
        procedure=procedure_name,
        inventory=inventory,
        snapshot_digest=snapshot_digest,
    )


def _data_material(context: FrozenInspectionContext) -> FrozenMaterialInput:
    return next(item for item in context.material_inputs if item.path == "data/input.csv")


def _proposal_and_fact(
    context: FrozenInspectionContext,
) -> tuple[DependenceGrowthCertificate, GroupValueSequenceFact]:
    analysis = analyze_dependence_growth_python(context)
    assert analysis.state == "proposal", analysis.abstention_reasons
    assert isinstance(analysis.certificate, DependenceGrowthCertificate)
    fact, reason = prove_group_value_sequences_with_reason(
        _data_material(context), obligation=analysis.certificate.obligation
    )
    assert reason is None
    assert fact is not None
    return analysis.certificate, fact


def _final_certificate(
    certificate: DependenceGrowthCertificate, fact: GroupValueSequenceFact
) -> DependenceGrowthCertificate:
    by_key = {item.group_key: item for item in fact.groups}
    repeated = {
        unit
        for binding in certificate.operand_bindings
        for unit, count in Counter(by_key[binding.group_key].authorized_unit_ids).items()
        if count > 1
    }
    conclusion = "repeated_units" if repeated else "one_observation_per_unit"
    finalized = replace(certificate, conclusion=conclusion)
    return replace(
        finalized,
        certificate_id=_growth_certificate_identity(finalized, fact, conclusion),
    )


def _verify(
    certificate: DependenceGrowthCertificate,
    fact: GroupValueSequenceFact,
    context: FrozenInspectionContext,
    *,
    material: FrozenMaterialInput | None = None,
) -> tuple[Any | None, tuple[str, ...]]:
    failures: list[str] = []
    verified = verify_dependence_growth_certificate(
        certificate,
        trusted_group_facts=(fact,),
        trusted_material_inputs=(material or _data_material(context),),
        trusted_authorizations=_trusted_v2_authorizations(context),
        trusted_procedure_sets=_trusted_v2_procedure_sets(context),
        trusted_base_records=context.base_records,
        trusted_file_manifest_input=context.file_manifest_input,
        source_bytes=context.documents[0].content,
        _failure_reasons=failures,
    )
    return verified, tuple(failures)


def _case_context_with_data(case: Path, data: bytes) -> FrozenInspectionContext:
    inventory = {
        path.relative_to(case).as_posix(): path.read_bytes()
        for path in sorted(case.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }
    inventory["data/input.csv"] = data
    translation = json.loads(inventory["lock-translation.json"])
    if "authorization-lock.json" in inventory:
        lock = json.loads(inventory["authorization-lock.json"])
        authority = next(
            item
            for item in lock["records"]
            if item.get("record_type") == "human_method_authorization"
        )
        unit_column = authority["authorized_key_columns"][0]
        snapshot_digest = lock["snapshot_digest"]
    else:
        match = re.search(
            rb"Independent unit column:[ \t]*([^\r\n]+)",
            inventory["data-description.md"],
        )
        assert match is not None
        unit_column = match.group(1).decode("ascii").strip()
        snapshot_digest = sha256_digest(f"growth14-scratch:{case.name}".encode())
    return _context_from_inventory(
        source=inventory["workflow/analysis.py"],
        data=data,
        unit_column=unit_column,
        procedure=translation["resolved_procedures"][0],
        inventory=inventory,
        snapshot_digest=snapshot_digest,
    )


def _replace_base_payload(
    context: FrozenInspectionContext,
    ref: RecordRef,
    update: dict[str, object],
) -> FrozenInspectionContext:
    records: list[FrozenBaseRecord] = []
    for record in context.base_records:
        if record.ref != ref:
            records.append(record)
            continue
        payload = json.loads(record.canonical_payload)
        assert isinstance(payload, dict)
        payload.update(update)
        records.append(FrozenBaseRecord.from_record(record.ref, payload))
    return replace(context, base_records=tuple(records))


def _manifest_entries(context: FrozenInspectionContext) -> list[dict[str, Any]]:
    manifest = context.file_manifest_input
    assert manifest is not None
    return [
        cast(dict[str, Any], json.loads(line))
        for line in manifest.canonical_jsonl_bytes.decode("utf-8").splitlines()
    ]


def _manifest_input(
    entries: list[dict[str, Any]],
    *,
    file_manifest_ref: str = "observed/files.jsonl",
) -> FrozenFileManifestInput:
    content = b"".join((canonical_json(entry) + "\n").encode("utf-8") for entry in entries)
    return FrozenFileManifestInput(
        file_manifest_ref=file_manifest_ref,
        canonical_jsonl_bytes=content,
        manifest_digest=sha256_digest(content),
    )


def _raw_manifest_input(
    content: bytes,
    *,
    file_manifest_ref: str = "observed/files.jsonl",
) -> FrozenFileManifestInput:
    return FrozenFileManifestInput(
        file_manifest_ref=file_manifest_ref,
        canonical_jsonl_bytes=content,
        manifest_digest=sha256_digest(content),
    )


def _stale_manifest_digest(
    manifest: FrozenFileManifestInput,
) -> FrozenFileManifestInput:
    stale = object.__new__(FrozenFileManifestInput)
    object.__setattr__(stale, "file_manifest_ref", manifest.file_manifest_ref)
    object.__setattr__(stale, "canonical_jsonl_bytes", manifest.canonical_jsonl_bytes)
    object.__setattr__(stale, "manifest_digest", sha256_digest(b"different manifest"))
    return cast(FrozenFileManifestInput, stale)


def _snapshot_ref(context: FrozenInspectionContext) -> RecordRef:
    return next(
        record.ref
        for record in context.base_records
        if record.ref.record_type == "repository_snapshot"
    )


def _add_base_file_without_manifest(
    context: FrozenInspectionContext,
    *,
    path: str,
) -> FrozenInspectionContext:
    suffix = semantic_digest({"context": context.context_digest, "path": path})[-20:]
    file_ref = RecordRef("file_record", f"file:g14:base-only:{suffix}")
    identity_ref = RecordRef("asset_identity", f"asset:g14:base-only:{suffix}")
    digest = sha256_digest(b"base-only")
    file_record = _record(
        file_ref,
        {
            "record_type": "file_record",
            "file_record_id": file_ref.record_id,
            "path": path,
            "entry_kind": "regular_file",
            "byte_size": len(b"base-only"),
            "snapshot_ref": _snapshot_ref(context).to_dict(),
            "asset_identity_ref": identity_ref.to_dict(),
        },
    )
    identity = _record(
        identity_ref,
        {
            "record_type": "asset_identity",
            "asset_identity_id": identity_ref.record_id,
            "tier": "full_digest",
            "asset_ref": file_ref.to_dict(),
            "identity_evidence": {"kind": "full_digest", "digest": digest},
        },
    )
    return replace(context, base_records=(*context.base_records, file_record, identity))


def _assert_both_package_identity_paths_refuse(context: FrozenInspectionContext) -> None:
    source = context.documents[0]
    material = _data_material(context)
    assert (
        _analyzer_pandas_package_identity(
            context,
            source_path=source.path,
            source_digest=source.content_digest,
            material=material,
        )
        is None
    )
    assert (
        _kernel_pandas_package_identity(
            context.base_records,
            file_manifest_input=context.file_manifest_input,
            source_path=source.path,
            source_digest=source.content_digest,
            material=material,
        )
        is None
    )


def _stale_material(material: FrozenMaterialInput, content: bytes) -> FrozenMaterialInput:
    stale = object.__new__(FrozenMaterialInput)
    for field, value in (
        ("path", material.path),
        ("file_ref", material.file_ref),
        ("asset_identity_ref", material.asset_identity_ref),
        ("content", content),
        ("content_digest", material.content_digest),
    ):
        object.__setattr__(stale, field, value)
    return cast(FrozenMaterialInput, stale)


def _replace_csv_cell(
    data: bytes, *, column: str, replacement: bytes, row_number: int = 1
) -> bytes:
    records = data.split(b"\n")
    header = records[0].split(b",")
    column_index = header.index(column.encode("ascii"))
    cells = records[row_number].split(b",")
    cells[column_index] = replacement
    records[row_number] = b",".join(cells)
    return b"\n".join(records)


def _physical_siblings(data: bytes, *, value_column: str, unit_column: str) -> dict[str, bytes]:
    records = data.split(b"\n")
    doubled_index = data.index(b"\n")
    interior_index = data.index(b"\n", doubled_index + 1)
    quoted = _replace_csv_cell(
        data,
        column=value_column,
        replacement=b'"' + records[1].split(b",")[-1] + b'"',
    )
    ragged_records = list(records)
    ragged_records[1] += b",extra"
    return {
        "terminal_lf": data + b"\n",
        "crlf": data.replace(b"\n", b"\r\n"),
        "leading_lf": b"\n" + data,
        "doubled_lf": data[: doubled_index + 1] + b"\n" + data[doubled_index + 1 :],
        "interior_blank": data[: interior_index + 1] + b"\n" + data[interior_index + 1 :],
        "missing_token": _replace_csv_cell(data, column=value_column, replacement=b"NA"),
        "quoted": quoted,
        "ragged": b"\n".join(ragged_records),
        "non_ascii": _replace_csv_cell(data, column=unit_column, replacement=b"unit-\xc2\xb5"),
    }


def _coherent_material_kernel_failure(
    valid_context: FrozenInspectionContext,
    valid_certificate: DependenceGrowthCertificate,
    valid_fact: GroupValueSequenceFact,
    sibling_context: FrozenInspectionContext,
) -> tuple[str, ...]:
    source = sibling_context.documents[0]
    sibling_material = _data_material(sibling_context)
    package_identity = _analyzer_pandas_package_identity(
        sibling_context,
        source_path=source.path,
        source_digest=source.content_digest,
        material=sibling_material,
    )
    assert package_identity is not None
    descriptor = cast(PandasSourceDescriptor, valid_certificate.obligation.pandas_source)
    sibling_descriptor = replace(descriptor, package_identity=package_identity)
    sibling_obligation = replace(
        valid_certificate.obligation,
        content_digest=sibling_material.content_digest,
        pandas_source=sibling_descriptor,
    )
    authority = _trusted_v2_authorizations(sibling_context)[0]
    sibling_certificate = replace(
        valid_certificate,
        analysis_target_ref=authority.analysis_target_ref,
        procedure_ref=authority.procedure_ref,
        authority_record_id=authority.record_id,
        independent_unit_definition_id=authority.independent_unit_definition_id,
        obligation=sibling_obligation,
    )
    _verified, failures = _verify(
        sibling_certificate,
        valid_fact,
        sibling_context,
    )
    return failures


def _changed_source_certificate(
    valid_certificate: DependenceGrowthCertificate,
    changed_context: FrozenInspectionContext,
    *,
    replay_descriptor: bool,
) -> tuple[DependenceGrowthCertificate, GroupValueSequenceFact]:
    source = changed_context.documents[0]
    material = _data_material(changed_context)
    package = _kernel_pandas_package_identity(
        changed_context.base_records,
        file_manifest_input=changed_context.file_manifest_input,
        source_path=source.path,
        source_digest=source.content_digest,
        material=material,
    )
    assert package is not None
    old_descriptor = cast(PandasSourceDescriptor, valid_certificate.obligation.pandas_source)
    descriptor = replace(old_descriptor, package_identity=package)
    procedure_tokens = valid_certificate.procedure_call_tokens
    sink_token = valid_certificate.sink_token
    operand_tokens = valid_certificate.operand_slice_statement_tokens
    sink_tokens = valid_certificate.sink_bound_statement_tokens
    if replay_descriptor:
        tree = ast.parse(source.content.decode("utf-8"))
        replay, failure = _kernel_pandas_source_replay(tree, source.path, package)
        assert failure is None
        assert replay is not None
        descriptor = replay.descriptor
        procedure_tokens = (
            _kernel_node_token(source.path, replay.procedure_call, "procedure-call"),
        )
        sink_token = _kernel_node_token(source.path, replay.write_call, "selected-sink")
        old_indexes = {
            token: index for index, token in enumerate(old_descriptor.executable_statement_tokens)
        }
        operand_tokens = tuple(
            descriptor.executable_statement_tokens[old_indexes[token]]
            for token in valid_certificate.operand_slice_statement_tokens
        )
        sink_tokens = tuple(
            descriptor.executable_statement_tokens[old_indexes[token]]
            for token in valid_certificate.sink_bound_statement_tokens
        )
        assert descriptor.executable_statement_tokens == tuple(
            _kernel_statement_token(statement, index) for index, statement in enumerate(replay.body)
        )
    obligation = replace(valid_certificate.obligation, pandas_source=descriptor)
    fact, reason = prove_group_value_sequences_with_reason(material, obligation=obligation)
    assert reason is None
    assert fact is not None
    authority = _trusted_v2_authorizations(changed_context)[0]
    return (
        replace(
            valid_certificate,
            source_digest=source.content_digest,
            source_extent=(0, len(source.content)),
            analysis_target_ref=authority.analysis_target_ref,
            procedure_ref=authority.procedure_ref,
            authority_record_id=authority.record_id,
            independent_unit_definition_id=authority.independent_unit_definition_id,
            obligation=obligation,
            procedure_call_tokens=procedure_tokens,
            sink_token=sink_token,
            operand_slice_statement_tokens=operand_tokens,
            sink_bound_statement_tokens=sink_tokens,
        ),
        fact,
    )


def test_exact_frozen_inventory_digests_and_target_outcomes(project_root: Path) -> None:
    observed: dict[str, tuple[int, str]] = {}
    outcomes: dict[str, str] = {}
    for case_id in _INVENTORIES:
        context = _case_context(project_root / _CENSUS / case_id)
        source = context.documents[0]
        identity = _analyzer_pandas_package_identity(
            context,
            source_path=source.path,
            source_digest=source.content_digest,
            material=_data_material(context),
        )
        assert identity is not None
        observed[case_id] = (identity.regular_file_count, identity.inventory_digest)
        if case_id in _TARGETS:
            outcomes[case_id] = DependenceRecognitionV2ShadowAdapter().inspect(context)["outcome"]
    assert observed == _INVENTORIES
    assert outcomes == {
        "0006": "covered_negative",
        "0012": "covered_negative",
        "0025": "evaluation_candidate",
        "0030": "covered_negative",
        "0035": "covered_negative",
        "0038": "covered_negative",
        "0039": "covered_negative",
    }


def test_exact_five_excluded_census_first_walls(project_root: Path) -> None:
    observed = {
        case_id: tuple(
            DependenceRecognitionV2ShadowAdapter().inspect(
                _case_context(project_root / _CENSUS / case_id)
            )["abstention_reasons"]
        )
        for case_id in _EXCLUDED
    }
    assert observed == {key: (value,) for key, value in _EXCLUDED.items()}


def test_declared_isolated_pandas_runtime_and_complete_record_liveness() -> None:
    assert _RUNTIME.is_file()
    probe = r"""
import base64
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

import dateutil
import numpy
import pandas
import scipy

package_init = Path(pandas.__file__).resolve()
site_packages = package_init.parents[1]
dist_info = site_packages / "pandas-3.0.5.dist-info"
artifacts = {}
for name in ("METADATA", "RECORD", "WHEEL"):
    artifacts[name] = "sha256:" + hashlib.sha256((dist_info / name).read_bytes()).hexdigest()
record_bytes = (dist_info / "RECORD").read_bytes()
rows = list(csv.reader(io.StringIO(record_bytes.decode("utf-8"), newline="")))
hashed = 0
unhashed = 0
hashed_bytes = 0
missing = 0
mismatches = 0
for relative, carried_hash, carried_size in rows:
    if not carried_hash:
        unhashed += 1
        continue
    target = site_packages / relative
    if not target.is_file():
        missing += 1
        continue
    hashed += 1
    payload = target.read_bytes()
    hashed_bytes += len(payload)
    algorithm, encoded = carried_hash.split("=", 1)
    observed = base64.urlsafe_b64encode(hashlib.new(algorithm, payload).digest()).decode().rstrip("=")
    if observed != encoded or (carried_size and len(payload) != int(carried_size)):
        mismatches += 1
print(json.dumps({
    "python_version": ".".join(map(str, sys.version_info[:3])),
    "pandas_version": pandas.__version__,
    "numpy_version": numpy.__version__,
    "scipy_version": scipy.__version__,
    "python_dateutil_version": dateutil.__version__,
    "origin": str(package_init),
    "site_packages": str(site_packages),
    "artifacts": artifacts,
    "record_rows": len(rows),
    "hashed_regular_files": hashed,
    "unhashed_rows": unhashed,
    "hashed_regular_bytes": hashed_bytes,
    "missing_hashed_files": missing,
    "digest_mismatches": mismatches,
}, sort_keys=True))
"""
    completed = subprocess.run(
        [str(_RUNTIME), "-I", "-c", probe],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    observed = json.loads(completed.stdout)
    premise = PANDAS_DEVELOPMENT_RUNTIME_PREMISE
    assert observed["python_version"] == premise.python_version
    assert observed["pandas_version"] == premise.pandas_version
    assert observed["numpy_version"] == premise.numpy_version
    assert observed["scipy_version"] == premise.scipy_version
    assert observed["python_dateutil_version"] == premise.python_dateutil_version
    assert observed["origin"] == str(Path(observed["site_packages"]) / "pandas" / "__init__.py")
    assert observed["artifacts"] == {
        "METADATA": premise.pandas_metadata_sha256,
        "RECORD": premise.pandas_record_sha256,
        "WHEEL": premise.pandas_wheel_sha256,
    }
    for field in (
        "record_rows",
        "hashed_regular_files",
        "unhashed_rows",
        "hashed_regular_bytes",
        "missing_hashed_files",
        "digest_mismatches",
    ):
        assert observed[field] == getattr(premise, field)
    assert PANDAS_DEVELOPMENT_RUNTIME_PREMISE_DIGEST == semantic_digest(asdict(premise))


def test_pinned_scipy_two_result_destructuring_and_attribute_agreement() -> None:
    probe = r"""
import json
import math
from scipy import stats

payload = {}
for name, result in (
    ("ttest_ind", stats.ttest_ind([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])),
    ("mannwhitneyu", stats.mannwhitneyu([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])),
):
    statistic, p_value = result
    payload[name] = {
        "length": len(result),
        "finite": math.isfinite(float(statistic)) and math.isfinite(float(p_value)),
        "statistic_equal": float(statistic) == float(result.statistic),
        "pvalue_equal": float(p_value) == float(result.pvalue),
    }
print(json.dumps(payload, sort_keys=True))
"""
    completed = subprocess.run(
        [str(_RUNTIME), "-I", "-c", probe],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "mannwhitneyu": {
            "finite": True,
            "length": 2,
            "pvalue_equal": True,
            "statistic_equal": True,
        },
        "ttest_ind": {
            "finite": True,
            "length": 2,
            "pvalue_equal": True,
            "statistic_equal": True,
        },
    }


def _runtime_projection(
    data_path: Path,
    *,
    group_column: str,
    value_column: str,
    operands: tuple[tuple[str, str], ...],
) -> dict[str, dict[str, object]]:
    probe = r"""
import json
import sys
import pandas as pd

frame = pd.read_csv(sys.argv[1])
group_column = sys.argv[2]
value_column = sys.argv[3]
specifications = json.loads(sys.argv[4])
result = {}
for key, projection in specifications:
    series = frame[frame[group_column] == key][value_column]
    if projection == "dropna":
        operand = series.dropna()
    elif projection in {"values", "values_alias"}:
        operand = series.values
    else:
        operand = series
    result[key] = {
        "indexes": [int(value) for value in series.index.tolist()],
        "values": [repr(float(value)) for value in operand.tolist()],
        "dtype": str(operand.dtype),
    }
print(json.dumps(result, sort_keys=True))
"""
    completed = subprocess.run(
        [
            str(_RUNTIME),
            "-I",
            "-c",
            probe,
            str(data_path),
            group_column,
            value_column,
            json.dumps(operands),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    return cast(dict[str, dict[str, object]], json.loads(completed.stdout))


@pytest.mark.parametrize(
    ("projection", "procedure", "keyword", "data"),
    [
        ("series", "ttest_ind", "", _COVERED_DATA),
        ("series", "ttest_ind", ", equal_var=False", _REPEATED_DATA),
        ("values", "ttest_ind", "", _COVERED_DATA),
        ("values_alias", "mannwhitneyu", ", alternative='two-sided'", _REPEATED_DATA),
        ("dropna", "mannwhitneyu", ", method='auto'", _COVERED_DATA),
        ("series", "mannwhitneyu", ", alternative='less'", _REPEATED_DATA),
        ("values_alias", "ttest_ind", ", alternative='greater'", _COVERED_DATA),
    ],
)
def test_seven_operation_named_sources_execute_and_match_rebuilt_operands(
    tmp_path: Path,
    projection: str,
    procedure: str,
    keyword: str,
    data: bytes,
) -> None:
    source = _source(projection=projection, procedure=procedure, keyword=keyword)
    context = _synthetic_context(source, data, procedure=f"scipy.stats.{procedure}")
    certificate, fact = _proposal_and_fact(context)
    case = tmp_path / f"{projection}-{procedure}"
    (case / "workflow").mkdir(parents=True)
    (case / "data").mkdir()
    (case / "results").mkdir()
    (case / "workflow/analysis.py").write_text(source, encoding="utf-8")
    (case / "data/input.csv").write_bytes(data)
    completed = subprocess.run(
        [str(_RUNTIME), "-I", "workflow/analysis.py"],
        cwd=case,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    assert [path.relative_to(case).as_posix() for path in (case / "results").rglob("*")] == [
        "results/report.md"
    ]
    descriptor = cast(PandasSourceDescriptor, certificate.obligation.pandas_source)
    runtime = _runtime_projection(
        case / "data/input.csv",
        group_column=descriptor.group_column,
        value_column=descriptor.value_column,
        operands=tuple((item.group_key, item.projection) for item in descriptor.operands),
    )
    for group in fact.groups:
        observed = runtime[group.group_key]
        assert observed["indexes"] == [index - 1 for index in group.row_indices]
        assert observed["values"] == list(group.cast_value_reprs)
        assert observed["dtype"] == fact.pandas_value_dtype


def test_all_seven_frozen_target_bytes_match_pandas_indexes_values_and_dtypes(
    project_root: Path,
) -> None:
    observed_rows: dict[str, tuple[int, int]] = {}
    observed_dtypes: dict[str, str | None] = {}
    for case_id in _TARGETS:
        case = project_root / _CENSUS / case_id
        context = _case_context(case)
        certificate, fact = _proposal_and_fact(context)
        descriptor = cast(PandasSourceDescriptor, certificate.obligation.pandas_source)
        runtime = _runtime_projection(
            case / "data/input.csv",
            group_column=descriptor.group_column,
            value_column=descriptor.value_column,
            operands=tuple((item.group_key, item.projection) for item in descriptor.operands),
        )
        lengths: list[int] = []
        for group in fact.groups:
            observed = runtime[group.group_key]
            assert observed["indexes"] == [index - 1 for index in group.row_indices]
            assert observed["values"] == list(group.cast_value_reprs)
            assert observed["dtype"] == fact.pandas_value_dtype
            lengths.append(len(group.row_indices))
        observed_rows[case_id] = cast(tuple[int, int], tuple(lengths))
        observed_dtypes[case_id] = fact.pandas_value_dtype
    assert observed_rows == {
        "0006": (15, 15),
        "0012": (8, 8),
        "0025": (12, 12),
        "0030": (15, 15),
        "0035": (10, 10),
        "0038": (25, 25),
        "0039": (10, 10),
    }
    assert observed_dtypes == {
        "0006": "float64",
        "0012": "int64",
        "0025": "float64",
        "0030": "int64",
        "0035": "float64",
        "0038": "float64",
        "0039": "float64",
    }


def test_all_63_amended_frozen_byte_siblings_refuse_analyzer_and_kernel(
    project_root: Path,
) -> None:
    observed: dict[tuple[str, str], tuple[tuple[str, ...], tuple[str, ...]]] = {}
    for case_id in _TARGETS:
        case = project_root / _CENSUS / case_id
        valid_context = _case_context(case)
        valid_certificate, valid_fact = _proposal_and_fact(valid_context)
        descriptor = cast(PandasSourceDescriptor, valid_certificate.obligation.pandas_source)
        original = (case / "data/input.csv").read_bytes()
        variants = _physical_siblings(
            original,
            value_column=descriptor.value_column,
            unit_column=valid_certificate.obligation.authorized_unit_column,
        )
        assert len(variants) == 9
        for name, sibling in variants.items():
            sibling_context = _case_context_with_data(case, sibling)
            analysis = analyze_dependence_growth_python(sibling_context)
            analyzer_reasons = analysis.abstention_reasons
            expected_analyzer = (
                ("pandas-dropna-not-proven",)
                if name == "missing_token"
                and any(item.projection == "dropna" for item in descriptor.operands)
                else ("pandas-material-domain-unproven",)
            )
            kernel_reasons = _coherent_material_kernel_failure(
                valid_context,
                valid_certificate,
                valid_fact,
                sibling_context,
            )
            assert analyzer_reasons == expected_analyzer
            assert kernel_reasons == ("pandas-material-domain",)
            observed[(case_id, name)] = (analyzer_reasons, kernel_reasons)
    assert len(observed) == 63


@pytest.mark.parametrize("token", sorted(PANDAS_3_0_5_DEFAULT_MISSING_TOKENS))
def test_complete_pandas_missing_token_vocabulary_refuses_both_paths(
    token: str,
) -> None:
    valid_context = _synthetic_context(_source())
    valid_certificate, valid_fact = _proposal_and_fact(valid_context)
    sibling = _replace_csv_cell(
        _COVERED_DATA,
        column="value",
        replacement=token.encode("ascii"),
    )
    sibling_context = _synthetic_context(_source(), sibling)
    analysis = analyze_dependence_growth_python(sibling_context)
    assert analysis.abstention_reasons == ("pandas-material-domain-unproven",)
    assert _coherent_material_kernel_failure(
        valid_context,
        valid_certificate,
        valid_fact,
        sibling_context,
    ) == ("pandas-material-domain",)


def test_dropna_missing_value_uses_only_the_specific_analyzer_reason() -> None:
    source = _source(projection="dropna")
    valid_context = _synthetic_context(source)
    valid_certificate, valid_fact = _proposal_and_fact(valid_context)
    sibling = _replace_csv_cell(_COVERED_DATA, column="value", replacement=b"NaN")
    sibling_context = _synthetic_context(source, sibling)
    assert analyze_dependence_growth_python(sibling_context).abstention_reasons == (
        "pandas-dropna-not-proven",
    )
    assert _coherent_material_kernel_failure(
        valid_context,
        valid_certificate,
        valid_fact,
        sibling_context,
    ) == ("pandas-material-domain",)


@pytest.mark.parametrize("value", ["0", "999", "0.0", "999.9", "7.1"])
def test_exact_number_grammar_boundaries_admit(value: str) -> None:
    data = _group_data("A", "B", (value, "1", "2", "3"))
    context = _synthetic_context(_source(), data)
    certificate, fact = _proposal_and_fact(context)
    finalized = _final_certificate(certificate, fact)
    verified, failures = _verify(finalized, fact, context)
    assert failures == ()
    assert verified is not None


@pytest.mark.parametrize(
    "value",
    [
        "1000",
        "00",
        ".1",
        "1.",
        "1.00",
        "-1",
        "+1",
        "1e2",
        "1_0",
        "inf",
        "Infinity",
        "999999999999999999999999999999999999999",
        "0.74391500080636083",
    ],
)
def test_exact_number_grammar_siblings_refuse_both_paths(value: str) -> None:
    valid_context = _synthetic_context(_source())
    valid_certificate, valid_fact = _proposal_and_fact(valid_context)
    sibling = _group_data("A", "B", (value, "1", "2", "3"))
    sibling_context = _synthetic_context(_source(), sibling)
    assert analyze_dependence_growth_python(sibling_context).abstention_reasons == (
        "pandas-material-domain-unproven",
    )
    assert _coherent_material_kernel_failure(
        valid_context,
        valid_certificate,
        valid_fact,
        sibling_context,
    ) == ("pandas-material-domain",)


@pytest.mark.parametrize(
    ("left_key", "right_key"),
    [("A", "B"), ("A1_", "B2"), ("A" * 32, "B" * 32)],
)
def test_exact_group_literal_boundaries_admit(left_key: str, right_key: str) -> None:
    source = _source_groups(left_key, right_key)
    data = _group_data(left_key, right_key, ("1", "2", "3", "4"))
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_synthetic_context(source, data))
    assert payload["outcome"] == "covered_negative"


@pytest.mark.parametrize(
    ("left_key", "right_key"),
    [
        ("1", "2"),
        ("01", "02"),
        ("True", "False"),
        ("tRuE", "fAlSe"),
        ("NA", "Good"),
        ("Infinity", "Good"),
        ("_A", "B"),
        ("A-B", "C"),
        ("A" * 33, "B"),
    ],
)
def test_numeric_boolean_missing_and_malformed_group_keys_refuse(
    left_key: str, right_key: str
) -> None:
    valid_context = _synthetic_context(_source())
    valid_certificate, valid_fact = _proposal_and_fact(valid_context)
    source = _source_groups(left_key, right_key)
    data = _group_data(left_key, right_key, ("1", "2", "3", "4"))
    sibling_context = _synthetic_context(source, data)
    assert analyze_dependence_growth_python(sibling_context).abstention_reasons == (
        "pandas-material-domain-unproven",
    )
    # The changed source is independently closed first; use its own descriptor is
    # impossible because the domain deliberately emits no proposal.  The direct
    # byte route is covered with the unchanged valid source and hostile group bytes.
    byte_sibling = _synthetic_context(
        _source(), _group_data(left_key, right_key, ("1", "2", "3", "4"))
    )
    assert _coherent_material_kernel_failure(
        valid_context,
        valid_certificate,
        valid_fact,
        byte_sibling,
    ) == ("pandas-material-domain",)


def test_header_cell_and_group_membership_material_siblings() -> None:
    valid_context = _synthetic_context(_source())
    valid_certificate, valid_fact = _proposal_and_fact(valid_context)
    invalid = {
        "duplicate_header": b"unit_id,arm,value,value\nu1,A,1,1\nu2,A,2,2\nu3,B,3,3\nu4,B,4,4",
        "case_colliding_header": b"unit_id,arm,Arm,value\nu1,A,A,1\nu2,A,A,2\nu3,B,B,3\nu4,B,B,4",
        "missing_header": b"unit_id,arm,other\nu1,A,1\nu2,A,2\nu3,B,3\nu4,B,4",
        "empty_header": b"unit_id,,value\nu1,A,1\nu2,A,2\nu3,B,3\nu4,B,4",
        "missing_token_header": b"unit_id,arm,value,NA\nu1,A,1,x\nu2,A,2,x\nu3,B,3,x\nu4,B,4,x",
        "whitespace_header": b"unit_id,arm,value, extra\nu1,A,1,x\nu2,A,2,x\nu3,B,3,x\nu4,B,4,x",
        "empty_unit": _replace_csv_cell(_COVERED_DATA, column="unit_id", replacement=b""),
        "empty_group": _replace_csv_cell(_COVERED_DATA, column="arm", replacement=b""),
        "empty_value": _replace_csv_cell(_COVERED_DATA, column="value", replacement=b""),
        "unit_whitespace": _replace_csv_cell(_COVERED_DATA, column="unit_id", replacement=b" u1"),
        "group_whitespace": _replace_csv_cell(_COVERED_DATA, column="arm", replacement=b"A "),
        "value_whitespace": _replace_csv_cell(_COVERED_DATA, column="value", replacement=b" 1"),
        "unexpected_group": _replace_csv_cell(_COVERED_DATA, column="arm", replacement=b"C"),
        "unit_missing_token": _replace_csv_cell(
            _COVERED_DATA,
            column="unit_id",
            replacement=b"NA",
        ),
        "other_missing_token": b"unit_id,arm,value,note\nu1,A,1,NA\nu2,A,2,x\nu3,B,3,x\nu4,B,4,x",
        "escape": _replace_csv_cell(_COVERED_DATA, column="unit_id", replacement=b"u\\1"),
    }
    observed: dict[str, tuple[str, ...]] = {}
    for name, data in invalid.items():
        sibling_context = _synthetic_context(_source(), data)
        analysis = analyze_dependence_growth_python(sibling_context)
        assert analysis.abstention_reasons == ("pandas-material-domain-unproven",)
        failures = _coherent_material_kernel_failure(
            valid_context,
            valid_certificate,
            valid_fact,
            sibling_context,
        )
        assert failures == ("pandas-material-domain",)
        observed[name] = failures
    assert set(observed) == set(invalid)


def test_changed_row_order_multiplicity_and_membership_are_byte_rederived() -> None:
    forms = {
        "row_order": b"unit_id,arm,value\nu2,A,2\nu1,A,1\nu4,B,4\nu3,B,3",
        "multiplicity": _REPEATED_DATA,
        "membership": b"unit_id,arm,value\nu1,B,1\nu2,A,2\nu3,B,3\nu4,A,4",
    }
    facts: dict[str, GroupValueSequenceFact] = {}
    outcomes: dict[str, str] = {}
    for name, data in forms.items():
        context = _synthetic_context(_source(), data)
        certificate, fact = _proposal_and_fact(context)
        facts[name] = fact
        outcomes[name] = DependenceRecognitionV2ShadowAdapter().inspect(context)["outcome"]
        finalized = _final_certificate(certificate, fact)
        verified, failures = _verify(finalized, fact, context)
        assert failures == ()
        assert verified is not None
        assert verified.fact is not fact
        assert verified.fact == fact
    assert facts["row_order"].groups[0].source_values == ("2", "1")
    assert facts["membership"].groups[0].row_indices == (2, 4)
    assert outcomes == {
        "row_order": "covered_negative",
        "multiplicity": "evaluation_candidate",
        "membership": "covered_negative",
    }


def test_pinned_runtime_reproduces_bool_numeric_object_and_precision_divergences(
    tmp_path: Path,
) -> None:
    probes = {
        "bool_group": b"unit_id,arm,value\nu1,True,1\nu2,True,2\nu3,False,3\nu4,False,4",
        "numeric_group": b"unit_id,arm,value\nu1,1,1\nu2,1,2\nu3,2,3\nu4,2,4",
        "huge_object": _group_data(
            "A",
            "B",
            ("999999999999999999999999999999999999999", "1", "2", "3"),
        ),
        "high_precision": _group_data("A", "B", ("0.74391500080636083", "1", "2", "3")),
    }
    probe_script = r"""
import json
import sys
import pandas as pd

frame = pd.read_csv(sys.argv[1])
payload = {
    "group_dtype": str(frame["arm"].dtype),
    "value_dtype": str(frame["value"].dtype),
    "string_selected": int((frame["arm"] == sys.argv[2]).sum()),
    "first_value_repr": repr(frame["value"].iloc[0]),
}
print(json.dumps(payload, sort_keys=True))
"""
    observed: dict[str, dict[str, object]] = {}
    for name, data in probes.items():
        path = tmp_path / f"{name}.csv"
        path.write_bytes(data)
        selected = "True" if name == "bool_group" else "1" if name == "numeric_group" else "A"
        completed = subprocess.run(
            [str(_RUNTIME), "-I", "-c", probe_script, str(path), selected],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert completed.returncode == 0, completed.stderr
        observed[name] = cast(dict[str, object], json.loads(completed.stdout))
    assert observed["bool_group"]["group_dtype"] == "bool"
    assert observed["bool_group"]["string_selected"] == 0
    assert observed["numeric_group"]["group_dtype"] == "int64"
    assert observed["numeric_group"]["string_selected"] == 0
    assert observed["huge_object"]["value_dtype"] == "object"
    assert observed["high_precision"]["value_dtype"] == "float64"
    assert observed["high_precision"]["first_value_repr"] != repr(float("0.74391500080636083"))
    for name, data in probes.items():
        source = (
            _source_groups("True", "False")
            if name == "bool_group"
            else _source_groups("1", "2")
            if name == "numeric_group"
            else _source()
        )
        assert analyze_dependence_growth_python(
            _synthetic_context(source, data)
        ).abstention_reasons == ("pandas-material-domain-unproven",)


def test_analyzer_and_kernel_independently_rederive_equal_package_identity() -> None:
    context = _synthetic_context(_source())
    source = context.documents[0]
    material = _data_material(context)
    analyzer_identity = _analyzer_pandas_package_identity(
        context,
        source_path=source.path,
        source_digest=source.content_digest,
        material=material,
    )
    kernel_identity = _kernel_pandas_package_identity(
        context.base_records,
        file_manifest_input=context.file_manifest_input,
        source_path=source.path,
        source_digest=source.content_digest,
        material=material,
    )
    assert analyzer_identity is not None
    assert kernel_identity is not None
    assert analyzer_identity == kernel_identity
    assert analyzer_identity is not kernel_identity
    assert analyzer_identity.regular_file_count == 3


def _manifest_bijection_sibling(case: str) -> FrozenInspectionContext:
    context = _synthetic_context(_source())
    entries = _manifest_entries(context)
    if case == "missing-entry":
        return replace(context, file_manifest_input=_manifest_input(entries[:-1]))
    if case == "extra-entry":
        extra = {
            "record_type": "file_record",
            "file_record_id": "file:g14:manifest-extra",
            "path": "extra/unbound.txt",
            "entry_kind": "regular_file",
            "byte_size": 0,
            "snapshot_ref": _snapshot_ref(context).to_dict(),
            "asset_identity_ref": {
                "record_type": "asset_identity",
                "record_id": "asset:g14:manifest-extra",
            },
        }
        return replace(context, file_manifest_input=_manifest_input([*entries, extra]))
    if case == "duplicate-entry":
        return replace(context, file_manifest_input=_manifest_input([*entries, entries[0]]))
    if case in {
        "path-mismatch",
        "kind-mismatch",
        "identity-reference-mismatch",
        "byte-size-mismatch",
        "snapshot-reference-mismatch",
    }:
        changed = copy.deepcopy(entries)
        target = changed[0]
        if case == "path-mismatch":
            target["path"] = "changed/path.txt"
        elif case == "kind-mismatch":
            target["entry_kind"] = "special"
        elif case == "identity-reference-mismatch":
            target["asset_identity_ref"] = {
                "record_type": "asset_identity",
                "record_id": "asset:g14:mismatch",
            }
        elif case == "byte-size-mismatch":
            target["byte_size"] = int(target["byte_size"]) + 1
        else:
            target["snapshot_ref"] = {
                "record_type": "repository_snapshot",
                "record_id": "snapshot:g14:mismatch",
            }
        return replace(context, file_manifest_input=_manifest_input(changed))
    if case == "malformed-line":
        return replace(context, file_manifest_input=_raw_manifest_input(b'{"broken"\n'))
    if case == "noncanonical-line":
        noncanonical = (json.dumps(entries[0], sort_keys=True) + "\n").encode("utf-8")
        remainder = b"".join(
            (canonical_json(entry) + "\n").encode("utf-8") for entry in entries[1:]
        )
        return replace(
            context,
            file_manifest_input=_raw_manifest_input(noncanonical + remainder),
        )
    if case == "missing-terminal-newline":
        manifest = context.file_manifest_input
        assert manifest is not None
        return replace(
            context,
            file_manifest_input=_raw_manifest_input(manifest.canonical_jsonl_bytes[:-1]),
        )
    if case == "missing-input":
        return replace(context, file_manifest_input=None)
    if case == "manifest-reference-mismatch":
        return replace(
            context,
            file_manifest_input=_manifest_input(entries, file_manifest_ref="other/files.jsonl"),
        )
    if case == "manifest-digest-mismatch":
        manifest = context.file_manifest_input
        assert manifest is not None
        return replace(context, file_manifest_input=_stale_manifest_digest(manifest))
    if case == "extra-base-record":
        return _add_base_file_without_manifest(context, path="extra/base-only.txt")
    if case == "duplicate-base-path":
        return _add_base_file_without_manifest(context, path=entries[0]["path"])
    if case == "identity-digest-mismatch":
        target_entry = next(item for item in entries if item["path"] == "workflow/analysis.py")
        identity_ref = target_entry["asset_identity_ref"]
        assert isinstance(identity_ref, dict)
        return _replace_base_payload(
            context,
            RecordRef("asset_identity", str(identity_ref["record_id"])),
            {
                "identity_evidence": {
                    "kind": "full_digest",
                    "digest": sha256_digest(b"different content"),
                }
            },
        )
    if case == "duplicate-identity-association":
        target_entry = next(item for item in entries if item["path"] == "data-description.md")
        file_ref = RecordRef("file_record", str(target_entry["file_record_id"]))
        duplicate_ref = RecordRef("asset_identity", "asset:g14:duplicate-association")
        duplicate = _record(
            duplicate_ref,
            {
                "record_type": "asset_identity",
                "asset_identity_id": duplicate_ref.record_id,
                "tier": "full_digest",
                "asset_ref": file_ref.to_dict(),
                "identity_evidence": {
                    "kind": "full_digest",
                    "digest": sha256_digest(b"duplicate association"),
                },
            },
        )
        return replace(context, base_records=(*context.base_records, duplicate))
    if case == "non-regular":
        return _synthetic_context(
            _source(), extra_inventory_entries=(("workflow/device", "special"),)
        )
    if case == "symlink":
        return _synthetic_context(
            _source(), extra_inventory_entries=(("workflow/linked.py", "symlink"),)
        )
    raise AssertionError(case)


@pytest.mark.parametrize(
    "case",
    [
        "missing-entry",
        "extra-entry",
        "duplicate-entry",
        "path-mismatch",
        "kind-mismatch",
        "identity-reference-mismatch",
        "byte-size-mismatch",
        "snapshot-reference-mismatch",
        "malformed-line",
        "noncanonical-line",
        "missing-terminal-newline",
        "missing-input",
        "manifest-reference-mismatch",
        "manifest-digest-mismatch",
        "extra-base-record",
        "duplicate-base-path",
        "identity-digest-mismatch",
        "duplicate-identity-association",
        "non-regular",
        "symlink",
    ],
)
def test_manifest_bijection_sibling_matrix_refuses_in_both_independent_paths(
    case: str,
) -> None:
    context = _manifest_bijection_sibling(case)
    _assert_both_package_identity_paths_refuse(context)
    assert analyze_dependence_growth_python(context).abstention_reasons == (
        "pandas-package-identity-unproven",
    )


def test_exact_shadow_record_omission_refuses_analyzer_kernel_and_adapter() -> None:
    complete = _synthetic_context(
        _source(), inventory_additions={"workflow/pandas.py": b"MARKER = 'fake'\n"}
    )
    shadow_file = next(
        record
        for record in complete.base_records
        if record.ref.record_type == "file_record"
        and json.loads(record.canonical_payload).get("path") == "workflow/pandas.py"
    )
    shadow_payload = cast(dict[str, Any], json.loads(shadow_file.canonical_payload))
    shadow_identity_ref = RecordRef(
        "asset_identity", str(shadow_payload["asset_identity_ref"]["record_id"])
    )
    complete_manifest = complete.file_manifest_input
    assert complete_manifest is not None
    assert analyze_dependence_growth_python(complete).abstention_reasons == (
        "pandas-package-identity-unproven",
    )

    omitted = replace(
        complete,
        base_records=tuple(
            record
            for record in complete.base_records
            if record.ref not in {shadow_file.ref, shadow_identity_ref}
        ),
    )
    assert len(complete.base_records) - len(omitted.base_records) == 2
    assert omitted.file_manifest_input is complete_manifest
    assert _snapshot_ref(omitted) == _snapshot_ref(complete)
    _assert_both_package_identity_paths_refuse(omitted)
    assert analyze_dependence_growth_python(omitted).abstention_reasons == (
        "pandas-package-identity-unproven",
    )
    adapter_payload = DependenceRecognitionV2ShadowAdapter().inspect(omitted)
    assert adapter_payload["outcome"] == "unsupported"
    assert adapter_payload["abstention_reasons"] == ["pandas-package-identity-unproven"]

    truncated_entries = [
        entry for entry in _manifest_entries(complete) if entry["path"] != "workflow/pandas.py"
    ]
    simulated_incomplete = replace(
        omitted,
        file_manifest_input=_manifest_input(truncated_entries),
    )
    proposed, _old_fact = _proposal_and_fact(simulated_incomplete)
    proposed_source = proposed.obligation.pandas_source
    assert proposed_source is not None
    claimed_identity = replace(
        proposed_source.package_identity,
        file_manifest_digest=complete_manifest.manifest_digest,
    )
    assert isinstance(claimed_identity, PandasPackageIdentity)
    claimed_source = replace(proposed_source, package_identity=claimed_identity)
    claimed_obligation = replace(proposed.obligation, pandas_source=claimed_source)
    fact, reason = prove_group_value_sequences_with_reason(
        _data_material(omitted), obligation=claimed_obligation
    )
    assert reason is None
    assert fact is not None
    hand_built = _final_certificate(
        replace(proposed, obligation=claimed_obligation),
        fact,
    )
    failures: list[str] = []
    verified = verify_dependence_growth_certificate(
        hand_built,
        trusted_group_facts=(fact,),
        trusted_material_inputs=(_data_material(omitted),),
        trusted_authorizations=_trusted_v2_authorizations(omitted),
        trusted_procedure_sets=_trusted_v2_procedure_sets(omitted),
        trusted_base_records=omitted.base_records,
        trusted_file_manifest_input=complete_manifest,
        source_bytes=omitted.documents[0].content,
        _failure_reasons=failures,
    )
    assert verified is None
    assert failures == ["pandas-package-identity"]


@pytest.mark.parametrize(
    "path",
    [
        "pandas.py",
        "workflow/pandas.py",
        "pandas.pyc",
        "pandas/__init__.py",
        "workflow/pandas/__init__.py",
        "sitecustomize.py",
        "workflow/usercustomize.py",
        "customization.pth",
        "workflow/customization.pth",
    ],
)
def test_every_import_reachable_shadow_or_customization_route_refuses_before_source(
    path: str,
) -> None:
    hostile_source = _source().replace(
        "left = frame[frame['arm'] == 'A']['value']",
        "left = frame.groupby('arm')['value']",
    )
    context = _synthetic_context(
        hostile_source,
        inventory_additions={path: b"hostile = True\n"},
    )
    analysis = analyze_dependence_growth_python(context)
    assert analysis.abstention_reasons == ("pandas-package-identity-unproven",)
    source = context.documents[0]
    assert (
        _analyzer_pandas_package_identity(
            context,
            source_path=source.path,
            source_digest=source.content_digest,
            material=_data_material(context),
        )
        is None
    )
    assert (
        _kernel_pandas_package_identity(
            context.base_records,
            file_manifest_input=context.file_manifest_input,
            source_path=source.path,
            source_digest=source.content_digest,
            material=_data_material(context),
        )
        is None
    )


def test_symlink_incomplete_and_ambiguous_inventories_refuse_package_first() -> None:
    source = _source().replace(
        "left = frame[frame['arm'] == 'A']['value']",
        "left = frame.groupby('arm')['value']",
    )
    symlink_context = _synthetic_context(
        source,
        extra_inventory_entries=(("workflow/linked.py", "symlink"),),
    )
    base = _synthetic_context(source)
    description_record = next(
        record
        for record in base.base_records
        if record.ref.record_type == "file_record"
        and json.loads(record.canonical_payload).get("path") == "data-description.md"
    )
    incomplete_context = _replace_base_payload(
        base, description_record.ref, {"asset_identity_ref": None}
    )
    second_snapshot = _record(
        RecordRef("repository_snapshot", "snapshot:g14:ambiguous"),
        {
            "snapshot_id": "snapshot:g14:ambiguous",
            "snapshot_digest": base.snapshot_digest,
            "included_roots": ["."],
            "file_manifest_ref": "other/files.jsonl",
            "immutability": True,
            "extensions": {"x-material-full-digest-paths": []},
        },
    )
    ambiguous_context = replace(base, base_records=(*base.base_records, second_snapshot))
    snapshot_record = next(
        item for item in base.base_records if item.ref.record_type == "repository_snapshot"
    )
    no_manifest_context = _replace_base_payload(
        base, snapshot_record.ref, {"file_manifest_ref": ""}
    )
    source_file = base.documents[0].file_ref
    missing_source_context = replace(
        base,
        base_records=tuple(
            item
            for item in base.base_records
            if item.ref != source_file
            and not (
                item.ref.record_type == "asset_identity"
                and json.loads(item.canonical_payload).get("asset_ref") == source_file.to_dict()
            )
        ),
    )
    for context in (
        symlink_context,
        incomplete_context,
        ambiguous_context,
        no_manifest_context,
        missing_source_context,
    ):
        assert analyze_dependence_growth_python(context).abstention_reasons == (
            "pandas-package-identity-unproven",
        )


def test_legacy_context_without_complete_inventory_refuses_package_identity() -> None:
    complete = _synthetic_context(_source())
    required_material_refs = {
        ref
        for material in complete.material_inputs
        for ref in (material.file_ref, material.asset_identity_ref)
    }
    incomplete = replace(
        complete,
        base_records=tuple(
            record
            for record in complete.base_records
            if record.ref.record_type not in {"file_record", "asset_identity"}
            or record.ref in required_material_refs
        ),
    )
    assert analyze_dependence_growth_python(incomplete).abstention_reasons == (
        "pandas-package-identity-unproven",
    )


def test_hostile_adjacent_pandas_module_loads_normally_but_both_proofs_refuse(
    tmp_path: Path,
) -> None:
    case = tmp_path / "hostile-shadow"
    (case / "workflow").mkdir(parents=True)
    (case / "workflow/pandas.py").write_text("MARKER = 'fake'\n", encoding="ascii")
    control = case / "workflow/control.py"
    control.write_text(
        "import pandas\nprint(getattr(pandas, 'MARKER', 'real'))\nprint(pandas.__file__)\n",
        encoding="ascii",
    )
    ordinary = subprocess.run(
        [str(_RUNTIME), "workflow/control.py"],
        cwd=case,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    isolated = subprocess.run(
        [str(_RUNTIME), "-I", "workflow/control.py"],
        cwd=case,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert ordinary.returncode == isolated.returncode == 0
    assert ordinary.stdout.splitlines()[0] == "fake"
    assert ordinary.stdout.splitlines()[1].endswith("workflow/pandas.py")
    assert isolated.stdout.splitlines()[0] == "real"
    assert isolated.stdout.splitlines()[1].endswith("site-packages/pandas/__init__.py")

    context = _synthetic_context(
        _source(), inventory_additions={"workflow/pandas.py": b"MARKER = 'fake'\n"}
    )
    assert analyze_dependence_growth_python(context).abstention_reasons == (
        "pandas-package-identity-unproven",
    )
    valid_context = _synthetic_context(_source())
    proposal, fact = _proposal_and_fact(valid_context)
    finalized = _final_certificate(proposal, fact)
    failures: list[str] = []
    verified = verify_dependence_growth_certificate(
        finalized,
        trusted_group_facts=(fact,),
        trusted_material_inputs=(_data_material(valid_context),),
        trusted_authorizations=_trusted_v2_authorizations(valid_context),
        trusted_procedure_sets=_trusted_v2_procedure_sets(valid_context),
        trusted_base_records=context.base_records,
        trusted_file_manifest_input=context.file_manifest_input,
        source_bytes=valid_context.documents[0].content,
        _failure_reasons=failures,
    )
    assert verified is None
    assert failures == ["pandas-package-identity"]


@pytest.mark.parametrize(
    ("source", "reason"),
    [
        (
            _source().replace("import pandas as pd", "import pandas as panda"),
            "unsupported-import-form",
        ),
        (
            _source().replace("import pandas as pd", "from pandas import read_csv"),
            "unsupported-import-form",
        ),
        (
            _source().replace("import pandas as pd", "import pandas as pd\nimport pandas as pd"),
            "unsupported-import-form",
        ),
        (
            _source().replace("from scipy import stats", "from scipy import stats\npd = object()"),
            "unsupported-import-form",
        ),
        (
            _source().replace("pd.read_csv('data/input.csv')", "pd.read_csv('other.csv')"),
            "pandas-reader-form-unsupported",
        ),
        (
            _source().replace(
                "pd.read_csv('data/input.csv')", "pd.read_csv('data/input.csv', dtype=str)"
            ),
            "pandas-reader-form-unsupported",
        ),
        (
            _source().replace(
                "frame = pd.read_csv('data/input.csv')",
                "frame = pd.read_csv('data/input.csv')\nother = pd.read_csv('data/input.csv')",
            ),
            "pandas-reader-form-unsupported",
        ),
        (
            _source().replace(
                "frame = pd.read_csv('data/input.csv')",
                "reader = pd.read_csv\nframe = reader('data/input.csv')",
            ),
            "pandas-reader-form-unsupported",
        ),
        (
            _source().replace(
                "left = frame[frame['arm'] == 'A']['value']", "left = frame.groupby('arm')['value']"
            ),
            "pandas-frame-transform-not-closed",
        ),
        (
            _source().replace(
                "left = frame[frame['arm'] == 'A']['value']",
                "left = frame.loc[frame['arm'] == 'A', 'value']",
            ),
            "pandas-frame-transform-not-closed",
        ),
        (
            _source().replace(
                "frame = pd.read_csv('data/input.csv')",
                "frame = pd.read_csv('data/input.csv')\nframe = frame.sort_values('value')",
            ),
            "pandas-frame-transform-not-closed",
        ),
        (
            _source().replace("frame['arm'] == 'A'", "'A' == frame['arm']"),
            "pandas-operand-form-unsupported",
        ),
        (
            _source().replace("frame['arm'] == 'A'", "frame['arm'] == 'A' == True"),
            "pandas-operand-form-unsupported",
        ),
        (
            _source().replace("['value']\nright", "['value'][:]\nright"),
            "pandas-operand-form-unsupported",
        ),
        (
            _source().replace("['value']\nright", "['value'].to_numpy()\nright"),
            "pandas-operand-form-unsupported",
        ),
        (
            _source().replace("['value']\nright", "['value'].values()\nright"),
            "pandas-operand-form-unsupported",
        ),
        (
            _source(projection="dropna").replace(".dropna()", ".dropna(how='any')", 1),
            "pandas-operand-form-unsupported",
        ),
        (
            _source().replace("right = frame[frame['arm'] == 'B']['value']", "right = left"),
            "pandas-operand-form-unsupported",
        ),
        (
            _source().replace("statistic, p_value =", "statistic ="),
            "pandas-result-binding-unproven",
        ),
        (
            _source().replace("statistic, p_value =", "(statistic, nested), p_value ="),
            "pandas-result-binding-unproven",
        ),
        (
            _source().replace("statistic, p_value =", "statistic, *p_value ="),
            "pandas-result-binding-unproven",
        ),
        (
            _source().replace("statistic, p_value =", "statistic, statistic ="),
            "pandas-result-binding-unproven",
        ),
        (
            _source().replace("statistic, p_value =", "statistic = 0\nstatistic, p_value ="),
            "pandas-result-binding-unproven",
        ),
        (
            _source(
                projection="values",
                summaries="left_mean = left.median()\nright_mean = right.mean()",
            ),
            "pandas-summary-form-unsupported",
        ),
        (
            _source(summaries="left_mean = left.std(ddof=True)\nright_mean = right.mean()"),
            "pandas-summary-form-unsupported",
        ),
        (
            _source(summaries="left_mean = left.quantile()\nright_mean = right.mean()"),
            "pandas-summary-form-unsupported",
        ),
        (
            _source().replace("'results/report.md', 'w'", "'results/report.md', 'a'"),
            "pandas-sink-form-unsupported",
        ),
        (
            _source().replace("'results/report.md', 'w'", "'results/other.md', 'w'"),
            "pandas-sink-form-unsupported",
        ),
        (
            _source().replace("handle.write(report)", "handle.writelines(report)"),
            "pandas-sink-form-unsupported",
        ),
        (
            _source().replace(
                "handle.write(report)", "handle.write(report)\n    handle.write(report)"
            ),
            "pandas-sink-form-unsupported",
        ),
        (
            _source().replace("handle.write(report)", "alias = handle\n    handle.write(report)"),
            "pandas-sink-form-unsupported",
        ),
        ("def helper():\n    pass\n" + _source(), "pandas-script-function-not-closed"),
        (
            _source().replace(
                "frame = pd.read_csv",
                "for marker in [1]:\n    marker = marker\nframe = pd.read_csv",
            ),
            "pandas-script-shape-not-closed",
        ),
        (
            _source().replace("frame = pd.read_csv", "assert True\nframe = pd.read_csv"),
            "pandas-script-shape-not-closed",
        ),
        (
            _source().replace(
                "frame = pd.read_csv",
                "try:\n    marker = 1\nexcept Exception:\n    marker = 2\nframe = pd.read_csv",
            ),
            "pandas-script-shape-not-closed",
        ),
        (
            _source().replace(
                "frame = pd.read_csv",
                "match 1:\n    case 1:\n        marker = 1\nframe = pd.read_csv",
            ),
            "pandas-script-shape-not-closed",
        ),
        (
            _source().replace(
                "frame = pd.read_csv", "items = [x for x in [1]]\nframe = pd.read_csv"
            ),
            "pandas-script-shape-not-closed",
        ),
        (
            _source().replace(
                "frame = pd.read_csv", "if True:\n    marker = 1\nframe = pd.read_csv"
            ),
            "pandas-script-shape-not-closed",
        ),
        (
            _source().replace(
                "import pandas as pd", "import pandas as pd\nfrom __future__ import annotations"
            ),
            "python-parse-unsupported",
        ),
    ],
)
def test_source_category_siblings_have_exact_singleton_reasons(source: str, reason: str) -> None:
    analysis = analyze_dependence_growth_python(_synthetic_context(source))
    assert analysis.abstention_reasons == (reason,)


@pytest.mark.parametrize(
    ("insertion", "reason"),
    [
        ("counter = 0\ncounter += 1\n", "augmented-assignment-not-modeled"),
        ("marker: int = 1\n", "annotated-assignment-not-modeled"),
        ("marker = (captured := 1)\n", "named-expression-not-modeled"),
        ("marker = 1\ndel marker\n", "delete-not-modeled"),
        ("if True:\n    raise ValueError('stop')\n", "raise-guard-not-modeled"),
    ],
)
def test_shared_eager_source_reasons_retain_singleton_precedence(
    insertion: str, reason: str
) -> None:
    source = _source().replace(
        "frame = pd.read_csv('data/input.csv')",
        insertion + "frame = pd.read_csv('data/input.csv')",
    )
    assert analyze_dependence_growth_python(_synthetic_context(source)).abstention_reasons == (
        reason,
    )


def test_partition_is_the_only_operand_and_sink_classifier_definition(
    project_root: Path,
) -> None:
    analyzer_tree = ast.parse(
        (project_root / "src/sc_referee/dependence_recognition_v2/python_analyzer.py").read_text(
            encoding="utf-8"
        )
    )
    kernel_tree = ast.parse(
        (project_root / "src/sc_referee/dependence_recognition_v2/certificate.py").read_text(
            encoding="utf-8"
        )
    )
    analyzer_definitions = [
        node
        for node in ast.walk(analyzer_tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_partition_sink_bound_set"
    ]
    kernel_definitions = [
        node
        for node in ast.walk(kernel_tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_kernel_partition_body"
    ]
    assert len(analyzer_definitions) == len(kernel_definitions) == 1
    analyzer_partition_calls = {
        node.func.id
        for node in ast.walk(analyzer_definitions[0])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"_pandas_selections", "_pandas_procedure", "_pandas_writer"}
    }
    analyzer_all_calls = {
        node.func.id
        for node in ast.walk(analyzer_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"_pandas_selections", "_pandas_procedure", "_pandas_writer"}
    }
    assert (
        analyzer_partition_calls
        == analyzer_all_calls
        == {
            "_pandas_selections",
            "_pandas_procedure",
            "_pandas_writer",
        }
    )
    kernel_partition_replays = [
        node
        for node in ast.walk(kernel_definitions[0])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_kernel_pandas_source_replay"
    ]
    kernel_all_replays = [
        node
        for node in ast.walk(kernel_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_kernel_pandas_source_replay"
    ]
    assert len(kernel_partition_replays) == len(kernel_all_replays) == 1
    assert "pandas-binding-not-closed" not in DEPENDENCE_V2_REASON_REGISTRY


def test_outer_parse_package_and_import_precedence_is_total() -> None:
    compile_invalid = _source().replace(
        "import pandas as pd",
        "import pandas as pd\nfrom __future__ import annotations",
    )
    complete_invalid = _synthetic_context(compile_invalid)
    no_authority = replace(
        complete_invalid,
        base_records=tuple(
            record
            for record in complete_invalid.base_records
            if record.ref.record_type != "human_method_authorization"
        ),
    )
    no_material = replace(complete_invalid, material_inputs=())
    invalid_snapshot = next(
        record
        for record in complete_invalid.base_records
        if record.ref.record_type == "repository_snapshot"
    )
    no_inventory = _replace_base_payload(
        complete_invalid,
        invalid_snapshot.ref,
        {"file_manifest_ref": ""},
    )
    authority_analysis = analyze_dependence_growth_python(no_authority)
    assert authority_analysis.state == "question"
    assert authority_analysis.abstention_reasons == ()
    assert analyze_dependence_growth_python(no_material).abstention_reasons == (
        "authority-material-binding-mismatch",
    )
    assert analyze_dependence_growth_python(no_inventory).abstention_reasons == (
        "python-parse-unsupported",
    )

    bad_import = _synthetic_context(
        _source().replace("import pandas as pd", "import pandas as panda")
    )
    bad_snapshot = next(
        record
        for record in bad_import.base_records
        if record.ref.record_type == "repository_snapshot"
    )
    bad_import_no_inventory = _replace_base_payload(
        bad_import,
        bad_snapshot.ref,
        {"file_manifest_ref": ""},
    )
    assert analyze_dependence_growth_python(bad_import_no_inventory).abstention_reasons == (
        "pandas-package-identity-unproven",
    )


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("frame_alias", "group-container-aliased"),
        ("series_alias", "group-container-aliased"),
        ("frame_rebind", "operand-name-rebound"),
        ("series_rebind", "operand-name-rebound"),
        ("operand_mutation", "sink-mutates-operand-name"),
    ],
)
def test_single_partition_owns_alias_rebind_and_mutation_reasons(
    mutation: str, reason: str
) -> None:
    source = _source()
    if mutation == "frame_alias":
        source = source.replace("left = frame", "frame_alias = frame\nleft = frame", 1)
    elif mutation == "series_alias":
        source = source.replace("right = frame", "left_alias = left\nright = frame", 1)
    elif mutation == "frame_rebind":
        source = source.replace("left = frame", "frame = frame\nleft = frame", 1)
    elif mutation == "series_rebind":
        source = source.replace("right = frame", "left = left\nright = frame", 1)
    else:
        source = source.replace(
            "statistic, p_value =",
            "left.update(left)\nstatistic, p_value =",
            1,
        )
    assert analyze_dependence_growth_python(_synthetic_context(source)).abstention_reasons == (
        reason,
    )


@pytest.mark.parametrize(
    "source",
    [
        _source().replace("left = frame", "frame_alias = frame\nleft = frame", 1),
        _source().replace("right = frame", "left_alias = left\nright = frame", 1),
        _source().replace("left = frame", "frame = frame\nleft = frame", 1),
        _source().replace("right = frame", "left = left\nright = frame", 1),
        _source().replace(
            "statistic, p_value =",
            "left.update(left)\nstatistic, p_value =",
            1,
        ),
        _source().replace("stats.ttest_ind(left, right)", "stats.ttest_ind(left, left)"),
    ],
)
def test_direct_kernel_single_partition_owns_coordinated_lineage_siblings(
    source: str,
) -> None:
    valid_context = _synthetic_context(_source())
    proposal, _fact = _proposal_and_fact(valid_context)
    changed_context = _synthetic_context(source)
    changed_certificate, changed_fact = _changed_source_certificate(
        proposal,
        changed_context,
        replay_descriptor=True,
    )
    assert _verify(changed_certificate, changed_fact, changed_context)[1] == (
        "pandas-single-partition",
    )


def _kernel_mutations(
    certificate: DependenceGrowthCertificate,
    fact: GroupValueSequenceFact,
    material: FrozenMaterialInput,
    selected: tuple[str, ...],
) -> tuple[DependenceGrowthCertificate, GroupValueSequenceFact, FrozenMaterialInput]:
    mutated_certificate = certificate
    mutated_fact = fact
    mutated_material = material
    for name in selected:
        descriptor = cast(PandasSourceDescriptor, mutated_certificate.obligation.pandas_source)
        if name == "package_runtime":
            package = replace(
                descriptor.package_identity,
                runtime_premise_id="pandas-development-runtime-forged",
            )
            descriptor = replace(descriptor, package_identity=package)
            mutated_certificate = replace(
                mutated_certificate,
                obligation=replace(mutated_certificate.obligation, pandas_source=descriptor),
            )
        elif name == "package_inventory":
            package = replace(
                descriptor.package_identity,
                inventory_digest="sha256:" + "0" * 64,
            )
            descriptor = replace(descriptor, package_identity=package)
            mutated_certificate = replace(
                mutated_certificate,
                obligation=replace(mutated_certificate.obligation, pandas_source=descriptor),
            )
        elif name == "source_span":
            descriptor = replace(
                descriptor,
                import_span=(
                    descriptor.import_span[0] + 1,
                    *descriptor.import_span[1:],
                ),
            )
            mutated_certificate = replace(
                mutated_certificate,
                obligation=replace(mutated_certificate.obligation, pandas_source=descriptor),
            )
        elif name == "source_projection":
            first = descriptor.operands[0]
            descriptor = replace(
                descriptor,
                operands=(
                    replace(
                        first,
                        selection_span=(
                            first.selection_span[0],
                            first.selection_span[1] + 1,
                            *first.selection_span[2:],
                        ),
                    ),
                    descriptor.operands[1],
                ),
            )
            mutated_certificate = replace(
                mutated_certificate,
                obligation=replace(mutated_certificate.obligation, pandas_source=descriptor),
            )
        elif name == "partition_binding":
            first = mutated_certificate.operand_bindings[0]
            mutated_certificate = replace(
                mutated_certificate,
                operand_bindings=(
                    replace(first, argument_name="forged_operand"),
                    mutated_certificate.operand_bindings[1],
                ),
            )
        elif name == "partition_tokens":
            mutated_certificate = replace(
                mutated_certificate,
                operand_slice_statement_tokens=("forged-partition-token",),
            )
        elif name == "material_terminal":
            mutated_material = _stale_material(material, material.content + b"\n")
        elif name == "material_crlf":
            mutated_material = _stale_material(material, material.content.replace(b"\n", b"\r\n"))
        elif name == "operand_value":
            first_group = mutated_fact.groups[0]
            mutated_fact = replace(
                mutated_fact,
                groups=(
                    replace(
                        first_group,
                        source_values=("999", *first_group.source_values[1:]),
                    ),
                    *mutated_fact.groups[1:],
                ),
            )
        elif name == "operand_row":
            first_group = mutated_fact.groups[0]
            mutated_fact = replace(
                mutated_fact,
                groups=(
                    replace(
                        first_group,
                        row_indices=tuple(reversed(first_group.row_indices)),
                    ),
                    *mutated_fact.groups[1:],
                ),
            )
        elif name == "result_names":
            mutated_certificate = replace(
                mutated_certificate,
                result_names=tuple(reversed(mutated_certificate.result_names)),
            )
        elif name == "result_sink":
            mutated_certificate = replace(mutated_certificate, sink_token="selected-sink:forged")
        else:
            raise AssertionError(name)
    return mutated_certificate, mutated_fact, mutated_material


def test_twelve_kernel_bypasses_and_all_66_pairs_220_triples_are_singleton_preemptive() -> None:
    context = _synthetic_context(_source())
    proposal, fact = _proposal_and_fact(context)
    certificate = _final_certificate(proposal, fact)
    material = _data_material(context)
    stages = {
        "package_runtime": (0, "pandas-package-identity"),
        "package_inventory": (0, "pandas-package-identity"),
        "source_span": (1, "pandas-source-closure"),
        "source_projection": (1, "pandas-source-closure"),
        "partition_binding": (2, "pandas-single-partition"),
        "partition_tokens": (2, "pandas-single-partition"),
        "material_terminal": (3, "pandas-material-domain"),
        "material_crlf": (3, "pandas-material-domain"),
        "operand_value": (4, "pandas-operand-values"),
        "operand_row": (4, "pandas-operand-values"),
        "result_names": (5, "pandas-result-sink"),
        "result_sink": (5, "pandas-result-sink"),
    }
    names = tuple(stages)
    observed_counts: dict[int, int] = {}
    for cardinality in (1, 2, 3):
        observed_counts[cardinality] = 0
        for selected in combinations(names, cardinality):
            mutated_certificate, mutated_fact, mutated_material = _kernel_mutations(
                certificate, fact, material, selected
            )
            _verified, failures = _verify(
                mutated_certificate,
                mutated_fact,
                context,
                material=mutated_material,
            )
            expected_name = min(selected, key=lambda item: stages[item][0])
            assert failures == (stages[expected_name][1],), selected
            observed_counts[cardinality] += 1
    assert observed_counts == {1: 12, 2: 66, 3: 220}


def test_kernel_returns_only_its_distinct_byte_rederived_fact_object() -> None:
    context = _synthetic_context(_source(), _REPEATED_DATA)
    proposal, supplied_fact = _proposal_and_fact(context)
    certificate = _final_certificate(proposal, supplied_fact)
    verified, failures = _verify(certificate, supplied_fact, context)
    assert failures == ()
    assert verified is not None
    assert verified.fact == supplied_fact
    assert verified.fact is not supplied_fact
    rebuilt = _kernel_replay_pandas_group_fact(_data_material(context), certificate.obligation)
    assert rebuilt == verified.fact
    assert rebuilt is not verified.fact
    assert verified.conclusion == "repeated_units"
    assert verified.certificate_id == _growth_certificate_identity(
        certificate, verified.fact, verified.conclusion
    )


def test_forged_covered_and_adverse_facts_refuse_at_operand_values() -> None:
    repeated_context = _synthetic_context(_source(), _REPEATED_DATA)
    repeated_proposal, repeated_fact = _proposal_and_fact(repeated_context)
    repeated_certificate = _final_certificate(repeated_proposal, repeated_fact)
    first_repeated_group = repeated_fact.groups[0]
    forged_covered = replace(
        repeated_fact,
        groups=(
            replace(
                first_repeated_group,
                authorized_unit_ids=tuple(
                    f"unit-key:forged-{index}"
                    for index in range(len(first_repeated_group.authorized_unit_ids))
                ),
            ),
            *repeated_fact.groups[1:],
        ),
    )
    assert _verify(repeated_certificate, forged_covered, repeated_context)[1] == (
        "pandas-operand-values",
    )

    unique_context = _synthetic_context(_source(), _COVERED_DATA)
    unique_proposal, unique_fact = _proposal_and_fact(unique_context)
    unique_certificate = _final_certificate(unique_proposal, unique_fact)
    first_unique_group = unique_fact.groups[0]
    forged_adverse = replace(
        unique_fact,
        groups=(
            replace(
                first_unique_group,
                authorized_unit_ids=(
                    first_unique_group.authorized_unit_ids[0],
                    first_unique_group.authorized_unit_ids[0],
                ),
            ),
            *unique_fact.groups[1:],
        ),
    )
    assert _verify(unique_certificate, forged_adverse, unique_context)[1] == (
        "pandas-operand-values",
    )


def test_fact_reference_mutation_preempts_operand_and_result_mutations() -> None:
    context = _synthetic_context(_source())
    proposal, fact = _proposal_and_fact(context)
    certificate = _final_certificate(proposal, fact)
    forged_fact = replace(
        fact,
        file_ref=replace(fact.file_ref, record_id="file:forged"),
        groups=(
            replace(fact.groups[0], row_indices=tuple(reversed(fact.groups[0].row_indices))),
            *fact.groups[1:],
        ),
    )
    forged_certificate = replace(
        certificate, result_names=tuple(reversed(certificate.result_names))
    )
    assert _verify(forged_certificate, forged_fact, context)[1] == ("pandas-material-domain",)


def test_hidden_dataframe_transform_cannot_be_omitted_from_source_descriptor() -> None:
    valid_context = _synthetic_context(_source())
    proposal, fact = _proposal_and_fact(valid_context)
    transformed_source = _source().replace(
        "frame = pd.read_csv('data/input.csv')",
        "frame = pd.read_csv('data/input.csv')\nframe = frame.sort_values('value')",
    )
    changed_context = _synthetic_context(transformed_source)
    hidden, changed_fact = _changed_source_certificate(
        proposal, changed_context, replay_descriptor=False
    )
    assert changed_fact.groups == fact.groups
    assert _verify(hidden, changed_fact, changed_context)[1] == ("pandas-source-closure",)


@pytest.mark.parametrize(
    ("source", "analyzer_reason"),
    [
        (
            _source().replace(
                "from scipy import stats",
                "from scipy import stats\n\nopen = 'collision'",
            ),
            "pandas-sink-form-unsupported",
        ),
        (
            _source(
                projection="values",
                summaries="left_mean = left.median()\nright_mean = right.mean()",
            ),
            "pandas-summary-form-unsupported",
        ),
        (
            _source(summaries="left_mean = left.std(ddof=True)\nright_mean = right.mean()"),
            "pandas-summary-form-unsupported",
        ),
    ],
)
def test_result_sink_bypasses_refuse_at_the_last_fixed_kernel_obligation(
    source: str, analyzer_reason: str
) -> None:
    valid_context = _synthetic_context(_source())
    proposal, _fact = _proposal_and_fact(valid_context)
    changed_context = _synthetic_context(source)
    assert analyze_dependence_growth_python(changed_context).abstention_reasons == (
        analyzer_reason,
    )
    changed_certificate, changed_fact = _changed_source_certificate(
        proposal, changed_context, replay_descriptor=True
    )
    assert _verify(changed_certificate, changed_fact, changed_context)[1] == ("pandas-result-sink",)


@pytest.mark.parametrize(
    ("descriptor_mutation", "expected_obligation"),
    [
        ("frame", "pandas-single-partition"),
        ("base_series", "pandas-single-partition"),
        ("operand_name", "pandas-single-partition"),
        ("group_column", "pandas-source-closure"),
        ("value_column", "pandas-source-closure"),
        ("group_literal", "pandas-source-closure"),
        ("projection", "pandas-source-closure"),
        ("omitted_operand", "pandas-source-closure"),
        ("procedure_target_span", "pandas-source-closure"),
        ("writer_span", "pandas-source-closure"),
        ("procedure_result_names", "pandas-result-sink"),
        ("writer_handle", "pandas-result-sink"),
    ],
)
def test_hand_built_source_descriptor_bypasses_route_to_the_exact_fixed_obligation(
    descriptor_mutation: str,
    expected_obligation: str,
) -> None:
    context = _synthetic_context(_source())
    proposal, fact = _proposal_and_fact(context)
    descriptor = cast(PandasSourceDescriptor, proposal.obligation.pandas_source)
    if descriptor_mutation == "frame":
        descriptor = replace(descriptor, frame_name="other_frame")
    elif descriptor_mutation == "base_series":
        descriptor = replace(
            descriptor,
            operands=(
                replace(descriptor.operands[0], base_series_name="other_base"),
                descriptor.operands[1],
            ),
        )
    elif descriptor_mutation == "operand_name":
        descriptor = replace(
            descriptor,
            operands=(
                replace(descriptor.operands[0], operand_name="other_operand"),
                descriptor.operands[1],
            ),
        )
    elif descriptor_mutation == "group_column":
        descriptor = replace(descriptor, group_column="other_group")
    elif descriptor_mutation == "value_column":
        descriptor = replace(descriptor, value_column="other_value")
    elif descriptor_mutation == "group_literal":
        descriptor = replace(
            descriptor,
            operands=(
                replace(descriptor.operands[0], group_key="C"),
                descriptor.operands[1],
            ),
        )
    elif descriptor_mutation == "projection":
        descriptor = replace(
            descriptor,
            operands=(
                replace(descriptor.operands[0], projection="values"),
                descriptor.operands[1],
            ),
        )
    elif descriptor_mutation == "omitted_operand":
        descriptor = replace(descriptor, operands=descriptor.operands[:1])
    elif descriptor_mutation == "procedure_target_span":
        descriptor = replace(descriptor, procedure_target_span=(0, 0, 0, 0))
    elif descriptor_mutation == "writer_span":
        descriptor = replace(descriptor, writer_span=(0, 0, 0, 0))
    elif descriptor_mutation == "procedure_result_names":
        descriptor = replace(descriptor, procedure_result_names=("other", "names"))
    else:
        descriptor = replace(descriptor, writer_handle="other_handle")
    forged = replace(
        proposal,
        obligation=replace(proposal.obligation, pandas_source=descriptor),
    )
    forged_fact = fact
    if expected_obligation == "pandas-result-sink":
        rebuilt, reason = prove_group_value_sequences_with_reason(
            _data_material(context),
            obligation=forged.obligation,
        )
        assert reason is None
        assert rebuilt is not None
        forged_fact = rebuilt
    assert _verify(forged, forged_fact, context)[1] == (expected_obligation,)


def test_35_alias_rebind_mutation_and_lineage_siblings_all_fail_closed() -> None:
    base = _source()

    def before_procedure(statement: str) -> str:
        return base.replace("statistic, p_value =", f"{statement}\nstatistic, p_value =", 1)

    sources = [
        before_procedure(f"left.{method}()")
        for method in (
            "drop",
            "dropna",
            "fillna",
            "rename",
            "sort_values",
            "update",
            "insert",
            "pop",
            "set_index",
            "reset_index",
            "clear",
            "extend",
        )
    ]
    sources.extend(
        (
            before_procedure("left.dropna(inplace=True)"),
            before_procedure("left.fillna(0, inplace=True)"),
            base.replace("left = frame", "frame_alias = frame\nleft = frame", 1),
            base.replace("right = frame", "left_alias = left\nright = frame", 1),
            before_procedure("right_alias = right"),
            base.replace("left = frame", "frame = frame\nleft = frame", 1),
            base.replace("right = frame", "left = left\nright = frame", 1),
            before_procedure("right = right"),
            before_procedure("frame.marker = 1"),
            before_procedure("left.marker = 1"),
            before_procedure("left[0] = 1"),
            before_procedure("frame['value'] = 1"),
            before_procedure("del left"),
            before_procedure("del frame"),
            before_procedure("print(left)"),
            before_procedure("escaped = list(left)"),
            before_procedure("escaped = tuple(left)"),
            before_procedure("escaped = consume(left)"),
            base.replace("['value']\nright", "['value'].values()\nright", 1),
            base.replace("['value']\nright", "['value'].to_numpy()\nright", 1),
            _source(projection="dropna").replace(".dropna()", ".dropna(how='any')", 1),
            base.replace(
                "right = frame[frame['arm'] == 'B']['value']",
                "right = frame[frame['arm'] == 'B']['value']\n"
                "third = frame[frame['arm'] == 'C']['value']",
                1,
            ),
            base.replace(
                "left = frame[frame['arm'] == 'A']['value']",
                "left = other_frame[other_frame['arm'] == 'A']['value']",
                1,
            ),
        )
    )
    assert len(sources) == 35
    observed: list[tuple[str, ...]] = []
    for source in sources:
        context = _synthetic_context(source)
        analysis = analyze_dependence_growth_python(context)
        payload = DependenceRecognitionV2ShadowAdapter().inspect(context)
        assert analysis.state == "unsupported"
        assert len(analysis.abstention_reasons) == 1
        assert payload["outcome"] == "unsupported"
        assert payload["abstention_reasons"] != ["v2-shadow-pipeline-exception"]
        observed.append(analysis.abstention_reasons)
    assert len(observed) == 35


@pytest.mark.parametrize(
    ("node_class", "snippet", "reason"),
    [
        ("For", "for item in [1]:\n    marker = item", "pandas-script-shape-not-closed"),
        ("AsyncFor", "async for item in stream:\n    marker = item", "python-parse-unsupported"),
        ("While", "while False:\n    marker = 1", "pandas-script-shape-not-closed"),
        ("Assert", "assert True", "pandas-script-shape-not-closed"),
        (
            "Try",
            "try:\n    marker = 1\nexcept Exception:\n    marker = 2",
            "pandas-script-shape-not-closed",
        ),
        (
            "TryStar",
            "try:\n    marker = 1\nexcept* Exception:\n    marker = 2",
            "pandas-script-shape-not-closed",
        ),
        ("Match", "match 1:\n    case 1:\n        marker = 1", "pandas-script-shape-not-closed"),
        ("Lambda", "marker = lambda: 1", "pandas-script-shape-not-closed"),
        ("ListComp", "marker = [item for item in [1]]", "pandas-script-shape-not-closed"),
        ("SetComp", "marker = {item for item in [1]}", "pandas-script-shape-not-closed"),
        ("DictComp", "marker = {item: item for item in [1]}", "pandas-script-shape-not-closed"),
        ("GeneratorExp", "marker = (item for item in [1])", "pandas-script-shape-not-closed"),
        ("Yield", "yield 1", "python-parse-unsupported"),
        ("YieldFrom", "yield from []", "python-parse-unsupported"),
        ("Await", "await operation", "python-parse-unsupported"),
        ("Global", "global marker", "pandas-script-shape-not-closed"),
        ("Nonlocal", "nonlocal marker", "python-parse-unsupported"),
        ("If", "if True:\n    marker = 1", "pandas-script-shape-not-closed"),
    ],
)
def test_all_eighteen_default_deny_ast_classes(node_class: str, snippet: str, reason: str) -> None:
    source = _source().replace(
        "frame = pd.read_csv('data/input.csv')",
        snippet + "\nframe = pd.read_csv('data/input.csv')",
    )
    tree = ast.parse(source)
    assert any(type(node).__name__ == node_class for node in ast.walk(tree))
    assert analyze_dependence_growth_python(_synthetic_context(source)).abstention_reasons == (
        reason,
    )


def _row8_pair_source(selected: frozenset[str]) -> str:
    reader_path = "other.csv" if "reader" in selected else "data/input.csv"
    frame_wall = "frame = frame.sort_values('value')\n" if "frame" in selected else ""
    generic_wall = "for marker in [1]:\n    marker = marker\n" if "generic" in selected else ""
    left = (
        "left = frame['value']"
        if "operand" in selected
        else "left = frame[frame['arm'] == 'A']['value']"
    )
    target = "statistic" if "result" in selected else "statistic, p_value"
    summary = "left_mean = left.quantile()" if "summary" in selected else "left_mean = left.mean()"
    mode = "a" if "sink" in selected else "w"
    return (
        "import pandas as pd\n"
        "from scipy import stats\n\n"
        f"frame = pd.read_csv('{reader_path}')\n"
        f"{frame_wall}{generic_wall}"
        f"{left}\n"
        "right = frame[frame['arm'] == 'B']['value']\n"
        f"{target} = stats.ttest_ind(left, right)\n"
        f"{summary}\n"
        "right_mean = right.mean()\n"
        "report = f'stat={statistic} p={p_value} left={left_mean} right={right_mean}'\n"
        f"with open('results/report.md', '{mode}') as handle:\n"
        "    handle.write(report)\n"
    )


def test_all_21_row8_category_pairs_use_the_first_fixed_category() -> None:
    categories = (
        ("reader", "pandas-reader-form-unsupported"),
        ("frame", "pandas-frame-transform-not-closed"),
        ("generic", "pandas-script-shape-not-closed"),
        ("operand", "pandas-operand-form-unsupported"),
        ("result", "pandas-result-binding-unproven"),
        ("summary", "pandas-summary-form-unsupported"),
        ("sink", "pandas-sink-form-unsupported"),
    )
    observed = 0
    for first_index, second_index in combinations(range(len(categories)), 2):
        selected = frozenset({categories[first_index][0], categories[second_index][0]})
        analysis = analyze_dependence_growth_python(_synthetic_context(_row8_pair_source(selected)))
        assert analysis.abstention_reasons == (categories[first_index][1],), selected
        observed += 1
    assert observed == 21


@pytest.mark.parametrize(
    ("projection", "procedure", "keyword", "data", "outcome"),
    [
        ("series", "ttest_ind", "", _COVERED_DATA, "covered_negative"),
        ("series", "ttest_ind", ", equal_var=False", _REPEATED_DATA, "evaluation_candidate"),
        ("values", "ttest_ind", "", _COVERED_DATA, "covered_negative"),
        (
            "values_alias",
            "mannwhitneyu",
            ", alternative='two-sided'",
            _REPEATED_DATA,
            "evaluation_candidate",
        ),
        ("dropna", "mannwhitneyu", ", method='auto'", _COVERED_DATA, "covered_negative"),
        ("series", "mannwhitneyu", ", alternative='less'", _REPEATED_DATA, "evaluation_candidate"),
        ("values_alias", "ttest_ind", ", alternative='greater'", _COVERED_DATA, "covered_negative"),
    ],
)
def test_seven_operation_named_source_forms_analyze(
    projection: str,
    procedure: str,
    keyword: str,
    data: bytes,
    outcome: str,
) -> None:
    context = _synthetic_context(
        _source(projection=projection, procedure=procedure, keyword=keyword),
        data,
        procedure=f"scipy.stats.{procedure}",
    )
    payload = DependenceRecognitionV2ShadowAdapter().inspect(context)
    assert payload["outcome"] == outcome, payload


def test_cross_operand_unit_control_remains_unsupported() -> None:
    context = _synthetic_context(_source(), _CROSS_DATA)
    payload = DependenceRecognitionV2ShadowAdapter().inspect(context)
    assert payload["outcome"] == "unsupported"
    assert payload["abstention_reasons"] == ["unit-spans-multiple-operands"]
