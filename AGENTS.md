# AGENTS.md

## Mission

Implement sc-referee as an evidence compiler that localizes demonstrated scientific-analysis issues while minimizing false accusations.

## Authority order

When instructions conflict, use this order:

1. Accepted ADRs and normative requirements in `reference/specification-v0.5.0-draft/`.
2. Current accepted public JSON Schemas in `reference/schemas-v0.18.0/`; older accepted versions
   remain immutable migration baselines.
3. `docs/implementation/MILESTONE_0_BUILD_SPEC.md`.
4. Other implementation-overlay documents.
5. Existing scaffold code.

Record unresolved conflicts in `docs/implementation/SCHEMA_GAP_REGISTER.md`; do not silently choose.

## Non-negotiable epistemic rules

- `Finding` means demonstrated issue only.
- Every Finding must satisfy direct entailment, no reversing unknown, exact applicability, completed finite counterevidence checks, bounded wording, and deterministic replay.
- Explicit literal model extraction may be used only when independently checkable and non-model verified.
- Implicit scientific interpretation requires authoritative corroboration.
- Open-ended LLM issue hunting is outside the production path.
- Conditional, unresolved, unsupported, and opaque cases are not Findings.
- No global pass, risk rating, publication-ready state, or correctness certificate.

## Engineering rules

- Python 3.11+.
- Strict type checking for core interfaces.
- Canonical JSON/JSONL; YAML only for human-editable policy and answers.
- SQLite is generated and disposable.
- No hidden global state in deterministic logic.
- Normalize and hash every model prompt and work packet.
- Localize parser failure; never fail the whole run for one unsupported file.
- Keep source-derived caches project-local.
- Maintain an immutable initial snapshot and mark live workspace divergence.
- The production MPP does not execute project-authored code. Any post-MPP execution adapter still
  requires explicit authorization, a qualifying rootless OCI backend, and the unresolved closure
  and trusted-probe gates; there is no unsafe fallback.
- Add tests before or with behavior changes.

## Required commands before completing work

```bash
ruff check .
ruff format --check .
mypy src
pytest
python scripts/validate_starter.py
```

## Change discipline

A change that alters record meaning, Finding eligibility, authority, execution privilege, or public capability claims requires an ADR or an explicit temporary-experiment record. Do not hide a policy change in code.
