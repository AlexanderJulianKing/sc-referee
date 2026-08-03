# Capabilities and limits

`sc-referee` can inventory an arbitrary scientific repository. It cannot understand everything in
an arbitrary repository. Scientific checks activate only when exact evidence matches a bounded,
declared profile; otherwise the program records a question, abstention, or coverage limitation.

## Cross-cutting behavior

Available now:

- immutable repository snapshots and explicit identity grades;
- canonical JSON/JSONL evidence with a rebuildable SQLite index;
- exact source locations and multidimensional Claim lineage;
- bounded static inspection of Python, Markdown, R Markdown, R, Jupyter notebooks, and Quarto;
- bounded plain or gzip-compressed CSV/TSV headers, selected dense/CSR/CSC H5AD structure,
  checksum declarations, and default Nextflow trace import;
- typed scientist questions and linked answer segments;
- semantic lock, integrity verification, deterministic report generation, and model-free replay;
- attached RO-Crate export under the project's bounded profile; and
- a generated public capability matrix tied to immutable manifests.

Not available as production behavior:

- open-ended model searching for scientific mistakes;
- automatic execution of project-authored code, notebooks, or workflow engines;
- automatic dependency reconstruction;
- general Python or R dataflow and runtime semantics;
- authentication of repository assertions or saved notebook output;
- general interpretation of figures, prose, formulas, or undocumented scientific intent; or
- a global risk score, pass, correctness certificate, or publication-ready decision.

## Deterministic scientific modules

All current calculation modules are Disclosure-only. Their strongest real-project result is a
bounded deterministic observation or incompatibility, not a production Finding.

| Module | Supported initial profile | Important abstentions |
|---|---|---|
| Multiple testing | Explicit complete-family Benjamini-Hochberg table | Incomplete families, alternate procedures, and undeclared scopes |
| Single-cell sensitivity | Selected dense-integer H5AD plus declared replicate-level two-arm model | Sparse/layered matrices, unresolved units or producer semantics, unsupported models |
| Effect relevance | Declared adjusted-p and log2-fold-change table with an explicit relevance floor | Inferred thresholds, alternate effect scales, significance-only claims |
| Design integrity | Declared categorical main effects, adjustment set, pairing, and aggregation keys | Continuous terms, interactions, arbitrary formulas, inferred confounders |
| R response/method | Exact namespaced calls from a finite DESeq2, edgeR, limma, and stats registry | Wrappers, dynamic dispatch, general R dataflow, unresolved response scale |
| Scanpy reuse | One exact neighbors → Leiden → marker-test object/group shape | Aliases, wrappers, Seurat, unverified safeguards, runtime object identity |
| eQTL sign/support | Donor-level unadjusted OLS with explicit allele and dosage orientation | Adjusted, mixed, nonlinear, and count-likelihood models; inferred orientation |
| Hi-C loop strength | Fixed-resolution cis single-pixel arithmetic background with exact exclusions | Balanced contacts, model-based expected counts, domains, stripes, covariates |

Every row has two deterministic evidence-layout adapters: the original explicit declaration in the
selected report and an explicitly selected YAML sidecar. Both normalize into the same family
evaluator. The sidecar's filename is irrelevant, but its marker, check ID, contract keys, referenced
paths, and material-input selection must be exact. It makes the bounded modules portable across
repository layouts; it does not infer missing scientific intent or prove that the declaration is
true.

The compact practical-parity matrix records the exact relationship to the earlier public feature
families: [`implementation/PRACTICAL_PARITY_MATRIX.md`](implementation/PRACTICAL_PARITY_MATRIX.md).

## Experimental method checks

The repository also contains bounded question and comparison machinery for explicit scientific
method choices. It can retain exact report and source operands, ask the scientist which requirement
governs, and deterministically compare supported typed values after the scientist answers.

These comparisons remain experimental and review-scoped. They do not establish historical intent,
execution, numeric causality, universal method correctness, detector qualification, or Finding
permission.

## Finding status

The complete Finding admission machinery is implemented and mutation-tested. The current complete
Finding-producing detector path is nevertheless a synthetic fixture-only test double. Public
real-project detectors and calculation modules are experimental or Disclosure-only.

That distinction is intentional: working infrastructure is not sufficient evidence that a
scientific detector deserves accusation authority.

## Large and unavailable data

The auditor can preserve bounded identities for very large assets without loading an entire
dataset into memory or rerunning the workflow. Depending on the evidence, identity may be a full
digest, a repository-declared checksum, a bounded fingerprint, or unidentified.

A weaker identity is not a scientific defect. It limits which downstream claims can be made. A
repository-declared checksum is retained as a declaration unless the target bytes were independently
verified.

Selected material inputs have a separate finite budget: at most eight paths and 16 MiB total. The
current H5AD structural adapter accepts bounded dense, CSR, and CSC integer `X` layouts. It scans
decompressed arrays in chunks of at most 1 MiB under a separate 64 MiB logical-read ceiling and
records the measured reads in the immutable snapshot. It never densifies sparse matrices. Layers,
`raw`, floating matrices, files outside the exact material-copy budget, and biological meaning
remain unsupported.

Fully identified `.csv.gz` and `.tsv.gz` files receive a bounded first-logical-record header
inventory: at most 64 KiB per decompressed read and a 1 MiB header plus one sentinel byte. If an
existing calculation contract selects the table, the calculation layer separately validates the
complete gzip stream and admits at most 8 MiB of decoded content per input and 64 MiB of aggregate
logical reads. Its locked receipt preserves both the physical gzip digest and a separate decoded
content digest. The seven table-consuming calculation families accept this view; the R
response/method check has no table input. These format mechanics do not establish column meaning,
producer lineage, method suitability, or support for a larger table.

## How to read coverage

For every audit, ask:

1. Which report or publication surface did the user select?
2. Which material inputs were explicitly selected?
3. Which files received structural or semantic inspection?
4. Which module contracts were applicable?
5. Which premises remained unknown or unsupported?
6. Did integrity verify after semantic lock?

Only then interpret the assessment arrays. An empty Finding array without those denominators is not
meaningful evidence of correctness.

## Qualification still missing

Real answer-blind cross-provider review, held-out positive and negative controls, pilot-informed
thresholds, maintainer promotion, and public qualification reports remain required before any
experimental real-project detector can emit Findings. Local fixtures and development benchmarks do
not substitute for that evidence.
