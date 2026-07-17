"""Wire the confounder-candidate diagnostic into the audit review flow.

The engine's checks emit gating `Finding`s. This diagnostic is EVIDENCE, not a verdict, so it does
not become a Finding and cannot gate a build. This hook gathers the diagnostic's inputs from the
audit context, runs `diagnose()` for whatever legs the inputs permit, and returns a record the audit
attaches to `AuditResult.diagnostics` (a non-gating field) and the report renders as evidence.

It never throws and never silently skips: when an input is missing it returns a structured
abstention with the reason, so the report shows the tool tried and why it could not, rather than an
absence that reads as "clean".
"""
from __future__ import annotations

import ast

import numpy as np
import pandas as pd

from sc_referee.code_signals import resolve_unit_of_test
from sc_referee.inference import bind as _bind
from sc_referee.inference.confounder_candidate import diagnose


def _abstain(reason: str) -> dict:
    return {"diagnostic": "confounder_candidate", "ran": False, "abstained": reason}


def _count_matrix(bundle):
    """The full units x genes count matrix (for a limma-voom trend), or None."""
    measure = getattr(bundle, "measure", None)
    counts = getattr(measure, "counts", None) if measure is not None else None
    if counts is None:
        return None
    if hasattr(counts, "toarray"):
        counts = counts.toarray()
    return np.asarray(counts, dtype=float)


def _reported_effect(bundle, outcome):
    """The analyst's reported effect for the target feature, to gate a proxy replay's faithfulness.

    Returns None when unavailable; the diagnostic then skips model legs for approximate replays
    rather than trusting an unchecked proxy.
    """
    rr = getattr(bundle, "reported_results", None)
    if rr is None or outcome is None or "feature_id" not in getattr(rr, "columns", []):
        return None
    effect_col = next((c for c in ("effect", "log2FoldChange", "logFC", "beta", "slope", "lfc")
                       if c in rr.columns), None)
    if effect_col is None:
        return None
    row = rr[rr["feature_id"].astype(str) == str(outcome)]
    if len(row) != 1:
        return None
    try:
        return float(row[effect_col].iloc[0])
    except (ValueError, TypeError):
        return None


def _sources(code_signals: dict) -> str:
    return "\n".join(code_signals.get("sources", []) if code_signals else [])


def _cells_frame(bundle) -> pd.DataFrame | None:
    """Assemble a cells x (grouping cols + gene counts) frame from observations + measure."""
    obs = getattr(bundle, "observations", None)
    if obs is None or not isinstance(obs, pd.DataFrame):
        return None
    frame = obs.reset_index(drop=False) if obs.index.name else obs.copy()
    measure = getattr(bundle, "measure", None)
    if measure is not None and getattr(measure, "counts", None) is not None:
        counts = measure.counts
        if hasattr(counts, "toarray"):
            counts = counts.toarray()
        counts = np.asarray(counts)
        feats = list(getattr(measure, "feature_index", []) or [])
        if counts.ndim == 2 and counts.shape[1] == len(feats) and counts.shape[0] == len(frame):
            genes = pd.DataFrame(counts, columns=feats, index=frame.index)
            # do not clobber grouping columns that share a gene name
            genes = genes[[g for g in feats if g not in frame.columns]]
            frame = pd.concat([frame, genes], axis=1)
    return frame


def _frame_aliases(source: str, columns) -> set:
    """Source variable names used as a frame carrying these columns: `c.HBB`, `df["y"]`, etc."""
    cols = set(columns)
    aliases = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return aliases
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.attr in cols:
            aliases.add(node.value.id)
        if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
                and isinstance(node.slice, ast.Constant) and node.slice.value in cols):
            aliases.add(node.value.id)
    return aliases


def _fitted_mask(bundle, design, frame):
    """The declared analysis subset, if the design provides one, aligned to `frame`."""
    try:
        from sc_referee.design import apply_subset
    except Exception:
        return None
    obs = getattr(bundle, "observations", None)
    if obs is None:
        return None
    try:
        sub = apply_subset(obs, design)
    except Exception:
        return None
    if sub is None or len(sub) == len(obs):
        return None
    mask = obs.index.isin(sub.index)
    return pd.Series(mask, index=frame.index) if len(mask) == len(frame) else None


def run_confounder_diagnostic(bundle, design) -> dict:
    """Run the diagnostic from the audit context. Returns a record for AuditResult.diagnostics.

    Applies to analyses with a declared exposure and a resolvable unit (eqtl today). Abstains -- with
    a reason -- on everything else.
    """
    exposure = getattr(design, "genotype_column", None) or getattr(design, "exposure_column", None)
    if not exposure:
        return _abstain("no declared exposure (genotype_column/exposure_column); the diagnostic "
                        "needs an exposure to price candidates against")

    code_signals = getattr(bundle, "code_signals", {}) or {}
    # prefer the design's declared unit (the CSP ratifies it); fall back to inferring from the code
    unit = getattr(design, "unit_of_test", None) or resolve_unit_of_test(code_signals)
    if not unit:
        return _abstain("could not resolve the unit of test (design.unit_of_test unset and none "
                        "inferable from the code); the diagnostic needs the unit at which the "
                        "exposure varies")

    frame = _cells_frame(bundle)
    if frame is None or exposure not in frame.columns or unit not in frame.columns:
        missing = [c for c in (exposure, unit) if frame is None or c not in frame.columns]
        return _abstain(f"assembled cell frame is missing required column(s): {missing}")

    source = _sources(code_signals)
    if not source.strip():
        return _abstain("no analyst source retained in code_signals; the scan and model recovery "
                        "both need the code")

    # bind the assembled frame under the names the source uses for it, plus common aliases
    tables = {}
    for alias in _frame_aliases(source, frame.columns) | {"c", "cells", "df", "adata", "obs"}:
        tables[alias] = frame

    fitted_mask = _fitted_mask(bundle, design, frame)
    outcome = getattr(design, "target_feature", None)
    reported_effect = _reported_effect(bundle, outcome)
    all_counts = _count_matrix(bundle)          # for a limma-voom mean-variance trend, if reached

    try:
        rec = diagnose(source, tables, unit=unit, exposure=exposure, fitted_mask=fitted_mask,
                       outcome=outcome, reported_effect=reported_effect, all_counts=all_counts)
    except Exception as exc:                       # never break the audit for a diagnostic
        return _abstain(f"diagnostic raised and was contained: {type(exc).__name__}: {exc}")

    return {
        "diagnostic": "confounder_candidate", "ran": True,
        "unit": unit, "exposure": exposure,
        "record": rec.to_json(), "markdown": rec.to_md(),
        "model_recovery": rec.model_recovery,
    }
