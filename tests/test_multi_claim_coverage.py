"""Phase 3: every declared report claim is audited only through its own producer."""
from __future__ import annotations

import json
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import pytest
from rich.console import Console
import yaml

from sc_referee import statuses as S
from sc_referee.audit import run_audit
from sc_referee.producer_binding import (
    bind_marker_extraction_report_producers,
    bind_uns_marker_report_producers,
)
from sc_referee.report import render_tty, to_json
from tests.inference._serialization import public_bytes


FROZEN_TTY = Path(__file__).parent / "frozen_oracles" / "report_ledger_phase3_tty.txt"
DEMO_CONFIG = Path(__file__).parent / "fixtures" / "report_ledger_demo" / "sc-referee.yaml"


SOURCE = """\
import numpy as np
import pandas as pd
import scanpy as sc
from scipy.stats import mannwhitneyu

adata = sc.read_h5ad('cells.h5ad')
sc.pp.normalize_total(adata)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata)
sc.pp.pca(adata)
sc.pp.neighbors(adata)
sc.tl.leiden(adata)
score = np.asarray(adata[:, ['RBFOX3', 'SYT1', 'SNAP25']].X.mean(axis=1)).ravel()
adata.obs['cell_type'] = np.where(score > np.median(score), 'neuronal', 'non_neuronal')
sc.tl.rank_genes_groups(adata, groupby='cell_type', method='wilcoxon')
de = sc.get.rank_genes_groups_df(adata, group='neuronal')
de.to_csv('results/de.csv', index=False)

psi = adata.X[:, 0] / (adata.X[:, 0] + adata.X[:, 1])
statistic, pvalue = mannwhitneyu(
    psi[adata.obs['cell_type'] == '0'],
    psi[adata.obs['cell_type'] == '1'],
)
splicing = pd.DataFrame({
    'gene': ['NRXN1'], 'pvalue': [pvalue], 'padj': [pvalue], 'log2fc': [0.25],
})
splicing.to_csv('results/splicing.csv', index=False)
"""


def _config(*, multi: bool) -> dict:
    config = {
        "analysis_type": "condition_contrast_DE",
        "confirmed_by_human": True,
        "design": {"condition": "cell_type", "replicate_unit": ["donor_id"], "batch": []},
        "contrasts": [{
            "name": "cell_type_1_vs_0", "reference": "0", "test": "1",
            "replicate_unit": ["donor_id"],
            "sample_unit": ["donor_id", "cell_type"],
            "pairing_unit": [], "model": "~ cell_type",
            "analyst_adjusted_for": ["cell_type"],
            "target_coefficient": "cell_type[T.1]",
        }],
        "reported_results": {"path": "results/de.csv", "unit_of_test": "cell"},
        "confidence": {"replicate_unit": "high", "condition": "high",
                       "analyst_adjusted_for": "high"},
    }
    if multi:
        config["claims"] = [
            {"name": "differential_expression", "path": "results/de.csv",
             "contrast": "cell_type_1_vs_0", "unit_of_test": "cell"},
            {"name": "alternative_splicing", "path": "results/splicing.csv",
             "contrast": "cell_type_1_vs_0", "unit_of_test": "cell",
             "value_kind": "derived_ratio"},
        ]
    return config


def _fixture(folder, *, multi: bool) -> None:
    (folder / "results").mkdir()
    donors = [f"D{i}" for i in range(1, 5) for _ in range(4)]
    groups = [value for _ in range(4) for value in ("0", "0", "1", "1")]
    counts = np.tile(np.array([
        [20, 5, 4], [18, 6, 4], [5, 20, 4], [6, 18, 4],
    ], dtype=np.int32), (4, 1))
    ad.AnnData(
        X=counts,
        obs=pd.DataFrame(
            {"donor_id": donors, "cell_type": groups},
            index=[f"c{i}" for i in range(len(donors))],
        ),
        var=pd.DataFrame(index=["NRXN1", "NRXN1_ALT", "OTHER"]),
    ).write_h5ad(folder / "cells.h5ad")
    (folder / "analysis.py").write_text(SOURCE)
    pd.DataFrame({
        "gene": ["NRXN1", "NRXN1_ALT", "OTHER"],
        "pvalue": [1e-8, 1e-7, 0.4], "padj": [2e-8, 2e-7, 0.4],
        "log2fc": [2.0, -2.0, 0.0],
    }).to_csv(folder / "results" / "de.csv", index=False)
    pd.DataFrame({
        "gene": ["NRXN1"], "pvalue": [0.001], "padj": [0.001], "log2fc": [0.25],
    }).to_csv(folder / "results" / "splicing.csv", index=False)
    (folder / "sc-referee.yaml").write_text(yaml.safe_dump(_config(multi=multi), sort_keys=False))


def _by_claim(result):
    out = {}
    for finding in result.findings:
        root = getattr(finding, "claim_root", None)
        if root is not None:
            out.setdefault(root["report_path"], []).append(finding)
    return out


def _claim_root(result, path):
    return getattr(_by_claim(result)[path][0], "claim_root")


def _states(findings):
    return [(finding.check_id, S.human_state(finding)) for finding in findings]


DE_STATES = [
    ("confounding", "clear"),
    ("experimental_unit", "not_checked"),
    ("multiple_testing", "not_checked"),
    ("effect_size_threshold", "clear"),
    ("pairing", "flagged"),
    ("double_dipping", "flagged"),
]
SPLICING_STATES = [
    ("confounding", "clear"),
    ("experimental_unit", "not_checked"),
    ("multiple_testing", "not_checked"),
    ("count_model", "n_a"),
    ("effect_size_threshold", "clear"),
    ("pairing", "flagged"),
    ("double_dipping", "not_checked"),
]

DE_UNSCOPED_STATES = [
    *DE_STATES[:-1],
    ("double_dipping", "not_checked"),
]


def test_ingest_binds_every_confirmed_declared_claim(tmp_path):
    from sc_referee.ingest import ingest

    _fixture(tmp_path, multi=True)
    bundle = ingest(tmp_path)

    assert [claim.report_relative_path for claim in bundle.reported_claims] == [
        "results/de.csv", "results/splicing.csv",
    ]
    assert [list(claim.reported_results["feature_id"]) for claim in bundle.reported_claims] == [
        ["NRXN1", "NRXN1_ALT", "OTHER"], ["NRXN1"],
    ]
    # The singular compatibility slot remains the first declared claim.
    assert bundle.reported_results.equals(bundle.reported_claims[0].reported_results)


def test_demo_config_declares_both_report_claims_and_is_schema_valid():
    from sc_referee.config import load_designs

    raw = yaml.safe_load(DEMO_CONFIG.read_text())
    assert [claim["path"] for claim in raw["claims"]] == [
        "results/de.csv", "results/splicing.csv",
    ]
    assert len(load_designs(DEMO_CONFIG)) == 1


def test_one_invalid_declared_claim_rejects_the_whole_manifest(tmp_path):
    from sc_referee.design import DesignError
    from sc_referee.ingest import ingest

    _fixture(tmp_path, multi=True)
    config = yaml.safe_load((tmp_path / "sc-referee.yaml").read_text())
    config["claims"][1]["path"] = "results/missing.csv"
    (tmp_path / "sc-referee.yaml").write_text(yaml.safe_dump(config, sort_keys=False))

    with pytest.raises(DesignError, match=r"claims\[1\]\.path.*does not exist"):
        ingest(tmp_path)


def test_second_claim_cannot_inherit_double_dipping_from_first_claim(tmp_path):
    _fixture(tmp_path, multi=True)

    result = run_audit(tmp_path, engine="simple")
    claims = _by_claim(result)
    assert list(claims) == ["results/de.csv", "results/splicing.csv"]

    de = {finding.check_id: finding for finding in claims["results/de.csv"]}
    splicing = {finding.check_id: finding for finding in claims["results/splicing.csv"]}

    assert S.human_state(de["double_dipping"]) == S.FLAGGED
    assert de["double_dipping"].coverage == S.COMPLETE

    # Absolute rail: mannwhitneyu is outside double-dipping coverage. The rank_genes_groups
    # producer elsewhere in this same file must never attach its accusation to splicing.csv.
    assert splicing["double_dipping"].status == S.NOT_AUDITED
    assert splicing["double_dipping"].coverage == S.NOT_RUN
    assert S.human_state(splicing["double_dipping"]) == S.NOT_CHECKED
    assert "mannwhitneyu" in splicing["double_dipping"].verdict
    assert "rank_genes_groups" not in splicing["double_dipping"].verdict

    assert S.human_state(splicing["experimental_unit"]) == S.NOT_CHECKED
    assert S.human_state(splicing["pairing"]) == S.FLAGGED
    assert S.human_state(splicing["count_model"]) == S.N_A


def test_realistic_preamble_and_gene_signature_subview_do_not_hide_marker_claim(tmp_path):
    _fixture(tmp_path, multi=True)

    claims = _by_claim(run_audit(tmp_path, engine="simple"))
    de = {finding.check_id: finding for finding in claims["results/de.csv"]}
    splicing = {finding.check_id: finding for finding in claims["results/splicing.csv"]}

    # Acceptance rail: this is the real demo shape, including normalization, clustering, and the
    # neuronal gene-signature AnnData subview that defeated the Phase 3a uns identity proof.
    assert S.human_state(de["double_dipping"]) == S.FLAGGED
    assert de["double_dipping"].coverage == S.COMPLETE
    assert S.human_state(splicing["double_dipping"]) == S.NOT_CHECKED
    assert splicing["double_dipping"].coverage == S.NOT_RUN
    assert S.human_state(de["experimental_unit"]) == S.NOT_CHECKED
    assert S.human_state(de["pairing"]) == S.FLAGGED
    assert S.human_state(splicing["experimental_unit"]) == S.NOT_CHECKED
    assert S.human_state(splicing["pairing"]) == S.FLAGGED


def test_short_marker_trace_binds_without_artifact_reader_preconditions(tmp_path):
    _fixture(tmp_path, multi=True)
    # Scoping needs only the exact extraction/local-frame/egress chain and must not require the
    # flagship analyzer's exact artifact-reader precondition merely to identify de.csv as markers.
    (tmp_path / "analysis.py").write_text(SOURCE.replace(
        "adata = sc.read_h5ad('cells.h5ad')",
        "adata = load_workbook()",
    ))

    result = run_audit(tmp_path, engine="simple")
    root = _claim_root(result, "results/de.csv")
    assert root["producing_test"] == "rank_genes_groups_df"
    assert root["producer_contract_id"] == "scanpy.get.rank_genes_groups_df.v1"
    de = {finding.check_id: finding for finding in _by_claim(result)["results/de.csv"]}
    assert S.human_state(de["double_dipping"]) == S.FLAGGED


@pytest.mark.parametrize(
    "replacement",
    [
        # Different AnnData identity is irrelevant to marker-claim classification.
        "other = sc.read_h5ad('cells.h5ad')\n"
        "de = sc.get.rank_genes_groups_df(other, group=None)",
        # A dynamic key is irrelevant because scoping does not prove an uns slot.
        "key = choose_key()\n"
        "de = sc.get.rank_genes_groups_df(adata, group=None, key=key)",
        # AnnData mutations before extraction are outside the local DataFrame trace.
        "maybe_mutate(adata)\n"
        "de = sc.get.rank_genes_groups_df(adata, group=None)",
        "adata.uns['rank_genes_groups'] = replacement\n"
        "de = sc.get.rank_genes_groups_df(adata, group=None)",
    ],
    ids=("different_object", "dynamic_key", "opaque_mutation", "intervening_uns_write"),
)
def test_short_marker_trace_ignores_ann_data_identity_and_uns_state(
    tmp_path, replacement,
):
    _fixture(tmp_path, multi=True)
    (tmp_path / "analysis.py").write_text(SOURCE.replace(
        "de = sc.get.rank_genes_groups_df(adata, group='neuronal')", replacement,
    ))

    result = run_audit(tmp_path, engine="simple")
    assert _claim_root(result, "results/de.csv")["producing_test"] == "rank_genes_groups_df"
    de = {finding.check_id: finding for finding in _by_claim(result)["results/de.csv"]}
    assert S.human_state(de["double_dipping"]) == S.FLAGGED


def test_short_marker_trace_ignores_multiple_uns_writers(tmp_path):
    _fixture(tmp_path, multi=True)
    (tmp_path / "analysis.py").write_text(SOURCE.replace(
        "de = sc.get.rank_genes_groups_df(adata, group='neuronal')",
        "sc.tl.rank_genes_groups(adata, groupby='cell_type', method='wilcoxon')\n"
        "de = sc.get.rank_genes_groups_df(adata, group='neuronal')",
    ))

    result = run_audit(tmp_path, engine="simple")
    assert _claim_root(result, "results/de.csv")["producing_test"] == "rank_genes_groups_df"
    de = {finding.check_id: finding for finding in _by_claim(result)["results/de.csv"]}
    assert S.human_state(de["double_dipping"]) == S.FLAGGED


def test_short_marker_trace_classifies_only_exact_extractor_dataframe_egress():
    binding = bind_marker_extraction_report_producers((SOURCE,))

    assert set(binding) == {"results/de.csv"}
    assert binding["results/de.csv"].contract_id == "scanpy.get.rank_genes_groups_df.v1"
    assert binding["results/de.csv"].marker_family == "rank_genes_groups"


def _assert_marker_red_team_abstains(folder):
    result = run_audit(folder, engine="simple")
    claims = _by_claim(result)

    assert _states(claims["results/de.csv"]) == DE_UNSCOPED_STATES
    assert _states(claims["results/splicing.csv"]) == SPLICING_STATES
    assert "producing_test" not in _claim_root(result, "results/de.csv")


def test_short_marker_trace_abstains_on_filesystem_equivalent_path_spellings(tmp_path):
    _fixture(tmp_path, multi=True)
    (tmp_path / "analysis.py").write_text(SOURCE.replace(
        "de.to_csv('results/de.csv', index=False)",
        "de.to_csv('results/de.csv', index=False)\n"
        "other.to_csv('./results//intermediate/../de.csv', index=False)",
    ))

    _assert_marker_red_team_abstains(tmp_path)


def test_short_marker_trace_havocs_global_reassignment_through_opaque_call(tmp_path):
    _fixture(tmp_path, multi=True)
    (tmp_path / "analysis.py").write_text(SOURCE.replace(
        "de = sc.get.rank_genes_groups_df(adata, group='neuronal')",
        "def replace_report():\n"
        "    global de\n"
        "    de = pd.read_csv('replacement.csv')\n\n"
        "de = sc.get.rank_genes_groups_df(adata, group='neuronal')\n"
        "replace_report()",
    ))

    _assert_marker_red_team_abstains(tmp_path)


def test_short_marker_trace_havocs_indirect_to_csv_monkeypatch(tmp_path):
    _fixture(tmp_path, multi=True)
    (tmp_path / "analysis.py").write_text(SOURCE.replace(
        "import scanpy as sc",
        "import scanpy as sc\nfrom unittest.mock import patch",
    ).replace(
        "de = sc.get.rank_genes_groups_df(adata, group='neuronal')",
        "de = sc.get.rank_genes_groups_df(adata, group='neuronal')\n"
        "patch('pandas.core.generic.DataFrame.to_csv', new=fake).start()",
    ))

    _assert_marker_red_team_abstains(tmp_path)


def test_marker_test_without_marker_extraction_does_not_enter_double_dipping_scope(tmp_path):
    _fixture(tmp_path, multi=True)
    replacement = """\
de = pd.DataFrame({
    'gene': ['NRXN1'],
    'pvalue': [sc.tl.rank_genes_groups(adata, groupby='cell_type')],
    'padj': [0.5],
    'log2fc': [0.0],
})"""
    (tmp_path / "analysis.py").write_text(SOURCE.replace(
        "de = sc.get.rank_genes_groups_df(adata, group='neuronal')", replacement,
    ))

    de = {finding.check_id: finding
          for finding in _by_claim(run_audit(tmp_path, engine="simple"))["results/de.csv"]}
    assert S.human_state(de["double_dipping"]) == S.NOT_CHECKED
    assert de["double_dipping"].coverage == S.NOT_RUN


@pytest.mark.parametrize(
    "source",
    [
        """\
import pandas as pd
import scanpy as sc
de = sc.get.rank_genes_groups_df(adata, group='neuronal')
de = pd.DataFrame({'pvalue': [0.5]})
de.to_csv('results/de.csv')
""",
        """\
import scanpy as sc
de = sc.get.rank_genes_groups_df(adata, group='neuronal')
mutate(de)
de.to_csv('results/de.csv')
""",
        """\
import scanpy as sc
de = sc.get.rank_genes_groups_df(adata, group='neuronal')
report = de
mutate(de)
report.to_csv('results/de.csv')
""",
        """\
import scanpy as sc
sc.get.rank_genes_groups_df(adata, group='neuronal').to_csv('results/de.csv')
""",
        """\
import scanpy as sc
de = sc.get.rank_genes_groups_df(adata, group='neuronal')
path = choose_path()
de.to_csv(path)
""",
        """\
import scanpy as sc
de = sc.get.rank_genes_groups_df(adata, group='neuronal')
de.to_csv('results/de.csv')
if stale:
    other.to_csv('results/de.csv')
""",
        """\
import scanpy as sc
de = sc.get.rank_genes_groups_df(adata, group='neuronal')
de.to_csv('results/de.csv')
other.to_csv('/absolute/results/de.csv')
""",
        """\
import scanpy as sc
extract = sc.get.rank_genes_groups_df
de = extract(adata, group='neuronal')
de.to_csv('results/de.csv')
""",
        """\
import scanpy as sc
exec(user_code)
de = sc.get.rank_genes_groups_df(adata, group='neuronal')
de.to_csv('results/de.csv')
""",
    ],
    ids=(
        "reassigned_non_marker", "opaque_dataframe_use", "opaque_alias_mutation",
        "opaque_inline_frame", "dynamic_path", "competing_path_writer",
        "mixed_absolute_relative_paths", "extractor_value_alias", "reflection",
    ),
)
def test_short_marker_trace_abstains_on_genuine_local_ambiguity(source):
    assert bind_marker_extraction_report_producers((source,)) == {}


def test_short_marker_trace_follows_plain_local_alias_and_parquet():
    source = """\
from scanpy.get import rank_genes_groups_df
de = rank_genes_groups_df(adata, group='neuronal')
report = de
report.to_parquet('results/de.parquet')
"""

    assert set(bind_marker_extraction_report_producers((source,))) == {"results/de.parquet"}


def test_bounded_marker_summaries_cover_custom_key_and_parquet_egress():
    source = """\
from scanpy import tl
from scanpy.get import rank_genes_groups_df

adata = load_workbook()
adata.uns['custom_markers'] = stale
tl.rank_genes_groups(adata, groupby='cell_type', key_added='custom_markers')
frame = rank_genes_groups_df(adata, group=None, key='custom_markers')
frame.to_parquet('results/de.parquet')
"""

    binding = bind_uns_marker_report_producers((source,))
    assert binding["results/de.parquet"].symbol == "rank_genes_groups"


@pytest.mark.parametrize(
    "source",
    [
        """\
import scanpy as sc
adata = load_workbook()
key = choose_key()
sc.tl.rank_genes_groups(adata, groupby='g', key_added=key)
frame = sc.get.rank_genes_groups_df(adata, group=None)
frame.to_csv('results/de.csv')
""",
        """\
import scanpy as sc
adata = load_workbook()
sc.tl.rank_genes_groups(adata, groupby='g')
frame = sc.get.rank_genes_groups_df(adata, group=None)
path = choose_path()
frame.to_csv(path)
""",
        """\
import scanpy as sc
adata = load_workbook()
shared_uns = adata.uns
sc.tl.rank_genes_groups(adata, groupby='g')
shared_uns['rank_genes_groups'] = replacement
frame = sc.get.rank_genes_groups_df(adata, group=None)
frame.to_csv('results/de.csv')
""",
        """\
import scanpy as sc
adata = load_workbook()
holder = [adata]
sc.tl.rank_genes_groups(adata, groupby='g')
holder[0].uns['rank_genes_groups'] = replacement
frame = sc.get.rank_genes_groups_df(adata, group=None)
frame.to_csv('results/de.csv')
""",
        """\
import scanpy as sc
adata = load_workbook()
sc.tl.rank_genes_groups(adata, groupby='g')
frame = sc.get.rank_genes_groups_df(adata, group=None)
other = frame
frame.to_csv('results/de.csv')
""",
        """\
import scanpy as sc
adata = load_workbook()
sc.tl.rank_genes_groups(adata, groupby='g')
mutate_module_state()
frame = sc.get.rank_genes_groups_df(adata, group=None)
frame.to_csv('results/de.csv')
""",
        """\
import pandas as pd
import scanpy as sc
pd.DataFrame.to_csv = custom_writer
adata = load_workbook()
sc.tl.rank_genes_groups(adata, groupby='g')
frame = sc.get.rank_genes_groups_df(adata, group=None)
frame.to_csv('results/de.csv')
""",
        """\
import scanpy as sc
adata = load_workbook()
shared_uns = getattr(adata, 'uns')
sc.tl.rank_genes_groups(adata, groupby='g')
shared_uns['rank_genes_groups'] = replacement
frame = sc.get.rank_genes_groups_df(adata, group=None)
frame.to_csv('results/de.csv')
""",
        """\
import scanpy as sc
adata = load_workbook()
sc.tl.rank_genes_groups(adata, groupby='g')
frame = sc.get.rank_genes_groups_df(adata, group=None)
frame.to_csv('results/de.csv')
if condition:
    stale.to_csv('results/de.csv')
""",
    ],
    ids=(
        "dynamic_writer_key", "dynamic_path", "preexisting_uns_alias", "container_alias",
        "marker_table_alias", "opaque_global_mutation", "patched_egress", "reflective_alias",
        "nested_competing_writer",
    ),
)
def test_bounded_marker_summaries_abstain_on_unproved_value_or_path_identity(source):
    assert bind_uns_marker_report_producers((source,)) == {}


def test_binding_second_claim_leaves_first_claim_finding_bytes_unchanged(tmp_path):
    _fixture(tmp_path, multi=False)
    singular = run_audit(tmp_path, engine="simple")
    singular_bytes = [public_bytes(finding) for finding in singular.findings]

    (tmp_path / "sc-referee.yaml").write_text(yaml.safe_dump(_config(multi=True), sort_keys=False))
    multi = run_audit(tmp_path, engine="simple")
    de_findings = _by_claim(multi)["results/de.csv"]

    assert [public_bytes(finding) for finding in de_findings] == singular_bytes


def test_unresolved_second_producer_gates_only_double_dipping(tmp_path):
    _fixture(tmp_path, multi=True)
    # A mannwhitneyu exists in the file, but the serialized table no longer depends on it. Mere
    # co-occurrence is not a claim binding and cannot authorize a double-dipping flag. The design
    # checks do not consume producer identity and must still evaluate the declared per-cell claim.
    (tmp_path / "analysis.py").write_text(SOURCE.replace(
        "'gene': ['NRXN1'], 'pvalue': [pvalue], 'padj': [pvalue], 'log2fc': [0.25]",
        "'gene': ['NRXN1'], 'pvalue': [0.5], 'padj': [0.5], 'log2fc': [0.25]",
    ))

    claims = _by_claim(run_audit(tmp_path, engine="simple"))
    assert _states(claims["results/de.csv"]) == DE_STATES
    assert _states(claims["results/splicing.csv"]) == SPLICING_STATES
    splicing = {finding.check_id: finding for finding in claims["results/splicing.csv"]}

    assert S.human_state(splicing["confounding"]) == S.CLEAR
    assert S.human_state(splicing["experimental_unit"]) == S.NOT_CHECKED
    assert S.human_state(splicing["pairing"]) == S.FLAGGED
    assert splicing["double_dipping"].coverage == S.NOT_RUN
    assert S.human_state(splicing["double_dipping"]) == S.NOT_CHECKED


def test_competing_second_writer_gates_only_double_dipping(tmp_path):
    _fixture(tmp_path, multi=True)
    (tmp_path / "stale_export.py").write_text("""\
import pandas as pd
stale = pd.DataFrame({'gene': ['NRXN1'], 'pvalue': [0.9]})
stale.to_csv('results/splicing.csv', index=False)
""")

    claims = _by_claim(run_audit(tmp_path, engine="simple"))
    assert _states(claims["results/de.csv"]) == DE_STATES
    assert _states(claims["results/splicing.csv"]) == SPLICING_STATES
    splicing = {finding.check_id: finding for finding in claims["results/splicing.csv"]}

    assert S.human_state(splicing["confounding"]) == S.CLEAR
    assert S.human_state(splicing["experimental_unit"]) == S.NOT_CHECKED
    assert S.human_state(splicing["pairing"]) == S.FLAGGED
    assert splicing["double_dipping"].coverage == S.NOT_RUN
    assert S.human_state(splicing["double_dipping"]) == S.NOT_CHECKED


def test_two_analysis_demo_render_is_frozen(tmp_path):
    _fixture(tmp_path, multi=True)
    result = run_audit(tmp_path, engine="simple")
    payload = json.loads(to_json(result))

    assert [analysis["claim"]["report_path"] for analysis in payload["analyses"]] == [
        "results/de.csv", "results/splicing.csv",
    ]
    # Differential no-regression: enumerate every cell, not only the two crux cells.
    assert [[
        (finding["check_id"], finding["human_state"])
        for finding in analysis["findings"]
    ] for analysis in payload["analyses"]] == [
        DE_STATES,
        SPLICING_STATES,
    ]

    console = Console(record=True, width=120, color_system=None)
    render_tty(result, console)
    rendered = console.export_text()
    assert rendered == FROZEN_TTY.read_text()


# --- fast-follow #52: string-target monkeypatch of an egress method must fail the scoper closed ------
def test_string_target_monkeypatch_of_to_csv_fails_closed():
    """red-team blocker 6: a mock.patch of DataFrame.to_csv by string target (before extraction) must
    not leave the egress trusted — the <df>.to_csv link is unsound, so the scoper fails closed."""
    from sc_referee.producer_binding import bind_marker_extraction_report_producers as scope
    src = (
        "import scanpy as sc\n"
        "from unittest.mock import patch\n"
        "patch('pandas.core.generic.DataFrame.to_csv', new=lambda *a, **k: None).start()\n"
        "de = sc.get.rank_genes_groups_df(adata)\n"
        "de.to_csv('x.csv')\n"
    )
    assert scope((src,)) == {}


def test_monkeypatch_by_setattr_string_also_fails_closed():
    from sc_referee.producer_binding import bind_marker_extraction_report_producers as scope
    src = (
        "import scanpy as sc\n"
        "mp.setattr('pandas.core.generic.DataFrame.to_parquet', fake)\n"
        "de = sc.get.rank_genes_groups_df(adata)\n"
        "de.to_parquet('x.parquet')\n"
    )
    assert scope((src,)) == {}


def test_clean_marker_egress_still_resolves_no_egress_string():
    """guard: an honest analysis (no egress-method string literal) still resolves."""
    from sc_referee.producer_binding import bind_marker_extraction_report_producers as scope
    src = (
        "import scanpy as sc\n"
        "de = sc.get.rank_genes_groups_df(adata, group='neuronal')\n"
        "de.to_csv('results/de.csv')\n"
    )
    assert 'results/de.csv' in scope((src,))
