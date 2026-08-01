from test_examples import errors, invalid, load

def test_second_static_profile_and_proof_examples_validate():
 assert not errors(load("static-qualification-profile.analysis-method.example.json"), "static_qualification_profile")
 assert not errors(load("static-qualification-proof.analysis-method.example.json"), "static_qualification_proof")

def test_static_profile_cannot_mix_detector_and_verifier():
 x=load("static-qualification-profile.analysis-method.example.json")
 x["verifier"]["entry_point"]="sc_referee_evaluation.static_qualification:verify_bounded_direction_case"
 invalid(x,"static_qualification_profile")

def test_static_proof_cannot_mix_profile_and_fact_shape():
 x=load("static-qualification-proof.analysis-method.example.json")
 x["proof_profile_kind"]="bounded_report_mean_direction_v1"
 invalid(x,"static_qualification_proof")

def test_method_fixture_requires_review_authority_collections():
 x=load("benchmark-fixture.static-method-good.example.json")
 del x["proof_evidence"]["public_inputs"]["answers"]
 invalid(x,"benchmark_fixture")
