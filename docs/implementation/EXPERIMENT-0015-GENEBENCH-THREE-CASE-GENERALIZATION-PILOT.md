# Experiment 0015: Three-case GeneBench generalization pilot

- **Status:** Active evaluation-private experiment
- **Date:** 2026-07-29
- **Governing decisions:** Accepted ADR-0017 and ADR-0018
- **Corpus ceiling:** Public development; not held out, qualification eligible, or promotion eligible

## Purpose

Test whether the evidence-first audit and answer-isolation boundaries survive more than the single
Hi-C demonstration, and collect concrete method failures before defining another production method
profile. This experiment does not treat a numeric mismatch as a Finding or let the answer-side
reference mutate the frozen production audit.

## Isolation and run protocol

The pinned GeneBench-Pro package revision
`8bb6cde6ab0b0554e867c46f5698fd953bf2c68a` first passed Experiment 0005 preflight. The existing
Experiment 0012 interface prepared three separate workspaces containing only `task.md` and declared
visible data:

1. `wf_selection`, for stochastic time-series and measurement-error modeling;
2. `carrier_cnv_pseudogene_residual_risk`, for multiclass assay calibration, conditioning, and
   target-population standardization; and
3. `statgen_cis_mvmr_winnerscurse_scaling_ldaware`, for allele orientation, independent effect
   estimation, LD-aware multivariable estimation, and scale conversion.

Three fresh-context agents were each restricted to one exact workspace and denied the package,
ground truth, grader, reference report, sibling workspaces, network, and prior-run context. Each
authored and executed only its own workflow. sc-referee then statically audited and semantically
locked each workspace before answer-side grading. All three audits emitted zero Findings and
verified no post-lock model access. Replay completed without project execution.

## Grader adapter boundary

The first grading attempt failed closed before comparison because the adapter supported only the
Hi-C case's tolerance-only numeric contract. The two new package contracts added:

- optional, paired finite `min_value`/`max_value` metadata around numeric absolute tolerances; and
- one closed composite form containing required, case-sensitive string equality plus required,
  bounded numeric absolute tolerance.

Experiment 0015 extends only the isolated GeneBench adapter to those exact forms. It does not import
or execute the package grader, accept relative tolerances, optional fields, case-insensitive matching,
arbitrary comparison code, or use results as labels or metrics. The generic
`grade-genebench-public-answer` command handles the mixed form; the existing numeric command remains
numeric-only. Tests cover bounded numeric success, mixed success, mixed mismatch, command dispatch,
write-once output, and self-consistent profile broadening that must fail closed.

## Frozen outcomes

| Case | Audit and semantic lock | Grade | Result |
|---|---|---|---|
| `wf_selection` | `audit:eb5cf01517384e068c9c17dd75278b5e`; `sha256:f8c6e4356c107b46018487e7f54775df8c3f1bae229cf0852e1b1c18033eacf5` | `genebench-answer-grade:0f5865bdcf0c7389de6b`; `sha256:3682f6d8465e7225dbed473322a13e4aa879eb60e8edd28d69542aea3735cfec` | The categorical locus matched. The selection coefficient's absolute error was `0.037656` against tolerance `0.02`. |
| `carrier_cnv_pseudogene_residual_risk` | `audit:c3491c237c8e40f8ae0f837b035061db`; `sha256:30811c612da9cd837df185f04c768363c747adec99143abb7f1be307d5e9f40a` | `genebench-multi-numeric-grade:9920251c4b8bc362c4d8`; `sha256:0e3d1c2e896fe6b3f71664c61b7b55c12ea75e64d716c2be357064ca650aff6c` | Both roster carrier frequencies matched. Residual risk, partner frequency, and couple risk were outside tolerance. |
| `statgen_cis_mvmr_winnerscurse_scaling_ldaware` | `audit:d310cbe459444065a93865d2ef61ac99`; `sha256:23f2a6e0e8983f918713074cb7dda23f466ef23989f9b6154300cbad5fa7f8e1` | `genebench-multi-numeric-grade:d564d88e479947720d44`; `sha256:108e6df87023e0472c8b4210cff21108af9b26ab49d61670708b6315333a8a20` | Both direct-effect estimates were within tolerance. |

The grades reveal agreement or disagreement only. They do not by themselves establish a scientific
issue, causal method failure, or Finding.

## Answer-side root-cause evidence

After the locks were frozen, the full-digest reference reports were inspected separately.

### Wright-Fisher measurement error

The frozen workflow explicitly models the reported `0.16` average error as a symmetric two-way
miscall probability. The reference report, digest
`sha256:d0af059c538232b17b1195b290ae308170f19fb04728964131f9788396ea6e17`, instead binds the
prompt's approximately `0.01` instrument floor, ancient C/T context, allele orientation, and average
error into directional rates of `0.31` derived-to-ancestral and `0.01` ancestral-to-derived. The
reference reproduces the frozen workflow's reported estimate under the symmetric interpretation and
shows the directional emission changes the answer. This is a localized evaluation root cause, not a
production Finding.

### Carrier-risk joint calibration and target construction

The frozen workflow calls the founder class when exactly one founder marker is high or when both are
high in the same phase. The reference report, digest
`sha256:05097045111f7fee64ca4ac1d37cc232c06835978609a6d1825fe3d42642a55c`, requires both
founder-marker rows to pass on the same non-missing phase set. The workflow also applies independent
per-class Rogan-Gladen inversions and calibrates poststratified positive rates after aggregation. The
reference instead solves the coupled multiclass detected-call equation, including the shared
noncarrier false-positive term, with a nonnegative active-set fit and estimates calibrated class
probabilities inside each ancestry/family-history/site/wave partner cell before full-roster
weighting. These exact differences explain why close carrier-frequency totals did not rescue the
conditional and partner-derived outputs. They remain evaluation root-cause evidence, not Findings.

### MVMR covered-good case

The MVMR workflow used holdout effects, allele harmonization, the supplied LD covariance, joint
estimation, robust residual handling, and usable-batch SD scaling. Its method was not identical to
the reference report's iterative residual-pruned GLS, but both released fields were within tolerance.
The pilot therefore supplies one important correct control: method wording differences alone must
not be promoted into an issue without an exact governing obligation and demonstrated consequence.

## Interpretation and next decision

The system has now survived three additional isolation, audit, replay, and grading lifecycles, and
the grading adapter covers two real package contract shapes without open-ended code execution. The
pilot also shows that method failures are heterogeneous. One case concerns directional measurement
error; one combines biological call construction, coupled calibration, and target-population
standardization; one succeeds despite a nonidentical robust estimator.

No new production method profile is justified yet. Each failure family has only one independent
case, so there is no recurring adjudicated failure from which to define a narrow reusable contract.
Experiment 0016 subsequently confirmed that four closed AST profiles localize the exact submitted
shapes and that the directional repair and complete three-part carrier repair recover the released
fixed-case answers. The next pilot should seek a second case for measurement-error directionality
or for coupled calibration/standardization, while retaining matching, ambiguous, and unsupported
controls. Until then, detector scope, schema v0.14.0, Finding eligibility, and qualification status
remain unchanged.
