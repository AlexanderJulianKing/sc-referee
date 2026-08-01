# Experiment 0039: General static scope joins

## Question

Can the existing publication, selected-cell, separate-source writer, calculation-input, and
imported-execution boundaries use one deterministic connectivity graph without changing public
scientific outputs or upgrading static evidence into an execution claim?

## Scope

This experiment completes post-MPP backlog item L05 under accepted ADR-0048. It introduces the
internal `general-static-scope-join-v1` graph. No public JSON Schema, Finding authority, detector
qualification, model privilege, or project-execution privilege changes.

Every `ScopeJoinProof` binds a closed relation, source and target public record references, exact
supporting-record payload digests, the immutable RepositorySnapshot digest, a finite evidence
profile, and explicit authority limitations. The graph has a deterministic digest, an eight-edge
path ceiling, and one-path-only resolution. Missing, competing, cyclic, weak, broken, or
same-path-conflicted evidence returns no path.

The graph keeps five authorities separate:

1. a PublicationSurface selected one exact full-digest Artifact;
2. a scientist or explicit invocation selected an exact item for review;
3. one independently reverified active notebook or Quarto cell is contained in the selected source
   Artifact;
4. one statically reachable Python writer declares the exact selected output path; and
5. an Execution record names exact input, output, or environment references.

None of those edges alone establishes that project code ran, that a writer produced the captured
bytes, that a selected item was scientifically material, or that the analysis was correct.

## Acceptance criteria

1. Existing selected-report and R Markdown paths resolve through the common publication edge while
   retaining their exact prior public relation names.
2. Notebook and Quarto cells use parser-result identity internally, so distinct cells from one
   same-path container cannot collapse, while their public citations and scope path remain
   unchanged.
3. The founder-orientation separate-source path is still exactly FileRecord to unique writer
   Operation to selected Artifact to PublicationSurface; competing, unreachable, dynamic, unused,
   or disconnected writers abstain.
4. Every frozen calculation input carries a graph path. Ordinary compact tables require exact
   full-digest snapshot identity plus the adapter's exact report declaration. Explicit material
   inputs additionally require an exact review-selection path.
5. Imported execution rows receive input, output, or environment edges only for exact existing
   public references. Current Nextflow rows with no input or output references remain disconnected
   from the selected report.
6. Linked scope Answers deterministically rebuild and replace the internal graph projection for the
   identical snapshot. Replay preserves the graph and public semantic output exactly.
7. Removing one evidence profile affects only consumers of that profile; it cannot create a path
   through another authority class.

## Tests added or strengthened

`tests/test_static_scope_joins.py` covers independent identity, review-selection, and execution
profiles; multiparent ambiguity; cycles; same-path record conflicts; weak identity; unselected
artifacts; disconnected transformed intermediates; imported executions without exact input/output
references; profile removal; bound-payload mutation; and deterministic graph-byte replay.

Existing `tests/test_scientific_check_integration.py` controls retain the selected-report,
unique-writer, competing-writer, unreachable-writer, unused-source, module-removal, no-execution,
and replay boundaries. `tests/test_cell_scientific_evidence.py` retains distinct notebook/Quarto
cell identity, disabled-cell, exact citation, no-execution, and replay controls.
`tests/test_calculation_checks.py` and the seven specialized calculation suites retain all current
outcomes through the shared graph, including the compact dense-H5AD/Biermann-compatible material
path. `tests/test_scope_selection.py` proves linked Answer preservation and graph refresh.

The content-addressed scientific and calculation release manifests now bind the shared graph and
context implementations. The regression-corpus component inventory, local source digests, ledger
digest, and execution-plan digest were refreshed mechanically; the retained cases and their
qualification exclusion did not change.

## Result

The complete 1,304-test unit and integration suite passes after migration. The full handoff
verifier also passes: Ruff and both strict mypy suites are clean; all 79 public schema examples
validate at schema 0.18.0; all 26 regression components, 10 sources, and 103 retained cases remain
complete and excluded from qualification use; the installable application and evaluation wheels
build; the walking-skeleton, interaction, semantic-lock, replay, RO-Crate, storage, capability, and
schema-migration checks pass through schema 0.18.0.

Existing public scope-join relations, questions, assertions, deterministic calculation
observations, disclosures, Findings, and replay projections remain under their previous output
ceilings. The semantic lock additionally contains the canonical internal graph projection and
digest. No project-authored code or model is used to construct or repair an edge.

## Remaining limitations

- Static writer reachability does not prove that the writer ran or produced the snapshotted bytes.
- Review selection does not prove execution, lineage, scientific intent, materiality, or
  correctness.
- Imported records are only as authoritative as their independently supported exact references;
  weak Nextflow rows remain disconnected from publication scope.
- The graph generalizes connectivity, not scientific vocabulary. Natural-language breadth remains
  L06, source-method breadth remains L07, and cross-cell dataflow remains L08.
- Arbitrary DAGs, dynamic writers, transformed payload provenance, runtime values, hidden notebook
  state, and large-format semantics remain unsupported.
