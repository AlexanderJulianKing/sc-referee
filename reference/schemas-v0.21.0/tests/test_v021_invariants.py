from copy import deepcopy

from test_examples import errors, invalid, load


def test_code_csv_qualification_identity_is_accepted():
 qualification=load("detector-qualification.code-csv-dependence.example.json")
 metric=load("qualification-metric-set.code-csv-dependence.example.json")
 assert qualification["detector_id"]=="detector:bounded-code-csv-dependence-conflict"
 assert qualification["detector_version"]=="3.1.0"
 assert metric["binding_scope"]==qualification["binding_scope"]
 assert not errors(qualification,"detector_qualification")
 assert not errors(metric,"qualification_metric_set")


def test_detector_identity_versions_cannot_cross():
 for name,record_type in (
  ("detector-qualification.code-csv-dependence.example.json","detector_qualification"),
  ("qualification-metric-set.code-csv-dependence.example.json","qualification_metric_set"),
 ):
  value=load(name)
  for target in (value,value["binding_scope"]):
   wrong=deepcopy(value)
   selected=wrong if target is value else wrong["binding_scope"]
   selected["detector_version"]="9.9.9"
   invalid(wrong,record_type)


def test_old_generic_identity_remains_accepted():
 qualification=load("detector-qualification.code-csv-dependence.example.json")
 metric=load("qualification-metric-set.code-csv-dependence.example.json")
 for value in (qualification,metric):
  value["detector_id"]="detector:bounded-analysis-method-conflict"
  value["detector_version"]="0.3.0"
  value["binding_scope"]["detector_id"]="detector:bounded-analysis-method-conflict"
  value["binding_scope"]["detector_version"]="0.3.0"
 assert qualification["detector_id"]=="detector:bounded-analysis-method-conflict"
 assert qualification["detector_version"]=="0.3.0"
 assert not errors(qualification,"detector_qualification")
 assert not errors(metric,"qualification_metric_set")


def test_historical_code_identity_remains_accepted():
 qualification=load("detector-qualification.code-csv-dependence.example.json")
 metric=load("qualification-metric-set.code-csv-dependence.example.json")
 for value in (qualification,metric):
  value["detector_version"]="2.1.0"
  value["binding_scope"]["detector_version"]="2.1.0"
 assert not errors(qualification,"detector_qualification")
 assert not errors(metric,"qualification_metric_set")


def test_reportless_finding_materiality_is_accepted_without_claiming_selection():
 finding=load("finding.example.json")
 finding["publication_materiality"]={
  "state":"unassessed",
  "reason":"no_selected_publication_surface",
  "rationale":"The reportless lane establishes no selected publication surface.",
  "candidate_publication_surface_ids":[],
 }
 assert not errors(finding,"finding")
