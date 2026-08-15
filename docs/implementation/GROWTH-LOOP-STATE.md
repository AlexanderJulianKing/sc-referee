# Growth-loop living state (maintained by the orchestrator, every iteration)

Updated: 2026-08-15 (handoff from the Fable orchestrator session).

## Scoreboard

- 84 lifetime blind free-form cases (batches A-I under
  evaluation/development/dependence-growth-loop/), ZERO false accusations, zero
  regressions. 83 measurable (batch-D case dc2b31d5 was intake-refused, never
  materialized). No blind catch yet; misses are honest named abstentions.
- Six demonstrated false-accusation routes killed in review before measurement
  (filter-predicate, paired/crossover, alias-then-mutate, counted-domain, AnnAssign
  rebind, plain-Assign rebind). The plain-Assign fix is structural (operand-name-rebound,
  all assignment forms through one partition test).
- v1.1.0 qualified detector + installed pins: untouched and live throughout.

## In flight at handoff

- Growth-9 build (G9-L vocabulary: builtins dict/any/all/tuple, reader-form
  [dict(row) for row in csv.DictReader(handle)], list-literal string constants;
  G9-H: argument-expression hoisting with refuse-at-binding container rule) +
  wall-mining corpus harness (scripts/wall_mining_corpus.py) + batch J configs
  (j1: opus-111..116/fable-44,45/opus-27; j2: opus-117..122/fable-46,47/opus-28,
  ready-but-unrun; checkpoint cadence). Fresh-session build launched from the
  implementer brief; on completion: full-suite gate, commit+manifest, push, fresh
  reviewer code review with probes, then first corpus census run.

## Heavy queue (evidence-ranked; measure premises before designing)

1. Paired-procedure family (ttest_rel/wilcoxon lock gap; recurring since batch C) —
   maintainer go-ahead required (different independence semantics = new claim shape).
2. Numeric comparison predicates for counts (float(row[x]) > CONST; batch-B 446cab
   flagship + recurring).
3. raise/validation guards inside helpers (part of the globals-read decomposition).
4. Position-sensitive rebind relaxation (allow rebinding after last consumer) — only
   if corpus census shows it matters; dataflow judgment = heavy.
5. Q3 two-branch sink returns (detached from growth-8; buys little).
6. class-defs/dataclass modeling (batch-D rq2's real wall).

## Actor inventory (one-use identities; continue numbering)

Authors spent through opus-110; blind reviewers through fable-43; hostile reviewers
interleaved (fable odd/even per envelope config); escalation through opus-26.
Batch J seats reserved above. Blind-batch seats may move to codex-cli transports
(model change is a harness config change: review it).

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
