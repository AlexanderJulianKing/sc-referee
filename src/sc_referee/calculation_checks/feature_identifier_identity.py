from __future__ import annotations

import copy
import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import h5py  # type: ignore[import-untyped]
import yaml

from sc_referee.calculation_checks.contracts import (
    selected_sidecar_contract,
    sidecar_adapter_manifest,
    with_sidecar_lineage,
)
from sc_referee.calculation_checks.core import (
    CalculationAdapterManifest,
    CalculationCheckContractError,
    CalculationCheckManifest,
    CalculationCheckModule,
    CalculationCheckRegistry,
    CalculationContext,
    CalculationObservation,
    CalculationRegistryEvaluation,
    FrozenCalculationInput,
    NamedOperand,
    ObservationReceipt,
    public_observation_record,
)
from sc_referee.calculation_checks.delimited import bounded_table_text
from sc_referee.calculation_checks.integration import CalculationCompilation
from sc_referee.calculation_checks.material_context import MaterialCalculationContext
from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.delimited_io import classify_delimited_path
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.version import SCHEMA_VERSION

FEATURE_IDENTIFIER_IDENTITY_CHECK_ID = "calculation-check:selected-feature-identifier-identity-v1"
FEATURE_IDENTIFIER_IDENTITY_DIMENSION = "feature_identifier_identity_requirement"
EXACT_IDENTITY_RELATION = "exact_identifier_set_equality"

MAX_TABLE_BYTES = 8 * 1024 * 1024
MAX_TABLE_ROWS = 100_000
MAX_TABLE_COLUMNS = 128
MAX_AXIS_IDENTIFIERS = 100_000
MAX_AXIS_TEXT_BYTES = 4 * 1024 * 1024
MAX_DIFFERENCE_EXAMPLES = 64

_BLOCK = re.compile(
    r"```sc-referee-feature-identity-v1\s*\n(?P<body>.*?)\n```",
    re.IGNORECASE | re.DOTALL,
)
_REQUIRED_KEYS = {
    "left_input",
    "left_identifier_column",
    "right_input",
    "right_identifier_field",
    "comparison",
}
_RECOGNITION_GRAMMAR_DIGEST = semantic_digest(
    {
        "block_pattern": _BLOCK.pattern,
        "required_keys": sorted(_REQUIRED_KEYS),
        "comparison": EXACT_IDENTITY_RELATION,
        "identifier_policy": "strict_utf8_nonempty_trimmed_unique_no_normalization",
        "left_input": "bounded_csv_or_tsv_complete_identifier_column",
        "right_input": "bounded_h5ad_var_dataset_complete_identifier_axis",
        "ceilings": {
            "table_bytes": MAX_TABLE_BYTES,
            "table_rows": MAX_TABLE_ROWS,
            "table_columns": MAX_TABLE_COLUMNS,
            "axis_identifiers": MAX_AXIS_IDENTIFIERS,
            "axis_text_bytes": MAX_AXIS_TEXT_BYTES,
            "difference_examples": MAX_DIFFERENCE_EXAMPLES,
        },
    }
)


class FeatureIdentifierIdentityError(ValueError):
    """Raised when an identifier comparison escapes the closed profile."""


@dataclass(frozen=True)
class FeatureIdentifierIdentityContract:
    left_input: str
    left_identifier_column: str
    right_input: str
    right_identifier_field: str
    comparison: str
    source_ref: dict[str, Any]


@dataclass(frozen=True)
class _IdentifierSet:
    values: frozenset[str]
    ordered_digest: str


class DeclaredFeatureIdentifierIdentityAdapter:
    """Compare one explicitly declared table column with one H5AD feature axis."""

    def __init__(self) -> None:
        self.manifest = CalculationAdapterManifest(
            adapter_id="calculation-adapter:declared-feature-identifier-identity-v1",
            adapter_version="1.0.0",
            implementation_digest=sha256_digest(Path(__file__).read_bytes()),
            recognition_grammar_digest=_RECOGNITION_GRAMMAR_DIGEST,
        )

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        try:
            report = context.selected_report.content.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise FeatureIdentifierIdentityError("selected report is not strict UTF-8") from error
        matches = list(_BLOCK.finditer(report))
        if not matches:
            return None
        if len(matches) != 1:
            return self._unsupported(
                context,
                context.selected_report.source_ref,
                "unique_feature_identity_declaration",
                "The selected report contains more than one feature-identity declaration.",
            )
        match = matches[0]
        source_ref = _block_source(context.selected_report, report, match)
        try:
            contract = _parse_contract_text(match.group("body"), source_ref)
        except FeatureIdentifierIdentityError as error:
            return self._unsupported(
                context,
                source_ref,
                "feature_identity_declaration_valid",
                str(error),
            )
        return self.inspect_normalized(context, contract)

    def inspect_normalized(
        self,
        context: CalculationContext,
        contract: FeatureIdentifierIdentityContract,
    ) -> CalculationObservation:
        if not isinstance(context, MaterialCalculationContext):
            return self._unsupported(
                context,
                contract.source_ref,
                "material_inputs_available",
                "The declared material inputs are not available in the frozen calculation view.",
            )
        left = _unique_material(context, contract.left_input)
        right = _unique_material(context, contract.right_input)
        available = tuple(item for item in (left, right) if item is not None)
        if left is None or right is None or left.artifact_ref == right.artifact_ref:
            return self._unsupported(
                context,
                contract.source_ref,
                "distinct_declared_material_inputs_bound",
                "Exactly one distinct full-digest material input could not be bound for each declared path.",
                inputs=available,
            )
        try:
            left_ids = _delimited_identifiers(left, contract.left_identifier_column)
            right_ids = _h5ad_feature_identifiers(right, contract.right_identifier_field)
        except (FeatureIdentifierIdentityError, OSError, ValueError) as error:
            return self._unsupported(
                context,
                contract.source_ref,
                "complete_unique_identifier_sets_available",
                str(error),
                inputs=(left, right),
            )

        left_only = sorted(left_ids.values - right_ids.values)
        right_only = sorted(right_ids.values - left_ids.values)
        overlap_count = len(left_ids.values & right_ids.values)
        conformant = not left_only and not right_only
        source_refs = (contract.source_ref, left.source_ref, right.source_ref)
        return CalculationObservation(
            applicability="applicable",
            comparison_outcome="conformant" if conformant else "nonconformant",
            target_ref=context.selected_surface_ref,
            input_refs=(context.selected_artifact_ref, left.artifact_ref, right.artifact_ref),
            source_refs=source_refs,
            operands=(
                NamedOperand("left_input_path", "string", left.path),
                NamedOperand("left_identifier_column", "string", contract.left_identifier_column),
                NamedOperand("right_input_path", "string", right.path),
                NamedOperand("right_identifier_field", "string", contract.right_identifier_field),
                NamedOperand("comparison_relation", "string", contract.comparison),
                NamedOperand("left_identifier_count", "integer", len(left_ids.values)),
                NamedOperand("right_identifier_count", "integer", len(right_ids.values)),
                NamedOperand("overlap_count", "integer", overlap_count),
                NamedOperand("left_only_count", "integer", len(left_only)),
                NamedOperand("right_only_count", "integer", len(right_only)),
                NamedOperand(
                    "left_only_examples",
                    "string_array",
                    left_only[:MAX_DIFFERENCE_EXAMPLES],
                ),
                NamedOperand(
                    "right_only_examples",
                    "string_array",
                    right_only[:MAX_DIFFERENCE_EXAMPLES],
                ),
                NamedOperand("left_identifier_set_digest", "string", left_ids.ordered_digest),
                NamedOperand("right_identifier_set_digest", "string", right_ids.ordered_digest),
            ),
            receipts=(
                ObservationReceipt(
                    "applicability",
                    "closed_feature_identity_declaration",
                    "passed",
                    (contract.source_ref,),
                    "One closed declaration names two exact material inputs, one table identifier column, one H5AD var field, and exact set equality.",
                ),
                ObservationReceipt(
                    "completeness",
                    "full_digest_material_identity",
                    "passed",
                    (left.source_ref, right.source_ref),
                    "Both declared artifacts are explicit full-digest material inputs in the immutable snapshot.",
                ),
                ObservationReceipt(
                    "completeness",
                    "complete_unique_identifier_axes",
                    "passed",
                    (left.source_ref, right.source_ref),
                    "Both complete declared identifier axes parsed within finite byte, row, column, and text ceilings and contain unique nonempty already-trimmed strings.",
                ),
                ObservationReceipt(
                    "counterevidence",
                    "normalization_or_alias_mapping",
                    "passed",
                    (contract.source_ref,),
                    "The closed comparison permits no normalization or alias mapping; any such requirement must use the alternate-mapping Answer and suppress this candidate.",
                ),
                ObservationReceipt(
                    "counterevidence",
                    "complete_set_comparison",
                    "passed",
                    (left.source_ref, right.source_ref),
                    "The complete unique identifier sets, not a sample or row order, were compared exactly.",
                ),
            ),
            lineage_status="complete",
            limitations=(
                "This observation establishes only exact decoded identifier-set equality or inequality for the two declared selected axes.",
                "It does not establish producer lineage, historical intent, which representation is authoritative, why a value differs, biological meaning, execution, numerical impact, or publication validity.",
                "A mismatch requires an exact human Answer before the experimental detector may emit an evaluation candidate; production Finding permission remains false.",
            ),
        )

    def _unsupported(
        self,
        context: CalculationContext,
        source_ref: dict[str, Any],
        predicate: str,
        detail: str,
        *,
        inputs: tuple[FrozenCalculationInput, ...] = (),
    ) -> CalculationObservation:
        return CalculationObservation(
            applicability="unsupported",
            comparison_outcome="unknown",
            target_ref=context.selected_surface_ref,
            input_refs=(context.selected_artifact_ref, *(item.artifact_ref for item in inputs)),
            source_refs=(source_ref, *(item.source_ref for item in inputs)),
            operands=(),
            receipts=(
                ObservationReceipt(
                    "completeness",
                    predicate,
                    "unsupported",
                    (source_ref, *(item.source_ref for item in inputs)),
                    detail,
                ),
            ),
            lineage_status="incomplete",
            limitations=(detail, "No identifier conflict or scientific issue was inferred."),
        )


class SelectedSidecarFeatureIdentifierIdentityAdapter:
    def __init__(self) -> None:
        self._evaluator = DeclaredFeatureIdentifierIdentityAdapter()
        self.manifest = sidecar_adapter_manifest(
            family="feature-identifier-identity",
            implementation_digest=sha256_digest(Path(__file__).read_bytes()),
        )

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        try:
            sidecar = selected_sidecar_contract(
                context,
                check_id=FEATURE_IDENTIFIER_IDENTITY_CHECK_ID,
            )
        except CalculationCheckContractError as error:
            raise FeatureIdentifierIdentityError(str(error)) from error
        if sidecar is None:
            return None
        contract = _parse_contract_value(sidecar.value, sidecar.source_ref)
        return with_sidecar_lineage(
            self._evaluator.inspect_normalized(context, contract),
            sidecar,
        )


def feature_identifier_identity_registry() -> CalculationCheckRegistry:
    check = CalculationCheckManifest(
        check_id=FEATURE_IDENTIFIER_IDENTITY_CHECK_ID,
        check_version="1.0.0",
        implementation_digest=sha256_digest(Path(__file__).read_bytes()),
        comparison_relation="selected_table_vs_h5ad_exact_feature_identifier_set_equality",
        output_ceiling="evaluation_candidate",
        permitted_wording=(
            "The two exact selected feature identifier sets conflict with the explicit human exact-equality requirement governing this review."
        ),
    )
    return CalculationCheckRegistry(
        (
            CalculationCheckModule(
                check,
                (
                    DeclaredFeatureIdentifierIdentityAdapter(),
                    SelectedSidecarFeatureIdentifierIdentityAdapter(),
                ),
            ),
        ),
        profile_id="deterministic_feature_identifier_identity_v1",
    )


def partition_feature_identifier_identity_evaluation(
    evaluation: CalculationRegistryEvaluation,
    *,
    run_id: str,
    created_at: str,
) -> tuple[CalculationRegistryEvaluation, CalculationCompilation]:
    """Keep the immutable v12 compiler isolated while compiling the new v13 module."""

    legacy = CalculationRegistryEvaluation(
        profile_id=evaluation.profile_id,
        registry_digest=evaluation.registry_digest,
        context_digest=evaluation.context_digest,
        modules=tuple(
            module
            for module in evaluation.modules
            if module.check_manifest.check_id != FEATURE_IDENTIFIER_IDENTITY_CHECK_ID
        ),
    )
    observations: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []
    disclosures: list[dict[str, Any]] = []
    for module in evaluation.modules:
        if module.check_manifest.check_id != FEATURE_IDENTIFIER_IDENTITY_CHECK_ID:
            continue
        record = public_observation_record(module, run_id=run_id, created_at=created_at)
        if record is None:
            continue
        observations.append(record)
        observation = module.observation
        assert observation is not None
        if observation.applicability == "unsupported":
            disclosures.append(
                _feature_identifier_identity_disclosure(
                    record,
                    run_id=run_id,
                    created_at=created_at,
                )
            )
        elif observation.comparison_outcome == "nonconformant":
            questions.append(
                _feature_identifier_identity_question(
                    record,
                    run_id=run_id,
                    created_at=created_at,
                )
            )
    return legacy, CalculationCompilation(
        tuple(observations),
        tuple(questions),
        tuple(disclosures),
    )


def _feature_identifier_identity_question(
    observation: dict[str, Any],
    *,
    run_id: str,
    created_at: str,
) -> dict[str, Any]:
    operands = {
        str(item["name"]): item.get("value")
        for item in observation.get("operands", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    observation_id = str(observation["deterministic_check_observation_id"])
    observation_ref = typed_ref("deterministic_check_observation", observation_id)
    question_id = stable_id(
        "question-feature-identifier-identity",
        run_id,
        str(observation["observation_digest"]),
    )
    exact_option = stable_id("answer-option", question_id, "exact-equality")
    different_option = stable_id("answer-option", question_id, "different-permitted")
    mapping_option = stable_id("answer-option", question_id, "alternate-mapping")
    unknown_option = stable_id("answer-option", question_id, "retain-unknown")
    target_ref = copy.deepcopy(observation["target_ref"])
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "material_question",
        "question_id": question_id,
        "audit_run_id": run_id,
        "question": (
            f"For this review, must {operands['left_input_path']} column "
            f"{operands['left_identifier_column']!r} and {operands['right_input_path']} field "
            f"{operands['right_identifier_field']!r} contain the same exact identifier set?"
        ),
        "unknown_semantic_dimension": FEATURE_IDENTIFIER_IDENTITY_DIMENSION,
        "why_it_matters": (
            f"The complete sets contain {operands['left_only_count']} left-only and "
            f"{operands['right_only_count']} right-only identifiers. Whether that exact "
            "difference is a review-scoped issue depends on the required identifier relationship."
        ),
        "candidate_answers": [
            {
                "answer_id": exact_option,
                "label": "Exact equality required",
                "value": {"relationship": EXACT_IDENTITY_RELATION},
                "consequence": (
                    "The experimental detector may evaluate the complete exact set difference; "
                    "it still cannot emit a production Finding without qualification."
                ),
            },
            {
                "answer_id": different_option,
                "label": "Different identifiers permitted",
                "value": {"relationship": "not_required"},
                "consequence": "The exact-equality detector is not applicable to this review.",
            },
            {
                "answer_id": mapping_option,
                "label": "A mapping governs",
                "value": {"relationship": "alternate_mapping"},
                "consequence": (
                    "The exact-equality detector abstains until a separate bounded mapping "
                    "profile exists."
                ),
            },
            {
                "answer_id": unknown_option,
                "label": "Retain unknown",
                "value": {"action": "retain_unknown"},
                "consequence": "No identifier-conflict candidate is emitted.",
            },
        ],
        "evidence_searched": [
            {
                "source": "selected report declaration and exact full-digest material inputs",
                "result": (
                    f"The complete unique sets contain {operands['left_identifier_count']} and "
                    f"{operands['right_identifier_count']} identifiers, with "
                    f"{operands['overlap_count']} exact matches."
                ),
            }
        ],
        "blocked_detector_ids": ["detector:bounded-feature-identifier-identity"],
        "affected_claim_ids": [],
        "linked_conditional_concern_ids": [],
        "priority": "high",
        "status": "open",
        "answer_ids": [],
        "created_at": created_at,
        "provenance": controller_provenance(
            "bounded_feature_identifier_identity_question_v1", created_at
        ),
        "extensions": {
            "x-calculation-observation-ref": observation_ref,
            "x-output-ceiling": "evaluation_candidate",
            "x-analysis-subject-ref": target_ref,
            "x-feature-identity-source-refs": copy.deepcopy(observation["source_refs"]),
            "x-feature-identity-observation-digest": observation["observation_digest"],
        },
    }


def _feature_identifier_identity_disclosure(
    observation: dict[str, Any],
    *,
    run_id: str,
    created_at: str,
) -> dict[str, Any]:
    observation_id = str(observation["deterministic_check_observation_id"])
    observation_ref = typed_ref("deterministic_check_observation", observation_id)
    limitations = observation.get("limitations", [])
    description = (
        str(limitations[0])
        if isinstance(limitations, list) and limitations
        else "The selected feature-identifier comparison could not be completed."
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "disclosure",
        "disclosure_id": stable_id("disclosure-feature-identity", run_id, observation_id),
        "audit_run_id": run_id,
        "disclosure_kind": "detector_gap",
        "title": "Selected feature-identifier comparison could not be completed",
        "description": description,
        "importance": "important",
        "non_accusatory": True,
        "affected_refs": [
            observation_ref,
            copy.deepcopy(observation["target_ref"]),
        ],
        "source_refs": copy.deepcopy(observation["source_refs"]),
        "coverage_status": "not_covered",
        "interpretive_consequence": (
            "No identifier conflict was established; the unsupported exact comparison remains "
            "outside detector coverage."
        ),
        "created_at": created_at,
        "provenance": controller_provenance(
            "bounded_feature_identifier_identity_disclosure_v1", created_at
        ),
        "extensions": {
            "x-calculation-observation-ref": observation_ref,
            "x-production-finding-permitted": False,
        },
    }


def _parse_contract_text(
    body: str, source_ref: dict[str, Any]
) -> FeatureIdentifierIdentityContract:
    try:
        value = yaml.safe_load(body)
    except yaml.YAMLError as error:
        raise FeatureIdentifierIdentityError(
            "feature-identity declaration is not valid bounded YAML"
        ) from error
    if not isinstance(value, dict):
        raise FeatureIdentifierIdentityError("feature-identity declaration must be a mapping")
    return _parse_contract_value(value, source_ref)


def _parse_contract_value(
    value: dict[str, Any], source_ref: dict[str, Any]
) -> FeatureIdentifierIdentityContract:
    if set(value) != _REQUIRED_KEYS:
        raise FeatureIdentifierIdentityError(
            "feature-identity declaration keys are missing, extra, or duplicated"
        )
    if any(not isinstance(value[key], str) or not value[key].strip() for key in _REQUIRED_KEYS):
        raise FeatureIdentifierIdentityError(
            "feature-identity declaration values must be nonempty strings"
        )
    normalized = {key: str(value[key]).strip() for key in _REQUIRED_KEYS}
    for key in ("left_input", "right_input"):
        path = PurePosixPath(normalized[key])
        if path.is_absolute() or ".." in path.parts:
            raise FeatureIdentifierIdentityError(
                "feature-identity input paths must be bounded and relative"
            )
    if normalized["left_input"] == normalized["right_input"]:
        raise FeatureIdentifierIdentityError("feature-identity inputs must be distinct")
    if classify_delimited_path(normalized["left_input"]) is None:
        raise FeatureIdentifierIdentityError("left feature-identity input must be CSV or TSV")
    if PurePosixPath(normalized["right_input"]).suffix.casefold() != ".h5ad":
        raise FeatureIdentifierIdentityError("right feature-identity input must be H5AD")
    if not normalized["right_identifier_field"].startswith("var/"):
        raise FeatureIdentifierIdentityError("right identifier field must name one H5AD var field")
    if normalized["comparison"] != EXACT_IDENTITY_RELATION:
        raise FeatureIdentifierIdentityError(
            "feature-identity comparison must be exact_identifier_set_equality"
        )
    return FeatureIdentifierIdentityContract(
        left_input=normalized["left_input"],
        left_identifier_column=normalized["left_identifier_column"],
        right_input=normalized["right_input"],
        right_identifier_field=normalized["right_identifier_field"],
        comparison=normalized["comparison"],
        source_ref=source_ref,
    )


def _unique_material(
    context: MaterialCalculationContext, path: str
) -> FrozenCalculationInput | None:
    matches = [item for item in context.material_inputs if item.path == path]
    return matches[0] if len(matches) == 1 else None


def _delimited_identifiers(material: FrozenCalculationInput, column: str) -> _IdentifierSet:
    text, delimiter = bounded_table_text(
        material,
        byte_ceiling=MAX_TABLE_BYTES,
        error_type=FeatureIdentifierIdentityError,
        label="declared feature table",
    )
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)
    header = reader.fieldnames
    if (
        header is None
        or len(header) > MAX_TABLE_COLUMNS
        or len(set(header)) != len(header)
        or column not in header
    ):
        raise FeatureIdentifierIdentityError(
            "declared feature table identifier column is unavailable or ambiguous"
        )
    identifiers: list[str] = []
    for row_index, row in enumerate(reader, start=1):
        if row_index > MAX_TABLE_ROWS:
            raise FeatureIdentifierIdentityError("declared feature table exceeds the row ceiling")
        value = row.get(column)
        if not isinstance(value, str) or not value or value != value.strip():
            raise FeatureIdentifierIdentityError(
                "declared feature table identifiers must be nonempty and already trimmed"
            )
        identifiers.append(value)
    return _unique_identifier_set(identifiers, label="declared feature table")


def _h5ad_feature_identifiers(material: FrozenCalculationInput, field: str) -> _IdentifierSet:
    try:
        handle = h5py.File(io.BytesIO(material.content), "r")
    except (OSError, ValueError) as error:
        raise FeatureIdentifierIdentityError("declared H5AD is not readable HDF5") from error
    with handle:
        if _attr_text(handle.attrs.get("encoding-type")) != "anndata":
            raise FeatureIdentifierIdentityError("declared H5AD is not encoded as AnnData")
        matrix = handle.get("X")
        if not isinstance(matrix, (h5py.Dataset, h5py.Group)):
            raise FeatureIdentifierIdentityError("declared H5AD X is unavailable")
        shape = matrix.shape if isinstance(matrix, h5py.Dataset) else None
        if shape is None:
            shape_attr = matrix.attrs.get("shape")
            if shape_attr is not None and len(shape_attr) == 2:
                shape = (int(shape_attr[0]), int(shape_attr[1]))
        if shape is None or len(shape) != 2:
            raise FeatureIdentifierIdentityError("declared H5AD feature-axis length is unavailable")
        expected = int(shape[1])
        if expected < 1 or expected > MAX_AXIS_IDENTIFIERS:
            raise FeatureIdentifierIdentityError("declared H5AD feature axis exceeds the ceiling")
        dataset = handle.get(field)
        if (
            not isinstance(dataset, h5py.Dataset)
            or len(dataset.shape) != 1
            or int(dataset.shape[0]) != expected
            or dataset.is_virtual
        ):
            raise FeatureIdentifierIdentityError(
                "declared H5AD feature identifier field is unavailable or inconsistent"
            )
        try:
            identifiers = [
                str(item) for item in dataset.asstr(encoding="utf-8", errors="strict")[...]
            ]
        except (OSError, TypeError, UnicodeError) as error:
            raise FeatureIdentifierIdentityError(
                "declared H5AD feature identifiers are not strict UTF-8 strings"
            ) from error
    if sum(len(item.encode("utf-8")) for item in identifiers) > MAX_AXIS_TEXT_BYTES:
        raise FeatureIdentifierIdentityError(
            "declared H5AD feature identifiers exceed the text ceiling"
        )
    if any(not item or item != item.strip() for item in identifiers):
        raise FeatureIdentifierIdentityError(
            "declared H5AD feature identifiers must be nonempty and already trimmed"
        )
    return _unique_identifier_set(identifiers, label="declared H5AD feature axis")


def _unique_identifier_set(values: list[str], *, label: str) -> _IdentifierSet:
    if not values:
        raise FeatureIdentifierIdentityError(f"{label} contains no identifiers")
    if len(values) != len(set(values)):
        raise FeatureIdentifierIdentityError(f"{label} contains duplicate identifiers")
    ordered = sorted(values)
    return _IdentifierSet(frozenset(values), semantic_digest(ordered))


def _block_source(
    report: FrozenCalculationInput,
    text: str,
    match: re.Match[str],
) -> dict[str, Any]:
    start = text.count("\n", 0, match.start()) + 1
    end = text.count("\n", 0, match.end()) + 1
    return {
        "source_kind": "file_span",
        "locator": f"{report.path}:{start}-{end}",
        "path": report.path,
        "start_line": start,
        "end_line": end,
        "quoted_text": match.group(0),
        "content_digest": report.content_digest,
    }


def _attr_text(value: Any) -> str | None:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="strict")
    return str(value) if isinstance(value, str) else None
