from sc_referee.csp import CspFieldState
from sc_referee.wizard import answers_to_config, csp_questions, render_form
from tests.factories import pseudobulk_confounding_bundle
from tests.test_wizard_random_intercept_ledger import _answers, _proposal
from tests.test_init_csp import target_proposal
from sc_referee.csp_contracts.target_population_estimand_v1 import (
    MANIFEST as TARGET_MANIFEST,
    REQUIRED_FIELDS as TARGET_FIELDS,
)


def test_target_questions_cover_fields_and_default_not_sure():
    questions = csp_questions(_proposal(), proposal=target_proposal())
    semantic = [q for q in questions if q.kind == "csp_semantic"]
    assert [q.role.rsplit(".", 1)[-1] for q in semantic] == list(TARGET_FIELDS)
    assert all(q.default == "not_sure" and "not_sure" in q.options for q in questions)


def test_target_teach_back_is_specific_and_comprehensible():
    questions = csp_questions(_proposal(), proposal=target_proposal())
    copy = " ".join(q.prompt + " " + q.why for q in questions).lower()
    assert "california registry" in copy
    assert "age_band" in copy and "sex" in copy
    assert "registry's counts" in copy and "rather than the proportions" in copy
    assert "these donors" in copy
    assert "q_s" not in copy and "formula" not in copy
    assert "confirm all" not in render_form(questions).lower()


def test_bare_population_choice_is_non_authorizing_copy():
    q = next(q for q in csp_questions(_proposal(), proposal=target_proposal())
             if q.role.endswith(".functional"))
    assert q.options == (
        "not_sure", "population_average_exact_census", "across_population")


def target_answers():
    prefix = "csp.target_population."
    return {prefix + field: TARGET_MANIFEST.teach_back_ids[field]
            for field in TARGET_FIELDS} | {
        prefix + "authority_attested": "yes",
        prefix + "consequence_acknowledged": "yes",
    }


def target_config(overrides=None, proposal=None):
    proposed = _proposal()
    proposed["csp_proposals"] = [proposal or target_proposal()]
    answers = _answers() | target_answers() | (overrides or {})
    return answers_to_config(
        answers, pseudobulk_confounding_bundle().observations.assign(
            age_band=["18-39"] * 8, sex=["F", "M"] * 4),
        proposed_config=proposed,
    )


def test_complete_target_ceremony_confirms_every_field_independently():
    contract = target_config()["contrasts"][0]["csp_contracts"][0]
    assert contract["authorized_consumers"] == ["target_population"]
    assert tuple(contract["fields"]) == TARGET_FIELDS
    assert all(field["state"] == "confirmed_high" for field in contract["fields"].values())
    assert len({field["confirmation_event_id"] for field in contract["fields"].values()}) \
        == len(TARGET_FIELDS)


@__import__("pytest").mark.parametrize("field_id", TARGET_FIELDS)
def test_target_not_sure_on_any_field_is_non_authorizing(field_id):
    key = f"csp.target_population.{field_id}"
    field = target_config({key: "not_sure"})["contrasts"][0]["csp_contracts"][0] \
        ["fields"][field_id]
    assert (field["state"], field["value"], field["confidence"]) == \
        ("unresolved", None, "low")


def test_broad_across_population_cannot_mint_functional():
    field = target_config({"csp.target_population.functional": "across_population"}) \
        ["contrasts"][0]["csp_contracts"][0]["fields"]["functional"]
    assert (field["state"], field["value"], field["confidence"]) == \
        ("declined_for_consumer", None, "low")


@__import__("pytest").mark.parametrize("missing", ["evidence", "authority", "consequence"])
def test_missing_target_ceremony_never_confirms_high(missing):
    proposal = target_proposal()
    overrides = {}
    if missing == "evidence":
        proposal["evidence_locations"] = []
    else:
        overrides[f"csp.target_population.{missing}_attested" if missing == "authority"
                  else "csp.target_population.consequence_acknowledged"] = "not_sure"
    fields = target_config(overrides, proposal)["contrasts"][0]["csp_contracts"][0] \
        ["fields"].values()
    assert all(field["state"] != "confirmed_high" and field["confidence"] == "low"
               for field in fields)


@__import__("pytest").mark.parametrize("defect", [
    "missing_strata", "unreconciled_census", "wrong_functional", "wrong_policy",
])
def test_inconsistent_target_candidate_never_authorizes(defect):
    proposal = target_proposal()
    if defect == "missing_strata":
        proposal["stratum_levels"] = []
    elif defect == "unreconciled_census":
        proposal["census_stratum_counts"] = [300, 199]
    elif defect == "wrong_functional":
        proposal["functional_candidate"] = "sample_average"
    else:
        proposal["support_policy_candidate"] = "allow_extrapolation"
    config = target_config(proposal=proposal)
    assert not config["contrasts"][0].get("csp_contracts")
    assert "csp_proposals" in config["unresolved"]


def _proposal_with_csp():
    proposal = _proposal()
    proposal["csp_proposals"] = [{
        "contract_type": "between_group_adjustment_obligation/v1",
        "group_source_column": "run",
        "evidence_locations": ["analysis.R:42"],
    }]
    return proposal


def test_between_group_questions_are_in_domain_unselected_and_abstention_default():
    questions = csp_questions(_proposal_with_csp(), group_source_column="run")
    assert [q.role for q in questions if q.kind == "csp_semantic"] == [
        "csp.run.between_group_policy",
        "csp.run.may_rely_on_re_exogeneity",
    ]
    for q in questions:
        assert q.default in (None, "not_sure")
    html = render_form(questions)
    assert "Not sure — leave this check not checked" in html
    assert "Hausman" not in html and "E[b_g|X_g]" not in html
    assert "run" in html.lower()
    assert "confirm all" not in html.lower()


def _config(**csp_answers):
    answers = _answers() | {
        "csp.run.between_group_policy": "remove_arbitrary",
        "csp.run.may_rely_on_re_exogeneity": "must_not_rely",
        "csp.run.authority_attested": "yes",
        "csp.run.consequence_acknowledged": "yes",
        **csp_answers,
    }
    return answers_to_config(
        answers, pseudobulk_confounding_bundle().observations,
        proposed_config=_proposal_with_csp(),
    )


def test_not_sure_is_stored_unresolved_and_never_high_confidence():
    config = _config(**{"csp.run.may_rely_on_re_exogeneity": "not_sure"})
    field = config["contrasts"][0]["csp_contracts"][0]["fields"][
        "may_rely_on_re_exogeneity"
    ]
    assert field["state"] == CspFieldState.UNRESOLVED.value
    assert field["value"] is None
    assert field["confidence"] == "low"


def test_wrong_teach_back_cannot_ratify_even_after_q1_affirmative():
    config = _config(**{"csp.run.may_rely_on_re_exogeneity": "may_rely"})
    field = config["contrasts"][0]["csp_contracts"][0]["fields"][
        "may_rely_on_re_exogeneity"
    ]
    assert field["value"] is True
    assert field["state"] == CspFieldState.DECLINED_FOR_CONSUMER.value
    assert field["confidence"] == "low"
    assert "ratification" not in config["contrasts"][0]["csp_contracts"][0]


def test_each_field_has_its_own_confirmation_metadata():
    config = _config()
    fields = config["contrasts"][0]["csp_contracts"][0]["fields"]
    assert all(field["state"] == "confirmed_high" for field in fields.values())
    assert fields["between_group_policy"]["confirmation_event_id"] != (
        fields["may_rely_on_re_exogeneity"]["confirmation_event_id"]
    )
    assert all(field["actor"] and field["confirmed_at"] for field in fields.values())


def test_missing_ceremony_or_evidence_never_confirms_high():
    for missing in ("csp.run.authority_attested", "csp.run.consequence_acknowledged"):
        answers = _answers() | {
            "csp.run.between_group_policy": "remove_arbitrary",
            "csp.run.may_rely_on_re_exogeneity": "must_not_rely",
            "csp.run.authority_attested": "yes",
            "csp.run.consequence_acknowledged": "yes",
        }
        del answers[missing]
        config = answers_to_config(
            answers, pseudobulk_confounding_bundle().observations,
            proposed_config=_proposal_with_csp(),
        )
        assert any(field["state"] != "confirmed_high" for field in
                   config["contrasts"][0]["csp_contracts"][0]["fields"].values())
    no_evidence = _proposal()
    no_evidence["csp_proposals"] = [{
        "contract_type": "between_group_adjustment_obligation/v1",
        "group_source_column": "run", "evidence_locations": [],
    }]
    answers = _answers() | {
        "csp.run.between_group_policy": "remove_arbitrary",
        "csp.run.may_rely_on_re_exogeneity": "must_not_rely",
        "csp.run.authority_attested": "yes", "csp.run.consequence_acknowledged": "yes",
    }
    config = answers_to_config(answers, pseudobulk_confounding_bundle().observations,
                               proposed_config=no_evidence)
    assert all(field["confidence"] == "low" for field in
               config["contrasts"][0]["csp_contracts"][0]["fields"].values())


def test_copy_discloses_consequence_and_realizable_self_attestation():
    questions = csp_questions(_proposal_with_csp(), group_source_column="run")
    text = " ".join(q.prompt + " " + q.why for q in questions)
    assert "confirmation may allow confounding_random_intercept_conditional to flag this result" in text.lower()
    assert "I am responsible for this result's scientific interpretation" in text
    assert "role" not in text.lower() and "authorized" not in text.lower()


def test_exact_fixed_effect_semantics_and_sensitivity_escape_is_non_authorizing():
    questions = csp_questions(_proposal_with_csp(), group_source_column="run")
    teach = next(q for q in questions if q.role.endswith("may_rely_on_re_exogeneity"))
    copy = (teach.prompt + " " + teach.why).lower()
    assert "exact fixed-effect-equivalent projection" in copy
    assert "random intercept never" in copy and "no matter how close" in copy
    assert "tolerance-level" in copy and "not" in copy
    assert "sensitivity_at_tolerance_is_sufficient" in teach.options

    config = _config(**{
        "csp.run.may_rely_on_re_exogeneity":
            "sensitivity_at_tolerance_is_sufficient"
    })
    field = config["contrasts"][0]["csp_contracts"][0]["fields"][
        "may_rely_on_re_exogeneity"
    ]
    assert field["state"] == CspFieldState.DECLINED_FOR_CONSUMER.value
    assert field["confidence"] == "low"


def test_sensitivity_at_tolerance_escape_routes_stage1_not_checked(tmp_path):
    import yaml

    from sc_referee import statuses as S
    from sc_referee.checks.confounding_random_intercept import (
        ConfoundingRandomInterceptCheck,
    )
    from sc_referee.config import load_designs

    config = _config(**{
        "csp.run.may_rely_on_re_exogeneity":
            "sensitivity_at_tolerance_is_sufficient"
    })
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(config))
    (design,) = load_designs(path)
    finding = ConfoundingRandomInterceptCheck().run(
        design, pseudobulk_confounding_bundle()
    )
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )
