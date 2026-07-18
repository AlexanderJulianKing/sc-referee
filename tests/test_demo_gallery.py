"""The public demo gallery is explicit about status and keeps every runnable entry healthy."""
import json
from pathlib import Path

import yaml

from sc_referee.audit import run_audit
from sc_referee.ingest import ingest
from sc_referee.report import to_html


ROOT = Path(__file__).parents[1]
GALLERY = ROOT / "demos"


def test_gallery_registry_has_runnable_published_multi_claim_and_gated_cases():
    registry = yaml.safe_load((GALLERY / "registry.yaml").read_text())
    by_id = {demo["id"]: demo for demo in registry["demos"]}

    assert by_id["biermann-pseudoreplication"]["evidence"] == "published_human_data"
    assert by_id["biermann-pseudoreplication-full"]["status"] == "reproducible_full_build"
    assert by_id["biermann-pseudoreplication-full"]["source_data"] == "GSE200218"
    assert (ROOT / by_id["biermann-pseudoreplication-full"]["entrypoint"] / "build_full.py").is_file()
    verified = json.loads(
        (ROOT / by_id["biermann-pseudoreplication-full"]["entrypoint"] / "VERIFIED_RUN.json").read_text()
    )
    assert verified["selected_input"]["shape_cells_by_unique_genes"] == [82783, 35650]
    assert all(verified["compact_capsule_exact_match"].values())
    assert verified["audit"]["patient_level_survivors"] == 770
    assert by_id["multi-claim-pipeline"]["claims"] == [
        "gene_expression", "alternative_splicing", "cluster_abundance",
    ]
    assert by_id["kang-paired-ifnb"]["status"] == "runnable_local_build"
    assert by_id["kang-paired-ifnb"]["evidence"] == "published_human_data"
    assert (ROOT / by_id["kang-paired-ifnb"]["entrypoint"]).is_dir()
    assert by_id["genebench-gbp07"]["status"] == "gated"
    for demo in by_id.values():
        if demo["status"] == "runnable":
            assert (ROOT / demo["entrypoint"]).is_dir()


def test_three_claim_demo_ingests_and_renders_three_named_analysis_sections():
    folder = GALLERY / "multi-claim-pipeline"
    bundle = ingest(folder)
    assert [claim.name for claim in bundle.reported_claims] == [
        "gene_expression", "alternative_splicing", "cluster_abundance",
    ]

    html = to_html(run_audit(folder, engine="simple"))
    assert html.count('class="analysis"') == 3
    for title in ("Gene expression", "Alternative splicing", "Cluster abundance"):
        assert f'class="a-title">{title}</h2>' in html


def test_cluster_abundance_gets_only_valid_cross_outcome_checks():
    result = run_audit(GALLERY / "multi-claim-pipeline", engine="simple")
    cluster = [
        finding for finding in result.findings
        if getattr(finding, "claim_root", {}).get("claim_id") == "claim:cluster_abundance"
    ]
    check_ids = {finding.check_id for finding in cluster}

    assert {"confounding", "pairing", "multiple_testing", "inference.enrichment_universe"} \
        <= check_ids
    assert not {"count_model", "effect_size", "experimental_unit", "pseudobulk_integrity"} \
        & check_ids


def test_not_applicable_finding_is_rendered_after_clear_findings():
    html = to_html(run_audit(GALLERY / "multi-claim-pipeline", engine="simple"))
    splicing = html.split('class="a-title">Alternative splicing</h2>', 1)[1] \
        .split('class="a-title">Cluster abundance</h2>', 1)[0]

    assert splicing.index("confounding") < splicing.index("count model")
