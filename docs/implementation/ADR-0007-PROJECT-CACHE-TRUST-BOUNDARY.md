# ADR-0007: Define the persisted project-cache trust boundary

- **Status:** Accepted
- **Date:** 2026-07-28
- **Schema release:** `0.8.0` (no schema change proposed)
- **Related requirements:** SA-FR-049, SA-FR-092–093, AC-25, AC-50

## Context

The project-local parser and descendant caches are content-addressed, canonical, self-digested,
project-identity-bound, and schema-validated after reuse. A nonblocking exclusive writer lease now
prevents concurrent audits from clobbering the mutable parser and descendant indices: a contending
run completes without cache reuse or writes rather than waiting past its audit deadline.

Those controls detect accidental corruption but do not authenticate a cache created or replaced by
an adversary who can write the project's `.sc-referee/` directory. Such an adversary can recompute
ordinary hashes after changing a payload. Because cached parser and lineage records may later feed
material detector premises, self-digests alone are not an adequate production trust boundary.

No purely project-local secret can solve this problem: an attacker who can replace both a blob and
all project-local verification material can forge the replacement. Resistance to an arbitrary
active process running as the same operating-system user is also not achievable with an ordinary
user-readable key file; that stronger threat requires an external credential or hardware/service
boundary.

## Decision

Adopt a tool-owned keyed-MAC profile for persisted source-derived cache data:

1. Generate or retrieve a random cache-authentication key from a tool-owned location outside the
   audited repository. Never copy the key into an audit record, cache entry, log, report, or
   semantic lock.
2. Authenticate every parser blob, descendant blob, and mutable index over its normalized content,
   format version, project identity, and key identifier using HMAC-SHA-256.
3. Verify the MAC before decoding a cached scientific payload for reuse. A missing key, unknown key
   identifier, invalid MAC, unsafe key storage, or unsupported platform makes persistent cache reuse
   unavailable for that run; the audit continues by recomputing.
4. Rotate keys by changing the nonsecret key identifier. Old entries become misses and are never
   silently accepted under a new key.
5. Keep the existing project-local source-data rule. Only the non-source-derived authentication key
   may live outside the repository.
6. Define the defended attacker as repository content, a copied/prepopulated project cache, or an
   offline writer that lacks access to the tool-owned key. An arbitrary active same-user process
   able to read tool credentials or process memory remains outside this profile and must be stated
   as a limitation.
7. Retain the nonblocking exclusive writer lease. Authentication and concurrency are independent:
   a valid MAC does not authorize a concurrent index write.

The implementation uses an injectable key-provider interface and a test-only in-memory provider.
The default provider resolves an explicit `SC_REFEREE_CACHE_AUTH_KEY` first, requiring URL-safe
base64 for exactly 32 key bytes. Without an explicit key it generates or retrieves the credential
from macOS Keychain or Linux Secret Service when the platform client is available. A CI process
must supply the explicit environment key. An invalid explicit value, provider failure, unavailable
credential store, unsafe cache path, or missing key disables persistent reuse without failing the
scientific audit.

The nonsecret key identifier is derived from the high-entropy key and is bound into the cache
policy, cache keys, every HMAC envelope, and mutable indices. Key bytes are never written into an
audit artifact, cache document, semantic lock, report, command-line argument, or log. Platform
creation sends the encoded credential over standard input rather than placing it in a process
argument.

## Alternatives

### Disable persisted source-derived reuse

Keep only in-process caching. This avoids persisted-cache authenticity entirely but removes the
required cache-warm descendant behavior and materially weakens AC-25.

### Keep self-digests and recompute material premises

Allow unauthenticated cache reuse only for nonmaterial outputs and recompute every value before it
can support a Finding. This creates two trust classes throughout lineage and detector scheduling,
and it forfeits cache benefit on the paths where correctness matters most.

### Claim protection from every same-user process

Require a separately authenticated service, hardware-backed key with access control, or another
security principal. A normal CLI key file cannot honestly make this claim. This is a larger product
and deployment decision than the current local vertical slice.

## Acceptance evidence required

1. Tampering with a blob payload and recomputing all ordinary digests produces a miss, never a hit.
2. Tampering with either mutable index produces fail-closed recomputation.
3. A key rotation makes old entries misses without deleting or misreading them.
4. No public or canonical audit artifact contains key bytes.
5. A missing/unavailable key disables persistent reuse without failing the scientific audit.
6. Two contending audits cannot write the cache simultaneously; the non-owner completes without
   waiting and leaves both indices unchanged.
7. Warm replay and output semantics remain identical, and cache reuse never independently
   establishes a Finding premise.

## Acceptance

Accepted by the repository owner on 2026-07-28 with the recommended credential source: platform
credential storage when available, an explicitly supplied secret for headless/CI use, and
fail-closed no-cache behavior when neither exists. The public schema remains exactly `0.8.0`.
