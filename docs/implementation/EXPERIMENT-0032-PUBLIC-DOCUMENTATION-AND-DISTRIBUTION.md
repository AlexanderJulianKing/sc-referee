# Experiment 0032: Public documentation and local plugin distribution

## Question

Can the practical-parity overhaul be approached and exercised by a new user without reading the
internal ADR and experiment history, while preserving every conservative capability boundary?

## Scope

This is a documentation and distribution experiment only. It does not change record meaning,
schema version, detector maturity, Finding admission, model authority, project-execution policy, or
scientific coverage.

The experiment:

- replaces the implementation-inventory README with a user-facing entry point;
- adds quickstart, agentic-skill, capability, and migration guides;
- adds a repo-local Codex marketplace entry for the existing validated skills-only plugin;
- updates stale task-board and release-gate status after the successful hosted matrix; and
- adds executable documentation-contract tests.

The repo marketplace packages no new inference or tool. It points to the existing
`plugins/sc-referee` directory, whose skill contents remain byte-identical to the authoritative
`.agents/skills` directories.

The Claude Code instructions describe a manual copy of those same Agent Skills. This is not a
Claude-specific adapter, public marketplace package, or provider qualification claim.

## Acceptance criteria

1. A new reader can find install, demo, first-audit, status, question, replay, and limitation
   guidance from the root README.
2. Every local Markdown link in the public documentation resolves to a repository file.
3. Public guides state the whole-root snapshot byte-access boundary and no-project-execution rule.
4. Public guides do not describe zero Findings as a pass or correctness result.
5. The repo marketplace points to the exact existing plugin with explicit installation and
   authentication policy.
6. The published demo and general-static command sequence passes from a clean environment.
7. Ruff, format, mypy, pytest, starter validation, and hosted Python 3.11–3.13 CI remain green.

## Test added

`tests/test_public_documentation.py` verifies the public-document set, relative links, version and
non-certification language, required safety boundaries, and absence of the stale `1,211` test-count
claim. `test_codex_plugin_marketplace_points_to_the_validated_local_plugin` validates the generated
repo marketplace and its exact plugin target.

## Remaining limitations

- Documentation smoke tests cannot prove that every reader will choose the correct report or
  material inputs.
- Local Codex marketplace installation is not public-directory publication or signing.
- The manual Claude Code path is not independently packaged or continuously exercised.
- Documentation does not satisfy real detector qualification, W3ID deployment, citation identity,
  or the final public-version decision.

## Result

The acceptance checks pass. A fresh Python 3.11 virtual environment installed the package from the
draft worktree and completed the documented version, 79-example schema validation, synthetic demo,
demo status, demo replay, ordinary general-static audit with selected report/material input,
ordinary status, and ordinary replay commands. The ordinary audit retained zero Findings, one
MaterialQuestion, twenty Disclosures, verified integrity, disabled project execution, and
model-free replay.

The complete repository gate passes Ruff, format checking across 316 files, strict mypy across 105
source files, 1,216 tests, and starter validation. The authoritative source and draft GitHub
worktree documentation bytes are synchronized. Hosted CI must rerun on the documentation commit;
the previously green six-job matrix is not silently reused as evidence for changed bytes.
