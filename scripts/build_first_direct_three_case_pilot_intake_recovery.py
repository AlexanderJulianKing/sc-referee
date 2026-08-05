from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_three_case_pilot_authoring import PILOT_AUTHORING_RELATIVE

PARENT_PROTOCOL_DIGEST = "sha256:51808c104df89a701f1b6dd612894207760c02da7c969dcb68df86ae589593af"
FAILED_CLAUDE_CAPTURE_DIGEST = (
    "sha256:c1fa1538979178f23fd24fdad9e9b17c48cdc9a29d71eb20af6e0e6f22a9ae0a"
)
FAILED_CLAUDE_RAW_DIGEST = "sha256:11d85f276ad63d098c66174ba81f2676da4df5e496e267f3ce46c318a391f07b"
CODEX_CAPTURE_DIGEST = "sha256:81c54a0662ca8ab4f7c2ff6e734d214911594cacf68c257c819d888bb061f5fe"
CODEX_RESPONSE_DIGEST = "sha256:0f5bc332d50ee8912ea0fc5952641c8a9de99510f45465fc171a1b5cfccdbe2d"
FROZEN_AT = "2026-08-05T02:05:00Z"
RECOVERY_AMENDMENT_DIGEST = (
    "sha256:3b4ab839a056256f6b93aba1e1f452a0ecb98cb17b93d915acf5b5318d00a06c"
)


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], digest_field: str, expected: str, label: str) -> None:
    supplied = record.pop(digest_field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[digest_field] = supplied


def _capture_digest(path: Path) -> str:
    return sha256_digest(path.read_bytes())


def _assignment(protocol: dict[str, Any], provider: str) -> dict[str, Any]:
    matches = [
        item
        for item in protocol["author_assignments"]
        if item["participant"]["provider"] == provider
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one {provider} author assignment.")
    return cast(dict[str, Any], matches[0])


def build_first_direct_three_case_pilot_intake_recovery(
    project_root: Path,
) -> dict[str, Any]:
    root = project_root / PILOT_AUTHORING_RELATIVE
    protocol = _load(root / "PILOT_AUTHORING_PROTOCOL.json")
    _replay(protocol, "protocol_digest", PARENT_PROTOCOL_DIGEST, "Parent authoring protocol")
    claude_assignment = _assignment(protocol, "Anthropic")
    codex_assignment = _assignment(protocol, "OpenAI")

    failed_path = root / "incoming" / "pilot-author-claude-01.failed.json"
    if _capture_digest(failed_path) != FAILED_CLAUDE_CAPTURE_DIGEST:
        raise ValueError("Retained Claude failure capture has drifted.")
    failed = _load(failed_path)
    if (
        failed.get("call_identity_id") != claude_assignment["call_identity_id"]
        or failed.get("attempt_status") != "invalid_json_retained"
        or failed.get("replacement_count") != 0
        or sha256_digest(str(failed.get("raw_response")).encode("utf-8"))
        != FAILED_CLAUDE_RAW_DIGEST
    ):
        raise ValueError("Retained Claude failure does not match the frozen first attempt.")
    try:
        json.loads(str(failed["raw_response"]))
    except json.JSONDecodeError as error:
        if (error.pos, error.lineno, error.colno) != (3688, 1, 3689):
            raise ValueError("Claude JSON failure location has drifted.") from error
    else:
        raise ValueError("The retained Claude response is no longer a JSON parse failure.")

    codex_path = root / "incoming" / "pilot-author-codex-01.json"
    if _capture_digest(codex_path) != CODEX_CAPTURE_DIGEST:
        raise ValueError("Retained Codex capture has drifted.")
    codex = _load(codex_path)
    response = cast(dict[str, Any], json.loads(str(codex["raw_response"])))
    if semantic_digest(response) != CODEX_RESPONSE_DIGEST:
        raise ValueError("Retained Codex response has drifted.")
    cases = cast(list[dict[str, Any]], response["authored_cases"])
    if len(cases) != 1 or cases[0]["case_id"] != codex_assignment["case_ids"][0]:
        raise ValueError("Retained Codex response is not the frozen single case.")
    declaration = cases[0]["author_declaration"]
    selected = declaration["selected_result_projection"]
    candidates = declaration["candidate_result_spans"]
    if (
        declaration["declaration_state"] != "one_selected_result"
        or selected is None
        or declaration["unsupported_producer_spans"]
        or not candidates
        or any(span != selected["result_span"] for span in candidates)
    ):
        raise ValueError("Codex response is not the exact redundant-locator intake case.")

    transport_requirements = (
        "Transport requirements for this single recovery attempt:\n"
        "- The prior attempt was retained because its response envelope did not parse as JSON. "
        "You are not shown that response and receive no scientific feedback.\n"
        "- Return syntactically valid JSON. Every file content must be one JSON string with all "
        "newlines, backslashes, and embedded quotation marks escaped as JSON requires.\n"
        "- In each Python producer, use only single-quoted Python string literals and do not put "
        "a double-quote character inside the producer content.\n"
        "- When declaration_state is one_selected_result, candidate_result_spans and "
        "unsupported_producer_spans must both be empty arrays.\n"
        "- Check that the complete response parses as one JSON object before returning it.\n\n"
    )
    marker = "Author-visible briefs:\n"
    original_prompt = str(claude_assignment["prompt"])
    if original_prompt.count(marker) != 1:
        raise ValueError("Claude prompt insertion marker is not unique.")
    recovery_prompt = original_prompt.replace(marker, transport_requirements + marker)
    recovery_call_identity = str(
        uuid5(
            NAMESPACE_URL,
            "sc-referee:first-three-case-pilot:claude-transport-recovery:"
            f"{claude_assignment['call_identity_id']}:{FAILED_CLAUDE_RAW_DIGEST}",
        )
    )
    amendment: dict[str, Any] = {
        "artifact_kind": "direct_qualification_pilot_author_intake_recovery_amendment",
        "amendment_version": "1.0.0",
        "parent_protocol_digest": PARENT_PROTOCOL_DIGEST,
        "triggering_attempt": {
            "participant_id": failed["participant_id"],
            "call_identity_id": failed["call_identity_id"],
            "input_capture_digest": FAILED_CLAUDE_CAPTURE_DIGEST,
            "raw_response_digest": FAILED_CLAUDE_RAW_DIGEST,
            "failure_class": "invalid_json_before_schema_or_scientific_admission",
            "json_error": {"position": 3688, "line": 1, "column": 3689},
            "retained_unchanged": True,
        },
        "transport_recovery_assignment": {
            "participant": claude_assignment["participant"],
            "case_ids": claude_assignment["case_ids"],
            "author_visible_brief_digests": claude_assignment["author_visible_brief_digests"],
            "call_identity_id": recovery_call_identity,
            "prompt": recovery_prompt,
            "prompt_digest": sha256_digest(recovery_prompt),
            "output_schema": claude_assignment["output_schema"],
            "output_schema_digest": claude_assignment["output_schema_digest"],
            "interaction_profile": claude_assignment["interaction_profile"],
            "replacement_count": 1,
        },
        "codex_declaration_canonicalization": {
            "participant_id": codex["participant_id"],
            "call_identity_id": codex["call_identity_id"],
            "input_capture_digest": CODEX_CAPTURE_DIGEST,
            "response_digest": CODEX_RESPONSE_DIGEST,
            "applies_only_when": (
                "declaration_state is one_selected_result and every candidate_result_span "
                "exactly equals selected_result_projection.result_span"
            ),
            "canonical_candidate_result_spans": [],
            "distinct_or_conflicting_candidate_span_rejected": True,
            "selected_result_projection_unchanged": True,
            "file_content_unchanged": True,
            "scientific_content_unchanged": True,
        },
        "execution_policy": {
            "additional_attempt_count": 1,
            "transport_recovery_trigger_only": True,
            "same_two_author_visible_briefs": True,
            "prior_response_visible_to_recovery_author": False,
            "scientific_feedback_visible_to_recovery_author": False,
            "further_repair_retry_or_replacement_permitted": False,
            "valid_codex_attempt_reused_unchanged": True,
            "all_attempts_retained": True,
            "heldout_brief_access_permitted": False,
            "excluded_pilot_brief_access_permitted": False,
        },
        "freeze_state": {
            "admitted_case_count": 0,
            "scientific_review_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "scientific_content_selection_criterion_used": False,
        },
        "frozen_at": FROZEN_AT,
        "qualification_authority": "none_author_intake_recovery_only",
    }
    amendment["amendment_digest"] = semantic_digest(amendment)
    if amendment["amendment_digest"] != RECOVERY_AMENDMENT_DIGEST:
        raise ValueError("Author intake recovery amendment digest has drifted.")
    return amendment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    amendment = build_first_direct_three_case_pilot_intake_recovery(project_root)
    destination = (
        project_root / PILOT_AUTHORING_RELATIVE / "AUTHORING_INTAKE_RECOVERY_AMENDMENT.json"
    )
    if destination.exists():
        raise FileExistsError(f"Refusing to replace frozen recovery amendment: {destination}")
    destination.write_text(
        json.dumps(amendment, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(amendment["amendment_digest"])


if __name__ == "__main__":
    main()
