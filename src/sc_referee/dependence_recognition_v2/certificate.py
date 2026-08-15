"""Small trusted kernel for dependence growth group and symbolic-count certificates."""

from __future__ import annotations

import ast
import copy
import posixpath
from collections import Counter
from dataclasses import asdict
from typing import Any, Literal, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.dependence_recognition.ir import HumanMethodAuthorization
from sc_referee.dependence_recognition_v2.ir import (
    DEPENDENCE_V2_KERNEL_REFUSAL_OBLIGATIONS,
    MAX_V2_AST_NODES,
    MAX_V2_INLINE_DEPTH,
    AuthorizedProcedureSet,
    CountDependenceCertificate,
    CountGroupDomainObligation,
    CountOperandObligation,
    CountPredicateAtom,
    CountProcedureFact,
    DependenceGrowthCertificate,
    GroupValueSequenceFact,
    VerifiedCountDependenceCertificate,
    VerifiedDependenceGrowthCertificate,
)

_PROCEDURE_ARITY = {
    "scipy.stats.ttest_ind": 2,
    "scipy.stats.ttest_ind:welch": 2,
    "scipy.stats.mannwhitneyu": 2,
}
_ROW_INDEPENDENT_VARIANTS = frozenset(_PROCEDURE_ARITY)
_GROUP_BASE_PROCEDURES = frozenset({"scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu"})
_COUNT_PROCEDURES = frozenset({"scipy.stats.binomtest", "scipy.stats.fisher_exact"})
_ALL_PROCEDURES = frozenset((*_PROCEDURE_ARITY, *_COUNT_PROCEDURES))
_DISTRIBUTION_HELPER_METHODS = frozenset(
    f"scipy.stats.{distribution}.{method}"
    for distribution in ("t", "norm")
    for method in ("ppf", "cdf", "sf")
)
assert not (_GROUP_BASE_PROCEDURES | _COUNT_PROCEDURES) & _DISTRIBUTION_HELPER_METHODS


def verify_dependence_growth_certificate(
    certificate: DependenceGrowthCertificate,
    *,
    trusted_group_facts: tuple[GroupValueSequenceFact, ...],
    trusted_authorizations: tuple[HumanMethodAuthorization, ...],
    trusted_procedure_sets: tuple[AuthorizedProcedureSet, ...] = (),
    source_bytes: bytes,
    _failure_reasons: list[str] | None = None,
) -> VerifiedDependenceGrowthCertificate | None:
    """Discharge every equation from source bytes and one trusted fact."""

    def refuse(obligation: str) -> VerifiedDependenceGrowthCertificate | None:
        if obligation not in DEPENDENCE_V2_KERNEL_REFUSAL_OBLIGATIONS:
            raise AssertionError(f"unknown kernel refusal obligation: {obligation}")
        if _failure_reasons is not None:
            _failure_reasons.append(obligation)
        return None

    if (
        len(trusted_group_facts) != 1
        or len(trusted_authorizations) != 1
        or sha256_digest(source_bytes) != certificate.source_digest
        or certificate.source_extent != (0, len(source_bytes))
        or not certificate.resolved_callables
        or any(item not in _PROCEDURE_ARITY for item in certificate.resolved_callables)
        or len(certificate.resolved_callables) != len(certificate.procedure_call_tokens)
        or len(certificate.resolved_callables) != len(certificate.result_names)
        or not certificate.authority_record_id
        or not certificate.independent_unit_definition_id
    ):
        return refuse("envelope-binding")
    fact = trusted_group_facts[0]
    authority = trusted_authorizations[0]
    obligation = certificate.obligation
    if (
        authority.record_type != "human_method_authorization"
        or authority.authority_state != "authorized"
        or authority.record_id != certificate.authority_record_id
        or authority.analysis_target_ref != certificate.analysis_target_ref
        or authority.procedure_ref != certificate.procedure_ref
        or authority.independent_unit_definition_id != certificate.independent_unit_definition_id
        or authority.authorized_key_columns != (obligation.authorized_unit_column,)
        or authority.input_path != obligation.path
        or authority.input_content_digest != obligation.content_digest
    ):
        return refuse("authority-binding")
    if trusted_procedure_sets:
        if (
            len(trusted_procedure_sets) != 1
            or trusted_procedure_sets[0].record_id != authority.procedure_ref.record_id
            or trusted_procedure_sets[0].resolved_callables
            != tuple(dict.fromkeys(certificate.resolved_callables))
        ):
            return refuse("authority-binding")
    elif len(certificate.resolved_callables) != 1:
        # Legacy hand-built single-call certificates predate the set channel;
        # no multi-call claim can use that compatibility path.
        return refuse("authority-binding")
    if any(item not in _ROW_INDEPENDENT_VARIANTS for item in certificate.resolved_callables):
        return refuse("procedure-set-homogeneity")
    if (
        fact.evidence_id != f"dependence-growth-group-proof:{semantic_digest(asdict(obligation))}"
        or fact.row_count <= 0
        or fact.row_count > 10_000
        or len(fact.groups) > 256
        or not fact.header
        or len(fact.header) != len(set(fact.header))
        or any(not item for item in fact.header)
        or not {
            fact.authorized_unit_column,
            fact.group_key_column,
            fact.value_column,
        }
        <= set(fact.header)
        or fact.path != obligation.path
        or fact.content_digest != obligation.content_digest
        or fact.line_model != obligation.line_model
        or fact.reader_form != obligation.reader_form
        or fact.encoding != obligation.encoding
        or fact.authorized_unit_column != obligation.authorized_unit_column
        or fact.group_key_column != obligation.group_key_column
        or fact.value_column != obligation.value_column
        or fact.cast_kind != obligation.cast_kind
        or fact.predeclared_bucket_keys != obligation.predeclared_bucket_keys
        or (fact.encoding == "ascii" and not fact.ascii_bytes_proven)
    ):
        return refuse("fact-closure")
    try:
        tree = ast.parse(source_bytes.decode("utf-8", errors="strict"))
    except (SyntaxError, UnicodeDecodeError, ValueError, RecursionError):
        return refuse("source-parse")
    if sum(1 for _ in ast.walk(tree)) > MAX_V2_AST_NODES:
        return refuse("source-size")
    tree = _kernel_without_docstrings(tree)
    if not _kernel_replay_function_bookkeeping(tree, certificate):
        return refuse("rename-injectivity")
    if not _kernel_replay_source_claims(tree, certificate, fact):
        return refuse("source-semantic-replay")
    if not _kernel_sink_partition_matches(tree, certificate):
        return refuse("sink-partition")

    groups = {item.group_key: item for item in fact.groups}
    if len(groups) != len(fact.groups) or not groups:
        return refuse("group-partition")
    all_rows = [index for group in fact.groups for index in group.row_indices]
    if sorted(all_rows) != list(range(1, fact.row_count + 1)) or len(all_rows) != fact.row_count:
        return refuse("group-partition")
    all_observations = [item for group in fact.groups for item in group.observation_ids]
    if len(all_observations) != len(set(all_observations)) or any(
        not item for item in all_observations
    ):
        return refuse("observation-identity")
    for group in fact.groups:
        length = len(group.row_indices)
        if not (
            length
            == len(group.observation_ids)
            == len(group.authorized_unit_ids)
            == len(group.source_values)
            == len(group.cast_value_reprs)
        ):
            return refuse("group-length-equation")

    if len({_PROCEDURE_ARITY[item] for item in certificate.resolved_callables}) != 1:
        return refuse("operand-binding")
    arity = _PROCEDURE_ARITY[certificate.resolved_callables[0]]
    bindings = certificate.operand_bindings
    if (
        len(bindings) != arity
        or tuple(item.position for item in bindings) != tuple(range(arity))
        or len({item.group_key for item in bindings}) != len(bindings)
        or {item.group_key for item in bindings} != set(groups)
    ):
        return refuse("operand-binding")

    unit_operand_memberships: dict[str, set[int]] = {}
    repeated: set[str] = set()
    for binding in bindings:
        sequence = groups[binding.group_key]
        counts = Counter(sequence.authorized_unit_ids)
        repeated.update(unit for unit, count in counts.items() if count > 1)
        for unit in counts:
            unit_operand_memberships.setdefault(unit, set()).add(binding.position)
    if any(len(positions) > 1 for positions in unit_operand_memberships.values()):
        return refuse("operand-disjointness")
    conclusion = "repeated_units" if repeated else "one_observation_per_unit"
    if certificate.conclusion != conclusion:
        return refuse("conclusion-equation")

    renames = certificate.alpha_renames
    if len({item.fresh_name for item in renames}) != len(renames):
        return refuse("alpha-renaming")
    if any(
        not item.fresh_name.startswith("__dependence_v2_")
        or item.original_name == item.fresh_name
        or not item.call_path_id
        or len(item.call_span) != 4
        for item in renames
    ):
        return refuse("alpha-renaming")
    if len(set(certificate.dead_syntactic_construct_tokens)) != len(
        certificate.dead_syntactic_construct_tokens
    ):
        return refuse("dead-construct-completeness")
    if not _kernel_replay_function_bookkeeping(tree, certificate):
        return refuse("dead-construct-completeness")

    expected_id = f"dependence-growth-certificate:{semantic_digest({'source_digest': certificate.source_digest, 'fact': fact.evidence_id, 'bindings': [asdict(item) for item in bindings], 'conclusion': conclusion})}"
    if certificate.certificate_id != expected_id:
        return refuse("certificate-identity")
    return VerifiedDependenceGrowthCertificate(
        certificate_id=certificate.certificate_id,
        source_path=certificate.source_path,
        source_digest=certificate.source_digest,
        resolved_callables=certificate.resolved_callables,
        conclusion=conclusion,
        fact=fact,
        operand_bindings=bindings,
        repeated_unit_ids=tuple(sorted(repeated)),
        alpha_renames=renames,
        operand_slice_statement_tokens=certificate.operand_slice_statement_tokens,
        sink_bound_statement_tokens=certificate.sink_bound_statement_tokens,
        dead_syntactic_construct_tokens=certificate.dead_syntactic_construct_tokens,
    )


def verify_count_dependence_certificate(
    certificate: CountDependenceCertificate,
    *,
    trusted_count_facts: tuple[CountProcedureFact, ...],
    trusted_authorizations: tuple[HumanMethodAuthorization, ...],
    source_bytes: bytes,
    _failure_reasons: list[str] | None = None,
) -> VerifiedCountDependenceCertificate | None:
    """Replay symbolic count obligations and recompute every row set in-kernel."""

    def refuse(obligation: str) -> VerifiedCountDependenceCertificate | None:
        if obligation not in DEPENDENCE_V2_KERNEL_REFUSAL_OBLIGATIONS:
            raise AssertionError(f"unknown kernel refusal obligation: {obligation}")
        if _failure_reasons is not None:
            _failure_reasons.append(obligation)
        return None

    if (
        len(trusted_count_facts) != 1
        or len(trusted_authorizations) != 1
        or sha256_digest(source_bytes) != certificate.source_digest
        or certificate.source_extent != (0, len(source_bytes))
        or certificate.resolved_callable
        not in {"scipy.stats.binomtest", "scipy.stats.fisher_exact"}
    ):
        return refuse("envelope-binding")
    fact = trusted_count_facts[0]
    authority = trusted_authorizations[0]
    obligation = certificate.obligation
    if (
        authority.record_type != "human_method_authorization"
        or authority.authority_state != "authorized"
        or authority.record_id != certificate.authority_record_id
        or authority.analysis_target_ref != certificate.analysis_target_ref
        or authority.procedure_ref != certificate.procedure_ref
        or authority.independent_unit_definition_id != certificate.independent_unit_definition_id
        or authority.authorized_key_columns != (obligation.authorized_unit_column,)
        or authority.input_path != obligation.path
        or authority.input_content_digest != obligation.content_digest
    ):
        return refuse("authority-binding")
    if (
        fact.evidence_id != f"dependence-growth-count-proof:{semantic_digest(asdict(obligation))}"
        or fact.path != obligation.path
        or fact.content_digest != obligation.content_digest
        or fact.line_model != obligation.line_model
        or fact.reader_form != obligation.reader_form
        or fact.encoding != obligation.encoding
        or fact.authorized_unit_column != obligation.authorized_unit_column
        or fact.row_count <= 0
        or fact.row_count != len(fact.rows)
        or len(fact.header) != len(set(fact.header))
        or any(not item for item in fact.header)
        or fact.authorized_unit_column not in fact.header
        or (fact.encoding == "ascii" and not fact.ascii_bytes_proven)
    ):
        return refuse("count-fact-closure")
    if tuple(row.row_index for row in fact.rows) != tuple(range(1, fact.row_count + 1)):
        return refuse("count-fact-closure")
    for row in fact.rows:
        values = dict(row.values)
        if (
            tuple(values) != fact.header
            or len(values) != len(row.values)
            or values[fact.authorized_unit_column] == ""
            or row.observation_id
            != "observation:"
            + semantic_digest(
                {
                    "path": fact.path,
                    "digest": fact.content_digest,
                    "row": row.row_index,
                }
            )
            or row.authorized_unit_id
            != "unit-key:"
            + semantic_digest(
                {
                    "column": fact.authorized_unit_column,
                    "value": values[fact.authorized_unit_column],
                }
            )
        ):
            return refuse("count-fact-closure")
    for group in obligation.group_domains:
        if (
            group.group_key_column not in fact.header
            or not group.predeclared_bucket_keys
            or len(group.predeclared_bucket_keys) != len(set(group.predeclared_bucket_keys))
            or any(
                dict(row.values)[group.group_key_column] not in group.predeclared_bucket_keys
                for row in fact.rows
            )
        ):
            return refuse("count-set-equations")
    expected_universe = _kernel_matching_rows(fact, obligation.universe_atoms)
    if tuple(fact.universe_row_indices) != expected_universe:
        return refuse("count-set-equations")
    if len(fact.operands) != len(obligation.operands):
        return refuse("count-fact-closure")
    by_identity = {(item.operand_id, item.position): item for item in fact.operands}
    if len(by_identity) != len(fact.operands):
        return refuse("count-fact-closure")
    for operand in obligation.operands:
        proof = by_identity.get((operand.operand_id, operand.position))
        if proof is None:
            return refuse("count-fact-closure")
        expected_rows = _kernel_matching_rows(
            fact, (*operand.domain_atoms, *operand.predicate_atoms)
        )
        expected_domain_rows = _kernel_matching_rows(fact, operand.domain_atoms)
        rows_by_index = {row.row_index: row for row in fact.rows}
        if (
            proof.row_indices != expected_rows
            or proof.cardinality != len(expected_rows)
            or proof.observation_ids
            != tuple(rows_by_index[index].observation_id for index in expected_rows)
            or proof.authorized_unit_ids
            != tuple(rows_by_index[index].authorized_unit_id for index in expected_rows)
            or not set(expected_rows) <= set(expected_domain_rows)
        ):
            return refuse("count-set-equations")
    try:
        tree = ast.parse(source_bytes.decode("utf-8", errors="strict"))
    except (SyntaxError, UnicodeDecodeError, ValueError, RecursionError):
        return refuse("source-parse")
    if sum(1 for _ in ast.walk(tree)) > MAX_V2_AST_NODES:
        return refuse("source-size")
    tree = _kernel_without_docstrings(tree)
    if not _kernel_replay_function_bookkeeping(tree, certificate):
        return refuse("rename-injectivity")
    if not _kernel_replay_count_claims(tree, certificate):
        return refuse("count-source-semantic-replay")
    if not _kernel_sink_partition_matches(tree, certificate):
        return refuse("sink-partition")

    proofs = {item.position: item for item in fact.operands}
    repeated: set[str] = set()
    if certificate.resolved_callable == "scipy.stats.binomtest":
        if (
            set(proofs) != {0, 1}
            or any(not proofs[position].row_indices for position in (0, 1))
            or not set(proofs[0].row_indices) <= set(proofs[1].row_indices)
        ):
            return refuse("count-subset-partition")
        repeated.update(
            unit for unit, count in Counter(proofs[1].authorized_unit_ids).items() if count > 1
        )
    else:
        if set(proofs) != {0, 1, 2, 3} or not fact.universe_row_indices:
            return refuse("count-subset-partition")
        cell_sets = [set(proofs[index].row_indices) for index in range(4)]
        if any(
            left & right for index, left in enumerate(cell_sets) for right in cell_sets[index + 1 :]
        ) or set().union(*cell_sets) != set(fact.universe_row_indices):
            return refuse("count-subset-partition")
        if not _kernel_fisher_atoms_are_factorial(certificate.obligation.operands):
            return refuse("count-cells-factorial")
        unit_cells: dict[str, set[int]] = {}
        for proof in fact.operands:
            for unit in proof.authorized_unit_ids:
                unit_cells.setdefault(unit, set()).add(proof.position)
        if any(len(cells) > 1 for cells in unit_cells.values()):
            return refuse("count-unit-nonspanning")
        repeated.update(
            unit
            for proof in fact.operands
            for unit, count in Counter(proof.authorized_unit_ids).items()
            if count > 1
        )
    conclusion = "repeated_units" if repeated else "one_observation_per_unit"
    if certificate.conclusion != conclusion:
        return refuse("conclusion-equation")
    if not _kernel_replay_function_bookkeeping(tree, certificate):
        return refuse("dead-construct-completeness")
    expected_id = "dependence-growth-count-certificate:" + semantic_digest(
        {
            "source_digest": certificate.source_digest,
            "fact": fact.evidence_id,
            "procedure": certificate.resolved_callable,
            "conclusion": conclusion,
        }
    )
    if certificate.certificate_id != expected_id:
        return refuse("certificate-identity")
    return VerifiedCountDependenceCertificate(
        certificate_id=certificate.certificate_id,
        source_path=certificate.source_path,
        source_digest=certificate.source_digest,
        resolved_callable=certificate.resolved_callable,
        conclusion=conclusion,
        fact=fact,
        repeated_unit_ids=tuple(sorted(repeated)),
        alpha_renames=certificate.alpha_renames,
        operand_slice_statement_tokens=certificate.operand_slice_statement_tokens,
        sink_bound_statement_tokens=certificate.sink_bound_statement_tokens,
        dead_syntactic_construct_tokens=certificate.dead_syntactic_construct_tokens,
    )


def _kernel_fisher_atoms_are_factorial(
    operands: tuple[CountOperandObligation, ...],
) -> bool:
    """Independently establish the exact two-column, two-level cell product."""

    if len(operands) != 4:
        return False
    combinations: set[tuple[tuple[str, str], ...]] = set()
    levels: dict[str, set[str]] = {}
    for operand in operands:
        atoms = operand.predicate_atoms
        if (
            len(atoms) != 2
            or any(atom.operator != "eq" for atom in atoms)
            or len({atom.column for atom in atoms}) != 2
        ):
            return False
        combination = tuple(sorted((atom.column, atom.literal) for atom in atoms))
        combinations.add(combination)
        for column, literal in combination:
            levels.setdefault(column, set()).add(literal)
    if len(levels) != 2 or any(len(values) != 2 for values in levels.values()):
        return False
    columns = tuple(sorted(levels))
    expected = {
        tuple(sorted(((columns[0], left), (columns[1], right))))
        for left in levels[columns[0]]
        for right in levels[columns[1]]
    }
    return len(combinations) == 4 and combinations == expected


def _kernel_without_docstrings(tree: ast.Module) -> ast.Module:
    """Independently erase only leading module and function docstrings."""

    normalized = copy.deepcopy(tree)

    def without_leading_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            return body[1:]
        return body

    normalized.body = without_leading_docstring(normalized.body)
    for statement in normalized.body:
        if isinstance(statement, ast.FunctionDef):
            statement.body = without_leading_docstring(statement.body)
    return normalized


def _kernel_matching_rows(
    fact: CountProcedureFact, atoms: tuple[CountPredicateAtom, ...]
) -> tuple[int, ...]:
    matches: list[int] = []
    for row in fact.rows:
        values = dict(row.values)
        if all(
            (values.get(atom.column) == atom.literal)
            if atom.operator == "eq"
            else (values.get(atom.column) != atom.literal)
            for atom in atoms
        ):
            matches.append(row.row_index)
    return tuple(matches)


def _kernel_replay_count_claims(tree: ast.Module, certificate: CountDependenceCertificate) -> bool:
    """Independently reconstruct the symbolic count shapes from source AST."""

    if not _kernel_import_forms_closed(tree) or not _kernel_typing_uses_closed(tree):
        return False
    module_assignment_names = [
        node.targets[0].id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    ]
    if len(module_assignment_names) != len(set(module_assignment_names)):
        return False
    imports = _kernel_imports(tree)
    if set(module_assignment_names) & set(imports):
        return False
    constants = _kernel_constants(tree)
    if not _kernel_module_collection_uses_closed(tree, constants):
        return False
    partition = _kernel_partition_body(tree, certificate)
    if partition is None:
        return False
    flattened, _operand_names = partition
    tree = ast.Module(body=flattened, type_ignores=[])
    if not _kernel_count_live_syntax_closed(tree, certificate, imports, constants):
        return False
    if _kernel_count_group_obligations(tree, certificate) != certificate.obligation.group_domains:
        return False
    assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)]
    procedures = [
        node
        for node in assignments
        if len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Call)
        and _kernel_callable(node.value.func, imports)
        in {"scipy.stats.binomtest", "scipy.stats.fisher_exact"}
    ]
    if len(procedures) != 1:
        return False
    procedure = procedures[0]
    if not isinstance(procedure.value, ast.Call):
        return False
    call = procedure.value
    assert isinstance(call, ast.Call)
    resolved = _kernel_callable(call.func, imports)
    target = procedure.targets[0]
    assert isinstance(target, ast.Name)
    if (
        resolved != certificate.resolved_callable
        or _kernel_node_token(certificate.source_path, call, "procedure-call")
        != certificate.procedure_call_token
        or _kernel_renamed_name(tree, certificate, procedure, target.id) != certificate.result_name
        or not _kernel_count_options_closed(call, certificate.resolved_callable, constants)
    ):
        return False
    expressions = _kernel_count_call_expressions(call, certificate.resolved_callable, assignments)
    if expressions is None or len(expressions) != len(certificate.obligation.operands):
        return False
    domains = _kernel_count_domains(tree, certificate, constants)
    replayed: list[CountOperandObligation] = []
    for position, (expression, _proposed) in enumerate(
        zip(expressions, certificate.obligation.operands, strict=True)
    ):
        if not isinstance(expression, ast.Name):
            return False
        resolved_name = _kernel_renamed_name(tree, certificate, call, expression.id)
        derivation = _kernel_count_derivation(tree, certificate, resolved_name, domains, constants)
        if derivation is None:
            return False
        domain_kind, domain_atoms, predicate_atoms = derivation
        replayed.append(
            CountOperandObligation(
                operand_id=resolved_name,
                position=position,
                domain_kind=cast(Literal["rows", "group_rows", "filtered_rows"], domain_kind),
                domain_atoms=domain_atoms,
                predicate_atoms=predicate_atoms,
            )
        )
    if tuple(replayed) != certificate.obligation.operands:
        return False
    if certificate.resolved_callable == "scipy.stats.binomtest":
        universe = replayed[1].domain_atoms
    else:
        common = set(replayed[0].domain_atoms)
        for item in replayed[1:]:
            common.intersection_update(item.domain_atoms)
        universe = tuple(atom for atom in replayed[0].domain_atoms if atom in common)
    if universe != certificate.obligation.universe_atoms:
        return False
    if not _kernel_count_reader_matches(tree, certificate, constants):
        return False
    return _kernel_count_sink_matches(tree, certificate, constants)


def _kernel_count_group_obligations(
    tree: ast.Module, certificate: CountDependenceCertificate
) -> tuple[CountGroupDomainObligation, ...]:
    obligations: list[CountGroupDomainObligation] = []
    for loop in (node for node in ast.walk(tree) if isinstance(node, ast.For)):
        if not _kernel_count_group_loop_allowed(loop, certificate):
            continue
        assert isinstance(loop.target, ast.Name)
        call = cast(ast.Call, cast(ast.Expr, loop.body[0]).value)
        target = cast(ast.Subscript, cast(ast.Attribute, call.func).value)
        column = _kernel_row_column(target.slice, loop.target.id)
        if column is None or not isinstance(target.value, ast.Name):
            return ()
        group_name = _kernel_renamed_name(tree, certificate, target, target.value.id)
        declarations = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and _kernel_renamed_name(tree, certificate, node, node.targets[0].id) == group_name
            and isinstance(node.value, ast.Dict)
        ]
        if len(declarations) != 1:
            return ()
        declaration = declarations[0]
        if not declaration.keys or any(
            not isinstance(key, ast.Constant)
            or not isinstance(key.value, str)
            or not isinstance(value, ast.List)
            or value.elts
            for key, value in zip(declaration.keys, declaration.values, strict=True)
        ):
            return ()
        obligations.append(
            CountGroupDomainObligation(
                group_key_column=column,
                predeclared_bucket_keys=tuple(
                    cast(str, cast(ast.Constant, key).value) for key in declaration.keys
                ),
            )
        )
    return tuple(sorted(obligations))


def _kernel_count_live_syntax_closed(
    tree: ast.Module,
    certificate: CountDependenceCertificate,
    imports: dict[str, str],
    constants: dict[str, object],
) -> bool:
    functions = {item.name for item in tree.body if isinstance(item, ast.FunctionDef)}
    operand_names = {item.operand_id for item in certificate.obligation.operands}
    assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)]
    procedure_assignments = {
        id(node)
        for node in assignments
        if len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Call)
        and _kernel_callable(node.value.func, imports) in _COUNT_PROCEDURES
    }
    derivation_roots = [
        node
        for node in (*assignments, *(item for item in ast.walk(tree) if isinstance(item, ast.For)))
        if any(
            isinstance(candidate, ast.Name)
            and isinstance(candidate.ctx, ast.Store)
            and _kernel_renamed_name(tree, certificate, candidate, candidate.id) in operand_names
            for candidate in ast.walk(node)
        )
    ]
    used_source_names = {
        candidate.id
        for root in derivation_roots
        for candidate in ast.walk(root)
        if isinstance(candidate, ast.Name) and isinstance(candidate.ctx, ast.Load)
    }
    forbidden = (
        ast.While,
        ast.AsyncFor,
        ast.AsyncWith,
        ast.Try,
        ast.Match,
        ast.SetComp,
        ast.DictComp,
        ast.Raise,
        ast.Assert,
        ast.Yield,
        ast.YieldFrom,
        ast.Await,
        ast.AugAssign,
        ast.AnnAssign,
        ast.NamedExpr,
        ast.Delete,
    )
    if any(isinstance(node, forbidden) for node in ast.walk(tree)):
        return False
    group_domains_used = any(
        item.domain_kind == "group_rows" for item in certificate.obligation.operands
    )
    group_loops = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.For) and _kernel_count_group_loop_allowed(node, certificate)
    ]
    if (group_domains_used and len(group_loops) != 1) or (not group_domains_used and group_loops):
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            entry = isinstance(call.func, ast.Name) and call.func.id in functions
            sink = isinstance(call.func, ast.Attribute) and call.func.attr == "write_text"
            path_prep = _kernel_closed_makedirs(call, constants)
            grouped = any(
                _kernel_count_for_allowed(loop, tree, certificate) and node in set(ast.walk(loop))
                for loop in ast.walk(tree)
                if isinstance(loop, ast.For)
            )
            if not (entry or sink or path_prep or grouped):
                return False
        if isinstance(node, ast.If) and not _kernel_main_guard(node):
            if not any(
                _kernel_count_for_allowed(loop, tree, certificate) and node in set(ast.walk(loop))
                for loop in ast.walk(tree)
                if isinstance(loop, ast.For)
            ):
                return False
        if isinstance(node, ast.Call):
            resolved = _kernel_callable(node.func, imports)
            if resolved in _COUNT_PROCEDURES:
                continue
            if isinstance(node.func, ast.Name) and node.func.id in functions | {
                "Path",
                "list",
                "len",
                "sum",
                "str",
            }:
                continue
            if isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and imports.get(node.func.value.id) == "csv"
                    and node.func.attr == "DictReader"
                ):
                    continue
                if node.func.attr in {"open", "read_text", "splitlines", "write_text"}:
                    continue
                if node.func.attr == "append":
                    continue
            if _kernel_path_value(node, constants) is not None or _kernel_closed_makedirs(
                node, constants
            ):
                continue
            return False
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                return False
            value = node.value
            renamed_target = _kernel_renamed_name(tree, certificate, node, node.targets[0].id)
            if node.targets[0].id in constants:
                continue
            if (
                isinstance(value, ast.Constant)
                and value.value == 0
                and renamed_target in operand_names
            ):
                continue
            if (
                isinstance(value, ast.Dict)
                and value.keys
                and all(
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and isinstance(item, ast.List)
                    and not item.elts
                    for key, item in zip(value.keys, value.values, strict=True)
                )
            ) and any(item.domain_kind == "group_rows" for item in certificate.obligation.operands):
                continue
            if isinstance(value, ast.List) and any(
                isinstance(call.func, ast.Attribute | ast.Name)
                and _kernel_callable(call.func, imports) == "scipy.stats.fisher_exact"
                and len(call.args) == 1
                and isinstance(call.args[0], ast.Name)
                and call.args[0].id == node.targets[0].id
                for call in ast.walk(tree)
                if isinstance(call, ast.Call)
            ):
                continue
            if isinstance(value, ast.ListComp) and node.targets[0].id in used_source_names:
                continue
            if id(node) in procedure_assignments:
                continue
            if (
                renamed_target in operand_names
                and isinstance(value, ast.Call)
                and (isinstance(value.func, ast.Name) and value.func.id in {"list", "len", "sum"})
            ):
                continue
            if _kernel_is_reader_assignment(node):
                continue
            return False
        if isinstance(node, ast.For):
            if not _kernel_count_for_allowed(node, tree, certificate):
                return False
    return bool(certificate.procedure_call_token and certificate.sink_token)


def _kernel_count_for_allowed(
    loop: ast.For, tree: ast.Module, certificate: CountDependenceCertificate
) -> bool:
    if not isinstance(loop.target, ast.Name) or loop.orelse:
        return False
    operand_names = {item.operand_id for item in certificate.obligation.operands}
    stored = {
        _kernel_renamed_name(tree, certificate, node, node.id)
        for node in ast.walk(loop)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    if stored & operand_names:
        return bool(
            len(loop.body) == 1
            and isinstance(loop.body[0], ast.If)
            and not loop.body[0].orelse
            and len(loop.body[0].body) == 1
            and isinstance(loop.body[0].body[0], ast.AugAssign)
            and isinstance(loop.body[0].body[0].target, ast.Name)
            and _kernel_renamed_name(
                tree,
                certificate,
                loop.body[0].body[0],
                loop.body[0].body[0].target.id,
            )
            in operand_names
            and isinstance(loop.body[0].body[0].op, ast.Add)
            and isinstance(loop.body[0].body[0].value, ast.Constant)
            and type(loop.body[0].body[0].value.value) is int
            and loop.body[0].body[0].value.value == 1
        )
    return _kernel_count_group_loop_allowed(loop, certificate)


def _kernel_count_group_loop_allowed(
    loop: ast.For, certificate: CountDependenceCertificate
) -> bool:
    if not isinstance(loop.target, ast.Name):
        return False
    columns = {
        atom.column
        for item in certificate.obligation.operands
        if item.domain_kind == "group_rows"
        for atom in item.domain_atoms
    }
    return bool(
        columns
        and len(loop.body) == 1
        and isinstance(loop.body[0], ast.Expr)
        and isinstance(loop.body[0].value, ast.Call)
        and isinstance(loop.body[0].value.func, ast.Attribute)
        and loop.body[0].value.func.attr == "append"
        and len(loop.body[0].value.args) == 1
        and not loop.body[0].value.keywords
        and isinstance(loop.body[0].value.args[0], ast.Name)
        and loop.body[0].value.args[0].id == loop.target.id
        and isinstance(loop.body[0].value.func.value, ast.Subscript)
        and _kernel_row_column(loop.body[0].value.func.value.slice, loop.target.id) in columns
    )


def _kernel_count_options_closed(
    call: ast.Call, resolved: str, constants: dict[str, object]
) -> bool:
    keywords = {item.arg: item.value for item in call.keywords if item.arg is not None}
    if len(keywords) != len(call.keywords):
        return False
    alternative = keywords.pop("alternative", None)
    if alternative is not None and not (
        isinstance(alternative, ast.Constant) and alternative.value == "two-sided"
    ):
        return False
    if resolved == "scipy.stats.binomtest":
        if len(call.args) not in {2, 3} or set(keywords) - {"p"}:
            return False
        if len(call.args) == 3 and "p" in keywords:
            return False
        p_value = call.args[2] if len(call.args) == 3 else keywords.get("p")
        if p_value is not None and _kernel_numeric_constant(p_value, constants) is None:
            return False
        return True
    return len(call.args) == 1 and not keywords


def _kernel_count_call_expressions(
    call: ast.Call, resolved: str, assignments: list[ast.Assign]
) -> tuple[ast.expr, ...] | None:
    if resolved == "scipy.stats.binomtest":
        return tuple(call.args[:2])
    table: ast.expr = call.args[0]
    if isinstance(table, ast.Name):
        matches = [
            item.value
            for item in assignments
            if len(item.targets) == 1
            and isinstance(item.targets[0], ast.Name)
            and item.targets[0].id == table.id
        ]
        if len(matches) != 1:
            return None
        table = matches[0]
    if not (
        isinstance(table, ast.List)
        and len(table.elts) == 2
        and all(isinstance(row, ast.List) and len(row.elts) == 2 for row in table.elts)
    ):
        return None
    return tuple(cell for row in table.elts if isinstance(row, ast.List) for cell in row.elts)


def _kernel_count_domains(
    tree: ast.Module,
    certificate: CountDependenceCertificate,
    constants: dict[str, object],
) -> dict[str, tuple[str, tuple[CountPredicateAtom, ...], int]]:
    domains: dict[str, tuple[str, tuple[CountPredicateAtom, ...], int]] = {}
    for assignment in (node for node in ast.walk(tree) if isinstance(node, ast.Assign)):
        if len(assignment.targets) != 1 or not isinstance(assignment.targets[0], ast.Name):
            continue
        target = _kernel_renamed_name(tree, certificate, assignment, assignment.targets[0].id)
        if _kernel_is_reader_assignment(assignment):
            domains[target] = ("rows", (), 0)
    changed = True
    while changed:
        changed = False
        for assignment in (node for node in ast.walk(tree) if isinstance(node, ast.Assign)):
            if (
                len(assignment.targets) != 1
                or not isinstance(assignment.targets[0], ast.Name)
                or not isinstance(assignment.value, ast.ListComp)
            ):
                continue
            target = _kernel_renamed_name(tree, certificate, assignment, assignment.targets[0].id)
            if target in domains:
                continue
            comp = assignment.value
            if (
                len(comp.generators) != 1
                or comp.generators[0].is_async
                or len(comp.generators[0].ifs) != 1
                or not isinstance(comp.generators[0].target, ast.Name)
                or not isinstance(comp.elt, ast.Name)
                or comp.elt.id != comp.generators[0].target.id
            ):
                continue
            source = _kernel_count_domain_expr(
                tree, certificate, comp.generators[0].iter, domains, constants
            )
            atoms = _kernel_count_predicate(comp.generators[0].ifs[0], comp.generators[0].target.id)
            if source is None or source[2] != 0 or atoms is None:
                continue
            domains[target] = ("filtered_rows", (*source[1], *atoms), 1)
            changed = True
    for loop in (node for node in ast.walk(tree) if isinstance(node, ast.For)):
        if not (
            isinstance(loop.target, ast.Name)
            and len(loop.body) == 1
            and isinstance(loop.body[0], ast.Expr)
            and isinstance(loop.body[0].value, ast.Call)
        ):
            continue
        call = loop.body[0].value
        if not (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "append"
            and len(call.args) == 1
            and isinstance(call.args[0], ast.Name)
            and call.args[0].id == loop.target.id
            and isinstance(call.func.value, ast.Subscript)
            and isinstance(call.func.value.value, ast.Name)
        ):
            continue
        column = _kernel_row_column(call.func.value.slice, loop.target.id)
        if column is not None:
            group_name = _kernel_renamed_name(tree, certificate, call, call.func.value.value.id)
            declarations = [
                item.value
                for item in ast.walk(tree)
                if isinstance(item, ast.Assign)
                and len(item.targets) == 1
                and isinstance(item.targets[0], ast.Name)
                and _kernel_renamed_name(tree, certificate, item, item.targets[0].id) == group_name
                and isinstance(item.value, ast.Dict)
                and item.value.keys
                and all(
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and isinstance(value, ast.List)
                    and not value.elts
                    for key, value in zip(item.value.keys, item.value.values, strict=True)
                )
            ]
            if len(declarations) == 1:
                domains[f"__group__:{group_name}:{column}"] = ("group_rows", (), 0)
    return domains


def _kernel_is_reader_assignment(assignment: ast.Assign) -> bool:
    value = assignment.value
    return bool(
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "list"
        and len(value.args) == 1
        and isinstance(value.args[0], ast.Call)
        and isinstance(value.args[0].func, ast.Attribute)
        and value.args[0].func.attr == "DictReader"
    )


def _kernel_count_domain_expr(
    tree: ast.Module,
    certificate: CountDependenceCertificate,
    expression: ast.expr,
    domains: dict[str, tuple[str, tuple[CountPredicateAtom, ...], int]],
    constants: dict[str, object],
) -> tuple[str, tuple[CountPredicateAtom, ...], int] | None:
    if isinstance(expression, ast.Name):
        name = _kernel_renamed_name(tree, certificate, expression, expression.id)
        return domains.get(name)
    if isinstance(expression, ast.Subscript) and isinstance(expression.value, ast.Name):
        group_name = _kernel_renamed_name(tree, certificate, expression, expression.value.id)
        key = _kernel_string_value(expression.slice, constants)
        candidates = [
            (token, domain)
            for token, domain in domains.items()
            if token.startswith(f"__group__:{group_name}:")
        ]
        if key is None or len(candidates) != 1:
            return None
        token, domain = candidates[0]
        return (
            domain[0],
            (CountPredicateAtom(token.rsplit(":", 1)[1], "eq", key),),
            0,
        )
    return None


def _kernel_count_derivation(
    tree: ast.Module,
    certificate: CountDependenceCertificate,
    name: str,
    domains: dict[str, tuple[str, tuple[CountPredicateAtom, ...], int]],
    constants: dict[str, object],
) -> tuple[str, tuple[CountPredicateAtom, ...], tuple[CountPredicateAtom, ...]] | None:
    assignments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and _kernel_renamed_name(tree, certificate, node, node.targets[0].id) == name
    ]
    for assignment in assignments:
        expression = assignment.value
        if (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and expression.func.id == "len"
            and len(expression.args) == 1
            and not expression.keywords
        ):
            domain = _kernel_count_domain_expr(
                tree, certificate, expression.args[0], domains, constants
            )
            return (domain[0], domain[1], ()) if domain is not None else None
        if (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and expression.func.id == "sum"
            and len(expression.args) == 1
            and isinstance(expression.args[0], ast.GeneratorExp)
        ):
            generator = expression.args[0]
            if (
                not isinstance(generator.elt, ast.Constant)
                or generator.elt.value != 1
                or len(generator.generators) != 1
                or not isinstance(generator.generators[0].target, ast.Name)
            ):
                return None
            domain = _kernel_count_domain_expr(
                tree, certificate, generator.generators[0].iter, domains, constants
            )
            predicates = (
                _kernel_count_predicate(
                    generator.generators[0].ifs[0], generator.generators[0].target.id
                )
                if len(generator.generators[0].ifs) == 1
                else (() if not generator.generators[0].ifs else None)
            )
            if domain is None or predicates is None:
                return None
            return domain[0], domain[1], predicates
    for loop in (node for node in ast.walk(tree) if isinstance(node, ast.For)):
        increments = [
            node
            for node in ast.walk(loop)
            if isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and _kernel_renamed_name(tree, certificate, node, node.target.id) == name
        ]
        if len(increments) != 1 or not isinstance(loop.target, ast.Name):
            continue
        if (
            len(loop.body) != 1
            or not isinstance(loop.body[0], ast.If)
            or loop.body[0].orelse
            or len(loop.body[0].body) != 1
            or loop.body[0].body[0] is not increments[0]
        ):
            return None
        domain = _kernel_count_domain_expr(tree, certificate, loop.iter, domains, constants)
        predicates = _kernel_count_predicate(loop.body[0].test, loop.target.id)
        if domain is None or predicates is None:
            return None
        return domain[0], domain[1], predicates
    return None


def _kernel_count_predicate(
    expression: ast.expr, row_name: str
) -> tuple[CountPredicateAtom, ...] | None:
    parts = (
        expression.values
        if isinstance(expression, ast.BoolOp) and isinstance(expression.op, ast.And)
        else [expression]
    )
    result: list[CountPredicateAtom] = []
    for part in parts:
        if not (
            isinstance(part, ast.Compare)
            and len(part.ops) == len(part.comparators) == 1
            and isinstance(part.ops[0], ast.Eq | ast.NotEq)
        ):
            return None
        column = _kernel_row_column(part.left, row_name)
        literal = part.comparators[0]
        if (
            column is None
            or not isinstance(literal, ast.Constant)
            or not isinstance(literal.value, str)
        ):
            return None
        result.append(
            CountPredicateAtom(
                column,
                "eq" if isinstance(part.ops[0], ast.Eq) else "ne",
                literal.value,
            )
        )
    return tuple(result)


def _kernel_count_reader_matches(
    tree: ast.Module,
    certificate: CountDependenceCertificate,
    constants: dict[str, object],
) -> bool:
    obligation = certificate.obligation
    paths: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "DictReader"
            and len(node.args) == 1
        ):
            continue
        source = node.args[0]
        if isinstance(source, ast.Name):
            for with_node in (item for item in ast.walk(tree) if isinstance(item, ast.With)):
                for item in with_node.items:
                    if (
                        isinstance(item.optional_vars, ast.Name)
                        and item.optional_vars.id == source.id
                        and isinstance(item.context_expr, ast.Call)
                        and isinstance(item.context_expr.func, ast.Attribute)
                        and item.context_expr.func.attr == "open"
                    ):
                        values = {
                            keyword.arg: keyword.value
                            for keyword in item.context_expr.keywords
                            if keyword.arg is not None
                        }
                        path = _kernel_path_value(item.context_expr.func.value, constants)
                        encoding = _kernel_string_value(values.get("encoding"), constants)
                        if (
                            path is not None
                            and encoding is not None
                            and _kernel_string_value(values.get("newline"), constants) == ""
                        ):
                            paths.append((path, encoding))
        elif (
            isinstance(source, ast.Call)
            and isinstance(source.func, ast.Attribute)
            and source.func.attr == "splitlines"
            and isinstance(source.func.value, ast.Call)
            and isinstance(source.func.value.func, ast.Attribute)
            and source.func.value.func.attr == "read_text"
        ):
            read = source.func.value
            values = {
                keyword.arg: keyword.value for keyword in read.keywords if keyword.arg is not None
            }
            assert isinstance(read.func, ast.Attribute)
            path = _kernel_path_value(read.func.value, constants)
            encoding = _kernel_string_value(values.get("encoding"), constants)
            if path is not None and encoding is not None:
                paths.append((path, encoding))
    return paths == [(obligation.path, obligation.encoding)]


def _kernel_count_sink_matches(
    tree: ast.Module,
    certificate: CountDependenceCertificate,
    constants: dict[str, object],
) -> bool:
    writes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write_text"
    ]
    if len(writes) != 1:
        return False
    write = writes[0]
    if len(write.args) != 1:
        return False
    return (
        _kernel_path_value(cast(ast.Attribute, write.func).value, constants)
        == certificate.obligation.result_path
        and _kernel_node_token(certificate.source_path, write, "selected-sink")
        == certificate.sink_token
    )


def _kernel_node_token(path: str, node: ast.AST, kind: str) -> str:
    return f"{kind}:{semantic_digest({'path': path, 'line': getattr(node, 'lineno', 0), 'column': getattr(node, 'col_offset', 0)})}"


def _kernel_replay_source_claims(
    tree: ast.Module,
    certificate: DependenceGrowthCertificate,
    fact: GroupValueSequenceFact,
) -> bool:
    """Independently replay the bounded grouping, binding, reader, and sink shapes."""

    all_constants = _kernel_constants(tree)
    if not _kernel_module_collection_uses_closed(tree, all_constants):
        return False
    constants = {name: value for name, value in all_constants.items() if isinstance(value, str)}
    if not _kernel_import_forms_closed(tree) or not _kernel_typing_uses_closed(tree):
        return False
    imports = _kernel_imports(tree)
    partition = _kernel_partition_body(tree, certificate)
    if partition is None:
        return False
    flattened, _operand_names = partition
    tree = ast.Module(body=flattened, type_ignores=[])
    if not _kernel_live_syntax_closed(tree, certificate, fact):
        return False
    appends = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "append"
    ]
    if len(appends) != 1 or len(appends[0].args) != 1 or appends[0].keywords:
        return False
    append = appends[0]
    loop = next(
        (
            parent
            for parent in ast.walk(tree)
            if isinstance(parent, ast.For) and append in set(ast.walk(parent))
        ),
        None,
    )
    if loop is None or not isinstance(loop.target, ast.Name):
        return False
    if (
        loop.orelse
        or len(loop.body) != 1
        or not isinstance(loop.body[0], ast.Expr)
        or loop.body[0].value is not append
    ):
        return False
    row_name = loop.target.id
    value = _kernel_row_value(append.args[0], row_name)
    if not isinstance(append.func, ast.Attribute):
        return False
    receiver = append.func.value
    group_name: str | None = None
    key_column: str | None = None
    if (
        isinstance(receiver, ast.Call)
        and isinstance(receiver.func, ast.Attribute)
        and receiver.func.attr == "setdefault"
        and isinstance(receiver.func.value, ast.Name)
        and len(receiver.args) == 2
        and not receiver.keywords
        and isinstance(receiver.args[1], ast.List)
        and not receiver.args[1].elts
    ):
        group_name = receiver.func.value.id
        key_column = _kernel_row_column(receiver.args[0], row_name)
    elif isinstance(receiver, ast.Subscript) and isinstance(receiver.value, ast.Name):
        group_name = receiver.value.id
        key_column = _kernel_row_column(receiver.slice, row_name)
    if group_name is None or (
        value != (fact.value_column, fact.cast_kind)
        or _kernel_renamed_name(tree, certificate, append, group_name)
        != certificate.group_container_name
        or key_column != fact.group_key_column
    ):
        return False
    declarations = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and _kernel_renamed_name(tree, certificate, node, node.targets[0].id)
        == certificate.group_container_name
    ]
    if len(declarations) != 1:
        return False
    declared_kind = (
        "defaultdict_list"
        if isinstance(declarations[0], ast.Call)
        and isinstance(declarations[0].func, ast.Name)
        and imports.get(declarations[0].func.id) == "collections.defaultdict"
        and len(declarations[0].args) == 1
        and isinstance(declarations[0].args[0], ast.Name)
        and declarations[0].args[0].id == "list"
        and not declarations[0].keywords
        else "dict"
        if isinstance(declarations[0], ast.Dict)
        or (
            isinstance(declarations[0], ast.Call)
            and isinstance(declarations[0].func, ast.Name)
            and imports.get(declarations[0].func.id) == "collections.OrderedDict"
            and not declarations[0].args
            and not declarations[0].keywords
        )
        else None
    )
    if declared_kind != certificate.group_container_kind:
        return False

    census = _kernel_group_census(tree.body, imports, certificate)
    if census is None:
        return False
    procedure_assignments, _helpers = census
    aliases = _kernel_group_aliases(tree, group_name, constants, fact)
    expected_keys = tuple(item.group_key for item in certificate.operand_bindings)
    expected_shapes: tuple[str, ...] | None = None
    for procedure_assignment in procedure_assignments:
        call = cast(ast.Call, procedure_assignment.value)
        if len(call.args) != len(certificate.operand_bindings):
            return False
        replayed_keys: list[str] = []
        shapes: list[str] = []
        for argument in call.args:
            key = _kernel_group_key(argument, group_name, constants)
            if isinstance(argument, ast.Name):
                key = aliases.get(argument.id, key)
            if key is None:
                return False
            replayed_keys.append(key)
            shapes.append(ast.dump(argument, include_attributes=False))
        if tuple(replayed_keys) != expected_keys:
            return False
        if expected_shapes is None:
            expected_shapes = tuple(shapes)
        elif tuple(shapes) != expected_shapes:
            return False

    writes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write_text"
    ]
    if len(writes) != 1:
        return False
    write = writes[0]
    if len(write.args) != 1:
        return False
    return _kernel_reader_matches(tree, fact, constants)


def _kernel_renamed_name(
    tree: ast.Module,
    certificate: DependenceGrowthCertificate | CountDependenceCertificate,
    node: ast.AST,
    original: str,
) -> str:
    owner = next(
        (
            function.name
            for function in tree.body
            if isinstance(function, ast.FunctionDef) and node in set(ast.walk(function))
        ),
        None,
    )
    if owner is None:
        return original
    function = next(
        item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == owner
    )
    parameters = [item.arg for item in function.args.args]
    if original in parameters:
        position = parameters.index(original)
        calls = [
            call
            for call in ast.walk(tree)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == owner
            and len(call.args) > position
        ]
        if len(calls) == 1 and isinstance(calls[0].args[position], ast.Name):
            argument = calls[0].args[position]
            assert isinstance(argument, ast.Name)
            return _kernel_renamed_name(tree, certificate, calls[0], argument.id)
    matches = [
        item.fresh_name
        for item in certificate.alpha_renames
        if item.function_name == owner and item.original_name == original
    ]
    return matches[0] if len(matches) == 1 else original


def _kernel_string_constants(tree: ast.Module) -> dict[str, str]:
    return {
        name: value for name, value in _kernel_constants(tree).items() if isinstance(value, str)
    }


def _kernel_constants(tree: ast.Module) -> dict[str, object]:
    values: dict[str, object] = {}
    for statement in tree.body:
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            continue
        value = statement.value
        if isinstance(value, ast.Constant) and type(value.value) in {str, int, float}:
            values[statement.targets[0].id] = value.value
        elif (
            isinstance(value, ast.Tuple)
            and value.elts
            and all(
                isinstance(item, ast.Constant) and isinstance(item.value, str)
                for item in value.elts
            )
        ):
            values[statement.targets[0].id] = tuple(
                cast(str, cast(ast.Constant, item).value) for item in value.elts
            )
        elif (
            isinstance(value, ast.Dict)
            and value.keys
            and all(
                isinstance(key, ast.Constant)
                and isinstance(key.value, str)
                and isinstance(item, ast.Constant)
                and isinstance(item.value, str)
                for key, item in zip(value.keys, value.values, strict=True)
            )
        ):
            pairs = [
                (
                    cast(str, cast(ast.Constant, key).value),
                    cast(str, cast(ast.Constant, item).value),
                )
                for key, item in zip(value.keys, value.values, strict=True)
            ]
            if len({key for key, _item in pairs}) != len(pairs):
                continue
            values[statement.targets[0].id] = dict(pairs)
        elif isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name):
            folded = _kernel_collection_subscript(values.get(value.value.id), value.slice, values)
            if folded is not None:
                values[statement.targets[0].id] = folded
        elif (path_value := _kernel_path_value(value, values)) is not None:
            values[statement.targets[0].id] = path_value
    return values


def _kernel_constant_expression(value: object) -> ast.expr:
    if isinstance(value, tuple):
        return ast.Tuple(elts=[ast.Constant(item) for item in value], ctx=ast.Load())
    if isinstance(value, dict):
        return ast.Dict(
            keys=[ast.Constant(item) for item in value],
            values=[ast.Constant(item) for item in value.values()],
        )
    return ast.Constant(cast(Any, value))


def _kernel_collection_subscript(
    collection: object, key: ast.expr, constants: dict[str, object]
) -> str | None:
    if isinstance(key, ast.Name):
        key = ast.Constant(cast(Any, constants.get(key.id)))
    if isinstance(collection, tuple):
        if not isinstance(key, ast.Constant) or type(key.value) is not int:
            return None
        index = key.value
        return collection[index] if 0 <= index < len(collection) else None
    if isinstance(collection, dict):
        if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
            return None
        value = collection.get(key.value)
        return value if isinstance(value, str) else None
    return None


def _kernel_module_collection_uses_closed(tree: ast.Module, constants: dict[str, object]) -> bool:
    collections = {
        name: value for name, value in constants.items() if isinstance(value, tuple | dict)
    }
    if not collections:
        return True
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in collections
        ):
            continue
        parent = parents.get(node)
        if isinstance(parent, ast.Subscript) and parent.value is node:
            if _kernel_collection_subscript(collections[node.id], parent.slice, constants) is None:
                return False
            continue
        if isinstance(parent, ast.For | ast.comprehension) and parent.iter is node:
            continue
        if (
            isinstance(parent, ast.Compare)
            and node in parent.comparators
            and any(isinstance(operator, ast.In | ast.NotIn) for operator in parent.ops)
        ):
            continue
        return False
    return True


def _kernel_string_value(expression: ast.expr | None, constants: dict[str, object]) -> str | None:
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return expression.value
    if isinstance(expression, ast.Name):
        value = constants.get(expression.id)
        return value if isinstance(value, str) else None
    return None


def _kernel_numeric_constant(
    expression: ast.expr, constants: dict[str, object]
) -> int | float | None:
    if isinstance(expression, ast.Constant) and type(expression.value) in {int, float}:
        return cast(int | float, expression.value)
    if isinstance(expression, ast.Name):
        value = constants.get(expression.id)
        return cast(int | float, value) if type(value) in {int, float} else None
    return None


def _kernel_path_value(expression: ast.expr, constants: dict[str, object]) -> str | None:
    divided = _kernel_path_division_value(expression)
    if divided is not None:
        return divided
    direct = _kernel_string_value(expression, constants)
    if direct is not None:
        return direct
    if (
        isinstance(expression, ast.Call)
        and (
            (isinstance(expression.func, ast.Name) and expression.func.id == "Path")
            or _kernel_attribute_chain(expression.func) == ("pathlib", "Path")
        )
        and len(expression.args) == 1
        and not expression.keywords
    ):
        return _kernel_string_value(expression.args[0], constants)
    if (
        isinstance(expression, ast.Call)
        and _kernel_attribute_chain(expression.func) == ("os", "path", "join")
        and len(expression.args) >= 2
        and not expression.keywords
        and all(
            isinstance(argument, ast.Constant) and isinstance(argument.value, str)
            for argument in expression.args
        )
    ):
        return posixpath.join(
            *(
                str(argument.value)
                for argument in expression.args
                if isinstance(argument, ast.Constant)
            )
        )
    if (
        isinstance(expression, ast.Call)
        and _kernel_attribute_chain(expression.func) == ("os", "path", "dirname")
        and len(expression.args) == 1
        and not expression.keywords
    ):
        path = _kernel_path_value(expression.args[0], constants)
        return posixpath.dirname(path) if path is not None else None
    return None


def _kernel_path_division_value(expression: ast.expr) -> str | None:
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "Path"
        and len(expression.args) == 1
        and not expression.keywords
        and isinstance(expression.args[0], ast.Constant)
        and isinstance(expression.args[0].value, str)
    ):
        return expression.args[0].value
    if not (
        isinstance(expression, ast.BinOp)
        and isinstance(expression.op, ast.Div)
        and isinstance(expression.right, ast.Constant)
        and isinstance(expression.right.value, str)
    ):
        return None
    left = _kernel_path_division_value(expression.left)
    return posixpath.join(left, expression.right.value) if left is not None else None


def _kernel_attribute_chain(expression: ast.expr) -> tuple[str, ...] | None:
    parts: list[str] = []
    while isinstance(expression, ast.Attribute):
        parts.append(expression.attr)
        expression = expression.value
    return (expression.id, *reversed(parts)) if isinstance(expression, ast.Name) else None


def _kernel_imports(tree: ast.Module) -> dict[str, str]:
    values: dict[str, str] = {}
    for statement in tree.body:
        if isinstance(statement, ast.ImportFrom) and statement.level == 0:
            for alias in statement.names:
                local = alias.asname or alias.name
                values[local] = f"{statement.module}.{alias.name}"
        elif isinstance(statement, ast.Import):
            for alias in statement.names:
                values[alias.asname or alias.name.split(".")[0]] = alias.name
    return values


def _kernel_import_forms_closed(tree: ast.Module) -> bool:
    allowed_imports = {
        ("numpy", "np"),
        ("math", None),
        ("pathlib", None),
        ("csv", None),
        ("os", None),
        ("statistics", None),
    }
    future_index = (
        1
        if tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
        else 0
    )
    future_statement = tree.body[future_index] if future_index < len(tree.body) else None
    future_annotations = bool(
        isinstance(future_statement, ast.ImportFrom)
        and future_statement.level == 0
        and future_statement.module == "__future__"
        and len(future_statement.names) == 1
        and future_statement.names[0].name == "annotations"
        and future_statement.names[0].asname is None
    )
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            if len(statement.names) != 1:
                return False
            alias = statement.names[0]
            if (alias.name, alias.asname) not in allowed_imports:
                return False
        elif isinstance(statement, ast.ImportFrom):
            if statement.level or not statement.names:
                return False
            if (
                statement.module in {"__future__", "dataclasses", "scipy"}
                and len(statement.names) != 1
            ):
                return False
            for alias in statement.names:
                if alias.asname is not None or alias.name == "*":
                    return False
                if statement.module == "typing":
                    if not future_annotations:
                        return False
                    continue
                if (statement.module, alias.name) not in {
                    ("__future__", "annotations"),
                    ("dataclasses", "dataclass"),
                    ("pathlib", "Path"),
                    ("scipy", "stats"),
                    ("collections", "defaultdict"),
                    ("collections", "OrderedDict"),
                    *(
                        ("statistics", name)
                        for name in {"fmean", "mean", "stdev", "median", "variance"}
                    ),
                    *(
                        ("scipy.stats", name.rsplit(".", 1)[1])
                        for name in (_GROUP_BASE_PROCEDURES | _COUNT_PROCEDURES)
                    ),
                }:
                    return False
    return True


def _kernel_annotation_nodes(root: ast.AST) -> set[ast.AST]:
    expressions: list[ast.expr] = []
    for node in ast.walk(root):
        if isinstance(node, ast.AnnAssign):
            expressions.append(node.annotation)
        elif isinstance(node, ast.arg) and node.annotation is not None:
            expressions.append(node.annotation)
        elif isinstance(node, ast.FunctionDef) and node.returns is not None:
            expressions.append(node.returns)
    return {node for expression in expressions for node in ast.walk(expression)}


def _kernel_typing_uses_closed(tree: ast.Module) -> bool:
    imports = _kernel_imports(tree)
    typing_names = {name for name, target in imports.items() if target.startswith("typing.")}
    if not typing_names:
        return True
    annotation_nodes = _kernel_annotation_nodes(tree)
    return not any(
        isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node.id in typing_names
        and node not in annotation_nodes
        for node in ast.walk(tree)
    )


def _kernel_partition_operand_names(
    body: list[ast.stmt], procedures: tuple[ast.Assign, ...]
) -> set[str]:
    """Derive the sole kernel-side operand definition used by the sink partition."""

    definitions: dict[str, list[ast.expr]] = {}
    for statement in body:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            definitions.setdefault(statement.targets[0].id, []).append(statement.value)
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.value is not None
        ):
            definitions.setdefault(statement.target.id, []).append(statement.value)
    operands = {
        node.id
        for procedure in procedures
        for node in ast.walk(procedure.value)
        if isinstance(node, ast.Name)
    }
    operands.update(
        node.id
        for statement in body
        if isinstance(statement, ast.With | ast.For)
        for node in ast.walk(statement)
        if isinstance(node, ast.Name)
    )
    changed = True
    while changed:
        changed = False
        for name in tuple(operands):
            values = definitions.get(name)
            if values is None:
                continue
            for value in values:
                for node in ast.walk(value):
                    if isinstance(node, ast.Name) and node.id not in operands:
                        operands.add(node.id)
                        changed = True
        for name, values in definitions.items():
            if name in operands:
                continue
            if any(
                isinstance(value, ast.Subscript)
                and isinstance(value.value, ast.Name)
                and value.value.id in operands
                and not isinstance(value.slice, ast.Slice)
                for value in values
            ):
                operands.add(name)
                changed = True
    return operands


def _kernel_partition_operand_aliases(body: list[ast.stmt], operands: set[str]) -> set[str]:
    aliases: set[str] = set()
    changed = True
    while changed:
        changed = False
        protected = operands | aliases
        for statement in body:
            target: ast.Name | None = None
            value: ast.expr | None = None
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                target, value = statement.targets[0], statement.value
            elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                target, value = statement.target, statement.value
            if (
                target is not None
                and isinstance(value, ast.Name)
                and value.id in protected
                and target.id not in protected
            ):
                aliases.add(target.id)
                changed = True
    return aliases


def _kernel_scipy_stats_callable(expression: ast.expr, imports: dict[str, str]) -> str | None:
    parts: list[str] = []
    while isinstance(expression, ast.Attribute):
        parts.append(expression.attr)
        expression = expression.value
    if not isinstance(expression, ast.Name):
        return None
    root = imports.get(expression.id)
    if root is None:
        return None
    value = ".".join((root, *reversed(parts)))
    return value if value.startswith("scipy.stats.") else None


def _kernel_group_variant(call: ast.Call, resolved: str) -> str | None:
    if resolved == "scipy.stats.ttest_ind":
        if len(call.args) != 2 or any(
            item.arg not in {"equal_var", "alternative"} for item in call.keywords
        ):
            return None
        equal_var = True
        for item in call.keywords:
            if item.arg == "equal_var":
                if not isinstance(item.value, ast.Constant) or type(item.value.value) is not bool:
                    return None
                equal_var = bool(item.value.value)
            elif item.arg == "alternative" and not (
                isinstance(item.value, ast.Constant)
                and item.value.value in {"two-sided", "less", "greater"}
            ):
                return None
        return resolved if equal_var else "scipy.stats.ttest_ind:welch"
    if resolved == "scipy.stats.mannwhitneyu":
        if len(call.args) != 2:
            return None
        allowed = {
            "alternative": {"two-sided", "less", "greater"},
            "method": {"auto", "exact", "asymptotic"},
        }
        if any(item.arg not in allowed for item in call.keywords):
            return None
        if any(
            not isinstance(item.value, ast.Constant)
            or not isinstance(item.value.value, str)
            or item.value.value not in allowed[cast(str, item.arg)]
            for item in call.keywords
        ):
            return None
        return resolved
    return None


def _kernel_group_census(
    body: list[ast.stmt],
    imports: dict[str, str],
    certificate: DependenceGrowthCertificate,
) -> tuple[tuple[ast.Assign, ...], tuple[tuple[ast.Assign, str, ast.Call], ...]] | None:
    """Re-derive H-1's ordered census without trusting analyzer classification."""

    parents = {
        child: parent
        for statement in body
        for parent in ast.walk(statement)
        for child in ast.iter_child_nodes(parent)
    }
    procedures: list[ast.Assign] = []
    variants: list[str] = []
    helpers: list[tuple[ast.Assign, str, ast.Call]] = []
    for statement in body:
        for call in (node for node in ast.walk(statement) if isinstance(node, ast.Call)):
            resolved = _kernel_scipy_stats_callable(call.func, imports)
            if resolved is None:
                continue
            if resolved in _GROUP_BASE_PROCEDURES:
                if not (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                    and statement.value is call
                ):
                    return None
                variant = _kernel_group_variant(call, resolved)
                if variant is None:
                    return None
                procedures.append(statement)
                variants.append(variant)
            elif resolved in _COUNT_PROCEDURES:
                return None
            elif resolved in _DISTRIBUTION_HELPER_METHODS:
                if not (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                    and statement.value is call
                ):
                    return None
                helpers.append((statement, statement.targets[0].id, call))
            elif not (isinstance(parents.get(call), ast.Attribute) and parents[call] is call.func):
                return None
    if (
        not procedures
        or tuple(variants) != certificate.resolved_callables
        or tuple(
            _kernel_node_token(certificate.source_path, statement.value, "procedure-call")
            for statement in procedures
            if isinstance(statement.value, ast.Call)
        )
        != certificate.procedure_call_tokens
        or tuple(cast(ast.Name, statement.targets[0]).id for statement in procedures)
        != certificate.result_names
    ):
        return None
    helper_targets = {target for _statement, target, _call in helpers}
    if any(
        sum(
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == target
            for statement in body
        )
        != 1
        for target in helper_targets
    ):
        return None
    return tuple(procedures), tuple(helpers)


def _kernel_lower_annotations_for_partition(
    body: list[ast.stmt], operands: set[str]
) -> list[ast.stmt] | None:
    normalized: list[ast.stmt] = []
    for statement in body:
        if not isinstance(statement, ast.AnnAssign):
            normalized.append(statement)
            continue
        if not isinstance(statement.target, ast.Name) or statement.target.id in operands:
            return None
        if statement.value is None:
            continue
        normalized.append(
            ast.copy_location(
                ast.Assign(targets=[copy.deepcopy(statement.target)], value=statement.value),
                statement,
            )
        )
    return normalized


def _kernel_partition_body(
    tree: ast.Module,
    certificate: DependenceGrowthCertificate | CountDependenceCertificate,
) -> tuple[list[ast.stmt], set[str]] | None:
    body = _kernel_flattened_module(tree, certificate)
    if body is None:
        return None
    imports = _kernel_imports(tree)
    if isinstance(certificate, CountDependenceCertificate):
        procedures = tuple(
            statement
            for statement in body
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Call)
            and _kernel_resolved_call(statement.value.func, imports)
            == certificate.resolved_callable
        )
        if len(procedures) != 1:
            return None
    else:
        census = _kernel_group_census(body, imports, certificate)
        if census is None:
            return None
        procedures, helpers = census
    operands = _kernel_partition_operand_names(body, procedures)
    if _kernel_rebound_operand_names(body, operands):
        return None
    if not isinstance(certificate, CountDependenceCertificate) and any(
        target in operands for _statement, target, _call in helpers
    ):
        return None
    annotation_protected_names = operands | _kernel_partition_operand_aliases(body, operands)
    normalized = _kernel_lower_annotations_for_partition(body, annotation_protected_names)
    return (normalized, operands) if normalized is not None else None


def _kernel_rebound_operand_names(body: list[ast.stmt], operands: set[str]) -> set[str]:
    """Independently reject every multiply bound partition operand name."""

    def bound_names(target: ast.expr) -> set[str]:
        if isinstance(target, ast.Name):
            return {target.id}
        if isinstance(target, ast.List | ast.Tuple):
            return set().union(*(bound_names(item) for item in target.elts))
        if isinstance(target, ast.Starred):
            return bound_names(target.value)
        return set()

    counts: Counter[str] = Counter()
    for statement in body:
        for node in ast.walk(statement):
            targets: tuple[ast.expr, ...] = ()
            if isinstance(node, ast.Assign):
                targets = tuple(node.targets)
            elif isinstance(node, ast.AnnAssign | ast.AugAssign | ast.NamedExpr):
                targets = (node.target,)
            elif isinstance(node, ast.For | ast.AsyncFor):
                targets = (node.target,)
            elif isinstance(node, ast.With | ast.AsyncWith):
                targets = tuple(
                    item.optional_vars for item in node.items if item.optional_vars is not None
                )
            for target in targets:
                counts.update(bound_names(target) & operands)
    return {name for name, count in counts.items() if count > 1}


def _kernel_live_syntax_closed(
    tree: ast.Module,
    certificate: DependenceGrowthCertificate,
    fact: GroupValueSequenceFact,
) -> bool:
    """Close statement syntax before the dedicated semantic replayers run."""

    if sum(isinstance(node, ast.For) for node in ast.walk(tree)) != 1:
        return False
    if any(
        isinstance(
            node,
            ast.While
            | ast.AsyncFor
            | ast.AsyncWith
            | ast.Try
            | ast.Match
            | ast.ListComp
            | ast.SetComp
            | ast.DictComp
            | ast.GeneratorExp
            | ast.Raise
            | ast.Assert
            | ast.Yield
            | ast.YieldFrom
            | ast.Await,
        )
        for node in ast.walk(tree)
    ):
        return False
    group_originals = {
        item.original_name
        for item in certificate.alpha_renames
        if item.fresh_name == certificate.group_container_name
    }
    group_names = {*group_originals, certificate.group_container_name}
    for node in ast.walk(tree):
        if isinstance(node, ast.AugAssign | ast.AnnAssign | ast.NamedExpr | ast.Delete):
            return False
    return set(fact.predeclared_bucket_keys) == _kernel_predeclared_keys(tree, group_names)


def _kernel_main_guard(node: ast.If) -> bool:
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == len(test.comparators) == 1
        and isinstance(test.ops[0], ast.Eq)
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
        and not node.orelse
    )


def _kernel_call_allowed(
    node: ast.Call,
    functions: set[str],
    group_names: set[str],
    imports: dict[str, str],
    constants: dict[str, object],
) -> bool:
    if _kernel_path_value(node, constants) is not None or _kernel_closed_makedirs(node, constants):
        return True
    if isinstance(node.func, ast.Name):
        return (
            node.func.id in functions | {"Path", "list", "float", "int", "str", "sorted"}
            or imports.get(node.func.id) in _PROCEDURE_ARITY
        )
    if not isinstance(node.func, ast.Attribute):
        return False
    resolved_stats = _kernel_scipy_stats_callable(node.func, imports)
    if resolved_stats in _DISTRIBUTION_HELPER_METHODS:
        return True
    if isinstance(node.func.value, ast.Name):
        base = node.func.value.id
        if base in group_names and node.func.attr in {"setdefault", "items"}:
            return True
        if imports.get(base) == "csv" and node.func.attr == "DictReader":
            return True
        if (
            imports.get(base) == "scipy.stats"
            and f"scipy.stats.{node.func.attr}" in _PROCEDURE_ARITY
        ):
            return True
        if imports.get(base) == "numpy" and node.func.attr in {"array", "asarray"}:
            return True
        if imports.get(base) == "pathlib" and node.func.attr == "Path":
            return True
        if node.func.attr in {"open", "read_text", "write_text"}:
            return True
    if isinstance(node.func.value, ast.Call) and node.func.attr == "append":
        inner = node.func.value
        return (
            isinstance(inner.func, ast.Attribute)
            and isinstance(inner.func.value, ast.Name)
            and inner.func.value.id in group_names
            and inner.func.attr == "setdefault"
        )
    if isinstance(node.func.value, ast.Subscript) and node.func.attr == "append":
        return (
            isinstance(node.func.value.value, ast.Name) and node.func.value.value.id in group_names
        )
    return (
        node.func.attr == "items"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in group_names
    )


def _kernel_closed_makedirs(node: ast.Call, constants: dict[str, object]) -> bool:
    return bool(
        _kernel_attribute_chain(node.func) == ("os", "makedirs")
        and len(node.args) == 1
        and len(node.keywords) == 1
        and node.keywords[0].arg == "exist_ok"
        and isinstance(node.keywords[0].value, ast.Constant)
        and node.keywords[0].value.value is True
        and _kernel_path_value(node.args[0], constants) is not None
    )


def _kernel_assignment_allowed(
    node: ast.Assign,
    functions: set[str],
    group_names: set[str],
    constants: dict[str, object],
    imports: dict[str, str],
) -> bool:
    if len(node.targets) != 1:
        return False
    target = node.targets[0]
    if isinstance(target, ast.Name) and target.id in constants:
        return True
    if (
        isinstance(target, ast.Name)
        and target.id in group_names
        and isinstance(node.value, ast.Dict)
    ):
        return True
    if isinstance(target, ast.Tuple):
        return (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "sorted"
        )
    if not isinstance(target, ast.Name):
        return False
    if isinstance(node.value, ast.Call):
        if isinstance(node.value.func, ast.Name) and node.value.func.id in functions | {"list"}:
            return True
        if _kernel_callable(node.value.func, imports) is not None or (
            _kernel_scipy_stats_callable(node.value.func, imports) in _DISTRIBUTION_HELPER_METHODS
        ):
            return True
    return any(
        _kernel_group_key(node.value, group_name, cast(dict[str, str], constants)) is not None
        for group_name in group_names
    )


def _kernel_predeclared_keys(tree: ast.Module, group_names: set[str]) -> set[str]:
    keys: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in group_names
            and isinstance(node.value, ast.Dict)
        ):
            keys.update(
                item.value
                for item in node.value.keys
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            )
    return keys


def _kernel_callable(expression: ast.expr, imports: dict[str, str]) -> str | None:
    if isinstance(expression, ast.Name):
        value = imports.get(expression.id)
        return value if value in _ALL_PROCEDURES else None
    if isinstance(expression, ast.Attribute) and isinstance(expression.value, ast.Name):
        base = imports.get(expression.value.id)
        value = f"{base}.{expression.attr}"
        return value if value in _ALL_PROCEDURES else None
    return None


def _kernel_row_column(expression: ast.expr, row_name: str) -> str | None:
    if (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.value, ast.Name)
        and expression.value.id == row_name
        and isinstance(expression.slice, ast.Constant)
        and isinstance(expression.slice.value, str)
    ):
        return expression.slice.value
    return None


def _kernel_row_value(expression: ast.expr, row_name: str) -> tuple[str, str] | None:
    direct = _kernel_row_column(expression, row_name)
    if direct is not None:
        return direct, "none"
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id in {"float", "int"}
        and len(expression.args) == 1
        and not expression.keywords
    ):
        column = _kernel_row_column(expression.args[0], row_name)
        if column is not None:
            return column, expression.func.id
    return None


def _kernel_group_key(
    expression: ast.expr, group_name: str, constants: dict[str, str]
) -> str | None:
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and isinstance(expression.func.value, ast.Name)
        and expression.func.value.id == "np"
        and expression.func.attr in {"array", "asarray"}
        and len(expression.args) == 1
    ):
        if any(item.arg != "dtype" for item in expression.keywords):
            return None
        if expression.keywords and not (
            len(expression.keywords) == 1
            and isinstance(expression.keywords[0].value, ast.Name)
            and expression.keywords[0].value.id == "float"
        ):
            return None
        expression = expression.args[0]
    if not (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.value, ast.Name)
        and expression.value.id == group_name
    ):
        return None
    if isinstance(expression.slice, ast.Constant) and isinstance(expression.slice.value, str):
        return expression.slice.value
    if isinstance(expression.slice, ast.Name):
        return constants.get(expression.slice.id)
    return None


def _kernel_group_aliases(
    tree: ast.Module,
    group_name: str,
    constants: dict[str, str],
    fact: GroupValueSequenceFact,
) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            if isinstance(node.targets[0], ast.Name):
                key = _kernel_group_key(node.value, group_name, constants)
                if key is not None:
                    aliases[node.targets[0].id] = key
            if (
                isinstance(node.targets[0], ast.Tuple)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "sorted"
                and len(node.value.args) == 1
                and not node.value.keywords
                and isinstance(node.value.args[0], ast.Call)
                and isinstance(node.value.args[0].func, ast.Attribute)
                and isinstance(node.value.args[0].func.value, ast.Name)
                and node.value.args[0].func.value.id == group_name
                and node.value.args[0].func.attr == "items"
                and not node.value.args[0].args
                and not node.value.args[0].keywords
            ):
                keys = sorted(item.group_key for item in fact.groups)
                if len(node.targets[0].elts) != len(keys):
                    return {}
                for index, element in enumerate(node.targets[0].elts):
                    if (
                        not isinstance(element, ast.Tuple)
                        or len(element.elts) != 2
                        or not isinstance(element.elts[1], ast.Name)
                    ):
                        return {}
                    aliases[element.elts[1].id] = keys[index]
    return aliases


def _kernel_reader_matches(
    tree: ast.Module, fact: GroupValueSequenceFact, constants: dict[str, str]
) -> bool:
    encodings: list[str] = []
    paths: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"open", "read_text"}:
            continue
        keywords = {item.arg: item.value for item in node.keywords if item.arg is not None}
        encoding = keywords.get("encoding")
        if isinstance(encoding, ast.Constant) and isinstance(encoding.value, str):
            encodings.append(encoding.value.lower())
            base = node.func.value
            if isinstance(base, ast.Name) and base.id in constants:
                paths.append(constants[base.id])
            elif isinstance(base, ast.Constant) and isinstance(base.value, str):
                paths.append(base.value)
            elif isinstance(base, ast.Name):
                resolved = _kernel_parameter_string(tree, node, base.id, constants)
                if resolved is not None:
                    paths.append(resolved)
    return encodings == [fact.encoding] and paths == [fact.path]


def _kernel_parameter_string(
    tree: ast.Module,
    node: ast.AST,
    name: str,
    constants: dict[str, str],
) -> str | None:
    owner = next(
        (
            function
            for function in tree.body
            if isinstance(function, ast.FunctionDef) and node in set(ast.walk(function))
        ),
        None,
    )
    if owner is None:
        return constants.get(name)
    parameters = [item.arg for item in owner.args.args]
    if name not in parameters:
        return constants.get(name)
    position = parameters.index(name)
    calls = [
        call
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == owner.name
        and len(call.args) > position
    ]
    if len(calls) != 1:
        return None
    argument = calls[0].args[position]
    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
        return argument.value
    if isinstance(argument, ast.Name):
        return _kernel_parameter_string(tree, calls[0], argument.id, constants)
    return None


def _kernel_replay_function_bookkeeping(
    tree: ast.Module,
    certificate: DependenceGrowthCertificate | CountDependenceCertificate,
) -> bool:
    functions = {item.name: item for item in tree.body if isinstance(item, ast.FunctionDef)}
    imports = _kernel_imports(tree)
    import_names = set(imports)
    typing_names = {name for name, target in imports.items() if target.startswith("typing.")}
    constants = set(_kernel_constants(tree))
    if any(
        not _kernel_function_shape_closed(
            item, import_names, typing_names, constants, set(functions)
        )
        for item in functions.values()
    ):
        return False
    graph = {
        name: {
            node.func.id
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in functions
        }
        for name, function in functions.items()
    }
    if _kernel_graph_cyclic(graph):
        return False
    roots = {
        node.func.id
        for statement in tree.body
        if not isinstance(statement, ast.FunctionDef)
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in functions
    }
    if functions and any(
        node.args or node.keywords
        for statement in tree.body
        if not isinstance(statement, ast.FunctionDef)
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in functions
    ):
        return False
    called: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in called:
            continue
        called.add(name)
        pending.extend(graph[name])
    if any(_kernel_graph_depth(root, graph) > 3 for root in roots):
        return False
    sites = _kernel_call_sites(tree, functions)
    expected_pairs: set[tuple[str, str, str, str, tuple[int, int, int, int]]] = set()
    for name, call_path_id, span in sites:
        function = functions[name]
        originals = {item.arg for item in function.args.args}
        originals.update(
            node.id
            for node in ast.walk(function)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
        )
        call_number = call_path_id.rsplit(":", 1)[-1]
        expected_pairs.update(
            (
                name,
                call_path_id,
                original,
                f"__dependence_v2_{call_number}_{original}",
                span,
            )
            for original in originals
        )
    actual_pairs = {
        (
            item.function_name,
            item.call_path_id,
            item.original_name,
            item.fresh_name,
            item.call_span,
        )
        for item in certificate.alpha_renames
    }
    caller_visible = (
        {
            node.id
            for statement in tree.body
            for node in ast.walk(statement)
            if isinstance(node, ast.Name)
        }
        | set(functions)
        | import_names
        | constants
    )
    fresh = [item.fresh_name for item in certificate.alpha_renames]
    expected_dead = tuple(sorted(f"dead-function:{name}" for name in set(functions) - called))
    return (
        actual_pairs == expected_pairs
        and len(fresh) == len(set(fresh))
        and not set(fresh) & caller_visible
        and certificate.dead_syntactic_construct_tokens == expected_dead
    )


class _KernelInlineTransformer(ast.NodeTransformer):
    def __init__(self, arguments: dict[str, ast.expr], names: dict[str, str]) -> None:
        self.arguments = arguments
        self.names = names

    def visit_Name(self, node: ast.Name) -> ast.expr:
        if isinstance(node.ctx, ast.Load) and node.id in self.arguments:
            return ast.copy_location(copy.deepcopy(self.arguments[node.id]), node)
        if node.id in self.names:
            return ast.copy_location(ast.Name(self.names[node.id], node.ctx), node)
        return node


def _kernel_flattened_module(
    tree: ast.Module, certificate: DependenceGrowthCertificate | CountDependenceCertificate
) -> list[ast.stmt] | None:
    """Independently replay inlining; certificate names are used only after injectivity replay."""

    functions = {item.name: item for item in tree.body if isinstance(item, ast.FunctionDef)}
    constants = _kernel_constants(tree)
    rename_map = {
        (item.function_name, item.call_path_id, item.original_name): item.fresh_name
        for item in certificate.alpha_renames
    }
    counter = 0

    def inline(
        statements: list[ast.stmt], parent: tuple[str, ...], depth: int
    ) -> list[ast.stmt] | None:
        nonlocal counter
        result: list[ast.stmt] = []
        for statement in statements:
            if (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Call)
                and isinstance(statement.value.func, ast.Attribute)
                and statement.value.func.attr == "write_text"
                and statement.value.args
            ):
                sink_result = inline_sink_expression(statement.value.args[0], parent, depth)
                if sink_result is None:
                    return None
                prefix, payload = sink_result
                if prefix or ast.dump(payload, include_attributes=False) != ast.dump(
                    statement.value.args[0], include_attributes=False
                ):
                    sink_statement = copy.deepcopy(statement)
                    assert isinstance(sink_statement, ast.Expr)
                    assert isinstance(sink_statement.value, ast.Call)
                    sink_statement.value.args[0] = payload
                    result.extend(prefix)
                    result.append(sink_statement)
                    continue
            target: ast.expr | None = None
            call: ast.Call | None = None
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
                call = statement.value
            elif (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.value, ast.Call)
            ):
                target, call = statement.targets[0], statement.value
            if not (
                call is not None and isinstance(call.func, ast.Name) and call.func.id in functions
            ):
                result.append(copy.deepcopy(statement))
                continue
            if depth >= MAX_V2_INLINE_DEPTH:
                return None
            function = functions[call.func.id]
            if call.keywords or len(call.args) != len(function.args.args):
                return None
            counter += 1
            path = (*parent, f"{call.func.id}:{counter}")
            path_id = "inline-call-path:" + "/".join(path)
            parameters = [item.arg for item in function.args.args]
            arguments = {
                name: copy.deepcopy(_kernel_constant_expression(constants[item.id]))
                if isinstance(item, ast.Name) and item.id in constants
                else copy.deepcopy(item)
                for name, item in zip(parameters, call.args, strict=True)
            }
            stored = {
                node.id
                for node in ast.walk(function)
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
            }
            originals = [*parameters, *sorted(stored - set(parameters))]
            names = {
                name: rename_map[(function.name, path_id, name)]
                for name in originals
                if (function.name, path_id, name) in rename_map
            }
            if len(names) != len(originals):
                return None
            # Replay module-constant substitution in callee scope before alpha
            # renaming, excluding parameter/local shadows.
            bound_names = set(parameters) | stored
            callee_constants = {
                name: value for name, value in constants.items() if name not in bound_names
            }
            constant_transformer = _KernelConstantTransformer(callee_constants)
            constant_body = [
                constant_transformer.visit(copy.deepcopy(item)) for item in function.body
            ]
            transformer = _KernelInlineTransformer(arguments, names)
            nested = [
                ast.fix_missing_locations(cast(ast.stmt, transformer.visit(item)))
                for item in constant_body
            ]
            return_value: ast.expr | None = None
            nested_return: str | None = None
            if nested and isinstance(nested[-1], ast.Return):
                return_value = cast(ast.Return, nested.pop()).value
            elif (
                nested
                and isinstance(nested[-1], ast.With)
                and nested[-1].body
                and isinstance(nested[-1].body[-1], ast.Return)
            ):
                returned = cast(ast.Return, nested[-1].body.pop())
                if returned.value is not None:
                    nested_return = f"__dependence_v2_{counter}_return"
                    nested[-1].body.append(
                        ast.Assign([ast.Name(nested_return, ast.Store())], returned.value)
                    )
            flattened = inline(nested, path, depth + 1)
            if flattened is None:
                return None
            result.extend(flattened)
            if return_value is not None:
                return_result = inline_sink_expression(return_value, path, depth + 1)
                if return_result is None:
                    return None
                return_prefix, return_value = return_result
                result.extend(return_prefix)
            if target is not None:
                value = (
                    ast.Name(nested_return, ast.Load())
                    if nested_return is not None
                    else return_value
                    if return_value is not None
                    else ast.Constant(None)
                )
                result.append(ast.Assign([copy.deepcopy(target)], value))
            elif nested_return is not None:
                result.append(ast.Expr(ast.Name(nested_return, ast.Load())))
            elif return_value is not None:
                result.append(ast.Expr(return_value))
        return result

    def inline_sink_expression(
        expression: ast.expr, parent: tuple[str, ...], depth: int
    ) -> tuple[list[ast.stmt], ast.expr] | None:
        if (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and expression.func.id in functions
        ):
            placeholder = ast.Name("__dependence_v2_sink_placeholder", ast.Store())
            flattened = inline(
                [ast.Assign([placeholder], copy.deepcopy(expression))], parent, depth
            )
            if not flattened or not isinstance(flattened[-1], ast.Assign):
                return None
            final_assignment = flattened.pop()
            assert isinstance(final_assignment, ast.Assign)
            replacement = final_assignment.value
            nested_result = inline_sink_expression(replacement, parent, depth)
            if nested_result is None:
                return None
            nested_prefix, replacement = nested_result
            return [*flattened, *nested_prefix], replacement

        prefix: list[ast.stmt] = []
        normalized = copy.deepcopy(expression)
        for field, value in ast.iter_fields(normalized):
            if isinstance(value, ast.expr):
                nested_result = inline_sink_expression(value, parent, depth)
                if nested_result is None:
                    return None
                nested, replacement = nested_result
                prefix.extend(nested)
                setattr(normalized, field, replacement)
            elif isinstance(value, list):
                replacements: list[object] = []
                for item in value:
                    if isinstance(item, ast.expr):
                        nested_result = inline_sink_expression(item, parent, depth)
                        if nested_result is None:
                            return None
                        nested, replacement = nested_result
                        prefix.extend(nested)
                        replacements.append(replacement)
                    else:
                        replacements.append(item)
                setattr(normalized, field, replacements)
        return prefix, normalized

    executable: list[ast.stmt] = []
    for item in tree.body:
        if isinstance(item, ast.FunctionDef | ast.Import | ast.ImportFrom):
            continue
        if (
            isinstance(item, ast.Assign)
            and len(item.targets) == 1
            and isinstance(item.targets[0], ast.Name)
            and item.targets[0].id in constants
        ):
            continue
        if isinstance(item, ast.If) and _kernel_main_guard(item):
            executable.extend(item.body)
        else:
            executable.append(item)
    flattened = inline(executable, (), 0)
    if flattened is None:
        return None
    transformer = _KernelConstantTransformer(constants)
    return [
        ast.fix_missing_locations(cast(ast.stmt, transformer.visit(copy.deepcopy(item))))
        for item in flattened
    ]


class _KernelConstantTransformer(ast.NodeTransformer):
    def __init__(self, constants: dict[str, object]) -> None:
        self.constants = constants

    def visit_Name(self, node: ast.Name) -> ast.expr:
        if isinstance(node.ctx, ast.Load) and node.id in self.constants:
            return ast.copy_location(_kernel_constant_expression(self.constants[node.id]), node)
        return node

    def visit_Subscript(self, node: ast.Subscript) -> ast.expr:
        original_value = node.value
        visited = cast(ast.Subscript, self.generic_visit(node))
        if isinstance(original_value, ast.Name) and original_value.id in self.constants:
            folded = _kernel_collection_subscript(
                self.constants[original_value.id], visited.slice, self.constants
            )
            if folded is not None:
                return ast.copy_location(ast.Constant(folded), node)
        return visited


def _kernel_statement_token(statement: ast.stmt, index: int) -> str:
    return "flattened-statement:" + semantic_digest(
        {"index": index, "syntax": ast.dump(statement, include_attributes=False)}
    )


def _kernel_sink_expression_closed(
    expression: ast.expr, operands: set[str], scalar_sequences: set[str]
) -> bool:
    if isinstance(expression, ast.Name | ast.Constant):
        return True
    if isinstance(expression, ast.Slice):
        return all(
            item is None or _kernel_sink_expression_closed(item, operands, scalar_sequences)
            for item in (expression.lower, expression.upper, expression.step)
        )
    if isinstance(expression, ast.Subscript):
        return (
            (
                not (isinstance(expression.value, ast.Name) and expression.value.id in operands)
                or (
                    isinstance(expression.slice, ast.Slice)
                    and expression.value.id in scalar_sequences
                )
            )
            and _kernel_sink_expression_closed(expression.value, operands, scalar_sequences)
            and _kernel_sink_expression_closed(expression.slice, operands, scalar_sequences)
        )
    if isinstance(expression, ast.List | ast.Tuple | ast.Set):
        return all(
            not (isinstance(item, ast.Name) and item.id in operands)
            and _kernel_sink_expression_closed(item, operands, scalar_sequences)
            for item in expression.elts
        )
    if isinstance(expression, ast.Dict):
        return all(
            item is None
            or (
                not (isinstance(item, ast.Name) and item.id in operands)
                and _kernel_sink_expression_closed(item, operands, scalar_sequences)
            )
            for item in (*expression.keys, *expression.values)
        )
    if isinstance(expression, ast.BinOp):
        return _kernel_sink_expression_closed(
            expression.left, operands, scalar_sequences
        ) and _kernel_sink_expression_closed(expression.right, operands, scalar_sequences)
    if isinstance(expression, ast.UnaryOp):
        return _kernel_sink_expression_closed(expression.operand, operands, scalar_sequences)
    if isinstance(expression, ast.BoolOp):
        return all(
            _kernel_sink_expression_closed(item, operands, scalar_sequences)
            for item in expression.values
        )
    if isinstance(expression, ast.Compare):
        return _kernel_sink_expression_closed(expression.left, operands, scalar_sequences) and all(
            _kernel_sink_expression_closed(item, operands, scalar_sequences)
            for item in expression.comparators
        )
    if isinstance(expression, ast.JoinedStr):
        return all(
            not isinstance(item, ast.FormattedValue)
            or (
                _kernel_sink_expression_closed(item.value, operands, scalar_sequences)
                and (
                    item.format_spec is None
                    or _kernel_sink_expression_closed(item.format_spec, operands, scalar_sequences)
                )
            )
            for item in expression.values
        )
    if isinstance(expression, ast.IfExp):
        return all(
            _kernel_sink_expression_closed(item, operands, scalar_sequences)
            for item in (expression.test, expression.body, expression.orelse)
        )
    if not isinstance(expression, ast.Call):
        return False
    helper_chain = _kernel_attribute_chain(expression.func)
    if (
        helper_chain is not None
        and len(helper_chain) == 3
        and (f"scipy.stats.{helper_chain[1]}.{helper_chain[2]}" in _DISTRIBUTION_HELPER_METHODS)
    ):
        return all(
            _kernel_sink_expression_closed(item, operands, scalar_sequences)
            for item in expression.args
        ) and all(
            _kernel_sink_expression_closed(item.value, operands, scalar_sequences)
            for item in expression.keywords
        )
    name_calls = {
        "len",
        "min",
        "max",
        "sum",
        "sorted",
        "round",
        "abs",
        "list",
        "str",
        "fmean",
        "mean",
        "stdev",
        "median",
        "variance",
    }
    module_calls = {
        "statistics.mean",
        "statistics.fmean",
        "statistics.stdev",
        "statistics.median",
        "statistics.variance",
        "np.mean",
        "np.std",
        "np.var",
        "np.median",
        "math.sqrt",
        "math.isnan",
    }
    string_methods = {
        "format",
        "join",
        "lower",
        "upper",
        "strip",
        "lstrip",
        "rstrip",
        "replace",
        "split",
    }
    if isinstance(expression.func, ast.Name):
        if expression.func.id not in name_calls or expression.keywords:
            return False
        if (
            expression.func.id in {"list", "sorted"}
            and expression.args
            and isinstance(expression.args[0], ast.Name)
            and expression.args[0].id in operands
            and expression.args[0].id not in scalar_sequences
        ):
            return False
    elif isinstance(expression.func, ast.Attribute):
        if (
            isinstance(expression.func.value, ast.Name)
            and f"{expression.func.value.id}.{expression.func.attr}" in module_calls
        ):
            if expression.keywords:
                return False
        elif expression.func.attr not in string_methods:
            return False
        if not _kernel_sink_expression_closed(expression.func.value, operands, scalar_sequences):
            return False
    else:
        return False
    return all(
        _kernel_sink_expression_closed(item, operands, scalar_sequences) for item in expression.args
    ) and all(
        _kernel_sink_expression_closed(item.value, operands, scalar_sequences)
        for item in expression.keywords
    )


def _kernel_sink_partition_matches(
    tree: ast.Module, certificate: DependenceGrowthCertificate | CountDependenceCertificate
) -> bool:
    partition = _kernel_partition_body(tree, certificate)
    if partition is None:
        return False
    body, operands = partition
    imports = _kernel_imports(tree)
    if isinstance(certificate, CountDependenceCertificate):
        procedures = tuple(
            statement
            for statement in body
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Call)
            and _kernel_resolved_call(statement.value.func, imports)
            == certificate.resolved_callable
        )
        if len(procedures) != 1:
            return False
    else:
        census = _kernel_group_census(body, imports, certificate)
        if census is None:
            return False
        procedures, _helpers = census
    writes = [
        (statement, node)
        for statement in body
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write_text"
    ]
    if not procedures or len(writes) != 1:
        return False
    scalar_sequences = {
        argument.id
        for procedure in procedures
        for argument in cast(ast.Call, procedure.value).args
        if isinstance(argument, ast.Name)
    }
    sink_statement, sink = writes[0]
    if not isinstance(sink_statement, ast.Expr) or len(sink.args) != 1:
        return False
    definitions = {
        statement.targets[0].id: statement.value
        for statement in body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    }
    for statement in body:
        if (
            isinstance(statement, ast.If)
            and len(statement.body) == len(statement.orelse) == 1
            and isinstance(statement.body[0], ast.Assign)
            and isinstance(statement.orelse[0], ast.Assign)
            and len(statement.body[0].targets) == len(statement.orelse[0].targets) == 1
            and isinstance(statement.body[0].targets[0], ast.Name)
            and isinstance(statement.orelse[0].targets[0], ast.Name)
            and statement.body[0].targets[0].id == statement.orelse[0].targets[0].id
        ):
            definitions[statement.body[0].targets[0].id] = ast.IfExp(
                statement.test, statement.body[0].value, statement.orelse[0].value
            )
    operand_indices: set[int] = set()
    for index, statement in enumerate(body):
        stores = {
            node.id
            for node in ast.walk(statement)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
        }
        if (
            statement in procedures
            or isinstance(statement, ast.With | ast.For)
            or stores & operands
        ):
            operand_indices.add(index)
    sink_index = body.index(sink_statement)
    sink_indices = {sink_index}
    pending = [node.id for node in ast.walk(sink.args[0]) if isinstance(node, ast.Name)]
    sink_names: set[str] = set()
    while pending:
        name = pending.pop()
        if name in sink_names:
            continue
        sink_names.add(name)
        if name in definitions:
            pending.extend(
                node.id for node in ast.walk(definitions[name]) if isinstance(node, ast.Name)
            )
    sink_names -= operands
    for index, statement in enumerate(body):
        if index in operand_indices or index in sink_indices:
            continue
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and _kernel_closed_makedirs(statement.value, _kernel_constants(tree))
        ):
            sink_indices.add(index)
            continue
        if isinstance(statement, ast.If):
            branches = [*statement.body, *statement.orelse]
            if not (
                len(statement.body) == len(statement.orelse) == 1
                and all(
                    isinstance(branch, ast.Assign)
                    and len(branch.targets) == 1
                    and isinstance(branch.targets[0], ast.Name)
                    and branch.targets[0].id in sink_names
                    and _kernel_sink_expression_closed(branch.value, operands, scalar_sequences)
                    for branch in branches
                )
                and _kernel_sink_expression_closed(statement.test, operands, scalar_sequences)
            ):
                return False
            sink_indices.add(index)
            continue
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id in sink_names
            and not (isinstance(statement.value, ast.Name) and statement.value.id in operands)
            and _kernel_sink_expression_closed(statement.value, operands, scalar_sequences)
        ):
            return False
        sink_indices.add(index)
    if not _kernel_sink_expression_closed(sink.args[0], operands, scalar_sequences):
        return False
    return certificate.operand_slice_statement_tokens == tuple(
        _kernel_statement_token(body[index], index) for index in sorted(operand_indices)
    ) and certificate.sink_bound_statement_tokens == tuple(
        _kernel_statement_token(body[index], index) for index in sorted(sink_indices)
    )


def _kernel_resolved_call(expression: ast.expr, imports: dict[str, str]) -> str | None:
    if isinstance(expression, ast.Name):
        return imports.get(expression.id)
    if isinstance(expression, ast.Attribute) and isinstance(expression.value, ast.Name):
        prefix = imports.get(expression.value.id)
        return f"{prefix}.{expression.attr}" if prefix is not None else None
    return None


def _kernel_call_sites(
    tree: ast.Module, functions: dict[str, ast.FunctionDef]
) -> tuple[tuple[str, str, tuple[int, int, int, int]], ...]:
    """Independently enumerate the bounded acyclic call-path identities."""

    counter = 0
    result: list[tuple[str, str, tuple[int, int, int, int]]] = []

    def walk(statements: list[ast.stmt], parent: tuple[str, ...], depth: int) -> None:
        nonlocal counter
        if depth > MAX_V2_INLINE_DEPTH:
            return
        for statement in statements:
            calls: list[ast.Call] = []
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
                if isinstance(statement.value.func, ast.Name):
                    calls.append(statement.value)
                elif (
                    isinstance(statement.value.func, ast.Attribute)
                    and statement.value.func.attr == "write_text"
                    and statement.value.args
                ):
                    calls.extend(
                        node
                        for node in ast.walk(statement.value.args[0])
                        if isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id in functions
                    )
            elif (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.value, ast.Call)
            ):
                calls.append(statement.value)
            elif isinstance(statement, ast.Return) and statement.value is not None:
                calls.extend(
                    node
                    for node in ast.walk(statement.value)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in functions
                )
            for call in calls:
                if not isinstance(call.func, ast.Name) or call.func.id not in functions:
                    continue
                counter += 1
                component = f"{call.func.id}:{counter}"
                path = (*parent, component)
                result.append(
                    (
                        call.func.id,
                        "inline-call-path:" + "/".join(path),
                        (
                            getattr(call, "lineno", 0),
                            getattr(call, "col_offset", 0),
                            getattr(call, "end_lineno", 0),
                            getattr(call, "end_col_offset", 0),
                        ),
                    )
                )
                walk(functions[call.func.id].body, path, depth + 1)

    executable: list[ast.stmt] = []
    for item in tree.body:
        if isinstance(item, ast.FunctionDef | ast.Import | ast.ImportFrom):
            continue
        if isinstance(item, ast.If) and _kernel_main_guard(item):
            executable.extend(item.body)
        else:
            executable.append(item)
    walk(executable, (), 0)
    return tuple(result)


def _kernel_function_shape_closed(
    function: ast.FunctionDef,
    import_names: set[str],
    typing_names: set[str],
    constants: set[str],
    function_names: set[str],
) -> bool:
    args = function.args
    if (
        args.posonlyargs
        or args.kwonlyargs
        or args.defaults
        or args.kw_defaults
        or args.vararg is not None
        or args.kwarg is not None
    ):
        return False
    if any(
        isinstance(node, ast.Global | ast.Nonlocal | ast.Lambda)
        or (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            and node is not function
        )
        for node in ast.walk(function)
    ):
        return False
    parameters = {item.arg for item in args.args}
    stored = {
        node.id
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    if parameters & stored or (parameters | stored) & import_names:
        return False
    annotation_nodes = _kernel_annotation_nodes(function)
    loads = {
        node.id
        for node in ast.walk(function)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node not in annotation_nodes
    }
    if loads & typing_names:
        return False
    allowed = (
        parameters
        | stored
        | constants
        | import_names
        | function_names
        | {
            "list",
            "set",
            "float",
            "int",
            "sorted",
            "str",
            "len",
            "min",
            "max",
            "sum",
            "round",
            "abs",
            "range",
            "enumerate",
        }
    )
    if loads - allowed:
        return False
    returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
    return len(returns) <= 1 and (not returns or _kernel_final_return(function.body, returns[0]))


def _kernel_final_return(body: list[ast.stmt], target: ast.Return) -> bool:
    return bool(
        (body and body[-1] is target)
        or (
            body
            and isinstance(body[-1], ast.With)
            and body[-1].body
            and body[-1].body[-1] is target
        )
    )


def _kernel_graph_cyclic(graph: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(name: str) -> bool:
        if name in visiting:
            return True
        if name in done:
            return False
        visiting.add(name)
        if any(visit(child) for child in graph[name]):
            return True
        visiting.remove(name)
        done.add(name)
        return False

    return any(visit(name) for name in graph)


def _kernel_graph_depth(name: str, graph: dict[str, set[str]]) -> int:
    return 1 + max((_kernel_graph_depth(child, graph) for child in graph[name]), default=0)
