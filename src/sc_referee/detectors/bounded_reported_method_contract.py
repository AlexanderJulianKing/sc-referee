from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.method_contracts import (
    EXPECTED_COUNT_PROFILE_ID,
    EXPECTED_COUNT_PROFILE_MANIFEST,
    EXPECTED_COUNT_PROFILE_VERSION,
    EXPECTED_COUNT_REQUIRED_DIMENSIONS,
    MethodContractError,
    profiles_conflict,
    project_expected_count_ledger,
)
from sc_referee.version import SCHEMA_VERSION, __version__


class BoundedMethodContractDetectorError(ValueError):
    """Raised when the detector manifest does not bind this implementation exactly."""


class BoundedReportedMethodContractConflictDetector:
    """Compare one closed reported method profile with one verified governing profile."""

    detector_id = "detector:bounded-reported-method-contract-conflict"
    detector_version = "0.1.0"
    entry_point = (
        "sc_referee.detectors.bounded_reported_method_contract:"
        "BoundedReportedMethodContractConflictDetector"
    )
    maturity = "experimental"
    check_ids = (
        "check:alternate-or-superseding-intent",
        "check:conflicting-reported-method",
        "check:sensitivity-only-qualifier",
        "check:protocol-amendment",
        "check:approved-deviation",
        "check:conditional-applicability",
        "check:claim-method-scope",
        "check:unsupported-method-construct",
    )

    def __init__(self, manifest: Mapping[str, Any]) -> None:
        self.manifest = deepcopy(dict(manifest))
        self._validate_manifest()
        self.manifest_digest = semantic_digest(self.manifest)

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())

    def evaluate(self, locked_case: Mapping[str, Any], claim: Mapping[str, Any]) -> dict[str, Any]:
        packet = self._work_packet(locked_case, claim)
        input_digest = semantic_digest(packet)
        claim_id = str(claim.get("claim_id", "unknown"))
        base = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "detector_result",
            "result_id": stable_id(
                "detector-result",
                self.detector_id,
                self.detector_version,
                claim_id,
                input_digest,
            ),
            "audit_run_id": str(locked_case["audit_run_id"]),
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "detector_manifest_digest": self.manifest_digest,
            "detector_maturity": self.maturity,
            "target_refs": [{"record_type": "claim", "record_id": claim_id}],
            "evaluated_at": str(locked_case["locked_at"]),
            "runtime_mode": "static",
            "deterministic_input_digest": input_digest,
            "provenance": {
                "actor": {"actor_kind": "detector", "actor_id": self.detector_id},
                "method": "deterministic_bounded_reported_method_contract_comparison",
                "created_at": str(locked_case["locked_at"]),
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "extensions": {
                "x-evaluation-only": True,
                "x-production-finding-permitted": False,
                "x-detector-profile": "bounded_reported_method_contract_conflict_v1",
                "x-method-profile-id": EXPECTED_COUNT_PROFILE_ID,
                "x-method-profile-version": EXPECTED_COUNT_PROFILE_VERSION,
                "x-profile-manifest-digest": semantic_digest(EXPECTED_COUNT_PROFILE_MANIFEST),
            },
        }
        problem = _claim_problem(claim)
        if problem is not None:
            return self._terminal(
                base,
                state="unsupported_path",
                applicability="not_applicable",
                basis=problem,
                unsupported=[problem],
                premises=[],
                evidence=[],
                checks=_unavailable_checks(self.check_ids, problem),
                gaps=[problem],
            )

        contracts = packet["scientific_contracts"]
        if len(contracts) != 1:
            problem = "The Claim does not resolve to one exact ScientificContract."
            return self._terminal(
                base,
                state="insufficient_semantics",
                applicability="uncertain",
                basis=problem,
                unsupported=[],
                premises=[
                    _premise(
                        "premise:one-scoped-method-contract",
                        "One Claim-scoped expected-count ScientificContract resolves.",
                        "unknown",
                        True,
                        [],
                    )
                ],
                evidence=[],
                checks=_unavailable_checks(self.check_ids, problem),
                gaps=[problem],
            )
        contract = contracts[0]
        assertions = packet["semantic_assertions"]
        checks, check_evidence, counterevidence = _finite_counterevidence(
            claim, contract, assertions
        )
        if counterevidence:
            basis = (
                "At least one finite counterevidence or scope check prevents an exact, "
                "unambiguous method-contract comparison."
            )
            return self._terminal(
                base,
                state="insufficient_semantics",
                applicability="uncertain",
                basis=basis,
                unsupported=[],
                premises=[
                    _premise(
                        "premise:finite-method-counterevidence-absent",
                        "All eight closed counterevidence checks complete without a suppressor.",
                        "refuted",
                        True,
                        [item["evidence_id"] for item in check_evidence],
                    )
                ],
                evidence=check_evidence,
                checks=checks,
                gaps=counterevidence,
            )
        try:
            ledger = project_expected_count_ledger(
                claim_id=str(claim["claim_id"]),
                contract=contract,
                assertions=assertions,
            )
        except MethodContractError as error:
            problem = f"The closed expected-count ledger is incomplete: {error}"
            return self._terminal(
                base,
                state="insufficient_semantics",
                applicability="uncertain",
                basis=problem,
                unsupported=[],
                premises=[
                    _premise(
                        "premise:complete-method-ledger",
                        "One complete controller-recomputed intended/reported method ledger exists.",
                        "unknown",
                        True,
                        [],
                    )
                ],
                evidence=check_evidence,
                checks=checks,
                gaps=[problem],
            )

        intended = ledger["intended_profile"]
        reported = ledger["reported_profile"]
        ledger_evidence = [
            {
                "evidence_id": "evidence:intended-method-profile",
                "description": (
                    "Six separately controller-verified intended assertions reconstruct one "
                    "closed governing expected-count profile."
                ),
                "support_role": "supports",
                "source_refs": deepcopy(ledger["source_refs"]),
                "record_refs": [
                    {"record_type": "scientific_contract", "record_id": ledger["contract_id"]},
                    *[
                        {"record_type": "semantic_assertion", "record_id": assertion_id}
                        for assertion_id in ledger["intended_assertion_ids"]
                    ],
                ],
                "observed_value": intended,
            },
            {
                "evidence_id": "evidence:reported-method-profile",
                "description": (
                    "One exact selected-report grammar reconstructs one closed reported "
                    "expected-count profile."
                ),
                "support_role": "supports",
                "source_refs": deepcopy(ledger["source_refs"]),
                "record_refs": [
                    {
                        "record_type": "semantic_assertion",
                        "record_id": ledger["reported_assertion_id"],
                    }
                ],
                "observed_value": reported,
            },
            {
                "evidence_id": "evidence:exact-method-profile-comparison",
                "description": (
                    "The detector compared the two complete profiles field for field under the "
                    "same profile version."
                ),
                "support_role": "supports",
                "source_refs": deepcopy(ledger["source_refs"]),
                "record_refs": [{"record_type": "claim", "record_id": str(claim["claim_id"])}],
                "observed_value": {
                    "profiles_equal": not profiles_conflict(ledger),
                    "ledger_digest": ledger["ledger_digest"],
                },
            },
        ]
        evidence = [*check_evidence, *ledger_evidence]
        premises = [
            _premise(
                "premise:verified-governing-method-profile",
                "A scope-bound human Answer was separately verified into one complete governing profile.",
                "established",
                True,
                ["evidence:intended-method-profile"],
            ),
            _premise(
                "premise:verified-reported-method-profile",
                "One unambiguous selected-report method statement yields one complete reported profile.",
                "established",
                True,
                ["evidence:reported-method-profile"],
            ),
            _premise(
                "premise:finite-method-counterevidence-absent",
                "All eight closed counterevidence checks completed without a suppressor.",
                "established",
                True,
                [item["evidence_id"] for item in check_evidence],
            ),
        ]
        conflict = profiles_conflict(ledger)
        premises.append(
            _premise(
                "premise:exact-method-profile-conflict",
                "The complete intended and reported expected-count profiles differ exactly.",
                "established" if conflict else "refuted",
                True,
                ["evidence:exact-method-profile-comparison"],
            )
        )
        basis = (
            "One complete closed intended profile and one complete closed reported profile were "
            "recomputed under the same version, and all finite checks completed."
        )
        extra = {"x-method-ledger-digest": ledger["ledger_digest"]}
        if not conflict:
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
                extra_extensions=extra,
            )
        candidate = {
            "assessment_type": "finding",
            "title": "Reported expected-count method conflicts with the declared obligation",
            "bounded_statement": (
                "For this Claim, the selected report states the "
                f"{reported['estimator_family']} expected-count profile, while the separately "
                "verified governing declaration specifies the "
                f"{intended['estimator_family']} profile. The closed profiles differ exactly; "
                "this does not establish which code ran, why any numeric result differs, or that "
                "the declared profile is universally correct."
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
            extra_extensions=extra,
        )

    def _work_packet(
        self, locked_case: Mapping[str, Any], claim: Mapping[str, Any]
    ) -> dict[str, Any]:
        claim_id = str(claim.get("claim_id", ""))
        contract_id = str(claim.get("scientific_contract_id", ""))
        contracts = [
            deepcopy(item)
            for item in locked_case.get("scientific_contracts", [])
            if isinstance(item, Mapping) and str(item.get("contract_id")) == contract_id
        ]
        assertion_ids = _contract_assertion_ids(contracts)
        assertions = [
            deepcopy(item)
            for item in locked_case.get("semantic_assertions", [])
            if isinstance(item, Mapping)
            and (
                _ref_equals(item.get("subject_ref"), "claim", claim_id)
                or str(item.get("assertion_id")) in assertion_ids
            )
        ]
        return {
            "profile": "bounded_reported_method_contract_work_packet_v1",
            "audit_run_id": str(locked_case["audit_run_id"]),
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "detector_manifest_digest": self.manifest_digest,
            "target_claim": deepcopy(dict(claim)),
            "scientific_contracts": contracts,
            "semantic_assertions": assertions,
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
                raise BoundedMethodContractDetectorError(
                    f"bounded method-contract detector manifest has invalid {key}"
                )
        implementation = self.manifest.get("implementation")
        if not isinstance(implementation, Mapping):
            raise BoundedMethodContractDetectorError(
                "method-contract detector manifest lacks implementation identity"
            )
        if implementation.get("entry_point") != self.entry_point:
            raise BoundedMethodContractDetectorError("detector manifest entry point mismatch")
        if implementation.get("deterministic") is not True:
            raise BoundedMethodContractDetectorError("detector must be deterministic")
        if implementation.get("implementation_digest") != self.implementation_digest():
            raise BoundedMethodContractDetectorError("detector implementation digest mismatch")
        declared_checks = tuple(
            str(item.get("check_id"))
            for item in self.manifest.get("counterevidence_protocol", [])
            if isinstance(item, Mapping)
        )
        if declared_checks != self.check_ids:
            raise BoundedMethodContractDetectorError("detector counterevidence protocol mismatch")
        outputs = self.manifest.get("permitted_output_types")
        if not isinstance(outputs, list) or "finding" in outputs:
            raise BoundedMethodContractDetectorError(
                "experimental detector manifest cannot permit Findings"
            )


def _claim_problem(claim: Mapping[str, Any]) -> str | None:
    extraction = claim.get("extraction")
    extensions = claim.get("extensions")
    if (
        claim.get("record_type") != "claim"
        or claim.get("claim_status") != "final"
        or claim.get("claim_kind") != "quantitative"
        or not isinstance(extraction, Mapping)
        or extraction.get("method") != "deterministic"
        or extraction.get("explicit_source_meaning") is not True
        or extraction.get("independently_verified") is not True
        or not isinstance(extensions, Mapping)
        or extensions.get("x-method-profile-id") != EXPECTED_COUNT_PROFILE_ID
    ):
        return "The target is outside the exact expected-count quantitative Claim profile."
    return None


def _finite_counterevidence(
    claim: Mapping[str, Any],
    contract: Mapping[str, Any],
    assertions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    claim_id = str(claim.get("claim_id"))
    dimensions = contract.get("dimensions")
    selected_ids: set[str] = set()
    if isinstance(dimensions, Mapping):
        for dimension in EXPECTED_COUNT_REQUIRED_DIMENSIONS:
            slot = dimensions.get(dimension)
            if isinstance(slot, Mapping):
                accepted = slot.get("accepted_assertion_ids")
                if isinstance(accepted, Sequence) and not isinstance(accepted, (str, bytes)):
                    selected_ids.update(str(value) for value in accepted)
    intended = [
        item
        for item in assertions
        if str(item.get("predicate", "")).startswith("verified_intended_")
        and item.get("epistemic_status") == "accepted"
    ]
    reports = [
        item
        for item in assertions
        if item.get("predicate") == "reported_expected_count_background_profile"
        and item.get("epistemic_status") == "accepted"
    ]
    signals: list[tuple[str, list[dict[str, Any]], str]] = [
        (
            "alternate or superseding intended profile",
            [
                item
                for item in assertions
                if (
                    item.get("predicate") == "superseding_expected_count_background_profile"
                    or (
                        str(item.get("predicate", "")).startswith("verified_intended_")
                        and str(item.get("assertion_id")) not in selected_ids
                    )
                )
                and item.get("epistemic_status") == "accepted"
            ],
            "No alternate or superseding accepted intended profile is present.",
        ),
        (
            "conflicting reported method statement",
            reports if len(reports) > 1 else [],
            "Exactly one accepted reported method statement is present or the ledger remains unresolved.",
        ),
        (
            "sensitivity-only method qualifier",
            [
                item
                for item in reports
                if item.get("extensions", {}).get("x-sensitivity-only") is True
            ],
            "The primary reported method assertion is not marked sensitivity-only.",
        ),
        (
            "governing protocol amendment",
            _predicate_assertions(assertions, "governing_protocol_amendment"),
            "No accepted governing protocol amendment is present.",
        ),
        (
            "approved method deviation",
            _predicate_assertions(assertions, "approved_method_deviation"),
            "No accepted approved method deviation is present.",
        ),
        (
            "conditional applicability mismatch",
            [
                item
                for item in _predicate_assertions(assertions, "method_obligation_applicability")
                if item.get("object") != "applies"
            ],
            "No accepted conditional-applicability mismatch is present.",
        ),
        (
            "Claim-to-method scope mismatch",
            [
                item
                for item in [*intended, *reports]
                if not _ref_equals(item.get("subject_ref"), "claim", claim_id)
            ]
            + (
                [{"record_type": "scientific_contract", "contract_id": contract.get("contract_id")}]
                if not _contract_matches_claim(contract, claim_id)
                else []
            ),
            "The contract and all method assertions have the exact target Claim scope.",
        ),
        (
            "unsupported method construct",
            [dict(item) for item in [claim, *reports] if _unsupported_constructs(item)],
            "No target record declares an unsupported method construct.",
        ),
    ]
    checks: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    reasons: list[str] = []
    fallback_sources = _source_refs(claim)
    for check_id, (label, matches, negative_note) in zip(
        BoundedReportedMethodContractConflictDetector.check_ids, signals, strict=True
    ):
        evidence_id = f"evidence:{check_id.removeprefix('check:')}"
        found = bool(matches)
        refs = _record_refs(matches) or [{"record_type": "claim", "record_id": claim_id}]
        sources = _matching_sources(matches) or fallback_sources
        evidence.append(
            {
                "evidence_id": evidence_id,
                "description": (
                    f"The locked target records were searched for {label}; "
                    + ("a suppressing record was found." if found else negative_note)
                ),
                "support_role": "counterevidence" if found else "supports",
                "source_refs": sources,
                "record_refs": refs,
                "observed_value": (
                    [str(item.get("assertion_id") or item.get("contract_id")) for item in matches]
                    if found
                    else "none_found"
                ),
            }
        )
        checks.append(
            {
                "check_id": check_id,
                "status": "completed",
                "outcome": "counterevidence_found" if found else "no_counterevidence",
                "evidence_ids": [evidence_id],
                "notes": f"Suppressor found: {label}." if found else negative_note,
            }
        )
        if found:
            reasons.append(f"Finite check found {label}.")
    return checks, evidence, reasons


def _predicate_assertions(
    assertions: Sequence[Mapping[str, Any]], predicate: str
) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in assertions
        if item.get("predicate") == predicate and item.get("epistemic_status") == "accepted"
    ]


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


def _contract_matches_claim(contract: Mapping[str, Any], claim_id: str) -> bool:
    scope = contract.get("scope")
    if not isinstance(scope, Mapping) or scope.get("level") != "claim":
        return False
    subjects = scope.get("subject_refs")
    return (
        isinstance(subjects, Sequence)
        and not isinstance(subjects, (str, bytes))
        and subjects == [{"record_type": "claim", "record_id": claim_id}]
    )


def _unsupported_constructs(record: Mapping[str, Any]) -> bool:
    extensions = record.get("extensions")
    return (
        isinstance(extensions, Mapping)
        and isinstance(extensions.get("x-unsupported-method-constructs"), list)
        and bool(extensions["x-unsupported-method-constructs"])
    )


def _record_refs(records: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for record in records:
        for record_type, key in (
            ("semantic_assertion", "assertion_id"),
            ("scientific_contract", "contract_id"),
            ("claim", "claim_id"),
        ):
            value = record.get(key)
            if isinstance(value, str):
                refs.append({"record_type": record_type, "record_id": value})
                break
    return refs


def _matching_sources(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_digest: dict[str, dict[str, Any]] = {}
    for record in records:
        for ref in _source_refs(record):
            by_digest[semantic_digest(ref)] = ref
    return [by_digest[key] for key in sorted(by_digest)]


def _source_refs(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    values = record.get("source_refs")
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    return [deepcopy(dict(value)) for value in values if isinstance(value, Mapping)]


def _ref_equals(value: object, record_type: str, record_id: str) -> bool:
    return (
        isinstance(value, Mapping)
        and value.get("record_type") == record_type
        and value.get("record_id") == record_id
    )


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


def _premise(
    premise_id: str,
    statement: str,
    state: str,
    material: bool,
    evidence_ids: list[str],
) -> dict[str, Any]:
    return {
        "premise_id": premise_id,
        "statement": statement,
        "state": state,
        "material": material,
        "evidence_ids": evidence_ids,
    }
