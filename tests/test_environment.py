"""Local .env support for the desktop launcher and Claude proposal path."""
import os

from sc_referee.environment import load_local_env


def test_load_local_env_finds_project_key_without_overwriting_process_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    original = os.environ.pop("ANTHROPIC_API_KEY", None)
    (tmp_path / ".env").write_text(
        "# local Referee configuration\n"
        "ANTHROPIC_API_KEY='from-file'\n"
        "UNRELATED_SETTING=do-not-import\n"
    )

    try:
        assert load_local_env() is True
        assert os.environ["ANTHROPIC_API_KEY"] == "from-file"
        assert "UNRELATED_SETTING" not in os.environ

        os.environ["ANTHROPIC_API_KEY"] = "from-process"
        assert load_local_env() is True
        assert os.environ["ANTHROPIC_API_KEY"] == "from-process"
    finally:
        os.environ.pop("ANTHROPIC_API_KEY", None)
        if original is not None:
            os.environ["ANTHROPIC_API_KEY"] = original


def test_load_local_env_is_optional(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    original = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        assert load_local_env() is False
    finally:
        if original is not None:
            os.environ["ANTHROPIC_API_KEY"] = original
