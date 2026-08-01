# ADR-0048: Compile one general static scope-join graph

- **Status:** Accepted
- **Date:** 2026-08-01
- **Related decisions:** ADR-0037, ADR-0038, ADR-0039, ADR-0044, ADR-0045, ADR-0047
- **Related backlog item:** L05
- **Coordinated schema release:** None; retain public schema 0.18.0

## Context

sc-referee already carries several exact connectivity proofs, but they were introduced inside
individual adapters. Selected-report wording, selected notebook and Quarto cells, a uniquely
reachable separate Python writer, declared calculation inputs, and compact single-cell inputs all
reach their review subject through different code paths. This makes new adapters expensive and
creates a risk that two checks interpret the same static edge differently.

ADR-0047 now lets the scientist select exact source, input, and output identities. Those selections
need a shared consumer. Selection establishes review scope only; it must not be relabelled as
execution, provenance, primary-analysis status, or scientific correctness.

## Decision

1. The controller compiles one immutable `general-static-scope-join-v1` graph from the exact
   RepositorySnapshot, full-digest AssetIdentity records, selected PublicationSurface, bounded
   review-scope selections, static ParserResult and Operation records, snapshotted Artifacts, and
   imported or controller-observed Execution records.
2. Every graph edge is a typed `ScopeJoinProof`: source and target record references, a closed
   relation, an evidence profile, exact supporting record references, a deterministic evidence
   digest, the source snapshot digest, and explicit authority limitations. The graph itself is
   canonically ordered and self-digested.
3. The initial closed relations cover:
   - exact publication-surface selection;
   - scientist- or invocation-selected analysis source, material input, and analysis output;
   - verified active cell containment in one selected notebook or Quarto Artifact;
   - one statically reachable source Operation and its mutually referenced snapshotted output;
   - full-digest Artifact availability for a later exact declared-input adapter binding; and
   - Execution input, output, and environment edges only when those exact public references exist.
4. A path resolver returns a path only when the requested profile has one canonical finite path.
   Zero paths remain unavailable. Multiple distinct paths, cycles, broken reciprocal references,
   same-path identity conflicts, weak identities, unsafe paths, and paths above the finite edge
   ceiling remain ambiguous or unsupported.
5. Scientific adapters consume the common resolver instead of implementing their own graph walk.
   Existing public scope-join relation projections remain unchanged in this migration so current
   questions, experimental detector inputs, and replay meaning do not drift.
6. Calculation contexts admit bytes through the same graph. Explicit material inputs must have an
   exact selected-review path. Ordinary compact tabular candidates may expose only a full-digest
   snapshot-identity path; the calculation adapter must still bind one exact path declared in the
   selected report before producing an applicable observation.
7. Imported execution evidence is not upgraded. The current bounded Nextflow trace rows declare no
   input or output references, so they remain isolated imported records and cannot close a path to
   the publication surface. A future importer may add edges only from independently supported exact
   public references.
8. The semantic lock records the internal graph projection and digest. It is not a new public
   record, Finding premise, execution claim, or correctness claim. Model calls cannot construct or
   repair graph edges.

## Authority and schema impact

No public schema change is required. Existing public questions and observations continue to carry
their current scope-join projections. The general graph is an internal deterministic lock input and
uses only existing public record references as evidence.

This ADR changes internal connectivity authority and is accepted under the repository owner's
standing authorization for non-material ADR and schema decisions. It does not authorize project
execution, allow model confidence to establish a premise, or promote any detector.

## Acceptance evidence required

- current founder-orientation report/source agreement remains unchanged;
- selected notebook and Quarto cells retain exact distinct citations;
- the separate-source writer path retains its exact three public edges;
- all eight calculation families and the frozen Biermann path retain their outcomes;
- multiparent, same-path identity, ambiguous producer, unused source, dynamic writer, transformed
  payload, weak identity, and unselected Artifact controls fail closed;
- removing the common graph or one edge profile affects only its consumers;
- imported executions without exact input/output references remain disconnected;
- no project code executes and no model call occurs after semantic lock; and
- the graph, public semantic records, and report meaning replay exactly.

## Remaining limitations

Static scope is not runtime lineage. A selected file may be relevant to review without having run;
a literal writer may never have executed; and an imported trace may be repository-authored or
incomplete. General graph construction reduces duplicated connectivity code but does not make the
supported parser, format, wording, or scientific-method vocabulary general.
