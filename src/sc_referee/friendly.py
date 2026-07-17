"""The friendly `referee` launcher.

For reviewers who are not comfortable on the command line: run `referee` with no arguments and a
single localhost browser flow explains the review, invokes the native folder picker, confirms the
design, shows the live audit handoff, and replaces itself with the finished report.
`referee /path/to/folder` still works for anyone who would rather type the path.

The tkinter windows, the audit, the HTML render, and the browser open are all injected (see
`run_friendly`) so the orchestration is testable without a display or a browser.
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import urllib.parse
import webbrowser
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from sc_referee.audit import run_audit
from sc_referee.report import to_html
from sc_referee.wizard import (
    SUPPORTED_TYPES, _CSS, _confirm_page, _existing_confirmed_config, _reported_for_folder,
    answers_to_config, design_questions, render_form, run_wizard,
)


def _tk_ask_directory() -> str:
    """Open a standalone native folder chooser.

    Do not give the chooser a hidden Tk parent. On macOS that turns the native panel into a sheet
    attached to an invisible window: it appears at the top-left and cannot be moved like a normal
    Finder panel. With no explicit parent, tkinter owns a temporary root internally and the OS can
    center and move the chooser normally.
    """
    from tkinter import filedialog

    return filedialog.askdirectory(
        title="Choose an analysis folder for sc-referee", mustexist=True)


def pick_folder(*, ask=_tk_ask_directory) -> Path | None:
    """The chosen analysis folder, or None if the reviewer cancelled the dialog."""
    raw = ask()
    return Path(raw) if raw else None


def open_in_browser(html: str, *, browser_open=webbrowser.open, directory=None) -> Path:
    """Write the report to a file and open it in the default browser.

    Written to a temp location, never into the analysis folder: the referee inspects that folder
    without leaving anything behind in it.
    """
    directory = Path(directory) if directory is not None else Path(tempfile.mkdtemp(prefix="sc-referee-"))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "sc-referee-report.html"
    path.write_text(html)
    browser_open(path.as_uri())
    return path


def _welcome_page(message: str | None = None) -> str:
    notice = (f'<p class="welcome-notice">{message}</p>' if message else "")
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>sc-referee — independent review</title>"
            f"<style>{_CSS}"
            ".welcome{padding-top:0}.welcome-hero{padding:76px 0 54px;border-bottom:1px solid var(--rule2)}"
            ".welcome-kicker{font-family:var(--mono);font-size:11px;letter-spacing:.15em;"
            "text-transform:uppercase;color:var(--dim);margin-bottom:15px}"
            ".welcome h1{font-size:clamp(38px,7vw,62px);line-height:.98;letter-spacing:-.045em;"
            "font-weight:650;max-width:10ch;margin:0 0 25px}"
            ".welcome-lede{font-size:18px;line-height:1.55;color:var(--mut);max-width:53ch;margin:0}"
            ".welcome-action{display:flex;align-items:center;gap:20px;flex-wrap:wrap;margin-top:31px}"
            ".welcome-action .run{margin:0;padding:14px 22px}.local{font-family:var(--mono);font-size:11px;"
            "color:var(--dim);letter-spacing:.02em}.welcome-steps{display:grid;grid-template-columns:repeat(3,1fr);"
            "gap:28px;padding:30px 0}.welcome-step{border-top:2px solid var(--ink);padding-top:12px}"
            ".welcome-step b{font-family:var(--mono);font-size:10px;letter-spacing:.13em;color:var(--dim)}"
            ".welcome-step h2{font-size:16px;margin:8px 0 5px}.welcome-step p{font-size:13px;line-height:1.5;"
            "color:var(--mut);margin:0}.welcome-notice{color:var(--accent);font-size:13px;margin:18px 0 0}"
            "@media(max-width:620px){.welcome-hero{padding:48px 0 38px}.welcome-steps{grid-template-columns:1fr;"
            "gap:20px}.welcome-step{display:grid;grid-template-columns:35px 1fr;column-gap:10px}.welcome-step h2{"
            "margin:0}.welcome-step p{grid-column:2}}"
            "</style></head><body><main class='welcome'>"
            "<header><span class='brand'>sc<b>·</b>referee</span><span class='hlabel'>independent review</span></header>"
            "<section class='welcome-hero'><div class='welcome-kicker'>For single-cell analyses</div>"
            "<h1>Review the analysis, not the story.</h1>"
            "<p class='welcome-lede'>Referee reads the supplied data, results, and code; asks you to "
            "confirm the scientific claim; then independently recomputes the statistics at the "
            "correct experimental unit.</p>"
            f"{notice}<div class='welcome-action'><form method='post' action='/choose'>"
            "<button class='run' type='submit'>Choose analysis folder&nbsp; →</button></form>"
            "<span class='local'>runs locally · source files stay unchanged</span></div></section>"
            "<section class='welcome-steps' aria-label='How the review works'>"
            "<div class='welcome-step'><b>01</b><h2>Read</h2><p>Inspect metadata, reported results, "
            "and the code that produced them.</p></div>"
            "<div class='welcome-step'><b>02</b><h2>Confirm</h2><p>You ratify the biological claim. "
            "Claude may interpret; it never decides a verdict.</p></div>"
            "<div class='welcome-step'><b>03</b><h2>Recompute</h2><p>Deterministic checks test the "
            "analysis and report exactly what held up.</p></div>"
            "</section></main></body></html>")


def _error_page(message: str) -> str:
    import html
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<style>{_CSS}</style><title>sc-referee — could not finish</title></head>"
            "<body><main><header><span class='brand'>sc<b>·</b>referee</span>"
            "<span class='hlabel'>review stopped</span></header><section class='section'>"
            "<div class='section-kicker'>Could not finish the review</div>"
            f"<h1>Referee stopped safely.</h1><p class='section-note'>{html.escape(message)}</p>"
            "<p class='section-note'>Your analysis files were not changed.</p>"
            "</section></main></body></html>")


def _workload(bundle) -> tuple[str, str]:
    observations = len(bundle.observations)
    features = len(bundle.feature_metadata)
    label = f"{observations:,} observations × {features:,} features"
    if observations <= 100 and features <= 50_000:
        estimate = "Usually 15–60 seconds for a folder this size."
    elif observations <= 100_000 and features <= 60_000:
        estimate = "Usually 1–3 minutes for a folder this size."
    else:
        estimate = "Large matrices can take several minutes."
    return label, estimate


def serve_friendly_app(folder: Path | None = None, *, browser_open=webbrowser.open,
                       choose=_tk_ask_directory, host="127.0.0.1", port=0) -> int:
    """Run the complete friendly workflow in one localhost tab.

    The browser owns explanation and state; the OS owns choosing a local path; a worker thread owns
    the expensive audit so the waiting page can report honestly instead of appearing frozen.
    """
    import yaml

    from sc_referee import init as _init
    from sc_referee.ingest import ingest

    state = {"stage": "welcome", "folder": None, "bundle": None, "config": None,
             "page": None, "report": None, "error": None}
    finished = threading.Event()

    def prepare(selected: Path):
        bundle = ingest(selected)
        existing = _existing_confirmed_config(selected)
        config, source = ((existing, "confirmed_config") if existing is not None
                          else _init.propose(selected))
        questions = design_questions(config, list(bundle.observations.columns),
                                     analysis_types=SUPPORTED_TYPES)
        if questions:
            questions[0] = replace(questions[0], proposal_source=source)
        state.update(stage="design", folder=selected, bundle=bundle, config=config,
                     page=render_form(questions))

    if folder is not None:
        try:
            prepare(Path(folder))
        except Exception as exc:
            state.update(stage="error", error=str(exc))

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, content, *, status=200, content_type="text/html; charset=utf-8"):
            payload = content.encode() if isinstance(content, str) else content
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            path = urllib.parse.urlparse(self.path).path
            if path == "/status":
                self.send(json.dumps({"stage": state["stage"]}),
                          content_type="application/json; charset=utf-8")
            elif path == "/report" and state["report"] is not None:
                self.send(state["report"])
                finished.set()
            elif path == "/error" and state["error"] is not None:
                self.send(_error_page(state["error"]))
                finished.set()
            elif state["stage"] == "design":
                self.send(state["page"])
            elif state["stage"] == "error":
                self.send(_error_page(state["error"]))
                finished.set()
            else:
                self.send(_welcome_page())

        def do_POST(self):
            path = urllib.parse.urlparse(self.path).path
            if path == "/choose":
                selected = choose()
                if not selected:
                    self.send(_welcome_page("No folder selected. Nothing was changed."))
                    return
                try:
                    prepare(Path(selected))
                    self.send(state["page"])
                except Exception as exc:
                    state.update(stage="error", error=str(exc))
                    self.send(_error_page(str(exc)))
                    finished.set()
                return
            if path != "/submit" or state["stage"] != "design":
                self.send("Not found", status=404, content_type="text/plain; charset=utf-8")
                return

            body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
            parsed = urllib.parse.parse_qs(body, keep_blank_values=True)
            answers = {key: (values if len(values) > 1 else values[0])
                       for key, values in parsed.items()}
            try:
                bundle, config, selected = state["bundle"], state["config"], state["folder"]
                confirmed = answers_to_config(
                    answers, bundle.observations,
                    code_signals=getattr(bundle, "code_signals", {}),
                    reported=_reported_for_folder(config, selected), proposed_config=config)
                (selected / "sc-referee.yaml").write_text(
                    yaml.safe_dump(confirmed, sort_keys=False))
                workload, estimate = _workload(bundle)
                state["stage"] = "running"

                def audit_worker():
                    try:
                        state["report"] = to_html(run_audit(selected))
                        state["stage"] = "done"
                    except Exception as exc:
                        state.update(stage="error", error=str(exc))

                threading.Thread(target=audit_worker, daemon=True).start()
                self.send(_confirm_page(workload=workload, estimate=estimate, poll=True))
            except Exception as exc:
                state.update(stage="error", error=str(exc))
                self.send(_error_page(str(exc)))
                finished.set()

    server = HTTPServer((host, port), Handler)
    browser_open(f"http://{host}:{server.server_port}/")
    try:
        while not finished.is_set():
            server.handle_request()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 2 if state["stage"] == "error" else 0


def run_friendly(argv, *, pick=pick_folder, run=run_audit, render=to_html, show=open_in_browser,
                 wizard=run_wizard, out=print) -> int:
    """Pick a folder (or take one as argv[0]), audit it, and open the ledger in the browser.

    Returns 0 when a report was shown (or the reviewer cancelled) and 2 when the folder could not be
    reviewed — the verdict itself lives in the browser page, not the exit code.
    """
    from sc_referee.design import DesignError
    from sc_referee.ingest import IngestError

    if argv:
        folder = Path(argv[0])
    else:
        try:
            folder = pick()
        except Exception:                # tkinter missing, or no display available
            out("Could not open a folder picker. Pass the folder path instead:  "
                "referee /path/to/analysis")
            return 2
        if folder is None:
            out("No folder selected — nothing to review.")
            return 0

    # Ask/confirm the experimental design before auditing, so the report can render a blocking,
    # human-ratified verdict. A cancelled wizard writes nothing; the audit then renders the honest
    # "Proposed" report (unchanged from before the wizard existed).
    try:
        wizard(folder)
    except (IngestError, FileNotFoundError) as e:
        out(f"Cannot review this folder: {e}")
        return 2

    try:
        result = run(folder)
    except (IngestError, FileNotFoundError) as e:
        out(f"Cannot review this folder: {e}")
        return 2
    except DesignError as e:
        out(f"The confirmed design has a problem: {e}")
        return 2

    show(render(result))
    out("Opened the report in your browser.")
    return 0


def main() -> None:
    from sc_referee.environment import load_local_env

    load_local_env()
    folder = Path(sys.argv[1]) if sys.argv[1:] else None
    sys.exit(serve_friendly_app(folder))


if __name__ == "__main__":
    main()
