# sc-referee

**The bioinformatics reviewer you can leave behind.**

sc-referee is an extensible, deterministic review engine for computational biology. Point it at an
analysis folder—data, metadata, results, and ideally code. Referee reconstructs the scientific
claim, asks a scientist to confirm the load-bearing design facts, and independently checks the
analysis using deterministic statistics.

Its adapters handle standard single-cell files and multi-sample layouts. Its modular checks encode
recurring review decisions such as pseudoreplication, confounding, pairing, multiple testing, count
models, and circular inference. Every report distinguishes what was verified, what was flagged,
and what lacked enough evidence to audit.

> **Claude proposes. A scientist ratifies. Arithmetic decides.**

```bash
# From the cloned repository root (requires uv: https://docs.astral.sh/uv/)
uv venv --python 3.11
uv pip install --python .venv/bin/python ".[engine,llm]"
.venv/bin/referee                 # open the desktop folder picker
# .venv/bin/referee ./analysis    # or review a specific folder directly
```

## A published analysis, reviewed from the real data

The authors of the [Biermann et al. melanoma study](https://doi.org/10.1016/j.cell.2022.06.007)
compared tumor cells from brain and peripheral metastases with a cell-level MAST analysis. Referee
reconstructed that comparison from the official [GSE200218 public count
matrix](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE200218) and repeated the inference with
patients as the independent units.

**16,289 reported discoveries became 770 patient-level survivors.** In other words, **95.3% lost
significance after correcting the experimental unit**.

Referee also refused to overstate the finding. The patient-level recomputation was underpowered
(`powered_fraction = 0.3817`), so it presented the collapse as a critical discrepancy while
withholding a hard blocker. It did not claim that 95.3% of the biology was false.

Two versions are provided:

- [`demos/biermann-pseudoreplication/`](demos/biermann-pseudoreplication/) is a 5 MB, immediately
  runnable capsule containing the published result family and its exact patient-level aggregate.
- [`demos/biermann-pseudoreplication-full/`](demos/biermann-pseudoreplication-full/) downloads the
  official 145,555-cell matrix, reconstructs the 82,783 tumor nuclei, verifies count-for-count
  equality with the compact capsule, and runs Referee on the sparse full-cell matrix.

```bash
.venv/bin/referee demos/biermann-pseudoreplication
```

## How it works

```text
analysis folder
      │
      ▼
1. ADAPT      H5AD, count tables, metadata, code, and declared sample shards
      │
      ▼
2. DESCRIBE   Claude proposes roles; deterministic signals win; a scientist confirms
      │
      ▼
3. AUDIT      claim-specific checks recompute, prove, or measure the consequence
      │
      ▼
4. REPORT     clear · flagged · not checked · not applicable
```

### 1. Adapt varied analysis layouts

Adapters convert supported artifacts into one canonical evidence model: observations, feature
identities, raw counts or declared measurements, reported claims, code signals, and provenance.
Scientific checks operate on that model rather than on a particular filename convention.

### 2. Confirm scientific intent

Some facts cannot be recovered safely from bytes alone: which column is the biological replicate,
which group is the reference, or whether a measured technical axis is genuinely a nuisance.
Deterministic signals resolve unambiguous cases. Claude may propose only structured roles when they
are ambiguous. A scientist confirms the load-bearing facts; Claude cannot author the formula or the
verdict.

### 3. Run deterministic checks

Each check declares the analysis types and evidence it requires. Some checks recompute the result,
some prove a design-matrix fact, and some measure a discrepancy that must be interpreted under an
explicit power or evidence gate. The LLM is not part of this stage.

### 4. Report coverage, not just warnings

Referee never mistakes missing evidence for a clean analysis:

- **Clear** — the audited decision passed.
- **Flagged** — the evidence earned an adverse finding.
- **Not checked** — the decision was relevant, but a required artifact, premise, binding, or power
  condition was missing.
- **N/A** — the check genuinely did not apply to that claim.

If the folder itself is dangerously ambiguous—for example, two candidate matrices with no declared
assembly—Referee stops safely with exit code `2` rather than auditing whichever file sorts first.

## What it accepts

| Analysis layout | Current behavior |
|---|---|
| One raw-count H5AD, dense or sparse | Supported; full recomputation is available when design evidence is present |
| Cell-by-gene CSV/TSV plus cell metadata | Supported |
| One declared H5AD or count-table shard per biological sample | Supported through a confirmed, integrity-bound manifest |
| Normalized values without raw counts | Structural and report-level checks still run; raw-count recomputations are marked **not checked** |
| Multiple plausible matrices or result tables | Refuses or leaves the claim unbound until the intended artifact is declared |
| Specialized Hi-C contact folders | Supported for the loop-strength claim contract |
| Generic 10x MTX directory | Not yet a first-class input path; convert to H5AD or a supported table layout |
| Arbitrary chunks of one sample across many files | Not yet a supported assembly contract |
| One file per cell | Not a supported or practical layout |

The strongest current target is a standard single-cell analysis folder containing an H5AD or count
table, observation metadata, a results table, and analysis code. AI-produced workflows often use
these conventions, but Referee does not assume that an AI-generated folder is complete or
unambiguous.

## What it audits today

Coverage is organized by **scientific decision**, not merely by file type.

| Decision family | Current reach |
|---|---|
| Condition-contrast differential expression | Flagship path: experimental unit, confounding, pairing, count model, multiple testing, effect-size context, and pseudobulk integrity |
| Marker detection | Circular cluster-then-test provenance and relevant cross-cutting checks |
| Differential abundance | Confounding, pairing, multiple testing, and enrichment-universe coverage; no general compositional-inference engine yet |
| eQTL | Effect-allele orientation and supported sign-conformance contracts |
| Hi-C | Specialized loop-strength claim recomputation |
| Contamination/confounding | Contract-driven measurement and fitted-design geometry; the live GB-P07 demo remains gated until its complete evidence chain is independently cleared |
| Trajectory and spatial claims | Narrow circularity or independence policies, not complete validation of the biological analysis |

No warning means only that the decisions listed as audited passed. It does not mean every decision
in the project was examined. The detailed boundary is maintained in
[`docs/coverage-boundary.md`](docs/coverage-boundary.md).

## Built to accumulate scientific expertise

The durable artifact is not this week's check count. It is the machinery for turning another
hard-earned review lesson into executable policy.

Referee separates two extension points:

- **Adapters** teach it how to assemble another artifact or storage layout into the canonical
  evidence model.
- **Checks** teach it how to audit another scientific decision and what evidence must be present
  before a verdict is allowed.

A new check reuses the existing confirmation gates, status semantics, report renderers, citations,
CI behavior, and adversarial-test conventions. Contributors do not have to build a new application
for every analysis type.

Today this is a stable internal extension seam, not yet a drop-in third-party plugin SDK. A public
SDK would additionally require versioned manifests, entry-point discovery, compatibility checks,
isolation, and a conformance suite.

## Why not just ask Claude?

- **Referee recomputes; an LLM critiques.** It returns the corrected number and the measured
  discrepancy, not merely a warning that something might be wrong.
- **It is independent of the system that produced the analysis.** Asking the authoring model to
  grade its own work shares its blind spots.
- **It is deterministic and persistent.** The same evidence produces the same verdict in a local
  report or CI run.
- **It applies the checklist without relying on the analyst to know what to ask.**
- **Its uncertainty is typed.** Missing evidence becomes a specific coverage gap, not reassuring
  prose.

## Evidence portfolio

Each example has a different job. They should not be presented as interchangeable proof.

| Case | Role | What it establishes |
|---|---|---|
| **Biermann melanoma** | Published-analysis audit | Referee can expose a publication-threatening experimental-unit discrepancy in a real published analysis while preserving the power qualification |
| **Kang paired IFN-β** | Real-data calibration | A deliberately naive analysis on public human data is corrected without erasing a strong genuine response; this is not an error attributed to Kang et al. |
| **GeneBench-Pro GB-P07** | Collaborative adversarial case | Claude, scientist-ratified premises, and deterministic geometry can expose a subtle contamination/confounding failure; the live case remains gated until fully integrated |
| **Synthetic fixtures** | Known-truth validation | Individual checks are tested against clean controls, planted failures, abstention cases, and adversarial mutations |

See [`demos/`](demos/) for the runnable/gated gallery and
[`docs/planning/2026-07-12-final-hackathon-strategy.md`](docs/planning/2026-07-12-final-hackathon-strategy.md)
for the claim discipline behind it.

## Validation against planted truth

The headline benchmark uses a multi-sample negative-binomial simulator mirroring **muscat**'s
`simData` design. The simulator plants a known set of sample-level DE genes. From every dataset the
harness emits a pseudoreplicated per-cell analysis and an independently estimated replicate-aware
analysis, then scores Referee against the planted truth.

**120 deterministic datasets**: 20 seeds × donor counts `{3, 4, 5, 6, 8, 12}`.

| Measurement | Result |
|---|---:|
| Pseudoreplicated analyses never green-lit | **120 / 120** |
| Correct analyses never falsely accused | **120 / 120** |
| Strong `blocker` earned | **83.3%** overall; **100% at n ≥ 4** |
| Honest `needs_evidence` abstention | **16.7%**, all at `n = 3` |
| Precision against planted genes | per-cell **0.068** → pseudobulk **0.883** |
| Pseudobulk recall | **0.734** |

The correct arm is not Referee's own output recycled as an answer key. It is an independent
pseudobulk → log2CPM → Welch *t* → BH estimator, and the harness fails if its agreement becomes
degenerate. Committed metrics live in [`bench/metrics.json`](bench/metrics.json), with regression
floors in [`bench/expected_metrics.json`](bench/expected_metrics.json).

```bash
PYTHONPATH=src:. python bench/run_benchmark.py --seeds 20 --out bench/metrics.json
```

These numbers validate the experimental-unit pathway under known truth. They are not evidence that
every registered decision family has the same measured sensitivity.

## Adversarial testing

The red-team corpus attacks the boundaries that commonly make scientific automation unsafe:

- duplicate or transposed matrices, malformed counts, missing and extra cells;
- normalized data presented as counts and ambiguous internal H5AD layers;
- missing, duplicated, reordered, or undeclared sample shards;
- decoy matrices and competing reported-result tables;
- post-confirmation file mutation, stale digests, and path escapes;
- ambiguous statistical producers, aliased imports, monkey-patching, and multiple writers;
- paired/unpaired confusion, confounded designs, low power, and clean look-alike controls;
- contamination-specific proposal injection, row permutation, crafted names, nonfinite axes,
  random-intercept/weight/offset substitutions, and mutation after ratification.

The purpose of this corpus is to establish safe behavior over the supported contracts: either the
correct finding, a visibly conditional result, or a value-free abstention. It is not yet a measured
recognition-rate benchmark over a representative sample of naturally occurring lab folders.

Implementation notes and gate history are recorded in
[`tests/PIPELINE_BUILD_NOTES.md`](tests/PIPELINE_BUILD_NOTES.md); the complete routing and refusal
logic is mapped in [`docs/decision-tree.md`](docs/decision-tree.md).

## Use it

### Desktop flow

```bash
.venv/bin/referee                 # choose a folder in the native picker
.venv/bin/referee ./analysis      # or skip the picker
```

Choose an analysis folder, review the proposed design, and let the browser report open when the
audit finishes.

### Explicit CLI flow

```bash
.venv/bin/sc-referee init    ./analysis
.venv/bin/sc-referee confirm ./analysis/sc-referee.yaml
.venv/bin/sc-referee audit   ./analysis \
  --html ./analysis/sc-referee-report.html \
  --json ./analysis/sc-referee-report.json
```

For Claude-assisted proposals, put `ANTHROPIC_API_KEY=...` in a gitignored `.env` in the directory
where Referee is launched, or export it in the shell. Exported values take precedence.

Exit codes:

- `0` — no blocker was earned;
- `1` — a blocker was earned;
- `2` — the analysis could not be evaluated safely because its input or configuration was invalid.

### Continuous review

The reusable GitHub Action can audit the analysis on every pull request, attach the report, and fail
only when a blocker is earned:

```yaml
jobs:
  referee:
    uses: ./.github/workflows/sc-referee.yml
    with:
      folder: analysis
```

Repository contributors can use `./scripts/dev-install.sh` for a local development installation.

## Project status

Early open-source build created for **Built with Claude: Life Sciences**, Builder Track. The
flagship condition-DE pathway is runnable and backed by synthetic known-truth validation plus real
public-data anchors. Several additional decision families are narrower or contract-driven, as
documented above.

The long-term goal is a growing, open-source library of executable peer-review decisions: a lab's
hard-earned methods knowledge, applied consistently to every future analysis after its original
author has moved on.

## References

- Biermann J, Melms JC, Amin AD, et al. **Dissecting the treatment-naïve ecosystem of human
  melanoma brain metastasis.** *Cell*. 2022;185(14):2591–2608.e30.
  [DOI](https://doi.org/10.1016/j.cell.2022.06.007) ·
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/35803246/) ·
  [open-access full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC9677434/)
- **GSE200218: Melanoma Brain Metastasis Atlas, sc/snRNA-seq.**
  [NCBI GEO record and processed files](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE200218)
- Izar Lab. **Melanoma Brain Metastasis analysis code.**
  [GitHub repository](https://github.com/IzarLab/Melanoma_Brain_Metastasis)

## License

Apache-2.0. See [LICENSE](LICENSE).
