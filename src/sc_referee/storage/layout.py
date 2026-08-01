from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AuditLayout:
    root: Path

    @property
    def observed(self) -> Path:
        return self.root / "observed"

    @property
    def derived(self) -> Path:
        return self.root / "derived"

    @property
    def lock_path(self) -> Path:
        return self.root / "semantic.lock.json"

    @property
    def bundle_path(self) -> Path:
        return self.root / "audit.bundle.json"

    @property
    def report_path(self) -> Path:
        return self.root / "report.html"

    @property
    def sqlite_path(self) -> Path:
        return self.root / "audit.db"

    def create(self) -> None:
        self.observed.mkdir(parents=True, exist_ok=True)
        self.derived.mkdir(parents=True, exist_ok=True)
