# Nonblocking implementation defaults

These are approved **trial defaults** for the implementation starter. They keep coding unblocked while preserving the open-decision process.

| Topic | Trial default |
|---|---|
| Claude command packaging | Standalone `/scientific-audit` alias plus namespaced plugin command where required |
| Interactive protocol | Typed MCP adapter plus canonical CLI; implement CLI first |
| Bundle signing | Manifest is signable; key management and mandatory signing deferred |
| Telemetry | None by default; future telemetry must be explicit opt-in |
| False-positive feedback | Later local, user-reviewed redaction/export tool; never automatic upload |
| Numeric detector thresholds | Deferred until the pilot corpus; accepted safety gates remain mandatory |

A coding agent may implement against these defaults but must not represent deferred items as final public policy.
