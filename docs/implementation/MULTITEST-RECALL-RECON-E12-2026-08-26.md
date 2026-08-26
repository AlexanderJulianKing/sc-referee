# MT 2.1 recall recon over the envelope-12 misses (2026-08-26)

Provenance: isolated Opus recon at repo state 5b43cb2, executed-ladder discipline per
FINDINGS-PLAYBOOK.md; every claim is a measured analyzer outcome; repo untouched. Baseline
reproduces blind-envelope-12-2026-08-26/AUDIT_RESULTS.json 15/15.

## Headline
- Four misses diagnosed to exact constructs with executed ladders. P1 = two walls (verdict helper
  called through another helper - the terminal-helper rewrite runs only ONCE, before inlining;
  plus a p-value entering pandas.DataFrame). P3 = family call with no statement-level binding
  (record/loop expansion clones 1 call into 24 syntactic copies, tripping the cardinality guard
  on the analyzer's own artifact). P5 = three stacked walls (nested formatting helper; unfolded
  record-flag branch; corrected-subset positions unprovable through a filtered positional record
  list). P6 = NOT a residual: len(OUTCOMES) as the family size and ast.Set membership are both
  decidable from frozen bytes; with both admitted it becomes a TRUE candidate/strict_subset
  (positions {0,1} of 5).
- Adopted proposals: D6 (run the closed terminal presentation/verdict-helper rewrite a SECOND
  time after helper inlining - no new grammar, pure ordering fix), D2 (statement-level binding
  normalization for family-test calls in sub-expression position - normalization, not admission;
  whole-module census untouched), D5 (closed frozen set literal for membership DECISIONS only -
  never an ordering/iteration source; mutation anywhere abstains), D3 (len(X) = family size only
  when X provably IS the contract outcome table; every other len fails closed).
- Withdrawn after execution: D1 (zero effect anywhere) and D4 (a REAL RECALL REGRESSION: inlining
  formatting helpers manufactured fake decision/correction evidence, costing 1 opened positive
  and 3 corpus catches). Lesson for the playbook: helper INLINING of presentation code creates
  false evidence; the transformer route (D6) is the safe equivalent.
- Six FA fixtures executed: none accuses; two correctly return covered/complete (whole-family
  hand Bonferroni via len; whole-family set) - abstention removed in the SAFE direction.

## Projected oracle (adapter level, to pin in the design)
Opened movements, exactly 3 of 45: E12-P3 -> candidate/none; E12-P5 -> abstain
pvalue-family-collection-unresolved (one wall deeper); E12-P6 -> candidate/strict_subset {0,1}/5.
Corpus: ZERO rows move (all 50 byte-identical). E10/E11 oracles unchanged. Opened floor 12/18 ->
14/18. Post-delta E12 15-row table in the recon transcript.

## Correct-case impact: NONE FLIP
25 corpus-correct 0 candidates; 27 opened negatives 0 candidates, 0 reason changes; 19/25 corpus
misstep catches unchanged; 0 lost anywhere.

## Honest ceiling and residuals
The delta gains zero on the unbiased corpus estimator - it closes four STRUCTURAL holes shown by
fresh authors, worth more than idiom admissions, but the arrival curve still governs; E13
expectation is tempered. Blind window stays 2/18 until future envelopes.
Residuals left open deliberately: (1) p-values entering pandas.DataFrame - the live guard behind
E12-N1/N2; a closed positional record-table model is scopeable but is the largest new accusation
surface on file and must be its own design; (2) corrected-subset selection through a runtime
filter over a positional record list - the identity fact must be slice-proved before a
strict_subset conviction; correction-family-lineage-unresolved is correct until a
positional-record subset model exists; (3) the record-flag branch fold, dominated by (2), bundle
them; (4) zip(record_list, adjusted) write-back appears on both polarities - measure both.
