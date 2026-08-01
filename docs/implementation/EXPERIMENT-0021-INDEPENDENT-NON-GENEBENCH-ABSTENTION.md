# Experiment 0021: Independent non-GeneBench scientific-check abstention

- **Status:** Completed phase-A false-applicability screen; external applicable portability remains
  open
- **Date:** 2026-07-29
- **Governing decision:** Accepted revised ADR-0020
- **Public schema change:** None; accepted schema v0.14.0 remains unchanged
- **Production capability change:** None

## Purpose

Test whether the ADR-0020 scientific-check registry spuriously asks its narrow QTL,
pulse-admixture, or MVMR questions when it encounters independently authored public repositories
with realistic nearby vocabulary, different layouts, and different implementation languages.

This is a conservative false-applicability test. The repositories were not selected because they
contain demonstrated scientific mistakes, and no outcome below is an accusation about their
scientific quality. A correct `not_applicable` or `unsupported` result is the intended outcome when
an installed adapter cannot establish one of its exact operands.

The experiment separately asks whether any current adapter is genuinely applicable to an
independent repository. That second condition is necessary before claiming useful method-level
portability.

## Frozen public inputs

Each repository was acquired from its exact public commit archive, extracted into a temporary
workspace, and audited with its root `README.md` as the user-selected publication surface. The
archives and audit outputs were not vendored into this repository.

| Repository | Exact commit | Archive SHA-256 | Relevant independent shape |
|---|---|---|---|
| [rqtl/qtl2](https://github.com/rqtl/qtl2/tree/3329fb52cdced4762c6f82b3b5e3c294382ad9ca) | `3329fb52cdced4762c6f82b3b5e3c294382ad9ca` | `7bb6bf6879311453c226b646b2a8a8a2b08a8117c9ba6891f671b7559d54a460` | R/C++ multi-parent QTL package with explicit HMM vocabulary |
| [dmgatti/DOQTL](https://github.com/dmgatti/DOQTL/tree/3434b9fb6d2381aec467ac4030110e3de4b727c1) | `3434b9fb6d2381aec467ac4030110e3de4b727c1` | `38d243038bc109d5870e8527aafa0bdfb9b26ffc723d56818b3d1772be72703c` | R/C multi-founder QTL package |
| [broadinstitute/tensorqtl](https://github.com/broadinstitute/tensorqtl/tree/0c4db65a0cdc47f3b824ae530b89d270ef5e0096) | `0c4db65a0cdc47f3b824ae530b89d270ef5e0096` | `72a79ceae55fde22f2197b427efa8391443aabde6f1d7a03dcc648e2d14594a1` | Python QTL package with allele-order vocabulary but no founder-HMM target |
| [WSpiller/MVMR](https://github.com/WSpiller/MVMR/tree/bceaa38088d093a5d30c713afb016e7fbc7ed2be) | `bceaa38088d093a5d30c713afb016e7fbc7ed2be` | `e1b8c506a5c4986c866db161bcbbe9efaa5d52b1890f8edfcd58a41df3b46482` | R MVMR package with robust-estimation material |
| [qingyuanzhao/mr.raps](https://github.com/qingyuanzhao/mr.raps/tree/dd79b5bd74d10b699503cdd226d70c726f11c796) | `dd79b5bd74d10b699503cdd226d70c726f11c796` | `4544157289f92caf59bc33c9d1d544de0ea8027f946efec6a4676c8a2ac75101` | R robust-MR package whose report wording reaches a method-like boundary |
| [ZhaotongL/MVMR-cML](https://github.com/ZhaotongL/MVMR-cML/tree/20d09a54637e70a35f31a43d56c1e6276c99bb17) | `20d09a54637e70a35f31a43d56c1e6276c99bb17` | `31c6c8ffe49e747881c12f65babb945be91aa9b553c70f30c6419f060a5f88c4` | R/Rcpp MVMR package with a different source and report layout |

No project-authored file was imported or executed. The ordinary standard-mode audit kept project
execution disabled. No audit or replay made a model call.

## Results

| Repository | Audit ID | Semantic-lock digest | Founder check | Pulse check | MVMR check | Findings / questions |
|---|---|---|---|---|---|---:|
| qtl2 | `audit:83d77fd21c8b4c25931dcd2eaf476c79` | `sha256:2fc4b14126bbb00f03cefff155d58c498b1b94dfd32dfa779a85aaaad3ac2f71` | `not_applicable` | `not_applicable` | `not_applicable` | 0 / 0 |
| DOQTL | `audit:b90f16bb38fe4c87a4a96a694b67b1d7` | `sha256:19153638a39b7f7a288e8b13cc3ee205e3a80ab25c431907dde4ca7ca3232dcd` | `not_applicable` | `not_applicable` | `not_applicable` | 0 / 0 |
| tensorQTL | `audit:cf0bf74585e24c11a316868558ed6bdd` | `sha256:7dd0aa565277ce7877d931dc077c757c8851158f7705f5ce282d155247949443` | `not_applicable` | `not_applicable` | `not_applicable` | 0 / 0 |
| MVMR | `audit:8ea10950eab642b4bf1fb03864abcd40` | `sha256:b0dd30375303b07d0360448ed9e3b6570a0cb1715ce34c6839ba72765d301fe3` | `not_applicable` | `not_applicable` | `not_applicable` | 0 / 0 |
| mr.raps | `audit:d2dca874b2ce45779ed9b40f587ccdd4` | `sha256:7afea8d68538ac17e18482f49375055ca98f899a8414591ca63cf7aff90a2fc1` | `not_applicable` | `not_applicable` | `unsupported` | 0 / 0 |
| MVMR-cML | `audit:ce8701ecb597472599a0b5e6d32caeb7` | `sha256:c8f9edb0557da8c5bf80fab2ac430b359e631a26922a72de44bebc73b26666a9` | `not_applicable` | `not_applicable` | `not_applicable` | 0 / 0 |

The five `not_applicable` MVMR outcomes record that every completed adapter determined its exact
representation did not apply. The mr.raps README contains robust-method wording close to the MVMR
check, but it does not state either enumerated LD-covariance operand. The adapter therefore returns
`unsupported` with the exact basis “Method-like wording is present, but no enumerated exact
declaration is supported.” It does not create a MaterialQuestion.

All six audits report `partial_evidence_unavailable`; none is a correctness certificate. Each
replay preserved the audit ID, snapshot digest, semantic-lock digest, assessment counts, and every
repository path with zero additions, changes, or removals.

## Adjudication

The phase-A false-applicability screen **passes**:

- realistic QTL, HMM, allele, MVMR, and robust-estimation vocabulary did not create a false
  MaterialQuestion;
- the closest lexical hard negative became `unsupported`, not an invented operand;
- all six runs retained zero Findings and zero ConditionalConcerns;
- different R, C/C++, Python, Rcpp, package, vignette, and flat-report layouts did not cause an
  adapter failure; and
- replay was deterministic without project execution or model access.

Useful external method-level portability **does not yet pass**. No independent repository produced
an `applicable` normalized observation through any installed adapter. The current selected-report
grammars are exact enough that their positive phrases occur only in the controlled development
workspaces inspected so far. The only source adapter is Python-specific, and its static
observation cannot create public evidence without the deliberately missing typed
source-to-selected-analysis join.

It would be incorrect to relabel six safe abstentions as proof that sc-referee can recognize these
methods across ordinary scientific repositories.

## Test, acceptance criterion, and remaining limitation

- **Test added:** six commit-pinned, answer-blind, non-executing public-repository audits and six
  model-free replays, including domain-near QTL and robust-MR hard negatives.
- **Acceptance criterion satisfied:** independent-author false-applicability, opaque-boundary,
  nearby-vocabulary, mixed-layout, and deterministic-replay behavior all fail closed.
- **Acceptance criterion not satisfied:** no current adapter supports an independently authored
  applicable representation, so the ADR-0020 experimental method-portability claim remains
  unavailable.
- **Remaining coverage limitation:** the public inputs are correctness-unlabeled controls selected
  for safe abstention. They do not qualify a detector, validate a scientific requirement, prove a
  numeric consequence, cover R/R Markdown source semantics, or supply the typed
  source-to-selected-analysis join.

## Next bounded decision

The next positive-portability attempt must begin from a naturally occurring, independently
authored scientific representation rather than another controlled phrase. It needs:

1. an exact abstract method obligation supported independently of a benchmark answer;
2. a capability-limited adapter for that real representation;
3. a covered-good applicable control plus nearby hard negatives;
4. explicit typed scope binding to the reviewed analysis; and
5. the same question-only, no-Finding ceiling until ordinary detector qualification succeeds.

Adding R/R Markdown parsing, changing the source-to-analysis record meaning, or broadening public
capability claims required a separate accepted ADR. Accepted
[ADR-0021](ADR-0021-RMARKDOWN-MVMR-COVARIANCE-CHECK.md) uses recurring independent public MVMR
`gencov` calls as that external-first representation while keeping the scientist's sample-overlap
premise explicit and the output question-only. Its bounded implementation and positive external
connectivity validation are recorded in
[Experiment 0022](EXPERIMENT-0022-EXTERNAL-RMARKDOWN-ADAPTER-CONNECTIVITY.md).
