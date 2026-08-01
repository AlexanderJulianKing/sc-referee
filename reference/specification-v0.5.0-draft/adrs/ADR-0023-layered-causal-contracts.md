# ADR-0023: Use layered causal contracts with optional scoped causal structure

## Status

Accepted.

## Context

Requiring a complete DAG for every causal claim is burdensome and can create false precision. Omitting causal structure entirely prevents legitimate estimand and adjustment checks.

## Decision

Every explicitly causal claim has a typed claim-intent, target-estimand, and identification contract. Covariate roles are estimand-scoped. A causal graph is optional and declares partial_open_world, complete_for_named_query, or closed_world scope. Graph-dependent detectors abstain when required structure is absent. Model-invented causal relations cannot support Findings. See SA-FR-019, SA-FR-077, and SA-FR-078.

## Consequences

- Narrow causal mismatches can be detected without a complete graph.
- Adjustment-set sufficiency cannot be claimed from missing structure.
- Scientist assumptions are evaluated for implementation consistency, not certified as biological truth.
