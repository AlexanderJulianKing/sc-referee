# sc-referee specification package

**Version:** 0.5.0-draft

This package is the modular product, architecture, schema, runtime, security, detector, evaluation, and implementation specification for **sc-referee**, a conservative scientific-analysis auditor invoked in Claude Code as `/scientific-audit`.

The project name continues the original Claude Life Sciences hackathon prototype. Version 0.4 established the public identity, W3ID schema namespace, licensing, detector governance, Python and R parser stacks, canonical storage, report renderer, sandbox backend, cache boundary, and repository-mutation behavior.

## Review entry points

- `MASTER_SPEC.html` — rendered reading copy.
- `MASTER_SPEC.md` — consolidated Markdown.
- `sc-referee-specification-v0.5.0.docx` — Word review copy.
- `DECISIONS_v0.5.md` — accepted decisions in this round.
- `docs/12-open-decisions.md` — remaining unresolved decisions.
- `ACCEPTANCE_CRITERIA.md` — executable product gates.
- `references/schema-package-v0.5.0/` — matching schema baseline.

The modular Markdown chapters, ADRs, accepted decision log, and machine registers are the editing source of truth. Consolidated Markdown, HTML, and DOCX are generated review views.

## Public-release prerequisite

The v0.5 schemas use the accepted W3ID namespace locally. Remote W3ID redirect registration and external resolution testing remain pending and must pass AC-52 before the schema package is published as a stable release. See `references/W3ID_REGISTRATION.md`.
