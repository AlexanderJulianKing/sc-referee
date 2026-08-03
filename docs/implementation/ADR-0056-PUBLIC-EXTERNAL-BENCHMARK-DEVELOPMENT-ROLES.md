# ADR-0056: Separate public benchmark roles from detector authority

- **Status:** Accepted under the owner's standing authorization for non-escalating architecture
  decisions
- **Date:** 2026-08-02
- **Related decisions:** ADR-0018, ADR-0019, ADR-0020, ADR-0042, ADR-0044
- **Related backlog item:** L11
- **Coordinated schema release:** None; retain public schema 0.18.0
- **Finding impact:** None; public benchmark cases remain Finding- and qualification-ineligible
- **Execution impact:** None; this decision does not authorize production or evaluation execution

## Context

The ten public GeneBench-Pro problems have all contributed to capability development and therefore
cannot be represented as held-out evidence. Public alternatives have different strengths:

- ScienceAgentBench supplies 102 expert-validated scientific programming tasks from 44 papers,
  standardized program outputs, and a verified public task split. Its gold and evaluation archive
  is separately distributed and must not be redistributed. Passing its evaluator establishes task
  completion, not that every scientific choice in the program is justified.
- BLADE supplies openly licensed research questions, datasets, and expert analysis-decision
  annotations. It intentionally admits multiple reasonable analyses, includes unresolved choices,
  and uses model-assisted matching in its official evaluator. Its annotations cannot be converted
  into a single universal right method.
- DiscoveryBench focuses on hypotheses and abstract workflows rather than inspectable scientific
  code repositories.

No public benchmark inspected supplies all of: answer isolation, deterministic method-level gold,
independent qualification eligibility, ordinary repository form, and unrestricted redistribution.
The implementation must use each source only for the role its evidence supports.

## Decision

1. Use public external benchmarks only as **development recurrence sources**. They may reveal a
   repeated connectivity gap, adapter gap, unsupported representation, or candidate atomic
   scientific choice.
2. Keep the workflow-authoring packet answer-isolated. Gold programs, scoring code, annotations,
   evaluator outputs, and prior sc-referee results stay outside the author workspace.
3. Pin every source by repository or dataset revision, preserve license and provenance, and label
   every retained case `benchmark_derived`, `answer_side` where applicable, and
   `qualification_status: excluded`.
4. Do not treat benchmark success, a gold program, model agreement, or numerical agreement as
   scientific-method authority by itself. A premise may use an explicit task requirement or a
   closed expert annotation only when the wording directly establishes that exact premise and no
   benchmark record marks the choice unresolved or admits the observed alternative.
5. Require independent recurrence before production code is broadened. A one-case observation
   remains evaluation-only. Recurrent candidates must still pass the full L11 positive,
   corrected, reverse, ambiguous, unsupported, sibling-isolation, mutation, no-execution, and
   replay pack.
6. ScienceAgentBench task 70 is the first candidate recurrence case because its public task packet
   explicitly requires separating donor effects in a single-cell VAE analysis. Three fresh
   authoring runs receive the task packet but no answer-side material. They author repositories but
   do not execute them. Their frozen outputs are audited after the fact.
7. BLADE remains a secondary source of diverse analysis representations and hard negatives. Its
   expert alternatives may test abstention, but the public annotations do not establish that an
   unlisted method is wrong.
8. These cases cannot qualify a detector, support a held-out accuracy number, authorize a Finding,
   or justify a domain-wide capability claim. Those gates remain unchanged.

## Alternatives rejected

### Call a new public benchmark held out

Rejected because the tasks and often their solutions are public, and the development team selects
cases after inspecting benchmark metadata.

### Use official benchmark pass/fail as scientific authority

Rejected because output fidelity and scientific-method validity are different claims.

### Encode every expert-listed alternative as mandatory

Rejected because BLADE deliberately represents a multiverse of reasonable decisions, including
explicitly uncertain ones.

### Wait for an unavailable private benchmark before continuing

Rejected because public benchmark recurrence can safely improve development coverage when its
ceiling is explicit.

## Acceptance evidence required

- exact source revisions and license terms are recorded;
- author workspaces contain no answer-side files;
- three independent task-70 workflows are frozen before audit;
- every audit remains non-executing and produces no Finding;
- any implementation proposal classifies the repeated miss before changing code; and
- all public documentation preserves the development-only ceiling.

## Remaining limitations

Public benchmark cases are contamination-prone and cannot replace an authenticated, answer-blind,
cross-provider qualification panel. ScienceAgentBench's independently distributed benchmark
archive is local-use only under its stated redistribution restriction. This decision does not make
the benchmark's gold program a universal scientific method or extend sc-referee beyond exact
tested adapters.
