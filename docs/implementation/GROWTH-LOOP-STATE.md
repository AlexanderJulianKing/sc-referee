# Growth-loop living state (maintained by the orchestrator, every iteration)

Updated: 2026-08-16 (Growth-12 closed; Growth-13 build complete and code review is the next gate).

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
- The current raw wall leader is twelve `unsupported-import-form` cases, but all twelve
  import pandas and therefore do not present a demonstrated pure import-vocabulary
  gain: dataframe/reader semantics remain outside the current closed recognizer. That
  evidence does not reorder the explicit paired-family go-ahead. No blind checkpoint
  is due until roughly three to four additional reviewed rounds after J1/J2.

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
1. NEXT — Paired-procedure family (ttest_rel/wilcoxon lock gap; recurring since batch C) —
   GO-AHEAD GRANTED (maintainer decision, relayed via the Fable escalation channel,
   2026-08-16): the new claim shape may be designed. Constraints: full HEAVY gauntlet;
   the memo must state the paired-design independence semantics explicitly (same unit
   measured twice is the LEGITIMATE shape there, so the growth-3-era paired/crossover
   must-not-accuse fixtures become the round's central regressions); fail-closed on any
   ambiguity between paired and independent claims; dev lanes only. Sequence after
   queue item 0 unless census evidence reorders.
2. Numeric comparison predicates for counts (float(row[x]) > CONST; batch-B 446cab
   flagship + recurring, including J2 rq2).
3. raise/validation guards inside helpers (part of the globals-read decomposition).
4. Module-constant closure variants (J1 rq2 and J2 rq6) and import-use decomposition
   (J1 rq1, J2 rq3) — measure exact syntax before deciding whether any slice is LIGHT.
5. Position-sensitive rebind relaxation (allow rebinding after last consumer) — only
   if corpus census shows it matters; dataflow judgment = heavy.
6. Q3 two-branch sink returns (detached from growth-8; buys little).
7. class-defs/dataclass modeling (batch-D rq2's real wall).

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
