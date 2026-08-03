# Experiment 0049: GeneBench cold recognition wave 1

- **Status:** Completed first six-case development wave
- **Date:** 2026-08-03
- **Decision:** Accepted ADR-0059
- **Schema:** Unchanged at `0.18.0`
- **Corpus ceiling:** Public development; not held-out, metric-eligible, qualification-eligible,
  or promotion-eligible

## Question

When fresh agents independently implement public GeneBench-Pro tasks from task text and declared
data only, does the ordinary auditor recognize the method choices that distinguish common correct
and incorrect workflows? Can misses be repaired with generic bounded rules rather than case IDs,
answer keys, or open-ended model review?

## Frozen source and isolation

- source: OpenAI GeneBench-Pro public package on Hugging Face;
- pinned revision: `8bb6cde6ab0b0554e867c46f5698fd953bf2c68a`;
- verified manifest digest:
  `sha256:729335607c5bab8dfcb8c3beccbe74c2ecea9a83dc839a9b166973616870b556`;
- verified checksums digest:
  `sha256:49fe74516853287411e5c50c88ce5f5cd76362716139248ad5641496014f760`.

Each author saw one prepared task workspace and was prohibited from inspecting answer-side files,
other cases, prior attempts, repository evaluation code, or network resources. Workflows were run
by the authors, frozen by the auditor, and graded only after semantic lock. The production audit
had no answer access and did not execute the project code.

## Results

| Case | Answer-side grade | Prior scientific questions | Updated relevant coverage |
|---|---|---:|---|
| Multi-parent QTL | outside contract | 0 | `applicable`: direct founder input reached HMM emission; one orientation question |
| Wright-Fisher selection | within contract | 0 | `applicable`: direction-specific two-rate observation model; one interpretation question |
| Carrier residual risk | outside contract | 0 | `applicable`: observed distributions were standardized before joint calibration; one estimator-order question |
| Masked Hi-C loop strength | outside contract | 0 | `applicable`: same-diagonal arithmetic expected count and focal-background omission; two requirement questions |
| Ambient-state eQTL | outside contract | 0 | `applicable`: negative-control technical signal was carried into unit aggregation but omitted from the enumerated primary adjustment set; one requirement question |
| cis-MVMR | within contract | 0 relevant scientific questions | control; the audit exposed only a general output-scope question |

The first three audited workflows all initially returned zero Findings, zero concerns, zero
questions, and twenty coverage Disclosures. Across the first six cold cases, four answers were
outside the public grading contract and two were within it. After the bounded changes, all four
grade-mismatching cases produce a relevant scientific method question. One within-contract
workflow produces a relevant question that can become a covered negative after an authorized
requirement is supplied. A question is not counted as an identified error.

## Replay identities for the first implemented wave

| Case | Audit | Semantic lock |
|---|---|---|
| Multi-parent QTL | `audit:083b715c44974bd6956ba3ecab071442` | `sha256:2a8b22aff904f424f4ca3fd5c6dd81ba01de41e39ba7dc0455c46b1e66847c06` |
| Wright-Fisher selection | `audit:2dfbf9b7fcc94dcaa9b1993c677b3b80` | `sha256:2a68fd123bab1922392b477fa002fbbdd1e3b3ee474c9f378dc4d828d600dd7f` |
| Carrier residual risk | `audit:fb5e635e06224cd3874078f8516ec19b` | `sha256:440981b09b50013950a4d19242ed27affc3f833f0c0f5842d7cc2401ab5e5aae` |
| Masked Hi-C loop strength | `audit:0812f1cf573a457e994fc2e53d3ced00` | `sha256:a2175badad89a87d0569535d1180bc97e98698458a1c5e8d7180af4c70166b91` |
| Ambient-state eQTL | `audit:ffddd01cf6214b6a8ded35324404e4eb` | `sha256:3f476dbef9b2530722837f078372d8db5a5ca4e971ee5ac5b4c578689e26ea77` |
| cis-MVMR | `audit:2247d806b12d46a7815931ea5928cfc1` | `sha256:64d6eb0879f69c6548237552424f46eb33a9614f35971be4058e64494bf0eb23` |

The Hi-C rerun localized both independent method choices. The ambient-state rerun localized the
missing adjustment-set decision without asserting that the data contain a qualifying group.
cis-MVMR remains bounded control evidence rather than an adverse result.

## Interpretation

This wave demonstrates that the registry and question lifecycle were not the missing foundation;
natural-language and source-recognition breadth was. It also demonstrates a usable development
loop: cold authoring, pre-answer audit, answer-side grade, generic case formulation, controls, and
forward rerun.

It does **not** demonstrate production error-detection sensitivity. The cases are public, finite,
agent-generated, and development-visible after freezing. An answer mismatch alone does not prove a
scientific method error, and a recognized method choice remains unresolved until an external
requirement governs the review.

## Next wave

1. Implement the coverage-ledger generator required by ADR-0020 or retain an exact generated
   documentation ledger until its record shape stabilizes.
2. Build a generic recoverable-technical-stratum case from data distribution, model-covariate, and
   scope evidence; do not add an ambient-task special case.
3. Continue four remaining answer-isolated GeneBench workflows and preserve within-contract
   controls.
4. Start the separate generic DependenceCase/pseudoreplication vertical from the portfolio plan.
5. Run non-GeneBench, independent-author false-applicability and portability tests before making
   any method-level portability claim.
