# Shipped pipeline fixes — 2026-07-10

This note is intentionally under `tests/`: the authorized change boundary excluded the inference
engine (including its historical `BUILD_NOTES.md`) and the general documentation tree.

## Claim binding for multi-output workflows

- `config.confirmed_reported_path()` reads only the canonical in-folder `sc-referee.yaml` and grants
  claim-selection authority only when `confirmed_by_human: true`.
- `ingest()` validates the confirmed `reported_results.path` as an existing regular CSV/TSV under
  the audited folder and requires the existing reported-DE shape (feature/gene plus p or adjusted-p).
  A missing, escaping, unsupported, unreadable, or non-DE declaration raises `DesignError`; it can
  never become a scientific finding.
- With multiple report-shaped tables, a valid confirmed declaration binds exactly the declared
  table via `_load_reported`. Without confirmed authority, the legacy ambiguity guard still binds
  none. With one table, the legacy auto-detection output and provenance are byte-frozen unchanged.
- The existing JSON schema already defined `reported_results.path`, `gene_col`, `padj_col`, and
  `unit_of_test`; no schema relaxation or migration was necessary. The config loader gained the
  narrow confirmed-path projection needed by the ingest-first audit order.
- This round intentionally implements the minimum singular claim contract. A `claims:` list was
  not added because the shipped `Bundle` has one `reported_results` slot; pretending to support
  multiple simultaneous claim roots without changing that model would silently discard claims.
- The authority applies to the canonical `<folder>/sc-referee.yaml`. Supporting an alternate
  external `--design` file during ingest would require changing the audit seam, outside this
  round's allowed files.

## Init proposer enum robustness

- `_normalize_proposer_enums()` runs before tool-payload schema validation.
- Every confidence role preserves only `high` or `low`; all other values (including `medium`) become
  `low`.
- Unknown `analysis_type` becomes `other`; unknown `unit_of_test` becomes `null`; unknown
  `type_confidence` becomes `low`. An unknown unresolved-role label marks every model-authored role
  unresolved. Valid enum values are unchanged, and malformed non-enum shapes still fail validation.
- `write_config()` remains the final schema gate and still forces `confirmed_by_human: false`.

## Frozen differential enumeration

The machine-readable oracle is `tests/frozen_oracles/pipeline_claim_init_oracles.json`.

- New fixture `two_tables_confirmed_declared_claim`: `reported_results=None` (ambiguous; report-bound
  checks abstained) -> `reported_results=de_claim.csv` (confirmed declared claim is audited). This is
  the intended new coverage path; downstream statuses remain those of unchanged shipped checks.
- New fixture `claude_medium_role_confidence`: init schema-validation crash -> schema-valid proposal
  with the drifting role at `low` and `confirmed_by_human: false`. This is a config-generation change,
  not an audit verdict change.
- Existing shipped fixture verdict changes: **none**.
- Existing single-table ingest output is frozen byte-for-byte, including canonical values, source
  columns, and provenance.

## TDD and verification

Initial focused red command (five expected failures before production changes):

```text
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest -q tests/test_reported_decoy.py tests/test_init.py -k 'confirmed_declared_claim or invalid_confirmed_claim or unconfirmed_claim or medium_role_confidence or valid_claude_role_confidence or all_proposer_enum_drift'
```

Focused green command:

```text
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest -q tests/test_reported_decoy.py tests/test_init.py tests/test_schemas.py
```

Final full command:

```text
PYTHONPATH=/tmp/sc-referee-pytest-site UV_CACHE_DIR=/tmp/sc-referee-uv-cache MPLCONFIGDIR=/tmp/sc-referee-mpl uv run pytest
```

Result: **836 passed, 4 warnings in 54.27s**. The temporary `sitecustomize` only supplies a finite
value for macOS `SC_SEM_NSEMS_MAX`, whose read is denied by the managed sandbox; an unwrapped run
otherwise produced 820 passes plus 16 PyDESeq2/Joblib permission failures. No repository file was
used to alter the test environment.

No analyzed code was executed. No inference-engine file was changed. No git operation was run.

## Phase 3c hardening: accusation-direction short-trace soundness

Phase 3c closes three routes by which a non-marker artifact could retain the short marker-extraction
classification. The changes are monotone-conservative: they only remove producer bindings and turn
the affected `double_dipping` cell into `NOT CHECKED`; they do not create a new `FLAGGED` cell.

### Fix A — lexical path-collision keys

Before counting every literal `to_csv` / `to_parquet` egress, the short binder now applies
`os.path.normpath`-style lexical normalization to relative paths. Thus `results/de.csv` and
`./results//intermediate/../de.csv` share one uniqueness key and count as two writers. Absolute
paths, mixed absolute/relative inventories, empty/NUL paths, and non-literal or otherwise unresolved
path components fail closed. The binder still exposes the original raw literal key, and
`_claim_bindings` still performs its prior exact raw claim-path lookup. Normalization can therefore
detect a new collision but cannot make a formerly unmatched spelling classify a claim.

### Fix B — opaque-call havoc for all live marker aliases

Once any exact marker-extracted frame is live, every call other than the exact extractor statement
or a direct, unnested `to_csv` / `to_parquet` egress on that proved live frame clears **all** live
marker names and aliases. The call need not mention the frame syntactically. This closes both a
global/closure replacement such as `replace_report()` and an indirect
`patch('pandas.core.generic.DataFrame.to_csv', new=fake).start()` before egress. Egress-shaped calls
on an unproved receiver and reviewed egresses containing nested calls also havoc all live frames.

The general safe-callee allowlist is deliberately **empty**. No `print`, `len`, or other general
callee is currently exempt: without an accusation-grade effect summary, even a familiar callee may
be shadowed, invoke user protocol code, rebind a global/closure, or patch the egress method. The exact
marker extractor and direct live-frame egress are structural proof steps handled separately, not
members of the allowlist.

### Adversarial TDD and differential

Three named audit-level tests were added in `tests/test_multi_claim_coverage.py`:

- `test_short_marker_trace_abstains_on_filesystem_equivalent_path_spellings` covers `./`, `..`, and
  redundant separators in a non-marker overwrite of the marker report;
- `test_short_marker_trace_havocs_global_reassignment_through_opaque_call` covers an indirect
  `global de` replacement before egress; and
- `test_short_marker_trace_havocs_indirect_to_csv_monkeypatch` covers an indirect mock patch of
  `DataFrame.to_csv` before egress.

The existing ambiguity parameterization also now covers a mixed absolute/relative path inventory.
Before the production change, the three named tests all failed with
`results/de.csv / double_dipping = FLAGGED`. After the change, each is `NOT CHECKED (NOT_RUN)`.
In each adversarial fixture this is the complete per-claim cell differential:

- `results/de.csv`: only `double_dipping FLAGGED -> NOT CHECKED`; `confounding CLEAR`,
  `experimental_unit FLAGGED`, `multiple_testing CLEAR`, `effect_size_threshold CLEAR`, and
  `pairing FLAGGED` are unchanged.
- `results/splicing.csv`: no cell changes — `confounding CLEAR`, `experimental_unit FLAGGED`,
  `multiple_testing NOT CHECKED`, `count_model N/A`, `effect_size_threshold CLEAR`,
  `pairing FLAGGED`, and `double_dipping NOT CHECKED`.

The real demo differential is **no cell changes**: DE retains those first five states plus
`double_dipping FLAGGED`, while splicing retains the seven states above and is never a marker claim.
The frozen 120-column render and singular-folder finding bytes remain identical.

TDD red command and result:

```text
PYTHONPATH=. UV_CACHE_DIR=/tmp/sc-referee-uv-cache MPLCONFIGDIR=/tmp/sc-referee-mpl uv run pytest -q tests/test_multi_claim_coverage.py -k 'filesystem_equivalent_path_spellings or global_reassignment_through_opaque_call or indirect_to_csv_monkeypatch'
```

Result before production changes: **3 failed**. Focused final result:

```text
PYTHONPATH=. UV_CACHE_DIR=/tmp/sc-referee-uv-cache MPLCONFIGDIR=/tmp/sc-referee-mpl uv run pytest -q tests/test_multi_claim_coverage.py
```

Result: **40 passed**. Final full-suite command:

```text
PYTHONPATH=/tmp/sc-referee-pytest-site UV_CACHE_DIR=/tmp/sc-referee-uv-cache MPLCONFIGDIR=/tmp/sc-referee-mpl uv run pytest -q
```

Result: **920 passed, 4 warnings**. The existing external `/tmp` `sitecustomize` supplies only the
managed-macOS `SC_SEM_NSEMS_MAX` query documented in prior phases; it is not a repository change.
Frozen SinkUse/callee resolution, check arithmetic, detector/inference-engine code, and frozen oracle
files were untouched. No analyzed code was executed. No git operation was run.

## Phase 3b redirect: short marker-extraction claim scope

Phase 3b keeps the Phase 3a multi-claim loop and its design-check un-gating, but removes the full
`rank_genes_groups -> adata.uns -> rank_genes_groups_df -> report` proof from **double-dipping
scoping**. The `bind_uns_marker_report_producers` machinery remains available unchanged for consumers
that need shared-state provenance. It no longer decides whether a reported claim is a marker claim.

The scoping proof is now exactly the local report-value trace:

```text
exact scanpy.get.rank_genes_groups_df call
    -> assigned local DataFrame name (plain local aliases supported)
    -> that live name.to_csv/to_parquet(one literal, globally unique report path)
```

This proof classifies the report family only. It does not inspect the AnnData argument, `uns` key,
upstream marker writer, object aliases, preamble, subviews, or in-place AnnData mutations. Claim
metadata therefore names the exact extraction contract
`scanpy.get.rank_genes_groups_df.v1`; the unchanged double-dipping detector receives its existing
`rank_genes_groups` marker-family signal only after that extraction trace succeeds.

The short trace fails closed on a parse gap, dynamic egress path, patched egress, reflection, nested
or inline/opaque egress receiver, competing writer for the literal report path, a non-marker
reassignment of the DataFrame variable, or an opaque/in-place use of that variable before egress.
Alias identity is conservative: after `report = de`, an opaque mutation through either spelling
invalidates both. A generic nearby `rank_genes_groups` sink without a report-bound marker extraction
does not enter scope. An inline `pd.DataFrame(...).to_csv(...)` report derived from `mannwhitneyu`
cannot be classified as a marker claim.

The acceptance source in `tests/test_multi_claim_coverage.py` is the realistic demo shape, including
`normalize_total`, `log1p`, `highly_variable_genes`, PCA, neighbors, Leiden, and the neuronal gene
signature subview:

```text
np.asarray(adata[:, ['RBFOX3', 'SYT1', 'SNAP25']].X.mean(axis=1)).ravel()
```

On that exact source, the complete per-claim differential remains:

- `results/de.csv`: `confounding CLEAR`, `experimental_unit FLAGGED`, `multiple_testing CLEAR`,
  `effect_size_threshold CLEAR`, `pairing FLAGGED`, `double_dipping FLAGGED`.
- `results/splicing.csv`: `confounding CLEAR`, `experimental_unit FLAGGED`, `multiple_testing NOT
  CHECKED`, `count_model N/A`, `effect_size_threshold CLEAR`, `pairing FLAGGED`, `double_dipping NOT
  CHECKED` (`NOT_RUN`).

The singular-folder byte oracle remains green. The 120-column realistic two-analysis render is frozen
at `tests/frozen_oracles/report_ledger_phase3_tty.txt`. Frozen SinkUse/callee resolution, check
arithmetic, detector code, and inference-engine code were not changed.

TDD red command:

```text
PYTHONPATH=. UV_CACHE_DIR=/tmp/sc-referee-uv-cache MPLCONFIGDIR=/tmp/sc-referee-mpl uv run pytest -q tests/test_multi_claim_coverage.py -x
```

The first realistic run failed at the acceptance rail with `de.csv double_dipping = NOT CHECKED`
instead of `FLAGGED`, reproducing the Phase 3a preamble/subview failure. Focused final verification:

```text
PYTHONPATH=. UV_CACHE_DIR=/tmp/sc-referee-uv-cache MPLCONFIGDIR=/tmp/sc-referee-mpl uv run pytest -q tests/test_audit.py tests/test_double_dipping.py tests/test_report.py tests/inference/test_live_differential_gate.py tests/inference/test_computed_double_dipping_live.py tests/test_multi_claim_coverage.py
```

Result: **99 passed**. Final full-suite command:

```text
PYTHONPATH=/tmp/sc-referee-pytest-site UV_CACHE_DIR=/tmp/sc-referee-uv-cache MPLCONFIGDIR=/tmp/sc-referee-mpl uv run pytest -q
```

Result: **916 passed, 4 warnings**. The first unshimmed run reached only the known managed-sandbox
denial of `os.sysconf("SC_SEM_NSEMS_MAX")` inside joblib/PyDESeq2. The already-documented `/tmp`
`sitecustomize` supplies only that read-only query; it is not a repository change.

---

# Phase 3 / 3a — bind and scope every declared reported claim

## Per-claim binding

- A confirmed config may now declare an ordered top-level `claims:` list. Each entry names a
  report-relative `path` and may name its `contrast`, claim-local `analysis_type`, `unit_of_test`,
  and `value_kind`. The legacy singular `reported_results` object remains the compatibility
  projection and is unchanged for folders without `claims:`.
- `ingest()` validates every declared artifact as an in-folder regular CSV/TSV with the existing
  reported-table shape. It loads all entries into `bundle.reported_claims` in declaration order and
  leaves `bundle.reported_results` pointing at the first claim. One missing, escaping, duplicate,
  unsupported, unreadable, or non-report-shaped entry rejects the whole manifest as `DesignError`;
  no declaration can be silently dropped.
- Each claim is bound parse-only to an exact producing sink. Generic registered sinks retain the
  deliberately narrow static binding: exactly one literal `to_csv` writer, exactly one reaching
  registered sink, and an exact `DataFrame` p/q field dependency. Phase 3a replaces the former
  dependence on the full double-dipping analyzer for Scanpy marker egress with the bounded producer
  summaries below. Missing a judgment is accepted; choosing a possible producer is not.
- The audit uses a shallow claim-local bundle with only that claim's table, original columns,
  measured report digest/locator, declared unit, and exact producing method. Full parsed sources stay
  available only to report-path-scoped proof code. Findings receive their claim root as direct
  metadata outside the legacy dataclass projection, so adding the second claim does not change the
  first claim's serialized finding bytes.

## Phase 3a bounded producer-summary set and uns must-flow

The producer binder is layered on top of the frozen `SinkUse`/callee resolver; neither frozen
resolver nor any check's finding arithmetic changed. Its complete summary set is:

- exact `scanpy.tl.rank_genes_groups`: writes its AnnData receiver's
  `uns[literal key_added]`, defaulting to `uns['rank_genes_groups']`;
- exact `scanpy.get.rank_genes_groups_df`: reads the same AnnData identity and literal `key`,
  defaulting to `uns['rank_genes_groups']`, and returns the marker table; and
- `DataFrame.to_csv` / `DataFrame.to_parquet`: egresses that exact table receiver to one literal,
  globally unique path.

The must-flow is straight-line and contained in one parsed source. The exact SinkUse supplies the
marker-test producer identity; the frozen callee resolver supplies the extractor identity. The
extractor must read the same object name and key written by the one unambiguous marker writer of that
key. A direct stale uns value before the marker call is killed by the later strong write
(last-writer-wins). A parse gap, nested/competing or dynamic-key writer, multiple marker writers of
the key, different AnnData identity, dynamic extractor key, pre-existing object/uns alias,
intervening direct or opaque mutation, marker-table alias/mutation, patched egress, dynamic path, or
multiple/nested writers of the report path makes the binding unavailable. Unsupported cases fail
closed to `NOT CHECKED`; no nearby producer is guessed.

## Phase 3a claim-scoping rule

Producer coverage gates only the code/provenance-sensitive `double_dipping` cell. Design-based
checks (`experimental_unit`, `pairing`, and `confounding`) consume the claim-local declared design,
observations, and `unit_of_test`, so they evaluate per claim even when the producing test is
unresolved. The declared-derived-ratio `count_model` N/A rule remains an applicability rule, not a
producer-flow clearance.

In particular, `double_dipping` runs only for a claim bound to its covered marker-test family. The
splicing table binds to `scipy.stats.mannwhitneyu.v1`, so the `rank_genes_groups` witness elsewhere
in the same source cannot route or run double-dipping for splicing. Unit and pairing checks run for
splicing because the confirmed claim declares a per-cell test with donor as the biological
replicate; producer resolution is irrelevant to those design facts. A confirmed
`value_kind: derived_ratio` proves the raw count-model precondition false and yields `N/A`, not a
clearance.

The adversarial fixtures freeze both failure modes:

- a nearby `mannwhitneyu` whose result does not feed the table's p/q field; and
- a second literal writer to `results/splicing.csv`.

For both, `experimental_unit` and `pairing` remain `FLAGGED`, `confounding` remains `CLEAR`, and only
`double_dipping` becomes `NOT CHECKED (NOT_RUN)`.

The tests enumerate every cell for both producer-gap fixtures, not only those four crux checks. In
each fixture the DE row remains the six-cell matrix below; the splicing row remains, in order:
`confounding CLEAR`, `experimental_unit FLAGGED`, `multiple_testing NOT CHECKED`, `count_model N/A`,
`effect_size_threshold CLEAR`, `pairing FLAGGED`, and `double_dipping NOT CHECKED`. Thus losing the
splicing producer changes no design/table-based cell and cannot contaminate the DE row.

## Frozen two-analysis demo: every cell

The confirmed declaration is
`tests/fixtures/report_ledger_demo/sc-referee.yaml`; the complete 120-column TTY render is frozen at
`tests/frozen_oracles/report_ledger_phase3_tty.txt`.

### `results/de.csv` — exact `rank_genes_groups` producer

- `confounding`: `CLEAR` (`pass`, complete) — exact design algebra finds the cell-type contrast
  estimable against the declared nuisance structure.
- `experimental_unit`: `FLAGGED` (`needs_evidence`, complete) — the declared per-cell claim was
  evaluated by the donor-level recompute; no claimed-significant feature was testable/matched in the
  recompute.
- `multiple_testing`: `CLEAR` (`pass`, complete) — BH is reconstructable and the claims survive.
- `effect_size_threshold`: `CLEAR` (`pass`, complete) — both claimed discoveries meet the existing
  effect-size policy.
- `pairing`: `FLAGGED` (`needs_evidence`, complete) — all four donor levels occur in both arms while
  the confirmed model is unpaired.
- `double_dipping`: `FLAGGED` (`needs_evidence`, complete) — the exact report-path proof binds the
  marker p-values to the naive `rank_genes_groups` test and its data-derived grouping.

These six `Finding` objects are byte-identical to the singular `reported_results: de.csv` audit.
Only direct claim-root metadata, intentionally excluded from the legacy dataclass serializer, is
added for grouping.

### `results/splicing.csv` — exact `mannwhitneyu` producer

- `confounding`: `CLEAR` (`pass`, complete) — the shared confirmed contrast remains estimable.
- `experimental_unit`: `FLAGGED` (`needs_evidence`, complete) — the check evaluated this confirmed
  per-cell claim at donor level; the submitted significant-only table cannot reconstruct a
  comparable FDR family.
- `multiple_testing`: `NOT CHECKED` (`needs_evidence`, `not_run`) — every submitted row is
  significant, so the full family needed for BH is absent.
- `count_model`: `N/A` (`pass`, `not_applicable`) — the confirmed claim is a rank test on a derived
  ratio, not a raw-count model.
- `effect_size_threshold`: `CLEAR` (`pass`, complete) — the one claimed effect meets the existing
  threshold.
- `pairing`: `FLAGGED` (`needs_evidence`, complete) — this claim's own test is per-cell and all four
  donors span both arms while the model is unpaired.
- `double_dipping`: `NOT CHECKED` (`not_audited`, `not_run`) — `mannwhitneyu` is outside the detector's
  covered marker-test family. The DE claim's `rank_genes_groups` witness is not consulted for this
  cell.

Frozen footer: `13 findings · 5 clear · 5 flagged · 2 not checked · 1 n/a`.

## Differential no-regression and verification

- Existing fixtures/statuses/verdicts/render changes: **none**. Folders without `claims:` execute the
  pre-Phase-3 singular branch unchanged.
- New multi-claim fixture: the existing DE findings are byte-identical; seven honest splicing cells
  are added as enumerated above.
- New producer-gap fixtures add only explicit `NOT CHECKED` cells; no adverse finding is introduced.

Initial red command:

```text
PYTHONPATH=/tmp/sc-referee-pytest-site UV_CACHE_DIR=/tmp/sc-referee-uv-cache MPLCONFIGDIR=/tmp/sc-referee-mpl uv run pytest -q tests/test_multi_claim_coverage.py
```

Result before implementation: **4 failed** — no `reported_claims`, no per-claim roots, and only the
singular DE analysis rendered.

Focused final command:

```text
PYTHONPATH=/tmp/sc-referee-pytest-site UV_CACHE_DIR=/tmp/sc-referee-uv-cache MPLCONFIGDIR=/tmp/sc-referee-mpl uv run pytest -q tests/test_multi_claim_coverage.py
```

Result: **8 passed**.

Final full command:

```text
PYTHONPATH=/tmp/sc-referee-pytest-site UV_CACHE_DIR=/tmp/sc-referee-uv-cache MPLCONFIGDIR=/tmp/sc-referee-mpl uv run pytest -q
```

Result: **888 passed, 4 warnings** (the 880-test Phase-2 baseline plus 8 Phase-3 tests).

### Phase 3a TDD and differential gate

Initial focused red command:

```text
.venv/bin/pytest -q tests/test_multi_claim_coverage.py
```

Result before Phase 3a production changes: **5 failed**. The failures reproduced the missed marker
bind without the full double-dipping analyzer's artifact-reader precondition, two unsafe stale/mutated
uns bindings, and the two design-check over-gating cases.

Focused final result: **24 passed**. The acceptance matrix enumerates all 13 demo cells above and
byte-freezes the same two-analysis TTY render. Additional producer red-team cases cover a different
AnnData identity; custom/default and dynamic keys; last-writer-wins; multiple same-key writers;
direct, aliased, and opaque uns mutation; CSV and Parquet egress; dynamic, patched, nested, and
competing paths; and marker-table aliasing.

The first unwrapped full run (before two additional parser-only alias cases were added) reproduced
the managed macOS Joblib denial: **886 passed, 10 failed, 6 errors, 4 warnings**; all 16
failures/errors were
`PermissionError: os.sysconf('SC_SEM_NSEMS_MAX')` in PyDESeq2/Joblib.

Final full command using the already-documented temporary test-process compatibility shim:

```text
PYTHONPATH=/tmp/sc-referee-pytest-site MPLCONFIGDIR=/tmp/sc-referee-mpl .venv/bin/pytest
```

Result: **904 passed, 4 warnings in 51.41s**. The temporary shim only returns a finite value for the
sandbox-denied semaphore-limit query; it is not a repository change.

No analyzed code was executed. No check finding arithmetic or inference evidence math changed. No
git operation was run.

---

# Round 2 — multi-concern routing

## Routing changes

Only `applies_to` routing changed; no check's finding/evaluation logic changed.

- `double_dipping` retains its legacy `marker_detection` route byte-for-byte. The new
  `condition_contrast_DE` cross-route requires every one of: `unit_of_test: cell`, a confirmed
  design, a non-empty reported table with at least one finite in-range p/q value, an unambiguous cell-marker
  call, and `groupby_provenance` resolving the marker test's actual grouping specifically as
  `data_derived`. `unresolved` provenance, an incidental clustering call, predefined grouping, and
  coarse token co-occurrence cannot activate the new route.
- The live inference `double_dipping.v1` verifier now advertises both analysis labels. Its new
  condition-DE route delegates to the same strict report-bound shipped predicate above: producer
  identities without a real report claim cannot make the verifier apply. Its existing
  `needs_evidence` cap is unchanged.
- `experimental_unit` retains its legacy condition-DE route byte-for-byte. Its new marker route uses
  the shared `marker_unit_concern_is_proved` allowlist.
- `pairing` retains its legacy condition-DE route byte-for-byte and uses the same allowlist for its
  new marker route.
- The marker unit/pairing allowlist requires every one of: confirmed design; high-confidence
  replicate role; declared cell-level test; a non-empty reported result; replicate columns present
  in `.obs`; the parse-only exact sink resolver independently resolving the test as per-cell; exact
  declared reference and test levels; and at least one replicate key observed in both levels after
  applying the declared subset. Missing, empty, conflicting, or ambiguous evidence disables the
  route rather than producing a guessed finding.

`registry.py` did not require a change: it already asks every registered verifier's `applies_to`
predicate independently, so removing the single-bucket behavior belonged at those predicates.

## Frozen differential enumeration

The complete finding bytes and old/new inventories are frozen in
`tests/frozen_oracles/multi_concern_routing_oracles.json`.

### New `marker_detection` structural fixture

- `double_dipping`: `needs_evidence` -> `needs_evidence`, byte-identical. This was already applicable.
- `experimental_unit`: absent -> `needs_evidence`. Reason: the exact parsed marker sink tests cells,
  every ratified donor spans both cluster levels, and a non-empty report is bound. The recompute
  honestly reports that the submitted significant-only table cannot reconstruct the FDR family.
- `pairing`: absent -> `needs_evidence`. Reason: all four donor levels span both declared cluster
  arms while the ratified model declares no pairing, so the data is paired-capable.

### New `condition_contrast_DE` structural fixture

- `double_dipping`: absent -> `needs_evidence`. Reason: the report-bound marker grouping is exactly
  data-derived from the expression matrix and feeds an unambiguous per-cell marker test.
- `experimental_unit`: `needs_evidence` -> `needs_evidence`, byte-identical.
- `pairing`: `needs_evidence` -> `needs_evidence`, byte-identical.

### Existing fixtures

- Existing fixture verdict changes: **none**.
- Existing already-applicable findings retain byte-exact serialized output; the frozen acceptance
  fixture also proves this across both labelings.

## Specificity tests

The new routes stay off for:

- condition DE with an incidental Leiden call but a predefined tested grouping;
- a marker contrast that varies only between replicates, not within one;
- an unconfirmed marker design;
- a sample-level exact sink despite a contradictory `unit_of_test: cell` declaration;
- a missing report; and
- an empty report.

The empty-report case is tested independently against both the shipped check and the inference
verifier, closing the engine's former producer-identity shortcut at the routing boundary.

## TDD and verification

Initial acceptance red command:

```text
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest -q tests/test_multi_concern_routing.py
```

Result before production changes: **2 failed, 5 passed** — marker detection lacked
`experimental_unit`/`pairing`, and condition DE lacked `double_dipping`.

The empty-report specificity test was separately observed red before its minimal guard:

```text
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest -q tests/test_multi_concern_routing.py -k empty_report
```

Final focused result: **9 passed**.

Final full command:

```text
PYTHONPATH=/tmp/sc-referee-pytest-site UV_CACHE_DIR=/tmp/sc-referee-uv-cache MPLCONFIGDIR=/tmp/sc-referee-mpl uv run pytest
```

Final result: **845 passed, 4 warnings in 59.83s**. As in Round 1, the temporary `/tmp`
`sitecustomize` only supplies the sandbox-denied macOS semaphore-limit query for PyDESeq2/Joblib;
it is not a repository change.

No analyzed code was executed. No check finding logic was changed. No git operation was run.

---

# Phase 1 — report ledger grouped by bound claim

## Presentation changes

- `render_tty()` now emits `▸ Analysis N — <resolved report path>` followed by the recognition
  line, then prints that claim's findings in their original order. The existing status label,
  check ID, verdict text, metrics detail, citations, worst status, and CI conclusion are unchanged.
- Recognition is projected only from resolved declared facts: `Design.analysis_type`, a complete
  `test vs reference` pair, `Design.unit_of_test`, and an authoritative confirmed
  `reported_results.path`. A missing, `UNKNOWN`, or `unresolved` fact is omitted; a half-resolved
  contrast is never rendered. An alternate external `--design` can describe the contrast but is
  not allowed to masquerade as ingest's canonical in-folder claim binding. The deep analysis-code
  chain is not reconstructed in this phase.
- Exact claim-root metadata, when attached to a finding as `claim_root` or
  `claim_root_binding`, is the grouping key. Legacy Phase 1 findings carry no root field and
  therefore retain the one-bound-claim grouping. A frozen two-root fixture proves stable
  encounter-order grouping for Phase 3 without changing `Finding` or audit orchestration, and
  proves that auxiliary diagnostic metadata cannot split one exact root into two groups.
- TTY and Markdown end with counts from the statuses actually present, in the shipped status
  vocabulary. JSON adds top-level `analyses` and `coverage`; every analysis contains `claim`,
  `recognition`, `findings`, and per-analysis `coverage`. The top-level `findings` array is retained
  as a schema/backward-compatible projection and is byte-identical to the grouped finding records.
- Markdown finding headings move from level 2 to level 3 beneath the new level-2 analysis group.
  Status strings and verdict paragraphs remain byte-identical.

## Frozen differential enumeration

The complete minimal TTY, Markdown, and JSON render is frozen inline in `tests/test_report.py`.
That file also freezes the real `confounding_alias` bound-claim recognition, status counts,
finding order/status/verdict identity, unresolved-fact omission, and two exact claim roots.

Every pre-existing renderer fixture changes as follows:

- `tests/test_report_header.py`, unconfirmed manual `condition_contrast_DE` result:
  old flat finding immediately after the `PROPOSED` header -> new `Analysis 1` group plus minimal
  true recognition `Analysis — condition_contrast_DE.`, the identical `needs_evidence` finding,
  and `coverage: 1 finding · 1 needs_evidence`. No path, contrast, or unit is available on this
  hand-built result, so none is fabricated. The Markdown finding heading is nested one level.
- `tests/test_report_header.py`, confirmed manual `condition_contrast_DE` result:
  old flat finding immediately after the `CONFIRMED` header -> the same group/recognition/coverage
  additions as the unconfirmed case. The existing human-ratified header distinction, finding
  status, and verdict remain unchanged.
- `tests/test_coverage.py`, confirmed `trajectory`/unhandled-analysis JSON result:
  old top-level metadata plus one `not_audited` finding -> those identical fields and flat finding,
  plus one `analyses` entry recognised from the confirmed declaration and Design, and coverage
  `{findings: 1, statuses: {not_audited: 1}}`. Worst status, full-audit flag, CI conclusion, status,
  and verdict are unchanged.
- `tests/test_schemas.py`, confirmed `confounding_alias` JSON result (also used by the strict-JSON
  fixture): old metadata and flat findings -> those identical values plus one analysis for
  `results/de.csv`, recognition
  `Analysis — condition_contrast_DE  (results/de.csv): stim vs ctrl, per sample.`, and coverage
  `{findings: 5, statuses: {blocker: 1, needs_evidence: 3, pass: 1}}`. The existing `Infinity` JSON
  normalization and every finding record remain unchanged; the shipped permissive report schema
  continues to validate.

Existing fixture verdict/status changes: **none**. New status names: **none**. Verdict arithmetic,
check routing, inference, ingest, and audit orchestration changes: **none**.

## TDD and verification

Initial red command, before the production render change:

```text
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/test_report.py
```

Result: **3 failed** (`analyses` did not exist in the old flat renderer).

Focused green command:

```text
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/test_report.py tests/test_report_header.py tests/test_coverage.py tests/test_schemas.py
```

Result: **22 passed**.

The literal unwrapped full command reached all tests but the managed macOS sandbox denied Joblib's
read-only `os.sysconf("SC_SEM_NSEMS_MAX")` query: **845 passed, 10 failed, 6 errors, 4 warnings**.
All 16 failures/errors were the already-documented PyDESeq2/Joblib permission path.

Final full command:

```text
PYTHONPATH=/tmp/sc-referee-pytest-site UV_CACHE_DIR=/tmp/sc-referee-uv-cache MPLCONFIGDIR=/tmp/sc-referee-mpl uv run pytest
```

Result: **861 passed, 4 warnings in 51.53s** (the 856-test baseline plus 5 Phase 1 tests). The
pre-existing temporary `/tmp` `sitecustomize` supplies only a finite value for the sandbox-denied
semaphore-limit query; it is not a repository change.

No analyzed code was executed. No verdict-producing file was changed. No git operation was run.

---

# Phase 2 — four-axis finding state and first-class NOT CHECKED

## Canonical model and derivation

`Finding` now accepts four orthogonal, report-only axes:

```text
applicability : applies | not_applicable | unknown              (default: applies)
judgment      : conformant | violation | concern | unresolved   (default: unset)
coverage      : complete | partial | not_run                    (default: complete)
proof_grade   : exact | recomputed | structural | advisory      (default: unset)
```

The axes are constructor metadata retained on each Finding instance. They are excluded from the
legacy dataclass field projection, equality, and repr, so every pre-Phase-2 `public_bytes(Finding)`
oracle remains byte-identical. The report emits all four axes explicitly. An informational finding
with no explicit grade receives `advisory`; other unset grades remain unset rather than inventing a
proof basis.

`statuses.human_state()` is the only derivation point. It is presentation-only and is never called
by audit severity or CI code:

- `applicability=not_applicable` -> `n_a`.
- supported `judgment=violation|concern` -> `flagged`, even with incomplete coverage.
- shipped `blocker|major|informational` -> `flagged`, even with a contradictory incomplete-coverage
  annotation; Phase 2 permits only genuine `needs_evidence` abstentions to reclassify.
- `applicability=unknown` or `coverage=partial|not_run` -> `not_checked`.
- `applies + conformant + complete` -> `clear`.
- default-axis compatibility fallback: `pass -> clear`; `not_audited -> not_checked`;
  `needs_evidence|major|blocker -> flagged`; `informational -> flagged` with advisory proof grade.
- unmatched/invalid combinations fail closed to the shipped mapping; an explicitly unresolved,
  complete judgment is `flagged`, never silently clear.

The shipped `status` remains on every TTY/Markdown/JSON finding. TTY and Markdown lead with the
derived label and show the shipped status parenthetically. JSON retains status inventories and adds
human-state inventories; coverage footer text counts only `clear`, `flagged`, `not checked`, and
`n/a`.

## Exhaustive NEEDS_EVIDENCE -> NOT CHECKED reclassification ledger

Every item below keeps `status=needs_evidence` byte-for-byte and adds only `coverage=not_run` at the
check-owned return. Each is an abstention because the named input prevented that check's recompute or
comparison from completing; none is evidence that the invariant was violated.

### `allele_orientation`

- `the reported per-allele sign depends on which allele the dosage counts; the orientation contract
  is incomplete (<missing facts>), so the sign is uncertified.` The dosage/effect orientation cannot
  be selected, so no sign comparison ran.
- `the effect-allele orientation footprint is unresolved (<reason>); no sign verdict is asserted.`
  The check explicitly asserts no verdict because the transform cannot be resolved.

### `confounding`

- `a covariate (<name>) varies within the sample unit; cannot build a clean factor table`. The
  sample-level design matrix cannot be formed, so aliasing/estimability was not computed.
- `the declared contrast levels are not both present (<reference> vs <test>) — this is a
  configuration error, not a finding about the science`. There is no two-level target to compare.
- `the target has no variation after subsetting (only one level present) — a configuration error,
  not a finding about the science`. The estimability algebra has no varying target.

### `count_model`

- `no reported result found to check against`. There is no report-bound claim to compare.
- `no analysis code was found, so the statistical model cannot be identified — a negative-binomial
  fit and a t-test on log-CPM are indistinguishable from the reported table alone`. The producing
  model cannot be bound from the available input.
- `the code contains both a count model (<methods>) and a non-count test (<tests>); which produced the
  reported table cannot be determined from the source`. The producing model is ambiguous.
- `the statistical model used could not be identified from the code`. No supported producer was
  resolved, so the model comparison did not run.

### `effect_size_threshold`

- `no effect-size column was reported, so effect size could not be assessed`. There are no effects
  to compare to the policy floor.
- `no p-value/adjusted-p column to identify the claimed discoveries`. The claim set cannot be bound.
- `the claimed-significant discoveries have no reported effect size, so effect size could not be
  assessed`. The bound claim rows have no finite effect values.

### `experimental_unit`

- `a covariate (<name>) varies within the sample unit`. The replicate-level recompute cannot form
  one coherent covariate value per aggregate.
- `the contrast (<column>) varies within the sample unit <keys> — aggregation would merge the two
  arms into one sample`. This is the recompute precondition: aggregating would destroy the contrast,
  so this check abstains instead of running nonsense. Any actual merge concern remains owned and
  flagged by `pseudobulk_integrity` when its stronger report-bound preconditions are met.
- `no reported result found to check against`. There are no reported discoveries to compare with
  the replicate-aware recompute.

### `hic_loop_strength`

- `the Hi-C loop-strength estimator contract is incomplete (<missing facts>); the report-bound delta
  is uncertified.` The exact functional cannot be selected.
- `the report-delta tolerance is invalid or unratified; no magnitude verdict is asserted.` The
  report/recompute magnitude comparison has no valid decision tolerance.

### `multiple_testing`

- `no reported result found to check against`. There is no report-bound p-value family.
- `the reported table carries no raw p-values, so the FDR cannot be recomputed`. BH has no inputs.
- `every reported row is significant — the full tested family is absent, so BH cannot be rebuilt`.
  The denominator/family needed for the recompute is missing; this labels this check NOT CHECKED and
  does not call the discoveries conformant.

### `pairing`

- `the pairing relation was not evaluated because the declared key <key> has missing column(s)
  <fields> in .obs; no complete-pair claim is asserted.` The complete declared key is unavailable;
  reducing it would fabricate pair coverage.
- `the duplicated-pairing relation could not be evaluated (<reason>); no blocker is asserted.` The
  functional-dependency proof returned unresolved, so no matching claim was made.

### `pseudobulk_integrity`

- `the ratified aggregation key <key> names column(s) absent from .obs (<fields>); the actual
  pseudobulk grouping cannot be reconstructed, so the merge check did not run.` Reducing the key
  could false-accuse a valid aggregation.
- `the aggregation merge relation could not be evaluated (<reason>); no blocker is asserted.` The
  relational proof did not complete.

The conservative exclusions are equally important. These stay `FLAGGED`: every double-dipping
finding; unconfirmed but measured aliasing/multiple-testing/sign/orientation/Hi-C disagreements;
omitted or ambiguous pairing supported by observed pairs; zero complete pairs; an actually observed
arm merge; normalized `.X`, unresolved count-sink binding, or missing aggregation values in the mixed
`pseudobulk_integrity` concern path; and all earned-verdict outcomes after a recompute, including
incomparable, too-few-replicate, and underpowered/exploratory panels. Those outcomes carry a real
supported concern or combine coverage uncertainty with one, so over-flagging is the safe result.

## Frozen fixture mapping

`tests/test_status_model.py` freezes the complete default status projection, concern-over-coverage
precedence, all four axes, unchanged gating outputs, JSON classification, and all 22 named legacy
confounding fixtures. Their exact old-status -> human-state inventory is:

- `alias_confirmed blocker->flagged`; `paired_crossed pass->clear`;
  `alias_unconfirmed needs_evidence->flagged`; `alias_low_condition needs_evidence->flagged`;
  `alias_low_replicate blocker->flagged`.
- `missing_level needs_evidence->not_checked`; `varying_covariate
  needs_evidence->not_checked`.
- `weak_omitted pass->clear`; `near_adjusted informational->flagged`; `near_omitted
  major->flagged`; `partial_omitted major->flagged`; `partial_adjusted pass->clear`;
  `partial_patsy pass->clear`; `xor_additive pass->clear`; `one_per_cell pass->clear`.
- `unpaired_crossed pass->clear`; `unpaired_no_batch pass->clear`; `donor_in_model
  blocker->flagged`; `single_bridge major->flagged`; `high_cardinality major->flagged`;
  `clean_reverse_contrast pass->clear`; `fixture_confounding_alias blocker->flagged`.

`tests/test_report.py` freezes the Phase-1 bound-claim fixture finding-by-finding:

- `confounding blocker->flagged` (supported complete aliasing).
- `multiple_testing needs_evidence->not_checked` (full family absent; BH did not run).
- `count_model needs_evidence->not_checked` (analysis code absent; producer unidentified).
- `effect_size_threshold pass->clear` (complete reported effect comparison).
- `pairing needs_evidence->flagged` (observed zero complete pairs is a supported concern).

Every other existing fixture is exhaustively covered by the default mapping above unless it enters
one of the exact return branches in the reclassification ledger; focused owner tests freeze each
reachable reclassification family. The legacy dataclass byte oracles remain unchanged.

## Gating differential and verification

No code in `audit.py` changed. `SEVERITY`, `FAIL_ON_DEFAULT`, status assignment/clamping,
`worst_status()`, `ci_fails()`, `ci_conclusion()`, and `fully_audited()` are unchanged. The axis-only
gating test applies deliberately contradictory axis values to all six shipped statuses and proves
identical gating results. The `confounding_alias` acceptance fixture still produces:

```text
worst_status=blocker · ci_fails=True · ci_conclusion=fail · fully_audited=True
```

Initial Phase-2 red command:

```text
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest -q tests/test_status_model.py tests/test_count_model.py tests/test_effect_size.py tests/test_experimental_unit.py tests/test_multiple_testing.py tests/test_pairing.py tests/test_pseudobulk_integrity.py tests/test_confounding.py tests/test_allele_orientation.py tests/test_hic_loop_strength.py
```

It failed at the missing axes, derivation, and coverage annotations as intended. The unrelated
PyDESeq2 failures were the already-documented sandbox denial of
`os.sysconf("SC_SEM_NSEMS_MAX")`.

Focused green commands covered the status/check suite and the report/header/coverage/schema suite.
Final full command:

```text
PYTHONPATH=/tmp/sc-referee-pytest-site UV_CACHE_DIR=/tmp/sc-referee-uv-cache MPLCONFIGDIR=/tmp/sc-referee-mpl uv run pytest
```

Final result: **880 passed, 4 warnings**. The pre-existing `/tmp` `sitecustomize` only supplies the
sandbox-denied macOS semaphore-limit query and is not a repository change.

No analyzed code was executed. No inference-engine file was changed. No git operation was run.
