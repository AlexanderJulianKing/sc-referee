from __future__ import annotations

import ast
import locale
import os
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee_evaluation.qualification_identity import (
    validate_identity_registry,
    validate_provider_session_identity_evidence,
)
from sc_referee_evaluation.selected_result_qualification_io import (
    QualificationIOError,
    RootedReader,
    RootedTreeRead,
)

if TYPE_CHECKING:
    from sc_referee_evaluation.selected_result_qualification_oracle import (
        ConstructionCertificate,
        SpanCertificate,
    )

BLIND_REVIEW_VERSION = "1.1.0-development"
RECONCILIATION_VERSION = "1.1.0-development"
FROZEN_SEMANTIC_REVIEW_CONTRACT_DIGEST = (
    "sha256:bf3f4c325f8aac9e70045ff57bdcfc28cbf28764bc1974f55e83ec201b3b04a9"
)


class SelectedResultSemanticReviewError(ValueError):
    """Raised when a blind semantic-review artifact cannot replay exactly."""


def freeze_blind_semantic_review(
    *,
    case_root: Path,
    target_packet: Mapping[str, Any],
    assignment_binding: Mapping[str, Any],
    runner_freeze_digest: str,
    semantic_contract: Mapping[str, Any],
    identity_registry: Mapping[str, Any],
    author_identity: Mapping[str, Any],
    validator_identity: Mapping[str, Any],
    validator_identity_evidence: Mapping[str, Any],
    semantic_conclusion: Mapping[str, Any],
    binding_evidence: Mapping[str, Any] | None,
    rule_trace: Sequence[Mapping[str, Any]],
    independence_declaration: Mapping[str, Any],
    completed_at: str,
) -> dict[str, Any]:
    """Freeze a complete review before any construction certificate is an input.

    This operation deliberately has no certificate parameter and does not import the target
    verifier.  It verifies retained bytes, exact evidence spans, the semantic-contract digest,
    and a retained identity receipt, but it does not treat the reviewer's conclusion as true.
    """

    case_tree = _read_case_tree(case_root)
    packet = _target_packet(target_packet)
    assignment = _assignment_binding(assignment_binding, packet=packet)
    contract = _semantic_contract(semantic_contract)
    registry = validate_identity_registry(identity_registry)
    author = _identity(author_identity, "case author")
    validator = _identity(validator_identity, "semantic validator")
    _require_author_reviewer_independence(author, validator)
    inventory = _inventory_case_tree(case_tree)
    conclusion = _semantic_conclusion(
        semantic_conclusion,
        reason_codes_by_state=_reason_taxonomy(contract),
    )
    canonical_binding = _binding_evidence(case_tree, binding_evidence)
    expected_binding_digest = (
        semantic_digest(canonical_binding) if canonical_binding is not None else None
    )
    if conclusion["positive_binding_digest"] != expected_binding_digest:
        raise SelectedResultSemanticReviewError(
            "Blind review conclusion does not bind its retained positive evidence."
        )
    trace = _rule_trace(case_tree, rule_trace)
    if not trace:
        raise SelectedResultSemanticReviewError(
            "Blind semantic review requires a retained non-empty rule trace."
        )
    _validate_conclusion_trace(
        case_tree=case_tree,
        packet=packet,
        inventory=inventory,
        conclusion=conclusion,
        binding=canonical_binding,
        trace=trace,
    )
    input_manifest_digest = semantic_digest(
        {
            "case_inventory": inventory,
            "target_packet": packet,
            "assignment_binding": assignment,
            "runner_freeze_digest": runner_freeze_digest,
            "semantic_contract_digest": contract["contract_digest"],
        }
    )
    review_content_digest = semantic_digest(
        {
            "input_manifest_digest": input_manifest_digest,
            "semantic_conclusion": conclusion,
            "binding_evidence": canonical_binding,
            "rule_trace": trace,
            "independence_declaration": independence_declaration,
        }
    )
    identity_evidence = validate_provider_session_identity_evidence(
        validator_identity_evidence,
        registry=registry,
        identity=validator,
        role="semantic-reviewer",
        case_id=packet["case_id"],
        target_packet_digest=semantic_digest(packet),
        assignment_digest=str(assignment["assignment_digest"]),
        semantic_contract_digest=str(contract["contract_digest"]),
        input_manifest_digest=input_manifest_digest,
        review_content_digest=review_content_digest,
    )
    declaration = _independence_declaration(independence_declaration)
    completed = _timestamp(completed_at)
    completion_receipt = _mapping(identity_evidence["completion_receipt"], "completion_receipt")
    if _timestamp(str(completion_receipt["issued_at"])) > completed:
        raise SelectedResultSemanticReviewError(
            "Validator identity evidence postdates the blind review."
        )
    record: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_blind_semantic_review",
        "blind_review_version": BLIND_REVIEW_VERSION,
        "case_id": packet["case_id"],
        "target_packet": packet,
        "assignment_binding": assignment,
        "runner_freeze_digest": _digest(runner_freeze_digest, "runner_freeze_digest"),
        "semantic_contract_digest": contract["contract_digest"],
        "identity_registry_digest": registry["identity_registry_digest"],
        "input_manifest_digest": input_manifest_digest,
        "review_content_digest": review_content_digest,
        "case_inventory": inventory,
        "case_inventory_digest": semantic_digest(inventory),
        "semantic_conclusion": conclusion,
        "binding_evidence": canonical_binding,
        "rule_trace": trace,
        "author_identity": author,
        "validator_identity": validator,
        "validator_identity_evidence": identity_evidence,
        "independence_declaration": declaration,
        "completed_at": _iso(completed),
        "construction_certificate_available": False,
        "target_source_available": False,
        "target_tests_available": False,
        "target_output_available": False,
        "qualification_authority": "none_blind_semantic_review_only",
    }
    record["blind_review_digest"] = semantic_digest(record)
    return record


def revalidate_blind_semantic_review(
    value: Mapping[str, Any],
    *,
    case_root: Path,
    target_packet: Mapping[str, Any],
    assignment_binding: Mapping[str, Any],
    runner_freeze_digest: str,
    semantic_contract: Mapping[str, Any],
    identity_registry: Mapping[str, Any],
    author_identity: Mapping[str, Any],
) -> dict[str, Any]:
    """Replay a blind review from the retained evidence without a certificate."""

    review = _self_digested(value, "blind_review_digest")
    required = {
        "artifact_kind",
        "blind_review_version",
        "case_id",
        "target_packet",
        "assignment_binding",
        "runner_freeze_digest",
        "semantic_contract_digest",
        "identity_registry_digest",
        "input_manifest_digest",
        "review_content_digest",
        "case_inventory",
        "case_inventory_digest",
        "semantic_conclusion",
        "binding_evidence",
        "rule_trace",
        "author_identity",
        "validator_identity",
        "validator_identity_evidence",
        "independence_declaration",
        "completed_at",
        "construction_certificate_available",
        "target_source_available",
        "target_tests_available",
        "target_output_available",
        "qualification_authority",
        "blind_review_digest",
    }
    _exact_keys(review, required, "blind semantic review")
    packet = _target_packet(target_packet)
    assignment = _assignment_binding(assignment_binding, packet=packet)
    contract = _semantic_contract(semantic_contract)
    registry = validate_identity_registry(identity_registry)
    author = _identity(author_identity, "case author")
    validator = _identity(
        _mapping(review["validator_identity"], "validator_identity"), "semantic validator"
    )
    _require_author_reviewer_independence(author, validator)
    case_tree = _read_case_tree(case_root)
    inventory = _inventory_case_tree(case_tree)
    conclusion = _semantic_conclusion(
        _mapping(review["semantic_conclusion"], "semantic_conclusion"),
        reason_codes_by_state=_reason_taxonomy(contract),
    )
    binding = _binding_evidence(
        case_tree,
        cast(Mapping[str, Any] | None, review["binding_evidence"]),
    )
    trace = _rule_trace(
        case_tree,
        _object_sequence(review["rule_trace"], "rule_trace"),
    )
    _validate_conclusion_trace(
        case_tree=case_tree,
        packet=packet,
        inventory=inventory,
        conclusion=conclusion,
        binding=binding,
        trace=trace,
    )
    input_manifest_digest = semantic_digest(
        {
            "case_inventory": inventory,
            "target_packet": packet,
            "assignment_binding": assignment,
            "runner_freeze_digest": runner_freeze_digest,
            "semantic_contract_digest": contract["contract_digest"],
        }
    )
    review_content_digest = semantic_digest(
        {
            "input_manifest_digest": input_manifest_digest,
            "semantic_conclusion": conclusion,
            "binding_evidence": binding,
            "rule_trace": trace,
            "independence_declaration": review["independence_declaration"],
        }
    )
    identity_evidence = validate_provider_session_identity_evidence(
        _mapping(review["validator_identity_evidence"], "validator_identity_evidence"),
        registry=registry,
        identity=validator,
        role="semantic-reviewer",
        case_id=packet["case_id"],
        target_packet_digest=semantic_digest(packet),
        assignment_digest=str(assignment["assignment_digest"]),
        semantic_contract_digest=str(contract["contract_digest"]),
        input_manifest_digest=input_manifest_digest,
        review_content_digest=review_content_digest,
    )
    expected_binding_digest = semantic_digest(binding) if binding is not None else None
    if (
        review["artifact_kind"] != "selected_result_verifier_blind_semantic_review"
        or review["blind_review_version"] != BLIND_REVIEW_VERSION
        or review["qualification_authority"] != "none_blind_semantic_review_only"
        or review["case_id"] != packet["case_id"]
        or review["target_packet"] != packet
        or review["assignment_binding"] != assignment
        or review["runner_freeze_digest"] != runner_freeze_digest
        or review["semantic_contract_digest"] != contract["contract_digest"]
        or review["identity_registry_digest"] != registry["identity_registry_digest"]
        or review["input_manifest_digest"] != input_manifest_digest
        or review["review_content_digest"] != review_content_digest
        or review["case_inventory"] != inventory
        or review["case_inventory_digest"] != semantic_digest(inventory)
        or review["semantic_conclusion"] != conclusion
        or review["binding_evidence"] != binding
        or review["rule_trace"] != trace
        or review["author_identity"] != author
        or review["validator_identity_evidence"] != identity_evidence
        or conclusion["positive_binding_digest"] != expected_binding_digest
        or review["construction_certificate_available"] is not False
        or review["target_source_available"] is not False
        or review["target_tests_available"] is not False
        or review["target_output_available"] is not False
    ):
        raise SelectedResultSemanticReviewError("Blind semantic review does not replay.")
    _independence_declaration(
        _mapping(review["independence_declaration"], "independence_declaration")
    )
    completed = _timestamp(_text(review["completed_at"], "completed_at"))
    completion_receipt = _mapping(identity_evidence["completion_receipt"], "completion_receipt")
    if _timestamp(str(completion_receipt["issued_at"])) > completed:
        raise SelectedResultSemanticReviewError(
            "Validator identity evidence postdates the blind review."
        )
    return review


def reconcile_blind_semantic_review(
    *,
    blind_review: Mapping[str, Any],
    case_root: Path,
    certificate: ConstructionCertificate,
    target_packet: Mapping[str, Any],
    assignment_binding: Mapping[str, Any],
    runner_freeze_digest: str,
    semantic_contract: Mapping[str, Any],
    identity_registry: Mapping[str, Any],
    author_identity: Mapping[str, Any],
    certificate_revealed_at: str,
    reconciled_at: str,
) -> dict[str, Any]:
    """Compare one already-frozen blind conclusion with the byte-verified certificate."""

    from sc_referee_evaluation.selected_result_qualification_oracle import (
        verify_construction_certificate,
    )

    review = revalidate_blind_semantic_review(
        blind_review,
        case_root=case_root,
        target_packet=target_packet,
        assignment_binding=assignment_binding,
        runner_freeze_digest=runner_freeze_digest,
        semantic_contract=semantic_contract,
        identity_registry=identity_registry,
        author_identity=author_identity,
    )
    revealed = _timestamp(certificate_revealed_at)
    reconciled = _timestamp(reconciled_at)
    if revealed < _timestamp(str(review["completed_at"])):
        raise SelectedResultSemanticReviewError(
            "Construction certificate was revealed before the blind review was frozen."
        )
    if reconciled < revealed:
        raise SelectedResultSemanticReviewError(
            "Certificate reconciliation predates certificate reveal."
        )
    verified = verify_construction_certificate(certificate, case_root)
    if certificate.case_id != review["case_id"]:
        raise SelectedResultSemanticReviewError(
            "Construction certificate and blind review case identities differ."
        )
    certificate_binding = _certificate_binding_evidence(certificate)
    certificate_conclusion = {
        "expected_state": verified.expected_state,
        "reason_codes": list(verified.reason_codes),
        "positive_binding_digest": (
            semantic_digest(certificate_binding) if certificate_binding is not None else None
        ),
    }
    agreement = review["semantic_conclusion"] == certificate_conclusion
    record: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_semantic_reconciliation",
        "reconciliation_version": RECONCILIATION_VERSION,
        "case_id": review["case_id"],
        "blind_review_digest": review["blind_review_digest"],
        "blind_review": review,
        "construction_certificate_digest": certificate.certificate_digest,
        "certificate_conclusion": certificate_conclusion,
        "certificate_revealed_at": _iso(revealed),
        "reconciled_at": _iso(reconciled),
        "agrees_with_construction_certificate": agreement,
        "target_output_available": False,
        "qualification_authority": "none_semantic_reconciliation_only",
    }
    record["semantic_reconciliation_digest"] = semantic_digest(record)
    return record


def revalidate_semantic_reconciliation(
    value: Mapping[str, Any],
    *,
    case_root: Path,
    certificate: ConstructionCertificate,
    target_packet: Mapping[str, Any],
    assignment_binding: Mapping[str, Any],
    runner_freeze_digest: str,
    semantic_contract: Mapping[str, Any],
    identity_registry: Mapping[str, Any],
    author_identity: Mapping[str, Any],
) -> dict[str, Any]:
    """Replay a post-reveal reconciliation and its embedded blind record."""

    current = _self_digested(value, "semantic_reconciliation_digest")
    required = {
        "artifact_kind",
        "reconciliation_version",
        "case_id",
        "blind_review_digest",
        "blind_review",
        "construction_certificate_digest",
        "certificate_conclusion",
        "certificate_revealed_at",
        "reconciled_at",
        "agrees_with_construction_certificate",
        "target_output_available",
        "qualification_authority",
        "semantic_reconciliation_digest",
    }
    _exact_keys(current, required, "semantic reconciliation")
    rebuilt = reconcile_blind_semantic_review(
        blind_review=_mapping(current["blind_review"], "blind_review"),
        case_root=case_root,
        certificate=certificate,
        target_packet=target_packet,
        assignment_binding=assignment_binding,
        runner_freeze_digest=runner_freeze_digest,
        semantic_contract=semantic_contract,
        identity_registry=identity_registry,
        author_identity=author_identity,
        certificate_revealed_at=_text(
            current["certificate_revealed_at"], "certificate_revealed_at"
        ),
        reconciled_at=_text(current["reconciled_at"], "reconciled_at"),
    )
    if rebuilt != current:
        raise SelectedResultSemanticReviewError(
            "Semantic reconciliation does not replay from its blind review and certificate."
        )
    return current


def certificate_binding_evidence(
    certificate: ConstructionCertificate,
) -> dict[str, Any] | None:
    """Public projection used by the qualification controller and test fixtures."""

    return _certificate_binding_evidence(certificate)


def _certificate_binding_evidence(
    certificate: ConstructionCertificate,
) -> dict[str, Any] | None:
    binding = certificate.positive_binding
    if binding is None:
        return None
    spans = {item.span_id: item for item in certificate.spans}
    try:
        return _canonical_binding(
            result=spans[binding.result_span_id],
            producer=spans[binding.producer_span_id],
            operands=[spans[item] for item in binding.operand_span_ids],
            report=spans[binding.report_span_id],
        )
    except KeyError as error:
        raise SelectedResultSemanticReviewError(
            "Certificate positive binding references an absent span."
        ) from error


def _binding_evidence(
    case_tree: RootedTreeRead, value: Mapping[str, Any] | None
) -> dict[str, Any] | None:
    if value is None:
        return None
    binding = dict(value)
    _exact_keys(
        binding,
        {"result", "producer", "operands", "report"},
        "positive binding evidence",
    )
    result = _evidence_span(case_tree, binding["result"], "result")
    producer = _evidence_span(case_tree, binding["producer"], "producer")
    report = _evidence_span(case_tree, binding["report"], "report")
    operands = [
        _evidence_span(case_tree, item, "operand")
        for item in _sequence(binding["operands"], "binding operands")
    ]
    if not operands:
        raise SelectedResultSemanticReviewError(
            "Positive binding evidence requires at least one operand."
        )
    canonical = {
        "result": result,
        "producer": producer,
        "operands": sorted(
            operands,
            key=lambda item: (str(item["path"]), int(item["start"]), int(item["end"])),
        ),
        "report": report,
    }
    return canonical


def _canonical_binding(
    *,
    result: SpanCertificate,
    producer: SpanCertificate,
    operands: Sequence[SpanCertificate],
    report: SpanCertificate,
) -> dict[str, Any]:
    def project(span: SpanCertificate) -> dict[str, Any]:
        return {
            "path": span.path,
            "start": span.start,
            "end": span.end,
            "sha256": (
                span.sha256 if span.sha256.startswith("sha256:") else f"sha256:{span.sha256}"
            ),
        }

    return {
        "result": project(result),
        "producer": project(producer),
        "operands": sorted(
            (project(item) for item in operands),
            key=lambda item: (str(item["path"]), int(item["start"]), int(item["end"])),
        ),
        "report": project(report),
    }


def _evidence_span(case_tree: RootedTreeRead, value: Any, role: str) -> dict[str, Any]:
    span = dict(_mapping(value, f"{role} evidence span"))
    _exact_keys(span, {"path", "start", "end", "sha256"}, f"{role} evidence span")
    path = _relative_path(span["path"], f"{role} evidence path")
    start = _integer(span["start"], f"{role} evidence start")
    end = _integer(span["end"], f"{role} evidence end")
    payload = _payload(case_tree, path)
    if start < 0 or end <= start or end > len(payload):
        raise SelectedResultSemanticReviewError(f"{role} evidence span is outside its file.")
    supplied = _digest(span["sha256"], f"{role} evidence sha256")
    if supplied != sha256_digest(payload[start:end]):
        raise SelectedResultSemanticReviewError(f"{role} evidence span digest has drifted.")
    return {"path": path, "start": start, "end": end, "sha256": supplied}


def _rule_trace(
    case_tree: RootedTreeRead, values: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for raw in values:
        item = dict(raw)
        _exact_keys(item, {"rule_id", "outcome", "evidence"}, "semantic rule trace item")
        rule_id = _text(item["rule_id"], "semantic rule id")
        outcome = _text(item["outcome"], "semantic rule outcome")
        if outcome not in {"matched", "not_matched", "not_applicable"}:
            raise SelectedResultSemanticReviewError("Semantic rule outcome is unsupported.")
        evidence = [
            _evidence_span(case_tree, span, "rule-trace")
            for span in _sequence(item["evidence"], "semantic rule evidence")
        ]
        if outcome == "matched" and not evidence:
            raise SelectedResultSemanticReviewError(
                "A matched semantic rule requires retained byte evidence."
            )
        result.append({"rule_id": rule_id, "outcome": outcome, "evidence": evidence})
    if len({item["rule_id"] for item in result}) != len(result):
        raise SelectedResultSemanticReviewError("Semantic rule trace repeats a rule id.")
    return result


def _validate_conclusion_trace(
    *,
    case_tree: RootedTreeRead,
    packet: Mapping[str, str],
    inventory: Sequence[Mapping[str, Any]],
    conclusion: Mapping[str, Any],
    binding: Mapping[str, Any] | None,
    trace: Sequence[Mapping[str, Any]],
) -> None:
    matched = [item for item in trace if item["outcome"] == "matched"]
    state = str(conclusion["expected_state"])
    reasons = cast(list[str], conclusion["reason_codes"])
    if state == "V":
        if (
            binding is None
            or len(matched) != 1
            or matched[0]["rule_id"] != "supported_single_binding"
        ):
            raise SelectedResultSemanticReviewError(
                "V requires one matched supported-single-binding trace and full binding evidence."
            )
        _validate_v_binding_shape(case_tree, binding)
        return
    if binding is not None or len(reasons) != 1 or len(matched) != 1:
        raise SelectedResultSemanticReviewError(
            "A non-V conclusion requires exactly one matched reason trace and no V binding."
        )
    reason = reasons[0]
    if matched[0]["rule_id"] != reason:
        raise SelectedResultSemanticReviewError(
            "Matched semantic rule does not equal the concluded reason."
        )
    evidence = cast(Sequence[Mapping[str, Any]], matched[0]["evidence"])
    paths = [str(item["path"]) for item in inventory]
    report_path = packet["selected_report_path"]

    if reason == "multiple_selected_result_bindings_rederived":
        if len({semantic_digest(dict(item)) for item in evidence}) < 2:
            raise SelectedResultSemanticReviewError(
                "Ambiguity requires at least two distinct retained binding witnesses."
            )
        return
    if reason == "selected_report_missing":
        _require(not _inventory_has_path(paths, report_path), reason)
        return
    if reason == "selected_report_empty":
        _require(_payload(case_tree, report_path) == b"", reason)
        return
    if reason == "selected_result_marker_missing":
        payload = _payload(case_tree, report_path)
        text = _ascii_lf(payload, reason)
        _require(
            bool(text.splitlines())
            and not any(line.strip().startswith("[selected-result]") for line in text.splitlines()),
            reason,
        )
        return
    if reason == "unsupported_selected_report_role":
        payload = _payload(case_tree, report_path)
        mode = _inventory_mode(inventory, report_path)
        _require(
            PurePosixPath(report_path).suffix.lower() not in {".md", ".txt"}
            or bool(mode & 0o111)
            or payload.startswith(b"#!")
            or b"\x00" in payload,
            reason,
        )
        return
    if reason == "unsupported_non_python_source_artifact":
        _require(any(_is_forbidden_source_path(path) for path in paths), reason)
        return
    if reason == "python_source_absent":
        _require(not any(path.endswith(".py") for path in paths), reason)
        return
    if reason == "python_source_byte_ceiling_exceeded":
        _require(
            any(
                path.endswith(".py") and len(_payload(case_tree, path)) > 1_048_576
                for path in paths
            ),
            reason,
        )
        return
    if reason == "python_source_parse_failed":
        failures = 0
        for path in paths:
            if not path.endswith(".py"):
                continue
            try:
                ast.parse(_payload(case_tree, path).decode("utf-8"), filename=path)
            except (MemoryError, RecursionError, SyntaxError, UnicodeDecodeError, ValueError):
                failures += 1
        _require(failures > 0, reason)
        return
    if reason == "python_ast_node_ceiling_exceeded":
        exceeded = False
        for path in paths:
            if path.endswith(".py"):
                try:
                    tree = ast.parse(_payload(case_tree, path).decode("utf-8"), filename=path)
                except (SyntaxError, UnicodeDecodeError, ValueError):
                    continue
                exceeded = exceeded or sum(1 for _ in ast.walk(tree)) > 50_000
        _require(exceeded, reason)
        return
    if reason == "unsupported_source_operand_role":
        _require(
            any(
                _operand_role_unsupported(case_tree, inventory, str(item["path"]))
                for item in evidence
            ),
            reason,
        )
        return
    if reason == "non_utf8_selected_result_evidence":
        _require(
            any(
                path.endswith(".py") and not _decodes(_payload(case_tree, path), "utf-8")
                for path in paths
            ),
            reason,
        )
        return
    if reason == "unsupported_python_encoding_declaration":
        cookie = re.compile(rb"^[ \t\f]*\#.*?coding[:=][ \t]*[-_.a-zA-Z0-9]+")
        _require(
            any(
                path.endswith(".py")
                and (
                    _payload(case_tree, path).startswith(b"\xef\xbb\xbf")
                    or any(
                        cookie.match(line) for line in _payload(case_tree, path).split(b"\n")[:2]
                    )
                )
                for path in paths
            ),
            reason,
        )
        return
    if reason == "non_lf_normalized_text_evidence":
        _require(any(b"\r" in _payload(case_tree, str(item["path"])) for item in evidence), reason)
        return
    if reason == "non_ascii_text_evidence":
        _require(
            any(not _decodes(_payload(case_tree, str(item["path"])), "ascii") for item in evidence),
            reason,
        )
        return
    if reason == "selected_result_line_ceiling_exceeded":
        _require(
            any(
                len(_payload(case_tree, str(item["path"])).splitlines()) > 10_000
                for item in evidence
            ),
            reason,
        )
        return
    if reason == "text_io_runtime_unsupported":
        encoding = locale.getencoding()
        try:
            round_trip = bytes(range(128)).decode(encoding).encode(encoding)
        except (LookupError, UnicodeError):
            round_trip = b""
        _require(os.linesep != "\n" or round_trip != bytes(range(128)), reason)
        return
    # The remaining exact-AST/dataflow reasons require human semantic review under the complete
    # frozen grammar.  Their full byte witnesses remain replayed above; two authenticated blind
    # reviews and post-reveal agreement are still required.  They are not converted into software
    # truth by this evidence-shape validator.


def _validate_v_binding_shape(case_tree: RootedTreeRead, binding: Mapping[str, Any]) -> None:
    report = cast(Mapping[str, Any], binding["report"])
    result = cast(Mapping[str, Any], binding["result"])
    producer = cast(Mapping[str, Any], binding["producer"])
    operands = cast(Sequence[Mapping[str, Any]], binding["operands"])
    report_payload = _payload(case_tree, str(report["path"]))
    if int(report["start"]) != 0 or int(report["end"]) != len(report_payload):
        raise SelectedResultSemanticReviewError("V report evidence must cover the complete file.")
    for operand in operands:
        payload = _payload(case_tree, str(operand["path"]))
        if int(operand["start"]) != 0 or int(operand["end"]) != len(payload):
            raise SelectedResultSemanticReviewError(
                "V operand evidence must cover the complete file."
            )
    for label, span in (("result", result), ("producer", producer)):
        payload = _payload(case_tree, str(span["path"]))
        boundaries = _line_boundaries(payload)
        if (int(span["start"]), int(span["end"])) not in boundaries:
            raise SelectedResultSemanticReviewError(
                f"V {label} evidence must cover complete retained lines."
            )


def _line_boundaries(payload: bytes) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    lines = payload.splitlines(keepends=True)
    cursor = 0
    for start_index in range(len(lines)):
        start = sum(len(item) for item in lines[:start_index])
        cursor = start
        for line in lines[start_index:]:
            cursor += len(line)
            result.add((start, cursor))
    return result


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise SelectedResultSemanticReviewError(
            f"Retained review evidence does not demonstrate {reason}."
        )


def _inventory_has_path(paths: Sequence[str], path: str) -> bool:
    return path in paths


def _inventory_mode(inventory: Sequence[Mapping[str, Any]], path: str) -> int:
    matches = [int(item["mode"]) for item in inventory if item["path"] == path]
    if len(matches) != 1:
        raise SelectedResultSemanticReviewError("Evidence path is absent from the inventory.")
    return matches[0]


def _payload(case_tree: RootedTreeRead, path: str) -> bytes:
    try:
        return case_tree.read_bytes(path)
    except QualificationIOError as error:
        raise SelectedResultSemanticReviewError(
            "Semantic evidence path is absent or unsafe."
        ) from error


def _ascii_lf(payload: bytes, reason: str) -> str:
    try:
        text = payload.decode("ascii")
    except UnicodeDecodeError as error:
        raise SelectedResultSemanticReviewError(
            f"Retained evidence for {reason} is not ASCII."
        ) from error
    if "\r" in text:
        raise SelectedResultSemanticReviewError(
            f"Retained evidence for {reason} is not LF-normalized."
        )
    return text


def _decodes(payload: bytes, encoding: str) -> bool:
    try:
        payload.decode(encoding)
    except UnicodeDecodeError:
        return False
    return True


def _operand_role_unsupported(
    case_tree: RootedTreeRead, inventory: Sequence[Mapping[str, Any]], path: str
) -> bool:
    payload = _payload(case_tree, path)
    mode = _inventory_mode(inventory, path)
    return (
        PurePosixPath(path).suffix.lower() not in {".csv", ".tsv"}
        or bool(mode & 0o111)
        or payload.startswith(b"#!")
        or b"\x00" in payload
    )


def _is_forbidden_source_path(path: str) -> bool:
    suffixes = {
        ".bash",
        ".c",
        ".cc",
        ".clj",
        ".cpp",
        ".cs",
        ".cwl",
        ".do",
        ".fish",
        ".fs",
        ".fsx",
        ".go",
        ".groovy",
        ".h",
        ".hpp",
        ".ipynb",
        ".java",
        ".jl",
        ".js",
        ".jsx",
        ".kt",
        ".kts",
        ".lua",
        ".m",
        ".nf",
        ".php",
        ".pl",
        ".pm",
        ".r",
        ".rb",
        ".rmd",
        ".rs",
        ".sas",
        ".scala",
        ".sh",
        ".smk",
        ".sql",
        ".swift",
        ".ts",
        ".tsx",
        ".wdl",
        ".zsh",
    }
    names = {"dockerfile", "jenkinsfile", "makefile", "nextflow.config", "snakefile"}
    pure = PurePosixPath(path)
    return pure.suffix.lower() in suffixes or pure.name.lower() in names


def _semantic_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    contract = dict(value)
    supplied = contract.pop("contract_digest", None)
    if supplied != semantic_digest(contract):
        raise SelectedResultSemanticReviewError("Semantic review contract digest does not replay.")
    contract["contract_digest"] = supplied
    if (
        contract.get("artifact_kind") != "selected_result_verifier_semantic_review_contract"
        or contract.get("contract_version") != "1.1.0"
        or contract.get("contract_digest") != FROZEN_SEMANTIC_REVIEW_CONTRACT_DIGEST
        or contract.get("qualification_authority") != "none_semantic_review_contract_only"
    ):
        raise SelectedResultSemanticReviewError("Unsupported semantic review contract.")
    _reason_taxonomy(contract)
    return contract


def _reason_taxonomy(contract: Mapping[str, Any]) -> dict[str, frozenset[str]]:
    raw = _mapping(contract.get("reason_codes_by_state"), "reason_codes_by_state")
    if set(raw) != {"V", "A", "I", "U"}:
        raise SelectedResultSemanticReviewError("Semantic reason taxonomy is incomplete.")
    result = {
        state: frozenset(
            _text(item, f"{state} reason") for item in _sequence(raw[state], f"{state} reasons")
        )
        for state in ("V", "A", "I", "U")
    }
    if result["V"]:
        raise SelectedResultSemanticReviewError("V cannot register a reason code.")
    return result


def _semantic_conclusion(
    value: Mapping[str, Any], *, reason_codes_by_state: Mapping[str, frozenset[str]]
) -> dict[str, Any]:
    conclusion = dict(value)
    _exact_keys(
        conclusion,
        {"expected_state", "reason_codes", "positive_binding_digest"},
        "semantic conclusion",
    )
    state = _text(conclusion["expected_state"], "expected_state")
    if state not in {"V", "A", "I", "U"}:
        raise SelectedResultSemanticReviewError("Expected state must be V, A, I, or U.")
    reasons = [
        _text(item, "semantic reason")
        for item in _sequence(conclusion["reason_codes"], "semantic reasons")
    ]
    if state == "V":
        if reasons or conclusion["positive_binding_digest"] is None:
            raise SelectedResultSemanticReviewError(
                "V requires one positive-binding digest and no reason code."
            )
        binding_digest: str | None = _digest(
            conclusion["positive_binding_digest"], "positive_binding_digest"
        )
    else:
        if (
            len(reasons) != 1
            or reasons[0] not in reason_codes_by_state[state]
            or conclusion["positive_binding_digest"] is not None
        ):
            raise SelectedResultSemanticReviewError(
                "Non-V requires one registered reason and no positive binding."
            )
        binding_digest = None
    return {
        "expected_state": state,
        "reason_codes": reasons,
        "positive_binding_digest": binding_digest,
    }


def _independence_declaration(value: Mapping[str, Any]) -> dict[str, bool]:
    declaration = dict(value)
    expected = {
        "case_bytes_inspected": True,
        "semantic_contract_inspected": True,
        "construction_certificate_seen": False,
        "target_source_seen": False,
        "target_tests_seen": False,
        "target_output_seen": False,
        "other_review_seen": False,
    }
    _exact_keys(declaration, set(expected), "blind-review independence declaration")
    if declaration != expected:
        raise SelectedResultSemanticReviewError(
            "Semantic review was not blind at the time its conclusion was frozen."
        )
    return cast(dict[str, bool], declaration)


def _read_case_tree(case_root: Path) -> RootedTreeRead:
    try:
        with RootedReader(case_root) as reader:
            return reader.read_case_tree()
    except QualificationIOError as error:
        raise SelectedResultSemanticReviewError(
            "Blind review case tree could not be read as one immutable tree."
        ) from error


def _inventory_case_tree(case_tree: RootedTreeRead) -> list[dict[str, Any]]:
    return [
        {
            "path": item.relative_path,
            "size": item.byte_length,
            "sha256": item.content_digest,
            "mode": item.mode,
        }
        for item in case_tree.files
    ]


def _target_packet(value: Mapping[str, Any]) -> dict[str, str]:
    packet = dict(value)
    _exact_keys(
        packet,
        {"case_id", "profile_id", "selected_report_path"},
        "target packet",
    )
    return {
        "case_id": _text(packet["case_id"], "case_id"),
        "profile_id": _text(packet["profile_id"], "profile_id"),
        "selected_report_path": _relative_path(
            packet["selected_report_path"], "selected_report_path"
        ),
    }


def _assignment_binding(value: Mapping[str, Any], *, packet: Mapping[str, str]) -> dict[str, Any]:
    binding = dict(value)
    _exact_keys(
        binding,
        {
            "assignment_digest",
            "block",
            "provider_slot",
            "assignment_position",
            "case_id",
            "target_packet",
        },
        "assignment binding",
    )
    _digest(binding["assignment_digest"], "assignment_digest")
    if binding["case_id"] != packet["case_id"] or binding["target_packet"] != dict(packet):
        raise SelectedResultSemanticReviewError(
            "Assignment binding does not match the target packet."
        )
    return binding


def _identity(value: Mapping[str, Any], label: str) -> dict[str, str]:
    identity = dict(value)
    _exact_keys(
        identity,
        {"actor_id", "provider", "execution_context_id", "identity_evidence_digest"},
        f"{label} identity",
    )
    return {key: _text(identity[key], f"{label} {key}") for key in identity}


def _require_author_reviewer_independence(
    author: Mapping[str, str], validator: Mapping[str, str]
) -> None:
    if (
        author["actor_id"] == validator["actor_id"]
        or author["provider"] == validator["provider"]
        or author["execution_context_id"] == validator["execution_context_id"]
    ):
        raise SelectedResultSemanticReviewError(
            "Semantic validator is not cross-provider independent of the case author."
        )


def _self_digested(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    supplied = result.pop(field, None)
    if supplied != semantic_digest(result):
        raise SelectedResultSemanticReviewError(f"{field} does not replay.")
    result[field] = supplied
    return result


def _relative_path(value: Any, label: str) -> str:
    text = _text(value, label)
    path = PurePosixPath(text)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise SelectedResultSemanticReviewError(f"{label} must be a safe relative POSIX path.")
    return path.as_posix()


def _digest(value: Any, label: str) -> str:
    text = _text(value, label)
    if not text.startswith("sha256:") or len(text) != 71:
        raise SelectedResultSemanticReviewError(f"{label} must be a SHA-256 digest.")
    try:
        int(text[7:], 16)
    except ValueError as error:
        raise SelectedResultSemanticReviewError(f"{label} must be a SHA-256 digest.") from error
    return text


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise SelectedResultSemanticReviewError("Timestamp is invalid.") from error
    if parsed.tzinfo is None:
        raise SelectedResultSemanticReviewError("Timestamp requires a timezone.")
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _integer(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SelectedResultSemanticReviewError(f"{label} must be an integer.")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\n" in value or "\r" in value:
        raise SelectedResultSemanticReviewError(f"{label} must be non-empty one-line text.")
    return value


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SelectedResultSemanticReviewError(f"{label} must be an object.")
    return value


def _sequence(value: Any, label: str) -> Sequence[Any]:
    if not isinstance(value, (list, tuple)):
        raise SelectedResultSemanticReviewError(f"{label} must be a list.")
    return value


def _object_sequence(value: Any, label: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in _sequence(value, label):
        if not isinstance(item, Mapping):
            raise SelectedResultSemanticReviewError(f"{label} entries must be objects.")
        result.append(dict(item))
    return result


def _exact_keys(value: Mapping[str, Any], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise SelectedResultSemanticReviewError(f"{label} has an unsupported shape.")


__all__ = [
    "BLIND_REVIEW_VERSION",
    "FROZEN_SEMANTIC_REVIEW_CONTRACT_DIGEST",
    "RECONCILIATION_VERSION",
    "SelectedResultSemanticReviewError",
    "certificate_binding_evidence",
    "freeze_blind_semantic_review",
    "reconcile_blind_semantic_review",
    "revalidate_blind_semantic_review",
    "revalidate_semantic_reconciliation",
]
