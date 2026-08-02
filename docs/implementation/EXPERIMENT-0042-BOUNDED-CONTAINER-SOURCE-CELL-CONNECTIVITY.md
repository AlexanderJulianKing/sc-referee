# Experiment 0042: Bounded container-source cell connectivity

## Question

Can an exact, independently parsed Jupyter, Quarto, or R Markdown cell contribute to an existing
question-only scientific adapter when its parent file is selected as an analysis source, without
inventing cross-cell state, execution order, or output provenance?

## Scope

This experiment implements L08 under ADR-0051. It extends the common static scope graph and the
existing non-executing cell-language bridge. It adds no public schema, detector, Finding authority,
model privilege, or project-execution privilege.

The R Markdown inventory now assigns collision-free identities, exact code digests, absolute
spans, and literal evaluation declarations to bounded fenced R chunks. The shared bridge
re-extracts exact active-or-unspecified chunk bytes and delegates them to the existing dual R
parsers. Jupyter, Quarto, and R Markdown virtual sources use one child ParserResult-to-parent
FileRecord proof before the existing scientist-selected analysis-source edge.

Cells remain independent documents. The implementation does not concatenate them, use saved
execution counts as evidence of execution, authenticate saved output, or infer that a cell governed
the reported analysis. Explicitly disabled cells and virtual cells without the exact containment
proof cannot inherit whole-file analysis-source scope.

## Acceptance criteria

1. A complete supported Python or R method shape in one exact selected-source cell can produce the
   existing normalized, question-only observation and an exact container citation.
2. Jupyter, Quarto, and R Markdown parents use the same two-edge selected-source proof.
3. Disabled and unselected cells have no path to the selected publication surface.
4. Method fragments split across cells remain unsupported regardless of cell order or saved
   execution counts.
5. Duplicate cell or chunk text retains distinct identities and cache scopes.
6. Conflicting language declarations, parser disagreement, unsupported engines, malformed or
   over-budget containers, and bridge drift fail locally.
7. No project-authored code executes, and semantic-lock replay preserves parser results and public
   assessments.
8. Existing R Markdown MVMR behavior remains unchanged under the v0.2 inventory identity, with
   disabled chunks still excluded.

## Tests added or strengthened

- `tests/test_static_scope_joins.py` covers the exact selected-source path for Jupyter, Quarto, and
  R Markdown, plus disabled and unselected cells.
- `tests/test_static_source_method_adapters.py` proves a selected R Markdown cell contributes the
  existing LD-whitening operand with an exact citation, and proves that cross-cell hidden state,
  reversed cell order, and conflicting saved execution counts do not create an operand.
- `tests/test_rmarkdown_parser.py` covers bounded chunk identity, duplicate labels, literal
  evaluation state, dual-R bridging, no execution, semantic lock, and replay.
- `tests/test_cell_language_bridge.py` keeps duplicate-cell cache isolation, conflicting notebook
  language declarations, finite ceilings, no execution, and replay while pinning the v0.2 bridge
  receipt.
- `tests/test_capability_matrix.py` keeps structural R Markdown inventory separate from delegated
  operation extraction and publishes the exact v0.2 bridge limits.
- Existing Jupyter, Quarto, static-source, R Markdown MVMR, regression-ledger, and module-baseline
  suites remain mandatory regression controls.

## Result

The bounded connectivity path is implemented. A selected active-or-unspecified cell can feed an
existing static scientific adapter only through the exact child-to-parent and selected-source
edges. Disabled, unselected, cross-cell-dependent, conflicting-language, and unsupported paths
abstain. The R Markdown v0.2 inventory and bridge preserve the existing MVMR question lifecycle.
Schema v0.18.0 and all Finding ceilings are unchanged. The checkpoint passes 1,357 tests, Ruff,
format checking, strict typing for 108 production and 28 evaluation files, 79 public schema
examples, the 113-case regression ledger with all 26 module baselines, deterministic replay, and
the complete clean-wheel handoff verifier.

## Remaining limitations

- No cross-cell binding, notebook kernel state, execution chronology, rendered document behavior,
  saved-output authenticity, or code-to-output provenance is established.
- An `unspecified` evaluation declaration means only that the source was not explicitly disabled;
  it is not evidence that the cell ran.
- Only exact Python and R cells within the bounded container subsets are delegated. Other engines,
  magics, dynamic chunks, general R Markdown/Quarto semantics, and over-budget containers remain
  unsupported.
- Connectivity can support an observation or bounded scientist question, not a Finding, correctness
  certificate, or claim that the selected cell governed the published result.
