from __future__ import annotations

import sys

# The independently reviewed launcher lives outside the locked core/evaluation distributions.
# It sets this process-local value only after the official anchor and every frozen distribution
# RECORD have replayed. A direct import therefore remains fail closed at UNFROZEN.
_APPROVED_DIGEST_ATTRIBUTE = "_sc_referee_approved_runner_freeze_digest"
_APPROVED_LAUNCH_RECEIPT_ATTRIBUTE = "_sc_referee_qualification_launch_receipt"
_main = sys.modules.get("__main__")
_approved = getattr(_main, _APPROVED_DIGEST_ATTRIBUTE, "UNFROZEN")
_launch_receipt = getattr(_main, _APPROVED_LAUNCH_RECEIPT_ATTRIBUTE, None)
OFFICIAL_RUNNER_FREEZE_DIGEST = (
    _approved
    if isinstance(_approved, str) and _approved.startswith("sha256:") and len(_approved) == 71
    else "UNFROZEN"
)
APPROVED_LAUNCH_RECEIPT = dict(_launch_receipt) if isinstance(_launch_receipt, dict) else None


__all__ = ["APPROVED_LAUNCH_RECEIPT", "OFFICIAL_RUNNER_FREEZE_DIGEST"]
