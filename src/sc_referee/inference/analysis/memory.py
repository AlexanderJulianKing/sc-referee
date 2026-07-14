"""May-points-to memory with literal fields, strong/weak updates, and opaque-call havoc."""
from __future__ import annotations

from dataclasses import dataclass

from sc_referee.inference.domains.bilattice import MayMust
from sc_referee.inference.domains.effects import EffectValue
from sc_referee.inference.domains.origin import unknown_origin
from sc_referee.inference.domains.value import AbsValue


@dataclass
class MemoryCell:
    value: AbsValue
    definitions: MayMust[str]


class AbstractHeap:
    def __init__(self):
        self._locations: set[str] = set()
        self._cells: dict[tuple[str, str], MemoryCell] = {}

    def allocate(self, location: str) -> str:
        self._locations.add(location)
        return location

    def fields(self, location: str) -> tuple[str, ...]:
        return tuple(field for loc, field in self._cells if loc == location)

    def write(self, points_to: frozenset[str], field: str | None, value: AbsValue,
              *, definition: str, definite: bool) -> bool:
        exact_field = field is not None
        strong = definite and len(points_to) == 1 and exact_field
        targets = []
        for location in points_to:
            self.allocate(location)
            if exact_field:
                targets.append((location, field))
            else:
                known = self.fields(location)
                targets.extend((location, known_field) for known_field in known)
                targets.append((location, "<unknown-field>"))
        for key in dict.fromkeys(targets):
            previous = self._cells.get(key)
            if strong:
                self._cells[key] = MemoryCell(value, MayMust(frozenset({definition}),
                                                              frozenset({definition})))
            else:
                joined = value if previous is None else previous.value.join(value)
                may_defs = frozenset({definition}) if previous is None else previous.definitions.may | {definition}
                self._cells[key] = MemoryCell(joined, MayMust(may_defs, frozenset()))
        return strong

    def read(self, points_to: frozenset[str], field: str | None) -> AbsValue:
        values = []
        for location in points_to:
            if field is None:
                values.extend(cell.value for (loc, _), cell in self._cells.items() if loc == location)
            else:
                for key in ((location, field), (location, "<unknown-field>")):
                    if key in self._cells:
                        values.append(self._cells[key].value)
        if not values:
            return AbsValue(unknown=True)
        result = values[0]
        for value in values[1:]:
            result = result.join(value)
        return result

    def reaching_definitions(self, location: str, field: str) -> MayMust[str]:
        cells = [self._cells[key] for key in ((location, field), (location, "<unknown-field>"))
                 if key in self._cells]
        if not cells:
            return MayMust(frozenset(), frozenset())
        value = cells[0].definitions
        for cell in cells[1:]:
            value = value.join(cell.definitions)
        return value

    def havoc(self, reachable: frozenset[str], boundary_id: str) -> None:
        unknown = AbsValue(origins=frozenset({unknown_origin(boundary_id)}), unknown=True)
        for location in reachable:
            self.allocate(location)
            fields = self.fields(location) or ("<unknown-field>",)
            for field in fields:
                key = (location, field)
                previous = self._cells.get(key)
                value = unknown if previous is None else previous.value.join(unknown)
                may_defs = previous.definitions.may if previous is not None else frozenset()
                self._cells[key] = MemoryCell(value, MayMust(may_defs, frozenset()))


def opaque_call(boundary_id: str, arguments: tuple[AbsValue, ...], heap: AbstractHeap):
    reachable = frozenset().union(*(argument.points_to for argument in arguments))
    origins = frozenset().union(*(argument.origins for argument in arguments))
    heap.havoc(reachable, boundary_id)
    returned = AbsValue(points_to=reachable,
                        origins=origins | {unknown_origin(boundary_id)}, unknown=True)
    effects = EffectValue(
        reads=reachable,
        writes=reachable,
        return_dependencies=frozenset(str(i) for i in range(len(arguments))),
        egresses=frozenset({"<unknown-egress>"}),
        unknown_effects=frozenset({boundary_id}),
    )
    return returned, effects
