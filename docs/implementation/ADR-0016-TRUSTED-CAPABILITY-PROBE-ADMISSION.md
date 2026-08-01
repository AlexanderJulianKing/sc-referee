# ADR-0016: Require a trusted probe origin before capability evidence can authorize execution

- **Status:** Deferred by accepted ADR-0017
- **Date:** 2026-07-29
- **Former proposed coordinated schema release:** `0.15.0` with ADR-0015 (not scheduled)
- **Related requirements:** SA-FR-047–049, SA-FR-074, SA-FR-091, AC-28–32, AC-49

## Context

Accepted ADR-0013 requires a controller-observed effective rootless-OCI probe. The current v0.14
implementation correctly probes a Podman service and records its transcript, but two origin
premises are not yet protected strongly enough for real launch admission:

1. `authorize-execution --capability` accepts a canonical, schema-valid SandboxCapability JSON
   file. Schema validity and self-consistent digests prove record shape, not that the controller
   actually ran the probe. Repository text or any local producer can manufacture the same public
   bytes.
2. `probe-execution-capability --image` accepts any digest-pinned image. The command injected into
   the container is auditor-authored, but an untrusted image controls the `python` executable and
   can forge the probe output. A digest proves which image was used, not that the image belongs to
   sc-referee or implements the expected probe runtime.

Direct human authorization is necessary but does not make those factual sandbox premises true.
The current source-lock, one-use registry, snapshot, and launch-envelope checks remain valuable,
but a public capability record alone cannot safely enable them. No project-authored code has been
launched through this path.

## Decision

Coordinate this correction with forward-only schema v0.15.0. Keep v0.14.0 immutable.

### 1. Publish an auditor-owned probe-image identity manifest

The production wheel carries a closed, versioned manifest of supported probe images. Each entry
binds the OCI reference, manifest digest, target architecture, contained probe-runtime identity,
source/build recipe digest, and sc-referee version range. The manifest contains no mutable tag.

Only an exact manifest entry may run a qualifying probe. Arbitrary digest-pinned images may be
inspected for diagnostics but must produce `project_code_execution_supported: false`. Image
retrieval remains a separate provenance-recorded controller action and is never performed by the
probe or authorization command.

### 2. Add trusted probe-origin evidence to SandboxCapability

A complete v0.15 SandboxCapability binds:

- the packaged probe-image manifest entry and semantic digest;
- the exact probe image manifest digest re-observed immediately before the probe;
- the sc-referee ToolIdentity and probe implementation digest;
- the canonical probe transcript Artifact and AssetIdentity semantic digests; and
- `probe_origin_status: controller_executed_trusted_probe`.

Legacy, imported, synthetic, arbitrary-image, missing-closure, or user-authored origins are
explicitly nonqualifying. A model, repository file, Scientist Answer, or public JSON record cannot
set or upgrade the trusted status.

### 3. Remove public-record launch admission

The authorization CLI no longer accepts a standalone capability JSON file as launch-enabling
input. It accepts the original controller-created probe package and independently verifies its
closed inventory, canonical bytes, semantic digests, filesystem safety, expiry, executable
identity, endpoint identity, image identity, and trusted manifest entry. A copied public record is
inert.

Immediately before presenting the fresh authorization challenge, the controller reruns the
auditor-owned probe into a new private candidate package and requires the same material backend
identity plus controls at least as strict as the proposed launch. Only that fresh result is bound
to the authorization. Abandoned or failed challenges create no reusable authorization.

Immediately before consuming authorization, the executor rechecks the bound executable, endpoint,
image, expiry, and private candidate-package identity. It does not trust a replacement public
capability file. Re-probing executes only the packaged auditor probe, never project code.

### 4. Keep capability evidence separate from consent

The trusted probe establishes observed sandbox facts only. The fresh attached-terminal challenge
remains the sole consent transition. Neither a trusted capability nor its private candidate
package authorizes a launch by itself, and the authorization remains single use.

### 5. Migrate fail closed

The v0.14→v0.15 migration marks every older qualifying SandboxCapability
`legacy_probe_origin_unavailable`, sets project-execution support false, and removes dependent
authorization, clean-control, metric, qualification, and promotion authority. It does not infer a
trusted image, probe invocation, private package, or tool identity from v0.14 provenance strings.

## Alternatives

### Trust canonical JSON plus transcript hashes

Rejected because any local producer can construct a self-consistent record and transcript.

### Trust any digest-pinned image

Rejected because immutability identifies an image but does not make its interpreter or probe
behavior auditor-owned.

### Treat direct user confirmation as verification of the capability

Rejected because consent and factual effective-control evidence are separate authorities. The
user should not have to reverse-engineer a probe transcript to authorize safely.

### Store a reusable secret in the repository

Rejected because repository material is untrusted and copyable. A signature could authenticate a
release manifest, but it would not prove that the local probe actually ran; fresh controller
observation is still required.

## Acceptance evidence required

1. Production probe admission rejects a mutable tag, unknown digest, wrong architecture, changed
   build/implementation digest, and arbitrary image before treating any output as qualifying.
2. A malicious image that prints a perfect-looking probe result cannot produce a qualifying
   SandboxCapability.
3. Authorization rejects a standalone, copied, migrated, synthetic, or self-consistent forged
   capability record before presenting the challenge or creating registry state.
4. The fresh pre-authorization probe binds the exact executable, endpoint, image, limits, tool
   identity, transcript Artifact, AssetIdentity, and private candidate package; mutation of any
   component fails closed.
5. Repository text, model output, Scientist Answers, and WorkItems cannot select the trusted probe
   image, assert trusted origin, broaden limits, or bypass the fresh probe.
6. Execution rechecks the private capability-package identity and material backend facts before
   atomic authorization consumption; copied packages and post-authorization drift cannot launch.
7. Probe failure or missing supported image leaves static audit available and consumes no project
   authorization.
8. v0.14→v0.15 migration invents no trusted probe origin, capability, authorization, execution,
   clean control, metric, qualification, or promotion authority.
9. At least one clean hosted run exercises the packaged auditor probe against a qualifying local
   rootless Podman service before project-execution support is claimed for that release.

## Consequences

- The current v0.14 request, authorization, linked evidence, and replay mechanics remain tested,
  but the production launch path must stay disabled until this admission correction is accepted
  and implemented.
- A release needs a reproducibly built, architecture-specific auditor probe image or equivalent
  immutable runtime artifact before it can claim project-execution support.
- Local static audit and model-free replay remain fully available without Podman or a probe image.

## Pre-acceptance safety action

Pending this decision, `execute-authorized` refuses before reading registry state or calling the
internal executor. `tests/test_execution_request.py` injects a sentinel executor and proves it is
not reached when standalone capability JSON is supplied. This is a fail-closed stopgap for
acceptance criteria 3 and 7, not an implementation of trusted probe admission. The internal
executor remains covered with auditor-owned synthetic runtime tests so its non-privilege mechanics
do not regress. Remaining coverage is the substance of this ADR: no packaged probe image, fresh
controller re-probe, trusted capability closure, v0.15 migration, or live qualifying run exists.

## Pre-acceptance structural-verifier preparation

The read-only `verify_capability_probe_package_structure` implementation now closes what can be
closed without changing public meaning or granting launch authority. It accepts exactly the five
files and one directory emitted by the v0.14 Podman probe, rejects links and nonregular or
multiply-linked files, enforces bounded canonical bytes, validates all public records, replays the
fixed eleven-command transcript shape, recomputes the effective-control projection, and
reconstructs the exact SandboxCapability, Artifact, and AssetIdentity records. It executes no
command and does not inspect an audited project.

`tests/test_execution_probe.py` covers the valid read-only reconstruction, canonical mutations of
each retained component, noncanonical JSON, an added inventory entry, changed input bytes, and a
symlink substitution. A multiply-linked-file case and a digest-rebound, otherwise self-consistent
network-control mutation also fail closed. These tests are implementation preparation for
acceptance criterion 4's package-mutation clause. They do not satisfy its origin or
launch-admission clauses: a byte-for-byte copy remains structurally verifiable, and a wholly
fabricated but internally consistent package cannot be distinguished from controller-created
evidence. The copied-package test preserves that limitation explicitly, while
`tests/test_execution_request.py` continues to prove that no such package or standalone record can
reach the executor.
