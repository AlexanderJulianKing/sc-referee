# ADR-0068: Qualification process consolidation

- **Status:** Accepted by the maintainer on 2026-08-07, in session, after a directed sweep for
  process overhead that does not protect a real evidentiary property
- **Date:** 2026-08-07
- **Scope:** All qualification-program process machinery from this date forward. Already-frozen
  artifacts, ledgers, and sealed blocks are unaffected; nothing frozen reopens.
- **Relates to:** Experiment 0056; ADR-0066; ADR-0067; TEN_FINDINGS_DELIVERY_PLAN.md

## Context

One envelope's pilot machinery grew to 82 single-use scripts, 20 artifact directories, 12
reviewer-calibration rounds, and 40 hand-declared timestamp constants. Declared-in-advance
timestamps caused three separate forward-dating failures. The experiment document still stated
panel requirements that the accepted ADR-0067 had already replaced. Milestones were being
recorded three times (machine ledgers, a delivery-plan table, and experiment-document prose),
and the redundant copies drifted. The maintainer reviewed the inventory and directed
consolidation: every rule must be scoped to exactly the property it protects.

The properties that remain load-bearing and are not reduced by this ADR: blind authoring of the
report surface, labels frozen before detector observation, deterministic replay, served-model
post-verification for CLI transports, and sealed held-out material.

## Decision

1. **One parameterized pipeline per protocol family.** Qualification steps (authoring, intake,
   calibration, review, labels, detector run, metrics) run through a single maintained pipeline
   implementation driven by per-envelope configuration, not through new single-use scripts per
   iteration. The pipeline is built once, as the vehicle for the ADR-0069 architecture, so it is
   not built twice.
2. **Per-envelope manifest carries the digest chain.** Each step reads its upstream digests from
   the envelope's manifest file, which the pipeline updates programmatically on each freeze.
   Hand-edited digest constants in code are retired.
3. **Timestamps are recorded, never declared.** Every `frozen_at`, `run_at`, and `created_at` is
   stamped from the clock at artifact-write time. Chronology validators compare recorded values.
   Declaring a timestamp in advance is prohibited; this retires the forward-dating failure class.
4. **Calibration binds to the configuration, not the participant label.** A calibration result
   binds to (model id, pinned binary digest, calibration protocol digest) and is recorded in a
   calibration registry. It is reused across participant labels and iterations until one bound
   component changes. Re-running an identical calibration for a fresh actor name is prohibited.
5. **One disclosure sentence.** The cross-provider unavailability disclosure required by
   ADR-0066/0067 is one standing sentence in each qualification report. Evaluation-private
   shadow adjudication records and per-case deferral prose are not produced under the lean
   protocol.
6. **One narrative logbook.** Machine ledgers are the evidentiary record. The delivery-plan
   evidence table is the single narrative log, one row per milestone. Experiment documents change
   only through dated protocol amendments, not per-milestone prose.
7. **Held-out role sets are chosen at seal time, default four.** For envelopes not yet sealed,
   the maintainer chooses the held-out role set when sealing; the default is error-bearing,
   corrected twin, valid alternative, and hard negative. Envelope 10's already-sealed seven-role
   block is unchanged. The four surplus frozen assignments remain immutable and unopened.
8. **Sighted mechanical repair of authored cases is permitted outside the blind surface.**
   Defects in an authored case that do not touch the report's sentences or numbers (paths,
   newlines, transport artifacts, byte mismatches) may be repaired by hand, logged, and the case
   proceeds and counts. Fixes inside the report surface require one fresh blind authoring call.
   This replaces the blanket no-repair rule.

## Consequences

- Each pilot iteration drops from roughly ten new scripts and several hand-edited freezes to one
  configuration change and one pipeline run.
- The forward-dating and digest-transcription failure classes are removed structurally instead
  of by discipline.
- Existing single-use scripts remain in the repository as the frozen record of already-executed
  protocols; they are not ported, re-run, or deleted.
- EXPERIMENT-0056's retained-requirements text is amended to defer to the accepted review ADRs;
  the amendment is recorded in that document with this ADR as authority.
