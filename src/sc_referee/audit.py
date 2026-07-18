"""Audit orchestration — the deterministic half of the loop.

Given a folder (ingested) and a human-confirmed design, run every applicable check and collect
Findings. No LLM here: this is the part that re-runs identically in CI forever.

Three invariants live in this file, not in the checks:
  1. A CONFIG error (a level that does not exist in the data) raises `DesignError` and never
     masquerades as a `blocker`. `blocker` means "your science is wrong", never "your YAML is wrong".
  2. A check that *should* have run but could not (`cannot_evaluate`) emits `not_audited`.
     Silence is the one thing a trust tool may never do.
  3. A crashing check degrades to `needs_evidence` for that check, and never destroys the report
     for the checks that succeeded.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import dataclass, field
import hashlib
from pathlib import Path

import yaml

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.config import load_designs
from sc_referee.design import validate_design_against
from sc_referee.ingest import ingest
from sc_referee.producer_binding import ClaimProducer as _ClaimProducer
from sc_referee.registry import build_checks

COVERAGE_ID = "coverage"


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _target_names(node) -> set[str]:
    """Names whose value is changed by one assignment target (conservative over-approximation)."""
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, (ast.Tuple, ast.List)):
        return set().union(*(_target_names(item) for item in node.elts)) if node.elts else set()
    if isinstance(node, (ast.Subscript, ast.Attribute)):
        base = node.value
        while isinstance(base, (ast.Subscript, ast.Attribute)):
            base = base.value
        return {base.id} if isinstance(base, ast.Name) else set()
    return set()


def _load_names(node) -> set[str]:
    return {item.id for item in ast.walk(node)
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)}


def _generic_report_producers(sources) -> tuple[dict[str, _ClaimProducer], bool]:
    """Bind literal ``DataFrame.to_csv`` egresses to one exact registered sink producer.

    This is deliberately a small, parse-only may-flow. Any parse failure, dynamic CSV path,
    multiple writers, or multiple reaching sinks makes the binding unavailable. It can therefore
    miss a producer, but it cannot select one of several possible producers and accuse the wrong
    claim.
    """
    from sc_referee.sink_use import bind_sinks
    from sc_referee.source_ast import const_str, iter_call_sites, parse_sources, terminal_symbol

    parsed = parse_sources(sources)
    bound = bind_sinks(sources)
    uses = {use.callsite_id: use for use in bound.uses}
    sites = iter_call_sites(parsed)
    producer_by_node = {
        id(site.call): _ClaimProducer(
            site.id, uses[site.id].contract.contract_id, uses[site.id].contract.symbol,
            uses[site.id].contract.sink_kind,
        )
        for site in sites if site.id in uses
    }

    writes: dict[str, list[tuple[int, ast.AST]]] = {}
    uncertain = bool(bound.diagnostics or any(item.tree is None for item in parsed))
    bindings: dict[str, _ClaimProducer] = {}
    for source in parsed:
        if source.tree is None:
            continue
        dependencies: dict[str, set[str]] = {}
        direct: dict[str, set[_ClaimProducer]] = {}
        assignment_counts: dict[str, int] = {}
        multiply_assigned: set[str] = set()
        report_frames: set[str] = set()
        for statement in ast.walk(source.tree):
            targets = []
            value = None
            if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                targets = (list(statement.targets) if isinstance(statement, ast.Assign)
                           else [statement.target])
                value = statement.value
            elif isinstance(statement, ast.AugAssign):
                targets, value = [statement.target], statement.value
            if value is not None:
                names = set().union(*(_target_names(target) for target in targets))
                for name in names:
                    assignment_counts[name] = assignment_counts.get(name, 0) + 1
                    if assignment_counts[name] > 1:
                        multiply_assigned.add(name)

                # Accusation-grade generic binding is limited to an exact DataFrame constructor
                # whose p/q field depends on the sink. A statistic reaching only an unrelated
                # display column is not proof that it produced the reported inferential claim.
                dependency_value = value
                if isinstance(value, ast.Call) and terminal_symbol(value) == "DataFrame":
                    mapping = value.args[0] if value.args else None
                    if isinstance(mapping, ast.Dict):
                        p_fields = {
                            "pvalue", "p_value", "p-value", "pval", "pvals", "padj",
                            "pvals_adj", "qvalue", "qval", "qvals", "fdr", "adj_p",
                            "p_val", "p_val_adj", "adj.p.val", "p.value",
                        }
                        selected = [item for key, item in zip(mapping.keys, mapping.values)
                                    if (const_str(key) or "").strip().lower() in p_fields]
                        if selected:
                            dependency_value = ast.Tuple(elts=selected, ctx=ast.Load())
                            report_frames.update(names)
                rhs_names = _load_names(dependency_value)
                rhs_producers = {producer_by_node[id(call)] for call in ast.walk(dependency_value)
                                 if isinstance(call, ast.Call) and id(call) in producer_by_node}
                for name in names:
                    dependencies.setdefault(name, set()).update(rhs_names)
                    direct.setdefault(name, set()).update(rhs_producers)

            if (isinstance(statement, ast.Call)
                    and isinstance(statement.func, ast.Attribute)
                    and statement.func.attr == "to_csv"):
                path_node = (statement.args[0] if statement.args else
                             next((kw.value for kw in statement.keywords
                                   if kw.arg == "path_or_buf"), None))
                path = const_str(path_node) if path_node is not None else None
                if path is None:
                    uncertain = True
                else:
                    writes.setdefault(path, []).append((source.source_index, statement.func.value))

        resolved = {name: set(values) for name, values in direct.items()}
        for _ in range(len(dependencies) + 1):
            changed = False
            for name, parents in dependencies.items():
                values = set(direct.get(name, ()))
                for parent in parents:
                    values.update(resolved.get(parent, ()))
                if values != resolved.get(name, set()):
                    resolved[name] = values
                    changed = True
            if not changed:
                break

        forward_names = {name for name, values in resolved.items() if values}
        if multiply_assigned & forward_names:
            uncertain = True
        for call in (item for item in ast.walk(source.tree) if isinstance(item, ast.Call)):
            if terminal_symbol(call) in {"DataFrame", "to_csv"} or id(call) in producer_by_node:
                continue
            arguments = [*call.args, *(keyword.value for keyword in call.keywords)]
            if isinstance(call.func, ast.Attribute):
                arguments.append(call.func.value)
            if any(_load_names(argument) & forward_names for argument in arguments):
                # An opaque call could mutate or replace a sink-derived value. Missing the claim is
                # acceptable; certifying a stale producer after possible mutation is not.
                uncertain = True

        for path, path_writes in writes.items():
            local = [receiver for source_index, receiver in path_writes
                     if source_index == source.source_index]
            if len(path_writes) != 1 or len(local) != 1:
                continue
            reached = set()
            receiver = local[0]
            receiver_names = _load_names(receiver)
            if not receiver_names or not receiver_names <= report_frames:
                continue
            reached.update(producer_by_node[id(call)] for call in ast.walk(receiver)
                           if isinstance(call, ast.Call) and id(call) in producer_by_node)
            for name in receiver_names:
                reached.update(resolved.get(name, ()))
            if len(reached) == 1:
                bindings[path] = next(iter(reached))
    # A later source can add a competing writer after an earlier source tentatively bound the path.
    # Re-check uniqueness over the complete source inventory before exposing any binding.
    bindings = {path: producer for path, producer in bindings.items()
                if len(writes.get(path, ())) == 1}
    return ({} if uncertain else bindings), uncertain


def _claim_bindings(bundle, claims, folder: Path) -> dict[str, _ClaimProducer | None]:
    """Resolve each report path to its own producing test, failing closed per claim."""
    sources = tuple((getattr(bundle, "code_signals", {}) or {}).get("sources", ()))
    generic, _ = _generic_report_producers(sources)
    from sc_referee.producer_binding import bind_marker_extraction_report_producers
    marker = bind_marker_extraction_report_producers(sources)
    by_path: dict[str, _ClaimProducer | None] = {
        claim.report_relative_path: marker.get(
            claim.report_relative_path, generic.get(claim.report_relative_path),
        )
        for claim in claims
    }
    return by_path


def _claim_root(claim, producer: _ClaimProducer | None, design, folder: Path) -> dict:
    report_path = folder / claim.report_relative_path
    _, reference, test = design.contrast_column_and_levels()
    root = {
        "claim_id": f"claim:{claim.name or claim.report_relative_path}",
        "report_artifact_digest": _sha256(report_path.read_bytes()),
        "report_locator_digest": _sha256(str(report_path.resolve()).encode()),
        "report_path": claim.report_relative_path,
        "analysis_type": design.analysis_type,
        "test": test,
        "reference": reference,
        "unit_of_test": design.unit_of_test,
        "contrast": design.name,
    }
    if producer is not None:
        root.update(
            producing_value_digest=_sha256(
                f"{producer.contract_id}|{producer.callsite_id}|{claim.report_relative_path}".encode()),
            producer_callsite=producer.callsite_id,
            producer_contract_id=producer.contract_id,
            producing_test=producer.symbol,
        )
    if claim.value_kind is not None:
        root["value_kind"] = claim.value_kind
    return root


def _coverage_gap(check_id: str, claim, producer, *, detail: str | None = None) -> Finding:
    producing = producer.symbol if producer is not None else "an unresolved producing test"
    reason = detail or (
        f"{check_id} did not evaluate {claim.report_relative_path}: its coverage does not reach "
        f"the claim's own producer ({producing}); this claim is NOT CHECKED, not flagged."
    )
    return Finding(check_id, S.NOT_AUDITED, reason, coverage=S.NOT_RUN)


def _claim_scope_override(check, design, claim, producer) -> Finding | None:
    """Return an explicit non-evaluated cell, or ``None`` when normal routing may proceed."""
    if check.id == "count_model" and claim.value_kind == "derived_ratio":
        return Finding(
            check.id, S.PASS,
            "this result comes from a rank test on a value you declared as a computed ratio, not "
            "from a model of raw counts — so the 'was a proper count model used?' check simply "
            "doesn't apply here.",
            applicability=S.NOT_APPLICABLE,
        )
    if check.id == "double_dipping" and design.unit_of_test == "cell" \
            and design.analysis_type in {"condition_contrast_DE", "marker_detection"}:
        # Marker-claim scope is earned only by the short extraction -> local frame -> egress trace.
        # A nearby or generically data-dependent marker-test call is not sufficient.
        covered = producer is not None and producer.marker_family is not None
        if not covered:
            producing = producer.symbol if producer is not None else "unresolved"
            return _coverage_gap(
                check.id, claim, producer,
                detail=(f"double_dipping did not evaluate {claim.report_relative_path}: the claim's "
                        f"own producing test is {producing}, outside this detector's covered "
                        f"marker-test family; coverage is NOT_RUN."),
            )
    return None


@dataclass
class AuditResult:
    findings: list = field(default_factory=list)
    analysis_type: str = None
    confirmed_by_human: bool = False
    engine: str = "pydeseq2"
    folder: str = None
    design_path: str = None
    diagnostics: list = field(default_factory=list)  # EVIDENCE, never gates (§ confounder-candidate)

    def worst_status(self) -> str:
        if not self.findings:
            return S.NOT_AUDITED  # nothing ran -> never claim `pass`
        return max((f.status for f in self.findings), key=lambda s: S.SEVERITY.get(s, 0))

    def ci_fails(self, fail_on=S.FAIL_ON_DEFAULT) -> bool:
        """Only a blocker fails the build (configurable). Everything else is posted, not gated."""
        return any(f.status in fail_on for f in self.findings)

    def ci_conclusion(self, fail_on=S.FAIL_ON_DEFAULT) -> str:
        """fail | neutral | pass.

        `neutral` covers advisory and unaudited findings: they are POSTED, never rendered as a
        clean bill of health. This is what carries "we did not look" honestly, so the exit code
        does not have to lie about it.
        """
        if self.ci_fails(fail_on):
            return "fail"
        advisory = (S.MAJOR, S.NEEDS_EVIDENCE, S.NOT_AUDITED)
        if not self.findings or any(f.status in advisory for f in self.findings):
            return "neutral"
        if not self.confirmed_by_human:
            return "neutral"     # nothing was ratified — a clean `pass` would overclaim
        # `pass` is a POSITIVE claim, so it needs a proof rather than the mere absence of
        # complaints: at least one applicable check that reached complete coverage and conformed.
        # A not-applicable finding spelled `pass` proves nothing about this analysis.
        proved = any(
            finding.status == S.PASS
            and finding.applicability == S.APPLIES
            and finding.coverage == S.COMPLETE
            and finding.judgment in (None, S.CONFORMANT)
            for finding in self.findings
        )
        return "pass" if proved else "neutral"

    def fully_audited(self) -> bool:
        """False when some check that should have run could not. A green CI run on a
        not-fully-audited analysis means "we didn't look", NOT "we looked and it's clean"."""
        return bool(self.findings) and not any(f.status == S.NOT_AUDITED for f in self.findings)


def _clamp_to_entitlement(check, finding: Finding) -> Finding:
    """Enforce the safety invariant: a verifier may not emit a status more CI-severe than its
    declared `max_status`. A `blocker` from a verifier not entitled to one is the worst failure, so
    the spine clamps it down (the safe direction) rather than trusting each check to self-police.
    (design doc §9.3.)"""
    cap = getattr(check, "max_status", S.BLOCKER)
    if S.SEVERITY.get(finding.status, 0) > S.SEVERITY.get(cap, 5):
        finding.status = cap
    return finding


def _safe_run(check, design, bundle, reported) -> Finding:
    """One broken check must not cost the user every other finding; and no check may exceed its
    block entitlement (`max_status`)."""
    try:
        return _clamp_to_entitlement(check, check.run(design, bundle, reported))
    except ModuleNotFoundError as e:
        if not (e.name or "").startswith("pydeseq2"):
            raise
        return Finding(check.id, S.NEEDS_EVIDENCE,
                       f"this check needs an optional dependency that is not installed ({e}). "
                       f"Install `sc-referee[engine]`, or re-run with `--engine simple`.")


def _run_audit_with_inputs(folder, design_path=None, engine: str = "pydeseq2"):
    from dataclasses import replace

    folder = Path(folder)
    design_path = Path(design_path) if design_path else folder / "sc-referee.yaml"
    # Hi-C is the sole parallel-bundle vertical. Peek only at the declared type to select its adapter;
    # every existing type retains the original ingest(folder) -> load_designs(design_path) call order.
    raw_type = None
    if design_path.exists():
        try:
            raw_config = yaml.safe_load(design_path.read_text())
        except (OSError, UnicodeError, yaml.YAMLError):
            # Preserve the legacy path's failure order: ingest first, then let load_designs report
            # the malformed/unreadable config exactly where it did before Hi-C routing existed.
            raw_config = None
        if isinstance(raw_config, dict):
            raw_type = raw_config.get("analysis_type")
    if raw_type == "hic_loop_strength":
        from sc_referee.adapters.hic_contact_adapter import read_hic_contact_folder
        bundle = read_hic_contact_folder(folder)
    else:
        bundle = ingest(folder)
    from sc_referee.inference.live import attach_live_contracts
    reported_claims = tuple(getattr(bundle, "reported_claims", ()) or ())
    # Preserve the singular audit path exactly. Multi-claim audits attach a fresh measured report
    # observation to each scoped bundle below.
    if not reported_claims:
        attach_live_contracts(bundle, folder)
    designs = load_designs(design_path)

    # A multi-file audit may only BLOCK if the manifest is human-confirmed too. Force the design to
    # unconfirmed when the manifest is not — the checks gate on `design.confirmed_by_human`, so this is
    # what actually downgrades their blockers (not merely the report header).
    manifest_path = folder / "sc-referee.manifest.yaml"
    if manifest_path.exists():
        from sc_referee.manifest import load_manifest
        if not load_manifest(manifest_path).confirmed_by_human:
            designs = [replace(d, confirmed_by_human=False) for d in designs]

    checks = build_checks(engine)
    findings: list[Finding] = []
    analysis_type = designs[0].analysis_type if designs else None

    if reported_claims:
        from dataclasses import replace
        from sc_referee.design import DesignError

        producers = _claim_bindings(bundle, reported_claims, folder)
        for claim in reported_claims:
            if claim.contrast is not None:
                matching = [design for design in designs if design.name == claim.contrast]
            else:
                matching = list(designs) if len(designs) == 1 else []
            if len(matching) != 1:
                raise DesignError(
                    f"claim {claim.report_relative_path!r} must bind exactly one contrast; "
                    f"declared {claim.contrast!r}, matched {len(matching)}")
            design = replace(
                matching[0],
                analysis_type=claim.analysis_type or matching[0].analysis_type,
                unit_of_test=(claim.unit_of_test if claim.unit_of_test is not None
                              else matching[0].unit_of_test),
            )
            scoped = copy.copy(bundle)
            scoped.reported_results = claim.reported_results
            scoped.reported_columns = list(claim.reported_columns)
            scoped.provenance = copy.deepcopy(getattr(bundle, "provenance", {}) or {})
            scoped.provenance["reported"] = {
                "path": claim.report_relative_path,
                "reason": "confirmed sc-referee.yaml declared this reported claim",
            }
            producer = producers.get(claim.report_relative_path)
            scoped.code_signals = dict(getattr(bundle, "code_signals", {}) or {})
            # Check-owned method routing sees only this claim's exact producer. Full parsed sources
            # remain available to producer-flow proofs that are explicitly report-path scoped.
            scoped.code_signals["de_calls"] = (
                [(producer.marker_family or producer.symbol).lower()]
                if producer is not None else []
            )
            attach_live_contracts(scoped, folder)
            validate_design_against(scoped.observations, design)
            root = _claim_root(claim, producer, design, folder)
            ran = 0
            for check in checks:
                finding = _claim_scope_override(check, design, claim, producer)
                if finding is None:
                    reason = getattr(check, "cannot_evaluate", lambda d, b: None)(design, scoped)
                    if reason:
                        finding = Finding(check.id, S.NOT_AUDITED, reason)
                    elif check.applies_to(design, scoped):
                        finding = _safe_run(check, design, scoped, claim.reported_results)
                if finding is not None:
                    # Direct metadata is intentionally outside Finding's legacy dataclass field
                    # projection: adding a second claim cannot alter the first claim's finding bytes.
                    finding.claim_root = root
                    findings.append(finding)
                    ran += 1
            if not ran:
                finding = Finding(
                    COVERAGE_ID, S.NOT_AUDITED,
                    f"{design.analysis_type} is recognised, but no methods check is available for it "
                    f"yet — this analysis was NOT audited. A green run does not mean 'checked and clean'.",
                    metrics={"analysis_type": design.analysis_type, "contrast": design.name},
                )
                finding.claim_root = root
                findings.append(finding)
    else:
        for design in designs:
            if design.analysis_type == "hic_loop_strength":
                from sc_referee.adapters.hic_contact_adapter import validate_hic_design_against
                validate_hic_design_against(bundle, design)
            else:
                validate_design_against(bundle.observations, design)  # DesignError -> config error, not a verdict
            ran = 0
            for check in checks:
                reason = getattr(check, "cannot_evaluate", lambda d, b: None)(design, bundle)
                if reason:
                    findings.append(Finding(check.id, S.NOT_AUDITED, reason))
                    ran += 1
                    continue
                if check.applies_to(design, bundle):
                    findings.append(_safe_run(check, design, bundle, bundle.reported_results))
                    ran += 1
            if not ran:
                findings.append(Finding(
                    COVERAGE_ID, S.NOT_AUDITED,
                    f"{design.analysis_type} is recognised, but no methods check is available for it "
                    f"yet — this analysis was NOT audited. A green run does not mean 'checked and clean'.",
                    metrics={"analysis_type": design.analysis_type, "contrast": design.name},
                ))
    # `designs` already reflects the manifest gate (downgraded above), so the checks could not have
    # blocked on an unratified layout.
    confirmed = bool(designs and getattr(designs[0], "confirmed_by_human", False))

    # Confounder-candidate diagnostic: EVIDENCE, never a gate. Wrapped so a diagnostic failure can
    # never cost the user the audit, and always records why it abstained rather than skipping.
    diagnostics = []
    if designs:
        try:
            from sc_referee.inference.audit_hook import run_confounder_diagnostic
            diagnostics.append(run_confounder_diagnostic(bundle, designs[0]))
        except Exception as exc:
            diagnostics.append({"diagnostic": "confounder_candidate", "ran": False,
                                "abstained": f"hook raised and was contained: "
                                             f"{type(exc).__name__}: {exc}"})

    result = AuditResult(
        findings=findings,
        analysis_type=analysis_type,
        confirmed_by_human=confirmed,
        engine=engine,
        folder=str(folder.resolve()),
        design_path=str(design_path.resolve()),
        diagnostics=diagnostics,
    )
    return result, tuple(designs), bundle


def run_audit(folder, design_path=None, engine: str = "pydeseq2") -> AuditResult:
    """Run an audit through the stable result-only API used by existing callers."""
    result, _, _ = _run_audit_with_inputs(folder, design_path, engine)
    return result


def run_audit_with_inputs(folder, design_path=None, engine: str = "pydeseq2"):
    """Run once and retain the exact gated Designs + Bundle consumed by a proof artifact."""
    return _run_audit_with_inputs(folder, design_path, engine)
