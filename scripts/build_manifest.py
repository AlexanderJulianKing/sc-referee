from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_RELATIVE_PATH = "MANIFEST.sha256"

# Every generated artifact currently included in the handoff is tracked.  Keep
# this closed tuple explicit so a future untracked generated artifact must be
# intentionally admitted rather than being swept in from the working tree.
INTENTIONALLY_GENERATED_ARTIFACTS: tuple[str, ...] = ()


def git_tree_inventory(root: Path = ROOT) -> tuple[str, ...]:
    """Return the exact file inventory committed at ``HEAD``.

    Content is read from the working tree so a regenerated manifest describes
    the proposed tracked changes, but path admission comes only from Git's
    committed tree.  Untracked and ignored working-tree files are therefore
    incapable of entering the manifest.
    """

    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "ls-tree",
                "-r",
                "--full-tree",
                "--name-only",
                "-z",
                "HEAD",
            ],
            check=True,
            capture_output=True,
        )
        paths = tuple(
            item.decode("utf-8", errors="strict") for item in completed.stdout.split(b"\0") if item
        )
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as error:
        raise RuntimeError("unable to read the committed Git tree for the manifest") from error
    if not paths or len(paths) != len(set(paths)):
        raise RuntimeError("the committed Git tree inventory is empty or ambiguous")
    return tuple(sorted(paths))


def manifest_inventory(root: Path = ROOT) -> tuple[str, ...]:
    """Return the closed tracked-plus-explicit-generated manifest inventory."""

    relative_paths = (set(git_tree_inventory(root)) - {MANIFEST_RELATIVE_PATH}) | set(
        INTENTIONALLY_GENERATED_ARTIFACTS
    )
    for relative in relative_paths:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or not (root / path).is_file():
            raise RuntimeError(f"manifest inventory path is unavailable: {relative}")
    return tuple(sorted(relative_paths))


def build_manifest_rows(root: Path = ROOT) -> tuple[str, ...]:
    """Hash current bytes for the exact admitted path inventory."""

    return tuple(
        f"{hashlib.sha256((root / relative).read_bytes()).hexdigest()}  {relative}"
        for relative in manifest_inventory(root)
    )


def main() -> None:
    rows = build_manifest_rows()
    (ROOT / MANIFEST_RELATIVE_PATH).write_text("\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
