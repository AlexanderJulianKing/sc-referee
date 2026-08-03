# Experiment 0048: ScienceAgentBench local DTI-input recurrence

- **Status:** Completed bounded development loop
- **Date:** 2026-08-02
- **Decision:** Accepted ADR-0056 under the owner's standing authorization
- **Schema:** Unchanged at `0.18.0`
- **Backlog item:** L11
- **Corpus ceiling:** Public development; neither held-out, qualification-eligible, nor
  promotion-eligible

## Question

When fresh coding agents implement the independently published DAVIS drug-target-interaction task,
do they repeatedly substitute a packaged or remote dataset loader for the task's listed local
train/validation files, misalign drugs, targets, and affinity matrices, or emit the wrong ranked
identity? If a miss recurs, can it be classified before any production code changes?

## Why this task

The official ScienceAgentBench paper documents a Claude 3.5 Sonnet failure on verified task 12:
with expert knowledge, the generated workflow used an automatic DAVIS loader that did not read the
benchmark's modified local dataset correctly. Without expert knowledge, it used an overly simple
representation. The paper's published case establishes that this is a real agent failure mode, but
it does not make either historical generated program a production label for a new run.

## Frozen source

- ScienceAgentBench repository revision:
  `c26e151ed601ba109dc4d35e057ff8e73fec469d`
- verified Hugging Face dataset revision:
  `9c6e96c9e74572e979b0930ee735041cef528cb7`
- task: verified instance 12, Bioinformatics
- author packet: `evaluation/scienceagentbench-public-v1/task-0012/agent-task.md`

The author packet contains no gold program, evaluator, expected output, case-study program, prior
workflow, prior audit, or answer-side annotation.

## Procedure

1. Materialize separate temporary workspaces from the author packet.
2. Give each fresh agent only its workspace and ask it to author, but not run, the workflow.
3. Freeze each repository before audit.
4. Audit each repository after the fact without project-code execution.
5. Record exact local-input use, affinity-matrix alignment, scale declaration, ranking identity,
   and the audit's recognized or unsupported evidence.
6. Require independent recurrence before proposing an adapter or check.

## Acceptance criterion targeted

This experiment targets L11 recurrence on a failure family already documented by an independent
benchmark, while preserving answer isolation and a zero-Finding ceiling.

## Result

Three independent fresh authoring attempts produced the same boundary mistake: each joined every
nonempty or non-FASTA-header line of the task's named two-line record into one sequence value. Two
programs were materialized and frozen with exact digests; the third returned a matching complete
draft but its authoring transport did not materialize the file, so that draft is supporting
recurrence evidence rather than a retained regression artifact.

| Run | Role | `analysis.py` digest | Audit evidence |
| --- | --- | --- | --- |
| B | recurrent adverse author | `sha256:c931a219a99f93104a4d8ee288fd3b1888f933b4b62126f178d21c81abd059e8` | audit `audit:d507f5c31035406d99f37024815b1b68`; semantic lock `sha256:d7e2d11242341f9fe89aa730cc8808ed881faa334663e35e059687601de80152`; 0 Findings, 20 Disclosures, 0 deterministic observations |
| C | recurrent adverse author | `sha256:230520310bb767ee803f2c3bedfe31084e66bb5f54371a05b08b1d3ac7c0be7e` | audit `audit:2de47c0aad184ed1b32c7d5fc945b263`; semantic lock `sha256:727f55daf82539bc385d3b703b77da418ce2c659628ce86a83cd478522962a31`; 0 Findings, 20 Disclosures, 0 deterministic observations |
| A | fresh corrected control | `sha256:c46d04e92f365c50df947cc1ed9d557df5699b6eefd37f443226499b43e74e60` | selected line 1 as sequence, retained line 2 as label, and was not executed |

The original audits had no selected copy of the separately distributed input and predated the new
check, so they correctly made no boundary claim. The recurrence was classified as a new atomic,
static record-consumption check rather than a benchmark-specific adapter or a general biological
judgment.

Accepted ADR-0057 adds
`calculation-check:selected-sequence-record-boundary-v1` in calculation profile v12. It requires
an exact selected two-line record, a unique inert Python AST join, and a closed exact path flow from
that record to the read. The output is a Disclosure only. Benchmark names, answer-side files,
model judgment, project execution, and downstream predictions are absent from the grammar.

The mandatory controls cover the recurrent direct and single-call path forms, corrected first-line
selection, all-sequence and FASTA-header second lines, wrong and decoy paths, additional line
validation, unresolved parent directories, reassigned names, unreturned parser defaults, ambiguity,
unsupported syntax, module removal and sibling isolation, source-identity mutation, an execution
trap, no late model access, deterministic replay, and canonical v12 manifest verification.

## Acceptance criterion satisfied

The same exact boundary failure recurred across independent fresh authors before implementation,
the repair was separately authored, the miss was classified before coding, and the resulting check
uses a general byte-and-AST contract with the full L11 control ceiling. It adds no Finding authority
and does not treat benchmark output scoring as scientific authority.

## Remaining limitation

The benchmark is public, the experiment did not execute the generated workflows, and the task's
official pass/fail evaluator is not scientific-method authority. The benchmark's actual two-line
record and gold package are not redistributed. The static check does not prove runtime use,
downstream impact, scientific correctness, broad sequence-format support, detector qualification,
or Finding eligibility. Its initial path-flow grammar deliberately abstains on dynamic or
multi-call source.
