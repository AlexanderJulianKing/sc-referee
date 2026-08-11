# First production Finding demonstrations

This directory records the first production-authorized Findings published by `sc-referee` for
the two exact binding-scoped grants installed under ADR-0075. Both positive workflows and both
matched control twins were passed through the real `run_audit` controller path. The controller
did not execute project-authored code. Each committed replay reproduces the original detector
results, Findings, and coverage record.

The timestamps below are **recorded, not declared**: the builder accepts no timestamp argument and
copies each value from the controller-created AuditRun. `DEMONSTRATION_RECORD.json` binds the
project bytes, audit bundle, semantic lock, replay bundle, installed grant identities, and exact
published wording. This directory's `MANIFEST.sha256` closes every committed file except itself.

## complete-domain

Recorded at `2026-08-11T09:32:57Z` by AuditRun `audit:802f4185e11e4f6cbb6d02453b026311`.

### Finding text as published

**Selected method declaration conflicts with the review requirement**

For this selected analysis, the binding-required selected-report evidence declares 'retained_observed_subset_exposure_only', while the scope-bound scientist Answer requires 'complete_declared_domain_exposure'. Those exact operands differ. This does not establish that the source ran, that the difference caused a numerical error, or that the required operand is universally correct.

**Severity:** moderate — The selected analysis declaration conflicts with one exact pre-authorized review requirement; numerical and broader scientific consequences were not established.

**Publication materiality:** local — The demonstrated conflict is localized to the exact selected publication surface and is not projected to other claims or analyses.

**Next action:** Align the selected analysis with the governing requirement or document an authorized amendment and re-audit.

### Authority chain

1. Sealed examination: [`evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/heldout-v207-seven-case/HELDOUT_OPENING.json`](../../evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/heldout-v207-seven-case/HELDOUT_OPENING.json) and [`evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/heldout-v207-seven-case/detector-run/DETECTOR_RUN_LEDGER.json`](../../evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/heldout-v207-seven-case/detector-run/DETECTOR_RUN_LEDGER.json).
2. Promotion decision: [`docs/implementation/ADR-0071-COMPLETE-DOMAIN-ENVELOPE-PROMOTION.md`](../../docs/implementation/ADR-0071-COMPLETE-DOMAIN-ENVELOPE-PROMOTION.md).
3. Installed qualification: `qualification:complete-domain-exposure-denominator-v207-round2` at `sha256:3a44dbdb144c152b7185c0dccc6bf855346093341324acfd443689982dd02dbe` with metric set `qualification-metric-set:cbb01f0b08e407f6a4f8` at `sha256:50fda7205c683b49fc42351de25c7b98a46bd8ef62b7ca9379703c55e12e67a1`.
4. Installed external pin: binding `method-conflict-binding:complete-domain-exposure-denominator-v1` at `sha256:d67b3bb459c32f84f4d920cffc9b56ab68d96741932bf3771926070342ff94e2`, detector manifest `sha256:9c6270f47a2ab2d2a75183a9e4a2d2a955974e5968bacc2ba75778a1ae8ab3fb`.
5. Controller run: [`complete-domain/error/audit/audit.bundle.json`](complete-domain/error/audit/audit.bundle.json), replayed at [`complete-domain/error/replay/audit.bundle.json`](complete-domain/error/replay/audit.bundle.json).

The matched control twin is committed at [`complete-domain/control/`](complete-domain/control/) and produced zero Findings through the same contract, audit, policy, and replay path.

## dependence

Recorded at `2026-08-11T09:33:00Z` by AuditRun `audit:0aa4317772af43deb9d32f5d9e59a68a`.

### Finding text as published

**Selected method declaration conflicts with the review requirement**

For this selected analysis, the binding-required exact-scope static-source evidence declares 'multiple_analyzed_rows_per_authorized_independent_unit', while the scope-bound scientist Answer requires 'one_analyzed_row_per_authorized_independent_unit'. Those exact operands differ. This does not establish that the source ran, that the difference caused a numerical error, or that the required operand is universally correct.

**Severity:** moderate — The selected analysis declaration conflicts with one exact pre-authorized review requirement; numerical and broader scientific consequences were not established.

**Publication materiality:** local — The demonstrated conflict is localized to the exact selected publication surface and is not projected to other claims or analyses.

**Next action:** Align the selected analysis with the governing requirement or document an authorized amendment and re-audit.

### Authority chain

1. Sealed examination: [`evaluation/qualification/authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-direct-lane/heldout-seven-case/opening/DEPENDENCE_HELDOUT_OPENING.json`](../../evaluation/qualification/authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-direct-lane/heldout-seven-case/opening/DEPENDENCE_HELDOUT_OPENING.json) and [`evaluation/qualification/authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-direct-lane/heldout-seven-case/detector-run/DETECTOR_RUN_LEDGER.json`](../../evaluation/qualification/authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-direct-lane/heldout-seven-case/detector-run/DETECTOR_RUN_LEDGER.json).
2. Promotion decision: [`docs/implementation/ADR-0073-DEPENDENCE-ENVELOPE-PROMOTION.md`](../../docs/implementation/ADR-0073-DEPENDENCE-ENVELOPE-PROMOTION.md).
3. Installed qualification: `qualification:authorized-independent-unit-entry-v110-round2` at `sha256:a9114559f7b4ba0b75d704f0b6ba746e2150a8cb32da0cf3e8a9e975c541f9ba` with metric set `qualification-metric-set:ca098eea52a6cb1d4e62` at `sha256:27ac7cc5d1112661cef27a88694fef711f62877213f791e44a614ff52953f1ed`.
4. Installed external pin: binding `method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1` at `sha256:56e8ccdef15d3c2371864e02cab92becb0c6859091ee782c94be2ac9b4b1a43d`, detector manifest `sha256:9c6270f47a2ab2d2a75183a9e4a2d2a955974e5968bacc2ba75778a1ae8ab3fb`.
5. Controller run: [`dependence/error/audit/audit.bundle.json`](dependence/error/audit/audit.bundle.json), replayed at [`dependence/error/replay/audit.bundle.json`](dependence/error/replay/audit.bundle.json).

The matched control twin is committed at [`dependence/control/`](dependence/control/) and produced zero Findings through the same contract, audit, policy, and replay path.

## Scope

These are canonical demonstrations of two already-qualified, exact envelopes. They are not new
qualification cases, do not enlarge either recognition grammar, and make no claim about code
execution, numerical causality, bias direction, or scientific correctness outside each Finding's
stated scope.
