from __future__ import annotations


def test_straight_line_identity_flow_is_an_exact_claim_slice_for_live_certification():
    from sc_referee.inference import AnalysisRequest, analyze
    from sc_referee.inference.api import ANALYZER_VERSION
    from sc_referee.inference.api import ArtifactManifest
    from sc_referee.inference.claims.inventory import StructuredClaimManifest, StructuredClaimRoot
    from sc_referee.inference.live import ExactArtifactBinding

    assert ANALYZER_VERSION == "sc-referee.inference.increment-9.live.advisory-v4"
    root = StructuredClaimRoot(
        "claim:1", "sha256:report", "table.claim", "reported", "sha256:producer",
        "reported_value", "fact:root",
    )
    artifact = ExactArtifactBinding(
        "report", "json", "sha256:schema", "sha256:report", "writer:1", "serializer:1",
        True, True, True, True,
    )
    snapshot = analyze(AnalysisRequest(
        ("reported = source\n",), artifacts=ArtifactManifest((artifact,)),
        claims=StructuredClaimManifest((root,)),
    ))
    claim_slice = snapshot.claim_slices["claim:1"]
    assert claim_slice.coverage_complete is True
    assert claim_slice.unavoidable_producers
    assert snapshot.coverage.complete is True


def test_opaque_call_on_live_claim_path_forces_may_only_and_incomplete_coverage():
    from sc_referee.inference import AnalysisRequest, analyze
    from sc_referee.inference.api import ArtifactManifest
    from sc_referee.inference.claims.inventory import StructuredClaimManifest, StructuredClaimRoot
    from sc_referee.inference.live import ExactArtifactBinding

    root = StructuredClaimRoot(
        "claim:1", "sha256:report", "table.claim", "reported", "sha256:producer",
        "reported_value", "fact:root",
    )
    artifact = ExactArtifactBinding(
        "report", "json", "sha256:schema", "sha256:report", "writer:1", "serializer:1",
        True, True, True, True,
    )
    snapshot = analyze(AnalysisRequest(
        ("reported = opaque(source)\n",), artifacts=ArtifactManifest((artifact,)),
        claims=StructuredClaimManifest((root,)),
    ))
    assert snapshot.claim_slices["claim:1"].unavoidable_producers == frozenset()
    assert snapshot.coverage.complete is False
