# sc-referee schema package

**Version:** 0.5.0

This package defines typed evidence, control, semantic, assessment, parser, execution-capability, cache, performance, and detector-qualification records for **sc-referee** using JSON Schema Draft 2020-12.

Version 0.5.0 continues the public `sc-referee` identity and immutable canonical namespace established in 0.4.0:

```text
https://w3id.org/sc-referee/schema/v0.5.0/
```

## Epistemic taxonomy

- `Finding` means a demonstrated, narrowly bounded issue.
- `ConditionalConcern` states a possible issue only if an explicit unresolved premise is true.
- `MaterialQuestion` records scientific meaning that can change the audit.
- `Disclosure` records coverage, lineage, opacity, evidence, or reproducibility limitations without alleging a defect.

There is no public `supported` tier, generic production hypothesis record, numerical finding confidence, pass state, or global risk score.

## New in 0.5.0

- `AgentReview` records pinned model, agent, prompt, tool-policy, environment, blindness, transcript, verdict, and evidence for one independent review run.
- `BenchmarkAdjudication` requires a cross-provider, multi-run, two-stage protocol, requires Stage-2 falsification attempts, and forbids majority vote from overriding material disagreement.
- The initial reference pair is Claude Code with Claude Opus 5 and Codex with GPT-5.6 Sol; exact identifiers are pinned per run and may evolve through a versioned protocol.
- `BenchmarkFixture` distinguishes `verified_good_fixture`, `scope_verified_good`, `hard_negative_fixture`, positive, and ambiguous cases.
- `CapabilityMatrix` expresses narrow versioned capability envelopes and prohibits domain-wide support claims.
- `ROCrateExport` packages the native audit bundle using RO-Crate 1.3 while leaving sc-referee records canonical.
- Detector qualification now supports agent-panel, mixed, or human review bases and makes agent-only qualification explicit.
- Promotion safety gates are structural now; universal numerical cutoffs remain deferred until a pilot corpus supports a separate threshold ADR.

## Validation

```bash
python tools/validate_records.py examples
pytest -q
```

The schemas validate record shape and selected within-record invariants. Graph reachability, source resolution, reviewer independence and provider participation across linked records, SQLite rebuild equivalence, rootless-runtime verification, finite counterevidence completeness, and scientific detector validity remain deterministic controller responsibilities.
