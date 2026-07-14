"""Synthetic, folder-shaped validation battery for the shipped ``run_audit`` API.

The analysis scripts are parsed, never executed.  Every folder nevertheless contains the same
artifacts as a small real analysis: AnnData, analysis source, confirmed design, and reported CSVs.
Ground truth is declared independently here; benchmark code never changes an engine verdict.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import anndata as ad
import numpy as np
import pandas as pd
import yaml

from sc_referee import statuses as S
from sc_referee.audit import run_audit


FLAGGED = "flagged"
CLEAR = "clear"
NOT_CHECKED = "not_checked"
NOT_FLAGGED = "not_flagged"
NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class Expectation:
    invariant: str
    expected: str
    rationale: str
    correct_analysis: bool
    claim_path: str | None = None


@dataclass(frozen=True)
class Scenario:
    name: str
    title: str
    build: Callable[[Path], None]
    expectations: tuple[Expectation, ...]


@dataclass(frozen=True)
class ScoreRow:
    scenario: str
    invariant: str
    expected: str
    actual: str
    actual_status: str
    correct: bool
    correct_analysis: bool
    rationale: str
    verdict: str

    @property
    def false_alarm(self) -> bool:
        return self.correct_analysis and self.actual == FLAGGED

    @property
    def caught(self) -> bool:
        return self.expected == FLAGGED and self.actual == FLAGGED

    @property
    def diagnostic(self) -> str:
        return (f"{self.scenario}/{self.invariant}: expected {self.expected}, "
                f"got {self.actual} ({self.actual_status}): {self.verdict}")


@dataclass(frozen=True)
class Scorecard:
    rows: tuple[ScoreRow, ...]

    @property
    def false_alarms(self) -> tuple[ScoreRow, ...]:
        return tuple(row for row in self.rows if row.false_alarm)

    @property
    def false_alarm_count(self) -> int:
        return len(self.false_alarms)

    @property
    def catch_count(self) -> int:
        return sum(row.caught for row in self.rows)

    @property
    def abstain_count(self) -> int:
        return sum(row.actual == NOT_CHECKED for row in self.rows)

    @property
    def correct_count(self) -> int:
        return sum(row.correct for row in self.rows)


def _is_correct(expected: str, actual: str) -> bool:
    if expected == NOT_FLAGGED:
        return actual != FLAGGED
    return expected == actual


def _genes(n: int = 32) -> list[str]:
    return [f"g{i}" for i in range(n)]


def _paired_data(*, effect: bool = False, normalized: bool = False, seed: int = 7):
    """Eight paired donors with enough genes for stable CPM-based recomputation."""
    rng = np.random.default_rng(seed)
    genes = _genes()
    obs_rows: list[tuple[str, str, str]] = []
    rows: list[np.ndarray] = []
    for donor_i in range(8):
        donor = f"D{donor_i + 1}"
        batch = "B1" if donor_i < 4 else "B2"
        donor_base = rng.integers(85, 116, size=len(genes))
        for condition in ("ctrl", "stim"):
            for _ in range(8):
                values = donor_base.copy()
                if effect and condition == "stim":
                    values[0] += 140
                elif not effect and condition == "stim":
                    # Tiny, sign-balanced donor shifts: per-cell reports can claim hits, while the
                    # powered donor-aware recompute has a stable null centered at zero.
                    values[:10] += 4 if donor_i % 2 == 0 else -4
                rows.append(values)
                obs_rows.append((donor, condition, batch))
    matrix = np.asarray(rows, dtype=np.int32)
    if normalized:
        matrix = np.log1p(matrix.astype(float))
    obs = pd.DataFrame(obs_rows, columns=["donor_id", "condition", "batch"],
                       index=[f"c{i}" for i in range(len(rows))])
    return matrix, obs, genes


def _unpaired_data(*, aliased: bool, seed: int = 11):
    rng = np.random.default_rng(seed)
    genes = _genes()
    obs_rows = []
    rows = []
    for donor_i in range(8):
        donor = f"D{donor_i + 1}"
        condition = "ctrl" if donor_i < 4 else "stim"
        if aliased:
            batch = "B1" if condition == "ctrl" else "B2"
        else:
            batch = "B1" if donor_i in (0, 1, 4, 5) else "B2"
        for _ in range(6):
            values = rng.poisson(90, size=len(genes)).astype(np.int32)
            if condition == "stim":
                values[0] += 60
            rows.append(values)
            obs_rows.append((donor, condition, batch))
    obs = pd.DataFrame(obs_rows, columns=["donor_id", "condition", "batch"],
                       index=[f"c{i}" for i in range(len(rows))])
    return np.asarray(rows), obs, genes


def _report(genes, *, significant: int = 1, uncorrected: bool = False) -> pd.DataFrame:
    genes = list(genes)
    if uncorrected:
        pvalue = np.array([0.04] * significant + [0.90] * (len(genes) - significant))
        padj = pvalue.copy()
    else:
        pvalue = np.array([1e-8] * significant + [0.50] * (len(genes) - significant))
        padj = np.array([1e-6] * significant + [0.80] * (len(genes) - significant))
    return pd.DataFrame({
        "gene": genes,
        "pvalue": pvalue,
        "padj": padj,
        "log2fc": [2.0] * significant + [0.0] * (len(genes) - significant),
    })


def _config(*, analysis_type="condition_contrast_DE", condition="condition",
            reference="ctrl", test="stim", batch=(), unit="cell", paired=True,
            model=None, report_path="results/de.csv", aggregation_key=None,
            claims=None) -> dict:
    model = model or (f"~ {' + '.join([*batch, condition])}" if batch else f"~ {condition}")
    contrast = {
        "name": f"{test}_vs_{reference}", "reference": reference, "test": test,
        "replicate_unit": ["donor_id"], "sample_unit": ["donor_id", condition],
        "pairing_unit": (["donor_id"] if paired else []), "model": model,
        "target_coefficient": f"{condition}[T.{test}]", "unit_of_test": unit,
    }
    if aggregation_key is not None:
        contrast["aggregation_key"] = list(aggregation_key)
    cfg = {
        "analysis_type": analysis_type,
        "confirmed_by_human": True,
        "design": {"condition": condition, "replicate_unit": ["donor_id"], "batch": list(batch)},
        "contrasts": [contrast],
        "reported_results": {"path": report_path, "unit_of_test": unit},
        "confidence": {"replicate_unit": "high", "condition": "high",
                       "aggregation_key": "high"},
    }
    if claims is not None:
        cfg["claims"] = claims
    return cfg


def _write_folder(folder: Path, *, matrix, obs, genes, source: str, report: pd.DataFrame,
                  config: dict, expected: str, report_path: str = "results/de.csv") -> None:
    folder.mkdir(parents=True)
    (folder / "results").mkdir()
    adata = ad.AnnData(X=matrix, obs=obs, var=pd.DataFrame(index=genes))
    if np.issubdtype(np.asarray(matrix).dtype, np.integer):
        adata.layers["counts"] = matrix.copy()
    adata.write_h5ad(folder / "cells.h5ad")
    (folder / "analysis.py").write_text(source)
    report.to_csv(folder / report_path, index=False)
    (folder / "sc-referee.yaml").write_text(yaml.safe_dump(config, sort_keys=False))
    (folder / "EXPECTED.md").write_text(expected.rstrip() + "\n")


MARKER_SOURCE = """\
import scanpy as sc
from sklearn.mixture import GaussianMixture
adata = sc.read_h5ad('cells.h5ad')
labels = GaussianMixture(2).fit_predict(adata.X)
adata.obs['cluster'] = labels.astype(str)
sc.tl.rank_genes_groups(adata, groupby='cluster', method='wilcoxon')
markers = sc.get.rank_genes_groups_df(adata, group='1')
markers.to_csv('results/de.csv', index=False)
"""


EXTERNAL_SOURCE = """\
import scanpy as sc
adata = sc.read_h5ad('cells.h5ad')
sc.tl.rank_genes_groups(adata, groupby='condition', method='wilcoxon')
de = sc.get.rank_genes_groups_df(adata, group='stim')
de.to_csv('results/de.csv', index=False)
"""


PSEUDOBULK_SOURCE = """\
import pandas as pd
from pydeseq2.dds import DeseqDataSet
from pydeseq2.ds import DeseqStats
import scanpy as sc
adata = sc.read_h5ad('cells.h5ad')
counts = pd.DataFrame(adata.layers['counts'], index=adata.obs_names, columns=adata.var_names)
groups = [adata.obs['donor_id'], adata.obs['condition']]
pb = counts.groupby(groups, observed=True).sum()
meta = adata.obs[['donor_id', 'condition']].drop_duplicates().set_index(['donor_id', 'condition'])
dds = DeseqDataSet(counts=pb, metadata=meta, design='~condition')
dds.deseq2()
stats = DeseqStats(dds, contrast=('condition', 'stim', 'ctrl'))
stats.summary()
de = stats.results_df.rename_axis('gene').reset_index()
de.to_csv('results/de.csv', index=False)
"""


def _double_dip(folder: Path) -> None:
    matrix, obs, genes = _paired_data(effect=True)
    obs = obs.rename(columns={"condition": "cluster"})
    obs["cluster"] = obs["cluster"].map({"ctrl": "0", "stim": "1"})
    cfg = _config(analysis_type="marker_detection", condition="cluster", reference="0", test="1",
                  unit="cell", paired=False)
    _write_folder(folder, matrix=matrix, obs=obs, genes=genes, source=MARKER_SOURCE,
                  report=_report(genes, significant=8), config=cfg,
                  expected="Ground truth: expression-derived clusters are tested on the same expression; "
                           "double_dipping must be flagged.")


def _external_grouping(folder: Path) -> None:
    matrix, obs, genes = _paired_data(effect=True)
    cfg = _config(analysis_type="marker_detection", unit="cell", paired=True)
    _write_folder(folder, matrix=matrix, obs=obs, genes=genes, source=EXTERNAL_SOURCE,
                  report=_report(genes, significant=1), config=cfg,
                  expected="Ground truth: condition is pre-existing sample metadata; double_dipping "
                           "must not be flagged.")


def _pseudoreplication(folder: Path) -> None:
    matrix, obs, genes = _paired_data(effect=False)
    cfg = _config(unit="cell", paired=False)
    cfg["contrasts"][0]["report_inference_contract"] = {
        "producer_binding": "exact", "response_scale": "raw_counts",
        "method_family": "rank_based", "dependence_semantics": "iid_rows",
    }
    _write_folder(folder, matrix=matrix, obs=obs, genes=genes, source=EXTERNAL_SOURCE,
                  report=_report(genes, significant=10), config=cfg,
                  expected="Ground truth: cells were tested as independent and paired donors were "
                           "ignored; experimental_unit and pairing must be flagged.")


def _proper_pseudobulk(folder: Path) -> None:
    matrix, obs, genes = _paired_data(effect=True)
    cfg = _config(unit="sample", paired=True, aggregation_key=("donor_id", "condition"))
    _write_folder(folder, matrix=matrix, obs=obs, genes=genes, source=PSEUDOBULK_SOURCE,
                  report=_report(genes, significant=1), config=cfg,
                  expected="Ground truth: raw counts are aggregated by donor and condition before a "
                           "count model; pseudobulk_integrity must clear.")


def _confounding(folder: Path, *, aliased: bool) -> None:
    matrix, obs, genes = _unpaired_data(aliased=aliased)
    cfg = _config(batch=("batch",), unit="sample", paired=False,
                  model="~ batch + condition", aggregation_key=("donor_id", "condition"))
    # This scorecard arm represents a fully specified, correct fitted design rather than an
    # uncaptured one: the analyst's model explicitly contains both labels.
    cfg["contrasts"][0]["analyst_adjusted_for"] = ["batch", "condition"]
    cfg["confidence"]["analyst_adjusted_for"] = "high"
    _write_folder(folder, matrix=matrix, obs=obs, genes=genes, source=PSEUDOBULK_SOURCE,
                  report=_report(genes, significant=1), config=cfg,
                  expected=("Ground truth: condition is perfectly aliased with batch; confounding must "
                            "be flagged." if aliased else
                            "Ground truth: each batch contains both conditions; confounding must clear."))


def _normalized(folder: Path) -> None:
    matrix, obs, genes = _paired_data(effect=True, normalized=True)
    cfg = _config(unit="cell", paired=True)
    _write_folder(folder, matrix=matrix, obs=obs, genes=genes, source=EXTERNAL_SOURCE,
                  report=_report(genes, significant=1), config=cfg,
                  expected="Ground truth: only normalized values are available; the raw-count-dependent "
                           "experimental_unit check must abstain (not_audited).")


ORTHOGONAL_SOURCE = """\
import numpy as np
import pandas as pd
import scanpy as sc
from scipy.stats import mannwhitneyu
adata = sc.read_h5ad('cells.h5ad')
sc.pp.pca(adata)
sc.pp.neighbors(adata)
sc.tl.leiden(adata)
score = np.asarray(adata[:, ['g2', 'g3']].X.mean(axis=1)).ravel()
adata.obs['cell_type'] = np.where(score > np.median(score), 'neuronal', 'other')
sc.tl.rank_genes_groups(adata, groupby='cell_type', method='wilcoxon')
de = sc.get.rank_genes_groups_df(adata, group='neuronal')
de.to_csv('results/de.csv', index=False)
psi = adata.X[:, 0] / (adata.X[:, 0] + adata.X[:, 1])
statistic, pvalue = mannwhitneyu(psi[adata.obs['cell_type'] == 'neuronal'],
                                psi[adata.obs['cell_type'] == 'other'])
splicing = pd.DataFrame({'gene': ['isoform_ratio'], 'pvalue': [pvalue],
                         'padj': [pvalue], 'log2fc': [0.4]})
splicing.to_csv('results/splicing.csv', index=False)
"""


def _orthogonal_axes(folder: Path) -> None:
    rng = np.random.default_rng(19)
    genes = _genes()
    obs_rows, rows = [], []
    for donor_i in range(6):
        for group in ("neuronal", "other"):
            for _ in range(10):
                total = int(rng.poisson(80))
                frac = 0.75 if group == "neuronal" else 0.25
                iso1 = rng.binomial(total, frac)
                values = rng.poisson(20, size=len(genes)).astype(np.int32)
                values[0], values[1] = iso1, total - iso1
                values[2:4] += 70 if group == "neuronal" else 0
                rows.append(values)
                obs_rows.append((f"D{donor_i + 1}", group))
    obs = pd.DataFrame(obs_rows, columns=["donor_id", "cell_type"],
                       index=[f"c{i}" for i in range(len(rows))])
    claims = [
        {"name": "magnitude_markers", "path": "results/de.csv",
         "contrast": "neuronal_vs_other", "unit_of_test": "cell"},
        {"name": "isoform_usage", "path": "results/splicing.csv",
         "contrast": "neuronal_vs_other", "unit_of_test": "cell", "value_kind": "derived_ratio"},
    ]
    cfg = _config(analysis_type="marker_detection", condition="cell_type", reference="other",
                  test="neuronal", unit="cell", paired=True, claims=claims)
    cfg["contrasts"][0]["name"] = "neuronal_vs_other"
    _write_folder(folder, matrix=np.asarray(rows), obs=obs, genes=genes, source=ORTHOGONAL_SOURCE,
                  report=_report(genes, significant=4), config=cfg,
                  expected="Ground truth: clustering uses magnitude genes while the relevant claim tests "
                           "an isoform ratio; double_dipping must not be attributed to splicing.")
    pd.DataFrame({"gene": ["isoform_ratio"], "pvalue": [1e-6], "padj": [1e-5],
                  "log2fc": [0.4]}).to_csv(folder / "results" / "splicing.csv", index=False)


def _uncorrected(folder: Path) -> None:
    matrix, obs, genes = _unpaired_data(aliased=False, seed=23)
    cfg = _config(unit="sample", paired=False, aggregation_key=("donor_id", "condition"))
    cfg["contrasts"][0]["multiplicity_contract"] = {
        "claim_type": "error_controlled_discovery", "error_criterion": "fdr",
        "adjustment_method": "benjamini_hochberg", "family_complete": True,
    }
    _write_folder(folder, matrix=matrix, obs=obs, genes=genes, source=PSEUDOBULK_SOURCE,
                  report=_report(genes, significant=3, uncorrected=True), config=cfg,
                  expected="Ground truth: raw p-values were copied into padj and the calls do not survive "
                           "BH; multiple_testing must be flagged.")


def _wrong_count_model(folder: Path) -> None:
    matrix, obs, genes = _paired_data(effect=True, seed=29)
    source = """\
import pandas as pd
from scipy.stats import ttest_rel
import scanpy as sc
from statsmodels.stats.multitest import multipletests
adata = sc.read_h5ad('cells.h5ad')
counts = pd.DataFrame(adata.layers['counts'], index=adata.obs_names, columns=adata.var_names)
pb = counts.groupby([adata.obs['donor_id'], adata.obs['condition']], observed=True).sum()
ctrl = pb.xs('ctrl', level='condition').sort_index()
stim = pb.xs('stim', level='condition').sort_index()
statistic, pvalue = ttest_rel(stim, ctrl, axis=0)
padj = multipletests(pvalue, method='fdr_bh')[1]
de = pd.DataFrame({'gene': counts.columns, 'pvalue': pvalue, 'padj': padj,
                   'log2fc': statistic})
de.to_csv('results/de.csv', index=False)
"""
    cfg = _config(unit="sample", paired=True, aggregation_key=("donor_id", "condition"))
    cfg["contrasts"][0]["report_inference_contract"] = {
        "producer_binding": "exact", "response_scale": "raw_counts",
        "method_family": "gaussian", "dependence_semantics": "paired",
    }
    _write_folder(folder, matrix=matrix, obs=obs, genes=genes, source=source,
                  report=_report(genes, significant=1), config=cfg,
                  expected="Ground truth: donor pseudobulk counts were analyzed with a Gaussian t-test, "
                           "not a count model; count_model must be flagged.")


def _merged_arms(folder: Path) -> None:
    matrix, obs, genes = _paired_data(effect=True, seed=31)
    cfg = _config(unit="sample", paired=True, aggregation_key=("donor_id",))
    _write_folder(folder, matrix=matrix, obs=obs, genes=genes, source=PSEUDOBULK_SOURCE,
                  report=_report(genes, significant=1), config=cfg,
                  expected="Ground truth: donor-only aggregation merges control and stimulated cells; "
                           "pseudobulk_integrity must be flagged.")


SCENARIOS = (
    Scenario("double_dip", "Cluster then test the same expression", _double_dip, (
        Expectation("double_dipping", FLAGGED, "Same-data selection invalidates marker p-values.", False),)),
    Scenario("external_grouping", "External metadata grouping", _external_grouping, (
        Expectation("double_dipping", NOT_FLAGGED, "Condition was not learned from expression.", True),)),
    Scenario("pseudoreplication", "Cells tested while donors are replicates", _pseudoreplication, (
        Expectation("experimental_unit", FLAGGED, "Cell-level claims collapse at donor level.", False),
        Expectation("pairing", FLAGGED, "The paired-capable donor structure was omitted.", False),)),
    Scenario("proper_pseudobulk", "Proper donor-by-condition pseudobulk", _proper_pseudobulk, (
        Expectation("pseudobulk_integrity", CLEAR, "Aggregation preserves both donor and arm.", True),)),
    Scenario("confounded_design", "Condition perfectly aliases batch",
             lambda p: _confounding(p, aliased=True), (
        Expectation("confounding", FLAGGED, "The condition coefficient is not estimable.", False),)),
    Scenario("balanced_design", "Condition crossed with batch",
             lambda p: _confounding(p, aliased=False), (
        Expectation("confounding", CLEAR, "Both conditions occur in both batches.", True),)),
    Scenario("normalized_only", "Normalized matrix without raw counts", _normalized, (
        Expectation("experimental_unit", NOT_CHECKED, "A raw-count recompute is impossible.", True),)),
    Scenario("orthogonal_axes_splicing", "Magnitude clustering, isoform-ratio test", _orthogonal_axes, (
        Expectation("double_dipping", NOT_FLAGGED, "The splicing producer is outside marker-test coverage.",
                    True, claim_path="results/splicing.csv"),)),
    Scenario("uncorrected_pvalues", "Uncorrected p-values", _uncorrected, (
        Expectation("multiple_testing", FLAGGED, "Reported discoveries fail BH correction.", False),)),
    Scenario("wrong_count_model", "Gaussian test on donor pseudobulk counts", _wrong_count_model, (
        Expectation("count_model", FLAGGED, "A t-test is not a count model.", False),)),
    Scenario("merged_pseudobulk_arms", "Aggregation key merges contrast arms", _merged_arms, (
        Expectation("pseudobulk_integrity", FLAGGED, "Donor-only groups mix both conditions.", False),)),
)


def _finding_for(result, expectation: Expectation):
    matches = []
    for finding in result.findings:
        if finding.check_id != expectation.invariant:
            continue
        root = getattr(finding, "claim_root", None)
        if expectation.claim_path is None or (root and root.get("report_path") == expectation.claim_path):
            matches.append(finding)
    if not matches:
        return None
    if len(matches) != 1:
        raise AssertionError(
            f"expected one {expectation.invariant} finding for {expectation.claim_path}, got {len(matches)}")
    return matches[0]


def evaluate_battery(root: Path, emit: Callable[[str], None] | None = None) -> Scorecard:
    rows = []
    for scenario in SCENARIOS:
        folder = root / scenario.name
        scenario.build(folder)
        result = run_audit(folder, engine="simple")
        if emit:
            emit(f"[{scenario.name}] shipped run_audit(engine='simple')")
        for expectation in scenario.expectations:
            finding = _finding_for(result, expectation)
            if finding is None:
                actual, actual_status, verdict = NOT_APPLICABLE, NOT_APPLICABLE, "check did not apply"
            else:
                actual = S.human_state(finding)
                actual_status = finding.status
                verdict = " ".join(finding.verdict.split())
            row = ScoreRow(
                scenario=scenario.name, invariant=expectation.invariant,
                expected=expectation.expected, actual=actual, actual_status=actual_status,
                correct=_is_correct(expectation.expected, actual),
                correct_analysis=expectation.correct_analysis,
                rationale=expectation.rationale, verdict=verdict,
            )
            rows.append(row)
            if emit:
                emit(f"  {row.invariant}: expected={row.expected} actual={row.actual} "
                     f"status={row.actual_status} correct={row.correct}")
    return Scorecard(tuple(rows))


def render_scorecard(scorecard: Scorecard) -> str:
    total = len(scorecard.rows)
    lines = [
        "# sc-referee validation scorecard",
        "",
        "This is a measurement of the shipped `run_audit(folder, engine=\"simple\")` behavior. "
        "The benchmark does not execute `analysis.py` and does not modify engine behavior.",
        "",
        "## Summary",
        "",
        f"- **False alarms:** {scorecard.false_alarm_count} (correct analyses flagged; required: 0)",
        f"- **Catches:** {scorecard.catch_count} (known issue rows flagged)",
        f"- **Abstentions:** {scorecard.abstain_count} (`not_checked` rows)",
        f"- **Overall correctness:** {scorecard.correct_count}/{total} "
        f"({scorecard.correct_count / total:.1%})",
        "",
        "A `not_flagged` expectation accepts clear, not-applicable, or explicit abstention; it only "
        "fails when the engine attributes a concern to a scientifically valid analysis.",
        "",
        "## Verdicts",
        "",
        "| Scenario | Invariant | Expected | Actual state | Shipped status | Correct? |",
        "|---|---|---:|---:|---:|:---:|",
    ]
    for row in scorecard.rows:
        lines.append(f"| `{row.scenario}` | `{row.invariant}` | {row.expected} | {row.actual} | "
                     f"{row.actual_status} | {'yes' if row.correct else 'NO'} |")
    lines.extend(["", "## Findings", ""])
    if scorecard.false_alarms:
        lines.append("### False alarms")
        lines.append("")
        lines.extend(f"- {row.diagnostic}" for row in scorecard.false_alarms)
        lines.append("")
    else:
        lines.extend(["- No correct analysis was flagged: false-alarm count is zero.", ""])
    misses = [row for row in scorecard.rows if row.expected == FLAGGED and not row.caught]
    if misses:
        lines.append("### Surprising misses")
        lines.append("")
        lines.extend(f"- {row.diagnostic}" for row in misses)
        lines.append("")
    else:
        lines.extend(["- Every known issue in this battery was flagged.", ""])
    coverage_gaps = [row for row in scorecard.rows if row.actual == NOT_CHECKED]
    if coverage_gaps:
        lines.append("### Coverage gaps / intentional abstentions")
        lines.append("")
        for row in coverage_gaps:
            lines.append(f"- `{row.scenario}` / `{row.invariant}`: {row.verdict}")
        lines.append("")
    lines.extend([
        "## Scenario ground truth",
        "",
    ])
    for scenario in SCENARIOS:
        lines.append(f"- `{scenario.name}` — {scenario.title}.")
        for expectation in scenario.expectations:
            lines.append(f"  - `{expectation.invariant}` → **{expectation.expected}**: "
                         f"{expectation.rationale}")
    lines.extend([
        "",
        "## Reproduce",
        "",
        "```bash",
        ".venv/bin/pytest -q -s tests/benchmark",
        "```",
        "",
        "The pytest session creates each self-contained folder under its temporary directory and "
        "prints each relevant finding as soon as that scenario finishes.",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    import tempfile

    parser = argparse.ArgumentParser(description="Run the sc-referee synthetic validation battery")
    parser.add_argument("--write-scorecard", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="sc-referee-benchmark-") as tmp:
        card = evaluate_battery(Path(tmp), emit=print)
    rendered = render_scorecard(card)
    if args.write_scorecard:
        args.write_scorecard.write_text(rendered)
    else:
        print(rendered)
