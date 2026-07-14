"""The typed sink-contract registry — the shared foundation for the next wave of checks (error-catalog
round-2 spec). For an inferential call it answers: is it a sink? which arg is response / grouping /
block? what input scale + unit does it assume? is it calibrated / selection-aware? where does its
output go? An UNKNOWN call (or a version outside the contract's spec) resolves to None → the caller
emits `needs_evidence` ("unknown means review"). No blocker is ever built on an unresolved contract.
"""


def test_resolves_a_known_marker_sink():
    from sc_referee.sinks import resolve_sink
    c = resolve_sink("rank_genes_groups", module="scanpy.tl")
    assert c is not None and c.sink_kind == "marker"
    assert any(p.role == "grouping" for p in c.inputs)
    assert "pvals_adj" in c.report.pvalue_fields
    # it is a naive selection-aware sink over de-novo clustering — the double-dipping shape
    assert "clustering" in c.selection.protected_selection_kinds


def test_ttest_ind_assumes_iid_continuous_not_raw_counts():
    from sc_referee.sinks import resolve_sink
    c = resolve_sink("ttest_ind", module="scipy.stats")
    assert c is not None and c.calibration.independence_semantics == "iid_rows"
    resp = next(p for p in c.inputs if p.role.startswith("response"))
    assert "log_normalized" in resp.accepted_scales and "raw_counts" not in resp.accepted_scales


def test_deseq_is_a_count_model_accepting_raw_counts_only():
    from sc_referee.sinks import resolve_sink
    c = resolve_sink("DeseqDataSet", module="pydeseq2.dds")
    assert c is not None and c.sink_kind == "de"
    resp = next(p for p in c.inputs if p.role == "response")
    assert "raw_counts" in resp.accepted_scales and "log_normalized" not in resp.accepted_scales
    assert "sample" in resp.accepted_units or "aggregate" in resp.accepted_units


def test_unknown_symbol_resolves_to_none():
    from sc_referee.sinks import resolve_sink
    assert resolve_sink("totally_made_up_test_fn") is None


def test_version_outside_contract_spec_is_unknown_contract():
    from sc_referee.sinks import resolve_sink
    assert resolve_sink("ttest_ind", module="scipy.stats", version="0.5") is None      # < >=1.9
    assert resolve_sink("ttest_ind", module="scipy.stats", version="1.11") is not None


def test_resolution_is_case_sensitive_on_symbol():
    # Python/R are case-sensitive: DESEQDATASET is not DeseqDataSet. Wrong case must NOT resolve, or a
    # distinct uppercase callable could receive the wrong contract (adversarial re-review #7).
    from sc_referee.sinks import resolve_sink
    assert resolve_sink("DeseqDataSet") is not None and resolve_sink("FindMarkers") is not None
    assert resolve_sink("deseqdataset") is None and resolve_sink("DESEQDATASET") is None


def test_ports_use_structured_locators_with_positional_fallback():
    # scanpy/scipy are FREE FUNCTIONS, not methods — the response is an argument, never a `receiver`
    # (adversarial design consult, Q3). rank_genes_groups(adata, 'leiden') binds groupby positionally.
    from sc_referee.sinks import resolve_sink
    c = resolve_sink("rank_genes_groups", module="scanpy.tl")
    grouping = next(p for p in c.inputs if p.role == "grouping")
    gkeys = {(l.kind, l.name, l.index) for l in grouping.locators}
    assert ("kw", "groupby", None) in gkeys and ("arg", None, 1) in gkeys
    response = next(p for p in c.inputs if p.role == "response")
    assert all(l.kind != "receiver" for l in response.locators)
    assert ("arg", None, 0) in {(l.kind, l.name, l.index) for l in response.locators}


def test_seurat_findmarkers_grouping_is_named_only_no_positional_guess():
    # R has no Python AST binder — a positional group convention (ident.1 vs group.by vs cells.1 differ
    # in meaning) must not be guessed. Bind the named arg only. (adversarial review Q3.)
    from sc_referee.sinks import resolve_sink
    c = resolve_sink("FindMarkers", module="Seurat")
    grouping = next(p for p in c.inputs if p.role == "grouping")
    assert all(l.kind == "kw" for l in grouping.locators)


def test_resolve_sink_status_reports_the_reason():
    from sc_referee.sinks import resolve_sink_status
    # a PINNED contract with no version supplied is version_unknown, NOT exact — an unconfirmed version
    # must never be laundered into blocker-eligibility (adversarial review #5).
    contract, status = resolve_sink_status("rank_genes_groups", module="scanpy.tl")
    assert contract is not None and status == "version_unknown"
    # a contract with no version pin has nothing to confirm -> exact
    c0, s0 = resolve_sink_status("DeseqDataSet", module="pydeseq2.dds")
    assert c0 is not None and s0 == "exact"
    assert resolve_sink_status("totally_made_up") == (None, "unknown_symbol")
    c2, s2 = resolve_sink_status("ttest_ind", module="scipy.stats", version="0.5")
    assert c2 is None and s2 == "version_mismatch"        # symbol known, version outside spec
    c3, s3 = resolve_sink_status("ttest_ind", module="scipy.stats", version="1.11")
    assert c3 is not None and s3 == "exact"               # version supplied and compatible
    # a supplied-but-UNPARSEABLE version cannot be confirmed -> version_unknown, never exact (adversarial review #7)
    c4, s4 = resolve_sink_status("ttest_ind", module="scipy.stats", version="not-a-version")
    assert s4 == "version_unknown"


def test_seurat_findmarkers_requires_v4_or_v5_and_a_supported_test_use():
    from sc_referee.sinks import resolve_sink_status

    assert resolve_sink_status(
        "FindMarkers", module="Seurat", arguments={"test.use": "wilcox"}
    ) == (None, "version_unknown")
    assert resolve_sink_status(
        "FindMarkers", module="Seurat", version="3.2.3", arguments={"test.use": "wilcox"}
    ) == (None, "version_mismatch")
    assert resolve_sink_status(
        "FindMarkers", module="Seurat", version="4.4.0"
    ) == (None, "argument_unknown")
    assert resolve_sink_status(
        "FindMarkers", module="Seurat", version="5.1.0", arguments={"test.use": "LR"}
    ) == (None, "argument_mismatch")


def test_seurat_findmarkers_dynamic_test_use_abstains():
    from sc_referee.sinks import resolve_sink_status

    # A non-literal extractor result must never select a calibration variant or crash resolution.
    assert resolve_sink_status(
        "FindMarkers", module="Seurat", version="5.1.0",
        arguments={"test.use": ["runtime-computed"]},
    ) == (None, "argument_unknown")


def test_seurat_findmarkers_default_and_wilcox_are_v4_plus_normalized_pvalue_contracts():
    from sc_referee.sinks import resolve_sink_status

    for arguments in ({}, {"test.use": "wilcox"}):
        contract, status = resolve_sink_status(
            "FindMarkers", module="Seurat", version="4.4.0", arguments=arguments
        )
        assert status == "exact"
        assert contract.contract_id == "seurat.FindMarkers.v4.wilcox"
        response = next(port for port in contract.inputs if port.role == "response")
        assert response.accepted_scales == frozenset({"log_normalized", "normalized_counts"})
        assert contract.calibration.output_kind == "pvalue"
        assert contract.report.effect_fields == ("avg_log2FC",)


def test_seurat_findmarkers_count_tests_read_raw_counts_only():
    from sc_referee.sinks import resolve_sink_status

    for test_use in ("negbinom", "DESeq2"):
        contract, status = resolve_sink_status(
            "FindMarkers", module="Seurat", version="5.1.0",
            arguments={"test.use": test_use},
        )
        assert status == "exact"
        assert contract.contract_id == "seurat.FindMarkers.v4.count"
        response = next(port for port in contract.inputs if port.role == "response")
        assert response.accepted_kinds == frozenset({"counts"})
        assert response.accepted_scales == frozenset({"raw_counts"})
        assert contract.calibration.output_kind == "pvalue"


def test_seurat_findmarkers_roc_is_a_score_without_pvalue_fields_or_asserted_scale():
    from sc_referee.sinks import resolve_sink_status

    contract, status = resolve_sink_status(
        "FindMarkers", module="Seurat", version="5.1.0", arguments={"test.use": "roc"}
    )
    assert status == "exact"
    assert contract.contract_id == "seurat.FindMarkers.v4.roc"
    assert contract.sink_kind == "classifier"
    assert contract.calibration.output_kind == "score"
    assert contract.calibration.independence_semantics == "none"
    assert contract.report.pvalue_fields == ()
    assert contract.report.qvalue_fields == ()
    response = next(port for port in contract.inputs if port.role == "response")
    assert response.accepted_kinds == frozenset()
    assert response.accepted_scales == frozenset()


def test_scvi_and_scanvi_de_are_inferred_posterior_score_candidates_that_must_abstain():
    from sc_referee.sinks import sink_contract_candidates, resolve_sink_status

    for module in ("scvi.model.SCVI", "scvi.model.SCANVI"):
        candidates = sink_contract_candidates("differential_expression", module=module)
        assert len(candidates) == 1
        contract = candidates[0]
        assert contract.sink_kind == "bayesian_de"
        assert contract.calibration.output_kind == "score"
        assert contract.calibration.independence_semantics == "unknown"
        assert contract.report.pvalue_fields == ()
        assert contract.report.qvalue_fields == ()
        assert contract.evidence_level == "inferred"
        assert resolve_sink_status(
            "differential_expression", module=module, version="1.3.0"
        ) == (None, "needs_evidence")


def test_rank_velocity_genes_is_only_an_inferred_descriptive_score_candidate():
    from sc_referee.sinks import sink_contract_candidates, resolve_sink_status

    candidates = sink_contract_candidates("rank_velocity_genes", module="scvelo.tl")
    assert len(candidates) == 1
    contract = candidates[0]
    assert contract.sink_kind == "descriptive_ranking"
    assert contract.calibration.output_kind == "score"
    assert contract.report.pvalue_fields == ()
    assert contract.evidence_level == "inferred"
    assert resolve_sink_status(
        "rank_velocity_genes", module="scvelo.tl", version="0.3.3"
    ) == (None, "needs_evidence")
