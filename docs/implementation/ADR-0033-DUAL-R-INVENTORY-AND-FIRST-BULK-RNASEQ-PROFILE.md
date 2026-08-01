# ADR-0033: Add dual non-evaluating R inventory and the first bulk RNA-seq profile

- **Status:** Accepted under the repository owner's standing authorization for non-authority-
  changing development ADRs
- **Date:** 2026-07-30
- **Related decisions:** Normative specification ADR-0031 and ADR-0036, accepted implementation
  ADR-0017, and Experiment 0025
- **Schema impact:** None; accepted schema v0.15.0 remains unchanged

## Context

The domain-neutral evidence path, modular question registry, skill transport, and replay now work
across the ten public GeneBench development families. The next named product gap is not another
benchmark-specific question. SA-FR-089 requires resilient Tree-sitter-R inspection plus an
isolated non-evaluating base-R `parse(keep.source = TRUE)` / `getParseData()` helper when R is
available. SA-FR-094 and AC-54 separately require the first narrow domain pack to declare exact
DESeq2, edgeR, and limma-voom operations without making bulk RNA-seq define the core.

The current implementation has only a bounded R Markdown chunk inventory. It does not parse `.R`
source, compare independent R parsers, or publish a bulk RNA-seq capability profile. Pretending
that the R Markdown connector is general R support would overstate the evidence. Adding a bulk
RNA-seq detector before the source boundary and a recurring scientific obligation exist would
also violate the project's anti-overfitting rule.

## Decision

### 1. Add two independently identified `.R` parser results

Every fully captured regular `.R` source at or below a 2,000,000-byte parser ceiling receives:

1. `parser:r-tree-sitter-inventory` version `0.1.0`, using `tree-sitter` `>=0.25.2,<0.26` and
   `tree-sitter-r` `1.3.0` pinned to upstream commit
   `346d3707b8c9301f1051e8f6e32666e67529f7d2`; and
2. `parser:r-base-parse-data` version `0.1.0`, produced only by the auditor-owned helper when a
  usable base-R executable is present.

The grammar dependency is commit- and archive-hash-pinned and its MIT license, source, version, and digest are
carried in package and repository third-party notices. Public-release dependency packaging may be
reconciled later; this overhaul must not distort the scientific or parser contract to match an
older public repository layout.

The two ParserResults remain separate public records. Tree-sitter is available without R. Missing,
timed-out, failed, or structurally invalid base-R output becomes a localized
`parser_unavailable`, `error`, or partial ParserResult and never suppresses the Tree-sitter result
or the rest of the audit.

### 2. Keep the base-R helper parse-only

The controller may launch only the packaged helper with an argument-vector subprocess, `R
--vanilla --slave`, a bounded timeout, a temporary auditor-owned working directory and home, and
an isolated auditor-owned copy of the immutable materialized source bytes. The helper may call only base-R parsing and serialization
functions needed for `parse(keep.source = TRUE)` and `getParseData()`.

It must never call `source`, `sys.source`, `eval`, `evalq`, `parse` followed by evaluation,
`library`, `require`, `attach`, package installation, network functions, project scripts, or
project workflow commands. R expressions such as `system()`, file writes, network calls, and
package loads remain inert syntax. Tests use an embedded write marker and require that it never
appears.

### 3. Inventory syntax and exact call surfaces, not scientific meaning

Each backend records exact source spans for its bounded call inventory. A call observation may
contain only:

- the literal terminal function name;
- a literal `package::function` or `package:::function` target when present;
- literal argument names;
- source coordinates and source text digest; and
- whether the target is direct, namespaced, or otherwise dynamic/opaque.

Unqualified names do not establish package ownership. Aliases, wrappers, tidy evaluation,
generated formulas, computed dispatch, dataflow, package behavior, runtime execution, and
scientific intent remain unknown. No public Operation, AnalysisDecision, Claim lineage edge,
scientific-check operand, DetectorResult, or Finding is emitted from this first call inventory.

When both backends complete, the controller compares syntax acceptance and the canonical direct or
namespaced call-span inventory. Exact disagreement is recorded in `parser_disagreement` on both
records and makes coverage partial. Agreement is recorded only as a finite comparison receipt; it
does not establish that the code ran or that either parser captured runtime meaning.

### 4. Publish three separate narrow bulk RNA-seq profiles

The generated capability matrix receives three no-detector entries under domain
`bulk_rna_seq_differential_expression`:

- DESeq2: `DESeqDataSetFromMatrix`, `DESeq`, and `results`;
- edgeR quasi-likelihood: `DGEList`, `filterByExpr`, `glmQLFit`, and `glmQLFTest`; and
- limma-voom: `DGEList`, `filterByExpr`, `calcNormFactors`, `voom`, `lmFit`, `eBayes`, and
  `topTable`.

These are exact syntactic operation scopes, not complete workflow recipes. Syntax recognition and
call extraction are partial; semantic modeling is `not_started`; tested and inferred package
versions remain empty; no detector manifest is attached; and the strongest detector-dependent
assessment is unavailable. The matrix continues to prohibit domain-wide support or validation
claims.

### 5. Keep the general architecture and authority unchanged

The R parsers plug into the existing snapshot, canonical ParserResult, coverage, cache-policy,
semantic-lock, report, and replay path. R source-derived caching is initially disabled and reported
as unavailable rather than weakening the project-local authenticated cache contract.

This decision does not add a scientific-check rule, detector, Finding authority, model call,
project-code execution privilege, schema release, package-version compatibility claim, or
qualification evidence. A later bulk RNA-seq scientific check must begin from a concrete recurring
method obligation and pass the same positive, verified-good, ambiguous, hard-negative, removal,
sibling, replay, and false-question controls as every other shared module.

## Alternatives rejected

### Treat the R Markdown chunk inventory as general R parsing

Rejected because it inventories fenced chunk boundaries only and explicitly does not establish R
syntax, package calls, or rendered behavior.

### Use only base R

Rejected because R may be absent and the normative architecture requires resilient Tree-sitter-R
coverage independently of a project R environment.

### Use only Tree-sitter-R

Rejected because the accepted architecture requires an independent base-R parse-data comparison
when R is available and explicit parser disagreement.

### Add a DESeq2-versus-edgeR-versus-limma correctness question

Rejected because selecting an engine is not itself a demonstrated issue and no governing
scientific obligation or recurring incompatibility has yet been established. The first pack
declares observable scope and gaps; it does not invent a universal method ranking.

### Infer package ownership from bare function names

Rejected because R permits rebinding, masking, aliases, wrappers, and dynamic dispatch. Only an
explicit namespace is package-identifying in this increment.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** Tree-sitter parsing without R; separately identified base-R parse data when R is
  available; exact direct and namespaced call spans; parser agreement and disagreement; malformed,
  oversized, unavailable-R, timed-out, invalid-helper-output, and dynamic-call cases; an inert
  `system()`/file-write marker; arbitrary-repository audit, status, semantic lock, and replay;
  project-local cache non-use for `.R`; exact three-entry capability generation; mutation failures
  for operation scope, parser identity, versions, detector claims, and domain-wide claims; and
  built-wheel inclusion of the helper and third-party provenance.
- **Acceptance criterion satisfied:** AC-47 gains the accepted dual static R parser boundary and
  AC-54 gains three independently declared narrow bulk RNA-seq operation profiles, while the
  default audit remains non-executing and every result stays replayable and coverage-bounded.
- **Remaining limitation:** this slice does not parse R Markdown chunks through the dual stack,
  build general R dataflow or formula semantics, establish package ownership for unqualified calls,
  inspect rendered output, validate any DE design or contrast, test package versions, qualify a
  detector, or establish correctness of a bulk RNA-seq workflow. Those remain explicit gaps rather
  than inferred support.
