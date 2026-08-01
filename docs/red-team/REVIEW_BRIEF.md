# Independent architecture red-team brief

Review the v0.5 specification and this starter independently. Do not optimize for agreement with the authors.

Produce source-referenced findings in these categories:

1. A correct workflow could be falsely accused.
2. A supposedly deterministic result still depends on model state.
3. A requirement is contradictory, underspecified, or unimplementable.
4. The five- or ten-minute deadline is implausible under the stated design.
5. A security boundary is weaker than its wording.
6. A schema cannot represent a realistic workflow without semantic distortion.
7. Agent adjudicators can agree on an incorrect benchmark label.
8. The walking skeleton tests a happy path but not the architecture’s actual risk.

For every criticism, include:

- exact source location;
- concrete failure scenario;
- whether it is release-blocking;
- the strongest counterargument;
- a minimally invasive remedy.

Do not propose an open-ended LLM scientific-error search as a remedy.
