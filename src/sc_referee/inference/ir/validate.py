from __future__ import annotations


def validate_program(program) -> None:
    block_ids = set(program.cfg.blocks)
    for block in program.cfg.blocks.values():
        unknown = (set(block.successors) | set(block.exceptional_successors)) - block_ids
        if unknown:
            raise ValueError(f"CFG contains unknown successors: {sorted(unknown)}")
    identifiers = [instruction.id for block in program.cfg.blocks.values()
                   for instruction in block.instructions]
    identifiers += list(program.value_definitions) + list(program.memory_versions)
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("IR identifiers are not unique")

