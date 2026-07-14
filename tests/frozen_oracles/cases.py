"""Inputs frozen from every legacy provenance, sink-binding, and confounding test shape.

The expected public outputs live in ``legacy_oracles.json``.  This module intentionally contains
only input construction; regenerating the output file is a deliberate review action.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from tests.factories import (
    alias_obs,
    make_design,
    paired_crossed_obs,
    single_bridge_obs,
    unpaired_crossed_obs,
    unpaired_nobatch_obs,
)


def source_cases():
    notebook = json.dumps({"cells": [
        {"cell_type": "markdown", "source": ["# markers\n"]},
        {"cell_type": "code", "source": [
            "import scanpy as sc\n", "sc.tl.rank_genes_groups(adata, groupby='grp')\n",
        ]},
    ]})
    magic_notebook = json.dumps({"cells": [{"cell_type": "code", "source": [
        "%matplotlib inline\n", "labels = discover(adata.X)\n", "adata.obs['sub'] = labels\n",
        "sc.tl.rank_genes_groups(adata, groupby='sub')\n",
    ]}]})
    cases = [
        ("bespoke_embedding", ["import scanpy as sc\nlabels = discover_subpops(adata.obsm['X_pca'])\nadata.obs['subpop'] = labels\nsc.tl.rank_genes_groups(adata, groupby='subpop')\n"]),
        ("gmm_matrix", ["from sklearn.mixture import GaussianMixture\nlabels = GaussianMixture(10).fit_predict(adata.X)\nadata.obs['gmm'] = labels\nsc.tl.rank_genes_groups(adata, groupby='gmm')\n"]),
        ("metadata_relabel", ["import scanpy as sc\nadata.obs['condition'] = adata.obs['sample'].map({'s1': 'A', 's2': 'B'})\nsc.tl.rank_genes_groups(adata, groupby='condition')\n"]),
        ("untouched_group", ["import scanpy as sc\nsc.tl.rank_genes_groups(adata, groupby='genotype')\n"]),
        ("dynamic_group", ["import scanpy as sc\ncol = pick_column()\nsc.tl.rank_genes_groups(adata, groupby=col)\n"]),
        ("cross_source_obs", ["adata.obs['subpop'] = kmeans(adata.X)\n", "import scanpy as sc\nsc.tl.rank_genes_groups(adata, groupby='subpop')\n"]),
        ("notebook", ["labels = kmeans(adata.X)\nadata.obs['grp'] = labels\n", notebook]),
        ("implicit_leiden", ["import scanpy as sc\nsc.tl.leiden(adata, key_added='clust')\nsc.tl.rank_genes_groups(adata, groupby='clust')\n"]),
        ("annotated_cluster", ["import scanpy as sc\nsc.tl.leiden(adata, key_added='leiden')\nadata.obs['celltype'] = adata.obs['leiden'].map({'0': 'T', '1': 'B'})\nsc.tl.rank_genes_groups(adata, groupby='celltype')\n"]),
        ("annotated_assignment", ["import scanpy as sc\nlabels: 'np.ndarray' = discover_subpops(adata.obsm['X_pca'])\nadata.obs['sub'] = labels\nsc.tl.rank_genes_groups(adata, groupby='sub')\n"]),
        ("tuple_unpack", ["import scanpy as sc\nlabels, centers = kmeans_with_centers(adata.X)\nadata.obs['sub'] = labels\nsc.tl.rank_genes_groups(adata, groupby='sub')\n"]),
        ("magic_notebook", [magic_notebook]),
        ("parse_failure_marker", ["this is not (valid python at all;;; sc.tl.rank_genes_groups(adata, groupby='x')\n"]),
        ("spatial_external", ["from sklearn.cluster import KMeans\nlabels = KMeans(3).fit_predict(adata.obsm['spatial'])\nadata.obs['region'] = labels\nsc.tl.rank_genes_groups(adata, groupby='region')\n"]),
        ("later_overwrite", ["import scanpy as sc\nadata.obs['B'] = adata.obs['A']\nadata.obs['A'] = kmeans(adata.X)\nsc.tl.rank_genes_groups(adata, groupby='B')\n"]),
        ("obsm_written", ["import scanpy as sc\nadata.obsm['emb'] = pca(adata.X)\nlabels = kmeans(adata.obsm['emb'])\nadata.obs['region'] = labels\nsc.tl.rank_genes_groups(adata, groupby='region')\n"]),
        ("external_adjacency", ["import scanpy as sc\nA = load_external_anatomical_graph()\nsc.tl.leiden(adata, adjacency=A, key_added='region')\nsc.tl.rank_genes_groups(adata, groupby='region')\n"]),
        ("non_anndata_x", ["import scanpy as sc\nimport pandas as pd\nmetadata = pd.read_csv('m.csv')\nlabels = predefined_partition(metadata.X)\nadata.obs['cohort'] = labels\nsc.tl.rank_genes_groups(adata, groupby='cohort')\n"]),
        ("conditional_group", ["import scanpy as sc\nif flag:\n    adata.obs['g'] = discover(adata.X)\nelse:\n    adata.obs['g'] = adata.obs['genotype']\nsc.tl.rank_genes_groups(adata, groupby='g')\n"]),
        ("sc_read_identity", ["import scanpy as sc\nobj = sc.read('input.h5ad')\nobj.obs['g'] = discover(obj.X)\nsc.tl.rank_genes_groups(obj, groupby='g')\n"]),
        ("obsm_external_overwrite", ["import scanpy as sc\nadata.obsm['emb'] = pca(adata.X)\nadata.obsm['emb'] = load_external_embedding()\nlabels = cluster(adata.obsm['emb'])\nadata.obs['g'] = labels\nsc.tl.rank_genes_groups(adata, groupby='g')\n"]),
        ("positional_group", ["import scanpy as sc\nsc.tl.rank_genes_groups(adata, 'leiden')\n"]),
        ("scanpy_alias", ["import scanpy as sx\nsx.tl.rank_genes_groups(adata, 'leiden')\n"]),
        ("local_ttest", ["def ttest_ind(a, b):\n    return donor_blocked_permutation(a, b)\nresult = ttest_ind(case, control)\n"]),
        ("unknown_numpy", ["import numpy as np\nnp.mean(adata.X)\n"]),
        ("unimported_ttest", ["ttest_ind(a, b)\n"]),
        ("deseq", ["from pydeseq2.dds import DeseqDataSet\ndds = DeseqDataSet(counts=cts, metadata=md, design='~condition')\n"]),
        ("deseq_splat", ["from pydeseq2.dds import DeseqDataSet\ndds = DeseqDataSet(**cfg)\n"]),
        ("deseq_optional_splat", ["from pydeseq2.dds import DeseqDataSet\ndds = DeseqDataSet(counts=c, metadata=m, **cfg)\n"]),
        ("parse_failure_sink", ["import scipy.stats as st\nst.ttest_ind(a, b)\nif\n"]),
        ("duplicate_argument", ["import scipy.stats as st\nst.ttest_ind(x, y, a=z)\n"]),
        ("per_source_imports", ["import scanpy as sc\nsc.tl.rank_genes_groups(adata, 'leiden')\n", "import my_pipeline as sc\nsc.run()\n"]),
        ("lookalike_module", ["import project.scipy.stats as stats\nstats.ttest_ind(a, b)\n"]),
        ("star_import", ["from scipy.stats import *\nttest_ind(a, b)\n"]),
        ("ambiguous_import", ["import project.custom_stats as stats\nstats.ttest_ind(a, b)\nimport scipy.stats as stats\n"]),
        ("match_capture", ["import scipy.stats as stats\nmatch obj:\n    case {'stats': stats}:\n        stats.ttest_ind(a, b)\n"]),
        ("patch_prefix", ["import scanpy as sc\nsc.tl = custom_ns\nsc.tl.rank_genes_groups(adata, 'g')\n"]),
        ("patch_alias", ["import scanpy as sc\nt = sc.tl\nt.rank_genes_groups = custom\nsc.tl.rank_genes_groups(adata, 'g')\n"]),
        ("ambiguous_sink_alias", ["from scipy.stats import ttest_ind as welch\ndef unrelated(welch):\n    return welch\nresult = welch(a, b)\n"]),
        ("indirect_attribute", ["import scanpy as sc\ntest = sc.tl.rank_genes_groups\ntest(adata, 'g')\n"]),
        ("indirect_getattr", ["import scipy.stats as stats\ngetattr(stats, 'ttest_ind')(a, b)\n"]),
        ("uppercase_sink", ["from pydeseq2.dds import DESEQDATASET\nDESEQDATASET(counts=c, metadata=m, design='~x')\n"]),
        ("patch_for_target", ["import scanpy as sc\nfor sc.tl.rank_genes_groups in [custom]:\n    sc.tl.rank_genes_groups(adata, 'g')\n"]),
        ("patch_with_target", ["import scanpy as sc\nwith cm() as sc.tl.rank_genes_groups:\n    sc.tl.rank_genes_groups(adata, 'g')\n"]),
        ("patch_globals", ["import scipy.stats as stats\nglobals()['stats'] = custom\nstats.ttest_ind(a, b)\n"]),
        ("patch_setattr_alias", ["import scanpy as sc\nsa = setattr\nsa(sc.tl, 'rank_genes_groups', custom)\nsc.tl.rank_genes_groups(adata, 'g')\n"]),
        ("patch_object", ["import scanpy as sc\npatch.object(sc.tl, 'rank_genes_groups', custom)\nsc.tl.rank_genes_groups(adata, 'g')\n"]),
        ("multiple_from_import", ["from scipy.stats import ttest_ind as test\nresult = test(a, b)\nfrom project import custom as test\n"]),
        ("relative_import", ["from .stats import ttest_ind as test\ntest(a, b)\n"]),
        ("dict_lookup", ["import scipy.stats as stats\nstats.__dict__['ttest_ind'](a, b)\n"]),
        ("globals_update", ["import scipy.stats as stats\nglobals().update(stats=custom)\nstats.ttest_ind(a, b)\n"]),
        ("module_dict_update", ["import scanpy as sc\nsc.tl.__dict__.update(rank_genes_groups=custom)\nsc.tl.rank_genes_groups(adata, 'g')\n"]),
        ("globals_dict_update", ["import scipy.stats as stats\nglobals().update({'stats': custom})\nstats.ttest_ind(a, b)\n"]),
        ("patch_object_keywords", ["import scanpy as sc\npatch.object(target=sc.tl, attribute='rank_genes_groups', new=custom)\nsc.tl.rank_genes_groups(adata, 'g')\n"]),
        ("getattribute", ["import scipy.stats as stats\nstats.__getattribute__('ttest_ind')(a, b)\n"]),
        ("fixture_ambiguous_group", [
            (Path(__file__).parents[2] / "fixtures" / "ambiguous_group" / "analysis.py").read_text()
        ]),
    ]
    return cases


def _obs(rows, columns):
    frame = pd.DataFrame(rows, columns=columns)
    frame.insert(0, "donor_id", [f"D{i + 1}" for i in range(len(frame))])
    return frame


def confounding_cases():
    from sc_referee.config import load_designs
    from sc_referee.ingest import ingest

    weak = _obs(([('ctrl', 'R1')] * 10 + [('ctrl', 'R2')] * 10
                 + [('stim', 'R1')] * 9 + [('stim', 'R2')] * 11), ["condition", "run"])
    near = _obs([('ctrl', 'R1')] * 20 + [('stim', 'R1')] + [('stim', 'R2')] * 19,
                ["condition", "run"])
    partial = _obs([('ctrl', 'R1')] * 3 + [('stim', 'R1')] + [('ctrl', 'R2')]
                   + [('stim', 'R2')] * 3, ["condition", "run"])
    xor = _obs([(condition, run, sex)
                for run in ("R1", "R2") for sex in ("M", "F")
                for condition in (["ctrl"] * 2 if (run == "R1") == (sex == "M") else ["stim"] * 2)],
               ["condition", "run", "sex"])
    one_per_cell = _obs([(condition, run) for run in ("R1", "R2", "R3")
                         for condition in ("ctrl", "stim")], ["condition", "run"])
    absent = pd.DataFrame({"donor_id": [f"D{i}" for i in range(6)],
                           "condition": ["ctrl"] * 6, "run": ["R1", "R2"] * 3})
    varying = pd.DataFrame({"donor_id": ["D1", "D1", "D2", "D2"],
                            "condition": ["ctrl", "ctrl", "stim", "stim"],
                            "run": ["R1", "R2", "R2", "R2"]})
    high_cardinality = []
    for run in range(40):
        conditions = ["ctrl", "ctrl"] if run < 20 else (["stim", "stim"] if run < 39 else ["ctrl", "stim"])
        high_cardinality.extend((f"D{run}_{i}", condition, f"R{run}")
                                for i, condition in enumerate(conditions))
    high_cardinality = pd.DataFrame(high_cardinality, columns=["donor_id", "condition", "run"])

    def captured(adjusted_for, **kwargs):
        """Reconstruct the legacy cases with their formerly implicit fitted-model fact explicit."""
        return make_design(analyst_adjusted_for=adjusted_for, **kwargs)

    cases = [
        ("alias_confirmed", alias_obs(), captured(["condition"], sample_unit=("donor_id",))),
        ("paired_crossed", paired_crossed_obs(), captured(["condition"], sample_unit=("donor_id", "condition"))),
        ("alias_unconfirmed", alias_obs(), captured(["condition"], confirmed=False, sample_unit=("donor_id",))),
        ("alias_low_condition", alias_obs(), captured(["condition"], condition_confidence_high=False, sample_unit=("donor_id",))),
        ("alias_low_replicate", alias_obs(), captured(["condition"], confidence_high=False, sample_unit=("donor_id",))),
        ("missing_level", absent, captured(["condition"], sample_unit=("donor_id",))),
        ("varying_covariate", varying, captured(["condition"], sample_unit=("donor_id",))),
        ("weak_omitted", weak, captured(["condition"], model="~ condition", batch=("run",), sample_unit=("donor_id",))),
        ("near_adjusted", near, captured(["run", "condition"], model="~ run + condition", batch=("run",), sample_unit=("donor_id",))),
        ("near_omitted", near, captured(["condition"], model="~ condition", batch=("run",), sample_unit=("donor_id",))),
        ("partial_omitted", partial, captured(["condition"], model="~ condition", batch=("run",), sample_unit=("donor_id",))),
        ("partial_adjusted", partial, captured(["run", "condition"], model="~ run + condition", batch=("run",), sample_unit=("donor_id",))),
        ("partial_patsy", partial, captured(["run", "condition"], model="~ C(run) + condition", batch=("run",), sample_unit=("donor_id",))),
        ("xor_additive", xor, captured(["sex", "condition"], model="~ sex + condition", batch=("run",), sample_unit=("donor_id",))),
        ("one_per_cell", one_per_cell, captured(["condition"], batch=("run",), sample_unit=("donor_id",))),
        ("unpaired_crossed", unpaired_crossed_obs(), captured(["condition"], sample_unit=("donor_id",))),
        ("unpaired_no_batch", unpaired_nobatch_obs(), captured(["condition"], batch=(), sample_unit=("donor_id",))),
        ("donor_in_model", unpaired_crossed_obs(), captured(["donor_id", "condition"], model="~ donor_id + condition", batch=(), sample_unit=("donor_id",))),
        ("single_bridge", single_bridge_obs(), captured(["condition"], sample_unit=("donor_id",))),
        ("high_cardinality", high_cardinality, captured(["condition"], model="~ condition", batch=("run",), sample_unit=("donor_id",))),
        ("clean_reverse_contrast", pd.DataFrame({"donor_id": [f"D{i}" for i in range(6)], "condition": ["ctrl"] * 3 + ["stim"] * 3}), captured(["condition"], batch=(), sample_unit=("donor_id",), reference="stim", test="ctrl")),
    ]
    fixture = Path(__file__).parents[2] / "fixtures" / "confounding_alias"
    fixture_design = load_designs(fixture / "sc-referee.yaml")[0]
    fixture_design.analyst_adjusted_for = ["culture_condition"]
    fixture_design.confidence["analyst_adjusted_for"] = "high"
    cases.append(("fixture_confounding_alias", ingest(fixture).observations, fixture_design))
    return cases
