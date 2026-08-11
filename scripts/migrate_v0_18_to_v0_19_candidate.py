"""Compatibility import for the accepted public v0.18-to-v0.19 migration.

The candidate path is retained for callers from the review phase. New code must
use :mod:`scripts.migrate_v0_18_to_v0_19`.
"""

from __future__ import annotations

from scripts.migrate_v0_18_to_v0_19 import (
    SOURCE_VERSION,
    TARGET_VERSION,
    PublicMigrationError,
    main,
    migrate_public_bundle,
)

CandidateMigrationError = PublicMigrationError
migrate_public_bundle_to_candidate = migrate_public_bundle

__all__ = [
    "SOURCE_VERSION",
    "TARGET_VERSION",
    "CandidateMigrationError",
    "migrate_public_bundle_to_candidate",
]


if __name__ == "__main__":
    raise SystemExit(main())
