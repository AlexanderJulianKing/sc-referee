# sc-referee — example report fragment

## Executive assessment

**No claims needing correction were identified within the inspected evidence and validated detector coverage.**

The audit inspected 18 of 20 final-claim paths. Two MaterialQuestions remain unresolved, one claim depends on an opaque external operation, and three detector coverage gaps are documented below. This is not a determination that the analysis is correct.

| Assessment type | Count |
|---|---:|
| Findings | 0 |
| ConditionalConcerns | 1 |
| MaterialQuestions | 2 |
| Disclosures | 4 |

## Conditional concern

### If `sample_id` identifies donors, repeated donor measurements appear to be modeled as independent

**Condition:** The meaning of `sample_id` is unresolved.  
**Potential impact:** Material if true.  
**Affected claims:** Figure 3 treatment effect; abstract direction statement.

The fitted model has one row per `sample_id` and no explicit donor-level random effect or cluster-robust uncertainty. This is not a Finding because the repository does not define whether `sample_id` denotes a donor, library, or sequencing lane.

## Material question

### What biological or technical unit does `sample_id` identify?

**Why it matters:** The answer determines whether the repeated-measures detector applies.  
**Evidence searched:** data dictionary, code comments, notebook markdown, sample sheet.  
**Plausible answers:** donor; specimen; library; lane; unknown.

## Disclosure

### Custom variant caller treated as an opaque boundary

The downstream VCF was inventoried and its checksum was recorded. The custom caller's internal measurement and error semantics were not inspected. This does not allege that the caller is incorrect; it limits what the audit establishes for dependent claims.
