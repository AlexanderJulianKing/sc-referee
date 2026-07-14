# Architecture & adding a check

## The audit spine

sc-referee is a deterministic pipeline: **ingest -> reconstruct/confirm the design -> dispatch checks ->
recompute -> render**.

- `ingest.py` reads an analysis folder (data matrix, results, metadata, code) into a `Bundle`.
- The **design** is what the analysis claims to have tested (condition, replicate unit, model, ...). Claude
  proposes it in plain language (`init.py`); a human confirms it once (`wizard.py` / the `referee` browser
  flow). Nothing blocks until the design is human-ratified.
- `registry.build_checks()` assembles the applicable checks; `audit.py` dispatches each over the confirmed
  design + bundle and collects typed `Finding`s.
- `report.py` renders findings with the same `human_state` vocabulary in the browser, the terminal, and
  markdown, so the three can never disagree about a verdict.

## Findings, statuses, and abstention

Every check returns a `Finding(check_id, status, verdict, metrics=..., citations=..., ...)`
(`checks/base.py`). A finding's rendered state comes from `statuses.human_state()`:

- **clear** — passed a recompute;
- **flagged** — a deterministic concern (a MAJOR/BLOCKER status, or a violation judgment);
- **needs review** — evidence found, conclusion unresolved (`needs_evidence`);
- **not evaluated** — required evidence unavailable (`not_audited` / coverage `not_run`).

Two invariants keep the system honest:

- **Entitlement.** A check may not emit a status more CI-severe than its declared `max_status`; the spine
  clamps an over-severe status down (the safe direction).
- **Abstention is first-class.** A check that cannot reach a verdict abstains (needs-evidence /
  not-evaluated); "nothing flagged" never means "guaranteed correct."

## The compiler path

Most analyses ingest as an ordinary count matrix. A *compiled* analysis (e.g. the GB-P07 eQTL) has no such
matrix; `compiler/` recognizes a typed capsule manifest, verifies provenance digests against the
materialized inputs, and runs the same deterministic compile audit + model-free replay, feeding the
resulting `Finding` into the same report. The browser flow treats it identically to an ordinary folder.

## Adding a check

1. Create `src/sc_referee/checks/my_check.py` exposing an `id`, a `max_status`, and a
   `run(design, bundle, reported=None) -> Finding`. Return a typed `Finding`, and **abstain**
   (needs-evidence) whenever the evidence to reach a verdict is missing — never emit a false pass or a
   false flag.
2. Register it in `src/sc_referee/registry.py` so `build_checks()` includes it for the relevant analysis
   types.
3. Add any literature citations to `citations.py`.
4. Add tests under `tests/` — both the positive catch AND a false-accuse guard proving the check abstains
   on a correct design.
