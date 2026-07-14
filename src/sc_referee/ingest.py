"""Folder discovery -> canonical Bundle. (spec §[1], C1)

`ingest(folder)` walks the directory (top level, then one level down) and resolves three
roles by pattern — data matrix (required), reported results (optional), code (optional) —
recording each resolved path + reason in `provenance`. It never silently guesses which
file is the data. (D1 covers the AnnData + reported-CSV roles; EIP + code parsing land next.)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from sc_referee.adapters.anndata_adapter import read_anndata
from sc_referee.adapters.csv_adapter import find_counts_candidates, read_csv
from sc_referee.bundle import Bundle
from sc_referee.code_signals import parse_code_signals
from sc_referee import synonyms

MANIFEST_NAME = "sc-referee.manifest.yaml"


@dataclass(frozen=True)
class ReportedClaim:
    """One confirmed report artifact and its claim-local routing declarations."""

    report_relative_path: str
    reported_results: pd.DataFrame
    reported_columns: tuple[str, ...]
    name: str | None = None
    contrast: str | None = None
    analysis_type: str | None = None
    unit_of_test: str | None = None
    value_kind: str | None = None


class IngestError(Exception):
    """The folder cannot be resolved to a single unambiguous analysis to audit. Distinct from
    `FileNotFoundError` (nothing to read): here there is TOO MUCH, and guessing one would risk a
    partial/wrong-scope audit. A manifest (future) declares how multiple files assemble."""


def _walk(folder: Path, pattern: str):
    """Top level first, then exactly one level down."""
    return sorted(folder.glob(pattern)) + sorted(folder.glob(f"*/{pattern}"))


def _sep_for(path: Path) -> str:
    return "\t" if str(path).endswith(".tsv") else ","


def _load_reported(path: Path, *, error_type=IngestError, label=None):
    try:
        df = pd.read_csv(path, sep=_sep_for(path))
    except (OSError, UnicodeError, ValueError, pd.errors.ParserError,
            pd.errors.EmptyDataError) as exc:
        raise error_type(f"{label or path}: could not parse reported table: {exc}") from exc
    binding = synonyms.bind_columns(df.columns)
    if binding["gene"] is None:
        return None
    out = pd.DataFrame({"feature_id": df[binding["gene"]].astype(str)})
    out["pvalue"] = df[binding["pval"]] if binding["pval"] else pd.NA
    out["padj"] = df[binding["padj"]] if binding["padj"] else pd.NA
    out["effect"] = df[binding["effect"]] if binding["effect"] else pd.NA
    return out


def _validated_report_header(path: Path, *, error_type=IngestError, label=None) -> tuple[str, ...]:
    from sc_referee.adapters.csv_adapter import raw_header

    display = label or str(path)
    try:
        columns = tuple(raw_header(path, _sep_for(path)))
    except (OSError, UnicodeError, ValueError) as exc:
        raise error_type(f"{display} could not be parsed: {exc}") from exc
    seen, duplicates = set(), []
    for column in columns:
        if column in seen and column not in duplicates:
            duplicates.append(column)
        seen.add(column)
    if duplicates:
        raise error_type(
            f"{display} has duplicate raw header(s) {duplicates}; refusing before pandas can "
            "rename them and bind the wrong reported column")
    return columns


def _reported_candidates(folder: Path, exclude: set):
    """EVERY CSV/TSV (other than the data/shard/obs files) whose header looks like reported DE output.
    More than one means the scope is ambiguous — the caller binds none rather than a possible decoy."""
    out = []
    for csv in _walk(folder, "*.csv") + _walk(folder, "*.tsv"):
        if csv.resolve() in exclude:
            continue
        try:
            header = _validated_report_header(csv)
        except IngestError:
            raise
        except (OSError, UnicodeError, ValueError):
            continue
        if synonyms.is_reported_de(header):
            out.append(csv)
    return out


def _confirmed_reported_claim(folder: Path) -> Path | None:
    """Resolve and validate the one report claim the confirmed folder config declares.

    The path is data, not code: it must stay under the audited folder and parse as the same closed
    reported-DE shape used by auto-discovery. A bad declaration is a ``DesignError`` so it can never
    be rendered as a scientific finding.
    """
    from sc_referee.config import confirmed_reported_path
    from sc_referee.design import DesignError

    declared = confirmed_reported_path(folder / "sc-referee.yaml")
    if declared is None:
        return None

    root = folder.resolve()
    path = (folder / declared).resolve()
    try:
        path.relative_to(root)
    except ValueError as e:
        raise DesignError(
            f"reported_results.path {declared!r} must name a table under the analysis folder") from e
    if not path.is_file():
        raise DesignError(f"reported_results.path {declared!r} does not exist under the analysis folder")
    if path.suffix.lower() not in {".csv", ".tsv"}:
        raise DesignError(
            f"reported_results.path {declared!r} is not a supported CSV/TSV reported-DE table")
    header = _validated_report_header(
        path, error_type=DesignError, label=f"reported_results.path {declared!r}")
    if not synonyms.is_reported_de(header):
        raise DesignError(
            f"reported_results.path {declared!r} is not a reported-DE table "
            f"(expected a feature/gene column and a p-value or adjusted-p column)")
    return path


def _confirmed_reported_claims(folder: Path) -> tuple[ReportedClaim, ...]:
    """Validate and load every claim in the confirmed ``claims`` manifest.

    A declared path is authority only after the same closed, in-folder table validation as the
    singular contract.  One bad entry rejects the config; silently dropping it would create a
    false impression of complete claim coverage.
    """
    from sc_referee.config import confirmed_reported_claims
    from sc_referee.design import DesignError

    specs = confirmed_reported_claims(folder / "sc-referee.yaml")
    if not specs:
        return ()
    root = folder.resolve()
    seen = set()
    claims = []
    for index, spec in enumerate(specs):
        declared = spec.get("path")
        label = f"claims[{index}].path"
        if not isinstance(declared, str) or not declared.strip():
            raise DesignError(f"{label} must name a table under the analysis folder")
        path = (folder / declared).resolve()
        try:
            path.relative_to(root)
        except ValueError as e:
            raise DesignError(
                f"{label} {declared!r} must name a table under the analysis folder") from e
        if path in seen:
            raise DesignError(f"{label} {declared!r} duplicates an earlier reported claim")
        seen.add(path)
        if not path.is_file():
            raise DesignError(f"{label} {declared!r} does not exist under the analysis folder")
        if path.suffix.lower() not in {".csv", ".tsv"}:
            raise DesignError(f"{label} {declared!r} is not a supported CSV/TSV reported-DE table")
        columns = _validated_report_header(
            path, error_type=DesignError, label=f"{label} {declared!r}")
        if not synonyms.is_reported_de(columns):
            raise DesignError(
                f"{label} {declared!r} is not a reported-DE table "
                f"(expected a feature/gene column and a p-value or adjusted-p column)")
        table = _load_reported(path, error_type=DesignError, label=f"{label} {declared!r}")
        claims.append(ReportedClaim(
            path.relative_to(root).as_posix(), table, columns,
            name=spec.get("name"), contrast=spec.get("contrast"),
            analysis_type=spec.get("analysis_type"), unit_of_test=spec.get("unit_of_test"),
            value_kind=spec.get("value_kind"),
        ))
    return tuple(claims)


def ingest(folder, *, confirming=False) -> Bundle:
    folder = Path(folder)
    provenance: dict = {}
    exclude_reported: set = set()   # data/shard/obs files that must not be mis-bound as reported-DE

    def rel(path: Path) -> str:
        try:
            return path.relative_to(folder).as_posix()
        except ValueError:
            return str(path)

    manifest_path = folder / MANIFEST_NAME
    if manifest_path.exists():
        # A manifest declares how multiple files assemble -> the deterministic assembler builds ONE
        # Bundle from the shards (verified, not trusted). Lazy imports: assemble imports IngestError.
        from sc_referee.adapters.assemble import assemble
        from sc_referee.manifest import load_manifest
        manifest = load_manifest(manifest_path)
        bundle = assemble(manifest, folder, confirming=confirming)
        data_path = manifest_path
        # A declared count shard / obs table is NOT the reported-DE results — exclude them from
        # reported discovery so a shard whose columns look DE-ish can't be mis-bound as results.
        exclude_reported |= {(folder / s.path).resolve() for s in manifest.shards}
        exclude_reported |= {(folder / s.obs_path).resolve() for s in manifest.shards if s.obs_path}
        provenance["data"] = {"path": MANIFEST_NAME,
                              "reason": f"assembled {len(manifest.shards)} shard(s) declared in the manifest"}
        provenance["manifest"] = {
            "shards": list(getattr(bundle, "manifest_accounting", [])),
            "exclusions": list(manifest.excluded),
        }
    else:
        # Single-file routing: AnnData first, then a CSV/TSV analysis (counts.csv + obs.csv).
        from sc_referee.manifest import discover_matrix_files
        h5ads = _walk(folder, "*.h5ad")
        csv_candidates = find_counts_candidates(folder)

        # Refuse-on-ambiguity: >1 candidate data matrix and no manifest declaring how they assemble.
        # Taking the first would silently audit a partial/wrong scope — an `atlas.h5ad` decoy, one arm
        # of a condition split, one mouse of eight. Count EVERY matrix (incl. subdir CSV shards).
        candidates = discover_matrix_files(folder)
        if len(candidates) > 1:
            names = ", ".join(sorted(rel(p) for p, _ in candidates))
            raise IngestError(
                f"{folder}: {len(candidates)} candidate data matrices found ({names}). sc-referee "
                f"audits ONE assembled matrix and will not guess which is the analysis. Provide a "
                f"single matrix, or run `sc-referee init` to declare a manifest that says how they "
                f"assemble (which file is which sample/condition).")

        if h5ads:
            data_path = h5ads[0]
            try:
                bundle = read_anndata(data_path)
            except (OSError, ValueError) as e:
                raise IngestError(f"{data_path}: could not ingest AnnData: {e}") from e
            provenance["data"] = {"path": rel(data_path), "reason": "the single *.h5ad under the folder",
                                  "matrix_slot": getattr(bundle, "matrix_slot", None)}
        elif csv_candidates:
            data_path = csv_candidates[0]
            try:
                bundle = read_csv(folder)
            except IngestError:
                raise
            except (OSError, UnicodeError, ValueError, pd.errors.ParserError,
                    pd.errors.EmptyDataError) as e:
                raise IngestError(f"{data_path}: could not ingest delimited matrix/metadata: {e}") from e
            provenance["data"] = {"path": rel(data_path),
                                  "reason": "CSV/TSV count matrix (cells x genes) + cell-metadata table"}
        else:
            raise FileNotFoundError(
                f"{folder}: no supported data matrix found. Provide a .h5ad, or a CSV/TSV analysis "
                f"(counts.csv + obs.csv, cells x genes with a cell_id index). "
                f"(10x .mtx support lands next.)")

    exclude_reported.add(Path(data_path).resolve())
    declared_claims = _confirmed_reported_claims(folder)
    declared_reported = None if declared_claims else _confirmed_reported_claim(folder)
    reported = _reported_candidates(folder, exclude_reported)
    if declared_claims:
        # The confirmed list is the complete claim manifest. Preserve the singular compatibility
        # slot as its first entry while retaining every claim for the Phase-3 audit loop.
        bundle.reported_claims = declared_claims
        first = declared_claims[0]
        bundle.reported_results = first.reported_results
        bundle.reported_columns = list(first.reported_columns)
        provenance["reported"] = {
            "path": first.report_relative_path,
            "reason": "confirmed sc-referee.yaml declared this reported claim",
        }
        provenance["reported_claims"] = [
            {"path": claim.report_relative_path,
             "reason": "confirmed sc-referee.yaml declared this reported claim"}
            for claim in declared_claims
        ]
    elif declared_reported is not None:
        # A confirmed declaration is authority independently of shallow auto-discovery. This covers
        # deep report paths and prevents a shallow decoy from overriding the ratified artifact.
        from sc_referee.design import DesignError
        rp = declared_reported
        bundle.reported_results = _load_reported(rp, error_type=DesignError,
                                                 label=f"reported_results.path {rel(rp)!r}")
        bundle.reported_columns = list(_validated_report_header(
            rp, error_type=DesignError,
            label=f"reported_results.path {rel(rp)!r}"))
        provenance["reported"] = {
            "path": rel(rp),
            "reason": "confirmed sc-referee.yaml declared this reported claim",
        }
    elif len(reported) == 1:
        rp = reported[0]
        bundle.reported_results = _load_reported(rp)
        bundle.reported_columns = list(map(str, pd.read_csv(rp, nrows=0, sep=_sep_for(rp)).columns))
        provenance["reported"] = {"path": rel(rp), "reason": "header matched reported-DE synonyms"}
    elif len(reported) > 1:
        # Ambiguous: an old rerun beside the paper's table, per-subset DE tables, etc. Bind NONE
        # so the checks abstain rather than audit a decoy; the human declares which.
        names = ", ".join(sorted(rel(p) for p in reported))
        provenance["reported"] = {"path": None,
            "reason": (f"AMBIGUOUS: {len(reported)} reported-DE tables ({names}); none bound to "
                       f"avoid auditing a decoy — declare which is the analysis's output.")}

    code_signals = parse_code_signals(folder)
    if code_signals["files"]:
        bundle.code_signals = code_signals
        provenance["code"] = {"path": ", ".join(code_signals["files"]),
                              "reason": "parsed (never executed) for imports + DE/cluster/DA calls"}

    bundle.provenance = provenance
    return bundle
