"""Zero-data-prose renderer for the one closed Slice-C M3 report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, cast

from sc_referee_evaluation.audit_ladder.slice_c.composition import SliceCCompositionResultV1
from sc_referee_evaluation.audit_ladder.slice_c.core import (
    SliceCContractError,
    canonical_json_bytes,
    sha256,
)
from sc_referee_evaluation.audit_ladder.slice_c.observations import (
    ObservationSetV1,
    validate_observations_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.repository import (
    CapturedWorld1MaterialsV1,
    RegistryBundleV1,
)

_APPENDIX_SIZE: Final = 48_094
_APPENDIX_SHA256: Final = "sha256:1f28948d9d268e26cd40bd1bef998969214dec94494d4e35e990b89108a0873f"
_REPORT_SIZE: Final = 49_609
_REPORT_SHA256: Final = "sha256:217e40ce0a4f9781191bac82d8e81410aa981186b3fec57593bb53896e45b3ca"
_RUNTIME_PREMISE_ID: Final = "scanpy-1.11.5-cpython-3.11.15-macos-arm64-v1"
_RUNTIME_PREMISE_DIGEST: Final = (
    "sha256:09fe04ea03c03221bf20c00b5e45cd8f66f00d7476f98da64df5dcde79dc7eeb"
)


class SliceCRendererError(RuntimeError):
    """The closed report could not be rendered atomically."""


@dataclass(frozen=True, slots=True)
class RenderedSliceCReportV1:
    report_bytes: bytes
    appendix_bytes: bytes
    report_sha256: str
    appendix_sha256: str

    def __post_init__(self) -> None:
        if (
            type(self) is not RenderedSliceCReportV1
            or len(self.report_bytes) != _REPORT_SIZE
            or len(self.appendix_bytes) != _APPENDIX_SIZE
            or self.report_sha256 != _REPORT_SHA256
            or self.appendix_sha256 != _APPENDIX_SHA256
            or sha256(self.report_bytes) != self.report_sha256
            or sha256(self.appendix_bytes) != self.appendix_sha256
        ):
            raise SliceCRendererError("rendered artifact identity differs")


def renderer_runtime_premise_v1() -> tuple[str, str]:
    """Return the independently fixed renderer provenance carrier."""

    return _RUNTIME_PREMISE_ID, _RUNTIME_PREMISE_DIGEST


def _validate_renderer_registry(value: dict[str, Any]) -> None:
    if set(value) != {
        "appendix_indent",
        "blank_line_policy",
        "disclosures",
        "empty_section_sentence",
        "grade_prefixes",
        "header",
        "headings",
        "m3_concern",
        "m3_coverage",
        "schema",
        "terminal_lf_count",
    }:
        raise SliceCRendererError("renderer registry member set differs")
    if (
        value.get("schema") != "slice-c-renderer-registry-v2"
        or value.get("appendix_indent") != "    "
        or value.get("blank_line_policy") != "exactly-one-between-header-heading-and-section-blocks"
        or value.get("empty_section_sentence") != "None."
        or value.get("terminal_lf_count") != 1
        or value.get("headings")
        != [
            "## Findings",
            "## Conditional concerns",
            "## Material questions",
            "## Disclosures",
            "## Coverage",
            "## Verified observation appendix",
        ]
        or value.get("grade_prefixes")
        != {
            "conditional_concern": "- **ConditionalConcern:** ",
            "coverage_limit": "- **Coverage limit:** ",
            "disclosure": "- **Disclosure:** ",
        }
        or type(value.get("disclosures")) is not list
        or len(cast(list[object], value["disclosures"])) != 4
        or any(type(item) is not str for item in cast(list[object], value["disclosures"]))
        or type(value.get("header")) is not str
        or type(value.get("m3_concern")) is not str
        or type(value.get("m3_coverage")) is not str
    ):
        raise SliceCRendererError("renderer registry literals differ")


def render_world1_report_v1(
    *,
    registry: RegistryBundleV1,
    materials: CapturedWorld1MaterialsV1,
    request_digest: str,
    observations: ObservationSetV1,
    composition: SliceCCompositionResultV1,
) -> RenderedSliceCReportV1:
    """Validate the sole report state and emit the report and appendix together."""

    try:
        validate_observations_v1(observations, materials=materials, request_digest=request_digest)
    except SliceCContractError as error:
        raise SliceCRendererError("observation set is not renderable") from error
    if (
        type(composition) is not SliceCCompositionResultV1
        or not composition.conditional_concern
        or composition.finding_count != 0
        or composition.material_question_count != 0
        or composition.missing_premises != ("world1.animal-id-is-independent-unit.v1",)
    ):
        raise SliceCRendererError("composition state is not the one M3 state")
    renderer = registry.renderer
    _validate_renderer_registry(renderer)
    appendix_value = {
        "h5ad_file_ref": materials.h5ad_file_ref,
        "observations": [observation.to_dict() for observation in observations],
        "request_digest": request_digest,
        "runtime_premise_digest": _RUNTIME_PREMISE_DIGEST,
        "runtime_premise_id": _RUNTIME_PREMISE_ID,
        "schema": "slice-c-world1-machine-appendix-v1",
        "snapshot_ref": materials.snapshot_ref,
        "source_file_ref": materials.source_file_ref,
    }
    appendix = canonical_json_bytes(appendix_value)
    if len(appendix) != _APPENDIX_SIZE or sha256(appendix) != _APPENDIX_SHA256:
        raise SliceCRendererError("canonical appendix identity differs")
    headings = cast(list[str], renderer["headings"])
    prefixes = cast(dict[str, str], renderer["grade_prefixes"])
    disclosures = cast(list[str], renderer["disclosures"])
    blocks = [
        cast(str, renderer["header"]),
        headings[0],
        cast(str, renderer["empty_section_sentence"]),
        headings[1],
        prefixes["conditional_concern"] + cast(str, renderer["m3_concern"]),
        headings[2],
        cast(str, renderer["empty_section_sentence"]),
        headings[3],
        "\n".join(prefixes["disclosure"] + disclosure for disclosure in disclosures),
        headings[4],
        prefixes["coverage_limit"] + cast(str, renderer["m3_coverage"]),
        headings[5],
        cast(str, renderer["appendix_indent"]) + appendix.decode("utf-8", "strict"),
    ]
    report = ("\n\n".join(blocks) + "\n").encode("utf-8", "strict")
    if len(report) != _REPORT_SIZE or sha256(report) != _REPORT_SHA256:
        raise SliceCRendererError("Markdown report identity differs")
    return RenderedSliceCReportV1(
        report_bytes=report,
        appendix_bytes=appendix,
        report_sha256=_REPORT_SHA256,
        appendix_sha256=_APPENDIX_SHA256,
    )


__all__ = [
    "RenderedSliceCReportV1",
    "SliceCRendererError",
    "render_world1_report_v1",
    "renderer_runtime_premise_v1",
]
