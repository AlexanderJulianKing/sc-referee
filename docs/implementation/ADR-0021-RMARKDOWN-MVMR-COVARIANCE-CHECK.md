# ADR-0021: Selected R Markdown reports and an external-first MVMR covariance check

- **Status:** Accepted, revision 3
- **Date:** 2026-07-29
- **Revised:** 2026-07-29 to make reusable adapter connectivity the governing architecture and
  record the completed external validation
- **Accepted:** 2026-07-29 by repository owner
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None proposed
- **Related decisions:** Accepted ADR-0019 and ADR-0020
- **Evidence basis:** Experiment 0021 and the public representations listed below

## Plain-language summary

Experiment 0021 showed that the new scientific-check framework is cautious on real repositories:
it did not invent a question or Finding in six independent projects. It also showed that the
current checks are not yet useful outside the controlled examples because they recognize only very
specific Markdown sentences.

The next check should start from a method choice that actually appears in independent scientific
work. Public MVMR analyses repeatedly call `strength_mvmr()` or `pleiotropy_mvmr()` with
`gencov = 0`. Whether zero covariance is appropriate depends on a factual premise the repository
often does not contain: whether the GWAS samples used for the different exposures overlap.

This ADR establishes a reusable connectivity path and proves it with one narrow, non-executing R
Markdown case. A format connector inventories the selected `.Rmd` report without scientific
interpretation. A separate method adapter converts one exact package-call shape into the same
normalized observation contract already used by other scientific checks. The shared scope join
binds that observation to the selected analysis, and the existing method-level reducer asks which
sample-overlap condition governs. The scientist supplies the premise; deterministic code performs
the comparison. The model does neither.

## Context

Experiment 0021 tested six independently authored QTL and robust-MR repositories. All six audits
and replays retained zero Findings and zero MaterialQuestions. Five MVMR-check outcomes were
`not_applicable`; the closest robust-MR lexical hard negative was correctly `unsupported`. This
passes a false-applicability screen.

No installed adapter produced an applicable observation on an independent repository. The current
selected-report adapters recognize exact phrases found in controlled development reports, and the
only source adapter recognizes one narrow Python shape without a typed source-to-selected-analysis
join. It would be misleading to call safe abstention useful method portability.

A bounded public-code search identified a naturally recurring representation:

- [MRCIEU/TwoSampleMR `vignettes/perform_mr.Rmd`](https://github.com/MRCIEU/TwoSampleMR/blob/951e5bae10d843741f7c383efb851dfb2ee58fbb/vignettes/perform_mr.Rmd)
  uses `gencov = 0` for the MVMR strength and pleiotropy diagnostics;
- [AndrewsLabUCSF/MR-tutorial `scripts/MVMR.Rmd`](https://github.com/AndrewsLabUCSF/MR-tutorial/blob/08aceff045426fb9d99f48bb555c6f492b0a680f/scripts/MVMR.Rmd)
  independently uses the same named method operand;
- [VilteBaltra/loneliness-mediation `reverse-MR.Rmd`](https://github.com/VilteBaltra/loneliness-mediation/blob/0ed39de1302447f6798cfc3890f9def4d53419ed/reverse-MR.Rmd)
  explicitly comments that covariance is being fixed at zero; and
- [WSpiller/MVMR `vignettes/MVMR.rmd`](https://github.com/WSpiller/MVMR/blob/bceaa38088d093a5d30c713afb016e7fbc7ed2be/vignettes/MVMR.rmd)
  demonstrates both zero covariance and covariance supplied through `Xcovmat`.

The MVMR package's independently authored
[`estimating-phenotypic-correlations.rmd`](https://github.com/WSpiller/MVMR/blob/bceaa38088d093a5d30c713afb016e7fbc7ed2be/vignettes/estimating-phenotypic-correlations.rmd)
states the bounded method rule: cross-exposure effect-estimate covariance is zero when the exposure
GWAS samples do not overlap; with any overlap, the diagnostics and robust estimation require an
estimate of that covariance. The corresponding primary method paper is Sanderson et al.,
*Statistics in Medicine* 2021, DOI
[`10.1002/sim.9133`](https://doi.org/10.1002/sim.9133).

A current ordinary audit can resolve an explicitly selected `.Rmd` publication surface but emits
no parser record for it. All installed report adapters therefore return `unsupported`. The
preflight audit is `audit:3818a4ab65ab4734b6a5beaace6c399d`.

## Recommended decision

### 0. Make adapter connectivity reusable

Keep three responsibilities separate:

1. **Format connectors** convert bounded immutable files into parser-owned, source-spanned
   structural inventories without scientific meaning.
2. **Method adapters** consume one or more declared connector outputs and translate exact supported
   structures into the existing `NormalizedMethodObservation` contract.
3. **Scope connectors** use typed record identity to prove that the observed target belongs to the
   scientist-selected analysis surface.

The scientific-check reducer remains independent of file format, language, repository path, and
package layout. A future notebook, R-source, or other format connector may feed the same method
adapter only after its own accepted scope and validation. Parser code must not contain MVMR rules,
and the MVMR adapter must not invent its own R Markdown parser or controller branch.

Every connection is declared in the adapter manifest by parser identity, evidence plane, semantic
roles, exact scope-join profile, and known gaps. The registry continues to arbitrate normalized
observations without knowing which connector produced them.

### 1. Add a bounded R Markdown source inventory

Add `parser:rmarkdown-selected-report-inventory` for bounded `.Rmd` or `.rmd` source files captured
by the ordinary repository inventory. The format connector may inventory multiple bounded files;
only the exact explicitly selected publication source may feed this method adapter or create its
public question.

The parser must:

- require a fully captured, strict UTF-8 file under the ordinary report-size budget;
- inventory YAML front matter, prose spans, and fenced R code-chunk spans;
- preserve exact repository-relative path, byte digest, line spans, chunk label, and literal chunk
  options;
- treat code as static text and never invoke R, knitr, Quarto, Pandoc, a package, or project code;
- localize malformed fences, invalid UTF-8, unsupported inline execution forms, and over-budget
  files without failing the audit; and
- make no general R-syntax, rendered-document, package-behavior, or execution claim.

This is not general R parsing. It is a bounded document-and-chunk inventory for the selected report
source. Other `.R`, `.Rmd`, Quarto, notebook, or generated output semantics remain unsupported.

### 2. Add one package-call adapter behind the ADR-0020 interface

Add `adapter:mvmr-cross-exposure-covariance:selected-rmarkdown-v1` and method-level check
`check:mvmr-cross-exposure-covariance`.

Applicability requires all of the following:

1. exactly one resolved, explicitly selected R Markdown publication source;
2. an immutable parser record for that same selected artifact;
3. one or more active R chunks containing supported calls to `strength_mvmr()` or
   `pleiotropy_mvmr()`, optionally namespace-qualified as `MVMR::`, with every admitted call
   resolving to the same operand;
4. an explicit named `gencov` argument; and
5. completed checks for comments, disabled chunks, multiple targets, contradictory operands, and
   unsupported dynamic expressions.

The v1 adapter recognizes only:

- literal numeric zero as `zero_cross_exposure_covariance`; and
- one local covariance object produced in the selected report by a closed
  `phenocov_mvmr(...)` or `snpcov_mvmr(...)` assignment and passed unchanged as `gencov`, normalized
  as `provided_cross_exposure_covariance`.

Aliases, sourced helpers, computed call targets, reassignment, loops, branches, dynamic chunk
generation, partial matching, positional inference, and general R dataflow are `unsupported`.
Commented calls and chunks explicitly marked `eval=FALSE` cannot establish an observed operand.
More than one active diagnostic target with conflicting operands is `ambiguous`.

The observation is a static statement about the selected report source. It does not establish that
the chunk ran, that the rendered report includes its output, that the inputs have the described
sample relationship, or that the analysis is scientifically correct.

### 3. Ask for the factual governing condition, not a model judgment

When the adapter yields one supported operand, the check may create this closed question:

> Which exposure-sample condition governs the covariance used by these MVMR diagnostics?

The finite candidates are:

- `nonoverlapping_exposure_gwas_samples_permit_zero_covariance`; and
- `overlapping_exposure_gwas_samples_require_estimated_covariance`.

The ordinary explicit unknown option remains available. The question must explain that the
scientist should choose from actual study/sample provenance, not from the code's apparent intent.
A model proposal may normalize an explicit literal repository statement about overlap, but it
cannot select the governing candidate, infer overlap from dataset names, or establish the premise
by confidence.

The accepted Answer is scoped only to the selected publication surface and the
`measurement_model` dimension. It does not become a global rule for the repository or other MVMR
analyses.

### 4. Keep the deterministic comparison narrow

After the scientist Answer:

- zero observed plus non-overlapping requirement is an exact covered result;
- provided covariance plus overlapping requirement is an exact covered result;
- zero observed plus overlapping requirement is an exact review-scoped incompatibility candidate;
- provided covariance plus a scientist-selected zero-covariance requirement is an exact
  review-scoped incompatibility candidate; this states only that the recorded operands differ and
  does not claim numerical harm; and
- unknown, unsupported, ambiguous, or incomplete evidence produces no compatibility conclusion.

The module remains `question_only`. It cannot emit a Finding, DetectorResult, metric contribution,
scientific-correctness claim, numeric-causality claim, or accusation about a public repository.

### 5. Require independent external validation before any capability wording

Before implementation is described as supporting this representation, it must pass:

- at least two of the pinned independent applied R Markdown repositories above as applicable
  zero-covariance observations without using repository identity;
- the unchanged WSpiller package vignette as an expected mixed-operand ambiguity, plus a
  controlled mutation that isolates its provided-covariance branch;
- generic `robust`, `MVMR`, `covariance`, and `gencov` lexical hard negatives;
- commented, disabled, missing-argument, multiple-target, contradictory, dynamic, renamed-local,
  path, formatting, chunk-label, and namespace-qualification metamorphic cases;
- sibling-module byte stability and packaged manifest identity;
- an ordinary fresh-context skill run that reaches the exact question and stops without answering
  it; and
- semantic lock and replay with no model or project execution.

Because the independent public repositories do not establish their own sample-overlap premise, they
can validate applicability and question transport but cannot be graded as covered-good or
incompatible without an Answer from an authorized scientist for that analysis.

## Implementation and validation result

[Experiment 0022](EXPERIMENT-0022-EXTERNAL-RMARKDOWN-ADAPTER-CONNECTIVITY.md) completes this
decision. The implementation adds the bounded R Markdown connector, the selected-surface method
adapter, the shared scope join, the question-only check, release manifests, and regression tests.
It also fixes a connector-ordering defect found during external validation: the explicitly selected
report is now prioritized within the unchanged whole-repository full-digest byte budget, so a
valid selected source cannot be crowded out by earlier files. An over-budget selected source still
fails closed.

Two independent applied repositories produce applicable zero-covariance observations and exactly
one open scientist question. A display-only TwoSampleMR code block remains `not_applicable`; the
unchanged WSpiller vignette remains `ambiguous` because it intentionally demonstrates both zero and
provided covariance; an evaluator-owned mutation that comments only the zero calls exposes the
provided-covariance branch. A fresh-context skill run reaches the same exact question and stops
without answering it. All audits retain zero Findings, zero project execution, zero model calls,
and deterministic replay.

## Schema and architecture impact

No schema release is proposed. Existing v0.14.0 FileRecord, Artifact, ParserResult,
PublicationSurface, ScientificContract, SemanticAssertion, MaterialQuestion, Answer, Disclosure,
semantic-lock, and replay records are sufficient if the selected R Markdown source artifact is the
same artifact referenced by the parser and check observation.

If implementation cannot express that same-artifact scope join without changing one of those
record meanings, it must stop and propose a forward-only schema ADR. It must not reuse the earlier
unscoped static-source exception.

This ADR deliberately pulls forward only selected R Markdown report inventory and one closed
package-call grammar. General R parsing, Quarto, notebook execution, knitr rendering, package
semantics, and arbitrary R source analysis remain outside scope.

## Test, acceptance criterion, and remaining limitation

- **Test proposed:** parser localization and no-execution tests; the closed MVMR call grammar;
  independent applicable public R Markdown cases; provided-covariance, ambiguity, mutation, and
  hard-negative controls; module isolation; fresh-context question transport; lock; and replay.
- **Acceptance criterion:** sc-referee recognizes one naturally occurring method representation
  across independent authors, asks only for the missing sample-provenance premise, and
  deterministically compares the supplied premise with the exact static method operand.
- **Remaining limitation:** this supports two enumerated operands in selected R Markdown files for
  two named MVMR diagnostic functions. It does not recognize arbitrary MVMR workflows, establish
  execution, decide sample overlap, qualify a detector, or generalize to R source code.

## Consequences

Positive:

- the first external applicable check begins from real independent scientific workflows rather
  than benchmark prose;
- the scientist answers a concrete provenance question instead of approving a model's method
  judgment;
- the comparison remains deterministic and replayable; and
- R Markdown becomes useful without adding R execution or a general R analyzer.

Costs:

- one additional static document inventory and one narrow call grammar must be maintained;
- `.Rmd` support must be described precisely so users do not mistake chunk inventory for rendered
  report or execution evidence; and
- covered-good scientific validation still requires an authorized scientist who knows the sample
  overlap for the reviewed analysis.

## Alternatives

### Broaden the existing MVMR Markdown phrases

Rejected. The independent repositories express the method through R Markdown calls, not the
controlled phrases. Looser keyword matching would increase false questions without establishing an
operand.

### Add a general R parser now

Rejected for this milestone. The evidence supports one closed selected-report representation, not
arbitrary R syntax, dataflow, package dispatch, or scientific semantics.

### Infer sample overlap from data-source names or model confidence

Rejected. Sample provenance is a material scientific premise. It must remain unknown or come from
an authorized scientist or independently checkable explicit evidence.

### Treat `gencov = 0` as a Finding

Rejected. Zero covariance is appropriate under a documented non-overlap condition, and the static
call does not prove execution or the sample relationship.
