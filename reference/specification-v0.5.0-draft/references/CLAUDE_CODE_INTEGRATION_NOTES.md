# Claude Code integration notes

**Verified:** 2026-07-27  
**Status:** Informative, not a stable product contract

Claude Code integration changes more quickly than the scientific audit core. The plugin implementation should recheck these facts during Milestone 5 and before each supported-release claim.

## Skills

Official documentation states that a directory-based `SKILL.md` can be invoked directly with `/skill-name`; skills can include supporting files, invocation controls, tool allowlists, and subagent execution.

Source: <https://code.claude.com/docs/en/skills>

Design implication: a standalone `scientific-audit` skill can provide the requested `/scientific-audit` entry point while delegating stateful work to the local controller.

## Plugins and MCP servers

Official documentation states that plugins can bundle MCP servers through `.mcp.json` or plugin metadata and that enabled plugin servers are started and exposed as tools by Claude Code.

Source: <https://code.claude.com/docs/en/mcp>

Design implication: the full distribution can bundle a typed local audit server while retaining a standalone CLI.

## Hooks

Official documentation describes plugin hooks and lifecycle-scoped hooks in skills and subagents. Hooks can invoke commands, prompts, agents, HTTP endpoints, or MCP tools, depending on event and policy.

Source: <https://code.claude.com/docs/en/hooks>

Design implication: hooks may validate non-scientific policy or record completion, but scientific correctness must not depend on a hook firing.

## Settings, permissions, and plugins

Official settings documentation describes skills, MCP servers, project/user subagents, plugin configuration, permission denials for sensitive paths, and managed policies that can restrict customization surfaces.

Source: <https://code.claude.com/docs/en/settings>

Design implication: deployment documentation must explain how organization policy can block project-local skills, agents, hooks, or MCP servers and how to use plugin or managed distribution where required.

## Subagents

Official documentation describes custom subagents as Markdown files with YAML frontmatter, custom prompts, restricted tools, permission modes, hooks, and skills.

Source: <https://code.claude.com/docs/en/sub-agents>

Design implication: workflow mapping, claim extraction, semantic resolution, and exact source-evidence verification can be isolated into bounded agents with least-privilege tools, but their outputs remain proposed records.
