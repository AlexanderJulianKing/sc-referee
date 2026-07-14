"""Small, dependency-free loading of Referee's local configuration.

Only the two variables Referee owns are accepted from ``.env``. Existing process values win, so
CI, shell exports, and deployment configuration are never overwritten by a local file.
"""
from __future__ import annotations

import os
import re
from pathlib import Path


_ENV_KEYS = frozenset({"ANTHROPIC_API_KEY", "SC_REFEREE_MODEL"})
_ASSIGNMENT = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")


def load_local_env(path: str | Path | None = None) -> bool:
    """Load supported keys from ``path`` or ``./.env``; return whether Claude is configured."""
    env_path = Path(path) if path is not None else Path.cwd() / ".env"
    if not env_path.is_file():
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _ASSIGNMENT.match(line)
        if not match or match.group(1) not in _ENV_KEYS:
            continue
        key, value = match.groups()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        os.environ.setdefault(key, value)

    return bool(os.environ.get("ANTHROPIC_API_KEY"))
