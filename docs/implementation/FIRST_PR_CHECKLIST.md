# First implementation PR checklist

- [ ] Ran the existing tests before changes.
- [ ] Selected the earliest incomplete task from the task board.
- [ ] Added an executable test for every claimed behavior.
- [ ] Did not broaden detector, parser, execution, or domain scope unnecessarily.
- [ ] Did not introduce model calls into deterministic modules.
- [ ] Did not introduce project-code execution.
- [ ] Preserved separate Finding, ConditionalConcern, MaterialQuestion, and Disclosure semantics.
- [ ] Preserved no-correctness-certificate report language.
- [ ] Validated generated public records against v0.5 schemas.
- [ ] Documented any provisional-schema or architecture gap.
- [ ] Updated task and acceptance status.
- [ ] Left `pytest` and `python scripts/validate_starter.py` green.
