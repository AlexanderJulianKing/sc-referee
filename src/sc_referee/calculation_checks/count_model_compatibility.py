from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from sc_referee.calculation_checks.contracts import (
    selected_sidecar_contract,
    sidecar_adapter_manifest,
    with_sidecar_lineage,
)
from sc_referee.calculation_checks.core import (
    CalculationAdapterManifest,
    CalculationCheckManifest,
    CalculationCheckModule,
    CalculationCheckRegistry,
    CalculationContext,
    CalculationObservation,
    FrozenCalculationInput,
    NamedOperand,
    ObservationReceipt,
)
from sc_referee.calculation_checks.material_context import MaterialCalculationContext
from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.parsers.r_dual import inspect_r_source

COUNT_MODEL_CHECK_ID = "calculation-check:r-count-model-compatibility-v1"

_BLOCK = re.compile(
    r"```sc-referee-count-model-compatibility-v1\s*\n(?P<body>.*?)\n```",
    re.IGNORECASE | re.DOTALL,
)
_REQUIRED_KEYS = {
    "source_file",
    "producer_call",
    "response_scale",
    "required_method_family",
    "producer_binding",
}
_CALL_FAMILIES = {
    "DESeq2::DESeq": "negative_binomial_count_likelihood",
    "edgeR::exactTest": "negative_binomial_count_likelihood",
    "edgeR::glmFit": "negative_binomial_count_likelihood",
    "edgeR::glmQLFit": "negative_binomial_count_likelihood",
    "stats::t.test": "generic_continuous_location_test",
    "stats::wilcox.test": "generic_continuous_location_test",
    "stats::lm": "generic_continuous_location_test",
    "limma::lmFit": "generic_continuous_location_test",
}
_RECOGNITION_GRAMMAR_DIGEST = semantic_digest(
    {
        "block_pattern": _BLOCK.pattern,
        "required_keys": sorted(_REQUIRED_KEYS),
        "producer_calls": _CALL_FAMILIES,
        "response_scale": [
            "raw_counts",
            "transformed_continuous",
            "normalized_continuous",
            "unresolved",
        ],
        "required_method_family": [
            "count_likelihood",
            "continuous_location_model",
            "unresolved",
        ],
        "producer_binding": ["exact", "unresolved"],
        "r_parser": "tree_sitter_only_no_source_execution",
    }
)


class CountModelCompatibilityError(ValueError):
    """Raised when a count-model declaration escapes the closed contract."""


@dataclass(frozen=True)
class _Contract:
    source_file: str
    producer_call: str
    response_scale: str
    required_method_family: str
    producer_binding: str
    source_ref: dict[str, Any]


class DeclaredCountModelCompatibilityAdapter:
    def __init__(self) -> None:
        self.manifest = CalculationAdapterManifest(
            adapter_id="calculation-adapter:declared-r-count-model-compatibility-v1",
            adapter_version="1.0.0",
            implementation_digest=semantic_digest(
                {
                    "adapter_source": sha256_digest(Path(__file__).read_bytes()),
                    "recognition_grammar_digest": _RECOGNITION_GRAMMAR_DIGEST,
                }
            ),
            recognition_grammar_digest=_RECOGNITION_GRAMMAR_DIGEST,
        )

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        try:
            report = context.selected_report.content.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise CountModelCompatibilityError("selected report is not strict UTF-8") from error
        matches = list(_BLOCK.finditer(report))
        if not matches:
            return None
        if len(matches) != 1:
            return self._unsupported(
                context,
                context.selected_report.source_ref,
                "unique_count_model_contract",
                "The selected report contains more than one count-model compatibility contract.",
            )
        match = matches[0]
        source_ref = _block_source(context.selected_report, report, match)
        try:
            contract = _parse_contract(match.group("body"), source_ref)
        except CountModelCompatibilityError as error:
            return self._unsupported(
                context,
                source_ref,
                "count_model_contract_valid",
                str(error),
            )
        return self.inspect_normalized(context, contract)

    def inspect_normalized(
        self,
        context: CalculationContext,
        contract: _Contract,
    ) -> CalculationObservation:
        source_ref = contract.source_ref
        if (
            contract.response_scale == "unresolved"
            or contract.required_method_family == "unresolved"
            or contract.producer_binding == "unresolved"
        ):
            return self._unsupported(
                context,
                source_ref,
                "producer_scale_and_requirement_resolved",
                "The exact producer, response scale, or required method family remains unresolved; no compatibility conclusion was drawn.",
            )
        if not isinstance(context, MaterialCalculationContext):
            return self._unsupported(
                context,
                source_ref,
                "material_calculation_context_available",
                "The explicitly selected producer source was not available in the frozen material-input view.",
            )
        source = _unique_material(context, contract.source_file)
        if source is None:
            return self._unsupported(
                context,
                source_ref,
                "declared_producer_source_bound",
                "Exactly one fully identified declared producer source could not be bound.",
            )
        tree_result, _ = inspect_r_source(
            source.content,
            Path(source.path),
            "audit:bounded-count-model-static-inspection",
            source_path=source.path,
            r_executable="",
        )
        if tree_result.get("state") != "parsed":
            return self._unsupported(
                context,
                source_ref,
                "producer_source_fully_parsed",
                "The declared R producer source did not parse completely under the bounded static parser.",
                source=source,
            )
        extensions = tree_result.get("extensions")
        calls = extensions.get("x-r-calls") if isinstance(extensions, dict) else None
        if not isinstance(calls, list):
            return self._unsupported(
                context,
                source_ref,
                "producer_call_inventory_available",
                "The bounded R call inventory was unavailable.",
                source=source,
            )
        namespace, terminal = contract.producer_call.split("::", maxsplit=1)
        matching = [
            call
            for call in calls
            if call.get("target_kind") == "namespaced"
            and call.get("namespace") == namespace
            and call.get("namespace_operator") == "::"
            and call.get("terminal_name") == terminal
        ]
        if len(matching) != 1 or not isinstance(matching[0].get("source_ref"), dict):
            return self._unsupported(
                context,
                source_ref,
                "unique_exact_producer_call",
                "The declared namespaced producer call was absent or occurred more than once; exact producer binding was not established.",
                source=source,
            )
        call_source = dict(matching[0]["source_ref"])
        observed_family = _CALL_FAMILIES[contract.producer_call]
        compatible = _compatible(contract, observed_family)
        sources = (source_ref, call_source)
        return CalculationObservation(
            applicability="applicable",
            comparison_outcome="conformant" if compatible else "nonconformant",
            target_ref=context.selected_surface_ref,
            input_refs=(context.selected_artifact_ref, source.artifact_ref),
            source_refs=sources,
            operands=(
                NamedOperand("producer_source_path", "string", source.path),
                NamedOperand("producer_call", "string", contract.producer_call),
                NamedOperand("observed_method_family", "string", observed_family),
                NamedOperand("response_scale", "string", contract.response_scale),
                NamedOperand("required_method_family", "string", contract.required_method_family),
                NamedOperand("method_scale_compatible", "boolean", compatible),
                NamedOperand("producer_call_occurrences", "integer", len(matching)),
            ),
            receipts=(
                ObservationReceipt(
                    "applicability",
                    "explicit_count_model_contract",
                    "passed",
                    (source_ref,),
                    "One closed declaration binds the exact producer source, namespaced call, response scale, and required method family.",
                ),
                ObservationReceipt(
                    "completeness",
                    "fully_identified_producer_source",
                    "passed",
                    (source.source_ref,),
                    "The explicitly selected producer source has a complete content digest.",
                ),
                ObservationReceipt(
                    "completeness",
                    "unique_static_producer_call",
                    "passed",
                    (call_source,),
                    "The exact namespaced producer call occurred once in a completely parsed R source.",
                ),
                ObservationReceipt(
                    "counterevidence",
                    "alternate_or_ambiguous_producer",
                    "passed",
                    sources,
                    "An absent, repeated, unqualified, dynamic, or syntactically incomplete producer would have forced abstention.",
                ),
            ),
            lineage_status="complete",
            limitations=(
                "Static call identity plus the explicit producer binding does not prove execution, runtime dispatch, argument dataflow, numerical impact, or historical use.",
                "The initial registry covers a finite set of namespaced R methods and two coarse response-scale contracts only.",
                "No project-authored code was executed, and this module cannot emit a Finding.",
            ),
        )

    def _unsupported(
        self,
        context: CalculationContext,
        source_ref: dict[str, Any],
        predicate: str,
        detail: str,
        *,
        source: FrozenCalculationInput | None = None,
    ) -> CalculationObservation:
        inputs = (
            (context.selected_artifact_ref,)
            if source is None
            else (
                context.selected_artifact_ref,
                source.artifact_ref,
            )
        )
        sources = (source_ref,) if source is None else (source_ref, source.source_ref)
        return CalculationObservation(
            applicability="unsupported",
            comparison_outcome="unknown",
            target_ref=context.selected_surface_ref,
            input_refs=inputs,
            source_refs=sources,
            operands=(),
            receipts=(
                ObservationReceipt("completeness", predicate, "unsupported", sources, detail),
            ),
            lineage_status="incomplete",
            limitations=(detail, "No method/scale incompatibility was inferred."),
        )


class SelectedSidecarCountModelCompatibilityAdapter:
    def __init__(self) -> None:
        self.manifest = sidecar_adapter_manifest(
            family="r-count-model-compatibility",
            implementation_digest=sha256_digest(Path(__file__).read_bytes()),
        )
        self._evaluator = DeclaredCountModelCompatibilityAdapter()

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        sidecar = selected_sidecar_contract(context, check_id=COUNT_MODEL_CHECK_ID)
        if sidecar is None:
            return None
        contract = _parse_contract_value(sidecar.value, sidecar.source_ref)
        return with_sidecar_lineage(
            self._evaluator.inspect_normalized(context, contract),
            sidecar,
        )


def count_model_compatibility_registry() -> CalculationCheckRegistry:
    adapter = DeclaredCountModelCompatibilityAdapter()
    check = CalculationCheckManifest(
        check_id=COUNT_MODEL_CHECK_ID,
        check_version="1.0.0",
        implementation_digest=sha256_digest(Path(__file__).read_bytes()),
        comparison_relation="declared_r_producer_method_response_scale_compatibility",
        output_ceiling="disclosure_only",
        permitted_wording=(
            "The unique exact R producer call belongs to a method family incompatible with the explicitly bound response scale and required family."
        ),
    )
    return CalculationCheckRegistry(
        (CalculationCheckModule(check, (adapter,)),),
        profile_id="deterministic_r_count_model_compatibility_v1",
    )


def _parse_contract(body: str, source_ref: dict[str, Any]) -> _Contract:
    try:
        value = yaml.safe_load(body)
    except yaml.YAMLError as error:
        raise CountModelCompatibilityError("count-model contract is not valid YAML") from error
    if not isinstance(value, dict):
        raise CountModelCompatibilityError("count-model contract must be a mapping")
    return _parse_contract_value(value, source_ref)


def _parse_contract_value(value: dict[str, Any], source_ref: dict[str, Any]) -> _Contract:
    if set(value) != _REQUIRED_KEYS:
        raise CountModelCompatibilityError("count-model contract keys are missing or extra")
    if any(not isinstance(value[key], str) or not value[key].strip() for key in _REQUIRED_KEYS):
        raise CountModelCompatibilityError("count-model contract values must be nonempty strings")
    path = PurePosixPath(str(value["source_file"]))
    if path.is_absolute() or ".." in path.parts or path.suffix.casefold() != ".r":
        raise CountModelCompatibilityError("producer source must be one bounded .R path")
    if value["producer_call"] not in _CALL_FAMILIES:
        raise CountModelCompatibilityError(
            "producer call is outside the closed namespaced registry"
        )
    if value["response_scale"] not in {
        "raw_counts",
        "transformed_continuous",
        "normalized_continuous",
        "unresolved",
    }:
        raise CountModelCompatibilityError("response scale is outside the closed vocabulary")
    if value["required_method_family"] not in {
        "count_likelihood",
        "continuous_location_model",
        "unresolved",
    }:
        raise CountModelCompatibilityError(
            "required method family is outside the closed vocabulary"
        )
    if value["producer_binding"] not in {"exact", "unresolved"}:
        raise CountModelCompatibilityError("producer binding is outside the closed vocabulary")
    return _Contract(
        source_file=str(value["source_file"]).strip(),
        producer_call=str(value["producer_call"]).strip(),
        response_scale=str(value["response_scale"]).strip(),
        required_method_family=str(value["required_method_family"]).strip(),
        producer_binding=str(value["producer_binding"]).strip(),
        source_ref=source_ref,
    )


def _compatible(contract: _Contract, observed_family: str) -> bool:
    if contract.required_method_family == "count_likelihood":
        return (
            contract.response_scale == "raw_counts"
            and observed_family == "negative_binomial_count_likelihood"
        )
    return (
        contract.response_scale in {"transformed_continuous", "normalized_continuous"}
        and observed_family == "generic_continuous_location_test"
    )


def _unique_material(
    context: MaterialCalculationContext, path: str
) -> FrozenCalculationInput | None:
    matches = [item for item in context.material_inputs if item.path == path]
    return matches[0] if len(matches) == 1 else None


def _block_source(
    report: FrozenCalculationInput, text: str, match: re.Match[str]
) -> dict[str, Any]:
    start = text.count("\n", 0, match.start()) + 1
    end = text.count("\n", 0, match.end()) + 1
    return {
        "source_kind": "file_span",
        "locator": f"{report.path}:{start}-{end}",
        "path": report.path,
        "content_digest": report.content_digest,
        "start_line": start,
        "end_line": end,
        "quoted_text": match.group(0),
    }
