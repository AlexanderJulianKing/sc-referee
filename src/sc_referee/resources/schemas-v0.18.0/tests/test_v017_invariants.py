from test_examples import errors, invalid, load

def test_typed_method_profile_and_proof_examples_validate():
 assert not errors(load("static-qualification-profile.analysis-method.example.json"), "static_qualification_profile")
 assert not errors(load("static-qualification-proof.analysis-method.example.json"), "static_qualification_proof")

def test_typed_method_profile_cannot_reuse_production_adapter_identity():
 x=load("static-qualification-profile.analysis-method.example.json")
 x["method_binding"]["qualification_adapter"]["adapter_id"]="adapter:production"
 invalid(x,"static_qualification_profile")

def test_typed_method_proof_rejects_relation_kind_mixing():
 x=load("static-qualification-proof.analysis-method.example.json")
 x["derived_facts"]["comparison_form"]="set_relation"
 invalid(x,"static_qualification_proof")

def test_typed_method_profile_and_proof_allow_one_report_plane():
 p=load("static-qualification-profile.analysis-method.example.json")
 p["method_binding"]["required_evidence_planes"]=["reported_text"]
 p["method_binding"]["required_assertion_roles"]=["reported"]
 assert not errors(p,"static_qualification_profile")
 x=load("static-qualification-proof.analysis-method.example.json")
 x["derived_facts"]["observations"]=x["derived_facts"]["observations"][:1]
 x["derived_facts"]["candidate_paths"]=["report.md"]
 assert not errors(x,"static_qualification_proof")
