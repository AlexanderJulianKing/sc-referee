# sc-referee

**An independent statistical review for single-cell analyses.**

sc-referee reviews single-cell analysis folders for specific statistical failure modes, including
pseudoreplication, omitted confounders, multiple-testing errors, and circular analysis. It reconstructs
the experimental design from the supplied data, results, and code; asks the scientist to confirm
ambiguous context; and then runs deterministic checks at the appropriate experimental unit. When the
available evidence cannot support a conclusion, the report says so.

> 🎬 **Watch the demo:** https://www.youtube.com/watch?v=1VGWTWFhlNI

---

## What it does

Point it at an analysis folder. sc-referee follows three steps:

1. **Reconstruct** — deterministic readers recognize common data, result, metadata, and code layouts. When
   they cannot confidently map an unfamiliar folder, an optional Claude step proposes the missing
   structure from the supplied files.
2. **Confirm** — you review and correct the reconstructed design and supply scientific context that
   cannot be recovered reliably from the folder.
3. **Verify** — applicable deterministic verifiers recompute the relevant quantities and report what is
   **clear**, **flagged**, **needs review**, or **not evaluated**.

The application and statistical checks run locally and leave your source files unchanged. The optional
Claude reconstruction step requires access to the Anthropic API.

## Two worked examples

**Pseudoreplication (published human data).** In a supplemental table from a published human melanoma
study, the authors reported **16,289** genes as significant using a cell-level analysis. When biological
*samples* — not individual cells — are treated as the independent units, **770** remain. **95.3%** of the
published discoveries lose significance under the sample-level analysis. sc-referee reports the
discrepancy while also noting that the corrected analysis had limited power: loss of significance does
not prove that the original findings were false.
→ [`data/biermann/`](data/biermann/)

**Latent ambient-RNA confounding (public benchmark).** In a public GeneBench-Pro case, sc-referee detects
that the fitted model omitted the ambient-RNA contamination variable the user confirmed was relevant. It
also marks allele orientation as *needs review* and donor/genotype support as *clear*. The report
establishes that the variable was omitted; it does not claim how that omission changed the estimated
effect. → [`demos/genebench-gbp07/`](demos/genebench-gbp07/)

## What it can catch

sc-referee ships with more than a dozen verifier classes. These are not keyword warnings. Depending on
the workflow, it can rebuild pseudobulk samples, refit models at the biological-replicate level, recompute
false-discovery-rate corrections, reconstruct the fitted design matrix, trace selection and testing
through analysis code, and compare reported statistics with independent calculations.

| Where an analysis can go wrong | What sc-referee independently checks |
|---|---|
| Cells are counted as replicates | Rebuilds sample-level pseudobulks, reruns the test, and reports how many of the original discoveries survive. |
| Treatment is entangled with batch | Uses design-matrix rank and column-space calculations to test whether the biological effect is identifiable and whether confirmed technical variables were actually adjusted for. |
| A latent contamination signal is omitted | Tests whether a user-confirmed ambient-RNA contamination variable is present in the fitted model. |
| Significance does not survive multiplicity correction | Recomputes Benjamini–Hochberg correction over the complete supplied family of raw p-values. |
| The statistical model does not match the data | Traces which code produced the result and checks whether raw counts were analyzed with a count model rather than an incompatible generic test. |
| Pairing or aggregation is broken | Checks whether donor pairing was preserved, comparison groups were merged during pseudobulk aggregation, or missing keys silently dropped cells. |
| Clusters are tested on the data that created them | Detects calibrated marker inference performed after selecting clusters from the same expression data without a selection-aware safeguard. |
| Statistical significance is mistaken for biological importance | Measures how much of a discovery list falls below a declared effect-size threshold and reports the result as an advisory. |
| An eQTL is oriented or supported incorrectly | Checks effect-allele direction, donor-level genotype support, and contamination adjustment under explicit eQTL contracts. |
| A Hi-C loop-strength claim does not match its estimator | Recomputes the reported observed/expected contrast under the confirmed resolution, masking, background, and replicate rules. |

Each verifier declares the evidence it requires and the strongest conclusion that evidence can support.
If the necessary data, code, or scientific context is missing, the report says *needs review* or *not
evaluated* instead of filling the gap with a guess.

## How to read the report

When a check lacks the evidence required for a conclusion, it returns *needs review* (relevant evidence
was found, but the conclusion remains unresolved) or *not evaluated* (required evidence was unavailable).
A finding marked *clear* means only that the specific check found no issue in the evidence it examined;
it is not validation of the entire analysis. Each finding records the evidence it used and the scope of
the conclusion it reached.

## Install

Requires Python >= 3.10.

```bash
# with uv (recommended)
uv venv && uv pip install -e '.[engine]'

# or with pip
pip install -e '.[engine]'
```

The `engine` extra (pydeseq2 + scanpy) enables the count-based reanalysis used by the pseudoreplication
checks. Optional extras: `llm` (adds `anthropic` for the Claude reconstruction step; also honors
`ANTHROPIC_API_KEY`), `dev` (test tooling).

## Run the local review interface

```bash
referee
```

This starts a temporary server on `127.0.0.1` and opens the review interface in your default browser.
Choose an analysis folder, review the reconstructed design, and run the audit. Two bundled analyses
reproduce the examples above:

- **`data/biermann`** — pseudoreplication and the 95.3% sample-level reduction.
- **`demos/genebench-gbp07`** — latent ambient-RNA confounding and two supporting checks.

Prefer the command line? `referee data/biermann` or `referee demos/genebench-gbp07` skips the folder
picker. `sc-referee --help` exposes the full CLI.

## Demos

| Demo | Folder | What it shows |
|---|---|---|
| Biermann pseudoreplication | [`data/biermann/`](data/biermann/) | 16,289 cell-level discoveries reduced to 770 under sample-level analysis (published GSE200218 aggregate) |
| GeneBench GB-P07 | [`demos/genebench-gbp07/`](demos/genebench-gbp07/) | An ambient-RNA contamination variable omitted from an eQTL fitted design (external benchmark; bytes not redistributed) |
| Multi-claim pipeline | [`demos/multi-claim-pipeline/`](demos/multi-claim-pipeline/) | One experiment, three result families routed to the right checks (synthetic) |

Every bundled demo carries an `ATTRIBUTION.md` with its data provenance and redistribution terms.

## How it's built

`src/sc_referee` implements the review pipeline: **ingest -> reconstruct and confirm the design -> select
checks -> recompute -> render**. Each verifier returns a typed `Finding` and declares the highest severity
its evidence can support. The compiler adapter (`src/sc_referee/compiler`) brings analyses without a
standard count matrix into the same review flow. See **[`docs/architecture.md`](docs/architecture.md)**
for the design and a walkthrough of adding a new check, and the technical explainers in
[`docs/explainers/`](docs/explainers/).

## License & citation

Apache-2.0 (see [`LICENSE`](LICENSE)). If you use sc-referee in your work, please cite it — see
[`CITATION.cff`](CITATION.cff).
