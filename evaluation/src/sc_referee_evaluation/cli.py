from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.detectors.admission import AdmissionContext
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee_evaluation.analysis_method_qualification import (
    AnalysisMethodQualificationError,
    freeze_bounded_analysis_method_profile,
    freeze_protocol_artifact,
    verify_bounded_analysis_method_case,
)
from sc_referee_evaluation.candidate import (
    EvaluationCandidateProjectionError,
    project_evaluation_candidate,
)
from sc_referee_evaluation.capture import (
    ReviewCaptureError,
    capture_review_submission,
    load_review_capture,
)
from sc_referee_evaluation.comparison import DetectorComparisonError, compare_detector_output
from sc_referee_evaluation.corpus import (
    CorpusPreflightError,
    preflight_genebench_public_package,
)
from sc_referee_evaluation.fixture import (
    FixtureGenerationError,
    FixtureProofInputs,
    generate_ambiguous_fixture,
    generate_control_fixture,
    generate_positive_fixture,
    generate_static_control_fixture,
)
from sc_referee_evaluation.genebench_grader import (
    GeneBenchNumericGradeError,
    grade_genebench_public_answer,
    grade_genebench_public_numeric_answer,
)
from sc_referee_evaluation.genebench_workspace import (
    GeneBenchWorkspaceError,
    prepare_genebench_public_case,
)
from sc_referee_evaluation.grader import ExactJsonGraderError, grade_exact_json_output
from sc_referee_evaluation.method_contract_diagnostic import (
    MethodContractDiagnosticError,
    diagnose_genebench_method_contract_conflict,
)
from sc_referee_evaluation.metrics import QualificationMetricError, build_qualification_metric_set
from sc_referee_evaluation.posthoc_review import (
    PosthocValidationReviewError,
    build_posthoc_validation_review,
)
from sc_referee_evaluation.qualification_adapter_registry import (
    registered_qualification_adapter,
)
from sc_referee_evaluation.review_protocol import (
    ReviewProtocolError,
    build_stage1_review_packet,
    build_stage2_review_packet,
    freeze_scientific_label,
    freeze_stage1_panel,
)
from sc_referee_evaluation.root_cause import (
    RootCauseReconciliationError,
    build_adjudicated_root_cause,
)
from sc_referee_evaluation.source_method_probe import (
    SourceMethodProbeError,
    probe_python_method_shapes,
)
from sc_referee_evaluation.stage3 import (
    Stage3ProtocolError,
    build_stage3_review_packet,
    reconcile_detector_case,
)
from sc_referee_evaluation.static_qualification import (
    StaticQualificationError,
    freeze_bounded_direction_profile,
    verify_bounded_direction_case,
)
from sc_referee_evaluation.typed_method_qualification import (
    TypedMethodQualificationError,
    freeze_typed_method_profile,
    revalidate_registered_typed_method_proof,
    verify_registered_typed_method_case,
)
from sc_referee_evaluation.validation import EvaluationValidationError, validate_case_packet
from sc_referee_evaluation.workspace import BlindWorkspaceError, build_blind_workspace

_PROTOCOL_VERSION = "0.2.0"
_Handler = Callable[[argparse.Namespace], Path]


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        handler: _Handler = arguments.handler
        output = handler(arguments)
    except (
        BlindWorkspaceError,
        CorpusPreflightError,
        GeneBenchWorkspaceError,
        GeneBenchNumericGradeError,
        MethodContractDiagnosticError,
        SourceMethodProbeError,
        PosthocValidationReviewError,
        DetectorComparisonError,
        EvaluationValidationError,
        EvaluationCandidateProjectionError,
        ExactJsonGraderError,
        FixtureGenerationError,
        ReviewProtocolError,
        RootCauseReconciliationError,
        Stage3ProtocolError,
        ReviewCaptureError,
        QualificationMetricError,
        StaticQualificationError,
        AnalysisMethodQualificationError,
        TypedMethodQualificationError,
        json.JSONDecodeError,
        OSError,
        TypeError,
    ) as error:
        print(f"sc-referee-eval: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {output}")
    return 0


def entrypoint() -> None:
    raise SystemExit(main())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sc-referee-eval",
        description="Operate the isolated answer-side qualification protocol.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    corpus_preflight = commands.add_parser("preflight-genebench-public")
    corpus_preflight.add_argument("--package-root", required=True)
    corpus_preflight.add_argument("--source-revision", required=True)
    corpus_preflight.add_argument("--expected-manifest-digest", required=True)
    corpus_preflight.add_argument("--expected-checksums-digest", required=True)
    corpus_preflight.add_argument("--output", required=True)
    corpus_preflight.set_defaults(handler=_corpus_preflight_command)

    corpus_case = commands.add_parser("prepare-genebench-public-case")
    corpus_case.add_argument("--package-root", required=True)
    corpus_case.add_argument("--preflight", required=True)
    corpus_case.add_argument("--eval-id", required=True)
    corpus_case.add_argument("--created-at", required=True)
    corpus_case.add_argument("--output-root", required=True)
    corpus_case.set_defaults(handler=_genebench_case_command)

    validate = commands.add_parser("validate-case")
    validate.add_argument("--fixture", required=True)
    validate.add_argument("--adjudication", required=True)
    validate.add_argument("--reviews-jsonl", required=True)
    validate.add_argument("--adjudicated-root-causes-jsonl")
    validate.add_argument("--schema-root", required=True)
    validate.add_argument("--output", required=True)
    validate.add_argument("--snapshot")
    validate.add_argument("--file-records-jsonl")
    validate.add_argument("--asset-identities-jsonl")
    validate.add_argument("--materialized-root")
    validate.set_defaults(handler=_validate_case_command)

    workspace = commands.add_parser("build-workspace")
    workspace.add_argument("--source-root", required=True)
    workspace.add_argument("--snapshot", required=True)
    workspace.add_argument("--file-records-jsonl", required=True)
    workspace.add_argument("--asset-identities-jsonl", required=True)
    workspace.add_argument("--created-at", required=True)
    workspace.add_argument("--destination", required=True)
    workspace.add_argument("--spec", required=True)
    workspace.add_argument("--manifest", required=True)
    workspace.set_defaults(handler=_build_workspace_command)

    stage1_packet = commands.add_parser("stage1-packet")
    stage1_packet.add_argument("--case-id", required=True)
    stage1_packet.add_argument("--workspace-manifest", required=True)
    stage1_packet.add_argument("--reviewer-agent", required=True)
    stage1_packet.add_argument("--prompt", required=True)
    stage1_packet.add_argument("--created-at", required=True)
    stage1_packet.add_argument("--output", required=True)
    stage1_packet.set_defaults(handler=_stage1_packet_command)

    stage1_freeze = commands.add_parser("freeze-stage1")
    stage1_freeze.add_argument("--capture", action="append", required=True)
    stage1_freeze.add_argument("--schema-root", required=True)
    stage1_freeze.add_argument("--frozen-at", required=True)
    stage1_freeze.add_argument("--output", required=True)
    stage1_freeze.set_defaults(handler=_stage1_freeze_command)

    capture = commands.add_parser("capture-review")
    capture.add_argument("--review", required=True)
    capture.add_argument("--packet", required=True)
    capture.add_argument("--transcript", required=True)
    capture.add_argument("--schema-root", required=True)
    capture.add_argument("--captured-at", required=True)
    capture.add_argument("--destination", required=True)
    capture.set_defaults(handler=_capture_review_command)

    stage2_packet = commands.add_parser("stage2-packet")
    stage2_packet.add_argument("--stage1-freeze", required=True)
    stage2_packet.add_argument("--stage1-capture", action="append", required=True)
    stage2_packet.add_argument("--schema-root", required=True)
    stage2_packet.add_argument("--reviewer-agent", required=True)
    stage2_packet.add_argument("--prompt", required=True)
    stage2_packet.add_argument("--evidence-spec", required=True)
    stage2_packet.add_argument("--created-at", required=True)
    stage2_packet.add_argument("--output", required=True)
    stage2_packet.set_defaults(handler=_stage2_packet_command)

    reconcile = commands.add_parser("reconcile-root-cause")
    reconcile.add_argument("--stage1-capture", action="append", required=True)
    reconcile.add_argument("--stage2-capture", action="append", required=True)
    reconcile.add_argument("--schema-root", required=True)
    reconcile.add_argument("--resolution-spec", required=True)
    reconcile.add_argument("--adjudicated-at", required=True)
    reconcile.add_argument("--output", required=True)
    reconcile.set_defaults(handler=_reconcile_root_cause_command)

    label_freeze = commands.add_parser("freeze-label")
    label_freeze.add_argument("--adjudication", required=True)
    label_freeze.add_argument("--stage1-freeze", required=True)
    label_freeze.add_argument("--stage1-capture", action="append", required=True)
    label_freeze.add_argument("--stage2-capture", action="append", required=True)
    label_freeze.add_argument("--adjudicated-root-cause", action="append")
    label_freeze.add_argument("--schema-root", required=True)
    label_freeze.add_argument("--frozen-at", required=True)
    label_freeze.add_argument("--output", required=True)
    label_freeze.set_defaults(handler=_label_freeze_command)

    label_replay = commands.add_parser("replay-label-freeze")
    label_replay.add_argument("--source-label-freeze", required=True)
    label_replay.add_argument("--adjudication", required=True)
    label_replay.add_argument("--stage1-freeze", required=True)
    label_replay.add_argument("--stage1-capture", action="append", required=True)
    label_replay.add_argument("--stage2-capture", action="append", required=True)
    label_replay.add_argument("--adjudicated-root-cause", action="append")
    label_replay.add_argument("--schema-root", required=True)
    label_replay.add_argument("--output", required=True)
    label_replay.set_defaults(handler=_label_replay_command)

    comparison = commands.add_parser("compare-stage3")
    comparison.add_argument("--fixture", required=True)
    comparison.add_argument("--adjudication", required=True)
    comparison.add_argument("--label-freeze", required=True)
    comparison.add_argument("--audit-bundle", required=True)
    comparison.add_argument("--detector-id", required=True)
    comparison.add_argument("--schema-root", required=True)
    comparison.add_argument("--compared-at", required=True)
    comparison.add_argument("--output", required=True)
    comparison.set_defaults(handler=_comparison_command)

    candidate = commands.add_parser("project-candidate")
    _add_candidate_projection_arguments(candidate, replay=False)
    candidate.set_defaults(handler=_candidate_projection_command)

    candidate_replay = commands.add_parser("replay-candidate")
    _add_candidate_projection_arguments(candidate_replay, replay=True)
    candidate_replay.set_defaults(handler=_candidate_replay_command)

    stage3_packet = commands.add_parser("stage3-packet")
    stage3_packet.add_argument("--fixture", required=True)
    stage3_packet.add_argument("--adjudication", required=True)
    stage3_packet.add_argument("--stage1-freeze", required=True)
    stage3_packet.add_argument("--label-freeze", required=True)
    stage3_packet.add_argument("--audit-bundle", required=True)
    stage3_packet.add_argument("--candidate", action="append")
    stage3_packet.add_argument("--adjudicated-root-cause", action="append")
    stage3_packet.add_argument("--detector-id", required=True)
    stage3_packet.add_argument("--reviewer-agent", required=True)
    stage3_packet.add_argument("--prompt", required=True)
    stage3_packet.add_argument("--schema-root", required=True)
    stage3_packet.add_argument("--created-at", required=True)
    stage3_packet.add_argument("--output", required=True)
    stage3_packet.set_defaults(handler=_stage3_packet_command)

    stage3_reconcile = commands.add_parser("reconcile-stage3")
    _add_stage3_reconciliation_arguments(stage3_reconcile, require_reconciled_at=True)
    stage3_reconcile.set_defaults(handler=_stage3_reconcile_command)

    stage3_replay = commands.add_parser("replay-stage3")
    _add_stage3_reconciliation_arguments(stage3_replay, require_reconciled_at=False)
    stage3_replay.add_argument("--source-outcome", required=True)
    stage3_replay.set_defaults(handler=_stage3_replay_command)

    metrics = commands.add_parser("calculate-metrics")
    _add_metric_arguments(metrics, replay=False)
    metrics.set_defaults(handler=_metrics_command)

    metrics_replay = commands.add_parser("replay-metrics")
    _add_metric_arguments(metrics_replay, replay=True)
    metrics_replay.set_defaults(handler=_metrics_replay_command)

    grader = commands.add_parser("grade-json")
    grader.add_argument("--fixture", required=True)
    grader.add_argument("--adjudication", required=True)
    grader.add_argument("--snapshot", required=True)
    grader.add_argument("--file-records-jsonl", required=True)
    grader.add_argument("--asset-identities-jsonl", required=True)
    grader.add_argument("--materialized-root", required=True)
    grader.add_argument("--grader-spec", required=True)
    grader.add_argument("--schema-root", required=True)
    grader.add_argument("--graded-at", required=True)
    grader.add_argument("--output", required=True)
    grader.set_defaults(handler=_grader_command)

    genebench_grader = commands.add_parser("grade-genebench-public-numeric")
    genebench_grader.add_argument("--package-root", required=True)
    genebench_grader.add_argument("--preflight", required=True)
    genebench_grader.add_argument("--eval-id", required=True)
    genebench_grader.add_argument("--audit-root", required=True)
    genebench_grader.add_argument("--schema-root", required=True)
    genebench_grader.add_argument("--graded-at", required=True)
    genebench_grader.add_argument("--output", required=True)
    genebench_grader.set_defaults(handler=_genebench_grader_command)

    genebench_answer_grader = commands.add_parser("grade-genebench-public-answer")
    genebench_answer_grader.add_argument("--package-root", required=True)
    genebench_answer_grader.add_argument("--preflight", required=True)
    genebench_answer_grader.add_argument("--eval-id", required=True)
    genebench_answer_grader.add_argument("--audit-root", required=True)
    genebench_answer_grader.add_argument("--schema-root", required=True)
    genebench_answer_grader.add_argument("--graded-at", required=True)
    genebench_answer_grader.add_argument("--output", required=True)
    genebench_answer_grader.set_defaults(handler=_genebench_answer_grader_command)

    method_diagnostic = commands.add_parser("diagnose-genebench-method-contract")
    method_diagnostic.add_argument("--audit-root", required=True)
    method_diagnostic.add_argument("--schema-root", required=True)
    method_diagnostic.add_argument("--reference-profile", required=True)
    method_diagnostic.add_argument("--reference-id", required=True)
    method_diagnostic.add_argument("--reference-content-digest", required=True)
    method_diagnostic.add_argument("--diagnosed-at", required=True)
    method_diagnostic.add_argument("--output", required=True)
    method_diagnostic.set_defaults(handler=_method_contract_diagnostic_command)

    source_method_probe = commands.add_parser("probe-python-method-shapes")
    source_method_probe.add_argument("--source-root", required=True)
    source_method_probe.add_argument("--source", required=True)
    source_method_probe.add_argument("--profile", action="append", required=True)
    source_method_probe.add_argument("--reference-id", required=True)
    source_method_probe.add_argument("--reference-content-digest", required=True)
    source_method_probe.add_argument("--diagnosed-at", required=True)
    source_method_probe.add_argument("--output", required=True)
    source_method_probe.set_defaults(handler=_source_method_probe_command)

    posthoc_review = commands.add_parser("compile-posthoc-validation-review")
    posthoc_review.add_argument("--source-probe", required=True)
    posthoc_review.add_argument("--review-spec", required=True)
    posthoc_review.add_argument("--reviewed-at", required=True)
    posthoc_review.add_argument("--output", required=True)
    posthoc_review.set_defaults(handler=_posthoc_validation_review_command)

    positive_fixture = commands.add_parser("generate-positive-fixture")
    positive_fixture.add_argument("--adjudication", required=True)
    positive_fixture.add_argument("--stage1-capture", action="append", required=True)
    positive_fixture.add_argument("--stage2-capture", action="append", required=True)
    positive_fixture.add_argument("--stage1-freeze", required=True)
    positive_fixture.add_argument("--workspace-manifest", action="append", required=True)
    positive_fixture.add_argument("--adjudicated-root-cause", action="append", required=True)
    positive_fixture.add_argument("--snapshot", required=True)
    positive_fixture.add_argument("--file-records-jsonl", required=True)
    positive_fixture.add_argument("--asset-identities-jsonl", required=True)
    positive_fixture.add_argument("--materialized-root", required=True)
    positive_fixture.add_argument("--fixture-spec", required=True)
    positive_fixture.add_argument("--schema-root", required=True)
    positive_fixture.add_argument("--created-at", required=True)
    positive_fixture.add_argument("--output", required=True)
    positive_fixture.set_defaults(handler=_positive_fixture_command)

    control_fixture = commands.add_parser("generate-control-fixture")
    control_fixture.add_argument("--adjudication", required=True)
    control_fixture.add_argument("--stage1-capture", action="append", required=True)
    control_fixture.add_argument("--stage2-capture", action="append", required=True)
    control_fixture.add_argument("--stage1-freeze", required=True)
    control_fixture.add_argument("--workspace-manifest", action="append", required=True)
    control_fixture.add_argument("--snapshot", required=True)
    control_fixture.add_argument("--file-records-jsonl", required=True)
    control_fixture.add_argument("--asset-identities-jsonl", required=True)
    control_fixture.add_argument("--materialized-root", required=True)
    control_fixture.add_argument("--scientific-contract", action="append", required=True)
    control_fixture.add_argument("--operation", action="append", required=True)
    control_fixture.add_argument("--environment", action="append", required=True)
    control_fixture.add_argument("--execution", action="append", required=True)
    control_fixture.add_argument("--sandbox-capability", action="append")
    control_fixture.add_argument("--evidence-record", action="append")
    control_fixture.add_argument("--fixture-spec", required=True)
    control_fixture.add_argument("--schema-root", required=True)
    control_fixture.add_argument("--created-at", required=True)
    control_fixture.add_argument("--output", required=True)
    control_fixture.set_defaults(handler=_control_fixture_command)

    static_profile = commands.add_parser("freeze-static-profile")
    static_profile.add_argument("--detector-manifest", required=True)
    static_profile.add_argument("--parser-manifest", action="append", required=True)
    static_profile.add_argument("--semantic-profile-manifest", action="append", required=True)
    static_profile.add_argument("--version-manifest", action="append", required=True)
    static_profile.add_argument("--selection-protocol-artifact", required=True)
    static_profile.add_argument("--frozen-at", required=True)
    static_profile.add_argument("--max-candidate-files", type=int, default=1000)
    static_profile.add_argument("--max-total-bytes", type=int, default=10_000_000)
    static_profile.add_argument("--max-recursion-depth", type=int, default=32)
    static_profile.add_argument("--max-elapsed-milliseconds", type=int, default=5000)
    static_profile.add_argument("--output", required=True)
    static_profile.set_defaults(handler=_static_profile_command)

    static_proof = commands.add_parser("verify-static-case")
    static_proof.add_argument("--materialized-root", required=True)
    static_proof.add_argument("--profile", required=True)
    static_proof.add_argument("--detector-manifest", required=True)
    static_proof.add_argument("--parser-manifest", action="append", required=True)
    static_proof.add_argument("--semantic-profile-manifest", action="append", required=True)
    static_proof.add_argument("--version-manifest", action="append", required=True)
    static_proof.add_argument("--case-assignment-artifact", required=True)
    static_proof.add_argument("--label-freeze-artifact", required=True)
    static_proof.add_argument("--snapshot", required=True)
    static_proof.add_argument("--file-records-jsonl", required=True)
    static_proof.add_argument("--asset-identities-jsonl", required=True)
    static_proof.add_argument("--proof-frozen-at", required=True)
    static_proof.add_argument("--output", required=True)
    static_proof.set_defaults(handler=_static_proof_command)

    method_profile = commands.add_parser("freeze-analysis-method-static-profile")
    method_profile.add_argument("--detector-manifest", required=True)
    method_profile.add_argument("--parser-manifest", action="append", required=True)
    method_profile.add_argument("--semantic-profile-manifest", action="append", required=True)
    method_profile.add_argument("--version-manifest", action="append", required=True)
    method_profile.add_argument("--selection-protocol-artifact", required=True)
    method_profile.add_argument("--frozen-at", required=True)
    method_profile.add_argument("--max-candidate-files", type=int, default=1000)
    method_profile.add_argument("--max-total-bytes", type=int, default=10_000_000)
    method_profile.add_argument("--max-recursion-depth", type=int, default=32)
    method_profile.add_argument("--max-elapsed-milliseconds", type=int, default=5000)
    method_profile.add_argument("--output", required=True)
    method_profile.set_defaults(handler=_analysis_method_static_profile_command)

    method_assignment = commands.add_parser("assign-analysis-method-static-case")
    method_assignment.add_argument("--profile", required=True)
    method_assignment.add_argument("--case-id", required=True)
    method_assignment.add_argument("--selected-report", required=True)
    method_assignment.add_argument("--assigned-at", required=True)
    method_assignment.add_argument("--output", required=True)
    method_assignment.set_defaults(handler=_analysis_method_static_assignment_command)

    method_proof = commands.add_parser("verify-analysis-method-static-case")
    method_proof.add_argument("--materialized-root", required=True)
    method_proof.add_argument("--profile", required=True)
    method_proof.add_argument("--detector-manifest", required=True)
    method_proof.add_argument("--parser-manifest", action="append", required=True)
    method_proof.add_argument("--semantic-profile-manifest", action="append", required=True)
    method_proof.add_argument("--version-manifest", action="append", required=True)
    method_proof.add_argument("--case-assignment-artifact", required=True)
    method_proof.add_argument("--label-freeze-artifact", required=True)
    method_proof.add_argument("--snapshot", required=True)
    method_proof.add_argument("--file-records-jsonl", required=True)
    method_proof.add_argument("--asset-identities-jsonl", required=True)
    method_proof.add_argument("--material-questions-jsonl", required=True)
    method_proof.add_argument("--answers-jsonl", required=True)
    method_proof.add_argument("--scientific-contracts-jsonl", required=True)
    method_proof.add_argument("--semantic-assertions-jsonl", required=True)
    method_proof.add_argument("--proof-frozen-at", required=True)
    method_proof.add_argument("--output", required=True)
    method_proof.set_defaults(handler=_analysis_method_static_proof_command)

    typed_method_profile = commands.add_parser("freeze-typed-method-static-profile")
    typed_method_profile.add_argument("--method-binding", required=True)
    typed_method_profile.add_argument("--detector-manifest", required=True)
    typed_method_profile.add_argument("--parser-manifest", action="append", required=True)
    typed_method_profile.add_argument("--semantic-profile-manifest", action="append", required=True)
    typed_method_profile.add_argument("--version-manifest", action="append", required=True)
    typed_method_profile.add_argument("--selection-protocol-artifact", required=True)
    typed_method_profile.add_argument("--candidate-suffix", action="append", required=True)
    typed_method_profile.add_argument("--frozen-at", required=True)
    typed_method_profile.add_argument("--max-candidate-files", type=int, default=1000)
    typed_method_profile.add_argument("--max-total-bytes", type=int, default=10_000_000)
    typed_method_profile.add_argument("--max-recursion-depth", type=int, default=32)
    typed_method_profile.add_argument("--max-elapsed-milliseconds", type=int, default=5000)
    typed_method_profile.add_argument("--output", required=True)
    typed_method_profile.set_defaults(handler=_typed_method_static_profile_command)

    typed_method_assignment = commands.add_parser("assign-typed-method-static-case")
    typed_method_assignment.add_argument("--profile", required=True)
    typed_method_assignment.add_argument("--case-id", required=True)
    typed_method_assignment.add_argument("--selected-report", required=True)
    typed_method_assignment.add_argument("--assigned-at", required=True)
    typed_method_assignment.add_argument("--output", required=True)
    typed_method_assignment.set_defaults(handler=_typed_method_static_assignment_command)

    typed_method_proof = commands.add_parser("verify-typed-method-static-case")
    _add_typed_method_proof_arguments(typed_method_proof, replay=False)
    typed_method_proof.set_defaults(handler=_typed_method_static_proof_command)

    typed_method_replay = commands.add_parser("replay-typed-method-static-case")
    _add_typed_method_proof_arguments(typed_method_replay, replay=True)
    typed_method_replay.set_defaults(handler=_typed_method_static_replay_command)

    static_fixture = commands.add_parser("generate-static-control-fixture")
    static_fixture.add_argument("--adjudication", required=True)
    static_fixture.add_argument("--stage1-capture", action="append", required=True)
    static_fixture.add_argument("--stage2-capture", action="append", required=True)
    static_fixture.add_argument("--stage1-freeze", required=True)
    static_fixture.add_argument("--workspace-manifest", action="append", required=True)
    static_fixture.add_argument("--snapshot", required=True)
    static_fixture.add_argument("--file-records-jsonl", required=True)
    static_fixture.add_argument("--asset-identities-jsonl", required=True)
    static_fixture.add_argument("--materialized-root", required=True)
    static_fixture.add_argument("--scientific-contract", action="append", required=True)
    static_fixture.add_argument("--material-question", action="append")
    static_fixture.add_argument("--answer", action="append")
    static_fixture.add_argument("--semantic-assertion", action="append")
    static_fixture.add_argument("--operation", action="append", required=True)
    static_fixture.add_argument("--evidence-record", action="append")
    static_fixture.add_argument("--static-profile", required=True)
    static_fixture.add_argument("--static-proof", required=True)
    static_fixture.add_argument("--case-assignment-artifact", required=True)
    static_fixture.add_argument("--static-label-freeze-artifact", required=True)
    static_fixture.add_argument("--scientific-label-freeze", required=True)
    static_fixture.add_argument("--detector-manifest", required=True)
    static_fixture.add_argument("--parser-manifest", action="append", required=True)
    static_fixture.add_argument("--semantic-profile-manifest", action="append", required=True)
    static_fixture.add_argument("--version-manifest", action="append", required=True)
    static_fixture.add_argument("--fixture-spec", required=True)
    static_fixture.add_argument("--schema-root", required=True)
    static_fixture.add_argument("--created-at", required=True)
    static_fixture.add_argument("--output", required=True)
    static_fixture.set_defaults(handler=_static_fixture_command)

    fixture = commands.add_parser("generate-ambiguous-fixture")
    fixture.add_argument("--adjudication", required=True)
    fixture.add_argument("--snapshot", required=True)
    fixture.add_argument("--file-records-jsonl", required=True)
    fixture.add_argument("--asset-identities-jsonl", required=True)
    fixture.add_argument("--fixture-spec", required=True)
    fixture.add_argument("--schema-root", required=True)
    fixture.add_argument("--created-at", required=True)
    fixture.add_argument("--output", required=True)
    fixture.set_defaults(handler=_fixture_command)
    return parser


def _corpus_preflight_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    preflight_genebench_public_package(
        Path(arguments.package_root),
        source_revision=str(arguments.source_revision),
        expected_manifest_digest=str(arguments.expected_manifest_digest),
        expected_checksums_digest=str(arguments.expected_checksums_digest),
        output=output,
    )
    return output


def _genebench_case_command(arguments: argparse.Namespace) -> Path:
    output_root = Path(arguments.output_root)
    prepare_genebench_public_case(
        Path(arguments.package_root),
        _load_object(Path(arguments.preflight)),
        str(arguments.eval_id),
        output_root,
        created_at=str(arguments.created_at),
    )
    return output_root / "case-preparation.json"


def _validate_case_command(arguments: argparse.Namespace) -> Path:
    output = _absent_output(arguments.output)
    fixture_path = Path(arguments.fixture)
    adjudication_path = Path(arguments.adjudication)
    reviews_path = Path(arguments.reviews_jsonl)
    optional = _optional_snapshot_arguments(arguments)
    report = validate_case_packet(
        _load_object(fixture_path),
        _load_object(adjudication_path),
        _load_jsonl(reviews_path),
        Path(arguments.schema_root),
        adjudicated_root_causes=(
            _load_jsonl(Path(arguments.adjudicated_root_causes_jsonl))
            if arguments.adjudicated_root_causes_jsonl
            else []
        ),
        snapshot=_load_object(optional["snapshot"]) if optional else None,
        file_records=_load_jsonl(optional["file_records"]) if optional else None,
        asset_identities=_load_jsonl(optional["asset_identities"]) if optional else None,
        materialized_root=optional.get("materialized_root") if optional else None,
    )
    report["evaluation_protocol_version"] = _PROTOCOL_VERSION
    input_paths = {
        "fixture": fixture_path,
        "adjudication": adjudication_path,
        "reviews": reviews_path,
        **optional,
    }
    if arguments.adjudicated_root_causes_jsonl:
        input_paths["adjudicated_root_causes"] = Path(arguments.adjudicated_root_causes_jsonl)
    report["input_digests"] = {
        role: sha256_digest(path.read_bytes())
        for role, path in sorted(input_paths.items())
        if role != "materialized_root"
    }
    report["validation_report_digest"] = semantic_digest(report)
    write_normalized_json_once(output, report)
    return output


def _build_workspace_command(arguments: argparse.Namespace) -> Path:
    spec = _load_object(Path(arguments.spec))
    files = _list_of_objects(spec.get("files"), "workspace files")
    typed_files = [
        {"path": str(item.get("path", "")), "role": str(item.get("role", ""))} for item in files
    ]
    manifest = Path(arguments.manifest)
    build_blind_workspace(
        Path(arguments.source_root),
        Path(arguments.destination),
        manifest,
        typed_files,
        snapshot=_load_object(Path(arguments.snapshot)),
        file_records=_load_jsonl(Path(arguments.file_records_jsonl)),
        asset_identities=_load_jsonl(Path(arguments.asset_identities_jsonl)),
        created_at=str(arguments.created_at),
        forbidden_source_paths=_string_set(spec.get("forbidden_source_paths", [])),
        forbidden_markers=_string_set(spec.get("forbidden_markers", [])),
        forbidden_digests=_string_set(spec.get("forbidden_digests", [])),
    )
    return manifest


def _stage1_packet_command(arguments: argparse.Namespace) -> Path:
    output = _absent_output(arguments.output)
    packet = build_stage1_review_packet(
        str(arguments.case_id),
        _load_object(Path(arguments.workspace_manifest)),
        _load_object(Path(arguments.reviewer_agent)),
        Path(arguments.prompt).read_text(encoding="utf-8"),
        created_at=str(arguments.created_at),
    )
    write_normalized_json_once(output, packet)
    return output


def _stage1_freeze_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    reviews, packets, manifests = _load_captures(
        arguments.capture, Path(arguments.schema_root), "stage1_blind"
    )
    freeze_stage1_panel(
        reviews,
        packets,
        manifests,
        Path(arguments.schema_root),
        frozen_at=str(arguments.frozen_at),
        output=output,
    )
    return output


def _capture_review_command(arguments: argparse.Namespace) -> Path:
    destination = Path(arguments.destination)
    capture_review_submission(
        _load_object(Path(arguments.review)),
        _load_object(Path(arguments.packet)),
        Path(arguments.transcript),
        Path(arguments.schema_root),
        captured_at=str(arguments.captured_at),
        destination=destination,
    )
    return destination / "capture.manifest.json"


def _stage2_packet_command(arguments: argparse.Namespace) -> Path:
    output = _absent_output(arguments.output)
    evidence = _load_object(Path(arguments.evidence_spec))
    stage1_reviews, _packets, _manifests = _load_captures(
        arguments.stage1_capture,
        Path(arguments.schema_root),
        "stage1_blind",
    )
    packet = build_stage2_review_packet(
        _load_object(Path(arguments.stage1_freeze)),
        stage1_reviews,
        _load_object(Path(arguments.reviewer_agent)),
        Path(arguments.prompt).read_text(encoding="utf-8"),
        created_at=str(arguments.created_at),
        answer_side_evidence_refs=_record_ref_list(evidence, "answer_side_evidence_refs"),
        reference_analysis_refs=_record_ref_list(evidence, "reference_analysis_refs"),
        execution_comparison_refs=_record_ref_list(evidence, "execution_comparison_refs"),
    )
    write_normalized_json_once(output, packet)
    return output


def _label_freeze_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    stage2_reviews, stage2_packets, stage2_manifests = _load_captures(
        arguments.stage2_capture,
        Path(arguments.schema_root),
        "stage2_scientific_adjudication",
    )
    stage1_reviews, _stage1_packets, _stage1_manifests = _load_captures(
        arguments.stage1_capture,
        Path(arguments.schema_root),
        "stage1_blind",
    )
    freeze_scientific_label(
        _load_object(Path(arguments.adjudication)),
        _load_object(Path(arguments.stage1_freeze)),
        stage2_reviews,
        stage2_packets,
        stage2_manifests,
        Path(arguments.schema_root),
        frozen_at=str(arguments.frozen_at),
        output=output,
        stage1_reviews=stage1_reviews,
        adjudicated_root_causes=[
            _load_object(Path(value)) for value in (arguments.adjudicated_root_cause or [])
        ],
    )
    return output


def _reconcile_root_cause_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    schema_root = Path(arguments.schema_root)
    stage1_reviews, _stage1_packets, _stage1_manifests = _load_captures(
        arguments.stage1_capture, schema_root, "stage1_blind"
    )
    stage2_reviews, _stage2_packets, _stage2_manifests = _load_captures(
        arguments.stage2_capture, schema_root, "stage2_scientific_adjudication"
    )
    spec = _load_object(Path(arguments.resolution_spec))
    if set(spec) != {
        "statement_source_review_id",
        "required_scientific_premises",
        "stronger_claims_excluded",
    }:
        raise RootCauseReconciliationError(
            "Root-cause resolution specification has unexpected fields."
        )
    build_adjudicated_root_cause(
        stage1_reviews,
        stage2_reviews,
        schema_root,
        adjudicated_at=str(arguments.adjudicated_at),
        statement_source_review_id=str(spec["statement_source_review_id"]),
        required_scientific_premises=_string_list(
            spec["required_scientific_premises"], "required scientific premises"
        ),
        stronger_claims_excluded=_string_list(
            spec["stronger_claims_excluded"], "stronger-claim exclusions"
        ),
        output=output,
    )
    return output


def _label_replay_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    schema_root = Path(arguments.schema_root)
    source_freeze = _load_object(Path(arguments.source_label_freeze))
    stage1_reviews, _stage1_packets, _stage1_manifests = _load_captures(
        arguments.stage1_capture, schema_root, "stage1_blind"
    )
    stage2_reviews, stage2_packets, stage2_manifests = _load_captures(
        arguments.stage2_capture, schema_root, "stage2_scientific_adjudication"
    )
    freeze_scientific_label(
        _load_object(Path(arguments.adjudication)),
        _load_object(Path(arguments.stage1_freeze)),
        stage2_reviews,
        stage2_packets,
        stage2_manifests,
        schema_root,
        frozen_at=str(source_freeze.get("frozen_at", "")),
        output=output,
        stage1_reviews=stage1_reviews,
        adjudicated_root_causes=[
            _load_object(Path(value)) for value in (arguments.adjudicated_root_cause or [])
        ],
        expected_freeze=source_freeze,
    )
    return output


def _comparison_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    compare_detector_output(
        _load_object(Path(arguments.fixture)),
        _load_object(Path(arguments.adjudication)),
        _load_object(Path(arguments.label_freeze)),
        _load_object(Path(arguments.audit_bundle)),
        str(arguments.detector_id),
        Path(arguments.schema_root),
        compared_at=str(arguments.compared_at),
        output=output,
    )
    return output


def _candidate_projection_command(arguments: argparse.Namespace) -> Path:
    return _run_candidate_projection(arguments, expected_candidate=None)


def _candidate_replay_command(arguments: argparse.Namespace) -> Path:
    return _run_candidate_projection(
        arguments, expected_candidate=_load_object(Path(arguments.source_candidate))
    )


def _run_candidate_projection(
    arguments: argparse.Namespace, *, expected_candidate: dict[str, Any] | None
) -> Path:
    output = Path(arguments.output)
    spec = _load_object(Path(arguments.admission_context))
    required = {
        "source_references_resolved",
        "wording_constraints_satisfied",
        "expected_deterministic_input_digest",
        "required_counterevidence_check_ids",
        "non_inferences",
    }
    if set(spec) != required:
        raise EvaluationCandidateProjectionError(
            "Evaluation admission-context specification has unexpected fields."
        )
    if not isinstance(spec["source_references_resolved"], bool) or not isinstance(
        spec["wording_constraints_satisfied"], bool
    ):
        raise EvaluationCandidateProjectionError(
            "Evaluation admission-context gate values must be booleans."
        )
    context = AdmissionContext(
        finding_draft=_load_object(Path(arguments.finding_draft)),
        source_references_resolved=spec["source_references_resolved"],
        detector_qualification_applies=False,
        wording_constraints_satisfied=spec["wording_constraints_satisfied"],
        expected_deterministic_input_digest=str(spec["expected_deterministic_input_digest"]),
        required_counterevidence_check_ids=tuple(
            _string_list(
                spec["required_counterevidence_check_ids"],
                "required counterevidence check IDs",
            )
        ),
        non_inferences=tuple(_string_list(spec["non_inferences"], "non-inferences")),
    )
    created_at = (
        str(expected_candidate.get("candidate_created_at", ""))
        if expected_candidate is not None
        else str(arguments.created_at)
    )
    project_evaluation_candidate(
        _load_object(Path(arguments.detector_result)),
        context,
        _load_object(Path(arguments.fixture)),
        _load_object(Path(arguments.label_freeze)),
        _load_object(Path(arguments.audit_bundle)),
        Path(arguments.schema_root),
        candidate_created_at=created_at,
        output=output,
        expected_candidate=expected_candidate,
    )
    return output


def _stage3_packet_command(arguments: argparse.Namespace) -> Path:
    output = _absent_output(arguments.output)
    packet = build_stage3_review_packet(
        _load_object(Path(arguments.fixture)),
        _load_object(Path(arguments.adjudication)),
        _load_object(Path(arguments.stage1_freeze)),
        _load_object(Path(arguments.label_freeze)),
        _load_object(Path(arguments.audit_bundle)),
        [_load_object(Path(value)) for value in (arguments.candidate or [])],
        [_load_object(Path(value)) for value in (arguments.adjudicated_root_cause or [])],
        str(arguments.detector_id),
        _load_object(Path(arguments.reviewer_agent)),
        Path(arguments.prompt).read_text(encoding="utf-8"),
        Path(arguments.schema_root),
        created_at=str(arguments.created_at),
    )
    write_normalized_json_once(output, packet)
    return output


def _stage3_reconcile_command(arguments: argparse.Namespace) -> Path:
    return _run_stage3_reconciliation(arguments, expected_outcome=None)


def _stage3_replay_command(arguments: argparse.Namespace) -> Path:
    return _run_stage3_reconciliation(
        arguments, expected_outcome=_load_object(Path(arguments.source_outcome))
    )


def _metrics_command(arguments: argparse.Namespace) -> Path:
    return _run_metrics(arguments, expected_metric_set=None)


def _metrics_replay_command(arguments: argparse.Namespace) -> Path:
    return _run_metrics(
        arguments, expected_metric_set=_load_object(Path(arguments.source_metric_set))
    )


def _run_metrics(
    arguments: argparse.Namespace, *, expected_metric_set: dict[str, Any] | None
) -> Path:
    output = Path(arguments.output)
    generated_at = (
        str(expected_metric_set.get("generated_at", ""))
        if expected_metric_set is not None
        else str(arguments.generated_at)
    )
    build_qualification_metric_set(
        [_load_object(Path(value)) for value in arguments.case_outcome],
        [_load_object(Path(value)) for value in arguments.fixture],
        _load_object(Path(arguments.qualification_envelope)),
        Path(arguments.schema_root),
        generated_at=generated_at,
        output=output,
        expected_metric_set=expected_metric_set,
    )
    return output


def _run_stage3_reconciliation(
    arguments: argparse.Namespace, *, expected_outcome: dict[str, Any] | None
) -> Path:
    output = Path(arguments.output)
    schema_root = Path(arguments.schema_root)
    reviews, packets, _manifests = _load_captures(
        arguments.stage3_capture, schema_root, "stage3_detector_comparison"
    )
    reconciled_at = (
        str(expected_outcome.get("reconciled_at", ""))
        if expected_outcome is not None
        else str(arguments.reconciled_at)
    )
    reconcile_detector_case(
        _load_object(Path(arguments.fixture)),
        _load_object(Path(arguments.adjudication)),
        _load_object(Path(arguments.stage1_freeze)),
        _load_object(Path(arguments.label_freeze)),
        _load_object(Path(arguments.audit_bundle)),
        [_load_object(Path(value)) for value in (arguments.candidate or [])],
        [_load_object(Path(value)) for value in (arguments.adjudicated_root_cause or [])],
        str(arguments.detector_id),
        reviews,
        packets,
        schema_root,
        reconciled_at=reconciled_at,
        output=output,
        expected_outcome=expected_outcome,
        fixture_proof_inputs=_fixture_proof_inputs_from_arguments(arguments),
    )
    return output


def _grader_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    grade_exact_json_output(
        _load_object(Path(arguments.fixture)),
        _load_object(Path(arguments.adjudication)),
        _load_object(Path(arguments.snapshot)),
        _load_jsonl(Path(arguments.file_records_jsonl)),
        _load_jsonl(Path(arguments.asset_identities_jsonl)),
        Path(arguments.materialized_root),
        _load_object(Path(arguments.grader_spec)),
        Path(arguments.schema_root),
        graded_at=str(arguments.graded_at),
        output=output,
    )
    return output


def _genebench_grader_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    grade_genebench_public_numeric_answer(
        Path(arguments.package_root),
        _load_object(Path(arguments.preflight)),
        str(arguments.eval_id),
        Path(arguments.audit_root),
        Path(arguments.schema_root),
        graded_at=str(arguments.graded_at),
        output=output,
    )
    return output


def _genebench_answer_grader_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    grade_genebench_public_answer(
        Path(arguments.package_root),
        _load_object(Path(arguments.preflight)),
        str(arguments.eval_id),
        Path(arguments.audit_root),
        Path(arguments.schema_root),
        graded_at=str(arguments.graded_at),
        output=output,
    )
    return output


def _method_contract_diagnostic_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    diagnose_genebench_method_contract_conflict(
        Path(arguments.audit_root),
        Path(arguments.schema_root),
        _load_object(Path(arguments.reference_profile)),
        reference_id=str(arguments.reference_id),
        reference_content_digest=str(arguments.reference_content_digest),
        diagnosed_at=str(arguments.diagnosed_at),
        output=output,
    )
    return output


def _source_method_probe_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    probe_python_method_shapes(
        Path(arguments.source_root),
        str(arguments.source),
        [str(value) for value in arguments.profile],
        reference_id=str(arguments.reference_id),
        reference_content_digest=str(arguments.reference_content_digest),
        diagnosed_at=str(arguments.diagnosed_at),
        output=output,
    )
    return output


def _posthoc_validation_review_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    build_posthoc_validation_review(
        _load_object(Path(arguments.source_probe)),
        _load_object(Path(arguments.review_spec)),
        reviewed_at=str(arguments.reviewed_at),
        output=output,
    )
    return output


def _fixture_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    generate_ambiguous_fixture(
        _load_object(Path(arguments.adjudication)),
        _load_object(Path(arguments.snapshot)),
        _load_jsonl(Path(arguments.file_records_jsonl)),
        _load_jsonl(Path(arguments.asset_identities_jsonl)),
        _load_object(Path(arguments.fixture_spec)),
        Path(arguments.schema_root),
        created_at=str(arguments.created_at),
        output=output,
    )
    return output


def _positive_fixture_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    schema_root = Path(arguments.schema_root)
    generate_positive_fixture(
        _load_object(Path(arguments.adjudication)),
        [Path(value) for value in arguments.stage1_capture],
        [Path(value) for value in arguments.stage2_capture],
        _load_object(Path(arguments.stage1_freeze)),
        [_load_object(Path(value)) for value in arguments.workspace_manifest],
        [_load_object(Path(value)) for value in arguments.adjudicated_root_cause],
        _load_object(Path(arguments.snapshot)),
        _load_jsonl(Path(arguments.file_records_jsonl)),
        _load_jsonl(Path(arguments.asset_identities_jsonl)),
        Path(arguments.materialized_root),
        _load_object(Path(arguments.fixture_spec)),
        schema_root,
        created_at=str(arguments.created_at),
        output=output,
    )
    return output


def _control_fixture_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    generate_control_fixture(
        _load_object(Path(arguments.adjudication)),
        [Path(value) for value in arguments.stage1_capture],
        [Path(value) for value in arguments.stage2_capture],
        _load_object(Path(arguments.stage1_freeze)),
        [_load_object(Path(value)) for value in arguments.workspace_manifest],
        _load_object(Path(arguments.snapshot)),
        _load_jsonl(Path(arguments.file_records_jsonl)),
        _load_jsonl(Path(arguments.asset_identities_jsonl)),
        Path(arguments.materialized_root),
        [_load_object(Path(value)) for value in arguments.scientific_contract],
        [_load_object(Path(value)) for value in arguments.operation],
        [_load_object(Path(value)) for value in arguments.environment],
        [_load_object(Path(value)) for value in arguments.execution],
        [_load_object(Path(value)) for value in (arguments.sandbox_capability or [])],
        [_load_object(Path(value)) for value in (arguments.evidence_record or [])],
        _load_object(Path(arguments.fixture_spec)),
        Path(arguments.schema_root),
        created_at=str(arguments.created_at),
        output=output,
    )
    return output


def _static_profile_command(arguments: argparse.Namespace) -> Path:
    output = _absent_output(arguments.output)
    profile = freeze_bounded_direction_profile(
        _load_object(Path(arguments.detector_manifest)),
        [_load_object(Path(value)) for value in arguments.parser_manifest],
        [_load_object(Path(value)) for value in arguments.semantic_profile_manifest],
        [_load_object(Path(value)) for value in arguments.version_manifest],
        _load_object(Path(arguments.selection_protocol_artifact)),
        frozen_at=str(arguments.frozen_at),
        max_candidate_files=int(arguments.max_candidate_files),
        max_total_bytes=int(arguments.max_total_bytes),
        max_recursion_depth=int(arguments.max_recursion_depth),
        max_elapsed_milliseconds=int(arguments.max_elapsed_milliseconds),
    )
    write_normalized_json_once(output, profile)
    return output


def _static_proof_command(arguments: argparse.Namespace) -> Path:
    output = _absent_output(arguments.output)
    proof = verify_bounded_direction_case(
        Path(arguments.materialized_root),
        _load_object(Path(arguments.profile)),
        _load_object(Path(arguments.case_assignment_artifact)),
        _load_object(Path(arguments.label_freeze_artifact)),
        _load_object(Path(arguments.snapshot)),
        _load_jsonl(Path(arguments.file_records_jsonl)),
        _load_jsonl(Path(arguments.asset_identities_jsonl)),
        detector_manifest=_load_object(Path(arguments.detector_manifest)),
        parser_manifests=[_load_object(Path(value)) for value in arguments.parser_manifest],
        semantic_profile_manifests=[
            _load_object(Path(value)) for value in arguments.semantic_profile_manifest
        ],
        version_manifests=[_load_object(Path(value)) for value in arguments.version_manifest],
        proof_frozen_at=str(arguments.proof_frozen_at),
    )
    write_normalized_json_once(output, proof)
    return output


def _analysis_method_static_profile_command(arguments: argparse.Namespace) -> Path:
    output = _absent_output(arguments.output)
    profile = freeze_bounded_analysis_method_profile(
        _load_object(Path(arguments.detector_manifest)),
        [_load_object(Path(value)) for value in arguments.parser_manifest],
        [_load_object(Path(value)) for value in arguments.semantic_profile_manifest],
        [_load_object(Path(value)) for value in arguments.version_manifest],
        _load_object(Path(arguments.selection_protocol_artifact)),
        frozen_at=str(arguments.frozen_at),
        max_candidate_files=int(arguments.max_candidate_files),
        max_total_bytes=int(arguments.max_total_bytes),
        max_recursion_depth=int(arguments.max_recursion_depth),
        max_elapsed_milliseconds=int(arguments.max_elapsed_milliseconds),
    )
    write_normalized_json_once(output, profile)
    return output


def _analysis_method_static_assignment_command(arguments: argparse.Namespace) -> Path:
    return _write_method_static_assignment(
        arguments, expected_profile_kind="bounded_analysis_method_conflict_v1"
    )


def _write_method_static_assignment(
    arguments: argparse.Namespace, *, expected_profile_kind: str
) -> Path:
    output = _absent_output(arguments.output)
    profile = _load_object(Path(arguments.profile))
    digest_basis = dict(profile)
    profile_digest = digest_basis.pop("profile_semantic_digest", None)
    protocol = profile.get("selection_protocol_artifact")
    report_path = PurePosixPath(str(arguments.selected_report))
    case_id = str(arguments.case_id).strip()
    assigned_at = str(arguments.assigned_at)
    if (
        profile.get("record_type") != "static_qualification_profile"
        or profile.get("profile_kind") != expected_profile_kind
        or profile_digest != semantic_digest(digest_basis)
        or not isinstance(protocol, dict)
        or not isinstance(protocol.get("artifact_id"), str)
        or not isinstance(protocol.get("content_digest"), str)
    ):
        raise AnalysisMethodQualificationError("Analysis-method profile identity is invalid.")
    if (
        not case_id
        or not str(report_path)
        or report_path.is_absolute()
        or "." in report_path.parts
        or ".." in report_path.parts
        or report_path.suffix != ".md"
    ):
        raise AnalysisMethodQualificationError(
            "Selected report path is not one safe Markdown path."
        )
    if _cli_timestamp(assigned_at) <= _cli_timestamp(str(profile.get("frozen_at", ""))):
        raise AnalysisMethodQualificationError("Case assignment must follow the profile freeze.")
    assignment = freeze_protocol_artifact(
        "opaque_case_assignment",
        stable_id("case-assignment", str(profile["profile_id"]), case_id),
        assigned_at,
        {
            "case_id": case_id,
            "selected_report_path": report_path.as_posix(),
            "selection_protocol_artifact_id": protocol["artifact_id"],
            "selection_protocol_artifact_digest": protocol["content_digest"],
        },
    )
    write_normalized_json_once(output, assignment)
    return output


def _analysis_method_static_proof_command(arguments: argparse.Namespace) -> Path:
    output = _absent_output(arguments.output)
    proof = verify_bounded_analysis_method_case(
        Path(arguments.materialized_root),
        _load_object(Path(arguments.profile)),
        _load_object(Path(arguments.case_assignment_artifact)),
        _load_object(Path(arguments.label_freeze_artifact)),
        _load_object(Path(arguments.snapshot)),
        _load_jsonl(Path(arguments.file_records_jsonl)),
        _load_jsonl(Path(arguments.asset_identities_jsonl)),
        _load_jsonl(Path(arguments.material_questions_jsonl)),
        _load_jsonl(Path(arguments.answers_jsonl)),
        _load_jsonl(Path(arguments.scientific_contracts_jsonl)),
        _load_jsonl(Path(arguments.semantic_assertions_jsonl)),
        detector_manifest=_load_object(Path(arguments.detector_manifest)),
        parser_manifests=[_load_object(Path(value)) for value in arguments.parser_manifest],
        semantic_profile_manifests=[
            _load_object(Path(value)) for value in arguments.semantic_profile_manifest
        ],
        version_manifests=[_load_object(Path(value)) for value in arguments.version_manifest],
        proof_frozen_at=str(arguments.proof_frozen_at),
    )
    write_normalized_json_once(output, proof)
    return output


def _typed_method_static_profile_command(arguments: argparse.Namespace) -> Path:
    output = _absent_output(arguments.output)
    binding = _load_object(Path(arguments.method_binding))
    profile = freeze_typed_method_profile(
        binding=binding,
        adapter=registered_qualification_adapter(binding),
        detector_manifest=_load_object(Path(arguments.detector_manifest)),
        parser_manifests=[_load_object(Path(value)) for value in arguments.parser_manifest],
        semantic_profile_manifests=[
            _load_object(Path(value)) for value in arguments.semantic_profile_manifest
        ],
        version_manifests=[_load_object(Path(value)) for value in arguments.version_manifest],
        selection_protocol_artifact=_load_object(Path(arguments.selection_protocol_artifact)),
        candidate_suffixes=[str(value) for value in arguments.candidate_suffix],
        frozen_at=str(arguments.frozen_at),
        max_candidate_files=int(arguments.max_candidate_files),
        max_total_bytes=int(arguments.max_total_bytes),
        max_recursion_depth=int(arguments.max_recursion_depth),
        max_elapsed_milliseconds=int(arguments.max_elapsed_milliseconds),
    )
    write_normalized_json_once(output, profile)
    return output


def _typed_method_static_assignment_command(arguments: argparse.Namespace) -> Path:
    return _write_method_static_assignment(
        arguments, expected_profile_kind="typed_static_method_conflict_v1"
    )


def _typed_method_static_proof_command(arguments: argparse.Namespace) -> Path:
    output = _absent_output(arguments.output)
    inputs = _typed_method_static_proof_inputs(arguments)
    proof = verify_registered_typed_method_case(
        **inputs,
        proof_frozen_at=str(arguments.proof_frozen_at),
    )
    write_normalized_json_once(output, proof)
    return output


def _typed_method_static_replay_command(arguments: argparse.Namespace) -> Path:
    output = _absent_output(arguments.output)
    proof = revalidate_registered_typed_method_proof(
        _load_object(Path(arguments.source_proof)),
        **_typed_method_static_proof_inputs(arguments),
    )
    write_normalized_json_once(output, proof)
    return output


def _typed_method_static_proof_inputs(arguments: argparse.Namespace) -> dict[str, Any]:
    profile = _load_object(Path(arguments.profile))
    binding = profile.get("method_binding")
    if not isinstance(binding, dict):
        raise TypedMethodQualificationError("typed profile binding is absent")
    return {
        "workspace_root": Path(arguments.materialized_root),
        "profile": profile,
        "adapter": registered_qualification_adapter(binding),
        "case_assignment_artifact": _load_object(Path(arguments.case_assignment_artifact)),
        "label_freeze_artifact": _load_object(Path(arguments.label_freeze_artifact)),
        "snapshot": _load_object(Path(arguments.snapshot)),
        "file_records": _load_jsonl(Path(arguments.file_records_jsonl)),
        "asset_identities": _load_jsonl(Path(arguments.asset_identities_jsonl)),
        "material_questions": _load_jsonl(Path(arguments.material_questions_jsonl)),
        "answers": _load_jsonl(Path(arguments.answers_jsonl)),
        "scientific_contracts": _load_jsonl(Path(arguments.scientific_contracts_jsonl)),
        "semantic_assertions": _load_jsonl(Path(arguments.semantic_assertions_jsonl)),
        "detector_manifest": _load_object(Path(arguments.detector_manifest)),
        "parser_manifests": [_load_object(Path(value)) for value in arguments.parser_manifest],
        "semantic_profile_manifests": [
            _load_object(Path(value)) for value in arguments.semantic_profile_manifest
        ],
        "version_manifests": [_load_object(Path(value)) for value in arguments.version_manifest],
    }


def _static_fixture_command(arguments: argparse.Namespace) -> Path:
    output = Path(arguments.output)
    proof_inputs = FixtureProofInputs(
        stage1_capture_directories=[Path(value) for value in arguments.stage1_capture],
        stage2_capture_directories=[Path(value) for value in arguments.stage2_capture],
        stage1_freeze=_load_object(Path(arguments.stage1_freeze)),
        workspace_manifests=[_load_object(Path(value)) for value in arguments.workspace_manifest],
        snapshot=_load_object(Path(arguments.snapshot)),
        file_records=_load_jsonl(Path(arguments.file_records_jsonl)),
        asset_identities=_load_jsonl(Path(arguments.asset_identities_jsonl)),
        materialized_root=Path(arguments.materialized_root),
        scientific_contracts=[_load_object(Path(value)) for value in arguments.scientific_contract],
        operations=[_load_object(Path(value)) for value in arguments.operation],
        environments=[],
        executions=[],
        sandbox_capabilities=[],
        evidence_records=[_load_object(Path(value)) for value in (arguments.evidence_record or [])],
        static_qualification_profile=_load_object(Path(arguments.static_profile)),
        static_qualification_proof=_load_object(Path(arguments.static_proof)),
        case_assignment_artifact=_load_object(Path(arguments.case_assignment_artifact)),
        static_label_freeze_artifact=_load_object(Path(arguments.static_label_freeze_artifact)),
        scientific_label_freeze=_load_object(Path(arguments.scientific_label_freeze)),
        detector_manifest=_load_object(Path(arguments.detector_manifest)),
        parser_manifests=[_load_object(Path(value)) for value in arguments.parser_manifest],
        semantic_profile_manifests=[
            _load_object(Path(value)) for value in arguments.semantic_profile_manifest
        ],
        version_manifests=[_load_object(Path(value)) for value in arguments.version_manifest],
        material_questions=[
            _load_object(Path(value)) for value in (arguments.material_question or [])
        ],
        answers=[_load_object(Path(value)) for value in (arguments.answer or [])],
        semantic_assertions=[
            _load_object(Path(value)) for value in (arguments.semantic_assertion or [])
        ],
    )
    generate_static_control_fixture(
        _load_object(Path(arguments.adjudication)),
        [],
        proof_inputs,
        _load_object(Path(arguments.fixture_spec)),
        Path(arguments.schema_root),
        created_at=str(arguments.created_at),
        output=output,
    )
    return output


def _optional_snapshot_arguments(arguments: argparse.Namespace) -> dict[str, Path]:
    raw = {
        "snapshot": arguments.snapshot,
        "file_records": arguments.file_records_jsonl,
        "asset_identities": arguments.asset_identities_jsonl,
        "materialized_root": arguments.materialized_root,
    }
    if not any(value is not None for value in raw.values()):
        return {}
    if not all(value is not None for value in raw.values()):
        raise EvaluationValidationError(
            "Snapshot resolution requires all four snapshot-related command options."
        )
    return {key: Path(str(value)) for key, value in raw.items()}


def _add_typed_method_proof_arguments(parser: argparse.ArgumentParser, *, replay: bool) -> None:
    if replay:
        parser.add_argument("--source-proof", required=True)
    parser.add_argument("--materialized-root", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--detector-manifest", required=True)
    parser.add_argument("--parser-manifest", action="append", required=True)
    parser.add_argument("--semantic-profile-manifest", action="append", required=True)
    parser.add_argument("--version-manifest", action="append", required=True)
    parser.add_argument("--case-assignment-artifact", required=True)
    parser.add_argument("--label-freeze-artifact", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--file-records-jsonl", required=True)
    parser.add_argument("--asset-identities-jsonl", required=True)
    parser.add_argument("--material-questions-jsonl", required=True)
    parser.add_argument("--answers-jsonl", required=True)
    parser.add_argument("--scientific-contracts-jsonl", required=True)
    parser.add_argument("--semantic-assertions-jsonl", required=True)
    if not replay:
        parser.add_argument("--proof-frozen-at", required=True)
    parser.add_argument("--output", required=True)


def _add_stage3_reconciliation_arguments(
    parser: argparse.ArgumentParser, *, require_reconciled_at: bool
) -> None:
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--adjudication", required=True)
    parser.add_argument("--stage1-freeze", required=True)
    parser.add_argument("--label-freeze", required=True)
    parser.add_argument("--audit-bundle", required=True)
    parser.add_argument("--candidate", action="append")
    parser.add_argument("--adjudicated-root-cause", action="append")
    parser.add_argument("--detector-id", required=True)
    parser.add_argument("--stage3-capture", action="append", required=True)
    parser.add_argument("--proof-stage1-capture", action="append")
    parser.add_argument("--proof-stage2-capture", action="append")
    parser.add_argument("--proof-stage1-freeze")
    parser.add_argument("--proof-workspace-manifest", action="append")
    parser.add_argument("--proof-snapshot")
    parser.add_argument("--proof-file-records-jsonl")
    parser.add_argument("--proof-asset-identities-jsonl")
    parser.add_argument("--proof-materialized-root")
    parser.add_argument("--proof-scientific-contract", action="append")
    parser.add_argument("--proof-material-question", action="append")
    parser.add_argument("--proof-answer", action="append")
    parser.add_argument("--proof-semantic-assertion", action="append")
    parser.add_argument("--proof-operation", action="append")
    parser.add_argument("--proof-environment", action="append")
    parser.add_argument("--proof-execution", action="append")
    parser.add_argument("--proof-sandbox-capability", action="append")
    parser.add_argument("--proof-evidence-record", action="append")
    parser.add_argument("--proof-static-profile")
    parser.add_argument("--proof-static-proof")
    parser.add_argument("--proof-case-assignment-artifact")
    parser.add_argument("--proof-static-label-freeze-artifact")
    parser.add_argument("--proof-scientific-label-freeze")
    parser.add_argument("--proof-detector-manifest")
    parser.add_argument("--proof-parser-manifest", action="append")
    parser.add_argument("--proof-semantic-profile-manifest", action="append")
    parser.add_argument("--proof-version-manifest", action="append")
    parser.add_argument("--schema-root", required=True)
    if require_reconciled_at:
        parser.add_argument("--reconciled-at", required=True)
    parser.add_argument("--output", required=True)


def _fixture_proof_inputs_from_arguments(
    arguments: argparse.Namespace,
) -> FixtureProofInputs | None:
    raw = {
        "stage1_capture": arguments.proof_stage1_capture,
        "stage2_capture": arguments.proof_stage2_capture,
        "stage1_freeze": arguments.proof_stage1_freeze,
        "workspace_manifest": arguments.proof_workspace_manifest,
        "snapshot": arguments.proof_snapshot,
        "file_records": arguments.proof_file_records_jsonl,
        "asset_identities": arguments.proof_asset_identities_jsonl,
        "materialized_root": arguments.proof_materialized_root,
    }
    if not any(value is not None for value in raw.values()):
        return None
    if not all(value is not None for value in raw.values()):
        missing = sorted(key for key, value in raw.items() if value is None)
        raise Stage3ProtocolError(f"Fixture proof replay is missing required inputs: {missing}.")
    return FixtureProofInputs(
        stage1_capture_directories=[Path(value) for value in arguments.proof_stage1_capture],
        stage2_capture_directories=[Path(value) for value in arguments.proof_stage2_capture],
        stage1_freeze=_load_object(Path(arguments.proof_stage1_freeze)),
        workspace_manifests=[
            _load_object(Path(value)) for value in arguments.proof_workspace_manifest
        ],
        snapshot=_load_object(Path(arguments.proof_snapshot)),
        file_records=_load_jsonl(Path(arguments.proof_file_records_jsonl)),
        asset_identities=_load_jsonl(Path(arguments.proof_asset_identities_jsonl)),
        materialized_root=Path(arguments.proof_materialized_root),
        scientific_contracts=[
            _load_object(Path(value)) for value in (arguments.proof_scientific_contract or [])
        ],
        operations=[_load_object(Path(value)) for value in (arguments.proof_operation or [])],
        environments=[_load_object(Path(value)) for value in (arguments.proof_environment or [])],
        executions=[_load_object(Path(value)) for value in (arguments.proof_execution or [])],
        sandbox_capabilities=[
            _load_object(Path(value)) for value in (arguments.proof_sandbox_capability or [])
        ],
        evidence_records=[
            _load_object(Path(value)) for value in (arguments.proof_evidence_record or [])
        ],
        static_qualification_profile=(
            _load_object(Path(arguments.proof_static_profile))
            if arguments.proof_static_profile is not None
            else None
        ),
        static_qualification_proof=(
            _load_object(Path(arguments.proof_static_proof))
            if arguments.proof_static_proof is not None
            else None
        ),
        case_assignment_artifact=(
            _load_object(Path(arguments.proof_case_assignment_artifact))
            if arguments.proof_case_assignment_artifact is not None
            else None
        ),
        static_label_freeze_artifact=(
            _load_object(Path(arguments.proof_static_label_freeze_artifact))
            if arguments.proof_static_label_freeze_artifact is not None
            else None
        ),
        scientific_label_freeze=(
            _load_object(Path(arguments.proof_scientific_label_freeze))
            if arguments.proof_scientific_label_freeze is not None
            else None
        ),
        detector_manifest=(
            _load_object(Path(arguments.proof_detector_manifest))
            if arguments.proof_detector_manifest is not None
            else None
        ),
        parser_manifests=[
            _load_object(Path(value)) for value in (arguments.proof_parser_manifest or [])
        ],
        semantic_profile_manifests=[
            _load_object(Path(value)) for value in (arguments.proof_semantic_profile_manifest or [])
        ],
        version_manifests=[
            _load_object(Path(value)) for value in (arguments.proof_version_manifest or [])
        ],
        material_questions=[
            _load_object(Path(value)) for value in (arguments.proof_material_question or [])
        ],
        answers=[_load_object(Path(value)) for value in (arguments.proof_answer or [])],
        semantic_assertions=[
            _load_object(Path(value)) for value in (arguments.proof_semantic_assertion or [])
        ],
    )


def _add_candidate_projection_arguments(parser: argparse.ArgumentParser, *, replay: bool) -> None:
    parser.add_argument("--detector-result", required=True)
    parser.add_argument("--finding-draft", required=True)
    parser.add_argument("--admission-context", required=True)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--label-freeze", required=True)
    parser.add_argument("--audit-bundle", required=True)
    parser.add_argument("--schema-root", required=True)
    if replay:
        parser.add_argument("--source-candidate", required=True)
    else:
        parser.add_argument("--created-at", required=True)
    parser.add_argument("--output", required=True)


def _add_metric_arguments(parser: argparse.ArgumentParser, *, replay: bool) -> None:
    parser.add_argument("--case-outcome", action="append", required=True)
    parser.add_argument("--fixture", action="append", required=True)
    parser.add_argument("--qualification-envelope", required=True)
    parser.add_argument("--schema-root", required=True)
    if replay:
        parser.add_argument("--source-metric-set", required=True)
    else:
        parser.add_argument("--generated-at", required=True)
    parser.add_argument("--output", required=True)


def _absent_output(value: str) -> Path:
    output = Path(value)
    if output.exists() or output.is_symlink():
        raise EvaluationValidationError(f"Output already exists: {output}")
    return output


def _cli_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise AnalysisMethodQualificationError(
            f"Invalid qualification timestamp {value!r}."
        ) from error
    if parsed.tzinfo is None:
        raise AnalysisMethodQualificationError("Qualification timestamps require a timezone.")
    return parsed


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected one JSON object in {path}")
    return value


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise TypeError(f"Expected a JSON object at {path}:{line_number}")
        records.append(value)
    return records


def _list_of_objects(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise TypeError(f"Expected {label} to be a list of JSON objects")
    return value


def _record_ref_list(value: dict[str, Any], key: str) -> list[dict[str, str]]:
    items = _list_of_objects(value.get(key), key)
    return [
        {
            "record_type": str(item.get("record_type", "")),
            "record_id": str(item.get("record_id", "")),
        }
        for item in items
    ]


def _string_set(value: Any) -> set[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError("Expected a list of strings in blind-workspace specification")
    return set(value)


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError(f"Expected {label} to be a list of strings")
    return value


def _load_captures(
    values: list[str], schema_root: Path, expected_stage: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    reviews: list[dict[str, Any]] = []
    packets: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    for value in values:
        review, packet, manifest = load_review_capture(Path(value), schema_root)
        if review.get("stage") != expected_stage:
            raise ReviewCaptureError(
                f"Expected a {expected_stage!r} capture, observed {review.get('stage')!r}."
            )
        reviews.append(review)
        packets.append(packet)
        manifests.append(manifest)
    return reviews, packets, manifests
