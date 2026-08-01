# Accepted decisions in specification 0.4.0

This revision incorporates the implementation-foundation review while retaining every accepted v0.2 and v0.3 scientific, runtime, security, and causal policy.

## Product and distribution

- The project is named **sc-referee**, continuing the Claude Life Sciences hackathon prototype identity.
- Repository, distribution, and CLI use `sc-referee`; Python imports use `sc_referee`; the Claude command remains `/scientific-audit`.
- Canonical schemas use immutable `https://w3id.org/sc-referee/schema/v0.4.0/` identifiers.
- Original project code, schemas, documentation, templates, and original fixtures use Apache License 2.0; external benchmark derivatives retain source-specific terms.

## Governance

- Experimental detectors require maintainer review and fixtures.
- Validated promotion requires one maintainer and one independent qualified scientific reviewer.
- Publication-grade promotion requires one maintainer and two independent scientific reviewers including domain expertise.
- Detector authors cannot satisfy independent-review roles, every promotion has a public qualification report, and emergency demotion is immediate.

## Implementation foundations

- Python 3.11 is the minimum runtime.
- JSON and JSONL are canonical; safe YAML is editable; SQLite is disposable and generated.
- Python parsing uses CPython `ast` plus `tokenize`.
- R parsing uses Tree-sitter-R and a non-evaluating base-R parser helper when available.
- Human reports use self-contained, autoescaped static Jinja2 HTML.
- Project-code execution requires a capability-reported rootless OCI backend; no subprocess-only fallback is allowed.
- Source-derived caches are project-local in version one.
- Live workspace edits mark `workspace_diverged`; the run remains bound to its initial immutable snapshot.


## Operational release status

The W3ID namespace decision is accepted. Registration and remote-resolution testing are separate release prerequisites and remain pending in this draft; local schema validation cannot establish them.
