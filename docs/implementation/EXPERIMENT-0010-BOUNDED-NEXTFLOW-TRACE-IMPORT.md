# Experiment 0010: Bounded default Nextflow trace import

- **Status:** Active local implementation profile; imported evidence only
- **Date:** 2026-07-29
- **Authority:** SA-FR-016, SA-FR-049, specification sections 6.13 and 6.16, and accepted ADR-0017
- **Scope:** Terminal task rows in a fully captured root `trace.txt` with the exact default
  Nextflow trace header
- **External profile reference:** [Nextflow trace-file documentation](https://docs.seqera.io/nextflow/reports#trace-file)

## Purpose

Admit one naturally produced workflow trace as bounded execution evidence without running project
code, treating repository text as authorization, or converting a self-reported task row into an
observed runtime fact. This is the first HPC/workflow evidence profile, not a general workflow-log
parser.

## Exact profile

The inspector considers only a root regular file named `trace.txt`. It operates only on a complete
immutable payload already admitted under `full_digest` identity and rehashes the materialized
payload before parsing. Strict UTF-8 and the exact 14-column default tab-delimited Nextflow header
are required.

The profile reads at most 2,000,000 bytes, inspects at most 4,096 task rows, retains at most 128
opaque-row boundaries, and accepts at most 4,096 characters in one field. Only internally
consistent terminal rows are promoted:

- `COMPLETED` with integer exit code `0`; or
- `FAILED` with a nonzero integer exit code.

Malformed, nonterminal, contradictory, over-field, or over-row records fail locally. A wrong
header, non-UTF-8 body, over-byte file, weak or missing identity, or changed captured payload emits
no Execution.

## Evidence meaning

Each admitted row emits an `Execution` with `execution_kind: imported`, `actor: external_import`,
`identity_strength: imported_weak`, and `authorization_evidence_status: imported`. The row source
span and full trace digest are retained. The matching imported Environment establishes only that
the exact default header identifies a Nextflow trace profile; runtime version, platform,
dependencies, containers, modules, and scheduler state remain unknown.

The task name is recorded only as a task label because the default trace does not capture the
command or script. Timing remains unavailable because the default fields do not supply both task
start and finish timestamps. Input and output references remain empty because the default trace
does not establish repository path lineage.

The imported record asserts that project code executed according to the repository-supplied trace,
but it is not controller-observed execution or independent authentication. It is not connected to
Claim lineage, a Finding premise, clean-control evidence, output correctness, or qualification
merely because the row is structurally valid.

## Exit evidence

- a valid completed and failed row each emits a schema-valid weak imported Execution;
- nonterminal and malformed rows remain localized opaque boundaries while valid rows survive;
- wrong-header, over-byte, and post-capture mutation cases emit no Execution;
- an end-to-end audit proves project-authored Nextflow source is not executed and the imported row
  does not enter Claim lineage or produce a Finding;
- model-free replay reproduces the parser, Execution, Environment, Claim, and coverage records; and
- the generated capability matrix discloses the exact profile with no detector, qualification,
  tested-version, inferred-compatibility, authenticity, or domain-wide support claim.

## Remaining coverage limitation

Custom Nextflow trace filenames, configured field sets, execution reports, histories, scheduler
logs, task scripts, work directories, retries, cached tasks, nonterminal tasks, workflow-level
status, input/output provenance, and all non-Nextflow workflow systems are unsupported. The profile
has not been independently qualified against a real external corpus.
