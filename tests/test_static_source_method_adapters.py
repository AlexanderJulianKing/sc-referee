from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.parsers.python_ast import inspect_python_source
from sc_referee.parsers.r_dual import inspect_r_source
from sc_referee.scientific_checks import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenSourceLocation,
    InspectionDocument,
    RecordRef,
    ScientificCheckRegistry,
    ScopeJoinEdge,
    ScopeJoinProof,
    StaticScopeJoinGraph,
)
from sc_referee.scientific_checks.profiles import scientific_check_release_registry
from sc_referee.scientific_checks.scope_joins import (
    CELL_SOURCE_PROFILE,
    PUBLICATION_PROFILE,
    REVIEW_SELECTION_PROFILES,
)
from sc_referee.scientific_checks.static_source_adapter import StaticSourceMethodAdapter

COPY_CHECK = "check:classifier-derived-copy-dosage-representation"
LD_CHECK = "check:ld-covariance-whitening-before-robust-fit"
EXPECTED = "continuous_posterior_expected_copy_dosage"
HARD = "integer_hard_copy_state_as_numeric_dosage"
CONTINUOUS = "direct_continuous_calibrated_copy_dosage"
WHITENED = "ld_covariance_cholesky_whitening_before_robust_fit"
SNAPSHOT_DIGEST = sha256_digest("static-source-adapter-test-snapshot")
CORPUS_ROOT = Path(__file__).resolve().parents[1] / "evaluation" / "static-source-adapter-v1"

PYTHON_EXPECTED = b"""\
from sklearn.linear_model import LogisticRegression
import numpy as np

classifier = LogisticRegression().fit(features, states)
probabilities = classifier.predict_proba(features)
copy_states = np.array([0, 1, 2])
segment_copy_dosage = probabilities @ copy_states
"""

PYTHON_CONTINUOUS_ALIAS = b"""\
from sklearn.linear_model import RidgeCV as Calibrator

calibrator = Calibrator(alphas=[0.1, 1.0]).fit(features, copy_index)
segment_copy_dosage = calibrator.predict(features)
"""

PYTHON_HARD = b"""\
from sklearn.linear_model import LogisticRegression

classifier = LogisticRegression().fit(features, states)
segment_copy_dosage = classifier.predict(features)
"""

PYTHON_LD_ALIAS = b"""\
from numpy.linalg import cholesky as factor_covariance
from numpy.linalg import solve as triangular_solve
from statsmodels.api import RLM as robust_fit
from statsmodels.robust.norms import TukeyBiweight as redescending_norm

factor = factor_covariance(ld_covariance)
y_white = triangular_solve(factor, outcome_innovations)
x_white = triangular_solve(factor, exposure_innovations)
fit = robust_fit(y_white, x_white, M=redescending_norm())
"""

R_EXPECTED = b"""\
classifier <- nnet::multinom(copy_state ~ marker_1 + marker_2, data=training)
probabilities <- stats::predict(classifier, newdata=cohort, type="probs")
copy_states <- base::c(0, 1, 2)
segment_copy_dosage <- probabilities %*% copy_states
"""

R_HARD_ALIAS = b"""\
classifier <- nnet::multinom(copy_state ~ marker_1 + marker_2, data=training)
predict_copy <- stats::predict
segment_copy_dosage <- predict_copy(classifier, newdata=cohort, type="class")
"""

R_LD_DIRECT = b"""\
library(MASS)
factor <- chol(ld_covariance)
y_white <- forwardsolve(factor, outcome_innovations)
x_white <- forwardsolve(factor, exposure_innovations)
fit <- rlm(y=y_white, x=x_white, psi=psi.bisquare)
"""

R_LD_NAMESPACED_FORMULA = b"""\
factor <- base::chol(ld_covariance)
y_white <- base::forwardsolve(factor, outcome_innovations)
x_white <- base::forwardsolve(factor, exposure_innovations)
fit <- MASS::rlm(y_white ~ 0 + x_white, psi=MASS::psi.bisquare)
"""


def _module(check_id: str):  # type: ignore[no-untyped-def]
    return next(
        module
        for module in scientific_check_release_registry().modules
        if module.manifest.check_id == check_id
    )


def _adapter(check_id: str, language: str) -> StaticSourceMethodAdapter:
    matches = [
        adapter
        for adapter in _module(check_id).adapters
        if isinstance(adapter, StaticSourceMethodAdapter) and adapter.language == language
    ]
    assert len(matches) == 1
    return matches[0]


def _proof(source: RecordRef, target: RecordRef, profile: str) -> ScopeJoinProof:
    return ScopeJoinProof.create(
        edge=ScopeJoinEdge(source, "selected_for_static_method_review", target),
        profile=profile,
        evidence_refs=(source, target),
        evidence_payload_digests=(sha256_digest(f"{source.record_id}:{target.record_id}"),),
        snapshot_digest=SNAPSHOT_DIGEST,
        authority_limitations=(
            "This exact static selection does not establish execution or scientific correctness.",
        ),
    )


def _context(
    payload: bytes,
    language: str,
    *,
    scoped: bool = True,
    parser_mutation: dict[str, Any] | None = None,
    report: bytes | None = None,
) -> FrozenInspectionContext:
    surface_ref = RecordRef("publication_surface", "publication-surface:source-test")
    artifact_ref = RecordRef("artifact", "artifact:report")
    identity_ref = RecordRef("asset_identity", "asset-identity:report")
    source_file_ref = RecordRef("file_record", "file:analysis-source")
    source_path = "analysis.py" if language == "python" else "analysis.R"
    if language == "python":
        parser_result = inspect_python_source(
            payload,
            Path(source_path),
            "audit:static-source-test",
            source_path=source_path,
        )
    else:
        parser_result, _ = inspect_r_source(
            payload,
            Path(source_path),
            "audit:static-source-test",
            source_path=source_path,
            r_executable="",
        )
    if parser_mutation:
        parser_result = {**parser_result, **parser_mutation}
    source_parser_ref = RecordRef("parser_result", str(parser_result["parser_result_id"]))
    parser_payload = canonical_json(parser_result).encode()
    documents = [
        InspectionDocument(
            path=source_path,
            file_ref=source_file_ref,
            content=payload,
            content_digest=sha256_digest(payload),
            media_type="text/x-python" if language == "python" else "text/x-r",
            parser_result_ref=source_parser_ref,
            parser_result_payload=parser_payload,
            parser_result_digest=sha256_digest(parser_payload),
        )
    ]
    report_digest = sha256_digest(report or b"unselected placeholder")
    base_records = [
        FrozenBaseRecord.from_record(
            surface_ref,
            {
                "publication_surface_id": surface_ref.record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [artifact_ref.to_dict()]},
            },
        ),
        FrozenBaseRecord.from_record(
            artifact_ref,
            {
                "artifact_id": artifact_ref.record_id,
                "kind": "report",
                "path": "report.md",
                "asset_identity_ref": identity_ref.to_dict(),
            },
        ),
        FrozenBaseRecord.from_record(
            identity_ref,
            {
                "asset_identity_id": identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": artifact_ref.to_dict(),
                "identity_evidence": {"kind": "full_digest", "digest": report_digest},
            },
        ),
        FrozenBaseRecord.from_record(
            source_file_ref, {"file_record_id": source_file_ref.record_id, "path": source_path}
        ),
        FrozenBaseRecord.from_record(source_parser_ref, parser_result),
    ]
    proofs = []
    if scoped:
        proofs.append(
            _proof(
                source_file_ref,
                surface_ref,
                REVIEW_SELECTION_PROFILES["analysis_source"],
            )
        )
    if report is not None:
        report_file_ref = RecordRef("file_record", "file:report")
        report_parser_ref = RecordRef("parser_result", "parser-result:report")
        report_parser = {
            "parser_result_id": report_parser_ref.record_id,
            "parser_id": "parser:markdown-inventory",
            "parser_version": "0.2.0",
            "state": "parsed",
        }
        report_parser_payload = canonical_json(report_parser).encode()
        documents.append(
            InspectionDocument(
                path="report.md",
                file_ref=report_file_ref,
                content=report,
                content_digest=report_digest,
                media_type="text/markdown",
                parser_result_ref=report_parser_ref,
                parser_result_payload=report_parser_payload,
                parser_result_digest=sha256_digest(report_parser_payload),
            )
        )
        base_records.extend(
            (
                FrozenBaseRecord.from_record(
                    report_file_ref,
                    {"file_record_id": report_file_ref.record_id, "path": "report.md"},
                ),
                FrozenBaseRecord.from_record(report_parser_ref, report_parser),
            )
        )
        proofs.append(_proof(artifact_ref, surface_ref, PUBLICATION_PROFILE))
    graph = StaticScopeJoinGraph(
        snapshot_digest=SNAPSHOT_DIGEST,
        proofs=tuple(sorted(proofs, key=lambda item: canonical_json(item.to_dict()))),
    )
    return FrozenInspectionContext(
        snapshot_digest=SNAPSHOT_DIGEST,
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=tuple(documents),
        base_records=tuple(sorted(base_records, key=lambda item: item.ref)),
        scope_join_graph=graph,
    )


def _selected_container_cell_context(
    payload: bytes,
    language: str,
    *,
    line_offset: int = 9,
    cell_identity: str = "method",
    execution_state: str = "unspecified",
    execution_value: int | None = None,
) -> FrozenInspectionContext:
    context = _context(payload, language, scoped=False)
    document = context.documents[0]
    assert document.parser_result_payload is not None
    assert document.parser_result_ref is not None
    parser_result = json.loads(document.parser_result_payload)
    container_path = "analysis.ipynb" if language == "python" else "analysis.Rmd"
    source_kind = "notebook_cell" if language == "python" else "document_chunk"
    source_ref: dict[str, Any] = {
        "source_kind": source_kind,
        "locator": f"{container_path}#cell={cell_identity}:code:10-20",
        "path": container_path,
        "content_digest": sha256_digest(b"container bytes"),
        "start_line": 10,
        "end_line": 20,
    }
    if language == "python":
        source_ref.update({"cell_id": cell_identity, "selector": "id"})
        execution_kind = "saved_execution_count"
        line_offset = 0
    else:
        source_ref["chunk_label"] = cell_identity
        execution_kind = "rmarkdown_eval_option"
    parser_result["source_ref"] = source_ref
    parser_result.setdefault("extensions", {})["x-virtual-source"] = {
        "profile": "bounded-container-cell-static-language-bridge-v2",
        "bridge_version": "0.2.0",
        "container_parser_result_id": "parser-result:container",
        "language": language,
        "source_digest": sha256_digest(payload),
        "source_ref": source_ref,
        "execution_declaration": {
            "kind": execution_kind,
            "state": execution_state,
            **({"value": execution_value} if execution_value is not None else {}),
            "establishes_execution": False,
        },
        "executes_project_code": False,
    }
    parser_payload = canonical_json(parser_result).encode()
    source_location = FrozenSourceLocation.from_source_ref(source_ref)
    virtual_document = replace(
        document,
        path=container_path,
        parser_result_payload=parser_payload,
        parser_result_digest=sha256_digest(parser_payload),
        source_location=source_location,
        line_offset=line_offset,
    )
    proofs = (
        _proof(document.parser_result_ref, document.file_ref, CELL_SOURCE_PROFILE),
        _proof(
            document.file_ref,
            context.selected_surface_ref,
            REVIEW_SELECTION_PROFILES["analysis_source"],
        ),
    )
    graph = StaticScopeJoinGraph(
        snapshot_digest=SNAPSHOT_DIGEST,
        proofs=tuple(sorted(proofs, key=lambda item: canonical_json(item.to_dict()))),
    )
    return replace(context, documents=(virtual_document,), scope_join_graph=graph)


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (PYTHON_EXPECTED, EXPECTED),
        (PYTHON_CONTINUOUS_ALIAS, CONTINUOUS),
        (PYTHON_HARD, HARD),
    ],
)
def test_python_copy_dosage_calls_and_aliases_normalize_existing_operands(
    payload: bytes, expected: str
) -> None:
    observation = _adapter(COPY_CHECK, "python").inspect(_context(payload, "python"))

    assert observation.applicability == "applicable"
    assert observation.observed_operand is not None
    assert observation.observed_operand.value == expected
    assert observation.evidence_plane == "static_source"
    assert observation.output_ceiling == "question_only"


@pytest.mark.parametrize(
    ("payload", "expected"),
    [(R_EXPECTED, EXPECTED), (R_HARD_ALIAS, HARD)],
)
def test_r_namespaced_calls_and_closed_namespace_aliases_normalize_existing_operands(
    payload: bytes, expected: str
) -> None:
    observation = _adapter(COPY_CHECK, "r").inspect(_context(payload, "r"))

    assert observation.applicability == "applicable"
    assert observation.observed_operand is not None
    assert observation.observed_operand.value == expected


def test_python_and_r_copy_formulas_are_cross_language_equivalent() -> None:
    python = _adapter(COPY_CHECK, "python").inspect(_context(PYTHON_EXPECTED, "python"))
    r = _adapter(COPY_CHECK, "r").inspect(_context(R_EXPECTED, "r"))

    assert python.observed_operand == r.observed_operand


@pytest.mark.parametrize(
    ("language", "payload"),
    [
        ("python", PYTHON_LD_ALIAS),
        ("r", R_LD_DIRECT),
        ("r", R_LD_NAMESPACED_FORMULA),
    ],
)
def test_ld_calls_method_arguments_and_formulas_normalize_whitening(
    language: str, payload: bytes
) -> None:
    observation = _adapter(LD_CHECK, language).inspect(_context(payload, language))

    assert observation.applicability == "applicable"
    assert observation.observed_operand is not None
    assert observation.observed_operand.value == WHITENED


def test_selected_rmarkdown_cell_contributes_scoped_observation_and_exact_citation() -> None:
    observation = _adapter(LD_CHECK, "r").inspect(
        _selected_container_cell_context(R_LD_DIRECT, "r")
    )

    assert observation.applicability == "applicable"
    assert observation.observed_operand is not None
    assert observation.observed_operand.value == WHITENED
    assert [edge.relation for edge in observation.scope_join_path] == [
        "contained_in_selected_analysis_source",
        "selected_analysis_source_for_review",
    ]
    assert observation.evidence_spans[0].path == "analysis.Rmd"
    assert observation.evidence_spans[0].content_digest == sha256_digest(b"container bytes")
    assert observation.evidence_spans[0].start_line >= 10


def test_cross_cell_hidden_state_and_saved_execution_order_do_not_create_operand() -> None:
    first = _selected_container_cell_context(
        b"from sklearn.linear_model import LogisticRegression\n"
        b"classifier = LogisticRegression().fit(features, states)\n"
        b"probabilities = classifier.predict_proba(features)\n",
        "python",
        cell_identity="later-saved-count",
        execution_state="literal",
        execution_value=20,
    )
    second = _selected_container_cell_context(
        b"copy_states = [0, 1, 2]\nsegment_copy_dosage = probabilities @ copy_states\n",
        "python",
        cell_identity="earlier-saved-count",
        execution_state="literal",
        execution_value=3,
        line_offset=30,
    )
    assert first.scope_join_graph is not None
    assert second.scope_join_graph is not None
    proofs_by_digest = {
        semantic_digest(proof.to_dict()): proof
        for proof in (
            *first.scope_join_graph.proofs,
            *second.scope_join_graph.proofs,
        )
    }
    graph = StaticScopeJoinGraph(
        snapshot_digest=SNAPSHOT_DIGEST,
        proofs=tuple(
            sorted(proofs_by_digest.values(), key=lambda item: canonical_json(item.to_dict()))
        ),
    )
    forward = replace(
        first,
        documents=(first.documents[0], second.documents[0]),
        scope_join_graph=graph,
    )
    reversed_cells = replace(
        first,
        documents=(second.documents[0], first.documents[0]),
        scope_join_graph=graph,
    )

    forward_observation = _adapter(COPY_CHECK, "python").inspect(forward)
    reversed_observation = _adapter(COPY_CHECK, "python").inspect(reversed_cells)

    assert forward_observation.applicability == "unsupported"
    assert forward_observation.observed_operand is None
    assert reversed_observation.applicability == "unsupported"
    assert reversed_observation.observed_operand is None


def test_shadowing_forces_local_unsupported_state() -> None:
    payload = PYTHON_EXPECTED + b"\nnp = object()\n"
    observation = _adapter(COPY_CHECK, "python").inspect(_context(payload, "python"))

    assert observation.applicability == "unsupported"
    assert observation.observed_operand is None
    assert "shadowed" in (observation.abstention_reason or "")


def test_dynamic_dispatch_does_not_create_an_operand() -> None:
    payload = b"""\
classifier = build_classifier()
predictor = getattr(classifier, "predict_proba")
probabilities = predictor(features)
copy_states = [0, 1, 2]
segment_copy_dosage = probabilities @ copy_states
"""
    observation = _adapter(COPY_CHECK, "python").inspect(_context(payload, "python"))

    assert observation.applicability == "unsupported"
    assert observation.observed_operand is None


def test_method_defining_branch_forces_abstention() -> None:
    payload = b"""\
from sklearn.linear_model import LogisticRegression
classifier = LogisticRegression().fit(features, states)
if use_hard_calls:
    segment_copy_dosage = classifier.predict(features)
"""
    observation = _adapter(COPY_CHECK, "python").inspect(_context(payload, "python"))

    assert observation.applicability == "unsupported"
    assert "branch-dependent" in (observation.abstention_reason or "")


def test_competing_source_operands_remain_ambiguous() -> None:
    payload = PYTHON_EXPECTED + b"\nsegment_copy_dosage = classifier.predict(features)\n"
    observation = _adapter(COPY_CHECK, "python").inspect(_context(payload, "python"))

    assert observation.applicability == "ambiguous"
    assert observation.observed_operand is None


def test_r_cross_parser_disagreement_forces_abstention() -> None:
    observation = _adapter(COPY_CHECK, "r").inspect(
        _context(
            R_EXPECTED,
            "r",
            parser_mutation={
                "state": "partially_parsed",
                "parser_disagreement": "injected call inventory disagreement",
            },
        )
    )

    assert observation.applicability == "unsupported"
    assert observation.observed_operand is None
    assert "parser" in (observation.abstention_reason or "").casefold()


def test_exact_unscoped_source_operand_is_preserved_only_as_suppressor() -> None:
    observation = _adapter(COPY_CHECK, "python").inspect(
        _context(PYTHON_EXPECTED, "python", scoped=False)
    )

    assert observation.applicability == "unsupported"
    assert observation.observed_operand is not None
    assert observation.observed_operand.value == EXPECTED
    assert observation.scope_join_path == ()


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            b"The full-cohort representation is continuous posterior expected copy dosage, "
            b"P(copy=1) + 2*P(copy=2), not an integer hard call.\n",
            "applicable",
        ),
        (
            b"The primary downstream association used an integer hard-call copy state, which "
            b"was treated directly as numeric dosage.\n",
            "ambiguous",
        ),
    ],
)
def test_report_and_source_agreement_or_disagreement_uses_existing_reducer(
    report_text: bytes, expected_state: str
) -> None:
    module = _module(COPY_CHECK)
    registry = ScientificCheckRegistry((module,))
    result = registry.evaluate(_context(PYTHON_EXPECTED, "python", report=report_text)).modules[0]

    assert result.state == expected_state
    assert result.adapter_failures == ()


@pytest.mark.parametrize(
    ("check_id", "payload"),
    [(COPY_CHECK, PYTHON_EXPECTED), (LD_CHECK, PYTHON_LD_ALIAS)],
)
def test_removing_source_adapters_changes_only_the_source_evidence_plane(
    check_id: str, payload: bytes
) -> None:
    module = _module(check_id)
    report_only = replace(
        module,
        adapter_manifests=tuple(
            item for item in module.adapter_manifests if item.evidence_plane == "reported_text"
        ),
        adapters=tuple(
            item for item in module.adapters if not isinstance(item, StaticSourceMethodAdapter)
        ),
    )
    context = _context(payload, "python")

    full = ScientificCheckRegistry((module,)).evaluate(context).modules[0]
    removed = ScientificCheckRegistry((report_only,)).evaluate(context).modules[0]

    assert full.state == "applicable"
    assert removed.state == "unsupported"
    assert {item.evidence_plane for item in full.observations} == {
        "reported_text",
        "static_source",
    }
    assert {item.evidence_plane for item in removed.observations} == {"reported_text"}


def test_static_source_grammar_digest_is_stable_and_identity_free() -> None:
    adapters = [
        _adapter(COPY_CHECK, "python"),
        _adapter(COPY_CHECK, "r"),
        _adapter(LD_CHECK, "python"),
        _adapter(LD_CHECK, "r"),
    ]

    assert len({item.recognition_grammar_digest for item in adapters}) == 4
    projection = canonical_json(
        {
            "digests": [item.recognition_grammar_digest for item in adapters],
            "ids": [item.adapter_id for item in adapters],
        }
    )
    assert "GeneBench" not in projection
    assert "structural-v2" not in projection
    assert all(item.implementation_digest.startswith("sha256:") for item in adapters)


def test_parser_payload_mutation_changes_context_identity() -> None:
    original = _context(PYTHON_EXPECTED, "python")
    mutated = _context(
        PYTHON_EXPECTED,
        "python",
        parser_mutation={"extensions": {"x-test-mutation": True}},
    )

    assert original.context_digest != mutated.context_digest
    assert semantic_digest(original.to_manifest_projection()) == original.context_digest
    assert json.loads(mutated.documents[0].parser_result_payload or b"{}")["extensions"] == {
        "x-test-mutation": True
    }


def test_frozen_static_source_corpus_identity_and_authority_ceiling() -> None:
    manifest = json.loads((CORPUS_ROOT / "manifest.json").read_text(encoding="utf-8"))
    projection = copy.deepcopy(manifest)
    recorded_digest = projection.pop("manifest_digest")

    assert manifest["qualification_use_permitted"] is False
    assert semantic_digest(projection) == recorded_digest
    assert len(manifest["cases"]) == 2
    for case in manifest["cases"]:
        path = CORPUS_ROOT / case["path"]
        assert path.is_file()
        assert sha256_digest(path.read_bytes()) == case["content_digest"]
        assert case["content_digest"] == case["origin_source_digest"]
        assert case["benchmark_derived"] is True
        assert case["qualification_status"] == "excluded"


@pytest.mark.parametrize(
    ("case_id", "expected_operand"),
    [
        (
            "static-source:structural-copy:posterior-expected",
            EXPECTED,
        ),
        (
            "static-source:structural-copy:direct-continuous",
            CONTINUOUS,
        ),
    ],
)
def test_frozen_real_structural_sources_normalize_without_repository_identity(
    case_id: str, expected_operand: str
) -> None:
    manifest = json.loads((CORPUS_ROOT / "manifest.json").read_text(encoding="utf-8"))
    case = next(item for item in manifest["cases"] if item["case_id"] == case_id)
    payload = (CORPUS_ROOT / case["path"]).read_bytes()

    observation = _adapter(COPY_CHECK, "python").inspect(_context(payload, "python"))

    assert observation.applicability == case["expected_applicability"]
    assert observation.observed_operand is not None
    assert observation.observed_operand.value == expected_operand


def test_full_nonexecuting_audit_routes_static_source_question_and_replays_exactly(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    report = b"# Static source review\n\nThe quantitative representation needs review.\n"
    (repository / "report.md").write_bytes(report)
    source = (
        PYTHON_EXPECTED
        + b"""\
from pathlib import Path
Path("report.md").write_text("# Static source review\\n", encoding="utf-8")
"""
    )
    (repository / "analysis.py").write_bytes(source)

    bundle = run_audit(
        repository,
        tmp_path / "audit",
        schema_root,
        report="report.md",
    )
    question_ids = {
        item.get("extensions", {}).get("x-scientific-check-id")
        for item in bundle["material_questions"]
    }

    assert COPY_CHECK in question_ids
    assert bundle["findings"] == []
    assert bundle["executions"] == []
    assert bundle["project_execution_authorizations"] == []
    assert bundle["performance_records"][0]["model_usage"]["calls"] == 0
    lock = json.loads((tmp_path / "audit" / "semantic.lock.json").read_text())
    assert lock["model_access_after_lock"] is False
    replayed = replay(
        tmp_path / "audit" / "semantic.lock.json",
        tmp_path / "replay",
        schema_root,
    )
    assert replayed["material_questions"] == bundle["material_questions"]
    assert replayed["findings"] == []
