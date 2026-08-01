# Controller state machine

## States

| State | Durable checkpoint |
|---|---|
| `CREATED` | Audit plan and run identity |
| `SNAPSHOTTED` | Immutable repository snapshot and manifest |
| `INVENTORIED` | File classification and candidate surfaces |
| `PARSED` | Parser records and explicit gaps |
| `SEMANTICS_LOCKED` | Accepted semantic records and lock digest |
| `DETECTED` | Detector results and admission decisions |
| `REPORTED` | Machine bundle, SQLite index, and HTML |
| `COMPLETE` | Integrity checks complete |

## Partial terminal states

- `PARTIAL_DEADLINE`
- `PARTIAL_HOST_LIMIT`
- `CANCELLED`
- `FAILED_CONTROLLER`

A parser error, unsupported construct, unavailable asset, or detector abstention does not imply `FAILED_CONTROLLER`; it becomes a record and coverage limitation.

## Transition rule

A transition is legal only if all outputs required by the source state are durable. Resumption creates a linked run segment; it never rewrites the original run history.
