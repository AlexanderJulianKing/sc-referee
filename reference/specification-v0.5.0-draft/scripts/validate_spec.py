#!/usr/bin/env python3
"""Validate internal consistency and accepted-policy invariants."""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

import yaml

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []
WARNINGS: list[str] = []


def error(msg: str) -> None:
    ERRORS.append(msg)


def warning(msg: str) -> None:
    WARNINGS.append(msg)


def parse_requirements() -> dict[str, dict[str, str]]:
    text = (ROOT / "docs" / "01-product-requirements.md").read_text(encoding="utf-8")
    result: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        m = re.match(r"\*\*(SA-FR-\d{3}) — (.+?) \((P\d(?:/P\d)?)\)\.\*\* (.+)", line)
        if m:
            rid, title, priority, body = m.groups()
        else:
            m = re.match(r"\*\*(SA-NFR-\d{3}) — (.+?)\.\*\* (.+)", line)
            if not m:
                continue
            rid, title, body = m.groups()
            priority = ""
        if rid in result:
            error(f"Duplicate requirement ID {rid}")
        result[rid] = {"title": title, "priority": priority, "requirement_text": body}
    return result


def validate_yaml_json() -> None:
    for path in sorted((ROOT / "machine").glob("*.yaml")):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            error(f"Invalid YAML {path.relative_to(ROOT)}: {exc}")
    for path in sorted((ROOT / "machine").glob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            error(f"Invalid JSON {path.relative_to(ROOT)}: {exc}")
    for path in sorted((ROOT / "examples").glob("*.yaml")):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            error(f"Invalid example YAML {path.relative_to(ROOT)}: {exc}")


def validate_decisions(reqs: dict[str, dict[str, str]]) -> tuple[int, int]:
    data = yaml.safe_load((ROOT / "machine" / "decisions.yaml").read_text(encoding="utf-8"))
    ids = [d["id"] for d in data["decisions"]]
    if len(ids) != len(set(ids)):
        error("Duplicate IDs in machine/decisions.yaml")
    adr_paths = sorted((ROOT / "adrs").glob("ADR-*.md"))
    adr_ids = {re.match(r"(ADR-\d{4})", p.name).group(1) for p in adr_paths}
    if set(ids) != adr_ids:
        error(f"ADR file/register mismatch: register={set(ids)}, files={adr_ids}")
    for decision in data["decisions"]:
        path = ROOT / decision["document"]
        if not path.exists():
            error(f"Missing ADR document {decision['document']}")
            continue
        for rid in re.findall(r"SA-(?:FR|NFR)-\d{3}", path.read_text(encoding="utf-8")):
            if rid not in reqs:
                error(f"{decision['id']} references unknown requirement {rid}")
    return len(ids), len(adr_paths)


def validate_open_decisions() -> int:
    machine = yaml.safe_load((ROOT / "machine" / "open-questions.yaml").read_text(encoding="utf-8"))["open_decisions"]
    mids = [x["id"] for x in machine]
    docids = re.findall(
        r"^### (OD-\d{3}) —",
        (ROOT / "docs" / "12-open-decisions.md").read_text(encoding="utf-8"),
        flags=re.M,
    )
    if len(mids) != len(set(mids)):
        error("Duplicate open-decision IDs")
    if mids != docids:
        error(f"Open-decision register does not match document order: machine={mids}, document={docids}")
    for item in machine:
        for field in ("question", "recommended_working_default", "resolve_by"):
            if not item.get(field):
                error(f"{item['id']} lacks {field}")
    return len(mids)


def validate_traceability(reqs: dict[str, dict[str, str]]) -> int:
    path = ROOT / "machine" / "requirements-traceability.csv"
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ids = [r["requirement_id"] for r in rows]
    if len(ids) != len(set(ids)):
        error("Duplicate requirement rows in traceability CSV")
    if set(ids) != set(reqs):
        error(f"Traceability coverage mismatch; missing={sorted(set(reqs)-set(ids))}, extra={sorted(set(ids)-set(reqs))}")
    for row in rows:
        rid = row["requirement_id"]
        source = reqs.get(rid)
        if source:
            for field in ("title", "priority", "requirement_text"):
                if row[field] != source[field]:
                    error(f"Traceability drift for {rid} field {field}: CSV={row[field]!r}, spec={source[field]!r}")
        target = ROOT / row["primary_spec"]
        if not target.exists():
            error(f"{rid} references missing primary_spec: {row['primary_spec']}")
        for target_text in filter(None, (x.strip() for x in row["supporting_specs"].split("|"))):
            if not (ROOT / target_text).exists():
                error(f"{rid} references missing supporting spec: {target_text}")
        for adr in filter(None, (x.strip() for x in row["architecture_decisions"].split("|"))):
            if not list((ROOT / "adrs").glob(f"{adr}-*.md")):
                error(f"{rid} references missing ADR: {adr}")
    return len(rows)


def validate_markdown_links() -> None:
    paths = (
        list(ROOT.glob("*.md"))
        + list((ROOT / "docs").glob("*.md"))
        + list((ROOT / "adrs").glob("*.md"))
        + list((ROOT / "templates").glob("*.md"))
        + list((ROOT / "examples").glob("*.md"))
        + list((ROOT / "references").glob("*.md"))
    )
    link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for raw in link_re.findall(text):
            dest = raw.strip().split()[0].strip("<>")
            if not dest or dest.startswith(("http://", "https://", "mailto:", "#")):
                continue
            dest = unquote(dest.split("#", 1)[0])
            target = (path.parent / dest).resolve()
            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                warning(f"Link escapes package in {path.relative_to(ROOT)}: {raw}")
                continue
            if not target.exists():
                error(f"Broken link in {path.relative_to(ROOT)}: {raw}")


def validate_master(adr_count: int) -> None:
    required = [
        "MASTER_SPEC.md",
        "MASTER_SPEC.html",
        "sc-referee-specification-v0.5.0.docx",
        "MANIFEST.sha256",
        "ACCEPTANCE_CRITERIA.md",
        "DECISIONS_v0.5.md",
    ]
    for name in required:
        if not (ROOT / name).exists():
            error(f"Missing generated or required artifact {name}; run scripts/build_spec.py")
    master = ROOT / "MASTER_SPEC.md"
    if master.exists():
        text = master.read_text(encoding="utf-8")
        for n in range(14):
            if f"# {n}." not in text:
                error(f"MASTER_SPEC.md lacks module {n}")
        for n in range(1, adr_count + 1):
            if f"## ADR-{n:04d}:" not in text:
                error(f"MASTER_SPEC.md lacks ADR-{n:04d}")
        for heading in (
            "# Contents {#contents}",
            "# Accepted policy decisions for version 0.5 {#accepted-decisions}",
            "# Appendix A. Acceptance criteria {#appendix-a}",
            "# Appendix B. Architecture Decision Records {#appendix-b}",
            "# Appendix C. Reference index {#appendix-c}",
        ):
            if heading not in text:
                error(f"MASTER_SPEC.md lacks {heading}")


def validate_policy_invariants() -> None:
    normative_paths = list((ROOT / "docs").glob("*.md")) + list((ROOT / "examples").glob("*")) + [ROOT / "REVIEW_CHECKLIST.md"]
    joined = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in normative_paths if p.is_file())
    prohibited_phrases = [
        "one bounded novel-concern pass",
        "deeper but finite novel-concern",
        "max_novel_concern_passes",
        "Stage 14 — Novel concern pass",
        "audit_submit_counterevidence",
        "finding-falsifier",
        "Are demonstrated, supported, conditional",
    ]
    for phrase in prohibited_phrases:
        if phrase in joined:
            error(f"Legacy v0.1 policy phrase remains: {phrase}")

    plan_paths = {
        "quick": ROOT / "examples" / "audit-plan.quick.yaml",
        "standard": ROOT / "examples" / "audit-plan.standard.yaml",
        "publication": ROOT / "examples" / "audit-plan.publication.yaml",
    }
    plans = {name: yaml.safe_load(path.read_text(encoding="utf-8")) for name, path in plan_paths.items()}
    plan = plans["standard"]
    expected_deadlines = {"quick": (120, 300), "standard": (480, 600), "publication": (1500, 1800)}
    for name, (cutoff, hard) in expected_deadlines.items():
        deadlines = plans[name].get("deadlines", {})
        if deadlines.get("clock") != "user_visible_elapsed" or deadlines.get("scheduling_cutoff_seconds") != cutoff or deadlines.get("hard_deadline_seconds") != hard:
            error(f"{name.title()} AuditPlan must use the accepted {cutoff}/{hard} user-visible deadline policy")
        model = plans[name].get("model_policy", {})
        if any(model.get(k) is not None for k in ("auditor_call_limit", "auditor_input_token_limit", "auditor_output_token_limit")):
            error(f"{name.title()} AuditPlan must not impose auditor-specific model call or token caps")
        if model.get("allow_open_ended_scientific_issue_search") is not False:
            error(f"{name.title()} AuditPlan must prohibit open-ended model issue search")
    if plans["quick"].get("execution_policy", {}).get("allow_dependency_installation") is not False:
        error("Quick AuditPlan must disable automatic dependency installation")
    for name in ("standard", "publication"):
        execution_policy = plans[name].get("execution_policy", {})
        if execution_policy.get("allow_dependency_installation") is not True or execution_policy.get("dependency_installation_isolation") != "isolated_environment_only":
            error(f"{name.title()} AuditPlan must allow dependency installation only in an isolated environment")
    if plan.get("model_policy", {}).get("allow_open_ended_scientific_issue_search") is not False:
        error("Standard AuditPlan must explicitly prohibit open-ended model issue search")
    if plan.get("finding_policy", {}).get("finding_means_demonstrated_issue_only") is not True:
        error("Standard AuditPlan must reserve Finding for demonstrated issues")
    if plan.get("finding_policy", {}).get("emit_numerical_finding_confidence") is not False:
        error("Standard AuditPlan must disable numerical finding confidence")
    execution = plan.get("execution_policy", {})
    if "project_code_execution" in execution.get("automatic_execution_levels", []):
        error("Project code must not be an automatic execution level")
    if execution.get("allow_dependency_installation") is not True or execution.get("dependency_installation_isolation") != "isolated_environment_only":
        error("Standard AuditPlan must allow only isolated dependency installation")
    if execution.get("allow_full_workflow_execution") is not False or execution.get("allow_hpc_submission") is not False:
        error("Standard AuditPlan must prohibit full-workflow execution and HPC submission")
    network = plan.get("network_policy", {})
    if network.get("claude_network_access") != "host_managed_unrestricted" or network.get("controller_network_access") != "allowed_with_provenance":
        error("Standard AuditPlan network policy is stale")
    if network.get("repository_content_can_authorize") is not False:
        error("Repository content must not authorize network activity")

    report_example = (ROOT / "examples" / "human-report-fragment.md").read_text(encoding="utf-8").lower()
    prohibited_status_patterns = [
        r"(?:^|\n)\s*(?:status:\s*)?analysis passed[.!]?\s*(?:$|\n)",
        r"(?:^|\n)\s*(?:status:\s*)?the analysis is correct[.!]?\s*(?:$|\n)",
        r"(?:^|\n)\s*(?:status:\s*)?publication ready[.!]?\s*(?:$|\n)",
        r"(?:^|\n)\s*(?:status:\s*)?certified valid[.!]?\s*(?:$|\n)",
    ]
    for pattern in prohibited_status_patterns:
        if re.search(pattern, report_example):
            error(f"Human report example contains prohibited positive status wording: {pattern}")

    integration = (ROOT / "docs" / "09-claude-integration.md").read_text(encoding="utf-8")
    if "MUST NOT search the project for unspecified scientific mistakes" not in integration:
        error("Claude integration lacks explicit no-open-ended-review prohibition")

    framework = (ROOT / "docs" / "05-detector-framework.md").read_text(encoding="utf-8")
    required_framework_phrases = [
        "direct entailment",
        "reversing unknown",
        "exact detector applicability",
        "finite counterevidence",
        "bounded wording",
    ]
    for phrase in required_framework_phrases:
        if phrase not in framework.lower():
            error(f"Detector framework lacks Finding-admission concept: {phrase}")
    for phrase in ("partial_open_world", "target estimand", "identification contract", "model-invented causal"):
        if phrase not in framework.lower():
            error(f"Detector framework lacks accepted causal-policy concept: {phrase}")

    foundation_text = "\n".join((ROOT / p).read_text(encoding="utf-8") for p in ["docs/02-system-architecture.md","docs/03-record-model.md","docs/04-audit-lifecycle.md","docs/05-detector-framework.md","docs/07-security-and-trust.md","docs/08-reporting-and-ux.md","docs/09-claude-integration.md"]).lower()
    for phrase in ("sc-referee", "https://w3id.org/sc-referee/schema/", "cpython `ast`", "tree-sitter-r", "jinja2", "rootless oci", "project-local", "workspace_diverged", "cross-provider agent adjudication"):
        if phrase not in foundation_text:
            error(f"Specification lacks accepted foundation concept: {phrase}")
    for plan_name, plan_obj in plans.items():
        if plan_obj.get("storage_policy", {}).get("generated_query_index") != "sqlite":
            error(f"{plan_name.title()} AuditPlan lacks generated SQLite policy")
        if plan_obj.get("parser_policy", {}).get("python_stack") != "cpython_ast_plus_tokenize":
            error(f"{plan_name.title()} AuditPlan lacks accepted Python parser stack")
        if plan_obj.get("cache_policy", {}).get("source_derived_scope") != "project_local_only":
            error(f"{plan_name.title()} AuditPlan lacks source-derived cache locality")
        if plan_obj.get("sandbox_policy", {}).get("project_code_backend") != "rootless_oci_required":
            error(f"{plan_name.title()} AuditPlan lacks rootless OCI project-execution policy")
        if plan_obj.get("report_policy", {}).get("renderer") != "jinja2_static_html":
            error(f"{plan_name.title()} AuditPlan lacks static Jinja2 renderer policy")

    evaluation = (ROOT / "docs" / "10-evaluation-and-validation.md").read_text(encoding="utf-8").lower()
    for phrase in ("claude opus 5", "gpt-5.6 sol", "four stage-1", "two fresh stage-2", "majority vote is never sufficient", "hard_negative_fixture", "ro-crate 1.3", "capability matrix", "agent-only", "falsification record"):
        if phrase not in evaluation:
            error(f"Evaluation specification lacks accepted v0.5 concept: {phrase}")
    if "independent qualified scientific reviewer" in foundation_text:
        error("Superseded mandatory-human detector qualification language remains in current normative modules")

    runtime = (ROOT / "docs" / "06-runtime-and-performance.md").read_text(encoding="utf-8").lower()
    for phrase in ("user-visible elapsed time", "120 seconds", "480 seconds", "1500 seconds", "reproductionrequest", "host-managed"):
        if phrase not in runtime:
            error(f"Runtime specification lacks accepted runtime concept: {phrase}")


def validate_schema_reference() -> None:
    root = ROOT / "references" / "schema-package-v0.5.0"
    required = [
        "schemas/v0.5.0/finding.schema.json",
        "schemas/v0.5.0/conditional-concern.schema.json",
        "schemas/v0.5.0/material-question.schema.json",
        "schemas/v0.5.0/disclosure.schema.json",
        "schemas/v0.5.0/record-union.schema.json",
        "schemas/v0.5.0/audit-plan.schema.json",
        "schemas/v0.5.0/asset-identity.schema.json",
        "schemas/v0.5.0/publication-surface.schema.json",
        "schemas/v0.5.0/external-evidence.schema.json",
        "schemas/v0.5.0/environment-reconstruction.schema.json",
        "schemas/v0.5.0/reproduction-request.schema.json",
        "schemas/v0.5.0/causal-contract.schema.json",
        "schemas/v0.5.0/repository-snapshot.schema.json",
        "schemas/v0.5.0/parser-manifest.schema.json",
        "schemas/v0.5.0/parser-result.schema.json",
        "schemas/v0.5.0/sandbox-capability.schema.json",
        "schemas/v0.5.0/cache-entry.schema.json",
        "schemas/v0.5.0/performance-record.schema.json",
        "schemas/v0.5.0/detector-qualification.schema.json",
        "schemas/v0.5.0/agent-review.schema.json",
        "schemas/v0.5.0/benchmark-adjudication.schema.json",
        "schemas/v0.5.0/benchmark-fixture.schema.json",
        "schemas/v0.5.0/capability-matrix.schema.json",
        "schemas/v0.5.0/ro-crate-export.schema.json",
        "MIGRATION_v0.4_to_v0.5.md",
        "VALIDATION.txt",
    ]
    for rel in required:
        if not (root / rel).exists():
            error(f"Missing schema reference artifact: references/schema-package-v0.5.0/{rel}")
    if (root / "VERSION").exists() and (root / "VERSION").read_text(encoding="utf-8").strip() != "0.5.0":
        error("Referenced schema package version is not 0.5.0")


def validate_audit_plan_examples_against_schema() -> None:
    schema_root = ROOT / "references" / "schema-package-v0.5.0"
    tool = schema_root / "tools" / "validate_records.py"
    plans = [
        ROOT / "examples" / "audit-plan.quick.yaml",
        ROOT / "examples" / "audit-plan.standard.yaml",
        ROOT / "examples" / "audit-plan.publication.yaml",
    ]
    if not tool.exists():
        error("Schema validator is unavailable for AuditPlan example validation")
        return
    proc = subprocess.run(
        [sys.executable, str(tool), "--schema", "audit_plan", *map(str, plans)],
        cwd=schema_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.returncode != 0:
        error("AuditPlan examples fail schema 0.5.0 validation:\n" + proc.stdout)


def validate_document_index() -> None:
    path = ROOT / "machine" / "document-index.json"
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != "0.5.0-draft":
        error(f"Document index has stale version {data.get('version')}")
    expected = {"MASTER_SPEC.md", "MASTER_SPEC.html", "sc-referee-specification-v0.5.0.docx"}
    if set(data.get("generated_review_copies", [])) != expected:
        error("Document index generated_review_copies is incomplete or stale")


def main() -> int:
    reqs = parse_requirements()
    validate_yaml_json()
    adr_count, _ = validate_decisions(reqs)
    open_count = validate_open_decisions()
    trace_count = validate_traceability(reqs)
    validate_markdown_links()
    validate_master(adr_count)
    validate_policy_invariants()
    validate_schema_reference()
    validate_audit_plan_examples_against_schema()
    validate_document_index()

    for msg in WARNINGS:
        print(f"WARNING: {msg}")
    if ERRORS:
        for msg in ERRORS:
            print(f"ERROR: {msg}", file=sys.stderr)
        print(f"Validation failed with {len(ERRORS)} error(s).", file=sys.stderr)
        return 1
    print(
        f"Validated {len(reqs)} requirements, {trace_count} traceability rows, "
        f"{adr_count} ADRs, and {open_count} open decisions."
    )
    print("Accepted epistemic, runtime, implementation-foundation, and v0.5 evaluation invariants are internally consistent.")
    print("Specification validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
