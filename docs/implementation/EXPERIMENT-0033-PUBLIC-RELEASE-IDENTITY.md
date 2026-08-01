# Experiment 0033: Public release identity

## Decision

The project owner authorized program version `0.3.0`, named Alexander King as the sole human
author, requested acknowledgment of OpenAI Codex and Anthropic Claude as AI development
collaborators, and authorized the overhaul pull request to replace `main` after all release gates
pass.

## Scope

This record changes release and attribution metadata only. It does not alter record meaning,
schema version, detector maturity, Finding admission, model authority, scientific coverage, or
project-execution policy.

The legal and citation author is Alexander King. Codex and Claude are acknowledged transparently
as AI development systems rather than described as human or legal authors. Their participation
does not establish any scientific premise or detector qualification.

## Acceptance criteria

1. The package, CLI, handoff manifest, public documentation, and evaluation dependency agree on
   program version `0.3.0`.
2. `CITATION.cff`, package metadata, NOTICE, and plugin metadata identify Alexander King as the
   human author or developer.
3. `ACKNOWLEDGMENTS.md` credits OpenAI Codex and Anthropic Claude while denying human, copyright,
   and independent-scientific-authority implications.
4. The plugin details metadata links to the public GitHub repository.
5. The prior public implementation remains available through Git history without a compatibility
   claim.
6. All local release gates and both hosted Python 3.11–3.13 matrices pass before merge.

## Tests added

`tests/test_release_identity.py` verifies the coordinated version, citation, authorship,
acknowledgment, and repository-link contract. Existing distribution and plugin tests verify the
CLI version and visible plugin metadata.

## Remaining limitations

- A GitHub merge is not a PyPI publication, signed artifact, DOI, or W3ID deployment.
- AI acknowledgment records development assistance, not a reproducible allocation of every line
  or decision to one system.
- Experimental real-project detectors remain Disclosure-only and unqualified for Findings.
