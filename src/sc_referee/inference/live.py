"""Conservative live audit adapters for declarative policies.

The optional folder file is an *input-routing manifest*, never an evidence manifest.  In
particular, scientific relations, accusation authority, ratification declarations, and observed
digests in that file are deliberately ignored.  Live evidence is derived from parsed source and
verifier-measured artifacts only.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.inference.api import ANALYZER_DIGEST
from sc_referee.inference.double_dipping import (
    DOUBLE_DIPPING_PREMISES,
    compute_double_dipping_evidence,
)
from sc_referee.inference.policy.evaluate import PolicySnapshot, evaluate
from sc_referee.inference.policy.schema import ValidityPolicy, canonical_policy_json
from sc_referee.inference.contracts.schema import SummaryBinding
from sc_referee.inference.proof.certificate import (
    Certificate,
    ClaimRootBinding,
    ClaimRootGrade as CertificateRootGrade,
    external_status,
)
from sc_referee.inference.proof.discharge import builtin_registry


@dataclass(frozen=True)
class ExactArtifactBinding:
    logical_role: str
    format: str
    schema_digest: str
    content_digest: str
    writer_version: str
    serializer_contract: str
    path_resolved: bool
    unique_writer: bool
    field_correspondence: bool
    no_later_mutation: bool

    @property
    def exact(self) -> bool:
        return all((self.logical_role, self.format, self.schema_digest, self.content_digest,
                    self.writer_version, self.serializer_contract, self.path_resolved,
                    self.unique_writer, self.field_correspondence, self.no_later_mutation))


@dataclass(frozen=True)
class LivePolicyContract:
    """Untrusted routing input admitted from ``sc-referee.inference.json``.

    Proposed facts are intentionally inert here.  A future fact integration may admit an item only
    after matching a code-owned fact kind and the existing ``design.confirmed_by_human`` gate.  No
    field in this type can express a proved relation, a claim-root grade, or an observation.
    """

    policy_id: str
    sources: tuple[str, ...]
    routing: Mapping[str, object]
    proposed_facts: tuple[Mapping[str, object], ...]

    def __post_init__(self):
        object.__setattr__(self, "routing", MappingProxyType(dict(self.routing)))
        object.__setattr__(self, "proposed_facts", tuple(
            MappingProxyType(dict(item)) for item in self.proposed_facts
        ))


@dataclass(frozen=True)
class VerifierObservation:
    """Artifact measurements made by the verifier, never deserialized from folder JSON."""

    report_artifact_digest: str | None
    report_locator_digest: str | None
    report_relative_path: str | None
    data_relative_path: str | None


_POLICY_MODULES = {
    "double_dipping.v1": "double_dipping",
    "confounding.v2": "confounding",
    "pseudoreplication.v1": "pseudoreplication",
    "allele_harmonization.v1": "allele_harmonization",
    "enrichment_universe.v1": "enrichment_universe",
    "coordinate_consumption.v1": "coordinate_consumption",
    "spatial_iid.v1": "spatial_iid",
    "trajectory_circularity.v1": "trajectory_circularity",
}
_ANALYSIS_TYPES = {
    "double_dipping.v1": ("marker_detection", "condition_contrast_DE"),
    "confounding.v2": ("condition_contrast_DE",),
    "pseudoreplication.v1": ("condition_contrast_DE",),
    "allele_harmonization.v1": ("eqtl",),
    "enrichment_universe.v1": ("differential_abundance",),
    "coordinate_consumption.v1": ("other",),
    "spatial_iid.v1": ("condition_contrast_DE",),
    "trajectory_circularity.v1": ("trajectory",),
}
_DIMENSIONS = {
    "double_dipping.v1": ("selection",),
    "confounding.v2": ("conditioning_set",),
    "pseudoreplication.v1": ("unit_of_independence",),
    "allele_harmonization.v1": ("orientation",),
    "enrichment_universe.v1": ("inclusion_set",),
    "coordinate_consumption.v1": ("inclusion_set",),
    "spatial_iid.v1": ("unit_of_independence",),
    "trajectory_circularity.v1": ("selection",),
}
_CITATIONS = {
    "double_dipping.v1": ("Chen & Witten 2023, JMLR 24:1",),
    "confounding.v2": ("Leek et al. 2010, Nat Rev Genet 11:733",),
    "pseudoreplication.v1": ("Lazic et al. 2018, PLoS Biol 16:e2005282",),
    "allele_harmonization.v1": ("Hartwig et al. 2016, Int J Epidemiol 45:1717",),
    "enrichment_universe.v1": ("Fisher 1935, The Design of Experiments",),
    "coordinate_consumption.v1": ("GA4GH Variation Representation Specification",),
    "spatial_iid.v1": ("Lazic et al. 2018, PLoS Biol 16:e2005282",),
    "trajectory_circularity.v1": ("Chen & Witten 2023, JMLR 24:1",),
}


def trusted_live_summary_binding(policy_id: str) -> SummaryBinding:
    """Code-owned exact identity for the live adapter contract of one policy version."""
    if policy_id not in _POLICY_MODULES:
        raise KeyError(policy_id)
    summary_payload = canonical_policy_json(_policy(policy_id)) + "|increment-9-live-adapter-v1"
    return SummaryBinding(
        "sc_referee.inference.live", policy_id, "1", ANALYZER_DIGEST,
        _sha256_bytes(summary_payload.encode()),
    )


def _policy(policy_id: str) -> ValidityPolicy:
    module = __import__(
        f"sc_referee.inference.policy.definitions.{_POLICY_MODULES[policy_id]}",
        fromlist=["POLICY"],
    )
    return module.POLICY


class EnginePolicyVerifier:
    proof_basis = "inference engine: parse-only computed facts"
    contract_fields = ("analysis_type", "name")

    def __init__(self, policy_id: str):
        self.policy_id = policy_id
        self.policy = _policy(policy_id)
        self.id = ("double_dipping" if policy_id == "double_dipping.v1"
                   else f"inference.{policy_id.removesuffix('.v1').removesuffix('.v2')}")
        self.analysis_types = _ANALYSIS_TYPES[policy_id]
        self.audit_dimensions = _DIMENSIONS[policy_id]
        self.citations = list(_CITATIONS[policy_id])
        self.max_status = (S.NEEDS_EVIDENCE if policy_id in {
            "double_dipping.v1", "trajectory_circularity.v1",
        }
                           else S.BLOCKER)

    def _cap_engine_finding(self, finding: Finding) -> Finding:
        """Defense in depth: direct verifier calls obey the same cap as the audit spine."""
        if (self.policy_id == "double_dipping.v1"
                and S.SEVERITY.get(finding.status, 0) > S.SEVERITY.get(S.NEEDS_EVIDENCE, 2)):
            finding.status = S.NEEDS_EVIDENCE
        return finding

    def _contract(self, bundle) -> LivePolicyContract | None:
        contracts = getattr(bundle, "_inference_live_contracts", {}) or {}
        contract = contracts.get(self.policy_id)
        return contract if isinstance(contract, LivePolicyContract) else None

    def applies_to(self, design, bundle) -> bool:
        if self.policy_id == "double_dipping.v1":
            if design.analysis_type not in self.analysis_types:
                return False
            if getattr(design, "unit_of_test", None) != "cell":
                return False
            from sc_referee.checks.double_dipping import DoubleDippingCheck
            if design.analysis_type == "condition_contrast_DE":
                # The newly widened surface uses the strict report-bound predicate. Producer identity
                # alone is not claim applicability (an empty/unbound report must not add a finding).
                return DoubleDippingCheck().applies_to(design, bundle)
            sources = tuple((getattr(bundle, "code_signals", {}) or {}).get("sources", ()))
            evidence = compute_double_dipping_evidence(
                sources,
                getattr(bundle, "reported_results", None),
                report_relative_path=getattr(
                    getattr(bundle, "_inference_verifier_observation", None),
                    "report_relative_path",
                    None,
                ),
                data_relative_path=getattr(
                    getattr(bundle, "_inference_verifier_observation", None),
                    "data_relative_path",
                    None,
                ),
            )
            exact_pipeline = bool(evidence.test_producer and evidence.selection_producer)
            if exact_pipeline:
                return True
            return DoubleDippingCheck().applies_to(design, bundle)
        if design.analysis_type not in self.analysis_types:
            return False
        if self.policy_id == "allele_harmonization.v1":
            # A bare eQTL label is not a multi-source harmonization context.  Until the code-owned
            # context recognizer resolves one exactly, the shipped allele-orientation check alone runs.
            return False
        if self.policy_id in {"confounding.v2", "pseudoreplication.v1", "spatial_iid.v1"}:
            return self._contract(bundle) is not None
        return True

    def cannot_evaluate(self, design, bundle):
        if design.analysis_type not in self.analysis_types:
            return None
        if self.policy_id == "double_dipping.v1":
            from sc_referee.checks.double_dipping import DoubleDippingCheck
            return DoubleDippingCheck().cannot_evaluate(design, bundle)
        if self.policy_id == "allele_harmonization.v1":
            return None
        if self.policy_id in {"confounding.v2", "pseudoreplication.v1", "spatial_iid.v1"} \
                and self._contract(bundle) is None:
            return None
        if self._contract(bundle) is None:
            return (
                f"{design.analysis_type}: {self.policy_id} has no complete ratified live inference "
                "contract; this policy was NOT AUDITED and cannot produce a blocker"
            )
        return None

    def run(self, design, bundle, reported=None) -> Finding:
        if self.policy_id == "double_dipping.v1":
            sources = tuple((getattr(bundle, "code_signals", {}) or {}).get("sources", ()))
            evidence = compute_double_dipping_evidence(
                sources,
                reported,
                report_relative_path=getattr(
                    getattr(bundle, "_inference_verifier_observation", None),
                    "report_relative_path",
                    None,
                ),
                data_relative_path=getattr(
                    getattr(bundle, "_inference_verifier_observation", None),
                    "data_relative_path",
                    None,
                ),
            )
            if evidence.test_producer and evidence.selection_producer:
                return self._run_double_dipping(design, bundle, reported, evidence=evidence)
            # Exact engine integration is intentionally narrow.  Preserve the shipped detector for
            # every unsupported case rather than turning partial migration into a silent regression.
            from sc_referee.checks.double_dipping import DoubleDippingCheck
            legacy = DoubleDippingCheck()
            if legacy.applies_to(design, bundle):
                return self._cap_engine_finding(legacy.run(design, bundle, reported))
            return self._run_double_dipping(design, bundle, reported, evidence=evidence)
        # The flagship policy is integrated below by a code-owned analyzer.  Every other policy is
        # deliberately dormant until it has the same computed-fact integration.  In particular, an
        # optional folder contract cannot move this result away from ABSTAIN.
        return Finding(
            self.id,
            S.NOT_AUDITED,
            "the engine has no complete code-computed fact integration for this policy; folder "
            "assertions are routing metadata only and cannot prove a premise",
            metrics={
                "policy_id": self.policy.id,
                "engine_outcome": "ABSTAIN",
                "policy_cap": self.max_status,
                "analyzer_digest": ANALYZER_DIGEST,
                "closed_world_complete": False,
                "obligations": ["code_computed_policy_facts"],
            },
            citations=self.citations,
        )

    def _run_double_dipping(self, design, bundle, reported, *, evidence=None) -> Finding:
        sources = tuple((getattr(bundle, "code_signals", {}) or {}).get("sources", ()))
        evidence = evidence or compute_double_dipping_evidence(
            sources,
            reported,
            report_relative_path=getattr(
                getattr(bundle, "_inference_verifier_observation", None),
                "report_relative_path",
                None,
            ),
            data_relative_path=getattr(
                getattr(bundle, "_inference_verifier_observation", None),
                "data_relative_path",
                None,
            ),
        )
        relations = dict(evidence.relations)
        relations["ReportClaimPValue"] = (
            "PROVED" if evidence.test_producer is not None and evidence.inventory_complete
            else "UNKNOWN"
        )
        possible = (frozenset({evidence.test_producer})
                    if evidence.test_producer is not None else frozenset())
        fully_computed = bool(
            evidence.inventory_complete
            and all(evidence.relations[item] == "PROVED" for item in DOUBLE_DIPPING_PREMISES)
        )
        policy_snapshot = PolicySnapshot(
            inventory_complete=evidence.inventory_complete,
            possible_producers=possible,
            covered_producers=possible if fully_computed else frozenset(),
            unknown_producers=frozenset() if evidence.inventory_complete else frozenset({"unknown"}),
            coverage=self.policy.required_coverage if fully_computed else frozenset(),
            relations=relations,
            facts={},
        )
        judgment = evaluate(
            self.policy,
            "claim:marker-pvalue",
            policy_snapshot,
            builtin_registry(),
        )

        observation = getattr(bundle, "_inference_verifier_observation", None)
        report_digest = getattr(observation, "report_artifact_digest", None)
        locator_digest = getattr(observation, "report_locator_digest", None)
        producing_digest = evidence.producing_value_digest
        ratification_id = _sha256_bytes(
            (f"design|{getattr(design, 'analysis_type', '')}|"
             f"{getattr(design, 'unit_of_test', '')}|{getattr(design, 'name', '')}").encode()
        )
        confirmed = bool(getattr(design, "confirmed_by_human", False))
        certificate_complete = bool(
            fully_computed and report_digest and locator_digest and producing_digest
        )
        binding = (ClaimRootBinding(
            "structured",
            "claim:marker-pvalue",
            report_digest,
            locator_digest,
            producing_digest,
        ) if certificate_complete else None)
        certificate = Certificate(
            self.policy.id,
            judgment.outcome,
            judgment.max_external_status,
            CertificateRootGrade.ACCUSATION_GRADE,
            binding,
            report_digest or "",
            ratification_id if confirmed else None,
            (ratification_id,) if confirmed else (),
            confirmed,
            certificate_complete,
            evidence.inventory_complete,
            report_digest or "",
            locator_digest or "",
            producing_digest or "",
        )
        status = external_status(certificate)
        metrics = {
            "policy_id": self.policy.id,
            "engine_outcome": judgment.outcome,
            "policy_cap": judgment.max_external_status,
            "analyzer_digest": ANALYZER_DIGEST,
            "evidence_origin": "parsed_source_and_measured_report",
            "proved_relations": sorted(
                relation for relation, value in evidence.relations.items() if value == "PROVED"
            ),
            "premise_sources": dict(evidence.premise_sources),
            "claim_slice_possible": sorted(map(str, evidence.claim_slice.possible_producers)),
            "claim_slice_unavoidable": sorted(evidence.claim_slice.unavoidable_producers),
            "grouping_slice_unavoidable": sorted(evidence.grouping_slice.unavoidable_producers),
            "test_producer": evidence.test_producer,
            "selection_producer": evidence.selection_producer,
            "summary_bindings": [binding.__dict__ for binding in evidence.summary_bindings],
            "closed_world_complete": certificate_complete,
            "unknown_reasons": list(evidence.unknown_reasons),
            "obligations": list(judgment.obligations),
        }
        if judgment.outcome == "VIOLATION_WITNESS":
            verdict = (
                "engine-computed double-dipping structure detected: the reported marker p-values "
                "are must-produced by an exact naive marker test whose grouping is must-produced "
                "by an exact selection over overlapping expression data. This witness needs human "
                "review; static analysis is not entitled to an adverse verdict."
            )
        else:
            verdict = (
                "the parse-only engine did not prove every double-dipping premise; unresolved "
                "scientific facts remain unknown and no accusation is made"
            )
        return self._cap_engine_finding(Finding(
            self.id,
            status,
            verdict,
            metrics=metrics,
            citations=self.citations,
            # The parse-only verifier is capped below adverse entitlement even when it records a
            # structural witness. Its external result is therefore an abstention, never a concern.
            coverage=S.NOT_RUN,
        ))


def build_engine_verifiers() -> list[EnginePolicyVerifier]:
    return [EnginePolicyVerifier(policy_id) for policy_id in _POLICY_MODULES]


def _freeze_json(value):
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    if isinstance(value, dict):
        return {str(key): _freeze_json(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"unsupported live-contract value: {type(value).__name__}")


def _sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _parse_contract(value, *, sources: tuple[str, ...]):
    if not isinstance(value, dict) or value.get("policy_id") not in _POLICY_MODULES:
        return None
    # Source digests may narrow routing, but never establish a scientific fact.  A mismatched route
    # is ignored; when absent, the contract remains generic routing metadata.
    expected_sources = value.get("source_digests")
    if expected_sources is not None:
        if not isinstance(expected_sources, list):
            return None
        actual_sources = tuple(_sha256_bytes(source.encode()) for source in sources)
        if tuple(expected_sources) != actual_sources:
            return None
    routing = value.get("routing", {})
    proposed = value.get("proposed_facts", ())
    if not isinstance(routing, dict) or not isinstance(proposed, (list, tuple)):
        return None
    if not all(isinstance(item, dict) for item in proposed):
        return None
    return LivePolicyContract(
        policy_id=value["policy_id"],
        sources=sources,
        routing=_freeze_json(routing),
        proposed_facts=tuple(_freeze_json(item) for item in proposed),
    )


def attach_live_contracts(bundle, folder) -> None:
    """Load inert routing metadata and independently measure the real report artifact.

    Legacy accusation-bearing keys are accepted only for backward-compatible parsing and discarded.
    This makes an old or malicious contract powerless instead of allowing it to self-attest.
    """
    contracts = {}
    folder = Path(folder)
    report_info = (getattr(bundle, "provenance", {}) or {}).get("reported", {}) or {}
    report_rel = report_info.get("path")
    data_info = (getattr(bundle, "provenance", {}) or {}).get("data", {}) or {}
    data_rel = data_info.get("path")
    report_path = folder / report_rel if isinstance(report_rel, str) and report_rel else None
    report_digest = (_sha256_bytes(report_path.read_bytes())
                     if report_path is not None and report_path.is_file() else None)
    locator_digest = (_sha256_bytes(str(report_path.resolve()).encode())
                      if report_path is not None and report_path.is_file() else None)
    setattr(bundle, "_inference_verifier_observation", VerifierObservation(
        report_digest,
        locator_digest,
        report_rel if isinstance(report_rel, str) else None,
        data_rel if isinstance(data_rel, str) else None,
    ))
    path = folder / "sc-referee.inference.json"
    if path.exists():
        try:
            payload = json.loads(path.read_text())
            if not isinstance(payload, dict) or payload.get("version") != 1:
                raise ValueError("unsupported live-contract version")
            sources = tuple((getattr(bundle, "code_signals", {}) or {}).get("sources", ()))
            for raw in payload.get("contracts", ()):
                contract = _parse_contract(raw, sources=sources)
                if contract is not None and contract.policy_id not in contracts:
                    contracts[contract.policy_id] = contract
        except (OSError, UnicodeError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            contracts = {}
    setattr(bundle, "_inference_live_contracts", contracts)
