"""The out-of-process native folder chooser helper (``sc_referee._folder_picker``).

The chooser runs in its own short-lived process so the long-lived ``referee`` server never initializes
Tk / the macOS ``NSApplication`` and is never left as an unresponsive foreground GUI app after the panel
closes. These tests pin the helper's JSON contract (success / cancel / failure), unicode/space handling,
and that it opens the native panel with no hidden parent (the centered/movable-panel guarantee).
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

from sc_referee import _folder_picker


def _run(**kw):
    buf = io.StringIO()
    code = _folder_picker.main(stdout=buf, **kw)
    return code, buf.getvalue()


def test_helper_emits_json_for_a_selected_path():
    code, out = _run(choose=lambda: "/chosen/dir")
    assert code == 0
    assert json.loads(out) == {"ok": True, "path": "/chosen/dir"}


def test_helper_emits_null_path_on_cancel():
    code, out = _run(choose=lambda: None)
    assert code == 0
    assert json.loads(out) == {"ok": True, "path": None}


def test_helper_reports_failure_as_json_not_a_crash():
    def boom():
        raise RuntimeError("no display / tkinter missing")

    code, out = _run(choose=boom)
    assert code == 3
    payload = json.loads(out)
    assert payload["ok"] is False
    assert "no display" in payload["error"]


def test_helper_preserves_unicode_and_spaces_in_paths():
    weird = "/data/z/Führung analysis 2024/données brutes"
    code, out = _run(choose=lambda: weird)
    assert code == 0
    assert json.loads(out)["path"] == weird


def test_choose_directory_opens_a_standalone_panel_with_no_hidden_parent(monkeypatch):
    from tkinter import filedialog

    received = {}
    monkeypatch.setattr(
        filedialog, "askdirectory",
        lambda **options: received.update(options) or "/chosen/dir",
    )
    assert _folder_picker.choose_directory() == "/chosen/dir"
    # No hidden parent: exactly title + mustexist, so the OS keeps the panel centered and movable
    # instead of pinning it top-left as an invisible-parent sheet.
    assert received == {
        "title": "Choose an analysis folder for sc-referee",
        "mustexist": True,
    }


def test_choose_directory_maps_a_cancelled_dialog_to_none(monkeypatch):
    from tkinter import filedialog

    monkeypatch.setattr(filedialog, "askdirectory", lambda **o: "")   # cancel returns ""
    assert _folder_picker.choose_directory() is None


def test_helper_runs_as_a_real_subprocess_and_emits_one_json_line():
    # Exercise main() in a genuine child process (no GUI: inject a fake chooser) to prove the
    # cross-process JSON protocol the parent relies on.
    code = ("import sys; from sc_referee import _folder_picker as fp;"
            "sys.exit(fp.main(choose=lambda: '/picked/folder'))")
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(p for p in sys.path if p)}
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout.strip()) == {"ok": True, "path": "/picked/folder"}
