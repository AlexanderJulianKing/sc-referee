# Growth-loop living state (maintained by the orchestrator, every iteration)

Updated: 2026-08-15 (Growth-10 resumed by explicit maintainer authorization).

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

## In flight

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

1. Paired-procedure family (ttest_rel/wilcoxon lock gap; recurring since batch C) —
   maintainer go-ahead required (different independence semantics = new claim shape).
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
