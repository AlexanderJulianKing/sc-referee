"""Layer 2 provenance (Phase A, increment 1): classify a marker/DE test's grouping column as
`data_derived`, `predefined_within_program`, or `unresolved` by tracing the expression matrix through
the code — NOT by matching method names. Method-agnostic by construction: a bespoke clustering
function is caught exactly like `leiden`, because taint follows the data, not the name.

This increment computes the MAY-level origin that drives the bundle verdict (`data_derived` →
needs_evidence). The must/overlap/tri-state/coverage machinery a *blocker* needs is later increments;
until then a data-derived grouping escalates, it does not silently accuse or clear.
"""


def test_bespoke_fn_on_embedding_makes_grouping_data_derived():
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "labels = discover_subpops(adata.obsm['X_pca'])\n"      # custom fn, no vocab entry
           "adata.obs['subpop'] = labels\n"
           "sc.tl.rank_genes_groups(adata, groupby='subpop')\n")
    tests = groupby_provenance([src])
    assert len(tests) == 1
    assert tests[0].groupby == "subpop"
    assert tests[0].origin == "data_derived"


def test_gmm_direct_matrix_access_is_data_derived():
    from sc_referee.provenance import groupby_provenance
    src = ("from sklearn.mixture import GaussianMixture\n"
           "labels = GaussianMixture(10).fit_predict(adata.X)\n"   # the pbmc_dex shape
           "adata.obs['gmm'] = labels\n"
           "sc.tl.rank_genes_groups(adata, groupby='gmm')\n")
    assert groupby_provenance([src])[0].origin == "data_derived"


def test_metadata_relabel_is_predefined():
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "adata.obs['condition'] = adata.obs['sample'].map({'s1': 'A', 's2': 'B'})\n"
           "sc.tl.rank_genes_groups(adata, groupby='condition')\n")
    assert groupby_provenance([src])[0].origin == "predefined_within_program"


def test_untouched_input_column_is_predefined():
    from sc_referee.provenance import groupby_provenance
    src = "import scanpy as sc\nsc.tl.rank_genes_groups(adata, groupby='genotype')\n"
    assert groupby_provenance([src])[0].origin == "predefined_within_program"


def test_dynamic_groupby_is_unresolved():
    from sc_referee.provenance import groupby_provenance
    src = "import scanpy as sc\ncol = pick_column()\nsc.tl.rank_genes_groups(adata, groupby=col)\n"
    t = groupby_provenance([src])[0]
    assert t.groupby is None and t.origin == "unresolved"


def test_cross_file_shared_obs_namespace():
    from sc_referee.provenance import groupby_provenance
    s1 = "adata.obs['subpop'] = kmeans(adata.X)\n"                                  # created step 1
    s2 = "import scanpy as sc\nsc.tl.rank_genes_groups(adata, groupby='subpop')\n"  # tested step 2
    t = [t for t in groupby_provenance([s1, s2]) if t.groupby == "subpop"][0]
    assert t.origin == "data_derived"


def test_notebook_source_is_parsed_not_skipped():
    """A .ipynb step's source is JSON, not Python — provenance must extract the code cells (the marker
    test in pbmc_dex lived in a notebook and was invisible). Never skip a step silently."""
    import json
    from sc_referee.provenance import groupby_provenance
    py_cluster = "labels = kmeans(adata.X)\nadata.obs['grp'] = labels\n"
    nb = json.dumps({"cells": [
        {"cell_type": "markdown", "source": ["# markers\n"]},
        {"cell_type": "code", "source": ["import scanpy as sc\n",
                                         "sc.tl.rank_genes_groups(adata, groupby='grp')\n"]}]})
    hit = [t for t in groupby_provenance([py_cluster, nb]) if t.groupby == "grp"]
    assert hit and hit[0].origin == "data_derived"


def test_implicit_leiden_key_added_is_data_derived():
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "sc.tl.leiden(adata, key_added='clust')\n"
           "sc.tl.rank_genes_groups(adata, groupby='clust')\n")
    assert groupby_provenance([src])[0].origin == "data_derived"


def test_annotated_clusters_are_still_data_derived():
    """Annotating a data-derived cluster (obs['celltype'] = obs['leiden'].map(...)) and testing on it
    is STILL de-novo — taint must flow through a data-derived obs column, not stop at it."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "sc.tl.leiden(adata, key_added='leiden')\n"
           "adata.obs['celltype'] = adata.obs['leiden'].map({'0': 'T', '1': 'B'})\n"
           "sc.tl.rank_genes_groups(adata, groupby='celltype')\n")
    assert groupby_provenance([src])[0].origin == "data_derived"


# --- non-X_ embedding written from an OPAQUE call (the scvi/harmony false-clearance, task #47) -------
# A latent stored under a non-`X_` obsm key via an opaque call (`model.get_latent_representation()`)
# was silently CLEARED: the X_-prefix taint rule missed it and the opaque RHS never populated
# obsm_data. Clustering on it and testing markers therefore read as `predefined_within_program`
# (a green clean). We cannot PROVE it is expression-derived (it might be external coords), so the
# honest verdict is `unresolved` (abstain / needs_evidence) — never a silent clean, never an accusation.

def test_opaque_write_to_non_X_obsm_then_cluster_is_unresolved():
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "from sklearn.mixture import GaussianMixture\n"
           "adata.obsm['scVI'] = model.get_latent_representation()\n"   # non-X_ key, opaque call
           "adata.obs['cluster'] = GaussianMixture(2).fit_predict(adata.obsm['scVI'])\n"
           "sc.tl.rank_genes_groups(adata, groupby='cluster')\n")
    assert groupby_provenance([src])[0].origin == "unresolved"


def test_opaque_write_to_X_prefixed_obsm_stays_data_derived():
    """Regression guard: the X_ convention is still caught as expression (data_derived), unchanged."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "from sklearn.mixture import GaussianMixture\n"
           "adata.obsm['X_scVI'] = model.get_latent_representation()\n"
           "adata.obs['cluster'] = GaussianMixture(2).fit_predict(adata.obsm['X_scVI'])\n"
           "sc.tl.rank_genes_groups(adata, groupby='cluster')\n")
    assert groupby_provenance([src])[0].origin == "data_derived"


def test_external_obsm_no_inscript_write_stays_predefined():
    """Regression guard (must NOT over-abstain): external coordinates never written in-script
    (`obsm['spatial']` supplied with the AnnData) stay predefined — clustering on them is valid."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "from sklearn.mixture import GaussianMixture\n"
           "adata.obs['cluster'] = GaussianMixture(2).fit_predict(adata.obsm['spatial'])\n"
           "sc.tl.rank_genes_groups(adata, groupby='cluster')\n")
    assert groupby_provenance([src])[0].origin == "predefined_within_program"


def test_obsm_written_from_visible_data_stays_data_derived():
    """Regression guard: a visible data write (obsm['scVI'] = adata.X[...]) is data_derived via the
    existing obsm_data mechanism, even under a non-X_ key — the opaque path must not shadow it."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "from sklearn.mixture import GaussianMixture\n"
           "adata.obsm['scVI'] = adata.X[:, :10]\n"
           "adata.obs['cluster'] = GaussianMixture(2).fit_predict(adata.obsm['scVI'])\n"
           "sc.tl.rank_genes_groups(adata, groupby='cluster')\n")
    assert groupby_provenance([src])[0].origin == "data_derived"


def test_plain_external_value_write_to_obsm_stays_predefined():
    """Regression guard (must NOT over-abstain): an obsm key assigned a plain external value (a bare
    name, not a computed call) is treated as external — predefined, not abstained."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "from sklearn.mixture import GaussianMixture\n"
           "adata.obsm['ext'] = external_coords\n"                       # bare Name RHS, not a call
           "adata.obs['cluster'] = GaussianMixture(2).fit_predict(adata.obsm['ext'])\n"
           "sc.tl.rank_genes_groups(adata, groupby='cluster')\n")
    assert groupby_provenance([src])[0].origin == "predefined_within_program"


# --- opacity must be a FULL symmetric taint (Codex review of #47): a monotonic may-set so branch
# order can't silently clear, and propagation through obs relabels and local variables like data does.

def test_opaque_in_one_branch_is_unresolved_regardless_of_order():
    """A silent clean must not depend on lexical branch order: opaque in one arm, meta in the other
    must escalate to unresolved (mirror of may_data). Both orderings must agree."""
    from sc_referee.provenance import groupby_provenance
    opaque_first = ("import scanpy as sc\n"
                    "from sklearn.mixture import GaussianMixture\n"
                    "adata.obsm['scVI'] = model.get_latent_representation()\n"
                    "if flag:\n"
                    "    adata.obs['g'] = GaussianMixture(2).fit_predict(adata.obsm['scVI'])\n"
                    "else:\n"
                    "    adata.obs['g'] = adata.obs['condition']\n"
                    "sc.tl.rank_genes_groups(adata, groupby='g')\n")
    meta_first = ("import scanpy as sc\n"
                  "from sklearn.mixture import GaussianMixture\n"
                  "adata.obsm['scVI'] = model.get_latent_representation()\n"
                  "if flag:\n"
                  "    adata.obs['g'] = adata.obs['condition']\n"
                  "else:\n"
                  "    adata.obs['g'] = GaussianMixture(2).fit_predict(adata.obsm['scVI'])\n"
                  "sc.tl.rank_genes_groups(adata, groupby='g')\n")
    assert groupby_provenance([opaque_first])[0].origin == "unresolved"
    assert groupby_provenance([meta_first])[0].origin == "unresolved"


def test_opacity_propagates_through_obs_relabel():
    """Idiomatic: annotate the opaque cluster, then test the annotation. Opacity must flow through the
    obs->obs relabel exactly as data-derivedness does (cf. test_annotated_clusters_are_still...)."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "from sklearn.mixture import GaussianMixture\n"
           "adata.obsm['scVI'] = model.get_latent_representation()\n"
           "adata.obs['cluster'] = GaussianMixture(2).fit_predict(adata.obsm['scVI'])\n"
           "adata.obs['celltype'] = adata.obs['cluster'].map({'0': 'A', '1': 'B'})\n"
           "sc.tl.rank_genes_groups(adata, groupby='celltype')\n")
    assert groupby_provenance([src])[0].origin == "unresolved"


def test_opacity_propagates_through_local_variable():
    """Opacity must flow through a local intermediate variable, mirroring the data-tainted locals set."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "from sklearn.mixture import GaussianMixture\n"
           "adata.obsm['scVI'] = model.get_latent_representation()\n"
           "labels = GaussianMixture(2).fit_predict(adata.obsm['scVI'])\n"
           "adata.obs['cluster'] = labels\n"
           "sc.tl.rank_genes_groups(adata, groupby='cluster')\n")
    assert groupby_provenance([src])[0].origin == "unresolved"


def test_annotated_assignment_taints():
    """Codex finding 7: `labels: np.ndarray = discover(X)` (AnnAssign) must not lose taint."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "labels: 'np.ndarray' = discover_subpops(adata.obsm['X_pca'])\n"
           "adata.obs['sub'] = labels\n"
           "sc.tl.rank_genes_groups(adata, groupby='sub')\n")
    assert groupby_provenance([src])[0].origin == "data_derived"


def test_tuple_unpacking_taints():
    """Codex finding 7: `labels, centers = kmeans(X)` must taint labels."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "labels, centers = kmeans_with_centers(adata.X)\n"
           "adata.obs['sub'] = labels\n"
           "sc.tl.rank_genes_groups(adata, groupby='sub')\n")
    assert groupby_provenance([src])[0].origin == "data_derived"


def test_notebook_magic_is_stripped_before_parse():
    """Codex finding 3: a notebook magic (%matplotlib) must not make the whole cell unparseable and
    silently drop the marker test."""
    import json
    from sc_referee.provenance import groupby_provenance
    nb = json.dumps({"cells": [{"cell_type": "code", "source": [
        "%matplotlib inline\n",
        "labels = discover(adata.X)\n",
        "adata.obs['sub'] = labels\n",
        "sc.tl.rank_genes_groups(adata, groupby='sub')\n"]}]})
    assert groupby_provenance([nb])[0].origin == "data_derived"


def test_unparseable_source_with_marker_token_surfaces_unresolved():
    """Codex finding 3: if a source containing a marker call cannot be parsed at all, do not let it
    vanish — surface an unresolved marker test so the gate escalates."""
    from sc_referee.provenance import groupby_provenance
    src = "this is not (valid python at all;;; sc.tl.rank_genes_groups(adata, groupby='x')\n"
    tests = groupby_provenance([src])
    assert tests and any(t.origin == "unresolved" for t in tests)


def test_clustering_on_spatial_coords_is_not_data_derived():
    """Codex's false-accuse case: clustering on EXTERNAL spatial coordinates (obsm['spatial'], not an
    expression embedding) then testing genes is not circular w.r.t. the genes — the regions are
    predefined relative to the tested features. Only X_-prefixed embeddings (X_pca/X_umap/...) and
    .X/.layers/.raw count as expression. (spec §4.1/§4.3)"""
    from sc_referee.provenance import groupby_provenance
    src = ("from sklearn.cluster import KMeans\n"
           "labels = KMeans(3).fit_predict(adata.obsm['spatial'])\n"
           "adata.obs['region'] = labels\n"
           "sc.tl.rank_genes_groups(adata, groupby='region')\n")
    assert groupby_provenance([src])[0].origin != "data_derived"


def test_later_overwrite_does_not_taint_an_earlier_read():
    """Codex finding 6: flow-sensitivity. `B = A` copies A's value AT THAT POINT (predefined); a LATER
    overwrite `A = cluster(X)` must not retroactively taint B."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "adata.obs['B'] = adata.obs['A']\n"          # A is predefined here
           "adata.obs['A'] = kmeans(adata.X)\n"          # later overwrite
           "sc.tl.rank_genes_groups(adata, groupby='B')\n")
    assert groupby_provenance([src])[0].origin != "data_derived"


def test_obsm_written_from_expression_is_tracked():
    """Codex finding 4a: an obsm key VISIBLY written from expression is data-derived even without an
    X_ name — track obsm writes, don't judge by the key name alone."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "adata.obsm['emb'] = pca(adata.X)\n"          # 'emb' is written from X
           "labels = kmeans(adata.obsm['emb'])\n"
           "adata.obs['region'] = labels\n"
           "sc.tl.rank_genes_groups(adata, groupby='region')\n")
    assert groupby_provenance([src])[0].origin == "data_derived"


def test_implicit_clustering_on_external_adjacency_is_not_data_derived():
    """Codex finding 4b: leiden on an EXTERNAL adjacency graph is not derived from the expression, so
    its output is not data-derived. Implicit clustering must be gated on its operative input."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "A = load_external_anatomical_graph()\n"
           "sc.tl.leiden(adata, adjacency=A, key_added='region')\n"
           "sc.tl.rank_genes_groups(adata, groupby='region')\n")
    assert groupby_provenance([src])[0].origin != "data_derived"


def test_dot_x_on_non_anndata_receiver_is_not_expression():
    """Codex finding 9: `metadata.X` where metadata is a DataFrame is not the expression matrix. Only
    a known AnnData receiver's .X/.obsm/.layers count."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\nimport pandas as pd\n"
           "metadata = pd.read_csv('m.csv')\n"
           "labels = predefined_partition(metadata.X)\n"
           "adata.obs['cohort'] = labels\n"
           "sc.tl.rank_genes_groups(adata, groupby='cohort')\n")
    assert groupby_provenance([src])[0].origin != "data_derived"


def test_conditional_data_derived_branch_is_not_silently_clean():
    """Codex re-review #1: a column assigned data-derived in ONE branch must not read as predefined
    just because the other (predefined) branch is written last. Escalate (unresolved/data), don't clear."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "if flag:\n"
           "    adata.obs['g'] = discover(adata.X)\n"
           "else:\n"
           "    adata.obs['g'] = adata.obs['genotype']\n"
           "sc.tl.rank_genes_groups(adata, groupby='g')\n")
    assert groupby_provenance([src])[0].origin != "predefined_within_program"


def test_sc_read_result_is_recognized_as_anndata():
    """Codex re-review #2: `obj = sc.read(...)` binds an AnnData, so obj.X is the expression matrix."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "obj = sc.read('input.h5ad')\n"
           "obj.obs['g'] = discover(obj.X)\n"
           "sc.tl.rank_genes_groups(obj, groupby='g')\n")
    assert groupby_provenance([src])[0].origin == "data_derived"


def test_obsm_key_overwritten_by_external_is_no_longer_data():
    """Codex re-review #6: a data-derived obsm key overwritten by an external value must lose taint."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "adata.obsm['emb'] = pca(adata.X)\n"
           "adata.obsm['emb'] = load_external_embedding()\n"
           "labels = cluster(adata.obsm['emb'])\n"
           "adata.obs['g'] = labels\n"
           "sc.tl.rank_genes_groups(adata, groupby='g')\n")
    assert groupby_provenance([src])[0].origin != "data_derived"


def test_relabel_of_predefined_obs_column_stays_predefined():
    """Specificity guard for the above: a relabel of a NON-data-derived obs column
    (obs['grp'] = obs['sample'].map(...)) must remain predefined — taint flows through data-derived
    obs columns only, not every obs column."""
    from sc_referee.provenance import groupby_provenance
    src = ("import scanpy as sc\n"
           "adata.obs['grp'] = adata.obs['sample'].map({'s1': 'A', 's2': 'B'})\n"
           "sc.tl.rank_genes_groups(adata, groupby='grp')\n")
    assert groupby_provenance([src])[0].origin == "predefined_within_program"
