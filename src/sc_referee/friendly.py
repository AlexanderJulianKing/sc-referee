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
import subprocess
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
    SUPPORTED_TYPES, Question, ReviewClaim, ReviewFact, _CSS, _confirm_page,
    _existing_confirmed_config, _reported_for_folder, answers_to_config, design_questions,
    render_form, run_wizard,
)


class PickerError(RuntimeError):
    """The native folder chooser could not be run (no display / tkinter missing, or the helper crashed)."""


def _as_text(raw) -> str:
    """Decode subprocess output to text without ever raising (the result line is ASCII JSON)."""
    if isinstance(raw, bytes):
        return raw.decode("utf-8", "replace")
    return raw or ""


def _parse_picker_output(stdout: str) -> dict | None:
    """The chooser helper's validated JSON result, or None if it emitted no well-formed result line.

    Tolerant of stray stdout printed around the result (e.g. a Tk deprecation notice) and strict about the
    shape: the last line that parses to ``{"ok": <bool>, "path": <str|null>, ...}`` wins; anything else is
    ignored rather than mistaken for a selection or a cancellation.
    """
    for line in reversed((stdout or "").splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except ValueError:
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("ok"), bool):
            continue
        path = payload.get("path")
        if path is not None and not isinstance(path, str):
            continue
        return payload
    return None


def _ask_directory(*, python: str | None = None, run=subprocess.run) -> str:
    """Return the chosen directory ("" if cancelled) by running the chooser in a short-lived helper process.

    The native panel calls Tk(), which on macOS makes the calling process a foreground NSApplication for the
    rest of its life. Running it in this long-lived server would leave an unresponsive "python" app
    beach-balling in front of the browser after the panel closes. So the chooser is isolated in
    ``sc_referee._folder_picker``: when that helper process exits, macOS reclaims the GUI app and returns
    focus to the browser, and this server never initializes Tk. Raises PickerError if the helper can't run.

    The helper is launched by its absolute file path (not ``-m sc_referee._folder_picker``): ``-m`` puts the
    launch directory first on the child's path, so a stray ``sc_referee/`` folder in the reviewer's working
    directory could shadow the real package. The helper imports no sc_referee code, so a plain path works.
    """
    helper = str(Path(__file__).with_name("_folder_picker.py"))
    try:
        proc = run([python or sys.executable, helper], capture_output=True)
    except OSError as exc:
        raise PickerError(f"could not launch the folder chooser: {exc}") from exc

    # Prefer the helper's own result: it reports a graceful failure as {"ok": false, "error": ...} on
    # stdout even when it exits non-zero, so we keep that message instead of a bare exit status.
    payload = _parse_picker_output(_as_text(proc.stdout))
    if payload is not None:
        if not payload["ok"]:
            raise PickerError(str(payload.get("error") or "the folder chooser failed"))
        return payload.get("path") or ""

    # No well-formed result line: the helper crashed before it could emit one.
    tail = (_as_text(proc.stderr).strip().splitlines() or [""])[-1]
    raise PickerError(f"the folder chooser failed (status {proc.returncode}) {tail}".rstrip())


def pick_folder(*, ask=_ask_directory) -> Path | None:
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
            ".welcome h1{font-size:clamp(38px,7vw,62px);line-height:.98;letter-spacing:-.035em;"
            "font-weight:650;max-width:10ch;margin:0 0 25px}"
            ".welcome-lede{font-size:18px;line-height:1.55;color:var(--mut);max-width:53ch;margin:0}"
            ".welcome-action{display:flex;align-items:center;gap:20px;flex-wrap:wrap;margin-top:31px}"
            ".welcome-action .run{margin:0;padding:14px 22px;transition:background-color 160ms ease-out,"
            "color 160ms ease-out,transform 120ms ease-out}.welcome-action .run:hover{background:var(--accent)}"
            ".welcome-action .run:focus-visible{outline:3px solid var(--accent);outline-offset:3px}"
            ".welcome-action .run:active{transform:translateY(1px)}.local{font-family:var(--mono);font-size:11px;"
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
            "<section class='welcome-hero'><div class='welcome-kicker'>STATISTICAL REVIEW FOR SINGLE-CELL ANALYSIS</div>"
            "<h1>Catch the mistakes review misses.</h1>"
            "<p class='welcome-lede'>sc-referee checks single-cell data, results, and code for statistical "
            "mistakes that slip through human and AI review. Claude reconstructs the design; you confirm it; "
            "deterministic verifiers test the result and abstain when evidence is missing.</p>"
            f"{notice}<div class='welcome-action'><form method='post' action='/choose'>"
            "<button class='run' type='submit'>Choose analysis folder&nbsp; →</button></form>"
            "<span class='local'>runs locally · source files stay unchanged</span></div></section>"
            "<section class='welcome-steps' aria-label='How the review works'>"
            "<div class='welcome-step'><b>01</b><h2>Reconstruct</h2><p>Read the data, results, metadata, "
            "and code to determine what was actually tested.</p></div>"
            "<div class='welcome-step'><b>02</b><h2>Confirm</h2><p>Review and correct the proposed "
            "scientific design before it drives the audit.</p></div>"
            "<div class='welcome-step'><b>03</b><h2>Verify</h2><p>Run deterministic checks and report "
            "findings, discrepancies, and evidence limits.</p></div>"
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


_CAPSULE_ERROR_MESSAGE = "Referee could not complete this review from the supplied analysis folder."


class _CapsuleFriendlyError(RuntimeError):
    """Internal marker-path failure whose public text is deliberately fixed and generic."""


def _capsule_confirm_page(manifest) -> str:
    """Confirm a reconstructed analysis and answer the scientific context Referee needs.

    This is deliberately the ORDINARY design-review experience — same header, sections, copy and controls
    as the standard wizard. The compiled-capsule mechanism is an internal implementation detail and is
    never surfaced (no "capsule", "evidence sources", benchmark values, or "deterministic replay").
    """
    questions = [
        Question(
            role=question.group.lower(),
            prompt=question.prompt,
            why=question.why,
            kind="radio",
            options=("yes", "no", "not_sure"),
            default=question.default,
        )
        for question in manifest.questions
    ]
    label = {
        "eqtl": "Expression quantitative trait locus under review",
        "condition_contrast_DE": "Differential expression under review",
    }.get(manifest.analysis, "Scientific claim under review")
    claim = ReviewClaim(
        label=label,
        title=manifest.presentation.claim_title,
        facts=tuple(
            ReviewFact(label=fact.label, value=fact.value, caution=fact.caution)
            for fact in manifest.presentation.facts
        ),
    )
    return render_form(questions, claim=claim, reconstruction=manifest.reconstruction)


def _capsule_answers_from_form(manifest, answers) -> dict:
    """Map submitted radios to one ceremony answer per question — FAIL-CLOSED.

    An absent or unrecognized field becomes "not_sure" (unanswered), never a silent "yes": a crafted or
    empty POST must not authorize the finding. The form always pre-checks a value, so ordinary submits are
    unaffected; only a malformed submit is forced to abstain.
    """
    resolved = {}
    for question in manifest.questions:
        raw = answers.get(question.group.lower())
        if raw is None:  # Backward-compatible with pages opened before this presentation update.
            raw = answers.get(f"q__{question.group}")
        # Only a single recognized value authorizes. Missing, unrecognized, OR ambiguous (a duplicate
        # multi-valued field) fails closed to "not_sure" — a crafted POST cannot force a "yes".
        if isinstance(raw, list):
            raw = raw[0] if len(raw) == 1 else None
        resolved[question.group] = raw if raw in ("yes", "no", "not_sure") else "not_sure"
    return resolved


def _capsule_report(manifest, folder, answers) -> str:
    """Run the deterministic audit + replay for a compiled analysis and render the ORDINARY shared report.

    No bespoke panel, no benchmark values, no "replay MATCH", no "capsule": the reviewer sees a standard
    confirmed-eQTL report carrying the verifier's actual Finding. The only augmentation is a fixed,
    benchmark-free boundary sentence appended to a flagged finding's verdict (the scientific claim itself
    is the verifier's, unmodified).
    """
    from dataclasses import replace

    from sc_referee import statuses as S
    from sc_referee.audit import AuditResult
    from sc_referee.checks.allele_orientation import AlleleOrientationCheck
    from sc_referee.checks.base import Finding
    from sc_referee.checks.eqtl_design_support import EqtlDesignSupportCheck
    from sc_referee.compiler.capsule_kinds import get_capsule_kind, run_capsule_audit
    from sc_referee.compiler.capsule_manifest import verify_capsule_artifacts

    artifacts_dir = verify_capsule_artifacts(manifest, folder)   # re-check in the worker thread
    kind = get_capsule_kind(manifest.kind)
    result = run_capsule_audit(kind, artifacts_dir, answers)

    if result.finding is not None:
        src = result.finding
        verdict = src.verdict
        if S.human_state(src) == S.FLAGGED and kind.finding_boundary:
            verdict = f"{src.verdict} {kind.finding_boundary}"
        # Build a COPY (never mutate the verifier's finding, which the compile result also holds). Drop
        # conditional_on: its premise block dumps internal, dataset-specific provenance identities (scope
        # digests, estimand/basis ids) that must never reach the report; the verdict already states the
        # conditionality in prose.
        finding = Finding(src.check_id, src.status, verdict, metrics=src.metrics,
                          citations=src.citations, fix=src.fix, conditional_on=None,
                          applicability=src.applicability, judgment=src.judgment,
                          coverage=src.coverage, proof_grade=src.proof_grade)
    else:
        # A compilation abstention — surface a generic, leak-free message; internal detail stays internal.
        finding = Finding("contamination_confound", S.NEEDS_EVIDENCE,
                          "Referee could not complete this review from the supplied inputs.",
                          coverage=S.NOT_RUN)
    findings = [finding]
    if result.compilation is not None:
        compilation = result.compilation
        findings.append(EqtlDesignSupportCheck().run(
            compilation.design, compilation.bundle, compilation.bundle.reported_results,
        ))
        # The prepared fixture carries an internal benchmark locator, not a biological variant ID.
        # Treat it as absent in the product-facing orientation review so internal benchmark identity
        # cannot leak and the report asks for the real scientific metadata it needs.
        orientation_design = replace(compilation.design, variant_id=None)
        findings.append(AlleleOrientationCheck().run(
            orientation_design, compilation.bundle, compilation.bundle.reported_results,
        ))
    audit = AuditResult(
        findings=findings,
        analysis_type=manifest.analysis,
        confirmed_by_human=True,
        review_title=manifest.presentation.claim_title,
        review_recognition=manifest.presentation.recognition,
    )
    return to_html(audit)


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
                       choose=_ask_directory, host="127.0.0.1", port=0) -> int:
    """Run the complete friendly workflow in one localhost tab.

    The browser owns explanation and state; the OS owns choosing a local path; a worker thread owns
    the expensive audit so the waiting page can report honestly instead of appearing frozen.
    """
    import yaml

    from sc_referee import init as _init
    from sc_referee.compiler.capsule_kinds import get_capsule_kind
    from sc_referee.compiler.capsule_manifest import (
        CAPSULE_MANIFEST_NAME,
        load_capsule_manifest,
        verify_capsule_artifacts,
    )
    from sc_referee.ingest import ingest

    state = {"stage": "welcome", "folder": None, "bundle": None, "config": None,
             "capsule": None, "page": None, "report": None, "error": None}
    finished = threading.Event()

    def prepare(selected: Path):
        # A compiled-analysis capsule carries an explicit typed marker and no ordinary count matrix, so it
        # is recognized here — BEFORE standard ingest — and routed to its own confirm/audit path.
        if (selected / CAPSULE_MANIFEST_NAME).is_file():
            try:
                manifest = load_capsule_manifest(selected)
                if manifest is None:  # The marker was present, so this is a defensive fail-closed guard.
                    raise ValueError("marker disappeared while the folder was being prepared")
                verify_capsule_artifacts(manifest, selected)
                get_capsule_kind(manifest.kind)
            except Exception:
                # Marker parsing, provenance, and kind details are internal and may contain sensitive
                # identities or filenames. Only the fixed reviewer-safe message may cross this boundary.
                raise _CapsuleFriendlyError(_CAPSULE_ERROR_MESSAGE) from None
            state.update(stage="design", folder=selected, capsule=manifest, bundle=None,
                         config=None, page=_capsule_confirm_page(manifest))
            return
        bundle = ingest(selected)
        existing = _existing_confirmed_config(selected)
        config, source = ((existing, "confirmed_config") if existing is not None
                          else _init.propose(selected))
        questions = design_questions(config, list(bundle.observations.columns),
                                     analysis_types=SUPPORTED_TYPES)
        if questions:
            questions[0] = replace(questions[0], proposal_source=source)
        state.update(stage="design", folder=selected, capsule=None, bundle=bundle, config=config,
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
                try:
                    selected = choose()
                except PickerError:
                    self.send(_welcome_page(
                        "Could not open the folder chooser here. Re-run from a terminal as:  "
                        "referee /path/to/folder"))
                    return
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

            if state.get("capsule") is not None:
                manifest, selected = state["capsule"], state["folder"]
                premise_answers = _capsule_answers_from_form(manifest, answers)
                state["stage"] = "running"

                def capsule_worker():
                    try:
                        state["report"] = _capsule_report(manifest, selected, premise_answers)
                        state["stage"] = "done"
                    except Exception:
                        state.update(stage="error", error=_CAPSULE_ERROR_MESSAGE)

                threading.Thread(target=capsule_worker, daemon=True).start()
                self.send(_confirm_page(
                    workload=manifest.title,
                    estimate="Usually a few seconds for an analysis of this size.",
                    poll=True))
                return

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
