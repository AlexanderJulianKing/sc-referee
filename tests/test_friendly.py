"""The friendly `referee` launcher: folder-picker in, browser-rendered ledger out.

For a reviewer who is not comfortable on the command line — no path typing, no terminal reading.
The tkinter dialog and the browser open are injected so the orchestration is testable headless.
"""
from __future__ import annotations

import threading
import time
import urllib.request
from json import loads
from pathlib import Path
from types import SimpleNamespace

import pytest

from sc_referee.audit import AuditResult
from sc_referee.checks.base import Finding
from sc_referee.ingest import IngestError
from sc_referee import statuses as S
from sc_referee.friendly import (
    PickerError, _ask_directory, _welcome_page, _workload, open_in_browser, pick_folder,
    run_friendly, serve_friendly_app,
)
from sc_referee.wizard import _confirm_page


def _fake_result():
    return AuditResult(analysis_type="marker_detection",
                       findings=[Finding("x", S.PASS, "ok")])


def test_folder_argument_skips_the_picker_and_shows_a_report():
    calls = {}
    pick = lambda: (_ for _ in ()).throw(AssertionError("picker must not open when a folder is given"))
    run = lambda folder, *a, **k: calls.setdefault("run", folder) or _fake_result()
    show = lambda html: calls.setdefault("shown", html)

    code = run_friendly(["/data/analysis"], wizard=lambda folder: None, pick=pick, run=run,
                        render=lambda r: "<html>REPORT</html>", show=show)

    assert calls["run"] == Path("/data/analysis")
    assert calls["shown"] == "<html>REPORT</html>"
    assert code == 0


def test_browser_first_welcome_explains_the_complete_local_flow():
    html = _welcome_page()

    assert "Catch the mistakes review misses" in html
    assert "STATISTICAL REVIEW FOR SINGLE-CELL ANALYSIS" in html
    assert "Choose analysis folder" in html
    assert "runs locally" in html
    assert all(step in html for step in ("Reconstruct", "Confirm", "Verify"))
    assert "http://" not in html and "https://" not in html


def test_running_page_names_real_workload_and_conservative_time_range():
    bundle = SimpleNamespace(observations=range(27), feature_metadata=range(35_650))
    workload, estimate = _workload(bundle)
    html = _confirm_page(workload=workload, estimate=estimate, poll=True)

    assert "27 observations × 35,650 features" in html
    assert "15–60 seconds" in html
    assert "This page will become the finished report automatically" in html
    assert "progressbar" in html and "location.replace('/report')" in html


def test_no_argument_opens_the_picker():
    calls = {}
    pick = lambda: Path("/picked/folder")
    run = lambda folder, *a, **k: calls.setdefault("run", folder) or _fake_result()

    code = run_friendly([], wizard=lambda folder: None, pick=pick, run=run, render=lambda r: "<html/>",
                        show=lambda h: None)

    assert calls["run"] == Path("/picked/folder")
    assert code == 0


def test_cancelling_the_picker_exits_cleanly_without_running():
    calls = {"ran": False, "shown": False}
    pick = lambda: None                       # user closed the dialog
    run = lambda *a, **k: calls.__setitem__("ran", True)
    show = lambda h: calls.__setitem__("shown", True)
    out = []

    code = run_friendly([], wizard=lambda folder: None, pick=pick, run=run, render=lambda r: "x",
                        show=show, out=out.append)

    assert calls["ran"] is False and calls["shown"] is False
    assert code == 0
    assert any("no folder" in m.lower() for m in out)


def test_ingest_error_is_reported_friendly_not_as_a_traceback():
    def run(folder, *a, **k):
        raise IngestError("3 candidate matrices; refusing to guess")
    show = lambda h: (_ for _ in ()).throw(AssertionError("no report when the audit could not run"))
    out = []

    code = run_friendly(["/data"], wizard=lambda folder: None, pick=lambda: None, run=run,
                        render=lambda r: "x", show=show, out=out.append)

    assert code == 2
    assert any("candidate matrices" in m for m in out)     # the reason is surfaced
    assert not any("Traceback" in m for m in out)


def test_missing_folder_is_reported_friendly_not_as_a_traceback():
    def run(folder, *a, **k):
        raise FileNotFoundError(f"{folder}: no supported data matrix found.")
    show = lambda h: (_ for _ in ()).throw(AssertionError("no report when the folder is missing"))
    out = []

    code = run_friendly(["/typo/path"], wizard=lambda folder: None, pick=lambda: None, run=run,
                        render=lambda r: "x", show=show, out=out.append)

    assert code == 2
    assert any("no supported data matrix" in m for m in out)
    assert not any("Traceback" in m for m in out)


def test_open_in_browser_writes_the_report_and_opens_that_file(tmp_path):
    opened = {}
    browser_open = lambda uri: opened.setdefault("uri", uri)

    path = open_in_browser("<html>hi</html>", browser_open=browser_open, directory=tmp_path)

    assert path.exists()
    assert path.read_text() == "<html>hi</html>"
    assert opened["uri"] == path.as_uri()          # opened the file we just wrote, offline


def test_pick_folder_maps_a_cancelled_dialog_to_none():
    assert pick_folder(ask=lambda: "") is None                     # cancel → empty string → None
    assert pick_folder(ask=lambda: "/chosen/dir") == Path("/chosen/dir")


def _completed(stdout="", returncode=0, stderr=""):
    # Real subprocess.run(capture_output=True) returns BYTES; mirror that so decoding is exercised.
    enc = lambda s: s.encode() if isinstance(s, str) else s
    return SimpleNamespace(stdout=enc(stdout), stderr=enc(stderr), returncode=returncode)


def test_ask_directory_runs_the_chooser_in_a_subprocess_never_in_this_process():
    import os
    import sys

    calls = {}

    def fake_run(argv, **kw):
        calls["argv"] = argv
        return _completed(stdout='{"ok": true, "path": "/chosen/dir"}\n')

    assert _ask_directory(run=fake_run) == "/chosen/dir"
    # Isolation is the whole fix: the chooser runs as a separate process, so this server never
    # initializes Tk / the macOS NSApplication and is never left as a beach-balling foreground app.
    assert calls["argv"][0] == sys.executable
    # Launched by ABSOLUTE PATH, not `-m sc_referee._folder_picker`: `-m` puts the launch directory
    # first on the child's path, so a stray ./sc_referee could shadow the real helper.
    assert len(calls["argv"]) == 2
    assert os.path.isabs(calls["argv"][1]) and calls["argv"][1].endswith("_folder_picker.py")


def test_ask_directory_maps_cancel_to_empty_string():
    assert _ask_directory(run=lambda *a, **k: _completed(stdout='{"ok": true, "path": null}')) == ""


def test_ask_directory_never_imports_tkinter_into_the_calling_process():
    import os
    import subprocess
    import sys

    # The whole point of the fix: the server that calls _ask_directory must never initialize Tk in its
    # own process (that macOS NSApplication is what beach-balls). Run it in a fresh interpreter with a
    # fake chooser subprocess and assert Tk stays unloaded here.
    code = ("import sys; from types import SimpleNamespace;"
            "from sc_referee.friendly import _ask_directory;"
            "_ask_directory(run=lambda *a, **k: SimpleNamespace("
            "stdout='{\"ok\": true, \"path\": \"/x\"}', stderr='', returncode=0));"
            "print('TK-LOADED' if ('tkinter' in sys.modules or '_tkinter' in sys.modules) else 'TK-FREE')")
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(p for p in sys.path if p)}
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip().endswith("TK-FREE")


def test_ask_directory_preserves_unicode_and_spaces():
    weird = "/data/z/Führung analysis/données"
    run = lambda *a, **k: _completed(stdout='{"ok": true, "path": %s}' % __import__("json").dumps(weird))
    assert _ask_directory(run=run) == weird


def test_ask_directory_tolerates_stdout_noise_before_the_json():
    run = lambda *a, **k: _completed(stdout='DEPRECATION WARNING: Tk\n{"ok": true, "path": "/p"}\n')
    assert _ask_directory(run=run) == "/p"


def test_ask_directory_raises_pickererror_on_every_failure_mode():
    with pytest.raises(PickerError):                                   # non-zero exit
        _ask_directory(run=lambda *a, **k: _completed(returncode=1, stderr="boom"))
    with pytest.raises(PickerError):                                   # helper reported failure
        _ask_directory(run=lambda *a, **k: _completed(stdout='{"ok": false, "error": "no display"}'))
    with pytest.raises(PickerError):                                   # unreadable output
        _ask_directory(run=lambda *a, **k: _completed(stdout="not json at all"))

    def cannot_launch(*a, **k):
        raise OSError("exec failed")

    with pytest.raises(PickerError):                                   # subprocess could not start
        _ask_directory(run=cannot_launch)


def test_ask_directory_keeps_the_helpers_rich_error_even_on_nonzero_exit():
    # The helper writes {"ok": false, "error": ...} to stdout AND exits non-zero; we keep that message
    # rather than degrading to a bare exit status.
    run = lambda *a, **k: _completed(returncode=3, stdout='{"ok": false, "error": "TclError: no display"}')
    with pytest.raises(PickerError, match="no display"):
        _ask_directory(run=run)


def test_ask_directory_rejects_malformed_result_shapes():
    # A non-bool "ok" or a non-string "path" must NOT be mistaken for a selection or a cancellation —
    # a corrupt result degrades to PickerError (command-line hint), never a wrong/blank folder.
    for bad in ('{"ok": "false", "path": "/wrong"}', '{"ok": true, "path": 0}', '{"missing": 1}'):
        with pytest.raises(PickerError):
            _ask_directory(run=lambda *a, **k: _completed(stdout=bad))


# --- serve_friendly_app orchestration (folder chooser -> setup -> report) ------------------------

def _serve(*, choose, browser_open=None):
    """Start the friendly HTTP app on an ephemeral port in a daemon thread; return its base URL."""
    opens = []

    def _open(url):
        opens.append(url)
        if browser_open is not None:
            browser_open(url)

    threading.Thread(
        target=lambda: serve_friendly_app(None, browser_open=_open, choose=choose, port=0),
        daemon=True,
    ).start()
    for _ in range(300):
        if opens:
            break
        time.sleep(0.01)
    assert opens, "server never opened the browser / never bound a port"
    return opens[0].rstrip("/"), opens


def _post(base, path):
    req = urllib.request.Request(base + path, data=b"", method="POST")
    return urllib.request.urlopen(req, timeout=5).read().decode()


def test_serve_app_choose_cancel_returns_to_the_welcome_page():
    base, _ = _serve(choose=lambda: "")                     # reviewer cancelled the panel
    page = _post(base, "/choose")
    assert "No folder selected" in page
    assert "Choose analysis folder" in page                # back on the welcome page, server alive


def test_serve_app_choose_picker_failure_shows_a_command_line_hint_and_stays_up():
    def boom():
        raise PickerError("helper crashed / no display")

    base, _ = _serve(choose=boom)
    page = _post(base, "/choose")
    assert "referee /path/to/folder" in page               # tells them how to proceed
    # server survived the failure: the welcome page still serves
    assert "Choose analysis folder" in urllib.request.urlopen(base + "/", timeout=5).read().decode()


def test_serve_app_opens_the_browser_exactly_once_no_duplicate_tab():
    base, opens = _serve(choose=lambda: "")
    _post(base, "/choose")                                 # choosing must not spawn a second tab
    urllib.request.urlopen(base + "/", timeout=5).read()
    assert len(opens) == 1


def test_run_friendly_runs_the_wizard_before_the_audit():
    order = []
    def wizard(folder):
        order.append("wizard")
    def run(folder, *a, **k):
        order.append("audit")
        return _fake_result()

    code = run_friendly(["/data/analysis"], wizard=wizard, run=run,
                        render=lambda r: "<html/>", show=lambda h: None)

    assert order == ["wizard", "audit"]        # design confirmed BEFORE the audit runs
    assert code == 0


def test_unavailable_picker_falls_back_to_a_command_line_hint():
    def pick():
        raise RuntimeError("no display / tkinter missing")
    out = []
    code = run_friendly([], pick=pick, run=lambda *a, **k: _fake_result(), render=lambda r: "x",
                        show=lambda h: None, out=out.append)
    assert code == 2
    assert any("path" in m.lower() for m in out)                   # tells them to pass a path instead
