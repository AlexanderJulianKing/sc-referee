# ADR-0025: Keep the CasRx isoform-axis model separate from assay alignment

- **Status:** Accepted
- **Date:** 2026-07-30
- **Accepted:** Under the repository owner's standing authorization for non-major ADRs that do not
  expand Finding authority, schema meaning, execution privilege, or public maturity claims
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None
- **Related decisions:** Accepted ADR-0019, revised ADR-0020, and Experiment 0025
- **Evidence basis:** Experiment 0025 CRISPRi/CasRx fixed-case and reverse-control ablations

## Plain-language summary

The CRISPRi/CasRx case contains two different scientific decisions. One aligns measurements made
on different assay plates. The other decides how transcript overlap enters the CasRx effect model.
Correcting the plate offset fixed one requested effect but not the transcript-specific effect.

Two independently authored workflows estimated the transcript effect from a high-overlap guide
subset using one knockdown-efficiency axis. A repaired workflow instead represented each guide by
simultaneous effective dominant- and non-dominant-transcript knockdown axes. Reverting only that
axis choice moved the transcript estimate back outside tolerance. This ADR admits one narrow,
scientist-governed isoform-axis question without treating either choice as universally correct.

## Context

The frozen CRISPRi/CasRx workflow matched its binary decision but missed both requested numeric
effects. Applying only paired per-plate follow-up-minus-primary location offsets moved the neighbor
effect within tolerance while the lncRNA-specific effect still failed. A broader repair combining
the paired offsets, the two-axis CasRx model, and bounded pooled-screen preprocessing moved all
three answer fields within contract.

A reverse control retained every other repair but returned the CasRx stage to the high-overlap
one-axis regression. The lncRNA-specific absolute error increased to `0.013661709188756428`
against tolerance `0.01`, while the neighbor effect and decision remained within contract. This
supports the axis choice for that fixed case, but it does not establish a universal method rule or
make the evaluation answer production authority.

## Decision

### 1. Add one atomic question-only module

Add `check:casrx-isoform-axis-model` under the ScientificContract `measurement_model` dimension.
Its two closed operands are:

- `simultaneous_dominant_and_nondominant_effective_knockdown_axes`; and
- `high_dominant_overlap_subset_single_efficiency_axis`.

The question asks which model governs the dominant-transcript effect for the current review. The
scientist may select either operand or retain the requirement unresolved. Numeric proximity,
benchmark identity, and model confidence cannot select it.

### 2. Require an exact selected-report declaration

The two-axis operand requires one selected-Markdown paragraph that defines effective dominant
knockdown as overlap times knockdown efficiency, defines non-dominant knockdown as one minus
overlap times efficiency, and states that a simultaneous two-axis model supplies the dominant-axis
coefficient.

The one-axis operand requires a report-level CasRx context, an explicit guide restriction by
dominant- or major-isoform overlap, and a one-axis, through-origin, or least-squares relation between
growth effect and knockdown efficiency. The adapter does not hard-code a particular overlap
threshold.

QC plots, axis construction without an effect model, ordinary two-covariate regressions, or
conflicting supported declarations cannot establish one operand. They remain not applicable,
unsupported, or ambiguous as appropriate.

### 3. Keep axis choice separate from scale and offset

The paired-bridge location offset, any multiplicative cross-assay scale, and the isoform-axis model
can coexist. The new check must not answer or suppress
`check:paired-bridge-location-alignment`, and the bridge check must not infer the axis model.

Pooled-screen pseudocount, normalization, outlier, and local-effect-model choices also remain
separate unsupported families. The successful combined repair is not permission to merge them
into one calibration question.

### 4. Preserve the question-only ceiling

The module cannot infer that a non-dominant biological component exists, choose an overlap
threshold, prove that the reported fit executed, attribute a numeric mismatch, or emit a Finding.
Matching and conflicting scientist Answers compile only to deterministic Disclosures. No public
schema, detector maturity, qualification status, or execution privilege changes.

## Alternatives rejected

### Treat the paired bridge correction as sufficient

Rejected because the paired-offset-only ablation repaired the neighbor estimate but left the
transcript-specific estimate outside tolerance.

### Fold isoform axes into one broad assay-calibration question

Rejected because additive offset, multiplicative scale, and effect-axis design are independent and
can coexist. A composite choice would conceal partial repairs and repeat earlier semantic
conflations.

### Hard-code the benchmark's overlap threshold

Rejected because the reusable obligation is whether overlap is modeled through one restricted
axis or simultaneous effective axes, not whether one report used `0.90`.

## Acceptance evidence

- Exact one-axis and simultaneous-two-axis declarations each produce their own operand.
- Conflicting declarations are ambiguous; QC-only and unrelated regression lookalikes produce no
  question.
- The axis question and paired-bridge question coexist as two independent MaterialQuestions.
- Matching and conflicting Answers remain replay-stable Disclosures with zero Findings.
- Two independently authored failed reports expose the one-axis operand; the combined repaired
  report exposes the two-axis operand; the one-axis reverse control exposes the one-axis operand.
- All four semantic locks and rendered reports replay byte-for-byte without project execution or
  model access after lock.

## Remaining limitation

The adapter recognizes two explicit selected-Markdown declarations. It does not parse arbitrary
CasRx source code, validate isoform-overlap measurements, decide whether a second axis is
biologically warranted, choose a threshold, validate assay alignment, or establish numeric
causality. Those boundaries remain unknown or unsupported rather than Findings.
