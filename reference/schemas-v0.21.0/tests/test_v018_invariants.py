from test_examples import errors, invalid, load

def test_deterministic_observation_example_validates():
 assert not errors(load("deterministic-check-observation.example.json"), "deterministic_check_observation")

def test_applicable_observation_cannot_report_unknown():
 x=load("deterministic-check-observation.example.json")
 x["comparison"]["outcome"]="unknown"
 invalid(x,"deterministic_check_observation")

def test_observation_cannot_grant_finding_authority():
 x=load("deterministic-check-observation.example.json")
 x["production_finding_permitted"]=True
 invalid(x,"deterministic_check_observation")

def test_operand_arrays_are_bounded():
 x=load("deterministic-check-observation.example.json")
 x["operands"][0]={"name":"values","kind":"string_array","value":["x"]*10001}
 invalid(x,"deterministic_check_observation")
