# Prospective benchmark-blind authoring briefs

- **Status:** Coordinator template implemented; this repository contains no authored, labeled, or
  reviewed qualification cases
- **Related protocol:** Experiment 0051 and ADR-0042
- **Production impact:** None
- **Finding impact:** None
- **Execution impact:** None; authoring and review do not authorize project execution

## What this artifact is

`evaluation/prospective-qualification-v1/benchmark-blind-authoring-briefs.template.json` is a
coordinator-side source for the 10 relation envelopes and 7 controlled case roles in each study
block. Its Cartesian product describes 70 prospective assignments for the threshold pilot and 70
new assignments for the held-out block.

The template makes the scientific contrast intelligible without disclosing the detector's source,
recognizer mechanics, implementation identifiers, prior observations, adjudicated labels,
thresholds, or source-case identities. The ten premises are scoped choices for authored study
cases. They do not assert that any method is universally correct.

The artifact does not create independent evidence. A case becomes an eligible study input only
after the separately frozen protocol assigns an opaque case identity, a qualified independent
author creates and freezes the repository, every outcome is retained, and the required answer-blind
reviews and authentication checks are complete.

## Packet materialization boundary

The master template is not itself an author prompt. A coordinator must extract exactly one relation
brief and exactly one cell brief into a packet containing only:

- the opaque case identity and a block-neutral assignment token;
- the assigned relation premise and semantic roles;
- the assigned construction task;
- neutral repository deliverables; and
- the deadline and submission channel.

Do not include relation ordinals, other cell briefs, protocol mappings, detector files, existing
cases, review forms, or scoring material. Authors must not receive the check identifier, candidate
identifier, binding digest, expected detector behavior, or intended adjudication answer.

The designed cell is an authoring instruction, not a label. If the repository does not actually
instantiate that design, the no-replacement protocol retains the mismatch; reviewers do not repair
it into the intended cell.

## The seven construction roles

### Designed method conflict (`error_bearing`)

Create one coherent primary workflow whose report and inspectable source both use the contrasting
construction on the exact target governed by the supplied premise. Do not include a waiver,
amendment, sensitivity-only qualifier, or alternate target that resolves the contrast.

### Single-relation corrected twin (`corrected_twin`)

The same author receives only their frozen error-bearing reference and changes exactly the governed
semantic relation. The target, inputs, layout, prose style, and unrelated methods stay fixed. A
private coordinator change note records the semantic edit; it is not part of the review packet.

### Scoped valid alternative (`valid_alternative`)

The primary target follows the supplied premise. The contrasting construction is nevertheless used
substantively in a clearly different scope: for example, a sensitivity analysis, another target, or
an explicit pre-authorized exception. The boundary must be exact enough to show which method governs
the primary result.

### Near-language negative (`hard_negative`)

The project naturally uses much of the same scientific vocabulary while following the supplied
premise. It discusses the contrasting construction as rejected, hypothetical, historical, or bound
to another object. This is not satisfied by a token negated keyword sentence.

### Genuinely indeterminate method (`ambiguous`)

The project has a real target and plausible analysis, but available evidence does not settle one
material relation: operation order, target binding, primary-versus-sensitivity scope, or
representation identity. Empty files, arbitrary truncation, and hidden resolving notes are not
valid ambiguity.

### Locally unsupported evidence form (`unsupported`)

The relation is material but conservative static inspection cannot establish it because the
decisive construction is unavailable, opaque, dynamically assembled, or expressed in an
unsupported source form. The limitation should be localized. The repository must not be malicious,
credential-dependent, globally unreadable, or dependent on the referee executing project code.

### Independently rewritten implementation (`renamed_implementation`)

A distinct author and execution context receive the relation brief and this cell brief, but no
content or surface description from the referenced error-bearing case. The new workflow changes the
domain story or measurement setting, terminology, variable names, file layout, prose organization,
and code structure while independently instantiating the same abstract contrast. Synonym or filename
replacement alone is insufficient.

The existing protocol field remains `renamed_implementation` for compatibility; the author-facing
name is “independently rewritten implementation” because surface renaming is only one small part of
the requirement.

## The ten relation premises

1. Repair the inherited founder-state orientation against the declared reference before building
   the primary state-model emissions, versus using the supplied orientation directly.
2. Decompose an average of two directional measurement-error rates using an independent directional
   constraint, versus copying that average into both directions.
3. Correct the class distribution within each population cell before standardizing with target
   weights, versus combining observed cells before one aggregate correction.
4. Use a declared negative-binomial model prediction as the primary expected count, versus using a
   same-stratum arithmetic mean.
5. Include a technical group recoverable by the supplied proxy and grouping rule in the primary
   adjustment set, versus recovering or discussing it but omitting it from that model.
6. Select conditionally distinct signals in phase one and use matching joint coefficients in phase
   two, versus marginal selection followed by marginal coefficients.
7. Use the direct continuous calibrated prediction as the downstream quantitative exposure, versus
   using a hard, rounded, or posterior-expected value derived from classifier states.
8. Define primary somatic eligibility with a purity- and copy-adjusted clonal-fraction window,
   versus direct raw-signal and local-copy thresholds.
9. Jointly fit the measured target axes and observed guide nuisance terms in the primary local
   model, versus external subtraction followed by a reduced single-axis fit.
10. Use the complete declared map as the primary transition-time exposure denominator, versus only
    the length of retained high-confidence state calls.

These descriptions deliberately express operations, ordering, representations, scope, and targets.
They deliberately omit particular source tasks, repositories, filenames, variables, programming
languages, wording patterns, and prior detector behavior.

## Independence and chronology

- Freeze detector bytes before assignments.
- Materialize packet digests before an author receives a packet.
- Keep pilot and held-out case material disjoint.
- Do not expose pilot cases, reviews, thresholds, or observations to held-out authors.
- The corrected twin keeps the reference author; the independent rewrite must use a different
  author and context.
- Reviewers receive the frozen scientific premise and repository, not the designed cell type or
  authoring instructions.
- Preserve failed, contaminated, withdrawn, unavailable, and cell-mismatched assignments without
  replacement.

## What this still does not establish

The template, its digest, its tests, and any rehearsal material establish only that the study can be
specified consistently. They do not authenticate a participant, demonstrate independence, supply a
scientific label, estimate sensitivity or false-accusation rates, qualify any relation envelope,
promote a detector, or authorize a production Finding.
