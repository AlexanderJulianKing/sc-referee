# Experiment 0018: Full GeneBench public-development corpus sweep

- **Status:** Active evaluation-private experiment
- **Date:** 2026-07-29
- **Governing decisions:** Accepted ADR-0017 and ADR-0018
- **Corpus ceiling:** Public development; not held out, qualification eligible, or promotion eligible
- **Public schema change:** None; accepted schema v0.14.0 remains unchanged

## Purpose

Complete the ten-case public GeneBench-Pro development sweep, test the existing isolation, audit,
semantic-lock, grading, and static-probe boundaries on the three remaining workflows, and use the
complete result to choose the next product milestone. The experiment must not treat an answer
mismatch as a Finding, infer production scientific intent from an answer-side report, execute
submitted source during static inspection, or broaden an existing profile to make it fire.

## Isolation and run protocol

The pinned GeneBench-Pro package revision
`8bb6cde6ab0b0554e867c46f5698fd953bf2c68a` passed the existing full-package preflight as
`corpus-preflight:8730beb21ba287b04206`, digest
`sha256:cdec94825fc8801ddb6b8189ddc2595b033c6be09d83249e7d0a76ee70c6d37b`.
The existing preparer created three separate workspaces containing only derived `task.md` plus
declared data:

1. `multiparent_qtl_hmm_lmm`;
2. `crispri_casrx_transcript_vs_locus`; and
3. `popgen_recent_pulse_sexbias`.

The QTL and CRISPR agents independently authored their workflow files inside their assigned
workspaces and reported completing their analyses. The population-genetics agent performed a
fresh-context, read-only derivation but declined the authorized writes under its own safety policy.
The parent controller persisted exactly the source and three result files supplied in that agent's
message by `apply_patch`; neither the parent nor sc-referee executed that submitted source. This
provenance difference prevents treating the three runs as an authenticated, uniform agent panel,
but does not affect the later static-audit or snapshot-grade identities.

sc-referee audited and semantically locked every workspace before answer-side access. Because the
user had not designated a publication surface, each audit conservatively left the choice among
`report.md`, `task.md`, and no selected surface unresolved. Every audit therefore ended
`partial_evidence_unavailable` with zero Findings, zero conditional concerns, one material
publication-surface question, two disclosures, zero model calls, and verified absence of post-lock
model access. All three semantic locks replayed without project execution.

## Closed grader extension

The QTL and CRISPR contracts graded under version `0.3.0`. The first population-genetics grading
attempt failed closed before output because the public `multi_numeric_tolerance` contract supplies
`min_value` without `max_value` for the two generation-time fields. Version `0.4.0` adds only that
exact minimum-only numeric range form to the already supported multi-key absolute-tolerance
profile and advances its comparison-profile identity from `v2` to `v3`. Maximum-only ranges still
fail closed. Single-numeric and composite numeric profiles
retain their previous bound rules, and unknown fields, non-finite values, relative tolerances,
extra or missing answer keys, and changed grader shapes remain unsupported.

Version `0.4.0` also binds the grader version and comparison-profile identity into every new stable
grade ID. Historical records retain their original IDs and bytes; a grade emitted under the new
profile cannot collide with a semantically different earlier record over the same inputs.
Two write-once exploratory population-genetics records emitted while this identity defect was
being diagnosed remain preserved in temporary evaluation storage but are excluded from the frozen
outcome below. Only the version/profile-bound `v3` record is cited.

The adapter still imports and executes neither the package grader nor submitted workflow. It reads
the frozen full-digest `answer.json`, emits value digests rather than ground-truth values, and
marks every grade Finding-, metric-, held-out-, qualification-, and promotion-ineligible.

## Frozen outcomes

| Case | Audit and semantic lock | Grade | Result |
|---|---|---|---|
| `multiparent_qtl_hmm_lmm` | `audit:72211735745f4a1d95aaab0f8d3f548b`; `sha256:d80716fef34228d5bd1c618dabe3e7285db7a0c2963e427fc400459f7ccd4c93` | `genebench-answer-grade:0ccffdd63aba8e88627d`; `sha256:711fe001c5ef4893d391815a3da5b6ab3afbbdbdd705d268aac569986bc271e6` | Reported F4 rather than F5. Position `43.45` differed from `48.635551` by `5.185551` cM against tolerance `3.0`. |
| `crispri_casrx_transcript_vs_locus` | `audit:98f955296357435aa9fbb71fe6f241f1`; `sha256:1cf83cefa2fef1dcad6faf9adabe9c4ba69e74c9437b69f077d0a91d365bd1e5` | `genebench-answer-grade:2e69dd9f4c7a1e129010`; `sha256:a51a36586b51dde54904c10b5ae7bd72bdc33d34b7f4e8f76c85a0e42c21a07a` | Decision code `0` matched. Transcript and neighbor effects missed by `0.081988` and `0.038492` against tolerances `0.01` and `0.03`. |
| `popgen_recent_pulse_sexbias` | `audit:5e868ada290543f2b53a12f560acc669`; `sha256:1a5359d768410b789df03a4670c5dc3b73af01adf3598a25b58c567cba38a825` | `genebench-answer-grade:1377f72c3abc1a4eb16a`; `sha256:686d80c66d22f315830222ca7da045b3f715ad8da49ed472fc319a79cd33ab13` | Both ancestry fractions missed by `0.208585` and `0.159451`; both timing values missed by `0.457706` and `0.791738`. |

These are answer-contract observations only. They do not independently demonstrate a scientific
issue, production obligation, executed method, or root cause.

## Existing-profile recurrence test

After semantic lock, the Experiment 0016 Python-AST probe applied all four unchanged profiles to
each frozen `analysis.py`. All twelve case/profile combinations returned `unsupported_path`:

| Case | Source and diagnostic identities | Existing-profile result |
|---|---|---|
| `multiparent_qtl_hmm_lmm` | source `sha256:f69bd1d1c802de8cc6c8ecc8cadca9bcd962b23ea4b0dc6aee6a130a27431fcf`; probe `evaluation-python-source-method-probe:2c2fce0d8f2f110d40df`; diagnostic `sha256:4e3c0e0da1d5eaf312052fc43d5bb7ec13f217f607dc9d6f524b28a7f9719dcc` | Four `unsupported_path` results. |
| `crispri_casrx_transcript_vs_locus` | source `sha256:d5ce11ea5150b1354139fae7cb99741ec32f446cf3a7ecfeab731f628867b39d`; probe `evaluation-python-source-method-probe:71dc3a64455ba9934cdb`; diagnostic `sha256:8e7c69896440ebe86fc658bfda410d92fad5fad029fcec540eeac0f408e73c22` | Four `unsupported_path` results. |
| `popgen_recent_pulse_sexbias` | source `sha256:cf3284b90c21a7180f0f42c819263dc5143133bd330315fd55c9564f9039ef51`; probe `evaluation-python-source-method-probe:15579bdd397643893532`; diagnostic `sha256:11e9fba3389abe629a917bee2b230614fda4001afbdc2e02bed92449359a7d21` | Four `unsupported_path` results. |

The six workflows in Experiments 0017 and 0018 therefore provide zero recurrence for directional
measurement error, phased-composite construction, mutually exclusive class calibration, or
calibration-before-standardization. That negative result is evidence that the closed probes do not
act as generic wrong-answer detectors.

## Answer-side method adjudication

The following comparisons use public-development reference reports only after lock. Those reports
do not establish production intent.

### Multi-parent QTL

The submitted workflow performs an eight-state HMM and batch-adjusted mixed-model scan but never
detects or repairs allele-orientation outliers. Its F4 peak at `43.45` cM nearly reproduces the
public report's explicit no-orientation-correction ablation, F4 at `43.31` cM. The report, digest
`sha256:3e845fb63659a272bc098f2ce3118a9614385e9abe032f7afd409d4901f54dfa`,
identifies two posterior-mismatch outliers, reruns the HMM after correction, and recovers F5 at
`48.635551` cM. This is strong fixed-case answer-side evidence for omitted orientation repair, not
a production Finding or recurring profile.

### CRISPRi/CasRx transcript-versus-locus decomposition

The submitted source estimates the transcript effect from four high-overlap CasRx guides with one
through-origin slope and estimates the neighbor effect from a thresholded local subset using a
robust one-axis slope after subtracting that transcript estimate. It does not implement the public
report's complete pooled guide model with swap residual QC, GC excess, promoter-core status, and
joint measured LINC473/KIN1 knockdown; nor does it implement the two-axis dominant/non-dominant
CasRx model with bridge-derived per-plate offsets. The report, digest
`sha256:a0a0e124d546c9cd6667246ed98e4c2fcaeed8df914b6cb90bdc28a205d50e83`,
contains separate answer-changing ablations for these decisions. The submission differs at several
stages and no single public ablation reproduces both submitted values, so the experiment records a
compound method incompatibility without assigning sole numeric causality.

### Parent-specific recent-pulse ancestry

The submitted source removes low-confidence micro-tracts but never harmonizes the inverted chr3
A/B labels. Its reported ancestry fractions, `0.481968` and `0.565344`, reproduce the public
report's `0.4820` and `0.5653` filtering-without-chr3-correction basin. It then converts switch
counts with called ancestry exposure rather than the full `11.6` Morgan map length. The report,
digest `sha256:2b7283d929470bb7e102e15aa14121d444677c370faadfca5af9e8bb4b25093c`,
documents both omissions as answer-changing and gives a target-equivalent cleanup that retains chr3
correction and the full-map denominator. This is strong fixed-case compound evidence, not a
production Finding or a demonstrated reusable code grammar.

## Ten-case synthesis

| Case | Grade outcome | Bounded localization status |
|---|---|---|
| `hic_sv_masked_loop_strength` | All three fields outside tolerance. | Pre-answer audit asked which expected-count background governs; separate post-lock diagnostic localized the public reference conflict. |
| `wf_selection` | Locus matched; coefficient outside tolerance. | Exact static symmetric-error conflict; fixed-case directional repair recovered the answer. |
| `carrier_cnv_pseudogene_residual_risk` | Two fields matched; three outside tolerance. | Three exact static conflicts; complete fixed-case repair recovered all five fields. |
| `statgen_cis_mvmr_winnerscurse_scaling_ldaware` | Both fields within tolerance. | Covered-good public-development control; no issue inferred from method wording differences. |
| `statgen_scrna_ambient_state_eqtl` | Sole field outside tolerance. | Existing probes unsupported; public reference ablation closely reproduced an omitted recoverable group adjustment. |
| `structural_inversion_subhap_expression_risk` | Two fields matched; count and clinical estimate missed. | Existing probes unsupported; strict QC explains the count miss, while sole causality for the clinical miss remains unestablished. |
| `txr1_mtb_causal_sv` | Decision code matched; three numeric fields missed. | Existing probes unsupported; several target-reconstruction and assessment-weighting differences remain compound. |
| `multiparent_qtl_hmm_lmm` | Both fields missed. | Existing probes unsupported; no-orientation-correction ablation closely reproduces the submitted peak. |
| `crispri_casrx_transcript_vs_locus` | Decision code matched; two numeric fields missed. | Existing probes unsupported; multi-stage pooled/CasRx method incompatibility, without one isolated numeric cause. |
| `popgen_recent_pulse_sexbias` | All four fields missed. | Existing probes unsupported; no chr3 harmonization and called-span timing denominator are directly visible. |

One of ten workflows was wholly within its public answer contract. Nine missed at least one field.
The first three failure investigations demonstrate that exact, closed localization can work, while
the six later failed workflows supply six different answer-side method families and no recurrence
for the existing profiles. Production audits appropriately emitted no Findings without governing
intent and supported implementation premises, but that also means ordinary contract-free audits
did not explain these wrong answers. The corpus is public and may be contaminated in model
training; these counts are development diagnostics, not estimates of product accuracy.

## Product decision and next milestone

Do not add one detector per failed case. The full sweep provides stronger evidence for an
interactive post-hoc review workflow:

1. keep `scientific-audit` as the primary path for an existing analysis and keep the separate
   pre-analysis `method-contract` skill optional;
2. derive a partial method ledger from exact repository evidence, then let the present scientist
   answer only bounded unresolved questions before semantic lock;
3. separate model proposals, scope-bound scientist Answers, repository evidence, and deterministic
   controller verification rather than letting any one plane silently stand in for another;
4. compare only exact values, finite sets, and named step order under closed parsers, preserving
   every unsupported implementation path or unanswered question as unknown;
5. validate by re-auditing the existing QTL, CRISPRi/CasRx, and pulse-admixture workspaces plus
   unknown, conflict, false-self-compliance, and covered-good controls before adding a production
   detector or capability claim; and
6. add notebook, R, or further source support only when those post-hoc reviews expose a concrete
   evidence bottleneck.

This milestone can tell the scientist that the selected report or supported source conflicts with
the requirement they supplied for the current review. It cannot turn a retrospective Answer into
proof of historical intent, execution, numerical truth, or universal scientific correctness. That
limit must remain visible in the skill and product language.

A durable post-hoc ledger, its authority rules, and its agent interaction behavior change public
capability meaning and therefore require a proposed ADR before implementation. The initial proposal
should reuse v0.14.0 without a schema release unless a concrete dimension cannot be represented
without overloading.

## Acceptance evidence

- **Change:** evaluation grader version `0.4.0` adds only minimum-only range metadata in the exact
  multi-key absolute-tolerance profile encountered after lock.
- **Test:**
  `test_genebench_numeric_grader_accepts_minimum_only_range_and_rejects_maximum_only` covers the
  accepted form, canonical range output, version/profile-bound stable identity, and fail-closed
  maximum-only mutation; the existing grader suite retains all prior profile-broadening and
  non-execution checks.
- **Acceptance criterion satisfied:** all ten public cases have completed an answer-isolated,
  post-lock grading path; all three final audits replay; all twelve final existing-profile checks
  abstain on unrelated source; and the complete evidence supports an explicit next-milestone
  decision without changing schema, Findings, detector manifests, or capability claims.
- **Remaining coverage limitation:** the agents are unauthenticated public-development runners;
  the population-genetics workspace has parent-persisted agent content rather than an agent write;
  publication surfaces were unresolved; none of the final three methods has a single-change
  evaluator-owned repair run; no new family has independent recurrence; and no authenticated
  held-out reviewer panel or promoted detector exists.
