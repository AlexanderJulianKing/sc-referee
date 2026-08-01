# W3ID registration status

**Design decision:** canonical schema identifiers use immutable versioned paths under `https://w3id.org/sc-referee/schema/`.

**Current package status:** the local schemas and examples use that namespace consistently, but this package does not establish that the corresponding W3ID redirects have been registered or resolve remotely.

Before a public schema release, maintainers must:

1. register or update the W3ID redirect configuration;
2. verify that every published versioned schema identifier resolves to the exact immutable schema bytes or a stable representation of them;
3. verify redirects from a clean external environment;
4. record the redirect configuration revision and resolution test results; and
5. retain old versioned redirects indefinitely.

A `latest` path may be offered for human navigation but must never be persisted in audit records.
