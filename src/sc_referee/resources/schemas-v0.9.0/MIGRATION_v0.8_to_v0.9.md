# Migration from v0.8.0 to v0.9.0

Derive review-local candidate IDs only from exact existing demonstrated Stage-1 review content.
Do not infer cross-review equivalence. Demote legacy demonstrated Stage-2 reviews and positive
adjudications to insufficient evidence, preserving prior fields in `x-v0-8-*` extensions. Demote
legacy positive fixtures to ambiguous and preserve prior labels in extensions. Add an empty
AdjudicatedRootCause collection. Do not carry forward a StorageManifest because migrated bytes
require a new manifest.
