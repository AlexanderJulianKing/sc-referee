# Experiment 0047: ScienceAgentBench donor-adjustment recurrence

- **Status:** Completed; no adverse recurrence observed
- **Date:** 2026-08-02
- **Decision:** Accepted ADR-0056 under the owner's standing authorization
- **Schema:** Unchanged at `0.18.0`
- **Backlog item:** L11
- **Corpus ceiling:** Public development; neither held-out, qualification-eligible, nor
  promotion-eligible

## Question

When three fresh coding agents implement the same independently published single-cell task without
answer-side access, does omission of the task's explicit donor-separation requirement recur? If it
does, can the miss be classified as a connectivity gap, adapter gap, new atomic scientific choice,
unsupported representation, or absent governing authority before any production code changes?

## Frozen source

- ScienceAgentBench repository revision:
  `c26e151ed601ba109dc4d35e057ff8e73fec469d`
- verified Hugging Face dataset revision:
  `9c6e96c9e74572e979b0930ee735041cef528cb7`
- task: verified instance 70, Bioinformatics
- author packet: `evaluation/scienceagentbench-public-v1/task-0070/agent-task.md`

The author packet contains the public task, public domain knowledge, input path, and deliverable
shape. It contains no gold program, evaluator, expected output, prior workflow, prior audit, or
answer-side annotation.

## Procedure

1. Materialize three separate temporary workspaces from the same author packet.
2. Give each fresh agent only its workspace and ask it to author, but not run, the workflow.
3. Freeze each authored repository before any audit.
4. Audit each frozen repository after the fact with the scientific-audit skill and no project-code
   execution.
5. Record whether donor separation is explicitly implemented, explicitly omitted, ambiguous, or
   unsupported and whether sc-referee recognized the relevant evidence.
6. Require independent recurrence before proposing any adapter or scientific-check change.

## Tests required if recurrence justifies implementation

- the recurrent positive representation;
- a corrected donor-covariate twin;
- a reverse control where the named column is not a donor or grouping unit;
- an ambiguous case with unresolved donor identity;
- an unsupported dynamic-call case;
- sibling-module removal and isolation;
- source/task identity mutation;
- no project execution and no post-lock model access; and
- deterministic replay.

## Acceptance criterion targeted

This experiment targets L11's recurrence-before-coding rule on a public external task, with exact
answer isolation and an explicit classification of every miss.

## Result

All three independently authored workflows explicitly implemented donor adjustment. Each bound a
donor metadata column, preserved raw counts for SCVI, and passed the donor key through SCVI setup;
the implementations differed in their exact use of `batch_key`, categorical covariates, and
differential-expression batch correction. No project code was executed.

| Run | `analysis.py` digest | Audit ID | Semantic lock | Assessments |
| --- | --- | --- | --- | --- |
| A | `sha256:3225f4aff223d71eb31669eca34bb1565e3fb15abddf555ca767fca68b29e94b` | `audit:651ce899cc344cccb4b2e29143f151f8` | `sha256:8d78322f13759123e12c03d0eac8a90ce5761c9fbb6c60b3c3491445049762ae` | 0 Findings, 0 ConditionalConcerns, 0 questions, 20 Disclosures |
| B | `sha256:69324c26d47f2d9e12cae81e4917a84fb7ac87635436481e5f144075e6293e1b` | `audit:09db4c45845c4342a04faef0784089ef` | `sha256:c933dbbbbd53849fa81071ec642e6ad535afd4582a9328470ff9a307b1ae07c0` | 0 Findings, 0 ConditionalConcerns, 0 questions, 20 Disclosures |
| C | `sha256:2be86bc7df62faf88eaaa5b4d55b673b8ff5ce60c094fe41a03850cdd85d9f66` | `audit:ea4448ccb96740fbb45eeebd66af6edb` | `sha256:8901aaf0b863e9e9fe127c40f91af91413017bd0eb6ce91562c7dc2acc321364` | 0 Findings, 0 ConditionalConcerns, 0 questions, 20 Disclosures |

Every integrity check passed. Every audit resolved `REPORT.md`, recorded zero model calls, preserved
`model_access_after_lock: false`, and ended `partial_evidence_unavailable`. The common known gaps
were incomplete ScientificContract/claim binding, no eligible production detector, unidentified
assets, and static Python opacity. The program therefore did not make a false accusation, but it
also did not recognize donor adjustment as a supported scientific-check family.

The experiment's bounded question had a negative answer: donor-adjustment omission did not recur.
Under L11, no detector or adapter is added. These three workflows are retained only as external
clean development controls for a future general donor/grouping module.

## Test added

`tests/test_scienceagentbench_public_packet.py` verifies the pinned source revisions, exact author
packet digests, answer-side exclusion, redistribution boundary, no-execution instruction, and
qualification exclusion.

## Acceptance criterion satisfied

The case demonstrates the recurrence-before-coding gate: three fresh workflows were frozen and
audited, the hypothesized miss did not recur, and production code remained unchanged.

## Remaining limitation

These workflows were not executed against the benchmark H5AD, and sc-referee did not positively
recognize their donor adjustment. They do not prove functional benchmark completion, prevalence,
detector qualification, universal single-cell practice, or Finding authority.
