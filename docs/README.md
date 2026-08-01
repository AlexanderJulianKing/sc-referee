# sc-referee documentation

Start with the guide that matches what you are trying to do:

| Goal | Guide |
|---|---|
| Run a first audit and understand its output | [Quickstart](QUICKSTART.md) |
| Let Codex or Claude Code perform the bounded audit workflow | [Agentic skill](AGENTIC_SKILL.md) |
| Check whether a scientific method or file form is currently covered | [Capabilities](CAPABILITIES.md) |
| Move from the earlier public implementation to this overhaul | [Migration](MIGRATION.md) |
| Cite the software | [Citation metadata](../CITATION.cff) |
| Review human authorship and AI assistance | [Acknowledgments](../ACKNOWLEDGMENTS.md) |

The files under [`implementation/`](implementation/) are engineering records: accepted ADRs,
experiment reports, schema decisions, qualification evidence, and task history. They are retained
for auditability, but a new user should not need to read them before running the program.

The normative specification and immutable schema packages are under [`../reference/`](../reference/).
When a short user guide and an accepted ADR or schema disagree, the accepted ADR or schema wins.
