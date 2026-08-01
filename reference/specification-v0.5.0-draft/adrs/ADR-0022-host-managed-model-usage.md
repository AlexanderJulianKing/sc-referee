# ADR-0022: Impose no auditor-specific numeric model-call or token cap

## Status

Accepted.

## Context

Fixed call quotas can terminate useful extraction for arbitrary reasons and are redundant with a strict elapsed deadline. Users may operate under different Claude subscriptions or organization policies.

## Decision

Default auditor call and token limits are null. Host limits remain authoritative. Usage is packetized, deduplicated, recorded, and bounded by the hard elapsed deadline. Host exhaustion yields a partial audit. See SA-FR-052 and SA-FR-079.

## Consequences

- The auditor does not artificially underuse a subscription.
- Cost and usage remain measurable.
- “Uncapped” does not authorize open-ended issue search or irrelevant calls.
