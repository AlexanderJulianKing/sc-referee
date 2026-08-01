# Experiment 0025: Iterative answer-isolated capability development

- **Status:** Active development protocol; recurring question-only checks admitted conservatively
- **Date:** 2026-07-30
- **Governing decisions:** Accepted ADR-0017 through ADR-0032, including ADR-0018's
  unresolved-obligation rule
- **Latest adapter revisions:** `check:somatic-clonality-representation`,
  `check:posttreatment-missingness-strategy`, and
  `check:ld-covariance-whitening-before-robust-fit` version `1.1.0`; no detector or Finding
  authority

## Purpose

Improve scientific-check coverage through repeated fresh-context workflow generation without
turning individual GeneBench failures into repository-, case-, answer-, or syntax-specific rules.
This is the development loop that precedes authenticated cross-provider qualification. It does not
replace qualification, admit a label, set a promotion threshold, or change Finding eligibility.

## Three-loop protocol

### Inner loop: controlled mechanism cases

Every proposed scientific check or adapter must first exercise four distinct development controls:

1. a demonstrated positive containing the exact bounded incompatibility;
2. a verified-good counterpart implementing the named alternative;
3. an ambiguous case in which the finite evidence cannot select one operand; and
4. a hard negative whose similar surface form is scientifically or structurally inapplicable.

Mutation, module-removal, sibling-isolation, manifest-drift, semantic-lock, replay, and no-project-
execution tests remain mandatory. These controls may be synthetic or evaluator-constructed and are
mechanism evidence only.

### Middle loop: fresh answer-isolated workflows

For a selected capability family:

1. prepare a new workspace through the existing answer-isolated GeneBench boundary;
2. expose only the task and declared data to a fresh-context workflow-producing agent;
3. freeze and audit the produced repository before answer-side access;
4. replay the semantic lock without model access;
5. grade only after the lock through the closed answer-side contract;
6. adjudicate the fixed-case method difference separately from production records;
7. classify the failure as an evidence-adapter gap, a scientific-check gap, an unsupported
   representation, an unresolved governing requirement, or no demonstrated issue; and
8. rerun the frozen regression corpus plus a newly generated workflow after any implementation
   change.

Old public workflows are regression evidence. Newly generated workflows are development challenge
evidence. Neither is held-out qualification evidence because the tasks and answers are public and
may have appeared in model training data.

### Outer loop: frozen qualification

Authenticated independent cross-provider reviews begin only after a candidate capability is
frozen. That loop owns scientific-label admission, detector/root equivalence, clustered metrics,
pilot-informed thresholds, and maintainer promotion. No implementation change may be justified by
qualification outputs without starting a new candidate version and a new qualification run.

## Anti-overfitting admission rule

A development fix may enter the shared scientific-check registry only when all of the following
hold:

- the check is stated as one existing ScientificContract dimension and one closed comparison;
- neither the check nor an adapter contains a GeneBench ID, benchmark answer, fixture path,
  repository name, or expected numeric value;
- applicability is established from named semantic roles and a complete bounded scope join;
- at least one fresh answer-isolated run or independent external representation demonstrates the
  same abstract obligation beyond the source used to design the rule;
- positive, verified-good, ambiguous, hard-negative, and removal controls pass;
- unrelated and previously accepted negative repositories do not gain a false question or issue;
- missing intent remains a MaterialQuestion or explicit unknown; and
- the module remains question-only and Finding-ineligible unless separately qualified and
  promoted.

If recurrence does not appear, the fixed-case probe remains evaluation-only and the production
path reports the representation as unsupported. A literal match to one submitted implementation is
not recurrence.

## Development scorecard

Each capability-family batch records these outcomes separately:

| Measure | Meaning during development |
|---|---|
| Answer-contract outcome | Which required outputs were within or outside the closed grader contract |
| Audit disposition | Demonstrated conflict, MaterialQuestion, covered good, ambiguous, or unsupported |
| Root-cause equivalence | Whether the bounded audit output matches the separately adjudicated fixed-case cause |
| Adapter connectivity | Whether the relevant immutable representation reached the intended scientific check |
| False-question count | Questions created on verified-good, hard-negative, and unrelated repositories |
| Replay and authority | Whether the result replays without model access, project execution, or new Finding authority |

These are development observations, not promotion metrics. Numerical promotion thresholds remain
deferred until a real pilot exists.

## First recurrence batch

The first batch targets the broad `measurement_model` and calibration decision family using new
answer-isolated runs for:

- directional versus symmetric observation-error treatment;
- coupled versus independent class calibration and calibration/standardization order; and
- the existing LD-aware MVMR workflow as a covered-good guard.

The accepted record initially contained only one public-development positive for each exact
measurement/calibration failure shape, and Experiment 0017 found no recurrence. The batch therefore
ran before a shared module was added. If a new agent made a different mistake, that result remained
a negative recurrence test rather than permission to broaden the grammar.

## First-batch results

### Calibration order alone: apparent recurrence rejected

A fresh answer-isolated carrier-screening workflow independently implemented a four-class linear
calibration model and standardized observed class distributions to the full roster before
deconvolution. This initially appeared to recur the abstract Experiment 0016 ordering error.

The workflow was run twice with byte-identical `answer.json`, `diagnostics.json`, and `report.md`.
The pre-change audit (`audit:21cc6bfcf2284497aaa5178bcbaf60d0`) locked and replayed with zero
Findings and zero MaterialQuestions. Answer-side grading occurred only afterward: three of five
fields matched; partner carrier frequency missed by `0.01600075622288233` at tolerance `0.003`, and
couple reproductive risk missed by `0.00015858463990534944` at tolerance `0.0001`.

A subsequent algebraic counterevidence check rejected the proposed recurrence. Within each
ancestry, the workflow applies one fixed invertible calibration matrix to every post-stratification
cell. If `D(q) = (M^T)^-1 q` and the target weights are `w_c`, then

`D(sum_c w_c q_c) = sum_c w_c D(q_c)`.

Calibration and weighting therefore commute for this workflow. Reversing only those linear steps
cannot change its answer. The answer-side grade cannot fill a missing scientific premise.

The briefly added `check:calibration-before-target-population-weighting` module was consequently
removed from the shared registry. Its grammar did not establish a cell-varying or nonlinear
calibration mapping and could have converted a scientifically immaterial step reversal into an
experimental incompatibility Disclosure. The retained regression now requires this fixed-linear
representation to create no scientific-check question. The six Experiment 0021 independent
repositories had also retained zero questions and Findings during the temporary expansion, but
that false-applicability result cannot cure the missing material premise.

After removal, the unchanged workflow was audited and replayed again as
`audit:760b08f46411437cab9bd3a367b16513`: zero Findings, zero ConditionalConcerns, zero
MaterialQuestions, and six coverage Disclosures. This is the correct conservative disposition
for the rejected order-only interpretation.

### Constraint scope: recurring general estimator choice

Further finite inspection identified the actual noncommuting fork. Experiment 0016's
`0.2792493901` reconstruction did not merely reverse two linear steps: it used a nonnegative
active-set solver separately inside each post-stratum and then weighted the constrained cell
estimates. The fresh workflow instead standardized observed mutually exclusive class
distributions and jointly inverted one fixed matrix at the ancestry aggregate. Its aggregate
solutions were feasible, but an unconstrained inversion within two zero-positive cells would
produce negative class prevalence. Projecting each cell onto the probability constraint before
weighting is nonlinear, so it need not equal aggregate inversion.

This is a real estimator choice, not a demonstrated scientific error. The public task asks for a
full-roster frequency but does not state whether feasibility constraints govern each cell or the
aggregate. The answer-side target proves only which estimator generated the benchmark number; it
does not make that estimator authoritative for a scientific review. In particular, cellwise
nonnegative projection can remove negative sampling fluctuations before averaging and therefore
has different finite-sample behavior from an aggregate joint estimator.

Two additional answer-isolated fresh-context agents independently selected the same aggregate
joint calibration and reproduced the same five proposed values. Their child-agent filesystem
writes were denied, so they produced no persistent workspaces, byte-identity evidence, audits, or
grades and are recorded only as contextual repetition. The first fresh workflow remains the one
durable recurrence artifact required by the admission rule.

The admitted `check:poststratified-misclassification-estimator` is independent of DRX1,
GeneBench, repository paths, answers, and numeric values. It recognizes only either of two exact
selected-report declarations:

1. standardize observed mutually exclusive class distributions, then jointly calibrate the
   aggregate; or
2. jointly impose nonnegative probability constraints inside each post-stratum, then standardize
   the calibrated cell estimates.

It binds the existing `measurement_model` dimension and asks the scientist which estimator
governs the review. Either selection can become an exact compatible or incompatible Disclosure;
neither becomes a Finding, historical intent, numerical causality, or universal correctness. An
unanswered choice remains a MaterialQuestion.

The durable carrier workflow now audits as `audit:d3c13c17e95d4664ad8de2e7660b7a45`
with one such question, zero Findings, zero ConditionalConcerns, and eight Disclosures; its
semantic lock (`sha256:28ce4192a1bb4e66e7c1c7baabae14c1a007534712913c57303fbcfb2d010670`)
replays without model access. Six commit-pinned independent QTL and robust-MR repositories remain
`not_applicable` for the new check with zero questions and zero Findings. The MR-tutorial sibling
still produces only its pre-existing MVMR covariance question; the new check produces none.

A separate fresh-context usability run then invoked the repository-local `scientific-audit` skill
against that durable workflow. It reached the same exact estimator question, exposed both finite
scientist choices and the retain-unresolved path, and stopped without selecting an answer. The
run (`audit:ac1cd379ab074c06aa08e038373da5d1`) was integrity-verified with zero Findings, zero
ConditionalConcerns, one MaterialQuestion, and eight Disclosures. Its semantic lock
(`sha256:6ce2551b43d8020d8d4936649ccf2f75bdde4773ccca2271b369147a2d54cb6a`) replayed
model-free with matching assessments, question identity, counts, and byte-identical lock and
rendered-report files. This establishes end-to-end skill usability for the admitted question; it
does not establish which estimator the scientist should choose.

### Directional measurement error: negative recurrence

The fresh Wright-Fisher analysis did not repeat the original literal `0.16`-as-symmetric error.
Instead, it rejected that value as inconsistent, used a symmetric `0.01` primary approximation,
and exposed directional alternatives as sensitivities. Its proposed estimate (`s = 0.0462`) remains
outside the prior public answer tolerance, but this is a different unresolved method choice. The
old exact profile was not broadened. The agent's filesystem write was denied, so this arm is not a
frozen reproducibility artifact and supplies no admission evidence.

### LD-aware MVMR: retained regression guard

The new guard agent prepared the same LD-aware modeling design but could not write its assigned
temporary workspace because of the child-agent filesystem approval boundary. No new artifact or
claim is recorded. The already frozen, replayed, within-contract MVMR workflow remains the current
covered-good regression guard; this attempted rerun contributes no additional evidence.

## Second capability-family batch: classifier-derived copy dosage

A new answer-isolated structural-copy workflow was generated from only the public task and seven
declared data files. It persisted `analysis.py`, `report.md`, `diagnostics.json`, and `answer.json`,
ran the newly authored analysis twice, and obtained byte-identical artifacts. Before answer-side
access, the frozen repository audited as `audit:99fa9608a8194a32ae100859829eb71c` with zero
Findings, zero ConditionalConcerns, zero MaterialQuestions, and seven Disclosures; semantic lock
`sha256:a79fd54a156f55c4ba6d0374eae57d7c4a71089b62f804385a6158510c32f637`
replayed model-free.

The workflow explicitly used continuous posterior expected copy dosage,
`P(copy=1) + 2*P(copy=2)`, rather than an integer classifier label. It separately calibrated the
nested and outer structural states. Answer-side grading happened only after that audit and replay.
The reliable carrier count and support code matched exactly. The expression coefficient missed by
`0.036711` against tolerance `0.03`, and the clinical coefficient missed by `0.070301` against
tolerance `0.055`. This is an important hard control: selecting the benchmark-compatible dosage
representation does not make the whole workflow correct or prove which other choices caused the
remaining numerical differences.

The earlier durable structural workflow supplies the other representation. Its source assigns
integer classifier predictions as both nested and outer dosages, and its report says the
classifiers predicted copy counts. The answer-side reference separately treats continuous
calibrated dosage as its target and documents several tolerance-equivalent continuous estimators.
That establishes a recurring general choice between using a predicted integer copy state as a
numeric exposure and using posterior expected copy count as a continuous exposure. It does not
make the answer-side preference scientific authority for a production review.

The admitted `check:classifier-derived-copy-dosage-representation` therefore remains
`measurement_model`, `value_equals`, question-only, and Finding-ineligible. It contains no locus,
gene, repository, task, answer, or expected number. It recognizes only explicit selected-report
declarations of either:

1. a predicted integer hard copy state used directly as numeric dosage; or
2. posterior expected copy count, including the exact finite-state expectation, used as continuous
   dosage.

The fresh continuous workflow now audits as `audit:df91ed7f942e4416a7d8a7463fa638d8`
with one MaterialQuestion, zero Findings, zero ConditionalConcerns, and nine Disclosures. Its lock
`sha256:614d1b10daecc6472a42bcad93ebace374df65d22262ff11208816cf97ce459c`
replays without project execution or model access. Matching and conflicting scientist Answers are
covered by the ordinary deterministic compatibility lifecycle and remain Disclosures, never
Findings.

The earlier hard-call report does not explicitly state that its predicted copy counts are the
downstream quantitative representation in one supported declaration. The adapter therefore marks
that real report `unsupported` and asks no question rather than completing a cross-paragraph
co-reference or importing source semantics. This is a known connectivity limitation, not a reason
to broaden the grammar. Six commit-pinned independent QTL and robust-MR repositories retain zero
questions and Findings. The MR-tutorial sibling retains exactly its pre-existing MVMR covariance
question; the new dosage check creates none. All nine audits replayed with verified integrity, zero
model calls, and no model access after lock.

A separate fresh-context `scientific-audit` skill run reached the new dosage question, displayed
both finite scientist choices plus retain-unresolved, and stopped without selecting a governing
requirement. It reported zero Findings, zero ConditionalConcerns, one MaterialQuestion, and nine
Disclosures. Its model-free replay preserved the run ID, question ID, counts, coverage state,
semantic-lock digest, and byte-identical lock and rendered-report files. This validates the
ordinary skill path for the second module without granting the reviewing model scientific
authority.

## Third capability-family batch: recoverable technical grouping

A fresh answer-isolated single-cell eQTL workflow was generated from only its public task and
declared data files. It persisted `analysis.py`, `report.md`, `diagnostics.json`, and `answer.json`,
then reproduced all four files byte-for-byte on a second run. Their SHA-256 digests are,
respectively, `36fbc34df9ddbc3273e89a8d16327a4c4b4b8c3e126aacb87a7b5f5144aaa3f0`,
`a9951c49b96154948af3173ade616f085178a4c8b004ad76fccbbf8c4db16baa`,
`fa802d52ad6a4bab4e59e41f4ea42de1ef36d1284d117bcd020c649fc4301b0d`, and
`5cc7878e2f9ac06dd7c411f720ba00e4a1877f64b96ecf51d7a6af59d7f71194`.
Before answer-side access, the frozen repository audited as
`audit:ed33fc59eb84465c9e8c2b389433197f` with zero Findings, zero
ConditionalConcerns, zero MaterialQuestions, and eight Disclosures. Semantic lock
`sha256:ecab77443954971407cf63009735104541337bd34c02f43bfb376aa67f9b7683`
replayed model-free.

The workflow reported that no donor-specific ambient or technical group was directly observed,
none was reconstructed, and no such group was included in the association adjustment set. It
retained the possible association between genotype and an unrecorded technical grouping as a
material unknown. Its fitted effect was `-0.24284056215778033`; answer-side grading after lock
showed an absolute error of `0.3571151427243559` against tolerance `0.05`. The answer-side
reference instead reconstructs a donor technical-contamination group from a unit-level ambient
summary and includes that group as a covariate. That reference is evaluation evidence that the
choice matters in this case, not scientific authority for production audits and not proof that the
omission caused the entire numerical mismatch.

The recurring general obligation is therefore not a particular gene, contaminant, clustering
threshold, or benchmark answer. It is whether a recoverable technical grouping derived from a
unit-level negative-control or contamination summary belongs in the primary association
adjustment set. The admitted `check:recoverable-technical-group-adjustment` remains
`adjustment_set`, `value_equals`, question-only, and Finding-ineligible. It recognizes only exact
selected-Markdown declarations of either:

1. a donor- or unit-level technical group reconstructed from a mean ambient, contamination, or
   negative-control summary and included as a categorical covariate; or
2. an explicit statement that no such group was observed or reconstructed and no such covariate
   was included.

It asks the scientist which treatment governs the review or allows the question to remain
unresolved. It does not decide whether a candidate grouping is scientifically real, which
reconstruction is valid, whether the group is a confounder, or whether adjustment is required.
The fresh omission workflow now audits as `audit:f4116f2a9e494936be0223c1b05e3c5c`
with zero Findings, zero ConditionalConcerns, one MaterialQuestion, and ten Disclosures. Its lock
`sha256:439f33c1e47900a28a79c065deb88a1bfce7cf049b1f01b9c53b83cf8fd27e2a`
replays without project execution or model access.

Controlled matching and conflicting Answers remain deterministic Disclosures. An ambient-QC plot
without an adjustment-set declaration safely abstains; directly observed sequencing batches and
biological treatment groups are not treated as recovered technical groups. The prior structural,
qtl2, DOQTL, tensorQTL, MVMR, mr.raps, and MVMR-cML workflows receive no new question. The public
MR tutorial retains only its existing covariance question while this new module is conservatively
`unsupported`. All nine audits have verified integrity, zero Findings, zero model calls, no model
access after semantic lock, and successful model-free replay.

A fresh-context `scientific-audit` skill run first omitted a final-report designation. The skill
correctly refused to infer that `report.md` was authoritative and asked only the publication-
surface question. A second clean invocation explicitly designated `report.md`. That run
(`audit:4840c5f63272483aade4f778d4933af0`) reached the exact technical-group question, displayed
both finite scientist choices plus retain-unresolved, and stopped without answering. It had zero
Findings, zero ConditionalConcerns, one MaterialQuestion, ten Disclosures, verified integrity,
zero model calls, and semantic lock
`sha256:6edf8ba8fc2aac57d2aa28c565582d9a06f16af6ccfbcbc25a567f8ffccaa80c`.
Its model-free replay preserved the audit and lock identities, counts, semantic projection, and
byte-identical lock and rendered-report files. This validates the normal explicit-report skill
path and preserves the publication-surface boundary when the caller has not selected a report.

## Fourth validation batch: fresh multi-parent QTL covered-good recurrence

A new answer-isolated multi-parent QTL workflow was generated from only its public task and four
declared data files. Its untouched task workspace first audited as
`audit:515561463b574570824116edccd05e33` with semantic lock
`sha256:6229ba4601a78474b37b71838efb6558045aa949ae35bbccf61664510e917929`,
zero Findings, zero ConditionalConcerns, zero MaterialQuestions, eight Disclosures, and a
byte-identical model-free replay. The independent workflow then persisted `analysis.py`,
`report.md`, `diagnostics.json`, and `answer.json`; ran twice; and reproduced all four files
byte-for-byte. Their SHA-256 digests are, respectively,
`5fd4e3d96cc0dac4d06127e2a1c0914c5a39b8ffbd5cd62ef4b0bdfe456ac635`,
`25e6a3a84d30f9898fa55b7f24c8fc00353b77a310ad845e16f9ecc9f5f994dc`,
`143ec7719378aeac5e2295a6d285dbe6a1b9acafc0a5e4686f32cf2d25be0b42`, and
`f78bb40860b20e6053784934a2522fddf257b4c885d63d841fa39eaeb20416af`.

The workflow explicitly aligned marker and sample identities, repaired two founder-marker
orientations before HMM emission, fitted an eight-state founder-origin HMM, and performed a
batch-adjusted seven-contrast founder scan. Before answer-side access it audited as
`audit:d5aa84c0c6e54619abc793bc7a33a22d` with zero Findings, zero ConditionalConcerns, zero
MaterialQuestions, and nine Disclosures. Semantic lock
`sha256:87c258b3ae9dff3e37397a963edb77d2d1402b24c6684c025f765033ae95eead`
replayed model-free. Grading happened only after lock. Founder `F5` matched exactly, and position
`46.5` differed from the hidden target by `2.1355513534494364` cM against tolerance `3.0`; the
complete answer was within contract. This is a fresh covered-good recurrence for orientation
repair, not a correctness certificate for every HMM or QTL modeling choice.

The pre-grade audit also exposed a bounded adapter-connectivity gap. Its selected report says
“Founder 0/1 alleles were oriented ... before HMM emissions,” while the accepted report adapter
recognized only the narrower “Founder alleles were reoriented before the HMM emission” form. The
report grammar now permits the optional explicit `0/1`, `binary`, or `marker` modifier and singular
or plural `emission`, while retaining the same orientation-before-emission verb relation, operand,
scientist question, and question-only ceiling. No scientific requirement, authority, or Finding
eligibility changed.

After that connectivity repair, the unchanged frozen workflow audits as
`audit:82cba3808a4f4bd1b54408e590970c1a` with zero Findings, zero ConditionalConcerns, one
MaterialQuestion, and ten Disclosures. Its lock
`sha256:7a1d3b1e47fb808b8b9e4d438c6b67da49b5d962155e36eed8d2f217acf413b4`
replays model-free. The observed operand is exactly
`repair_ril_founder_orientation_before_hmm_emission`; the scientist may select either closed
orientation rule or retain the question unresolved. A matched lookalike about plotting founder
alleles remains question-free. Commit-pinned qtl2, DOQTL, and tensorQTL audits also retain zero
questions and Findings, verified integrity, zero model calls, and successful replay.

A separate fresh-target `scientific-audit` skill run with `report.md` explicitly selected reached
the same question and observed operand. It displayed both finite orientation requirements plus
retain-unresolved, then stopped without answering. The run
(`audit:346db79ea8b44b64ad1dee6b9ca843ce`) had verified integrity, zero Findings, zero
ConditionalConcerns, one MaterialQuestion, ten Disclosures, zero model calls, and semantic lock
`sha256:65982fdcefce16a2e93064a70216ddcd257c30e2f7b21040c000be8d2626d246`.
Replay preserved the audit, snapshot, lock, question/options, semantic projection, and byte-
identical lock and report files. This validates ordinary skill usability for the newly connected
wording without allowing the reviewing agent to select the scientific requirement.

## Fifth validation batch: paired-bridge location alignment

A fresh answer-isolated CRISPRi/CasRx workflow was generated from only its public task and five
declared data files. The untouched task workspace first audited as
`audit:2d867e1bcb554619959258ba55c37776` with semantic lock
`sha256:1044ff4cc2689b5a8f49b827f6fd81ba0b80a76c9e63d42c8bf749420805236e`,
zero Findings, zero ConditionalConcerns, zero MaterialQuestions, and a byte-identical model-free
replay. The independent workflow then wrote `analysis.py`, `report.md`, `diagnostics.json`, and
`answer.json`, ran twice, and reproduced all four files byte-for-byte. Their SHA-256 digests are,
respectively, `a9eee94b36726f3391f0cc0428d5d71835ef468d5731152812b6611ee758929e`,
`6a5d320212e82e072b21bb81e1152c8140b67e6fa563597d1b29812fe13bc551`,
`e6323982cc412d70b4c5a928e113957be6e04d9f0ae6be8b4fc6e412040c56cc`, and
`d5f0d76a646c70f3298eed7e6252a2cebb36bdae2bdb967f6cf9521fda3c6640`.

Before answer-side access, the workflow audited as `audit:29d66b6f668243e1aeb4e0f3f5a173c6`
with semantic lock
`sha256:62e117898475ade135202af57c9aa4aba9474042ac12e2d577e4585abb87b1c4`,
zero Findings, zero ConditionalConcerns, zero MaterialQuestions, and model-free replay. Grading
happened only after lock. The target decision matched, but the lncRNA-specific and
neighbor-mediated effects missed their tolerances by `0.13890423637406768` and
`0.12305975878382125`, respectively. The answer was outside contract. The grade demonstrates a
result mismatch only; it does not establish its scientific cause.

Finite post-lock inspection of the evaluation report found a paired-bridge location correction,
two CasRx axes, and a joint effect model. That report is mechanism evidence for this public
development case, not production authority. An independent design review rejected a proposed
three-way calibration question because additive group offsets, multiplicative scaling, and
validation-only use can coexist. The admitted module is therefore the narrower atomic
`check:paired-bridge-location-alignment`: whether the scientist's review requires a
follow-up-minus-primary location offset estimated separately from paired bridge measurements and
subtracted before the follow-up effect fit. Global multiplicative scale and effect-axis choices
remain separate unresolved families. The check is selected-Markdown-only, question-only, and
cannot establish that either method ran, caused the mismatch, or is scientifically required.

The unchanged fresh workflow now audits as `audit:5274abf7918843ed9bcbd36596882b95`
with semantic lock
`sha256:032aee738860b382746e76950a541480d24f8d622e392b2eff2ed76edda3b4f9`,
zero Findings, zero ConditionalConcerns, one MaterialQuestion, and eleven Disclosures. An earlier
independently authored CRISPRi/CasRx workflow also produces exactly this question under
`audit:8e2aef76cdff45fa83f17cbfe56985a7` and semantic lock
`sha256:4cd22cbfce4230fff23a9f8dae74d49191ccba7fe4c27d7b8c0be55d92c5af14`.
Both report the no-paired-bridge-offset operand through different surrounding normalization
policies. Matching and conflicting scientist Answers remain Disclosures. An ordinary
negative-control-centering lookalike, a mixed offset-plus-scale positive, module removal, sibling
isolation, and ten unrelated or sibling workflows establish the finite development controls. The
three commit-pinned QTL and three robust-MR repositories remain at zero questions; the four local
siblings retain only their pre-existing applicable question. Every audit has verified integrity,
zero Findings, no project execution, and byte-stable semantic-lock, report, and question replay.

A fresh-target `scientific-audit` skill run (`audit:5d803a33f7214603a8748667f6c745a5`)
displayed the exact require-offset and do-not-require-offset choices plus retain-unresolved, made
the offset direction explicit, and stopped without answering. It had zero Findings, zero
ConditionalConcerns, one MaterialQuestion, eleven Disclosures, zero model calls, and semantic lock
`sha256:dcbf1d06b16534063963a1bc13a9595bb577ca087c521abbc8c52acf93f28706`.
Model-free replay preserved the semantic projection and byte-identical lock, report, and typed
question files.

## Sixth validation batch: called-tract ancestry exposure connectivity

A fresh answer-isolated pulse-admixture workflow was generated from only its public task and two
declared data files. The untouched task workspace first audited as
`audit:54145906e7b045daade4da27900e7cdc` with semantic lock
`sha256:19187ab2db78310a7e4f5700b6337d0026a7e713ce31ef95920dafc419fa21ad`,
zero Findings, zero ConditionalConcerns, zero MaterialQuestions, and byte-identical model-free
replay. The workflow wrote `analysis.py`, `report.md`, `diagnostics.json`, and `answer.json`, ran
twice, and reproduced all four files byte-for-byte. Their SHA-256 digests are, respectively,
`6c1a0e8b333321a89a953bc545accc60f2fb5761a7b42a037710bc556b5b7598`,
`e810e5874db343be016239f4bfa0d81a76583275e400226580b4b32b8ade81aa`,
`2f29cc6bf2b7116ec0a831fd8f310c78d75d467c1828f0be6cfe6ef2423bc6fc`, and
`6128f5f2ac04be533fcccd74df819c977cf4f9f6fa4dbb22d78b17e3a3080685`.

Before grading, it audited as `audit:eaddc790156a4e9b9a12fb80f7fcb1f8` with semantic lock
`sha256:c115853659383813eb2a076be4f193032861a2dab97d3ee44c4edbe4ddee8847`,
zero Findings, zero ConditionalConcerns, zero MaterialQuestions, and model-free replay. All four
numeric fields later missed their tolerances. The ancestry-fraction errors were
`0.20858515288813212` and `0.1594510162169105`; the pulse-time errors were
`1.5634726203506382` and `1.9186369379235355`. The workflow explicitly used eligible called
ancestry-A plus ancestry-B length as its denominator and excluded gaps and filtered tracts, but it
did not harmonize the chromosome-3 ancestry labels. That latter omission remains a compound,
unsupported path; the grade does not authorize a new detector or identify a unique cause.

The explicit called-length wording exposed a connectivity gap in the already accepted
`check:full-map-ancestry-exposure`, not a new scientific obligation. The bounded report adapter now
recognizes an exact declaration that the denominator is eligible called A plus eligible called B
length and that uncalled, filtered, or rejected intervals are excluded. A called-length QC-table
lookalike remains unsupported. The unchanged workflow now audits as
`audit:e607f9fe9b6645c783189352035780ca` with semantic lock
`sha256:b16912c2d0a7871700e72ca9554360280413209347f7c2e523998fbcc0c28fd7`,
zero Findings, zero ConditionalConcerns, one MaterialQuestion, and eleven Disclosures. It reports
exactly `high_confidence_called_tract_exposure_only`; the scientist may select either closed
exposure universe or retain the requirement unresolved. The paired-bridge module is not applicable
here, and the broader negative-control audits gained no false question. Semantic lock, report, and
question outputs reproduce byte-for-byte without model access.

A fresh-target `scientific-audit` skill run (`audit:4c3d59a429d946689057f06728c5bbcd`)
found exactly that one question, presented full-map exposure, retained-called-tract exposure, and
retain-unresolved, then stopped without answering. It had verified integrity, zero Findings, zero
ConditionalConcerns, one MaterialQuestion, eleven Disclosures, no project execution, zero model
calls, and semantic lock
`sha256:550154554a13acc1622ebb79e6f3a4f9983cfc6547fefa0afb506ee237808386`.
Model-free replay preserved the audit and semantic records and produced byte-identical lock,
rendered report, and typed question projection.

### Adapter connectivity defect found during the loop

The interaction test found that a matched single-line report ending in one newline produced an
evidence endpoint one line beyond `splitlines()`. The shared selected-report adapter now excludes
terminal newline bytes from paragraph spans. The regression uses the already accepted founder-
orientation question and proves that the same one-line source can proceed through structured
Answer, deterministic Disclosure, semantic lock, and replay.

## Seventh validation batch: direct-standardization conditioning set

A new answer-isolated carrier-screening workflow was generated from only the public task and five
declared data files after the user explicitly authorized the fresh agent to write and run its newly
authored analysis in the isolated temporary workspace. The untouched task workspace first audited
as `audit:587bdfb67e3c434d89da84c11b0203b6` with semantic lock
`sha256:d482b225967cadfe3390715b7c45406b822699c837b7d9bc0251408a95cd8c2a`,
snapshot digest
`sha256:6bbec871dd4b4e9bd6a5236fb26fa6f5bf3051fbae91e6010ba301a85c2ada18`,
zero Findings, zero ConditionalConcerns, zero MaterialQuestions, nine Disclosures, and a
byte-identical model-free replay. One discarded agent attempt was stopped after its context was
contaminated by sibling answer-side information; its accidental repository-root placeholder was
removed before the authorized fresh run, and no output from that attempt entered the experiment.

The authorized workflow wrote `analysis.py`, `report.md`, `diagnostics.json`, and `answer.json`, ran
twice, and reproduced all four files byte-for-byte. Their SHA-256 digests are, respectively,
`9c59241d3adf94ba49ed78a2f38de0c53ee4cc814a0a1804a292f3fd6d40d354`,
`352ac4b82d590f5310f0f9050cf0d4ea617b529df0f7270040afc9fc9900c61b`,
`d7ee5cc29979bdda2b647e58a9da3b0d2e6502d46efe3a2f1798533204051b40`, and
`540f4dc7a6970217012682b0232aeea4180bbbe56ba1dca3a29a6eda6925c26b`.
It fitted ancestry- and batch-specific multinomial latent-class mixtures from the control
confusion matrices. For partners, however, it standardized completed rows to the full roster only
over ancestry and family-history tier while treating intake site and collection wave as
testing-selection variables outside the standardization cells.

Before answer-side access, the frozen workflow audited as
`audit:f17af2456cc847ddafd236b83c483108` with semantic lock
`sha256:4516418d0d0611694c0feaa127b13b7d377396333b6c086944338a7236572b23`,
snapshot digest
`sha256:705565b1e1c2f7e0dd4898fcde64fb78152ea849c555201ea7ce3ee6cc5ccdc1`,
zero Findings, zero ConditionalConcerns, zero MaterialQuestions, ten Disclosures, and byte-
identical replay. Grading happened only after lock. The AFR and EUR carrier frequencies and AFR
residual negative-screen risk were within tolerance, with absolute errors below `7e-13`. The
reported full-roster partner frequency (`0.229793362209`) missed by
`0.04945602785549899` against tolerance `0.003`; the derived couple risk
(`0.002277498456`) missed by `0.0004901622314265543` against tolerance `0.0001`. This
is a three-of-five answer-contract result, not proof that the omitted variables caused either
mismatch.

An independent design review accepted only the atomic missingness-and-transport choice and
rejected any rule that would infer a required conditioning set merely because a variable predicts
completion. The new selected-Markdown, question-only
`check:direct-standardization-conditioning-set` asks:

> Which conditioning set governs direct standardization from completed rows to the full target
> roster for this review?

Its two finite scientist-governed operands are: include the specifically named testing-
availability variables with the declared substantive risk strata, or standardize only over the
substantive risk strata and keep the availability variables diagnostic-only. The authority basis
explicitly leaves the choice to the review's exchangeability, outcome-relationship, and positivity
assumptions. Predicting completion alone neither requires nor forbids inclusion. Complete/census
data, QC- or assay-calibration-only variables, ordinary outcome covariates, generic nonrandom-
testing prose, inverse-probability or doubly robust estimators, and partial or contradictory
conditioning sets do not produce a supported operand.

The unchanged new workflow now audits as `audit:470fd5f795c546e4bc37135e24b16900`
with semantic lock
`sha256:6a89e2f25e1f84e1812a58097593c431de13a22446c4fed470bdadb3e2c3745a`,
zero Findings, zero ConditionalConcerns, one MaterialQuestion, and twelve Disclosures. It exposes
exactly `substantive_risk_strata_only_with_availability_variables_diagnostic`. The earlier
independently authored carrier workflow audits as
`audit:5cd91ed6f44b4ab2bbc1858afed1c127` with semantic lock
`sha256:47987d9f68ab17bcc641cddc123097d789084837acb99beef7fcbe39ba58a189`,
zero Findings, zero ConditionalConcerns, two MaterialQuestions, and thirteen Disclosures. One is
its pre-existing calibration-estimator question; the new question exposes the opposite
`include_named_availability_variables_in_direct_standardization_cells` operand. Both audit/replay
pairs preserve byte-identical semantic locks and reports without model access.

Four unrelated local workflow controls retain only their pre-existing founder-orientation,
technical-group, copy-dosage, or ancestry-exposure question. Commit-pinned qtl2, DOQTL,
tensorQTL, MVMR, mr.raps, and MVMR-cML repositories retain zero questions. All ten controls have
verified integrity, zero Findings, zero ConditionalConcerns, no project execution, zero model
calls, and byte-identical lock/report replay. This is recurrence across two independent carrier
reports under opposite policies plus finite negative controls; it remains public development
evidence, not qualification, causal attribution, or authority to select either method.

A fresh-context `scientific-audit` skill user, isolated from the grade, answer, diagnostics,
implementation, and prior audit outputs, independently reached the same one question and stopped
without answering it. The run's question ID is
`question-analysis-scientific-check:8a0b4a0282f468b7ebc9`; its semantic lock is
`sha256:43448dcc8e74ac29d6954e8d5ae47547096b849f604445a728db85f49e877ad6`.
Audit and replay each have verified integrity, zero Findings, zero ConditionalConcerns, one
MaterialQuestion, twelve Disclosures, zero model calls, and no project execution. Their counts,
coverage status, open-question identity, typed question projection, semantic lock, and rendered
report match; the lock and report files are byte-identical. This validates ordinary post-hoc skill
usability for the new question without allowing the reviewing agent to select the governing
requirement.

## Eighth validation batch: causal closure of known misses

Development paused new workflow generation and returned to two frozen failures with one-change
ablation discipline. This distinguishes a detector-connectivity miss from a scientifically
different error and avoids broadening a question merely because a new workflow failed.

### Carrier conditioning-set ablation

The seventh carrier workflow was copied without changing its assay calls, control calibration,
screening-risk calculation, residual-risk calculation, inheritance calculation, or point-estimate
code. The only scientific change expanded partner direct-standardization cells from ancestry by
family-history tier to ancestry by family-history tier by intake site by collection wave. Sparse
finer cells made the optional descriptive bootstrap unstable, so the ablation reports that interval
as unavailable; this does not enter any graded point estimate.

Two executions reproduced `analysis.py`, `answer.json`, `diagnostics.json`, and `report.md`
byte-for-byte with SHA-256 digests
`676e75926df70d5d902428b39549b7e3cbf8194ceef09b6fd0e1eb91953a6cb3`,
`fe169cc8fcc64250312b58e1d6be390bd87be75192631c9aabba0c51b78771a2`,
`7fc56cec967427355d21fb688aba87eeecb58b78615e72c0f6efc2e10abb7d63`, and
`b7aee190b8c059007c403380904d89feb2d06dc1b06cd4cc7fef4c966c30dde6`.
All five answers are now within contract. The formerly missed partner frequency is
`0.278169059361` with absolute error `0.0010803307034989995` against tolerance `0.003`; couple
risk is `0.002756953453` with absolute error `0.000010707234426554548` against tolerance
`0.0001`. This causally supports the already admitted conditioning-set question for this frozen
workflow; it does not prove that those variables universally belong in every transport estimator.

The natural passive report sentence initially exposed a grammar gap. The bounded adapter now
accepts “completed-test call distributions were directly standardized” with the same explicitly
named cells and full-roster basis. The repaired audit is
`audit:d9ef7ba9042648c98539fd6bb5099c4b` with semantic lock
`sha256:a31cbdb88e0de367ce9d06ffb45ec6b424ad2b1208afc76c547e4d0770ba7812`, zero
Findings, zero ConditionalConcerns, one MaterialQuestion, and twelve Disclosures. It observes only
`include_named_availability_variables_in_direct_standardization_cells`; replay preserves the lock
and report byte-for-byte.

### Population-genetics ablations

The frozen pulse-admixture workflow was first copied with one change: reverse chromosome-3 A/B
labels before exposure and transition counting. Two runs reproduced byte-identically. Both
ancestry fractions moved within tolerance—parent 1 to `0.27640186653566884` and parent 2 to
`0.721746516387806`—while both timing estimates remained far outside tolerance. This isolates
chromosome-label orientation as the cause of the two fraction misses but rejects it as a complete
explanation of the timing misses.

A second bounded ablation retained that label repair and made two pulse-timing changes together:
count transitions between successive eligible tracts within a chromosome across intervening
uncalled or filtered spans, while keeping chromosome ends as boundaries; and use the complete
chromosome-map length in `t = N_switch / (2 m (1-m) L_map)`. Two runs reproduced all four output
files byte-for-byte. The answers are parent-1 fraction `0.27640186653566884`, parent-1 time
`3.0171829257469582`, parent-2 fraction `0.721746516387806`, and parent-2 time
`6.009588564735541`. Their absolute errors are `0.0030190438397632025`,
`0.020645`, `0.003048315982476013`, and `0.0410105`, all inside tolerances `0.01`, `0.05`,
`0.01`, and `0.1`. The output digests are
`51770473558f9c75a69d807f2edf8818f8c732e827755cf4102814ca4b8f938d`,
`e3938396f03558e4802dfeb9a015826a6da3432cd4cb8f01ac87966818acd111`,
`201dc752fdb4ddc377a2f4f5e322b4f9cf5b1fda3b73ecd75a46f955b0fdd725`, and
`bfaf8af0cf2b5d400c4174f62d5ab6cb801ba57a7c0ee98d8b0a31c75494f5ea` for analysis,
answer, diagnostics, and report.

The successful report legitimately uses eligible called A plus B length for ancestry fractions
and full chromosome-map length for pulse timing. The previous
`check:full-map-ancestry-exposure` grammar nevertheless matched the fraction paragraph first and
misreported called-tract exposure for the pulse model. Accepted ADR-0023 corrects that semantic
conflation without a schema release: check and adapter version `1.1.0` bind only the pulse-time
definition, and an ancestry-fraction denominator cannot trigger or answer the question. Transition
path continuity remains a separate unsupported choice because it has not independently recurred.

After the correction, the original audit (`audit:6c91131aa4394aabb03dcf63a8fe4086`) and the
label-only audit (`audit:b9a7568fee5c4f92a1e7c3e36dcb7e44`) each observe
`high_confidence_called_tract_exposure_only` under `time_definition`. The combined corrected audit
(`audit:dace0ad75e6b4b41b9a030370433228f`) observes
`full_chromosome_map_exposure` under the same dimension, despite the distinct called denominator
for its ancestry fraction. Their semantic-lock digests are, respectively,
`sha256:dce53e3f84ed2bccf1d8f4bd1c06288b760f934e346081448e6509b9c73c0785`,
`sha256:f28ebeacb527e8c6aaa3b5b61cd1f9bced0487bca6dd5f255bc3c6e89af33164`, and
`sha256:4fff566d7457bed90e38b53ae1b063c4050f9e6ee7d4abc6a0b45ba2f31134de`.
All three audits have verified integrity, zero Findings, zero ConditionalConcerns, one
MaterialQuestion, twelve Disclosures, no project execution, and byte-identical lock/report replay.

### CRISPRi/CasRx ablations

The frozen CRISPRi/CasRx workflow was first copied with only the paired location-alignment repair:
follow-up-minus-primary bridge offsets were estimated per plate and subtracted before the follow-up
effect fit. Two executions reproduced `analysis.py`, `answer.json`, `diagnostics.json`, and
`report.md` byte-for-byte with SHA-256 digests
`6d5646549192655591dec3ab891f530ac5ba14a80c0377d50870742cba1be414`,
`b7b37c36ed2f32c962db712c1938f62b75868567fb70ffb2f9cb8bde3e9a5043`,
`d341d9dfad924466b5b46fe8cf1fa4200e6e8cb6ef2aa3c9e22cb52b9af2d92b`, and
`6df1e7ffdd21833a25678bff49b9490e041e9277054562ef44a554b32400db4e`.
The neighbor-mediated effect moved within tolerance, with absolute error
`0.02634191716182166` against `0.03`, but the lncRNA-specific effect still missed by
`0.08078180945642932` against `0.01`. Grade
`genebench-answer-grade:7d1a15eadd6746bc42a7` is therefore outside contract. This causally
supports the paired-offset question for the neighbor estimate while proving that it is not a
complete explanation of the transcript miss.

A combined repair retained those offsets, used simultaneous effective dominant- and non-dominant-
transcript CasRx axes, and repaired the bounded pooled-screen preprocessing and local model. Two
runs reproduced all four output files with digests
`64728f6bbc015ece33dcc64453614ec1038a6ed7f9ab583dbd98bff3e91deaa1`,
`ea1e81b957649132f302842f8d7b36647e7da6a4dcaa98665d7160c58dee9a2e`,
`340b4fbef99af44b2e801d3ea0c4217e803e5af302a83d89d07b18bc0914e289`, and
`fd0e428cef4594ea41e2ed2b273396e365c5e02224a5bdad9d599333a84aaa2d`.
The decision remained `0`; the lncRNA effect was `-0.04801200309835169` with absolute error
`3.098351693264778e-9`; and the neighbor effect was `-0.6149638621700209` with absolute error
`0.02352813782997909`. All fields are within contract under
`genebench-answer-grade:83b9fc0e2620d56ee98c`.

The combined repair is not treated as one indivisible method. A reverse control retained every
other combined repair but restored the high-overlap one-axis CasRx regression. It reproduced with
analysis/answer/diagnostics/report digests
`a4b2c2b93cb5c6c39a794f5e91ebe27058a8a3a3d3def230e37a4019aa64873d`,
`294d5b0ca42914238776469f2c4a8645d64f2c0b56240ab52757c1658e2f3e50`,
`7736dd3730edf23187d4736b97b47442201a3b41091e607e0405b5fb11d7f66c`, and
`522f6b0013f3d41c8cb373fdd6d16438a2b5575c5b0b81de4fe0adaf7ec8a78b`.
Its lncRNA error rose to `0.013661709188756428`, outside tolerance, while the neighbor effect and
decision remained within contract. A two-axis repair placed on the original incorrect pooled scale
also left the lncRNA estimate outside tolerance. Together these controls show an interaction: the
two-axis model matters after the other repairs, but it is not sufficient on a wrong upstream scale.

Accepted ADR-0025 therefore adds only `check:casrx-isoform-axis-model`. It asks the scientist to
choose between a high-dominant-overlap single efficiency axis and simultaneous effective dominant/
non-dominant axes, or retain the requirement unresolved. It contains no fixed overlap threshold,
benchmark answer, or numeric authority and remains independent of the paired-bridge question.
Two independently authored failed reports expose the one-axis operand. The combined report exposes
the two-axis operand, and the reverse control returns to the one-axis operand. Their audits are
`audit:45f3def61a454d6299ac490704b004c5`,
`audit:f87426a9bb694d4cb8a869c0e5de4c35`,
`audit:8c9c4a70d1f84562a337ff75adcc63c9`, and
`audit:7a95e69be892427f9f94abd7ea832a8d`; their semantic-lock SHA-256 digests are
`249a689b08eeea5df2bf16386336401eb03428adadb50e43f296f0adecdf3609`,
`702efc1ac7a4d6bc64a51da4ea90dbfff2f96550dbd6bec4f1c179c22e9a1846`,
`aa73296c355ebdc3eecbee8060b6a13d4ff8385dbc15d7d702ef18b09ee9175d`, and
`b3be8b47a5fc243f61715d0b29169c09c29a5a52f6c9fe70110792e0b25f25d2`.
Each has zero Findings and byte-identical lock/report replay.

### Structural-copy calibration ablations

The fresh structural workflow already used posterior expected copy count rather than an integer
hard state, but its pooled multinomial classifiers produced `expression_log_fc = 0.296630` and
`subhap_log_or = -0.330620`, missing by `0.036711` and `0.070301`. The public evaluation record
describes a different continuous calibration target: fit copy count directly from marker evidence
within ancestry groups, then transport the clipped continuous predictions into the downstream
models.

A bounded upstream-calibration ablation left the reliable carrier definition, downstream weighting,
clinical model, expression model, support rule, and output contract unchanged. It replaced the two
pooled copy-state classifiers with separate ancestry-stratified RidgeCV regressions for segment B
and outer orientation, using the released marker panel and PCs and clipping predictions to 0--2.
Two executions reproduced `analysis.py`, `answer.json`, `diagnostics.json`, and `report.md`
byte-for-byte with SHA-256 digests
`017d290acbd9b3760b41cb44f3ca7e9587a0bca9fb417841aa9fa6a9b8e188ca`,
`9b25aac66dae6fdf2dbe0e65c54b122b5ecb658f3be26c1d704f0cb111448779`,
`bfad997b733d222599c3658fca9670bb1b3e7b1721ade085975c809970b33c78`, and
`4201ebb82670071af28568a8146d49f117f407cf5093740fa7d3f90dfe158d99`.
The outputs are carrier count `195`, support code `1`, expression coefficient `0.318087`, and
clinical coefficient `-0.368725`. Their errors are `0`, `0`, `0.015254`, and `0.032196`; all are
within contract under `genebench-answer-grade:23898f37dd51de805bd8`.

Two reverse controls separate the calibration decisions. A pooled direct RidgeCV model retained
the direct continuous representation but missed the clinical tolerance by `0.131777`. An ancestry-
stratified multinomial classifier retained posterior expected dosage but missed expression by
`0.032623` and clinical by `0.104990`. Their grades,
`genebench-answer-grade:da2474c7954ade8409ca` and
`genebench-answer-grade:9bb356a87ba42431659b`, remain outside contract. Thus direct-versus-
posterior representation and pooled-versus-group-specific calibration are independent, interacting
choices; neither is a universal one-step fix.

Accepted ADR-0024 corrects only the already admitted dosage-representation question. Check and
adapter version `1.1.0` add `direct_continuous_calibrated_copy_dosage` beside integer hard state and
posterior expected copy count. Exact report wording is required, scientist authority is preserved,
and the module remains question-only. Calibration pooling is deliberately not added: the original
report does not explicitly bind that policy, and no independently recurring report-connected pair
supports a finite pooling question.

The posterior workflow, successful direct ablation, pooled-direct reverse control, and stratified-
posterior reverse control audit as `audit:ddef29412dfa477ba13987ee0cb1046a`,
`audit:94080fc29d094034bb719c2725cafd7a`,
`audit:1cbecd06b58b4d81aed7d6edf056a34b`, and
`audit:1f94de7e6c3349f6a73424806ccf1d9e`. The first and fourth expose posterior expectation; the
second and third expose direct continuous calibration. Their semantic-lock SHA-256 digests are
`8c79b48a85dfe1eca47076d2b2ba4f81eaaf7c4459f80200bdf739f62bdaab06`,
`3fe513b56e1c45ed2f150e988bb82abd0e4350ef005b631b5f28dc2da3541b3f`,
`7770909e35db0c0be753255ae44e71e675ae84decb6546afb13d50a4e34ba494`, and
`2eb68890116b93453aa638b5a42aeb1772f5853e2b8777b31e6c567a68132020`.
All have zero Findings and byte-identical lock/report replay. The older hard-call report remains
conservatively unsupported. QTL, ambient-eQTL, carrier, pulse-admixture, and CRISPR sibling
workflows retain only their existing questions; the revised dosage module is not applicable to all
five, and each control replays byte-identically.

### Poststratified misclassification-estimator causal closure

The durable carrier rerun had already isolated two wrong outputs: aggregate joint calibration gave
partner frequency `0.2632486338416167` and derived couple risk `0.002609076047521205`, while its
three screening quantities exactly matched the released contract. A one-change ablation retained
the calls, control matrices, post-strata, full-roster weights, screening estimates, Bayes residual,
and Mendelian calculation. It instead fit nonnegative joint class probabilities inside each
post-stratum and then standardized the calibrated cell estimates. Four of the sixteen cells had a
negative component under unconstrained inversion.

The constrained ablation produced partner frequency `0.279249390064499` and couple risk
`0.0027676606874265553`; all five fields are within contract under
`genebench-answer-grade:ec8a8dbcac1271e07f43`. Its analysis, answer, diagnostics, and report SHA-256
digests are `f69270885575d523fdaf6cda0ec8083dff314d0bbc564aa4456ef4e5f3c2f917`,
`d8b5e9581c7cdc123191ee37a6ebc891078861a5053e3e497af3f0d18fbf7ef8`,
`ef67caf088dc6cdde01f984e610c8434aae07bf995819aa00dd8f43ef369a452`, and
`04bd0d9528c2e742a2b2fa65b6e960d49fd61226d658a32475cf22201ed3e9a6` and reproduce across two
executions.

A reverse control performed the same calibration inside each cell but deliberately retained the
unconstrained linear estimates before weighting. Linearity returned the original two wrong values
exactly, and grade `genebench-answer-grade:2389cc1625ecc4130bad` remains outside contract. This
separates the material nonnegative constraint from a scientifically immaterial order-only rewrite.
Its four artifact digests are
`2ddae543b0504923756b8d2e33b81f6239fac26199849bb3da939ffc41980ece`,
`05d4649de10e95cb015be530e47b2f0ca188216de812629836a6ff4e37acfeb0`,
`47856967e66c686e2a65be793ca2899faf3f7b21cb3cac6fed58df49d187099b`, and
`97eb51c2a83ed86fcb90be47d480148d3e6b956d1272d9b01bfb831987d31994` and also reproduce.

The repaired report audits as `audit:cf4090f543cf4b02b6f759913c3b553a`, exposes exactly the
existing `poststratified-misclassification-estimator` question, and has semantic-lock file digest
`015cfabb60280910d3a5a68c191a8db169059e69e8944686508d09529f2da2da`. The unconstrained reverse
control audits as `audit:dd8d3c9109e64c3f83977eac78eb225c`, correctly exposes no candidate for
its unsupported representation, and has lock digest
`112c2df370562e8155ee38b377aee75f0475055d1bac3d0df1e57ba32c78f37e`. Both have zero Findings,
zero ConditionalConcerns, no project execution during audit, and byte-identical semantic-lock and
HTML-report replay. This is fixed-case causal evidence for the already admitted question, not
scientist authority, universal estimator preference, detector qualification, or Finding permission.

### Ambient-state eQTL two-axis causal closure

The original ambient-state workflow used the higher two-means cluster of CP10K-normalized,
ambient-corrected IFI6 and ISG15 and omitted any reconstructed technical group. It estimated
`-0.24284056215778033`, an absolute error of `0.3571151427243559`. The released reference report
made two separable observed-data choices: recover a donor group from the gap in donor mean HBB-
derived contamination and recover activation on a scale consistent with the corrected marker
counts. A bounded 2-by-2 retained the outcome correction, markers, deterministic two-means
algorithm, donor pseudobulk, offset, ordinary covariates, model family, and output contract.

Changing only the marker score from CP10K-normalized corrected counts to corrected-count scale
gave `-0.35992817688451284`, error `0.2400275279976234`, outside contract under
`genebench-answer-grade:4407ec9a65b6e12d1c26`. Keeping the original state rule and adding only the
recovered 12-low/12-high contamination group gave `-0.38952915642628516`, error
`0.21042654845585107`, outside under `genebench-answer-grade:80345ddcf1ee013691c5`. Combining the
two changes gave `-0.554563920997461`, error `0.04539178388467524`, within contract under
`genebench-answer-grade:4c0152556d63b24e2c56`. Neither axis is sufficient alone.

The scale-only analysis/answer/diagnostics/report digests are
`95a141486b2b1cab5ede1e8f691f2a8b709c6c8a1986f3953f528e46354e047f`,
`d178083a1e223b393c08bdc0007e2831b85efd3243c0b671d6f33955bba45655`,
`7734d3dbc4ebd8c1e7e8c2686bb1273786602291a79bb00886ecaff3c84023aa`, and
`ca9c692ce4b897aee13f5ecad41564fe9e28e99d9051ea0e111f4f90783caeb5`. The group-only digests are
`80210f70cb6a55bc688321b12612c04d0bddc302eda3ec351d5b8d5af728088d`,
`bcbcb401194317fbf390f93a50f04fe7db23b31df9ad8787cd693d390404a2eb`,
`63752948200b5fd09054da82f437493611eacdad84538d2dfd8d42dcdce01185`, and
`e82828d99456b07094ab2f739d7864f7910eac5929bd30ea73234f011afc75bf`. The combined digests are
`c7441bba43ad4a5865b0b4a5efe6a4e76b0df27afcd43417f605b454e255dad4`,
`c928dec835cf81045e215bdb84c4940f06bbdcd2731fdc9ef52809522651a053`,
`e30f69d896b7c05184d994e8e0af45f9ccd1a8d8305b0ad5bec2b3f1c8bf04d5`, and
`3436aef4cd5a4b47e57e8e452710624d6be2ef9968ddd22f50d047d2bda014c8`. Each reproduces across
two executions.

The three audits are `audit:1365bb549e6643109b6171d611227ac2`,
`audit:3bd8970eeb0f4227831f6b113197102b`, and
`audit:eb1f25a4de874abfa677a52d1d965513`, with semantic-lock file digests
`f3b6ba414d94e4ba8056aad0957420d537b3c907b8043e5ea608fc434f0c7614`,
`fb78055beccb13905f401d3e97bfac582deed50d3fccc1d2befddaa4c71ccad7`, and
`5765d06bcc66876d4a2aef8028418bcb59fdb1ef9dcf506fa1a90b6b63ffe424`. Each exposes exactly the
existing recoverable-technical-group question, has zero Findings, and replays lock and HTML report
byte-for-byte without project execution or post-lock model access.

An evaluator-owned finite decomposition also tested positive-marker-only and positive-minus-
negative-marker scores on corrected-count and CP10K scales with either two-means or the visible
reference threshold. Several distinct state rules were within tolerance once the recovered group
was included. Therefore no activation-marker formula, fixed threshold, or universal raw-count-
scale question is admitted. The current state-recovery scale remains unsupported until a general
scientist-governed obligation recurs beyond this case. The technical-group question is causally
relevant here but is not a whole-workflow correctness certificate.

### TXR1 target/estimator compound-failure closure

The frozen TXR1 workflow selected `387` patients and reported therapy code `1`, benefit `36.5`,
toxicity `33.6`, and net utility `24.8`. The public contract expects code `1`, benefit `42.9143`
within `0.5`, toxicity `35.9689` within `1.0`, and net utility `30.3252` within `0.4`. Visual and
text inspection of the released reference report identified two independent method axes: the
molecular target reconstruction and the missing-outcome target-trial estimator.

An evaluator-owned reconstruction used the released analysis-set expression residual, the
purity/copy-adjusted single-copy CCF and long-read/phase handoff gates, normalized IPTW/IPCW
benefit risks, and normalized treatment-weighted toxicity. It recovered target `n=354`, benefit
`42.9326`, toxicity `35.9668`, and net `30.3443`; all four graded fields pass. The evaluator and
the bridge that places the original estimator on the repaired target have SHA-256 digests
`c3e3cbcd11281eff4d4ed6cc01f913dc586a036097d4585ec10bd4a377d3d372` and
`3877b3b07b20b9cf810c156b5e34176d56f16e289c6578482dd8dad63ea20c6f`.

A 2-by-2 then varied the two axes independently. The target-only repair retained the generated
sequential outcome-imputation/AIPW estimator and returned `44.3`, `33.6`, and `32.5`; all three
numeric fields remain outside contract. Its analysis/answer/diagnostics/report digests are
`e0b656df850b9bd47c0cc6437a57a909e7931b3a6474fd9381e3c65dec1ee2db`,
`803f33c61f0ae74090490c672d8a5ac0c5291640e03b04c8958b077fd69f6329`,
`ce5431a8ec3dfc4b21f593108ebe3855b45639266c80b9f1f1e17f92a33ce09b`, and
`d0614cb8a4405291359a2b67f4d717f5d65e7cf32afc76416db3cb050e4852d3`.

The estimator-only repair retained the generated `387`-patient target and returned benefit
`39.58`, toxicity `35.4116`, and net `27.1859`. Toxicity passes, while benefit and net remain
outside. Its four digests are
`9e20a037ac6638d1f88acd18514e55bffbbd841b3e48f6e3cb64f2360e1ba1d7`,
`816131be317e735a6753dfa8cd3738310c93e4c3219f697e30bce43d12caa772`,
`5187778f720465b627b7dd4d2115cac587e8bded3badb3bb5bb961962d28a877`, and
`ede3b85261ef989ebf52a656d9266f618b63460d3776606f4d27d1b4a33076a8`.
The combined repair is the passing evaluator above; its materialized workflow digests are
`cd10ddf3a04dc7bb563554d2091170b43f4f4e6a97793f74fefb36c523b283dd`,
`5303d4fa0cc4b825010fcf72917af8f1ca3d32ae340543a2ab0512466a8c95ef`,
`2c2329230dcee73f8db603cf144c6e6b8940139c6aad2736525873ba38128edf`, and
`433291c02b2aeba38a1323e14029c7a6812ba34fe9b0d6dec2aaa7d852202902`.

Accepted ADR-0026 therefore adds two independent question-only modules rather than a compound
TXR1 rule. `check:somatic-clonality-representation` distinguishes a direct local-copy ceiling from
a purity/copy-adjusted clonal-fraction eligibility window.
`check:posttreatment-missingness-strategy` distinguishes sequential outcome imputation that
conditions on a reported post-treatment endpoint from assessment weighting that excludes that
endpoint from the missingness model. Both preserve scientist authority, omit benchmark numbers
and thresholds from their manifests, and cannot emit Findings.

The original, target-only, estimator-only, and combined audits are
`audit:5cc7a86bacf4439ca91b0c41e968a003`,
`audit:4976a4569b5d4b098b4b0f19dab3548e`,
`audit:fdb7850a9455418db99c4586504204ad`, and
`audit:df880187e72548f0b13e810bff98a523`. Their semantic-lock file digests are
`f8bd4fff1dcfe92cc097fa55ec9076d849b94e51480b8298fd572c6b925e807f`,
`6a89b0236c33d1aa8af762ada8646cb558b60aa68661e5c44d05d2f54abcf919`,
`93bf5c3ef1176d8b141d83e064f8f8b6d7ea505b3c8c905024f3b7022011ae9d`, and
`174040c8aa51d48fa76edebb3dc842ab04bd1df20e8d627de00cf20ba629d6b1`.
Each has zero Findings, exactly two questions, no project execution during audit, and byte-identical
semantic-lock and HTML-report replay. Their observed operand pairs form the expected 2-by-2.

### Fresh Wright-Fisher recurrence and directional-error question

A new answer-isolated agent independently implemented an exact finite-state haploid Wright-Fisher
HMM from only the released task and data. It correctly used the outgroup to polarize REF as the
derived allele before HMM emission, omitted the zero-coverage generation, used the supplied
generation-specific effective population sizes, and selected locus `A`. Its `analysis.py`,
`answer.json`, `diagnostics.json`, and `report.md` SHA-256 digests are
`eaf64345e806fd51c8fce700294b50428259edf08df7dd01574f568c2fb813eb`,
`5d4b0b68a402148f97fcf7052dfb78529663284bda91ea2ff949219430363442`,
`8e9927ad28f74ff64d662c01d129f57556e39c631d724c39e17985aa97d16177`, and
`83f6980558cbfebe15e8104d800082370e6082e548bd827a5f27f7ba7b9c30a6`; two executions were
byte-identical.

Before answer-side access, audit `audit:a05907b667504106b0fae40200afa7c2` locked and replayed with
zero Findings, zero ConditionalConcerns, and zero MaterialQuestions. Grading occurred only after
that replay. The selected locus passed exactly, but `s=0.063559` missed the released `0.101256` by
`0.037697`, outside the `0.02` absolute tolerance. Visual and textual inspection of the released
reference then localized the exact ablation: the workflow used the reported average error `0.16`
as a symmetric rate in both directions, while a direction-specific split of `0.31` and `0.01`
recovers approximately `s=0.101255`.

This is recurrence rather than a new one-off interpretation. The earlier independently written
Wright-Fisher report also stated that only the average of two directional allele-miscall rates was
available and that its read likelihood assumed symmetric errors. Accepted ADR-0027 therefore adds
`check:directional-measurement-error-interpretation` under `measurement_model`, with two closed
operands: use the reported average symmetrically, or decompose it using an independently supplied
directional constraint. The check does not infer the direction, floor, assay mechanism, or correct
operand.

The fresh workflow now audits as `audit:130936c892bd4097b8d1813c6bc531aa`; the earlier workflow
audits as `audit:66673a5c95464478a92fd1502ae78bd0`. Each has zero Findings, zero
ConditionalConcerns, exactly one directional-error question, and byte-identical semantic-lock and
HTML-report replay. Their semantic-lock file digests are
`127fa6277662850d516cd5e977162e82987b0db6427789518549648e8c60a104` and
`c013aa2fb408a8a10fee476bc0e49c0311a8dffd29dfafb893ccfe7ace038b5e`.

The post-change repository checkpoint passes `956` tests, Ruff lint and formatting, strict typing,
starter and schema validation, and the complete clean-wheel handoff verifier. The handoff verifier
also passes the walking skeleton, model-free replay, general audit, scientific interaction flows,
RO-Crate export, capability generation, and migrations from v0.6.0 through v0.15.0.

### Fresh Hi-C recurrence now reaches ADR-0018's unresolved expected-count question

A separate answer-isolated agent implemented a deterministic 20 kb Hi-C loop-enrichment workflow
using a per-replicate arithmetic mean of all 15 same-distance pixels, including the focal pixel, as
expected count. It also checked complete upper triangles, exact distance labels, two replicates per
condition, target annotations, and exact 20 kb-to-40 kb aggregation. The first attempted execution
with the host's older system Python stopped before writing outputs because
`Path.write_text(newline=...)` was unavailable. Re-execution under the project's supported Python
3.12 environment succeeded twice with byte-identical outputs. The analysis, answer, diagnostics,
and report digests are `e35d2e097f53d75d6a893d8f764a02b106984416d923338c7731c4f92b775039`,
`0a6eaab03a273bfd842422220a877f2eb0a4a9aa828cef8fb426b13c09f61556`,
`6d318350e43e2d272ca85a264de1fb2e617acc9f7d45e8e4408cb5423a67a512`, and
`e6e4767946729b5277920e47855831939489830991da06b38d17d8ef2e310c60`.

The audit locked and replayed before answer-side access. The staged input digests exactly match the
reacquired immutable GeneBench problem. Post-lock grading returned zero of three fields within
tolerance: case `1.068707542692679` versus `1.8807937197289109`, control
`-0.7497128915841309` versus `-0.5185535629629917`, and delta `1.81842043427681` versus
`2.3993472826919024`. The released reference requires a masked, condition-specific negative-
binomial background with replicate intercepts, condition-specific distance and GC terms, a
restriction-site term, low-mappability and case-specific stripe exclusions, target exclusion, and
20 kb scoring.

The first post-directional audit was `audit:a986df003a7f472ab7144d9f6f862f1c`, with semantic-lock
digest `63bb9ddb417adbaa54de903500099a5cd2e1816f62c7b1aa8af882febddb4836`. It had zero
Findings, zero ConditionalConcerns, zero MaterialQuestions, and byte-identical semantic-lock and
HTML-report replay. That zero-question result exposed an implementation gap in already accepted
ADR-0018 rather than a reason to add a Hi-C-specific binary check.

The ordinary post-hoc audit now implements ADR-0018's claimless unresolved-obligation branch. It
requires every premise to be exact: one completely inspected conventional task-like Markdown
source requests three role-bound mean log2(observed/expected) outputs; no complete supported
expected-count profile is present; the selected report contains exactly one enumerated
target-inclusive same-stratum mean; the report gives exactly one value for each requested output;
and one exact target-exclusion sensitivity changes at least one requested value. The compiler
emits one analysis-scoped draft ScientificContract and one MaterialQuestion asking which closed
six-dimension expected-count profile governs. It emits no Claim, SemanticAssertion, detector
candidate, ConditionalConcern, or Finding. A human may provide the existing complete
`expected_count_background_v1` value or retain unknown; because the reported method remains an
unsupported partial representation, even a complete human Answer creates only Finding-ineligible
analysis-scoped declarations and no method-conflict candidate.

The final fresh Hi-C audit is `audit:5c9b0290a86b40219119b4742cd33262`, with semantic-lock file
digest `b92617024297240c6414077a61a8a746ffd16e0d82c545f1610a940a3f250ad0` and report digest
`a6ee454cb71d18a08cc9e420f1496023cf34be446310adb557ddd9007497da54`. It has zero Claims,
zero Findings, zero ConditionalConcerns, and exactly one question. The question records that
`case_loop_strength`, `control_loop_strength`, and `delta_loop_strength` all change under the
report's target-exclusion sensitivity, without describing the difference as material or naming the
answer-side negative-binomial method. Semantic evidence and HTML replay byte-for-byte.

The grammar is role-bound rather than Hi-C-key-bound. A non-Hi-C stratified-signal fixture with
different output names reaches the same question, while its equal-value covered negative,
duplicate-method ambiguity, and misbound-sensitivity hard negative all abstain with zero Findings.
The capability matrix publishes this as a separate no-detector question-only profile, so the
experimental method-conflict detector does not falsely claim to cover the unresolved
representation.

The final repository checkpoint passes `969` tests, Ruff lint and formatting, strict typing,
starter and schema validation, and the complete clean-wheel handoff verifier. The handoff also
passes installed-wheel capability generation with eight entries, the walking skeleton,
model-free replay, general audit, linked interaction flows, RO-Crate export, and every migration
from v0.6.0 through v0.15.0.

A fresh-context `scientific-audit` skill user then tested only the visible Hi-C workspace. Its
first run correctly reached one claimless question with zero Findings and model-free replay, but
found that “provide six closed dimensions” was not independently actionable for a scientist. The
question now includes a plain-language guide and its affirmative option is “Provide expected-count
recipe.” It asks for the background observations; estimator, likelihood, and link; replicate or
group handling; covariates; resolution, scale, and orientation; and exclusions including focal-
target handling. The post-fix fresh audit is `audit:ffb320f2c5d8498fab4f78f5ddd3e388` with zero
Findings, zero ConditionalConcerns, one MaterialQuestion, and 15 Disclosures. The fresh user found
the report independently actionable with no remaining broad usability defect; semantic lock,
report, semantic projection, and coverage replay identically with zero model calls.

### Fresh pulse-admixture recurrence closes transition-path continuity

A new answer-isolated agent independently implemented the pulse-admixture task from only the
staged task and two data files. It masked posterior-below-0.90 or low-complexity-above-0.50 tracts,
merged only touching same-ancestry retained tracts, counted switches only at touching retained
boundaries, used retained callable length as timing exposure, and used all ancestry labels
literally. Four completed executions reproduced `answer.json`, `diagnostics.json`, and `report.md`
byte-for-byte. Their SHA-256 digests are
`98f0f48c60a77f3863e173d735272b34ead5cf95c1a6f1c48df9b5c49ce3cc10`,
`1497e7ec46620670d2ebfdfa90c9647b35623bc92ee6d3cea33d8602afcd7beb`, and
`065c7a3617c128419445904bac10e867ee9f17bb1d70dd23c4107af7531cabf0`;
the restored, revalidated analysis digest is
`acaada28516fd137f96328d257b54b8925d348a7f494db3f2b87437e4e44d242`.

The first audit locked and replayed before answer-side access as
`audit:ab6b650733a9446cb89993055a0f6a8d`, with zero Findings, zero ConditionalConcerns,
and zero MaterialQuestions. Post-lock grading found all four fields outside contract. The ancestry-
fraction errors, `0.20858515288813217` and `0.1594510162169106`, exactly recur the prior workflow's
errors; the timing errors, `1.5634726203506382` and `1.9186369379235364`, recur its timing failure.
The zero-question audit therefore exposed both a connectivity gap in ADR-0023's accepted exposure
check and a missing transition-path representation.

An evaluator-owned 2-by-2 first repaired the independently demonstrated chromosome-3 label
orientation in every cell, then varied only transition continuity across retained-data gaps and
full-map timing exposure. The results were:

| Transition path | Timing exposure | Parent-1 time error | Parent-2 time error | Grade |
|---|---|---:|---:|---|
| terminate at gaps | retained called length | `1.1973164184866216` | `0.9948031597759437` | outside |
| preserve across gaps | retained called length | `0.1830671959214092` | `0.38405026024117195` | outside |
| terminate at gaps | full map | `1.3137233753657345` | `1.3287794465941092` | outside |
| preserve across gaps | full map | `0.0206449786170384` | `0.04101046843649314` | within |

The fraction fields remain within tolerance in all four cells. Every cell ran twice with identical
outputs and was audited, semantically locked, replayed, and only then graded. This proves that path
continuity and exposure are separate and jointly necessary in this fixed case; it does not make
either choice universally correct.

Accepted ADR-0028 adds the domain-neutral, question-only
`check:within-sequence-transition-path-continuity` under `dependence_structure`. Its two operands
preserve the path across missing, masked, filtered, or uncalled intervals within a sequence, or
terminate the path at those intervals. The adapter requires one explicit selected-Markdown method
declaration and cannot infer hidden states or select the governing choice. ADR-0023's existing
exposure adapter now also recognizes the fresh report's explicit retained-callable, complete-map,
and map-excluded-from-time-exposure forms without treating an ancestry-fraction denominator as a
timing operand.

The unchanged fresh baseline now audits as `audit:9ab8f2d765444da384c60233d0775c5a`
with semantic-lock digest
`sha256:08a166ceec369a39d62f705422279209df6f785a474a3350eeb63886e5510343`,
zero Findings, zero ConditionalConcerns, and exactly two independent questions. The prior baseline,
prior combined repair, and all four fresh 2-by-2 reports project their exact operand pairs. Finite
positive, covered-negative, ambiguity, plotting-only, incomplete-declaration, coexistence, module-
removal, structured-Answer, and replay tests preserve zero Findings. This adds no schema release,
detector qualification, execution privilege, numeric authority, or public maturity claim. The
resulting full checkpoint passes `980` tests and the complete clean-wheel handoff verifier.

### Fresh structural covered-good recurrence repairs linked report connectivity

A fresh answer-isolated agent independently analyzed the structural-copy task from only the task
and seven released data files. It retained 483 reliable calibration records, calibrated the named
segment-B and outer-orientation continuous copy indices separately within ancestry using RidgeCV,
and kept the two dosages separate downstream. Two executions reproduced `answer.json`,
`diagnostics.json`, and `report.md` byte-for-byte. The analysis, answer, diagnostics, and report
SHA-256 digests are
`1cdc64d849d1861f506ba42298ad77b7442133bbcfa77a72439fd1ceb45c8d32`,
`5c7e124d4e316f0532b3cc121e8f192c323071aaeeddc7ed6b5c1dd46d4de62f`,
`bfc1c41c909e886cd92016b97551fc6b4ea1565b1cc391f5ab7f7d22c166f565`, and
`725e5bd550b107f2cbecc411a22c3af53b4d49201b27c744b0555822b9dbf7a0`.

Pre-answer audit `audit:e36a5a3550e34a5cb8428d9ed373ebe4` locked and replayed with zero
Findings, zero ConditionalConcerns, zero MaterialQuestions, and no project execution. Only after
that replay, answer-side grading passed all four fields: carrier count `195`, support code `1`,
expression coefficient `0.34902668888389443` with absolute error `0.015685688883894433`, and
clinical coefficient `-0.3961798925816906` with absolute error `0.004741107418309409`.

The zero-question result exposed a bounded connectivity miss in accepted ADR-0024. The selected
report explicitly retained a continuous copy index rather than rounding, named Ridge regression
for the segment-B index, and used calibrated segment-B dosage in the downstream model, but those
statements occupied separate paragraphs. Accepted ADR-0029 advances the stable dosage check and
adapter to `1.2.0` and permits only this finite same-literal-target document join. The unchanged
workflow then produces exactly the existing direct-continuous representation question; the
posterior, prior direct, pooled-direct, and stratified-posterior reports retain their exact prior
operands and replay byte-identically with zero Findings.

The fresh agent selected group-specific calibration and passed. The earlier pooled-calibration
failure therefore did not independently recur, so no pooling-versus-stratification question is
added. Mismatched-target and calibration-QC-only reports remain unsupported, unrelated report
sections are excluded from the evidence span, and no schema, Finding authority, numeric authority,
execution privilege, qualification, or general calibration claim changes. The resulting full
checkpoint passes `984` tests and the complete clean-wheel handoff verifier.

### Fresh ambient-state recurrence repairs bounded technical-group co-reference

A third answer-isolated ambient-state workflow was generated from only the public task and three
declared data files. It estimated `-0.5207800755679264` and locked before the answer-side truth was
read. The official grader later reported truth `-0.5999557048821362`, absolute error
`0.07917562931420985`, and failure against the exact `0.05` tolerance.

The fresh workflow used a CP10K-normalized ambient-corrected IFI6/ISG15 score, a deterministic
two-normal mixture, donor pseudobulk, an additive ambient CXCL10 mean term, and ordinary donor
covariates. A frozen evaluator-owned decomposition changed only activation scale, only recovered-
technical-group adjustment, or both. Scale only estimated `-0.44444648467856884` with absolute
error `0.1555092202035674`; group only estimated `-0.6569431728534296` with error
`0.05698746797129339`; and the combined arm estimated `-0.6386823006260116` with error
`0.03872659574387538`. Only the combined arm is within the released tolerance. This independently
recurs the two-axis interaction seen in the earlier workflow, while again failing to justify a
universal score, marker set, threshold, or activation-scale rule.

The pre-repair audits of the three ablations were `audit:34407de8a6fa4ac6823e42750e2d4463`,
`audit:9640daa83d4d469bb573aed3f6664b51`, and
`audit:a627541e296f431ba035d59decea7018`. Each locked and replayed exactly, but all three exposed
zero questions. The group-only and combined reports explicitly said that donor soup fractions
separated into low and high ranges, that the workflow reconstructed **that** technical group, and
that it included **it** as a categorical covariate in the primary model. The existing adapter
triggered but classified this ordinary pronoun-linked form as unsupported.

Accepted ADR-0030 advances only the existing technical-group check and adapter to `1.1.0`. Its new
paragraph-scoped form requires an explicit technical-proxy summary and separation, `that`
technical group, and `it` as a categorical covariate in the primary model, all within finite
distances. The post-change scale-only, group-only, combined, and untouched fresh-baseline audits
are `audit:7be63f3cfea644c494405f405782dbe1`,
`audit:a4a0552913f84e6daddc1391e960225b`,
`audit:47554cd445dd47afa08ad7a965f94d5e`, and
`audit:e7cbf3f7d506452b8049fd0925c52219`. Their semantic-lock file SHA-256 digests are
`fecd6b92eabfea75da1de2f2f3a846506ab33d30163f18e933a530930541e580`,
`82a2d41360625c6f5000fd1a9e2488613a630a57936b9d33a7afca586263d2d6`,
`1c78ff4f4945e035127989492c9f0acb06cf384c65c2a614bb354ad448159703`, and
`c004d2ef95abad1b0d9fc53ed731ed75fec8e61efa3e23e53a12dd2da12a638e`.
The two reports without group inclusion remain question-free; the two inclusion reports expose
exactly the existing adjustment-set question and operand. Every run has zero Findings, verified
integrity, no project execution, no model calls, and byte-identical lock and HTML replay.
The resulting full checkpoint passes `987` tests and the complete clean-wheel handoff verifier.

### Fresh TXR1 recurrence preserves unsupported choices and repairs report connectivity

A second answer-isolated TXR1 workflow was generated from only the public task and seven declared
data files. Its two executions were byte-identical. Before answer-side grading, audit
`audit:efdf460705fe470b9905ef5fd6a7cbfd` locked and replayed with zero Findings, zero
MaterialQuestions, verified integrity, no project execution, and no model calls. The workflow
defined a 400-patient promoter-facing molecular target without either accepted ADR-0026 clonality
gate and used cross-fitted AIPW whose assessment model included observed post-treatment toxicity.
Both representations were correctly unsupported.

The official grader later reported benefit `31.332`, toxicity `33.832`, and net utility `19.491`
percentage points against truths `42.9143`, `35.9689`, and `30.3252`; all three numeric fields
failed. A frozen evaluator-owned two-by-two retained the fresh AIPW implementation while changing
only the molecular target, only exclusion of toxicity from the assessment predictors, or both.
Target-only returned `44.009`, `36.325`, and `31.296`; missingness-only returned `32.443`,
`33.832`, and `20.602`; combined returned `45.023`, `36.325`, and `32.309`. Target-only and
combined pass toxicity but remain outside benefit and net tolerances. Missingness-only fails all
three. The target definition accounts for most of the fixed-case discrepancy; excluding toxicity
does not repair this fresh workflow, and the residual AIPW-versus-normalized-IPW difference remains
unsupported.

The repaired reports nevertheless state two already accepted operands explicitly. Accepted
ADR-0031 advances the somatic-clonality and posttreatment-missingness checks and adapters to
`1.1.0` with finite selected-report forms for an evaluator-frozen Markdown-inline
`reference_target` adjusted-CCF gate and a primary/evaluator-owned baseline-only assessment model
with explicit post-treatment exclusion and inverse-assessment transport. It adds no new operand or
scientific rule. Post-change audits `audit:aeebf955c8fd47879eebbb70ecbe0924`,
`audit:c15cb8014e4d472f9020103d094f8adc`,
`audit:bbfb115e9ab64c1eaa4b0f78467463eb`, and
`audit:eb570462d9f5496c93c276942f95f8f6` form the expected zero/target/missingness/both question
matrix. All preserve zero Findings, verified integrity, no execution, zero model calls, and
byte-identical semantic-lock and HTML-report replay.

### Fresh MVMR recurrence separates instrument construction from heterogeneity response

A fresh answer-isolated MVMR workflow was generated from only the public task and nine declared
data files. It harmonized all alleles, used phase separation, conditioned marginal associations
through the full LD matrix, selected six phase-1 joint signals, fitted phase-2 joint coefficients
by full-covariance zero-intercept generalized IVW, and applied outcome-independent batch QC and
within-batch protein scaling. Two executions were byte-identical. Pre-answer audit
`audit:47ac5a10f8ce41dbb3a60324224f5e59` locked and replayed with zero Findings and zero questions.

The workflow returned PROTA `0.4014409387` and PROTB `0.3647942733`. After lock and replay, the
official grader exposed truths `0.2931551453124849` and `0.22207276661877273`; absolute errors were
`0.10828579338751515` and `0.1427215066812273`, so both fields failed the exact `0.025`
tolerances. A frozen evaluator-owned two-by-two held harmonization, phase separation, LD input,
protein scaling, and QC fixed while crossing phase-1 marginal versus LD-conditional instrument
construction with zero-intercept GLS versus a fixed Tukey-biweight fit on Cholesky-whitened
residual innovations.

Conditional-GLS returned `0.4014409387` and `0.3647942733`; marginal-GLS returned
`0.3269302012` and `0.3315084093`; conditional-robust returned `0.4006839265` and
`0.3719899837`; and marginal-robust returned `0.2900914882` and `0.2275588522`. Only the combined
marginal-robust cell passes both released tolerances. This makes instrument construction and
heterogeneity response two separate fixed-case causes, without making either benchmark-compatible
choice universally correct.

Accepted ADR-0032 adds exact question-only
`check:phase-split-mvmr-instrument-construction` and
`check:mvmr-residual-heterogeneity-estimator`. It separately advances the existing
`check:ld-covariance-whitening-before-robust-fit` adapter to `1.1.0` for the natural
`M-regression`/lower-Cholesky wording. Final audits `audit:d812552543d54ddbbd7e5b6ddc990038`,
`audit:4a7c06a73a6d4ad99a1e734d2c1956a9`,
`audit:5fc6a60df28f442fa6abb39f2899f4f7`,
`audit:14320a3d5d324a8ebd90404ddfa44f3f`, and
`audit:2d884560227847e5b5215e3e7629954e` expose the expected instrument/estimator matrix, with the
two robust cells also exposing the independent LD-whitening question. Earlier robust workflow
`audit:1a2ae4a827054408859ee42d9598dd55` exposes its robust and whitening operands but retains an
unsupported instrument representation because its report does not explicitly call the phase-1
screen marginal. MVMR, MVMR-cML, and mr.raps controls receive no question; MR-tutorial retains only
its prior ADR-0021 covariance question. All ten audits have zero Findings, verified integrity, no
project execution, no model calls, and byte-identical semantic-lock and HTML-report replay.

An independent fresh-context agent then used the repository-local `scientific-audit` skill on the
untouched workflow with `report.md` explicitly selected. Audit
`audit:72d115c5400140e0b17a2d8c04581b21` exposes exactly the conditional-instrument and
generalized-IVW/GLS questions, presents the finite alternatives and retain-unresolved options, and
records no Answer. It has zero Findings, zero ConditionalConcerns, two MaterialQuestions, and
twenty Disclosures. Its replay preserves semantic records, assessment counts, coverage, semantic-
lock digest `sha256:d543e4ad5bdb6f97d3e7a16942625d595ac0370a8bf65f7af9f4a96c5932e95a`,
and HTML-report bytes with verified integrity, no project execution, and zero model calls.

The resulting full checkpoint passes `1013` tests, Ruff, formatting, strict typing, and
starter/schema validation, plus the complete clean-wheel handoff verifier.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** exact aggregate and constrained-cellwise declarations; matching and conflicting
  scientist Answers; ambiguous dual declarations; classifier and under-specified hard negatives;
  module removal and sibling isolation; semantic lock and replay; the fixed-linear order-only hard
  negative; the single-line terminal-newline evidence-span regression; exact integer-hard-state
  and posterior-expected-copy declarations; dosage ambiguity, carrier-count-only, classifier-plot,
  under-specified cross-paragraph, and medication-dosage hard negatives; dosage-module removal;
  matching/conflicting dosage Answers with replay; exact reconstructed-group and explicit-omission
  declarations; technical-group ambiguity; QC-plot-only, observed-batch, and biological-group hard
  negatives; bounded source-first `that`/`it` technical-group co-reference; a non-GeneBench sample-
  level positive; a sensitivity-model-only hard negative; technical-group module removal and
  sibling isolation; and matching/conflicting technical-group Answers with replay; natural `0/1`
  founder-orientation wording; its plotting
  lookalike hard negative; independent qtl2, DOQTL, and tensorQTL false-question replays; exact
  paired-bridge require/no-offset declarations; an offset-plus-scale coexistence control;
  ambiguity, ordinary negative-control centering, bridge-QC-only, absent-bridge, removal, sibling,
  matching/conflicting Answer, and replay controls; natural eligible-called A-plus-B denominator
  wording; a called-length QC-table hard negative; exact include-availability and diagnostic-only
  direct-standardization declarations; dual-declaration ambiguity; complete-data, QC-only,
  ordinary-covariate, generic-missingness, inverse-probability, and mixed-conditioning hard
  negatives; direct-standardization module removal and sibling isolation; and matching/conflicting
  target-population Answers with replay; mixed called-fraction/full-map-time separation; exact
  called-time and full-map-time declarations; fraction-only, transition-path-only, and conflicting-
  time-definition controls; and original, label-only, and combined population-genetics audit/replay
  regressions; exact one-axis and simultaneous-two-axis CasRx declarations; CasRx ambiguity,
  axis-construction-only and unrelated-regression hard negatives; independent coexistence with the
  paired-bridge question; module removal and sibling isolation; matching/conflicting Answers and
  replay; exact direct-continuous copy-calibration declarations; three-way dosage ambiguity;
  calibration-QC-only and directly measured dosage hard negatives; and posterior, direct, pooled-
  direct, stratified-posterior, old-structural, and five sibling audit/replay regressions; exact
  sequential-imputation and assessment-weighting missingness declarations; exact direct-copy-
  ceiling and adjusted-clonal-window target declarations; dual-declaration ambiguity; descriptive,
  complete-outcome, baseline-history, QC-only, and negated-target hard negatives; a four-cell
  module-independence regression; and original, target-only, estimator-only, and combined TXR1
  audit/replay regressions; exact symmetric-average and direction-specific measurement-error
  declarations; the earlier and fresh Wright-Fisher report representations; dual-declaration
  ambiguity; QC-only and symmetric-transition hard negatives; directional-error/founder sibling
  independence; module removal; and both real Wright-Fisher audit/replay regressions.
  ADR-0018's claimless expected-count branch adds an exact actual-workflow positive; missing-task,
  missing-sensitivity, equal-value, duplicate-method, complete-profile-present, and missing-output
  suppressors; a non-Hi-C role-bound positive, covered negative, ambiguity, and hard negative; a
  closed analysis-scoped Answer test; capability-profile separation; and byte-identical audit,
  semantic-lock, report, interaction, and replay checks.
  ADR-0028 adds both independently authored terminate-path declarations; prior and fresh preserve-
  path declarations; the existing and natural pulse-exposure forms; exact positive, ambiguity,
  plotting-only, and incomplete-declaration controls; transition/exposure coexistence; module
  removal and sibling isolation; matching/conflicting scientist Answers; the four-cell fixed-case
  ablation; and deterministic audit, semantic-lock, HTML-report, and Answer replay.
  ADR-0031 adds natural adjusted-CCF and baseline-only assessment positives; sensitivity-only
  missingness and clonality hard negatives; and the fresh TXR1 zero/target/missingness/both
  connectivity regression. ADR-0032 adds exact marginal and LD-conditional phase-split instrument
  declarations; exact generalized-IVW/GLS and robust LD-whitened estimator declarations;
  instrument ambiguity; sensitivity-only and single-exposure hard negatives; independent robust-
  estimator/LD-whitening coexistence; the four-cell instrument/estimator regression; the fresh and
  prior independent MVMR reports; and four public-repository audit/replay controls.
- **Acceptance criterion satisfied:** a fresh answer-isolated persistent workflow demonstrated the
  general estimator-choice obligation beyond the evaluation-side design source; the finite
  controls, six independent negative repositories, existing MVMR sibling, audit, and replay all
  preserve zero Findings and no project execution. A separate fresh-context skill user also
  retrieved the exact estimator, dosage, and explicit-report technical-group questions and
  choices, retained each unknown, and completed byte-stable model-free replays. A third
  answer-isolated workflow exposed a distinct adjustment-set choice, and its finite controls plus
  eight unrelated or sibling workflows preserved zero false questions and Findings. Without an
  explicit final-report designation, the skill asks for publication-surface selection instead of
  guessing. A fresh covered-good QTL workflow independently repaired founder orientation and
  passed both answer fields; the bounded grammar repair connects its natural report wording without
  changing the scientific choice or creating questions in three independent QTL repositories. A
  fresh-target skill run exposes the exact two orientation choices plus retain-unresolved and
  replays byte-identically without answering. Two independently authored CRISPRi/CasRx reports
  now expose the same atomic paired-bridge location-alignment choice under different surrounding
  policies; finite controls prove that ordinary centering and unrelated repositories do not
  inherit the question. The new pulse-admixture workflow reconnects natural called-length wording
  to the existing exposure-universe question without adding a scientific rule; a fresh-target
  skill run reaches that one question, retains scientist authority, and replays byte-identically.
  Two independently authored carrier reports now expose opposite sides of one atomic direct-
  standardization conditioning-set choice. Ten unrelated or sibling workflows inherit no new
  question, and a fresh-target skill run reaches the exact choices, stops without answering, and
  replays byte-identically.
  One-change carrier conditioning repairs both previously missed carrier outputs, and the staged
  population-genetics ablations separate the fraction-label cause from the pulse-timing cause.
  Accepted ADR-0023 prevents the audit from mistaking the ancestry-fraction denominator for the
  pulse-time exposure while preserving one closed, scientist-governed timing question. The
  CRISPR paired-offset ablation repairs only the neighbor effect; the combined repair moves all
  fields within contract, and the one-axis reverse control independently moves the transcript
  effect back outside tolerance. Accepted ADR-0025 therefore adds only the atomic CasRx axis
  question. The structural direct/group-specific calibration moves all four fields within contract,
  while pooled-direct and stratified-posterior reverse controls remain outside. Accepted ADR-0024
  adds direct continuous calibration as a third dosage representation without conflating it with
  pooling policy. Five sibling workflows inherit no dosage question, and every audit/replay pair
  remains zero-Finding and byte-stable for its semantic lock and report. The carrier constrained-
  cell ablation repairs its two remaining fields, while cellwise unconstrained inversion exactly
  reproduces the original failures; the repaired report reaches the already admitted estimator
  question and both controls replay byte-identically with zero Findings. The ambient-state 2-by-2
  shows that recovered-group inclusion and corrected-marker scale interact: neither one-change arm
  passes, while their combination does. All three reports reach only the existing technical-group
  question and replay byte-identically with zero Findings. The TXR1 2-by-2 proves that target
  reconstruction and missing-outcome strategy are independently necessary in the fixed case:
  neither one-axis repair passes all outputs, while the combined repair does. Accepted ADR-0026
  adds two separate question-only modules; all four reports project the expected operand pairs and
  replay byte-identically with zero Findings. The fresh Wright-Fisher workflow recurs the earlier
  symmetric-average choice and misses only the coefficient after choosing the correct locus;
  accepted ADR-0027 now exposes that measurement-model choice in both independently written reports
  with zero Findings and byte-identical replay. The fresh Hi-C workflow reproduces the earlier
  same-distance failure on byte-identical inputs. It now reaches ADR-0018's bounded, claimless
  expected-count question because the report itself demonstrates changed requested values under
  target exclusion. The output remains a question—not a benchmark-specific method rule, conflict
  candidate, or Finding—and a non-Hi-C portability set proves that the role binding is not tied to
  the GeneBench output names.
  A second independently authored pulse-admixture workflow exactly recurs the earlier label,
  transition-path, and timing-exposure failure. The fresh 2-by-2 proves that transition continuity
  and full-map exposure are separate and jointly necessary in the fixed case. The original fresh
  report now reaches two atomic scientist questions, while the combined repair moves all four
  fields within contract and reports the opposite operands. A third independently authored
  ambient-state workflow repeats the two-axis interaction: neither activation-scale-only nor
  technical-group-only repair enters the exact tolerance, while their combination does. The
  bounded ADR-0030 connectivity repair exposes the existing technical-group question only in the
  two reports that explicitly include that group and leaves the untouched and scale-only reports
  question-free.
  The second fresh TXR1 workflow retains two unsupported representations and fails all numeric
  fields; its fixed two-by-two shows that the reference target explains most of the discrepancy
  while baseline-only assessment weighting does not repair the fresh AIPW result. ADR-0031 adds
  only report connectivity for the two already accepted questions. The fresh MVMR two-by-two then
  separates phase-split instrument construction from residual-heterogeneity response: neither
  marginal screening nor robust LD-whitened fitting alone passes, while their combination passes
  both fields. ADR-0032 admits those two atomic questions without selecting a method, preserves
  LD-whitening as a third independent question in robust cells, and leaves three public MVMR
  repositories question-free while MR-tutorial retains only its existing covariance question.
- **Remaining limitations:** the adapter covers two exact Markdown report declarations, not source
  code, general prose, non-Markdown formats, or all constrained prevalence estimators. It cannot
  decide which estimator is scientifically governing, prove that either ran, or attribute a
  numeric mismatch. The dosage adapter recognizes three explicit representations but cannot choose
  among them, validate calibration, infer pooling or stratification, or connect the earlier hard-
  call source to its report without a typed source-to-analysis join. The
  technical-group adapter requires an explicit selected-report declaration and recognizes only
  finite named or `that`/`it` inclusion forms. It cannot validate a reconstructed group's
  scientific meaning, infer confounding, choose an adjustment set, or recognize arbitrary co-
  reference. Fresh
  local agents are not authenticated independent reviewers, and GeneBench is public-development
  material, so none of these modules qualifies or promotes a detector. The expanded founder report
  grammar still recognizes only one explicit sentence relation and cannot establish that the
  reported repair executed or that its particular orientation algorithm is valid. The
  paired-bridge adapter covers one additive location-alignment relation only; it does not cover
  multiplicative scale, arbitrary calibration prose, or validate bridge comparability. The CasRx
  axis adapter recognizes two exact report declarations but cannot validate overlap measurements,
  decide that a non-dominant component exists, choose a threshold, or attribute a numeric mismatch.
  The pulse-time exposure grammar cannot detect label harmonization, validate
  ancestry calls, establish the governing timing definition, or cover the separately demonstrated
  transition-path continuity choice. The direct-standardization adapter covers only
  two explicit selected-Markdown declarations for direct cell standardization. It does not cover
  IPW, doubly robust transport, general missing-data models, cross-paragraph co-reference, validate
  exchangeability or positivity, choose a conditioning set, or attribute either numeric mismatch.
  The carrier ablation establishes one fixed-case numerical mechanism only; it does not prove that
  cellwise feasibility constraints govern another study, select a finite-sample bias policy, or
  turn the matching estimator declaration into a correctness certificate.
  The ambient decomposition found multiple target-equivalent state rules and only one fixed case;
  marker composition, normalization scale, and threshold selection therefore remain unsupported
  rather than becoming a benchmark-specific scientific check. The existing technical-group check
  cannot attribute the entire numeric miss or certify the surrounding state definition.
  The TXR1 adapters cover two explicit report operands per axis only. They cannot infer temporal
  order from source names, validate missingness identification, establish alteration multiplicity,
  select a clonality threshold, cover implicit or non-Markdown methods, or generalize fixed-case
  numerical causality beyond the released synthetic task.
  The phase-split MVMR adapters cover explicit selected-Markdown declarations only. They cannot
  validate instrument strength or exclusion restrictions, choose marginal or conditional signal
  construction, diagnose pleiotropy, validate the LD reference or SNP order, select a robust
  tuning constant, infer a primary method from sensitivity prose, broaden ADR-0021's R-Markdown
  covariance surface, or generalize the fixed-case numerical interaction.
  The directional-error adapter cannot infer which direction has the larger error rate, establish
  a baseline floor, validate an assay mechanism, or choose the governing operand. Its recurrence
  uses one public development task and therefore does not qualify a detector. The claimless
  expected-count obligation covers only two enumerated target-inclusive same-stratum mean forms,
  one conventional task-like Markdown naming convention, exactly three case/control/delta roles,
  and exact target-exclusion sensitivities. It does not parse general incomplete methods, choose a
  governing estimator, establish a tolerance or materiality, attribute the numeric mismatch,
  validate masking or covariates, or make the unsupported reported representation eligible for the
  experimental conflict detector.
  The transition-path adapter covers two explicit within-sequence retained-state declarations. It
  cannot infer latent states inside gaps, validate censoring or missingness assumptions, parse
  source data flow, or choose whether continuity should govern another scientific model. Its
  recurrence remains one public-development task and cannot qualify a detector.
  These remain question-only development modules with no detector qualification or Finding
  authority.
