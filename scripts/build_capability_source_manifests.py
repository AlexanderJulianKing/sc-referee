from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.parsers.python_ast import PARSER_ID as PYTHON_PARSER_ID
from sc_referee.parsers.python_ast import PARSER_VERSION as PYTHON_PARSER_VERSION
from sc_referee.version import SCHEMA_VERSION, __version__

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_ROOT = ROOT / "src" / "sc_referee" / "resources" / "capability-manifests-v1"
GENERATED_AT = "2026-07-30T00:00:00Z"
ANALYSIS_METHOD_CONFLICT_CHECK_IDS = sorted(
    [
        "check:full-map-ancestry-exposure",
        "check:casrx-isoform-axis-model",
        "check:classifier-derived-copy-dosage-representation",
        "check:direct-standardization-conditioning-set",
        "check:directional-measurement-error-interpretation",
        "check:expected-count-background-construction",
        "check:expected-count-focal-target-handling",
        "check:founder-orientation-before-hmm-emission",
        "check:ld-covariance-whitening-before-robust-fit",
        "check:local-perturbation-primary-row-scope",
        "check:local-perturbation-regression-specification",
        "check:mvmr-cross-exposure-covariance",
        "check:mvmr-residual-heterogeneity-estimator",
        "check:paired-bridge-location-alignment",
        "check:phase-split-mvmr-instrument-construction",
        "check:poststratified-misclassification-estimator",
        "check:posttreatment-missingness-strategy",
        "check:recoverable-technical-group-adjustment",
        "check:somatic-clonality-representation",
        "check:within-sequence-transition-path-continuity",
    ]
)


def _load(name: str) -> dict[str, Any]:
    value = json.loads((MANIFEST_ROOT / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain one JSON object")
    return value


def _write(name: str, value: object) -> None:
    (MANIFEST_ROOT / name).write_text(canonical_json(value) + "\n", encoding="utf-8")


def _upsert(collection: dict[str, Any], id_field: str, record: dict[str, Any]) -> None:
    records = collection.get("records")
    if not isinstance(records, list):
        raise ValueError("capability source collection requires a records array")
    retained = [item for item in records if item.get(id_field) != record[id_field]]
    retained.append(record)
    retained.sort(key=lambda item: str(item[id_field]))
    collection["records"] = retained


def main() -> None:
    parser_collection = _load("parser-manifests.json")
    tabular_parser_resource = ROOT / "src" / "sc_referee" / "tabular_inventory.py"
    _upsert(
        parser_collection,
        "parser_id",
        {
            "backend": "other",
            "capabilities": ["inventory", "exact_spans", "source_references"],
            "executes_project_code": False,
            "extensions": {"x-implementation-resource": "tabular_inventory.py"},
            "grammar_or_runtime_identity": [
                "Python standard-library strict CSV first-record reader",
                "bounded identity or gzip logical-record stream under ADR-0054",
            ],
            "implementation_digest": sha256_digest(tabular_parser_resource.read_bytes()),
            "language_or_surface": "delimited_table",
            "limitations": [
                "Only the first logical record is interpreted as a header.",
                "For gzip inputs, bytes after the first logical record are not decompressed or validated.",
                "Column names do not establish storage types, scientific meanings, row shape, row count, or cell values.",
            ],
            "parser_id": "parser:tabular-delimited-header-inventory",
            "parser_version": "0.2.0",
            "provenance": {
                "actor": {
                    "actor_id": "software:sc-referee-controller",
                    "actor_kind": "controller",
                    "display_name": "sc-referee controller",
                },
                "created_at": GENERATED_AT,
                "method": "deterministic_release_manifest",
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "record_type": "parser_manifest",
            "runtime_requirements": ["Python >=3.11", "strict UTF-8 header"],
            "schema_version": SCHEMA_VERSION,
            "supported_versions": [
                "Comma-delimited CSV and tab-delimited TSV first logical records, stored directly or in one gzip byte stream, under ADR-0054"
            ],
            "unsupported_constructs": [
                "row and cell inspection",
                "compression formats other than gzip",
                "non-UTF-8 headers",
                "non-comma CSV and non-tab TSV dialects",
                "headers above 1024 columns or 1 MiB",
                "gzip member integrity after the first logical record",
                "scientific interpretation",
            ],
        },
    )
    python_parser_resource = ROOT / "src" / "sc_referee" / "parsers" / "python_ast.py"
    _upsert(
        parser_collection,
        "parser_id",
        {
            "backend": "cpython_ast_tokenize",
            "capabilities": [
                "inventory",
                "syntax_tree",
                "exact_spans",
                "comments",
                "operation_extraction",
                "source_references",
            ],
            "executes_project_code": False,
            "extensions": {"x-implementation-resource": "parsers/python_ast.py"},
            "grammar_or_runtime_identity": [
                "CPython ast and tokenize from the active auditor runtime",
                "bounded literal and exact source-parent-relative static path inventory v2",
            ],
            "implementation_digest": sha256_digest(python_parser_resource.read_bytes()),
            "language_or_surface": "python",
            "limitations": [
                "Syntax rejected by the active CPython runtime is localized as partial coverage.",
                "Operation extraction recognizes only declared literal static forms.",
                "A static selected-output writer does not establish project execution or authorship of existing bytes.",
            ],
            "parser_id": PYTHON_PARSER_ID,
            "parser_version": PYTHON_PARSER_VERSION,
            "provenance": {
                "actor": {
                    "actor_id": "software:sc-referee-controller",
                    "actor_kind": "controller",
                    "display_name": "sc-referee controller",
                },
                "created_at": GENERATED_AT,
                "method": "deterministic_release_manifest",
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "record_type": "parser_manifest",
            "runtime_requirements": ["Python >=3.11"],
            "schema_version": SCHEMA_VERSION,
            "supported_versions": [
                "CPython source syntax accepted by the active Python 3.11+ runtime"
            ],
            "unsupported_constructs": [
                "runtime-generated code",
                "computed call targets",
                "wildcard-import binding resolution",
                "dynamic, absolute, parent-traversing, rebound, or non-source-parent write roots",
                "general control-flow and DAG result lineage",
            ],
        },
    )
    parser_resource = ROOT / "src" / "sc_referee" / "parsers" / "rmarkdown_inventory.py"
    _upsert(
        parser_collection,
        "parser_id",
        {
            "backend": "other",
            "capabilities": [
                "inventory",
                "exact_spans",
                "error_recovery",
                "source_references",
            ],
            "executes_project_code": False,
            "extensions": {
                "x-implementation-resource": "parsers/rmarkdown_inventory.py",
            },
            "grammar_or_runtime_identity": [
                "bounded strict-UTF-8 YAML, prose, and fenced R-chunk inventory v2"
            ],
            "implementation_digest": sha256_digest(parser_resource.read_bytes()),
            "language_or_surface": "r_markdown",
            "limitations": [
                "This is a bounded document and chunk inventory, not a general R parser or an R Markdown renderer.",
                "Only literal fenced {r} or {R} chunks and literal eval=FALSE/F options are classified.",
            ],
            "parser_id": "parser:rmarkdown-selected-report-inventory",
            "parser_version": "0.2.0",
            "provenance": {
                "actor": {
                    "actor_id": "software:sc-referee-controller",
                    "actor_kind": "controller",
                    "display_name": "sc-referee controller",
                },
                "created_at": GENERATED_AT,
                "method": "deterministic_release_manifest",
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "record_type": "parser_manifest",
            "runtime_requirements": ["Python >=3.11", "strict UTF-8 input"],
            "schema_version": SCHEMA_VERSION,
            "supported_versions": [
                "Strict UTF-8 R Markdown sources using the bounded fenced-R-chunk subset in ADR-0021 and ADR-0051"
            ],
            "unsupported_constructs": [
                "general R syntax and dataflow",
                "inline R semantics",
                "knitr, Quarto, or Pandoc rendering",
                "runtime-generated chunks",
                "project execution and package behavior",
            ],
        },
    )
    notebook_parser_resource = ROOT / "src" / "sc_referee" / "parsers" / "jupyter_inventory.py"
    _upsert(
        parser_collection,
        "parser_id",
        {
            "backend": "jupyter_json",
            "capabilities": [
                "inventory",
                "error_recovery",
                "source_references",
            ],
            "executes_project_code": False,
            "extensions": {
                "x-implementation-resource": "parsers/jupyter_inventory.py",
            },
            "grammar_or_runtime_identity": [
                "Python strict JSON decoder with duplicate-key rejection under bounded nbformat 4 inventory v2"
            ],
            "implementation_digest": sha256_digest(notebook_parser_resource.read_bytes()),
            "language_or_surface": "jupyter_notebook",
            "limitations": [
                "Only bounded nbformat 4 cell source and saved-output structure is inventoried.",
                "Cell code, Markdown, outputs, attachments, widgets, kernels, and runtime state are not executed, rendered, authenticated, or semantically interpreted.",
            ],
            "parser_id": "parser:jupyter-notebook-inventory",
            "parser_version": "0.2.0",
            "provenance": {
                "actor": {
                    "actor_id": "software:sc-referee-controller",
                    "actor_kind": "controller",
                    "display_name": "sc-referee controller",
                },
                "created_at": GENERATED_AT,
                "method": "deterministic_release_manifest",
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "record_type": "parser_manifest",
            "runtime_requirements": ["Python >=3.11", "strict UTF-8 JSON input"],
            "schema_version": SCHEMA_VERSION,
            "supported_versions": [
                "nbformat 4 JSON within the finite ADR-0034 cell and output inventory profile"
            ],
            "unsupported_constructs": [
                "nbformat versions other than 4",
                "cell code and magic interpretation outside the separately declared static cell-language bridge",
                "kernel execution and hidden state",
                "saved-output authenticity and code-to-output provenance",
                "Markdown, HTML, widget, and attachment rendering",
                "scientific interpretation",
            ],
        },
    )
    quarto_parser_resource = ROOT / "src" / "sc_referee" / "parsers" / "quarto_inventory.py"
    _upsert(
        parser_collection,
        "parser_id",
        {
            "backend": "other",
            "capabilities": ["inventory", "exact_spans", "error_recovery", "source_references"],
            "executes_project_code": False,
            "extensions": {"x-implementation-resource": "parsers/quarto_inventory.py"},
            "grammar_or_runtime_identity": [
                "bounded strict-UTF-8 Quarto front-matter, prose, and executable-cell inventory v2"
            ],
            "implementation_digest": sha256_digest(quarto_parser_resource.read_bytes()),
            "language_or_surface": "quarto",
            "limitations": [
                "Only exact triple-backtick literal-engine cells and leading literal #| options are inventoried.",
                "Quarto, Pandoc, kernels, extensions, filters, includes, and project code are not rendered or executed.",
            ],
            "parser_id": "parser:quarto-source-inventory",
            "parser_version": "0.2.0",
            "provenance": {
                "actor": {
                    "actor_id": "software:sc-referee-controller",
                    "actor_kind": "controller",
                    "display_name": "sc-referee controller",
                },
                "created_at": GENERATED_AT,
                "method": "deterministic_release_manifest",
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "record_type": "parser_manifest",
            "runtime_requirements": ["Python >=3.11", "strict UTF-8 input"],
            "schema_version": SCHEMA_VERSION,
            "supported_versions": [
                "Quarto-like .qmd source within the finite ADR-0035 structural subset; no Quarto release conformance claimed"
            ],
            "unsupported_constructs": [
                "YAML and Quarto project semantics",
                "cell code outside the separately declared static cell-language bridge and all inline-code interpretation",
                "shortcodes, includes, cross-references, filters, and extensions",
                "Pandoc and output-format rendering",
                "kernel and project execution",
                "artifact lineage and scientific interpretation",
            ],
        },
    )
    bridge_resource = ROOT / "src" / "sc_referee" / "parsers" / "cell_language_bridge.py"
    _upsert(
        parser_collection,
        "parser_id",
        {
            "backend": "other",
            "capabilities": [
                "inventory",
                "exact_spans",
                "operation_extraction",
                "error_recovery",
                "source_references",
            ],
            "executes_project_code": False,
            "extensions": {
                "x-implementation-resource": "parsers/cell_language_bridge.py",
                "x-delegated-parser-ids": [
                    "parser:python-ast-tokenize",
                    "parser:r-base-parse-data",
                    "parser:r-tree-sitter-inventory",
                ],
            },
            "grammar_or_runtime_identity": [
                "bounded independently parsed Python-or-R container cells under ADR-0036 and ADR-0051 with ADR-0037 source-location transport"
            ],
            "implementation_digest": sha256_digest(bridge_resource.read_bytes()),
            "language_or_surface": "container_cell",
            "limitations": [
                "Only cells with an exact unconflicted Python or R language declaration are delegated to the existing static parsers.",
                "Cells are parsed independently; cross-cell state, execution order, runtime behavior, and code-to-output provenance remain unknown.",
            ],
            "parser_id": "parser:container-cell-language-bridge",
            "parser_version": "0.2.0",
            "provenance": {
                "actor": {
                    "actor_id": "software:sc-referee-controller",
                    "actor_kind": "controller",
                    "display_name": "sc-referee controller",
                },
                "created_at": GENERATED_AT,
                "method": "deterministic_release_manifest",
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "record_type": "parser_manifest",
            "runtime_requirements": [
                "Python >=3.11",
                "strict UTF-8 cell source",
            ],
            "schema_version": SCHEMA_VERSION,
            "supported_versions": [
                "Exact Python or R cells extracted from bounded ADR-0034/ADR-0035/ADR-0051 container inventories"
            ],
            "unsupported_constructs": [
                "conflicting, absent, or unsupported notebook language declarations",
                "Quarto cell engines other than Python and R",
                "R Markdown chunks outside the exact fenced R subset",
                "more than 200 recognized code cells per container",
                "cross-cell bindings and runtime state",
                "kernel magics, output authenticity, rendering, and project execution",
                "Claims, scientific interpretation, detectors, and Findings",
            ],
        },
    )
    r_parser_resource = ROOT / "src" / "sc_referee" / "parsers" / "r_dual.py"
    r_parser_digest = sha256_digest(r_parser_resource.read_bytes())
    common_r_parser = {
        "capabilities": [
            "inventory",
            "syntax_tree",
            "exact_spans",
            "operation_extraction",
            "error_recovery",
            "source_references",
        ],
        "executes_project_code": False,
        "extensions": {"x-implementation-resource": "parsers/r_dual.py"},
        "implementation_digest": r_parser_digest,
        "language_or_surface": "r",
        "limitations": [
            "Only direct identifier and literal namespace call targets, literal argument names, and source spans are inventoried.",
            "Static syntax does not establish evaluation, dispatch, package ownership for direct calls, dataflow, formulas, or scientific meaning.",
        ],
        "parser_version": "0.1.0",
        "provenance": {
            "actor": {
                "actor_id": "software:sc-referee-controller",
                "actor_kind": "controller",
                "display_name": "sc-referee controller",
            },
            "created_at": GENERATED_AT,
            "method": "deterministic_release_manifest",
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "record_type": "parser_manifest",
        "schema_version": SCHEMA_VERSION,
        "unsupported_constructs": [
            "runtime-generated and computed call targets",
            "tidy evaluation and nonstandard evaluation",
            "package loading and dispatch resolution",
            "general control flow and dataflow",
            "project execution and scientific interpretation",
        ],
    }
    _upsert(
        parser_collection,
        "parser_id",
        {
            **common_r_parser,
            "backend": "tree_sitter_r",
            "grammar_or_runtime_identity": [
                "tree-sitter 0.25.x with tree-sitter-r 1.3.0 at commit 346d3707b8c9301f1051e8f6e32666e67529f7d2"
            ],
            "parser_id": "parser:r-tree-sitter-inventory",
            "runtime_requirements": [
                "Python >=3.11",
                "tree-sitter >=0.25.2,<0.26",
                "tree-sitter-r grammar 1.3.0",
                "strict UTF-8 input",
            ],
            "supported_versions": [
                "R syntax recognized by tree-sitter-r 1.3.0 at commit 346d3707b8c9301f1051e8f6e32666e67529f7d2"
            ],
        },
    )
    _upsert(
        parser_collection,
        "parser_id",
        {
            **common_r_parser,
            "backend": "base_r_parse_data",
            "grammar_or_runtime_identity": [
                "active base-R parse(keep.source=TRUE) and getParseData() runtime"
            ],
            "parser_id": "parser:r-base-parse-data",
            "runtime_requirements": [
                "Python >=3.11",
                "base R executable on PATH for the independent parse-data receipt",
                "strict UTF-8 input",
            ],
            "supported_versions": [
                "R source syntax accepted by the active base-R runtime without sourcing or evaluation"
            ],
        },
    )
    feature_identity_parser_resource = (
        ROOT / "src" / "sc_referee" / "calculation_checks" / "feature_identifier_identity.py"
    )
    _upsert(
        parser_collection,
        "parser_id",
        {
            "backend": "other",
            "capabilities": [
                "inventory",
                "exact_spans",
                "operation_extraction",
                "error_recovery",
                "source_references",
            ],
            "executes_project_code": False,
            "extensions": {
                "x-implementation-resource": ("calculation_checks/feature_identifier_identity.py")
            },
            "grammar_or_runtime_identity": [
                "bounded strict-UTF-8 Markdown declaration and delimited identifier column",
                "bounded h5py read of one AnnData X feature-axis length and one declared var dataset",
            ],
            "implementation_digest": sha256_digest(feature_identity_parser_resource.read_bytes()),
            "language_or_surface": "selected_feature_identifier_axes",
            "limitations": [
                "Only one exact declared CSV or TSV column and one exact declared H5AD var dataset are read completely within finite ceilings.",
                "No aliases, normalization, duplicate identifiers, producer lineage, execution, or biological meaning are interpreted.",
            ],
            "parser_id": "parser:selected-feature-identifier-axes",
            "parser_version": "0.1.0",
            "provenance": {
                "actor": {
                    "actor_id": "software:sc-referee-controller",
                    "actor_kind": "controller",
                    "display_name": "sc-referee controller",
                },
                "created_at": "2026-08-02T00:00:00Z",
                "method": "deterministic_release_manifest",
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "record_type": "parser_manifest",
            "runtime_requirements": [
                "Python >=3.11",
                "h5py available in the auditor environment",
                "strict UTF-8 identifier strings",
            ],
            "schema_version": SCHEMA_VERSION,
            "supported_versions": [
                "Closed sc-referee-feature-identity-v1 declarations, CSV or TSV tables, and AnnData-encoded HDF5 with a dense or declared-shape sparse X axis"
            ],
            "unsupported_constructs": [
                "compressed tables",
                "categorical-coded H5AD var fields",
                "more than one declaration or sidecar observation",
                "identifier aliases and normalization",
                "duplicate, empty, or surrounding-whitespace identifiers",
                "objects outside the finite byte, row, column, axis, and text ceilings",
                "scientific interpretation and project execution",
            ],
        },
    )
    _write("parser-manifests.json", parser_collection)

    detector_collection = _load("detector-manifests.json")
    analysis_conflict_resource = (
        ROOT / "src" / "sc_referee" / "detectors" / "bounded_analysis_method_conflict.py"
    )
    analysis_conflict_checks = [
        (
            "check:analysis-requirement-authority",
            "Require one exact human Answer and its controller-verified review requirement.",
        ),
        (
            "check:reported-method-uniqueness",
            "Require one exact selected-report operand under the bound scope digest.",
        ),
        (
            "check:static-method-uniqueness",
            "Require one exact static-source operand under the bound scope digest.",
        ),
        (
            "check:observed-plane-agreement",
            "Require the selected report and static source to expose the same operand.",
        ),
        (
            "check:selected-output-scope-closure",
            "Reverify the full-digest file-to-writer-to-report-to-publication-surface graph.",
        ),
        (
            "check:alternate-or-superseding-intent",
            "Search accepted scoped assertions for another governing review requirement.",
        ),
        (
            "check:governing-protocol-amendment",
            "Search accepted scoped assertions for a governing protocol amendment.",
        ),
        (
            "check:approved-method-deviation",
            "Search accepted scoped assertions for an approved method deviation.",
        ),
        (
            "check:conditional-applicability",
            "Search accepted scoped assertions for a conditional-applicability mismatch.",
        ),
        (
            "check:sensitivity-or-unsupported-qualifier",
            "Search the selected observations for sensitivity-only or unsupported-method qualifiers.",
        ),
    ]
    _upsert(
        detector_collection,
        "detector_id",
        {
            "abstain_when": [
                "The target is not one answered analysis question with an exact scope-bound human Answer and a registered, digest-bound method-conflict binding.",
                "The report and source observations are absent, duplicated, disagree, or do not close through one exact selected-output writer graph.",
                "Any alternate requirement, amendment, approved deviation, conditional mismatch, sensitivity qualifier, or unsupported construct is present.",
            ],
            "accepted_assertion_classes": [
                "deterministic_derivation",
                "explicit_text_extraction",
            ],
            "applies_to_record_types": [
                "answer",
                "artifact",
                "file_record",
                "material_question",
                "operation",
                "publication_surface",
                "scientific_contract",
                "semantic_assertion",
            ],
            "assumptions": [],
            "counterevidence_protocol": [
                {
                    "applies_when": (
                        "One answered, explicitly registered analysis-method question is scheduled."
                    ),
                    "check_id": check_id,
                    "counterevidence_effect": "suppress_candidate",
                    "description": description,
                    "sources_to_search": [
                        "locked question, Answer, contract, assertions, and exact scope graph"
                    ],
                    "unavailability_effect": "block_finding",
                }
                for check_id, description in analysis_conflict_checks
            ],
            "coverage_contract": {
                "covered_when": (
                    "One exact human review requirement and every binding-required evidence-plane "
                    "operand resolve through the exact selected-analysis scope, and all ten finite "
                    "checks complete without a suppressor."
                ),
                "not_covered_when": (
                    "Any authority, uniqueness, corroboration, scope, identity, or finite-check "
                    "prerequisite is unavailable or unsupported."
                ),
                "partially_covered_when": (
                    "Not used by version 0.3.0; incomplete or conflicted records remain not covered."
                ),
            },
            "description": (
                "Compares one scope-bound human review requirement with identical operands from "
                "the evidence planes explicitly required by each content-addressed binding."
            ),
            "detector_family": "analysis_method_requirement_consistency",
            "detector_id": "detector:bounded-analysis-method-conflict",
            "detector_version": "0.3.0",
            "domains": ["domain_neutral_scientific_analysis"],
            "extensions": {
                "x-adr-ref": (
                    "docs/implementation/ADR-0042-MODULAR-METHOD-CHECK-EXTENSION-BOUNDARY.md"
                ),
                "x-implementation-resource": ("detectors/bounded_analysis_method_conflict.py"),
                "x-production-finding-permitted": False,
                "x-scientific-check-ids": ANALYSIS_METHOD_CONFLICT_CHECK_IDS,
            },
            "implementation": {
                "deterministic": True,
                "entry_point": (
                    "sc_referee.detectors.bounded_analysis_method_conflict:"
                    "BoundedAnalysisMethodConflictDetector"
                ),
                "implementation_digest": sha256_digest(analysis_conflict_resource.read_bytes()),
            },
            "issue_classes": ["x-review-scoped-analysis-method-requirement-mismatch"],
            "languages": ["markdown", "python", "r", "r_markdown"],
            "limitations": [
                "Experimental output cannot become a production Finding.",
                "Only scientific checks explicitly present in the content-addressed release binding registry are covered.",
                "No project execution, historical intent, numerical causality, universal method adequacy, or broader scientific correctness is established.",
            ],
            "maturity": "experimental",
            "permitted_output_types": ["disclosure"],
            "provenance": {
                "actor": {
                    "actor_id": "detector:bounded-analysis-method-conflict",
                    "actor_kind": "detector",
                },
                "created_at": GENERATED_AT,
                "method": "deterministic_detection",
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "record_type": "detector_manifest",
            "required_evidence": [
                "one exact answered analysis-scoped MaterialQuestion",
                "one scope-bound human Answer and controller-verified requirement",
                "one exact operand from every evidence plane declared by the registered binding",
                "one exact selected-analysis scope graph appropriate to those evidence planes",
                "ten completed finite counterevidence checks",
            ],
            "schema_version": SCHEMA_VERSION,
            "supported_operations": [
                "analysis_scoped_scientific_check_question_v1",
                "closed_method_comparison_algebra_v1",
                "exact_selected_output_writer_scope_v1",
                "posthoc_method_ledger_v1",
                "registered_typed_method_conflict_binding_v1",
                "scope_bound_structured_answer_v1",
            ],
            "test_fixtures": {
                "ambiguous": [
                    "tests/test_bounded_analysis_method_conflict.py::test_missing_scope_identity_suppresses_candidate"
                ],
                "counterevidence": [
                    "tests/test_bounded_analysis_method_conflict.py::test_each_finite_counterevidence_mutation_suppresses_candidate"
                ],
                "positive": [
                    "tests/test_bounded_analysis_method_conflict.py::test_exact_analysis_method_conflict_is_evaluation_only_and_replay_stable"
                ],
                "unsupported_path": [
                    "tests/test_bounded_analysis_method_conflict.py::test_non_allowlisted_question_is_an_unsupported_path"
                ],
                "verified_good_negative": [
                    "tests/test_bounded_analysis_method_conflict.py::test_matching_analysis_method_is_one_covered_negative"
                ],
            },
            "title": "Bounded analysis-method/review-requirement consistency",
            "validation": {
                "agent_adjudication_count": 0,
                "evaluation_ref": "adr:0040",
                "human_scientific_approval_count": 0,
                "qualification_record_ref": None,
                "qualification_review_basis": "not_qualified",
                "software_maintainer_approval_count": 0,
                "status": "development_only",
            },
            "wording_constraints": [
                "State only that the registered selected report and exactly scoped static-source method declaration differs from the scientist's requirement for this review.",
                "Do not claim that the source ran, that the declaration caused a numerical error, or that the scientist's requirement is universally scientifically correct.",
                "Do not describe an experimental evaluation candidate as a Finding.",
            ],
            "workflow_systems": [],
        },
    )
    feature_identity_resource = (
        ROOT / "src" / "sc_referee" / "detectors" / "feature_identifier_identity.py"
    )
    feature_identity_checks = [
        (
            "check:feature-identity-human-requirement",
            "Require one exact human Answer selecting exact identifier-set equality for this review.",
        ),
        (
            "check:feature-identity-material-inputs",
            "Require both declared artifacts to be selected full-digest material inputs.",
        ),
        (
            "check:feature-identity-unique-axes",
            "Require complete, nonempty, already-trimmed, unique identifier axes within finite ceilings.",
        ),
        (
            "check:feature-identity-alternate-mapping",
            "Suppress the candidate when a mapping, alias, normalization, or different-identifier relationship governs.",
        ),
        (
            "check:feature-identity-complete-comparison",
            "Require one complete exact set comparison rather than a sample or order comparison.",
        ),
    ]
    _upsert(
        detector_collection,
        "detector_id",
        {
            "abstain_when": [
                "The target is not one complete selected-feature-identifier deterministic observation with an exact linked MaterialQuestion.",
                "The scientist has not selected exact identifier-set equality for this review.",
                "Either selected artifact, identifier axis, full-digest identity, finite read, uniqueness check, or exact comparison is incomplete.",
                "A mapping, normalization, alias relation, duplicate identifier, malformed input, or unsupported H5AD field is present.",
            ],
            "accepted_assertion_classes": [
                "deterministic_derivation",
                "explicit_text_extraction",
            ],
            "applies_to_record_types": [
                "answer",
                "artifact",
                "deterministic_check_observation",
                "material_question",
                "publication_surface",
            ],
            "assumptions": [],
            "counterevidence_protocol": [
                {
                    "applies_when": (
                        "One complete nonconformant selected feature-identity observation is scheduled."
                    ),
                    "check_id": check_id,
                    "counterevidence_effect": "suppress_candidate",
                    "description": description,
                    "sources_to_search": [
                        "locked selected report declaration, full-digest material inputs, MaterialQuestion, human Answer, and deterministic observation"
                    ],
                    "unavailability_effect": "block_finding",
                }
                for check_id, description in feature_identity_checks
            ],
            "coverage_contract": {
                "covered_when": (
                    "One exact human equality requirement, two selected full-digest complete unique identifier axes, the no-normalization boundary, and the complete exact set comparison all resolve."
                ),
                "not_covered_when": (
                    "Any authority, selection, identity, parsing, uniqueness, mapping, or finite-comparison prerequisite is unavailable, conflicted, or unsupported."
                ),
                "partially_covered_when": (
                    "Not used by version 0.1.0; incomplete or conflicted targets remain not covered."
                ),
            },
            "description": (
                "Compares one complete selected delimited identifier column with one complete selected H5AD feature axis under an exact human review-scoped equality requirement."
            ),
            "detector_family": "data_identifier_identity_consistency",
            "detector_id": "detector:bounded-feature-identifier-identity",
            "detector_version": "0.1.0",
            "domains": ["domain_neutral_scientific_analysis"],
            "extensions": {
                "x-adr-ref": (
                    "docs/implementation/ADR-0058-SELECTED-FEATURE-IDENTIFIER-IDENTITY.md"
                ),
                "x-calculation-check-id": (
                    "calculation-check:selected-feature-identifier-identity-v1"
                ),
                "x-implementation-resource": "detectors/feature_identifier_identity.py",
                "x-production-finding-permitted": False,
            },
            "implementation": {
                "deterministic": True,
                "entry_point": (
                    "sc_referee.detectors.feature_identifier_identity:"
                    "BoundedFeatureIdentifierIdentityDetector"
                ),
                "implementation_digest": sha256_digest(feature_identity_resource.read_bytes()),
            },
            "issue_classes": ["x-feature-identifier-identity-conflict"],
            "languages": ["delimited_table", "h5ad"],
            "limitations": [
                "Experimental output cannot become a production Finding.",
                "Only one exact selected delimited column and H5AD var dataset under the closed declaration are covered.",
                "No producer lineage, historical intent, repair direction, biological meaning, execution, numerical impact, or publication invalidity is established.",
            ],
            "maturity": "experimental",
            "permitted_output_types": ["disclosure"],
            "provenance": {
                "actor": {
                    "actor_id": "detector:bounded-feature-identifier-identity",
                    "actor_kind": "detector",
                },
                "created_at": "2026-08-02T00:00:00Z",
                "method": "deterministic_detection",
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "record_type": "detector_manifest",
            "required_evidence": [
                "one closed selected feature-identity comparison declaration",
                "two exact full-digest selected material inputs",
                "one complete unique delimited identifier column and one complete unique H5AD var field",
                "one exact human Answer requiring identifier-set equality for this review",
                "five completed finite counterevidence checks",
            ],
            "schema_version": SCHEMA_VERSION,
            "supported_operations": [
                "bounded_complete_delimited_identifier_column_v1",
                "bounded_complete_h5ad_var_identifier_axis_v1",
                "exact_identifier_set_equality_v1",
                "feature_identifier_identity_requirement_answer_v1",
            ],
            "test_fixtures": {
                "ambiguous": [
                    "tests/test_feature_identifier_identity.py::test_retained_unknown_suppresses_candidate"
                ],
                "counterevidence": [
                    "tests/test_feature_identifier_identity.py::test_alternate_mapping_suppresses_candidate"
                ],
                "positive": [
                    "tests/test_feature_identifier_identity.py::test_answered_exact_mismatch_is_evaluation_only_and_replays"
                ],
                "unsupported_path": [
                    "tests/test_feature_identifier_identity.py::test_duplicate_identifiers_are_unsupported"
                ],
                "verified_good_negative": [
                    "tests/test_feature_identifier_identity.py::test_reordered_equal_sets_produce_no_adverse_assessment"
                ],
            },
            "title": "Bounded selected feature-identifier identity consistency",
            "validation": {
                "agent_adjudication_count": 0,
                "evaluation_ref": "adr:0058",
                "human_scientific_approval_count": 0,
                "qualification_record_ref": None,
                "qualification_review_basis": "not_qualified",
                "software_maintainer_approval_count": 0,
                "status": "development_only",
            },
            "wording_constraints": [
                "State only that the two exact selected complete identifier sets conflict with the human exact-equality requirement governing this review.",
                "Do not infer corruption, spreadsheet conversion, producer lineage, which side is authoritative, repair direction, biological meaning, execution, numerical impact, or publication invalidity.",
                "Do not describe an experimental evaluation candidate as a Finding.",
            ],
            "workflow_systems": [],
        },
    )
    _write("detector-manifests.json", detector_collection)

    profile_collection = _load("profile-manifests.json")
    python_profiles = [
        record
        for record in profile_collection.get("records", [])
        if record.get("profile_id") == "semantic-profile:python-bounded-static-inspection-v1"
    ]
    if len(python_profiles) != 1:
        raise ValueError("bounded Python static-inspection capability profile must be unique")
    python_profiles[0]["operation_scope"] = [
        "bounded_literal_filter_predicates",
        "bounded_literal_two_group_mean_difference",
        "bounded_linear_single_result_renderer_lineage",
        "python_ast_and_token_inventory",
        "static_literal_and_source_parent_relative_write_paths_v2",
    ]
    python_profiles[0]["known_gaps"] = [
        "No public detector manifest is attached to this profile.",
        "Package dispatch and scientific meaning are not inferred from call names.",
        "ADR-0039 adds one exact selected-output writer scope for an existing question-only adapter; it does not establish execution, primary-analysis status, numerical causality, or Finding authority.",
    ]
    expected_count_profiles = [
        record
        for record in profile_collection.get("records", [])
        if record.get("profile_id") == "semantic-profile:bounded-expected-count-method-contract-v1"
    ]
    if len(expected_count_profiles) != 1:
        raise ValueError("bounded expected-count capability profile must be unique")
    expected_count_profile = expected_count_profiles[0]
    expected_count_profile["operation_scope"] = [
        "bounded_expected_count_quantitative_sentence_v1",
        "bounded_expected_count_report_profile_v1",
        "bounded_expected_count_sensitivity_sentence_v1",
        "deterministic_expected_count_answer_derivation_v1",
        "expected_count_method_ledger_v1",
    ]
    expected_count_profile["known_gaps"] = [
        "The detector is experimental, unqualified, and cannot emit a production Finding.",
        "Only expected_count_background_v1 and exact closed report and Answer grammars are covered.",
        "Approximation tolerance, execution, numeric-cause attribution, and broader method adequacy remain unavailable.",
    ]
    _upsert(
        profile_collection,
        "profile_id",
        {
            "abstention_conditions": [
                "The closed declaration, exact human requirement, selected full-digest material inputs, complete unique axes, or exact set comparison is unavailable.",
                "A mapping, normalization, alias relation, duplicate identifier, unsupported H5AD field, malformed input, or finite ceiling is encountered.",
            ],
            "capability_entry_id": "capability:bounded-feature-identifier-identity-v1",
            "detector_refs": [
                {
                    "record_type": "detector_manifest",
                    "record_id": "detector:bounded-feature-identifier-identity",
                }
            ],
            "domain": "domain_neutral_scientific_analysis",
            "known_gaps": [
                "The detector is experimental, unqualified, and cannot emit a production Finding.",
                "Only exact set identity between one selected delimited column and one selected H5AD var dataset is covered.",
                "Mappings, normalization, duplicate identifiers, other data formats, producer lineage, biological meaning, and downstream impact remain unavailable.",
            ],
            "language": None,
            "operation_extraction": "complete_for_declared_forms",
            "operation_scope": [
                "bounded_complete_delimited_identifier_column_v1",
                "bounded_complete_h5ad_var_identifier_axis_v1",
                "exact_identifier_set_equality_v1",
                "feature_identifier_identity_requirement_answer_v1",
            ],
            "package": None,
            "parser_refs": [
                {
                    "record_id": "parser:selected-feature-identifier-axes",
                    "record_type": "parser_manifest",
                }
            ],
            "profile_id": "semantic-profile:bounded-feature-identifier-identity-v1",
            "semantic_modeling": "partial",
            "syntax_recognition": "complete_for_declared_forms",
            "version_manifest_ref": ("version-manifest:bounded-feature-identifier-identity-v1"),
        },
    )
    _upsert(
        profile_collection,
        "profile_id",
        {
            "abstention_conditions": [
                "The answered question has no exact content-addressed method-conflict binding in the locked scientific-check registry.",
                "The report/source operands or selected-output graph are incomplete, ambiguous, or lack full-digest identity.",
                "The human Answer does not establish one exact review-scoped requirement or any finite counterevidence check is unavailable.",
            ],
            "capability_entry_id": "capability:bounded-analysis-method-conflict-v1",
            "detector_refs": [
                {
                    "record_id": "detector:bounded-analysis-method-conflict",
                    "record_type": "detector_manifest",
                }
            ],
            "domain": "domain_neutral_scientific_analysis",
            "known_gaps": [
                "The detector is experimental, unqualified, and cannot emit a production Finding.",
                "The engine is structurally reusable, but release coverage remains limited to explicitly registered and independently qualified scientific checks.",
                "No execution, historical-intent, numeric-cause, universal-method, or domain-wide correctness claim is made.",
            ],
            "language": None,
            "operation_extraction": "partial",
            "operation_scope": [
                "analysis_scoped_scientific_check_question_v1",
                "closed_method_comparison_algebra_v1",
                "exact_selected_output_writer_scope_v1",
                "posthoc_method_ledger_v1",
                "registered_typed_method_conflict_binding_v1",
                "scope_bound_structured_answer_v1",
            ],
            "package": None,
            "parser_refs": [
                {
                    "record_id": "parser:markdown-inventory",
                    "record_type": "parser_manifest",
                },
                {
                    "record_id": "parser:python-ast-tokenize",
                    "record_type": "parser_manifest",
                },
            ],
            "profile_id": "semantic-profile:bounded-analysis-method-conflict-v1",
            "semantic_modeling": "partial",
            "syntax_recognition": "partial",
            "version_manifest_ref": "version-manifest:bounded-analysis-method-conflict-v1",
        },
    )
    _upsert(
        profile_collection,
        "profile_id",
        {
            "abstention_conditions": [
                "One completely inspected conventional task-like Markdown path does not request three role-bound mean log2(observed/expected) outputs.",
                "The selected report does not contain exactly one enumerated target-inclusive same-stratum mean, one value for every requested output, and one exact target-exclusion sensitivity.",
                "A supported complete expected-count declaration is present, the primary and sensitivity values are identical, or any required source is incomplete or ambiguous.",
            ],
            "capability_entry_id": "capability:bounded-expected-count-unresolved-obligation-v1",
            "detector_refs": [],
            "domain": "domain_neutral_scientific_analysis",
            "known_gaps": [
                "This profile emits only an analysis-scoped MaterialQuestion and cannot emit a candidate or Finding.",
                "It requires one conventional task-like Markdown path, three role-bound outputs, and one enumerated target-inclusion sensitivity.",
                "It does not choose an estimator, establish materiality, attribute numeric cause, execute project code, or cover general prose and formats.",
            ],
            "language": "markdown",
            "operation_extraction": "not_started",
            "operation_scope": ["bounded_expected_count_unresolved_obligation_v1"],
            "package": None,
            "parser_refs": [
                {
                    "record_id": "parser:markdown-inventory",
                    "record_type": "parser_manifest",
                }
            ],
            "profile_id": "semantic-profile:bounded-expected-count-unresolved-obligation-v1",
            "semantic_modeling": "partial",
            "syntax_recognition": "partial",
            "version_manifest_ref": (
                "version-manifest:bounded-expected-count-unresolved-obligation-v1"
            ),
        },
    )
    _upsert(
        profile_collection,
        "profile_id",
        {
            "abstention_conditions": [
                "The selected R Markdown source is not fully captured under immutable full-digest identity.",
                "The chunk inventory is malformed, incomplete, or requires rendered or runtime semantics.",
                "A conclusion requires general R parsing, package behavior, execution, or scientific interpretation.",
            ],
            "capability_entry_id": "capability:rmarkdown-selected-report-inventory-v1",
            "detector_refs": [],
            "domain": "domain_neutral_scientific_analysis",
            "known_gaps": [
                "The MVMR covariance module is separately pinned as question-only in the scientific-check release manifest and cannot emit a Finding.",
                "Exact active R chunks may delegate to existing bounded R adapters, but this does not claim general R Markdown, R, cross-chunk state, or package support.",
            ],
            "language": "r_markdown",
            "operation_extraction": "not_started",
            "operation_scope": ["bounded_rmarkdown_source_chunk_inventory_v2"],
            "package": None,
            "parser_refs": [
                {
                    "record_id": "parser:rmarkdown-selected-report-inventory",
                    "record_type": "parser_manifest",
                }
            ],
            "profile_id": "semantic-profile:rmarkdown-selected-report-inventory-v1",
            "semantic_modeling": "not_started",
            "syntax_recognition": "partial",
            "version_manifest_ref": "version-manifest:rmarkdown-selected-report-inventory-v1",
        },
    )
    r_parser_refs = [
        {
            "record_id": "parser:r-base-parse-data",
            "record_type": "parser_manifest",
        },
        {
            "record_id": "parser:r-tree-sitter-inventory",
            "record_type": "parser_manifest",
        },
    ]
    r_profiles = [
        (
            "deseq2",
            "DESeq2",
            [
                "r_literal_call_deseqdatasetfrommatrix_v1",
                "r_literal_call_deseq_v1",
                "r_literal_call_results_v1",
            ],
        ),
        (
            "edger",
            "edgeR",
            [
                "r_literal_call_dgelist_v1",
                "r_literal_call_filterbyexpr_v1",
                "r_literal_call_glmqlfit_v1",
                "r_literal_call_glmqlftest_v1",
            ],
        ),
        (
            "limma-voom",
            "limma",
            [
                "r_literal_call_dgelist_v1",
                "r_literal_call_filterbyexpr_v1",
                "r_literal_call_calcnormfactors_v1",
                "r_literal_call_voom_v1",
                "r_literal_call_lmfit_v1",
                "r_literal_call_ebayes_v1",
                "r_literal_call_toptable_v1",
            ],
        ),
    ]
    for profile_slug, package, operation_scope in r_profiles:
        _upsert(
            profile_collection,
            "profile_id",
            {
                "abstention_conditions": [
                    "The R source is not a regular strict-UTF-8 file within the finite parser ceilings.",
                    "The required call target is computed, package identity is implicit and ambiguous, or the two available parser inventories disagree.",
                    "A conclusion requires runtime dispatch, formula meaning, object provenance, dataflow, package behavior, execution, or scientific interpretation.",
                ],
                "capability_entry_id": f"capability:r-{profile_slug}-call-inventory-v1",
                "detector_refs": [],
                "domain": "bulk_rna_seq_differential_expression",
                "known_gaps": [
                    "This profile inventories only exact direct or literal namespace call syntax and argument names.",
                    "It does not determine whether the calls form a valid workflow, whether arguments have appropriate values, or whether the scientific analysis is correct.",
                    "No detector, question module, or Finding permission is attached.",
                ],
                "language": "r",
                "operation_extraction": "partial",
                "operation_scope": operation_scope,
                "package": package,
                "parser_refs": r_parser_refs,
                "profile_id": f"semantic-profile:r-{profile_slug}-call-inventory-v1",
                "semantic_modeling": "not_started",
                "syntax_recognition": "partial",
                "version_manifest_ref": f"version-manifest:r-{profile_slug}-call-inventory-v1",
            },
        )
    _upsert(
        profile_collection,
        "profile_id",
        {
            "abstention_conditions": [
                "The notebook is not a regular strict-UTF-8 nbformat 4 JSON file within every finite inventory ceiling.",
                "A cell identity, source, metadata object, execution-count literal, or saved-output shape is invalid or ambiguous.",
                "A conclusion requires code or Markdown parsing, output authenticity, execution order, hidden state, environment identity, rendering, or scientific meaning.",
            ],
            "capability_entry_id": "capability:jupyter-notebook-inventory-v1",
            "detector_refs": [],
            "domain": "domain_neutral_scientific_analysis",
            "known_gaps": [
                "This profile inventories only notebook cells and saved-output structure.",
                "Saved outputs are repository-supplied evidence and do not establish execution or result provenance.",
                "No Claim extractor, operation extractor, scientific-check module, detector, or Finding permission is attached.",
            ],
            "language": "jupyter_notebook",
            "operation_extraction": "not_started",
            "operation_scope": ["bounded_nbformat4_cell_output_inventory_v1"],
            "package": None,
            "parser_refs": [
                {
                    "record_id": "parser:jupyter-notebook-inventory",
                    "record_type": "parser_manifest",
                }
            ],
            "profile_id": "semantic-profile:jupyter-notebook-inventory-v1",
            "semantic_modeling": "not_started",
            "syntax_recognition": "partial",
            "version_manifest_ref": "version-manifest:jupyter-notebook-inventory-v1",
        },
    )
    _upsert(
        profile_collection,
        "profile_id",
        {
            "abstention_conditions": [
                "The source is not a regular strict-UTF-8 .qmd file within every finite inventory ceiling.",
                "Front matter, an admitted executable cell, or a literal cell identity is incomplete or ambiguous.",
                "A conclusion requires YAML, code, inline expression, rendering, execution, artifact lineage, or scientific meaning.",
            ],
            "capability_entry_id": "capability:quarto-source-inventory-v1",
            "detector_refs": [],
            "domain": "domain_neutral_scientific_analysis",
            "known_gaps": [
                "This profile inventories only front-matter, prose, and exact executable-cell boundaries.",
                "No Quarto project, render, kernel, extension, filter, include, operation, Claim, detector, or Finding authority is attached.",
            ],
            "language": "quarto",
            "operation_extraction": "not_started",
            "operation_scope": ["bounded_quarto_source_cell_inventory_v1"],
            "package": None,
            "parser_refs": [
                {
                    "record_id": "parser:quarto-source-inventory",
                    "record_type": "parser_manifest",
                }
            ],
            "profile_id": "semantic-profile:quarto-source-inventory-v1",
            "semantic_modeling": "not_started",
            "syntax_recognition": "partial",
            "version_manifest_ref": "version-manifest:quarto-source-inventory-v1",
        },
    )
    _upsert(
        profile_collection,
        "profile_id",
        {
            "abstention_conditions": [
                "The parent notebook, Quarto, or R Markdown inventory is incomplete, over budget, or cannot reverify the exact cell bytes.",
                "A notebook language declaration is absent, unsupported, or conflicting, or a Quarto cell engine is not exactly Python or R.",
                "A conclusion requires cross-cell state, execution, output provenance, rendering, a Claim, or scientific meaning.",
            ],
            "capability_entry_id": "capability:container-cell-static-language-bridge-v1",
            "detector_refs": [],
            "domain": "domain_neutral_scientific_analysis",
            "known_gaps": [
                "This profile delegates at most 200 recognized cells independently to the existing static Python or R parsers.",
                "It preserves container cell locations but does not establish cross-cell bindings, execution order, runtime behavior, or code-to-output provenance.",
                "ADR-0037 permits existing exact static adapters to inspect independently reverified cell bytes. ADR-0038 and ADR-0051 admit only exact selected-container or selected-analysis-source containment; they add no execution, primary-analysis, Claim, detector, or Finding authority.",
            ],
            "language": "container_cell",
            "operation_extraction": "partial",
            "operation_scope": [
                "bounded_container_cell_static_language_bridge_v2",
                "python_bounded_static_operation_inventory_v1",
                "r_direct_and_namespaced_call_inventory_v1",
            ],
            "package": None,
            "parser_refs": [
                {
                    "record_id": "parser:container-cell-language-bridge",
                    "record_type": "parser_manifest",
                }
            ],
            "profile_id": "semantic-profile:container-cell-static-language-bridge-v1",
            "semantic_modeling": "not_started",
            "syntax_recognition": "partial",
            "version_manifest_ref": "version-manifest:container-cell-static-language-bridge-v1",
        },
    )
    _write("profile-manifests.json", profile_collection)

    version_collection = _load("version-manifests.json")
    _upsert(
        version_collection,
        "version_manifest_id",
        {
            "evidence_refs": [
                "docs/implementation/ADR-0058-SELECTED-FEATURE-IDENTIFIER-IDENTITY.md",
                "src/sc_referee/calculation_checks/feature_identifier_identity.py",
                "src/sc_referee/detectors/feature_identifier_identity.py",
                "tests/test_feature_identifier_identity.py",
            ],
            "inferred_compatibility": [],
            "known_gaps": [
                "No CSV, TSV, HDF5, AnnData, h5py, or producer-version envelope has independent qualification evidence."
            ],
            "profile_ref": "semantic-profile:bounded-feature-identifier-identity-v1",
            "tested_versions": [],
            "version_manifest_id": ("version-manifest:bounded-feature-identifier-identity-v1"),
        },
    )
    tabular_versions = [
        record
        for record in version_collection.get("records", [])
        if record.get("version_manifest_id")
        == "version-manifest:tabular-delimited-header-inventory-v1"
    ]
    if len(tabular_versions) != 1:
        raise ValueError("tabular delimited version manifest must be unique")
    tabular_versions[0]["evidence_refs"] = [
        "docs/implementation/ADR-0054-BOUNDED-GZIP-DELIMITED-HEADER-INVENTORY.md",
        "src/sc_referee/delimited_io.py",
        "src/sc_referee/tabular_inventory.py",
        "tests/test_tabular_inventory.py",
        "tests/test_capability_matrix.py",
    ]
    tabular_versions[0]["known_gaps"] = [
        "No release-qualified CSV, TSV, or gzip version/dialect envelope is published.",
        "Only first-record header inventory is qualified; gzip bodies and full compressed calculation inputs remain unsupported.",
    ]
    expected_count_versions = [
        record
        for record in version_collection.get("records", [])
        if record.get("version_manifest_id")
        == "version-manifest:bounded-expected-count-method-contract-v1"
    ]
    if len(expected_count_versions) != 1:
        raise ValueError("bounded expected-count version manifest must be unique")
    expected_count_versions[0]["evidence_refs"] = [
        "docs/implementation/ADR-0018-BOUNDED-INTENDED-VS-REPORTED-METHOD-CONFLICT.md",
        "tests/test_bounded_reported_method_contract.py",
    ]
    python_versions = [
        record
        for record in version_collection.get("records", [])
        if record.get("version_manifest_id")
        == "version-manifest:python-bounded-static-inspection-v1"
    ]
    if len(python_versions) != 1:
        raise ValueError("bounded Python static-inspection version manifest must be unique")
    python_versions[0]["evidence_refs"] = [
        "docs/implementation/ADR-0039-EXACT-SELECTED-OUTPUT-WRITER-SCOPE-JOIN.md",
        "src/sc_referee/parsers/python_ast.py",
        "tests/test_python_parser.py",
        "tests/test_scientific_check_integration.py",
        "tests/test_interaction_protocol.py",
    ]
    _upsert(
        version_collection,
        "version_manifest_id",
        {
            "evidence_refs": [
                "docs/implementation/ADR-0040-BOUNDED-ANALYSIS-METHOD-CONFLICT-EVALUATION.md",
                "src/sc_referee/detectors/bounded_analysis_method_conflict.py",
                "tests/test_bounded_analysis_method_conflict.py",
                "tests/test_interaction_protocol.py",
            ],
            "inferred_compatibility": [],
            "known_gaps": [
                "No language, workflow-system, scientific-domain, or method-family version envelope has independent qualification evidence."
            ],
            "profile_ref": "semantic-profile:bounded-analysis-method-conflict-v1",
            "tested_versions": [],
            "version_manifest_id": "version-manifest:bounded-analysis-method-conflict-v1",
        },
    )
    _upsert(
        version_collection,
        "version_manifest_id",
        {
            "evidence_refs": [
                "docs/implementation/ADR-0018-BOUNDED-INTENDED-VS-REPORTED-METHOD-CONFLICT.md",
                "docs/implementation/EXPERIMENT-0025-ITERATIVE-ANSWER-ISOLATED-CAPABILITY-DEVELOPMENT.md",
                "src/sc_referee/expected_count_obligation.py",
                "tests/test_general_audit.py",
                "tests/test_interaction_protocol.py",
            ],
            "inferred_compatibility": [],
            "known_gaps": [
                "No Markdown version, scientific domain, method family beyond the two enumerated target-inclusive mean forms, or workflow system has independent qualification evidence."
            ],
            "profile_ref": "semantic-profile:bounded-expected-count-unresolved-obligation-v1",
            "tested_versions": [],
            "version_manifest_id": (
                "version-manifest:bounded-expected-count-unresolved-obligation-v1"
            ),
        },
    )
    _upsert(
        version_collection,
        "version_manifest_id",
        {
            "evidence_refs": [
                "docs/implementation/ADR-0021-RMARKDOWN-MVMR-COVARIANCE-CHECK.md",
                "docs/implementation/EXPERIMENT-0022-EXTERNAL-RMARKDOWN-ADAPTER-CONNECTIVITY.md",
                "tests/test_rmarkdown_parser.py",
                "tests/test_scientific_check_integration.py",
            ],
            "inferred_compatibility": [],
            "known_gaps": [
                "No release-qualified R Markdown, knitr, R, or MVMR package version envelope is published."
            ],
            "profile_ref": "semantic-profile:rmarkdown-selected-report-inventory-v1",
            "tested_versions": [],
            "version_manifest_id": "version-manifest:rmarkdown-selected-report-inventory-v1",
        },
    )
    for profile_slug, package, _operation_scope in r_profiles:
        _upsert(
            version_collection,
            "version_manifest_id",
            {
                "evidence_refs": [
                    "docs/implementation/ADR-0033-DUAL-R-INVENTORY-AND-FIRST-BULK-RNASEQ-PROFILE.md",
                    "src/sc_referee/parsers/r_dual.py",
                    "tests/test_r_parser.py",
                    "tests/test_capability_matrix.py",
                ],
                "inferred_compatibility": [],
                "known_gaps": [
                    f"No {package} package release has independent qualification evidence; package versions and compatibility are not claimed."
                ],
                "profile_ref": f"semantic-profile:r-{profile_slug}-call-inventory-v1",
                "tested_versions": [],
                "version_manifest_id": f"version-manifest:r-{profile_slug}-call-inventory-v1",
            },
        )
    _upsert(
        version_collection,
        "version_manifest_id",
        {
            "evidence_refs": [
                "docs/implementation/ADR-0034-BOUNDED-JUPYTER-NOTEBOOK-INVENTORY.md",
                "src/sc_referee/parsers/jupyter_inventory.py",
                "tests/test_jupyter_parser.py",
                "tests/test_capability_matrix.py",
            ],
            "inferred_compatibility": [],
            "known_gaps": [
                "No Jupyter frontend, kernel, language, extension, widget, or notebook minor version has independent qualification evidence."
            ],
            "profile_ref": "semantic-profile:jupyter-notebook-inventory-v1",
            "tested_versions": [],
            "version_manifest_id": "version-manifest:jupyter-notebook-inventory-v1",
        },
    )
    _upsert(
        version_collection,
        "version_manifest_id",
        {
            "evidence_refs": [
                "docs/implementation/ADR-0035-BOUNDED-QUARTO-SOURCE-INVENTORY.md",
                "src/sc_referee/parsers/quarto_inventory.py",
                "tests/test_quarto_parser.py",
                "tests/test_capability_matrix.py",
            ],
            "inferred_compatibility": [],
            "known_gaps": [
                "No Quarto, Pandoc, kernel, extension, filter, or output-format version has independent qualification evidence."
            ],
            "profile_ref": "semantic-profile:quarto-source-inventory-v1",
            "tested_versions": [],
            "version_manifest_id": "version-manifest:quarto-source-inventory-v1",
        },
    )
    _upsert(
        version_collection,
        "version_manifest_id",
        {
            "evidence_refs": [
                "docs/implementation/ADR-0036-BOUNDED-CONTAINER-CELL-LANGUAGE-BRIDGE.md",
                "docs/implementation/ADR-0037-CELL-AWARE-SCIENTIFIC-EVIDENCE-CONTRACT.md",
                "docs/implementation/ADR-0038-SELECTED-CONTAINER-CELL-SCOPE-JOIN.md",
                "docs/implementation/ADR-0051-BOUNDED-CONTAINER-SOURCE-CELL-CONNECTIVITY.md",
                "src/sc_referee/parsers/cell_language_bridge.py",
                "tests/test_cell_language_bridge.py",
                "tests/test_cell_scientific_evidence.py",
                "tests/test_capability_matrix.py",
            ],
            "inferred_compatibility": [],
            "known_gaps": [
                "No Jupyter, Quarto, R Markdown, Python, R, kernel, package, or cell-order version envelope has independent qualification evidence."
            ],
            "profile_ref": "semantic-profile:container-cell-static-language-bridge-v1",
            "tested_versions": [],
            "version_manifest_id": "version-manifest:container-cell-static-language-bridge-v1",
        },
    )
    _write("version-manifests.json", version_collection)

    for collection_name in ("parser-manifests.json", "detector-manifests.json"):
        public_collection = _load(collection_name)
        records = public_collection.get("records")
        if not isinstance(records, list):
            raise ValueError(f"{collection_name} requires a records array")
        for record in records:
            if not isinstance(record, dict):
                raise ValueError(f"{collection_name} contains a malformed record")
            record["schema_version"] = SCHEMA_VERSION
            extensions = record.get("extensions")
            resource = (
                extensions.get("x-implementation-resource")
                if isinstance(extensions, dict)
                else None
            )
            if collection_name == "parser-manifests.json" and isinstance(resource, str):
                record["implementation_digest"] = sha256_digest(
                    (ROOT / "src" / "sc_referee" / resource).read_bytes()
                )
        _write(collection_name, public_collection)

    manifest_set = _load("manifest-set.json")
    manifest_set["schema_version"] = SCHEMA_VERSION
    manifest_set["generated_at"] = GENERATED_AT
    for descriptor in manifest_set["collections"]:
        path = MANIFEST_ROOT / descriptor["path"]
        descriptor["digest"] = sha256_digest(path.read_bytes())
    _write("manifest-set.json", manifest_set)


if __name__ == "__main__":
    main()
