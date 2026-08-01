# Specification review checklist

## Scientific safety

- Does every path from model interpretation to a Finding pass through exact-source validation and a non-model verification?
- Can any unknown, conflicted, unavailable, or unsupported premise accidentally become a negative result or a Finding?
- Does scientist authority resolve intended scientific meaning without rewriting observed computation or report wording?
- Are Findings, ConditionalConcerns, MaterialQuestions, Disclosures, and detector abstentions visibly and numerically separate?
- Does every Finding pass the five admission conditions and remain narrowly worded?
- Could any wording imply that zero Findings means the analysis is correct?
- Is open-ended model issue discovery absent from every production mode and tool path?

## Runtime and usability

- Does each audit mode have a user-visible scheduling cutoff, hard deadline, and explicit stopping policy?
- Are high-materiality validated checks scheduled before lower-value work?
- Can the controller return a valid partial report after timeout, cancellation, or component failure?
- Are repeated audits incremental and content-addressed?
- Are scientist questions limited to meanings that can change an assessment or affected claim?
- Can the scientist obtain a useful report without project-code execution or HPC submission, while optional dependency reconstruction remains isolated?

## Coverage and lineage

- Is the entire project inventoried even when deep inspection is selective?
- Does deep inspection include final-claim lineage and the selection envelope?
- Are opaque operations, unavailable data, parser failures, unsupported paths, and unqualified detector regions represented separately?
- Does every final claim have an exact source reference, Scientific Contract, and graded computational lineage?
- Are root Findings linked to all materially affected descendants without duplicate accusations?
- Does a negative detector result state precisely the coverage within which no issue was detected?

## Security

- Is project text treated as untrusted evidence rather than agent instruction?
- Does static inspection avoid importing, sourcing, deserializing, or executing project code?
- Are auditor-owned verification and explicitly authorized project-code execution sandboxed, logged, deadline-bounded, and incapable of writing outside permitted roots?
- Are Claude/controller network inquiry, project-code network authority, dependency reconstruction, and project-code execution represented as separate privilege classes?
- Are benchmark answer keys isolated from production packages and agent workspaces?

## Evaluation

- Are verified-good and multiple defensible workflows included?
- Are splits performed by scientific problem rather than workflow instance?
- Is the false-accusation rate for Findings a release-blocking metric?
- Are ConditionalConcerns and MaterialQuestions evaluated separately rather than counted as lower-confidence Findings?
- Are runtime, coverage honesty, abstention quality, and deterministic replay evaluated alongside root-cause detection?
- Is independent adjudication kept distinct from scientist disposition?


## Runtime-policy review

- Do model, queue, retrieval, installation, sandbox, execution, and rendering latency count toward the user-visible deadline?
- Do quick, standard, and publication defaults remain 120/300, 480/600, and 1500/1800 seconds?
- Is there no sc-referee numeric model-call or token cap while host limits and usage telemetry remain explicit?
- Does every material controller network retrieval have durable provenance?
- Can no repository instruction grant execution or network permission?
- Does an unresolved publication surface leave materiality unassessed rather than guessed?
- Do causal detectors distinguish estimand, identification, implementation, and report layers and respect partial-open-world graphs?


## Implementation-foundation review

- [ ] Product, import, CLI, slash-command, and schema identities are not conflated.
- [ ] The W3ID path is versioned and immutable.
- [ ] Apache licensing does not silently cover external benchmark derivatives.
- [ ] Detector promotion has the required independent roles.
- [ ] Python and R parser limitations are disclosed rather than hidden.
- [ ] SQLite can be deleted and rebuilt.
- [ ] Jinja output escapes repository content and is readable offline without JavaScript.
- [ ] Project execution has no subprocess-only fallback.
- [ ] Source-derived cache remains project-local.
- [ ] Workspace divergence never mixes live edits into the current snapshot.


## Agent qualification review

- Are at least two provider families represented and exact configurations pinned?
- Are Stage-1 reviewers blind to answers, grades, detector identity, sc-referee output, and other reviews?
- Are Stage-2 adjudicators fresh contexts and still blind to sc-referee output until label freeze?
- Does any material dissent exclude rather than majority-vote the case?
- Are agent-only labels disclosed without human-expert wording?
- Are verified-good and hard-negative proof obligations positive rather than based only on reviewer silence?
- Is the capability claim limited to the generated matrix envelope?
