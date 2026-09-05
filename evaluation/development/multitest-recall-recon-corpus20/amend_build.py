"""Build a prototype amended copy of the v2 dataflow module.

Each refinement is gated by an environment flag so its corpus effect can be measured
independently.  This is measurement scaffolding for the delta-2.1 brief, never a design.
"""
from __future__ import annotations

from pathlib import Path

SRC = Path(
    "/Users/alexanderking/.cache/recon-scratch/vnext/src/sc_referee/scientific_checks/"
    "code_csv_multiple_testing_dataflow_v2.py"
)
OUT = Path("/Users/alexanderking/.cache/recon-scratch/work/amended_dataflow_v2.py")

HEADER = '''
import os as _os


def _AMEND(flag):
    return flag in _os.environ.get("MT_AMEND", "").split(",")


def _amend_presentation_percent_payload(node, parents):
    """A1: a display tuple that is exactly the right operand of `LITERAL % (...)`."""

    owner = parents.get(node)
    return bool(
        isinstance(owner, ast.BinOp)
        and isinstance(owner.op, ast.Mod)
        and owner.right is node
        and isinstance(owner.left, ast.Constant)
        and isinstance(owner.left.value, str)
    )
'''

PATCHES: list[tuple[str, str]] = [
    # ---- A1: %-format payload tuple is presentation, not a family container -------
    (
        """                if self._p_sequence(node) is None:
                    return True""",
        """                if _AMEND("A1") and _amend_presentation_percent_payload(node, parents):
                    continue
                if self._p_sequence(node) is None:
                    return True""",
    ),
    # ---- A1 (second half): the `%` BinOp itself is a presentation edge ------------
    (
        """                if self._presentation_concat(node):
                    continue
                return "unresolved-manual-correction-present\"""",
        """                if self._presentation_concat(node):
                    continue
                if _AMEND("A1") and self._amend_presentation_percent(node):
                    continue
                return "unresolved-manual-correction-present\"""",
    ),
    # ---- A2: zip transport loop over the contract family + a reconstructed PSEQ ----
    (
        """            known = [item for item in sequences if item is not None]
            return bool(
                len(known) >= 2
                and all(item == known[0] for item in known[1:])
                and len(known[0]) == len(set(known[0]))
                and any(
                    isinstance(item, ast.Name) and item.id in self.correction_return_names
                    for item in node.iter.args
                )
            )""",
        """            known = [item for item in sequences if item is not None]
            if _AMEND("A2"):
                others = [
                    item
                    for item, sequence in zip(node.iter.args, sequences)
                    if sequence is None
                ]
                return bool(
                    known
                    and all(item == known[0] for item in known[1:])
                    and len(known[0]) == len(set(known[0]))
                    and len(known[0]) == len(self.outcome_columns)
                    and all(
                        _mt_outcome_iteration_bindings(
                            item, ast.Name(id="_", ctx=ast.Store()), self.resolver,
                            self.outcome_columns,
                        )
                        is not None
                        or self._amend_outcome_family_sequence(item)
                        for item in others
                    )
                )
            return bool(
                len(known) >= 2
                and all(item == known[0] for item in known[1:])
                and len(known[0]) == len(set(known[0]))
                and any(
                    isinstance(item, ast.Name) and item.id in self.correction_return_names
                    for item in node.iter.args
                )
            )""",
    ),
    # ---- A3: statement-form terminal rendering ------------------------------------
    (
        """        for owner, expression in controls:
            if isinstance(owner, ast.IfExp) and self._terminal_rendering_ifexp(owner):
                continue""",
        """        for owner, expression in controls:
            if isinstance(owner, ast.IfExp) and self._terminal_rendering_ifexp(owner):
                continue
            if (
                _AMEND("A3")
                and isinstance(owner, ast.If)
                and self._amend_terminal_rendering_if(owner)
            ):
                continue""",
    ),
]

HELPERS = '''
    def _amend_presentation_percent(self, node) -> bool:
        """A1: `LITERAL % PAYLOAD` reaching only registered sinks is presentation."""

        if not (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Mod)
            and isinstance(node.left, ast.Constant)
            and isinstance(node.left.value, str)
        ):
            return False
        combined = (*self.original_scope, *self.scope)
        parents = {
            child: parent
            for parent in _walk_statements(combined)
            for child in ast.iter_child_nodes(parent)
        }
        return self._mt_v2_rendering_load_reaches_sink(node, parents)

    def _amend_outcome_family_sequence(self, node) -> bool:
        sequence = self.resolver.sequence(node)
        if sequence is None:
            return False
        if tuple(sequence) == tuple(self.outcome_columns):
            return True
        return tuple(
            item[0] if isinstance(item, tuple) and item else item for item in sequence
        ) == tuple(self.outcome_columns)

    def _amend_constant_string(self, node) -> bool:
        return bool(
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value
            and "\\x00" not in node.value
            and len(node.value.encode("utf-8")) <= 256
        )

    def _amend_terminal_rendering_if(self, node) -> bool:
        """A3: the exact statement twin of the 4.8 terminal-rendering ternary."""

        if node.orelse is None or len(node.body) != 1 or len(node.orelse) != 1:
            return False
        if not (
            self._decision_positions_in_expr(node.test, set(), 0)
            or len(self._p_origins(node.test)) == 1
        ):
            return False
        body, orelse = node.body[0], node.orelse[0]
        # A3a: one Assign of a Constant[str] to the same single Name target in both arms.
        if (
            isinstance(body, ast.Assign)
            and isinstance(orelse, ast.Assign)
            and len(body.targets) == 1
            and len(orelse.targets) == 1
            and isinstance(body.targets[0], ast.Name)
            and isinstance(orelse.targets[0], ast.Name)
            and body.targets[0].id == orelse.targets[0].id
            and self._amend_constant_string(body.value)
            and self._amend_constant_string(orelse.value)
        ):
            combined = (*self.original_scope, *self.scope)
            parents = {
                child: parent
                for parent in _walk_statements(combined)
                for child in ast.iter_child_nodes(parent)
            }
            loads = [
                item
                for item in _walk_statements(combined)
                if isinstance(item, ast.Name)
                and isinstance(item.ctx, ast.Load)
                and item.id == body.targets[0].id
            ]
            return bool(
                loads
                and all(self._mt_v2_rendering_load_reaches_sink(item, parents) for item in loads)
            )
        # A3b: one registered sink call with only constant payloads in both arms.
        sink_calls = {sink.call: sink for sink in self.sinks}

        def rendering_sink(statement) -> bool:
            if not (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)):
                return False
            sink = sink_calls.get(statement.value)
            if sink is None or not sink.p_result_eligible:
                return False
            return all(self._amend_constant_string(payload) for payload in sink.payloads)

        return rendering_sink(body) and rendering_sink(orelse)
'''

text = SRC.read_text()
for old, new in PATCHES:
    if old not in text:
        raise SystemExit(f"patch anchor missing: {old.splitlines()[0]!r}")
    text = text.replace(old, new, 1)

anchor = "    def _terminal_family_transport_loop(self"
if anchor not in text:
    raise SystemExit("helper anchor missing")
text = text.replace(anchor, HELPERS + "\n" + anchor, 1)

marker = "CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST"
position = text.index(marker)
text = text[:position] + HEADER + "\n\n" + text[position:]
OUT.write_text(text)
print("wrote", OUT)
