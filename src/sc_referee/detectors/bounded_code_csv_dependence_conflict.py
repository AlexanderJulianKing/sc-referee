from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.detectors import bounded_analysis_method_conflict as legacy
from sc_referee.posthoc_method_ledger import (
    PosthocMethodLedgerError,
    project_analysis_posthoc_method_ledger,
)
from sc_referee.review_case import ReviewCase, review_gates_from_counterevidence
from sc_referee.scientific_checks.core import MethodConflictBinding
from sc_referee.version import SCHEMA_VERSION, __version__


class BoundedCodeCsvDependenceConflictDetector(legacy.BoundedAnalysisMethodConflictDetector):
    """Evaluate the exact reportless code/CSV dependence contract conflict."""

    detector_id = "detector:bounded-code-csv-dependence-conflict"
    detector_version = "1.0.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_dependence_conflict:"
        "BoundedCodeCsvDependenceConflictDetector"
    )
    maturity = "experimental"

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())

    def evaluate(
        self, locked_case: Mapping[str, Any], question: Mapping[str, Any]
    ) -> dict[str, Any]:
        packet = self._work_packet(locked_case, question)
        input_digest = semantic_digest(packet)
        subject_ref = _analysis_subject(question, self.bindings_by_check)
        target_ref = subject_ref or {
            "record_type": "file_record",
            "record_id": "file:unknown",
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
                "method": "deterministic_bounded_code_csv_dependence_conflict_evaluation",
                "created_at": str(locked_case["locked_at"]),
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "extensions": {
                "x-evaluation-only": True,
                "x-production-finding-permitted": False,
                "x-detector-profile": "bounded_code_csv_dependence_conflict_v1",
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
        target_problem = legacy._target_problem(question, subject_ref, binding)
        if target_problem is not None:
            return self._terminal(
                base,
                state="unsupported_path",
                applicability="not_applicable",
                basis=target_problem,
                unsupported=[target_problem],
                premises=[],
                evidence=[],
                checks=legacy._unavailable_checks(self.check_ids, target_problem),
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
                    legacy._premise(
                        "premise:one-analysis-contract",
                        "One exact analysis-scoped ScientificContract resolves.",
                        "unknown",
                        True,
                        [],
                    )
                ],
                evidence=[],
                checks=legacy._unavailable_checks(self.check_ids, problem),
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
                    legacy._premise(
                        "premise:closed-analysis-method-ledger",
                        "The closed analysis-scoped method ledger replays exactly.",
                        "unknown",
                        True,
                        [],
                    )
                ],
                evidence=[],
                checks=legacy._unavailable_checks(self.check_ids, problem),
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
        applicability_gates, counterevidence_gates = review_gates_from_counterevidence(checks)
        review_case = ReviewCase(
            case_family="analysis_method_requirement_consistency",
            case_version="1.0.0",
            target_ref=deepcopy(subject_ref),
            requirement=deepcopy(ledger.get("requirement")),
            observed_operand=deepcopy(ledger.get("observed")),
            comparison_form=comparison_form,
            analysis_binding={
                "binding_id": binding.binding_id,
                "contract_id": str(contracts[0]["contract_id"]),
                "scientific_check_id": binding.check_id,
                "scope_join_path": deepcopy(list(scope_path)),
                "scope_join_digest": scope_digest,
            },
            evidence_planes=tuple(binding.required_evidence_planes),
            applicability_gates=applicability_gates,
            counterevidence_gates=counterevidence_gates,
            affected_descendant_refs=(),
            unresolved_dimensions=(str(dimension),) if suppressors else (),
            unsupported_constructs=(),
            output_ceiling="evaluation_candidate",
        )
        review_case_extensions = {
            "x-posthoc-method-ledger-digest": ledger["ledger_digest"],
            "x-review-case-profile": "analysis_method_requirement_consistency:1.0.0",
            "x-review-case-digest": review_case.review_case_digest,
        }
        ledger_evidence = {
            "evidence_id": "evidence:analysis-method-ledger",
            "description": (
                "The controller-recomputed ledger compares one exact human review requirement "
                f"with the binding-required {legacy._plane_description(binding)} operand(s)."
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
            legacy._premise(
                "premise:verified-analysis-requirement",
                "One scope-bound human Answer supplies the governing requirement for this review.",
                "established" if not suppressors else "unknown",
                True,
                ["evidence:analysis-requirement-authority"],
            ),
            legacy._premise(
                "premise:corroborated-report-and-source-operand",
                f"The binding-required {legacy._plane_description(binding)} evidence exposes one "
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
            legacy._premise(
                "premise:finite-analysis-counterevidence-absent",
                "All ten closed checks completed without a suppressor.",
                "established" if not suppressors else "refuted",
                True,
                [item["evidence_id"] for item in check_evidence],
            ),
        ]
        outcome = str(ledger.get("outcome"))
        premises.append(
            legacy._premise(
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
                extra_extensions=review_case_extensions,
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
                extra_extensions=review_case_extensions,
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
                extra_extensions=review_case_extensions,
            )

        candidate = {
            "assessment_type": "finding",
            "title": "Selected code fact conflicts with the review requirement",
            "bounded_statement": (
                f"For this selected analysis, the binding-required "
                f"{legacy._plane_description(binding)} evidence establishes "
                f"{ledger['observed']!r}, while the scope-bound scientist Answer requires "
                f"{ledger['requirement']!r}. Those exact operands differ. This does not "
                "establish that the source ran, that the difference caused a numerical error, "
                "or that the required operand is universally correct."
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
            extra_extensions=review_case_extensions,
        )


def _analysis_subject(
    question: Mapping[str, Any],
    bindings_by_check: Mapping[str, MethodConflictBinding],
) -> dict[str, str] | None:
    extensions = question.get("extensions")
    value = extensions.get("x-analysis-subject-ref") if isinstance(extensions, Mapping) else None
    check_id = (
        str(extensions.get("x-scientific-check-id", "")) if isinstance(extensions, Mapping) else ""
    )
    binding = bindings_by_check.get(check_id)
    if (
        isinstance(value, Mapping)
        and value.get("record_type") == "file_record"
        and isinstance(value.get("record_id"), str)
        and binding is not None
        and binding.required_evidence_planes == ("static_source",)
    ):
        return {"record_type": "file_record", "record_id": str(value["record_id"])}
    return None


def _finite_checks(
    packet: Mapping[str, Any],
    question: Mapping[str, Any],
    ledger: Mapping[str, Any],
    observed_ids: list[str],
    check_ids: tuple[str, ...],
    binding: MethodConflictBinding,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    checks, evidence, suppressors = legacy._finite_checks(
        packet, question, ledger, observed_ids, check_ids, binding
    )
    if not _scope_graph_is_closed(packet, ledger):
        return checks, evidence, suppressors
    failed_note = "The exact selected-output writer scope graph is unavailable or inconsistent."
    passed_note = "The exact full-digest analysis.py-to-snapshot scope graph closes."
    check_id = "check:selected-output-scope-closure"
    for check in checks:
        if check.get("check_id") == check_id:
            check.update(
                {
                    "outcome": "no_counterevidence",
                    "notes": passed_note,
                }
            )
    evidence_id = "evidence:selected-output-scope-closure"
    for item in evidence:
        if item.get("evidence_id") == evidence_id:
            item.update(
                {
                    "description": passed_note,
                    "support_role": "supports",
                    "observed_value": "passed",
                }
            )
    removed = False
    corrected: list[str] = []
    for suppressor in suppressors:
        if suppressor == failed_note and not removed:
            removed = True
        else:
            corrected.append(suppressor)
    return checks, evidence, corrected


def _scope_graph_is_closed(packet: Mapping[str, Any], ledger: Mapping[str, Any]) -> bool:
    path = ledger.get("scope_join_path")
    if not isinstance(path, list) or len(path) != 1:
        return False
    if semantic_digest(path) != ledger.get("scope_join_digest"):
        return False
    edge = path[0]
    if not isinstance(edge, Mapping) or edge.get("relation") != "has_full_digest_in_snapshot":
        return False
    source_ref = edge.get("source_ref")
    target_ref = edge.get("target_ref")
    if ledger.get("analysis_subject_ref") != source_ref:
        return False
    files = legacy._records_by_id(packet.get("file_records"), "file_record_id")
    identities = legacy._records_by_id(packet.get("asset_identities"), "asset_identity_id")
    source_file = files.get(legacy._ref_id(source_ref))
    return bool(
        source_file is not None
        and source_file.get("entry_kind") == "regular_file"
        and source_file.get("snapshot_ref") == target_ref
        and isinstance(target_ref, Mapping)
        and target_ref.get("record_type") == "repository_snapshot"
        and legacy._has_full_identity(source_ref, source_file, identities)
    )
