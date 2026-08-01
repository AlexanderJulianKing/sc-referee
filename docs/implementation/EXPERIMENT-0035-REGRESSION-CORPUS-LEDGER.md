# Experiment 0035: Versioned regression-corpus ledger

## Question

Can sc-referee freeze the development evidence that currently exercises every active scientific
and calculation-check module, detect inventory or source drift, and prevent answer-visible or
benchmark-derived cases from silently becoming qualification evidence?

## Scope

This experiment adds an evaluation-only inventory and validator. It changes no public schema,
record meaning, scientific check, calculation check, assessment authority, Finding admission rule,
or project-execution privilege.

The versioned ledger records:

- the exact version and manifest digest of every active scientific and calculation-check module;
- each retained source's local content/tree digest or immutable external revision contract;
- the exact pytest function or retained-tree path that identifies a case;
- expected applicability and the maximum permitted public assessment type; and
- explicit answer-side, benchmark-derived, and qualification-exclusion labels.

The validator reads test modules with Python's syntax tree only. It does not import test modules,
run retained workflows, invoke a model, or treat the ledger as scientific authority.

## Acceptance criteria

1. Every active scientific-check and calculation-check module is present at its exact registry
   version and manifest digest.
2. Every active module maps to at least one retained case, and every retained source maps back to a
   case.
3. Local sources resolve without traversal or symlinks and match exact file or deterministic tree
   digests; external sources require HTTPS, a full Git commit revision, and a payload digest.
4. Case and source IDs are unique, pytest selectors exist, and all references resolve.
5. Scientific cases cannot exceed `material_question`; calculation cases cannot exceed
   `disclosure`; mixed-authority cases are rejected.
6. The ledger, every source, and every case are development-only and qualification-excluded.
7. The ledger is canonical JSON, self-digested, checked in CI, and checked by the complete handoff
   verifier.

## Tests added

`tests/test_regression_corpus_ledger.py` covers the accepted ledger, exact live-registry coverage,
duplicate identities, unused sources, noncanonical JSON, ledger and manifest drift, missing module
coverage, qualification leakage at all three levels, traversal, local source mutation, missing
pytest selectors, immutable external revisions, retained-tree byte and symlink mutation, Finding
ceilings, and mixed scientific/calculation authority.

## Result

The v1 ledger binds 26 active modules to 29 retained cases across nine sources. All sources and
cases are explicitly excluded from qualification. The focused ledger tests and all 1,232 repository
tests pass. Ruff, format checking, strict mypy for 105 production and 26 evaluation source files,
the 79 public schema examples, the walking skeleton, and the standalone ledger validator pass.

## Remaining limitations

- Inventory coverage does not establish scientific representativeness, independent validation,
  detector qualification, or Finding authority.
- Most current entries identify pytest-generated fixtures rather than independently materialized
  repositories.
- L02 must run the declared local cases through one semantic comparison command; L03 must fill
  every mandatory regression role for every active module.
- An immutable external revision proves source identity only when its payload is separately
  materialized and digest-verified; this ledger performs no network retrieval.
