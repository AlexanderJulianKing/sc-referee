from __future__ import annotations

from pathlib import Path

import pytest

from sc_referee.reproduction import _bounded_declaration_text, _runtime_values


@pytest.mark.parametrize(
    ("name", "text", "expected"),
    [
        (
            "pyproject.toml",
            '[project]\nrequires-python = ">=3.11"\n',
            [">=3.11"],
        ),
        (
            "pyproject.toml",
            '[tool.poetry.dependencies]\npython = "^3.12"\n',
            ["^3.12"],
        ),
        ("Pipfile", '[requires]\npython_full_version = "3.11.9"\n', ["3.11.9"]),
        (
            "Pipfile.lock",
            '{"_meta":{"requires":{"python_version":"3.10"}}}',
            ["3.10"],
        ),
        ("setup.cfg", "[options]\npython_requires = >=3.9\n", [">=3.9"]),
        ("environment.yml", "dependencies:\n  - python=3.12\n  - numpy\n", ["=3.12"]),
        (".python-version", "3.11.8\n", ["3.11.8"]),
        ("runtime.txt", "python-3.12.2\n", ["3.12.2"]),
        ("pixi.toml", '[dependencies]\npython = ">=3.10"\n', [">=3.10"]),
        ("uv.lock", 'requires-python = ">=3.12"\n', [">=3.12"]),
        ("poetry.lock", '[metadata]\npython-versions = ">=3.11"\n', [">=3.11"]),
    ],
)
def test_runtime_declaration_readers_return_only_bounded_literal_values(
    name: str, text: str, expected: list[str]
) -> None:
    assert _runtime_values(name, text) == expected


def test_environment_declaration_reader_rejects_unbounded_files(tmp_path: Path) -> None:
    declaration = tmp_path / "pyproject.toml"
    declaration.write_bytes(b"x" * 1_000_001)

    with pytest.raises(ValueError, match="bounded inspection size"):
        _bounded_declaration_text(declaration)
