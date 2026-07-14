"""sink_use — bind detected call sites to resolved sink contracts (spine step 1b).

For every recognized inferential call, produce a SinkUse: the contract, the resolution status, and each
InputPort bound to the actual argument (keyword wins over positional). Callee identity is a PROVED fact
via the import table — a user's own `def ttest_ind` never binds to scipy, and `import scanpy as sx`
still resolves. v1 is STRUCTURAL — it does NOT infer assay scale/unit; the one value fact it fills is
the grouping port's ORIGIN, reused from the already-approved provenance taint. Unknown calls produce no
SinkUse; a **kwargs splat makes a port `unsupported`, never a false `missing`; a parse failure becomes a
diagnostic, never a silent drop. (adversarial review SinkUse-design + review.)
"""


def test_binds_positional_groupby():
    from sc_referee.sink_use import bind_sinks
    uses = bind_sinks(["import scanpy as sc\nsc.tl.rank_genes_groups(adata, 'leiden')\n"]).uses
    rgg = [u for u in uses if u.symbol == "rank_genes_groups"]
    assert len(rgg) == 1
    u = rgg[0]
    assert u.resolution_status == "version_unknown" and u.callsite_id   # pinned, version unconfirmed
    g = u.bound_ports["grouping"]
    assert g.status == "bound" and g.literal_value == "leiden"
    assert g.locator_used.kind == "arg" and g.locator_used.index == 1   # positional fallback used


def test_keyword_wins_over_positional():
    from sc_referee.sink_use import bind_sinks
    uses = bind_sinks(["import scanpy as sc\nsc.tl.rank_genes_groups(adata, groupby='ct')\n"]).uses
    g = uses[0].bound_ports["grouping"]
    assert g.status == "bound" and g.literal_value == "ct"
    assert g.locator_used.kind == "kw" and g.locator_used.name == "groupby"


def test_aliased_import_still_resolves():
    # `import scanpy as sx` — the fixed alias table used to miss this; the import table must resolve it
    from sc_referee.sink_use import bind_sinks
    uses = bind_sinks(["import scanpy as sx\nsx.tl.rank_genes_groups(adata, 'leiden')\n"]).uses
    assert any(u.symbol == "rank_genes_groups" and u.module == "scanpy.tl" for u in uses)


def test_locally_defined_ttest_is_not_bound_as_scipy():
    # the cardinal-rule fix: a user function shadowing a library name must NOT bind to the library sink
    from sc_referee.sink_use import bind_sinks
    src = ("def ttest_ind(a, b):\n    return donor_blocked_permutation(a, b)\n"
           "result = ttest_ind(case, control)\n")
    assert bind_sinks([src]).uses == []


def test_unknown_and_unimported_calls_produce_no_sinkuse():
    from sc_referee.sink_use import bind_sinks
    # np.mean is imported but not a registered sink; a bare unimported name never resolves
    assert bind_sinks(["import numpy as np\nnp.mean(adata.X)\n"]).uses == []
    assert bind_sinks(["ttest_ind(a, b)\n"]).uses == []          # no import -> unresolved


def test_deseq_binds_counts_keyword_only_and_reads_response_role():
    from sc_referee.sink_use import bind_sinks
    src = ("from pydeseq2.dds import DeseqDataSet\n"
           "dds = DeseqDataSet(counts=cts, metadata=md, design='~condition')\n")
    u = [u for u in bind_sinks([src]).uses if u.symbol.lower() == "deseqdataset"][0]
    assert u.resolution_status == "exact"                        # DeseqDataSet has no version pin
    resp = u.bound_ports["response"]
    assert resp.status == "bound" and resp.locator_used.kind == "kw" and resp.locator_used.name == "counts"


def test_kwargs_splat_makes_ports_unsupported_not_missing():
    # neither a required NOR an optional port may be declared missing when a **splat could hide it
    from sc_referee.sink_use import bind_sinks
    req = "from pydeseq2.dds import DeseqDataSet\ndds = DeseqDataSet(**cfg)\n"
    assert bind_sinks([req]).uses[0].bound_ports["response"].status == "unsupported"
    opt = "from pydeseq2.dds import DeseqDataSet\ndds = DeseqDataSet(counts=c, metadata=m, **cfg)\n"
    assert bind_sinks([opt]).uses[0].bound_ports["design"].status == "unsupported"   # optional, splat-hidden


def test_parse_failure_is_a_diagnostic_not_a_silent_drop():
    from sc_referee.sink_use import bind_sinks
    res = bind_sinks(["import scipy.stats as st\nst.ttest_ind(a, b)\nif\n"])   # trailing syntax error
    assert any(d["kind"] == "parse_error" and d["source_index"] == 0 for d in res.diagnostics)


def test_grouping_origin_reuses_provenance_taint():
    from sc_referee.sink_use import bind_sinks
    derived = ("import scanpy as sc\nlabels = kmeans(adata.X)\nadata.obs['sub'] = labels\n"
               "sc.tl.rank_genes_groups(adata, groupby='sub')\n")
    g = bind_sinks([derived]).uses[0].bound_ports["grouping"]
    assert g.value_type.origins == frozenset({"primary_data"}) and g.value_type.kind == "labels"
    predefined = "import scanpy as sc\nsc.tl.rank_genes_groups(adata, groupby='genotype')\n"
    g2 = bind_sinks([predefined]).uses[0].bound_ports["grouping"]
    assert g2.value_type.origins == frozenset({"metadata"})


def test_same_param_positional_and_keyword_is_invalid_not_bound():
    # ttest_ind(x, y, a=z): `a` is given both positionally (arg0) and by keyword -> a TypeError call,
    # never a correct analysis. Report invalid_call, don't silently pick one (adversarial review #8).
    from sc_referee.sink_use import bind_sinks
    src = "import scipy.stats as st\nst.ttest_ind(x, y, a=z)\n"
    u = bind_sinks([src]).uses[0]
    assert u.bound_ports["response_a"].status == "invalid_call"


def test_dynamic_groupby_origin_is_unknown():
    from sc_referee.sink_use import bind_sinks
    src = "import scanpy as sc\ncol = pick()\nsc.tl.rank_genes_groups(adata, groupby=col)\n"
    g = bind_sinks([src]).uses[0].bound_ports["grouping"]
    assert g.status == "bound" and g.literal_value is None
    assert g.value_type.origins == frozenset({"unknown"})


def test_imports_are_per_source_not_unioned():
    # source 1 rebinding the name `sc` to a different package must NOT corrupt source 0's real sink,
    # and must not let source 1's `sc` resolve to scanpy (adversarial re-review blocker #1).
    from sc_referee.sink_use import bind_sinks
    s0 = "import scanpy as sc\nsc.tl.rank_genes_groups(adata, 'leiden')\n"
    s1 = "import my_pipeline as sc\nsc.run()\n"
    uses = bind_sinks([s0, s1]).uses
    rgg = [u for u in uses if u.symbol == "rank_genes_groups"]
    assert len(rgg) == 1 and rgg[0].source_span[0] == 0        # source 0 still resolves, source 1 unaffected


def test_lookalike_module_does_not_masquerade_as_scipy():
    # `project.scipy.stats` must not match the scipy.stats contract via suffix (adversarial re-review #4)
    from sc_referee.sink_use import bind_sinks
    src = "import project.scipy.stats as stats\nstats.ttest_ind(a, b)\n"
    assert not [u for u in bind_sinks([src]).uses if u.symbol.lower() == "ttest_ind"]


def test_star_imported_sink_becomes_a_review_candidate():
    # `from scipy.stats import *` then `ttest_ind(...)` must not silently vanish (adversarial re-review #6)
    from sc_referee.sink_use import bind_sinks
    res = bind_sinks(["from scipy.stats import *\nttest_ind(a, b)\n"])
    assert res.uses == []
    assert any(d["kind"] == "unresolved_sink_candidate" and d["symbol"] == "ttest_ind"
               for d in res.diagnostics)


def test_multiple_imports_under_one_name_abstain_and_diagnose():
    # try/except-style re-import: `stats` bound to two different packages -> ambiguous -> never bound as
    # scipy, but surfaced (adversarial re-review #2 wrong-contract).
    from sc_referee.sink_use import bind_sinks
    src = ("import project.custom_stats as stats\nstats.ttest_ind(a, b)\nimport scipy.stats as stats\n")
    res = bind_sinks([src])
    assert res.uses == []
    assert any(d["symbol"] == "ttest_ind" for d in res.diagnostics)


def test_match_capture_shadows_import():
    # `case {"stats": stats}` binds a captured value, not the imported module -> must not bind as scipy
    from sc_referee.sink_use import bind_sinks
    src = ("import scipy.stats as stats\n"
           "match obj:\n    case {'stats': stats}:\n        stats.ttest_ind(a, b)\n")
    assert bind_sinks([src]).uses == []


def test_monkeypatch_prefix_and_alias_invalidate_the_sink():
    from sc_referee.sink_use import bind_sinks
    prefix = "import scanpy as sc\nsc.tl = custom_ns\nsc.tl.rank_genes_groups(adata, 'g')\n"
    assert bind_sinks([prefix]).uses == []            # a patched PREFIX invalidates descendants
    alias = ("import scanpy as sc\nt = sc.tl\nt.rank_genes_groups = custom\n"
             "sc.tl.rank_genes_groups(adata, 'g')\n")
    assert bind_sinks([alias]).uses == []             # patch reaching the symbol via an alias havocs it


def test_module_rejected_sink_is_still_diagnosed():
    # `project.scipy.stats` resolves to a module the registry rejects; it must not vanish (re-review #1)
    from sc_referee.sink_use import bind_sinks
    res = bind_sinks(["import project.scipy.stats as stats\nstats.ttest_ind(a, b)\n"])
    assert res.uses == [] and any(d["symbol"] == "ttest_ind" for d in res.diagnostics)


def test_import_aliased_ambiguous_sink_is_diagnosed_under_its_real_name():
    from sc_referee.sink_use import bind_sinks
    src = ("from scipy.stats import ttest_ind as welch\n"
           "def unrelated(welch):\n    return welch\n"
           "result = welch(a, b)\n")
    res = bind_sinks([src])
    assert res.uses == []                             # welch is ambiguous (param + import) -> abstain
    assert any(d["symbol"] == "ttest_ind" for d in res.diagnostics)   # surfaced via the import binding


def test_indirect_sink_references_are_diagnosed():
    from sc_referee.sink_use import bind_sinks
    alias = "import scanpy as sc\ntest = sc.tl.rank_genes_groups\ntest(adata, 'g')\n"
    res = bind_sinks([alias])
    assert res.uses == [] and any(d["symbol"] == "rank_genes_groups" for d in res.diagnostics)
    getr = "import scipy.stats as stats\ngetattr(stats, 'ttest_ind')(a, b)\n"
    assert any(d["symbol"] == "ttest_ind" for d in bind_sinks([getr]).diagnostics)


def test_uppercase_sink_symbol_does_not_bind_but_is_flagged():
    from sc_referee.sink_use import bind_sinks
    src = "from pydeseq2.dds import DESEQDATASET\nDESEQDATASET(counts=c, metadata=m, design='~x')\n"
    res = bind_sinks([src])
    assert res.uses == []                             # DESEQDATASET != DeseqDataSet (case-sensitive)
    assert any(d["symbol"] == "deseqdataset" for d in res.diagnostics)


def test_exotic_monkeypatch_forms_never_bind_the_naive_contract():
    # adversarial-review round-4: for/with attribute targets, globals()[], setattr-alias, patch.object all patch the
    # sink but slipped past syntax-specific detection. The ctx=Store + (imported-obj,"str") rules close
    # the class. Every one must yield NO SinkUse (over-abstention is fine; a wrong contract is not).
    from sc_referee.sink_use import bind_sinks
    cases = [
        "import scanpy as sc\nfor sc.tl.rank_genes_groups in [custom]:\n    sc.tl.rank_genes_groups(adata, 'g')\n",
        "import scanpy as sc\nwith cm() as sc.tl.rank_genes_groups:\n    sc.tl.rank_genes_groups(adata, 'g')\n",
        "import scipy.stats as stats\nglobals()['stats'] = custom\nstats.ttest_ind(a, b)\n",
        "import scanpy as sc\nsa = setattr\nsa(sc.tl, 'rank_genes_groups', custom)\nsc.tl.rank_genes_groups(adata, 'g')\n",
        "import scanpy as sc\npatch.object(sc.tl, 'rank_genes_groups', custom)\nsc.tl.rank_genes_groups(adata, 'g')\n",
    ]
    for src in cases:
        assert bind_sinks([src]).uses == [], f"wrong-contract bind survived:\n{src}"


def test_multiple_import_loses_no_diagnosis_and_relative_import_is_flagged():
    from sc_referee.sink_use import bind_sinks
    multi = ("from scipy.stats import ttest_ind as test\nresult = test(a, b)\n"
             "from project import custom as test\n")
    res = bind_sinks([multi])
    assert res.uses == [] and any(d["symbol"] == "ttest_ind" for d in res.diagnostics)
    rel = "from .stats import ttest_ind as test\ntest(a, b)\n"
    assert any(d["symbol"] == "ttest_ind" for d in bind_sinks([rel]).diagnostics)
    dct = "import scipy.stats as stats\nstats.__dict__['ttest_ind'](a, b)\n"
    assert any(d["symbol"] == "ttest_ind" for d in bind_sinks([dct]).diagnostics)


def test_clean_analysis_still_resolves_no_over_abstain_regression():
    from sc_referee.sink_use import bind_sinks
    clean = "import scanpy as sc\nsc.tl.rank_genes_groups(adata, 'leiden')\n"
    uses = bind_sinks([clean]).uses
    assert len(uses) == 1 and uses[0].module == "scanpy.tl" and uses[0].symbol == "rank_genes_groups"


def test_call_based_namespace_mutations_never_bind_the_naive_contract():
    # adversarial-review round-5: .update()/keyword/receiver mutation forms bypassed the positional patch rule.
    from sc_referee.sink_use import bind_sinks
    cases = [
        "import scipy.stats as stats\nglobals().update(stats=custom)\nstats.ttest_ind(a, b)\n",
        "import scanpy as sc\nsc.tl.__dict__.update(rank_genes_groups=custom)\nsc.tl.rank_genes_groups(adata, 'g')\n",
        "import scipy.stats as stats\nglobals().update({'stats': custom})\nstats.ttest_ind(a, b)\n",
        "import scanpy as sc\npatch.object(target=sc.tl, attribute='rank_genes_groups', new=custom)\n"
        "sc.tl.rank_genes_groups(adata, 'g')\n",
    ]
    for src in cases:
        assert bind_sinks([src]).uses == [], f"wrong-contract bind survived:\n{src}"


def test_getattribute_indirect_call_is_diagnosed():
    from sc_referee.sink_use import bind_sinks
    src = "import scipy.stats as stats\nstats.__getattribute__('ttest_ind')(a, b)\n"
    assert any(d["symbol"] == "ttest_ind" for d in bind_sinks([src]).diagnostics)
