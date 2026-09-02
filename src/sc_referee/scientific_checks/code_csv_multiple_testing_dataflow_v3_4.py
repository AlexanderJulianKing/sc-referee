"""Multiple-testing 3.4 ordered integration over the byte-frozen 3.3 pipeline.

The ordering rule in design section 3.3 is the load-bearing safety property of this delta, and
it was chosen against executed evidence rather than on principle:

1. run every unchanged adapter precondition and global census on original bytes;
2. run the **complete unchanged 3.3 pipeline** and record its result;
3. if that result is a classification, return it untouched.  No 3.4 admission is attempted;
4. otherwise re-analyze with the section-4 comprehension normalization supplied as a graph fact
   and the section-6 and section-7 admissions inside the 3.4 correction recognizer;
5. adopt the re-analysis only if it is itself a classification.  If it abstains, return the
   step-2 abstention reason byte-for-byte.

An earlier revision normalized unconditionally and lost two pinned 3.3 candidates: on E16 P3 the
normalization resolved the p-lineage, the first reason stopped being `unresolved-pvalue-consumer`
and the frozen helper-record route was never attempted.  Under steps 3 and 5 every frozen 3.3
classification and every frozen 3.3 abstention reason survives by construction, so the only rows
3.4 can move are abstentions it converts into classifications.

Section 8's outcome-headers reason routing is measured in the design and **not applied** here:
3.4 emits the frozen reason unchanged.  Extension B, the terminal `IfExp` print-only production,
is specified in the design and is **not** part of this recognizer set.

The round-3 audit fix adds the one narrowing that steps 3 and 5 cannot express as an admission.
A false accusation was demonstrated on the *classification* side: a correct, complete Bonferroni
pass written through a second name for the record collection is classified `candidate`/`none`
over the uncorrected family, because the frozen engine reconstructs family membership from the
stores written through the collection's own name and never sees the aliased one.  Before a
classification is returned -- the frozen one at step 3 or the re-analysed one at step 5 -- the
round-1/round-2 alias closure must find no store, mutation, or display escape on any other name
for that collection.  When it finds one, the row lands on `pvalue-family-collection-unresolved`,
which is the frozen reason the identical through-name program already carries; no reason is
added.  Abstentions are untouched, so no frozen abstention reason can move.

The round-4 audit fix widens *which names* that closure covers and changes nothing else about
this module.  A second name for the collection is not the only binding a correction store can
travel through: `for name, record in results.items(): record["p"] = ...` stores through the
iterated record, which is not an alias edge, so a complete correct Bonferroni pass was still
published as an accusation.  The predicate now enumerates every record-derived binding -- the
mapping views and their wrappers, the subscript and lookup forms, the walrus, comprehension, and
`async for` spellings, and every chain of them -- and refuses on the same reason.  The ordering
rule, the admissions, the reason set, and the abstention paths are untouched.

The round-5 audit fix follows the store into the next scope, which is the one route round 4 named
and left open.  A correct, complete Bonferroni pass whose per-record correction is written inside
a project-local helper -- `def bonferroni_adjust(entry, n_tests): entry["p"] = min(entry["p"] *
n_tests, 1.0)`, called as `bonferroni_adjust(record, len(OUTCOMES))` -- was still published as an
accusation, because argument passing is a non-capture under the frozen discipline and nothing
binds `entry` to the record.  A call whose callee resolves to a definition in this module now
makes the call site a mutation of every argument whose bound parameter is stored through in the
callee body, checked against the same name sets and landing on the same reason.  Builtins,
library calls, and helpers imported from other modules resolve to nothing and stay non-captures,
which is the frozen `len(OUTCOMES)` discipline every earlier round preserves.  The ordering rule,
the admissions, the reason set, and the abstention paths are again untouched.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from typing import Any

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_comprehension_v3_4 import (
    normalize_comprehensions,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    MultipleTestingDataflowFacts,
    MultipleTestingDataflowResult,
    MultipleTestingEvidenceSpan,
    SourceEnvelope,
    _analyze_v3_core,
    _mt30_model_facts,
    select_code_source_envelope,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    analyze_code_csv_multiple_testing_dataflow as _frozen_v33_analyze,
)

CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)
FROZEN_V33_DATAFLOW_DELEGATE = (
    "sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3:"
    "analyze_code_csv_multiple_testing_dataflow"
)

#: Reasons whose 3.3 graph proof is re-attempted inside the 3.4 re-analysis.
_TERMINAL_PRESENTATION_REASON = "hierarchical-gatekeeping-present"
_HELPER_RECORD_REASON = "unresolved-pvalue-consumer"

#: The frozen reason the identical program carries when the same store is written through the
#: collection name itself.  It is in the closed 3.3 reason set; round 3 adds no reason.
_COLLECTION_ALIAS_REASON = "pvalue-family-collection-unresolved"


def _record_collection_alias_unresolved(content: bytes) -> bool:
    """Round 3: refuse to classify a family whose record collection is stored through an alias.

    The frozen 3.3 engine reconstructs the p-value family from the stores written through the
    record collection's own name.  A store written through a second name for the same object is
    invisible to that reconstruction, so a complete Bonferroni pass spelled

    ```python
    adjusted = results
    for name in adjusted:
        adjusted[name]["p"] = min(adjusted[name]["p"] * len(OUTCOMES), 1.0)
    ```

    is classified `candidate`/`none` over the full family, while the identical program written
    through `results` refuses at `pvalue-family-collection-unresolved` because the member the
    store names cannot be resolved.  The alias hides the correction rather than resolving the
    family, so the aliased spelling lands on the through-name spelling's own frozen reason.

    Round 4 widens the closure from *names for the collection* to every binding that reaches a
    record inside it.  `for name, record in results.items(): record["p"] = ...` is the same
    defect through a loop target rather than through an alias edge, and the enumeration in
    `record_derived_names` covers the mapping views, their wrappers, the subscript and lookup
    forms, the walrus, comprehension, and `async for` spellings, and every chain of them.

    Round 5 follows the store into the next scope.  `bonferroni_adjust(record, len(OUTCOMES))`
    into a project-local helper that writes `entry["p"] = ...` corrects every declared outcome
    and was invisible to round 4 for the same reason `record["p"] = ...` was invisible to round
    3: argument passing is a non-capture, so nothing bound the parameter to the record.  A call
    whose callee resolves to a definition in this module is now a mutation of the arguments whose
    parameters it stores through; builtins, library calls, and helpers from other modules resolve
    to nothing and stay non-captures.

    This is a narrowing of an inherited defect.  The byte-frozen v3 and v3.3 lanes carry it and
    stay byte-identical; the active 3.4 binding supersedes them, and only 3.4 is narrowed.  The
    closure is applied to *classifications only*, so no abstention reason anywhere can move.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        record_collection_alias_unresolved,
    )

    try:
        tree = ast.parse(content)
    except (SyntaxError, ValueError, RecursionError):
        return False
    return record_collection_alias_unresolved(tree)


def _apply_v34_ap(
    content: bytes,
    *,
    baseline: MultipleTestingDataflowResult,
    authorized_path: str,
    group_column: str,
    outcome_columns: tuple[str, ...],
    csv_header: Any,
    group_values: tuple[str, str],
    csv_content: bytes,
) -> MultipleTestingDataflowResult:
    """Apply the 3.4 AP proof, whose only delta is the section-6 and section-7 admissions."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        analyze_correction_model,
    )

    arguments: dict[str, Any] = {
        "authorized_path": authorized_path,
        "group_column": group_column,
        "csv_header": csv_header,
        "group_values": group_values,
        "csv_content": csv_content,
    }
    model = analyze_correction_model(
        content,
        baseline=baseline,
        outcome_columns=outcome_columns,
        **arguments,
    )
    if not model.changed:
        return baseline
    facts_result = _mt30_model_facts(
        content,
        outcome_columns=outcome_columns,
        outcome=model.outcome,
        detail=model.detail,
    )
    if facts_result.reason is not None or facts_result.facts is None:
        return baseline
    position = model.detail.get("source_position")
    if (
        not isinstance(position, list)
        or len(position) != 4
        or not all(isinstance(item, int) for item in position)
    ):
        return baseline
    start_line, start_column, end_line, end_column = position
    if min(start_line, end_line) < 1 or min(start_column, end_column) < 0:
        return baseline
    correction_span = MultipleTestingEvidenceSpan(
        "correction",
        None,
        start_line,
        end_line,
        start_column + 1,
        end_column + 1,
    )
    return MultipleTestingDataflowResult(
        replace(
            facts_result.facts,
            evidence_spans=(*facts_result.facts.evidence_spans, correction_span),
        ),
        None,
    )


def _reanalyze_with_v34_admissions(
    content: bytes,
    *,
    authorized_path: str,
    group_column: str,
    outcome_columns: tuple[str, ...],
    csv_header: Any,
    group_values: tuple[str, str],
    csv_content: bytes,
) -> MultipleTestingDataflowResult:
    """Step 4: the 3.3 pipeline shape with the three shipped 3.4 admissions installed.

    The comprehension normalization enters as an `ast.Module` graph fact, exactly as the frozen
    3.3 helper-record graph does.  Global censuses continue to run on the original bytes inside
    the copied core, so a normalized family can never hide a census fact.
    """

    arguments: dict[str, Any] = {
        "authorized_path": authorized_path,
        "group_column": group_column,
        "outcome_columns": outcome_columns,
        "csv_header": csv_header,
        "group_values": group_values,
        "csv_content": csv_content,
    }
    normalization = normalize_comprehensions(content, outcome_columns)
    analysis_tree: ast.Module | None = None if normalization is None else normalization.tree
    terminal_exclusions: frozenset[tuple[tuple[int, int, int, int], str, str]] = frozenset()

    external = _apply_v34_ap(
        content,
        baseline=_analyze_v3_core(content, analysis_tree=analysis_tree, **arguments),
        **arguments,
    )
    if external.reason is None:
        return external

    from sc_referee.scientific_checks.code_csv_multiple_testing_helper_record_v3_4 import (
        build_helper_record_graph,
    )
    from sc_referee.scientific_checks.code_csv_multiple_testing_terminal_presentation_v3_3 import (
        prove_terminal_presentation,
    )

    if external.reason == _TERMINAL_PRESENTATION_REASON:
        proof = prove_terminal_presentation(content)
        if proof is None:
            return external
        terminal_exclusions = proof.occurrences
    elif external.reason == _HELPER_RECORD_REASON and analysis_tree is None:
        graph = build_helper_record_graph(content, outcome_columns)
        if graph is None:
            return external
        repeated = build_helper_record_graph(content, outcome_columns)
        if repeated is None or ast.dump(repeated.tree, include_attributes=True) != ast.dump(
            graph.tree, include_attributes=True
        ):
            return MultipleTestingDataflowResult(None, "multiple-testing-code-inspection-exception")
        analysis_tree = graph.tree
    else:
        return external

    downstream = _analyze_v3_core(
        content,
        analysis_tree=analysis_tree,
        terminal_exclusions=terminal_exclusions,
        **arguments,
    )
    return _apply_v34_ap(content, baseline=downstream, **arguments)


def analyze_code_csv_multiple_testing_dataflow(
    content: bytes,
    *,
    authorized_path: str,
    group_column: str,
    outcome_columns: tuple[str, ...],
    csv_header: Any,
    group_values: tuple[str, str],
    csv_content: bytes,
) -> MultipleTestingDataflowResult:
    """Run the complete unchanged 3.3 pipeline first, then the 3.4 admissions only if it abstained."""

    arguments: dict[str, Any] = {
        "authorized_path": authorized_path,
        "group_column": group_column,
        "outcome_columns": outcome_columns,
        "csv_header": csv_header,
        "group_values": group_values,
        "csv_content": csv_content,
    }
    frozen = _frozen_v33_analyze(content, **arguments)
    if frozen.reason is None:
        # Round 3: a classification whose record collection is stored through an alias lands on
        # the frozen reason the through-name spelling of the same program lands on.
        if _record_collection_alias_unresolved(content):
            return MultipleTestingDataflowResult(None, _COLLECTION_ALIAS_REASON)
        # Step 3: a frozen 3.3 classification is returned untouched and no admission is tried.
        return frozen
    attempted = _reanalyze_with_v34_admissions(content, **arguments)
    if attempted.reason is None and not _record_collection_alias_unresolved(content):
        # Step 5: the re-analysis is adopted only when it is itself a classification.
        return attempted
    # Steps 5 and 6: an abstaining re-analysis returns the frozen 3.3 reason byte-for-byte.  A
    # re-analysis refused by the round-3 closure is an abstaining re-analysis for that purpose.
    return frozen


__all__ = [
    "CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST",
    "FROZEN_V33_DATAFLOW_DELEGATE",
    "MultipleTestingDataflowFacts",
    "MultipleTestingDataflowResult",
    "MultipleTestingEvidenceSpan",
    "SourceEnvelope",
    "analyze_code_csv_multiple_testing_dataflow",
    "select_code_source_envelope",
]
