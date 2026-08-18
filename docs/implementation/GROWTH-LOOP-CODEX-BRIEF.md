# Growth-loop implementer brief (Codex)

Fresh-session brief for building dependence recognizer v2 growth rounds. Read this,
the current design memo (path given in your task), and EXPERIMENT-0060 before coding.
Branch: dev/dependence-growth. The orchestrator commits; never touch .git.

## Architecture in one paragraph

src/sc_referee/dependence_recognition_v2/ is an UNREGISTERED development shadow
recognizer (propose-then-verify: python_analyzer.py proposes, certificate.py's kernel
independently re-derives everything from the flattened module and frozen CSV bytes;
ir.py carries shapes; the adapter is reached ONLY via the development harness in
evaluation/src/sc_referee_evaluation/lean_pipeline.py + scripts/lean_pipeline.py
envelope configs). Pipeline: inline-first (alpha-renaming flattener, call-path evidence,
acyclicity), partition-second (ONE kernel-re-derived operand/sink classification over
flattened statements). Locks: authority/locks-v2/ per-case, deterministic role-blind
translation from the author's data-description declarations.

## Frozen surfaces (any byte change = build failure)

The six v1 files under src/sc_referee/dependence_recognition/, EXPERIMENT-0058,
registry.json, grant-set.json, method_conflict_grant_pins.py, capability matrix,
qualification records, all frozen lanes under evaluation/development/ and
evaluation/qualification/, public docs. Installed pins must stay live (tests enforce).

## Standing constraints

- Never widen beyond the memo; where memo sections conflict, later amendments win.
  List underspecified decisions explicitly; never improvise wider.
- Exactly ONE operand classification; anything needing a second closure or a new
  class-inheritance relation: STOP and report for a design round.
- Every abstention route gets a specific named reason (no catch-alls); extend the
  canonical reason registry + its equality test.
- Fixtures execute in the pinned sandbox and assert OBSERVED outcomes (full sorted
  reason sets), never widened to pass. Reviewer probes from the round become fixtures.
- Pinned development runtimes are immutable inputs, not fallback tooling environments.
  Execute only a runtime explicitly assigned by the memo/prompt, only through its
  bound isolated launcher, with both `-B` and `PYTHONDONTWRITEBYTECODE=1`; validate its
  exact manifest before and after. Never probe, import, install, or compile inside a
  concurrent track's runtime. Generic dependency/tool discovery uses the repository
  environment.
- Frozen-corpus re-measure (all batches) after grammar changes; report movements.
- Development-loop gating: harness behavior changes gate on config.development_loop;
  qualification envelopes stay byte-identical in behavior.

## Commands

Focused: PYTHONPATH=.:src:evaluation/src .venv/bin/python -m pytest -q
tests/test_dependence_recognition_v2*.py tests/test_dependence_free_envelope.py
tests/test_release_identity.py — plus scoped ruff/mypy (mypy src). Full suite is the
orchestrator's. MANIFEST.sha256: regenerate via scripts/build_manifest.py LAST; new
untracked files enter it only after the orchestrator's commit (known one-commit lag).

## Report format

Files changed; exact pytest output lines; fixture outcome tables (observed);
re-measure movement table; narrow decisions listed; nothing widened.
