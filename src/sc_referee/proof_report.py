"""Renderer-independent evidence model for a deterministic scientific-claim audit."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
import hashlib
import math
from pathlib import Path
import shlex
from string import Formatter

from sc_referee import statuses as S
from sc_referee.registry import CHECKS

PROOF_STATE_BY_STATUS = {
    S.BLOCKER: "PROVED_VIOLATION",
    S.PASS: "PROVED_CONFORMANT",
    S.NEEDS_EVIDENCE: "UNRESOLVED_CONTRACT",
    S.NOT_AUDITED: "NOT_AUDITED",
    S.MAJOR: "PROVED_DEFECT",
    S.INFORMATIONAL: "INFORMATIONAL",
}
PROOF_STATES = tuple(dict.fromkeys(PROOF_STATE_BY_STATUS.values()))
PROVED_ADVERSE_STATES = frozenset(("PROVED_VIOLATION", "PROVED_DEFECT"))
PROOF_BASES = frozenset((
    "independent recompute", "design-matrix algebra", "provenance/static",
))


@dataclass(frozen=True)
class InputDigest:
    role: str
    path: str | None
    sha256: str | None
    available: bool
    reason: str | None = None


@dataclass(frozen=True)
class ProofStateCount:
    proof_state: str
    count: int


@dataclass(frozen=True)
class ProofFinding:
    check_id: str
    audit_dimensions: tuple[str, ...]
    proof_state: str
    raw_status: str
    claim: str | None
    contract: dict
    proof_basis: str
    evidence: dict
    verdict: str
    citations: tuple[str, ...]
    dimensions_are_causal: bool


@dataclass(frozen=True)
class ProofReport:
    analysis_type: str | None
    overall_status: str
    ci_conclusion: str
    replay_command: str
    input_digests: tuple[InputDigest, ...]
    coverage: tuple[ProofStateCount, ...]
    findings: tuple[ProofFinding, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_digest(value) -> str | None:
    text = str(value).lower() if value is not None else ""
    return text if len(text) == 64 and all(c in "0123456789abcdef" for c in text) else None


def _digest_entry(role, path_text, *, folder, declared_digest=None, reason=None):
    digest = _valid_digest(declared_digest)
    if not path_text:
        if digest:
            return InputDigest(role, None, digest, True, "digest supplied by provenance")
        return InputDigest(
            role, None, None, False,
            reason or "no input path or digest was available from bundle provenance",
        )
    path = Path(path_text)
    if digest:
        return InputDigest(role, str(path_text), digest, True, "digest supplied by provenance")
    if not path.is_absolute() and folder is None:
        return InputDigest(
            role, str(path_text), None, False,
            "relative provenance path cannot be resolved without the analysis folder",
        )
    resolved = path if path.is_absolute() else folder / path
    if not resolved.exists() or not resolved.is_file():
        return InputDigest(
            role, str(path_text), None, False,
            f"input path does not exist or is not a file: {resolved}",
        )
    try:
        return InputDigest(role, str(path_text), _sha256(resolved), True, "sha256 computed from input")
    except OSError as error:
        return InputDigest(role, str(path_text), None, False, f"sha256 could not be formed: {error}")


def _input_digests(audit_result, bundle, folder):
    design_path = getattr(audit_result, "design_path", None)
    if design_path is None and folder is not None:
        design_path = str(folder / "sc-referee.yaml")
    entries = [_digest_entry("design", design_path, folder=folder,
                             reason="the design YAML path was not available")]

    provenance = getattr(bundle, "provenance", None) or {}
    if not provenance:
        entries.append(InputDigest(
            "data", None, None, False,
            "bundle provenance did not identify the data input; no digest was fabricated",
        ))
        return tuple(entries)
    for role, info in provenance.items():
        if not isinstance(info, dict):
            entries.append(InputDigest(
                str(role), None, None, False,
                "provenance entry was not a structured path/digest record",
            ))
            continue
        raw_path = str(info.get("path") or "")
        whole = Path(raw_path) if raw_path else None
        whole_resolved = (whole if whole is not None and whole.is_absolute()
                          else (folder / whole if whole is not None and folder is not None else None))
        # Provenance currently represents some multi-file roles as comma-separated text. Prefer an
        # actual whole path first so a legitimate filename containing a comma is never split.
        if whole_resolved is not None and whole_resolved.is_file():
            paths = [raw_path]
        else:
            paths = [part.strip() for part in raw_path.split(",") if part.strip()]
        if not paths:
            entries.append(_digest_entry(
                str(role), None, folder=folder, reason=info.get("reason")))
            continue
        for index, path in enumerate(paths):
            entry_role = str(role) if index == 0 else f"{role}:{index + 1}"
            declared = info.get("sha256") or info.get("digest") if len(paths) == 1 else None
            entries.append(_digest_entry(
                entry_role, path, folder=folder, declared_digest=declared,
                reason=info.get("reason"),
            ))
    return tuple(entries)


def _plain_value(value):
    if hasattr(value, "item") and callable(value.item):
        try:
            value = value.item()
        except (TypeError, ValueError):
            pass
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return [_plain_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _plain_value(item) for key, item in value.items()}
    return value


def _contract(check, design):
    fields = getattr(check, "contract_fields", ())
    return {
        "confirmed_by_human": bool(getattr(design, "confirmed_by_human", False)),
        "confidence": dict(getattr(design, "confidence", {}) or {}),
        "facts": {name: _plain_value(getattr(design, name, None)) for name in fields},
    }


def _claim(check, design):
    template = getattr(check, "claim_template", None)
    if not template:
        return None
    fields = [name for _, name, _, _ in Formatter().parse(template) if name]
    values = {name: getattr(design, name, None) for name in fields}
    if any(value is None for value in values.values()):
        return None
    return template.format(**values)


def _abstention_reason(finding):
    metrics = finding.metrics or {}
    for key in ("recompute_reason", "report_binding_reason", "coverage_reason", "reason"):
        if metrics.get(key):
            return str(metrics[key])
    unresolved = metrics.get("unresolved_contract") or metrics.get("missing_fields")
    if unresolved:
        values = unresolved if isinstance(unresolved, (list, tuple)) else [unresolved]
        return "unresolved contract: " + ", ".join(map(str, values))
    if finding.status == S.NEEDS_EVIDENCE:
        return "required evidence remains unresolved"
    return "required audit prerequisite was unavailable"


def _proof_basis(check, finding):
    if finding.status in (S.NEEDS_EVIDENCE, S.NOT_AUDITED):
        return f"abstention: {_abstention_reason(finding)}"
    basis = getattr(check, "proof_basis_by_status", {}).get(
        finding.status, getattr(check, "proof_basis", None))
    if basis not in PROOF_BASES:
        raise ValueError(f"check {finding.check_id!r} has unsupported proof_basis {basis!r}")
    return basis


def _replay_command(audit_result, folder):
    audit_folder = folder or (Path(audit_result.folder) if getattr(audit_result, "folder", None)
                              else Path("."))
    design_path = (Path(audit_result.design_path)
                   if getattr(audit_result, "design_path", None)
                   else audit_folder / "sc-referee.yaml")
    engine = getattr(audit_result, "engine", None) or "pydeseq2"
    return " ".join((
        "sc-referee", "audit", shlex.quote(str(audit_folder)), "--design",
        shlex.quote(str(design_path)), "--engine", shlex.quote(str(engine)),
    ))


def build_proof_report(audit_result, design, bundle, *, folder=None) -> ProofReport:
    """Build presentation-neutral proof facts; never reinterpret verdict prose."""
    folder = Path(folder) if folder is not None else (
        Path(audit_result.folder) if getattr(audit_result, "folder", None) else None)
    checks = {check.id: check for check in CHECKS}
    proof_findings = []
    counts = {state: 0 for state in PROOF_STATES}
    for finding in audit_result.findings:
        if finding.status not in PROOF_STATE_BY_STATUS:
            raise ValueError(f"unknown Finding status {finding.status!r}")
        state = PROOF_STATE_BY_STATUS[finding.status]
        counts[state] += 1
        check = checks.get(finding.check_id)
        dimensions = tuple(getattr(check, "audit_dimensions", ()))
        causal = bool(
            state in PROVED_ADVERSE_STATES
            and len(dimensions) == 1
            and dimensions != ("advisory_policy",)
        )
        proof_findings.append(ProofFinding(
            check_id=finding.check_id,
            audit_dimensions=dimensions,
            proof_state=state,
            raw_status=finding.status,
            claim=_claim(check, design) if check else None,
            contract=_contract(check, design) if check else {
                "confirmed_by_human": bool(getattr(design, "confirmed_by_human", False)),
                "confidence": dict(getattr(design, "confidence", {}) or {}),
                "facts": {},
            },
            proof_basis=_proof_basis(check, finding) if check else (
                f"abstention: {_abstention_reason(finding)}"),
            evidence=dict(finding.metrics or {}),
            verdict=finding.verdict,
            citations=tuple(finding.citations or ()),
            dimensions_are_causal=causal,
        ))
    return ProofReport(
        analysis_type=audit_result.analysis_type,
        overall_status=audit_result.worst_status(),
        ci_conclusion=audit_result.ci_conclusion(),
        replay_command=_replay_command(audit_result, folder),
        input_digests=_input_digests(audit_result, bundle, folder),
        coverage=tuple(ProofStateCount(state, counts[state]) for state in PROOF_STATES),
        findings=tuple(proof_findings),
    )


_STATE_DISPLAY = {
    "PROVED_VIOLATION": ("Proved violation", "brick"),
    "PROVED_DEFECT": ("Proved defect", "brick"),
    "UNRESOLVED_CONTRACT": ("Unresolved contract", "ochre"),
    "NOT_AUDITED": ("Not audited", "slate"),
    "INFORMATIONAL": ("Informational", "slate"),
    "PROVED_CONFORMANT": ("Proved conformant", "pine"),
}
_ANALYSIS_LABEL = {
    "condition_contrast_DE": "Differential expression",
    "eqtl": "Ambient/state-aware eQTL",
    "hic_loop_strength": "Hi-C chromatin-loop strength",
    "marker_detection": "Marker detection",
}
_DIMENSION_LABEL = {
    "unit_of_independence": "unit of independence", "orientation": "orientation",
    "inclusion_set": "inclusion set", "conditioning_set": "conditioning", "scale": "scale",
    "selection": "selection", "estimand": "estimand", "weighting": "weighting",
    "calibration": "calibration", "advisory_policy": "advisory policy",
}


def _humanize(key: str) -> str:
    text = str(key).replace("_", " ").strip()
    return (text[:1].upper() + text[1:]) if text else text


def _fmt_scalar(value) -> str | None:
    value = _plain_value(value)
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if not math.isfinite(value):
            return "nan" if math.isnan(value) else ("inf" if value > 0 else "-inf")
        return f"{round(value, 3):g}"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return value
    return None


def _measurements(evidence: dict):
    """(label, kind, payload) rows from a finding's raw metrics, in stable order. kind is 'num' (a
    formatted number, rendered as a big figure), 'text' (a short string), or 'tags' (a flat list)."""
    rows = []
    for key, value in evidence.items():
        plain = _plain_value(value)
        if isinstance(plain, bool):
            rows.append((_humanize(key), "text", "yes" if plain else "no"))
        elif isinstance(plain, (int, float)):
            scalar = _fmt_scalar(plain)
            if scalar is not None:
                rows.append((_humanize(key), "num", scalar))
        elif isinstance(plain, str):
            rows.append((_humanize(key), "text", plain))
        elif isinstance(plain, list) and plain and all(not isinstance(v, (dict, list)) for v in plain):
            rows.append((_humanize(key), "tags", [str(v) for v in plain]))
    return rows


def _e(text) -> str:
    return escape(str(text))


def render_proof_report_html(report: ProofReport, *, external_reference: dict | None = None) -> str:
    """Render the ProofReport as a self-contained styled HTML proof report.

    Generic over any audit: the headline (worst) finding is shown in full claim -> contract -> proof
    basis -> arithmetic -> verdict grammar; any remaining findings are listed. The signal colour tracks
    the overall proof state. `external_reference` is an OPTIONAL case-study annotation (e.g. a benchmark
    truth the tool does not itself know); it renders as a clearly-separated exhibit only when supplied.
    """
    state = PROOF_STATE_BY_STATUS.get(report.overall_status, "NOT_AUDITED")
    display, signal = _STATE_DISPLAY.get(state, ("Not audited", "slate"))
    findings = list(report.findings)
    headline = next((f for f in findings if f.raw_status == report.overall_status),
                    findings[0] if findings else None)
    others = [f for f in findings if f is not headline]
    analysis = _ANALYSIS_LABEL.get(report.analysis_type or "", report.analysis_type or "analysis")

    parts = []
    if headline is not None:
        dims = " · ".join(_DIMENSION_LABEL.get(d, d) for d in headline.audit_dimensions) or "—"
        claim = (_e(headline.claim) if headline.claim
                 else "This analysis reports no single bound scalar for this check.")
        parts.append(
            f'<div class="step" data-n="01"><div class="h">The claim</div>'
            f'<div class="claim">{claim}</div>'
            f'<div class="dim"><s>failure shape —</s> {_e(dims)}</div></div>')

        facts = (headline.contract.get("facts") or {})
        rows = [(k, v) for k, v in facts.items() if v is not None and v != [] and v != {}]
        conf = "human-confirmed" if headline.contract.get("confirmed_by_human") else "not human-confirmed"
        contract_rows = "".join(
            f'<div class="ctrow"><span class="k">{_e(_humanize(k))}</span>'
            f'<span class="v">{_e(_fmt_scalar(v) if _fmt_scalar(v) is not None else v)}</span></div>'
            for k, v in rows)
        contract_rows += (f'<div class="ctrow"><span class="k">Ratification</span>'
                          f'<span class="v">{_e(conf)}</span></div>')
        parts.append(f'<div class="step" data-n="02"><div class="h">Ratified contract</div>{contract_rows}</div>')

        parts.append(
            f'<div class="step" data-n="03"><div class="h">Proof basis</div>'
            f'<div class="basis">{_e(headline.proof_basis)}</div></div>')

        def _cell(kind, payload):
            if kind == "num":
                return f'<div class="n{" hi" if str(payload)[:1] == "-" else ""}">{_e(payload)}</div>'
            if kind == "tags":
                return f'<div class="tags">{"".join(f"<span>{_e(t)}</span>" for t in payload)}</div>'
            return f'<div class="nv">{_e(payload)}</div>'

        meas = _measurements(headline.evidence)
        if meas:
            mrows = "".join(
                f'<div class="mrow"><div class="t">{_e(label)}</div>{_cell(kind, payload)}</div>'
                for label, kind, payload in meas)
            parts.append(f'<div class="step" data-n="04"><div class="h">Independent arithmetic</div>'
                         f'<div class="meas">{mrows}</div></div>')

    spine = f'<div class="spine">{"".join(parts)}</div>' if parts else ""

    exhibit = ""
    if external_reference:
        exhibit = (
            f'<div class="exhibit"><div class="kick">'
            f'{_e(external_reference.get("label", "External reference — not sc-referee output"))}</div>'
            f'<p>{_e(external_reference.get("body", ""))}</p></div>')

    other_html = ""
    if others:
        items = "".join(
            f'<div class="ofrow"><span class="odot d-{_STATE_DISPLAY.get(f.proof_state, ("", "slate"))[1]}">'
            f'</span><span class="ock">{_e(f.check_id)}</span>'
            f'<span class="ocs">{_e(_STATE_DISPLAY.get(f.proof_state, (f.proof_state, ""))[0])}</span></div>'
            for f in others)
        other_html = f'<div class="others"><div class="kick">Other checks on this analysis</div>{items}</div>'

    digest_bits = " ".join(
        f'<span><b>{_e(d.role)}</b> {_e(d.sha256[:4] + "…" + d.sha256[-4:])}</span>'
        for d in report.input_digests if d.available and d.sha256)
    ci = "did not pass CI" if report.ci_conclusion == S.BLOCKER else "passes CI"
    cert_line = {
        "PROVED_VIOLATION": "The referee recomputed the correct procedure and the claim did not survive it.",
        "PROVED_DEFECT": "The referee recomputed the correct procedure and the claim did not survive it.",
        "UNRESOLVED_CONTRACT": "The referee recomputed, could not settle the claim, and named exactly what it needs — instead of guessing.",
        "NOT_AUDITED": "The referee could not form the proof for this claim, and declined to certify it.",
        "PROVED_CONFORMANT": "The referee recomputed the correct procedure and the claim survived it.",
        "INFORMATIONAL": "The referee recorded a measured fact that is not, by itself, a defect.",
    }.get(state, "")
    cert_head = {
        "PROVED_VIOLATION": "Proved wrong by recomputation.",
        "PROVED_DEFECT": "A measured defect, by recomputation.",
        "UNRESOLVED_CONTRACT": "Neither certified, nor accused.",
        "NOT_AUDITED": "Out of coverage — not certified.",
        "PROVED_CONFORMANT": "Certified by recomputation.",
        "INFORMATIONAL": "Recorded, not a defect.",
    }.get(state, "Verdict recorded.")

    return _TEMPLATE.format(
        signal=signal, analysis=_e(analysis), display=_e(display),
        lede=_e(headline.verdict) if headline else "No findings were produced for this analysis.",
        report_id=_e(report.analysis_type or "analysis"), ci=_e(ci),
        spine=spine, exhibit=exhibit, others=other_html,
        cert_head=_e(cert_head), cert_line=_e(cert_line),
        digests=digest_bits, replay=_e(report.replay_command),
    )


_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>sc-referee — audit report</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --paper:oklch(98.6% 0.008 82);--ink:oklch(26% 0.02 62);--ink2:oklch(46% 0.018 66);--ink3:oklch(63% 0.014 72);
  --rule:oklch(90.5% 0.012 80);--rule2:oklch(84% 0.016 78);
  --brick:oklch(51% 0.16 30);--ochre:oklch(56% 0.125 66);--pine:oklch(47% 0.10 158);--slate:oklch(46% 0.03 250);
  --rust:oklch(47% 0.12 46);--rust-soft:oklch(96% 0.024 52);--sig:var(--{signal});
  --disp:"Space Grotesk",ui-sans-serif,sans-serif;--body:"Instrument Sans",ui-sans-serif,sans-serif;--code:"JetBrains Mono",ui-monospace,monospace;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:oklch(95% 0.01 82);color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}}
.sheet{{max-width:820px;margin:24px auto;background:var(--paper);padding:40px 52px 46px;border:1px solid var(--rule2)}}
.kick{{font-family:var(--disp);font-size:11px;font-weight:500;letter-spacing:.16em;text-transform:uppercase;color:var(--ink3)}}
.mast{{display:flex;justify-content:space-between;align-items:baseline;padding-bottom:26px}}
.wm{{font-family:var(--disp);font-size:17px;font-weight:600;letter-spacing:-.01em;display:flex;align-items:center;gap:11px}}
.wm .tk{{display:inline-flex;gap:3px;align-items:flex-end}}
.wm .tk s{{width:3px;background:var(--ink);text-decoration:none;border-radius:1px}}
.wm .tk s:nth-child(1){{height:9px}}.wm .tk s:nth-child(2){{height:15px;background:var(--sig)}}.wm .tk s:nth-child(3){{height:11px}}
.mast .rt{{text-align:right;line-height:1.7}}.mast .rt div{{font-family:var(--disp);font-size:11px;color:var(--ink3);letter-spacing:.03em}}.mast .rt b{{color:var(--ink2);font-weight:500}}
.hero{{border-top:2px solid var(--ink);padding-top:22px}}
.hero .an{{font-size:16px;color:var(--ink2);max-width:62ch;margin:0 0 22px;line-height:1.5}}
.ruling{{font-family:var(--disp);font-weight:600;font-size:clamp(38px,7vw,58px);line-height:1;letter-spacing:-.025em;color:var(--sig);margin:0}}
.ruling::before{{content:"";display:block;width:52px;height:5px;background:var(--sig);margin-bottom:20px}}
.lede{{font-size:16.5px;line-height:1.55;max-width:58ch;margin:18px 0 0;color:var(--ink)}}
.spine{{margin:38px 0 0;padding-left:34px;border-left:1px solid var(--rule2);position:relative}}
.step{{position:relative;padding:0 0 30px}}.step:last-child{{padding-bottom:6px}}
.step::before{{content:attr(data-n);position:absolute;left:-34px;top:-2px;width:34px;text-align:center;font-family:var(--disp);font-size:11px;font-weight:600;color:var(--sig);background:var(--paper);padding:2px 0}}
.step .h{{font-family:var(--disp);font-size:11.5px;font-weight:600;letter-spacing:.13em;text-transform:uppercase;color:var(--ink3);margin-bottom:11px}}
.claim{{font-size:19px;line-height:1.4}}
.dim{{display:inline-block;font-family:var(--disp);font-size:11px;font-weight:500;letter-spacing:.04em;color:var(--ink2);border-bottom:2px solid var(--sig);padding-bottom:1px;margin-top:13px}}
.dim s{{color:var(--ink3);text-decoration:none;letter-spacing:.1em;text-transform:uppercase;font-size:10px}}
.ctrow{{display:flex;justify-content:space-between;gap:20px;padding:8px 0;border-bottom:1px solid var(--rule)}}
.ctrow:last-child{{border-bottom:none}}.ctrow .k{{color:var(--ink2)}}
.ctrow .v{{font-family:var(--disp);font-variant-numeric:tabular-nums;font-size:14px}}
.basis{{font-size:16px;line-height:1.55;max-width:60ch}}
.meas{{display:flex;flex-direction:column}}
.mrow{{display:flex;align-items:baseline;justify-content:space-between;gap:24px;padding:12px 0;border-bottom:1px solid var(--rule)}}
.mrow:last-child{{border-bottom:none}}.mrow .t{{font-size:14px;color:var(--ink2)}}
.mrow .n{{font-family:var(--disp);font-variant-numeric:tabular-nums;font-size:26px;font-weight:600;line-height:1;letter-spacing:-.01em}}
.mrow .n.hi{{color:var(--sig)}}
.mrow .nv{{font-family:var(--disp);font-size:13.5px;color:var(--ink2);text-align:right;max-width:58%;line-height:1.45}}
.mrow .tags{{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}}
.mrow .tags span{{font-family:var(--disp);font-size:12px;color:var(--sig);border-bottom:2px solid var(--sig);padding-bottom:1px}}
.exhibit{{margin:32px 0 6px;background:var(--rust-soft);padding:20px 24px}}
.exhibit .kick{{color:var(--rust)}}.exhibit p{{margin:9px 0 0;font-size:14.5px;color:var(--ink2);line-height:1.55;max-width:64ch}}
.others{{margin:30px 0 0}}.others .kick{{margin-bottom:12px}}
.ofrow{{display:flex;align-items:center;gap:12px;padding:9px 0;border-top:1px solid var(--rule)}}
.odot{{width:9px;height:9px;border-radius:50%;flex:none}}.d-brick{{background:var(--brick)}}.d-ochre{{background:var(--ochre)}}.d-pine{{background:var(--pine)}}.d-slate{{background:var(--slate)}}
.ock{{font-family:var(--disp);font-size:13.5px;font-weight:500}}.ocs{{margin-left:auto;color:var(--ink2);font-size:13.5px}}
.cert{{margin-top:36px;padding-top:22px;border-top:2px solid var(--ink)}}
.cert .row{{display:flex;align-items:center;gap:16px}}
.cert .tag{{font-family:var(--disp);font-size:9px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink);border:1.5px solid var(--ink);border-radius:50%;width:62px;height:62px;flex:none;display:flex;align-items:center;justify-content:center;text-align:center;line-height:1.35;padding:6px}}
.cert .txt b{{font-family:var(--disp);font-size:17px;font-weight:600;display:block;letter-spacing:-.01em}}
.cert .txt span{{color:var(--ink2);font-size:13.5px}}
.cert .meta{{display:flex;gap:24px;flex-wrap:wrap;margin-top:20px;padding-top:16px;border-top:1px solid var(--rule);font-family:var(--code);font-size:11px;color:var(--ink3)}}
.cert .meta b{{color:var(--ink2);font-weight:400}}.cert .meta .cmd{{color:var(--pine)}}
@media(max-width:680px){{.sheet{{padding:28px 24px}}}}
</style></head>
<body><div class="sheet">
  <div class="mast"><div class="wm"><span class="tk"><s></s><s></s><s></s></span>sc-referee</div>
    <div class="rt"><div><b>report</b> {report_id}</div><div><b>result</b> {ci}</div></div></div>
  <div class="hero"><p class="an">{analysis} — audited by sc-referee: proposed by an analyst, ratified once by a human, decided by arithmetic.</p>
    <h1 class="ruling">{display}</h1><p class="lede">{lede}</p></div>
  {spine}
  {exhibit}
  {others}
  <div class="cert"><div class="row"><div class="tag">Verdict by arithmetic</div>
    <div class="txt"><b>{cert_head}</b><span>{cert_line} No language model participated in this verdict.</span></div></div>
    <div class="meta">{digests}<span class="cmd">&#8250; {replay}</span></div></div>
</div></body></html>
"""
