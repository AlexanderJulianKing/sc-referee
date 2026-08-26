from __future__ import annotations

import copy

import pytest

from sc_referee.core.ids import semantic_digest
from sc_referee.scientific_requirement_contract import (
    MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
    ScientificRequirementContractError,
    build_scientific_requirement_records,
    resolve_scientific_requirement_profile,
    resolved_scientific_requirement_from_lock_profile,
    scientific_requirement_lock_profile,
)


def _multiple_testing_profile() -> dict[str, object]:
    return {
        "profile_id": "scientific_check_requirement_v1",
        "profile_version": MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
        "check_id": "check:authorized-complete-family-correction-over-code-test-battery",
        "candidate_id": "complete-correction-over-authorized-outcome-family",
        "semantic_role_authority": {
            "authorized_test_family": {
                "material_input_path": "data.csv",
                "group_contrast_column": "group",
                "outcome_columns": ["m1", "m2", "m3"],
                "family_member_rule": "one-two-group-test-per-named-outcome-column",
                "correction_scope": "complete-authorized-family",
            }
        },
    }


def _old_profiles() -> list[dict[str, object]]:
    common: dict[str, object] = {
        "profile_id": "scientific_check_requirement_v1",
        "check_id": "check:founder-orientation-before-hmm-emission",
        "candidate_id": "repair-before-emission",
    }
    return [
        {**common, "profile_version": "1.0.0"},
        {**common, "profile_version": "1.1.0", "semantic_role_authority": {}},
    ]


def _record_kwargs() -> dict[str, object]:
    return {
        "run_id": "audit:test",
        "created_at": "2026-08-24T00:00:00Z",
        "snapshot_digest": "sha256:" + "1" * 64,
        "task_record": {"file_record_id": "file:task", "path": "task.md"},
        "task_source_ref": {
            "record_type": "file_record",
            "record_id": "file:task",
            "path": "task.md",
            "content_digest": "sha256:" + "2" * 64,
        },
        "actor_id": "human:test",
        "files_total": 2,
    }


def _dependence_profile() -> dict[str, object]:
    return {
        "profile_id": "scientific_check_requirement_v1",
        "profile_version": "1.1.0",
        "check_id": "check:authorized-independent-unit-entry-into-row-independent-procedure",
        "candidate_id": "one-analyzed-row-per-authorized-independent-unit",
        "semantic_role_authority": {
            "authorized_independent_unit_key": {
                "material_input_path": "data.csv",
                "column_name": "participant_id",
                "group_contrast_column": "group",
            }
        },
    }


def test_profile_1_2_slims_authority_and_derives_api_and_group_values() -> None:
    resolved = resolve_scientific_requirement_profile(_multiple_testing_profile())

    assert resolved.profile_version == "1.2.0"
    assert resolved.check_version == "2.1.0"
    assert resolved.dimension == "selection_process"
    assert resolved.value == "complete_family_correction_over_authorized_outcome_family"
    family = resolved.semantic_role_authority["authorized_test_family"]  # type: ignore[index]
    assert set(family) == {
        "material_input_path",
        "group_contrast_column",
        "outcome_columns",
        "family_member_rule",
        "correction_scope",
    }
    assert "group_contrast_values" not in family
    assert "registered_test_api" not in family


def test_profile_1_2_snapshot_and_lock_round_trip() -> None:
    resolved = resolve_scientific_requirement_profile(_multiple_testing_profile())
    family = resolved.semantic_role_authority["authorized_test_family"]  # type: ignore[index]
    resolved = resolved.with_authority_binding_snapshot(
        {
            "authorized_test_family": {
                **family,
                "material_input_content_digest": "sha256:" + "a" * 64,
            }
        }
    )
    lock = scientific_requirement_lock_profile(resolved)

    assert resolved_scientific_requirement_from_lock_profile(lock).manifest == resolved.manifest


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"group_contrast_values": ["a", "b"]}, "wrong exact field set"),
        ({"registered_test_api": "scipy.stats.ttest_ind"}, "wrong exact field set"),
        ({"outcome_columns": ["m1", "m2"]}, "outcome columns are invalid"),
        ({"outcome_columns": ["m1", "m1", "m3"]}, "outcome columns are invalid"),
        ({"outcome_columns": ["group", "m2", "m3"]}, "outcome columns are invalid"),
        ({"material_input_path": "../data.csv"}, "material path is invalid"),
        ({"group_contrast_column": "bad header"}, "group/contrast column is invalid"),
        ({"family_member_rule": "anything-else"}, "member rule is invalid"),
        ({"correction_scope": "strict-subset"}, "correction scope is invalid"),
    ],
)
def test_profile_1_2_wrong_exact_authority_shapes_fail_closed(
    mutation: dict[str, object], message: str
) -> None:
    profile = _multiple_testing_profile()
    family = profile["semantic_role_authority"]["authorized_test_family"]  # type: ignore[index]
    family.update(mutation)  # type: ignore[union-attr]

    with pytest.raises(ScientificRequirementContractError, match=message):
        resolve_scientific_requirement_profile(profile)


def test_head_08c0ccb_profile_lock_record_and_answer_bytes_remain_frozen() -> None:
    expected = {
        "1.0.0": {
            "manifest": "sha256:796441627764bcd2c867a521d3de71a9836db330aa8306b99ddd15da72fcdcfc",
            "lock": "sha256:9ab5b0a27afb2a632e5a05f522dd0cff948a79fc590e60b360069351d6f8ea61",
            "records": "sha256:c1ca8cbbdf3a5feb7063c3d02c6f2eb871f2dd0ae3731e770558e1fbf12888e3",
            "answer": "sha256:c193c930f154e2ad094ad133491b94e78c5042462b5b60a0a20f5df202bc21bd",
            "answer_digest": "sha256:2d77a5566e3abf41da629b6217b881044ead904850127b1c8f6dff31875fa260",
        },
        "1.1.0": {
            "manifest": "sha256:d0775b8c9bdd8cdf74dd3f79a98123d5a97925369e7e6cefa93314efbcb45359",
            "lock": "sha256:27af2b509a90f645e7c97bf741ff10a38e5de8194c53103cac8c0a2cba321192",
            "records": "sha256:6195a43caa394dffdb5f537b12147f0689dff152043832c82ad5bf57a60bc2c1",
            "answer": "sha256:004cef5b4439cc76887f7c2d2e57d165b30baab4bb59597094401d3a5b9788d3",
            "answer_digest": "sha256:0a281b35673b6cf08496b169dc9452e74855983fb39ed6c86d29316e448b87b2",
        },
    }
    for profile in _old_profiles():
        version = str(profile["profile_version"])
        resolved = resolve_scientific_requirement_profile(copy.deepcopy(profile))
        lock = scientific_requirement_lock_profile(resolved)
        records = build_scientific_requirement_records(resolved=resolved, **_record_kwargs())  # type: ignore[arg-type]
        answer = records["answers"][0]
        assert semantic_digest(resolved.manifest) == expected[version]["manifest"]
        assert semantic_digest(lock) == expected[version]["lock"]
        assert semantic_digest(records) == expected[version]["records"]
        assert semantic_digest(answer) == expected[version]["answer"]
        assert answer["answer_digest"] == expected[version]["answer_digest"]


def test_parent_commit_real_dependence_1_1_authority_profile_remains_golden() -> None:
    expected = {
        "manifest": "sha256:0d533399e445c987126ddf184032ead8465f2ecdad8d9bcb2d2cbd9918e2cd4d",
        "lock": "sha256:f9166f98a6fad9e2ccb8999d9ea39078b68f14765bf23a0b4658da6c07582332",
        "records": "sha256:920217afb5b9972547032eb160add42e7bdac9342ecbed639f490ca78e528be0",
        "answer": "sha256:72df5784fc92ed789c87754ed8e54ee8f0f52ca955792d1ae1dd0927f69e2dab",
        "answer_digest": "sha256:a317fd5de4d9e280f69af469ad4d6edb56c47b9e7c40b98944ced398424d1d69",
    }
    resolved = resolve_scientific_requirement_profile(_dependence_profile())
    lock = scientific_requirement_lock_profile(resolved)
    records = build_scientific_requirement_records(resolved=resolved, **_record_kwargs())  # type: ignore[arg-type]
    answer = records["answers"][0]

    assert resolved.semantic_role_authority == _dependence_profile()["semantic_role_authority"]
    assert semantic_digest(resolved.manifest) == expected["manifest"]
    assert semantic_digest(lock) == expected["lock"]
    assert semantic_digest(records) == expected["records"]
    assert semantic_digest(answer) == expected["answer"]
    assert answer["answer_digest"] == expected["answer_digest"]


def test_head_08c0ccb_error_strings_remain_exact() -> None:
    wrong_version = _old_profiles()[1]
    wrong_version["profile_version"] = "9.9.9"
    with pytest.raises(ScientificRequirementContractError) as error:
        resolve_scientific_requirement_profile(wrong_version)
    assert str(error.value) == "unsupported scientific requirement profile version"

    wrong_fields = _old_profiles()[1]
    wrong_fields["extra"] = True
    with pytest.raises(ScientificRequirementContractError) as error:
        resolve_scientific_requirement_profile(wrong_fields)
    assert (
        str(error.value) == "scientific requirement profile has the wrong exact versioned field set"
    )

    dependence_authority = _dependence_profile()
    dependence_authority["semantic_role_authority"] = {}
    with pytest.raises(ScientificRequirementContractError) as error:
        resolve_scientific_requirement_profile(dependence_authority)
    assert str(error.value) == ("dependence semantic-role authority has the wrong exact role set")

    empty_authority = _old_profiles()[1]
    empty_authority["semantic_role_authority"] = {"authorized_independent_unit_key": {}}
    with pytest.raises(ScientificRequirementContractError) as error:
        resolve_scientific_requirement_profile(empty_authority)
    assert str(error.value) == (
        "non-dependence scientific requirements require empty semantic-role authority"
    )

    unsafe_path = _dependence_profile()
    unsafe_path["semantic_role_authority"]["authorized_independent_unit_key"][  # type: ignore[index]
        "material_input_path"
    ] = "../data.csv"
    with pytest.raises(ScientificRequirementContractError) as error:
        resolve_scientific_requirement_profile(unsafe_path)
    assert str(error.value) == "authorized independent-unit material path is invalid"

    unsafe_column = _dependence_profile()
    unsafe_column["semantic_role_authority"]["authorized_independent_unit_key"][  # type: ignore[index]
        "column_name"
    ] = "bad header"
    with pytest.raises(ScientificRequirementContractError) as error:
        resolve_scientific_requirement_profile(unsafe_column)
    assert str(error.value) == "authorized independent-unit column name is invalid"

    resolved = resolve_scientific_requirement_profile(_dependence_profile())
    authority = resolved.semantic_role_authority["authorized_independent_unit_key"]  # type: ignore[index]
    drifted = resolved.with_authority_binding_snapshot(
        {
            "authorized_independent_unit_key": {
                **authority,
                "column_name": "different_participant_id",
                "material_input_content_digest": "sha256:" + "a" * 64,
            }
        }
    )
    lock = scientific_requirement_lock_profile(drifted)
    with pytest.raises(ScientificRequirementContractError) as error:
        resolved_scientific_requirement_from_lock_profile(lock)
    assert str(error.value) == "authority binding snapshot drifted"
