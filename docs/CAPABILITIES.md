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

Current calculation modules emit bounded deterministic observations. Most are Disclosure-only;
the selected feature-identifier module may feed one experimental evaluation candidate after an
exact human Answer. None can emit a production Finding in this release.

This table inventories calculations; it is not an end-to-end detector matrix. The private
[maturity ledger](implementation/CAPABILITY_MATURITY_LEDGER.md) reports `inventoried`, `recognized`,
`structurally_verified`, `impact_tested`, `evaluation_candidate`, and `finding_qualified`
independently. No earlier dimension implies a later one, and no aggregate “full” status is assigned.

| Module | Supported initial profile | Important abstentions |
|---|---|---|
| Multiple-testing calculation | Explicit complete-family Benjamini-Hochberg table | Incomplete families, alternate procedures, and undeclared scopes |
| Single-cell sensitivity | Selected dense-integer H5AD plus declared replicate-level two-arm model | Sparse/layered matrices, unresolved units or producer semantics, unsupported models |
| Effect relevance | Declared adjusted-p and log2-fold-change table with an explicit relevance floor | Inferred thresholds, alternate effect scales, significance-only claims |
| Design integrity | Declared categorical main effects, adjustment set, pairing, and aggregation keys | Continuous terms, interactions, arbitrary formulas, inferred confounders |
| R response/method | Exact namespaced calls from a finite DESeq2, edgeR, limma, and stats registry | Wrappers, dynamic dispatch, general R dataflow, unresolved response scale |
| Scanpy reuse | One exact neighbors → Leiden → marker-test object/group shape | Aliases, wrappers, Seurat, unverified safeguards, runtime object identity |
| eQTL sign/support | Donor-level unadjusted OLS with explicit allele and dosage orientation | Adjusted, mixed, nonlinear, and count-likelihood models; inferred orientation |
| Hi-C loop strength | Fixed-resolution cis single-pixel arithmetic background with exact exclusions | Balanced contacts, model-based expected counts, domains, stripes, covariates |
| Selected feature identity | Exact set comparison between one selected CSV/TSV column and one selected H5AD `var/` string field | Mappings, normalization, duplicates, unsupported encodings, inferred equality requirements |

Every row has two deterministic evidence-layout adapters: the original explicit declaration in the
selected report and an explicitly selected YAML sidecar. Both normalize into the same family
evaluator. The sidecar's filename is irrelevant, but its marker, check ID, contract keys, referenced
paths, and material-input selection must be exact. It makes the bounded modules portable across
repository layouts; it does not infer missing scientific intent or prove that the declaration is
true.

The compact practical-parity matrix records the exact relationship to the earlier public feature
families: [`implementation/PRACTICAL_PARITY_MATRIX.md`](implementation/PRACTICAL_PARITY_MATRIX.md).

## Development-lane checks

The multiple-testing code-recognition check is at development lane `3.5.0`. It starts from a
human-confirmed ordered outcome family and two-group contrast column. It then looks for one
registered two-group test per declared outcome and classifies correction coverage as complete,
partial, or no correction. It can also retain a bounded correction-scope question and human
attestation when the correction site is structurally unresolved. This check runs only in the
development lane, cannot emit a Finding, and is not promoted. Its current authority boundary is
recorded in
[`ADR-0079`](implementation/ADR-0079-MULTIPLE-TESTING-CODE-SLICE-2.0-INVERSION.md) and
[`ADR-0080`](implementation/ADR-0080-MULTIPLE-TESTING-CORRECTION-SCOPE-QUESTIONS-AND-ATTESTATIONS.md).

### Known limitations of the multiple-testing lane

- Adversarial probes found residual analyzer-level accusation routes for a list stored through a
  dictionary key or `defaultdict`, a two-hop identity-return chain, a lambda default argument, and
  an unresolved object's project-local `append` method. These shapes are outside the sealed and
  corpus universe. None produced an accusation in any sealed E10-E18 negative; every such negative
  had zero candidates. See the custodian post-audit note in
  [`ADR-0079`](implementation/ADR-0079-MULTIPLE-TESTING-CODE-SLICE-2.0-INVERSION.md) and each
  envelope's `AUDIT_RESULTS.json` under `evaluation/development/blind-envelope-10-2026-08-24/`
  through `blind-envelope-18-2026-09-01/`.
- The library-correction path does not inspect the decision threshold. A complete-family clearance
  establishes only that every declared outcome used its own corrected result; agreement with a
  declared threshold is outside that claim. See
  [`ADR-0079`](implementation/ADR-0079-MULTIPLE-TESTING-CODE-SLICE-2.0-INVERSION.md).
- Two ranked recall deltas are specified but not installed: set-literal adjusted-p-value selectors
  and standard-library CSV-reader lineage. See the E18
  [recall reconciliation](implementation/MULTITEST-RECALL-RECON-E18-2026-09-02.md).
- A Bonferroni factor equal to the corrected subset size needs a policy decision about whether it
  can ever establish correction of the declared family. This is recall delta D in the
  [manual-correction reconciliation](implementation/MULTITEST-RECALL-RECON-MANUAL-CORRECTION-2026-09-03.md).
- The broader manual-correction family remains open, including split-then-cap and `None`-sentinel
  raw/corrected partitions. See the same
  [manual-correction reconciliation](implementation/MULTITEST-RECALL-RECON-MANUAL-CORRECTION-2026-09-03.md).
- Two rounds of adversarial review found routes that cleared a family whose verdicts were read off
  the raw p-value while the corrected values went unread. Both are closed in `3.5.0`. Both are still
  present in the byte-frozen `3.1` to `3.4` lanes, which `3.5.0` supersedes in the active development
  binding. See the round 1 and round 2 audit-fix records in
  [`ADR-0079`](implementation/ADR-0079-MULTIPLE-TESTING-CODE-SLICE-2.0-INVERSION.md).
- Two contrived shapes still clear at the analyzer level in `3.5.0` and in the frozen `3.4` lane: a
  constant index rebound before hand-unrolled prints (through a one-element `for`, an augmented
  assignment, a `match` capture, or a walrus), and the results collection reordered through a
  `match` capture or a `for` target before position-indexed prints. Negative indexing of the
  correction vector abstains where the positive spelling clears. No sealed case contains these
  shapes. They are recorded in
  [`ADR-0079`](implementation/ADR-0079-MULTIPLE-TESTING-CODE-SLICE-2.0-INVERSION.md).
- Pinned read-only forms deliberately abstain. The round oracles include read-only helpers over
  mapping `keys`, `items`, `values`, and `copy`; wrappers such as `OrderedDict`, `deque`, and
  `tabulate`; scalar-projection helpers; an `operator.itemgetter` sort key; tracing decorators;
  unawaited async work; cached read-only helpers; and read-only pandas `apply`. See the audit-fix
  round records collected in
  [`ADR-0079`](implementation/ADR-0079-MULTIPLE-TESTING-CODE-SLICE-2.0-INVERSION.md).

## Experimental method checks

The repository also contains bounded question and comparison machinery for explicit scientific
method and data-identity choices. It can retain exact operands, ask the scientist which requirement
governs, and deterministically compare supported typed values after the scientist answers.

These comparisons remain experimental and review-scoped. They do not establish historical intent,
execution, numeric causality, universal method correctness, detector qualification, or Finding
permission.

## Finding status

The complete Finding admission machinery is implemented and mutation-tested. Exactly two bounded
real-project bindings are qualified and product-wired: the complete-domain exposure-denominator
check and the authorized-unit dependence/pseudoreplication check. Their accepted promotions are
recorded in [`ADR-0071`](implementation/ADR-0071-COMPLETE-DOMAIN-ENVELOPE-PROMOTION.md) and
[`ADR-0073`](implementation/ADR-0073-DEPENDENCE-ENVELOPE-PROMOTION.md). Broader siblings remain
unqualified.

The selected feature-identifier path can satisfy every non-maturity gate and produce a replayable
evaluation candidate, but production admission rejects it until independent qualification and an
accepted promotion record exist. The multiple-testing development lane is likewise unqualified
and Finding-ineligible.

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
