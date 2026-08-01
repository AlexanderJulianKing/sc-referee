# ADR-0036: Add a bounded non-executing container-cell language bridge

- **Status:** Accepted under the repository owner's standing authorization for non-authority-
  changing development ADRs
- **Date:** 2026-07-30
- **Related decisions:** Accepted ADR-0017, ADR-0033, ADR-0034, and ADR-0035
- **Schema impact:** None; accepted schema v0.15.0 remains unchanged

## Context

ADR-0034 and ADR-0035 preserve notebook and Quarto cell boundaries, but their cells stop at
structural inventory. Consequently, Python and R code already supported as ordinary source files
becomes opaque merely because it is stored in a notebook or Quarto container. Closing that adapter
gap does not require a kernel, rendering, project execution, a new scientific rule, or a new public
schema.

The bridge must not imply that independently parsed cells ran in order or shared one runtime. It
also must not silently choose a language from a conflicting notebook envelope or interpret an
unsupported Quarto engine.

## Decision

### 1. Admit only exact Python and R cell declarations

For an nbformat-4 notebook, the bridge accepts code cells only when the nonempty
`metadata.language_info.name` and `metadata.kernelspec.language` declarations, when present,
normalize to one identical exact value: `python` or `r`. Absent, conflicting, and other language
declarations remain explicit opaque boundaries.

For Quarto, each already-inventoried literal cell engine is treated independently. Exact
case-insensitive `python` and `r` engines are admitted. Other engines remain opaque. At most 200
recognized code cells in one container are bridged; exceeding the ceiling skips the bridge for the
container instead of selecting an arbitrary prefix.

### 2. Reuse existing static parsers over controller-extracted bytes

The controller re-extracts each inventoried cell from the immutable snapshot and verifies its
digest before parsing. Python cells use the existing CPython AST/token parser over in-memory bytes.
R cells use Tree-sitter-R and the existing optional isolated base-R parse-data helper. The helper
parses an auditor-written isolated copy and never sources or evaluates the text.

Each child ParserResult receives a stable identity containing the container digest, exact cell
identity, and cell-source digest. All child syntax and Operation source references are rebound to
the public `notebook_cell` or `document_chunk` location. Quarto line spans are translated back to
absolute document lines; notebook spans remain cell-relative.

### 3. Preserve cache and replay boundaries

The parent container result remains the authenticated parser-cache unit. Its component version and
dependency inventory bind the bridge behavior. Child Python static-graph descendants use the exact
cell locator, rather than only the shared container path, as their cache scope. Semantic lock and
replay store the resulting child ParserResults and promoted Operations canonically.

The bounded numerical verifier and scientific-check adapters continue to ignore virtual cell
sources until they have cell-aware evidence contracts. They must not read the notebook JSON or the
whole Quarto document as if it were Python source.

### 4. Do not add scientific or execution authority

The bridge establishes only static syntax, calls, and already-supported Python Operations for each
cell in isolation. It does not establish cross-cell bindings, execution order, hidden state,
environment identity, saved-output authenticity, code-to-output provenance, rendered meaning,
Claims, scientific operands, detector eligibility, or Findings. Repository cell text remains
evidence and is never treated as instructions.

A separate detector-free capability profile records this exact bridge. Tested and inferred version
lists remain empty, semantic modeling remains `not_started`, and domain-wide support remains
prohibited.

## Alternatives rejected

### Start a notebook kernel or render Quarto

Rejected because either can execute project-authored code and depends on unverified runtime state.

### Infer language from code, kernel names, or filename conventions

Rejected because heuristic language selection can turn ambiguity into a false premise.

### Treat cells as one concatenated program

Rejected because concatenation invents ordering, shared bindings, and runtime semantics that the
container bytes do not establish.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** exact Python notebook cell parsing; collision-free identities for identical
  cells; conflicting notebook declarations; Python/R/unsupported Quarto engines; absolute Quarto
  source spans; inert execution markers; finite bridge ceiling; schema validation; parent cache
  hit/invalidation; static descendant cache isolation; semantic lock; and replay.
- **Acceptance criterion satisfied:** supported static Python and R syntax inside bounded notebook
  and Quarto cells enters canonical parser/Operation evidence with exact container locations and no
  project execution.
- **Remaining limitation:** cells are independent static fragments. Cross-cell dataflow, notebook
  magics, runtime state, output provenance, rendering, Claims, scientific-check adapters, and all
  new detector or Finding authority remain unsupported.
