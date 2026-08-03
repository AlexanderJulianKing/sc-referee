# Experiment 0050: GeneBench cold recognition wave 2

- **Status:** Completed remaining four-case development wave
- **Date:** 2026-08-03
- **Decision:** Accepted ADR-0059
- **Schema:** Unchanged at `0.18.0`
- **Corpus ceiling:** Public development; not held-out, metric-eligible, qualification-eligible,
  or promotion-eligible

## Question

Does the answer-isolated cold loop continue to expose generic recognition gaps in the remaining
four GeneBench-Pro workflows, and can those gaps be closed without task identifiers, answer
values, filenames, or open-ended model issue hunting?

## Isolation and order

Each author received only one public task and its declared data. Authors could not inspect
answer-side evaluation files, public reference reports, other attempts, repository recognizer
code, audit outputs, or network resources. Each workflow was frozen and audited before its public
evaluation contract was opened. Reference reports were inspected only after the pre-answer audit
and numeric grade were fixed.

The source revision and checksum identities are the same pinned corpus recorded in Experiment
0049.

## Results

| Case | Public grade | Pre-change relevant questions | Updated relevant coverage |
|---|---|---:|---|
| Structural inversion | outside contract on subhaplotype risk | 0 | classifier-derived posterior expected copy dosage; one representation question |
| TXR1 causal SV | outside contract on all three numeric fields | 0 | raw molecule-fraction/local-copy target gate and sequential post-treatment endpoint integration; two independent questions |
| CRISPRi/CasRx locus decomposition | outside contract on neighbor effect | 0 | nominal focal-row scope and external-subtraction/single-axis local model; two independent questions |
| Recent-pulse sex-biased ancestry | outside contract on all four fields | 0 | called-path rather than full-map pulse exposure and exact hidden-gap path integration; two independent questions |

The structural-inversion author trained class models and used posterior expected copy count as a
continuous exposure where the evaluation contract required direct continuous calibration. The
TXR1 author used an unadjusted molecular-fraction/local-copy gate and conditioned missingness and
outcome models on a post-treatment endpoint. The CRISPRi/CasRx author restricted the primary local
model to nominal focal rows, subtracted an external transcript contribution, and fitted one
remaining axis without the evaluation model's guide-level nuisance structure. The recent-pulse
author used a gap-aware called-path likelihood rather than full map exposure.

The population-genetics author also failed to harmonize one chromosome's reversed binary ancestry
labels. That error drives the wrong ancestry fractions and remains absent from automatic coverage;
it requires a future bounded data/model adapter rather than an unsafe claim from missing report
wording.

## Replay identities

| Case | Audit | Semantic lock |
|---|---|---|
| Structural inversion | `audit:d0f78757646e433d89b3e237a97496c4` | `sha256:1241e9948373a6cfe1935fae84562e5b60ce73a5cc1433fe327c9cbc322e273f` |
| TXR1 causal SV | `audit:7aa8de92f481412ea14d74be904b9431` | `sha256:4529b88b25a100c04aa07aa91e04349fb32b37e9e3f1aef55067795303b84306` |
| CRISPRi/CasRx | `audit:ff814cdcd8524eb2aed548ad4570af76` | `sha256:e9e2d42388740e9d3ee8c7b95c29d636620d0c14e49cf326ea0b38558eff34e4` |
| Recent-pulse ancestry | `audit:2753b0ec580f49f08639931098c09c46` | `sha256:c00f023d240b8d83d9bb22fbf5601ccd9dbac024c4bc05ae8f89e9543b6251c5` |

## External-contract comparison replays

One exact observed operand per case was compared with the independently supplied public evaluation
requirement. Each replay produced one `exact_conflict_candidate` Disclosure titled “One exact
review-scoped method incompatibility” and zero Findings.

| Case | Audit | Semantic lock |
|---|---|---|
| Structural inversion | `audit:144025a2a76941ac949e0dde71324719` | `sha256:6306ecceae939e332e1f77fa794bc2bc205047d66c38d8825d03ede3f0b0ff80` |
| TXR1 causal SV | `audit:a62f87f6727e4b4fbac68d133d410fc4` | `sha256:97fa8b2b66119f5ebe5962fd5e9b6c6f08f3d84ea9c6c68488bf07f3e1c98d42` |
| CRISPRi/CasRx | `audit:029a76bf076442789a111d7249239de9` | `sha256:efe682c9960fb32f04d26089cf173e590a80531b80f42ef78eceba58cb7f170b` |
| Recent-pulse ancestry | `audit:b738b89043394ffa89ff0bbdcd4992a4` | `sha256:8760690d7b3e9e898c90a612694d9d13c6c2daf9090488ca3510d09a8281f8ac` |

The ambient-state case from wave 1 was also replayed against its external adjustment-set
requirement: `audit:d16c5f30e1af45d5a28dbc7a3f758acc`, semantic lock
`sha256:b487572a02f09bab9c9005ff8785232887e0e80b5fa2318e54f8a1cc5b42b50e`.

## Interpretation

Across both waves, all eight grade-mismatching workflows now produce at least one relevant method
question. Five produce an exact evaluation-only incompatibility after external authority is added.
One of two within-contract controls also produces a relevant unresolved question. These are useful
recognition and comparison results, but they are not Findings, sensitivity/specificity estimates,
or evidence of generalization beyond this public development corpus.

The next work should keep two lanes separate: build the missing group-label data/model adapter for
this cold case, and proceed with the already planned domain-neutral dependence/pseudoreplication
vertical using independent non-benchmark qualification material.
