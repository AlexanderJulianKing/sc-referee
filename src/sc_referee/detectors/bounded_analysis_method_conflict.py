from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.posthoc_method_ledger import (
    PosthocMethodLedgerError,
    project_analysis_posthoc_method_ledger,
)
from sc_referee.scientific_checks.core import MethodConflictBinding
from sc_referee.version import SCHEMA_VERSION, __version__


class BoundedAnalysisMethodConflictError(ValueError):
    """Raised when the detector manifest does not bind this implementation exactly."""


class BoundedAnalysisMethodConflictDetector:
    """Evaluate registered exact analysis-scoped report/source method conflicts."""

    detector_id = "detector:bounded-analysis-method-conflict"
    detector_version = "0.2.0"
    entry_point = (
        "sc_referee.detectors.bounded_analysis_method_conflict:"
        "BoundedAnalysisMethodConflictDetector"
    )
    maturity = "experimental"
    check_ids = (
        "check:analysis-requirement-authority",
        "check:reported-method-uniqueness",
        "check:static-method-uniqueness",
        "check:observed-plane-agreement",
        "check:selected-output-scope-closure",
        "check:alternate-or-superseding-intent",
        "check:governing-protocol-amendment",
        "check:approved-method-deviation",
        "check:conditional-applicability",
        "check:sensitivity-or-unsupported-qualifier",
    )

    def __init__(
        self,
        manifest: Mapping[str, Any],
        bindings: Sequence[MethodConflictBinding],
    ) -> None:
        self.manifest = deepcopy(dict(manifest))
        self.bindings = tuple(sorted(bindings, key=lambda item: item.binding_id))
        self.bindings_by_check = {item.check_id: item for item in self.bindings}
        self.supported_check_ids = tuple(sorted(self.bindings_by_check))
        self._validate_manifest()
        self.manifest_digest = semantic_digest(self.manifest)

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())

    def evaluate(
        self, locked_case: Mapping[str, Any], question: Mapping[str, Any]
    ) -> dict[str, Any]:
        packet = self._work_packet(locked_case, question)
        input_digest = semantic_digest(packet)
        subject_ref = _analysis_subject(question)
        target_ref = subject_ref or {
            "record_type": "publication_surface",
            "record_id": "publication-surface:unknown",
        }
        base = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "detector_result",
            "result_id": stable_id(
                "detector-result",
                self.detector_id,
                self.detector_version,
                str(question.get("question_id", "unknown")),
                input_digest,
            ),
            "audit_run_id": str(locked_case["audit_run_id"]),
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "detector_manifest_digest": self.manifest_digest,
            "detector_maturity": self.maturity,
            "target_refs": [target_ref],
            "evaluated_at": str(locked_case["locked_at"]),
            "runtime_mode": "static",
            "deterministic_input_digest": input_digest,
            "provenance": {
                "actor": {"actor_kind": "detector", "actor_id": self.detector_id},
                "method": "deterministic_bounded_analysis_method_conflict_evaluation",
                "created_at": str(locked_case["locked_at"]),
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "extensions": {
                "x-evaluation-only": True,
                "x-production-finding-permitted": False,
                "x-detector-profile": "bounded_analysis_method_conflict_v1",
                "x-scientific-check-ids": list(self.supported_check_ids),
            },
        }
        extensions = question.get("extensions")
        check_id = (
            str(extensions.get("x-scientific-check-id", ""))
            if isinstance(extensions, Mapping)
            else ""
        )
        binding = self.bindings_by_check.get(check_id)
        target_problem = _target_problem(question, subject_ref, binding)
        if target_problem is not None:
            return self._terminal(
                base,
                state="unsupported_path",
                applicability="not_applicable",
                basis=target_problem,
                unsupported=[target_problem],
                premises=[],
                evidence=[],
                checks=_unavailable_checks(self.check_ids, target_problem),
                gaps=[target_problem],
            )

        contracts = packet["scientific_contracts"]
        if len(contracts) != 1:
            problem = "The answered question does not resolve to one exact analysis contract."
            return self._terminal(
                base,
                state="insufficient_semantics",
                applicability="uncertain",
                basis=problem,
                unsupported=[],
                premises=[
                    _premise(
                        "premise:one-analysis-contract",
                        "One exact analysis-scoped ScientificContract resolves.",
                        "unknown",
                        True,
                        [],
                    )
                ],
                evidence=[],
                checks=_unavailable_checks(self.check_ids, problem),
                gaps=[problem],
            )

        assert binding is not None
        extensions = question["extensions"]
        assert isinstance(extensions, Mapping)
        forms = extensions["x-posthoc-comparison-forms"]
        observed_by_dimension = extensions["x-posthoc-reported-assertion-ids"]
        assert isinstance(forms, Mapping) and isinstance(observed_by_dimension, Mapping)
        dimension = next(iter(forms))
        comparison_form = str(forms[dimension])
        observed_ids = observed_by_dimension[dimension]
        scope_path = extensions["x-scientific-check-scope-join-path"]
        scope_digest = str(extensions["x-scientific-check-scope-join-digest"])
        assert isinstance(observed_ids, Sequence) and not isinstance(observed_ids, (str, bytes))
        assert isinstance(scope_path, Sequence) and not isinstance(scope_path, (str, bytes))
        assert subject_ref is not None
        try:
            ledger = project_analysis_posthoc_method_ledger(
                analysis_subject_ref=subject_ref,
                contract=contracts[0],
                assertions=packet["semantic_assertions"],
                observed_assertion_ids=[str(value) for value in observed_ids],
                dimension=str(dimension),
                comparison_form=comparison_form,
                scope_join_path=[dict(edge) for edge in scope_path if isinstance(edge, Mapping)],
                scope_join_digest=scope_digest,
            )
        except (PosthocMethodLedgerError, TypeError, ValueError) as error:
            problem = f"The closed analysis method ledger rejected this input: {error}"
            return self._terminal(
                base,
                state="insufficient_semantics",
                applicability="uncertain",
                basis=problem,
                unsupported=[],
                premises=[
                    _premise(
                        "premise:closed-analysis-method-ledger",
                        "The closed analysis-scoped method ledger replays exactly.",
                        "unknown",
                        True,
                        [],
                    )
                ],
                evidence=[],
                checks=_unavailable_checks(self.check_ids, problem),
                gaps=[problem],
            )

        checks, check_evidence, suppressors = _finite_checks(
            packet,
            question,
            ledger,
            [str(value) for value in observed_ids],
            self.check_ids,
            binding,
        )
        ledger_evidence = {
            "evidence_id": "evidence:analysis-method-ledger",
            "description": (
                "The controller-recomputed ledger compares one exact human review requirement "
                f"with the binding-required {_plane_description(binding)} operand(s)."
            ),
            "support_role": "supports",
            "source_refs": deepcopy(ledger.get("source_refs", [])),
            "record_refs": deepcopy(ledger.get("assertion_refs", [])),
            "observed_value": {
                "requirement": deepcopy(ledger.get("requirement")),
                "observed": deepcopy(ledger.get("observed")),
                "outcome": ledger.get("outcome"),
                "ledger_digest": ledger.get("ledger_digest"),
            },
        }
        evidence = [*check_evidence, ledger_evidence]
        premises = [
            _premise(
                "premise:verified-analysis-requirement",
                "One scope-bound human Answer supplies the governing requirement for this review.",
                "established" if not suppressors else "unknown",
                True,
                ["evidence:analysis-requirement-authority"],
            ),
            _premise(
                "premise:corroborated-report-and-source-operand",
                f"The binding-required {_plane_description(binding)} evidence exposes one "
                "unambiguous operand.",
                "established" if not suppressors else "unknown",
                True,
                [
                    "evidence:reported-method-uniqueness",
                    "evidence:static-method-uniqueness",
                    "evidence:observed-plane-agreement",
                    "evidence:selected-output-scope-closure",
                ],
            ),
            _premise(
                "premise:finite-analysis-counterevidence-absent",
                "All ten closed checks completed without a suppressor.",
                "established" if not suppressors else "refuted",
                True,
                [item["evidence_id"] for item in check_evidence],
            ),
        ]
        outcome = str(ledger.get("outcome"))
        premises.append(
            _premise(
                "premise:exact-analysis-method-conflict",
                "The exact observed and scientist-required operands differ.",
                (
                    "established"
                    if outcome == "exact_conflict_candidate" and not suppressors
                    else "refuted"
                    if outcome == "covered_negative" and not suppressors
                    else "unknown"
                ),
                True,
                ["evidence:analysis-method-ledger"],
            )
        )
        if suppressors:
            basis = (
                "At least one finite authority, uniqueness, scope, or counterevidence check "
                "prevents an exact analysis-method conflict evaluation."
            )
            return self._terminal(
                base,
                state="insufficient_semantics",
                applicability="uncertain",
                basis=basis,
                unsupported=[],
                premises=premises,
                evidence=evidence,
                checks=checks,
                gaps=suppressors,
                extra_extensions={"x-posthoc-method-ledger-digest": ledger["ledger_digest"]},
            )

        basis = (
            "One human review requirement and one binding-complete observed operand were "
            "compared under the exact selected-output scope after all finite checks."
        )
        if outcome == "covered_negative":
            return self._terminal(
                base,
                state="no_issue_detected_within_coverage",
                applicability="applicable",
                basis=basis,
                unsupported=[],
                premises=premises,
                evidence=evidence,
                checks=checks,
                gaps=[],
                extra_extensions={"x-posthoc-method-ledger-digest": ledger["ledger_digest"]},
            )
        if outcome != "exact_conflict_candidate":
            problem = f"The closed ledger outcome is {outcome}; no exact conflict is established."
            return self._terminal(
                base,
                state="insufficient_semantics",
                applicability="uncertain",
                basis=problem,
                unsupported=[],
                premises=premises,
                evidence=evidence,
                checks=checks,
                gaps=[problem],
                extra_extensions={"x-posthoc-method-ledger-digest": ledger["ledger_digest"]},
            )

        candidate = {
            "assessment_type": "finding",
            "title": "Selected method declaration conflicts with the review requirement",
            "bounded_statement": (
                f"For this selected analysis, the binding-required {_plane_description(binding)} "
                f"evidence declares {ledger['observed']!r}, while the scope-bound scientist Answer "
                f"requires {ledger['requirement']!r}. Those exact operands differ. This does "
                "not establish that the source ran, that the difference caused a numerical "
                "error, or that the required operand is universally correct."
            ),
            "material_premise_ids": [
                str(item["premise_id"]) for item in premises if item["state"] == "established"
            ],
            "unresolved_material_premise_ids": [],
        }
        return self._terminal(
            base,
            state="evaluation_finding_candidate",
            applicability="applicable",
            basis=basis,
            unsupported=[],
            premises=premises,
            evidence=evidence,
            checks=checks,
            gaps=[],
            candidate=candidate,
            extra_extensions={"x-posthoc-method-ledger-digest": ledger["ledger_digest"]},
        )

    def _work_packet(
        self, locked_case: Mapping[str, Any], question: Mapping[str, Any]
    ) -> dict[str, Any]:
        extensions = question.get("extensions")
        contract_id = ""
        subject_ref: Mapping[str, Any] | None = None
        if isinstance(extensions, Mapping):
            contract_ref = extensions.get("x-contract-ref")
            if isinstance(contract_ref, Mapping):
                contract_id = str(contract_ref.get("record_id", ""))
            candidate_subject = extensions.get("x-analysis-subject-ref")
            if isinstance(candidate_subject, Mapping):
                subject_ref = candidate_subject
        contracts = [
            deepcopy(dict(item))
            for item in locked_case.get("scientific_contracts", [])
            if isinstance(item, Mapping) and item.get("contract_id") == contract_id
        ]
        assertion_ids = _contract_assertion_ids(contracts)
        observed_ids: set[str] = set()
        if isinstance(extensions, Mapping):
            observed_by_dimension = extensions.get("x-posthoc-reported-assertion-ids")
            if isinstance(observed_by_dimension, Mapping):
                for values in observed_by_dimension.values():
                    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
                        observed_ids.update(str(value) for value in values)
        assertions = [
            deepcopy(dict(item))
            for item in locked_case.get("semantic_assertions", [])
            if isinstance(item, Mapping)
            and (
                str(item.get("assertion_id")) in assertion_ids
                or str(item.get("assertion_id")) in observed_ids
                or (subject_ref is not None and item.get("subject_ref") == subject_ref)
                or (
                    isinstance(extensions, Mapping)
                    and item.get("extensions", {}).get("x-scientific-check-id")
                    == extensions.get("x-scientific-check-id")
                    and item.get("extensions", {}).get("x-scientific-check-scope-join-digest")
                    == extensions.get("x-scientific-check-scope-join-digest")
                )
            )
        ]
        question_id = str(question.get("question_id", ""))
        answers = [
            deepcopy(dict(item))
            for item in locked_case.get("answers", [])
            if isinstance(item, Mapping)
            and item.get("question_ref")
            == {"record_type": "material_question", "record_id": question_id}
        ]
        return {
            "profile": "bounded_analysis_method_conflict_work_packet_v1",
            "audit_run_id": str(locked_case["audit_run_id"]),
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "detector_manifest_digest": self.manifest_digest,
            "target_question": deepcopy(dict(question)),
            "scientific_contracts": contracts,
            "semantic_assertions": assertions,
            "answers": answers,
            "file_records": _mapping_records(locked_case, "file_records"),
            "asset_identities": _mapping_records(locked_case, "asset_identities"),
            "operations": _mapping_records(locked_case, "operations"),
            "artifacts": _mapping_records(locked_case, "artifacts"),
            "publication_surfaces": _mapping_records(locked_case, "publication_surfaces"),
        }

    def _terminal(
        self,
        base: dict[str, Any],
        *,
        state: str,
        applicability: str,
        basis: str,
        unsupported: list[str],
        premises: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        checks: list[dict[str, Any]],
        gaps: list[str],
        candidate: dict[str, Any] | None = None,
        extra_extensions: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = deepcopy(base)
        record.update(
            {
                "state": state,
                "applicability": {
                    "status": applicability,
                    "basis": basis,
                    "unsupported_constructs": unsupported,
                },
                "premise_evaluations": premises,
                "evidence": evidence,
                "counterevidence_execution": checks,
                "coverage": {
                    "status": "covered" if applicability == "applicable" else "not_covered",
                    "basis": basis,
                    "gaps": gaps,
                },
                "unavailable_evidence": gaps,
            }
        )
        if candidate is not None:
            record["candidate"] = candidate
        if extra_extensions is not None:
            record["extensions"].update(deepcopy(dict(extra_extensions)))
        return record

    def _validate_manifest(self) -> None:
        expected = {
            "record_type": "detector_manifest",
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "maturity": self.maturity,
        }
        for key, value in expected.items():
            if self.manifest.get(key) != value:
                raise BoundedAnalysisMethodConflictError(
                    f"bounded analysis-method detector manifest has invalid {key}"
                )
        implementation = self.manifest.get("implementation")
        if not isinstance(implementation, Mapping):
            raise BoundedAnalysisMethodConflictError(
                "analysis-method detector manifest lacks implementation identity"
            )
        if implementation.get("entry_point") != self.entry_point:
            raise BoundedAnalysisMethodConflictError("detector manifest entry point mismatch")
        if implementation.get("deterministic") is not True:
            raise BoundedAnalysisMethodConflictError("detector must be deterministic")
        if implementation.get("implementation_digest") != self.implementation_digest():
            raise BoundedAnalysisMethodConflictError("detector implementation digest mismatch")
        declared_checks = tuple(
            str(item.get("check_id"))
            for item in self.manifest.get("counterevidence_protocol", [])
            if isinstance(item, Mapping)
        )
        if declared_checks != self.check_ids:
            raise BoundedAnalysisMethodConflictError("detector counterevidence protocol mismatch")
        declared_scientific_checks = self.manifest.get("extensions", {}).get(
            "x-scientific-check-ids"
        )
        if declared_scientific_checks != list(self.supported_check_ids):
            raise BoundedAnalysisMethodConflictError("scientific-check allowlist mismatch")
        if not self.bindings or len(self.bindings_by_check) != len(self.bindings):
            raise BoundedAnalysisMethodConflictError(
                "detector requires unique explicit method-conflict bindings"
            )
        detector_manifest_digest = semantic_digest(self.manifest)
        for binding in self.bindings:
            if (
                binding.detector_id != self.detector_id
                or binding.detector_version != self.detector_version
                or binding.detector_manifest_digest != detector_manifest_digest
                or binding.production_finding_permitted
            ):
                raise BoundedAnalysisMethodConflictError(
                    f"method-conflict binding {binding.binding_id} drifts from detector manifest"
                )
        outputs = self.manifest.get("permitted_output_types")
        if not isinstance(outputs, list) or "finding" in outputs:
            raise BoundedAnalysisMethodConflictError(
                "experimental detector manifest cannot permit Findings"
            )


def _target_problem(
    question: Mapping[str, Any],
    subject_ref: dict[str, str] | None,
    binding: MethodConflictBinding | None,
) -> str | None:
    extensions = question.get("extensions")
    forms = (
        extensions.get("x-posthoc-comparison-forms") if isinstance(extensions, Mapping) else None
    )
    observed = (
        extensions.get("x-posthoc-reported-assertion-ids")
        if isinstance(extensions, Mapping)
        else None
    )
    scope_path = (
        extensions.get("x-scientific-check-scope-join-path")
        if isinstance(extensions, Mapping)
        else None
    )
    if (
        question.get("record_type") != "material_question"
        or question.get("status") != "answered"
        or not isinstance(extensions, Mapping)
        or binding is None
        or extensions.get("x-scientific-check-id") != binding.check_id
        or extensions.get("x-output-ceiling") != "question_only"
        or subject_ref is None
        or forms != {binding.dimension: binding.comparison_form}
        or not isinstance(observed, Mapping)
        or set(observed) != {binding.dimension}
        or not isinstance(observed[binding.dimension], list)
        or len(observed[binding.dimension]) != len(binding.required_evidence_planes)
        or not isinstance(scope_path, list)
    ):
        return "The target is outside the exact answered analysis-method conflict profile."
    return None


def _analysis_subject(question: Mapping[str, Any]) -> dict[str, str] | None:
    extensions = question.get("extensions")
    value = extensions.get("x-analysis-subject-ref") if isinstance(extensions, Mapping) else None
    if (
        isinstance(value, Mapping)
        and value.get("record_type") == "publication_surface"
        and isinstance(value.get("record_id"), str)
    ):
        return {"record_type": "publication_surface", "record_id": str(value["record_id"])}
    return None


def _finite_checks(
    packet: Mapping[str, Any],
    question: Mapping[str, Any],
    ledger: Mapping[str, Any],
    observed_ids: list[str],
    check_ids: tuple[str, ...],
    binding: MethodConflictBinding,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    assertions = _mapping_list(packet.get("semantic_assertions"))
    answers = _mapping_list(packet.get("answers"))
    by_id = {str(item.get("assertion_id")): item for item in assertions}
    selected = [by_id[value] for value in observed_ids if value in by_id]
    # Assertion roles are a closed framework invariant, not an ordered pair.  The
    # binding serializes them canonically, so assigning meaning by tuple position
    # would make replay depend on sort order.
    reported_role = "reported"
    static_role = "observed"
    reported = [item for item in selected if item.get("semantic_role") == reported_role]
    static = [item for item in selected if item.get("semantic_role") == static_role]
    required_planes = set(binding.required_evidence_planes)
    requirement_refs = [
        ref
        for ref in ledger.get("assertion_refs", [])
        if isinstance(ref, Mapping)
        and str(ref.get("record_id", "")).startswith("assertion-verified-posthoc-intent:")
    ]
    requirement_ids = {str(ref["record_id"]) for ref in requirement_refs}
    requirements = [item for item in assertions if item.get("assertion_id") in requirement_ids]
    authority_ok = (
        len(requirements) == len(answers) == 1
        and requirements[0].get("extensions", {}).get("x-answer-ref")
        == {"record_type": "answer", "record_id": answers[0].get("answer_id")}
        and requirements[0].get("extensions", {}).get("x-answer-digest")
        == answers[0].get("answer_digest")
        and answers[0].get("respondent", {}).get("actor_kind") == "human"
        and answers[0].get("authority_scope", {}).get("subject_refs")
        == [ledger.get("analysis_subject_ref")]
        and answers[0].get("answer_value", {}).get(binding.dimension) == ledger.get("requirement")
    )
    same_subject_assertions = [
        item
        for item in assertions
        if item.get("subject_ref") == ledger.get("analysis_subject_ref")
        and item.get("epistemic_status") == "accepted"
    ]
    scope_digest = question.get("extensions", {}).get("x-scientific-check-scope-join-digest")
    check_id = question.get("extensions", {}).get("x-scientific-check-id")
    same_scope_assertions = [
        item
        for item in assertions
        if item.get("epistemic_status") == "accepted"
        and item.get("extensions", {}).get("x-scientific-check-id") == check_id
        and item.get("extensions", {}).get("x-scientific-check-scope-join-digest") == scope_digest
    ]
    extra_requirements = [
        item
        for item in same_subject_assertions
        if item.get("predicate") == f"verified_intended_{binding.dimension}"
        and item.get("assertion_id") not in requirement_ids
    ]
    extra_reported = [
        item
        for item in same_scope_assertions
        if item.get("semantic_role") == reported_role
        and item.get("assertion_id") not in observed_ids
    ]
    extra_static = [
        item
        for item in same_scope_assertions
        if item.get("semantic_role") == static_role and item.get("assertion_id") not in observed_ids
    ]
    scope_ok = _scope_graph_is_closed(packet, ledger)
    observed_authority = ledger.get("authority", {}).get("observed")
    expected_authority = {
        frozenset({"reported_text"}): "verified_reported_wording",
        frozenset({"static_source"}): "verified_static_source",
        frozenset({"reported_text", "static_source"}): ("corroborated_report_and_static_source"),
    }.get(frozenset(required_planes))
    selected_planes = {
        "reported_text" if item.get("semantic_role") == reported_role else "static_source"
        for item in selected
        if item.get("semantic_role") in {reported_role, static_role}
    }

    def predicate_matches(predicate: str) -> list[dict[str, Any]]:
        return [item for item in same_subject_assertions if item.get("predicate") == predicate]

    applicability_mismatch = [
        item
        for item in predicate_matches("method_obligation_applicability")
        if item.get("object") != "applies"
    ]
    qualifier_matches = [
        item
        for item in selected
        if item.get("extensions", {}).get("x-sensitivity-only") is True
        or bool(item.get("extensions", {}).get("x-unsupported-method-constructs"))
    ]
    signals: list[tuple[bool, str, list[dict[str, Any]], str]] = [
        (
            authority_ok,
            "One exact human Answer and its controller-verified requirement resolve.",
            [] if authority_ok else [*answers, *requirements],
            "The human Answer or controller-verified requirement is missing, duplicated, or mismatched.",
        ),
        (
            (
                len(reported) == 1 and not extra_reported
                if "reported_text" in required_planes
                else not reported
            ),
            (
                "Exactly one bound selected-report operand is present."
                if "reported_text" in required_planes
                else "The binding does not require a selected-report operand."
            ),
            extra_reported if "reported_text" in required_planes else reported,
            "The selected-report operand requirement is missing, ambiguous, or mismatched.",
        ),
        (
            (
                len(static) == 1 and not extra_static
                if "static_source" in required_planes
                else not static
            ),
            (
                "Exactly one bound static-source operand is present."
                if "static_source" in required_planes
                else "The binding does not require a static-source operand."
            ),
            extra_static if "static_source" in required_planes else static,
            "The static-source operand requirement is missing, ambiguous, or mismatched.",
        ),
        (
            selected_planes == required_planes and observed_authority == expected_authority,
            "Every binding-required evidence plane exposes one identical typed operand.",
            selected,
            "The binding-required evidence planes do not resolve to one typed operand.",
        ),
        (
            scope_ok,
            "The exact selected-output writer scope graph closes under full-digest identity.",
            [],
            "The exact selected-output writer scope graph is unavailable or inconsistent.",
        ),
        (
            not extra_requirements,
            "No alternate or superseding accepted requirement is present.",
            extra_requirements,
            "An alternate or superseding accepted requirement is present.",
        ),
        (
            not predicate_matches("governing_protocol_amendment"),
            "No accepted governing protocol amendment is present.",
            predicate_matches("governing_protocol_amendment"),
            "An accepted governing protocol amendment is present.",
        ),
        (
            not predicate_matches("approved_method_deviation"),
            "No accepted approved method deviation is present.",
            predicate_matches("approved_method_deviation"),
            "An accepted approved method deviation is present.",
        ),
        (
            not applicability_mismatch,
            "No accepted conditional-applicability mismatch is present.",
            applicability_mismatch,
            "An accepted conditional-applicability mismatch is present.",
        ),
        (
            not qualifier_matches,
            "No sensitivity-only or unsupported-method qualifier is present.",
            qualifier_matches,
            "A sensitivity-only or unsupported-method qualifier is present.",
        ),
    ]
    checks: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    suppressors: list[str] = []
    target_ref = ledger.get("analysis_subject_ref")
    for check_id, (passed, passed_note, matches, failed_note) in zip(
        check_ids, signals, strict=True
    ):
        evidence_id = f"evidence:{check_id.removeprefix('check:')}"
        source_refs = _deduplicated_sources(matches)
        record_refs = _record_refs(matches)
        if not record_refs and isinstance(target_ref, Mapping):
            record_refs = [deepcopy(dict(target_ref))]
        evidence.append(
            {
                "evidence_id": evidence_id,
                "description": passed_note if passed else failed_note,
                "support_role": "supports" if passed else "counterevidence",
                "source_refs": source_refs,
                "record_refs": record_refs,
                "observed_value": "passed" if passed else "suppressor_present",
            }
        )
        checks.append(
            {
                "check_id": check_id,
                "status": "completed",
                "outcome": "no_counterevidence" if passed else "counterevidence_found",
                "evidence_ids": [evidence_id],
                "notes": passed_note if passed else failed_note,
            }
        )
        if not passed:
            suppressors.append(failed_note)
    return checks, evidence, suppressors


def _scope_graph_is_closed(packet: Mapping[str, Any], ledger: Mapping[str, Any]) -> bool:
    path = ledger.get("scope_join_path")
    if not isinstance(path, list) or not path:
        return False
    if semantic_digest(path) != ledger.get("scope_join_digest"):
        return False
    if any(
        not isinstance(edge, Mapping)
        or _ref_id(edge.get("source_ref")) == ""
        or _ref_id(edge.get("target_ref")) == ""
        or not isinstance(edge.get("relation"), str)
        for edge in path
    ):
        return False
    if any(
        path[index].get("target_ref") != path[index + 1].get("source_ref")
        for index in range(len(path) - 1)
    ) or path[-1].get("target_ref") != ledger.get("analysis_subject_ref"):
        return False
    files = _records_by_id(packet.get("file_records"), "file_record_id")
    operations = _records_by_id(packet.get("operations"), "operation_id")
    artifacts = _records_by_id(packet.get("artifacts"), "artifact_id")
    surfaces = _records_by_id(packet.get("publication_surfaces"), "publication_surface_id")
    identities = _records_by_id(packet.get("asset_identities"), "asset_identity_id")
    return all(
        _scope_edge_is_closed(edge, files, operations, artifacts, surfaces, identities)
        for edge in path
    )


def _scope_edge_is_closed(
    edge: Mapping[str, Any],
    files: Mapping[str, Mapping[str, Any]],
    operations: Mapping[str, Mapping[str, Any]],
    artifacts: Mapping[str, Mapping[str, Any]],
    surfaces: Mapping[str, Mapping[str, Any]],
    identities: Mapping[str, Mapping[str, Any]],
) -> bool:
    source_ref = edge.get("source_ref")
    target_ref = edge.get("target_ref")
    relation = edge.get("relation")
    if relation == "contains_unique_static_selected_output_writer":
        source_file = files.get(_ref_id(source_ref))
        operation = operations.get(_ref_id(target_ref))
        if source_file is None or operation is None:
            return False
        implementation = operation.get("implementation")
        implementation_name = (
            implementation.get("name") if isinstance(implementation, Mapping) else implementation
        )
        return bool(
            _has_full_identity(source_ref, source_file, identities)
            and source_file.get("entry_kind") == "regular_file"
            and operation.get("inspection_status") == "supported"
            and isinstance(implementation_name, str)
            and implementation_name.endswith((".write_text", ".write_bytes"))
        )
    if relation == "declares_selected_output_artifact":
        operation = operations.get(_ref_id(source_ref))
        artifact = artifacts.get(_ref_id(target_ref))
        return bool(
            operation is not None
            and artifact is not None
            and operation.get("output_refs") == [target_ref]
            and artifact.get("producer_operation_refs") == [source_ref]
            and _has_full_identity(target_ref, artifact, identities)
        )
    if relation in {
        "selected_by_publication_surface",
        "selected_source_artifact_of_publication_surface",
    }:
        artifact = artifacts.get(_ref_id(source_ref))
        surface = surfaces.get(_ref_id(target_ref))
        return bool(
            artifact is not None
            and surface is not None
            and _has_full_identity(source_ref, artifact, identities)
            and surface.get("status") == "resolved"
            and surface.get("selection", {}).get("selected_surface_refs") == [source_ref]
        )
    return False


def _has_full_identity(
    asset_ref: object,
    asset: Mapping[str, Any],
    identities: Mapping[str, Mapping[str, Any]],
) -> bool:
    identity = identities.get(_ref_id(asset.get("asset_identity_ref")))
    return bool(
        identity is not None
        and identity.get("tier") == "full_digest"
        and identity.get("asset_ref") == asset_ref
    )


def _plane_description(binding: MethodConflictBinding) -> str:
    labels = {
        "reported_text": "selected-report",
        "static_source": "exact-scope static-source",
    }
    return " and ".join(labels[value] for value in binding.required_evidence_planes)


def _ref_id(value: object) -> str:
    return str(value.get("record_id", "")) if isinstance(value, Mapping) else ""


def _records_by_id(value: object, id_field: str) -> dict[str, dict[str, Any]]:
    return {
        str(item[id_field]): item
        for item in _mapping_list(value)
        if isinstance(item.get(id_field), str)
    }


def _mapping_records(locked_case: Mapping[str, Any], field: str) -> list[dict[str, Any]]:
    return [deepcopy(item) for item in _mapping_list(locked_case.get(field))]


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _contract_assertion_ids(contracts: Sequence[Mapping[str, Any]]) -> set[str]:
    values: set[str] = set()
    for contract in contracts:
        dimensions = contract.get("dimensions")
        if not isinstance(dimensions, Mapping):
            continue
        for slot in dimensions.values():
            if not isinstance(slot, Mapping):
                continue
            for field in ("assertion_ids", "accepted_assertion_ids"):
                identities = slot.get(field)
                if isinstance(identities, Sequence) and not isinstance(identities, (str, bytes)):
                    values.update(str(value) for value in identities)
    return values


def _premise(
    premise_id: str,
    description: str,
    state: str,
    material: bool,
    evidence_ids: list[str],
) -> dict[str, Any]:
    return {
        "premise_id": premise_id,
        "statement": description,
        "state": state,
        "material": material,
        "evidence_ids": evidence_ids,
    }


def _record_refs(records: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    refs: dict[str, dict[str, str]] = {}
    for record in records:
        for record_type, field in (
            ("answer", "answer_id"),
            ("semantic_assertion", "assertion_id"),
            ("scientific_contract", "contract_id"),
            ("publication_surface", "publication_surface_id"),
            ("file_record", "file_record_id"),
            ("operation", "operation_id"),
            ("artifact", "artifact_id"),
        ):
            value = record.get(field)
            if isinstance(value, str):
                ref = {"record_type": record_type, "record_id": value}
                refs[canonical_json(ref)] = ref
                break
    return [refs[key] for key in sorted(refs)]


def _deduplicated_sources(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    refs: dict[str, dict[str, Any]] = {}
    for record in records:
        values = record.get("source_refs")
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            continue
        for value in values:
            if isinstance(value, Mapping):
                ref = deepcopy(dict(value))
                refs[canonical_json(ref)] = ref
    return [refs[key] for key in sorted(refs)]


def _unavailable_checks(check_ids: tuple[str, ...], reason: str) -> list[dict[str, Any]]:
    return [
        {
            "check_id": check_id,
            "status": "unavailable",
            "outcome": "inconclusive",
            "evidence_ids": [],
            "notes": reason,
        }
        for check_id in check_ids
    ]
