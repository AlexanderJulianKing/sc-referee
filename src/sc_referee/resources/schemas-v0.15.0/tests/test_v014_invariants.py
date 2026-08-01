from test_examples import invalid, load
from copy import deepcopy
def test_project_work_item_is_closed_non_authority():
 x=load("work-item.project-execution.example.json"); x["packet"]["policy"]["launch_authorized"]=True; invalid(x,"work_item")
def test_project_packet_has_no_prompt_identity():
 x=load("work-item.project-execution.example.json"); x["packet"]["prompt_template_id"]="prompt:invented"; invalid(x,"work_item")
def test_semantic_packet_cannot_be_project_request():
 x=load("work-item.ready.example.json"); y=load("work-item.project-execution.example.json"); x["packet"]=deepcopy(y["packet"]); invalid(x,"work_item")
def test_complete_authorization_requires_work_item_digest():
 x=load("project-execution-authorization.example.json"); x["scope"]["work_item_semantic_digest"]=None; invalid(x,"project_execution_authorization")
