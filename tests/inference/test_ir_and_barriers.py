from __future__ import annotations

from pathlib import Path


def _request(*sources):
    from sc_referee.inference.api import AnalysisRequest

    return AnalysisRequest(sources=tuple(sources))


def test_analyze_is_parse_only_and_emits_only_abstain(tmp_path):
    from sc_referee.inference import analyze

    sentinel = tmp_path / "must-not-exist"
    source = f"open({str(sentinel)!r}, 'w').write('executed')\nx = 1\n"
    snapshot = analyze(_request(source))

    assert snapshot.outcome == "ABSTAIN"
    assert not sentinel.exists()
    assert snapshot.program.sources[0].original == source


def test_frontend_reuses_source_ast_normalization_and_callsite_ids():
    import json

    from sc_referee.inference import analyze
    from sc_referee.source_ast import iter_call_sites, parse_sources

    notebook = json.dumps({"cells": [{"cell_type": "code", "source": [
        "%matplotlib inline\n", "import scanpy as sc\n",
        "sc.tl.rank_genes_groups(adata, groupby='g')\n",
    ]}]})
    snapshot = analyze(_request(notebook))

    expected = [site.id for site in iter_call_sites(parse_sources([notebook]))]
    assert [call.callsite_id for call in snapshot.program.calls] == expected
    assert snapshot.program.sources[0].parsed.tree is not None


def test_cfg_and_value_ssa_are_deterministic_and_merge_with_phi():
    from sc_referee.inference import analyze

    source = "x = 0\nif flag:\n    x = 1\nelse:\n    x = 2\ny = x\n"
    first = analyze(_request(source)).program
    second = analyze(_request(source)).program

    assert first == second
    assert len(first.cfg.blocks) >= 5
    assert any(len(block.successors) == 2 for block in first.cfg.blocks.values())
    phis = [instruction for block in first.cfg.blocks.values()
            for instruction in block.instructions if instruction.op == "phi"]
    assert len(phis) == 1
    assert phis[0].target == "x"
    assert len(phis[0].operands) == 2
    y_def = next(definition for definition in first.value_definitions.values()
                 if definition.variable == "y")
    assert y_def.dependencies == (phis[0].result,)


def test_literal_fields_receive_memory_ssa_versions():
    from sc_referee.inference import analyze

    program = analyze(_request(
        "adata.obs['group'] = labels\na = adata.obs['group']\nadata.obs[key] = other\n"
    )).program

    exact = [version for version in program.memory_versions.values()
             if version.field == "group"]
    dynamic = [version for version in program.memory_versions.values()
               if version.field == "<unknown-field>"]
    assert exact and exact[0].strong_update is True
    assert dynamic and dynamic[0].strong_update is False


def test_every_unsupported_or_unparsed_construct_is_an_explicit_barrier():
    from sc_referee.inference import analyze

    snapshot = analyze(_request(
        "f = lambda x: x\nvalue = eval(code)\n",
        "def broken(:\n",
        "async def work():\n    await task()\n",
    ))
    kinds = {barrier.kind for barrier in snapshot.program.barriers}

    assert "unsupported_syntax" in kinds
    assert "dynamic_execution" in kinds
    assert "parse_error" in kinds
    assert snapshot.coverage.complete is False
    assert all(barrier.id and barrier.span.source_index >= 0 for barrier in snapshot.program.barriers)


def test_r_and_reflection_boundaries_are_explicit_not_silent():
    from sc_referee.inference import AnalysisRequest, analyze
    from sc_referee.inference.frontend.common import SourceUnit

    r_source = SourceUnit.from_text("result <- FindMarkers(object, ident.1='A')\n", language="r")
    snapshot = analyze(AnalysisRequest((r_source, "fn = getattr(module, name)\n")))
    kinds = {barrier.kind for barrier in snapshot.program.barriers}
    assert "unsupported_language" in kinds
    assert "reflection" in kinds
    assert snapshot.coverage.frontend_complete is False


def test_supported_program_has_stable_ids_and_complete_frontend_coverage():
    from sc_referee.inference import analyze

    source = "x = 1\ny = x + 2\n"
    first = analyze(_request(source))
    second = analyze(_request(source))

    assert first.coverage.source_complete is True
    assert first.coverage.frontend_complete is True
    assert first.coverage.complete is False  # claim/artifact coverage is not implemented in Increment 1
    assert first.program.barriers == ()
    assert tuple(first.program.value_definitions) == tuple(second.program.value_definitions)


def test_increment_one_module_skeleton_is_importable():
    modules = (
        "frontend.common", "frontend.python", "frontend.r", "frontend.claims", "frontend.config",
        "ir.nodes", "ir.cfg", "ir.lower", "ir.validate",
        "contracts.schema", "contracts.registry", "contracts.builtin", "contracts.library",
        "domains.bilattice", "domains.origin", "domains.region", "domains.unit",
        "domains.calibration", "domains.effects", "domains.selection", "domains.value",
        "analysis.transfer", "analysis.memory", "analysis.artifacts", "analysis.dependence",
        "analysis.fixpoint", "analysis.interpret", "claims.inventory", "claims.bind", "claims.slice",
        "refinement.types", "refinement.infer", "proof.obligations", "proof.discharge",
        "proof.facts", "proof.certificate", "policy.schema", "policy.evaluate", "policy.aggregate",
        "policy.double_dipping", "policy.pseudoreplication", "policy.confounding",
        "policy.allele_harmonization", "policy.enrichment_universe",
        "policy.coordinate_consumption", "policy.trajectory_circularity",
    )
    for module in modules:
        __import__(f"sc_referee.inference.{module}")


def test_analyzer_identity_is_bumped_for_the_increment_nine_live_tcb():
    from sc_referee.inference.api import ANALYZER_VERSION

    assert ANALYZER_VERSION == "sc-referee.inference.increment-9.live.advisory-v4"
