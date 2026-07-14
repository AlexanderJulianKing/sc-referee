"""Forward worklist solving with delayed widening and explicit loop-must discipline."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable, Generic, Mapping, TypeVar

from sc_referee.inference.domains.bilattice import MayMust

S = TypeVar("S")


@dataclass(frozen=True)
class FixpointResult(Generic[S]):
    states: Mapping[str, S]
    widened_points: frozenset[str]
    narrowed_points: frozenset[str]
    steps: int


def solve(*, successors: Mapping[str, tuple[str, ...]], entry: str, initial: S,
          transfer: Callable[[str, S], S], join: Callable[[S, S], S],
          widen: Callable[[S, S], S], growth_before_widen: int = 2,
          max_steps: int = 10000,
          narrow: Callable[[str, S], S] | None = None) -> FixpointResult[S]:
    states: dict[str, S] = {entry: initial}
    growth: dict[str, int] = {}
    widened_points: set[str] = set()
    worklist = deque([entry])
    steps = 0
    while worklist:
        block = worklist.popleft()
        steps += 1
        if steps > max_steps:
            raise RuntimeError("fixpoint resource limit exhausted")
        outgoing = transfer(block, states[block])
        for successor in successors.get(block, ()):
            if successor not in states:
                states[successor] = outgoing
                worklist.append(successor)
                continue
            previous = states[successor]
            candidate = join(previous, outgoing)
            if candidate == previous:
                continue
            count = growth.get(successor, 0) + 1
            growth[successor] = count
            if count > growth_before_widen:
                candidate = widen(previous, candidate)
                widened_points.add(successor)
            if candidate != previous:
                states[successor] = candidate
                worklist.append(successor)
    narrowed_points = set()
    if narrow is not None:
        for block, state in tuple(states.items()):
            candidate = narrow(block, state)
            if candidate != state:
                states[block] = candidate
                narrowed_points.add(block)
    return FixpointResult(dict(states), frozenset(widened_points),
                          frozenset(narrowed_points), steps)


def loop_may_must(pre: MayMust, body: MayMust, *, at_least_one_iteration: bool,
                  preserved: bool) -> MayMust:
    may = pre.may | body.may
    if at_least_one_iteration and preserved:
        must = pre.must | body.must
    elif preserved:
        must = pre.must
    else:
        must = frozenset()
    return MayMust(frozenset(may), frozenset(must))
