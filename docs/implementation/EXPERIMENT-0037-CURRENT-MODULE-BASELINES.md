# Experiment 0037: Complete current-module regression baselines

## Question

Can every active scientific-question and deterministic calculation module be bound to a complete,
machine-checked development baseline without inventing a scientifically preferred answer for
question-only modules or promoting development fixtures into qualification evidence?

## Scope

This experiment completes post-MPP backlog item L03. It changes answer-side development machinery
and focused regression tests only. It changes no public schema, record meaning, detector authority,
Finding admission rule, scientific-check output ceiling, calculation-check output ceiling, model
privilege, or project-execution privilege.

The baseline projection is generated from the active registry inventory and the canonical
regression ledger. Calculation modules require a positive/applicable case, corrected or conformant
twin, hard negative, ambiguity or unsupported boundary, removal and sibling-isolation check, and
semantic replay. Question-only scientific modules require an applicable question case, matching
close negative, ambiguity or unsupported boundary, removal and sibling-isolation check, and
semantic replay. They do not require an invented “correct” scientific answer.

Existing focused tests remain the executable evidence. The ledger references those tests by exact
source digest and selector, and the one-command runner derives its pytest selection from the ledger.
The new baseline validator runs before the corpus, so losing one required role fails the product
gate before any direct audit begins.

## Acceptance criteria

1. Every one of the 26 active modules satisfies its kind-specific mandatory baseline.
2. Removing any required role from any single module produces one exact, named completeness gap.
3. The question-only policy requires matching and unresolved controls without representing either
   as an authorized scientific answer.
4. Every positive calculation selector performs an actual semantic-lock replay comparison.
5. Every scientific module has executable hard-negative, ambiguity/unsupported, removal-isolation,
   and replay coverage; every calculation module has the corresponding controls plus a corrected
   or conformant twin.
6. The one-command corpus continues to execute no retained project-authored code, create no
   qualification evidence, admit no Findings, and make no model calls.

## Tests added or strengthened

`tests/test_regression_module_baselines.py` generates the completeness assertion over the current
registry and corpus. It independently removes every required role from every module and verifies
the exact reported gap, locks the distinct question-only policy, and rejects unknown component
references and kinds.

Focused calculation tests now compare their positive audit with a real replay. The eQTL family adds
an unrelated descriptive donor plot as a hard negative. Scientific-check integration adds explicit
founder-orientation and MVMR boundaries and close negatives, an unrelated expected-count report,
generic per-module removal with sibling isolation, and an actual full-registry replay comparison.

The canonical development ledger now contains 103 cases: 99 pytest-backed declarations through 67
unique selectors and four directly audited repository controls. The extra ledger declarations map
the already focused controls to their exact module roles rather than duplicating their fixtures.

## Result

The generated projection reports all 26 active modules complete. The focused ledger, baseline, and
runner suites pass, and a real one-command corpus run passes all 99 pytest-backed case declarations
through 67 selectors plus four direct audits and exact replays. The run records zero target-project
executions, zero Findings, zero model calls, and no post-lock model access.

## Remaining limitations

- These are answer-visible, qualification-excluded development controls. Completeness of the role
  matrix does not establish scientific representativeness or detector validity.
- Most controls remain pytest fixtures rather than independently authored natural repositories.
- A single focused test can support more than one module or role only when its assertions actually
  exercise each mapped behavior; the ledger is an index, not a substitute for those assertions.
- Counterevidence, mutation, no-execution, and independent false-positive controls remain mandatory
  for future material changes even though L03's current-module acceptance names the six baseline
  classes enforced here.
- L04 and L05 must still make ordinary report, source, input, output, and cell selection and scope
  connectivity reusable across repositories.
