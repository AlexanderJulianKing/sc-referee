"""The friendly `referee` launcher: folder-picker in, browser-rendered ledger out.

For a reviewer who is not comfortable on the command line — no path typing, no terminal reading.
The tkinter dialog and the browser open are injected so the orchestration is testable headless.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from sc_referee.audit import AuditResult
from sc_referee.checks.base import Finding
from sc_referee.ingest import IngestError
from sc_referee import statuses as S
from sc_referee.friendly import (
    _tk_ask_directory, _welcome_page, _workload, open_in_browser, pick_folder, run_friendly,
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

    assert "Check the analysis behind the claim" in html
    assert "Independent scientific review" in html
    assert "Choose analysis folder" in html
    assert "runs locally" in html
    assert all(step in html for step in ("Inspect", "Confirm", "Check"))
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


def test_native_folder_chooser_is_standalone_not_attached_to_a_hidden_parent(monkeypatch):
    from tkinter import filedialog

    received = {}
    monkeypatch.setattr(
        filedialog, "askdirectory",
        lambda **options: received.update(options) or "/chosen/dir",
    )

    assert _tk_ask_directory() == "/chosen/dir"
    assert received == {
        "title": "Choose an analysis folder for sc-referee",
        "mustexist": True,
    }


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
