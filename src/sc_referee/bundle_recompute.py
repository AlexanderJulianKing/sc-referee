"""Wire the pseudobulk recompute into the bundle path — the recompute diagnostic for a Claude-Science
export.

The bundle's structural checks (double_dipping) never touch the matrix. This is the other half: when the
export ships a data file that loads as RAW counts and its `obs` carries a resolvable condition + a
donor/replicate column, we **run our own replicate-aware analysis on their data** — aggregate cells to
pseudobulk per donor, re-run the contrast, and report how many genes survive at the DONOR level. It
never runs THEIR code (parse-never-execute stands); it runs OUR analysis on THEIR data.

A bundle carries no human ratification, so this is a **needs_evidence diagnostic**, never a pass or a
blocker — the recompute check's own `blocking_allowed` gate would cap it anyway. When the counts can't
be loaded as raw ints, or a single condition + replicate can't be resolved deterministically (the
"semantics undecidable" wall), it says so honestly and points to `init → confirm → audit`, which is
where the confirmed-design recompute lives.
"""
from __future__ import annotations

import os
import re
import tempfile
import zipfile
from pathlib import Path

from sc_referee import statuses as S
from sc_referee.checks.base import Finding

CHECK_ID = "pseudobulk_recompute"
_DE_GROUPS = ("de_cell", "de_sample", "de_ambiguous")   # a differential-expression contrast in the pipeline
_CLAIMED_RE = re.compile(r"(\d[\d,]*)\s+(?:differentially[\s-]expressed|de|significant)\b[^.\n]{0,20}?genes", re.I)
_HANDOFF = "run `init → confirm → audit` on the counts to recompute at the replicate level."


def _has_de_contrast(inv) -> bool:
    return any(any(s.calls.get(g) for g in _DE_GROUPS) for s in inv.steps)


def _load_counts_bundle(inv, root):
    """The first bundle data file that loads as an AnnData with RAW counts, else None. Handles a folder
    or a `.zip` (member extracted to a temp file, then removed)."""
    from sc_referee.adapters.anndata_adapter import read_anndata
    root = Path(root)
    for d in inv.data:
        if not d.name.lower().endswith(".h5ad"):
            continue
        tmp = None
        try:
            if root.suffix == ".zip":
                with zipfile.ZipFile(root) as z:
                    raw = z.read(d.name)
                fd, tmp = tempfile.mkstemp(suffix=".h5ad")
                os.write(fd, raw)
                os.close(fd)
                bundle = read_anndata(tmp)
            else:
                bundle = read_anndata(root / d.name)
            if getattr(bundle.measure, "kind", None) == "counts":
                return bundle
        except Exception:
            continue
        finally:
            if tmp and os.path.exists(tmp):
                os.unlink(tmp)
    return None


def _resolve_roles(obs):
    """(replicate, condition, ref_level, test_level) when they resolve UNAMBIGUOUSLY, else None. Requires
    a detectable replicate column and EXACTLY ONE two-level column that is constant within replicate (each
    donor in one arm — the case where pseudobulk-per-donor is well defined). Anything ambiguous defers to
    the human confirm."""
    from sc_referee.adapters._common import detect_replicate_var
    rep = detect_replicate_var(list(obs.columns))
    if not rep or rep not in obs.columns:
        return None
    cands = []
    for c in obs.columns:
        if c == rep:
            continue
        levels = obs[c].dropna().unique()
        if len(levels) != 2:
            continue
        if bool((obs.groupby(rep, observed=True)[c].nunique(dropna=True) <= 1).all()):
            cands.append(c)
    if len(cands) != 1:
        return None
    cond = cands[0]
    ref, test = sorted(map(str, obs[cond].dropna().unique()))
    return rep, cond, ref, test


def _design(rep, cond, ref, test):
    from sc_referee.design import Design
    return Design(
        analysis_type="condition_contrast_DE",
        confirmed_by_human=False,                        # a bundle is never ratified -> diagnostic only
        confidence={"replicate_unit": "high", "condition": "high"},
        condition=cond, batch=[], replicate_unit=[rep],
        reference=ref, test=test, model=f"~ {cond}",
        target_coefficient=f"{cond}[T.{test}]", sample_unit=[rep], unit_of_test="cell",
    )


def _claimed_de_count(inv):
    for r in inv.reports:
        for claim in r.claims:
            m = _CLAIMED_RE.search(claim)
            if m:
                return int(m.group(1).replace(",", ""))
    return None


def _note(msg: str) -> Finding:
    return Finding(CHECK_ID, S.NEEDS_EVIDENCE, msg)


def bundle_recompute(inv, root):
    """A needs_evidence recompute diagnostic for a bundle, or None when the pipeline has no DE contrast."""
    if not _has_de_contrast(inv):
        return None
    bundle = _load_counts_bundle(inv, root)
    if bundle is None:
        return _note("a pseudobulk recompute is available for this contrast, but no data file in the "
                     f"export loads as raw counts — {_HANDOFF}")
    roles = _resolve_roles(bundle.observations)
    if roles is None:
        return _note("a pseudobulk recompute is available for this contrast, but a single condition + "
                     f"donor/replicate column could not be resolved from the data — {_HANDOFF}")
    rep, cond, ref, test = roles
    try:
        from sc_referee.engine import aggregate_to_pseudobulk
        from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute
        design = _design(rep, cond, ref, test)
        pb, meta = aggregate_to_pseudobulk(bundle, design)
        res = pydeseq2_recompute(pb, meta, design)       # DESeq2 GLM — handles the unpaired nested-donor case
        n_sig = int((res.table["padj"] < 0.05).sum())
        n_rep = int(res.n_replicates_per_arm)
    except Exception as exc:                             # degenerate aggregation, etc. -> abstain honestly
        return _note("a pseudobulk recompute is available for this contrast, but it could not be completed "
                     f"automatically ({type(exc).__name__}) — {_HANDOFF}")
    if n_rep < 3:
        return _note(f"recomputed the '{cond}' contrast at the donor level, but only {n_rep} biological "
                     f"replicate(s) per arm — too few for a replicate-aware verdict (need ≥ 3). Treat the "
                     f"cell-level claims as exploratory.")
    claimed = _claimed_de_count(inv)
    vs = f" vs ~{claimed} claimed in the report" if claimed is not None else ""
    return Finding(
        CHECK_ID, S.NEEDS_EVIDENCE,
        f"recomputed the '{cond}' contrast at the DONOR level (pseudobulk over '{rep}', {n_rep} "
        f"replicates/arm, DESeq2): {n_sig} gene(s) reach padj<0.05{vs}. A large drop is the "
        f"pseudoreplication signature — cell-level tests count cells as replicates and overstate "
        f"significance. This is a diagnostic on an UNCONFIRMED design; confirm it (`init → confirm → "
        f"audit`) for the full replicate-aware verdict. (We recomputed OUR analysis on their data; we "
        f"did not run their code, and this does not verify their reported number.)",
        metrics={"engine": "pydeseq2", "recompute_significant": n_sig, "replicates_per_arm": n_rep,
                 "claimed_de": claimed, "condition": cond, "replicate": rep})
