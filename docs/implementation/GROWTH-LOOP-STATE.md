# Growth-loop living state (maintained by the orchestrator, every iteration)

Updated: 2026-08-16 (Growth-12/13 closed; Growth-14 pandas revival is maintainer-
authorized but queued after Growth-15; Growth-15 Option A passed its one authorized
resumed HEAVY design review and is cleared for a fresh build; no re-measure or batch
is authorized).

## Scoreboard

- 96 lifetime blind free-form cases (batches A-J under
  evaluation/development/dependence-growth-loop/), ZERO false accusations, zero
  regressions. 95 measurable (batch-D case dc2b31d5 was intake-refused, never
  materialized). No blind catch yet; misses are honest named abstentions.
- Six demonstrated false-accusation routes killed in review before measurement
  (filter-predicate, paired/crossover, alias-then-mutate, counted-domain, AnnAssign
  rebind, plain-Assign rebind). The plain-Assign fix is structural (operand-name-rebound,
  all assignment forms through one partition test).
- v1.1.0 qualified detector + installed pins: untouched and live throughout.
- Maintainer checkpoint trigger: every frozen re-measure now separately reports
  whether a planted positive reaches full development analysis and emits an adverse
  certificate. This is observation only and never rescoring. The first such event
  triggers prompt checkpoint batch K (both envelopes, normal gates). The current
  95-case refresh has 47 planted positives and `0/47` retroactive certifications, so
  batch K is not triggered yet.

## Closed this iteration

- Growth-9 G9-L + amended G9-H shipped on `dev/dependence-growth` through
  `4ca0532`: builtins dict/any/all/tuple, DictReader shallow-copy form,
  list-literal string constants, and positional argument-expression hoisting with
  the one partition reused and operand-container identity refused at binding time.
- Frozen A-I2 re-measure: 83 materialized cases, 29 reason-set movements, zero
  outcome-class movements, accusations `0 -> 0`. Both installed pins remained live;
  protected v1, EXPERIMENT-0058, registry/grants/pins/capability/qualification, and
  frozen lanes had zero changed paths.
- Fresh adversarial review demonstrated both subscript and bare-name analyzer-bypass
  proposals reach certificates and the kernel independently refuses each with
  `certificate-kernel-refusal:sink-partition`. Alias/mutation, all rebind sibling
  forms, paired/crossover, vacuous clearance, runtime operand equality,
  compile-validity, reason-registry, cardinality, production-unreachability, and
  pin-liveness probes passed. Final fresh reviewer verdict: `CLEAR FOR BATCHES`.
- Orchestrator full-suite gates reached 100% with verified `PYTEST_EXIT=0` before
  each accepted push. One intermediate gate failed only because the reviewed test
  changed before manifest regeneration; release identity and the repeated full gate
  passed after the manifest was rebuilt.
- First open wall-corpus census completed at
  `evaluation/development/wall-mining-corpus/run-40/`: 40 Haiku generations, cap 3,
  122/122 JSON files purpose-stamped `development_wall_mining`, no measurement
  authority. It is NOT useful for ranking: all 40 descriptions omitted the optional
  exact `Independent unit column:` declaration, all translations were `no-lock`, all
  outcomes were `question` / `independent-unit-definition-unresolved`, and the wall
  frequency map is empty. Do not infer a grammar priority from this run.
- Checkpoint J1 + J2 completed: 12 new blind cases, 12 opportunities, zero false
  accusations, zero catches. J1 outcomes were one `abstained_no_authority`, two
  `abstained_unsupported`, one `missed_no_authority`, and two
  `missed_unsupported`; J2 had two, one, two, and one respectively. Exact planted
  miss walls: J1 `module-constant-not-closed`, `import-use-outside-grammar`, and
  `function-return-shape`; J2 `import-use-outside-grammar`,
  `augmented-assignment-not-modeled`, and
  `count-predicate-not-closed;raise-guard-not-modeled`. Non-error abstention walls
  also included `unsupported-import-form`, module constants, and the combined
  function closure/globals/return/raise set. No rates were published.

- Growth-11 code review completed CLEAR FOR BATCHES with no findings (fresh codex-cli
  reviewer session 01a009fe, launched by the Fable escalation session during a ~3-hour
  overlord stall after the `f035bd9` push; `.git` was locked read-only for the session
  per the process-control record). Executed probes: shadowed/parameter/user-function
  `open` all abstained; alias-then-mutate and sink-position probes moved to existing
  specific walls; dynamic names stayed default-deny. Independent 40-case
  `run-40-authority-2` re-measure: 11 reason-set movements exactly matching the memo,
  zero outcome-class movements, zero accusations. Reason-registry equality, targeted
  Ruff/format, `mypy src` (159 files), starter validator, both pin-liveness checks,
  production import isolation, and the full suite (4055 passed, `PYTEST_EXIT=0`
  against the pristine `f035bd9` archive) all passed. Protected paths untouched.

- Growth-12 (heavy-queue item 0, intake declarations) design arc completed by the
  Fable escalation session during the continuing overlord stall, all steps via fresh
  codex-cli sessions with the repo read-only or `.git` locked: memo authored with
  measured premises (session 01a00a6c); round-1 review BLOCKED with an executed
  fail-open ("Ignore this bogus example. Independent unit column: plant_id" minted a
  lock) plus a v1/v2 lane conflation in the memo's own replay claims; v2 amendments
  appended (protocol-precedence rule with deterministic guards, total refusal
  precedence chain, lane-separated claims, versioned hostile-packet replay); round-2
  fresh review returned CLEAR TO BUILD with no findings and explicit
  PROTOCOL-PRECEDENCE: ASSENT. IMPORTANT PREMISE CORRECTION now on record: all 27
  measured dead cases contain the exact declaration string; the 21 batch deaths are
  procedure-stage in the v2 lane (9 ambiguous, 9 unavailable, 1 unresolved — the
  adapter's independent-unit-definition-unresolved is a no-v2-authority proxy, working
  as designed); only the six census cases are genuine declaration-layout misses, so
  this round's v2-lane yield is exactly six census translations and zero batch
  movements. Queue item 0's original aggregate premise is superseded by the memo §3.2.
  Consequence for ranking: procedure-stage walls now likely outrank intake; the
  paired-procedure go-ahead (queue item 1) covers part of the unavailable set.
  The round-2 reviewer flagged the hostile-packet replay seam at
  `lean_pipeline.py:2961-2973` for the builder.
- Growth-12 build and repair are complete through `7f822fc`. The initial build
  (`f4d1bac` + manifest `095d121`) was BLOCKED in code review after markdown-fenced
  declarations minted locks through both the terminal and legacy standalone routes,
  plus three narrower receipt/completeness/provenance blockers. Binding memo v3
  section 16 required a total triple-backtick presence refusal in both profiles,
  restored stripped-emptiness completeness checks without relaxing byte-exact
  matching, lane-local receipts, and complete versioned digest chains. A fresh fix
  builder implemented exactly those seven-file amendments; the orchestrator's full
  suite passed with verified `PYTEST_EXIT=0`, and the repair was committed as
  `45104f8` with manifest `7f822fc` and pushed.
- Fresh code reviewer session `01a00af7` reviewed exact clean HEAD `7f822fc` and
  returned `VERDICT: CLEAR FOR RE-MEASURE`, with no BLOCKER/MAJOR/MINOR findings and
  explicit `PROTOCOL-PRECEDENCE: ASSENT`. Executed probes covered 16 direct fence
  profile/placement combinations, five growth-loop end-to-end cases, both wall-census
  routes, semantic conflict/case-collision, whitespace completeness, lane receipts,
  provenance, retained hostile replay, 27/27 evidence descriptions and 7/7 legacy
  fixture modules marker-free, pins, production isolation, reason registry,
  cardinality, protected paths, targeted Ruff/mypy/starter validation, and a full
  `PYTEST_EXIT=0`. Protected/frozen changed paths were zero against both the round and
  repair bases.
- The gated scratch re-measure of immutable `run-40-authority-2` completed with
  `REMEASURE_EXIT=0`, no model calls, and no project-code execution. Exactly cases
  `0005`, `0011`, `0024`, `0026`, `0030`, and `0038` moved from `no-lock` to
  `lock-projected`; transport counts moved `33/7 -> 39/1`. Those six moved from
  authority `question` to honest named `unsupported` walls, so outcomes moved
  `34 unsupported + 6 question -> 40 unsupported`; accusations remained `0`.
  Seventeen reason sets differ from the immutable stored run: the six Growth-12
  transport gains plus the eleven already-reviewed Growth-11 `open` decompositions.
  The current 39-lock wall census is: `unsupported-import-form` 12,
  `raise-guard-not-modeled` 7, `function-globals-read` 6,
  `function-return-shape` 6, `module-constant-not-closed` 6,
  `reader-form-unsupported` 5, `augmented-assignment-not-modeled` 2,
  `function-closure` 2, and `import-use-outside-grammar` 2. The source corpus stayed
  276 files with identical before/after inventory digest
  `sha256:cfc5b235202a4a7a369c358b540c196afb221321258ab830fa537363cb98f0ac`;
  the repository remained clean.

## Growth-10/11 closure record

- RESUMED by Alex's explicit authorization: Growth 10 may use a recursively
  enumerated, default-deny AST language for wall-census procedure authority; unknown
  or dynamic Python forms receive `no-lock`. No recognizer, grant, pin, registry,
  qualification, or frozen-lane change is authorized.
- The revised Growth-10 memo must receive a fresh HEAVY `CLEAR TO BUILD` review before
  any builder runs. If code later clears review, the next immutable corpus is
  `run-40-authority-2`; the empty `run-40` remains frozen evidence and is never retried
  or rescored. Do not run another blind checkpoint until roughly three to four
  additional reviewed growth rounds accumulate.
- Maintainer threat-model decision: future adversarial rounds should assume ordinary
  real-researcher code written by a reasonable programmer. Reviewers still probe
  realistic mistakes, ordinary aliases and rebinding, and direct escapes from the
  stated default-deny boundary. They must not turn future rounds into an arms race
  against deliberately absurd or obfuscated interpreter puzzles (for example,
  disguising namespace corruption through `exec` or traceback frames). Unknown or
  dynamic forms deterministically receive `no-lock`; refusal is the safety boundary,
  not a defect the recognizer must defeat.
- Fresh resumed design review 4 validated that boundary, the recursive AST envelope,
  ordinary binding siblings, pinned fixture, strict-CSV approach, safe allocation,
  prompt neutrality, pins, and production isolation, but returned `BLOCKED` on a
  non-adversarial provenance join: the baseline records one authorization lock while
  the shadow adapter inspects separately synthesized authority records. The memo now
  requires one base context, one persisted and verified lock, the exact lock record
  set applied to the adapter context, and explicit lock-to-translation-to-shadow
  digest bindings. It also makes the canonical SciPy import module-level and requires
  whole-stream `csv.reader(..., strict=True)` plus NUL rejection. A new fresh design
  review gates any builder.
- Fresh resumed design review 5 then executed the repaired exact-lock chain
  successfully, but returned `BLOCKED` on one finite direct sibling: an additional
  ordinary `import scipy as sp` or `import scipy.stats as spstats` could replace the
  authorized procedure before the canonical call. The memo now requires the canonical
  module-level import to be the only SciPy-rooted import anywhere and adds both
  combined alias/mutation `no-lock` fixtures. It also makes dangling run-path symlink
  refusal explicit. One final fresh resumed design review gates the build; a third
  failure would trigger the orchestrator brief's persistent-failure halt.
- Fresh resumed design review 6 returned `CLEAR TO BUILD` with no findings. Its
  executed probes confirmed the 82-class exact-field AST envelope, strict CSV
  refusals, both direct SciPy alias cases, one exact persisted lock applied into the
  inspected context, run/dangling-symlink controls, pins, production isolation, and
  byte-identical `run-40`.
- A fresh Growth-10 builder implemented the cleared memo, limited to
  `scripts/wall_mining_corpus.py` and `tests/test_wall_mining_corpus.py`. The builder
  reported 320/320 implementation-specific and v2 regression tests passing, clean
  targeted Ruff and mypy checks, a passing starter validator, and the frozen 243-file
  `run-40` digest still exactly
  `71de6d51847d65449e5393af80ae9048bfbf3e979c0a1b971111be5e23d4a240`.
  Its combined release-identity run failed only because this orchestrator-owned state
  and the new build had not yet entered the manifest sequence. The orchestrator must
  commit, regenerate the manifest, run the verified full-suite gate, and push; a
  separate fresh code review still gates `run-40-authority-2`.
- The orchestrator committed the build as `1fb3450`, regenerated the manifest in
  `bb050ee`, verified the full repository suite with `PYTEST_EXIT=0`, and pushed both
  commits. A first fresh code reviewer returned `CLEAR FOR BATCHES` after 77 focused
  tests and 20 independent ordinary binding/mutation probes. Before accepting that
  gate, the orchestrator noticed the probe set did not visibly exercise the memo's
  explicit default-bound `ast.Import` sibling and sent it to a second fresh reviewer.
- The bounded fresh follow-up review returned `BLOCKED` with an executed ordinary-code
  fail-open: both `import stats` and compile-valid `import stats.helpers` bind the name
  `stats`, but the implementation checked only `alias.asname`. Both sources returned
  an authorized `scipy.stats.ttest_ind` transport, and an end-to-end scratch case wrote
  `authorization-lock.json` without executing the source. Existing 77/77 tests passed
  because they covered explicit aliases but not default import bindings. No corpus was
  run and no accusation was emitted. The narrow fix is to compute each `ast.Import`'s
  actual Python binding (`asname` or the first dotted component), apply the existing
  forbidden-binding rule to it, and add permanent `no-lock` tests for both failing
  forms plus safe/explicit-alias contrasts. A new fresh builder must make only that
  reviewed repair; a new fresh code reviewer still gates `run-40-authority-2`.
- Fresh fix builder 1 made exactly that repair: `ast.Import` now checks `asname` or
  the first dotted component, with permanent refusals for `import stats`,
  `import stats.helpers`, and `import math as stats`; `import stats as other` remains
  the non-rebinding contrast. An end-to-end regression verifies the default-bound
  source writes no lock and passes an authority-free context to the adapter. The
  builder reported 82/82 focused tests, targeted Ruff check/format, and diff checks
  passing, with only the two authorized functional files changed. The orchestrator
  must repeat the manifest/full-suite/push sequence and a new fresh reviewer must clear
  the repaired exact snapshot before `run-40-authority-2`.
- The orchestrator committed fix builder 1 as `23775d2`, regenerated the manifest as
  `ddadb1d`, verified another full-suite `PYTEST_EXIT=0`, and pushed both commits. A
  new fresh code reviewer then returned `CLEAR FOR BATCHES` with no findings after
  independently reproducing both former failures as `no-lock` with no lock file and
  zero authority records, exercising dotted/multi/default/explicit import siblings,
  passing 82/82 focused tests and the full repository suite, and rechecking the AST,
  CSV, exact-lock replay, provenance, allocation, pin, v1, production, capability,
  qualification, and frozen-tree invariants. `run-40` remained 243 files at exact
  digest `71de6d51847d65449e5393af80ae9048bfbf3e979c0a1b971111be5e23d4a240`.
  Growth 10 is now cleared to create exactly one new immutable non-measurement corpus,
  `run-40-authority-2`; zero accusations and transport/wall separation remain gates.
- Immutable `run-40-authority-2` completed with `CENSUS_EXIT=0`: 40/40 isolated Haiku
  calls, concurrency cap 3, no retries, no project-code execution, 40 unique sessions,
  and 276 purpose-stamped files (aggregate tree digest
  `f13a2728c1e46c4e308fe731bb28ec8c54f6d31a8491b63a17f87bb33677809f`).
  Thirty-three cases were `lock-projected`; seven were `no-lock` (six
  `unit-declaration-missing-or-ambiguous`, one
  `procedure-source-not-compilable`). Every lock/no-lock file-presence relation and
  every generation/isolation stamp replayed correctly. Outcomes were 34 `unsupported`
  and six `question`: ZERO accusations/findings. The original 243-file `run-40`
  remained byte-identical at its recorded digest.
- Growth-10 honest wall ranking among lock-projected cases is now usable:
  `function-globals-read` 17, `unsupported-import-form` 10,
  `function-return-shape` 6, `raise-guard-not-modeled` 6,
  `module-constant-not-closed` 4, `function-closure` 2, and
  `import-use-outside-grammar` 2. Transport refusals remain separate from recognizer
  walls and do not enter this ranking. The next design must measure the concrete
  `function-globals-read` source forms before proposing Growth 11; no blind checkpoint
  is due yet.

## In flight

- Maintainer sequencing decision (Fable escalation channel, confirmed with Alex,
  2026-08-16): after Growth-13, run Growth-14 on the twelve-case census pandas/import
  family, then Growth-15 on the seven-case census raise family. Rank future work by
  cases actually completed, not raw wall occurrences. Nothing in this decision
  promises admission or relaxes a reviewer gate.
- Fresh scratch census refresh on reviewed HEAD `dd3cebd` reproduced 40 open cases,
  39 locks / one procedure-source no-lock, 40 unsupported, and walls
  `unsupported-import-form 12`, `raise-guard-not-modeled 7`,
  `function-globals-read 6`, `function-return-shape 6`,
  `module-constant-not-closed 6`, `reader-form-unsupported 5`, and the smaller
  recorded walls, with zero accusations, model calls, or project-code execution.
  The frozen A-J2 refresh found 95 materialized cases, 79 authentic locks, 15
  no-locks, one retained static replay, 80 unsupported / 15 questions, and zero
  accusations. All 47 `positive_demonstrated` cases remained short of full analysis;
  none emitted an adverse certificate. The first-occurrence batch-K trigger therefore
  remains armed but inactive.
- Growth-14 census inventory: exact cases `0004`, `0006`, `0009`, `0012`, `0014`,
  `0016`, `0025`, `0027`, `0030`, `0035`, `0038`, and `0039` all bind `pd` only via
  `import pandas as pd`, call `pd.read_csv` on the authorized input, and form two
  independent operands by equality-filtering one group column and selecting one value
  column. Optional observed forms are `.values`, `.dropna()`, dataframe
  `dropna(subset=[...])`, a positive-value filter, and `.notna().copy()`. Strict-byte
  replay shows eleven cases have one selected row per authorized unit; case `0025`
  has four rows for each of six station ids and no cross-operand unit. Import-only
  unmasking completes zero cases, so the memo must measure and name every secondary
  wall and may promise only the exact closed subset it proves.
- The earlier validation-guard memo is deferred evidence for Growth-15:
  `~/Desktop/random_stuff/sc-referee-design-memos/dependence-grammar-growth-14-validation-guard-design-2026-08-16.md`.
  Fresh reviewer session `01a00c16-faef-77a3-9443-6cf8b2730ec8` returned
  `GUARD-INERTNESS-ONLY: REFUSE`, `SINGLE-OPERAND-CLASSIFICATION: REFUSE`, and
  `VERDICT: BLOCKED`, without changing the repository. BLOCKER 1 demonstrated that
  an ordinary module helper shadowing `len` (and similarly `set`) can make a runtime-
  true guard appear mathematically false after erasure, exposing both a covered-
  negative and an adverse candidate. This is a rejected design route, not a shipped,
  corpus, scored, or production accusation. BLOCKER 2 showed five proposed targets
  lacked the claimed existing sequence classification, including an undefined
  `.strip()` normalization. A MAJOR finding requires total mixed-state refusal
  precedence. Growth-15 amendments must prove real `len`/`set` binding in analyzer
  and kernel, consume the sole shared classifier or narrow the target set, forbid any
  guard-specific lineage, and specify exact mixed-state/kernel precedence before a
  fresh design review. No guard builder is authorized.

- Growth-13 is the maintainer-authorized paired-procedure family HEAVY design. Exact
  frozen census: nine workflows, seven `ttest_rel` calls, four `wilcoxon` calls, and
  eleven calls total because two workflows contain both. Stored historical authority
  evidence is 5 unavailable / 4 ambiguous, but the current Growth-7+ resolver replay
  is 9 unavailable because it returns on the first unregistered paired member. Under
  the proposed closed paired registry and raw-call precedence, seven workflows have
  one singular-lock opportunity and the two dual-call workflows remain mandatory
  `procedure-ambiguous-multiple-statistical-calls` no-locks. All seven singular cases
  have measured downstream syntax walls; no frozen-case admission or candidate is
  promised. The design defines position-level independence: the two sides at one row
  are one legitimate pair position, and adversity requires the same authorized unit
  at multiple pair positions. The growth-3 paired/crossover control remains central
  and must never accuse or clear under the paired path.
- Growth-13 HEAVY design review round 1 used fresh reviewer session `01a00b33` on
  exact clean HEAD `423346c` with `.git` read-only and returned `VERDICT: BLOCKED`.
  The reviewer reproduced all census counts, proposed 7-lock/2-no-lock transport,
  downstream walls, SciPy-1.14.0 signatures, pair-position equation, byte/value-exact
  runtime operands, kernel architecture, wording, isolation, and protected boundary.
  No repository file changed, no corpus ran, and no accusation occurred. Two findings
  blocked: (1) extending the existing authority census would mint a `ttest_rel` lock
  after ordinary root/member rebinding even though an executed pinned-runtime source
  invoked `ReplacementStats.ttest_rel`; the same fail-open covered assignment,
  annotated/augmented/tuple/walrus, loop/with targets, parameter/def/class shadowing,
  later import, attribute mutation, and deletion; (2) the memo did not bind exact full
  reason sets and precedence for all paired refusal fixtures.
- Binding memo v2 sections 15–16 now require a recursively enumerated, scope-aware,
  default-deny authority binding pass; one exact transport-only
  `procedure-binding-not-closed` reason; raw call-token precedence before deduplication;
  no lock file and zero authority records for every invalidated form; redundant direct
  callable parentheses treated as semantically identical; a complete paired domain and
  kernel reason vocabulary; deterministic stage precedence; and exact full sorted
  transport, recognizer, CSV-domain, and kernel-bypass matrices. Reasonable direct
  aliases/rebinding/mutation remain in scope; obfuscated interpreter puzzles remain out
  of scope per the maintainer threat-model decision. A different fresh reviewer must
  re-execute the replacement-runtime/binding probes, explicitly assent or refuse on
  transport precedence, and return `CLEAR TO BUILD` before any builder may run.
- Growth-13 HEAVY design review round 2 used fresh reviewer session `01a00b42` and
  returned `VERDICT: BLOCKED` with `TRANSPORT-PRECEDENCE: ASSENT`. Its `/tmp`
  prototype and pinned-runtime probes closed round-1 finding 1: every required
  assignment/scope/import/deletion/member-mutation invalidator produced no lock file
  and zero authority records; dynamic aliases stayed unresolved; raw duplicate/mixed
  call precedence, helper exclusion, parentheses, the exact 7-lock/2-no-lock frozen
  opportunity, paired semantics, runtime operands, kernel shape, wording, pins, v1,
  production isolation, and protected/frozen boundaries passed. Round-1 finding 2
  remained blocked by three phase-label contradictions only: the authority-free proxy
  belongs in `reason_code` with empty `abstention_reasons`; clear/extend reaches the
  earlier existing `sink-mutates-operand-name`; and material-selection mismatch,
  paired obligation mismatch, and invalid `FrozenMaterialInput` construction are
  different phases. Binding memo v3 section 18 corrects those exact payloads without
  changing the grammar or transport precedence. One third fresh design reviewer must
  clear both original findings before any builder runs; another failure reaches the
  orchestrator brief's persistent three-attempt escalation threshold.
- Growth-13 HEAVY design review round 3 used fresh reviewer session `01a00b4b` on
  exact committed base `423346c` with `.git` read-only and returned unconditional
  `VERDICT: CLEAR TO BUILD` with `TRANSPORT-PRECEDENCE: ASSENT` and no findings. It
  independently reproduced the exact authority-free adapter payload, all four direct
  left/right `clear`/`extend` singleton refusals at the existing partition, and the
  material-selection / paired-obligation / constructor / kernel-fact phase split. It
  confirmed that binding memo v3 resolves both original round-1 findings, preserves
  the recursively enumerated default-deny transport, the seven-singular/two-ambiguity
  opportunity, pair-position semantics, independent paired kernel, wording ceiling,
  production isolation, and every protected boundary. No repository or memo file was
  changed by the reviewer, no corpus ran, and no accusation occurred. A fresh builder
  may now implement the complete cleared memo through section 18; the builder remains
  barred from commits, pushes, frozen-lane changes, and all protected surfaces.
- Fresh Growth-13 builder session `01a00b51` implemented the complete cleared memo on
  exact base `423346c` with `.git` read-only. It added the recursively enumerated,
  scope-aware, default-deny authority pass; singular-only paired transport; distinct
  paired IR/domain/certificate/kernel/adapter paths; and the exact authority,
  phase-precedence, pair-position, runtime, kernel-bypass, and nine-workflow census
  regressions. The builder did not review, commit, push, run a frozen corpus, or edit
  STATE. Its final evidence was 66/66 Growth-13 tests and 364/364 focused tests, scoped
  Ruff/format, `mypy src` over 161 source files, starter validation over 79 public
  examples, both installed-pin checks, production isolation, and exact seven-lock /
  two-ambiguity census assertions. The only focused-suite exclusion was the manifest
  inventory test reserved for the orchestrator's commit-then-regenerate sequence.
- The orchestrator audited the handoff against `423346c`: changed paths are confined
  to the memo-authorized development v2/harness/test/EXPERIMENT-0060 surface; protected
  and frozen changed paths are zero; `git diff --check` passes. The exact uncommitted
  full suite ran all 4,166 tests and had one failure only at
  `test_manifest_builder_inventory_equals_git_tree_listing`, caused by the necessarily
  stale pre-commit manifest. Repeating the full repository suite with only that one
  identity test deselected passed all other 4,165 tests with verified
  `PYTEST_EXIT=0`. The orchestrator must now commit the functional inventory, rebuild
  and separately commit `MANIFEST.sha256`, require an exact full-suite exit 0, push a
  clean snapshot, and send that snapshot to a different fresh code reviewer. Only
  `CLEAR FOR RE-MEASURE` permits the nine-case scratch retranslation; no frozen case
  has been rerun and no accusation has occurred.
- Growth-13 code review on exact clean pushed HEAD `dfa3bb1` is BLOCKED. Fresh
  reviewer session `01a00b95` first demonstrated a Section-15 fail-open but terminated
  when its platform filter rejected a benign review-only kernel probe, so it emitted
  no final verdict. Different fresh completion reviewer session `01a00b9b` then
  independently reproduced and bounded the defects, returned `VERDICT: BLOCKED`, and
  explicitly reported `TRANSPORT-PRECEDENCE: REFUSE`. Eight of 38 closed-binding
  probes failed: member Store targets through for/with/comprehension, an establishing
  import in the wrong lexical scope, annotated/destructuring/named-expression callable
  aliases beside a direct call, and a module-object alias beside a direct call all
  minted a singular paired lock. A pinned SciPy-1.14.0 source printed `REPLACEMENT`
  while end-to-end translation created one human authorization and an actual v2 lock
  file. These are incorrect authority records, not recognizer or scored accusations.
- The completion reviewer also found six paired-fact closure mutations accepted by
  the kernel: valid-looking wrong unit ids, changed exact source strings with equal
  numeric casts, reordered headers, reordered row values, changed frozen file refs,
  and changed multiplicity. The last changed a valid adverse repeated-unit fact into
  a verified `one_pair_position_per_unit` covered-negative conclusion. This is a
  demonstrated false-accusation/clearance route at the kernel boundary, but no adapter
  output from altered trusted evidence, production Finding, scored case, frozen case,
  or re-measure was emitted. A paired-vector walrus rebind also returned the safe but
  memo-wrong `named-expression-not-modeled` instead of `operand-name-rebound`.
  All other paired semantics, Section-18 phases, exact 7-lock/2-ambiguity opportunity,
  thirteen straightforward kernel obligations, runtime operands, wording, pins,
  production isolation, protected/frozen identity, scoped static checks, 66/66
  Growth-13 tests, and the full 4,166-test `PYTEST_EXIT=0` passed. Binding memo
  Section 22 records the narrow repair. A fresh fix builder must implement only that
  inventory; a different fresh code reviewer still gates any re-measure.
- Fresh fix builder session `01a00bb3` implemented exactly binding memo Section 22 on
  base `dfa3bb1`, without editing STATE, committing, pushing, or running a frozen
  corpus. The existing authority pass now closes member Store/Del targets, lexical
  import/call ownership, and all reviewed callable/module alias forms; the paired
  kernel independently reconstructs the complete strict-CSV fact from the selected
  frozen material bytes and references; and paired operand walruses reach the existing
  sole operand/sink partition before the generic named-expression refusal. The
  reviewer transport replay moved from 30/38 to 38/38, every reviewed end-to-end
  source produced zero authority records and no lock file (including pinned runtime
  replacement sources that printed `REPLACEMENT`), every valid-looking fact mutation
  was refused at singleton `paired-fact-closure`, and the paired/non-paired walrus
  reasons were exactly `operand-name-rebound` / `named-expression-not-modeled`.
  Builder validation passed 78/78 Growth-13 tests (the original 66 plus twelve repair
  regressions), 376 focused tests with only the orchestrator-owned manifest inventory
  test deselected, scoped Ruff/format, `mypy src` over 161 files, starter validation,
  installed pins, production isolation, and protected/frozen diff checks.
- The orchestrator verified the repair handoff on exact `dfa3bb1`: only the five
  authorized Growth-13 development implementation/test/EXPERIMENT-0060 files plus
  this pre-existing living-state edit differ; `git diff --check` passes; manifest,
  v1, EXPERIMENT-0058, authority/grants/pins/registry, qualification, protected, and
  frozen-lane diffs are zero. The full repository functional suite, with only
  `test_manifest_builder_inventory_equals_git_tree_listing` deselected until the
  commit-then-regenerate sequence, reached 100% with captured `PYTEST_EXIT=0`.
  The functional repair and this gate record were committed as `8c8a7ce`. Manifest
  regeneration, the exact all-test gate, push, and a different fresh code review
  remain required. No re-measure or accusation has occurred.
- The orchestrator regenerated the manifest and committed the repaired release
  inventory as `19950b2`, then ran the exact repository-wide suite to 100% with
  captured `PYTEST_EXIT=0` and pushed clean `dev/dependence-growth`. Fresh repaired-
  snapshot reviewer session `01a00bdb` independently reviewed exact local and remote
  HEAD `19950b2` with `.git` read-only and returned no BLOCKER, MAJOR, or MINOR
  findings, `TRANSPORT-PRECEDENCE: ASSENT`, and
  `VERDICT: CLEAR FOR RE-MEASURE`. It re-executed all eight former transport
  fail-opens end to end (exact reasons, zero authority, no lock file), three pinned
  SciPy-1.14.0 replacements that printed `REPLACEMENT`, the seven-lock/two-ambiguity
  opportunity, every paired-fact alteration and singleton kernel obligation, walrus
  precedence, paired/crossover/runtime/CSV/Wilcoxon/phase controls, pins, production
  isolation, reason registry, manifest identity, scoped static checks, and all 4,178
  repository tests with captured `PYTEST_EXIT=0`. Protected and frozen differences
  were zero, the tree stayed clean, and no re-measure or accusation occurred in review.
- The gated scratch Growth-13 re-measure then compared committed pre-round base
  `423346c` with reviewed head `19950b2` across the same nine immutable paired
  workflows. Both sides rebuilt their inspection contexts from frozen audit records
  where available, ran the description-to-v2-lock translation, persisted and applied
  the exact generated lock records, and inspected the shadow adapter. No authored
  project code or model ran. Transport moved exactly from nine unavailable no-locks
  to seven singular locks plus two ambiguity no-locks. Exactly the seven singular
  cases moved from non-accusatory `question` to non-accusatory `unsupported` at the
  reviewed walls: `41cfd...` `function-return-shape;raise-guard-not-modeled`,
  `f75b...` `function-globals-read;raise-guard-not-modeled`, `c38b...`
  `function-closure;function-return-shape`, `58960...`, `cc45...`, and `5d9a...`
  `import-use-outside-grammar`, and positive I1 `2d0d...`
  `module-constant-not-closed`. The two dual-call cases `407236...` and `be2cd...`
  stayed non-accusatory questions behind
  `procedure-ambiguous-multiple-statistical-calls`. Accusations remained `0 -> 0`,
  `REMEASURE_EXIT=0`, and the complete frozen growth-loop lane had identical
  before/after filesystem digest
  `sha256:1cc36ea1bba28e643e25aafac848ed36695ab486d87cf7c3c1c8c414b492adad`.
  HEAD/remote remained `19950b2` and the repository stayed clean. Growth-13 is closed.
- The current raw wall leader is twelve `unsupported-import-form` cases. All twelve
  use exact `import pandas as pd` plus `pd.read_csv` and dataframe/series selection;
  this is not an import-only vocabulary change. A scratch import-only unmask moved
  eleven cases immediately to `module-constant-not-closed` and case `0027` to
  `raise-guard-not-modeled`, so accepting the import alone completes zero cases.
  Maintainer priority nevertheless selects this family for Growth-14 by case-
  completion yield. The round must therefore be HEAVY and may design only a recursively
  closed pandas-to-existing-classifier lowering, independently rederived by the
  kernel; unknown/dynamic dataframe forms remain no-analysis. Growth-15 is the
  separately sequenced abort-only raise round. Numeric predicates are deferred.
- Growth-14 HEAVY design review attempt 1 used fresh reviewer session
  `01a00c3f-d808-7203-beee-614b3e4c9340` on exact clean local/remote HEAD `dfdb62a`
  with `.git` read-only. The reviewer returned `PANDAS-INVARIANCE: REFUSE`,
  `SINGLE-OPERAND-CLASSIFICATION: REFUSE`, and `VERDICT: BLOCKED`; no builder ran and
  no frozen case was re-measured. The decisive blocker is fundamental under the
  protected-pin constraint: original source plus frozen bytes cannot prove that
  `import pandas as pd` resolves to the intended package or that its unpinned dtype/
  selection semantics match the proposed strict reconstruction. Executed ordinary
  siblings showed an adjacent `pandas.py` winning import resolution, `True`/`False`
  group tokens becoming bool and selecting different rows from strict string
  equality, and a huge finite decimal becoming object dtype and failing in SciPy.
  Other blockers were a competing pandas-local operand classifier, incomplete
  source/reason/kernel precedence (including census `0016`), and unproved real-builtin
  `open` binding; ndarray `.median()` also demonstrated the need for projection-
  specific summaries. These are pre-build design findings, not accusations.
- Binding memo Section 16 records the no-build disposition. Growth-14 is deferred
  until a separately authorized and reviewed package-identity premise exists; it may
  not add, change, or simulate a pandas pin, and an import-only build remains
  forbidden because its measured completion yield is zero. Reviewer validation
  otherwise passed seven target runtime differentials, two SciPy destructuring
  probes, a scratch independent-kernel mutation suite, 385 focused tests, all 4,178
  repository tests, scoped static checks, pins, production isolation, v1/protected/
  frozen identity, and the explicit frozen planted-positive observation at `0/47`.
  The maintainer's ordering was honored by evaluating this family first; Growth-15
  may now proceed independently through its full HEAVY gates.
- Growth-15's active amended memo is
  `~/Desktop/random_stuff/sc-referee-design-memos/dependence-grammar-growth-15-abort-only-raise-design-2026-08-16.md`.
  It supersedes, but does not erase, the rejected guard-fact draft. The new proof is
  path-relative abort-only control flow: supported conditions reuse the existing pure
  expression boundary, every `len` must independently resolve to the real builtin,
  `set`/seen-set/guard facts/guard-specific reader or grouping lineage are deleted,
  and a full conclusion must map every condition name through the existing sole
  partition and prove every guard false from the existing trusted group fact. A
  standalone wall scan may decompose syntax only and can never create a certificate.
  Scratch source-only deletion measured exactly nine expected reason-set movements:
  all seven census cases plus frozen positives G2 `a8b660...` and J2 `729d20...`;
  all remain unsupported, all seventeen non-target raise workflows retain their
  complete current sets, and no accusation or outcome movement occurred. Because
  Growth-14 did not unlock its forecast downstream cases, Growth-15 now completes zero
  census cases on the unchanged base; the memo records that yield correction rather
  than widening. A fresh HEAVY design review, with explicit fallthrough, sole-
  classifier, and precedence assent/refusal, gates any builder.
- Growth-15 exhausted its three permitted fresh design-review attempts without a
  build. Attempt 1 (`01a00c74-86c3-76c2-96ff-b7bd03544749`) returned
  `FALLTHROUGH-INERTNESS: REFUSE`, `SINGLE-OPERAND-CLASSIFICATION: ASSENT`, and
  `PROTOCOL-PRECEDENCE: ASSENT`: existing NumPy-array operands made cardinality-only
  `NotName` truth testing unsound. Binding Section 13 proposed exact builtin-container
  provenance. Attempt 2 (`01a00c9a-8485-7ac1-acaf-c679f44aace2`) returned
  `FALLTHROUGH-INERTNESS: ASSENT`, `SINGLE-OPERAND-CLASSIFICATION: REFUSE`, and
  `PROTOCOL-PRECEDENCE: ASSENT`: `.get(CONSTANT, [])` was outside the sole partition,
  and true empty-container controls had to retain existing fact/domain precedence.
  Binding Section 14 consequently made all `NotName` handling syntax-only and left
  only exact real-builtin `LenCompare` atoms in the proposed full path.
- Fresh attempt 3 (`01a00cb5-e886-7603-aeac-5c38cd71a715`) reviewed exact clean local
  and remote `a0ea4e0`, returned `FALLTHROUGH-INERTNESS: REFUSE`,
  `SINGLE-OPERAND-CLASSIFICATION: ASSENT`, `PROTOCOL-PRECEDENCE: REFUSE`, and
  `VERDICT: BLOCKED`, and triggered persistent-failure escalation. Its executed
  counterexample began with an adverse repeated-unit fact whose real group lengths
  were `(1, 4)`, for which `len(left) < 2 or len(right) < 2` aborts before the
  procedure/report. Moving one complete row-evidence tuple between supplied groups
  produced lengths `(2, 3)` while retaining the repeated unit and `repeated_units`
  conclusion; the existing independent kernel accepted the mutation with no failure.
  The proposed guard evaluation would then expose an unreachable adverse
  `evaluation_candidate`. This is a pre-build kernel-bypass route, not a shipped or
  scored accusation. The reviewer found no other issue; reproduced the complete
  26-workflow / 55-raise inventory, exact nine movements, seventeen freezes, zero
  outcomes and completions, all `NotName` refusals, ordinary precedence controls,
  protected identity, and `0/47` planted-positive observation; and passed 385 focused
  plus all 4,178 repository tests. Memo Section 15 records the binding no-build
  disposition. The two unselected maintainer options are complete independent
  byte-derived group-fact reconstruction before guard evaluation, analogous to the
  repaired paired kernel, or making `LenCompare` syntax-only too. No builder,
  re-measure, or batch is authorized pending maintainer direction.
- MAINTAINER-AUTHORIZED BUT SEQUENCED AFTER GROWTH-15 (Fable escalation channel,
  confirmed with Alex, 2026-08-16): revive the Growth-14 pandas family only after
  Growth-15 closes. The new HEAVY design may prove package identity from each frozen
  case's complete file inventory (including absence of an adjacent shadowing module)
  plus a declared pinned development runtime. A specific pandas version may be added
  only to the development sandbox and treated as an immutable v2-development premise;
  qualified v1 surfaces, grant pins, registry, and every protected path remain byte-
  frozen. The modeled pandas subset must be narrow and default-deny against that exact
  version. Bool group-token coercion, object-dtype huge decimals, strict-string
  selection mismatch, and every previously demonstrated dtype/selection divergence
  must become explicit refusal fixtures or receive a separately proved safe
  reconstruction rule. The earlier no-build disposition remains correct. This
  authorization does not start a build, bypass HEAVY review, relax zero-FA discipline,
  or change the `0/47` batch-K trigger.
- MAINTAINER ACKNOWLEDGMENT (Fable escalation channel, confirmed with Alex,
  2026-08-16): the Growth-15 third-review escalation is expected and correct. The
  exact evidence is persisted above and in memo Section 15. The maintainer response
  will be a design principle, as in Growth 10, not authorization for an ad hoc patch.
  Growth 15 remains blocked and no implementation, re-measure, batch, or queued
  Growth-14 work may start until that principle arrives and passes the normal fresh
  HEAVY design-review gate.
- MAINTAINER RESUMPTION PRINCIPLE (Fable escalation channel, decided under Alex's
  delegated authority, 2026-08-16): Growth-15 Section-15.2 Option A is selected for
  exactly one resumed design round. Before guard evaluation, the kernel must
  independently reconstruct the complete ordinary group fact from digest-bound frozen
  bytes, analogous to the repaired paired kernel. Guard evaluation, source replay,
  operand equations, conclusions, certificate identity, and the verified result all
  consume that one replayed object; supplied or certificate-carried facts never feed
  a guard. Thus the attempt-3 `(1, 4) -> (2, 3)` row-tuple mutation becomes impossible
  by construction, not by a mutation blacklist. Option B (`LenCompare` syntax-only)
  is rejected. Exact builtin-container provenance remains a refusal boundary,
  `NotName` remains syntax-only, and exact real-builtin-proven `LenCompare` atoms and
  `Or` trees remain the only truth-evaluated forms. Memo Section 16 is binding. One
  fresh maximum-effort HEAVY reviewer must reproduce the exact counterexample and full
  attempt-3 inventory and return explicit fact-replay assent plus unconditional
  `CLEAR TO BUILD`; otherwise halt and escalate directly to Alex with no fifth design
  variation. No build, re-measure, batch, or queued Growth-14 work is yet authorized.
- Growth-15's one authorized resumed Option-A HEAVY design review used fresh maximum-
  effort reviewer session `01a00d0f-7c96-7781-904a-d491e4845a19` on exact clean
  local/remote base `679899c2ab9e392ffe8cf55c143e6f6913fc36d0`, with `.git`
  read-only. The reviewer returned no BLOCKER, MAJOR, or MINOR findings and the exact
  required footer: `FALLTHROUGH-INERTNESS: ASSENT`,
  `SINGLE-OPERAND-CLASSIFICATION: ASSENT`, `PROTOCOL-PRECEDENCE: ASSENT`,
  `FACT-REPLAY-CLOSURE: ASSENT`, `VERDICT: CLEAR TO BUILD`.
- Its independent prototype re-derived every existing ordinary group-fact field from
  the frozen bytes; matched the controller across both line models and casts,
  dynamic/predeclared buckets, seven supported-domain cases, 28 refusal-domain cases,
  300 deterministic fuzz cases, and direct/subscript/sorted/NumPy operand forms; and
  refused every top-level, nested, tuple-movement, omission, duplication, reorder, and
  cross-field supplied-fact mutation at singleton `fact-closure`. The exact attempt-3
  real `(1, 4)` / supplied `(2, 3)` counterexample closed before guard evaluation,
  while the authentic replayed guard returned only `sink-controls-operand-flow`.
  Fact/domain precedence, syntax-only `NotName`, real-builtin `LenCompare`/`Or`, token
  closure, source replay, conclusion identity, and controller-helper monkeypatch
  independence all passed. The final provenance probe also showed that coordinated
  file/asset-reference substitutions are rejected while constructing the trusted
  `FrozenInspectionContext`, before certificate verification.
- The reviewer reproduced the complete 26-workflow / 55-raise inventory with exactly
  nine syntax-only reason movements, seventeen freezes, zero outcome movements, zero
  completions, and zero accusations. The planted-positive observation remains
  `0/47`; batch K is not triggered. Validation passed 377 focused tests, scoped Ruff
  and format, `mypy src` over 161 files, starter validation, both live pins,
  production/protected/frozen identity, and the corrected authoritative serial full
  suite (`4,178 passed`, six warnings, exit 0). Two discarded full-suite launches are
  preserved as reviewer invocation artifacts: bare `pytest` was absent, then a
  detached-clone run omitted that clone's `src`; the complete rerun with explicit
  clone `PYTHONPATH` was green. A fresh implementer may build the complete binding
  memo through Section 16. A different fresh maximum-effort code reviewer still gates
  any frozen re-measure; no Growth-15 implementation or corpus run has occurred yet.

## Resolved halt record — Growth 10 wall-census authority transport

- Design memo:
  `~/Desktop/random_stuff/sc-referee-design-memos/dependence-grammar-growth-10-design-2026-08-15.md`.
  No builder session was launched and no Growth-10 repository code was changed.
- Fresh design review 1: BLOCKED. Executed probes showed duplicate headers,
  empty/missing unit cells, repeated same-procedure calls, and stale import aliases
  could project locks; same-content cases in distinct runs also shared downstream
  provenance digests.
- Fresh design review 2: BLOCKED. The first amendment's canonical `import scipy` form
  was itself refused by the unchanged recognizer as `unsupported-import-form`; the
  review also required symlink-safe run allocation and complete inner-reference
  provenance assertions.
- Fresh design review 3: BLOCKED. Although `from scipy import stats` passed the
  recognizer import grammar and reached the honest next wall, two pinned-runtime probes
  satisfied all seven proposed finite-root rules yet replaced `stats.ttest_ind`: one
  aliased `exec`, and one wrote through an exception traceback frame's globals using a
  split string. Both printed `FAKE`. The proposed rule set was therefore a blacklist,
  not a closed executable language, and could mint false procedure authority.
- This is a persistent design/review failure, not a scored false accusation: no new
  corpus was run, no case was scored, no accusation was emitted, and the lifetime
  scoreboard remains 96 blind cases / zero false accusations. Reviewers verified both
  installed pins live, v2 production-unreachable, protected paths unchanged, and the
  243-file `run-40` tree byte-unchanged (aggregate digest
  `71de6d51847d65449e5393af80ae9048bfbf3e979c0a1b971111be5e23d4a240`).
- Alex resolved the halt after reviewing the meaning of the hostile probes. His exact
  authorization is the default-deny AST decision recorded under `In flight`; the
  prior blacklist design remains rejected and may not be built.

## Heavy queue (evidence-ranked; measure premises before designing)

0. COMPLETED in Growth-12 through `7f822fc` and fresh `CLEAR FOR RE-MEASURE`.
   MAINTAINER-AUTHORIZED (Alex, relayed via the Fable escalation channel, 2026-08-16),
   unit-declaration intake broadening. Original queue premise: 21 frozen
   blind free cases and 6/40 of run-40-authority-2 died at
   `independent-unit-definition-unresolved` because the free-form description never
   contained the exact `Independent unit column:` string — the single largest miss
   cause, ahead of any grammar wall. Authorized scope: a HEAVY design round letting
   the deterministic role-blind lock translation accept ordinary declaration
   phrasings of the independent-unit column. Constraints: translation stays
   deterministic, role-blind, and fail-closed (ambiguous or conflicting phrasings
   still resolve to no-lock, never to a guessed lock); this touches the authority
   layer, so the full design gauntlet applies and the memo must enumerate refusal
   fixtures for near-miss phrasings; no change to v1, registry, grants, pins,
   qualification records, or any promoted surface — development lanes only. Measure
   the exact phrasings in the 21+6 dead cases first and put them in the memo.
   Memo measurement corrected the premise: only six census layouts were declaration
   misses; all 21 batch descriptions already declared the column and stayed at
   procedure-stage v2 no-lock. The six census translations moved exactly as reviewed,
   with zero accusations. Maintainer intent remains a first honest blind FINDING.
1. COMPLETED in Growth-13 through `19950b2`, fresh `CLEAR FOR RE-MEASURE`, and the
   zero-accusation nine-case scratch re-measure. Paired-procedure family
   (ttest_rel/wilcoxon lock gap; recurring since batch C) — GO-AHEAD GRANTED
   (maintainer decision, relayed via the Fable escalation channel,
   2026-08-16): the new claim shape may be designed. Constraints: full HEAVY gauntlet;
   the memo must state the paired-design independence semantics explicitly (same unit
   measured twice is the LEGITIMATE shape there, so the growth-3-era paired/crossover
   must-not-accuse fixtures become the round's central regressions); fail-closed on any
   ambiguity between paired and independent claims; dev lanes only. Sequence after
   queue item 0 unless census evidence reorders.
2. MAINTAINER-AUTHORIZED FOR REVIVAL AFTER GROWTH-15 CLOSES (Fable escalation channel,
   confirmed with Alex, 2026-08-16); the prior Growth-14 no-build disposition remains
   correct: `unsupported-import-form`, twelve of 39 authentic census locks. All
   twelve are pandas workflows, so an import-only change is forbidden and measured
   to complete zero cases. Design the smallest recursively closed pandas/read/filter/
   operand slice that lowers into the existing sole classification; the kernel must
   independently rederive it. The authorized package-identity premise must prove
   resolution to real pandas from the complete per-case file inventory, including no
   adjacent shadowing module, and a specific pinned pandas version may be declared and
   installed only in the development sandbox. Dynamic forms remain default-deny;
   dtype/selection divergences demonstrated in review become refusal fixtures or
   separately proved reconstruction rules. Qualified v1 surfaces, grant pins,
   registry, every protected path, and frozen lanes remain byte-frozen. Fresh HEAVY
   design and code reviews still gate any build or re-measure; do not start this item
   until Growth-15 closes.
3. CLEARED TO BUILD as Growth-15: `raise-guard-not-modeled`, seven census cases.
   After three blocked reviews, the maintainer selected complete independent byte-
   derived ordinary group-fact reconstruction (Option A). Fresh resumed reviewer
   `01a00d0f` executed the full required matrix and returned all four assents plus
   unconditional `CLEAR TO BUILD`. A fresh implementer may build binding memo Section
   16; a different fresh maximum-effort code reviewer, full-suite gate, and zero-
   accusation scratch re-measure still gate closure. Do not run a frozen re-measure,
   batch, or advance queued Growth-14 before those gates.
4. Numeric comparison predicates for counts (float(row[x]) > CONST). The refreshed
   premise has no authentic direct numeric census opportunity; `446cab...` is a
   count-trial declaration no-lock and J2 uses a computed `delta`. Re-measure before
   reviving.
5. Module-constant closure variants (J1 rq2 and J2 rq6) and import-use decomposition
   (J1 rq1, J2 rq3) — measure exact syntax before deciding whether any slice is LIGHT.
6. Position-sensitive rebind relaxation (allow rebinding after last consumer) — only
   if corpus census shows it matters; dataflow judgment = heavy.
7. Q3 two-branch sink returns (detached from growth-8; buys little).
8. class-defs/dataclass modeling (batch-D rq2's real wall).

## Actor inventory (one-use identities; continue numbering)

Authors spent through opus-122; primary blind reviewers through fable-46; hostile
reviewer identities through fable-47; escalation identities through opus-28.
Blind-batch seats may move to codex-cli transports
(model change is a harness config change: review it).

## Process-control record

- The inherited Growth-9 builder attempt committed and pushed despite the implementer
  brief. Fresh review covered the exact pushed snapshot and found no code-safety
  consequence, but the role-separation breach is recorded. Subsequent builder and
  reviewer sessions ran with `.git` made read-only and restored by an orchestrator
  shell trap. Continue that technical control for every delegated session; only the
  orchestrator may commit or push.
- MAINTAINER PROCESS DECISION (Fable escalation channel, confirmed with Alex,
  2026-08-16): full-suite gates may run across cores through `pytest-xdist` or an
  equivalent only after the parallelization itself is treated as a reviewed harness
  change and one clean complete serial/parallel equivalence run demonstrates test
  isolation. Fresh contexts, executed probes, exact exit-code capture, and every gate
  remain unchanged. On current clean `f7cf3fc`, the repository `.venv` reports
  `ModuleNotFoundError` for `xdist`; therefore serial pytest remains the authoritative
  gate until that reviewed equivalence is completed. Merely installing or invoking a
  parallel runner does not satisfy this condition.
- While a design or code reviewer is running, the orchestrator may concurrently
  perform only the next round's read-only premise measurement: census reads, wall
  counts, and frozen-case reads. This overlap never permits a build, state or memo
  commit, frozen-lane write, re-measure, batch, or mutation while the reviewer gate is
  pending. Reviewer findings still take precedence over all speculative next-round
  measurements.
- Reviewer reasoning effort is risk-tiered without changing the mandatory probe set
  or any gate. Kernel-boundary, authority-layer, harness, and other HEAVY reviews use
  maximum reasoning effort. A genuinely pure-vocabulary diff may use medium reasoning
  effort, still in a fresh context and with the same mandatory executed probes. Risk
  ambiguity defaults to maximum effort; effort tiering never converts a HEAVY round
  into a LIGHT round or relaxes role separation.

## Key file map

- Design memos + review history: ~/Desktop/random_stuff/sc-referee-design-memos/
- v2 recognizer: src/sc_referee/dependence_recognition_v2/ (EXPERIMENT-0060)
- Harness: evaluation/src/sc_referee_evaluation/lean_pipeline.py + scripts/lean_pipeline.py
- Frozen lanes: evaluation/development/dependence-growth-loop/batch-*
- Pinned sandbox: ~/Desktop/random_stuff/sc-referee-pilot-runtime/scipy114-venv
- Suites: tests/test_dependence_recognition_v2*.py, test_dependence_free_envelope.py,
  test_release_identity.py; full suite gates pushes.

## Standing maintainer decisions on record

Autonomous loop authorized (no pings except FA halt / reserved decisions / persistent
failure). Efficiency restructure adopted (fresh sessions + briefs, corpus censuses,
checkpoint batches). Variable names must never carry recognition meaning (operations
and library configurations only). Deadline asks default to polished-and-public
(maintainer memory); nothing in this loop publishes without him.

Maintainer checkpoint decision (Fable escalation channel, 2026-08-16): on every
frozen re-measure, explicitly inspect planted positives for a new development-lane
adverse certificate after full analysis, without rescoring. The first occurrence
triggers checkpoint batch K promptly, both envelopes and all normal design/code gates,
instead of waiting for the ordinary three-to-four-round cadence.
