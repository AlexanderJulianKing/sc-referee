# ADR-0036: Separate the domain-neutral core slice from the first bulk RNA-seq profile

## Status

Accepted.

## Context

The public GeneBench material motivates the architecture but does not map cleanly to a conventional bulk RNA-seq vertical slice. Letting one domain define the core would overfit the evidence model.

## Decision

The first architectural slice exercises the complete evidence-compiler path on domain-neutral records and GeneBench-derived or synthetic fixtures. The first named domain pack is a deliberately narrow bulk RNA-seq differential-expression profile covering enumerated DESeq2, edgeR, and limma-voom operations. See SA-FR-094.

## Consequences

- Core records remain reusable across domains.
- GeneBench alignment begins immediately.
- Bulk RNA-seq remains the first broadly useful bioinformatics profile without defining the architecture.
