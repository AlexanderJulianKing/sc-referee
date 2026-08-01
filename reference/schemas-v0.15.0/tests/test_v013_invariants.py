from test_examples import invalid, load
from copy import deepcopy
def test_authorization_network_is_closed():
 x=load("project-execution-authorization.example.json"); x["network_policy"]="allowed"; invalid(x,"project_execution_authorization")
def test_supported_capability_requires_probe():
 x=load("sandbox-capability.example.json"); x["capability_evidence"]=None; invalid(x,"sandbox_capability")
def test_project_execution_requires_exact_projection():
 x=load("execution.project-workflow.example.json"); x["project_execution"]=None; invalid(x,"execution")
def test_auditor_execution_cannot_claim_project_projection():
 x=load("execution.auditor-verification.example.json"); y=load("execution.project-workflow.example.json"); x["project_execution"]=deepcopy(y["project_execution"]); invalid(x,"execution")
def test_bundle_requires_authorization_collection():
 x=load("audit-bundle.example.json"); x.pop("project_execution_authorizations"); invalid(x,"audit_bundle")
