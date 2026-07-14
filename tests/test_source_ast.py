"""source_ast — the ONE shared parse + call-site enumeration that provenance (taint) and sink_use
(contract binding) both consume, so the two never drift on which calls exist or what code they see
(adversarial design consult, Q1 anti-drift). It normalizes notebooks/magics, yields statements in
source order, and assigns every call a STABLE id (`source_index:lineno:col`) so a MarkerTest and its
SinkUse can be joined by that id.
"""


def test_parse_sources_normalizes_notebook_and_magics():
    from sc_referee.source_ast import parse_sources
    import json
    nb = json.dumps({"cells": [
        {"cell_type": "markdown", "source": ["# heading\n"]},
        {"cell_type": "code", "source": ["%matplotlib inline\n", "import scanpy as sc\n",
                                          "sc.tl.rank_genes_groups(adata, groupby='leiden')\n"]},
    ]})
    parsed = parse_sources([nb])
    assert len(parsed) == 1
    assert parsed[0].tree is not None and parsed[0].parse_error is None
    # the magic line was stripped before parsing; the marker call survived
    assert parsed[0].source_index == 0


def test_unparseable_source_records_error_not_crash():
    from sc_referee.source_ast import parse_sources
    parsed = parse_sources(["import scanpy as sc\ndef (:\n"])   # syntax error
    assert len(parsed) == 1
    assert parsed[0].tree is None and parsed[0].parse_error is not None


def test_iter_call_sites_extracts_symbol_and_module_hint():
    from sc_referee.source_ast import parse_sources, iter_call_sites
    src = ("import scanpy as sc\n"
           "sc.tl.rank_genes_groups(adata, groupby='leiden')\n"
           "ttest_ind(a, b)\n")
    sites = iter_call_sites(parse_sources([src]))
    by_symbol = {s.symbol: s for s in sites}
    assert "rank_genes_groups" in by_symbol and "ttest_ind" in by_symbol
    # dotted attribute chain -> symbol is the last attr; module_hint carries the prefix
    assert by_symbol["rank_genes_groups"].module_hint == "sc.tl"
    # a bare Name call has no module prefix
    assert by_symbol["ttest_ind"].module_hint is None


def test_call_site_ids_are_stable_and_carry_source_index():
    from sc_referee.source_ast import parse_sources, iter_call_sites
    src = "import scanpy as sc\nsc.tl.rank_genes_groups(adata, groupby='leiden')\n"
    a = iter_call_sites(parse_sources([src, src]))
    b = iter_call_sites(parse_sources([src, src]))
    # deterministic: same code -> identical ids (the join key provenance & sink_use rely on)
    assert [s.id for s in a] == [s.id for s in b]
    # the two identical sources are distinguished by source_index in the id
    idxs = sorted({s.source_index for s in a})
    assert idxs == [0, 1]
    assert all(s.id.startswith(f"{s.source_index}:") for s in a)


def test_nested_calls_are_each_enumerated_once():
    from sc_referee.source_ast import parse_sources, iter_call_sites
    src = "labels = GaussianMixture(10).fit_predict(adata.X)\n"
    symbols = [s.symbol for s in iter_call_sites(parse_sources([src]))]
    # both the outer .fit_predict and the inner GaussianMixture(...) are calls, each once
    assert symbols.count("fit_predict") == 1
    assert symbols.count("gaussianmixture") == 1


def test_call_site_ids_are_unique_even_at_the_same_start_position():
    # `lineno:col` alone collides: in a chained call `x.a().b()` the outer and inner Call nodes share
    # the SAME (lineno, col_offset=0), so the id must include the full span or two calls join to the
    # same taint origin (adversarial review #4).
    from sc_referee.source_ast import parse_sources, iter_call_sites
    src = "pipeline.first_step().second_step()\n"
    sites = iter_call_sites(parse_sources([src]))
    starts = {(s.lineno, s.col_offset) for s in sites}
    assert len(starts) == 1                          # both calls genuinely share a start position
    ids = [s.id for s in sites]
    assert len(ids) == len(set(ids)), f"call-site ids collided: {ids}"


def test_iter_call_sites_is_in_document_order():
    # the docstring promises document order; ast.walk is breadth-first, so it must be sorted (adversarial review #7).
    from sc_referee.source_ast import parse_sources, iter_call_sites
    src = "wrapper(\n    first_call(a)\n)\nsecond_call(b)\n"
    symbols = [s.symbol for s in iter_call_sites(parse_sources([src]))]
    assert symbols.index("first_call") < symbols.index("second_call")


def test_malformed_notebook_json_does_not_crash():
    # a cell whose source is not a list-of-strings must be tolerated at the parser boundary (adversarial review #9).
    from sc_referee.source_ast import parse_sources
    bad = '{"cells":[{"cell_type":"code","source":[1]}]}'
    parsed = parse_sources([bad])            # must not raise
    assert len(parsed) == 1


def test_source_env_resolves_aliases_and_from_imports():
    from sc_referee.source_ast import parse_sources, source_env, resolve_callee, iter_call_sites
    src = ("import scanpy as sx\n"
           "from scipy.stats import ttest_ind as welch\n"
           "sx.tl.rank_genes_groups(adata, 'leiden')\n"
           "welch(a, b)\n")
    parsed = parse_sources([src])
    env = source_env(parsed[0])
    by_symbol = {s.symbol: s for s in iter_call_sites(parsed)}
    # aliased module: sx -> scanpy, so sx.tl.rank_genes_groups is scanpy.tl.rank_genes_groups
    assert resolve_callee(by_symbol["rank_genes_groups"], env) == ("scanpy.tl", "rank_genes_groups")
    # aliased from-import: welch -> scipy.stats.ttest_ind
    assert resolve_callee(by_symbol["welch"], env) == ("scipy.stats", "ttest_ind")


def test_locally_defined_name_is_not_resolved_to_a_library_sink():
    # a user function named ttest_ind must NOT resolve to scipy — callee identity is a PROVED fact,
    # and a bare name with no traced import is unresolved (adversarial review #1, the cardinal-rule fix).
    from sc_referee.source_ast import parse_sources, source_env, resolve_callee, iter_call_sites
    src = ("def ttest_ind(a, b):\n    return donor_blocked_permutation(a, b)\n"
           "result = ttest_ind(case, control)\n")
    parsed = parse_sources([src])
    env = source_env(parsed[0])
    site = next(s for s in iter_call_sites(parsed) if s.symbol == "ttest_ind")
    assert resolve_callee(site, env) is None


def test_from_submodule_import_resolves_to_the_submodule():
    # `from scipy import stats` then `stats.ttest_ind(...)` — the binding is module-or-symbol ambiguous;
    # form the candidate `scipy.stats` and let the exact registry match accept it (adversarial re-review #5).
    from sc_referee.source_ast import parse_sources, source_env, resolve_callee, iter_call_sites
    parsed = parse_sources(["from scipy import stats\nstats.ttest_ind(a, b)\n"])
    env = source_env(parsed[0])
    site = next(s for s in iter_call_sites(parsed) if s.symbol == "ttest_ind")
    assert resolve_callee(site, env) == ("scipy.stats", "ttest_ind")


def test_function_parameter_shadows_an_imported_name():
    # `def run(stats): stats.ttest_ind(...)` — `stats` is a param, not the imported module. Ambiguous
    # binding -> unresolved, so it is never falsely bound as scipy (adversarial re-review #2 false match).
    from sc_referee.source_ast import parse_sources, source_env, resolve_callee, iter_call_sites
    src = ("import scipy.stats as stats\n"
           "def run(stats):\n    return stats.ttest_ind(a, b)\n")
    parsed = parse_sources([src])
    env = source_env(parsed[0])
    site = next(s for s in iter_call_sites(parsed) if s.symbol == "ttest_ind")
    assert resolve_callee(site, env) is None


def test_visible_monkeypatch_invalidates_the_path():
    from sc_referee.source_ast import parse_sources, source_env, resolve_callee, iter_call_sites
    src = ("import scanpy as sc\n"
           "sc.tl.rank_genes_groups = selection_aware_marker_test\n"
           "sc.tl.rank_genes_groups(adata, 'leiden')\n")
    parsed = parse_sources([src])
    env = source_env(parsed[0])
    site = next(s for s in iter_call_sites(parsed) if s.symbol == "rank_genes_groups")
    assert resolve_callee(site, env) is None          # patched path is not the naive library contract
    # an UNRELATED attribute write must NOT invalidate the sink
    ok = parse_sources(["import scanpy as sc\nsc.settings.verbosity = 0\nsc.tl.rank_genes_groups(adata, 'g')\n"])
    env2 = source_env(ok[0])
    s2 = next(s for s in iter_call_sites(ok) if s.symbol == "rank_genes_groups")
    assert resolve_callee(s2, env2) == ("scanpy.tl", "rank_genes_groups")
