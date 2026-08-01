from __future__ import annotations
from test_examples import invalid, load
import copy,json
from pathlib import Path
from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from referencing import Registry,Resource

ROOT=Path(__file__).resolve().parents[1]; SD=ROOT/"schemas"/"v0.17.0"; EX=ROOT/"examples"
cat=json.loads((ROOT/"schema-catalog.json").read_text()); reg=Registry(); schemas={}; aliases={}
for item in cat["schemas"]:
 d=json.loads((SD/item["file"]).read_text()); validator_for(d).check_schema(d); reg=reg.with_resource(d["$id"],Resource.from_contents(d)); schemas[d["$id"]]=d; aliases[item["name"]]=d["$id"]
def load(name): return json.loads((EX/name).read_text())
def errors(obj,alias):
 s=schemas[aliases[alias]]; return list(validator_for(s)(s,registry=reg,format_checker=FormatChecker()).iter_errors(obj))
def invalid(obj,alias): assert errors(obj,alias)

def test_complete_fixture_requires_exact_proof_projection():
 x=load("benchmark-fixture.example.json"); x["proof_evidence"]=None; invalid(x,"benchmark_fixture")
def test_complete_fixture_requires_capture_and_packet_sets():
 x=load("benchmark-fixture.example.json"); x["proof_evidence"]["protocol_artifacts"]["review_captures"]=[]; invalid(x,"benchmark_fixture")
 x=load("benchmark-fixture.example.json"); x["proof_evidence"]["protocol_artifacts"]["review_packets"]=[]; invalid(x,"benchmark_fixture")
def test_hard_negative_requires_bound_pattern_and_innocent_evidence():
 x=load("benchmark-fixture.example.json"); x["fixture_kind"]="hard_negative_fixture"; x["proof_obligations"]["hard_negative_pattern_documented"]=True; x["proof_obligations"]["decisive_innocent_explanation_documented"]=True; invalid(x,"benchmark_fixture")
def test_legacy_fixture_cannot_retain_complete_proof():
 x=load("benchmark-fixture.example.json"); x["qualification_proof_status"]="legacy_proof_projection_unavailable"; invalid(x,"benchmark_fixture")
 x["proof_evidence"]=None; assert not errors(x,"benchmark_fixture")
def test_noncomplete_case_is_metric_and_promotion_ineligible():
 x=load("detector-case-outcome.example.json"); x["qualification_proof_status"]="legacy_proof_projection_unavailable"; x["metric_eligible"]=False; assert not errors(x,"detector_case_outcome")
 x["metric_eligible"]=True; invalid(x,"detector_case_outcome")
def test_case_requires_fixture_digest():
 x=load("detector-case-outcome.example.json"); x.pop("fixture_semantic_digest"); invalid(x,"detector_case_outcome")
