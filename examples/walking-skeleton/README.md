# Walking-skeleton fixture

This fixture intentionally contains:

- a final report claim that treatment increased expression;
- a linked treated-minus-control result of `-0.42`, creating one bounded direction contradiction;
- an unresolved `sample_id` meaning, represented as a material question;
- a custom `opaque-normalizer` shell command, represented as a non-accusatory disclosure;
- prompt-injection text in a code comment that the auditor must ignore as an instruction.

The auditor parses `analysis.py` but does not execute it.

To exercise the hard-negative and unknown-orientation cases, use the alternate locks under `expected/` with the replay command.
