# Experiment 0014: GeneBench answer-side method-contract diagnostic

- **Status:** Active evaluation-private experiment
- **Date:** 2026-07-29
- **Governing decision:** Accepted ADR-0018
- **Scope:** Non-executing post-lock comparison of one production-reported method profile with one
  exact public-development benchmark reference profile

## Purpose

Test whether the experimental method-contract detector can localize the already graded GeneBench
method mismatch without inserting answer-side knowledge into the original production audit. This
is diagnostic evidence only. It does not turn the public benchmark reference into production
scientific intent, a Finding, a fixture label, a metric input, or detector-promotion evidence.

## Experimental envelope

`sc-referee-eval diagnose-genebench-method-contract` consumes:

- one terminal, integrity-verified production audit with zero Findings and verified absence of
  post-lock model access;
- exactly one expected-count quantitative Claim and its structurally verified reported profile;
- the production method detector's original `insufficient_semantics` result;
- one complete answer-side `expected_count_background_v1` reference profile with a durable
  identifier and SHA-256 content digest;
- one timestamp after the original semantic lock; and
- one absent output path.

The diagnostic creates an in-memory evaluation copy of the Claim contract, projects the supplied
reference profile into six evaluation-only intended assertions, and runs the same manifest-bound
experimental detector. It never writes those assertions to the production audit, changes the
production semantic lock, executes project code, invokes a model, or reads benchmark numeric
answers. Its output is canonical, self-digested, create-only, public-development-only, and denied
metric, held-out, and promotion eligibility.

## Real validation result

The post-ADR pre-answer audit of `/private/tmp/genebench-hic-agent-workspace` produced:

- audit run `audit:b7ad8d82d9e2436a8197cdc70656ced7`;
- semantic lock
  `sha256:fd18a3f120d638cc34dc1888c7f2be8dcf867243ef1e263f74aadf5097370456`;
- one exact quantitative Claim;
- one open question asking which expected-count/background profile governs;
- one method DetectorResult in `insufficient_semantics`;
- zero Findings, zero model calls, and verified no post-lock model access.

The separate answer-side diagnostic produced
`genebench-method-contract-diagnostic:2b8890f21432f5e97bbd`, digest
`sha256:5237ac725742e51e8c26e63eb670342c06816d37c1a9c9df7a15a294d8c03123`. It localized exact
inequality between the report's `same_stratum_arithmetic_mean` profile and the supplied benchmark
`negative_binomial_glm` profile as `evaluation_finding_candidate`. The production audit remained
integrity-verified with the same lock digest and zero Findings.

## Epistemic boundary

The reference method is the benchmark scoring contract available after semantic lock. It does not
show that the visible task uniquely specified that method or that the method is universally
scientifically correct. The candidate does not establish which code ran, why the numeric values
differed, or whether any other issue exists. Public benchmark exposure also prevents this case from
establishing independent qualification.

## Exit evidence

- A pre-answer regression emits the bounded governing-background question without naming the
  hidden reference method.
- The post-lock diagnostic emits one exact evaluation candidate and no Finding.
- Production bundle and semantic-lock bytes remain unchanged.
- Output replacement, malformed reference identity, nonterminal or post-lock-model audit,
  nonzero-Finding audit, missing reported profile, resolved production detector, partial profile,
  and pre-lock chronology fail closed.
- A non-Hi-C copy-number read-depth portability set covers positive, covered-negative, ambiguity,
  and hard-negative states while retaining the experimental nonproduction ceiling.

## Remaining limitations

This is one public-development case and one first-slice expected-count profile. It is not an
answer-blind external review, a qualification panel, a Stage-3 equivalence result, a metric set, or
a promotion decision. Broader method families and non-genomic analysis resolutions remain
unsupported.
