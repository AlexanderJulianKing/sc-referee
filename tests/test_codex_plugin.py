from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

STRICT_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)

GITHUB_REPOSITORY = "https://github.com/AlexanderJulianKing/sc-referee"


def _relative_files(root: Path) -> list[Path]:
    return sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())


def test_codex_plugin_manifest_declares_the_bounded_local_surface(project_root: Path) -> None:
    plugin_root = project_root / "plugins" / "sc-referee"
    manifest = json.loads(
        (plugin_root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )

    assert manifest["name"] == plugin_root.name
    assert STRICT_SEMVER.fullmatch(manifest["version"])
    assert manifest["version"].startswith("0.3.0+codex.")
    assert manifest["skills"] == "./skills/"
    assert manifest["license"] == "Apache-2.0"
    assert manifest["author"]["name"] == "Alexander King"
    assert manifest["author"]["url"] == "https://github.com/AlexanderJulianKing"
    assert manifest["repository"] == GITHUB_REPOSITORY
    assert manifest["homepage"] == f"{GITHUB_REPOSITORY}#readme"
    assert manifest["interface"]["websiteURL"] == GITHUB_REPOSITORY
    assert manifest["interface"]["developerName"] == "Alexander King"
    assert manifest["interface"]["capabilities"] == [
        "Expected-count/background method contract",
        "Static scientific audit",
        "Typed human-in-the-loop resolution",
        "Model-free replay",
    ]
    prompts = manifest["interface"]["defaultPrompt"]
    assert 1 <= len(prompts) <= 3
    assert all(len(prompt) <= 128 for prompt in prompts)
    assert "installed sc-referee CLI" in manifest["interface"]["longDescription"]
    assert (
        "one supported expected-count/background profile"
        in manifest["interface"]["longDescription"]
    )
    assert "scientist-supplied expected-count/background profile" in prompts[0]
    assert "method contracts" not in manifest["description"]


def test_codex_plugin_marketplace_points_to_the_validated_local_plugin(
    project_root: Path,
) -> None:
    marketplace = json.loads(
        (project_root / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
    )

    assert marketplace["name"] == "sc-referee"
    assert marketplace["interface"]["displayName"] == "Sc Referee"
    assert marketplace["plugins"] == [
        {
            "name": "sc-referee",
            "source": {"source": "local", "path": "./plugins/sc-referee"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Developer Tools",
        }
    ]
    assert (project_root / marketplace["plugins"][0]["source"]["path"]).is_dir()


@pytest.mark.parametrize("skill_name", ["scientific-audit", "method-contract"])
def test_codex_plugin_skill_is_an_exact_copy_of_the_authoritative_skill(
    project_root: Path,
    skill_name: str,
) -> None:
    authoritative = project_root / ".agents" / "skills" / skill_name
    packaged = project_root / "plugins" / "sc-referee" / "skills" / skill_name

    assert _relative_files(packaged) == _relative_files(authoritative)
    for relative_path in _relative_files(authoritative):
        assert (packaged / relative_path).read_bytes() == (
            authoritative / relative_path
        ).read_bytes()
