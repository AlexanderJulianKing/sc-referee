# Experiment 0022: External R Markdown adapter connectivity

- **Status:** Completed; bounded connectivity milestone passes
- **Date:** 2026-07-29
- **Governing decision:** Accepted ADR-0021, revision 3
- **Public schema change:** None; accepted schema v0.14.0 remains unchanged
- **Production detector or Finding authority:** None

## Purpose

Test whether the ADR-0021 connector architecture can carry one naturally occurring scientific
method representation from an independently authored R Markdown source into the ordinary
sc-referee scientist-question lifecycle. This is a connectivity and false-applicability test, not
a correctness judgment about any public repository.

The required path is:

1. a format connector inventories immutable R Markdown structure without scientific meaning or
   execution;
2. the MVMR method adapter recognizes only its closed named-call and operand grammar;
3. a typed same-Artifact scope join binds the observation to the selected publication surface;
4. the shared reducer asks the scientist for the missing sample-overlap premise; and
5. the audit locks and replays without a model or project execution.

## Frozen public inputs

The exact commit archives were downloaded and extracted only into a temporary validation
workspace. They are not vendored into this repository.

| Repository | Exact commit | Archive SHA-256 | Selected surface |
|---|---|---|---|
| [MRCIEU/TwoSampleMR](https://github.com/MRCIEU/TwoSampleMR/tree/951e5bae10d843741f7c383efb851dfb2ee58fbb) | `951e5bae10d843741f7c383efb851dfb2ee58fbb` | `e0e8ce1332b1ab098bcabaa740a71410d460c0947932b0cd58ca771c05ac1a00` | `vignettes/perform_mr.Rmd` |
| [AndrewsLabUCSF/MR-tutorial](https://github.com/AndrewsLabUCSF/MR-tutorial/tree/08aceff045426fb9d99f48bb555c6f492b0a680f) | `08aceff045426fb9d99f48bb555c6f492b0a680f` | `4d06d1ee81e4194dbd1166381d268efae3870e17ecb1cadc5e68a03aac6ba090` | `scripts/MVMR.Rmd` |
| [VilteBaltra/loneliness-mediation](https://github.com/VilteBaltra/loneliness-mediation/tree/0ed39de1302447f6798cfc3890f9def4d53419ed) | `0ed39de1302447f6798cfc3890f9def4d53419ed` | `f94a209edd5f37f12852d23bf89467da6433ff25224135e5af865af40bb19bad` | `reverse-MR.Rmd` |
| [WSpiller/MVMR](https://github.com/WSpiller/MVMR/tree/bceaa38088d093a5d30c713afb016e7fbc7ed2be) | `bceaa38088d093a5d30c713afb016e7fbc7ed2be` | `e1b8c506a5c4986c866db161bcbbe9efaa5d52b1890f8edfcd58a41df3b46482` | `vignettes/MVMR.rmd` |

No public repository supplied an authorized Answer about its actual exposure-sample overlap. The
runs therefore validate question transport and abstention only; they do not classify any analysis
as scientifically compatible or incompatible.

## Connectivity failure found and repaired

The first MR-tutorial audit failed before adapter inspection even though the explicitly selected
file existed. The whole-repository full-digest budget was consumed by earlier analysis files, so
`scripts/MVMR.Rmd` received no complete immutable identity and could not become a publication
surface.

The snapshot API now accepts safe repository-relative `preferred_full_digest_paths`, and the audit
controller places the explicitly selected report first within the unchanged byte budget. This is
priority, not an unbounded read: an over-budget selected file still fails closed. The snapshot
records the preferred paths in `x-preferred-full-digest-paths`. A regression test proves that a
selected R Markdown surface is materialized and fully identified while a competing file becomes
unidentified under an intentionally tiny budget.

## External results

| Case | Audit ID | Semantic-lock digest | MVMR module | Questions | Findings |
|---|---|---|---|---:|---:|
| TwoSampleMR display-only code block | `audit:ef715d9f89c64427815676352ca2d408` | `sha256:2a788a474ee04b8b89f1c94cd849323a7bda688f3e38a06df03b914d2b7af328` | `not_applicable` | 0 | 0 |
| MR-tutorial active chunks | `audit:fc33b3c5371b48a3a26f707ad3b7feef` | `sha256:539ba83f98f0dba74ab64d80b2b6c575716c29ae80c562156fdfd18544f50484` | `applicable`: zero covariance | 1 | 0 |
| loneliness-mediation active chunks | `audit:a2277575c2c14996a37c9e6883dbcd34` | `sha256:7d5454f293e74834cae3925f5fcf1befac38338a6b9e4c74bfe938e2cbdf5f8a` | `applicable`: zero covariance | 1 | 0 |
| WSpiller vignette, unchanged | `audit:7cff8972588747ff98a7cba349e8ede3` | `sha256:5a9a4c61b7b36ff6f5a6ebfcd29cbf2e03bfa5bb4a32dc8fe07d16645db2fe9f` | `ambiguous`: both operands occur | 0 | 0 |
| WSpiller controlled mutation suppressing the two zero calls | `audit:7bd3b88cbbe5419b9c950c0a8b0fd8eb` | `sha256:6aaae2b684421996257f4d2422cfe8bec8a5564eb43a0a8ce6b3734206b76f78` | `applicable`: provided covariance | 1 | 0 |

The TwoSampleMR calls are inside a display-only ```` ```r ```` fence, not an executable R Markdown
```` ```{r} ```` chunk. The connector correctly does not treat displayed documentation as an
active workflow operation. The unchanged WSpiller vignette contains both zero and locally
constructed covariance branches, so the adapter correctly returns `ambiguous`; after the exact
two zero-call lines are replaced by comments in an evaluator-owned copy, it recognizes
`Xcovmat <- phenocov_mvmr(...)` followed by the two unchanged `gencov = Xcovmat` calls.

The two independent applicable zero cases preserve exact evidence spans:

- MR-tutorial: `scripts/MVMR.Rmd:512-513`;
- loneliness-mediation: `reverse-MR.Rmd:395` and `reverse-MR.Rmd:408`.

The controlled provided branch preserves `vignettes/MVMR.rmd:141-142` and line 160. Every
applicable observation uses `static_source`, the exact selected Artifact, and the typed
`selected_source_artifact_of_publication_surface` join.

All five runs report `partial_evidence_unavailable`; zero Findings is not a correctness
certificate. Every semantic lock records zero model calls, zero project Executions, and
`model_access_after_lock: false`. Replays preserve the audit ID, snapshot digest, semantic-lock
digest, assessment counts, and repository paths with zero additions, changes, or removals.

## Fresh-context skill result

An independent fresh-context agent read and followed the repository `scientific-audit` skill
against the pinned MR-tutorial repository. It selected `scripts/MVMR.Rmd`, ran standard mode,
verified integrity, retrieved the typed question, and stopped without selecting an Answer.

- audit ID: `audit:99da715331d5417b8949d6f3af6547a4`;
- semantic-lock digest:
  `sha256:caaa51300ec403d86a279ec54337e31b70113c607389afc15532626a0e2aca3d`;
- counts: 0 Findings, 0 ConditionalConcerns, 1 MaterialQuestion, and 7 Disclosures;
- observed operand: `zero_cross_exposure_covariance` at `scripts/MVMR.Rmd:512-513`;
- project Executions and authorizations: empty; controller model calls: zero; and
- the question remained open with the explicit unknown option available.

This passes skill usability for the new connector. It does not supply the scientist's sample
provenance or authorize a compatibility conclusion.

## Local tests

The implementation adds:

- schema-valid R Markdown front-matter, prose, chunk, disabled-chunk, malformed-fence, invalid-
  UTF-8, and no-execution parser tests;
- zero and local-constructor provided operands through the ordinary question lifecycle;
- commented, display-only, disabled, missing-argument, dynamic, reassigned-local, contradictory,
  and lexical hard negatives;
- path, suffix-case, chunk-label, formatting, and namespace metamorphic cases;
- selected-surface full-digest priority under a bounded budget;
- packaged scientific-check manifest identity and capability-source manifest validation; and
- independent audits, fresh-context skill transport, semantic locks, and model-free replays.

## Adjudication

The bounded connectivity milestone **passes**:

- the same zero-covariance representation is applicable in two independent applied repositories;
- one public display-only near match safely abstains;
- a public mixed-operand vignette is ambiguous rather than coerced;
- an evaluator-owned mutation exposes the supported provided-covariance branch;
- the selected-source snapshot ordering defect is fixed without increasing the byte budget;
- the skill reaches the exact scientist question and stops; and
- no path executes project code, makes a model authoritative, or emits a Finding.

The result is not general R support, general R Markdown support, scientific validation of MVMR,
or detector qualification. It proves one reusable format/method/scope connector seam with one
closed method representation.

## Test, acceptance criterion, and remaining limitation

- **Test added:** the parser, adapter, scope, hard-negative, mutation, snapshot-priority,
  independent-repository, fresh-context skill, lock, replay, and manifest tests listed above.
- **Acceptance criterion satisfied:** one naturally occurring representation travels across
  independent authors through reusable format, method, and scope contracts to one exact
  scientist-governed question, with safe abstention outside the closed grammar.
- **Remaining coverage limitation:** only single-line calls to `strength_mvmr()` and
  `pleiotropy_mvmr()` with literal zero or one unchanged local `phenocov_mvmr()`/`snpcov_mvmr()`
  object in active fenced R Markdown chunks are recognized. Execution, sample overlap, numerical
  consequence, general R dataflow, rendered documents, and production Finding authority remain
  unavailable.
