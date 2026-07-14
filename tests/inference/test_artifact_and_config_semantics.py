from __future__ import annotations


def _artifact(role="table", *, schema="sha256:schema", content="sha256:content", path="results.csv"):
    from sc_referee.inference.analysis.artifacts import ArtifactId

    return ArtifactId(path, role, "csv", schema, content)


def _serializer(name="csv.v1"):
    from sc_referee.inference.analysis.artifacts import SerializerContract

    return SerializerContract(name, "csv", "1", f"sha256:{name}")


def _write(write_id, artifact, *, index=1, mode="write", path="results.csv",
           possible_mutation=False, serializer=None):
    from sc_referee.inference.analysis.artifacts import ArtifactWrite

    return ArtifactWrite(
        write_id=write_id, artifact=artifact, path=path, serializer=serializer or _serializer(),
        fields=("effect", "pvalue"), schema_digest=artifact.schema_digest,
        content_digest=artifact.content_digest, mode=mode, workflow_index=index,
        exact_path=True, possible_mutation=possible_mutation,
    )


def _read(artifact, *, index=3, path="results.csv", exact_path=True, serializer=None):
    from sc_referee.inference.analysis.artifacts import ArtifactRead

    return ArtifactRead(
        read_id="read:1", artifact=artifact, path=path, deserializer=serializer or _serializer(),
        field="pvalue", expected_schema_digest=artifact.schema_digest,
        expected_content_digest=artifact.content_digest, workflow_index=index, exact_path=exact_path,
    )


def test_exact_unique_artifact_writer_is_the_only_must_link():
    from sc_referee.inference.analysis.artifacts import ArtifactState, resolve_artifact_flow

    artifact = _artifact()
    writer = _write("write:1", artifact)
    result = resolve_artifact_flow(_read(artifact), ArtifactState((writer,)))

    assert result.must_producer == writer
    assert result.possible_producers == frozenset({writer})
    assert result.unknown_producer is None
    assert result.obligations == ()


def test_overwrite_append_and_possible_mutation_are_possible_only():
    from sc_referee.inference.analysis.artifacts import ArtifactState, resolve_artifact_flow

    artifact = _artifact()
    cases = (
        (_write("old", artifact, index=1), _write("overwrite", artifact, index=2)),
        (_write("base", artifact, index=1), _write("append", artifact, index=2, mode="append")),
        (_write("base", artifact, index=1), _write("maybe-mutated", artifact, index=2,
                                                   possible_mutation=True)),
    )
    for writes in cases:
        result = resolve_artifact_flow(_read(artifact), ArtifactState(writes))
        assert result.must_producer is None
        assert result.unknown_producer is not None
        assert result.possible_producers


def test_same_field_name_on_unrelated_artifacts_never_collapses_identity():
    from sc_referee.inference.analysis.artifacts import ArtifactState, resolve_artifact_flow

    left = _artifact("left", content="sha256:left")
    right = _artifact("right", content="sha256:right")
    result = resolve_artifact_flow(_read(left), ArtifactState((
        _write("left-writer", left), _write("right-writer", right),
    )))

    assert result.must_producer is None
    assert {writer.artifact.logical_role for writer in result.possible_producers} == {"left", "right"}
    assert result.unknown_producer is not None


def test_dynamic_path_glob_digest_field_and_serializer_mismatch_are_possible_only():
    from dataclasses import replace

    from sc_referee.inference.analysis.artifacts import ArtifactState, resolve_artifact_flow

    artifact = _artifact()
    state = ArtifactState((_write("writer", artifact),))
    bad_reads = (
        _read(artifact, path="result_*.csv", exact_path=False),
        replace(_read(artifact), expected_content_digest="sha256:other"),
        replace(_read(artifact), expected_schema_digest="sha256:other"),
        replace(_read(artifact), field="missing"),
        _read(artifact, serializer=_serializer("json.v1")),
    )
    for read in bad_reads:
        result = resolve_artifact_flow(read, state)
        assert result.must_producer is None
        assert result.unknown_producer is not None


def test_config_reads_require_literal_schema_valid_pinned_paths():
    from sc_referee.inference.frontend.config import ConfigState, UnknownConfig, read_config

    state = ConfigState(values={"model.alpha": 1}, schema_paths=frozenset({"model.alpha"}))
    exact = read_config(state, "model.alpha", literal_path=True)
    assert exact.value == 1 and exact.exact is True and exact.unknown is None

    for path, literal in (("model.missing", True), ("model.alpha", False), ("model.*", False)):
        result = read_config(state, path, literal_path=literal)
        assert result.exact is False
        assert isinstance(result.unknown, UnknownConfig)
