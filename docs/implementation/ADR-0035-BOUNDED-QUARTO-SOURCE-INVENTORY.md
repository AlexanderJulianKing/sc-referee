# ADR-0035: Add bounded non-rendering Quarto source inventory

- **Status:** Accepted under the repository owner's standing authorization for non-authority-
  changing development ADRs
- **Date:** 2026-07-30
- **Related decisions:** Normative SA-FR-007 and SA-FR-072, accepted ADR-0017, accepted ADR-0034
- **Schema impact:** None; accepted schema v0.15.0 remains unchanged

## Context

Quarto is the remaining P0 source surface with no parser connectivity. `.qmd` files already appear
as publication candidates, but the audit currently reports them as unsupported and cannot preserve
their executable-cell boundaries. Rendering a Quarto document can invoke project code, language
kernels, filters, extensions, includes, and external resources, so rendering is outside the
production non-executing path.

The public SourceRef already supports `document_chunk` and `chunk_label`. A bounded source-only
inventory can therefore close the location boundary without a schema release or any claim of
Quarto conformance, execution, rendered meaning, or scientific correctness.

## Decision

### 1. Recognize one finite source subset

`parser:quarto-source-inventory` version `0.1.0` accepts regular strict-UTF-8 `.qmd` files at or
below 2,000,000 bytes and 100,000 lines. It inventories:

- one optional leading `---` YAML front-matter span closed by `---` or `...`, without parsing YAML;
- nonempty prose lines outside executable cells; and
- at most 2,000 exact triple-backtick cells whose opening line is
  ```` ```{engine} ```` with a literal bounded engine token.

Other Markdown fences remain prose/source material; they are not promoted as executable Quarto
cells. Unterminated front matter or admitted executable cells produce localized partial coverage.

### 2. Preserve exact cell identities without interpreting code

Each cell records a zero-based index, literal engine, fence/code line boundaries, exact code-text
digest, and a `document_chunk` SourceRef. Literal leading `#| key: value` option lines are
inventoried as strings. A unique bounded `label` option becomes the declared chunk label;
otherwise a deterministic collision-free `cell-N` label is marked synthetic. Duplicate labels
make the affected cells partial and synthetic rather than selecting one.

Only literal `eval: false` or `eval: true` is classified. Every other evaluation form is unknown.
The classification records source declaration only and never establishes actual execution.

### 3. Never render or execute

The parser performs byte reading, strict UTF-8 decoding, finite line scanning, regular-expression
matching, and hashing only. It does not invoke `quarto`, Pandoc, Jupyter, knitr, R, Python, Julia,
shell, project extensions, filters, includes, shortcodes, or network access. Cell code and document
text are repository evidence, never instructions.

Quarto YAML meaning, profiles, parameters, project configuration, includes, cross-references,
shortcodes, inline code, Markdown rendering, filters, output formats, generated artifacts, runtime
order, environments, and scientific meaning remain opaque.

### 4. Integrate only structural connectivity

`.qmd` enters project-local authenticated parser caching, canonical audit records, coverage,
semantic lock, report, diff, and model-free replay. It is removed from the unsupported-source list
but does not produce Claims, Operations, scientific-check operands, or Findings.

The generated capability matrix receives one detector-free `quarto` entry. Syntax recognition is
partial; operation extraction and semantic modeling are `not_started`; tested/inferred versions
are empty; and domain-wide support remains prohibited.

## Alternatives rejected

### Render the document to discover its actual output

Rejected because rendering can execute project-authored code and extensions and depends on an
unverified environment.

### Reuse the R Markdown adapter and treat every cell as R

Rejected because Quarto is multi-engine and its cell-option syntax and rendering semantics differ.

### Parse YAML or cell code in the first increment

Rejected because structural source connectivity does not require interpreting configuration or
language semantics. Those bridges need separate bounded contracts and controls.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** valid front matter/prose/multi-engine cells, exact chunk references, declared and
  collision-free synthetic labels, literal evaluation states, unclosed front matter/cells, invalid
  UTF-8, byte/line/cell ceilings, inert code markers, safe source paths, whole-audit selection,
  authenticated cache hit/invalidation, semantic lock/replay, capability mutation rejection, and
  built-wheel inspection.
- **Acceptance criterion satisfied:** SA-FR-007 and AC-02 gain exact bounded Quarto source locations
  through a versioned non-executing adapter.
- **Remaining limitation:** no YAML, Markdown, inline-code, shortcode, include, project, code-cell,
  rendering, runtime, environment, artifact-lineage, Claim, or scientific semantics are modeled.
  This is Quarto source connectivity, not Quarto workflow validation.
