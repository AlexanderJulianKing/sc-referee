"""Multiple-testing 3.5 ordered integration over the shipped 3.4 lane.

The ordering rule is inherited unchanged from 3.4, and it is the load-bearing safety property
of this delta as well:

1. run the **complete unchanged 3.4 lane** and record its result;
2. if that result is a classification, return it untouched.  No 3.5 production is attempted;
3. otherwise re-analyze with the 3.4 comprehension normalization and correction recognizer
   over the versioned 3.5 engine, whose four widened predicates are the whole of this delta;
4. adopt the re-analysis only if it is itself a classification.  If it abstains, return the
   step-1 abstention reason byte-for-byte.

Under steps 2 and 4 every frozen 3.4 classification and every frozen 3.4 abstention reason
survives by construction, so the only rows 3.5 can move are abstentions it converts into
classifications.  The 3.4 lane becomes the frozen previous lane under 3.5 exactly as the 3.3
lane became the frozen previous lane under 3.4.

Two closures narrow step 2, both applied before a frozen classification is returned and both
one-directional.  The round-3 to round-7 alias closure refuses a classification outright.  The
MT 3.5 fix round-1 consumption proof (`_consumption_narrowed`) refuses a *clearance* that rests
on a library correction whose returned arrays never reach a decision; that route is inherited
from the frozen lanes, so a proof living only in the 3.5 engine could never reach the rows it
is for.  Neither closure can add a corrected position, change a family size, or turn an
abstention into a classification.

The round-3 to round-7 alias closure runs before any classification is returned -- the frozen
one at step 2 and the re-analysed one at step 4 -- exactly as it does in 3.4.  It is not
weakened, bypassed, or reordered here: this module calls the same 3.4 predicate over the same
original bytes and lands on the same frozen `pvalue-family-collection-unresolved` reason.

No abstention reason is added.  The closed set stays at 61.  Delta 2 (set literals in the AP
selector) and delta 3 (standard-library `csv` reader lineage) are specified in the design and
are **not** installed: an executed, deliberately over-generous reader stand-in shows a third
wall (`helper-free-name-unbound`) sitting in front of both, so under the ordering rule neither
could change a public byte.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from typing import Any

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_admission_census_v3_5 import (
    suspended_admissions,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_comprehension_v3_4 import (
    normalize_comprehensions,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_core_v3_5 import (
    MultipleTestingDataflowFacts,
    MultipleTestingDataflowResult,
    MultipleTestingEvidenceSpan,
    SourceEnvelope,
    _analyze_v3_core,
    _mt30_model_facts,
    select_code_source_envelope,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
    analyze_code_csv_multiple_testing_dataflow as _frozen_v34_analyze,
)

CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V3_5_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)
FROZEN_V34_DATAFLOW_DELEGATE = (
    "sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4:"
    "analyze_code_csv_multiple_testing_dataflow"
)

#: Reasons whose 3.3 graph proof is re-attempted inside the 3.5 re-analysis.  Unchanged.
_TERMINAL_PRESENTATION_REASON = "hierarchical-gatekeeping-present"
_HELPER_RECORD_REASON = "unresolved-pvalue-consumer"

#: The frozen reason the identical program carries when the same store is written through the
#: collection name itself.  It is in the closed 3.3 reason set; 3.5 adds no reason.
_COLLECTION_ALIAS_REASON = "pvalue-family-collection-unresolved"

#: The frozen reason the 3.2 AP path already emits at its own conclusion-consumption gate.
#: The fix round-1 library-correction consumption proof lands on the same one, so the closed
#: set stays at 61.
_CONSUMPTION_REASON = "unresolved-manual-correction-present"


def _record_collection_alias_unresolved(content: bytes) -> bool:
    """Rounds 3 to 7: refuse to classify a family whose record collection escapes its name.

    This is the shipped 3.4 closure, called unchanged over the original bytes.  It refuses a
    classification whenever a store, mutation, or display escape reaches the p-record
    collection through any binding other than the collection's own name -- an alias, a
    record-derived binding, or a project-local helper parameter -- and lands on the frozen
    reason the through-name spelling of the same program already carries.  3.5 neither widens
    nor narrows it, and applies it at both points a classification can be returned.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        record_collection_alias_unresolved,
    )

    try:
        tree = ast.parse(content)
    except (SyntaxError, ValueError, RecursionError):
        return False
    return record_collection_alias_unresolved(tree)


def _apply_v35_ap(
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
    """Apply the shipped 3.4 AP proof, which 3.5 does not change.

    Delta 2 would have widened this proof's per-row truth evaluation; it is specified and not
    installed, so the recognizer here is the 3.4 one, byte for byte.
    """

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


def _reanalyze_with_v35_productions(
    content: bytes,
    *,
    authorized_path: str,
    group_column: str,
    outcome_columns: tuple[str, ...],
    csv_header: Any,
    group_values: tuple[str, str],
    csv_content: bytes,
) -> MultipleTestingDataflowResult:
    """Step 3: the 3.4 re-analysis shape run over the versioned 3.5 engine.

    The comprehension normalization enters as an `ast.Module` graph fact, exactly as the
    frozen 3.3 helper-record graph does.  Global censuses continue to run on the original
    bytes inside the copied core, and both 3.5 delta tables are built from the original bytes
    there, so a normalized family can never hide a census fact or move an admission.
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

    external = _apply_v35_ap(
        content,
        baseline=_analyze_v3_core(content, analysis_tree=analysis_tree, **arguments),
        **arguments,
    )
    if external.reason is None:
        return external

    from sc_referee.scientific_checks.code_csv_multiple_testing_helper_record_v3_5 import (
        build_helper_record_graph,
    )
    from sc_referee.scientific_checks.code_csv_multiple_testing_terminal_presentation_v3_5 import (
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
    return _apply_v35_ap(content, baseline=downstream, **arguments)


def _consumption_narrowed(
    content: bytes,
    frozen: MultipleTestingDataflowResult,
    *,
    authorized_path: str,
    group_column: str,
    outcome_columns: tuple[str, ...],
    csv_header: Any,
    group_values: tuple[str, str],
    csv_content: bytes,
) -> MultipleTestingDataflowResult | None:
    """MT 3.5 fix round 1: narrow a frozen 3.4 clearance whose correction is never consumed.

    The false-clearance route the 3.5 audit demonstrated is inherited: `multipletests` over the
    whole authorized family whose `reject` and adjusted arrays are never read, beside verdicts
    printed from raw p-values, is cleared `covered`/`complete` by the shipped 3.4 lane as well,
    and therefore by every lane before it.  The custodian measured it on 3.4 directly.  Step 2
    of the ordering rule returns a frozen 3.4 classification untouched, so the 3.5 core's own
    consumption proof cannot reach those rows unless it is applied here, exactly as the
    round-3 to round-7 alias closure is applied at both classification returns.

    The narrowing is one-directional and checked to be so.  It can only remove corrected
    positions from the frozen row or replace the row with the frozen consumption reason; it
    can never add a corrected position, change the family size, or turn an abstention into a
    classification.  `None` means the frozen row stands.
    """

    if frozen.facts is None or not frozen.facts.corrected_positions:
        return None
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

    def probe() -> MultipleTestingDataflowResult:
        return _apply_v35_ap(
            content,
            baseline=_analyze_v3_core(content, analysis_tree=analysis_tree, **arguments),
            **arguments,
        )

    # The probe posts no admissions: the row it is asked about is one the ordering rule is
    # about to answer from the frozen lane, and a probe that changes nothing may not leave a
    # 3.5 admission behind it.  When it does change the row, it is re-run with the census open
    # below, so a published row always records its own analysis.
    with suspended_admissions():
        core = probe()
    if core.reason == _CONSUMPTION_REASON:
        # The core reached the consumption gate and refused: some position of the recognised
        # library correction is neither proved to consume its own corrected value nor proved
        # to conclude from its own raw p-value.  A clearance may not stand on that.
        return MultipleTestingDataflowResult(None, _CONSUMPTION_REASON)
    if core.reason is not None:
        # The 3.5 core cannot reach a classification at all for some other reason, so it has
        # nothing to say about this row's corrected positions and the frozen row stands.
        return None
    if core.facts is None or core.facts.family_size != frozen.facts.family_size:
        return None
    before = set(frozen.facts.corrected_positions)
    after = set(core.facts.corrected_positions)
    if not after < before:
        return None
    return probe()


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
    """Run the complete unchanged 3.4 lane first, then the 3.5 productions only if it abstained."""

    arguments: dict[str, Any] = {
        "authorized_path": authorized_path,
        "group_column": group_column,
        "outcome_columns": outcome_columns,
        "csv_header": csv_header,
        "group_values": group_values,
        "csv_content": csv_content,
    }
    frozen = _frozen_v34_analyze(content, **arguments)
    if frozen.reason is None:
        # The round-3 to round-7 closure runs before a classification is returned.  The 3.4
        # lane already applied it to reach this classification; applying it again here is
        # idempotent and keeps the closure ahead of every return in this module.
        if _record_collection_alias_unresolved(content):
            return MultipleTestingDataflowResult(None, _COLLECTION_ALIAS_REASON)
        narrowed = _consumption_narrowed(content, frozen, **arguments)
        if narrowed is not None:
            return narrowed
        # Step 2: a frozen 3.4 classification is returned untouched and no production is tried.
        return frozen
    attempted = _reanalyze_with_v35_productions(content, **arguments)
    if attempted.reason is None and not _record_collection_alias_unresolved(content):
        # Step 4: the re-analysis is adopted only when it is itself a classification.
        return attempted
    # Step 4 otherwise: an abstaining re-analysis returns the frozen 3.4 reason byte-for-byte.
    # A re-analysis refused by the alias closure is an abstaining re-analysis for that purpose.
    return frozen


__all__ = [
    "CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V3_5_IMPLEMENTATION_DIGEST",
    "FROZEN_V34_DATAFLOW_DELEGATE",
    "MultipleTestingDataflowFacts",
    "MultipleTestingDataflowResult",
    "MultipleTestingEvidenceSpan",
    "SourceEnvelope",
    "analyze_code_csv_multiple_testing_dataflow",
    "select_code_source_envelope",
]
