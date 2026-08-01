# sc-referee schema package

**Version:** 0.9.0

This immutable JSON Schema Draft 2020-12 package defines the public sc-referee record model at
`https://w3id.org/sc-referee/schema/v0.9.0/`.

Version 0.9.0 implements accepted ADR-0008. Blind Stage-1 AgentReviews receive only review-local
root-cause candidate identities. Fresh Stage-2 reviewers independently reconcile exact frozen
candidate sets. A public AdjudicatedRootCause exists only after cross-provider membership,
evidence, falsification, chronology, and dissent gates pass.

Prose similarity, embeddings, confidence, and majority vote cannot establish root-cause identity.
The canonical identity does not map detector Findings or create qualification metrics. Accepted
v0.8.0 and earlier schema packages remain immutable.
