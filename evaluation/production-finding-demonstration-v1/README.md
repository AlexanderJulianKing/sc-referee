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

Recorded at `2026-08-11T19:53:52Z` by AuditRun `audit:51deeeb2a09c48aab25daeb9a1eb80a3`.

### Finding text as published

**Selected method declaration conflicts with the review requirement**

For this selected analysis, the binding-required selected-report evidence declares 'retained_observed_subset_exposure_only', while the scope-bound scientist Answer requires 'complete_declared_domain_exposure'. Those exact operands differ. This does not establish that the source ran, that the difference caused a numerical error, or that the required operand is universally correct.

**Severity:** moderate — The selected analysis declaration conflicts with one exact pre-authorized review requirement; numerical and broader scientific consequences were not established.

**Publication materiality:** local — The demonstrated conflict is localized to the exact selected publication surface and is not projected to other claims or analyses.

**Next action:** Align the selected analysis with the governing requirement or document an authorized amendment and re-audit.

### Authority chain

1. Sealed examination: [`evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/heldout-v207-seven-case/HELDOUT_OPENING.json`](../../evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/heldout-v207-seven-case/HELDOUT_OPENING.json) and [`evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/heldout-v207-seven-case/detector-run/DETECTOR_RUN_LEDGER.json`](../../evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/heldout-v207-seven-case/detector-run/DETECTOR_RUN_LEDGER.json).
2. Promotion decision: [`docs/implementation/ADR-0071-COMPLETE-DOMAIN-ENVELOPE-PROMOTION.md`](../../docs/implementation/ADR-0071-COMPLETE-DOMAIN-ENVELOPE-PROMOTION.md).
3. Installed qualification: `qualification:complete-domain-exposure-denominator-v207-round2` at `sha256:caedfac75ba4a28ffa0ae81488d022b984bca782c9411fc43938b9ce812b4e0e` with metric set `qualification-metric-set:329715c3cf01ed499eb5` at `sha256:6be79a7a0f1260c984664909fe709f28b63c1163e6ef548e5faf3c03654ff98f`.
4. Installed external pin: binding `method-conflict-binding:complete-domain-exposure-denominator-v1` at `sha256:0f59ece664acbc541006037fbfc8518c21e8fee9768ed47a651f6532226950f9`, detector manifest `sha256:a5b089be6a18b220f56fd345450912a3aa7ee3e132ff519117b879cee8e72c41`.
5. Controller run: [`complete-domain/error/audit/audit.bundle.json`](complete-domain/error/audit/audit.bundle.json), replayed at [`complete-domain/error/replay/audit.bundle.json`](complete-domain/error/replay/audit.bundle.json).

The matched control twin is committed at [`complete-domain/control/`](complete-domain/control/) and produced zero Findings through the same contract, audit, policy, and replay path.

## dependence

Recorded at `2026-08-11T19:53:55Z` by AuditRun `audit:8f9deb23913e432fb0273aafca0582d4`.

### Finding text as published

**Selected method declaration conflicts with the review requirement**

For this selected analysis, the binding-required exact-scope static-source evidence declares 'multiple_analyzed_rows_per_authorized_independent_unit', while the scope-bound scientist Answer requires 'one_analyzed_row_per_authorized_independent_unit'. Those exact operands differ. This does not establish that the source ran, that the difference caused a numerical error, or that the required operand is universally correct.

**Severity:** moderate — The selected analysis declaration conflicts with one exact pre-authorized review requirement; numerical and broader scientific consequences were not established.

**Publication materiality:** local — The demonstrated conflict is localized to the exact selected publication surface and is not projected to other claims or analyses.

**Next action:** Align the selected analysis with the governing requirement or document an authorized amendment and re-audit.

### Authority chain

1. Sealed examination: [`evaluation/qualification/authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-direct-lane/heldout-seven-case/opening/DEPENDENCE_HELDOUT_OPENING.json`](../../evaluation/qualification/authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-direct-lane/heldout-seven-case/opening/DEPENDENCE_HELDOUT_OPENING.json) and [`evaluation/qualification/authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-direct-lane/heldout-seven-case/detector-run/DETECTOR_RUN_LEDGER.json`](../../evaluation/qualification/authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-direct-lane/heldout-seven-case/detector-run/DETECTOR_RUN_LEDGER.json).
2. Promotion decision: [`docs/implementation/ADR-0073-DEPENDENCE-ENVELOPE-PROMOTION.md`](../../docs/implementation/ADR-0073-DEPENDENCE-ENVELOPE-PROMOTION.md).
3. Installed qualification: `qualification:authorized-independent-unit-entry-v110-round2` at `sha256:a3c0ebebde92bfff4e7eacff8427d944d7a3f33b43b206fc071e4d85c37d3b3d` with metric set `qualification-metric-set:81c3713d3b6e81d999de` at `sha256:8469007a7067cbc6ca49a8c8672e9771d61ae2df5a1eb34086992eae53c03c99`.
4. Installed external pin: binding `method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1` at `sha256:f58801cd66b18487da2d33ab2f424392b2d64bf84697ccd336de6ef8ba2cda1b`, detector manifest `sha256:a5b089be6a18b220f56fd345450912a3aa7ee3e132ff519117b879cee8e72c41`.
5. Controller run: [`dependence/error/audit/audit.bundle.json`](dependence/error/audit/audit.bundle.json), replayed at [`dependence/error/replay/audit.bundle.json`](dependence/error/replay/audit.bundle.json).

The matched control twin is committed at [`dependence/control/`](dependence/control/) and produced zero Findings through the same contract, audit, policy, and replay path.

## Scope

These are canonical demonstrations of two already-qualified, exact envelopes. They are not new
qualification cases, do not enlarge either recognition grammar, and make no claim about code
execution, numerical causality, bias direction, or scientific correctness outside each Finding's
stated scope.
