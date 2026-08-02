# ADR-0051: Connect exact active container cells to selected analysis sources

- **Status:** Accepted under the repository owner's standing authorization for non-material
  backlog decisions
- **Date:** 2026-08-02
- **Related decisions:** ADR-0034 through ADR-0038, ADR-0047, ADR-0048, and ADR-0050
- **Related backlog item:** L08
- **Coordinated public schema release:** None; retain schema 0.18.0
- **Finding impact:** None; connected observations remain question-only

## Context

The controller already inventories Jupyter and Quarto cells, re-extracts exact Python or R bytes,
and lets an independently self-contained cell participate when its whole container is the selected
publication surface. That does not cover the ordinary repository layout in which a Markdown report
is selected for review and a notebook, Quarto document, or R Markdown document is separately
selected as an analysis source. The generic source-selection edge currently addresses only the
container FileRecord, so applying it directly to every virtual cell would also admit disabled or
otherwise unsupported cells without a cell-specific proof.

R Markdown has a bounded chunk inventory, but its R chunks do not yet enter the shared static R
parser and scientific-adapter boundary. Treating the whole document as R would confuse prose,
chunk options, and code.

## Decision

### 1. Add one exact selected-source cell-containment path

The general static scope graph may connect a verified virtual-cell ParserResult to its exact parent
FileRecord when all of the following hold:

- the parent is a full-digest snapshotted regular file;
- the child was independently re-extracted from that exact parent by the accepted cell-language
  bridge;
- the child language is exactly Python or R and its controller parser receipt is complete;
- the cell is not explicitly disabled; and
- the parent FileRecord has one accepted analysis-source selection edge to the selected
  publication surface.

The resulting two-edge path establishes only that the exact active-or-unspecified cell is contained
in a scientist-selected analysis source. It does not establish execution, cell order, primary
analysis status, data lineage, output production, or scientific correctness.

Virtual cells may no longer inherit a whole-file analysis-source edge directly. Without the exact
cell-containment proof they remain unscoped suppressors.

### 2. Bridge bounded R Markdown R chunks

The R Markdown parser assigns every closed R chunk a collision-free identity, exact code digest,
absolute source span, and closed evaluation declaration. The existing cell-language bridge then
re-extracts those bytes and delegates them to the existing static R parsers without invoking R
Markdown, knitr, Pandoc, or project-authored code.

Literal `eval=FALSE` or `eval=F` chunks are parsed as inert evidence but cannot receive analysis
scope. Missing or ordinary evaluation options remain `unspecified`, not proof that a chunk ran.

### 3. Keep cross-cell state outside the positive path

One cell may contribute an observation only when the existing language adapter proves its complete
closed method shape inside that cell. Imports, assignments, objects, or method steps spread across
multiple cells are not concatenated and do not create a supported operand. Saved notebook
execution counts, document order, duplicate text, or matching outputs cannot close that gap.

Competing complete operands in distinct scoped cells remain ambiguous through the existing module
reducer. A method-like fragment that depends on another cell remains unsupported. Execution-count
mismatch, hidden state, cell reordering, prose/code disagreement, and saved output therefore cannot
be used to select a governing method.

### 4. Preserve authority and replay boundaries

The new graph profile, bridge version, parser versions, manifests, and exact evidence digests enter
the semantic lock and replay deterministically. No model constructs or repairs the path, and no
model call occurs after semantic lock. Repository text remains evidence and project code is never
executed.

This is an internal connectivity and advertised parser-coverage change. It does not alter public
record schemas, detector eligibility, Finding authority, or the meaning of scientist selection.

## Alternatives rejected

### Concatenate cells into one program

Rejected because it invents shared state and order and can turn a stale notebook history into a
false scientific premise.

### Use saved execution counts as execution proof

Rejected because counts are mutable repository-supplied metadata and do not authenticate a kernel,
environment, code version, or output.

### Treat an entire R Markdown file as R source

Rejected because prose, chunk headers, inline expressions, and rendering semantics are not R
program bytes.

## Test, acceptance criterion, and remaining limitation

- **Tests required:** separately selected Jupyter, Quarto, and R Markdown sources; exact active-cell
  citations; literal disabled cells; unselected containers; duplicate cell text; reordered cells;
  notebook execution-count mismatch; hidden cross-cell state; conflicting language declarations;
  prose/code disagreement; cache invalidation; bridge and manifest mutation; no execution; semantic
  lock; and replay.
- **Acceptance criterion:** a self-contained supported Python or R method shape in one exact active
  cell can feed the existing question-only adapter through the common scope graph when its parent
  source is selected, while disabled, unselected, cross-cell-dependent, or ambiguous shapes fail
  closed.
- **Remaining limitation:** no cross-cell binding, notebook execution semantics, knitr/Quarto
  rendering, saved-output provenance, general R Markdown semantics, detector qualification, or
  Finding permission is introduced.
