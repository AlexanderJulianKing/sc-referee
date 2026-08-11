from copy import deepcopy
from test_examples import invalid, load

def test_static_fixture_cannot_claim_execution():
 x=load("benchmark-fixture.static-good.example.json"); x["execution_evidence"]="clean_environment_executed"; invalid(x,"benchmark_fixture")

def test_static_hard_negative_requires_decisive_evidence():
 x=load("benchmark-fixture.static-hard.example.json"); x["proof_evidence"]["hard_negative_evidence"]["decisive_innocent_explanation"]=[]; invalid(x,"benchmark_fixture")

def test_static_proof_chronology_has_no_detector_timestamp():
 x=load("static-qualification-proof.example.json"); x["chronology"]["detector_dispatched_at"]="2026-07-30T18:04:00Z"; invalid(x,"static_qualification_proof")

def test_static_profile_is_exactly_bounded_to_first_detector():
 x=load("static-qualification-profile.example.json"); x["target_detector"]["detector_id"]="detector:any"; invalid(x,"static_qualification_profile")
