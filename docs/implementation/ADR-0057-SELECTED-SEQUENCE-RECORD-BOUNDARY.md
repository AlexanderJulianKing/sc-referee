# ADR-0057: Add a bounded selected sequence-record boundary check

- **Status:** Accepted under the owner's standing authorization for non-escalating architecture
  decisions
- **Date:** 2026-08-02
- **Related decisions:** ADR-0017, ADR-0044, ADR-0056
- **Related backlog item:** L11
- **Coordinated schema release:** None; retain public schema 0.18.0
- **Finding impact:** None; the new check is Disclosure-only
- **Execution impact:** None; selected Python is parsed as inert AST and never imported or run

## Context

Experiment 0048 observed the same input-boundary mistake in independently authored workflows: a
two-line text record contained an amino-acid-alphabet-only value followed by a human-readable label,
while the Python parser joined every nonempty or non-FASTA-header line into one sequence value. A
fresh corrected author selected the first line and retained the second as a label.

This recurrence is narrower than a scientific-method disagreement. The relevant facts can be
checked from exact selected bytes and a closed Python AST shape. No benchmark answer, model
judgment, execution, downstream prediction, or biological-effect claim is needed.

## Decision

1. Add `calculation-check:selected-sequence-record-boundary-v1` as a ninth deterministic
   calculation-check family in registry profile v12. Its ceiling is `disclosure_only`, and
   `production_finding_permitted` remains false.
2. Inspect only exact scientist-selected, full-digest material inputs. The record must be strict
   UTF-8 under 64 KiB with exactly two nonempty, already-trimmed lines. Line 1 must contain 20 to
   10,000 characters from the closed amino-acid alphabet. Line 2 must be at most 256 characters,
   contain alphabetic text and at least one character outside that alphabet, and not begin with a
   FASTA header marker.
3. Parse selected `.py` source with the standard-library AST without importing or executing it.
   Recognize only one empty-string join over one list/generator comprehension fed by
   `read_text(...).splitlines()`. The element may be the line, `strip()`, or `upper()`. Filters may
   retain nonempty lines and/or exclude FASTA headers, but may not contain an additional validator.
4. Require an exact path flow from the selected record into that read. The initial grammar accepts
   a direct/assigned `Path` literal or one uniquely called function whose matching argument is
   bound by an exact `argparse` default or constructor field. A filename literal elsewhere in the
   source is insufficient. Every path fragment and single-call parameter substitution must resolve;
   unresolved parents, repeated assignments, and parser defaults not returned by that parser
   abstain.
5. Multiple record/parser pairs or join shapes produce an ambiguous observation with no operands.
   A unique selected Python parse failure produces an unsupported observation. Dynamic dispatch,
   multiple calls, unbound attributes, structured formats, other languages, and out-of-budget
   inputs abstain.
6. The adverse observation states only that the uniquely path-bound static parser includes line 2
   in its constructed value. It does not claim execution, runtime selection, downstream model use,
   numerical impact, scientific incorrectness, or publication use.
7. Bind the exact record lines and join span into source references, record finite receipts and
   limitations, preserve semantic-lock replay, and publish a content-addressed immutable v12
   manifest. Schema v0.18.0 and prior manifest releases remain unchanged.

## Alternatives rejected

### Key on the benchmark filename or task identity

Rejected because the issue is a general record-boundary shape. Benchmark names, paths, answers,
and model outputs are not part of the check identity or recognition grammar.

### Treat any sequence-alphabet line followed by prose as an issue

Rejected because file contents alone do not show how a program consumes them. Exact selected
source, a closed join shape, and exact path flow are all required.

### Infer that the workflow ran or its result is invalid

Rejected because static source does not establish execution or downstream use. The strongest
permitted output is a non-accusatory Disclosure of the exact constructed-value boundary.

## Acceptance evidence required

- recurrent join forms and direct, `argparse`, and constructor-field path bindings are recognized;
- a first-line-only repair, all-sequence second line, FASTA header, wrong-path literal, unresolved
  parent, reassigned name, unreturned parser default, additional validation, dynamic form, and
  over-broad source association do not produce the adverse state;
- multiple consumers remain ambiguous and parse failure is localized as unsupported;
- module removal changes no sibling calculation observation;
- a project-code execution trap remains untouched and the semantic lock records no late model
  access;
- exact observations, Disclosures, Findings, and coverage replay; and
- the v12 manifest is canonical, packaged, and denies Finding permission.

## Remaining limitations

The alphabet-and-shape test is not a general sequence-file validator and does not establish that a
line is biologically meaningful. The initial path-flow grammar is deliberately small. Wrapped
records, FASTA/FASTQ, JSON, tabular formats, helper indirection, class methods, multiple call sites,
other languages, runtime provenance, and downstream effect remain unsupported. Public benchmark
development evidence and synthetic controls cannot qualify this check or grant Finding authority.
