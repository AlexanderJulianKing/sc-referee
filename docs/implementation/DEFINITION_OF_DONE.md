# Definition of done

A task is done when:

- behavior is covered by tests;
- deterministic outputs are normalized and stable;
- errors and abstentions are typed rather than logged only as prose;
- source locations resolve against the immutable snapshot;
- no new Finding path bypasses the admission function;
- report wording is controlled by assessment type;
- coverage is updated;
- documentation and task-board status are updated;
- no architecture or schema conflict is hidden.

Milestone 0 is done only when a clean environment can run the demo and replay, and the contradiction, hard-negative, unknown, opaque, prompt-injection, deadline, and SQLite-rebuild tests all pass.
