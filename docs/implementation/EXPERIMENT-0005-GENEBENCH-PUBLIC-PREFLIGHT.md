# Experiment 0005: GeneBench-Pro public-package preflight

- **Status:** Active evaluation-private experiment; not qualification evidence
- **Date:** 2026-07-28; real-package run updated 2026-07-29
- **Scope:** Non-executing local verification of one pinned public case-study package

## Purpose

Prepare the accepted answer-blind artifact protocol for a real public package without downloading
the full corpus into this repository, executing its grader, exposing ground truth to an agent
workspace, invoking a model, or representing public examples as held-out qualification evidence.

## Verified upstream baseline

The full official package was downloaded to temporary storage and preflighted on 2026-07-29 at:

- source: `https://huggingface.co/datasets/openai/genebench-pro-public-package`;
- full revision: `8bb6cde6ab0b0554e867c46f5698fd953bf2c68a`;
- package version: `2026-06-26`;
- 10 public problems and 77 checksum-covered files;
- manifest digest:
  `sha256:72933560e3c3b633f11e3b68baa1c0844a7bf49ae4ba8a8f7b9a76f73ac7b556`;
- checksum-inventory digest:
  `sha256:49fe745725bfa98e132e72bc5ecad980d93267f634ec37ae34e2b609059bf760`;
- verified payload: 16,163,815 bytes;
- license projection: consistent `cc-by-4.0` metadata and `CC-BY-4.0` license file; and
- preflight digest:
  `sha256:e7c1ad20c4e70625bb68a9f50a2062029e0f96bf1bd254ed08dca313cc9f4685`.

The preflight admitted this immutable baseline only for public-development preparation. It made no
legal conclusion, granted no redistribution permission, did not execute the grader or any project
code, and did not invoke a model. The package remains outside this repository.

The official repository's then-current revision
`eb75a3c0996b3cedcc9af685bad02fd166848fa2` was also acquired and tested. Its dataset card and
LICENSE both identify MIT, but its tracked checksum inventory contains stale digests for both
files. Preflight rejected it at `LICENSE` checksum drift. sc-referee does not waive or repair
upstream integrity assertions; a later commit must be independently pinned and reverified before
it replaces the valid baseline.

## Exact envelope

`sc-referee-eval preflight-genebench-public` consumes an already-local package plus one full source
revision and separately supplied full digests for `manifest.json` and `checksums.sha256`. It:

- requires a real, non-symlink package directory and keeps its output outside that directory;
- parses strict UTF-8 JSON with duplicate-key rejection;
- validates the closed package, layout, problem, file, and eval-config shapes observed at the
  pinned release;
- rejects unsafe paths, symlinks, special files, missing files, unexpected files, duplicate or
  unsorted checksums, byte-size drift, digest drift, UUID/ID drift, and self-consistent config
  contract changes;
- streams full SHA-256 verification of every declared file without deserialization;
- reads task, ground truth, and grader configuration runner-side but emits only task, ground-truth,
  and grader digests—never ground-truth values;
- emits exact visible data identities and a plan that exposes only derived `task.md` plus the
  declared problem data files;
- marks eval config, ground truth, grader, reference report, and reference grader runner-only;
- identifies metadata/LICENSE consistency without deciding legal permission;
- marks the preflight report itself answer-side and ineligible for an agent workspace;
- fixes the maximum corpus partition to `public_development`; and
- records `project_code_executed:false` and `model_invoked:false`.

The implementation never imports or executes `reference_grader.py`. It does not create the blind
workspace yet; the accepted immutable snapshot/workspace builder remains the later boundary.

## Safety boundaries

- Public ground truth and reports create possible model-training contamination. These cases can
  validate mechanics but cannot be held-out or promotion evidence.
- A supplied revision is not a retrieval receipt. A later external-evidence path must bind the
  revision to the verified payload digests.
- Structural preflight does not establish scientific correctness, reviewer identity,
  independence, execution, a fixture label, a detector score, or a Finding.
- A package revision with stale self-declared checksums is rejected even if its visible license
  metadata is otherwise consistent.
- Platform metadata `.DS_Store` and a local `.git/` directory may be ignored and are disclosed;
  every other unexpected file fails closed.

## Exit evidence

- `test_public_corpus_preflight_is_answer_blind_nonexecuting_and_public_only` verifies the exact
  answer-side/public-development boundary and proves a malicious synthetic reference grader is not
  imported or run.
- `test_consistent_license_allows_only_public_development_preparation` verifies that even a
  consistent license cannot grant held-out status.
- `test_public_corpus_preflight_rejects_stale_license_inventory` reproduces the observed failure
  class and verifies that a post-inventory license edit cannot enter preparation.
- `test_public_corpus_cli_is_canonical_write_once_and_model_free` verifies the isolated CLI,
  deterministic canonical output, write-once behavior, and model-free replay.
- Mutation tests reject payload drift, symlinks, unexpected files, unsafe paths, a self-consistent
  answer-side config expansion, weak revision identity, digest drift, and output inside the source
  package.

## Remaining limitation

The valid 16.2 MB baseline has passed preflight, but no case workspace or agent-produced workflow
exists, no reviewer has been invoked, and no project code has executed. The current upstream head
is unusable until its checksum inventory is repaired. Any public case run remains
public-development evidence and cannot qualify or promote a detector. Accepted ADR-0017 also keeps
sc-referee's own project-code executor outside the MPP; an external agent may produce a workflow,
but the auditor remains non-executing.
