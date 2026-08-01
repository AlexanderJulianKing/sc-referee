from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.core import (
    FrozenInspectionContext,
    InspectionDocument,
    ReceiptKind,
    RecordRef,
)

_COMMON_IMPLEMENTATION_DIGEST = sha256_digest(Path(__file__).read_bytes())


def adapter_implementation_digest(implementation_path: Path) -> str:
    """Bind an adapter to its own module and the small shared identity/scope helper."""

    return semantic_digest(
        {
            "adapter_implementation_digest": sha256_digest(implementation_path.read_bytes()),
            "shared_adapter_helper_digest": _COMMON_IMPLEMENTATION_DIGEST,
        }
    )


def selected_report_document(context: FrozenInspectionContext) -> InspectionDocument | None:
    return selected_surface_document(
        context,
        parser_id="parser:markdown-inventory",
        parser_version="0.2.0",
        media_type="text/markdown",
    )


def selected_surface_document(
    context: FrozenInspectionContext,
    *,
    parser_id: str,
    parser_version: str,
    media_type: str,
) -> InspectionDocument | None:
    artifact = base_record(context, context.selected_artifact_ref)
    if artifact is None or artifact.get("kind") != "report":
        return None
    path = artifact.get("path")
    if not isinstance(path, str):
        return None
    matches = [
        item
        for item in context.documents
        if item.path == path
        and item.media_type == media_type
        and item.content_digest in artifact_content_digests(context, artifact)
        and item.parser_result_ref is not None
        and item.parser_result_payload is not None
    ]
    if len(matches) != 1:
        return None
    parser = json.loads(matches[0].parser_result_payload or b"{}")
    if (
        parser.get("parser_id") != parser_id
        or parser.get("parser_version") != parser_version
        or parser.get("state") not in {"parsed", "partially_parsed"}
    ):
        return None
    return matches[0]


def selected_surface_owns_artifact(context: FrozenInspectionContext) -> bool:
    surface = base_record(context, context.selected_surface_ref)
    if surface is None or surface.get("status") != "resolved":
        return False
    selection = surface.get("selection")
    return isinstance(selection, dict) and selection.get("selected_surface_refs") == [
        context.selected_artifact_ref.to_dict()
    ]


def base_record(context: FrozenInspectionContext, ref: RecordRef) -> dict[str, Any] | None:
    matches = [item for item in context.base_records if item.ref == ref]
    if len(matches) != 1:
        return None
    value = json.loads(matches[0].canonical_payload)
    return value if isinstance(value, dict) else None


def artifact_content_digests(
    context: FrozenInspectionContext, artifact: dict[str, Any]
) -> set[str]:
    identity_ref = artifact.get("asset_identity_ref")
    if not isinstance(identity_ref, dict):
        return set()
    identity = base_record(
        context,
        RecordRef(str(identity_ref.get("record_type")), str(identity_ref.get("record_id"))),
    )
    if identity is None or identity.get("tier") != "full_digest":
        return set()
    digest = identity.get("identity_evidence", {}).get("digest")
    return {str(digest)} if isinstance(digest, str) else set()


def receipt_kind(receipt_id: str) -> ReceiptKind:
    if "ambigu" in receipt_id:
        return "ambiguity"
    if "sibling" in receipt_id or "alternative" in receipt_id:
        return "sibling"
    if "suppress" in receipt_id:
        return "suppressor"
    return "counterevidence"


def receipt_description(receipt_id: str) -> str:
    return {
        "exactly-one-supported-declaration": (
            "Exactly one enumerated method declaration matched the selected report."
        ),
        "contradictory-declaration-absent": (
            "No contradictory enumerated declaration matched the selected report."
        ),
        "selected-surface-identity-complete": (
            "The report bytes have a full digest and are the exact selected Artifact."
        ),
        "finite-paragraph-scan-complete": (
            "Every paragraph in the selected immutable report was checked."
        ),
    }.get(receipt_id, f"The finite {receipt_id} check completed.")
