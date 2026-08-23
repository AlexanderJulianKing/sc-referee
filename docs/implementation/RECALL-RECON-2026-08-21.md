# Recall reconnaissance — 2026-08-21

## Scope, snapshot, and evidence discipline

This is a read-only reconnaissance memo except for this new file. I did not execute project-authored
code, run a builder, alter a detector, or inspect or modify the quarantined Slice-C files. The governing
standard is that a `Finding` is a demonstrated issue and must pass direct-entailment, applicability,
counterevidence, bounded-wording, and replay gates; unknown, conditional, and opaque cases are not
Findings (`AGENTS.md:20-28`). The production MPP does not execute project-authored code
(`AGENTS.md:41-43`).

Evidence labels used below:

- **Observed** — directly established from tracked source, records, or the required repository checks.
- **Inference** — a reasoned conclusion from those observations, not directly measured.
- **Needs verification** — a counterfactual, prevalence claim, or proposed behavior that needs a new
  controlled measurement or design review.

**Observed repository snapshot.** `git rev-parse --show-toplevel` returned
`/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext`. The branch was
`dev/dependence-growth` at `b64be791a0f9139702ade8c268023e1650ca3400`. The required
`git status --short | wc -l` returned **4** because Git collapses untracked directories by default.
Expanded status showed one tracked modification, the already-modified
`docs/implementation/GROWTH-LOOP-STATE.md`, plus exactly 25 authorized untracked Slice-C files and
zero staged paths. The state file independently records the same HEAD, one tracked STATE modification,
25 untracked paths, and zero staged paths (`docs/implementation/GROWTH-LOOP-STATE.md:2791-2798`),
then repeats that the 25 paths remain untracked (`docs/implementation/GROWTH-LOOP-STATE.md:2873-2879`).

**Bottom line.** **Observed:** the lifetime blind record is 108 cases, 107 measurable, zero false
accusations, and zero blind catches (`docs/implementation/GROWTH-LOOP-STATE.md:43-47`). There are two
installed production promotion pins, not a general production detector. One pin, complete-domain
exposure, is reachable using the public CLI inputs. The dependence pin is wired into the shared audit
controller, but its required unit-key authorization enters through controller-only parameters absent
from the `audit` CLI. Everything else is question-, disclosure-, conditional-, demo-, or evaluation-only.
Perfect measured precision therefore does not demonstrate useful recognition.

## 1. Recognizer and detector inventory

### 1.1 What the normal `audit` path schedules

**Observed.** The Typer `audit` command accepts a report, method-contract lock, and up to eight selected
material inputs, then calls `run_audit`; it does not expose dependence-authorization lock or case-id
options (`src/sc_referee/cli.py:682-734`). `run_audit` installs the default scientific- and
calculation-check registries (`src/sc_referee/controller.py:667-720`), evaluates them against a frozen
inspection context (`src/sc_referee/controller.py:1060-1148`), and binds a supplied method-contract lock
to applicable questions (`src/sc_referee/controller.py:1215-1233`). The normal detector dispatcher then
runs registered method conflicts plus three specialized experimental detectors
(`src/sc_referee/controller.py:3459-3527`).

The practical inventory is:

| Component | Implemented and normal-audit wired? | Highest output it can actually produce today | What it can convict |
|---|---:|---|---|
| `detector:bounded-analysis-method-conflict` | Yes | Production `Finding`, but only after an exact installed pin resolves | Exactly two pinned method-declaration conflicts described below; no generic scientific error |
| `detector:bounded-report-mean-direction` | Yes | `evaluation_finding_candidate` | Nothing in production; it can flag an explicit report direction opposed to an exact linked raw mean difference (`src/sc_referee/detectors/bounded_report_mean_direction.py:18-32`, `:325-347`) |
| `detector:bounded-reported-method-contract-conflict` | Yes | `evaluation_finding_candidate` | Nothing in production; it can compare one closed reported expected-count method with one verified governing profile (`src/sc_referee/detectors/bounded_reported_method_contract.py:25-44`, `:300-318`) |
| `detector:bounded-feature-identifier-identity` | Yes | `evaluation_finding_candidate` | Nothing in production; it can state an exact mismatch between two complete, unique identifier sets under a human equality requirement (`src/sc_referee/detectors/feature_identifier_identity.py:22-37`, `:338-379`) |
| 23 default scientific-check modules | Yes | Normally `MaterialQuestion`; two exact bindings can be promoted after conflict evaluation | Only the two pin scopes below |
| 10 default calculation-check modules | Yes | Nine `Disclosure`; feature identity may reach an evaluation candidate | Nothing in production |

The generic conflict detector itself is experimental and emits only an evaluation candidate when the
human-required operand and binding-complete observed operand differ after ten closed checks
(`src/sc_referee/detectors/bounded_analysis_method_conflict.py:22-43`, `:255-370`). Promotion is a
separate controller step: it requires an installed exact pin, matching qualification evidence and
manifest, then re-runs Finding admission (`src/sc_referee/controller.py:3530-3594`). Admission rejects
anything with unresolved premises, unsupported constructs, gaps, unavailable evidence, incomplete
counterevidence, unresolved source references, or digest drift (`src/sc_referee/detectors/admission.py:22-41`,
`:44-131`).

### 1.2 The two exact production pins

**Observed.** The controller's closed `GRANT_PINS` table contains exactly two entries
(`src/sc_referee/detectors/method_conflict_grant_pins.py:43-138`):

1. `check:complete-domain-exposure-denominator` v2.0.7. It can convict only this bounded declaration
   conflict: the selected rate or spacing uses retained-observed-subset exposure while the pre-analysis
   human requirement selects complete-declared-domain exposure, or the exact reverse. The profile
   expressly refuses to infer the governing domain and requires scientist-supplied authority
   (`src/sc_referee/scientific_checks/profiles.py:1277-1338`). This is **public-CLI reachable**: the
   CLI exposes every input used by the audited controller call, and the retained installed-grant
   end-to-end test encodes one expected Finding plus replay equality using only `report` and
   `method_contract_lock`
   (`tests/test_installed_method_conflict_grants.py:201-233`).

2. `check:authorized-independent-unit-entry-into-row-independent-procedure` v1.1.0. It can convict
   only this bounded declaration conflict: an authorized independent-unit key has multiple analyzed
   rows entering a certified row-independent registered procedure and selected result sink while the
   pre-analysis human requirement selects one analyzed row per authorized unit. The required roles are
   unit key, complete row domain, procedure call, and selected sink
   (`src/sc_referee/scientific_checks/dependence_recognition_adapter.py:42-65`). The check wrapper is
   question-only and never itself emits a Finding (`src/sc_referee/scientific_checks/dependence_recognition_adapter.py:1-8`,
   `:92-122`). This pin is **controller-wired but not public-CLI complete**. The retained production
   demonstration calls `run_audit` with both public inputs and the additional
   `dependence_authorization_lock`/`dependence_authorization_case_id` arguments
   (`evaluation/src/sc_referee_evaluation/production_finding_demonstration.py:300-334`); those two
   arguments exist on `run_audit` (`src/sc_referee/controller.py:667-685`) but not on the CLI command.

**Inference.** Calling both pins “live” is correct at the controller/admission layer, but calling both
end-user CLI capabilities would overstate the present surface. **Needs verification:** an end-to-end
subprocess invocation, using only documented CLI options, should be added to the capability evidence if
the dependence pin is ever claimed as user-facing.

### 1.3 Scientific checks that are wired but cannot convict

**Observed.** The release builds 20 report profiles, MVMR covariance, dependence recognition,
multiple-testing recognition, and a removable conformance module; the default registry removes the
last, leaving 23 (`src/sc_referee/scientific_checks/profiles.py:145-175`, `:217-249`). `_module` assigns
the substantive modules `maturity_tier="question_only"` (`src/sc_referee/scientific_checks/profiles.py:412-430`).
Every substantive module receives a method-conflict binding, but a binding without one of the two
installed pins cannot be promoted.

For completeness, the 23 normal modules are:

- expected-count background construction — question only, no pin;
- expected-count focal-target handling — question only, no pin;
- founder orientation before HMM emission — question only, no pin;
- directional measurement-error interpretation — question only, no pin;
- within-sequence transition-path continuity — question only, no pin;
- full-map ancestry exposure — question only, no pin;
- **complete-domain exposure denominator — question producer plus installed promotion pin**;
- phase-split MVMR instrument construction — question only, no pin;
- MVMR residual-heterogeneity estimator — question only, no pin;
- LD covariance whitening before robust fit — question only, no pin;
- poststratified misclassification estimator — question only, no pin;
- post-treatment missingness strategy — question only, no pin;
- somatic clonality representation — question only, no pin;
- direct-standardization conditioning set — question only, no pin;
- classifier-derived copy-dosage representation — question only, no pin;
- recoverable technical-group adjustment — question only, no pin;
- CasRx isoform-axis model — question only, no pin;
- paired-bridge location alignment — question only, no pin;
- local-perturbation primary-row scope — question only, no pin;
- local-perturbation regression specification — question only, no pin;
- MVMR cross-exposure covariance — question only, no pin;
- **authorized independent-unit entry into a row-independent procedure — question producer plus
  installed promotion pin, with the CLI authority limitation above**;
- complete-family correction over a performed test battery — question only, no pin.

The multiple-testing module is especially relevant to recall. It already defines the exact roles
`authorized_test_family`, `performed_test_battery`, `multiplicity_correction_call`, and
`selected_result_sink`, and maps a strict-subset correction to an observed conflict, but its registered
output ceiling remains question-only (`src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py:42-69`,
`:91-121`). It therefore cannot convict a multiple-testing omission today.

### 1.4 Calculation checks that are wired but cannot convict

**Observed.** The default registry installs BH conformance, single-cell replicate sensitivity,
effect-size relevance, tabular design integrity, R count-model compatibility, Scanpy selection reuse,
donor eQTL sign, Hi-C loop strength, sequence-record boundary, and feature-identifier identity
(`src/sc_referee/calculation_checks/profiles.py:157-209`, `:251-319`). The BH manifest is
`disclosure_only` (`src/sc_referee/calculation_checks/profiles.py:157-170`); count model, design
integrity, effect size, eQTL sign, Hi-C, selection reuse, sequence boundary, and single-cell sensitivity
also declare `disclosure_only` at, respectively,
`src/sc_referee/calculation_checks/count_model_compatibility.py:321`,
`design_integrity.py:357`, `effect_size_summary.py:331`, `eqtl_sign.py:341`,
`hic_loop_strength.py:386`, `selection_reuse.py:373`, `sequence_record_boundary.py:261`, and
`single_cell_sensitivity.py:538`. Feature-identifier identity reaches only `evaluation_candidate`
(`src/sc_referee/calculation_checks/feature_identifier_identity.py:318`). **Actual convictions: none.**

### 1.5 Implemented but unreachable from normal audit, and designed-only names

**Observed — implemented but unreachable from normal `audit`:**

- `DependenceRecognitionV2ShadowAdapter` and its large analyzer are explicitly “unregistered
  development-only,” report-only, and production-Finding-disabled
  (`src/sc_referee/dependence_recognition_v2/adapter.py:1-18`, `:51-76`). There are no imports of this
  package from outside `src/sc_referee/dependence_recognition_v2`; evaluation code invokes it directly.
- `ClaimResultDirectionDetector` and `SampleUnitDependenceQuestionDetector` run in `_derive_from_lock`,
  the walking-skeleton `demo` path, not `_evaluate_general_detectors`
  (`src/sc_referee/controller.py:4187-4234`). The former is a fixture-bound direction detector
  (`src/sc_referee/detectors/claim_result_agreement.py:14-27`); the latter intentionally leaves the
  meaning of repeated `sample_id` unresolved and emits at most a conditional concern
  (`src/sc_referee/detectors/sample_unit_dependence.py:9-36`). The CLI exposes `demo` as a separate
  command (`src/sc_referee/cli.py:746-761`).

**Observed — designed/coverage names only:** `detector:population-comparison-estimand`,
`detector:denominator-control-set`, `detector:explicit-dependence`, and
`detector:lineage-completeness` are inserted into coverage accounting
(`src/sc_referee/controller.py:3922-3937`) but have no detector implementation or normal dispatcher
entry. **Inference:** these are placeholders, not latent recognizers. The only other source occurrence is
lineage-completeness in reproduction metadata (`src/sc_referee/reproduction.py:366`).

## 2. Planted positives and the observations that are missing

### 2.1 The six honest Batch-K misses, ranked by closeness to a bounded catch

All six labels are dependence positives. Their frozen detector ledgers report zero production Findings,
zero false accusations, and the six named terminal walls
(`docs/implementation/GROWTH-LOOP-STATE.md:548-565`). In every case, the production check lacked one
accepted, scope-joined observation containing all four dependence roles: authoritative unit key,
complete analyzed-row domain, row-independent procedure, and selected result sink. The projects contain
strong raw evidence; the recognizer did not certify the join.

The ranking below is an **inference** about the smallest plausible verifier, not a completion claim.
The tree already disproves “remove the first wall and the case completes”: reader-only substitution
exposed a second wall in every measured recurrence (`docs/implementation/GROWTH-LOOP-STATE.md:2464-2475`).

| Rank | Blind positive | What is directly present | Exact observation the tool lacked | Static feasibility without project execution |
|---:|---|---|---|---|
| 1 | K2 `556f3545bebb45a3b005` | Five fish contribute four rows; `fish_tag` is declared the independent unit (`evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/556f3545bebb45a3b005/data-description.md:3-7`, `:27-29`). `binomtest(count_hits(rows), len(rows))` pools all rows (`evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/556f3545bebb45a3b005/workflow/analysis.py:81-86`), and the report explicitly says all 20 rows were pooled as independent with no grouping (`evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/556f3545bebb45a3b005/results/report.md:17-24`, `:32`). | A certified row-domain/procedure/sink join. V2 stopped at `augmented-assignment-not-modeled`, caused by report construction `lines += [...]` (`evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/556f3545bebb45a3b005/workflow/analysis.py:56-77`), not by the binomial operands. | **Feasible:** exact AST relevance slicing plus full CSV multiplicity plus literal report text. **Needs verification:** ignoring or normalizing the report-list augmentation must be proven non-interfering with selected-sink identity. |
| 2 | K1 `e9e2718573bb47f7d17b` | Twelve colonies contribute four nubbins and `colony_id` is the unit (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/e9e2718573bb47f7d17b/data-description.md:3-13`, `:17-32`). All nubbin values feed `stats.ttest_ind` (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/e9e2718573bb47f7d17b/workflow/analysis.py:23-30`, `:49-58`); the report says every nubbin is one observation (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/e9e2718573bb47f7d17b/results/report.md:3-8`). | The same four-role certificate. V2 rejected the multi-return p-label helper (`function-return-shape`); the analyzer refuses more than one return or a non-final return (`src/sc_referee/dependence_recognition_v2/python_analyzer.py:3722-3733`). | **Feasible:** bounded AST handling of a pure formatting helper, CSV multiplicity, and report text. **Needs verification:** secondary walls and exact writer composition. |
| 3 | K2 `3ae92d0bb421d6eee99e` | Twelve plots contribute five readings and `plot_id` is the unit (`evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/3ae92d0bb421d6eee99e/data-description.md:3-13`, `:17-30`). Pooled row values feed `ttest_ind`, and the selected result says “60 individual chamber readings” (`evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/3ae92d0bb421d6eee99e/workflow/analysis.py:45-64`; `evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/3ae92d0bb421d6eee99e/results/report.md:13-18`). | The same certificate; V2 stopped on the two-return `p_phrase` formatter (`evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/3ae92d0bb421d6eee99e/workflow/analysis.py:39-42`). | **Feasible** by the same bounded report/AST/CSV route; secondary-wall verification required. |
| 4 | K2 `2c458d2b523ea8c1bd90` | Twenty windows from six gearboxes, with `gearbox_id` as unit (`evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/2c458d2b523ea8c1bd90/data-description.md:3-12`, `:16-24`). `reader = csv.DictReader(handle); return list(reader)` feeds a row-count binomial test (`evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/2c458d2b523ea8c1bd90/workflow/analysis.py:20-23`, `:32-38`), and the report explicitly calls every window independent (`evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/2c458d2b523ea8c1bd90/results/report.md:10-19`, `:28`). | The same certificate; V2 stopped at `reader-form-unsupported`. Its reader recognizer requires one closed direct assignment/alias chain (`src/sc_referee/dependence_recognition_v2/python_analyzer.py:4160-4209`). | **Feasible**, but ranked lower because reader-only unmasking is already known to reveal another wall in every measured case; this exact case's secondary wall needs verification. |
| 5 | K1 `6b2da0c7167dbba3738f` | Ten reactors contribute six rows and `reactor_id` is the unit (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/6b2da0c7167dbba3738f/data-description.md:3-9`, `:20-21`). All measurements feed Welch `ttest_ind`; the report says each sampling-day measurement is an observation (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/6b2da0c7167dbba3738f/workflow/analysis.py:36-54`; `evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/6b2da0c7167dbba3738f/results/report.md:15-27`). | The same certificate; V2 stopped at the multi-name `from collections import Counter, defaultdict`, where `Counter` is outside the closed import grammar (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/6b2da0c7167dbba3738f/workflow/analysis.py:8-13`; `src/sc_referee/dependence_recognition_v2/python_analyzer.py:3200-3233`). | **Feasible**, but the ancillary `Counter` tally also uses augmented assignment and likely masks further walls. Verify counterfactual completion before design. |
| 6 | K1 `0de3a6061d3bb4056306` | Ten plots contribute four rows and `plot_id` is the unit (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/0de3a6061d3bb4056306/data-description.md:3-14`). Grouped row values feed `ttest_ind`; the report says all 40 rows enter as observations (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/0de3a6061d3bb4056306/workflow/analysis.py:49-58`, `:85-91`; `evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/0de3a6061d3bb4056306/results/report.md:7-20`). | The same certificate; V2 stopped at `import-use-outside-grammar`, including `math.fsum`, while its closed math use permits only `sqrt`/`isnan` (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/0de3a6061d3bb4056306/workflow/analysis.py:35-40`; `src/sc_referee/dependence_recognition_v2/python_analyzer.py:3338-3360`). | **Feasible**, but the statistics/report construction is the broadest of the six. Multiple secondary walls are plausible and need verification. |

**Observed strategic fact:** the two binomial reports explicitly call their pooled row-level trials
“independent.” The four `ttest_ind` reports make a narrower literal declaration: rows or measurements
entered “as one observation,” a record “contributed one observation,” or the test used “60 individual
chamber readings.” A focused report-text observation joined to a full selected CSV and external unit-key
authority could establish a much smaller static predicate than extending the v2 whole-program grammar.
Repository prose may support evidence and quotation, but cannot itself mint the unit authority; the
standing state says precisely that (`docs/implementation/GROWTH-LOOP-STATE.md:99-104`).

### 2.2 Full blind planted-positive inventory, including K

The corpus has 54 positive labels / 53 materialized positives (`docs/implementation/GROWTH-LOOP-STATE.md:566-569`).
Below, `U(reason)` means the tool lacked a complete certified static-source observation because the named
grammar wall terminated analysis; `A` means accepted independent-unit authority was unresolved at the
comparison boundary; `B` means the case was burned before detector measurement, so no honest technical
missing observation can be attributed; and `I` means intake refused and no project was materialized.
`A+U` records both facts when the frozen ledger reports `missed_no_authority` and a v2 wall. Each listed
materialized case is, in principle, inspectable using static Python AST, full CSV rows, and report text;
the current recognizer simply failed to produce the four-role certificate. Burned and intake-refused
cases require a new non-qualification retrospective inspection before feasibility can be claimed.

| Batch | Positive cases and exact frozen terminal observation |
|---|---|
| A | `6da5419523f5f9dbedf9` — U(`dependence-shadow-abstention`; no v2 reason retained); `76373b4a2b2f380d43da` — B; `d1d4ed0e518ad533a2dc` — U(same). Source: `evaluation/development/dependence-growth-loop/batch-a/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| B | `3c2b93c9545d8518e1f3` — U(`unsupported-import-form`); `446cab155cd792398f9d` — A; `ae04f2973df030f612b9` — A. Source: `evaluation/development/dependence-growth-loop/batch-b/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| C | `5eeb6e5adc4fc675c771` — B; `b98cd6e8d9f893450053` — U(`function-multiple-call-sites`, `report-composition-not-modeled`, `unsupported-import-form`); `d674ebb8c31ed83be287` — U(`function-multiple-call-sites`, `import-use-outside-grammar`, `report-composition-not-modeled`). Source: `evaluation/development/dependence-growth-loop/batch-c/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| D | `396f4dceee2b19f08009` — U(`unsupported-import-form`); `6e47ef090eb8989d547d` — B; `dc2b31d5da33d148736a` — I. Source: `evaluation/development/dependence-growth-loop/batch-d/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| E1 | `47b6fb6bf1d4fbcefd7c` — U(`import-use-outside-grammar`); `7afb4508b0d957f51ca7` — U(`module-constant-not-closed`); `d3f093e9da995ca1027a` — B. Source: `evaluation/development/dependence-growth-loop/batch-e1/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| E2 | `128c2bd7128bc67b5964` — A+U(`count-predicate-not-closed`, `function-entry-not-closed`, `function-globals-read`); `18f0af8326d59d579c43` — B; `fa5259eb594c121b4dac` — A+U(`count-predicate-not-closed`, `function-entry-not-closed`). Source: `evaluation/development/dependence-growth-loop/batch-e2/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| F1 | `99fa42046e8fc8cc47de` — U(`function-return-shape`); `9d4a9dcdc2ab130e6736` — U(`unsupported-import-form`); `ca3125c6ca6002055d70` — A+U(`count-predicate-not-closed`, `unsupported-import-form`). Source: `evaluation/development/dependence-growth-loop/batch-f1/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| F2 | `b511aff6f2e4b54ee5ce` — A+U(`unsupported-import-form`); `d288f3b6bbda69d32acf` — U(`unsupported-import-form`); `e0b267c13e8a30d07b48` — B. Source: `evaluation/development/dependence-growth-loop/batch-f2/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| G1 | `30108f0d34292b11cab8` — A+U(`function-argument-not-simple`); `8b55946a92793ebcd387` — U(`function-globals-read`, `function-return-shape`); `aec630c60b86af0d2a96` — A+U(`count-predicate-not-closed`, `module-constant-not-closed`). Source: `evaluation/development/dependence-growth-loop/batch-g1/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| G2 | `a8b660a9685f13f0187f` — U(`function-globals-read`); `ae33434a6064f4251cbc` — U(`import-use-outside-grammar`); `ff99e13110aad17a7fd0` — U(`sink-helper-call`). Source: `evaluation/development/dependence-growth-loop/batch-g2/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| H1 | `46f08f48dfee5b1142a4` — A+U(`unsupported-import-form`); `a7abfa9adc44baaea6d6` — A; `d8e451762e6f79802f9f` — A+U(`function-globals-read`, `sink-helper-call`). Source: `evaluation/development/dependence-growth-loop/batch-h1/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| H2 | `2c76f6934e057bc62ce3` — B; `78bfad17cf5492340eb0` — U(`function-default-params`, `function-globals-read`, `function-return-shape`, `sink-helper-call`); `c80463fdc728955797e6` — U(`sink-helper-call`). Source: `evaluation/development/dependence-growth-loop/batch-h2/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| I1 | `2d0d2730b44ebe8f168e` — frozen comparison U but retained reason `independent-unit-definition-unresolved`; `c8ab843fba03148d3afc` — A+U(`unsupported-import-form`); `ce7daed01bb0fa178e26` — U(`function-argument-not-simple`). The first record's comparison/reason mismatch needs current-head verification rather than reinterpretation. Source: `evaluation/development/dependence-growth-loop/batch-i1/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| I2 | `1469a50a5381493a261b` — U(`function-globals-read`); `256ce9b8dd475ee95a97` — A+U(`function-globals-read`); `5f4ec238d04074266e32` — U(`function-argument-not-simple`). Source: `evaluation/development/dependence-growth-loop/batch-i2/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| J1 | `0446d28064111ee3fa4a` — U(`module-constant-not-closed`); `68ab4a740a5628e5849f` — A+U(`import-use-outside-grammar`); `e38216a09d49fd3302f4` — U(`function-return-shape`). Source: `evaluation/development/dependence-growth-loop/batch-j1/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| J2 | `219c020158a9081bab54` — U(`import-use-outside-grammar`); `56e4106c5ef7a44d29c8` — A+U(`augmented-assignment-not-modeled`); `729d2099346c87040906` — A+U(`count-predicate-not-closed`, `raise-guard-not-modeled`). Source: `evaluation/development/dependence-growth-loop/batch-j2/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| K1 | `0de3a6061d3bb4056306` — U(`import-use-outside-grammar`); `6b2da0c7167dbba3738f` — U(`unsupported-import-form`); `e9e2718573bb47f7d17b` — U(`function-return-shape`). Source: `evaluation/development/dependence-growth-loop/batch-k1/detector-run/DETECTOR_RUN_LEDGER.json:1`. |
| K2 | `2c458d2b523ea8c1bd90` — A+U(`reader-form-unsupported`); `3ae92d0bb421d6eee99e` — U(`function-return-shape`); `556f3545bebb45a3b005` — A+U(`augmented-assignment-not-modeled`). Source: `evaluation/development/dependence-growth-loop/batch-k2/detector-run/DETECTOR_RUN_LEDGER.json:1`. |

**Observed:** the pre-K reviewed-head remeasurement still found all 47 earlier materialized positives short
of full analysis and no adverse certificates (`docs/implementation/GROWTH-LOOP-STATE.md:1491-1501`).
That confirms the outcome, not which single wall should be built next.

### 2.3 Other planted positives that must not be counted as blind recall

**Answer-visible regression corpus.** `evaluation/regression-corpus-v1/ledger.json:1` contains 155
development cases, including 35 `case_role="positive"` cases: one for each of the ten calculation
components and 25 positive scientific-check fixtures (some components have both specialized and generic
positive fixtures). Every case is qualification-excluded; `qualification_use_permitted` is false, and
the ledger says most are pytest-generated rather than independently materialized repositories. These
show that adapters can recognize their designed shapes, not blind natural-project recall. Their highest
ceilings are Disclosure or MaterialQuestion, not Finding.

**Qualification positives.** A tree inventory finds 29 `positive_demonstrated` labels: 16
complete-domain exposure cases, six dependence cases, six founder-orientation cases, and one
copy-dosage case. Representative labels and the canonical ledger shape are visible in the one-line
scientific ledgers for
complete-domain (`evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/pilot-scientific-labels-three-case/SCIENTIFIC_LABEL_LEDGER.json:1`),
dependence (`evaluation/qualification/authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-direct-lane/heldout-seven-case/SCIENTIFIC_LABEL_LEDGER.json:1`),
founder orientation (`evaluation/qualification/founder-orientation-before-hmm-emission-v2.1.5-lane/pilot-a/SCIENTIFIC_LABEL_LEDGER.json:1`),
and copy dosage (`evaluation/qualification/classifier-derived-copy-dosage-representation-v2.0.4-lane/pilot-a/SCIENTIFIC_LABEL_LEDGER.json:1`).
Only the exact current dependence and complete-domain grant identities can promote; the pin table does
not authorize founder-orientation or copy-dosage Findings. These cases are now label-visible and have
already been consumed as development/qualification evidence; regardless of their original sealing, they
cannot supply the requested fresh blind N.

**Multiple-testing development control.** The explicit BH nonconformance control is another planted
positive, but its control specification sets production-Finding permission false and describes the tree
as mechanism behavior rather than natural-workflow recognition evidence
(`evaluation/development-controls/multiple-testing-bh-v1/CONTROL_SPEC.json:1`). It lacks a production
authority/promotion pin even when its declared table can be recomputed.

### 2.4 Which static surfaces can supply the missing observation

| Surface | What is feasible without executing project code | Current limitation |
|---|---|---|
| Python/R AST | Exact closed call, operand, aggregation, split, correction, and writer relations for registered forms | Every unsupported construct must abstain; the v2 dependence analyzer currently rejects whole files for many irrelevant forms |
| Selected CSV/TSV | Full-digest row counts, exact unit multiplicities, group constancy, split overlap, family cardinality | Unselected delimited files receive header-only inventory; row shape, values, types, and meanings remain unknown (`src/sc_referee/controller.py:483-519`) |
| Selected H5AD | Matrix shape, obs/var field names, index uniqueness, and storage can be read statically (`src/sc_referee/h5ad_inventory.py:285-351`) | Current output is physical structure only; biological-replicate meaning and use require separate evidence (`src/sc_referee/controller.py:522-555`). It does not expose donor/condition value vectors or multiplicities, and field names do not establish meaning (`src/sc_referee/h5ad_inventory.py:720-744`) |
| Report text | Literal method declarations, row/sample counts, “each row independent” admissions, correction claims, and selected-result wording can be span-bound | Prose cannot mint scientific authority; ambiguous wording must remain a question |
| Notebook source and saved outputs | Cell source is statically inspectable; output type and payload digest can be inventoried | Saved outputs are explicitly unverified, may be stale/edited, and do not establish execution order, hidden state, environment, or code-to-output provenance (`src/sc_referee/parsers/jupyter_inventory.py:154-215`, `:236-255`) |

## 3. Three high-value missteps that can meet a zero-false-accusation static standard

“Most common” below is an **inference based on domain practice, not a prevalence result from this
repository**. A prevalence ranking needs an external representative corpus. The predicates are deliberately
narrower than the general error classes.

### 3.1 Pseudoreplication / wrong unit of analysis

**Finding predicate required:**

1. A pre-analysis human authority record names the independent-unit key and the selected contrast.
2. A full-digest selected CSV, or a new bounded H5AD metadata-value adapter, proves more than one analyzed
   row/cell per authorized unit and exact unit membership in the compared groups.
3. Either (a) closed AST proves those rows/cells, without unit aggregation or dependence-aware modeling,
   feed one registered row-independent inferential procedure and selected writer, or (b) the selected
   report explicitly states that every row/cell was entered independently, names the registered
   procedure, and its stated N equals the complete table domain.
4. The selected result is inferential, not descriptive or sensitivity-only.
5. Finite suppressors all resolve: no pseudobulk/unit aggregation, pairing, random effect, cluster-robust
   variance, repeated-measures model, unit-level resampling, approved deviation, protocol amendment, or
   unsupported opaque path.

**Bounded Finding wording:** “For the selected analysis, the report/source declares N row-level
observations entering procedure P, while the authorized independent-unit key has U unique values with
repeated rows. No dependence-aware or unit-level reduction is present in the completely inspected
scope.” It must not claim that code executed, estimate bias, or call the whole analysis invalid.

**False-accusation mode:** the apparent unit column is not authoritative; rows/cells are actually the
randomized independent units; a donor-aware model or aggregation occurs on an uninspected path; the test
is a declared sensitivity/descriptive analysis; or the report's N refers to already-aggregated units.
Any one of these makes a Finding impermissible.

### 3.2 Multiple-testing omission or strict-subset correction

**Finding predicate required:**

1. A pre-analysis authority record defines one exact test family and requires a named correction.
2. Closed AST or a complete declared sidecar enumerates every performed test and the provenance of every
   p-value in that family.
3. The correction call receives a proven strict subset, or the selected report explicitly bases the
   family conclusion on unadjusted p-values while claiming the complete family.
4. The selected sink and claim are uniquely joined, and all correction/test paths are inspected.
5. Finite suppressors resolve: no prespecified single primary endpoint, disjoint families, hierarchical
   gatekeeping, closed testing, valid adaptive procedure, upstream correction, or exploratory-only claim.

The current multiple-testing recognizer already names essentially these four semantic roles but stops at
question-only (`src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py:42-69`,
`:91-121`). **False-accusation mode:** family boundaries were inferred from filenames or loop shape;
correction occurs upstream or in an unsupported library; hypotheses are legitimately separate families;
or the selected statement is descriptive. Static AST plus selected tables and report text is feasible;
notebook saved output alone is not.

### 3.3 Train/test or feature-selection leakage

Scope this to an exact split/fit/use relation, not the vague claim “data leakage.”

**Finding predicate required:**

1. A human authority record states that the selected metric estimates held-out generalization and names
   the independent split unit.
2. Exact selected CSV/H5AD metadata proves train/test unit-ID overlap, **or** closed AST proves a
   label-dependent feature-selection/fitting operation is fit on the union/full dataset and the same
   fitted object or selected feature set feeds the test metric.
3. The selected report sink uniquely claims held-out performance from that metric.
4. Finite suppressors resolve: no fold-specific/nested refit, group-aware cross-validation, legitimate
   cross-validation rotation, train-only fit hidden behind a supported wrapper, explicitly transductive
   target, or in-sample claim.

The installed Scanpy selection-reuse calculation check is a useful mechanism seed but is disclosure-only
(`src/sc_referee/calculation_checks/profiles.py:174-209`; `src/sc_referee/calculation_checks/selection_reuse.py:373`).
**False-accusation mode:** row IDs overlap but independent-unit IDs do not; repeated observations were
split correctly by unit; preprocessing was fit on train only; cross-validation intentionally reuses each
sample in different test folds; or the report never claims held-out performance. Current H5AD inventory
is insufficient because it does not expose exact split/unit value vectors.

## 4. Proposed next vertical slice: explicitly reported row-wise two-sample t-test pseudoreplication

This slice covers **one** misstep class only:

> A selected report uses one closed literal form to declare that row-level records from one complete
> selected table each supplied an observation to a two-sample `scipy.stats.ttest_ind` analysis, while an
> authoritative unit key repeats and no unit-level/dependence-aware method is declared in the completely
> inspected scope.

It does **not** cover binomial tests, paired tests, generic SciPy calls, implicit code-only dependence,
notebooks with unresolved runtime state, H5AD without exact metadata values, or arbitrary pseudoreplication.
The four Batch-K t-test positives are retrospective development targets; the two binomial positives remain
out of scope.

Why this slice: the K reports already provide the strongest possible literal admissions, so a focused
report-span verifier plus full selected CSV relation can avoid opportunistic expansion of the v2
whole-file grammar. It directly serves recall while preserving a small finite counterevidence surface.

### Acceptance criteria

1. **Normal path:** the result must enter through the ordinary `sc-referee audit` path, not `demo`, an
   evaluation-only adapter, or direct use of hidden controller parameters.
2. **Exact authority:** one pre-analysis, human-authored, digest-bound contract must supply the independent
   unit column and one-row-per-independent-unit requirement. Repository prose alone is insufficient.
3. **Exact material and cardinality relation:** one explicitly selected full-digest CSV must have a
   unique header, a complete row domain, a present nonempty unit column, and exact repeated unit values.
   `N_report` may be either one literal total or the arithmetic sum of exactly two per-group `n` cells in
   one report table; for the latter, both group labels must be the same literal groups named by the test,
   and no competing total, group table, or test may exist. `N_report` must equal the CSV data-row count.
   The method span and total/per-group-N span may be distinct only within the same selected report, with
   no more than 16 physical lines between their nearest boundaries, at most one intervening Markdown
   heading, and no intervening competing method, result, or N declaration. This bounded two-span join
   admits e9e2718's `24 + 24 = 48` table and 3ae92's adjacent method/N spans without treating arbitrary
   report-wide numbers as one analysis.
4. **Exact report relation:** the joined report evidence must (a) use one closed t-test spelling —
   `two-sample Student t-test`, `Welch's two-sample t-test`, or `scipy.stats.ttest_ind`, allowing only the
   observed `t test`/`t-test` hyphen variant — and (b) contain exactly one contiguous token sequence
   matching one of these four whitespace-normalized templates. Prose tokens are case-folded; the
   `<SELECTED_PATH>` slot remains byte-exact and case-sensitive:

   - `each of the <N> measurement rows entered the test as one observation`;
   - `each sampling-day measurement in the file was entered as one observation`;
   - `every nubbin record in <SELECTED_PATH> contributed one observation to the test`, where the path
     must equal the selected CSV path; or
   - `<TTEST_NAME> on the <N> individual chamber readings`, where `<TTEST_NAME>` is one of the closed
     spellings in 4(a).

   It must then join to one selected inferential result under criterion 3's span bound. No synonym,
   semantic paraphrase, or LLM judgment may satisfy the predicate. In particular,
   **`independent-samples t-test` or `two independent groups` must not satisfy 4(b)**: those phrases can
   describe independence between comparison groups while saying nothing about whether repeated rows
   within a biological unit were modeled independently. Likewise, a bare `N observations were analyzed`
   is insufficient because those observations may already be unit-level aggregates.
5. **Closed suppressors:** any mention or evidence of unit aggregation/pseudobulk, pairing, mixed/random
   effects, cluster-robust inference, repeated-measures modeling, unit-level resampling, sensitivity-only
   status, approved deviation, superseding protocol, ambiguous N, multiple candidate tables/results, or
   unsupported report composition forces non-Finding output.
6. **Bounded accusation:** the Finding states only the exact report/table/authority conflict and preserves
   the non-inferences that execution, numerical causality, bias direction, and global correctness are not
   established.
7. **Blind recall N = 3:** after implementation and all wording/predicate bytes are frozen, one new sealed
   six-case envelope must contain three fresh planted positives and three hard negatives. The normal CLI
   must admit a replay-identical Finding for **all 3/3 positives**. Existing K cases are development
   sanity checks and do not count toward N because their labels and walls are already visible.
8. **Zero false accusations:** zero false Findings on all 108 existing blind cases, all newly generated
   negatives, all 155 answer-visible regression cases, and the applicable qualification/control families.
   Correctly catching an existing planted positive is not a false accusation; scoring must report false
   accusations separately from total Findings.
9. **Retrospective development target:** before the blind envelope, the revised predicate should admit
   all four K `ttest_ind` positives: `0de3a6061d3bb4056306` through template 1 and literal total 40;
   `6b2da0c7167dbba3738f` through template 2 and literal total 60; `e9e2718573bb47f7d17b`
   through template 3 plus the exact `24 + 24 = 48` group-table sum; and
   `3ae92d0bb421d6eee99e` through template 4 plus the bounded adjacent method/N join. It should abstain
   on the two K binomial positives because their procedure is outside this slice. Failure to reach four
   is a design signal, not blind evidence to tune against indefinitely.
10. **No project execution:** AST/table/report inspection only. Saved notebook outputs cannot close the
    predicate.

**Needs verification and authorization:** the present scientific-requirement contract does not carry a
general public unit-column field, while the controller-only dependence authorization lock is an
evaluation-shaped route. Adding an authority field or exposing a new CLI input changes authority,
Finding eligibility, and likely a public record. `AGENTS.md` requires an ADR or explicit temporary
experiment for that class of change (`AGENTS.md:56-58`). No build should start until Alex chooses the
authority surface and the design receives its required review.

### Reviewer's alternative: promote the multiple-testing strict-subset conflict

The side-by-side alternative is to promote the existing multiple-testing machinery, which already
projects the four semantic roles, maps `strict_subset_correction`, and supports exact BH recomputation;
that could produce a first catch but would earn no recall credit on the 54 dependence-only planted
positives. Its minimal production route is a reviewed human authority surface naming the exact test
family and BH requirement, an ADR authorizing the ceiling/Finding-eligibility change plus an exact
qualification pin, and a fresh sealed blind envelope containing strict-subset positives and hard
negatives with zero false Findings. This memo does not choose between that route and the dependence
slice above.

## 5. Surfaces to park from the recall mission

“Park” means preserve as evidence/compatibility surface but exclude from the next recall slice. Nothing
should be deleted.

- **The 25 untracked Slice-C paths** — park untouched: formal M3 is incomplete and blocked, while the
  paths concern a report/publication transaction rather than scientific recall
  (`docs/implementation/GROWTH-LOOP-STATE.md:2748-2760`, `:2873-2879`).
- **Slice-C worker/runtime/publication/sandbox machinery and its review artifacts** — park: it addresses
  authenticated publication and execution-boundary claims, which are outside this task and prohibited as
  a workstream here; it cannot close a unit/test/sink scientific predicate.
- **Post-MPP execution authorization, OCI backend, and execution-security qualification surfaces** —
  retain for compatibility, park from prioritization: production MPP is static by rule
  (`AGENTS.md:41-43`), and executing project code is neither needed nor authorized for the proposed slice.
- **`src/sc_referee/dependence_recognition_v2/` whole-program grammar growth** — freeze as development
  evidence and a regression oracle: it is explicitly unregistered/report-only
  (`src/sc_referee/dependence_recognition_v2/adapter.py:1-18`, `:65-76`) and 54 blind positives have
  yielded no catch. Do not resume opportunistic wall-by-wall widening without measured whole-case yield.
- **Pure reader-form widening** — park: favorable reader substitution completed 0/7 census and 0/7
  frozen recurrences (`docs/implementation/GROWTH-LOOP-STATE.md:2464-2475`).
- **The original `wall-mining-corpus/run-40`** — archive only: all 40 omitted unit authority, produced an
  empty wall-frequency map, and the state explicitly says it is not useful for ranking
  (`docs/implementation/GROWTH-LOOP-STATE.md:1289-1295`).
- **Walking-skeleton `demo` detectors** — retain as tutorial/regression fixtures, park from mission
  investment: their locked fixture cannot establish recognition over arbitrary audits
  (`src/sc_referee/controller.py:4187-4234`).
- **Coverage-only detector names** — label as planned/absent and park until a concrete vertical slice
  owns one: merely listing them in coverage does not create recognition
  (`src/sc_referee/controller.py:3922-3937`).
- **Answer-visible regression and historical qualification positives as recall evidence** — keep them as
  safety/mechanism tests, but park them from blind recall scoring; the regression ledger itself forbids
  qualification use and warns against representativeness claims
  (`evaluation/regression-corpus-v1/ledger.json:1`).

## Claims that still need verification

- The ranking among the six K positives is counterfactual. Only a non-mutating, current-head
  premise-by-premise remeasurement can establish secondary walls and completion yield.
- The three “most common” classes are a domain-priority judgment, not prevalence measured on a
  representative repository sample.
- A report-text-first t-test slice appears smaller than v2 AST widening, but its exact grammar,
  counterevidence list, and adversarial false-accusation surface require a frozen design and hostile
  review.
- Public-CLI dependence conviction has not been demonstrated. Existing evidence uses hidden controller
  authority arguments.
- H5AD pseudoreplication and leakage detection is statically feasible in principle, but the current H5AD
  inventory does not expose the metadata value relations needed by either predicate.

## Decisions only Alex can make

- Authorize or reject the proposed single-class, report-text-first row-wise `ttest_ind` dependence slice.
- Settle whether **N = 3 fresh blind positives** is sufficient for the first recall-bearing slice.
- Choose the unit-authority surface: extend the existing scientific-requirement contract, design a new
  authority record, or expose a reviewed CLI form of dependence authorization.
- Authorize the ADR or temporary-experiment record required before any authority/Finding-eligibility or
  public CLI change.
- Decide whether dependence may be described publicly as controller-wired only, or whether a public-CLI
  demonstration is required before retaining a capability claim.
- Confirm that Slice C, execution/security machinery, v2 wall-by-wall grammar growth, pure reader-form
  work, and run-40 wall mining remain parked while recall work proceeds.
- Decide whether the next representative blind population should remain CSV/report-first or require
  H5AD metadata-value support before measurement.
