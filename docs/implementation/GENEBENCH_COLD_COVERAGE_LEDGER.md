# GeneBench cold-workflow coverage ledger

- **Status:** Development ledger required by ADR-0020; all ten cases populated
- **Updated:** 2026-08-03
- **Authority:** Evaluation only. This ledger cannot emit or qualify production Findings.

## State definitions

- `absent`: no relevant installed scientific-check family exists.
- `unsupported`: a relevant family exists, but the bounded evidence or scope did not close.
- `applicable`: one exact observed operand is recognized; the governing requirement is unresolved.
- `checked`: an external human or evaluation contract was compared with the operand. The outcome
  must be reported separately as compatible, incompatible, or unresolved.

Answer grade and recognition coverage are separate. `outside_contract` does not prove a scientific
error or its cause. `applicable` means the auditor can ask the right bounded question, not that it
has accused the workflow.

## Wave 1

| Case | Public grade | Relevant check | State | Audit result |
|---|---|---|---|---|
| `multiparent_qtl_hmm_lmm` | outside contract | founder orientation before HMM emission | applicable | direct founder input localized; high-priority requirement question |
| `wf_selection` | within contract | directional measurement-error interpretation | applicable | two distinct directional rates localized; requirement question, no adverse conclusion |
| `carrier_cnv_pseudogene_residual_risk` | outside contract | poststratified misclassification estimator | applicable | standardize-then-calibrate order localized; high-priority requirement question |
| `hic_sv_masked_loop_strength` | outside contract | expected-count construction and focal-target handling | applicable | same-diagonal arithmetic background and focal omission localized as two independent questions |
| `statgen_scrna_ambient_state_eqtl` | outside contract | recoverable technical-group covariate | checked / incompatible | observed omission conflicts with the external evaluation requirement to include the recovered technical group; evaluation-only exact-conflict Disclosure, no Finding |
| `statgen_cis_mvmr_winnerscurse_scaling_ldaware` | within contract | phase split, covariance, heterogeneity, and LD treatment | unsupported in this Python/report layout | no relevant adverse conclusion; a general output-scope question remained |

## Wave 2

| Case | Public grade | Relevant check | State | Audit result |
|---|---|---|---|---|
| `structural_inversion_subhap_expression_risk` | outside contract | classifier-derived copy-dosage representation | checked / incompatible | posterior expected copy dosage conflicts with the evaluation requirement for direct continuous copy calibration; exact-conflict Disclosure, no Finding |
| `txr1_mtb_causal_sv` | outside contract | somatic clonality representation; post-treatment missingness strategy | checked / incompatible for clonality; applicable for missingness | direct molecule-fraction/local-copy gate conflicts with the evaluation requirement for purity/copy-adjusted clonality; sequential post-treatment endpoint integration is independently localized and unresolved |
| `crispri_casrx_transcript_vs_locus` | outside contract | local-perturbation primary row scope and regression specification | checked / incompatible for regression; applicable for row scope | external target subtraction followed by one remaining axis conflicts with the evaluation requirement for a joint nuisance-adjusted local model; nominal focal-row restriction is independently localized |
| `popgen_recent_pulse_sexbias` | outside contract | full-map ancestry exposure; within-sequence path continuity | checked / incompatible for exposure; applicable for path continuity | called-path exposure conflicts with the evaluation requirement for full chromosome-map exposure; exact hidden-gap integration is independently localized |

## Current bounded conclusion

All eight grade-mismatching cold workflows now reach at least one relevant scientific question.
Five have an evaluation-only exact incompatibility after an external contract was supplied. One of
two within-contract controls also reaches a relevant unresolved question; the other has no relevant
question in its current Python/report layout. Zero production Findings were emitted.

Therefore the honest current claim is **eight-of-eight relevant-question localization on this
public-development corpus**, not eight-of-eight error detection and not general workflow coverage.
The population-genetics workflow's chromosome-local label inversion remains absent from automatic
coverage even though its full-map exposure mismatch is checked.
