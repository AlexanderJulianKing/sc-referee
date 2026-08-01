from __future__ import annotations
import copy,json
from pathlib import Path
import pytest
from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from referencing import Registry, Resource

ROOT=Path(__file__).resolve().parents[1]; SD=ROOT/"schemas"/"v0.17.0"; EX=ROOT/"examples"
cat=json.loads((ROOT/"schema-catalog.json").read_text()); reg=Registry(); schemas={}; aliases={}
for item in cat["schemas"]:
 d=json.loads((SD/item["file"]).read_text()); validator_for(d).check_schema(d); reg=reg.with_resource(d["$id"],Resource.from_contents(d)); schemas[d["$id"]]=d; aliases[item["name"]]=d["$id"]
def load(name): return json.loads((EX/name).read_text())
def errors(obj,alias):
 s=schemas[aliases[alias]]; return list(validator_for(s)(s,registry=reg,format_checker=FormatChecker()).iter_errors(obj))
def invalid(obj,alias): assert errors(obj,alias)

def test_all_examples_validate():
 for p in EX.glob("*.json"):
  obj=json.loads(p.read_text()); assert not errors(obj,obj["record_type"].replace("-","_")),p.name
def test_finding_cannot_have_unresolved_material_premise():
 x=load("finding.example.json"); x["admission"]["unresolved_material_premise_ids"]=["premise:unknown"]; invalid(x,"finding")
def test_finding_requires_all_admission_booleans_true():
 x=load("finding.example.json"); x["admission"]["direct_entailment"]=False; invalid(x,"finding")
def test_experimental_manifest_cannot_emit_finding():
 x=load("detector-manifest.example.json"); x["maturity"]="experimental"; invalid(x,"detector_manifest")
def test_implicit_inference_cannot_be_finding_eligible():
 x=load("semantic-assertion.example.json"); x["assertion_class"]="implicit_scientific_inference"; invalid(x,"semantic_assertion")
def test_model_finding_eligible_assertion_must_be_explicit_extraction():
 x=load("semantic-assertion.example.json"); x["assertion_class"]="metadata_definition"; invalid(x,"semantic_assertion")
def test_scientist_declaration_requires_human_scientist_answer():
 x=load("semantic-assertion.example.json"); x["assertion_class"]="scientist_declaration"; invalid(x,"semantic_assertion")
def test_complete_claim_has_no_missing_or_opaque_links():
 x=load("claim.lineage-complete.example.json"); x["lineage"]["missing_links"]=["missing input checksum"]; invalid(x,"claim")
def test_negative_result_requires_actual_coverage():
 x=load("detector-result.example.json"); x["state"]="no_issue_detected_within_coverage"; x.pop("candidate"); x["coverage"]["status"]="not_covered"; invalid(x,"detector_result")
def test_coverage_cannot_allow_correctness_conclusion():
 x=load("coverage-record.example.json"); x["interpretation_policy"]["correctness_conclusion_allowed"]=True; invalid(x,"coverage_record")
def test_scientist_disposition_has_no_false_positive_status():
 x=load("scientist-disposition.example.json"); x["status"]="false_positive"; invalid(x,"scientist_disposition")
def test_record_union_references_canonical_files_only():
 u=json.loads((SD/"record-union.schema.json").read_text()); assert "$defs" not in u; assert len(u["oneOf"])==56


def test_standard_plan_has_no_auditor_model_caps():
 x=load("audit-plan.example.json"); assert x["model_policy"]["auditor_call_limit"] is None; assert x["model_policy"]["auditor_input_token_limit"] is None

def test_standard_plan_keeps_project_code_out_of_automatic_levels():
 x=load("audit-plan.example.json"); assert "project_code_execution" not in x["execution_policy"]["automatic_execution_levels"]

def test_standard_plan_forbids_hpc_submission_and_full_workflow():
 x=load("audit-plan.example.json"); assert x["execution_policy"]["allow_hpc_submission"] is False; assert x["execution_policy"]["allow_full_workflow_execution"] is False

def test_standard_plan_deadline_clock_is_user_visible_elapsed():
 x=load("audit-plan.example.json"); assert x["deadlines"]["clock"]=="user_visible_elapsed"; assert x["deadlines"]["hard_deadline_seconds"]==600

def test_quick_plan_may_disable_dependency_installation():
 x=load("audit-plan.example.json"); x["mode"]="quick"; x["deadlines"]["scheduling_cutoff_seconds"]=120; x["deadlines"]["hard_deadline_seconds"]=300; x["execution_policy"]["allow_dependency_installation"]=False; assert not errors(x,"audit_plan")

def test_unresolved_publication_surface_makes_materiality_unassessed():
 x=load("finding.example.json"); x["publication_materiality"]={"state":"unassessed","reason":"unresolved_publication_surface","rationale":"Two candidate manuscripts remain.","candidate_publication_surface_ids":["surface:a","surface:b"]}; assert not errors(x,"finding")

def test_approximate_environment_requires_reason():
 x=load("environment-reconstruction.example.json"); x.pop("approximation_reason"); invalid(x,"environment_reconstruction")

def test_weak_asset_identity_requires_limitation():
 x=load("asset-identity.example.json"); x["tier"]="weak_fingerprint"; x["identity_evidence"]={"kind":"weak_fingerprint","path":"data.bin","size_bytes":10,"sampled_fingerprint":{"algorithm":"sha256","value":"c"*64}}; x["limitations"]=[]; invalid(x,"asset_identity")

def test_unresolved_surface_cannot_enable_publication_materiality():
 x=load("publication-surface.example.json"); x["status"]="unresolved"; x["selection"]={"kind":"unresolved","reason":"Two candidates remain","material_question_id":"question:surface","candidate_surface_refs":[{"record_type":"artifact","record_id":"a"},{"record_type":"artifact","record_id":"b"}]}; x["publication_materiality_assessable"]=True; invalid(x,"publication_surface")



def test_w3id_namespace_is_canonical():
    for schema in schemas.values():
        assert schema["$id"].startswith("https://w3id.org/sc-referee/schema/v0.17.0/")


def test_source_derived_cache_is_project_local():
    x=load("cache-entry.example.json")
    x["cache_scope"]="user_global_tool_asset"
    invalid(x,"cache_entry")


def test_project_execution_requires_rootless_oci_capability():
    x=load("sandbox-capability.example.json")
    x["backend_kind"]="auditor_subprocess"
    invalid(x,"sandbox_capability")


def test_repository_snapshot_never_mixes_live_content():
    x=load("repository-snapshot.example.json")
    x["live_workspace_state"]["mix_live_content_into_run"]=True
    invalid(x,"repository_snapshot")


def test_validated_qualification_needs_agent_adjudication():
    x=load("detector-qualification.example.json")
    x["agent_adjudication_refs"]=[]
    invalid(x,"detector_qualification")


def test_audit_plan_encodes_implementation_foundations():
    x=load("audit-plan.example.json")
    assert x["parser_policy"]["python_stack"]=="cpython_ast_plus_tokenize"
    assert x["storage_policy"]["generated_query_index"]=="sqlite"
    assert x["cache_policy"]["source_derived_scope"]=="project_local_only"
    assert x["sandbox_policy"]["project_code_backend"]=="rootless_oci_required"
    assert x["report_policy"]["renderer"]=="jinja2_static_html"


def test_tool_identity_fixes_public_names():
    x=load("tool-identity.example.json")
    x["import_namespace"]="sciaudit"
    invalid(x,"tool_identity")

def test_cache_policy_forbids_cross_repository_source_reuse():
    x=load("cache-policy.example.json")
    x["cross_repository_source_derived_reuse"]=True
    invalid(x,"cache_policy")

def test_storage_manifest_keeps_sqlite_noncanonical():
    x=load("storage-manifest.example.json")
    x["generated_query_index"]["canonical"]=True
    invalid(x,"storage_manifest")


def test_validated_manifest_requires_qualification_record():
    x=load("detector-manifest.example.json")
    x["validation"]["qualification_record_ref"]=None
    invalid(x,"detector_manifest")

def test_publication_grade_manifest_requires_qualification_record():
    x=load("detector-manifest.example.json")
    x["maturity"]="publication_grade"
    x["validation"]["agent_adjudication_count"]=0
    invalid(x,"detector_manifest")


def test_stage1_agent_review_is_fully_blind():
    x=load("agent-review.example.json")
    x["blindness"]["sc_referee_output_hidden"]=False
    invalid(x,"agent_review")


def test_benchmark_adjudication_cannot_use_majority_vote():
    x=load("benchmark-adjudication.example.json")
    x["majority_vote_permitted"]=True
    invalid(x,"benchmark_adjudication")


def test_material_disagreement_blocks_positive_label():
    x=load("benchmark-adjudication.example.json")
    x["agreement"]["material_disagreement"]=True
    invalid(x,"benchmark_adjudication")


def test_verified_good_fixture_forbids_global_correctness_claim():
    x=load("benchmark-fixture.example.json")
    x["global_correctness_claim_allowed"]=True
    invalid(x,"benchmark_fixture")


def test_capability_matrix_forbids_domain_wide_support_claim():
    x=load("capability-matrix.example.json")
    x["domain_wide_support_claim_allowed"]=True
    invalid(x,"capability_matrix")


def test_ro_crate_export_keeps_native_records():
    x=load("ro-crate-export.example.json")
    x["native_records_included"]=False
    invalid(x,"ro_crate_export")


def test_agent_panel_qualification_discloses_basis():
    x=load("detector-qualification.example.json")
    x["qualification_basis_disclosure"]=""
    invalid(x,"detector_qualification")



def test_stage2_review_requires_falsification_attempt():
    x=load("agent-review.stage2.example.json")
    x.pop("falsification_attempt")
    invalid(x,"agent_review")


def test_eligible_adjudication_requires_falsification_records():
    x=load("benchmark-adjudication.example.json")
    x["deterministic_checks"]["falsification_records_complete"]=False
    invalid(x,"benchmark_adjudication")


def test_adjudication_records_two_runs_per_provider():
    x=load("benchmark-adjudication.example.json")
    x["provider_participation"][0]["stage1_review_count"]=1
    invalid(x,"benchmark_adjudication")


def test_hard_negative_requires_decisive_innocent_explanation_and_execution():
    x=load("benchmark-fixture.example.json")
    x["fixture_kind"]="hard_negative_fixture"
    x["proof_obligations"]["hard_negative_pattern_documented"]=True
    x["proof_obligations"]["decisive_innocent_explanation_documented"]=False
    invalid(x,"benchmark_fixture")


def test_experimental_capability_cannot_claim_finding():
    x=load("capability-matrix.example.json")
    d=x["entries"][0]["detectors"][0]
    d["maturity"]="experimental"; d["qualification_ref"]=None; d["review_basis"]="not_qualified"
    invalid(x,"capability_matrix")


def test_agent_only_qualification_cannot_contain_human_approvals():
    x=load("detector-qualification.example.json")
    x["human_scientific_approvals"]=[{"reviewer":{"actor_kind":"human","actor_id":"person:r","display_name":"Reviewer"},"independent_of_author":True,"domain_expertise":["statistics"]}]
    invalid(x,"detector_qualification")


def test_human_only_panel_cannot_promote_under_agent_required_policy():
    x=load("detector-qualification.example.json")
    x["outcome"]="promoted"; x["effective_maturity"]="validated"
    x["review_basis"]="human_panel"; x["agent_adjudication_refs"]=[]
    x["human_scientific_approvals"]=[{"reviewer":{"actor_kind":"human","actor_id":"person:r","display_name":"Reviewer"},"independent_of_author":True,"domain_expertise":["statistics"]}]
    invalid(x,"detector_qualification")


def test_unavailable_publication_surface_is_valid_explicit_unknown():
 x=load("publication-surface.unavailable.example.json"); assert not errors(x,"publication_surface")

def test_resolved_publication_surface_requires_a_candidate():
 x=load("publication-surface.example.json"); x["candidates"]=[]; invalid(x,"publication_surface")

def test_empty_publication_surface_cannot_enable_materiality():
 x=load("publication-surface.unavailable.example.json"); x["publication_materiality_assessable"]=True; invalid(x,"publication_surface")

def test_empty_coverage_refs_cannot_be_labeled_resolved():
 x=load("coverage-record.example.json"); x["scope"]["publication_surface_refs"]=[]; invalid(x,"coverage_record")

def test_unavailable_coverage_requires_empty_surface_refs():
 x=load("coverage-record.example.json"); x["scope"]["publication_surface_status"]="unavailable"; invalid(x,"coverage_record")
