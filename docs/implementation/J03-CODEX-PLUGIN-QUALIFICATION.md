# J03 Codex plugin qualification

## Scope

The repository contains a Codex plugin package at `plugins/sc-referee`. It is a distribution
surface for the already qualified `scientific-audit` skill, not a new scientific inference layer.
The plugin invokes the installed deterministic `sc-referee` CLI through the skill protocol. It
does not bundle an MCP server, execute project-authored code, or alter a public schema.

The manifest intentionally contains no homepage or repository URL. Compatibility with the legacy
public GitHub implementation is not a design input for this overhaul.

## Acceptance evidence

- The plugin-creator `validate_plugin.py` validator accepts the manifest and component layout.
- The skill-creator `quick_validate.py` validator accepts the packaged `scientific-audit` skill.
- `tests/test_codex_plugin.py` validates the bounded manifest surface, strict semantic version,
  absence of legacy repository metadata, starter-prompt limits, and the installed-CLI dependency
  disclosure.
- The same test requires every packaged skill file to be byte-identical to the authoritative
  `.agents/skills/scientific-audit` copy, preventing behavior or epistemic-policy drift.
- Existing agent-protocol and fresh-context J01 evidence exercises the exact skill contents through
  question, proposal, human Answer, semantic lock, status verification, and model-free replay.
- The default personal marketplace was created with the plugin-creator scaffold, the validated
  repository package was copied into its declared source, and `codex plugin add
  sc-referee@personal` completed successfully.
- `codex plugin list` reports `sc-referee@personal` as `installed, enabled`; the current validated
  development cachebuster is recorded in `plugins/sc-referee/.codex-plugin/plugin.json`.
- Recursive byte comparison shows both the personal source and Codex's installed cache are exact
  copies of the validated repository package; the cached manifest and skill validators also pass.
- After the user quit and restarted Codex, the new task's discovered skill catalog included
  `sc-referee:scientific-audit` at the installed personal-cache path. This is direct fresh-task
  discovery evidence rather than an inference from `codex plugin list`.

This satisfies J03's Codex surface: a reusable plugin package is validated, installed, and
fresh-task discovered without changing scientific meaning.

## Remaining limitations

- The plugin depends on an independently installed `sc-referee` CLI; it does not install the Python
  package or execute setup code automatically.
- No MCP server, Claude adapter, public marketplace, signing, publication, or legacy-repository
  compatibility is claimed.
