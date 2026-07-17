"""Report rendering — plain-language first, technical detail underneath. (spec §[5])

The status is deterministic (from the check); this module only *presents* it. A green run
never hides an unaudited analysis: needs_evidence / not_audited are shown, never dropped.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, is_dataclass
import html
import json
import math
from pathlib import Path

from rich.console import Console
from rich.markup import escape

from sc_referee import statuses as S
from sc_referee.engine import BLOCKER_AT

_STYLE = {
    S.BLOCKER: "bold white on red",
    S.MAJOR: "bold black on yellow",
    S.NEEDS_EVIDENCE: "bold cyan",
    S.PASS: "bold green",
    S.NOT_AUDITED: "dim",
    S.INFORMATIONAL: "blue",
}

_TAG = {
    "confounding": "deterministic · power-independent",
    "experimental_unit": "recompute · earned-verdict",
}


def _resolved(value) -> bool:
    """Recognition degrades to silence for absent or explicitly unresolved facts."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"unknown", "unresolved"}
    return True


def _declared_context(result) -> dict:
    """Project only facts that the completed audit retained through its design path.

    A report path is more sensitive than an ordinary design field: it identifies the claim all
    findings are being placed under.  It is therefore included only when human confirmation made
    the declaration authoritative during ingest.  If that binding cannot be recovered, the path
    stays silent rather than being reconstructed from filenames.
    """
    context = {}
    if _resolved(getattr(result, "analysis_type", None)):
        context["analysis_type"] = result.analysis_type

    design_path = getattr(result, "design_path", None)
    if not design_path:
        return context
    try:
        from sc_referee.config import confirmed_reported_path, load_designs

        designs = load_designs(design_path)
        # Findings do not yet carry a contrast index.  With more than one Design, assigning the
        # flat findings to either contrast would be a guess; Phase 3 will supply claim roots.
        if len(designs) == 1:
            design = designs[0]
            for field in ("analysis_type", "unit_of_test"):
                value = getattr(design, field, None)
                if _resolved(value):
                    context[field] = value
            _, reference, test = design.contrast_column_and_levels()
            if _resolved(test) and _resolved(reference):
                context.update(test=test, reference=reference)
        # Ingest grants claim-selection authority only to the canonical in-folder config. An
        # alternate --design file can describe the contrast but did not bind the table.
        canonical_design = (
            Path(result.folder) / "sc-referee.yaml" if getattr(result, "folder", None) else None
        )
        report_path = (
            confirmed_reported_path(design_path)
            if canonical_design is not None
            and Path(design_path).resolve() == canonical_design.resolve()
            else None
        )
        if _resolved(report_path):
            context["report_path"] = report_path
    except (OSError, UnicodeError, TypeError, ValueError):
        # Rendering must not replace an already-computed audit with a presentation-time failure.
        # The retained AuditResult fields above remain safe to describe.
        pass
    return context


def _claim_payload(finding):
    """Return exact claim-root metadata when a finding carries it.

    Phase 1 findings have no dedicated claim field, so all legacy findings fall into the single
    report-bound claim.  The two accepted projections let the grouping remain N-claim capable when
    the coverage phase starts attaching exact roots, without altering Finding in this phase.
    """
    direct = getattr(finding, "claim_root", None)
    if direct is not None:
        return asdict(direct) if is_dataclass(direct) else direct
    metrics = getattr(finding, "metrics", {}) or {}
    for key in ("claim_root", "claim_root_binding"):
        value = metrics.get(key)
        if value is not None:
            return asdict(value) if is_dataclass(value) else value
    return None


def _claim_key(claim) -> str:
    if claim is None:
        return "__single_bound_claim__"
    if isinstance(claim, dict) and any(
        claim.get(field) is not None
        for field in (
            "claim_id", "report_artifact_digest", "report_locator_digest",
            "producing_value_digest",
        )
    ):
        # Auxiliary evidence/diagnostic metadata is not row identity. Keep the certificate binding
        # plus the remaining spec §4 claim-root coordinates, when supplied.
        identity_fields = (
            "kind", "claim_id", "report_artifact_digest", "report_locator_digest",
            "producing_value_digest", "contrast", "test", "reference", "target", "estimand",
            "multiplicity_family",
        )
        claim = {field: claim[field] for field in identity_fields if field in claim}
    return json.dumps(_jsonable(claim), sort_keys=True, separators=(",", ":"), default=str)


def _claim_context(claim, fallback: dict) -> dict:
    context = dict(fallback)
    if not isinstance(claim, dict):
        return context
    # A fallback path names today's singular claim.  It must not leak onto a different explicit
    # root merely because that root carries only digests and no display path.
    context.pop("report_path", None)
    aliases = {
        "analysis_type": ("analysis_type",),
        "test": ("test",),
        "reference": ("reference",),
        "unit_of_test": ("unit_of_test",),
        "report_path": ("report_path", "report_relative_path", "path"),
    }
    for target, candidates in aliases.items():
        for candidate in candidates:
            value = claim.get(candidate)
            if _resolved(value):
                context[target] = value
                break
    return context


def _recognition(context: dict) -> str:
    line = "Analysis"
    if _resolved(context.get("analysis_type")):
        line += f" — {context['analysis_type']}"
    if _resolved(context.get("report_path")):
        line += f"  ({context['report_path']})"

    details = []
    if _resolved(context.get("test")) and _resolved(context.get("reference")):
        details.append(f"{context['test']} vs {context['reference']}")
    if _resolved(context.get("unit_of_test")):
        details.append(f"per {context['unit_of_test']}")
    return line + (f": {', '.join(details)}." if details else ".")


def _coverage(findings) -> dict:
    status_counts = Counter(f.status for f in findings)
    human_counts = Counter(S.human_state(f) for f in findings)
    return {
        "findings": len(findings),
        "human_states": {state: human_counts[state] for state in S.HUMAN_STATES if human_counts[state]},
        # Retain the shipped status inventory for compatibility and differential review. Footer
        # presentation uses human_states only; neither inventory participates in gating.
        "statuses": {status: status_counts[status] for status in S.STATUSES if status_counts[status]},
    }


def _coverage_line(coverage: dict) -> str:
    count = coverage["findings"]
    parts = [f"{count} {'finding' if count == 1 else 'findings'}"]
    labels = {S.NOT_CHECKED: "not checked", S.N_A: "n/a"}
    parts.extend(f"{n} {labels.get(state, state)}"
                 for state, n in coverage["human_states"].items())
    return "coverage: " + " · ".join(parts)


def _analysis_groups(result) -> list[dict]:
    fallback = _declared_context(result)
    default_claim = (
        {"report_path": fallback["report_path"]} if "report_path" in fallback else None
    )
    groups_by_key = {}
    for finding in result.findings:
        claim = _claim_payload(finding)
        if claim is None:
            claim = default_claim
        key = _claim_key(claim)
        if key not in groups_by_key:
            context = _claim_context(claim, fallback)
            groups_by_key[key] = {
                "claim": claim,
                "recognition": _recognition(context),
                "report_path": context.get("report_path"),
                "findings": [],
            }
        groups_by_key[key]["findings"].append(finding)

    # Even an empty result must say what was (not) covered when an analysis is known.
    if not groups_by_key and fallback:
        context = _claim_context(default_claim, fallback)
        groups_by_key[_claim_key(default_claim)] = {
            "claim": default_claim,
            "recognition": _recognition(context),
            "report_path": context.get("report_path"),
            "findings": [],
        }
    groups = list(groups_by_key.values())
    for group in groups:
        group["coverage"] = _coverage(group["findings"])
    return groups


def _withheld_collapse(f):
    """Presentation only: when experimental_unit OBSERVED a blocker-sized collapse but WITHHELD the
    hard block (because the corrected sample-level analysis was underpowered), return the observed
    evidence strength and the verdict qualification as separate pieces — so the report leads with the
    discrepancy instead of burying it under the caveat. Returns None for every other finding.

    Adjudication is untouched: f.status stays needs_evidence, and the thresholds this reads
    (BLOCKER_AT and the check's own powered gate) are unchanged — this only reformats what a human sees.
    """
    if getattr(f, "check_id", None) != "experimental_unit" or f.status != S.NEEDS_EVIDENCE:
        return None
    m = f.metrics or {}
    survival = m.get("survival_rate")
    reported = m.get("valid_reported_sig")
    survived = m.get("survivors")
    # Exactly the underpower-after-collapse gate: every earlier needs_evidence reason is excluded
    # (not comparable, nothing testable, a within-sample covariate, no recorded replicate, <3/arm),
    # and the observed collapse is blocker-sized. Uses only the check's own reported metrics.
    if (survival is None or not reported or survived is None
            or not m.get("comparable") or not m.get("covariates_constant")
            or not m.get("replicate_recorded") or (m.get("n_replicates_per_arm") or 0) < 3
            or m.get("powered") is not False or survival > BLOCKER_AT):
        return None
    reported, survived = int(reported), int(survived)
    collapse = 1.0 - survival
    return {
        "collapse_rate": collapse,
        "headline": (f"Critical discrepancy: {collapse:.1%} of reported discoveries lost "
                     "significance when recomputed at the sample level."),
        "counts": f"{reported:,} reported → {survived:,} survived.",
        "qualification": ("Final blocker withheld: the corrected sample-level analysis was "
                          "underpowered, so disappearance alone is not conclusive."),
    }


def render_tty(result, console: Console | None = None) -> None:
    console = console or Console()
    if result.analysis_type:
        if result.confirmed_by_human:
            console.print(f"[bold]CONFIRMED[/]  {result.analysis_type} [dim](human-ratified)[/]\n")
        else:
            console.print(f"[bold yellow]PROPOSED[/]  {result.analysis_type} "
                          f"[dim](unconfirmed — nothing can block; run [/]sc-referee confirm[dim])[/]\n")

    groups = _analysis_groups(result)
    for index, group in enumerate(groups, start=1):
        path = group["report_path"]
        console.print(f"[bold]▸ Analysis {index}[/]" + (f" — {escape(str(path))}" if path else ""))
        console.print(f"  {escape(group['recognition'])}\n")
        for f in group["findings"]:
            style = _STYLE.get(f.status, "white")
            tag = _TAG.get(f.check_id, "")
            state = S.human_state(f)
            label = {S.NOT_CHECKED: "NOT CHECKED", S.N_A: "N/A"}.get(state, state.upper())
            console.print(f"[{style}] {label} [/] [dim]({f.status})[/]  [bold]{f.check_id}[/]"
                          + (rf"   [dim]\[{tag}][/]" if tag else ""))
            disc = _withheld_collapse(f)
            if disc:
                console.print(f"  [bold red]{escape(disc['headline'])}[/]")
                console.print(f"  [bold]{escape(disc['counts'])}[/]")
                console.print(f"  [dim]{escape(disc['qualification'])}[/]")
            else:
                console.print(f"  {f.verdict}")
            if f.conditional_on is not None:
                marker = f.conditional_on
                dual = bool(marker.component_identities)
                label = ("CONDITIONAL ON BOTH RATIFIED PREMISES" if dual
                         else "CONDITIONAL ON YOUR CONFIRMED PREMISE")
                console.print(f"  [bold]{label}[/]")
                console.print(f"  {escape(marker.plain_language_premise)}")
                if dual:
                    console.print(
                        "  [dim]component identities:[/] "
                        f"{escape(json.dumps(dict(marker.component_identities), sort_keys=True))}"
                    )
                    console.print("  Invalidating either removes authorization for this finding.")
                console.print(
                    f"  [dim]premise contract:[/] {escape(marker.contract_type)} · "
                    f"{escape(marker.contract_id)}"
                )
                console.print(
                    f"  [dim]decisive fields:[/] "
                    f"{escape(json.dumps(dict(marker.decisive_fields), sort_keys=True))}"
                )
                console.print(
                    f"  [dim]bound scope:[/] "
                    f"{escape(json.dumps(dict(marker.scope), sort_keys=True))}"
                )
            if f.metrics.get("aliased_with"):
                console.print(f"  [dim]aliased with:[/] {f.metrics['aliased_with']}")
            for c in f.citations:
                console.print(f"  [dim]ref:[/] {c}")
            console.print()

    conclusion = result.ci_conclusion()
    ci = {"fail": "   [bold red]CI: FAIL[/]",
          "neutral": "   [yellow]CI: neutral[/]" + ("" if result.fully_audited() else " [yellow]— NOT FULLY AUDITED[/]"),
          "pass": "   [green]CI: pass[/]"}[conclusion]
    console.print(f"[dim]worst status:[/] {result.worst_status()}{ci}")
    console.print(f"[dim]{_coverage_line(_coverage(result.findings))}[/]")


def _jsonable(v):
    """Non-finite floats (e.g. vif=inf on an aliased design) are not valid JSON — Python
    would emit a bare `Infinity`, breaking jq and the CI artifact. Render them as strings."""
    if isinstance(v, float):
        if math.isinf(v):
            return "Infinity" if v > 0 else "-Infinity"
        if math.isnan(v):
            return "NaN"
        return v
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    return v


def _finding_dict(f) -> dict:
    payload = {
        "check_id": f.check_id,
        "status": f.status,
        "human_state": S.human_state(f),
        "applicability": f.applicability,
        "judgment": f.judgment,
        "coverage": f.coverage,
        "proof_grade": f.proof_grade,
        "verdict": f.verdict,
        "metrics": _jsonable(f.metrics),
        "citations": f.citations,
        "fix": f.fix,
    }
    if f.conditional_on is not None:
        marker = f.conditional_on
        payload["conditional_on"] = {
            "contract_id": marker.contract_id,
            "contract_type": marker.contract_type,
            "decisive_fields": _jsonable(dict(marker.decisive_fields)),
            "plain_language_premise": marker.plain_language_premise,
            "scope": _jsonable(dict(marker.scope)),
        }
        if marker.component_identities:
            payload["conditional_on"]["component_identities"] = _jsonable(
                dict(marker.component_identities)
            )
    return payload


def to_json(result) -> str:
    groups = _analysis_groups(result)
    # Evidence, never gates. Emitted only when the diagnostic actually produced something, so a
    # result without it is byte-identical to before this field existed (frozen oracles unchanged).
    diagnostics = list(getattr(result, "diagnostics", []) or [])
    extra = {"diagnostics": diagnostics} if diagnostics else {}
    return json.dumps(
        {
            "analysis_type": result.analysis_type,
            "confirmed_by_human": result.confirmed_by_human,
            "worst_status": result.worst_status(),
            "ci_fails": result.ci_fails(),
            "ci_conclusion": result.ci_conclusion(),
            "fully_audited": result.fully_audited(),
            "analyses": [
                {
                    "claim": _jsonable(group["claim"]),
                    "recognition": group["recognition"],
                    "findings": [_finding_dict(f) for f in group["findings"]],
                    "coverage": group["coverage"],
                }
                for group in groups
            ],
            "coverage": _coverage(result.findings),
            # Compatibility projection for the shipped report schema and existing consumers.  The
            # canonical presentation above is grouped; these are the identical finding records.
            "findings": [_finding_dict(f) for f in result.findings],
            **extra,
        },
        indent=2,
        default=str,
    ) + "\n"


def to_md(result) -> str:
    lines = [f"# sc-referee report", ""]
    if result.analysis_type:
        if result.confirmed_by_human:
            lines.append(f"**Confirmed analysis type:** `{result.analysis_type}` (human-ratified)\n")
        else:
            lines.append(f"**Proposed analysis type:** `{result.analysis_type}` "
                         f"(unconfirmed — nothing can block until `sc-referee confirm`)\n")
    for index, group in enumerate(_analysis_groups(result), start=1):
        path = group["report_path"]
        lines.append(f"## Analysis {index}" + (f" — `{path}`" if path else ""))
        lines.append("")
        lines.append(group["recognition"])
        lines.append("")
        for f in group["findings"]:
            lines.append(f"### `{S.human_state(f)}` (`{f.status}`) — {f.check_id}")
            lines.append("")
            disc = _withheld_collapse(f)
            if disc:
                lines.append(f"**{disc['headline']}**")
                lines.append("")
                lines.append(f"**{disc['counts']}**")
                lines.append("")
                lines.append(f"_{disc['qualification']}_")
            else:
                lines.append(f.verdict)
            lines.append("")
            if f.conditional_on is not None:
                marker = f.conditional_on
                dual = bool(marker.component_identities)
                lines.append("**" + (
                    "CONDITIONAL ON BOTH RATIFIED PREMISES" if dual
                    else "CONDITIONAL ON YOUR CONFIRMED PREMISE"
                ) + "**")
                lines.append("")
                lines.append(marker.plain_language_premise)
                lines.append("")
                if dual:
                    lines.append(
                        "Component identities: `" +
                        json.dumps(dict(marker.component_identities), sort_keys=True) + "`"
                    )
                    lines.append("")
                    lines.append("Invalidating either removes authorization for this finding.")
                    lines.append("")
                lines.append(
                    f"Premise contract: `{marker.contract_type}` · `{marker.contract_id}`"
                )
                lines.append("")
                lines.append(
                    "Decisive fields: `" +
                    json.dumps(dict(marker.decisive_fields), sort_keys=True) + "`"
                )
                lines.append("")
                lines.append(
                    "Bound scope: `" + json.dumps(dict(marker.scope), sort_keys=True) + "`"
                )
                lines.append("")
            for c in f.citations:
                lines.append(f"- ref: {c}")
            lines.append("")
    tail = {"fail": "CI **fails**",
            "neutral": "CI **neutral** — posted, not a clean bill of health"
                       + ("" if result.fully_audited() else " (**not fully audited**)"),
            "pass": "CI passes"}[result.ci_conclusion()]
    lines.append(f"**Worst status:** `{result.worst_status()}` — {tail}")
    lines.append("")
    lines.append(f"**Coverage:** {_coverage_line(_coverage(result.findings)).removeprefix('coverage: ')}")
    return "\n".join(lines) + "\n"


# Human-state → (channel label, css state class). Mirrors render_tty's labels exactly, so the browser
# page and the terminal never disagree about a finding's state.
_HTML_STATE = {
    S.CLEAR: ("CLEAR", "s-clear"),
    S.FLAGGED: ("FLAGGED", "s-flagged"),
    S.NOT_CHECKED: ("NOT CHECKED", "s-not-checked"),
    S.N_A: ("N/A", "s-na"),
}

# Precision-instrument aesthetic (see .impeccable.md): a light-first technical datasheet. Monospace for the
# MEASURED tokens (statuses, counts, check ids) where mono means "exact/tabular"; sans for the human
# verdicts. Color is reserved for verdict meaning only; hairline rules; sharp corners; one crisp
# instrument-boot on load. Self-contained + OFFLINE — inline CSS, NO external fetch (opens with no network).
_HTML_CSS = """
:root{color-scheme:light dark;
 --paper:#f4f5f3;--ink:#191b1f;--mut:#5f6670;--dim:#9aa0a8;--rule:#dcdfd9;--rule2:#c3c7c0;
 --clear:#157f3b;--flag:#c1272d;--nc:#9a6b00;--na:#4f5a68;
 --clear-w:#e9f0ea;--flag-w:#f8eae9;--nc-w:#f4edda;--na-w:#eceef1;
 --mono:"JetBrains Mono","SFMono-Regular","Cascadia Code",ui-monospace,Menlo,Consolas,monospace;
 --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
@media(prefers-color-scheme:dark){:root{
 --paper:#111317;--ink:#e7e9ec;--mut:#9aa1ab;--dim:#616772;--rule:#2a2e35;--rule2:#3a3f47;
 --clear:#5bd07f;--flag:#f0817f;--nc:#e0b654;--na:#9fb0c2;
 --clear-w:#14241a;--flag-w:#2a1718;--nc-w:#292112;--na-w:#1a1e25}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;
 line-height:1.55;-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
main{max-width:760px;margin:0 auto;padding:0 22px 72px}
header{display:flex;align-items:baseline;justify-content:space-between;gap:16px;padding:22px 0 14px}
.brand{font-family:var(--mono);font-size:12px;letter-spacing:.26em;text-transform:uppercase;color:var(--mut)}
.brand b{color:var(--ink);font-weight:600}
.hlabel{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}

/* HERO — editorial result first; hierarchy comes from type and space, not a dashboard card */
.hero{border-top:2px solid var(--ink);border-bottom:1px solid var(--rule2);padding:31px 0 29px;margin:0 0 4px}
.hero-head{display:flex;align-items:center;gap:11px}
.hero-led{width:10px;height:10px;flex:none;border-radius:1px}
.hero.s-flagged .hero-led{background:var(--flag)} .hero.s-clear .hero-led{background:var(--clear)}
.hero.s-not-checked .hero-led,.hero.s-discrepancy .hero-led{background:var(--nc)}
.hero.s-na .hero-led{background:var(--na)}
.hero-title{font-size:clamp(32px,6vw,48px);font-weight:650;letter-spacing:-.04em;color:var(--ink);line-height:1.02}
.hero-sum{font-family:var(--mono);font-size:11.5px;letter-spacing:.02em;color:var(--mut);margin-top:17px}
.hero-note{font-size:15px;color:var(--mut);margin-top:12px;line-height:1.55;max-width:62ch}

.ident{font-family:var(--mono);font-size:11.5px;letter-spacing:.07em;text-transform:uppercase;
 color:var(--mut);padding:15px 0 2px}
.ident .ratified{color:var(--clear)}.ident .proposed{color:var(--nc)}
.ident .note{color:var(--dim);text-transform:none;letter-spacing:0}
.analysis{margin:26px 0 0;padding-left:16px;border-left:1px solid var(--rule)}
.a-index{font-family:var(--mono);font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;
 color:var(--dim);margin:0 0 7px}
.a-index b{color:var(--ink);font-weight:600}
.a-title{font-size:26px;line-height:1.12;letter-spacing:-.025em;margin:0 0 5px;font-weight:650}
.a-path{font-family:var(--mono);font-size:10.5px;color:var(--dim);margin:0 0 7px;overflow-wrap:anywhere}
.recognition{margin:0 0 17px;color:var(--mut);font-size:14px;line-height:1.5}

/* channel rows — a flagged channel outweighs a clear one (rhythm, not uniform padding) */
.chan{padding:12px 0;border-top:1px solid var(--rule)}
.chan:first-of-type{border-top:none;padding-top:2px}
.chan.s-flagged{border-top:2px solid var(--flag);padding-top:13px}
/* Unresolved is a state in this completed report, not a promise of an in-page remediation flow. */
.chan.needs-input{border-top-color:var(--nc)}
.tag{font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;
 color:var(--nc);border:1px solid var(--nc);border-radius:2px;padding:1px 6px}
.chan-head{display:flex;align-items:center;gap:9px;flex-wrap:wrap}
.led{width:8px;height:8px;flex:none;border-radius:1px;transform:translateY(1px)}
.state{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.11em}
.check{font-family:var(--mono);font-size:13px;color:var(--ink);font-weight:500}
.verdict{margin:6px 0 0;padding-left:17px;font-size:14.5px;line-height:1.62;color:var(--ink);max-width:62ch}
.chan.s-clear .verdict{color:var(--mut)}
.chan.s-na{padding-top:9px;padding-bottom:9px}
.chan.s-na .check,.chan.s-na .verdict{color:var(--dim)}
.chan.s-na .verdict{font-size:13.5px}
.premise-dependent{margin:10px 17px 2px;padding:10px 12px;border:1px solid var(--rule2);
 background:var(--paper);font-size:12.5px;line-height:1.5}
.premise-label{font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.08em;
 text-transform:uppercase;color:var(--flag);margin-bottom:4px}
.premise-meta{font-family:var(--mono);font-size:10.5px;color:var(--dim);margin-top:5px}
.ref{font-family:var(--mono);font-size:11px;color:var(--dim);padding-left:17px;margin-top:5px}
.s-clear .led{background:var(--clear)}.s-clear .state{color:var(--clear)}
.s-flagged .led{background:var(--flag)}.s-flagged .state{color:var(--flag)}
.s-not-checked .led{background:var(--nc)}.s-not-checked .state{color:var(--nc)}
.s-na .led{background:var(--na)}.s-na .state{color:var(--na)}
footer{margin-top:32px;border-top:2px solid var(--rule2);padding-top:15px;font-family:var(--mono);
 font-size:12px;letter-spacing:.03em}
.readout{display:flex;gap:12px;flex-wrap:wrap;align-items:baseline}
.readout .k,.coverage .k{color:var(--dim);text-transform:uppercase;letter-spacing:.12em;font-size:10.5px}
.readout .worst{color:var(--ink);font-weight:600}
.readout .fail{color:var(--flag)}.readout .pass{color:var(--clear)}.readout .neutral{color:var(--nc)}
.coverage{margin-top:9px;color:var(--mut)}
/* taxonomy legend — teaches the four states inline, so NOT CHECKED vs N/A never puzzles a first-timer */
.legend{margin-top:16px;display:flex;flex-wrap:wrap;gap:6px 18px;font-family:var(--mono);font-size:10.5px;
 letter-spacing:.02em;color:var(--dim)}
.legend .k{text-transform:uppercase;letter-spacing:.12em}
.legend span b{font-weight:600}
.legend .lc{color:var(--clear)}.legend .lf{color:var(--flag)}.legend .ln{color:var(--nc)}.legend .la{color:var(--na)}
.discrepancy{margin:.1em 0 .2em}
.disc-headline{margin:.15em 0;font-weight:600;color:var(--nc);font-size:15px}
.disc-counts{margin:.15em 0;font-family:var(--mono);font-size:13px}
.disc-qual{margin:.15em 0;color:var(--mut);font-size:13px}
@media(prefers-reduced-motion:no-preference){
 .hero{animation:boot .42s cubic-bezier(.2,.7,.2,1) both}
 .chan{animation:boot .36s cubic-bezier(.2,.7,.2,1) both;animation-delay:calc(.08s + var(--i,0)*26ms)}
 @keyframes boot{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}}
"""


def _html_finding(f, i) -> str:
    # One channel row. Only the human state shows on the line; the raw engine status lives in the
    # hover title so the primary read isn't two status vocabularies competing (quieter, not lossy).
    # A needs-evidence result remains visibly unresolved, without implying this static endpoint has
    # another form waiting behind it.
    label, cls = _HTML_STATE.get(S.human_state(f), (S.human_state(f).upper(), "s-na"))
    if _needs_input(f):
        cls += " needs-input"
    disc = _withheld_collapse(f)
    if disc:
        verdict_html = (
            '<div class="discrepancy">'
            f'<p class="disc-headline">{html.escape(disc["headline"])}</p>'
            f'<p class="disc-counts">{html.escape(disc["counts"])}</p>'
            f'<p class="disc-qual">{html.escape(disc["qualification"])}</p>'
            '</div>'
        )
    else:
        verdict_html = f'<p class="verdict">{html.escape(str(f.verdict))}</p>'
    check_label = {
        "inference.enrichment_universe": "analysis universe",
    }.get(str(f.check_id), str(f.check_id).replace("_", " "))
    parts = [
        f'<div class="chan {cls}" style="--i:{i}" title="engine status: {html.escape(str(f.status))}">',
        '<div class="chan-head">',
        '<span class="led"></span>',
        f'<span class="state">{label}</span>',
        f'<span class="check">{html.escape(check_label)}</span>',
        ('<span class="tag">unresolved</span>' if _needs_input(f) else ''),
        '</div>',
        verdict_html,
    ]
    if f.conditional_on is not None:
        marker = f.conditional_on
        dual = bool(marker.component_identities)
        label = ("CONDITIONAL ON BOTH RATIFIED PREMISES" if dual
                 else "CONDITIONAL ON YOUR CONFIRMED PREMISE")
        parts.extend([
            '<div class="premise-dependent">',
            f'<div class="premise-label">{label}</div>',
            f'<div>{html.escape(marker.plain_language_premise)}</div>',
            f'<div class="premise-meta">{html.escape(marker.contract_type)} · '
            f'{html.escape(marker.contract_id)}</div>',
            f'<div class="premise-meta">decisive · '
            f'{html.escape(json.dumps(dict(marker.decisive_fields), sort_keys=True))}</div>',
            f'<div class="premise-meta">scope · '
            f'{html.escape(json.dumps(dict(marker.scope), sort_keys=True))}</div>',
        ])
        if dual:
            parts.extend([
                f'<div class="premise-meta">component identities · '
                f'{html.escape(json.dumps(dict(marker.component_identities), sort_keys=True))}</div>',
                '<div>Invalidating either removes authorization for this finding.</div>',
            ])
        parts.append('</div>')
    for c in f.citations:
        parts.append(f'<div class="ref">ref&nbsp;· {html.escape(str(c))}</div>')
    parts.append('</div>')
    return "".join(parts)


def _needs_input(f) -> bool:
    """An ACTIONABLE not-checked: the analyst must supply something (a NEEDS_EVIDENCE abstention that
    landed in not-checked because its coverage is NOT_RUN — e.g. an unratified contract), as opposed to
    a benign NOT_AUDITED where there is nothing for them to do."""
    return S.human_state(f) == S.NOT_CHECKED and f.status == S.NEEDS_EVIDENCE


def _finding_rank(f) -> int:
    # Serious first, then an observed-but-qualified collapse, then other unresolved evidence.
    hstate = S.human_state(f)
    if hstate == S.FLAGGED:
        return 0
    if _withheld_collapse(f):
        return 1
    if hstate == S.NOT_CHECKED:
        return 2 if _needs_input(f) else 3
    if hstate == S.N_A:
        return 5
    return 4


def _hero(result) -> str:
    """The measured outcome first, followed immediately by its evidential qualification."""
    from collections import Counter
    findings = result.findings
    hs = Counter(S.human_state(f) for f in findings)
    flagged, clear, na = hs[S.FLAGGED], hs[S.CLEAR], hs[S.N_A]
    needs_input = sum(1 for f in findings if _needs_input(f))
    benign_nc = hs[S.NOT_CHECKED] - needs_input
    withheld = next((disc for f in findings if (disc := _withheld_collapse(f))), None)

    if flagged:
        state = "s-flagged"
        title = (f"{flagged} finding{'' if flagged == 1 else 's'} "
                 f"need{'s' if flagged == 1 else ''} your attention")
        note = ("Flagged doesn't mean your analysis is wrong — it means these need a look before you "
                "trust the result. Each finding below says exactly what to check.")
    elif withheld:
        state = "s-discrepancy"
        title = f'{withheld["collapse_rate"]:.1%} lost significance after correcting the experimental unit'
        note = ("After treating biological samples — not individual cells — as independent, "
                f'{withheld["counts"]} {withheld["qualification"]}')
    elif needs_input:
        state = "s-not-checked"
        title = f"{needs_input} check{'' if needs_input == 1 else 's'} unresolved"
        note = (f"Referee completed this review. {needs_input} check"
                f"{'' if needs_input == 1 else 's'} could not reach a verdict from the evidence "
                f"supplied. {'It remains' if needs_input == 1 else 'They remain'} not checked — "
                "neither cleared nor flagged. Each result below "
                "explains the limitation.")
    elif benign_nc:
        state = "s-not-checked"
        title = "Nothing flagged"
        note = (f"But {benign_nc} check{'' if benign_nc == 1 else 's'} couldn't run — a clean report "
                "here means “we found no problem,” not “guaranteed correct.”")
    elif clear:
        state = "s-clear"
        title = "All clear"
        note = "Every claim in this analysis held up to an independent recomputation."
    else:
        state = "s-na"
        title = "Nothing to report"
        note = "No applicable checks ran on this analysis."
    order = [(flagged, "flagged"), (needs_input, "unresolved"), (clear, "clear"),
             (benign_nc, "not checked"), (na, "n/a")]
    seg = " · ".join(f"{n} {lab}" for n, lab in order if n)
    parts = [f'<div class="hero {state}"><div class="hero-head"><span class="hero-led"></span>'
             f'<span class="hero-title">{html.escape(title)}</span></div>']
    if seg:
        parts.append(f'<div class="hero-sum">{html.escape(seg)}</div>')
    parts.append(f'<div class="hero-note">{html.escape(note)}</div></div>')
    return "".join(parts)


def _analysis_title(group, result) -> str:
    claim = group.get("claim")
    if isinstance(claim, dict):
        claim_id = claim.get("claim_id")
        if _resolved(claim_id):
            name = str(claim_id).removeprefix("claim:")
            if name and not name.startswith("results/"):
                return name.replace("_", " ").strip().capitalize()
        analysis_type = claim.get("analysis_type")
    else:
        analysis_type = None
    analysis_type = analysis_type or getattr(result, "analysis_type", None)
    return {
        "condition_contrast_DE": "Differential expression between conditions",
        "marker_detection": "Marker detection",
        "differential_abundance": "Differential abundance",
        "trajectory": "Trajectory analysis",
        "eqtl": "Expression quantitative trait locus",
    }.get(str(analysis_type), str(analysis_type or "Analysis").replace("_", " ").capitalize())


def to_html(result) -> str:
    """Render the per-claim ledger as a self-contained, OFFLINE HTML page in the precision-instrument
    aesthetic (.impeccable.md) — the browser view the friendly `referee` launcher opens. Pure
    presentation over the same _analysis_groups / human_state the TTY and Markdown renderers use, so the
    three can never disagree about a verdict."""
    worst = result.worst_status()
    body = ['<main>',
            '<header><span class="brand">sc<b>·</b>referee</span>'
            '<span class="hlabel">report</span></header>',
            _hero(result)]
    if result.analysis_type:
        analysis_label = {
            "condition_contrast_DE": "differential expression between conditions",
            "marker_detection": "marker detection",
        }.get(str(result.analysis_type), str(result.analysis_type).replace("_", " "))
        if result.confirmed_by_human:
            body.append(f'<div class="ident" data-analysis-type="{html.escape(str(result.analysis_type))}">'
                        '<span class="ratified">■ confirmed</span> · '
                        f'{html.escape(analysis_label)}</div>')
        else:
            body.append(f'<div class="ident" data-analysis-type="{html.escape(str(result.analysis_type))}">'
                        '<span class="proposed">□ proposed</span> · '
                        f'{html.escape(analysis_label)} '
                        f'<span class="note">— nothing can block until you confirm the design</span></div>')

    i = 0
    for index, group in enumerate(_analysis_groups(result), start=1):
        path = group["report_path"]
        body.append('<section class="analysis">')
        body.append(f'<p class="a-index">analysis <b>{index:02d}</b></p>')
        body.append(f'<h2 class="a-title">{html.escape(_analysis_title(group, result))}</h2>')
        if path:
            body.append(f'<p class="a-path">{html.escape(str(path))}</p>')
        recognition = str(group["recognition"])
        if "): " in recognition:
            recognition = recognition.split("): ", 1)[1]
        elif ": " in recognition:
            recognition = recognition.split(": ", 1)[1]
        body.append(f'<p class="recognition">{html.escape(recognition)}</p>')
        findings = sorted(group["findings"], key=lambda f: (_finding_rank(f), str(f.check_id)))
        for f in findings:
            i += 1
            body.append(_html_finding(f, i))
        body.append('</section>')
        i += 1

    conclusion = result.ci_conclusion()
    ci_txt = {"fail": "CI FAIL",
              "neutral": "CI NEUTRAL" + ("" if result.fully_audited() else " · NOT FULLY AUDITED"),
              "pass": "CI PASS"}[conclusion]
    coverage = _coverage_line(_coverage(result.findings)).removeprefix("coverage: ")
    body.append(
        '<footer>'
        f'<div class="readout"><span class="k">worst</span>'
        f'<span class="worst">{html.escape(worst)}</span>'
        f'<span class="{conclusion}">{html.escape(ci_txt)}</span></div>'
        f'<div class="coverage"><span class="k">coverage</span> &nbsp;{html.escape(coverage)}</div>'
        '<div class="legend"><span class="k">states</span>'
        '<span><b class="lc">clear</b> passed a recompute</span>'
        '<span><b class="lf">flagged</b> needs your review</span>'
        "<span><b class=\"ln\">not checked</b> couldn't verify</span>"
        "<span><b class=\"la\">n/a</b> doesn't apply here</span></div>"
        '</footer>')
    body.append('</main>')

    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>sc-referee report</title>"
        f"<style>{_HTML_CSS}</style></head><body>\n"
        + "\n".join(body)
        + "\n</body></html>\n"
    )
