# Experiment 0046: Bounded gzip inputs for deterministic calculations

- **Status:** Completed
- **Date:** 2026-08-02
- **Decision:** Accepted ADR-0055 under the owner's standing authorization
- **Schema:** Unchanged at `0.18.0`
- **Backlog item:** Third tranche of L10

## Question

Can exact gzip-compressed CSV and TSV summaries feed all existing table-consuming deterministic
calculation families with the same normalized scientific result as uncompressed inputs, while
remaining bounded, replayable, non-executing, and fail-closed?

## Design

The calculation-context builder completely streams exact snapshot `.csv.gz` and `.tsv.gz` bytes
through the shared auditor-owned reader. It enforces 64 KiB chunks, an 8 MiB per-input decoded
content ceiling plus a sentinel byte, and a 64 MiB aggregate logical-read ceiling. It caches one
decoded view per exact path and physical digest. The physical and decoded identities, measured
reads, ceilings, and termination state are locked in deterministic receipts.

All seven table-consuming adapters use one shared decoded-table boundary. Their existing
scientific contracts and normalized calculation cores are unchanged.

## Tests added or extended

- paired identity/gzip sidecar cases in
  `test_bh_sidecar_layout_uses_same_calculation_with_alternate_paths_and_columns`,
  `test_selected_sidecar_layout_normalizes_to_same_design_metrics`,
  `test_selected_sidecar_layout_normalizes_to_same_effect_summary`,
  `test_selected_sidecar_layout_normalizes_to_same_eqtl_sign_recompute`,
  `test_selected_sidecar_layout_normalizes_to_same_hic_recompute`,
  `test_selected_sidecar_layout_normalizes_to_same_selection_reuse_pattern`, and
  `test_selected_sidecar_layout_normalizes_to_same_sensitivity_recompute`;
- `test_bh_compressed_table_failures_are_localized_without_findings` covers malformed gzip, an
  8 MiB decoded compression bomb, and strict UTF-8 failure;
- `test_selected_compressed_table_is_decoded_once_under_aggregate_budget` covers deduplication and
  deterministic aggregate-budget exhaustion;
- `test_compressed_calculation_reader_propagates_cancellation_between_chunks` covers cancellation;
  and
- the gzip BH case covers locked receipts, live mutation, replay, and a project-code execution
  trap. All existing L09 and L10 controls remain active.

## Acceptance criterion targeted

This tranche targets complete bounded gzip-table input for L09, deterministic measured receipts,
localized over-budget and malformed coverage, cross-family equivalence, cancellation, immutable
replay, and unchanged scientific authority.

## Result

All targeted controls pass. The full checkpoint passes 1,391 tests, Ruff, formatting, strict
typing for 111 production and 28 evaluation files, starter/schema validation, the 121-case
regression ledger with all 26 module baselines, and the complete clean-wheel handoff verifier.
The public schema remains 0.18.0, all affected calculations remain Disclosure-only, and no
project-authored code or model is invoked.

## Remaining limitation

This experiment does not support other compression formats, Parquet/Arrow, Zarr, summaries above
the declared decoded budgets, or any new scientific calculation or Finding authority.
