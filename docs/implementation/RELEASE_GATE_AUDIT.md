# Release-gate audit

## Current gate snapshot

The current first vertical slice passes the complete local handoff under isolated Python 3.11.15,
the project Python 3.12 environment, and isolated Python 3.13.13:

- editable install and console entry point;
- Ruff lint and format check;
- strict mypy over `src`;
- the full test suite;
- immutable accepted public schema validation through active v0.19.0, with v0.18.0 retained as an
  immutable migration baseline;
- starter validation and storage-integrity checks;
- immutable-snapshot demo;
- model-free replay of derived assessments; and
- byte-identical replay of AssetIdentity, Operation, Artifact, and ObservedResult JSONL;
- deterministic report-byte regeneration as part of integrity status; and
- deterministic attached RO-Crate 1.3 export with native-byte preservation and bounded offline
  validation from the built production wheel; and
- deterministic generation and exact reproduction of the fail-closed 16-entry public capability
  matrix from the built production wheel, with explicitly experimental, unqualified,
  Finding-ineligible detector entries and no tested-version, inferred-compatibility,
  qualification, or domain-wide support claim in the bundled release set.

The draft replacement branch also passes hosted GitHub Actions for Python 3.11, 3.12, and 3.13 on
both push and pull-request events. Every job performs installation, Ruff, formatting, strict mypy,
the complete test suite, starter validation, walking-skeleton artifact generation, and artifact
upload where configured.

The demo remains explicitly synthetic. It rejects repositories without `fixture_mode: true`, and
its fixture qualification envelope says that no public detector qualification is claimed.

## Gate status details

### ✅ A01 / H05 — hosted Python release matrix

Satisfied on the draft replacement branch. Hosted push run `30683312102` and pull-request run
`30683313655` both completed successfully on Python 3.11, 3.12, and 3.13. The first hosted attempt
exposed an undeclared NumPy typing boundary; the direct `numpy>=1.26,<2.5` dependency and its
regression test corrected that packaging defect before the successful matrix.

### D01 / E01 — local public observed-plane schema release

Satisfied locally. The repository owner accepted ADR-0002 at exact version `0.6.0`. The immutable
package adds `AuditRun`, `StageResult`, `FileRecord`, `Operation`, `Artifact`, and `ObservedResult`
together with the catalog, record union, required AuditBundle arrays, 50 examples, 58 package
tests, migration note, and exact manifest. Runtime persistence no longer uses provisional schemas.

The walking skeleton emits and validates the six public record types directly. Model-free replay
preserves file, operation, artifact, observed-result, and identity bytes without inventing a second
execution history. Public v0.5 bundle migration leaves the new arrays empty and drops the stale
StorageManifest instead of synthesizing evidence. The immutable v0.5 package remains unchanged.

Still external: deploy the v0.6.0 identifiers at W3ID and obtain hosted conformance evidence if and
when publication is authorized. Local package generation does not claim that deployment occurred.

### I05 / J02 — local typed semantic interaction release

Satisfied locally. The repository owner accepted ADR-0004 and schema `0.7.0`. The package adds
WorkItem and Answer records, three pre-lock AuditRun states, required bundle arrays, 54 examples,
invariant tests, and a fail-closed v0.6→v0.7 migration. The linked CLI protocol recaptures the exact
snapshot, validates model proposals against packet/prompt digests and source bytes, preserves
model/scientist conflicts, rejects post-lock submissions, and replays without model access.
The next linked segment can resolve any bounded subset of the 17 ScientificContract dimensions as
accepted but Finding-ineligible scientist intent while leaving omitted dimensions and observed
lineage independent of those declarations. Active experiment 0002 can reconstruct one exact
Python/CSV mean-difference result and partial Claim lineage, but it retains the unobserved
project-execution and claim-specific report-generation boundaries and does not establish detector
applicability. An exact whitelisted result-Artifact flow may reach a literal report writer either
directly or through at most eight ordered, uniquely bound, top-level assignments as static source
evidence without closing either boundary.

Independent fresh-context qualification of the repository skill now passes, and its exact contents
are packaged in a repository-contained Codex plugin that passes local manifest and skill
validation. The qualification environment reports that personal plugin installed and enabled, with
its installed cache byte-identical to the validated source; a post-restart fresh task discovered
the namespaced skill. Still external: W3ID deployment and any cross-provider qualification. An MCP
transport and broader observed-lineage profiles are later work, not implied by this local protocol.

### F01 — real detector qualification

The fixture test double cannot truthfully be promoted. Accepted ADR-0037 requires at least four
independent Stage-1 blind reviews (two per provider family) and two fresh Stage-2 adjudications
(one per provider family), with exact prompt, tool, environment, model, context, and transcript
identities. ADR-0042 also requires a held-out corpus, verified-good and hard-negative controls,
decisive counterevidence, clustered uncertainty, disagreement exclusion, public reporting, and a
pilot-informed numerical-threshold ADR before the first validated promotion.

Required evidence and authority: the cross-provider blind review corpus, reconciled adjudication
records, maintainer approval, public qualification report, and accepted numeric-threshold ADR.
Fabricating placeholder reviews, treating this implementation run as an independent review, or
using the public walking-skeleton development fixture for qualification would violate the
accepted protocol.

The new isolated `sc-referee-evaluation` package is infrastructure only. Accepted ADR-0008 and
public schema v0.9.0 add recomputed review-local candidate identities, exact fresh Stage-2
membership reconciliation, and public `AdjudicatedRootCause` records. The deterministic packet
validator reconciles linked 4+2 panel records, providers, independent contexts, chronology,
dissent, canonical root references, and fixture-label compatibility; the production wheel contains
none of its code. A positive scientific label is admitted only for the declared fixture scope after
both canonical root reconciliation and immutable source checks pass. It independently resolves
full-digest file-span evidence against immutable fixture records and
bytes and can build a fresh allowlisted blind-review workspace after exact path, digest, marker,
hidden-file-content, and symlink checks. Markers and full hidden text are checked across bounded
UTF-8/UTF-16 and Unicode/newline-normalized variants. The scanner explicitly cannot detect
paraphrases, partial transformations, compression, encryption, or undisclosed answer-side content.
Digest-bound Stage-1 and Stage-2 packets now enforce the 2x2 plus
1x2 provider structure, fresh contexts, falsification records, and label-before-detector freeze
chronology. The isolated CLI now constructs every artifact in that chronology and validates the
completed case without making model calls or executing project code. It can deterministically
create and model-free replay the root-bound scientific-label freeze. Canonical JSONL, disposable
SQLite, AuditBundle validation, and report rendering preserve the root record without turning it
into a Finding. Accepted ADR-0009 through ADR-0012 plus public v0.10.0/v0.11.0/v0.12.0 now close
Stage-3 detector-to-root equivalence, the experimental-only Finding-shaped result state, exact
per-DetectorResult opportunity projection, all twelve point-estimate formulas, and the deterministic
problem-cluster bootstrap. The isolated CLI projects and replays candidates, reconciles exact case
outcomes, and calculates and byte-replays metric sets without model calls. Production reports
independently recompute all input digests, exclusions, counts, ratios, and intervals and disclose
agent-panel review as non-human-expert. Promotion remains prohibited and thresholds remain
deferred. Neither schema-valid examples nor structurally consistent synthetic protocol packets are
qualification evidence.

The immutable v0.9.0 package contains 63 examples and a reproducible release manifest. Its
v0.8-to-v0.9 migration derives review-local Stage-1 IDs only from exact existing content, demotes
legacy Stage-2 demonstrated reviews and positive adjudications to insufficient evidence, converts
legacy positive fixtures to ambiguous, and invents no reconciliation set or canonical root.

The CLI capture boundary now retains canonical review and packet records plus exact transcript
bytes in a write-once self-digested directory, and later CLI freezes require those captures.
Capture proves byte identity and packet consistency only; it does not authenticate authorship,
provider identity, or independence, and it does not stand in for real cross-provider reviews.

Experiment 0004 adds one exact, non-executing JSON value grader over a fully reconstructed
content-addressed snapshot manifest. Its match/mismatch output is deliberately not metric-eligible:
final-value agreement does not establish scientific validity, and disagreement does not establish
a demonstrated issue. No general grader or clean-execution evidence pipeline is claimed.

Fixture generation is likewise fail-closed. An excluded adjudication emits only an
`ambiguous_fixture` with no satisfied proof obligation. Complete public-development positive,
verified-good, scope-verified-good, and hard-negative fixtures require the exact accepted v0.12.0
proof projection over captures, packets, transcripts, workspaces, snapshot, freezes, public
records, and chronology. Clean verified-good and hard-negative fixtures additionally require a
supplied successful authorized project-workflow Execution and qualifying rootless-OCI
SandboxCapability. Construction validates those existing records but never launches project code;
subprocess, auditor, failed, network-enabled, unsafe-fallback, unresolved-scope, and evidence-drift
cases fail closed. Stage 3 replays the private proof inputs before metric admission, metrics bind
the exact fixture digest and status, and reports re-resolve bundled public proof records. This is
synthetic mechanism evidence, not external reviewer independence or detector qualification.
The v0.14 proof cannot bind the complete linked execution dependency closure, and v0.14 launch
admission cannot prove that standalone capability JSON came from a trusted controller-run probe or
that its user-selected digest-pinned image was auditor-owned. Accepted ADR-0017 defers the built-in
executor beyond the evidence-first MPP. Experiment 0023 also proves that v0.14.0 cannot admit a
complete non-executing verified-good or hard-negative control. Accepted ADR-0022/schema v0.15.0
now adds distinct static control kinds plus an independently implemented raw-byte proof. Its
synthetic construction, chronology, mutation, stratified-metric, report, and replay gates pass
without executing project code. Deferred ADR-0015 and
ADR-0016, or equally conservative successors, keep real launch and execution-dependent
clean-control admission unavailable until both gaps are closed. Static detector qualification
also remains unavailable pending real answer-blind cross-provider controls, pilot-informed
thresholds, and maintainer promotion. None of this blocks static audit, bounded inspection of existing
evidence, or detector implementation under the experimental maturity ceiling.

Evaluation-private Experiment 0005 adds a non-executing preflight for one already-local, exact
revision of the GeneBench-Pro public package. Synthetic tests prove that the preflight verifies a
closed manifest/checksum/config envelope without importing a deliberately malicious reference
grader or emitting its ground-truth value. The full official initial revision has now passed all
77 declared hashes with consistent CC-BY-4.0 identifiers and is admitted only for
public-development preparation. The current MIT-labelled head is independently rejected because
its checksum inventory still names earlier LICENSE and README bytes. sc-referee grants no
redistribution authority and does not repair the upstream package. Public answers cap these cases
at `public_development`; they cannot satisfy the held-out qualification gate.

Evaluation-private Experiment 0012 now turns one admitted case into a separate agent-eligible
workspace containing only derived task text and the exact staged data allowlist. Its config,
canonical ground truth, grader, reference report, immutable source snapshot, and receipts remain
runner-side. An authorized fresh-context agent produced and twice reproduced a workflow, which was
then audited and replayed before runner-side answers were reacquired. Experiment 0013's
non-executing grade records all three output fields outside tolerance. After accepted ADR-0018, a
new pre-answer audit extracts the exact quantitative Claim and reported background, asks which
background governs, and retains zero Findings. Experiment 0014 separately supplies the public
answer-side reference profile and localizes the exact method conflict as an experimental candidate
without changing production evidence. Experiment 0015 adds three more isolated runs: MVMR passes,
while Wright-Fisher and carrier-risk expose distinct answer-side root causes after their zero-Finding
production locks. The new grades remain public-development observations, and neither one-case
failure family defines a production rule. Experiment 0016's four closed static probes localize the
exact source forms and its fixed-case ablations recover the released answers, but the answer-side
obligations, single positives, and narrow Python grammars remain ineligible for production Finding
authority or qualification. Experiment 0017's three targeted follow-ups preserve all twelve prior
profiles as unsupported and reveal three different one-case method families; this is evidence
against broadening the existing grammars, not qualification evidence. No authenticated reviewer
panel or Stage-3 comparison has run, and the public cases remain ineligible for held-out
qualification or promotion.

Experiment 0018 completes the remaining three public-development cases. All three answers miss at
least one contract field, all three production audits retain zero Findings, and all twelve
applications of the four existing static profiles return `unsupported_path`. Across the complete
ten-case sweep, one workflow is wholly within contract and nine are not. These cases demonstrate a
working isolation and replay harness plus inadequate contract-free scientific localization; they
do not constitute an accuracy estimate because the corpus is public and the agents are
unauthenticated. An interactive post-hoc review workflow with bounded scientist clarification is
now the accepted next milestone and is specified in accepted ADR-0019. Experiment 0019 implements
the closed ledger and fixed-workspace evaluation slice: QTL and pulse-admixture yield exact review-
scoped conflicts, MVMR yields a covered negative, and CRISPRi/CasRx remains explicitly unknown.
Every result is non-executing, model-free, and Finding-ineligible. A synthetic false-self-
compliance control passes without granting a report declaration execution authority. Experiment
0020 completes the fresh-context raw-repository skill run: the agent uses the skill and replays
correctly, but the production audit emits no Claim, contract, method assertion, or question, so the
required scientist interaction is blocked before it begins. Accepted revised ADR-0020 now supplies
that missing production path through one modular registry of method-level scientific checks and
language/tool adapters sharing one analysis-scoped question lifecycle. QTL, pulse-admixture, and
MVMR are marker profiles using the same controller seam, not case-specific controller branches;
a removable conformance module proves explicit `not_installed` coverage without changing
substantive module-local output. Independent fresh-context broad-design review reports no remaining
architecture blockers after the adapter/reducer contract, sibling isolation, and typed source-
scope join were made normative. A follow-up fresh-context QTL skill audit reaches one exact
scientist question with zero Findings and exposes the observation and finite choices in both agent
and HTML surfaces. The repository owner then selected repair-before-emission through the structured
Answer path. The locked segment records one exact review-scoped incompatibility Disclosure, zero
Findings, no open question, and no model access after lock; replay preserves semantic identity and
assessment counts. The pre-analysis `method-contract` remains optional. This implements an
experimental question-only extension seam; it does not improve detector maturity, qualified
capability claims, metrics, or Finding authority. Experiment 0021 adds six commit-pinned,
independently authored non-GeneBench QTL and robust-MR repositories. Their ordinary audits and
replays retain zero false questions and Findings; the closest lexical hard negative is explicitly
unsupported. This passes a false-applicability gate but not useful method portability because no
installed adapter produces an applicable independent observation. External covered-good
applicability and any public static-source-to-analysis join remained open at that boundary.
Accepted ADR-0021 and Experiment 0022 now close that bounded connectivity gate: the R Markdown
inventory, MVMR `gencov` adapter, and same-Artifact scope join produce one exact scientist question
on two independent applied repositories. Display-only code abstains, the unchanged public mixed-
operand vignette remains ambiguous, and a controlled mutation proves the provided-covariance
branch. The fresh-context skill reaches the question and stops. The selected report is now
prioritized within the unchanged immutable-snapshot byte budget after external validation exposed
its earlier starvation. All audits and replays retain zero Findings, zero project execution, and
zero model calls. General R/R Markdown support, the missing scientist sample-provenance Answer,
detector qualification, cross-provider answer-blind evidence, and Finding authority remain open.

## Exact release posture

The evidence-first vertical slice and practical-parity modules are locally executable and hosted-CI
verified. The project owner selected public-alpha version 0.3.0, fixed Alexander King as the sole
human author, acknowledged OpenAI Codex and Anthropic Claude as AI development collaborators, and
authorized the GitHub replacement after final green release gates. Citation, migration, and
Git-history archival presentation are present. A release tag and any W3ID deployment remain
separate publication operations.

Experimental real-project detectors still lack answer-blind cross-provider qualification and
maintainer promotion, so they cannot emit production Findings. That qualification is a capability-
promotion gate, not permission to hide the useful Disclosure-only audit behind a global
“incomplete” label. Built-in project-code execution remains post-MPP.
