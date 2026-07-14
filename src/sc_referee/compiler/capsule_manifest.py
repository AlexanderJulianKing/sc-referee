"""Typed marker that lets a *compiled* analysis enter the friendly browser flow — invisibly.

A folder that carries ``sc-referee-capsule.yaml`` is a compiled-analysis capsule: it has no conventional
count matrix, so ordinary ingest cannot recognize it, but it points at canonical compiler artifacts and
declares the scientific questions a human must answer before the analysis can be evaluated. This module is
deliberately GENERAL — it never mentions a benchmark id, a folder name, or a verdict — and it is an internal
implementation detail: nothing here (or downstream) is shown to the reviewer as a "capsule". It parses and
validates the marker, resolves the artifacts directory safely, and verifies the artifacts against declared
digests so a missing or altered materialization abstains honestly instead of auditing the wrong bytes.

Deliberately absent: any external benchmark truth (reference answers, held-out coefficients). That belongs
only in separate demo-validation documentation, never in a product payload.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
from typing import Mapping

from sc_referee.compiler.inventory import InventoryPathError, confine_inventory_path


CAPSULE_MANIFEST_NAME = "sc-referee-capsule.yaml"
CAPSULE_SCHEMA = "sc-referee/compiled-analysis@v1"


class CapsuleManifestError(ValueError):
    """The capsule marker is present but malformed, unsupported, or unverifiable."""


def _reject_unsafe_relative(relative: str, *, what: str) -> None:
    """Reject absolute/traversal/backslash relative paths WITHOUT requiring the path to exist yet.

    ``confine_inventory_path`` resolves strictly (the target must exist), which is right once bytes are
    materialized but wrong for parsing a not-yet-prepared capsule. This is the existence-free safety gate.
    """
    parts = PurePosixPath(relative)
    if parts.is_absolute() or not relative or ".." in parts.parts or "\\" in relative:
        raise CapsuleManifestError(f"capsule {what} must be a confined relative path: {relative!r}")


@dataclass(frozen=True)
class Question:
    """One human-answerable scientific question, mapped to a ceremony group; drives the audit."""

    group: str
    prompt: str
    why: str
    default: str


@dataclass(frozen=True)
class ReviewFact:
    """One compact, reviewer-safe fact shown consistently in setup and report framing."""

    label: str
    value: str
    caution: bool = False


@dataclass(frozen=True)
class ReviewPresentation:
    """Display context for the ordinary review shell; never scientific adjudication input."""

    claim_title: str
    recognition: str
    facts: tuple[ReviewFact, ...] = ()


@dataclass(frozen=True)
class CompiledCapsuleManifest:
    kind: str
    title: str
    analysis: str
    reconstruction: str
    artifacts_dir: str
    artifact_digests: Mapping[str, str]
    questions: tuple[Question, ...]
    provenance_source: str
    presentation: ReviewPresentation


def _require(mapping: object, key: str, where: str) -> object:
    if not isinstance(mapping, Mapping) or key not in mapping:
        raise CapsuleManifestError(f"capsule manifest {where} is missing required key {key!r}")
    return mapping[key]


def _require_str(mapping: object, key: str, where: str) -> str:
    value = _require(mapping, key, where)
    if not isinstance(value, str) or not value.strip():
        raise CapsuleManifestError(f"capsule manifest {where}.{key} must be a non-empty string")
    return value


def load_capsule_manifest(folder: str | Path) -> CompiledCapsuleManifest | None:
    """Return the parsed capsule manifest, or ``None`` when the folder carries no marker.

    ``None`` means "not a capsule — fall through to ordinary ingest". A present-but-broken marker raises
    ``CapsuleManifestError`` so the caller can show an honest error page rather than silently ingesting.
    """
    import yaml

    root = Path(folder)
    marker = root / CAPSULE_MANIFEST_NAME
    if not marker.is_file():
        return None
    try:
        data = yaml.safe_load(marker.read_text())
    except yaml.YAMLError as exc:
        raise CapsuleManifestError(f"capsule manifest is not valid YAML: {exc}") from exc
    if not isinstance(data, Mapping):
        raise CapsuleManifestError("capsule manifest must be a mapping")

    schema = _require_str(data, "capsule_schema", "root")
    if schema != CAPSULE_SCHEMA:
        raise CapsuleManifestError(
            f"unsupported capsule schema {schema!r}; expected {CAPSULE_SCHEMA!r}")

    artifacts_dir = _require_str(data, "artifacts_dir", "root")
    # Validate safety now (no traversal/absolute), but do NOT require existence — a not-yet-materialized
    # capsule must still parse; verify_capsule_artifacts checks presence and digests later.
    _reject_unsafe_relative(artifacts_dir, what="artifacts_dir")

    provenance = _require(data, "provenance", "root")
    artifacts = _require(provenance, "artifacts", "provenance")
    if not isinstance(artifacts, Mapping) or not artifacts:
        raise CapsuleManifestError("capsule manifest provenance.artifacts must be a non-empty mapping")
    artifact_digests: dict[str, str] = {}
    for name, digest in artifacts.items():
        if not isinstance(name, str) or not isinstance(digest, str) or not digest.startswith("sha256:"):
            raise CapsuleManifestError(
                f"capsule provenance digest for {name!r} must be a 'sha256:...' string")
        artifact_digests[name] = digest

    questions: list[Question] = []
    for item in _require(data, "questions", "root") or ():
        questions.append(Question(
            group=_require_str(item, "group", "questions"),
            prompt=_require_str(item, "prompt", "questions"),
            why=_require_str(item, "why", "questions"),
            default=str(_require(item, "default", "questions")).strip().lower(),
        ))
    if not questions:
        raise CapsuleManifestError("capsule manifest must declare its scientific questions")

    raw_presentation = data.get("presentation", {})
    if raw_presentation is None:
        raw_presentation = {}
    if not isinstance(raw_presentation, Mapping):
        raise CapsuleManifestError("capsule manifest presentation must be a mapping")
    claim_title = raw_presentation.get("claim_title", data.get("title"))
    recognition = raw_presentation.get("recognition", data.get("reconstruction"))
    if not isinstance(claim_title, str) or not claim_title.strip():
        raise CapsuleManifestError("capsule manifest presentation.claim_title must be a non-empty string")
    if not isinstance(recognition, str) or not recognition.strip():
        raise CapsuleManifestError("capsule manifest presentation.recognition must be a non-empty string")
    facts: list[ReviewFact] = []
    raw_facts = raw_presentation.get("facts", ())
    if not isinstance(raw_facts, (list, tuple)):
        raise CapsuleManifestError("capsule manifest presentation.facts must be a list")
    for item in raw_facts:
        label = _require_str(item, "label", "presentation.facts")
        value = _require_str(item, "value", "presentation.facts")
        caution = item.get("caution", False) if isinstance(item, Mapping) else False
        if not isinstance(caution, bool):
            raise CapsuleManifestError(
                "capsule manifest presentation.facts.caution must be true or false")
        facts.append(ReviewFact(label=label, value=value, caution=caution))

    return CompiledCapsuleManifest(
        kind=_require_str(data, "capsule_kind", "root"),
        title=_require_str(data, "title", "root"),
        analysis=_require_str(data, "analysis", "root"),
        reconstruction=_require_str(data, "reconstruction", "root"),
        artifacts_dir=artifacts_dir,
        artifact_digests=artifact_digests,
        questions=tuple(questions),
        provenance_source=_require_str(provenance, "source", "provenance"),
        presentation=ReviewPresentation(
            claim_title=claim_title.strip(),
            recognition=recognition.strip(),
            facts=tuple(facts),
        ),
    )


def verify_capsule_artifacts(manifest: CompiledCapsuleManifest, folder: str | Path) -> Path:
    """Confirm every declared artifact is present and matches its digest; return the artifacts dir.

    Raises ``CapsuleManifestError`` on a missing directory, missing file, or digest mismatch — the caller
    turns that into an honest "not prepared / provenance mismatch" page instead of a verdict. A missing
    target is reported as a clean abstention; symlink-escape safety is enforced (via strict confinement)
    only once the target is known to exist.
    """
    root = Path(folder)
    _reject_unsafe_relative(manifest.artifacts_dir, what="artifacts_dir")
    if not (root / manifest.artifacts_dir).is_dir():
        raise CapsuleManifestError(
            f"capsule artifacts directory {manifest.artifacts_dir!r} is not present; "
            "the analysis inputs have not been materialized for this folder")
    try:
        artifacts_dir = confine_inventory_path(root, manifest.artifacts_dir)  # exists -> safe to confine
    except InventoryPathError as exc:
        raise CapsuleManifestError(
            "capsule artifacts directory is not safely confined to the selected folder") from exc
    for name, expected in manifest.artifact_digests.items():
        _reject_unsafe_relative(name, what="artifact name")
        if not (artifacts_dir / name).is_file():
            raise CapsuleManifestError(
                f"capsule artifact {name!r} is missing from {manifest.artifacts_dir!r}")
        try:
            path = confine_inventory_path(artifacts_dir, name)
        except InventoryPathError as exc:
            raise CapsuleManifestError(
                f"capsule artifact {name!r} is not safely confined to its artifacts directory") from exc
        actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise CapsuleManifestError(
                f"capsule artifact {name!r} does not match its recorded digest "
                "(provenance mismatch: the materialized bytes differ from what this folder was built from)")
    return artifacts_dir
