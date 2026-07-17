"""sc-referee CLI.

    sc-referee init  ./analysis --out sc-referee.yaml   # propose (plain) + human confirms  [D4]
    sc-referee audit ./analysis --design sc-referee.yaml # deterministic verdict; exits nonzero on blocker
    sc-referee fix   ./analysis --check experimental_unit --out template.py   # [D5]
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from sc_referee.audit import run_audit, run_audit_with_inputs
from sc_referee.report import render_tty, to_json, to_md

app = typer.Typer(add_completion=False, help="The bioinformatics reviewer you can leave behind.")
console = Console()


@app.command()
def audit(
    folder: Path = typer.Argument(..., help="Analysis folder (data + results, ideally code)."),
    design: Optional[Path] = typer.Option(None, "--design", help="Confirmed sc-referee.yaml (defaults to <folder>/sc-referee.yaml)."),
    engine: str = typer.Option("pydeseq2", "--engine", help="Recompute engine: pydeseq2 (can block) or simple (advisory only)."),
    json_out: Optional[Path] = typer.Option(None, "--json", help="Write the report as JSON."),
    md_out: Optional[Path] = typer.Option(None, "--md", help="Write the report as Markdown."),
    html_out: Optional[Path] = typer.Option(
        None, "--html", help="Write a renderer-independent Scientific Claim Proof Report as HTML."),
):
    """Re-run the statistically correct procedure and render a graded verdict.

    Exit codes:  0 = no blocker · 1 = blocker · 2 = the design cannot be evaluated (config error).
    """
    from sc_referee.design import DesignError
    from sc_referee.ingest import IngestError

    if engine not in ("pydeseq2", "simple"):
        console.print(f"[bold red]unknown engine[/] {engine!r} — choose pydeseq2 or simple")
        raise typer.Exit(code=2)
    try:
        if html_out:
            result, proof_designs, proof_bundle = run_audit_with_inputs(
                folder, design, engine=engine)
        else:
            result = run_audit(folder, design, engine=engine)
    except IngestError as e:
        # Too many candidate matrices: refuse rather than silently audit a partial/wrong scope.
        console.print(f"[bold red]cannot audit[/] {e}")
        raise typer.Exit(code=2)
    except DesignError as e:
        # A blocker means "your science is wrong". This means "your YAML is wrong".
        console.print(f"[bold red]config error[/] in the ratified design: {e}")
        console.print("[dim]No verdict was rendered. Fix sc-referee.yaml and re-run.[/]")
        raise typer.Exit(code=2)

    render_tty(result, console)
    if json_out:
        json_out.write_text(to_json(result))
    if md_out:
        md_out.write_text(to_md(result))
    if html_out:
        import yaml
        from sc_referee.proof_report import build_proof_report, render_proof_report_html

        if len(proof_designs) != 1:
            console.print("[bold red]cannot write proof report[/] the current proof artifact binds "
                          "exactly one contrast; split this multi-contrast audit first")
            raise typer.Exit(code=2)
        # OPTIONAL human-supplied external reference (e.g. a benchmark truth the tool does not itself
        # know). Rendered as a clearly-separated exhibit; never presented as the referee's own output.
        external_reference = None
        design_path = design or (folder / "sc-referee.yaml")
        try:
            raw_cfg = yaml.safe_load(Path(design_path).read_text())
            if isinstance(raw_cfg, dict) and isinstance(raw_cfg.get("external_reference"), dict):
                external_reference = raw_cfg["external_reference"]
        except (OSError, yaml.YAMLError):
            external_reference = None
        proof_report = build_proof_report(
            result, proof_designs[0], proof_bundle, folder=Path(result.folder))
        html_out.write_text(render_proof_report_html(
            proof_report, external_reference=external_reference))
    # Exit 1 means "a ratified analysis has an unresolved blocker". A draft that no human has
    # confirmed never blocks the pipeline: the thesis is that nothing blocks before ratification.
    # (The report still records ci_fails()=True — an unconfirmed analysis is not *certified*, it
    # is only not *blocked*; certification and the pipeline gate are deliberately separate.)
    if result.confirmed_by_human and result.ci_fails():
        raise typer.Exit(code=1)


_SOURCE_LABEL = {
    "hard_signals": ("[teal]deterministic[/]", "unambiguous — Claude was not called"),
    "claude": ("[blue]Claude[/]", "a role was ambiguous; the model reasoned across the signals"),
    "heuristic_no_llm": ("[yellow]heuristic[/]", "no model available — roles left unresolved"),
}


@app.command("compile")
def compile_folder(
    folder: Path = typer.Argument(..., help="Analysis folder to resolve on the opt-in compiler path."),
    answer: list[str] = typer.Option(
        [], "--answer", help="Scientific ceremony decision, e.g. measurement=yes (repeat four times)."
    ),
    yes: bool = typer.Option(False, "--yes", help="Answer yes to all four scientific confirmations."),
    confirm_bindings: Optional[str] = typer.Option(
        None,
        "--confirm-bindings",
        help="Confirm the exact proposal ID printed by a prior review-only compile run.",
    ),
):
    """Compile a raw folder through Claude bindings, human ceremony, and model-free replay."""
    import os
    import sys

    from sc_referee.compiler.pipeline import (
        record_organizational_confirmation,
        render_organizational_review,
        run_compile_audit,
    )
    from sc_referee.csp_contracts.contamination_condensed_ceremony import (
        CondensedAnswer,
        CondensedGroup,
    )

    if yes and answer:
        console.print("[bold red]cannot compile[/] use either --yes or --answer, not both")
        raise typer.Exit(code=2)

    decisions: dict[CondensedGroup, CondensedAnswer] = {}
    if yes:
        decisions = {group: CondensedAnswer.YES for group in CondensedGroup}
    elif answer:
        for item in answer:
            if "=" not in item:
                console.print(f"[bold red]invalid answer[/] {item!r}; expected group=yes|no|not_sure")
                raise typer.Exit(code=2)
            raw_group, raw_value = item.split("=", 1)
            try:
                group = CondensedGroup(raw_group.strip().title())
                value = CondensedAnswer(
                    raw_value.strip().lower().replace("-", "_").replace(" ", "_")
                )
            except ValueError:
                console.print(f"[bold red]invalid answer[/] {item!r}; expected group=yes|no|not_sure")
                raise typer.Exit(code=2)
            if group in decisions:
                console.print(f"[bold red]invalid answer[/] duplicate decision for {group.value}")
                raise typer.Exit(code=2)
            decisions[group] = value
    elif sys.stdin.isatty():
        prompts = {
            CondensedGroup.MEASUREMENT: "Accept the proposed basis as the scoped contamination measurement?",
            CondensedGroup.TIMING: "Confirm the proposed timing and assignment premises?",
            CondensedGroup.ESTIMAND: "Confirm this exact basis is required for the scoped estimand?",
            CondensedGroup.AUTHORITY: "Accept responsibility for this scientific interpretation?",
        }
        console.print("[bold]Four scientific confirmations[/] [dim](yes/no/not_sure)[/]")
        for group in CondensedGroup:
            raw = typer.prompt(f"{group.value}: {prompts[group]}", default="not_sure")
            normalized = raw.strip().lower().replace("-", "_").replace(" ", "_")
            try:
                decisions[group] = CondensedAnswer(normalized)
            except ValueError:
                console.print(f"[bold red]invalid answer[/] {raw!r}; use yes, no, or not_sure")
                raise typer.Exit(code=2)

    def organizational_reviewer(proposal):
        console.print(render_organizational_review(proposal), markup=False)
        accepted = False
        if confirm_bindings is not None:
            if confirm_bindings != proposal.proposal_id:
                raise ValueError(
                    "--confirm-bindings does not match the current proposal ID; evidence or "
                    "inventory may have changed"
                )
            accepted = True
        elif sys.stdin.isatty():
            accepted = typer.confirm(
                "Accept these exact structural bindings as the organizational mapping?",
                default=False,
            )
        if not accepted:
            return None
        return record_organizational_confirmation(
            proposal,
            actor=os.environ.get("USER", "interactive human"),
        )

    try:
        result = run_compile_audit(
            folder,
            answers=decisions,
            organizational_reviewer=organizational_reviewer,
        )
    except ValueError as exc:
        if not decisions and not os.environ.get("ANTHROPIC_API_KEY") and "four ceremony answers" in str(exc):
            console.print(
                "[yellow]compile needed[/] — provide --yes or all four --answer decisions to run it"
            )
            console.print("[dim]No Claude/model call was made.[/]")
            return
        console.print(f"[bold red]cannot compile[/] {exc}")
        raise typer.Exit(code=2)
    except (OSError, RuntimeError, TypeError, AssertionError) as exc:
        console.print(f"[bold red]cannot compile[/] {exc}")
        raise typer.Exit(code=2)
    console.print(result.summary, markup=False)


@app.command()
def init(
    folder: Path = typer.Argument(..., help="Analysis folder to propose a design for."),
    out: Optional[Path] = typer.Option(None, "--out", help="Defaults to <folder>/sc-referee.yaml."),
):
    """Propose the analysis type + design in plain language, for a human to confirm."""
    from sc_referee.init import propose, write_config
    from sc_referee.ingest import MANIFEST_NAME

    # Multi-file layout with no manifest yet: draft one (enumerate the shards) for the human to fill,
    # BEFORE proposing roles — the design is proposed on the assembled matrix once the manifest exists.
    from sc_referee.manifest import discover_matrix_files
    manifest_path = folder / MANIFEST_NAME
    if not manifest_path.exists() and len(discover_matrix_files(folder)) > 1:
        from sc_referee.layout_proposer import propose_manifest
        from sc_referee.manifest import write_manifest
        man, source = propose_manifest(folder)   # Claude if an API key is present, else deterministic
        write_manifest(man, manifest_path)
        who = {"claude": "[blue]Claude[/] proposed the layout",
               "heuristic_no_llm": "[yellow]deterministic[/] draft — no API key, semantic labels left blank"}[source]
        console.print(f"[bold]MULTI-FILE[/]  {len(man.shards)} shards — {who} [dim](unconfirmed)[/]\n")
        for role, note in man.confidence.items():
            console.print(f"  [green]{role}[/] {note}")          # a design column already in every .obs
        for s in man.shards:
            extra = ", ".join(f"{k}={v}" for k, v in s.constants.items() if k != "sample_id")
            fallback = "[dim]sample_id only — design from .obs[/]" if man.confidence else "[yellow](fill condition/replicate)[/]"
            console.print(f"  [dim]{s.path}[/]  " + (extra or fallback))
        for e in man.excluded:
            console.print(f"  [yellow]excluded[/] {e.get('path')} — {e.get('reason', '')}")
        if man.unresolved:
            console.print(f"\n  [yellow]unresolved:[/] {', '.join(man.unresolved)} — fill these before confirming")
        console.print(f"\n[dim]wrote[/] {manifest_path}\n  [yellow]next:[/] review the layout, then "
                      f"re-run [bold]sc-referee init[/] to propose the design, and [bold]sc-referee confirm[/].")
        raise typer.Exit(code=0)

    out = out or folder / "sc-referee.yaml"
    try:
        proposal, source = propose(folder)
    except ValueError as e:
        (folder / "init_failed.txt").write_text(f"{e}\n")
        console.print(f"[bold red]init failed:[/] {e}")
        raise typer.Exit(code=2)

    who, why = _SOURCE_LABEL[source]
    console.print(f"[bold]PROPOSAL[/]  {proposal['analysis_type']}   {who} [dim]({why})[/]\n")
    console.print(f"  {proposal['plain_summary']}\n")
    for evidence in proposal.get("type_evidence", []):
        console.print(f"  [dim]evidence:[/] {evidence}")
    for role, level in proposal.get("confidence", {}).items():
        style = "green" if level == "high" else "yellow"
        console.print(f"  [dim]confidence:[/] {role} = [{style}]{level}[/]")
    if proposal.get("unresolved"):
        console.print(f"\n  [yellow]unresolved:[/] {', '.join(proposal['unresolved'])} — correct these before confirming")

    write_config(proposal, out)
    console.print(f"\n[dim]wrote[/] {out}  [dim]with[/] confirmed_by_human: [yellow]false[/]")
    console.print("[dim]Nothing can be blocked until you ratify it:[/] sc-referee confirm "
                  f"{out}   [dim](or edit it first)[/]")


@app.command()
def confirm(
    target: Path = typer.Argument(..., help="The analysis folder (or its sc-referee.yaml) to ratify."),
):
    """Ratify a proposal. For a multi-file analysis this RE-DERIVES first: re-assemble from the
    (possibly hand-edited) manifest, re-validate the design against that assembly, record the shards'
    hashes, and only then flip both `confirmed_by_human` flags. Until this runs, no check may block."""
    from sc_referee.config import load_designs
    from sc_referee.design import DesignError, validate_design_against
    from sc_referee.ingest import MANIFEST_NAME, IngestError, ingest
    from sc_referee.init import confirm_config

    folder = target if target.is_dir() else target.parent
    config = folder / "sc-referee.yaml" if target.is_dir() else target
    manifest_path = folder / MANIFEST_NAME

    if manifest_path.exists():
        from sc_referee.manifest import load_manifest, record_hashes, write_manifest
        if load_manifest(manifest_path).unresolved:          # the layout still has open questions
            console.print("[bold red]cannot confirm[/] — the layout has unresolved items:")
            for u in load_manifest(manifest_path).unresolved:
                console.print(f"  [yellow]•[/] {u}")
            console.print("[dim]Resolve them in the manifest, then re-run confirm.[/]")
            raise typer.Exit(code=2)
        try:
            bundle = ingest(folder, confirming=True)     # validation-only; no scientific check runs
        except (IngestError, FileNotFoundError, ValueError) as e:
            console.print(f"[bold red]cannot confirm[/] — the layout no longer assembles: {e}")
            raise typer.Exit(code=2)
        try:
            for dsn in load_designs(config):             # the design must still fit the fresh assembly
                validate_design_against(bundle.observations, dsn)
                need = list(dsn.replicate_unit or []) + list(dsn.batch or [])   # every declared factor
                missing = [c for c in need if c not in bundle.observations.columns]
                if missing:
                    raise DesignError(f"design column(s) {missing} are not present in the assembled "
                                      f"data (columns: {list(bundle.observations.columns)})")
        except DesignError as e:
            console.print(f"[bold red]cannot confirm[/] — the design no longer fits the assembled data: {e}")
            console.print("[dim]Re-run `sc-referee init` to re-propose the design against the current manifest.[/]")
            raise typer.Exit(code=2)
        # Confirm the DESIGN first, then bind + confirm the manifest — so a design failure leaves
        # nothing confirmed (and a half state fails safe: the audit gate requires BOTH to block).
        try:
            confirm_config(config)                       # refuses if the design has unresolved roles
        except ValueError as e:
            console.print(f"[bold red]cannot confirm[/] {e}")
            raise typer.Exit(code=2)
        manifest = load_manifest(manifest_path)
        record_hashes(manifest, folder, verified_hashes=bundle.manifest_hashes)
        manifest.confirmed_by_human = True
        write_manifest(manifest, manifest_path)
        console.print(f"[green]confirmed[/] {manifest_path.name} — {len(manifest.shards)} shards "
                      f"assembled, content + files hashed.")
        console.print(f"[green]confirmed[/] {config.name} — deterministic checks may now render a verdict.")
        return

    try:
        confirm_config(config)
    except ValueError as e:
        console.print(f"[bold red]cannot confirm[/] {e}")
        raise typer.Exit(code=2)
    console.print(f"[green]confirmed[/] {config.name} — deterministic checks may now render a verdict.")


_STATUS_STYLE = {"blocker": "bold red", "major": "yellow", "needs_evidence": "cyan",
                 "informational": "magenta", "not_audited": "dim", "pass": "green"}


@app.command()
def fix(
    folder: Path = typer.Argument(..., help="Analysis folder (same one you audited)."),
    design: Optional[Path] = typer.Option(None, "--design", help="Confirmed sc-referee.yaml (defaults to <folder>/sc-referee.yaml)."),
    engine: str = typer.Option("pydeseq2", "--engine", help="Recompute engine: pydeseq2 or simple."),
    check: Optional[str] = typer.Option(None, "--check", help="Only fix this check (default: every flagged check)."),
    out: Optional[Path] = typer.Option(None, "--out", help="Where to write the runnable pseudobulk template (defaults to <folder>/corrected_reanalysis_template.py)."),
):
    """Emit a corrected-reanalysis for each flagged check — the actionable other half of the verdict.

    For pseudoreplication it writes a RUNNABLE pseudobulk script; for the others, the exact edit to
    apply. Templates are generated from your confirmed design, never from an LLM.
    """
    from sc_referee.config import load_designs
    from sc_referee.design import DesignError
    from sc_referee.ingest import IngestError

    from sc_referee.fixes import fix_for

    design_path = design or folder / "sc-referee.yaml"
    try:
        result = run_audit(folder, design_path, engine=engine)
        designs = load_designs(design_path)
    except IngestError as e:
        console.print(f"[bold red]cannot audit[/] {e}")
        raise typer.Exit(code=2)
    except DesignError as e:
        console.print(f"[bold red]config error[/] in the ratified design: {e}")
        raise typer.Exit(code=2)
    dsn = designs[0]   # one contrast today; multi-contrast fixes land with the multi-contrast path

    findings = [f for f in result.findings if (f.check_id == check if check else True)]
    fixes = [(f, fix_for(f, dsn)) for f in findings]
    fixes = [(f, text) for f, text in fixes if text]
    if not fixes:
        console.print("[green]Nothing to fix[/] — no flagged finding has an available correction.")
        raise typer.Exit(code=0)

    for f, text in fixes:
        console.print(f"\n[bold]{f.check_id}[/]  [{_STATUS_STYLE.get(f.status, 'white')}]{f.status}[/]")
        console.print(text)

    runnable = next((text for f, text in fixes if f.check_id == "experimental_unit"), None)
    if runnable:
        out_path = out or folder / "corrected_reanalysis_template.py"
        out_path.write_text(runnable)
        console.print(f"\n[dim]wrote runnable pseudobulk template →[/] {out_path}")


@app.command()
def bundle(
    path: Path = typer.Argument(..., help="A multi-step analysis export — a folder or a .zip (e.g. a Claude Science bundle)."),
):
    """Inventory a multi-step analysis export — PARSE it, never run it — and say honestly what can be audited.

    Real workflows are a chain of steps and a report full of claims, not one clean result. This lists the
    pipeline steps (their methods, declared inputs, and conversation lineage), the data, and the report's
    numeric claims — then computes a coverage verdict. If no step runs an analysis sc-referee checks, it
    says NOT_AUDITED rather than letting a green run read as 'clean'.
    """
    from sc_referee.bundle_recompute import bundle_recompute
    from sc_referee.science_bundle import attribute_claims, bundle_findings, coverage_verdict, inventory_bundle

    if not path.exists():
        console.print(f"[bold red]no such path[/] {path}")
        raise typer.Exit(code=2)
    inv = inventory_bundle(path)
    n_claims = sum(len(r.claims) for r in inv.reports)
    console.print(f"[bold]BUNDLE[/] {inv.root} — {len(inv.steps)} steps · {len(inv.data)} data files · "
                  f"{len(inv.reports)} report(s) · {n_claims} numeric claims\n")

    for s in inv.steps:
        methods = ", ".join(f"[cyan]{g}[/]:{'/'.join(v)}" for g, v in s.calls.items()) or "[dim]no recognized analysis call[/]"
        pos = f"[bold]{s.order}[/]" if s.order is not None else "[dim]·[/]"
        lin = f"  [dim]lineage {s.lineage}[/]" if s.lineage else ""
        console.print(f"  {pos} {s.name}{lin}")
        console.print(f"     {methods}")
        if s.declared_inputs:
            console.print(f"     [dim]inputs: {', '.join(s.declared_inputs)}[/]")

    cov = coverage_verdict(inv)
    findings = bundle_findings(inv)
    style = "green" if cov.status == "auditable" else "bold yellow"
    console.print(f"\n[{style}]{cov.status.upper()}[/] — {cov.reason}")
    # a real structural finding supersedes the coarse "double_dipping applies" coverage note
    for note in cov.notes:
        if "double_dipping" in note and findings:
            continue
        console.print(f"  [yellow]note:[/] {note}")

    if findings:
        console.print("\n[bold]structural checks[/]")
        for f in findings:
            st = _STATUS_STYLE.get(f.status, "white")
            where = " + ".join(dict.fromkeys((f.metrics.get("cluster_steps") or [])
                                             + (f.metrics.get("marker_steps") or [])))
            loc = f"  [dim]{where}[/]" if where else ""
            console.print(f"  [{st}]{f.status}[/]  [bold]{f.check_id}[/]{loc}")
            console.print(f"     {f.verdict}")
        if any(f.status == "needs_evidence" for f in findings):
            console.print("     [dim]to render a blocking verdict, confirm that contrast: "
                          "init → confirm → audit on the offending step's data.[/]")

    recompute = bundle_recompute(inv, path)
    if recompute is not None:
        st = _STATUS_STYLE.get(recompute.status, "white")
        console.print("\n[bold]recompute[/] [dim](our analysis on their data — never their code)[/]")
        console.print(f"  [{st}]{recompute.status}[/]  [bold]{recompute.check_id}[/]")
        console.print(f"     {recompute.verdict}")

    claims = attribute_claims(inv)
    flagged_claims = [a for a in claims if a.status == "needs_evidence"]
    if flagged_claims:
        console.print("\n[bold]claims resting on a flagged test[/] [dim](method, not the number)[/]")
        for a in flagged_claims:
            console.print(f"  [cyan]needs_evidence[/]  “{a.claim}”")
            console.print(f"     [dim]← produced by a de-novo-cluster marker test (groupby={a.grouping}); "
                          f"its p-values are not valid for post-clustering inference. The reported number "
                          f"itself is not verified — only its method.[/]")
    if n_claims:
        unresolved = sum(1 for a in claims if a.status == "unresolved")
        console.print(f"\n[dim]{n_claims} numeric claim(s) parsed; {len(flagged_claims)} attributed to a "
                      f"flagged test, {unresolved} marker-claim(s) could not be uniquely attributed. Claim "
                      f"recomputation is not wired — we certify method/data-flow validity, not the number.[/]")


if __name__ == "__main__":
    app()
