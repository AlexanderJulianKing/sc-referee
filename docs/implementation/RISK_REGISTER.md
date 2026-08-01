# Implementation risk register

| Risk | Trigger | Consequence | Required mitigation |
|---|---|---|---|
| False accusation | Correct workflow admitted as a Finding | Loss of scientific trust | Hard negatives, bounded wording, admission gate, permanent regression fixture |
| LLM semantic drift | Repeated extraction changes a material premise | Nondeterministic or incorrect Finding | Exact evidence, independent verification, explicit unknowns, no model after lock |
| Architecture overreach | Broad domain work begins before the skeleton works | Delayed feedback and coupled design | Enforce Milestone 0 cut and task order |
| Runtime blowup | Whole repository repeatedly sent to a model | Deadline failure | Backward slicing, bounded packets, caching, partial reports |
| Dynamic-language blind spot | Parser guesses `eval`, dispatch, generated code, or tidy evaluation | Incorrect lineage or applicability | Opaque operation and explicit parser coverage |
| Unsafe execution | Static inspection imports or executes project code | Host compromise or exfiltration | Static reads only; rootless OCI for later authorized execution |
| Prompt injection | Repository text directs the agent to bypass policy | Policy or permission bypass | Treat repository content as evidence; adversarial tests |
| Wrong publication surface | Obsolete report selected | Misattached findings | Explicit-evidence precedence and material question |
| Cache contamination | Source-derived cache crosses projects | Privacy leak or stale semantics | Project-local content-addressed cache |
| Agent consensus error | Multiple adjudicators repeat the same mistake | Invalid qualification label | Cross-provider review, deterministic checks, disagreement exclusion |
| Schema drift | Code emits shapes not represented by public schema | Invalid bundles | Provisional namespace, schema-gap register, promotion ADR |
| Weak data identity | A path changes underneath the audit | False reproducibility | Tiered identity and evidence ceilings |
| Workspace mutation | Run combines different file versions | Incoherent evidence | Immutable snapshot and divergence disclosure |
| Capability overclaim | Parsing is described as scientific validation | User overtrust | Generated multidimensional capability matrix |
