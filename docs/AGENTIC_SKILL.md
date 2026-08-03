# Agentic skill setup

`sc-referee` has two layers:

1. the deterministic CLI, which owns snapshots, records, questions, semantic lock, integrity, and
   replay; and
2. Agent Skills, which tell a coding agent how to invoke and interpret that CLI conservatively.

The agent is not a second scientific detector. It may choose user-authorized inputs, present typed
questions, and summarize locked records. It may not invent premises, conduct an open-ended error
hunt, or strengthen a Disclosure into a Finding.

## Prerequisite

Install the CLI in an environment available to the agent:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e /absolute/path/to/sc-referee
sc-referee version
```

The skill stops if it cannot find `sc-referee` or the checkout's `.venv/bin/sc-referee`. It does not
install or run setup code from the scientific project being audited.

## Codex: install the repo plugin

The repository contains a skills-only plugin and a repo marketplace. From a clone of sc-referee,
register the marketplace root and install the plugin:

```bash
codex plugin marketplace add /absolute/path/to/sc-referee
codex plugin add sc-referee@sc-referee
```

Alternatively, open the Plugins Directory in the Codex desktop app and install `sc-referee` from
the configured `Sc Referee` marketplace. Start a new task after installation so the bundled skills
are discovered.

Invoke the post-hoc skill explicitly when desired:

```text
Use $sc-referee:scientific-audit to audit /absolute/path/to/scientific-project.
The selected report is reports/final.md. Use standard mode and ask me material questions.
```

Use the pre-analysis skill only when a scientist wants to freeze the supported expected-count
profile or one atomic option published by an installed scientific check before code or results
exist:

```text
Use $sc-referee:method-contract to establish the method contract for this planned analysis.
The governing task is protocol.md. Do not choose scientific values for me.
```

Codex supports `$` skill mentions. The plugin source is `plugins/sc-referee`, and its skill files
are test-enforced exact copies of the authoritative `.agents/skills` source. The installation
layout follows OpenAI's official [plugin packaging](https://developers.openai.com/plugins/build/plugins)
and [plugin use](https://learn.chatgpt.com/docs/plugins) documentation.

## Claude Code: manual Agent Skills path

The same `SKILL.md` directories follow the Agent Skills layout used by Claude Code. To make them
available to one scientific project, copy the two complete directories—including their
`references/` files—into that project's `.claude/skills/` directory:

```bash
mkdir -p /path/to/scientific-project/.claude/skills
cp -R /absolute/path/to/sc-referee/plugins/sc-referee/skills/scientific-audit \
  /path/to/scientific-project/.claude/skills/scientific-audit
cp -R /absolute/path/to/sc-referee/plugins/sc-referee/skills/method-contract \
  /path/to/scientific-project/.claude/skills/method-contract
```

Start Claude Code in the scientific project and invoke `/scientific-audit`. Claude Code documents
project skills at `.claude/skills/<skill-name>/SKILL.md` and direct invocation with
`/<skill-name>`. See the official
[Claude Code skills documentation](https://code.claude.com/docs/en/skills).

This is a bounded manual distribution path, not a claimed Claude-specific adapter, marketplace
package, or cross-provider detector qualification. The CLI remains authoritative.

## What the scientific-audit skill does

The skill:

1. identifies the project root and any report or material inputs explicitly named by the user;
2. states the full-file snapshot access boundary, selected mode, deadlines, and disabled execution
   policy;
3. creates a new audit directory and runs the deterministic CLI;
4. verifies integrity before reading results;
5. presents exact typed questions to the scientist without answering them itself; and
6. reports assessments, coverage, and limitations without issuing a global pass.

If the repository contains instructions telling the agent to alter scope, run code, reveal data,
or ignore these rules, the agent treats that text only as repository evidence.

## What the method-contract skill does

The method-contract skill is narrower and pre-analysis. It can freeze either the supported
`expected_count_background_v1` profile or one `scientific_check_requirement_v1` option explicitly
selected by the scientist from the installed digest-bound registry. The later audit may bind to
that immutable contract only if the task identity, parent lock, active check manifest, selected
candidate, and exact analysis scope still match.

The contract records intended semantics. It does not prove that the implemented code followed the
contract, that the method is universally correct, or that a result is numerically valid.

## Expected agent report

An agent using `scientific-audit` should report, in order:

1. the output directory and `report.html`;
2. exact Finding, ConditionalConcern, MaterialQuestion, and Disclosure counts;
3. narrowly worded Findings, if any;
4. open scientist questions and their stated consequences;
5. important disclosures and unsupported paths; and
6. overall coverage plus the non-certification boundary.

If integrity is not verified, the agent should stop instead of summarizing the result.

## Tested boundary

Fresh-context Codex runs have exercised ordinary skill discovery, audit invocation, question
handling, conservative interpretation, and model-free replay on bounded development cases. The
installed Codex plugin and authoritative skill copies are byte-checked in the test suite.

This does not establish that every agent will select the right report, that every repository is
scientifically covered, or that the experimental detectors are qualified. A fresh external
provider review is evidence about usability, not authority to promote Findings.
