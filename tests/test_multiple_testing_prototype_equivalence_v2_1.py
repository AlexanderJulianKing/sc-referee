from __future__ import annotations

import ast
import csv
import importlib.util
import io
import json
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_1 as final
from sc_referee.core.ids import sha256_digest

_RECON = Path("evaluation/development/multitest-recall-recon-corpus20")
_CORPUS = Path("evaluation/development/multitest-open-corpus-v1")


def _prototype() -> ModuleType:
    path = _RECON / "amended_dataflow_v2.py"
    spec = importlib.util.spec_from_file_location("multitest_recon_amended_v2", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _finite(value: str) -> bool:
    try:
        number = float(value)
    except ValueError:
        return False
    return number == number and number not in {float("inf"), float("-inf")}


def _inputs(spec: str) -> dict[str, object]:
    case = _CORPUS / "cases" / spec
    csv_content = (case / "data.csv").read_bytes()
    rows = list(csv.reader(io.StringIO(csv_content.decode("utf-8"))))
    header = tuple(rows[0])
    counts = Counter(row[1] for row in rows[1:])
    return {
        "content": (case / "analysis.py").read_bytes(),
        "authorized_path": "data.csv",
        "group_column": header[1],
        "outcome_columns": tuple(
            column
            for index, column in enumerate(header)
            if index not in {0, 1} and all(_finite(row[index]) for row in rows[1:])
        ),
        "csv_header": header,
        "group_values": tuple(sorted(counts, key=lambda value: value.encode("utf-8"))),
        "csv_content": csv_content,
    }


def _nodes(scope: tuple[ast.stmt, ...], node_type: type[ast.AST]) -> dict[tuple[int, int], ast.AST]:
    return {
        (node.lineno, node.col_offset): node
        for statement in scope
        for node in ast.walk(statement)
        if isinstance(node, node_type)
    }


def test_frozen_r1_r2_r3b_prototype_and_final_classifiers_are_extensionally_equal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert sha256_digest((_RECON / "amend_build.py").read_bytes()) == (
        "sha256:904bcf01e15dfa02d46b00658241b2b0fd4fcb9199e1a64e823a47bdbea47162"
    )
    assert sha256_digest((_RECON / "amended_dataflow_v2.py").read_bytes()) == (
        "sha256:f78b09c5bf33cda865753214553445ed48de1bd68b1a74a50ad5756b144f28c0"
    )
    monkeypatch.setenv("MT_AMEND", "A1,A2,A3")
    prototype = _prototype()
    labels = json.loads((_CORPUS / "specs" / "labels.json").read_text(encoding="utf-8"))
    prototype_candidates: set[str] = set()
    compared_percent_nodes = 0
    compared_rendering_ifs = 0
    direct_sink_if_inventory = 0

    for spec in sorted(labels):
        raw_tree = ast.parse((_CORPUS / "cases" / spec / "analysis.py").read_bytes())
        direct_sink_if_inventory += sum(
            isinstance(node, ast.If)
            and len(node.body) == len(node.orelse) == 1
            and all(
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Call)
                and isinstance(statement.value.func, ast.Name)
                and statement.value.func.id == "print"
                for statement in (*node.body, *node.orelse)
            )
            for node in ast.walk(raw_tree)
        )
        prototype_engines: list[Any] = []
        final_engines: list[Any] = []
        prototype_init = prototype._MtEngine.__init__
        final_init = final._MtEngine.__init__

        def capture_prototype(
            self: Any,
            *args: Any,
            _init: Any = prototype_init,
            _engines: list[Any] = prototype_engines,
            **kwargs: Any,
        ) -> None:
            _init(self, *args, **kwargs)
            _engines.append(self)

        def capture_final(
            self: Any,
            *args: Any,
            _init: Any = final_init,
            _engines: list[Any] = final_engines,
            **kwargs: Any,
        ) -> None:
            _init(self, *args, **kwargs)
            _engines.append(self)

        monkeypatch.setattr(prototype._MtEngine, "__init__", capture_prototype)
        monkeypatch.setattr(final._MtEngine, "__init__", capture_final)
        prototype_result = prototype.analyze_code_csv_multiple_testing_dataflow(**_inputs(spec))
        final.analyze_code_csv_multiple_testing_dataflow(**_inputs(spec))
        monkeypatch.setattr(prototype._MtEngine, "__init__", prototype_init)
        monkeypatch.setattr(final._MtEngine, "__init__", final_init)

        if (
            prototype_result.reason is None
            and prototype_result.facts.correction_classification != "complete"
        ):
            prototype_candidates.add(spec)
        assert len(prototype_engines) <= 1
        assert len(final_engines) <= 1
        if not prototype_engines or not final_engines:
            continue
        p_engine = prototype_engines[0]
        f_engine = final_engines[0]

        p_bins = _nodes(p_engine.scope, ast.BinOp)
        f_bins = _nodes(f_engine.scope, ast.BinOp)
        shared_bins = set(p_bins) & set(f_bins)
        p_percent = {
            position
            for position in shared_bins
            if f_engine._p_origins(f_bins[position].right)
            if prototype._MtEngine._amend_presentation_percent(p_engine, p_bins[position])
        }
        f_percent = {
            position
            for position in shared_bins
            if f_engine._literal_percent_presentation(f_bins[position])
        }
        assert p_percent == f_percent
        compared_percent_nodes += len(p_percent)

        p_ifs = _nodes(p_engine.scope, ast.If)
        f_ifs = _nodes(f_engine.scope, ast.If)
        shared_ifs = set(p_ifs) & set(f_ifs)
        p_rendering = {
            position
            for position in shared_ifs
            if prototype._MtEngine._amend_terminal_rendering_if(p_engine, p_ifs[position])
        }
        f_rendering = {
            position
            for position in shared_ifs
            if f_engine._mt_v21_terminal_rendering_if(f_ifs[position]) is not None
        }
        # The corpus-wide prototype did not segment repeated assigned verdict
        # names (R12); compare its applicable nodes, while the final classifier
        # is allowed to reach the separately reviewed R12 copies.
        assert p_rendering <= f_rendering
        compared_rendering_ifs += len(p_rendering)

    assert prototype_candidates == {"spec-19", "spec-33"}
    assert not {spec for spec in prototype_candidates if labels[spec]["label"] == "correct"}
    assert compared_percent_nodes > 0
    assert compared_rendering_ifs == 7
    assert direct_sink_if_inventory == 13


def test_r2_r3b_classifier_is_used_by_both_hierarchy_and_conclusion_registries() -> None:
    tree = ast.parse(Path(final.__file__).read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_mt_v21_terminal_rendering_if"
    ]
    assert len(calls) == 2
