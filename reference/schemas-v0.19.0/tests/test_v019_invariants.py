from copy import deepcopy

from test_examples import errors, invalid, load


def test_maintainer_approval_is_dated_and_decision_bound():
 x=load("detector-qualification.example.json")
 x["software_maintainer_approvals"][0].pop("approved_on")
 invalid(x,"detector_qualification")


def test_flattened_maintainer_actor_is_refused():
 x=load("detector-qualification.example.json")
 x["software_maintainer_approvals"]=[x["software_maintainer_approvals"][0]["actor"]]
 invalid(x,"detector_qualification")


def test_maintainer_decision_ref_is_an_adr_path():
 x=load("detector-qualification.example.json")
 x["software_maintainer_approvals"][0]["decision_ref"]="not-an-adr"
 invalid(x,"detector_qualification")


def test_agent_review_paths_belong_in_evaluation_refs():
 x=load("detector-qualification.example.json")
 assert x["review_basis"]=="agent_panel"
 assert len(x["evaluation_refs"])==2
 x["agent_adjudication_refs"]=[]
 assert not errors(x,"detector_qualification")
 for refs in ([],x["evaluation_refs"][:1]):
  y=deepcopy(x)
  y["evaluation_refs"]=refs
  invalid(y,"detector_qualification")


def test_static_scope_disclosure_states_stage3_artifact_status():
 x=load("detector-qualification.example.json")
 x["qualification_proof_families"]=["static_closed_scope"]
 x["static_scope_disclosure"]={
  "profile_refs":[{"record_type":"static_qualification_profile","record_id":"static-profile:test"}],
  "scope_statement":"One closed static scope.",
  "execution_claimed":False,
  "global_correctness_claimed":False,
  "stage3_comparison_artifact_exists":False,
 }
 assert not errors(x,"detector_qualification")
 x["static_scope_disclosure"].pop("stage3_comparison_artifact_exists")
 invalid(x,"detector_qualification")
