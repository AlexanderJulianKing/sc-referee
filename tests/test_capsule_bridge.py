"""The compiled-analysis capsule bridge: an ordinary browser review, capsule mechanism invisible.

These tests pin the separation Alexander requires: the reviewer experiences an ordinary analysis folder
(design confirmation + shared report), while the capsule marker, digests, registry, deterministic compile
audit, and replay stay internal. No external benchmark truth (+0.4839 / −0.600 / reference answer) may reach
any user-facing payload; the confirmation answers must genuinely drive abstention; provenance/replay integrity
must remain intact; and the bridge must be kind-based, never keyed on a dataset name.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from sc_referee.compiler.capsule_kinds import (
    CapsuleKind,
    UnknownCapsuleKind,
    get_capsule_kind,
    register_capsule_kind,
    run_capsule_audit,
)
from sc_referee.compiler.capsule_manifest import (
    CAPSULE_MANIFEST_NAME,
    CAPSULE_SCHEMA,
    CapsuleManifestError,
    load_capsule_manifest,
    verify_capsule_artifacts,
)
from sc_referee.compiler.pipeline import CompileAuditResult
from sc_referee.derivations.gbp07_capsule import CAPSULE_KIND, gbp07_zip_path, prepare_gbp07_capsule
from sc_referee.friendly import (
    _capsule_answers_from_form,
    _capsule_confirm_page,
    _capsule_report,
    serve_friendly_app,
)


# Every token that must never appear in a user-facing payload (confirm page or report). Includes the
# lowercase/internal forms that hide in identities and metrics (e.g. "estimand:gbp07-eqtl:v1").
FORBIDDEN_UI_TERMS = (
    "GB-P07", "gbp07", "GeneBench", "genebench", "benchmark", "reference answer", "0.4839", "0.600",
    "capsule", "compiled analysis", "evidence source", "deterministic replay", "replay match",
    "submission.csv", "estimand:", "basis:", "row_ledger", "fitted_design_identity", "csp:",
)


def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _synthetic_capsule(folder: Path, *, kind="synthetic_kind/v1") -> Path:
    """A minimal, benchmark-free capsule folder with a NON-GB-P07 kind — proves generality."""
    artifacts = folder / "inputs"
    artifacts.mkdir(parents=True)
    payload = b"col_a,col_b\n1,2\n"
    (artifacts / "table.csv").write_bytes(payload)
    manifest = {
        "capsule_schema": CAPSULE_SCHEMA,
        "capsule_kind": kind,
        "title": "Some analysis",
        "analysis": "eqtl",
        "reconstruction": "I read this as an analysis of X on Y. Is that right?",
        "artifacts_dir": "inputs",
        "provenance": {"source": "internal fixture", "artifacts": {"table.csv": _sha(payload)}},
        "questions": [
            {"group": "Measurement", "prompt": "Is Q1 true?", "why": "because", "default": "yes"},
            {"group": "Timing", "prompt": "Is Q2 true?", "why": "because", "default": "yes"},
        ],
    }
    (folder / CAPSULE_MANIFEST_NAME).write_text(yaml.safe_dump(manifest, sort_keys=False))
    return folder


@pytest.fixture
def gbp07_folder(tmp_path):
    if not gbp07_zip_path().exists():
        pytest.skip("GB-P07 benchmark archive not available in this environment")
    prepare_gbp07_capsule(tmp_path)
    return tmp_path


def _compile_result(summary="synthetic result"):
    return CompileAuditResult(
        normal_audit_applies=False,
        proposal=None,
        finding=None,
        capsule=None,
        replay_status=None,
        summary=summary,
    )


def _start_app(folder):
    import threading
    import time

    opens = []
    threading.Thread(target=lambda: serve_friendly_app(
        folder, browser_open=lambda url: opens.append(url), choose=lambda: None, port=0),
        daemon=True).start()
    for _ in range(300):
        if opens:
            return opens[0].rstrip("/")
        time.sleep(0.02)
    raise AssertionError("friendly app did not start")


def _get(base, path):
    import urllib.request

    return urllib.request.urlopen(base + path, timeout=10).read().decode()


def _assert_generic_error_page(html):
    assert "Referee could not complete this review from the supplied analysis folder." in html
    assert not any(term.lower() in html.lower() for term in FORBIDDEN_UI_TERMS)


# --- 1. detection before ingest, and honest degradation ------------------------------------------

def test_no_marker_is_not_a_capsule(tmp_path):
    (tmp_path / "something.txt").write_text("hi")
    assert load_capsule_manifest(tmp_path) is None      # falls through to ordinary ingest


def test_capsule_marker_is_recognized_without_a_matrix(tmp_path):
    _synthetic_capsule(tmp_path)
    manifest = load_capsule_manifest(tmp_path)           # recognized despite no count matrix
    assert manifest is not None and manifest.kind == "synthetic_kind/v1"
    assert [q.group for q in manifest.questions] == ["Measurement", "Timing"]


def test_malformed_manifest_raises_not_silently_ingests(tmp_path):
    (tmp_path / CAPSULE_MANIFEST_NAME).write_text("capsule_schema: wrong/schema@v9\n")
    with pytest.raises(CapsuleManifestError):
        load_capsule_manifest(tmp_path)
    (tmp_path / CAPSULE_MANIFEST_NAME).write_text(": : not valid yaml : :")
    with pytest.raises(CapsuleManifestError):
        load_capsule_manifest(tmp_path)


def test_missing_required_key_raises(tmp_path):
    (tmp_path / CAPSULE_MANIFEST_NAME).write_text(yaml.safe_dump({
        "capsule_schema": CAPSULE_SCHEMA, "capsule_kind": "k", "title": "t",
        "analysis": "eqtl", "reconstruction": "r", "artifacts_dir": "x",
        "provenance": {"source": "s", "artifacts": {"a": "sha256:00"}},
        # no questions
    }))
    with pytest.raises(CapsuleManifestError):
        load_capsule_manifest(tmp_path)


# --- 2. provenance / digest verification (honest abstention) -------------------------------------

def test_verify_passes_when_digests_match(tmp_path):
    _synthetic_capsule(tmp_path)
    manifest = load_capsule_manifest(tmp_path)
    assert verify_capsule_artifacts(manifest, tmp_path).name == "inputs"


def test_verify_abstains_on_missing_artifacts(tmp_path):
    _synthetic_capsule(tmp_path)
    manifest = load_capsule_manifest(tmp_path)
    (tmp_path / "inputs" / "table.csv").unlink()
    with pytest.raises(CapsuleManifestError):
        verify_capsule_artifacts(manifest, tmp_path)


def test_verify_abstains_on_digest_mismatch(tmp_path):
    _synthetic_capsule(tmp_path)
    manifest = load_capsule_manifest(tmp_path)
    (tmp_path / "inputs" / "table.csv").write_bytes(b"tampered")
    with pytest.raises(CapsuleManifestError, match="provenance mismatch"):
        verify_capsule_artifacts(manifest, tmp_path)


def test_verify_converts_artifacts_directory_symlink_escape(tmp_path):
    selected = _synthetic_capsule(tmp_path / "selected")
    manifest = load_capsule_manifest(selected)
    (selected / "inputs" / "table.csv").unlink()
    (selected / "inputs").rmdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "table.csv").write_bytes(b"col_a,col_b\n1,2\n")
    (selected / "inputs").symlink_to(outside, target_is_directory=True)

    with pytest.raises(CapsuleManifestError):
        verify_capsule_artifacts(manifest, selected)


def test_verify_converts_artifact_symlink_escape(tmp_path):
    selected = _synthetic_capsule(tmp_path / "selected")
    manifest = load_capsule_manifest(selected)
    (selected / "inputs" / "table.csv").unlink()
    outside = tmp_path / "outside.csv"
    outside.write_bytes(b"col_a,col_b\n1,2\n")
    (selected / "inputs" / "table.csv").symlink_to(outside)

    with pytest.raises(CapsuleManifestError):
        verify_capsule_artifacts(manifest, selected)


# --- 3. registry is kind-based and dataset-name-independent ---------------------------------------

def test_registry_resolves_the_gbp07_kind():
    kind = get_capsule_kind(CAPSULE_KIND)
    assert isinstance(kind, CapsuleKind) and callable(kind.runner)


def test_registry_dispatches_via_each_kinds_runner(tmp_path):
    calls = []
    expected = _compile_result()

    def unrelated_runner(artifacts_dir, answers):
        calls.append((artifacts_dir, answers))
        return expected

    kind = CapsuleKind(kind="unrelated_workflow/v1", runner=unrelated_runner)
    register_capsule_kind(kind)
    answers = {"Different question": "yes"}

    registered = get_capsule_kind("unrelated_workflow/v1")
    assert run_capsule_audit(registered, tmp_path, answers) is expected
    assert calls == [(tmp_path, answers)]


def test_unknown_kind_raises_not_falls_back_to_gbp07():
    with pytest.raises(UnknownCapsuleKind):
        get_capsule_kind("no_such_kind/v1")


def test_bridge_source_has_no_dataset_name_conditional():
    # The general bridge (marker parser + friendly routing) must route on the typed kind, never on a
    # benchmark id or folder name. (capsule_kinds legitimately imports the builtin kind to register it.)
    import sc_referee.compiler.capsule_manifest as m
    import sc_referee.friendly as f
    for module in (m, f):
        src = Path(module.__file__).read_text().lower()
        assert "gb-p07" not in src and "gbp07" not in src and "genebench" not in src, module.__name__


# --- 4. confirmation drives the audit, replay + provenance stay intact (needs the archive) --------

def test_all_yes_flags_and_replays_match(gbp07_folder):
    manifest = load_capsule_manifest(gbp07_folder)
    result = run_capsule_audit(get_capsule_kind(manifest.kind),
                               verify_capsule_artifacts(manifest, gbp07_folder),
                               {q.group: "yes" for q in manifest.questions})
    assert result.finding is not None and result.finding.status == "major"
    assert result.replay_status is not None and result.replay_status.value == "match"


def test_not_sure_makes_the_check_abstain(gbp07_folder):
    manifest = load_capsule_manifest(gbp07_folder)
    answers = {q.group: ("not_sure" if q.group == "Measurement" else "yes") for q in manifest.questions}
    result = run_capsule_audit(get_capsule_kind(manifest.kind),
                               verify_capsule_artifacts(manifest, gbp07_folder), answers)
    assert result.finding.status == "needs_evidence"      # a single "not sure" abstains, not flags


# --- 5. confirm page: ordinary wizard vocabulary, no leakage --------------------------------------

def test_confirm_page_reads_as_the_ordinary_wizard(tmp_path):
    _synthetic_capsule(tmp_path)
    html = _capsule_confirm_page(load_capsule_manifest(tmp_path))
    assert "Review my read of your analysis" in html
    assert "What the folder cannot establish" in html
    assert "set up · design" in html and "Confirm design and run review" in html
    assert "Expression quantitative trait locus under review" in html and "Some analysis" in html
    assert 'name="measurement"' in html and 'value="not_sure"' in html


def test_confirm_page_excludes_every_forbidden_term(gbp07_folder):
    html = _capsule_confirm_page(load_capsule_manifest(gbp07_folder)).lower()
    for term in FORBIDDEN_UI_TERMS:
        assert term.lower() not in html, term


def test_answers_from_form_maps_and_fails_closed(tmp_path):
    manifest = load_capsule_manifest(_synthetic_capsule(tmp_path))
    resolved = _capsule_answers_from_form(manifest, {"measurement": "no"})
    assert resolved == {"Measurement": "no", "Timing": "not_sure"}  # missing -> fail closed
    assert _capsule_answers_from_form(manifest, {"timing": ["not_sure"]})["Timing"] == "not_sure"
    assert _capsule_answers_from_form(manifest, {"timing": "unexpected"})["Timing"] == "not_sure"
    # A duplicate (multi-valued) field is ambiguous -> fail closed, never authorize on the first value.
    assert _capsule_answers_from_form(manifest, {"measurement": ["yes", "not_sure"]})["Measurement"] == "not_sure"


# --- 6. failure pages: fixed reviewer-safe text, no internal exception details -------------------

@pytest.mark.parametrize("failure", ("missing artifact", "malformed manifest"))
def test_prepare_failure_renders_only_generic_error(tmp_path, failure):
    if failure == "missing artifact":
        _synthetic_capsule(tmp_path)
        (tmp_path / "inputs" / "table.csv").unlink()
    else:
        (tmp_path / CAPSULE_MANIFEST_NAME).write_text(": : malformed capsule GB-P07 submission.csv")

    html = _get(_start_app(tmp_path), "/")
    _assert_generic_error_page(html)


def test_worker_exception_renders_only_generic_error(tmp_path, monkeypatch):
    import json
    import time
    import urllib.parse
    import urllib.request
    import sc_referee.friendly as friendly

    kind_name = "worker_failure_workflow/v1"
    _synthetic_capsule(tmp_path, kind=kind_name)
    register_capsule_kind(CapsuleKind(kind=kind_name, runner=lambda folder, answers: _compile_result()))

    def fail_with_internal_detail(*args, **kwargs):
        raise RuntimeError(
            "fresh compiler capsule did not replay exactly; GB-P07 submission.csv row_ledger")

    monkeypatch.setattr(friendly, "_capsule_report", fail_with_internal_detail)
    base = _start_app(tmp_path)
    body = urllib.parse.urlencode({"measurement": "yes", "timing": "yes"}).encode()
    waiting = urllib.request.urlopen(
        urllib.request.Request(base + "/submit", data=body, method="POST"), timeout=10).read().decode()
    assert not any(term.lower() in waiting.lower() for term in FORBIDDEN_UI_TERMS)

    for _ in range(300):
        if json.loads(_get(base, "/status"))["stage"] == "error":
            break
        time.sleep(0.02)
    else:
        raise AssertionError("worker failure did not reach the error state")

    _assert_generic_error_page(_get(base, "/error"))


# --- 7. report: ordinary shared report, finding + boundary, no leakage ----------------------------

def test_report_excludes_every_forbidden_term(gbp07_folder):
    manifest = load_capsule_manifest(gbp07_folder)
    html = _capsule_report(manifest, gbp07_folder, {q.group: "yes" for q in manifest.questions})
    low = html.lower()
    for term in FORBIDDEN_UI_TERMS:
        assert term.lower() not in low, term


def test_report_carries_the_verifier_finding_and_boundary(gbp07_folder):
    manifest = load_capsule_manifest(gbp07_folder)
    html = _capsule_report(manifest, gbp07_folder, {q.group: "yes" for q in manifest.questions})
    assert "Referee verified that the fitted model does not include that basis" in html  # finding
    assert "confirmed adjustment is missing, but not how the omission affected" in html  # boundary
    assert "1 finding needs your attention" in html                    # flagged hero
    assert "3 checks: 1 flagged · 1 need review · 1 passed" in html
    assert "donor-level design with 24 distinct donors" in html
    assert "Genotype dosage counts are 0: 8, 1: 8, 2: 8" in html
    assert "folder does not establish which allele the genotype dosage counts" in html
    assert "effect allele, variant alleles, ploidy" in html
    assert "CXCL10 expression ~ genotype" in html                      # same claim identity as setup
    assert "evaluated per donor" in html                               # same scientific framing as setup


def test_report_makes_no_bare_causal_claim(gbp07_folder):
    manifest = load_capsule_manifest(gbp07_folder)
    html = _capsule_report(manifest, gbp07_folder, {q.group: "yes" for q in manifest.questions})
    # The only permitted uses of "caused/affected" are the explicit NON-claims of causation.
    import re
    for sentence in re.split(r"(?<=[.!?])\s+", re.sub(r"<[^>]+>", " ", html)):
        if "caused" in sentence.lower():
            assert "not" in sentence.lower(), sentence


def test_abstained_report_is_needs_review_without_a_boundary(gbp07_folder):
    manifest = load_capsule_manifest(gbp07_folder)
    html = _capsule_report(manifest, gbp07_folder,
                           {q.group: ("not_sure" if q.group == "Measurement" else "yes")
                            for q in manifest.questions})
    assert "confirmed adjustment is missing" not in html               # no boundary on an abstention
    assert "need" in html.lower()                                      # rendered as needs-review, not flagged


# --- 8. full HTTP flow through the friendly route -------------------------------------------------

def test_http_flow_selects_capsule_folder_and_reports(gbp07_folder):
    import json
    import threading
    import time
    import urllib.parse
    import urllib.request

    opens = []
    threading.Thread(target=lambda: serve_friendly_app(
        gbp07_folder, browser_open=lambda u: opens.append(u), choose=lambda: None, port=0),
        daemon=True).start()
    for _ in range(300):
        if opens:
            break
        time.sleep(0.02)
    base = opens[0].rstrip("/")
    get = lambda p: urllib.request.urlopen(base + p, timeout=10).read().decode()

    assert json.loads(get("/status"))["stage"] == "design"
    assert "Review my read of your analysis" in get("/")               # ordinary confirm page, not ingest error
    body = urllib.parse.urlencode({g: "yes" for g in ("measurement", "timing", "estimand", "authority")})
    waiting = urllib.request.urlopen(
        urllib.request.Request(base + "/submit", data=body.encode(), method="POST"),
        timeout=10).read().decode()
    assert "CXCL10 eQTL analysis" in waiting
    assert not any(t.lower() in waiting.lower() for t in FORBIDDEN_UI_TERMS)
    stage = "?"
    for _ in range(150):
        stage = json.loads(get("/status"))["stage"]
        if stage in ("done", "error"):
            break
        time.sleep(0.3)
    assert stage == "done"
    report = get("/report")
    assert "1 finding needs your attention" in report
    assert "3 checks: 1 flagged · 1 need review · 1 passed" in report
    assert not any(t.lower() in report.lower() for t in FORBIDDEN_UI_TERMS)


# --- 9. shared report behavior: a flagged finding reads FLAGGED overall (footer alignment) --------

def test_flagged_finding_reads_flagged_in_the_overall_badge():
    from sc_referee.audit import AuditResult
    from sc_referee.checks.base import Finding
    from sc_referee import statuses as S
    from sc_referee.report import to_html

    html = to_html(AuditResult(findings=[Finding("x", S.MAJOR, "something is off")],
                               analysis_type="eqtl", confirmed_by_human=True))
    overall = html.split("overall review")[1].split("</span>")[1]
    assert "FLAGGED" in overall            # a MAJOR finding must not read CLEAR in the footer
