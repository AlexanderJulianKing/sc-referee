# ADR-0075: Round-2 promotion-record re-derivation

- Status: Accepted
- Date: 2026-08-11
- Decision owners: sc-referee maintainers
- Scope: Round-2 evidence re-derivation and exact binding-scoped grant installation

## Context

ADR-0071 and ADR-0073 accepted binding-scoped promotion decisions using private Round-1
records. Acceptance of public schema v0.19.0 changed the schema-versioned detector-manifest
and binding digests. It also made the Round-1 private shapes unsuitable as active public-schema
qualification evidence. ADR-0074 separately ruled the complete-domain detector's non-blind
seven-case replay at the current adapter bytes into the existing qualification decision.

The maintainer's blanket approval for the Round-2 construction authorizes deterministic
re-derivation of both record sets. The subsequent Stage-6 approval installs only the two exact
binding grants. It does not change the shared detector's experimental maturity or authorize any
sibling binding.

## Decision under review

Retain each Round-1 `promotion/` directory as history and place the re-derived records in the
sibling `promotion-round2/` directory. The builders must replay the frozen ledger and authoring
protocol, read the active binding and detector identity, validate both outputs against the
active v0.19 registry, and fail closed on any sealed or live-identity drift.

The record digests constructed for review are:

| Binding | Qualification digest | Metric-set digest | Threshold-policy digest |
| --- | --- | --- | --- |
| complete-domain exposure denominator | `sha256:3a44dbdb144c152b7185c0dccc6bf855346093341324acfd443689982dd02dbe` | `sha256:50fda7205c683b49fc42351de25c7b98a46bd8ef62b7ca9379703c55e12e67a1` | `sha256:fcf27c8d4d315fe836e0d35356ecadc496be4e53b607617d18c8c4bd670efc80` |
| authorized independent-unit entry | `sha256:a9114559f7b4ba0b75d704f0b6ba746e2150a8cb32da0cf3e8a9e975c541f9ba` | `sha256:27ac7cc5d1112661cef27a88694fef711f62877213f791e44a614ff52953f1ed` | `sha256:92af51be5f6d5e5127337963025cf0932747b4a088e7376f6d22d9d68d0ff644` |

## Current pin table

| Field | Complete-domain | Dependence |
| --- | --- | --- |
| binding digest | `sha256:d67b3bb459c32f84f4d920cffc9b56ab68d96741932bf3771926070342ff94e2` | `sha256:56e8ccdef15d3c2371864e02cab92becb0c6859091ee782c94be2ac9b4b1a43d` |
| check manifest digest | `sha256:c3ef7acd8597c86e8a121ba43e94d4f2a2993c08cd2c14981b85b13c431841a9` | `sha256:4f48a3104693cd6cdcf215bd620b59449ee87c3cd969ddbe7285f168e598ab21` |
| detector manifest digest | `sha256:9c6270f47a2ab2d2a75183a9e4a2d2a955974e5968bacc2ba75778a1ae8ab3fb` | `sha256:9c6270f47a2ab2d2a75183a9e4a2d2a955974e5968bacc2ba75778a1ae8ab3fb` |
| exam/current adapter implementation | `sha256:cb6de94e39efdf726cc516178b77b85443044415b72c8671025ef9c2e6eef05c` | `sha256:d5d22803d309ddda51651bcc033cb3e5aa4e093988550fb489b7e9671e289c54` |
| exam/current adapter manifest | `sha256:231046e541e1e84671b7fe716a2454c67d2d931f1cfe432e7de80512987d3a20` | `sha256:81df54974a949648f6f86287df725c1a69ce63f41100480d299680f92eee3776` |
| recognition grammar | `sha256:c757692071a6925a5ca5e409dc0ad79f7421fcdbc93fb15c14efb30050524362` | `sha256:bb3b283145ec1420491771ca49fbd2214e553602a735af2a6f7027980c8be873` |
| qualification adapter implementation | `sha256:9b318abe37e34d7484c3d4f5bebad28f6e48e306bca9c0c8c8e6e42aaa432a0b` | `sha256:a8989baf0eba769aa1f458e36f73c99a409d73653d90d7f540f7742816c34c64` |

The complete-domain adapter identity is the HEAD identity ruled admissible by ADR-0074. The
dependence adapter identity already matches the sealed exam; its binding and detector-manifest
digests nevertheless moved when schema v0.19 became active.

## Field-by-field divergence from Round 1

| Record field or field family | Round 1 retained history | Round 2 re-derivation | Evidence meaning |
| --- | --- | --- | --- |
| `schema_version` | `0.19.0-round1-private` | `0.19.0` | Representation only. |
| `qualification_id` | suffix `round1` | suffix `round2` | Distinguishes the new record; no new exam. |
| detector and binding digests | exam-time/pre-v0.19 values | active v0.19 values above | Identity repin required by the schema flip. |
| qualification-adapter version/digest | Round-1 projector `1.0.0` | Round-2 projector `2.0.0` | Binds the public-shape/current-pin projector. |
| projected case `schema_version` and detector digest | private/exam-time | public/current | Changes input digests and therefore the derived `metric_set_id`; outcomes and labels do not change. |
| `qualification_proof_families` | `positive_issue`, `static_closed_scope` | `static_closed_scope` | Uses the closed v0.19 proof-family vocabulary; positive cases remain represented by metric evidence. |
| `agent_adjudication_refs` | evaluation paths encoded as strings | empty array | No adjudication `RecordRef` is invented. |
| `evaluation_refs` | absent | the same review and label ledger paths | Correct v0.19 channel for evaluation ledger paths. |
| `author_actor_ids` | absent | derived from the digest-replayed sealed authoring protocol | Provenance made explicit without new testimony. |
| `human_scientific_approvals` | absent | empty array | Agent-only review remains disclosed. |
| `software_maintainer_approvals` | flat private object | v0.19 `MaintainerApproval` with nested actor | Same Alex approval, date, and ADR decision reference. |
| `static_scope_disclosure.stage3_comparison_artifact_exists` | explicit false in retained records | explicit false | The accepted lean substitute is unchanged; complete-domain additionally cites ADR-0074 replay. |
| dependence `absolute_count_requirements` | private policy extension requiring zero missed roots | omitted from public policy | The observed `missed_roots == 0` remains in metrics; any future resolver gate is pinned locally. |
| dependence `safety_gates.no_missed_roots` | private extra gate | omitted | v0.19 admits only the closed standard gate vocabulary. |
| disclosure, non-inference, and provenance method text | Round-1 construction wording | Round-2 re-derivation/no-grant wording | Makes the changed representation and unchanged authority explicit. |
| record and policy semantic digests | Round-1 values | values above | Mechanical consequence of the enumerated changes. |

The frozen detector ledgers, scientific labels, authoring protocols, case membership, outcome
states, metric estimates, counts, threshold bars, report references, and maintainer decision
references do not change.

## Consequences

- A test-local `GrantPin` can resolve each exact Round-2 pair against its matching live binding.
- Every sibling binding refuses the same test-local pin.
- Stage 6 installs two `GrantPin` entries, the two qualifications, and their metric sets under a
  separate digest-closed grant resource. Production resolution remains fail-closed on every pin.
- The capability matrix publishes `finding` only inside the two exact binding-grant entries. The
  generic detector remains experimental with a disclosure ceiling, and all twenty sibling
  bindings remain unqualified.
- The five-collection capability manifest invariant remains unchanged; grant metrics and external
  pins live in `qualification-grants-v1`.
