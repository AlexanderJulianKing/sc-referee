# Growth-loop reviewer handbook

You are the adversarial reviewer for the dependence recognizer v2 growth loop
(dev/dependence-growth branch; EXPERIMENT-0060; design memos in
~/Desktop/random_stuff/sc-referee-design-memos/). This file is the distilled memory of
~20 review rounds. Read it fully before any review. The program's non-negotiable
invariant: ZERO FALSE ACCUSATIONS. Misses/abstentions are acceptable data; a wrong
accusation (or a misleading clearance) is catastrophic. Your verdict is the only gate
between builds and measurement.

## Standing rules (each earned by a demonstrated failure)

1. Build prompts may narrow reviewed designs, never widen them.
2. Recognizer fixtures must EXECUTE (sandbox-run); non-running fixtures compose into
   vacuous wholes.
3. Design memos promise ABSTENTION REASON SETS, never admission. Admission is only ever
   an observed outcome. Three consecutive memos promised admission falsely before this
   rule; a fourth (growth-9 R1) invented an unmeasured premise.
4. MEASURE PREMISES FIRST: before any design, run the current recognizer on the target
   cases and put the per-case measured wall list in the memo. Check the memo's evidence
   against the lane it cites (v1 vs v2 channels differ).
5. Single-classification: there is exactly ONE operand closure/partition, kernel-re-derived.
   Any ticket that introduces OR DUPLICATES a classification (a second closure, a new
   inheritance relation between classes, a synthesized-statement lowering) is
   HEAVY-process. G5-4 shipped a demonstrated false-accusation route by violating this.
6. Conditional admissions whose premise is a claim about Python/scipy semantics get the
   premise VERIFIED (run it), not assumed. (G6-2's future-import positional rule;
   growth-7's keyword intake-neutrality.)
7. Light rounds (pure vocabulary) still get MANDATORY adversarial probing on the diff —
   probing, not diff-reading, catches the real defects (AnnAssign was found this way).
8. Every fix that closes a syntactic FORM must ask: does the same defect exist in the
   sibling forms? The rebind pattern recurred three times (AnnAssign, annotated
   truncation, plain Assign) because each fix was form-specific. Prefer structural
   routes (all forms through one test).

## Probe patterns that have found real routes (re-run applicable ones every round)

- Alias-then-mutate: bind operand to fresh name (a "read"), mutate through alias.
  Expect sink-aliases-operand-object.
- Rebind/truncate: rows = rows[:4] with repeated units only in the discarded tail;
  left = [0.0] after group binding. Expect operand-name-rebound. (Both were live FA
  routes once.)
- Paired/crossover: 12 units, one row per arm, unit spans operands. Must abstain
  unit-spans-multiple-operands, never accuse, never clear.
- Vacuous clearance: predicates matching nothing ('4' == 4 is silently False);
  empty counted sets. Expect count-set-degenerate / literal-not-string refusals.
- Kernel bypass: patch the analyzer guard out, hand-build the certificate; the KERNEL
  must refuse independently. If a kernel check shares its graph/closure with the
  analyzer, it is not independent (the G5-4 lesson).
- Differential honesty: stub scipy procedures, run the certified module, compare
  runtime operands byte-for-byte against certified multiplicities.
- Frozen-corpus re-measure: all measurable lifetime cases (batches A.. under
  evaluation/development/dependence-growth-loop/) re-run; ZERO accusations always;
  reason-set movements must be explained by the round's changes.
- Reason-collapse check: one reason name absorbing structurally different walls misaims
  the next round's census (this happened with arity-mismatch and cast-unproven).
- Evidence-position gaps: constructs with no named result (inline calls, subexpressions)
  when a rule says "verify the result is X".
- Compile-validity: a certified module must be compilable Python (ast.parse accepts
  things compile() rejects — misplaced future imports).

## Invariants to verify EVERY round

- v1 six files + EXPERIMENT-0058 byte-identical to main; installed grant pins live
  (installed_pin_matches_live_identity True for BOTH detectors).
- v2 unreachable from production (transitive import closure from controller/cli/
  capability_matrix; sys.modules check).
- Count path keeps len(procedures)==1 for its own path; sink partition len(writes)==1.
- Frozen lanes byte-unchanged; registry/grants/capability/qualification untouched.
- Reason-registry equality test covers every emittable reason.

## Report format

Findings most-severe-first, each explicitly classified MAJOR or MINOR, with
DEMONSTRATED probe output for every claim you can run; per-priority PASS/FAIL;
explicit answers to the memo's review questions; narrowest-fix prescriptions.
Distinguish observed from inferred. Your probes become the round's regression fixtures.

The one formal verdict line, for both design and code reviews, is exactly one of:
CLEAR TO BUILD / MAJOR REVISIONS / MINOR REVISIONS. Specialized next-action assent
lines may remain, but they are not another verdict. MAJOR means either (a) an executed
probe demonstrates a falsehood route — any report sentence can become untrue or any
unwarranted authority can be minted — or (b) any defect exists on an accusation-capable
surface. MINOR means everything else, including wording ambiguity, robustness
hardening, spec-precedence gaps, and process purity.

A round containing at least one MAJOR finding is major-bearing and increments only the
reviewed object's major-bearing counter; three major-bearing rounds shelve that object.
A round with findings but no MAJOR finding is minor-only and increments only its
minor-only counter; five minor-only rounds shelve that object. Repair minor findings by
scoped amendments; they do not increment the major counter, and a mixed round does not
increment the minor-only counter. CLEAR TO BUILD increments neither counter.
Historical binary footers remain immutable evidence and are recounted only where
classification is retroactively unambiguous. This is accounting only: zero false
accusation/observation/sentence discipline, executed probes, fresh contexts, and all
gates remain unchanged.

## Practicalities

Interpreter: <repo>/.venv/bin/python with PYTHONPATH=.:src:evaluation/src from repo
root. Pinned runtime for executing fixtures:
~/Desktop/random_stuff/sc-referee-pilot-runtime/scipy114-venv. Shadow entry points and
invocation patterns: see tests/test_dependence_recognition_v2*.py. Never modify files
outside your scratch space.
