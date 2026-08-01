from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {"MANIFEST.sha256", "VALIDATION.txt"}
EXCLUDED_PARTS = {
    ".demo-audit",
    ".demo-replay",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}


def main() -> None:
    rows = []
    for path in sorted(ROOT.rglob("*")):
        if (
            not path.is_file()
            or path.name in EXCLUDE
            or any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in path.parts)
        ):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{digest}  {path.relative_to(ROOT).as_posix()}")
    (ROOT / "MANIFEST.sha256").write_text("\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
