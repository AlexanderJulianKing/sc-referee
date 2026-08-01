# ADR-0034: Add bounded non-executing Jupyter notebook inventory

- **Status:** Accepted under the repository owner's standing authorization for non-authority-
  changing development ADRs
- **Date:** 2026-07-30
- **Related decisions:** Normative SA-FR-003 and SA-FR-007, accepted implementation ADR-0017,
  accepted ADR-0033
- **Schema impact:** None; accepted schema v0.15.0 remains unchanged

## Context

The audit now handles Python, Markdown, bounded R Markdown, and bounded `.R` syntax, but `.ipynb`
files still appear only as publication candidates and unsupported source paths. Notebook-first
scientists therefore cannot see which cells and saved outputs the immutable audit actually
captured. The public SourceRef vocabulary already includes `notebook_cell`, `cell_id`, and
`selector`, so a schema release is not needed for a conservative inventory.

Notebook JSON is not execution evidence. A saved execution count may be stale, duplicated, null,
or inconsistent with cell order; saved outputs may be stale or manually edited; markdown is
untrusted repository text; and code cells may contain arbitrary project code. This increment must
make those materials addressable without executing, rendering, trusting, or scientifically
interpreting them.

## Decision

### 1. Recognize one bounded notebook envelope

`parser:jupyter-notebook-inventory` version `0.1.0` accepts only a regular strict-UTF-8 JSON file
at or below 5,000,000 bytes with:

- `nbformat` exactly `4` and a nonnegative integer `nbformat_minor`;
- a JSON object root and a `cells` array of at most 2,000 objects;
- cell types limited to `markdown`, `code`, and `raw`;
- cell `source` represented only as one string or an array of strings; and
- no duplicate JSON object keys.

Malformed JSON, duplicate keys, unsupported notebook versions, invalid cells, and finite-budget
violations produce a localized ParserResult. They never stop unrelated files or the audit.

### 2. Preserve exact semantic cell and output pointers

Each admitted cell records its zero-based index, cell type, exact source-text digest, source byte
count, source line count, metadata digest, and a `notebook_cell` SourceRef. A unique nonempty v4
cell `id` is preserved. Missing IDs use a deterministic `index-N` locator and are explicitly marked
synthetic; duplicate or invalid IDs make the notebook partial rather than silently selecting one.

Code cells preserve the literal JSON execution count only when it is null or a nonnegative
integer. Any other form is opaque. Up to 10,000 saved output objects across the notebook are
inventoried by cell and output index, output type, canonical payload digest, and a SourceRef whose
selector is `output-N`. Attachments and output payloads are not decoded, rendered, or promoted to
scientific results in this increment.

### 3. Treat notebook state as evidence, never as execution

The parser uses only strict JSON decoding and canonical hashing. It does not import `nbformat`,
start a kernel, execute a cell, render Markdown or HTML, deserialize arbitrary objects, resolve
widgets, load attachments, invoke project environments, or make network calls. Instruction-like
markdown and dangerous-looking code are inert bytes.

Execution counts, cell order, metadata, and saved outputs are recorded observations only. They do
not establish that cells ran, ran in that order, produced the saved output, used the current
environment, or generated the selected publication surface. Hidden state and out-of-order
execution remain explicit notebook-runtime unknowns.

### 4. Integrate only the inventory boundary

`.ipynb` becomes a supported, project-locally cached parser path. The ParserResult enters the
canonical audit, coverage, semantic lock, report, diff, and model-free replay paths. A notebook may
remain a publication candidate, but this increment does not extract Claims, Python/R operations,
scientific-check operands, or Findings from cells. Selected-notebook claim extraction therefore
remains unavailable and visible as a coverage limitation.

The generated capability matrix receives one detector-free `jupyter_notebook` entry for bounded
v4 cell and saved-output inventory. Syntax recognition is partial, operation extraction and
semantic modeling are `not_started`, tested/inferred versions are empty, and domain-wide support
remains prohibited.

## Alternatives rejected

### Execute cells to determine their true order or outputs

Rejected because the production MPP does not execute project-authored code and notebook execution
would introduce hidden environment, state, cost, and security dependencies.

### Trust saved output as a reproduced result

Rejected because notebook output is repository-supplied evidence and may be stale or edited.

### Parse every code cell as Python or R immediately

Rejected because kernels may use many languages and magics, cell semantics differ from script
semantics, and a generic cell-to-operation bridge needs its own bounded contract and controls.

### Treat array position as a real missing cell ID

Rejected because an index is a deterministic locator but not author-supplied notebook identity.
The distinction remains explicit.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** valid v4 markdown/code/raw cells; string and string-array sources; preserved and
  synthetic cell identities, including collision avoidance against author-supplied IDs; saved-
  output selectors and digests; inert code/markdown markers;
  malformed JSON, duplicate keys, invalid version/cell/source/execution-count/output, duplicate
  cell IDs, cell/output/byte ceilings, source-path safety, whole-audit selection and coverage,
  project-local cache hit/invalidation, semantic lock and replay, exact detector-free capability
  generation and mutation rejection, and built-wheel notebook audit.
- **Acceptance criterion satisfied:** AC-02 and SA-FR-003 gain an exact, non-executing notebook
  source-location inventory that works in a notebook-only workspace and survives audit/replay.
- **Remaining limitation:** cells are not parsed into general operations or Claims; notebook
  markdown and saved HTML are not rendered; outputs are not authenticated or linked to code;
  execution order, hidden state, kernels, magics, widgets, attachments, environments, and
  scientific meaning remain unknown. This is source connectivity, not notebook correctness.
