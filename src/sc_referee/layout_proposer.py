"""The Claude LAYOUT proposer — `init`, one level up (spec v2 §5).

Where a multi-file analysis encodes its design in the *filenames or directory structure* (WT_1.h5ad,
KO_2.h5ad) rather than in each file's `.obs`, a regex cannot safely recover the mapping. Claude reads
the directory METADATA ONLY (filenames, obs column names + a value preview, shapes — never the
matrices) and PROPOSES the per-shard semantic constants (condition / replicate / batch) and any files
to exclude, for a human to confirm. It never decides: the proposal lands in `sc-referee.manifest.yaml`
with `confirmed_by_human: false`, and arithmetic re-derives everything checkable at assembly time.

No API key -> deterministic fallback (`draft_manifest`, sample_ids only): honest, never a guess.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import anndata as ad
import jsonschema
import pandas as pd

from sc_referee.adapters._common import BIOLOGICAL_REPLICATE_TOKENS
from sc_referee.manifest import Manifest, Shard, discover_matrix_files, draft_manifest

DEFAULT_MODEL = "claude-opus-4-8"
LAYOUT_TOOL = "propose_layout"

LAYOUT_SYSTEM_PROMPT = """You are helping a non-expert ratify how a MULTI-FILE single-cell analysis \
is laid out on disk. Each file is one shard of one experiment. From the metadata only (filenames, \
each file's obs column names + a small value preview, and shapes), propose, PER SHARD, the semantic \
label columns the layout implies — typically `condition`, and where you can tell them apart, a \
biological `replicate` unit and a `batch`. These become obs columns a human confirms; they cannot be \
read off a filename with certainty, which is why you propose and a human ratifies.

Rules:
- Propose a constant ONLY when the metadata supports it (a filename token like WT/KO/stim, or a shared \
obs column). If a file's own obs already carries condition/replicate, you do not need a constant for it \
— say so in `plain_summary` and leave it out.
- If a file looks like it does NOT belong to this experiment (a reference atlas, an unrelated sample), \
put it in `excluded` with a reason.
- Put any role you cannot settle in `unresolved`. NEVER guess. `sample_id` is handled deterministically \
— do not propose it.
- You assign meaning; you never author statistics or decide a verdict."""


def layout_tool_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["shards"],
        "properties": {
            "plain_summary": {"type": "string"},
            "shards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "constants"],
                    "properties": {
                        "path": {"type": "string"},
                        "constants": {"type": "object", "additionalProperties": {"type": "string"}},
                    },
                },
            },
            "excluded": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "reason"],
                    "properties": {"path": {"type": "string"}, "reason": {"type": "string"}},
                },
            },
            "confidence": {"type": "object", "additionalProperties": {"enum": ["high", "medium", "low"]}},
            "unresolved": {"type": "array", "items": {"type": "string"}},
        },
    }


def scan_shards(folder) -> list:
    """Per-shard METADATA (never the full matrix): path, sample_id (filename stem), format, shape, obs
    columns + a small value preview — the evidence the proposer reasons over. h5ad carries its own obs;
    a CSV counts shard has none (its design comes from a per-shard obs file or manifest constants)."""
    folder = Path(folder)
    out = []
    for p, fmt in discover_matrix_files(folder):
        rel = p.relative_to(folder).as_posix()
        if fmt == "h5ad":
            a = ad.read_h5ad(p, backed="r")
            try:
                obs = a.obs
                out.append({
                    "path": rel, "sample_id": p.stem, "format": "h5ad",
                    "n_cells": int(a.n_obs), "n_genes": int(a.n_vars),
                    "obs_columns": [str(c) for c in obs.columns],
                    "obs_preview": {str(c): [str(v) for v in list(obs[c].unique())[:5]] for c in obs.columns},
                })
            finally:
                if getattr(a, "isbacked", False) and a.file is not None:
                    a.file.close()
        else:
            header = pd.read_csv(p, nrows=0, sep="," if fmt == "csv" else "\t")
            out.append({
                "path": rel, "sample_id": p.stem, "format": fmt,
                "n_cells": None, "n_genes": max(len(header.columns) - 1, 0),
                "obs_columns": [], "obs_preview": {},
            })
    return out


def _manifest_from_payload(payload: dict, meta: list) -> Manifest:
    jsonschema.validate(payload, layout_tool_schema())
    scanned = {m["path"] for m in meta}
    proposed = {s["path"]: (s.get("constants") or {}) for s in payload["shards"]}
    excluded_list = payload.get("excluded") or []
    excluded_paths = {e["path"] for e in excluded_list}

    # The model may only assign meaning to files that EXIST — a hallucinated path is not confirmable.
    unknown = sorted((set(proposed) | excluded_paths) - scanned)
    if unknown:
        raise ValueError(f"the layout proposal references files not found in the folder: {unknown} "
                         f"(scanned: {sorted(scanned)}).")

    shards, sample_ids, unclassified = [], [], []
    for m in meta:
        if m["path"] in excluded_paths:
            continue
        sid = m["sample_id"]
        sample_ids.append(sid)
        # sample_id is deterministic; the model's proposed semantic constants ride on top.
        constants = {"sample_id": sid, **{k: str(v) for k, v in proposed.get(m["path"], {}).items()}}
        shards.append(Shard(path=m["path"], format=m.get("format", "h5ad"), constants=constants))
        if m["path"] not in proposed:
            unclassified.append(m["path"])

    unresolved = list(payload.get("unresolved") or [])
    if unclassified:   # a shard the model neither labeled nor excluded — surfaced, not silently blank
        unresolved.append(f"unclassified shards (no proposed constants, not excluded): {unclassified} "
                          f"— fill their constants or exclude them before confirming")
    return Manifest(
        shards=shards,
        expected_sample_ids=sample_ids,
        excluded=excluded_list,
        confidence=payload.get("confidence") or {},
        unresolved=unresolved,
        confirmed_by_human=False,
    )


def _call_layout_proposer(client, meta: list, model: str | None = None) -> dict:
    model = model or os.environ.get("SC_REFEREE_MODEL", DEFAULT_MODEL)
    message = client.messages.create(   # NO temperature (the API rejects it for this model)
        model=model, max_tokens=2000, system=LAYOUT_SYSTEM_PROMPT,
        tools=[{"name": LAYOUT_TOOL,
                "description": "Propose the per-shard layout constants for a human to ratify.",
                "input_schema": layout_tool_schema()}],
        tool_choice={"type": "tool", "name": LAYOUT_TOOL},
        messages=[{"role": "user", "content": json.dumps(meta, indent=2, default=str)}],
    )
    uses = [b for b in message.content
            if getattr(b, "type", None) == "tool_use" and b.name == LAYOUT_TOOL]
    if not uses:
        raise ValueError("layout: the model did not call `propose_layout` (returned prose instead)")
    payload = uses[0].input
    try:
        jsonschema.validate(payload, layout_tool_schema())
    except jsonschema.ValidationError as e:
        raise ValueError(f"layout: the model's proposal failed schema validation: {e.message}") from e
    return payload


def _shared_obs_role(meta: list, tokens) -> str | None:
    """An obs column present in EVERY shard whose name matches a token — an embedded design column the
    design can name directly, so no constant is needed for it."""
    if not meta:
        return None
    common = set(meta[0]["obs_columns"])
    for m in meta[1:]:
        common &= set(m["obs_columns"])
    for c in sorted(common):
        if any(tok in str(c).lower() for tok in tokens):
            return c
    return None


def _deterministic_draft(folder, meta: list) -> Manifest:
    """The no-LLM draft, made smarter: if condition / replicate already live in every shard's `.obs`,
    note that (the design will name the column) instead of nagging the human to fill a constant."""
    from sc_referee.init import CONDITION_TOKENS

    manifest = draft_manifest(folder)
    found = {}
    cond = _shared_obs_role(meta, CONDITION_TOKENS)
    rep = _shared_obs_role(meta, BIOLOGICAL_REPLICATE_TOKENS)   # donor/mouse, NOT a technical sample_id
    if cond:
        found["condition"] = cond
    if rep:
        found["replicate_unit"] = rep
    manifest.confidence = {role: f"in .obs ({col})" for role, col in found.items()}
    manifest.unresolved = (
        [] if "condition" in found
        else ["condition: not in any shard's .obs — add a `condition` constant per shard, or a per-shard obs file"])
    return manifest


def propose_manifest(folder, client="auto", model: str | None = None):
    """Returns (Manifest, source) with source in {claude, heuristic_no_llm}. `client='auto'` resolves
    an Anthropic client from the environment; None (or no key) -> the deterministic draft."""
    folder = Path(folder)
    meta = scan_shards(folder)
    if len(meta) < 2:
        raise ValueError(f"{folder}: propose_manifest is for multi-file analyses "
                         f"(found {len(meta)} .h5ad).")
    if client == "auto":
        from sc_referee.init import _default_client
        client = _default_client()
    if client is None:
        return _deterministic_draft(folder, meta), "heuristic_no_llm"
    return _manifest_from_payload(_call_layout_proposer(client, meta, model), meta), "claude"
